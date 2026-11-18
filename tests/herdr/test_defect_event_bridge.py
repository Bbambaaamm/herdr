"""Tests for the #100 Event Fabric -> defect admission bridge.

Every proposal here ends at the EXISTING AdmissionControl; none of these tests
dispatch work, spend budget, or write outside their own tmp_path audit sink.

The bridge translates an open CI failure only when #100 publishes a stable
identity of the *defined* check (``Observation.check_id``); an older observation
shape with no defined check name is still refused rather than guessed.  The
durable journal and the gate underneath are exercised directly throughout,
because they must be correct regardless of the translation outcome.
"""

from __future__ import annotations

import threading

import pytest

from herdr.admission import AdmissionControl, AuditLog, PlanBudget, ResourceUsage
from herdr.defect_admission import (
    DecisionJournal,
    DefectCategory,
    DefectContext,
    DefectError,
    DefectObservation,
    DefectSource,
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
        "facts": (("head", HEAD), ("run_id", 11), ("job_id", 22),
                  ("job_name", "Validate Python dashboard and telemetry")),
    }
    payload.update(overrides)
    return Observation(**payload)


def envelope(observation=None):
    """Build a #100 envelope the way ``correlate`` does from the durable log."""
    return next(iter(correlate([ci_observation() if observation is None else observation])))


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


def defect(**overrides):
    payload = {
        "source": DefectSource.CI_CHECK,
        "category": DefectCategory.VALIDATION_FAILURE,
        "repository": PROJECT,
        "commit_sha": HEAD,
        "ref": "refs/pull/237/head",
        "subject": ("pr-237", "workflow-12345"),
        "finding_identity": "ci-12345",
        "workflow": "12345",
        "check_run_id": "11",
        "event_revision": "rev-1",
        "observed_at": 1_700_000_000,
        "evidence_sha256": (EVIDENCE,),
    }
    payload.update(overrides)
    return DefectObservation(**payload)


def control(tmp_path):
    return AdmissionControl(
        budget=PlanBudget(),
        audit_log=AuditLog(str(tmp_path / "admission.jsonl")),
        consumer_policy_hook=quantlab_paper_policy,
    )


def journal(tmp_path):
    return DecisionJournal(AuditLog(str(tmp_path / "defect.jsonl")))


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


def repair_identity(defect_observation):
    return (
        agent_identity(defect_observation),
        task_graph_spec(),
        tuple(sorted(repair_tools())),
    )


# --- translation: the defined check identity ------------------------------- #


def test_open_ci_failure_is_refused_without_a_stable_check_identity():
    """An older #100 shape with no defined check name must not be guessed."""
    observation = ci_observation(facts=(("head", HEAD), ("run_id", 11), ("job_id", 22)))
    with pytest.raises(DefectError) as raised:
        defect_from_observation(observation)
    assert "stable check identity" in str(raised.value)


def test_open_ci_failure_translates_with_the_defined_check_identity():
    """The #100 check_id becomes the defect's stable finding identity."""
    defect = defect_from_observation(ci_observation())
    assert defect is not None
    assert defect.finding_identity == ci_observation().check_id
    assert defect.workflow == "12345"
    assert defect.check_run_id == "22"
    assert defect.commit_sha == HEAD
    assert defect.repository == PROJECT
    assert defect.subject == ("pr-237", "workflow-12345")


def test_repeated_ci_runs_are_one_defect():
    """A re-run (new run/job id) keeps the semantic identity."""
    first = defect_from_observation(ci_observation())
    assert first is not None
    second = defect_from_observation(ci_observation(
        facts=(("head", HEAD), ("run_id", 99), ("job_id", 1234),
               ("job_name", "Validate Python dashboard and telemetry"))))
    assert second is not None
    assert first.fingerprint == second.fingerprint
    assert first.deduplication_id != second.deduplication_id


