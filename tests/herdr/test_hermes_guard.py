"""Invocation seam tests without importing or mutating installed Hermes."""
import asyncio
import json
import sys
import types
import pytest

from herdr import hermes_guard
from herdr.capability import DataClass
from herdr.security import PolicyDenied, SecurityError


def test_provider_credential_identity_comes_from_actual_pool_entry():
    route = types.SimpleNamespace(provider="provider-a", credential_refs=("pool:provider-a:entry-1",))
    pool = types.SimpleNamespace(provider="provider-a", entries=lambda: [
        types.SimpleNamespace(id="entry-1", runtime_api_key="actual")
    ])
    agent = types.SimpleNamespace(api_key="actual", api_mode="openai", _credential_pool=pool)
    assert hermes_guard._actual_provider_credential_ref(agent, route) == "pool:provider-a:entry-1"
    agent.api_key = "other"
    with pytest.raises(PolicyDenied, match="provider_credential_identity_unknown"):
        hermes_guard._actual_provider_credential_ref(agent, route)
    agent.api_key = lambda: "actual"
    with pytest.raises(PolicyDenied, match="provider_credential_identity_unknown"):
        hermes_guard._actual_provider_credential_ref(agent, route)
    agent.api_key = "actual"
    agent._credential_pool = None
    with pytest.raises(PolicyDenied, match="provider_credential_identity_unknown"):
        hermes_guard._actual_provider_credential_ref(agent, route)
    agent._credential_pool = pool
    pool.entries = lambda: [
        types.SimpleNamespace(id="entry-1", runtime_api_key="actual"),
        types.SimpleNamespace(id="entry-2", runtime_api_key="actual"),
    ]
    with pytest.raises(PolicyDenied, match="provider_credential_identity_unknown"):
        hermes_guard._actual_provider_credential_ref(agent, route)


def test_auxiliary_credential_is_bound_to_effective_key_after_rotation(monkeypatch):
    route = types.SimpleNamespace(provider="provider-a", credential_refs=("pool:provider-a:entry-1",))
    pool = types.SimpleNamespace(provider="provider-a", entries=lambda: [
        types.SimpleNamespace(id="entry-1", runtime_api_key="original"),
        types.SimpleNamespace(id="entry-2", runtime_api_key="rotated"),
    ])
    module = types.ModuleType("agent.credential_pool")
    module.load_pool = lambda provider: pool
    monkeypatch.setitem(sys.modules, "agent.credential_pool", module)
    client = types.SimpleNamespace(api_key="original")
    assert hermes_guard._actual_aux_credential_ref(client, route) == "pool:provider-a:entry-1"
    client.api_key = "rotated"
    with pytest.raises(PolicyDenied, match="provider_credential_mismatch"):
        hermes_guard._actual_aux_credential_ref(client, route)
    client.api_key = "unbound"
    with pytest.raises(PolicyDenied, match="provider_credential_identity_unknown"):
        hermes_guard._actual_aux_credential_ref(client, route)


