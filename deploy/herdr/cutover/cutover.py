#!/usr/bin/env python3
"""One-step, fail-closed runtime cutover to an immutable Herdr release."""
from __future__ import annotations

from argparse import ArgumentParser
from contextlib import contextmanager
from functools import wraps
import importlib
import importlib.machinery
import hashlib
import base64
import json
import os
import signal
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import types

try:
    import fcntl
except ImportError:  # pragma: no cover - production cutover is Linux-only
    fcntl = None

try:
    import grp
    import pwd
except ImportError:  # pragma: no cover - production cutover is Linux-only
    grp = None
    pwd = None

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from herdr.release import (  # noqa: E402
    CONSUMERS,
    ReleaseError,
    canonical_json,
    consumer_digest,
    extract_archive,
    sha256,
    verify_archive,
    verify_tree,
)
from deploy.herdr.cutover.systemd_authority import SystemdAuthority, verify_release_runtime  # noqa: E402
from deploy.herdr.cutover import transaction_contract as transactions  # noqa: E402


HOST = "quantlab-staging-01"
LEGACY = Path("/opt/agent-platform/release")
RELEASES = Path("/opt/herdr/releases")
CURRENT = Path("/opt/herdr/current")
CONSUMER_DIR = Path("/etc/herdr/consumers")
STATE_DIR = Path("/var/lib/herdr/deployments")
INCOMING_DIR = Path("/var/lib/herdr/incoming")
PUBLIC_STATE = Path("/var/lib/agent-platform-herdr/deployed-release.json")
IMMUTABLE_PREFLIGHT_ROOTS = (
    Path("/opt/herdr/releases"),
    Path("/var/lib/herdr/incoming"),
)
NGINX_ROUTE = Path("/etc/agent-platform/nginx-server.conf")
NGINX_LOCATION_COMMON = Path("/etc/agent-platform/nginx-location-common.conf")
UNIT_DIR = Path("/etc/systemd/system")
DEPLOYMENT_LOCK = Path("/run/herdr/cutover.lock")
WATCHDOG_LOCK = Path("/home/agentops/.local/state/agent-stack/watchdog.lock")
WATCHDOG_STABILITY_SECONDS = 6
UNITS = (
    "agent-platform-web.service",
    "agent-platform-export.service",
    "agent-platform-herdr.service",
    "agent-platform-export.timer",
    "agent-platform-herdr.timer",
    "agent-stack-watchdog.service",
)

# One-time bridge for the deployed RC8 marker, which predates
# payload_manifest_sha256 in deployed-release.json. These hashes are reviewed
# immutable source evidence from commit d58283bc4bf98490bb96bd9bffd58b293b451061.
# Once staging is on a marker that carries payload_manifest_sha256, upgrades use
# the generic manifest-bound path below.
RECOVERY_RC8_TAG = "v0.3.0-rc.8"
RECOVERY_RC8_COMMIT = "d58283bc4bf98490bb96bd9bffd58b293b451061"
RECOVERY_TARGET_TAG = "v0.3.0-rc.12"
RECOVERY_TARGET_COMMIT = "1d524ff25d8b340cb638224effb0f445fb4e4e98"
RECOVERY_TARGET_CONFIG_SHA256 = (
    "3c7660874e437dd49dcbff83db20761fd595743c15ce3969a457d6f1de199ba9"
)
RECOVERY_TARGET_PAYLOAD_MANIFEST_SHA256 = (
    "b97aa3900ad642ee55433cdb09b58fb99bb435360427a63eb1f68d9baa76938a"
)
RECOVERY_TARGET_ARCHIVE_SHA256 = (
    "0f4fa8a24de0c367008532acb6319487d0da1948f458ee8d036910720ecb7b0f"
)
SNAPSHOT = Path("/var/lib/agent-platform/snapshot.json")
BRIDGE = Path("/var/lib/agent-platform-herdr/herdr.json")
WEB_CONFIG = Path("/etc/agent-platform/web.json")
HERDR_SOCKET = Path("/home/agentops/.config/herdr/herdr.sock")
RECOVERY_ROUTER_DATABASES = {
    "majak": Path("/home/agentops/.hermes/profiles/majak/model-router/router.db"),
    "quantlab": Path("/home/agentops/.hermes/profiles/quantlab/model-router/router.db"),
}
RECOVERY_FAIL_CLOSED_PUBLIC_STATUSES = frozenset({"401", "502", "503"})
RECOVERY_ROUTER_GROUP_COUNT_SQL = """SELECT count(*) FROM (
SELECT task_id,actual_model,provider FROM
(SELECT id,task_id,actual_model,provider FROM requests ORDER BY id DESC LIMIT 1000)
GROUP BY task_id,actual_model,provider LIMIT 51)"""


BOOTSTRAP_VERSIONED_UNIT_HASHES = {
    (
        "v0.3.0-rc.8",
        "d58283bc4bf98490bb96bd9bffd58b293b451061",
    ): {
        "agent-platform-web.service":
            "c5a834ae268d02f5b27938f90c3d9bf766118399f65ae07d9f3016a530460e5e",
        "agent-platform-export.service":
            "f674e5d42bea703c48d1dd7156bff56d07d21f314c8379f6a9255114c946e608",
        "agent-platform-herdr.service":
            "d02e097c200e4c28290b24029ec7cbe6a73aec2a46635df86929c1b4e266d4da",
        "agent-platform-export.timer":
            "e568c8d2a5fb27f9e968868952d296191e3be30962c0dba1fc415c35c994cf04",
        "agent-platform-herdr.timer":
            "875c7512d5504a0f10cd2b975cffc5ff8116529cc8d147d37c5fee8c83cf8e28",
        "agent-stack-watchdog.service":
            "4263cadfa131fe3e117989751d3966058ab74748b82ca28683a99d5e7c61a413",
    },
}


def need(value: bool, message: str) -> None:
    if not value:
        raise ReleaseError(message)


@contextmanager
def deployment_lock():
    """Serialize every cutover from authorization through rollback."""
    need(fcntl is not None, "deployment_lock_unavailable")
    runtime_parent = DEPLOYMENT_LOCK.parent.parent
    parent_info = os.lstat(runtime_parent)
    need(
        stat.S_ISDIR(parent_info.st_mode)
        and parent_info.st_uid == 0
        and not stat.S_IMODE(parent_info.st_mode) & 0o022,
        "unsafe_deployment_lock_parent",
    )
    try:
        os.mkdir(DEPLOYMENT_LOCK.parent, 0o700)
    except FileExistsError:
        pass
    directory_info = os.lstat(DEPLOYMENT_LOCK.parent)
    need(
        stat.S_ISDIR(directory_info.st_mode)
        and directory_info.st_uid == 0
        and not stat.S_IMODE(directory_info.st_mode) & 0o077,
        "unsafe_deployment_lock_directory",
    )
    flags = os.O_CREAT | os.O_RDWR
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(DEPLOYMENT_LOCK, flags, 0o600)
    locked = False
    try:
        info = os.fstat(descriptor)
        need(
            stat.S_ISREG(info.st_mode)
            and info.st_uid == 0
            and not stat.S_IMODE(info.st_mode) & 0o077,
            "unsafe_deployment_lock",
        )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ReleaseError("deployment_in_progress") from error
        locked = True
        yield
    finally:
        if locked:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def serialized_deployment(operation):
    @wraps(operation)
    def locked_operation(*args, **kwargs):
        with deployment_lock():
            return operation(*args, **kwargs)

    return locked_operation


def digest_file(path: Path) -> str:
    need(path.is_file() and not path.is_symlink(), f"unsafe_file:{path}")
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and 0 <= before.st_size <= 64*1024**2, "unsafe_digest_file")
        total = 0
        while chunk := stream.read(min(65536, before.st_size + 1 - total)):
            total += len(chunk)
            need(total <= before.st_size, "digest_file_grew")
            digest.update(chunk)
        need(total == before.st_size and transactions.stamp(os.fstat(stream.fileno()))
             == transactions.stamp(before), "digest_file_changed")
    return digest.hexdigest()


def pin_archive(source: Path) -> Path:
    """Copy an operator-owned archive through a pinned fd into root-only storage."""
    info = os.lstat(source)
    sudo_uid = int(os.environ.get("SUDO_UID", "-1"))
    need(stat.S_ISREG(info.st_mode) and not info.st_mode & 0o022
         and info.st_nlink == 1 and info.st_uid in (0, sudo_uid)
         and 0 < info.st_size <= 64 * 1024 * 1024,
         "unsafe_release_archive")
    base = INCOMING_DIR.parent
    base_existed = base.exists()
    INCOMING_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    need(not INCOMING_DIR.parent.is_symlink() and not INCOMING_DIR.is_symlink(),
         "incoming_directory_is_symlink")
    if not base_existed:
        os.chown(base, 0, 0)
        os.chmod(base, 0o700)
    for directory in (base, INCOMING_DIR):
        directory_info = directory.stat()
        need(directory_info.st_uid == 0 and not directory_info.st_mode & 0o077,
             "unsafe_incoming_directory")
    target = INCOMING_DIR / f"release-{os.getpid()}-{time.time_ns()}.tar.gz"
    source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        pinned = os.fstat(source_fd)
        need(transactions.stamp(pinned) == transactions.stamp(info), "release_archive_changed")
        with os.fdopen(source_fd, "rb", closefd=False) as input_stream, \
             os.fdopen(target_fd, "wb", closefd=False) as output_stream:
            remaining = info.st_size
            while remaining:
                chunk = input_stream.read(min(1024 * 1024, remaining))
                need(bool(chunk), "release_archive_short_read")
                output_stream.write(chunk)
                remaining -= len(chunk)
            need(not input_stream.read(1), "release_archive_grew")
            output_stream.flush()
            os.fsync(output_stream.fileno())
        need(transactions.stamp(os.fstat(source_fd)) == transactions.stamp(info)
             and transactions.stamp(os.lstat(source)) == transactions.stamp(info),
             "release_archive_changed")
        os.chown(target, 0, 0, follow_symlinks=False)
        os.chmod(target, 0o400, follow_symlinks=False)
        need(target.stat().st_size == info.st_size, "pinned_archive_size_mismatch")
        return target
    except BaseException:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(source_fd)
        os.close(target_fd)