def test_two_defined_checks_are_two_defects():
    """Two failing checks on one revision must not collapse into one record."""
    base = defect_from_observation(ci_observation())
    other = defect_from_observation(ci_observation(
        facts=(("head", HEAD), ("run_id", 11), ("job_id", 23),
               ("job_name", "Run the offline repository contract"))))
    assert base is not None and other is not None
    assert other.fingerprint != base.fingerprint


def test_a_new_source_revision_is_a_new_defect():
    base = defect_from_observation(ci_observation())
    changed = defect_from_observation(ci_observation(
        revision="rev-2",
        facts=(("head", "f" * 40), ("run_id", 11), ("job_id", 22),
               ("job_name", "Validate Python dashboard and telemetry"))))
    assert base is not None and changed is not None
    assert changed.fingerprint != base.fingerprint


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


def test_open_success_is_a_contradictory_record_not_a_defect():
    assert defect_from_observation(ci_observation(detail=Detail.CI_SUCCESS)) is None


def test_open_skipped_is_not_a_defect():
    assert defect_from_observation(ci_observation(detail=Detail.CI_SKIPPED)) is None


def test_missing_ci_facts_are_rejected_not_guessed():
    observation = ci_observation(facts=(("run_id", 11), ("job_id", 22)))
    with pytest.raises(DefectError):
        defect_from_observation(observation)


def test_short_ci_subject_is_rejected():
    with pytest.raises(DefectError):
        defect_from_observation(ci_observation(subject=("237",)))


def test_non_observation_input_is_rejected():
    with pytest.raises(DefectError):
        defect_category(object())


def test_only_open_ci_failure_maps_to_a_defect_category():
    assert defect_category(ci_observation()) is DefectCategory.VALIDATION_FAILURE
    assert defect_category(ci_observation(state=State.RESOLVED)) is None


# --- proposal contract ----------------------------------------------------- #


def test_proposal_refuses_a_ci_observation_without_a_stable_check_identity(tmp_path):
    """An older #100 shape is refused before anything is written anywhere."""
    observation = ci_observation(facts=(("head", HEAD), ("run_id", 11), ("job_id", 22)))
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(observation), context(), control(tmp_path), host_usage(),
            pin=EVIDENCE, journal=journal(tmp_path),
        )
    assert not (tmp_path / "admission.jsonl").exists()
    assert not (tmp_path / "defect.jsonl").exists()


def test_proposal_admits_an_identified_ci_defect(tmp_path):
    proposal = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path),
    )
    assert proposal["eligible"] is True
    assert proposal["reason"] != "unverified-check-identity"
    assert proposal["authorizes_execution"] is False
    assert proposal["task_proposals_submitted"] == 0
    assert proposal["budget_operations"] == 0
    expected = defect_from_observation(ci_observation())
    assert expected is not None
    assert proposal["fingerprint"] == expected.fingerprint


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
        pin="c" * 64, journal=journal(tmp_path),
    )
    assert proposal["eligible"] is False
    assert proposal["reason"] == "not-a-code-defect"
    assert proposal["authorizes_execution"] is False
    assert not (tmp_path / "defect.jsonl").exists()


def test_proposal_requires_a_100_envelope(tmp_path):
    with pytest.raises(DefectError):
        admission_proposal(
            ci_observation(), context(), control(tmp_path), host_usage(),
            pin=EVIDENCE, journal=journal(tmp_path),
        )


def test_proposal_requires_the_real_gate(tmp_path):
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(), context(), object(), host_usage(),
            pin=EVIDENCE, journal=journal(tmp_path),
        )


def test_proposal_requires_a_journal(tmp_path):
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(), context(), control(tmp_path), host_usage(),
            pin=EVIDENCE, journal=object(),
        )


def test_proposal_requires_the_pinned_evidence_digest(tmp_path):
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(), context(), control(tmp_path), host_usage(),
            pin="e" * 64, journal=journal(tmp_path),
        )
    with pytest.raises(DefectError):
        admission_proposal(
            envelope(), context(), control(tmp_path), host_usage(),
            pin=object(), journal=journal(tmp_path),
        )


