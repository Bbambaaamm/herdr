"""Host-only sealed profile issuance and backwards-compatible sandbox handoff.

No task/prompt can approve its own profile manifest, and no test calls models.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

import pytest

from herdr.policy_launch import ApprovedProfile, HostPolicyLaunchFactory
from herdr.private_profile_namespace import PrivateProfileError, PrivateProfileSnapshot
from herdr.security import SecurityError
from tests.herdr.test_policy_launch import mount, cleanup, factory_for
from tests.herdr.test_security import grant

ROOT = Path(__file__).resolve().parents[2]
SANDBOX_SOURCE = ROOT / "agent-stack/bin/agent_durable_sandbox.py"


def sandbox_module():
    spec = importlib.util.spec_from_file_location("sandbox_host_profile_handoff_tests", SANDBOX_SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def approved_profile(tmp_path, *, name="quantlab"):
    path = tmp_path / "profiles" / name
    path.mkdir(parents=True)
    values = {
        "config.yaml": b"provider: fictitious-zero-network\n",
        ".env": b"FIXTURE_TOKEN=not-a-real-credential\n",
        "auth.json": b'{"dummy":"fixture"}\n',
    }
    for relative, raw in values.items():
        (path / relative).write_bytes(raw)
    hashes = {rel: hashlib.sha256(raw).hexdigest() for rel, raw in values.items()}
    return ApprovedProfile(name, path, hashes), values


def test_host_profile_approval_is_typed_and_manifest_immutable(tmp_path):
    approved, values = approved_profile(tmp_path)
    original = dict(approved.files)
    assert original.keys() == values.keys()
    with pytest.raises(TypeError):
        approved.files["config.yaml"] = "f" * 64
    with pytest.raises(SecurityError, match="approved profile manifest"):
        ApprovedProfile("quantlab", approved.source, {"config.yaml": original["config.yaml"]})
    with pytest.raises(SecurityError, match="approved profile name"):
        ApprovedProfile("../quantlab", approved.source, original)
    with pytest.raises(SecurityError, match="approved profile digest"):
        ApprovedProfile("quantlab", approved.source, {**original, "config.yaml": "not-a-sha"})


def test_host_factory_freezes_only_after_exact_grant_and_closes_after_pane(tmp_path, monkeypatch):
    item = mount(tmp_path)
    workspace = tmp_path / "admitted-workspace"
    workspace.mkdir()
    planned = grant(workspace)
    factory = factory_for(tmp_path, item, lambda **kw: planned)
    approved, values = approved_profile(tmp_path)
    factory.approved_profile = approved  # Host-only injection, never task JSON.
    # The minimal test fixture has no bootstrap shim modules. Stub only
    # bootstrap socket creation, not grant admission/profile snapshot logic.
    from herdr.host_bootstrap import HostBootstrap
    class FakeBootstrap:
        def cleanup_after_pane_closed(self): pass
    monkeypatch.setattr(HostBootstrap, "create",
                        classmethod(lambda cls, *args, **kwargs: FakeBootstrap()))
    try:
        prepared = factory.prepare(identity=planned.identity, workspace=workspace,
                                   tools=planned.scope.tools,
                                   permissions=planned.scope.permissions)
        snapshot = prepared.private_profile_snapshot
        assert isinstance(snapshot, PrivateProfileSnapshot)
        assert snapshot.name == approved.name
        assert len(snapshot.files) == len(values)
        for file in snapshot.files:
            file.verify()
            assert os.pread(file.fd, file.size, 0) == values[file.relative]
            with pytest.raises(OSError):
                os.pwrite(file.fd, b"attack", 0)
        (approved.source / "config.yaml").write_bytes(b"ATTACK-CHANGED-HOST\n")
        assert next(file for file in snapshot.files if file.relative == "config.yaml").sha256 == approved.files["config.yaml"]
        prepared.cleanup_after_pane_closed()
        with pytest.raises(PrivateProfileError, match="profile_seal_closed"):
            snapshot.verify()
    finally:
        cleanup(item)


def test_factory_rejects_bad_host_manifest_without_creating_usable_launch(tmp_path):
    item = mount(tmp_path)
    workspace = tmp_path / "worker"
    workspace.mkdir()
    planned = grant(workspace)
    factory = factory_for(tmp_path, item, lambda **kw: planned)
    approved, _ = approved_profile(tmp_path)
    factory.approved_profile = ApprovedProfile(
        approved.name, approved.source, {**approved.files, "config.yaml": "0" * 64}
    )
    try:
        with pytest.raises(PrivateProfileError, match="profile_source_digest_mismatch"):
            factory.prepare(identity=planned.identity, workspace=workspace,
                            tools=planned.scope.tools,
                            permissions=planned.scope.permissions)
        leftovers = [p for p in (tmp_path / "store").iterdir()
                     if p.name not in {".ownership.lock"} and p.name.startswith("herdr-ownership")]
        assert not leftovers
    finally:
        cleanup(item)


def test_wrong_or_missing_grant_does_not_read_profile_files(tmp_path, monkeypatch):
    item = mount(tmp_path)
    workspace = tmp_path / "worker"
    workspace.mkdir()
    planned = grant(workspace)
    factory = factory_for(tmp_path, item, lambda **kw: None)
    approved, _ = approved_profile(tmp_path)
    factory.approved_profile = approved
    called = []
    monkeypatch.setattr(ApprovedProfile, "freeze",
                        lambda self: called.append(True))
    try:
        with pytest.raises(SecurityError):
            factory.prepare(identity=planned.identity, workspace=workspace,
                            tools=planned.scope.tools,
                            permissions=planned.scope.permissions)
        assert not called
    finally:
        cleanup(item)


def test_opt_in_sandbox_rejects_profile_selection_or_authority_mismatch(tmp_path, monkeypatch):
    sandbox = sandbox_module()
    approved, _ = approved_profile(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hermes = tmp_path / "herdr"
    hermes.write_text("#!/bin/sh\n")
    hermes.chmod(0o755)
    policy = tmp_path / "policy"
    policy.write_text("#!/bin/sh\n")
    policy.chmod(0o755)
    config = tmp_path / "config"
    config.mkdir()
    monkeypatch.setattr(sandbox, "HERDR_CONFIG", config)
    class StubMount:
        def descriptors(self): return []
    with approved.freeze() as snapshot:
        with pytest.raises(RuntimeError, match="durable_private_profile_authority_required"):
            sandbox.command(workspace, hermes, policy=policy,
                            private_profile_snapshot=snapshot, hermes_profile="quantlab")
        with pytest.raises(RuntimeError, match="durable_private_profile_authority_required"):
            sandbox.command(workspace, hermes, policy=policy, policy_mount=StubMount(),
                            private_profile_snapshot=snapshot, hermes_profile="majak")
        command = sandbox.command(workspace, hermes, policy=policy, policy_mount=StubMount(),
                                  private_profile_snapshot=snapshot, hermes_profile="quantlab")
        assert command[0:4] == ["/usr/bin/python3", "-I", "-S", "-c"]
        assert "--remount-ro" in command
        assert command[-3:] == ["--noprofile", "--norc", "-i"]
        assert "FIXTURE_TOKEN=not-a-real-credential" not in str(command)


def test_private_snapshot_mount_attestation_only_accepts_its_exact_ro_view(tmp_path):
    sandbox = sandbox_module()
    approved, values = approved_profile(tmp_path)
    with approved.freeze() as snapshot:
        # Use a disposable root fixture: mountinfo is separately supplied
        # by a physical child-namespace test below, never fake a PASS claim.
        home = Path("/home/agentops")
        modes = {str(home): {"ro"}}
        filesystems = {str(home): "tmpfs"}
        assert not sandbox._private_profile_namespace_verified(
            tmp_path, modes, filesystems, snapshot)


def test_real_host_selected_private_profile_mounts_and_attestation(tmp_path, monkeypatch):
    """Actual bwrap CHILD with host-selected manifest, no native SDK/model."""
    import shutil
    if shutil.which("bwrap") is None or not Path("/home/agentops").is_dir():
        pytest.skip("fixed staging HOME/bwrap unavailable")
    sandbox = sandbox_module()
    approved, values = approved_profile(tmp_path)
    workspace = tmp_path / "task-workspace"
    workspace.mkdir()
    hermes = tmp_path / "fake-herdr"
    hermes.write_bytes(b"#!/bin/sh\nexit 0\n")
    hermes.chmod(0o755)
    policy = tmp_path / "fake-cli-policy"
    policy.write_bytes(b"#!/bin/sh\nexit 3\n")
    policy.chmod(0o555)
    config = tmp_path / "fake-config-control"
    config.mkdir()
    monkeypatch.setattr(sandbox, "HERDR_CONFIG", config)

    class StubMount:
        def descriptors(self): return []

    with approved.freeze() as snapshot:
        args = sandbox.command(
            workspace, hermes, policy=policy,
            policy_mount=StubMount(), private_profile_snapshot=snapshot,
            hermes_profile=approved.name,
        )
        assert "FIXTURE_TOKEN" not in str(args)
        delimiter = args.index("--")
        args[delimiter + 1:] = ["/bin/sleep", "4"]
        proc = subprocess.Popen(args, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            time.sleep(0.4)
            if proc.poll() is not None:
                error = (proc.stderr.read() or b"")[:800].decode(errors="replace")
                if "Operation not permitted" in error:
                    pytest.skip("CI runner does not permit unprivileged bubblewrap")
                pytest.fail("host-approved private HOME sandbox failed: " + error)
            children = Path(f"/proc/{proc.pid}/task/{proc.pid}/children").read_text().split()
            assert len(children) == 1
            child = int(children[0])
            namespace_root = Path(f"/proc/{child}/root")
            mount_lines = Path(f"/proc/{child}/mountinfo").read_text().splitlines()
            modes = {}
            filesystems = {}
            for line in mount_lines:
                before, after = line.split(" - ", 1)
                parts = before.split()
                modes[parts[4]] = set(parts[5].split(","))
                filesystems[parts[4]] = after.split()[0]
            assert sandbox._private_profile_namespace_verified(
                namespace_root, modes, filesystems, snapshot,
            )
            for entry in snapshot.files:
                name = namespace_root / str(snapshot.destination / entry.relative).lstrip("/")
                assert name.read_bytes() == values[entry.relative]
            # Host-side same-UID rename cannot redirect the sealed profile.
            approved.source.rename(tmp_path / "profile-original")
            attacker = tmp_path / "attacker"
            attacker.mkdir()
            (attacker / "config.yaml").write_bytes(b"changed")
            approved.source.symlink_to(attacker, target_is_directory=True)
            assert sandbox._private_profile_namespace_verified(
                namespace_root, modes, filesystems, snapshot,
            )
            private_log = namespace_root / str(snapshot.destination / "logs/proof.txt").lstrip("/")
            private_log.write_bytes(b"runtime-only")
            assert private_log.read_bytes() == b"runtime-only"
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
