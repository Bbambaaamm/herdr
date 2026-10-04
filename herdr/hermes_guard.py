"""In-process Hermes v0.21.5 invocation guard for Herdr issue #76.

Hermes toolsets and plugin hooks remain useful UI/defense-in-depth surfaces, but
are not authority: v0.21.5 exposes explicit skip_* flags and middleware itself
fails open on plugin errors.  This adapter therefore guards the real dispatch
seams without modifying the Hermes installation:

* agent.tool_executor middleware -- catches every model-emitted execution path;
* model_tools.handle_function_call -- catches direct/aliased/model calls;
* ToolRegistry.dispatch -- catches effective post-middleware local arguments;
* connector dispatch -- catches the non-registry connector execution seam.

The adapter is intentionally installed by a host launcher *after* an
authenticated Herdr grant has been verified.  It never reads model content as
authority.
"""
from __future__ import annotations

import functools
import inspect
import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from herdr.security import InvocationGuard, PolicyDenied, SecurityError, ProviderRequest, canonical_digest


class HermesCompatibilityError(RuntimeError):
    """Installed Hermes dispatch contract is not the versioned surface we audited."""


_AUTHORIZED_CALL: ContextVar[tuple[str, str] | None] = ContextVar(
    "herdr_authorized_call", default=None
)
_ACTIVE_AGENT: ContextVar[Any | None] = ContextVar("herdr_active_provider_agent", default=None)
_META_READ_TOOLS = frozenset({"tool_search", "tool_describe"})
_BRIDGE_TOOL = "tool_call"


def _call_digest(tool: str, args: Mapping[str, Any] | None) -> str:
    return canonical_digest({"tool": tool, "args": dict(args or {})})


def _denied_result(reason: str, detail: str = "") -> str:
    try:
        from tools.registry import tool_error

        return tool_error(
            f"HERDR_SECURITY_DENIED[{reason}]"
            + (f": {detail}" if detail else "")
        )
    except Exception:
        return json.dumps(
            {
                "error": {
                    "code": "HERDR_SECURITY_DENIED",
                    "reason": reason,
                    "detail": detail[:256],
                }
            },
            ensure_ascii=False,
        )


def _effective_request_data_class(guard: InvocationGuard) -> Any:
    """Use the most sensitive class in the signed task scope.

    Route metadata describes what a destination may accept; it must never be
    reused as a claim about the sensitivity of the request being sent.
    """
    classes = tuple(getattr(getattr(guard, "grant", None), "scope", None).data_classes)
    if not classes:
        raise PolicyDenied("request_data_class_unknown")
    order = {"public": 0, "internal": 1, "sensitive": 2}
    try:
        return max(classes, key=lambda item: order[item.value])
    except (AttributeError, KeyError) as exc:
        raise PolicyDenied("request_data_class_unknown") from exc


def _actual_provider_credential_ref(agent: Any, route: Any) -> str | None:
    """Resolve the actual selected key through Hermes' credential pool identity."""
    refs = tuple(getattr(route, "credential_refs", ()) or ())
    raw = getattr(agent, "api_key", None)
    if getattr(agent, "api_mode", None) == "anthropic_messages":
        raw = getattr(agent, "_anthropic_api_key", None) or raw
    if raw is None:
        raw = ""
    if not isinstance(raw, str):
        raise PolicyDenied("provider_credential_identity_unknown")
    if not raw:
        if refs:
            raise PolicyDenied("provider_credential_missing")
        return None
    pool = getattr(agent, "_credential_pool", None)
    if getattr(pool, "provider", None) != route.provider:
        raise PolicyDenied("provider_credential_identity_unknown")
    return _bind_pool_credential(pool, raw, route.provider, refs)


