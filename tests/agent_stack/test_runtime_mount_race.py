"""Prove stale SDK mount plans are rejected before native Hermes receives input."""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "agent-stack" / "bin" / "agent_durable_sandbox.py"


def sandbox_module():
    loader = importlib.machinery.SourceFileLoader("sandbox_runtime_race_test", str(PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    # Dataclasses in sandbox require the module to be registered.
    import sys
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def paths_fixture(tmp_path, monkeypatch):
    sandbox = sandbox_module()
    monkeypatch.setattr(sandbox, "HOME", tmp_path)
    roots = [tmp_path / ".hermes", tmp_path / ".hermes" / "profiles" / "quantlab"]
    for root in roots:
        root.mkdir(parents=True, exist_ok=True)
        for name in ("sessions", "cache", "logs"):
            (root / name).mkdir()
    (tmp_path / ".cache").mkdir()
    actual = sandbox._ephemeral_sdk_runtime_dirs(tmp_path)
    mounts = {str(p): {"rw"} for p in actual}
    fs = {str(p): "tmpfs" for p in actual}
    return sandbox, actual, mounts, fs


def test_post_mount_attestation_checks_tmpfs_and_rw(tmp_path, monkeypatch):
    sandbox, paths, mounts, fs = paths_fixture(tmp_path, monkeypatch)
    assert sandbox._sdk_runtime_masks_verified(Path("/"), mounts, fs)
    target = str(paths[-1])
    assert target in mounts
    mounts[target] = {"ro"}
    assert not sandbox._sdk_runtime_masks_verified(Path("/"), mounts, fs)
    mounts[target] = {"rw"}
    fs[target] = "ext4"
    assert not sandbox._sdk_runtime_masks_verified(Path("/"), mounts, fs)


def test_new_directory_not_present_in_mount_plan_is_denied(tmp_path, monkeypatch):
    sandbox, paths, modes, fs = paths_fixture(tmp_path, monkeypatch)
    missing = tmp_path / ".hermes" / "profiles" / "new-profile"
    missing.mkdir()
    (missing / "logs").mkdir()
    assert not sandbox._sdk_runtime_masks_verified(Path("/"), modes, fs)


@pytest.mark.parametrize("rel", [
    ".cache",
    ".hermes/profiles/quantlab/logs",
    ".hermes/profiles/quantlab/sessions",
    ".hermes/profiles/quantlab/cache",
    ".hermes/profiles/quantlab",
])
def test_post_mount_rejects_swapped_symlink(tmp_path, monkeypatch, rel):
    sandbox, paths, modes, fs = paths_fixture(tmp_path, monkeypatch)
    target = tmp_path / rel
    backup = tmp_path / "saved-original"
    target.rename(backup)
    destination = tmp_path / "workspace"
    destination.mkdir()
    target.symlink_to(destination, target_is_directory=True)
    assert not sandbox._sdk_runtime_masks_verified(Path("/"), modes, fs)


@pytest.mark.parametrize("attack", ["swapped_alias", "appeared_after_planning"])
def test_policy_fd_launcher_rechecks_runtime_at_exec(tmp_path, attack):
    sandbox = sandbox_module()
    home = tmp_path
    profile = home / ".hermes" / "profiles" / "quantlab"
    profile.mkdir(parents=True)
    sessions = profile / "sessions"
    sessions.mkdir()
    planned = [str(sessions)]
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    if attack == "swapped_alias":
        sessions.rename(tmp_path / "old-session")
        sessions.symlink_to(workspace, target_is_directory=True)
        expected = b"policy_fd_runtime_directory_alias"
    else:
        # A second directory appeared after command assembly. It was not
        # included in --tmpfs argv, and must not silently become writable.
        (profile / "logs").mkdir()
        expected = b"policy_fd_runtime_mount_mismatch"
    folder = tmp_path / "source"
    folder.mkdir()
    fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        item = {"source": f"/proc/{os.getpid()}/fd/{fd}", "fd": fd,
                "device": st.st_dev, "inode": st.st_ino,
                "kind": "directory", "target": "/tmp/herdr-policy-race-fixture"}
        code = sandbox._POLICY_FD_LAUNCHER.replace(
            'home = Path("/home/agentops")', "home = Path(" + repr(str(home)) + ")"
        )
        assert code != sandbox._POLICY_FD_LAUNCHER
        arguments = ["/usr/bin/bwrap", "--ro-bind-fd", str(fd), item["target"],
                     "--tmpfs", *planned, "--", "/bin/true"]
        result = subprocess.run(
            ["/usr/bin/python3", "-I", "-S", "-c", code,
             json.dumps([item]), *arguments],
            capture_output=True, timeout=5,
        )
        assert result.returncode != 0
        assert expected in result.stderr
    finally:
        os.close(fd)
