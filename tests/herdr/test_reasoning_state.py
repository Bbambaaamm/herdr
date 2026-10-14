import json

import pytest

from herdr.capability import DataClass
from herdr.context import SourceRef, SourceState
from herdr.reasoning_state import (
    ClaimState,
    EvidenceLifecycle,
    ReasoningEvent,
    ReasoningStateError,
    materialize,
)
from herdr.security import InvocationIdentity


def identity(task="task"):
    return InvocationIdentity("github:org/repo", "agent", "parent-agent", "parent-task",
                              task, "run-token", 7)


def source(label="one", *, state=SourceState.VERIFIED):
    char = label[0] if label and label[0] in "abcdef0123456789" else "a"
    return SourceRef(
        uri=f"artifact://evidence/{label}",
        sha256=char * 64,
        project="org-repo",
        revision="rev-1",
        data_class=DataClass.INTERNAL,
        state=state,
    )


def test_replay_is_deterministic_and_json_roundtrips():
    ident = identity()
    events = [
        ReasoningEvent.evidence_added(
            ident, 1, evidence_id="ev-1", statement="The observed value is 42.",
            sources=(source("a"),), reason_code="source_observed",
        ),
        ReasoningEvent.claim_upserted(
            ident, 2, claim_id="claim-1", statement="The value is 42.",
            state=ClaimState.SUPPORTED, evidence_ids=("ev-1",), reason_code="source_supported",
        ),
        ReasoningEvent.gap_upserted(
            ident, 3, gap_id="gap-1", question="Is the value current?",
            reason_code="freshness_unknown",
        ),
    ]
    wire = [event.to_json() for event in events]
    restored = [ReasoningEvent.from_json(json.loads(json.dumps(item))) for item in wire]

    first = materialize(events)
    second = materialize(restored)
    assert first.hash == second.hash
    assert first.to_json() == second.to_json()
    assert [item.evidence_id for item in first.active_evidence] == ["ev-1"]
    assert [item.claim_id for item in first.supported_claims] == ["claim-1"]
    assert [item.gap_id for item in first.open_gaps] == ["gap-1"]


def test_supersession_preserves_history_and_downgrades_supported_claim():
    ident = identity()
    result = materialize([
        ReasoningEvent.evidence_added(
            ident, 1, evidence_id="old", statement="Old statement.",
            sources=(source("a"),), reason_code="source_observed",
        ),
        ReasoningEvent.claim_upserted(
            ident, 2, claim_id="claim", statement="Claim based on old evidence.",
            state=ClaimState.SUPPORTED, evidence_ids=("old",), reason_code="source_supported",
        ),
        ReasoningEvent.evidence_added(
            ident, 3, evidence_id="new", statement="Newer statement.",
            sources=(source("b"),), supersedes=("old",), reason_code="newer_source",
        ),
    ])
    rows = {item.evidence_id: item for item in result.evidence}
    assert rows["old"].state is EvidenceLifecycle.SUPERSEDED
    assert rows["old"].superseded_by == "new"
    assert rows["new"].state is EvidenceLifecycle.ACTIVE
    claim = result.claims[0]
    assert claim.state is ClaimState.UNKNOWN
    assert claim.evidence_ids == ()
    assert claim.reason_code == "support_retired"


def test_retraction_preserves_history_and_prevents_stale_support():
    ident = identity()
    result = materialize([
        ReasoningEvent.evidence_added(
            ident, 1, evidence_id="ev", statement="Temporary evidence.",
            sources=(source("a"),), reason_code="source_observed",
        ),
        ReasoningEvent.claim_upserted(
            ident, 2, claim_id="claim", statement="Supported claim.",
            state=ClaimState.SUPPORTED, evidence_ids=("ev",), reason_code="source_supported",
        ),
        ReasoningEvent.evidence_retracted(
            ident, 3, evidence_id="ev", reason_code="source_retracted",
        ),
    ])
    assert result.evidence[0].state is EvidenceLifecycle.RETRACTED
    assert result.claims[0].state is ClaimState.UNKNOWN
    assert result.supported_claims == ()


@pytest.mark.parametrize("state", [SourceState.STALE, SourceState.UNAVAILABLE, SourceState.CONFLICT])
def test_noncurrent_source_cannot_enter_active_working_evidence(state):
    with pytest.raises(ReasoningStateError, match="active_evidence_source_state"):
        ReasoningEvent.evidence_added(
            identity(), 1, evidence_id="ev", statement="Unsafe current evidence.",
            sources=(source("a", state=state),), reason_code="source_observed",
        )


