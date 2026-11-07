from dataclasses import replace
from pathlib import Path

import pytest

from herdr.evidence import digest
from herdr.fallback_recovery import (
    ProviderFailureObservation,
    RecoveryAction,
    decide_managed_fallback,
)
from herdr.routing import FailureKind, FailureScope, ScopeAttestation
from herdr.scheduler import AuditLog, DynamicChildScheduler
from herdr.scheduler_routing import select_managed_task_route
from herdr.security import InvocationIdentity
from herdr.taskgraph import GRAPH_VERSION, TaskGraph, TaskGraphEnvelope
from tests.herdr.test_capability import NOW, fixture
from tests.herdr.test_scheduler_routing import ALLOCATION, FakeBudgetGate, identity, route_kwargs, task_node


def _scheduled(tmp_path: Path):
    node = task_node()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    scheduler.submit(
        TaskGraph(
            envelope=TaskGraphEnvelope(
                issue="Bbambaaamm/herdr#79",
                spec_hash="sha256:" + "a" * 64,
                graph_version=GRAPH_VERSION,
                created_at=NOW,
                planner="router-p1c-test@1",
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
    return scheduler, node, ident, kwargs, route


def _attestation(executor_id: str, registry_hash: str, requirement_hash: str):
    return ScopeAttestation.for_context(
        executor_id,
        FailureScope.CANDIDATE_LOCAL,
        "provider-boundary",
        registry_hash,
        requirement_hash,
    )


def test_laguna_404_model_not_found_falls_back_only_with_trusted_scope(tmp_path):
    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)
    attestation = _attestation(
        "a-runtime", kwargs["registry"].snapshot.hash, kwargs["requirement"].hash
    )
    transition = decide_managed_fallback(
        scheduler,
        task_id=node.id,
        route=route,
        observation=ProviderFailureObservation(
            executor_id="a-runtime",
            status_code=404,
            message="model not found: Laguna",
            model_known=False,
            scope=FailureScope.CANDIDATE_LOCAL,
            scope_attestation=attestation,
        ),
        identity=ident,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=ALLOCATION,
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
        fallback_count=0,
        max_fallbacks=1,
    )
    assert transition.action is RecoveryAction.FALLBACK
    assert transition.failure is FailureKind.MODEL_NOT_FOUND
    assert transition.handoff is not None
    assert transition.handoff.selected_executor == "b-runtime"


def test_claude_404_insufficient_credits_is_terminal(tmp_path):
    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)
    transition = decide_managed_fallback(
        scheduler,
        task_id=node.id,
        route=route,
        observation=ProviderFailureObservation(
            executor_id="a-runtime",
            status_code=404,
            message="Claude Opus 5.5 insufficient credits",
            model_known=True,
            scope=FailureScope.CANDIDATE_LOCAL,
            scope_attestation=_attestation(
                "a-runtime", kwargs["registry"].snapshot.hash, kwargs["requirement"].hash
            ),
        ),
        identity=ident,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=ALLOCATION,
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
        fallback_count=0,
        max_fallbacks=1,
    )
    assert transition.action is RecoveryAction.FALLBACK
    assert transition.failure is FailureKind.INSUFFICIENT_CREDITS
    assert transition.handoff is not None
    assert transition.handoff.selected_executor == "b-runtime"


@pytest.mark.parametrize(
    "observation",
    [
        ProviderFailureObservation(
            executor_id="a-runtime",
            status_code=503,
            message="provider unavailable",
            scope=FailureScope.CANDIDATE_LOCAL,
        ),
        ProviderFailureObservation(
            executor_id="a-runtime",
            status_code=429,
            message="rate limit",
            scope=FailureScope.UNKNOWN,
        ),
    ],
)
def test_missing_or_untrusted_scope_blocks_fallback(tmp_path, observation):
    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)
    transition = decide_managed_fallback(
        scheduler,
        task_id=node.id,
        route=route,
        observation=observation,
        identity=ident,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=ALLOCATION,
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
        fallback_count=0,
        max_fallbacks=1,
    )
    assert transition.action is RecoveryAction.BLOCK
    assert transition.handoff is None


def test_unknown_delivery_requires_reconciliation_before_fallback(tmp_path):
    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)
    transition = decide_managed_fallback(
        scheduler,
        task_id=node.id,
        route=route,
        observation=ProviderFailureObservation(
            executor_id="a-runtime",
            status_code=503,
            message="provider unavailable",
            delivery_uncertain=True,
        ),
        identity=ident,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=ALLOCATION,
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
        fallback_count=0,
        max_fallbacks=1,
    )
    assert transition.action is RecoveryAction.RECONCILE
    assert transition.reconciliation_required is True


def test_duplicate_recovery_replay_is_idempotent_in_existing_audit_log(tmp_path):
    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)
    observation = ProviderFailureObservation(
        executor_id="a-runtime",
        status_code=503,
        message="provider unavailable",
        delivery_uncertain=True,
    )
    args = dict(
        scheduler=scheduler,
        task_id=node.id,
        route=route,
        observation=observation,
        identity=ident,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=ALLOCATION,
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
        fallback_count=0,
        max_fallbacks=1,
    )
    first = decide_managed_fallback(**args)
    second = decide_managed_fallback(**args)
    scheduler.audit_log.flush()
    events = [row for row in scheduler.audit_log.replay() if row.get("event") == "managed_fallback_transition"]
    assert first.action is RecoveryAction.RECONCILE
    assert second.action is RecoveryAction.RECONCILE
    assert len(events) == 1



def test_terminal_budget_or_policy_denial_cannot_fallback_even_if_scope_claimed(tmp_path):
    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)
    attestation = _attestation(
        "a-runtime", kwargs["registry"].snapshot.hash, kwargs["requirement"].hash
    )
    for message in ("budget exceeded", "policy denied"):
        transition = decide_managed_fallback(
            scheduler,
            task_id=node.id,
            route=route,
            observation=ProviderFailureObservation(
                executor_id="a-runtime",
                message=message,
                scope=FailureScope.CANDIDATE_LOCAL,
                scope_attestation=attestation,
            ),
            identity=ident,
            registry=kwargs["registry"],
            requirement=kwargs["requirement"],
            policy=kwargs["policy"],
            runtime_state=kwargs["runtime_state"],
            at=kwargs["at"],
            policy_version=kwargs["policy_version"],
            budget_gate=kwargs["budget_gate"],
            budget_allocation_id=ALLOCATION,
            expected_registry_hash=kwargs["expected_registry_hash"],
            expected_requirement_hash=kwargs["expected_requirement_hash"],
            fallback_count=0,
            max_fallbacks=1,
        )
        assert transition.action is RecoveryAction.BLOCK
        assert transition.handoff is None
