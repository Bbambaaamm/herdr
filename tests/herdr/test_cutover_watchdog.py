"""W01-W26: effective systemd authority and transactional watchdog regression."""
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess

import pytest

from test_cutover_transaction import host  # isolated real-file transaction fixture
from herdr.release import ReleaseError
from deploy.herdr.cutover import cutover as current

REAL_VERIFY_CANDIDATE = current.verify_candidate_systemd_runtime
REAL_START_WATCHDOG = current.start_watchdog_service


def test_W22_candidate_watchdog_never_uses_baseline_dropin(host, monkeypatch):
    host.degraded()
    dropin = host.c.UNIT_DIR / "agent-stack-watchdog.service.d/126-capacity-repair.conf"
    dropin.parent.mkdir()
    dropin.write_bytes(b"[Service]\nExecStart=\nExecStart=/approved-capacity-watchdog\n")
    original = host.c.start_watchdog_service

    def start():
        assert not dropin.exists(), "candidate dispatch still uses baseline override"
        original()

    monkeypatch.setattr(host.c, "start_watchdog_service", start)
    assert host.apply()["status"] == "success"


def test_W19_journal_preserves_exact_override_authority(host, monkeypatch):
    host.degraded()
    dropin = host.c.UNIT_DIR / "agent-stack-watchdog.service.d/126-capacity-repair.conf"
    dropin.parent.mkdir()
    dropin.write_bytes(b"capacity-protected-baseline")
    original = host.c.begin_transaction

    def begin(*args):
        path = original(*args)
        journal = json.loads(path.read_bytes())
        assert str(dropin) in journal["files"], "SIGKILL loses baseline override authority"
        return path

    monkeypatch.setattr(host.c, "begin_transaction", begin)
    host.apply()


def baseline_override(host):
    path = host.c.UNIT_DIR / "agent-stack-watchdog.service.d/126-capacity-repair.conf"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"capacity-protected-baseline")
    path.chmod(0o640)
    return path, host.c.snapshot_file(path)


@pytest.mark.parametrize("phase", ["before", "after", "reload", "bridge", "snapshot", "web", "watchdog", "sigterm"],
                         ids=["W08", "W09", "W10", "W11", "W12", "W13", "W14", "W18"])
def test_failure_restores_exact_override_before_watchdog(host, monkeypatch, phase):
    host.degraded()
    c = host.c
    dropin, before = baseline_override(host)
    observed = []
    start = c.start_watchdog_service
    def checked_start():
        if c.CURRENT.resolve() == host.candidate:
            assert not dropin.exists()
            if phase == "watchdog":
                raise ReleaseError("injected_watchdog_start")
        else:
            # Real file state, not an ordering log: exact bytes/mode/owner exist
            # before a single rollback watchdog activation is allowed.
            assert c.snapshot_file(dropin) == before
            assert c.watchdog_permit_path().is_file()
            observed.append("restored")
        start()
    monkeypatch.setattr(c, "start_watchdog_service", checked_start)
    if phase == "before":
        monkeypatch.setattr(c, "reconcile_systemd_authority", lambda _: (_ for _ in ()).throw(ReleaseError("before_remove")))
    elif phase == "after":
        monkeypatch.setattr(c, "install_units", lambda *a, **k: (_ for _ in ()).throw(ReleaseError("after_remove")))
    elif phase == "reload":
        original = c.run
        failed = []
        def run(*args, **kwargs):
            if args == ("/usr/bin/systemctl", "daemon-reload") and not failed:
                failed.append(True)
                raise ReleaseError("reload_failed")
            return original(*args, **kwargs)
        monkeypatch.setattr(c, "run", run)
    elif phase in ("bridge", "snapshot"):
        def ready(*args):
            raise ReleaseError(phase + "_failed")
        monkeypatch.setattr(c, "assert_candidate_ready", ready)
    elif phase == "web":
        host.failure["candidate"] = True
    elif phase == "sigterm":
        remove = c.remove_regular_file
        sent = []
        def interrupt(path):
            remove(path)
            if path == dropin and not sent:
                sent.append(True)
                os.kill(os.getpid(), signal.SIGTERM)
        monkeypatch.setattr(c, "remove_regular_file", interrupt)
    with pytest.raises(ReleaseError, match="rollback_degraded"):
        host.apply()
    assert observed == ["restored"]
    assert c.snapshot_file(dropin) == before
    assert not c.watchdog_permit_path().exists()
    assert not c.watchdog_fence_path().exists()
    assert not (c.STATE_DIR / "transaction.json").exists()
    backup = list(c.STATE_DIR.glob("*-baseline-authority.json"))
    assert len(backup) == 1
    import base64
    assert base64.b64decode(json.loads(backup[0].read_bytes())["files"][str(dropin)][0]) == before[0]


