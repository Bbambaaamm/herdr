#!/usr/bin/env python3
"""One-step, fail-closed runtime cutover to an immutable Herdr release."""
from __future__ import annotations

from argparse import ArgumentParser
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

try:
    import grp
except ImportError:  # pragma: no cover - production cutover is Linux-only
    grp = None

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from herdr.release import (  # noqa: E402
    CONSUMERS,
    ReleaseError,
    canonical_json,
    consumer_digest,
    safe_extract,
    sha256,
    verify_archive,
    verify_tree,
)


HOST = "quantlab-staging-01"
LEGACY = Path("/opt/agent-platform/release")
RELEASES = Path("/opt/herdr/releases")
CURRENT = Path("/opt/herdr/current")
CONSUMER_DIR = Path("/etc/herdr/consumers")
STATE_DIR = Path("/var/lib/herdr/deployments")
INCOMING_DIR = Path("/var/lib/herdr/incoming")
PUBLIC_STATE = Path("/var/lib/agent-platform-herdr/deployed-release.json")
NGINX_ROUTE = Path("/etc/agent-platform/nginx-server.conf")
UNIT_DIR = Path("/etc/systemd/system")
UNITS = (
    "agent-platform-web.service",
    "agent-platform-export.service",
    "agent-platform-herdr.service",
    "agent-platform-export.timer",
    "agent-platform-herdr.timer",
)


def need(value: bool, message: str) -> None:
    if not value:
        raise ReleaseError(message)


