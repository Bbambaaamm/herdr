"""Tests for the #100 Event Fabric -> defect admission bridge.

Every proposal here ends at the EXISTING AdmissionControl; none of these tests
dispatch work, spend budget, or write outside their own tmp_path audit sink.
"""

from __future__ import annotations

import pytest

from herdr.admission import AdmissionControl, AuditLog, PlanBudget, ResourceUsage
from herdr.defect_admission import (
    DecisionJournal,
    DefectCategory,
    DefectContext,
    DefectError,
    DefectObservation,
    decide_defect_admission,
)
from herdr.defect_event_bridge import (
    DEFECT_CATEGORY,
    admission_proposal,
    agent_identity,
    defect_category,
    defect_from_observation,
    repair_tools,
    task_graph_spec,
)
from herdr.consumer_policies import quantlab_paper_policy
from herdr.operational_incidents import (
    Detail,
    IncidentType,
    Observation,
    OperationalIncident,
    Scope,
    Source,
    State,
    correlate,
)

HEAD = "a" * 40
EVIDENCE = "d" * 64
CONSUMER = "herdr"
PROJECT = "Bbambaaamm/herdr"


def scope():
    return Scope(consumer=CONSUMER, project=PROJECT)


def ci_observation(**overrides):
    payload = {
        "source": Source.CI,
        "kind": IncidentType.CI_VALIDATION_FAILED,
        "scope": scope(),
        "subject": ("237", "12345"),
        "revision": "rev-1",
        "event_at": 1_700_000_000,
        "observed_at": 1_700_000_060,
        "state": State.OPEN,
        "detail": Detail.CI_FAILURE,
        "evidence_sha256": (EVIDENCE,),
        "facts": (("head", HEAD), ("run_id", 11), ("job_id", 22)),
    }
    payload.update(overrides)
    return Observation(**payload)


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


def control(tmp_path):
    return AdmissionControl(
        budget=PlanBudget(),
        audit_log=AuditLog(str(tmp_path / "admission.jsonl")),
        consumer_policy_hook=quantlab_paper_policy,
    )


def host_usage(**overrides):
    """Realistic host telemetry: the #8 gate fails closed without it."""
    payload = {
        "active_agents": 0,
        "cpu": 0.0,
        "ram": 0.0,
        "queue_depth": 0,
        "elapsed_seconds": 0.0,
        "swap_risk": 0.0,
        "load1": 0.0,
        "logical_cpus": 8,
        "total_ram_bytes": 8 * 1024**3,
        "mem_available_bytes": 6 * 1024**3,
    }
    payload.update(overrides)
    return ResourceUsage(**payload)


# --- translation ----------------------------------------------------------- #


def test_open_ci_observation_translates_to_a_defect():
    defect = defect_from_observation(ci_observation())
    assert isinstance(defect, DefectObservation)
    assert defect.source.value == "github-actions-check"
    assert defect.category is DefectCategory.VALIDATION_FAILURE
    assert defect.repository == PROJECT
    assert defect.commit_sha == HEAD
    assert defect.ref == "refs/pull/237/head"
    assert defect.finding_identity == ci_observation().correlation_id


def test_resolved_ci_observation_is_not_a_defect():
    assert defect_from_observation(ci_observation(state=State.RESOLVED)) is None
    assert defect_from_observation(ci_observation(state=State.UNKNOWN)) is None


def test_worker_incident_is_not_a_code_defect():
    observation = Observation(
        source=Source.WORKER,
        kind=IncidentType.WORKER_STALLED,
        scope=scope(),
        subject=("task-1",),
        revision="rev-1",
        event_at=1_700_000_000,
        observed_at=1_700_000_060,
        state=State.OPEN,
        detail=Detail.HEARTBEAT_MISSING,
        evidence_sha256=("b" * 64,),
        task_id="task-1",
    )
    assert defect_from_observation(observation) is None


