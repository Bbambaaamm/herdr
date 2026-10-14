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
    monkeypatch.setattr(worker.os, "pidfd_open", lambda *args: os.open("/dev/null", os.O_RDONLY))
    monkeypatch.setattr(worker.signal, "pidfd_send_signal", lambda *args: killed.append(args))
    monkeypatch.setattr(worker, "_bridge_exited", lambda pidfd: True)
    monkeypatch.setattr(worker.os, "kill", lambda *args: pytest.fail("numeric PID signal is forbidden"))
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
    monkeypatch.setattr(worker.os, "pidfd_open", lambda *args: os.open("/dev/null", os.O_RDONLY))
    monkeypatch.setattr(worker.signal, "pidfd_send_signal", lambda *args: pytest.fail("reused process was signalled"))
    monkeypatch.setattr(worker.os, "kill", lambda *args: pytest.fail("numeric PID signal is forbidden"))
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
    monkeypatch.setattr(worker.os, "pidfd_open", lambda *args: os.open("/dev/null", os.O_RDONLY))
    monkeypatch.setattr(worker.signal, "pidfd_send_signal", lambda *args: pytest.fail("unverified or exited process signalled"))
    session = {"bridge_pid": 123}
    if state in {"S", "unreadable"}:
        with pytest.raises(RuntimeError, match="identity_unverified"):
            worker.stop_bridge(session)
    else:
        worker.stop_bridge(session)


@pytest.mark.parametrize("exit_during_verification", [False, True])
def test_bridge_stop_uses_actual_stable_pidfd(monkeypatch, exit_during_verification):
    import subprocess
    worker = load("automatic_bridge_actual_pidfd_test", "agent-task-worker")
    process = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(60)"])
    def verified(session):
        # Launch identity is an explicit double; the handle and signal are real.
        if exit_during_verification:
            handle = os.pidfd_open(process.pid, 0)
            try: worker.signal.pidfd_send_signal(handle, worker.signal.SIGTERM)
            finally: os.close(handle)
            process.wait(timeout=5)
        return True
    monkeypatch.setattr(worker, "bridge_alive", verified)
    monkeypatch.setattr(worker.os, "kill", lambda *args: pytest.fail("numeric PID signal is forbidden"))
    try:
        worker.stop_bridge({"bridge_pid": process.pid})
        process.wait(timeout=5)
        assert process.returncode is not None
    finally:
        if process.poll() is None:
            handle = os.pidfd_open(process.pid, 0)
            try: worker.signal.pidfd_send_signal(handle, worker.signal.SIGKILL)
            finally: os.close(handle)
            process.wait(timeout=5)


def test_bridge_exit_timeout_keeps_cleanup_unproven(monkeypatch):
    worker = load("automatic_bridge_exit_timeout_test", "agent-task-worker")
    monkeypatch.setattr(worker.os, "pidfd_open", lambda *args: os.open("/dev/null", os.O_RDONLY))
    monkeypatch.setattr(worker.signal, "pidfd_send_signal", lambda *args: None)
    monkeypatch.setattr(worker, "bridge_alive", lambda session: True)
    monkeypatch.setattr(worker, "_bridge_exited", lambda pidfd: False)
    session = {"bridge_pid": 123, "closed_at": "previous-marker"}
    assert not worker._cleanup_bridge(session)
    assert "closed_at" not in session
    assert session["cleanup_status"] == "bridge_cleanup_unproven"


@pytest.mark.parametrize("closed", [False, True])
def test_unverified_bridge_cannot_close_or_replace_session(tmp_path, monkeypatch, closed):
    worker = load("automatic_bridge_cleanup_gate_test", "agent-task-worker")
    session = {"owned_pane": True, "pane_id": "owned", "bridge_pid": 123}
    if closed: session["closed_at"] = "stale-closed-marker"
    task = {"execution_session": session}
    monkeypatch.setattr(worker, "_cleanup_prepared_root_launch", lambda task: None)
    monkeypatch.setattr(worker, "_herdr_json", lambda *args, **kwargs: {"result": {"panes": []}})
    monkeypatch.setattr(worker, "stop_bridge",
                        lambda session: (_ for _ in ()).throw(RuntimeError("durable_bridge_identity_unverified")))
    assert worker.cleanup_task_session(task) is False
    assert "closed_at" not in session
    assert session["cleanup_status"] == "bridge_cleanup_unproven"
    with pytest.raises(RuntimeError, match="previous_task_session_not_closed"):
        worker.prepare_attempt(task)


