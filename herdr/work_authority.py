"""Work phase IPC on the already authenticated physical bootstrap authority."""
import json
import os
import socket
import struct
import time

from .bootstrap_authority import SOCKET_PATH, _recv_line, inspect_peer
from .security import InvocationIdentity, PolicyDenied
from .work_cycle import require, WorkContractError
from .evidence import canonical


# Physical peer/mount verification runs before authorization and again after
# budget callbacks. Allow that work while bounding the *whole* exchange, not
# each received chunk. A transport failure never authorizes an economic retry:
# the host may already have retained the original operation reservation.
_WORK_REQUEST_TIMEOUT_SECONDS = 60


_SDK_OBSERVATION_TIMEOUT_SECONDS = 0.5


def _work_response(payload, *, max_bytes, timeout_seconds=None):
    seconds = _WORK_REQUEST_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    deadline = time.monotonic() + seconds
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        def bounded(operation, *args):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("work authority exchange timed out")
            connection.settimeout(remaining)
            result = operation(*args)
            if time.monotonic() > deadline:
                raise TimeoutError("work authority exchange timed out")
            return result
        bounded(connection.connect, str(SOCKET_PATH))
        bounded(connection.sendall, payload)
        result = bytearray()
        while len(result) <= max_bytes:
            chunk = bounded(connection.recv, min(1024, max_bytes + 1 - len(result)))
            if not chunk:
                break
            result.extend(chunk)
            if b"\n" in result:
                break
    return bytes(result)


