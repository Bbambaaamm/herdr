"""Offline shadow-acceptance harness for Router v5.

The harness exercises the existing TaskGraph/scheduler, handoff, host guard and
budget gate using a caller-supplied fake provider. It records evidence only; it
cannot reserve budget, call a real provider, or change routing policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable, Mapping

from .evidence import digest
from .scheduler_routing import ManagedExecutionHandoff, ManagedRoute, build_execution_handoff
from .security import InvocationIdentity
from .taskgraph import LifecycleState


class ShadowOutcome(StrEnum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ShadowAcceptanceError(ValueError):
    """A shadow-only validation input is not safe to evaluate."""


@dataclass(frozen=True)
class ShadowProviderResult:
    status: str
    artifact: Mapping[str, Any]


@dataclass(frozen=True)
class ShadowAcceptanceResult:
    case_id: str
    outcome: ShadowOutcome
    static_route: Mapping[str, Any]
    shadow_route: Mapping[str, Any]
    handoff: Mapping[str, Any] | None
    provider_calls: int
    unauthorized_operations: tuple[str, ...]
    events: tuple[Mapping[str, Any], ...]
    reason: str

    @property
    def evidence_sha256(self) -> str:
        return digest({
            "case_id": self.case_id,
            "outcome": self.outcome.value,
            "static_route": dict(self.static_route),
            "shadow_route": dict(self.shadow_route),
            "handoff": dict(self.handoff) if self.handoff else None,
            "provider_calls": self.provider_calls,
            "unauthorized_operations": list(self.unauthorized_operations),
            "events": [dict(item) for item in self.events],
            "reason": self.reason,
        })

    def to_json(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "outcome": self.outcome.value,
            "static_route": dict(self.static_route),
            "shadow_route": dict(self.shadow_route),
            "handoff": dict(self.handoff) if self.handoff else None,
            "provider_calls": self.provider_calls,
            "unauthorized_operations": list(self.unauthorized_operations),
            "events": [dict(item) for item in self.events],
            "reason": self.reason,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True)
class ShadowHostGate:
    """Small test seam representing the existing host authorization gate."""

    authorize: Callable[[ManagedExecutionHandoff, InvocationIdentity], None]


def _route_json(route: ManagedRoute) -> dict[str, Any]:
    decision = route.decision
    return {
        "decision_sha256": route.decision_sha256,
        "selected_model": decision.selected_model,
        "selected_provider": decision.selected_provider,
        "selected_executor": decision.selected_executor,
        "failure": decision.failure.value if decision.failure else None,
        "failure_scope": decision.failure_scope.value if decision.failure_scope else None,
        "reasons": list(decision.reasons),
        "rejected_candidates": [item.to_json() for item in decision.rejected_candidates],
    }


def _handoff_json(handoff: ManagedExecutionHandoff) -> dict[str, Any]:
    return {
        "task_id": handoff.task_id,
        "attempt": handoff.attempt,
        "consumer": handoff.consumer,
        "agent_id": handoff.agent_id,
        "selected_executor": handoff.selected_executor,
        "selected_provider": handoff.selected_provider,
        "selected_model": handoff.selected_model,
        "decision_sha256": handoff.decision_sha256,
        "registry_hash": handoff.registry_hash,
        "requirement_hash": handoff.requirement_hash,
        "budget_allocation_id": handoff.budget_allocation_id,
    }


_ECONOMIC_COUNTERS = ("reserve_calls", "charge_calls", "settle_calls")


def _economic_snapshot(budget_gate: Any) -> dict[str, int]:
    """Read optional test/telemetry counters without creating an authority."""
    snapshot: dict[str, int] = {}
    for name in _ECONOMIC_COUNTERS:
        value = getattr(budget_gate, name, 0)
        if type(value) is not int or value < 0:
            raise ShadowAcceptanceError(f"invalid economic counter: {name}")
        snapshot[name] = value
    return snapshot


def _economic_violations(snapshot: Mapping[str, int]) -> tuple[str, ...]:
    """Any nonzero economic counter is forbidden in shadow mode."""
    return tuple(name for name in _ECONOMIC_COUNTERS if snapshot.get(name, 0) != 0)


def run_shadow_acceptance(
    *,
    case_id: str,
    scheduler: Any,
    route: ManagedRoute,
    identity: InvocationIdentity,
    registry: Any,
    requirement: Any,
    policy: Any,
    budget_gate: Any,
    host_gate: ShadowHostGate,
    fake_provider: Callable[[ManagedExecutionHandoff], ShadowProviderResult],
    static_route: Mapping[str, Any],
) -> ShadowAcceptanceResult:
    """Run one deterministic, non-economic shadow case.

    The callback is intentionally a fake-provider seam. It is invoked only after
    the existing scheduler handoff, host identity and WorkBudgetAuthority checks
    succeed. The harness never performs reserve/charge/settle or network I/O.
    """
    if not case_id or not isinstance(static_route, Mapping):
        raise ShadowAcceptanceError("case id and static route required")
    record = scheduler.record_for(route.routing_input.task_id)
    if record.state is not LifecycleState.RUNNING:
        raise ShadowAcceptanceError("shadow acceptance requires a dispatched TaskNode")
    unauthorized: list[str] = []
    events: list[Mapping[str, Any]] = []
    calls = 0
    shadow_route = _route_json(route)
    handoff: ManagedExecutionHandoff | None = None
    before_economic: dict[str, int] = {}
    try:
        handoff = build_execution_handoff(
            scheduler=scheduler,
            route=route,
            identity=identity,
            registry=registry,
            requirement=requirement,
            policy=policy,
            budget_gate=budget_gate,
        )
        host_gate.authorize(handoff, identity)
        handoff.authorize(
            identity=identity,
            budget_gate=budget_gate,
            provider=handoff.selected_provider,
            model=handoff.selected_model,
        )
        before_economic = _economic_snapshot(budget_gate)
        unauthorized.extend(_economic_violations(before_economic))
        if unauthorized:
            raise ShadowAcceptanceError(
                "shadow economic operation detected before fake provider: "
                + ",".join(unauthorized)
            )
        # Count invocation before entering the callback so a callback that
        # mutates a counter and then raises is still recorded as invoked.
        calls = 1
        result = fake_provider(handoff)
        after_economic = _economic_snapshot(budget_gate)
        unauthorized.extend(_economic_violations(after_economic))
        if unauthorized:
            raise ShadowAcceptanceError(
                "shadow economic operation detected after fake provider: "
                + ",".join(unauthorized)
            )
        if not isinstance(result, ShadowProviderResult):
            raise ShadowAcceptanceError("fake provider must return ShadowProviderResult")
        if result.status != "success":
            raise ShadowAcceptanceError("shadow provider did not return success")
        events.append({
            "event": "router_v5_shadow_acceptance",
            "version": 1,
            "case_id": case_id,
            "mode": "SHADOW",
            "task_id": handoff.task_id,
            "attempt": handoff.attempt,
            "static_route": dict(static_route),
            "shadow_route": shadow_route,
            "handoff": _handoff_json(handoff),
            "provider_calls": calls,
            "provider_kind": "FAKE_OFFLINE",
            "economic_operation": False,
            "credentials_exposed": False,
            "result_status": result.status,
        })
        scheduler.audit_log.append_if_absent(
            dict(events[-1]),
            identity_fields=("event", "case_id", "task_id", "attempt"),
        )
        return ShadowAcceptanceResult(
            case_id=case_id,
            outcome=ShadowOutcome.PASS,
            static_route=dict(static_route),
            shadow_route=shadow_route,
            handoff=_handoff_json(handoff),
            provider_calls=calls,
            unauthorized_operations=tuple(unauthorized),
            events=tuple(events),
            reason="offline shadow path completed",
        )
    except Exception as exc:
        try:
            after_economic = _economic_snapshot(budget_gate)
            unauthorized.extend(
                name for name in _economic_violations(after_economic)
                if name not in unauthorized
            )
        except ShadowAcceptanceError:
            pass
        events.append({
            "event": "router_v5_shadow_acceptance",
            "version": 1,
            "case_id": case_id,
            "mode": "SHADOW",
            "task_id": route.routing_input.task_id,
            "shadow_route": shadow_route,
            "provider_calls": calls,
            "economic_operation": bool(unauthorized),
            "unauthorized_operations": list(unauthorized),
            "status": "BLOCKED",
            "reason": str(exc),
        })
        return ShadowAcceptanceResult(
            case_id=case_id,
            outcome=ShadowOutcome.BLOCKED,
            static_route=dict(static_route),
            shadow_route=shadow_route,
            handoff=_handoff_json(handoff) if handoff else None,
            provider_calls=calls,
            unauthorized_operations=tuple(unauthorized),
            events=tuple(events),
            reason=str(exc),
        )
