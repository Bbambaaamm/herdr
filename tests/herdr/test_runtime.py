from __future__ import annotations

import hashlib
import dataclasses
import json
import os
import re
import threading
import time
import types
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest
import herdr.runtime as runtime_mod

from herdr.consumer_policies import allow_all_consumer_policy, quantlab_paper_policy

from herdr.admission import (
    AdmissionControl,
    AgentIdentity,
    AuditLog as AdmissionAuditLog,
    PlanBudget,
    ResourceUsage,
    TaskGraphSpec,
)
from herdr.scheduler import _Lease
from herdr.scheduler import AuditLog as SchedulerAuditLog, ChildProposal, DynamicChildScheduler
from herdr.runtime import (
    HERDR_CONTEXT_BLOCKER,
    AdmissionRegistry,
    CommandResult,
    HerdrChildRuntime,
    HerdrRuntimeError,
    PreDeliveryFailure,
    build_two_child_canary,
)


class FakeHerdrRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.created: list[str] = []
        self.closed: list[str] = []
        self.agents: dict[str, dict[str, str]] = {}
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
        if call[:2] == ("pane", "run"):
            if len(call) >= 4 and "exec hermes " in call[3]:
                pane_id = call[2]
                self.agents[pane_id] = {
                    "agent": "hermes",
                    "name": f"manual-{pane_id.replace(':', '-')}",
                    "pane_id": pane_id,
                    "agent_status": "idle",
                }
            return CommandResult(0, "", "")
        if call[:2] == ("agent", "get"):
            target = call[2]
            agent = self.agents.get(target)
            if agent is None:
                agent = next((row for row in self.agents.values()
                              if row.get("name") == target), None)
            if agent is None:
                return CommandResult(1, json.dumps({"error": {"code": "agent_not_found"}}), "")
            return CommandResult(0, json.dumps({"result": {"agent": agent}}), "")
        if call[:2] == ("agent", "rename"):
            target, name = call[2], call[3]
            agent = self.agents.get(target)
            if agent is None:
                return CommandResult(1, json.dumps({"error": {"code": "agent_not_found"}}), "")
            agent["name"] = name
            return CommandResult(0, json.dumps({"result": {"agent": agent}}), "")
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
            self.agents.pop(call[2], None)
            return CommandResult(0, json.dumps({"result": {"closed": True}}), "")
        raise AssertionError(f"unexpected Herdr call: {call}")


def _canary(tmp_path: Path):
    return build_two_child_canary(
        parent_agent_id="quantlab-hermes",
        audit_path=tmp_path / "events.jsonl",
        clock=lambda: 1000.0,
    )


def _admission(tmp_path: Path) -> AdmissionControl:
    return AdmissionControl(
        audit_log=AdmissionAuditLog(tmp_path / "admission.jsonl"),
        consumer_policy_hook=quantlab_paper_policy,
    )


def _registry(tmp_path: Path) -> AdmissionRegistry:
    return AdmissionRegistry(tmp_path / "admission-registry.json")


def test_managed_admission_release_requires_exact_claim(tmp_path: Path):
    registry = _registry(tmp_path)
    entry = {"agent_id": "child-agent", "repo": "repo", "issue": "82",
             "task_id": "other-child", "fencing_token": 7, "lease_until": 9999999999}
    registry._write([entry])
    registry.release("child-agent", task_id="child", fencing_token=8)
    assert registry._read() == [entry]
    registry.release("child-agent", task_id="other-child", fencing_token=7)
    assert registry._read() == []


def test_managed_observation_rejects_wrong_live_pane(tmp_path: Path) -> None:
    class WrongPaneRunner:
        def run(self, args, timeout_seconds=30.0):
            return CommandResult(0, json.dumps({"result": {"agent": {
                "pane_id": "someone-elses-pane", "agent_status": "done"}}}), "")

    scheduler = _canary(tmp_path)[0]
    runtime = HerdrChildRuntime(scheduler, WrongPaneRunner(), cwd=tmp_path)
    runtime._owned_panes.add("owned-pane")
    with pytest.raises(HerdrRuntimeError, match="child_wrong_pane"):
        runtime._verify_live_child("child", "owned-pane", "marker")
    with pytest.raises(HerdrRuntimeError, match="child_pane_unowned"):
        runtime._verify_live_child("child", "unowned-pane", "marker")


@pytest.mark.parametrize("case", ["reused_pane", "wrong_agent", "wrong_marker",
                                  "absent", "exact"])
def test_cleanup_bound_child_proves_live_binding(tmp_path: Path, monkeypatch, case):
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=(), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "cleanup",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    rec = scheduler._tasks[child.id]
    assert scheduler.bind_execution_session(child.id, rec.run_token, lease.agent_id,
                                            "child-pane", "child-marker")
    evidence = [{"artifact": "exact"}]
    digest = hashlib.sha256(json.dumps(evidence, sort_keys=True,
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    assert scheduler.publish_child_result(child.id, rec.run_token, lease.agent_id,
                                          lease.fencing_token, rec.idempotency_key,
                                          digest, evidence)
    assert rec.attempt_state == "terminal"
    if case == "wrong_agent":
        rec.execution_agent = "other-agent"

    class Runner:
        def __init__(self):
            self.closed = []
        def run(self, args, timeout_seconds=30.0):
            if args[:2] == ["pane", "list"]:
                panes = [] if case == "absent" else [{"pane_id": "child-pane"}]
                return CommandResult(0, json.dumps({"result": {"panes": panes}}), "")
            if args[:2] == ["pane", "close"]:
                self.closed.append(args[2])
                return CommandResult(0, json.dumps({"result": {"closed": True}}), "")
            raise AssertionError(args)

    runner = Runner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
                                admission_registry=_registry(tmp_path))
    releases = []
    monkeypatch.setattr(runtime.admission_registry, "release",
                        lambda agent, **kw: releases.append(agent))
    verified = []
    def verify(agent, pane, marker, *, require_sandbox=False, require_owned=True, require_bootstrap=True):
        verified.append((agent, pane, marker, require_sandbox, require_owned))
        if case in {"reused_pane", "wrong_marker"}:
            raise HerdrRuntimeError("child_marker_missing", pane)
        return "done"
    monkeypatch.setattr(runtime, "_verify_live_child", verify)
    if case in {"reused_pane", "wrong_agent", "wrong_marker"}:
        with pytest.raises(HerdrRuntimeError):
            runtime.cleanup_bound_child(child.id)
        assert runner.closed == []
    else:
        runtime.cleanup_bound_child(child.id)
        assert runner.closed == ([] if case == "absent" else ["child-pane"])
    assert releases == ([lease.agent_id] if case in {"absent", "exact"} else [])
    if case in {"exact", "reused_pane", "wrong_marker"}:
        assert verified == [(lease.agent_id, "child-pane", "child-marker", True, False)]


@pytest.mark.parametrize("case", ["absent", "exact", "wrong_marker", "wrong_agent"])
def test_managed_pre_delivery_cleanup_requires_created_identity(tmp_path, monkeypatch, case):
    scheduler = _canary(tmp_path)[0]
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
                                admission_registry=_registry(tmp_path))
    lease = _Lease(task_id="child", agent_id="child-agent", holder="test",
                   fencing_token=1, lease_until=100)
    runtime._owned_panes.add("child-pane")
    runtime._reserved_agents.add(lease.agent_id)
    runtime._reservation_panes[lease.agent_id] = "child-pane"
    def run(args, timeout_seconds=30.0):
        if args[:2] == ["pane", "list"]:
            panes = [] if case == "absent" else [{"pane_id": "child-pane"}]
            return CommandResult(0, json.dumps({"result": {"panes": panes}}), "")
        if args[:2] == ["pane", "close"]:
            runner.closed.append(args[2])
            return CommandResult(0, "{}", "")
        raise AssertionError(args)
    monkeypatch.setattr(runner, "run", run)
    monkeypatch.setattr(runtime, "_verify_created_pane_marker", lambda pane, marker:
        (_ for _ in ()).throw(HerdrRuntimeError("child_cleanup_unproven", pane))
        if case == "wrong_marker" else None)
    monkeypatch.setattr(runtime, "_verify_live_child", lambda agent, pane, marker, **kw:
        (_ for _ in ()).throw(HerdrRuntimeError("child_wrong_pane", pane))
        if case == "wrong_agent" else "done")
    monkeypatch.setattr(runtime.admission_registry, "release", lambda *args, **kw: None)
    if case in {"wrong_marker", "wrong_agent"}:
        with pytest.raises(HerdrRuntimeError):
            runtime.cleanup_managed_pre_delivery(lease, "child-pane", "child-marker",
                                                 agent_start_attempted=True)
    else:
        runtime.cleanup_managed_pre_delivery(lease, "child-pane", "child-marker",
                                             agent_start_attempted=True)
    assert runner.closed == (["child-pane"] if case == "exact" else [])


def test_managed_pre_delivery_unknown_pane_preserves_reservation(tmp_path, monkeypatch):
    scheduler = _canary(tmp_path)[0]
    runtime = HerdrChildRuntime(scheduler, FakeHerdrRunner(), cwd=tmp_path,
                                admission_registry=_registry(tmp_path))
    lease = _Lease(task_id="child", agent_id="child-agent", holder="test",
                   fencing_token=1, lease_until=100)
    released = []
    monkeypatch.setattr(runtime.admission_registry, "release",
                        lambda *args, **kw: released.append(args))
    with pytest.raises(HerdrRuntimeError, match="child_cleanup_unproven"):
        runtime.cleanup_managed_pre_delivery(lease, None, "marker",
                                             agent_start_attempted=False)
    assert released == []


def test_managed_child_writable_is_exact_result_file_only(tmp_path: Path):
    scheduler = _canary(tmp_path)[0]
    runtime = HerdrChildRuntime(
        scheduler, FakeHerdrRunner(), cwd=tmp_path,
        snapshot_path=tmp_path / "attempt" / "swarm.json",
        admission_registry=_registry(tmp_path),
    )
    target, = runtime._child_result_writable("child-a")
    assert target == tmp_path / "attempt" / "results" / "child-a.result.json"
    assert target.is_file()
    assert target.stat().st_mode & 0o777 == 0o600
    assert target.parent != target
    assert not (target.parent / "child-b.result.json").exists()
    with pytest.raises(HerdrRuntimeError, match="child_result_target_exists"):
        runtime._child_result_writable("child-a")