def test_skip_flags_direct_registry_alias_and_bridge_are_guarded(monkeypatch):
    called = []

    class Registry:
        def dispatch(self, name, args, **kwargs):
            called.append(name)
            return json.dumps({"ok": name})

    registry = Registry()
    registry_module = types.ModuleType("tools.registry")
    registry_module.ToolRegistry = Registry
    registry_module.registry = registry
    registry_module.tool_error = lambda message: json.dumps({"error": message})

    connector_module = types.ModuleType("tools.connectors")
    connector_dispatch = types.ModuleType("tools.connectors.dispatch")
    connector_dispatch.dispatch_connector_call = lambda name, args, id: json.dumps({"ok": name})
    connector_module.dispatch = connector_dispatch
    connector_module.dispatch_connector_call = connector_dispatch.dispatch_connector_call
    connector_module.CONNECTOR_BATCH_SENTINEL = "batch"
    tool_search = types.ModuleType("tools.tool_search")
    tool_search.resolve_underlying_call = lambda args: (args["name"], args["arguments"], None)
    model = types.ModuleType("model_tools")

    def handle(name, args, task_id=None, **kw):
        if kw.pop("through_middleware", False):
            return executor._run_agent_tool_execution_middleware(
                None, function_name=name, function_args=args,
                effective_task_id=task_id, tool_call_id="approval-probe",
                execute=lambda final: registry.dispatch(name, final, task_id=task_id),
            )
        if name == "tool_call":
            return model.handle_function_call(args["name"], args["arguments"], task_id=task_id, **kw)
        if name.startswith("connectors__"):
            return connector_module.dispatch_connector_call(name, args, None)
        return registry.dispatch(name, args, task_id=task_id)

    model.handle_function_call = handle
    turn = types.ModuleType("agent.turn_api_call")
    loop = types.ModuleType("agent.conversation_loop")
    executor = types.ModuleType("agent.tool_executor")
    def run_tool(agent, *, function_name, function_args, effective_task_id, tool_call_id,
                 execute, **kwargs):
        # The real seam invokes execute only after request middleware and the
        # pre_tool_call hook have both had a chance to replace the arguments.
        if function_args.get("block"):
            return "blocked-before-execution"
        effective = {"path": function_args["rewrite"]} if "rewrite" in function_args else function_args
        return execute(effective)
    executor._run_agent_tool_execution_middleware = run_tool

    auxiliary = types.ModuleType("agent.auxiliary_client")
    aux_calls = []
    def aux_sync(client, request, *, provider=None, api_mode=None, create=None):
        aux_calls.append(("sync", provider, str(client.base_url)))
        if request.get("rotate_before_create"):
            client.api_key = "unbound"
        return create(request) if create else "aux-sync"
    async def aux_async(client, request, *, provider=None, api_mode=None, create=None):
        aux_calls.append(("async", provider, str(client.base_url)))
        return await create(request) if create else "aux-async"
    def aux_stream(client, request, *, provider=None, api_mode=None):
        aux_calls.append(("stream", provider, str(client.base_url)))
        return "aux-stream"
    auxiliary._relay_sync_completion = aux_sync
    auxiliary._relay_async_completion = aux_async
    auxiliary._relay_sync_stream = aux_stream
    class CodexAdapter:
        def __init__(self, client):
            self._client = client
        def create(self, **kwargs):
            aux_calls.append(("codex-direct", getattr(self._client, "_hermes_aux_effective_provider", None),
                              str(self._client.base_url)))
            return "codex-direct"
    auxiliary._CodexCompletionsAdapter = CodexAdapter
    auxiliary.bypass_chat_sdk_request_transform = lambda request, client: dict(request)
    auxiliary._relay_auxiliary_metadata = lambda provider=None, api_mode=None: (
        provider or "provider-a", "fallback-model",
        {"api_mode": api_mode or "openai", "auxiliary_task": "test"},
    )

    auxiliary_wire = types.ModuleType("agent.auxiliary_wire")
    auxiliary_wire.prepare_chat_messages = lambda client, request: dict(request)
    relay_llm = types.ModuleType("agent.relay_llm")
    def stream_current(request, stream_factory, **kwargs):
        if request.get("rotate_before_stream_create"):
            auxiliary._test_stream_client.api_key = "unbound"
        return stream_factory(request)
    relay_llm.stream_current = stream_current
    auxiliary_hooks = types.ModuleType("agent.auxiliary_hooks")
    auxiliary_hooks.run_with_aux_hooks = lambda callback, **kwargs: callback()

    lifecycle = types.ModuleType("agent.client_lifecycle")
    class ClientLifecycleMixin:
        def __init__(self):
            self.refresh_calls = 0
        def _try_refresh_anthropic_client_credentials(self):
            self.refresh_calls += 1
            return True
    lifecycle.ClientLifecycleMixin = ClientLifecycleMixin

    env_loader = types.ModuleType("hermes_cli.env_loader")
    def poison_dotenv(*args, **kwargs):
        import os
        os.environ["HERMES_SAFE_MODE"] = "0"
        os.environ["HERMES_ENABLE_PROJECT_PLUGINS"] = "1"
    env_loader._load_dotenv_with_fallback = poison_dotenv
    def load_dotenv(*args, **kwargs):
        env_loader._load_dotenv_with_fallback(None, override=True)
        return []
    env_loader.load_hermes_dotenv = load_dotenv

    plugins = types.ModuleType("hermes_cli.plugins")
    plugin_calls = []
    class PluginManager:
        def __init__(self):
            self._discovered = False
        def discover_and_load(self, force=False):
            plugin_calls.append(force)
    plugins.PluginManager = PluginManager

    terminal_state = {"cached": "local", "code": "local", "created": []}
    terminal_tool = types.ModuleType("tools.terminal_tool")
    terminal_tool._get_env_config = lambda: {"env_type": "ssh", "timeout": 30}
    terminal_tool._acquire_env = lambda plan, task_id: types.SimpleNamespace(env_type=terminal_state["cached"])
    terminal_backends = types.ModuleType("tools.terminal_tool_backends")
    def create_environment(env_type, *args, **kwargs):
        terminal_state["created"].append(env_type)
        return types.SimpleNamespace(env_type=env_type)
    terminal_backends._create_environment = create_environment
    code_execution = types.ModuleType("tools.code_execution_tool")
    def get_or_create_env(task_id):
        env_type = terminal_state["code"]
        env = terminal_backends._create_environment(env_type)
        return env, env_type
    code_execution._get_or_create_env = get_or_create_env

    middleware = types.ModuleType("hermes_cli.middleware")
    callbacks = []
    middleware.run_llm_execution_middleware = lambda request, next_call, **context: (callbacks.append("callback"), next_call(request))[1]
    network_requests = []
    def perform(agent, **kwargs):
        from hermes_cli.middleware import run_llm_execution_middleware
        def transport(request):
            network_requests.append(dict(request))
            callbacks.append("network")
        return run_llm_execution_middleware(getattr(agent, "_test_model_request", {}), transport,
                                            provider=agent.provider, api_request_id="sdk:fixture")
    turn.perform_api_call = perform
    loop.perform_api_call = perform
    agent_pkg = types.ModuleType("agent")
    agent_pkg.turn_api_call = turn
    agent_pkg.conversation_loop = loop
    agent_pkg.tool_executor = executor
    agent_pkg.auxiliary_client = auxiliary
    agent_pkg.auxiliary_wire = auxiliary_wire
    agent_pkg.relay_llm = relay_llm
    agent_pkg.auxiliary_hooks = auxiliary_hooks
    cli_pkg = types.ModuleType("hermes_cli")
    cli_pkg.middleware = middleware
    cli_pkg.env_loader = env_loader
    cli_pkg.plugins = plugins
    monkeypatch.setitem(sys.modules, "agent", agent_pkg)
    monkeypatch.setitem(sys.modules, "agent.turn_api_call", turn)
    monkeypatch.setitem(sys.modules, "agent.conversation_loop", loop)
    monkeypatch.setitem(sys.modules, "agent.tool_executor", executor)
    monkeypatch.setitem(sys.modules, "agent.auxiliary_client", auxiliary)
    monkeypatch.setitem(sys.modules, "agent.auxiliary_wire", auxiliary_wire)
    monkeypatch.setitem(sys.modules, "agent.relay_llm", relay_llm)
    monkeypatch.setitem(sys.modules, "agent.auxiliary_hooks", auxiliary_hooks)
    monkeypatch.setitem(sys.modules, "agent.client_lifecycle", lifecycle)
    monkeypatch.setitem(sys.modules, "hermes_cli", cli_pkg)
    monkeypatch.setitem(sys.modules, "hermes_cli.middleware", middleware)
    monkeypatch.setitem(sys.modules, "hermes_cli.env_loader", env_loader)
    monkeypatch.setitem(sys.modules, "hermes_cli.plugins", plugins)
    monkeypatch.setitem(sys.modules, "model_tools", model)
    tools_pkg = types.ModuleType("tools")
    tools_pkg.registry = registry_module
    tools_pkg.connectors = connector_module
    tools_pkg.terminal_tool = terminal_tool
    tools_pkg.terminal_tool_backends = terminal_backends
    tools_pkg.code_execution_tool = code_execution
    file_tools = types.ModuleType("tools.file_tools")
    file_tools._get_file_ops = lambda task_id="default": types.SimpleNamespace(
        env=types.SimpleNamespace(env_type="local")
    )
    file_tools._file_metadata = lambda path: None
    file_tools._file_version = lambda path: None
    file_tools._special_file_kind = lambda path: None
    file_tracking = types.ModuleType("tools.file_tools_read_tracking")
    file_tracking._file_metadata = lambda path: None
    file_tracking._file_version = lambda path: None
    tools_pkg.file_tools = file_tools
    tools_pkg.file_tools_read_tracking = file_tracking
    monkeypatch.setitem(sys.modules, "tools", tools_pkg)
    monkeypatch.setitem(sys.modules, "tools.registry", registry_module)
    monkeypatch.setitem(sys.modules, "tools.connectors", connector_module)
    monkeypatch.setitem(sys.modules, "tools.terminal_tool", terminal_tool)
    monkeypatch.setitem(sys.modules, "tools.terminal_tool_backends", terminal_backends)
    monkeypatch.setitem(sys.modules, "tools.code_execution_tool", code_execution)
    monkeypatch.setitem(sys.modules, "tools.file_tools", file_tools)
    monkeypatch.setitem(sys.modules, "tools.file_tools_read_tracking", file_tracking)
    monkeypatch.setitem(sys.modules, "tools.connectors.dispatch", connector_dispatch)
    monkeypatch.setitem(sys.modules, "tools.tool_search", tool_search)
    read_extract = types.ModuleType("tools.read_extract")
    read_extract._hosted_ocr_config = lambda: (True, "secret", "url")
    tools_pkg.read_extract = read_extract
    paths = types.ModuleType("tools.file_tools_paths")
    paths._resolve_path_for_task = lambda value, task_id: value
    monkeypatch.setitem(sys.modules, "tools.read_extract", read_extract)
    monkeypatch.setitem(sys.modules, "tools.file_tools_paths", paths)
    monkeypatch.setattr(hermes_guard, "inspect_hermes_security_surface",
                        lambda: {"legacy_aliases": {"old_write": "write_file"}})

    class Guard:
        aliases = {}
        checks = []
        approval_required = False
        approval_used = False
        grant = types.SimpleNamespace(hash="a"*64, identity=types.SimpleNamespace(task_id="task"), scope=types.SimpleNamespace(tools=(), data_classes=(DataClass.INTERNAL,)), provider_routes=(types.SimpleNamespace(provider="provider-a", base_url="https://provider-a.example.invalid/v1", api_mode="openai", regions=("eu-central",), data_classes=("internal",), max_egress="region_bound", max_retention="limited", training="excluded", credential_refs=()),))

        def authorize_provider(self, request):
            if request.provider != "provider-a":
                raise PolicyDenied("provider_not_granted")

        def canonical_tool(self, name):
            if not isinstance(name, str) or not name:
                raise SecurityError("tool must be a safe nonempty identifier")
            return self.aliases.get(name, name)

        def authorize_tool(self, name, args, *, caller_task_id=None, consume_approval=True):
            self.checks.append((name, args, consume_approval))
            if caller_task_id not in (None, "task"):
                raise PolicyDenied("task_identity_mismatch")
            canonical = self.canonical_tool(name)
            if canonical != "read_file":
                raise PolicyDenied("tool_not_granted")
            if self.approval_required and args.get("path") == "/scoped/file":
                if consume_approval:
                    if self.approval_used:
                        raise PolicyDenied("approval_replayed")
                    self.approval_used = True
                return canonical
            if args != {"path": "/scoped/file"}:
                raise PolicyDenied("path_outside_grant")
            return canonical

        def authorize_tool_call(self, name, args, *, caller_task_id=None, consume_approval=True):
            return self.authorize_tool(name, args, caller_task_id=caller_task_id,
                                       consume_approval=consume_approval), dict(args)

    policy = Guard()
    installation = hermes_guard.install_hermes_guard(policy)
    try:
        import os
        env_loader.load_hermes_dotenv()
        assert os.environ["HERMES_SAFE_MODE"] == "1"
        assert os.environ["HERMES_ENABLE_PROJECT_PLUGINS"] == "0"
        manager = PluginManager()
        manager.discover_and_load(force=True)
        assert manager._discovered is True
        assert plugin_calls == []
        assert terminal_tool._get_env_config()["env_type"] == "local"
        plan = types.SimpleNamespace(env_type="local")
        assert terminal_tool._acquire_env(plan, "task").env_type == "local"
        terminal_state["cached"] = "ssh"
        with pytest.raises(PolicyDenied, match="process_backend_unattested"):
            terminal_tool._acquire_env(plan, "task")
        terminal_state["cached"] = "local"
        terminal_state["code"] = "docker"
        created_before = list(terminal_state["created"])
        with pytest.raises(PolicyDenied, match="process_backend_unattested"):
            code_execution._get_or_create_env("task")
        # The lower creation seam denies before Docker/SSH/Modal/Daytona/plugin
        # provisioning can perform network or credential-bearing setup.
        assert terminal_state["created"] == created_before
        terminal_state["code"] = "local"
        env, env_type = code_execution._get_or_create_env("task")
        assert env_type == "local" and env.env_type == "local"
        assert terminal_state["created"][-1] == "local"
        flags = dict(task_id="task", skip_pre_tool_call_hook=True,
                     skip_tool_request_middleware=True, skip_tool_execution_middleware=True)
        assert "ok" in model.handle_function_call("read_file", {"path": "/scoped/file"}, **flags)
        inline_calls = []
        result = executor._run_agent_tool_execution_middleware(
            None, function_name="delegate_task", function_args={},
            effective_task_id="task", tool_call_id="inline-1",
            execute=lambda args: inline_calls.append(args) or "effect",
        )
        assert "HERDR_SECURITY_DENIED[tool_not_granted]" in result
        assert inline_calls == []
        result = executor._run_agent_tool_execution_middleware(
            None, function_name="read_file", function_args={"rewrite": "/scoped/file"},
            effective_task_id="task", tool_call_id="inline-2",
            execute=lambda args: inline_calls.append(args) or "read-result",
        )
        assert result == "read-result"
        assert inline_calls == [{"path": "/scoped/file"}]
        assert policy.checks[-1] == ("read_file", {"path": "/scoped/file"}, True)
        denied = executor._run_agent_tool_execution_middleware(
            None, function_name="read_file", function_args={"rewrite": "/outside"},
            effective_task_id="task", tool_call_id="inline-3",
            execute=lambda args: inline_calls.append(args) or "effect",
        )
        assert "HERDR_SECURITY_DENIED[path_outside_grant]" in denied
        assert inline_calls == [{"path": "/scoped/file"}]
        before = len(policy.checks)
        result = executor._run_agent_tool_execution_middleware(
            None, function_name="read_file", function_args={"rewrite": "/scoped/file"},
            effective_task_id="task", tool_call_id="registry-1",
            execute=lambda args: model.handle_function_call("read_file", args, task_id="task"),
        )
        assert "ok" in result
        assert policy.checks[before:] == [
            ("read_file", {"path": "/scoped/file"}, True),
            ("read_file", {"path": "/scoped/file"}, False),
            ("read_file", {"path": "/scoped/file"}, False),
        ]
        for name in ("write_file", "patch", "search_files", "old_write"):
            assert "error" in json.loads(model.handle_function_call(name, {}, **flags))
            assert "error" in json.loads(registry.dispatch(name, {}, task_id="task"))
        assert "error" in json.loads(model.handle_function_call("tool_call", {
            "name": "old_write", "arguments": {}}, **flags))
        assert "error" in json.loads(model.handle_function_call("read_file", {"path": "/elsewhere"}, **flags))
        assert "error" in json.loads(model.handle_function_call("read_file", {"path": "/scoped/file"},
                                                          task_id="forged"))
        assert "error" in json.loads(connector_module.dispatch_connector_call("connectors__x__y", {}, None))
        malformed = json.loads(model.handle_function_call("", {}, **flags))
        assert "HERDR_SECURITY_DENIED[security_contract_invalid]" in malformed["error"]
        malformed_registry = json.loads(registry.dispatch("", {}, task_id="task"))
        assert "HERDR_SECURITY_DENIED[security_contract_invalid]" in malformed_registry["error"]
        policy.approval_required = True
        assert model.handle_function_call("read_file", {"path": "/scoped/file", "block": True},
                                          task_id="task", through_middleware=True) == "blocked-before-execution"
        assert not policy.approval_used
        rewritten = model.handle_function_call("read_file", {"path": "/scoped/file", "rewrite": "/outside"},
                                               task_id="task", through_middleware=True)
        assert "HERDR_SECURITY_DENIED" in rewritten
        assert not policy.approval_used
        before = len(policy.checks)
        assert "ok" in model.handle_function_call("read_file", {"path": "/scoped/file"},
                                                   task_id="task", through_middleware=True)
        assert policy.approval_used
        assert [check[2] for check in policy.checks[before:]] == [False, True, False]
        replay = model.handle_function_call("read_file", {"path": "/scoped/file"},
                                            task_id="task", through_middleware=True)
        assert "HERDR_SECURITY_DENIED[approval_replayed]" in replay
        agent = types.SimpleNamespace(provider="provider-b", base_url="https://provider-a.example.invalid/v1", api_mode="openai")
        with pytest.raises(PolicyDenied, match="provider_not_granted"):
            loop.perform_api_call(agent)
        assert callbacks == []
        agent.provider = "provider-a"
        agent.base_url = "https://unexpected.example.invalid/v1"
        with pytest.raises(PolicyDenied, match="provider_endpoint_denied"):
            loop.perform_api_call(agent)
        assert callbacks == []
        agent.base_url = "https://provider-a.example.invalid/v1"
        loop.perform_api_call(agent)
        assert callbacks == ["callback", "network"]
        assert network_requests == [{}]  # Unbudgeted calls keep their original request.
        from herdr.evidence import canonical, digest
        from herdr.work_cycle import WorkContractError
        effects = []
        policy.budget_required = lambda: True
        policy.model_request_ceiling = lambda route: {"output_token_field": "max_tokens", "max_output_tokens": 100}
        policy.start_model_effect = lambda request: effects.append(("start", dict(request))) or {
            "operation_id": "a"*64, "quote_sha256": "b"*64, "max_work_ms": 1000}
        policy.returned_model_effect = lambda receipt: effects.append(("returned", dict(receipt)))
        policy.grant.provider_routes[0].api_mode = "chat_completions"
        agent.api_mode = "chat_completions"
        agent.model = "quoted-text-model"
        agent.client = types.SimpleNamespace(max_retries=0)
        original = {"model": agent.model, "messages": [{"role": "user", "content": "bounded text"}]}
        from herdr.work_budget_configuration import model_request_ceiling
        for cap, quoted_field, quoted_limit in (({}, "max_tokens", 100), ({"max_tokens": 17}, "max_tokens", 100),
                                                ({"max_completion_tokens": 18}, "max_completion_tokens", 100),
                                                ({}, "max_tokens", 32768)):
            policy.model_request_ceiling = lambda route, field=quoted_field, limit=quoted_limit: model_request_ceiling({
                **route, "output_token_field": field, "max_output_tokens": limit})
            request = {**original, **cap}
            agent._test_model_request = request
            loop.perform_api_call(agent)
            sent = network_requests[-1]
            expected = next(iter(cap.values()), quoted_limit)
            assert next(sent[key] for key in ("max_tokens", "max_completion_tokens") if key in sent) == expected
            assert request == {**original, **cap}  # The middleware's request was not mutated.
            start, returned = effects[-2:]
            assert start[0] == "start" and returned[0] == "returned"
            assert start[1]["request_sha256"] == digest(sent)
            assert start[1]["request_bytes"] == len(canonical(sent))
            assert start[1]["output_tokens"] == expected
            assert agent._disable_streaming is False
        before = (len(effects), len(network_requests))
        for invalid in ({"max_tokens": None}, {"max_tokens": True}, {"max_tokens": 0},
                        {"max_tokens": 1, "max_completion_tokens": 2}, {"max_output_tokens": 1},
                        {"stream": True}):
            agent._test_model_request = {**original, **invalid}
            with pytest.raises(WorkContractError):
                loop.perform_api_call(agent)
            assert (len(effects), len(network_requests)) == before
        # A preexisting incompatible cap must stop before either reservation or transport.
        from herdr.work_budget_configuration import model_request_ceiling
        policy.model_request_ceiling = lambda route: model_request_ceiling({**route, "max_output_tokens": 100})
        for model_name, wrong_cap in (("openai/o3-2025-04-16", {"max_tokens": 17}),
                                      ("quoted-text-model", {"max_completion_tokens": 18})):
            agent.model = model_name
            request = {**original, "model": model_name, **wrong_cap}
            agent._test_model_request = request
            before = (len(effects), len(network_requests))
            with pytest.raises(PolicyDenied, match="model_quote_token_field_mismatch"):
                loop.perform_api_call(agent)
            assert (len(effects), len(network_requests)) == before
            assert request == {**original, "model": model_name, **wrong_cap}
            assert agent._disable_streaming is False
        agent.model = original["model"]
        policy.budget_required = lambda: False
        policy.grant.provider_routes[0].api_mode = "openai"
        agent.api_mode = "openai"
        del agent._test_model_request
        callbacks.clear()
        def switch(request, next_call, **context):
            callbacks.append("switch_callback")
            agent.provider = "provider-b"
            return next_call(request)
        # A middleware callback can change the route after the outer check.
        installation.uninstall()
        middleware.run_llm_execution_middleware = switch
        installation = hermes_guard.install_hermes_guard(Guard())
        agent.provider = "provider-a"
        with pytest.raises(PolicyDenied, match="provider_not_granted"):
            loop.perform_api_call(agent)
        assert callbacks == ["switch_callback"]

        # The guarded process never rotates native Anthropic credentials after
        # authorization. A future refresh must be brokered and re-attested.
        lifecycle_instance = ClientLifecycleMixin()
        assert lifecycle_instance._try_refresh_anthropic_client_credentials() is False
        assert lifecycle_instance.refresh_calls == 0

        # Auxiliary compression/vision/memory attempts reach separate final
        # transport seams. Every physical primary/retry/fallback/stream attempt
        # is authorized from its resolved endpoint before its callback executes.
        physical_stream = []
        completions = types.SimpleNamespace(
            create=lambda **kwargs: physical_stream.append(dict(kwargs)) or "stream-ok"
        )
        aux_client = types.SimpleNamespace(
            base_url="https://provider-a.example.invalid/v1", api_key="",
            chat=types.SimpleNamespace(completions=completions),
        )
        auxiliary._test_stream_client = aux_client
        executed = []
        assert auxiliary._relay_sync_completion(
            aux_client, {"messages": []}, provider="provider-a", api_mode="openai",
            create=lambda request: executed.append("sync") or "sync-ok",
        ) == "sync-ok"
        with pytest.raises(PolicyDenied, match="provider_credential_identity_unknown"):
            auxiliary._relay_sync_completion(
                aux_client, {"rotate_before_create": True}, provider="provider-a",
                api_mode="openai", create=lambda request: executed.append("rotated"),
            )
        aux_client.api_key = ""
        async def async_create(request):
            return "async-ok"
        assert asyncio.run(auxiliary._relay_async_completion(
            aux_client, {"messages": []}, provider="provider-a", api_mode="openai",
            create=async_create,
        )) == "async-ok"
        assert auxiliary._relay_sync_stream(
            aux_client, {"messages": []}, provider="provider-a", api_mode="openai"
        ) == "stream-ok"
        before_stream = len(physical_stream)
        aux_client.api_key = ""
        with pytest.raises(PolicyDenied, match="provider_credential_identity_unknown"):
            auxiliary._relay_sync_stream(
                aux_client, {"messages": [], "rotate_before_stream_create": True},
                provider="provider-a", api_mode="openai",
            )
        assert len(physical_stream) == before_stream
        aux_client.api_key = ""
        with pytest.raises(PolicyDenied, match="provider_not_granted"):
            auxiliary._relay_sync_completion(
                aux_client, {"messages": []}, provider="provider-b", api_mode="openai",
                create=lambda request: executed.append("denied") or "must-not-run",
            )
        with pytest.raises(PolicyDenied, match="provider_endpoint_denied"):
            auxiliary._relay_sync_completion(
                types.SimpleNamespace(base_url="https://wrong.example.invalid/v1", api_key=""),
                {"messages": []}, provider="provider-a", api_mode="openai",
                create=lambda request: executed.append("wrong") or "must-not-run",
            )

        # The special MoA Codex branch bypasses _relay_sync_stream in Hermes,
        # so its physical Responses adapter is guarded independently.
        policy.grant.provider_routes[0].api_mode = "codex_responses"
        real_codex = types.SimpleNamespace(
            base_url="https://provider-a.example.invalid/v1",
            api_key="",
            _hermes_aux_effective_provider="actual",
        )
        assert CodexAdapter(real_codex).create(model="codex") == "codex-direct"
        assert aux_calls[-1][0] == "codex-direct"
        assert executed == ["sync"]
        assert called == ["read_file", "read_file", "read_file"]
    finally:
        installation.uninstall()


