import importlib.util
import json
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "agent-stack" / "bin"
loader = SourceFileLoader("agent_stack_recovery", str(BIN / "agent-stack-recovery"))
spec = importlib.util.spec_from_loader(loader.name, loader)
recovery = importlib.util.module_from_spec(spec)
loader.exec_module(recovery)


def configure_paths(tmp_path):
    recovery.ROOT = tmp_path
    recovery.RUNNING = tmp_path / "running"
    recovery.DONE = tmp_path / "done"
    recovery.BLOCKED = tmp_path / "blocked"
    recovery.FAILED = tmp_path / "failed"
    recovery.RESULTS = tmp_path / "results"
    for path in (
        recovery.RUNNING,
        recovery.DONE,
        recovery.BLOCKED,
        recovery.FAILED,
        recovery.RESULTS,
    ):
        path.mkdir(parents=True, exist_ok=True)


def task(now, *, task_id="task-1", timeout=1800):
    return {
        "id": task_id,
        "run_token": "token-1",
        "timeout_seconds": timeout,
        "attempt_started_at": (now - timedelta(seconds=timeout + 600)).isoformat(),
        "issue": 9,
        "repo": "Bbambaaamm/herdr",
    }


def write_task(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_stale_orphan_blocks_without_blind_requeue(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())

    recovery.recover_orphan_tasks(now)

    assert not path.exists()
    blocked = json.loads((recovery.BLOCKED / path.name).read_text(encoding="utf-8"))
    assert blocked["watchdog_blocker"] == "orphaned_running_unknown_delivery"
    assert blocked["attempt_state"] == "blocked"
    result = json.loads((recovery.RESULTS / "task-1.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert result["blocker"] == "orphaned_running_unknown_delivery"


def test_live_worker_prevents_orphan_recovery(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: {path.resolve()})

    recovery.recover_orphan_tasks(now)

    assert path.exists()
    assert not (recovery.BLOCKED / path.name).exists()


def test_matching_completed_result_terminalizes_done(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    payload = task(now)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, payload)
    write_task(
        recovery.RESULTS / "task-1.json",
        {
            "task_id": "task-1",
            "run_token": "token-1",
            "status": "completed",
            "blocker": None,
        },
    )
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())

    recovery.recover_orphan_tasks(now)

    done = json.loads((recovery.DONE / path.name).read_text(encoding="utf-8"))
    assert done["attempt_state"] == "done"
    assert done["result_status"] == "completed"
    assert not (recovery.BLOCKED / path.name).exists()


def test_mismatched_result_is_not_overwritten(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    canonical = recovery.RESULTS / "task-1.json"
    original = {
        "task_id": "task-1",
        "run_token": "older-token",
        "status": "completed",
    }
    write_task(canonical, original)
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())

    recovery.recover_orphan_tasks(now)

    assert json.loads(canonical.read_text(encoding="utf-8")) == original
    sidecars = list(recovery.RESULTS.glob("task-1.watchdog-recovery-*.json"))
    assert len(sidecars) == 1
    assert json.loads(sidecars[0].read_text(encoding="utf-8"))["status"] == "blocked"


def test_codex_update_dialog_detection_only_matches_active_menu():
    dialog = """
Update available · 0.156.1 → 0.157.1
› 1. Update now
  2. Skip
  3. Skip until next version
  enter continue · esc skip
"""
    ready = dialog + """
╭────────────────────────╮
│ >_ OpenAI Codex        │
╰────────────────────────╯
› Ask Codex to do anything
"""
    assert recovery.is_codex_update_dialog(dialog) is True
    assert recovery.is_codex_update_dialog(ready) is False


def test_plain_update_banner_is_not_treated_as_blocking_dialog():
    banner = """
✨ Update available! 0.156.1 -> 0.157.1
Run npm install -g @openai/codex to update.
› Ask Codex to do anything
"""
    assert recovery.is_codex_update_dialog(banner) is False
