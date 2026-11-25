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


def _paused_raw(_legacy_checkpoint_sha: str | None = None) -> bytes:
    # Mirrors the real supervisor emergency-checkpoint.json: no checkpoint hash.
    # The legacy argument is accepted and ignored so fixtures never rewrite the
    # original artifact schema.
    paused = {
        "status": "PAUSED",
        "safe_to_continue": False,
        "reason": "emergency stop",
        "next_action": "reconcile before explicit restart",
        "progress_key": "supervisor-paused:emergency",
        "source": "supervisor_emergency_checkpoint",
    }
    return json.dumps(paused, sort_keys=True).encode("utf-8")


def _default_binding():
    checkpoint_raw = _checkpoint_raw()
    waiting_raw = _waiting_raw(hashlib.sha256(checkpoint_raw).hexdigest())
    paused_raw = _paused_raw()
    return {
        "checkpoint": hashlib.sha256(checkpoint_raw).hexdigest(),
        "waiting": hashlib.sha256(waiting_raw).hexdigest(),
        "pause": hashlib.sha256(paused_raw).hexdigest(),
    }


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
        "original_artifact_sha256": _default_binding(),
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


@pytest.mark.parametrize("receipt_hash", ["c" * 64, "d" * 64])
def test_r6_crash_after_claim_before_start_is_always_blocked(rec, receipt_hash):
    receipt = {
        "claim_id": "claim-1",
        "checkpoint_sha256": hashlib.sha256(_checkpoint_raw()).hexdigest(),
        "state": "consumed",
        "receipt_sha256": receipt_hash,
        "request_key": "req-crash-1",
        "incident_id": "incident-53",
        "no_start_verified": True,
    }
    decision = _evaluate(
        rec, crash_window="after_claim_before_start",
        request_key="req-crash-1",
        observed=_observed(incident_id="incident-53", claim_receipt=receipt))
    assert decision.decision == "BLOCKED"
    assert decision.reason == rec.BLOCKED_CRASH_WINDOW
    assert decision.direct_worker_launch_authorized is False


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


def test_emergency_pause_does_not_require_invented_checkpoint_field(rec):
    checkpoint_raw = _checkpoint_raw()
    digest = hashlib.sha256(checkpoint_raw).hexdigest()
    paused = json.loads(_paused_raw())
    assert "checkpoint_sha256" not in paused
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw,
        original_waiting_raw=_waiting_raw(digest),
        emergency_pause_raw=_paused_raw(), observed=_observed())
    assert decision.decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY


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


def test_review_invalid_request_keys_are_blocked(rec):
    cyclic = {}
    cyclic["self"] = cyclic
    for bad_key in (object(), "k" * 8193, {"a": 1}, cyclic):
        decision = _evaluate(rec, request_key=bad_key)
        assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE
        assert decision.proposal_digest is None

    bad_receipt = {"kind": "admitted_proposal",
                   "request_key": "r" * 8193,
                   "evidence_digest": "0" * 64,
                   "proposal_digest": "0" * 64}
    decision = _evaluate(rec, prior_receipts=(bad_receipt,), request_key="req-1")
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE


@pytest.mark.parametrize("blank_key", ["", " ", "\t", "\n", "\u00a0\u2003",
                                       " \t\r\n "], ids=["empty", "space", "tab",
                                                        "newline", "unicode-space",
                                                        "mixed"])
def test_review_blank_request_keys_block_at_entry_and_receipt(rec, blank_key):
    entry = _evaluate(rec, request_key=blank_key)
    assert entry.reason == rec.BLOCKED_MALFORMED_EVIDENCE
    assert entry.proposal_digest is None

    receipt = {"kind": "admitted_proposal", "request_key": blank_key,
               "evidence_digest": "0" * 64, "proposal_digest": "0" * 64}
    replay = _evaluate(rec, prior_receipts=(receipt,), request_key="req-1")
    assert replay.reason == rec.BLOCKED_MALFORMED_EVIDENCE
    assert replay.proposal_digest is None


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


def _parts(checkpoint_raw, waiting_raw, paused_raw, decision):
    return dict(
        checkpoint_sha256=decision.checkpoint_sha256,
        checkpoint_commit=decision.checkpoint_commit,
        current_head=decision.current_head,
        original_waiting_sha256=hashlib.sha256(waiting_raw).hexdigest(),
        emergency_pause_sha256=hashlib.sha256(paused_raw).hexdigest())


