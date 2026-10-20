"""Offline extraction bounds: tiny fixtures exercise host-selected ceilings."""
import gzip
import io
import tarfile
from dataclasses import replace

import pytest

from herdr import release
from deploy.herdr.cutover import cutover


def bundle(tmp_path, entries, *, raw_tail=b""):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, data, kind in entries:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.size = len(data) if kind == tarfile.REGTYPE else 0
            member.linkname = "/outside" if kind in (tarfile.LNKTYPE, tarfile.SYMTYPE) else ""
            archive.addfile(member, io.BytesIO(data) if member.size else None)
    path = tmp_path / "input.tar.gz"
    path.write_bytes(gzip.compress(raw.getvalue() + raw_tail))
    return path


def limits(**overrides):
    return replace(release.DEFAULT_ARCHIVE_LIMITS, **overrides)


def test_valid_archive_uses_forward_reader_and_keeps_modes(tmp_path):
    path = bundle(tmp_path, [("root/a", b"a" * 512, tarfile.REGTYPE),
                             ("root/b", b"ok", tarfile.REGTYPE)])
    target = tmp_path / "extracted"
    release.extract_archive(path, target)
    assert (target / "root/a").read_bytes() == b"a" * 512
    assert (target / "root/b").read_bytes() == b"ok"


@pytest.mark.parametrize("bound,entries,error", [
    ({"max_members": 1}, [("a", b"", tarfile.REGTYPE), ("b", b"", tarfile.REGTYPE)], "member_limit"),
    ({"max_file_bytes": 3}, [("a", b"abcd", tarfile.REGTYPE)], "file_size_limit"),
    ({"max_total_bytes": 5}, [("a", b"abc", tarfile.REGTYPE), ("b", b"def", tarfile.REGTYPE)], "total_size_limit"),
    ({"max_path_depth": 2}, [("a/b/c", b"", tarfile.REGTYPE)], "path_limit"),
    ({"max_path_bytes": 3}, [("long", b"", tarfile.REGTYPE)], "path_limit"),
    ({"max_members": 2}, [("a/b/c/d", b"", tarfile.REGTYPE)], "object_limit"),
    ({}, [("a", b"x", tarfile.REGTYPE), ("a", b"x", tarfile.REGTYPE)], "duplicate"),
])
def test_resource_limits_reject_and_remove_partial_tree(tmp_path, bound, entries, error):
    path = bundle(tmp_path, entries)
    target = tmp_path / "extracted"
    with pytest.raises(release.ReleaseError, match=error):
        release.extract_archive(path, target, limits=limits(**bound))
    assert not target.exists()


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE,
                                  tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.GNUTYPE_SPARSE])