def test_policy_file_ops_binary_read_uses_pinned_root_fd(tmp_path):
    import base64
    from herdr.file_authority import RootFDWorkspace

    root = tmp_path / "workspace"
    pinned = tmp_path / "workspace-pinned"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "document.bin").write_bytes(b"trusted-bytes")
    (outside / "document.bin").write_bytes(b"outside-bytes")

    class ReadResult:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.error = kwargs.get("error")

    common = types.SimpleNamespace(ReadResult=ReadResult)
    delegate = types.SimpleNamespace()
    authority = RootFDWorkspace((str(root),))
    try:
        ops = hermes_guard._PolicyFileOps(authority, delegate, common, types.SimpleNamespace())
        root.rename(pinned)
        root.symlink_to(outside, target_is_directory=True)
        result = ops.read_file_bytes(str(root / "document.bin"), max_bytes=1024)
        assert result.error is None
        assert base64.b64decode(result.base64_content) == b"trusted-bytes"
        assert result.is_binary is True
    finally:
        authority.close()


def test_policy_search_cannot_delegate_shell_or_follow_a_raced_file(tmp_path,monkeypatch):
    from herdr.file_authority import RootFDWorkspace
    from dataclasses import dataclass,field
    @dataclass
    class Result:
        matches:list=field(default_factory=list)
        files:list=field(default_factory=list)
        counts:dict=field(default_factory=dict)
        total_count:int=0
        truncated:bool=False
        limit_reason:str|None=None
        error:str|None=None
    root=tmp_path/"work";outside=tmp_path/"outside";root.mkdir();outside.mkdir()
    target=root/"safe.txt";target.write_text("needle in owned file")
    secret=outside/"secret.txt";secret.write_text("needle outside secret")
    authority=RootFDWorkspace((str(root),))
    delegate=types.SimpleNamespace(search=lambda *a,**kw:pytest.fail("raw backend search forbidden"))
    common=types.SimpleNamespace(SearchResult=Result,SearchMatch=lambda path,line_number,content:
        types.SimpleNamespace(path=path,line_number=line_number,content=content))
    ops=hermes_guard._PolicyFileOps(authority,delegate,common,types.SimpleNamespace())
    try:
        result=ops.search("needle",str(root))
        assert result.total_count==1 and result.matches[0].content=="needle in owned file"
        assert ops.search("*.txt",str(root),target="files").files==[str(target)]
        assert ops.search("(needle)+",str(root)).error
        original=authority.read_bytes
        def race(path,**kw):
            target.unlink();target.symlink_to(secret)
            return original(path,**kw)
        monkeypatch.setattr(authority,"read_bytes",race)
        assert ops.search("needle",str(root)).error
        assert secret.read_text()=="needle outside secret"
        with pytest.raises(PolicyDenied,match="file_operation_unattested"):
            ops._execute
    finally: authority.close()

