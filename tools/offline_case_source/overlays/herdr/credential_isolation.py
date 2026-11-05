"""Physical SDK credential boundary observation shared by seal and retention.

The approved manifest describes the host snapshot.  Only its explicitly safe
projection is mounted in the SDK namespace.  A digest or reference is never
evidence that a process cannot read a credential.
"""
from __future__ import annotations

import hashlib
import errno
import json
import os
from pathlib import Path
import re
import stat


_SAFE_FILES = frozenset({"config.yaml", ".env", "herdr-sdk-policy.json"})
_SAFE_ENV = frozenset({
    "HOME", "PATH", "LANG", "LC_ALL", "TERM", "TMPDIR", "USER", "LOGNAME",
    "PYTHONNOUSERSITE", "HERMES_SAFE_MODE", "HERMES_ENABLE_PROJECT_PLUGINS",
    "HERDR_DURABLE_SANDBOX", "HERDR_DURABLE_TASK_PANE",
    "HERDR_POLICY_CONSUMER", "HERDR_POLICY_AGENT_ID", "HERDR_POLICY_PARENT_AGENT_ID",
    "HERDR_POLICY_PARENT_TASK_ID", "HERDR_POLICY_TASK_ID", "HERDR_POLICY_RUN_TOKEN",
    "HERDR_POLICY_FENCING_TOKEN",
    "HERDR_POLICY_STAGE1_PROOF_SHA256",
    "HERMES_HOME", "HERMES_MANAGED_DIR",
})
_SECRET_VALUE = re.compile(rb"(?i)(bearer\s|sk-[a-z0-9_-]{12,}|eyJ[a-z0-9_-]{12,}\.)")
WORKER_PROFILE = "herdr189-reference-lifetime"
# Exact reviewed source is also pinned in the prospective case inventory.
# A root-published record for another same-name policy cannot widen it.
WORKER_PROFILE_SOURCE_SHA256 = "42c8d021a856eb5e9c59b9f335695f296ea17b91eb3a04044ca6ef0e7bdf6d62"
CONFINEMENT_APPROVAL = Path("/etc/herdr/worker-confinement.json")
CONFINEMENT_SOURCE = Path("/etc/herdr/worker-profile.apparmor")
KERNEL_PROFILES = Path("/sys/kernel/security/apparmor/policy/profiles")
SYSTEM_RUNTIME_FILES = frozenset({
    "/bin/bash", "/usr/bin/python3", "/usr/bin/python3.14",
    "/lib64/ld-linux-x86-64.so.2", "/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
    *("/usr/lib/x86_64-linux-gnu/" + name for name in (
        "libc.so.6", "libm.so.6", "libz.so.1", "libexpat.so.1",
        "libtinfo.so.6", "libtinfo.so.6.6", "libpthread.so.0",
        "libdl.so.2", "libutil.so.1", "librt.so.1", "libssl.so.3",
        "libcrypto.so.3")),
    "/etc/ld.so.cache", "/etc/localtime", "/etc/hosts",
    "/etc/hostname", "/etc/resolv.conf", "/etc/nsswitch.conf",
    "/etc/passwd", "/etc/group",
})