def test_links_devices_and_sparse_files_denied(tmp_path, kind):
    path = bundle(tmp_path, [("bad", b"", kind)])
    with pytest.raises(release.ReleaseError, match="unsupported_archive_member"):
        release.extract_archive(path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("name", ["../outside", "/absolute", "a/../../outside", "a\\b", "C:bad"])
def test_paths_denied_without_escape(tmp_path, name):
    path = bundle(tmp_path, [(name, b"x", tarfile.REGTYPE)])
    with pytest.raises(release.ReleaseError, match="unsafe_archive_path"):
        release.extract_archive(path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_existing_data_and_symlink_destination_preserved(tmp_path):
    path = bundle(tmp_path, [("a", b"x", tarfile.REGTYPE)])
    target = tmp_path / "out"
    target.mkdir()
    (target / "keep").write_bytes(b"original")
    with pytest.raises(release.ReleaseError, match="not_empty"):
        release.extract_archive(path, target)
    assert (target / "keep").read_bytes() == b"original"
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(release.ReleaseError, match="unsafe_extraction_destination"):
        release.extract_archive(path, link)
    assert link.is_symlink()


def test_stream_limit_and_hidden_tail_are_counted(tmp_path):
    path = bundle(tmp_path, [("a", b"x", tarfile.REGTYPE)], raw_tail=b"z" * 40000)
    target = tmp_path / "out"
    with pytest.raises(release.ReleaseError, match="expansion_limit"):
        release.extract_archive(path, target, limits=limits(max_stream_bytes=12000))
    assert not target.exists()


def test_gzip_crc_failure_cleans_previous_members(tmp_path):
    path = bundle(tmp_path, [("a", b"first", tarfile.REGTYPE)])
    content = bytearray(path.read_bytes())
    content[-8] ^= 1
    path.write_bytes(content)
    with pytest.raises(release.ReleaseError, match="invalid_or_truncated"):
        release.extract_archive(path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_huge_pax_header_fails_before_large_metadata_read(tmp_path):
    member = tarfile.TarInfo("extended")
    member.type = tarfile.XHDTYPE
    member.size = 16 * 1024 * 1024
    path = tmp_path / "huge-pax.tar.gz"
    # Header only: the declared size must not cause a 16 MiB allocation/read.
    path.write_bytes(gzip.compress(member.tobuf(format=tarfile.USTAR_FORMAT)))
    with pytest.raises(release.ReleaseError, match="metadata.*limit"):
        release.extract_archive(path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_actual_stream_bytes_cannot_exceed_declared_member(tmp_path):
    member = tarfile.TarInfo("a")
    member.size = 1
    class DishonestArchive:
        def __iter__(self): return iter([member])
        def extractfile(self, member): return io.BytesIO(b"more than one")
        def getmembers(self): raise AssertionError("unbounded member enumeration")
    with pytest.raises(release.ReleaseError, match="actual_file_size_limit"):
        release.safe_extract(DishonestArchive(), tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_short_actual_stream_cannot_be_accepted(tmp_path):
    member = tarfile.TarInfo("a")
    member.size = 5
    class ShortArchive:
        def __iter__(self): return iter([member])
        def extractfile(self, member): return io.BytesIO(b"x")
    with pytest.raises(release.ReleaseError, match="truncated_archive_file"):
        release.safe_extract(ShortArchive(), tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_compressed_limit_is_checked_before_parsing(tmp_path):
    path = bundle(tmp_path, [("a", b"x", tarfile.REGTYPE)])
    with pytest.raises(release.ReleaseError, match="compressed_size_limit"):
        release.extract_archive(path, tmp_path / "out", limits=limits(max_compressed_bytes=1))
    assert not (tmp_path / "out").exists()


def test_cutover_extraction_cannot_bypass_resource_bounds(tmp_path, monkeypatch):
    called = []
    def denied(archive, destination):
        called.append((archive, destination))
        raise release.ReleaseError("archive_member_limit")
    monkeypatch.setattr(cutover, "extract_archive", denied)
    monkeypatch.setattr(cutover, "verify_tree", lambda _: pytest.fail("verification after denial"))
    with pytest.raises(release.ReleaseError, match="archive_member_limit"):
        cutover.extract_candidate(tmp_path / "archive", tmp_path / "out")
    assert len(called) == 1


def test_defaults_are_positive_immutable_host_limits():
    with pytest.raises(release.ReleaseError, match="invalid_archive_limits"):
        limits(max_members=0)
    with pytest.raises(release.ReleaseError, match="invalid_archive_limits"):
        limits(max_members=True)


def test_hidden_metadata_headers_count_against_member_budget(tmp_path):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for _ in range(3):
            header = tarfile.TarInfo("metadata")
            header.type = tarfile.XGLTYPE
            header.size = 0
            archive.addfile(header)
        header = tarfile.TarInfo("a")
        archive.addfile(header)
    path = tmp_path / "hidden.tar.gz"
    path.write_bytes(gzip.compress(raw.getvalue()))
    with pytest.raises(release.ReleaseError, match="member_limit"):
        release.extract_archive(path, tmp_path / "out", limits=limits(max_members=2))
    assert not (tmp_path / "out").exists()


def test_nested_metadata_depth_is_bounded_before_python_recursion(tmp_path):
    raw = b""
    for _ in range(4):
        header = tarfile.TarInfo("metadata")
        header.type = tarfile.XHDTYPE
        header.size = 0
        raw += header.tobuf()
    raw += tarfile.TarInfo("a").tobuf() + b"\0" * 1024
    path = tmp_path / "nested.tar.gz"
    path.write_bytes(gzip.compress(raw))
    with pytest.raises(release.ReleaseError, match="metadata_depth_limit"):
        release.extract_archive(path, tmp_path / "out", limits=limits(max_header_depth=2))
    assert not (tmp_path / "out").exists()


def test_growing_gzip_optional_header_stops_at_snapshot_byte_limit(tmp_path, monkeypatch):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        member = tarfile.TarInfo("root/a")
        member.size = 1
        archive.addfile(member, io.BytesIO(b"a"))
    path = tmp_path / "input.tar.gz"
    path.write_bytes(gzip.compress(raw.getvalue()))
    initial_bytes = path.stat().st_size
    assert initial_bytes < 128

    # A second valid empty gzip member has a large optional filename. Parsing
    # that filename consumes compressed input without yielding inflated bytes.
    # Grow only this synthetic file after the initial fstat and before gzip read.
    tail = (b"\x1f\x8b\x08\x08" + b"\0" * 4 + b"\0\xff"
            + b"x" * (1024 * 1024) + b"\0"
            + b"\x03\x00" + b"\0" * 8)
    saved_fdopen = release.os.fdopen
    observed = {"raw_bytes": 0, "grew": False}

    class ObservedRaw:
        def __init__(self, source):
            self.source = source

        def __getattr__(self, name):
            return getattr(self.source, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.source.__exit__(*args)

        def read(self, size=-1):
            if not observed["grew"]:
                observed["grew"] = True
                with path.open("ab") as output:
                    output.write(tail)
            body = self.source.read(size)
            observed["raw_bytes"] += len(body)
            return body

    monkeypatch.setattr(release.os, "fdopen",
                        lambda *args, **kwargs: ObservedRaw(saved_fdopen(*args, **kwargs)))
    target = tmp_path / "output"
    with pytest.raises(release.ReleaseError):
        release.extract_archive(
            path, target,
            limits=replace(release.DEFAULT_ARCHIVE_LIMITS,
                           max_compressed_bytes=128, max_stream_bytes=20000),
        )
    assert observed["grew"] is True
    # The one-byte overflow probe is the only permitted read past the snapshot.
    assert observed["raw_bytes"] <= initial_bytes + 1
    assert not target.exists()
