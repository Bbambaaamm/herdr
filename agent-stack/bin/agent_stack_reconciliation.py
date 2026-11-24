"""Offline incident reconciliation evaluator for the existing Herdr supervisor.

This module is the bounded, dependency-safe evaluation half of the R1-R8
contract.  It never starts, stops, resumes or schedules anything, performs no
filesystem/network/Git/provider I/O and holds no durable state.  Callers pass
immutable bytes produced by trusted host collectors; the output is either a
``BLOCKED_*`` decision with a stable reason code or a proposal that still
requires fresh operator acceptance through the existing supervisor admission.

Integration contract (no new authority, no scheduler):

* The existing ``supervisor.py`` remains the only bootstrap/resume authority.
  Its emergency ``PAUSED`` continuation, unaccepted WAITING and original
  checkpoint bytes are immutable inputs here; this module cannot rewrite them.
* ``--resume-reviewed`` must keep rejecting emergency PAUSED.  A generic
  resume ticket is never converted into an admissible incident proposal.
* A successful proposal is not a command to launch a worker.  Exactly one
  parent supervised cycle is planned, then new evidence is required again, and
  no interactive panel may be started while that cycle runs.
* Replay of the same request with the same evidence digest is idempotent and
  produces no additional start; a conflicting replay or a concurrent admission
  for the same incident is blocked.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence

MAX_BYTES = 4 * 1024 * 1024
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
BOUND_STRING_MAX = 8192
MAX_OBSERVED_KEYS = 200
MAX_RECEIPTS = 100
MAX_COLLECTION_DEPTH = 8

# Proposal/decision codes.  These describe eligibility only.
PROPOSE_OPERATOR_REVIEW_ONLY = "PROPOSE_OPERATOR_REVIEW_ONLY"
REPLAY_IDENTICAL_NO_START = "REPLAY_IDENTICAL_NO_START"

BLOCKED_MALFORMED_EVIDENCE = "BLOCKED_MALFORMED_EVIDENCE"
BLOCKED_MISSING_OBSERVED_EVIDENCE = "BLOCKED_MISSING_OR_INVALID_OBSERVED_EVIDENCE"
BLOCKED_CHECKPOINT_INVALID = "BLOCKED_CHECKPOINT_INVALID"
BLOCKED_ORIGINAL_WAITING_INVALID = "BLOCKED_ORIGINAL_WAITING_INVALID"
BLOCKED_EMERGENCY_PAUSE_INVALID = "BLOCKED_EMERGENCY_PAUSE_INVALID"
BLOCKED_GENERIC_RESUME = "BLOCKED_GENERIC_RESUME_REJECTED"
BLOCKED_LINEAGE = "BLOCKED_LINEAGE_UNVERIFIED"
BLOCKED_HEAD_MISMATCH = "BLOCKED_HEAD_MISMATCH"
BLOCKED_EVIDENCE_CI_REVIEW = "BLOCKED_EVIDENCE_CI_REVIEW_UNVERIFIED"
BLOCKED_INTERACTIVE_PRESENT = "BLOCKED_INTERACTIVE_SESSION_PRESENT"
BLOCKED_ACTIVE_SUPERVISOR = "BLOCKED_ACTIVE_SUPERVISOR"
BLOCKED_LOCKS_HELD = "BLOCKED_LOCKS_HELD"
BLOCKED_CAPACITY_NOT_READY = "BLOCKED_CAPACITY_NOT_READY"
BLOCKED_UNKNOWN_SIDE_EFFECT = "BLOCKED_UNKNOWN_SIDE_EFFECT_NO_RETRY"
BLOCKED_CRASH_WINDOW = "BLOCKED_CRASH_WINDOW_UNRESOLVED"
BLOCKED_OPERATOR_REVIEW = "BLOCKED_OPERATOR_REVIEW_INVALID"
BLOCKED_POLICY_DRIFT = "BLOCKED_POLICY_BUDGET_FENCE_DRIFT"
BLOCKED_CONCURRENT_ADMISSION = "BLOCKED_CONCURRENT_ADMISSION"
BLOCKED_REPLAY_CONFLICT = "BLOCKED_REPLAY_CONFLICT"


class ReconciliationError(ValueError):
    """Malformed caller input; never guessed."""


def digest(raw: bytes) -> str:
    if not isinstance(raw, (bytes, bytearray)):
        raise ReconciliationError("digest_input_not_bytes")
    if len(raw) > MAX_BYTES:
        raise ReconciliationError("digest_input_too_large")
    return hashlib.sha256(bytes(raw)).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _value_depth(value: Any) -> int:
    if type(value) is dict:
        return 1 + max((_value_depth(item) for item in value.values()), default=0)
    if type(value) in (list, tuple):
        return 1 + max((_value_depth(item) for item in value), default=0)
    return 0


def validate_observed_bounds(observed: Any) -> None:
    """Pre-parse bounds for the observed collection (count/depth/bytes)."""
    if type(observed) is not dict:
        raise ReconciliationError("observed_not_object")
    if len(observed) > MAX_OBSERVED_KEYS:
        raise ReconciliationError("observed_too_many_keys")
    if any(type(key) is not str for key in observed):
        raise ReconciliationError("observed_key_not_string")
    if _value_depth(observed) > MAX_COLLECTION_DEPTH:
        raise ReconciliationError("observed_too_deep")
    try:
        encoded = canonical_json(observed)
    except (TypeError, ValueError) as exc:
        raise ReconciliationError("observed_not_serializable") from exc
    if len(encoded) > MAX_BYTES:
        raise ReconciliationError("observed_too_large")


def validate_receipt_bounds(prior_receipts: Any) -> None:
    """Pre-traversal bounds for derived receipts (count/depth/bytes)."""
    if not isinstance(prior_receipts, (list, tuple)):
        raise ReconciliationError("receipts_not_sequence")
    if len(prior_receipts) > MAX_RECEIPTS:
        raise ReconciliationError("too_many_receipts")
    for item in prior_receipts:
        if type(item) is not dict:
            raise ReconciliationError("receipt_not_object")
        if any(type(key) is not str for key in item):
            raise ReconciliationError("receipt_key_not_string")
        if _value_depth(item) > MAX_COLLECTION_DEPTH:
            raise ReconciliationError("receipt_too_deep")
    try:
        encoded = canonical_json(list(prior_receipts))
    except (TypeError, ValueError) as exc:
        raise ReconciliationError("receipts_not_serializable") from exc
    if len(encoded) > MAX_BYTES:
        raise ReconciliationError("receipts_too_large")


@dataclass(frozen=True)
class ReconciliationDecision:
    """Bounded, deterministic, redacted result."""

    decision: str
    reason: str
    checkpoint_sha256: str | None = None
    checkpoint_commit: str | None = None
    current_head: str | None = None
    proposal_digest: str | None = None
    direct_worker_launch_authorized: bool = False
    requires_fresh_operator_acceptance: bool = False
    max_parent_cycles: int | None = None
    interactive_panel_start_during_cycle: bool = False
    replay: bool = False

    def to_json(self) -> bytes:
        return canonical_json(
            {
                "decision": self.decision,
                "reason": self.reason,
                "checkpoint_sha256": self.checkpoint_sha256,
                "checkpoint_commit": self.checkpoint_commit,
                "current_head": self.current_head,
                "proposal_digest": self.proposal_digest,
                "direct_worker_launch_authorized": self.direct_worker_launch_authorized,
                "requires_fresh_operator_acceptance": self.requires_fresh_operator_acceptance,
                "max_parent_cycles": self.max_parent_cycles,
                "interactive_panel_start_during_cycle": self.interactive_panel_start_during_cycle,
                "replay": self.replay,
            }
        )


def _blocked(reason: str, **fields: Any) -> ReconciliationDecision:
    return ReconciliationDecision(decision="BLOCKED", reason=reason, **fields)


def _bounded_json(raw: bytes, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, (bytes, bytearray)):
        raise ReconciliationError(label + "_not_bytes")
    if len(raw) > MAX_BYTES:
        raise ReconciliationError(label + "_too_large")
    try:
        value = json.loads(bytes(raw))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReconciliationError(label + "_malformed") from exc
    if type(value) is not dict:
        raise ReconciliationError(label + "_not_object")
    return value


def validate_checkpoint(checkpoint: Mapping[str, Any]) -> str:
    """Validate the existing supervisor checkpoint schema; return commit."""
    for key in ("task", "worktree", "branch", "commit", "next_action"):
        if not isinstance(checkpoint.get(key), str) or not checkpoint[key].strip():
            raise ReconciliationError("checkpoint_missing_" + key)
    for key in ("changed_files", "tests", "side_processes"):
        if type(checkpoint.get(key)) is not list:
            raise ReconciliationError("checkpoint_missing_list_" + key)
    for key in ("pr", "ci", "review"):
        if key not in checkpoint:
            raise ReconciliationError("checkpoint_missing_" + key)
    commit = checkpoint["commit"]
    if not isinstance(commit, str) or not SHA40.fullmatch(commit):
        raise ReconciliationError("invalid_checkpoint_commit")
    return commit


def validate_original_waiting(waiting: Mapping[str, Any], checkpoint_sha256: str) -> None:
    """The original WAITING intent must match the checkpoint digest exactly and
    carry the same required bounded continuation fields as supervisor.py."""
    if waiting.get("status") != "WAITING" or waiting.get("safe_to_continue") is not True:
        raise ReconciliationError("original_waiting_invalid")
    if waiting.get("checkpoint_sha256") != checkpoint_sha256:
        raise ReconciliationError("original_checkpoint_digest_mismatch")
    for key in ("reason", "next_action", "progress_key"):
        value = waiting.get(key)
        if type(value) is not str or not value.strip() or len(value) > BOUND_STRING_MAX:
            raise ReconciliationError("original_waiting_" + key + "_invalid")


def validate_emergency_pause(paused: Mapping[str, Any]) -> None:
    """Emergency PAUSED must come from the supervisor emergency path.

    The real artifact contains status/safety/reason/next_action/progress_key/
    source only; no checkpoint field.  Hash binding is done through the
    separate trusted ``observed`` evidence, never by rewriting the artifact.
    """
    if paused.get("status") != "PAUSED" or paused.get("safe_to_continue") is not False:
        raise ReconciliationError("emergency_pause_invalid")
    if paused.get("source") != "supervisor_emergency_checkpoint":
        raise ReconciliationError("emergency_pause_source_invalid")
    for key in ("reason", "next_action", "progress_key"):
        value = paused.get(key)
        if type(value) is not str or not value.strip() or len(value) > BOUND_STRING_MAX:
            raise ReconciliationError("emergency_pause_" + key + "_invalid")


def validate_original_hash_binding(observed: Mapping[str, Any], checkpoint_sha256: str,
                                   waiting_sha256: str, pause_sha256: str) -> None:
    """Bind the three immutable original artifacts via separate trusted evidence.

    The real emergency PAUSED record has no checkpoint field, so binding lives
    in the collector observation instead of being invented inside artifacts.
    """
    binding = observed.get("original_artifact_sha256")
    if type(binding) is not dict:
        raise ReconciliationError("original_hash_binding_missing")
    expected = {
        "checkpoint": checkpoint_sha256,
        "waiting": waiting_sha256,
        "pause": pause_sha256,
    }
    for key, value in expected.items():
        actual = binding.get(key)
        if type(actual) is not str or not HEX64.fullmatch(actual) or actual != value:
            raise ReconciliationError("original_hash_binding_" + key + "_mismatch")


REQUIRED_OBSERVED_BOOLEANS = (
    "checkpoint_changed",
    "original_is_ancestor_of_current",
    "remote_head_matches",
    "exact_head_ci_pass",
    "exact_head_independent_review_pass",
    "review_stale",
    "review_expired",
    "supervisor_alive",
    "interactive_hermes_present",
    "locks_free",
    "capacity_ready",
    "native_durable_work_unknown",
    "native_durable_work_pending",
    "side_processes_reconciled",
    "live_side_child",
    "original_exit_zero",
    "policy_and_budget_unchanged",
    "one_shot_admission_verified",
    "fence_budget_current",
)


def validate_observed_shape(observed: Mapping[str, Any]) -> None:
    """Every known-negative fact must be present with the exact boolean type.

    Missing, ``None`` or stringly-typed facts are invalid evidence; they must
    never be interpreted as a negative answer.
    """
    for key in REQUIRED_OBSERVED_BOOLEANS:
        if type(observed.get(key)) is not bool:
            raise ReconciliationError("observed_" + key + "_not_bool")
    if type(observed.get("exact_current_pr_head")) is not str \
            or not SHA40.fullmatch(observed["exact_current_pr_head"]):
        raise ReconciliationError("observed_exact_current_pr_head_invalid")
    if type(observed.get("independent_review_head")) is not str \
            or not SHA40.fullmatch(observed["independent_review_head"]):
        raise ReconciliationError("observed_independent_review_head_invalid")
    for key in ("resume_mode", "resume_ticket_kind"):
        value = observed.get(key)
        if value is not None and type(value) is not str:
            raise ReconciliationError("observed_" + key + "_invalid")


def validate_resume_ticket(ticket: Mapping[str, Any], *, previous: str,
                           continuation_sha256: str) -> None:
    """Mirror the existing supervisor reviewed-resume binding checks.

    The ticket must name the previous job exactly and bind the unchanged
    continuation decision digest.  A generic ticket for an emergency PAUSED
    incident is rejected by the caller, never silently accepted.
    """
    if ticket.get("previous") != previous:
        raise ReconciliationError("resume_previous_mismatch")
    if ticket.get("decision_sha256") != continuation_sha256:
        raise ReconciliationError("resume_decision_digest_mismatch")


def validate_operator_review(operator: Any, current_head: str,
                             observed: Mapping[str, Any]) -> bool:
    """Return True only for a present, typed, head-bound, unexpired review."""
    if type(operator) is not dict:
        raise ReconciliationError("operator_review_not_object")
    if type(operator.get("accepted")) is not bool or operator["accepted"] is not True:
        raise ReconciliationError("operator_review_not_accepted")
    if type(operator.get("head")) is not str or operator["head"] != current_head:
        raise ReconciliationError("operator_review_head_mismatch")
    expires = operator.get("expires_at_epoch")
    if type(expires) is not int or isinstance(expires, bool) or expires < 0:
        raise ReconciliationError("operator_review_expiry_invalid")
    now = observed.get("now_epoch")
    if type(now) is not int or isinstance(now, bool):
        raise ReconciliationError("operator_review_now_invalid")
    return expires > now


def validate_claim_receipt(receipt: Any, *, checkpoint_sha256: str,
                           request_key: str | None, incident_id: str | None) -> None:
    """A crash-window receipt must be a trusted released/no-start proof.

    It has to bind the exact checkpoint raw digest, the incident id and the
    reconciliation request key, and carry an explicit verified no-start flag.
    An arbitrary 64-hex placeholder or ``state=consumed`` alone proves nothing.
    """
    if type(receipt) is not dict:
        raise ReconciliationError("claim_receipt_not_object")
    claim_id = receipt.get("claim_id")
    if type(claim_id) is not str or not claim_id.strip() or len(claim_id) > BOUND_STRING_MAX:
        raise ReconciliationError("claim_receipt_id_invalid")
    if receipt.get("checkpoint_sha256") != checkpoint_sha256:
        raise ReconciliationError("claim_receipt_checkpoint_mismatch")
    if receipt.get("state") not in ("released", "consumed"):
        raise ReconciliationError("claim_receipt_state_invalid")
    if type(receipt.get("receipt_sha256")) is not str \
            or not HEX64.fullmatch(receipt["receipt_sha256"]):
        raise ReconciliationError("claim_receipt_hash_invalid")
    if type(request_key) is not str or not request_key.strip():
        raise ReconciliationError("claim_receipt_request_unbound")
    if receipt.get("request_key") != request_key:
        raise ReconciliationError("claim_receipt_request_mismatch")
    if type(incident_id) is not str or not incident_id.strip():
        raise ReconciliationError("claim_receipt_incident_unbound")
    if receipt.get("incident_id") != incident_id:
        raise ReconciliationError("claim_receipt_incident_mismatch")
    if receipt.get("no_start_verified") is not True:
        raise ReconciliationError("claim_receipt_no_start_unverified")


def derive_evidence_digest(
    *,
    checkpoint_raw: bytes,
    original_waiting_raw: bytes | None,
    emergency_pause_raw: bytes,
    observed: Mapping[str, Any],
    crash_window: str | None = None,
) -> str:
    """Canonical evidence digest used for idempotent replay receipts."""
    validate_observed_bounds(observed)
    return digest(canonical_json({
        "checkpoint_sha256": digest(checkpoint_raw),
        "checkpoint_commit": validate_checkpoint(_bounded_json(checkpoint_raw, "checkpoint")),
        "current_head": observed.get("exact_current_pr_head"),
        "waiting_sha256": digest(original_waiting_raw) if original_waiting_raw is not None else None,
        "pause_sha256": digest(emergency_pause_raw),
        "observed": {key: observed.get(key) for key in sorted(observed)},
        "crash_window": crash_window,
    }))


def evaluate_incident(
    *,
    checkpoint_raw: bytes,
    original_waiting_raw: bytes | None,
    emergency_pause_raw: bytes,
    observed: Mapping[str, Any],
    prior_receipts: Sequence[Mapping[str, Any]] = (),
    request_key: str | None = None,
    crash_window: str | None = None,
) -> ReconciliationDecision:
    """Return a proposal or a fail-closed decision; never authorize a start.

    ``observed`` is supplied by trusted host collectors and must contain the
    exact-head, lineage, CI/review, process, lock, capacity and side-effect
    facts listed below.  Missing facts are failures, not defaults.
    """
    try:
        validate_observed_bounds(observed)
    except ReconciliationError as exc:
        code = (BLOCKED_MISSING_OBSERVED_EVIDENCE
                if exc.args and exc.args[0] == "observed_not_object"
                else BLOCKED_MALFORMED_EVIDENCE)
        return _blocked(code)
    try:
        validate_receipt_bounds(prior_receipts)
    except ReconciliationError:
        return _blocked(BLOCKED_MALFORMED_EVIDENCE)
    if original_waiting_raw is None:
        return _blocked(BLOCKED_ORIGINAL_WAITING_INVALID)
    try:
        checkpoint = _bounded_json(checkpoint_raw, "checkpoint")
        paused = _bounded_json(emergency_pause_raw, "emergency_pause")
        waiting = _bounded_json(original_waiting_raw, "original_waiting")
    except ReconciliationError:
        return _blocked(BLOCKED_MALFORMED_EVIDENCE)

    checkpoint_sha256 = digest(checkpoint_raw)
    waiting_sha256 = digest(original_waiting_raw)
    pause_sha256 = digest(emergency_pause_raw)
    try:
        checkpoint_commit = validate_checkpoint(checkpoint)
        validate_emergency_pause(paused)
        validate_original_waiting(waiting, checkpoint_sha256)
    except ReconciliationError:
        return _blocked(BLOCKED_CHECKPOINT_INVALID, checkpoint_sha256=checkpoint_sha256)
    try:
        validate_observed_shape(observed)
        validate_original_hash_binding(
            observed, checkpoint_sha256, waiting_sha256, pause_sha256)
    except ReconciliationError:
        return _blocked(BLOCKED_MISSING_OBSERVED_EVIDENCE, checkpoint_sha256=checkpoint_sha256)

    # R1: generic resume is never an admissible reconciliation path.
    resume_mode = observed.get("resume_mode")
    resume_kind = observed.get("resume_ticket_kind")
    if resume_mode in ("generic", "resume-reviewed") or resume_kind == "generic":
        return _blocked(BLOCKED_GENERIC_RESUME, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit)

    # R2: lineage and exact head must be verified; changed head blocks.
    current_head = observed.get("exact_current_pr_head")
    if not isinstance(current_head, str) or not SHA40.fullmatch(current_head):
        return _blocked(BLOCKED_HEAD_MISMATCH, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit)
    if observed.get("checkpoint_changed") is True:
        return _blocked(BLOCKED_LINEAGE, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)
    if observed.get("original_is_ancestor_of_current") is not True:
        return _blocked(BLOCKED_LINEAGE, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)
    if observed.get("remote_head_matches") is not True:
        return _blocked(BLOCKED_HEAD_MISMATCH, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    # R3: exact-head CI and independent review proofs, no stale review.
    if observed.get("exact_head_ci_pass") is not True:
        return _blocked(BLOCKED_EVIDENCE_CI_REVIEW, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)
    if observed.get("exact_head_independent_review_pass") is not True:
        return _blocked(BLOCKED_EVIDENCE_CI_REVIEW, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)
    review_head = observed.get("independent_review_head")
    if review_head != current_head or observed.get("review_stale") is True \
            or observed.get("review_expired") is True:
        return _blocked(BLOCKED_EVIDENCE_CI_REVIEW, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    # Existing supervisor bootstrap still alive -> fail closed.
    if observed.get("supervisor_alive") is True:
        return _blocked(BLOCKED_ACTIVE_SUPERVISOR, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    # R4: an interactive Hermes session must be released before any proposal.
    if observed.get("interactive_hermes_present") is True:
        return _blocked(BLOCKED_INTERACTIVE_PRESENT, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    if observed.get("locks_free") is not True:
        return _blocked(BLOCKED_LOCKS_HELD, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)
    if observed.get("capacity_ready") is not True:
        return _blocked(BLOCKED_CAPACITY_NOT_READY, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    # R5/R6: uncertain side effects never retry; crash windows need resolution.
    if observed.get("native_durable_work_unknown") is True \
            or observed.get("native_durable_work_pending") is True:
        return _blocked(BLOCKED_UNKNOWN_SIDE_EFFECT, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)
    if observed.get("side_processes_reconciled") is not True \
            or observed.get("live_side_child") is True \
            or observed.get("original_exit_zero") is not True:
        return _blocked(BLOCKED_UNKNOWN_SIDE_EFFECT, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)
    if crash_window is not None:
        if crash_window == "after_start_before_receipt":
            return _blocked(BLOCKED_UNKNOWN_SIDE_EFFECT, checkpoint_sha256=checkpoint_sha256,
                            checkpoint_commit=checkpoint_commit, current_head=current_head)
        if crash_window == "after_claim_before_start":
            try:
                validate_claim_receipt(
                    observed.get("claim_receipt"),
                    checkpoint_sha256=checkpoint_sha256,
                    request_key=request_key,
                    incident_id=observed.get("incident_id"))
            except ReconciliationError:
                return _blocked(BLOCKED_CRASH_WINDOW, checkpoint_sha256=checkpoint_sha256,
                                checkpoint_commit=checkpoint_commit, current_head=current_head)
        elif crash_window != "before_claim":
            return _blocked(BLOCKED_MALFORMED_EVIDENCE, checkpoint_sha256=checkpoint_sha256,
                            checkpoint_commit=checkpoint_commit, current_head=current_head)

    # R7: operator review must be present, fresh and bound to the current head.
    try:
        operator_ok = validate_operator_review(
            observed.get("operator_review"), current_head, observed)
    except ReconciliationError:
        operator_ok = False
    if operator_ok is not True:
        return _blocked(BLOCKED_OPERATOR_REVIEW, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    # R7: policy/budget/fence drift denies; no fallback model.
    if observed.get("policy_and_budget_unchanged") is not True \
            or observed.get("one_shot_admission_verified") is not True \
            or observed.get("fence_budget_current") is not True:
        return _blocked(BLOCKED_POLICY_DRIFT, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    # Replay/concurrency control on the derived receipt, not on durable state.
    try:
        evidence_digest = derive_evidence_digest(
            checkpoint_raw=checkpoint_raw,
            original_waiting_raw=original_waiting_raw,
            emergency_pause_raw=emergency_pause_raw,
            observed=observed,
            crash_window=crash_window,
        )
    except ReconciliationError:
        return _blocked(BLOCKED_MALFORMED_EVIDENCE, checkpoint_sha256=checkpoint_sha256)
    if not isinstance(prior_receipts, (list, tuple)):
        return _blocked(BLOCKED_MALFORMED_EVIDENCE, checkpoint_sha256=checkpoint_sha256)
    proposals = []
    for item in prior_receipts:
        if not isinstance(item, Mapping):
            return _blocked(BLOCKED_MALFORMED_EVIDENCE, checkpoint_sha256=checkpoint_sha256)
        if type(item.get("kind")) is not str:
            return _blocked(BLOCKED_MALFORMED_EVIDENCE, checkpoint_sha256=checkpoint_sha256)
        if item.get("request_key") is not None and type(item.get("request_key")) is not str:
            return _blocked(BLOCKED_MALFORMED_EVIDENCE, checkpoint_sha256=checkpoint_sha256)
        if type(item.get("evidence_digest")) is not str \
                or not re.fullmatch(r"[0-9a-f]{64}", item["evidence_digest"]):
            return _blocked(BLOCKED_MALFORMED_EVIDENCE, checkpoint_sha256=checkpoint_sha256)
        if item.get("kind") == "admitted_proposal":
            proposals.append(item)
    for item in proposals:
        if request_key is not None and item.get("request_key") == request_key:
            if item.get("evidence_digest") == evidence_digest:
                return ReconciliationDecision(
                    decision=REPLAY_IDENTICAL_NO_START, reason="replay_identical",
                    checkpoint_sha256=checkpoint_sha256, checkpoint_commit=checkpoint_commit,
                    current_head=current_head, proposal_digest=item.get("proposal_digest"),
                    direct_worker_launch_authorized=False,
                    requires_fresh_operator_acceptance=False,
                    max_parent_cycles=None, replay=True)
            return _blocked(BLOCKED_REPLAY_CONFLICT, checkpoint_sha256=checkpoint_sha256,
                            checkpoint_commit=checkpoint_commit, current_head=current_head)
    if proposals:
        return _blocked(BLOCKED_CONCURRENT_ADMISSION, checkpoint_sha256=checkpoint_sha256,
                        checkpoint_commit=checkpoint_commit, current_head=current_head)

    proposal = {
        "kind": "admitted_proposal",
        "request_key": request_key,
        "evidence_digest": evidence_digest,
        "checkpoint_sha256": checkpoint_sha256,
        "checkpoint_commit": checkpoint_commit,
        "current_head": current_head,
        "original_waiting_sha256": digest(original_waiting_raw) if original_waiting_raw is not None else None,
        "emergency_pause_sha256": digest(emergency_pause_raw),
        "max_parent_cycles": 1,
        "requires_new_evidence_after": True,
        "interactive_panel_start_during_cycle": False,
        "direct_worker_launch_authorized": False,
        "requires_fresh_operator_acceptance": True,
    }
    proposal_digest = digest(canonical_json(proposal))
    return ReconciliationDecision(
        decision=PROPOSE_OPERATOR_REVIEW_ONLY, reason="eligible_for_operator_review",
        checkpoint_sha256=checkpoint_sha256, checkpoint_commit=checkpoint_commit,
        current_head=current_head, proposal_digest=proposal_digest,
        direct_worker_launch_authorized=False,
        requires_fresh_operator_acceptance=True,
        max_parent_cycles=1, interactive_panel_start_during_cycle=False, replay=False)
