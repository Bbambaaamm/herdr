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
from herdr.operational_incidents import (
    Detail,
    IncidentType,
    Observation,
    OperationalIncident,
    Source,
    State,
)

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
    evidence = observation.evidence_sha256[0]
    return DefectObservation(
        source=DefectSource.CI_CHECK,
        category=category,
        repository=observation.scope.project,
        commit_sha=head,
        ref=f"refs/pull/{pr}/head",
        subject=(f"pr-{pr}", f"workflow-{workflow}"),
        # #100 exposes no stable workflow-job *definition* id today: its
        # ``job_id`` is a per-run instance and its ``correlation_id`` covers the
        # whole (source, scope, subject) group.  Collapsing by correlation alone
        # would hide a second failing job, so the pinned evidence digest of the
        # individual #100 output participates in the identity.  That errs on the
        # side of reporting distinct failures; a stable definition id from #100
        # would replace it.
        finding_identity=f"ci-{observation.correlation_id[:16]}-{evidence[:12]}",
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
    envelope: OperationalIncident,
    context,
    control: AdmissionControl,
    usage: ResourceUsage,
    *,
    pin: str,
    journal: DecisionJournal,
) -> dict:
    """Run the full proposal path against the EXISTING admission gate.

    The input must be a #100 ``OperationalIncident`` envelope (produced by
    ``correlate`` from the durable incident log), not a bare observation and
    never a raw webhook.  ``pin`` must be one of the envelope's own evidence
    digests.  Provenance beyond that is #100's EventEnvelope boundary, not this
    module's: the bridge never authenticates its input, it only refuses input
    that did not come from the #100 fabric.

    ``journal`` is mandatory.  The defect decision is recorded durably, and the
    gate verdict separately.  Only a recorded ALLOW makes the proposal
    idempotent: a pending verdict (crash between the two writes) or a denied one
    stays re-evaluable, so a transient gate denial can never wedge a repair.

    The result carries ``authorizes_execution=False`` and no economic effect:
    it is a proposal for #8 to accept or deny, not permission to act.
    """
    if type(envelope) is not OperationalIncident:
        raise DefectError("not a #100 incident envelope")
    observation = envelope.current
    if type(observation) is not Observation:
        raise DefectError("not an operational observation")
    if type(control) is not AdmissionControl:
        raise DefectError("not an approved admission gate")
    if type(journal) is not DecisionJournal:
        raise DefectError("durable dedup journal is required")
    if type(pin) is not str or pin not in observation.evidence_sha256:
        raise DefectError("envelope is not pinned to the supplied evidence")
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
    journal.record(decision)
    outcome = journal.gate_outcome(decision)
    if outcome is not None and outcome.get("denied") is False:
        # A real allow already exists for this exact defect: idempotent.
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
            "admission": {"denied": False, "reason": "ALLOWED",
                          "detail": "gate already allowed this defect"},
        }
    if decision.disposition is DefectDisposition.ADMIT:
        verdict = control.check(
            agent_identity(defect), task_graph_spec(), usage, tuple(sorted(repair_tools()))
        )
        reason = getattr(verdict, "reason", None)
        reason_text = str(reason) if reason is not None else "ALLOWED"
        journal.record_gate(decision, denied=bool(verdict.denied), reason=reason_text)
        admission = {
            "denied": bool(verdict.denied),
            "reason": reason_text,
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