def test_duplicate_v4a_add_targets_deny_before_any_file_effect(tmp_path):
    from herdr.file_authority import RootFDWorkspace
    from types import SimpleNamespace
    root=tmp_path/"workspace";root.mkdir()
    target=str(root/"new.txt");applied=[]
    class Result:
        def __init__(self,**kwargs): self.__dict__.update(kwargs)
    parser=SimpleNamespace(
        parse_v4a_patch=lambda raw:(
            [SimpleNamespace(file_path=target,operation=SimpleNamespace(value="add")),
             SimpleNamespace(file_path=str(root/"./new.txt"),operation=SimpleNamespace(value="add"))],None),
        apply_v4a_operations=lambda *args:applied.append(args))
    authority=RootFDWorkspace((str(root),))
    try:
        ops=hermes_guard._PolicyFileOps(authority,SimpleNamespace(),
                                       SimpleNamespace(PatchResult=Result),parser)
        result=ops.patch_v4a("two adds")
        assert result.error=="duplicate V4A Add target"
        assert applied==[] and not (root/"new.txt").exists()
    finally: authority.close()


@pytest.mark.parametrize("expected,actual",[
    ("https://gateway.example/v1?tenant=approved/","https://gateway.example/v1?tenant=approved"),
    ("https://gateway.example/v1//","https://gateway.example/v1/"),
])
def test_auxiliary_transport_rejects_distinct_query_or_path(expected,actual):
    route=types.SimpleNamespace(provider="provider-a",base_url=expected,api_mode="openai")
    guard=types.SimpleNamespace(grant=types.SimpleNamespace(provider_routes=(route,)))
    client=types.SimpleNamespace(base_url=actual)
    with pytest.raises(PolicyDenied,match="provider_endpoint_denied"):
        hermes_guard._effective_aux_route(guard,client,"provider-a","openai")
    client.base_url=expected
    assert hermes_guard._effective_aux_route(guard,client,"provider-a","openai") is route


