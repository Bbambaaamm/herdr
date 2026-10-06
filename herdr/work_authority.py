"""Work phase IPC on the already authenticated physical bootstrap authority."""
import json
import os
import socket
import struct

from .bootstrap_authority import SOCKET_PATH, _recv_line, inspect_peer
from .security import InvocationIdentity, PolicyDenied
from .work_cycle import require, WorkContractError
from .evidence import canonical


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
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(5)
                connection.connect(str(SOCKET_PATH))
                connection.sendall(payload)
                result = bytearray()
                while len(result) < 128:
                    chunk = connection.recv(128 - len(result))
                    if not chunk:
                        break
                    result.extend(chunk)
                    if b"\n" in result:
                        break
                if bytes(result) != b"work-ok\n":
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
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(5);connection.connect(str(SOCKET_PATH));connection.sendall(encoded)
                result=bytearray()
                while len(result)<=8192:
                    chunk=connection.recv(min(1024,8193-len(result)))
                    if not chunk:break
                    result.extend(chunk)
                    if b"\n" in result:break
            require(len(result)<=8192 and result.endswith(b"\n"),"bounded budget response required")
            parsed=json.loads(result)
            require(isinstance(parsed,dict),"closed host budget response required")
            return parsed
        except PolicyDenied:raise
        except (EvidenceError,OSError,ValueError,TypeError) as exc:
            raise PolicyDenied("work_budget_unavailable") from exc

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

def _dispatch_work_connection(owner, connection):
    """Only the exact observed stage-two process can ask about its phase.

    Other peers go through the unchanged stage-one admission broker. The
    request itself never advances a phase, records PASS, or changes a plan.
    """
    receipt = owner.launch._published_bootstrap_receipt
    if receipt is None:
        return False
    accepted_peer = False
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
        if request.get("op") == "work-budget":
            require(set(request)=={"op","identity","grant_sha256","action","payload"}
                    and request["action"] in {"status","start","returned"} and isinstance(request["payload"],dict),
                    "closed budget request required")
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
        elif request.get("op") == "work-verify":
            require(set(request) in ({"op", "identity", "grant_sha256", "request_id"}, {"op", "identity", "grant_sha256", "request_id", "handoff"})
                    and "herdr_verify_work" in owner.launch.grant.scope.tools,
                    "verification tool is not granted")
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
            callback = owner.work_authority
            if callback is not None:
                require(callback(owner.launch.identity, owner.launch.grant.hash,
                                 kind=request["kind"], tool=request["tool"]) is True,
                        "work authority denied")
            connection.sendall(b"work-ok\n")
    except Exception:
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