def _bind_pool_credential(pool: Any, raw: str, provider: str, refs: tuple[str, ...]) -> str:
    """Bind the effective key to exactly one entry; a pool cursor is not proof."""
    entries = getattr(pool, "entries", None)
    if not callable(entries):
        raise PolicyDenied("provider_credential_identity_unknown")
    try:
        matches = [item for item in entries() if getattr(item, "runtime_api_key", None) == raw]
    except Exception as exc:
        raise PolicyDenied("provider_credential_identity_unknown") from exc
    if len(matches) != 1:
        raise PolicyDenied("provider_credential_identity_unknown")
    entry_id = getattr(matches[0], "id", None)
    if not isinstance(entry_id, str) or not entry_id:
        raise PolicyDenied("provider_credential_identity_unknown")
    actual = f"pool:{provider}:{entry_id}"
    if actual not in refs:
        raise PolicyDenied("provider_credential_mismatch")
    return actual


def _endpoint(value: Any) -> str:
    return str(value or "").rstrip("/")


def _effective_aux_route(guard: InvocationGuard, client: Any, provider: Any, api_mode: Any) -> Any:
    """Resolve the actual auxiliary transport to exactly one signed provider route."""
    routes = tuple(getattr(getattr(guard, "grant", None), "provider_routes", ()) or ())
    actual_endpoint = _endpoint(getattr(client, "base_url", None))
    actual_mode = str(api_mode or "")
    named = [route for route in routes if route.provider == provider]
    if named:
        candidates = named
    elif provider in (None, "", "auto", "auxiliary", "actual"):
        candidates = [
            route for route in routes
            if _endpoint(route.base_url) == actual_endpoint and route.api_mode == actual_mode
        ]
    else:
        candidates = []
    if len(candidates) != 1:
        raise PolicyDenied("provider_not_granted", str(provider)[:100])
    route = candidates[0]
    if _endpoint(route.base_url) != actual_endpoint or route.api_mode != actual_mode:
        raise PolicyDenied("provider_endpoint_denied", str(route.provider)[:100])
    return route


def _actual_aux_credential_ref(client: Any, route: Any) -> str | None:
    """Resolve the final auxiliary client's actual key through Hermes' trusted pool."""
    refs = tuple(getattr(route, "credential_refs", ()) or ())
    raw = getattr(client, "api_key", None)
    if raw is None:
        raw = ""
    if not isinstance(raw, str):
        raise PolicyDenied("provider_credential_identity_unknown")
    if not raw:
        if refs:
            raise PolicyDenied("provider_credential_missing")
        return None
    try:
        from agent.credential_pool import load_pool
        pool = load_pool(route.provider)
    except Exception as exc:
        raise PolicyDenied("provider_credential_identity_unknown") from exc
    if getattr(pool, "provider", None) != route.provider:
        raise PolicyDenied("provider_credential_identity_unknown")
    return _bind_pool_credential(pool, raw, route.provider, refs)


def _authorize_aux_transport(
    guard: InvocationGuard, client: Any, provider: Any, api_mode: Any
) -> None:
    route = _effective_aux_route(guard, client, provider, api_mode)
    if len(route.regions) != 1 or len(route.data_classes) != 1:
        raise PolicyDenied("provider_route_ambiguous", str(route.provider))
    guard.authorize_provider(ProviderRequest(
        provider=route.provider,
        region=route.regions[0],
        data_class=_effective_request_data_class(guard),
        egress=route.max_egress,
        retention=route.max_retention,
        training=route.training,
        credential_ref=_actual_aux_credential_ref(client, route),
    ))