def test_quantlab_profile_admission_is_paper_only(tmp_path: Path, monkeypatch):
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="root-run", idempotency_key="root-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="Bbambaaamm/herdr", issue="82", role="writer",
        tools=("read_file",), permissions=(), policy_profile="quantlab")
    child = scheduler.delegate_child("parent", "root-run", "paper",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    runtime = HerdrChildRuntime(
        scheduler, FakeHerdrRunner(), cwd=tmp_path,
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane", "HERDR_PROFILE": "quantlab"},
        admission_registry=_registry(tmp_path), resource_usage_factory=lambda *_: _healthy_usage(),
    )
    runtime._skill_checked = True
    captured = []
    monkeypatch.setattr(runtime.admission_registry, "reserve",
                        lambda admission, identity, spec, usage, tools, lease, **kw:
                        captured.append(identity))
    runtime._admit_child(lease)
    assert captured and captured[0].paper_only is True


def test_managed_runtime_binds_owned_pane_before_prompt(tmp_path: Path, monkeypatch) -> None:
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="root-run", idempotency_key="root-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="Bbambaaamm/herdr", issue="82", role="writer",
        tools=("read_file",), permissions=(), policy_profile="herdr-core")
    child = scheduler.delegate_child("parent", "root-run", "research",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    rec = scheduler._tasks[child.id]
    scheduler.bind_child_prompt(child.id, "inspect now")
    events = []

    class Runner:
        executable = "/bin/true"
        def run(self, args, timeout_seconds=30.0):
            assert args[:2] == ["agent", "prompt"]
            assert rec.execution_pane == "created-pane"
            assert scheduler.authorize_child_delivery(child.id, rec.run_token,
                lease.agent_id, lease.fencing_token, rec.idempotency_key)
            events.append("prompt")
            return CommandResult(0, json.dumps({"result": {"agent": {
                "agent_status": "done"}}}), "")

    runtime = HerdrChildRuntime(scheduler, Runner(), cwd=tmp_path)
    monkeypatch.setattr(runtime, "prepare", lambda: events.append("prepare"))
    monkeypatch.setattr(runtime, "_admit_child", lambda lease: events.append("admit"))
    def create(index, marker, policy_env):
        assert policy_env["HERDR_DURABLE_TASK_ID"] == child.id
        assert "agent-stack/policy-bin" in policy_env["PATH"]
        runtime._owned_panes.add("created-pane")
        events.append("create")
        return "created-pane"
    monkeypatch.setattr(runtime, "_create_pane", create)
    def sandbox_child(pane, marker, real, task_id):
        events.append("sandbox")
        from tests.policy_launch_fakes import policy_fixture
        launch=next(iter(runtime._policy_launches.values()))
        runtime._sandbox_proofs[pane] = {"sandbox_pid":123,"policy_sha256":"a"*64,
                                        "invocation_policy":policy_fixture(launch.identity)}
        return tmp_path / "policy"
    monkeypatch.setattr(runtime, "_sandbox_child_pane", sandbox_child)
    monkeypatch.setattr(runtime, "_start_agent", lambda lease, pane: events.append("start"))
    monkeypatch.setattr(runtime, "_verify_live_child",
                        lambda agent, pane, marker, *, require_sandbox=False:
                        "done" if pane == "created-pane" and require_sandbox else "unavailable")
    monkeypatch.setattr(runtime, "cleanup", lambda: events.append("cleanup"))
    assert runtime.run_managed_child(lease, "inspect now", run_token=rec.run_token,
                                     idempotency_key=rec.idempotency_key) == "settled"
    assert events == ["prepare", "admit", "create", "sandbox", "start", "prompt"]
    assert rec.execution_agent == lease.agent_id
    assert rec.execution_pane == "created-pane"
    assert rec.observed_execution == "settled"
    assert rec.state.value == "running"


def test_private_child_approval_failure_precedes_provider_and_pane(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
    from herdr.security import SecurityError
    scheduler=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"))
    scheduler.register_external_parent_attempt(task_id="parent",run_token="root-run",
        idempotency_key="root-key",agent_name="parent-agent",pane_id="parent-pane",marker="parent-marker",
        repo="Bbambaaamm/herdr",issue="82",role="writer",tools=("read_file",),
        permissions=(),policy_profile="herdr-core")
    child=scheduler.delegate_child("parent","root-run","research",
        ChildProposal("writer",("read_file",),"reader",("read_file",),child_task="inspect"))
    lease=scheduler.dispatch(task_ids={child.id})[0];rec=scheduler._tasks[child.id]
    scheduler.bind_child_prompt(child.id,"inspect now")
    class Runner:
        executable="/bin/true"
        def run(self,*args,**kwargs):pytest.fail("no native process before private approval")
    factory=FakeHostPolicyLaunchFactory();original=factory.prepare_child
    runtime=HerdrChildRuntime(scheduler,Runner(),cwd=tmp_path,policy_launch_factory=factory)
    def prepare(**kwargs):
        launch=original(**kwargs)
        launch.private_profile_snapshot=SimpleNamespace(name=runtime.env.get("HERDR_HERMES_PROFILE","quantlab"))
        return launch
    monkeypatch.setattr(factory,"prepare_child",prepare)
    monkeypatch.setattr(runtime,"prepare",lambda:None)
    monkeypatch.setattr(runtime,"_admit_child",lambda lease:None)
    def deny(task_id,real):raise SecurityError("private mount approval missing")
    monkeypatch.setattr(runtime,"_prepare_private_child_command",deny)
    monkeypatch.setattr(runtime,"_preflight_child_provider",lambda:pytest.fail("no mutable private credential preflight"))
    monkeypatch.setattr(runtime,"_create_pane",lambda *args:pytest.fail("approval must precede pane"))
    with pytest.raises(HerdrRuntimeError,match="child_pre_delivery_failed"):
        runtime.run_managed_child(lease,"inspect now",run_token=rec.run_token,idempotency_key=rec.idempotency_key)
    assert not runtime._policy_launches and not runtime._private_sandbox_commands
    assert factory.created[0].events[-1]==("closed",)
    assert rec.execution_pane is None and not rec.economic_delivery_attempted


def test_managed_done_without_inner_sandbox_cannot_settle(tmp_path: Path, monkeypatch) -> None:
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=(), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "research",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    rec = scheduler._tasks[child.id]

    class Runner:
        executable = "/bin/true"
        def run(self, args, timeout_seconds=30.0):
            if args[:2] == ["agent", "get"]:
                return CommandResult(0, json.dumps({"result": {"agent": {
                    "name": lease.agent_id, "pane_id": "child-pane",
                    "agent_status": "done"}}}), "")
            return CommandResult(0, json.dumps({"result": {"process_info": {
                "shell_pid": 1, "foreground_processes": []}}}), "")

    runtime = HerdrChildRuntime(scheduler, Runner(), cwd=tmp_path)
    monkeypatch.setattr(runtime, "prepare", lambda: None)
    monkeypatch.setattr(runtime, "_admit_child", lambda lease: None)
    monkeypatch.setattr(runtime, "_create_pane", lambda *args: "child-pane")
    monkeypatch.setattr(runtime, "_sandbox_child_pane", lambda *args: tmp_path / "policy")
    monkeypatch.setattr(runtime, "_start_agent", lambda *args: None)
    runtime._owned_panes.add("child-pane")
    monkeypatch.setattr(runtime, "cleanup", lambda: None)
    with pytest.raises(HerdrRuntimeError, match="child_pre_delivery_failed"):
        runtime.run_managed_child(lease, "inspect", run_token=rec.run_token,
                                  idempotency_key=rec.idempotency_key)
    assert rec.observed_execution == "unavailable"
    assert not any(e.get("event") == "execution_observed"
                   for e in scheduler.audit_log.replay())


@pytest.mark.parametrize("phase", ["host_guard", "admission", "pane", "agent_start"])
def test_managed_pre_delivery_boundary(tmp_path: Path, monkeypatch, phase) -> None:
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=(), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "research",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    rec = scheduler._tasks[child.id]
    class Runner(FakeHerdrRunner):
        executable = "/bin/true"
    runner = Runner()
    runtime = HerdrChildRuntime(
        scheduler, runner, cwd=tmp_path,
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane"},
        host_guard=lambda: phase != "host_guard",
        admission=_admission(tmp_path), admission_registry=_registry(tmp_path),
        resource_usage_factory=(_global_cap_usage if phase == "admission" else _healthy_usage))
    if phase == "pane":
        monkeypatch.setattr(runtime, "_admit_child", lambda lease: None)
        monkeypatch.setattr(runtime, "_create_pane", lambda *args: (_ for _ in ()).throw(
            HerdrRuntimeError("herdr_command_failed", "pane uncertain")))
    if phase == "agent_start":
        monkeypatch.setattr(runtime, "_admit_child", lambda lease: None)
        monkeypatch.setattr(runtime, "_sandbox_child_pane",
                            lambda *args: tmp_path / "policy")
        monkeypatch.setattr(runtime, "_start_agent", lambda *args: (_ for _ in ()).throw(
            HerdrRuntimeError("herdr_command_failed", "agent start denied")))
    with pytest.raises(PreDeliveryFailure) as failure:
        runtime.run_managed_child(lease, "inspect", run_token=rec.run_token,
                                  idempotency_key=rec.idempotency_key)
    assert failure.value.cleanup_complete is (phase not in {"pane", "agent_start"})
    assert not any(call[:2] == ("agent", "prompt") for call in runner.calls)
    assert rec.observed_execution == "unavailable"
    assert rec.state.value == "blocked" and rec.lease is None
    replay = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    replay.replay()
    assert replay._tasks[child.id].pre_delivery_failure
    assert replay._tasks[child.id].cleanup_complete is (phase not in {"pane", "agent_start"})


@pytest.mark.parametrize("role,tools,permissions,expected", [
    ("reader", ("read_file",), ("workspace-write",), False),
    ("writer", ("write_file",), (), False),
    ("writer", ("read_file",), ("workspace-write",), False),
    ("writer", ("write_file",), ("workspace-write",), True),
])
def test_child_workspace_write_requires_role_tool_and_permission(
        tmp_path, role, tools, permissions, expected):
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role="writer", tools=("read_file", "write_file"),
        permissions=("workspace-write",), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "scope",
        ChildProposal("writer", ("read_file", "write_file"), role, tools,
                      child_permissions=permissions, child_task="inspect"))
    runtime = HerdrChildRuntime(scheduler, FakeHerdrRunner(), cwd=tmp_path)
    assert runtime._child_workspace_writable(child.id) is expected


@pytest.mark.parametrize("tools,expected", [
    (("read_file", "search_files"), "file"),
    (("read_file", "write_file", "patch"), "file"),
])
def test_legacy_canary_agent_start_uses_explicit_admitted_toolset(tmp_path, tools, expected):
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    role = "writer" if set(tools) & {"patch","write_file"} else "reader"
    parent_role = "reviewer" if role == "reviewer" else "writer"
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role=parent_role, tools=tools,
        permissions=("workspace-write",), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "scope",
        ChildProposal(parent_role, tools, role, tools, child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
                                env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane"})
    runtime._skill_checked = True

    runtime._start_agent(lease, "child-pane")

    call = next(call for call in runner.calls if call[:2] == ("agent", "start"))
    assert call[call.index("--toolsets") + 1] == expected
    assert call.index("--toolsets") > call.index("chat")
    assert not any(value in call for value in (
        "terminal", "code_execution", "web", "browser", "delegation",
        "connections", "computer_use", "cron", "mcp", "plugins"))


def _write_profile_auth(profile_dir, expires_at):
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "config.yaml").write_text("model: {}\n", encoding="utf-8")
    (profile_dir / "auth.json").write_text(json.dumps({
        "providers": {"nous": {"agent_key_expires_at": expires_at}}}), encoding="utf-8")


def test_trusted_provider_preflight_accepts_nous_key_above_runtime_ttl(tmp_path, monkeypatch):
    binary = tmp_path / "hermes"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    profile_dir = tmp_path / "profiles" / "quantlab"
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    _write_profile_auth(profile_dir, future)
    calls = []

    class Proc:
        def __init__(self, out="", rc=0):
            self.returncode, self.stdout, self.stderr = rc, out, ""

    def fake_run(argv, **kwargs):
        calls.append(argv)
        tail = argv[-3:]
        if tail == ["config", "get", "model.provider"]:
            return Proc("nous\n")
        if argv[-2:] == ["config", "path"]:
            return Proc(str(profile_dir / "config.yaml") + "\n")
        if tail == ["auth", "status", "nous"]:
            return Proc("nous: logged in\n")
        if tail == ["auth", "refresh", "nous"]:
            pytest.fail("fresh credential must not rotate")
        raise AssertionError(argv)

    monkeypatch.setattr(runtime_mod.subprocess, "run", fake_run)
    runtime_mod._trusted_hermes_profile_preflight(
        "quantlab", executable=str(binary), env={"HOME": "/home/agentops"})
    assert not any(call[-3:] == ["auth", "refresh", "nous"] for call in calls)


def test_trusted_provider_preflight_refreshes_nous_below_runtime_ttl(tmp_path, monkeypatch):
    binary = tmp_path / "hermes"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    profile_dir = tmp_path / "profiles" / "quantlab"
    stale = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    fresh = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    _write_profile_auth(profile_dir, stale)
    calls = []

    class Proc:
        def __init__(self, out="", rc=0):
            self.returncode, self.stdout, self.stderr = rc, out, ""

    def fake_run(argv, **kwargs):
        calls.append(argv)
        tail = argv[-3:]
        if tail == ["config", "get", "model.provider"]:
            return Proc("nous\n")
        if argv[-2:] == ["config", "path"]:
            return Proc(str(profile_dir / "config.yaml") + "\n")
        if tail == ["auth", "status", "nous"]:
            return Proc("nous: logged in\n")
        if tail == ["auth", "refresh", "nous"]:
            _write_profile_auth(profile_dir, fresh)
            return Proc("Refreshed nous credential #1\n")
        raise AssertionError(argv)

    monkeypatch.setattr(runtime_mod.subprocess, "run", fake_run)
    runtime_mod._trusted_hermes_profile_preflight(
        "quantlab", executable=str(binary), env={"HOME": "/home/agentops"})
    assert sum(call[-3:] == ["auth", "refresh", "nous"] for call in calls) == 1
    assert sum(call[-3:] == ["auth", "status", "nous"] for call in calls) == 2


def test_trusted_provider_preflight_fails_closed_on_short_post_refresh_ttl(tmp_path, monkeypatch):
    binary = tmp_path / "hermes"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    profile_dir = tmp_path / "profiles" / "quantlab"
    short = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    _write_profile_auth(profile_dir, short)

    class Proc:
        def __init__(self, out="", rc=0):
            self.returncode, self.stdout, self.stderr = rc, out, ""

    def fake_run(argv, **kwargs):
        tail = argv[-3:]
        if tail == ["config", "get", "model.provider"]:
            return Proc("nous\n")
        if argv[-2:] == ["config", "path"]:
            return Proc(str(profile_dir / "config.yaml") + "\n")
        if tail == ["auth", "status", "nous"]:
            return Proc("nous: logged in\n")
        if tail == ["auth", "refresh", "nous"]:
            return Proc("Refreshed nous credential #1\n")
        raise AssertionError(argv)

    monkeypatch.setattr(runtime_mod.subprocess, "run", fake_run)
    with pytest.raises(HerdrRuntimeError, match="child_provider_preflight_failed"):
        runtime_mod._trusted_hermes_profile_preflight(
            "quantlab", executable=str(binary), env={"HOME": "/home/agentops"})


def test_trusted_provider_preflight_fails_closed_when_auth_not_logged_in(tmp_path, monkeypatch):
    binary = tmp_path / "hermes"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    profile_dir = tmp_path / "profiles" / "quantlab"
    _write_profile_auth(profile_dir, (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())

    class Proc:
        def __init__(self, out):
            self.returncode, self.stdout, self.stderr = 0, out, ""

    def fake_run(argv, **kwargs):
        tail = argv[-3:]
        if tail == ["config", "get", "model.provider"]:
            return Proc("nous\n")
        if argv[-2:] == ["config", "path"]:
            return Proc(str(profile_dir / "config.yaml") + "\n")
        if tail == ["auth", "status", "nous"]:
            return Proc("nous: logged out\n")
        raise AssertionError(argv)

    monkeypatch.setattr(runtime_mod.subprocess, "run", fake_run)
    with pytest.raises(HerdrRuntimeError, match="child_provider_preflight_failed"):
        runtime_mod._trusted_hermes_profile_preflight(
            "quantlab", executable=str(binary), env={"HOME": "/home/agentops"})


def test_managed_agent_start_rejects_unmapped_permission_before_runner(tmp_path):
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=("future-permission",), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "scope-permission",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      parent_permissions=("future-permission",),
                      child_permissions=("future-permission",), child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
                                env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane"})
    runtime._skill_checked = True

    with pytest.raises(HerdrRuntimeError, match="child_permission_unmapped"):
        runtime._start_agent(lease, "child-pane")
    assert runner.calls == []


def test_managed_agent_start_rejects_unmapped_tool_before_runner(tmp_path):
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=(), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "scope",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    scheduler._tasks[child.id].node = dataclasses.replace(
        scheduler._tasks[child.id].node, tools=("read_file", "future_tool"))
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
                                env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane"})
    runtime._skill_checked = True

    with pytest.raises(HerdrRuntimeError, match="child_toolset_unmapped"):
        runtime._start_agent(lease, "child-pane")
    assert runner.calls == []


def test_prompt_invocation_error_preserves_accepted_child(tmp_path: Path, monkeypatch) -> None:
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=(), policy_profile="default")
    child = scheduler.delegate_child("parent", "parent-run", "research",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    rec = scheduler._tasks[child.id]
    scheduler.bind_child_prompt(child.id, "inspect")
    class Runner:
        executable = "/bin/true"
        def run(self, args, **kwargs):
            assert args[:2] == ["agent", "prompt"]
            raise OSError("transport lost after invocation")
    runtime = HerdrChildRuntime(scheduler, Runner(), cwd=tmp_path)
    monkeypatch.setattr(runtime, "prepare", lambda: None)
    monkeypatch.setattr(runtime, "_admit_child", lambda lease: None)
    def create(*args):
        runtime._owned_panes.add("child-pane")
        return "child-pane"
    monkeypatch.setattr(runtime, "_create_pane", create)
    def sandbox_child(pane, *args):
        from tests.policy_launch_fakes import policy_fixture
        launch=next(iter(runtime._policy_launches.values()))
        runtime._sandbox_proofs[pane] = {"sandbox_pid":123,"policy_sha256":"a"*64,
                                        "invocation_policy":policy_fixture(launch.identity)}
        return tmp_path / "policy"
    monkeypatch.setattr(runtime, "_sandbox_child_pane", sandbox_child)
    monkeypatch.setattr(runtime, "_start_agent", lambda *args: None)
    monkeypatch.setattr(runtime, "_verify_live_child", lambda *args, **kwargs: "working")
    with pytest.raises(OSError, match="transport lost"):
        runtime.run_managed_child(lease, "inspect", run_token=rec.run_token,
                                  idempotency_key=rec.idempotency_key)
    assert rec.state.value == "running" and rec.lease is lease
    assert rec.pre_delivery_failure is None and rec.execution_pane == "child-pane"
    assert rec.economic_delivery_attempted is True
    replay = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    replay.replay()
    assert replay._tasks[child.id].state.value == "running"
    assert replay._tasks[child.id].pre_delivery_failure is None
    assert replay._tasks[child.id].economic_delivery_attempted is True


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
        admission_registry=_registry(tmp_path),
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
        admission_registry=_registry(tmp_path),
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
        admission_registry=_registry(tmp_path),
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
    assert all(call[call.index("--toolsets") + 1] == "bot_room" for call in starts)
    assert all(call[call.index("--max-turns") + 1] == "1" for call in starts)

    payload = json.loads(snapshot_path.read_text())
    assert {
        "version",
        "observed_at",
        "repo",
        "issue",
        "paper_only",
        "tasks",
        "agents",
        "edges",
    }.issubset(payload)
    assert payload["policy_profiles"] == ["quantlab-paper"]
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
    registry_state = json.loads((tmp_path / "admission-registry.json").read_text())
    assert registry_state["entries"] == []


def test_long_running_children_refresh_runtime_snapshot(tmp_path: Path, monkeypatch) -> None:
    scheduler, _, leases, prompts = _canary(tmp_path)
    runner = FakeHerdrRunner()
    snapshot_path = tmp_path / "swarm.json"
    calls = []
    original_export = scheduler.export_snapshot

    def counted_export(path):
        calls.append(time.monotonic())
        return original_export(path)

    monkeypatch.setattr(scheduler, "export_snapshot", counted_export)
    runtime = HerdrChildRuntime(
        scheduler,
        runner,
        cwd=tmp_path,
        snapshot_path=snapshot_path,
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p1"},
        host_guard=lambda: True,
        admission=_admission(tmp_path),
        admission_registry=_registry(tmp_path),
        resource_usage_factory=_healthy_usage,
        snapshot_heartbeat_seconds=0.01,
    )
    runtime.run_parallel(leases, prompts)

    # Initial live snapshot + at least one in-flight heartbeat + final snapshot.
    assert len(calls) >= 3
    assert snapshot_path.exists()


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
        admission_registry=_registry(tmp_path),
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
        admission_registry=_registry(tmp_path),
        resource_usage_factory=_healthy_usage,
    )
    with pytest.raises(HerdrRuntimeError) as exc:
        runtime.run_parallel(leases, prompts)
    assert exc.value.code == "child_not_settled"
    assert sorted(runner.closed) == sorted(runner.created)
    assert all(scheduler._tasks[lease.task_id].state.value == "running" for lease in leases)


def test_admission_registry_enforces_global_limit_across_runtimes(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    admission = AdmissionControl(
        budget=PlanBudget(max_global_agents=1, max_agents_per_repo=4, max_agents_per_issue=3),
        audit_log=AdmissionAuditLog(tmp_path / "registry-admission.jsonl"),
        consumer_policy_hook=allow_all_consumer_policy,
    )
    identity = AgentIdentity(
        role="reader",
        repo="Bbambaaamm/herdr",
        issue="3",
        parent_role="reader",
        parent_tools=frozenset(),
        paper_only=True,
    )
    spec = TaskGraphSpec(node_count=1, max_depth=1, max_fanout=0)
    first = _Lease("t1", "h1", "q3-a-f1", 1100.0, 1)
    second = _Lease("t2", "h2", "q3-b-f2", 1100.0, 2)

    registry.reserve(admission, identity, spec, _healthy_usage(), (), first, now=1000.0)
    with pytest.raises(HerdrRuntimeError) as exc:
        registry.reserve(admission, identity, spec, _healthy_usage(), (), second, now=1000.0)

    assert exc.value.code == "child_admission_denied"
    assert exc.value.detail == "global_agent_limit"
    state = json.loads((tmp_path / "admission-registry.json").read_text())
    assert [row["agent_id"] for row in state["entries"]] == ["q3-a-f1"]


def test_admission_registry_keeps_expired_slot_until_explicit_release(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    admission = AdmissionControl(
        budget=PlanBudget(max_global_agents=1, max_agents_per_repo=1, max_agents_per_issue=1),
        audit_log=AdmissionAuditLog(tmp_path / "registry-expiry.jsonl"),
        consumer_policy_hook=allow_all_consumer_policy,
    )
    identity = AgentIdentity(
        role="reader",
        repo="Bbambaaamm/herdr",
        issue="3",
        parent_role="reader",
        parent_tools=frozenset(),
        paper_only=True,
    )
    spec = TaskGraphSpec(node_count=1, max_depth=1, max_fanout=0)
    stale = _Lease("stale", "h1", "q3-stale-f1", 1005.0, 1)
    fresh = _Lease("fresh", "h2", "q3-fresh-f2", 1200.0, 2)

    registry.reserve(admission, identity, spec, _healthy_usage(), (), stale, now=1000.0)
    with pytest.raises(HerdrRuntimeError, match="child_admission_denied"):
        registry.reserve(admission, identity, spec, _healthy_usage(), (), fresh, now=1006.0)

    state = json.loads((tmp_path / "admission-registry.json").read_text())
    assert [row["agent_id"] for row in state["entries"]] == ["q3-stale-f1"]
    registry.release("q3-fresh-f2", now=1006.0)
    assert [row["agent_id"] for row in json.loads(
        (tmp_path / "admission-registry.json").read_text())["entries"]] == ["q3-stale-f1"]
    registry.release("q3-stale-f1", now=1006.0)
    assert json.loads((tmp_path / "admission-registry.json").read_text())["entries"] == []


def test_admission_registry_release_preserves_other_expired_reservations(tmp_path: Path):
    registry = _registry(tmp_path)
    registry._write([
        {"agent_id": agent, "repo": "repo", "issue": "1", "task_id": agent,
         "fencing_token": 1, "lease_until": 1.0}
        for agent in ("expired-a", "expired-b", "target")
    ])
    registry.release("target", now=100.0)
    assert [entry["agent_id"] for entry in registry._read()] == ["expired-a", "expired-b"]


def test_admission_registry_fsyncs_file_and_directory(tmp_path: Path, monkeypatch):
    registry = _registry(tmp_path)
    calls = []
    actual_fsync = os.fsync
    def track_fsync(fd):
        calls.append(os.fstat(fd).st_mode)
        actual_fsync(fd)
    monkeypatch.setattr(os, "fsync", track_fsync)
    registry._write([])
    assert len(calls) == 2
    assert os.path.isfile(registry.path)
    assert registry.path.stat().st_mode & 0o777 == 0o640
    assert os.path.isdir(registry.path.parent)
    import stat
    assert stat.S_ISREG(calls[0]) and stat.S_ISDIR(calls[1])


@pytest.mark.parametrize("writable", [False, True])
@pytest.mark.parametrize("swap_path", [False, True])
def test_actual_child_sandbox_proof_persists_exact_attestation(tmp_path, monkeypatch, writable, swap_path):
    """Exercise production sandbox construction/verify/digest, without a provider."""
    import shutil
    import subprocess
    import tempfile
    from importlib.machinery import SourceFileLoader
    if not shutil.which("bwrap"):
        pytest.skip("bubblewrap unavailable on this host")
    probe = subprocess.run(["bwrap", "--ro-bind", "/", "/", "--unshare-pid", "--", "/bin/true"],
                           capture_output=True)
    if probe.returncode:
        pytest.skip("host user namespace policy denies bubblewrap")
    base = Path(os.environ.get("HERDR_BOUNDARY_TEST_ROOT", "/home/agentops/tmp"))
    if not base.is_dir() or not os.access(base, os.W_OK):
        pytest.skip("physical sandbox fixture root unavailable")
    with tempfile.TemporaryDirectory(prefix="child-attestation-", dir=base) as directory:
        root = Path(directory)
        workspace = root / "worktrees" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "identity.txt").write_text("held")
        siblings = root / "results" / "sibling.result.json"
        siblings.parent.mkdir()
        siblings.write_text("foreign-result")
        fake_home = root / "home"
        config = fake_home / ".config/herdr"
        releases = root / "releases"
        config.mkdir(parents=True)
        releases.mkdir()
        old_exec = SourceFileLoader.exec_module
        loaded = {}
        def load(loader, module):
            old_exec(loader, module)
            if loader.name == "agent_durable_sandbox_runtime":
                module.HOME = fake_home
                module.HERDR_CONFIG = config
                module.HERDR_RELEASES = releases
                module.DEFAULT_WRITABLE = ()
                # Exercise the real copy routine on this fixture's filesystem;
                # shared /tmp can have a separate per-UID quota on staging.
                module.tempfile = types.SimpleNamespace(
                    mkstemp=lambda **kwargs: tempfile.mkstemp(
                        **{**kwargs, "dir": root}),
                )
                # This fixture launches bwrap through a pipe; native TTY readiness
                # is covered separately by real-PTY and owned-server checks.
                module.pane_input_ready = lambda *args: True
                module.verify_pane_prompt = lambda *args, **kwargs: None
                loaded["sandbox"] = module
        monkeypatch.setattr(SourceFileLoader, "exec_module", load)
        scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(root / "events.jsonl"))
        scheduler.register_external_parent_attempt(
            task_id="parent", run_token="parent-run", idempotency_key="parent-key",
            agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
            repo="repo", issue="82", role="writer", tools=("read_file", "write_file"),
            permissions=("workspace-write",), policy_profile="default")
        child = scheduler.delegate_child("parent", "parent-run", "attestation",
            ChildProposal("writer", ("read_file", "write_file"),
                          "writer" if writable else "reader",
                          ("write_file",) if writable else ("read_file",),
                          parent_permissions=("workspace-write",),
                          child_permissions=("workspace-write",) if writable else (), child_task="inspect"))
        lease = scheduler.dispatch(task_ids={child.id})[0]
        record = scheduler._tasks[child.id]
        marker = "child-" + record.run_token
        sandbox_process = None
        class Runner:
            def run(self, args, **kwargs):
                nonlocal sandbox_process
                if args[:2] == ["pane", "run"]:
                    sandbox_process = subprocess.Popen(
                        ["/bin/bash", "-c", args[3]], stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                        env={"PATH": "/usr/bin:/bin", "HOME": str(fake_home),
                             "HERDR_DURABLE_TASK_PANE": marker})
                    return CommandResult(0, "", "")
                assert args[:2] == ["pane", "process-info"]
                if sandbox_process is None:
                    return CommandResult(0, json.dumps({"result": {"process_info": {}}}), "")
                processes = []
                for _ in range(50):
                    assert sandbox_process.poll() is None, sandbox_process.stderr.read(8192).decode()
                    for proc in Path("/proc").iterdir():
                        if not proc.name.isdigit():
                            continue
                        try:
                            env = (proc / "environ").read_bytes().split(b"\0")
                            if f"HERDR_DURABLE_TASK_PANE={marker}".encode() in env:
                                processes.append({"pid": int(proc.name)})
                        except OSError:
                            continue
                    if loaded["sandbox"].inner_pid({"foreground_processes": processes}, marker):
                        break
                    time.sleep(0.02)
                return CommandResult(0, json.dumps({"result": {"process_info":
                    {"foreground_processes": processes}}}), "")
        from types import SimpleNamespace
        directory_fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        directory_stat = os.fstat(directory_fd)
        if swap_path:
            outside = root / "foreign"
            outside.mkdir()
            (outside / "identity.txt").write_text("foreign")
            workspace.rename(workspace.with_name("held-original"))
            workspace.symlink_to(outside, target_is_directory=True)
        pinned = SimpleNamespace(logical=workspace, fd=directory_fd, root=workspace.parent,
            source=f"/proc/{os.getpid()}/fd/{directory_fd}",
            device=directory_stat.st_dev, inode=directory_stat.st_ino)
        def verify_pin():
            current = os.fstat(directory_fd)
            assert (current.st_dev, current.st_ino) == (pinned.device, pinned.inode)
        pinned.verify = verify_pin
        pinned.identity = f"{workspace}|{pinned.device}:{pinned.inode}"
        runtime = HerdrChildRuntime(scheduler, Runner(), cwd=workspace,
                                    pinned_worktree=pinned, snapshot_path=root / "swarm.json")
        assert scheduler.bind_pre_delivery_pane(child.id, record.run_token, lease.agent_id, "owned-pane", marker)
        policy = None
        try:
            policy = runtime._sandbox_child_pane("owned-pane", marker, "/bin/true", child.id)
            proof = runtime._sandbox_proofs["owned-pane"]
            assert proof["sandbox_pid"] > 0
            assert proof["policy_sha256"] == hashlib.sha256(policy.read_bytes()).hexdigest()
            # Execute actual filesystem operations in the established namespace.
            # Record observations only through the one admitted result file.
            import shlex
            import sys
            script = """import json, pathlib, sys
workspace, mine, sibling = map(pathlib.Path, sys.argv[1:])
observed = {"identity": (workspace / "identity.txt").read_text()}
for name, target in (("workspace_write", workspace / "probe.txt"), ("sibling_write", sibling)):
    try:
        target.write_text("effect")
        observed[name] = True
    except OSError:
        observed[name] = False
mine.write_text(json.dumps(observed))
"""
            mine = root / "results" / (child.id + ".result.json")
            sandbox_process.stdin.write((shlex.join([sys.executable, "-I", "-c", script,
                                        str(workspace), str(mine), str(siblings)]) + "\n").encode())
            sandbox_process.stdin.flush()
            observed = None
            for _ in range(100):
                try:
                    observed = json.loads(mine.read_text())
                    break
                except (OSError, ValueError):
                    time.sleep(0.01)
            assert observed == {"identity": "held", "workspace_write": writable, "sibling_write": False}
            assert siblings.read_text() == "foreign-result"
            physical = workspace.with_name("held-original") if swap_path else workspace
            assert (physical / "probe.txt").exists() is writable
            if swap_path:
                assert not (outside / "probe.txt").exists()
            assert scheduler.attest_execution_sandbox(child.id, record.run_token, lease.agent_id,
                "owned-pane", marker, sandbox_pid=proof["sandbox_pid"], policy_sha256=proof["policy_sha256"])
            replay = DynamicChildScheduler(audit_log=SchedulerAuditLog(root / "events.jsonl"))
            replay.replay()
            recovered = replay._tasks[child.id]
            assert recovered.execution_sandbox_verified
            assert recovered.execution_sandbox_attestation["run_token"] == record.run_token
            assert recovered.execution_sandbox_attestation["policy_sha256"] == proof["policy_sha256"]
        finally:
            if sandbox_process is not None:
                if sandbox_process.stdin:
                    sandbox_process.stdin.close()
                try:
                    sandbox_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    sandbox_process.kill()
                    sandbox_process.wait(timeout=2)
            os.close(directory_fd)
            if policy is not None:
                policy.unlink(missing_ok=True)


@pytest.mark.parametrize("phase", ["result", "construct", "launch", "inspect", "verify"])
def test_child_sandbox_failure_removes_frozen_policy(tmp_path, monkeypatch, phase):
    from importlib.machinery import SourceFileLoader
    import types
    scheduler = types.SimpleNamespace(_tasks={"task":types.SimpleNamespace(idempotency_key="slot-key",agent_id=None)})
    policy = tmp_path / "frozen-policy"
    policy.write_text("frozen")
    original = SourceFileLoader.exec_module
    def load(loader, module):
        original(loader, module)
        if loader.name != "agent_durable_sandbox_runtime":
            return
        module.frozen_policy = lambda: policy
        def command(*a, **k):
            if phase == "construct":
                raise RuntimeError("construction failed")
            return ["bwrap", "/bin/bash"]
        module.command = command
        module.inner_pid = lambda *a: 123
        module.pane_input_ready = lambda *a: True
        module.verify_pane_prompt = lambda *a, **kw: None
        module.verify = lambda *a, **k: phase != "verify"
    if phase == "verify":
        from herdr import runtime as runtime_module
        clock = [0.0]
        monkeypatch.setattr(runtime_module.time, "monotonic", lambda: clock[0])
        monkeypatch.setattr(runtime_module.time, "sleep",
                            lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    monkeypatch.setattr(SourceFileLoader, "exec_module", load)
    class Runner:
        def run(self, args, **kwargs):
            if (phase == "launch" and args[:2] == ["pane", "run"]
                    or phase == "inspect" and args[:2] == ["pane", "process-info"]):
                raise RuntimeError("transport failed")
            if args[:2] == ["pane", "run"]:
                return CommandResult(0, "", "")
            return CommandResult(0, json.dumps({"result": {"process_info": {}}}), "")
    runtime = HerdrChildRuntime(scheduler, Runner(), cwd=tmp_path, snapshot_path=tmp_path / "scheduler.json")
    from tests.policy_launch_fakes import FakePreparedPolicyLaunch
    from tests.herdr.test_security import identity
    runtime._policy_launches["task"] = FakePreparedPolicyLaunch(identity(task_id="task"))
    def result(*a):
        if phase == "result":
            raise RuntimeError("result failed")
        return (tmp_path / "result.json",)
    monkeypatch.setattr(runtime, "_child_result_writable", result)
    monkeypatch.setattr(runtime, "_child_workspace_writable", lambda *a: False)
    with pytest.raises(RuntimeError):
        runtime._sandbox_child_pane("owned", "marker", "/bin/true", "task")
    assert not policy.exists()
    assert "owned" not in runtime._sandbox_proofs


@pytest.mark.parametrize("phase,ownership", [("created", "exact"), ("bound", "exact"),
                                          ("created", "duplicate"), ("created", "wrong_fence")])
def test_split_crash_recovers_durable_intent_with_actual_process_identity(tmp_path, monkeypatch, phase, ownership):
    import os
    import subprocess
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent-stack/bin"))
    import agent_durable_children as children
    from herdr.consumer_policies import policy_for_profile
    root = tmp_path / "state"
    root.mkdir()
    directory = children.ensure_attempt_directory(root, "parent", "parent-run")
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(directory / "scheduler.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="parent-run", idempotency_key="parent-key",
        agent_name="parent-agent", pane_id="parent-pane", marker="parent-marker",
        repo="Bbambaaamm/herdr", issue="82", role="writer", tools=("read_file",), permissions=(), policy_profile="herdr-core")
    children.mark_ledger_required(directory)
    child = scheduler.delegate_child("parent", "parent-run", "research",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",), child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    record = scheduler._tasks[child.id]
    registry = _registry(tmp_path)
    processes = {}
    closed = []
    class Runner(FakeHerdrRunner):
        executable = "/bin/true"
        def run(self, args, timeout_seconds=30.0):
            if args == ["pane", "list"]:
                result = {"panes": [{"pane_id": pane} for pane, process in processes.items()
                                    if process.poll() is None]}
            elif args[:2] == ["pane", "process-info"]:
                result = {"process_info": {"shell_pid": processes[args[-1]].pid}}
            elif args[:2] == ["pane", "close"]:
                pane = args[-1]
                closed.append(pane)
                processes[pane].terminate()
                processes[pane].wait(timeout=5)
                result = {}
            else:
                assert args[:2] not in (["agent", "start"], ["agent", "prompt"])
                return super().run(args, timeout_seconds=timeout_seconds)
            return CommandResult(0, json.dumps({"result": result}), "")
    runner = Runner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane", "HERDR_PROFILE": "herdr-core"},
        host_guard=lambda: True,
        admission=AdmissionControl(audit_log=AdmissionAuditLog(tmp_path / "admission.jsonl"),
            consumer_policy_hook=policy_for_profile("herdr-core")),
        admission_registry=registry, resource_usage_factory=_healthy_usage)
    def create(index, marker, policy_env):
        replay = DynamicChildScheduler(audit_log=SchedulerAuditLog(directory / "scheduler.jsonl"))
        replay.replay()
        intent = replay._tasks[child.id]
        assert intent.pre_delivery_pane_creation_attempted and intent.execution_pane is None
        assert intent.execution_marker == marker and intent.execution_agent == lease.agent_id
        assert replay.audit_log.replay()[-1]["event"] == "child_pane_split_started"
        assert intent.pane_split_started is True
        for pane in ("owned-pane", "foreign-pane"):
            env = {**os.environ, **policy_env, "HERDR_DURABLE_TASK_PANE": marker}
            if pane == "foreign-pane" and ownership != "duplicate":
                env["HERDR_DURABLE_FENCING_TOKEN"] = str(lease.fencing_token + 1)
            if pane == "owned-pane" and ownership == "wrong_fence":
                env["HERDR_DURABLE_FENCING_TOKEN"] = str(lease.fencing_token + 2)
            processes[pane] = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], env=env)
            import time
            deadline=time.monotonic()+3
            while True:
                observed=Path(f"/proc/{processes[pane].pid}/environ").read_bytes().split(b"\0")
                if f"HERDR_DURABLE_FENCING_TOKEN={env['HERDR_DURABLE_FENCING_TOKEN']}".encode() in observed: break
                if time.monotonic()>=deadline: pytest.fail("test child exec environment never became ready")
                time.sleep(0.005)
        if phase == "created":
            raise SystemExit("bridge killed after pane creation before returned identity")
        runtime._owned_panes.add("owned-pane")
        return "owned-pane"
    monkeypatch.setattr(runtime, "_create_pane", create)
    original_bind = scheduler.bind_pre_delivery_pane
    def bind(*args):
        assert original_bind(*args)
        raise SystemExit("bridge killed after durable pane binding")
    monkeypatch.setattr(scheduler, "bind_pre_delivery_pane", bind)
    monkeypatch.setattr(runtime, "_sandbox_child_pane",
        lambda *a: pytest.fail("crashed split cannot reach agent/sandbox startup"))
    try:
        with pytest.raises(SystemExit):
            runtime.run_managed_child(lease, "inspect", run_token=record.run_token,
                                       idempotency_key=record.idempotency_key)
        entries = registry._read()
        assert len(entries) == 1 and entries[0]["task_id"] == child.id
        foreign_reservation = {**entries[0], "agent_id": "foreign-agent", "task_id": "foreign-task",
                               "fencing_token": 999}
        registry._write(entries + [foreign_reservation])
        monkeypatch.setattr(children, "SubprocessHerdrRunner", lambda *a: runner)
        monkeypatch.setattr(children, "AdmissionRegistry", lambda: registry)
        with children.parent_attempt_guard(root, "parent", "parent-run", reconcile_results=True) as terminal:
            assert terminal is (ownership == "exact")
        replay = DynamicChildScheduler(audit_log=SchedulerAuditLog(directory / "scheduler.jsonl"))
        replay.replay()
        recovered = replay._tasks[child.id]
        assert (recovered.run_token, recovered.fencing_token, recovered.idempotency_key) == (
            record.run_token, record.fencing_token, record.idempotency_key)
        assert sum(e["event"] == "spawn_child" for e in replay.audit_log.replay()) == 1
        if ownership == "exact":
            assert closed == ["owned-pane"] and recovered.cleanup_complete
            assert recovered.state.value == "blocked" and recovered.lease is None
            assert registry._read() == [foreign_reservation]
            assert processes["foreign-pane"].poll() is None
            with children.parent_attempt_guard(root, "parent", "parent-run", reconcile_results=True) as terminal:
                assert terminal
            assert closed == ["owned-pane"]
        else:
            assert closed == [] and recovered.state.value == "running" and recovered.lease is not None
            assert not recovered.cleanup_complete and len(registry._read()) == 2
            assert all(process.poll() is None for process in processes.values())
    finally:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)