def _receipt(rec, parts, request_key, evidence_digest):
    return {"kind": "admitted_proposal", "request_key": request_key,
            "evidence_digest": evidence_digest,
            "proposal_digest": rec.derive_proposal_digest(
                request_key=request_key, evidence_digest=evidence_digest, **parts)}


def test_replay_same_request_and_evidence_is_idempotent(rec):
    checkpoint_raw, waiting_raw, paused_raw, observed = _inputs()
    proposal = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed, request_key="req-1")
    assert proposal.decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY
    evidence_digest = rec.derive_evidence_digest(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed)
    receipt = _receipt(rec, _parts(checkpoint_raw, waiting_raw, paused_raw, proposal),
                       "req-1", evidence_digest)
    replay = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed,
        prior_receipts=(receipt,), request_key="req-1")
    assert replay.decision == rec.REPLAY_IDENTICAL_NO_START
    assert replay.replay is True
    assert replay.proposal_digest == proposal.proposal_digest
    assert replay.direct_worker_launch_authorized is False


def test_replay_same_request_with_changed_evidence_conflicts(rec):
    checkpoint_raw, waiting_raw, paused_raw, _ = _inputs()
    changed = _observed(operator_note="changed-after-receipt")
    baseline = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=_observed(), request_key="req-1")
    parts = _parts(checkpoint_raw, waiting_raw, paused_raw, baseline)
    receipt = _receipt(rec, parts, "req-1", "0" * 64)
    conflict = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=changed,
        prior_receipts=(receipt,), request_key="req-1")
    assert conflict.reason == rec.BLOCKED_REPLAY_CONFLICT
    assert conflict.direct_worker_launch_authorized is False


@pytest.mark.parametrize("order", ["matching_first", "conflicting_first"])
def test_review_conflicting_duplicate_receipts_block_in_any_order(rec, order):
    checkpoint_raw, waiting_raw, paused_raw, observed = _inputs()
    baseline = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed, request_key="req-1")
    parts = _parts(checkpoint_raw, waiting_raw, paused_raw, baseline)
    matching_digest = rec.derive_evidence_digest(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed)
    matching = _receipt(rec, parts, "req-1", matching_digest)
    conflicting = _receipt(rec, parts, "req-1", "1" * 64)
    receipts = (matching, conflicting) if order == "matching_first" \
        else (conflicting, matching)
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed,
        prior_receipts=receipts, request_key="req-1")
    assert decision.reason == rec.BLOCKED_REPLAY_CONFLICT
    assert decision.proposal_digest is None


@pytest.mark.parametrize("fake_digest", ["0" * 64, "f" * 64])
def test_review_arbitrary_valid_length_receipt_digest_never_replays(rec, fake_digest):
    checkpoint_raw, waiting_raw, paused_raw, observed = _inputs()
    baseline = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed, request_key="req-1")
    parts = _parts(checkpoint_raw, waiting_raw, paused_raw, baseline)
    evidence_digest = rec.derive_evidence_digest(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed)
    receipt = {"kind": "admitted_proposal", "request_key": "req-1",
               "evidence_digest": evidence_digest,
               "proposal_digest": fake_digest}
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed,
        prior_receipts=(receipt,), request_key="req-1")
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE
    assert decision.proposal_digest is None


def test_concurrent_admission_after_proposal_blocks(rec):
    checkpoint_raw, waiting_raw, paused_raw, observed = _inputs()
    baseline = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed, request_key="req-2")
    parts = _parts(checkpoint_raw, waiting_raw, paused_raw, baseline)
    admitted = _receipt(rec, parts, "req-1", rec.derive_evidence_digest(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed))
    second = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed,
        prior_receipts=(admitted,), request_key="req-2")
    assert second.reason == rec.BLOCKED_CONCURRENT_ADMISSION
    assert second.direct_worker_launch_authorized is False


def test_review_injected_prior_receipt_digest_is_blocked(rec):
    receipt = {"kind": "admitted_proposal", "request_key": "req-1",
               "evidence_digest": "a" * 64,
               "proposal_digest": {"injected": 1}}
    decision = rec.evaluate_incident(
        checkpoint_raw=_checkpoint_raw(),
        original_waiting_raw=_waiting_raw(
            hashlib.sha256(_checkpoint_raw()).hexdigest()),
        emergency_pause_raw=_paused_raw(), observed=_observed(),
        prior_receipts=(receipt,), request_key="req-1")
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE
    assert decision.proposal_digest is None


