"""Synthetic low-capacity contract for the existing maintenance path (#126).

The watchdog invokes ``hermes-maintenance`` every minute, so the reserve check and
the capacity diagnostic must be exercisable without touching the real filesystem:
every test here monkeypatches the free-space observation and uses a tmp STATE.
"""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack/bin/hermes-maintenance"
GIB = 1024 ** 3
MIB = 1024 ** 2


def load_module(monkeypatch, tmp_path):
    loader = importlib.machinery.SourceFileLoader("maintenance_capacity_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    with monkeypatch.context() as isolated:
        isolated.setattr(Path, "mkdir", lambda *args, **kwargs: None)
        isolated.setattr(os, "chmod", lambda *args, **kwargs: None)
        isolated.setattr(os, "umask", lambda *args, **kwargs: None)
        loader.exec_module(module)
    module.HOME = tmp_path
    module.STATE = tmp_path / "state"
    module.BACKUPS = tmp_path / "backups"
    module.AUDITS = tmp_path / "audits"
    module.STAMPS = tmp_path / "stamps"
    module.LOG = tmp_path / "maintenance.log"
    module.BIN = tmp_path / "bin"
    for path in (module.STATE, module.BACKUPS, module.AUDITS, module.STAMPS):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(os, "chmod", lambda *args, **kwargs: None)
    return module


def set_free(module, monkeypatch, free_bytes):
    monkeypatch.setattr(module, "statvfs_free_bytes", lambda: free_bytes)


def read_log(module):
    return module.LOG.read_text(encoding="utf-8")


def required_bytes(module, peak):
    return module.CAPACITY_FLOOR_BYTES + module.CAPACITY_START_GUARD_BYTES + peak


def test_capacity_floor_is_the_existing_autonomy_floor():
    from herdr.autonomy_gate import MIN_ROOT_FREE_BYTES

    assert MIN_ROOT_FREE_BYTES == 10 * GIB


def test_observe_capacity_fails_closed_when_statvfs_unavailable(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    monkeypatch.setattr(module, "statvfs_free_bytes", lambda: None)
    decision = module.observe_capacity(0)
    assert decision["ready"] is False
    assert decision["reason"] == "capacity_unavailable"
    assert decision["missing_bytes"] == decision["required_bytes"]


def test_observe_capacity_rejects_untrustworthy_statvfs(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)

    class FloatStatvfs:
        f_frsize = 4096.0
        f_bavail = 1.0

    monkeypatch.setattr(module.os, "statvfs", lambda path: FloatStatvfs())
    assert module.statvfs_free_bytes() is None
    assert module.observe_capacity(0)["reason"] == "capacity_unavailable"


def test_observe_capacity_is_exact_at_the_boundary(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    peak = module.backup_preparation_peak()
    required = required_bytes(module, peak)
    set_free(module, monkeypatch, required - 1)
    assert module.observe_capacity(peak)["ready"] is False
    set_free(module, monkeypatch, required)
    assert module.observe_capacity(peak)["ready"] is True


def test_backup_preparation_peak_uses_newest_zip_and_reserve(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    # Name order and mtime order disagree on purpose: selection must follow mtime.
    older_name = module.BACKUPS / "hermes-backup-auto-20260101-000000.zip"
    newer_name = module.BACKUPS / "hermes-backup-auto-20260102-000000.zip"
    with open(older_name, "wb") as handle:
        handle.truncate(600 * MIB)
    with open(newer_name, "wb") as handle:
        handle.truncate(100 * MIB)
    os.utime(older_name, (2, 2))
    os.utime(newer_name, (1, 1))
    assert module.backup_preparation_peak() == (
        600 * MIB * module.BACKUP_PEAK_FACTOR + module.BACKUP_SAFETY_RESERVE_BYTES
    )


def test_backup_preparation_peak_without_archives_is_conservative(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    assert module.backup_preparation_peak() == (
        module.BACKUP_BASE_BYTES * module.BACKUP_PEAK_FACTOR + module.BACKUP_SAFETY_RESERVE_BYTES
    )
    assert module.BACKUP_BASE_BYTES >= 512 * MIB


def test_daily_backup_is_skipped_and_not_marked_when_capacity_low(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 4 * GIB)
    calls = []
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: calls.append(args) or (0, ""))
    module.daily_backup()
    assert calls == []
    assert not (module.STAMPS / "backup").exists()
    assert "capacity HOLD backup" in read_log(module)
    assert "backup OK" not in read_log(module)


def test_daily_backup_runs_and_marks_when_capacity_sufficient(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 20 * GIB)
    calls = []
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: calls.append(args) or (0, ""))
    module.daily_backup()
    assert len(calls) == 1
    assert (module.STAMPS / "backup").exists()
    assert "backup OK" in read_log(module)


def test_daily_offsite_prepare_is_skipped_when_capacity_low(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 4 * GIB)
    calls = []
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: calls.append(args) or (0, ""))
    module.daily_offsite_prepare()
    assert calls == []
    assert not (module.STAMPS / "offsite-prepare").exists()
    assert "capacity HOLD offsite-prepare" in read_log(module)


def test_gated_path_deletes_nothing_and_keeps_existing_artifacts(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 4 * GIB)
    keeper = module.BACKUPS / "hermes-backup-auto-20260101-000000.zip"
    keeper.write_bytes(b"keep-me")
    deleted = []
    monkeypatch.setattr(module.shutil, "rmtree", lambda *args, **kwargs: deleted.append(args))
    monkeypatch.setattr(module.os, "remove", lambda *args, **kwargs: deleted.append(args))
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: (0, ""))
    module.daily_backup()
    module.daily_offsite_prepare()
    assert deleted == []
    assert keeper.read_bytes() == b"keep-me"


def test_capacity_diagnostic_logs_only_on_state_change(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 4 * GIB)
    module.capacity_diagnostic()
    module.capacity_diagnostic()
    assert read_log(module).count("capacity NOT_READY") == 1
    set_free(module, monkeypatch, 20 * GIB)
    module.capacity_diagnostic()
    module.capacity_diagnostic()
    text = read_log(module)
    assert text.count("capacity NOT_READY") == 1
    assert text.count("capacity READY") == 1
    state = json.loads((module.STATE / "capacity-diagnostic.json").read_text(encoding="utf-8"))
    assert state == {"ready": True, "reason": "capacity_ready", "held": [],
                     "available_bytes": 20 * GIB,
                     "required_bytes": module.CAPACITY_FLOOR_BYTES + module.CAPACITY_START_GUARD_BYTES}


def test_hold_is_reported_once_per_step_per_episode(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 4 * GIB)
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: (0, ""))
    for _ in range(3):
        module.daily_backup()
        module.daily_offsite_prepare()
    text = read_log(module)
    assert text.count("capacity HOLD backup") == 1
    assert text.count("capacity HOLD offsite-prepare") == 1
    set_free(module, monkeypatch, 20 * GIB)
    module.capacity_diagnostic()
    set_free(module, monkeypatch, 4 * GIB)
    module.daily_backup()
    assert read_log(module).count("capacity HOLD backup") == 2


