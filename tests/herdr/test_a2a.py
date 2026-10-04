import json
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from herdr.a2a import (A2AError, Admission, BindingStore, Gateway, HEADER, Identity,
                       decode_child_proposal, discover_card, parse_card, registration)
from herdr.scheduler import AuditLog, DenyReason, DynamicChildScheduler


def setup(tmp_path):
    raw = {"name": "remote", "description": "bounded executor", "version": "1.0.1", "capabilities": {}, "defaultInputModes": ["text/plain"], "defaultOutputModes": ["text/plain"], "skills": [], "supportedInterfaces": [{"url": "https://remote.example/a2a", "protocolBinding": "HTTP+JSON", "protocolVersion": "1.0"}]}
    card = parse_card(raw)
    policy = Admission(card.fingerprint, card.interfaces[0].fingerprint, "remote-exec", "remote-provider", "remote-cap", "remote-runtime", ("read_file",))
    identity = Identity("parent", "child", "task-1", "run-1", 7, "idem-1")
    return raw, card, policy, identity, BindingStore(tmp_path / "binding.json")


def task(state="TASK_STATE_WORKING", task_id="remote-task", context="remote-context", artifacts=None):
    payload = {"id": task_id, "status": {"state": state}, "artifacts": artifacts or []}
    if context is not None:
        payload["contextId"] = context
    return {"task": payload}


class Mock:
    def __init__(self, response=None):
        self.response = response or task()
        self.sends = []
        self.gets = []
        self.cancels = []

    def discover(self, url, headers):
        assert headers == HEADER
        assert url == "https://remote.example/.well-known/agent-card.json"
        return self.discovered

    def send(self, interface, message, headers):
        assert headers == HEADER
        self.sends.append(message)
        return self.response

    def get(self, interface, request, headers):
        assert headers == HEADER
        self.gets.append(request)
        return self.response

    def cancel(self, interface, request, headers):
        assert headers == HEADER
        self.cancels.append(request)
        return task("TASK_STATE_CANCELED")


def test_card_and_registration(tmp_path):
    raw, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    transport.discovered = raw
    assert discover_card(transport, "https://remote.example").fingerprint == card.fingerprint
    assert HEADER == {"A2A-Version": "1.0"}
    assert card.interfaces[0].protocol_binding == "HTTP+JSON"
    assert card.interfaces[0].protocol_version == "1.0"
    assert card.interfaces[0].tenant is None
    assert parse_card(raw).fingerprint == card.fingerprint
    with pytest.raises(A2AError):
        Gateway(Mock(), store, card, replace(policy, card_fingerprint="0" * 64))
    executor, runtime, provenance = registration(card, policy, observed_at="2026-10-04T00:00:00Z", ttl_seconds=60, registry_hash="a" * 64)
    assert executor.id == runtime.executor_id == policy.executor_id
    assert provenance["card_fingerprint"] == card.fingerprint
    assert runtime.health == "unknown"


