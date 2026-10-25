"""Canonical bootstrap transport wiring, with explicit no-exec SDK/trust ports.

These components exercise the real bootstrap ordering and module-origin checks.
They do not attest mounts, launch a CLI or authorize/model/budget operations.
"""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace, ModuleType
import sys

import pytest

from herdr import security, work_authority, work_contract_host
from tests.herdr.test_policy_bootstrap import _launcher, LAUNCHER
from tests.herdr.test_security import grant as grant_fixture


def wiring(monkeypatch, tmp_path, *, private=True, outcome=None, fault=None):
    module = _launcher()
    events, imports, created = [], [], []
    hermes = tmp_path / "hermes"
    hermes.mkdir()
    policy_root = LAUNCHER.parents[2]
    monkeypatch.setattr(module, "HERMES_ROOT", hermes)
    monkeypatch.setattr(module, "POLICY_CODE_ROOT", policy_root)
    monkeypatch.setattr(module, "BUNDLE_PATH", tmp_path / "bundle")
    monkeypatch.setattr(module, "_require_host_bootstrap_authority", lambda: events.append("authority"))
    proof = {"schema_version": "herdr-policy-bootstrap-2" if private else "herdr-policy-bootstrap-1"}
    monkeypatch.setattr(module, "_require_stage1_continuity", lambda: proof)
    monkeypatch.setattr(module, "_require_production_mount", lambda *a, **kw: None)
    monkeypatch.setattr(module, "_verify_runtime", lambda root: None)
    monkeypatch.setattr(module, "_verify_hermes_build", lambda root: module.HERMES_EXECUTOR)
    monkeypatch.setattr(module, "_reset_import_path", lambda *args: None)
    monkeypatch.setattr(module, "_configure_ephemeral_sdk_state", lambda root: events.append("sdk-state"))
    policy = SimpleNamespace(display={"cli_multiline_shortcuts": False}) if private else None
    failure = RuntimeError("unit-only boundary failure")
    def verify_policy(got, args):
        assert got is proof and args == ["chat", "--profile", "approved"]
        events.append("verified-policy")
        if fault == "verification": raise failure
        return policy
    monkeypatch.setattr(module, "_verified_private_sdk_policy", verify_policy)
    grant = grant_fixture(tmp_path)
    grant = replace(grant, scope=replace(grant.scope, executors=(module.HERMES_EXECUTOR,)))
    for name, env_name in module.IDENTITY_ENV.items():
        monkeypatch.setenv(env_name, str(getattr(grant.identity, name)))
    monkeypatch.setattr(security, "load_policy_bundle",
                        lambda root, identity: grant if identity == grant.identity else pytest.fail("identity drift"))
    installed = []
    guard_module = ModuleType("herdr.hermes_guard")
    guard_module.__file__ = str(policy_root / "herdr/hermes_guard.py")
    def install_guard(guard, **kwargs):
        assert type(guard) is work_contract_host.WorkInvocationGuard
        assert type(guard.work_authority) is work_authority.WorkAuthorityClient
        assert guard.grant is grant
        assert kwargs == ({"private_sdk_policy": policy} if private else {})
        events.append("guard-installed")
        if fault == "guard": raise failure
        installed.append(guard)
    guard_module.install_hermes_guard = install_guard
    main_module = ModuleType("hermes_cli.main")
    main_path = hermes / "main.py"; main_path.write_text("")
    main_module.__file__ = str(main_path)
    cli_module = ModuleType("cli")
    cli_path = hermes / "cli.py"; cli_path.write_text("")
    cli_module.__file__ = str(cli_path)
    def initialize(instance):
        created.append(instance)
        events.append("cli-constructed")
    cli_type = type("HermesCLI", (), {"__module__": "cli", "__init__": initialize})
    cli_module.HermesCLI = cli_type
    original_init = cli_type.__init__
    transport_module = ModuleType("herdr.hermes_terminal_transport")
    transport_module.__file__ = str(policy_root / "herdr/hermes_terminal_transport.py")
    active = []
    @contextmanager
    def factory(got_cli, guard, *, private_sdk_policy):
        assert got_cli is cli_type and guard is installed[0] and private_sdk_policy is policy
        assert policy.display["cli_multiline_shortcuts"] is False
        assert events.index("guard-installed") < events.index("transport-import")
        assert sys.argv == [str(hermes / "hermes"), "chat", "--profile", "approved"]
        events.append("transport-enter")
        if fault == "factory": raise failure
        def scoped(instance, *args, **kwargs):
            assert active == [True]
            return original_init(instance, *args, **kwargs)
        cli_type.__init__ = scoped
        active.append(True)
        try:
            yield
        finally:
            active.clear()
            cli_type.__init__ = original_init
            events.append("transport-restored")
    transport_module.native_cli_transport_factory = factory
    @contextmanager
    def label():
        events.append("label-enter")
        try: yield
        finally: events.append("label-restored")
    monkeypatch.setattr(module, "_native_hermes_process_label", label)
    def main():
        assert installed and events.index("verified-policy") < events.index("guard-installed")
        if private:
            assert active == [True]
            cli_type()
        else:
            assert active == [] and cli_type.__init__ is original_init
        events.append("main")
        if isinstance(outcome, BaseException): raise outcome
        return outcome
    main_module.main = main
    modules = {"herdr.security": security, "herdr.hermes_guard": guard_module,
               "herdr.work_contract_host": work_contract_host,
               "herdr.work_authority": work_authority, "hermes_cli.main": main_module,
               "herdr.hermes_terminal_transport": transport_module, "cli": cli_module}
    def import_module(name):
        imports.append(name)
        if name in ("cli", "herdr.hermes_terminal_transport"):
            assert private and "guard-installed" in events
            events.append("cli-import" if name == "cli" else "transport-import")
        assert name in modules, name
        return modules[name]
    # Keep the global importlib implementation intact for pytest/other modules.
    monkeypatch.setattr(module, "importlib", SimpleNamespace(import_module=import_module))
    if fault in ("cli-origin", "transport-origin"):
        outside = tmp_path / "foreign.py"; outside.write_text("")
        modules["cli" if fault == "cli-origin" else "herdr.hermes_terminal_transport"].__file__ = str(outside)
    return SimpleNamespace(module=module, events=events, imports=imports, active=active,
        cli_type=cli_type, original_init=original_init, created=created, failure=failure)


