"""Host-owned read-only capacity attestation over the existing protected reads.

The account-writable watcher report is an untrusted observation. This module
independently measures the host filesystem and binds that measurement to the
report, the optional root-owned receipt and the caller's host policy. It never
dispatches work, reserves budget, signs anything, or grants execution authority.

Trust model:
- publisher identity comes from ``operation_readiness.read_capacity_report``,
  which only accepts an owner-0 ancestry with a publisher-1001 regular file;
- host identity is the host name plus host-owned (root) execution;
- filesystem identity is the device/inode/mount of a no-follow directory
  snapshot, optionally pinned by policy;
- the measurement is taken by this module, never copied from the report.

Every check fails closed with :class:`AttestationError`. No receipt, an
unpinned non-root measurement, a stale report, an expired receipt, a symlink or
an inode race all deny ``HOST_OWNED``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import errno
import math
import os
from pathlib import Path
import re
import socket
import stat

from . import operation_readiness as readiness
from .evidence import digest
from .operational_adapters import _object
from .operational_incidents import Scope, epoch, token

SCHEMA = "herdr-capacity-attestation-1"
RECEIPT_SCHEMA = "herdr-capacity-receipt-1"
REPORT_PATH = "/var/lib/herdr-capacity-watch/status.json"
RECEIPT_PATH = "/run/herdr/capacity-exporter/receipt.json"
PUBLISHER_UID = 1001
MEASURE_PATH = "/"
MAX_AGE_SECONDS = 900
MAX_DRIFT_BYTES_PER_SECOND = 1 << 30
MAX_SLACK = 1 << 30

# Installed watcher floor/guard (deploy/herdr/check_capacity.py). The host policy
# must agree with the installed watcher; a different floor is a blocker.
DEFAULT_FLOOR = 9663676416
DEFAULT_START_GUARD = 134217728
DEFAULT_DRIFT_BYTES_PER_SECOND = 512 << 20
DEFAULT_BASE_SLACK = 256 << 20

REPORT_FIELDS = frozenset({
    "ready", "available_bytes", "required_bytes", "missing_bytes", "margin_bytes",
    "capacity_warning", "checked_at_epoch", "model_calls", "cleanup_performed",
})
RECEIPT_FIELDS = frozenset({
    "schema_version", "server", "consumer", "project", "event_at", "source_sha256",
})
_MOUNT_RECORD = 2_097_152


class AttestationError(ValueError):
    """A host capacity check failed closed; it conveys no execution authority."""


def _closed(condition, message):
    """Fail closed: every denial is an AttestationError, never a silent value."""
    if not condition:
        raise AttestationError(message)


@dataclass(frozen=True)
class HostIdentity:
    hostname: str
    euid: int


@dataclass(frozen=True)
class AttestorPolicy:
    """Host-selected measurement, identity pins and freshness bounds."""

    server: str
    scope: Scope
    measure_path: str = MEASURE_PATH
    expected_device: int | None = None
    expected_inode: int | None = None
    expected_mount: str | None = None
    max_age: int = MAX_AGE_SECONDS
    floor: int = DEFAULT_FLOOR
    start_guard: int = DEFAULT_START_GUARD
    drift_bytes_per_second: int = DEFAULT_DRIFT_BYTES_PER_SECOND
    base_slack: int = DEFAULT_BASE_SLACK

    def __post_init__(self):
        token(self.server)
        _closed(type(self.scope) is Scope, "invalid capacity attestor scope")
        _absolute_path(self.measure_path, "invalid capacity measurement path")
        _closed(self.expected_device is None or _counter(self.expected_device),
                "invalid expected device")
        _closed(self.expected_inode is None or _counter(self.expected_inode),
                "invalid expected inode")
        _closed(self.expected_mount is None or _absolute_path(self.expected_mount,
                "invalid expected mount", require_result=True), "invalid expected mount")
        _closed(type(self.max_age) is int and 0 < self.max_age <= MAX_AGE_SECONDS,
                "invalid capacity freshness policy")
        _closed(_counter(self.floor) and _counter(self.start_guard),
                "invalid capacity floor policy")
        _closed(_counter(self.drift_bytes_per_second)
                and self.drift_bytes_per_second <= MAX_DRIFT_BYTES_PER_SECOND,
                "invalid capacity drift policy")
        _closed(_counter(self.base_slack) and self.base_slack <= MAX_SLACK,
                "invalid capacity slack policy")


@dataclass(frozen=True)
class FilesystemMeasurement:
    path: str
    device: int
    inode: int
    mount: str
    fragment_size: int
    block_size: int
    available_bytes: int


@dataclass(frozen=True)
class Attestation:
    schema_version: str
    server: str
    scope: Scope
    trust: str
    available_bytes: int
    required_bytes: int
    ready: bool
    measured_at: int
    report_event_at: int
    device: int
    inode: int
    mount: str
    publisher_uid: int
    report_path: str
    receipt_path: str | None
    report_sha256: str
    receipt_sha256: str | None
    evidence_sha256: tuple[str, ...]
    report_bytes: bytes
    receipt_bytes: bytes | None

    def to_dict(self):
        return {
            "schema_version": self.schema_version, "server": self.server,
            "scope": asdict(self.scope), "trust": self.trust,
            "available_bytes": self.available_bytes, "required_bytes": self.required_bytes,
            "ready": self.ready, "measured_at": self.measured_at,
            "report_event_at": self.report_event_at, "device": self.device,
            "inode": self.inode, "mount": self.mount, "publisher_uid": self.publisher_uid,
            "report_path": self.report_path, "receipt_path": self.receipt_path,
            "report_sha256": self.report_sha256, "receipt_sha256": self.receipt_sha256,
            "evidence_sha256": self.evidence_sha256,
        }


def _counter(value):
    return type(value) is int and 0 <= value < 2 ** 63


def _signed_counter(value):
    return type(value) is int and -(2 ** 63) < value < 2 ** 63


def _absolute_path(value, message, *, require_result=False):
    ok = type(value) is str and value.startswith("/") and ".." not in Path(value).parts
    if require_result:
        return ok
    _closed(ok, message)
    return None


def host_identity() -> HostIdentity:
    """The calling process identity; root execution is required for host trust."""
    return HostIdentity(socket.gethostname(), os.geteuid())


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_nlink, info.st_uid, info.st_gid,
            info.st_mode, info.st_mtime_ns, info.st_ctime_ns)


def _snapshot(path):
    """One no-follow directory snapshot: identity plus filesystem counters."""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        counters = os.fstatvfs(fd)
    finally:
        os.close(fd)
    return info, counters


def _mount_point(device, path):
    """Nearest mount point for a device, from the host mount table only."""
    expected = f"{os.major(device)}:{os.minor(device)}"
    try:
        with open("/proc/self/mountinfo", "r", encoding="utf-8") as stream:
            text = stream.read(_MOUNT_RECORD + 1)
    except (OSError, UnicodeError):
        return "UNKNOWN"
    if len(text) > _MOUNT_RECORD:
        return "UNKNOWN"
    matches = []
    for line in text.splitlines():
        prefix, separator, _suffix = line.partition(" - ")
        fields = prefix.split(" ")
        if not separator or len(fields) < 6 or any(not part for part in fields[:6]):
            return "UNKNOWN"
        if fields[2] != expected:
            continue
        point = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), fields[4])
        if path == point or path.startswith(point.rstrip("/") + "/"):
            matches.append(point)
    return max(matches, key=len) if matches else "UNKNOWN"


def measure_filesystem(path: str = MEASURE_PATH) -> FilesystemMeasurement:
    """Independently measure one directory's filesystem, or fail closed.

    The path is opened no-follow twice so a symlink or a replacement between
    the two snapshots is observable. This narrows, but cannot eliminate, the
    remaining open-to-stat race; a pinned device/inode is still required.
    """
    if not (type(path) is str and path.startswith("/") and ".." not in Path(path).parts):
        raise AttestationError("invalid capacity measurement path")
    try:
        first_info, first_counters = _snapshot(path)
        second_info, _second_counters = _snapshot(path)
    except OSError as exc:
        # Linux reports ELOOP for O_NOFOLLOW, but ENOTDIR when O_DIRECTORY is
        # combined with it; both deny a symlink measurement.
        if exc.errno == errno.ELOOP or (
                exc.errno == errno.ENOTDIR and os.path.islink(path)):
            raise AttestationError("capacity measurement path is a symlink") from exc
        raise AttestationError("capacity measurement path is unavailable") from exc
    _closed(stat.S_ISDIR(first_info.st_mode), "capacity measurement path is not a directory")
    _closed(_stamp(first_info) == _stamp(second_info), "capacity measurement inode race")
    return FilesystemMeasurement(
        path=path, device=first_info.st_dev, inode=first_info.st_ino,
        mount=_mount_point(first_info.st_dev, path),
        fragment_size=first_counters.f_frsize, block_size=first_counters.f_bsize,
        available_bytes=first_counters.f_bavail * first_counters.f_frsize,
    )


def _require_filesystem_identity(policy, measurement):
    _closed(type(measurement) is FilesystemMeasurement, "invalid capacity measurement")
    if policy.expected_device is None:
        _closed(policy.measure_path == MEASURE_PATH and measurement.mount == MEASURE_PATH,
                "unpinned capacity measurement must be the host root filesystem")
        return
    _closed(measurement.device == policy.expected_device, "capacity filesystem device mismatch")
    if policy.expected_inode is not None:
        _closed(measurement.inode == policy.expected_inode, "capacity filesystem inode mismatch")
    if policy.expected_mount is not None:
        _closed(measurement.mount == policy.expected_mount, "capacity filesystem mount mismatch")


def _read_receipt():
    try:
        return readiness.read_protected(RECEIPT_PATH, limit=4096)
    except (OSError, readiness.ReadinessError):
        return None


def verify(policy: AttestorPolicy, *, now, host=None, measurement=None,
           report=None, receipt=None) -> Attestation:
    """Verify host identity, filesystem identity, publisher report and receipt.

    ``report``/``receipt`` default to the existing protected reads. Callers that
    supply bytes must have read them through the same protected boundary.
    """
    _closed(type(policy) is AttestorPolicy, "invalid capacity attestor policy")
    now = epoch(now)
    identity = host if host is not None else host_identity()
    _closed(type(identity) is HostIdentity and identity.hostname == policy.server,
            "capacity host identity mismatch")
    _closed(identity.euid == 0, "capacity attestor requires host-owned execution")

    if report is None:
        report = readiness.read_capacity_report()
    row, report_sha256 = _object(report, REPORT_FIELDS)
    checked = row["checked_at_epoch"]
    _closed(type(checked) in (int, float) and math.isfinite(checked) and 0 <= checked <= now,
            "invalid capacity report observation time")
    _closed(type(row["ready"]) is bool and type(row["capacity_warning"]) is bool
            and type(row["model_calls"]) is int and row["model_calls"] == 0
            and row["cleanup_performed"] is False, "invalid capacity report flags")
    for key in ("available_bytes", "required_bytes", "missing_bytes", "margin_bytes"):
        _closed(_signed_counter(row[key]), "invalid capacity report counter")

    receipt_sha256 = None
    if receipt is None:
        receipt = _read_receipt()
    if receipt is not None:
        data, _ = _object(receipt, RECEIPT_FIELDS)
        _closed(data["schema_version"] == RECEIPT_SCHEMA and data["server"] == policy.server
                and data["consumer"] == policy.scope.consumer
                and data["project"] == policy.scope.project
                and type(data["event_at"]) is int and data["event_at"] == int(checked)
                and data["source_sha256"] == report_sha256,
                "capacity receipt identity or digest mismatch")
        _closed(0 <= now - data["event_at"] <= policy.max_age, "capacity receipt expired")
        receipt_sha256 = digest(data)

    _closed(0 <= now - int(checked) <= policy.max_age, "capacity report stale")
    current = measurement if measurement is not None else measure_filesystem(policy.measure_path)
    _require_filesystem_identity(policy, current)
    required_bytes = readiness.capacity(
        current.available_bytes, floor=policy.floor, start_guard=policy.start_guard,
    )["required_bytes"]
    _closed(row["required_bytes"] == required_bytes,
            "capacity report required bytes disagree with host policy")

    drift = max(0.0, now - checked)
    allowance = policy.base_slack + int(policy.drift_bytes_per_second * drift)
    _closed(abs(row["available_bytes"] - current.available_bytes) <= allowance,
            "capacity report measurement mismatch")

    return Attestation(
        schema_version=SCHEMA, server=policy.server, scope=policy.scope,
        trust="HOST_OWNED" if receipt is not None else "PUBLISHER_OBSERVED",
        available_bytes=current.available_bytes, required_bytes=required_bytes,
        ready=current.available_bytes >= required_bytes, measured_at=now,
        report_event_at=int(checked), device=current.device, inode=current.inode,
        mount=current.mount, publisher_uid=PUBLISHER_UID, report_path=REPORT_PATH,
        receipt_path=RECEIPT_PATH if receipt is not None else None,
        report_sha256=report_sha256, receipt_sha256=receipt_sha256,
        evidence_sha256=(report_sha256, receipt_sha256) if receipt_sha256 else (report_sha256,),
        report_bytes=report, receipt_bytes=receipt,
    )


def attestation_digest(attestation: Attestation) -> str:
    """Digest of the verified attestation, for evidence refs and replay checks."""
    return digest(attestation.to_dict())
