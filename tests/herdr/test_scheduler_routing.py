"""Offline P1-A managed scheduler routing integration tests."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr.capability import Health
from herdr.evidence import digest
from herdr.routing import FailureKind, FailureScope
from herdr.scheduler import AuditLog, DynamicChildScheduler
from herdr.scheduler_routing import (
    RoutingIntegrationError,
    build_execution_handoff,
    record_managed_route,
    select_managed_task_route,
)
from herdr.security import InvocationIdentity, PolicyDenied
from herdr.work_contract_host import WorkInvocationGuard
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
    registry, scope, requirement, _ = fixture()
    routing = {
        "enabled": enabled,
        "capability_id": requirement.capability_id,
        "policy_version": "router-v5-policy-1",
        "policy_profile": "default",
        "registry_hash": registry.snapshot.hash,
        "scope_hash": scope.hash,
        "requirement_hash": requirement.hash,
        "requirement_tools_sha256": digest(sorted(requirement.tools)),
        "requirement_permissions_sha256": digest(sorted(requirement.permissions)),
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
    task_policy = dict(kwargs["task"].model_policy)
    routing = dict(task_policy["routing_v5"])
    routing["scope_hash"] = kwargs["policy"].hash
    task_policy["routing_v5"] = routing
    kwargs["task"] = replace(kwargs["task"], model_policy=task_policy)
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


def test_unknown_budget_measurement_blocks_routing_but_unrelated_stop_does_not():
    budget = FakeBudgetGate(unknown_measurements=("op-1",))
    with pytest.raises(RoutingIntegrationError, match="budget"):
        select_managed_task_route(**route_kwargs(budget=budget))
    assert budget.calls == []

    scoped_stop = FakeBudgetGate(active_stops=({"scope": "provider", "provider": "unrelated"},))
    route = select_managed_task_route(**route_kwargs(budget=scoped_stop))
    assert route.decision.selected_provider == "a"
    assert scoped_stop.calls == [None, "a"]


def test_selected_provider_budget_stop_blocks_handoff_selection():
    class StopSelectedProvider(FakeBudgetGate):
        def require_active(self, allocation_id, identity, provider=None):
            super().require_active(allocation_id, identity, provider)
            if provider == "a":
                raise RoutingIntegrationError("budget stop for selected provider")

    budget = StopSelectedProvider()
    with pytest.raises(RoutingIntegrationError, match="budget stop"):
        select_managed_task_route(**route_kwargs(budget=budget))
    assert budget.calls == [None, "a"]


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


@pytest.mark.parametrize(
    ("field", "mutated"),
    [
        ("tools", ("search", "write")),
        ("permissions", ("repo:read", "repo:write")),
    ],
)
def test_requirement_cannot_exceed_authoritative_task_or_parent_policy(field, mutated):
    kwargs = route_kwargs()
    kwargs["requirement"] = replace(kwargs["requirement"], **{field: mutated})
    with pytest.raises(RoutingIntegrationError, match="not bound|authoritative requirement|exceed"):
        select_managed_task_route(**kwargs)


def test_requirement_identity_must_match_task_payload():
    kwargs = route_kwargs()
    kwargs["requirement"] = replace(kwargs["requirement"], capability_id="other")
    with pytest.raises(RoutingIntegrationError, match="authoritative requirement"):
        select_managed_task_route(**kwargs)


def test_scope_must_match_authoritative_task_payload():
    kwargs = route_kwargs()
    kwargs["policy"] = replace(kwargs["policy"], providers=("b",))
    with pytest.raises(RoutingIntegrationError, match="scope is not bound"):
        select_managed_task_route(**kwargs)


def test_task_requirement_binding_cannot_be_replaced_by_caller():
    kwargs = route_kwargs()
    task_policy = dict(kwargs["task"].model_policy)
    routing = dict(task_policy["routing_v5"])
    routing["requirement_hash"] = "c" * 64
    task_policy["routing_v5"] = routing
    kwargs["task"] = replace(kwargs["task"], model_policy=task_policy)
    with pytest.raises(RoutingIntegrationError, match="requirement is not bound"):
        select_managed_task_route(**kwargs)


def _scheduled_route(tmp_path: Path):
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
    return scheduler, route


def test_recording_route_is_idempotent_and_does_not_grant_execution(tmp_path: Path):
    scheduler, route = _scheduled_route(tmp_path)
    assert scheduler.record_for(route.routing_input.task_id).state.value == "pending"
    assert record_managed_route(scheduler, route) is True
    assert record_managed_route(scheduler, route) is False
    assert scheduler.record_for(route.routing_input.task_id).state.value == "pending"
    events = [x for x in scheduler.audit_log.replay() if x.get("event") == "routing_decision"]
    assert len(events) == 1
    assert events[0]["task_id"] == route.routing_input.task_id
    assert events[0]["decision_sha256"] == route.decision_sha256


def test_recording_route_is_atomic_under_concurrency(tmp_path: Path):
    scheduler, route = _scheduled_route(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: record_managed_route(scheduler, route), range(32)))
    assert sum(results) == 1
    events = [x for x in scheduler.audit_log.replay() if x.get("event") == "routing_decision"]
    assert len(events) == 1


def test_recording_route_is_idempotent_after_replay(tmp_path: Path):
    scheduler, route = _scheduled_route(tmp_path)
    assert record_managed_route(scheduler, route) is True
    replayed = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    replayed.submit(
        TaskGraph(
            envelope=TaskGraphEnvelope(
                issue="Bbambaaamm/herdr#79",
                spec_hash="sha256:" + "b" * 64,
                graph_version=GRAPH_VERSION,
                created_at=NOW,
                planner="router-test@1",
                policy_profile="default",
            ),
            nodes=(task_node(),),
        ),
        repo="Bbambaaamm/herdr",
        issue="79",
    )
    assert record_managed_route(replayed, route) is False




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



def test_recording_route_rejects_authoritative_task_drift(tmp_path: Path):
    scheduler, _route = _scheduled_route(tmp_path)
    kwargs = route_kwargs()
    alternate_policy = replace(kwargs["policy"], providers=("b",), executors=("b-runtime",))
    alternate_task = task_node()
    altered_policy = dict(alternate_task.model_policy)
    altered_routing = dict(altered_policy["routing_v5"])
    altered_routing["scope_hash"] = alternate_policy.hash
    altered_policy["routing_v5"] = altered_routing
    alternate_task = replace(alternate_task, model_policy=altered_policy)
    alternate_route = select_managed_task_route(
        **{**kwargs, "task": alternate_task, "policy": alternate_policy}
    )
    with pytest.raises(RoutingIntegrationError, match="authoritative TaskNode"):
        record_managed_route(scheduler, alternate_route)
    assert not [row for row in scheduler.audit_log.replay() if row.get("event") == "routing_decision"]


def test_execution_handoff_binds_dispatched_record_and_rechecks_budget(tmp_path: Path):
    node = task_node()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    graph = TaskGraph(
        envelope=TaskGraphEnvelope(
            issue="Bbambaaamm/herdr#79",
            spec_hash="sha256:" + "d" * 64,
            graph_version=GRAPH_VERSION,
            created_at=NOW,
            planner="router-test@1",
            policy_profile="default",
        ),
        nodes=(node,),
    )
    scheduler.submit(graph, repo="Bbambaaamm/herdr", issue="79")
    scheduler.dispatch(task_ids={node.id})
    record = scheduler.record_for(node.id)
    record.parent_agent_id = "agent-parent"
    record.parent_task_id = "parent-task"
    route_args = route_kwargs(
        identity=InvocationIdentity(
            consumer="github:Bbambaaamm/herdr",
            agent_id=record.agent_id,
            parent_agent_id="agent-parent",
            parent_task_id="parent-task",
            task_id=node.id,
            run_token=record.run_token,
            fencing_token=record.lease.fencing_token,
        )
    )
    route = select_managed_task_route(**route_args)
    handoff = scheduler.prepare_managed_execution_handoff(
        route,
        identity=route_args["identity"],
        registry=route_args["registry"],
        requirement=route_args["requirement"],
        policy=route_args["policy"],
        budget_gate=route_args["budget_gate"],
    )
    handoff.authorize(
        identity=route_args["identity"],
        budget_gate=route_args["budget_gate"],
        provider=route.decision.selected_provider,
        model=route.decision.selected_model,
    )
    assert handoff.task_id == node.id
    assert route_args["budget_gate"].calls[-1] == route.decision.selected_provider

    host_guard = object.__new__(WorkInvocationGuard)
    host_guard.grant = SimpleNamespace(identity=route_args["identity"])
    host_guard._routing_handoff = None
    host_guard.bind_routing_handoff(handoff)
    assert host_guard.authorize_routing_model(
        route.decision.selected_provider, route.decision.selected_model
    ) is True
    with pytest.raises(PolicyDenied, match="model_mismatch"):
        host_guard.authorize_routing_model(route.decision.selected_provider, "substitute-model")

    tampered_model = replace(route, decision=replace(route.decision, selected_model="substitute-model"))
    with pytest.raises(RoutingIntegrationError, match="selected capability/model"):
        build_execution_handoff(
            scheduler=scheduler, route=tampered_model,
            identity=route_args["identity"], registry=route_args["registry"],
            requirement=route_args["requirement"], policy=route_args["policy"],
            budget_gate=route_args["budget_gate"],
        )
    tampered_provider = replace(route, decision=replace(route.decision, selected_provider="b"))
    with pytest.raises(RoutingIntegrationError, match="selected capability/model"):
        build_execution_handoff(
            scheduler=scheduler, route=tampered_provider,
            identity=route_args["identity"], registry=route_args["registry"],
            requirement=route_args["requirement"], policy=route_args["policy"],
            budget_gate=route_args["budget_gate"],
        )


def test_execution_handoff_rejects_provider_or_model_switch(tmp_path: Path):
    node = task_node()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    scheduler.submit(
        TaskGraph(
            envelope=TaskGraphEnvelope(
                issue="Bbambaaamm/herdr#79",
                spec_hash="sha256:" + "e" * 64,
                graph_version=GRAPH_VERSION,
                created_at=NOW,
                planner="router-test@1",
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
    ident = InvocationIdentity(
        consumer="github:Bbambaaamm/herdr",
        agent_id=record.agent_id,
        parent_agent_id="agent-parent",
        parent_task_id="parent-task",
        task_id=node.id,
        run_token=record.run_token,
        fencing_token=record.lease.fencing_token,
    )
    kwargs = route_kwargs(identity=ident)
    route = select_managed_task_route(**kwargs)
    handoff = build_execution_handoff(
        scheduler=scheduler, route=route, identity=ident,
        registry=kwargs["registry"], requirement=kwargs["requirement"],
        policy=kwargs["policy"], budget_gate=kwargs["budget_gate"],
    )
    with pytest.raises(RoutingIntegrationError, match="provider mismatch"):
        handoff.authorize(identity=ident, budget_gate=kwargs["budget_gate"], provider="b")
    with pytest.raises(RoutingIntegrationError, match="model mismatch"):
        handoff.authorize(identity=ident, budget_gate=kwargs["budget_gate"], model="other-model")



def test_host_guard_rejects_attribute_only_handoff():
    guard = object.__new__(WorkInvocationGuard)
    guard.grant = SimpleNamespace(identity=identity())
    guard._routing_handoff = None
    fake = SimpleNamespace(
        task_id=guard.grant.identity.task_id,
        run_token=guard.grant.identity.run_token,
        fencing_token=guard.grant.identity.fencing_token,
        selected_provider="a",
        selected_model="reason",
    )
    with pytest.raises(PolicyDenied, match="untrusted_type"):
        guard.bind_routing_handoff(fake)
