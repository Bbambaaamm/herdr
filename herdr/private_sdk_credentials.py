"""Private Nous SDK auth transactions over an authenticated immutable profile.

The SDK may update pool bookkeeping in this invocation's memory. It cannot
persist credentials, import another profile, refresh a token, or contact an
auth endpoint. Actual inference still uses the ordinary guarded SDK client.
"""
from contextlib import contextmanager
from copy import deepcopy
import math
import sys
import threading

from .security import PolicyDenied

_SECRETS = frozenset({"access_token", "refresh_token", "agent_key", "api_key", "token", "anon_token", "client_secret", "id_token", "device_code"})
_URLS = frozenset({"base_url", "inference_base_url", "portal_base_url"})


def _need(value, code):
    if not value:
        raise PolicyDenied(code)


def _values(value, names):
    result = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in names and item not in (None, ""):
                _need(type(item) is str, "private_sdk_auth_value_invalid")
                result.add(item)
            result.update(_values(item, names))
    elif isinstance(value, list):
        for item in value:
            result.update(_values(item, names))
    return result


class PrivateSDKAuthView:
    """One isolated, serialized view; the approved auth.json is never written."""

    def __init__(self, policy, providers):
        self.policy = policy
        self.path = policy.profile_home / "auth.json"
        self.providers = frozenset(providers)
        self.lock = threading.RLock()
        self.closed = False
        source = policy.read_auth_store()
        _need(type(source) is dict, "private_sdk_auth_store_invalid")
        self.store = deepcopy(source)
        for section in ("providers", "credential_pool"):
            values = self.store.get(section, {})
            _need(type(values) is dict, "private_sdk_auth_store_invalid")
            self.store[section] = {name: deepcopy(value) for name, value in values.items()
                                   if name in self.providers}
        if self.store.get("active_provider") not in self.providers:
            self.store.pop("active_provider", None)
        self.secrets = _values(self.store, _SECRETS)
        self.urls = _values(self.store, _URLS)

    def _check(self, path=None):
        _need(not self.closed, "private_sdk_auth_view_closed")
        self.policy.reassert()
        _need(path is None or path == self.path,
              "private_sdk_auth_store_path_changed")
        # Read the sealed bytes again, not a mutable SDK cache.
        self.policy.read_auth_store()

    def close(self):
        with self.lock:
            self.closed = True
            self.store.clear()
            self.secrets.clear()
            self.urls.clear()

    def _validate(self, value):
        _need(type(value) is dict, "private_sdk_auth_store_invalid")
        for section in ("providers", "credential_pool"):
            fields = value.get(section, {})
            _need(type(fields) is dict and set(fields) <= self.providers,
                  "private_sdk_auth_provider_changed")
        active = value.get("active_provider")
        _need(active is None or active in self.providers,
              "private_sdk_auth_provider_changed")
        _need(_values(value, _SECRETS) <= self.secrets,
              "private_sdk_auth_credential_changed")
        _need(_values(value, _URLS) <= self.urls,
              "private_sdk_auth_endpoint_changed")

    def read(self, auth_file=None):
        from pathlib import Path
        path = None if auth_file is None else Path(auth_file)
        with self.lock:
            self._check(path)
            return deepcopy(self.store)

    def save(self, auth_store, target_path=None):
        from pathlib import Path
        path = None if target_path is None else Path(target_path)
        with self.lock:
            self._check(path)
            self._validate(auth_store)
            self.store = deepcopy(auth_store)
            return self.path

    @contextmanager
    def transaction(self, timeout_seconds=30, *, target_path=None):
        from pathlib import Path
        path = None if target_path is None else Path(target_path)
        _need(type(timeout_seconds) in (int, float) and math.isfinite(timeout_seconds)
              and timeout_seconds >= 0, "private_sdk_auth_timeout_invalid")
        self._check(path)
        acquired = self.lock.acquire(timeout=min(float(timeout_seconds), 30.0))
        _need(acquired, "private_sdk_auth_lock_timeout")
        try:
            self._check(path)
            yield
        finally:
            self.lock.release()

    def global_store(self):
        self._check()
        return {}

    def merge_shared(self, state):
        self._check()
        _need(_values(state, _SECRETS) <= self.secrets,
              "private_sdk_auth_credential_changed")
        return False

    def write_shared(self, state):
        self._check()
        _need(_values(state, _SECRETS) <= self.secrets,
              "private_sdk_auth_credential_changed")
        _need(_values(state, _URLS) <= self.urls,
              "private_sdk_auth_endpoint_changed")


