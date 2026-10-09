import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

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
        returncode = None
        def poll(self):
            return None

    def fake_popen(*args, **kwargs):
        active["value"] = True
        return FakeProcess()

    monkeypatch.setattr(dispatcher, "worker_running", worker_running)
    monkeypatch.setattr(dispatcher.subprocess, "Popen", fake_popen)

    assert dispatcher.launch(pending) == 0

    running = dispatcher.RUNNING / "task-1.json"
    saved = json.loads(running.read_text(encoding="utf-8"))
    assert saved["dispatch_claimed_at"]
    assert saved["dispatch_claimed_at"] > saved["attempt_started_at"]


def test_due_tasks_skips_herdr_on_low_disk_without_mutating_pending(tmp_path, monkeypatch):
    dispatcher.ROOT = tmp_path
    dispatcher.PENDING = tmp_path / "pending"
    dispatcher.LOG = tmp_path / "dispatch.log"
    dispatcher.PENDING.mkdir(parents=True)
    herdr = dispatcher.PENDING / "herdr.json"
    other = dispatcher.PENDING / "other.json"
    herdr_payload = {"id": "herdr-53", "consumer": "herdr",
                     "repo": "Bbambaaamm/herdr", "priority": 1,
                     "run_token": "original-run", "attempts": 3}
    herdr.write_text(json.dumps(herdr_payload))
    other.write_text(json.dumps({"id": "majak", "consumer": "majak",
                                 "repo": "Bbambaaamm/dotacni-majak", "priority": 60}))
    monkeypatch.setattr(dispatcher, "disk_headroom_blocker",
                        lambda repo, consumer: "autonomy_disk_headroom_insufficient"
                        if repo == "Bbambaaamm/herdr" else None)
    assert dispatcher.due_tasks() == [other]
    assert json.loads(herdr.read_text()) == herdr_payload
    monkeypatch.setattr(dispatcher, "disk_headroom_blocker", lambda *_: None)
    assert dispatcher.due_tasks() == [herdr, other]
    assert json.loads(herdr.read_text()) == herdr_payload


def test_direct_launch_rechecks_disk_before_claiming_task(tmp_path, monkeypatch):
    dispatcher.ROOT = tmp_path
    dispatcher.PENDING = tmp_path / "pending"
    dispatcher.RUNNING = tmp_path / "running"
    dispatcher.LOG = tmp_path / "dispatch.log"
    for path in (dispatcher.PENDING, dispatcher.RUNNING, tmp_path / "logs"):
        path.mkdir(parents=True, exist_ok=True)
    task = dispatcher.PENDING / "root-task.json"
    original = {"id": "root-task", "consumer": "herdr",
                "repo": "Bbambaaamm/herdr", "run_token": "original-token"}
    task.write_text(json.dumps(original))

    monkeypatch.setattr(dispatcher, "worker_running", lambda: False)
    monkeypatch.setattr(dispatcher, "disk_headroom_blocker",
                        lambda repo, consumer: "autonomy_disk_headroom_insufficient")
    def no_process(*args, **kwargs):
        raise AssertionError("worker must not be started under low headroom")
    monkeypatch.setattr(dispatcher.subprocess, "Popen", no_process)
    assert dispatcher.launch(task) == 0
    assert task.exists()
    assert not (dispatcher.RUNNING / task.name).exists()
    assert json.loads(task.read_text()) == original
    assert "autonomy_disk_headroom_insufficient" in dispatcher.LOG.read_text()
