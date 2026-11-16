"""Read-only, bounded scratch build registry inventory for Herdr issue #126.

NO deletion, no quarantine, no lease/authority publication. A candidate is
NEVER automatically eligible for cleanup: the host-owned authority, live
lease/fencing and durable evidence must be reviewed separately.

This scans only explicit direct children of a supplied operator-chosen root.
Directory FDs, O_NOFOLLOW and stat identity checks prevent symlink traversal.
A race, mount boundary, parse failure or traversal limit is fail-closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

_ALLOWED_NAME = re.compile(r"^(?:herdr-hermes-build|hermes-security-lock|herdr-build)-[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_MANIFEST = "herdr-build-manifest.json"
_MAX_MANIFEST = 65536


class BuildInventoryError(ValueError):
    """Invalid root, entry or requested boundary. No partial approval."""


def _identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return info.st_dev, info.st_ino, info.st_uid, info.st_mode, info.st_ctime_ns


def _open_dir(path: Path) -> int:
    if not path.is_absolute() or ".." in path.parts or not path.parts[1:]:
        raise BuildInventoryError("ABSOLUTE_NO_SYMLINK_ROOT_REQUIRED")
    # Walk each ancestor using a held directory FD. O_NOFOLLOW on the final
    # path alone would otherwise permit symlinked *parent* components.
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for component in path.parts[1:]:
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=fd,
                )
            except OSError as exc:
                raise BuildInventoryError("ABSOLUTE_NO_SYMLINK_ROOT_REQUIRED") from exc
            os.close(fd)
            fd = next_fd
        info = os.fstat(fd)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o022):
            raise BuildInventoryError("ROOT_OWNER_OR_MODE_UNSAFE")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_manifest(fd: int, expected_name: str) -> tuple[dict[str, Any] | None, str]:
    try:
        handle = os.open(
            _MANIFEST, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=fd,
        )
    except FileNotFoundError:
        return None, "NOT_REGISTERED_LEGACY_BUILD"
    except OSError:
        return None, "MANIFEST_OPEN_DENIED"
    try:
        info = os.fstat(handle)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_uid != os.getuid() or not 0 < info.st_size <= _MAX_MANIFEST):
            return None, "MANIFEST_UNSAFE"
        raw = os.read(handle, info.st_size + 1)
        if (len(raw) != info.st_size or _identity(os.fstat(handle)) != _identity(info)):
            return None, "MANIFEST_CHANGED"
        try:
            manifest = json.loads(raw)
        except (ValueError, UnicodeError):
            return None, "MANIFEST_INVALID"
        if (type(manifest) is not dict or manifest.get("schema_version") != 1
                or manifest.get("build_id") != expected_name
                or type(manifest.get("source_commit")) is not str
                or not re.fullmatch(r"[0-9a-f]{40}", manifest["source_commit"])):
            return None, "MANIFEST_INVALID"
        # Never accept an agent-supplied manifest as cleanup authorization.
        return {
            "build_id": manifest["build_id"],
            "source_commit": manifest["source_commit"],
            "declared_state": str(manifest.get("state", "UNKNOWN"))[:48],
        }, "UNTRUSTED_DECLARATION_ONLY"
    finally:
        os.close(handle)


@dataclass
class _Bounds:
    max_entries: int
    max_depth: int
    count: int = 0
    allocated_bytes: int = 0
    regular_files: int = 0
    directories: int = 0
    symlinks: int = 0
    limits_hit: bool = False
    boundary_changes: int = 0
    unreadable: int = 0
    hardlinked_files: int = 0


def _walk(fd: int, root_dev: int, state: _Bounds, depth: int,
          seen: set[tuple[int, int]]) -> None:
    """Best-effort bounded measurement only, never an integrity grant."""
    if depth > state.max_depth:
        state.limits_hit = True
        return
    try:
        rows = os.scandir(fd)
        with rows as entries:
            for item in entries:
                if state.count >= state.max_entries:
                    state.limits_hit = True
                    return
                state.count += 1
                try:
                    info = os.stat(item.name, dir_fd=fd, follow_symlinks=False)
                except OSError:
                    state.unreadable += 1
                    continue
                if info.st_dev != root_dev:
                    state.boundary_changes += 1
                    continue
                token = info.st_dev, info.st_ino
                if token in seen:
                    continue
                seen.add(token)
                state.allocated_bytes += info.st_blocks * 512
                if stat.S_ISLNK(info.st_mode):
                    state.symlinks += 1
                    continue
                if stat.S_ISREG(info.st_mode):
                    state.regular_files += 1
                    if info.st_nlink > 1:
                        state.hardlinked_files += 1
                elif stat.S_ISDIR(info.st_mode):
                    state.directories += 1
                    if depth >= state.max_depth:
                        state.limits_hit = True
                        continue
                    try:
                        child = os.open(item.name, os.O_RDONLY | os.O_DIRECTORY
                                        | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
                    except OSError:
                        state.unreadable += 1
                        continue
                    try:
                        if _identity(os.fstat(child)) != _identity(info):
                            state.boundary_changes += 1
                            continue
                        _walk(child, root_dev, state, depth + 1, seen)
                    finally:
                        os.close(child)
                else:
                    state.boundary_changes += 1
    except OSError:
        state.unreadable += 1


def scan_one(rootfd: int, root: Path, name: str,
             *, max_entries: int = 20000, max_depth: int = 20) -> dict[str, Any]:
    if not _ALLOWED_NAME.fullmatch(name) or name in (".", "..") or "/" in name:
        raise BuildInventoryError("CANDIDATE_NAME_NOT_ALLOWED")
    if type(max_entries) is not int or not 1 <= max_entries <= 500000:
        raise BuildInventoryError("INVALID_MAX_ENTRIES")
    if type(max_depth) is not int or not 1 <= max_depth <= 64:
        raise BuildInventoryError("INVALID_MAX_DEPTH")
    try:
        expected = os.stat(name, dir_fd=rootfd, follow_symlinks=False)
    except FileNotFoundError:
        raise BuildInventoryError("CANDIDATE_MISSING")
    if not stat.S_ISDIR(expected.st_mode) or expected.st_uid != os.getuid():
        raise BuildInventoryError("CANDIDATE_OWNER_OR_TYPE_UNSAFE")
    if expected.st_mode & 0o022:
        raise BuildInventoryError("CANDIDATE_WRITABLE_BY_OTHER")
    try:
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                     dir_fd=rootfd)
    except OSError as exc:
        raise BuildInventoryError("CANDIDATE_OPEN_DENIED") from exc
    try:
        if _identity(os.fstat(fd)) != _identity(expected):
            raise BuildInventoryError("CANDIDATE_IDENTITY_CHANGED")
        manifest, manifest_status = _read_manifest(fd, name)
        count = _Bounds(max_entries, max_depth, allocated_bytes=expected.st_blocks * 512,
                        directories=1)
        seen = {(expected.st_dev, expected.st_ino)}
        _walk(fd, expected.st_dev, count, 0, seen)
        changed = _identity(os.fstat(fd)) != _identity(expected)
        if changed:
            count.boundary_changes += 1
        blockers = ["UNVERIFIED_EVIDENCE", "LIVE_LEASE_AND_FENCING_UNKNOWN",
                    "ACTIVE_PROCESS_AND_OPEN_FD_UNKNOWN",
                    "PARENT_ACK_AND_RECOVERY_UNKNOWN", "NO_CLEANUP_AUTHORITY"]
        if manifest_status != "UNTRUSTED_DECLARATION_ONLY":
            blockers.append(manifest_status)
        else:
            blockers.append("MANIFEST_NOT_HOST_ATTESTED")
        if count.limits_hit:
            blockers.append("TRAVERSAL_INCOMPLETE")
        if count.boundary_changes:
            blockers.append("FILESYSTEM_OR_IDENTITY_BOUNDARY_UNCERTAIN")
        if count.symlinks:
            blockers.append("SYMLINKS_PRESENT")
        if count.unreadable:
            blockers.append("UNREADABLE_ENTRIES")
        if count.hardlinked_files:
            blockers.append("HARDLINKS_PRESENT")
        # Only a measurement: even a complete scan is NOT a deletion permit.
        return {
            "name": name,
            "path": str(root / name),
            "owner_uid": expected.st_uid,
            "root_device": expected.st_dev,
            "root_inode": expected.st_ino,
            "allocated_bytes_observed": count.allocated_bytes,
            "measurement_complete": not (count.limits_hit or count.unreadable
                                         or count.boundary_changes),
            "entries_observed": count.count,
            "regular_files_observed": count.regular_files,
            "symlinks_observed": count.symlinks,
            "manifest_status": manifest_status,
            "manifest": manifest,
            "state": "BLOCKED_REVIEW",
            "cleanup_authorized": False,
            "can_delete": False,
            "blockers": blockers,
        }
    finally:
        os.close(fd)


def inventory(root: Path, names: tuple[str, ...], *,
              max_entries: int = 20000, max_depth: int = 20) -> dict[str, Any]:
    """Read-only explicit-target inventory, never enumerate unknown project roots."""
    if not isinstance(names, tuple) or not 1 <= len(names) <= 32 or len(set(names)) != len(names):
        raise BuildInventoryError("BOUNDED_UNIQUE_CANDIDATES_REQUIRED")
    root = Path(root)
    fd = _open_dir(root)
    try:
        before = _identity(os.fstat(fd))
        candidates = [scan_one(fd, root, n, max_entries=max_entries,
                               max_depth=max_depth) for n in names]
        if _identity(os.fstat(fd)) != before:
            raise BuildInventoryError("ROOT_IDENTITY_CHANGED")
    finally:
        os.close(fd)
    return {
        "schema_version": "herdr-build-lifecycle-observation-v1",
        "mode": "READ_ONLY",
        "root": str(root),
        "candidates": candidates,
        "candidate_count": len(candidates),
        "total_observed_bytes_not_reclaimable_estimate": sum(
            row["allocated_bytes_observed"] for row in candidates),
        "deletion_performed": False,
        "cleanup_authorized": False,
        "model_calls": 0,
        "note": "Observed bytes may be partial and must never authorize deletion.",
    }