def test_audit_posture_records_the_capacity_decision(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 4 * GIB)
    monkeypatch.setattr(module, "command_report", lambda wrapper: "")
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: (127, ""))
    module.daily_audit()
    posture = next(module.AUDITS.glob("*/backup-posture.txt"))
    text = posture.read_text(encoding="utf-8")
    assert "capacity_ready=False" in text
    assert "capacity_reason=capacity_insufficient" in text
    assert f"capacity_available_bytes={4 * GIB}" in text


def test_main_runs_the_capacity_diagnostic_before_the_expensive_steps(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    set_free(module, monkeypatch, 4 * GIB)
    order = []
    monkeypatch.setattr(module, "security_guard", lambda: order.append("security_guard"))
    monkeypatch.setattr(module, "capacity_diagnostic",
                        lambda: order.append("capacity_diagnostic"))
    monkeypatch.setattr(module, "agent_task_maintenance",
                        lambda: order.append("agent_task_maintenance"))
    monkeypatch.setattr(module, "codex_usage_snapshot",
                        lambda: order.append("codex_usage_snapshot"))
    monkeypatch.setattr(module, "daily_backup", lambda: order.append("daily_backup"))
    monkeypatch.setattr(module, "daily_offsite_prepare",
                        lambda: order.append("daily_offsite_prepare"))
    monkeypatch.setattr(module, "daily_offsite_sync",
                        lambda: order.append("daily_offsite_sync"))
    monkeypatch.setattr(module, "daily_audit", lambda: order.append("daily_audit"))
    monkeypatch.setattr(module, "weekly_self_review",
                        lambda: order.append("weekly_self_review"))
    module.main()
    assert order == ["security_guard", "capacity_diagnostic", "agent_task_maintenance",
                     "codex_usage_snapshot", "daily_backup", "daily_offsite_prepare",
                     "daily_offsite_sync", "daily_audit", "weekly_self_review"]
