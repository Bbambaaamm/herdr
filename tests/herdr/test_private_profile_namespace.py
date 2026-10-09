"""Lifetime profile isolation: sealed, bounded inputs in a private HOME."""
from __future__ import annotations

import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time

import pytest
from herdr.private_profile_namespace import (
    PrivateProfileError, PrivateProfileSnapshot,
)

HOME = Path("/home/agentops")


def fixture_profile(tmp_path):
    root = tmp_path / "approved-profile"
    root.mkdir()
    content = {
        "config.yaml": b"model: fixture-free-only\n",
        ".env": b"DUMMY_TOKEN_FOR_TESTS=not-a-secret\n",
        "auth.json": b'{"fake_credential":"fixture"}\n',
        "prefill.json": b'["approved fixture"]\n',
    }
    for name, raw in content.items():
        (root / name).write_bytes(raw)
    return root, content, {key: hashlib.sha256(value).hexdigest()
                           for key, value in content.items()}


def test_freezes_approved_inputs_and_cannot_mutate_sealed_memfd(tmp_path):
    source, values, approved = fixture_profile(tmp_path)
    with PrivateProfileSnapshot.from_approved(
        source, name="quantlab", approved_sha256=approved,
    ) as profile:
        profile.verify()
        assert profile.destination == HOME / ".hermes/profiles/quantlab"
        assert len(profile.files) == 4
        before = {record.relative: os.pread(record.fd, record.size, 0)
                  for record in profile.files}
        assert before == values
        with pytest.raises(OSError):
            os.pwrite(profile.files[0].fd, b"hostile", 0)
        (source / "config.yaml").write_bytes(b"CHANGED AFTER SNAPSHOT")
        assert {record.relative: os.pread(record.fd, record.size, 0)
                for record in profile.files} == values
        mount = profile.mount_arguments()
        assert mount[:2] == ["--tmpfs", str(HOME)]
        assert "--ro-bind-data" in mount
        assert not any(str(source) in value for value in mount)
    with pytest.raises(PrivateProfileError, match="profile_seal_closed"):
        profile.verify()


def test_refuse_missing_or_untrusted_digests(tmp_path):
    source, values, approved = fixture_profile(tmp_path)
    with pytest.raises(PrivateProfileError, match="profile_manifest_invalid"):
        PrivateProfileSnapshot.from_approved(
            source, name="quantlab", approved_sha256={"config.yaml": approved["config.yaml"]})
    wrong = dict(approved)
    wrong["config.yaml"] = "0" * 64
    with pytest.raises(PrivateProfileError, match="profile_source_digest_mismatch"):
        PrivateProfileSnapshot.from_approved(source, name="quantlab", approved_sha256=wrong)
    with pytest.raises(PrivateProfileError, match="profile_name_invalid"):
        PrivateProfileSnapshot.from_approved(source, name="../quantlab",
                                             approved_sha256=approved)
    with pytest.raises(PrivateProfileError, match="profile_home_policy_invalid"):
        PrivateProfileSnapshot.from_approved(source, name="quantlab",
                                             approved_sha256=approved,home=tmp_path)


@pytest.mark.parametrize("malicious", [
    "../config.yaml", "logs/agent.log", "sessions/state.db",
    "state.db", "/etc/passwd", "subdir//config.yaml",
])
def test_untrusted_profile_source_paths_denied(tmp_path, malicious):
    source, values, approved = fixture_profile(tmp_path)
    probe = dict(approved)
    probe[malicious] = "f" * 64
    with pytest.raises(PrivateProfileError):
        PrivateProfileSnapshot.from_approved(
            source, name="quantlab", approved_sha256=probe)


@pytest.mark.parametrize("swap", ["file_alias", "profile_alias"])
def test_symlinked_approved_sources_are_denied(tmp_path, swap):
    source, values, approved = fixture_profile(tmp_path)
    original = source
    if swap == "profile_alias":
        outside = tmp_path / "outside"
        source.rename(outside)
        source.symlink_to(outside, target_is_directory=True)
    else:
        target = source / "config.yaml"
        target.rename(source / "saved.yaml")
        target.symlink_to(source / "saved.yaml")
    with pytest.raises(OSError):
        PrivateProfileSnapshot.from_approved(
            source, name="quantlab", approved_sha256=approved)


def test_oversized_source_and_mutable_input_are_denied(tmp_path):
    source, values, approved = fixture_profile(tmp_path)
    huge = b"x" * 131_073
    (source / "config.yaml").write_bytes(huge)
    approved["config.yaml"] = hashlib.sha256(huge).hexdigest()
    with pytest.raises(PrivateProfileError, match="profile_source_size_invalid"):
        PrivateProfileSnapshot.from_approved(source, name="quantlab", approved_sha256=approved)


