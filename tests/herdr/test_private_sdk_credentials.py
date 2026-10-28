"""Private auth metadata stays in memory; SDK inference is not replaced."""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types

import pytest

from herdr import private_profile_namespace as namespace
from herdr.hermes_guard import GuardInstallation
from herdr.private_profile_namespace import PrivateSDKPolicy, PrivateProfileError
from herdr.private_sdk_credentials import (
    PrivateSDKAuthView, _no_auth_network, install_private_sdk_credentials,
)
from herdr.security import PolicyDenied


@pytest.fixture
def snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(namespace, "_HOME", tmp_path)
    monkeypatch.setattr(namespace, "MANAGED_SENTINEL", tmp_path / "managed-sentinel-absent")
    home = tmp_path / ".hermes/profiles/private"
    home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_MANAGED_DIR", str(tmp_path / "managed-sentinel-absent"))
    config = json.dumps({"display": {"cli_multiline_shortcuts": False},
                         "fallback_model": [], "fallback_providers": []}).encode()
    store = {
        "version": 1, "active_provider": "nous",
        "providers": {"nous": {
            "access_token": "approved-access", "agent_key": "approved-access",
            "refresh_token": "approved-refresh", "expires_at": "2030-01-01T00:00:00Z",
            "portal_base_url": "https://portal.nousresearch.com",
            "inference_base_url": "https://inference-api.nousresearch.com/v1",
        }, "unapproved": {"access_token": "not-granted"}},
        "credential_pool": {"nous": [{
            "id": "fixed", "source": "device_code", "access_token": "approved-access",
            "agent_key": "approved-access", "priority": 0, "request_count": 0,
            "inference_base_url": "https://inference-api.nousresearch.com/v1",
        }], "unapproved": [{"access_token": "not-granted"}]},
    }
    auth = json.dumps(store).encode()
    (home / "config.yaml").write_bytes(config)
    (home / "auth.json").write_bytes(auth)
    policy = PrivateSDKPolicy("private", "a" * 64,
                              hashlib.sha256(config).hexdigest(),
                              hashlib.sha256(auth).hexdigest())
    return policy, home, store


def test_auth_is_bound_to_authenticated_member_and_rechecked(snapshot):
    policy, home, _ = snapshot
    assert policy.read_auth_store()["providers"]["nous"]["access_token"] == "approved-access"
    view = PrivateSDKAuthView(policy, {"nous"})
    (home / "auth.json").write_text('{"providers":{}}')
    with pytest.raises(PrivateProfileError, match="private_sdk_auth_changed"):
        view.read()


def test_auth_path_cannot_be_replaced_by_symlink(snapshot, tmp_path):
    policy, home, _ = snapshot
    alias = tmp_path / "alias.json"
    alias.write_bytes((home / "auth.json").read_bytes())
    (home / "auth.json").unlink()
    (home / "auth.json").symlink_to(alias)
    with pytest.raises((OSError, PrivateProfileError)):
        policy.read_auth_store()


def test_private_transactions_update_metadata_without_lock_or_disk_write(snapshot):
    policy, home, _ = snapshot
    before = {name: ((home / name).read_bytes(), (home / name).stat().st_mtime_ns)
              for name in ("auth.json", "config.yaml")}
    view = PrivateSDKAuthView(policy, {"nous"})
    with view.transaction():
        data = view.read()
        data["credential_pool"]["nous"][0]["request_count"] = 7
        assert view.save(data) == home / "auth.json"
    assert view.read()["credential_pool"]["nous"][0]["request_count"] == 7
    assert not (home / "auth.lock").exists()
    assert {name: ((home / name).read_bytes(), (home / name).stat().st_mtime_ns)
            for name in before} == before


def test_private_read_is_a_copy_and_unapproved_providers_are_hidden(snapshot):
    view = PrivateSDKAuthView(snapshot[0], {"nous"})
    data = view.read()
    assert set(data["providers"]) == set(data["credential_pool"]) == {"nous"}
    data["providers"]["nous"]["access_token"] = "not-approved"
    assert view.read()["providers"]["nous"]["access_token"] == "approved-access"
    assert view.global_store() == {}


@pytest.mark.parametrize("section,key,value", [
    ("providers", "access_token", "new-credential"),
    ("providers", "refresh_token", "new-refresh"),
    ("providers", "agent_key", "new-key"),
    ("providers", "anon_token", "new-guest"),
    ("providers", "inference_base_url", "https://unapproved.example/v1"),
    ("credential_pool", "access_token", "new-credential"),
])
def test_credential_or_endpoint_change_is_denied_without_changing_view(snapshot, section, key, value):
    view = PrivateSDKAuthView(snapshot[0], {"nous"})
    before = view.read()
    update = deepcopy(before)
    target = update[section]["nous"]
    if section == "credential_pool":
        target = target[0]
    target[key] = value
    with pytest.raises(PolicyDenied):
        view.save(update)
    assert view.read() == before


