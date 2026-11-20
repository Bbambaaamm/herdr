"""Phase 2: READ-ONLY host-evidence verification for disposable build scans.

Ed25519 receipts must be signed by an independently root-owned issuer whose
public key is anchored under protected /etc/herdr. The user-owned build
manifest NEVER establishes authority. Even a valid signed receipt is a
historical assertion only; it cannot authorize or execute cleanup.

Live mount/process/lease/fencing/evidence verification must ultimately take
place together, under the privileged host cleanup authority at deletion time.
This module deliberately has no deletion/move/approval API.
"""
from __future__ import annotations

import base64
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

from .build_lifecycle import inventory
from .operation_readiness import read_protected

_SHA = re.compile(r"^[0-9a-f]{64}$")
_GIT = re.compile(r"^[0-9a-f]{40}$")
_KEY = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SCHEMA = "herdr-build-host-evidence-v1"
_TRUST_SCHEMA = "herdr-build-evidence-trust-v1"
_MAX_RECORD = 16384


class BuildHostEvidenceError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _strict_json(payload: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BuildHostEvidenceError("HOST_EVIDENCE_DUPLICATE_JSON_FIELD")
            result[key] = value
        return result

    try:
        return json.loads(payload, object_pairs_hook=unique)
    except BuildHostEvidenceError:
        raise
    except (ValueError, UnicodeError) as exc:
        raise BuildHostEvidenceError("HOST_EVIDENCE_JSON_INVALID") from exc


def _b64(text: str, expected_bytes: int) -> bytes:
    if not isinstance(text, str) or len(text) > 256:
        raise BuildHostEvidenceError("EVIDENCE_SIGNATURE_OR_KEY_INVALID")
    try:
        result = base64.b64decode(text, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise BuildHostEvidenceError("EVIDENCE_SIGNATURE_OR_KEY_INVALID") from exc
    if len(result) != expected_bytes:
        raise BuildHostEvidenceError("EVIDENCE_SIGNATURE_OR_KEY_INVALID")
    return result


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 48:
        raise BuildHostEvidenceError("EVIDENCE_TIMESTAMP_INVALID")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BuildHostEvidenceError("EVIDENCE_TIMESTAMP_INVALID") from exc
    if result.tzinfo is None or result.utcoffset() != datetime.now(UTC).utcoffset():
        raise BuildHostEvidenceError("EVIDENCE_TIMESTAMP_INVALID")
    return result.astimezone(UTC)


def validate_receipt(
    envelope: dict[str, Any],
    *,
    public_key: bytes,
    expected_key_id: str,
    expected_build_id: str,
    expected_device: int,
    expected_inode: int,
    expected_owner_uid: int,
    at: datetime | None = None,
) -> dict[str, Any]:
    """Verify cryptography AND precise scan-bound identity, never approval.

    A validated envelope reports only that a trusted issuer signed specified
    historical facts. It DOES NOT prove no current process or lease exists.
    """
    if type(envelope) is not dict or set(envelope) != {
        "schema_version", "algorithm", "key_id", "receipt", "signature"
    }:
        raise BuildHostEvidenceError("HOST_EVIDENCE_ENVELOPE_INVALID")
    if (envelope["schema_version"] != _SCHEMA
            or envelope["algorithm"] != "ed25519"
            or envelope["key_id"] != expected_key_id
            or not _KEY.fullmatch(str(expected_key_id))):
        raise BuildHostEvidenceError("HOST_EVIDENCE_ENVELOPE_INVALID")
    receipt = envelope["receipt"]
    required = {
        "build_id", "source_commit", "root_device", "root_inode", "owner_uid",
        "task_id", "attempt", "fencing_token", "lease_state",
        "evidence_digest", "parent_ack_digest", "issued_at", "expires_at",
        "issuer", "observation_mode",
    }
    if type(receipt) is not dict or set(receipt) != required:
        raise BuildHostEvidenceError("HOST_EVIDENCE_RECEIPT_INVALID")
    if (receipt["build_id"] != expected_build_id
            or type(receipt["root_device"]) is not int or receipt["root_device"] != expected_device
            or type(receipt["root_inode"]) is not int or receipt["root_inode"] != expected_inode
            or type(receipt["owner_uid"]) is not int or receipt["owner_uid"] != expected_owner_uid):
        raise BuildHostEvidenceError("HOST_EVIDENCE_BUILD_IDENTITY_MISMATCH")
    if (type(receipt["source_commit"]) is not str or not _GIT.fullmatch(receipt["source_commit"])
            or type(receipt["task_id"]) is not str or not 1 <= len(receipt["task_id"]) <= 128
            or type(receipt["attempt"]) is not int or receipt["attempt"] < 0
            or type(receipt["fencing_token"]) is not int or receipt["fencing_token"] < 0
            or type(receipt["evidence_digest"]) is not str
            or not _SHA.fullmatch(receipt["evidence_digest"])
            or type(receipt["parent_ack_digest"]) is not str
            or not _SHA.fullmatch(receipt["parent_ack_digest"])
            or receipt["lease_state"] != "RELEASED"
            or receipt["issuer"] != "root-owned-build-evidence-issuer"
            or receipt["observation_mode"] != "HOST_READ_ONLY"):
        raise BuildHostEvidenceError("HOST_EVIDENCE_RECEIPT_INVALID")
    issued = _timestamp(receipt["issued_at"])
    expiry = _timestamp(receipt["expires_at"])
    current = at or datetime.now(UTC)
    if current.tzinfo is None or not issued <= current <= expiry or (expiry - issued).total_seconds() > 300:
        raise BuildHostEvidenceError("HOST_EVIDENCE_EXPIRED_OR_FUTURE")
    if not isinstance(public_key, bytes) or len(public_key) != 32:
        raise BuildHostEvidenceError("HOST_EVIDENCE_TRUST_ANCHOR_INVALID")
    unsigned = {
        "schema_version": envelope["schema_version"],
        "algorithm": envelope["algorithm"],
        "key_id": envelope["key_id"],
        "receipt": receipt,
    }
    if len(_canonical(unsigned)) > _MAX_RECORD:
        raise BuildHostEvidenceError("HOST_EVIDENCE_OVERSIZED")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            _b64(envelope["signature"], 64), _canonical(unsigned)
        )
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise BuildHostEvidenceError("HOST_EVIDENCE_SIGNATURE_INVALID") from exc
    return {
        "signature_verified": True,
        "build_identity_verified": True,
        "task_id": receipt["task_id"],
        "attempt": receipt["attempt"],
        "fencing_token": receipt["fencing_token"],
        "source_commit": receipt["source_commit"],
        "issued_at": receipt["issued_at"],
        "expires_at": receipt["expires_at"],
        "evidence_digest": receipt["evidence_digest"],
        "parent_ack_digest": receipt["parent_ack_digest"],
        "cleanup_authorized": False,
    }


def read_root_trust_anchor(path: Path = Path("/etc/herdr/build-lifecycle-trust.json")) -> tuple[str, bytes]:
    """Read through existing root-owned no-follow protection, not user paths."""
    data = read_protected(path, owner=0, limit=4096)
    try:
        root = _strict_json(data)
    except (ValueError, UnicodeError) as exc:
        raise BuildHostEvidenceError("HOST_EVIDENCE_TRUST_ANCHOR_INVALID") from exc
    if type(root) is not dict or set(root) != {
        "schema_version", "algorithm", "key_id", "public_key_b64"
    } or root["schema_version"] != _TRUST_SCHEMA or root["algorithm"] != "ed25519":
        raise BuildHostEvidenceError("HOST_EVIDENCE_TRUST_ANCHOR_INVALID")
    key_id = root["key_id"]
    if not isinstance(key_id, str) or not _KEY.fullmatch(key_id):
        raise BuildHostEvidenceError("HOST_EVIDENCE_TRUST_ANCHOR_INVALID")
    return key_id, _b64(root["public_key_b64"], 32)


def read_root_envelope(path: Path) -> dict[str, Any]:
    """A receipt must be in a separately root-controlled, read-only tree."""
    body = read_protected(path, owner=0, limit=_MAX_RECORD)
    try:
        value = _strict_json(body)
    except (ValueError, UnicodeError) as exc:
        raise BuildHostEvidenceError("HOST_EVIDENCE_ENVELOPE_INVALID") from exc
    if type(value) is not dict:
        raise BuildHostEvidenceError("HOST_EVIDENCE_ENVELOPE_INVALID")
    return value


def _normalized_root_text(path: Path) -> str:
    """Collapse a leading POSIX double slash so kernel paths compare equal.

    POSIX permits exactly two leading slashes and ``Path`` preserves them, while
    /proc links and mountinfo use a single leading slash.  An accepted root
    spelled ``//x`` would otherwise silently suppress mount and process
    observations for ``/x``.  Normalization keeps the read-only evidence correct
    and changes nothing about what is authorized (nothing).
    """
    text = str(path)
    if text.startswith("//"):
        return "/" + text.lstrip("/")
    return text


def inspect_mount_boundary(path: Path, *, mountinfo: str | None = None) -> dict[str, Any]:
    """Detect known mount boundaries; never assert mount absence authority.

    Uses parent host /proc/self/mountinfo only, not other process namespaces.
    A full privileged mount namespace comparison is still required.
    """
    if mountinfo is None:
        try:
            with Path("/proc/self/mountinfo").open("rb") as stream:
                data = stream.read(2_097_153)
            if len(data) > 2_097_152:
                return {"state": "UNKNOWN", "matches": [], "cleanup_authorized": False}
            mountinfo = data.decode("utf-8")
        except (OSError, UnicodeError):
            return {"state": "UNKNOWN", "matches": [], "cleanup_authorized": False}
    if type(mountinfo) is not str or len(mountinfo) > 2_097_152:
        return {"state": "UNKNOWN", "matches": [], "cleanup_authorized": False}
    path_text = _normalized_root_text(path)
    matches = []

    def unescape_mountpoint(value: str) -> str:
        return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)

    for line in mountinfo.splitlines():
        prefix, sep, _suffix = line.partition(" - ")
        fields = prefix.split(" ")
        if not sep or len(fields) < 6 or any(not part for part in fields[:6]):
            return {"state": "UNKNOWN", "matches": [], "cleanup_authorized": False}
        point = unescape_mountpoint(fields[4])
        if point == path_text or point.startswith(path_text + "/"):
            matches.append(point)
    return {
        "state": "MOUNT_FOUND" if matches else "NO_MOUNT_IN_OWN_NAMESPACE_ONLY",
        "matches": matches[:64],
        "cleanup_authorized": False,
    }


