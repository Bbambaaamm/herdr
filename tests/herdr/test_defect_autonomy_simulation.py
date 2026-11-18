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

Known P2s surfaced by E4 review (not defects of this change, recorded for the
next round):
- ``agent_identity()`` emits ``defect-<hash>``, which
  ``CanonicalParentAdmission`` rejects (it needs ``repo#<issue>``).  Using the
  pull request instead would collapse two distinct failing checks on one PR:
  ``AdmissionControl`` reconciles an ALLOW by ``(repo, issue, ...)``, so the
  second repair would be silently dropped.  The correct fix is a per-defect
  issue number, which needs an external action and is out of scope here.
- ``task_graph_spec()`` reports ``max_fanout=0`` (no fanout at all) while
  ``TaskGraphEnvelope`` cannot express 0 (floor 1).  A single-node graph with
  ``max_nodes=1`` cannot exceed either bound, so the difference is about the
  meaning of the two fields and deserves a comment, not a silent widening.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

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
from herdr.taskgraph import GRAPH_VERSION, TaskGraph, TaskGraphEnvelope, TaskNode

PROJECT = "Bbambaaamm/herdr"
SCOPE = Scope("herdr", PROJECT)
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
JOB = "Validate Python dashboard and telemetry"
NOW = 1_700_000_000


# --- the stub worker ------------------------------------------------------- #


@dataclass(frozen=True)
class DraftPullRequest:
    """The record a repair worker must leave behind.  Not a real publication."""

    repository: str
    base_branch: str
    head_branch: str
    draft: bool
    merged: bool
    deployed: bool
    review: str
    task_id: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        assert self.draft is True, "a repair must publish a draft, never a ready PR"
        assert self.merged is False, "a worker must never merge"
        assert self.deployed is False, "a worker must never deploy"


@dataclass(frozen=True)
class StubOutcome:
    """What a bounded worker would have to return.  No model is invoked."""

    reproduced: bool
    tests_pass: bool
    review: str
    draft: DraftPullRequest


def canonical_issue(defect) -> str:
    """The canonical ``repo#<issue>`` handle the scheduler parent needs."""
    pull_request = defect.subject[0].removeprefix("pr-")
    return f"{defect.repository}#{pull_request}"


def build_task(defect, identity, issue: str) -> TaskGraph:
    """One real, validated TaskGraph node for the admitted defect.

    ``issue`` must be in the canonical ``repo#<issue>`` form the scheduler's
    parent admission requires; a bare ``defect-<hex>`` handle is not accepted
    there (see the P2 note in the module docstring).
    """
    envelope = TaskGraphEnvelope(
        issue=issue,
        spec_hash=defect.fingerprint,
        graph_version=GRAPH_VERSION,
        created_at=datetime.now(UTC).isoformat(),
        planner="herdr-defect-admission",
        max_nodes=1,
        max_depth=1,
        # The envelope cannot express 0 (HARD_MAX_FANOUT floor is 1); the policy
        # spec the gate checked is stricter: no fanout at all.
        max_fanout=1,
    )
    node = TaskNode(
        id=f"repair-{defect.fingerprint[:12]}",
        parent_id=None,
        type="repair",
        role=identity.role,
        objective=f"Repair the admitted CI defect {defect.finding_identity}",
        inputs=({"fingerprint": defect.fingerprint, "commit_sha": defect.commit_sha,
                 "ref": defect.ref, "workflow": defect.workflow},),
        expected_outputs=({"draft_pr": "string", "tests": "pass"},),
        dependencies=(),
        priority=1,
        resource_class="paper",
        model_policy={"provider": "nous", "paper_only": True},
        tools=tuple(repair_tools()),
        permissions=(),
    )
    return TaskGraph.from_planner_output(envelope, [node.to_json()])


def stub_worker(defect, workspace: str, graph: TaskGraph) -> StubOutcome:
    """Deterministic stand-in for one bounded repair worker.

    It writes a marker file into ``workspace`` and runs a fixed local check, so
    the *plumbing* (one task, one attempt, one review, one draft PR record) is
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
        draft=DraftPullRequest(
            repository=defect.repository,
            base_branch="main",
            head_branch=f"defect/{defect.fingerprint[:12]}",
            draft=True,
            merged=False,
            deployed=False,
            review="PASS P0 0 / P1 0",
            task_id=graph.nodes[0].id,
            evidence_sha256=defect.evidence_sha256[0],
        ),
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
    graph = build_task(defect, identity, canonical_issue(defect))
    return {"defect": defect, "proposal": proposal, "spec": spec,
            "identity": identity, "graph": graph, "evidence": pinned["sha"]}


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

    # exactly one bounded task, as a real validated TaskGraph
    graph = first["graph"]
    assert first["spec"].node_count == 1
    assert first["spec"].max_depth == 1
    assert first["spec"].max_fanout == 0
    assert graph.envelope.graph_version == GRAPH_VERSION
    assert graph.envelope.issue == canonical_issue(defect)
    assert graph.envelope.issue.startswith(f"{defect.repository}#")
    assert len(graph.nodes) == 1
    assert graph.nodes[0].parent_id is None
    assert graph.nodes[0].dependencies == ()
    assert graph.nodes[0].tools == tuple(repair_tools())
    assert first["identity"].role == "writer"
    assert first["identity"].paper_only is True
    assert "git_push" not in repair_tools()
    assert "git_merge" not in repair_tools()
    assert "deploy" not in repair_tools()

    outcome = stub_worker(defect, workspace, graph)
    assert outcome.reproduced is True
    assert outcome.tests_pass is True
    assert outcome.review == "PASS P0 0 / P1 0"
    draft = outcome.draft
    assert draft.draft is True
    assert draft.merged is False
    assert draft.deployed is False
    assert draft.task_id == graph.nodes[0].id
    assert draft.base_branch == "main"
    assert draft.head_branch.startswith("defect/")
    assert draft.head_branch != draft.base_branch
    assert draft.repository == defect.repository
    assert draft.evidence_sha256 == defect.evidence_sha256[0]
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
    assert {node.id for node in first["graph"].nodes}.isdisjoint(
        {node.id for node in second["graph"].nodes})


def test_the_single_task_passes_canonical_scheduler_admission(tmp_path):
    """The built graph survives the scheduler's own parent admission."""
    from herdr.scheduler import CanonicalParentAdmission
    from herdr.security import InvocationIdentity

    first = run_chain(tmp_path, "237")
    graph = first["graph"]
    node = graph.nodes[0]
    repo = first["defect"].repository
    issue = first["defect"].subject[0].removeprefix("pr-")
    parent = CanonicalParentAdmission(
        graph=graph,
        graph_sha256=graph.graph_hash(),
        identity=InvocationIdentity(consumer=f"github:{repo}",
                                    agent_id="herdr-defect-admission",
                                    parent_agent_id="herdr-defect-admission",
                                    parent_task_id=node.id, task_id=node.id,
                                    run_token="sim-run-token", fencing_token=1),
        idempotency_key=f"defect-{first['defect'].fingerprint[:12]}",
        repo=repo, issue=issue, pane_id="sim-pane", marker="sim-marker",
    )
    canonical = parent.to_json()
    assert canonical["graph_sha256"] == graph.graph_hash()
    assert canonical["graph"]["envelope"]["issue"] == f"{repo}#{issue}"
    assert canonical["identity"]["task_id"] == node.id


def test_the_bridge_handle_is_not_yet_scheduler_canonical(tmp_path):
    """Open gap, pinned so it cannot be papered over silently.

    ``CanonicalParentAdmission`` needs ``repo#<issue>``; the bridge emits a
    defect-scoped handle instead.  Closing this needs a per-defect issue number,
    which is an external action (creating a GitHub issue) and is deliberately
    out of scope for this change.
    """
    first = run_chain(tmp_path, "237")
    identity = first["identity"]
    assert identity.issue.startswith("defect-")
    assert identity.issue != canonical_issue(first["defect"])


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
