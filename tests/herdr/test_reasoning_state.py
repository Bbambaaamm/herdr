import json
from dataclasses import replace

import pytest

from herdr.capability import DataClass
from herdr.context import SourceRef, SourceState
from herdr.reasoning_state import (
    ClaimState,
    ConclusionClaim,
    EvidenceLifecycle,
    OpenGap,
    ReasoningEvent,
    ReasoningEventKind,
    ReasoningProjection,
    ReasoningStateError,
    WorkingEvidenceEntry,
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


def evidence(name="ev", *, lifecycle=EvidenceLifecycle.ACTIVE, source_state=SourceState.VERIFIED,
             superseded_by=None):
    return WorkingEvidenceEntry(name, "Observed candidate.", (source("a", state=source_state),),
                                lifecycle, superseded_by)


def claim(*, state=ClaimState.SUPPORTED, evidence_ids=("ev",)):
    return ConclusionClaim("claim", "Working claim.", state, evidence_ids, "observed")


def projection(*, evidence_rows=(), claims=(), gaps=()):
    return ReasoningProjection(identity(), 1, evidence_rows, claims, gaps)


@pytest.mark.parametrize("state", [EvidenceLifecycle.RETRACTED, EvidenceLifecycle.SUPERSEDED])
def test_regression_direct_projection_cannot_expose_retired_support(state):
    rows = (evidence(lifecycle=state, superseded_by="new" if state is EvidenceLifecycle.SUPERSEDED else None),
            evidence("new"))
    with pytest.raises(ReasoningStateError):
        projection(evidence_rows=rows, claims=(claim(),))


def test_regression_direct_projection_cannot_expose_unverified_support():
    with pytest.raises(ReasoningStateError, match="supported_claim_unverified_source"):
        projection(evidence_rows=(evidence(source_state=SourceState.UNVERIFIED),), claims=(claim(),))


@pytest.mark.parametrize("rows,claims,gaps", [
    ((evidence(), evidence()), (), ()),
    ((evidence(),), (claim(), claim()), ()),
    ((), (), (OpenGap("gap", "Why?", "unknown"), OpenGap("gap", "Why?", "unknown"))),
    ((), (claim(),), ()),
])
def test_regression_direct_projection_rejects_duplicate_and_dangling_ids(rows, claims, gaps):
    with pytest.raises(ReasoningStateError):
        projection(evidence_rows=rows, claims=claims, gaps=gaps)


@pytest.mark.parametrize("rows", [
    lambda: (evidence("ev", lifecycle=EvidenceLifecycle.SUPERSEDED, superseded_by="missing"),),
    lambda: (evidence("ev", lifecycle=EvidenceLifecycle.SUPERSEDED, superseded_by="ev"),),
    lambda: (evidence("a", lifecycle=EvidenceLifecycle.SUPERSEDED, superseded_by="b"),
             evidence("b", lifecycle=EvidenceLifecycle.SUPERSEDED, superseded_by="a")),
])
def test_regression_direct_projection_rejects_invalid_supersession_graph(rows):
    with pytest.raises(ReasoningStateError):
        projection(evidence_rows=rows())


@pytest.mark.parametrize("state", [SourceState.STALE, SourceState.UNAVAILABLE, SourceState.CONFLICT])
def test_regression_direct_entry_rejects_noncurrent_active_sources(state):
    with pytest.raises(ReasoningStateError, match="active_evidence_source_state"):
        evidence(source_state=state)


@pytest.mark.parametrize("value", ["ghp_abcdefgh", "sk-abcdefgh", "../escape", "a/b", "a\nb"])
@pytest.mark.parametrize("kind", ["evidence", "claim", "gap", "reason", "support", "supersedes"])
def test_regression_all_identifier_metadata_is_nonsecret_and_safe(value, kind):
    with pytest.raises(ReasoningStateError):
        if kind == "evidence":
            evidence(value)
        elif kind == "claim":
            ConclusionClaim(value, "Candidate.", ClaimState.UNKNOWN, (), "unknown")
        elif kind == "gap":
            OpenGap(value, "Why?", "unknown")
        elif kind == "reason":
            OpenGap("gap", "Why?", value)
        elif kind == "support":
            claim(evidence_ids=(value,))
        else:
            ReasoningEvent.evidence_added(identity(), 1, evidence_id="new", statement="New.",
                                          sources=(source(),), supersedes=(value,))


@pytest.mark.parametrize("version", [True, False, 0, 2, "1", 1.0])
def test_regression_wire_version_is_exact_integer(version):
    raw = ReasoningEvent.gap_upserted(identity(), 1, gap_id="gap", question="Why?",
                                     reason_code="unknown").to_json()
    raw["version"] = version
    with pytest.raises(ReasoningStateError):
        ReasoningEvent.from_json(raw)


@pytest.mark.parametrize("factory", [
    lambda: ReasoningEvent(identity(), 1, "ghp_abcdefgh", {}),
    lambda: ConclusionClaim("claim", "Candidate.", "ghp_abcdefgh", (), "unknown"),
    lambda: WorkingEvidenceEntry("ev", "Candidate.", (source(),), "ghp_abcdefgh"),
])
def test_regression_invalid_enums_use_safe_errors(factory):
    with pytest.raises(ReasoningStateError) as caught:
        factory()
    assert "ghp_abcdefgh" not in str(caught.value)
    assert caught.value.__suppress_context__ or caught.value.__context__ is None


def test_regression_retirement_invalidates_every_claim_reference():
    ident = identity()
    events = [
        ReasoningEvent.evidence_added(ident, 1, evidence_id="one", statement="One.", sources=(source(),)),
        ReasoningEvent.evidence_added(ident, 2, evidence_id="two", statement="Two.", sources=(source(),)),
        ReasoningEvent.claim_upserted(ident, 3, claim_id="claim", statement="Candidate.",
                                     state=ClaimState.SUPPORTED, evidence_ids=("one", "two"),
                                     reason_code="observed"),
        ReasoningEvent.evidence_retracted(ident, 4, evidence_id="one", reason_code="withdrawn"),
        ReasoningEvent.evidence_retracted(ident, 5, evidence_id="two", reason_code="withdrawn"),
    ]
    result = materialize(events)
    assert result.claims[0].state is ClaimState.UNKNOWN
    assert result.claims[0].evidence_ids == ()


class GuardedInfinite:
    """An infinite source with a test sentinel so the old implementation cannot hang."""
    def __init__(self, value, limit):
        self.value, self.limit, self.consumed = value, limit, 0

    def __iter__(self):
        while True:
            self.consumed += 1
            if self.consumed > self.limit + 1:
                raise AssertionError("unbounded iterator consumed beyond limit plus one")
            yield self.value


@pytest.mark.parametrize("path,limit", [
    ("events", 2048), ("event_sources", 16), ("event_supersedes", 16),
    ("event_claim_ids", 64), ("entry_sources", 16), ("claim_ids", 64),
    ("projection_evidence", 256), ("projection_claims", 256), ("projection_gaps", 128),
])
def test_regression_iterables_are_bounded_before_exhaustion(path, limit):
    item = {"events": ReasoningEvent.gap_upserted(identity(), 1, gap_id="gap", question="Why?", reason_code="unknown"),
            "event_sources": source(), "event_supersedes": "ev", "event_claim_ids": "ev",
            "entry_sources": source(), "claim_ids": "ev", "projection_evidence": evidence(),
            "projection_claims": claim(), "projection_gaps": OpenGap("gap", "Why?", "unknown")}[path]
    values = GuardedInfinite(item, limit)
    with pytest.raises(ReasoningStateError):
        if path == "events":
            materialize(values)
        elif path.startswith("event_"):
            options = {"sources": (source(),), "supersedes": ()}
            if path == "event_claim_ids":
                ReasoningEvent.claim_upserted(identity(), 1, claim_id="claim", statement="Candidate.",
                                             state=ClaimState.UNKNOWN, evidence_ids=values,
                                             reason_code="unknown")
            else:
                options["sources" if path == "event_sources" else "supersedes"] = values
                ReasoningEvent.evidence_added(identity(), 1, evidence_id="new", statement="Candidate.", **options)
        elif path == "entry_sources":
            WorkingEvidenceEntry("ev", "Candidate.", values)
        elif path == "claim_ids":
            claim(evidence_ids=values)
        else:
            projection(**{path.removeprefix("projection_").replace("evidence", "evidence_rows"): values})
    assert values.consumed == limit + 1


@pytest.mark.parametrize("export", ["to_json", "active_evidence", "supported_claims", "hash"])
def test_regression_export_revalidates_support_graph(export):
    result = projection(evidence_rows=(evidence(),), claims=(claim(),))
    object.__setattr__(result, "evidence", (evidence(lifecycle=EvidenceLifecycle.RETRACTED),))
    with pytest.raises(ReasoningStateError):
        value = getattr(result, export)
        if callable(value):
            value()


@pytest.mark.parametrize("state", [ClaimState.UNKNOWN, ClaimState.CONTESTED])
def test_retirement_cleans_unknown_and_contested_bindings(state):
    ident = identity()
    result = materialize([
        ReasoningEvent.evidence_added(ident, 1, evidence_id="ev", statement="Observed.", sources=(source(),)),
        ReasoningEvent.claim_upserted(ident, 2, claim_id="claim", statement="Candidate.", state=state,
                                     evidence_ids=("ev",), reason_code="unknown"),
        ReasoningEvent.evidence_retracted(ident, 3, evidence_id="ev", reason_code="withdrawn"),
    ])
    assert result.claims[0].evidence_ids == ()
    assert result.claims[0].state is ClaimState.UNKNOWN


def test_supersession_chain_may_end_in_retracted_history_without_current_support():
    result = projection(evidence_rows=(
        evidence("a", lifecycle=EvidenceLifecycle.SUPERSEDED, superseded_by="b"),
        evidence("b", lifecycle=EvidenceLifecycle.SUPERSEDED, superseded_by="c"),
        evidence("c", lifecycle=EvidenceLifecycle.RETRACTED),
    ))
    assert result.active_evidence == () and result.supported_claims == ()
    assert len(result.to_json()["evidence"]) == 3


def test_direct_projection_order_is_canonical():
    first = projection(evidence_rows=(evidence("a"), evidence("b")))
    second = projection(evidence_rows=(evidence("b"), evidence("a")))
    assert first.hash == second.hash


@pytest.mark.parametrize("field", ["task_id", "run_token", "fencing_token"])
def test_replay_rejects_stale_host_identity(field):
    ident = identity()
    current = replace(ident, **{field: 8 if field == "fencing_token" else "changed"})
    event = ReasoningEvent.gap_upserted(ident, 1, gap_id="gap", question="Why?", reason_code="unknown")
    with pytest.raises(ReasoningStateError, match="reasoning_identity_stale"):
        materialize([event], expected_identity=current)
    assert materialize([event], expected_identity=ident).identity == ident


@pytest.mark.parametrize("field", ["consumer", "agent_id", "parent_agent_id",
                                  "parent_task_id", "task_id", "run_token"])
def test_identity_metadata_cannot_leak_known_credential_shapes(field):
    ident = replace(identity(), **{field: "ghp_abcdefgh"})
    with pytest.raises(ReasoningStateError) as caught:
        ReasoningEvent.gap_upserted(ident, 1, gap_id="gap", question="Why?", reason_code="unknown")
    assert "ghp_abcdefgh" not in str(caught.value)


def test_source_metadata_is_checked_before_export():
    ref = source()
    object.__setattr__(ref, "uri", "https://user:password@example.test/path")
    with pytest.raises(ReasoningStateError) as caught:
        WorkingEvidenceEntry("ev", "Observed.", (ref,))
    assert "password" not in str(caught.value)


@pytest.mark.parametrize("factory", [
    lambda: ReasoningEvent.gap_upserted(identity(), 1, gap_id="gap", question="\ud800", reason_code="unknown"),
    lambda: ReasoningEvent.evidence_added(identity(), 1, evidence_id="ev", statement="Observed.",
                                        sources=(object(),)),
    lambda: claim(evidence_ids=([1],)),
    lambda: ReasoningEvent.from_json({"version": 1, "identity": [], "sequence": 1,
                                     "kind": "gap_resolved", "data": {}}),
])
def test_malformed_input_uses_only_safe_contract_errors(factory):
    with pytest.raises(ReasoningStateError):
        factory()


@pytest.mark.parametrize("field,value", [
    ("kind", "ghp_abcdefgh"), ("data", b'{"unsafe":true}'),
    ("sequence", True), ("data", b"x" * 131073),
], ids=["invalid-kind", "invalid-schema", "boolean-sequence", "oversized-bytes"])
def test_event_export_revalidates_even_tampered_immutable_objects(field, value):
    event = ReasoningEvent.gap_upserted(identity(), 1, gap_id="gap", question="Why?", reason_code="unknown")
    object.__setattr__(event, field, value)
    with pytest.raises(ReasoningStateError) as caught:
        event.to_json()
    assert "ghp_abcdefgh" not in str(caught.value)
    with pytest.raises(ReasoningStateError):
        materialize([event])


def test_projection_total_bytes_are_bounded_at_construction_and_export(monkeypatch):
    import herdr.reasoning_state as module
    rows = tuple(WorkingEvidenceEntry(f"ev-{i}", "x" * 8192, (source(),)) for i in range(256))
    claims = tuple(ConclusionClaim(f"claim-{i}", "y" * 8192, ClaimState.SUPPORTED,
                                   ("ev-0",), "observed") for i in range(256))
    with pytest.raises(ReasoningStateError, match="reasoning_bytes_bound"):
        projection(evidence_rows=rows, claims=claims)
    result = projection(evidence_rows=(evidence(),))
    monkeypatch.setattr(module, "MAX_PROJECTION_BYTES", 64)
    # Default arguments pin an upper ceiling; the public construction limit
    # uses the named constant so hosts cannot accidentally export above it.
    with pytest.raises(ReasoningStateError, match="reasoning_bytes_bound"):
        result.to_json()


def test_event_and_replay_total_byte_bounds(monkeypatch):
    import herdr.reasoning_state as module
    monkeypatch.setattr(module, "MAX_EVENT_BYTES", 256)
    with pytest.raises(ReasoningStateError, match="reasoning_bytes_bound"):
        ReasoningEvent.gap_upserted(identity(), 1, gap_id="gap", question="q" * 256, reason_code="unknown")
    monkeypatch.setattr(module, "MAX_EVENT_BYTES", 131072)
    event = ReasoningEvent.gap_upserted(identity(), 1, gap_id="gap", question="Why?", reason_code="unknown")
    monkeypatch.setattr(module, "MAX_REPLAY_BYTES", 1)
    with pytest.raises(ReasoningStateError, match="reasoning_replay_bytes"):
        materialize([event])


def test_contract_does_not_supply_artifact_or_completion_authority():
    from herdr.reviewer import ReviewInput, ReviewerGate, ReviewVerdict
    from herdr.security import SecurityError, SecurityGrant
    from herdr.taskgraph import GraphValidationError, TaskGraphEnvelope
    from herdr.workspace import ArtifactRef
    result = projection(evidence_rows=(evidence(),), claims=(claim(),))
    with pytest.raises(SecurityError):
        SecurityGrant.from_dict(result.to_json())
    with pytest.raises(GraphValidationError):
        TaskGraphEnvelope.from_dict(result.to_json())
    artifact = ArtifactRef("task", 1, "a" * 40, "b" * 40, "c" * 64, ("file.py",), "branch")
    review = ReviewerGate().review(ReviewInput(
        "d" * 64, artifact, "worker", json.dumps(result.to_json()), (), None))
    assert review.verdict is ReviewVerdict.BLOCK

