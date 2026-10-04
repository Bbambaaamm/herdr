import hashlib
import importlib.util
import json
import stat
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[2] / "agent-stack/bin"
sys.path.insert(0, str(BIN))

from herdr.scheduler import AuditLog, ChildProposal, DynamicChildScheduler
import agent_durable_children
from agent_durable_children import (all_children_terminal, attempt_directory,
                                    ensure_attempt_directory, ledger_required, mark_ledger_required,
                                    parent_attempt_guard)


def load(name, file):
    loader = SourceFileLoader(name, str(BIN / file))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture
def setup(tmp_path):
    worker = load("worker_child_gate", "agent-task-worker")
    recovery = load("recovery_child_gate", "agent-stack-recovery")
    for module in (worker, recovery):
        module.ROOT = tmp_path
        for name in ("PENDING", "RUNNING", "DONE", "BLOCKED", "FAILED", "RESULTS", "LOGS"):
            directory = tmp_path / name.lower()
            directory.mkdir(exist_ok=True)
            setattr(module, name, directory)
    task = {"id": "parent", "run_token": "run-1", "idempotency_key": "key-1",
            "attempts": 0, "max_attempts": 4, "attempt_state": "accepted",
            "execution_session": {"owned_pane": True, "pane_id": "pane-1"}}
    path = worker.RUNNING / "parent.json"
    path.write_text(json.dumps(task))
    directory = tmp_path / "durable-children" / hashlib.sha256(b"parent:run-1").hexdigest()
    scheduler = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="run-1", idempotency_key="key-1",
        agent_name="agent", pane_id="pane-1", marker="marker", repo="repo",
        issue="82", role="writer", tools=("read_file",), permissions=(),
        policy_profile="default")
    assert (directory / "scheduler.jsonl").is_file()
    mark_ledger_required(directory)
    child = scheduler.delegate_child("parent", "run-1", "key",
        ChildProposal("writer", ("read_file",), "reader", ("read_file",),
                      child_task="inspect"))
    lease = scheduler.dispatch(task_ids={child.id})[0]
    return worker, recovery, task, path, scheduler, child, lease


def test_guard_directory_without_scheduler_allows_terminalization(tmp_path):
    directory = attempt_directory(tmp_path, "parent", "run-1")
    assert all_children_terminal(tmp_path, "parent", "run-1")
    with parent_attempt_guard(tmp_path, "parent", "run-1") as terminal:
        assert terminal
        assert directory.is_dir()
        assert not ledger_required(directory)
        assert not (directory / "scheduler.jsonl").exists()
    assert not all_children_terminal(tmp_path, "parent", "run-1")


def test_guard_persists_private_attempt_directories_and_lock(tmp_path, monkeypatch):
    directory = attempt_directory(tmp_path, "parent", "run-1")
    container = directory.parent
    synced = []
    original = agent_durable_children._fsync_directory

    def record_fsync(path):
        synced.append(path)
        original(path)

    monkeypatch.setattr(agent_durable_children, "_fsync_directory", record_fsync)
    with parent_attempt_guard(tmp_path, "parent", "run-1"):
        assert (directory / "bridge.lock").is_file()
        assert synced == [tmp_path, container, directory, directory]
    for path in (container, directory):
        mode = path.lstat().st_mode
        assert stat.S_ISDIR(mode)
        assert stat.S_IMODE(mode) == 0o700


@pytest.mark.parametrize("symlink_at", ["root", "container", "attempt"])
def test_guard_rejects_symlink_directories(tmp_path, symlink_at):
    root = tmp_path / "state"
    root.mkdir()
    directory = attempt_directory(root, "parent", "run-1")
    outside = tmp_path / "outside"
    outside.mkdir()
    if symlink_at == "root":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    elif symlink_at == "container":
        directory.parent.symlink_to(outside, target_is_directory=True)
    else:
        directory.parent.mkdir()
        directory.symlink_to(outside, target_is_directory=True)
    with pytest.raises(NotADirectoryError):
        with parent_attempt_guard(root, "parent", "run-1"):
            pass
    assert not (outside / "bridge.lock").exists()


def test_ensure_attempt_directory_requires_existing_root(tmp_path):
    with pytest.raises(FileNotFoundError):
        ensure_attempt_directory(tmp_path / "missing", "parent", "run-1")


