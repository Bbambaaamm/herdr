import copy

import pytest

from herdr.reconciliation import DecisionStatus, DurableEvidence, TaskIdentity, TaskSnapshot, reconcile_task
from herdr.result_contract import (
    RESULT_SCHEMA,
    ResultContractError,
    canonical_result_for_task,
    receipt_payload_for_result,
    validate_result_contract,
)


def task(**changes):
    value = {
        "repo": "Bbambaaamm/herdr", "issue": 79, "id": "task-79", "attempt_id": 3,
        "run_token": "run-3", "fencing_token": 8,
        "ownership_epoch": {"version": 1, "run_token": "run-3", "fencing_token": 8},
        "idempotency_key": "idem-79-3", "consumer": "github:Bbambaaamm/herdr",
        "parent_task_id": "parent-1", "parent_run_token": "parent-run-1",
        "attempt_state": "working",
    }
    value.update(changes)
    return value


def result(**changes):
    value = {
        "status": "completed", "evidence": [{"artifact": "sha256:" + "a" * 64}],
        "summary": "verified fixture", "completed_at": "2026-11-08T10:00:00Z",
    }
    value.update(changes)
    return value


def accepted_result(task_value=None, **changes):
    identity = task_value or task()
    value = result(authoritative=True, result_identity={
        "repository": identity["repo"], "issue": identity["issue"],
        "task_id": identity["id"], "attempt_id": identity["attempt_id"],
        "run_token": identity["run_token"], "fencing_token": identity["fencing_token"],
        "ownership_epoch": identity["ownership_epoch"],
        "idempotency_key": identity["idempotency_key"], "consumer": identity["consumer"],
        "parent_task_id": identity.get("parent_task_id"),
        "parent_run_token": identity.get("parent_run_token"),
    })
    value.update(changes)
    return value


def snapshot(**changes):
    identity = TaskIdentity(
        repository="Bbambaaamm/herdr", issue="79", task_id="task-79", attempt_id=3,
        run_token="run-3", fencing_token=8,
        ownership_epoch={"version": 1, "run_token": "run-3", "fencing_token": 8},
        idempotency_key="idem-79-3", consumer="github:Bbambaaamm/herdr",
        parent_task_id="parent-1", parent_run_token="parent-run-1",
    )
    durable_values = {"status": "completed", "result_exists": True,
                      "completion_authority": True}
    durable_values.update(changes)
    durable = DurableEvidence(**durable_values)
    return TaskSnapshot(identity, durable)


def test_new_result_contract_binds_complete_root_and_child_identity():
    record = canonical_result_for_task(task(), result())
    assert record["result_contract"]["schema"] == RESULT_SCHEMA
    assert record["identity"]["attempt_id"] == 3
    assert record["identity"]["parent_task_id"] == "parent-1"
    assert validate_result_contract(record).to_dict() == record["identity"]


def test_canonical_serialization_is_stable_and_does_not_add_secrets():
    one = canonical_result_for_task(task(), result())
    two = canonical_result_for_task(task(), result())
    assert one == two
    assert "prompt" not in one["result_contract"]
    assert "credential" not in one["result_contract"]


def test_receipt_projection_preserves_original_closed_sdk_payload():
    raw = {
        "task_id": task()["id"], "run_token": task()["run_token"],
        "fencing_token": task()["fencing_token"],
        "idempotency_key": task()["idempotency_key"],
        "status": "completed", "evidence": [{"artifact": "sha256:" + "a" * 64}],
        "artifact_sha256": "b" * 64, "summary": "verified fixture",
    }
    record = canonical_result_for_task(task(), {**raw, "observed_at": "2026-11-08T10:00:00Z"})
    assert receipt_payload_for_result(record, expected_identity=record["identity"]) == raw


def test_receipt_projection_rejects_incomplete_canonical_payload():
    raw = {"status": "completed", "evidence": [{"artifact": "sha256:" + "a" * 64}],
           "summary": "verified fixture", "completed_at": "2026-11-08T10:00:00Z"}
    record = canonical_result_for_task(task(), raw)
    record.pop("artifact_sha256", None)
    with pytest.raises(ResultContractError):
        receipt_payload_for_result(record, expected_identity=record["identity"])


def test_receipt_projection_requires_authoritative_identity_when_supplied():
    record = canonical_result_for_task(task(), result())
    foreign = dict(record["identity"], attempt_id=99)
    with pytest.raises(ResultContractError, match="result_contract_identity_mismatch"):
        receipt_payload_for_result(record, expected_identity=foreign)