@pytest.fixture(autouse=True)
def explicit_host_policy_for_lifecycle_tests(monkeypatch):
    from tests.policy_launch_fakes import install_runtime_policy_fixture
    from herdr.runtime import HerdrChildRuntime
    install_runtime_policy_fixture(monkeypatch, HerdrChildRuntime)

@pytest.fixture(autouse=True)
def explicit_host_completion_port_for_lifecycle_only(monkeypatch):
    from tests.policy_launch_fakes import install_child_completion_fixture
    install_child_completion_fixture(monkeypatch)


@pytest.mark.parametrize("alias",["read","write","review"])
def test_unsupported_file_alias_is_rejected_before_agent_start(alias):
    with pytest.raises(HerdrRuntimeError,match="child_toolset_unmapped"):
        runtime_mod._child_toolsets((alias,))

def _interrupted_start_record(tmp_path):
    scheduler=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"))
    scheduler.register_external_parent_attempt(task_id="parent",run_token="parent-run",
        idempotency_key="parent-key",agent_name="parent-agent",pane_id="parent-pane",
        marker="parent-marker",repo="repo",issue="82",role="writer",
        tools=("read_file",),permissions=(),policy_profile="default")
    child=scheduler.delegate_child("parent","parent-run","startup",
        ChildProposal("writer",("read_file",),"reader",("read_file",),child_task="inspect"))
    lease=scheduler.dispatch(task_ids={child.id})[0];rec=scheduler._tasks[child.id]
    scheduler.bind_child_prompt(child.id,"inspect")
    assert scheduler.record_child_pane_intent(child.id,rec.run_token,rec.agent_id,
        rec.fencing_token,rec.idempotency_key,f"child-{rec.run_token}")
    assert scheduler.bind_pre_delivery_pane(child.id,rec.run_token,lease.agent_id,"owned-pane",f"child-{rec.run_token}")
    scheduler.mark_pre_delivery_agent_start(child.id)
    return scheduler,child,rec