class _NoAuthNetwork:
    def request(self, *args, **kwargs):
        raise PolicyDenied("private_sdk_auth_network_forbidden")

    get = post = put = delete = patch = send = stream = request


@contextmanager
def _no_auth_network(*args, **kwargs):
    yield _NoAuthNetwork()


def _sdk_module(module):
    name = getattr(module, "__name__", "")
    return (name.startswith(("hermes_cli.", "agent."))
            or name in {"cli", "run_agent"})


def _replace_aliases(installation, auth, name, replacement):
    """Replace the definition and exact cached SDK aliases, restoring all on exit."""
    original = getattr(auth, name)
    owner = sys.modules.get(getattr(original, "__module__", ""))
    targets = [auth]
    if owner is not None and _sdk_module(owner):
        targets.append(owner)
    targets.extend(module for module in tuple(sys.modules.values())
                   if module is not None and _sdk_module(module))
    seen = set()
    # auth may re-export a lazily loaded fragment through __getattr__.
    installation._remember(auth, name, replacement)
    seen.add((id(auth), name))
    for module in targets:
        for alias, value in tuple(vars(module).items()):
            key = (id(module), alias)
            if key not in seen and value is original:
                installation._remember(module, alias, replacement)
                seen.add(key)


class CredentiallessReferenceAuthView:
    """Deny-only SDK auth view bound to the ORIGINAL admitted host reference.

    Empty store/state is an enforced absence of SDK auth access, not evidence
    of isolation, provider readiness, a credential or host-effect authority.
    Native inference keeps the independent original WorkAuthority transport.
    """
    def __init__(self, installation, policy, binding):
        self.guard = installation.guard
        self.policy, self.binding = policy, binding
        self.grant = self.guard.grant
        self.grant_hash = self.grant.hash
        self.identity = self.grant.identity
        self.closed = False
        self._check()

    def _check(self):
        from .security import InvocationGuard
        from .work_contract_host import WorkInvocationGuard
        from .private_profile_namespace import PrivateSDKPolicy
        from agent.host_reference import HostCredentialReference
        grant, binding = self.guard.grant, self.binding
        _need(not self.closed and type(self.guard) in (InvocationGuard, WorkInvocationGuard)
              and type(self.policy) is PrivateSDKPolicy and type(binding) is HostCredentialReference
              and getattr(self.guard, "_admitted_host_reference", None) is binding
              and grant is self.grant and grant.identity == self.identity
              and grant.hash == self.grant_hash and grant.is_active()
              and grant.runtime_assurance.sandbox_verified is True
              and grant.runtime_assurance.credentials_isolated is True
              and self.policy.auth_sha256 is None
              and self.policy.projection_sha256 is not None,
              "credentialless_reference_bootstrap_binding_required")
        _need(frozenset(grant.scope.providers) == {"nous"}
              and len(grant.provider_routes) == len(grant.credential_refs) == 1,
              "credentialless_reference_single_route_required")
        route = grant.provider_routes[0]
        _need(route.provider == binding.provider == "nous"
              and route.base_url == binding.endpoint == "https://inference-api.nousresearch.com/v1"
              and route.api_mode == binding.api_mode == "chat_completions"
              and tuple(route.credential_refs) == tuple(grant.credential_refs) == (binding.credential_ref,)
              and binding.credential_ref == "pool:nous:" + binding.entry_id
              and binding.model.endswith(":free")
              and binding.profile_sha256 == self.policy.profile_sha256
              and binding.projection_sha256 == self.policy.projection_sha256
              and binding.grant_hash == self.grant_hash
              and binding.workspace == grant.workspace_root
              and binding.fence == str(grant.identity.fencing_token)
              and binding.lineage == grant.identity.parent_task_id,
              "credentialless_reference_route_or_profile_changed")
        self.policy.reassert()
        self.policy.verify_config_path(self.policy.profile_home / "config.yaml")

    def read(self, auth_file=None):
        from pathlib import Path
        self._check()
        _need(auth_file is None or Path(auth_file) == self.policy.profile_home / "auth.json",
              "credentialless_reference_auth_path_changed")
        return {}  # No SDK auth.json is made up, opened, cached or persisted.

    def provider_state(self, auth_store, provider_id):
        self._check()
        _need(type(auth_store) is dict and not auth_store and provider_id == "nous",
              "credentialless_reference_auth_state_denied")
        return None

    def provider_state_with_source(self, auth_store, provider_id):
        return self.provider_state(auth_store, provider_id), None

    def deny(self, *_args, **_kwargs):
        self._check()
        raise PolicyDenied("credentialless_reference_auth_effect_forbidden")

    def close(self):
        self.closed = True


