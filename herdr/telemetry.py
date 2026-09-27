"""Consumer-neutral append-only swarm telemetry for Herdr.

The telemetry contract is intentionally closed: it contains operational metadata
needed by Herdr/Machine City and has no prompt, response, raw tool arguments,
credential or arbitrary metadata field.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Mapping

_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]{1,256}$")
_SHA = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_MAX_EVENTS_READ = 10_000


class TelemetryError(ValueError):
    pass


class EventType(StrEnum):
    TASK_STATE = "task_state"
    MODEL_ROUTE = "model_route"
    MODEL_FALLBACK = "model_fallback"
    TOOL_CALL = "tool_call"
    ARTIFACT = "artifact"
    VALIDATION = "validation"
    REVIEW = "review"
    RETRY = "retry"
    TIMEOUT = "timeout"
    BLOCKER = "blocker"
    RESOURCE = "resource"


class CostUnknownReason(StrEnum):
    PROVIDER_NOT_REPORTED = "provider_not_reported"
    PRICING_MISSING = "pricing_missing"
    TOKEN_USAGE_MISSING = "token_usage_missing"
    NON_BILLABLE = "non_billable"


def _nonneg(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TelemetryError(f"{field_name} must be a non-negative integer")
    return value


def _token(value: str | None, field_name: str, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise TelemetryError(f"{field_name} is required")
        return None
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise TelemetryError(f"{field_name} is not a safe telemetry token")
    return value


def _sha(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise TelemetryError(f"{field_name} must be a lowercase 40/64-char hex digest")
    return value


def _timestamp(value: str) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise TelemetryError("timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TelemetryError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise TelemetryError("timestamp must include timezone")
    return parsed.astimezone(UTC).isoformat()


@dataclass(frozen=True)
class PricingEntry:
    provider: str
    model: str
    version: str
    input_microusd_per_million: int
    output_microusd_per_million: int
    cached_microusd_per_million: int = 0
    currency: str = "USD"

    def __post_init__(self) -> None:
        _token(self.provider, "provider", required=True)
        _token(self.model, "model", required=True)
        _token(self.version, "pricing version", required=True)
        for name in (
            "input_microusd_per_million",
            "output_microusd_per_million",
            "cached_microusd_per_million",
        ):
            _nonneg(getattr(self, name), name)
        if self.currency != "USD":
            raise TelemetryError("pricing registry currently supports USD only")


class PricingRegistry:
    def __init__(self, entries: Iterable[PricingEntry] = ()) -> None:
        self._entries: dict[tuple[str, str, str], PricingEntry] = {}
        for entry in entries:
            key = (entry.provider, entry.model, entry.version)
            if key in self._entries:
                raise TelemetryError(f"duplicate pricing entry: {key}")
            self._entries[key] = entry

    def estimate(
        self,
        *,
        provider: str,
        model: str,
        version: str,
        input_tokens: int | None,
        output_tokens: int | None,
        cached_tokens: int | None = 0,
    ) -> tuple[int | None, CostUnknownReason | None]:
        if input_tokens is None or output_tokens is None:
            return None, CostUnknownReason.TOKEN_USAGE_MISSING
        key = (provider, model, version)
        entry = self._entries.get(key)
        if entry is None:
            return None, CostUnknownReason.PRICING_MISSING
        inp = _nonneg(input_tokens, "input_tokens") or 0
        out = _nonneg(output_tokens, "output_tokens") or 0
        cached = _nonneg(cached_tokens, "cached_tokens") or 0
        if cached > inp:
            raise TelemetryError("cached_tokens cannot exceed input_tokens")
        uncached = inp - cached
        numerator = (
            uncached * entry.input_microusd_per_million
            + cached * entry.cached_microusd_per_million
            + out * entry.output_microusd_per_million
        )
        return (numerator + 999_999) // 1_000_000, None


@dataclass(frozen=True)
class TelemetryEvent:
    sequence: int
    timestamp: str
    event_type: EventType
    issue: str
    task_id: str
    attempt: int
    agent_id: str
    role: str
    parent_task_id: str | None = None
    state: str | None = None
    reason: str | None = None
    provider: str | None = None
    model: str | None = None
    router_decision: str | None = None
    fallback_chain: tuple[str, ...] = ()
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    request_latency_ms: int | None = None
    model_latency_ms: int | None = None
    runtime_ms: int | None = None
    queue_wait_ms: int | None = None
    estimated_cost_microusd: int | None = None
    actual_cost_microusd: int | None = None
    cost_unknown_reason: CostUnknownReason | None = CostUnknownReason.PROVIDER_NOT_REPORTED
    currency: str = "USD"
    pricing_version: str | None = None
    tool_names: tuple[str, ...] = ()
    branch: str | None = None
    base_sha: str | None = None
    result_sha: str | None = None
    test_result: str | None = None
    reviewer_result: str | None = None
    retry_count: int = 0
    blocker: str | None = None
    cpu_millis: int | None = None
    max_rss_bytes: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0:
            raise TelemetryError("sequence must be a non-negative integer")
        object.__setattr__(self, "timestamp", _timestamp(self.timestamp))
        for name in ("issue", "task_id", "agent_id", "role"):
            _token(getattr(self, name), name, required=True)
        for name in (
            "parent_task_id", "state", "reason", "provider", "model",
            "router_decision", "pricing_version", "test_result",
            "reviewer_result", "blocker",
        ):
            _token(getattr(self, name), name)
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 0:
            raise TelemetryError("attempt must be a non-negative integer")
        for name in (
            "input_tokens", "output_tokens", "cached_tokens", "request_latency_ms",
            "model_latency_ms", "runtime_ms", "queue_wait_ms",
            "estimated_cost_microusd", "actual_cost_microusd", "retry_count",
            "cpu_millis", "max_rss_bytes",
        ):
            _nonneg(getattr(self, name), name)
        if self.cached_tokens is not None and self.input_tokens is not None and self.cached_tokens > self.input_tokens:
            raise TelemetryError("cached_tokens cannot exceed input_tokens")
        for value in self.fallback_chain:
            _token(value, "fallback_chain item", required=True)
        for value in self.tool_names:
            _token(value, "tool name", required=True)
        if len(self.tool_names) > 64 or len(self.fallback_chain) > 16:
            raise TelemetryError("telemetry tuple exceeds bounded contract")
        if self.branch is not None and ("\n" in self.branch or len(self.branch) > 256):
            raise TelemetryError("branch is invalid")
        _sha(self.base_sha, "base_sha")
        _sha(self.result_sha, "result_sha")
        if self.currency != "USD":
            raise TelemetryError("currency must be USD")
        if self.actual_cost_microusd is None and self.cost_unknown_reason is None:
            raise TelemetryError("unknown actual cost requires cost_unknown_reason")
        if self.actual_cost_microusd is not None and self.cost_unknown_reason is not None:
            raise TelemetryError("known actual cost cannot carry cost_unknown_reason")
        if (self.actual_cost_microusd is not None or self.estimated_cost_microusd is not None) and not self.pricing_version:
            raise TelemetryError("known/estimated cost requires pricing_version")
        if self.event_type is EventType.MODEL_FALLBACK and not self.fallback_chain:
            raise TelemetryError("model_fallback event requires fallback_chain")

    @property
    def event_id(self) -> str:
        payload = self.to_json(include_event_id=False)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def to_json(self, *, include_event_id: bool = True) -> dict[str, object]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["cost_unknown_reason"] = (
            self.cost_unknown_reason.value if self.cost_unknown_reason is not None else None
        )
        data["fallback_chain"] = list(self.fallback_chain)
        data["tool_names"] = list(self.tool_names)
        if include_event_id:
            data["event_id"] = self.event_id
        return data

    @classmethod
    def from_json(cls, raw: Mapping[str, object]) -> "TelemetryEvent":
        allowed = {f.name for f in cls.__dataclass_fields__.values()} | {"event_id"}
        extra = set(raw) - allowed
        if extra:
            raise TelemetryError(f"unknown telemetry fields rejected: {sorted(extra)}")
        values = dict(raw)
        expected_id = values.pop("event_id", None)
        values["event_type"] = EventType(str(values["event_type"]))
        reason = values.get("cost_unknown_reason")
        values["cost_unknown_reason"] = (
            None if reason is None else CostUnknownReason(str(reason))
        )
        values["fallback_chain"] = tuple(values.get("fallback_chain") or ())
        values["tool_names"] = tuple(values.get("tool_names") or ())
        event = cls(**values)
        if expected_id is not None and expected_id != event.event_id:
            raise TelemetryError("telemetry event_id mismatch")
        return event


@dataclass(frozen=True)
class Aggregate:
    events: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    actual_cost_microusd: int = 0
    unknown_cost_events: int = 0
    fallbacks: int = 0
    latency_ms_total: int = 0
    latency_samples: int = 0

    def add(self, event: TelemetryEvent) -> "Aggregate":
        latency = event.model_latency_ms if event.model_latency_ms is not None else event.request_latency_ms
        return Aggregate(
            events=self.events + 1,
            input_tokens=self.input_tokens + (event.input_tokens or 0),
            output_tokens=self.output_tokens + (event.output_tokens or 0),
            cached_tokens=self.cached_tokens + (event.cached_tokens or 0),
            actual_cost_microusd=self.actual_cost_microusd + (event.actual_cost_microusd or 0),
            unknown_cost_events=self.unknown_cost_events + int(event.actual_cost_microusd is None),
            fallbacks=self.fallbacks + int(event.event_type is EventType.MODEL_FALLBACK),
            latency_ms_total=self.latency_ms_total + (latency or 0),
            latency_samples=self.latency_samples + int(latency is not None),
        )


@dataclass(frozen=True)
class TelemetryReadModel:
    last_sequence: int
    tasks: dict[str, dict[str, object]]
    by_issue: dict[str, Aggregate]
    by_agent: dict[str, Aggregate]
    by_model: dict[str, Aggregate]
    by_day: dict[str, Aggregate]

    def to_json(self) -> dict[str, object]:
        def agg(values: Mapping[str, Aggregate]) -> dict[str, dict[str, int]]:
            return {key: asdict(value) for key, value in sorted(values.items())}
        return {
            "last_sequence": self.last_sequence,
            "tasks": {key: value for key, value in sorted(self.tasks.items())},
            "by_issue": agg(self.by_issue),
            "by_agent": agg(self.by_agent),
            "by_model": agg(self.by_model),
            "by_day": agg(self.by_day),
        }


def materialize(events: Iterable[TelemetryEvent]) -> TelemetryReadModel:
    tasks: dict[str, dict[str, object]] = {}
    by_issue: dict[str, Aggregate] = defaultdict(Aggregate)
    by_agent: dict[str, Aggregate] = defaultdict(Aggregate)
    by_model: dict[str, Aggregate] = defaultdict(Aggregate)
    by_day: dict[str, Aggregate] = defaultdict(Aggregate)
    last = 0
    for event in events:
        if event.sequence <= last:
            raise TelemetryError("event sequence must be strictly increasing")
        last = event.sequence
        state = tasks.setdefault(
            event.task_id,
            {
                "issue": event.issue,
                "task_id": event.task_id,
                "parent_task_id": event.parent_task_id,
                "agent_id": event.agent_id,
                "role": event.role,
                "attempt": event.attempt,
                "state": None,
                "model": None,
                "provider": None,
                "last_event_type": None,
                "last_sequence": 0,
                "last_timestamp": None,
                "blocker": None,
                "reviewer_result": None,
                "result_sha": None,
            },
        )
        state.update(
            {
                "parent_task_id": event.parent_task_id,
                "agent_id": event.agent_id,
                "role": event.role,
                "attempt": event.attempt,
                "last_event_type": event.event_type.value,
                "last_sequence": event.sequence,
                "last_timestamp": event.timestamp,
            }
        )
        if event.state is not None:
            state["state"] = event.state
        if event.model is not None:
            state["model"] = event.model
        if event.provider is not None:
            state["provider"] = event.provider
        if event.blocker is not None:
            state["blocker"] = event.blocker
        if event.reviewer_result is not None:
            state["reviewer_result"] = event.reviewer_result
        if event.result_sha is not None:
            state["result_sha"] = event.result_sha

        by_issue[event.issue] = by_issue[event.issue].add(event)
        by_agent[event.agent_id] = by_agent[event.agent_id].add(event)
        if event.model:
            by_model[event.model] = by_model[event.model].add(event)
        day = event.timestamp[:10]
        by_day[day] = by_day[day].add(event)

    return TelemetryReadModel(
        last_sequence=last,
        tasks=tasks,
        by_issue=dict(by_issue),
        by_agent=dict(by_agent),
        by_model=dict(by_model),
        by_day=dict(by_day),
    )


class TelemetryStore:
    """Append-only JSONL store with monotonic sequence and bounded live reads."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def read(self, *, max_events: int = _MAX_EVENTS_READ) -> tuple[TelemetryEvent, ...]:
        if max_events < 1 or max_events > _MAX_EVENTS_READ:
            raise TelemetryError("max_events outside bounded contract")
        if not self.path.exists():
            return ()
        events: list[TelemetryEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                if len(events) >= max_events:
                    raise TelemetryError("telemetry log exceeds bounded read limit")
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise TelemetryError(f"malformed telemetry line {line_no}") from exc
                event = TelemetryEvent.from_json(raw)
                if events and event.sequence <= events[-1].sequence:
                    raise TelemetryError("telemetry sequence is not strictly increasing")
                events.append(event)
        return tuple(events)

    def append(self, event: TelemetryEvent) -> TelemetryEvent:
        if event.sequence != 0:
            raise TelemetryError("append expects sequence=0; store assigns authority sequence")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            existing = self.read()
            sequence = existing[-1].sequence + 1 if existing else 1
            assigned = replace(event, sequence=sequence)
            payload = json.dumps(
                assigned.to_json(), sort_keys=True, separators=(",", ":")
            ) + "\n"
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        return assigned

    def read_since(self, sequence: int, *, limit: int = 256) -> tuple[TelemetryEvent, ...]:
        if sequence < 0 or limit < 1 or limit > 1024:
            raise TelemetryError("invalid live-read bounds")
        return tuple(event for event in self.read() if event.sequence > sequence)[:limit]

    def sse_since(self, sequence: int, *, limit: int = 256) -> str:
        frames: list[str] = []
        for event in self.read_since(sequence, limit=limit):
            data = json.dumps(event.to_json(), sort_keys=True, separators=(",", ":"))
            frames.append(f"id: {event.sequence}\nevent: herdr\ndata: {data}\n\n")
        return "".join(frames)

    def materialize(self) -> TelemetryReadModel:
        return materialize(self.read())


def new_event(
    *,
    event_type: EventType,
    issue: str,
    task_id: str,
    agent_id: str,
    role: str,
    attempt: int = 0,
    timestamp: str | None = None,
    **kwargs: object,
) -> TelemetryEvent:
    """Construct a sequence-free event for TelemetryStore.append()."""
    return TelemetryEvent(
        sequence=0,
        timestamp=timestamp or datetime.now(UTC).isoformat(),
        event_type=event_type,
        issue=issue,
        task_id=task_id,
        attempt=attempt,
        agent_id=agent_id,
        role=role,
        **kwargs,
    )