def test_v4a_update_denies_before_earlier_add_can_mutate(tmp_path):
    from herdr.file_authority import RootFDWorkspace
    root=tmp_path/"workspace";root.mkdir();target=root/"existing";target.write_text("original")
    class Result:
        def __init__(self,**kwargs):self.__dict__.update(kwargs)
    applied=[]
    parser=types.SimpleNamespace(parse_v4a_patch=lambda raw:([
        types.SimpleNamespace(file_path=str(root/"new"),operation=types.SimpleNamespace(value="add")),
        types.SimpleNamespace(file_path=str(target),operation=types.SimpleNamespace(value="update"))],None),
        apply_v4a_operations=lambda *args:applied.append(args))
    authority=RootFDWorkspace((str(root),))
    try:
        ops=hermes_guard._PolicyFileOps(authority,types.SimpleNamespace(),
            types.SimpleNamespace(PatchResult=Result),parser)
        result=ops.patch_v4a("add then unsupported update")
        assert "conditional replacement unavailable" in result.error
        assert applied==[] and target.read_text()=="original" and not (root/"new").exists()
    finally:authority.close()



def _read_hash_ops(root, gate):
    """Small result double; the pinned SDK JSON contract is tested separately."""
    from dataclasses import dataclass
    from herdr.file_authority import RootFDWorkspace

    @dataclass
    class ReadResult:
        content: str = ""
        total_lines: int = 0
        file_size: int = 0
        truncated: bool = False
        error: str | None = None
        base64_content: str | None = None
        is_binary: bool = False

        def to_dict(self):
            return {key: value for key, value in vars(self).items()
                    if not key.startswith("_") and value is not None}

    authority = RootFDWorkspace((str(root),))
    delegate = types.SimpleNamespace(_add_line_numbers=lambda value, offset:
        "\n".join(f"{offset+i}|{line}" for i, line in enumerate(value.splitlines())))
    return authority, hermes_guard._PolicyFileOps(authority, delegate,
        types.SimpleNamespace(ReadResult=ReadResult), types.SimpleNamespace(),
        redaction_gate=gate)


