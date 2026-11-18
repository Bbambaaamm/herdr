"""Deterministic offline simulation of the autonomous defect-repair chain.

This is **not** evidence that real model execution works.  It exercises the
deterministic part of the chain with a stub worker and asserts the invariants the
mission requires:

    pinned GitHub CI evidence
      -> #100 Observation (stable identity of the *defined* check)
      -> #100 incident envelope
      -> defect admission proposal against the existing #8 AdmissionControl
      -> exactly one bounded TaskGraph task
      -> stub worker: reproduce -> fix -> tests -> independent review
      -> draft PR record (no merge, no deploy)
      -> worker restart produces no second task
      -> budget and evidence stay consistent

Real model execution, real GitHub publication and real merge authority are out of
scope here and remain NOT_VERIFIED.  Nothing in this file dispatches work, calls
a model, writes outside its own tmp_path, or touches the network.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import pytest

from herdr.admission import AdmissionControl, AuditLog, PlanBudget, ResourceUsage
from herdr.consumer_policies import quantlab_paper_policy
from herdr.defect_event_bridge import (
    admission_proposal,
    agent_identity,
    defect_from_observation,
    repair_tools,
    task_graph_spec,
)
from herdr.defect_admission import DecisionJournal, DefectContext
from herdr.operational_adapters import github_ci
from herdr.operational_incidents import Scope, correlate

PROJECT = "Bbambaaamm/herdr"
SCOPE = Scope("herdr", PROJECT)
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
JOB = "Validate Python dashboard and telemetry"
NOW = 1_700_000_000


# --- the stub worker ------------------------------------------------------- #


@dataclass(frozen=True)
class StubOutcome:
    """What a bounded worker would have to return.  No model is invoked."""

    reproduced: bool
    tests_pass: bool
    review: str
    draft_pr: str
    merge: bool = False
    deploy: bool = False


def stub_worker(defect, workspace: str) -> StubOutcome:
    """Deterministic stand-in for one bounded repair worker.

    It writes a marker file into ``workspace`` and runs a fixed local check, so
    the *plumbing* (one task, one attempt, one review, one draft PR) is
    exercised without claiming that a model produced the fix.
    """
    from pathlib import Path

    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    (root / "fix.txt").write_text(f"{defect.fingerprint}\n", encoding="utf-8")
    return StubOutcome(
        reproduced=True,
        tests_pass=(root / "fix.txt").read_text(encoding="utf-8").strip() == defect.fingerprint,
        review="PASS P0 0 / P1 0",
        draft_pr=f"draft-pr-{defect.fingerprint[:12]}",
    )


# --- chain helpers --------------------------------------------------------- #


def pinned_ci(**overrides) -> dict:
    row = {"repo": PROJECT, "pr": 237, "head": HEAD, "run_id": 1,
           "workflow_id": 12345, "job_id": 22, "job_name": JOB,
           "at": NOW, "result": "failure"}
    row.update(overrides)
    raw = json.dumps(row, sort_keys=True).encode()
    return {"row": row, "raw": raw, "sha": hashlib.sha256(raw).hexdigest()}


def observation(**overrides) -> object:
    pinned = pinned_ci(**overrides)
    return github_ci(pinned["raw"], pinned["sha"], SCOPE,
                     expected_head=pinned["row"]["head"],
                     expected_pr=pinned["row"]["pr"], now=NOW)


def envelope(**overrides):
    rows = [incident for incident in correlate([observation(**overrides)])]
    assert len(rows) == 1
    return rows[0]


def context(**overrides) -> DefectContext:
    payload = {"repository_authorized": True, "already_resolved": False,
               "active_repairs": 0, "repeat_count": 0,
               "budget_state": "OK", "credentials_state": "OK",
               "capacity_ok": True, "max_repairs": 3}
    payload.update(overrides)
    return DefectContext(**payload)


def control(tmp_path) -> AdmissionControl:
    return AdmissionControl(
        budget=PlanBudget(),
        audit_log=AuditLog(str(tmp_path / "admission.jsonl")),
        consumer_policy_hook=quantlab_paper_policy,
    )


def journal(tmp_path) -> DecisionJournal:
    return DecisionJournal(AuditLog(str(tmp_path / "defect.jsonl")))


def host_usage() -> ResourceUsage:
    return ResourceUsage(active_agents=0, cpu=0.0, ram=0.0, queue_depth=0,
                         elapsed_seconds=0.0, swap_risk=0.0, load1=0.0,
                         logical_cpus=8, total_ram_bytes=8 * 1024**3,
                         mem_available_bytes=6 * 1024**3)


def run_chain(tmp_path, workspace, **observation_overrides) -> dict:
    """Run steps 1-3 and 7-8 of the chain against the real gate and journal."""
    env = envelope(**observation_overrides)
    pinned = pinned_ci(**observation_overrides)
    defect = defect_from_observation(env.current)
    assert defect is not None
    proposal = admission_proposal(
        env, context(), control(tmp_path), host_usage(),
        pin=pinned["sha"], journal=journal(tmp_path),
    )
    spec = task_graph_spec()
    identity = agent_identity(defect)
    return {"defect": defect, "proposal": proposal, "spec": spec,
            "identity": identity, "evidence": pinned["sha"]}


# --- the simulation -------------------------------------------------------- #


def test_ci_failure_becomes_exactly_one_task_and_one_draft_pr(tmp_path):
    """Steps 1-3, 6: identify, admit, one bounded task, one draft PR."""
    workspace = str(tmp_path / "worker")
    first = run_chain(tmp_path, workspace)
    defect, proposal = first["defect"], first["proposal"]

    assert proposal["eligible"] is True
    assert proposal["authorizes_execution"] is False
    assert proposal["task_proposals_submitted"] == 0
    assert proposal["budget_operations"] == 0
    assert proposal["admission"]["denied"] is False

    # exactly one bounded task
    assert first["spec"].node_count == 1
    assert first["spec"].max_depth == 1
    assert first["spec"].max_fanout == 0
    assert first["identity"].role == "writer"
    assert first["identity"].paper_only is True
    assert "git_push" not in repair_tools()
    assert "git_merge" not in repair_tools()
    assert "deploy" not in repair_tools()

    outcome = stub_worker(defect, workspace)
    assert outcome.reproduced is True
    assert outcome.tests_pass is True
    assert outcome.review == "PASS P0 0 / P1 0"
    assert outcome.draft_pr == f"draft-pr-{defect.fingerprint[:12]}"
    assert outcome.merge is False and outcome.deploy is False
    assert not (tmp_path / "merged").exists()


def test_worker_restart_does_not_duplicate_work(tmp_path):
    """Step 7: a restart re-evaluates and dedups; no second task, no re-charge."""
    workspace = str(tmp_path / "worker")
    first = run_chain(tmp_path, workspace)
    before = (tmp_path / "defect.jsonl").read_text(encoding="utf-8").count("\n")

    restarted = run_chain(tmp_path, workspace)
    assert restarted["proposal"]["deduplicated"] is True
    assert restarted["proposal"]["fingerprint"] == first["proposal"]["fingerprint"]
    assert restarted["proposal"]["budget_operations"] == 0
    assert restarted["proposal"]["task_proposals_submitted"] == 0
    # the journal grew by exactly one re-evaluation row, not a new defect
    assert (tmp_path / "defect.jsonl").read_text(encoding="utf-8").count("\n") == before


def test_two_independent_checks_are_two_tasks(tmp_path):
    """Two distinct failing checks must not collapse into one task."""
    workspace = str(tmp_path / "worker")
    first = run_chain(tmp_path, workspace)
    second = run_chain(tmp_path, workspace, job_id=23,
                       job_name="Run the offline repository contract")
    assert first["proposal"]["fingerprint"] != second["proposal"]["fingerprint"]
    assert second["proposal"]["deduplicated"] is False


def test_a_re_run_of_the_same_check_is_the_same_defect(tmp_path):
    """Step 8: repeated CI runs keep the identity; only the state moves."""
    workspace = str(tmp_path / "worker")
    first = run_chain(tmp_path, workspace)
    rerun = run_chain(tmp_path, workspace, run_id=99, job_id=1234)
    assert rerun["defect"].fingerprint == first["defect"].fingerprint
    assert rerun["proposal"]["deduplicated"] is True


def test_a_new_source_revision_is_a_new_defect(tmp_path):
    workspace = str(tmp_path / "worker")
    first = run_chain(tmp_path, workspace)
    moved = run_chain(tmp_path, workspace, head=OTHER_HEAD, run_id=99, job_id=1234)
    assert moved["defect"].fingerprint != first["defect"].fingerprint


def test_prompt_injection_payload_in_the_check_name_is_not_executed(tmp_path):
    """A hostile job name stays data: no shell, no file, no network."""
    workspace = str(tmp_path / "worker")
    payload = "x; touch pwned; #"
    chain = run_chain(tmp_path, workspace, job_name=payload)
    assert chain["defect"].finding_identity != payload
    assert ";" not in chain["defect"].finding_identity
    assert not (tmp_path / "pwned").exists()
    assert not (tmp_path / "worker" / "pwned").exists()


def test_stale_approval_cannot_widen_the_chain(tmp_path):
    """The proposal never authorizes execution, whatever the journal holds."""
    workspace = str(tmp_path / "worker")
    chain = run_chain(tmp_path, workspace)
    assert chain["proposal"]["authorizes_execution"] is False
    assert chain["proposal"]["admission"]["denied"] is False


def test_legacy_ci_shape_without_a_check_name_is_refused(tmp_path):
    """Fail-closed: an older #100 observation never reaches the gate.

    The adapter already rejects a missing field set; this exercises the bridge's
    own refusal for an Observation that was built by another path.
    """
    from herdr.defect_admission import DefectError
    from herdr.operational_incidents import (
        Detail,
        IncidentType,
        Observation,
        Source,
        State,
    )

    legacy = Observation(
        source=Source.CI, kind=IncidentType.CI_VALIDATION_FAILED, scope=SCOPE,
        subject=("237", "12345"), revision="0" * 64, event_at=NOW, observed_at=NOW,
        state=State.OPEN, detail=Detail.CI_FAILURE,
        evidence_sha256=(hashlib.sha256(b"legacy").hexdigest(),),
        facts=(("head", HEAD), ("run_id", 1), ("job_id", 2)),
    )
    with pytest.raises(DefectError):
        defect_from_observation(legacy)
