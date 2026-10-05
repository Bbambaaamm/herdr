import json
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from herdr import a2a as a2a_module
from herdr.a2a import (A2AError, Admission, BindingStore, Gateway, HEADER, Identity,
                       decode_child_proposal, discover_card, parse_card, registration)
from herdr.scheduler import AuditLog, DenyReason, DynamicChildScheduler




@pytest.fixture(autouse=True)
def _isolated_economic_claim_root(monkeypatch, tmp_path):
    """Tests keep the production economic namespace contract without /var writes."""
    monkeypatch.setattr(
        a2a_module, "ECONOMIC_CLAIM_ROOT", tmp_path / ".economic-claims"
    )

def setup(tmp_path):
    raw = {
        "name": "remote",
        "description": "bounded executor",
        "version": "1.0.1",
        "capabilities": {},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [{
            "id": "bounded-work",
            "name": "Bounded work",
            "description": "Perform bounded delegated work.",
            "tags": ["bounded"],
        }],
        "supportedInterfaces": [{
            "url": "https://remote.example/a2a",
            "protocolBinding": "HTTP+JSON",
            "protocolVersion": "1.0",
        }],
    }
    card = parse_card(raw)
    policy = Admission(
        card.fingerprint, card.interfaces[0].fingerprint, "remote-exec",
        "remote-provider", "remote-cap", "remote-runtime", ("read_file",), str(tmp_path),
    )
    identity = Identity("github:repo", "parent", "child", "task-1", "run-1", 7, "idem-1")
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
    assert transport.sends[0]["configuration"] == {"returnImmediately": True, "historyLength": 0}
    assert store.read()["delivery"] == "bound"
    artifact = {"artifactId": "result-1", "parts": [{"text": "done"}]}
    transport.response = task("TASK_STATE_COMPLETED", artifacts=[artifact])
    candidates = Gateway(transport, store, card, policy).poll(identity)
    assert len(candidates) == 1
    assert candidates[0].identity == identity
    assert candidates[0].content == artifact
    assert candidates[0].acceptance == "requires_shared_85_acceptance"
    assert store.read()["last_observation"] == "TASK_STATE_COMPLETED"
    assert transport.gets == [{"id": "remote-task", "historyLength": 0}]
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
    # Simulate caller loss/restart after the durable direct state was written.
    restarted = Gateway(transport, store, card, policy)
    recovered = restarted.recover(identity)
    assert len(recovered) == 1 and recovered[0].digest == candidates[0].digest
    assert restarted.poll(identity)[0].digest == candidates[0].digest
    assert transport.gets == []
    assert len(transport.sends) == 1


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
    assert transport.gets == [{"id": "remote-task", "historyLength": 0}]
    assert len(transport.sends) == 1


def test_malformed_and_secret_card_and_results(tmp_path):
    raw, card, policy, identity, store = setup(tmp_path)
    for bad in ({**raw, "supportedInterfaces": [{**raw["supportedInterfaces"][0], "protocolVersion": "1.0.1"}]},
                {**raw, "x": 1}, {**raw, "description": "password=abc"},
                {**raw, "description": "x" * 33000}):
        with pytest.raises(A2AError):
            parse_card(bad)
    for index, bad in enumerate((
        task(artifacts=[{"artifactId": "a", "parts": [{"text": "x" * 132000}]}]),
        task(artifacts=[{"artifactId": "a", "parts": [{"raw": "x", "text": "y"}]}]),
        task(state="BOGUS"),
    )):
        attempt = replace(identity, idempotency_key=f"bad-{index}")
        with pytest.raises(A2AError):
            Gateway(
                Mock(bad), BindingStore(tmp_path / f"bad-{index}.json"), card, policy
            ).send(attempt, "work")


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
    for change in (
        {"capabilities": []},
        {"skills": []},
        {"skills": ["invalid"]},
        {"defaultInputModes": []},
        {"description": 7},
    ):
        with pytest.raises(A2AError):
            parse_card({**raw, **change})
    grpc = {
        **raw,
        "supportedInterfaces": [{
            "url": "https://grpc.remote.example/a2a",
            "protocolBinding": "GRPC",
            "protocolVersion": "1.0",
            "tenant": "team-1",
        }],
    }
    assert parse_card(grpc).interfaces[0].url == "https://grpc.remote.example/a2a"
    for address in (
        "http://remote.example",
        "remote.example:443",
        "remote.example:0",
        "../socket",
    ):
        with pytest.raises(A2AError):
            parse_card({
                **grpc,
                "supportedInterfaces": [{**grpc["supportedInterfaces"][0], "url": address}],
            })


def test_tenant_sent_in_service_requests(tmp_path):
    raw, _, _, identity, store = setup(tmp_path)
    raw["supportedInterfaces"][0]["tenant"] = "org=東京 west"
    card = parse_card(raw)
    policy = Admission(
        card.fingerprint, card.interfaces[0].fingerprint, "remote-exec",
        "remote-provider", "remote-cap", "remote-runtime", (), str(tmp_path),
    )
    transport = Mock()
    gateway = Gateway(transport, store, card, policy)
    gateway.send(identity, "work")
    gateway.poll(identity)
    gateway.cancel(identity)
    assert transport.sends[0]["tenant"] == "org=東京 west"
    assert transport.gets == [{
        "id": "remote-task", "historyLength": 0, "tenant": "org=東京 west"
    }]
    assert transport.cancels == [{"id": "remote-task", "tenant": "org=東京 west"}]