@pytest.mark.parametrize("raw", [
    b"alpha\nbeta\n", b"alpha\r\nbeta\r\n", b"\xef\xbb\xbfalpha\r\n",
    b"alpha\rbeta\r", "Příliš žluťoučký \u212b A\u030a\n".encode(),
    b"alpha", b"alpha\n\n", b"",
], ids=["lf", "crlf", "bom", "lone-cr", "unicode", "no-final-newline", "trailing-blank", "empty"])
def test_policy_read_public_hashes_bind_exact_utf8_buffer(tmp_path, raw):
    import hashlib
    target = tmp_path / "source.py"; target.write_bytes(raw)
    seen = []
    def gate(path, text):
        seen.append((path, text))
        return text
    authority, ops = _read_hash_ops(tmp_path, gate)
    try:
        result = ops.read_file(str(target), offset=1, limit=1).to_dict()
        assert result["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert result["sha256_crlf_to_lf"] == hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        assert result["hash_scope"] == "entire-read-buffer"
        assert seen == [(str(target), raw.decode("utf-8"))]
        assert result["file_size"] == len(raw)
    finally:
        authority.close()


def test_policy_read_hashes_do_not_reread_or_hash_only_the_visible_page(tmp_path, monkeypatch):
    import hashlib
    target = tmp_path / "large.py"
    raw = b"visible\n" + b"hidden-but-public\n" * 3000
    target.write_bytes(raw)
    authority, ops = _read_hash_ops(tmp_path, lambda path, text: text)
    original = authority.read_bytes
    reads = []
    def counted(path, **kwargs):
        reads.append(path)
        value = original(path, **kwargs)
        # A later replacement must not make metadata describe different bytes
        # from those used to produce this page.
        target.write_bytes(b"replacement-after-the-read\n")
        return value
    monkeypatch.setattr(authority, "read_bytes", counted)
    try:
        result = ops.read_file(str(target), limit=1).to_dict()
        assert reads == [str(target)]
        assert result["content"] == "1|visible" and result["truncated"] is True
        assert result["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert result["raw_sha256"] != hashlib.sha256(target.read_bytes()).hexdigest()
    finally:
        authority.close()


@pytest.mark.parametrize("failure", ["absent", "not-callable", "raises", "none", "number", "changed"])
def test_policy_read_optional_hash_gate_fails_closed_without_breaking_content(tmp_path, failure):
    target = tmp_path / "source.py"; target.write_text("visible\n")
    def raises(path, text):
        raise RuntimeError("unit-only unavailable redactor")
    gates = {"absent": None, "not-callable": 1, "raises": raises,
             "none": lambda path, text: None, "number": lambda path, text: 1,
             "changed": lambda path, text: "redacted"}
    authority, ops = _read_hash_ops(tmp_path, gates[failure])
    try:
        result = ops.read_file(str(target), limit=1).to_dict()
        assert result["content"] == "1|visible" and not result.get("error")
        assert not {"raw_sha256", "sha256_crlf_to_lf", "hash_scope"} & result.keys()
    finally:
        authority.close()


def test_policy_read_hidden_redacted_text_never_discloses_a_whole_file_hash(tmp_path):
    target = tmp_path / "source.py"; target.write_text("visible\nunit-secret-on-hidden-line\n")
    seen = []
    def gate(path, text):
        seen.append(text)
        return text.replace("unit-secret-on-hidden-line", "<redacted>")
    authority, ops = _read_hash_ops(tmp_path, gate)
    try:
        result = ops.read_file(str(target), limit=1).to_dict()
        assert seen == ["visible\nunit-secret-on-hidden-line\n"]
        assert result["content"] == "1|visible"
        assert not {"raw_sha256", "sha256_crlf_to_lf", "hash_scope"} & result.keys()
    finally:
        authority.close()


@pytest.mark.parametrize("failure", ["outside", "symlink", "non-utf8", "pagination"])
def test_policy_read_errors_never_return_public_hashes(tmp_path, failure):
    root = tmp_path / "root"; root.mkdir()
    target = root / "source.py"; target.write_bytes(b"public\n")
    outside = tmp_path / "outside.py"; outside.write_bytes(b"outside\n")
    selected = str(target)
    if failure == "outside": selected = str(outside)
    elif failure == "symlink": target.unlink(); target.symlink_to(outside)
    elif failure == "non-utf8": target.write_bytes(b"\xff\xfe")
    authority, ops = _read_hash_ops(root, lambda path, text: text)
    try:
        result = ops.read_file(selected, offset=0 if failure == "pagination" else 1).to_dict()
        assert result["error"]
        assert not {"raw_sha256", "sha256_crlf_to_lf", "hash_scope"} & result.keys()
    finally:
        authority.close()


def test_policy_binary_read_and_nul_text_never_return_public_hashes(tmp_path):
    target = tmp_path / "data.bin"; target.write_bytes(b"binary\x00payload")
    authority, ops = _read_hash_ops(tmp_path, lambda path, text: text)
    try:
        for result in (ops.read_file_bytes(str(target)).to_dict(),
                       ops.read_file(str(target)).to_dict()):
            assert not {"raw_sha256", "sha256_crlf_to_lf", "hash_scope"} & result.keys()
    finally:
        authority.close()


def test_pinned_sdk_formatter_preserves_safe_whole_read_hashes(tmp_path):
    """Actual guard, file formatter and redactor; no CLI/agent/auth/provider call."""
    import os
    from pathlib import Path
    import subprocess

    sdk = Path("/opt/herdr/releases/p0-5035d92-test/hermes")
    python = Path("/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11")
    if not sdk.is_dir() or not python.is_file():
        pytest.skip("pinned SDK formatter component unavailable")
    repo = Path(__file__).resolve().parents[2]
    script = r'''
import hashlib,json,os,socket,subprocess,sys,types
from pathlib import Path
repo,sdk,scratch=map(Path,sys.argv[1:4])
sys.path[:0]=[str(repo),str(sdk),str(sdk/"venv/lib/python3.11/site-packages")]
def denied(*args,**kwargs):raise AssertionError("component attempted external effect")
socket.socket.connect=denied;socket.socket.connect_ex=denied;socket.getaddrinfo=denied
subprocess.Popen=denied;os.system=denied
pins={
"tools/file_tools.py":"e1c5dec811b68b59d0926b1d9fa5aab3e89aef4d47a492b22aa03bc162acc095",
"tools/file_operations_common.py":"dc0a3d7c46376694eaa918a2c9239dbbc0d77234ffe6010582c8c112e835cae8",
"tools/file_operations.py":"f0089dae05fd7695aaafbea55e5ce17eb8f4b07e3d8d83a17989a005e682f804",
"agent/redact.py":"85f6bcf8577697713dbf12992a75ec4f269f90e52523475a8d84a9d287b81c5b"}
for name,digest in pins.items():assert hashlib.sha256((sdk/name).read_bytes()).hexdigest()==digest
home=scratch/"home";home.mkdir()
profile=home/".hermes";profile.mkdir();(profile/"config.yaml").write_text("{}\n")
os.environ.update(HOME=str(home),HERMES_HOME=str(profile),HERMES_SAFE_MODE="1",
                  HERMES_ENABLE_PROJECT_PLUGINS="0",HERMES_REDACT_SECRETS="true")
from tools import file_tools,terminal_tool
from tools.file_operations import ShellFileOperations
from herdr.hermes_guard import install_hermes_guard
from herdr.security import InvocationGuard,SecurityGrant
unit_grant=SecurityGrant.from_dict(json.loads(sys.argv[4]))
work=scratch/"work";work.mkdir()
delegate=ShellFileOperations(None,cwd=str(work))
# This is the lower environment acquisition seam only: formatting, redaction,
# authority reads/writes, guard installation and to_dict below remain actual.
file_tools._get_file_ops=lambda task_id="default":delegate
terminal_tool._get_env_config=lambda:{"env_type":"local"}
installation=install_hermes_guard(InvocationGuard(unit_grant))
try:
 original=file_tools.redact_sensitive_text
 seen=[]
 def observe(text,**kwargs):
  seen.append(text)
  return original(text,**kwargs)
 file_tools.redact_sensitive_text=observe
 target=work/"source.py";raw=b"visible\r\n"+b"public hidden line\r\n"*3000;target.write_bytes(raw)
 first=json.loads(file_tools.read_file_tool(str(target),offset=1,limit=1,task_id="child-task"))
 assert first.get("raw_sha256")==hashlib.sha256(raw).hexdigest(),first
 assert first["sha256_crlf_to_lf"]==hashlib.sha256(raw.replace(b"\r\n",b"\n")).hexdigest()
 assert first["hash_scope"]=="entire-read-buffer" and first["truncated"] is True
 assert raw.decode() in seen and len(first["content"])<100
 proxy=file_tools._get_file_ops("child-task")
 patched=proxy.patch_replace(str(target),"visible","edited")
 assert not patched.success and "conditional replacement unavailable" in patched.error
 assert target.read_bytes()==raw  # Preserve the existing shared-writer barrier.
 written=proxy.write_file(str(target),"edited\npublic replacement\n")
 assert written.verified is True and not written.error
 changed=target.read_bytes()
 second=json.loads(file_tools.read_file_tool(str(target),offset=1,limit=1,task_id="child-task"))
 assert second["raw_sha256"]==hashlib.sha256(changed).hexdigest()!=first["raw_sha256"]
 created=work/"created.py"
 added=proxy.patch_v4a("*** Begin Patch\n*** Add File: "+str(created)+"\n+public addition\n*** End Patch\n")
 assert added.success and not added.error, added.error
 created_read=json.loads(file_tools.read_file_tool(str(created),limit=1,task_id="child-task"))
 assert created_read["raw_sha256"]==hashlib.sha256(created.read_bytes()).hexdigest()
 secret=work/"hidden.py";secret.write_text("visible\n"+"sk-"+"A"*40+"\n")
 secret_result=json.loads(file_tools.read_file_tool(str(secret),limit=1,task_id="child-task"))
 assert "error" not in secret_result and secret_result["content"].startswith("1|visible")
 assert not {"raw_sha256","sha256_crlf_to_lf","hash_scope"}&secret_result.keys()
 # A replaced/unavailable current display redactor cannot reuse an older gate.
 file_tools.redact_sensitive_text=None
 unavailable=proxy.read_file(str(target),limit=1).to_dict()
 assert not {"raw_sha256","sha256_crlf_to_lf","hash_scope"}&unavailable.keys()
 print(json.dumps({"actual_sdk_formatter_json":True,"actual_install_gate":True,
  "public_hashes_before_pagination":True,"patch_update_denied":True,
  "v4a_add_then_read_hash":True,"write_then_new_hash":True,
  "hidden_secret_digest_suppressed":True,"current_redactor_lookup":True,
  "cli_model_auth_or_provider_calls":0}))
finally:
 installation.uninstall()
'''
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "launch-home"),
           "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(tmp_path)}
    from tests.herdr.test_security import grant as unit_grant
    grant_json = json.dumps(unit_grant(tmp_path / "work", tools=("read_file", "write_file", "patch")).to_json())
    result = subprocess.run([str(python), "-I", "-B", "-c", script, str(repo), str(sdk), str(tmp_path), grant_json],
                            env=env, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])["actual_sdk_formatter_json"] is True
