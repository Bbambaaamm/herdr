"""Typed handoff binding/replay, explicit partial/conflict and no authority expansion."""
import hashlib
import json
from dataclasses import replace
import pytest
from herdr.child_ownership import OwnershipError
from herdr.handoff import HandoffEnvelope, child_spec_digest
from herdr.scheduler import AuditLog, DynamicChildScheduler
from tests.herdr.test_child_ownership import parent, registry, scheduler, ownership, proposal


def claimed(tmp_path):
    owner = parent()
    store = registry(tmp_path)
    item = scheduler(tmp_path, owner, store)
    node = item.delegate_child(owner.task_id, owner.run_token, "handoff",
        proposal(owner, ownership(owner, files=("owned.py",))))
    item.dispatch(task_ids={node.id}, managed_start=True)
    return owner, store, item, item._tasks[node.id]


def publish(item, rec, evidence, *, status="completed"):
    sha = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return item.publish_child_result(rec.id, rec.run_token, rec.agent_id, rec.fencing_token,
                                    rec.idempotency_key, sha, evidence, status=status)


def test_actual_child_publication_retains_same_typed_handoff_through_cold_replay(tmp_path):
    owner, store, item, rec = claimed(tmp_path)
    evidence = [{"report": "candidate", "handoff_details": {
        "assumptions": ["schema contract stays frozen"], "out_of_scope": ["rollout"]}}]
    original_scope = rec.ownership
    assert publish(item, rec, evidence)
    envelope = HandoffEnvelope.from_json(rec.result_handoff)
    envelope.require_current(rec, registry=store)
    assert envelope.current_state == "UNKNOWN" and envelope.base_sha256 is None
    assert "semantic_acceptance" in envelope.unknowns and envelope.accepted_decisions == ()
    assert envelope.out_of_scope == ("rollout",)
    assert envelope.ownership == original_scope and rec.ownership == original_scope
    replay = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "graph.jsonl"),
        ownership_registry=store, ownership_parent=owner)
    replay.replay()
    assert replay._tasks[rec.id].result_handoff == rec.result_handoff
    assert replay.dispatch(task_ids={rec.id}, managed_start=True) == []


@pytest.mark.parametrize("details,state", [
    ({"remaining_criteria": ["integration still pending"]}, "PARTIAL"),
    ({"contradictions": ["API version conflicts with parent"]}, "CONFLICT"),
])
def test_partial_or_conflicting_child_handoff_cannot_complete(tmp_path, details, state):
    _, store, item, rec = claimed(tmp_path)
    evidence = [{"handoff_details": details}]
    before = item.audit_log._path.read_bytes()
    assert not publish(item, rec, evidence)
    assert rec.attempt_state != "terminal" and rec.result_handoff is None
    assert item.audit_log._path.read_bytes() == before
    assert publish(item, rec, evidence, status="blocked")
    envelope = HandoffEnvelope.from_json(rec.result_handoff)
    assert envelope.current_state == state
    envelope.require_current(rec, registry=store)


@pytest.mark.parametrize("changed", ["spec", "run", "scope", "base", "artifact"])
def test_stale_handoff_rejects_changed_task_attempt_scope_base_or_artifact(tmp_path, changed):
    _, store, item, rec = claimed(tmp_path)
    assert publish(item, rec, [{"report": "candidate"}])
    envelope = HandoffEnvelope.from_json(rec.result_handoff)
    if changed == "spec":
        candidate = replace(rec, node=replace(rec.node, objective="different task"))
    elif changed == "run":
        candidate = replace(rec, run_token="different-run")
    elif changed == "scope":
        candidate = replace(rec, ownership=replace(rec.ownership, handoff_ref="different-artifact"))
    elif changed == "artifact":
        candidate = replace(rec, result_artifact_sha256="b"*64)
    else:
        candidate = rec
    with pytest.raises(OwnershipError):
        envelope.require_current(candidate, base_sha256="b"*64 if changed == "base" else None, registry=store)


@pytest.mark.parametrize("details", [
    {"unknown_field": "ignored"},
    {"unknowns": ["x"]*33},
    {"next_action": ""},
    {"contradictions": ["control\ncharacter"]},
    {"unknowns": "unbounded prose"},
])
def test_host_projection_rejects_invalid_handoff_details_before_publication(tmp_path, details):
    _, _, item, rec = claimed(tmp_path)
    assert not publish(item, rec, [{"handoff_details": details}])
    assert rec.state.value == "running" and rec.result_handoff is None


def test_handoff_cannot_add_grants_or_self_approve_completion(tmp_path):
    _, _, item, rec = claimed(tmp_path)
    assert publish(item, rec, [{"report": "candidate"}])
    raw = rec.result_handoff
    with pytest.raises(OwnershipError, match="closed_schema"):
        HandoffEnvelope.from_json({**raw, "permissions": ["production-write"]})
    with pytest.raises(OwnershipError, match="incomplete_claim"):
        HandoffEnvelope.from_json({**raw, "current_state": "COMPLETE"})