def test_required_ledger_missing_fails_closed_with_and_without_guard(tmp_path):
    directory = attempt_directory(tmp_path, "parent", "run-1")
    directory.mkdir(parents=True)
    ledger = directory / "scheduler.jsonl"
    scheduler = DynamicChildScheduler(audit_log=AuditLog(ledger))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="run-1", idempotency_key="key-1",
        agent_name="agent", pane_id="pane-1", marker="marker", repo="repo",
        issue="82", role="writer", tools=("read_file",), permissions=(),
        policy_profile="default")
    mark_ledger_required(directory)
    assert ledger_required(directory)
    assert (directory / "scheduler.required").stat().st_mode & 0o777 == 0o600
    with parent_attempt_guard(tmp_path, "parent", "run-1") as terminal:
        assert terminal
    ledger.unlink()
    assert not all_children_terminal(tmp_path, "parent", "run-1")
    with parent_attempt_guard(tmp_path, "parent", "run-1") as terminal:
        assert not terminal


def test_existing_ledger_without_required_sentinel_fails_closed(tmp_path):
    directory = attempt_directory(tmp_path, "parent", "run-1")
    directory.mkdir(parents=True)
    scheduler = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent", run_token="run-1", idempotency_key="key-1",
        agent_name="agent", pane_id="pane-1", marker="marker", repo="repo",
        issue="82", role="writer", tools=("read_file",), permissions=(),
        policy_profile="default")
    mark_ledger_required(directory)
    assert all_children_terminal(tmp_path, "parent", "run-1")
    (directory / "scheduler.required").unlink()
    assert not all_children_terminal(tmp_path, "parent", "run-1")
    with parent_attempt_guard(tmp_path, "parent", "run-1") as terminal:
        assert not terminal


