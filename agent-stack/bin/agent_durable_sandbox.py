"""Construct and verify the durable task pane's mount and PID boundary."""
from herdr.observed_proc import os
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
from herdr.observed_proc import Path

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

# Root launch authorities read the exact native argv from /proc.  Keep that
# independently bounded from the shell text carried by pane.run: shell quoting
# can expand a safe argv substantially without changing the launched process.
MAX_HOST_LAUNCH_ARGV_BYTES = 32768
MAX_PANE_SHELL_COMMAND_BYTES = 65536


def _argv_bytes(args: list[str]) -> int:
    return sum(len(value.encode("utf-8")) + 1 for value in args)


def _bounded_host_command(args: list[str]) -> list[str]:
    if _argv_bytes(args) > MAX_HOST_LAUNCH_ARGV_BYTES:
        raise RuntimeError("durable_sandbox_host_argv_too_large")
    return args


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
import ctypes
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
system_runtime_files = set(__HERDR_SYSTEM_RUNTIME_FILES__)
plan_envelope = None
received_fds = []
if isinstance(entries, dict):
    plan_envelope = entries
    base_keys = {"schema_version", "authority", "authority_sha256", "entries"}
    if (set(entries) not in (base_keys, base_keys | {"transport"})
        or ("transport" in entries and entries["transport"] != "herdr-native-fd-handoff-1")
        or entries["schema_version"] != "herdr-private-mount-plan-1"):
        raise SystemExit("policy_fd_private_plan_invalid")
    entries = entries["entries"]
if not isinstance(entries, list) or not 1 <= len(entries) <= 96:
    raise SystemExit("policy_fd_launch_invalid")
if plan_envelope is not None and "transport" in plan_envelope:
    # This source tree is selected by the approved launcher.  -I -S removes
    # ambient imports, so admit only this exact sibling package directory.
    package_root = Path(__HERDR_PACKAGE_ROOT__)
    if not package_root.is_absolute() or package_root.name != 'herdr':
        raise SystemExit('policy_fd_package_root_invalid')
    sys.path.insert(0, str(package_root.parent))
    from herdr.native_fd_handoff import receive_descriptors
    received_fds = receive_descriptors(plan_envelope, args)
