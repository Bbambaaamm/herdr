"""Offline, fail-closed contract tests for Herdr v1.7 admission control (#8).

All tests are PAPER-only and use injected ResourceUsage / in-memory AuditLog — no
live host probe, no network, no live broker, no credential.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from herdr.admission import (
    AdmissionControl,
    AgentIdentity,
    AllowDecision,
    AuditLog,
    DenyDecision,
    DenyReason,
    PlanBudget,
    ResourceUsage,
    TaskGraphSpec,
)


def _writer_identity(
    role: str = "writer",
    repo: str = "QuantLab",
    issue: str = "187",
    parent_tools: frozenset[str] | None = None,
    parent_role: str | None = None,
    paper_only: bool = True,
) -> AgentIdentity:
    return AgentIdentity(
        role=role,
        repo=repo,
        issue=issue,
        parent_role=parent_role,
        parent_tools=parent_tools or frozenset(),
        paper_only=paper_only,
    )


def _idle_usage() -> ResourceUsage:
    """Healthy host snapshot: 16GiB RAM (8GiB free), 8 logical CPUs, load1=1.

    This makes the fail-closed host-pressure gate (load1 > 1.5*cpus OR
    mem_available < max(2GiB, 20% total)) pass for normal small spawns, so
    the caller can test the specific resource/policy path they care about
    by overriding the relevant fields.
    """
    return ResourceUsage(
        active_agents=0,
        agents_per_repo={},
        agents_per_issue={},
        cpu=0.10,
        ram=0.20,
        queue_depth=0,
        elapsed_seconds=1,
        # host telemetry (healthy 16GiB machine, 8 cores, light load)
        swap_risk=0.0,
        load1=1.0,
        logical_cpus=8,
        total_ram_bytes=16 * 1024**3,
        mem_available_bytes=8 * 1024**3,
    )


def _tmp_audit(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "admission.jsonl")


# --- Acceptance: planner cannot bypass limits via larger graph output ----- #


def test_planner_graph_within_limits_is_admitted(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=10, max_depth=3, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, AllowDecision)


@pytest.mark.parametrize("node_count", [65, 128, 1000])
def test_planner_runaway_graph_is_denied(node_count: int, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=node_count, max_depth=4, max_fanout=6)
    decision = ac.check(_writer_identity(), spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason in (
        DenyReason.PLANNER_GRAPH_TOO_LARGE,
        DenyReason.DAG_NODE_LIMIT,
    )


@pytest.mark.parametrize("depth", [9, 50])
def test_planner_deep_graph_is_denied(depth: int, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=10, max_depth=depth, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.DAG_DEPTH_LIMIT


@pytest.mark.parametrize("fanout", [7, 100])
def test_planner_wide_graph_is_denied(fanout: int, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=10, max_depth=2, max_fanout=fanout)
    decision = ac.check(_writer_identity(), spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.DAG_FANOUT_LIMIT


# --- Acceptance: child may not escalate tools/permissions beyond parent --- #


def test_child_can_not_escalate_tools_beyond_parent(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    parent_tools = frozenset({"read_file", "search_files"})
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    child = _writer_identity(parent_tools=parent_tools, parent_role="writer")
    # child wants write_file — NOT in parent's tool set.
    decision = ac.check(child, spec, _idle_usage(), ["read_file", "search_files", "write_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.TOOL_ESCALATION


def test_child_can_not_use_tool_outside_role_allowlist(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    writer = _writer_identity(role="writer", parent_tools=frozenset({"read_file"}))
    # `git_push` is an operator tool — a writer cannot escalate into operator.
    decision = ac.check(writer, spec, _idle_usage(), ["read_file", "git_push"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason in (
        DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST,
        DenyReason.PERMISSION_ESCALATION,
    )


def test_child_can_not_escalate_role_above_parent(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    # parent is reader; child claims writer while keeping the same read-only tool.
    child = _writer_identity(
        role="writer",
        parent_tools=frozenset({"read_file"}),
        parent_role="reader",
    )
    decision = ac.check(child, spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.PERMISSION_ESCALATION


# --- Acceptance: resource pressure blocks a heavy spawn before start ------ #


@pytest.mark.parametrize(
    "field,value", [("cpu", 0.81), ("cpu", 0.95), ("ram", 0.86), ("ram", 0.99)]
)
def test_resource_pressure_blocks_heavy_spawn(field: str, value: float, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = _idle_usage()
    usage = replace(usage, **{field: value})
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason in (
        DenyReason.CPU_BUDGET,
        DenyReason.RAM_BUDGET,
        DenyReason.RESOURCE_PRESSURE,
    )


def test_queue_backpressure_blocks_spawn(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = replace(_idle_usage(), queue_depth=65)
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.QUEUE_BACKPRESSURE


def test_task_time_budget_blocks_long_running(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = replace(_idle_usage(), elapsed_seconds=1801)
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.TASK_TIME_BUDGET


def test_global_agent_cap_blocks_spawn(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = replace(_idle_usage(), active_agents=5)
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.GLOBAL_AGENT_LIMIT


def test_missing_host_telemetry_fails_closed(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = ResourceUsage(cpu=0.10, ram=0.20)
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.RESOURCE_PRESSURE


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mem_available_bytes", 3 * 1024**3),
        ("load1", 12.1),
    ],
)
def test_host_pressure_blocks_spawn(field: str, value: int | float, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = replace(_idle_usage(), **{field: value})
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.RESOURCE_PRESSURE


def test_per_repo_agent_cap_blocks_spawn(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = replace(_idle_usage(), agents_per_repo={"QuantLab": 4})
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.PER_REPO_AGENT_LIMIT


def test_per_issue_agent_cap_blocks_spawn(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = replace(_idle_usage(), agents_per_issue={("QuantLab", "187"): 3})
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.PER_ISSUE_AGENT_LIMIT


# --- Acceptance: runaway subtask plan is bounded ------------------------- #


def test_runaway_subtask_plan_is_bounded(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    # A planner emitting a maximal, deep, fanning graph is still bounded by
    # the approved v1.7 ceilings (64 nodes, depth 4, fanout 6).
    spec = TaskGraphSpec(node_count=1_000_000, max_depth=1_000, max_fanout=1_000)
    usage = _idle_usage()
    decision = ac.check(_writer_identity(), spec, usage, ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason in (DenyReason.PLANNER_GRAPH_TOO_LARGE, DenyReason.DAG_NODE_LIMIT)


# --- Acceptance: PAPER-only — no live broker/trading permissions ----------- #


def test_paper_only_blocks_live_trading_tool(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(
        _writer_identity(), spec, _idle_usage(), ["read_file", "alpaca-order.submit"]
    )
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.LIVE_TRADING_TOOL


@pytest.mark.parametrize("role", ["reader", "writer", "operator"])
def test_no_live_broker_permissions_in_allowlists(role: str) -> None:
    allowlist = PlanBudget().role_tool_allowlist.get(role, frozenset())
    for tool in allowlist:
        assert not any(
            tool.startswith(p)
            for p in ("alpaca-order", "alpaca-position", "broker", "live-broker", "trade")
        ), tool


def test_non_paper_only_spawn_is_denied(tmp_path: Path) -> None:
    ac = AdmissionControl(paper_only=True, audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    identity = _writer_identity(paper_only=False)  # child claims live
    decision = ac.check(identity, spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.LIVE_TRADING_TOOL


# --- Acceptance: protected paths / secrets denied ------------------------ #


@pytest.mark.parametrize(
    "tool",
    [
        "patch backend/src/quantlab/trading.py",
        "read backend/src/quantlab/phase4.py",
        "search_files backend/src/quantlab/security.py",
    ],
)
def test_protected_paths_denied(tool: str, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, _idle_usage(), [tool])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.PROTECTED_PATH


@pytest.mark.parametrize("tool", ["shell export API_KEY=xxx", "patch alpaca_secret_key"])
def test_secret_access_denied(tool: str, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, _idle_usage(), [tool])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.SECRET_ACCESS


# --- Acceptance: denial is durably audited (Machine City visible) --------- #


def test_denial_is_audited_and_visible(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=1_000_000, max_depth=2, max_fanout=2)
    decision = ac.check(_writer_identity(), spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    log = ac.audit_log
    assert log is not None
    events = log.replay()
    assert events
    denies = [e for e in events if e["event"] == "deny"]
    assert denies
    assert denies[-1]["reason"] == DenyReason.PLANNER_GRAPH_TOO_LARGE.value
    # JSONL format: one record per line, parseable.
    raw = log.path.read_text(encoding="utf-8").strip().splitlines()
    assert all(json.loads(line) for line in raw)


# --- Acceptance: cancellation is durable (survives restart) -------------- #


def test_cancellation_is_durable(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    task_id = "236-test-task-0001"
    record = ac.cancel(task_id, "runaway subtask exceeded DAG budget")
    assert record["event"] == "cancel"
    assert record["task_id"] == task_id
    # Replay must surface the cancel record after a "restart" (same log file).
    replayed = ac.audit_log.replay()  # type: ignore[union-attr]
    cancels = [e for e in replayed if e["event"] == "cancel" and e["task_id"] == task_id]
    assert cancels == [record]


def test_audit_log_rejects_corrupt_line_as_tamper_evident(tmp_path: Path) -> None:
    log = _tmp_audit(tmp_path)
    log.append({"event": "allow", "agents_after": 1})
    with log.path.open("a", encoding="utf-8") as fh:
        fh.write("this-is-not-json\n")
    with pytest.raises(json.JSONDecodeError):
        log.replay()


# --- Acceptance: operator role is never auto-spawned ---------------------- #


def test_operator_role_is_not_auto_spawnable(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    spec = TaskGraphSpec(node_count=5, max_depth=2, max_fanout=2)
    child = _writer_identity(
        role="operator", parent_role="writer", parent_tools=frozenset({"read_file"})
    )
    decision = ac.check(child, spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.NON_SPAWNABLE_ROLE


def test_audit_sink_is_required_fail_closed() -> None:
    with pytest.raises(ValueError, match="audit sink"):
        AdmissionControl()


def test_empty_parent_toolset_denies_child_tools(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    child = _writer_identity(parent_role="writer", parent_tools=frozenset())
    decision = ac.check(
        child,
        TaskGraphSpec(node_count=1, max_depth=1, max_fanout=0),
        _idle_usage(),
        ["read_file"],
    )
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.TOOL_ESCALATION


def test_auto_spawn_allowlists_do_not_include_unrestricted_shell() -> None:
    budget = PlanBudget()
    assert "shell" not in budget.role_tool_allowlist["reader"]
    assert "shell" not in budget.role_tool_allowlist["writer"]


@pytest.mark.parametrize(
    "spec",
    [
        TaskGraphSpec(node_count=0, max_depth=1, max_fanout=0),
        TaskGraphSpec(node_count=1, max_depth=0, max_fanout=0),
        TaskGraphSpec(node_count=1, max_depth=1, max_fanout=-1),
    ],
)
def test_malformed_graph_dimensions_fail_closed(spec: TaskGraphSpec, tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    decision = ac.check(_writer_identity(), spec, _idle_usage(), ["read_file"])
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.INVALID_GRAPH_SPEC


def test_nonfinite_resource_telemetry_fails_closed(tmp_path: Path) -> None:
    ac = AdmissionControl(audit_log=_tmp_audit(tmp_path))
    usage = replace(_idle_usage(), cpu=float("nan"))
    decision = ac.check(
        _writer_identity(),
        TaskGraphSpec(node_count=1, max_depth=1, max_fanout=0),
        usage,
        ["read_file"],
    )
    assert isinstance(decision, DenyDecision)
    assert decision.reason == DenyReason.INVALID_RESOURCE_TELEMETRY
