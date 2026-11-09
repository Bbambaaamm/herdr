"""Canonical host-bound result evidence for new durable publications.

This module is deliberately a contract, not a second result store or an
acceptance authority.  The worker owns the source task snapshot; this helper
only projects that already-authoritative identity into a bounded, versioned
result envelope and rejects mismatches.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import hashlib
import json


RESULT_SCHEMA = "herdr-durable-result-v1"
RESULT_VERSION = 1
RESULT_STATUSES = frozenset({"completed", "blocked", "failed", "terminal_unknown"})
_VERIFICATION_STATES = frozenset({"candidate", "verified", "unverified", "terminal_unknown"})
_AUTHORITY_TYPES = frozenset({"host_result_publisher", "host_completion_acceptance", "host_control"})
_MAX_BYTES = 131072
_RECEIPT_FIELDS = ("task_id", "run_token", "fencing_token", "idempotency_key",
                   "status", "evidence", "artifact_sha256", "summary")


class ResultContractError(ValueError):
    """A result cannot be bound to the authoritative task snapshot."""


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ResultContractError("result_contract_not_canonical_json") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str, *, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ResultContractError(f"{field}_invalid")
    return value


def _integer(value: Any, field: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ResultContractError(f"{field}_invalid")
    return value


def _optional_text(value: Any, field: str, *, maximum: int = 512) -> str | None:
    if value is None:
        return None
    return _text(value, field, maximum=maximum)


def _ownership_epoch(value: Any, *, run_token: str, fencing_token: int) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"version", "run_token", "fencing_token"}:
        raise ResultContractError("ownership_epoch_not_host_issued")
    version = _integer(value.get("version"), "ownership_epoch.version", minimum=1)
    epoch_run = _text(value.get("run_token"), "ownership_epoch.run_token")
    epoch_fence = _integer(value.get("fencing_token"), "ownership_epoch.fencing_token", minimum=1)
    if epoch_run != run_token or epoch_fence != fencing_token:
        raise ResultContractError("ownership_epoch_identity_mismatch")
    return {"version": version, "run_token": epoch_run, "fencing_token": epoch_fence}


@dataclass(frozen=True)
class ResultIdentity:
    repository: str
    issue: str | int
    task_id: str
    attempt_id: int
    run_token: str
    fencing_token: int
    ownership_epoch: Mapping[str, Any]
    idempotency_key: str
    consumer: str
    parent_task_id: str | None = None
    parent_run_token: str | None = None

    def __post_init__(self) -> None:
        _text(self.repository, "identity.repository")
        if not (isinstance(self.issue, str) and self.issue or type(self.issue) is int and self.issue >= 0):
            raise ResultContractError("identity.issue_invalid")
        _text(self.task_id, "identity.task_id")
        _integer(self.attempt_id, "identity.attempt_id")
        _text(self.run_token, "identity.run_token")
        _integer(self.fencing_token, "identity.fencing_token", minimum=1)
        _text(self.idempotency_key, "identity.idempotency_key", maximum=256)
        _text(self.consumer, "identity.consumer")
        if (self.parent_task_id is None) != (self.parent_run_token is None):
            raise ResultContractError("identity_parent_lineage_incomplete")
        if self.parent_task_id is not None:
            _text(self.parent_task_id, "identity.parent_task_id")
            _text(self.parent_run_token, "identity.parent_run_token")
        _ownership_epoch(self.ownership_epoch, run_token=self.run_token,
                         fencing_token=self.fencing_token)

    def to_dict(self) -> dict[str, Any]:
        value = {
            "repository": self.repository, "issue": self.issue,
            "task_id": self.task_id, "attempt_id": self.attempt_id,
            "run_token": self.run_token, "fencing_token": self.fencing_token,
            "ownership_epoch": dict(self.ownership_epoch),
            "idempotency_key": self.idempotency_key, "consumer": self.consumer,
        }
        if self.parent_task_id is not None:
            value.update(parent_task_id=self.parent_task_id, parent_run_token=self.parent_run_token)
        return value

    @classmethod
    def from_task(cls, task: Mapping[str, Any]) -> "ResultIdentity":
        if not isinstance(task, Mapping):
            raise ResultContractError("authoritative_task_not_object")
        required = ("repo", "issue", "id", "attempt_id", "run_token", "fencing_token",
                    "ownership_epoch", "idempotency_key", "consumer")
        if any(field not in task for field in required):
            raise ResultContractError("authoritative_task_identity_incomplete")
        return cls(repository=task["repo"], issue=task["issue"], task_id=task["id"],
                   attempt_id=task["attempt_id"], run_token=task["run_token"],
                   fencing_token=task["fencing_token"], ownership_epoch=task["ownership_epoch"],
                   idempotency_key=task["idempotency_key"], consumer=task["consumer"],
                   parent_task_id=task.get("parent_task_id"), parent_run_token=task.get("parent_run_token"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ResultIdentity":
        if not isinstance(value, Mapping):
            raise ResultContractError("result_identity_not_object")
        optional = {"parent_task_id", "parent_run_token"}
        required = {"repository", "issue", "task_id", "attempt_id", "run_token", "fencing_token",
                    "ownership_epoch", "idempotency_key", "consumer"}
        if set(value) - (required | optional) or not required <= set(value):
            raise ResultContractError("result_identity_schema_invalid")
        return cls(**dict(value))


def _result_status(result: Mapping[str, Any]) -> str:
    status = result.get("status")
    if not isinstance(status, str) or status not in RESULT_STATUSES:
        raise ResultContractError("result_status_invalid")
    return status


def _observed_at(result: Mapping[str, Any]) -> str:
    value = result.get("completed_at") or result.get("observed_at")
    if value is None:
        raise ResultContractError("result_publication_timestamp_missing")
    return _text(value, "result.observed_at", maximum=128)


def canonical_result_for_task(task: Mapping[str, Any], result: Mapping[str, Any], *,
                              verification_state: str = "candidate",
                              producer: str = "agent-stack/bin/agent-task-worker") -> dict[str, Any]:
    """Bind one new publication to the exact host task identity.

    Missing host fields are errors; no attempt counter, epoch, consumer or
    token is invented.  The returned object preserves the worker payload and
    adds a deterministic contract envelope for reconciliation.
    """
    if not isinstance(result, Mapping):
        raise ResultContractError("result_not_object")
    identity = ResultIdentity.from_task(task)
    status = _result_status(result)
    if verification_state not in _VERIFICATION_STATES:
        raise ResultContractError("verification_state_invalid")
    producer = _text(producer, "result.producer", maximum=128)
    if (status == "terminal_unknown") != (verification_state == "terminal_unknown"):
        raise ResultContractError("terminal_unknown_requires_terminal_state")
    existing = result.get("identity")
    if existing is not None and ResultIdentity.from_dict(existing).to_dict() != identity.to_dict():
        raise ResultContractError("result_identity_conflict")
    for field, expected in (("task_id", identity.task_id),
                            ("run_token", identity.run_token),
                            ("fencing_token", identity.fencing_token),
                            ("idempotency_key", identity.idempotency_key)):
        if field in result and result[field] != expected:
            raise ResultContractError(f"result_{field}_conflict")
    payload = dict(result)
    payload["task_id"] = identity.task_id
    payload["run_token"] = identity.run_token
    payload["fencing_token"] = identity.fencing_token
    payload["idempotency_key"] = identity.idempotency_key
    payload["identity"] = identity.to_dict()
    evidence = payload.get("evidence")
    source_payload = dict(payload)
    source_payload.pop("result_contract", None)
    envelope: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "version": RESULT_VERSION,
        "identity": identity.to_dict(),
        "result": {"status": status, "observed_at": _observed_at(payload)},
        "provenance": {"producer": producer, "source_digest": _digest(source_payload)},
        "authority": {
            "issuer": "herdr-host",
            "authority_type": "host_result_publisher",
            "identity_binding": _digest(identity.to_dict()),
            "verification_state": verification_state,
        },
        "recovery": {
            "attempt_state": str(task.get("attempt_state") or "unknown"),
            "delivery_uncertain": task.get("attempt_state") == "delivery_uncertain",
            "terminal_unknown": status == "terminal_unknown",
        },
    }
    if evidence is not None:
        envelope["result"]["result_ref"] = "sha256:" + _digest(evidence)
    if payload.get("completion_bundle_hash"):
        envelope["result"]["completion_evidence_ref"] = _text(payload["completion_bundle_hash"], "completion_bundle_hash")
    if payload.get("blocker"):
        envelope["recovery"]["blocker_reason"] = _text(payload["blocker"], "result.blocker", maximum=2048)
    payload["result_contract"] = envelope
    if len(_canonical(payload)) > _MAX_BYTES:
        raise ResultContractError("result_contract_exceeds_bound")
    return payload


def receipt_payload_for_result(record: Mapping[str, Any], *,
                              expected_identity: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Project a canonical result back to the immutable SDK receipt payload.

    The host result contract is an envelope around the closed eight-field SDK
    payload. Existing WorkResultAuthority receipts bind those original bytes;
    verification must compare the same projection rather than the later
    host-added identity, timestamp and contract fields. Legacy records without
    an envelope remain byte-for-byte compatible.
    """
    if not isinstance(record, Mapping):
        raise ResultContractError("result_not_object")
    if "result_contract" not in record:
        return dict(record)
    if expected_identity is None:
        raise ResultContractError("result_contract_expected_identity_missing")
    validate_result_contract(record, expected_identity=expected_identity)
    missing = [field for field in _RECEIPT_FIELDS if field not in record]
    if missing:
        raise ResultContractError("result_receipt_payload_incomplete")
    return {field: record[field] for field in _RECEIPT_FIELDS}


