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


def install_private_sdk_credentials(installation, policy):
    """Keep the SDK's credential selection and pool bookkeeping inside one view."""
    if policy.auth_sha256 is None:
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