def test_parts_and_agent_context(tmp_path):
    _, card, policy, identity, _ = setup(tmp_path)
    valid_parts = (
        {"data": {"answer": 1}},
        {"data": [1, "x"]},
        {"data": "scalar"},
        {"data": 7},
        {"data": True},
        {"data": None},
        {"raw": "YQ==", "mediaType": "application/octet-stream"},
        {"raw": "YQ", "mediaType": "application/octet-stream"},
        {"raw": "-_8", "mediaType": "application/octet-stream"},
    )
    for index, part in enumerate(valid_parts):
        attempt = replace(identity, idempotency_key=f"valid-part-{index}")
        Gateway(
            Mock(task(artifacts=[{"artifactId": "a", "parts": [part]}])),
            BindingStore(tmp_path / f"valid-{index}.json"), card, policy,
        ).send(attempt, "work")
    for index, part in enumerate((
        {"raw": "!!!"}, {"raw": "A"}, {"raw": "YQ==", "data": {}}, {"data": object()},
    )):
        attempt = replace(identity, idempotency_key=f"invalid-part-{index}")
        with pytest.raises(A2AError):
            Gateway(
                Mock(task(artifacts=[{"artifactId": "a", "parts": [part]}])),
                BindingStore(tmp_path / f"invalid-{index}.json"), card, policy,
            ).send(attempt, "work")
    with pytest.raises(A2AError, match="contextId"):
        Gateway(
            Mock({"message": {"messageId": "reply", "role": "ROLE_AGENT", "parts": [{"text": "answer"}]}}),
            BindingStore(tmp_path / "no-context.json"), card, policy,
        ).send(replace(identity, idempotency_key="no-context"), "work")


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

    # Absence is an unobserved optional field. Its first later observation
    # binds metadata without changing the Herdr identity or economic fence.
    transport.response = task("TASK_STATE_WORKING", context="late-context")
    assert Gateway(transport, store, card, policy).poll(identity)==()
    assert store.read()["remote_context_id"]=="late-context"
    assert store.read()["identity"]==bound["identity"]
    transport.response=task("TASK_STATE_WORKING",context="foreign-context")
    with pytest.raises(A2AError,match="remote binding"):
        Gateway(transport,store,card,policy).poll(identity)
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


def test_cancel_task_terminal_artifact_is_durable_candidate(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    gateway = Gateway(transport, store, card, policy)
    gateway.send(identity, "work")
    artifact = {"artifactId": "cancel-race", "parts": [{"text": "completed while cancelling"}]}

    def completed_cancel(interface, request, headers):
        transport.cancels.append(request)
        return task("TASK_STATE_COMPLETED", artifacts=[artifact])

    transport.cancel = completed_cancel
    candidates = gateway.cancel(identity)
    assert len(candidates) == 1
    assert candidates[0].content == artifact
    restarted = Gateway(transport, store, card, policy)
    recovered = restarted.recover(identity)
    assert len(recovered) == 1
    assert recovered[0].digest == candidates[0].digest
    assert recovered[0].acceptance == "requires_shared_85_acceptance"
    assert store.read()["last_observation"] == "TASK_STATE_COMPLETED"


def test_part_url_allows_signed_query_but_not_embedded_credentials(tmp_path):
    _, card, policy, identity, _ = setup(tmp_path)
    signed = "https://files.example/download/report?token=opaque-signed-reference&expires=123"
    response = task("TASK_STATE_COMPLETED", artifacts=[
        {"artifactId": "file", "parts": [{"url": signed, "mediaType": "application/octet-stream"}]}
    ])
    candidate, = Gateway(
        Mock(response), BindingStore(tmp_path / "signed-url.json"), card, policy
    ).send(replace(identity, idempotency_key="signed-url"), "work")
    assert candidate.content["parts"][0]["url"] == signed

    bad = task("TASK_STATE_COMPLETED", artifacts=[
        {"artifactId": "file", "parts": [{"url": "https://user:pass@files.example/download?x=1"}]}
    ])
    with pytest.raises(A2AError, match="part URL"):
        Gateway(
            Mock(bad), BindingStore(tmp_path / "bad-url.json"), card, policy
        ).send(replace(identity, idempotency_key="bad-url"), "work")


def test_remote_task_and_context_ids_are_bounded_opaque_strings(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    task_id = "opaque==任务/with space"
    context_id = "ctx=κόσμε"
    transport = Mock(task(task_id=task_id, context=context_id))
    Gateway(transport, store, card, policy).send(identity, "work")
    bound = store.read()
    assert bound["remote_task_id"] == task_id
    assert bound["remote_context_id"] == context_id
    transport.response = task(task_id=task_id, context=context_id)
    assert Gateway(transport, store, card, policy).poll(identity) == ()
    assert transport.gets == [{"id": task_id, "historyLength": 0}]

    with pytest.raises(A2AError, match="task id"):
        Gateway(
            Mock(task(task_id="bad\nremote", context=context_id)),
            BindingStore(tmp_path / "control-id.json"), card, policy,
        ).send(replace(identity, idempotency_key="control-id"), "work")


def test_oauth_card_metadata_is_not_mistaken_for_raw_secret(tmp_path):
    raw, _, _, _, _ = setup(tmp_path)
    raw["securitySchemes"] = {
        "oauth": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://auth.example/authorize",
                    "tokenUrl": "https://auth.example/token",
                },
                "clientCredentials": {"tokenUrl": "https://auth.example/token"},
                "password": {"tokenUrl": "https://auth.example/token"},
            },
        }
    }
    assert parse_card(raw).name == "remote"

    compromised = {**raw, "description": "api_key=sk-abcdefghijklmnopqrstuvwxyz123456"}
    with pytest.raises(A2AError, match="secret-like"):
        parse_card(compromised)


