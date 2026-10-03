"""Construct and verify the durable task pane's mount and PID boundary."""
import os
import shlex
import shutil
import stat
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
        "--bind" if child_workspace_writable is not False else "--ro-bind",
        pinned_worktree.source if pinned_worktree else str(workspace), str(workspace),
        "--proc", "/proc",
        "--chdir", str(workspace),
    ]
    seen = {workspace}
    defaults = DEFAULT_WRITABLE if child_workspace_writable is None else DEFAULT_WRITABLE[:2]
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

    args += ["--tmpfs", str(HERDR_CONFIG), "--tmpfs", str(HERDR_RELEASES)]
    for path in {real_binary, real_binary.resolve(strict=True)}:
        args += ["--ro-bind", str(policy), str(path)]
    args += [
        "--setenv", "HERDR_DURABLE_SANDBOX", "1",
        "--", "/bin/bash", "-i",
    ]
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
) -> bool:
    """Require expected mounts, hidden Herdr paths and non-host namespaces."""
    expected = {str(real_binary.absolute()), str(real_binary.resolve()),
                str(HERDR_CONFIG), str(HERDR_RELEASES)}
    for _ in range(attempts):
        try:
            root = Path(f"/proc/{pid}/root")
            mounts = Path(f"/proc/{pid}/mountinfo").read_text(encoding="utf-8")
            targets = {line.split(" - ", 1)[0].split()[4] for line in mounts.splitlines()}
            env = _env(pid)
            config = root / str(HERDR_CONFIG).lstrip("/")
            releases = root / str(HERDR_RELEASES).lstrip("/")
            hidden = (config.is_dir() and not any(config.iterdir())
                      and releases.is_dir() and not any(releases.iterdir()))
            policy_matches = (
                root / str(real_binary).lstrip("/")
            ).read_bytes() == policy.read_bytes()
            ns = (
                os.readlink(f"/proc/{pid}/ns/pid") != os.readlink("/proc/self/ns/pid")
                and os.readlink(f"/proc/{pid}/ns/mnt") != os.readlink("/proc/self/ns/mnt")
            )
            if (
                expected <= targets
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
