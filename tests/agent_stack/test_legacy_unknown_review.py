"""Synthetic-only unit tests: no production state, provider or network access."""
from dataclasses import replace
import hashlib
import json
import pytest

from herdr.evidence import EvidenceError
import herdr.legacy_unknown_review as candidate


def prepare(monkeypatch):
    task = {
        "id": candidate.TASK_ID, "repo": candidate.REPOSITORY, "issue": 53,
        "kind": "github_root_orchestration",
        "attempt_state": "blocked", "attempt_id": 0, "attempts": 0,
        "delivery_reconcile_count": 12,
        "run_token": "secret-run", "idempotency_key": "secret-idempotency",
        "execution_session": {"pane_id": "w4:p5", "cleanup_status": "closed"},
        "prompt": "SECRET PROMPT"
    }
    result = {
        "task_id": candidate.TASK_ID, "run_token": "secret-run",
        "status": "blocked", "blocker": "delivery_uncertain_requires_recovery"
    }
    evidence = candidate.OriginalEvidence(
        json.dumps(task).encode(), json.dumps(result).encode(), b"original-log")
    for field, data in (("TASK_SHA256", evidence.task),
                        ("RESULT_SHA256", evidence.result),
                        ("LOG_SHA256", evidence.worker_log)):
        monkeypatch.setattr(candidate, field, hashlib.sha256(data).hexdigest())
    return evidence


def test_exact_evidence_is_hold_only_and_redacted(monkeypatch):
    evidence = prepare(monkeypatch)
    obs = candidate.SessionObservation(
        "20261002_102241_25ddcf", True, 81,
        "1d7c4035e44f0be2a857de25b17b2dfe84018cb7")
    report = candidate.inspect(evidence, obs)
    assert report["session_evidence_status"] == "HISTORICAL_SESSION_CANDIDATE"
    assert report["outcome"] == report["accounting"] == "UNKNOWN"
    assert report["decision"] == "HUMAN_REVIEW_REQUIRED"
    assert not report["automatic_retry_allowed"]
    assert not report["mark_done_allowed"]
    assert not report["production_transition_authorized"]
    assert "secret-" not in json.dumps(report)
    assert "SECRET PROMPT" not in json.dumps(report)


def test_unverified_session_stays_unknown(monkeypatch):
    evidence = prepare(monkeypatch)
    for observation in (
        None,
        candidate.SessionObservation("wrong", True, 81, None),
        candidate.SessionObservation("20261002_102241_25ddcf", False, 81, None),
    ):
        report = candidate.inspect(evidence, observation)
        assert report["session_evidence_status"] == "UNVERIFIED"


@pytest.mark.parametrize("field", ("task", "result", "worker_log"))
def test_modified_original_is_denied(monkeypatch, field):
    evidence = prepare(monkeypatch)
    modified = replace(evidence, **{field: getattr(evidence, field) + b" "})
    with pytest.raises(EvidenceError, match="source_changed"):
        candidate.inspect(modified)


@pytest.mark.parametrize("field, value", (
    ("issue", 54), ("repo", "other/other"),
    ("attempt_state", "done"), ("attempt_id", 2),
    ("delivery_reconcile_count", 13),
    ("fencing_token", 0), ("ownership_epoch", {"version": 1}),
    ("result_contract", {}), ("run_token", "forged"),
    ("execution_session", {"pane_id": "w4:pJ", "cleanup_status": "closed"}),
))
def test_invalid_identity_or_modern_fields_denied(monkeypatch, field, value):
    evidence = prepare(monkeypatch)
    task = json.loads(evidence.task)
    task[field] = value
    forged = json.dumps(task).encode()
    monkeypatch.setattr(candidate, "TASK_SHA256", hashlib.sha256(forged).hexdigest())
    with pytest.raises(EvidenceError, match="identity_mismatch|not_legacy"):
        candidate.inspect(replace(evidence, task=forged))


def test_duplicate_keys_denied(monkeypatch):
    evidence = prepare(monkeypatch)
    forged = evidence.task[:-1] + b', "issue":53}'
    monkeypatch.setattr(candidate, "TASK_SHA256", hashlib.sha256(forged).hexdigest())
    with pytest.raises(EvidenceError, match="duplicate_field"):
        candidate.inspect(replace(evidence, task=forged))


def test_oversized_log_denied(monkeypatch):
    evidence = prepare(monkeypatch)
    with pytest.raises(EvidenceError, match="invalid_size"):
        candidate.inspect(replace(evidence, worker_log=b"x" * (candidate.MAX_BYTES + 1)))
