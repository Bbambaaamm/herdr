"""Pure task-local reasoning-state contracts for Execution Fabric (#95).

This module intentionally owns no durable store, scheduler, memory, permission
or final completion authority. It materializes a bounded current projection
from host-validated append-only events. A future #95 ExecutionEvent stream may
persist these events; replay must remain deterministic.

LongHarness-inspired working evidence is not #85 EvidenceBundle and is not
#105 long-term memory.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from itertools import islice
from typing import Iterable

from .context import SecretRedactor, SourceRef, SourceState
from .security import InvocationIdentity

VERSION = 1
MAX_EVENTS = 2048
MAX_EVIDENCE = 256
MAX_CLAIMS = 256
MAX_GAPS = 128
MAX_SOURCES = 16
MAX_TEXT_BYTES = 8192
MAX_EVENT_BYTES = 131072
MAX_PROJECTION_BYTES = 4 * 1024 * 1024
MAX_REPLAY_BYTES = 16 * 1024 * 1024

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")


class ReasoningStateError(ValueError):
    """Bounded fail-closed contract error without source bytes."""


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise ReasoningStateError(code)


def _text(value: object, code: str, maximum: int = MAX_TEXT_BYTES) -> str:
    _need(type(value) is str and value and len(value) <= maximum
          and not any(ord(char) < 32 and char not in "\n\t" for char in value), code)
    try:
        _need(len(value.encode("utf-8")) <= maximum, code)
    except UnicodeError:
        raise ReasoningStateError(code) from None
    _need(SecretRedactor().redact(value) == value, code + "_secret")
    return value


def _identifier(value: object, code: str) -> str:
    _need(type(value) is str and _ID.fullmatch(value) is not None and ".." not in value, code)
    _need(SecretRedactor().redact(value) == value, code + "_secret")
    return value


def _reason(value: object) -> str:
    return _identifier(value, "reason_code")


def _bounded(values: Iterable, maximum: int, code: str) -> tuple:
    """Never exhaust an unbounded iterable; one extra element proves overflow.

    The host must still supply iterators whose individual next() calls terminate.
    This pure contract does not execute arbitrary iterators in a process sandbox.
    """
    _need(not isinstance(values, (str, bytes, dict)), code)
    try:
        result = tuple(islice(iter(values), maximum + 1))
    except Exception:
        raise ReasoningStateError(code) from None
    _need(len(result) <= maximum, code)
    return result


def _enum(typ, value: object, code: str):
    _need(type(value) in (str, typ) and len(value) <= 128, code)
    try:
        return typ(value)
    except (TypeError, ValueError):
        raise ReasoningStateError(code) from None


def _keys(value: object, expected: set[str], code: str) -> None:
    _need(type(value) is dict and len(value) == len(expected) and set(value) == expected, code)


def _identity(value: object) -> InvocationIdentity:
    _need(type(value) is InvocationIdentity, "reasoning_identity")
    try:
        raw = value.to_json()
        for name, item in raw.items():
            if name != "fencing_token":
                _need(type(item) is str and len(item) <= 256, "reasoning_identity")
                _need(SecretRedactor().redact(item) == item, "reasoning_identity_secret")
        InvocationIdentity.from_dict(raw)
    except (TypeError, ValueError):
        raise ReasoningStateError("reasoning_identity") from None
    return value


def _identity_from_json(value: object) -> InvocationIdentity:
    _keys(value, {"consumer", "agent_id", "parent_agent_id", "parent_task_id",
                  "task_id", "run_token", "fencing_token"}, "reasoning_identity")
    _need(all(type(item) is str and len(item) <= 256
              for name, item in value.items() if name != "fencing_token"), "reasoning_identity")
    try:
        return _identity(InvocationIdentity.from_dict(value))
    except (TypeError, ValueError):
        raise ReasoningStateError("reasoning_identity") from None


def _ids(values: Iterable[str], maximum: int, code: str) -> tuple[str, ...]:
    result = _bounded(values, maximum, code)
    for value in result:
        _identifier(value, code)
    _need(len(set(result)) == len(result), code)
    return result


def _canonical(value: object, maximum: int = MAX_PROJECTION_BYTES) -> bytes:
    try:
        result = bytearray()
        encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False, allow_nan=False)
        for chunk in encoder.iterencode(value):
            encoded = chunk.encode("utf-8")
            _need(len(result) + len(encoded) <= maximum, "reasoning_bytes_bound")
            result.extend(encoded)
        return bytes(result)
    except ReasoningStateError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ReasoningStateError("reasoning_state_not_canonical") from None


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _source_json(source: SourceRef) -> dict[str, object]:
    _need(type(source) is SourceRef, "source_ref_schema")
    try:
        raw = {name: getattr(source, name) for name in (
            "uri", "sha256", "project", "revision", "data_class", "state", "holdout_series")}
        for name, item in raw.items():
            _need((name == "holdout_series" and item is None)
                  or isinstance(item, str) and len(item) <= 2048, "source_ref_schema")
        checked = SourceRef(**raw)
        value = asdict(checked)
        _need(SecretRedactor().tree(value) == value, "source_ref_secret")
        value["data_class"] = checked.data_class.value
        value["state"] = checked.state.value
    except (TypeError, ValueError, UnicodeError):
        raise ReasoningStateError("source_ref_schema") from None
    return value


def _source_from_json(value: object) -> SourceRef:
    _keys(value, {"uri", "sha256", "project", "revision", "data_class", "state", "holdout_series"},
          "source_ref_schema")
    _need(all((name == "holdout_series" and item is None)
              or isinstance(item, str) and len(item) <= 2048
              for name, item in value.items()), "source_ref_schema")
    try:
        result = SourceRef(**value)
        _source_json(result)
        return result
    except (TypeError, ValueError, UnicodeError):
        raise ReasoningStateError("source_ref_schema") from None


class EvidenceLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"


class ClaimState(StrEnum):
    SUPPORTED = "SUPPORTED"
    CONTESTED = "CONTESTED"
    UNKNOWN = "UNKNOWN"


class ReasoningEventKind(StrEnum):
    EVIDENCE_ADDED = "evidence_added"
    EVIDENCE_RETRACTED = "evidence_retracted"
    CLAIM_UPSERTED = "claim_upserted"
    GAP_UPSERTED = "gap_upserted"
    GAP_RESOLVED = "gap_resolved"


@dataclass(frozen=True)
class WorkingEvidenceEntry:
    evidence_id: str
    statement: str
    sources: tuple[SourceRef, ...]
    state: EvidenceLifecycle = EvidenceLifecycle.ACTIVE
    superseded_by: str | None = None
    reason_code: str = "accepted_candidate"

    def __post_init__(self) -> None:
        _identifier(self.evidence_id, "evidence_id")
        _text(self.statement, "evidence_statement")
        object.__setattr__(self, "sources", _bounded(self.sources, MAX_SOURCES, "evidence_sources"))
        _need(1 <= len(self.sources) <= MAX_SOURCES
              and all(type(source) is SourceRef for source in self.sources),
              "evidence_sources")
        object.__setattr__(self, "sources", tuple(_source_from_json(_source_json(x)) for x in self.sources))
        object.__setattr__(self, "state", _enum(EvidenceLifecycle, self.state, "evidence_state"))
        if self.state is EvidenceLifecycle.ACTIVE:
            _need(all(source.state in {SourceState.VERIFIED, SourceState.UNVERIFIED}
                      for source in self.sources), "active_evidence_source_state")
        if self.superseded_by is not None:
            _identifier(self.superseded_by, "superseded_by")
            _need(self.superseded_by != self.evidence_id, "evidence_self_supersession")
        _reason(self.reason_code)
        _need((self.state is EvidenceLifecycle.SUPERSEDED) == (self.superseded_by is not None),
              "evidence_supersession_binding")

    @property
    def statement_sha256(self) -> str:
        self.__post_init__()
        return hashlib.sha256(self.statement.encode("utf-8")).hexdigest()

    def to_json(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "evidence_id": self.evidence_id,
            "statement": self.statement,
            "statement_sha256": self.statement_sha256,
            "sources": [_source_json(source) for source in self.sources],
            "state": self.state.value,
            "superseded_by": self.superseded_by,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class ConclusionClaim:
    claim_id: str
    statement: str
    state: ClaimState
    evidence_ids: tuple[str, ...]
    reason_code: str

    def __post_init__(self) -> None:
        _identifier(self.claim_id, "claim_id")
        _text(self.statement, "claim_statement")
        object.__setattr__(self, "state", _enum(ClaimState, self.state, "claim_state"))
        object.__setattr__(self, "evidence_ids", _ids(self.evidence_ids, 64, "claim_evidence_ids"))
        _reason(self.reason_code)
        _need(self.state is ClaimState.UNKNOWN or bool(self.evidence_ids),
              "claim_support_required")

    @property
    def statement_sha256(self) -> str:
        self.__post_init__()
        return hashlib.sha256(self.statement.encode("utf-8")).hexdigest()

    def to_json(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "statement_sha256": self.statement_sha256,
            "state": self.state.value,
            "evidence_ids": list(self.evidence_ids),
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class OpenGap:
    gap_id: str
    question: str
    reason_code: str

    def __post_init__(self) -> None:
        _identifier(self.gap_id, "gap_id")
        _text(self.question, "gap_question", maximum=4096)
        _reason(self.reason_code)

    def to_json(self) -> dict[str, object]:
        self.__post_init__()
        return asdict(self)


@dataclass(frozen=True)
class ReasoningEvent:
    identity: InvocationIdentity
    sequence: int
    kind: ReasoningEventKind
    data: bytes | dict[str, object]

    def _validate_header(self) -> None:
        _identity(self.identity)
        _need(type(self.sequence) is int and 1 <= self.sequence <= MAX_EVENTS,
              "reasoning_event_sequence")
        object.__setattr__(self, "kind", _enum(ReasoningEventKind, self.kind, "reasoning_event_kind"))

    def __post_init__(self) -> None:
        self._validate_header()
        _need(type(self.data) is dict, "reasoning_event_data")
        normalized = self._validate_data(self.data)
        raw = _canonical(normalized, MAX_EVENT_BYTES)
        object.__setattr__(self, "data", raw)
        self.to_json()

    def _payload(self) -> dict[str, object]:
        self._validate_header()
        _need(type(self.data) is bytes and len(self.data) <= MAX_EVENT_BYTES, "reasoning_event_bytes")
        try:
            value = json.loads(self.data)
        except (TypeError, ValueError, UnicodeError, RecursionError):
            raise ReasoningStateError("reasoning_event_data") from None
        normalized = self._validate_data(value)
        _need(_canonical(normalized, MAX_EVENT_BYTES) == self.data, "reasoning_event_not_canonical")
        return normalized

    def _validate_data(self, data: dict[str, object]) -> dict[str, object]:
        if self.kind is ReasoningEventKind.EVIDENCE_ADDED:
            expected = {"evidence_id", "statement", "sources", "supersedes", "reason_code"}
            _keys(data, expected, "evidence_added_schema")
            _identifier(data["evidence_id"], "evidence_id")
            _text(data["statement"], "evidence_statement")
            _reason(data["reason_code"])
            raw_sources = data["sources"]
            _need(type(raw_sources) is list and 1 <= len(raw_sources) <= MAX_SOURCES,
                  "evidence_sources")
            sources = tuple(_source_from_json(item) for item in raw_sources)
            _need(all(source.state in {SourceState.VERIFIED, SourceState.UNVERIFIED}
                      for source in sources), "active_evidence_source_state")
            raw_supersedes = data["supersedes"]
            _need(type(raw_supersedes) is list, "evidence_supersedes")
            raw_supersedes = _ids(raw_supersedes, 16, "evidence_supersedes")
            return {
                "evidence_id": data["evidence_id"],
                "statement": data["statement"],
                "sources": [_source_json(source) for source in sources],
                "supersedes": list(raw_supersedes),
                "reason_code": data["reason_code"],
            }

        if self.kind is ReasoningEventKind.EVIDENCE_RETRACTED:
            _keys(data, {"evidence_id", "reason_code"}, "evidence_retracted_schema")
            _identifier(data["evidence_id"], "evidence_id")
            _reason(data["reason_code"])
            return data

        if self.kind is ReasoningEventKind.CLAIM_UPSERTED:
            expected = {"claim_id", "statement", "state", "evidence_ids", "reason_code"}
            _keys(data, expected, "claim_upserted_schema")
            _identifier(data["claim_id"], "claim_id")
            _text(data["statement"], "claim_statement")
            state = _enum(ClaimState, data["state"], "claim_state")
            raw_ids = data["evidence_ids"]
            _need(type(raw_ids) is list, "claim_evidence_ids")
            raw_ids = _ids(raw_ids, 64, "claim_evidence_ids")
            _need(state is ClaimState.UNKNOWN or bool(raw_ids), "claim_support_required")
            _reason(data["reason_code"])
            return {**data, "state": state.value, "evidence_ids": list(raw_ids)}

        if self.kind is ReasoningEventKind.GAP_UPSERTED:
            _keys(data, {"gap_id", "question", "reason_code"}, "gap_upserted_schema")
            _identifier(data["gap_id"], "gap_id")
            _text(data["question"], "gap_question", maximum=4096)
            _reason(data["reason_code"])
            return data

        if self.kind is ReasoningEventKind.GAP_RESOLVED:
            _keys(data, {"gap_id", "reason_code"}, "gap_resolved_schema")
            _identifier(data["gap_id"], "gap_id")
            _reason(data["reason_code"])
            return data

        raise ReasoningStateError("reasoning_event_kind")

    @classmethod
    def evidence_added(cls, identity: InvocationIdentity, sequence: int, *,
                       evidence_id: str, statement: str, sources: Iterable[SourceRef],
                       supersedes: Iterable[str] = (), reason_code: str = "accepted_candidate") -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.EVIDENCE_ADDED, {
            "evidence_id": evidence_id,
            "statement": statement,
            "sources": [_source_json(source) for source in _bounded(sources, MAX_SOURCES, "evidence_sources")],
            "supersedes": list(_ids(supersedes, 16, "evidence_supersedes")),
            "reason_code": reason_code,
        })

    @classmethod
    def evidence_retracted(cls, identity: InvocationIdentity, sequence: int, *,
                           evidence_id: str, reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.EVIDENCE_RETRACTED, {
            "evidence_id": evidence_id, "reason_code": reason_code,
        })

    @classmethod
    def claim_upserted(cls, identity: InvocationIdentity, sequence: int, *,
                       claim_id: str, statement: str, state: ClaimState,
                       evidence_ids: Iterable[str] = (), reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.CLAIM_UPSERTED, {
            "claim_id": claim_id,
            "statement": statement,
            "state": _enum(ClaimState, state, "claim_state").value,
            "evidence_ids": list(_ids(evidence_ids, 64, "claim_evidence_ids")),
            "reason_code": reason_code,
        })

    @classmethod
    def gap_upserted(cls, identity: InvocationIdentity, sequence: int, *,
                     gap_id: str, question: str, reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.GAP_UPSERTED, {
            "gap_id": gap_id, "question": question, "reason_code": reason_code,
        })

    @classmethod
    def gap_resolved(cls, identity: InvocationIdentity, sequence: int, *,
                     gap_id: str, reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.GAP_RESOLVED, {
            "gap_id": gap_id, "reason_code": reason_code,
        })

    def to_json(self) -> dict[str, object]:
        payload = self._payload()
        result = {
            "version": VERSION,
            "identity": self.identity.to_json(),
            "sequence": self.sequence,
            "kind": self.kind.value,
            "data": payload,
        }
        _canonical(result, MAX_EVENT_BYTES)
        return result

    @classmethod
    def from_json(cls, value: object) -> "ReasoningEvent":
        _keys(value, {"version", "identity", "sequence", "kind", "data"}, "reasoning_event_schema")
        _need(type(value["version"]) is int and value["version"] == VERSION, "reasoning_event_schema")
        try:
            identity = _identity_from_json(value["identity"])
            result = cls(identity, value["sequence"], value["kind"], value["data"])
            result.to_json()
            return result
        except ReasoningStateError:
            raise
        except (TypeError, ValueError):
            raise ReasoningStateError("reasoning_event_schema") from None


@dataclass(frozen=True)
class ReasoningProjection:
    identity: InvocationIdentity
    last_sequence: int
    evidence: tuple[WorkingEvidenceEntry, ...]
    claims: tuple[ConclusionClaim, ...]
    open_gaps: tuple[OpenGap, ...]

    def __post_init__(self) -> None:
        _identity(self.identity)
        _need(type(self.last_sequence) is int and 1 <= self.last_sequence <= MAX_EVENTS,
              "reasoning_projection_sequence")
        for field_name, typ, maximum in (
            ("evidence", WorkingEvidenceEntry, MAX_EVIDENCE),
            ("claims", ConclusionClaim, MAX_CLAIMS),
            ("open_gaps", OpenGap, MAX_GAPS),
        ):
            values = _bounded(getattr(self, field_name), maximum, "reasoning_projection_bound")
            _need(all(type(item) is typ for item in values),
                  "reasoning_projection_bound")
            for item in values:
                item.__post_init__()
            key = {"evidence": "evidence_id", "claims": "claim_id", "open_gaps": "gap_id"}[field_name]
            _need(len({getattr(item, key) for item in values}) == len(values),
                  "reasoning_duplicate_" + field_name)
            object.__setattr__(self, field_name, tuple(sorted(values, key=lambda x: getattr(x, key))))
        evidence = {item.evidence_id: item for item in self.evidence}
        # A supersession may point to later-retired history, but not to a
        # missing entry, itself or a cycle. No recursion on adversarial graphs.
        for entry in self.evidence:
            seen = {entry.evidence_id}
            target = entry.superseded_by
            while target is not None:
                _need(target in evidence, "reasoning_supersession_missing")
                _need(target not in seen, "reasoning_supersession_cycle")
                seen.add(target)
                target = evidence[target].superseded_by
        for claim in self.claims:
            _need(all(item in evidence and evidence[item].state is EvidenceLifecycle.ACTIVE
                      for item in claim.evidence_ids), "claim_nonactive_evidence")
            if claim.state is ClaimState.SUPPORTED:
                _need(all(source.state is SourceState.VERIFIED
                          for item in claim.evidence_ids for source in evidence[item].sources),
                      "supported_claim_unverified_source")
        _canonical(self._payload(), MAX_PROJECTION_BYTES)

    @property
    def active_evidence(self) -> tuple[WorkingEvidenceEntry, ...]:
        self.__post_init__()
        return tuple(item for item in self.evidence if item.state is EvidenceLifecycle.ACTIVE)

    @property
    def supported_claims(self) -> tuple[ConclusionClaim, ...]:
        self.__post_init__()
        return tuple(item for item in self.claims if item.state is ClaimState.SUPPORTED)

    def _payload(self) -> dict[str, object]:
        return {
            "version": VERSION,
            "identity": self.identity.to_json(),
            "last_sequence": self.last_sequence,
            "evidence": [item.to_json() for item in self.evidence],
            "claims": [item.to_json() for item in self.claims],
            "open_gaps": [item.to_json() for item in self.open_gaps],
        }

    def to_json(self) -> dict[str, object]:
        self.__post_init__()
        return self._payload()

    @property
    def hash(self) -> str:
        return _digest(self.to_json())


def _downgrade_claims(claims: dict[str, ConclusionClaim], retired: set[str]) -> None:
    for claim_id, claim in tuple(claims.items()):
        if retired.intersection(claim.evidence_ids):
            remaining = tuple(item for item in claim.evidence_ids if item not in retired)
            claims[claim_id] = replace(
                claim,
                state=(ClaimState.UNKNOWN if claim.state is ClaimState.SUPPORTED or not remaining
                       else claim.state),
                evidence_ids=remaining,
                reason_code="support_retired",
            )


def materialize(events: Iterable[ReasoningEvent], *,
                expected_identity: InvocationIdentity | None = None) -> ReasoningProjection:
    """Project one complete bounded prefix, without executing or accepting work.

    expected_identity is supplied by the host, never inferred from a provider
    session. This compares identity/fence only, not WorkPlan/policy freshness.
    """
    items = _bounded(events, MAX_EVENTS, "reasoning_events_bound")
    _need(1 <= len(items) and all(type(event) is ReasoningEvent for event in items),
          "reasoning_events_bound")
    identity = items[0].identity
    if expected_identity is not None:
        _need(_identity(expected_identity) == identity, "reasoning_identity_stale")
    evidence: dict[str, WorkingEvidenceEntry] = {}
    claims: dict[str, ConclusionClaim] = {}
    gaps: dict[str, OpenGap] = {}
    replay_bytes = 0

    for expected, event in enumerate(items, start=1):
        payload = event.to_json()
        replay_bytes += len(_canonical(payload, MAX_EVENT_BYTES))
        _need(replay_bytes <= MAX_REPLAY_BYTES, "reasoning_replay_bytes")
        _need(event.identity == identity, "reasoning_identity_changed")
        _need(event.sequence == expected, "reasoning_sequence_gap")
        data = payload["data"]

        if event.kind is ReasoningEventKind.EVIDENCE_ADDED:
            evidence_id = data["evidence_id"]
            _need(evidence_id not in evidence, "duplicate_evidence_id")
            supersedes = tuple(data["supersedes"])
            _need(evidence_id not in supersedes, "evidence_self_supersession")
            for old_id in supersedes:
                _need(old_id in evidence and evidence[old_id].state is EvidenceLifecycle.ACTIVE,
                      "superseded_evidence_not_active")
            sources = tuple(_source_from_json(value) for value in data["sources"])
            entry = WorkingEvidenceEntry(
                evidence_id=evidence_id,
                statement=data["statement"],
                sources=sources,
                reason_code=data["reason_code"],
            )
            evidence[evidence_id] = entry
            retired: set[str] = set()
            for old_id in supersedes:
                old = evidence[old_id]
                evidence[old_id] = replace(
                    old,
                    state=EvidenceLifecycle.SUPERSEDED,
                    superseded_by=evidence_id,
                    reason_code="superseded",
                )
                retired.add(old_id)
            _downgrade_claims(claims, retired)

        elif event.kind is ReasoningEventKind.EVIDENCE_RETRACTED:
            evidence_id = data["evidence_id"]
            _need(evidence_id in evidence and evidence[evidence_id].state is EvidenceLifecycle.ACTIVE,
                  "retracted_evidence_not_active")
            evidence[evidence_id] = replace(
                evidence[evidence_id],
                state=EvidenceLifecycle.RETRACTED,
                superseded_by=None,
                reason_code=data["reason_code"],
            )
            _downgrade_claims(claims, {evidence_id})

        elif event.kind is ReasoningEventKind.CLAIM_UPSERTED:
            ids = tuple(data["evidence_ids"])
            _need(all(item in evidence and evidence[item].state is EvidenceLifecycle.ACTIVE for item in ids),
                  "claim_nonactive_evidence")
            state = ClaimState(data["state"])
            if state is ClaimState.SUPPORTED:
                _need(bool(ids), "claim_support_required")
                _need(all(source.state is SourceState.VERIFIED
                          for item in ids for source in evidence[item].sources),
                      "supported_claim_unverified_source")
            claim = ConclusionClaim(
                claim_id=data["claim_id"],
                statement=data["statement"],
                state=state,
                evidence_ids=ids,
                reason_code=data["reason_code"],
            )
            claims[claim.claim_id] = claim
            _need(len(claims) <= MAX_CLAIMS, "reasoning_claim_bound")

        elif event.kind is ReasoningEventKind.GAP_UPSERTED:
            gap = OpenGap(data["gap_id"], data["question"], data["reason_code"])
            gaps[gap.gap_id] = gap
            _need(len(gaps) <= MAX_GAPS, "reasoning_gap_bound")

        elif event.kind is ReasoningEventKind.GAP_RESOLVED:
            gap_id = data["gap_id"]
            _need(gap_id in gaps, "resolved_gap_missing")
            del gaps[gap_id]

        _need(len(evidence) <= MAX_EVIDENCE, "reasoning_evidence_bound")

    return ReasoningProjection(
        identity=identity,
        last_sequence=len(items),
        evidence=tuple(evidence[key] for key in sorted(evidence)),
        claims=tuple(claims[key] for key in sorted(claims)),
        open_gaps=tuple(gaps[key] for key in sorted(gaps)),
    )