def validate_result_contract(record: Mapping[str, Any], *, expected_identity: Mapping[str, Any] | None = None) -> ResultIdentity:
    """Validate a canonical envelope without granting completion authority."""
    if not isinstance(record, Mapping) or not isinstance(record.get("result_contract"), Mapping):
        raise ResultContractError("result_contract_missing")
    envelope = record["result_contract"]
    required = {"schema", "version", "identity", "result", "provenance", "authority", "recovery"}
    if set(envelope) != required or envelope["schema"] != RESULT_SCHEMA or envelope["version"] != RESULT_VERSION:
        raise ResultContractError("result_contract_schema_invalid")
    identity = ResultIdentity.from_dict(envelope["identity"])
    if expected_identity is not None and identity.to_dict() != dict(expected_identity):
        raise ResultContractError("result_contract_identity_mismatch")
    if (record.get("identity") != identity.to_dict()
            or record.get("task_id") != identity.task_id
            or record.get("run_token") != identity.run_token
            or record.get("fencing_token") != identity.fencing_token
            or record.get("idempotency_key") != identity.idempotency_key):
        raise ResultContractError("result_contract_binding_mismatch")
    result = envelope["result"]
    if not isinstance(result, Mapping) or set(result) - {"status", "observed_at", "result_ref", "completion_evidence_ref"}:
        raise ResultContractError("result_contract_result_invalid")
    if result.get("status") != record.get("status"):
        raise ResultContractError("result_contract_status_mismatch")
    _text(result.get("observed_at"), "result_contract.observed_at", maximum=128)
    provenance = envelope["provenance"]
    if (not isinstance(provenance, Mapping)
            or set(provenance) != {"producer", "source_digest"}):
        raise ResultContractError("result_contract_provenance_invalid")
    _text(provenance.get("producer"), "result_contract.producer", maximum=128)
    source_payload = dict(record)
    source_payload.pop("result_contract", None)
    if provenance.get("source_digest") != _digest(source_payload):
        raise ResultContractError("result_contract_source_digest_invalid")
    authority = envelope["authority"]
    if not isinstance(authority, Mapping) or set(authority) != {"issuer", "authority_type", "identity_binding", "verification_state"}:
        raise ResultContractError("result_contract_authority_invalid")
    if (authority.get("issuer") != "herdr-host"
            or not isinstance(authority.get("authority_type"), str)
            or authority.get("authority_type") not in _AUTHORITY_TYPES):
        raise ResultContractError("result_contract_authority_untrusted")
    if authority.get("identity_binding") != _digest(identity.to_dict()):
        raise ResultContractError("result_contract_identity_binding_invalid")
    if (not isinstance(authority.get("verification_state"), str)
            or authority.get("verification_state") not in _VERIFICATION_STATES):
        raise ResultContractError("result_contract_verification_state_invalid")
    verification_state = authority["verification_state"]
    status = _result_status(record)
    if ((verification_state == "terminal_unknown") != (status == "terminal_unknown")):
        raise ResultContractError("result_contract_terminal_state_invalid")
    recovery = envelope["recovery"]
    if not isinstance(recovery, Mapping) or not isinstance(recovery.get("delivery_uncertain"), bool) or not isinstance(recovery.get("terminal_unknown"), bool):
        raise ResultContractError("result_contract_recovery_invalid")
    if recovery["terminal_unknown"] and record.get("status") != "terminal_unknown":
        raise ResultContractError("result_contract_terminal_state_invalid")
    if "result_ref" in result:
        evidence = record.get("evidence")
        if evidence is None or result["result_ref"] != "sha256:" + _digest(evidence):
            raise ResultContractError("result_contract_result_ref_invalid")
    if "completion_evidence_ref" in result:
        bundle_hash = record.get("completion_bundle_hash")
        if bundle_hash is None or result["completion_evidence_ref"] != bundle_hash:
            raise ResultContractError("result_contract_completion_ref_invalid")
    return identity

