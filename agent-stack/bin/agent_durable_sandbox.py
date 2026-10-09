"""Construct and verify the durable task pane's mount and PID boundary."""
import os
import re
import json
import hashlib
import shlex
import secrets
import shutil
import stat
import sys
import tempfile
import termios
import time
from dataclasses import dataclass
from pathlib import Path

BWRAP = Path("/usr/bin/bwrap")
HOME = Path("/home/agentops")
HERDR_CONFIG = HOME / ".config/herdr"
HERDR_RELEASES = Path("/opt/agent-platform")
POLICY = Path(__file__).resolve().parents[1] / "policy-bin/herdr"
DEFAULT_WRITABLE = (
    HOME / ".hermes",
    HOME / ".cache",
    HOME / "worktrees",
)


# Duplicate the bridge's held directory BEFORE bwrap enters a user namespace.
# Reopening its /proc FD refers to the held inode, never the mutable logical path.
# --bind-fd consumes that inherited descriptor without a cross-namespace proc read.
_PINNED_LAUNCHER = """
import os, stat, sys
source, original_fd, device, inode = sys.argv[1:5]
args = sys.argv[5:]
fd = os.open(source, os.O_PATH | os.O_DIRECTORY)
held = os.fstat(fd)
if not stat.S_ISDIR(held.st_mode) or (held.st_dev, held.st_ino) != (int(device), int(inode)):
    raise SystemExit("pinned_worktree_identity_mismatch")
positions = [i for i, arg in enumerate(args) if arg in ("--bind-fd", "--ro-bind-fd")]
if len(positions) != 1 or args[positions[0] + 1] != original_fd:
    raise SystemExit("pinned_worktree_launch_invalid")
args[positions[0] + 1] = str(fd)
os.set_inheritable(fd, True)
os.execv(args[0], args)
"""


