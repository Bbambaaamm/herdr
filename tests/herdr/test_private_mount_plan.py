"""No provider, no host task store, no privileged publication."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from herdr.private_mount_plan import ApprovedPrivateMountPlan, PinnedLaunchPath, request_for, isolated_destination_anchor
from herdr.security import SecurityError, canonical_json_bytes
from tests.herdr.test_policy_launch import proof_scheduler


def test_exact_root_plan_binds_argv_descriptors_and_attempt(tmp_path, monkeypatch):
    from herdr.security import InvocationIdentity
    import herdr.host_configuration as configuration
    _, _, _, proof = proof_scheduler(tmp_path)
    identity = InvocationIdentity.from_dict(proof["identity"])
    argv = ["/usr/bin/bwrap", "--bind-fd", "7", "/tmp/work", "--", "/bin/true"]
    descriptors = [{"fd": 7, "device": 1, "inode": 3, "kind": "directory", "target": "/tmp/work", "source": "/proc/123/fd/7"}]
    request = request_for(identity, descriptors, argv)
    path = Path("/etc/herdr/launch-plans") / (hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest() + ".json")
    # Unit fixture substitutes only the already root-verified record reader.
    monkeypatch.setattr(configuration, "_read_configuration", lambda selected: request)
    real_lstat = Path.lstat
    fixture = tmp_path / "record"
    fixture.write_text("fixture")
    monkeypatch.setattr(Path, "lstat", lambda selected: real_lstat(fixture if selected == path else selected))
    approved = ApprovedPrivateMountPlan.read(path, identity)
    envelope = approved.authorize(descriptors, argv)
    assert envelope["entries"] == descriptors
    assert request["writable_targets"] == ["/tmp/work"]
    with pytest.raises(SecurityError, match="differs from root approval"):
        approved.authorize(descriptors, [*argv[:-1], "/bin/bash"])
    with pytest.raises(SecurityError, match="differs from root approval"):
        approved.authorize([{**descriptors[0], "inode": 4}], argv)
    with pytest.raises(SecurityError, match="outside host authority"):
        ApprovedPrivateMountPlan.read(tmp_path / path.name, identity)


def test_worker_cannot_issue_its_own_root_approval(tmp_path):
    from herdr.security import InvocationIdentity
    _, _, _, proof = proof_scheduler(tmp_path)
    identity = InvocationIdentity.from_dict(proof["identity"])
    with pytest.raises(SecurityError, match="outside host authority"):
        ApprovedPrivateMountPlan.read(tmp_path / "self-approved.json", identity)


@pytest.mark.parametrize("path", ["/home/agentops/.ssh/work", "/home/agentops/.aws/work", "/home/agentops/.hermes/work", "/proc/work", "/run/work", "/workspace"])
def test_sensitive_or_unanchored_destinations_are_never_workspaces(path):
    with pytest.raises(SecurityError):
        isolated_destination_anchor(Path(path))


def test_exact_result_pin_rejects_symlink_or_inode_substitution(tmp_path):
    path = tmp_path / "result.json"
    path.touch(mode=0o600)
    expected = path.stat()
    pin = PinnedLaunchPath(path, directory=False, expected=(expected.st_dev, expected.st_ino))
    try:
        path.rename(tmp_path / "original.json")
        path.symlink_to(tmp_path / "original.json")
        pin.verify()
        assert pin.inode == expected.st_ino
        with pytest.raises((SecurityError, OSError)):
            PinnedLaunchPath(path, directory=False, expected=(expected.st_dev, expected.st_ino))
    finally:
        pin.close()
    assert pin.fd == -1


def test_actual_kernel_workspace_pin_survives_host_source_and_destination_swap(tmp_path):
    if not Path("/usr/bin/bwrap").is_file():
        pytest.skip("bubblewrap absent")
    source = tmp_path / "tree" / "work"
    source.mkdir(parents=True)
    (source / "sentinel").write_bytes(b"approved")
    pin = PinnedLaunchPath(source, directory=True)
    argv = ["/usr/bin/bwrap", "--ro-bind", "/", "/", "--unshare-net", "--unshare-pid",
            "--proc", "/proc", "--tmpfs", "/tmp", "--dir", "/tmp/owned",
            "--bind-fd", str(pin.fd), "/tmp/owned", "--remount-ro", "/tmp",
            "--", "/bin/sleep", "5"]
    process = subprocess.Popen(argv, pass_fds=(pin.fd,), stderr=subprocess.PIPE)
    try:
        time.sleep(.25)
        if process.poll() is not None:
            failure = process.stderr.read(800).decode(errors="replace")
            if "Operation not permitted" in failure or "Creating new namespace failed" in failure:
                pytest.skip("unprivileged namespace unavailable")
            pytest.fail(failure)
        children = Path(f"/proc/{process.pid}/task/{process.pid}/children").read_text().split()
        assert len(children) == 1
        child = int(children[0])
        inside = Path(f"/proc/{child}/root/tmp/owned")
        assert os.readlink(f"/proc/{child}/ns/net") != os.readlink("/proc/self/ns/net")
        source.parent.rename(tmp_path / "renamed-tree")
        source.parent.symlink_to("/home/agentops/.hermes", target_is_directory=True)
        assert (inside / "sentinel").read_bytes() == b"approved"
        assert not (inside / "profiles").exists()
        with pytest.raises(OSError):
            inside.rename(inside.parent / "replaced")
        assert (inside / "sentinel").read_bytes() == b"approved"
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
        pin.close()


def test_actual_kernel_mount_alias_cannot_be_pinned_as_a_workspace(tmp_path):
    if not Path("/usr/bin/bwrap").is_file():
        pytest.skip("bubblewrap absent")
    repo = Path(__file__).resolve().parents[2]
    child_code = "\n".join([
        "import sys", "from pathlib import Path", f"sys.path.insert(0,{str(repo)!r})",
        "from herdr.private_mount_plan import PinnedLaunchPath",
        "try: PinnedLaunchPath(Path('/tmp/alias'), directory=True)",
        "except Exception as error:", " print(str(error)); sys.exit(0)",
        "sys.exit(3)",
    ])
    result = subprocess.run(["/usr/bin/bwrap", "--ro-bind", "/", "/", "--unshare-net", "--unshare-pid",
                             "--proc", "/proc", "--tmpfs", "/tmp", "--ro-bind", str(tmp_path), "/tmp/alias",
                             "--", sys.executable, "-I", "-c", child_code], capture_output=True, timeout=8)
    if b"Operation not permitted" in result.stderr or b"Creating new namespace failed" in result.stderr:
        pytest.skip("unprivileged namespace unavailable")
    assert result.returncode == 0
    assert b"mount alias below a mutable root" in result.stdout
