"""Deterministic fixtures for the defect-observation admission bridge (#100/#53).

Proposal-only: every ADMIT result carries ``authorizes_execution=False`` and no
test dispatches work, writes the budget ledger or grants a privilege.
"""
from __future__ import annotations

import pytest

from herdr.admission import AuditLog
from herdr.defect_admission import (
    DecisionJournal,
    DefectCategory,
    DefectContext,
    DefectDecision,
    DefectDisposition,
    DefectError,
    DefectObservation,
    DefectSource,
    admission_summary,
    approval_is_stale,
    decide_defect_admission,
)

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


def observation(**overrides):
    payload = {
        "source": DefectSource.CI_CHECK,
        "category": DefectCategory.VALIDATION_FAILURE,
        "repository": "Bbambaaamm/herdr",
        "commit_sha": SHA_A,
        "ref": "feat/example",
        "subject": ("test_example", "test_it"),
        "observed_at": 1_000,
        "workflow": "Herdr contract",
        "check_identity": "herdr-contract",
        "check_run_id": "run-1",
        "event_revision": "rev-1",
        "evidence_sha256": ("d" * 64,),
    }
    payload.update(overrides)
    return DefectObservation(**payload)


def context(**overrides):
    payload = {
        "repository_authorized": True,
        "already_resolved": False,
        "active_repairs": 0,
        "repeat_count": 0,
        "budget_state": "OK",
        "credentials_state": "OK",
        "capacity_ok": True,
        "max_repairs": 3,
    }
    payload.update(overrides)
    return DefectContext(**payload)


# --- §8 A: a new CI regression produces exactly one proposal ---------------- #


def test_a_new_ci_regression_is_admitted_as_a_proposal():
    decision = decide_defect_admission(observation(), context())
    assert decision.disposition is DefectDisposition.ADMIT
    assert decision.task_class == "validation_failure"
    assert decision.proposal["graph"] == {
        "node_count": 1, "max_depth": 1, "max_fanout": 0, "root_task": "defect-repair",
    }
    assert decision.proposal["paper_only"] is True
    assert decision.proposal["authorizes_execution"] is False
    assert decision.proposal["task_proposals_submitted"] == 0
    assert decision.proposal["budget_operations"] == 0


# --- §8 B: a duplicate CI event creates no second record -------------------- #


def test_b_duplicate_ci_event_creates_no_duplicate_record(tmp_path):
    journal = DecisionJournal(AuditLog(tmp_path / "audit.jsonl"))
    decision = decide_defect_admission(observation(), context())
    first, created = journal.record(decision)
    assert created is True
    second, created_again = journal.record(decision)
    assert created_again is False
    assert second == first
    assert len(journal._log.replay()) == 1


# --- §8 C: a known resolved defect is a no-op ------------------------------ #


def test_c_known_resolved_defect_is_no_action():
    decision = decide_defect_admission(observation(), context(already_resolved=True))
    assert decision.disposition is DefectDisposition.NO_ACTION
    assert decision.proposal == {}


# --- §8 D: a reopened failure on a new SHA stays detectable ----------------- #


def test_d_reopened_failure_on_new_sha_is_a_new_record(tmp_path):
    journal = DecisionJournal(AuditLog(tmp_path / "audit.jsonl"))
    first = decide_defect_admission(observation(), context())
    second = decide_defect_admission(observation(commit_sha=SHA_B), context())
    assert first.fingerprint != second.fingerprint
    assert journal.record(first)[1] is True
    assert journal.record(second)[1] is True
    assert len(journal._log.replay()) == 2


# --- §8 E: a review finding follows the same workflow ---------------------- #


def test_e_review_finding_is_admitted_through_the_same_workflow():
    decision = decide_defect_admission(
        observation(source=DefectSource.REVIEW_COMMENT,
                    category=DefectCategory.REVIEW_FINDING),
        context(),
    )
    assert decision.disposition is DefectDisposition.ADMIT
    assert decision.task_class == "review_finding"
    assert decision.proposal["authorizes_execution"] is False


