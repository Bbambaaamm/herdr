from __future__ import annotations

import socket
import threading
from dataclasses import replace

import pytest

from herdr.external_knowledge import (
    KnowledgeRequest,
    KnowledgeResponse,
    KnowledgeSourceResult,
)
from herdr.external_knowledge_tool import ARGUMENTS, TOOL
from herdr.security import RiskClass, ToolRule
from herdr.work_authority import WorkAuthorityClient, dispatch_work_connection
from tests.herdr.test_work_authority import owner_for
from tests.herdr.test_work_contract_host import factory_fixture


def ready(tmp_path):
    factory, root, plan, grant, log = factory_fixture(tmp_path)
    rule = ToolRule(TOOL, RiskClass.READ, ARGUMENTS, requires_sandbox=True)
    grant = replace(
        grant,
        scope=replace(grant.scope, tools=(*grant.scope.tools, TOOL)),
        tool_rules=(*grant.tool_rules, rule),
    )
    plan = replace(plan, grant_sha256=grant.hash)
    factory.approve = lambda **_kwargs: plan
    factory.prepare(
        identity=plan.identity,
        workspace=root,
        grant=grant,
        spec_sha256=plan.spec_sha256,
    )
    return factory, root, plan, grant, log


def response(request, answer="found"):
    return KnowledgeResponse(
        request.request_id,
        "completed",
        answer,
        tuple(
            KnowledgeSourceResult(source, "ok", 10, answer=f"{source}:{answer}")
            for source in request.sources
        ),
        False,
    )


def test_authenticated_bootstrap_peer_can_retrieve_but_callback_sees_exact_binding(
    tmp_path, monkeypatch
):
    factory, _root, _plan, grant, _log = ready(tmp_path)
    owner, observed = owner_for(factory, grant)
    calls = []

    def query(identity, grant_sha256, provider_id, request):
        calls.append((identity, grant_sha256, provider_id, request))
        return response(request)

    owner.external_knowledge_authority = lambda *_args: True
    owner.external_knowledge_query = query
    path = tmp_path / "authority.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH", path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    listener.listen(1)
    listener.settimeout(5)
    errors = []

    def serve():
        try:
            connection, _ = listener.accept()
            assert dispatch_work_connection(owner, connection)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        request = KnowledgeRequest.create(
            "Find prior repair", ("mail", "documents"), request_id="req-1"
        )
        result = WorkAuthorityClient().external_knowledge(
            grant.identity, grant.hash, "corp", request
        )
        thread.join(6)
    finally:
        listener.close()

    assert not thread.is_alive() and not errors
    assert result.status == "completed" and result.answer == "found"
    assert len(calls) == 1
    assert calls[0][0] == grant.identity
    assert calls[0][1] == grant.hash
    assert calls[0][2] == "corp"
    assert calls[0][3] == request
    assert len(observed) == 2


def test_host_withholds_result_if_work_phase_changes_during_external_retrieval(
    tmp_path, monkeypatch
):
    factory, root, plan, grant, _log = ready(tmp_path)
    owner, _observed = owner_for(factory, grant)

    def query(identity, _grant_sha256, _provider_id, request):
        # Move the work cycle out of WORK while the remote read is in flight.
        (root / "result.py").write_text(
            "def approved():\n    return 3\n\ndef foreign():\n    return 2\n"
        )
        factory.verify(identity)
        return response(request, "must-not-cross-phase-boundary")

    owner.external_knowledge_authority = lambda *_args: True
    owner.external_knowledge_query = query
    path = tmp_path / "authority.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH", path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    listener.listen(1)
    listener.settimeout(5)

    thread = threading.Thread(
        target=lambda: dispatch_work_connection(owner, listener.accept()[0]),
        daemon=True,
    )
    thread.start()
    try:
        request = KnowledgeRequest.create("x", ("mail",), request_id="phase")
        try:
            WorkAuthorityClient().external_knowledge(
                grant.identity, grant.hash, "corp", request
            )
            raised = False
        except Exception as exc:
            raised = True
            assert "external_knowledge" in str(exc)
        thread.join(6)
    finally:
        listener.close()
    assert raised
    assert factory.cycle(plan.identity).phase.value != "work"


def test_unbound_host_callback_fails_closed_without_provider_call(tmp_path, monkeypatch):
    factory, _root, _plan, grant, _log = ready(tmp_path)
    owner, _observed = owner_for(factory, grant)
    owner.external_knowledge_authority = lambda *_args: True
    path = tmp_path / "authority.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH", path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    listener.listen(1)
    listener.settimeout(5)
    thread = threading.Thread(
        target=lambda: dispatch_work_connection(owner, listener.accept()[0]),
        daemon=True,
    )
    thread.start()
    try:
        request = KnowledgeRequest.create("x", ("mail",), request_id="missing")
        try:
            WorkAuthorityClient().external_knowledge(
                grant.identity, grant.hash, "corp", request
            )
            raised = False
        except Exception as exc:
            raised = True
            assert "external_knowledge" in str(exc)
        thread.join(6)
    finally:
        listener.close()
    assert raised


def test_durable_authority_change_during_retrieval_withholds_result_without_work_gate(
    tmp_path, monkeypatch
):
    factory, _root, _plan, grant, _log = ready(tmp_path)
    owner, _observed = owner_for(factory, grant)
    owner.work_authority = None
    checks = []

    def authority(*_args):
        checks.append(1)
        return len(checks) == 1

    def query(_identity, _grant_sha256, _provider_id, request):
        return response(request, "must-not-cross-durable-boundary")

    owner.external_knowledge_authority = authority
    owner.external_knowledge_query = query
    path = tmp_path / "authority.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH", path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    listener.listen(1)
    listener.settimeout(5)
    thread = threading.Thread(
        target=lambda: dispatch_work_connection(owner, listener.accept()[0]),
        daemon=True,
    )
    thread.start()
    try:
        request = KnowledgeRequest.create("x", ("mail",), request_id="revoked")
        with pytest.raises(Exception, match="external_knowledge"):
            WorkAuthorityClient().external_knowledge(
                grant.identity, grant.hash, "corp", request
            )
        thread.join(6)
    finally:
        listener.close()
    assert checks == [1, 1]
