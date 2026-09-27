from __future__ import annotations

from dataclasses import replace

import pytest

from herdr.reviewer import (
    EvidenceRecord,
    ModelReview,
    RedispatchAction,
    ReviewerGate,
    ReviewInput,
    ReviewReason,
    ReviewVerdict,
    StaleReviewError,
    evidence_hash,
)
from herdr.workspace import ArtifactRef

RESULT = "1" * 64
OTHER = "2" * 64


def artifact(*, attempt: int = 0, result_sha: str = RESULT, files=("src/a.py",)) -> ArtifactRef:
    return ArtifactRef(
        task_id="task-5",
        attempt=attempt,
        base_sha="a" * 40,
        commit_sha="b" * 40,
        result_sha=result_sha,
        changed_files=tuple(files),
        branch="herdr/i5/task",
    )


def evidence(
    art: ArtifactRef,
    *,
    producer: str = "trusted-ci",
    passed: bool = True,
) -> tuple[EvidenceRecord, ...]:
    return tuple(
        EvidenceRecord(
            name=name,
            passed=passed,
            artifact_result_sha=art.result_sha,
            producer=producer,
            evidence_sha256=evidence_hash(f"{name}:{passed}"),
        )
        for name in ("tests", "lint", "build")
    )


def model_review(
    gate: ReviewerGate,
    art: ArtifactRef,
    ev: tuple[EvidenceRecord, ...],
    *,
    actor: str = "independent-reviewer",
    verdict: ReviewVerdict = ReviewVerdict.PASS,
) -> ModelReview:
    return ModelReview(
        artifact_result_sha=art.result_sha,
        evidence_digest=gate.evidence_digest(ev),
        actor_id=actor,
        provider="fixture-provider",
        model="fixture-reviewer",
        verdict=verdict,
        review_sha256=evidence_hash("model-review"),
    )


def inp(
    gate: ReviewerGate,
    art: ArtifactRef,
    ev: tuple[EvidenceRecord, ...],
    *,
    claim: str = "PASS",
    actor: str = "worker-a",
    reviewer: ModelReview | None = None,
) -> ReviewInput:
    return ReviewInput(
        spec_hash="sha256:" + "c" * 64,
        artifact=art,
        worker_actor=actor,
        worker_claim=claim,
        evidence=ev,
        model_review=reviewer if reviewer is not None else model_review(gate, art, ev),
    )


def test_worker_text_pass_without_evidence_is_blocked() -> None:
    gate = ReviewerGate()
    art = artifact()
    value = ReviewInput(
        spec_hash="sha256:" + "c" * 64,
        artifact=art,
        worker_actor="worker-a",
        worker_claim="PASS",
        evidence=(),
        model_review=None,
    )
    record = gate.review(value)
    assert record.verdict is ReviewVerdict.BLOCK
    assert record.reason is ReviewReason.WORKER_TEXT_ONLY


def test_worker_provided_evidence_is_not_trusted() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art, producer="worker")
    record = gate.review(inp(gate, art, ev))
    assert record.reason is ReviewReason.EVIDENCE_UNTRUSTED


def test_stale_evidence_is_blocked() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = list(evidence(art))
    ev[0] = replace(ev[0], artifact_result_sha=OTHER)
    record = gate.review(inp(gate, art, tuple(ev)))
    assert record.reason is ReviewReason.EVIDENCE_STALE


def test_failed_validator_is_blocked() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art, passed=False)
    record = gate.review(inp(gate, art, ev))
    assert record.reason is ReviewReason.VALIDATOR_FAILED


def test_model_review_is_required() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art)
    value = ReviewInput(
        spec_hash="sha256:" + "c" * 64,
        artifact=art,
        worker_actor="worker-a",
        worker_claim="done",
        evidence=ev,
        model_review=None,
    )
    record = gate.review(value)
    assert record.reason is ReviewReason.MODEL_REVIEW_REQUIRED


def test_reviewer_must_be_independent() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art)
    review = model_review(gate, art, ev, actor="worker-a")
    record = gate.review(inp(gate, art, ev, reviewer=review))
    assert record.reason is ReviewReason.REVIEWER_NOT_INDEPENDENT


def test_model_review_is_bound_to_artifact_and_evidence() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art)
    review = replace(model_review(gate, art, ev), artifact_result_sha=OTHER)
    record = gate.review(inp(gate, art, ev, reviewer=review))
    assert record.reason is ReviewReason.MODEL_REVIEW_STALE

    review2 = replace(model_review(gate, art, ev), evidence_digest=OTHER)
    record2 = gate.review(inp(gate, art, ev, reviewer=review2))
    assert record2.reason is ReviewReason.MODEL_REVIEW_STALE


def test_valid_independent_evidence_and_review_pass() -> None:
    gate = ReviewerGate()
    art = artifact(attempt=1)
    ev = evidence(art)
    record = gate.review(inp(gate, art, ev))
    assert record.verdict is ReviewVerdict.PASS
    assert record.reason is ReviewReason.NONE
    assert record.task_id == art.task_id
    assert record.attempt == art.attempt
    assert record.base_sha == art.base_sha
    assert record.commit_sha == art.commit_sha
    assert record.result_sha == art.result_sha
    assert len(record.review_hash) == 64


def test_new_artifact_invalidates_old_review_record() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art)
    record = gate.review(inp(gate, art, ev))
    gate.validate_record(record, art)
    changed = artifact(attempt=1, result_sha=OTHER)
    with pytest.raises(StaleReviewError):
        gate.validate_record(record, changed)


def test_bounded_redispatch_then_needs_replan() -> None:
    gate = ReviewerGate(max_fix_attempts=2)
    art0 = artifact(attempt=0)
    ev0 = evidence(art0, passed=False)
    r0 = gate.review(inp(gate, art0, ev0))
    assert gate.next_action(r0) is RedispatchAction.REDISPATCH

    art2 = artifact(attempt=2)
    ev2 = evidence(art2, passed=False)
    r2 = gate.review(inp(gate, art2, ev2))
    assert gate.next_action(r2) is RedispatchAction.NEEDS_REPLAN


def test_model_needs_replan_is_not_redispatched() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art)
    review = model_review(gate, art, ev, verdict=ReviewVerdict.NEEDS_REPLAN)
    record = gate.review(inp(gate, art, ev, reviewer=review))
    assert record.verdict is ReviewVerdict.NEEDS_REPLAN
    assert gate.next_action(record) is RedispatchAction.NEEDS_REPLAN


def test_protected_path_escalates_to_needs_replan() -> None:
    gate = ReviewerGate(protected_paths=("security/",))
    art = artifact(files=("security/policy.py",))
    ev = evidence(art)
    record = gate.review(inp(gate, art, ev))
    assert record.verdict is ReviewVerdict.NEEDS_REPLAN
    assert record.reason is ReviewReason.PROTECTED_PATH


def test_duplicate_evidence_category_fails_closed() -> None:
    gate = ReviewerGate()
    art = artifact()
    first = evidence(art)[0]
    ev = (first, first, *evidence(art)[1:])
    record = gate.review(inp(gate, art, ev))
    assert record.reason is ReviewReason.EVIDENCE_DUPLICATE


def test_model_block_remains_block() -> None:
    gate = ReviewerGate()
    art = artifact()
    ev = evidence(art)
    review = model_review(gate, art, ev, verdict=ReviewVerdict.BLOCK)
    record = gate.review(inp(gate, art, ev, reviewer=review))
    assert record.verdict is ReviewVerdict.BLOCK
    assert record.reason is ReviewReason.MODEL_BLOCK