def test_unknown_bounded_service_response_fields_are_ignored(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    response = {
        "task": {
            "id": "remote-task",
            "contextId": "remote-context",
            "status": {"state": "TASK_STATE_COMPLETED", "futureStatus": {"v": 1}},
            "artifacts": [{
                "artifactId": "artifact",
                "parts": [{"text": "ok", "futurePart": True}],
                "futureArtifact": "ignored",
            }],
            "futureTask": [1, 2, 3],
        },
        "futureEnvelope": {"extension": True},
    }
    candidate, = Gateway(Mock(response), store, card, policy).send(identity, "work")
    assert candidate.content["futureArtifact"] == "ignored"
    assert candidate.content["parts"][0]["futurePart"] is True


def test_binding_parent_directories_are_fsynced_before_economic_send(tmp_path, monkeypatch):
    _, card, policy, identity, _ = setup(tmp_path)
    store = BindingStore(
        tmp_path / "new-a" / "new-b" / "binding.json", authority_root=tmp_path
    )
    real_fsync = a2a_module.os.fsync
    directory_syncs = []
    dispatched = []

    def traced_fsync(fd):
        info = a2a_module.os.fstat(fd)
        if a2a_module.stat.S_ISDIR(info.st_mode):
            directory_syncs.append((info.st_dev, info.st_ino))
        return real_fsync(fd)

    monkeypatch.setattr(a2a_module.os, "fsync", traced_fsync)

    class DurableMock(Mock):
        def send(self, interface, message, headers):
            # Both newly created directory entries must already have durable
            # parent-directory fsync evidence before economic transport.
            assert (tmp_path / "new-a" / "new-b").is_dir()
            assert len(directory_syncs) >= 4
            dispatched.append(True)
            return super().send(interface, message, headers)

    Gateway(DurableMock(), store, card, policy).send(identity, "work")
    assert dispatched == [True]
    assert store.read()["delivery"] == "bound"


@pytest.mark.parametrize("child_task", [None, {}, [], "", "   "])
def test_child_proposal_rejects_malformed_objective(tmp_path, child_task):
    _, card, policy, identity, store = setup(tmp_path)
    artifact = {"artifactId": "proposal", "parts": [{"text": json.dumps({
        "child_role": "reader",
        "child_tools": ["read_file"],
        "child_permissions": ["read"],
        "child_task": child_task,
    })}]}
    candidate = Gateway(
        Mock(task("TASK_STATE_COMPLETED", artifacts=[artifact])),
        store, card, policy,
    ).send(identity, "work")[0]
    with pytest.raises(A2AError, match="child task"):
        decode_child_proposal(
            candidate,
            parent_role="reader",
            parent_tools=("read_file",),
            parent_permissions=("read",),
        )


def test_direct_candidate_is_atomic_with_direct_delivery_state(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    response = {"message": {
        "messageId": "direct-reply",
        "contextId": "opaque-context",
        "role": "ROLE_AGENT",
        "parts": [{"text": "answer"}],
    }}
    Gateway(Mock(response), store, card, policy).send(identity, "question")
    raw = store.read()
    assert raw["delivery"] == "direct"
    assert len(raw["candidates"]) == 1
    assert Gateway(Mock(), store, card, policy).recover(identity)[0].content["messageId"] == "direct-reply"


def test_same_identity_cannot_redispatch_through_different_binding_file(tmp_path):
    _, card, policy, identity, first_store = setup(tmp_path)
    transport = Mock()

    def ambiguous(*args):
        transport.sends.append(args)
        raise RuntimeError("lost response")

    transport.send = ambiguous
    with pytest.raises(RuntimeError, match="lost response"):
        Gateway(transport, first_store, card, policy).send(identity, "work")
    assert first_store.read()["delivery"] == "send_started"

    second_store = BindingStore(tmp_path / "different-binding.json")
    with pytest.raises(A2AError, match="delivery already started"):
        Gateway(transport, second_store, card, policy).send(identity, "work")
    assert len(transport.sends) == 1


def test_binding_store_rejects_ancestor_symlink(tmp_path):
    _, card, policy, identity, _ = setup(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    link = tmp_path / "redirect"
    link.symlink_to(outside, target_is_directory=True)
    store = BindingStore(
        link / "binding.json", authority_root=tmp_path
    )
    with pytest.raises(A2AError, match="binding directory"):
        Gateway(Mock(), store, card, policy).send(identity, "work")
    assert not (outside / "binding.json").exists()


def test_task_status_message_is_preserved_as_candidate(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    status_message = {
        "messageId": "status-message",
        "taskId": "remote-task",
        "contextId": "remote-context",
        "role": "ROLE_AGENT",
        "parts": [{"text": "working answer"}],
    }
    response = {
        "task": {
            "id": "remote-task",
            "contextId": "remote-context",
            "status": {
                "state": "TASK_STATE_WORKING",
                "message": status_message,
            },
            "artifacts": [],
        }
    }
    candidate, = Gateway(Mock(response), store, card, policy).send(identity, "work")
    assert candidate.kind == "message"
    assert candidate.remote_task_id == "remote-task"
    assert candidate.remote_context_id == "remote-context"
    assert candidate.content == status_message
    assert Gateway(Mock(), store, card, policy).recover(identity)[0].digest == candidate.digest


def test_remote_ids_reject_unicode_control_characters(tmp_path):
    _, card, policy, identity, _ = setup(tmp_path)
    for index, remote_task in enumerate(("bad\u0085id", "bad\u202eid")):
        attempt = replace(identity, idempotency_key=f"unicode-control-{index}")
        with pytest.raises(A2AError, match="task id"):
            Gateway(
                Mock(task(task_id=remote_task)),
                BindingStore(tmp_path / f"unicode-control-{index}.json"),
                card,
                policy,
            ).send(attempt, "work")


def test_gateway_rejects_binding_authority_root_not_in_admission(tmp_path):
    _, card, policy, identity, _ = setup(tmp_path)
    other = tmp_path / "other-root"
    store = BindingStore(other / "binding.json")
    with pytest.raises(A2AError, match="binding authority root not locally admitted"):
        Gateway(Mock(), store, card, policy)


def test_same_identity_cannot_redispatch_after_admitted_binding_root_change(tmp_path):
    raw, card, base_policy, identity, _ = setup(tmp_path)
    root_a = tmp_path / "bindings-a"
    root_b = tmp_path / "bindings-b"
    policy_a = replace(base_policy, binding_root=str(root_a))
    policy_b = replace(base_policy, binding_root=str(root_b))
    first = BindingStore(root_a / "attempt.json", authority_root=root_a)
    second = BindingStore(root_b / "attempt.json", authority_root=root_b)
    transport = Mock()

    def ambiguous(*args):
        transport.sends.append(args)
        raise RuntimeError("lost response")

    transport.send = ambiguous
    with pytest.raises(RuntimeError, match="lost response"):
        Gateway(transport, first, card, policy_a).send(identity, "work")

    with pytest.raises(A2AError, match="delivery already started"):
        Gateway(transport, second, card, policy_b).send(identity, "work")
    assert len(transport.sends) == 1


def test_two_large_valid_responses_preserve_late_cancel_candidate(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    early = {
        "artifactId": "early-large",
        "parts": [{"text": "A" * 100_000}],
    }
    late = {
        "artifactId": "late-large",
        "parts": [{"text": "B" * 100_000}],
    }
    transport = Mock(task("TASK_STATE_WORKING", artifacts=[early]))
    gateway = Gateway(transport, store, card, policy)
    first, = gateway.send(identity, "work")

    def completed_cancel(interface, request, headers):
        transport.cancels.append(request)
        return task("TASK_STATE_COMPLETED", artifacts=[late])

    transport.cancel = completed_cancel
    second, = gateway.cancel(identity)
    recovered = Gateway(transport, store, card, policy).recover(identity)
    assert {item.digest for item in recovered} == {first.digest, second.digest}
    assert second.content["artifactId"] == "late-large"


def test_response_capacity_exhaustion_fails_before_remote_poll(tmp_path, monkeypatch):
    _, card, policy, identity, store = setup(tmp_path)
    artifact = {"artifactId": "one", "parts": [{"text": "candidate"}]}
    transport = Mock(task("TASK_STATE_WORKING", artifacts=[artifact]))
    gateway = Gateway(transport, store, card, policy)
    gateway.send(identity, "work")
    monkeypatch.setattr(a2a_module, "MAX_CANDIDATES", 1)

    with pytest.raises(A2AError, match="candidate recovery capacity exhausted"):
        gateway.poll(identity)
    assert transport.gets == []


def test_benign_security_words_remain_durable_candidates(tmp_path):
    _, card, policy, identity, direct_store = setup(tmp_path)
    direct_message = {
        "messageId": "direct-benign-security",
        "contextId": "context",
        "role": "ROLE_AGENT",
        "parts": [{"text": "Use the Authorization header described in the runbook."}],
    }
    direct_gateway = Gateway(
        Mock({"message": direct_message}), direct_store, card, policy
    )
    direct_candidate, = direct_gateway.send(identity, "help")
    assert direct_gateway.recover(identity)[0].digest == direct_candidate.digest

    late_identity = replace(identity, idempotency_key="benign-late-cancel")
    late_store = BindingStore(tmp_path / "benign-late.json")
    late_transport = Mock()
    late_gateway = Gateway(late_transport, late_store, card, policy)
    late_gateway.send(late_identity, "work")
    late_artifact = {
        "artifactId": "late-benign-security",
        "parts": [{"text": "Credential rotation procedure completed without exposing secrets."}],
    }

    def completed_cancel(interface, request, headers):
        late_transport.cancels.append(request)
        return task("TASK_STATE_COMPLETED", artifacts=[late_artifact])

    late_transport.cancel = completed_cancel
    late_candidate, = late_gateway.cancel(late_identity)
    recovered = late_gateway.recover(late_identity)
    assert recovered[-1].digest == late_candidate.digest
    assert recovered[-1].content == late_artifact

def test_required_extensions_are_rejected_before_admission(tmp_path):
    raw, _, _, _, _ = setup(tmp_path)
    optional = {
        **raw,
        "capabilities": {
            "extensions": [{
                "uri": "https://extensions.example/optional",
                "required": False,
            }],
        },
    }
    assert parse_card(optional).name == "remote"
    required = {
        **raw,
        "capabilities": {
            "extensions": [{
                "uri": "https://extensions.example/required",
                "required": True,
            }],
        },
    }
    with pytest.raises(A2AError, match="unsupported required extension"):
        parse_card(required)


def test_get_and_cancel_accept_bare_task_responses(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    gateway = Gateway(transport, store, card, policy)
    gateway.send(identity, "work")

    transport.response = task("TASK_STATE_WORKING")["task"]
    assert gateway.poll(identity) == ()

    late = {"artifactId": "bare-cancel", "parts": [{"text": "late result"}]}
    def bare_cancel(interface, request, headers):
        transport.cancels.append(request)
        return task("TASK_STATE_COMPLETED", artifacts=[late])["task"]
    transport.cancel = bare_cancel

    candidate, = gateway.cancel(identity)
    assert candidate.content == late
    assert gateway.recover(identity)[-1].digest == candidate.digest


def test_existing_binding_ancestor_chain_is_fsynced_before_send(tmp_path, monkeypatch):
    _, card, policy, identity, _ = setup(tmp_path)
    root = tmp_path / "preexisting" / "a" / "b"
    root.mkdir(parents=True)
    store = BindingStore(root / "binding.json", authority_root=tmp_path)

    expected = {
        (path.stat().st_dev, path.stat().st_ino)
        for path in (
            tmp_path,
            tmp_path / "preexisting",
            tmp_path / "preexisting" / "a",
            root,
        )
    }
    seen = set()
    real_fsync = a2a_module.os.fsync

    def traced(fd):
        info = a2a_module.os.fstat(fd)
        if a2a_module.stat.S_ISDIR(info.st_mode):
            seen.add((info.st_dev, info.st_ino))
        return real_fsync(fd)

    monkeypatch.setattr(a2a_module.os, "fsync", traced)

    class CheckBeforeSend(Mock):
        def send(self, interface, message, headers):
            assert expected <= seen
            return super().send(interface, message, headers)

    Gateway(CheckBeforeSend(), store, card, policy).send(identity, "work")


@pytest.mark.parametrize("port",["99999","abc","0","-1"])
def test_card_invalid_https_port_rejected_before_admission(tmp_path,port):
    raw,*_=setup(tmp_path)
    raw["supportedInterfaces"][0]["url"]="https://remote.example:"+port+"/a2a"
    with pytest.raises(A2AError,match="URL"):
        parse_card(raw)

def test_card_security_descriptions_and_unicode_skill_id_are_metadata(tmp_path):
    raw,*_=setup(tmp_path)
    raw["description"]="Credential rotation and password reset assistance"
    raw["skills"][0]["id"]="skill=翻訳"
    raw["skills"][0]["name"]="Password reset assistance"
    raw["skills"][0]["description"]="Credential rotation"
    card=parse_card(raw)
    assert card.name=="remote" and card.supports_text_input
    raw["skills"][0]["description"]="api_key=sk-"+("a"*32)
    with pytest.raises(A2AError,match="secret"):
        parse_card(raw)

def test_duplicate_remote_skill_ids_denied(tmp_path):
    raw,*_=setup(tmp_path)
    raw["skills"].append(dict(raw["skills"][0]))
    with pytest.raises(A2AError,match="duplicate"):
        parse_card(raw)

def test_non_text_card_denied_before_economic_claim(tmp_path):
    raw,_,admission,identity,store=setup(tmp_path)
    raw["defaultInputModes"]=["image/png"]
    raw["skills"][0]["inputModes"]=["application/json"]
    card=parse_card(raw)
    admission=replace(admission,card_fingerprint=card.fingerprint)
    transport=Mock();gateway=Gateway(transport,store,card,admission)
    with pytest.raises(A2AError,match="text input"):
        gateway.send(identity,"work")
    assert transport.sends==[] and store.read() is None
    assert not a2a_module.ECONOMIC_CLAIM_ROOT.exists()

def test_declared_skill_text_mode_can_override_image_default(tmp_path):
    raw,_,admission,identity,store=setup(tmp_path)
    raw["defaultInputModes"]=["image/png"]
    raw["skills"][0]["inputModes"]=["text/plain"]
    card=parse_card(raw);admission=replace(admission,card_fingerprint=card.fingerprint)
    transport=Mock()
    Gateway(transport,store,card,admission).send(identity,"work")
    assert len(transport.sends)==1

@pytest.mark.parametrize("bare",[False,True])
def test_cancel_large_ignored_history_preserves_late_artifacts(tmp_path,bare):
    _,card,admission,identity,store=setup(tmp_path)
    transport=Mock();gateway=Gateway(transport,store,card,admission)
    gateway.send(identity,"work")
    artifact={"artifactId":"late-result","parts":[{"text":"completed before cancellation"}]}
    response=task("TASK_STATE_CANCELED",artifacts=[artifact])
    response["task"]["history"]=[{"parts":[{"text":"x"*200000}]}]
    transport.cancel=lambda *args:response["task"] if bare else response
    candidates=gateway.cancel(identity)
    assert len(candidates)==1 and candidates[0].content==artifact
    recovered=Gateway(Mock(),BindingStore(store.path),card,admission).recover(identity)
    assert len(recovered)==1 and recovered[0].content==artifact
    assert store.read()["last_observation"]=="TASK_STATE_CANCELED"


@pytest.mark.parametrize("number,name",list(enumerate(
    "TASK_STATE_UNSPECIFIED TASK_STATE_SUBMITTED TASK_STATE_WORKING TASK_STATE_COMPLETED TASK_STATE_FAILED TASK_STATE_CANCELED TASK_STATE_INPUT_REQUIRED TASK_STATE_REJECTED TASK_STATE_AUTH_REQUIRED".split())))
def test_numeric_protojson_task_state_is_normalized(tmp_path,number,name):
    _,card,policy,identity,store=setup(tmp_path)
    Gateway(Mock(task(number)),store,card,policy).send(identity,"work")
    assert store.read()["last_observation"]==name

@pytest.mark.parametrize("value",[True,False,9,-1,1.0,"UNKNOWN"])
def test_invalid_protojson_state_is_rejected(tmp_path,value):
    _,card,policy,identity,store=setup(tmp_path)
    with pytest.raises(A2AError,match="state"):
        Gateway(Mock(task(value)),store,card,policy).send(identity,"work")

@pytest.mark.parametrize("url",["https://remote example/a2a","https://remote\nexample/a2a",
    "https://bad-.example/a2a","https://.example/a2a","https://remote.example:bad/a2a"])
def test_malformed_https_authority_denied_before_admission(tmp_path,url):
    raw,*_=setup(tmp_path)
    raw["supportedInterfaces"][0]["url"]=url
    with pytest.raises(A2AError,match="HTTPS"):parse_card(raw)

@pytest.mark.parametrize("url",["https://[::1]:443/a2a","https://xn--p1ai.example/a2a",
                               "https://翻訳.example/a2a"])
def test_valid_https_authorities_remain_discoverable(tmp_path,url):
    raw,*_=setup(tmp_path);raw["supportedInterfaces"][0]["url"]=url
    assert parse_card(raw).interfaces[0].url==url

def test_every_skill_override_removes_default_text_before_economic_claim(tmp_path):
    raw,_,_,identity,store=setup(tmp_path)
    raw["skills"][0]["inputModes"]=["image/png"]
    card=parse_card(raw)
    policy=Admission(card.fingerprint,card.interfaces[0].fingerprint,"remote-exec",
        "remote-provider","remote-cap","remote-runtime",("read_file",),str(tmp_path))
    transport=Mock()
    with pytest.raises(A2AError,match="text input"):
        Gateway(transport,store,card,policy).send(identity,"work")
    assert transport.sends==[] and store.read() is None

def test_inherited_skill_default_retains_text(tmp_path):
    raw,*_=setup(tmp_path)
    raw["skills"].append({**raw["skills"][0],"id":"image","inputModes":["image/png"]})
    assert parse_card(raw).supports_text_input

def test_context_from_status_message_is_durable_and_cannot_change(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    payload=task(context=None)
    payload["task"]["status"]["message"]={"messageId":"status-1","role":2,
        "parts":[{"text":"working"}],"contextId":"context-from-message"}
    transport=Mock(payload);gateway=Gateway(transport,store,card,policy)
    candidate=gateway.send(identity,"work")[0]
    assert candidate.remote_context_id=="context-from-message"
    assert store.read()["remote_context_id"]=="context-from-message"
    changed=json.loads(json.dumps(payload))
    changed["task"]["status"]["message"].update(messageId="status-2",contextId="other-context")
    transport.response=changed
    with pytest.raises(A2AError,match="binding mismatch"):gateway.poll(identity)
    assert len(gateway.recover(identity))==1

def test_duplicate_task_artifact_ids_are_rejected(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    response=task(artifacts=[{"artifactId":"same","parts":[{"text":"one"}]},
                             {"artifactId":"same","parts":[{"text":"two"}]}])
    with pytest.raises(A2AError,match="duplicate artifact"):
        Gateway(Mock(response),store,card,policy).send(identity,"work")


@pytest.mark.parametrize("key",["inputModes","outputModes"])
@pytest.mark.parametrize("empty",[[],None])
def test_optional_empty_or_null_skill_modes_inherit_required_defaults(tmp_path,key,empty):
    raw,*_=setup(tmp_path);raw["skills"][0][key]=empty
    assert parse_card(raw).supports_text_input

@pytest.mark.parametrize("bad",["xn--abc","xn--ls8h","xn--"])
def test_fake_idna_alabel_denied_before_card_admission(tmp_path,bad):
    raw,*_=setup(tmp_path);raw["supportedInterfaces"][0]["url"]=f"https://{bad}.example/a2a"
    with pytest.raises(A2AError,match="HTTPS"):parse_card(raw)

@pytest.mark.parametrize("bare",[False,True])
@pytest.mark.parametrize("null_fields",[False,True])
def test_bound_context_survives_later_unobserved_optional_fields(tmp_path,bare,null_fields):
    _,card,policy,identity,store=setup(tmp_path)
    payload=task(context=None)
    payload["task"]["status"]["message"]={"messageId":"status-1","role":2,
        "parts":[{"text":"working"}],"contextId":"known-context"}
    transport=Mock(payload);gateway=Gateway(transport,store,card,policy)
    gateway.send(identity,"work")
    later=task("TASK_STATE_COMPLETED",context=None,
        artifacts=[{"artifactId":"final","parts":[{"text":"late result"}]}])
    if null_fields:
        later["task"]["contextId"]=None;later["task"]["status"]["message"]=None
    transport.response=later["task"] if bare else later
    candidate,=gateway.poll(identity)
    assert candidate.remote_context_id=="known-context"
    assert store.read()["remote_context_id"]=="known-context"
    assert len(Gateway(Mock(),store,card,policy).recover(identity))==2

def test_context_first_observed_after_send_binds_once_without_new_economic_send(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    transport=Mock(task(context=None));gateway=Gateway(transport,store,card,policy)
    gateway.send(identity,"work");assert store.read()["remote_context_id"] is None
    transport.response=task("TASK_STATE_WORKING",context="learned-context",
        artifacts=[{"artifactId":"one","parts":[{"text":"first result"}]}])
    first,=gateway.poll(identity)
    assert first.remote_context_id=="learned-context" and store.read()["remote_context_id"]=="learned-context"
    transport.response=task("TASK_STATE_COMPLETED",context=None,
        artifacts=[{"artifactId":"two","parts":[{"text":"final result"}]}])
    second,=gateway.poll(identity)
    assert second.remote_context_id=="learned-context"
    transport.response=task(context="foreign-context")
    with pytest.raises(A2AError,match="binding mismatch"):gateway.poll(identity)
    assert len(transport.sends)==1 and len(gateway.recover(identity))==2


@pytest.mark.parametrize("host", ["xn--fa-hia.de", "faß.de", "xn--3xa.example", "ς.example"])
def test_idna2008_deviation_domains_remain_discoverable(tmp_path, host):
    raw, *_ = setup(tmp_path)
    raw["supportedInterfaces"][0]["url"] = f"https://{host}/a2a"
    assert parse_card(raw).interfaces[0].url == f"https://{host}/a2a"

@pytest.mark.parametrize("host", ["a_b.example", "ab--cd.example", "a\u200db.example",
                                  "\u0301a.example", "xn--ls8h.example"])
def test_strict_idna2008_invalid_domains_denied(tmp_path, host):
    raw, *_ = setup(tmp_path)
    raw["supportedInterfaces"][0]["url"] = f"https://{host}/a2a"
    with pytest.raises(A2AError, match="HTTPS"):
        parse_card(raw)

@pytest.mark.parametrize("empty", [None, ""])
def test_null_optional_message_task_id_is_direct_and_restart_never_resends(tmp_path, empty):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock({"message": {"messageId": "reply", "taskId": empty,
        "contextId": "context", "role": "ROLE_AGENT", "parts": [{"text": "answer"}]}})
    first, = Gateway(transport, store, card, policy).send(identity, "work")
    assert first.remote_task_id is None and store.read()["delivery"] == "direct"
    restarted = Gateway(transport, store, card, policy)
    assert restarted.poll(identity)[0].digest == first.digest
    assert restarted.recover(identity)[0].digest == first.digest
    assert len(transport.sends) == 1 and transport.gets == []


@pytest.mark.parametrize("operation", ["send", "poll", "cancel"])
@pytest.mark.parametrize("bare", [False, True])
@pytest.mark.parametrize("empty", [None, ""])
def test_null_optional_status_message_task_id_keeps_candidates_and_binding(tmp_path, operation, bare, empty):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock(); gateway = Gateway(transport, store, card, policy)
    response = task("TASK_STATE_WORKING")
    response["task"]["status"]["message"] = {"messageId":"current", "role":"ROLE_AGENT",
        "contextId":"remote-context", "taskId":empty, "parts":[{"text":"findings", "metadata":None}]}
    response["task"]["artifacts"] = None
    if operation == "send":
        transport.response = response
        candidate, = gateway.send(identity,"work")
    else:
        gateway.send(identity,"work")
        transport.response = response["task"] if bare else response
        if operation == "poll":
            candidate, = gateway.poll(identity)
        else:
            response["task"]["status"]["state"] = "TASK_STATE_CANCELED"
            response["task"]["history"] = None
            transport.cancel = lambda interface, request, headers: response["task"] if bare else response
            candidate, = gateway.cancel(identity)
    assert candidate.remote_task_id == "remote-task"
    assert len(gateway.recover(identity)) == 1 and len(transport.sends) == 1

@pytest.mark.parametrize("fence", [0, -1, True, 1.0, 2**63])
def test_invalid_fence_rejected_before_gateway_or_economic_claim(fence):
    with pytest.raises(A2AError, match="fence"):
        Identity("github:repo","parent","child","task","run",fence,"key")


@pytest.mark.parametrize("operation", ["send","poll","cancel"])
@pytest.mark.parametrize("scalar", ["filename","mediaType","media_type"])
def test_optional_null_part_strings_are_unset_without_losing_response(tmp_path,operation,scalar):
    _,card,policy,identity,store=setup(tmp_path)
    response=task()
    response["task"]["artifacts"]=[{"artifact_id":"answer","parts":[
        {"text":"findings",scalar:None,"metadata":None}]}]
    transport=Mock(response);gateway=Gateway(transport,store,card,policy)
    if operation=="send": candidate,=gateway.send(identity,"work")
    else:
        transport.response=task();gateway.send(identity,"work");transport.response=response
        if operation=="poll":candidate,=gateway.poll(identity)
        else:
            response["task"]["status"]["state"]="TASK_STATE_CANCELED"
            transport.cancel=lambda *args:response["task"]
            candidate,=gateway.cancel(identity)
    assert candidate.content["parts"]==[{"text":"findings"}]
    assert len(gateway.recover(identity))==1 and len(transport.sends)==1

@pytest.mark.parametrize("operation", ["send","poll","cancel"])
@pytest.mark.parametrize("bare", [False,True])
def test_original_proto_names_normalize_only_protocol_objects(tmp_path,operation,bare):
    _,card,policy,identity,store=setup(tmp_path)
    opaque={"message_id":"payload","context_id":"data-not-authority","media_type":None}
    value={"id":"remote-task","context_id":"remote-context","status":{
        "state":"TASK_STATE_WORKING","message":{"message_id":"status","role":2,
            "context_id":"remote-context","task_id":None,"parts":[{"data":opaque,"media_type":"application/json"}]}},
        "artifacts":[{"artifact_id":"report","parts":[{"text":"report","media_type":"text/plain"}]}]}
    transport=Mock();gateway=Gateway(transport,store,card,policy)
    if operation=="send":
        transport.response={"task":value};results=gateway.send(identity,"work")
    else:
        gateway.send(identity,"work");transport.response=value if bare else {"task":value}
        if operation=="poll":results=gateway.poll(identity)
        else:
            value["status"]["state"]="TASK_STATE_CANCELED"
            transport.cancel=lambda *args:value if bare else {"task":value}
            results=gateway.cancel(identity)
    assert len(results)==2 and results[0].content["messageId"]=="status"
    assert results[0].content["parts"][0]["data"]==opaque
    assert results[1].content["artifactId"]=="report"
    assert results[1].content["parts"][0]["mediaType"]=="text/plain"
    assert store.read()["remote_context_id"]=="remote-context"
    assert len(transport.sends)==1

def test_direct_original_proto_names_and_null_scalar_oneof_do_not_rewrite_data_null(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    response={"message":{"message_id":"direct","context_id":"ctx","task_id":None,"role":2,
        "parts":[{"text":None,"raw":None,"url":None,"data":None,"media_type":None}]}}
    candidate,=Gateway(Mock(response),store,card,policy).send(identity,"work")
    assert candidate.content["parts"]==[{"data":None}]
    assert candidate.remote_task_id is None

def test_duplicate_proto_aliases_are_ambiguous_and_never_resend(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    transport=Mock({"message":{"messageId":"a","message_id":"a","contextId":"ctx","role":2,"parts":[{"text":"reply"}]}})
    gateway=Gateway(transport,store,card,policy)
    with pytest.raises(A2AError,match="duplicate proto"):gateway.send(identity,"work")
    assert len(transport.sends)==1
    with pytest.raises(A2AError):gateway.send(identity,"work")
    assert len(transport.sends)==1


@pytest.mark.parametrize("alias", ["supportedInterfaces", "supported_interfaces"])
def test_card_null_optional_fields_and_tenant_are_unset(tmp_path, alias):
    raw, original, _, _, _ = setup(tmp_path)
    raw[alias] = raw.pop("supportedInterfaces")
    raw[alias][0]["tenant"] = None
    raw["provider"] = None
    raw["documentationUrl"] = None
    raw["skills"][0]["inputModes"] = None
    raw["skills"][0]["outputModes"] = None
    raw["capabilities"]["extensions"] = None
    card = parse_card(raw)
    assert card.interfaces[0].tenant is None
    assert card.interfaces[0].fingerprint == original.interfaces[0].fingerprint
    assert card.supports_text_input
    raw["capabilities"]["extensions"] = [{"uri": "https://example.test/optional", "required": None}]
    assert parse_card(raw).interfaces == original.interfaces
    raw[alias][0]["tenant"] = 0
    with pytest.raises(A2AError, match="tenant"):
        parse_card(raw)


@pytest.mark.parametrize("field", ["name", "version", "supportedInterfaces", "capabilities", "skills", "defaultInputModes"])
def test_card_required_null_fields_still_deny(tmp_path, field):
    raw, _, _, _, _ = setup(tmp_path)
    raw[field] = None
    with pytest.raises(A2AError):
        parse_card(raw)


@pytest.mark.parametrize("text", ["Implement password reset", "Document credential rotation", "Describe the Authorization header"])
def test_security_task_terms_without_values_are_delivered(tmp_path, text):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    Gateway(transport, store, card, policy).send(identity, text)
    assert len(transport.sends) == 1

@pytest.mark.parametrize("text", ["password=do-not-export", "api_key: do-not-export", "Authorization: Bearer abcdefghijklmnop", "ghp_" + "a"*30])
def test_outbound_actual_secret_values_denied_before_claim(tmp_path, text):
    _, card, policy, identity, store = setup(tmp_path)
    transport = Mock()
    with pytest.raises(A2AError, match="secret-like"):
        Gateway(transport, store, card, policy).send(identity, text)
    assert transport.sends == [] and not store.path.exists()
    assert not a2a_module.ECONOMIC_CLAIM_ROOT.exists()

@pytest.mark.parametrize("existing", [False, True])
def test_binding_file_cannot_equal_authority_root(tmp_path, existing):
    root = tmp_path / "authority"
    if existing: root.mkdir()
    with pytest.raises(A2AError, match="outside authority"):
        BindingStore(root, authority_root=root)
    assert not (tmp_path / "authority.lock").exists()

def test_economic_claims_are_scoped_to_consumer_and_restart_stays_one_use(tmp_path):
    _, card, policy, identity, store = setup(tmp_path)
    other = replace(identity, consumer="github:other")
    assert other.message_id != identity.message_id
    first, second = Mock(), Mock()
    Gateway(first, store, card, policy).send(identity, "work")
    other_store = BindingStore(tmp_path / "other.json")
    Gateway(second, other_store, card, policy).send(other, "work")
    assert len(first.sends) == len(second.sends) == 1
    with pytest.raises(A2AError, match="already started"):
        Gateway(first, BindingStore(tmp_path / "again.json"), card, policy).send(identity, "work")
    assert len(first.sends) == 1
    assert Gateway(second, other_store, card, policy).recover(other) == ()

@pytest.mark.parametrize("label",["credential","credentials","secret","private_key","client_secret","refresh_token","Cookie","Set-Cookie"])
def test_all_concrete_secret_classes_denied_before_outbound_claim(tmp_path,label):
    _,card,policy,identity,store=setup(tmp_path);transport=Mock()
    with pytest.raises(A2AError,match="secret-like"):Gateway(transport,store,card,policy).send(identity,label+": do-not-export")
    assert transport.sends==[] and not store.path.exists()

@pytest.mark.parametrize("depth",[33,1100])
@pytest.mark.parametrize("operation",["send","poll","cancel"])
def test_deep_untrusted_json_has_typed_denial_and_no_resend(tmp_path,depth,operation):
    _,card,policy,identity,store=setup(tmp_path);transport=Mock();gateway=Gateway(transport,store,card,policy)
    if operation!="send":gateway.send(identity,"work")
    nested="leaf"
    for _ in range(depth):nested=[nested]
    response=task(artifacts=[{"artifactId":"nested","parts":[{"data":nested}]}])
    transport.response=response;transport.cancel=lambda *args:response
    with pytest.raises(A2AError):getattr(gateway,operation)(identity,"work") if operation=="send" else getattr(gateway,operation)(identity)
    assert len(transport.sends)==1
    with pytest.raises(A2AError,match="already started"):gateway.send(identity,"work")

@pytest.mark.parametrize("operation",["send","poll","cancel"])
def test_null_unselected_envelope_alternative_is_unset(tmp_path,operation):
    _,card,policy,identity,store=setup(tmp_path);transport=Mock();gateway=Gateway(transport,store,card,policy)
    if operation!="send":gateway.send(identity,"work")
    response={**task("TASK_STATE_CANCELED" if operation=="cancel" else "TASK_STATE_WORKING"),"message":None}
    transport.response=response;transport.cancel=lambda *args:response
    getattr(gateway,operation)(identity,"work") if operation=="send" else getattr(gateway,operation)(identity)
    assert store.read()["remote_task_id"]=="remote-task" and len(transport.sends)==1

def test_direct_message_ignores_null_task_envelope_alternative(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    transport=Mock({"task":None,"message":{"messageId":"reply","contextId":"context","role":"ROLE_AGENT","parts":[{"text":"answer"}]}})
    candidate,=Gateway(transport,store,card,policy).send(identity,"work")
    assert candidate.remote_task_id is None and store.read()["delivery"]=="direct"

@pytest.mark.parametrize("text",["Implement password reset","Document credential rotation","Describe cookie handling"])
def test_benign_security_child_proposal_reaches_normal_scheduler_admission(tmp_path,text):
    _,card,policy,identity,store=setup(tmp_path)
    raw={"child_role":"reader","child_tools":["read_file"],"child_permissions":[],"child_task":text}
    artifacts=[{"artifactId":"proposal","parts":[{"text":json.dumps(raw)}]}]
    candidate,=Gateway(Mock(task("TASK_STATE_COMPLETED",artifacts=artifacts)),store,card,policy).send(identity,"work")
    proposal=decode_child_proposal(candidate,parent_role="reader",parent_tools=("read_file",),parent_permissions=())
    scheduler=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"events.jsonl"))
    assert scheduler.evaluate_child_proposal(proposal) and scheduler.snapshot()["tasks"]==[]


@pytest.mark.parametrize("name", ["password", "credential", "private_key", "api_key",
    "client_secret", "refresh_token", "access_token", "authorization", "cookie", "set-cookie"])
@pytest.mark.parametrize("quote", ['"', "'"])
def test_quoted_concrete_secret_assignments_deny_before_economic_dispatch(tmp_path,name,quote):
    _,card,policy,identity,store=setup(tmp_path)
    transport=Mock()
    secret="{"+quote+name+quote+":"+quote+"do-not-export"+quote+"}"
    with pytest.raises(A2AError):
        Gateway(transport,store,card,policy).send(identity,secret)
    assert transport.sends==[] and store.read() is None

@pytest.mark.parametrize("text,code", [
    ("["*800+"0"+"]"*800,"depth"),
    ("["*10000+"0"+"]"*10000,"text bound"),
    ("{bad JSON","invalid proposal JSON"),
    ('{"child_role":"reader","child_role":"writer"}',"duplicate"),
    ("[NaN]","invalid proposal JSON")])
def test_untrusted_child_proposal_parser_failure_is_bounded_and_typed(tmp_path,text,code):
    _,card,policy,identity,store=setup(tmp_path)
    artifacts=[{"artifactId":"proposal","parts":[{"text":text}]}]
    candidate,=Gateway(Mock(task("TASK_STATE_COMPLETED",artifacts=artifacts)),store,card,policy).send(identity,"work")
    with pytest.raises(A2AError,match=code):
        decode_child_proposal(candidate,parent_role="reader",parent_tools=("read_file",),parent_permissions=())

def test_child_proposal_parser_does_not_count_quoted_brackets_as_nesting(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    raw={"child_role":"reader","child_tools":["read_file"],"child_permissions":[],
         "child_task":'Inspect "'+"["*100+'"'+"}"*100}
    candidate,=Gateway(Mock(task("TASK_STATE_COMPLETED",artifacts=[
        {"artifactId":"proposal","parts":[{"text":json.dumps(raw)}]}])),store,card,policy).send(identity,"work")
    proposal=decode_child_proposal(candidate,parent_role="reader",parent_tools=("read_file",),parent_permissions=())
    assert proposal.child_task==raw["child_task"]

def test_send_explicitly_requests_no_task_history(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    class HistoryServer(Mock):
        def send(self,interface,request,headers):
            assert request["configuration"]["historyLength"]==0
            return super().send(interface,request,headers)
    transport=HistoryServer()
    Gateway(transport,store,card,policy).send(identity,"work")
    assert store.read()["delivery"]=="bound" and len(transport.sends)==1


@pytest.mark.parametrize("name",["password","credential","private_key","api_key","client_secret",
    "refresh_token","access_token","authorization","cookie","set-cookie"])
@pytest.mark.parametrize("position",[0,3])
def test_json_unicode_escaped_protected_key_denies_before_economic_dispatch(tmp_path,name,position):
    _,card,policy,identity,store=setup(tmp_path)
    transport=Mock()
    key=name[:position]+chr(92)+"u"+format(ord(name[position]),"04x")+name[position+1:]
    text='{"'+key+'":"do-not-export"}'
    with pytest.raises(A2AError,match="secret"):
        Gateway(transport,store,card,policy).send(identity,text)
    assert transport.sends==[] and store.read() is None

@pytest.mark.parametrize("suffix",["?","#","/?","/#","?query","#fragment"])
def test_discovery_query_or_fragment_delimiter_denies_before_transport(tmp_path,suffix):
    class DeniedTransport:
        def discover(self,*args):pytest.fail("invalid origin contacted a remote endpoint")
    with pytest.raises(A2AError,match="origin"):
        discover_card(DeniedTransport(),"https://remote.example"+suffix)

@pytest.mark.parametrize("value",[chr(0xd800), "before"+chr(0xdfff)+"after"])
def test_remote_identifiers_reject_surrogates_through_typed_error(value):
    with pytest.raises(A2AError,match="invalid remote id"):
        a2a_module._remote_id(value,"remote id")

def test_surrogate_task_text_denies_before_dispatch(tmp_path):
    _,card,policy,identity,store=setup(tmp_path)
    transport=Mock()
    with pytest.raises(A2AError,match="message text"):
        Gateway(transport,store,card,policy).send(identity,chr(0xd800))
    assert transport.sends==[] and store.read() is None