@pytest.mark.parametrize("legacy",[False,True])
def test_crash_after_agent_start_recovers_only_proven_absent_prompt(tmp_path,monkeypatch,legacy):
    scheduler,child,rec=_interrupted_start_record(tmp_path)
    if legacy:
        events=scheduler.audit_log.replay()
        for event in events:
            if event["event"]=="child_agent_start_attempted":event.pop("delivery_protocol_version")
        scheduler.audit_log._path.write_text("".join(json.dumps(e)+"\n" for e in events))
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));replay.replay()
    recovered=replay._tasks[child.id];closed=[]
    runtime=HerdrChildRuntime(replay,FakeHerdrRunner(),cwd=tmp_path)
    monkeypatch.setattr(runtime,"cleanup_bound_pre_delivery",lambda task_id:closed.append(task_id))
    if legacy:
        assert recovered.economic_delivery_attempted is None
        with pytest.raises(HerdrRuntimeError,match="cleanup_unproven"):runtime.recover_interrupted_child_start(child.id)
        assert not closed and recovered.state.value=="running"
    else:
        assert recovered.economic_delivery_attempted is False
        runtime.recover_interrupted_child_start(child.id)
        assert closed==[child.id] and recovered.cleanup_complete
        assert recovered.state.value=="blocked" and recovered.run_token==rec.run_token
        replay2=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));replay2.replay()
        assert replay2._tasks[child.id].cleanup_complete

