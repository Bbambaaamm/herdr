import importlib.util
import json
import os
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from herdr import autonomy_gate, recovery_unknown

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "agent-stack" / "bin"
sys.path.insert(0, str(BIN))
loader = SourceFileLoader("agent_task_dispatcher", str(BIN / "agent-task-dispatcher"))
spec = importlib.util.spec_from_loader(loader.name, loader)
dispatcher = importlib.util.module_from_spec(spec)
loader.exec_module(dispatcher)


def test_launch_stamps_fresh_dispatch_claim_before_running(tmp_path, monkeypatch):
    dispatcher.ROOT = tmp_path
    dispatcher.PENDING = tmp_path / "pending"
    dispatcher.RUNNING = tmp_path / "running"
    dispatcher.LOG = tmp_path / "dispatch.log"
    dispatcher.WORKER = Path("/fake/agent-task-worker")
    for path in (dispatcher.PENDING, dispatcher.RUNNING, tmp_path / "logs"):
        path.mkdir(parents=True, exist_ok=True)

    pending = dispatcher.PENDING / "task-1.json"
    pending.write_text(
        json.dumps({
            "id": "task-1",
            "attempt_started_at": "2026-09-26T00:00:00+00:00",
            "priority": 1,
        }),
        encoding="utf-8",
    )

    active = {"value": False}

    def worker_running():
        return active["value"]

    class FakeProcess:
        pid = os.getpid()
        returncode = None
        def poll(self):
            return None

    def fake_popen(*args, **kwargs):
        active["value"] = True
        running = dispatcher.RUNNING / "task-1.json"
        task = json.loads(running.read_text())
        task["dispatch_admission"] = {"nonce": task["dispatch_admission_nonce"],
            "pid": os.getpid(), "start_ticks": dispatcher.process_start_ticks(os.getpid()),
            "parent_pid": os.getpid()}
        running.write_text(json.dumps(task))
        return FakeProcess()

    monkeypatch.setattr(dispatcher, "worker_running", worker_running)
    monkeypatch.setattr(dispatcher.subprocess, "Popen", fake_popen)

    assert dispatcher.launch(pending) == 0

    running = dispatcher.RUNNING / "task-1.json"
    saved = json.loads(running.read_text(encoding="utf-8"))
    assert saved["dispatch_claimed_at"]
    assert saved["dispatch_claimed_at"] > saved["attempt_started_at"]


@pytest.fixture
def capacity_dispatch(tmp_path, monkeypatch):
    for name in ("pending", "running", "blocked", "logs", "results"):
        (tmp_path / name).mkdir()
    for key, value in {"ROOT": tmp_path, "PENDING": tmp_path / "pending",
            "RUNNING": tmp_path / "running", "LOG": tmp_path / "dispatch.log"}.items():
        monkeypatch.setattr(dispatcher, key, value)
    monkeypatch.setattr(recovery_unknown, "DECISIONS", tmp_path / "decisions")
    monkeypatch.setattr(dispatcher, "worker_running", lambda: False)
    capacity = SimpleNamespace(f_frsize=1, f_bavail=10737418240)
    monkeypatch.setattr(autonomy_gate.os, "statvfs", lambda _: capacity, raising=False)
    host = Mock(side_effect=AssertionError("withheld task must not select a host launch"))
    spawn = Mock(side_effect=AssertionError("withheld task must not spawn a worker"))
    monkeypatch.setattr(dispatcher, "host_entrypoint_command", host)
    monkeypatch.setattr(dispatcher.subprocess, "Popen", spawn)
    task = {"id": "synthetic-capacity", "repo": "Bbambaaamm/herdr", "consumer": "herdr",
        "run_token": "original-run", "attempts": 6, "attempt_id": 6, "fencing_token": 7,
        "ownership_epoch": {"version": 1}, "max_model_calls": 40, "max_cost_microusd": 10000000,
        "github_admission": {"approval_id": 42}, "not_before": "2000-01-01T00:00:00+00:00"}
    pending = tmp_path / "pending/synthetic-capacity.json"
    pending.write_text(json.dumps(task, indent=2) + "\n")
    history = tmp_path / "consumed-history.json"
    history.write_text(json.dumps({"used_approvals": {"42": task["id"]}}))
    ledger = tmp_path / "held-ledger.jsonl"
    ledger.write_bytes(b'{"operation":"original","state":"inflight"}\n')
    return SimpleNamespace(root=tmp_path, pending=pending, capacity=capacity, host=host, spawn=spawn,
        retained={p: p.read_bytes() for p in (pending, history, ledger)})


@pytest.mark.parametrize("available,selected", [(10737418239, False), (10737418240, True), (10737418241, True), (None, False)])
def test_due_capacity_boundary_preserves_exact_pending_identity_and_history(capacity_dispatch, available, selected):
    f = capacity_dispatch;f.capacity.f_bavail = available
    assert dispatcher.due_tasks() == ([f.pending] if selected else [])
    assert {p: p.read_bytes() for p in f.retained} == f.retained
    assert not list((f.root / "running").iterdir())
    f.host.assert_not_called();f.spawn.assert_not_called()