class WorkAuthorityClient:
    """Fixed host socket; environment/model data cannot select another authority."""
    def __call__(self, identity, grant_sha256, *, kind, tool=None):
        require(isinstance(identity, InvocationIdentity) and kind in {"provider", "tool"},
                "exact work authority request required")
        request = {"op": "work-authorize", "identity": identity.to_json(),
                   "grant_sha256": grant_sha256, "kind": kind, "tool": tool}
        payload = canonical(request) + b"\n"
        require(len(payload) <= 8192, "work authority request exceeds bound")
        try:
            result = _work_response(payload, max_bytes=128)
            if result != b"work-ok\n":
                raise PolicyDenied("work_phase_forbids_invocation")
        except PolicyDenied:
            raise
        except (OSError, TimeoutError) as exc:
            raise PolicyDenied("work_authority_unavailable") from exc
        return True

    def effect(self,identity,grant_sha256,action,payload):
        from .evidence import EvidenceError
        try:
            request={"op":"work-budget","identity":identity.to_json(),"grant_sha256":grant_sha256,
                     "action":action,"payload":payload}
            encoded=json.dumps(request,sort_keys=True,separators=(",",":")).encode()+b"\n"
            require(len(encoded)<=8192,"bounded model budget transport required")
            result=_work_response(encoded,max_bytes=8192)
            require(len(result)<=8192 and result.endswith(b"\n"),"bounded budget response required")
            parsed=json.loads(result)
            require(isinstance(parsed,dict),"closed host budget response required")
            return parsed
        except PolicyDenied:raise
        except (EvidenceError,OSError,ValueError,TypeError) as exc:
            raise PolicyDenied("work_budget_unavailable") from exc

    def model_transport(self, identity, grant_sha256, request_id, receipt, payload):
        """Two bounded frames; the authenticated header precedes the large body."""
        from .host_model_transport import MAX_BODY, MAX_RESPONSE
        import hashlib
        body = canonical(payload)
        require(0 < len(body) <= MAX_BODY, "bounded host model body required")
        header = canonical({"op": "work-model", "identity": identity.to_json(),
            "grant_sha256": grant_sha256, "operation_id": receipt["operation_id"],
            "request_id": request_id, "body_bytes": len(body),
            "body_sha256": hashlib.sha256(body).hexdigest()}) + b"\n"
        require(len(header) <= 8192, "bounded host model header required")
        deadline = time.monotonic() + receipt["max_work_ms"] / 1000
        def remaining(connection):
            seconds = deadline - time.monotonic()
            require(seconds > 0, "host model exchange deadline exhausted")
            connection.settimeout(seconds)
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                remaining(connection); connection.connect(str(SOCKET_PATH))
                remaining(connection); connection.sendall(header)
                ack = bytearray()
                while len(ack) < 32 and not ack.endswith(b"\n"):
                    remaining(connection)
                    part = connection.recv(1)
                    if not part: break
                    ack.extend(part)
                require(bytes(ack) == b"model-body-ready\n", "host model header denied")
                remaining(connection); connection.sendall(body)
                result = bytearray()
                while len(result) <= MAX_RESPONSE:
                    remaining(connection)
                    part = connection.recv(min(65536, MAX_RESPONSE + 1 - len(result)))
                    if not part: break
                    result.extend(part)
                    if b"\n" in result: break
            require(len(result) <= MAX_RESPONSE and result.endswith(b"\n")
                    and result.count(b"\n") == 1, "bounded host model result required")
            value = json.loads(result)
            require(type(value) is dict and value.get("kind") in
                    {"http_response", "invalid_response", "unknown"}, "host model result invalid")
            return value
        except PolicyDenied:
            raise
        except Exception as error:
            raise PolicyDenied("host_model_transport_unavailable") from error

    def observe(self, identity, grant_sha256, observation):
        # No retry: a lost ACK may follow a durable observation. This transport
        # does not authorize any effect and cannot change budget delivery state.
        from .sdk_observation import validate_observation
        try:
            require(isinstance(identity, InvocationIdentity), "SDK observation identity required")
            request = {"op": "work-sdk-observation", "identity": identity.to_json(),
                       "grant_sha256": grant_sha256,
                       "observation": validate_observation(observation)}
            payload = canonical(request) + b"\n"
            require(len(payload) <= 8192, "bounded SDK observation required")
            return _work_response(payload, max_bytes=128,
                timeout_seconds=_SDK_OBSERVATION_TIMEOUT_SECONDS) == b"observation-ok\n"
        except Exception:
            return False

    def external_knowledge(self, identity, grant_sha256, provider_id, request):
        from .external_knowledge import KnowledgeContractError, KnowledgeRequest, KnowledgeResponse
        try:
            if (not isinstance(identity, InvocationIdentity)
                    or not isinstance(request, KnowledgeRequest)
                    or not isinstance(provider_id, str)):
                raise PolicyDenied("external_knowledge_request_invalid")
            message = {
                "op": "external-knowledge-query",
                "identity": identity.to_json(),
                "grant_sha256": grant_sha256,
                "provider_id": provider_id,
                "request": request.to_dict(),
            }
            payload = json.dumps(
                message, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8") + b"\n"
            if len(payload) > 8192:
                raise PolicyDenied("external_knowledge_request_too_large")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(905)
                connection.connect(str(SOCKET_PATH))
                connection.sendall(payload)
                result = bytearray()
                limit = 2_000_000
                while len(result) <= limit:
                    chunk = connection.recv(min(65_536, limit + 1 - len(result)))
                    if not chunk:
                        break
                    result.extend(chunk)
                    if b"\n" in result:
                        break
            if (len(result) > limit or not result.endswith(b"\n")
                    or result.count(b"\n") != 1):
                raise PolicyDenied("external_knowledge_response_invalid")
            parsed = json.loads(result)
            response = KnowledgeResponse.from_dict(parsed)
            if (response.request_id != request.request_id
                    or {item.source for item in response.sources} != set(request.sources)):
                raise PolicyDenied("external_knowledge_response_mismatch")
            return response
        except PolicyDenied:
            raise
        except (KnowledgeContractError, OSError, TimeoutError, ValueError, TypeError, UnicodeError) as exc:
            raise PolicyDenied("external_knowledge_unavailable") from exc

    def verify(self, identity, grant_sha256, request_id, handoff=None):
        from .evidence import EvidenceError
        try:
            return self._verify_transport(identity,grant_sha256,request_id,handoff)
        except PolicyDenied:
            raise
        except (EvidenceError,ValueError,TypeError,OSError) as exc:
            raise PolicyDenied("work_verification_denied") from exc

    def _verify_transport(self, identity, grant_sha256, request_id, handoff=None):
        request = {"op": "work-verify", "identity": identity.to_json(),
                   "grant_sha256": grant_sha256, "request_id": request_id}
        if handoff is not None: request["handoff"] = handoff
        payload = canonical(request) + b"\n"
        require(len(payload) <= 8192, "verification request exceeds bound")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(905)
                connection.connect(str(SOCKET_PATH)); connection.sendall(payload)
                result = bytearray()
                while len(result) <= 8192:
                    chunk = connection.recv(min(1024, 8193 - len(result)))
                    if not chunk:
                        break
                    result.extend(chunk)
                    if b"\n" in result:
                        break
                require(len(result) <= 8192 and result.endswith(b"\n"), "bounded verification response required")
                outcome = json.loads(result)
                require(isinstance(outcome, dict) and outcome.get("status") in {"pass", "failed", "unavailable", "unknown"},
                        "host verification response invalid")
                return outcome
        except PolicyDenied:
            raise
        except (OSError, ValueError, TypeError) as exc:
            raise PolicyDenied("work_verification_unavailable") from exc


def dispatch_work_connection(owner, connection):
    from .work_lifetime import bounded_host_request
    # This starts before receipt/peer/mount/request checks and remains active
    # through response encoding and delivery, on this same broker thread.
    try:
        with bounded_host_request(900):
            return _dispatch_work_connection(owner,connection)
    except WorkContractError:
        # _dispatch already closes accepted peers and sends its bounded denial.
        # Context-exit expiry must never kill the authority listener.
        return True

def _observe_authenticated_denial(owner, peer, binding, operation, error):
    """Host-only best effort; historical ports keep their original denial."""
    try:
        from types import MethodType
        from .work_contract_host import HostWorkContractFactory
        from .host_work_denial import describe_denial
        from .work_lifetime import require_work_time
        callback = getattr(owner, "work_authority", None)
        if (type(callback) is not MethodType
                or type(callback.__self__) is not HostWorkContractFactory
                or callback.__func__ is not HostWorkContractFactory.authorize_invocation):
            return False
        identity, grant_sha256 = binding
        require_work_time()
        # This reports the request's earlier verified binding, not live authority
        # now: an exiting peer/expired grant must not erase its host failure.
        return callback.__self__.observe_host_denial(
            identity, grant_sha256, describe_denial(operation, error, peer)) is True
    except BaseException:
        # No observer failure, including failed fsync, may replace the denial.
        return False


def _dispatch_work_connection(owner, connection):
    """Only the exact observed stage-two process can ask about its phase.

    Other peers go through the unchanged stage-one admission broker. The
    request itself never advances a phase, records PASS, or changes a plan.
    """
    receipt = owner.launch._published_bootstrap_receipt
    if receipt is None:
        return False
    accepted_peer = False
    authenticated_binding, operation = None, None
    try:
        pid, uid, _ = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if pid != receipt.peer_pid or uid != os.geteuid():
            return False
        accepted_peer = True
        from .work_lifetime import require_work_time,remaining_work_seconds
        require_work_time()
        peer = inspect_peer(pid)
        require(peer.start_ticks == receipt.process_start_ticks
                and (peer.exe_device, peer.exe_inode) == (receipt.python_device, receipt.python_inode),
                "work authority peer changed")
        owner.launch.mount.verify_mounted(pid, owner.launch.sealed)
        require_work_time()
        require(owner.launch.grant.is_active(), "work authority grant expired")
        connection.settimeout(remaining_work_seconds(5))
        request = _recv_line(connection)
        require_work_time()
        require(request.get("identity") == owner.launch.identity.to_json()
                and request.get("grant_sha256") == owner.launch.grant.hash, "work authority binding invalid")
        authenticated_binding = (owner.launch.identity, owner.launch.grant.hash)
        if request.get("op") == "work-sdk-observation":
            from .sdk_observation import validate_observation
            require(set(request) == {"op", "identity", "grant_sha256", "observation"},
                    "closed SDK observation request required")
            observation = validate_observation(request["observation"])
            operation = "work-sdk-observation"
            callback = getattr(owner, "work_observe", None)
            require(callable(callback), "host SDK observation unavailable")
            require(callback(owner.launch.identity, owner.launch.grant.hash, observation) is True,
                    "host SDK observation denied")
            require_work_time()
            after = inspect_peer(pid)
            require(after == peer and owner.launch.grant.is_active(),
                    "SDK observation peer or grant changed")
            owner.launch.mount.verify_mounted(pid, owner.launch.sealed)
            require_work_time()
            connection.sendall(b"observation-ok\n")
        elif request.get("op") == "work-model":
            from .host_model_transport import MAX_BODY, MAX_RESPONSE, execute_host_model
            import re
            require(set(request) == {"op", "identity", "grant_sha256", "operation_id",
                    "request_id", "body_bytes", "body_sha256"}
                    and type(request["body_bytes"]) is int and 0 < request["body_bytes"] <= MAX_BODY
                    and isinstance(request["request_id"], str)
                    and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", request["request_id"])
                    and all(isinstance(request[key], str) and
                        re.fullmatch(r"[0-9a-f]{64}", request[key])
                        for key in ("operation_id", "body_sha256")),
                    "closed host model header required")
            operation = "work-model"
            connection.sendall(b"model-body-ready\n")
            body = bytearray(); body_deadline = time.monotonic() + 5
            while len(body) < request["body_bytes"]:
                seconds = min(body_deadline - time.monotonic(), remaining_work_seconds(5))
                require(seconds > 0, "host model body deadline exhausted")
                connection.settimeout(seconds)
                part = connection.recv(min(65536, request["body_bytes"] - len(body)))
                require(bool(part), "host model body shortened")
                body.extend(part)
            result = execute_host_model(owner, request, bytes(body))
            require_work_time()
            after = inspect_peer(pid)
            require(after == peer and owner.launch.grant.is_active(), "host model peer changed")
            owner.launch.mount.verify_mounted(pid, owner.launch.sealed)
            encoded = canonical(result) + b"\n"
            require(len(encoded) <= MAX_RESPONSE, "host model response exceeds bound")
            connection.settimeout(remaining_work_seconds(5))
            connection.sendall(encoded)
        elif request.get("op") == "work-budget":
            require(set(request)=={"op","identity","grant_sha256","action","payload"}
                    and request["action"] in {"status","ceiling","start","returned"} and isinstance(request["payload"],dict),
                    "closed budget request required")
            operation = "work-budget"
            callback=getattr(owner,"work_budget",None)
            if callback is None:
                require(request["action"]=="status" and request["payload"]=={},"budget authority missing")
                result={"required":False}
            else:
                result=callback(owner.launch.identity,owner.launch.grant.hash,request["action"],request["payload"])
            after=inspect_peer(pid)
            require(after==peer and owner.launch.grant.is_active(),"budget peer changed during reservation")
            owner.launch.mount.verify_mounted(pid,owner.launch.sealed)
            encoded=json.dumps(result,sort_keys=True,separators=(",",":")).encode()+b"\n"
            require(len(encoded)<=8192,"budget response exceeds bound")
            connection.sendall(encoded)
        elif request.get("op") == "external-knowledge-query":
            require(set(request) == {
                        "op", "identity", "grant_sha256", "provider_id", "request"
                    } and "herdr_external_knowledge" in owner.launch.grant.scope.tools,
                    "external knowledge tool is not granted")
            operation = "external-knowledge-query"
            callback = getattr(owner, "external_knowledge_query", None)
            durable_authority = getattr(owner, "external_knowledge_authority", None)
            require(callable(callback) and callable(durable_authority),
                    "external knowledge host authority unavailable")
            from .external_knowledge import KnowledgeRequest, KnowledgeResponse
            knowledge_request = KnowledgeRequest.from_dict(request["request"])
            provider_id = request["provider_id"]
            require(isinstance(provider_id, str) and 0 < len(provider_id) <= 64,
                    "external knowledge provider invalid")
            require(durable_authority(
                owner.launch.identity, owner.launch.grant.hash,
                provider_id, knowledge_request
            ) is True, "external knowledge durable authority denied")
            if owner.work_authority is not None:
                require(owner.work_authority(
                    owner.launch.identity, owner.launch.grant.hash,
                    kind="tool", tool="herdr_external_knowledge"
                ) is True, "external knowledge phase denied")
            from .work_lifetime import require_grant_lifetime
            require_grant_lifetime(owner.launch.grant, 900)
            response = callback(
                owner.launch.identity,
                owner.launch.grant.hash,
                provider_id,
                knowledge_request,
            )
            require(isinstance(response, KnowledgeResponse)
                    and response.request_id == knowledge_request.request_id
                    and {item.source for item in response.sources} == set(knowledge_request.sources),
                    "external knowledge response invalid")
            require_work_time()
            after = inspect_peer(pid)
            require(after == peer and owner.launch.grant.is_active(),
                    "external knowledge peer or grant changed during retrieval")
            owner.launch.mount.verify_mounted(pid, owner.launch.sealed)
            require(durable_authority(
                owner.launch.identity, owner.launch.grant.hash,
                provider_id, knowledge_request
            ) is True, "external knowledge durable authority changed")
            if owner.work_authority is not None:
                require(owner.work_authority(
                    owner.launch.identity, owner.launch.grant.hash,
                    kind="tool", tool="herdr_external_knowledge"
                ) is True, "external knowledge phase changed")
            encoded = json.dumps(
                response.to_dict(), sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8") + b"\n"
            require(len(encoded) <= 2_000_000, "external knowledge response exceeds bound")
            connection.settimeout(remaining_work_seconds(5))
            connection.sendall(encoded)
        elif request.get("op") == "work-verify":
            require(set(request) in ({"op", "identity", "grant_sha256", "request_id"}, {"op", "identity", "grant_sha256", "request_id", "handoff"})
                    and "herdr_verify_work" in owner.launch.grant.scope.tools,
                    "verification tool is not granted")
            operation = "work-verify"
            callback = getattr(owner, "work_verify", None)
            require(callable(callback), "host verification authority unavailable")
            from .work_lifetime import check_wall_seconds, require_grant_lifetime
            target=getattr(callback,"__self__",None)
            if target is not None and callable(getattr(target,"cycle",None)):
                current=target.cycle(owner.launch.identity)
                seconds=check_wall_seconds(current.plan,getattr(target,"local_commit_policy",None))
            else:
                seconds=900  # Closed host transport fixture without an exact plan.
            require_grant_lifetime(owner.launch.grant,900)
            from .work_lifetime import bounded_host_request
            with bounded_host_request(seconds):
                outcome = (callback(owner.launch.identity, owner.launch.grant.hash, request["request_id"], handoff=request["handoff"])
                           if "handoff" in request else callback(owner.launch.identity, owner.launch.grant.hash, request["request_id"]))
            require_work_time()
            after = inspect_peer(pid)
            require(after == peer and owner.launch.grant.is_active(),
                    "work authority peer or grant changed during verification")
            owner.launch.mount.verify_mounted(pid, owner.launch.sealed)
            require_work_time()
            encoded = canonical(outcome) + b"\n"
            require(len(encoded) <= 8192, "verification outcome exceeds bound")
            connection.settimeout(remaining_work_seconds(5))
            require_work_time()
            connection.sendall(encoded)
            require_work_time()
        else:
            require(set(request) == {"op", "identity", "grant_sha256", "kind", "tool"}
                    and request["op"] == "work-authorize" and request["kind"] in {"provider", "tool"}
                    and ((request["kind"] == "provider" and request["tool"] is None)
                         or (request["kind"] == "tool" and isinstance(request["tool"], str)
                             and 0 < len(request["tool"]) <= 128)), "work authority binding invalid")
            operation = "work-authorize"
            callback = owner.work_authority
            if callback is not None:
                require(callback(owner.launch.identity, owner.launch.grant.hash,
                                 kind=request["kind"], tool=request["tool"]) is True,
                        "work authority denied")
            connection.sendall(b"work-ok\n")
    except Exception as error:
        if authenticated_binding is not None and operation is not None:
            _observe_authenticated_denial(owner, peer, authenticated_binding, operation, error)
        try:
            connection.sendall(b"denied\n")
        except OSError:
            pass
    finally:
        # Irrelevant peers returned False above still belong to the bootstrap
        # broker and must retain their connection for its own early rejection.
        if accepted_peer:
            connection.close()
    return True
