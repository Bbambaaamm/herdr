import copy
import json
import os
import tempfile
from pathlib import Path

import pytest

import herdr.durable_identity_adapter as adapter

from herdr.durable_identity_adapter import (
    ADAPTER_VERSION,
    DurableIdentityAdapterError,
    build_reconciliation_snapshot,
    collect_authoritative_attempt_evidence,
    normalize_legacy_durable_task,
    normalize_legacy_result_records,
    read_legacy_json,
    reconcile_legacy_task,
)
from herdr.reconciliation import DecisionStatus, build_report


def legacy(**changes):
    value = {
        "repository": "Bbambaaamm/herdr", "issue": "79", "task_id": "legacy-79",
        "attempt_id": 3, "run_token": "run-3", "fencing_token": 8,
        "ownership_epoch": 2, "ownership_epoch_schema": "host-v1",
        "ownership_epoch_authority": "host", "idempotency_key": "idem-79-3",
        "consumer": "github:Bbambaaamm/herdr", "status": "blocked",
        "blocker": "provider unavailable", "observed_at": "2026-11-08T10:00:00Z",
    }
    value.update(changes)
    return value


def result(**changes):
    value = {
        "task_id": "legacy-79", "run_token": "run-3", "attempt_id": 3,
        "fencing_token": 8, "ownership_epoch": 2, "idempotency_key": "idem-79-3",
        "consumer": "github:Bbambaaamm/herdr", "status": "completed",
        "authoritative": True,
    }
    value.update(changes)
    return value


def test_supported_host_epoch_builds_identity_only_with_explicit_contract():
    normalized = normalize_legacy_durable_task(legacy())
    assert normalized.supported is True
    assert normalized.snapshot.identity.ownership_epoch == 2
    assert normalized.reason_code is None


@pytest.mark.parametrize("field", [
    "repository", "issue", "task_id", "attempt_id", "run_token",
    "fencing_token", "idempotency_key", "consumer",
])
def test_missing_required_identity_is_unknown(field):
    raw = legacy()
    raw.pop(field)
    normalized = normalize_legacy_durable_task(raw)
    assert normalized.supported is False
    decision = reconcile_legacy_task(raw)
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.safe_to_retry is False


@pytest.mark.parametrize("value", [None, 0, 1, "2", {"epoch": 2}, {"value": 2}])
def test_missing_or_untrusted_epoch_never_defaults_to_zero(value):
    raw = legacy()
    raw.pop("ownership_epoch_schema", None)
    raw.pop("ownership_epoch_authority", None)
    raw["ownership_epoch"] = value
    decision = reconcile_legacy_task(raw)
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "unsupported_legacy_ownership_epoch"


def test_nested_epoch_requires_schema_and_host_authority():
    raw = legacy(ownership_epoch={"schema": "host-v1", "authority": "host", "value": 9})
    normalized = normalize_legacy_durable_task(raw)
    assert normalized.supported is True
    assert normalized.snapshot.identity.ownership_epoch == 9


@pytest.mark.parametrize("field,value", [
    ("attempt_id", True), ("fencing_token", 8.0), ("run_token", 3),
    ("consumer", ""), ("parent_task_id", "only-parent"),
])
def test_malformed_identity_fails_closed(field, value):
    raw = legacy(**{field: value})
    decision = reconcile_legacy_task(raw)
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.safe_to_retry is False


def test_matching_authoritative_result_is_reconciled():
    raw = legacy(status="completed", result_exists=True, completion_authority=True,
                 result_identity=result(), result_status="completed")
    decision = reconcile_legacy_task(raw, result_records=[result()])
    assert decision.status is DecisionStatus.RESULT_CONFIRMED
    assert decision.policy_version == ADAPTER_VERSION


@pytest.mark.parametrize("field,value", [
    ("run_token", "foreign"), ("attempt_id", 2), ("fencing_token", 7),
    ("ownership_epoch", 1), ("idempotency_key", "foreign"),
    ("consumer", "github:other/repo"),
])
def test_stale_or_foreign_result_cannot_confirm(field, value):
    raw = legacy(status="completed", result_exists=True, completion_authority=True)
    decision = reconcile_legacy_task(raw, result_records=[result(**{field: value})])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_identity_mismatch"


def test_result_identity_conflict_is_not_overridden():
    raw = legacy(status="completed", result_exists=True, completion_authority=True,
                 result_identity=result(), result_status="completed")
    decision = reconcile_legacy_task(raw, result_records=[result(), result(status="failed")])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "conflicting_or_duplicate_results"


