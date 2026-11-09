from dataclasses import replace

import pytest

from herdr.reconciliation import (
    DecisionStatus,
    DurableEvidence,
    ExternalEvidence,
    ReconciliationError,
    TaskIdentity,
    TaskSnapshot,
    build_report,
    reconcile_snapshot,
    reconcile_task,
)
from herdr.result_contract import canonical_result_for_task


def identity(**changes):
    value = dict(
        repository="Bbambaaamm/herdr", issue="79", task_id="task-79",
        attempt_id=3, run_token="run-3", fencing_token=8, ownership_epoch=2,
        idempotency_key="idem-79-3", consumer="github:Bbambaaamm/herdr",
        parent_task_id="parent-1", parent_run_token="parent-run-1",
    )
    value.update(changes)
    return TaskIdentity(**value)


def snapshot(**changes):
    value = dict(status="blocked", blocker="provider unavailable", observed_at="2026-11-08T10:00:00Z")
    current_identity = changes.pop("identity", None) or identity()
    value.update(changes)
    return TaskSnapshot(current_identity, DurableEvidence(**value))


def result(**changes):
    value = dict(
        task_id="task-79", run_token="run-3", attempt_id=3, fencing_token=8,
        ownership_epoch=2, idempotency_key="idem-79-3", consumer="github:Bbambaaamm/herdr",
        parent_task_id="parent-1", parent_run_token="parent-run-1",
        status="completed", authoritative=True,
    )
    value.update(changes)
    return value


def test_matching_authoritative_result_is_confirmed():
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    decision = reconcile_task(current, [result()], observed_at="fixed")
    assert decision.status is DecisionStatus.RESULT_CONFIRMED
    assert decision.identity_match is True
    assert decision.safe_to_retry is False


@pytest.mark.parametrize("field, value", [("run_token", None), ("idempotency_key", None), ("attempt_id", None), ("fencing_token", None)])
def test_incomplete_identity_fails_closed(field, value):
    decision = reconcile_task(snapshot(identity=identity(**{field: value})))
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "incomplete_attempt_identity"


def test_stale_run_token_cannot_confirm():
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    decision = reconcile_task(current, [result(run_token="old-run")])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_identity_mismatch"


@pytest.mark.parametrize("field", ["attempt_id", "fencing_token", "ownership_epoch", "consumer", "parent_task_id", "parent_run_token"])
def test_stale_or_foreign_identity_cannot_confirm(field):
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    replacement = {"attempt_id": 2, "fencing_token": 7, "ownership_epoch": 1,
                   "consumer": "github:other/repo", "parent_task_id": "foreign", "parent_run_token": "foreign-run"}[field]
    decision = reconcile_task(current, [result(**{field: replacement})])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_identity_mismatch"


def test_duplicate_matching_results_are_unknown():
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    decision = reconcile_task(current, [result(), result(result_digest="different")])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "conflicting_or_duplicate_results"


def test_duplicate_evidence_digest_is_order_independent():
    current = snapshot(result_exists=True)
    older = result(run_token="old-run", attempt_id=2)
    newer = result(status="failed")
    one = reconcile_task(current, [older, newer], observed_at="fixed")
    two = reconcile_task(current, [newer, older], observed_at="fixed")
    assert one.status is DecisionStatus.UNKNOWN
    assert one.decision_id == two.decision_id


def test_invalid_contract_evidence_is_order_independent():
    canonical_task = {
        "repo": "Bbambaaamm/herdr", "issue": 79, "id": "task-79", "attempt_id": 3,
        "run_token": "run-3", "fencing_token": 8,
        "ownership_epoch": {"version": 1, "run_token": "run-3", "fencing_token": 8},
        "idempotency_key": "idem-79-3", "consumer": "github:Bbambaaamm/herdr",
    }
    base = {"status": "completed", "evidence": [{"artifact": "sha256:" + "a" * 64}],
            "summary": "fixture", "completed_at": "2026-11-08T10:00:00Z"}
    first = canonical_result_for_task(canonical_task, base)
    second = canonical_result_for_task(canonical_task, {**base, "summary": "other"})
    first["result_contract"]["authority"]["identity_binding"] = "1" * 64
    second["result_contract"]["authority"]["identity_binding"] = "2" * 64
    one = reconcile_task(snapshot(), [first, second], observed_at="fixed")
    two = reconcile_task(snapshot(), [second, first], observed_at="fixed")
    assert one.reason_code == two.reason_code == "result_contract_invalid"
    assert one.decision_id == two.decision_id
    assert one.evidence_refs == two.evidence_refs


def test_completed_status_without_authority_is_not_acceptance():
    current = snapshot(status="completed", result_exists=True, completion_authority=False)
    decision = reconcile_task(current, [result(authoritative=False)])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "completion_authority_unproven"


@pytest.mark.parametrize("field", ["authoritative", "completion_authority"])
def test_non_boolean_result_authority_is_not_coerced(field):
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    decision = reconcile_task(current, [result(**{field: "false"})])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "completion_authority_unproven"


@pytest.mark.parametrize("field, value", [("attempt_id", True), ("fencing_token", 8.0), ("ownership_epoch", True)])
def test_non_exact_result_identity_types_are_rejected(field, value):
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    decision = reconcile_task(current, [result(**{field: value})])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_identity_mismatch"


