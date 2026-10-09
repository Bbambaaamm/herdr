"""Deterministic, fail-closed Herdr release bundle primitives."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
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
    "docs/CONSUMERS.md",
    "docs/VERSIONING_AND_DEPLOYMENT.md",
    "herdr",
    "skills",
    "docs/architecture/AGENT_SKILLS.md",
    "docs/architecture/CONTEXT_MEMORY.md",
    "docs/architecture/INVOCATION_POLICY_LAUNCH.md",
    "docs/architecture/IMMUTABLE_PROFILE_NAMESPACE_129.md",
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
    _need(name == str(path) and not path.is_absolute() and ".." not in path.parts and path.parts,
          "unsafe_archive_path")
    return path


def safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    for member in archive.getmembers():
        path = _safe_name(member.name)
        _need(member.isfile() or member.isdir(), "unsupported_archive_member")
        target = destination.joinpath(*path.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        if member.isdir():
            target.mkdir(exist_ok=True)
            continue
        stream = archive.extractfile(member)
        _need(stream is not None, "missing_archive_file")
        with target.open("xb") as output:
            while chunk := stream.read(1024 * 1024):
                output.write(chunk)
        target.chmod(member.mode & 0o755)


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
        with tarfile.open(path, "r:gz") as archive:
            safe_extract(archive, destination)
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