def test_capacity_incident_is_not_routed_to_a_repair_backlog():
    observation = Observation(
        source=Source.CAPACITY,
        kind=IncidentType.CAPACITY_BELOW_FLOOR,
        scope=scope(),
        subject=("capacity",),
        revision="rev-1",
        event_at=1_700_000_000,
        observed_at=1_700_000_060,
        state=State.OPEN,
        detail=Detail.BELOW_FLOOR,
        evidence_sha256=("c" * 64,),
        facts=(("available_bytes", 1),),
    )
    assert defect_from_observation(observation) is None
    assert DEFECT_CATEGORY.get((Source.CAPACITY, IncidentType.CAPACITY_BELOW_FLOOR)) is None


def test_missing_ci_facts_are_rejected_not_guessed():
    observation = ci_observation(facts=(("run_id", 11), ("job_id", 22)))
    with pytest.raises(DefectError):
        defect_from_observation(observation)


def test_open_success_is_a_contradictory_record_not_a_defect():
    observation = ci_observation(detail=Detail.CI_SUCCESS)
    assert defect_from_observation(observation) is None


def test_open_skipped_is_not_a_defect():
    assert defect_from_observation(ci_observation(detail=Detail.CI_SKIPPED)) is None


def test_non_observation_input_is_rejected():
    with pytest.raises(DefectError):
        defect_category(object())


def test_open_state_is_the_only_defect_state():
    assert defect_category(ci_observation()) is DefectCategory.VALIDATION_FAILURE
    assert defect_category(ci_observation(state=State.RESOLVED)) is None


# --- identity -------------------------------------------------------------- #


def test_repeated_run_of_one_check_is_one_defect():
    first = defect_from_observation(ci_observation(facts=(("head", HEAD), ("run_id", 11), ("job_id", 22))))
    second = defect_from_observation(ci_observation(facts=(("head", HEAD), ("run_id", 999), ("job_id", 22))))
    assert first.fingerprint == second.fingerprint
    # Delivery identity still differs, so dedup keeps a separate event row.
    assert first.deduplication_id != second.deduplication_id


def test_two_job_instances_of_one_workflow_are_one_defect():
    """job_id is a per-run instance id; it must not fragment one red PR."""
    first = defect_from_observation(ci_observation(facts=(("head", HEAD), ("run_id", 11), ("job_id", 22))))
    second = defect_from_observation(ci_observation(facts=(("head", HEAD), ("run_id", 11), ("job_id", 23))))
    assert first.fingerprint == second.fingerprint


def test_two_workflows_on_one_pr_are_two_defects():
    first = defect_from_observation(ci_observation(subject=("237", "12345")))
    second = defect_from_observation(ci_observation(subject=("237", "67890")))
    assert first.fingerprint != second.fingerprint


def test_new_revision_of_one_check_is_the_same_defect():
    first = defect_from_observation(ci_observation(revision="rev-1"))
    second = defect_from_observation(ci_observation(revision="rev-2"))
    assert first.fingerprint == second.fingerprint
    assert first.deduplication_id != second.deduplication_id


# --- proposal shape -------------------------------------------------------- #


def test_repair_tools_reuse_the_writer_allowlist_without_operator_tools():
    tools = repair_tools()
    assert "patch" in tools and "write_file" in tools
    assert "git_push" not in tools and "deploy" not in tools and "git_merge" not in tools


def test_task_graph_spec_is_a_single_node_plan():
    spec = task_graph_spec()
    assert spec.node_count == 1 and spec.max_depth == 1 and spec.max_fanout == 0


def test_identity_is_paper_only_and_bound_to_the_repository():
    identity = agent_identity(defect_from_observation(ci_observation()))
    assert identity.role == "writer"
    assert identity.repo == PROJECT
    assert identity.paper_only is True
    assert identity.parent_role is None


def test_identity_input_is_validated():
    with pytest.raises(DefectError):
        agent_identity(object())


# --- end to end against the existing gate ---------------------------------- #


def journal(tmp_path):
    return DecisionJournal(AuditLog(str(tmp_path / "defect.jsonl")))


def envelope(observation=None):
    """Build a #100 envelope the way ``correlate`` does from the durable log."""
    return next(iter(correlate([ci_observation() if observation is None else observation])))


def test_admit_path_never_authorizes_execution(tmp_path):
    proposal = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert proposal["eligible"] is True
    assert proposal["disposition"] == "ADMIT"
    assert proposal["deduplicated"] is False
    assert proposal["authorizes_execution"] is False
    assert proposal["task_proposals_submitted"] == 0
    assert proposal["budget_operations"] == 0
    # #8 is the only gate that may allow a spawn, and it did.
    assert proposal["admission"]["denied"] is False