def _read_bounded(path: Path, maximum: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("credential observation exceeds bound")
    return raw


def _environment(raw: bytes, profile_name: str) -> bool:
    if not raw.endswith(b"\0"):
        return False
    seen = set()
    values = {}
    for pair in raw[:-1].split(b"\0"):
        if b"=" not in pair:
            return False
        key, value = pair.split(b"=", 1)
        try:
            name = key.decode("ascii")
        except UnicodeError:
            return False
        if (name not in _SAFE_ENV or name in seen or len(value) > 4096
                or _SECRET_VALUE.search(value)):
            return False
        seen.add(name)
        values[name] = value
    expected = {
        "HOME": b"/home/agentops",
        "HERMES_HOME": ("/home/agentops/.hermes/profiles/" + profile_name).encode(),
        "HERMES_MANAGED_DIR": b"/run/herdr/policy-code/no-managed-scope",
        "HERMES_SAFE_MODE": b"1",
        "HERMES_ENABLE_PROJECT_PLUGINS": b"0",
    }
    if any(key in values and values[key] != value for key, value in expected.items()):
        return False
    return {"HOME", "HERDR_POLICY_TASK_ID", "HERDR_POLICY_FENCING_TOKEN"} <= seen


def _fd_links(links: dict[int, str]) -> bool:
    if type(links) is not dict or len(links) > 32:
        return False
    for number, target in links.items():
        if type(number) is not int or number > 2 or number < 0 or type(target) is not str:
            return False
        if target not in {"/dev/null", "/dev/tty"} and not re.fullmatch(r"/dev/pts/[0-9]+", target):
            return False
    return True


def _capture_fd_links(pid: int) -> dict[int, str]:
    if pid == os.getpid():
        return _capture_own_fd_links(pid)
    names = tuple(Path(f"/proc/{pid}/fd").iterdir())
    if len(names) > 32:
        raise ValueError("credential FD observation exceeds bound")
    result = {}
    for path in names:
        if not path.name.isdecimal():
            raise ValueError("credential FD observation ambiguous")
        result[int(path.name)] = os.readlink(path)
    return result


def _capture_own_fd_links(pid: int) -> dict[int, str]:
    """Identify ONLY the live scandir measurement handle, never skip races.

    CPython's iterator holds its opendir FD while each entry is inspected.
    A preexisting descriptor to the same directory creates a second candidate
    and is rejected. After iterator closure this EXACT measured FD must be
    EBADF. ENOENT on any entry, or reuse of the measured number, always denies.
    External/root observation keeps the original strict capture path.
    """
    if type(pid) is not int or pid != os.getpid() or pid <= 0:
        raise ValueError("exact self FD observation required")
    directory = f"/proc/{pid}/fd"
    before = os.stat(directory)
    if not stat.S_ISDIR(before.st_mode):
        raise ValueError("self FD directory invalid")
    result = {}; measurement = None; count = 0
    with os.scandir(directory) as entries:
        for entry in entries:
            count += 1
            if (count > 33 or not entry.name.isdecimal() or len(entry.name) > 10
                    or entry.path != directory + "/" + entry.name):
                raise ValueError("self FD observation ambiguous or exceeds bound")
            number = int(entry.name)
            if number in result or number == measurement:
                raise ValueError("duplicate self FD observation")
            target = os.readlink(entry.path)  # NEVER ignore foreign/racy ENOENT.
            if target == directory:
                info = os.stat(entry.path)
                if (measurement is not None or number <= 2 or not stat.S_ISDIR(info.st_mode)
                        or (info.st_dev, info.st_ino) != (before.st_dev, before.st_ino)):
                    raise ValueError("own measurement FD is not unique and exact")
                measurement = number
            else:
                result[number] = target
    if measurement is None or len(result) > 32:
        raise ValueError("own live measurement FD not established")
    try:
        os.fstat(measurement)
    except OSError as exc:
        if exc.errno != errno.EBADF:
            raise ValueError("own measurement FD state unknown") from exc
    else:
        raise ValueError("own measurement FD was reused or not closed")
    after = os.stat(directory)
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise ValueError("self FD directory changed")
    return result


def _process_tree(pid: int) -> tuple[int, ...]:
    """Bounded snapshot through every thread, not only the thread-group leader."""
    seen = set()
    pending = [pid]
    while pending:
        current = pending.pop()
        if current in seen or len(seen) >= 64:
            raise ValueError("credential process tree ambiguous or exceeds bound")
        seen.add(current)
        tasks = tuple(Path(f"/proc/{current}/task").iterdir())
        if not tasks or len(tasks) > 64:
            raise ValueError("credential task inventory ambiguous")
        for task in tasks:
            if not task.name.isdecimal():
                raise ValueError("credential task inventory malformed")
            raw = _read_bounded(task / "children", 4096)
            for child in raw.split():
                if not child.isdecimal() or int(child) <= 0 or int(child) in seen:
                    raise ValueError("credential process tree malformed")
                pending.append(int(child))
    return tuple(sorted(seen))


def _approved_confinement() -> dict:
    """Read a host-owned approval, never a worker or SDK supplied digest.

    The administrator must pin both reviewed source and the actual compiled
    policy exported by the kernel. Missing securityfs support denies sealing.
    """
    from .policy_launch import _verify_root_owned_ancestry
    from .credential_ingress_filter import filter_bytes
    _verify_root_owned_ancestry(CONFINEMENT_APPROVAL.parent)
    result = {}
    for path, limit in ((CONFINEMENT_APPROVAL, 4096),
                        (CONFINEMENT_SOURCE, 1_048_576)):
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
                or stat.S_IMODE(info.st_mode) & 0o022):
            raise ValueError("worker confinement approval is not root protected")
        result[path] = _read_bounded(path, limit)
    record = json.loads(result[CONFINEMENT_APPROVAL])
    if (type(record) is not dict or set(record) != {
            "schema_version", "profile", "source_sha256",
            "loaded_sha256", "filter_sha256", "system_files"}
            or record["schema_version"] != "herdr-worker-confinement-1"
            or record["profile"] != WORKER_PROFILE
            or any(type(record[key]) is not str
                   or not re.fullmatch(r"[a-f0-9]{64}", record[key])
                   for key in ("source_sha256", "loaded_sha256", "filter_sha256"))
            or record["source_sha256"] != WORKER_PROFILE_SOURCE_SHA256
            or hashlib.sha256(result[CONFINEMENT_SOURCE]).hexdigest()
                   != record["source_sha256"]
            or hashlib.sha256(filter_bytes()).hexdigest()
                   != record["filter_sha256"]
            or type(record["system_files"]) is not dict
            or set(record["system_files"]) != SYSTEM_RUNTIME_FILES):
        raise ValueError("worker confinement approval differs from source or filter")
    for name, digest in record["system_files"].items():
        if type(digest) is not str or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("system runtime digest malformed")
        path = Path(name).resolve(strict=True)
        _verify_root_owned_ancestry(path.parent)
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
                or stat.S_IMODE(info.st_mode) & 0o022
                or hashlib.sha256(_read_bounded(path, 16_777_216)).hexdigest() != digest):
            raise ValueError("approved system runtime file changed")
    return record


