#!/usr/bin/env python3
"""Fail-closed activation of the repository-only Heating Hermes consumer."""
from __future__ import annotations

from argparse import ArgumentParser
from contextlib import ExitStack, contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import time
from types import SimpleNamespace

try:
    import fcntl
except ImportError:  # pragma: no cover - production activation is Linux-only
    fcntl = None

try:
    import pwd
except ImportError:  # pragma: no cover - tests run on Windows too
    pwd = SimpleNamespace(getpwnam=lambda _name: (_ for _ in ()).throw(
        ActivationError("unix_account_database_required")))


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from herdr.release import canonical_json, verify_tree  # noqa: E402
from herdr.security import InvocationIdentity, SecurityGrant  # noqa: E402
from deploy.herdr.cutover.cutover import deployment_lock  # noqa: E402


HOST_POLICY = Path("/etc/herdr/host-policy.json")
CURRENT = Path("/opt/herdr/current")
BACKUPS = Path("/var/lib/herdr/consumer-activations")
ACTIVATION_LOCK = Path("/run/herdr/heating-activation.lock")
TASK_ROOT = Path("/home/agentops/.local/state/agent-stack/tasks")
WORKSPACE = Path("/home/agentops/workspaces/heating")
RESULTS = TASK_ROOT / "results"
CONSUMER = "github:Bbambaaamm/heating"
SOURCE_CONSUMER = "github:Bbambaaamm/herdr"
TOOLS = (
    "read_file",
    "search_files",
    "patch",
    "write_file",
    "herdr_verify_work",
    "herdr_submit_result",
)
VALIDITY_HOURS = 168
MAX_POLICY_BYTES = 4 * 1024 * 1024
MAX_CODE_BYTES = 16 * 1024 * 1024
MAX_CODE_FILE_BYTES = 4 * 1024 * 1024
MAX_RUNTIME_FILES = 65536
RELEASE_OWNER_UID = 0


class ActivationError(RuntimeError):
    pass


def need(value: object, reason: str) -> None:
    if not value:
        raise ActivationError(reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_json(path: Path, *, owner: int = 0) -> tuple[dict, bytes]:
    info = os.lstat(path)
    need(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode),
         "host_policy_not_regular")
    need(info.st_uid == owner and not info.st_mode & 0o022
         and 0 < info.st_size <= MAX_POLICY_BYTES, "unsafe_host_policy")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        pinned = os.fstat(fd)
        raw = b""
        while len(raw) <= MAX_POLICY_BYTES:
            part = os.read(fd, min(65536, MAX_POLICY_BYTES + 1 - len(raw)))
            if not part:
                break
            raw += part
        named = os.stat(path, follow_symlinks=False)
        stamp = lambda value: (
            value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, value.st_uid, value.st_mode,
        )
        need(stamp(info) == stamp(pinned) == stamp(named) and len(raw) == info.st_size,
             "host_policy_changed")
    finally:
        os.close(fd)
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError("invalid_host_policy_json") from exc
    need(isinstance(value, dict), "invalid_host_policy_document")
    return value, raw


def release_inventory(release: Path) -> tuple[dict[str, str], tuple[str, ...], int]:
    release = release.resolve(strict=True)
    for directory in (release, *[item for item in release.rglob("*") if item.is_dir()]):
        info = directory.lstat()
        need(not directory.is_symlink() and stat.S_ISDIR(info.st_mode)
             and info.st_uid == RELEASE_OWNER_UID
             and (os.name == "nt" or not info.st_mode & 0o222),
             "release_tree_not_immutable")
    files: dict[str, str] = {}
    executable: list[str] = []
    total = 0
    for path in sorted([item for item in release.rglob("*") if item.is_file()]):
        info = path.lstat()
        need(not path.is_symlink() and stat.S_ISREG(info.st_mode)
             and info.st_uid == RELEASE_OWNER_UID and not info.st_mode & 0o222,
             "release_tree_not_immutable")
        need(info.st_size <= MAX_CODE_FILE_BYTES, "release_file_too_large")
        relative = path.relative_to(release).as_posix()
        body = path.read_bytes()
        need(len(body) == info.st_size, "release_file_changed")
        files[relative] = digest(body)
        if info.st_mode & 0o111:
            executable.append(relative)
        total += len(body)
        need(total <= MAX_CODE_BYTES, "release_tree_too_large")
    need(bool(files) and "RELEASE.json" in files and "MANIFEST.sha256" in files,
         "release_inventory_incomplete")
    return files, tuple(executable), total


def _open_runtime_file(root_fd: int, name: str) -> int:
    directory = os.dup(root_fd)
    try:
        parts = name.split("/")
        for part in parts[:-1]:
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        return os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=directory,
        )
    finally:
        os.close(directory)