@pytest.mark.parametrize("failure", ["restore", "watchdog", "cleanup"], ids=["W17", "W16_start_failure", "W16_cleanup_failure"])
def test_incomplete_rollback_keeps_start_fence_and_revokes_permit(host, monkeypatch, failure):
    host.degraded()
    c = host.c
    dropin, _ = baseline_override(host)
    host.failure["candidate"] = True
    if failure == "restore":
        original = c.restore_file
        def restore(path, value):
            if path == dropin:
                raise ReleaseError("restore_override_failed")
            original(path, value)
        monkeypatch.setattr(c, "restore_file", restore)
    elif failure == "watchdog":
        monkeypatch.setattr(c, "start_watchdog_service", lambda: (_ for _ in ()).throw(ReleaseError("rollback_watchdog_failed")))
    else:
        monkeypatch.setattr(c, "cleanup_watchdog_fence", lambda: (_ for _ in ()).throw(ReleaseError("cleanup_failed")))
    with pytest.raises(ReleaseError, match="rollback_incomplete"):
        host.apply()
    assert host.states["agent-stack-watchdog.service"] == "inactive"
    assert (c.STATE_DIR / "transaction.json").is_file()
    assert c.watchdog_fence_path().is_file()
    assert not c.watchdog_permit_path().exists()
    assert c.NGINX_ROUTE.read_bytes() == b"maintenance"


def test_W26_healthy_exercise_retains_standard_authority(host):
    result = host.apply()
    assert result["rollback_exercised"] is True
    assert ("ready", host.previous) in host.events
    assert not host.c.watchdog_fence_path().exists()


def test_W26_healthy_capacity_exercise_restores_then_reconciles(host, monkeypatch):
    dropin, original = baseline_override(host)
    ready = host.c.assert_candidate_ready
    checked = []
    def verify(target, document):
        if target == host.previous:
            assert host.c.snapshot_file(dropin) == original
            assert not host.c.watchdog_permit_path().exists()
            checked.append(target)
        else:
            assert not dropin.exists()
        ready(target, document)
    monkeypatch.setattr(host.c, "assert_candidate_ready", verify)
    result = host.apply()
    assert result["status"] == "success" and result["rollback_exercised"]
    assert checked == [host.previous]
    assert not dropin.exists()


def test_W07_candidate_unit_drift_cannot_validate_itself(host, monkeypatch):
    c = host.c
    c.CURRENT.unlink()
    c.CURRENT.symlink_to(host.candidate)
    monkeypatch.setattr(c, "verify_tree", lambda _: {})
    def reject(*args):
        raise ReleaseError("already_deployed_unit_mismatch")
    monkeypatch.setattr(c, "assert_deployed_coherence", reject)
    with pytest.raises(ReleaseError, match="already_deployed_unit_mismatch"):
        REAL_VERIFY_CANDIDATE(host.candidate, {"host_policy": c.capture_systemd_authority()["host_policy"]})


def test_W23_candidate_requires_full_reviewed_maintenance(tmp_path, monkeypatch):
    from deploy.herdr.cutover import systemd_authority as authority
    binary = tmp_path / "agent-stack/bin"
    binary.mkdir(parents=True)
    (binary / "agent-stack-watchdog").write_bytes(b"unreviewed")
    with pytest.raises(ReleaseError, match="candidate_capacity_contract_drift"):
        authority.verify_release_runtime(tmp_path)


def test_W07_no_config_reload_after_watchdog_start_authorization(host, monkeypatch):
    host.events.clear()
    monkeypatch.setattr(host.c, "watchdog_runtime_state", lambda: ("active", "running", 123, 0))
    monkeypatch.setattr(host.c.time, "sleep", lambda _: None)
    REAL_START_WATCHDOG()
    assert ("/usr/bin/systemctl", "start", "agent-stack-watchdog.service") in host.events
    assert ("/usr/bin/systemctl", "daemon-reload") not in host.events


@pytest.mark.skipif(not shutil.which("systemd-analyze"), reason="systemd condition evaluator unavailable")
@pytest.mark.parametrize("journal,permit,allowed", [(False, False, True), (True, False, False), (True, True, True)],
                         ids=["W01_normal_boot", "W19_power_loss_no_permit", "W16_verified_start"])
def test_actual_systemd_start_conditions(tmp_path, journal, permit, allowed):
    record = tmp_path / "transaction.json"
    approval = tmp_path / "permit"
    if journal:
        record.write_text("retained")
    if permit:
        approval.write_text("verified")
    result = subprocess.run(["systemd-analyze", "condition",
        "ConditionPathExists=|!" + str(record), "ConditionPathExists=|" + str(approval)], capture_output=True)
    assert (result.returncode == 0) == allowed