def inspect_process_references(
    path: Path, *, proc: Path = Path("/proc"),
    max_pids: int = 2048, max_fds: int = 256,
) -> dict[str, Any]:
    """Best-effort read-only /proc owner references; NEVER an absence proof.

    Only a privileged host with complete PID/mount namespace visibility can
    claim that a build is inactive. An inaccessible fd, cwd or PID races to
    UNKNOWN, and even a scan with no matches is scoped to the *current*
    namespace/instant only (not a lease/fencing or future-use assertion).
    """
    if (type(max_pids) is not int or not 1 <= max_pids <= 16384
            or type(max_fds) is not int or not 1 <= max_fds <= 4096):
        raise BuildHostEvidenceError("PROCESS_SCAN_BOUNDS_INVALID")
    base = _normalized_root_text(path)
    references = []
    incomplete = False
    try:
        entries = []
        with os.scandir(proc) as listing:
            for entry in listing:
                if not entry.name.isdecimal():
                    continue
                if len(entries) >= max_pids:
                    incomplete = True
                    break
                entries.append(entry.name)
    except OSError:
        return {
            "state": "UNKNOWN", "references": [],
            "incomplete": True, "cleanup_authorized": False,
        }
    entries.sort(key=int)

    def hit(value: str) -> bool:
        # A deleted cwd/fd may still hold blocks; retain its path observation.
        value = value.removesuffix(" (deleted)")
        return value == base or value.startswith(base + "/")

    for pid in entries:
        directory = proc / pid
        observed = False
        for field in ("cwd", "root"):
            try:
                target = os.readlink(directory / field)
            except FileNotFoundError:
                incomplete = True
                continue
            except (OSError, PermissionError):
                incomplete = True
                continue
            if hit(target):
                if len(references) < 64:
                    references.append({"pid": int(pid), "via": field})
                observed = True
        fd_dir = directory / "fd"
        try:
            fds = []
            with os.scandir(fd_dir) as fd_listing:
                for item in fd_listing:
                    if len(fds) >= max_fds:
                        incomplete = True
                        break
                    fds.append(item.name)
        except OSError:
            incomplete = True
            continue
        fds.sort()
        for fd in fds:
            try:
                target = os.readlink(fd_dir / fd)
            except OSError:
                incomplete = True
                continue
            if hit(target):
                if len(references) < 64:
                    references.append({"pid": int(pid), "via": "fd"})
                observed = True
                break
        if len(references) >= 64:
            incomplete = True
            break
    return {
        "state": ("REFERENCES_OBSERVED" if references
                  else "UNKNOWN" if incomplete
                  else "NO_REFERENCE_IN_VISIBLE_NAMESPACE_ONLY"),
        "references": references,
        "incomplete": incomplete,
        "cleanup_authorized": False,
    }


