"""Primary Nous transport through the authenticated host; SDK network stays closed.

The caller supplies no URL, credentials, or new budget. A durable one-shot
intent binds the exact already-started operation to its immutable request.
"""
from pathlib import Path
import ctypes
import fcntl
import socket
import struct
import secrets
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


def _request_http(request):
    """Fixed URL, no proxy, redirects, refresh, retries, or inherited secrets."""
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
    return result


def _protect_process():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(4, 0, 0, 0, 0) or libc.prctl(3, 0, 0, 0, 0) != 0:
        raise RuntimeError("private transport process required")


def _peer(connection):
    return struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))


def _receive(connection, maximum):
    def exact(size):
        result = bytearray()
        while len(result) < size:
            block = connection.recv(min(65536, size - len(result)))
            if not block:
                raise ValueError("short private transport frame")
            result.extend(block)
        return bytes(result)
    size = struct.unpack("!I", exact(4))[0]
    if not 0 < size <= maximum:
        raise ValueError("private transport frame exceeds bound")
    return json.loads(exact(size), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def _send(connection, value, maximum):
    raw = _json(value)
    if not 0 < len(raw) <= maximum:
        raise ValueError("private transport frame exceeds bound")
    connection.sendall(struct.pack("!I", len(raw)) + raw)


def _http_child(address, parent_pid, seconds):
    # Exec resets dumpability. Protect FIRST, then create a NEW socket. Never
    # send credentials or response bodies over descriptors inherited at exec:
    # a same-UID observer could have opened those pipes before protection.
    _protect_process()
    if not address.startswith("herdr-model-") or len(address) > 100:
        raise SystemExit(2)
    if parent_pid != os.getppid() or not 0 < seconds <= 900:
        raise SystemExit(2)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(seconds)
        connection.connect("\0" + address)
        pid, uid, _ = _peer(connection)
        if pid != parent_pid or uid != os.getuid():
            raise SystemExit(2)
        request = _receive(connection, MAX_BODY + 32768)
        # Budget time includes setup; a request cannot extend the parent's
        # original deadline. The parent also kills its owned group on expiry.
        request["timeout_seconds"] = min(request["timeout_seconds"], seconds)
        _send(connection, _request_http(request), MAX_RESPONSE + 16384)


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "--http-child":
        raise SystemExit(2)
    _http_child(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]))
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
    request = {"credential": credential, "payload": payload, "timeout_seconds": seconds}
    # The existing host entrypoint must have protected the credential owner.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(3, 0, 0, 0, 0) != 0 or not 0 < seconds <= 900:
        raise RuntimeError("protected model host required")
    deadline = time.monotonic() + seconds
    address = "herdr-model-" + secrets.token_hex(24)
    process = None
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind("\0" + address)
        listener.listen(4)
        try:
            process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                "--http-child", address, str(os.getpid()), str(seconds)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                close_fds=True, start_new_session=True,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
            # Reject connections from every other PID, even the same UID.
            for _ in range(16):
                listener.settimeout(max(0.001, deadline - time.monotonic()))
                connection, _ = listener.accept()
                with connection:
                    if _peer(connection)[:2] != (process.pid, os.getuid()):
                        continue
                    connection.settimeout(max(0.001, deadline - time.monotonic()))
                    _send(connection, request, MAX_BODY + 32768)
                    answer = _receive(connection, MAX_RESPONSE + 16384)
                    process.wait(timeout=max(0.001, deadline-time.monotonic()))
                    if process.returncode:
                        raise ValueError("private transport process failed")
                    require(type(answer) is dict and answer.get("kind") in
                        {"http_response", "invalid_response", "unknown"}, "invalid host model result")
                    return answer
            raise ValueError("private transport peer not established")
        except (OSError, ValueError, subprocess.SubprocessError):
            return {"kind": "unknown", "http_status": None, "error_type": "TransportProcessError"}
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=3)



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


_OFFLINE_NONCE = "03414499dd0d1986968b2393d44275d0"
_OFFLINE_HOST_LABEL = "herdr-offline-controller-03414499dd0d1986 (enforce)"
_FIXTURE_MODEL = "meituan/longcat-2.0:free"
_FIXTURE_EDIT = "def add(left, right):\n    return left + right\n"