def test_duplicate_agent_start_event_cannot_clear_possible_prompt_effect(tmp_path):
    from herdr.scheduler import SchedulerError
    scheduler,child,rec=_interrupted_start_record(tmp_path)
    original=next(e for e in scheduler.audit_log.replay() if e["event"]=="child_agent_start_attempted")
    scheduler.audit_log.append(original);scheduler.audit_log.flush()
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"))
    with pytest.raises(SchedulerError,match="repeated child agent start"):replay.replay()


@pytest.mark.parametrize("field,value",[("agent_id","foreign"),("fencing_token",999),("idempotency_key","foreign"),("delivery_protocol_version",1.0)])
def test_new_start_protocol_replay_requires_full_attempt_identity_and_integer_version(tmp_path,field,value):
    from herdr.scheduler import SchedulerError
    scheduler,child,rec=_interrupted_start_record(tmp_path)
    events=scheduler.audit_log.replay()
    for event in events:
        if event["event"]=="child_agent_start_attempted":event[field]=value
    scheduler.audit_log._path.write_text("".join(json.dumps(e)+"\n" for e in events))
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"))
    with pytest.raises(SchedulerError):replay.replay()

def test_prompt_intent_is_durable_one_use_and_prevents_pre_delivery_cleanup(tmp_path,monkeypatch):
    scheduler,child,rec=_interrupted_start_record(tmp_path)
    monkeypatch.setattr(scheduler,"authorize_child_delivery",lambda *args:True)
    args=(child.id,rec.run_token,rec.agent_id,rec.fencing_token,rec.idempotency_key)
    assert scheduler.mark_child_delivery_started(*args) is True
    assert scheduler.mark_child_delivery_started(*args) is False
    assert scheduler.fail_child_pre_delivery(*args,"cannot assume delivery absent",cleanup_complete=False) is False
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));replay.replay()
    assert replay._tasks[child.id].economic_delivery_attempted is True
    assert len([e for e in replay.audit_log.replay() if e["event"]=="child_prompt_delivery_attempted"])==1


