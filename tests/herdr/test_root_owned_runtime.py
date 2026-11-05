"""#129: same-UID cannot mutate operator-published root-owned runtime code.

This test never runs Hermes or a provider. The staging-only kernel proof uses
a nonsecret RC26 provenance file as a representative immutable code input.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time

import pytest

from herdr.policy_launch import (
    ApprovedImmutableTree, CODE_TARGET, FrozenTree, RUNTIME_TARGETS,
)
from herdr.security import SecurityError

PUBLISHED = Path(
    "/opt/herdr/releases/v0.3.0-rc.26-4d09b58b4416/provenance"
)
FILENAME = "external-runtime-dependency.txt"


def approved_nonsecret_release_tree():
    if os.geteuid() == 0:
        pytest.skip("same-UID adversary proof must never write released files as root")
    if not PUBLISHED.is_dir() or not (PUBLISHED / FILENAME).is_file():
        pytest.skip("staging RC26 root-published nonsecret fixture is absent")
    assert [p.name for p in PUBLISHED.iterdir()] == [FILENAME]
    raw = (PUBLISHED / FILENAME).read_bytes()
    return ApprovedImmutableTree(
        PUBLISHED, CODE_TARGET,
        {FILENAME: hashlib.sha256(raw).hexdigest()},
    ), raw


def test_same_uid_mutable_tree_cannot_claim_immutable_runtime(tmp_path):
    own = tmp_path / "mutable"
    own.mkdir()
    (own / "code.py").write_bytes(b"approved")
    manifest = {"code.py": hashlib.sha256(b"approved").hexdigest()}
    approved = ApprovedImmutableTree(own, CODE_TARGET, manifest)
    with pytest.raises(SecurityError, match="root protected"):
        approved.freeze(tmp_path / "storage", writable_roots=())


def test_symlinked_root_ancestry_never_counts_as_operator_immutable(tmp_path):
    definition, _ = approved_nonsecret_release_tree()
    alias = tmp_path / "root-owned-alias"
    alias.symlink_to(definition.source, target_is_directory=True)
    with pytest.raises(SecurityError, match="root protected"):
        FrozenTree.attach_immutable(
            alias, target=CODE_TARGET, files=definition.files,
        )


def test_root_published_release_remains_unmodified_after_owned_pane_cleanup():
    approved, raw = approved_nonsecret_release_tree()
    tree = approved.freeze(PUBLISHED, writable_roots=())
    assert tree.immutable_host_source
    try:
        tree.verify()
        assert tree.path == approved.source
        assert (tree.path / FILENAME).read_bytes() == raw
        with pytest.raises(PermissionError):
            (tree.path / FILENAME).write_bytes(b"tamper")
        with pytest.raises(PermissionError):
            (tree.path / FILENAME).chmod(0o666)
        with pytest.raises(PermissionError):
            (tree.path / FILENAME).rename(tree.path / "replaced")
    finally:
        tree.cleanup_after_pane_closed()
    assert tree.fd == -1
    assert (approved.source / FILENAME).read_bytes() == raw


def test_root_owned_sdk_tree_stays_unmodified_in_actual_bwrap_child():
    approved, raw = approved_nonsecret_release_tree()
    if not shutil.which("bwrap"):
        pytest.skip("bwrap not installed")
    tree = approved.freeze(PUBLISHED, writable_roots=())
    proc = None
    try:
        command = [
            "/usr/bin/bwrap", "--ro-bind", "/", "/",
            "--unshare-pid", "--dev", "/dev", "--proc", "/proc",
            "--tmpfs", "/tmp", "--dir", "/tmp/operator-code",
            "--ro-bind-fd", str(tree.fd), "/tmp/operator-code",
            "--", "/bin/sleep", "5",
        ]
        proc = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, pass_fds=(tree.fd,),
        )
        time.sleep(.35)
        if proc.poll() is not None:
            detail = (proc.stderr.read() or b"")[:400].decode(errors="replace")
            if "Operation not permitted" in detail:
                pytest.skip("sandbox user namespace disabled by CI")
            pytest.fail("root-owned code mount failed: " + detail)
        descendants = Path(
            f"/proc/{proc.pid}/task/{proc.pid}/children"
        ).read_text().split()
        assert len(descendants) == 1
        child = int(descendants[0])
        assert os.readlink(f"/proc/{child}/ns/mnt") != os.readlink(
            "/proc/self/ns/mnt"
        )
        inside = Path(f"/proc/{child}/root/tmp/operator-code") / FILENAME
        assert inside.read_bytes() == raw
        mounted = inside.parent.stat()
        assert (mounted.st_dev, mounted.st_ino) == (tree.device, tree.inode)
        mountinfo = Path(f"/proc/{child}/mountinfo").read_text()
        assert any(
            " /tmp/operator-code " in row
            and "ro" in row.split(" - ", 1)[0].split()[5].split(",")
            for row in mountinfo.splitlines()
        )
        # A process with exactly the host worker UID cannot chmod or alter
        # release bytes even while its namespace holds a readonly bind.
        with pytest.raises(PermissionError):
            (PUBLISHED / FILENAME).chmod(0o666)
        with pytest.raises(PermissionError):
            (PUBLISHED / FILENAME).write_bytes(b"attacker")
        with pytest.raises(PermissionError):
            (PUBLISHED / "no-bytecode-cache").mkdir()
        with pytest.raises(OSError):
            (inside.parent / "no-bytecode-cache").mkdir()
        assert not (PUBLISHED / "no-bytecode-cache").exists()
        assert not (inside.parent / "no-bytecode-cache").exists()
        assert inside.read_bytes() == raw
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        tree.cleanup_after_pane_closed()


def test_mutable_copy_remains_untrusted_even_after_digest_verification(tmp_path):
    from tests.herdr.test_policy_launch import mount, cleanup
    bundle = mount(tmp_path)
    try:
        assert not bundle.code.immutable_host_source
        assert not all(tree.immutable_host_source for tree in bundle.runtime)
        with pytest.raises(SecurityError, match="private profile requires root-protected"):
            bundle.require_immutable_runtime()
    finally:
        cleanup(bundle)


def test_operator_protected_runtime_requires_all_three_trees(tmp_path):
    from herdr.policy_launch import PolicyMount
    from herdr.security import stage_policy_bundle
    approved, _ = approved_nonsecret_release_tree()
    stage = stage_policy_bundle(tmp_path / "grant.bundle.json")
    code = None
    runtime = []
    try:
        code = approved.freeze(PUBLISHED, writable_roots=())
        for target in sorted(RUNTIME_TARGETS):
            runtime.append(
                FrozenTree.attach_immutable(
                    PUBLISHED, target=target, files=approved.files,
                )
            )
        mounted = PolicyMount(stage, code, tuple(runtime))
        mounted.require_immutable_runtime()
        entries = mounted.descriptors()
        assert len(entries) == 4
        assert all(e["source"].startswith("/proc/") for e in entries)
        assert all(e["kind"] == "directory" for e in entries[1:])
        # Every descriptor remains an actual root-owned protected inode.
        for tree in (mounted.code, *mounted.runtime):
            tree.verify()
            assert tree.immutable_host_source
    finally:
        for tree in ([code] if code is not None else []) + runtime:
            tree.cleanup_after_pane_closed()
        stage.close()
        stage.path.unlink(missing_ok=True)
