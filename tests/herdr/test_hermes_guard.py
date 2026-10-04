"""Invocation seam tests without importing or mutating installed Hermes."""
import json
import sys
import types
import pytest

from herdr import hermes_guard
from herdr.capability import DataClass
from herdr.security import PolicyDenied, SecurityError


def test_provider_credential_identity_comes_from_actual_pool_entry():
    route = types.SimpleNamespace(provider="provider-a", credential_refs=("pool:provider-a:entry-1",))
    pool = types.SimpleNamespace(provider="provider-a", entry_id_for_api_key=lambda key: "entry-1" if key == "actual" else None)
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
        effective = {"path": function_args["rewrite"]} if "rewrite" in function_args else function_args
        return execute(effective)
    executor._run_agent_tool_execution_middleware = run_tool
    middleware = types.ModuleType("hermes_cli.middleware")
    callbacks = []
    middleware.run_llm_execution_middleware = lambda request, next_call, **context: (callbacks.append("callback"), next_call(request))[1]
    def perform(agent, **kwargs):
        from hermes_cli.middleware import run_llm_execution_middleware
        return run_llm_execution_middleware({}, lambda request: callbacks.append("network"), provider=agent.provider)
    turn.perform_api_call = perform
    loop.perform_api_call = perform
    agent_pkg = types.ModuleType("agent")
    agent_pkg.turn_api_call = turn
    agent_pkg.conversation_loop = loop
    agent_pkg.tool_executor = executor
    cli_pkg = types.ModuleType("hermes_cli")
    cli_pkg.middleware = middleware
    monkeypatch.setitem(sys.modules, "agent", agent_pkg)
    monkeypatch.setitem(sys.modules, "agent.turn_api_call", turn)
    monkeypatch.setitem(sys.modules, "agent.conversation_loop", loop)
    monkeypatch.setitem(sys.modules, "agent.tool_executor", executor)
    monkeypatch.setitem(sys.modules, "hermes_cli", cli_pkg)
    monkeypatch.setitem(sys.modules, "hermes_cli.middleware", middleware)
    monkeypatch.setitem(sys.modules, "model_tools", model)
    monkeypatch.setitem(sys.modules, "tools", types.ModuleType("tools"))
    monkeypatch.setitem(sys.modules, "tools.registry", registry_module)
    monkeypatch.setitem(sys.modules, "tools.connectors", connector_module)
    monkeypatch.setitem(sys.modules, "tools.connectors.dispatch", connector_dispatch)
    monkeypatch.setitem(sys.modules, "tools.tool_search", tool_search)
    read_extract = types.ModuleType("tools.read_extract")
    read_extract._hosted_ocr_config = lambda: (True, "secret", "url")
    paths = types.ModuleType("tools.file_tools_paths")
    paths._resolve_path_for_task = lambda value, task_id: value
    monkeypatch.setitem(sys.modules, "tools.read_extract", read_extract)
    monkeypatch.setitem(sys.modules, "tools.file_tools_paths", paths)
    monkeypatch.setattr(hermes_guard, "inspect_hermes_security_surface",
                        lambda: {"legacy_aliases": {"old_write": "write_file"}})

    class Guard:
        aliases = {}
        checks = []
        grant = types.SimpleNamespace(identity=types.SimpleNamespace(task_id="task"), scope=types.SimpleNamespace(data_classes=(DataClass.INTERNAL,)), provider_routes=(types.SimpleNamespace(provider="provider-a", base_url="https://provider-a.example.invalid/v1", api_mode="openai", regions=("eu-central",), data_classes=("internal",), max_egress="region_bound", max_retention="limited", training="excluded", credential_refs=()),))

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
            if args != {"path": "/scoped/file"}:
                raise PolicyDenied("path_outside_grant")
            return canonical

        def authorize_tool_call(self, name, args, *, caller_task_id=None, consume_approval=True):
            return self.authorize_tool(name, args, caller_task_id=caller_task_id,
                                       consume_approval=consume_approval), dict(args)

    policy = Guard()
    installation = hermes_guard.install_hermes_guard(policy)
    try:
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
        assert called == ["read_file", "read_file"]
    finally:
        installation.uninstall()