def _loaded_profile_sha256() -> str:
    """Hash the kernel's loaded compiled policy, never a name-only label."""
    found = []
    for directory in KERNEL_PROFILES.iterdir():
        if not directory.is_dir():
            continue
        if _read_bounded(directory / "name", 256).strip() == WORKER_PROFILE.encode():
            found.append(hashlib.sha256(_read_bounded(directory / "raw_data", 16_777_216)).hexdigest())
    if len(found) != 1:
        raise ValueError("loaded worker policy is unavailable or ambiguous")
    return found[0]


def _observed_system_runtime(pid: int, rows: dict, approval: dict) -> bool:
    """Reopen every approved host file through the worker's private root."""
    root = Path(f"/proc/{pid}/root")
    found = set()
    for top in ("bin", "lib", "lib64", "usr", "etc"):
        base = root / top
        if not base.is_dir() or base.is_symlink():
            return False
        for directory, dirs, files in os.walk(base, followlinks=False):
            if len(found) + len(dirs) + len(files) > 4096:
                return False
            for child in dirs:
                if (Path(directory) / child).is_symlink():
                    return False
            for child in files:
                path = Path(directory) / child
                if path.is_symlink() or not path.is_file():
                    return False
                found.add("/" + str(path.relative_to(root)))
    if found != SYSTEM_RUNTIME_FILES:
        return False
    for name, digest in approval["system_files"].items():
        if "ro" not in rows.get(name, set()) or "__stacked__" in rows.get(name, set()):
            return False
        path = root / name.lstrip("/")
        current = root
        for part in Path(name).parts[1:]:
            current /= part
            if current.is_symlink():
                return False
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode)
                or hashlib.sha256(_read_bounded(path, 16_777_216)).hexdigest() != digest):
            return False
    return True


def _kernel_boundary(pid: int, approval: dict) -> bool:
    """Require the proposed inherited label and an installed syscall filter.

    This verifies confinement state at observation. The pinned launcher and
    profile source define the rules; physical enforcement needs separate host
    approval and observation.
    """
    if (_loaded_profile_sha256() != approval["loaded_sha256"]):
        return False
    label = _read_bounded(Path(f"/proc/{pid}/attr/current"), 256).decode().strip()
    if label not in {f"{WORKER_PROFILE} (enforce)",
                     f"{WORKER_PROFILE}//&unpriv_bwrap (enforce)"}:
        return False
    status = _read_bounded(Path(f"/proc/{pid}/status"), 65536).decode()
    fields = {}
    for line in status.splitlines():
        key, _, value = line.partition(":")
        if key in {"Seccomp", "NoNewPrivs"}:
            if key in fields:
                return False
            fields[key] = value.strip()
    return fields == {"Seccomp": "2", "NoNewPrivs": "1"}


