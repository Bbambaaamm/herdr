"""Verified cold storage for inactive, regular cache trees; never authorizes work."""
from pathlib import Path
import base64
import ctypes
import errno
import hashlib
import json
import lzma
import os
import shutil
import stat
import tarfile
import tempfile
import time


class ArchiveError(RuntimeError):
    pass


def need(ok, reason):
    if not ok:
        raise ArchiveError(reason)


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def _open_dir(path):
    path = Path(path)
    need(path.is_absolute() and ".." not in path.parts, "absolute_directory_required")
    fd = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            nxt = os.open(part, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = nxt
        opened = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_NOATIME | os.O_CLOEXEC, dir_fd=fd)
        os.close(fd)
        return opened
    except BaseException:
        os.close(fd)
        raise


def _mount_id(fd):
    for line in Path(f"/proc/self/fdinfo/{fd}").read_text().splitlines():
        if line.startswith("mnt_id:"):
            return int(line.split()[1])
    raise ArchiveError("mount_identity_unavailable")


def _stamp(info):
    return {"device": info.st_dev, "inode": info.st_ino, "mode": stat.S_IMODE(info.st_mode),
            "uid": info.st_uid, "gid": info.st_gid, "size": info.st_size, "nlink": info.st_nlink,
            "allocated_bytes": info.st_blocks * 512, "mtime_ns": info.st_mtime_ns, "ctime_ns": info.st_ctime_ns}


def _attributes(fd):
    values = {k: base64.b64encode(os.getxattr(fd, k)).decode() for k in os.listxattr(fd)}
    need(sum(len(k) + len(v) for k, v in values.items()) <= 65536, "extended_metadata_too_large")
    return values


class _Reader:
    def __init__(self, stream):
        self.stream, self.hash, self.count = stream, hashlib.sha256(), 0

    def read(self, size=-1):
        data = self.stream.read(size)
        self.hash.update(data)
        self.count += len(data)
        return data


def scan_tree(source, owner, *, archive=None, max_entries=5000, max_bytes=1073741824):
    """Read regular files through pinned directory FDs; reject aliases and links."""
    source = Path(source)
    root_fd = _open_dir(source)
    root_info = os.fstat(root_fd)
    root_mount = _mount_id(root_fd)
    rows, total = [], [0]
    try:
        def visit(fd, relative, depth):
            need(depth <= 32 and len(rows) < max_entries, "cache_tree_limit")
            before = os.fstat(fd)
            need(_mount_id(fd) == root_mount, "cache_mount_alias_denied")
            need(stat.S_ISDIR(before.st_mode) and before.st_uid == owner and before.st_dev == root_info.st_dev
                 and not before.st_mode & 0o6000, "cache_directory_identity")
            row = {"path": relative, "kind": "directory", **_stamp(before),
                   "atime_ns": before.st_atime_ns, "xattrs": _attributes(fd)}
            rows.append(row)
            if archive:
                item = tarfile.TarInfo(relative)
                item.type, item.mode, item.uid, item.gid, item.mtime = tarfile.DIRTYPE, row["mode"], row["uid"], row["gid"], row["mtime_ns"] / 1e9
                archive.addfile(item)
            for name in sorted(os.listdir(fd)):
                need(name not in (".", "..") and "/" not in name, "cache_name_denied")
                relative_name = name if relative == "." else relative + "/" + name
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                need(info.st_dev == root_info.st_dev and info.st_uid == owner and not info.st_mode & 0o6000,
                     "cache_member_identity")
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NOATIME, dir_fd=fd)
                    try:
                        need(_stamp(os.fstat(child)) == _stamp(info), "cache_directory_changed")
                        visit(child, relative_name, depth + 1)
                    finally:
                        os.close(child)
                    continue
                need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and len(rows) < max_entries,
                     "cache_regular_exclusive_member_required")
                total[0] += info.st_size
                need(total[0] <= max_bytes, "cache_byte_limit")
                opened = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOATIME, dir_fd=fd)
                try:
                    need(_mount_id(opened) == root_mount and _stamp(os.fstat(opened)) == _stamp(info), "cache_file_changed_before_read")
                    row = {"path": relative_name, "kind": "regular", **_stamp(info),
                           "atime_ns": info.st_atime_ns, "xattrs": _attributes(opened)}
                    with os.fdopen(os.dup(opened), "rb") as stream:
                        reader = _Reader(stream)
                        if archive:
                            item = tarfile.TarInfo(relative_name)
                            item.size, item.mode, item.uid, item.gid, item.mtime = row["size"], row["mode"], row["uid"], row["gid"], row["mtime_ns"] / 1e9
                            archive.addfile(item, reader)
                        else:
                            while reader.read(1048576):
                                pass
                        need(reader.count == info.st_size, "cache_payload_size_changed")
                        row["sha256"] = reader.hash.hexdigest()
                    need(_stamp(os.fstat(opened)) == _stamp(info)
                         and _stamp(os.stat(name, dir_fd=fd, follow_symlinks=False)) == _stamp(info),
                         "cache_file_changed_during_read")
                    rows.append(row)
                finally:
                    os.close(opened)
            need(_stamp(os.fstat(fd)) == _stamp(before), "cache_directory_changed_during_read")
        visit(root_fd, ".", 0)
        need(_stamp(os.fstat(root_fd)) == _stamp(root_info) == _stamp(source.lstat()), "cache_root_changed")
        return rows
    finally:
        os.close(root_fd)


