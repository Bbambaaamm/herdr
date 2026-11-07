"""P1-D shadow acceptance and offline Router v5 E2E regressions."""
from dataclasses import replace
from pathlib import Path

import pytest

from herdr.routing import FailureKind, FailureScope, classify_failure
from herdr.scheduler import AuditLog, DynamicChildScheduler
from herdr.scheduler_routing import select_managed_task_route
from herdr.shadow_acceptance import (
    ShadowAcceptanceResult,
    ShadowHostGate,
    ShadowOutcome,
    ShadowProviderResult,
    run_shadow_acceptance,
)
from herdr.security import InvocationIdentity, PolicyDenied
from herdr.taskgraph import GRAPH_VERSION, TaskGraph, TaskGraphEnvelope
from tests.herdr.test_capability import NOW
from tests.herdr.test_scheduler_routing import (
    ALLOCATION,
    FakeBudgetGate,
    route_kwargs,
    task_node,
)


def _scheduled(tmp_path: Path):
    node = task_node()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    scheduler.submit(
        TaskGraph(
            envelope=TaskGraphEnvelope(
                issue="Bbambaaamm/herdr#79",
                spec_hash="sha256:" + "d" * 64,
                graph_version=GRAPH_VERSION,
                created_at=NOW,
                planner="shadow-p1d@1",
                policy_profile="default",
            ),
            nodes=(node,),
        ),
        repo="Bbambaaamm/herdr",
        issue="79",
    )
    scheduler.dispatch(task_ids={node.id})
    record = scheduler.record_for(node.id)
    record.parent_agent_id = "agent-parent"
    record.parent_task_id = "parent-task"
    identity = InvocationIdentity(
        consumer="github:Bbambaaamm/herdr",
        agent_id=record.agent_id,
        parent_agent_id="agent-parent",
        parent_task_id="parent-task",
        task_id=node.id,
        run_token=record.run_token,
        fencing_token=record.lease.fencing_token,
    )
    kwargs = route_kwargs(identity=identity)
    route = scheduler.select_managed_route(
        node.id,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=ALLOCATION,
        identity=identity,
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
    )
    return scheduler, route, identity, kwargs


def _host_gate():
    calls = []

    def authorize(handoff, identity):
        handoff.authorize_identity(identity=identity)
        calls.append(handoff.task_id)

    return ShadowHostGate(authorize), calls


def test_e2e_shadow_success_records_static_comparison_and_evidence(tmp_path):
    scheduler, route, identity, kwargs = _scheduled(tmp_path)
    host, host_calls = _host_gate()
    provider_calls = []

    result = run_shadow_acceptance(
        case_id="A-success",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=kwargs["budget_gate"],
        host_gate=host,
        fake_provider=lambda handoff: (
            provider_calls.append((handoff.selected_provider, handoff.selected_model))
            or ShadowProviderResult("success", {"artifact": "fixture"})
        ),
        static_route={"model": "legacy-model", "provider": "legacy"},
    )

    assert result.outcome is ShadowOutcome.PASS
    assert result.provider_calls == 1
    assert result.unauthorized_operations == ()
    assert result.evidence_sha256
    assert host_calls == [route.routing_input.task_id]
    assert provider_calls == [("a", route.decision.selected_model)]
    events = [e for e in scheduler.audit_log.replay() if e.get("event") == "router_v5_shadow_acceptance"]
    assert len(events) == 1
    assert events[0]["economic_operation"] is False
    assert events[0]["credentials_exposed"] is False


def test_shadow_host_denial_blocks_before_fake_provider(tmp_path):
    scheduler, route, identity, kwargs = _scheduled(tmp_path)
    calls = []

    def deny(_handoff, _identity):
        raise PolicyDenied("host_shadow_denied")

    result = run_shadow_acceptance(
        case_id="E-policy-denied",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=kwargs["budget_gate"],
        host_gate=ShadowHostGate(deny),
        fake_provider=lambda _handoff: (
            calls.append(True) or ShadowProviderResult("success", {})
        ),
        static_route={"model": "legacy-model"},
    )

    assert result.outcome is ShadowOutcome.BLOCKED
    assert result.provider_calls == 0
    assert calls == []


def test_shadow_provider_failure_is_not_retried_or_rerouted(tmp_path):
    scheduler, route, identity, kwargs = _scheduled(tmp_path)
    calls = []

    def provider(_handoff):
        calls.append(True)
        return ShadowProviderResult("failure", {"kind": FailureKind.PROVIDER_UNAVAILABLE.value})

    result = run_shadow_acceptance(
        case_id="D-provider-outage",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=kwargs["budget_gate"],
        host_gate=_host_gate()[0],
        fake_provider=provider,
        static_route={"model": "legacy-model"},
    )

    assert result.outcome is ShadowOutcome.BLOCKED
    assert result.provider_calls == 1
    assert calls == [True]


@pytest.mark.parametrize(
    ("status", "message", "expected"),
    [
        (404, "model not found: Laguna", FailureKind.MODEL_NOT_FOUND),
        (404, "Claude Opus 5.5 insufficient credits", FailureKind.INSUFFICIENT_CREDITS),
        (429, "rate limit", FailureKind.RATE_LIMITED),
        (503, "provider unavailable", FailureKind.PROVIDER_UNAVAILABLE),
    ],
)
def test_offline_failure_taxonomy_is_deterministic(status, message, expected):
    assert classify_failure(status_code=status, message=message, model_known=False) is expected