_POLICY_FD_LAUNCHER = r"""
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

if len(sys.argv) < 3 or len(sys.argv[1]) > 65536:
    raise SystemExit("policy_fd_launch_invalid")
entries = json.loads(sys.argv[1])
args = sys.argv[2:]
if not isinstance(entries, list) or not 1 <= len(entries) <= 96:
    raise SystemExit("policy_fd_launch_invalid")
mapping, targets, approved_files = {}, set(), set()
profile_name = None
total_profile_bytes = 0
for item in entries:
    if not isinstance(item, dict):
        raise SystemExit("policy_fd_launch_invalid")
    kind = item.get("kind")
    sealed = kind == "sealed-profile-data"
    ordinary = {"source", "fd", "device", "inode", "kind", "target"}
    expected_keys = ordinary | ({"sha256", "size"} if sealed else set())
    if set(item) != expected_keys:
        raise SystemExit("policy_fd_launch_invalid")
    if (any(type(item[k]) is not int or item[k] < 0
            for k in ("fd", "device", "inode"))
        or kind not in ("file", "directory", "socket", "sealed-profile-data")
        or not isinstance(item["source"], str)
        or not re.fullmatch(r"/proc/[1-9][0-9]{0,9}/fd/[0-9]{1,10}", item["source"])
        or item["source"].rsplit("/", 1)[-1] != str(item["fd"])
        or not isinstance(item["target"], str)
        or not item["target"].startswith("/")
        or item["fd"] in mapping or item["target"] in targets):
        raise SystemExit("policy_fd_launch_invalid")
    if sealed:
        match = re.fullmatch(
            r"/home/agentops/\.hermes/profiles/"
            r"([a-z0-9][a-z0-9_-]{0,31})/([a-zA-Z0-9_.\-/]{1,256})",
            item["target"],
        )
        if (match is None or any(p in ("", ".", "..") for p in match.group(2).split("/"))
            or match.group(2).split("/")[0] in
            {"sessions", "cache", "logs", "pastes", "state.db", ".hermes_history",
             "state.db-wal", "state.db-shm"}):
            raise SystemExit("policy_fd_profile_target_invalid")
        if profile_name is None:
            profile_name = match.group(1)
        if profile_name != match.group(1):
            raise SystemExit("policy_fd_profile_mismatch")
        size, digest = item["size"], item["sha256"]
        if (type(size) is not int or not 0 <= size <= 131072
            or not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None):
            raise SystemExit("policy_fd_profile_manifest_invalid")
        total_profile_bytes += size
        if total_profile_bytes > 524288:
            raise SystemExit("policy_fd_profile_manifest_invalid")
        approved_files.add(match.group(2))
    opened = os.open(
        item["source"],
        (os.O_RDONLY | os.O_CLOEXEC) if sealed
        else (os.O_PATH | (os.O_DIRECTORY if kind == "directory" else 0)),
    )
    held = os.fstat(opened)
    correct = (
        stat.S_ISDIR(held.st_mode) if kind == "directory"
        else stat.S_ISSOCK(held.st_mode) if kind == "socket"
        else stat.S_ISREG(held.st_mode)
    )
    if not correct or (held.st_dev, held.st_ino) != (item["device"], item["inode"]):
        raise SystemExit("policy_fd_identity_mismatch")
    if sealed:
        required_seals = 1 | 2 | 4 | 8
        if (held.st_size != size
            or fcntl.fcntl(opened, getattr(fcntl, "F_GET_SEALS", 1034))
            & required_seals != required_seals):
            raise SystemExit("policy_fd_profile_not_sealed")
        if hashlib.sha256(os.pread(opened, size, 0)).hexdigest() != digest:
            raise SystemExit("policy_fd_profile_digest_mismatch")
    mapping[item["fd"]] = (opened, item["target"], kind)
    targets.add(item["target"])

try:
    arg_end = args.index("--")
except ValueError:
    raise SystemExit("policy_fd_launch_invalid")
used = set()
# Consume FD bindings only inside bwrap's option grammar. Command arguments
# after -- can never satisfy a required sealed-profile mount.
for index, arg in enumerate(args[:arg_end]):
    if arg in ("--bind-fd", "--ro-bind-fd", "--ro-bind-data"):
        if index + 2 >= arg_end or not args[index + 1].isdigit():
            raise SystemExit("policy_fd_launch_invalid")
        original = int(args[index + 1])
        if original not in mapping or original in used:
            raise SystemExit("policy_fd_launch_invalid")
        opened, target, kind = mapping[original]
        if (args[index + 2] != target
            or (arg == "--ro-bind-data") != (kind == "sealed-profile-data")):
            raise SystemExit("policy_fd_launch_invalid")
        if kind == "sealed-profile-data":
            os.lseek(opened, 0, os.SEEK_SET)
        args[index + 1] = str(opened)
        os.set_inheritable(opened, True)
        used.add(original)
if used != set(mapping) or not args or args[0] != "/usr/bin/bwrap":
    raise SystemExit("policy_fd_launch_invalid")

home = Path("/home/agentops")
root = home / ".hermes"
profiles = root / "profiles"
tmpfs_targets = [args[i + 1] for i in range(arg_end - 1)
                 if args[i] == "--tmpfs"]
private_home = str(home) in tmpfs_targets
if private_home:
    if not approved_files or not {"config.yaml", ".env"} <= approved_files:
        raise SystemExit("policy_fd_profile_required")
    if tmpfs_targets.count(str(home)) != 1:
        raise SystemExit("policy_fd_private_home_invalid")
    parent = os.lstat(home.parent)
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
        or stat.S_IMODE(parent.st_mode) & 0o022):
        raise SystemExit("policy_fd_home_anchor_untrusted")
    # The entire private HOME base must be remounted read-only *after* the
    # sealed inputs and every other mount operation. A writable ancestor
    # allows a same-UID process to rename the mounted profile and replace the
    # logical pathname while Hermes is still running. The four runtime tmpfs
    # submounts are separate and remain writable (nonrecursive remount).
    if args[:4] != ["/usr/bin/bwrap", "--ro-bind", "/", "/"]:
        raise SystemExit("policy_fd_private_home_base_invalid")
    try:
        end = args.index("--")
    except ValueError:
        raise SystemExit("policy_fd_launch_invalid")
    # All private-home launches use a closed bwrap grammar. Never accept
    # --args: recursive option expansion bypasses ordinary mount validation.
    # Deny capability grants, alternate PID namespaces, fail-open modes and
    # new options unless independently audited and added to this contract.
    flags = {"--unshare-pid", "--die-with-parent", "--unshare-net"}
    path_options = {"--dev", "--proc", "--tmpfs", "--dir", "--chdir",
                    "--remount-ro"}
    one_value = path_options | {"--unsetenv"}
    two_values = {"--ro-bind", "--bind", "--ro-bind-fd", "--bind-fd",
                  "--ro-bind-data", "--setenv"}
    bind_options = two_values - {"--setenv"}
    parsed = []
    offset = 1
    while offset < end:
        option = args[offset]
        width = 0 if option in flags else 1 if option in one_value else (
            2 if option in two_values else -1)
        if width < 0 or offset + width >= end:
            raise SystemExit("policy_fd_private_option_denied")
        values = args[offset + 1:offset + 1 + width]
        if option in path_options or option in bind_options:
            destination = values[-1]
            if (not destination.startswith("/")
                or not os.path.isabs(destination)
                or os.path.normpath(destination) != destination
                or "//" in destination or "\\x00" in destination):
                raise SystemExit("policy_fd_private_mount_path_invalid")
        if option == "--setenv":
            if values[0] not in ("HOME", "PATH", "HERDR_DURABLE_SANDBOX"):
                raise SystemExit("policy_fd_private_home_env_invalid")
            if values[0] == "HOME" and values[1] != str(home):
                raise SystemExit("policy_fd_private_home_env_invalid")
        if option == "--unsetenv" and values[0] == "HOME":
            raise SystemExit("policy_fd_private_home_env_invalid")
        parsed.append((option, values, offset))
        offset += 1 + width
    # A destination-only mount guard is insufficient. Aliasing the original
    # host HOME or host procfs to an unrelated destination re-exposes it even
    # when private HOME is readonly and /proc is a fresh PID namespace.
    for option, values, position in parsed:
        if option not in ("--bind", "--ro-bind"):
            continue
        source_text, destination_text = values
        if (not source_text.startswith("/")
            or os.path.normpath(source_text) != source_text
            or "//" in source_text):
            raise SystemExit("policy_fd_private_mount_path_invalid")
        source = Path(source_text)
        resolved = Path(os.path.realpath(source_text))
        destination = Path(destination_text)
        if (position == 1 and option == "--ro-bind"
            and values == ["/", "/"]):
            continue
        if (source == Path("/") or resolved == Path("/")
            or source == home.parent or resolved == home.parent
            or source == home or resolved == home
            or source == root or root in source.parents
            or resolved == root or root in resolved.parents
            or source == Path("/proc") or Path("/proc") in source.parents
            or resolved == Path("/proc") or Path("/proc") in resolved.parents):
            raise SystemExit("policy_fd_private_source_exposes_host")
        # Approved worker/result binds must preserve their absolute target
        # identity. Never move a host-home subtree beneath another alias.
        if ((home in source.parents or home in resolved.parents)
            and (source != destination or resolved != source)):
            raise SystemExit("policy_fd_private_source_exposes_host")
    if (sum(option == "--unshare-pid" for option, _, _ in parsed) != 1
        or sum(option == "--proc" and value == ["/proc"]
               for option, value, _ in parsed) != 1):
        raise SystemExit("policy_fd_private_proc_missing")
    if (sum(option == "--setenv" and value == ["HOME", str(home)]
            for option, value, _ in parsed) != 1):
        raise SystemExit("policy_fd_private_home_env_invalid")
    # SDK and XDG path overrides are host-environment inputs, not trusted
    # profile authority. Every private-home execution clears them explicitly.
    relocation_keys = ("HERMES_HOME", "HERMES_PROFILE", "HERMES_CONFIG_DIR",
                       "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME",
                       "XDG_CACHE_HOME")
    if any(sum(option == "--unsetenv" and value == [key]
               for option, value, _ in parsed) != 1
           for key in relocation_keys):
        raise SystemExit("policy_fd_private_home_env_invalid")
    if any(option in bind_options
           and (Path(value[-1]) == Path("/proc")
                or Path("/proc") in Path(value[-1]).parents)
           for option, value, position in parsed if position > 1):
        raise SystemExit("policy_fd_private_proc_shadowed")
    if (args[end - 2:end] != ["--remount-ro", str(home)]
        or sum(args[i] == "--remount-ro" for i in range(end)) != 1):
        raise SystemExit("policy_fd_private_home_not_readonly")
    home_mask = next(i for i in range(end - 1)
                     if args[i] == "--tmpfs" and args[i + 1] == str(home))
    if home_mask >= end - 2:
        raise SystemExit("policy_fd_private_home_order_invalid")
    selected_profile = profiles / profile_name
    profile_runtime = {str(selected_profile / n)
                       for n in ("sessions", "cache", "logs", "pastes")}
    runtime_mounts = [args[i + 1] for i in range(end - 1)
                      if args[i] == "--tmpfs" and args[i + 1] in profile_runtime]
    if len(runtime_mounts) != len(profile_runtime) or set(runtime_mounts) != profile_runtime:
        raise SystemExit("policy_fd_private_runtime_missing")
    for i, arg in enumerate(args[:end]):
        if arg == "--ro-bind-data" and i < home_mask:
            raise SystemExit("policy_fd_private_home_order_invalid")
        if arg in ("--bind", "--ro-bind", "--dev-bind",
                   "--bind-try", "--ro-bind-try", "--dev-bind-try",
                   "--bind-fd", "--ro-bind-fd"):
            if i + 2 >= end:
                raise SystemExit("policy_fd_launch_invalid")
            destination = Path(args[i + 2])
            # /home and / are ancestors of HOME. A *later* bind there
            # shadows the complete profile namespace even when the private
            # /home/agentops tmpfs itself has already been mounted.
            if destination == home or destination in home.parents:
                if not (i == 1 and arg == "--ro-bind"
                        and args[i + 1:i + 3] == ["/", "/"]):
                    raise SystemExit("policy_fd_private_home_shadowed")
            if destination == root or root in destination.parents:
                # Only the independently verified immutable Hermes SDK tree
                # may live outside the sealed selected-profile input files.
                if not (arg == "--ro-bind-fd"
                        and destination == root / "hermes-agent"):
                    raise SystemExit("policy_fd_private_home_shadowed")
        if arg in ("--tmpfs", "--dev", "--proc", "--mqueue",
                   "--tmp-overlay", "--ro-overlay"):
            if i + 1 >= end:
                raise SystemExit("policy_fd_launch_invalid")
            destination = Path(args[i + 1])
            if destination in home.parents:
                raise SystemExit("policy_fd_private_home_shadowed")
            if destination == root or root in destination.parents:
                if not (arg == "--tmpfs" and str(destination) in profile_runtime):
                    raise SystemExit("policy_fd_private_home_shadowed")
        if arg in ("--file", "--bind-data", "--symlink"):
            if i + 2 >= end:
                raise SystemExit("policy_fd_launch_invalid")
            destination = Path(args[i + 2])
            if (destination == home or destination in home.parents
                or destination == root or root in destination.parents):
                raise SystemExit("policy_fd_private_home_shadowed")
        if arg == "--overlay":
            raise SystemExit("policy_fd_private_home_shadowed")
    # Runtime tmpfs mounts must be installed *after* the private home root,
    # and before its final read-only remount; otherwise data can leak or be
    # destroyed by an overmount without violating a simple target-set check.
    for i in range(end - 1):
        if args[i] == "--tmpfs" and args[i + 1] in profile_runtime:
            if not home_mask < i < end - 2:
                raise SystemExit("policy_fd_private_home_order_invalid")

    # All FD-backed mounts must also be host-policy destinations, not just
    # correct caller-supplied inode tuples. Without this check an attacker can
    # re-export the host /proc, HOME or credential subtree under /mnt/alias.
    # The *opened* FD path (not a caller-supplied "source" string) is checked.
    workspace_dirs = [v[0] for op, v, _ in parsed if op == "--chdir"]
    ordinary_entries = [item for item in entries
                        if item["kind"] != "sealed-profile-data"]
    # Disposable no-agent kernel tests may carry only sealed file data.
    # Any launch with ordinary code/workspace FDs requires an exact cwd.
    if len(workspace_dirs) > 1 or (ordinary_entries and len(workspace_dirs) != 1):
        raise SystemExit("policy_fd_private_workspace_invalid")
    workspace = Path(workspace_dirs[0]) if workspace_dirs else None
    sensitive = (Path("/"), Path("/home"), home, root,
                 home / ".ssh", home / ".aws", home / ".gnupg",
                 home / ".config", home / ".kube", Path("/proc"))
    approved_dir_targets = {
        Path("/run/herdr/policy-code"),
        Path("/run/herdr-bootstrap"),
        root / "hermes-agent",
        home / ".local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu",
        workspace,
    }
    approved_file_targets = {
        Path("/run/herdr-policy/grant.bundle.json"),
    }
    approved_socket_targets = {
        Path("/run/herdr-policy/bootstrap-authority.sock"),
    }
    for item in entries:
        if item["kind"] == "sealed-profile-data":
            continue
        target = Path(item["target"])
        allowed = {
            "directory": approved_dir_targets,
            "file": approved_file_targets,
            "socket": approved_socket_targets,
        }[item["kind"]]
        if target not in allowed:
            raise SystemExit("policy_fd_private_fd_target_untrusted")
        opened = mapping[item["fd"]][0]
        if item["kind"] != "socket":
            actual = os.readlink("/proc/self/fd/" + str(opened))
            if (not actual.startswith("/") or actual.endswith(" (deleted)")
                or os.path.normpath(actual) != actual
                or os.path.realpath(actual) != actual):
                raise SystemExit("policy_fd_private_fd_source_untrusted")
            path = Path(actual)
            if any(path == root_path for root_path in sensitive):
                raise SystemExit("policy_fd_private_fd_source_untrusted")
            if (root in path.parents or Path("/proc") in path.parents
                or any(x in path.parents for x in sensitive[4:-1])):
                raise SystemExit("policy_fd_private_fd_source_untrusted")
            if target == workspace and path != workspace:
                raise SystemExit("policy_fd_private_fd_source_untrusted")
    # Pin any remaining literal bind by a no-follow O_PATH FD *before*
    # execv(), eliminating the host rename/symlink gap between realpath()
    # validation and bwrap consuming its mount source.
    #
    # Only the one exact admitted working directory can be writable. A
    # root-published, immutable shim may be bound readonly over a known CLI
    # executable location. Unknown destinations (including /mnt/tree/alias)
    # and HOME credential paths are always denied, even if source==target.
    for option, values, position in parsed:
        if option not in ("--bind", "--ro-bind") or position == 1:
            continue
        source_text, target_text = values
        destination = Path(target_text)
        is_workspace = (workspace is not None
                        and destination == workspace
                        and source_text == str(workspace))
        is_cli = (option == "--ro-bind"
                  and re.fullmatch(
                      r"/home/agentops/\.local/(?:bin/[a-zA-Z0-9._-]+|"
                      r"share/uv/tools/[a-zA-Z0-9._/-]+)", target_text) is not None)
        if not (is_workspace or is_cli):
            raise SystemExit("policy_fd_private_literal_target_untrusted")
        source_fd = os.open(
            source_text, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        info = os.fstat(source_fd)
        if (is_workspace and not stat.S_ISDIR(info.st_mode)
            or is_cli and not stat.S_ISREG(info.st_mode)):
            raise SystemExit("policy_fd_private_literal_source_invalid")
        original_inode = os.readlink("/proc/self/fd/" + str(source_fd))
        if (original_inode != source_text
            or os.path.realpath(original_inode) != source_text
            or original_inode.endswith(" (deleted)")):
            raise SystemExit("policy_fd_private_literal_source_invalid")
        if is_cli:
            # Do not put user-owned policy shell code into an otherwise
            # immutable namespace. The real publisher must create new
            # root-owned source inodes under root-controlled ancestors.
            source_root = Path("/")
            for component in Path(source_text).parts[1:]:
                source_root /= component
                ancestor = os.lstat(source_root)
                if (ancestor.st_uid != 0
                    or stat.S_IMODE(ancestor.st_mode) & 0o022):
                    raise SystemExit("policy_fd_private_literal_source_untrusted")
            if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
                raise SystemExit("policy_fd_private_literal_source_untrusted")
        args[position] = "--bind-fd" if option == "--bind" else "--ro-bind-fd"
        args[position + 1] = str(source_fd)
        os.set_inheritable(source_fd, True)
    # The pinned FD is the only source Bubblewrap may mount; pathname
    # swaps performed after this check cannot alter that inode's identity.
else:
    if approved_files:
        raise SystemExit("policy_fd_profile_data_without_private_home")
    # Legacy mask inventory must remain strict until the production caller
    # is migrated to private HOME and sealed profile configuration.
    if root.is_symlink() or profiles.is_symlink():
        raise SystemExit("policy_fd_runtime_profile_alias")
    roots = [root]
    if profiles.is_dir():
        profiles_list = list(profiles.iterdir())
        if len(profiles_list) > 128 or any(p.is_symlink() for p in profiles_list):
            raise SystemExit("policy_fd_runtime_profile_alias")
        roots += [p for p in profiles_list if p.is_dir()]
    candidates = [home / ".cache"] + [
        p / n for p in roots for n in ("sessions", "cache", "logs")
    ]
    if any(p.is_symlink() for p in candidates):
        raise SystemExit("policy_fd_runtime_directory_alias")
    actual = {t for t in tmpfs_targets
              if t == str(home / ".cache") or t.startswith(str(root) + "/")}
    required = {str(p) for p in candidates if p.is_dir()}
    if actual != required:
        raise SystemExit("policy_fd_runtime_mount_mismatch")
os.execv(args[0], args)
"""

