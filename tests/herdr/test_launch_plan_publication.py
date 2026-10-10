"""Operator issuance in disposable files; root checks are explicit test doubles.

No test publishes a real root record, installs an issuer or touches task state.
"""
from datetime import UTC, datetime, timedelta
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from herdr import host_configuration, launch_plan_publication as publication, private_mount_plan
from herdr.private_mount_plan import ApprovedPrivateMountPlan, request_for
from herdr.security import InvocationIdentity, SecurityError, canonical_json_bytes


@pytest.fixture
def approved(tmp_path, monkeypatch):
    authority = tmp_path / "plans"
    authority.mkdir()
    tickets = tmp_path / "approvals"
    tickets.mkdir()
    identity = InvocationIdentity("github:example/repo", "child", "root", "root-task", "child-task", "run-1", 1)
    identity_sha = hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest()
    entries = [
        {"source": "/proc/123/fd/7", "fd": 7, "device": 1, "inode": 4,
         "kind": "directory", "target": "/tmp/fixture-work"},
        {"source": "/proc/123/fd/8", "fd": 8, "device": 1, "inode": 5,
         "kind": "reserved-result", "target": "/tmp/fixture-result.json",
         "reservation": {"schema_version": "herdr-result-reservation-1", "path": "/tmp/fixture-result.json",
                         "device": 1, "inode": 5, "identity_sha256": identity_sha,
                         "idempotency_key": "fixture-result", "max_bytes": 8192}},
    ]
    argv = ["/usr/bin/bwrap", "--unshare-net", "--bind-fd", "7", "/tmp/fixture-work",
            "--bind-fd", "8", "/tmp/fixture-result.json", "--", "/bin/true"]
    now = datetime(2026, 1, 1, tzinfo=UTC)
    ticket = {"schema_version": publication.TICKET_VERSION, "plan": request_for(identity, entries, argv),
              "argv": argv, "not_before": (now - timedelta(seconds=10)).isoformat(),
              "expires_at": (now + timedelta(seconds=60)).isoformat()}
    path = tickets / (identity_sha + ".json")
    path.write_bytes(canonical_json_bytes(ticket))
    # These four substitutions isolate the operator's root authority and clock.
    # File bytes, inode creation, fsync, permissions and atomic rename stay real.
    monkeypatch.setattr(publication, "AUTHORITY_ROOT", authority)
    monkeypatch.setattr(publication, "APPROVAL_ROOT", tickets)
    monkeypatch.setattr(private_mount_plan, "AUTHORITY_ROOT", authority)
    monkeypatch.setattr(publication, "_utc_now", lambda: now)
    monkeypatch.setattr(host_configuration, "_read_configuration", lambda selected: json.loads(Path(selected).read_bytes()))
    monkeypatch.setattr(publication, "_verify_root_owned_ancestry", lambda selected: None)
    return path, ticket, identity, authority, now


def save(path, ticket):
    path.write_bytes(canonical_json_bytes(ticket))


def permit_test_operator(monkeypatch):
    # Only a test double; files still belong to the actual unprivileged test UID.
    monkeypatch.setattr(publication.os, "geteuid", lambda: 0)
    monkeypatch.setattr(publication, "_root_owner", lambda info: None)


def test_default_preflight_does_not_create_a_plan(approved):
    path, ticket, identity, authority, _ = approved
    result = publication.publish_approved_launch_plan(path)
    assert result["published"] is False
    assert result["destination"] == str(authority / path.name)
    assert result["plan_sha256"] == hashlib.sha256(canonical_json_bytes(ticket["plan"])).hexdigest()
    assert list(authority.iterdir()) == []


