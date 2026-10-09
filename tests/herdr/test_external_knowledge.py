from __future__ import annotations

from dataclasses import replace

import pytest

from herdr.external_knowledge import (
    ExternalKnowledgeRegistry,
    KnowledgeContractError,
    KnowledgeErrorCode,
    KnowledgeRequest,
    KnowledgeResponse,
    KnowledgeSourceResult,
    ProviderHealth,
)


def ok_source(name="mail"):
    return KnowledgeSourceResult(name, "ok", 10, answer="evidence", conversation_id="cid")


def error_source(name="chat"):
    return KnowledgeSourceResult(
        name, "error", 20, error_code=KnowledgeErrorCode.UPSTREAM_TRANSIENT, retryable=True
    )


class Provider:
    provider_id = "example-provider"

    def __init__(self, response):
        self.response = response

    def health(self):
        return ProviderHealth("ready")

    def query(self, request):
        return replace(self.response, request_id=request.request_id)


def test_request_is_closed_bounded_and_serializable():
    item = KnowledgeRequest.create("find incident", ("mail", "chat"), request_id="req-1")
    assert item.to_dict() == {
        "request_id": "req-1",
        "query": "find incident",
        "sources": ["mail", "chat"],
        "mode": "search",
    }
    with pytest.raises(KnowledgeContractError, match="invalid_query"):
        KnowledgeRequest.create("", ("mail",))
    with pytest.raises(KnowledgeContractError, match="invalid_sources"):
        KnowledgeRequest.create("x", ("mail", "mail"))
    with pytest.raises(KnowledgeContractError, match="invalid_sources"):
        KnowledgeRequest.create("x", ("../../mail",))


def test_success_partial_and_error_response_invariants():
    complete = KnowledgeResponse("req", "completed", "answer", (ok_source(),), False)
    assert complete.to_dict()["meta"] == {"partial": False}

    partial = KnowledgeResponse(
        "req", "completed", "answer", (ok_source(), error_source()), True
    )
    assert partial.partial

    failed = KnowledgeResponse("req", "error", "", (error_source("mail"),), False)
    assert failed.status == "error"

    with pytest.raises(KnowledgeContractError, match="invalid_partial_flag"):
        KnowledgeResponse("req", "completed", "answer", (ok_source(), error_source()), False)
    with pytest.raises(KnowledgeContractError, match="invalid_error_response"):
        KnowledgeResponse("req", "error", "invented", (error_source("mail"),), False)


def test_source_result_never_mixes_success_and_error_payloads():
    with pytest.raises(KnowledgeContractError, match="invalid_source_success"):
        KnowledgeSourceResult(
            "mail", "ok", 1, answer="x",
            error_code=KnowledgeErrorCode.UPSTREAM_TRANSIENT,
        )
    with pytest.raises(KnowledgeContractError, match="invalid_source_error"):
        KnowledgeSourceResult(
            "mail", "error", 1, answer="raw provider error",
            error_code=KnowledgeErrorCode.INTERNAL_ERROR,
        )


def test_registry_is_explicit_duplicate_safe_and_source_monotonic():
    registry = ExternalKnowledgeRegistry()
    response = KnowledgeResponse("placeholder", "completed", "x", (ok_source(),), False)
    registry.register(Provider(response))
    assert registry.provider_ids() == ("example-provider",)
    assert registry.health("example-provider") == ProviderHealth("ready")

    request = KnowledgeRequest.create("x", ("mail",), request_id="req")
    assert registry.query("example-provider", request).request_id == "req"

    with pytest.raises(KnowledgeContractError, match="duplicate_provider"):
        registry.register(Provider(response))

    expanded = KnowledgeResponse(
        "placeholder", "completed", "x",
        (ok_source("mail"), ok_source("chat")), False,
    )
    other = ExternalKnowledgeRegistry()
    other.register(Provider(expanded))
    with pytest.raises(KnowledgeContractError, match="provider_source_mismatch"):
        other.query("example-provider", request)

    omitted = ExternalKnowledgeRegistry()
    omitted.register(Provider(KnowledgeResponse(
        "placeholder", "completed", "x", (ok_source("mail"),), False
    )))
    broad_request = KnowledgeRequest.create("x", ("mail", "chat"), request_id="broad")
    with pytest.raises(KnowledgeContractError, match="provider_source_mismatch"):
        omitted.query("example-provider", broad_request)


def test_registry_rejects_unknown_or_mismatched_provider_response():
    registry = ExternalKnowledgeRegistry()
    with pytest.raises(KnowledgeContractError, match="unknown_provider"):
        registry.health("missing")

    class WrongProvider(Provider):
        def query(self, request):
            return self.response

    response = KnowledgeResponse("other", "completed", "x", (ok_source(),), False)
    registry.register(WrongProvider(response))
    request = KnowledgeRequest.create("x", ("mail",), request_id="req")
    with pytest.raises(KnowledgeContractError, match="provider_response_mismatch"):
        registry.query("example-provider", request)


def test_health_contract_is_closed():
    assert ProviderHealth("auth_required", KnowledgeErrorCode.AUTH_REQUIRED).status == "auth_required"
    with pytest.raises(KnowledgeContractError, match="invalid_ready_health"):
        ProviderHealth("ready", KnowledgeErrorCode.AUTH_REQUIRED)
    with pytest.raises(KnowledgeContractError, match="invalid_failed_health"):
        ProviderHealth("unavailable")