def digest_file(path: Path) -> str:
    need(path.is_file() and not path.is_symlink(), f"unsafe_file:{path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def pin_archive(source: Path) -> Path:
    """Copy an operator-owned archive through a pinned fd into root-only storage."""
    info = os.lstat(source)
    sudo_uid = int(os.environ.get("SUDO_UID", "-1"))
    need(stat.S_ISREG(info.st_mode) and not info.st_mode & 0o022
         and info.st_uid in (0, sudo_uid) and 0 < info.st_size <= 64 * 1024 * 1024,
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
        need((pinned.st_dev, pinned.st_ino, pinned.st_size) ==
             (info.st_dev, info.st_ino, info.st_size), "release_archive_changed")
        with os.fdopen(source_fd, "rb", closefd=False) as input_stream, \
             os.fdopen(target_fd, "wb", closefd=False) as output_stream:
            shutil.copyfileobj(input_stream, output_stream, 1024 * 1024)
            output_stream.flush()
            os.fsync(output_stream.fileno())
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


def expected_hashes(path: Path) -> dict[Path, str]:
    values: dict[Path, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        digest, separator, filename = line.partition("  ")
        target = Path(filename)
        need(bool(separator) and len(digest) == 64 and target.is_absolute()
             and target not in values, "invalid_expected_hash_manifest")
        values[target] = digest
    need(set(values) == {*(UNIT_DIR / name for name in UNITS), NGINX_ROUTE},
         "incomplete_expected_hash_manifest")
    return values


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, check=check, capture_output=True, text=True,
                            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
    return result.stdout.strip()


def http_status(url: str) -> str:
    return run("/usr/bin/curl", "--silent", "--show-error", "--max-time", "10",
               "--output", "/dev/null", "--write-out", "%{http_code}", url)


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
    prefixes = ("agent_platform_dashboard/", "deploy/agent_platform/production/")
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
    with tarfile.open(archive, "r:gz") as bundle:
        safe_extract(bundle, destination)
    roots = list(destination.iterdir())
    need(len(roots) == 1 and roots[0].is_dir(), "invalid_release_archive_root")
    verify_tree(roots[0])
    return roots[0]


def preflight(archive: Path, expected_legacy_commit: str) -> dict[str, object]:
    release = verify_archive(archive)
    need((ROOT / "RELEASE.json").is_file() and verify_tree(ROOT) == release,
         "cutover_tool_release_mismatch")
    need(socket.gethostname() == HOST, "wrong_host")
    need(LEGACY.is_dir() and not LEGACY.is_symlink(), "legacy_release_missing")
    legacy_commit = (LEGACY / "DEPLOYED_GIT_SHA").read_text(encoding="ascii").strip()
    need(legacy_commit == expected_legacy_commit, "legacy_commit_mismatch")
    dependency = release["external_dependency"]
    binary = LEGACY / "herdr"
    need(binary.stat().st_size == dependency["size"] and digest_file(binary) == dependency["sha256"],
         "external_binary_mismatch")
    manifest = ROOT / "deploy" / "herdr" / "cutover" / "legacy-quantlab-staging-01.sha256"
    for path, digest in expected_hashes(manifest).items():
        if path.name.endswith((".service", ".timer")):
            candidate = ROOT / "deploy" / "agent_platform" / "production" / f"{path.name}.in"
            need(digest_file(path) in (digest, digest_file(candidate)), f"unexpected_runtime_drift:{path}")
        else:
            need(digest_file(path) == digest, f"unexpected_runtime_drift:{path}")
    statuses = {unit: run("/usr/bin/systemctl", "is-active", unit, check=False) for unit in UNITS}
    need(statuses["agent-platform-web.service"] == "active"
         and statuses["agent-platform-export.timer"] == "active"
         and statuses["agent-platform-herdr.timer"] == "active", "runtime_not_healthy")
    with tempfile.TemporaryDirectory(prefix="herdr-preflight-") as folder:
        candidate = extract_candidate(archive, Path(folder))
        comparison = compare_trees(candidate, LEGACY)
    current = None
    if CURRENT.exists() or CURRENT.is_symlink():
        need(CURRENT.is_symlink(), "current_is_not_symlink")
        current = str(CURRENT.resolve(strict=True))
    direct_health = http_status("http://127.0.0.1:3010/agent-platform/health")
    public_health = http_status("https://2.28.67.165/agent-platform/health")
    need(direct_health == "401" and public_health == "401", "auth_boundary_regressed")
    return {
        "status": "preflight_ok",
        "release": release,
        "legacy_commit": legacy_commit,
        "legacy_release": str(LEGACY),
        "current": current,
        "runtime_diff": comparison,
        "services": statuses,
        "direct_health": direct_health,
        "public_health": public_health,
        "public_root": http_status("https://2.28.67.165/"),
    }


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


def install_units(release_root: Path, legacy_hashes: dict[Path, str]) -> None:
    bundle = release_root / "deploy" / "agent_platform" / "production"
    for name in UNITS:
        source = bundle / f"{name}.in"
        destination = UNIT_DIR / name
        need(source.is_file() and not source.is_symlink(), f"release_unit_missing:{name}")
        current = digest_file(destination)
        desired = digest_file(source)
        need(current in (legacy_hashes[destination], desired), f"unit_drift:{name}")
        if current != desired:
            atomic_write(destination, source.read_bytes(), 0o644)


def deployed_document(release: dict[str, object], config_digest: str, deployed_at: int) -> dict[str, object]:
    need(config_digest == release["config_contract_sha256"], "deployment_config_mismatch")
    return {
        "version": 1,
        "tag": release["tag"],
        "commit": release["commit"],
        "config_sha256": config_digest,
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


def switch_runtime(target: Path, document: dict[str, object] | None) -> None:
    run("/usr/bin/systemctl", "stop", "agent-platform-web.service")
    atomic_symlink(target, CURRENT)
    if document is not None:
        write_deployed(document)
    run("/usr/bin/systemctl", "daemon-reload")
    run("/usr/bin/systemctl", "start", "agent-platform-herdr.service")
    run("/usr/bin/systemctl", "start", "agent-platform-export.service")
    run("/usr/bin/systemctl", "start", "agent-platform-web.service")
    for _ in range(10):
        try:
            status = http_status("http://127.0.0.1:3010/agent-platform/health")
        except subprocess.SubprocessError:
            status = ""
        if status == "401":
            break
        time.sleep(1)
    else:
        raise ReleaseError("direct_health_failed")
    need(run("/usr/bin/systemctl", "is-active", "agent-platform-web.service") == "active",
         "web_not_active")
    assert_hardening()


def apply(archive: Path, expected_legacy_commit: str, confirmation: str) -> dict[str, object]:
    need(os.geteuid() == 0, "root_required")
    archive = pin_archive(archive)
    release = verify_archive(archive)
    identifier = f"{release['tag']}-{release['commit'][:12]}"
    need(confirmation == identifier, "confirmation_mismatch")
    report = preflight(archive, expected_legacy_commit)
    candidate = install_candidate(archive, release)
    if CURRENT.is_symlink() and CURRENT.resolve(strict=True) == candidate:
        archive.unlink()
        return {**report, "status": "already_deployed", "current": str(candidate)}
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
    config_digest = install_consumers(candidate, release["config_contract_sha256"])
    hashes = expected_hashes(candidate / "deploy" / "herdr" / "cutover" /
                             "legacy-quantlab-staging-01.sha256")
    active_route = NGINX_ROUTE.read_bytes()
    need(sha256(active_route) == hashes[NGINX_ROUTE], "nginx_route_drift")
    root_status = http_status("https://2.28.67.165/")
    maintenance = (candidate / "deploy" / "agent_platform" / "production" /
                   "nginx-maintenance.conf.in").read_bytes()
    document = deployed_document(release, config_digest, int(time.time()))
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    for directory in (STATE_DIR.parent, STATE_DIR):
        info = directory.stat()
        need(info.st_uid == 0 and not info.st_mode & 0o077, "unsafe_state_directory")
    state_path = STATE_DIR / f"{document['deployed_at']}-{identifier}.json"
    switched = False
    timers_stopped = False
    try:
        atomic_write(NGINX_ROUTE, maintenance, 0o644)
        run("/usr/sbin/nginx", "-t")
        run("/usr/bin/systemctl", "reload", "nginx")
        need(http_status("https://2.28.67.165/agent-platform/health") == "503",
             "maintenance_route_not_fail_closed")
        need(http_status("https://2.28.67.165/") == root_status, "public_root_changed")
        run("/usr/bin/systemctl", "stop", "agent-platform-export.timer",
            "agent-platform-herdr.timer")
        timers_stopped = True
        install_units(candidate, hashes)
        switched = True
        switch_runtime(candidate, document)
        # Exercise the exact rollback path while the public route remains fail-closed.
        switch_runtime(previous, None)
        need(http_status("https://2.28.67.165/") == root_status, "rollback_root_changed")
        switch_runtime(candidate, document)
        run("/usr/bin/systemctl", "start", "agent-platform-herdr.timer",
            "agent-platform-export.timer")
        timers_stopped = False
        evidence_archive = STATE_DIR / f"{document['deployed_at']}-{identifier}.tar.gz"
        os.replace(archive, evidence_archive)
        state = {
            **document,
            "release_path": str(candidate),
            "previous_path": str(previous),
            "rollback_exercised": True,
            "public_root_status": root_status,
            "archive_sha256": digest_file(evidence_archive),
            "archive_path": str(evidence_archive),
        }
        atomic_write(state_path, canonical_json(state), 0o600)
        atomic_write(NGINX_ROUTE, active_route, 0o644)
        run("/usr/sbin/nginx", "-t")
        run("/usr/bin/systemctl", "reload", "nginx")
        need(http_status("https://2.28.67.165/agent-platform/health") == "401",
             "public_auth_boundary_failed")
        need(http_status("https://2.28.67.165/") == root_status, "public_root_changed")
        return {"status": "success", **state, "state_file": str(state_path)}
    except BaseException:
        try:
            if switched:
                switch_runtime(previous, None)
            if timers_stopped:
                run("/usr/bin/systemctl", "start", "agent-platform-herdr.timer",
                    "agent-platform-export.timer")
            atomic_write(NGINX_ROUTE, active_route, 0o644)
            run("/usr/sbin/nginx", "-t")
            run("/usr/bin/systemctl", "reload", "nginx")
        finally:
            raise


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-legacy-commit", required=True)
    parser.add_argument("--confirm")
    args = parser.parse_args()
    try:
        archive = args.archive.resolve(strict=True)
        if args.mode == "preflight":
            result = preflight(archive, args.expected_legacy_commit)
        else:
            result = apply(archive, args.expected_legacy_commit, args.confirm or "")
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ReleaseError, subprocess.SubprocessError, ValueError) as exc:
        print(f"cutover_failed:{exc}", file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