@dataclass
class PinnedWorktree:
    """A directory held by the bridge until the managed sandbox is running."""

    logical: Path
    fd: int
    device: int
    inode: int
    root: Path | None = None

    @property
    def identity(self) -> str:
        return f"{self.logical}|{self.device}:{self.inode}"

    @property
    def source(self) -> str:
        return f"/proc/{os.getpid()}/fd/{self.fd}"

    def verify(self) -> None:
        try:
            held = os.fstat(self.fd)
            source = os.stat(self.source)
        except OSError as exc:
            raise RuntimeError("pinned_worktree_unavailable") from exc
        if (not stat.S_ISDIR(held.st_mode) or
                (held.st_dev, held.st_ino) != (self.device, self.inode) or
                (source.st_dev, source.st_ino) != (self.device, self.inode)):
            raise RuntimeError("pinned_worktree_identity_mismatch")

    def close(self) -> None:
        os.close(self.fd)


def frozen_policy() -> Path:
    fd, name = tempfile.mkstemp(prefix="herdr-durable-policy-", dir="/tmp")
    try:
        with os.fdopen(fd, "wb") as target, POLICY.open("rb") as source:
            shutil.copyfileobj(source, target)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(name, 0o555)
        return Path(name)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def _ephemeral_sdk_runtime_dirs(home: Path) -> tuple[Path, ...]:
    """Mask only SDK data directories; named profiles keep immutable inputs."""
    root = home / ".hermes"
    profiles = root / "profiles"
    if root.is_symlink() or profiles.is_symlink():
        raise RuntimeError("durable_sdk_profile_alias_unverified")
    roots = [root]
    if profiles.is_dir():
        entries = sorted(profiles.iterdir())
        if len(entries) > 128:
            raise RuntimeError("durable_sdk_profile_count_exceeded")
        # A profile alias can resolve to the writable task workspace after the
        # sandbox binds are installed, exposing credentials/config to writes.
        # Skipping its runtime masks does not stop Hermes from loading it.
        if any(p.is_symlink() for p in entries):
            raise RuntimeError("durable_sdk_profile_alias_unverified")
        roots.extend(p for p in entries if p.is_dir())
    candidates = [home / ".cache"]
    candidates.extend(p / name for p in roots for name in ("sessions", "cache", "logs"))
    # A skipped alias remains visible to Hermes and may point into the writable
    # workspace. Every runtime alias must fail closed, even if dangling.
    if any(p.is_symlink() for p in candidates):
        raise RuntimeError("durable_sdk_runtime_alias_unverified")
    # A named profile that lacks these directories cannot initialize Hermes
    # with an otherwise read-only host root. Fail before consuming any model
    # budget; do not silently launch with unmasked runtime state.
    if any(not (p / name).is_dir() for p in roots[1:]
           for name in ("sessions", "cache", "logs")):
        raise RuntimeError("durable_sdk_profile_runtime_missing")
    return tuple(p for p in candidates if p.is_dir())


