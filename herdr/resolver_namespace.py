"""Public host DNS input retained across a private /run namespace.

Only the host resolver configuration is eligible. The root issuer independently
compares its trusted source with the sealed data proposed by the worker.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import pwd
import stat

from .private_profile_namespace import (
    PrivateProfileError, SealedProfileInput, _F_ADD_SEALS, _REQUIRED_SEALS,
)
from .security import SecurityError

KIND = "sealed-resolver-data"
MAX_BYTES = 16384
TARGETS = frozenset({"/etc/resolv.conf", "/run/systemd/resolve/stub-resolv.conf",
                     "/run/systemd/resolve/resolv.conf"})


def require(condition, reason):
    if not condition:
        raise SecurityError(reason)


def _owners(host_uid):
    owners = {0}
    try:
        uid = pwd.getpwnam("systemd-resolve").pw_uid
    except KeyError:
        return owners
    require(uid != host_uid or uid == 0, "resolver service shares the worker identity")
    owners.add(uid)
    return owners


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_uid, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _trusted_read(target, owners):
    """Open a fixed path component by component; never follow source links."""
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    fd = -1
    try:
        for name in Path(target).parts[1:-1]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=parent)
            os.close(parent)
            parent = child
            info = os.fstat(parent)
            require(info.st_uid in owners and not info.st_mode & 0o022,
                    "resolver source ancestry is writable or untrusted")
        fd = os.open(Path(target).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                     dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid in owners
                and not before.st_mode & 0o022 and 0 < before.st_size <= MAX_BYTES,
                "resolver source must be trusted, regular and bounded")
        data = os.read(fd, MAX_BYTES + 1)
        require(len(data) == before.st_size and _stamp(before) == _stamp(os.fstat(fd)),
                "resolver source changed while reading")
        return data
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent)


def read_host_resolver(*, host_uid=None):
    """Select only a regular /etc file or the two supported systemd targets."""
    host_uid = os.geteuid() if host_uid is None else host_uid
    etc = os.open("/etc", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        directory = os.fstat(etc)
        require(directory.st_uid == 0 and not directory.st_mode & 0o022,
                "resolver selector directory is untrusted")
        before = os.stat("resolv.conf", dir_fd=etc, follow_symlinks=False)
        require(before.st_uid == 0, "resolver selector must be root owned")
        target = "/etc/resolv.conf"
        if stat.S_ISLNK(before.st_mode):
            link = os.readlink("resolv.conf", dir_fd=etc)
            target = os.path.normpath(os.path.join("/etc", link))
            require(target in TARGETS and target != "/etc/resolv.conf",
                    "unsupported resolver symlink target")
        else:
            require(stat.S_ISREG(before.st_mode), "resolver selector must be regular or supported symlink")
        data = _trusted_read(target, {0} if target == "/etc/resolv.conf" else _owners(host_uid))
        require(_stamp(before) == _stamp(os.stat("resolv.conf", dir_fd=etc, follow_symlinks=False)),
                "resolver selector changed while reading")
        return target, data
    finally:
        os.close(etc)


def verify_descriptor(entry, fd):
    require(entry["kind"] == KIND and entry["target"] in TARGETS
            and type(entry["size"]) is int and 0 < entry["size"] <= MAX_BYTES,
            "resolver descriptor target or bound invalid")
    try:
        SealedProfileInput("resolver", fd, entry["size"], entry["sha256"]).verify()
    except PrivateProfileError as error:
        raise SecurityError("resolver seal or digest invalid") from error


def verify_host_descriptor(entry, fd, *, host_uid):
    verify_descriptor(entry, fd)
    target, data = read_host_resolver(host_uid=host_uid)
    require(entry["target"] == target and os.pread(fd, MAX_BYTES + 1, 0) == data,
            "resolver data differs from trusted host source")


def verify_mounted(entry, pid, rows):
    target = entry["target"]
    require(entry["kind"] == KIND and target in TARGETS and 0 < entry["size"] <= MAX_BYTES
            and "ro" in rows.get(target, set()) and "rw" not in rows.get(target, set())
            and "__stacked__" not in rows.get(target, set()), "resolver mount is not exclusively read only")
    fd = os.open(f"/proc/{pid}/root{target}", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_size == entry["size"]
                and hashlib.sha256(os.pread(fd, MAX_BYTES + 1, 0)).hexdigest() == entry["sha256"],
                "mounted resolver data differs from approved snapshot")
    finally:
        os.close(fd)


@dataclass
class ResolverSnapshot:
    target: str
    data: SealedProfileInput

    @classmethod
    def create(cls):
        import fcntl
        target, body = read_host_resolver()
        fd = os.memfd_create("herdr-resolver", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        try:
            pending = memoryview(body)
            while pending:
                written = os.write(fd, pending)
                require(written > 0, "resolver snapshot write stopped")
                pending = pending[written:]
            os.lseek(fd, 0, os.SEEK_SET)
            fcntl.fcntl(fd, _F_ADD_SEALS, _REQUIRED_SEALS)
            data = SealedProfileInput("resolver", fd, len(body), hashlib.sha256(body).hexdigest())
            data.verify()
            return cls(target, data)
        except BaseException:
            os.close(fd)
            raise

    def descriptor(self):
        self.data.verify()
        info = os.fstat(self.data.fd)
        return {"source": f"/proc/{os.getpid()}/fd/{self.data.fd}", "fd": self.data.fd,
                "device": info.st_dev, "inode": info.st_ino, "kind": KIND,
                "target": self.target, "size": self.data.size, "sha256": self.data.sha256}

    def parent_args(self):
        require(self.target in TARGETS, "resolver snapshot target invalid")
        if self.target.startswith("/run/"):
            return ["--dir", "/run/systemd", "--dir", "/run/systemd/resolve"]
        return []

    def close(self):
        self.data.close()
