"""Host evidence phase 2: signed historic receipts are NEVER cleanup grants."""
from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from herdr import build_lifecycle_host_evidence as h


def fixture(*, device=2050, inode=88, uid=1001, at=None):
    now = at or datetime.now(UTC)
    raw = {
        "build_id": "herdr-hermes-build-case1",
        "source_commit": "a" * 40,
        "root_device": device,
        "root_inode": inode,
        "owner_uid": uid,
        "task_id": "task-7",
        "attempt": 2,
        "fencing_token": 4,
        "lease_state": "RELEASED",
        "evidence_digest": "b" * 64,
        "parent_ack_digest": "c" * 64,
        "issued_at": (now - timedelta(seconds=10)).isoformat(),
        "expires_at": (now + timedelta(seconds=30)).isoformat(),
        "issuer": "root-owned-build-evidence-issuer",
        "observation_mode": "HOST_READ_ONLY",
    }
    signer = Ed25519PrivateKey.generate()
    public = signer.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    envelope = {
        "schema_version": "herdr-build-host-evidence-v1",
        "algorithm": "ed25519",
        "key_id": "host-test",
        "receipt": raw,
    }
    envelope["signature"] = base64.b64encode(signer.sign(h._canonical(envelope))).decode()
    return envelope, public, now


def valid(envelope, public, now):
    return h.validate_receipt(
        envelope, public_key=public, expected_key_id="host-test",
        expected_build_id="herdr-hermes-build-case1",
        expected_device=2050, expected_inode=88, expected_owner_uid=1001,
        at=now,
    )


def test_signed_host_receipt_is_historical_not_cleanup_authority():
    row, public, now = fixture()
    verified = valid(row, public, now)
    assert verified["signature_verified"]
    assert verified["fencing_token"] == 4
    assert verified["parent_ack_digest"] == "c" * 64
    assert verified["cleanup_authorized"] is False


@pytest.mark.parametrize("field,value", [
    ("build_id", "herdr-hermes-build-other"),
    ("root_inode", 9),
    ("root_device", 2),
    ("owner_uid", 0),
])
def test_exact_build_identity_fenced_off(field, value):
    row, public, now = fixture()
    row["receipt"][field] = value
    with pytest.raises(h.BuildHostEvidenceError, match="IDENTITY_MISMATCH"):
        valid(row, public, now)


def test_forged_fencing_or_parent_ack_invalidates_signature():
    row, public, now = fixture()
    for field, value in (
        ("fencing_token", 500),
        ("parent_ack_digest", "d" * 64),
        ("evidence_digest", "e" * 64),
        ("lease_state", "RELEASED_EXTRA"),
    ):
        mutant = json.loads(json.dumps(row))
        mutant["receipt"][field] = value
        with pytest.raises(h.BuildHostEvidenceError):
            valid(mutant, public, now)


def test_forged_signature_or_wrong_key_rejected():
    row, public, now = fixture()
    other, other_public, _ = fixture()
    with pytest.raises(h.BuildHostEvidenceError, match="SIGNATURE_INVALID"):
        valid(row, other_public, now)
    row["signature"] = other["signature"]
    with pytest.raises(h.BuildHostEvidenceError, match="SIGNATURE_INVALID"):
        valid(row, public, now)


def test_expired_receipt_not_promoted_to_live_authority():
    row, public, now = fixture()
    with pytest.raises(h.BuildHostEvidenceError, match="EXPIRED"):
        valid(row, public, now + timedelta(minutes=20))


def test_oversized_or_unbounded_signed_data_denied():
    row, public, now = fixture()
    row["receipt"]["task_id"] = "x" * 15000
    with pytest.raises(h.BuildHostEvidenceError):
        valid(row, public, now)


def test_host_trust_anchor_must_be_protected_root_not_scratch(tmp_path):
    trust = tmp_path / "trust.json"
    row, pub, now = fixture()
    trust.write_text(json.dumps({
        "schema_version": "herdr-build-evidence-trust-v1",
        "algorithm": "ed25519", "key_id": "host-test",
        "public_key_b64": base64.b64encode(pub).decode(),
    }))
    with pytest.raises((RuntimeError, ValueError, OSError)):
        h.read_root_trust_anchor(trust)


def test_unprivileged_receipt_file_is_not_root_evidence(tmp_path):
    row, pub, now = fixture()
    file = tmp_path / "receipt.json"
    file.write_text(json.dumps(row))
    with pytest.raises((RuntimeError, ValueError, OSError)):
        h.read_root_envelope(file)


