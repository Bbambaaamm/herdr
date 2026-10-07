"""Construct and verify the durable task pane's mount and PID boundary."""
import os
import json
import shlex
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


_POLICY_FD_LAUNCHER = '\nimport json, os, re, stat, sys\nif len(sys.argv) < 3 or len(sys.argv[1]) > 65536:\n    raise SystemExit("policy_fd_launch_invalid")\nentries = json.loads(sys.argv[1])\nargs = sys.argv[2:]\nif not isinstance(entries, list) or not 1 <= len(entries) <= 72:\n    raise SystemExit("policy_fd_launch_invalid")\nmapping, targets = {}, set()\nfor item in entries:\n    if not isinstance(item, dict) or set(item) != {"source","fd","device","inode","kind","target"}:\n        raise SystemExit("policy_fd_launch_invalid")\n    if (any(type(item[k]) is not int or item[k] < 0 for k in ("fd","device","inode")) or\n        item["kind"] not in ("file","directory","socket") or\n        not isinstance(item["source"], str) or\n        not re.fullmatch(r"/proc/[1-9][0-9]{0,9}/fd/[0-9]{1,10}", item["source"]) or\n        item["source"].rsplit("/",1)[-1] != str(item["fd"]) or\n        not isinstance(item["target"], str) or not item["target"].startswith("/") or\n        item["fd"] in mapping or item["target"] in targets):\n        raise SystemExit("policy_fd_launch_invalid")\n    opened = os.open(item["source"], os.O_PATH | (os.O_DIRECTORY if item["kind"] == "directory" else 0))\n    held = os.fstat(opened)\n    kind = {"directory":stat.S_ISDIR,"file":stat.S_ISREG,"socket":stat.S_ISSOCK}[item["kind"]]\n    if not kind(held.st_mode) or (held.st_dev,held.st_ino) != (item["device"],item["inode"]):\n        raise SystemExit("policy_fd_identity_mismatch")\n    mapping[item["fd"]] = (opened, item["target"])\n    targets.add(item["target"])\nused = set()\nfor index, arg in enumerate(args):\n    if arg in ("--bind-fd","--ro-bind-fd"):\n        if index + 2 >= len(args) or not args[index+1].isdigit():\n            raise SystemExit("policy_fd_launch_invalid")\n        original = int(args[index+1])\n        if original not in mapping or original in used or args[index+2] != mapping[original][1]:\n            raise SystemExit("policy_fd_launch_invalid")\n        opened, _ = mapping[original]\n        args[index+1] = str(opened)\n        os.set_inheritable(opened, True)\n        used.add(original)\nif used != set(mapping) or not args or args[0] != "/usr/bin/bwrap":\n    raise SystemExit("policy_fd_launch_invalid")\nos.execv(args[0], args)\n'

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
) -> list[str]:
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
        # The host Hermes profile (including credentials/config) stays read-only.
        # Give a managed chat only ephemeral session and cache state.
        for runtime_dir in (HOME / ".cache", HOME / ".hermes/sessions",
                            HOME / ".hermes/cache", HOME / ".hermes/logs"):
            if runtime_dir.is_dir():
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
        args += ["--tmpfs", "/run", "--dir", "/run/herdr", "--dir", "/run/herdr-policy"]
        for entry in policy_mount.descriptors():
            args += ["--ro-bind-fd", str(entry["fd"]), entry["target"]]
        from herdr.launch_environment import STARTUP_CONTROLS
        for name in sorted(set(STARTUP_CONTROLS)|{key for key in os.environ if key.startswith("LD_")}):
            args += ["--unsetenv",name]
        args += ["--setenv", "PATH", "/run/herdr-bootstrap:/usr/bin:/bin"]
    args += [
        "--setenv", "HERDR_DURABLE_SANDBOX", "1",
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


def shell_command(args: list[str]) -> str:
    from herdr.launch_environment import STARTUP_CONTROLS
    controls=sorted(set(STARTUP_CONTROLS)|{key for key in os.environ
                    if key.startswith("LD_") and key.replace("_","").isalnum()})
    return "unset " + " ".join(map(shlex.quote,controls)) + "; exec " + shlex.join(args)


def _env(pid: int) -> set[bytes]:
    return set(Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"))


def pane_input_ready(process_info: dict, marker: str) -> bool:
    """Require the owned host shell's terminal to accept an untruncated command."""
    fd = None
    try:
        pid = int(process_info.get("shell_pid") or 0)
        if pid <= 0:
            return False
        expected = f"HERDR_DURABLE_TASK_PANE={marker}".encode()
        if expected not in _env(pid):
            return False
        if os.readlink(f"/proc/{pid}/ns/pid") != os.readlink("/proc/self/ns/pid"):
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
