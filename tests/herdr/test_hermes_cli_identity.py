"""Offline proposal components; real guard data, no CLI startup/model/authority."""
from contextvars import copy_context
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import inspect
import json
import socket
import subprocess
import threading

import pytest
from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
from herdr.security import (InvocationGuard, InvocationIdentity, PolicyDenied,
    ProcessPolicy, RuntimeAssurance, SecurityGrant, NetworkAccess, ToolRule, RiskClass)
from herdr.hermes_cli_identity import CLIInvocationBinding

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def effects_forbidden(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("network/process forbidden in component")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    monkeypatch.setattr(socket.socket, "sendto", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(subprocess, "Popen", deny)


def guard(tmp_path, task="component-herdr-task", **changes):
    identity = InvocationIdentity("github:unit/repo", "agent", "parent-agent",
                                  "parent-task", task, "run-1", 1)
    identity = replace(identity, **changes)
    scope = CapabilityScope(
        providers=(), capabilities=("reasoning",), executors=("hermes-runtime",),
        tools=("read_file", "write_file"), permissions=("repo:read",),
        regions=("eu-central",), data_classes=(DataClass.PUBLIC,),
        input_modalities=("text",), output_modalities=("text",),
        max_cost_microusd=0, max_context_tokens=8192,
        max_egress=Egress.REGION_BOUND, max_retention=Retention.LIMITED,
        training=Training.EXCLUDED)
    rules = (ToolRule("read_file", RiskClass.READ, ("path", "offset", "limit"),
                      path_fields=("path",), allowed_roots=(str(tmp_path),)),
             ToolRule("write_file", RiskClass.WORKSPACE_WRITE, ("path", "content"),
                      path_fields=("path",), allowed_roots=(str(tmp_path),)))
    assurance = RuntimeAssurance(True, "a" * 64, NetworkAccess.NONE, (), True)
    grant = SecurityGrant(
        "unit-grant", str(tmp_path), identity, scope, rules,
        ProcessPolicy(False, (), NetworkAccess.NONE), assurance, (), (), (), (),
        "2026-01-01T00:00:00+00:00", "2030-01-01T00:00:00+00:00")
    return InvocationGuard(grant)


def fixture_types():
    class AIAgent:
        def __init__(self, session):
            self.session_id = session
            self.callback = lambda agent, task_id: task_id
        def run_conversation(self, user_message, system_message=None, conversation_history=None,
                             task_id=None, stream_callback=None, *, relay_metadata=None):
            return self.callback(self, task_id), {
                "user_message": user_message, "system_message": system_message,
                "conversation_history": conversation_history, "task_id": task_id,
                "stream_callback": stream_callback, "relay_metadata": relay_metadata}
    class HermesCLI:
        def __init__(self, session="sdk-session"):
            self.session_id = session
            self.agent = None
    HermesCLI.__module__ = "cli"
    AIAgent.__module__ = "run_agent"
    return HermesCLI, AIAgent


def prepare(binding, cli_type, agent_type, session="sdk-session"):
    cli = cli_type(session)
    agent = agent_type(session)
    cli.agent = agent
    def authorize(agent, task_id):
        token = binding.begin_tool(agent, task_id)
        try:
            return binding.caller_task_id(task_id)
        finally:
            binding.end_tool(token)
    agent.callback = authorize
    return cli, agent


@pytest.mark.parametrize("task,changes", [
    ("root-task", {"parent_task_id": "root-task", "parent_agent_id": "root-agent"}),
    ("child-task", {"parent_task_id": "root-task", "parent_agent_id": "root-agent"}),
    ("recovered-task", {"run_token": "recovered-run", "fencing_token": 19}),
])
def test_original_sdk_arguments_and_session_unchanged_only_guard_id_maps(tmp_path, task, changes):
    item = guard(tmp_path, task, **changes)
    binding = CLIInvocationBinding(item)
    cli_type, agent_type = fixture_types()
    original_init, original_run = cli_type.__init__, agent_type.run_conversation
    original_signature = inspect.signature(original_run)
    marker = object()
    with binding.factory(cli_type, agent_type):
        cli, agent = prepare(binding, cli_type, agent_type)
        assert agent_type.run_conversation.__wrapped__ is original_run
        assert inspect.signature(agent_type.run_conversation) == original_signature
        result, args = agent.run_conversation(marker, "system", [marker], "sdk-session",
            marker, relay_metadata=marker)
        assert result == task
        assert args == dict(user_message=marker, system_message="system",
            conversation_history=[marker], task_id="sdk-session",
            stream_callback=marker, relay_metadata=marker)
        assert cli.session_id == agent.session_id == "sdk-session"
    assert cli_type.__init__ is original_init and agent_type.run_conversation is original_run


@pytest.mark.parametrize("foreign", ("foreign", None, "component-herdr-task", ""))
def test_input_task_id_cannot_create_an_alias(tmp_path, foreign):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        _, agent = prepare(binding, cli_type, agent_type)
        with pytest.raises(PolicyDenied, match="task_mismatch"):
            agent.run_conversation("message", task_id=foreign)


def test_unbound_or_cross_agent_never_acquires_turn(tmp_path):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        cli, _ = prepare(binding, cli_type, agent_type)
        foreign = agent_type(cli.session_id)
        with pytest.raises(PolicyDenied, match="agent_unbound"):
            foreign.run_conversation("message", task_id=cli.session_id)
        with pytest.raises(PolicyDenied, match="tool_outside_turn"):
            binding.begin_tool(foreign, cli.session_id)


def test_session_rotation_and_agent_reinit_between_turns_preserve_sdk_semantics(tmp_path):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        cli, old = prepare(binding, cli_type, agent_type)
        assert old.run_conversation("first", task_id=old.session_id)[0] == "component-herdr-task"
        cli.session_id = "sdk-rotated"
        new = agent_type(cli.session_id)
        cli.agent = new
        new.callback = old.callback
        with pytest.raises(PolicyDenied, match="agent_unbound"):
            old.run_conversation("stale", task_id=old.session_id)
        assert new.run_conversation("next", task_id=new.session_id)[0] == "component-herdr-task"


@pytest.mark.parametrize("change", ("cli-session", "agent-session", "agent", "grant", "close"))
def test_change_inside_turn_denies_before_authorization(tmp_path, change):
    item = guard(tmp_path)
    binding = CLIInvocationBinding(item)
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        cli, agent = prepare(binding, cli_type, agent_type)
        def callback(agent, task_id):
            token = binding.begin_tool(agent, task_id)
            try:
                if change == "cli-session": cli.session_id = "changed"
                elif change == "agent-session": agent.session_id = "changed"
                elif change == "agent": cli.agent = agent_type(cli.session_id)
                elif change == "grant": item.grant = replace(item.grant, grant_id="new-grant")
                else: binding.close()
                with pytest.raises(PolicyDenied):
                    binding.caller_task_id(task_id)
                return "denied"
            finally:
                binding.end_tool(token)
        agent.callback = callback
        assert agent.run_conversation("message", task_id="sdk-session")[0] == "denied"


def test_copied_old_worker_context_cannot_attach_to_later_same_session_turn(tmp_path):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        cli, agent = prepare(binding, cli_type, agent_type)
        retained = []
        def first(agent, task_id):
            retained.append(copy_context())
            return "captured"
        agent.callback = first
        agent.run_conversation("first", task_id=cli.session_id)
        with pytest.raises(PolicyDenied, match="tool_outside_turn"):
            retained[0].run(binding.begin_tool, agent, cli.session_id)
        def next_turn(agent, task_id):
            with pytest.raises(PolicyDenied, match="tool_outside_turn"):
                retained[0].run(binding.begin_tool, agent, task_id)
            return "stale denied"
        agent.callback = next_turn
        assert agent.run_conversation("next", task_id=cli.session_id)[0] == "stale denied"


def test_parallel_copied_workers_and_nested_registry_resolution_only_while_turn_live(tmp_path):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        cli, agent = prepare(binding, cli_type, agent_type)
        def run(agent, task_id):
            results, errors = [], []
            def worker():
                try:
                    token = binding.begin_tool(agent, task_id)
                    try:
                        results.append((binding.caller_task_id(task_id),
                            binding.caller_task_id(None),
                            binding.path_task_id("component-herdr-task")))
                    finally:
                        binding.end_tool(token)
                except BaseException as error: errors.append(type(error).__name__)
            threads = [threading.Thread(target=copy_context().run, args=(worker,)) for _ in range(2)]
            for thread in threads: thread.start()
            for thread in threads: thread.join(2)
            assert not errors and len(results) == 2
            assert results == [("component-herdr-task", "component-herdr-task", "sdk-session")] * 2
            return "both allowed"
        agent.callback = run
        assert agent.run_conversation("message", task_id=cli.session_id)[0] == "both allowed"
    with pytest.raises(PolicyDenied):
        binding.caller_task_id(cli.session_id)


def test_overlapping_turn_or_factory_denies(tmp_path):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        cli, agent = prepare(binding, cli_type, agent_type)
        def callback(agent, task_id):
            with pytest.raises(PolicyDenied, match="turn_overlap"):
                with binding.turn(agent, task_id): pass
            return "denied nested"
        agent.callback = callback
        assert agent.run_conversation("message", task_id=cli.session_id)[0] == "denied nested"
        other = CLIInvocationBinding(binding.guard)
        with pytest.raises(PolicyDenied, match="factory_overlap"):
            with other.factory(cli_type, agent_type): pass


def test_later_owner_not_overwritten_on_uninstall(tmp_path):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    original = cli_type.__init__
    later = lambda self, *args, **kwargs: None
    with pytest.raises(PolicyDenied, match="factory_owner_changed"):
        with binding.factory(cli_type, agent_type):
            cli_type.__init__ = later
    assert cli_type.__init__ is later
    cli_type.__init__ = original


def test_expired_same_grant_and_installation_close_revoke_copied_context(tmp_path, monkeypatch):
    item = guard(tmp_path)
    binding = CLIInvocationBinding(item)
    cli_type, agent_type = fixture_types()
    with binding.factory(cli_type, agent_type):
        cli, agent = prepare(binding, cli_type, agent_type)
        def callback(agent, task_id):
            token = binding.begin_tool(agent, task_id)
            try:
                monkeypatch.setattr(type(item.grant), "is_active", lambda self: False)
                with pytest.raises(PolicyDenied, match="grant_changed"):
                    binding.caller_task_id(task_id)
                return "denied expired"
            finally: binding.end_tool(token)
        agent.callback = callback
        assert agent.run_conversation("message", task_id=cli.session_id)[0] == "denied expired"


@pytest.mark.parametrize("sealed,args,expected", [
    (True, ["-p", "approved", "chat"], True),
    (True, ["--profile", "approved", "chat", "--continue", "name"], True),
    (False, ["-p", "approved", "chat"], False),
    (True, ["-p", "approved", "--version"], False),
    (True, ["-p", "approved", "gateway"], False),
    (True, ["-p", "approved", "acp"], False),
    (True, ["chat"], False),
    (False, [], False),
])
def test_authenticated_private_ordinary_cli_lane_only(sealed, args, expected):
    import ast
    path = REPO / "agent-stack/bin/agent-hermes-policy-run"
    tree = ast.parse(path.read_text())
    bootstrap = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "bootstrap")
    value = next(n.value for n in bootstrap.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "use_cli_identity" for t in n.targets))
    expression = ast.Expression(value)
    assert eval(compile(ast.fix_missing_locations(expression), "<closed-lane-component>", "eval"),
                {"private_sdk_policy": object() if sealed else None,
                 "hermes_args": args}) is expected