@pytest.mark.parametrize("case", ["exact", "exact-stderr", "mixed-json", "transport", "malformed", "other-error",
    "prompt-maybe-sent", "legacy-unknown", "wrong-pane", "missing-grant-proof", "wrong-marker"])
def test_no_agent_created_cleanup_requires_no_prompt_and_retained_physical_proof(tmp_path, monkeypatch, case):
    from importlib.machinery import SourceFileLoader
    from herdr import policy_launch
    scheduler, child, rec = _interrupted_start_record(tmp_path)
    marker = rec.execution_marker
    rec.execution_sandbox_verified = case != "missing-grant-proof"
    rec.execution_sandbox_attestation = {"sandbox_pid": 321, "invocation_policy": {"retained": True},
        "authority": "physical", "task_id": rec.id, "run_token": rec.run_token,
        "fencing_token": rec.fencing_token, "agent_name": rec.agent_id,
        "pane_id": rec.execution_pane, "marker": marker, "worktree_identity": {}}
    if case == "prompt-maybe-sent": rec.economic_delivery_attempted = True
    if case == "legacy-unknown": rec.economic_delivery_attempted = None
    if case == "wrong-pane": rec.execution_pane = "different"
    response = '{"error":{"code":"agent_not_found"}}'
    if case == "transport": response = '{"error":{"code":"transport_error"}}'
    if case == "malformed": response = "not-json"
    if case == "other-error": response = '{"error":{"message":"agent not found"}}'
    class Runner:
        def __init__(self): self.closed = []
        def run(self, args, timeout_seconds=30.0):
            if args[:2] == ["pane", "list"]:
                return CommandResult(0, '{"result":{"panes":[{"pane_id":"owned-pane"}]}}', "")
            if args[:2] == ["agent", "get"]:
                return CommandResult(1, "" if case == "exact-stderr" else response,
                                     response if case in {"exact-stderr", "mixed-json"} else "")
            if args[:2] == ["pane", "process-info"]:
                return CommandResult(0, '{"result":{"process_info":{"shell_pid":123}}}', "")
            if args[:2] == ["pane", "close"]:
                self.closed.append(args[2]); return CommandResult(0, "{}", "")
            raise AssertionError(args)
    runner = Runner(); runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
        admission_registry=_registry(tmp_path))
    runtime._owned_panes.add("owned-pane")
    monkeypatch.setattr(runtime, "_verify_created_pane_marker", lambda *args: None)
    original = SourceFileLoader.exec_module
    def load(loader, module):
        if loader.name == "agent_durable_sandbox_verify":
            module.inner_pid = lambda process, supplied: 0 if case == "wrong-marker" else 321
        else: original(loader, module)
    monkeypatch.setattr(SourceFileLoader, "exec_module", load)
    verified = []
    def verify(proof, *, identity, pid, attestation, require_bootstrap=True, **kw):
        assert proof == {"retained": True} and pid == 321
        assert identity.task_id == rec.id and identity.run_token == rec.run_token
        assert identity.agent_id == rec.agent_id and identity.fencing_token == rec.fencing_token
        assert identity.parent_task_id == rec.parent_task_id and identity.parent_agent_id == rec.parent_agent_id
        assert not require_bootstrap and attestation["marker"] == marker
        verified.append(identity.to_json())
    monkeypatch.setattr(policy_launch, "verify_retained_policy_evidence", verify)
    if case in {"exact", "exact-stderr"}:
        runtime.cleanup_managed_pre_delivery(rec.lease, "owned-pane", marker, agent_start_attempted=True)
        assert runner.closed == ["owned-pane"] and len(verified) == 1
    else:
        with pytest.raises(HerdrRuntimeError):
            runtime.cleanup_managed_pre_delivery(rec.lease, "owned-pane", marker, agent_start_attempted=True)
        assert runner.closed == [] and verified == []


