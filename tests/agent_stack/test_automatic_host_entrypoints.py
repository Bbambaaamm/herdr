"""Host launch wiring: real dispatch/bridge paths with explicit authority doubles."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import os
import sys

import pytest

from herdr import host_configuration as host, launch_plan_issuer as issuer
from herdr.host_bootstrap import PYTHON_TARGET

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "agent-stack/bin"
sys.path.insert(0, str(BIN))


def load(name, entry):
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader(name, str(BIN / entry))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def protected_policy(tmp_path, monkeypatch):
    # The reader/root authority are doubles here; launcher arguments and actual
    # dispatcher state writes are tested. This is not privileged acceptance.
    code = tmp_path / "published-code"
    code.mkdir()
    source = code / "herdr/host_configuration.py"
    source.parent.mkdir()
    source.touch()
    monkeypatch.setattr(host, "__file__", str(source))
    raw = {"schema_version": 2, "host_uid": os.geteuid(),
           "code": {"source": str(code)},
           "runtime": [{"source": str(tmp_path / "published-python"),
                        "target": str(PYTHON_TARGET)}],
           "private_launch": {"plan_handoff": {"automatic_issuer": True}}}
    authority = {"entrypoints": ["agent-stack/bin/agent-task-worker",
                                "agent-stack/bin/agent-durable-bridge"]}
    monkeypatch.setattr(host, "_read_configuration", lambda path: deepcopy(raw))
    monkeypatch.setattr(issuer, "_policy", lambda: (deepcopy(authority), deepcopy(raw)))
    return raw, authority


@pytest.mark.parametrize("entry", ["agent-task-worker", "agent-durable-bridge"])
def test_automatic_host_command_selects_only_pinned_wrapper(tmp_path, monkeypatch, entry):
    raw, authority = protected_policy(tmp_path, monkeypatch)
    args = ["literal task with spaces", "--literal"]
    binding = {}
    result = host.host_entrypoint_command("agent-stack/bin/" + entry, args,
                                         legacy_command=["/mutable/legacy"], binding=binding)
    assert binding == {"host_policy_sha256": issuer._digest(raw), "code_source": raw["code"]["source"]}
    assert result == [str(tmp_path / "published-python/bin/python3.11"), "-I", "-B",
                      raw["code"]["source"] + "/" + issuer.HOST_ENTRYPOINT,
                      "agent-stack/bin/" + entry, *args]
    assert args == ["literal task with spaces", "--literal"]


@pytest.mark.parametrize("state", ["missing", "schema1", "manual"])
def test_legacy_host_commands_keep_the_existing_invocation(tmp_path, monkeypatch, state):
    legacy = ["/existing/python", "/existing/bridge", "--arg", "literal"]
    if state == "missing":
        def missing(path):
            raise FileNotFoundError(path)
        monkeypatch.setattr(host, "_read_configuration", missing)
    else:
        raw = {"schema_version": 1} if state == "schema1" else {
            "schema_version": 2, "private_launch": {"plan_handoff": {}}}
        monkeypatch.setattr(host, "_read_configuration", lambda path: raw)
    monkeypatch.setattr(issuer, "_policy", lambda: pytest.fail("manual mode contacted issuer"))
    result = host.host_entrypoint_command("agent-stack/bin/agent-durable-bridge",
                                         ["literal"], legacy_command=legacy)
    assert result == legacy and result is not legacy


@pytest.mark.parametrize("fault", ["wrong-release", "wrong-uid", "unknown-entry",
                                  "policy-race", "false-opt-in", "bool-version",
                                  "malformed-handoff", "bad-argument"])
def test_automatic_host_command_denies_invalid_authority(tmp_path, monkeypatch, fault):
    raw, authority = protected_policy(tmp_path, monkeypatch)
    args = ["literal"]
    if fault == "wrong-release":
        raw["code"]["source"] = str(tmp_path / "other")
    elif fault == "wrong-uid":
        raw["host_uid"] += 1
    elif fault == "unknown-entry":
        authority["entrypoints"] = ["agent-stack/bin/other"]
    elif fault == "policy-race":
        changed = deepcopy(raw)
        changed["host_uid"] += 1
        monkeypatch.setattr(issuer, "_policy", lambda: (authority, changed))
    elif fault == "false-opt-in":
        raw["private_launch"]["plan_handoff"]["automatic_issuer"] = False
    elif fault == "bool-version":
        raw["schema_version"] = True
    elif fault == "malformed-handoff":
        raw["private_launch"]["plan_handoff"] = "task-selected"
    elif fault == "bad-argument":
        args = ["embedded\0argument"]
    with pytest.raises(host.SecurityError):
        host.host_entrypoint_command("agent-stack/bin/agent-task-worker", args,
                                     legacy_command=["unsafe-fallback"])


def setup_dispatcher(tmp_path, monkeypatch):
    dispatcher = load("automatic_dispatch_test", "agent-task-dispatcher")
    dispatcher.ROOT = tmp_path
    dispatcher.PENDING = tmp_path / "pending"
    dispatcher.RUNNING = tmp_path / "running"
    dispatcher.LOG = tmp_path / "dispatch.log"
    for path in (dispatcher.PENDING, dispatcher.RUNNING, tmp_path / "logs"):
        path.mkdir()
    task = dispatcher.PENDING / "work.json"
    task.write_text(json.dumps({"id": "work", "priority": 1}))
    monkeypatch.setattr(dispatcher, "worker_running", lambda: False)
    return dispatcher, task


def test_real_dispatcher_passes_the_host_wrapper_to_popen(tmp_path, monkeypatch):
    dispatcher, task = setup_dispatcher(tmp_path, monkeypatch)
    wrapped = ["/pinned/python", "-I", "-B", "/pinned/wrapper",
               "agent-stack/bin/agent-task-worker", str(dispatcher.RUNNING / task.name)]
    def command(entry, args, **kwargs):
        assert entry == "agent-stack/bin/agent-task-worker"
        assert args == [str(dispatcher.RUNNING / task.name)]
        assert task.exists() and not (dispatcher.RUNNING / task.name).exists()
        return wrapped
    monkeypatch.setattr(dispatcher, "host_entrypoint_command", command, raising=False)
    calls = []
    def popen(argv, **kwargs):
        calls.append((argv, kwargs))
        monkeypatch.setattr(dispatcher, "worker_running", lambda: True)
        return SimpleNamespace(poll=lambda: None)
    monkeypatch.setattr(dispatcher.subprocess, "Popen", popen)
    dispatcher.ENV = {**dispatcher.ENV, "PYTHONPATH": "/attacker", "LD_PRELOAD": "/attacker.so"}
    assert dispatcher.launch(task) == 0
    assert calls[0][0] == wrapped
    assert "PYTHONPATH" not in calls[0][1]["env"] and "LD_PRELOAD" not in calls[0][1]["env"]
    assert json.loads((dispatcher.RUNNING / task.name).read_text())["dispatch_claimed_at"]


def test_dispatcher_denial_preserves_pending_bytes_before_claim(tmp_path, monkeypatch):
    dispatcher, task = setup_dispatcher(tmp_path, monkeypatch)
    original = task.read_bytes()
    def denied(*args, **kwargs):
        raise host.SecurityError("entrypoint not approved")
    monkeypatch.setattr(dispatcher, "host_entrypoint_command", denied, raising=False)
    monkeypatch.setattr(dispatcher.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("denial spawned worker"))
    with pytest.raises(host.SecurityError):
        dispatcher.launch(task)
    assert task.read_bytes() == original and not list(dispatcher.RUNNING.iterdir())
    assert not dispatcher.LOG.exists() and not list((tmp_path / "logs").iterdir())


def test_actual_start_bridge_uses_wrapped_command(tmp_path, monkeypatch):
    worker = load("automatic_bridge_start_test", "agent-task-worker")
    worker.LOGS = tmp_path / "logs"
    assert not any(key.startswith("PYTHON") for key in worker.ENV)
    path = tmp_path / "task.json"
    path.write_text("{}")
    task = {"id": "task", "run_token": "run", "task_file": str(path)}
    session = {"agent_name": "agent", "pane_id": "pane", "pane_marker": "marker"}
    wrapped = ["/pinned/python", "-I", "-B", "/pinned/wrapper", "agent-stack/bin/agent-durable-bridge"]
    selected = []
    def command(entry, args, **kwargs):
        selected.append(args)
        assert entry == "agent-stack/bin/agent-durable-bridge"
        assert args[:2] == ["--task-file", str(path)]
        return wrapped + args
    monkeypatch.setattr(worker, "host_entrypoint_command", command, raising=False)
    monkeypatch.setattr(worker, "bridge_alive", lambda session: False)
    monkeypatch.setattr(worker, "persist_execution_session", lambda task: None)
    monkeypatch.setattr(worker, "process_start_ticks", lambda pid: 44)
    calls = []
    monkeypatch.setattr(worker.subprocess, "Popen",
                        lambda argv, **kwargs: calls.append(argv) or SimpleNamespace(pid=123, poll=lambda: None))
    class Socket:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): pass
        def connect(self, address): pass
    monkeypatch.setattr(worker.socket, "socket", lambda *args: Socket())
    worker.start_bridge(task, session)
    assert calls == [wrapped + selected[0]]
    assert session["bridge_pid"] == 123 and session["bridge_task_id"] == "task"
    assert session["bridge_launch"]["argv"] == calls[0]
    assert session["bridge_launch"]["process_start_ticks"] == 44


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("forged", [False, True])
def test_bridge_liveness_and_stop_recognize_exact_launch_prefix(tmp_path, monkeypatch, wrapped, forged):
    worker = load("automatic_bridge_liveness_test", "agent-task-worker")
    expected = ([str(tmp_path / "python"), "-I", "-B", str(tmp_path / "wrapper"),
                 "agent-stack/bin/agent-durable-bridge"] if wrapped else
                [sys.executable, str(worker.BRIDGE)])
    monkeypatch.setattr(worker, "host_entrypoint_command",
                        lambda *args, **kwargs: expected, raising=False)
    issued = [*expected, "--task-id", "task", "--run-token", "run"]
    argv = list(issued)
    if forged: argv.insert(0, "/unapproved-launcher")
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda path: "\0".join(argv).encode() + b"\0"
                        if str(path) == "/proc/123/cmdline" else original(path))
    session = {"bridge_pid": 123, "bridge_task_id": "task", "bridge_run_token": "run",
               "bridge_socket": worker.bridge_socket_name({"id": "task", "run_token": "run"})}
    session["bridge_launch"] = {"schema_version": "herdr-host-bridge-launch-1",
        "argv": issued, "process_start_ticks": 44,
        "host_policy_sha256": "a" * 64 if wrapped else None,
        "code_source": str(tmp_path) if wrapped else None}
    monkeypatch.setattr(worker, "process_start_ticks", lambda pid: 44)
    monkeypatch.setattr(worker, "_bridge_process_live", lambda pid: True)
    monkeypatch.setattr(worker, "host_entrypoint_command", lambda *args, **kwargs: pytest.fail("current policy cannot redefine a live bridge"))
    assert worker.bridge_alive(session) is (not forged)
    killed = []
    monkeypatch.setattr(worker.os, "kill", lambda *args: killed.append(args))
    if forged:
        with pytest.raises(RuntimeError, match="identity_unverified"):
            worker.stop_bridge(session)
    else:
        worker.stop_bridge(session)
    assert bool(killed) is (not forged)


def test_reused_bridge_pid_requires_reconciliation_before_stop_or_restart(tmp_path, monkeypatch):
    worker = load("automatic_bridge_reuse_test", "agent-task-worker")
    argv = ["/old/pinned/python", "-I", "-B", "/old/pinned/wrapper",
            "agent-stack/bin/agent-durable-bridge", "--task-id", "task", "--run-token", "run"]
    session = {"bridge_pid": 123, "bridge_task_id": "task", "bridge_run_token": "run",
               "bridge_socket": worker.bridge_socket_name({"id": "task", "run_token": "run"}),
               "bridge_launch": {"schema_version": "herdr-host-bridge-launch-1",
                 "argv": argv, "process_start_ticks": 44,
                 "host_policy_sha256": "a" * 64, "code_source": "/old/pinned"}}
    original_read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda path: "\0".join(argv).encode() + b"\0"
                        if str(path) == "/proc/123/cmdline" else original_read(path))
    monkeypatch.setattr(worker, "_bridge_process_live", lambda pid: True)
    monkeypatch.setattr(worker, "process_start_ticks", lambda pid: 45)
    monkeypatch.setattr(worker.os, "kill", lambda *args: pytest.fail("reused PID was signalled"))
    monkeypatch.setattr(worker.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("a second bridge was started"))
    assert not worker.bridge_alive(session)
    with pytest.raises(RuntimeError, match="identity_unverified"):
        worker.stop_bridge(session)
    with pytest.raises(RuntimeError, match="identity_unverified"):
        worker.start_bridge({}, session)


@pytest.mark.parametrize("state", ["Z", "X", "S", "unreadable"])
def test_bridge_reconciliation_distinguishes_exited_from_live_processes(monkeypatch, state):
    worker = load("automatic_bridge_process_state_test", "agent-task-worker")
    original_read = Path.read_text
    def stat_text(path, *args, **kwargs):
        if str(path) == "/proc/123/stat":
            if state == "unreadable": raise PermissionError("explicit proc reader double")
            return f"123 (bridge name with ) bracket) {state} 1 2 3"
        return original_read(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", stat_text)
    assert worker._bridge_process_live(123) is (state in {"S", "unreadable"})
    monkeypatch.setattr(worker, "bridge_alive", lambda session: False)
    monkeypatch.setattr(worker.os, "kill", lambda *args: pytest.fail("unverified or exited process signalled"))
    session = {"bridge_pid": 123}
    if state in {"S", "unreadable"}:
        with pytest.raises(RuntimeError, match="identity_unverified"):
            worker.stop_bridge(session)
    else:
        worker.stop_bridge(session)