def test_receipt_projection_rejects_canonical_record_without_authoritative_identity():
    record = canonical_result_for_task(task(), result())
    with pytest.raises(ResultContractError, match="expected_identity_missing"):
        receipt_payload_for_result(record)


def test_missing_publication_timestamp_is_not_filled_from_wall_clock():
    raw = result()
    raw.pop("completed_at")
    with pytest.raises(ResultContractError, match="result_publication_timestamp_missing"):
        canonical_result_for_task(task(), raw)


@pytest.mark.parametrize("field", [
    "repo", "issue", "id", "attempt_id", "run_token", "fencing_token",
    "ownership_epoch", "idempotency_key", "consumer",
])
def test_missing_authoritative_identity_never_gets_a_default(field):
    raw = task()
    raw.pop(field)
    with pytest.raises(ResultContractError, match="authoritative_task_identity_incomplete"):
        canonical_result_for_task(raw, result())


@pytest.mark.parametrize("field, value", [
    ("attempt_id", 2), ("run_token", "foreign"), ("fencing_token", 9),
    ("idempotency_key", "foreign"), ("consumer", "github:other/repo"),
    ("ownership_epoch", {"version": 1, "run_token": "foreign", "fencing_token": 8}),
])
def test_result_identity_conflict_is_fail_closed(field, value):
    record = canonical_result_for_task(task(), result())
    record["identity"][field] = value
    with pytest.raises(ResultContractError):
        validate_result_contract(record)


@pytest.mark.parametrize("field, value", [
    ("status", "done"), ("status", "terminal_unknown"), ("result_contract", {}),
])
def test_malformed_or_terminal_contract_does_not_validate(field, value):
    record = canonical_result_for_task(task(), result())
    record[field] = value
    with pytest.raises(ResultContractError):
        validate_result_contract(record)


def test_terminal_unknown_is_explicit_and_precedes_completed_claim():
    record = canonical_result_for_task(task(attempt_state="terminal_unknown"),
                                       result(status="terminal_unknown"),
                                       verification_state="terminal_unknown")
    current = snapshot(status="completed", terminal_unknown=True, delivery_uncertain=True)
    decision = reconcile_task(current, [record])
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED
    assert decision.safe_to_retry is False


def test_valid_contract_can_confirm_only_with_durable_host_acceptance():
    record = canonical_result_for_task(task(), accepted_result(), verification_state="verified")
    decision = reconcile_task(snapshot(), [record], observed_at="fixed")
    assert decision.status is DecisionStatus.RESULT_CONFIRMED
    assert decision.safe_to_retry is False


def test_invalid_contract_cannot_confirm_even_when_payload_looks_completed():
    record = canonical_result_for_task(task(), accepted_result(), verification_state="verified")
    tampered = copy.deepcopy(record)
    tampered["result_contract"]["authority"]["identity_binding"] = "0" * 64
    decision = reconcile_task(snapshot(), [tampered])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_contract_invalid"


def test_delivery_uncertainty_remains_recovery_required_with_valid_contract():
    record = canonical_result_for_task(task(), result(), verification_state="candidate")
    decision = reconcile_task(snapshot(delivery_uncertain=True), [record])
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED
    assert decision.safe_to_retry is False


def test_human_gate_is_not_overridden_by_result_contract():
    record = canonical_result_for_task(task(), accepted_result(), verification_state="verified")
    decision = reconcile_task(snapshot(status="blocked", blocker="human approval required",
                                       completion_authority=False), [record])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.safe_to_retry is False


def test_provenance_digest_and_evidence_reference_are_checked():
    record = canonical_result_for_task(task(), result())
    record["evidence"] = [{"artifact": "sha256:" + "b" * 64}]
    with pytest.raises(ResultContractError, match="source_digest_invalid|result_ref_invalid"):
        validate_result_contract(record)


def test_recovery_fields_are_publication_time_evidence_not_rebuilt_from_task_state():
    record = canonical_result_for_task(task(attempt_state="delivery_uncertain"), result(),
                                       verification_state="verified")
    assert record["result_contract"]["recovery"]["delivery_uncertain"] is True
    assert record["result_contract"]["recovery"]["attempt_state"] == "delivery_uncertain"
    validate_result_contract(record)


@pytest.mark.parametrize("field", ["authority_type", "verification_state"])
def test_non_string_authority_fields_fail_as_contract_errors(field):
    record = canonical_result_for_task(task(), result())
    record["result_contract"]["authority"][field] = []
    with pytest.raises(ResultContractError):
        validate_result_contract(record)