def test_send_poll_candidate_no_completion(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    gateway = Gateway(transport, store, card, policy)
    assert gateway.send(identity, "do bounded work") == ()
    assert transport.sends[0]["message"]["messageId"] == identity.message_id
    assert store.read()["delivery"] == "bound"
    artifact = {"artifactId": "result-1", "parts": [{"text": "done"}]}
    transport.response = task("TASK_STATE_COMPLETED", artifacts=[artifact])
    candidates = Gateway(transport, store, card, policy).poll(identity)
    assert len(candidates) == 1
    assert candidates[0].identity == identity
    assert candidates[0].content == artifact
    assert candidates[0].acceptance == "requires_shared_85_acceptance"
    assert store.read()["last_observation"] == "TASK_STATE_COMPLETED"
    assert transport.gets == [{"id": "remote-task"}]
    assert len(transport.sends) == 1


def test_ambiguous_send_never_retried(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    def crash(*args):
        transport.sends.append(args)
        raise RuntimeError("lost response")
    transport.send = crash
    with pytest.raises(RuntimeError):
        Gateway(transport, store, card, policy).send(identity, "work")
    assert store.read()["delivery"] == "send_started"
    with pytest.raises(A2AError, match="delivery already started"):
        Gateway(transport, store, card, policy).send(identity, "work")
    assert len(transport.sends) == 1
    with pytest.raises(A2AError, match="reconciliation"):
        Gateway(transport, store, card, policy).poll(identity)


def test_identity_fence_remote_binding_and_cancel(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    Gateway(transport, store, card, policy).send(identity, "work")
    assert identity.message_id != replace(identity, fencing_token=8).message_id
    for wrong in (replace(identity, fencing_token=8), replace(identity, idempotency_key="idem-2")):
        with pytest.raises(A2AError, match="identity"):
            Gateway(transport, store, card, policy).poll(wrong)
    for wrong_response in (task(task_id="other"), task(context="other")):
        transport.response = wrong_response
        with pytest.raises(A2AError, match="remote binding"):
            Gateway(transport, store, card, policy).poll(identity)
    transport.response = task()
    gateway = Gateway(transport, store, card, policy)
    gateway.cancel(identity)
    assert store.read()["cancel_intent"] is True
    Gateway(transport, store, card, policy).retry_cancel(identity)
    assert transport.cancels == [{"id": "remote-task"}, {"id": "remote-task"}]


def test_cancel_intent_survives_lost_response(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    Gateway(transport, store, card, policy).send(identity, "work")
    original_cancel = transport.cancel
    def lost_response(interface, task_id, headers):
        transport.cancels.append(task_id)
        raise RuntimeError("cancel response lost")
    transport.cancel = lost_response
    with pytest.raises(RuntimeError):
        Gateway(transport, store, card, policy).cancel(identity)
    assert store.read()["cancel_intent"] is True
    transport.cancel = original_cancel
    Gateway(transport, store, card, policy).retry_cancel(identity)
    assert transport.cancels == [{"id": "remote-task"}, {"id": "remote-task"}]


def test_direct_message(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock({"message": {"messageId": "reply-1", "contextId": "remote-context", "role": "ROLE_AGENT", "parts": [{"text": "answer"}]}})
    candidates = Gateway(transport, store, card, policy).send(identity, "question")
    assert candidates[0].kind == "message"
    assert candidates[0].remote_task_id is None
    assert store.read()["delivery"] == "direct"
    with pytest.raises(A2AError):
        Gateway(transport, store, card, policy).poll(identity)


def test_message_response_with_task_id_binds_existing_remote_task(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock({"message": {
        "messageId": "reply-task-1",
        "contextId": "remote-context",
        "taskId": "remote-task",
        "role": "ROLE_AGENT",
        "parts": [{"text": "task accepted"}],
    }})
    candidates = Gateway(transport, store, card, policy).send(identity, "question")
    assert candidates[0].remote_task_id == "remote-task"
    assert candidates[0].remote_context_id == "remote-context"
    bound = store.read()
    assert bound["delivery"] == "bound"
    assert bound["remote_task_id"] == "remote-task"
    assert bound["remote_context_id"] == "remote-context"
    assert bound["last_observation"] == "message"

    transport.response = task("TASK_STATE_WORKING")
    assert Gateway(transport, store, card, policy).poll(identity) == ()
    assert transport.gets == [{"id": "remote-task"}]
    assert len(transport.sends) == 1


def test_malformed_and_secret_card_and_results(tmp_path):
    raw, card, policy, identity, store = setup(tmp_path)
    for bad in ({**raw, "supportedInterfaces": [{**raw["supportedInterfaces"][0], "protocolVersion": "1.0.1"}]},
                {**raw, "x": 1}, {**raw, "description": "password=abc"},
                {**raw, "description": "x" * 33000}):
        with pytest.raises(A2AError):
            parse_card(bad)
    for bad in (task(artifacts=[{"artifactId": "a", "parts": [{"text": "x" * 132000}]}]),
                task(artifacts=[{"artifactId": "a", "parts": [{"raw": "x", "text": "y"}]}]),
                task(state="BOGUS")):
        with pytest.raises(A2AError):
            Gateway(Mock(bad), BindingStore(tmp_path / ("bad-" + str(len(json.dumps(bad))) + ".json")), card, policy).send(identity, "work")


def test_child_proposal_is_data_only(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    artifact = {"artifactId": "proposal", "parts": [{"text": json.dumps({"child_role": "reader", "child_tools": ["patch"], "child_permissions": ["admin"], "child_task": "change files"})}]}
    gateway = Gateway(Mock(task("TASK_STATE_COMPLETED", artifacts=[artifact])), store, card, policy)
    candidate = gateway.send(identity, "work")[0]
    proposal = decode_child_proposal(candidate, parent_role="reader", parent_tools=("read_file",), parent_permissions=("read",))
    # Consumer validation denies the proposed escalation; decoding has no scheduler handle.
    scheduler = DynamicChildScheduler(clock=lambda: 1.0, audit_log=AuditLog(tmp_path / "events.jsonl"))
    before = scheduler.snapshot()
    decision = scheduler.evaluate_child_proposal(proposal)
    assert not decision
    assert decision.reason in {DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST, DenyReason.CHILD_TOOL_ESCALATION}
    assert scheduler.snapshot() == before
    assert not hasattr(gateway, "spawn_child")


def test_gateway_has_no_reviewer_dependency():
    source = (Path(__file__).parents[2] / "herdr" / "a2a.py").read_text()
    assert "herdr.reviewer" not in source


def test_normative_card_fields_and_grpc(tmp_path):
    raw, _, _, _, _ = setup(tmp_path)
    for field in ("name", "description", "version", "supportedInterfaces", "capabilities", "defaultInputModes", "defaultOutputModes", "skills"):
        with pytest.raises(A2AError):
            parse_card({key: value for key, value in raw.items() if key != field})
    for change in ({"capabilities": []}, {"skills": ["invalid"]}, {"defaultInputModes": []}, {"description": 7}):
        with pytest.raises(A2AError):
            parse_card({**raw, **change})
    grpc = {**raw, "supportedInterfaces": [{"url": "remote.example:443", "protocolBinding": "GRPC", "protocolVersion": "1.0", "tenant": "team-1"}]}
    assert parse_card(grpc).interfaces[0].url == "remote.example:443"
    for address in ("http://remote.example", "remote.example:0", "remote.example:99999", "../socket"):
        with pytest.raises(A2AError):
            parse_card({**grpc, "supportedInterfaces": [{**grpc["supportedInterfaces"][0], "url": address}]})


def test_tenant_sent_in_service_requests(tmp_path):
    raw, _, _, identity, store = setup(tmp_path)
    raw["supportedInterfaces"][0]["tenant"] = "team-1"
    card = parse_card(raw)
    policy = Admission(card.fingerprint, card.interfaces[0].fingerprint, "remote-exec", "remote-provider", "remote-cap", "remote-runtime", ())
    transport = Mock()
    gateway = Gateway(transport, store, card, policy)
    gateway.send(identity, "work")
    gateway.poll(identity)
    gateway.cancel(identity)
    assert transport.sends[0]["tenant"] == "team-1"
    assert transport.gets == [{"id": "remote-task", "tenant": "team-1"}]
    assert transport.cancels == [{"id": "remote-task", "tenant": "team-1"}]


def test_parts_and_agent_context(tmp_path):
    _, card, policy, identity, _ = setup(tmp_path)
    valid_parts = ({"data": {"answer": 1}}, {"data": [1, "x"]}, {"data": "scalar"}, {"data": 7}, {"data": True}, {"data": None}, {"raw": "YQ==", "mediaType": "application/octet-stream"})
    for index, part in enumerate(valid_parts):
        Gateway(Mock(task(artifacts=[{"artifactId": "a", "parts": [part]}])), BindingStore(tmp_path / f"valid-{index}.json"), card, policy).send(identity, "work")
    for part in ({"raw": "!!!"}, {"raw": "YQ="}, {"raw": "YQ==", "data": {}}, {"data": object()}):
        with pytest.raises(A2AError):
            Gateway(Mock(task(artifacts=[{"artifactId": "a", "parts": [part]}])), BindingStore(tmp_path / ("invalid-" + str(len(list(tmp_path.iterdir()))) + ".json")), card, policy).send(identity, "work")
    with pytest.raises(A2AError, match="contextId"):
        Gateway(Mock({"message": {"messageId": "reply", "role": "ROLE_AGENT", "parts": [{"text": "answer"}]}}), BindingStore(tmp_path / "no-context.json"), card, policy).send(identity, "work")


def test_binding_symlink_and_nonregular_rejected(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    other = tmp_path / "other.json"
    other.write_text("{}")
    store.path.symlink_to(other)
    with pytest.raises(A2AError):
        store.read()
    with pytest.raises(A2AError):
        Gateway(Mock(), store, card, policy).send(identity, "work")
    store.path.unlink()
    store.path.mkdir()
    with pytest.raises(A2AError):
        store.read()


def test_concurrent_poll_cancel_preserves_intent(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    Gateway(transport, store, card, policy).send(identity, "work")
    entered = threading.Event()
    release = threading.Event()
    original_get = transport.get
    def slow_get(*args):
        entered.set()
        assert release.wait(5)
        return original_get(*args)
    transport.get = slow_get
    failures = []
    def poll():
        try:
            Gateway(transport, store, card, policy).poll(identity)
        except Exception as exc:
            failures.append(exc)
    def cancel():
        try:
            Gateway(transport, store, card, policy).cancel(identity)
        except Exception as exc:
            failures.append(exc)
    first = threading.Thread(target=poll)
    second = threading.Thread(target=cancel)
    first.start()
    assert entered.wait(5)
    second.start()
    release.set()
    first.join(5)
    second.join(5)
    assert not first.is_alive() and not second.is_alive() and not failures
    assert store.read()["cancel_intent"] is True
    assert transport.cancels == [{"id": "remote-task"}]


def test_stale_task_and_discovery_is_not_admission(tmp_path):
    raw, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    transport.discovered = raw
    discovered = discover_card(transport, "https://remote.example")
    with pytest.raises(A2AError, match="admitted"):
        Gateway(transport, store, discovered, replace(policy, card_fingerprint="0" * 64))
    Gateway(transport, store, card, policy).send(identity, "work")
    for stale in (replace(identity, task_id="other-task"), replace(identity, child_agent_id="other-child"), replace(identity, run_token="other-run")):
        with pytest.raises(A2AError, match="identity"):
            Gateway(transport, store, card, policy).poll(stale)
    assert len(transport.sends) == 1


def test_late_remote_completion_is_candidate_only(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    gateway = Gateway(transport, store, card, policy)
    gateway.send(identity, "work")
    gateway.cancel(identity)
    transport.response = task("TASK_STATE_COMPLETED", artifacts=[{"artifactId": "late", "parts": [{"data": {"result": "ok"}}]}])
    candidate, = Gateway(transport, store, card, policy).poll(identity)
    assert candidate.acceptance == "requires_shared_85_acceptance"
    assert candidate.identity == identity
    assert store.read()["cancel_intent"] is True
    assert store.read()["last_observation"] == "TASK_STATE_COMPLETED"


def test_task_context_optional_unspecified_state_and_context_binding(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock(task("TASK_STATE_UNSPECIFIED", context=None))
    assert Gateway(transport, store, card, policy).send(identity, "work") == ()
    bound = store.read()
    assert bound["remote_task_id"] == "remote-task"
    assert bound["remote_context_id"] is None
    assert bound["last_observation"] == "TASK_STATE_UNSPECIFIED"

    # Remote context is execution metadata. Once the first task response bound
    # its exact absence, a later context cannot silently create a new session
    # identity or reset Herdr's economic fence.
    transport.response = task("TASK_STATE_WORKING", context="late-context")
    with pytest.raises(A2AError, match="remote binding"):
        Gateway(transport, store, card, policy).poll(identity)
    assert len(transport.sends) == 1


def test_concurrent_send_has_single_economic_dispatch(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    entered = threading.Event()
    release = threading.Event()
    original_send = transport.send

    def slow_send(*args):
        entered.set()
        assert release.wait(5)
        return original_send(*args)

    transport.send = slow_send
    outcomes = []

    def invoke():
        try:
            Gateway(transport, store, card, policy).send(identity, "work")
            outcomes.append("sent")
        except A2AError as exc:
            outcomes.append(str(exc))

    first = threading.Thread(target=invoke)
    second = threading.Thread(target=invoke)
    first.start()
    assert entered.wait(5)
    second.start()
    release.set()
    first.join(5)
    second.join(5)
    assert sorted(outcomes) == [
        "delivery already started; reconcile ambiguous send",
        "sent",
    ]
    assert len(transport.sends) == 1
