"""Offline P1-A managed scheduler routing integration tests."""
from dataclasses import replace
from pathlib import Path

import pytest

from herdr.capability import Health
from herdr.routing import FailureKind, FailureScope
from herdr.scheduler import AuditLog, DynamicChildScheduler
from herdr.scheduler_routing import (
    RoutingIntegrationError,
    record_managed_route,
    select_managed_task_route,
)
from herdr.security import InvocationIdentity
from herdr.taskgraph import GRAPH_VERSION, TaskGraph, TaskGraphEnvelope, TaskNode
from tests.herdr.test_capability import NOW, fixture


ALLOCATION = "a" * 64


class FakeBudgetGate:
    def __init__(self, *, active_stops=(), unknown_measurements=()):
        self.calls = []
        self._snapshot = {
            "version": 1,
            "allocation_id": ALLOCATION,
            "charged_upper_bounds": {
                "work_ms": 0,
                "model_calls": 0,
                "tokens": 0,
                "cost_microusd": 0,
            },
            "inflight": {},
            "unknown_measurements": list(unknown_measurements),
            "implementation_attempts": 0,
            "fallbacks": 0,
            "variants": 0,
            "trials": 0,
            "instabilities": [],
            "counters": {},
            "implementation_retries": 0,
            "active_stops": list(active_stops),
        }

    def snapshot(self, allocation_id):
        assert allocation_id == ALLOCATION
        return dict(self._snapshot)

    def require_active(self, allocation_id, identity, provider=None):
        assert allocation_id == ALLOCATION
        assert isinstance(identity, InvocationIdentity)
        self.calls.append(provider)


def task_node(*, enabled=True, task_id="task-router-1"):
    routing = {
        "enabled": enabled,
        "capability_id": "reason",
        "policy_version": "router-v5-policy-1",
    }
    return TaskNode(
        id=task_id,
        parent_id=None,
        type="task",
        role="writer",
        objective="offline router selection",
        inputs=[{"artifact_ref": "fixture"}],
        expected_outputs=[{"kind": "result"}],
        dependencies=[],
        priority=1,
        resource_class="small",
        model_policy={"model": "legacy-model", "fallback_model": "legacy-fallback", "routing_v5": routing},
        tools=("search",),
        permissions=("repo:read",),
        timeout_seconds=120,
        max_attempts=2,
    )


def identity(task_id="task-router-1"):
    return InvocationIdentity(
        consumer="github:Bbambaaamm/herdr",
        agent_id="agent-router",
        parent_agent_id="agent-parent",
        parent_task_id="parent-task",
        task_id=task_id,
        run_token="run-router-1",
        fencing_token=1,
    )


def inputs():
    registry, scope, requirement, states = fixture()
    return registry, scope, requirement, states


def route_kwargs(budget=None, **overrides):
    registry, scope, requirement, states = inputs()
    budget = budget or FakeBudgetGate()
    return {
        "task": task_node(),
        "registry": registry,
        "requirement": requirement,
        "policy": scope,
        "runtime_state": states,
        "at": NOW,
        "policy_version": "router-v5-policy-1",
        "policy_profile": "default",
        "budget_gate": budget,
        "budget_allocation_id": ALLOCATION,
        "identity": identity(),
        "expected_registry_hash": registry.snapshot.hash,
        "expected_requirement_hash": requirement.hash,
        **overrides,
    }


def test_p1a_selects_compatible_executor_and_does_not_dispatch():
    budget = FakeBudgetGate()
    route = select_managed_task_route(**route_kwargs(budget=budget))
    assert route.decision.selected_executor == "a-runtime"
    assert route.decision.selected_provider == "a"
    assert route.routing_input.task_id == "task-router-1"
    assert route.routing_input.parent_scope_hash == route_kwargs()["policy"].hash
    assert budget.calls == [None, "a"]


def test_static_model_policy_is_not_implicitly_rerouted():
    kwargs = route_kwargs()
    kwargs["task"] = task_node(enabled=False)
    with pytest.raises(RoutingIntegrationError, match="not enabled"):
        select_managed_task_route(**kwargs)


def test_missing_capability_and_unauthorized_provider_are_fail_closed():
    registry, scope, requirement, states = inputs()
    budget = FakeBudgetGate()
    kwargs = route_kwargs(budget=budget, policy=replace(scope, providers=("ghost-provider",)))
    route = select_managed_task_route(**kwargs)
    assert route.decision.selected_executor is None
    assert route.decision.failure is FailureKind.POLICY_DENIED
    assert route.decision.failure_scope is FailureScope.UNKNOWN
    assert budget.calls == [None]