def inspect_hermes_security_surface() -> dict[str, Any]:
    """Fail-closed compatibility probe for the installed Hermes import surface."""
    try:
        import model_tools
        from hermes_cli import middleware, plugins
        from agent import auxiliary_client, turn_api_call, conversation_loop, tool_executor
        from agent.client_lifecycle import ClientLifecycleMixin
        from tools import connectors, read_extract
        from tools.file_tools_paths import _resolve_path_for_task
        from tools.registry import registry
        from toolsets import resolve_toolset
    except Exception as exc:
        raise HermesCompatibilityError(f"required Hermes modules unavailable: {exc}") from exc

    params = inspect.signature(model_tools.handle_function_call).parameters
    required_params = {
        "function_name",
        "function_args",
        "task_id",
        "skip_pre_tool_call_hook",
        "skip_tool_request_middleware",
        "skip_tool_execution_middleware",
    }
    missing = sorted(required_params - set(params))
    if missing:
        raise HermesCompatibilityError(
            f"handle_function_call surface drifted; missing {missing}"
        )
    if not callable(getattr(registry, "dispatch", None)):
        raise HermesCompatibilityError("registry.dispatch unavailable")
    audited = {
        "agent", "function_name", "function_args", "effective_task_id",
        "tool_call_id", "execute", "scope_block", "display_index",
        "middleware_trace", "begin_execution", "authorization_gate",
    }
    seam = getattr(tool_executor, "_run_agent_tool_execution_middleware", None)
    if not callable(seam) or tuple(inspect.signature(seam).parameters) != (
        "agent", "function_name", "function_args", "effective_task_id", "tool_call_id",
        "execute", "scope_block", "display_index", "middleware_trace",
        "begin_execution", "authorization_gate",
    ):
        raise HermesCompatibilityError("agent tool-execution seam drifted")
    seam_params = inspect.signature(seam).parameters
    if set(seam_params) != audited or any(
        seam_params[name].kind is not inspect.Parameter.KEYWORD_ONLY
        for name in audited if name != "agent"
    ) or seam_params["agent"].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD:
        raise HermesCompatibilityError("agent tool-execution signature drifted")
    dispatch_once = getattr(tool_executor, "_dispatch_authorized_once", None)
    if not callable(dispatch_once) or tuple(inspect.signature(dispatch_once).parameters) != (
        "agent", "state", "ref", "execute", "scope_block", "display_index",
        "begin_execution", "authorization_gate",
    ):
        raise HermesCompatibilityError("agent authorized-dispatch seam drifted")
    if not callable(getattr(connectors, "dispatch_connector_call", None)):
        raise HermesCompatibilityError("connector dispatch unavailable")
    if not callable(getattr(turn_api_call, "perform_api_call", None)) or conversation_loop.perform_api_call is not turn_api_call.perform_api_call:
        raise HermesCompatibilityError("provider execution seam drifted")
    if not callable(getattr(middleware, "run_llm_execution_middleware", None)):
        raise HermesCompatibilityError("provider middleware seam unavailable")
    for name in ("_relay_sync_completion", "_relay_async_completion", "_relay_sync_stream"):
        if not callable(getattr(auxiliary_client, name, None)):
            raise HermesCompatibilityError(f"auxiliary provider seam unavailable: {name}")
    codex_adapter = getattr(auxiliary_client, "_CodexCompletionsAdapter", None)
    if codex_adapter is None or not callable(getattr(codex_adapter, "create", None)):
        raise HermesCompatibilityError("Codex auxiliary Responses seam unavailable")
    if not callable(getattr(ClientLifecycleMixin, "_try_refresh_anthropic_client_credentials", None)):
        raise HermesCompatibilityError("Anthropic credential-refresh seam unavailable")
    if not callable(_resolve_path_for_task):
        raise HermesCompatibilityError("Hermes task path resolver unavailable")
    if not callable(getattr(read_extract, "_hosted_ocr_config", None)):
        raise HermesCompatibilityError("Hermes hosted OCR seam unavailable")
    if "pre_tool_call" not in getattr(plugins, "VALID_HOOKS", set()):
        raise HermesCompatibilityError("pre_tool_call compatibility hook unavailable")
    middleware_required = {"tool_request", "tool_execution"}
    if not middleware_required <= set(getattr(middleware, "VALID_MIDDLEWARE", set())):
        raise HermesCompatibilityError("tool middleware compatibility surface unavailable")

    file_tools = tuple(resolve_toolset("file"))
    expected_file_tools = {"read_file", "write_file", "patch", "search_files"}
    if not expected_file_tools <= set(file_tools):
        raise HermesCompatibilityError(
            "Hermes file toolset no longer contains the audited four-tool bundle"
        )
    aliases = dict(getattr(model_tools, "_LEGACY_TOOL_ALIASES", {}))
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in aliases.items()):
        raise HermesCompatibilityError("legacy tool alias table is malformed")
    return {
        "handle_skip_flags": sorted(
            name for name in required_params if name.startswith("skip_")
        ),
        "file_toolset": list(file_tools),
        "legacy_aliases": aliases,
        "pre_tool_call_supported": True,
        "tool_request_middleware_supported": True,
        "tool_execution_middleware_supported": True,
        "agent_tool_execution_seam": True,
        "auxiliary_provider_seams": True,
        "anthropic_refresh_disabled_under_guard": True,
        "task_path_resolver": True,
        "hosted_ocr_disabled_under_guard": True,
        "security_authority": "herdr_dispatch_guard",
    }


