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
