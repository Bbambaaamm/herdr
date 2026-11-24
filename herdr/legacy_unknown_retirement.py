"""Host-owned, one-shot retirement of exactly one pre-fencing legacy UNKNOWN task.

Original blocked task/result/log bytes are NEVER rewritten. Only a verified,
root-owned operator decision + durably published receipt can release *intake*.
The old economic attempt remains UNKNOWN and is never automatically retried.
"""
from __future__ import annotations
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import time

from .evidence import EvidenceError
from . import recovery_unknown as guarded
from .legacy_unknown_review import (
    OriginalEvidence, TASK_ID, TASK_SHA256, RESULT_SHA256, LOG_SHA256, inspect,
)

SCHEMA = "herdr-legacy-unknown-retirement-v1"
RECEIPT_SCHEMA = "herdr-legacy-unknown-retirement-receipt-v1"
REVIEW_EVIDENCE_SHA256 = "c017dd6c579a4db6b986119e922fe96903e1fc9c2a3f257ed454ac2eb5f0e062"
DECISION_FILE = TASK_ID + ".legacy-retirement.json"
RECEIPT_NAME = TASK_ID + ".legacy-unknown-retirement-"
HASH = re.compile(r"[0-9a-f]{64}\Z")
LOCKS = ("recovery.lock", "github-intake-state.lock", "dispatcher.lock",
         "worker.lock", "worker.loop.lock")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _evidence(root: Path):
    files = (
        root / "blocked" / (TASK_ID + ".json"),
        root / "results" / (TASK_ID + ".json"),
        root / "logs" / (TASK_ID + ".worker.log"),
    )
    snapshots = [guarded.snapshot(p, maximum=1048576) for p in files]
    raw = tuple(x[0] for x in snapshots)
    report = inspect(OriginalEvidence(*raw))
    return raw, snapshots, report


def _approval_path(decisions: Path) -> Path:
    return decisions / DECISION_FILE


def _decision(decisions: Path) -> tuple[dict, str]:
    # Production uses the existing root-owned recovery decision directory.
    raw, _ = guarded.snapshot(_approval_path(decisions), owner=0, maximum=131072,
                               protected=True)
    obj = guarded._json(raw)
    keys = {"schema_version", "action", "task_id", "original_task_sha256",
            "original_result_sha256", "original_log_sha256", "review_evidence_sha256",
            "issued_at_epoch", "expires_at_epoch", "approval_reference",
            "writer_scope", "billing_disposition"}
    if (type(obj) is not dict or set(obj) != keys
            or obj["schema_version"] != SCHEMA
            or obj["action"] != "retire_legacy_unknown_intake_blocker"
            or obj["task_id"] != TASK_ID
            or obj["original_task_sha256"] != TASK_SHA256
            or obj["original_result_sha256"] != RESULT_SHA256
            or obj["original_log_sha256"] != LOG_SHA256
            or obj["writer_scope"] != "reviewed_writers_quiesced_and_locked"
            or obj["billing_disposition"] != "preserved_unknown"
            or not isinstance(obj["approval_reference"], str)
            or not 1 <= len(obj["approval_reference"]) <= 128
            or type(obj["issued_at_epoch"]) is not int
            or type(obj["expires_at_epoch"]) is not int
            or not 0 < obj["expires_at_epoch"] - obj["issued_at_epoch"] <= 3600
            or obj["review_evidence_sha256"] != REVIEW_EVIDENCE_SHA256):
        raise EvidenceError("legacy_retirement_decision_invalid")
    return obj, _sha(raw)


def _receipt_path(root: Path, decision_hash: str):
    return root / "results" / (RECEIPT_NAME + decision_hash + ".json")


def _receipt_payload(decision_hash: str, decision: dict, report: dict):
    return {
        "schema_version": RECEIPT_SCHEMA,
        "task_id": TASK_ID,
        "decision_sha256": decision_hash,
        "review_evidence_sha256": decision["review_evidence_sha256"],
        "source_sha256": report["source_sha256"],
        "approval_reference": decision["approval_reference"],
        "task_outcome": "UNKNOWN",
        "accounting": "preserved_unknown",
        "automatic_retry_allowed": False,
        "original_task_preserved": True,
        "original_result_preserved": True,
        "new_economic_attempt_authorized": False,
    }