def test_setup_cleanup_keeps_failed_bridge_session_open(tmp_path, monkeypatch):
    from tests.agent_stack import test_worker_handshake as fixture
    fixture.configure_paths(tmp_path)
    fixture.explicit_host_policy_for_worker_lifecycle_tests.__wrapped__(monkeypatch)
    worker = fixture.worker
    task = fixture.base_task()
    task.update(workspace=str(tmp_path / "workspace"), run_token="setup-run",
                routing={"selected_agent": "quantlab-hermes"})
    def native(args, **kwargs):
        if args[:2] == ["agent", "get"]:
            return {"result": {"agent": {"agent": "hermes", "pane_id": "coordinator", "workspace_id": "w2"}}}
        if args[:2] == ["pane", "split"]: return {"result": {"pane": {"pane_id": "owned-pane"}}}
        if args[:2] == ["pane", "list"]: return {"result": {"panes": []}}
        raise AssertionError(args)
    def start(task, session):
        session["bridge_pid"] = 123
        raise RuntimeError("durable_bridge_identity_unverified")
    monkeypatch.setattr(worker, "_herdr_json", native)
    monkeypatch.setattr(worker, "start_bridge", start)
    monkeypatch.setattr(worker, "_cleanup_setup_pane", lambda *args, **kwargs: True)
    monkeypatch.setattr(worker, "_cleanup_prepared_root_launch", lambda task: None)
    monkeypatch.setattr(worker, "frozen_policy", lambda: fixture._policy_file(tmp_path))
    monkeypatch.setattr(worker, "sandbox_command", lambda *args, **kwargs: ["bwrap"])
    monkeypatch.setattr(worker, "stop_bridge",
                        lambda session: (_ for _ in ()).throw(RuntimeError("durable_bridge_identity_unverified")))
    with pytest.raises(RuntimeError, match="task_session_cleanup_failed:bridge_cleanup_unproven"):
        worker.create_task_session(task)
    assert "closed_at" not in task["execution_session"]
    assert task["execution_session"]["cleanup_status"] == "bridge_cleanup_unproven"


def test_worker_startup_reconciles_owned_stale_closed_session(tmp_path, monkeypatch):
    from tests.agent_stack import test_worker_handshake as fixture
    fixture.configure_paths(tmp_path)
    worker = fixture.worker
    task = fixture.base_task()
    worker.prepare_attempt(task)
    token = task["run_token"]
    task["attempt_state"] = "retry_scheduled"
    task["execution_session"] = {"owned_pane": True, "pane_id": "owned",
        "bridge_pid": 123, "closed_at": "stale-marker"}
    path = worker.PENDING / "task-1.json"
    worker.write_json(path, task)
    monkeypatch.setattr(worker, "prepare_attempt", lambda *args: pytest.fail("old session was replaced"))
    monkeypatch.setattr(worker, "_herdr_json", lambda *args, **kwargs: {"result": {"panes": []}})
    monkeypatch.setattr(worker, "stop_bridge",
                        lambda session: (_ for _ in ()).throw(RuntimeError("durable_bridge_identity_unverified")))
    assert worker.main(path) == 1
    saved = json.loads((worker.BLOCKED / path.name).read_text())
    assert saved["run_token"] == token and saved["attempts"] == 0
    assert "closed_at" not in saved["execution_session"]
    assert saved["execution_session"]["cleanup_status"] == "bridge_cleanup_unproven"


@pytest.mark.parametrize("child", [False, True])
def test_worker_quarantines_automatic_plan_ambiguity_without_retry(tmp_path, monkeypatch, child):
    from tests.agent_stack import test_worker_handshake as fixture
    from herdr.launch_plan_handoff import LaunchPlanReconciliationRequired
    fixture.configure_paths(tmp_path)
    worker = fixture.worker
    task = fixture.base_task()
    if child:
        task.update(parent_task_id="parent", run_token="child-run",
                    idempotency_key="child-key", fencing_token=7, delegation_key="scope")
    path = worker.RUNNING / "task-1.json"
    worker.write_json(path, task)
    monkeypatch.setattr(worker, "ensure_parent_scope", lambda task: None)
    monkeypatch.setattr(worker, "freeze_plan", lambda *args: None)
    monkeypatch.setattr(worker, "decide_model_route", lambda task: {"tier": "free", "selected_agent": "fixture"})
    monkeypatch.setattr(worker, "record_model_route", lambda *args: None)
    attempted = []
    def session(task):
        attempted.append((task["run_token"], task["idempotency_key"], task["attempts"]))
        raise LaunchPlanReconciliationRequired("ambiguous plan")
    monkeypatch.setattr(worker, "create_task_session", session)
    monkeypatch.setattr(worker, "retry", lambda *args: pytest.fail("ambiguous plan caused redispatch"))
    monkeypatch.setattr(worker, "run_prompt", lambda *args: pytest.fail("provider dispatch before plan reconciliation"))
    assert worker.main(path) == 1
    saved = json.loads((worker.BLOCKED / path.name).read_text())
    assert [(saved["run_token"], saved["idempotency_key"], saved["attempts"])] == attempted
    assert saved["attempts"] == 0 and not list(worker.PENDING.iterdir())
    result = json.loads(worker.result_path(task["id"]).read_text())
    assert result["blocker"] == "task_launch_plan_reconciliation_required"



