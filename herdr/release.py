"""Deterministic, fail-closed Herdr release bundle primitives."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import gzip
import hashlib
import io
import json
import os
import stat
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile
from typing import BinaryIO, Iterable


SCHEMA_VERSION = 1
TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z][0-9A-Za-z.-]{0,47})?")
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
CONSUMERS = ("heating", "herdr", "majak", "quantlab")
PAYLOAD_PATHS = (
    "README.md",
    "requirements-mcp.txt",
    "docs/architecture/MCP_GATEWAY.md",
    "docs/architecture/EXTERNAL_KNOWLEDGE.md",
    "docs/architecture/GITHUB_INTAKE_ADMISSION.md",
    "agent-stack",
    "agent_platform_dashboard/__init__.py",
    "agent_platform_dashboard/production_auth.py",
    "agent_platform_dashboard/production_contract.py",
    "agent_platform_dashboard/production_credentials.py",
    "agent_platform_dashboard/production_export.py",
    "agent_platform_dashboard/production_herdr.py",
    "agent_platform_dashboard/production_io.py",
    "agent_platform_dashboard/production_sources.py",
    "agent_platform_dashboard/production_web.py",
    "agent_platform_dashboard/static",
    "configs/consumers",
    "deploy/agent_platform/production",
    "deploy/herdr/cutover",
    "deploy/herdr/external-knowledge.example.json",
    "docs/CONSUMERS.md",
    "docs/VERSIONING_AND_DEPLOYMENT.md",
    "herdr",
    "skills",
    "docs/architecture/AGENT_SKILLS.md",
    "docs/architecture/CONTEXT_MEMORY.md",
    "docs/architecture/INVOCATION_POLICY_LAUNCH.md",
    "docs/architecture/COMPLETION_EVIDENCE.md",

    "docs/architecture/WORK_NODE_CONTRACT.md",
    "integrations/search-router",
    "provenance/external-runtime-dependency.txt",
)


class ReleaseError(ValueError):
    pass


def _need(value: bool, message: str) -> None:
    if not value:
        raise ReleaseError(message)


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def release_id(tag: str, commit: str) -> str:
    _need(bool(TAG.fullmatch(tag)), "invalid_tag")
    _need(bool(HEX40.fullmatch(commit)), "invalid_commit")
    return f"{tag}-{commit[:12]}"


def parse_external_dependency(data: bytes) -> dict[str, object]:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ReleaseError("invalid_external_dependency") from exc
    _need(lines[:1] == ["herdr 0.9.1"], "unexpected_external_version")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if not line or line.startswith("note="):
            continue
        key, separator, value = line.partition("=")
        _need(bool(separator) and key not in fields, "invalid_external_dependency")
        fields[key] = value
    _need(HEX64.fullmatch(fields.get("binary_sha256", "")) is not None,
          "invalid_external_digest")
    _need(fields.get("binary_size", "").isdigit() and int(fields["binary_size"]) > 0,
          "invalid_external_size")
    return {
        "name": "herdr",
        "version": "0.9.1",
        "sha256": fields["binary_sha256"],
        "size": int(fields["binary_size"]),
    }


def parse_consumer(data: bytes, expected: str) -> dict[str, object]:
    _need(expected in CONSUMERS, "unknown_consumer")
    try:
        text = data.decode("utf-8")
    except UnicodeError as exc:
        raise ReleaseError("invalid_consumer_encoding") from exc
    _need("\t" not in text and "#" not in text and "&" not in text and "*" not in text,
          "unsupported_consumer_yaml")
    scalars: dict[str, str] = {}
    nested: dict[str, dict[str, str]] = {}
    lists: dict[str, list[str]] = {}
    section: str | None = None
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("    ") or raw.startswith("   "):
            raise ReleaseError("invalid_consumer_indentation")
        if raw.startswith("  - "):
            _need(section == "hard_invariants", "unexpected_consumer_list")
            value = raw[4:]
            _need(bool(re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value)), "invalid_invariant")
            lists.setdefault(section, []).append(value)
            continue
        if raw.startswith("  "):
            _need(section in ("inheritance", "routing"), "unexpected_nested_consumer_key")
            key, separator, value = raw[2:].partition(": ")
            _need(bool(separator) and key not in nested.setdefault(section, {}),
                  "invalid_nested_consumer_key")
            nested[section][key] = value
            continue
        key, separator, value = raw.partition(":")
        _need(bool(separator) and key not in scalars and key not in nested and key not in lists,
              "invalid_consumer_key")
        if value:
            _need(value.startswith(" "), "invalid_consumer_scalar")
            scalars[key] = value[1:]
            section = None
        else:
            section = key
            if key == "hard_invariants":
                lists[key] = []
            else:
                nested[key] = {}
    _need(set(scalars) == {"schema_version", "consumer", "repository", "policy_profile"},
          "invalid_consumer_scalars")
    _need(set(lists) == {"hard_invariants"} and bool(lists["hard_invariants"]),
          "invalid_consumer_invariants")
    _need(len(lists["hard_invariants"]) == len(set(lists["hard_invariants"])),
          "duplicate_consumer_invariant")
    _need(set(nested) == {"inheritance", "routing"}, "invalid_consumer_sections")
    _need(scalars["schema_version"] == "1" and scalars["consumer"] == expected,
          "invalid_consumer_identity")
    _need(bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", scalars["repository"])),
          "invalid_consumer_repository")
    _need(bool(re.fullmatch(r"[a-z][a-z0-9-]{0,63}", scalars["policy_profile"])),
          "invalid_policy_profile")
    _need(nested["inheritance"] == {"child_may_expand_parent_permissions": "false"},
          "permission_inheritance_not_fail_closed")
    _need(nested["routing"] == {"capability_aware": "true", "cost_aware": "true"},
          "invalid_routing_contract")
    return {
        **scalars,
        "hard_invariants": tuple(lists["hard_invariants"]),
        "inheritance": nested["inheritance"],
        "routing": nested["routing"],
    }


def consumer_digest(files: dict[str, bytes]) -> str:
    _need(set(files) == {f"{name}.yaml" for name in CONSUMERS}, "incomplete_consumers")
    digest = hashlib.sha256()
    for name in sorted(files):
        expected = name.removesuffix(".yaml")
        parse_consumer(files[name], expected)
        digest.update(name.encode() + b"\0" + files[name] + b"\0")
    return digest.hexdigest()


def _safe_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    _need(not any(c in name for c in ("\\", "\0", ":")), "unsafe_archive_path")
    _need(name == str(path) and not path.is_absolute() and ".." not in path.parts and path.parts,
          "unsafe_archive_path")
    return path


@dataclass(frozen=True)
class ArchiveLimits:
    """Host-selected ceilings; none are read from the archive or its manifest."""

    max_members: int = 8192
    max_file_bytes: int = 64 * 1024 * 1024
    max_total_bytes: int = 256 * 1024 * 1024
    max_stream_bytes: int = 320 * 1024 * 1024
    max_compressed_bytes: int = 64 * 1024 * 1024
    max_path_bytes: int = 4096
    max_path_depth: int = 32
    max_expansion_ratio: int = 200
    max_metadata_bytes: int = 64 * 1024
    max_header_depth: int = 16

    def __post_init__(self) -> None:
        _need(all(type(value) is int and value > 0 for value in vars(self).values()),
              "invalid_archive_limits")


DEFAULT_ARCHIVE_LIMITS = ArchiveLimits()
_ARCHIVE_CHUNK_BYTES = 64 * 1024
_MAX_TAR_READ_BYTES = 1024 * 1024


class _BoundedCompressedReader:
    """Bound raw reads too: gzip header strings need not inflate any tar bytes."""

    def __init__(self, source: BinaryIO, limit: int):
        self.source = source
        self.limit = limit
        self.consumed = 0

    def read(self, size: int) -> bytes:
        _need(type(size) is int and 0 <= size <= _MAX_TAR_READ_BYTES,
              "archive_compressed_read_limit")
        requested = min(size, self.limit - self.consumed + 1)
        chunk = self.source.read(requested)
        _need(len(chunk) <= requested, "archive_compressed_read_overflow")
        self.consumed += len(chunk)
        _need(self.consumed <= self.limit, "archive_compressed_size_limit")
        return chunk

    def tell(self) -> int:
        return self.consumed


class _BoundedArchiveReader:
    """Bound inflation before tarfile can allocate extended-header payloads."""

    def __init__(self, source: BinaryIO, limit: int):
        self.source = source
        self.limit = limit
        self.consumed = 0

    def tell(self) -> int:
        return getattr(self, "position", 0)

    def seek(self, offset: int, whence: int = 0) -> int:
        # TarFile reads one byte behind the next header after extracting a file.
        # A small lookback avoids rewinding gzip and repeatedly inflating input.
        target = offset + self.tell() if whence == 1 else offset
        _need(whence in (0, 1) and type(target) is int and target >= 0,
              "archive_seek_limit")
        cache = getattr(self, "cache", b"")
        _need(target >= self.consumed - len(cache), "archive_backward_seek_limit")
        while self.consumed < target:
            self.position = self.consumed
            _need(bool(self.read(min(_ARCHIVE_CHUNK_BYTES, target - self.consumed))),
                  "truncated_archive_file")
        self.position = target
        return target

    def read(self, size: int) -> bytes:
        _need(type(size) is int and 0 <= size <= _MAX_TAR_READ_BYTES,
              "archive_metadata_read_limit")
        position = self.tell()
        cache = getattr(self, "cache", b"")
        replay = min(size, self.consumed - position)
        prefix = cache[position - (self.consumed - len(cache)):][:replay]
        requested = min(size - replay, self.limit - self.consumed + 1)
        chunk = self.source.read(requested)
        _need(len(chunk) <= requested, "archive_stream_read_overflow")
        self.consumed += len(chunk)
        _need(self.consumed <= self.limit, "archive_expansion_limit")
        self.cache = (cache + chunk)[-_MAX_TAR_READ_BYTES:]
        self.position = position + len(prefix) + len(chunk)
        return prefix + chunk


def _bounded_tar_info(limits: ArchiveLimits):
    class BoundedTarInfo(tarfile.TarInfo):
        def _proc_member(self, archive):
            # tarfile resolves PAX/GNU metadata recursively before yielding a
            # member. Count those hidden headers and limit recursion as well.
            count = getattr(archive, "_bounded_headers", 0) + 1
            depth = getattr(archive, "_bounded_header_depth", 0) + 1
            archive._bounded_headers = count
            _need(count <= limits.max_members, "archive_member_limit")
            _need(depth <= limits.max_header_depth, "archive_metadata_depth_limit")
            metadata = self.type in (tarfile.XHDTYPE, tarfile.XGLTYPE,
                                    tarfile.SOLARIS_XHDTYPE, tarfile.GNUTYPE_LONGNAME,
                                    tarfile.GNUTYPE_LONGLINK)
            _need(not metadata or 0 <= self.size <= limits.max_metadata_bytes,
                  "archive_metadata_size_limit")
            _need(self.type != tarfile.GNUTYPE_SPARSE, "unsupported_archive_member")
            archive._bounded_header_depth = depth
            try:
                return super()._proc_member(archive)
            finally:
                archive._bounded_header_depth = depth - 1
        def _proc_pax(self, archive):
            # Reject sparse extensions before stdlib reads a sparse map from a
            # subsequent file body. A post-parse member.sparse check is too late.
            if self.type == tarfile.XGLTYPE:
                total = getattr(archive, "_bounded_global_metadata", 0) + self.size
                _need(total <= limits.max_metadata_bytes, "archive_global_metadata_limit")
                archive._bounded_global_metadata = total
            position = archive.fileobj.tell()
            raw = archive.fileobj.read(self._block(self.size))
            _need(len(raw) == self._block(self.size), "truncated_archive_metadata")
            payload = raw[:self.size]
            offset = 0
            while offset < len(payload):
                space = payload.find(b" ", offset)
                digits = payload[offset:space] if space >= 0 else b""
                _need(1 <= len(digits) <= 10 and digits.isdigit(), "invalid_archive_metadata")
                length = int(digits)
                end = offset + length
                _need(length >= 5 and space + 1 < end <= len(payload)
                      and payload[end - 1:end] == b"\n", "invalid_archive_metadata")
                key, equals, _ = payload[space + 1:end - 1].partition(b"=")
                _need(bool(key) and equals == b"=", "invalid_archive_metadata")
                _need(not key.startswith(b"GNU.sparse."), "unsupported_archive_member")
                offset = end
            archive.fileobj.seek(position)
            return super()._proc_pax(archive)
    return BoundedTarInfo


@contextmanager
def _extraction_destination(destination: Path):
    """Only remove objects created in a new/empty private extraction directory."""
    destination = Path(destination)
    created: list[tuple[Path, bool]] = []
    try:
        _need(not destination.is_symlink(), "unsafe_extraction_destination")
        if not destination.exists():
            destination.mkdir(mode=0o700)
            created.append((destination, True))
        _need(destination.is_dir() and not any(destination.iterdir()),
              "extraction_destination_not_empty")
        yield destination, created
    except BaseException:
        for path, directory in reversed(created):
            try:
                if directory:
                    path.rmdir()
                else:
                    path.unlink()
            except FileNotFoundError:
                pass
        raise


def _uncached_members(archive: tarfile.TarFile, limits: ArchiveLimits):
    if not isinstance(archive, tarfile.TarFile):
        yield from archive
        return
    # safe_extract also accepts a caller-owned TarFile that was already partly
    # read. Preserve that bounded prefix; external releases start with one item.
    _need(len(archive.members) <= limits.max_members, "archive_member_limit")
    prefix = tuple(archive.members)
    archive.members.clear()
    if archive.firstmember is not None:
        first = archive.next()
        if not prefix:
            prefix = (first,)
        else:
            _need(first is prefix[0], "invalid_archive_member_cache")
    yield from prefix
    if archive._loaded:
        return
    while True:
        member = archive.next()
        # TarFile.__iter__ retains every TarInfo (and its global PAX dict copy).
        # Links are disallowed, so later lookup never needs this cache.
        archive.members.clear()
        if member is None:
            return
        yield member


def _extract_members(archive: tarfile.TarFile, destination: Path,
                     limits: ArchiveLimits, created: list[tuple[Path, bool]]) -> None:
    count = total = 0
    seen: set[str] = set()
    # Do not retain every TarInfo/global metadata dictionary while iterating.
    for member in _uncached_members(archive, limits):
        count += 1
        _need(count <= limits.max_members, "archive_member_limit")
        path = _safe_name(member.name)
        _need(len(member.name.encode("utf-8")) <= limits.max_path_bytes
              and len(path.parts) <= limits.max_path_depth, "archive_path_limit")
        _need(member.name not in seen, "duplicate_archive_member")
        seen.add(member.name)
        _need(member.type in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
              and member.sparse is None, "unsupported_archive_member")
        _need(type(member.size) is int and 0 <= member.size <= limits.max_file_bytes,
              "archive_file_size_limit")
        _need(not member.isdir() or member.size == 0, "invalid_archive_directory_size")
        current = destination
        for component in path.parts[:-1]:
            current = current / component
            if current.exists():
                _need(current.is_dir() and not current.is_symlink(), "unsafe_archive_parent")
            else:
                _need(len(created) < limits.max_members + 1, "archive_object_limit")
                current.mkdir()
                created.append((current, True))
        target = destination.joinpath(*path.parts)
        if member.isdir():
            if not target.exists():
                _need(len(created) < limits.max_members + 1, "archive_object_limit")
                target.mkdir()
                created.append((target, True))
            _need(target.is_dir() and not target.is_symlink(), "unsafe_archive_directory")
            continue
        _need(total + member.size <= limits.max_total_bytes, "archive_total_size_limit")
        stream = archive.extractfile(member)
        _need(stream is not None, "missing_archive_file")
        _need(len(created) < limits.max_members + 1, "archive_object_limit")
        copied = 0
        with stream, target.open("xb") as output:
            created.append((target, False))
            while chunk := stream.read(_ARCHIVE_CHUNK_BYTES):
                copied += len(chunk)
                _need(len(chunk) <= _ARCHIVE_CHUNK_BYTES and copied <= member.size
                      and copied <= limits.max_file_bytes, "archive_actual_file_size_limit")
                _need(total + len(chunk) <= limits.max_total_bytes, "archive_actual_total_size_limit")
                output.write(chunk)
                total += len(chunk)
        _need(copied == member.size, "truncated_archive_file")
        target.chmod(member.mode & 0o755)


def safe_extract(archive: tarfile.TarFile, destination: Path, *,
                 limits: ArchiveLimits = DEFAULT_ARCHIVE_LIMITS) -> None:
    """Bound members and actual extracted bytes; input parsing must also be bounded.

    Release/cutover entrypoints use extract_archive(), which bounds gzip inflation
    and metadata reads before tarfile parses even the first member.
    """
    with _extraction_destination(destination) as (folder, created):
        _extract_members(archive, folder, limits, created)


def extract_archive(path: Path, destination: Path, *,
                    limits: ArchiveLimits = DEFAULT_ARCHIVE_LIMITS) -> None:
    """Stream a gzip release with resource bounds and transactional cleanup."""
    with _extraction_destination(destination) as (folder, created):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        with os.fdopen(fd, "rb", buffering=0) as source:
            before = os.fstat(source.fileno())
            _need(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= limits.max_compressed_bytes,
                  "archive_compressed_size_limit")
            inflation_limit = min(limits.max_stream_bytes,
                                  max(_MAX_TAR_READ_BYTES, before.st_size * limits.max_expansion_ratio))
            try:
                compressed = _BoundedCompressedReader(source, before.st_size)
                with gzip.GzipFile(fileobj=compressed, mode="rb") as inflated:
                    reader = _BoundedArchiveReader(inflated, inflation_limit)
                    with tarfile.open(fileobj=reader, mode="r:",
                                      tarinfo=_bounded_tar_info(limits)) as archive:
                        _extract_members(archive, folder, limits, created)
                        # Validate gzip trailers/concatenated streams, including
                        # bytes after tar's end marker, within the same budget.
                        while reader.read(_ARCHIVE_CHUNK_BYTES):
                            pass
            except (OSError, EOFError, tarfile.TarError) as exc:
                raise ReleaseError("invalid_or_truncated_release_archive") from exc
            after = os.fstat(source.fileno())
            _need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                  == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                  "release_archive_changed")


def file_manifest(root: Path, *, exclude: Iterable[str] = ()) -> bytes:
    excluded = set(exclude)
    lines = []
    files = (path for path in root.rglob("*") if path.is_file())
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        _need(not path.is_symlink(), "release_symlink_forbidden")
        lines.append(f"{sha256(path.read_bytes())}  {relative}\n")
    return "".join(lines).encode()


def verify_tree(root: Path) -> dict[str, object]:
    _need(root.is_dir() and not root.is_symlink(), "release_root_invalid")
    release_path = root / "RELEASE.json"
    manifest_path = root / "MANIFEST.sha256"
    try:
        release = json.loads(release_path.read_bytes())
    except (OSError, ValueError, UnicodeError) as exc:
        raise ReleaseError("invalid_release_metadata") from exc
    _need(type(release) is dict and set(release) == {
        "schema_version", "tag", "commit", "commit_time", "config_contract_sha256",
        "external_dependency", "payload_manifest_sha256",
    }, "invalid_release_metadata")
    _need(release["schema_version"] == SCHEMA_VERSION, "invalid_release_schema")
    _need(release_id(release["tag"], release["commit"]) == root.name, "release_identity_mismatch")
    _need(type(release["commit_time"]) is int and release["commit_time"] >= 0,
          "invalid_commit_time")
    _need(HEX64.fullmatch(release["config_contract_sha256"]) is not None,
          "invalid_config_digest")
    dependency = release["external_dependency"]
    _need(type(dependency) is dict and set(dependency) == {"name", "version", "sha256", "size"},
          "invalid_external_dependency")
    _need(dependency["name"] == "herdr" and dependency["version"] == "0.9.1"
          and HEX64.fullmatch(dependency["sha256"]) is not None
          and type(dependency["size"]) is int and dependency["size"] > 0,
          "invalid_external_dependency")
    manifest = manifest_path.read_bytes()
    _need(sha256(manifest) == release["payload_manifest_sha256"], "manifest_digest_mismatch")
    expected: dict[str, str] = {}
    for line in manifest.decode("ascii").splitlines():
        digest, separator, name = line.partition("  ")
        _need(bool(separator) and HEX64.fullmatch(digest) is not None and name not in expected,
              "invalid_manifest")
        _safe_name(name)
        expected[name] = digest
    actual = {}
    normalized_release = canonical_json({**release, "payload_manifest_sha256": "0" * 64})
    for path in root.rglob("*"):
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        relative = path.relative_to(root).as_posix()
        actual[relative] = sha256(normalized_release if relative == "RELEASE.json" else path.read_bytes())
    _need(actual == expected, "release_payload_mismatch")
    consumers = {name: (root / "configs" / "consumers" / name).read_bytes()
                 for name in (f"{consumer}.yaml" for consumer in CONSUMERS)}
    _need(consumer_digest(consumers) == release["config_contract_sha256"],
          "config_contract_mismatch")
    return release


def verify_archive(path: Path) -> dict[str, object]:
    _need(path.is_file() and not path.is_symlink(), "release_archive_invalid")
    with tempfile.TemporaryDirectory(prefix="herdr-verify-") as folder:
        destination = Path(folder)
        extract_archive(path, destination)
        roots = list(destination.iterdir())
        _need(len(roots) == 1 and roots[0].is_dir(), "release_archive_root_invalid")
        return verify_tree(roots[0])


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                            text=not binary)
    return result.stdout if binary else result.stdout.strip()


def build_release(repo: Path, tag: str, commit: str, output: Path) -> dict[str, object]:
    identifier = release_id(tag, commit)
    _need(_git(repo, "rev-parse", f"refs/tags/{tag}^{{commit}}") == commit,
          "tag_commit_mismatch")
    _need(_git(repo, "cat-file", "-t", f"refs/tags/{tag}") == "tag", "annotated_tag_required")
    _need(_git(repo, "status", "--porcelain", "--untracked-files=no") == "", "dirty_repository")
    commit_time = int(_git(repo, "show", "-s", "--format=%ct", commit))
    tree = _git(repo, "ls-tree", "-r", commit, "--", *PAYLOAD_PATHS)
    executable_paths = {
        line.split(maxsplit=3)[3]
        for line in tree.splitlines()
        if line.startswith("100755 ")
    }
    # Archive committed bytes, never platform-specific checkout conversions.
    archive_data = _git(repo, "-c", "core.autocrlf=false", "archive", "--format=tar",
                        commit, "--", *PAYLOAD_PATHS, binary=True)
    with tempfile.TemporaryDirectory(prefix="herdr-build-") as folder:
        staging = Path(folder) / identifier
        staging.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive_data), mode="r:") as archive:
            safe_extract(archive, staging)
        consumers = {name: (staging / "configs" / "consumers" / name).read_bytes()
                     for name in (f"{consumer}.yaml" for consumer in CONSUMERS)}
        dependency = parse_external_dependency(
            (staging / "provenance" / "external-runtime-dependency.txt").read_bytes())
        release = {
            "schema_version": SCHEMA_VERSION,
            "tag": tag,
            "commit": commit,
            "commit_time": commit_time,
            "config_contract_sha256": consumer_digest(consumers),
            "external_dependency": dependency,
            "payload_manifest_sha256": "0" * 64,
        }
        (staging / "RELEASE.json").write_bytes(canonical_json(release))
        # RELEASE.json binds the manifest and is itself in it. Break the cycle by
        # storing its digest line with the payload_manifest_sha256 field normalized.
        normalized = canonical_json(release)
        entries = []
        files = (path for path in staging.rglob("*") if path.is_file())
        for item in sorted(files, key=lambda path: path.relative_to(staging).as_posix()):
            relative = item.relative_to(staging).as_posix()
            data = normalized if relative == "RELEASE.json" else item.read_bytes()
            entries.append(f"{sha256(data)}  {relative}\n")
        manifest = "".join(entries).encode()
        release["payload_manifest_sha256"] = sha256(manifest)
        (staging / "RELEASE.json").write_bytes(canonical_json(release))
        (staging / "MANIFEST.sha256").write_bytes(manifest)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped:
                with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    items = [staging, *staging.rglob("*")]
                    items.sort(key=lambda item: "" if item == staging else
                               item.relative_to(staging).as_posix())
                    for item in items:
                        relative = Path(identifier) / item.relative_to(staging)
                        payload_name = item.relative_to(staging).as_posix()
                        info = archive.gettarinfo(str(item), arcname=relative.as_posix())
                        info.uid = info.gid = 0
                        info.uname = info.gname = "root"
                        info.mtime = commit_time
                        if info.isdir():
                            info.mode = 0o555
                            archive.addfile(info)
                        else:
                            info.mode = 0o555 if payload_name in executable_paths else 0o444
                            with item.open("rb") as stream:
                                archive.addfile(info, stream)
    verified = verify_archive(output)
    _need(verified == release, "built_release_verification_failed")
    return {**release, "archive_sha256": sha256(output.read_bytes()), "archive": str(output)}
