"""Exercise only disposable user-owned copy fixtures; never publish as root."""
import hashlib
import errno
import os
import stat
from dataclasses import replace
from pathlib import Path
import pytest
from herdr.policy_launch import ApprovedTree, CODE_TARGET
from herdr.runtime_publication import copy_reviewed_payload, _rename_without_replacement, publish_reviewed_runtime
from herdr.security import SecurityError


def fixture(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "program").write_bytes(b"reviewed-bytes")
    storage = tmp_path / "storage"
    storage.mkdir()
    tree = ApprovedTree(source, CODE_TARGET,
                        {"program": hashlib.sha256(b"reviewed-bytes").hexdigest()}, ("program",))
    return tree, storage


def test_worker_uid_cannot_publish_or_read_an_approval_as_a_publish_attempt(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("privileged publisher is never invoked by this test suite")
    with pytest.raises(SecurityError, match="privileged release operator"):
        publish_reviewed_runtime(tmp_path / "does-not-exist.json", publish=True)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("fault", [None, "hermes-shim", "herdr-cli", "python-bit", "python-missing"])
def test_publication_requires_every_directly_executed_entrypoint(tmp_path, monkeypatch, fault):
    from herdr import host_configuration, runtime_publication
    from herdr.host_bootstrap import SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE, PYTHON_TARGET, PYTHON_EXECUTABLE
    from herdr.policy_launch import RUNTIME_TARGETS
    def raw_tree(name, target, files, executable):
        return {"source": "/approved/" + name, "target": str(target),
                "files": {path: "a" * 64 for path in files}, "executable_files": executable,
                "max_bytes": 33554432, "max_file_bytes": 4194304}
    cli = "agent-stack/policy-bin/herdr"
    raw = {"schema_version": "herdr-runtime-publication-1", "version": "fixture",
           "destination": str(tmp_path), "trees": {
               "code": raw_tree("code", CODE_TARGET, [SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE, cli], [SHIM_SOURCE, cli]),
               "hermes": raw_tree("hermes", next(t for t in RUNTIME_TARGETS if t != PYTHON_TARGET), ["module.py"], []),
               "python": raw_tree("python", PYTHON_TARGET, [PYTHON_EXECUTABLE], [PYTHON_EXECUTABLE]),
           }}
    if fault == "hermes-shim":
        raw["trees"]["code"]["executable_files"].remove(SHIM_SOURCE)
    elif fault == "herdr-cli":
        raw["trees"]["code"]["executable_files"].remove(cli)
    elif fault == "python-bit":
        raw["trees"]["python"]["executable_files"].clear()
    elif fault == "python-missing":
        raw["trees"]["python"]["files"].clear()
    # Pure schema fixture only. No test claims a real root record or runs the
    # privileged publisher; actual source/destination checks remain mandatory.
    monkeypatch.setattr(host_configuration, "_read_configuration", lambda path: raw)
    monkeypatch.setattr(runtime_publication, "_verify_root_owned_ancestry", lambda path: None)
    if fault:
        with pytest.raises(SecurityError, match="executable entrypoint approval"):
            publish_reviewed_runtime(Path("/etc/herdr/runtime-publication.json"))
    else:
        assert publish_reviewed_runtime(Path("/etc/herdr/runtime-publication.json"))["published"] is False
    assert list(tmp_path.iterdir()) == []


def test_publication_copy_creates_new_inodes_even_with_old_writable_fd(tmp_path):
    tree, storage = fixture(tmp_path)
    old_fd = os.open(tree.source / "program", os.O_RDWR)
    copied = copy_reviewed_payload(tree, storage)
    try:
        assert (copied.path / "program").stat().st_ino != (tree.source / "program").stat().st_ino
        os.pwrite(old_fd, b"ATTACK", 0)
        assert (copied.path / "program").read_bytes() == b"reviewed-bytes"
        assert stat.S_IMODE(copied.path.stat().st_mode) == 0o555
        assert stat.S_IMODE((copied.path / "program").stat().st_mode) == 0o555
        copied.verify()
    finally:
        os.close(old_fd)
        copied.cleanup_after_pane_closed()


def test_nonexecutable_runtime_payload_is_readable_without_write_authority(tmp_path):
    tree, storage = fixture(tmp_path)
    copied = copy_reviewed_payload(replace(tree, executable_files=()), storage)
    try:
        assert stat.S_IMODE((copied.path / "program").stat().st_mode) == 0o444
        assert stat.S_IMODE(copied.path.stat().st_mode) == 0o555
    finally:
        copied.cleanup_after_pane_closed()


@pytest.mark.parametrize("attack", ["symlink", "hardlink", "digest"])
def test_publication_denies_unreviewed_payload(tmp_path, attack):
    tree, storage = fixture(tmp_path)
    if attack == "symlink":
        (tree.source / "program").rename(tree.source / "original")
        (tree.source / "program").symlink_to("original")
    elif attack == "hardlink":
        os.link(tree.source / "program", tree.source / "alias")
    else:
        (tree.source / "program").write_bytes(b"changed")
    with pytest.raises((SecurityError, OSError)):
        copy_reviewed_payload(tree, storage)


def test_atomic_publication_never_replaces_an_existing_version(tmp_path):
    (tmp_path / "pending").mkdir()
    (tmp_path / "existing").mkdir()
    (tmp_path / "existing" / "keep").write_bytes(b"keep")
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(OSError):
            _rename_without_replacement(fd, "pending", "existing")
        assert (tmp_path / "existing" / "keep").read_bytes() == b"keep"
        _rename_without_replacement(fd, "pending", "new-version")
        assert (tmp_path / "new-version").is_dir()
    finally:
        os.close(fd)


def test_disk_full_during_copy_preserves_source_and_existing_release(tmp_path, monkeypatch):
    tree, storage = fixture(tmp_path)
    existing = storage / "existing"
    existing.mkdir()
    (existing / "keep").write_bytes(b"keep")
    original = Path.open
    def fail_new_payload(path, mode="r", *args, **kwargs):
        if mode == "xb" and path.name == "program":
            raise OSError(errno.ENOSPC, "fixture disk full")
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", fail_new_payload)
    with pytest.raises(OSError) as failure:
        copy_reviewed_payload(tree, storage)
    assert failure.value.errno == errno.ENOSPC
    assert (tree.source / "program").read_bytes() == b"reviewed-bytes"
    assert (existing / "keep").read_bytes() == b"keep"
    assert list(storage.iterdir()) == [existing]
