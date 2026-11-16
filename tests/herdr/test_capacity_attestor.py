"""Host-owned capacity attestor: independent measurement and fail-closed negatives."""
from dataclasses import replace
import hashlib
import json
import os

import pytest

from herdr import capacity_attestor as attestor
from herdr import operation_readiness as readiness
from herdr.evidence import canonical, digest
from herdr.operational_incidents import Scope


NOW = 1794820000
SERVER = "quantlab-staging-01"
SCOPE = Scope("herdr", "Bbambaaamm/herdr")
FLOOR = attestor.DEFAULT_FLOOR
GUARD = attestor.DEFAULT_START_GUARD
DEVICE = 2049
INODE = 2


def report(available, at=NOW - 1, **overrides):
    return canonical({
        **readiness.capacity(available, floor=FLOOR, start_guard=GUARD),
        "checked_at_epoch": at + 0.25, "model_calls": 0, "cleanup_performed": False,
        **overrides,
    })


def receipt(raw, at=NOW - 1, **overrides):
    return canonical({
        "schema_version": attestor.RECEIPT_SCHEMA, "server": SERVER,
        "consumer": SCOPE.consumer, "project": SCOPE.project,
        "event_at": at, "source_sha256": hashlib.sha256(raw).hexdigest(),
        **overrides,
    })


def measurement(available, *, path=attestor.MEASURE_PATH, device=DEVICE, inode=INODE, mount=None):
    return attestor.FilesystemMeasurement(
        path=path, device=device, inode=inode, mount=mount if mount is not None else path,
        fragment_size=4096, block_size=4096, available_bytes=available)


@pytest.fixture
def feed(monkeypatch):
    state = {"report": None, "receipt": None}

    def read_protected(path, *, owner=0, limit=1048576):
        assert (path, owner, limit) == (attestor.RECEIPT_PATH, 0, 4096)
        if state["receipt"] is None:
            raise FileNotFoundError
        return state["receipt"]

    monkeypatch.setattr(attestor.readiness, "read_capacity_report", lambda: state["report"])
    monkeypatch.setattr(attestor.readiness, "read_protected", read_protected)
    return state


@pytest.fixture
def measured(monkeypatch):
    state = {"available": 1, "device": DEVICE, "inode": INODE,
             "mount": attestor.MEASURE_PATH, "path": attestor.MEASURE_PATH}

    def measure(path=attestor.MEASURE_PATH):
        return measurement(state["available"], path=state["path"], device=state["device"],
                           inode=state["inode"], mount=state["mount"])

    monkeypatch.setattr(attestor, "measure_filesystem", measure)
    monkeypatch.setattr(attestor, "host_identity",
                        lambda: attestor.HostIdentity(SERVER, 0))
    return state


@pytest.fixture
def policy():
    return attestor.AttestorPolicy(SERVER, SCOPE, expected_device=DEVICE, expected_inode=INODE)


def install(state, available, *, at=NOW - 1, with_receipt=True):
    raw = report(available, at=at)
    state["report"] = raw
    state["receipt"] = receipt(raw, at=at) if with_receipt else None
    return raw


def test_attestation_binds_independent_measurement_and_receipt(feed, measured, policy):
    raw = install(feed, 10 ** 11)
    measured["available"] = 10 ** 11
    result = attestor.verify(policy, now=NOW)
    assert result.schema_version == attestor.SCHEMA
    assert result.trust == "HOST_OWNED"
    assert result.available_bytes == 10 ** 11
    assert result.required_bytes == FLOOR + GUARD
    assert result.ready is True
    assert (result.device, result.inode, result.mount) == (DEVICE, INODE, "/")
    assert result.publisher_uid == attestor.PUBLISHER_UID
    assert result.report_sha256 == hashlib.sha256(raw).hexdigest()
    assert result.receipt_sha256 == digest(json.loads(feed["receipt"]))
    assert result.report_bytes == raw and result.receipt_bytes == feed["receipt"]
    assert result.evidence_sha256 == (result.report_sha256, result.receipt_sha256)
    assert attestor.attestation_digest(result) == digest(result.to_dict())


def test_without_receipt_trust_stays_publisher_observed(feed, measured, policy):
    install(feed, 10 ** 11, with_receipt=False)
    measured["available"] = 10 ** 11
    result = attestor.verify(policy, now=NOW)
    assert result.trust == "PUBLISHER_OBSERVED"
    assert result.receipt_bytes is None and result.receipt_sha256 is None
    assert result.evidence_sha256 == (result.report_sha256,)


def test_report_readiness_flag_is_not_trusted(feed, measured, policy):
    row = json.loads(report(FLOOR - 1))
    row["ready"] = True
    feed["report"] = canonical(row)
    feed["receipt"] = receipt(feed["report"])
    measured["available"] = FLOOR - 1
    result = attestor.verify(policy, now=NOW)
    assert result.ready is False
    assert result.available_bytes == FLOOR - 1


def test_forged_measurement_blocked(feed, measured, policy):
    install(feed, 10 ** 12)
    measured["available"] = 10 ** 9
    with pytest.raises(attestor.AttestationError, match="measurement mismatch"):
        attestor.verify(policy, now=NOW)


def test_filesystem_device_mismatch_blocked(feed, measured, policy):
    install(feed, 10 ** 11)
    measured["available"] = 10 ** 11
    measured["device"] = 4096
    with pytest.raises(attestor.AttestationError, match="device mismatch"):
        attestor.verify(policy, now=NOW)


def test_filesystem_inode_mismatch_blocked(feed, measured, policy):
    install(feed, 10 ** 11)
    measured["available"] = 10 ** 11
    measured["inode"] = 99
    with pytest.raises(attestor.AttestationError, match="inode mismatch"):
        attestor.verify(policy, now=NOW)


