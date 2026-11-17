"""Tests for the #100 Event Fabric -> defect admission bridge.

Every proposal here ends at the EXISTING AdmissionControl; none of these tests
dispatch work, spend budget, or write outside their own tmp_path audit sink.
"""

from __future__ import annotations

import pytest

from herdr.admission import AdmissionControl, AuditLog, PlanBudget, ResourceUsage
from herdr.defect_admission import DefectCategory, DefectError, DefectObservation
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
    Scope,
    Source,
    State,
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
    from herdr.defect_admission import DefectContext

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
    assert defect.finding_identity == "ci-12345-22"


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
    observation = ci_observation(facts=(("head", HEAD), ("run_id", 11)))
    with pytest.raises(DefectError):
        defect_from_observation(observation)


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


def test_two_distinct_checks_are_two_defects():
    first = defect_from_observation(ci_observation(facts=(("head", HEAD), ("run_id", 11), ("job_id", 22))))
    second = defect_from_observation(ci_observation(facts=(("head", HEAD), ("run_id", 11), ("job_id", 23))))
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


def test_admit_path_never_authorizes_execution(tmp_path):
    proposal = admission_proposal(
        ci_observation(), context(), control(tmp_path), host_usage()
    )
    assert proposal["eligible"] is True
    assert proposal["disposition"] == "ADMIT"
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
    proposal = admission_proposal(observation, context(), control(tmp_path), ResourceUsage())
    assert proposal["eligible"] is False
    assert proposal["authorizes_execution"] is False


def test_defect_gate_denial_is_propagated_without_consulting_the_swarm_gate(tmp_path):
    proposal = admission_proposal(
        ci_observation(), context(budget_state="EXHAUSTED"), control(tmp_path), host_usage()
    )
    assert proposal["disposition"] == "BLOCKED"
    assert proposal["admission"]["denied"] is True
    assert proposal["admission"]["reason"] == "defect-admission"


def test_swarm_gate_denial_is_propagated(tmp_path):
    proposal = admission_proposal(
        ci_observation(), context(), control(tmp_path), host_usage(active_agents=4)
    )
    assert proposal["admission"]["denied"] is True
    assert proposal["admission"]["reason"] == "global_agent_limit"


def test_existing_gate_audits_its_own_decision(tmp_path):
    admission_proposal(ci_observation(), context(), control(tmp_path), host_usage())
    records = (tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(records) == 1
    assert '"event": "allow"' in records[0]


def test_denied_defect_never_reaches_the_swarm_gate(tmp_path):
    admission_proposal(
        ci_observation(), context(budget_state="EXHAUSTED"), control(tmp_path), host_usage()
    )
    assert not (tmp_path / "admission.jsonl").exists()