def unresolved_private_launch_fixture(tmp_path, monkeypatch):
    """Real create_task_session flow; authority/native transport are explicit doubles."""
    from tests.agent_stack import test_worker_handshake as fixture
    from herdr.launch_plan_handoff import LaunchPlanReconciliationRequired
    fixture.configure_paths(tmp_path)
    fixture.explicit_host_policy_for_worker_lifecycle_tests.__wrapped__(monkeypatch)
    worker = fixture.worker
    factory = worker.HOST_POLICY_LAUNCH_FACTORY
    original = factory.prepare
    def prepare(**kwargs):
        launch = original(**kwargs)
        launch.private_profile_snapshot = SimpleNamespace(name="quantlab")
        def unresolved(builder):
            raise LaunchPlanReconciliationRequired("published plan reply unavailable")
        monkeypatch.setattr(launch, "prepare_private_command", unresolved)
        return launch
    monkeypatch.setattr(factory, "prepare", prepare)
    def native(args, **kwargs):
        assert args[:2] == ["agent", "get"], "no pane/provider action is allowed"
        return {"result": {"agent": {"agent": "hermes", "pane_id": "coordinator",
                                     "workspace_id": "workspace"}}}
    monkeypatch.setattr(worker, "_herdr_json", native)
    monkeypatch.setattr(worker, "_preflight_root_provider",
                        lambda *args: pytest.fail("private launch refreshed provider credentials"))
    monkeypatch.setattr(worker, "frozen_policy", lambda: fixture._policy_file(tmp_path))
    def cleanup(task):
        raise RuntimeError("launch storage changed before cleanup")
    monkeypatch.setattr(worker, "_cleanup_prepared_root_launch", cleanup)
    return worker, fixture.base_task()


def test_actual_pre_split_cleanup_failure_is_blocking_and_retains_evidence(tmp_path, monkeypatch):
    from herdr.launch_plan_handoff import LaunchPlanReconciliationRequired
    worker, task = unresolved_private_launch_fixture(tmp_path, monkeypatch)
    worker.prepare_attempt(task)
    task.update(workspace=str(tmp_path), fencing_token=1)
    with pytest.raises(RuntimeError, match="task_session_cleanup_failed:pre_split") as error:
        worker.create_task_session(task)
    assert isinstance(error.value.__cause__, RuntimeError)
    assert "launch storage changed" in str(error.value.__cause__)
    assert "LaunchPlanReconciliationRequired" in str(error.value)
    session = task["execution_session"]
    assert session["pane_split_started"] is False and "closed_at" not in session
    assert session["cleanup_status"] == "launch_cleanup_failed"
    assert Path(session["policy_file"]).is_file()
    assert (task["id"], task["run_token"]) in worker.HOST_POLICY_LAUNCHES


@pytest.mark.parametrize("child", [False, True])
def test_actual_worker_quarantines_lost_reply_plus_cleanup_failure(tmp_path, monkeypatch, child):
    worker, task = unresolved_private_launch_fixture(tmp_path, monkeypatch)
    task["workspace"] = str(tmp_path)
    if child:
        task.update(parent_task_id="parent", run_token="child-run", idempotency_key="child-key",
                    fencing_token=7, delegation_key="scope")
    path = worker.RUNNING / "task-1.json"
    worker.write_json(path, task)
    monkeypatch.setattr(worker, "ensure_parent_scope", lambda task: None)
    monkeypatch.setattr(worker, "freeze_plan", lambda *args: None)
    monkeypatch.setattr(worker, "decide_model_route",
                        lambda task: {"tier": "free", "selected_agent": "fixture"})
    monkeypatch.setattr(worker, "record_model_route", lambda *args: None)
    attempted = []
    real = worker.create_task_session
    def create(task):
        attempted.append((task["run_token"], task["idempotency_key"], task["attempts"]))
        return real(task)
    monkeypatch.setattr(worker, "create_task_session", create)
    monkeypatch.setattr(worker, "retry", lambda *args: pytest.fail("cleanup failure caused redispatch"))
    monkeypatch.setattr(worker, "run_prompt", lambda *args: pytest.fail("unreconciled plan reached provider"))
    assert worker.main(path) == 1
    saved = json.loads((worker.BLOCKED / path.name).read_text())
    assert [(saved["run_token"], saved["idempotency_key"], saved["attempts"])] == attempted
    assert saved["attempts"] == 0 and not list(worker.PENDING.iterdir())
    assert saved["attempt_state"] == "delivery_uncertain"
    session = saved["execution_session"]
    assert session["cleanup_status"] == "launch_cleanup_failed" and "closed_at" not in session
    assert Path(session["policy_file"]).is_file()
    assert (saved["id"], saved["run_token"]) in worker.HOST_POLICY_LAUNCHES
    result = json.loads(worker.result_path(task["id"]).read_text())
    assert result["blocker"] == "task_session_isolation_uncertain"