def test_mountinfo_scoped_detection_remains_non_authoritative(tmp_path):
    path = tmp_path / "herdr-hermes-build-case1"
    path.mkdir()
    mountinfo = f"50 40 8:1 / {path} rw,relatime - ext4 /dev/sda1 rw\n"
    row = h.inspect_mount_boundary(path, mountinfo=mountinfo)
    assert row["state"] == "MOUNT_FOUND"
    assert row["matches"] == [str(path)]
    assert row["cleanup_authorized"] is False
    other = h.inspect_mount_boundary(path, mountinfo="50 40 8:1 / /var rw - ext4 /dev/sda1 rw\n")
    assert other["state"] == "NO_MOUNT_IN_OWN_NAMESPACE_ONLY"
    assert other["cleanup_authorized"] is False


def test_double_slash_root_is_normalized_for_mount_comparison(tmp_path):
    # POSIX permits exactly two leading slashes and Path preserves them, while
    # mountinfo uses a single leading slash.  The accepted root must not be able
    # to suppress the mount observation for the same directory.
    path = tmp_path / "herdr-hermes-build-case1"
    path.mkdir()
    mountinfo = f"50 40 8:1 / {path} rw,relatime - ext4 /dev/sda1 rw\n"
    row = h.inspect_mount_boundary(Path("//" + str(path)), mountinfo=mountinfo)
    assert row["state"] == "MOUNT_FOUND"
    assert row["matches"] == [str(path)]
    assert row["cleanup_authorized"] is False