def host_evidence_scan(
    root: Path,
    names: tuple[str, ...],
    *,
    trust_path: Path = Path("/etc/herdr/build-lifecycle-trust.json"),
    receipt_root: Path = Path("/etc/herdr/build-lifecycle-receipts"),
    max_entries: int = 20000,
    max_depth: int = 20,
) -> dict[str, Any]:
    """Observe build inventory + cryptographic root receipts, without cleanup.

    Missing trust/receipts are expected for current RC6; still report all
    candidates as blocked without constructing a test approval.
    """
    report = inventory(root, names, max_entries=max_entries, max_depth=max_depth)
    try:
        key_id, public_key = read_root_trust_anchor(trust_path)
    except (OSError, ValueError, RuntimeError):
        key_id, public_key = None, None
    for row in report["candidates"]:
        row["host_evidence_state"] = "ROOT_EVIDENCE_UNAVAILABLE"
        row["host_evidence"] = None
        row["mount_observation"] = inspect_mount_boundary(Path(row["path"]))
        row["process_observation"] = inspect_process_references(Path(row["path"]))
        row["lease_fencing_observation"] = "UNKNOWN_NO_LIVE_HOST_AUTHORITY"
        row["parent_ack_observation"] = "UNKNOWN_NO_LIVE_HOST_AUTHORITY"
        if row["mount_observation"]["state"] == "MOUNT_FOUND":
            row["blockers"].append("ACTIVE_MOUNT_OBSERVED")
        if row["process_observation"]["state"] == "REFERENCES_OBSERVED":
            row["blockers"].append("PROCESS_REFERENCE_OBSERVED")
        elif row["process_observation"]["state"] == "UNKNOWN":
            row["blockers"].append("PROCESS_VISIBILITY_INCOMPLETE")
        if key_id is None:
            row["blockers"].append("TRUSTED_ROOT_EVIDENCE_UNAVAILABLE")
            continue
        name = row["name"] + ".json"
        try:
            envelope = read_root_envelope(receipt_root / name)
            result = validate_receipt(
                envelope, public_key=public_key, expected_key_id=key_id,
                expected_build_id=row["name"],
                expected_device=row["root_device"],
                expected_inode=row["root_inode"],
                expected_owner_uid=row["owner_uid"],
            )
        except (OSError, ValueError, RuntimeError):
            row["host_evidence_state"] = "ROOT_EVIDENCE_INVALID_OR_UNAVAILABLE"
            row["blockers"].append("HOST_EVIDENCE_NOT_VERIFIED")
            continue
        row["host_evidence_state"] = "HISTORICAL_SIGNATURE_VALID_ONLY"
        row["host_evidence"] = result
        row["blockers"].append("RUNTIME_HOST_REVALIDATION_REQUIRED")
        # Historical receipt cannot authorize deletion, even when signed.
        row["state"] = "BLOCKED_REVIEW"
        row["cleanup_authorized"] = False
        row["can_delete"] = False
    report["schema_version"] = "herdr-build-host-evidence-observation-v1"
    report["live_authority_accepted"] = False
    report["cleanup_authorized"] = False
    report["deletion_performed"] = False
    return report