def _equivalent(left, right, *, renamed=False, restored=False):
    if len(left) != len(right):
        return False
    for a, b in zip(left, right):
        ignored = {"atime_ns"}
        if renamed and a["path"] == ".":
            ignored.add("ctime_ns")
        if restored:
            ignored |= {"device", "inode", "ctime_ns", "allocated_bytes"}
            if a["kind"] == "directory":
                ignored |= {"size", "nlink"}
        if {k: v for k, v in a.items() if k not in ignored} != {k: v for k, v in b.items() if k not in ignored}:
            return False
    return True


def _safe_relative(value):
    path = Path(value)
    need(not path.is_absolute() and ".." not in path.parts and len(path.parts) <= 32, "archive_member_path")
    return path


def verify_archive(archive, rows, expected_digest):
    need(digest_file(archive) == expected_digest, "protected_archive_digest_changed")
    with lzma.open(archive, "rb") as stream, tarfile.open(fileobj=stream, mode="r|") as saved:
        count = 0
        for item in saved:
            need(count < len(rows), "archive_member_count_changed")
            expected = rows[count]
            count += 1
            need(item.name == expected["path"] and _safe_relative(item.name) is not None, "archive_member_changed")
            need(item.mode == expected["mode"] and item.uid == expected["uid"] and item.gid == expected["gid"], "archive_member_metadata")
            if expected["kind"] == "directory":
                need(item.isdir(), "archive_directory_changed")
            else:
                need(item.isreg() and item.size == expected["size"], "archive_file_changed")
                payload = saved.extractfile(item)
                h, size = hashlib.sha256(), 0
                for block in iter(lambda: payload.read(1048576), b""):
                    size += len(block)
                    need(size <= expected["size"], "archive_payload_too_large")
                    h.update(block)
                need(size == expected["size"] and h.hexdigest() == expected["sha256"], "archive_payload_changed")
        need(count == len(rows), "archive_member_count_changed")


def active_references(rows, *, proc=Path("/proc")):
    identities = {(r["device"], r["inode"]) for r in rows}
    found = []
    for process in proc.iterdir():
        if not process.name.isdigit() or int(process.name) == os.getpid():
            continue
        try:
            for name in ("cwd", "exe"):
                try:
                    info = (process / name).stat()
                    if (info.st_dev, info.st_ino) in identities:
                        found.append((int(process.name), name))
                except FileNotFoundError:
                    pass
            for fd in (process / "fd").iterdir():
                try:
                    info = fd.stat()
                    if (info.st_dev, info.st_ino) in identities:
                        found.append((int(process.name), "fd"))
                except FileNotFoundError:
                    pass
            for line in (process / "maps").read_text().splitlines():
                fields = line.split(None, 5)
                if len(fields) >= 5 and fields[4].isdigit():
                    major, minor = (int(v, 16) for v in fields[3].split(":"))
                    if (os.makedev(major, minor), int(fields[4])) in identities:
                        found.append((int(process.name), "mapped_file"))
        except FileNotFoundError:
            pass
        except OSError as error:
            raise ArchiveError("live_process_could_not_be_inspected") from error
    return found