def test_parent_result_payload_retains_exact_bytes_after_source_mutation_and_restart(tmp_path):
    scheduler, child, rec = _interrupted_start_record(tmp_path)
    evidence = [{"answer": "reader findings", "nested": {"paths": ["example.py"]}}]
    raw = json.dumps(evidence, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    sha = hashlib.sha256(raw).hexdigest()
    assert scheduler.publish_child_result(child.id, rec.run_token, rec.agent_id,
        rec.fencing_token, rec.idempotency_key, sha, evidence)
    evidence[0]["answer"] = "rewritten"
    assert rec.result_evidence_canonical == raw
    replay = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    replay.replay(); recovered = replay._tasks[child.id]
    assert recovered.result_evidence_canonical == raw
    assert recovered.result_artifact_sha256 == sha
    # The public observation snapshot contains only the digest.
    assert "reader findings" not in json.dumps(scheduler.snapshot())


@pytest.mark.parametrize("protocol", ["before-effect", "started", "legacy"])
def test_zero_pane_recovery_requires_versioned_no_split_proof_and_keeps_same_attempt(tmp_path,monkeypatch,protocol):
    scheduler,child,rec=_interrupted_start_record(tmp_path)
    # Reconstruct the durable intent boundary before any pane bind/start events.
    events=scheduler.audit_log.replay()
    cutoff=next(i for i,e in enumerate(events) if e["event"]=="child_pane_creation_attempted")
    events=events[:cutoff+1]
    if protocol=="legacy": events[-1].pop("split_protocol_version")
    scheduler.audit_log._path.write_text("".join(json.dumps(e)+"\n" for e in events))
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));replay.replay()
    recovered=replay._tasks[child.id]
    if protocol=="started":
        assert replay.mark_child_split_started(child.id,recovered.run_token,recovered.agent_id,
            recovered.fencing_token,recovered.idempotency_key)
    class EmptyRunner:
        def __init__(self):self.scans=0
        def run(self,args,timeout_seconds=30):
            assert args==["pane","list"];self.scans+=1
            return CommandResult(0,'{"result":{"panes":[]}}',"")
    runner=EmptyRunner();runtime=HerdrChildRuntime(replay,runner,cwd=tmp_path,admission_registry=_registry(tmp_path))
    released=[];cleaned=[]
    monkeypatch.setattr(runtime.admission_registry,"release",lambda agent,**kw:released.append((agent,kw)))
    monkeypatch.setattr(runtime,"_cleanup_policy_launch",lambda task_id,pane_id=None:cleaned.append(task_id))
    original=(recovered.run_token,recovered.fencing_token,recovered.idempotency_key)
    if protocol=="before-effect":
        runtime.recover_interrupted_child_start(child.id)
        assert recovered.cleanup_complete and recovered.state.value=="blocked"
        assert len(released)==1 and cleaned==[child.id] and runner.scans==1
        again=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));again.replay()
        assert again._tasks[child.id].cleanup_complete
    else:
        with pytest.raises(HerdrRuntimeError,match="cleanup_unproven"):
            runtime.recover_interrupted_child_start(child.id)
        assert not released and not cleaned and recovered.state.value=="running"
    assert (recovered.run_token,recovered.fencing_token,recovered.idempotency_key)==original

def test_split_start_is_fsync_durable_one_use_before_native_effect(tmp_path):
    scheduler,child,rec=_interrupted_start_record(tmp_path)
    events=scheduler.audit_log.replay()
    cutoff=next(i for i,e in enumerate(events) if e["event"]=="child_pane_creation_attempted")
    scheduler.audit_log._path.write_text("".join(json.dumps(e)+"\n" for e in events[:cutoff+1]))
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));replay.replay()
    record=replay._tasks[child.id]
    args=(child.id,record.run_token,record.agent_id,record.fencing_token,record.idempotency_key)
    assert replay.mark_child_split_started(*args)
    assert not replay.mark_child_split_started(*args)
    third=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));third.replay()
    assert third._tasks[child.id].pane_split_started is True

@pytest.mark.parametrize("phase",["admission","policy_prepare"])
def test_resource_preparation_crash_retains_recoverable_pre_split_intent(tmp_path,monkeypatch,phase):
    from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
    scheduler,child,record=_interrupted_start_record(tmp_path)
    events=scheduler.audit_log.replay()
    cutoff=next(i for i,e in enumerate(events) if e["event"]=="child_pane_creation_attempted")
    scheduler.audit_log._path.write_text("".join(json.dumps(e)+"\n" for e in events[:cutoff]))
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));replay.replay()
    current=replay._tasks[child.id]
    factory=FakeHostPolicyLaunchFactory()
    runner=FakeHerdrRunner();runner.executable="/bin/true"
    runtime=HerdrChildRuntime(replay,runner,cwd=tmp_path,policy_launch_factory=factory,admission_registry=_registry(tmp_path))
    monkeypatch.setattr(runtime,"prepare",lambda:None)
    def interrupted(*args,**kwargs):
        durable=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));durable.replay()
        found=durable._tasks[child.id]
        assert found.pane_split_started is False and found.pre_delivery_pane_creation_attempted
        assert (found.run_token,found.agent_id,found.fencing_token,found.idempotency_key)==(
            current.run_token,current.agent_id,current.fencing_token,current.idempotency_key)
        raise SystemExit("simulated host death")
    monkeypatch.setattr(runtime,"_admit_child",interrupted if phase=="admission" else lambda lease:None)
    if phase=="policy_prepare":monkeypatch.setattr(factory,"prepare_child",interrupted)
    with pytest.raises(SystemExit):runtime.run_managed_child(current.lease,"work",
        run_token=current.run_token,idempotency_key=current.idempotency_key)
    recovered=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));recovered.replay()
    class Empty:
        def run(self,args,**kwargs):
            assert args==["pane","list"]
            return CommandResult(0,'{"result":{"panes":[]}}',"")
    cleanup=HerdrChildRuntime(recovered,Empty(),cwd=tmp_path,policy_launch_factory=factory,admission_registry=_registry(tmp_path))
    cleanup.recover_interrupted_child_start(child.id)
    assert recovered._tasks[child.id].cleanup_complete
    assert recovered._tasks[child.id].run_token==current.run_token
    assert not any(call[:2] in {("pane","split"),("agent","prompt")} for call in runner.calls)

def test_nested_delegation_is_rejected_before_any_admission_effect(tmp_path):
    from herdr.runtime import _child_toolsets
    with pytest.raises(HerdrRuntimeError,match="nested_delegation_unavailable"):
        _child_toolsets(("herdr_delegate_child",))
    assert _child_toolsets(("herdr_delegate_child",),allow_delegation=True)=="herdr_delegation"

def test_atomic_managed_claim_survives_crash_before_runtime_entry(tmp_path,monkeypatch):
    scheduler,child,rec=_interrupted_start_record(tmp_path)
    events=scheduler.audit_log.replay()
    cutoff=next(i for i,e in enumerate(events) if e["event"]=="claim" and e["task_id"]==child.id)
    scheduler.audit_log._path.write_text("".join(json.dumps(e)+"\n" for e in events[:cutoff]))
    replay=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));replay.replay()
    lease,=replay.dispatch(task_ids={child.id},managed_start=True)
    durable=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"));durable.replay()
    record=durable._tasks[child.id]
    assert record.pane_split_started is False and record.pre_delivery_pane_creation_attempted
    assert record.execution_marker=="child-"+record.run_token
    assert durable.record_child_pane_intent(child.id,record.run_token,record.agent_id,
        record.fencing_token,record.idempotency_key,record.execution_marker)
    class Empty:
        def run(self,args,**kwargs):
            assert args==["pane","list"]
            return CommandResult(0,'{"result":{"panes":[]}}',"")
    runtime=HerdrChildRuntime(durable,Empty(),cwd=tmp_path,admission_registry=_registry(tmp_path))
    monkeypatch.setattr(runtime,"_cleanup_policy_launch",lambda *args:None)
    runtime.recover_interrupted_child_start(child.id)
    assert record.cleanup_complete and record.state.value=="blocked"
    assert record.fencing_token==lease.fencing_token