def test_review_request_key_none_replays_only_unbound_same_binding(rec):
    checkpoint_raw = _checkpoint_raw()
    waiting_raw = _waiting_raw(hashlib.sha256(checkpoint_raw).hexdigest())
    paused_raw = _paused_raw()
    observed = _observed()
    common = dict(checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
                  emergency_pause_raw=paused_raw, observed=observed)
    proposal = rec.evaluate_incident(**common, request_key=None)
    assert proposal.decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY
    evidence_digest = rec.derive_evidence_digest(**common)
    parts = _parts(checkpoint_raw, waiting_raw, paused_raw, proposal)
    unbound = _receipt(rec, parts, None, evidence_digest)
    replay = rec.evaluate_incident(**common, prior_receipts=(unbound,),
                                   request_key=None)
    assert replay.decision == rec.REPLAY_IDENTICAL_NO_START
    assert isinstance(replay.proposal_digest, str) and len(replay.proposal_digest) == 64

    bound = _receipt(rec, parts, "req-1", evidence_digest)
    cross = rec.evaluate_incident(**common, prior_receipts=(bound,),
                                  request_key=None)
    assert cross.reason == rec.BLOCKED_CONCURRENT_ADMISSION


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


# Review regressions (offline-reconcile-independent-review-1c1459c) -----------
def test_review_real_paused_schema_is_not_rewritten_and_binds_separately(rec):
    paused = json.loads(_paused_raw())
    assert "checkpoint_sha256" not in paused

    checkpoint_raw = _checkpoint_raw()
    checkpoint_sha = hashlib.sha256(checkpoint_raw).hexdigest()
    waiting_raw = _waiting_raw(checkpoint_sha)
    paused_raw = _paused_raw()
    observed = _observed(original_artifact_sha256={
        "checkpoint": checkpoint_sha,
        "waiting": hashlib.sha256(waiting_raw).hexdigest(),
        "pause": hashlib.sha256(paused_raw).hexdigest(),
    })
    assert rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=observed
    ).decision == rec.PROPOSE_OPERATOR_REVIEW_ONLY

    binding = dict(observed["original_artifact_sha256"])
    binding["pause"] = "0" * 64
    assert rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw,
        observed=_observed(original_artifact_sha256=binding)).reason \
        == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE

    without = {k: v for k, v in observed.items() if k != "original_artifact_sha256"}
    assert rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw, original_waiting_raw=waiting_raw,
        emergency_pause_raw=paused_raw, observed=without).reason \
        == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE


@pytest.mark.parametrize("mutate", [
    lambda w: w.pop("reason"),
    lambda w: w.update(reason="   "),
    lambda w: w.update(next_action=""),
    lambda w: w.pop("progress_key"),
    lambda w: w.update(reason="r" * 8193),
])
def test_review_waiting_required_fields_fail_closed(rec, mutate):
    checkpoint_raw = _checkpoint_raw()
    digest = hashlib.sha256(checkpoint_raw).hexdigest()
    waiting = json.loads(_waiting_raw(digest))
    mutate(waiting)
    decision = rec.evaluate_incident(
        checkpoint_raw=checkpoint_raw,
        original_waiting_raw=json.dumps(waiting).encode(),
        emergency_pause_raw=_paused_raw(), observed=_observed())
    assert decision.reason == rec.BLOCKED_CHECKPOINT_INVALID


@pytest.mark.parametrize("receipt", [
    {"claim_id": "claim-1", "state": "consumed", "receipt_sha256": "c" * 64},
    {"claim_id": "claim-1",
     "checkpoint_sha256": hashlib.sha256(_checkpoint_raw()).hexdigest(),
     "state": "consumed", "receipt_sha256": "c" * 64,
     "request_key": "req-crash-2", "incident_id": "incident-53"},
    {"claim_id": "claim-1",
     "checkpoint_sha256": hashlib.sha256(_checkpoint_raw()).hexdigest(),
     "state": "consumed", "receipt_sha256": "c" * 64,
     "request_key": "req-crash-2", "incident_id": "other-incident",
     "no_start_verified": True},
    {"claim_id": "claim-1",
     "checkpoint_sha256": hashlib.sha256(_checkpoint_raw()).hexdigest(),
     "state": "consumed", "receipt_sha256": "c" * 64,
     "request_key": "req-crash-2", "incident_id": "incident-53",
     "no_start_verified": False},
])
def test_review_placeholder_claim_receipt_does_not_prove_no_start(rec, receipt):
    decision = _evaluate(
        rec, crash_window="after_claim_before_start",
        request_key="req-crash-2",
        observed=_observed(incident_id="incident-53", claim_receipt=receipt))
    assert decision.reason == rec.BLOCKED_CRASH_WINDOW
    assert decision.direct_worker_launch_authorized is False


