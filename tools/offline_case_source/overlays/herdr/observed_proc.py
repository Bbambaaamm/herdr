"""Read-only privileged metadata view for existing host verifiers.

Only approved /proc/PID targets are delegated. Public immutable file contents
are reopened through the controller's OWN already approved source descriptors
after the root peer proves target/source inode equality. No remote file-body,
credential, arbitrary pathname or FD-content operation is exposed.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import errno
import hashlib
import io
import os as _os
from pathlib import Path as _Path
import re
import types
from .case_roster import (CONTEXT_ROOT, ROSTER_PATH, SUFFIX, OBSERVER_LABEL,
                        canonical, decode, digest, require)

_DIRECT = ContextVar("herdr_root_metadata_direct", default=False)
_CONCRETE = type(_Path())


def native_scope_enabled():
    if _DIRECT.get(): return True
    try:
        from .prep_entry import protected_json
        value = protected_json(_Path(ROSTER_PATH))
    except FileNotFoundError:
        return False
    except Exception:
        raise PermissionError(errno.EACCES, "native observer scope unknown")
    return value["controller"]["pid"] == _os.getpid() and _os.geteuid() == 1001


@contextmanager
def root_direct_scope():
    require(_os.geteuid() == _os.getegid() == 0 and
        _Path("/proc/self/attr/current").read_text().strip() == OBSERVER_LABEL + " (enforce)" and
        _Path("/proc/self/cgroup").read_text().splitlines() ==
        ["0::/system.slice/herdr-offline-observer-" + SUFFIX + ".service"], "exact_root_metadata_domain_required")
    token = _DIRECT.set(True)
    try: yield
    finally: _DIRECT.reset(token)


def target(value):
    if isinstance(value, int): return None
    raw = _os.fsdecode(value).replace("\\", "/")
    match = re.fullmatch(r"/proc/([1-9][0-9]*)(/.*)?", raw)
    if not match or int(match[1]) == _os.getpid() or _DIRECT.get() or not native_scope_enabled(): return None
    suffix = match[2] or ""
    require("\0" not in suffix and all(x not in (".", "..") for x in suffix.split("/")), "canonical_proc_suffix_required")
    return int(match[1]), suffix


def rpc(pid, suffix, operation):
    from .observer_client import LinuxClientOps
    ops = LinuxClientOps(); roster = ops.roster()
    query = {"v": "herdr-offline-metadata-2", "pid": pid, "suffix": suffix, "op": operation}
    packet = canonical(query); answer = decode(ops.exchange(packet, roster))
    require(type(answer) is dict and answer.get("v") == query["v"] and
        answer.get("request_sha256") == hashlib.sha256(packet).hexdigest() and
        answer.get("roster_sha256") == roster.sha256 and answer.get("pid") == pid and
        answer.get("role") in ("root", "child") and answer.get("observer_pid") == ops.peer_pid,
        "root_metadata_response_binding_changed")
    context = ops.context(answer["role"])
    require(answer["context_sha256"] == digest(context) and
        answer["identity_sha256"] == digest(roster.slot(answer["role"])["identity"]) and
        type(answer["start_ticks"]) is int and answer["start_ticks"] > 0 and
        ops.roster().sha256 == roster.sha256, "canonical_metadata_context_changed")
    data = answer["data"]
    if "errno" in data:
        if data["errno"] == errno.ENOENT: raise FileNotFoundError(errno.ENOENT, "observed object absent")
        raise PermissionError(errno.EACCES, "metadata observation unknown")
    return data, context


_bound_rpc = rpc
def rpc(pid, suffix, operation):
    try: return _bound_rpc(pid, suffix, operation)
    except FileNotFoundError: raise
    except Exception as error:
        raise PermissionError(errno.EACCES, "root metadata observation unavailable") from error


def stat_for(value, *, follow=True):
    selected = target(value)
    if selected is None: return _os.stat(value, follow_symlinks=follow)
    data, _ = rpc(*selected, "stat" if follow else "lstat")
    require(type(data.get("stat")) is dict, "root_stat_response_invalid")
    return types.SimpleNamespace(**data["stat"])


def open_source(value, mode="rb"):
    selected = target(value)
    if selected is None: return _Path(value).open(mode)
    require(mode in ("r", "rb"), "readonly_observation_required")
    data, context = rpc(*selected, "read")
    if "text" in data:
        raw = data["text"].encode("utf-8")
        return io.BytesIO(raw) if mode == "rb" else io.StringIO(data["text"])
    source = data.get("local_source")
    require(type(source) is str and re.fullmatch(r"/proc/" + str(_os.getpid()) + r"/fd/[0-9]+(?:/[^\0]+)?", source)
        and all(x not in (".", "..") for x in source.split("/")), "own_approved_source_fd_required")
    fd = _os.open(source, _os.O_RDONLY | _os.O_CLOEXEC | _os.O_NONBLOCK)
    try:
        current = _os.fstat(fd); remote = data["stat"]
        require((current.st_dev, current.st_ino, current.st_mode, current.st_size) ==
            tuple(remote[k] for k in ("st_dev", "st_ino", "st_mode", "st_size")), "target_source_inode_changed")
        stream = _os.fdopen(fd, mode); fd = -1
        return stream
    finally:
        if fd >= 0: _os.close(fd)


class _PathType(type):
    def __instancecheck__(cls, value): return isinstance(value, _Path)


class Path(_CONCRETE, metaclass=_PathType):
    def open(self, mode="r", *args, **kwargs):
        if target(self) is None: return super().open(mode, *args, **kwargs)
        require(not args and not kwargs, "closed_remote_read_options_required")
        return open_source(self, mode)
    def read_bytes(self):
        with self.open("rb") as stream: return stream.read()
    def read_text(self, encoding=None, errors=None):
        raw = self.read_bytes(); return raw.decode(encoding or "utf-8", errors or "strict")
    def stat(self, *, follow_symlinks=True):
        return stat_for(self, follow=follow_symlinks) if target(self) else super().stat(follow_symlinks=follow_symlinks)
    def lstat(self): return self.stat(follow_symlinks=False)
    def exists(self):
        try: self.stat(); return True
        except FileNotFoundError: return False
    def is_dir(self):
        import stat
        try: return stat.S_ISDIR(self.stat().st_mode)
        except FileNotFoundError: return False
    def is_file(self):
        import stat
        try: return stat.S_ISREG(self.stat().st_mode)
        except FileNotFoundError: return False
    def is_symlink(self):
        import stat
        try: return stat.S_ISLNK(self.lstat().st_mode)
        except FileNotFoundError: return False
    def iterdir(self):
        selected = target(self)
        if selected is None: yield from super().iterdir(); return
        data, _ = rpc(*selected, "list")
        names = data["names"]
        require(type(names) is list and len(names) <= 4096 and all(type(n) is str and n not in ("", ".", "..")
            and "/" not in n and "\\" not in n for n in names), "root_directory_response_invalid")
        for name in names: yield self / name


class _Entries:
    def __init__(self, root): self.rows = iter(root.iterdir())
    def __enter__(self): return self
    def __exit__(self, *_a): self.close()
    def close(self): pass
    def __iter__(self): return self
    def __next__(self):
        p = next(self.rows)
        return types.SimpleNamespace(name=p.name, path=str(p), is_dir=lambda **kw: p.is_dir(),
            is_file=lambda **kw: p.is_file(), is_symlink=p.is_symlink,
            stat=lambda **kw: p.stat(follow_symlinks=kw.get("follow_symlinks", True)))


class _PathFunctions:
    def __getattr__(self, name): return getattr(_os.path, name)
    def lexists(self, value):
        if not target(value): return _os.path.lexists(value)
        try: Path(value).lstat(); return True
        except FileNotFoundError: return False
    def exists(self, value): return Path(value).exists() if target(value) else _os.path.exists(value)
    def isfile(self, value): return Path(value).is_file() if target(value) else _os.path.isfile(value)
    def isdir(self, value): return Path(value).is_dir() if target(value) else _os.path.isdir(value)


class _OS:
    path = _PathFunctions()
    def __getattr__(self, name): return getattr(_os, name)
    def stat(self, value, *args, **kwargs):
        return stat_for(value, follow=kwargs.get("follow_symlinks", True)) if target(value) else _os.stat(value, *args, **kwargs)
    def readlink(self, value, *args, **kwargs):
        if not target(value): return _os.readlink(value, *args, **kwargs)
        return rpc(*target(value), "readlink")[0]["link"]
    def scandir(self, value): return _Entries(Path(value)) if target(value) else _os.scandir(value)
    def open(self, value, flags, *args, **kwargs):
        if not target(value): return _os.open(value, flags, *args, **kwargs)
        require(not flags & (_os.O_WRONLY | _os.O_RDWR | _os.O_CREAT | _os.O_TRUNC), "readonly_proc_open_required")
        stream = open_source(value, "rb")
        # Only immutable source-backed reads need an FD in existing verifiers.
        # Kernel text snapshots are intentionally not forged into inode FDs.
        require(hasattr(stream, "fileno"), "kernel_text_has_no_transferable_fd")
        try: fd = _os.dup(stream.fileno())
        finally: stream.close()
        return fd


os = _OS()