def test_real_root_scan_blocks_missing_trust_and_no_authority(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir(mode=0o700)
    candidate = root / "herdr-hermes-build-case1"
    candidate.mkdir(mode=0o700)
    (candidate / "result.txt").write_text("result")
    report = h.host_evidence_scan(
        root, (candidate.name,),
        trust_path=tmp_path / "untrusted.json",
        receipt_root=tmp_path,
    )
    row = report["candidates"][0]
    assert row["host_evidence_state"] == "ROOT_EVIDENCE_UNAVAILABLE"
    assert row["process_observation"]["state"] in (
        "UNKNOWN", "NO_REFERENCE_IN_VISIBLE_NAMESPACE_ONLY",
        "REFERENCES_OBSERVED",
    )
    assert row["process_observation"]["cleanup_authorized"] is False
    assert "TRUSTED_ROOT_EVIDENCE_UNAVAILABLE" in row["blockers"]
    assert row["can_delete"] is False
    assert report["deletion_performed"] is False
    assert report["live_authority_accepted"] is False
    assert (candidate / "result.txt").read_text() == "result"


def test_even_valid_signed_historical_receipt_not_authorization(monkeypatch, tmp_path):
    root = tmp_path / "scratch"
    root.mkdir(mode=0o700)
    candidate = root / "herdr-hermes-build-case1"
    candidate.mkdir(mode=0o700)
    info = candidate.stat()
    envelope, public, now = fixture(device=info.st_dev, inode=info.st_ino, uid=os.getuid())
    # This injection is a test fixture only. The production path reads only
    # independently protected root-owned trust and receipt material.
    monkeypatch.setattr(h, "read_root_trust_anchor", lambda path: ("host-test", public))
    monkeypatch.setattr(h, "read_root_envelope", lambda path: envelope)
    report = h.host_evidence_scan(root, (candidate.name,))
    row = report["candidates"][0]
    assert row["host_evidence_state"] == "HISTORICAL_SIGNATURE_VALID_ONLY"
    assert row["host_evidence"]["signature_verified"] is True
    assert "RUNTIME_HOST_REVALIDATION_REQUIRED" in row["blockers"]
    assert row["cleanup_authorized"] is False
    assert row["can_delete"] is False


def test_process_reference_detector_observes_open_fd(tmp_path):
    base = tmp_path / "scratch"
    base.mkdir()
    path = base / "herdr-hermes-build-case1"
    path.mkdir()
    proc = tmp_path / "proc"
    pid = proc / "12345"
    fd = pid / "fd"
    fd.mkdir(parents=True)
    (pid / "cwd").symlink_to("/unrelated")
    (pid / "root").symlink_to("/")
    (fd / "7").symlink_to(path / "artifact.txt")
    result = h.inspect_process_references(path, proc=proc)
    assert result["state"] == "REFERENCES_OBSERVED"
    assert result["references"] == [{"pid": 12345, "via": "fd"}]
    assert result["cleanup_authorized"] is False


def test_double_slash_root_is_normalized_for_process_comparison(tmp_path):
    # A root spelled with a leading double slash must still match the single
    # slash spelling used by /proc cwd/root/fd links.
    base = tmp_path / "scratch"
    base.mkdir()
    path = base / "herdr-hermes-build-case1"
    path.mkdir()
    proc = tmp_path / "proc"
    pid = proc / "12345"
    fd = pid / "fd"
    fd.mkdir(parents=True)
    (pid / "cwd").symlink_to("/unrelated")
    (pid / "root").symlink_to("/")
    (fd / "7").symlink_to(path / "artifact.txt")
    result = h.inspect_process_references(Path("//" + str(path)), proc=proc)
    assert result["state"] == "REFERENCES_OBSERVED"
    assert result["references"] == [{"pid": 12345, "via": "fd"}]
    assert result["cleanup_authorized"] is False


def test_process_reference_detector_unknown_when_pid_inaccessible(tmp_path):
    path = tmp_path / "herdr-hermes-build-case1"
    path.mkdir()
    proc = tmp_path / "proc"
    (proc / "12345").mkdir(parents=True)
    result = h.inspect_process_references(path, proc=proc)
    assert result["state"] == "UNKNOWN"
    assert result["incomplete"]
    assert result["cleanup_authorized"] is False


def test_process_reference_detector_limits_are_fail_closed(tmp_path):
    path = tmp_path / "herdr-hermes-build-case1"
    path.mkdir()
    proc = tmp_path / "proc"
    for pid in ("1", "2", "3"):
        (proc / pid / "fd").mkdir(parents=True)
        (proc / pid / "cwd").symlink_to("/unrelated")
        (proc / pid / "root").symlink_to("/")
    result = h.inspect_process_references(path, proc=proc, max_pids=1)
    assert result["state"] == "UNKNOWN"
    assert result["incomplete"]
    assert result["cleanup_authorized"] is False


def test_no_filesystem_mutation_and_no_model_call(monkeypatch, tmp_path):
    import shutil
    import socket
    def blocked(*a, **kw):
        raise AssertionError("side-effect attempted")
    root = tmp_path / "scratch"
    root.mkdir(mode=0o700)
    candidate = root / "herdr-hermes-build-case1"
    candidate.mkdir(mode=0o700)
    monkeypatch.setattr(os, "unlink", blocked)
    monkeypatch.setattr(os, "rmdir", blocked)
    monkeypatch.setattr(shutil, "rmtree", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    report = h.host_evidence_scan(root, (candidate.name,), trust_path=tmp_path / "missing")
    assert report["model_calls"] == 0
    assert report["deletion_performed"] is False


def test_process_scan_never_uses_unbounded_listdir(monkeypatch, tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    proc = tmp_path / "proc"
    fds = proc / "1000" / "fd"
    fds.mkdir(parents=True)
    (proc / "1000" / "cwd").symlink_to("/")
    (proc / "1000" / "root").symlink_to("/")
    for i in range(12):
        (fds / str(i)).symlink_to("/elsewhere")
    def forbid_listdir(*_args, **_kwargs):
        raise AssertionError("unbounded listdir on /proc is forbidden")
    monkeypatch.setattr(os, "listdir", forbid_listdir)
    report = h.inspect_process_references(root, proc=proc, max_pids=5, max_fds=2)
    assert report["incomplete"] is True
    assert report["state"] == "UNKNOWN"
    assert report["cleanup_authorized"] is False


def test_process_scan_stops_at_bounded_number_of_pids(monkeypatch, tmp_path):
    proc = tmp_path / "proc"
    proc.mkdir()
    for i in range(30):
        (proc / str(2000 + i) / "fd").mkdir(parents=True)
    report = h.inspect_process_references(tmp_path / "missing",
                                          proc=proc, max_pids=3)
    assert report["incomplete"] is True
    assert report["state"] == "UNKNOWN"
    assert not report["cleanup_authorized"]


def test_escaped_mountpoint_is_detected_and_never_authorized(tmp_path):
    path = tmp_path / "herdr build"
    encoded = str(path).replace(" ", r"\040")
    mountinfo = f"50 40 8:1 / {encoded} rw,relatime - ext4 /dev/sda1 rw\n"
    result = h.inspect_mount_boundary(path, mountinfo=mountinfo)
    assert result["state"] == "MOUNT_FOUND"
    assert result["matches"] == [str(path)]
    assert result["cleanup_authorized"] is False


def test_ambiguous_or_oversized_mountinfo_is_unknown(tmp_path):
    path = tmp_path / "herdr build"
    for mountinfo in (
        "not a valid mountinfo record",
        "bad" * 700000,
        "50 40 8:1 / /bad rw,relatime",
    ):
        result = h.inspect_mount_boundary(path, mountinfo=mountinfo)
        assert result["state"] == "UNKNOWN"
        assert result["cleanup_authorized"] is False


def test_root_trust_and_receipt_duplicate_json_fields_fail_closed(tmp_path):
    root = tmp_path / "receipt.json"
    root.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(h.BuildHostEvidenceError, match="DUPLICATE_JSON"):
        h._strict_json(root.read_bytes())
    with pytest.raises(h.BuildHostEvidenceError, match="JSON_INVALID"):
        h._strict_json(b"{garbled")