def test_proposal_never_authorizes_execution(tmp_path):
    proposal = admission_proposal(
        envelope(), context(), control(tmp_path), host_usage(),
        pin=EVIDENCE, journal=journal(tmp_path),
    )
    assert proposal["authorizes_execution"] is False


def test_repair_tools_exclude_operator_tools():
    tools = repair_tools()
    assert "herdr_verify_work" in tools
    assert "patch" in tools and "write_file" in tools
    for forbidden in ("git_push", "deploy", "git_merge", "herdr_operator"):
        assert forbidden not in tools


def test_task_graph_spec_is_a_single_node_plan():
    spec = task_graph_spec()
    assert spec.node_count == 1 and spec.max_depth == 1 and spec.max_fanout == 0


def test_identity_is_paper_only_and_bound_to_the_repository():
    identity = agent_identity(defect())
    assert identity.role == "writer"
    assert identity.repo == PROJECT
    assert identity.paper_only is True
    assert identity.parent_role is None


def test_identity_input_is_validated():
    with pytest.raises(DefectError):
        agent_identity(object())


# --- durable journal + the existing gate ----------------------------------- #


def test_recorded_allow_is_idempotent(tmp_path):
    j = journal(tmp_path)
    decision = decide_defect_admission(defect(), context())
    assert j.record(decision)[1] is True
    assert j.record(decision)[1] is False


def test_denied_verdict_is_retryable(tmp_path):
    j = journal(tmp_path)
    decision = decide_defect_admission(defect(), context())
    identity, spec, tools = repair_identity(defect())
    gate = control(tmp_path)
    first = j.evaluate(decision, control=gate, usage=host_usage(active_agents=4),
                       spec=spec, identity=identity, tools=tools)
    assert first["denied"] is True and first["deduplicated"] is False
    second = j.evaluate(decision, control=gate, usage=host_usage(),
                        spec=spec, identity=identity, tools=tools)
    assert second["denied"] is False and second["deduplicated"] is False


def test_pending_verdict_is_retryable(tmp_path):
    """A crash before the verdict write must leave the defect re-evaluable."""
    j = journal(tmp_path)
    decision = decide_defect_admission(defect(), context())
    j.record(decision)
    assert j.gate_outcome(decision) is None
    verdict = j.evaluate(decision, control=control(tmp_path), usage=host_usage(),
                         spec=task_graph_spec(), identity=agent_identity(defect()),
                         tools=tuple(sorted(repair_tools())))
    assert verdict["deduplicated"] is False and verdict["denied"] is False


def test_deny_then_allow_is_recorded(tmp_path):
    j = journal(tmp_path)
    decision = decide_defect_admission(defect(), context())
    identity, spec, tools = repair_identity(defect())
    gate = control(tmp_path)
    j.evaluate(decision, control=gate, usage=host_usage(active_agents=4),
               spec=spec, identity=identity, tools=tools)
    j.evaluate(decision, control=gate, usage=host_usage(),
               spec=spec, identity=identity, tools=tools)
    final = j.gate_outcome(decision)
    assert final is not None
    assert final["denied"] is False


