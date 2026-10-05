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

import os

import base64
import difflib
import functools
import fnmatch
import time
import inspect
import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from herdr.file_authority import FileAuthorityError, RootFDWorkspace
from herdr.security import InvocationGuard, PolicyDenied, SecurityError, ProviderRequest, canonical_digest


class _PolicyFileOps:
    """Hermes FileOperations facade backed by pinned nofollow root FDs."""

    def __init__(self, workspace: RootFDWorkspace, delegate: Any, common: Any, patch_parser: Any) -> None:
        self._workspace = workspace
        self._delegate = delegate
        self._common = common
        self._patch_parser = patch_parser

    def __getattr__(self, name: str) -> Any:
        if name not in {"env","_add_line_numbers"}:
            raise PolicyDenied("file_operation_unattested",name[:64])
        return getattr(self._delegate, name)

    def read_file_raw(self, path: str) -> Any:
        try:
            content = self._workspace.read_text(path)
        except (OSError, FileAuthorityError) as exc:
            return self._common.ReadResult(error=str(exc))
        return self._common.ReadResult(
            content=content, total_lines=len(content.splitlines()),
            file_size=len(content.encode("utf-8")),
        )

    def read_file_bytes(self, path: str, max_bytes: int | None = None) -> Any:
        limit = self._workspace_max_file_bytes() if max_bytes is None else max_bytes
        if type(limit) is not int or limit < 0:
            return self._common.ReadResult(error="invalid binary read limit")
        limit=min(limit,self._workspace_max_file_bytes())
        try:
            raw = self._workspace.read_bytes(path, limit=limit)
        except (OSError, FileAuthorityError) as exc:
            return self._common.ReadResult(error=str(exc))
        return self._common.ReadResult(
            base64_content=base64.b64encode(raw).decode("ascii"),
            file_size=len(raw),
            is_binary=True,
        )

    @staticmethod
    def _workspace_max_file_bytes() -> int:
        from herdr.file_authority import MAX_FILE_BYTES
        return MAX_FILE_BYTES

    def read_file(self, path: str, offset: int = 1, limit: int = 2000) -> Any:
        result = self.read_file_raw(path)
        if result.error:
            return result
        if type(offset) is not int or type(limit) is not int or offset < 1 or limit < 1:
            return self._common.ReadResult(error="invalid read pagination")
        lines = result.content.splitlines(keepends=True)
        page = "".join(lines[offset - 1:offset - 1 + limit])
        numbered = self._delegate._add_line_numbers(page, offset)
        return self._common.ReadResult(
            content=numbered, total_lines=len(lines), file_size=result.file_size,
            truncated=(offset - 1 + limit) < len(lines),
        )

    def search(self,pattern,path=".",target="content",file_glob=None,limit=50,offset=0,
               output_mode="content",context=0,order="discovery"):
        """No shell/backend delegation. This attested profile supports literals
        and file globs; regex/context profiles require separate host admission.
        """
        common=self._common
        if (not isinstance(pattern,str) or not 0<len(pattern)<=1024 or
            type(limit) is not int or not 1<=limit<=200 or type(offset) is not int or not 0<=offset<=1000
            or target not in {"content","files"} or output_mode not in {"content","files_only","count"}
            or type(context) is not int or context!=0 or order!="discovery" or file_glob is not None and (not isinstance(file_glob,str) or len(file_glob)>256)):
            return common.SearchResult(error="unsupported bounded policy-mode search profile")
        if target=="content" and any(x in pattern for x in "[]()*+?{}|^$\\"):
            return common.SearchResult(error="policy-mode search supports literal content; regex needs an admitted search profile")
        # A regex dot is also unsupported rather than silently changed to literal.
        if target=="content" and "." in pattern:
            return common.SearchResult(error="policy-mode search supports literal content; regex dot is unsupported")
        result=common.SearchResult();total_bytes=0;deadline=time.monotonic()+2
        try:
            paths=self._workspace.list_regular_files(path,deadline=deadline)
            matches=[];files=[];counts={}
            for name in paths:
                if time.monotonic()>deadline: raise FileAuthorityError("search elapsed bound exceeded")
                if file_glob and not fnmatch.fnmatchcase(name,file_glob) and not fnmatch.fnmatchcase(Path(name).name,file_glob): continue
                if target=="files":
                    if fnmatch.fnmatchcase(name,pattern) or fnmatch.fnmatchcase(Path(name).name,pattern): files.append(name)
                    continue
                raw=self._workspace.read_bytes(name,limit=524288)
                total_bytes+=len(raw)
                if total_bytes>8388608: raise FileAuthorityError("search bytes exceed bound")
                try: text=raw.decode("utf-8")
                except UnicodeDecodeError: continue
                hit=0
                for number,line in enumerate(text.splitlines(),1):
                    if pattern in line:
                        hit+=1
                        if output_mode=="content":
                            if len(line.encode())>4096: raise FileAuthorityError("search line exceeds bound")
                            matches.append(common.SearchMatch(name,number,line))
                if hit: counts[name]=hit;files.append(name)
                if sum(len(x.content.encode()) for x in matches)>262144:
                    raise FileAuthorityError("search output exceeds bound")
            result.total_count=len(files) if target=="files" or output_mode=="files_only" else sum(counts.values())
            if target=="files" or output_mode=="files_only": result.files=files[offset:offset+limit]
            elif output_mode=="count": result.counts=dict(list(counts.items())[offset:offset+limit])
            else: result.matches=matches[offset:offset+limit]
            result.truncated=result.total_count>offset+limit
            if result.truncated: result.limit_reason="pagination"
            return result
        except (OSError,FileAuthorityError) as exc:
            return common.SearchResult(error=str(exc))

    def write_file(self, path: str, content: str, pre_content: str | None = None) -> Any:
        try:
            count, digest = self._workspace.write_text(path, content, expected_content=pre_content)
        except (OSError, FileAuthorityError) as exc:
            return self._common.WriteResult(error=str(exc))
        return self._common.WriteResult(
            bytes_written=count, dirs_created=bool(Path(path).parent), verified=True,
            _content_sha256=digest,
        )

    def patch_replace(self, path: str, old_string: str, new_string: str, replace_all: bool = False) -> Any:
        read = self.read_file_raw(path)
        if read.error:
            return self._common.PatchResult(error=read.error)
        from tools.fuzzy_match import fuzzy_find_and_replace, is_already_applied
        updated, count, _strategy, error = fuzzy_find_and_replace(
            read.content, old_string, new_string, replace_all
        )
        if error or count == 0:
            if is_already_applied(read.content, old_string, new_string):
                return self._common.PatchResult(
                    success=True, no_change=True, note="edit already applied"
                )
            return self._common.PatchResult(error=error or "old_string not found")
        write = self.write_file(path, updated, pre_content=read.content)
        if write.error:
            return self._common.PatchResult(error=write.error)
        diff = "".join(difflib.unified_diff(
            read.content.splitlines(keepends=True), updated.splitlines(keepends=True),
            fromfile=f"a/{path}", tofile=f"b/{path}",
        ))
        return self._common.PatchResult(success=True, diff=diff, files_modified=[path])

    def patch_v4a(self, patch_content: str) -> Any:
        operations, error = self._patch_parser.parse_v4a_patch(patch_content)
        if error:
            return self._common.PatchResult(error=error)

        if any(getattr(getattr(op,"operation",None),"value",None)=="update" for op in operations):
            return self._common.PatchResult(error="conditional replacement unavailable on shared workspace")

        # V4A Add is create-only. The parser's generic apply path calls
        # write_file for both Add and Update, so interpose only the first write
        # for each Add target with an atomic no-clobber create.
        add_rows = [
            op.file_path for op in operations
            if getattr(getattr(op, "operation", None), "value", None) == "add"
        ]
        canonical_adds = [os.path.normpath(path) for path in add_rows]
        if len(canonical_adds) != len(set(canonical_adds)):
            return self._common.PatchResult(error="duplicate V4A Add target")
        add_targets = set(add_rows)
        parent = self

        class _V4AApplyOps:
            def __getattr__(self, name: str) -> Any:
                return getattr(parent, name)

            def write_file(
                self, path: str, content: str, pre_content: str | None = None
            ) -> Any:
                if path in add_targets:
                    add_targets.remove(path)
                    try:
                        count, digest = parent._workspace.create_text(path, content)
                    except (OSError, FileAuthorityError) as exc:
                        return parent._common.WriteResult(error=str(exc))
                    return parent._common.WriteResult(
                        bytes_written=count, verified=True, _content_sha256=digest
                    )
                return parent.write_file(path, content, pre_content=pre_content)

        return self._patch_parser.apply_v4a_operations(operations, _V4AApplyOps())

    def delete_file(self, path: str) -> Any:
        try:
            self._workspace.delete_file(path)
            return self._common.WriteResult(verified=True)
        except (OSError, FileAuthorityError) as exc:
            return self._common.WriteResult(error=str(exc))

    def move_file(self, source: str, destination: str) -> Any:
        try:
            self._workspace.move_file(source, destination)
            return self._common.WriteResult(verified=True)
        except (OSError, FileAuthorityError) as exc:
            return self._common.WriteResult(error=str(exc))