def test_actual_worker_publish_denied_before_approval_read(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("suite does not invoke a real privileged publication")
    with pytest.raises(SecurityError, match="privileged operator"):
        publication.publish_approved_launch_plan(tmp_path / "missing", publish=True)
    assert list(tmp_path.iterdir()) == []


def test_actual_worker_cannot_supply_a_root_ticket(tmp_path):
    path = tmp_path / "worker-ticket.json"
    path.write_text("{}")
    with pytest.raises(SecurityError, match="outside fixed host authority"):
        publication.publish_approved_launch_plan(path)


def test_real_protected_reader_rejects_worker_owned_ticket(approved, monkeypatch):
    path, *_ = approved
    # Restore the production reader; moving the path constant does not turn
    # an ordinary user's ticket/ancestry into a genuine host approval.
    monkeypatch.undo()
    monkeypatch.setattr(publication, "APPROVAL_ROOT", path.parent)
    with pytest.raises(SecurityError, match="untrusted"):
        publication.publish_approved_launch_plan(path)


@pytest.mark.parametrize("fault", ["expired", "future", "long", "naive", "invalid", "numeric", "reversed"])
def test_finite_operator_issuance_window(approved, fault):
    path, ticket, _, authority, now = approved
    if fault == "expired": ticket["expires_at"] = now.isoformat()
    elif fault == "future": ticket["not_before"] = (now + timedelta(seconds=1)).isoformat()
    elif fault == "long": ticket["expires_at"] = (now + timedelta(hours=2)).isoformat()
    elif fault == "naive": ticket["not_before"] = "2026-01-01T00:00:00"
    elif fault == "invalid": ticket["expires_at"] = "not-a-date"
    elif fault == "numeric": ticket["not_before"] = True
    else: ticket["expires_at"] = (now - timedelta(minutes=1)).isoformat()
    save(path, ticket)
    with pytest.raises(SecurityError, match="approval window"):
        publication.publish_approved_launch_plan(path)
    assert list(authority.iterdir()) == []


@pytest.mark.parametrize("fault", ["extra", "version", "plan-version", "identity-extra", "fence-bool", "name", "hardlink"])
def test_closed_operator_ticket_and_full_identity(approved, fault):
    path, ticket, _, authority, _ = approved
    if fault == "extra": ticket["worker_request_path"] = "/tmp/worker-data"
    elif fault == "version": ticket["schema_version"] = "worker-self-approval"
    elif fault == "plan-version": ticket["plan"]["schema_version"] = "wrong"
    elif fault == "identity-extra": ticket["plan"]["identity"]["approval"] = True
    elif fault == "fence-bool": ticket["plan"]["identity"]["fencing_token"] = True
    elif fault == "name":
        changed = path.with_name("wrong-name.json")
        path.rename(changed)
        path = changed
    else: os.link(path, path.parent / "alias")
    save(path, ticket)
    with pytest.raises(SecurityError):
        publication.publish_approved_launch_plan(path)
    assert list(authority.iterdir()) == []


@pytest.mark.parametrize("fault", ["sha", "argv-extra", "argv-nul", "argv-bound", "executor", "separator", "descriptor-extra",
                                   "source", "target", "duplicate-fd", "duplicate-target", "boolean-fd", "unknown-kind",
                                   "missing-bind", "duplicate-bind", "bind-target", "result-identity", "result-path", "result-inode",
                                   "result-key", "result-size", "writes", "kind-list", "double-root"])
def test_complete_plan_shape_and_command_binding(approved, fault):
    path, ticket, _, authority, _ = approved
    plan, argv = ticket["plan"], ticket["argv"]
    entry = plan["descriptors"][1]
    if fault == "sha": plan["argv_sha256"] = "0" * 64
    elif fault == "argv-extra": argv.append("unexpected-command-argument")
    elif fault == "argv-nul": argv[-1] = "bad\0argument"
    elif fault == "argv-bound": argv[-1] = "a" * 33000
    elif fault == "executor": argv[0] = "/bin/sh"
    elif fault == "separator": argv.remove("--")
    elif fault == "descriptor-extra": entry["authority"] = "worker"
    elif fault == "source": entry["source"] = "/proc/123/fd/7"
    elif fault == "target": entry["target"] = "/tmp/../secret"
    elif fault == "duplicate-fd": entry["fd"] = 7; entry["source"] = "/proc/123/fd/7"
    elif fault == "duplicate-target": entry["target"] = plan["descriptors"][0]["target"]
    elif fault == "boolean-fd": entry["fd"] = True
    elif fault == "unknown-kind": entry["kind"] = "self-approved-root"
    elif fault == "kind-list": entry["kind"] = []
    elif fault == "double-root": entry["target"] = "//tmp/fixture-result.json"
    elif fault == "missing-bind": del argv[5:8]
    elif fault == "duplicate-bind": argv[5:5] = argv[2:5]
    elif fault == "bind-target": argv[7] = "/tmp/different-slot"
    elif fault == "result-identity": entry["reservation"]["identity_sha256"] = "0" * 64
    elif fault == "result-path": entry["reservation"]["path"] = "/tmp/different-slot"
    elif fault == "result-inode": entry["reservation"]["inode"] = True
    elif fault == "result-key": entry["reservation"]["idempotency_key"] = "space is invalid"
    elif fault == "result-size": entry["reservation"]["max_bytes"] = 0
    else: plan["writable_targets"] = []
    save(path, ticket)
    with pytest.raises(SecurityError):
        publication.publish_approved_launch_plan(path)
    assert list(authority.iterdir()) == []


def test_new_inode_record_is_consumed_by_existing_plan_reader(approved, monkeypatch):
    path, ticket, identity, authority, _ = approved
    permit_test_operator(monkeypatch)
    result = publication.publish_approved_launch_plan(path, publish=True)
    target = authority / path.name
    assert result["published"] is True
    assert target.read_bytes() == canonical_json_bytes(ticket["plan"])
    assert target.stat().st_ino != path.stat().st_ino
    assert stat.S_IMODE(target.stat().st_mode) == 0o444
    assert target.stat().st_nlink == 1
    plan = ApprovedPrivateMountPlan.read(target, identity)
    assert plan.authorize(ticket["plan"]["descriptors"], ticket["argv"])["authority"] == str(target)
    with pytest.raises(SecurityError):
        plan.authorize(ticket["plan"]["descriptors"], [*ticket["argv"], "changed"])


def test_existing_plan_never_replaced_and_failure_stage_retained(approved, monkeypatch):
    path, ticket, identity, authority, _ = approved
    permit_test_operator(monkeypatch)
    publication.publish_approved_launch_plan(path, publish=True)
    target = authority / path.name
    before = target.stat()
    with pytest.raises(OSError) as failure:
        publication.publish_approved_launch_plan(path, publish=True)
    assert failure.value.errno == errno.EEXIST
    assert target.stat().st_ino == before.st_ino
    assert target.read_bytes() == canonical_json_bytes(ticket["plan"])
    assert len(list(authority.glob(".launch-plan-*"))) == 1
    with pytest.raises(SecurityError, match="outside host authority"):
        ApprovedPrivateMountPlan.read(next(authority.glob(".launch-plan-*")), identity)


@pytest.mark.parametrize("fault", ["expires", "withdraw", "enospc"])
def test_late_failure_denies_before_atomic_visibility_and_closes_fds(approved, monkeypatch, fault):
    path, ticket, identity, authority, now = approved
    permit_test_operator(monkeypatch)
    original = publication.os.fsync
    def fail(fd):
        if fault == "enospc": raise OSError(errno.ENOSPC, "injected fixture disk full")
        original(fd)
        if fault == "expires": monkeypatch.setattr(publication, "_utc_now", lambda: now + timedelta(minutes=3))
        else:
            ticket["expires_at"] = (now + timedelta(seconds=50)).isoformat()
            save(path, ticket)
    monkeypatch.setattr(publication.os, "fsync", fail)
    before = set(os.listdir("/proc/self/fd"))
    with pytest.raises((SecurityError, OSError)):
        publication.publish_approved_launch_plan(path, publish=True)
    assert not (authority / path.name).exists()
    assert len(list(authority.glob(".launch-plan-*"))) == 1
    with pytest.raises(SecurityError, match="outside host authority"):
        ApprovedPrivateMountPlan.read(next(authority.glob(".launch-plan-*")), identity)
    assert set(os.listdir("/proc/self/fd")) == before


def test_cli_worker_denial(approved):
    if os.geteuid() == 0:
        pytest.skip("suite never invokes the CLI as a privileged operator")
    script = Path(__file__).resolve().parents[2] / "scripts/publish-herdr-launch-plan.py"
    result = subprocess.run([sys.executable, str(script), "--configuration", "/etc/herdr/nonexistent-approval.json",
                             "--publish"], capture_output=True, timeout=10)
    assert result.returncode != 0
    assert b"requires privileged operator" in result.stderr


def test_mismatched_actual_new_inode_owner_denies_even_with_only_uid_double(approved, monkeypatch):
    if os.geteuid() == 0:
        pytest.skip("requires actual ordinary-user file ownership")
    path, _, _, authority, _ = approved
    monkeypatch.setattr(publication.os, "geteuid", lambda: 0)
    with pytest.raises(SecurityError, match="root-owned inode"):
        publication.publish_approved_launch_plan(path, publish=True)
    assert not (authority / path.name).exists()


def test_post_rename_sync_failure_retains_visible_record_for_reconciliation(approved, monkeypatch):
    path, ticket, _, authority, _ = approved
    permit_test_operator(monkeypatch)
    original = publication.os.fsync
    calls = []
    def fail_parent(fd):
        calls.append(fd)
        if stat.S_ISDIR(os.fstat(fd).st_mode): raise OSError(errno.EIO, "injected directory sync failure")
        original(fd)
    monkeypatch.setattr(publication.os, "fsync", fail_parent)
    before = set(os.listdir("/proc/self/fd"))
    with pytest.raises(OSError) as failure:
        publication.publish_approved_launch_plan(path, publish=True)
    assert failure.value.errno == errno.EIO
    assert (authority / path.name).read_bytes() == canonical_json_bytes(ticket["plan"])
    assert len(calls) == 2
    assert set(os.listdir("/proc/self/fd")) == before