def sanitized_runtime_inventory(definitions: object) -> tuple[list[dict], int]:
    """Drop mutable VCS metadata while proving every retained runtime byte."""
    fields = {
        "source", "target", "files", "executable_files", "max_bytes",
        "max_file_bytes",
    }
    need(isinstance(definitions, list) and len(definitions) == 2,
         "host_policy_runtime_inventory_invalid")
    proposal: list[dict] = []
    removed = 0
    for definition in definitions:
        need(isinstance(definition, dict) and set(definition) == fields,
             "host_policy_runtime_inventory_invalid")
        source = Path(str(definition["source"]))
        target = PurePosixPath(str(definition["target"]))
        files = definition["files"]
        executable = definition["executable_files"]
        max_bytes = definition["max_bytes"]
        max_file_bytes = definition["max_file_bytes"]
        need(source.is_absolute() and source.resolve(strict=True) == source
             and source.is_dir() and not source.is_symlink()
             and target.is_absolute(), "host_policy_runtime_path_invalid")
        need(isinstance(files, dict) and 0 < len(files) <= MAX_RUNTIME_FILES
             and isinstance(executable, list)
             and all(isinstance(name, str) for name in executable)
             and set(executable) <= set(files)
             and type(max_bytes) is int and 0 < max_bytes <= 2_147_483_648
             and type(max_file_bytes) is int
             and 0 < max_file_bytes <= 268_435_456,
             "host_policy_runtime_inventory_invalid")
        root_fd = None
        if os.name != "nt":
            root_fd = os.open(
                source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        retained: dict[str, str] = {}
        total = 0
        try:
            for name, expected in sorted(files.items()):
                need(isinstance(name, str) and name
                     and len(name.encode("utf-8")) <= 1024
                     and all(part not in {"", ".", ".."} for part in name.split("/"))
                     and "\\" not in name
                     and isinstance(expected, str) and len(expected) == 64
                     and all(character in "0123456789abcdef" for character in expected),
                     "host_policy_runtime_inventory_invalid")
                if name == ".git" or name.startswith(".git/"):
                    removed += 1
                    continue
                if os.name == "nt":
                    path = source.joinpath(*name.split("/"))
                    info = path.lstat()
                    need(path.is_file() and not path.is_symlink()
                         and info.st_size <= max_file_bytes,
                         "runtime_source_not_bounded_regular_file")
                    body = path.read_bytes()
                    need(len(body) == info.st_size and digest(body) == expected,
                         "runtime_source_differs_from_approved_bytes")
                else:
                    fd = _open_runtime_file(root_fd, name)
                    try:
                        info = os.fstat(fd)
                        need(stat.S_ISREG(info.st_mode) and info.st_size <= max_file_bytes,
                             "runtime_source_not_bounded_regular_file")
                        remaining = info.st_size
                        runtime_digest = hashlib.sha256()
                        while remaining:
                            chunk = os.read(fd, min(remaining, 1_048_576))
                            need(bool(chunk), "runtime_source_shortened")
                            runtime_digest.update(chunk)
                            remaining -= len(chunk)
                        need(not os.read(fd, 1)
                             and runtime_digest.hexdigest() == expected,
                             "runtime_source_differs_from_approved_bytes")
                    finally:
                        os.close(fd)
                total += info.st_size
                need(total <= max_bytes, "runtime_source_byte_limit")
                retained[name] = expected
        finally:
            if root_fd is not None:
                os.close(root_fd)
        need(bool(retained), "runtime_inventory_empty_after_sanitization")
        proposal.append({
            **definition,
            "source": str(source),
            "target": str(target),
            "files": retained,
            "executable_files": sorted(
                name for name in executable if name in retained),
        })
    return proposal, removed


def _heating_template(source: SecurityGrant, release: dict, issued: datetime) -> SecurityGrant:
    need(source.identity.consumer == SOURCE_CONSUMER, "source_template_identity_mismatch")
    need(not source.approvals and source.parent_grant_hash is None,
         "source_template_not_root_ceiling")
    need(set(TOOLS) <= set(source.scope.tools), "source_template_missing_required_tools")
    need(not source.process.enabled, "source_template_process_capability_forbidden")
    rules = []
    for rule in source.tool_rules:
        if rule.tool not in TOOLS:
            continue
        if rule.tool in {"read_file", "search_files", "patch", "write_file"}:
            rule = replace(rule, allowed_roots=(str(WORKSPACE),), result_slot=None)
        elif rule.tool == "herdr_submit_result":
            rule = replace(rule, allowed_roots=(str(RESULTS),), result_slot=None)
        else:
            rule = replace(rule, result_slot=None)
        rules.append(rule)
    need({rule.tool for rule in rules} == set(TOOLS), "source_template_rule_mismatch")
    commit = str(release["commit"])
    identity = InvocationIdentity(
        consumer=CONSUMER,
        agent_id="host-policy-template",
        parent_agent_id="host-policy-root",
        parent_task_id="host-policy-root",
        task_id="host-policy-template-heating",
        run_token=f"heating-{commit[:12]}-{int(issued.timestamp())}",
        fencing_token=1,
    )
    return replace(
        source,
        grant_id=f"host-heating-{commit[:12]}-{int(issued.timestamp())}",
        workspace_root=str(WORKSPACE),
        identity=identity,
        scope=replace(source.scope, tools=TOOLS, permissions=("workspace-write",)),
        tool_rules=tuple(rules),
        approvals=(),
        issued_at=issued.isoformat(),
        expires_at=(issued + timedelta(hours=VALIDITY_HOURS)).isoformat(),
        parent_grant_hash=None,
    )


def _same_security_ceiling(retained: SecurityGrant, desired: SecurityGrant) -> bool:
    """Ignore only release/hour metadata when validating a reviewed renewal."""
    normalized = replace(
        retained,
        grant_id=desired.grant_id,
        identity=replace(retained.identity, run_token=desired.identity.run_token),
        issued_at=desired.issued_at,
        expires_at=desired.expires_at,
    )
    return normalized.to_json() == desired.to_json()


def planned_policy(raw: dict, release_root: Path, release: dict,
                   issued: datetime) -> tuple[dict, SecurityGrant, int]:
    required = {
        "schema_version", "host_uid", "code", "runtime", "storage",
        "templates", "grant_ttl_seconds", "task_store_root",
    }
    version = raw.get("schema_version")
    if type(version) is int and version == 2:
        required |= {"private_launch"}
    need(set(raw) in (required, required | {"work_contracts"})
         and type(version) is int and version in (1, 2),
         "unsupported_host_policy_schema")
    agentops = pwd.getpwnam("agentops")
    need(raw.get("host_uid") == agentops.pw_uid, "host_policy_uid_mismatch")
    need(Path(str(raw.get("task_store_root"))) == TASK_ROOT,
         "host_policy_task_root_mismatch")
    templates = raw.get("templates")
    need(isinstance(templates, dict) and SOURCE_CONSUMER in templates,
         "source_consumer_template_missing")
    source = SecurityGrant.from_dict(templates[SOURCE_CONSUMER])
    desired = _heating_template(source, release, issued)
    existing = templates.get(CONSUMER)
    if existing is not None:
        retained = SecurityGrant.from_dict(existing)
        need(_same_security_ceiling(retained, desired), "heating_policy_drift")
    files, executable, total = release_inventory(release_root)
    code = raw.get("code")
    need(isinstance(code, dict) and code.get("target") == "/run/herdr/policy-code",
         "host_policy_code_target_mismatch")
    runtime, _ = sanitized_runtime_inventory(raw.get("runtime"))
    proposal = json.loads(json.dumps(raw))
    proposal["code"] = {
        "source": str(release_root),
        "target": "/run/herdr/policy-code",
        "files": files,
        "executable_files": list(executable),
        "max_bytes": MAX_CODE_BYTES,
        "max_file_bytes": MAX_CODE_FILE_BYTES,
    }
    proposal["runtime"] = runtime
    proposal["templates"][CONSUMER] = desired.to_json()
    need(len(canonical_json(proposal)) <= MAX_POLICY_BYTES, "planned_host_policy_too_large")
    return proposal, desired, total


def validate_environment(release_root: Path) -> dict:
    need(CURRENT.is_symlink() and CURRENT.resolve(strict=True) == release_root,
         "release_not_current")
    release = verify_tree(release_root)
    need(release_root.name == f"{release['tag']}-{str(release['commit'])[:12]}",
         "release_identity_mismatch")
    need(WORKSPACE.resolve(strict=True) == WORKSPACE and WORKSPACE.is_dir(),
         "heating_workspace_missing")
    return release


def preflight(release_root: Path, *, issued: datetime | None = None) -> tuple[dict, dict]:
    release_root = release_root.resolve(strict=True)
    release = validate_environment(release_root)
    raw, before = safe_json(HOST_POLICY)
    issued = issued or datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    proposal, desired, total = planned_policy(raw, release_root, release, issued)
    planned_digest = digest(canonical_json(proposal))
    confirmation = (
        f"activate-heating-{release['tag']}-{str(release['commit'])[:12]}-"
        f"{planned_digest[:16]}"
    )
    report = {
        "status": "preflight_ok",
        "consumer": CONSUMER,
        "release": {"tag": release["tag"], "commit": release["commit"]},
        "current_policy_sha256": digest(before),
        "planned_policy_sha256": planned_digest,
        "code_files": len(proposal["code"]["files"]),
        "code_bytes": total,
        "runtime_vcs_files_removed": sum(
            len(before_runtime["files"]) - len(after_runtime["files"])
            for before_runtime, after_runtime
            in zip(raw["runtime"], proposal["runtime"], strict=True)
        ),
        "tools": list(desired.scope.tools),
        "permissions": list(desired.scope.permissions),
        "workspace": desired.workspace_root,
        "valid_until": desired.expires_at,
        "live_control_capability": False,
        "confirmation": confirmation,
    }
    return report, proposal


@contextmanager
def exclusive_file_lock(path: Path, *, owner: int, create: bool = False):
    need(fcntl is not None, "linux_file_lock_required")
    flags = os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW
    if create:
        flags |= os.O_CREAT
    fd = os.open(path, flags, 0o600)
    try:
        info = os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_uid == owner
             and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600,
             "unsafe_activation_lock")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except BlockingIOError as exc:
        raise ActivationError("activation_or_worker_busy") from exc
    finally:
        os.close(fd)


