"""Read-only durable task reconciliation over existing Herdr authorities.

The engine consumes snapshots produced by the existing durable store, result
slots and external evidence adapters.  It never writes durable state, retries
delivery, changes a queue, or grants execution authority.  A decision is a
deterministic, redacted evidence object; callers remain responsible for any
separately authorised human action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping

from .evidence import canonical, digest
from .result_contract import ResultContractError, validate_result_contract


class ReconciliationError(ValueError):
    """Malformed evidence is rejected rather than guessed."""


class DecisionStatus(StrEnum):
    STILL_BLOCKED = "STILL_BLOCKED"
    STALE_BLOCKER = "STALE_BLOCKER"
    RESULT_CONFIRMED = "RESULT_CONFIRMED"
    HUMAN_GATE = "HUMAN_GATE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    UNKNOWN = "UNKNOWN"


_STATUSES = {item.value for item in DecisionStatus}
_REDACTED_KEYS = {"prompt", "secret", "token", "credential", "authorization", "api_key"}


def _text(value: Any, field: str, *, required: bool = True, maximum: int = 512) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ReconciliationError(f"{field} must be bounded text")
    return value


def _integer(value: Any, field: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ReconciliationError(f"{field} must be an integer >= {minimum}")
    return value


def _bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise ReconciliationError(f"{field} must be boolean")
    return value


def _optional_bool(value: Any, field: str, default: bool = False) -> bool:
    if value is None:
        return default
    return _bool(value, field)


def _redact(value: Any) -> Any:
    """Return bounded evidence without prompts, credentials or secret-like keys."""
    if isinstance(value, Mapping):
        return {
            str(key): _redact(item)
            for key, item in value.items()
            if str(key).lower() not in _REDACTED_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    if isinstance(value, str) and len(value) > 1024:
        return value[:1024] + "…"
    return value


@dataclass(frozen=True)
class TaskIdentity:
    repository: str | None
    issue: str | None
    task_id: str | None
    attempt_id: int | None
    run_token: str | None
    fencing_token: int | None
    ownership_epoch: int | Mapping[str, Any] | None
    idempotency_key: str | None
    consumer: str | None
    parent_task_id: str | None = None
    parent_run_token: str | None = None

    def __post_init__(self) -> None:
        for name in ("repository", "issue", "task_id", "run_token", "idempotency_key", "consumer"):
            value = getattr(self, name)
            if value is not None:
                _text(value, f"identity.{name}")
        for name in ("attempt_id", "fencing_token"):
            value = getattr(self, name)
            if value is not None:
                _integer(value, f"identity.{name}")
        if self.ownership_epoch is not None:
            if type(self.ownership_epoch) is int:
                _integer(self.ownership_epoch, "identity.ownership_epoch")
            elif isinstance(self.ownership_epoch, Mapping):
                if set(self.ownership_epoch) != {"version", "run_token", "fencing_token"}:
                    raise ReconciliationError("identity.ownership_epoch is invalid")
                _integer(self.ownership_epoch.get("version"), "identity.ownership_epoch.version", minimum=1)
                _text(self.ownership_epoch.get("run_token"), "identity.ownership_epoch.run_token")
                _integer(self.ownership_epoch.get("fencing_token"), "identity.ownership_epoch.fencing_token", minimum=1)
            else:
                raise ReconciliationError("identity.ownership_epoch is invalid")
        if self.parent_task_id is not None:
            _text(self.parent_task_id, "identity.parent_task_id")
        if self.parent_run_token is not None:
            _text(self.parent_run_token, "identity.parent_run_token")
        if (self.parent_task_id is None) != (self.parent_run_token is None):
            raise ReconciliationError("parent task/run identity must be complete")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskIdentity":
        if not isinstance(value, Mapping):
            raise ReconciliationError("task identity must be an object")
        return cls(
            repository=value.get("repository", value.get("repo")),
            issue=value.get("issue"),
            task_id=value.get("task_id", value.get("id")),
            attempt_id=value.get("attempt_id", value.get("attempt")),
            run_token=value.get("run_token"),
            fencing_token=value.get("fencing_token"),
            ownership_epoch=value.get("ownership_epoch"),
            idempotency_key=value.get("idempotency_key"),
            consumer=value.get("consumer"),
            parent_task_id=value.get("parent_task_id"),
            parent_run_token=value.get("parent_run_token"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "issue": self.issue,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "run_token": self.run_token,
            "fencing_token": self.fencing_token,
            "ownership_epoch": self.ownership_epoch,
            "idempotency_key": self.idempotency_key,
            "consumer": self.consumer,
            "parent_task_id": self.parent_task_id,
            "parent_run_token": self.parent_run_token,
        }


@dataclass(frozen=True)
class DurableEvidence:
    status: str
    blocker: str | None = None
    submission_intent: bool = False
    result_exists: bool = False
    result_identity: Mapping[str, Any] | None = None
    result_status: str | None = None
    completion_authority: bool = False
    recovery_state: str | None = None
    superseded_by: str | None = None
    observed_at: str = "1970-01-01T00:00:00Z"
    provenance: str = "durable_snapshot"
    delivery_uncertain: bool = False
    terminal_unknown: bool = False
    attempt_open: bool = False
    budget_reserved: bool = False

    def __post_init__(self) -> None:
        _text(self.status, "durable.status")
        if self.blocker is not None:
            _text(self.blocker, "durable.blocker")
        for name in ("submission_intent", "result_exists", "completion_authority",
                     "delivery_uncertain", "terminal_unknown", "attempt_open", "budget_reserved"):
            _bool(getattr(self, name), f"durable.{name}")
        for name in ("result_status", "recovery_state", "superseded_by", "observed_at", "provenance"):
            if getattr(self, name) is not None:
                _text(getattr(self, name), f"durable.{name}")
        if self.result_identity is not None and not isinstance(self.result_identity, Mapping):
            raise ReconciliationError("durable.result_identity must be an object")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DurableEvidence":
        if not isinstance(value, Mapping):
            raise ReconciliationError("durable evidence must be an object")
        state = str(value.get("status", value.get("scheduler_state", value.get("attempt_state", ""))))
        recovery = value.get("recovery_state", value.get("watchdog_blocker"))
        uncertain = _optional_bool(value.get("delivery_uncertain"), "durable.delivery_uncertain", state == "delivery_uncertain")
        if state in {"terminal_unknown", "unknown_delivery"}:
            uncertain = True
        result = value.get("result_identity")
        if result is None and isinstance(value.get("result"), Mapping):
            result = value["result"].get("identity")
        return cls(
            status=state,
            blocker=value.get("blocker", value.get("last_error")),
            submission_intent=_optional_bool(value.get("submission_intent", value.get("submitted")), "durable.submission_intent"),
            result_exists=_optional_bool(value.get("result_exists"), "durable.result_exists", value.get("result") is not None),
            result_identity=result,
            result_status=value.get("result_status", value.get("result", {}).get("status") if isinstance(value.get("result"), Mapping) else None),
            completion_authority=_optional_bool(value.get("completion_authority", value.get("result", {}).get("authoritative") if isinstance(value.get("result"), Mapping) else None), "durable.completion_authority"),
            recovery_state=recovery,
            superseded_by=value.get("superseded_by"),
            observed_at=str(value.get("observed_at", "1970-01-01T00:00:00Z")),
            provenance=str(value.get("provenance", "durable_snapshot")),
            delivery_uncertain=uncertain,
            terminal_unknown=_optional_bool(value.get("terminal_unknown"), "durable.terminal_unknown", state == "terminal_unknown"),
            attempt_open=_optional_bool(value.get("attempt_open"), "durable.attempt_open", state in {"dispatching", "accepted", "working", "verifying"}),
            budget_reserved=_optional_bool(value.get("budget_reserved"), "durable.budget_reserved"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _redact({
            "status": self.status, "blocker": self.blocker,
            "submission_intent": self.submission_intent, "result_exists": self.result_exists,
            "result_identity": dict(self.result_identity) if self.result_identity is not None else None,
            "result_status": self.result_status, "completion_authority": self.completion_authority,
            "recovery_state": self.recovery_state, "superseded_by": self.superseded_by,
            "observed_at": self.observed_at, "provenance": self.provenance,
            "delivery_uncertain": self.delivery_uncertain, "terminal_unknown": self.terminal_unknown,
            "attempt_open": self.attempt_open, "budget_reserved": self.budget_reserved,
        })


@dataclass(frozen=True)
class ExternalEvidence:
    issue_state: str | None = None
    pr_state: str | None = None
    review_state: str | None = None
    required_ci: str | bool | None = None
    dependency_state: str | None = None
    available: bool = True
    error_code: str | None = None
    observed_at: str = "1970-01-01T00:00:00Z"
    provenance: str = "github_snapshot"

    def __post_init__(self) -> None:
        for name in ("issue_state", "pr_state", "review_state", "dependency_state", "error_code", "observed_at", "provenance"):
            if getattr(self, name) is not None:
                _text(getattr(self, name), f"external.{name}")
        _bool(self.available, "external.available")
        if self.required_ci is not None and not isinstance(self.required_ci, (str, bool)):
            raise ReconciliationError("external.required_ci must be text or boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ExternalEvidence | None":
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise ReconciliationError("external evidence must be an object")
        return cls(
            issue_state=value.get("issue_state", value.get("issue")),
            pr_state=value.get("pr_state", value.get("pull_request")),
            review_state=value.get("review_state", value.get("review")),
            required_ci=value.get("required_ci", value.get("ci")),
            dependency_state=value.get("dependency_state", value.get("dependency")),
            available=_optional_bool(value.get("available"), "external.available", True), error_code=value.get("error_code"),
            observed_at=str(value.get("observed_at", "1970-01-01T00:00:00Z")),
            provenance=str(value.get("provenance", "github_snapshot")),
        )

    def to_dict(self) -> dict[str, Any]:
        return _redact({
            "issue_state": self.issue_state, "pr_state": self.pr_state,
            "review_state": self.review_state, "required_ci": self.required_ci,
            "dependency_state": self.dependency_state, "available": self.available,
            "error_code": self.error_code, "observed_at": self.observed_at,
            "provenance": self.provenance,
        })


@dataclass(frozen=True)
class TaskSnapshot:
    identity: TaskIdentity
    durable: DurableEvidence

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskSnapshot":
        if not isinstance(value, Mapping):
            raise ReconciliationError("task snapshot must be an object")
        identity_source = value.get("identity", value)
        durable_source = value.get("durable", value)
        return cls(TaskIdentity.from_mapping(identity_source), DurableEvidence.from_mapping(durable_source))


@dataclass(frozen=True)
class ReconciliationDecision:
    decision_id: str
    task_id: str
    status: DecisionStatus
    reason_code: str
    evidence_refs: tuple[str, ...]
    identity_match: bool
    confidence: str
    required_action: str
    human_gate: bool
    safe_to_retry: bool
    policy_version: str
    observed_at: str

    def __post_init__(self) -> None:
        _text(self.decision_id, "decision_id", maximum=64)
        _text(self.task_id, "task_id")
        object.__setattr__(self, "status", DecisionStatus(self.status))
        for name in ("reason_code", "confidence", "required_action", "policy_version", "observed_at"):
            _text(getattr(self, name), f"decision.{name}")
        if self.confidence not in {"high", "medium", "low"}:
            raise ReconciliationError("decision.confidence is invalid")
        if type(self.identity_match) is not bool or type(self.human_gate) is not bool:
            raise ReconciliationError("decision booleans are invalid")
        if self.safe_to_retry is not False:
            raise ReconciliationError("reconciliation retry authority is disabled")
        if not isinstance(self.evidence_refs, tuple) or any(not isinstance(x, str) for x in self.evidence_refs):
            raise ReconciliationError("decision evidence_refs must be text tuple")

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id, "task_id": self.task_id,
            "status": self.status.value, "reason_code": self.reason_code,
            "evidence_refs": list(self.evidence_refs), "identity_match": self.identity_match,
            "confidence": self.confidence, "required_action": self.required_action,
            "human_gate": self.human_gate, "safe_to_retry": False,
            "policy_version": self.policy_version, "observed_at": self.observed_at,
        }


def _result_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    identity = record.get("identity") if isinstance(record.get("identity"), Mapping) else record
    return {
        "task_id": identity.get("task_id", identity.get("id")),
        "run_token": identity.get("run_token"),
        "attempt_id": identity.get("attempt_id", identity.get("attempt")),
        "fencing_token": identity.get("fencing_token"),
        "ownership_epoch": identity.get("ownership_epoch"),
        "idempotency_key": identity.get("idempotency_key"),
        "consumer": identity.get("consumer"),
        "parent_task_id": identity.get("parent_task_id"),
        "parent_run_token": identity.get("parent_run_token"),
    }


def _valid_result_identity(identity: Mapping[str, Any]) -> bool:
    required_text = ("task_id", "run_token", "idempotency_key", "consumer")
    if any(not isinstance(identity.get(field), str) or not identity.get(field) for field in required_text):
        return False
    for field in ("attempt_id", "fencing_token"):
        if type(identity.get(field)) is not int or identity[field] < 0:
            return False
    epoch = identity.get("ownership_epoch")
    if type(epoch) is int:
        if epoch < 0:
            return False
    elif isinstance(epoch, Mapping):
        if set(epoch) != {"version", "run_token", "fencing_token"}:
            return False
        if (type(epoch.get("version")) is not int or epoch["version"] < 1
                or not isinstance(epoch.get("run_token"), str) or not epoch["run_token"]
                or type(epoch.get("fencing_token")) is not int or epoch["fencing_token"] < 1
                or epoch["run_token"] != identity.get("run_token")
                or epoch["fencing_token"] != identity.get("fencing_token")):
            return False
    else:
        return False
    for field in ("parent_task_id", "parent_run_token"):
        if identity.get(field) is not None and not isinstance(identity[field], str):
            return False
    return True


def _record_authority(record: Mapping[str, Any]) -> bool | None:
    values = []
    for field in ("completion_authority", "authoritative"):
        if field in record:
            if type(record[field]) is not bool:
                return None
            values.append(record[field])
    if len(values) > 1 and values[0] != values[1]:
        return None
    return values[0] if values else False


def _stable_records(records: Iterable[Mapping[str, Any]]) -> list[Any]:
    return sorted((_redact(record) for record in records), key=lambda record: canonical(record))


def _matches(expected: TaskIdentity, record: Mapping[str, Any]) -> bool:
    actual = _result_identity(record)
    if not _valid_result_identity(actual):
        return False
    for field in ("task_id", "run_token", "attempt_id", "fencing_token", "ownership_epoch", "idempotency_key"):
        if actual[field] != getattr(expected, field):
            return False
    for field in ("consumer", "parent_task_id", "parent_run_token"):
        if actual[field] != getattr(expected, field):
            return False
    return True


def _identity_complete(identity: TaskIdentity) -> bool:
    return bool(identity.task_id and identity.run_token and identity.idempotency_key
                and identity.attempt_id is not None and identity.fencing_token is not None
                and identity.fencing_token >= 0 and identity.ownership_epoch is not None
                and identity.consumer)


def _reason_and_action(durable: DurableEvidence) -> tuple[str, str, bool]:
    blocker = (durable.blocker or "").lower()
    if any(word in blocker for word in ("human", "approval", "credential", "privilege", "authorize", "manual_gate")):
        return "human_approval_required", "obtain_human_approval", True
    return "durable_blocker_active", "inspect_blocker", False


def _decision(snapshot: TaskSnapshot, status: DecisionStatus, reason: str, refs: Iterable[str],
              *, identity_match: bool, confidence: str, action: str, human_gate: bool,
              policy_version: str, observed_at: str) -> ReconciliationDecision:
    evidence_refs = tuple(sorted(set(refs)))
    payload = {
        "task_id": snapshot.identity.task_id,
        "status": status.value,
        "reason_code": reason,
        "identity": digest(snapshot.identity.to_dict()),
        "durable": digest(snapshot.durable.to_dict()),
        "evidence_refs": evidence_refs,
        "policy_version": policy_version,
    }
    return ReconciliationDecision(
        decision_id=digest(payload), task_id=snapshot.identity.task_id, status=status,
        reason_code=reason, evidence_refs=evidence_refs, identity_match=identity_match,
        confidence=confidence, required_action=action, human_gate=human_gate,
        safe_to_retry=False, policy_version=policy_version, observed_at=observed_at,
    )


def reconcile_task(snapshot: TaskSnapshot | Mapping[str, Any], result_records: Iterable[Mapping[str, Any]] = (),
                   external: ExternalEvidence | Mapping[str, Any] | None = None, *,
                   policy_version: str = "reconciliation-v1", observed_at: str | None = None) -> ReconciliationDecision:
    """Classify one immutable snapshot without performing any side effect."""
    if not isinstance(snapshot, TaskSnapshot):
        snapshot = TaskSnapshot.from_mapping(snapshot)
    ext = external if isinstance(external, ExternalEvidence) else ExternalEvidence.from_mapping(external)
    records = tuple(result_records or ())
    if any(not isinstance(record, Mapping) for record in records):
        raise ReconciliationError("result records must be objects")
    refs = ["identity:" + digest(snapshot.identity.to_dict()),
            "durable:" + digest(snapshot.durable.to_dict())]
    if ext is not None:
        refs.append("external:" + digest(ext.to_dict()))
    obs = observed_at or snapshot.durable.observed_at or (ext.observed_at if ext else "1970-01-01T00:00:00Z")
    if not _identity_complete(snapshot.identity):
        return _decision(snapshot, DecisionStatus.UNKNOWN, "incomplete_attempt_identity", refs,
                         identity_match=False, confidence="high", action="refresh_authoritative_identity",
                         human_gate=False, policy_version=policy_version, observed_at=obs)

    invalid_contract_refs = []
    for record in records:
        if "result_contract" not in record:
            continue
        try:
            validate_result_contract(record)
        except ResultContractError:
            invalid_contract_refs.append("result_contract:" + digest(_redact(record.get("result_contract"))))
    if invalid_contract_refs:
        refs.extend(sorted(set(invalid_contract_refs)))
        return _decision(snapshot, DecisionStatus.UNKNOWN, "result_contract_invalid", refs,
                         identity_match=False, confidence="high", action="refresh_result_evidence",
                         human_gate=False, policy_version=policy_version, observed_at=obs)

    matching = [record for record in records if _matches(snapshot.identity, record)]
    same_task = [record for record in records if _result_identity(record).get("task_id") == snapshot.identity.task_id]
    if len(same_task) > 1:
        refs.append("result_records:" + digest(_stable_records(same_task)))
        return _decision(snapshot, DecisionStatus.UNKNOWN, "conflicting_or_duplicate_results", refs,
                         identity_match=False, confidence="high", action="reconcile_duplicate_results",
                         human_gate=False, policy_version=policy_version, observed_at=obs)
    completed = [record for record in matching if str(record.get("status", record.get("result_status", ""))).lower() in {"completed", "done", "accepted"}]
    if len(matching) > 1:
        return _decision(snapshot, DecisionStatus.UNKNOWN, "conflicting_or_duplicate_results", refs,
                         identity_match=False, confidence="high", action="reconcile_duplicate_results",
                         human_gate=False, policy_version=policy_version, observed_at=obs)

    uncertain = snapshot.durable.delivery_uncertain or snapshot.durable.terminal_unknown or snapshot.durable.recovery_state in {
        "delivery_uncertain_requires_recovery", "delivery_uncertain", "terminal_unknown", "recovery_required"
    }
    if uncertain:
        return _decision(snapshot, DecisionStatus.RECOVERY_REQUIRED, "unknown_delivery_requires_reconciliation", refs,
                         identity_match=bool(matching), confidence="high", action="operator_reconciliation",
                         human_gate=False, policy_version=policy_version, observed_at=obs)

    if completed:
        record = completed[0]
        authoritative = _record_authority(record)
        result_identity = _result_identity(record)
        if authoritative is not True or not snapshot.durable.completion_authority:
            return _decision(snapshot, DecisionStatus.UNKNOWN, "completion_authority_unproven", refs,
                             identity_match=True, confidence="high", action="verify_host_completion_authority",
                             human_gate=False, policy_version=policy_version, observed_at=obs)
        if snapshot.durable.result_identity is not None:
            durable_identity = _result_identity(snapshot.durable.result_identity)
            if not _valid_result_identity(durable_identity) or durable_identity != result_identity:
                return _decision(snapshot, DecisionStatus.UNKNOWN, "durable_result_identity_conflict", refs,
                                 identity_match=True, confidence="high", action="reconcile_result_evidence",
                                 human_gate=False, policy_version=policy_version, observed_at=obs)
        if snapshot.durable.result_status is not None and snapshot.durable.result_status.lower() not in {"completed", "done", "accepted"}:
            return _decision(snapshot, DecisionStatus.UNKNOWN, "durable_result_status_conflict", refs,
                             identity_match=True, confidence="high", action="reconcile_result_evidence",
                             human_gate=False, policy_version=policy_version, observed_at=obs)
        if snapshot.durable.status.lower() not in {"completed", "done", "accepted"}:
            return _decision(snapshot, DecisionStatus.UNKNOWN, "result_durable_state_conflict", refs,
                             identity_match=True, confidence="high", action="reconcile_durable_state",
                             human_gate=False, policy_version=policy_version, observed_at=obs)
        refs.append("result:" + digest(_redact({"identity": result_identity, "record": record})))
        return _decision(snapshot, DecisionStatus.RESULT_CONFIRMED, "authoritative_matching_result", refs,
                         identity_match=True, confidence="high", action="explicit_acceptance_review",
                         human_gate=False, policy_version=policy_version, observed_at=obs)

    if snapshot.durable.result_exists and not matching:
        refs.append("result_records:" + digest(_stable_records(records)))
        return _decision(snapshot, DecisionStatus.UNKNOWN, "result_identity_mismatch", refs,
                         identity_match=False, confidence="high", action="refresh_result_evidence",
                         human_gate=False, policy_version=policy_version, observed_at=obs)

    base_reason, base_action, base_gate = _reason_and_action(snapshot.durable)
    if ext is not None:
        if base_gate:
            return _decision(snapshot, DecisionStatus.HUMAN_GATE, base_reason, refs, identity_match=True,
                             confidence="high", action=base_action, human_gate=True,
                             policy_version=policy_version, observed_at=obs)
        if not ext.available:
            return _decision(snapshot, DecisionStatus.UNKNOWN, "external_evidence_unavailable", refs,
                             identity_match=True, confidence="high", action="refresh_external_evidence",
                             human_gate=False, policy_version=policy_version, observed_at=obs)
        issue = (ext.issue_state or "").lower()
        pr = (ext.pr_state or "").lower()
        if (issue in {"closed", "completed"} or pr in {"merged", "closed"}) and snapshot.durable.status.lower() in {"blocked", "failed", "pending"}:
            return _decision(snapshot, DecisionStatus.STALE_BLOCKER, "external_completion_supersedes_blocker", refs,
                             identity_match=True, confidence="medium", action="refresh_blocker_evidence",
                             human_gate=False, policy_version=policy_version, observed_at=obs)
        if issue in {"open", "reopened"} and snapshot.durable.status.lower() in {"done", "completed", "closed"}:
            return _decision(snapshot, DecisionStatus.STALE_BLOCKER, "durable_completion_conflicts_with_open_issue", refs,
                             identity_match=True, confidence="medium", action="refresh_durable_evidence",
                             human_gate=False, policy_version=policy_version, observed_at=obs)
        if ext.required_ci in {False, "failed", "failure", "red"}:
            return _decision(snapshot, DecisionStatus.STILL_BLOCKED, "required_ci_not_green", refs,
                             identity_match=True, confidence="high", action="repair_ci_or_refresh", human_gate=False,
                             policy_version=policy_version, observed_at=obs)
        if ext.review_state and ext.review_state.lower() in {"stale", "changes_requested", "pending"}:
            return _decision(snapshot, DecisionStatus.STILL_BLOCKED, "review_gate_incomplete", refs,
                             identity_match=True, confidence="high", action="complete_review_gate", human_gate=False,
                             policy_version=policy_version, observed_at=obs)

    if snapshot.durable.submission_intent and not matching:
        return _decision(snapshot, DecisionStatus.RECOVERY_REQUIRED, "submission_without_matching_result", refs,
                         identity_match=True, confidence="high", action="reconcile_submission", human_gate=False,
                         policy_version=policy_version, observed_at=obs)
    if base_gate:
        return _decision(snapshot, DecisionStatus.HUMAN_GATE, base_reason, refs, identity_match=True,
                         confidence="high", action=base_action, human_gate=True, policy_version=policy_version, observed_at=obs)
    if snapshot.durable.status.lower() in {"blocked", "failed", "pending", "queued", "waiting"}:
        return _decision(snapshot, DecisionStatus.STILL_BLOCKED, base_reason, refs, identity_match=True,
                         confidence="high", action=base_action, human_gate=False, policy_version=policy_version, observed_at=obs)
    return _decision(snapshot, DecisionStatus.UNKNOWN, "unsupported_durable_state", refs, identity_match=True,
                     confidence="high", action="refresh_authoritative_snapshot", human_gate=False,
                     policy_version=policy_version, observed_at=obs)


def reconcile_snapshot(tasks: Iterable[TaskSnapshot | Mapping[str, Any]],
                       results_by_task: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
                       external_by_task: Mapping[str, ExternalEvidence | Mapping[str, Any]] | None = None,
                       *, policy_version: str = "reconciliation-v1") -> tuple[ReconciliationDecision, ...]:
    results_by_task = results_by_task or {}
    external_by_task = external_by_task or {}
    snapshots = [task if isinstance(task, TaskSnapshot) else TaskSnapshot.from_mapping(task) for task in tasks]
    return tuple(reconcile_task(task, results_by_task.get(task.identity.task_id, ()),
                                external_by_task.get(task.identity.task_id), policy_version=policy_version)
                 for task in sorted(snapshots, key=lambda item: item.identity.task_id))


def build_report(decisions: Iterable[ReconciliationDecision], *, replay_status: str = "NOT_RUN") -> dict[str, Any]:
    rows = [item.to_dict() if isinstance(item, ReconciliationDecision) else item for item in decisions]
    rows = sorted(rows, key=lambda item: item["task_id"])
    counts = {status.value: 0 for status in DecisionStatus}
    for row in rows:
        status = row["status"]
        if status not in _STATUSES:
            raise ReconciliationError("report contains unknown decision status")
        counts[status] += 1
    if sum(counts.values()) != len(rows):
        raise ReconciliationError("classification count does not match rows")
    return {
        "schema": "herdr-reconciliation-report-v1",
        "replay_status": replay_status,
        "decision_count": len(rows),
        "counts": counts,
        "safe_to_retry": False,
        "rows": rows,
    }


def normalize_task_snapshot(raw: Mapping[str, Any]) -> TaskSnapshot:
    """Normalize one read-only durable-store row; no store access is performed."""
    return TaskSnapshot.from_mapping(raw)


def normalize_external_evidence(raw: Mapping[str, Any] | None) -> ExternalEvidence | None:
    """Normalize a caller-supplied GitHub snapshot without granting authority."""
    return ExternalEvidence.from_mapping(raw)