def test_concurrent_deliveries_reach_the_gate_once(tmp_path):
    """The claim, the gate call and the verdict write are one atomic claim."""
    gate = control(tmp_path)
    j = journal(tmp_path)
    decision = decide_defect_admission(defect(), context())
    identity, spec, tools = repair_identity(defect())
    results, errors = [], []

    def deliver():
        try:
            results.append(j.evaluate(decision, control=gate, usage=host_usage(),
                                      spec=spec, identity=identity, tools=tools))
        except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion
            errors.append(exc)

    threads = [threading.Thread(target=deliver) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert len(results) == 6
    assert sum(1 for row in results if row["deduplicated"]) == 5
    assert sum(1 for row in results if row["denied"] is False) == 6
    rows = (tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1


def test_crash_after_allow_is_reconciled(tmp_path):
    """An ALLOW in #8's log without a verdict here must not re-spawn."""
    gate = control(tmp_path)
    identity, spec, tools = repair_identity(defect())
    gate.check(identity, spec, host_usage(), tools)
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    verdict = journal(tmp_path).evaluate(
        decide_defect_admission(defect(), context()),
        control=gate, usage=host_usage(), spec=spec, identity=identity, tools=tools,
    )
    assert verdict["deduplicated"] is True
    assert verdict["denied"] is False
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_reconciliation_requires_the_same_tool_set(tmp_path):
    """A narrower earlier ALLOW must not authorize a wider request (E4 r12)."""
    gate = control(tmp_path)
    identity, spec = agent_identity(defect()), task_graph_spec()
    narrow = tuple(sorted(repair_tools()))
    wide = narrow + ("git_push",)
    gate.check(identity, spec, host_usage(), narrow)
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    verdict = journal(tmp_path).evaluate(
        decide_defect_admission(defect(), context()),
        control=gate, usage=host_usage(), spec=spec, identity=identity, tools=wide,
    )
    assert verdict["deduplicated"] is False
    assert verdict["denied"] is True
    # the gate was consulted again: one #8 decision per distinct request
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_reconciliation_requires_the_same_policy_identity(tmp_path):
    """E4 r13: paper-only mode and parent authority are part of the ALLOW."""
    gate = control(tmp_path)
    strict = agent_identity(defect(), paper_only=False)
    identity, spec = agent_identity(defect()), task_graph_spec()
    tools = tuple(sorted(repair_tools()))
    gate.check(identity, spec, host_usage(), tools)  # paper_only=True
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    verdict = journal(tmp_path).evaluate(
        decide_defect_admission(defect(), context()),
        control=gate, usage=host_usage(), spec=spec, identity=strict, tools=tools,
    )
    assert verdict["deduplicated"] is False
    assert verdict["denied"] is True
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_reconciliation_requires_the_same_parent_authority(tmp_path):
    gate = control(tmp_path)
    identity, spec = agent_identity(defect()), task_graph_spec()
    tools = tuple(sorted(repair_tools()))
    gate.check(identity, spec, host_usage(), tools)
    delegated = agent_identity(defect(), parent_role="writer")
    verdict = journal(tmp_path).evaluate(
        decide_defect_admission(defect(), context()),
        control=gate, usage=host_usage(), spec=spec, identity=delegated, tools=tools,
    )
    assert verdict["deduplicated"] is False
    assert len((tmp_path / "admission.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_incomplete_older_audit_row_is_not_evidence(tmp_path):
    """An ALLOW recorded before these fields existed must not reconcile."""
    path = tmp_path / "admission.jsonl"
    path.write_text(
        '{"event": "allow", "admit:role": "writer", "admit:repo": "'
        + PROJECT
        + '", "admit:issue": "defect-'
        + defect().fingerprint[:12]
        + '"}\n',
        encoding="utf-8",
    )
    gate = AdmissionControl(
        budget=PlanBudget(),
        audit_log=AuditLog(str(path)),
        consumer_policy_hook=quantlab_paper_policy,
    )
    identity, spec = agent_identity(defect()), task_graph_spec()
    tools = tuple(sorted(repair_tools()))
    assert gate.has_allow(identity, spec, tools) is False
    verdict = journal(tmp_path).evaluate(
        decide_defect_admission(defect(), context()),
        control=gate, usage=host_usage(), spec=spec, identity=identity, tools=tools,
    )
    assert verdict["deduplicated"] is False


def test_blocked_disposition_is_a_defect_gate_denial(tmp_path):
    decision = decide_defect_admission(defect(), context(budget_state="EXHAUSTED"))
    assert decision.disposition.value == "BLOCKED"
    assert decision.reasons
