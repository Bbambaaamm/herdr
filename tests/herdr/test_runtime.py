from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

import pytest

from herdr.admission import AdmissionControl, AuditLog as AdmissionAuditLog, ResourceUsage
from herdr.runtime import (
    HERDR_CONTEXT_BLOCKER,
    CommandResult,
    HerdrChildRuntime,
    HerdrRuntimeError,
    build_two_child_canary,
)


class FakeHerdrRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.created: list[str] = []
        self.closed: list[str] = []
        self.active_prompts = 0
        self.max_active_prompts = 0
        self.prompt_status = "done"
        self._lock = threading.Lock()

    def run(self, args, timeout_seconds: float = 30.0) -> CommandResult:
        del timeout_seconds
        call = tuple(args)
        with self._lock:
            self.calls.append(call)
        if call == ("--skill",):
            return CommandResult(0, "---\nname: herdr\n", "")
        if call[:2] == ("pane", "split"):
            pane_id = f"w9:p{len(self.created) + 1}"
            self.created.append(pane_id)
            payload = {"result": {"pane": {"pane_id": pane_id}}}
            return CommandResult(0, json.dumps(payload), "")
        if call[:2] == ("agent", "start"):
            payload = {"result": {"agent": {"name": call[2]}}}
            return CommandResult(0, json.dumps(payload), "")
        if call[:2] == ("agent", "prompt"):
            with self._lock:
                self.active_prompts += 1
                self.max_active_prompts = max(self.max_active_prompts, self.active_prompts)
            time.sleep(0.04)
            with self._lock:
                self.active_prompts -= 1
            return CommandResult(
                0,
                json.dumps({"result": {"agent": {"agent_status": self.prompt_status}}}),
                "",
            )
        if call[:2] == ("pane", "close"):
            self.closed.append(call[2])
            return CommandResult(0, json.dumps({"result": {"closed": True}}), "")
        raise AssertionError(f"unexpected Herdr call: {call}")


def _canary(tmp_path: Path):
    return build_two_child_canary(
        parent_agent_id="quantlab-hermes",
        audit_path=tmp_path / "events.jsonl",
        clock=lambda: 1000.0,
    )


def _admission(tmp_path: Path) -> AdmissionControl:
    return AdmissionControl(audit_log=AdmissionAuditLog(tmp_path / "admission.jsonl"))


def _healthy_usage(*_args) -> ResourceUsage:
    return ResourceUsage(
        active_agents=0,
        agents_per_repo={},
        agents_per_issue={},
        cpu=0.10,
        ram=0.20,
        queue_depth=0,
        elapsed_seconds=1,
        swap_risk=0.0,
        load1=1.0,
        logical_cpus=8,
        total_ram_bytes=16 * 1024**3,
        mem_available_bytes=8 * 1024**3,
    )


def _global_cap_usage(*_args) -> ResourceUsage:
    usage = _healthy_usage()
    usage.active_agents = 4
    return usage


def test_live_runtime_requires_managed_herdr_context(tmp_path: Path) -> None:
    scheduler, _, leases, prompts = _canary(tmp_path)
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(
        scheduler,
        runner,
        cwd=tmp_path,
        snapshot_path=tmp_path / "swarm.json",
        env={},
        host_guard=lambda: True,
        admission=_admission(tmp_path),
        resource_usage_factory=_healthy_usage,
    )
    with pytest.raises(HerdrRuntimeError) as exc:
        runtime.run_parallel(leases, prompts)
    assert exc.value.code == HERDR_CONTEXT_BLOCKER
    assert runner.calls == []


def test_host_pressure_denies_before_any_herdr_control(tmp_path: Path) -> None:
    scheduler, _, leases, prompts = _canary(tmp_path)
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(
        scheduler,
        runner,
        cwd=tmp_path,
        snapshot_path=tmp_path / "swarm.json",
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p1"},
        host_guard=lambda: False,
    )
    with pytest.raises(HerdrRuntimeError) as exc:
        runtime.run_parallel(leases, prompts)
    assert exc.value.code == "resource_pressure"
    assert runner.calls == []


def test_admission_denial_happens_before_child_process_creation(tmp_path: Path) -> None:
    scheduler, _, leases, prompts = _canary(tmp_path)
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(
        scheduler,
        runner,
        cwd=tmp_path,
        snapshot_path=tmp_path / "swarm.json",
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p1"},
        host_guard=lambda: True,
        admission=_admission(tmp_path),
        resource_usage_factory=_global_cap_usage,
    )
    with pytest.raises(HerdrRuntimeError) as exc:
        runtime.run_parallel(leases, prompts)

    assert exc.value.code == "child_admission_denied"
    assert exc.value.detail == "global_agent_limit"
    assert runner.created == []
    assert not any(call[:2] == ("pane", "split") for call in runner.calls)
    assert not any(call[:2] == ("agent", "start") for call in runner.calls)
    events = [json.loads(line) for line in (tmp_path / "admission.jsonl").read_text().splitlines()]
    assert events[-1]["event"] == "deny"
    assert events[-1]["reason"] == "global_agent_limit"


