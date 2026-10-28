"""Credential-free adapter to the existing root-owned GitHub transport.

The original ParentArtifactPublisher still verifies the result and owns its
durable intent ledger. This channel executes only its three transport methods.
"""
from types import SimpleNamespace
import base64
import ctypes
import json
import os
import re
import socket
import struct
import time

from .parent_publication import require
from .evidence import EvidenceUnavailable

MAX_FRAME = 3000000


def _peer(connection):
    return struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))


def _read(connection):
    def exact(size):
        raw = bytearray()
        while len(raw) < size:
            block = connection.recv(min(65536, size-len(raw)))
            if not block:
                raise ValueError("short publication frame")
            raw.extend(block)
        return bytes(raw)
    size = struct.unpack("!I", exact(4))[0]
    require(0 < size <= MAX_FRAME, "bounded publication frame required")
    return json.loads(exact(size), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def _write(connection, value):
    raw = json.dumps(value, separators=(",", ":"), allow_nan=False).encode()
    require(0 < len(raw) <= MAX_FRAME, "bounded publication frame required")
    connection.sendall(struct.pack("!I", len(raw)) + raw)


class GitHubParentTransportProxy:
    def __init__(self, *, permit, address, root_pid):
        require(type(address) is str and address.startswith("herdr-parent-") and len(address) <= 100
                and type(root_pid) is int and root_pid > 0, "closed root publication peer required")
        require(ctypes.CDLL(None).prctl(3, 0, 0, 0, 0) == 0, "protected publication caller required")
        self.permit, self.address, self.root_pid = permit, address, root_pid

    def protect_from(self, writable_roots):
        # No local credentials or scratch directory exist on this side.
        pass

    def _call(self, method, permit, artifact, **values):
        require(permit == self.permit, "publication permit changed")
        remaining = permit.expires_at_epoch - time.time()
        require(remaining > 0, "publication permit expired")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(min(200, remaining))
            connection.connect("\0"+self.address)
            require(_peer(connection)[:2] == (self.root_pid, 0), "root publication peer changed")
            _write(connection, {"method": method, "permit": permit.hash,
                "commit_sha": artifact.commit_sha, **values})
            answer = _read(connection)
        require(type(answer) is dict and set(answer) == {"ok", "result"} and type(answer["ok"]) is bool,
                "closed publication response required")
        if not answer["ok"]:
            raise EvidenceUnavailable("root publication transport stopped; reconcile original")
        return answer["result"]

    def observe(self, permit, artifact):
        return self._call("observe", permit, artifact)

    def push(self, permit, artifact, bundle):
        require(type(bundle) is bytes and 0 < len(bundle) <= 2000000, "bounded publication bundle required")
        return self._call("push", permit, artifact, bundle=base64.b64encode(bundle).decode("ascii"))

    def create_pull_request(self, permit, artifact, request):
        return self._call("create_pull_request", permit, artifact, request=request)


def execute_request(request, *, permit, transport):
    """No arbitrary executable, URL, repository, grant, or budget on this port."""
    require(type(request) is dict and request.get("permit") == permit.hash, "publication permit changed")
    method = request.get("method")
    extra = {"bundle"} if method == "push" else {"request"} if method == "create_pull_request" else set()
    require(method in {"observe", "push", "create_pull_request"}
            and set(request) == {"method", "permit", "commit_sha"} | extra
            and type(request["commit_sha"]) is str and re.fullmatch("[0-9a-f]{40}", request["commit_sha"])
            and time.time() < permit.expires_at_epoch, "closed publication operation required")
    artifact = SimpleNamespace(commit_sha=request["commit_sha"])
    if method == "observe":
        return transport.observe(permit, artifact)
    if method == "push":
        require(type(request["bundle"]) is str and len(request["bundle"]) <= 2666668, "bounded publication bundle required")
        bundle = base64.b64decode(request["bundle"], validate=True)
        require(0 < len(bundle) <= 2000000, "bounded publication bundle required")
        return transport.push(permit, artifact, bundle)
    body = request["request"]
    require(type(body) is dict and set(body) in ({"title", "body", "head", "base"}, {"title", "body", "head", "base", "draft"})
            and body["head"] == permit.head_branch and body["base"] == permit.base_branch
            and body.get("draft", True) is True and type(body["title"]) is str and len(body["title"]) <= 256
            and type(body["body"]) is str and len(body["body"].encode()) <= 65536,
            "closed publication pull request required")
    return transport.create_pull_request(permit, artifact, body)


def serve_parent_transport(listener, process, *, permit, transport, timeout=210):
    require(os.geteuid() == 0, "root publication executor required")
    deadline = time.monotonic() + timeout
    attempts = 0
    while process.poll() is None:
        require(time.monotonic() < deadline and attempts < 32, "bounded publication executor stopped")
        listener.settimeout(min(.2, max(.001, deadline-time.monotonic())))
        try:
            connection, _ = listener.accept()
        except socket.timeout:
            continue
        attempts += 1
        with connection:
            # The original publisher is exec'ed without a fork between the
            # recorded Popen PID and the protected host entrypoint.
            if _peer(connection)[:2] != (process.pid, 1001) or process.poll() is not None:
                continue
            connection.settimeout(min(200, max(.001, deadline-time.monotonic())))
            try:
                result = execute_request(_read(connection), permit=permit, transport=transport)
                _write(connection, {"ok": True, "result": result})
            except Exception:
                _write(connection, {"ok": False, "result": None})
                raise EvidenceUnavailable("root publication operation stopped; reconcile original") from None
    return process.returncode