def atomic_write(path: Path, data: bytes, mode: int) -> None:
    temporary = path.with_name(f".{path.name}.heating-{os.getpid()}-{time.time_ns()}")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, 0, 0, follow_symlinks=False)
        os.chmod(temporary, mode, follow_symlinks=False)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def verify_as_agentops() -> None:
    agentops = pwd.getpwnam("agentops")
    pid = os.fork()
    if pid == 0:
        try:
            os.setgroups([])
            os.setgid(agentops.pw_gid)
            os.setuid(agentops.pw_uid)
            from herdr.host_configuration import build_host_policy_factory
            factory = build_host_policy_factory()
            identity = InvocationIdentity(
                consumer=CONSUMER,
                agent_id="heating-activation-probe",
                parent_agent_id="heating-hermes",
                parent_task_id="coordinator:heating-hermes",
                task_id="heating-activation-probe",
                run_token=f"heating-activation-probe-{os.getpid()}-{time.time_ns()}",
                fencing_token=1,
            )
            launch = factory.prepare(
                identity=identity,
                workspace=WORKSPACE,
                tools=TOOLS,
                permissions=("workspace-write",),
            )
            try:
                need(launch.identity == identity
                     and set(launch.grant.scope.tools) == set(TOOLS),
                     "heating_consumer_not_loaded")
            finally:
                launch.cleanup_after_pane_closed()
        except BaseException:
            os._exit(1)
        os._exit(0)
    _, status = os.waitpid(pid, 0)
    need(os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0,
         "agentops_policy_verification_failed")