def command(
    workspace: Path,
    real_binary: Path,
    *,
    writable: tuple[Path, ...] = (),
    policy: Path | None = None,
    child_workspace_writable: bool | None = None,
    pinned_worktree: PinnedWorktree | None = None,
    policy_mount=None,
    owned_write_pins=None,
    admission_root: Path | None = None,
    private_profile_snapshot=None,
    hermes_profile: str | None = None,
) -> list[str]:
    if private_profile_snapshot is not None:
        from herdr.private_profile_namespace import PrivateProfileSnapshot
        if (policy_mount is None
                or not isinstance(private_profile_snapshot, PrivateProfileSnapshot)
                or hermes_profile != private_profile_snapshot.name):
            raise RuntimeError("durable_private_profile_authority_required")
        # A host-writable workspace or durable result slot mounted by pathname
        # can be swapped after host validation and before bwrap consumes it.
        # The child already has an admitted pinned worktree FD, but neither
        # root nor child currently supplies a pinned writable result-slot FD.
        # Fail CLOSED for the new mode until both root/child paths provide
        # complete FD-owned write mounts; don't regress legacy behavior.
        if pinned_worktree is None or writable:
            raise RuntimeError("durable_private_profile_sources_unpinned")
        private_profile_mounts = private_profile_snapshot.mount_arguments()
    else:
        private_profile_mounts = []
    if admission_root is not None and policy_mount is None:
        raise RuntimeError("ownership_epoch_authenticated_launch_required")
    workspace = Path(workspace).absolute() if pinned_worktree else workspace.resolve(strict=True)
    if child_workspace_writable is not None:
        if (pinned_worktree is None or pinned_worktree.logical != workspace):
            raise RuntimeError("managed_child_worktree_unpinned")
        pinned_worktree.verify()
    if owned_write_pins is not None:
        from herdr.owned_write_mounts import OwnedWritePins
        if (not isinstance(owned_write_pins,OwnedWritePins) or
                owned_write_pins.worktree is not pinned_worktree or
                child_workspace_writable is not False or policy_mount is None):
            raise RuntimeError("owned_write_mount_authority_required")
        owned_write_pins.verify()
    real_binary = real_binary.absolute()
    policy = policy or POLICY
    if not BWRAP.is_file() or not policy.is_file() or not real_binary.is_file():
        raise RuntimeError("durable_sandbox_prerequisite_missing")
    if (pinned_worktree is None and not workspace.is_dir()) or not HERDR_CONFIG.is_dir():
        raise RuntimeError("durable_sandbox_workspace_or_config_missing")
    if workspace == HERDR_RELEASES or HERDR_RELEASES in workspace.parents:
        raise RuntimeError("durable_sandbox_workspace_exposes_herdr_releases")
    if child_workspace_writable is not None:
        if len(writable) != 1:
            raise RuntimeError("managed_child_exact_result_required")
        result = Path(writable[0])
        if (result.parent.name != "results" or not result.name.endswith(".result.json")
                or not stat.S_ISREG(result.lstat().st_mode)):
            raise RuntimeError("managed_child_exact_result_required")
        result = result.resolve(strict=True)
        if result.is_relative_to(workspace):
            raise RuntimeError("managed_child_result_inside_workspace")
        if pinned_worktree.root and (result == pinned_worktree.root or
                                     pinned_worktree.root in result.parents):
            raise RuntimeError("managed_child_result_inside_worktree_root")

    # Keep the host root read-only. Root tasks retain their workspace bind;
    # managed children receive it writable only with admitted write scope.
    # Mask control paths after writable binds and over-mount the local CLI.
    args = [
        str(BWRAP),
        "--ro-bind", "/", "/",
        "--dev", "/dev",
        "--unshare-pid",
        *(["--die-with-parent"] if admission_root is not None else []),
        "--tmpfs", "/tmp",
        *(private_profile_mounts[:-2] if private_profile_mounts else []),
        *([] if pinned_worktree is None else
          ["--tmpfs", str(workspace.parent), "--dir", str(workspace)]),
        (("--bind-fd" if child_workspace_writable is not False else "--ro-bind-fd")
         if pinned_worktree else
         ("--bind" if child_workspace_writable is not False else "--ro-bind")),
        str(pinned_worktree.fd) if pinned_worktree else str(workspace), str(workspace),
        "--proc", "/proc",
        "--chdir", str(workspace),
    ]
    seen = {workspace}
    defaults = DEFAULT_WRITABLE if child_workspace_writable is None and policy_mount is None else ()
    for raw in (*defaults, *writable):
        path = Path(raw)
        if not path.exists():
            continue
        path = path.resolve(strict=True)
        if child_workspace_writable is not None and (
            path in result.parents or
            (pinned_worktree.root is not None and
             (path == pinned_worktree.root or pinned_worktree.root in path.parents
              or path in pinned_worktree.root.parents)) or
            (child_workspace_writable is False and (
                path == workspace or path in workspace.parents
                or (workspace in path.parents and path != result)))
        ):
            continue
        if path in seen:
            continue
        seen.add(path)
        args += ["--bind", str(path), str(path)]

    if owned_write_pins is not None:
        for entry in owned_write_pins.descriptors():
            args += ["--bind-fd",str(entry["fd"]),entry["target"]]

    if child_workspace_writable is not None or policy_mount is not None:
        # With a reviewed, signed profile snapshot, the private HOME and
        # exact writable runtime submounts already hide all mutable host
        # profiles. Never overlay host-controlled profile directories here.
        if private_profile_snapshot is None:
            for runtime_dir in _ephemeral_sdk_runtime_dirs(HOME):
                args += ["--tmpfs", str(runtime_dir)]
        # Keep the host network namespace: Hermes needs provider egress and
        # the durable delegation bridge uses an abstract AF_UNIX socket, which
        # is scoped by the network namespace. Network-capable model tools are
        # denied by the explicit Hermes toolset allowlist instead.

    args += ["--tmpfs", str(HERDR_CONFIG), "--tmpfs", str(HERDR_RELEASES)]
    for path in {real_binary, real_binary.resolve(strict=True)}:
        args += ["--ro-bind", str(policy), str(path)]
    if policy_mount is not None:
        # Host-only immutable copies override mutable checkout/runtime aliases.
        descriptors = policy_mount.descriptors()
        if owned_write_pins is not None:descriptors.extend(owned_write_pins.descriptors())
        if private_profile_snapshot is not None:
            descriptors.extend(private_profile_snapshot.fd_descriptors())
        args += ["--tmpfs", "/run", "--dir", "/run/herdr", "--dir", "/run/herdr-policy"]
        for entry in policy_mount.descriptors():
            args += ["--ro-bind-fd", str(entry["fd"]), entry["target"]]
        from herdr.launch_environment import STARTUP_CONTROLS
        for name in sorted(set(STARTUP_CONTROLS)|{key for key in os.environ if key.startswith("LD_")}):
            args += ["--unsetenv",name]
        args += ["--setenv", "PATH", "/run/herdr-bootstrap:/usr/bin:/bin"]
    args += [
        "--setenv", "HERDR_DURABLE_SANDBOX", "1",
        *(private_profile_mounts[-2:] if private_profile_mounts else []),
        "--", "/bin/bash", "--noprofile", "--norc", "-i",
    ]
    if policy_mount is not None:
        if pinned_worktree is not None:
            descriptors.insert(0, {"source": pinned_worktree.source, "fd": pinned_worktree.fd,
                                  "device": pinned_worktree.device, "inode": pinned_worktree.inode,
                                  "kind": "directory", "target": str(pinned_worktree.logical)})
        result_command = ["/usr/bin/python3", "-I", "-S", "-c", _POLICY_FD_LAUNCHER,
                          json.dumps(descriptors, separators=(",", ":")), *args]
        if admission_root is not None:
            from herdr.ownership_epoch import custodial_command, legacy_admission_guard
            with legacy_admission_guard(admission_root) as epoch:
                return custodial_command(result_command, epoch)
        return result_command
    if pinned_worktree is not None:
        return [sys.executable, "-I", "-c", _PINNED_LAUNCHER,
                pinned_worktree.source, str(pinned_worktree.fd),
                str(pinned_worktree.device), str(pinned_worktree.inode), *args]
    return args


