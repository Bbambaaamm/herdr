"""Fixed synthetic response and verification at the EXISTING host I/O boundary.

This creates no new endpoint, authorization, provider route or model port.
The actual SDK must enter the original authenticated WorkAuthority listener,
reserve/start the original cumulative operation and receive/settle its response.
"""
import json
from pathlib import Path
from herdr.evidence import canonical, digest
from herdr.work_cycle import require

NONCE = "03414499dd0d1986968b2393d44275d0"


def probe_message(identity, grant_sha256, role):
    require(role in {"root", "child"}, "fixed case role required")
    return "HERDR_OFFLINE_GUARDED_INGRESS_1 " + digest({"nonce": NONCE, "role": role,
        "identity": identity.to_json(), "grant_sha256": grant_sha256})


def probe_response(payload, identity, grant, role, ordinal):
    """Return None for ordinary reviewed fixture traffic; never provider fallback."""
    expected = probe_message(identity, grant.hash, role)
    messages = payload.get("messages")
    if not (isinstance(messages, list) and messages and type(messages[-1]) is dict and
            messages[-1].get("role") == "user" and messages[-1].get("content") == expected):
        return None
    # The original complete request/body/provider/quote validation has already
    # run. Preserve legitimate original control schemas; they confer no new
    # authority, and this fixed response never requests a tool invocation.
    require(ordinal == 1 and payload.get("stream", False) is False,
            "single original guarded fixture request required")
    from .security import InvocationGuard
    names = [InvocationGuard(grant).canonical_tool(item["function"]["name"]) for item in payload.get("tools", [])]
    require(len(names) == len(set(names)) and set(names) <= set(grant.scope.tools),
            "fixture tool declarations exceed original admitted grant")
    return {"kind": "http_response", "http_status": 200,
        "body": {"id": "offline-guarded-" + role, "object": "chat.completion",
            "created": 0, "model": payload["model"], "choices": [{"index": 0,
                "message": {"role": "assistant", "content": "guarded-ingress-ok"},
                "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}}


def verify_probe_receipt(factory, launch, *, role):
    from herdr.host_model_transport import _read_private, _fixture_binding, validate_transport_events
    from herdr.work_contract_host import HostWorkContractFactory
    from types import MethodType
    require(type(factory) is HostWorkContractFactory and
        type(launch.mount.bootstrap.work_budget) is MethodType and
        launch.mount.bootstrap.work_budget.__self__ is factory,
        "original bound host model authority required")
    identity = launch.identity
    cycle = factory.cycle(identity)
    events = [row for row in factory.audit_log.replay() if row.get("work_cycle") == identity.to_json()]
    transport = [row for row in events if row.get("event") in {"work_model_transport_intent", "work_model_transport_receipt"}]
    validate_transport_events(transport, identity, cycle.plan.hash, launch.grant.hash)
    intents = [row for row in transport if row["event"] == "work_model_transport_intent"]
    require(len(intents) == 1, "exactly one SDK model ingress required")
    operation_id = intents[0]["operation_id"]
    directory = factory.storage / "model-transport"
    intent = _read_private(directory / (operation_id + ".intent.json"))
    receipt = _read_private(directory / (operation_id + ".response.json"))
    require(receipt["binding"] == intent and intent["identity"] == identity.to_json() and
        intent["grant_sha256"] == launch.grant.hash and intent["plan_sha256"] == cycle.plan.hash and
        receipt["result"]["body"]["id"] == "offline-guarded-" + role and
        receipt["result"]["body"]["choices"][0]["message"]["content"] == "guarded-ingress-ok",
        "original fixed guarded SDK response missing")
    authority = factory.budget_authority
    with authority._serialized():
        state = authority._state()
        op = state["operations"].get(operation_id)
        require(op is not None and op["identity"] == identity.to_json() and op["started"] and
            op["plan_sha256"] == cycle.plan.hash and op["provider"] == "nous" and
            op["usage"] is not None and op["usage"]["model_calls"] == 1 and
            op["usage"]["cost_microusd"] is None and op["demand"]["cost_microusd"] == 0 and
            op["settlement_sha256"], "SDK response not settled in original cumulative budget")
    failures = [row for row in events if row.get("event") in {"work_sdk_observation", "work_host_denial"}]
    require(not failures, "SDK or authenticated ingress denial observed")
    return {"schema": "canonical-guarded-sdk-ingress-1", "outcome": "SDK_GUARDED_SYNTHETIC_INGRESS",
        "role": role, "identity": identity.to_json(), "grant_sha256": launch.grant.hash,
        "plan_sha256": cycle.plan.hash, "operation_id": operation_id,
        "body_sha256": intent["body_sha256"], "response_sha256": digest(receipt),
        "settlement_sha256": op["settlement_sha256"], "synthetic_responses": 1,
        "budget_unknown_measurements": ["work_ms", "tokens", "cost_microusd"],
        "external_model": 0, "external_http": 0, "external_cost": 0,
        "semantic_child_acceptance": "NOT_ESTABLISHED"}
