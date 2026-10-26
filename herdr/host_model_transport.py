"""Primary Nous transport through the authenticated host; SDK network stays closed.

The caller supplies no URL, credentials, or new budget. A durable one-shot
intent binds the exact already-started operation to its immutable request.
"""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import ssl

MAX_BODY = 524288
MAX_RESPONSE = 2097152
ENDPOINT = "https://inference-api.nousresearch.com/v1"


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def _http_child():
    """Fixed URL, no proxy, redirects, refresh, retries, or inherited secrets."""
    raw = sys.stdin.buffer.read(MAX_BODY + 32769)
    if len(raw) > MAX_BODY + 32768:
        raise SystemExit(2)
    request = json.loads(raw)
    if set(request) != {"credential", "payload", "timeout_seconds"}:
        raise SystemExit(2)
    seconds = request["timeout_seconds"]
    if type(seconds) not in (int, float) or not 0 < seconds <= 900:
        raise SystemExit(2)
    credential = request["credential"]
    if type(credential) is not str or not 0 < len(credential) <= 16384 or "\n" in credential or "\r" in credential:
        raise SystemExit(2)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    payload = dict(request["payload"])
    extra = payload.pop("extra_body", {})
    payload.pop("timeout", None)
    payload.update(extra)  # The pinned OpenAI SDK flattens its extra_body argument too.
    wire = urllib.request.Request(ENDPOINT + "/chat/completions",
        data=_json(payload), method="POST",
        headers={"Authorization": "Bearer " + credential,
                 "Content-Type": "application/json", "Accept": "application/json"})
    try:
        try:
            response = opener.open(wire, timeout=seconds)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            data = response.read(MAX_RESPONSE + 1)
            status = response.status
        if len(data) > MAX_RESPONSE:
            result = {"kind": "invalid_response", "http_status": status,
                      "error_type": "ResponseTooLarge"}
        else:
            try:
                body = json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
                if type(body) is not dict:
                    raise ValueError()
                result = {"kind": "http_response", "http_status": status, "body": body}
            except (ValueError, UnicodeError):
                result = {"kind": "invalid_response", "http_status": status,
                          "error_type": "InvalidJSON"}
    except Exception as error:
        # Fixed metadata only. Exception strings/args can contain authentication.
        kind = ("TimeoutError" if isinstance(error, TimeoutError) else
                "URLError" if isinstance(error, urllib.error.URLError) else
                "SSLError" if isinstance(error, ssl.SSLError) else "TransportError")
        result = {"kind": "unknown", "http_status": None, "error_type": kind}
    sys.stdout.buffer.write(_json(result) + b"\n")


if __name__ == "__main__":
    if sys.argv[1:] != ["--http-child"]:
        raise SystemExit(2)
    _http_child()
    raise SystemExit(0)

from .evidence import canonical, digest
from .security import InvocationGuard, ProviderRequest, PolicyDenied
from .work_cycle import require, WorkPhase
from .work_lifetime import remaining_work_seconds
from .work_model_deadline import validate_text_request


