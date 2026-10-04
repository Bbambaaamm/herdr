"""Construct and verify the durable task pane's mount and PID boundary."""
import os
import shlex
import shutil
import stat
import sys
import tempfile
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
    with os.fdopen(fd, "wb") as target, POLICY.open("rb") as source:
        shutil.copyfileobj(source, target)
        target.flush()
        os.fsync(target.fileno())
    os.chmod(name, 0o555)
    return Path(name)


def command(
    workspace: Path,
    real_binary: Path,
    *,
    writable: tuple[Path, ...] = (),
    policy: Path | None = None,
    child_workspace_writable: bool | None = None,
    pinned_worktree: PinnedWorktree | None = None,
) -> list[str]:
    workspace = Path(workspace).absolute() if pinned_worktree else workspace.resolve(strict=True)
    if child_workspace_writable is not None:
        if (pinned_worktree is None or pinned_worktree.logical != workspace):
            raise RuntimeError("managed_child_worktree_unpinned")
        pinned_worktree.verify()
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
    defaults = DEFAULT_WRITABLE if child_workspace_writable is None else ()
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

    if child_workspace_writable is not None:
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
    args += [
        "--setenv", "HERDR_DURABLE_SANDBOX", "1",
        "--", "/bin/bash", "-i",
    ]
    if pinned_worktree is not None:
        return [sys.executable, "-I", "-c", _PINNED_LAUNCHER,
                pinned_worktree.source, str(pinned_worktree.fd),
                str(pinned_worktree.device), str(pinned_worktree.inode), *args]
    return args


def shell_command(args: list[str]) -> str:
    return "exec " + shlex.join(args)


def _env(pid: int) -> set[bytes]:
    return set(Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"))


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
        except (OSError, ValueError, IndexError):
            pass
        time.sleep(0.1)
    return False