def _mount_aliases(root: Path, rows: dict, mountinfo: bytes, approved: dict,
                   admitted_workspace: str | None) -> bool:
    """Inspect every mounted target, including paths outside the profile.

    The private root is an empty tmpfs. This scan rejects extra mounts and
    credential aliases before either seal or retained acceptance.
    """
    if len(rows) > 4096 or len(mountinfo) > 1_048_576:
        return False
    protected = approved["files"]["auth.json"]
    selected = f"/home/agentops/.hermes/profiles/{approved['name']}/"
    safe_files = {selected + name for name in _SAFE_FILES}
    safe_other_files = set(SYSTEM_RUNTIME_FILES) | {"/etc/resolv.conf", "/etc/hosts", "/etc/hostname",
                        "/run/systemd/resolve/stub-resolv.conf",
                        "/run/systemd/resolve/resolv.conf",
                        "/run/herdr-policy/grant.bundle.json"}
    safe_dirs = {"/", "/proc", "/dev", "/dev/pts", "/dev/shm", "/tmp",
                 "/run", "/run/herdr", "/run/herdr-policy",
                 "/run/herdr-bootstrap", "/home/agentops",
                 "/home/agentops/.config/herdr",
                 "/opt/agent-platform", selected.rstrip("/"),
                 *(selected + name for name in ("sessions", "cache", "logs", "pastes"))}
    parsed = set()
    for line in mountinfo.splitlines():
        left, separator, _ = line.partition(b" - ")
        fields = left.split()
        if not separator or len(fields) < 6:
            return False
        raw = fields[4]
        for old, new in ((b"\\040", b" "), (b"\\011", b"\t"),
                         (b"\\012", b"\n"), (b"\\134", b"\\")):
            raw = raw.replace(old, new)
        try:
            target = raw.decode("utf-8")
        except UnicodeError:
            return False
        if (not target.startswith("/") or os.path.normpath(target) != target
                or target in parsed or target not in rows
                or "__stacked__" in rows[target]):
            return False
        parsed.add(target)
        # A mount anywhere in the host-root view may alias the protected
        # credential. Reject all unexpected regular-file mounts, regardless
        # of their name or readonly flag.
        path = root / target.lstrip("/")
        ancestor = root
        for part in Path(target).parts[1:]:
            ancestor /= part
            if ancestor.is_symlink():
                return False
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            return False
        if stat.S_ISREG(info.st_mode):
            if target not in safe_files | safe_other_files:
                return False
            if (target in safe_other_files and hashlib.sha256(
                    _read_bounded(path, 131072)).hexdigest() == protected):
                return False
        elif stat.S_ISDIR(info.st_mode):
            # Directory aliases are just as dangerous as file aliases. The
            # admitted workspace and immutable runtime mounts are verified
            # against the root-owned exact mount plan by the caller.
            if (target not in safe_dirs and target != admitted_workspace
                and not re.fullmatch(r"/home/agentops/tmp/hermes-[^/]+/results", target)
                and target not in {
                    "/run/herdr/policy-code", "/home/agentops/.hermes/hermes-agent",
                    "/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu",
                }):
                return False
        else:
            if target != "/run/herdr-policy/bootstrap-authority.sock":
                return False
        if target.startswith(selected) and target not in safe_files and target not in {
                selected + name for name in ("sessions", "cache", "logs", "pastes")}:
            return False
    return parsed == set(rows)


def _no_alias(root: Path, profile: Path) -> bool:
    # The private HOME is a tmpfs populated by the fixed mount plan. Reject
    # siblings and symlinks which could re-expose a protected profile by alias.
    hermes = root / "home/agentops/.hermes"
    profiles = hermes / "profiles"
    if (not stat.S_ISDIR(hermes.lstat().st_mode)
            or not stat.S_ISDIR(profiles.lstat().st_mode)
            or not stat.S_ISDIR((hermes / "hermes-agent").lstat().st_mode)
            or {item.name for item in profiles.iterdir()} != {profile.name}
            or {item.name for item in hermes.iterdir()} != {"profiles", "hermes-agent"}):
        return False
    if not stat.S_ISDIR(profile.lstat().st_mode):
        return False
    allowed = _SAFE_FILES | {"sessions", "cache", "logs", "pastes",
        "cron", "memories", "pairing", "hooks", "image_cache", "audio_cache", "skills"}
    if any(item.name not in allowed or item.is_symlink() for item in profile.iterdir()):
        return False
    config = root / "home/agentops/.config"
    private_config = config / "herdr"
    # The approved mount plan creates this private parent and an empty herdr
    # tmpfs.  Reject all other config entries, including symlinks and hidden
    # credential stores, while allowing the required private mount point.
    if not stat.S_ISDIR(config.lstat().st_mode) or not stat.S_ISDIR(private_config.lstat().st_mode):
        return False
    if {entry.name for entry in config.iterdir()} != {"herdr"} or any(private_config.iterdir()):
        return False
    sensitive = (
        profile / "auth.json", root / "home/agentops/.aws",
        root / "home/agentops/.ssh",
        root / "home/agentops/.gnupg", root / "home/agentops/.kube",
    )
    for path in sensitive:
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        return False
    return True


