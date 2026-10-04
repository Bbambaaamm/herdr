"""Offline same-interpreter bootstrap ordering and fixed production path tests."""
from __future__ import annotations
import importlib.machinery
import importlib.util
import hashlib
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

from herdr import security

LAUNCHER = Path(__file__).resolve().parents[2] / 'agent-stack/bin/agent-hermes-policy-run'
POLICY_BIN = LAUNCHER.parents[1] / 'policy-bin/hermes'


def _launcher():
    loader = importlib.machinery.SourceFileLoader('herdr76_policy_bootstrap_test', str(LAUNCHER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_fixed_production_entry_preserves_argv_without_policy_override(monkeypatch):
    module = _launcher()
    seen = []
    monkeypatch.setattr(module, 'bootstrap', lambda args: seen.append(args) or 0)
    monkeypatch.setenv(module._INTERPRETER_FD_ENV, 'test-stage-two')
    monkeypatch.setattr(sys, 'argv', [str(LAUNCHER), '--grant', '/model/choice', '--key-fd', '3'])
    assert module.main() == 0
    assert seen == [['--grant', '/model/choice', '--key-fd', '3']]
    assert module.BUNDLE_PATH == Path('/run/herdr-policy/grant.bundle.json')


def test_policy_bin_hermes_invokes_guarded_launcher():
    assert POLICY_BIN.is_file()
    assert not POLICY_BIN.is_symlink()
    assert POLICY_BIN.read_text() == '#!/bin/sh\nexec /usr/bin/python3 -I -S /run/herdr/policy-code/agent-stack/bin/agent-hermes-policy-run "$@"\n'
    assert POLICY_BIN.stat().st_mode & 0o111
    assert LAUNCHER.read_text(encoding="utf-8").splitlines()[0] == (
        "#!/usr/bin/python3 -I -S"
    )
    module = _launcher()
    with pytest.raises(
        SystemExit, match="security path is not on a dedicated read-only trust mount"
    ):
        module._require_production_mount(module.BUNDLE_PATH, exact=True)


def test_same_process_guard_precedes_hermes_main(monkeypatch, tmp_path):
    module = _launcher()
    monkeypatch.setattr(module, '_verify_hermes_build', lambda root: module.HERMES_EXECUTOR)
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
    def main():
        assert events == ['verified', 'installed']
        assert os.environ["HERMES_SAFE_MODE"] == "1"
        assert os.environ["HERMES_ENABLE_PROJECT_PLUGINS"] == "0"
        assert sys.argv == [str(hermes / 'hermes'), 'chat', '--profile', 'test']
        events.append('main')
        return 0
    fake_main.main = main
    fake_pkg = types.ModuleType('hermes_cli')
    fake_pkg.main = fake_main
    monkeypatch.setitem(sys.modules, 'herdr.hermes_guard', fake_guard)
    monkeypatch.setitem(sys.modules, 'hermes_cli', fake_pkg)
    monkeypatch.setitem(sys.modules, 'hermes_cli.main', fake_main)
    monkeypatch.setattr(security, 'InvocationGuard', lambda grant: grant)
    monkeypatch.setattr(security, 'load_policy_bundle',
                        lambda root, got, **kwargs: (
                            events.append('verified') if root == tmp_path / 'bundle' and got == identity
                            else (_ for _ in ()).throw(AssertionError('alternate authority used'))
                        ) or types.SimpleNamespace(scope=types.SimpleNamespace(executors=(module.HERMES_EXECUTOR,))))
    saved_path, saved_argv = sys.path[:], sys.argv[:]
    try:
        assert module.bootstrap(['chat', '--profile', 'test'], bundle_path=tmp_path / 'bundle',
                                policy_code_root=LAUNCHER.parents[2],
                                hermes_root=hermes) == 0
    finally:
        sys.path[:] = saved_path
        sys.argv[:] = saved_argv
    assert events == ['verified', 'installed', 'main']


def test_launcher_requires_exact_pane_identity(monkeypatch, tmp_path):
    module = _launcher()
    monkeypatch.setattr(module, '_verify_hermes_build', lambda root: module.HERMES_EXECUTOR)
    hermes = tmp_path / 'hermes'
    (hermes / 'venv').mkdir(parents=True)
    (hermes / 'model_tools.py').write_text('')
    (hermes / 'hermes').write_text('')
    monkeypatch.delenv(module.IDENTITY_ENV['fencing_token'], raising=False)
    saved_path = sys.path[:]
    try:
        try:
            module.bootstrap([], bundle_path=tmp_path / 'bundle',
                             policy_code_root=LAUNCHER.parents[2], hermes_root=hermes)
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
    module._require_production_mount(trusted, exact=True)

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

    monkeypatch.setattr(module, "_require_production_mount", require)
    with pytest.raises(RuntimeError, match="stop-after-trust-roots"):
        module.bootstrap([])
    assert calls == [
        (module.BUNDLE_PATH, True),
        (module.POLICY_CODE_ROOT, False),
        (module.HERMES_ROOT, True),
        (module.PYTHON_ROOT, True),
    ]
