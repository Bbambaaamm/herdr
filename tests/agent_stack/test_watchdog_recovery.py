import importlib.util
import json
import os
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
    raw = str(payload.get("attempt_started_at") or "")
    if raw:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        os.utime(path, (stamp, stamp))


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
    assert not (recovery.RESULTS / "task-1.json").exists()
    sidecars = list(recovery.RESULTS.glob("task-1.watchdog-recovery-*.json"))
    assert len(sidecars) == 1
    result = json.loads(sidecars[0].read_text(encoding="utf-8"))
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


def test_recent_dispatch_claim_beats_old_attempt_timestamp(tmp_path):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    payload = task(now)
    payload["dispatch_claimed_at"] = (now - timedelta(seconds=10)).isoformat()
    path = recovery.RUNNING / "task-1.json"
    write_task(path, payload)
    old = (now - timedelta(hours=2)).timestamp()
    os.utime(path, (old, old))

    assert recovery.parse_started(payload, path) == now - timedelta(seconds=10)


def test_worker_appearing_on_second_check_prevents_orphan_block(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    calls = iter((set(), {path.resolve()}))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: next(calls))

    recovery.recover_orphan_tasks(now)

    assert path.exists()
    assert not (recovery.BLOCKED / path.name).exists()


def test_result_appearing_on_second_check_terminalizes_instead_of_block(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())
    completed = {
        "task_id": "task-1",
        "run_token": "token-1",
        "status": "completed",
        "blocker": None,
    }
    calls = iter(((None, "missing"), (completed, "matched")))
    monkeypatch.setattr(recovery, "matching_result", lambda task: next(calls))

    recovery.recover_orphan_tasks(now)

    assert (recovery.DONE / path.name).exists()
    assert not (recovery.BLOCKED / path.name).exists()


def test_historical_dialog_followed_by_work_is_not_active():
    text = """
› 1. Update now
  2. Skip
  3. Skip until next version
  enter continue · esc skip
• Ran git status
• Working (5s)
"""
    assert recovery.is_codex_update_dialog(text) is False


def test_working_codex_with_quoted_menu_never_receives_escape(monkeypatch):
    quoted = """
User asked about:
› 1. Update now
  2. Skip
  3. Skip until next version
  enter continue · esc skip
"""
    calls = []

    def fake_run(args, timeout=15.0):
        calls.append(list(args))
        if args == ["agent", "list"]:
            payload = {
                "result": {
                    "agents": [{
                        "agent": "codex",
                        "name": "quantlab-sol",
                        "agent_status": "working",
                        "interactive_ready": True,
                    }]
                }
            }
            return recovery.subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        if args[:2] == ["agent", "read"]:
            return recovery.subprocess.CompletedProcess(args, 0, quoted, "")
        return recovery.subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(recovery, "run_herdr", fake_run)
    recovery.recover_codex_update_dialogs()

    assert not any(call[:2] == ["agent", "send-keys"] for call in calls)


def test_quoted_update_menu_with_trailing_text_is_not_active():
    quoted = """
Update available · 0.156.1 → 0.157.1
› 1. Update now
  2. Skip
  3. Skip until next version
  enter continue · esc skip
This menu was quoted in a task and is not interactive.
"""
    assert recovery.is_codex_update_dialog(quoted) is False


def test_idle_codex_ordinary_tui_never_receives_escape(monkeypatch):
    dialog = """
Update available · 0.156.1 → 0.157.1
› 1. Update now
  2. Skip
  3. Skip until next version
  enter continue · esc skip
"""
    calls = []

    def fake_run(args, timeout=15.0):
        calls.append(list(args))
        if args == ["agent", "list"]:
            payload = {
                "result": {
                    "agents": [{
                        "agent": "codex",
                        "name": "quantlab-sol",
                        "agent_status": "idle",
                        "interactive_ready": True,
                        "terminal_title_stripped": "quantlab",
                    }]
                }
            }
            return recovery.subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        if args[:2] == ["agent", "read"]:
            return recovery.subprocess.CompletedProcess(args, 0, dialog, "")
        return recovery.subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(recovery, "run_herdr", fake_run)
    recovery.recover_codex_update_dialogs()

    assert not any(call[:2] == ["agent", "send-keys"] for call in calls)


def test_idle_shell_active_update_menu_is_skipped(monkeypatch):
    dialog = """
Update available · 0.156.1 → 0.157.1
Release notes: https://github.com/openai/codex/releases/latest
› 1. Update now (runs `npm install -g @openai/codex`)
  2. Skip
  3. Skip until next version
  enter continue · esc skip
"""
    ready = """
╭────────────────────────╮
│ >_ OpenAI Codex        │
╰────────────────────────╯
› Ask Codex to do anything
"""
    calls = []
    reads = iter((dialog, ready))

    def fake_run(args, timeout=15.0):
        calls.append(list(args))
        if args == ["agent", "list"]:
            payload = {
                "result": {
                    "agents": [{
                        "agent": "codex",
                        "name": "quantlab-sol",
                        "agent_status": "idle",
                        "interactive_ready": True,
                        "terminal_title_stripped": "agentops@quantlab-staging-01: ~/workspaces/quantlab",
                    }]
                }
            }
            return recovery.subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        if args[:2] == ["agent", "read"]:
            return recovery.subprocess.CompletedProcess(args, 0, next(reads), "")
        if args[:2] == ["agent", "send-keys"]:
            return recovery.subprocess.CompletedProcess(args, 0, '{"result":{"type":"ok"}}', "")
        raise AssertionError(args)

    monkeypatch.setattr(recovery, "run_herdr", fake_run)
    monkeypatch.setattr(recovery.time, "sleep", lambda _: None)
    recovery.recover_codex_update_dialogs()

    assert ["agent", "send-keys", "quantlab-sol", "esc"] in calls