def _write_new(path, body):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    with os.fdopen(fd, "wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def _sync_directories(*paths):
    for path in paths:
        fd = _open_dir(path)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _protected(path):
    for parent in [Path(path), *Path(path).parents]:
        info = parent.lstat()
        need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and not info.st_mode & 0o022,
             "protected_archive_ancestry_required")


def prepare_cache_archive(source, parent, *, owner, scratch=Path("/dev/shm")):
    source, parent = Path(source), Path(parent)
    need(source.is_absolute() and source != Path("/") and ".." not in source.parts, "cache_source_path_denied")
    need(parent != source and source not in parent.parents and parent not in source.parents, "archive_source_overlap_denied")
    _protected(parent)
    parent_fd = _open_dir(source.parent)
    try:
        source_parent = _stamp(os.fstat(parent_fd))
    finally:
        os.close(parent_fd)
    with tempfile.TemporaryDirectory(prefix="herdr-cache-snapshot-", dir=scratch) as temporary:
        temp = Path(temporary) / "content.tar.xz"
        with lzma.open(temp, "xb", preset=3) as compressed, tarfile.open(fileobj=compressed, mode="w|") as archive:
            rows = scan_tree(source, owner, archive=archive)
        need(_equivalent(rows, scan_tree(source, owner)), "cache_changed_after_snapshot")
        need(not active_references(rows), "cache_has_active_process_references")
        archive_sha = digest_file(temp)
        verify_archive(temp, rows, archive_sha)
        destination = Path(tempfile.mkdtemp(prefix="herdr-cache-preserved-", dir=parent))
        destination.chmod(0o700)
        fd = os.open(destination / "content.tar.xz", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        with os.fdopen(fd, "wb") as output, temp.open("rb") as stream:
            shutil.copyfileobj(stream, output, 1048576)
            output.flush()
            os.fsync(output.fileno())
        verify_archive(destination / "content.tar.xz", rows, archive_sha)
        receipt = {"version": 1, "source": str(source), "owner": owner, "source_parent": source_parent,
                   "rows": rows, "archive_sha256": archive_sha, "archive_bytes": temp.stat().st_size,
                   "original_bytes_verified": True, "created_at_epoch": time.time()}
        _write_new(destination / "restore-catalogue.json", (json.dumps(receipt, sort_keys=True) + "\n").encode())
        # Persist both the archive entries and the new directory name before
        # this catalogue can be used to reclaim its original.
        _sync_directories(destination, destination.parent)
        return destination, receipt


def _rename_noreplace(source_parent, source_name, target_parent, target_name):
    libc = ctypes.CDLL(None, use_errno=True)
    need(hasattr(libc, "renameat2"), "atomic_no_replace_rename_unavailable")
    rename = libc.renameat2
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(source_parent, os.fsencode(source_name), target_parent, os.fsencode(target_name), 1):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def restore_cache_archive(destination):
    destination = Path(destination)
    _protected(destination)
    receipt = json.loads((destination / "restore-catalogue.json").read_bytes())
    archive = destination / "content.tar.xz"
    verify_archive(archive, receipt["rows"], receipt["archive_sha256"])
    restored = destination / "restored"
    restored.mkdir(mode=0o700)
    with lzma.open(archive, "rb") as stream, tarfile.open(fileobj=stream, mode="r|") as saved:
        for item, row in zip(saved, receipt["rows"]):
            target = restored / _safe_relative(row["path"])
            if row["kind"] == "directory":
                if row["path"] != ".":
                    target.mkdir(mode=0o700)
            else:
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "wb") as out, saved.extractfile(item) as data:
                    shutil.copyfileobj(data, out, 1048576)
    for row in reversed(receipt["rows"]):
        target = restored / _safe_relative(row["path"])
        os.chown(target, row["uid"], row["gid"])
        os.chmod(target, row["mode"])
        for key, value in row["xattrs"].items():
            os.setxattr(target, key, base64.b64decode(value))
        os.utime(target, ns=(row["atime_ns"], row["mtime_ns"]))
    need(_equivalent(receipt["rows"], scan_tree(restored, receipt["owner"]), restored=True), "restored_cache_differs")
    source = Path(receipt["source"])
    parent_fd, destination_fd = _open_dir(source.parent), _open_dir(destination)
    try:
        parent_info = os.fstat(parent_fd)
        need((parent_info.st_dev, parent_info.st_ino) == (receipt["source_parent"]["device"], receipt["source_parent"]["inode"]), "restore_parent_changed")
        # Persist restored bytes/metadata and their directory entries before
        # publishing the restored source name. The protected archive remains.
        for row in reversed(receipt["rows"]):
            target = restored / _safe_relative(row["path"])
            synced = (_open_dir(target) if row["kind"] == "directory" else
                os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC))
            try:
                os.fsync(synced)
            finally:
                os.close(synced)
        os.fsync(destination_fd)
        _rename_noreplace(destination_fd, "restored", parent_fd, source.name)
        os.fsync(parent_fd)
        os.fsync(destination_fd)
    finally:
        os.close(parent_fd)
        os.close(destination_fd)
    return {"restored": True, "source": str(source)}


