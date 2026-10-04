import argparse
import errno
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import threading
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "agent-stack/bin"
sys.path.insert(0, str(BIN))

from herdr.scheduler import AuditLog, DynamicChildScheduler
from herdr.runtime import (AdmissionRegistry, CommandResult, HerdrChildRuntime,
                           MAX_PROMPT_CHARS)
from herdr.admission import AdmissionControl, AuditLog as AdmissionAuditLog, ResourceUsage
from agent_durable_children import (all_children_terminal, attempt_directory,
                                    ledger_required, parent_attempt_guard)

HELPER = ROOT / "agent-stack/bin/agent-durable-child"
SERVER = ROOT / "agent-stack/bin/agent-durable-bridge"
SANDBOX = ROOT / "agent-stack/bin/agent_durable_sandbox.py"
WRAPPER = ROOT / "agent-stack/policy-bin/herdr"
loader = SourceFileLoader("agent_durable_child_test", str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
bridge = importlib.util.module_from_spec(spec)
loader.exec_module(bridge)
server_loader = SourceFileLoader("agent_durable_bridge_test", str(SERVER))
server_spec = importlib.util.spec_from_loader(server_loader.name, server_loader)
server = importlib.util.module_from_spec(server_spec)
server_loader.exec_module(server)
sandbox_loader = SourceFileLoader("agent_durable_sandbox_test", str(SANDBOX))
sandbox_spec = importlib.util.spec_from_loader(sandbox_loader.name, sandbox_loader)
sandbox = importlib.util.module_from_spec(sandbox_spec)
sandbox_loader.exec_module(sandbox)


@contextmanager
def _test_pin(workspace, root=None):
    fd = os.open(workspace, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
    held = os.fstat(fd)
    pin = sandbox.PinnedWorktree(Path(workspace), fd, held.st_dev, held.st_ino, root)
    try:
        yield pin
    finally:
        pin.close()


def test_task_pane_wrapper_denies_mutation_and_passes_read_only(tmp_path):
    real = tmp_path / "real-herdr"
    real.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n", encoding="utf-8")
    real.chmod(0o755)
    env = {**os.environ, "HERDR_REAL_BINARY": str(real),
           "HERDR_DURABLE_TASK_ID": "parent"}
    denied = subprocess.run([str(WRAPPER), "agent", "prompt", "herdr-codex", "work"],
                            env=env, capture_output=True, text=True)
    assert denied.returncode == 126
    assert "denied" in denied.stderr
    allowed = subprocess.run([str(WRAPPER), "agent", "get", "herdr-codex"],
                             env=env, capture_output=True, text=True)
    assert allowed.returncode == 0
    assert allowed.stdout.strip() == "agent get herdr-codex"
    for command in (("agent", "start"), ("agent", "send-keys"),
                    ("pane", "send-text"), ("pane", "run")):
        assert subprocess.run([str(WRAPPER), *command], env=env,
                              capture_output=True).returncode == 126


def _task(tmp_path):
    state = tmp_path / "tasks"
    running = state / "running"
    running.mkdir(parents=True)
    path = running / "parent.json"
    task = {"id": "parent", "run_token": "run-1", "idempotency_key": "attempt-1",
            "attempt_state": "accepted", "task_file": str(path), "repo": "Bbambaaamm/herdr",
            "issue": 82, "workspace": str(tmp_path), "safety_profile": "herdr-core",
            "worktree_root": "/home/agentops/worktrees/herdr",
            "parent_role": "writer", "parent_tools": ["read_file", "search_files"],
            "parent_permissions": [], "execution_session": {
                "agent_name": "parent-agent", "pane_id": "parent-pane",
                "pane_marker": "marker", "session_name": "marker", "owned_pane": True}}
    path.write_text(json.dumps(task), encoding="utf-8")
    return task, path


def _env(monkeypatch, path):
    for name, value in {
        "HERDR_REAL_BINARY": "/bin/true", "HERDR_DURABLE_TASK_ID": "parent",
        "HERDR_DURABLE_RUN_TOKEN": "run-1", "HERDR_DURABLE_TASK_FILE": str(path),
        "HERDR_DURABLE_AGENT": "parent-agent", "HERDR_DURABLE_MARKER": "marker",
        "HERDR_DURABLE_TASK_PANE": "marker", "HERDR_PANE_ID": "parent-pane",
    }.items():
        monkeypatch.setenv(name, value)


def test_forged_parent_context_rejected_before_delivery(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    class NoRunner:
        def run(self, *args, **kwargs):
            raise AssertionError("live control must not be reached")
    for name, wrong in (("HERDR_DURABLE_TASK_ID", "other"),
                        ("HERDR_DURABLE_RUN_TOKEN", "other"),
                        ("HERDR_PANE_ID", "other")):
        original = os.environ[name]
        monkeypatch.setenv(name, wrong)
        with pytest.raises(ValueError):
            bridge._parent_context(NoRunner())
        monkeypatch.setenv(name, original)
    task["execution_session"]["pane_id"] = "different"
    path.write_text(json.dumps(task), encoding="utf-8")
    with pytest.raises(ValueError):
        bridge._parent_context(NoRunner())


def test_parent_context_requires_live_agent_and_marker(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    original_read_bytes = Path.read_bytes
    def read_bytes(target):
        if str(target) == "/proc/123/environ":
            return b"HERDR_DURABLE_TASK_PANE=marker\0"
        return original_read_bytes(target)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)

    class Runner:
        pane = "parent-pane"
        def run(self, args, timeout_seconds=30.0):
            if args[:2] == ["agent", "get"]:
                result = {"agent": {"pane_id": self.pane, "name": "parent-agent"}}
            else:
                result = {"process_info": {"shell_pid": 123}}
            return CommandResult(0, json.dumps({"result": result}), "")
    runner = Runner()
    assert bridge._parent_context(runner)[1] == "parent-pane"
    runner.pane = "other-pane"
    with pytest.raises(ValueError, match="parent agent"):
        bridge._parent_context(runner)


def test_bridge_flushes_claim_before_delivery_and_replay_deduplicates(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    calls = []
    cleanups = []
    class Runtime:
        def __init__(self, scheduler, runner, **kwargs):
            self.scheduler = scheduler
        def run_managed_child(self, lease, prompt, *, run_token, idempotency_key):
            events = self.scheduler.audit_log.replay()
            assert events[-2]["event"] == "claim"
            assert events[-1]["event"] == "child_prompt_bound"
            assert self.scheduler.audit_log._path.read_text().count('"event":"claim"') == 2
            calls.append((lease, run_token, idempotency_key))
            return "settled"
        def cleanup_bound_child(self, task_id):
            cleanups.append(task_id)
    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    args = argparse.Namespace(key="research", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    first = bridge.delegate(args)
    second = bridge.delegate(args)
    assert first["task_id"] == second["task_id"]
    assert len(calls) == 1
    assert first["run_token"] == calls[0][1]
    directory = path.parent.parent / "durable-children" / hashlib.sha256(b"parent:run-1").hexdigest()
    assert ledger_required(directory)
    recovered = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
    recovered.replay()
    rec = recovered._tasks[first["task_id"]]
    assert rec.lease.holder == calls[0][0].holder
    assert rec.run_token == first["run_token"]
    assert rec.fencing_token == first["fencing_token"]
    assert rec.idempotency_key == first["idempotency_key"]
    assert recovered.reclaim(rec.lease.holder) == []

    # A late exact result is reconciled on the same child identity. It does not
    # trigger a second prompt and permits cleanup of the preserved child pane.
    result_dir = directory / "results"
    result_dir.mkdir(exist_ok=True)
    evidence = [{"late": True}]
    evidence_sha = hashlib.sha256(json.dumps(evidence, sort_keys=True,
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    (result_dir / f"{first['task_id']}.result.json").write_text(json.dumps({
        "task_id": first["task_id"], "run_token": first["run_token"],
        "fencing_token": first["fencing_token"], "idempotency_key": first["idempotency_key"],
        "status": "completed", "evidence": evidence, "artifact_sha256": evidence_sha,
    }))
    reconciled = bridge.delegate(args)
    assert reconciled["state"] == "done"
    assert len(calls) == 1
    assert cleanups == [first["task_id"]]

    args.prompt = "different work"
    with pytest.raises(Exception, match="different prompt"):
        bridge.delegate(args)
    args.prompt = "read files"
    (directory / "scheduler.jsonl").unlink()
    with pytest.raises(Exception, match="scheduler ledger missing"):
        bridge.delegate(args)
    assert not (directory / "scheduler.jsonl").exists()


def test_capacity_denial_releases_parent_gate_without_reprompt(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    registry = AdmissionRegistry(tmp_path / "admission-registry.json")
    monkeypatch.setattr(bridge, "AdmissionRegistry", lambda: registry)
    class CapacityRuntime(HerdrChildRuntime):
        def __init__(self, *args, **kwargs):
            kwargs["host_guard"] = lambda: True
            kwargs["admission"] = AdmissionControl(
                audit_log=AdmissionAuditLog(tmp_path / "admission-audit.jsonl"))
            kwargs["resource_usage_factory"] = lambda *_: ResourceUsage(
                active_agents=4, agents_per_repo={}, agents_per_issue={},
                cpu=0.1, ram=0.2, queue_depth=0, elapsed_seconds=1,
                swap_risk=0.0, load1=1.0, logical_cpus=8,
                total_ram_bytes=16 * 1024**3, mem_available_bytes=8 * 1024**3)
            super().__init__(*args, **kwargs)
    monkeypatch.setattr(bridge, "HerdrChildRuntime", CapacityRuntime)
    class Runner:
        executable = "/bin/true"
        def __init__(self):
            self.calls = []
        def run(self, args, **kwargs):
            self.calls.append(tuple(args))
            if args == ["--skill"]:
                return CommandResult(0, "---\nname: herdr\n", "")
            raise AssertionError(f"unexpected child control: {args}")
    runner = Runner()
    args = argparse.Namespace(key="capacity", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    first = bridge.delegate(args, runner=runner)
    assert first["state"] == "blocked"
    assert "child_admission_denied" in first["pre_delivery_failure"]
    assert bridge.delegate(args, runner=runner)["task_id"] == first["task_id"]
    assert runner.calls == [("--skill",)]
    directory = attempt_directory(path.parent.parent, "parent", "run-1")
    replay = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
    replay.replay()
    rec = replay._tasks[first["task_id"]]
    assert rec.lease is None and rec.pre_delivery_failure == first["pre_delivery_failure"]
    assert rec.result_status is None and rec.observed_execution == "unavailable"
    assert rec.cleanup_complete
    assert registry._read() == []
    assert all_children_terminal(path.parent.parent, "parent", "run-1")
    assert sum(e["event"] == "child_pre_delivery_failed" for e in replay.audit_log.replay()) == 1
    assert sum(e["event"] == "child_pre_delivery_cleanup_complete" for e in replay.audit_log.replay()) == 1
    ledger = directory / "scheduler.jsonl"
    lines = ledger.read_text().splitlines()
    ledger.write_text("\n".join(lines[:-1]) + "\n")
    assert not all_children_terminal(path.parent.parent, "parent", "run-1")
    ledger.write_text("\n".join(lines[:-1] + [json.dumps({
        **json.loads(lines[-1]), "fencing_token": -1})]) + "\n")
    assert not all_children_terminal(path.parent.parent, "parent", "run-1")
    ledger.write_text("\n".join(lines) + "\n")
    recovery_loader = SourceFileLoader("capacity_recovery", str(BIN / "agent-stack-recovery"))
    recovery_spec = importlib.util.spec_from_loader(recovery_loader.name, recovery_loader)
    recovery = importlib.util.module_from_spec(recovery_spec)
    recovery_loader.exec_module(recovery)
    recovery.ROOT = path.parent.parent
    for name in ("PENDING", "RUNNING", "DONE", "BLOCKED", "FAILED", "RESULTS", "LOGS"):
        directory_path = recovery.ROOT / name.lower()
        directory_path.mkdir(exist_ok=True)
        setattr(recovery, name, directory_path)
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda parent: True)
    recovery.terminalize_from_result(
        path, task, {"task_id": "parent", "run_token": "run-1",
                     "status": "completed", "evidence": ["done"]}, 0)
    assert (recovery.DONE / path.name).exists()


def test_post_prompt_error_remains_quarantined(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    registry = AdmissionRegistry(tmp_path / "admission-registry.json")
    monkeypatch.setattr(bridge, "AdmissionRegistry", lambda: registry)
    class Runtime(HerdrChildRuntime):
        def prepare(self):
            pass
        def _admit_child(self, lease):
            pass
        def _create_pane(self, *args):
            self._owned_panes.add("child-pane")
            return "child-pane"
        def _sandbox_child_pane(self, pane_id, *args):
            policy = tmp_path / "policy"
            policy.write_text("policy", encoding="utf-8")
            self._sandbox_proofs[pane_id] = {
                "sandbox_pid": 123,
                "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
            }
            return policy
        def _start_agent(self, *args):
            pass
        def _verify_live_child(self, *args, **kwargs):
            return "working"
    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    class Runner:
        executable = "/bin/true"
        def __init__(self):
            self.prompts = 0
        def run(self, args, **kwargs):
            assert args[:2] == ["agent", "prompt"]
            self.prompts += 1
            raise OSError("prompt transport ambiguous")
    runner = Runner()
    args = argparse.Namespace(key="ambiguous", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    with pytest.raises(OSError, match="ambiguous"):
        bridge.delegate(args, runner=runner)
    same = bridge.delegate(args, runner=runner)
    assert same["state"] == "running" and runner.prompts == 1
    assert not all_children_terminal(path.parent.parent, "parent", "run-1")
    replay = DynamicChildScheduler(audit_log=AuditLog(
        attempt_directory(path.parent.parent, "parent", "run-1") / "scheduler.jsonl"))
    replay.replay()
    rec = replay._tasks[same["task_id"]]
    assert rec.pre_delivery_failure is None and rec.execution_pane == "child-pane"


def test_empty_parent_result_placeholder_does_not_block_first_child(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    parent_result = path.parent.parent / "results" / "parent.json"
    parent_result.parent.mkdir(exist_ok=True)
    parent_result.touch()
    registries = []
    class Runtime:
        def __init__(self, scheduler, runner, **kwargs):
            registries.append(kwargs["admission_registry"].path)
        def run_managed_child(self, *args, **kwargs):
            return "working"
    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    args = argparse.Namespace(key="first", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    result = bridge.delegate(args)
    assert result["state"] == "running"
    assert registries == [bridge.AdmissionRegistry().path]


def test_nonempty_parent_result_missing_identity_fails_closed(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    parent_result = path.parent.parent / "results" / "parent.json"
    parent_result.parent.mkdir(exist_ok=True)
    parent_result.write_text("{}", encoding="utf-8")
    args = argparse.Namespace(key="first", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    with pytest.raises(ValueError, match="parent result identity mismatch"):
        bridge.delegate(args)


def test_nonempty_corrupt_parent_result_fails_closed(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    parent_result = path.parent.parent / "results" / "parent.json"
    parent_result.parent.mkdir(exist_ok=True)
    parent_result.write_text("not-json", encoding="utf-8")
    args = argparse.Namespace(key="first", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    with pytest.raises(ValueError, match="parent result is corrupt"):
        bridge.delegate(args)


def test_existing_ledger_without_sentinel_cannot_delegate_or_repair(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    class Runtime:
        def __init__(self, *args, **kwargs):
            pass
        def run_managed_child(self, *args, **kwargs):
            return "working"
    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    args = argparse.Namespace(key="sentinel", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    first = bridge.delegate(args)
    directory = path.parent.parent / "durable-children" / hashlib.sha256(b"parent:run-1").hexdigest()
    sentinel = directory / "scheduler.required"
    assert sentinel.is_file()
    sentinel.unlink()
    with pytest.raises(Exception, match="sentinel missing"):
        bridge.delegate(args)
    assert not sentinel.exists(), "missing sentinel must never be silently recreated"
    replay = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
    replay.replay()
    assert replay._tasks[first["task_id"]].attempt_state == "accepted"


def test_delivery_prompt_specifies_exact_evidence_serialization():
    prompt = bridge._delivery_prompt("inspect", Path("/tmp/result.json"), "child",
                                     "run", 7, "key")
    assert "json.dumps(evidence, sort_keys=True, ensure_ascii=False, allow_nan=False)" in prompt
    assert "default separators/whitespace" in prompt


def test_oversized_managed_prompt_rejected_before_child_spawn(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    args = argparse.Namespace(key="large", role="reader", objective="inspect",
                              prompt="x" * (MAX_PROMPT_CHARS - 100),
                              tool=["read_file"], permission=[])
    with pytest.raises(ValueError, match="managed child prompt exceeds"):
        bridge.delegate(args)
    directory = path.parent.parent / "durable-children" / hashlib.sha256(b"parent:run-1").hexdigest()
    ledger = directory / "scheduler.jsonl"
    assert not ledger.exists()
    assert not ledger_required(directory)
    assert not directory.exists()


def test_boundary_managed_prompt_claims_with_runtime_valid_length(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    directory = path.parent.parent / "durable-children" / hashlib.sha256(b"parent:run-1").hexdigest()
    child_id = "parent-child-" + hashlib.sha256(b"parent:run-1:boundary").hexdigest()[:16]
    result_path = directory / "results" / f"{child_id}.result.json"
    overhead = len(bridge._delivery_prompt("", result_path, child_id,
                                          "x" * 32, 257, "x" * 64))
    prompts = []

    class Runtime:
        def __init__(self, *args, **kwargs):
            pass

        def run_managed_child(self, lease, prompt, **kwargs):
            prompts.append(prompt)
            return "working"

    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    args = argparse.Namespace(key="boundary", role="reader", objective="inspect",
                              prompt="x" * (MAX_PROMPT_CHARS - overhead),
                              tool=["read_file"], permission=[])
    claimed = bridge.delegate(args)
    assert claimed["state"] == "running"
    assert len(prompts) == 1 and len(prompts[0]) <= MAX_PROMPT_CHARS
    assert (directory / "scheduler.jsonl").exists()


def test_bridge_request_prompt_limit_matches_runtime():
    identity = {"task_id": "parent", "run_token": "run-1", "agent": "agent",
                "pane": "pane", "marker": "marker"}
    request = {"operation": "delegate", **identity, "key": "key", "role": "reader",
               "objective": "inspect", "prompt": "x" * MAX_PROMPT_CHARS,
               "tool": [], "permission": [], "cwd": ""}
    assert server.validate_request(request, identity).prompt == request["prompt"]
    request["prompt"] += "x"
    with pytest.raises(ValueError, match="invalid delegation field"):
        server.validate_request(request, identity)


def test_terminal_move_holds_bridge_claim_until_parent_recheck(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    args = argparse.Namespace(key="race", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    entered = threading.Event()
    finished = threading.Event()
    errors = []
    state_root = path.parent.parent
    with parent_attempt_guard(state_root, "parent", "run-1") as terminal:
        assert terminal
        def claim():
            entered.set()
            try:
                bridge.delegate(args)
            except (ValueError, FileNotFoundError) as exc:
                errors.append(exc)
            finally:
                finished.set()
        thread = threading.Thread(target=claim)
        thread.start()
        assert entered.wait(1)
        assert not finished.wait(0.1)
        task["attempt_state"] = "done"
        path.write_text(json.dumps(task), encoding="utf-8")
        done = state_root / "done"
        done.mkdir()
        path.replace(done / path.name)
    thread.join(timeout=2)
    assert finished.is_set() and errors
    ledger = state_root / "durable-children" / hashlib.sha256(b"parent:run-1").hexdigest() / "scheduler.jsonl"
    assert not ledger.exists()


@pytest.mark.parametrize("transition", ["worker_finish", "worker_retry", "recovery_result"])
def test_parent_transition_serializes_real_child_claim(tmp_path, monkeypatch, transition):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    class Runtime:
        def __init__(self, *args, **kwargs):
            pass
        def run_managed_child(self, *args, **kwargs):
            return "working"
    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    args = argparse.Namespace(key="late", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    filename = "agent-task-worker" if transition.startswith("worker") else "agent-stack-recovery"
    module_loader = SourceFileLoader(f"claim_race_{transition}", str(BIN / filename))
    module_spec = importlib.util.spec_from_loader(module_loader.name, module_loader)
    module = importlib.util.module_from_spec(module_spec)
    module_loader.exec_module(module)
    state_root = path.parent.parent
    module.ROOT = state_root
    for name in ("PENDING", "RUNNING", "DONE", "BLOCKED", "FAILED", "RESULTS", "LOGS"):
        directory = state_root / name.lower()
        directory.mkdir(exist_ok=True)
        setattr(module, name, directory)
    if transition != "worker_retry":
        result = {"task_id": "parent", "run_token": "run-1", "status": "completed",
                  "evidence": ["done"]}
        (module.RESULTS / "parent.json").write_text(json.dumps(result))
    if transition == "recovery_result":
        monkeypatch.setattr(module, "cleanup_task_owned_pane", lambda task: True)
    if transition == "worker_finish":
        monkeypatch.setattr(module, "cleanup_task_session", lambda task: True)

    started = threading.Event()
    finished = threading.Event()
    errors = []
    original_move = module.move if transition.startswith("worker") else module.move_task

    def move_under_guard(*move_args):
        def claim():
            started.set()
            try:
                bridge.delegate(args)
            except (ValueError, FileNotFoundError) as exc:
                errors.append(exc)
            finally:
                finished.set()
        thread = threading.Thread(target=claim)
        thread.start()
        assert started.wait(2)
        assert not finished.wait(0.1), "child claim crossed the terminal decision"
        moved = original_move(*move_args)
        return moved

    monkeypatch.setattr(module, "move" if transition.startswith("worker") else "move_task",
                        move_under_guard)
    if transition == "worker_finish":
        module.finish(path, task, "done")
        destination = module.DONE
    elif transition == "worker_retry":
        module.retry(path, task, "provider unavailable")
        destination = module.PENDING
    else:
        module.terminalize_from_result(path, task, result, 0)
        destination = module.DONE
    assert finished.wait(2)
    assert errors
    assert (destination / path.name).exists()
    directory = state_root / "durable-children" / hashlib.sha256(b"parent:run-1").hexdigest()
    assert not (directory / "scheduler.jsonl").exists()


@pytest.mark.parametrize("status,state", [("completed", "done"),
                                          ("blocked", "blocked"),
                                          ("failed", "failed")])
def test_bridge_publishes_only_canonical_child_evidence(tmp_path, monkeypatch, status, state):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    class Runtime:
        def __init__(self, scheduler, runner, **kwargs):
            self.scheduler = scheduler
            self.directory = kwargs["snapshot_path"].parent
        def run_managed_child(self, lease, prompt, *, run_token, idempotency_key):
            assert self.scheduler.bind_execution_session(
                lease.task_id, run_token, lease.agent_id, "child-pane", "child-marker")
            evidence = [{"path": "artifact", "checked": True}]
            digest = hashlib.sha256(json.dumps(evidence, sort_keys=True,
                ensure_ascii=False).encode()).hexdigest()
            result = {"task_id": lease.task_id, "run_token": run_token,
                      "fencing_token": lease.fencing_token,
                      "idempotency_key": idempotency_key, "status": status,
                      "evidence": evidence, "artifact_sha256": digest}
            (self.directory / "results").mkdir(exist_ok=True)
            (self.directory / "results" / f"{lease.task_id}.result.json").write_text(json.dumps(result))
            return "settled"
        def cleanup(self):
            pass
        def cleanup_bound_child(self, task_id):
            pass
    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    args = argparse.Namespace(key="publication", role="reader", objective="inspect",
                              prompt="read files", tool=["read_file"], permission=[])
    result = bridge.delegate(args)
    assert result["state"] == state
    assert result["result_status"] == status
    directory = attempt_directory(path.parent.parent, task["id"], task["run_token"])
    replay = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
    replay.replay()
    assert replay._tasks[result["task_id"]].cleanup_complete
    assert bridge.delegate(args)["task_id"] == result["task_id"]


def test_sandbox_command_is_narrow_and_overmounts_absolute_herdr(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = tmp_path / "herdr-config"
    config.mkdir()
    real = tmp_path / "real-herdr"
    real.write_text("real", encoding="utf-8")
    policy = tmp_path / "policy"
    policy.write_text("policy", encoding="utf-8")
    fake_bwrap = tmp_path / "bwrap"
    fake_bwrap.write_text("", encoding="utf-8")
    monkeypatch.setattr(sandbox, "BWRAP", fake_bwrap)
    monkeypatch.setattr(sandbox, "HERDR_CONFIG", config)
    monkeypatch.setattr(sandbox, "DEFAULT_WRITABLE", ())

    args = sandbox.command(workspace, real, policy=policy)
    joined = " ".join(args)
    assert args[:4] == [str(fake_bwrap), "--ro-bind", "/", "/"]
    assert "--unshare-pid" in args
    assert ["--bind", str(workspace.resolve()), str(workspace.resolve())] == args[
        args.index(str(workspace.resolve())) - 1: args.index(str(workspace.resolve())) + 2
    ]
    assert "/home/agentops /home/agentops" not in joined
    assert "--tmpfs" in args and str(config) in args
    historical = Path("/opt/agent-platform/release-before-cost-router-20260926T224938Z/herdr")
    assert historical.is_relative_to(sandbox.HERDR_RELEASES)
    mounts = [(args[index], args[index + 1], args[index + 2])
              for index in range(len(args) - 2)
              if args[index] in {"--bind", "--ro-bind"}]
    masks = [(index, args[index + 1]) for index in range(len(args) - 1)
             if args[index] == "--tmpfs"]
    release_mask = next(index for index, target in masks
                        if target == str(sandbox.HERDR_RELEASES))
    assert not any(index > release_mask and
                   (target == str(historical) or target == str(sandbox.HERDR_RELEASES)
                    or Path(target).is_relative_to(sandbox.HERDR_RELEASES))
                   for index in range(len(args) - 2)
                   if args[index] in {"--bind", "--ro-bind"}
                   for target in [args[index + 2]])
    assert ["--tmpfs", str(sandbox.HERDR_RELEASES)] == args[release_mask:release_mask + 2]
    assert all(target != str(historical) for _, _, target in mounts)
    pairs = list(zip(args, args[1:], args[2:]))
    assert any(a == "--ro-bind" and b == str(policy) and c == str(real) for a, b, c in pairs)
    assert "HERDR_DURABLE_SANDBOX" in args and "1" in args


def test_child_cwd_requires_exact_git_worktree_for_writer(tmp_path):
    root = tmp_path / "worktrees"
    worktree = root / "issue-82"
    worktree.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(worktree)], check=True)
    task = {"workspace": str(tmp_path), "worktree_root": str(root)}
    args = argparse.Namespace(role="writer", tool=["write_file"],
                              permission=["workspace-write"], cwd=str(worktree))
    assert bridge._resolve_child_cwd(task, args) == worktree.resolve()

    args.cwd = str(root)
    with pytest.raises(ValueError, match="below consumer root"):
        bridge._resolve_child_cwd(task, args)
    outside = tmp_path / "outside"
    outside.mkdir()
    subprocess.run(["git", "init", "-q", str(outside)], check=True)
    args.cwd = str(outside)
    with pytest.raises(ValueError, match="below consumer root"):
        bridge._resolve_child_cwd(task, args)


def test_pinned_writable_worktree_survives_path_swap(tmp_path, monkeypatch):
    root = tmp_path / "worktrees"
    original = root / "issue-82"
    original.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(original)], check=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    task = {"workspace": str(tmp_path), "worktree_root": str(root)}
    request = argparse.Namespace(role="writer", tool=["write_file"],
                                 permission=["workspace-write"], cwd=str(original))
    pin = bridge._pin_child_cwd(task, request)
    try:
        moved = root / "issue-82-moved"
        original.rename(moved)
        original.symlink_to(outside, target_is_directory=True)
        result = tmp_path / "state" / "results" / "child.result.json"
        result.parent.mkdir(parents=True)
        result.touch()
        config = tmp_path / "config"
        config.mkdir()
        real = tmp_path / "real"
        real.touch()
        policy = tmp_path / "policy"
        policy.touch()
        bwrap = tmp_path / "bwrap"
        bwrap.touch()
        monkeypatch.setattr(sandbox, "BWRAP", bwrap)
        monkeypatch.setattr(sandbox, "HERDR_CONFIG", config)
        monkeypatch.setattr(sandbox, "DEFAULT_WRITABLE", ())
        command = sandbox.command(original, real, writable=(result,), policy=policy,
                                  child_workspace_writable=True, pinned_worktree=pin)
        mounts = [(command[i], command[i + 1], command[i + 2])
                  for i in range(len(command) - 2) if command[i] in {"--bind", "--ro-bind", "--bind-fd", "--ro-bind-fd"}]
        assert ("--bind-fd", str(pin.fd), str(original)) in mounts
        assert command.index(pin.source) < command.index("--proc")
        assert os.stat(pin.source).st_ino == moved.stat().st_ino
        assert os.stat(pin.source).st_ino != outside.stat().st_ino
        assert ["--chdir", str(original)] == command[
            command.index("--chdir"):command.index("--chdir") + 2]
    finally:
        pin.close()


def test_pinned_worktree_fd_identity_mismatch_fails_closed(tmp_path):
    workspace = tmp_path / "worktree"
    workspace.mkdir()
    with _test_pin(workspace) as pin:
        pin.inode += 1
        with pytest.raises(RuntimeError, match="pinned_worktree_identity_mismatch"):
            sandbox.command(workspace, Path("/bin/true"),
                            child_workspace_writable=True, pinned_worktree=pin)


def test_delegation_key_binds_replayed_worktree_path_and_inode(tmp_path, monkeypatch):
    task, path = _task(tmp_path)
    _env(monkeypatch, path)
    root = tmp_path / "worktrees"
    first = root / "first"
    second = root / "second"
    for worktree in (first, second):
        worktree.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(worktree)], check=True)
    task["worktree_root"] = str(root)
    path.write_text(json.dumps(task))
    monkeypatch.setattr(bridge, "_parent_context",
                        lambda runner: (task, "parent-pane", "parent-agent", "marker"))
    deliveries = []
    class Runtime:
        def __init__(self, *args, **kwargs):
            pass
        def run_managed_child(self, *args, **kwargs):
            deliveries.append("once")
            return "working"
    monkeypatch.setattr(bridge, "HerdrChildRuntime", Runtime)
    request = argparse.Namespace(key="same-key", role="reader", objective="inspect",
                                 prompt="read files", tool=["read_file"],
                                 permission=[], cwd=str(first))
    child = bridge.delegate(request)
    assert bridge.delegate(request)["task_id"] == child["task_id"]
    assert deliveries == ["once"]
    ledger = attempt_directory(path.parent.parent, "parent", "run-1") / "scheduler.jsonl"
    replay = DynamicChildScheduler(audit_log=AuditLog(ledger))
    replay.replay()
    assert replay._tasks[child["task_id"]].worktree_identity.startswith(str(first) + "|")
    request.cwd = str(second)
    with pytest.raises(Exception, match="delegation key reused"):
        bridge.delegate(request)
    first.rename(root / "first-old")
    first.mkdir()
    subprocess.run(["git", "init", "-q", str(first)], check=True)
    request.cwd = str(first)
    with pytest.raises(Exception, match="delegation key reused"):
        bridge.delegate(request)
    assert deliveries == ["once"]


def test_read_only_child_defaults_to_parent_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    task = {"workspace": str(workspace), "worktree_root": str(tmp_path / "worktrees")}
    args = argparse.Namespace(role="reader", tool=["read_file"], permission=[], cwd="")
    assert bridge._resolve_child_cwd(task, args) == workspace.resolve()
    with _test_pin(workspace) as expected:
        pinned = bridge._pin_child_cwd(task, args)
        try:
            assert pinned.identity == expected.identity
        finally:
            pinned.close()


def test_child_sandbox_workspace_scope_and_exact_result_mount(tmp_path, monkeypatch):
    workspace = tmp_path / "worktrees" / "repo"
    workspace.mkdir(parents=True)
    sibling_worktree = workspace.parent / "sibling"
    sibling_worktree.mkdir()
    cache = tmp_path / "cache"
    cache.symlink_to(sibling_worktree, target_is_directory=True)
    hermes = tmp_path / "hermes"
    hermes.mkdir()
    result_dir = tmp_path / "state" / "results"
    result_dir.mkdir(parents=True)
    mine = result_dir / "mine.result.json"
    sibling = result_dir / "sibling.result.json"
    mine.touch()
    sibling.touch()
    config = tmp_path / "config"
    config.mkdir()
    real = tmp_path / "real"
    real.touch()
    policy = tmp_path / "policy"
    policy.touch()
    bwrap = tmp_path / "bwrap"
    bwrap.touch()
    monkeypatch.setattr(sandbox, "BWRAP", bwrap)
    monkeypatch.setattr(sandbox, "HERDR_CONFIG", config)
    monkeypatch.setattr(sandbox, "DEFAULT_WRITABLE", (cache, hermes, workspace.parent))
    for allowed in (False, True):
        with _test_pin(workspace, workspace.parent) as pin:
            args = sandbox.command(workspace, real, writable=(mine,), policy=policy,
                                   child_workspace_writable=allowed,
                                   pinned_worktree=pin)
        mounts = [(args[i], args[i + 1], args[i + 2])
                  for i in range(len(args) - 2) if args[i] in {"--bind", "--ro-bind", "--bind-fd", "--ro-bind-fd"}]
        # Provider egress + the abstract durable bridge require the host net
        # namespace; network model-tools are filtered at Hermes toolset level.
        assert "--unshare-net" not in args
        assert not any(mode == "--bind" and target in {
            str(sandbox.HOME / ".hermes"), str(sandbox.HOME / ".cache")}
            for mode, _, target in mounts)
        assert (("--bind-fd" if allowed else "--ro-bind-fd"), str(pin.fd), str(workspace)) in mounts
        assert ("--bind", str(workspace.parent), str(workspace.parent)) not in mounts
        assert ("--bind", str(mine), str(mine)) in mounts
        assert not any(mode == "--bind" and target == str(sibling)
                       for mode, _, target in mounts)
        assert not any(mode == "--bind" and target == str(sibling_worktree)
                       for mode, _, target in mounts)
        assert not any(mode == "--bind" and target == str(result_dir)
                       for mode, _, target in mounts)


def test_generated_sandbox_hides_historical_release_and_control_socket(tmp_path):
    if not (sandbox.BWRAP.is_file() and sandbox.HERDR_CONFIG.is_dir()
            and Path("/home/agentops/.local/bin/herdr").is_file()):
        pytest.skip("host Herdr sandbox prerequisites unavailable")
    probe = subprocess.run([str(sandbox.BWRAP), "--ro-bind", "/", "/", "--", "/bin/true"],
                           capture_output=True, text=True)
    if "No permissions to create a new namespace" in probe.stderr:
        pytest.skip("user namespaces unavailable in test environment")
    assert probe.returncode == 0, probe.stderr

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    policy = tmp_path / "policy"
    policy.write_text("policy", encoding="utf-8")
    historical = "/opt/agent-platform/release-before-cost-router-20260926T224938Z/herdr"
    args = sandbox.command(workspace, Path("/home/agentops/.local/bin/herdr"), policy=policy)
    args = args[:args.index("--")] + ["--", "/bin/sh", "-c",
        'test ! -e "$1" && test ! -e /home/agentops/.config/herdr/herdr.sock '
        '&& test ! -e /home/agentops/.config/herdr/config.toml '
        '&& test "$(cat /home/agentops/.local/bin/herdr)" = policy', "sh", historical]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_rpc_client_uses_only_abstract_bridge_and_strict_schema(monkeypatch):
    name = "@herdr-test-rpc-" + os.urandom(4).hex()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
        try:
            probe.bind("\0" + name[1:] + "-probe")
        except OSError as exc:
            if exc.errno == errno.EPERM:
                pytest.skip("abstract Unix sockets are unavailable in this sandbox")
            raise
    received = {}
    ready = threading.Event()

    def serve_once():
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind("\0" + name[1:])
            listener.listen(1)
            ready.set()
            connection, _ = listener.accept()
            with connection:
                length = int.from_bytes(bridge._receive(connection, 4), "big")
                request = json.loads(bridge._receive(connection, length))
                received.update(request)
                payload = json.dumps({"ok": True, "result": {"task_id": "child"}, "error": None}).encode()
                connection.sendall(len(payload).to_bytes(4, "big") + payload)

    thread = threading.Thread(target=serve_once, daemon=True)
    thread.start()
    ready.wait(2)
    for key, value in {
        "HERDR_DURABLE_SANDBOX": "1",
        "HERDR_DURABLE_BRIDGE_SOCKET": name,
        "HERDR_DURABLE_TASK_ID": "parent",
        "HERDR_DURABLE_RUN_TOKEN": "run-1",
        "HERDR_DURABLE_AGENT": "parent-agent",
        "HERDR_PANE_ID": "parent-pane",
        "HERDR_DURABLE_MARKER": "marker",
        "HERDR_REAL_BINARY": "/definitely/not/executed",
    }.items():
        monkeypatch.setenv(key, value)
    args = argparse.Namespace(key="k", role="reader", objective="inspect", prompt="read",
                              tool=["read_file"], permission=[])
    assert bridge.client_delegate(args) == {"task_id": "child"}
    thread.join(2)
    assert set(received) == server.FIELDS
    assert received["operation"] == "delegate"
    assert "task_file" not in received
    assert received["task_id"] == "parent"


def test_bridge_request_schema_rejects_unknown_and_forged_identity():
    identity = {"task_id": "parent", "run_token": "run", "agent": "a", "pane": "p", "marker": "m"}
    request = {
        "operation": "delegate", "task_id": "parent", "run_token": "run",
        "agent": "a", "pane": "p", "marker": "m", "key": "k", "role": "reader",
        "objective": "o", "prompt": "p", "tool": [], "permission": [], "cwd": "",
    }
    assert server.validate_request(request, identity).key == "k"
    with pytest.raises(ValueError, match="schema"):
        server.validate_request({**request, "extra": True}, identity)
    with pytest.raises(ValueError, match="schema"):
        server.validate_request({**request, "operation": "exec"}, identity)
    with pytest.raises(ValueError, match="identity"):
        server.validate_request({**request, "run_token": "forged"}, identity)


def test_bridge_follows_task_move_without_trusting_client_path(tmp_path):
    task, running = _task(tmp_path)
    root = running.parent.parent
    assert server._current_task_file(root, "parent", "run-1") == running.resolve()
    blocked_dir = root / "blocked"
    blocked_dir.mkdir()
    blocked = blocked_dir / running.name
    running.replace(blocked)
    assert server._current_task_file(root, "parent", "run-1") == blocked.resolve()
    done_dir = root / "done"
    done_dir.mkdir()
    done = done_dir / blocked.name
    blocked.replace(done)
    with pytest.raises(ValueError, match="terminal"):
        server._current_task_file(root, "parent", "run-1")
