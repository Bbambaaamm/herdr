"""Real budget/identity/phase bindings for isolated primary model transport."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from types import SimpleNamespace
import pytest

from herdr import host_model_transport as transport
from herdr.capability import Egress
from herdr.evidence import canonical, digest
from herdr.work_budget import BudgetAllocation, BudgetLimits
from herdr.work_budget_configuration import bind_budget
from herdr.work_cycle import WorkContractError
from tests.herdr.test_work_contract_host import factory_fixture


def prepared(tmp_path, monkeypatch, large=False, shared=False):
    factory, root, original, grant, log = factory_fixture(tmp_path)
    route = replace(grant.provider_routes[0], provider="nous", base_url=transport.ENDPOINT,
                    api_mode="chat_completions", max_egress=Egress.GLOBAL,
                    credential_refs=("pool:nous:test",))
    grant = replace(grant, scope=replace(grant.scope, providers=("nous",),
                    max_egress=Egress.GLOBAL, max_cost_microusd=0, max_context_tokens=65536),
                    provider_routes=(route,), credential_refs=("pool:nous:test",))
    if shared:
        from herdr.security import NetworkAccess
        grant = replace(grant, runtime_assurance=replace(grant.runtime_assurance,network_access=NetworkAccess.GLOBAL))
    limits = BudgetLimits(1000000, 1000000, 5, 100000, 0, 2, 1, 1, 1)
    allocation = BudgetAllocation(digest("transport-allocation"), grant.identity.consumer,
                    digest("transport-work"), digest("transport-lineage"), digest("approval"), limits)
    quote = {"provider": "nous", "model": "test-model:free", "api_mode": "chat_completions",
             "base_url": transport.ENDPOINT, "max_request_bytes": 20000 if large else 4096,
             "max_output_tokens": 100, "max_tokens": 20100 if large else 5000, "max_cost_microusd": 0,
             "max_work_ms": 20000}
    plan = replace(original, grant_sha256=grant.hash, budget_reference=allocation.hash)
    factory.approve = lambda **kwargs: plan
    private = tmp_path / "private"; private.mkdir(mode=0o700)
    bind_budget(factory, {"version": 1, "allocation": asdict(allocation), "ancestors": [],
                         "model_quotes": [quote]}, storage=private, writable_roots=(root,))
    factory.prepare(identity=grant.identity, workspace=root, grant=grant, spec_sha256=plan.spec_sha256)
    payload = {"model": quote["model"], "messages": [{"role": "user", "content": "x" * 10000 if large else "private-input-sentinel"}],
               "max_tokens": 50}
    body = canonical(payload); request_id = "sdk:transport:one"
    receipt = factory.budget_effect(grant.identity, grant.hash, "start", {
        "request_id": request_id, **{k: quote[k] for k in ("provider", "model", "api_mode", "base_url")},
        "request_sha256": hashlib.sha256(body).hexdigest(), "request_bytes": len(body), "output_tokens": 50})
    header = {"op": "work-model", "identity": grant.identity.to_json(), "grant_sha256": grant.hash,
              "operation_id": receipt["operation_id"], "request_id": request_id,
              "body_bytes": len(body), "body_sha256": hashlib.sha256(body).hexdigest()}
    owner = SimpleNamespace(work_budget=factory.budget_effect,
              launch=SimpleNamespace(grant=grant, identity=grant.identity,
                                     private_profile_snapshot=object()))
    monkeypatch.setattr(transport, "_credential", lambda snapshot, reference: "test-private-key")
    return factory, owner, header, body, allocation


def test_original_operation_is_sent_once_and_response_replayed_without_network(tmp_path, monkeypatch):
    factory, owner, header, body, allocation = prepared(tmp_path, monkeypatch)
    calls = []
    def perform(key, payload, seconds):
        assert key == "test-private-key" and 0 < seconds < 20
        assert list((factory.storage / "model-transport").glob("*.intent.json"))
        calls.append(payload)
        return {"kind": "http_response", "http_status": 200, "body": {"content": "ACK"}}
    first = transport.execute_host_model(owner, header, body, perform=perform)
    assert transport.execute_host_model(owner, header, body, perform=perform) == first
    assert len(calls) == 1
    for path in (factory.storage / "model-transport").iterdir():
        assert path.stat().st_mode & 0o777 == 0o600
        assert b"test-private-key" not in path.read_bytes()
        assert b"private-input-sentinel" not in path.read_bytes()
    # Delivery state is not falsely released before the authenticated SDK ACK.
    assert factory.budget_authority.snapshot(allocation.allocation_id)["inflight"] == 1


@pytest.mark.parametrize("fault", ["body", "request_id", "operation_id", "model", "output"])
def test_changed_request_cannot_reuse_original_reservation(tmp_path, monkeypatch, fault):
    factory, owner, header, body, _ = prepared(tmp_path, monkeypatch)
    header = dict(header)
    if fault == "body":
        body += b" "
    elif fault == "request_id":
        header["request_id"] = "another-request"
    elif fault == "operation_id":
        header["operation_id"] = "a" * 64
    else:
        payload = json.loads(body)
        payload["model" if fault == "model" else "max_tokens"] = "paid-other" if fault == "model" else 101
        body = canonical(payload); header["body_bytes"] = len(body)
        header["body_sha256"] = hashlib.sha256(body).hexdigest()
    with pytest.raises((WorkContractError, KeyError)):
        transport.execute_host_model(owner, header, body,
            perform=lambda *args: pytest.fail("changed request reached the network"))


def test_unknown_delivery_is_retained_and_never_resent(tmp_path, monkeypatch):
    factory, owner, header, body, allocation = prepared(tmp_path, monkeypatch)
    calls = []
    def perform(*args):
        calls.append(True)
        return {"kind": "unknown", "http_status": None, "error_type": "TimeoutError"}
    result = transport.execute_host_model(owner, header, body, perform=perform)
    assert result["kind"] == "unknown"
    assert transport.execute_host_model(owner, header, body, perform=perform) == result
    assert len(calls) == 1
    assert factory.budget_authority.snapshot(allocation.allocation_id)["inflight"] == 1


def test_original_intent_without_response_never_becomes_another_http_request(tmp_path, monkeypatch):
    factory, owner, header, body, _ = prepared(tmp_path, monkeypatch)
    def crash(*args):
        raise RuntimeError("injected process loss after durable intent")
    with pytest.raises(RuntimeError):
        transport.execute_host_model(owner, header, body, perform=crash)
    with pytest.raises(WorkContractError, match="unresolved"):
        transport.execute_host_model(owner, header, body,
            perform=lambda *args: pytest.fail("unresolved original was resent"))


def test_observed_http_rejection_can_settle_without_releasing_usage_ceiling(tmp_path, monkeypatch):
    factory, owner, header, body, allocation = prepared(tmp_path, monkeypatch)
    answer = transport.execute_host_model(owner, header, body,
        perform=lambda *args: {"kind": "http_response", "http_status": 429,
                              "body": {"error": {"type": "rate_limit"}}})
    assert answer["http_status"] == 429
    factory.budget_effect(owner.launch.identity, owner.launch.grant.hash, "returned",
                          {"operation_id": header["operation_id"]})
    state = factory.budget_authority.snapshot(allocation.allocation_id)
    assert state["inflight"] == 0 and state["charged_upper_bounds"]["model_calls"] == 1
    assert state["charged_upper_bounds"]["tokens"] == 5000


def test_completed_or_changed_grant_cannot_forward(tmp_path, monkeypatch):
    _, owner, header, body, _ = prepared(tmp_path, monkeypatch)
    owner.launch.grant = replace(owner.launch.grant, grant_id="different-grant")
    with pytest.raises(WorkContractError, match="changed"):
        transport.execute_host_model(owner, header, body,
            perform=lambda *args: pytest.fail("changed authority reached HTTP"))


def test_noncanonical_json_and_unsandboxed_profile_are_denied(tmp_path, monkeypatch):
    _, owner, header, body, _ = prepared(tmp_path, monkeypatch)
    body = json.dumps(json.loads(body), indent=2).encode()
    header = {**header, "body_bytes": len(body), "body_sha256": hashlib.sha256(body).hexdigest()}
    with pytest.raises(WorkContractError, match="canonical"):
        transport.execute_host_model(owner, header, body)


def test_untrusted_callback_cannot_masquerade_as_host_authority():
    owner = SimpleNamespace(work_budget=lambda *args: None)
    with pytest.raises(WorkContractError, match="protected host"):
        transport.execute_host_model(owner, {}, b"")

@pytest.mark.parametrize("shared", [False, True])
def test_real_peer_large_framed_request_and_response(tmp_path, monkeypatch, shared):
    import socket
    import threading
    from herdr.work_authority import WorkAuthorityClient, dispatch_work_connection
    from tests.herdr.test_work_authority import owner_for
    factory, original, header, body, _ = prepared(tmp_path, monkeypatch, large=True, shared=shared)
    owner, observed = owner_for(factory, original.launch.grant)
    owner.work_budget = factory.budget_effect
    owner.launch.private_profile_snapshot = object()
    path = tmp_path / "model.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH", path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(1); listener.settimeout(5)
    calls = []
    response = {"kind": "http_response", "http_status": 200, "body": {"content": "x" * 16000}}
    def perform(*args):
        calls.append(True)
        return response
    monkeypatch.setattr(transport, "_perform_http", perform)
    errors = []
    def server():
        try:
            connection, _ = listener.accept()
            assert dispatch_work_connection(owner, connection)
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=server, daemon=True); thread.start()
    try:
        grant = original.launch.grant
        answer = WorkAuthorityClient().model_transport(grant.identity, grant.hash,
            header["request_id"], {"operation_id": header["operation_id"], "max_work_ms": 20000},
            json.loads(body))
        assert answer == response and len(body) > 8192 and len(calls) == 1
        thread.join(5); assert not thread.is_alive() and not errors and len(observed) == 2
    finally:
        listener.close()


def test_sealed_credential_identity_is_used_without_global_auth_or_refresh(tmp_path, monkeypatch):
    import sys, types
    from herdr.private_profile_namespace import PrivateProfileSnapshot
    source = tmp_path / "quantlab"; source.mkdir()
    values = {"config.yaml": b"{}", ".env": b"",
              "auth.json": json.dumps({"credential_pool": {"nous": [
                  {"id": "test", "agent_key": "valid-fixture-key", "scope": "invoke",
                   "agent_key_expires_at": "2030-01-01T00:00:00Z"}]}}).encode()}
    for name, value in values.items(): (source / name).write_bytes(value)
    snapshot = PrivateProfileSnapshot.from_approved(source, name="quantlab",
        approved_sha256={name: hashlib.sha256(value).hexdigest() for name, value in values.items()})
    package = types.ModuleType("hermes_cli"); auth = types.ModuleType("hermes_cli.auth")
    calls = []
    def usable(token, **kwargs):
        calls.append(token); return token == "valid-fixture-key"
    auth._nous_invoke_jwt_is_usable = usable
    package.auth = auth; monkeypatch.setitem(sys.modules, "hermes_cli", package)
    monkeypatch.setitem(sys.modules, "hermes_cli.auth", auth)
    try:
        assert transport._credential(snapshot, "pool:nous:test") == "valid-fixture-key"
        assert calls == ["valid-fixture-key"]
        with pytest.raises(WorkContractError):
            transport._credential(snapshot, "pool:nous:foreign")
        with pytest.raises(WorkContractError):
            transport._credential(snapshot, "pool:paid:foreign")
    finally:
        snapshot.close()


def test_cached_response_survives_wire_deadline_but_cannot_be_changed(tmp_path, monkeypatch):
    factory, owner, header, body, _ = prepared(tmp_path, monkeypatch)
    answer = {"kind": "http_response", "http_status": 200, "body": {"choices": []}}
    transport.execute_host_model(owner, header, body, perform=lambda *args: answer)
    now = transport.time.time()
    monkeypatch.setattr(transport.time, "time", lambda: now + 30)
    assert transport.execute_host_model(owner, header, body,
        perform=lambda *args: pytest.fail("cached response was resent")) == answer
    path = factory.storage / "model-transport" / (header["operation_id"] + ".response.json")
    value = json.loads(path.read_bytes()); value["result"]["body"] = {"changed": True}
    path.write_bytes(canonical(value))
    with pytest.raises(WorkContractError, match="response changed"):
        transport.execute_host_model(owner, header, body,
            perform=lambda *args: pytest.fail("tampered receipt caused an HTTP request"))


def test_http_child_flattens_sdk_metadata_and_never_uses_environment_proxy(monkeypatch):
    import io
    import urllib.request
    payload = {"model": "test-model:free", "messages": [{"role": "user", "content": "hello"}],
               "max_tokens": 20, "timeout": 120,
               "extra_body": {"tags": ["fixture"], "session_id": "session"}}
    stdin = SimpleNamespace(buffer=io.BytesIO(transport._json(
        {"credential": "private-fixture-key", "payload": payload, "timeout_seconds": 5})))
    stdout = SimpleNamespace(buffer=io.BytesIO())
    monkeypatch.setattr(transport.sys, "stdin", stdin)
    monkeypatch.setattr(transport.sys, "stdout", stdout)
    handlers = []
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit): return b'{"choices":[]}'
    def build(*values):
        handlers.extend(values)
        def open_(request, timeout):
            wire = json.loads(request.data)
            assert wire == {k: v for k, v in payload.items() if k not in {"timeout", "extra_body"}} | payload["extra_body"]
            assert request.full_url == transport.ENDPOINT + "/chat/completions"
            assert request.get_header("Authorization") == "Bearer private-fixture-key"
            assert timeout == 5
            return Response()
        return SimpleNamespace(open=open_)
    monkeypatch.setattr(urllib.request, "build_opener", build)
    answer = transport._request_http(json.loads(stdin.buffer.getvalue()))
    assert answer == {"kind": "http_response", "http_status": 200, "body": {"choices": []}}
    proxy = next(value for value in handlers if isinstance(value, urllib.request.ProxyHandler))
    assert proxy.proxies == {}
    redirect = next(value for value in handlers if isinstance(value, urllib.request.HTTPRedirectHandler))
    assert redirect.redirect_request(None, None, None, None, None, None) is None
    assert b"private-fixture-key" not in stdout.buffer.getvalue()


def test_http_child_reports_fixed_unknown_metadata_without_exception_secret(monkeypatch):
    import io
    import urllib.error
    stdin = SimpleNamespace(buffer=io.BytesIO(transport._json({"credential": "private-fixture-key",
        "payload": {"model": "test-model:free"}, "timeout_seconds": 5})))
    stdout = SimpleNamespace(buffer=io.BytesIO())
    monkeypatch.setattr(transport.sys, "stdin", stdin)
    monkeypatch.setattr(transport.sys, "stdout", stdout)
    def fail(*args, **kwargs):
        raise urllib.error.URLError("contains private-fixture-key")
    monkeypatch.setattr(transport.urllib.request, "build_opener", lambda *args: SimpleNamespace(open=fail))
    answer = transport._request_http(json.loads(stdin.buffer.getvalue()))
    assert answer == {
        "kind": "unknown", "http_status": None, "error_type": "URLError"}
    assert b"private-fixture-key" not in stdout.buffer.getvalue()


@pytest.mark.skipif(os.geteuid() != 0, reason="physical network namespace proof requires administrator")
def test_isolated_process_uses_host_socket_with_real_peer_and_sdk_response(tmp_path, monkeypatch):
    # Component proof: real net namespaces, peer PID/executable and framing.
    # The explicit mount port is NOT full native-worker/mount acceptance.
    import socket, subprocess, sys
    from pathlib import Path
    from herdr.bootstrap_authority import inspect_peer
    from herdr.work_authority import dispatch_work_connection
    from tests.herdr.test_work_authority import owner_for
    factory, original, header, body, allocation = prepared(tmp_path, monkeypatch, large=True)
    path = tmp_path / "bridge.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(1); listener.settimeout(10)
    child_code = """
