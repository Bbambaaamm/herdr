import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import shutil
import stat
import sys
import tarfile

import pytest

from herdr import operation_archives as a

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux directory FD and mount contract")


@pytest.fixture
def cache(tmp_path, monkeypatch):
    source = tmp_path / "cache"
    (source / "nested").mkdir(parents=True)
    (source / "nested" / "payload").write_bytes(b"unique-cache-data" * 900)
    (source / "empty").write_bytes(b"")
    (source / "nested" / "payload").chmod(0o640)
    os.setxattr(source / "nested" / "payload", "user.retained", b"test-value")
    protected = tmp_path / "protected"
    protected.mkdir(mode=0o700)
    # Only replace root ancestry for the pytest-owned temporary parent.
    def fixture_ancestry(path):
        assert Path(path) == protected or protected in Path(path).parents
        assert not Path(path).is_symlink()
    monkeypatch.setattr(a, "_protected", fixture_ancestry)
    monkeypatch.setattr(a, "active_references", lambda rows: [])
    return source, protected, tmp_path


def prepare(cache):
    source, protected, scratch = cache
    return a.prepare_cache_archive(source, protected, owner=os.geteuid(), scratch=scratch)


def test_roundtrip_preserves_bytes_permissions_times_and_xattrs(cache):
    source = cache[0]
    before = a.scan_tree(source, os.geteuid())
    destination, receipt = prepare(cache)
    assert source.exists() and receipt["original_bytes_verified"]
    assert a.reclaim_cache_archive(destination)["all_original_bytes_preserved"]
    assert not source.exists()
    assert a.restore_cache_archive(destination)["restored"]
    assert a._equivalent(before, a.scan_tree(source, os.geteuid()), restored=True)
    assert os.getxattr(source / "nested/payload", "user.retained") == b"test-value"
    assert stat.S_IMODE((destination / "content.tar.xz").stat().st_mode) == 0o400


def test_extra_archive_member_rejected(cache):
    destination, receipt = prepare(cache)
    archive = destination / "extra.tar.xz"
    with lzma.open(archive, "wb") as out, tarfile.open(fileobj=out, mode="w|") as saved:
        for row in receipt["rows"]:
            item = tarfile.TarInfo(row["path"])
            item.mode, item.uid, item.gid = row["mode"], row["uid"], row["gid"]
            if row["kind"] == "directory":
                item.type = tarfile.DIRTYPE
                saved.addfile(item)
            else:
                data = (cache[0] / row["path"]).read_bytes()
                item.size = len(data)
                saved.addfile(item, io.BytesIO(data))
        saved.addfile(tarfile.TarInfo("unexpected"))
    with pytest.raises(a.ArchiveError, match="member_count"):
        a.verify_archive(archive, receipt["rows"], a.digest_file(archive))


def test_source_drift_never_removed(cache):
    destination, _ = prepare(cache)
    (cache[0] / "new-file").write_text("new data")
    with pytest.raises(a.ArchiveError, match="source_changed"):
        a.reclaim_cache_archive(destination)
    assert (cache[0] / "new-file").read_text() == "new data"


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_unsafe_members_rejected(cache, kind):
    source = cache[0]
    if kind == "symlink":
        (source / "alias").symlink_to(source / "nested/payload")
    elif kind == "hardlink":
        os.link(source / "nested/payload", source / "alias")
    else:
        os.mkfifo(source / "alias")
    with pytest.raises(a.ArchiveError, match="exclusive_member"):
        prepare(cache)
    assert (source / "nested/payload").exists()


def test_active_reference_blocks_removal(cache, monkeypatch):
    destination, _ = prepare(cache)
    monkeypatch.setattr(a, "active_references", lambda rows: [(123, "fd")])
    with pytest.raises(a.ArchiveError, match="active_process"):
        a.reclaim_cache_archive(destination)
    assert cache[0].exists()


def test_corrupt_archive_does_not_remove_source(cache):
    destination, _ = prepare(cache)
    (destination / "content.tar.xz").chmod(0o600)
    with (destination / "content.tar.xz").open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(a.ArchiveError, match="digest_changed"):
        a.reclaim_cache_archive(destination)
    assert cache[0].exists()


def test_partial_purge_failure_restores_everything(cache):
    destination, receipt = prepare(cache)
    def partial(path):
        (path / "nested/payload").unlink()
        raise OSError("injected failure")
    with pytest.raises(OSError, match="injected"):
        a.reclaim_cache_archive(destination, remove=partial)
    assert a._equivalent(receipt["rows"], a.scan_tree(cache[0], os.geteuid()), restored=True)
    assert not (destination / "completion.json").exists()


def test_source_replacement_never_overwritten_on_restore(cache):
    destination, _ = prepare(cache)
    a.reclaim_cache_archive(destination)
    cache[0].mkdir()
    (cache[0] / "new-owner-data").write_text("keep")
    with pytest.raises(FileExistsError):
        a.restore_cache_archive(destination)
    assert (cache[0] / "new-owner-data").read_text() == "keep"


def test_intent_replay_is_denied(cache):
    destination, _ = prepare(cache)
    (destination / "reclamation-intent.json").write_text("existing intent")
    with pytest.raises(FileExistsError):
        a.reclaim_cache_archive(destination)
    assert cache[0].exists()


def test_archive_source_overlap_denied(cache):
    with pytest.raises(a.ArchiveError, match="overlap"):
        a.prepare_cache_archive(cache[0], cache[0] / "archive", owner=os.geteuid())


def test_process_scan_detects_open_fd_and_mapping(tmp_path):
    source = tmp_path / "payload"
    source.write_bytes(b"body")
    info = source.stat()
    proc = tmp_path / "proc"
    process = proc / "99999999"
    (process / "fd").mkdir(parents=True)
    (process / "fd/3").symlink_to(source)
    device = f"{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}"
    (process / "maps").write_text(f"1000-2000 r--p 00000000 {device} {info.st_ino} hidden-name\n")
    refs = a.active_references([{"device": info.st_dev, "inode": info.st_ino}], proc=proc)
    assert (99999999, "fd") in refs and (99999999, "mapped_file") in refs


def test_process_inspection_error_fails_closed(tmp_path):
    proc = tmp_path / "proc"
    (proc / "99999999").mkdir(parents=True)
    (proc / "99999999/fd").write_text("invalid")
    with pytest.raises(a.ArchiveError, match="could_not_be_inspected"):
        a.active_references([], proc=proc)


def test_missing_directory_durability_never_allows_original_removal(cache,monkeypatch):
    destination,_=prepare(cache);original=a.os.fsync
    def unavailable(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):raise OSError('directory durability unavailable')
        return original(fd)
    monkeypatch.setattr(a.os,'fsync',unavailable)
    with pytest.raises(OSError,match='directory durability'):a.reclaim_cache_archive(destination)
    assert (cache[0]/'nested/payload').read_bytes()==b'unique-cache-data'*900


def test_prepared_archive_and_its_parent_names_are_fsynced(cache,monkeypatch):
    seen=[];original=a.os.fsync
    def record(fd):
        info=os.fstat(fd)
        if stat.S_ISDIR(info.st_mode):seen.append((info.st_dev,info.st_ino))
        return original(fd)
    monkeypatch.setattr(a.os,'fsync',record)
    destination,_=prepare(cache)
    for p in [destination,destination.parent]:
        info=p.stat();assert (info.st_dev,info.st_ino) in seen