@pytest.mark.parametrize("outcome,expected", [(None, 0), (7, 7)])
def test_private_bootstrap_scopes_factory_around_actual_main(monkeypatch, tmp_path, outcome, expected):
    case = wiring(monkeypatch, tmp_path, outcome=outcome)
    monkeypatch.setattr(sys, "argv", ["unit-bootstrap"])
    assert case.module.bootstrap(["chat", "--profile", "approved"]) == expected
    assert case.events.index("guard-installed") < case.events.index("transport-enter") < case.events.index("main")
    assert case.events[-2:] == ["transport-restored", "label-restored"]
    assert len(case.created) == 1 and case.active == []
    assert case.cli_type.__init__ is case.original_init


def test_exception_restores_factory_and_preserves_original(monkeypatch, tmp_path):
    original = ValueError("unit-only original SDK error")
    case = wiring(monkeypatch, tmp_path, outcome=original)
    monkeypatch.setattr(sys, "argv", ["unit-bootstrap"])
    with pytest.raises(ValueError) as caught:
        case.module.bootstrap(["chat", "--profile", "approved"])
    assert caught.value is original
    assert case.events[-2:] == ["transport-restored", "label-restored"]
    assert case.active == [] and case.cli_type.__init__ is case.original_init


def test_legacy_bootstrap_does_not_import_or_enter_transport(monkeypatch, tmp_path):
    case = wiring(monkeypatch, tmp_path, private=False)
    monkeypatch.setattr(sys, "argv", ["unit-bootstrap"])
    assert case.module.bootstrap(["chat", "--profile", "approved"]) == 0
    assert "cli" not in case.imports and "herdr.hermes_terminal_transport" not in case.imports
    assert "transport-enter" not in case.events and not case.created
    assert case.cli_type.__init__ is case.original_init


@pytest.mark.parametrize("fault", ["verification", "guard", "factory"])
def test_predelivery_failure_never_enters_main(monkeypatch, tmp_path, fault):
    case = wiring(monkeypatch, tmp_path, fault=fault)
    monkeypatch.setattr(sys, "argv", ["unit-bootstrap"])
    with pytest.raises(RuntimeError) as caught:
        case.module.bootstrap(["chat", "--profile", "approved"])
    assert caught.value is case.failure
    assert "main" not in case.events and not case.created and case.active == []
    assert case.cli_type.__init__ is case.original_init
    if fault != "factory":
        assert "herdr.hermes_terminal_transport" not in case.imports and "cli" not in case.imports


@pytest.mark.parametrize("fault,label", [
    ("cli-origin", "cli import escaped trusted root"),
    ("transport-origin", "herdr.hermes_terminal_transport import escaped trusted root"),
])
def test_untrusted_module_origin_denied_before_context_or_main(monkeypatch, tmp_path, fault, label):
    case = wiring(monkeypatch, tmp_path, fault=fault)
    monkeypatch.setattr(sys, "argv", ["unit-bootstrap"])
    with pytest.raises(SystemExit, match=label):
        case.module.bootstrap(["chat", "--profile", "approved"])
    assert "transport-enter" not in case.events and "main" not in case.events
    assert not case.created and case.cli_type.__init__ is case.original_init


def test_declared_overlay_main_line_remains_unique_and_exact():
    source = LAUNCHER.read_text()
    assert source.count("        result = hermes_main_module.main()\n") == 1