import errno,json,os,socket,sys
from types import SimpleNamespace
sys.path[:0]=json.loads(sys.argv[1])
from herdr.work_authority import WorkAuthorityClient
import herdr.work_authority as authority
probe=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
probe.settimeout(1)
code=probe.connect_ex(('203.0.113.1',443));probe.close()
print(json.dumps({'pid':os.getpid(),'network':os.readlink('/proc/self/ns/net'),'connect_errno':code}),flush=True)
data=json.loads(sys.stdin.readline())
authority.SOCKET_PATH=data['socket']
result=WorkAuthorityClient().model_transport(SimpleNamespace(to_json=lambda:data['identity']),
    data['grant_sha256'],data['request_id'],data['receipt'],data['payload'])
from openai.types.chat import ChatCompletion
completion=ChatCompletion.model_validate(result['body'])
assert result['kind']=='http_response' and completion.choices[0].message.content=='HOST_ACK'
print(json.dumps({'sdk_response_converted':True,'http_status':result['http_status']}),flush=True)
"""
    process = subprocess.Popen(['/usr/bin/unshare', '--net', '--fork', sys.executable, '-I', '-B', '-c',
        child_code, json.dumps([str(Path(__file__).resolve().parents[2]),
            '/opt/herdr/releases/p0-5035d92-test/hermes/venv/lib/python3.11/site-packages'])],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True, env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
    try:
        ready = json.loads(process.stdout.readline())
        import errno
        assert ready['connect_errno'] == errno.ENETUNREACH
        assert ready['network'] != os.readlink('/proc/self/ns/net')
        peer = inspect_peer(ready['pid'])
        owner, observed = owner_for(factory, original.launch.grant)
        owner.launch._published_bootstrap_receipt = SimpleNamespace(peer_pid=peer.pid,
            process_start_ticks=peer.start_ticks,python_device=peer.exe_device,python_inode=peer.exe_inode)
        owner.work_budget = factory.budget_effect
        owner.launch.private_profile_snapshot = object()
        calls = []
        def perform(*args):
            calls.append(True)
            return {'kind':'http_response','http_status':200,'body':{'id':'fixture',
                'object':'chat.completion','created':1,'model':'test-model:free',
                'choices':[{'index':0,'message':{'role':'assistant','content':'HOST_ACK'},'finish_reason':'stop'}]}}
        monkeypatch.setattr(transport, '_perform_http', perform)
        process.stdin.write(json.dumps({'socket':str(path),'identity':original.launch.identity.to_json(),
            'grant_sha256':original.launch.grant.hash,'request_id':header['request_id'],
            'receipt':{'operation_id':header['operation_id'],'max_work_ms':20000},'payload':json.loads(body)})+'\n')
        process.stdin.flush()
        connection,_=listener.accept()
        assert dispatch_work_connection(owner,connection)
        stdout,stderr=process.communicate(timeout=10)
        assert process.returncode == 0, stderr[-2000:]
        assert json.loads(stdout)=={'sdk_response_converted':True,'http_status':200}
        assert len(calls)==1 and len(observed)==2
        assert factory.budget_authority.snapshot(allocation.allocation_id)['inflight']==1
    finally:
        listener.close()
        if process.poll() is None:
            import signal
            os.killpg(process.pid,signal.SIGKILL);process.communicate()


def test_unverified_or_credential_exposed_runtime_cannot_use_host_transport(tmp_path, monkeypatch):
    from herdr.security import RuntimeAssurance, NetworkAccess
    _, owner, header, body, _ = prepared(tmp_path, monkeypatch)
    owner.launch.grant=replace(owner.launch.grant,runtime_assurance=RuntimeAssurance(False,None,NetworkAccess.NONE,(),False))
    with pytest.raises(WorkContractError,match='verified credential-isolated'):
        transport.execute_host_model(owner,header,body,perform=lambda *args:pytest.fail('unverified runtime reached provider'))