def _validated_receipt(root: Path, decisions: Path, report: dict) -> dict | None:
    try:
        decision, digest = _decision(decisions)
        raw, _ = guarded.snapshot(_receipt_path(root, digest), maximum=131072)
        receipt = guarded._json(raw)
        if type(receipt) is not dict or receipt != _receipt_payload(digest, decision, report):
            return None
        return receipt
    except (EvidenceError, FileNotFoundError, OSError, TypeError, ValueError, KeyError):
        return None


def retired(root: Path, task: dict, *, decisions: Path | None = None) -> bool:
    """Read-only intake visibility; no canonical task mutation or minted authority."""
    if not isinstance(task, dict) or task.get("id") != TASK_ID:
        return False
    decisions = guarded.DECISIONS if decisions is None else decisions
    try:
        originals, _, report = _evidence(Path(root))
        # The caller's indexed record must be exactly the verified original
        # blocked task, not merely reuse its id.
        if task != guarded._json(originals[0]):
            return False
        return _validated_receipt(Path(root), Path(decisions), report) is not None
    except (EvidenceError, FileNotFoundError, OSError, TypeError, ValueError):
        return False


def applies(task: dict) -> bool:
    return (isinstance(task, dict) and task.get("id") == TASK_ID
            and task.get("repo") == "Bbambaaamm/herdr"
            and task.get("attempt_state") == "blocked")


def _require_no_active_root(root: Path) -> None:
    """No new/equal root issue may be active while legacy retirement is applied."""
    for folder in ("pending", "running"):
        candidates = sorted((root / folder).glob("*.json"))
        if len(candidates) > 1024:
            raise EvidenceError("legacy_retirement_active_inventory_unbounded")
        for path in candidates:
            raw, _ = guarded.snapshot(path, maximum=1048576)
            entry = guarded._json(raw)
            if type(entry) is not dict:
                raise EvidenceError("legacy_retirement_active_inventory_invalid")
            if (entry.get("repo") == "Bbambaaamm/herdr"
                    and str(entry.get("issue")) == "53"):
                raise EvidenceError("legacy_retirement_parallel_root_work")


def apply(root: Path, *, active_workers, decisions: Path | None = None,
          dry_run: bool = False) -> dict:
    """Separate operator-only action; requires root-owned explicit approval.

    All queue writers must have been independently pinned and quiesced.
    This action NEVER dispatches work; no auto-approval, retry or budget settle.
    """
    if not callable(active_workers):
        raise EvidenceError("legacy_retirement_worker_observer_required")
    root = Path(root)
    decisions = guarded.DECISIONS if decisions is None else Path(decisions)
    with ExitStack() as locks:
        for name in LOCKS:
            locks.enter_context(guarded.queue_lock(root, name))
        originals, snapshots, report = _evidence(root)
        decision, digest = _decision(decisions)
        receipt = _receipt_payload(digest, decision, report)
        path = _receipt_path(root, digest)
        existing = _validated_receipt(root, decisions, report)
        if existing is not None:
            return {"status": "already_retired", "task_id": TASK_ID,
                    "task_outcome": "UNKNOWN", "accounting_mutated": False}
        if os.path.lexists(path):
            raise EvidenceError("legacy_retirement_conflicting_receipt")
        if not decision["issued_at_epoch"] <= time.time() < decision["expires_at_epoch"]:
            raise EvidenceError("legacy_retirement_approval_expired")
        if active_workers():
            raise EvidenceError("legacy_retirement_active_worker")
        _require_no_active_root(root)
        # A declaration of reviewed provenance is not a license to infer cost.
        if not HASH.fullmatch(decision["review_evidence_sha256"]):
            raise EvidenceError("legacy_retirement_review_evidence_missing")
        if dry_run:
            return {"status": "READY_FOR_SEPARATE_OPERATOR_APPLY",
                    "task_id": TASK_ID, "task_outcome": "UNKNOWN",
                    "accounting_mutated": False,
                    "activation_performed": False}
        raw_bytes = guarded.canonical(receipt) + b"\n"
        guarded._write(path, raw_bytes, exclusive=True)
        # No task/result mutation. Confirm exact original evidence after receipt.
        current, _, _ = _evidence(root)
        if current != originals:
            raise EvidenceError("legacy_retirement_input_changed_after_publication")
        return {"status": "legacy_unknown_retired", "task_id": TASK_ID,
                "task_outcome": "UNKNOWN", "accounting_mutated": False,
                "automatic_retry_allowed": False, "receipt_sha256": _sha(raw_bytes)}