def publish(scheduler, child, lease, status="completed"):
    rec = scheduler._tasks[child.id]
    evidence = [{"artifact": "exact"}]
    digest = hashlib.sha256(json.dumps(evidence, sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()
    assert scheduler.publish_child_result(child.id, rec.run_token, lease.agent_id,
                                          lease.fencing_token, rec.idempotency_key,
                                          digest, evidence, status=status)


def child_result(scheduler, child, **changes):
    rec = scheduler._tasks[child.id]
    evidence = [{"artifact": "late"}]
    payload = {"task_id": child.id, "run_token": rec.run_token,
               "fencing_token": rec.fencing_token,
               "idempotency_key": rec.idempotency_key, "status": "completed",
               "evidence": evidence,
               "artifact_sha256": hashlib.sha256(json.dumps(evidence, sort_keys=True,
                   ensure_ascii=False, allow_nan=False).encode()).hexdigest()}
    payload.update(changes)
    result_dir = scheduler.audit_log._path.parent / "results"
    result_dir.mkdir(exist_ok=True)
    (result_dir / f"{child.id}.result.json").write_text(json.dumps(payload))


def test_recovery_publishes_late_child_result_without_reprompt(setup, monkeypatch):
    worker, recovery, task, path, scheduler, child, _ = setup
    parent_result = {"task_id": "parent", "run_token": "run-1", "status": "completed"}
    (worker.RESULTS / "parent.json").write_text(json.dumps(parent_result))
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda task: True)
    recovery.terminalize_from_result(path, task, parent_result, 0)
    assert (recovery.BLOCKED / path.name).exists()
    child_result(scheduler, child)
    monkeypatch.setattr(recovery, "ensure_live_task_bridge", lambda *args: True)
    recovery.reconcile_watchdog_blocked_tasks()
    assert (recovery.DONE / path.name).exists()
    assert all_children_terminal(worker.ROOT, "parent", "run-1")
    events = scheduler.audit_log.replay()
    assert sum(event.get("event") == "claim" and event.get("task_id") == child.id
               for event in events) == 1
    assert sum(event.get("event") == "child_result" and event.get("task_id") == child.id
               for event in events) == 1


def test_bound_child_result_waits_for_durable_cleanup(setup, monkeypatch):
    worker, recovery, task, path, scheduler, child, lease = setup
    rec = scheduler._tasks[child.id]
    assert scheduler.bind_execution_session(child.id, rec.run_token, lease.agent_id,
                                            "child-pane", "child-marker")
    publish(scheduler, child, lease)
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")
    replay = DynamicChildScheduler(audit_log=AuditLog(scheduler.audit_log._path))
    replay.replay()
    assert not replay._tasks[child.id].cleanup_complete
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")
    assert scheduler.mark_child_cleanup_complete(child.id)
    assert all_children_terminal(worker.ROOT, "parent", "run-1")
    replay = DynamicChildScheduler(audit_log=AuditLog(scheduler.audit_log._path))
    replay.replay()
    assert replay._tasks[child.id].cleanup_complete
    ledger = scheduler.audit_log._path
    lines = ledger.read_text().splitlines()
    ledger.write_text("\n".join(line for line in lines if
        json.loads(line).get("event") != "child_cleanup_complete") + "\n")
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")
    ledger.write_text("\n".join(lines[:-1] + [json.dumps({
        **json.loads(lines[-1]), "marker": "wrong-marker"})]) + "\n")
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")


def test_pre_delivery_blocked_child_requires_proven_cleanup(setup):
    worker, _, _, _, scheduler, child, lease = setup
    rec = scheduler._tasks[child.id]
    assert scheduler.bind_pre_delivery_pane(child.id, rec.run_token, lease.agent_id,
                                            "child-pane", "child-marker")
    assert scheduler.fail_child_pre_delivery(child.id, rec.run_token, lease.agent_id,
                                             lease.fencing_token, rec.idempotency_key,
                                             "sandbox denied", cleanup_complete=False)
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")
    replay = DynamicChildScheduler(audit_log=AuditLog(scheduler.audit_log._path))
    replay.replay()
    assert replay._tasks[child.id].pre_delivery_failure == "sandbox denied"
    assert replay._tasks[child.id].lease is None
    assert scheduler.mark_child_cleanup_complete(child.id)
    assert all_children_terminal(worker.ROOT, "parent", "run-1")


def test_late_bound_child_cleanup_retries_before_parent_terminal(setup, monkeypatch):
    worker, recovery, task, path, scheduler, child, lease = setup
    rec = scheduler._tasks[child.id]
    assert scheduler.bind_execution_session(child.id, rec.run_token, lease.agent_id,
                                            "child-pane", "child-marker")
    child_result(scheduler, child)
    parent_result = {"task_id": "parent", "run_token": "run-1", "status": "completed"}
    (worker.RESULTS / "parent.json").write_text(json.dumps(parent_result))
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda task: True)
    monkeypatch.setattr(recovery, "ensure_live_task_bridge", lambda *args: True)
    calls = []
    class Runtime:
        def __init__(self, scheduler, runner, **kwargs):
            self.scheduler = scheduler
        def cleanup_bound_child(self, task_id):
            calls.append(task_id)
            if len(calls) == 1:
                raise RuntimeError("identity mismatch")
    monkeypatch.setattr(agent_durable_children, "HerdrChildRuntime", Runtime)
    recovery.terminalize_from_result(path, task, parent_result, 0)
    assert (recovery.BLOCKED / path.name).exists()
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")
    recovery.reconcile_watchdog_blocked_tasks()
    assert (recovery.BLOCKED / path.name).exists()
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")
    recovery.reconcile_watchdog_blocked_tasks()
    assert (recovery.DONE / path.name).exists()
    assert calls == [child.id, child.id]
    assert all_children_terminal(worker.ROOT, "parent", "run-1")


@pytest.mark.parametrize("changes", [
    {"run_token": "wrong"}, {"fencing_token": -1},
    {"idempotency_key": "wrong"}, {"artifact_sha256": "wrong"},
])
def test_recovery_quarantines_mismatched_late_child_result(setup, monkeypatch, changes):
    worker, recovery, task, path, scheduler, child, _ = setup
    parent_result = {"task_id": "parent", "run_token": "run-1", "status": "completed"}
    (worker.RESULTS / "parent.json").write_text(json.dumps(parent_result))
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda task: True)
    recovery.terminalize_from_result(path, task, parent_result, 0)
    child_result(scheduler, child, **changes)
    monkeypatch.setattr(recovery, "ensure_live_task_bridge", lambda *args: True)
    recovery.reconcile_watchdog_blocked_tasks()
    assert (recovery.BLOCKED / path.name).exists()
    assert not all_children_terminal(worker.ROOT, "parent", "run-1")
    assert not any(event.get("event") == "child_result"
                   for event in scheduler.audit_log.replay())