def test_two_real_child_contract_parallel_cleanup_and_snapshot(tmp_path: Path) -> None:
    scheduler, parent_lease, leases, prompts = _canary(tmp_path)
    runner = FakeHerdrRunner()
    snapshot_path = tmp_path / "swarm.json"
    runtime = HerdrChildRuntime(
        scheduler,
        runner,
        cwd=tmp_path,
        snapshot_path=snapshot_path,
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p1"},
        host_guard=lambda: True,
        admission=_admission(tmp_path),
        resource_usage_factory=_healthy_usage,
    )
    results = runtime.run_parallel(leases, prompts)

    assert results == {lease.task_id: True for lease in leases}
    assert runner.max_active_prompts == 2
    assert sorted(runner.closed) == sorted(runner.created)
    assert len(runner.created) == 2
    assert any(call == ("--skill",) for call in runner.calls)
    starts = [call for call in runner.calls if call[:2] == ("agent", "start")]
    assert len(starts) == 2
    assert all("-t" in call and call[call.index("-t") + 1] == "bot_room" for call in starts)
    assert all(
        "--max-turns" in call and call[call.index("--max-turns") + 1] == "1" for call in starts
    )

    payload = json.loads(snapshot_path.read_text())
    assert set(payload) == {
        "version",
        "observed_at",
        "repo",
        "issue",
        "paper_only",
        "tasks",
        "agents",
        "edges",
    }
    assert payload["paper_only"] is True
    assert snapshot_path.stat().st_mode & 0o777 == 0o640
    assert len(payload["agents"]) == 3
    assert {row["agent_id"] for row in payload["agents"]} >= {"quantlab-hermes"}
    child_agents = [row for row in payload["agents"] if row["agent_id"] != parent_lease.agent_id]
    assert len(child_agents) == 2
    assert len({row["agent_id"] for row in child_agents}) == 2
    for row in child_agents:
        assert row["parent_agent_id"] == "quantlab-hermes"
        assert row["parent_task_id"] == parent_lease.task_id
        assert row["fencing_token"] > parent_lease.fencing_token
        assert re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", row["agent_id"])

    parent_edges = [
        edge
        for edge in payload["edges"]
        if edge["kind"] == "parent" and edge["from"] == parent_lease.task_id
    ]
    assert len(parent_edges) == 2

    admission_events = [
        json.loads(line) for line in (tmp_path / "admission.jsonl").read_text().splitlines()
    ]
    allows = [event for event in admission_events if event["event"] == "allow"]
    assert len(allows) == 2
    assert all(event["admit:node_count"] == 3 for event in allows)
    assert all(event["admit:max_depth"] == 2 for event in allows)
    assert all(event["admit:max_fanout"] == 2 for event in allows)
    assert all(event["admit:child_tools_count"] == 0 for event in allows)


def test_cleanup_never_closes_unowned_parent_pane(tmp_path: Path) -> None:
    scheduler, _, leases, prompts = _canary(tmp_path)
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(
        scheduler,
        runner,
        cwd=tmp_path,
        snapshot_path=tmp_path / "swarm.json",
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p1"},
        host_guard=lambda: True,
        admission=_admission(tmp_path),
        resource_usage_factory=_healthy_usage,
    )
    runtime.run_parallel(leases, prompts)
    closed = {call[2] for call in runner.calls if call[:2] == ("pane", "close")}
    assert closed == set(runner.created)
    assert "w1:p1" not in closed


def test_blocked_child_is_not_committed_and_owned_panes_are_cleaned(tmp_path: Path) -> None:
    scheduler, _, leases, prompts = _canary(tmp_path)
    runner = FakeHerdrRunner()
    runner.prompt_status = "blocked"
    runtime = HerdrChildRuntime(
        scheduler,
        runner,
        cwd=tmp_path,
        snapshot_path=tmp_path / "swarm.json",
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p1"},
        host_guard=lambda: True,
        admission=_admission(tmp_path),
        resource_usage_factory=_healthy_usage,
    )
    with pytest.raises(HerdrRuntimeError) as exc:
        runtime.run_parallel(leases, prompts)
    assert exc.value.code == "child_not_settled"
    assert sorted(runner.closed) == sorted(runner.created)
    assert all(scheduler._tasks[lease.task_id].state.value == "running" for lease in leases)