def expected_hashes(
    path: Path,
    *,
    require_location_common: bool = False,
) -> dict[Path, str]:
    values: dict[Path, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        digest, separator, filename = line.partition("  ")
        target = Path(filename)
        need(bool(separator) and len(digest) == 64 and target.is_absolute()
             and target not in values, "invalid_expected_hash_manifest")
        values[target] = digest
    expected = {*(UNIT_DIR / name for name in UNITS), NGINX_ROUTE}
    if NGINX_LOCATION_COMMON in values:
        expected.add(NGINX_LOCATION_COMMON)
    need(set(values) == expected, "incomplete_expected_hash_manifest")
    need(
        not require_location_common or NGINX_LOCATION_COMMON in values,
        "auth_include_missing_from_expected_hash_manifest",
    )
    return values


def root_owned_readonly(path: Path) -> bool:
    info = path.stat()
    return info.st_uid == 0 and not info.st_mode & 0o022


def immutable_preflight_controller() -> bool:
    """Require root execution from an immutable, approved release tree."""
    if os.geteuid() != 0:
        return False
    try:
        root = ROOT.resolve(strict=True)
    except OSError:
        return False
    if not any(root.parent == prefix for prefix in IMMUTABLE_PREFLIGHT_ROOTS):
        return False
    try:
        current = root
        while current != Path("/"):
            if current.is_symlink() or not root_owned_readonly(current):
                return False
            current = current.parent
    except OSError:
        return False
    return True


def read_trusted_public_state(path: Path) -> dict[str, object]:
    """Read the root-owned marker without a check/use race."""
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ReleaseError("current_release_public_state_unreadable") from exc
    try:
        before = os.fstat(fd)
        need(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and before.st_uid == 0
            and not before.st_mode & 0o022
            and 0 < before.st_size <= 4096,
            "unsafe_current_release_public_state",
        )
        data = bytearray()
        while len(data) < before.st_size:
            chunk = os.read(fd, min(4096, before.st_size - len(data)))
            if not chunk:
                raise ReleaseError("current_release_public_state_short_read")
            data.extend(chunk)
        extra = os.read(fd, 1)
        after = os.fstat(fd)
        need(
            not extra
            and (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_uid,
                before.st_gid,
                before.st_nlink,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            == (
                after.st_dev,
                after.st_ino,
                after.st_mode,
                after.st_uid,
                after.st_gid,
                after.st_nlink,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ),
            "current_release_public_state_changed",
        )
    except ReleaseError:
        raise
    except OSError as exc:
        raise ReleaseError("current_release_public_state_unreadable") from exc
    finally:
        os.close(fd)
    try:
        value = json.loads(bytes(data).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError("current_release_public_state_invalid") from exc
    need(type(value) is dict, "current_release_public_state_invalid")
    return value


def current_release_unit_hashes() -> dict[Path, str]:
    """Return unit hashes independently bound to the deployed release identity."""
    if not CURRENT.exists() and not CURRENT.is_symlink():
        return {}
    need(CURRENT.is_symlink(), "current_is_not_symlink")
    current = CURRENT.resolve(strict=True)
    if current == LEGACY:
        return {}
    need(current.parent == RELEASES, "unexpected_current_release")
    need(root_owned_readonly(current), "unsafe_current_release")

    release_path = current / "RELEASE.json"
    manifest_path = current / "MANIFEST.sha256"
    for path, code in (
        (release_path, "unsafe_current_release_metadata"),
        (manifest_path, "unsafe_current_release_manifest"),
    ):
        need(path.is_file() and not path.is_symlink(), code)
        need(root_owned_readonly(path), code)

    try:
        document = json.loads(release_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError("current_release_metadata_invalid") from exc
    need(type(document) is dict
         and isinstance(document.get("tag"), str)
         and isinstance(document.get("commit"), str)
         and len(document["commit"]) == 40
         and current.name == f"{document['tag']}-{document['commit'][:12]}",
         "current_release_identity_mismatch")

    identity = (document["tag"], document["commit"])

    # RC8 predates independently persisted manifest evidence and its public
    # deployed marker may not be readable by the unprivileged operator running
    # preflight. Permit this one exact bootstrap identity only through reviewed
    # immutable unit hashes embedded in the incoming release. No other release
    # may use this path.
    baseline = BOOTSTRAP_VERSIONED_UNIT_HASHES.get(identity)
    if baseline is not None:
        need(set(baseline) == set(UNITS), "invalid_bootstrap_unit_baseline")
        hashes: dict[Path, str] = {}
        for name in UNITS:
            source = current / "deploy" / "agent_platform" / "production" / f"{name}.in"
            need(source.is_file() and not source.is_symlink(),
                 f"current_release_unit_missing:{name}")
            need(root_owned_readonly(source),
                 f"unsafe_current_release_unit:{name}")
            expected = baseline[name]
            need(digest_file(source) == expected,
                 f"current_release_unit_baseline_mismatch:{name}")
            installed = UNIT_DIR / name
            need(installed.is_file() and not installed.is_symlink(),
                 f"runtime_unit_missing:{name}")
            need(digest_file(installed) == expected,
                 f"runtime_unit_bootstrap_mismatch:{name}")
            hashes[installed] = expected
        return hashes

    need(PUBLIC_STATE.is_file() and not PUBLIC_STATE.is_symlink(),
         "current_release_public_state_missing")
    public = read_trusted_public_state(PUBLIC_STATE)
    need(type(public) is dict
         and public.get("version") == 1
         and public.get("tag") == document["tag"]
         and public.get("commit") == document["commit"]
         and public.get("config_sha256") == document.get("config_contract_sha256"),
         "current_release_public_state_mismatch")

    evidence_digest = public.get("payload_manifest_sha256")
    need(isinstance(evidence_digest, str)
         and len(evidence_digest) == 64
         and all(ch in "0123456789abcdef" for ch in evidence_digest)
         and document.get("payload_manifest_sha256") == evidence_digest,
         "current_release_manifest_evidence_mismatch")

    manifest_data = manifest_path.read_bytes()
    need(sha256(manifest_data) == evidence_digest,
         "current_release_manifest_mismatch")
    try:
        manifest_lines = manifest_data.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ReleaseError("current_release_manifest_invalid") from exc

    bound: dict[str, str] = {}
    for line in manifest_lines:
        digest, separator, name = line.partition("  ")
        need(bool(separator)
             and len(digest) == 64
             and all(ch in "0123456789abcdef" for ch in digest)
             and name not in bound,
             "current_release_manifest_invalid")
        bound[name] = digest

    hashes: dict[Path, str] = {}
    for name in UNITS:
        relative = f"deploy/agent_platform/production/{name}.in"
        source = current / relative
        need(relative in bound, f"current_release_unit_unbound:{name}")
        need(source.is_file() and not source.is_symlink(),
             f"current_release_unit_missing:{name}")
        need(root_owned_readonly(source),
             f"unsafe_current_release_unit:{name}")
        need(digest_file(source) == bound[relative],
             f"current_release_unit_manifest_mismatch:{name}")
        hashes[UNIT_DIR / name] = bound[relative]
    return hashes

def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, check=check, capture_output=True, text=True,
                            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
    return result.stdout.strip()


def http_status(url: str) -> str:
    return run("/usr/bin/curl", "--silent", "--show-error", "--max-time", "10",
               "--output", "/dev/null", "--write-out", "%{http_code}", url)


def wait_http_status(url: str, expected: str, *, attempts: int = 10,
                     delay: float = 1.0) -> str:
    """Wait for an asynchronous service or proxy reload to converge."""
    need(attempts > 0 and len(expected) == 3 and expected.isdigit(),
         "invalid_http_status_wait")
    last = ""
    for attempt in range(attempts):
        try:
            last = http_status(url)
        except subprocess.SubprocessError:
            last = ""
        if last == expected:
            return last
        if attempt + 1 < attempts:
            time.sleep(delay)
    raise ReleaseError(f"http_status_timeout:{expected}:{last or 'error'}")


def atomic_write(path: Path, data: bytes, mode: int, uid: int = 0, gid: int = 0) -> None:
    need(path.is_absolute() and path.parent.is_dir() and not path.parent.is_symlink(),
         "unsafe_atomic_destination")
    temporary = path.parent / f".{path.name}.{os.getpid()}.{time.time_ns()}"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, uid, gid, follow_symlinks=False)
        os.chmod(temporary, mode, follow_symlinks=False)
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass



def snapshot_file(path: Path) -> tuple[bytes, int, int, int] | None:
    if not path.exists() and not path.is_symlink():
        return None
    maximum = transactions.MARKER_MAX if path == PUBLIC_STATE else transactions.FILE_MAX
    return transactions.bounded_read(path, maximum)


def restore_file(
    path: Path,
    snapshot: tuple[bytes, int, int, int] | None,
) -> None:
    if snapshot is None:
        if path.exists() or path.is_symlink():
            need(
                path.is_file() and not path.is_symlink(),
                f"unsafe_restore_destination:{path}",
            )
            path.unlink()
        return

    data, mode, uid, gid = snapshot
    atomic_write(path, data, mode, uid, gid)


def snapshot_units() -> dict[Path, tuple[bytes, int, int, int]]:
    snapshots = {}
    for name in UNITS:
        path = UNIT_DIR / name
        snapshot = snapshot_file(path)
        need(snapshot is not None, f"runtime_unit_missing:{name}")
        snapshots[path] = snapshot
    return snapshots


def restore_units(
    snapshots: dict[Path, tuple[bytes, int, int, int]],
) -> None:
    for path, snapshot in snapshots.items():
        restore_file(path, snapshot)
    run("/usr/bin/systemctl", "daemon-reload")


def snapshot_unit_hashes(
    snapshots: dict[Path, tuple[bytes, int, int, int]],
) -> dict[Path, str]:
    return {
        path: sha256(snapshot[0])
        for path, snapshot in snapshots.items()
    }


def atomic_symlink(target: Path, link: Path) -> None:
    need(target.is_absolute() and target.is_dir() and not target.is_symlink(),
         "invalid_symlink_target")
    need(link.is_absolute() and link.parent.is_dir() and not link.parent.is_symlink(),
         "invalid_symlink_destination")
    temporary = link.parent / f".{link.name}.{os.getpid()}.{time.time_ns()}"
    os.symlink(str(target), temporary)
    try:
        os.replace(temporary, link)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def compare_trees(candidate: Path, legacy: Path) -> dict[str, object]:
    prefixes = (
        "agent-stack/",
        "agent_platform_dashboard/",
        "deploy/agent_platform/production/",
    )
    candidate_files = {
        item.relative_to(candidate).as_posix(): sha256(item.read_bytes())
        for item in candidate.rglob("*") if item.is_file()
        and item.relative_to(candidate).as_posix().startswith(prefixes)
    }
    legacy_files = {
        item.relative_to(legacy).as_posix(): sha256(item.read_bytes())
        for item in legacy.rglob("*") if item.is_file()
        and item.relative_to(legacy).as_posix().startswith(prefixes)
    }
    shared = set(candidate_files) & set(legacy_files)
    missing = sorted(set(legacy_files) - set(candidate_files))
    need(not missing, "candidate_drops_legacy_runtime_files")
    return {
        "unchanged": sum(candidate_files[name] == legacy_files[name] for name in shared),
        "changed": sum(candidate_files[name] != legacy_files[name] for name in shared),
        "added": len(set(candidate_files) - set(legacy_files)),
        "removed": 0,
        "candidate_files": len(candidate_files),
        "legacy_files": len(legacy_files),
    }


def extract_candidate(archive: Path, destination: Path) -> Path:
    extract_archive(archive, destination)
    roots = list(destination.iterdir())
    need(len(roots) == 1 and roots[0].is_dir(), "invalid_release_archive_root")
    verify_tree(roots[0])
    return roots[0]


def verify_recovery_target(
    archive: Path,
    release: dict[str, object],
) -> None:
    """Authorize the one-time recovery only for the reviewed RC12 bytes."""
    need(
        digest_file(archive) == RECOVERY_TARGET_ARCHIVE_SHA256,
        "recovery_target_archive_mismatch",
    )
    need(
        release.get("tag") == RECOVERY_TARGET_TAG
        and release.get("commit") == RECOVERY_TARGET_COMMIT
        and release.get("config_contract_sha256")
        == RECOVERY_TARGET_CONFIG_SHA256
        and release.get("payload_manifest_sha256")
        == RECOVERY_TARGET_PAYLOAD_MANIFEST_SHA256,
        "recovery_target_identity_mismatch",
    )


def live_unix_socket(path: Path) -> bool:
    """Prove that an exact, non-symlink Unix socket has a live listener."""
    try:
        info = os.lstat(path)
        if path.is_symlink() or not stat.S_ISSOCK(info.st_mode):
            return False
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(2)
            client.connect(str(path))
        return True
    except (OSError, TimeoutError):
        return False


def recovery_router_group_counts() -> dict[str, int]:
    """Count at most 51 live groups without publishing identifiers or rows."""
    from agent_platform_dashboard import production_sources as sources

    counts = {}
    for profile, path in RECOVERY_ROUTER_DATABASES.items():
        with sources.readonly(
            str(path),
            "requests",
            sources.ROUTER_COLUMNS,
        ) as database:
            value = database.execute(
                RECOVERY_ROUTER_GROUP_COUNT_SQL
            ).fetchone()[0]
        need(
            type(value) is int and 0 <= value <= 51,
            f"invalid_recovery_router_count:{profile}",
        )
        counts[profile] = value
    return counts


def rc8_router_recovery_evidence(statuses: dict[str, str]) -> bool:
    """Recognize only the exact fail-closed RC8 router-overflow recovery state."""
    if not CURRENT.is_symlink():
        return False
    expected = RELEASES / f"{RECOVERY_RC8_TAG}-{RECOVERY_RC8_COMMIT[:12]}"
    if CURRENT.resolve(strict=True) != expected:
        return False
    if statuses.get("agent-platform-web.service") not in {"failed", "inactive"}:
        return False
    if statuses.get("agent-platform-export.timer") != "active":
        return False
    if statuses.get("agent-platform-herdr.timer") != "active":
        return False
    if statuses.get("agent-stack-watchdog.service") != "inactive":
        return False
    if not live_unix_socket(HERDR_SOCKET):
        return False
    try:
        info = os.lstat(SNAPSHOT)
        if not stat.S_ISREG(info.st_mode) or SNAPSHOT.is_symlink() or info.st_size > 131072:
            return False
        snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if type(snapshot) is not dict or snapshot.get("version") != 1:
        return False
    generated_at = snapshot.get("generated_at")
    if type(generated_at) not in (int, float) or type(generated_at) is bool:
        return False
    if not 0 <= time.time() - generated_at <= 90:
        return False
    sources = snapshot.get("sources")
    if type(sources) is not list:
        return False
    pairs = {
        (item.get("profile"), item.get("kind")): item
        for item in sources
        if type(item) is dict
    }
    for profile in ("majak", "quantlab"):
        router = pairs.get((profile, "router"), {})
        if not (
            router.get("status") == "unavailable"
            and router.get("reason") == "source_failed"
            and router.get("rows") == []
        ):
            return False
        herdr = pairs.get((profile, "herdr"), {})
        if not (
            herdr.get("status") == "available"
            and herdr.get("reason") == "ok"
            and type(herdr.get("rows")) is list
            and bool(herdr["rows"])
        ):
            return False
    release_source = pairs.get(("quantlab", "release"), {})
    if not (
        release_source.get("status") == "available"
        and release_source.get("reason") == "ok"
        and type(release_source.get("rows")) is list
        and len(release_source["rows"]) == 1
    ):
        return False
    row = release_source["rows"][0]
    if not (
        row.get("tag") == RECOVERY_RC8_TAG
        and row.get("commit") == RECOVERY_RC8_COMMIT
    ):
        return False
    try:
        counts = recovery_router_group_counts()
    except Exception:
        return False
    return counts == {"majak": 51, "quantlab": 51}


def recovery_mode_authorized(
    statuses: dict[str, str],
    allow_degraded_rc8: bool,
) -> bool:
    authorized = (
        allow_degraded_rc8
        and os.geteuid() == 0
        and rc8_router_recovery_evidence(statuses)
    )
    if authorized:
        need(
            watchdog_lock_available(),
            "recovery_watchdog_lock_held",
        )
    return authorized


def preflight(
    archive: Path,
    expected_legacy_commit: str,
    *,
    allow_degraded_rc8: bool = False,
) -> dict[str, object]:
    need(
        immutable_preflight_controller(),
        "preflight_root_required_or_controller_not_immutable",
    )
    need(not (STATE_DIR / "transaction.json").exists()
         and not (STATE_DIR / "transaction.json").is_symlink(),
         "unfinished_deployment_requires_operator_reconciliation")
    release = verify_archive(archive)
    need((ROOT / "RELEASE.json").is_file(), "cutover_tool_release_missing")
    controller_release = verify_tree(ROOT)
    if allow_degraded_rc8:
        verify_recovery_target(archive, release)
    else:
        need(controller_release == release, "cutover_tool_release_mismatch")
    need(socket.gethostname() == HOST, "wrong_host")
    need(LEGACY.is_dir() and not LEGACY.is_symlink(), "legacy_release_missing")
    legacy_commit = (LEGACY / "DEPLOYED_GIT_SHA").read_text(encoding="ascii").strip()
    need(legacy_commit == expected_legacy_commit, "legacy_commit_mismatch")
    dependency = release["external_dependency"]
    binary = LEGACY / "herdr"
    need(binary.stat().st_size == dependency["size"] and digest_file(binary) == dependency["sha256"],
         "external_binary_mismatch")
    manifest = ROOT / "deploy" / "herdr" / "cutover" / "legacy-quantlab-staging-01.sha256"
    previous_units = current_release_unit_hashes()
    for path, digest in expected_hashes(
        manifest,
        require_location_common=allow_degraded_rc8,
    ).items():
        if path.name.endswith((".service", ".timer")):
            candidate = ROOT / "deploy" / "agent_platform" / "production" / f"{path.name}.in"
            allowed = {digest, digest_file(candidate)}
            previous = previous_units.get(path)
            if previous:
                allowed.add(previous)
            need(digest_file(path) in allowed, f"unexpected_runtime_drift:{path}")
        else:
            need(root_owned_readonly(path), f"unsafe_runtime_file:{path}")
            need(digest_file(path) == digest, f"unexpected_runtime_drift:{path}")
    statuses = {unit: run("/usr/bin/systemctl", "is-active", unit, check=False) for unit in UNITS}
    recovery_mode = recovery_mode_authorized(
        statuses,
        allow_degraded_rc8,
    )
    if not recovery_mode:
        need(statuses["agent-platform-web.service"] in {"active", "failed", "inactive"}
             and statuses["agent-platform-export.timer"] == "active"
             and statuses["agent-platform-herdr.timer"] == "active"
             and statuses["agent-stack-watchdog.service"] == "active",
             "runtime_not_healthy")
    with tempfile.TemporaryDirectory(prefix="herdr-preflight-") as folder:
        candidate = extract_candidate(archive, Path(folder))
        if not allow_degraded_rc8:
            verify_release_runtime(candidate)
        comparison = compare_trees(candidate, LEGACY)
        allocation = sum(max(4096, ((p.lstat().st_size + 4095) // 4096) * 4096)
                         for p in (candidate, *candidate.rglob("*")))
    current = None
    if CURRENT.exists() or CURRENT.is_symlink():
        need(CURRENT.is_symlink(), "current_is_not_symlink")
        current = str(CURRENT.resolve(strict=True))
    if recovery_mode:
        direct_health = "unavailable"
        public_health = http_status("https://2.28.67.165/agent-platform/health")
        # The exact active Nginx route was verified above. It authenticates
        # before proxying, so an unauthenticated probe remains fail-closed with
        # 401 even while the unavailable upstream would yield 502/503 after
        # successful authentication.
        need(
            public_health in RECOVERY_FAIL_CLOSED_PUBLIC_STATUSES,
            "recovery_public_boundary_not_fail_closed",
        )
    else:
        try:
            direct_health = http_status("http://127.0.0.1:3010/agent-platform/health")
        except subprocess.CalledProcessError as error:
            need(statuses["agent-platform-web.service"] != "active"
                 and error.returncode == 7, "direct_health_probe_failed")
            direct_health = "000"
        public_health = http_status("https://2.28.67.165/agent-platform/health")
        if statuses["agent-platform-web.service"] == "active":
            need(direct_health == "401" and public_health == "401", "auth_boundary_regressed")
        else:
            # Only availability may be degraded. Immutable identity, marker,
            # unit, route, consumer and worker gates still apply.
            need(current is not None and Path(current).parent == RELEASES,
                 "degraded_previous_requires_versioned_release")
            previous_release = verify_tree(Path(current))
            assert_deployed_coherence(Path(current), previous_release)
            need(live_unix_socket(HERDR_SOCKET), "degraded_previous_bridge_socket_unavailable")
            assert_no_active_durable_worker()
            need(direct_health in {"000", "502", "503"}
                 and public_health in RECOVERY_FAIL_CLOSED_PUBLIC_STATUSES,
                 "degraded_previous_boundary_not_fail_closed")
    systemd_authority = capture_systemd_authority()
    report = {
        "status": "preflight_ok",
        "systemd_authority": systemd_authority,
        "release": release,
        "legacy_commit": legacy_commit,
        "legacy_release": str(LEGACY),
        "current": current,
        "runtime_diff": comparison,
        "candidate_allocation_bytes": allocation,
        "services": statuses,
        "direct_health": direct_health,
        "public_health": public_health,
        "public_root": http_status("https://2.28.67.165/"),
        "recovery_mode": "rc8_router_overflow" if recovery_mode else None,
        "baseline_health": "degraded" if statuses["agent-platform-web.service"] != "active" else "healthy",
    }
    report["transaction_contract"] = verify_transaction_preparation(
        Path(current) if current else LEGACY, report, archive, allocation)
    return report


def install_candidate(archive: Path, release: dict[str, object]) -> Path:
    RELEASES.mkdir(parents=True, exist_ok=True, mode=0o755)
    need(not RELEASES.is_symlink(), "release_directory_is_symlink")
    for directory in (RELEASES.parent, RELEASES):
        info = directory.stat()
        need(info.st_uid == 0 and not info.st_mode & 0o022, "unsafe_release_directory")
    target = RELEASES / f"{release['tag']}-{release['commit'][:12]}"
    if target.exists():
        need(verify_tree(target) == release, "existing_release_mismatch")
        return target
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=RELEASES))
    try:
        extracted = extract_candidate(archive, staging)
        for item in sorted([extracted, *extracted.rglob("*")], reverse=True):
            if item.is_dir():
                os.chown(item, 0, 0, follow_symlinks=False)
                item.chmod(0o555)
            else:
                os.chown(item, 0, 0, follow_symlinks=False)
                item.chmod(0o555 if os.access(item, os.X_OK) else 0o444)
        os.replace(extracted, target)
        return target
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def install_consumers(release_root: Path, expected_digest: str) -> str:
    CONSUMER_DIR.mkdir(parents=True, exist_ok=True, mode=0o755)
    need(not CONSUMER_DIR.parent.is_symlink() and not CONSUMER_DIR.is_symlink(),
         "consumer_directory_is_symlink")
    for directory in (CONSUMER_DIR.parent, CONSUMER_DIR):
        info = directory.stat()
        need(info.st_uid == 0 and not info.st_mode & 0o022, "unsafe_consumer_directory")
    installed: dict[str, bytes] = {}
    for consumer in CONSUMERS:
        name = f"{consumer}.yaml"
        data = (release_root / "configs" / "consumers" / name).read_bytes()
        destination = CONSUMER_DIR / name
        if destination.exists():
            need(destination.is_file() and not destination.is_symlink()
                 and destination.read_bytes() == data, f"consumer_config_drift:{consumer}")
        else:
            atomic_write(destination, data, 0o644)
        installed[name] = destination.read_bytes()
    digest = consumer_digest(installed)
    need(digest == expected_digest, "installed_consumer_digest_mismatch")
    return digest


def install_units(
    release_root: Path,
    legacy_hashes: dict[Path, str],
    *,
    previous_hashes: dict[Path, str] | None = None,
) -> None:
    bundle = release_root / "deploy" / "agent_platform" / "production"
    for name in UNITS:
        source = bundle / f"{name}.in"
        destination = UNIT_DIR / name
        need(
            source.is_file() and not source.is_symlink(),
            f"release_unit_missing:{name}",
        )

        current = digest_file(destination)
        desired = digest_file(source)

        allowed = {
            legacy_hashes[destination],
            desired,
        }

        if previous_hashes is not None:
            previous = previous_hashes.get(destination)
            if previous:
                allowed.add(previous)

        need(
            current in allowed,
            f"unit_drift:{name}",
        )

        if current != desired:
            atomic_write(
                destination,
                source.read_bytes(),
                0o644,
            )


def assert_deployed_coherence(
    release_root: Path,
    release: dict[str, object],
) -> None:
    # A matching /opt/herdr/current symlink alone is not proof of a
    # completed deployment. A host/process interruption may happen
    # between symlink, unit and deployed-marker transitions.

    bundle = release_root / "deploy" / "agent_platform" / "production"

    for name in UNITS:
        source = bundle / f"{name}.in"
        destination = UNIT_DIR / name

        need(
            source.is_file() and not source.is_symlink(),
            f"already_deployed_release_unit_missing:{name}",
        )
        need(
            destination.is_file() and not destination.is_symlink(),
            f"already_deployed_unit_missing:{name}",
        )
        need(
            digest_file(destination) == digest_file(source),
            f"already_deployed_unit_mismatch:{name}",
        )

    installed: dict[str, bytes] = {}

    for consumer in CONSUMERS:
        name = f"{consumer}.yaml"
        source = release_root / "configs" / "consumers" / name
        destination = CONSUMER_DIR / name

        need(
            source.is_file() and not source.is_symlink(),
            f"already_deployed_consumer_source_missing:{consumer}",
        )
        need(
            destination.is_file() and not destination.is_symlink(),
            f"already_deployed_consumer_missing:{consumer}",
        )

        data = destination.read_bytes()

        need(
            data == source.read_bytes(),
            f"already_deployed_consumer_mismatch:{consumer}",
        )

        installed[name] = data

    need(
        consumer_digest(installed)
        == release["config_contract_sha256"],
        "already_deployed_consumer_digest_mismatch",
    )

    need(
        PUBLIC_STATE.is_file() and not PUBLIC_STATE.is_symlink(),
        "already_deployed_public_state_missing",
    )

    try:
        document = json.loads(
            PUBLIC_STATE.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(
            "already_deployed_public_state_invalid"
        ) from exc

    need(
        set(document)
        == {
            "version",
            "tag",
            "commit",
            "config_sha256",
            "payload_manifest_sha256",
            "deployed_at",
        },
        "already_deployed_public_state_shape",
    )

    need(
        document["version"] == 1
        and document["tag"] == release["tag"]
        and document["commit"] == release["commit"]
        and document["config_sha256"]
        == release["config_contract_sha256"]
        and document["payload_manifest_sha256"]
        == release["payload_manifest_sha256"]
        and isinstance(document["deployed_at"], int)
        and document["deployed_at"] > 0,
        "already_deployed_public_state_mismatch",
    )


def deployed_document(release: dict[str, object], config_digest: str, deployed_at: int) -> dict[str, object]:
    need(config_digest == release["config_contract_sha256"], "deployment_config_mismatch")
    manifest_digest = release.get("payload_manifest_sha256")
    need(isinstance(manifest_digest, str)
         and len(manifest_digest) == 64
         and all(ch in "0123456789abcdef" for ch in manifest_digest),
         "deployment_manifest_digest_invalid")
    return {
        "version": 1,
        "tag": release["tag"],
        "commit": release["commit"],
        "config_sha256": config_digest,
        "payload_manifest_sha256": manifest_digest,
        "deployed_at": deployed_at,
    }


def write_deployed(document: dict[str, object]) -> None:
    need(grp is not None, "linux_group_database_required")
    group = grp.getgrnam("agent-platform-read").gr_gid
    atomic_write(PUBLIC_STATE, canonical_json(document), 0o640, 0, group)


def assert_hardening() -> None:
    properties = run("/usr/bin/systemctl", "show", "agent-platform-herdr.service",
                     "-p", "ProtectKernelTunables", "-p", "ProtectKernelModules",
                     "-p", "ProtectControlGroups", "-p", "RestrictSUIDSGID",
                     "-p", "RestrictNamespaces", "-p", "LockPersonality")
    values = dict(line.split("=", 1) for line in properties.splitlines())
    need(values and set(values.values()) == {"yes"}, "herdr_hardening_regressed")


def assert_no_active_durable_worker() -> None:
    workers = run(
        "/usr/bin/pgrep",
        "-af",
        "[a]gent-task-worker",
        check=False,
    )
    need(not workers.strip(), "durable_worker_active")


def unit_state(unit: str) -> str:
    return run(
        "/usr/bin/systemctl",
        "is-active",
        unit,
        check=False,
    )


def watchdog_lock_available() -> bool:
    """Fail closed when durable dispatch is held outside the managed unit."""
    if fcntl is None:
        return False
    flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(WATCHDOG_LOCK, flags)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            return False
        try:
            fcntl.flock(
                descriptor,
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except (BlockingIOError, OSError):
            return False
        return True
    finally:
        os.close(descriptor)


def stop_recovery_units() -> None:
    """Quiesce every unit that can race with the one-time recovery."""
    timers = (
        "agent-platform-export.timer",
        "agent-platform-herdr.timer",
    )
    services = (
        "agent-platform-export.service",
        "agent-platform-herdr.service",
    )
    run(
        "/usr/bin/systemctl",
        "stop",
        *timers,
        *services,
        "agent-stack-watchdog.service",
    )
    for timer in timers:
        need(
            unit_state(timer) == "inactive",
            f"recovery_timer_not_stopped:{timer}",
        )
    for service in services:
        need(
            unit_state(service) in {"inactive", "failed"},
            f"recovery_service_not_stopped:{service}",
        )
    need(
        unit_state("agent-stack-watchdog.service") in {"inactive", "failed"},
        "recovery_watchdog_not_stopped",
    )
    need(
        watchdog_lock_available(),
        "recovery_watchdog_lock_held",
    )


def start_telemetry_timers() -> None:
    timers = (
        "agent-platform-herdr.timer",
        "agent-platform-export.timer",
    )
    run("/usr/bin/systemctl", "start", *timers)
    for timer in timers:
        need(
            unit_state(timer) == "active",
            f"telemetry_timer_not_active:{timer}",
        )


def stop_recovery_web() -> None:
    run(
        "/usr/bin/systemctl",
        "stop",
        "agent-platform-web.service",
    )
    need(
        unit_state("agent-platform-web.service") in {"inactive", "failed"},
        "recovery_web_not_stopped",
    )


def remove_regular_file(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    need(path.is_file() and not path.is_symlink(), f"unsafe_remove_file:{path}")
    path.unlink()
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def run_rollback_steps(steps):
    """Run every rollback step and retain bounded failure evidence."""
    errors = []

    for name, action in steps:
        try:
            action()
        except BaseException as exc:
            errors.append(
                f"{name}:{type(exc).__name__}:{exc}"
            )

    return errors


@contextmanager
def readiness_modules(target: Path):
    """Load only the selected immutable runtime's closed telemetry contracts.

    Never reuse controller modules for a historical release. A private package
    namespace keeps target relative imports separate without altering sys.path.
    """
    package = target / "agent_platform_dashboard"
    need(package.is_dir() and not package.is_symlink() and root_owned_readonly(package),
         "unsafe_readiness_package")
    # FileFinder prefers native extensions to .py. Check the complete package,
    # not just Python sources, before allowing any relative import. This also
    # protects the pre-manifest legacy bootstrap from unvalidated artifacts.
    forbidden = tuple(importlib.machinery.EXTENSION_SUFFIXES) + (".pyc", ".pyo")
    for path in package.rglob("*"):
        need(not path.is_symlink() and (path.is_dir() or path.is_file())
             and root_owned_readonly(path), "unsafe_readiness_artifact")
        need(not path.name.endswith(forbidden), "readiness_non_source_import_denied")
    alias = f"_herdr_readiness_{os.getpid()}_{time.time_ns()}"
    namespace = types.ModuleType(alias)
    namespace.__path__ = [str(package)]
    sys.modules[alias] = namespace
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield tuple(importlib.import_module(f"{alias}.{name}") for name in
                    ("production_contract", "production_sources", "production_io", "production_web"))
    finally:
        sys.dont_write_bytecode = previous_bytecode
        for name in list(sys.modules):
            if name == alias or name.startswith(alias + "."):
                del sys.modules[name]


def assert_candidate_ready(target: Path, document: dict[str, object] | None) -> None:
    if target == LEGACY:
        # The original bootstrap is authenticated by the existing pinned
        # legacy binary/commit/unit gates, not RELEASE.json or a public marker.
        need(document is None, "legacy_readiness_document_not_allowed")
        expected = None
    else:
        expected = document if document is not None else read_trusted_public_state(PUBLIC_STATE)
        need(verify_tree(target)["commit"] == expected["commit"], "readiness_release_mismatch")
    with readiness_modules(target) as modules:
        validate_readiness(expected, modules)


def validate_readiness(expected, modules) -> None:
    """Validate actual exporter output using the same closed contract as web.

    A successful oneshot/export alone is insufficient: export intentionally
    publishes unavailable sources when the bridge fails.
    """
    c, sources, io, web = modules
    read, regular = io.read, io.regular

    need(pwd is not None and grp is not None, "linux_accounts_required")
    uid = pwd.getpwnam("agentops").pw_uid
    gid = grp.getgrnam("agent-platform-read").gr_gid
    need(live_unix_socket(HERDR_SOCKET), "bridge_socket_unavailable")
    for path in (BRIDGE, SNAPSHOT):
        with regular(str(path)) as (_, info):
            need(info.st_uid == uid and info.st_gid == gid
                 and stat.S_IMODE(info.st_mode) == 0o640,
                 f"unsafe_readiness_file:{path.name}")
    now = int(time.time())
    bridge = {profile: sources.herdr(str(BRIDGE), profile, now)[0]
              for profile in c.PROFILES}
    snapshot = c.decode(read(str(SNAPSHOT), c.MAX_BYTES, owner=uid))
    need(0 <= now - snapshot["generated_at"] <= 90, "snapshot_stale")
    for source in snapshot["sources"]:
        if source["kind"] not in {"router", "herdr", "release"}:
            continue
        if source["kind"] == "release" and expected is None:
            continue  # The pinned legacy bootstrap predates the release marker.
        need(source["status"] == "available"
             and 0 <= now - source["observed_at"] <= 90,
             f"snapshot_source_unready:{source['profile']}:{source['kind']}")
        if source["kind"] == "herdr":
            need(bool(source["rows"]) and source["rows"] == bridge[source["profile"]],
                 "snapshot_bridge_mismatch")
        if source["kind"] == "release" and expected is not None:
            need(source["rows"] == [{key: expected[key] for key in
                 ("tag", "commit", "config_sha256", "deployed_at")}],
                 "snapshot_release_mismatch")
    # Also validate root-owned web config, credentials, profiles and freshness.
    application = web.load(str(WEB_CONFIG))
    need(application.snapshot_path == str(SNAPSHOT), "unexpected_web_snapshot_path")


def capture_systemd_authority():
    return SystemdAuthority(globals()).capture()


def verify_systemd_authority(authority, *, allow_fence=False):
    SystemdAuthority(globals()).verify(authority, allow_fence=allow_fence)


def watchdog_fence_path():
    return UNIT_DIR / "agent-stack-watchdog.service.d/264-cutover-transaction.conf"


def watchdog_permit_path():
    return DEPLOYMENT_LOCK.parent / "watchdog-verified"


def watchdog_fence_bytes():
    # Conditions are evaluated by the system manager, not by the service user.
    # The /run permit disappears on reboot. A retained journal then denies start.
    return ("[Unit]\nConditionPathExists=|!" + str(STATE_DIR / "transaction.json")
            + "\nConditionPathExists=|" + str(watchdog_permit_path()) + "\n").encode("ascii")


def cleanup_watchdog_fence():
    remove_regular_file(watchdog_fence_path())
    remove_regular_file(watchdog_permit_path())
    run("/usr/bin/systemctl", "daemon-reload")


def ensure_watchdog_fence():
    remove_regular_file(watchdog_permit_path())
    path = watchdog_fence_path()
    if not path.parent.exists():
        path.parent.mkdir(mode=0o755)
    need(root_owned_readonly(path.parent) and not path.parent.is_symlink(),
         "unsafe_watchdog_fence_directory")
    if path.exists() or path.is_symlink():
        need(not path.is_symlink() and root_owned_readonly(path)
             and path.read_bytes() == watchdog_fence_bytes(), "unexpected_watchdog_fence")
    atomic_write(path, watchdog_fence_bytes(), 0o644)
    run("/usr/bin/systemctl", "daemon-reload")


def permit_watchdog_start():
    need((STATE_DIR / "transaction.json").is_file(), "watchdog_transaction_missing")
    atomic_write(watchdog_permit_path(), b"verified\n", 0o600)


def reconcile_systemd_authority(authority, *, fenced=False):
    return SystemdAuthority(globals()).reconcile(authority, fenced=fenced)


def verify_candidate_systemd_runtime(candidate, authority):
    need(CURRENT.resolve(strict=True) == candidate, "candidate_runtime_release_mismatch")
    current = SystemdAuthority(globals()).capture(allow_capacity=False, allow_fence=True)
    need(current["host_policy"] == authority["host_policy"], "host_policy_changed")
    release = verify_tree(candidate)
    assert_deployed_coherence(candidate, release)
    verify_release_runtime(candidate)
    return current


def transaction_snapshots() -> dict[Path, tuple[bytes, int, int, int] | None]:
    paths = [PUBLIC_STATE, BRIDGE, SNAPSHOT, NGINX_ROUTE]
    paths.extend(CONSUMER_DIR / f"{name}.yaml" for name in CONSUMERS)
    paths.append(UNIT_DIR / "agent-stack-watchdog.service.d/126-capacity-repair.conf")
    paths.append(watchdog_fence_path())
    return {path: snapshot_file(path) for path in paths}


def begin_transaction(previous: Path, report: dict, snapshots: dict, units: dict) -> Path:
    """Retain root-only baseline evidence across SIGKILL or host interruption.

    An unresolved transaction is never replayed automatically. Preflight blocks
    a second apply until an operator reconciles these exact captured bytes.
    """
    path = STATE_DIR / "transaction.json"
    need(not path.exists() and not path.is_symlink(), "unfinished_deployment_requires_operator_reconciliation")
    backup = STATE_DIR / f"{time.time_ns()}-baseline-authority.json"
    need(not backup.exists() and not backup.is_symlink(), "authority_backup_exists")
    contract = transactions.Contract(globals())
    document, backup_bytes, journal, journal_bytes = contract.plan(
        previous, report, snapshots, units, backup)
    # Repeat after fresh snapshots under the apply lock, before any runtime
    # mutation. Preflight is an observation, never a transferable guarantee.
    reserve = transactions.RESERVE_BYTES
    space = os.statvfs(STATE_DIR)
    need(space.f_bavail * space.f_frsize >= 10*1024**3 + 128*1024**2 + reserve,
         "transaction_capacity_insufficient")
    atomic_write(backup, backup_bytes, 0o600)
    need(contract.read(backup, expected_sha256=sha256(backup_bytes)) == document,
         "authority_backup_verification_failed")
    report["authority_backup"] = journal["authority_backup"]
    atomic_write(path, journal_bytes, 0o600)
    need(contract.read(path, journal=True) == journal, "journal_verification_failed")
    return path


def verify_transaction_preparation(previous, report, archive, allocation):
    """Actual capture/serialization/restore validation; no persistent writes."""
    snapshots, units = transaction_snapshots(), snapshot_units()
    backup = STATE_DIR / "9999999999999999999-baseline-authority.json"
    _, raw, _, journal = transactions.Contract(globals()).plan(
        previous, report, snapshots, units, backup)
    capacity = transactions.capacity(globals(), archive, allocation)
    return dict(status="verified", authority_backup_serialized_bytes=len(raw),
                authority_backup_maximum_bytes=transactions.BACKUP_MAX,
                journal_serialized_bytes=len(journal), journal_maximum_bytes=transactions.JOURNAL_MAX,
                capacity=capacity)


def write_evidence(path, document):
    raw = canonical_json(document)
    need(type(document) is dict and len(raw) <= transactions.EVIDENCE_MAX, "evidence_size_or_type")
    need(transactions.decode(raw, transactions.EVIDENCE_MAX) == document, "evidence_serialization")
    atomic_write(path, raw, 0o600)
    need(transactions.bounded_read(path, transactions.EVIDENCE_MAX, aggregate=True)[0] == raw,
         "evidence_readback_failed")


def rollback_previous(previous, report, snapshots, units, maintenance):
    """Restore exact authority before reopening traffic or durable dispatch."""
    degraded = report.get("baseline_health") == "degraded"
    def validate_retained_authority():
        ref = report['authority_backup']
        contract = transactions.Contract(globals())
        journal = contract.read(STATE_DIR / 'transaction.json', journal=True)
        need(journal['authority_backup'] == ref, "rollback_journal_reference_mismatch")
        document = contract.read(Path(ref['path']), expected_sha256=ref['sha256'])
        need(contract.validate(document) == {**snapshots, **units}, "rollback_backup_snapshot_mismatch")
    errors = run_rollback_steps([
        ("revoke_watchdog_permit", lambda: remove_regular_file(watchdog_permit_path())),
        ("fence_rollback", ensure_watchdog_fence),
        ("quiesce", stop_recovery_units),
        ("stop_web", stop_recovery_web),
        ("validate_retained_authority", validate_retained_authority),
    ])
    if not errors:
        errors.extend(run_rollback_steps([
            ("restore_units", lambda: restore_units(units)),
            ("restore_current", lambda: atomic_symlink(previous, CURRENT)),
            *[(f"restore:{path.name}", lambda p=path, s=value: restore_file(p, s))
              for path, value in snapshots.items() if path != watchdog_fence_path()],
            ("daemon_reload", lambda: run("/usr/bin/systemctl", "daemon-reload")),
        ]))
    if not errors:
        def verify():
            need(CURRENT.resolve(strict=True) == previous, "rollback_current_mismatch")
            for path, value in {**snapshots, **units}.items():
                if path == watchdog_fence_path():
                    continue  # Retain the boot fence until restoration is verified.
                need(snapshot_file(path) == value, f"rollback_file_mismatch:{path.name}")
            verify_systemd_authority(report["systemd_authority"], allow_fence=True)
            need(unit_state("agent-platform-web.service") in {"inactive", "failed"},
                 "rollback_web_not_quiescent")
            if not degraded:
                # Exact restoration was verified above. Regenerate with the
                # previous runtime before freshness checks: captured data may
                # legitimately be older than 90 seconds after a long attempt.
                run("/usr/bin/systemctl", "reset-failed", "agent-platform-herdr.service",
                    "agent-platform-export.service")
                run("/usr/bin/systemctl", "start", "agent-platform-export.service")
                need(run("/usr/bin/systemctl", "show", "agent-platform-herdr.service",
                         "--property=Result", "--value") == "success", "rollback_bridge_service_failed")
                assert_candidate_ready(previous, None)
                run("/usr/bin/systemctl", "reset-failed", "agent-platform-web.service")
                run("/usr/bin/systemctl", "start", "agent-platform-web.service")
                wait_http_status("http://127.0.0.1:3010/agent-platform/health", "401")
                need(unit_state("agent-platform-web.service") == "active", "rollback_web_not_active")
            run("/usr/sbin/nginx", "-t")
            run("/usr/bin/systemctl", "reload", "nginx")
            public_url = "https://2.28.67.165/agent-platform/health"
            public = (http_status(public_url) if degraded else
                      wait_http_status(public_url, "401"))
            need(public in RECOVERY_FAIL_CLOSED_PUBLIC_STATUSES if degraded else public == "401",
                 "rollback_public_boundary_open")
            need(http_status("https://2.28.67.165/") == report["public_root"], "rollback_root_changed")
        errors.extend(run_rollback_steps([("verify_rollback", verify)]))
    if not errors:
        errors.extend(run_rollback_steps([("restore_timers", start_telemetry_timers)]))
    if errors:
        errors.extend(run_rollback_steps([
            ("quiesce_incomplete_rollback", stop_recovery_units),
            ("fail_closed_route", lambda: atomic_write(NGINX_ROUTE, maintenance, 0o644)),
            ("nginx_test", lambda: run("/usr/sbin/nginx", "-t")),
            ("nginx_reload", lambda: run("/usr/bin/systemctl", "reload", "nginx")),
        ]))
    return errors


def switch_runtime(
    target: Path,
    document: dict[str, object] | None,
    systemd_authority: dict | None = None,
) -> None:
    # Durable orchestration remains stopped for every intermediate
    # candidate/rollback transition. Dispatch is re-enabled only after
    # the final candidate is fully committed and externally healthy.
    run(
        "/usr/bin/systemctl",
        "stop",
        "agent-stack-watchdog.service",
        "agent-platform-web.service",
    )

    atomic_symlink(target, CURRENT)

    if document is not None:
        write_deployed(document)

    run("/usr/bin/systemctl", "daemon-reload")

    if systemd_authority is not None:
        if document is None:
            verify_systemd_authority(systemd_authority, allow_fence=True)
        else:
            verify_candidate_systemd_runtime(target, systemd_authority)

    # candidate -> rollback -> candidate performs several bounded
    # transitions in a short interval. Reset systemd's rate limiter
    # before every transition and start the Herdr oneshot only once,
    # through agent-platform-export.service's dependency graph.
    run(
        "/usr/bin/systemctl",
        "reset-failed",
        "agent-platform-herdr.service",
        "agent-platform-export.service",
        "agent-platform-web.service",
    )
    run(
        "/usr/bin/systemctl",
        "start",
        "agent-platform-export.service",
    )
    # Wants=/After= do not propagate a failed bridge to the exporter. Check
    # both the producer result and its newly generated contract-bound bytes.
    need(run("/usr/bin/systemctl", "show", "agent-platform-herdr.service",
             "--property=Result", "--value") == "success", "bridge_service_failed")
    assert_candidate_ready(target, document)
    run(
        "/usr/bin/systemctl",
        "start",
        "agent-platform-web.service",
    )

    wait_http_status(
        "http://127.0.0.1:3010/agent-platform/health",
        "401",
    )

    need(
        run(
            "/usr/bin/systemctl",
            "is-active",
            "agent-platform-web.service",
        )
        == "active",
        "web_not_active",
    )

    assert_hardening()


def watchdog_runtime_state() -> tuple[str, str, int, int]:
    output = run(
        "/usr/bin/systemctl",
        "show",
        "agent-stack-watchdog.service",
        "-p",
        "ActiveState",
        "-p",
        "SubState",
        "-p",
        "MainPID",
        "-p",
        "NRestarts",
    )
    try:
        values = dict(
            line.split("=", 1)
            for line in output.splitlines()
            if line
        )
        need(
            {"ActiveState", "SubState", "MainPID", "NRestarts"}
            <= set(values),
            "watchdog_state_invalid",
        )
        main_pid = int(values["MainPID"])
        restarts = int(values["NRestarts"])
    except (TypeError, ValueError):
        raise ReleaseError("watchdog_state_invalid") from None
    need(main_pid >= 0 and restarts >= 0, "watchdog_state_invalid")
    return (
        values["ActiveState"],
        values["SubState"],
        main_pid,
        restarts,
    )


def start_watchdog_service() -> None:
    # All callers reload and verify authority before authorizing this start.
    # Reloading here would activate pending configuration after that check.
    run(
        "/usr/bin/systemctl",
        "start",
        "agent-stack-watchdog.service",
    )
    before = watchdog_runtime_state()
    need(
        before[0:2] == ("active", "running")
        and before[2] > 0,
        "watchdog_not_active",
    )
    time.sleep(WATCHDOG_STABILITY_SECONDS)
    after = watchdog_runtime_state()
    need(
        after[0:2] == ("active", "running")
        and after[2] > 0,
        "watchdog_not_active",
    )
    need(
        after[2:] == before[2:],
        "watchdog_not_stable",
    )


@serialized_deployment
def apply(archive: Path, expected_legacy_commit: str, confirmation: str) -> dict[str, object]:
    need(os.geteuid() == 0, "root_required")
    report = preflight(archive, expected_legacy_commit)
    approved_release = verify_archive(archive)
    need(confirmation == f"{approved_release['tag']}-{approved_release['commit'][:12]}",
         "confirmation_mismatch")
    # Record preparation separately from committed deployment metadata. A
    # failed pre-journal attempt can leave an immutable candidate/pinned copy;
    # these are retained and never interpreted as activation or auto-deleted.
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    for directory in (STATE_DIR.parent, STATE_DIR):
        need(not directory.is_symlink() and directory.stat().st_uid == 0
             and not directory.stat().st_mode & 0o077, "unsafe_state_directory")
    preparation_path = STATE_DIR / f"{time.time_ns()}-preparation.json"
    preparation = dict(version=1, status="preparing", source_archive=str(archive),
                       source_sha256=digest_file(archive),
                       release=report.get("release"), previous=str(CURRENT.resolve()))
    write_evidence(preparation_path, preparation)
    archive = pin_archive(archive)
    preparation.update(status="archive_pinned", pinned_archive=str(archive))
    write_evidence(preparation_path, preparation)
    release = verify_archive(archive)
    need(release == approved_release, "release_changed_during_pinning")
    identifier = f"{release['tag']}-{release['commit'][:12]}"
    need(confirmation == identifier, "confirmation_mismatch")
    need(report.get("release", release) == release, "release_changed_after_preflight")
    candidate = install_candidate(archive, release)
    preparation.update(status="candidate_prepared", candidate=str(candidate), release=release)
    write_evidence(preparation_path, preparation)

    if CURRENT.is_symlink() and CURRENT.resolve(strict=True) == candidate:
        # Fail closed unless every mutable production authority proves
        # the same immutable release identity.
        assert_deployed_coherence(
            candidate,
            release,
        )
        archive.unlink()
        return {
            **report,
            "status": "already_deployed",
            "current": str(candidate),
        }
    if not CURRENT.exists() and not CURRENT.is_symlink():
        CURRENT.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        need(not CURRENT.parent.is_symlink(), "current_directory_is_symlink")
        parent_info = CURRENT.parent.stat()
        need(parent_info.st_uid == 0 and not parent_info.st_mode & 0o022,
             "unsafe_current_directory")
        atomic_symlink(LEGACY, CURRENT)
    need(CURRENT.is_symlink(), "current_is_not_symlink")
    previous = CURRENT.resolve(strict=True)
    need(previous == LEGACY or previous.parent == RELEASES, "unexpected_previous_release")
    config_digest = release["config_contract_sha256"]
    hashes = expected_hashes(candidate / "deploy" / "herdr" / "cutover" /
                             "legacy-quantlab-staging-01.sha256")
    active_route = NGINX_ROUTE.read_bytes()
    need(
        sha256(active_route) == hashes[NGINX_ROUTE],
        "nginx_route_drift",
    )

    root_status = http_status("https://2.28.67.165/")

    maintenance = (
        candidate
        / "deploy"
        / "agent_platform"
        / "production"
        / "nginx-maintenance.conf.in"
    ).read_bytes()

    document = deployed_document(
        release,
        config_digest,
        int(time.time()),
    )

    # Snapshot exact pre-deployment mutable authority. Rollback restores
    # these exact bytes, not merely a compatible approximation.
    unit_snapshots = snapshot_units()
    previous_unit_hashes = snapshot_unit_hashes(unit_snapshots)
    public_state_snapshot = snapshot_file(PUBLIC_STATE)
    baseline_snapshots = transaction_snapshots()
    verify_systemd_authority(report["systemd_authority"])
    degraded = report.get("baseline_health") == "degraded"

    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    for directory in (STATE_DIR.parent, STATE_DIR):
        need(not directory.is_symlink(), "unsafe_state_directory")
        info = directory.stat()
        need(
            info.st_uid == 0
            and not info.st_mode & 0o077,
            "unsafe_state_directory",
        )

    state_path = (
        STATE_DIR
        / f"{document['deployed_at']}-{identifier}.json"
    )

    evidence_archive = (
        STATE_DIR
        / f"{document['deployed_at']}-{identifier}.tar.gz"
    )

    switched = False
    timers_stopped = False
    watchdog_stopped = False
    evidence_moved = False
    transactions.capacity(globals(), archive, report.get("candidate_allocation_bytes", 256*1024**2))
    transaction = begin_transaction(previous, report, baseline_snapshots, unit_snapshots)
    previous_sigterm = signal.getsignal(signal.SIGTERM)

    def interrupted(_number, _frame):
        raise KeyboardInterrupt("deployment_interrupted")

    signal.signal(signal.SIGTERM, interrupted)

    try:
        install_consumers(candidate, config_digest)
        atomic_write(
            NGINX_ROUTE,
            maintenance,
            0o644,
        )

        run("/usr/sbin/nginx", "-t")
        run("/usr/bin/systemctl", "reload", "nginx")

        wait_http_status(
            "https://2.28.67.165/agent-platform/health",
            "503",
        )

        need(
            http_status("https://2.28.67.165/")
            == root_status,
            "public_root_changed",
        )

        stop_recovery_units()
        timers_stopped = True

        run(
            "/usr/bin/systemctl",
            "stop",
            "agent-stack-watchdog.service",
        )
        watchdog_stopped = True

        assert_no_active_durable_worker()

        # --------------------------------------------------------
        # Candidate #1 — verification, watchdog still stopped.
        # --------------------------------------------------------

        reconcile_systemd_authority(report["systemd_authority"])

        install_units(
            candidate,
            hashes,
            previous_hashes=previous_unit_hashes,
        )

        switched = True

        switch_runtime(
            candidate,
            document,
            report["systemd_authority"],
        )

        # --------------------------------------------------------
        # Exact rollback exercise.
        # Restore exact previous systemd unit bytes BEFORE booting
        # the previous release services.
        # --------------------------------------------------------

        if not degraded:
            restore_units(unit_snapshots)
            dropin = UNIT_DIR / "agent-stack-watchdog.service.d/126-capacity-repair.conf"
            restore_file(dropin, baseline_snapshots[dropin])
            # The marker must precede export; otherwise the previous runtime
            # publishes the candidate identity during the rollback exercise.
            restore_file(PUBLIC_STATE, public_state_snapshot)
            switch_runtime(previous, None, report["systemd_authority"])

            need(
                CURRENT.resolve(strict=True) == previous,
                "rollback_current_mismatch",
            )

            for path, digest in previous_unit_hashes.items():
                need(
                    digest_file(path) == digest,
                    f"rollback_unit_mismatch:{path.name}",
                )

            need(
                http_status("https://2.28.67.165/")
                == root_status,
                "rollback_root_changed",
            )

        # --------------------------------------------------------
        # Final candidate promotion — still NO durable dispatch.
        # --------------------------------------------------------

        if not degraded:
            assert_no_active_durable_worker()
            reconcile_systemd_authority(report["systemd_authority"], fenced=True)

        install_units(
            candidate,
            hashes,
            previous_hashes=previous_unit_hashes,
        )

        switch_runtime(
            candidate,
            document,
            report["systemd_authority"],
        )

        run(
            "/usr/bin/systemctl",
            "start",
            "agent-platform-herdr.timer",
            "agent-platform-export.timer",
        )
        timers_stopped = False

        # Preserve immutable deployment evidence before reopening
        # durable dispatch.
        os.replace(
            archive,
            evidence_archive,
        )
        evidence_moved = True

        state = {
            **document,
            "release_path": str(candidate),
            "previous_path": str(previous),
            "rollback_exercised": not degraded,
            "rollback_mode": "skipped_known_degraded_previous" if degraded else "healthy_boot_exercised",
            "baseline_health": report.get("baseline_health", "healthy"),
            "public_root_status": root_status,
            "archive_sha256": digest_file(
                evidence_archive
            ),
            "archive_path": str(evidence_archive),
            "baseline_authority_backup": report["authority_backup"],
        }

        write_evidence(state_path, state)

        # Restore public traffic and prove the final candidate before
        # allowing maintenance/dispatcher to run.
        atomic_write(
            NGINX_ROUTE,
            active_route,
            0o644,
        )

        run("/usr/sbin/nginx", "-t")
        run("/usr/bin/systemctl", "reload", "nginx")

        wait_http_status(
            "https://2.28.67.165/agent-platform/health",
            "401",
        )

        need(
            http_status("https://2.28.67.165/")
            == root_status,
            "public_root_changed",
        )

        need(
            CURRENT.resolve(strict=True) == candidate,
            "final_current_mismatch",
        )

        # This is intentionally the LAST state-changing runtime step.
        # The watchdog can dispatch only after deployment identity,
        # route and health evidence are durable.
        verify_candidate_systemd_runtime(candidate, report["systemd_authority"])
        permit_watchdog_start()
        start_watchdog_service()
        watchdog_stopped = False
        cleanup_watchdog_fence()
        verify_candidate_systemd_runtime(candidate, report["systemd_authority"])
        remove_regular_file(transaction)

        return {
            "status": "success",
            **state,
            "state_file": str(state_path),
        }

    except BaseException as original_error:
        rollback_errors = rollback_previous(
            previous, report, baseline_snapshots, unit_snapshots, maintenance)
        rollback_errors.extend(run_rollback_steps([
            ("remove_success_state", lambda: remove_regular_file(state_path)),
            ("preserve_failed_archive", lambda: os.replace(
                evidence_archive if evidence_moved else archive,
                STATE_DIR / f"{document['deployed_at']}-{identifier}.failed-{os.getpid()}.tar.gz")),
        ]))
        if not rollback_errors and report["services"]["agent-stack-watchdog.service"] == "active":
            rollback_errors.extend(run_rollback_steps([
                ("verify_watchdog_authority", lambda: verify_systemd_authority(report["systemd_authority"], allow_fence=True)),
                ("permit_restored_watchdog", permit_watchdog_start),
            ]))
            if not rollback_errors:
                rollback_errors.extend(run_rollback_steps([("restore_watchdog", start_watchdog_service)]))
        if not rollback_errors:
            rollback_errors.extend(run_rollback_steps([
                ("cleanup_watchdog_fence", cleanup_watchdog_fence),
                ("verify_after_fence_cleanup", lambda: verify_systemd_authority(report["systemd_authority"])),
            ]))
        if not rollback_errors:
            remove_regular_file(transaction)
        else:
            rollback_errors.extend(run_rollback_steps([("refence_incomplete_rollback", ensure_watchdog_fence)]))
            # Even an evidence-write failure prevents a completed rollback
            # claim. Retain the journal and quiesce dispatch for reconciliation.
            rollback_errors.extend(run_rollback_steps([
                ("revoke_incomplete_watchdog_permit", lambda: remove_regular_file(watchdog_permit_path())),
                ("quiesce_incomplete_rollback", stop_recovery_units),
                ("fail_closed_route", lambda: atomic_write(NGINX_ROUTE, maintenance, 0o644)),
                ("nginx_test", lambda: run("/usr/sbin/nginx", "-t")),
                ("nginx_reload", lambda: run("/usr/bin/systemctl", "reload", "nginx")),
            ]))
        outcome = "rollback_degraded:previous_restored_web_inactive" if degraded else "rollback_healthy"
        raise ReleaseError(
            f"deployment_failed:{type(original_error).__name__}:{original_error};"
            + ("rollback_incomplete:" + "|".join(rollback_errors) if rollback_errors else outcome)
        ) from original_error
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)


@serialized_deployment
def recovery_apply(
    archive: Path,
    expected_legacy_commit: str,
    confirmation: str,
) -> dict[str, object]:
    """Promote a reviewed candidate from the exact known-degraded RC8 state.

    This mode never pretends the degraded previous release can pass a healthy
    rollback boot. On failure it restores previous immutable authority and
    deliberately leaves the public Agent Platform route in maintenance mode.
    """
    need(os.geteuid() == 0, "root_required")
    archive = pin_archive(archive)
    release = verify_archive(archive)
    identifier = f"{release['tag']}-{release['commit'][:12]}"
    need(confirmation == identifier, "confirmation_mismatch")
    report = preflight(
        archive,
        expected_legacy_commit,
        allow_degraded_rc8=True,
    )
    need(report.get("recovery_mode") == "rc8_router_overflow",
         "recovery_mode_not_authorized")
    candidate = install_candidate(archive, release)
    need(CURRENT.is_symlink(), "current_is_not_symlink")
    previous = CURRENT.resolve(strict=True)
    expected_previous = RELEASES / f"{RECOVERY_RC8_TAG}-{RECOVERY_RC8_COMMIT[:12]}"
    need(previous == expected_previous, "unexpected_recovery_previous_release")

    config_digest = install_consumers(candidate, release["config_contract_sha256"])
    hashes = expected_hashes(
        candidate / "deploy" / "herdr" / "cutover" /
        "legacy-quantlab-staging-01.sha256"
    )
    active_route = NGINX_ROUTE.read_bytes()
    need(sha256(active_route) == hashes[NGINX_ROUTE], "nginx_route_drift")
    root_status = http_status("https://2.28.67.165/")
    maintenance = (
        candidate / "deploy" / "agent_platform" / "production" /
        "nginx-maintenance.conf.in"
    ).read_bytes()
    document = deployed_document(release, config_digest, int(time.time()))
    unit_snapshots = snapshot_units()
    previous_unit_hashes = snapshot_unit_hashes(unit_snapshots)
    public_state_snapshot = snapshot_file(PUBLIC_STATE)

    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    for directory in (STATE_DIR.parent, STATE_DIR):
        info = directory.stat()
        need(info.st_uid == 0 and not info.st_mode & 0o077,
             "unsafe_state_directory")
    state_path = STATE_DIR / f"{document['deployed_at']}-{identifier}.json"
    evidence_archive = STATE_DIR / f"{document['deployed_at']}-{identifier}.tar.gz"

    switched = False
    evidence_moved = False
    try:
        atomic_write(NGINX_ROUTE, maintenance, 0o644)
        run("/usr/sbin/nginx", "-t")
        run("/usr/bin/systemctl", "reload", "nginx")
        wait_http_status(
            "https://2.28.67.165/agent-platform/health",
            "503",
        )
        need(http_status("https://2.28.67.165/") == root_status,
             "public_root_changed")

        stop_recovery_units()
        stop_recovery_web()
        assert_no_active_durable_worker()

        install_units(
            candidate,
            hashes,
            previous_hashes=previous_unit_hashes,
        )
        switched = True
        switch_runtime(candidate, document)

        start_telemetry_timers()

        os.replace(archive, evidence_archive)
        evidence_moved = True
        state = {
            **document,
            "release_path": str(candidate),
            "previous_path": str(previous),
            "rollback_exercised": False,
            "rollback_mode": "skipped_known_degraded_previous",
            "recovery_mode": "rc8_router_overflow",
            "public_root_status": root_status,
            "archive_sha256": digest_file(evidence_archive),
            "archive_path": str(evidence_archive),
        }
        atomic_write(NGINX_ROUTE, active_route, 0o644)
        run("/usr/sbin/nginx", "-t")
        run("/usr/bin/systemctl", "reload", "nginx")
        wait_http_status(
            "https://2.28.67.165/agent-platform/health",
            "401",
        )
        need(http_status("https://2.28.67.165/") == root_status,
             "public_root_changed")
        need(CURRENT.resolve(strict=True) == candidate,
             "final_current_mismatch")
        write_evidence(state_path, state)
        recovered = SystemdAuthority(globals()).capture(allow_capacity=False)
        need(recovered["host_policy"] == report["systemd_authority"]["host_policy"],
             "host_policy_changed")
        assert_deployed_coherence(candidate, release)
        start_watchdog_service()
        return {
            "status": "success",
            **state,
            "state_file": str(state_path),
        }
    except BaseException as original_error:
        quiescence_errors = run_rollback_steps([
            ("quiesce_recovery_units", stop_recovery_units),
            ("stop_web", stop_recovery_web),
        ])
        errors = [*quiescence_errors, *run_rollback_steps([
            (
                "fail_closed_route",
                lambda: atomic_write(NGINX_ROUTE, maintenance, 0o644),
            ),
            ("nginx_config_test", lambda: run("/usr/sbin/nginx", "-t")),
            ("nginx_reload", lambda: run("/usr/bin/systemctl", "reload", "nginx")),
            (
                "public_maintenance",
                lambda: wait_http_status(
                    "https://2.28.67.165/agent-platform/health",
                    "503",
                ),
            ),
        ])]
        authority_restored = False
        if not quiescence_errors:
            try:
                restore_units(unit_snapshots)
                if switched:
                    atomic_symlink(previous, CURRENT)
                restore_file(PUBLIC_STATE, public_state_snapshot)
                run("/usr/bin/systemctl", "daemon-reload")
                need(CURRENT.resolve(strict=True) == previous,
                     "recovery_rollback_current_mismatch")
                for path, digest in previous_unit_hashes.items():
                    need(digest_file(path) == digest,
                         f"recovery_rollback_unit_mismatch:{path.name}")
                need(snapshot_file(PUBLIC_STATE) == public_state_snapshot,
                     "recovery_rollback_public_state_mismatch")
                remove_regular_file(state_path)
                need(not state_path.exists() and not state_path.is_symlink(),
                     "recovery_rollback_state_present")
                authority_restored = True
            except BaseException as restore_error:
                errors.append(
                    "restore_recovery_authority:"
                    f"{type(restore_error).__name__}:{restore_error}"
                )
        try:
            need(digest_file(NGINX_ROUTE) == sha256(maintenance),
                 "recovery_rollback_route_not_fail_closed")
            need(
                unit_state("agent-stack-watchdog.service")
                in {"inactive", "failed"},
                "recovery_rollback_watchdog_active",
            )
            need(http_status("https://2.28.67.165/") == root_status,
                 "recovery_rollback_root_changed")
        except BaseException as verify_error:
            errors.append(
                "verify_recovery_rollback:"
                f"{type(verify_error).__name__}:{verify_error}"
            )
        if authority_restored and not errors:
            errors.extend(run_rollback_steps([
                ("restart_timers", start_telemetry_timers),
            ]))
        try:
            source = evidence_archive if evidence_moved else archive
            need(source.is_file() and not source.is_symlink(),
                 "recovery_failed_archive_missing")
            failed_archive = STATE_DIR / (
                f"{document['deployed_at']}-{identifier}.failed.tar.gz"
            )
            if failed_archive.exists():
                failed_archive = STATE_DIR / (
                    f"{document['deployed_at']}-{identifier}.failed-"
                    f"{os.getpid()}.tar.gz"
                )
            os.replace(source, failed_archive)
        except BaseException as archive_error:
            errors.append(
                "preserve_failed_archive:"
                f"{type(archive_error).__name__}:{archive_error}"
            )
        if errors:
            raise ReleaseError(
                "recovery_deployment_failed:"
                f"{type(original_error).__name__}:{original_error};"
                "rollback_incomplete:" + "|".join(errors)
            ) from original_error
        raise ReleaseError(
            "recovery_deployment_failed:"
            f"{type(original_error).__name__}:{original_error};"
            "previous_restored_fail_closed"
        ) from original_error


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("preflight", "apply", "recovery-preflight", "recovery-apply"),
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-legacy-commit", required=True)
    parser.add_argument("--confirm")
    args = parser.parse_args()
    try:
        archive = args.archive.resolve(strict=True)
        if args.mode == "preflight":
            result = preflight(archive, args.expected_legacy_commit)
        elif args.mode == "recovery-preflight":
            need(os.geteuid() == 0, "recovery_preflight_root_required")
            result = preflight(
                archive,
                args.expected_legacy_commit,
                allow_degraded_rc8=True,
            )
            need(result.get("recovery_mode") == "rc8_router_overflow",
                 "recovery_mode_not_authorized")
        elif args.mode == "recovery-apply":
            result = recovery_apply(
                archive,
                args.expected_legacy_commit,
                args.confirm or "",
            )
        else:
            result = apply(archive, args.expected_legacy_commit, args.confirm or "")
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ReleaseError, subprocess.SubprocessError, ValueError) as exc:
        print(f"cutover_failed:{exc}", file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