class HermesCompatibilityError(RuntimeError):
    """Installed Hermes dispatch contract is not the versioned surface we audited."""


_AUTHORIZED_CALL: ContextVar[tuple[str, str, str] | None] = ContextVar(
    "herdr_authorized_call", default=None
)
_ACTIVE_AGENT: ContextVar[Any | None] = ContextVar("herdr_active_provider_agent", default=None)
_META_READ_TOOLS = frozenset({"tool_search", "tool_describe"})
_BRIDGE_TOOL = "tool_call"
_POLICY_ENV = {
    "HERMES_SAFE_MODE": "1",
    "HERMES_ENABLE_PROJECT_PLUGINS": "0",
}


def _reassert_policy_environment() -> None:
    import os
    for key, value in _POLICY_ENV.items():
        os.environ[key] = value


def _require_local_backend(env_type: Any, env: Any | None = None) -> None:
    if env_type != "local":
        raise PolicyDenied("process_backend_unattested", str(env_type)[:64])
    if env is not None:
        observed = getattr(env, "env_type", None)
        if observed != "local":
            raise PolicyDenied("process_backend_unattested", str(observed)[:64])


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
    return str(value or "")


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
        from hermes_cli import env_loader, middleware, plugins
        from agent import auxiliary_client, turn_api_call, conversation_loop, tool_executor
        from agent.client_lifecycle import ClientLifecycleMixin
        from tools import code_execution_tool, connectors, file_tools, file_tools_read_tracking, read_extract, terminal_tool, terminal_tool_backends
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
    if not callable(getattr(env_loader, "_load_dotenv_with_fallback", None)) or not callable(
        getattr(env_loader, "load_hermes_dotenv", None)
    ):
        raise HermesCompatibilityError("dotenv policy seam unavailable")
    if not isinstance(getattr(plugins, "PluginManager", None), type) or not callable(
        getattr(plugins.PluginManager, "discover_and_load", None)
    ):
        raise HermesCompatibilityError("plugin discovery seam unavailable")
    if not callable(getattr(terminal_tool, "_get_env_config", None)) or not callable(
        getattr(terminal_tool, "_acquire_env", None)
    ):
        raise HermesCompatibilityError("terminal backend seam unavailable")
    if not callable(getattr(code_execution_tool, "_get_or_create_env", None)):
        raise HermesCompatibilityError("execute_code backend seam unavailable")
    if not callable(getattr(terminal_tool_backends, "_create_environment", None)):
        raise HermesCompatibilityError("terminal environment creation seam unavailable")
    if not callable(getattr(file_tools, "_get_file_ops", None)):
        raise HermesCompatibilityError("file operations seam unavailable")
    if not all(callable(getattr(file_tools_read_tracking, name, None))
               for name in ("_file_metadata", "_file_version")):
        raise HermesCompatibilityError("file read-tracking seam unavailable")
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
        "dotenv_policy_locked": True,
        "dynamic_plugins_disabled_under_guard": True,
        "local_process_backend_enforced": True,
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
    finalizers: list[Callable[[], Any]] = field(default_factory=list)
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
        for finalizer in reversed(self.finalizers):
            try:
                finalizer()
            except Exception:
                pass
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
    from hermes_cli import env_loader, middleware, plugins
    from tools import code_execution_tool, connectors, file_tools, file_tools_read_tracking, read_extract, terminal_tool, terminal_tool_backends
    from tools.connectors import dispatch as connector_dispatch_module
    from tools.file_tools_paths import _resolve_path_for_task
    from tools.registry import ToolRegistry, registry

    aliases = dict(surface["legacy_aliases"])
    guard.aliases = aliases
    guard.path_resolver = lambda value, task_id: _resolve_path_for_task(
        value, task_id
    )
    installation = GuardInstallation(guard=guard, surface=surface)

    # Pin local file authority to the granted directory inodes. Hermes may keep
    # its higher-level formatting/search helpers, but physical read/write/patch
    # goes through RootFDWorkspace so a path/symlink swap after authorization
    # cannot redirect an open or rename outside the signed roots.
    file_rules = {rule.tool: rule for rule in getattr(guard.grant, "tool_rules", ())}
    file_roots = {
        root
        for tool in ("read_file", "write_file", "patch", "search_files")
        for root in getattr(file_rules.get(tool), "allowed_roots", ())
    }
    file_workspace = RootFDWorkspace(file_roots) if file_roots else None
    if file_workspace is not None:
        from tools import file_operations_common, patch_parser
        original_get_file_ops = file_tools._get_file_ops
        proxies: dict[int, _PolicyFileOps] = {}

        @functools.wraps(original_get_file_ops)
        def guarded_get_file_ops(task_id: str = "default") -> Any:
            # Check the configured backend BEFORE original_get_file_ops can
            # provision/connect a Docker/SSH/Modal/plugin environment.
            config = terminal_tool._get_env_config()
            _require_local_backend(config.get("env_type"))
            delegate = original_get_file_ops(task_id)
            env = getattr(delegate, "env", None)
            _require_local_backend(getattr(env, "env_type", "local"), env)
            key = id(delegate)
            proxy = proxies.get(key)
            if proxy is None:
                proxy = proxies[key] = _PolicyFileOps(
                    file_workspace, delegate, file_operations_common, patch_parser
                )
            return proxy

        installation._remember(file_tools, "_get_file_ops", guarded_get_file_ops)

        def guarded_file_metadata(path: str) -> tuple | None:
            try:
                return file_workspace.file_metadata(path)
            except (OSError, FileAuthorityError):
                return None

        def guarded_file_version(path: str) -> tuple | None:
            try:
                return file_workspace.file_version(path)
            except (OSError, FileAuthorityError):
                return None

        # Hermes imports these functions into file_tools at module import time,
        # while the tracking module also calls its own globals. Patch both
        # references so dedup/staleness hashing cannot reopen a raced symlink.
        installation._remember(file_tools, "_file_metadata", guarded_file_metadata)
        installation._remember(file_tools, "_file_version", guarded_file_version)
        installation._remember(
            file_tools_read_tracking, "_file_metadata", guarded_file_metadata
        )
        installation._remember(
            file_tools_read_tracking, "_file_version", guarded_file_version
        )
        # The original special-file precheck follows pathname symlinks with
        # os.stat. RootFDWorkspace uses O_NONBLOCK+O_NOFOLLOW and rejects
        # non-regular targets at the actual open seam, so avoid that unsafe
        # preliminary dereference in policy mode.
        installation._remember(file_tools, "_special_file_kind", lambda path: None)
        installation.finalizers.append(file_workspace.close)

    # Policy suppression is authority, not user config. Hermes reloads profile
    # dotenv files with override=True after profile selection, so reassert the
    # protected values after every dotenv layer and disable plugin discovery at
    # the manager method itself. A .env cannot turn policy mode back off.
    _reassert_policy_environment()
    original_dotenv_layer = env_loader._load_dotenv_with_fallback
    @functools.wraps(original_dotenv_layer)
    def guarded_dotenv_layer(*args: Any, **kwargs: Any) -> Any:
        try:
            return original_dotenv_layer(*args, **kwargs)
        finally:
            _reassert_policy_environment()
    installation._remember(env_loader, "_load_dotenv_with_fallback", guarded_dotenv_layer)

    original_dotenv_load = env_loader.load_hermes_dotenv
    @functools.wraps(original_dotenv_load)
    def guarded_dotenv_load(*args: Any, **kwargs: Any) -> Any:
        try:
            return original_dotenv_load(*args, **kwargs)
        finally:
            _reassert_policy_environment()
    installation._remember(env_loader, "load_hermes_dotenv", guarded_dotenv_load)

    def disabled_plugin_discovery(self: Any, force: bool = False) -> None:
        _reassert_policy_environment()
        self._discovered = True
        return None
    installation._remember(plugins.PluginManager, "discover_and_load", disabled_plugin_discovery)

    # #76 only attests the local process backend. Model-visible terminal and
    # execute_code must not escape to SSH/Docker/Modal/Daytona/plugin backends.
    original_terminal_config = terminal_tool._get_env_config
    @functools.wraps(original_terminal_config)
    def guarded_terminal_config() -> dict[str, Any]:
        config = dict(original_terminal_config())
        config["env_type"] = "local"
        return config
    installation._remember(terminal_tool, "_get_env_config", guarded_terminal_config)

    original_acquire_env = terminal_tool._acquire_env
    @functools.wraps(original_acquire_env)
    def guarded_acquire_env(plan: Any, task_id: Any) -> Any:
        _require_local_backend(getattr(plan, "env_type", None))
        env = original_acquire_env(plan, task_id)
        _require_local_backend(getattr(plan, "env_type", None), env)
        return env
    installation._remember(terminal_tool, "_acquire_env", guarded_acquire_env)

    # Guard the shared physical backend constructor itself. execute_code imports
    # this symbol immediately before provisioning; rejecting here prevents
    # Docker/SSH/Modal/Daytona/plugin setup, network use, or credential lookup
    # from occurring before the policy verdict.
    original_create_environment = terminal_tool_backends._create_environment
    @functools.wraps(original_create_environment)
    def guarded_create_environment(env_type: str, *args: Any, **kwargs: Any) -> Any:
        _require_local_backend(env_type)
        env = original_create_environment(env_type, *args, **kwargs)
        _require_local_backend(env_type, env)
        return env
    installation._remember(
        terminal_tool_backends, "_create_environment", guarded_create_environment
    )

    original_code_env = code_execution_tool._get_or_create_env
    @functools.wraps(original_code_env)
    def guarded_code_env(task_id: str) -> Any:
        env, env_type = original_code_env(task_id)
        _require_local_backend(env_type, env)
        return env, env_type
    installation._remember(code_execution_tool, "_get_or_create_env", guarded_code_env)

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
        # v0.21.5 Relay may defer stream_factory until first iteration, after
        # middleware/fallback state has changed. Reproduce the audited wrapper
        # but put authorization immediately around the physical create().
        _authorize_aux_transport(guard, client, provider, api_mode)
        from agent.auxiliary_wire import prepare_chat_messages
        from agent import relay_llm
        from agent.auxiliary_hooks import run_with_aux_hooks

        prepared = prepare_chat_messages(client, kwargs)
        def checked_create(request: dict[str, Any]) -> Any:
            _authorize_aux_transport(guard, client, provider, api_mode)
            transformed = auxiliary_client.bypass_chat_sdk_request_transform(request, client)
            return client.chat.completions.create(**transformed)

        route = auxiliary_client._relay_auxiliary_metadata(provider=provider, api_mode=api_mode)
        if route is None:
            return checked_create(prepared)
        provider_name, fallback_model, metadata = route
        model_name = str(prepared.get("model") or fallback_model)
        return run_with_aux_hooks(
            lambda: relay_llm.stream_current(
                prepared, checked_create, name=provider_name, model_name=model_name,
                finalizer=dict, metadata=metadata,
                completed_response_predicate=lambda value: hasattr(value, "choices"),
            ),
            aux_task=str(metadata.get("auxiliary_task") or ""),
            metadata=metadata,
            client=client,
            kwargs=prepared,
            provider=provider_name,
            model=model_name,
            api_mode=str(metadata.get("api_mode") or ""),
            streaming=True,
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
            token = _AUTHORIZED_CALL.set((guard.grant.hash, canonical, digest))
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
                consume_approval=(already != (guard.grant.hash, canonical, digest)),
            )
        except PolicyDenied as exc:
            return _denied_result(exc.reason, exc.detail)
        except (SecurityError, TypeError, ValueError):
            return _denied_result("security_contract_invalid")
        token = _AUTHORIZED_CALL.set((guard.grant.hash, canonical, _call_digest(canonical, checked)))
        try:
            return original_registry_dispatch(self, name, checked, *call_args, **kwargs)
        finally:
            _AUTHORIZED_CALL.reset(token)

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
                consume_approval=(already != (guard.grant.hash, canonical, digest)),
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

    from herdr.delegation_tool import register_delegation_tool
    try:
        register_delegation_tool(installation, registry, _AUTHORIZED_CALL, _call_digest)
        from herdr.result_submission import register_result_tool
        register_result_tool(installation, registry, _AUTHORIZED_CALL, _call_digest)
        from herdr.work_tool import register_work_tool
        register_work_tool(installation, registry, _AUTHORIZED_CALL, _call_digest)
    except BaseException:
        installation.uninstall()
        raise
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