@pytest.mark.parametrize("bad", [None, ["fact"], "text", 7])
def test_review_non_mapping_observed_returns_blocked(rec, bad):
    decision = rec.evaluate_incident(
        checkpoint_raw=_checkpoint_raw(),
        original_waiting_raw=_waiting_raw(hashlib.sha256(_checkpoint_raw()).hexdigest()),
        emergency_pause_raw=_paused_raw(), observed=bad)
    assert decision.decision == "BLOCKED"
    assert decision.reason == rec.BLOCKED_MISSING_OBSERVED_EVIDENCE


def test_review_observed_and_receipt_bounds_are_pre_serialization(rec):
    many_keys = {f"k{index}": True for index in range(rec.MAX_OBSERVED_KEYS + 1)}
    assert _evaluate(rec, observed=many_keys).reason == rec.BLOCKED_MALFORMED_EVIDENCE

    deep = "leaf"
    for _ in range(rec.MAX_COLLECTION_DEPTH + 1):
        deep = {"v": deep}
    assert _evaluate(rec, observed={"deep": deep}).reason == rec.BLOCKED_MALFORMED_EVIDENCE

    huge_value = {"blob": "x" * (rec.MAX_BYTES + 1)}
    assert _evaluate(rec, observed=huge_value).reason == rec.BLOCKED_MALFORMED_EVIDENCE

    too_many = tuple({"kind": "other", "evidence_digest": "0" * 64}
                     for _ in range(rec.MAX_RECEIPTS + 1))
    assert _evaluate(rec, prior_receipts=too_many).reason == rec.BLOCKED_MALFORMED_EVIDENCE

    huge_receipt = ({"kind": "other", "blob": "y" * (rec.MAX_BYTES + 1)},)
    assert _evaluate(rec, prior_receipts=huge_receipt).reason == rec.BLOCKED_MALFORMED_EVIDENCE

    assert _evaluate(rec, prior_receipts=(["not", "a", "mapping"],)).reason \
        == rec.BLOCKED_MALFORMED_EVIDENCE


def test_review_deep_and_cyclic_inputs_are_blocked_not_recursion_errors(rec):
    deep = "leaf"
    for _ in range(1200):
        deep = {"v": deep}
    decision = _evaluate(rec, observed={"deep": deep})
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE

    deep_receipts = ({"kind": "other", "nested": deep},)
    assert _evaluate(rec, prior_receipts=deep_receipts).reason \
        == rec.BLOCKED_MALFORMED_EVIDENCE

    cyclic = {}
    cyclic["self"] = cyclic
    assert _evaluate(rec, observed=cyclic).reason == rec.BLOCKED_MALFORMED_EVIDENCE

    cyclic_receipt = {"kind": "other"}
    cyclic_receipt["self"] = cyclic_receipt
    assert _evaluate(rec, prior_receipts=(cyclic_receipt,)).reason \
        == rec.BLOCKED_MALFORMED_EVIDENCE

    assert _evaluate(rec, observed={"blob": object()}).reason \
        == rec.BLOCKED_MALFORMED_EVIDENCE

    with pytest.raises(rec.ReconciliationError):
        rec.derive_evidence_digest(
            checkpoint_raw=_checkpoint_raw(),
            original_waiting_raw=_waiting_raw(
                hashlib.sha256(_checkpoint_raw()).hexdigest()),
            emergency_pause_raw=_paused_raw(),
            observed={"deep": deep})


def test_review_shared_dag_subtree_uses_unfolded_depth(rec):
    shared = {"x": {"y": {"z": 1}}}
    long_chain = shared
    for _ in range(6):
        long_chain = {"a": long_chain}
    dag_observed = _observed(long=long_chain, short=shared)
    decision = _evaluate(rec, observed=dag_observed)
    assert decision.reason == rec.BLOCKED_MALFORMED_EVIDENCE
    assert decision.direct_worker_launch_authorized is False

    dag_receipts = ({"kind": "other", "long": long_chain, "short": shared},)
    assert _evaluate(rec, prior_receipts=dag_receipts).reason \
        == rec.BLOCKED_MALFORMED_EVIDENCE
