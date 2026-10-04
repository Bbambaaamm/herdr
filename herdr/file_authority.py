"""Root-FD anchored local file authority for #76 policy mode."""
from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import stat
import time
from pathlib import Path
from typing import Iterable

MAX_FILE_BYTES = 32 * 1024 * 1024


class FileAuthorityError(OSError):
    pass


def _rename_noreplace(
    src_parent: int, src_name: str, dst_parent: int, dst_name: str
) -> None:
    """Linux renameat2(RENAME_NOREPLACE); fail closed when unavailable."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise FileAuthorityError("atomic no-clobber rename unavailable")
    renameat2.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        src_parent, os.fsencode(src_name), dst_parent, os.fsencode(dst_name), 1
    )
    if result != 0:
        err = ctypes.get_errno()
        if err == errno.EEXIST:
            raise FileAuthorityError("move destination already exists")
        raise FileAuthorityError(os.strerror(err))


class RootFDWorkspace:
    """Pin allowed directory inodes and perform I/O relative to held FDs."""

    def __init__(self, roots: Iterable[str]) -> None:
        unique = sorted({str(Path(root)) for root in roots}, key=len, reverse=True)
        if not unique:
            raise FileAuthorityError("no file roots granted")
        self._roots: list[tuple[Path, int]] = []
        try:
            for raw in unique:
                root = Path(raw)
                if not root.is_absolute():
                    raise FileAuthorityError("file root must be absolute")
                fd = os.open(
                    root,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                )
                info = os.fstat(fd)
                if not stat.S_ISDIR(info.st_mode):
                    os.close(fd)
                    raise FileAuthorityError("file root must be directory")
                self._roots.append((root, fd))
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        roots, self._roots = self._roots, []
        for _root, fd in roots:
            try:
                os.close(fd)
            except OSError:
                pass

    def _select(self, path: str) -> tuple[int, tuple[str, ...]]:
        candidate = Path(path)
        if not candidate.is_absolute():
            raise FileAuthorityError("authorized file path must be absolute")
        for root, fd in self._roots:
            try:
                relative = candidate.relative_to(root)
            except ValueError:
                continue
            parts = relative.parts
            if not parts or any(part in ("", ".", "..") for part in parts):
                raise FileAuthorityError("file path must name an entry below granted root")
            return fd, parts
        raise FileAuthorityError("file path outside pinned roots")

    def _parent(self, path: str, *, create: bool = False) -> tuple[int, str]:
        root_fd, parts = self._select(path)
        current = os.dup(root_fd)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, 0o755, dir_fd=current)
                    except FileExistsError:
                        pass
                next_fd = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=current,
                )
                os.close(current)
                current = next_fd
            return current, parts[-1]
        except BaseException:
            os.close(current)
            raise

    @staticmethod
    def _read_fd(fd: int, limit: int) -> bytes:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise FileAuthorityError("target is not a regular file")
        if info.st_size > limit:
            raise FileAuthorityError("file exceeds policy-mode bound")
        data = bytearray()
        while len(data) <= limit:
            chunk = os.read(fd, min(1024 * 1024, limit + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) > limit:
            raise FileAuthorityError("file exceeds policy-mode bound")
        return bytes(data)

    def list_regular_files(self,path: str,*,maximum: int=256,deadline: float|None=None) -> list[str]:
        """Bounded nofollow directory walk; names never become external authority."""
        if type(maximum) is not int or not 1 <= maximum <= 256:
            raise FileAuthorityError("bounded search file count required")
        if deadline is None: deadline=time.monotonic()+2
        candidate=Path(path)
        if not candidate.is_absolute() or ".." in candidate.parts:
            raise FileAuthorityError("exact search path required")
        selected=None
        for root,fd in self._roots:
            try: parts=candidate.relative_to(root).parts
            except ValueError: continue
            selected=(root,fd,parts);break
        if selected is None: raise FileAuthorityError("search outside pinned roots")
        root,fd,parts=selected
        current=os.dup(fd)
        rows=[];entries=0
        def visit(directory,logical,depth):
            nonlocal entries
            if depth>16: raise FileAuthorityError("search depth exceeds bound")
            names=[]
            with os.scandir(directory) as stream:
                for entry in stream:
                    if time.monotonic()>deadline:
                        raise FileAuthorityError("search elapsed bound exceeded")
                    entries+=1
                    if entries>4096: raise FileAuthorityError("search entry count exceeds bound")
                    names.append(entry.name)
            for name in sorted(names):
                if time.monotonic()>deadline:
                    raise FileAuthorityError("search elapsed bound exceeded")
                if name==".git": continue
                info=os.stat(name,dir_fd=directory,follow_symlinks=False)
                if stat.S_ISREG(info.st_mode):
                    rows.append(str(logical/name))
                    if len(rows)>maximum: raise FileAuthorityError("search file count exceeds bound")
                elif stat.S_ISDIR(info.st_mode):
                    child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=directory)
                    try: visit(child,logical/name,depth+1)
                    finally: os.close(child)
        try:
            for index,part in enumerate(parts):
                if index==len(parts)-1:
                    info=os.stat(part,dir_fd=current,follow_symlinks=False)
                    if stat.S_ISREG(info.st_mode): return [str(candidate)]
                child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=current)
                os.close(current);current=child
            visit(current,candidate,0)
            return rows
        finally: os.close(current)

    def file_metadata(self, path: str) -> tuple[int, int, int, int, int] | None:
        parent, name = self._parent(path)
        try:
            try:
                fd = os.open(
                    name,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                    dir_fd=parent,
                )
            except FileNotFoundError:
                return None
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    return None
                return (
                    info.st_dev, info.st_ino, info.st_size,
                    info.st_mtime_ns, info.st_ctime_ns,
                )
            finally:
                os.close(fd)
        finally:
            os.close(parent)

    def file_version(self, path: str) -> tuple | None:
        parent, name = self._parent(path)
        try:
            try:
                fd = os.open(
                    name,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                    dir_fd=parent,
                )
            except FileNotFoundError:
                return None
            digest = hashlib.sha256()
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE_BYTES:
                    return None
                total = 0
                while True:
                    chunk = os.read(fd, min(1024 * 1024, MAX_FILE_BYTES + 1 - total))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_FILE_BYTES:
                        return None
                    digest.update(chunk)
                after = os.fstat(fd)
                fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
                first = tuple(getattr(before, field) for field in fields)
                second = tuple(getattr(after, field) for field in fields)
                return (*first, digest.digest()) if first == second else None
            finally:
                os.close(fd)
        finally:
            os.close(parent)

    def read_bytes(self, path: str, *, limit: int = MAX_FILE_BYTES) -> bytes:
        parent, name = self._parent(path)
        try:
            fd = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=parent,
            )
            try:
                return self._read_fd(fd, limit)
            finally:
                os.close(fd)
        finally:
            os.close(parent)

    def read_text(self, path: str, *, limit: int = MAX_FILE_BYTES) -> str:
        try:
            return self.read_bytes(path, limit=limit).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FileAuthorityError("policy-mode file is not UTF-8 text") from exc

    def create_bytes(self, path: str, content: bytes) -> tuple[int, str]:
        """Atomically create one regular file without overwriting a raced-in target."""
        if len(content) > MAX_FILE_BYTES:
            raise FileAuthorityError("write exceeds policy-mode bound")
        parent, name = self._parent(path, create=True)
        temp = f".herdr-policy-{os.getpid()}-{os.urandom(12).hex()}"
        temp_fd = -1
        try:
            temp_fd = os.open(
                temp,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o644,
                dir_fd=parent,
            )
            view = memoryview(content)
            while view:
                written = os.write(temp_fd, view)
                if written <= 0:
                    raise FileAuthorityError("short policy-mode write")
                view = view[written:]
            os.fsync(temp_fd)
            os.close(temp_fd)
            temp_fd = -1
            try:
                os.link(
                    temp, name, src_dir_fd=parent, dst_dir_fd=parent,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise FileAuthorityError("create target already exists") from exc
            os.fsync(parent)
            return len(content), hashlib.sha256(content).hexdigest()
        finally:
            if temp_fd >= 0:
                os.close(temp_fd)
            try:
                os.unlink(temp, dir_fd=parent)
            except FileNotFoundError:
                pass
            os.close(parent)

    def create_text(self, path: str, content: str) -> tuple[int, str]:
        try:
            raw = content.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise FileAuthorityError("policy-mode text is not UTF-8 encodable") from exc
        return self.create_bytes(path, raw)

    def write_bytes(self, path: str, content: bytes) -> tuple[int, str]:
        if len(content) > MAX_FILE_BYTES:
            raise FileAuthorityError("write exceeds policy-mode bound")
        parent, name = self._parent(path, create=True)
        temp = f".herdr-policy-{os.getpid()}-{os.urandom(12).hex()}"
        temp_fd = -1
        try:
            mode = 0o644
            try:
                current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                current = None
            if current is not None:
                if not stat.S_ISREG(current.st_mode):
                    raise FileAuthorityError("write target is not a regular file")
                mode = stat.S_IMODE(current.st_mode)
            temp_fd = os.open(
                temp,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                mode,
                dir_fd=parent,
            )
            view = memoryview(content)
            while view:
                written = os.write(temp_fd, view)
                if written <= 0:
                    raise FileAuthorityError("short policy-mode write")
                view = view[written:]
            os.fsync(temp_fd)
            os.close(temp_fd)
            temp_fd = -1
            os.replace(temp, name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
            return len(content), hashlib.sha256(content).hexdigest()
        finally:
            if temp_fd >= 0:
                os.close(temp_fd)
            try:
                os.unlink(temp, dir_fd=parent)
            except FileNotFoundError:
                pass
            os.close(parent)

    def write_text(self, path: str, content: str) -> tuple[int, str]:
        try:
            raw = content.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise FileAuthorityError("policy-mode text is not UTF-8 encodable") from exc
        return self.write_bytes(path, raw)

    def delete_file(self, path: str) -> None:
        parent, name = self._parent(path)
        try:
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise FileAuthorityError("delete target is not a regular file")
            os.unlink(name, dir_fd=parent)
            os.fsync(parent)
        finally:
            os.close(parent)

    def move_file(self, source: str, destination: str) -> None:
        src_parent, src_name = self._parent(source)
        dst_parent, dst_name = self._parent(destination, create=True)
        try:
            source_info = os.stat(src_name, dir_fd=src_parent, follow_symlinks=False)
            if not stat.S_ISREG(source_info.st_mode):
                raise FileAuthorityError("move source is not a regular file")
            _rename_noreplace(src_parent, src_name, dst_parent, dst_name)
            os.fsync(src_parent)
            if dst_parent != src_parent:
                os.fsync(dst_parent)
        finally:
            os.close(src_parent)
            os.close(dst_parent)


__all__ = ["FileAuthorityError", "MAX_FILE_BYTES", "RootFDWorkspace"]