mapping, targets, approved_files = {}, set(), set()
profile_name = None
total_profile_bytes = 0
for source_index, item in enumerate(entries):
    if not isinstance(item, dict):
        raise SystemExit("policy_fd_launch_invalid")
    kind = item.get("kind")
    sealed_profile = kind == "sealed-profile-data"
    sealed_resolver = kind == "sealed-resolver-data"
    sealed = sealed_profile or sealed_resolver
    reserved = kind == "reserved-result"
    ordinary = {"source", "fd", "device", "inode", "kind", "target"}
    expected_keys = ordinary | ({"sha256", "size"} if sealed else {"reservation"} if reserved else set())
    if set(item) != expected_keys:
        raise SystemExit("policy_fd_launch_invalid")
    if (any(type(item[k]) is not int or item[k] < 0
            for k in ("fd", "device", "inode"))
        or kind not in ("file", "directory", "socket", "sealed-profile-data", "sealed-resolver-data", "reserved-result")
        or not isinstance(item["source"], str)
        or not re.fullmatch(r"/proc/[1-9][0-9]{0,9}/fd/[0-9]{1,10}", item["source"])
        or item["source"].rsplit("/", 1)[-1] != str(item["fd"])
        or not isinstance(item["target"], str)
        or not item["target"].startswith("/")
        or item["fd"] in mapping or item["target"] in targets):
        raise SystemExit("policy_fd_launch_invalid")
    if sealed_profile:
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
    if sealed_resolver:
        size, digest = item["size"], item["sha256"]
        if (plan_envelope is None or item["target"] not in {"/etc/resolv.conf",
            "/run/systemd/resolve/stub-resolv.conf", "/run/systemd/resolve/resolv.conf"}
            or type(size) is not int or not 0 < size <= 16384
            or not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None):
            raise SystemExit("policy_fd_resolver_manifest_invalid")
    opened = os.open(
        f"/proc/self/fd/{received_fds[source_index]}" if received_fds else item["source"],
        (os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK) if sealed or reserved
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
    if reserved:
        binding=item["reservation"]
        expected={"schema_version","path","device","inode","identity_sha256","idempotency_key","max_bytes"}
        if (not isinstance(binding,dict) or set(binding)!=expected
            or binding["schema_version"]!="herdr-result-reservation-1"
            or binding["path"]!=item["target"] or binding["device"]!=held.st_dev or binding["inode"]!=held.st_ino
            or any(type(binding[key]) is not int for key in ("device","inode"))
            or held.st_uid!=os.geteuid() or held.st_nlink!=1 or held.st_mode&0o777!=0o600 or held.st_size!=0
            or not isinstance(binding["identity_sha256"],str) or re.fullmatch("[0-9a-f]{64}",binding["identity_sha256"]) is None
            or not isinstance(binding["idempotency_key"],str) or re.fullmatch("[A-Za-z0-9._:/+-]{1,256}",binding["idempotency_key"]) is None
            or type(binding["max_bytes"]) is not int or not 1024<=binding["max_bytes"]<=131072):
            raise SystemExit("policy_fd_result_reservation_changed")
        expected_bytes=json.dumps(binding,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
        try:
            valid=(os.getxattr(opened,"user.herdr.result_reservation")==expected_bytes
                   and "user.herdr.result_submission" not in os.listxattr(opened))
        except OSError:valid=False
        stamp=lambda value:(value.st_dev,value.st_ino,value.st_uid,value.st_mode,value.st_nlink,
                            value.st_size,value.st_ctime_ns,value.st_mtime_ns)
        valid=valid and stamp(os.fstat(opened))==stamp(held)
        if not valid:raise SystemExit("policy_fd_result_reservation_changed")
        parent_fd=os.open("/",os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
        named_fd=-1
        try:
            target_path=Path(item["target"])
            if os.path.normpath(item["target"])!=item["target"]:raise ValueError("noncanonical result")
            class OpenHow(ctypes.Structure):
                _fields_=[("flags",ctypes.c_uint64),("mode",ctypes.c_uint64),("resolve",ctypes.c_uint64)]
            libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long
            how=OpenHow(os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC,0,0x2|0x4|0x8)
            named_fd=libc.syscall(437,parent_fd,ctypes.c_char_p(os.fsencode(target_path.relative_to('/').as_posix())),
                                  ctypes.byref(how),ctypes.sizeof(how))
            if named_fd<0:raise OSError(ctypes.get_errno(),"result lookup denied")
            named=os.fstat(named_fd)
            if (not stat.S_ISREG(named.st_mode) or (named.st_dev,named.st_ino)!=(held.st_dev,held.st_ino)
                or os.readlink(f"/proc/self/fd/{named_fd}")!=item["target"]):
                raise ValueError("result logical inode changed")
        except (OSError,ValueError):raise SystemExit("policy_fd_result_reservation_changed")
        finally:
            if named_fd>=0:os.close(named_fd)
            os.close(parent_fd)
        if plan_envelope is None:raise SystemExit("policy_fd_private_plan_required")
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
for received in received_fds:
    os.close(received)

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
            or (arg == "--ro-bind-data") != (kind in ("sealed-profile-data", "sealed-resolver-data"))):
            raise SystemExit("policy_fd_launch_invalid")
        if kind in ("sealed-profile-data", "sealed-resolver-data"):
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
private_home = str(home) in tmpfs_targets and (
    bool(approved_files) or plan_envelope is not None)
if private_home:
    if (plan_envelope is not None or any(item["kind"] != "sealed-profile-data" for item in entries)
        or any(args[i] in ("--bind", "--ro-bind") and i != 1
               for i in range(arg_end))):
        # A caller's inode tuples are claims, not host approval. Require the
        # exact descriptor and argv plan published by the existing root host
        # authority. The worker cannot create this record or self-approve it.
        if plan_envelope is None:
            raise SystemExit("policy_fd_private_plan_required")
        authority = Path(plan_envelope["authority"])
        if authority.parent != Path("/etc/herdr/launch-plans"):
            raise SystemExit("policy_fd_private_plan_untrusted")
        for parent_path in (*reversed(authority.parents), authority):
            info = os.lstat(parent_path)
            if (info.st_uid != 0 or info.st_mode & 0o022
                or not (stat.S_ISREG(info.st_mode) if parent_path == authority
                        else stat.S_ISDIR(info.st_mode))):
                raise SystemExit("policy_fd_private_plan_untrusted")
        authority_fd = os.open(authority, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            before = os.fstat(authority_fd)
            raw = os.read(authority_fd, 65537)
            after = os.fstat(authority_fd)
            if not 0 < len(raw) <= 65536 or os.read(authority_fd, 1):
                raise SystemExit("policy_fd_private_plan_invalid")
            stamp = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns, x.st_ctime_ns, x.st_uid, x.st_mode)
            if stamp(before) != stamp(after) or stamp(before) != stamp(os.lstat(authority)):
                raise SystemExit("policy_fd_private_plan_changed")
            approved_plan = json.loads(raw)
        finally:
            os.close(authority_fd)
        canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"),
                                             ensure_ascii=False, allow_nan=False).encode()
        # Restore the original FD tokens for the root-approved argv digest:
        # descriptor duplication above changes local numbers, never authority.
        original_args = sys.argv[2:]
        if (not isinstance(approved_plan, dict)
            or set(approved_plan) != {"schema_version", "identity", "descriptors", "argv_sha256", "writable_targets"}
            or approved_plan["schema_version"] != "herdr-private-mount-plan-1"
            or approved_plan["descriptors"] != entries
            or approved_plan["argv_sha256"] != hashlib.sha256(canonical(original_args)).hexdigest()
            or hashlib.sha256(canonical(approved_plan)).hexdigest() != plan_envelope["authority_sha256"]):
            raise SystemExit("policy_fd_private_plan_mismatch")
        writes = sorted(original_args[i + 2] for i in range(arg_end - 2)
                        if original_args[i] == "--bind-fd")
        if approved_plan["writable_targets"] != writes:
            raise SystemExit("policy_fd_private_plan_mode_mismatch")
        identity_env = {"consumer": "HERDR_POLICY_CONSUMER", "agent_id": "HERDR_POLICY_AGENT_ID",
                        "parent_agent_id": "HERDR_POLICY_PARENT_AGENT_ID", "parent_task_id": "HERDR_POLICY_PARENT_TASK_ID",
                        "task_id": "HERDR_POLICY_TASK_ID", "run_token": "HERDR_POLICY_RUN_TOKEN",
                        "fencing_token": "HERDR_POLICY_FENCING_TOKEN"}
        if (not isinstance(approved_plan["identity"], dict)
            or set(approved_plan["identity"]) != set(identity_env)
            or any(str(approved_plan["identity"][field]) != os.environ.get(key)
                   for field, key in identity_env.items())
            or authority.name != hashlib.sha256(canonical(approved_plan["identity"])).hexdigest() + ".json"):
            raise SystemExit("policy_fd_private_plan_identity_mismatch")
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
    if args[:3] != ["/usr/bin/bwrap", "--tmpfs", "/"]:
        raise SystemExit("policy_fd_private_home_base_invalid")
    try:
        end = args.index("--")
    except ValueError:
        raise SystemExit("policy_fd_launch_invalid")
    # All private-home launches use a closed bwrap grammar. Never accept
    # --args: recursive option expansion bypasses ordinary mount validation.
    # Deny capability grants, alternate PID namespaces, fail-open modes and
    # new options unless independently audited and added to this contract.
    flags = {"--unshare-user", "--unshare-pid", "--die-with-parent", "--unshare-net",
             "--disable-userns"}
    path_options = {"--dev", "--proc", "--tmpfs", "--dir", "--chdir",
                    "--remount-ro"}
    one_value = path_options | {"--unsetenv", "--cap-drop"}
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
        if option == "--cap-drop" and values != ["ALL"]:
            raise SystemExit("policy_fd_private_capability_invalid")
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
        if (option == "--ro-bind" and source_text == destination_text
            and source_text in system_runtime_files):
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
    if (sum(option == "--unshare-user" for option, _, _ in parsed) != 1
        or sum(option == "--disable-userns" for option, _, _ in parsed) != 1
        or sum(option == "--cap-drop" and value == ["ALL"]
               for option, value, _ in parsed) != 1):
        raise SystemExit("policy_fd_private_lifetime_boundary_missing")
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
    if (args[end - 4:end] != ["--remount-ro", str(home), "--remount-ro", "/"]
        or sum(op == "--remount-ro" and value == [str(home)]
               for op, value, _ in parsed) != 1
        or sum(op == "--remount-ro" and value == ["/"]
               for op, value, _ in parsed) != 1
        or any(op == "--remount-ro" and value[0] not in tmpfs_targets
               for op, value, _ in parsed)):
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
            if destination in home.parents and not (i == 1 and arg == "--tmpfs"
                                                    and destination == Path("/")):
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
    # Literal mounts cannot inherit authority from a plan's claimed target.
    # Check them before classifying the exact pinned system-runtime sequence.
    for option, values, position in parsed:
        if option not in ("--bind", "--ro-bind"):
            continue
        if (option == "--ro-bind" and values[0] == values[1]
                and values[0] in system_runtime_files):
            continue
        raise SystemExit("policy_fd_private_literal_source_unpinned")
    runtime_bindings = [(value[0], value[1]) for option, value, _ in parsed
                        if option == "--ro-bind" and value[0] in system_runtime_files]
    if runtime_bindings != [(name, name) for name in sorted(system_runtime_files)]:
        raise SystemExit("policy_fd_system_runtime_mounts_incomplete")

    # All FD-backed mounts must also be host-policy destinations, not just
    # correct caller-supplied inode tuples. Without this check an attacker can
    # re-export the host /proc, HOME or credential subtree under /mnt/alias.
    # The *opened* FD path (not a caller-supplied "source" string) is checked.
    workspace_dirs = [v[0] for op, v, _ in parsed if op == "--chdir"]
    ordinary_entries = [item for item in entries
                        if item["kind"] not in ("sealed-profile-data", "sealed-resolver-data")]
    # Disposable no-agent kernel tests may carry only sealed file data.
    # Any launch with ordinary code/workspace FDs requires an exact cwd.
    if len(workspace_dirs) > 1 or (ordinary_entries and len(workspace_dirs) != 1):
        raise SystemExit("policy_fd_private_workspace_invalid")
    workspace = Path(workspace_dirs[0]) if workspace_dirs else None
    sensitive = (Path("/"), Path("/home"), home, root,
                 home / ".ssh", home / ".aws", home / ".gnupg",
                 home / ".config", home / ".kube", Path("/proc"))
    if workspace is not None and any(workspace == p or p in workspace.parents
                                    for p in sensitive[3:]):
        raise SystemExit("policy_fd_private_workspace_sensitive")
    approved_dir_targets = {
        Path("/run/herdr/policy-code"),
        Path("/run/herdr-bootstrap"),
        root / "hermes-agent",
        home / ".local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu",
        workspace,
    }
    approved_file_targets = {
        Path("/run/herdr-policy/grant.bundle.json"),
        home / ".local/bin/herdr",
        home / ".local/bin/hermes",
    }
    if plan_envelope is not None and workspace is not None:
        approved_dir_targets.update(Path(e["target"]) for e in approved_plan["descriptors"]
                                    if e["kind"] == "directory"
                                    and workspace in Path(e["target"]).parents)
        approved_file_targets.update(Path(e["target"]) for e in approved_plan["descriptors"]
                                     if e["kind"] == "file"
                                     and workspace in Path(e["target"]).parents)
    approved_socket_targets = {
        Path("/run/herdr-policy/bootstrap-authority.sock"),
    }
    for item in entries:
        if item["kind"] in ("sealed-profile-data", "sealed-resolver-data"):
            continue
        target = Path(item["target"])
        allowed = {
            "directory": approved_dir_targets,
            "file": approved_file_targets,
            "reserved-result": approved_file_targets,
            "socket": approved_socket_targets,
        }[item["kind"]]
        if (target not in allowed and not (item["kind"] == "reserved-result"
            and plan_envelope is not None and target not in sensitive
            and not any(root_path in target.parents for root_path in sensitive[3:]))):
            raise SystemExit("policy_fd_private_fd_target_untrusted")
        bind_mode = next(op for op, value, _ in parsed
                         if op in ("--bind-fd", "--ro-bind-fd")
                         and value == [str(mapping[item["fd"]][0]), str(target)])
        if (target in {Path("/run/herdr/policy-code"), Path("/run/herdr-bootstrap"),
                      root / "hermes-agent", home / ".local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu",
                      Path("/run/herdr-policy/grant.bundle.json"),
                      Path("/run/herdr-policy/bootstrap-authority.sock")}
            or re.fullmatch(r"/home/agentops/\.local/(?:bin/[^/]+|share/uv/tools/.+)", str(target))):
            if bind_mode != "--ro-bind-fd":
                raise SystemExit("policy_fd_private_authority_writable")
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
            if (target == workspace or item["kind"]=="reserved-result") and path != target:
                raise SystemExit("policy_fd_private_fd_source_untrusted")
    # The pinned FD is the only source Bubblewrap may mount; pathname
    # swaps performed after this check cannot alter that inode's identity.
else:
    if (str(home) in tmpfs_targets
        or args[:4] == ["/usr/bin/bwrap", "--ro-bind", "/", "/"]):
        # The host may have a different account home (e.g. /home/runner).
        # Construct HOME beneath a private /home instead of trying to mkdir
        # on the read-only host root. Never rebind the host home inventory.
        # Seal both private bases after every child mount, nonrecursively.
        if (args[:8] != ["/usr/bin/bwrap", "--ro-bind", "/", "/",
                         "--tmpfs", str(home.parent), "--tmpfs", str(home)]
            or tmpfs_targets.count(str(home.parent)) != 1
            or tmpfs_targets.count(str(home)) != 1
            or args[arg_end - 4:arg_end] != ["--remount-ro", str(home.parent),
                                            "--remount-ro", str(home)]):
            raise SystemExit("policy_fd_runtime_home_not_readonly")
        home_environment = [args[i + 1:i + 3] for i in range(arg_end - 2)
                            if args[i] == "--setenv" and args[i + 1] == "HOME"]
        if (home_environment != [["HOME", str(home)]]
            or any(args[i:i + 2] == ["--unsetenv", "HOME"]
                   for i in range(arg_end - 1))):
            raise SystemExit("policy_fd_runtime_home_env_invalid")
    if any(item["kind"] == "sealed-resolver-data" for item in entries):
        raise SystemExit("policy_fd_resolver_without_private_home")
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
if approved_files:
    # This audited fixed filter is added after validating the root-approved
    # mount command. Bubblewrap installs it before the waiting shell; all
    # descendant forks and execs inherit it. No worker input selects rules.
    # The exact program is embedded by this pinned source module before an
    # isolated -S manual launcher starts; that launcher has no import path.
    if os.uname().machine != "x86_64":
        raise SystemExit("policy_fd_filter_architecture_unsupported")
    program = bytes.fromhex("__HERDR_FIXED_INGRESS_FILTER_HEX__")
    filter_fd = os.memfd_create("herdr-credential-ingress-filter",
                                os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    if os.write(filter_fd, program) != len(program):
        raise SystemExit("policy_fd_filter_incomplete")
    fcntl.fcntl(filter_fd, getattr(fcntl, "F_ADD_SEALS", 1033),
                getattr(fcntl, "F_SEAL_SEAL", 1) | getattr(fcntl, "F_SEAL_SHRINK", 2) |
                getattr(fcntl, "F_SEAL_GROW", 4) | getattr(fcntl, "F_SEAL_WRITE", 8))
    os.lseek(filter_fd, 0, os.SEEK_SET)
    os.set_inheritable(filter_fd, True)
    args[arg_end:arg_end] = ["--seccomp", str(filter_fd)]
    # Drop a possible host cwd and every host descriptor that is not an exact
    # mount source or the fixed filter BEFORE bwrap drops capabilities.
    os.chdir("/")
    kept = {0, 1, 2, filter_fd, *(opened for opened, _, _ in mapping.values())}
    for name in os.listdir("/proc/self/fd"):
        if name.isdecimal() and int(name) not in kept:
            try:
                os.close(int(name))
            except OSError as exc:
                if exc.errno != 9:  # listdir may have closed its own FD.
                    raise
os.execv(args[0], args)
"""

# This replacement is performed by the verified candidate source before the
# command is formed; the host-approved argv binds the resulting exact bytes.
from herdr.credential_ingress_filter import filter_bytes as _ingress_filter_bytes
from herdr.credential_isolation import SYSTEM_RUNTIME_FILES as _system_runtime_files
_POLICY_FD_LAUNCHER = _POLICY_FD_LAUNCHER.replace(
    "__HERDR_FIXED_INGRESS_FILTER_HEX__", _ingress_filter_bytes().hex())
_POLICY_FD_LAUNCHER = _POLICY_FD_LAUNCHER.replace(
    "__HERDR_SYSTEM_RUNTIME_FILES__", repr(sorted(_system_runtime_files)))
_POLICY_FD_LAUNCHER = _POLICY_FD_LAUNCHER.replace(
    "__HERDR_PACKAGE_ROOT__", repr(str(Path(__file__).resolve().parents[2] / 'herdr')))

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
    root_workspace_writable: bool | None = None,
    pinned_worktree: PinnedWorktree | None = None,
    policy_mount=None,
    owned_write_pins=None,
    admission_root: Path | None = None,
    private_profile_snapshot=None,
    hermes_profile: str | None = None,
) -> list[str]:
    if root_workspace_writable is not None and (
        type(root_workspace_writable) is not bool or child_workspace_writable is not None
        or private_profile_snapshot is None or policy_mount is None):
        raise RuntimeError("private_root_workspace_mode_required")
    workspace_writable = (child_workspace_writable is not False
        if root_workspace_writable is None else root_workspace_writable)
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
        pinned_worktree = pinned_worktree or getattr(policy_mount, "private_workspace_pin", None)
        private_result_pin = getattr(policy_mount, "private_result_pin", None)
        if (pinned_worktree is None
            or writable and (private_result_pin is None
                             or tuple(map(Path, writable)) != (private_result_pin.logical,))):
            raise RuntimeError("durable_private_profile_sources_unpinned")
        from herdr.policy_launch import PolicyMount
        from herdr.security import SecurityError
        # A readonly bind of an agentops-owned snapshot is mutable *from the
        # host* even when its contents passed SHA checks at launch. Only
        # complete root-published source trees can back a private profile.
        if not isinstance(policy_mount, PolicyMount):
            raise RuntimeError("durable_private_runtime_not_immutable")
        try:
            policy_mount.require_immutable_runtime()
        except SecurityError as exc:
            raise RuntimeError("durable_private_runtime_not_immutable") from exc
        private_profile_mounts = private_profile_snapshot.mount_arguments()
        from herdr.private_mount_plan import isolated_destination_anchor
        destinations = [Path(workspace), *map(Path, writable)]
        anchors = {isolated_destination_anchor(path) for path in destinations}
        private_anchors = sorted((p for p in anchors if p != HOME and p != Path("/tmp")
                                  and not any(q != p and q in p.parents for q in anchors)), key=str)
        private_destination_setup = []
        for anchor in private_anchors:
            private_destination_setup.extend(("--tmpfs", str(anchor)))
        for path in sorted({Path(workspace), *(Path(p).parent for p in writable)}, key=str):
            private_destination_setup.extend(("--dir", str(path)))
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
                not (child_workspace_writable is False and root_workspace_writable is None
                     or root_workspace_writable is False and child_workspace_writable is None)
                or policy_mount is None):
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

    # Private launch starts with an empty root and exact approved runtime
    # files. Other host paths, including sibling workspaces, do not exist.
    # Legacy launch retains its historical read-only root.
    # managed children retain their separate admitted workspace mode.
    # Mask control paths after writable binds and over-mount the local CLI.
    args = [
        str(BWRAP),
        *(["--tmpfs", "/"] if private_profile_mounts else ["--ro-bind", "/", "/"]),
        # /home exists on the host, but the fixed account home need not.
        # A private parent permits destination creation and hides other homes.
        *(["--tmpfs", str(HOME.parent), "--tmpfs", str(HOME)]
          if policy_mount is not None and not private_profile_mounts else []),
        *((part for name in sorted(_system_runtime_files) for part in
           ("--ro-bind", name, name)) if private_profile_mounts else []),
        "--dev", "/dev",
        *(["--unshare-user"] if private_profile_mounts else []),
        "--unshare-pid",
        *(["--disable-userns", "--cap-drop", "ALL"] if private_profile_mounts else []),
        *(["--die-with-parent"] if admission_root is not None else []),
        "--tmpfs", "/tmp",
        *(private_profile_mounts[:-2] if private_profile_mounts else []),
        *(private_destination_setup if private_profile_mounts else []),
        *([] if pinned_worktree is None or private_profile_mounts else
          ["--tmpfs", str(workspace.parent), "--dir", str(workspace)]),
        (("--bind-fd" if workspace_writable else "--ro-bind-fd")
         if pinned_worktree else
         ("--bind" if workspace_writable else "--ro-bind")),
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
        if private_profile_snapshot is not None:
            private_result_pin.verify()
            args += ["--bind-fd", str(private_result_pin.fd), str(path)]
        else:
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
        if private_profile_snapshot is not None:
            from herdr.policy_launch import _open_relative
            source = "agent-stack/policy-bin/herdr"
            if source not in dict(policy_mount.code.files):
                raise RuntimeError("durable_private_cli_artifact_unapproved")
            key = str(path)
            if key not in policy_mount.private_cli_pins:
                policy_mount.private_cli_pins[key] = _open_relative(policy_mount.code.fd, source)
            args += ["--ro-bind-fd", str(policy_mount.private_cli_pins[key]), str(path)]
        else:
            args += ["--ro-bind", str(policy), str(path)]
    if policy_mount is not None:
        # Public DNS must survive the private /run mask without exposing host runtime data.
        if private_profile_snapshot is not None and policy_mount.resolver_snapshot is None:
            from herdr.resolver_namespace import ResolverSnapshot
            policy_mount.resolver_snapshot = ResolverSnapshot.create()
        # Host-only immutable copies override mutable checkout/runtime aliases.
        descriptors = policy_mount.descriptors()
        if owned_write_pins is not None:descriptors.extend(owned_write_pins.descriptors())
        if private_profile_snapshot is not None:
            if private_result_pin is not None:
                descriptors.append(private_result_pin.descriptor())
            for target, fd in policy_mount.private_cli_pins.items():
                held = os.fstat(fd)
                descriptors.append({"source": f"/proc/{os.getpid()}/fd/{fd}", "fd": fd,
                                    "device": held.st_dev, "inode": held.st_ino,
                                    "kind": "file", "target": target})
            descriptors.extend(private_profile_snapshot.fd_descriptors())
        args += ["--tmpfs", "/run", "--dir", "/run/herdr", "--dir", "/run/herdr-policy"]
        if policy_mount.resolver_snapshot is not None:
            args += policy_mount.resolver_snapshot.parent_args()
        for entry in policy_mount.descriptors():
            option = "--ro-bind-data" if entry["kind"] == "sealed-resolver-data" else "--ro-bind-fd"
            args += [option, str(entry["fd"]), entry["target"]]
        from herdr.launch_environment import STARTUP_CONTROLS
        for name in sorted(set(STARTUP_CONTROLS)|{key for key in os.environ if key.startswith("LD_")}):
            args += ["--unsetenv",name]
        args += ["--setenv", "PATH", "/run/herdr/policy-code/agent-stack/policy-bin:/usr/bin:/bin"]
        if not private_profile_mounts:
            args += ["--setenv", "HOME", str(HOME)]
    args += [
        "--setenv", "HERDR_DURABLE_SANDBOX", "1",
        *(part for anchor in (private_anchors if private_profile_mounts else [])
          for part in ("--remount-ro", str(anchor))),
        *(private_profile_mounts[-2:] if private_profile_mounts else []),
        *(["--remount-ro", str(HOME.parent), "--remount-ro", str(HOME)]
          if policy_mount is not None and not private_profile_mounts else []),
        *(["--remount-ro", "/"] if private_profile_mounts else []),
        "--", "/bin/bash", "--noprofile", "--norc", "-i",
    ]
    if policy_mount is not None:
        if pinned_worktree is not None:
            descriptors.insert(0, {"source": pinned_worktree.source, "fd": pinned_worktree.fd,
                                  "device": pinned_worktree.device, "inode": pinned_worktree.inode,
                                  "kind": "directory", "target": str(pinned_worktree.logical)})
        if private_profile_snapshot is not None:
            from herdr.private_mount_plan import request_for, ApprovedPrivateMountPlan
            policy_mount.private_mount_request = request_for(policy_mount.private_identity, descriptors, args)
            policy_mount.private_mount_argv = list(args)
            plan = policy_mount.private_mount_plan
            if not isinstance(plan, ApprovedPrivateMountPlan):
                raise RuntimeError("durable_private_mount_plan_unapproved")
            descriptors = plan.authorize(descriptors, args)
        if getattr(policy_mount, "private_fd_handoff", False):
            from herdr.native_fd_handoff import VERSION, ENTRYPOINT
            from herdr.launch_plan_issuer import HOST_ENTRYPOINT
            from herdr.host_bootstrap import PYTHON_TARGET, PYTHON_EXECUTABLE
            policy_mount.require_immutable_runtime()
            if ENTRYPOINT not in dict(policy_mount.code.files):
                raise RuntimeError("native_descriptor_entrypoint_unapproved")
            descriptors = {**descriptors, "transport": VERSION}
            python = next(tree for tree in policy_mount.runtime if tree.target == PYTHON_TARGET)
            result_command = _bounded_host_command([str(python.path / PYTHON_EXECUTABLE), "-I", "-B",
                str(policy_mount.code.path / HOST_ENTRYPOINT), ENTRYPOINT,
                json.dumps(descriptors, separators=(",", ":")), *args])
        else:
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


def shell_command(args: list[str]) -> str:
    from herdr.launch_environment import STARTUP_CONTROLS
    controls=sorted(set(STARTUP_CONTROLS)|{key for key in os.environ
                    if key.startswith("LD_") and key.replace("_","").isalnum()})
    rendered = "unset " + " ".join(map(shlex.quote,controls)) + "; exec " + shlex.join(args)
    # Herdr pane.run carries the rendered shell text as one argv element. Its
    # byte bound is deliberately separate from the native host argv bound:
    # shlex quoting is transport syntax and can be much larger than /proc argv.
    if len(rendered.encode("utf-8")) > MAX_PANE_SHELL_COMMAND_BYTES:
        raise RuntimeError("durable_sandbox_shell_command_too_large")
    return rendered


def _env(pid: int) -> set[bytes]:
    return set(Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"))


def _terminal_input_ready(pid: int, marker: str) -> bool:
    """Require the marked process to own an active, noncanonical foreground TTY."""
    from herdr.observed_proc import native_scope_enabled, _DIRECT, rpc
    if native_scope_enabled() and not _DIRECT.get():
        return rpc(pid, '', 'terminal')[0]['ready']
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
    command = shlex.join(["/run/herdr/policy-code/agent-stack/policy-bin/hermes", *hermes_args])
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


def _runtime_home_mounts_verified(mounts: str) -> bool:
    """Attest both generic HOME bases from uncollapsed kernel mount records."""
    bases = {str(HOME.parent): [], str(HOME): []}
    try:
        for line in mounts.splitlines():
            left, right = line.split(" - ", 1)
            row = left.split()
            if row[4] in bases:
                bases[row[4]].append((set(row[5].split(",")), right.split()[0]))
        return all(len(records) == 1 and "ro" in records[0][0]
                   and "rw" not in records[0][0] and records[0][1] == "tmpfs"
                   for records in bases.values())
    except (ValueError, IndexError):
        return False


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
        for entry in snapshot.sdk_files:
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
                and (policy_mount is None or private_profile_snapshot is not None
                     or (_runtime_home_mounts_verified(mounts)
                         and f"HOME={HOME}".encode() in env))
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