def test_unverified_source_can_be_working_evidence_but_not_supported_fact():
    ident = identity()
    event = ReasoningEvent.evidence_added(
        ident, 1, evidence_id="ev", statement="Unverified candidate.",
        sources=(source("a", state=SourceState.UNVERIFIED),), reason_code="candidate",
    )
    with pytest.raises(ReasoningStateError, match="supported_claim_unverified_source"):
        materialize([
            event,
            ReasoningEvent.claim_upserted(
                ident, 2, claim_id="claim", statement="Premature conclusion.",
                state=ClaimState.SUPPORTED, evidence_ids=("ev",), reason_code="candidate",
            ),
        ])


def test_claim_cannot_reference_retired_or_missing_evidence():
    ident = identity()
    with pytest.raises(ReasoningStateError, match="claim_nonactive_evidence"):
        materialize([
            ReasoningEvent.evidence_added(
                ident, 1, evidence_id="ev", statement="Evidence.",
                sources=(source("a"),), reason_code="source_observed",
            ),
            ReasoningEvent.evidence_retracted(
                ident, 2, evidence_id="ev", reason_code="source_retracted",
            ),
            ReasoningEvent.claim_upserted(
                ident, 3, claim_id="claim", statement="Stale claim.",
                state=ClaimState.CONTESTED, evidence_ids=("ev",), reason_code="conflict",
            ),
        ])


def test_gap_resolution_is_explicit_and_replayable():
    ident = identity()
    result = materialize([
        ReasoningEvent.gap_upserted(
            ident, 1, gap_id="gap", question="Which revision is authoritative?",
            reason_code="revision_unknown",
        ),
        ReasoningEvent.gap_resolved(
            ident, 2, gap_id="gap", reason_code="revision_verified",
        ),
    ])
    assert result.open_gaps == ()


def test_sequence_and_identity_changes_fail_closed():
    ident = identity()
    event = ReasoningEvent.gap_upserted(
        ident, 1, gap_id="gap", question="Need evidence?", reason_code="evidence_missing",
    )
    with pytest.raises(ReasoningStateError, match="reasoning_sequence_gap"):
        materialize([event, ReasoningEvent.gap_resolved(
            ident, 3, gap_id="gap", reason_code="resolved",
        )])
    with pytest.raises(ReasoningStateError, match="reasoning_identity_changed"):
        materialize([event, ReasoningEvent.gap_resolved(
            identity("other"), 2, gap_id="gap", reason_code="resolved",
        )])


def test_duplicate_or_invalid_supersession_fails_closed():
    ident = identity()
    first = ReasoningEvent.evidence_added(
        ident, 1, evidence_id="ev", statement="Evidence.",
        sources=(source("a"),), reason_code="source_observed",
    )
    with pytest.raises(ReasoningStateError, match="duplicate_evidence_id"):
        materialize([first, ReasoningEvent.evidence_added(
            ident, 2, evidence_id="ev", statement="Duplicate.",
            sources=(source("b"),), reason_code="duplicate",
        )])
    with pytest.raises(ReasoningStateError, match="superseded_evidence_not_active"):
        materialize([first, ReasoningEvent.evidence_added(
            ident, 2, evidence_id="new", statement="New.",
            sources=(source("b"),), supersedes=("missing",), reason_code="newer_source",
        )])


def test_event_schema_is_closed():
    raw = ReasoningEvent.gap_upserted(
        identity(), 1, gap_id="gap", question="Question?", reason_code="unknown",
    ).to_json()
    raw["data"]["unexpected"] = True
    with pytest.raises(ReasoningStateError, match="gap_upserted_schema"):
        ReasoningEvent.from_json(raw)



def test_event_payload_is_immutable_after_construction():
    event = ReasoningEvent.gap_upserted(
        identity(), 1, gap_id="gap", question="Question?", reason_code="unknown",
    )
    first = event.to_json()
    first["data"]["question"] = "mutated"
    assert event.to_json()["data"]["question"] == "Question?"


def test_working_state_rejects_secret_like_text():
    with pytest.raises(ReasoningStateError, match="evidence_statement_secret"):
        ReasoningEvent.evidence_added(
            identity(), 1, evidence_id="ev", statement="api_key=supersecretvalue",
            sources=(source("a"),), reason_code="candidate",
        )