def evaluate_sdk_credentials(root: Path, approved: dict, rows: dict,
                             environment: bytes, fd_links: dict[int, str],
                             mountinfo: bytes, admitted_workspace: str | None = None) -> bool:
    """Closed decision over one captured process observation (inert fixtures use this)."""
    try:
        from .private_profile_namespace import verified_profile_identity
        if type(rows) is not dict or type(environment) is not bytes or type(mountinfo) is not bytes:
            return False
        approved = verified_profile_identity(approved)
        files = approved["files"]
        if (set(files) != _SAFE_FILES | {"auth.json"}
                or files[".env"] != hashlib.sha256(b"").hexdigest()):
            return False
        root = Path(root)
        profile = root / "home/agentops/.hermes/profiles" / approved["name"]
        if not _no_alias(root, profile):
            return False
        for name in _SAFE_FILES:
            path = profile / name
            info = path.lstat()
            target = "/home/agentops/.hermes/profiles/" + approved["name"] + "/" + name
            if (not stat.S_ISREG(info.st_mode) or "ro" not in rows.get(target, set())
                    or "__stacked__" in rows.get(target, set())
                    or hashlib.sha256(_read_bounded(path, 131072)).hexdigest() != files[name]):
                return False
        # No additional file may be mounted under the selected profile.  In
        # particular a readonly credential alias is still credential access.
        prefix = "/home/agentops/.hermes/profiles/" + approved["name"] + "/"
        permitted = {prefix + name for name in _SAFE_FILES}
        permitted.update(prefix + name for name in ("sessions", "cache", "logs", "pastes"))
        if any(path.startswith(prefix) and path not in permitted for path in rows):
            return False
        if (admitted_workspace is not None
                and (type(admitted_workspace) is not str or not admitted_workspace.startswith("/")
                     or os.path.normpath(admitted_workspace) != admitted_workspace)):
            return False
        if not _mount_aliases(root, rows, mountinfo, approved, admitted_workspace):
            return False
        lines = mountinfo.splitlines()
        if (not any(b" / ro" in line.split(b" - ", 1)[0]
                    and b" - tmpfs " in line for line in lines)
                or not any(b" /proc " in line.split(b" - ", 1)[0] and b" - proc " in line
                    for line in lines)
                or not any(b" /home/agentops ro" in line.split(b" - ", 1)[0]
                           and b" - tmpfs " in line for line in lines)):
            return False
        return _environment(environment, approved["name"]) and _fd_links(fd_links)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
        return False


def _observe_one(pid: int, approved: dict, rows: dict,
                 admitted_workspace: str | None = None) -> bool:
    return evaluate_sdk_credentials(
        Path(f"/proc/{pid}/root"), approved, rows,
        _read_bounded(Path(f"/proc/{pid}/environ"), 262144),
        _capture_fd_links(pid),
        _read_bounded(Path(f"/proc/{pid}/mountinfo"), 1_048_576),
        admitted_workspace,
    )


def _observe_sdk_credentials_direct(pid: int, approved: dict, rows: dict,
                            admitted_workspace: str | None = None) -> bool:
    """Return True only after direct, bounded observations of this process.

    Any unsupported FD, environment, alias, profile member, or mount state
    returns False.  The caller still verifies namespaces, exact mount plan,
    grant, and process identity separately.
    """
    try:
        if type(pid) is not int or pid <= 0:
            return False
        approval = _approved_confinement()
        before = _process_tree(pid)
        namespace = os.readlink(f"/proc/{pid}/ns/mnt")
        if any(os.readlink(f"/proc/{member}/ns/mnt") != namespace
               or not _kernel_boundary(member, approval)
               or not _observed_system_runtime(member, rows, approval)
               for member in before):
            return False
        if not all(_observe_one(member, approved, rows, admitted_workspace)
                   for member in before):
            return False
        # A process born during the scan must not inherit a credential FD or
        # alias without inspection. The caller must retry at a stable point.
        return _process_tree(pid) == before
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError):
        return False


def observe_sdk_credentials(pid, approved, rows, admitted_workspace=None):
    if pid == os.getpid():
        return _observe_sdk_credentials_direct(pid, approved, rows, admitted_workspace)
    from .observed_proc import native_scope_enabled, _DIRECT
    try:
        direct = _DIRECT.get() or not native_scope_enabled()
    except Exception:
        return False
    if direct:
        return _observe_sdk_credentials_direct(pid, approved, rows, admitted_workspace)
    from .observer_client import observe_from_host
    return observe_from_host(pid, approved, rows, admitted_workspace)