def _install_credentialless_reference(installation, policy, binding):
    """Block legacy identity/OAuth/global-store effects BEFORE native cmd_chat.

    No SDK bytes, ready booleans, provider resolver or native request authority
    are changed. Original config.provider readiness and actual typed reference
    constructor remain independent. A missing/changed native surface denies.
    """
    from hermes_cli import auth, auth_nous, anon_auth
    view = CredentiallessReferenceAuthView(installation, policy, binding)
    replacements = {
        (auth, "_load_auth_store"): view.read,
        (auth, "_load_provider_state"): view.provider_state,
        (auth, "_load_provider_state_with_source"): view.provider_state_with_source,
    }
    for owner, names in (
        (auth, ("_load_global_auth_store", "_save_auth_store", "_auth_store_lock",
                "_nous_shared_store_lock", "_merge_shared_nous_oauth_state", "_write_shared_nous_state",
                "get_auth_status", "resolve_nous_runtime_credentials", "_refresh_nous_or_quarantine")),
        (auth_nous, ("_nous_http_client",)),
        (anon_auth, ("ensure_portal_identity",)),
    ):
        for name in names:
            replacements[owner, name] = view.deny
    # Validate the complete pinned surface before replacing any attribute.
    for (owner, name) in replacements:
        _need(callable(getattr(owner, name, None)), "credentialless_reference_auth_surface_changed")
    for name, value in (("_RESOLVE_TOKEN_CACHE", {}), ("_nous_auth_status_cache", None),
                        ("_global_auth_store_cache", None)):
        if name in vars(auth):
            installation._remember(auth, name, value)
    for (owner, name), replacement in replacements.items():
        _replace_aliases(installation, owner, name, replacement)
    installation.finalizers.append(view.close)
    return view


def install_private_sdk_credentials(installation, policy):
    """Keep the SDK's credential selection and pool bookkeeping inside one view."""
    if policy.auth_sha256 is None:
        binding = getattr(installation.guard, "_admitted_host_reference", None)
        if binding is not None:
            return _install_credentialless_reference(installation, policy, binding)
        return None  # Existing configuration-only / zero-provider profiles.
    providers = frozenset(installation.guard.grant.scope.providers)
    if providers != {"nous"}:
        return None  # Other provider routes retain their existing behavior.
    from hermes_cli import auth, auth_nous

    view = PrivateSDKAuthView(policy, providers)
    replacements = {
        "_load_auth_store": view.read,
        "_save_auth_store": view.save,
        "_auth_store_lock": view.transaction,
        "_load_global_auth_store": view.global_store,
        "_nous_shared_store_lock": view.transaction,
        "_merge_shared_nous_oauth_state": view.merge_shared,
        "_write_shared_nous_state": view.write_shared,
        "_nous_http_client": _no_auth_network,
        "_refresh_nous_or_quarantine": _NoAuthNetwork().request,
    }
    owners = {name: (auth_nous if name == "_nous_http_client" else auth)
              for name in replacements}
    for name, owner in owners.items():
        _need(callable(getattr(owner, name, None)), "private_sdk_auth_surface_changed")
    for name, value in (("_RESOLVE_TOKEN_CACHE", {}),
                        ("_nous_auth_status_cache", None),
                        ("_global_auth_store_cache", None)):
        if name in vars(auth):
            installation._remember(auth, name, value)
    for name, replacement in replacements.items():
        _replace_aliases(installation, owners[name], name, replacement)

    original = auth.resolve_nous_runtime_credentials

    def resolve_runtime(*args, **kwargs):
        view._check()
        _need(not kwargs.get("force_refresh") and not kwargs.get("stale_access_token"),
              "private_sdk_auth_refresh_forbidden")
        return original(*args, **kwargs)

    _replace_aliases(installation, auth, "resolve_nous_runtime_credentials", resolve_runtime)
    installation.finalizers.append(view.close)
    return view