def test_durable_result_identity_conflict_is_not_overridden_by_matching_record():
    current = snapshot(
        status="completed", result_exists=True, completion_authority=True,
        result_identity={**result(), "run_token": "old-run"}, result_status="failed",
    )
    decision = reconcile_task(current, [result()])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "durable_result_identity_conflict"


def test_durable_result_status_conflict_is_not_overridden_by_matching_record():
    current = snapshot(status="completed", result_exists=True, completion_authority=True,
                       result_identity=result(), result_status="failed")
    decision = reconcile_task(current, [result()])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "durable_result_status_conflict"


def test_historical_completed_result_does_not_complete_current_blocked_attempt():
    decision = reconcile_task(snapshot(), [result(attempt_id=2, run_token="old-run")])
    assert decision.status is DecisionStatus.STILL_BLOCKED


@pytest.mark.parametrize("changes", [
    {"delivery_uncertain": True},
    {"terminal_unknown": True},
    {"recovery_state": "delivery_uncertain_requires_recovery"},
])
def test_delivery_uncertainty_requires_recovery(changes):
    decision = reconcile_task(snapshot(**changes), [result()])
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED
    assert decision.safe_to_retry is False


def test_submission_intent_without_result_requires_reconciliation():
    decision = reconcile_task(snapshot(submission_intent=True))
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED
    assert decision.reason_code == "submission_without_matching_result"


def test_result_exists_without_matching_identity_is_unknown():
    decision = reconcile_task(snapshot(result_exists=True), [result(run_token="wrong")])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_identity_mismatch"


def test_issue_closed_while_blocked_is_stale_not_accepted():
    decision = reconcile_task(snapshot(), external=ExternalEvidence(issue_state="closed"))
    assert decision.status is DecisionStatus.STALE_BLOCKER
    assert decision.human_gate is False


def test_external_evidence_cannot_erase_human_gate():
    current = snapshot(blocker="human approval required")
    for external in ({"issue_state": "closed"}, {"required_ci": "failed"}):
        decision = reconcile_task(current, external=external)
        assert decision.status is DecisionStatus.HUMAN_GATE
        assert decision.human_gate is True


def test_open_issue_conflicts_with_durable_done():
    decision = reconcile_task(snapshot(status="done"), external={"issue_state": "open"})
    assert decision.status is DecisionStatus.STALE_BLOCKER


def test_merged_pr_after_blocker_is_stale_blocker():
    decision = reconcile_task(snapshot(), external={"pr_state": "merged"})
    assert decision.status is DecisionStatus.STALE_BLOCKER


def test_required_ci_failure_keeps_task_blocked():
    decision = reconcile_task(snapshot(), external={"required_ci": "failed"})
    assert decision.status is DecisionStatus.STILL_BLOCKED
    assert decision.reason_code == "required_ci_not_green"


def test_stale_review_keeps_task_blocked():
    decision = reconcile_task(snapshot(), external={"review_state": "stale"})
    assert decision.status is DecisionStatus.STILL_BLOCKED
    assert decision.reason_code == "review_gate_incomplete"


def test_unavailable_external_evidence_is_unknown():
    decision = reconcile_task(snapshot(), external={"available": False, "error_code": "rate_limit"})
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "external_evidence_unavailable"


@pytest.mark.parametrize("blocker", ["human approval required", "credential missing", "manual_gate"])
def test_privileged_blocker_is_human_gate(blocker):
    decision = reconcile_task(snapshot(blocker=blocker))
    assert decision.status is DecisionStatus.HUMAN_GATE
    assert decision.human_gate is True


def test_unsupported_state_fails_closed():
    decision = reconcile_task(snapshot(status="mystery"))
    assert decision.status is DecisionStatus.UNKNOWN


def test_decision_is_deterministic_and_redacted():
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    one = reconcile_task(current, [result(prompt="do not publish", secret="hidden")], observed_at="fixed")
    two = reconcile_task(current, [result(prompt="do not publish", secret="hidden")], observed_at="fixed")
    assert one.to_dict() == two.to_dict()
    assert "hidden" not in repr(one.to_dict())


def test_snapshot_order_and_report_counts():
    first = snapshot()
    second = TaskSnapshot(replace(first.identity, task_id="task-1"), first.durable)
    decisions = reconcile_snapshot([first, second])
    assert [item.task_id for item in decisions] == ["task-1", "task-79"]
    report = build_report(decisions)
    assert report["decision_count"] == 2
    assert sum(report["counts"].values()) == 2
    assert report["safe_to_retry"] is False
    assert report["replay_status"] == "NOT_RUN"


def test_malformed_result_record_rejected():
    with pytest.raises(ReconciliationError):
        reconcile_task(snapshot(), ["not-an-object"])


def test_result_digest_and_evidence_refs_are_stable():
    current = snapshot(status="completed", result_exists=True, completion_authority=True)
    decision = reconcile_task(current, [result()], observed_at="fixed")
    assert decision.decision_id == reconcile_task(current, [result()], observed_at="fixed").decision_id
    assert all("prompt" not in ref and "secret" not in ref for ref in decision.evidence_refs)

