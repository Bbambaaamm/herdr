"""Read-only, fail-closed review for the October 2 legacy UNKNOWN episode.

NOT a retirement authority, replay API, queue mutation, or approval.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .evidence import EvidenceError

TASK_ID = "github-herdr-issue-53-20261002T102240Z"
REPOSITORY = "Bbambaaamm/herdr"
TASK_SHA256 = "fcc03dcd4cbc49666ddbd5fc5e991501b69d5c9f70a90227ed20b424bff116e3"
RESULT_SHA256 = "e7455f61ed2e19847c3fab72c1eb2ca1032facb334967b7e8132c1ec0b442490"
LOG_SHA256 = "daf3bb82f8d2e4a4b0c411c92e0f91f0427eb849ebf48ee03a16f548da7888fc"
SESSION_ID = "20261002_102241_25ddcf"
MAX_BYTES = 1048576


@dataclass(frozen=True)
class OriginalEvidence:
    task: bytes
    result: bytes
    worker_log: bytes


@dataclass(frozen=True)
class SessionObservation:
    session_id: str
    first_message_matches_task: bool
    observed_pr: int | None
    observed_commit: str | None


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode(data: bytes) -> dict:
    if type(data) is not bytes or not data or len(data) > MAX_BYTES:
        raise EvidenceError("legacy_unknown_invalid_size")

    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise EvidenceError("legacy_unknown_duplicate_field")
            value[key] = item
        return value

    try:
        result = json.loads(
            data, object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError())
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise EvidenceError("legacy_unknown_invalid_json") from exc
    if type(result) is not dict:
        raise EvidenceError("legacy_unknown_invalid_shape")
    return result


def inspect(evidence: OriginalEvidence, observation: SessionObservation | None = None) -> dict:
    """Validate exact immutable evidence and issue only a redacted hold report.

    Even complete historical provenance does not establish accounting settlement,
    execution acceptance, or permission to retire the original economic attempt.
    """
    if not isinstance(evidence, OriginalEvidence):
        raise EvidenceError("legacy_unknown_invalid_evidence")
    raw = (evidence.task, evidence.result, evidence.worker_log)
    if any(type(value) is not bytes or len(value) > MAX_BYTES for value in raw):
        raise EvidenceError("legacy_unknown_invalid_size")
    hashes = tuple(_sha(value) for value in raw)
    if hashes != (TASK_SHA256, RESULT_SHA256, LOG_SHA256):
        raise EvidenceError("legacy_unknown_source_changed")
    task, result = _decode(evidence.task), _decode(evidence.result)
    session = task.get("execution_session")
    if (task.get("id") != TASK_ID
        or task.get("repo") != REPOSITORY or task.get("issue") != 53
        or task.get("kind") != "github_root_orchestration"
        or task.get("attempt_state") != "blocked"
        or task.get("attempt_id") != 0 or task.get("attempts") != 0
        or task.get("delivery_reconcile_count") != 12
        or type(task.get("run_token")) is not str or not task["run_token"]
        or type(task.get("idempotency_key")) is not str or not task["idempotency_key"]
        or type(session) is not dict or session.get("pane_id") != "w4:p5"
        or session.get("cleanup_status") != "closed"
        or result.get("task_id") != TASK_ID
        or result.get("run_token") != task["run_token"]
        or result.get("status") != "blocked"
        or result.get("blocker") != "delivery_uncertain_requires_recovery"):
        raise EvidenceError("legacy_unknown_identity_mismatch")
    if any(k in task for k in ("fencing_token", "ownership_epoch", "result_contract")):
        raise EvidenceError("legacy_unknown_not_legacy")
    provenance = "UNVERIFIED"
    if observation is not None:
        if not isinstance(observation, SessionObservation):
            raise EvidenceError("legacy_unknown_observation_invalid")
        if (observation.session_id == SESSION_ID
            and observation.first_message_matches_task is True
            and observation.observed_pr == 81
            and observation.observed_commit == "1d7c4035e44f0be2a857de25b17b2dfe84018cb7"):
            provenance = "HISTORICAL_SESSION_CANDIDATE"
    return {
        "schema_version": "herdr-legacy-unknown-review-v1",
        "task_id": TASK_ID,
        "source_sha256": dict(zip(("task", "result", "worker_log"), hashes)),
        "session_evidence_status": provenance,
        "outcome": "UNKNOWN",
        "accounting": "UNKNOWN",
        "external_billing_verified": False,
        "decision": "HUMAN_REVIEW_REQUIRED",
        "automatic_retry_allowed": False,
        "mark_done_allowed": False,
        "production_transition_authorized": False,
    }