@pytest.mark.parametrize("available", [10737418239, None])
def test_direct_claim_withholds_before_any_task_mutation_or_spawn(capacity_dispatch, available):
    f = capacity_dispatch;f.capacity.f_bavail = available
    assert dispatcher.launch(f.pending) == 0
    assert {p: p.read_bytes() for p in f.retained} == f.retained
    assert not list((f.root / "running").iterdir())
    assert not list((f.root / "blocked").iterdir())
    f.host.assert_not_called();f.spawn.assert_not_called()


def test_capacity_drop_after_selection_is_rechecked_under_original_epoch(capacity_dispatch):
    f = capacity_dispatch
    assert dispatcher.due_tasks() == [f.pending]
    f.capacity.f_bavail = 10737418239
    assert dispatcher.launch(f.pending) == 0
    assert {p: p.read_bytes() for p in f.retained} == f.retained
    assert not list((f.root / "running").iterdir())
    f.host.assert_not_called();f.spawn.assert_not_called()


def test_uninspectable_capacity_due_and_direct_claim_fail_closed(capacity_dispatch, monkeypatch):
    f = capacity_dispatch
    def denied(_):raise PermissionError("synthetic filesystem unavailable")
    monkeypatch.setattr(autonomy_gate.os, "statvfs", denied)
    assert dispatcher.due_tasks() == []
    assert dispatcher.launch(f.pending) == 0
    assert {p: p.read_bytes() for p in f.retained} == f.retained
    f.host.assert_not_called();f.spawn.assert_not_called()


def test_unrelated_dispatch_and_either_herdr_identity_keep_their_scope(capacity_dispatch):
    f = capacity_dispatch;f.capacity.f_bavail = 0
    task = json.loads(f.pending.read_text())
    for repo, consumer, eligible in [("other/repo", "other", True),
            ("Bbambaaamm/herdr", "other", False), ("other/repo", "herdr", False)]:
        task.update(repo=repo, consumer=consumer);f.pending.write_text(json.dumps(task))
        assert dispatcher.due_tasks() == ([f.pending] if eligible else [])
    f.host.assert_not_called();f.spawn.assert_not_called()


def test_terminal_unknown_hold_precedes_capacity_and_keeps_all_retained_bytes(capacity_dispatch, monkeypatch):
    f = capacity_dispatch
    task = json.loads(f.pending.read_text());task.update(attempt_state="terminal_unknown", automatic_retry_allowed=False)
    f.pending.write_text(json.dumps(task));f.retained[f.pending] = f.pending.read_bytes()
    observe = Mock(side_effect=AssertionError("UNKNOWN cannot be reclassified as an eligible retry"))
    monkeypatch.setattr(dispatcher, "disk_headroom_blocker", observe)
    assert dispatcher.due_tasks() == []
    assert dispatcher.launch(f.pending) == 1
    assert {p: p.read_bytes() for p in f.retained} == f.retained
    observe.assert_not_called();f.host.assert_not_called();f.spawn.assert_not_called()


@pytest.mark.parametrize("available", [10737418239, None])
def test_capacity_drop_during_host_resolution_is_rechecked_before_first_mutation(capacity_dispatch, available):
    f = capacity_dispatch
    assert dispatcher.due_tasks() == [f.pending]
    def resolve(*args, **kwargs):
        f.capacity.f_bavail = available
        return ["/finite/synthetic/worker"]
    f.host.side_effect = resolve
    assert dispatcher.launch(f.pending) == 0
    f.host.assert_called_once()
    assert {p: p.read_bytes() for p in f.retained} == f.retained
    assert list((f.root / "pending").iterdir()) == [f.pending]
    assert not list((f.root / "running").iterdir())
    assert not list((f.root / "blocked").iterdir())
    f.spawn.assert_not_called()


@pytest.mark.parametrize("identity", ["ghp_abcdefgh", "github_pat_abcdefgh", "sk-abcdefgh", "line\ncredential", {"secret": "do-not-log"}])
def test_withheld_dispatch_does_not_publish_unsafe_task_identity(capacity_dispatch, identity):
    f = capacity_dispatch;f.capacity.f_bavail = 0
    task = json.loads(f.pending.read_text());task["id"] = identity
    f.pending.write_text(json.dumps(task));f.retained[f.pending] = f.pending.read_bytes()
    assert dispatcher.launch(f.pending) == 0
    message = (f.root / "dispatch.log").read_text()
    assert message.endswith(" withhold Herdr dispatch: autonomy_disk_headroom_insufficient\n")
    assert str(identity) not in message
    assert {p: p.read_bytes() for p in f.retained} == f.retained
    assert not list((f.root / "running").iterdir())
    f.host.assert_not_called();f.spawn.assert_not_called()
