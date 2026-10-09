from __future__ import annotations

import json
import os
import socket
import threading

from herdr.external_knowledge import (
    KnowledgeErrorCode,
    KnowledgeRequest,
    KnowledgeResponse,
    KnowledgeSourceResult,
)
from herdr.external_knowledge_host import (
    HostExternalKnowledgeClient,
    HostExternalKnowledgePolicy,
)
from tests.herdr.test_security import identity


def response_for(request, answer="found"):
    return KnowledgeResponse(
        request_id=request.request_id,
        status="completed",
        answer=answer,
        sources=tuple(
            KnowledgeSourceResult(source, "ok", 5, answer=f"{source}:{answer}")
            for source in request.sources
        ),
        partial=False,
    )


def test_host_policy_is_explicit_and_source_bounded():
    policy = HostExternalKnowledgePolicy({
        "github:Bbambaaamm/herdr": {
            "corp": ("mail", "chat", "documents"),
        }
    })
    assert policy.allows(
        "github:Bbambaaamm/herdr", "corp", ("mail", "documents")
    )
    assert not policy.allows(
        "github:Bbambaaamm/herdr", "corp", ("mail", "unknown")
    )
    assert not policy.allows(
        "github:Bbambaaamm/herdr", "other", ("mail",)
    )


def test_provider_client_sends_only_provider_and_request_not_grant_identity_or_secret(
    tmp_path, monkeypatch
):
    request = KnowledgeRequest.create(
        "find prior incident",
        ("mail", "chat"),
        request_id="req-1",
    )
    policy = HostExternalKnowledgePolicy({
        identity().consumer: {"corp": ("mail", "chat")}
    })
    monkeypatch.setattr(
        "herdr.external_knowledge_host.HostExternalKnowledgePolicy.from_file",
        lambda _path: policy,
    )
    path = tmp_path / "provider.sock"
    monkeypatch.setattr(
        "herdr.external_knowledge_host._trusted_socket",
        lambda value: value.lstat(),
    )
    received = []
    errors = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        os.chmod(path, 0o600)
        listener.listen(1)
        listener.settimeout(5)

        def serve():
            try:
                connection, _ = listener.accept()
                with connection:
                    raw = bytearray()
                    while b"\n" not in raw:
                        raw.extend(connection.recv(65536))
                    line, _, trailing = bytes(raw).partition(b"\n")
                    assert trailing == b""
                    payload = json.loads(line)
                    received.append(payload)
                    encoded = json.dumps({
                        "response": response_for(request).to_dict()
                    }, separators=(",", ":")).encode() + b"\n"
                    connection.sendall(encoded)
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=serve)
        thread.start()
        client = HostExternalKnowledgeClient(
            policy_path=tmp_path / "unused-policy",
            socket_path=path,
            timeout_seconds=5,
        )
        result = client.query(identity(), "a" * 64, "corp", request)
        thread.join(6)

    assert not thread.is_alive() and not errors
    assert result.status == "completed" and result.answer == "found"
    assert len(received) == 1
    assert set(received[0]) == {"version", "provider_id", "request"}
    assert received[0]["provider_id"] == "corp"
    assert "identity" not in received[0] and "grant_sha256" not in received[0]


def test_policy_denial_never_touches_provider_socket(tmp_path, monkeypatch):
    request = KnowledgeRequest.create("x", ("mail",), request_id="req")
    policy = HostExternalKnowledgePolicy({
        identity().consumer: {"corp": ("documents",)}
    })
    monkeypatch.setattr(
        "herdr.external_knowledge_host.HostExternalKnowledgePolicy.from_file",
        lambda _path: policy,
    )
    client = HostExternalKnowledgeClient(
        policy_path=tmp_path / "unused",
        socket_path=tmp_path / "missing.sock",
    )
    result = client.query(identity(), "b" * 64, "corp", request)
    assert result.status == "error"
    assert result.sources[0].error_code is KnowledgeErrorCode.AUTH_FORBIDDEN
    assert result.sources[0].retryable is False


def test_missing_provider_degrades_only_knowledge_capability(tmp_path, monkeypatch):
    request = KnowledgeRequest.create("x", ("mail",), request_id="req")
    policy = HostExternalKnowledgePolicy({
        identity().consumer: {"corp": ("mail",)}
    })
    monkeypatch.setattr(
        "herdr.external_knowledge_host.HostExternalKnowledgePolicy.from_file",
        lambda _path: policy,
    )
    from herdr.external_knowledge_host import ExternalKnowledgeHostError
    monkeypatch.setattr(
        "herdr.external_knowledge_host._trusted_socket",
        lambda _value: (_ for _ in ()).throw(
            ExternalKnowledgeHostError("provider_socket_unavailable")
        ),
    )
    result = HostExternalKnowledgeClient(
        policy_path=tmp_path / "unused",
        socket_path=tmp_path / "missing.sock",
    ).query(identity(), "c" * 64, "corp", request)
    assert result.status == "error"
    assert result.sources[0].error_code is KnowledgeErrorCode.PROVIDER_UNAVAILABLE
    assert result.sources[0].retryable is True


def test_provider_cannot_expand_or_omit_requested_sources(tmp_path, monkeypatch):
    request = KnowledgeRequest.create("x", ("mail", "chat"), request_id="req")
    policy = HostExternalKnowledgePolicy({
        identity().consumer: {"corp": ("mail", "chat", "documents")}
    })
    monkeypatch.setattr(
        "herdr.external_knowledge_host.HostExternalKnowledgePolicy.from_file",
        lambda _path: policy,
    )
    path = tmp_path / "provider.sock"
    monkeypatch.setattr(
        "herdr.external_knowledge_host._trusted_socket",
        lambda value: value.lstat(),
    )
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        os.chmod(path, 0o600)
        listener.listen(1)

        def serve():
            connection, _ = listener.accept()
            with connection:
                while b"\n" not in connection.recv(65536):
                    pass
                bad = KnowledgeResponse(
                    request_id=request.request_id,
                    status="completed",
                    answer="only mail",
                    sources=(KnowledgeSourceResult("mail", "ok", 1, answer="mail"),),
                    partial=False,
                )
                connection.sendall(
                    json.dumps({"response": bad.to_dict()}).encode() + b"\n"
                )

        thread = threading.Thread(target=serve)
        thread.start()
        result = HostExternalKnowledgeClient(
            policy_path=tmp_path / "unused",
            socket_path=path,
            timeout_seconds=5,
        ).query(identity(), "d" * 64, "corp", request)
        thread.join(5)
    assert result.status == "error"
    assert {
        row.error_code for row in result.sources
    } == {KnowledgeErrorCode.PROVIDER_UNAVAILABLE}
