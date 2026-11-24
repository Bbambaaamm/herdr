"""Offline incident reconciliation tests (R1-R8 + replay/concurrency/crash).

These tests use synthetic bootstrap artifacts shaped like the existing
``supervisor.py`` records.  They never touch the active supervisor, checkpoints,
locks, runtime paths or any process.  The evaluator is treated as an offline
basis for a future integration, never as admission authority.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "agent-stack" / "bin" / "agent_stack_reconciliation.py"
)


def _load():
    spec = importlib.util.spec_from_file_location(
        "agent_stack_reconciliation_test_" + str(abs(hash(MODULE_PATH))), MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def rec():
    return _load()


ORIGINAL_COMMIT = "a" * 40
CURRENT_HEAD = "b" * 40


def _checkpoint_raw() -> bytes:
    checkpoint = {
        "task": "reconcile paused cycle",
        "worktree": "/tmp/isolated-worktree",
        "branch": "fix/example",
        "commit": ORIGINAL_COMMIT,
        "next_action": "inspect retained evidence",
        "changed_files": ["a.py"],
        "tests": ["test_a.py"],
        "side_processes": [],
        "pr": "https://github.com/Bbambaaamm/herdr/pull/1",
        "ci": {"pass": True},
        "review": {"pass": True},
    }
    return json.dumps(checkpoint, sort_keys=True).encode("utf-8")


def _waiting_raw(checkpoint_sha256: str) -> bytes:
    waiting = {
        "status": "WAITING",
        "safe_to_continue": True,
        "reason": "operator input required",
        "next_action": "await operator",
        "progress_key": "wait:operator",
        "checkpoint_sha256": checkpoint_sha256,
    }
    return json.dumps(waiting, sort_keys=True).encode("utf-8")


def _paused_raw(checkpoint_sha256: str | None = None) -> bytes:
    if checkpoint_sha256 is None:
        checkpoint_sha256 = hashlib.sha256(_checkpoint_raw()).hexdigest()
    paused = {
        "status": "PAUSED",
        "safe_to_continue": False,
        "reason": "emergency stop",
        "next_action": "reconcile before explicit restart",
        "progress_key": "supervisor-paused:emergency",
        "source": "supervisor_emergency_checkpoint",
        "checkpoint_sha256": checkpoint_sha256,
    }
    return json.dumps(paused, sort_keys=True).encode("utf-8")


def _observed(**overrides):
    observed = {
        "exact_current_pr_head": CURRENT_HEAD,
        "checkpoint_changed": False,
        "original_is_ancestor_of_current": True,
        "remote_head_matches": True,
        "exact_head_ci_pass": True,
        "exact_head_independent_review_pass": True,
        "independent_review_head": CURRENT_HEAD,
        "review_stale": False,
        "review_expired": False,
        "supervisor_alive": False,
        "interactive_hermes_present": False,
        "locks_free": True,
        "capacity_ready": True,
        "native_durable_work_unknown": False,
        "native_durable_work_pending": False,
        "side_processes_reconciled": True,
        "live_side_child": False,
        "original_exit_zero": True,
        "operator_review": {"accepted": True, "head": CURRENT_HEAD,
                            "expires_at_epoch": 1900000000},
        "policy_and_budget_unchanged": True,
        "one_shot_admission_verified": True,
        "fence_budget_current": True,
        "now_epoch": 1800000000,
    }
    observed.update(overrides)
    return observed


def _artifacts():
    checkpoint_raw = _checkpoint_raw()
    checkpoint_sha = hashlib.sha256(checkpoint_raw).hexdigest()
    waiting_raw = _waiting_raw(checkpoint_sha)
    return checkpoint_raw, waiting_raw, _paused_raw(checkpoint_sha), checkpoint_sha


def _evaluate(rec, **overrides):
    checkpoint_raw, waiting_raw, paused_raw, _ = _artifacts()
    kwargs = dict(
        checkpoint_raw=checkpoint_raw,
        original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw,
        observed=_observed(),
    )
    kwargs.update(overrides)
    return rec.evaluate_incident(**kwargs)


# R1 -------------------------------------------------------------------------
def test_r1_generic_resume_rejected_for_emergency_paused(rec):
    decision = _evaluate(rec, observed=_observed(resume_mode="generic"))
    assert decision.decision == "BLOCKED"
    assert decision.reason == rec.BLOCKED_GENERIC_RESUME
    assert decision.direct_worker_launch_authorized is False

    reviewed = _evaluate(rec, observed=_observed(resume_mode="resume-reviewed"))
    assert reviewed.reason == rec.BLOCKED_GENERIC_RESUME
    assert reviewed.direct_worker_launch_authorized is False

    ticket = _evaluate(rec, observed=_observed(resume_ticket_kind="generic"))
    assert ticket.reason == rec.BLOCKED_GENERIC_RESUME


# R2 -------------------------------------------------------------------------
@pytest.mark.parametrize("override", [
    {"checkpoint_changed": True},
    {"original_is_ancestor_of_current": False},
])
def test_r2_lineage_break_blocks(rec, override):
    decision = _evaluate(rec, observed=_observed(**override))
    assert decision.reason == rec.BLOCKED_LINEAGE


def test_r2_remote_head_mismatch_blocks(rec):
    decision = _evaluate(rec, observed=_observed(remote_head_matches=False))
    assert decision.reason == rec.BLOCKED_HEAD_MISMATCH


def test_r2_missing_or_invalid_current_head_blocks(rec):
    assert _evaluate(rec, observed=_observed(exact_current_pr_head=None)).reason \
        == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE
    assert _evaluate(rec, observed=_observed(exact_current_pr_head="xyz")).reason \
        == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE


# R3 -------------------------------------------------------------------------
def test_r3_ci_failure_blocks(rec):
    decision = _evaluate(rec, observed=_observed(exact_head_ci_pass=False))
    assert decision.reason == rec.BLOCKED_EVIDENCE_CI_REVIEW


def test_r3_independent_review_failure_blocks(rec):
    decision = _evaluate(
        rec, observed=_observed(exact_head_independent_review_pass=False))
    assert decision.reason == rec.BLOCKED_EVIDENCE_CI_REVIEW


@pytest.mark.parametrize("override", [
    {"independent_review_head": "c" * 40},
    {"review_stale": True},
    {"review_expired": True},
])
def test_r3_stale_review_blocks(rec, override):
    decision = _evaluate(rec, observed=_observed(**override))
    assert decision.reason == rec.BLOCKED_EVIDENCE_CI_REVIEW


# R4 -------------------------------------------------------------------------
def test_r4_interactive_session_present_blocks(rec):
    decision = _evaluate(rec, observed=_observed(interactive_hermes_present=True))
    assert decision.reason == rec.BLOCKED_INTERACTIVE_PRESENT
    assert decision.direct_worker_launch_authorized is False


def test_active_supervisor_blocks(rec):
    decision = _evaluate(rec, observed=_observed(supervisor_alive=True))
    assert decision.reason == rec.BLOCKED_ACTIVE_SUPERVISOR


# R5 -------------------------------------------------------------------------
@pytest.mark.parametrize("override", [
    {"native_durable_work_unknown": True},
    {"native_durable_work_pending": True},
    {"side_processes_reconciled": False},
    {"live_side_child": True},
    {"original_exit_zero": False},
])
def test_r5_unknown_side_effect_never_retries(rec, override):
    decision = _evaluate(rec, observed=_observed(**override))
    assert decision.reason == rec.BLOCKED_UNKNOWN_SIDE_EFFECT
    assert decision.direct_worker_launch_authorized is False


def test_r5_after_start_before_receipt_is_unknown(rec):
    decision = _evaluate(rec, crash_window="after_start_before_receipt")
    assert decision.reason == rec.BLOCKED_UNKNOWN_SIDE_EFFECT


# R6 -------------------------------------------------------------------------
def test_r6_crash_before_claim_can_be_proposed_with_fresh_acceptance(rec):
    decision = _evaluate(rec, crash_window="before_claim")
    assert decision.decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY
    assert decision.requires_fresh_operator_acceptance is True


def test_r6_crash_after_claim_before_start_blocks_until_resolved(rec):
    blocked = _evaluate(rec, crash_window="after_claim_before_start")
    assert blocked.reason == rec.BLOCKED_CRASH_WINDOW

    released = _evaluate(
        rec, crash_window="after_claim_before_start",
        observed=_observed(claim_receipt={
            "claim_id": "claim-1",
            "checkpoint_sha256": hashlib.sha256(_checkpoint_raw()).hexdigest(),
            "state": "consumed",
            "receipt_sha256": "c" * 64,
        }))
    assert released.decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY


def test_r6_crash_window_value_is_validated(rec):
    decision = _evaluate(rec, crash_window="during_result_delivery")
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE


def test_resume_ticket_binding_mirrors_supervisor_checks(rec):
    previous = "/jobs/previous"
    continuation = b'{"status":"WAITING"}'
    sha = hashlib.sha256(continuation).hexdigest()
    rec.validate_resume_ticket(
        {"previous": previous, "decision_sha256": sha},
        previous=previous, continuation_sha256=sha)
    with pytest.raises(rec.ReconciliationError):
        rec.validate_resume_ticket(
            {"previous": "/jobs/other", "decision_sha256": sha},
            previous=previous, continuation_sha256=sha)
    with pytest.raises(rec.ReconciliationError):
        rec.validate_resume_ticket(
            {"previous": previous, "decision_sha256": "0" * 64},
            previous=previous, continuation_sha256=sha)


# R7 -------------------------------------------------------------------------
@pytest.mark.parametrize("override", [
    {"operator_review": None},
    {"operator_review": {"accepted": False, "head": CURRENT_HEAD}},
    {"operator_review": {"accepted": True, "head": "c" * 40}},
    {"operator_review": {"accepted": True, "head": CURRENT_HEAD}},
    {"operator_review": {"accepted": True, "head": CURRENT_HEAD,
                          "expires_at_epoch": "1900000000"}},
    {"operator_review": {"accepted": True, "head": CURRENT_HEAD,
                          "expires_at_epoch": True}},
    {"operator_review": {"accepted": True, "head": CURRENT_HEAD,
                          "expires_at_epoch": 1700000000}},
    {"now_epoch": True},
])
def test_r7_operator_review_gaps_block(rec, override):
    decision = _evaluate(rec, observed=_observed(**override))
    assert decision.reason == rec.BLOCKED_OPERATOR_REVIEW


@pytest.mark.parametrize("override", [
    {"policy_and_budget_unchanged": False},
    {"one_shot_admission_verified": False},
    {"fence_budget_current": False},
])
def test_r7_policy_budget_fence_drift_blocks(rec, override):
    decision = _evaluate(rec, observed=_observed(**override))
    assert decision.reason == rec.BLOCKED_POLICY_DRIFT


def test_locks_and_capacity_fail_closed(rec):
    assert _evaluate(rec, observed=_observed(locks_free=False)).reason \
        == rec.BLOCKED_LOCKS_HELD
    assert _evaluate(rec, observed=_observed(capacity_ready=False)).reason \
        == rec.BLOCKED_CAPACITY_NOT_READY


@pytest.mark.parametrize("key", [
    "supervisor_alive",
    "interactive_hermes_present",
    "native_durable_work_unknown",
    "native_durable_work_pending",
    "live_side_child",
    "checkpoint_changed",
    "exact_head_ci_pass",
    "original_exit_zero",
])
def test_omitted_or_wrong_typed_known_negative_facts_block(rec, key):
    observed = _observed()
    del observed[key]
    assert _evaluate(rec, observed=observed).reason \
        == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE
    assert _evaluate(rec, observed=_observed(**{key: "false"})).reason \
        == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE
    assert _evaluate(rec, observed=_observed(**{key: None})).reason \
        == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE


@pytest.mark.parametrize("key,value", [
    ("exact_current_pr_head", "not-a-sha"),
    ("independent_review_head", 7),
    ("resume_mode", 1),
    ("resume_ticket_kind", []),
])
def test_wrong_typed_observed_scalars_block(rec, key, value):
    decision = _evaluate(rec, observed=_observed(**{key: value}))
    assert decision.reason == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE


def test_exact_incident_requires_original_waiting_bytes(rec):
    checkpoint_raw, _, paused_raw, _ = _artifacts()
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=None,
        emergency_pause_raw=paused_raw, observed=_observed())
    assert decision.reason == rec.BLOCKED_ORIGINAL_WAITING_INVALID


def test_emergency_pause_must_bind_checkpoint_digest(rec):
    checkpoint_raw = _checkpoint_raw()
    paused = json.loads(_paused_raw(hashlib.sha256(checkpoint_raw).hexdigest()))
    paused["checkpoint_sha256"] = "0" * 64
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw,
        original_waiting_raw=_waiting_raw(hashlib.sha256(checkpoint_raw).hexdigest()),
        emergency_pause_raw=json.dumps(paused).encode(), observed=_observed())
    assert decision.reason == rec.BLOCKED_CHECKPOINT_INVALID


@pytest.mark.parametrize("receipt", [
    None,
    {"claim_id": "claim-1"},
    {"claim_id": "claim-1", "checkpoint_sha256": "0" * 64,
     "state": "consumed", "receipt_sha256": "c" * 64},
    {"claim_id": "claim-1", "checkpoint_sha256": hashlib.sha256(_checkpoint_raw()).hexdigest(),
     "state": "still-held", "receipt_sha256": "c" * 64},
    {"claim_id": "claim-1", "checkpoint_sha256": hashlib.sha256(_checkpoint_raw()).hexdigest(),
     "state": "released", "receipt_sha256": "xyz"},
])
def test_claim_receipt_binding_gaps_block(rec, receipt):
    decision = _evaluate(
        rec, crash_window="after_claim_before_start",
        observed=_observed(claim_receipt=receipt))
    assert decision.reason == rec.BLOCKED_CRASH_WINDOW


@pytest.mark.parametrize("receipts", [
    {"kind": "admitted_proposal"},
    [{"kind": 1, "request_key": "req-1", "evidence_digest": "a" * 64}],
    [{"kind": "admitted_proposal", "request_key": 1, "evidence_digest": "a" * 64}],
    [{"kind": "admitted_proposal", "request_key": "req-1",
      "evidence_digest": "short"}],
])
def test_malformed_prior_receipts_block(rec, receipts):
    decision = _evaluate(rec, prior_receipts=receipts)
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE


# R8 -------------------------------------------------------------------------
def test_r8_positive_proposal_plans_exactly_one_parent_cycle(rec):
    decision = _evaluate(rec)
    assert decision.decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY
    assert decision.max_parent_cycles == 1
    assert decision.interactive_panel_start_during_cycle is False
    assert decision.direct_worker_launch_authorized is False
    assert decision.requires_fresh_operator_acceptance is True
    assert isinstance(decision.proposal_digest, str) and len(decision.proposal_digest) == 64


def test_evaluation_is_deterministic(rec):
    first = _evaluate(rec)
    second = _evaluate(rec)
    assert first.to_json() == second.to_json()


# Replay / concurrency -------------------------------------------------------
def _proposal_decision(rec):
    checkpoint_raw, waiting_raw, paused_raw, _ = _artifacts()
    return rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=_observed(), request_key="req-1")


def _inputs():
    checkpoint_raw = _checkpoint_raw()
    waiting_raw = _waiting_raw(hashlib.sha256(checkpoint_raw).hexdigest())
    return checkpoint_raw, waiting_raw, _paused_raw(), _observed()


def test_replay_same_request_and_evidence_is_idempotent(rec):
    checkpoint_raw, waiting_raw, paused_raw, observed = _inputs()
    proposal = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed, request_key="req-1")
    assert proposal.decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY
    evidence_digest = rec.derive_evidence_digest(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed)
    receipt = {"kind": "admitted_proposal", "request_key": "req-1",
               "evidence_digest": evidence_digest}
    replay = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed,
        prior_receipts=(receipt,), request_key="req-1")
    assert replay.decision == rec.REPLAY_IDENTICAL_NO_START
    assert replay.replay is True
    assert replay.direct_worker_launch_authorized is False


def test_replay_same_request_with_changed_evidence_conflicts(rec):
    checkpoint_raw, waiting_raw, paused_raw, _ = _inputs()
    changed = _observed(operator_note="changed-after-receipt")
    receipt = {"kind": "admitted_proposal", "request_key": "req-1",
               "evidence_digest": "0" * 64}
    conflict = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=changed,
        prior_receipts=(receipt,), request_key="req-1")
    assert conflict.reason == rec.BLOCKED_REPLAY_CONFLICT
    assert conflict.direct_worker_launch_authorized is False


def test_concurrent_admission_after_proposal_blocks(rec):
    checkpoint_raw, waiting_raw, paused_raw, observed = _inputs()
    admitted = {
        "kind": "admitted_proposal",
        "request_key": "req-1",
        "evidence_digest": rec.derive_evidence_digest(
            checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
            emergency_pause_raw=paused_raw, observed=observed),
    }
    second = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed,
        prior_receipts=(admitted,), request_key="req-2")
    assert second.reason == rec.BLOCKED_CONCURRENT_ADMISSION
    assert second.direct_worker_launch_authorized is False


# Malformed evidence ---------------------------------------------------------
def test_malformed_json_fails_closed(rec):
    bad = b"{not json"
    decision = rec.evaluate_incident(
        checkpoint_raw=bad,
        original_waiting_raw=_waiting_raw(hashlib.sha256(bad).hexdigest()),
        emergency_pause_raw=_paused_raw(), observed=_observed())
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE


def test_oversize_evidence_fails_closed(rec):
    big = b"x" * (rec.MAX_BYTES + 1)
    decision = rec.evaluate_incident(
        checkpoint_raw=big,
        original_waiting_raw=_waiting_raw(hashlib.sha256(big).hexdigest()),
        emergency_pause_raw=_paused_raw(), observed=_observed())
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE


def test_checkpoint_schema_failures_are_specific(rec):
    bad = json.loads(_checkpoint_raw())
    bad["commit"] = "xyz"
    raw = json.dumps(bad).encode()
    digest = hashlib.sha256(raw).hexdigest()
    decision = rec.evaluate_incident(
        checkpoint_raw=raw,
        original_waiting_raw=_waiting_raw(digest),
        emergency_pause_raw=_paused_raw(digest), observed=_observed())
    assert decision.reason == rec.BLOCKED_CHECKPOINT_INVALID


def test_original_waiting_digest_mismatch_blocks(rec):
    checkpoint_raw = _checkpoint_raw()
    bad_waiting = json.dumps({"status": "WAITING", "safe_to_continue": True,
                              "checkpoint_sha256": "0" * 64}).encode()
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=bad_waiting,
        emergency_pause_raw=_paused_raw(), observed=_observed())
    assert decision.reason == rec.BLOCKED_CHECKPOINT_INVALID


def test_wrong_emergency_source_blocks(rec):
    checkpoint_raw = _checkpoint_raw()
    digest = hashlib.sha256(checkpoint_raw).hexdigest()
    paused = json.loads(_paused_raw(digest))
    paused["source"] = "manual"
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw,
        original_waiting_raw=_waiting_raw(digest),
        emergency_pause_raw=json.dumps(paused).encode(), observed=_observed())
    assert decision.reason == rec.BLOCKED_CHECKPOINT_INVALID