def test_non_defect_observation_is_not_eligible(tmp_path):
    observation = Observation(
        source=Source.CAPACITY,
        kind=IncidentType.CAPACITY_BELOW_FLOOR,
        scope=scope(),
        subject=("capacity",),
        revision="rev-1",
        event_at=1_700_000_000,
        observed_at=1_700_000_060,
        state=State.OPEN,
        detail=Detail.BELOW_FLOOR,
        evidence_sha256=("c" * 64,),
        facts=(("available_bytes", 1),),
    )
    proposal = admission_proposal(
        envelope(observation), context(), control(tmp_path), host_usage(),
        pin="c" * 64, journal=journal(tmp_path))
    assert proposal["eligible"] is False
    assert proposal["authorizes_execution"] is False
    assert not (tmp_path / "defect.jsonl").exists()


def test_redelivery_is_deduplicated_before_the_swarm_gate(tmp_path):
    """E4 round 8 P1-1: a redelivered event must not re-enter the gate."""
    first = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    second = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert first["admission"]["denied"] is False
    assert second["deduplicated"] is True
    assert second["admission"]["denied"] is False
    # exactly one swarm-gate decision; the defect log holds decision + verdict
    rows = (tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    defect_rows = (tmp_path / "defect.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(defect_rows) == 2


def test_forged_gate_is_rejected(tmp_path):
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(), context(), object(), host_usage(),
            pin=EVIDENCE, journal=journal(tmp_path))


def test_missing_journal_is_rejected(tmp_path):
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(), context(), control(tmp_path), host_usage(),
            pin=EVIDENCE, journal=None)


def test_unpinned_observation_is_rejected(tmp_path):
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(), context(), control(tmp_path), host_usage(),
            pin="e" * 64, journal=journal(tmp_path))