def test_reseeding_same_approved_token_is_private_bookkeeping(snapshot):
    view = PrivateSDKAuthView(snapshot[0], {"nous"})
    data = view.read()
    data["credential_pool"]["nous"].append({
        "id": "new-seed", "source": "device_code", "access_token": "approved-access",
        "agent_key": "approved-access", "priority": 1,
    })
    view.save(data)
    assert len(view.read()["credential_pool"]["nous"]) == 2


@pytest.mark.parametrize("action", ["read", "save", "transaction"])
def test_other_auth_store_path_is_denied(snapshot, tmp_path, action):
    view = PrivateSDKAuthView(snapshot[0], {"nous"})
    other = tmp_path / "other/auth.json"
    with pytest.raises(PolicyDenied, match="private_sdk_auth_store_path_changed"):
        if action == "read":
            view.read(other)
        elif action == "save":
            view.save(view.read(), target_path=other)
        else:
            with view.transaction(target_path=other):
                pytest.fail("other store transaction entered")
    assert not other.exists()


@pytest.mark.parametrize("timeout", [True, -1, float("inf"), float("nan"), "30"])
def test_nonfinite_or_untyped_transaction_timeout_denied(snapshot, timeout):
    view = PrivateSDKAuthView(snapshot[0], {"nous"})
    with pytest.raises(PolicyDenied, match="private_sdk_auth_timeout_invalid"):
        with view.transaction(timeout):
            pytest.fail("invalid lock entered")


def test_auth_network_is_denied_before_any_request():
    with _no_auth_network(15, True) as client:
        for method in ("get", "post", "request", "send", "stream"):
            with pytest.raises(PolicyDenied, match="private_sdk_auth_network_forbidden"):
                getattr(client, method)("https://portal.nousresearch.com")


def test_configuration_only_policy_keeps_existing_legacy_path():
    policy = PrivateSDKPolicy("private", "a" * 64, "b" * 64)
    assert install_private_sdk_credentials(None, policy) is None


def fake_sdk(monkeypatch):
    package = types.ModuleType("hermes_cli")
    auth = types.ModuleType("hermes_cli.auth")
    alias = types.ModuleType("agent.private_auth_test_alias")
    def mutable(*args, **kwargs):
        raise AssertionError("mutable SDK store or auth endpoint reached")
    names = (
        "_load_auth_store", "_save_auth_store", "_auth_store_lock",
        "_load_global_auth_store", "_nous_shared_store_lock",
        "_merge_shared_nous_oauth_state", "_write_shared_nous_state",
        "_nous_http_client", "_refresh_nous_or_quarantine",
    )
    # Distinct function objects, as in the SDK; do not turn every seam into one alias.
    for name in names:
        def original(*args, _name=name, **kwargs):
            return mutable(_name, *args, **kwargs)
        setattr(auth, name, original)
    def runtime(**kwargs):
        with auth._auth_store_lock():
            store = auth._load_auth_store()
            store["credential_pool"]["nous"][0]["request_count"] += 1
            auth._save_auth_store(store)
        with auth._nous_http_client(15, True):
            pass
        return {"api_key": store["providers"]["nous"]["agent_key"], "provider": "nous"}
    auth.resolve_nous_runtime_credentials = runtime
    alias.cached_read = auth._load_auth_store
    alias.cached_runtime = runtime
    nous = types.ModuleType("hermes_cli.auth_nous")
    nous._nous_http_client = auth._nous_http_client
    package.auth_nous = nous
    monkeypatch.setitem(sys.modules, "hermes_cli.auth_nous", nous)
    auth._RESOLVE_TOKEN_CACHE = {"prior": "prior-private-value"}
    auth._nous_auth_status_cache = ("prior",)
    package.auth = auth
    monkeypatch.setitem(sys.modules, "hermes_cli", package)
    monkeypatch.setitem(sys.modules, "hermes_cli.auth", auth)
    monkeypatch.setitem(sys.modules, alias.__name__, alias)
    return auth, alias


def test_installer_uses_real_guard_restoration_and_cached_aliases(monkeypatch, snapshot):
    auth, alias = fake_sdk(monkeypatch)
    old_read, old_runtime = auth._load_auth_store, auth.resolve_nous_runtime_credentials
    guard = types.SimpleNamespace(grant=types.SimpleNamespace(
        scope=types.SimpleNamespace(providers=("nous",))))
    installation = GuardInstallation(guard=guard)
    old_cache = auth._RESOLVE_TOKEN_CACHE
    view = install_private_sdk_credentials(installation, snapshot[0])
    try:
        assert auth._RESOLVE_TOKEN_CACHE == {} and auth._RESOLVE_TOKEN_CACHE is not old_cache
        assert auth._nous_auth_status_cache is None
        assert alias.cached_read() == view.read()
        assert alias.cached_runtime()["provider"] == "nous"
        assert view.read()["credential_pool"]["nous"][0]["request_count"] == 1
        with pytest.raises(PolicyDenied, match="private_sdk_auth_refresh_forbidden"):
            auth.resolve_nous_runtime_credentials(force_refresh=True)
        with pytest.raises(PolicyDenied, match="private_sdk_auth_network_forbidden"):
            auth._refresh_nous_or_quarantine()
    finally:
        installation.uninstall()
    assert auth._load_auth_store is old_read
    assert auth._RESOLVE_TOKEN_CACHE is old_cache
    assert auth._nous_auth_status_cache == ("prior",)
    assert alias.cached_read is old_read
    assert auth.resolve_nous_runtime_credentials is alias.cached_runtime is old_runtime
    assert not (snapshot[1] / "auth.lock").exists()
    with pytest.raises(PolicyDenied, match="private_sdk_auth_view_closed"):
        view.read()


