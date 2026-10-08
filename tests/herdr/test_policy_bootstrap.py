"""Offline same-interpreter bootstrap ordering and fixed production path tests."""
from __future__ import annotations
import importlib.machinery
import importlib.util
import hashlib
import json
import os
import subprocess
import sys
import types
import uuid
from pathlib import Path

import pytest

from herdr import security

LAUNCHER = Path(__file__).resolve().parents[2] / 'agent-stack/bin/agent-hermes-policy-run'
STAGE1 = Path(__file__).resolve().parents[2] / 'agent-stack/bin/agent-hermes-policy-stage1'
POLICY_BIN = LAUNCHER.parents[1] / 'policy-bin/hermes'


def _launcher():
    loader = importlib.machinery.SourceFileLoader('herdr76_policy_bootstrap_test', str(LAUNCHER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _stage1():
    loader = importlib.machinery.SourceFileLoader('herdr76_policy_stage1_test', str(STAGE1))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_fixed_production_entry_preserves_argv_without_policy_override(monkeypatch):
    module = _launcher()
    seen = []
    monkeypatch.setattr(module, 'bootstrap', lambda args: seen.append(args) or 0)
    monkeypatch.setenv(module._INTERPRETER_FD_ENV, 'test-stage-two')
    monkeypatch.setenv(module.STAGE1_PROOF_ENV, 'a' * 64)
    monkeypatch.setenv(module.STAGE2_FD_ENV, '9')
    monkeypatch.setenv(module.BOOTSTRAP_AUTH_FD_ENV, '10')
    monkeypatch.setattr(sys, 'argv', [str(LAUNCHER), '--grant', '/model/choice', '--key-fd', '3'])
    assert module.main() == 0
    assert seen == [['--grant', '/model/choice', '--key-fd', '3']]
    assert module.BUNDLE_PATH == Path('/run/herdr-policy/grant.bundle.json')


def test_policy_bin_hermes_invokes_guarded_launcher():
    assert POLICY_BIN.is_file()
    assert not POLICY_BIN.is_symlink()
    assert POLICY_BIN.read_text() == (
        '#!/bin/sh\n'
        'unset LD_PRELOAD LD_AUDIT LD_LIBRARY_PATH GLIBC_TUNABLES GCONV_PATH LOCPATH NLSPATH BASH_ENV ENV\n'
        'exec /usr/bin/python3 -I -S /run/herdr-bootstrap/agent-hermes-policy-stage1 "$@"\n'
    )
    assert "/run/herdr/policy-code" not in POLICY_BIN.read_text()
    assert POLICY_BIN.stat().st_mode & 0o111
    assert LAUNCHER.read_text(encoding="utf-8").splitlines()[0] == (
        "#!/usr/bin/python3 -I -S"
    )
    module = _launcher()
    with pytest.raises(
        SystemExit, match="security path (?:must have exactly one mountpoint|is not on a dedicated read-only trust mount)"
    ):
        module._require_production_mount(module.BUNDLE_PATH, exact=True)


@pytest.mark.parametrize("profile_consumed", [False, True])
def test_same_process_guard_precedes_hermes_main(monkeypatch, tmp_path, profile_consumed):
    module = _launcher()
    monkeypatch.setattr(module, '_verify_hermes_build', lambda root: module.HERMES_EXECUTOR)
    monkeypatch.setattr(module,'_require_host_bootstrap_authority',lambda:None)
    monkeypatch.setattr(module,'_require_stage1_continuity',lambda:None)
    monkeypatch.setattr(module,'_require_production_mount',lambda *args,**kwargs:None)
    monkeypatch.setattr(module,'_verify_runtime',lambda root:None)
    monkeypatch.setattr(module,'BUNDLE_PATH',tmp_path/'bundle')
    monkeypatch.setattr(module,'POLICY_CODE_ROOT',LAUNCHER.parents[2])
    monkeypatch.setattr(module,'HERMES_ROOT',tmp_path/'hermes')
    hermes = tmp_path / 'hermes'
    (hermes / 'venv').mkdir(parents=True)
    (hermes / 'model_tools.py').write_text('')
    (hermes / 'hermes').write_text('')
    identity = security.InvocationIdentity('github:Bbambaaamm/herdr', 'agent', 'parent',
                                           'parent-task', 'task', 'run', 3)
    for name, env_name in module.IDENTITY_ENV.items():
        monkeypatch.setenv(env_name, str(getattr(identity, name)))
    monkeypatch.setenv('HERDR_POLICY_BUNDLE_PATH', '/attacker/bundle.json')
    events = []
    fake_guard = types.ModuleType('herdr.hermes_guard')
    fake_guard.__file__ = str(LAUNCHER.parents[2] / 'herdr/hermes_guard.py')
    def install_guard(guard):
        assert os.environ["HERMES_SAFE_MODE"] == "1"
        assert os.environ["HERMES_ENABLE_PROJECT_PLUGINS"] == "0"
        events.append('installed')
    fake_guard.install_hermes_guard = install_guard
    fake_guard.InvocationGuard = lambda grant: grant
    fake_main = types.ModuleType('hermes_cli.main')
    fake_main.__file__ = str(hermes / 'hermes')
    fake_state = types.ModuleType('hermes_state')
    (hermes / 'hermes_state.py').write_text('')
    fake_state.__file__ = str(hermes / 'hermes_state.py')
    fake_state.DEFAULT_DB_PATH = hermes / 'state.db'
    fake_cli = types.ModuleType("cli")
    (hermes / "cli.py").write_text("")
    fake_cli.__file__ = str(hermes / "cli.py")
    approved_home = hermes / "approved-profile"
    fake_cli._hermes_home = approved_home
    config = {"model": "approved-model", "agent": {"prefill_messages_file": "prompts/approved.json"}}
    fake_cli.CLI_CONFIG = config
    fake_cli._resolve_prefill_messages_file = lambda cfg: (
        os.getenv("HERMES_PREFILL_MESSAGES_FILE", "")
        or cfg.get("prefill_messages_file", "")
        or cfg.get("agent", {}).get("prefill_messages_file", "")
    )
    fake_cli.get_hermes_home = lambda: approved_home
    monkeypatch.setitem(sys.modules, "cli", fake_cli)
    private_state = Path('/tmp') / ('herdr-sdk-state-test-' + uuid.uuid4().hex)
    monkeypatch.setattr(module, '_EPHEMERAL_SDK_STATE_ROOT', private_state)
    monkeypatch.setattr(module, '_require_private_sdk_tmp', lambda: 123)
    monkeypatch.setattr(module, '_sdk_state_mount_id', lambda path: 123)
    monkeypatch.setitem(sys.modules, 'hermes_state', fake_state)
    def main():
        assert events == ['verified', 'installed']
        assert fake_state.DEFAULT_DB_PATH == private_state / 'state.db'
        assert fake_cli._hermes_home == private_state
        assert fake_cli.get_hermes_home() == approved_home
        assert fake_cli.CLI_CONFIG is config
        # Prefill is loaded after CLI initialization: relative paths must still
        # resolve against the approved profile, never the writable SDK home.
        assert fake_cli._resolve_prefill_messages_file(config) == str(
            approved_home / "prompts/approved.json"
        )
        assert fake_cli._resolve_prefill_messages_file(
            {"prefill_messages_file": "/approved/external.json"}
        ) == "/approved/external.json"
        assert private_state.stat().st_mode & 0o777 == 0o700
        assert Path('/proc/self/comm').read_text().strip() == 'hermes'
        assert os.environ["HERMES_SAFE_MODE"] == "1"
        assert os.environ["HERMES_ENABLE_PROJECT_PLUGINS"] == "0"
        assert sys.argv == ([str(hermes / 'hermes'), 'chat'] if profile_consumed
                            else [str(hermes / 'hermes'), 'chat', '--profile', 'test'])
        events.append('main')
        return 0
    fake_main.main = main
    fake_pkg = types.ModuleType('hermes_cli')
    fake_pkg.main = fake_main
    monkeypatch.setitem(sys.modules, 'herdr.hermes_guard', fake_guard)
    monkeypatch.setitem(sys.modules, 'hermes_cli', fake_pkg)
    monkeypatch.setitem(sys.modules, 'hermes_cli.main', fake_main)
    from herdr import work_contract_host, work_authority
    def fixture_work_guard(grant, *, work_authority):
        from herdr.work_authority import WorkAuthorityClient
        assert isinstance(work_authority, WorkAuthorityClient)
        return grant
    monkeypatch.setattr(work_contract_host, 'WorkInvocationGuard', fixture_work_guard)
    monkeypatch.setattr(security, 'load_policy_bundle',
                        lambda root, got, **kwargs: (
                            events.append('verified') if root == tmp_path / 'bundle' and got == identity
                            else (_ for _ in ()).throw(AssertionError('alternate authority used'))
                        ) or types.SimpleNamespace(scope=types.SimpleNamespace(executors=(module.HERMES_EXECUTOR,))))
    original_import = module.importlib.import_module
    def import_with_profile_processing(name, *args, **kwargs):
        if name == "hermes_cli.main":
            assert events == ["verified", "installed"]
            assert sys.argv == [str(hermes / "hermes"), "chat", "--profile", "test"]
            if profile_consumed:
                del sys.argv[-2:]
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(module.importlib, "import_module", import_with_profile_processing)
    saved_path, saved_argv = sys.path[:], sys.argv[:]
    try:
        assert module.bootstrap(['chat', '--profile', 'test']) == 0
    finally:
        sys.path[:] = saved_path
        sys.argv[:] = saved_argv
        if private_state.exists():
            private_state.rmdir()
    assert events == ['verified', 'installed', 'main']


def test_launcher_requires_exact_pane_identity(monkeypatch, tmp_path):
    module = _launcher()
    monkeypatch.setattr(module, '_verify_hermes_build', lambda root: module.HERMES_EXECUTOR)
    monkeypatch.setattr(module,'_require_host_bootstrap_authority',lambda:None)
    monkeypatch.setattr(module,'_require_stage1_continuity',lambda:None)
    monkeypatch.setattr(module,'_require_production_mount',lambda *args,**kwargs:None)
    monkeypatch.setattr(module,'_verify_runtime',lambda root:None)
    monkeypatch.setattr(module,'BUNDLE_PATH',tmp_path/'bundle')
    monkeypatch.setattr(module,'POLICY_CODE_ROOT',LAUNCHER.parents[2])
    monkeypatch.setattr(module,'HERMES_ROOT',tmp_path/'hermes')
    hermes = tmp_path / 'hermes'
    (hermes / 'venv').mkdir(parents=True)
    (hermes / 'model_tools.py').write_text('')
    (hermes / 'hermes').write_text('')
    monkeypatch.delenv(module.IDENTITY_ENV['fencing_token'], raising=False)
    saved_path = sys.path[:]
    try:
        try:
            module.bootstrap([])
        except SystemExit as exc:
            assert 'signed Herdr grant rejected' in str(exc)
        else:
            assert False, 'missing fence was accepted'
    finally:
        sys.path[:] = saved_path


def test_preimport_executor_verifier_checks_actual_bytes(monkeypatch, tmp_path):
    module = _launcher()
    root = tmp_path / 'hermes'
    root.mkdir()
    (root / 'pyproject.toml').write_text('[project]\nversion = "0.21.5"\n')
    (root / 'model_tools.py').write_text('audited = True\n')
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    git('init')
    git('config', 'user.name', 'Test')
    git('config', 'user.email', 'test@example.invalid')
    git('add', '.')
    git('commit', '-m', 'audited')
    digest = hashlib.sha256()
    for name in subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).split(b'\0'):
        if name:
            digest.update(name + b'\0')
            digest.update(hashlib.sha256((root / name.decode()).read_bytes()).digest())
    expected = f'hermes:0.21.5:sha256:{digest.hexdigest()}'
    monkeypatch.setattr(module, 'HERMES_HEAD', git('rev-parse', 'HEAD'))
    monkeypatch.setattr(module, '_SOURCE_EXECUTOR', expected)
    assert module._verify_hermes_build(root) == module.HERMES_EXECUTOR
    (root / 'model_tools.py').write_text('audited = False\n')
    with pytest.raises(SystemExit, match='cannot verify audited Hermes build|differs from signed executor'):
        module._verify_hermes_build(root)
    (root / 'model_tools.py').write_text('audited = True\n')
    (root / '.git/info/exclude').write_text('injected.py\n')
    (root / 'injected.py').write_text('raise RuntimeError("imported")\n')
    with pytest.raises(SystemExit, match='cannot verify audited Hermes build'):
        module._verify_hermes_build(root)


def test_venv_import_surface_hash_excludes_only_unreachable_cache(tmp_path):
    module = _launcher()
    site = tmp_path / 'site-packages'
    package = site / 'package'
    package.mkdir(parents=True)
    source = package / '__init__.py'
    source.write_text('value = 1\n')
    original = module._digest_site_packages(site)
    cache = package / '__pycache__'
    cache.mkdir()
    (cache / '__init__.cpython-311.pyc').write_bytes(b'attacker bytecode')
    assert module._digest_site_packages(site) == original
    (package / 'module.pyc').write_bytes(b'also unreachable with pycache_prefix')
    with pytest.raises(SystemExit, match='sourceless venv bytecode'):
        module._digest_site_packages(site)
    (package / 'module.pyc').unlink()
    source.write_text('value = 2\n')
    assert module._digest_site_packages(site) != original
    source.write_text('value = 1\n')
    (site / 'startup.pth').write_text('import attacker\n')
    assert module._digest_site_packages(site) != original


def test_preimport_git_ignores_repo_local_fsmonitor(monkeypatch, tmp_path):
    module = _launcher()
    root = tmp_path / "hermes"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nversion = "0.21.5"\n')
    (root / "model_tools.py").write_text("audited = True\n")

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    git("init")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    git("add", ".")
    git("commit", "-m", "audited")

    digest = hashlib.sha256()
    for name in subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"]
    ).split(b"\0"):
        if name:
            digest.update(name + b"\0")
            digest.update(hashlib.sha256((root / name.decode()).read_bytes()).digest())
    monkeypatch.setattr(module, "HERMES_HEAD", git("rev-parse", "HEAD"))
    monkeypatch.setattr(
        module, "_SOURCE_EXECUTOR",
        f"hermes:0.21.5:sha256:{digest.hexdigest()}",
    )

    marker = tmp_path / "fsmonitor-executed"
    hook = tmp_path / "malicious-fsmonitor.sh"
    hook.write_text(
        "#!/bin/sh\nprintf executed >> " + str(marker) + "\nprintf '{}\\n'\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    git("config", "core.fsmonitor", str(hook))

    assert module._verify_hermes_build(root) == module.HERMES_EXECUTOR
    assert not marker.exists()


def test_production_trust_mount_requires_dedicated_readonly_exact_root(monkeypatch, tmp_path):
    module = _launcher()
    trusted = tmp_path / "trusted"

    monkeypatch.setattr(module, "_covering_mount", lambda path: (trusted, {"ro", "nosuid"}))
    monkeypatch.setattr(module, "_mount_rows", lambda: {str(trusted): {"ro", "nosuid"}})
    monkeypatch.setattr(module, "_mountpoint_count", lambda path: 1)
    module._require_production_mount(trusted, exact=True)

    for nested_mode in ("rw", "ro"):
        monkeypatch.setattr(
            module, "_mount_rows",
            lambda mode=nested_mode: {
                str(trusted): {"ro"}, str(trusted / "nested"): {mode}
            },
        )
        with pytest.raises(SystemExit, match="unexpected descendant mount below immutable trust root"):
            module._require_production_mount(trusted, exact=True)
    monkeypatch.setattr(module, "_mount_rows", lambda: {str(trusted): {"ro"}})

    monkeypatch.setattr(module, "_covering_mount", lambda path: (Path("/"), {"ro"}))
    with pytest.raises(SystemExit, match="dedicated read-only trust mount"):
        module._require_production_mount(trusted, exact=True)

    monkeypatch.setattr(module, "_covering_mount", lambda path: (trusted, {"rw", "nosuid"}))
    with pytest.raises(SystemExit, match="dedicated read-only trust mount"):
        module._require_production_mount(trusted, exact=True)

    parent = trusted.parent
    monkeypatch.setattr(module, "_covering_mount", lambda path: (parent, {"ro"}))
    with pytest.raises(SystemExit, match="dedicated read-only trust mount"):
        module._require_production_mount(trusted, exact=True)


def test_production_bootstrap_checks_all_lifetime_trust_roots_before_hashing(monkeypatch):
    module = _launcher()
    calls = []

    def require(path, *, exact=False):
        calls.append((path, exact))
        if path == module.PYTHON_ROOT:
            raise RuntimeError("stop-after-trust-roots")

    monkeypatch.setattr(module, "_require_host_bootstrap_authority",
                        lambda: calls.append(("hostauth", True)))
    monkeypatch.setattr(module, "_require_stage1_continuity", lambda: calls.append(("stage1", True)))
    monkeypatch.setattr(module, "_require_production_mount", require)
    with pytest.raises(RuntimeError, match="stop-after-trust-roots"):
        module.bootstrap([])
    assert calls == [
        ("hostauth", True),
        ("stage1", True),
        (module.BUNDLE_PATH, True),
        (module.POLICY_CODE_ROOT, True),
        (module.HERMES_ROOT, True),
        (module.PYTHON_ROOT, True),
    ]


def test_stage1_verifies_frozen_identity_digest_and_rw_descendants(monkeypatch, tmp_path):
    module = _stage1()
    bootstrap = tmp_path / "bootstrap"
    policy = tmp_path / "policy"
    hermes = tmp_path / "hermes"
    python_root = tmp_path / "python"
    for root in (bootstrap, policy, hermes, python_root):
        root.mkdir()
    (policy / "herdr").mkdir()
    (policy / "herdr/security.py").write_text("VALUE = 1\\n", encoding="utf-8")
    (hermes / "marker").write_text("h", encoding="utf-8")
    (python_root / "marker").write_text("p", encoding="utf-8")
    stdlib=python_root / "lib/python3.11"
    stdlib.mkdir(parents=True)
    (stdlib / "approved.py").write_text("approved=True\n")
    monkeypatch.setattr(module,"PYTHON_STDLIB_SHA256",module._stdlib_import_digest(stdlib))
    monkeypatch.setattr(module,"PYTHON_RUNTIME_TREE_SHA256",module._tree_manifest_digest(python_root))

    monkeypatch.setattr(module, "BOOTSTRAP_ROOT", bootstrap)
    monkeypatch.setattr(module, "POLICY_CODE_ROOT", policy)
    monkeypatch.setattr(module, "HERMES_ROOT", hermes)
    monkeypatch.setattr(module, "PYTHON_ROOT", python_root)
    identity = {
        "consumer": "github:Bbambaaamm/herdr",
        "agent_id": "agent",
        "parent_agent_id": "parent",
        "parent_task_id": "parent-task",
        "task_id": "task",
        "run_token": "run",
        "fencing_token": 9,
    }
    for field, env_name in module.IDENTITY_ENV.items():
        monkeypatch.setenv(env_name, str(identity[field]))

    rows = {str(root): {"ro"} for root in (bootstrap, policy, hermes, python_root)}
    policy_digest = module._tree_manifest_digest(policy)
    proof = {
        "schema_version": module.PROOF_VERSION,
        "authority": module.PROOF_AUTHORITY,
        "identity": identity,
        "trees": {},
    }
    for index, root in enumerate((policy, hermes, python_root)):
        info = root.stat()
        proof["trees"][str(root)] = {
            "device": info.st_dev,
            "inode": info.st_ino,
            "source_digest": policy_digest if root == policy else str(index + 1) * 64,
            "snapshot_kind": "host-frozen-copy",
        }
    proof_path = bootstrap / "immutable-trees.json"
    proof_path.write_text(
        json.dumps(proof, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    parsed, _ = module._read_proof(proof_path)
    module._verify_trees(parsed, rows)

    for nested_mode in ("rw", "ro"):
        poisoned = dict(rows)
        poisoned[str(policy / "nested")] = {nested_mode}
        with pytest.raises(SystemExit, match="unexpected descendant mount below immutable trust root"):
            module._verify_trees(parsed, poisoned)

    (policy / "herdr/security.py").write_text("VALUE = 2\\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="policy snapshot digest mismatch"):
        module._verify_trees(parsed, rows)


def test_stage2_direct_execution_without_stage1_proof_is_rejected(monkeypatch):
    module = _launcher()
    monkeypatch.delenv(module._INTERPRETER_FD_ENV, raising=False)
    monkeypatch.delenv(module.STAGE1_PROOF_ENV, raising=False)
    monkeypatch.delenv(module.STAGE2_FD_ENV, raising=False)
    monkeypatch.delenv(module.BOOTSTRAP_AUTH_FD_ENV, raising=False)
    with pytest.raises(SystemExit, match="verified immutable stage-one bootstrap required"):
        module.main()


def test_stage1_execs_verified_stage2_source_fd(monkeypatch):
    module = _stage1()
    from herdr.launch_environment import sanitize_environment
    monkeypatch.setattr(module.os,"environ",sanitize_environment(module.os.environ))
    monkeypatch.setattr(module, "_require_independent_stage0", lambda: None)
    monkeypatch.setattr(module, "_mount_rows", lambda: {})
    monkeypatch.setattr(module, "_require_exact_ro_tree", lambda *args: None)
    monkeypatch.setattr(module, "_read_proof", lambda *args: ({}, b"proof"))
    monkeypatch.setattr(module, "_verify_trees", lambda *args: None)
    monkeypatch.setattr(module, "_open_verified_stage2", lambda: 41)
    monkeypatch.setattr(module, "_open_verified_python", lambda: 42)
    monkeypatch.setattr(module, "_connect_host_authority", lambda *args: 43)
    monkeypatch.setattr(module, "_fresh_pycache_prefix", lambda: "/run/herdr-bootstrap/no-bytecode-cache")
    monkeypatch.setattr(module.os, "set_inheritable", lambda *args: None)
    seen = {}

    def fake_execve(executable, argv, env):
        seen.update(executable=executable, argv=argv, env=env)
        raise RuntimeError("execve captured")

    monkeypatch.setattr(module.os, "execve", fake_execve)
    with pytest.raises(RuntimeError, match="execve captured"):
        module.main(["chat", "--profile", "test"])
    assert seen["executable"] == "/proc/self/fd/42"
    assert seen["argv"] == [
        "/proc/self/fd/42", "-I", "-S", "-X",
        "pycache_prefix=/run/herdr-bootstrap/no-bytecode-cache", "/proc/self/fd/41",
        "chat", "--profile", "test",
    ]
    assert seen["env"][module.INTERPRETER_FD_ENV] == "42"
    assert seen["env"][module.STAGE2_FD_ENV] == "41"
    assert seen["env"][module.AUTHORITY_FD_ENV] == "43"
    assert seen["env"][module.PROOF_ENV] == hashlib.sha256(b"proof").hexdigest()


def test_stage2_continuity_binds_loaded_source_to_held_fd(monkeypatch):
    module = _launcher()
    fd = os.open(LAUNCHER, os.O_RDONLY)
    try:
        monkeypatch.setenv(module.STAGE2_FD_ENV, str(fd))
        module._require_held_stage2_source(str(LAUNCHER))
        other = LAUNCHER.parent / "agent-hermes-policy-stage1"
        with pytest.raises(SystemExit, match="stage-two source differs"):
            module._require_held_stage2_source(str(other))
    finally:
        os.close(fd)


def test_bundle_trust_path_rejects_stacked_mountpoints(monkeypatch, tmp_path):
    module = _launcher()
    trusted = tmp_path / "bundle.json"
    monkeypatch.setattr(module, "_mountpoint_count", lambda path: 2)
    monkeypatch.setattr(module, "_covering_mount", lambda path: (trusted, {"ro"}))
    monkeypatch.setattr(module, "_mount_rows", lambda: {str(trusted): {"ro"}})
    with pytest.raises(SystemExit, match="exactly one mountpoint"):
        module._require_production_mount(trusted, exact=True)

    monkeypatch.setattr(module, "_mountpoint_count", lambda path: 1)
    module._require_production_mount(trusted, exact=True)


def test_runtime_requires_startup_pycache_prefix(monkeypatch):
    module = _launcher()
    monkeypatch.setattr(module.sys, "pycache_prefix", None)
    with pytest.raises(SystemExit, match="pycache prefix"):
        module._require_startup_pycache_prefix()


def test_stage1_rejects_stacked_exact_trust_root(tmp_path):
    module = _stage1()
    root = tmp_path / "bootstrap"
    root.mkdir()
    info = root.stat()
    rows = {str(root): {"ro", "__stacked__"}}
    with pytest.raises(SystemExit, match="one exact read-only trust mount"):
        module._require_exact_ro_tree(root, rows)

def test_startup_cache_is_absent_under_frozen_root_not_same_uid_tmp(tmp_path,monkeypatch):
    stage1, stage2 = _stage1(), _launcher()
    root = tmp_path / "bootstrap"
    root.mkdir()
    monkeypatch.setattr(stage1,"BOOTSTRAP_ROOT",root)
    monkeypatch.setattr(stage2,"BOOTSTRAP_ROOT",root)
    monkeypatch.setattr(stage1,"_mount_rows",lambda:{str(root):{"ro"}})
    prefix = str(root / "no-bytecode-cache")
    assert stage1._fresh_pycache_prefix() == prefix
    monkeypatch.setattr(stage2.sys,"pycache_prefix",prefix)
    stage2._require_startup_pycache_prefix()
    # A peer-populated cache is rejected rather than trusted because of 0700.
    (root / "no-bytecode-cache").mkdir(mode=0o700)
    with pytest.raises(SystemExit,match="remain absent"):
        stage1._fresh_pycache_prefix()
    with pytest.raises(SystemExit,match="remain absent"):
        stage2._require_startup_pycache_prefix()
    monkeypatch.setattr(stage2.sys,"pycache_prefix","/tmp/herdr-policy-pycache-attacker")
    with pytest.raises(SystemExit,match="immutable startup"):
        stage2._require_startup_pycache_prefix()

def test_stage1_cache_requires_physical_readonly_bootstrap(tmp_path,monkeypatch):
    module = _stage1()
    root = tmp_path / "bootstrap"
    root.mkdir()
    monkeypatch.setattr(module,"BOOTSTRAP_ROOT",root)
    monkeypatch.setattr(module,"_mount_rows",lambda:{str(root):{"rw"}})
    with pytest.raises(SystemExit,match="read-only"):
        module._fresh_pycache_prefix()


def test_actual_user_namespace_keeps_stage0_verification_before_host_handshake():
    import shutil
    if not shutil.which("bwrap") or not _stage1().PYTHON_PATH.is_file():
        pytest.skip("bwrap/pinned runtime prerequisite unavailable")
    script=("import importlib.machinery,importlib.util;"
        f"loader=importlib.machinery.SourceFileLoader('stage1_probe',{str(STAGE1)!r});"
        "spec=importlib.util.spec_from_loader(loader.name,loader);"
        "m=importlib.util.module_from_spec(spec);loader.exec_module(m);"
        "m._require_independent_stage0();print('independent-stage0-ready-for-host-auth')")
    result=subprocess.run(["/usr/bin/bwrap","--ro-bind","/","/","--unshare-pid","--proc","/proc",
                           "--","/usr/bin/python3","-I","-S","-c",script],
                          capture_output=True,text=True,timeout=5)
    if result.returncode and "Operation not permitted" in result.stderr:
        pytest.skip("kernel user-namespace prerequisite unavailable")
    assert result.returncode==0,result.stderr
    assert "ready-for-host-auth" in result.stdout


def test_stage_two_bootstrap_json_encoder_is_available():
    module=_launcher()
    assert module._canonical_bootstrap({"op":"stage2"})==b'{"op":"stage2"}'

def test_independent_stage1_rejects_changed_startup_stdlib_before_exec(tmp_path,monkeypatch):
    module=_stage1();root=tmp_path/"python";stdlib=root/"lib/python3.11"
    (stdlib/"encodings").mkdir(parents=True)
    entry=stdlib/"encodings/__init__.py";entry.write_text("audited=True\n")
    expected=module._stdlib_import_digest(stdlib)
    monkeypatch.setattr(module,"PYTHON_ROOT",root)
    monkeypatch.setattr(module,"PYTHON_STDLIB_SHA256",expected)
    monkeypatch.setattr(module,"PYTHON_RUNTIME_TREE_SHA256",module._tree_manifest_digest(root))
    module._verify_pinned_startup_imports()
    entry.write_text("raise RuntimeError('must never execute')\n")
    with pytest.raises(SystemExit,match="before interpreter exec"):
        module._verify_pinned_startup_imports()

@pytest.mark.parametrize("name",["lib/python311.zip","pyvenv.cfg","bin/pyvenv.cfg"])
def test_stage1_denies_unaudited_startup_prefix_or_zip(tmp_path,monkeypatch,name):
    module=_stage1();root=tmp_path/"python";path=root/name
    path.parent.mkdir(parents=True);path.write_text("untrusted")
    monkeypatch.setattr(module,"PYTHON_ROOT",root)
    with pytest.raises(SystemExit,match="startup override"):module._verify_pinned_startup_imports()


def test_no_parameterized_bootstrap_or_custom_script_exec_escape(tmp_path):
    module=_launcher()
    with pytest.raises(TypeError):
        module.bootstrap([],bundle_path=tmp_path/"self-signed.json")
    assert not hasattr(module,"_exec_verified_interpreter")
    with pytest.raises(SystemExit,match="authority"):
        module.bootstrap([])

def test_stage1_checks_native_libraries_outside_stdlib_before_exec(tmp_path,monkeypatch):
    module=_stage1();root=tmp_path/"python";stdlib=root/"lib/python3.11"
    stdlib.mkdir(parents=True);(stdlib/"audited.py").write_text("approved")
    shared=root/"lib/libpython3.11.so.1.0";shared.write_bytes(b"audited-native")
    monkeypatch.setattr(module,"PYTHON_ROOT",root)
    monkeypatch.setattr(module,"PYTHON_RUNTIME_TREE_SHA256",module._tree_manifest_digest(root))
    monkeypatch.setattr(module,"PYTHON_STDLIB_SHA256",module._stdlib_import_digest(stdlib))
    module._verify_pinned_startup_imports()
    shared.write_bytes(b"malicious-native")
    with pytest.raises(SystemExit,match="complete Python runtime tree"):
        module._verify_pinned_startup_imports()

@pytest.mark.parametrize("raises", [False, True])
def test_native_actual_hermes_label_is_kernel_visible_and_restored(raises):
    module = _launcher()
    before = Path("/proc/self/comm").read_bytes()
    with pytest.raises(ValueError) if raises else __import__("contextlib").nullcontext():
        with module._native_hermes_process_label():
            assert Path("/proc/self/comm").read_text().strip() == "hermes"
            if raises:
                raise ValueError("main failed")
    assert Path("/proc/self/comm").read_bytes() == before


def test_unauthenticated_bootstrap_never_sets_native_agent_label(monkeypatch):
    module = _launcher()
    monkeypatch.setattr(module, "_require_host_bootstrap_authority",
        lambda: (_ for _ in ()).throw(SystemExit("host authority denied")))
    monkeypatch.setattr(module, "_native_hermes_process_label",
        lambda: pytest.fail("unverified program must not be labelled Hermes"))
    with pytest.raises(SystemExit, match="host authority denied"):
        module.bootstrap([])


@pytest.mark.parametrize("fields,filesystem", [
    ("3 1 0:2 / / rw", "ext4 root rw"),
    ("3 1 0:2 / /tmp ro", "tmpfs tmpfs rw"),
    ("3 1 0:2 /tmp /tmp rw", "tmpfs tmpfs rw"),
    ("4 1 0:2 / /tmp rw", "tmpfs tmpfs rw"),
])
def test_sdk_state_rejects_unverified_mount_before_import(monkeypatch, fields, filesystem):
    module = _launcher()
    monkeypatch.setattr(module, "_sdk_state_mount_id", lambda path: 3)
    original_read = Path.read_bytes
    def read(path):
        if path == Path("/proc/self/mountinfo"):
            return (fields + " - " + filesystem + "\n").encode()
        return original_read(path)
    monkeypatch.setattr(Path, "read_bytes", read)
    monkeypatch.setattr(module.importlib, "import_module",
                        lambda name: (_ for _ in ()).throw(AssertionError("SDK imported before mount check")))
    with pytest.raises(SystemExit, match="private writable SDK state mount unavailable"):
        module._configure_ephemeral_sdk_state(Path("/untrusted-sdk"))


def test_sdk_state_uses_opened_mount_over_covered_host_tmp(monkeypatch):
    module = _launcher()
    monkeypatch.setattr(module, "_sdk_state_mount_id", lambda path: 4)
    original_read = Path.read_bytes
    def read(path):
        if path == Path("/proc/self/mountinfo"):
            return b"3 1 0:2 / /tmp ro - tmpfs tmpfs rw\n4 3 0:3 / /tmp rw - tmpfs tmpfs rw\n"
        return original_read(path)
    monkeypatch.setattr(Path, "read_bytes", read)
    assert module._require_private_sdk_tmp() == 4


def test_sdk_state_rejects_existing_directory(monkeypatch, tmp_path):
    module = _launcher()
    fake_state = types.ModuleType("hermes_state")
    fake_state.__file__ = str(tmp_path / "hermes_state.py")
    (tmp_path / "hermes_state.py").write_text("")
    fake_state.DEFAULT_DB_PATH = tmp_path / "host-state.db"
    fake_cli = types.ModuleType("cli")
    (tmp_path / "cli.py").write_text("")
    fake_cli.__file__ = str(tmp_path / "cli.py")
    fake_cli._hermes_home = tmp_path / "host-home"
    fake_cli._resolve_prefill_messages_file = lambda cfg: cfg.get("prefill_messages_file", "")
    monkeypatch.setitem(sys.modules, "cli", fake_cli)
    directory = Path("/tmp") / ("herdr-sdk-state-existing-" + uuid.uuid4().hex)
    directory.mkdir(mode=0o700)
    monkeypatch.setattr(module, "_EPHEMERAL_SDK_STATE_ROOT", directory)
    monkeypatch.setattr(module, "_require_private_sdk_tmp", lambda: 123)
    monkeypatch.setattr(module, "_sdk_state_mount_id", lambda path: 123)
    monkeypatch.setitem(sys.modules, "hermes_state", fake_state)
    try:
        with pytest.raises(SystemExit, match="fresh private SDK state unavailable"):
            module._configure_ephemeral_sdk_state(tmp_path)
        assert fake_state.DEFAULT_DB_PATH == tmp_path / "host-state.db"
        assert fake_cli._hermes_home == tmp_path / "host-home"
    finally:
        directory.rmdir()


@pytest.mark.parametrize("untrusted", ["hermes_state", "cli"])
def test_sdk_state_rejects_untrusted_modules_before_redirect(monkeypatch, tmp_path, untrusted):
    module = _launcher()
    monkeypatch.setattr(module, "_require_private_sdk_tmp", lambda: 123)
    monkeypatch.setattr(module, "_sdk_state_mount_id", lambda path: 123)
    state = types.ModuleType("hermes_state")
    cli = types.ModuleType("cli")
    (tmp_path / "hermes_state.py").write_text("")
    (tmp_path / "cli.py").write_text("")
    state.__file__ = str(tmp_path / "hermes_state.py")
    cli.__file__ = str(tmp_path / "cli.py")
    state.DEFAULT_DB_PATH = tmp_path / "host-state.db"
    cli._hermes_home = tmp_path / "host-home"
    modules = {"hermes_state": state, "cli": cli}
    modules[untrusted].__file__ = str(tmp_path.parent / "untrusted.py")
    for name, value in modules.items():
        monkeypatch.setitem(sys.modules, name, value)
    directory = Path("/tmp") / ("herdr-sdk-state-untrusted-" + uuid.uuid4().hex)
    monkeypatch.setattr(module, "_EPHEMERAL_SDK_STATE_ROOT", directory)
    with pytest.raises(SystemExit):
        module._configure_ephemeral_sdk_state(tmp_path)
    assert not directory.exists()
    assert state.DEFAULT_DB_PATH == tmp_path / "host-state.db"
    assert cli._hermes_home == tmp_path / "host-home"