def test_missing_modern_work_profile_blocks_before_split_or_agent(tmp_path,monkeypatch):
    from herdr.work_cycle import WorkContractError
    from herdr.child_evidence import ChildCompletionAuthority
    scheduler=DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path/"events.jsonl"))
    scheduler.register_external_parent_attempt(task_id="parent",run_token="parent-run",
        idempotency_key="parent-key",agent_name="parent-agent",pane_id="parent-pane",
        marker="parent-marker",repo="Bbambaaamm/herdr",issue="86",role="writer",
        tools=("read_file",),permissions=(),policy_profile="herdr-core")
    child=scheduler.delegate_child("parent","parent-run","coding",
        ChildProposal("writer",("read_file",),"reader",("read_file",),child_task="inspect"))
    lease=scheduler.dispatch(task_ids={child.id})[0];rec=scheduler._tasks[child.id]
    scheduler.bind_child_prompt(child.id,"inspect")
    class Runner(FakeHerdrRunner):
        executable="/bin/true"
    runtime=HerdrChildRuntime(scheduler,Runner(),cwd=tmp_path)
    monkeypatch.setattr(runtime,"prepare",lambda:None)
    monkeypatch.setattr(runtime,"_admit_child",lambda lease:None)
    def unavailable(authority,record,launch):
        assert record is rec and launch.identity.task_id==child.id
        raise WorkContractError("approved modern work profile unavailable")
    monkeypatch.setattr(ChildCompletionAuthority,"preflight_work",unavailable)
    monkeypatch.setattr(runtime,"_create_pane",lambda *a:pytest.fail("missing profile cannot split"))
    monkeypatch.setattr(runtime,"_start_agent",lambda *a:pytest.fail("missing profile cannot start"))
    monkeypatch.setattr(runtime,"cleanup_managed_pre_delivery",lambda *a,**kw:None)
    with pytest.raises(runtime_mod.PreDeliveryFailure,match="modern work profile"):
        runtime.run_managed_child(lease,"inspect",run_token=rec.run_token,
                                  idempotency_key=rec.idempotency_key)
    assert not rec.pane_split_started and rec.execution_pane is None
    assert not any(event["event"]=="child_pane_split_started" for event in scheduler.audit_log.replay())


@pytest.mark.parametrize("case", ["delayed", "input-unready", "native-error", "json-ack", "text-ack", "stderr-ack", "prompt-unverified"])
def test_managed_child_waits_before_single_native_launch_and_full_verification(tmp_path, monkeypatch, case):
    from importlib.machinery import SourceFileLoader
    from types import SimpleNamespace
    from herdr import runtime as runtime_module
    from tests.policy_launch_fakes import FakePreparedPolicyLaunch
    from tests.herdr.test_security import identity
    clock = [0.0]
    monkeypatch.setattr(runtime_module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(runtime_module.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    policy = tmp_path / "frozen-policy"
    policy.write_text("frozen")
    verification = []
    original = SourceFileLoader.exec_module
    def load(loader, module):
        original(loader, module)
        if loader.name != "agent_durable_sandbox_runtime":
            return
        module.frozen_policy = lambda: policy
        module.command = lambda *args, **kwargs: ["/bin/true"]
        module.pane_input_ready = lambda info, marker: info.get("ready") is True
        def prompt(invoke, pane, marker, **kwargs):
            assert runner.input_checks >= 2 and runner.launches == 0
            runner.prompt_checks += 1
            if case == "prompt-unverified":
                raise RuntimeError("durable_pane_prompt_unverified")
        module.verify_pane_prompt = prompt
        module.inner_pid = lambda info, marker: info.get("pid")
        def verify(pid, real, marker, **kwargs):
            verification.append((pid, marker, kwargs))
            return True
        module.verify = verify
    monkeypatch.setattr(SourceFileLoader, "exec_module", load)
    record = SimpleNamespace(idempotency_key="slot-key", agent_id="child", run_token="run",
                             fencing_token=1, worktree_identity=None, ownership=None,
                             parent_agent_id=None, parent_task_id=None, id="task")
    scheduler = SimpleNamespace(_tasks={"task": record},
        task_node=lambda task: SimpleNamespace(tools=(), permissions=()))
    class Runner:
        def __init__(self):
            self.input_checks = self.sandbox_checks = self.launches = self.prompt_checks = 0
        def run(self, args, *, timeout_seconds=30.0):
            if args[:2] == ["pane", "process-info"]:
                assert args[2:] == ["--pane", "owned"]
                assert 0 < timeout_seconds <= 10
                if not self.launches:
                    self.input_checks += 1
                    value = {"ready": case != "input-unready" and self.input_checks >= 2}
                else:
                    self.sandbox_checks += 1
                    value = {"pid": 123 if self.sandbox_checks >= 2 else None}
                return CommandResult(0, json.dumps({"result": {"process_info": value}}), "")
            assert args[:3] == ["pane", "run", "owned"]
            assert self.input_checks >= 2 and self.prompt_checks == 1
            self.launches += 1
            return {
                "native-error": CommandResult(1, "", "native launch failed"),
                "json-ack": CommandResult(0, '{"result":{}}', ""),
                "text-ack": CommandResult(0, "unexpected", ""),
                "stderr-ack": CommandResult(0, "", "warning"),
            }.get(case, CommandResult(0, "", ""))
    runner = Runner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path, snapshot_path=tmp_path / "swarm.json")
    launch = FakePreparedPolicyLaunch(identity(task_id="task"))
    runtime._policy_launches["task"] = launch
    monkeypatch.setattr(runtime, "_child_workspace_writable", lambda task: False)
    if case == "delayed":
        assert runtime._sandbox_child_pane("owned", "marker", "/bin/true", "task") == policy
        assert runner.input_checks == runner.sandbox_checks == 2 and runner.launches == 1
        assert verification[0][0:2] == (123, "marker")
        assert verification[0][2]["attempts"] == 1
        assert verification[0][2]["policy_mount"] is launch.mount
        assert runtime._sandbox_proofs["owned"]["sandbox_pid"] == 123
    else:
        with pytest.raises(HerdrRuntimeError):
            runtime._sandbox_child_pane("owned", "marker", "/bin/true", "task")
        assert runner.launches == (0 if case in {"input-unready", "prompt-unverified"} else 1)
        assert runner.sandbox_checks == 0 and verification == []
        assert not policy.exists() and "owned" not in runtime._sandbox_proofs

def test_managed_start_cannot_fall_back_to_native_bare_shell_when_proof_missing(tmp_path):
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(task_id="parent", run_token="run",
        idempotency_key="key", agent_name="parent", pane_id="parent-pane", marker="marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=(), policy_profile="default")
    child = scheduler.delegate_child("parent", "run", "scope",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",), child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    runner = FakeHerdrRunner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane"})
    runtime._skill_checked = True
    runtime._managed_launch_panes.add("owned-pane")
    with pytest.raises(HerdrRuntimeError, match="child_invocation_policy_missing"):
        runtime._start_agent(lease, "owned-pane")
    assert runner.calls == []

@pytest.mark.parametrize("ack", ["", "{\"result\":{}}"])
def test_managed_start_uses_guarded_adapter_and_strict_empty_ack(tmp_path, monkeypatch, ack):
    import importlib.machinery
    scheduler = DynamicChildScheduler(audit_log=SchedulerAuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(task_id="parent", run_token="run",
        idempotency_key="key", agent_name="parent", pane_id="parent-pane", marker="marker",
        repo="repo", issue="82", role="writer", tools=("read_file",),
        permissions=(), policy_profile="default")
    child = scheduler.delegate_child("parent", "run", "scope",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",), child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    class Runner:
        calls = []
        def run(self, args, timeout_seconds=30):
            self.calls.append(args)
            assert args[:2] == ["pane", "run"]
            return CommandResult(0, ack, "")
    runner = Runner()
    runtime = HerdrChildRuntime(scheduler, runner, cwd=tmp_path,
        env={"HERDR_ENV": "1", "HERDR_PANE_ID": "parent-pane"})
    runtime._skill_checked = True
    runtime._managed_launch_panes.add("owned-pane")
    record = scheduler._tasks[child.id]
    record.execution_marker = "child-marker"
    launch = runtime._policy_launches[child.id]  # Explicit policy fixture.
    runtime._policy_panes["owned-pane"] = launch
    policy = tmp_path / "policy"
    policy.write_text("frozen-policy")
    runtime._sandbox_proofs["owned-pane"] = {"invocation_policy": {"test": True},
        "sandbox_pid": 123, "policy_file": policy, "real_binary": "/native/herdr",
        "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest()}
    original = importlib.machinery.SourceFileLoader.exec_module
    observed = []
    def execute(loader, module):
        original(loader, module)
        if loader.name != "agent_durable_sandbox_start":
            return
        def verify(pid, real, marker, **kwargs):
            observed.append((pid, real, marker, kwargs))
            return True
        def start(invoke, pane, marker, pid, name, args, **kwargs):
            assert kwargs["verify_boundary"]() is True
            assert pane == "owned-pane" and marker == "child-marker" and pid == 123
            assert args == ["-p", "quantlab", "chat", "--toolsets", "file",
                            "--max-turns", "1", "--run-budget", "600"]
            invoke(["pane", "run", pane, "owned adapter input"], timeout_seconds=5)
            return {"result": {"agent": {"name": name, "pane_id": pane}}}
        module.verify = verify
        module.start_sandbox_agent = start
    monkeypatch.setattr(importlib.machinery.SourceFileLoader, "exec_module", execute)
    if ack:
        with pytest.raises(HerdrRuntimeError, match="child_agent_input_unacknowledged"):
            runtime._start_agent(lease, "owned-pane")
    else:
        runtime._start_agent(lease, "owned-pane")
    assert observed == [(123, Path("/native/herdr"), "child-marker",
        {"policy": policy, "attempts": 1, "pinned_worktree": None,
         "child_workspace_writable": False, "policy_mount": launch.mount})]
    assert not any(call[:2] == ["agent", "start"] for call in runner.calls)
