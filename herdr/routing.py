"""Deterministic, offline Router v5 decision contract.

This module consumes the existing :mod:`herdr.capability` registry only.  It
never discovers providers, calls model APIs, or changes scheduler state.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Sequence

from .capability import (
    CapabilityMatch,
    CapabilityRegistry,
    CapabilityRequirement,
    CapabilityScope,
    Reason,
    RuntimeStateSnapshot,
)
from .telemetry import EventType, TelemetryEvent

ROUTING_SCHEMA_VERSION = "1.0.0"
_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]{1,256}$")


class RoutingError(ValueError):
    """Invalid routing contract input."""


class FailureKind(StrEnum):
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    POLICY_DENIED = "POLICY_DENIED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    UNKNOWN = "UNKNOWN"


class FailureScope(StrEnum):
    CANDIDATE_LOCAL = "candidate_local"
    ROUTING_WIDE = "routing_wide"


# Mapping input order is not an execution trace. Terminal failures therefore
# use this explicit stable precedence; attempted_fallbacks is a sorted set.
_FAILURE_PRECEDENCE = {
    FailureKind.POLICY_DENIED: 80,
    FailureKind.BUDGET_EXCEEDED: 70,
    FailureKind.INSUFFICIENT_CREDITS: 60,
    FailureKind.MODEL_NOT_FOUND: 50,
    FailureKind.CAPABILITY_MISMATCH: 40,
    FailureKind.RATE_LIMITED: 30,
    FailureKind.PROVIDER_UNAVAILABLE: 20,
    FailureKind.UNKNOWN: 10,
}


def _token(value: str, field: str) -> None:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise RoutingError(f"{field} must be a safe token")


def _digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class RejectedCandidate:
    executor_id: str
    provider_id: str
    model: str
    reason: str
    failure: FailureKind | None = None
    scope: FailureScope = FailureScope.CANDIDATE_LOCAL

    def __post_init__(self) -> None:
        for name in ("executor_id", "provider_id", "model", "reason"):
            _token(getattr(self, name), name)
        if self.failure is not None:
            object.__setattr__(self, "failure", FailureKind(self.failure))
        object.__setattr__(self, "scope", FailureScope(self.scope))

    def to_json(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "provider_id": self.provider_id,
            "model": self.model,
            "reason": self.reason,
            "failure": self.failure.value if self.failure else None,
            "scope": self.scope.value,
        }


@dataclass(frozen=True)
class RoutingDecision:
    """Versioned immutable result of one deterministic offline routing attempt."""

    policy_version: str
    registry_hash: str
    requirement_hash: str
    selected_model: str | None
    selected_provider: str | None
    selected_executor: str | None
    reasons: tuple[str, ...]
    rejected_candidates: tuple[RejectedCandidate, ...] = ()
    # Sorted executor IDs for prior failures; this is an unordered aggregate,
    # not an execution-order trace.
    attempted_fallbacks: tuple[str, ...] = ()
    failure: FailureKind | None = None
    failure_scope: FailureScope | None = None
    attempts: int = 0
    max_attempts: int = 1
    schema_version: str = ROUTING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != ROUTING_SCHEMA_VERSION:
            raise RoutingError("incompatible routing decision schema")
        for name in ("policy_version", "registry_hash", "requirement_hash"):
            _token(getattr(self, name), name)
        for name in ("selected_model", "selected_provider", "selected_executor"):
            value = getattr(self, name)
            if value is not None:
                _token(value, name)
        selected = (self.selected_model, self.selected_provider, self.selected_executor)
        if any(value is None for value in selected) and any(value is not None for value in selected):
            raise RoutingError("selected model, provider and executor must be all present or all absent")
        if self.selected_model is not None and self.failure is not None:
            raise RoutingError("selected route cannot carry a failure")
        if self.selected_model is None and self.failure is None:
            raise RoutingError("failed decision without selected route requires failure")
        if not isinstance(self.reasons, (tuple, list)) or not self.reasons:
            raise RoutingError("reasons must be non-empty")
        for reason in self.reasons:
            _token(reason, "reason")
        if not isinstance(self.rejected_candidates, (tuple, list)):
            raise RoutingError("rejected_candidates must be a sequence")
        rejected = tuple(self.rejected_candidates)
        if any(not isinstance(item, RejectedCandidate) for item in rejected):
            raise RoutingError("rejected_candidates must be typed")
        object.__setattr__(self, "rejected_candidates", rejected)
        attempted = tuple(self.attempted_fallbacks)
        for executor_id in attempted:
            _token(executor_id, "attempted_fallback")
        if len(attempted) != len(set(attempted)):
            raise RoutingError("attempted_fallbacks contains duplicates")
        object.__setattr__(self, "attempted_fallbacks", attempted)
        object.__setattr__(self, "reasons", tuple(self.reasons))
        if self.failure is not None:
            object.__setattr__(self, "failure", FailureKind(self.failure))
            object.__setattr__(self, "failure_scope", FailureScope(self.failure_scope or FailureScope.CANDIDATE_LOCAL))
        elif self.failure_scope is not None:
            raise RoutingError("failure_scope requires failure")
        if type(self.attempts) is not int or self.attempts < 0:
            raise RoutingError("attempts must be non-negative")
        if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 16:
            raise RoutingError("max_attempts must be bounded")
        if self.attempts > self.max_attempts:
            raise RoutingError("attempts cannot exceed max_attempts")

    @property
    def digest(self) -> str:
        return _digest(self.to_json(include_digest=False))

    def to_json(self, *, include_digest: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "registry_hash": self.registry_hash,
            "requirement_hash": self.requirement_hash,
            "selected_model": self.selected_model,
            "selected_provider": self.selected_provider,
            "selected_executor": self.selected_executor,
            "reasons": list(self.reasons),
            "rejected_candidates": [item.to_json() for item in self.rejected_candidates],
            "attempted_fallbacks": list(self.attempted_fallbacks),
            "failure": self.failure.value if self.failure else None,
            "failure_scope": self.failure_scope.value if self.failure_scope else None,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
        }
        if include_digest:
            data["decision_sha256"] = self.digest
        return data

    @classmethod
    def from_json(cls, raw: Mapping[str, Any], *, trusted: bool = True) -> "RoutingDecision":
        values = dict(raw)
        expected = values.pop("decision_sha256", None)
        if trusted and expected is None:
            raise RoutingError("trusted routing decision requires decision_sha256")
        values["reasons"] = tuple(values["reasons"])
        values["rejected_candidates"] = tuple(
            RejectedCandidate(
                executor_id=item["executor_id"],
                provider_id=item["provider_id"],
                model=item["model"],
                reason=item["reason"],
                failure=item.get("failure"),
                scope=item.get("scope", FailureScope.CANDIDATE_LOCAL),
            )
            for item in values["rejected_candidates"]
        )
        values["attempted_fallbacks"] = tuple(values.get("attempted_fallbacks", ()))
        decision = cls(**values)
        if expected is not None and expected != decision.digest:
            raise RoutingError("routing decision digest mismatch")
        return decision

    def to_telemetry_event(
        self,
        *,
        sequence: int,
        timestamp: str,
        issue: str,
        task_id: str,
        attempt: int,
        agent_id: str,
        role: str,
    ) -> TelemetryEvent:
        """Project the decision into the existing closed telemetry contract."""
        fallback = self.attempted_fallbacks
        event_type = EventType.MODEL_FALLBACK if fallback else EventType.MODEL_ROUTE
        return TelemetryEvent(
            sequence=sequence,
            timestamp=timestamp,
            event_type=event_type,
            issue=issue,
            task_id=task_id,
            attempt=attempt,
            agent_id=agent_id,
            role=role,
            provider=self.selected_provider,
            model=self.selected_model,
            router_decision=self.digest,
            fallback_chain=fallback,
            reason=self.reasons[0],
            blocker=self.failure.value if self.failure else None,
        )


def classify_failure(
    *,
    status_code: int | None = None,
    message: str = "",
    model_known: bool | None = None,
) -> FailureKind:
    """Classify provider observations without contacting a provider.

    Credit errors win over status-code heuristics so a 404 carrying an explicit
    insufficient-credit response cannot be misreported as a missing model.
    """
    text = message.lower()
    # Explicit authorization and budget denials are terminal for the stated
    # candidate and must not be masked by transport/status heuristics.
    if "policy denied" in text or "permission denied" in text:
        return FailureKind.POLICY_DENIED
    if "budget exceeded" in text or "budget limit" in text:
        return FailureKind.BUDGET_EXCEEDED
    if any(term in text for term in ("insufficient credit", "insufficient funds", "credit exhausted",
                                     "credits exhausted", "billing limit", "payment required")):
        return FailureKind.INSUFFICIENT_CREDITS
    if any(term in text for term in ("rate limit", "too many requests", "quota exceeded")) or status_code == 429:
        return FailureKind.RATE_LIMITED
    if any(term in text for term in ("model not found", "unknown model", "no such model",
                                     "model does not exist")) or (status_code == 404 and model_known is False):
        return FailureKind.MODEL_NOT_FOUND
    if status_code in (502, 503, 504) or any(term in text for term in ("provider unavailable",
                                                                         "service unavailable",
                                                                         "temporarily unavailable",
                                                                         "upstream timeout")):
        return FailureKind.PROVIDER_UNAVAILABLE
    if "capability mismatch" in text:
        return FailureKind.CAPABILITY_MISMATCH
    return FailureKind.UNKNOWN


def classify_failure_scope(message: str) -> FailureScope:
    """Classify whether an explicit denial applies to one candidate or the route."""
    text = message.lower()
    if any(term in text for term in ("task-wide", "routing-wide", "global policy", "all candidates", "entire task")):
        return FailureScope.ROUTING_WIDE
    return FailureScope.CANDIDATE_LOCAL


def _reason_failure(reason: Reason) -> FailureKind:
    if reason in (Reason.POLICY_DENIED, Reason.DATA_POLICY_DENIED):
        return FailureKind.POLICY_DENIED
    if reason is Reason.BUDGET_EXCEEDED:
        return FailureKind.BUDGET_EXCEEDED
    if reason is Reason.RATE_LIMITED:
        return FailureKind.RATE_LIMITED
    if reason is Reason.RUNTIME_UNAVAILABLE:
        return FailureKind.PROVIDER_UNAVAILABLE
    return FailureKind.CAPABILITY_MISMATCH


def _terminal_failure(
    failed: Mapping[str, FailureKind], rejections: Sequence[Any]
) -> FailureKind:
    candidates = list(failed.values())
    candidates.extend(_reason_failure(item.reason) for item in rejections)
    if not candidates:
        return FailureKind.CAPABILITY_MISMATCH
    return max(candidates, key=lambda item: (_FAILURE_PRECEDENCE[item], item.value))


def _model_for(registry: CapabilityRegistry, match: CapabilityMatch) -> str:
    caps = {item.id: item for item in registry.snapshot.capabilities}
    return caps[match.capability_id].spec_id


def _rejection_for_registry(
    registry: CapabilityRegistry,
    executor_id: str | None,
    reason: Reason,
) -> RejectedCandidate:
    executors = {item.id: item for item in registry.snapshot.executors}
    providers = {item.id: item for item in registry.snapshot.providers}
    caps = {item.id: item for item in registry.snapshot.capabilities}
    if executor_id is None or executor_id not in executors:
        return RejectedCandidate(
            executor_id="unknown",
            provider_id="unknown",
            model="unknown",
            reason=reason.value,
            failure=_reason_failure(reason),
        )
    executor = executors[executor_id]
    return RejectedCandidate(
        executor_id=executor.id,
        provider_id=executor.provider_id,
        model=caps[executor.capability_id].spec_id,
        reason=reason.value,
        failure=_reason_failure(reason),
    )


def select_route(
    registry: CapabilityRegistry,
    requirement: CapabilityRequirement,
    policy: CapabilityScope,
    runtime_state: Sequence[RuntimeStateSnapshot],
    *,
    at: str,
    policy_version: str,
    max_attempts: int = 1,
    failed_executors: Mapping[str, FailureKind] | None = None,
    failed_scopes: Mapping[str, FailureScope] | None = None,
) -> RoutingDecision:
    """Select a route from the existing registry, deterministically and offline."""
    if max_attempts < 1 or max_attempts > 16:
        raise RoutingError("max_attempts must be between 1 and 16")
    failed = {key: FailureKind(value) for key, value in (failed_executors or {}).items()}
    scopes = {key: FailureScope(value) for key, value in (failed_scopes or {}).items()}
    if set(scopes) - set(failed):
        raise RoutingError("failed_scopes contains an executor without a failure")
    result = registry.candidates(requirement, policy, tuple(runtime_state), at=at)
    known_ids = {item.id for item in registry.snapshot.executors}
    rejection_by_id = {item.executor_id: item.reason for item in result.rejections if item.executor_id}
    eligible_ids = {item.executor_id for item in result.matches}
    runtime_reasons = {Reason.RUNTIME_UNAVAILABLE, Reason.RUNTIME_STALE, Reason.RUNTIME_MISSING, Reason.RATE_LIMITED}
    invalid_failed = sorted(
        executor_id for executor_id in failed
        if executor_id not in known_ids
        or (executor_id not in eligible_ids and rejection_by_id.get(executor_id) not in runtime_reasons)
    )
    if invalid_failed:
        raise RoutingError("failed executor is not compatible with the current routing context: " + ",".join(invalid_failed))
    routing_wide = any(scopes.get(executor_id, FailureScope.CANDIDATE_LOCAL) is FailureScope.ROUTING_WIDE
                       for executor_id in failed)
    rejected = [_rejection_for_registry(registry, item.executor_id, item.reason) for item in result.rejections]
    for executor_id, failure in sorted(failed.items()):
        match = next((item for item in result.matches if item.executor_id == executor_id), None)
        if match is not None:
            rejected.append(RejectedCandidate(
                executor_id=executor_id,
                provider_id=match.provider_id,
                model=_model_for(registry, match),
                reason="fallback:" + failure.value,
                failure=failure,
                scope=scopes.get(executor_id, FailureScope.CANDIDATE_LOCAL),
            ))
        else:
            executor = next(item for item in registry.snapshot.executors if item.id == executor_id)
            provider = next(item for item in registry.snapshot.providers if item.id == executor.provider_id)
            capability = next(item for item in registry.snapshot.capabilities if item.id == executor.capability_id)
            rejected.append(RejectedCandidate(
                executor_id=executor.id,
                provider_id=provider.id,
                model=capability.spec_id,
                reason="fallback:" + failure.value,
                failure=failure,
                scope=scopes.get(executor_id, FailureScope.CANDIDATE_LOCAL),
            ))
    exhausted = len(failed) >= max_attempts or routing_wide
    available = [] if exhausted else [item for item in result.matches if item.executor_id not in failed]
    available.sort(key=lambda item: (-item.preference_score, item.executor_id))
    if available and len(available) > 0:
        chosen = available[0]
        model = _model_for(registry, chosen)
        reasons = ("preferred_provider" if chosen.preference_score else "deterministic_registry_order",)
        if failed:
            reasons = reasons + ("bounded_fallback",)
        return RoutingDecision(
            policy_version=policy_version,
            registry_hash=result.registry_hash,
            requirement_hash=requirement.hash,
            selected_model=model,
            selected_provider=chosen.provider_id,
            selected_executor=chosen.executor_id,
            reasons=reasons,
            rejected_candidates=tuple(rejected),
            attempted_fallbacks=tuple(sorted(failed)),
            attempts=min(len(failed) + 1, max_attempts),
            max_attempts=max_attempts,
        )
    if failed or result.rejections:
        failure = _terminal_failure(failed, result.rejections)
    elif requirement.legacy_model_hints and not available:
        failure = FailureKind.MODEL_NOT_FOUND
    else:
        failure = FailureKind.CAPABILITY_MISMATCH
    reasons = tuple(item.reason for item in rejected) or ("no_compatible_candidate",)
    return RoutingDecision(
        policy_version=policy_version,
        registry_hash=result.registry_hash,
        requirement_hash=requirement.hash,
        selected_model=None,
        selected_provider=None,
        selected_executor=None,
        reasons=reasons,
        rejected_candidates=tuple(rejected),
        attempted_fallbacks=tuple(sorted(failed)),
        failure=failure,
        failure_scope=FailureScope.ROUTING_WIDE if routing_wide else FailureScope.CANDIDATE_LOCAL,
        attempts=min(len(failed), max_attempts),
        max_attempts=max_attempts,
    )


def bounded_fallback(
    registry: CapabilityRegistry,
    requirement: CapabilityRequirement,
    policy: CapabilityScope,
    runtime_state: Sequence[RuntimeStateSnapshot],
    *,
    at: str,
    policy_version: str,
    failed_executors: Mapping[str, FailureKind],
    failed_scopes: Mapping[str, FailureScope] | None = None,
    max_attempts: int = 3,
) -> RoutingDecision:
    """Retry only compatible registry candidates and stop at a fixed bound."""
    if len(failed_executors) >= max_attempts:
        return select_route(
            registry, requirement, policy, runtime_state, at=at,
            policy_version=policy_version, max_attempts=max_attempts,
            failed_executors=failed_executors, failed_scopes=failed_scopes,
        )
    return select_route(
        registry, requirement, policy, runtime_state, at=at,
        policy_version=policy_version, max_attempts=max_attempts,
        failed_executors=failed_executors, failed_scopes=failed_scopes,
    )
