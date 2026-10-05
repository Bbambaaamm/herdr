"""Lifetime admission fence shared with pre-ownership worker binaries.

Legacy workers take LOCK_EX on worker.lock. Every new host admission and
namespace custodian takes LOCK_SH on that SAME inode. The new worker's
worker.loop.lock only serializes the new coordinator loop.
"""
from __future__ import annotations
import fcntl
import os
import stat
from contextlib import contextmanager
from pathlib import Path

from .child_ownership import OwnershipError, require


@contextmanager
def legacy_admission_guard(root):
    root = Path(root).absolute()
    require(root.resolve(strict=True) == root, "ownership_epoch_root")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    fd = None
    try:
        info = os.fstat(directory)
        require(info.st_uid == os.getuid() and not info.st_mode & 0o022,
                "ownership_epoch_root")
        fd = os.open("worker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW |
                     os.O_CLOEXEC | os.O_NONBLOCK, 0o600, dir_fd=directory)
        held = os.fstat(fd)
        require(stat.S_ISREG(held.st_mode) and held.st_uid == os.getuid()
                and stat.S_IMODE(held.st_mode) == 0o600 and held.st_nlink == 1,
                "ownership_epoch_lock")
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            raise OwnershipError("ownership_legacy_worker_active") from None
        named = os.stat("worker.lock", dir_fd=directory, follow_symlinks=False)
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino),
                "ownership_epoch_lock_changed")
        os.fsync(fd)
        os.fsync(directory)
        yield {"root": str(root), "device": held.st_dev, "inode": held.st_ino}
    finally:
        # Never share this open-file description with a worker/model process.
        if fd is not None:
            os.close(fd)
        os.close(directory)


# Standalone trusted host code: the model namespace receives no lock FD.
# PR_SET_PDEATHSIG closes the spawn-before-exec race; bwrap also uses
# --die-with-parent, so killing this custodian kills its complete PID namespace.
NAMESPACE_CUSTODIAN = r'''
import ctypes, fcntl, json, os, signal, stat, subprocess, sys
binding = json.loads(sys.argv[1])
if (not isinstance(binding, dict) or set(binding) != {"root", "device", "inode"}
        or type(binding["device"]) is not int or type(binding["inode"]) is not int):
    raise SystemExit("ownership_epoch_binding")
root = binding["root"]
if not isinstance(root, str) or not root.startswith("/") or os.path.realpath(root) != root:
    raise SystemExit("ownership_epoch_root")
directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
info = os.fstat(directory)
if info.st_uid != os.getuid() or info.st_mode & 0o022:
    raise SystemExit("ownership_epoch_root")
fd = os.open("worker.lock", os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
             dir_fd=directory)
held = os.fstat(fd)
if (not stat.S_ISREG(held.st_mode) or held.st_uid != os.getuid()
        or stat.S_IMODE(held.st_mode) != 0o600 or held.st_nlink != 1
        or (held.st_dev, held.st_ino) != (binding["device"], binding["inode"])):
    raise SystemExit("ownership_epoch_lock_changed")
fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
named = os.stat("worker.lock", dir_fd=directory, follow_symlinks=False)
if (named.st_dev, named.st_ino) != (held.st_dev, held.st_ino):
    raise SystemExit("ownership_epoch_lock_changed")
parent_pid = os.getpid()
def die_with_parent():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent_pid:
        os._exit(126)
child = subprocess.Popen(sys.argv[2:], close_fds=True, preexec_fn=die_with_parent)
try:
    code = child.wait()
finally:
    os.close(fd)
    os.close(directory)
raise SystemExit(code if code >= 0 else 128 - code)
'''


def custodial_command(command, binding):
    import json
    require(isinstance(command, list) and command, "ownership_epoch_command")
    require(isinstance(binding, dict) and set(binding) == {"root", "device", "inode"},
            "ownership_epoch_binding")
    return ["/usr/bin/python3", "-I", "-S", "-c", NAMESPACE_CUSTODIAN,
            json.dumps(binding, separators=(",", ":")), *command]