def _case_host():
    fd = os.open("/proc/self/attr/current", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        label = os.read(fd, 256).strip().decode("ascii", "strict")
    finally:
        os.close(fd)
    return label == _OFFLINE_HOST_LABEL


def _case_unit():
    fd = os.open("/proc/self/cgroup", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        groups = os.read(fd, 8192).decode("ascii", "strict").splitlines()
    finally:
        os.close(fd)
    return groups == ["0::/system.slice/herdr-offline-host-03414499dd0d1986.service"]


def _fixture_binding(factory, identity, grant, payload):
    """Use the existing root-approved selector and original work admission."""
    from .host_configuration import _read_configuration
    selector = _read_configuration(Path("/etc/herdr/offline-case-host.json"))
    require(selector.get("nonce") == _OFFLINE_NONCE and
            selector.get("host_label") + " (enforce)" == _OFFLINE_HOST_LABEL and
            grant.identity == identity and identity.consumer == "github:Bbambaaamm/herdr" and
            payload.get("model") == _FIXTURE_MODEL,
            "foreign offline fixture binding")
    task = factory.host_task
    require(type(task) is dict and task.get("id") == identity.task_id and
            task.get("run_token") == identity.run_token and
            task.get("fencing_token") == identity.fencing_token,
            "offline fixture task differs from original work")
    if identity.task_id == selector["task_id"]:
        require(identity.task_id.endswith(_OFFLINE_NONCE),
                "offline root task is outside the fixed case")
        require(identity.run_token == selector["run_token"] and
                identity.fencing_token == selector["fencing_token"],
                "offline root selector changed")
        role = "root"
    else:
        require(selector["task_id"].endswith(_OFFLINE_NONCE) and
                identity.parent_task_id == selector["task_id"] and
                identity.parent_agent_id == task.get("parent_agent_id") and
                task.get("derived_parent_admission_sha256"),
                "offline child lacks original parent admission")
        role = "child"
    admitted = factory.host_admission
    definition = admitted.get("definition") if type(admitted) is dict else None
    require(type(definition) is dict and
            definition.get("spec_version") == "offline-arithmetic-1" and
            definition.get("policy_version") == "offline-clean-1" and
            definition.get("criteria") == ["arithmetic"] and
            definition.get("discovery_files") == ["arithmetic.py", "check_arithmetic.py"] and
            definition.get("files") == [{"path": "arithmetic.py", "subtree": False,
                                         "symbols": []}],
            "offline arithmetic work definition changed")
    return role, definition


def _fixture_response(payload, role, definition, ordinal, workspace):
    """Fixed transport data; SDK tools and host semantic checks still decide work."""
    require(type(payload.get("tools")) is list and
            type(workspace) is str and workspace.startswith("/") and
            ".." not in Path(workspace).parts, "offline fixture tool or workspace changed")
    names = {row.get("function", {}).get("name") for row in payload["tools"]
             if type(row) is dict and row.get("type") == "function" and
             type(row.get("function")) is dict}
    require({"read_file", "write_file", "herdr_verify_work", "herdr_submit_result"} <= names and
            ("herdr_delegate_child" in names) == (role == "root"),
            "offline fixture SDK tool guard changed")
    calls = []
    if role == "root" and ordinal == 1:
        children = definition.get("managed_children", {}).get("children")
        require(type(children) is list and len(children) == 1,
                "one original managed child template required")
        child = children[0]
        require(child.get("key") == "arithmetic-child" and
                child.get("worktree_identity", "").count("|") == 1,
                "original child template changed")
        child_workspace = child["worktree_identity"].rsplit("|", 1)[0]
        require(Path(child_workspace).is_relative_to(Path(workspace)) and
                child_workspace != workspace, "child workspace outside original parent")
        calls = [("herdr_delegate_child", {"key": child["key"],
                  "objective": child["objective"], "role": child["role"],
                  "ownership": child["ownership"],
                  "prompt": "Repair add in arithmetic.py only; verify the frozen check and submit local result.",
                  "tool": child["tools"], "permission": child["permissions"],
                  "cwd": child_workspace, "model": _FIXTURE_MODEL,
                  "fallback_model": None})]
    else:
        step = ordinal - (1 if role == "root" else 0)
        if step == 1:
            calls = [("read_file", {"path": workspace.rstrip("/") + "/" + name,
                                    "offset": 1, "limit": 2000})
                     for name in ("arithmetic.py", "check_arithmetic.py")]
        elif step == 2:
            calls = [("write_file", {"path": workspace.rstrip("/") + "/arithmetic.py",
                                     "content": _FIXTURE_EDIT})]
        elif step == 3:
            calls = [("herdr_verify_work", {"request_id": "offline_validation_once",
                                            "handoff": {"pr_number": None}})]
        elif step == 4:
            submissions = []
            def collect(value):
                if type(value) is dict:
                    if "submission" in value:
                        require(value.get("status") == "pass" and
                                type(value["submission"]) is dict,
                                "actual host verification did not pass")
                        submissions.append(value["submission"])
                    else:
                        for child in value.values():
                            collect(child)
                elif type(value) is list:
                    for child in value:
                        collect(child)
            for message in payload.get("messages", []):
                if type(message) is dict and message.get("role") == "tool":
                    try:
                        collect(json.loads(message.get("content")))
                    except (TypeError, ValueError):
                        continue
            require(len(submissions) == 1, "actual host verification receipt required")
            calls = [("herdr_submit_result", submissions[0])]
        else:
            require(step == 5, "offline fixture turn bound exceeded")
    message = {"role": "assistant", "content": None if calls else
               "OFFLINE FIXTURE: exact local handoff submitted."}
    if calls:
        message["tool_calls"] = [{"id": "offline_%s_%d_%d" % (role, ordinal, index),
            "type": "function", "function": {"name": name,
            "arguments": json.dumps(arguments, sort_keys=True, separators=(",", ":"))}}
            for index, (name, arguments) in enumerate(calls)]
    return {"kind": "http_response", "http_status": 200,
            "body": {"id": "offline-%s-%d" % (role, ordinal),
            "object": "chat.completion", "created": 1, "model": _FIXTURE_MODEL,
            "choices": [{"index": 0, "message": message,
                         "finish_reason": "tool_calls" if calls else "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}}


def _perform_fixture(factory, identity, grant, payload, operation_id):
    role, definition = _fixture_binding(factory, identity, grant, payload)
    from .host_configuration import HOST_POLICY_CONFIG, _read_configuration
    storage = Path(_read_configuration(HOST_POLICY_CONFIG)["storage"])
    owner = storage.lstat()
    import stat
    require(storage.is_absolute() and storage.resolve(strict=True) == storage and
            stat.S_ISDIR(owner.st_mode) and owner.st_uid == os.geteuid() and
            owner.st_mode & 0o077 == 0 and factory.storage.is_relative_to(storage),
            "original private shared host storage required")
    root = storage / ("offline-fixture-" + _OFFLINE_NONCE)
    root.mkdir(mode=0o700, exist_ok=True)
    info = root.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and
            info.st_mode & 0o077 == 0 and root.resolve(strict=True) == root,
            "private shared fixture counter required")
    lock = os.open(root / "counter.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        info = os.fstat(lock)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
                info.st_mode & 0o777 == 0o600 and info.st_nlink == 1,
                "fixture counter lock changed")
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = []
        for path in root.iterdir():
            if path.name == "counter.lock":
                continue
            require(path.name.endswith(".json") and len(path.name) == 69 and
                    all(c in "0123456789abcdef" for c in path.name[:-5]),
                    "foreign fixture counter entry")
            row = _read_private(path)
            require(type(row) is dict and set(row) ==
                    {"role", "operation_id", "identity", "ordinal"} and
                    row["role"] in {"root", "child"} and
                    type(row["operation_id"]) is str and
                    path.name == row["operation_id"] + ".json" and
                    type(row["identity"]) is dict and
                    type(row["ordinal"]) is int and row["ordinal"] > 0,
                    "fixture counter record changed")
            rows.append(row)
        require(len(rows) < 16 and not any(row.get("operation_id") == operation_id for row in rows),
                "offline fixture cap or replay reached")
        ordinal = 1 + sum(row.get("role") == role for row in rows)
        from .canonical_case_probe import probe_response
        answer = probe_response(payload, identity, grant, role, ordinal)
        if answer is None:
            answer = _fixture_response(payload, role, definition, ordinal, grant.workspace_root)
        _write_once(root / (operation_id + ".json"),
                    {"role": role, "operation_id": operation_id,
                     "identity": identity.to_json(), "ordinal": ordinal})
        return answer
    finally:
        os.close(lock)


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
    assurance = grant.runtime_assurance
    # The exact grant was sealed against the authenticated native peer. Native
    # IPC may require a shared namespace; host delivery must not reject that
    # approved mode after the SDK correctly selected its protected work port.
    # This asserts the observed boundary, never claims physical NoNet isolation.
    require(grant.is_active() and assurance.sandbox_verified and assurance.credentials_isolated
            and assurance.network_access.value in {"none", "global"},
            "verified credential-isolated primary model profile required")
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
        offline = _case_host()
        in_case_unit = _case_unit()
        require(offline == in_case_unit,
                "offline fixture host label or cgroup changed")
        # An offline case whose host confinement is missing must never fall
        # through to the ordinary credential and HTTPS transport.
        case_identity = (identity.run_token == _OFFLINE_NONCE or
                         identity.task_id.endswith(_OFFLINE_NONCE) or
                         bool(identity.parent_task_id and
                              identity.parent_task_id.endswith(_OFFLINE_NONCE)))
        require(offline or not case_identity,
                "offline case host profile missing; HTTP fallback forbidden")
        if offline:
            require(perform is None, "offline fixture cannot accept a replacement transport")
            _fixture_binding(factory, identity, grant, payload)
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
        if not offline:
            credential = _credential(launch.private_profile_snapshot, route.credential_refs[0])
        _write_once(intent, binding)  # Durable one-shot boundary precedes HTTPS.
        cycle._record("model_transport_intent", grant_sha256=grant.hash,
            operation_id=header["operation_id"], body_sha256=header["body_sha256"])
        # No URL or authentication comes from the peer. The fixed child performs one request.
        answer = (_perform_fixture(factory, identity, grant, payload,
                                   header["operation_id"]) if offline else
                  (perform or _perform_http)(credential, payload, seconds))
        encoded = canonical(answer)
        require(len(encoded) <= MAX_RESPONSE, "bounded host model response required")
        _write_once(result, {"binding": binding, "result": answer})
        _record_receipt(cycle, grant, header["operation_id"], answer)
        return answer