@dataclass
class GuardInstallation:
    """Restorable in-process monkeypatch set; useful for tests and one-shot launchers."""

    guard: InvocationGuard
    originals: list[tuple[Any, str, Any]] = field(default_factory=list)
    surface: dict[str, Any] = field(default_factory=dict)
    installed: bool = True

    def _remember(self, owner: Any, name: str, replacement: Any) -> None:
        original = getattr(owner, name)
        self.originals.append((owner, name, original))
        setattr(owner, name, replacement)

    def uninstall(self) -> None:
        if not self.installed:
            return
        for owner, name, original in reversed(self.originals):
            setattr(owner, name, original)
        self.installed = False


def install_hermes_guard(guard: InvocationGuard) -> GuardInstallation:
    """Install #76 authority at all audited Hermes v0.21.5 execution seams.

    This must run before the model is allowed to issue tool calls.  Plugin
    pre_tool_call is intentionally *not* relied on: callers may set skip flags
    and middleware failures are fail-open in the audited Hermes version.
    """
    surface = inspect_hermes_security_surface()

    import model_tools
    from agent import auxiliary_client, conversation_loop, turn_api_call, tool_executor
    from agent.client_lifecycle import ClientLifecycleMixin
    from hermes_cli import middleware
    from tools import connectors, read_extract
    from tools.connectors import dispatch as connector_dispatch_module
    from tools.file_tools_paths import _resolve_path_for_task
    from tools.registry import ToolRegistry, registry

    aliases = dict(surface["legacy_aliases"])
    guard.aliases = aliases
    guard.path_resolver = lambda value, task_id: _resolve_path_for_task(
        value, task_id
    )
    installation = GuardInstallation(guard=guard, surface=surface)

    # A read_file PDF fallback can otherwise consume FIRECRAWL_API_KEY and send
    # document bytes to hosted OCR while the model only invoked a READ-class
    # tool. Under #76, cloud OCR must be an explicit separately granted tool.
    installation._remember(
        read_extract, "_hosted_ocr_config", lambda: (False, None, None)
    )

    # Native Anthropic rotates OAuth/pool credentials while constructing the
    # request-local client. That happens after the main provider precheck. In
    # policy mode rotation is disabled rather than accepting an unverified key;
    # a future brokered refresh must re-bind the resulting pool identity.
    installation._remember(
        ClientLifecycleMixin,
        "_try_refresh_anthropic_client_credentials",
        lambda self: False,
    )

    original_aux_sync = auxiliary_client._relay_sync_completion
    original_aux_async = auxiliary_client._relay_async_completion
    original_aux_stream = auxiliary_client._relay_sync_stream

    @functools.wraps(original_aux_sync)
    def guarded_aux_sync(
        client: Any,
        kwargs: dict[str, Any],
        *,
        provider: str | None = None,
        api_mode: str | None = None,
        create: Callable[[dict[str, Any]], Any] | None = None,
    ) -> Any:
        _authorize_aux_transport(guard, client, provider, api_mode)
        callback = create or (lambda request: auxiliary_client._create_with_progress(client, request))
        def checked_create(request: dict[str, Any]) -> Any:
            _authorize_aux_transport(guard, client, provider, api_mode)
            return callback(request)
        return original_aux_sync(
            client, kwargs, provider=provider, api_mode=api_mode, create=checked_create
        )

    @functools.wraps(original_aux_async)
    async def guarded_aux_async(
        client: Any,
        kwargs: dict[str, Any],
        *,
        provider: str | None = None,
        api_mode: str | None = None,
        create: Callable[[dict[str, Any]], Any] | None = None,
    ) -> Any:
        _authorize_aux_transport(guard, client, provider, api_mode)
        async def checked_create(request: dict[str, Any]) -> Any:
            _authorize_aux_transport(guard, client, provider, api_mode)
            if create is not None:
                return await create(request)
            return await auxiliary_client._acreate_with_progress(client, request)
        return await original_aux_async(
            client, kwargs, provider=provider, api_mode=api_mode, create=checked_create
        )

    @functools.wraps(original_aux_stream)
    def guarded_aux_stream(
        client: Any,
        kwargs: dict[str, Any],
        *,
        provider: str | None = None,
        api_mode: str | None = None,
    ) -> Any:
        _authorize_aux_transport(guard, client, provider, api_mode)
        return original_aux_stream(
            client, kwargs, provider=provider, api_mode=api_mode
        )

    installation._remember(
        auxiliary_client, "_relay_sync_completion", guarded_aux_sync
    )
    installation._remember(
        auxiliary_client, "_relay_async_completion", guarded_aux_async
    )
    installation._remember(
        auxiliary_client, "_relay_sync_stream", guarded_aux_stream
    )

    # MoA has one special Codex streaming branch that calls the Responses
    # adapter directly instead of _relay_sync_stream. Guard its physical
    # create() method as well so every provider attempt shares the same policy.
    codex_adapter = auxiliary_client._CodexCompletionsAdapter
    original_codex_create = codex_adapter.create

    @functools.wraps(original_codex_create)
    def guarded_codex_create(self: Any, **kwargs: Any) -> Any:
        real_client = getattr(self, "_client", None)
        if real_client is None:
            raise PolicyDenied("provider_context_missing")
        provider = getattr(real_client, "_hermes_aux_effective_provider", None)
        _authorize_aux_transport(
            guard, real_client, provider, "codex_responses"
        )
        return original_codex_create(self, **kwargs)

    installation._remember(codex_adapter, "create", guarded_codex_create)

    def authorize_agent_provider(agent: Any) -> None:
        provider = getattr(agent, "provider", None)
        routes = getattr(getattr(guard, "grant", None), "provider_routes", ())
        route = next((r for r in routes if r.provider == provider), None)
        if route is None:
            raise PolicyDenied("provider_not_granted", str(provider)[:100])
        if getattr(agent, "base_url", None) != route.base_url or getattr(agent, "api_mode", None) != route.api_mode:
            raise PolicyDenied("provider_endpoint_denied", str(provider)[:100])
        # A route must unambiguously describe the physical destination and
        # data handling contract. Never infer these from model request fields.
        if len(route.regions) != 1 or len(route.data_classes) != 1:
            raise PolicyDenied("provider_route_ambiguous", str(provider))
        credential_ref = _actual_provider_credential_ref(agent, route)
        data_class = _effective_request_data_class(guard)
        guard.authorize_provider(ProviderRequest(
            provider=provider, region=route.regions[0], data_class=data_class,
            egress=route.max_egress, retention=route.max_retention,
            training=route.training, credential_ref=credential_ref,
        ))

    original_perform = turn_api_call.perform_api_call

    @functools.wraps(original_perform)
    def guarded_perform(agent: Any, *args: Any, **kwargs: Any) -> Any:
        authorize_agent_provider(agent)
        token = _ACTIVE_AGENT.set(agent)
        try:
            return original_perform(agent, *args, **kwargs)
        finally:
            _ACTIVE_AGENT.reset(token)

    installation._remember(turn_api_call, "perform_api_call", guarded_perform)
    installation._remember(conversation_loop, "perform_api_call", guarded_perform)

    original_middleware = middleware.run_llm_execution_middleware

    @functools.wraps(original_middleware)
    def guarded_llm_execution(request: Any, next_call: Any, **context: Any) -> Any:
        agent = _ACTIVE_AGENT.get()
        if agent is None:
            raise PolicyDenied("provider_context_missing")
        authorize_agent_provider(agent)  # before any callback
        def guarded_next(payload: Any) -> Any:
            authorize_agent_provider(agent)  # after callbacks may switch routes
            return next_call(payload)
        return original_middleware(request, guarded_next, **context)

    installation._remember(middleware, "run_llm_execution_middleware", guarded_llm_execution)

    original_agent_execution = tool_executor._run_agent_tool_execution_middleware

    @functools.wraps(original_agent_execution)
    def guarded_agent_execution(agent: Any, *, function_name: str,
                                function_args: dict, effective_task_id: str,
                                tool_call_id: str, execute: Callable[..., Any],
                                **kwargs: Any) -> Any:
        def authorized_execute(final_args: dict[str, Any]) -> Any:
            if function_name in _META_READ_TOOLS:
                return execute(final_args)
            if function_name == _BRIDGE_TOOL:
                denied = _precheck_bridge(guard, final_args, effective_task_id)
                return denied if denied is not None else execute(final_args)
            try:
                canonical, checked = guard.authorize_tool_call(
                    function_name, final_args, caller_task_id=effective_task_id,
                    consume_approval=True,
                )
                digest = _call_digest(canonical, checked)
            except PolicyDenied as exc:
                return _denied_result(exc.reason, exc.detail)
            except (SecurityError, TypeError, ValueError):
                return _denied_result("security_contract_invalid")
            token = _AUTHORIZED_CALL.set((canonical, digest))
            try:
                return execute(checked)
            finally:
                _AUTHORIZED_CALL.reset(token)

        return original_agent_execution(
            agent, function_name=function_name, function_args=function_args,
            effective_task_id=effective_task_id, tool_call_id=tool_call_id,
            execute=authorized_execute, **kwargs,
        )

    installation._remember(tool_executor, "_run_agent_tool_execution_middleware", guarded_agent_execution)

    original_handle = model_tools.handle_function_call

    @functools.wraps(original_handle)
    def guarded_handle(
        function_name: str,
        function_args: Mapping[str, Any] | None,
        task_id: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # Tool-search metadata can reveal names/schemas but cannot perform the
        # operation.  The bridge itself is pre-checked below and every resolved
        # call is authorized again at the actual local/connector seam.
        if function_name in _META_READ_TOOLS:
            return original_handle(function_name, function_args, task_id, *args, **kwargs)

        if function_name == _BRIDGE_TOOL:
            denied = _precheck_bridge(guard, function_args, task_id)
            if denied is not None:
                return denied
            return original_handle(function_name, function_args, task_id, *args, **kwargs)

        try:
            _, checked = guard.authorize_tool_call(
                function_name,
                function_args,
                caller_task_id=task_id,
                consume_approval=False,
            )
        except PolicyDenied as exc:
            return _denied_result(exc.reason, exc.detail)
        except SecurityError:
            return _denied_result("security_contract_invalid")

        return original_handle(function_name, checked, task_id, *args, **kwargs)

    installation._remember(model_tools, "handle_function_call", guarded_handle)

    # Patch the class, not only the singleton instance: any alternate ToolRegistry
    # dispatch in this process is subject to the same host grant.  Only the
    # canonical Hermes singleton has meaningful registered tools, but this also
    # closes a trivial "call the class method directly" bypass.
    original_registry_dispatch = ToolRegistry.dispatch

    @functools.wraps(original_registry_dispatch)
    def guarded_registry_dispatch(
        self: Any,
        name: str,
        args: Mapping[str, Any] | None,
        *call_args: Any,
        **kwargs: Any,
    ) -> Any:
        try:
            canonical = guard.canonical_tool(name)
            digest = _call_digest(canonical, args)
            already = _AUTHORIZED_CALL.get()
            _, checked = guard.authorize_tool_call(
                canonical,
                args,
                caller_task_id=kwargs.get("task_id"),
                consume_approval=(already != (canonical, digest)),
            )
        except PolicyDenied as exc:
            return _denied_result(exc.reason, exc.detail)
        except (SecurityError, TypeError, ValueError):
            return _denied_result("security_contract_invalid")
        return original_registry_dispatch(self, name, checked, *call_args, **kwargs)

    installation._remember(ToolRegistry, "dispatch", guarded_registry_dispatch)

    # Connectors bypass ToolRegistry.dispatch in Hermes v0.21.5.  Patch both the
    # public package alias used by model_tools and the defining module symbol so
    # direct imports cannot evade the policy.
    original_connector_call = connector_dispatch_module.dispatch_connector_call

    @functools.wraps(original_connector_call)
    def guarded_connector_call(
        name: str,
        arguments: Mapping[str, Any] | None,
        tool_call_id: str | None = None,
    ) -> Any:
        try:
            canonical = guard.canonical_tool(name)
            digest = _call_digest(canonical, arguments)
            already = _AUTHORIZED_CALL.get()
            _, checked = guard.authorize_tool_call(
                canonical,
                arguments,
                caller_task_id=guard.grant.identity.task_id,
                consume_approval=(already != (canonical, digest)),
            )
        except PolicyDenied as exc:
            return _denied_result(exc.reason, exc.detail)
        except (SecurityError, TypeError, ValueError):
            return _denied_result("security_contract_invalid")
        return original_connector_call(name, checked, tool_call_id)

    installation._remember(
        connector_dispatch_module, "dispatch_connector_call", guarded_connector_call
    )
    installation._remember(connectors, "dispatch_connector_call", guarded_connector_call)

    # Sanity: the singleton must now resolve the patched class method.
    if getattr(registry.dispatch, "__func__", None) is not guarded_registry_dispatch:
        installation.uninstall()
        raise HermesCompatibilityError("failed to install registry dispatch guard")

    return installation


def _precheck_bridge(
    guard: InvocationGuard,
    function_args: Mapping[str, Any] | None,
    task_id: str | None,
) -> str | None:
    """Resolve bridge entries and deny any impossible underlying grant early.

    The precheck never consumes an approval.  Actual execution recursively
    reaches guarded_handle and/or guarded connector dispatch, where the exact
    effective post-middleware arguments are checked and approval is consumed.
    """
    try:
        from tools.connectors import CONNECTOR_BATCH_SENTINEL
        from tools.tool_search import resolve_underlying_call

        underlying, resolved_args, error = resolve_underlying_call(
            dict(function_args or {})
        )
    except Exception as exc:
        return _denied_result("bridge_resolution_failed", type(exc).__name__)
    if error or not underlying:
        return None

    candidates: list[tuple[str, Mapping[str, Any]]] = []
    if underlying == CONNECTOR_BATCH_SENTINEL:
        calls = resolved_args.get("calls") if isinstance(resolved_args, Mapping) else None
        if not isinstance(calls, list):
            return _denied_result("bridge_resolution_failed", "connector batch malformed")
        for entry in calls:
            if not isinstance(entry, Mapping):
                return _denied_result("bridge_resolution_failed", "connector entry malformed")
            name, args = entry.get("name"), entry.get("arguments", {})
            if not isinstance(name, str) or not isinstance(args, Mapping):
                return _denied_result("bridge_resolution_failed", "connector entry malformed")
            candidates.append((name, args))
    else:
        candidates.append((underlying, resolved_args))

    for name, args in candidates:
        try:
            guard.authorize_tool(
                name,
                args,
                caller_task_id=task_id,
                consume_approval=False,
            )
        except PolicyDenied as exc:
            return _denied_result(exc.reason, exc.detail)
        except (SecurityError, TypeError, ValueError):
            return _denied_result("security_contract_invalid")
    return None


__all__ = [
    "GuardInstallation",
    "HermesCompatibilityError",
    "inspect_hermes_security_surface",
    "install_hermes_guard",
]