@pytest.mark.parametrize("status,destination", [("completed", "DONE"),
                                              ("blocked", "BLOCKED"),
                                              ("failed", "PENDING")])
def test_parent_finish_waits_for_exact_child_result(setup, monkeypatch, status, destination):
    worker, _, task, path, scheduler, child, lease = setup
    monkeypatch.setattr(worker, "cleanup_task_session", lambda task: True)
    (worker.RESULTS / "parent.json").write_text(json.dumps({
        "task_id": "parent", "run_token": "run-1", "status": status}))
    worker.finish(path, task, "done")
    held = worker.BLOCKED / path.name
    saved = json.loads(held.read_text())
    assert saved["run_token"] == "run-1" and saved["attempts"] == 0
    assert saved["watchdog_blocker"] == "active_durable_children"
    assert saved["attempt_state"] == "result_ready"
    assert saved["execution_session"]["pane_id"] == "pane-1"
    assert not list(worker.PENDING.iterdir())
    publish(scheduler, child, lease)
    worker.finish(held, saved, "reconciled")
    final = json.loads((getattr(worker, destination) / "parent.json").read_text())
    assert "watchdog_blocker" not in final
    assert "recovery_action" not in final
    assert "delivery_reconcile_pending" not in final


def test_provider_retry_keeps_same_attempt_with_active_child(setup):
    worker, _, task, path, _, _, _ = setup
    worker.retry(path, task, "provider unavailable")
    saved = json.loads((worker.BLOCKED / path.name).read_text())
    assert saved["attempts"] == 0 and saved["run_token"] == "run-1"
    assert saved["attempt_state"] == "delivery_uncertain"
    assert not list(worker.PENDING.iterdir())


def test_recovery_rechecks_exact_parent_result_after_child_finishes(setup, monkeypatch):
    worker, recovery, task, path, scheduler, child, lease = setup
    result = {"task_id": "parent", "run_token": "run-1", "status": "completed"}
    (worker.RESULTS / "parent.json").write_text(json.dumps(result))
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda task: True)
    recovery.terminalize_from_result(path, task, result, 0)
    held = recovery.BLOCKED / path.name
    assert held.exists() and task["execution_session"].get("closed_at") is None
    monkeypatch.setattr(recovery, "ensure_live_task_bridge", lambda *args: True)
    publish(scheduler, child, lease, status="blocked")
    recovery.reconcile_watchdog_blocked_tasks()
    final = json.loads((recovery.DONE / "parent.json").read_text())
    assert "watchdog_blocker" not in final
    assert "recovery_action" not in final
    assert "delivery_reconcile_pending" not in final


def test_corrupt_child_ledger_fails_closed(setup):
    worker, _, task, path, scheduler, _, _ = setup
    scheduler.audit_log._path.write_text("{bad json\n")
    worker.retry(path, task, "provider unavailable")
    assert (worker.BLOCKED / path.name).exists()


def test_deleted_managed_ledger_blocks_worker_retry_and_recovery(setup):
    worker, recovery, task, path, scheduler, _, _ = setup
    directory = scheduler.audit_log._path.parent
    assert ledger_required(directory)
    scheduler.audit_log._path.unlink()
    worker.retry(path, task, "provider unavailable")
    held = worker.BLOCKED / path.name
    saved = json.loads(held.read_text())
    assert saved["attempts"] == 0
    assert saved["run_token"] == "run-1"
    assert saved["watchdog_blocker"] == "active_durable_children"
    result = {"task_id": "parent", "run_token": "run-1", "status": "completed"}
    recovery.terminalize_from_result(held, saved, result, 0)
    held_task = json.loads(held.read_text())
    assert held_task["watchdog_blocker"] == "active_durable_children"
    assert held_task["attempt_state"] == "result_ready"
    assert not (recovery.DONE / path.name).exists()


def parent_binding():
    return dict(task_id="parent", run_token="run-1", idempotency_key="key-1",
        agent_name="agent", pane_id="pane-1", marker="marker", repo="repo",
        issue="82", role="writer", tools=("read_file",), permissions=(), policy_profile="default")


