"""Bridge from the #100 operational Event Fabric to defect admission.

Ownership stays where it already is:

- #100 owns the single Event/Trigger and Human Steering surface.  This module
  only *translates* an already-correlated #100 ``Observation``.
- #53 owns the autonomous backlog; #82 the durable TaskGraph identity.
- #8 (parent #1) owns swarm admission.  A proposal built here is handed to the
  existing :class:`~herdr.admission.AdmissionControl`, which is the only gate
  that may allow a spawn.

This module never dispatches work, never proposes a second backlog, never
spends budget, and never widens the existing role tool allowlist.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from herdr.admission import (
    ROLE_TOOL_ALLOWLIST,
    AdmissionControl,
    AgentIdentity,
    ResourceUsage,
    TaskGraphSpec,
)
from herdr.defect_admission import (
    DefectCategory,
    DefectError,
    DefectObservation,
    DefectSource,
    DefectDecision,
    DefectDisposition,
    DecisionJournal,
    decide_defect_admission,
)
from herdr.operational_incidents import Detail, IncidentType, Observation, Source, State

__all__ = [
    "DEFECT_CATEGORY",
    "admission_proposal",
    "agent_identity",
    "defect_category",
    "defect_from_observation",
    "repair_tools",
    "task_graph_spec",
]

#: The single translation table.  Anything not listed here is *not* a code
#: defect: capacity, backup and worker incidents belong to their own operational
#: owners and must never be routed into a code-repair backlog.
DEFECT_CATEGORY: Mapping = MappingProxyType(
    {
        (Source.CI, IncidentType.CI_VALIDATION_FAILED): DefectCategory.VALIDATION_FAILURE,
    }
)

#: A CI observation is only a defect while it is still open.
_OPEN_STATES = frozenset({State.OPEN})


def defect_category(observation: Observation) -> DefectCategory | None:
    """Return the defect category, or ``None`` when this is not a code defect.

    Fail-closed: an observation shape that the Event Fabric did not already
    constrain is rejected rather than guessed at.  A CI observation is only a
    defect when it is both still open and reports an actual failure — an
    ``OPEN`` row carrying ``CI_SUCCESS`` is a contradictory record, not a defect.
    """
    if type(observation) is not Observation:
        raise DefectError("not an operational observation")
    category = DEFECT_CATEGORY.get((observation.source, observation.kind))
    if (category is None or observation.state not in _OPEN_STATES
            or observation.detail is not Detail.CI_FAILURE):
        return None
    return category


def defect_from_observation(observation: Observation) -> DefectObservation | None:
    """Translate an open #100 CI observation into the defect contract.

    Returns ``None`` for anything that is not an open CI validation failure.
    """
    category = defect_category(observation)
    if category is None:
        return None
    facts = dict(observation.facts)
    head, run_id = facts.get("head"), facts.get("run_id")
    if type(head) is not str or type(run_id) is not int:
        # The #100 CI adapter requires these facts, but a bridged observation
        # must not silently repair a missing identity.
        raise DefectError("CI observation lacks the head/run facts")
    subject = observation.subject
    if len(subject) < 2:
        raise DefectError("CI observation subject does not carry pr and workflow")
    pr, workflow = subject[0], subject[1]
    return DefectObservation(
        source=DefectSource.CI_CHECK,
        category=category,
        repository=observation.scope.project,
        commit_sha=head,
        ref=f"refs/pull/{pr}/head",
        subject=(f"pr-{pr}", f"workflow-{workflow}"),
        # #100's own correlation identity (source + scope + subject) is the only
        # stable check identity available today: the adapter's ``job_id`` is a
        # per-run instance id and would fragment one red PR into N defects.  A
        # per-check split needs #100 to expose the workflow job definition id.
        finding_identity=observation.correlation_id,
        workflow=workflow,
        check_run_id=str(run_id),
        event_revision=observation.revision,
        observed_at=observation.event_at,
        evidence_sha256=observation.evidence_sha256,
    )


def repair_tools() -> frozenset[str]:
    """Reuse the existing writer allowlist — operator tools stay gated."""
    return ROLE_TOOL_ALLOWLIST["writer"]


def task_graph_spec() -> TaskGraphSpec:
    """A bounded single-node repair plan; #8 still applies its own ceilings."""
    return TaskGraphSpec(node_count=1, max_depth=1, max_fanout=0)


def agent_identity(defect: DefectObservation) -> AgentIdentity:
    """Identity for the repair proposal, derived from the defect identity."""
    if type(defect) is not DefectObservation:
        raise DefectError("not a defect observation")
    return AgentIdentity(
        role="writer",
        repo=defect.repository,
        issue=f"defect-{defect.fingerprint[:12]}",
        parent_role=None,
        parent_tools=frozenset(),
        paper_only=True,
    )


def admission_proposal(
    observation: Observation,
    context,
    control: AdmissionControl,
    usage: ResourceUsage,
    *,
    pin: str,
    journal: DecisionJournal,
) -> dict:
    """Run the full proposal path against the EXISTING admission gate.

    ``pin`` is the #100 evidence digest that the observation was built from; it
    must match one of the observation's own evidence digests, so a fabricated
    observation cannot be paired with someone else's pinned evidence.

    ``journal`` is mandatory: without a durable dedup record a redelivered event
    would re-enter the swarm gate and produce a second allow.

    The result carries ``authorizes_execution=False`` and no economic effect:
    it is a proposal for #8 to accept or deny, not permission to act.
    """
    if type(observation) is not Observation:
        raise DefectError("not an operational observation")
    if type(control) is not AdmissionControl:
        raise DefectError("not an approved admission gate")
    if type(journal) is not DecisionJournal:
        raise DefectError("durable dedup journal is required")
    if type(pin) is not str or pin not in observation.evidence_sha256:
        raise DefectError("observation is not pinned to the supplied evidence")
    defect = defect_from_observation(observation)
    if defect is None:
        return {
            "eligible": False,
            "reason": "not-a-code-defect",
            "authorizes_execution": False,
            "task_proposals_submitted": 0,
            "budget_operations": 0,
        }
    decision: DefectDecision = decide_defect_admission(defect, context)
    _, recorded = journal.record(decision)
    if not recorded:
        # Durable dedup hit: this exact decision already exists.  Do not ask
        # the swarm gate again.
        return {
            "eligible": True,
            "fingerprint": defect.fingerprint,
            "deduplication_id": defect.deduplication_id,
            "disposition": decision.disposition.value,
            "reason": ",".join(decision.reasons),
            "deduplicated": True,
            "authorizes_execution": False,
            "task_proposals_submitted": 0,
            "budget_operations": 0,
            "admission": {"denied": True, "reason": "deduplicated",
                          "detail": "decision already recorded durably"},
        }
    if decision.disposition is DefectDisposition.ADMIT:
        verdict = control.check(
            agent_identity(defect), task_graph_spec(), usage, tuple(sorted(repair_tools()))
        )
        reason = getattr(verdict, "reason", None)
        admission = {
            "denied": bool(verdict.denied),
            "reason": str(reason) if reason is not None else "ALLOWED",
            "detail": str(getattr(verdict, "detail", "")),
        }
    else:
        admission = {"denied": True, "reason": "defect-admission",
                     "detail": ",".join(decision.reasons)}
    return {
        "eligible": True,
        "fingerprint": defect.fingerprint,
        "deduplication_id": defect.deduplication_id,
        "disposition": decision.disposition.value,
        "reason": ",".join(decision.reasons),
        "deduplicated": False,
        "authorizes_execution": False,
        "task_proposals_submitted": 0,
        "budget_operations": 0,
        "admission": admission,
    }
