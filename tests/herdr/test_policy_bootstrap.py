"""Offline same-interpreter bootstrap ordering and fixed production path tests."""
from __future__ import annotations
import importlib.machinery
import importlib.util
import subprocess
import sys
import types
from pathlib import Path

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
    monkeypatch.setattr(sys, 'argv', [str(LAUNCHER), '--grant', '/model/choice', '--key-fd', '3'])
    assert module.main() == 0
    assert seen == [['--grant', '/model/choice', '--key-fd', '3']]
    assert module.BUNDLE_PATH == Path('/run/herdr-policy/grant.bundle.json')


def test_policy_bin_hermes_invokes_guarded_launcher():
    assert POLICY_BIN.is_symlink()
    assert POLICY_BIN.resolve() == LAUNCHER
    result = subprocess.run([str(POLICY_BIN), '--version'], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode != 0
    assert 'security path is not on a dedicated read-only trust mount' in result.stdout


def test_same_process_guard_precedes_hermes_main(monkeypatch, tmp_path):
    module = _launcher()
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
    fake_guard.install_hermes_guard = lambda guard: events.append('installed')
    fake_guard.InvocationGuard = lambda grant: grant
    fake_main = types.ModuleType('hermes_cli.main')
    fake_main.__file__ = str(hermes / 'hermes')
    def main():
        assert events == ['verified', 'installed']
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
                        ) or object())
    monkeypatch.setattr(sys, 'prefix', str(hermes / 'venv'))
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
    hermes = tmp_path / 'hermes'
    (hermes / 'venv').mkdir(parents=True)
    (hermes / 'model_tools.py').write_text('')
    (hermes / 'hermes').write_text('')
    monkeypatch.setattr(sys, 'prefix', str(hermes / 'venv'))
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