@pytest.mark.parametrize("phase", ["pending", "ledger", "sentinel", "committed"])
def test_initial_parent_ledger_recovers_each_publication_crash(tmp_path, monkeypatch, phase):
    directory = ensure_attempt_directory(tmp_path, "parent", "run-1")
    original_atomic = agent_durable_children._atomic_control_file
    original_mark = agent_durable_children.mark_ledger_required
    def atomic(path, raw):
        original_atomic(path, raw)
        state = json.loads(raw).get("state") if path.name == agent_durable_children.INITIALIZATION else None
        if (phase == "pending" and state == "pending" or phase == "ledger" and path.name == "scheduler.jsonl"
                or phase == "committed" and state == "committed"):
            raise SystemExit("simulated process death after durable publication")
    def mark(path):
        original_mark(path)
        if phase == "sentinel":
            raise SystemExit("simulated process death after required sentinel")
    with monkeypatch.context() as patch:
        patch.setattr(agent_durable_children, "_atomic_control_file", atomic)
        patch.setattr(agent_durable_children, "mark_ledger_required", mark)
        with pytest.raises(SystemExit):
            with parent_attempt_guard(tmp_path, "parent", "run-1"):
                agent_durable_children.initialize_parent_scheduler(directory, **parent_binding())
    if phase != "committed":
        assert not all_children_terminal(tmp_path, "parent", "run-1")
    with parent_attempt_guard(tmp_path, "parent", "run-1", reconcile_results=True) as terminal:
        assert terminal
    assert ledger_required(directory)
    document = json.loads((directory / agent_durable_children.INITIALIZATION).read_text())
    assert document["state"] == "committed" and "ledger" not in document
    scheduler = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
    scheduler.replay()
    parent = scheduler._tasks["parent"]
    assert (parent.run_token, parent.idempotency_key, parent.execution_pane) == ("run-1", "key-1", "pane-1")
    assert [e["event"] for e in scheduler.audit_log.replay()] == ["submit", "claim", "execution_session_bound"]
    assert all_children_terminal(tmp_path, "parent", "run-1")


@pytest.mark.parametrize("artifact", ["scheduler.jsonl", "scheduler.required"])
def test_committed_initialization_never_recreates_lost_scheduler_artifacts(tmp_path, artifact):
    directory = ensure_attempt_directory(tmp_path, "parent", "run-1")
    with parent_attempt_guard(tmp_path, "parent", "run-1"):
        agent_durable_children.initialize_parent_scheduler(directory, **parent_binding())
    (directory / artifact).unlink()
    with parent_attempt_guard(tmp_path, "parent", "run-1", reconcile_results=True) as terminal:
        assert not terminal
    assert not (directory / artifact).exists()


@pytest.mark.parametrize("fault", ["wrong_run", "digest", "changed_ledger"])
def test_pending_initialization_conflict_remains_fail_closed(tmp_path, monkeypatch, fault):
    directory = ensure_attempt_directory(tmp_path, "parent", "run-1")
    original = agent_durable_children._atomic_control_file
    def atomic(path, raw):
        original(path, raw)
        if path.name == "scheduler.jsonl":
            raise SystemExit("crash before sentinel")
    with monkeypatch.context() as patch:
        patch.setattr(agent_durable_children, "_atomic_control_file", atomic)
        with pytest.raises(SystemExit):
            with parent_attempt_guard(tmp_path, "parent", "run-1"):
                agent_durable_children.initialize_parent_scheduler(directory, **parent_binding())
    metadata = directory / agent_durable_children.INITIALIZATION
    if fault == "changed_ledger":
        with (directory / "scheduler.jsonl").open("a") as handle:
            handle.write('{"event":"spawn_child","child_id":"foreign"}\n')
    else:
        value = json.loads(metadata.read_text())
        value["run_token" if fault == "wrong_run" else "ledger_sha256"] = "different"
        metadata.write_text(json.dumps(value))
    before = (directory / "scheduler.jsonl").read_bytes()
    assert not all_children_terminal(tmp_path, "parent", "run-1")
    with pytest.raises((ValueError, RuntimeError)):
        with parent_attempt_guard(tmp_path, "parent", "run-1"):
            pass
    assert (directory / "scheduler.jsonl").read_bytes() == before
    assert not ledger_required(directory)
