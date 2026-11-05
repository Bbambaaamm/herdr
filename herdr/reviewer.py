"""Herdr v1.4 independent reviewer gate and bounded redispatch.

The gate never trusts a worker's prose claim. It accepts only structured,
artifact-bound evidence from trusted validator/CI producers and an independent
model-review decision bound to the same artifact and evidence digest.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from .workspace import ArtifactRef

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ReviewVerdict(StrEnum):
    PASS = "pass"
    BLOCK = "block"
    NEEDS_REPLAN = "needs_replan"


class ReviewReason(StrEnum):
    NONE = "none"
    WORKER_TEXT_ONLY = "worker_text_pass_without_evidence"
    EVIDENCE_MISSING = "evidence_missing"
    EVIDENCE_DUPLICATE = "evidence_duplicate"
    EVIDENCE_UNTRUSTED = "evidence_untrusted"
    EVIDENCE_STALE = "evidence_stale"
    VALIDATOR_FAILED = "validator_failed"
    MODEL_REVIEW_REQUIRED = "model_review_required"
    MODEL_REVIEW_STALE = "model_review_stale"
    REVIEWER_NOT_INDEPENDENT = "reviewer_not_independent"
    MODEL_BLOCK = "model_block"
    PROTECTED_PATH = "protected_path"
    FIX_ATTEMPTS_EXHAUSTED = "fix_attempts_exhausted"


class RedispatchAction(StrEnum):
    REDISPATCH = "redispatch"
    NEEDS_REPLAN = "needs_replan"


class StaleReviewError(RuntimeError):
    """A prior review record is not valid for the supplied artifact."""


@dataclass(frozen=True)
class EvidenceRecord:
    name: str
    passed: bool
    artifact_result_sha: str
    producer: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        if not self.name or len(self.name) > 64:
            raise ValueError("evidence name is invalid")
        if not self.producer or len(self.producer) > 128:
            raise ValueError("evidence producer is invalid")
        if not _SHA256.fullmatch(self.artifact_result_sha):
            raise ValueError("evidence artifact_result_sha must be SHA-256")
        if not _SHA256.fullmatch(self.evidence_sha256):
            raise ValueError("evidence_sha256 must be SHA-256")


@dataclass(frozen=True)
class ModelReview:
    artifact_result_sha: str
    evidence_digest: str
    actor_id: str
    provider: str
    model: str
    verdict: ReviewVerdict
    review_sha256: str
    spec_hash: str | None = None

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.artifact_result_sha, "artifact_result_sha"),
            (self.evidence_digest, "evidence_digest"),
            (self.review_sha256, "review_sha256"),
        ):
            if not _SHA256.fullmatch(value):
                raise ValueError(f"{field_name} must be SHA-256")
        for value, field_name in (
            (self.actor_id, "actor_id"),
            (self.provider, "provider"),
            (self.model, "model"),
        ):
            if not value or len(value) > 256:
                raise ValueError(f"{field_name} is invalid")


@dataclass(frozen=True)
class ReviewInput:
    spec_hash: str
    artifact: ArtifactRef
    worker_actor: str
    worker_claim: str
    evidence: tuple[EvidenceRecord, ...]
    model_review: ModelReview | None

    def __post_init__(self) -> None:
        raw = self.spec_hash.removeprefix("sha256:")
        if not _SHA256.fullmatch(raw):
            raise ValueError("spec_hash must be SHA-256")
        if not self.worker_actor:
            raise ValueError("worker_actor is required")


@dataclass(frozen=True)
class ReviewRecord:
    verdict: ReviewVerdict
    reason: ReviewReason
    task_id: str
    attempt: int
    base_sha: str
    commit_sha: str
    result_sha: str
    changed_files: tuple[str, ...]
    reviewer_actor: str | None
    provider: str | None
    model: str | None
    evidence_digest: str
    review_hash: str
    details: tuple[str, ...] = ()


@dataclass
class ReviewerGate:
    max_fix_attempts: int = 3
    required_evidence: tuple[str, ...] = ("tests", "lint", "build")
    trusted_evidence_producers: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"trusted-ci", "trusted-validator", "trusted-local"}
        )
    )
    protected_paths: tuple[str, ...] = ()
    require_spec_binding: bool = False

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_fix_attempts, bool)
            or not isinstance(self.max_fix_attempts, int)
            or not 0 <= self.max_fix_attempts <= 10
        ):
            raise ValueError("max_fix_attempts must be in 0..10")
        if not self.required_evidence:
            raise ValueError("required_evidence cannot be empty")

    @staticmethod
    def evidence_digest(evidence: tuple[EvidenceRecord, ...]) -> str:
        rows = [asdict(item) for item in sorted(evidence, key=lambda item: item.name)]
        raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _record(
        self,
        inp: ReviewInput,
        verdict: ReviewVerdict,
        reason: ReviewReason,
        *,
        details: tuple[str, ...] = (),
    ) -> ReviewRecord:
        artifact = inp.artifact
        model_review = inp.model_review
        evidence_digest = self.evidence_digest(inp.evidence)
        payload = {
            "spec_hash": inp.spec_hash,
            "verdict": verdict.value,
            "reason": reason.value,
            "task_id": artifact.task_id,
            "attempt": artifact.attempt,
            "base_sha": artifact.base_sha,
            "commit_sha": artifact.commit_sha,
            "result_sha": artifact.result_sha,
            "changed_files": list(artifact.changed_files),
            "reviewer_actor": model_review.actor_id if model_review else None,
            "provider": model_review.provider if model_review else None,
            "model": model_review.model if model_review else None,
            "evidence_digest": evidence_digest,
        }
        review_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return ReviewRecord(
            verdict=verdict,
            reason=reason,
            task_id=artifact.task_id,
            attempt=artifact.attempt,
            base_sha=artifact.base_sha,
            commit_sha=artifact.commit_sha,
            result_sha=artifact.result_sha,
            changed_files=artifact.changed_files,
            reviewer_actor=model_review.actor_id if model_review else None,
            provider=model_review.provider if model_review else None,
            model=model_review.model if model_review else None,
            evidence_digest=evidence_digest,
            review_hash=review_hash,
            details=details,
        )

    def review(self, inp: ReviewInput) -> ReviewRecord:
        claim = (inp.worker_claim or "").strip().lower()
        if claim in {"pass", "ok", "success", "done"} and not inp.evidence:
            return self._record(
                inp,
                ReviewVerdict.BLOCK,
                ReviewReason.WORKER_TEXT_ONLY,
                details=("worker claim has no validator evidence",),
            )

        if self.protected_paths:
            protected = tuple(
                path
                for path in inp.artifact.changed_files
                if any(path.startswith(prefix) for prefix in self.protected_paths)
            )
            if protected:
                return self._record(
                    inp,
                    ReviewVerdict.NEEDS_REPLAN,
                    ReviewReason.PROTECTED_PATH,
                    details=("consumer safety policy requires escalation",),
                )

        by_name: dict[str, EvidenceRecord] = {}
        for item in inp.evidence:
            if item.name in by_name:
                return self._record(
                    inp,
                    ReviewVerdict.BLOCK,
                    ReviewReason.EVIDENCE_DUPLICATE,
                    details=(f"duplicate evidence category: {item.name}",),
                )
            by_name[item.name] = item

        missing = tuple(name for name in self.required_evidence if name not in by_name)
        if missing:
            return self._record(
                inp,
                ReviewVerdict.BLOCK,
                ReviewReason.EVIDENCE_MISSING,
                details=(f"missing evidence categories: {','.join(missing)}",),
            )

        for name in self.required_evidence:
            item = by_name[name]
            if item.artifact_result_sha != inp.artifact.result_sha:
                return self._record(
                    inp,
                    ReviewVerdict.BLOCK,
                    ReviewReason.EVIDENCE_STALE,
                    details=(f"evidence {name} targets a different artifact",),
                )
            if item.producer not in self.trusted_evidence_producers:
                return self._record(
                    inp,
                    ReviewVerdict.BLOCK,
                    ReviewReason.EVIDENCE_UNTRUSTED,
                    details=(f"evidence {name} producer is not trusted",),
                )
            if item.passed is not True:
                return self._record(
                    inp,
                    ReviewVerdict.BLOCK,
                    ReviewReason.VALIDATOR_FAILED,
                    details=(f"validator failed: {name}",),
                )

        evidence_digest = self.evidence_digest(inp.evidence)
        model_review = inp.model_review
        if model_review is None:
            return self._record(
                inp, ReviewVerdict.BLOCK, ReviewReason.MODEL_REVIEW_REQUIRED
            )
        if (
            model_review.artifact_result_sha != inp.artifact.result_sha
            or model_review.evidence_digest != evidence_digest
            or self.require_spec_binding and model_review.spec_hash != inp.spec_hash
        ):
            return self._record(
                inp, ReviewVerdict.BLOCK, ReviewReason.MODEL_REVIEW_STALE
            )
        if model_review.actor_id == inp.worker_actor:
            return self._record(
                inp, ReviewVerdict.BLOCK, ReviewReason.REVIEWER_NOT_INDEPENDENT
            )
        if model_review.verdict is ReviewVerdict.BLOCK:
            return self._record(inp, ReviewVerdict.BLOCK, ReviewReason.MODEL_BLOCK)
        if model_review.verdict is ReviewVerdict.NEEDS_REPLAN:
            return self._record(
                inp, ReviewVerdict.NEEDS_REPLAN, ReviewReason.MODEL_BLOCK
            )
        return self._record(inp, ReviewVerdict.PASS, ReviewReason.NONE)

    @staticmethod
    def validate_record(record: ReviewRecord, artifact: ArtifactRef) -> None:
        expected = (
            artifact.task_id,
            artifact.attempt,
            artifact.base_sha,
            artifact.commit_sha,
            artifact.result_sha,
            artifact.changed_files,
        )
        actual = (
            record.task_id,
            record.attempt,
            record.base_sha,
            record.commit_sha,
            record.result_sha,
            record.changed_files,
        )
        if actual != expected:
            raise StaleReviewError("review record does not bind to the exact artifact")

    def next_action(self, record: ReviewRecord) -> RedispatchAction | None:
        if record.verdict is ReviewVerdict.PASS:
            return None
        if record.verdict is ReviewVerdict.NEEDS_REPLAN:
            return RedispatchAction.NEEDS_REPLAN
        if record.attempt >= self.max_fix_attempts:
            return RedispatchAction.NEEDS_REPLAN
        return RedispatchAction.REDISPATCH


def evidence_hash(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