MAX_PANE_SHELL_COMMAND_BYTES = 32768


def shell_command(args: list[str]) -> str:
    from herdr.launch_environment import STARTUP_CONTROLS
    controls=sorted(set(STARTUP_CONTROLS)|{key for key in os.environ
                    if key.startswith("LD_") and key.replace("_","").isalnum()})
    rendered = "unset " + " ".join(map(shlex.quote,controls)) + "; exec " + shlex.join(args)
    # Herdr pane.run carries this as ONE argv element. Reject a huge profile
    # inventory instead of hitting Linux MAX_ARG_STRLEN / E2BIG ambiguously.
    if len(rendered.encode("utf-8")) > MAX_PANE_SHELL_COMMAND_BYTES:
        raise RuntimeError("durable_sandbox_shell_command_too_large")
    return rendered


def _env(pid: int) -> set[bytes]:
    return set(Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"))


def _terminal_input_ready(pid: int, marker: str) -> bool:
    """Require the marked process to own an active, noncanonical foreground TTY."""
    fd = None
    try:
        if pid <= 0:
            return False
        expected = f"HERDR_DURABLE_TASK_PANE={marker}".encode()
        if expected not in _env(pid):
            return False
        source = f"/proc/{pid}/fd/0"
        fd = os.open(source, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC)
        held = os.fstat(fd)
        if not stat.S_ISCHR(held.st_mode) or not os.isatty(fd):
            return False
        attributes = termios.tcgetattr(fd)
        named = os.stat(source)
        def terminal_owner():
            # Linux proc_pid_stat(5): pgrp, tty_nr, tpgid, starttime.
            data = Path(f"/proc/{pid}/stat").read_text()
            fields = data[data.rfind(")") + 2:].split()
            group, tty, foreground, start = map(int, (fields[2], fields[4], fields[5], fields[19]))
            tty &= 0xffffffff
            device = os.makedev((tty >> 8) & 0xff, (tty & 0xff) | ((tty >> 12) & 0xfff00))
            return group, foreground, device, start
        before = terminal_owner()
        shell_group, foreground_group, controlling_device, start_ticks = before
        return (not attributes[3] & termios.ICANON
                and foreground_group == shell_group
                and shell_group > 0 and start_ticks > 0
                and held.st_rdev == controlling_device
                and terminal_owner() == before
                and (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
                and expected in _env(pid))
    except (OSError, ValueError, TypeError, IndexError, termios.error):
        return False
    finally:
        if fd is not None:
            os.close(fd)


def pane_input_ready(process_info: dict, marker: str) -> bool:
    """Require the owned host shell's terminal to accept an untruncated command."""
    try:
        pid = int(process_info.get("shell_pid") or 0)
        return (pid > 0
                and os.readlink(f"/proc/{pid}/ns/pid") == os.readlink("/proc/self/ns/pid")
                and _terminal_input_ready(pid, marker))
    except (OSError, ValueError, TypeError):
        return False


def _pane_shell_instance(process_info: dict, marker: str) -> tuple[int, int] | None:
    if not pane_input_ready(process_info, marker):
        return None
    try:
        pid = int(process_info["shell_pid"])
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return pid, int(fields[19])
    except (OSError, ValueError, KeyError, IndexError):
        return None


def verify_pane_prompt(invoke, pane_id: str, marker: str, *, timeout_seconds=10.0,
                       _instance_reader=None) -> None:
    """Prove the owned shell executed a short challenge before sending its launch.

    A startup builtin read shares the shell PID and terminal flags. An encoded,
    fresh nonce cannot match the echoed input; only command execution produces
    the expected complete output line. Never resend a consumed challenge.
    """
    instance_reader = _instance_reader or _pane_shell_instance
    deadline = time.monotonic() + timeout_seconds
    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise RuntimeError("durable_pane_prompt_unverified")
        return value
    def process_info():
        reply = invoke(["pane", "process-info", "--pane", pane_id],
                       timeout_seconds=min(10.0, remaining()))
        info = (reply.get("result") or {}).get("process_info")
        return info if isinstance(info, dict) else {}
    instance = instance_reader(process_info(), marker)
    if instance is None:
        raise RuntimeError("durable_pane_prompt_unverified")
    nonce = "HERDR_PROMPT_" + secrets.token_hex(24)
    encoded = "".join(f"\\x{byte:02x}" for byte in nonce.encode("ascii"))
    challenge = "builtin printf '%b\\n' '" + encoded + "'"
    assert nonce not in challenge and len(challenge.encode()) < 4096
    invoke(["pane", "run", pane_id, challenge], timeout_seconds=min(10.0, remaining()))
    reply = invoke(["pane", "wait-output", pane_id, "--regex", "^" + nonce + "$",
                    "--source", "recent-unwrapped", "--lines", "20",
                    "--timeout", str(max(1, int(remaining() * 1000)))],
                   timeout_seconds=min(10.0, remaining()))
    result = reply.get("result") if isinstance(reply, dict) else None
    read = result.get("read") if isinstance(result, dict) else None
    if (not isinstance(result, dict) or result.get("type") != "output_matched"
            or result.get("pane_id") != pane_id or result.get("matched_line") != nonce
            or not isinstance(read, dict) or read.get("pane_id") != pane_id
            or not isinstance(read.get("text"), str) or nonce not in read["text"].splitlines()
            or type(result.get("revision")) is not int or result["revision"] < 0):
        raise RuntimeError("durable_pane_prompt_unverified")
    while True:
        if instance_reader(process_info(), marker) == instance:
            remaining()
            return
        time.sleep(min(0.05, remaining()))


def _authenticated_agent_instance(receipt, sandbox_pid, marker, agent_name):
    """Bind readiness to the host-authenticated child of the retained shell."""
    from herdr.bootstrap_authority import BootstrapContinuation, inspect_peer
    try:
        if (not isinstance(receipt, BootstrapContinuation)
                or receipt.identity["agent_id"] != agent_name
                or receipt.peer_pid == sandbox_pid):
            return None
        peer = inspect_peer(receipt.peer_pid)
        if (peer.ppid != sandbox_pid or peer.start_ticks != receipt.process_start_ticks
                or (peer.exe_device, peer.exe_inode) != (receipt.python_device, receipt.python_inode)):
            return None
        namespaces = tuple(os.readlink(f"/proc/{peer.pid}/ns/{name}") for name in ("pid", "mnt"))
        if namespaces != tuple(os.readlink(f"/proc/{sandbox_pid}/ns/{name}") for name in ("pid", "mnt")):
            return None
        env = _env(peer.pid)
        if (b"HERDR_DURABLE_SANDBOX=1" not in env
                or f"HERDR_DURABLE_TASK_PANE={marker}".encode() not in env):
            return None
        again = inspect_peer(peer.pid)
        if again != peer:
            return None
        return peer.pid, peer.start_ticks, *namespaces
    except (OSError, ValueError, RuntimeError):
        return None


def start_sandbox_agent(invoke, pane_id: str, marker: str, sandbox_pid: int,
                        agent_name: str, hermes_args: list[str], *,
                        verify_boundary, bootstrap_peer, timeout_seconds=60.0) -> dict:
    """Launch the fixed guarded Hermes entry once inside an attested owned pane.

    Native agent.start requires a bare host shell and rejects an existing bwrap
    boundary. This route proves the inner prompt, sends one fixed executable,
    retains the registered shell, waits for detection, and names its authenticated child.
    The caller must still confirm authenticated bootstrap before task delivery.
    """
    if (not callable(bootstrap_peer) or not callable(verify_boundary)
            or not isinstance(agent_name, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", agent_name)
            or type(sandbox_pid) is not int or sandbox_pid <= 0
            or not isinstance(hermes_args, list)
            or any(not isinstance(arg, str) or any(ord(c) < 32 or ord(c) == 127 for c in arg)
                   for arg in hermes_args)
            or type(timeout_seconds) not in (int, float)
            or not 0 < timeout_seconds <= 75):
        raise RuntimeError("durable_agent_launch_invalid")
    # The sealed bootstrap authorizes a child of the registered shell.
    # Replacing that shell with exec makes the stage-one peer ineligible.
    command = shlex.join(["/run/herdr-bootstrap/hermes", *hermes_args])
    if len(command.encode("utf-8")) >= 4096:
        raise RuntimeError("durable_agent_launch_invalid")
    deadline = time.monotonic() + timeout_seconds
    expected_process = None
    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise RuntimeError("durable_agent_launch_unverified")
        return value
    def process_instance():
        try:
            fields = Path(f"/proc/{sandbox_pid}/stat").read_text().rsplit(")", 1)[1].split()
            return (sandbox_pid, int(fields[19]),
                    os.readlink(f"/proc/{sandbox_pid}/ns/pid"),
                    os.readlink(f"/proc/{sandbox_pid}/ns/mnt"))
        except (OSError, ValueError, IndexError):
            return None
    def boundary():
        if verify_boundary() is not True:
            raise RuntimeError("durable_agent_boundary_unverified")
        if expected_process is not None and process_instance() != expected_process:
            raise RuntimeError("durable_agent_process_changed")
        remaining()
    def pane():
        reply = invoke(["pane", "get", pane_id], timeout_seconds=min(10.0, remaining()))
        result = reply.get("result") if isinstance(reply, dict) else None
        row = result.get("pane") if isinstance(result, dict) else None
        if (not isinstance(row, dict) or row.get("pane_id") != pane_id
                or not isinstance(row.get("terminal_id"), str) or not row["terminal_id"]):
            raise RuntimeError("durable_agent_pane_unverified")
        return row
    boundary()
    initial = pane()
    if initial.get("agent") is not None:
        raise RuntimeError("durable_agent_pane_busy")
    terminal_id = initial["terminal_id"]
    def inner_instance(info, expected_marker):
        boundary()
        if inner_pid(info, expected_marker) != sandbox_pid:
            return None
        if not _terminal_input_ready(sandbox_pid, expected_marker):
            return None
        return process_instance()
    def acknowledged(args, *, timeout_seconds):
        response = invoke(args, timeout_seconds=timeout_seconds)
        if args[:2] == ["pane", "run"] and response is not None:
            raise RuntimeError("durable_agent_input_unacknowledged")
        return response
    # bwrap verification can precede readline's first inner prompt.
    while True:
        reply = invoke(["pane", "process-info", "--pane", pane_id],
                       timeout_seconds=min(10.0, remaining()))
        info = (reply.get("result") or {}).get("process_info") if isinstance(reply, dict) else None
        instance = inner_instance(info, marker) if isinstance(info, dict) else None
        if instance is not None:
            expected_process = instance
            break
        time.sleep(min(0.05, remaining()))
    verify_pane_prompt(acknowledged, pane_id, marker,
                       timeout_seconds=remaining(), _instance_reader=inner_instance)
    boundary()
    current = pane()
    if current["terminal_id"] != terminal_id or current.get("agent") is not None:
        raise RuntimeError("durable_agent_pane_changed")
    acknowledged(["pane", "run", pane_id, command], timeout_seconds=min(10.0, remaining()))
    while True:
        boundary()
        current = pane()
        if current["terminal_id"] != terminal_id:
            raise RuntimeError("durable_agent_pane_changed")
        detected = current.get("agent")
        if detected == "hermes":
            break
        if detected is not None:
            raise RuntimeError("durable_agent_kind_mismatch")
        time.sleep(min(0.05, remaining()))
    boundary()
    reply = invoke(["agent", "rename", pane_id, agent_name],
                   timeout_seconds=min(10.0, remaining()))
    result = reply.get("result") if isinstance(reply, dict) else None
    agent = result.get("agent") if isinstance(result, dict) else None
    if (not isinstance(agent, dict) or agent.get("name") != agent_name
            or agent.get("pane_id") != pane_id or agent.get("terminal_id") != terminal_id
            or agent.get("agent") != "hermes"):
        raise RuntimeError("durable_agent_identity_unverified")
    expected_peer = None
    # Process discovery precedes Hermes' interactive initialization. Keep the
    # task prompt on the host until native screen detection AND the same
    # authenticated child process' noncanonical input terminal are ready.
    while True:
        boundary()
        ready = invoke(["agent", "get", agent_name],
                       timeout_seconds=min(10.0, remaining()))
        result = ready.get("result") if isinstance(ready, dict) else None
        current = result.get("agent") if isinstance(result, dict) else None
        if (not isinstance(current, dict) or current.get("name") != agent_name
                or current.get("pane_id") != pane_id or current.get("terminal_id") != terminal_id
                or current.get("agent") != "hermes"):
            raise RuntimeError("durable_agent_identity_unverified")
        status = current.get("agent_status")
        if status == "blocked":
            raise RuntimeError("durable_agent_startup_blocked")
        if status not in {"idle", "done", "working", "unknown"}:
            raise RuntimeError("durable_agent_status_unverified")
        receipt = bootstrap_peer(timeout_seconds=min(10.0, remaining()))
        peer = _authenticated_agent_instance(receipt, sandbox_pid, marker, agent_name)
        if peer is None or expected_peer is not None and peer != expected_peer:
            raise RuntimeError("durable_agent_bootstrap_peer_unverified")
        expected_peer = peer
        if status in {"idle", "done"} and _terminal_input_ready(peer[0], marker):
            boundary()
            if _authenticated_agent_instance(
                    bootstrap_peer(timeout_seconds=min(10.0, remaining())),
                    sandbox_pid, marker, agent_name) != expected_peer:
                raise RuntimeError("durable_agent_bootstrap_peer_changed")
            return ready
        time.sleep(min(0.05, remaining()))


def inner_pid(process_info: dict, marker: str) -> int | None:
    """Return a process proven to be inside this pane's bwrap namespaces."""
    host_pid_ns = os.readlink("/proc/self/ns/pid")
    host_mnt_ns = os.readlink("/proc/self/ns/mnt")
    candidates: list[int] = []
    for row in process_info.get("foreground_processes") or []:
        if not isinstance(row, dict):
            continue
        try:
            pid = int(row.get("pid") or 0)
        except (TypeError, ValueError):
            continue
        if pid > 0:
            candidates.append(pid)
    try:
        shell_pid = int(process_info.get("shell_pid") or 0)
    except (TypeError, ValueError):
        shell_pid = 0
    if shell_pid > 0:
        candidates.append(shell_pid)

    expected_marker = f"HERDR_DURABLE_TASK_PANE={marker}".encode()
    for pid in candidates:
        try:
            if (
                os.readlink(f"/proc/{pid}/ns/pid") == host_pid_ns
                or os.readlink(f"/proc/{pid}/ns/mnt") == host_mnt_ns
            ):
                continue
            env = _env(pid)
            if b"HERDR_DURABLE_SANDBOX=1" not in env or expected_marker not in env:
                continue
            return pid
        except OSError:
            continue
    return None


def _sdk_runtime_masks_verified(root: Path, modes: dict[str, set[str]],
                                filesystems: dict[str, str]) -> bool:
    """A verified namespace must mask every *present* SDK write directory.

    This independent post-bwrap check rejects a path changed after the
    pre-exec inventory, including a candidate that was absent until launch.
    """
    def inside(path: Path) -> Path:
        return root / str(path).lstrip("/")

    hermes = HOME / ".hermes"
    profiles = hermes / "profiles"
    if inside(hermes).is_symlink() or inside(profiles).is_symlink():
        return False
    roots = [hermes]
    if inside(profiles).is_dir():
        entries = list(inside(profiles).iterdir())
        if len(entries) > 128 or any(p.is_symlink() for p in entries):
            return False
        roots.extend(profiles / p.name for p in entries if p.is_dir())
    paths = [HOME / ".cache"]
    paths.extend(p / name for p in roots for name in ("sessions", "cache", "logs"))
    for path in paths:
        actual = inside(path)
        if actual.is_symlink():
            return False
        if actual.is_dir() and (
            "rw" not in modes.get(str(path), set())
            or filesystems.get(str(path)) != "tmpfs"
        ):
            return False
    return True


def _private_profile_namespace_verified(
    root: Path, modes: dict[str, set[str]],
    filesystems: dict[str, str], snapshot,
) -> bool:
    """Attest selected sealed profile, readonly home and private runtimes.

    This is additional physical evidence; it does not authorize an economic
    attempt, relax the grant, or replace the verified code/worktree mounts.
    """
    from herdr.private_profile_namespace import PrivateProfileSnapshot
    if not isinstance(snapshot, PrivateProfileSnapshot):
        return False
    try:
        snapshot.verify()
        if ("ro" not in modes.get(str(HOME), set())
                or filesystems.get(str(HOME)) != "tmpfs"):
            return False
        profiles_dir = root / str(HOME / ".hermes/profiles").lstrip("/")
        children = list(profiles_dir.iterdir())
        if (len(children) != 1 or children[0].name != snapshot.name
                or children[0].is_symlink() or not children[0].is_dir()):
            return False
        writable = {
            str(snapshot.destination / name)
            for name in ("sessions", "cache", "logs", "pastes")
        }
        for path in writable:
            target = root / path.lstrip("/")
            if (target.is_symlink() or not target.is_dir()
                    or "rw" not in modes.get(path, set())
                    or filesystems.get(path) != "tmpfs"):
                return False
        protected = HOME / ".hermes"
        for mountpath, options in modes.items():
            candidate = Path(mountpath)
            if (candidate == protected or protected in candidate.parents):
                if "rw" in options and mountpath not in writable:
                    return False
        for entry in snapshot.files:
            destination = snapshot.destination / entry.relative
            target = root / str(destination).lstrip("/")
            if (target.is_symlink() or not target.is_file()
                    or "ro" not in modes.get(str(destination), set())
                    or filesystems.get(str(destination)) != "tmpfs"):
                return False
            raw = target.read_bytes()
            if (len(raw) != entry.size
                    or hashlib.sha256(raw).hexdigest() != entry.sha256):
                return False
        return True
    except (OSError, RuntimeError, ValueError, IndexError):
        return False


def verify(
    pid: int,
    real_binary: Path,
    marker: str,
    *,
    policy: Path = POLICY,
    attempts: int = 30,
    pinned_worktree: PinnedWorktree | None = None,
    child_workspace_writable: bool | None = None,
    policy_mount=None,
    owned_write_pins=None,
    private_profile_snapshot=None,
) -> bool:
    """Require expected mounts, hidden Herdr paths and non-host namespaces."""
    # The kernel records the canonical destination when the CLI is a symlink.
    canonical_binary = real_binary.resolve(strict=True)
    expected = {str(canonical_binary), str(HERDR_CONFIG), str(HERDR_RELEASES)}
    if pinned_worktree is not None:
        expected.add(str(pinned_worktree.logical))
    for _ in range(attempts):
        try:
            root = Path(f"/proc/{pid}/root")
            mounts = Path(f"/proc/{pid}/mountinfo").read_text(encoding="utf-8")
            rows = [line.split(" - ", 1)[0].split() for line in mounts.splitlines()]
            def unescape(value):
                for old, new in ((r"\040", " "), (r"\011", "\t"),
                                 (r"\012", "\n"), (r"\134", "\\")):
                    value = value.replace(old, new)
                return value
            modes = {unescape(row[4]): set(row[5].split(",")) for row in rows}
            filesystems = {
                unescape(line.split(" - ", 1)[0].split()[4]):
                    line.split(" - ", 1)[1].split()[0]
                for line in mounts.splitlines()
            }
            targets = set(modes)
            workspace_matches = True
            if pinned_worktree is not None:
                pinned_worktree.verify()
                mounted = (root / str(pinned_worktree.logical).lstrip("/")).stat()
                expected_mode = "rw" if child_workspace_writable is True else "ro"
                workspace_matches = (
                    (mounted.st_dev, mounted.st_ino) == (pinned_worktree.device, pinned_worktree.inode)
                    and expected_mode in modes.get(str(pinned_worktree.logical), set()))
            if owned_write_pins is not None:
                owned_write_pins.verify_mounted(pid,modes)
            if policy_mount is not None:
                policy_mount.verify_mounted(pid)
            env = _env(pid)
            config = root / str(HERDR_CONFIG).lstrip("/")
            releases = root / str(HERDR_RELEASES).lstrip("/")
            hidden = (config.is_dir() and not any(config.iterdir())
                      and releases.is_dir() and not any(releases.iterdir()))
            policy_matches = (
                root / str(canonical_binary).lstrip("/")
            ).read_bytes() == policy.read_bytes()
            ns = (
                os.readlink(f"/proc/{pid}/ns/pid") != os.readlink("/proc/self/ns/pid")
                and os.readlink(f"/proc/{pid}/ns/mnt") != os.readlink("/proc/self/ns/mnt")
            )
            if (
                expected <= targets
                and "ro" in modes.get("/", set())
                and workspace_matches
                and (policy_mount is None or _sdk_runtime_masks_verified(
                    root, modes, filesystems))
                and (private_profile_snapshot is None
                     or _private_profile_namespace_verified(
                         root, modes, filesystems, private_profile_snapshot))
                and hidden
                and policy_matches
                and ns
                and b"HERDR_DURABLE_SANDBOX=1" in env
                and f"HERDR_DURABLE_TASK_PANE={marker}".encode() in env
            ):
                return True
        except (OSError, ValueError, IndexError, RuntimeError):
            pass
        time.sleep(0.1)
    return False
