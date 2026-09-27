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


def test_stale_orphan_is_quarantined_without_blind_requeue(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())

    recovery.recover_orphan_tasks(now)

    assert path.exists()
    assert not (recovery.BLOCKED / path.name).exists()
    quarantined = json.loads(path.read_text(encoding="utf-8"))
    assert quarantined["watchdog_blocker"] == "orphaned_running_unknown_delivery"
    assert quarantined["attempt_state"] == "delivery_uncertain"
    assert "result_status" not in quarantined
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


def test_idle_shell_active_update_menu_is_detected_read_only(monkeypatch, capsys):
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
    reads = iter((dialog,))

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
        raise AssertionError(args)

    monkeypatch.setattr(recovery, "run_herdr", fake_run)
    recovery.recover_codex_update_dialogs()

    assert not any(call[:2] == ["agent", "send-keys"] for call in calls)
    assert "codex_update_dialog_detected agent=quantlab-sol" in capsys.readouterr().out


def test_late_result_after_quarantine_terminalizes_on_next_cycle(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())

    recovery.recover_orphan_tasks(now)
    sidecars_before = list(recovery.RESULTS.glob("task-1.watchdog-recovery-*.json"))
    assert len(sidecars_before) == 1
    assert path.exists()

    write_task(
        recovery.RESULTS / "task-1.json",
        {
            "task_id": "task-1",
            "run_token": "token-1",
            "status": "completed",
            "blocker": None,
        },
    )
    recovery.recover_orphan_tasks(now + timedelta(seconds=60))

    assert not path.exists()
    assert (recovery.DONE / "task-1.json").exists()
    assert len(list(recovery.RESULTS.glob("task-1.watchdog-recovery-*.json"))) == 1


def test_quarantined_orphan_does_not_repeat_sidecar_evidence(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    path = recovery.RUNNING / "task-1.json"
    write_task(path, task(now))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())

    recovery.recover_orphan_tasks(now)
    recovery.recover_orphan_tasks(now + timedelta(seconds=60))

    assert path.exists()
    assert len(list(recovery.RESULTS.glob("task-1.watchdog-recovery-*.json"))) == 1


def test_terminal_result_waits_for_task_pane_cleanup(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    path = recovery.RUNNING / "task-1.json"
    payload = {
        "id": "task-1",
        "run_token": "token-1",
        "execution_session": {
            "owned_pane": True,
            "pane_id": "owned-pane",
            "coordinator_pane_id": "coordinator-pane",
        },
    }
    write_task(path, payload)
    result = {
        "task_id": "task-1",
        "run_token": "token-1",
        "status": "completed",
        "blocker": None,
    }
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda task: False)

    recovery.terminalize_from_result(path, payload, result, 0)

    assert path.exists()
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "delivery_uncertain"
    assert saved["watchdog_cleanup_blocker"] == "task_session_cleanup_failed"
    assert not (recovery.DONE / path.name).exists()

    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda task: True)
    recovery.terminalize_from_result(path, saved, result, 0)
    assert not path.exists()
    assert (recovery.DONE / path.name).exists()


def test_non_object_result_does_not_abort_recovery_of_later_task(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    now = datetime(2026, 9, 27, 7, 0, tzinfo=timezone.utc)
    first = recovery.RUNNING / "task-a.json"
    second = recovery.RUNNING / "task-b.json"
    write_task(first, task(now, task_id="task-a"))
    write_task(second, task(now, task_id="task-b"))
    monkeypatch.setattr(recovery, "active_worker_tasks", lambda: set())

    (recovery.RESULTS / "task-a.json").write_text("[]\n", encoding="utf-8")
    write_task(
        recovery.RESULTS / "task-b.json",
        {
            "task_id": "task-b",
            "run_token": "token-1",
            "status": "completed",
            "blocker": None,
        },
    )

    recovery.recover_orphan_tasks(now)

    assert first.exists()
    first_saved = json.loads(first.read_text(encoding="utf-8"))
    assert first_saved["attempt_state"] == "delivery_uncertain"
    assert "invalid_shape" in first_saved["last_error"]
    assert not second.exists()
    assert (recovery.DONE / "task-b.json").exists()
