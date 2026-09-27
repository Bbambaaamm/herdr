"""Offline release/cutover contract tests; no privileged or live operations."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

import pytest

from deploy.herdr.cutover import cutover
from herdr import release


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def consumer(name: str) -> bytes:
    return (f"schema_version: 1\nconsumer: {name}\nrepository: Example/{name}\n"
            f"policy_profile: {name}-safe\nhard_invariants:\n  - safe_only\n"
            "inheritance:\n  child_may_expand_parent_permissions: false\n"
            "routing:\n  capability_aware: true\n  cost_aware: true\n").encode()


def minimal_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    (repo / "configs" / "consumers").mkdir(parents=True)
    (repo / "provenance").mkdir()
    for name in release.CONSUMERS:
        (repo / "configs" / "consumers" / f"{name}.yaml").write_bytes(consumer(name))
    (repo / "provenance" / "external-runtime-dependency.txt").write_text(
        "herdr 0.9.1\nhome=https://herdr.dev\nbinary_sha256=" + "a" * 64
        + "\nbinary_size=42\nbinary_path=/external/herdr\n"
        "note=External binary dependency is pinned.\n", encoding="utf-8")
    (repo / "payload.txt").write_text("bounded payload\n", encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "add", ".")
    git(repo, "update-index", "--chmod=+x", "payload.txt")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@localhost",
        "commit", "-qm", "release fixture")
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@localhost",
        "tag", "-a", "v1.2.3-rc.1", "-m", "fixture")
    monkeypatch.setattr(release, "PAYLOAD_PATHS", (
        "configs/consumers", "provenance/external-runtime-dependency.txt", "payload.txt"))
    return repo, commit


def test_consumer_contract_is_closed_and_permission_monotonic():
    files = {f"{name}.yaml": consumer(name) for name in release.CONSUMERS}
    assert len(release.consumer_digest(files)) == 64
    unsafe = consumer("quantlab").replace(b"false", b"true")
    with pytest.raises(release.ReleaseError, match="permission_inheritance_not_fail_closed"):
        release.parse_consumer(unsafe, "quantlab")


def test_release_build_is_deterministic_and_tamper_evident(tmp_path, monkeypatch):
    repo, commit = minimal_repo(tmp_path, monkeypatch)
    git(repo, "config", "core.autocrlf", "true")
    first, second = tmp_path / "first.tar.gz", tmp_path / "second.tar.gz"
    one = release.build_release(repo, "v1.2.3-rc.1", commit, first)
    two = release.build_release(repo, "v1.2.3-rc.1", commit, second)
    assert first.read_bytes() == second.read_bytes()
    assert one["archive_sha256"] == two["archive_sha256"]
    assert one["config_contract_sha256"] == release.consumer_digest(
        {f"{name}.yaml": consumer(name) for name in release.CONSUMERS})
    assert release.verify_archive(first)["commit"] == commit
    with tarfile.open(first, "r:gz") as archive:
        members = archive.getmembers()
        assert [member.name for member in members[1:]] == sorted(
            member.name for member in members[1:])
        modes = {member.name: member.mode for member in members}
        prefix = f"v1.2.3-rc.1-{commit[:12]}"
        assert modes[f"{prefix}/payload.txt"] == 0o555
        assert modes[f"{prefix}/configs/consumers/heating.yaml"] == 0o444
    damaged = tmp_path / "damaged.tar.gz"
    data = bytearray(first.read_bytes())
    data[len(data) // 2] ^= 1
    damaged.write_bytes(data)
    with pytest.raises((release.ReleaseError, tarfile.TarError, OSError, EOFError)):
        release.verify_archive(damaged)


def test_safe_extract_rejects_traversal_and_links(tmp_path):
    for name, kind in (("../escape", "file"), ("release/link", "link")):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            info = tarfile.TarInfo(name)
            if kind == "link":
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
                archive.addfile(info)
            else:
                payload = b"x"
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:") as archive:
            with pytest.raises(release.ReleaseError):
                release.safe_extract(archive, tmp_path / kind)


def test_cutover_helpers_are_atomic_and_never_drop_legacy_files(tmp_path):
    legacy, candidate = tmp_path / "legacy", tmp_path / "candidate"
    for root in (legacy, candidate):
        (root / "agent_platform_dashboard").mkdir(parents=True)
        (root / "deploy" / "agent_platform" / "production").mkdir(parents=True)
        (root / "agent_platform_dashboard" / "production_web.py").write_text("old")
        (root / "deploy" / "agent_platform" / "production" / "launch.py").write_text("same")
    (candidate / "agent_platform_dashboard" / "production_web.py").write_text("new")
    (candidate / "agent_platform_dashboard" / "production_release.py").write_text("added")
    result = cutover.compare_trees(candidate, legacy)
    assert result == {"unchanged": 1, "changed": 1, "added": 1, "removed": 0,
                      "candidate_files": 3, "legacy_files": 2}
    (candidate / "deploy" / "agent_platform" / "production" / "launch.py").unlink()
    with pytest.raises(release.ReleaseError, match="candidate_drops"):
        cutover.compare_trees(candidate, legacy)

    if os.name != "nt":
        links = tmp_path / "links"
        links.mkdir()
        first, second = tmp_path / "first", tmp_path / "second"
        first.mkdir(); second.mkdir()
        cutover.atomic_symlink(first, links / "current")
        assert (links / "current").resolve() == first
        cutover.atomic_symlink(second, links / "current")
        assert (links / "current").resolve() == second


def test_runtime_units_use_only_atomic_current_symlink():
    for name in cutover.UNITS:
        template = Path("deploy/agent_platform/production") / f"{name}.in"
        text = template.read_text(encoding="utf-8")
        if name.endswith(".service"):
            assert "/opt/herdr/current" in text
            assert "/opt/agent-platform/release" not in text


def test_deployed_document_is_closed_and_binds_config():
    value = cutover.deployed_document(
        {"tag": "v1.2.3", "commit": "a" * 40, "config_contract_sha256": "b" * 64},
        "b" * 64, 100)
    assert json.dumps(value, sort_keys=True) == json.dumps({
        "version": 1, "tag": "v1.2.3", "commit": "a" * 40,
        "config_sha256": "b" * 64, "deployed_at": 100}, sort_keys=True)
    with pytest.raises(release.ReleaseError, match="deployment_config_mismatch"):
        cutover.deployed_document(
            {"tag": "v1.2.3", "commit": "a" * 40, "config_contract_sha256": "b" * 64},
            "c" * 64, 100)
