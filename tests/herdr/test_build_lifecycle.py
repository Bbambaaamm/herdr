"""Bounded read-only build inventory: no delete, approval or model calls."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from herdr.build_lifecycle import BuildInventoryError, inventory, scan_one, _open_dir


def root(tmp_path):
    base = tmp_path / "scratch"
    base.mkdir(mode=0o700)
    return base


def candidate(base, name="herdr-hermes-build-case1"):
    path = base / name
    path.mkdir(mode=0o700)
    (path / "sample.log").write_bytes(b"offline evidence")
    return path


def test_unregistered_build_is_observed_never_deletable(tmp_path):
    base = root(tmp_path)
    target = candidate(base)
    before = (target / "sample.log").read_bytes()
    result = inventory(base, (target.name,))
    row = result["candidates"][0]
    assert row["state"] == "BLOCKED_REVIEW"
    assert not row["can_delete"]
    assert not row["cleanup_authorized"]
    assert "NOT_REGISTERED_LEGACY_BUILD" in row["blockers"]
    assert result["deletion_performed"] is False
    assert result["model_calls"] == 0
    assert row["measurement_complete"] is True
    assert row["allocated_bytes_observed"] > 0
    assert (target / "sample.log").read_bytes() == before


def test_manifest_is_declarative_only_not_host_authority(tmp_path):
    base = root(tmp_path)
    target = candidate(base)
    manifest = {
        "schema_version": 1,
        "build_id": target.name,
        "source_commit": "a" * 40,
        "state": "CLEANUP_ELIGIBLE",
        "cleanup_approved": True,
    }
    (target / "herdr-build-manifest.json").write_text(json.dumps(manifest))
    result = inventory(base, (target.name,))
    row = result["candidates"][0]
    assert row["manifest_status"] == "UNTRUSTED_DECLARATION_ONLY"
    assert row["manifest"]["declared_state"] == "CLEANUP_ELIGIBLE"
    assert "MANIFEST_NOT_HOST_ATTESTED" in row["blockers"]
    assert row["can_delete"] is False


def test_symlink_candidate_is_denied_without_traversal(tmp_path):
    base = root(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    target = base / "herdr-hermes-build-evil"
    target.symlink_to(outside, target_is_directory=True)
    with pytest.raises(BuildInventoryError, match="OWNER_OR_TYPE"):
        inventory(base, (target.name,))
    assert list(outside.iterdir()) == []


def test_symlink_inside_tree_is_recorded_not_followed(tmp_path):
    base = root(tmp_path)
    target = candidate(base)
    (target / "external").symlink_to(tmp_path, target_is_directory=True)
    result = inventory(base, (target.name,))
    row = result["candidates"][0]
    assert row["symlinks_observed"] == 1
    assert "SYMLINKS_PRESENT" in row["blockers"]
    assert row["can_delete"] is False


def test_bound_limits_do_not_claim_complete_measurement(tmp_path):
    base = root(tmp_path)
    target = candidate(base)
    for i in range(25):
        (target / ("file" + str(i))).write_bytes(b"x")
    row = inventory(base, (target.name,), max_entries=5)["candidates"][0]
    assert row["entries_observed"] == 5
    assert row["measurement_complete"] is False
    assert "TRAVERSAL_INCOMPLETE" in row["blockers"]


@pytest.mark.parametrize("name", [
    "other-root", "../herdr-hermes-build-case1", "herdr-hermes-build/child",
    "herdr-hermes-build-\x00", ".",
])
def test_unapproved_names_denied(tmp_path, name):
    base = root(tmp_path)
    with pytest.raises(BuildInventoryError, match="CANDIDATE_NAME_NOT_ALLOWED"):
        inventory(base, (name,))


def test_rejects_duplicate_candidates(tmp_path):
    base = root(tmp_path)
    candidate(base)
    with pytest.raises(BuildInventoryError, match="BOUNDED_UNIQUE"):
        inventory(base, ("herdr-hermes-build-case1", "herdr-hermes-build-case1"))


def test_symlink_root_rejected(tmp_path):
    base = root(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(base, target_is_directory=True)
    with pytest.raises(BuildInventoryError, match="ABSOLUTE_NO_SYMLINK"):
        inventory(alias, ("herdr-hermes-build-case1",))


def test_symlinked_ancestor_in_root_denied(tmp_path):
    base = root(tmp_path)
    candidate(base)
    alias = tmp_path / "shortcut"
    alias.symlink_to(base, target_is_directory=True)
    with pytest.raises((BuildInventoryError, OSError)):
        inventory(alias / ".", ("herdr-hermes-build-case1",))


def test_invalid_manifest_does_not_crash_scanner(tmp_path):
    base = root(tmp_path)
    target = candidate(base)
    (target / "herdr-build-manifest.json").write_bytes(b"{garbage")
    row = inventory(base, (target.name,))["candidates"][0]
    assert row["manifest_status"] == "MANIFEST_INVALID"
    assert row["can_delete"] is False


def test_symlink_manifest_is_rejected(tmp_path):
    base = root(tmp_path)
    target = candidate(base)
    (target / "herdr-build-manifest.json").symlink_to(tmp_path / "absent.json")
    row = inventory(base, (target.name,))["candidates"][0]
    assert row["manifest_status"] in ("MANIFEST_OPEN_DENIED", "MANIFEST_UNSAFE")
    assert not row["can_delete"]


def test_unreadable_or_changed_inode_returns_only_blocked(tmp_path, monkeypatch):
    import herdr.build_lifecycle as module
    base = root(tmp_path)
    target = candidate(base)
    real = module._walk

    def uncertain(fd, dev, state, depth, seen):
        real(fd, dev, state, depth, seen)
        state.boundary_changes += 1

    monkeypatch.setattr(module, "_walk", uncertain)
    row = inventory(base, (target.name,))["candidates"][0]
    assert "FILESYSTEM_OR_IDENTITY_BOUNDARY_UNCERTAIN" in row["blockers"]
    assert not row["measurement_complete"]
    assert not row["can_delete"]


def test_no_delete_api_or_process_calls(tmp_path, monkeypatch):
    import shutil
    import socket
    import herdr.build_lifecycle as module

    def blocked(*args, **kwargs):
        raise AssertionError("side effect attempted")

    monkeypatch.setattr(os, "unlink", blocked)
    monkeypatch.setattr(os, "rmdir", blocked)
    monkeypatch.setattr(shutil, "rmtree", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    base = root(tmp_path)
    target = candidate(base)
    assert inventory(base, (target.name,))["deletion_performed"] is False
    assert not any(hasattr(module, name) for name in ("delete", "cleanup", "rmtree", "remove_build"))


def test_cli_is_readonly_and_invalid_paths_fail_closed(tmp_path):
    cli = Path(__file__).resolve().parents[2] / "scripts/scan-herdr-build-lifecycle.py"
    base = root(tmp_path)
    candidate(base)
    command = [
        sys.executable, "-I", "-B", str(cli), "--root", str(base),
        "--name", "herdr-hermes-build-case1",
    ]
    good = subprocess.run(command, capture_output=True, text=True, timeout=12)
    assert good.returncode == 0, good.stderr
    j = json.loads(good.stdout)
    assert j["cleanup_authorized"] is False
    assert j["deletion_performed"] is False
    bad = subprocess.run(command[:-1] + ["../other"], capture_output=True, text=True, timeout=12)
    assert bad.returncode == 2
    assert json.loads(bad.stdout)["cleanup_authorized"] is False
