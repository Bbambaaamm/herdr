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
    factory.profile_preflight = lambda name: name == approved.name
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
    factory.profile_preflight = lambda name: name == approved.name
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
        # Path-based root workspace and result mounts are not yet safe
        # against same-UID rename/symlink races. No production launch may
        # opt into the private profile until these sources are FD-pinned.
        with pytest.raises(RuntimeError, match="durable_private_profile_sources_unpinned"):
            sandbox.command(workspace, hermes, policy=policy, policy_mount=StubMount(),
                            private_profile_snapshot=snapshot, hermes_profile="quantlab")
        fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(fd)
        pin = sandbox.PinnedWorktree(workspace, fd, info.st_dev, info.st_ino, workspace.parent)
        try:
            with pytest.raises(RuntimeError, match="durable_private_profile_sources_unpinned"):
                sandbox.command(workspace, hermes, policy=policy, policy_mount=StubMount(),
                                private_profile_snapshot=snapshot, hermes_profile="quantlab",
                                pinned_worktree=pin, writable=(policy,))
            # An arbitrary host mount or a merely digest-checked,
            # agentops-owned code copy does not grant private-profile launch.
            with pytest.raises(RuntimeError, match="durable_private_runtime_not_immutable"):
                sandbox.command(workspace, hermes, policy=policy,
                                policy_mount=StubMount(), pinned_worktree=pin,
                                private_profile_snapshot=snapshot,
                                hermes_profile="quantlab")
        finally:
            pin.close()


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
    # Private HOME only admits a pinned policy shim from a root-owned
    # release. This nonsecret RC26 text file is a mounting fixture ONLY:
    # the child runs /bin/sleep, never this fake shim or any native SDK.
    hermes = Path("/home/agentops/.local/bin/herdr")
    policy = Path(
        "/opt/herdr/releases/v0.3.0-rc.26-4d09b58b4416/"
        "provenance/external-runtime-dependency.txt"
    )
    if not (hermes.is_file() and policy.is_file()):
        pytest.skip("root-published inert shim fixture unavailable")
    config = tmp_path / "fake-config-control"
    config.mkdir()
    monkeypatch.setattr(sandbox, "HERDR_CONFIG", config)
    immutable_policy_mount, immutable_stage = _root_published_mount_for_physical_test(
        tmp_path
    )

    with approved.freeze() as snapshot:
        fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(fd)
        pin = sandbox.PinnedWorktree(workspace, fd, info.st_dev, info.st_ino, workspace.parent)
        args = sandbox.command(
            workspace, hermes, policy=policy,
            policy_mount=immutable_policy_mount,
            private_profile_snapshot=snapshot,
            pinned_worktree=pin, hermes_profile=approved.name,
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
            pin.close()
            for tree in (immutable_policy_mount.code, *immutable_policy_mount.runtime):
                tree.cleanup_after_pane_closed()
            immutable_stage.close()
            immutable_stage.path.unlink(missing_ok=True)


def test_host_profile_refresh_is_required_before_seal(tmp_path, monkeypatch):
    item = mount(tmp_path)
    workspace = tmp_path / "worker"
    workspace.mkdir()
    admitted = grant(workspace)
    factory = factory_for(tmp_path, item, lambda **kwargs: admitted)
    approved, values = approved_profile(tmp_path)
    factory.approved_profile = approved
    try:
        with pytest.raises(SecurityError, match="preflight authority missing"):
            factory.prepare(identity=admitted.identity, workspace=workspace,
                            tools=admitted.scope.tools,
                            permissions=admitted.scope.permissions)
        # A refresh of the live auth bytes that is not approved in the
        # trusted manifest must fail closed, never seal stale credentials.
        calls = []
        def refreshed_before_freeze(profile_name):
            calls.append(profile_name)
            (approved.source / "auth.json").write_bytes(b'{"changed":"after-refresh"}\n')
            return True
        factory.profile_preflight = refreshed_before_freeze
        with pytest.raises(PrivateProfileError, match="profile_source_digest_mismatch"):
            factory.prepare(identity=admitted.identity, workspace=workspace,
                            tools=admitted.scope.tools,
                            permissions=admitted.scope.permissions)
        assert calls == ["quantlab"]
        # Reverting bytes to their reviewed hash accepts the profile without
        # asking the sandbox to run another host credential refresh.
        (approved.source / "auth.json").write_bytes(values["auth.json"])
    finally:
        cleanup(item)


def test_preflight_denial_does_not_freeze_credentials(tmp_path, monkeypatch):
    item = mount(tmp_path)
    workspace = tmp_path / "worker"
    workspace.mkdir()
    admitted = grant(workspace)
    factory = factory_for(tmp_path, item, lambda **kwargs: admitted)
    approved, _ = approved_profile(tmp_path)
    factory.approved_profile = approved
    factory.profile_preflight = lambda name: False
    frozen = []
    monkeypatch.setattr(ApprovedProfile, "freeze",
                        lambda self: frozen.append(self.name))
    try:
        with pytest.raises(SecurityError, match="preflight denied"):
            factory.prepare(identity=admitted.identity, workspace=workspace,
                            tools=admitted.scope.tools,
                            permissions=admitted.scope.permissions)
        assert frozen == []
    finally:
        cleanup(item)


def test_profile_memfds_close_even_when_earlier_cleanup_fails(tmp_path, monkeypatch):
    item = mount(tmp_path)
    workspace = tmp_path / "worker"
    workspace.mkdir()
    admitted = grant(workspace)
    factory = factory_for(tmp_path, item, lambda **kwargs: admitted)
    approved, _ = approved_profile(tmp_path)
    factory.approved_profile = approved
    factory.profile_preflight = lambda name: name == approved.name
    from herdr.host_bootstrap import HostBootstrap
    class FakeBootstrap:
        def cleanup_after_pane_closed(self): pass
    monkeypatch.setattr(HostBootstrap, "create",
                        classmethod(lambda cls, *args, **kwargs: FakeBootstrap()))
    prepared = None
    try:
        prepared = factory.prepare(identity=admitted.identity, workspace=workspace,
                                   tools=admitted.scope.tools,
                                   permissions=admitted.scope.permissions)
        profile = prepared.private_profile_snapshot
        profile.verify()
        original = prepared.mount.stage._same_inode
        def fail_stage():
            raise SecurityError("forced-stage-cleanup-failure")
        monkeypatch.setattr(prepared.mount.stage, "_same_inode", fail_stage)
        with pytest.raises(SecurityError, match="forced-stage-cleanup-failure"):
            prepared.cleanup_after_pane_closed()
        with pytest.raises(PrivateProfileError, match="profile_seal_closed"):
            profile.verify()
        # A retry may still finish all the other independently owned
        # cleanup resources, and closing already-closed memfds is idempotent.
        monkeypatch.setattr(prepared.mount.stage, "_same_inode", original)
        prepared.cleanup_after_pane_closed()
    finally:
        cleanup(item)


def test_profile_identity_is_canonical_and_signed_evidence_shape_is_bounded(tmp_path):
    from herdr.policy_launch import validate_policy_evidence
    from tests.policy_launch_fakes import policy_fixture
    approved, _ = approved_profile(tmp_path)
    with approved.freeze() as snapshot:
        assert snapshot.identity == approved.identity
        assert len(snapshot.identity["manifest_sha256"]) == 64
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        planned = grant(workspace)
        for modern in (False, True):
            proof = policy_fixture(planned.identity, modern=modern)
            proof["approved_profile"] = snapshot.identity
            assert validate_policy_evidence(proof, identity=planned.identity) == proof
            # Attempting to replace only profile digest or profile files
            # without updating both and the signature must be rejected.
            changed = {**proof, "approved_profile": {
                **proof["approved_profile"], "manifest_sha256": "0" * 64,
            }}
            with pytest.raises(SecurityError, match="approved profile evidence digest mismatch"):
                validate_policy_evidence(changed, identity=planned.identity)
            malformed = {**proof, "approved_profile": {
                **proof["approved_profile"], "private_key": "leak",
            }}
            with pytest.raises(SecurityError, match="approved profile evidence malformed"):
                validate_policy_evidence(malformed, identity=planned.identity)


def test_launch_requires_exact_approved_identity_in_signed_attestation(tmp_path):
    from herdr.policy_launch import PreparedPolicyLaunch
    approved, _ = approved_profile(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    planned = grant(workspace)
    class NoSeal:
        def seal(self, *args, **kwargs):
            raise AssertionError("no grant must be sealed without profile identity")
    with approved.freeze() as profile:
        prepared = PreparedPolicyLaunch(
            NoSeal(), planned, object(), "host-launch",
            private_profile_snapshot=profile,
        )
        for attestation in (
            {"task_id": planned.identity.task_id},
            {"task_id": planned.identity.task_id,
             "approved_profile": {**profile.identity, "manifest_sha256": "0" * 64}},
        ):
            with pytest.raises(SecurityError, match="approved profile must match"):
                prepared.seal(123, attestation, tools=(), permissions=())


def test_child_rejects_different_host_approved_profile_manifest(tmp_path):
    item = mount(tmp_path)
    workspace = tmp_path / "worker"
    workspace.mkdir()
    planned = grant(workspace)
    factory = factory_for(tmp_path, item, lambda **kwargs: planned, parent=planned)
    approved, _ = approved_profile(tmp_path)
    factory.approved_profile = approved
    factory.profile_preflight = lambda name: True
    try:
        with pytest.raises(SecurityError, match="child approved profile differs"):
            factory.prepare_child(identity=planned.identity, workspace=workspace,
                                  tools=planned.scope.tools,
                                  permissions=planned.scope.permissions)
        factory.parent_approved_profile = ApprovedProfile(
            approved.name, approved.source,
            {**approved.files, "config.yaml": "0" * 64},
        )
        with pytest.raises(SecurityError, match="child approved profile differs"):
            factory.prepare_child(identity=planned.identity, workspace=workspace,
                                  tools=planned.scope.tools,
                                  permissions=planned.scope.permissions)
        # A matching host manifest alone is insufficient: the child needs
        # the *accepted live parent launch* whose signed evidence committed
        # these exact file hashes.
        factory.parent_approved_profile = approved
        with pytest.raises(SecurityError, match="accepted live parent launch"):
            factory.prepare_child(identity=planned.identity, workspace=workspace,
                                  tools=planned.scope.tools,
                                  permissions=planned.scope.permissions)
        from herdr.policy_launch import PreparedPolicyLaunch
        with approved.freeze() as parent_snapshot:
            parent_launch = PreparedPolicyLaunch(
                object(), planned, None, "parent", private_profile_snapshot=parent_snapshot
            )
            parent_launch.sealed = object()
            parent_launch.evidence = lambda: {"approved_profile": approved.identity}
            factory.parent_launch = parent_launch
            # The signature/identity gate has passed. Normal parent-child
            # task/fence relationship is still enforced by the grant.
            with pytest.raises(SecurityError) as error:
                factory.prepare_child(identity=planned.identity, workspace=workspace,
                                      tools=planned.scope.tools,
                                      permissions=planned.scope.permissions)
            assert "child approved profile" not in str(error.value)
    finally:
        cleanup(item)


def test_retained_profile_identity_must_match_signed_attestation(tmp_path):
    from herdr.policy_launch import (
        process_start_ticks, verify_retained_policy_evidence,
    )
    from herdr.security import canonical_json_bytes
    from tests.policy_launch_fakes import policy_fixture
    approved, _ = approved_profile(tmp_path)
    workspace = tmp_path / "root"
    workspace.mkdir()
    planned = grant(workspace)
    proof = policy_fixture(planned.identity)
    proof["approved_profile"] = approved.identity
    proof["process_start_ticks"] = process_start_ticks(os.getpid())
    attacker = {**approved.identity, "manifest_sha256": "0" * 64}
    attestation = {
        "task_id": planned.identity.task_id,
        "run_token": planned.identity.run_token,
        "sandbox_pid": os.getpid(),
        "approved_profile": attacker,
    }
    proof["sandbox_attestation_sha256"] = hashlib.sha256(
        canonical_json_bytes(attestation)
    ).hexdigest()
    with pytest.raises(SecurityError, match="retained approved profile differs"):
        verify_retained_policy_evidence(
            proof, identity=planned.identity, pid=os.getpid(),
            attestation=attestation, require_bootstrap=False,
        )


def _root_published_mount_for_physical_test(tmp_path):
    """A nonsecret, root-owned released file stands in for code and Python.

    No running Hermes, secret or provider is accessed. The production
    publisher must independently publish the *real* signed code/runtime.
    """
    from herdr.policy_launch import (
        FrozenTree, PolicyMount, CODE_TARGET, RUNTIME_TARGETS,
    )
    from herdr.security import stage_policy_bundle
    published = Path(
        "/opt/herdr/releases/v0.3.0-rc.26-4d09b58b4416/provenance"
    )
    filename = "external-runtime-dependency.txt"
    if not (published / filename).is_file():
        pytest.skip("staging operator-published test fixture unavailable")
    manifest = {
        filename: hashlib.sha256((published / filename).read_bytes()).hexdigest()
    }
    stage = stage_policy_bundle(tmp_path / "policy-stage.json")
    trees = []
    try:
        for target in [CODE_TARGET, *sorted(RUNTIME_TARGETS)]:
            trees.append(
                FrozenTree.attach_immutable(
                    published, target=target, files=manifest,
                )
            )
        result = PolicyMount(stage, trees[0], tuple(trees[1:]))
        result.require_immutable_runtime()
        return result, stage
    except BaseException:
        for tree in trees:
            tree.cleanup_after_pane_closed()
        stage.close()
        stage.path.unlink(missing_ok=True)
        raise