def apply(release_root: Path, confirmation: str) -> dict:
    need(os.geteuid() == 0, "root_required")
    agentops = pwd.getpwnam("agentops")
    with ExitStack() as locks:
        locks.enter_context(deployment_lock())
        release_root = release_root.resolve(strict=True)
        validate_environment(release_root)
        locks.enter_context(exclusive_file_lock(ACTIVATION_LOCK, owner=0, create=True))
        locks.enter_context(exclusive_file_lock(
            TASK_ROOT / "dispatcher.lock", owner=agentops.pw_uid))
        locks.enter_context(exclusive_file_lock(
            TASK_ROOT / "worker.lock", owner=agentops.pw_uid))
        report, proposal = preflight(release_root)
        need(confirmation == report["confirmation"], "confirmation_mismatch")
        _, before = safe_json(HOST_POLICY)
        BACKUPS.mkdir(parents=True, exist_ok=True, mode=0o700)
        need(not BACKUPS.is_symlink(), "activation_backup_directory_is_symlink")
        os.chown(BACKUPS, 0, 0)
        os.chmod(BACKUPS, 0o700)
        backup_info = BACKUPS.stat()
        need(backup_info.st_uid == 0 and not backup_info.st_mode & 0o077,
             "unsafe_activation_backup_directory")
        backup = BACKUPS / f"{int(time.time())}-{digest(before)[:16]}-host-policy.json"
        need(not backup.exists(), "activation_backup_collision")
        atomic_write(backup, before, 0o600)
        try:
            planned = canonical_json(proposal)
            atomic_write(HOST_POLICY, planned, 0o644)
            retained, after = safe_json(HOST_POLICY)
            need(retained == proposal and after == planned, "activated_policy_mismatch")
            verify_as_agentops()
        except BaseException:
            atomic_write(HOST_POLICY, before, 0o644)
            raise
    return {
        **report,
        "status": "success",
        "backup": str(backup),
        "activated_policy_sha256": digest(canonical_json(proposal)),
        "confirmation": report["confirmation"],
    }


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "apply"))
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--confirm")
    args = parser.parse_args()
    try:
        if args.mode == "preflight":
            result, _ = preflight(args.release)
        else:
            result = apply(args.release, args.confirm or "")
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (ActivationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"heating_activation_failed:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