def test_result_without_explicit_epoch_is_unknown_even_when_task_epoch_is_zero():
    raw = legacy(ownership_epoch=0, status="completed", result_exists=True, completion_authority=True)
    incomplete = result()
    incomplete.pop("ownership_epoch")
    decision = reconcile_legacy_task(raw, result_records=[incomplete])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_ownership_epoch_invalid"


def test_embedded_result_without_explicit_epoch_is_unknown():
    embedded = result()
    embedded.pop("ownership_epoch")
    decision = reconcile_legacy_task(legacy(result_identity=embedded, result_exists=True))
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_ownership_epoch_invalid"


@pytest.mark.parametrize("bad_identity", [None, [], "text", 1, True])
def test_non_object_embedded_result_identity_fails_closed(bad_identity):
    decision = reconcile_legacy_task(
        legacy(result_identity=bad_identity, result_exists=True)
    )
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "result_identity_not_object"


@pytest.mark.parametrize("bad_identity", [None, [], "text", 1, True])
def test_non_object_nested_result_identity_fails_closed(bad_identity):
    with pytest.raises(DurableIdentityAdapterError, match="result_identity_not_object"):
        normalize_legacy_result_records(
            [{"identity": bad_identity}], require_identity=True
        )


@pytest.mark.parametrize("changes", [
    {"delivery_uncertain": True}, {"terminal_unknown": True},
    {"recovery_state": "delivery_uncertain_requires_recovery"},
])
def test_delivery_uncertainty_is_preserved_and_requires_recovery(changes):
    decision = reconcile_legacy_task(legacy(**changes), result_records=[result()])
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED
    assert decision.safe_to_retry is False


@pytest.mark.parametrize("attempt_state", ["delivery_uncertain", "terminal_unknown"])
def test_attempt_state_cannot_be_erased_by_completed_scheduler_state(attempt_state):
    raw = legacy(status="completed", attempt_state=attempt_state,
                 result_exists=True, completion_authority=True, result_identity=result())
    decision = reconcile_legacy_task(raw, result_records=[result()])
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED


def test_terminal_unknown_does_not_transfer_identity():
    raw = legacy(attempt_state="terminal_unknown", terminal_unknown=True,
                 idempotency_key="idem-78", task_id="herdr-78")
    decision = reconcile_legacy_task(raw)
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED
    assert "refresh" not in decision.required_action.lower() or decision.safe_to_retry is False


def test_submission_without_result_requires_reconciliation():
    decision = reconcile_legacy_task(legacy(submission_intent=True))
    assert decision.status is DecisionStatus.RECOVERY_REQUIRED
    assert decision.reason_code == "submission_without_matching_result"


def test_external_human_gate_is_not_erased():
    decision = reconcile_legacy_task(legacy(blocker="human approval required"), external={"issue_state": "closed"})
    assert decision.status is DecisionStatus.HUMAN_GATE
    assert decision.human_gate is True


def test_result_normalization_copies_and_rejects_non_objects():
    original = [result()]
    normalized = normalize_legacy_result_records(original)
    assert normalized == (original[0],)
    assert normalized[0] is not original[0]
    with pytest.raises(DurableIdentityAdapterError):
        normalize_legacy_result_records(["not-an-object"])


def test_attempt_evidence_is_bounded_and_has_stable_refs():
    normalized = normalize_legacy_durable_task(legacy())
    evidence = collect_authoritative_attempt_evidence(normalized, attempts=[{"ignored": True}], results=[result()], authority=[{"source": "host"}])
    assert evidence.conflicts == ()
    assert any(ref.startswith("results:") for ref in evidence.evidence_refs)
    repeat = collect_authoritative_attempt_evidence(normalized, results=[result()], authority=[{"source": "host"}])
    assert evidence.results == repeat.results
    assert evidence.authority == repeat.authority
    assert evidence.evidence_refs != repeat.evidence_refs  # the attempt observation is retained in refs


def test_attempt_or_host_authority_cannot_replace_task_identity():
    normalized = normalize_legacy_durable_task(legacy())
    evidence = collect_authoritative_attempt_evidence(
        normalized,
        attempts=[{"task_id": "legacy-79", "run_token": "foreign"}],
        authority=[{"task_id": "legacy-79", "fencing_token": 99}],
    )
    assert evidence.conflicts == ("attempt_identity_conflict", "authority_identity_conflict")
    decision = reconcile_legacy_task(
        legacy(), attempt_records=[{"task_id": "legacy-79", "run_token": "foreign"}]
    )
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "conflicting_legacy_evidence"