# --- §8 F/G: crash recovery and reconciliation ----------------------------- #


def test_f_decision_survives_a_journal_reopen(tmp_path):
    """A restarted consumer reconstructs the same admitted decision."""
    log = AuditLog(tmp_path / "audit.jsonl")
    decision = decide_defect_admission(observation(), context())
    DecisionJournal(log).record(decision)

    reopened = DecisionJournal(AuditLog(tmp_path / "audit.jsonl"))
    prior = reopened.prior(decision)
    assert prior is not None
    assert prior["fingerprint"] == decision.fingerprint
    assert reopened.record(decision)[1] is False


def test_g_unreconciled_delivery_is_unknown_not_a_second_economic_attempt():
    decision = decide_defect_admission(observation(), context(credentials_state="UNKNOWN"))
    assert decision.disposition is DefectDisposition.UNKNOWN
    assert decision.proposal == {}


# --- §8 H: provider 429 handling is owned by Router v5 (#236) -------------- #


def test_h_provider_rate_limit_is_not_a_defect_category():
    """No defect source may claim a provider 429; that is routing, not repair."""
    with pytest.raises(DefectError):
        observation(category=DefectCategory.RUNTIME_ERROR)


# --- §8 I: budget exhausted stops dispatch --------------------------------- #


def test_i_budget_exhausted_blocks_dispatch():
    decision = decide_defect_admission(observation(), context(budget_state="EXHAUSTED"))
    assert decision.disposition is DefectDisposition.BLOCKED
    assert "budget_exhausted" in decision.reasons


def test_i_budget_unknown_is_unknown():
    decision = decide_defect_admission(observation(), context(budget_state="UNKNOWN"))
    assert decision.disposition is DefectDisposition.UNKNOWN


# --- §8 J: missing credentials gate ---------------------------------------- #


def test_j_missing_credentials_gate():
    decision = decide_defect_admission(observation(), context(credentials_state="MISSING"))
    assert decision.disposition is DefectDisposition.CREDENTIAL_GATE


# --- §8 K: unauthorized repository is denied ------------------------------- #


def test_k_unauthorized_repository_is_denied():
    decision = decide_defect_admission(observation(), context(repository_authorized=False))
    assert decision.disposition is DefectDisposition.DENY
    assert "repository_not_authorized" in decision.reasons


# --- §8 L: untrusted text is data, never a grant --------------------------- #


def test_l_untrusted_text_is_denied():
    decision = decide_defect_admission(
        observation(source=DefectSource.UNTRUSTED_TEXT,
                    category=DefectCategory.UNCLASSIFIED),
        context(repository_authorized=True),
    )
    assert decision.disposition is DefectDisposition.DENY
    assert "untrusted_source" in decision.reasons


# --- §8 M: repeated failure hits the bounded stop --------------------------- #


def test_m_repeated_failure_blocks_further_repair():
    decision = decide_defect_admission(observation(), context(repeat_count=3))
    assert decision.disposition is DefectDisposition.BLOCKED
    assert "no_progress_ceiling" in decision.reasons


def test_m_active_repair_suppresses_a_second_proposal():
    decision = decide_defect_admission(observation(), context(active_repairs=1))
    assert decision.disposition is DefectDisposition.NO_ACTION


# --- §8 N: a successful fix yields no new proposal ------------------------- #


def test_n_successful_fix_is_no_action_for_the_next_selection():
    decision = decide_defect_admission(observation(), context(already_resolved=True))
    assert decision.disposition is DefectDisposition.NO_ACTION
    summary = admission_summary([decision])
    assert summary["task_proposals_submitted"] == 0
    assert summary["execution_authorized"] is False


# --- §8 O: capacity below floor blocks unsafe work ------------------------- #