def test_stale_registry_snapshot_and_changed_requirement_hash_stop_before_budget_selection():
    registry, scope, requirement, states = inputs()
    budget = FakeBudgetGate()
    kwargs = route_kwargs(budget=budget, expected_registry_hash="b" * 64)
    with pytest.raises(RoutingIntegrationError, match="stale registry"):
        select_managed_task_route(**kwargs)
    kwargs = route_kwargs(budget=budget, expected_requirement_hash="b" * 64)
    with pytest.raises(RoutingIntegrationError, match="changed requirement"):
        select_managed_task_route(**kwargs)
    assert budget.calls == []


def test_unknown_budget_measurement_or_active_stop_blocks_routing():
    for budget in (FakeBudgetGate(unknown_measurements=("op-1",)), FakeBudgetGate(active_stops=({"id": "stop"},))):
        with pytest.raises(RoutingIntegrationError, match="budget"):
            select_managed_task_route(**route_kwargs(budget=budget))
        assert budget.calls == []


def test_explicit_candidate_local_scope_only_applies_to_retryable_failure():
    budget = FakeBudgetGate()
    kwargs = route_kwargs(
        budget=budget,
        failed_executors={"a-runtime": FailureKind.PROVIDER_UNAVAILABLE},
        failed_scopes={"a-runtime": FailureScope.CANDIDATE_LOCAL},
        attempt=2,
    )
    route = select_managed_task_route(**kwargs)
    assert route.decision.selected_executor == "b-runtime"
    assert route.decision.attempted_fallbacks == ("a-runtime",)
    assert budget.calls == [None, "b"]


def test_recording_route_is_idempotent_and_does_not_grant_execution(tmp_path: Path):
    node = task_node()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    graph = TaskGraph(
        envelope=TaskGraphEnvelope(
            issue="Bbambaaamm/herdr#79",
            spec_hash="sha256:" + "b" * 64,
            graph_version=GRAPH_VERSION,
            created_at=NOW,
            planner="router-test@1",
            policy_profile="default",
        ),
        nodes=(node,),
    )
    scheduler.submit(graph, repo="Bbambaaamm/herdr", issue="79")
    kwargs = route_kwargs()
    route = scheduler.select_managed_route(
        node.id,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=kwargs["budget_allocation_id"],
        identity=kwargs["identity"],
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
    )
    assert scheduler.record_for(node.id).state.value == "pending"
    assert record_managed_route(scheduler, route) is True
    assert record_managed_route(scheduler, route) is False
    assert scheduler.record_for(node.id).state.value == "pending"
    events = [x for x in scheduler.audit_log.replay() if x.get("event") == "routing_decision"]
    assert len(events) == 1
    assert events[0]["task_id"] == node.id
    assert events[0]["decision_sha256"] == route.decision_sha256




def test_scheduler_wrapper_rejects_consumer_scope_drift(tmp_path: Path):
    node = task_node()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    graph = TaskGraph(
        envelope=TaskGraphEnvelope(
            issue="Bbambaaamm/herdr#79",
            spec_hash="sha256:" + "c" * 64,
            graph_version=GRAPH_VERSION,
            created_at=NOW,
            planner="router-test@1",
            policy_profile="default",
        ),
        nodes=(node,),
    )
    scheduler.submit(graph, repo="Bbambaaamm/herdr", issue="79")
    kwargs = route_kwargs(identity=InvocationIdentity(
        consumer="github:other/repo",
        agent_id="agent-router",
        parent_agent_id="agent-parent",
        parent_task_id="parent-task",
        task_id=node.id,
        run_token="run-router-1",
        fencing_token=1,
    ))
    with pytest.raises(RoutingIntegrationError, match="consumer"):
        scheduler.select_managed_route(
            node.id,
            registry=kwargs["registry"],
            requirement=kwargs["requirement"],
            policy=kwargs["policy"],
            runtime_state=kwargs["runtime_state"],
            at=kwargs["at"],
            policy_version=kwargs["policy_version"],
            budget_gate=kwargs["budget_gate"],
            budget_allocation_id=kwargs["budget_allocation_id"],
            identity=kwargs["identity"],
            expected_registry_hash=kwargs["expected_registry_hash"],
            expected_requirement_hash=kwargs["expected_requirement_hash"],
        )

def test_routing_input_rejects_identity_drift():
    kwargs = route_kwargs(identity=identity("other-task"))
    with pytest.raises(RoutingIntegrationError, match="bind to task"):
        select_managed_task_route(**kwargs)
