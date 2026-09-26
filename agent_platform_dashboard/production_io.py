"""Linux bounded no-follow I/O and single-instance atomic publication."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import PurePosixPath
import secrets
import stat

from .production_contract import need


@contextmanager
def directory(path):
    need(type(path) is str and path.startswith('/') and str(PurePosixPath(path)) == path
         and '..' not in PurePosixPath(path).parts and len(path) <= 1024)
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in PurePosixPath(path).parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


@contextmanager
def regular(path, *, private=False):
    p = PurePosixPath(path)
    need(str(p) == path and p.name not in ('', '.', '..'))
    with directory(str(p.parent)) as parent:
        fd = os.open(p.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        try:
            info = os.fstat(fd)
            need(stat.S_ISREG(info.st_mode) and not info.st_mode & (0o027 if private else 0o022))
            yield fd, info
        finally:
            os.close(fd)


def read(path, limit, *, private=False, owner=None):
    with regular(path, private=private) as (fd, info):
        need(info.st_size <= limit and (owner is None or info.st_uid == owner))
        chunks, size = [], 0
        while size <= limit:
            data = os.read(fd, min(8192, limit + 1 - size))
            if not data:
                break
            chunks.append(data)
            size += len(data)
        need(size <= limit)
        return b''.join(chunks)


@contextmanager
def publication(path):
    """Pin the output directory. The caller must keep it private to the exporter."""
    p = PurePosixPath(path)
    need(p.name == 'snapshot.json' or p.name == 'herdr.json')
    with directory(str(p.parent)) as parent:
        info = os.fstat(parent)
        need(info.st_uid == os.geteuid() and not info.st_mode & 0o022)
        lock = os.open(p.name + '.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
        try:
            info = os.fstat(lock)
            need(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and not info.st_mode & 0o077)
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield parent, p.name
        finally:
            os.close(lock)


def publish(target, data):
    parent, name = target
    need(type(data) is bytes and len(data) <= 131072)
    temporary = '.' + name + '.' + secrets.token_hex(8)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o640, dir_fd=parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fchmod(stream.fileno(), 0o640)
            os.fsync(stream.fileno())
        os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)
    finally:
        try:
            os.unlink(temporary, dir_fd=parent)
        except FileNotFoundError:
            pass