def reclaim_cache_archive(destination, *, remove=shutil.rmtree):
    destination = Path(destination)
    _protected(destination)
    receipt = json.loads((destination / "restore-catalogue.json").read_bytes())
    rows, source = receipt["rows"], Path(receipt["source"])
    verify_archive(destination / "content.tar.xz", rows, receipt["archive_sha256"])
    need(_equivalent(rows, scan_tree(source, receipt["owner"])), "cache_source_changed_before_reclamation")
    need(not active_references(rows), "cache_has_active_process_references")
    parent_fd, destination_fd = _open_dir(source.parent), _open_dir(destination)
    try:
        parent_info = os.fstat(parent_fd)
        need((parent_info.st_dev, parent_info.st_ino) == (receipt["source_parent"]["device"], receipt["source_parent"]["inode"]), "cache_parent_changed")
        _write_new(destination / "reclamation-intent.json", json.dumps({"at": time.time(), "source": str(source)}).encode())
        # Revalidate durability for pre-existing catalogues as well. A file
        # fsync alone does not persist the directory entry naming that file.
        for name in ("content.tar.xz", "restore-catalogue.json"):
            saved = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=destination_fd)
            try:
                os.fsync(saved)
            finally:
                os.close(saved)
        _sync_directories(destination.parent)
        os.fsync(destination_fd)
        _rename_noreplace(parent_fd, source.name, destination_fd, "quarantine")
        try:
            os.fsync(parent_fd)
            os.fsync(destination_fd)
        except BaseException:
            # Keep the actual original if persisting the isolation fails.
            _rename_noreplace(destination_fd, "quarantine", parent_fd, source.name)
            raise
    finally:
        os.close(parent_fd)
        os.close(destination_fd)
    quarantine = destination / "quarantine"
    try:
        need(_equivalent(rows, scan_tree(quarantine, receipt["owner"]), renamed=True), "isolated_cache_changed")
        need(not active_references(rows), "isolated_cache_has_active_process_references")
        need(shutil.rmtree.avoids_symlink_attacks, "safe_recursive_removal_unavailable")
        remove(quarantine)
        _sync_directories(destination)
        verify_archive(destination / "content.tar.xz", rows, receipt["archive_sha256"])
        result = {"completed": True, "all_original_bytes_preserved": True, "source": str(source),
                  "entries": len(rows), "restore_catalogue": str(destination / "restore-catalogue.json")}
        _write_new(destination / "completion.json", json.dumps(result, sort_keys=True).encode())
        _sync_directories(destination)
        return result
    except BaseException:
        if not source.exists():
            restore_cache_archive(destination)
        raise