def test_invalid_sdk_signature_does_not_hold_global_factory_lock(tmp_path):
    binding = CLIInvocationBinding(guard(tmp_path))
    cli_type, agent_type = fixture_types()
    original = agent_type.run_conversation
    original.__signature__ = object()
    try:
        with pytest.raises(TypeError):
            with binding.factory(cli_type, agent_type): pass
    finally:
        del original.__signature__
    with binding.factory(cli_type, agent_type):
        cli, agent = prepare(binding, cli_type, agent_type)
        assert agent.run_conversation("valid", task_id=cli.session_id)[0] == "component-herdr-task"


@pytest.mark.parametrize("primary_failure", (False, True))
def test_native_factory_then_identity_factory_constructs_once_and_restores_both(
        monkeypatch, tmp_path, primary_failure):
    from herdr import hermes_terminal_transport as transport
    from test_hermes_terminal_transport import (
        constructor_fixture, attach_created, paste, enter)
    ui, cli_type, base_constructor = constructor_fixture(monkeypatch, tmp_path)
    _, agent_type = fixture_types()
    def original_constructor(instance):
        base_constructor(instance)
        instance.session_id = "sdk-constructor-session"
        instance.agent = None
    cli_type.__init__ = original_constructor
    original_run = agent_type.run_conversation
    original_chat = cli_type.chat
    binding = CLIInvocationBinding(ui.guard)
    failure = ValueError("unit primary")
    instance = handle = None
    try:
        with transport.native_cli_transport_factory(
                cli_type, ui.guard, private_sdk_policy=ui.policy):
            native_constructor = cli_type.__init__
            with binding.factory(cli_type, agent_type):
                instance = cli_type()
                assert ui.constructed == [instance]
                attach_created(ui, instance)
                handle = ui.handle
                instance.agent = agent_type(instance.session_id)
                def callback(agent, task_id):
                    token = binding.begin_tool(agent, task_id)
                    try: return binding.caller_task_id(task_id)
                    finally: binding.end_tool(token)
                instance.agent.callback = callback
                assert instance.agent.run_conversation(
                    "unit", task_id=instance.session_id)[0] == ui.guard.grant.identity.task_id
                assert cli_type.chat is original_chat
                paste(ui, "unit constructor prompt")
                enter(ui)
                if primary_failure:
                    raise failure
                ui.loop.flush()
                assert instance._pending_input.get_nowait() == "unit constructor prompt"
                assert len(ui.calls) == 1
            assert cli_type.__init__ is native_constructor
    except ValueError as error:
        assert primary_failure and error is failure
    assert cli_type.__init__ is original_constructor
    assert agent_type.run_conversation is original_run
    assert handle is not None and not handle._installed
    ui.loop.flush()
    assert instance._pending_input.empty()