def test_attempt_identity_alias_is_checked():
    normalized = normalize_legacy_durable_task(legacy())
    evidence = collect_authoritative_attempt_evidence(
        normalized, attempts=[{"task_id": "legacy-79", "attempt_identity": 2}]
    )
    assert evidence.conflicts == ("attempt_identity_conflict",)


def test_duplicate_result_identity_is_not_authoritative():
    decision = reconcile_legacy_task(legacy(), result_records=[result(), result()])
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "conflicting_legacy_evidence"


def test_input_is_not_mutated_and_decision_is_deterministic():
    raw = legacy()
    before = copy.deepcopy(raw)
    one = reconcile_legacy_task(raw)
    two = reconcile_legacy_task(raw)
    assert raw == before
    assert one.to_dict() == two.to_dict()


def test_supported_decision_retains_attempt_and_authority_provenance():
    decision = reconcile_legacy_task(
        legacy(), result_records=[result()],
        attempt_records=[{"task_id": "legacy-79", "attempt_identity": 3, "audit_id": "a1"}],
        authority_records=[{"task_id": "legacy-79", "audit_id": "h1"}],
    )
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "completion_authority_unproven"
    assert any(ref.startswith("attempts:") for ref in decision.evidence_refs)
    assert any(ref.startswith("authority:") for ref in decision.evidence_refs)


def test_unknown_records_get_stable_redacted_identity_label():
    raw = {"id": "legacy-unknown", "secret": "do-not-publish"}
    decision = reconcile_legacy_task(raw)
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.decision_id == reconcile_legacy_task(raw).decision_id
    assert "do-not-publish" not in repr(decision.to_dict())


def test_file_reader_rejects_symlink_and_tocou_is_bounded():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        tmp_path = Path(directory)
        target = tmp_path / "record.json"
        target.write_text(json.dumps(legacy()), encoding="utf-8")
        assert read_legacy_json(target)["task_id"] == "legacy-79"
        link = tmp_path / "link.json"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks unavailable on this platform")
        with pytest.raises(DurableIdentityAdapterError, match="regular"):
            read_legacy_json(link)


def test_file_reader_rejects_pathname_replacement_between_lstat_and_open(monkeypatch):
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        tmp_path = Path(directory)
        target = tmp_path / "record.json"
        replacement = tmp_path / "replacement.json"
        target.write_text(json.dumps(legacy(task_id="before")), encoding="utf-8")
        replacement.write_text(json.dumps(legacy(task_id="after")), encoding="utf-8")
        real_open = adapter.os.open
        replaced = False

        def replace_before_open(path, flags, *args, **kwargs):
            nonlocal replaced
            if not replaced and Path(path) == target:
                replaced = True
                os.replace(replacement, target)
            return real_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(adapter.os, "open", replace_before_open)
        with pytest.raises(DurableIdentityAdapterError, match="changed_during_read"):
            read_legacy_json(target)


def test_non_object_file_is_rejected():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        target = Path(directory) / "array.json"
        target.write_text("[]", encoding="utf-8")
        with pytest.raises(DurableIdentityAdapterError, match="object"):
            read_legacy_json(target)


def test_report_can_classify_seventy_three_without_side_effects():
    rows = []
    for index in range(73):
        raw = legacy(task_id=f"legacy-{index}", issue=str(index + 1))
        rows.append(reconcile_legacy_task(raw))
    report = build_report(rows)
    assert report["decision_count"] == 73
    assert report["replay_status"] == "NOT_RUN"
    assert sum(report["counts"].values()) == 73
    assert report["safe_to_retry"] is False


def test_cross_consumer_is_not_accepted():
    raw = legacy(consumer="github:Bbambaaamm/other")
    decision = reconcile_legacy_task(raw)
    assert decision.status is DecisionStatus.UNKNOWN
    assert decision.reason_code == "cross_consumer_identity"


@pytest.mark.parametrize("bad", [None, [], "text", 1])
def test_non_mapping_legacy_row_fails_without_guessing(bad):
    with pytest.raises(DurableIdentityAdapterError):
        normalize_legacy_durable_task(bad)

