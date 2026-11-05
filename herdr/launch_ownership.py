"""Private ownership journal for policy resources across host-process death."""
from __future__ import annotations
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from pathlib import Path

from herdr.security import InvocationIdentity, SecurityError, canonical_json_bytes

MAX_RECORD = 16384


def _require(condition, message):
    if not condition: raise SecurityError(message)


def _directory(path):
    path = Path(path)
    _require(path.is_absolute() and path.resolve(strict=True) == path, "canonical private ownership storage required")
    info = path.lstat()
    _require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
             and stat.S_IMODE(info.st_mode) == 0o700, "private ownership storage requires owner mode 0700")
    return path, info


def _sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try: os.fsync(fd)
    finally: os.close(fd)


@contextlib.contextmanager
def _lock(storage):
    fd = os.open(storage / ".ownership.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                 and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1,
                 "protected ownership lock required")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _name(identity):
    _require(isinstance(identity, InvocationIdentity), "complete ownership identity required")
    return "ownership-" + hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest() + ".json"


def _read(storage, identity):
    target = storage / _name(identity)
    try: fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except FileNotFoundError: return None
    try:
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                 and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1 and info.st_size <= MAX_RECORD,
                 "protected bounded ownership record required")
        raw = os.read(fd, MAX_RECORD + 1)
        _require(len(raw) <= MAX_RECORD and not os.read(fd,1), "ownership record exceeds bound")
        named = target.lstat()
        _require((info.st_dev,info.st_ino) == (named.st_dev,named.st_ino), "ownership record replaced")
    finally: os.close(fd)
    try: value = json.loads(raw)
    except (ValueError, UnicodeError): raise SecurityError("invalid ownership record") from None
    keys = {"schema_version","identity","owner_pid","owner_start_ticks","storage_device","storage_inode",
            "directory","directory_device","directory_inode"}
    current = storage.lstat()
    _require(isinstance(value,dict) and set(value) == keys and type(value["schema_version"]) is int and value["schema_version"] == 1
        and value["identity"] == identity.to_json()
        and (value["storage_device"],value["storage_inode"]) == (current.st_dev,current.st_ino)
        and isinstance(value["directory"],str) and re.fullmatch(r"launch-[0-9a-f]{32}",value["directory"])
        and all(type(value[key]) is int and value[key] > 0 for key in
            ("owner_pid","owner_start_ticks","storage_device","storage_inode","directory_device","directory_inode")),
        "ownership record identity or storage changed")
    return value


def _verify_owned_contents(fd, *, depth=0, count=None):
    _require(depth <= 32, "ownership directory depth exceeds bound")
    count = [0] if count is None else count
    for name in os.listdir(fd):
        count[0] += 1
        _require(count[0] <= 262144, "ownership inventory exceeds bound")
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        _require(info.st_uid == os.getuid() and not info.st_mode & 0o022,
                 "ownership contents owner or mode changed")
        if stat.S_ISDIR(info.st_mode):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            try: _verify_owned_contents(child, depth=depth+1, count=count)
            finally: os.close(child)
        else:
            _require((stat.S_ISREG(info.st_mode) or stat.S_ISSOCK(info.st_mode)) and info.st_nlink == 1,
                     "ownership contents type or links changed")


def cleanup_orphan(storage, identity, *, live_owner=None):
    """Caller must first prove the exact pane absent/closed or no split effect.

    Cold recovery refuses a still-live original host. The live owner capability
    is held only on its prepared launch; a task/prompt cannot manufacture it.
    """
    from herdr.policy_launch import process_start_ticks
    storage, _ = _directory(storage)
    with _lock(storage):
        value = _read(storage, identity)
        if value is None: return False
        owner = (value["owner_pid"],value["owner_start_ticks"])
        try: alive = process_start_ticks(owner[0]) == owner[1]
        except (OSError, ValueError, SecurityError): alive = False
        _require(not alive or live_owner == owner == (os.getpid(), process_start_ticks(os.getpid())),
                 "original policy host is still alive")
        directory = storage / value["directory"]
        try: info = directory.lstat()
        except FileNotFoundError: info = None
        if info is not None:
            _require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                     and (info.st_dev,info.st_ino) == (value["directory_device"],value["directory_inode"])
                     and stat.S_IMODE(info.st_mode) == 0o700, "owned launch directory replaced")
            fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                held = os.fstat(fd)
                _require((held.st_dev,held.st_ino) == (info.st_dev,info.st_ino), "owned directory changed")
                _verify_owned_contents(fd)
                # All names belong to this immutable/private launch container.
                for root, dirs, files in os.walk(directory, topdown=False, followlinks=False):
                    for name in dirs: os.chmod(Path(root)/name, 0o700, follow_symlinks=False)
                os.chmod(directory,0o700)
                shutil.rmtree(directory)
            finally: os.close(fd)
        (storage / _name(identity)).unlink()
        _sync(storage)
        return True


class LaunchOwnership:
    def __init__(self, storage, identity, value):
        self.storage, self.identity, self.value = storage, identity, value
        self.directory = storage / value["directory"]
        self._owner = (value["owner_pid"],value["owner_start_ticks"])

    @classmethod
    def create(cls, storage, identity):
        from herdr.policy_launch import process_start_ticks
        storage, root = _directory(storage)
        with _lock(storage):
            _require(_read(storage,identity) is None, "policy launch already owned; reconcile same identity")
            directory = storage / ("launch-" + uuid.uuid4().hex)
            directory.mkdir(mode=0o700)
            info = directory.lstat()
            value = {"schema_version":1, "identity":identity.to_json(), "owner_pid":os.getpid(),
                "owner_start_ticks":process_start_ticks(os.getpid()), "storage_device":root.st_dev,
                "storage_inode":root.st_ino, "directory":directory.name,
                "directory_device":info.st_dev, "directory_inode":info.st_ino}
            fd = None
            try:
                raw = canonical_json_bytes(value)
                fd = os.open(storage / _name(identity), os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC,0o600)
                with os.fdopen(fd,"wb") as stream:
                    fd = None; stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                _sync(storage)
                return cls(storage,identity,value)
            except BaseException:
                if fd is not None: os.close(fd)
                directory.rmdir()
                raise

    def cleanup_after_pane_closed(self):
        return cleanup_orphan(self.storage,self.identity,live_owner=self._owner)