def test_filesystem_mount_mismatch_blocked(feed, measured, policy):
    install(feed, 10 ** 11)
    measured["available"] = 10 ** 11
    with pytest.raises(attestor.AttestationError, match="mount mismatch"):
        attestor.verify(replace(policy, expected_mount="/mnt/other"), now=NOW)


def test_unpinned_non_root_measurement_denied(feed, measured, tmp_path):
    policy = attestor.AttestorPolicy(SERVER, SCOPE, measure_path=str(tmp_path))
    install(feed, 10 ** 11)
    measured["available"] = 10 ** 11
    measured["path"] = str(tmp_path)
    measured["mount"] = str(tmp_path)
    with pytest.raises(attestor.AttestationError, match="unpinned"):
        attestor.verify(policy, now=NOW)


def test_host_identity_mismatch_blocked(feed, measured, policy, monkeypatch):
    install(feed, 10 ** 11)
    measured["available"] = 10 ** 11
    monkeypatch.setattr(attestor, "host_identity",
                        lambda: attestor.HostIdentity("other-host", 0))
    with pytest.raises(attestor.AttestationError, match="host identity mismatch"):
        attestor.verify(policy, now=NOW)


def test_non_host_execution_blocked(feed, measured, policy, monkeypatch):
    install(feed, 10 ** 11)
    measured["available"] = 10 ** 11
    monkeypatch.setattr(attestor, "host_identity",
                        lambda: attestor.HostIdentity(SERVER, 1001))
    with pytest.raises(attestor.AttestationError, match="host-owned execution"):
        attestor.verify(policy, now=NOW)


def test_replay_stale_report_blocked(feed, measured, policy):
    install(feed, 10 ** 11, at=NOW - attestor.MAX_AGE_SECONDS - 100, with_receipt=False)
    measured["available"] = 10 ** 11
    with pytest.raises(attestor.AttestationError, match="report stale"):
        attestor.verify(policy, now=NOW)


def test_expired_receipt_blocked(feed, measured, policy):
    install(feed, 10 ** 11, at=NOW - attestor.MAX_AGE_SECONDS - 100)
    measured["available"] = 10 ** 11
    with pytest.raises(attestor.AttestationError, match="receipt expired"):
        attestor.verify(policy, now=NOW)


def test_receipt_digest_mismatch_blocked(feed, measured, policy):
    raw = install(feed, 10 ** 11)
    feed["receipt"] = receipt(raw, source_sha256="0" * 64)
    measured["available"] = 10 ** 11
    with pytest.raises(attestor.AttestationError, match="identity or digest mismatch"):
        attestor.verify(policy, now=NOW)


def test_receipt_server_mismatch_blocked(feed, measured, policy):
    raw = install(feed, 10 ** 11)
    feed["receipt"] = receipt(raw, server="other-host")
    measured["available"] = 10 ** 11
    with pytest.raises(attestor.AttestationError, match="identity or digest mismatch"):
        attestor.verify(policy, now=NOW)


def test_receipt_schema_version_blocked(feed, measured, policy):
    raw = install(feed, 10 ** 11)
    feed["receipt"] = receipt(raw, schema_version="herdr-capacity-receipt-2")
    measured["available"] = 10 ** 11
    with pytest.raises(attestor.AttestationError, match="identity or digest mismatch"):
        attestor.verify(policy, now=NOW)


def test_report_floor_mismatch_blocked(feed, measured, policy):
    row = json.loads(report(10 ** 11))
    row["required_bytes"] = FLOOR
    feed["report"] = canonical(row)
    feed["receipt"] = receipt(feed["report"])
    measured["available"] = 10 ** 11
    with pytest.raises(attestor.AttestationError, match="required bytes disagree"):
        attestor.verify(policy, now=NOW)


@pytest.mark.parametrize("raw", [b"{", b'{"ready":false,"ready":true}', b" " * 65537])
def test_malformed_report_blocked(feed, measured, policy, raw):
    feed["report"] = raw
    with pytest.raises(ValueError):
        attestor.verify(policy, now=NOW)


def test_symlink_measurement_blocked(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(attestor.AttestationError, match="symlink"):
        attestor.measure_filesystem(str(link))


def test_missing_measurement_path_blocked(tmp_path):
    with pytest.raises(attestor.AttestationError, match="unavailable"):
        attestor.measure_filesystem(str(tmp_path / "missing"))


def test_measurement_path_traversal_denied():
    with pytest.raises(attestor.AttestationError, match="invalid capacity measurement path"):
        attestor.measure_filesystem("/../etc")


def test_inode_race_blocked(monkeypatch, tmp_path):
    first = tmp_path / "a"
    first.mkdir()
    second = tmp_path / "b"
    second.mkdir()
    snapshots = [(os.stat(first), os.statvfs(first)), (os.stat(second), os.statvfs(second))]
    monkeypatch.setattr(attestor, "_snapshot", lambda path: snapshots.pop(0))
    with pytest.raises(attestor.AttestationError, match="inode race"):
        attestor.measure_filesystem(str(first))


@pytest.mark.skipif(os.name != "posix", reason="host filesystem identity requires POSIX")
def test_real_root_measurement_is_independent():
    result = attestor.measure_filesystem("/")
    info = os.stat("/")
    counters = os.statvfs("/")
    assert result.device == info.st_dev
    assert result.inode == info.st_ino
    assert result.available_bytes == counters.f_bavail * counters.f_frsize
    assert result.fragment_size == counters.f_frsize
    assert result.mount == "/"