def test_defect_gate_denial_is_propagated_without_consulting_the_swarm_gate(tmp_path):
    proposal = admission_proposal(
        envelope(), context(budget_state="EXHAUSTED"), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert proposal["disposition"] == "BLOCKED"
    assert proposal["admission"]["denied"] is True
    assert proposal["admission"]["reason"] == "defect-admission"


def test_swarm_gate_denial_is_propagated(tmp_path):
    proposal = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(active_agents=4),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert proposal["admission"]["denied"] is True
    assert proposal["admission"]["reason"] == "global_agent_limit"


def test_existing_gate_audits_its_own_decision(tmp_path):
    admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    rows = (tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    assert '"event": "allow"' in rows[0]
    defect_rows = (tmp_path / "defect.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(defect_rows) == 2


def test_denied_defect_never_reaches_the_swarm_gate(tmp_path):
    admission_proposal(
        envelope(), context(budget_state="EXHAUSTED"), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert not (tmp_path / "admission.jsonl").exists()
    # but the durable defect decision is still recorded
    assert len((tmp_path / "defect.jsonl").read_text(encoding="utf-8").splitlines()) == 1


# --- E4 round 9 ------------------------------------------------------------ #


def test_bare_observation_is_not_an_envelope(tmp_path):
    """E4 r9 P1-3: the bridge input must be a #100 envelope, not a bare value."""
    with pytest.raises(DefectError):
        admission_proposal(
            ci_observation(), context(), control(tmp_path), host_usage(),
            pin=EVIDENCE, journal=journal(tmp_path))


def test_denied_gate_verdict_is_retryable(tmp_path):
    """E4 r9 P1-1: a gate denial must not wedge the repair forever."""
    first = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(active_agents=4),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert first["admission"]["denied"] is True
    assert first["deduplicated"] is False
    # capacity frees up: the same defect is evaluated again
    second = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert second["deduplicated"] is False
    assert second["admission"]["denied"] is False
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_pending_gate_verdict_is_retryable(tmp_path):
    """E4 r9 P1-1: a crash before the gate must not wedge the repair."""
    defect = defect_from_observation(ci_observation())
    decision = decide_defect_admission(defect, context())
    journal(tmp_path).record(decision)
    assert journal(tmp_path).gate_outcome(decision) is None
    proposal = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert proposal["deduplicated"] is False
    assert proposal["admission"]["denied"] is False


def test_recorded_allow_is_idempotent(tmp_path):
    admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    again = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path))
    assert again["deduplicated"] is True
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_two_workflows_are_two_defects():
    """E4 r11: the identity is #100's correlation id, so distinct workflows split."""
    first = defect_from_observation(ci_observation(subject=("237", "11111")))
    second = defect_from_observation(ci_observation(subject=("237", "22222")))
    assert first is not None and second is not None
    assert first.fingerprint != second.fingerprint


def test_unstable_run_fields_are_not_defect_identity():
    """E4 r11: repeated runs of one correlation stay one defect."""
    first = defect_from_observation(ci_observation(evidence_sha256=("d" * 64,), facts=(("head", HEAD), ("run_id", 11), ("job_id", 22))))
    second = defect_from_observation(ci_observation(evidence_sha256=("e" * 64,), facts=(("head", HEAD), ("run_id", 99), ("job_id", 88))))
    assert first.fingerprint == second.fingerprint
    assert first.deduplication_id != second.deduplication_id


def test_crash_after_allow_is_reconciled(tmp_path):
    """E4 r11 P1: an ALLOW in #8's log without a verdict here must not re-spawn."""
    gate = control(tmp_path)
    defect = defect_from_observation(ci_observation())
    assert defect is not None
    identity, spec = agent_identity(defect), task_graph_spec()
    gate.check(identity, spec, host_usage(), tuple(sorted(repair_tools())))
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    # simulate the crash: #8 allowed, this journal recorded no verdict
    verdict = DecisionJournal(AuditLog(str(tmp_path / "defect.jsonl"))).evaluate(
        decide_defect_admission(defect, context()),
        control=gate, usage=host_usage(), spec=spec, identity=identity,
        tools=tuple(sorted(repair_tools())))
    assert verdict["deduplicated"] is True
    assert verdict["denied"] is False
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_same_pinned_output_redelivered_is_one_defect():
    first = defect_from_observation(ci_observation())
    second = defect_from_observation(ci_observation())
    assert first.fingerprint == second.fingerprint


# --- E4 round 10 ----------------------------------------------------------- #


def test_blocked_disposition_overrides_a_recorded_allow(tmp_path):
    """E4 r10 P1-1: the defect gate's current verdict wins over an old ALLOW."""
    gate, usage = control(tmp_path), host_usage()
    first = admission_proposal(
        envelope(), context(), gate, usage, pin=EVIDENCE, journal=journal(tmp_path))
    assert first["admission"]["denied"] is False
    second = admission_proposal(
        envelope(), context(budget_state="EXHAUSTED"), gate, usage, pin=EVIDENCE,
        journal=journal(tmp_path))
    assert second["disposition"] == "BLOCKED"
    assert second["admission"]["denied"] is True
    assert second["deduplicated"] is False


def test_deny_then_allow_is_recorded(tmp_path):
    """E4 r10 P1-2: a later ALLOW must not be swallowed by an older DENY."""
    gate, usage = control(tmp_path), host_usage()
    denied = admission_proposal(
        envelope(), context(), gate, host_usage(active_agents=4), pin=EVIDENCE,
        journal=journal(tmp_path))
    assert denied["admission"]["denied"] is True
    allowed = admission_proposal(
        envelope(), context(), gate, usage, pin=EVIDENCE, journal=journal(tmp_path))
    assert allowed["admission"]["denied"] is False
    assert allowed["deduplicated"] is False


def test_concurrent_deliveries_reach_the_gate_once(tmp_path):
    """E4 r10 P1-3: the claim, the gate call and the verdict write are atomic."""
    import threading

    gate, usage = control(tmp_path), host_usage()
    results, errors = [], []

    def run():
        try:
            results.append(admission_proposal(
                envelope(), context(), gate, usage, pin=EVIDENCE,
                journal=journal(tmp_path)))
        except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert len(results) == 6
    assert sum(1 for r in results if r["admission"]["denied"] is False) == 6
    assert sum(1 for r in results if r["deduplicated"]) == 5
    rows = (tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1