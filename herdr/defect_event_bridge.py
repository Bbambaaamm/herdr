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

    Returns ``None`` for anything that is not an open CI validation failure, and
    raises :class:`DefectError` for a real CI failure whose defect identity the
    bridge cannot establish.

    #100 publishes no stable identity of the *defined* check: its ``job_id`` is a
    per-run instance, its per-run evidence digest changes on every run, and its
    ``correlation_id`` covers the whole (source, scope, subject) group.  None of
    those is a defensible identity for one CI defect — the first two fragment a
    red PR into N records, the third silently collapses N distinct failing checks
    into one and would dedup away a second, unrelated error.

    So the bridge refuses rather than guess.  A CI observation becomes a defect
    only once #100 publishes a stable per-check identity; this is a hard
    dependency on #100, not a convenience.
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
    raise DefectError(
        "no stable check identity from #100: refusing to identify a CI defect"
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

    A CI observation is refused with ``reason="unverified-check-identity"``
    until #100 publishes a stable per-check identity: #100's ``job_id`` is a
    per-run instance, its per-run evidence digest changes on every run, and its
    ``correlation_id`` covers the whole group, so none of them identifies one
    defect without either fragmenting a red PR or collapsing distinct checks.

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
    if defect_category(observation) is not None:
        return {
            "eligible": False,
            "reason": "unverified-check-identity",
            "authorizes_execution": False,
            "task_proposals_submitted": 0,
            "budget_operations": 0,
        }
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
    if decision.disposition is not DefectDisposition.ADMIT:
        # The defect gate is authoritative for its own verdict: a BLOCKED
        # defect stays blocked even if an earlier delivery was allowed.
        admission = {"denied": True, "reason": "defect-admission",
                     "detail": ",".join(decision.reasons)}
        deduplicated = False
    else:
        verdict = journal.evaluate(
            decision,
            control=control,
            usage=usage,
            spec=task_graph_spec(),
            identity=agent_identity(defect),
            tools=tuple(sorted(repair_tools())),
        )
        admission = {
            "denied": bool(verdict["denied"]),
            "reason": str(verdict["reason"]),
            "detail": str(verdict["detail"]),
        }
        deduplicated = bool(verdict["deduplicated"])
    return {
        "eligible": True,
        "fingerprint": defect.fingerprint,
        "deduplication_id": defect.deduplication_id,
        "disposition": decision.disposition.value,
        "reason": ",".join(decision.reasons),
        "deduplicated": deduplicated,
        "authorizes_execution": False,
        "task_proposals_submitted": 0,
        "budget_operations": 0,
        "admission": admission,
    }