def _write_once(path, value):
    raw = canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        with os.fdopen(os.dup(fd), "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    finally:
        os.close(fd)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _read_private(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        import stat
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and info.st_mode & 0o777 == 0o600 and info.st_nlink == 1
                and info.st_size <= MAX_RESPONSE + 16384,
                "host model receipt is untrusted")
        data = os.read(fd, MAX_RESPONSE + 16385)
        require(len(data) == info.st_size, "host model receipt changed")
        return json.loads(data)
    finally:
        os.close(fd)


def _credential(snapshot, reference):
    require(reference.startswith("pool:nous:"), "host model credential route unsupported")
    member = next((value for value in snapshot.files if value.relative == "auth.json"), None)
    require(member is not None, "sealed host model credential unavailable")
    member.verify()
    store = json.loads(os.pread(member.fd, member.size, 0))
    rows = store.get("credential_pool", {}).get("nous", [])
    matches = [row for row in rows if row.get("id") == reference.removeprefix("pool:nous:")]
    require(len(matches) == 1, "sealed model credential identity ambiguous")
    row = matches[0]
    # This pinned SDK helper only validates the JWT; it does not refresh it.
    from hermes_cli import auth
    for key, expiry in (("agent_key", "agent_key_expires_at"), ("access_token", "expires_at")):
        token = row.get(key)
        if (isinstance(token, str) and token.strip()
                and auth._nous_invoke_jwt_is_usable(token, scope=row.get("scope"), expires_at=row.get(expiry))):
            return token.strip()
    raise PolicyDenied("host_model_credential_expired")


def _perform_http(credential, payload, seconds):
    request = _json({"credential": credential, "payload": payload, "timeout_seconds": seconds})
    process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                                "--http-child"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, close_fds=True, start_new_session=True,
                               env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
    try:
        stdout, _ = process.communicate(request, timeout=seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL); process.communicate()
        return {"kind": "unknown", "http_status": None, "error_type": "TimeoutError"}
    if process.returncode or len(stdout) > MAX_RESPONSE + 16384:
        return {"kind": "unknown", "http_status": None, "error_type": "TransportProcessError"}
    try:
        answer = json.loads(stdout)
        require(type(answer) is dict and answer.get("kind") in
                {"http_response", "invalid_response", "unknown"}, "invalid host model result")
        return answer
    except Exception:
        return {"kind": "unknown", "http_status": None, "error_type": "InvalidTransportResult"}



def validate_transport_events(events, identity, plan_sha256, grant_sha256):
    """Descriptive receipts cannot advance work or change economic delivery."""
    import re
    require(len(events) <= 256, "host model receipt limit exceeded")
    intents, receipts = {}, set()
    common = {"event", "work_cycle", "plan_sha256", "grant_sha256", "operation_id"}
    for event in events:
        require(type(event) is dict and event.get("work_cycle") == identity.to_json()
                and event.get("plan_sha256") == plan_sha256
                and event.get("grant_sha256") == grant_sha256
                and isinstance(event.get("operation_id"), str)
                and re.fullmatch(r"[0-9a-f]{64}", event["operation_id"]),
                "host model metadata binding changed")
        operation = event["operation_id"]
        if event["event"] == "work_model_transport_intent":
            require(set(event) == common | {"body_sha256"} and operation not in intents
                    and isinstance(event["body_sha256"], str)
                    and re.fullmatch(r"[0-9a-f]{64}", event["body_sha256"]),
                    "host model intent metadata invalid")
            intents[operation] = event
        else:
            require(event["event"] == "work_model_transport_receipt"
                    and set(event) == common | {"outcome", "http_status", "response_sha256"}
                    and operation in intents and operation not in receipts
                    and event["outcome"] in {"http_response", "invalid_response", "unknown"}
                    and ((event["outcome"] == "unknown" and event["http_status"] is None)
                         or (event["outcome"] != "unknown" and type(event["http_status"]) is int
                             and 100 <= event["http_status"] <= 599))
                    and isinstance(event["response_sha256"], str)
                    and re.fullmatch(r"[0-9a-f]{64}", event["response_sha256"]),
                    "host model response metadata invalid")
            receipts.add(operation)


def _record_receipt(cycle, grant, operation, answer):
    values = {"grant_sha256": grant.hash, "operation_id": operation,
              "outcome": answer["kind"], "http_status": answer.get("http_status"),
              "response_sha256": hashlib.sha256(canonical(answer)).hexdigest()}
    existing = [row for row in cycle.audit_log.replay()
                if row.get("event") == "work_model_transport_receipt"
                and row.get("work_cycle") == cycle.plan.identity.to_json()
                and row.get("operation_id") == operation]
    if existing:
        require(len(existing) == 1 and all(existing[0].get(k) == v for k, v in values.items()),
                "retained model response changed")
    else:
        cycle._record("model_transport_receipt", **values)


def execute_host_model(owner, header, body, *, perform=None):
    """Host-only operation; never trust a route/key chosen by the SDK peer."""
    from types import MethodType, SimpleNamespace
    from .work_contract_host import HostWorkContractFactory
    callback = getattr(owner, "work_budget", None)
    require(type(callback) is MethodType
            and type(callback.__self__) is HostWorkContractFactory
            and callback.__func__ is HostWorkContractFactory.budget_effect,
            "protected host model authority unavailable")
    factory = callback.__self__; launch = owner.launch; grant = launch.grant
    identity = launch.identity
    require(type(body) is bytes and len(body) == header["body_bytes"]
            and 0 < len(body) <= MAX_BODY
            and hashlib.sha256(body).hexdigest() == header["body_sha256"],
            "host model request body changed")
    payload = json.loads(body)
    require(canonical(payload) == body, "canonical host model request required")
    require(grant.is_active() and grant.runtime_assurance.network_access.value == "none",
            "isolated primary model profile required")
    routes = [route for route in grant.provider_routes if route.provider == "nous"]
    require(len(routes) == 1 and routes[0].base_url == ENDPOINT
            and routes[0].api_mode == "chat_completions"
            and len(routes[0].credential_refs) == 1, "exact host model route required")
    route = routes[0]
    require(set(grant.scope.providers) == {"nous"} and grant.scope.max_cost_microusd == 0,
            "zero-cost Nous host model profile required")
    require(len(route.regions) == 1 and route.data_classes, "exact host model data route required")
    order = {"public": 0, "internal": 1, "sensitive": 2}
    data_class = max(grant.scope.data_classes, key=lambda item: order[item.value])
    InvocationGuard(grant).authorize_provider(ProviderRequest(
        "nous", route.regions[0], data_class, route.max_egress, route.max_retention,
        route.training, route.credential_refs[0]))
    with factory._lock:
        cycle, _ = factory._refresh(identity)
        require(cycle.phase is WorkPhase.WORK and cycle.plan.grant_sha256 == grant.hash,
                "host model work phase changed")
        allocation = factory.allocations.get(digest(identity.to_json()))
        require(allocation is not None, "host model allocation unavailable")
        authority = factory.budget_authority
        quote = factory.budget_quotes.get(("nous", payload.get("model"), "chat_completions", ENDPOINT))
        require(quote is not None and quote["model"].endswith(":free")
                and quote["max_cost_microusd"] == 0
                and len(body) <= quote["max_request_bytes"], "exact free model quote required")
        validate_text_request(payload, SimpleNamespace(provider="nous", model=quote["model"],
                              api_mode="chat_completions", base_url=ENDPOINT))
        output = payload.get("max_tokens", payload.get("max_completion_tokens"))
        require(output <= quote["max_output_tokens"], "host model output exceeds quote")
        with authority._serialized():
            state = authority._state()
            operation = state["operations"].get(header["operation_id"])
            expected = digest({"sdk_request": header["request_id"], "identity": identity.to_json(),
                               "plan": cycle.plan.hash, "request": header["body_sha256"]})
            require(operation is not None and operation["allocation_id"] == allocation.allocation_id
                    and operation["identity"] == identity.to_json()
                    and operation["plan_sha256"] == cycle.plan.hash and operation["provider"] == "nous"
                    and operation["semantic_key"] == expected and operation["started"]
                    and operation["usage"] is None, "original model reservation binding changed")
            authority.require_active(allocation.allocation_id, identity)
        directory = factory.storage / "model-transport"
        directory.mkdir(mode=0o700, exist_ok=True)
        require(directory.resolve(strict=True) == directory and directory.stat().st_uid == os.geteuid()
                and directory.stat().st_mode & 0o077 == 0, "private host model storage required")
        intent = directory / (header["operation_id"] + ".intent.json")
        result = directory / (header["operation_id"] + ".response.json")
        binding = {"version": 1, "identity": identity.to_json(), "grant_sha256": grant.hash,
                   "plan_sha256": cycle.plan.hash, "operation_id": header["operation_id"],
                   "request_id": header["request_id"], "body_sha256": header["body_sha256"]}
        if intent.exists():
            require(_read_private(intent) == binding, "original model transport intent changed")
            require(result.is_file(), "original model transport unresolved; never resend")
            receipt = _read_private(result)
            require(receipt["binding"] == binding, "model response binding changed")
            _record_receipt(cycle, grant, header["operation_id"], receipt["result"])
            return receipt["result"]
        starts = [row for row in authority.audit_log.replay() if row.get("event") == "work_budget_start"
                  and row.get("operation_id") == header["operation_id"]]
        require(len(starts) == 1, "original model start time unavailable")
        seconds = min(quote["max_work_ms"] / 1000 - (time.time() - starts[0]["at_ms"] / 1000) - 5,
                      remaining_work_seconds(900))
        from datetime import datetime
        seconds = min(seconds, (datetime.fromisoformat(grant.expires_at) -
                       datetime.now(datetime.fromisoformat(grant.expires_at).tzinfo)).total_seconds() - 5)
        require(seconds > 0, "host model transport deadline exhausted")
        credential = _credential(launch.private_profile_snapshot, route.credential_refs[0])
        _write_once(intent, binding)  # Durable one-shot boundary precedes HTTPS.
        cycle._record("model_transport_intent", grant_sha256=grant.hash,
            operation_id=header["operation_id"], body_sha256=header["body_sha256"])
        # No URL or authentication comes from the peer. The fixed child performs one request.
        answer = (perform or _perform_http)(credential, payload, seconds)
        encoded = canonical(answer)
        require(len(encoded) <= MAX_RESPONSE, "bounded host model response required")
        _write_once(result, {"binding": binding, "result": answer})
        _record_receipt(cycle, grant, header["operation_id"], answer)
        return answer