def test_unknown_delivery_and_terminal_denial_remain_non_executable():
    assert classify_failure(message="unknown delivery") is FailureKind.UNKNOWN
    assert classify_failure(status_code=403, message="policy denied") is FailureKind.POLICY_DENIED
    assert classify_failure(status_code=402, message="budget exceeded") is FailureKind.BUDGET_EXCEEDED
    assert FailureScope.ROUTING_WIDE.value == "routing_wide"


def test_shadow_rejects_non_dispatched_task_without_provider(tmp_path):
    node = task_node()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    scheduler.submit(
        TaskGraph(
            envelope=TaskGraphEnvelope(
                issue="Bbambaaamm/herdr#79",
                spec_hash="sha256:" + "e" * 64,
                graph_version=GRAPH_VERSION,
                created_at=NOW,
                planner="shadow-p1d@1",
                policy_profile="default",
            ),
            nodes=(node,),
        ),
        repo="Bbambaaamm/herdr",
        issue="79",
    )
    kwargs = route_kwargs()
    identity = kwargs["identity"]
    route = select_managed_task_route(**kwargs)
    with pytest.raises(ValueError, match="dispatched"):
        run_shadow_acceptance(
            case_id="not-dispatched",
            scheduler=scheduler,
            route=route,
            identity=identity,
            registry=kwargs["registry"],
            requirement=kwargs["requirement"],
            policy=kwargs["policy"],
            budget_gate=kwargs["budget_gate"],
            host_gate=_host_gate()[0],
            fake_provider=lambda _: ShadowProviderResult("success", {}),
            static_route={"model": "legacy-model"},
        )


def test_shadow_is_idempotent_on_replay(tmp_path):
    scheduler, route, identity, kwargs = _scheduled(tmp_path)
    host, _ = _host_gate()

    def provider(handoff):
        return ShadowProviderResult("success", {"model": handoff.selected_model})

    first = run_shadow_acceptance(
        case_id="G-replay",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=kwargs["budget_gate"],
        host_gate=host,
        fake_provider=provider,
        static_route={"model": "legacy-model"},
    )
    second = run_shadow_acceptance(
        case_id="G-replay",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=kwargs["budget_gate"],
        host_gate=host,
        fake_provider=provider,
        static_route={"model": "legacy-model"},
    )
    assert first.evidence_sha256 == second.evidence_sha256
    assert len([e for e in scheduler.audit_log.replay() if e.get("case_id") == "G-replay"]) == 1


@pytest.mark.parametrize("consumer", ["github:Bbambaaamm/herdr"])
def test_consumer_scope_is_carried_without_provider_or_credential_exposure(tmp_path, consumer):
    scheduler, route, identity, kwargs = _scheduled(tmp_path)
    assert identity.consumer == consumer
    host, _ = _host_gate()
    result = run_shadow_acceptance(
        case_id="I-consumer-isolation",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=kwargs["budget_gate"],
        host_gate=host,
        fake_provider=lambda _: ShadowProviderResult("success", {}),
        static_route={"model": "legacy-model"},
    )
    assert result.outcome is ShadowOutcome.PASS
    assert "credentials_exposed" not in result.handoff


class EconomicBudgetGate(FakeBudgetGate):
    def __init__(self, **counters):
        super().__init__()
        self.reserve_calls = counters.get("reserve_calls", 0)
        self.charge_calls = counters.get("charge_calls", 0)
        self.settle_calls = counters.get("settle_calls", 0)


@pytest.mark.parametrize("counter", ["reserve_calls", "charge_calls", "settle_calls"])
def test_shadow_fails_closed_before_provider_for_existing_economic_operation(tmp_path, counter):
    scheduler, route, identity, kwargs = _scheduled(tmp_path)
    budget = EconomicBudgetGate(**{counter: 1})
    provider_calls = []

    result = run_shadow_acceptance(
        case_id=f"pre-{counter}",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=budget,
        host_gate=_host_gate()[0],
        fake_provider=lambda _: (
            provider_calls.append(True) or ShadowProviderResult("success", {})
        ),
        static_route={"model": "legacy-model"},
    )

    assert result.outcome is ShadowOutcome.BLOCKED
    assert result.unauthorized_operations == (counter,)
    assert result.provider_calls == 0
    assert provider_calls == []
    assert result.outcome is not ShadowOutcome.PASS


@pytest.mark.parametrize("counter", ["reserve_calls", "charge_calls", "settle_calls"])
def test_shadow_fails_closed_when_callback_attempts_economic_operation(tmp_path, counter):
    scheduler, route, identity, kwargs = _scheduled(tmp_path)
    budget = EconomicBudgetGate()
    provider_calls = []

    def provider(_handoff):
        provider_calls.append(True)
        setattr(budget, counter, 1)
        return ShadowProviderResult("success", {})

    result = run_shadow_acceptance(
        case_id=f"callback-{counter}",
        scheduler=scheduler,
        route=route,
        identity=identity,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        budget_gate=budget,
        host_gate=_host_gate()[0],
        fake_provider=provider,
        static_route={"model": "legacy-model"},
    )

    assert result.outcome is ShadowOutcome.BLOCKED
    assert result.unauthorized_operations == (counter,)
    assert result.provider_calls == 1
    assert provider_calls == [True]
    assert all(event.get("status") != "PASS" for event in result.events)