def test_new_invocation_does_not_reuse_prior_shadow_metadata(snapshot):
    first = PrivateSDKAuthView(snapshot[0], {"nous"})
    data = first.read()
    data["credential_pool"]["nous"][0]["request_count"] = 15
    first.save(data)
    second = PrivateSDKAuthView(snapshot[0], {"nous"})
    assert second.read()["credential_pool"]["nous"][0]["request_count"] == 0


def test_live_sdk_read_and_pool_selection_are_offline(monkeypatch, snapshot):
    """Execute the pinned SDK resolver/pool code, without an inference client."""
    sdk = Path("/opt/herdr/releases/p0-5035d92-test/hermes")
    if not (sdk / "hermes_cli/auth.py").is_file():
        pytest.skip("pinned SDK not installed on this runner")
    if not globals().get("_PINNED_SDK_CHILD", False):
        import subprocess
        child = (
            "import sys,importlib.util,tempfile;from pathlib import Path;"
            "sys.path[:0]=" + repr(sys.path) + ";import pytest;"
            "spec=importlib.util.spec_from_file_location('private_sdk_child'," + repr(__file__) + ");"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
            "m._PINNED_SDK_CHILD=True;patch=pytest.MonkeyPatch();"
            "root=Path(tempfile.mkdtemp(prefix='herdr-pinned-auth-child-'));"
            "fixture=m.snapshot.__wrapped__(patch,root);"
            "m.test_live_sdk_read_and_pool_selection_are_offline(patch,fixture);"
            "patch.undo();import shutil;shutil.rmtree(root);"
            "print('PINNED_SDK_AUTH_OFFLINE_PASS')"
        )
        result = subprocess.run([sys.executable, "-I", "-B", "-c", child],
                                capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr[-4000:]
        assert "PINNED_SDK_AUTH_OFFLINE_PASS" in result.stdout
        return
    monkeypatch.syspath_prepend(str(sdk))
    from hermes_cli import auth, auth_nous
    import base64
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    token = part({"alg": "HS256"}) + "." + part({
        "scope": auth_nous.NOUS_INFERENCE_INVOKE_SCOPE, "exp": 1893456000,
    }) + ".public-fixture-signature"
    policy, home, source = snapshot
    source = deepcopy(source)
    source["providers"]["nous"].update(access_token=token, agent_key=token,
        scope=auth_nous.NOUS_INFERENCE_INVOKE_SCOPE,
        agent_key_expires_at="2030-01-01T00:00:00Z", client_id="hermes-cli")
    source["credential_pool"]["nous"][0].update(
        access_token=token, agent_key=token, auth_type="oauth",
        scope=auth_nous.NOUS_INFERENCE_INVOKE_SCOPE,
        expires_at="2030-01-01T00:00:00Z", agent_key_expires_at="2030-01-01T00:00:00Z")
    raw = json.dumps(source).encode()
    if globals().get("_READONLY_AUTH_FIXTURE", False):
        assert (home / "auth.json").read_bytes() == raw
    else:
        (home / "auth.json").write_bytes(raw)
    policy = PrivateSDKPolicy(policy.profile_name, policy.profile_sha256,
                              policy.config_sha256, hashlib.sha256(raw).hexdigest())
    guard = types.SimpleNamespace(grant=types.SimpleNamespace(
        scope=types.SimpleNamespace(providers=("nous",))))
    installation = GuardInstallation(guard=guard)
    before = (home / "auth.json").read_bytes()
    import httpx
    def denied(*args, **kwargs):
        pytest.fail("auth/inference HTTP attempted in offline SDK compatibility proof")
    monkeypatch.setattr(httpx.Client, "send", denied)
    install_private_sdk_credentials(installation, policy)
    try:
        creds = auth.resolve_nous_runtime_credentials()
        assert creds["provider"] == "nous" and creds["api_key"] == token
        assert creds["base_url"] == "https://inference-api.nousresearch.com/v1"
        assert auth.resolve_nous_access_token() == token
        status = auth.get_nous_auth_status()
        assert status["logged_in"] is True
        with pytest.raises(PolicyDenied, match="private_sdk_auth_refresh_forbidden"):
            auth.resolve_nous_runtime_credentials(force_refresh=True)
        from agent.credential_pool import load_pool
        pool = load_pool("nous")
        selected = pool.select(model="meituan/longcat-2.5-preview:free")
        assert selected is not None and selected.runtime_api_key == token
        assert not (home / "auth.lock").exists()
        assert (home / "auth.json").read_bytes() == before
        assert not list(home.rglob("*.tmp"))
    finally:
        installation.uninstall()