def test_o_capacity_below_floor_blocks_work():
    decision = decide_defect_admission(observation(), context(capacity_ok=False))
    assert decision.disposition is DefectDisposition.BLOCKED
    assert "capacity_below_floor" in decision.reasons


# --- §8 P/R: a changed HEAD invalidates the old approval ------------------ #


def test_p_changed_head_invalidates_the_old_approval():
    approval = {"commit_sha": SHA_A, "fingerprint": observation().fingerprint}
    assert approval_is_stale(approval, SHA_A) is False
    assert approval_is_stale(approval, SHA_B) is True


def test_p_changed_head_produces_a_new_fingerprint():
    assert observation().fingerprint != observation(commit_sha=SHA_B).fingerprint


def test_r_stale_approval_is_rejected_before_admission():
    approval = {"commit_sha": SHA_A}
    assert approval_is_stale(approval, SHA_C) is True
    decision = decide_defect_admission(observation(commit_sha=SHA_C), context())
    assert decision.proposal["commit_sha"] == SHA_C


# --- §8 Q: ingress restart is idempotent ----------------------------------- #


def test_q_ingress_restart_replays_the_same_single_record(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    decision = decide_defect_admission(observation(), context())
    for _ in range(3):
        DecisionJournal(AuditLog(log_path)).record(decision)
    assert len(AuditLog(log_path).replay()) == 1


# --- validation and aggregation -------------------------------------------- #


@pytest.mark.parametrize("overrides", [
    {"commit_sha": "not-a-sha"},
    {"repository": "not-a-repo"},
    {"subject": ()},
    {"subject": ("a", "b", "c", "d", "e")},
    {"observed_at": -1},
    {"event_revision": ""},
    {"evidence_sha256": ("d" * 64,) * 5},
])
def test_invalid_observations_fail_closed(overrides):
    with pytest.raises(DefectError):
        observation(**overrides)


def test_source_cannot_claim_an_unrelated_category():
    with pytest.raises(DefectError):
        observation(source=DefectSource.SECURITY_SCAN,
                    category=DefectCategory.TEST_REGRESSION)


def test_security_finding_requires_an_operator():
    decision = decide_defect_admission(
        observation(source=DefectSource.SECURITY_SCAN,
                    category=DefectCategory.SECURITY_FINDING),
        context(),
    )
    assert decision.disposition is DefectDisposition.HUMAN_GATE


def test_summary_reports_unparsed_as_unknown_not_zero():
    summary = admission_summary([object()])
    assert summary["unparsed"] == "UNKNOWN"
    assert summary["budget_operations"] == 0


# --- E4 round 1 remediation ------------------------------------------------- #


def test_two_distinct_checks_on_one_revision_are_two_defects():
    """E4 P1: the journal must not collapse distinct required checks."""
    first = observation(workflow="Herdr contract", check_run_id="run-1")
    second = observation(workflow="Herdr security", check_run_id="run-2")
    assert first.fingerprint != second.fingerprint


def test_one_check_redelivered_is_one_defect():
    first = observation(check_run_id="run-1", event_revision="rev-1")
    second = observation(check_run_id="run-1", event_revision="rev-1")
    assert first.fingerprint == second.fingerprint
    assert first.deduplication_id == second.deduplication_id


def test_repeated_runs_of_one_check_are_one_defect():
    """E4 P1: a run id is delivery identity, not semantic identity."""
    first = observation(workflow="Herdr contract", check_identity="herdr-contract",
                        check_run_id="run-1")
    second = observation(workflow="Herdr contract", check_identity="herdr-contract",
                         check_run_id="run-2")
    assert first.fingerprint == second.fingerprint
    assert first.deduplication_id != second.deduplication_id


def test_two_distinct_checks_in_one_workflow_are_two_defects():
    """E4 P1: workflow alone is not a stable check identity."""
    first = observation(workflow="Herdr contract", check_identity="herdr-contract",
                        check_run_id="run-1")
    second = observation(workflow="Herdr contract", check_identity="herdr-security",
                         check_run_id="run-2")
    assert first.fingerprint != second.fingerprint


def test_ci_observation_requires_a_stable_check_identity():
    with pytest.raises(DefectError):
        observation(source=DefectSource.CI_CHECK, check_identity="")


def test_unhandled_context_states_fail_closed():
    with pytest.raises(DefectError):
        context(budget_state="MISSING")
    with pytest.raises(DefectError):
        context(credentials_state="EXHAUSTED")


@pytest.mark.parametrize("overrides", [
    {"ref": "feat/ex\nline"},
    {"ref": ""},
    {"observed_at": 2 ** 100},
    {"evidence_sha256": ()},
])
def test_unbounded_or_empty_observation_fields_fail_closed(overrides):
    with pytest.raises(DefectError):
        observation(**overrides)


def test_untrusted_text_may_carry_no_evidence():
    obs = observation(source=DefectSource.UNTRUSTED_TEXT,
                      category=DefectCategory.UNCLASSIFIED,
                      evidence_sha256=())
    assert obs.evidence_sha256 == ()


def test_admit_payload_cannot_drop_the_proposal_only_contract():
    good = decide_defect_admission(observation(), context()).proposal
    broken = dict(good, authorizes_execution=True)
    with pytest.raises(DefectError):
        DefectDecision(DefectDisposition.ADMIT, "e" * 64, SHA_A, ("eligible",),
                       task_class="validation_failure", proposal=broken)


def test_concurrent_delivery_creates_one_durable_record(tmp_path):
    """E4 P1: record() must be atomic across concurrent callers."""
    import threading

    log_path = tmp_path / "audit.jsonl"
    decision = decide_defect_admission(observation(), context())
    created: list[bool] = []
    barrier = threading.Barrier(8)

    def deliver():
        barrier.wait()
        created.append(DecisionJournal(AuditLog(log_path)).record(decision)[1])

    threads = [threading.Thread(target=deliver) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(created) == 8
    assert created.count(True) == 1
    assert created.count(False) == 7
    assert len(AuditLog(log_path).replay()) == 1


def test_ci_check_cannot_claim_a_test_regression_without_evidence():
    """E4 P2: the #100 CI adapter proves a check failure, not a test regression."""
    with pytest.raises(DefectError):
        observation(source=DefectSource.CI_CHECK,
                    category=DefectCategory.TEST_REGRESSION)


def test_ci_check_cannot_claim_a_dependency_conflict():
    """E4 P2: only the dependent-PR source observes a conflict."""
    with pytest.raises(DefectError):
        observation(source=DefectSource.CI_CHECK,
                    category=DefectCategory.DEPENDENCY_CONFLICT)


# --- E4 round 2 remediation ------------------------------------------------- #


def test_unobserved_context_state_cannot_default_to_healthy():
    """E4 P1: every risk-relevant input must be supplied explicitly."""
    with pytest.raises(TypeError):
        DefectContext(repository_authorized=True)  # type: ignore[call-arg]


def test_admit_payload_is_immutable_after_validation():
    """E4 P1: a post-validation mutation must not be able to authorize."""
    decision = decide_defect_admission(observation(), context())
    assert decision.disposition is DefectDisposition.ADMIT
    with pytest.raises(TypeError):
        decision.proposal["authorizes_execution"] = True  # type: ignore[index]
    assert decision.proposal["authorizes_execution"] is False


def test_nested_admit_payload_is_immutable_after_validation():
    """E4 P1: freezing only the top map leaves nested limits mutable."""
    decision = decide_defect_admission(observation(), context())
    with pytest.raises(TypeError):
        decision.proposal["graph"]["node_count"] = 999  # type: ignore[index]
    assert decision.proposal["graph"]["node_count"] == 1  # type: ignore[index]


def test_admit_payload_cannot_be_reassigned():
    decision = decide_defect_admission(observation(), context())
    with pytest.raises(Exception):  # FrozenInstanceError
        decision.proposal = {}  # type: ignore[misc]