def test_mount_plan_requires_root_owned_home_anchor(tmp_path, monkeypatch):
    source, values, approved = fixture_profile(tmp_path)
    with PrivateProfileSnapshot.from_approved(
        source, name="quantlab", approved_sha256=approved,
    ) as frozen:
        true_lstat = os.lstat
        def fake_lstat(path):
            info = true_lstat(path)
            if Path(path) == HOME.parent:
                from types import SimpleNamespace
                return SimpleNamespace(st_mode=info.st_mode, st_uid=os.getuid()+3)
            return info
        monkeypatch.setattr(os, "lstat", fake_lstat)
        with pytest.raises(PrivateProfileError, match="profile_home_anchor_untrusted"):
            frozen.mount_arguments()


def test_same_uid_host_cannot_replace_profile_view_through_private_home(tmp_path):
    """Actual bwrap CHILD mount namespace; not the unisolated bwrap supervisor."""
    if shutil.which("bwrap") is None or not hasattr(os, "memfd_create"):
        pytest.skip("Linux bwrap with memfd is unavailable")
    source, values, approved = fixture_profile(tmp_path)
    with PrivateProfileSnapshot.from_approved(
        source, name="quantlab", approved_sha256=approved,
    ) as frozen:
        mounts = frozen.mount_arguments()
        # The private HOME must also permit explicit, bounded code/workspace
        # mounts after masking; it must not inherit their host parents.
        signed_sdk = tmp_path / "signed-sdk-fixture"
        signed_sdk.mkdir()
        (signed_sdk / "reviewed.py").write_bytes(b"reviewed code fixture\\n")
        owned_worktree = tmp_path / "owned-worktree-fixture"
        owned_worktree.mkdir()
        (owned_worktree / "task.txt").write_bytes(b"workspace fixture\\n")
        # Never use a real model/provider. The sandbox only runs sleep.
        args = ["/usr/bin/bwrap", "--ro-bind", "/", "/", "--dev", "/dev",
                "--proc", "/proc", "--unshare-pid", *mounts,
                "--ro-bind", str(signed_sdk), str(HOME / ".hermes/hermes-agent"),
                "--ro-bind", str(owned_worktree), str(HOME / "workspaces/owned"),
                "--", "/bin/sleep", "4"]
        with subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.PIPE,
                              pass_fds=tuple(item.fd for item in frozen.files)) as proc:
            time.sleep(0.25)
            if proc.poll() is not None:
                error = (proc.stderr.read() or b"")[:400].decode(errors="replace")
                if "Operation not permitted" in error or "Creating new namespace failed" in error:
                    pytest.skip("CI runner does not permit unprivileged bubblewrap")
                pytest.fail("private home bwrap launch failed: " + error)
            children = Path(f"/proc/{proc.pid}/task/{proc.pid}/children").read_text().split()
            assert len(children) == 1
            child = int(children[0])
            assert os.readlink(f"/proc/{child}/ns/mnt") != os.readlink("/proc/self/ns/mnt")
            mountinfo = Path(f"/proc/{child}/mountinfo").read_text()
            assert any(" /home/agentops " in row and " - tmpfs " in row
                       for row in mountinfo.splitlines())
            childroot = Path(f"/proc/{child}/root")
            assert (childroot / str(HOME / ".hermes/hermes-agent/reviewed.py").lstrip("/")).read_bytes() == b"reviewed code fixture\\n"
            assert (childroot / str(HOME / "workspaces/owned/task.txt").lstrip("/")).read_bytes() == b"workspace fixture\\n"
            assert not (childroot / str(HOME / ".hermes/profiles/majak").lstrip("/")).exists()
            for item in frozen.files:
                inside = Path(f"/proc/{child}/root") / str(
                    frozen.destination / item.relative
                ).lstrip("/")
                assert inside.read_bytes() == values[item.relative]
            # Replace all original source paths after sandbox and mounts exist.
            source.rename(tmp_path / "profile-old")
            hostile = tmp_path / "attacker"
            hostile.mkdir()
            for filename in values:
                (hostile / filename).write_bytes(b"attacker controlled")
            source.symlink_to(hostile, target_is_directory=True)
            for item in frozen.files:
                inside = Path(f"/proc/{child}/root") / str(
                    frozen.destination / item.relative
                ).lstrip("/")
                assert inside.read_bytes() == values[item.relative]
                assert inside.read_bytes() != b"attacker controlled"
            proc.terminate()
            proc.wait(timeout=2)
