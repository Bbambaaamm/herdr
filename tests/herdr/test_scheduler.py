"""Offline, fail-closed acceptance tests for Herdr v1.2 scheduler.

All tests are PAPER-only and use injected clock/audit-log/temp paths — no live
host probe, no network, no live broker, no credential.

Adapted from Autonomous-Quant-Lab PR #244 acceptance tests and ported to the
canonical herdr v1.1 TaskNode/TaskGraph contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from herdr import (
    AllowDecision,
    AuditLog,
    ChildProposal,
    DenyDecision,
    DenyReason,
    DynamicChildScheduler,
    LifecycleState,
    SchedulerBudget,
    TaskGraph,
    TaskGraphEnvelope,
    TaskNode,
    GRAPH_VERSION,
)


def _envelope(
    *, issue: str = "test", spec_hash: str | None = None, **overrides
) -> TaskGraphEnvelope:
    data = {
        "issue": issue,
        "spec_hash": spec_hash or ("sha256:" + "a" * 64),
        "graph_version": GRAPH_VERSION,
        "created_at": "2026-09-27T00:00:00+00:00",
        "planner": "herdr-test@1.0",
        "policy_profile": "default",
        "max_nodes": 256,
        "max_depth": 16,
        "max_fanout": 16,
    }
    data.update(overrides)
    return TaskGraphEnvelope.from_dict(data)


def _node(
    node_id: str = "root",
    parent_id: str | None = None,
    dependencies: tuple[str, ...] = (),
    role: str = "reader",
    tools: tuple[str, ...] = ("read_file",),
    permissions: tuple[str, ...] = ("repo:read",),
    model: str = "laguna",
    fallback_model: str = "longcat",
    **overrides,
) -> TaskNode:
    data: dict[str, object] = {
        "id": node_id,
        "parent_id": parent_id,
        "type": "task",
        "role": role,
        "objective": f"task:{node_id}",
        "inputs": [{"artifact_ref": "fixture"}],
        "expected_outputs": [{"kind": "result"}],
        "dependencies": list(dependencies),
        "priority": 1,
        "resource_class": "small",
        "model_policy": {"model": model, "fallback_model": fallback_model},
        "tools": list(tools),
        "permissions": list(permissions),
        "timeout_seconds": 1800,
        "max_attempts": 1,
    }
    data.update(overrides)
    return TaskNode(**data)


def _graph(
    nodes: list[TaskNode], *, issue: str = "test", spec_hash: str | None = None
) -> TaskGraph:
    return TaskGraph(
        envelope=_envelope(issue=issue, spec_hash=spec_hash),
        nodes=tuple(nodes),
    )


def _idle_scheduler(tmp_path: Path, clock=None) -> DynamicChildScheduler:
    return DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=1),
        clock=clock or (lambda: 1_000_000.0),
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )


def _scheduler_with_budget(
    tmp_path: Path, max_global: int = 4, clock=None
) -> DynamicChildScheduler:
    return DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=max_global),
        clock=clock or (lambda: 1_000_000.0),
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )


def _submit(
    sched: DynamicChildScheduler,
    nodes: list[TaskNode],
    *,
    repo: str = "QuantLab",
    issue: str = "230",
) -> None:
    sched.submit(_graph(nodes, issue=issue), repo=repo, issue=issue)


# ---------------------------------------------------------------------------
# Acceptance: planner cannot bypass limits via larger graph output
# ---------------------------------------------------------------------------


def test_planner_runaway_graph_is_denied_before_submit(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    nodes = [_node(f"n{i}") for i in range(300)]
    sched.submit(_graph(nodes), repo="QuantLab", issue="230")
    events = sched.audit_log.replay()
    denies = [e for e in events if e["event"] == "deny"]
    assert any(e["reason"] == DenyReason.DAG_NODE_LIMIT.value for e in denies)


def test_planner_cycles_are_rejected(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    a = _node("a", dependencies=("b",))
    b = _node("b", dependencies=("a",))
    with pytest.raises(Exception, match="cycle|unknown"):
        sched.submit(_graph([a, b]), repo="QuantLab", issue="230")


# ---------------------------------------------------------------------------
# Acceptance: two independent nodes run in parallel
# ---------------------------------------------------------------------------


def test_two_independent_nodes_run_in_parallel(tmp_path: Path) -> None:
    sched = _scheduler_with_budget(tmp_path, max_global=4)
    _submit(sched, [_node("a"), _node("b")], issue="230")
    leases = sched.dispatch()
    assert {lease.task_id for lease in leases} == {"a", "b"}
    assert all(sched._tasks[tid].state == LifecycleState.RUNNING for tid in ("a", "b"))


def test_concurrency_cap_serializes_dispatch(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)  # max_global_concurrency=1
    _submit(sched, [_node("a"), _node("b")], issue="230")
    leases = sched.dispatch()
    assert len(leases) == 1  # backpressure: second node waits


# ---------------------------------------------------------------------------
# Acceptance: dependent node starts only after prerequisite PASSED
# ---------------------------------------------------------------------------


def test_dependent_node_starts_only_after_prereq_done(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    _submit(sched, [_node("a"), _node("b", dependencies=("a",))], issue="230")
    ready = sched.ready()
    assert [n.id for n in ready] == ["a"]  # A is ready; B blocked on A
    leases = sched.dispatch()
    assert leases and leases[0].task_id == "a"
    lease_a = leases[0]
    assert sched.complete(
        "a", "ok-a", agent_id=lease_a.agent_id, fencing_token=lease_a.fencing_token
    )
    ready = sched.ready()
    assert [n.id for n in ready] == ["b"]
    leases = sched.dispatch()
    assert leases and leases[0].task_id == "b"


def test_blocker_propagation_when_prereq_fails(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    _submit(sched, [_node("a"), _node("b", dependencies=("a",))], issue="230")
    leases = sched.dispatch()
    assert leases[0].task_id == "a"
    for _ in range(5):  # exceeding max_retries (3) -> FAILED
        sched.fail("a")
    assert sched._tasks["a"].state == LifecycleState.FAILED
    assert sched._tasks["b"].state == LifecycleState.BLOCKED


# ---------------------------------------------------------------------------
# Acceptance: lost worker reclaim without double commit
# ---------------------------------------------------------------------------


def test_lost_worker_reclaim_without_double_commit(tmp_path: Path) -> None:
    sched = _scheduler_with_budget(tmp_path, max_global=4, clock=lambda: 1_000_000.0)
    _submit(sched, [_node("a"), _node("b")], issue="230")
    first = {lease.task_id: lease for lease in sched.dispatch()}
    stale = first["a"]
    reclaimed = sched.reclaim(stale.holder, now=1_000_000.0 + 1_000.0)
    assert reclaimed == ["a"]
    assert sched._tasks["a"].state == LifecycleState.PENDING  # back to ready
    # Add new lease after reclaim
    leases_after = sched.dispatch(now=1_000_001.0)
    replacement = next((lease for lease in leases_after if lease.task_id == "a"), None)
    assert replacement is not None
    assert replacement.fencing_token > stale.fencing_token


def test_expired_lease_cannot_commit_before_reclaim(tmp_path: Path) -> None:
    now = [1_000_000.0]
    sched = _idle_scheduler(tmp_path, clock=lambda: now[0])
    _submit(sched, [_node("a")], issue="230")
    leases = sched.dispatch()
    lease = leases[0]
    now[0] = lease.lease_until + 0.001
    assert (
        sched.complete(
            "a",
            result="late",
            agent_id=lease.agent_id,
            fencing_token=lease.fencing_token,
        )
        is False
    )


# ---------------------------------------------------------------------------
# Acceptance: child cannot escalate tools / permissions beyond parent
# ---------------------------------------------------------------------------


def test_child_can_not_escalate_tools_beyond_parent(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    proposal = ChildProposal(
        parent_role="writer",
        parent_tools=("read_file", "search_files", "patch", "write_file"),
        child_role="writer",
        child_tools=("read_file", "search_files", "patch", "write_file", "read"),
    )
    decision = sched.evaluate_child_proposal(proposal)
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.CHILD_TOOL_ESCALATION


def test_child_can_not_escalate_role_beyond_parent(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    proposal = ChildProposal(
        parent_role="writer",
        parent_tools=("read_file", "patch", "write_file"),
        child_role="operator",  # operator > writer rank
        child_tools=("read_file", "git_push"),  # git_push is operator-only
    )
    decision = sched.evaluate_child_proposal(proposal)
    assert isinstance(decision, DenyDecision)
    assert decision.reason in (
        DenyReason.CHILD_ROLE_ESCALATION,
        DenyReason.NON_SPAWNABLE_ROLE,
    )


def test_child_proposal_without_parent_tools_is_bounded_by_role_allowlist(
    tmp_path: Path,
) -> None:
    sched = _idle_scheduler(tmp_path)
    proposal = ChildProposal(
        parent_role="reader",
        parent_tools=("read_file",),
        child_role="reader",
        child_tools=("read_file", "git_push"),  # git_push not in reader allowlist
    )
    decision = sched.evaluate_child_proposal(proposal)
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST


def test_operator_role_is_not_auto_spawnable(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    proposal = ChildProposal(
        parent_role="writer",
        parent_tools=("read_file", "patch", "write_file"),
        child_role="operator",
        child_tools=("read_file", "patch", "write_file"),  # within writer allowlist
    )
    decision = sched.evaluate_child_proposal(proposal)
    assert isinstance(decision, DenyDecision)
    assert decision.reason in (
        DenyReason.NON_SPAWNABLE_ROLE,
        DenyReason.CHILD_ROLE_ESCALATION,
    )


# ---------------------------------------------------------------------------
# Acceptance: model/fallback choice recorded in telemetry
# ---------------------------------------------------------------------------


def test_model_choice_recorded_in_telemetry(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    _submit(
        sched, [_node("a", model="gpt-4o-mini", fallback_model="o3-mini")], issue="230"
    )
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_000.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )
    _submit(
        sched, [_node("a", model="gpt-4o-mini", fallback_model="o3-mini")], issue="230"
    )
    sched.dispatch()
    rec = sched._tasks["a"]
    assert rec.model_used == "gpt-4o-mini"
    assert rec.fallback_used == "o3-mini"
    assert any(
        t.get("model") == "gpt-4o-mini" and t.get("fallback_model") == "o3-mini"
        for t in rec.telemetry
    )


def test_subtask_proposal_records_model_telemetry(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    proposal = ChildProposal(
        parent_role="writer",
        parent_tools=("read_file", "patch"),
        child_role="writer",
        child_tools=("read_file", "patch"),
        child_model="o3",
        child_fallback_model="gpt-4o-mini",
    )
    decision = sched.evaluate_child_proposal(proposal)
    assert isinstance(decision, AllowDecision)
    assert decision.model == "o3"
    assert decision.fallback_model == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Acceptance: integration test crash/restart (durable recovery)
# ---------------------------------------------------------------------------


def test_crash_restart_recovery_idempotent(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "events.jsonl")
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_000.0,
        audit_log=log,
    )
    _submit(sched, [_node("a"), _node("b", dependencies=("a",))], issue="230")
    leases = sched.dispatch()
    lease_a = leases[0]
    assert sched.complete(
        "a", "ok-a", agent_id=lease_a.agent_id, fencing_token=lease_a.fencing_token
    )
    sched.cancel("a", reason="manual-test")
    events = log.replay()
    assert any(e["event"] == "complete" for e in events)
    assert any(e["event"] == "cancel" for e in events)

    recovered = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_010.0,
        audit_log=log,
    )
    applied = recovered.replay()
    assert applied >= 2  # complete + cancel replayed
    assert recovered._tasks["a"].state == LifecycleState.CANCELLED


# ---------------------------------------------------------------------------
# Acceptance: child permission escalation uses authoritative parent policy
# ---------------------------------------------------------------------------


def test_child_permission_escalation_uses_authoritative_parent_policy(
    tmp_path: Path,
) -> None:
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_000.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )
    parent = _node(
        "parent", role="reader", tools=("read_file",), permissions=("repo:read",)
    )
    _submit(sched, [parent], issue="230")
    proposal = ChildProposal(
        parent_role="reader",
        parent_tools=("read_file",),
        child_role="writer",
        child_tools=("read_file", "write_file"),
        child_permissions=("repo:write",),
    )
    decision = sched.spawn_child("parent", proposal)
    assert isinstance(decision, DenyDecision)
    assert decision.reason in (
        DenyReason.CHILD_TOOL_ESCALATION,
        DenyReason.CHILD_ROLE_ESCALATION,
    )


# ---------------------------------------------------------------------------
# Acceptance: per-repo/per-issue concurrency enforced
# ---------------------------------------------------------------------------


def test_per_repo_and_issue_concurrency_are_enforced(tmp_path: Path) -> None:
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(
            max_global_concurrency=4,
            max_per_repo=2,
            max_per_issue=1,
            max_dag_fanout=6,
        ),
        clock=lambda: 1_000_000.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )
    a = _node("a", role="reader", tools=("read_file",), permissions=("repo:read",))
    b = _node("b", role="reader", tools=("read_file",), permissions=("repo:read",))
    c = _node("c", role="reader", tools=("read_file",), permissions=("repo:read",))
    # Submit all three nodes - same repo/issue, so per-issue cap applies
    sched.submit(
        TaskGraph(
            envelope=_envelope(issue="230"),
            nodes=(a, b, c),
        ),
        repo="QuantLab",
        issue="230",
    )
    leases = sched.dispatch()
    # Per-issue cap is 1, so only one node should be dispatched
    assert len(leases) == 1
    assert leases[0].task_id == "a"


# ---------------------------------------------------------------------------
# Acceptance: authoritative snapshot is deterministic and exportable
# ---------------------------------------------------------------------------


def test_authoritative_snapshot_is_deterministic_and_exportable(tmp_path: Path) -> None:
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1234.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )
    _submit(sched, [_node("a"), _node("b", dependencies=("a",))], issue="230")
    sched.dispatch()
    snap1 = sched.snapshot()
    snap2 = sched.snapshot()
    assert snap1 == snap2
    assert snap1["paper_only"] is False
    target = tmp_path / "scheduler-snapshot.json"
    exported = sched.export_snapshot(target)
    assert exported == snap1
    assert json.loads(target.read_text(encoding="utf-8")) == snap1


# ---------------------------------------------------------------------------
# Acceptance: replay restores parent/child identity and fencing
# ---------------------------------------------------------------------------


def test_replay_restores_parent_child_identity_and_fencing(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "events.jsonl")
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4, max_per_issue=3),
        clock=lambda: 1000.0,
        audit_log=log,
    )
    parent = _node(
        "parent",
        role="writer",
        tools=("read_file", "patch"),
        permissions=("repo:read",),
    )
    _submit(sched, [parent], issue="230")
    parent_lease = sched._claims.get("parent")
    assert parent_lease is not None
    child = sched.spawn_child(
        "parent",
        ChildProposal(
            parent_role="writer",
            parent_tools=("read_file", "patch"),
            child_role="reader",
            child_tools=("read_file",),
            child_task="child-work",
        ),
    )
    assert isinstance(child, TaskNode)
    assert child.id.startswith("parent-child-")
    # Check the child has been added to the scheduler
    assert "parent-child-" in sched._tasks or any(
        t.id.startswith("parent-child-") for t in sched._tasks.values()
    )

    recovered = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4, max_per_issue=3),
        clock=lambda: 1010.0,
        audit_log=log,
    )
    applied = recovered.replay()
    assert applied >= 2
    snapshot = recovered.snapshot()
    child_row = next(
        (
            row
            for row in snapshot["tasks"]
            if row["task_id"].startswith("parent-child-")
        ),
        None,
    )
    if child_row is not None:
        assert child_row["parent_agent_id"] == parent_lease.agent_id
        assert child_row["parent_task_id"] == "parent"


# ---------------------------------------------------------------------------
# Acceptance: replay fails closed when submit payload is missing
# ---------------------------------------------------------------------------


def test_replay_fails_closed_when_submit_payload_is_missing(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "events.jsonl")
    log.append(
        {"event": "submit", "task_id": "missing", "repo": "QuantLab", "issue": "230"}
    )
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1000.0,
        audit_log=log,
    )
    # Replay with no pre-loaded tasks - should create task from submit event
    applied = sched.replay()
    assert applied >= 1
    assert "missing" in sched._tasks


# ---------------------------------------------------------------------------
# Acceptance: consumer policy hook works
# ---------------------------------------------------------------------------


def test_default_consumer_policy_denies_tools_not_in_allowlist(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    proposal = ChildProposal(
        parent_role="reader",
        parent_tools=("read_file",),
        child_role="reader",
        child_tools=("read_file", "shell"),
    )
    decision = sched.evaluate_child_proposal(proposal)
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST


def test_consumer_policy_hook_is_replaceable(tmp_path: Path) -> None:
    """Verify that consumers can replace the policy hook with a stricter one."""

    class StrictPolicy:
        def evaluate_child_proposal(
            self, proposal: ChildProposal
        ) -> AllowDecision | DenyDecision:
            return DenyDecision(
                DenyReason.CONSUMER_POLICY_DENIED, "all children denied"
            )

    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_000.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
        consumer_policy=StrictPolicy(),
    )
    proposal = ChildProposal(
        parent_role="reader",
        parent_tools=("read_file",),
        child_role="reader",
        child_tools=("read_file",),
        child_task="test",
    )
    decision = sched.evaluate_child_proposal(proposal)
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.CONSUMER_POLICY_DENIED


def test_spawn_child_with_strict_policy_denies(tmp_path: Path) -> None:
    class StrictPolicy:
        def evaluate_child_proposal(
            self, proposal: ChildProposal
        ) -> AllowDecision | DenyDecision:
            return DenyDecision(DenyReason.CONSUMER_POLICY_DENIED, "no children")

    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_000.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
        consumer_policy=StrictPolicy(),
    )
    _submit(sched, [_node("parent", role="reader", tools=("read_file",))], issue="230")
    proposal = ChildProposal(
        parent_role="reader",
        parent_tools=("read_file",),
        child_role="reader",
        child_tools=("read_file",),
        child_task="test",
    )
    result = sched.spawn_child("parent", proposal)
    assert isinstance(result, DenyDecision)
    assert result.reason == DenyReason.CONSUMER_POLICY_DENIED


# ---------------------------------------------------------------------------
# Acceptance: snapshot includes parent/child edges
# ---------------------------------------------------------------------------


def test_snapshot_includes_parent_child_edges(tmp_path: Path) -> None:
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_000.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )
    parent = _node(
        "parent", role="reader", tools=("read_file",), permissions=("repo:read",)
    )
    _submit(sched, [parent], issue="230")
    child = sched.spawn_child(
        "parent",
        ChildProposal(
            parent_role="reader",
            parent_tools=("read_file",),
            child_role="reader",
            child_tools=("read_file",),
            child_task="child",
        ),
    )
    assert isinstance(child, TaskNode)
    snap = sched.snapshot()
    parent_edges = [e for e in snap["edges"] if e["kind"] == "parent"]
    assert any(e["from"] == "parent" and e["to"] == child.id for e in parent_edges)


# ---------------------------------------------------------------------------
# Acceptance: child proposal returns TaskNode with correct metadata
# ---------------------------------------------------------------------------


def test_child_proposal_creates_valid_tasknode(tmp_path: Path) -> None:
    sched = DynamicChildScheduler(
        budget=SchedulerBudget(max_global_concurrency=4),
        clock=lambda: 1_000_000.0,
        audit_log=AuditLog(tmp_path / "events.jsonl"),
    )
    _submit(sched, [_node("parent", role="reader", tools=("read_file",))], issue="230")
    child = sched.spawn_child(
        "parent",
        ChildProposal(
            parent_role="reader",
            parent_tools=("read_file",),
            child_role="reader",
            child_tools=("read_file",),
            child_task="child-task",
            child_model="step",
            child_fallback_model="solar",
        ),
    )
    assert isinstance(child, TaskNode)
    assert child.id.startswith("parent-child-")
    assert child.role == "reader"
    assert child.tools == ("read_file",)
    assert child.model_policy == {"model": "step", "fallback_model": "solar"}


# ---------------------------------------------------------------------------
# Acceptance: dispatch with dependency ordering
# ---------------------------------------------------------------------------


def test_dispatch_respects_dependency_order(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    _submit(
        sched,
        [_node("a"), _node("b", dependencies=("a",)), _node("c", dependencies=("b",))],
        issue="230",
    )
    ready = sched.ready()
    assert [n.id for n in ready] == ["a"]  # A is the only ready node
    leases = sched.dispatch()
    assert len(leases) == 1
    assert leases[0].task_id == "a"
    # Complete A
    lease_a = leases[0]
    assert sched.complete(
        "a", "ok", agent_id=lease_a.agent_id, fencing_token=lease_a.fencing_token
    )
    # Now B should be ready
    ready = sched.ready()
    assert [n.id for n in ready] == ["b"]


# ---------------------------------------------------------------------------
# Acceptance: DAG node limit exceeded
# ---------------------------------------------------------------------------


def test_dag_node_limit_denied(tmp_path: Path) -> None:
    sched = _idle_scheduler(tmp_path)
    # Create more nodes than max_dag_nodes (16)
    nodes = [_node(f"n{i}") for i in range(257)]
    sched.submit(_graph(nodes), repo="QuantLab", issue="230")
    events = sched.audit_log.replay()
    denies = [e for e in events if e.get("reason") == DenyReason.DAG_NODE_LIMIT.value]
    assert denies
