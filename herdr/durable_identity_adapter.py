"""Strict, read-only compatibility for historical durable task records.

Legacy exports are observations, not an authority.  This module deliberately
requires an explicit host-owned ownership-epoch contract before constructing a
trusted :class:`~herdr.reconciliation.TaskIdentity`; every other shape is
returned as ``UNKNOWN`` by :func:`reconcile_legacy_task`.
"""
from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from .evidence import canonical, digest
from .reconciliation import (
    DecisionStatus,
    DurableEvidence,
    ExternalEvidence,
    ReconciliationDecision,
    ReconciliationError,
    TaskIdentity,
    TaskSnapshot,
    reconcile_task,
)


ADAPTER_VERSION = "durable-identity-adapter-v1"
SUPPORTED_EPOCH_SCHEMA = "host-v1"
SUPPORTED_EPOCH_AUTHORITY = "host"
_MAX_RECORD_BYTES = 2_000_000
_REQUIRED_IDENTITY = (
    "repository", "issue", "task_id", "attempt_id", "run_token",
    "fencing_token", "ownership_epoch", "idempotency_key", "consumer",
)


class DurableIdentityAdapterError(ValueError):
    """A legacy record cannot be safely normalized."""


@dataclass(frozen=True)
class LegacyNormalization:
    """Result of normalizing one immutable legacy object."""

    snapshot: TaskSnapshot
    supported: bool
    reason_code: str | None
    evidence_refs: tuple[str, ...]
    source_digest: str


@dataclass(frozen=True)
class AttemptEvidence:
    """Bounded evidence collected from caller-supplied immutable records."""

    attempts: tuple[Mapping[str, Any], ...]
    results: tuple[Mapping[str, Any], ...]
    authority: tuple[Mapping[str, Any], ...]
    conflicts: tuple[str, ...]
    evidence_refs: tuple[str, ...]


def _bounded_text(value: Any, field: str, *, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise DurableIdentityAdapterError(f"{field}_invalid")
    return value


def _strict_int(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        raise DurableIdentityAdapterError(f"{field}_invalid")
    return value


def _strict_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise DurableIdentityAdapterError(f"{field}_invalid")
    return value


def _raw_identity(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    nested = raw.get("identity")
    return nested if isinstance(nested, Mapping) else raw


def _decode_epoch(raw: Mapping[str, Any]) -> int:
    """Decode only the explicitly host-owned, versioned epoch contract.

    A bare ``epoch``/``ownership_epoch`` field is intentionally not trusted;
    callers cannot elevate an arbitrary legacy object by choosing its value.
    """
    source = _raw_identity(raw)
    schema = raw.get("ownership_epoch_schema", source.get("ownership_epoch_schema"))
    authority = raw.get("ownership_epoch_authority", source.get("ownership_epoch_authority"))
    value = source.get("ownership_epoch", raw.get("ownership_epoch"))
    if isinstance(value, Mapping):
        schema = value.get("schema", schema)
        authority = value.get("authority", authority)
        value = value.get("value")
    if schema != SUPPORTED_EPOCH_SCHEMA or authority != SUPPORTED_EPOCH_AUTHORITY:
        raise DurableIdentityAdapterError("unsupported_legacy_ownership_epoch")
    return _strict_int(value, "ownership_epoch")


def _identity_values(raw: Mapping[str, Any]) -> dict[str, Any]:
    source = _raw_identity(raw)
    values = {
        "repository": source.get("repository", source.get("repo")),
        "issue": source.get("issue"),
        "task_id": source.get("task_id", source.get("id")),
        # `attempts` is a retry count, never an attempt identity.
        "attempt_id": source.get("attempt_id", source.get("attempt_identity")),
        "run_token": source.get("run_token"),
        "fencing_token": source.get("fencing_token"),
        "ownership_epoch": _decode_epoch(raw),
        "idempotency_key": source.get("idempotency_key"),
        "consumer": source.get("consumer"),
        "parent_task_id": source.get("parent_task_id"),
        "parent_run_token": source.get("parent_run_token"),
    }
    for field in _REQUIRED_IDENTITY:
        value = values[field]
        if field in {"attempt_id", "fencing_token", "ownership_epoch"}:
            _strict_int(value, field)
        else:
            _bounded_text(value, field)
    if (values["parent_task_id"] is None) != (values["parent_run_token"] is None):
        raise DurableIdentityAdapterError("parent_identity_incomplete")
    for field in ("parent_task_id", "parent_run_token"):
        if values[field] is not None:
            _bounded_text(values[field], field)
    consumer = values["consumer"]
    repository = values["repository"]
    if consumer.startswith("github:") and consumer[7:] != repository:
        raise DurableIdentityAdapterError("cross_consumer_identity")
    return values


def _unknown_task_id(raw: Any) -> str:
    if isinstance(raw, Mapping):
        candidate = _raw_identity(raw).get("task_id", _raw_identity(raw).get("id"))
        if isinstance(candidate, str) and candidate and len(candidate) <= 512:
            return candidate
    return "legacy-unknown-" + digest(raw)[:32]


def _synthetic_snapshot(raw: Any) -> TaskSnapshot:
    identity = TaskIdentity(
        repository=None, issue=None, task_id=_unknown_task_id(raw), attempt_id=None,
        run_token=None, fencing_token=None, ownership_epoch=None, idempotency_key=None,
        consumer=None,
    )
    return TaskSnapshot(identity, DurableEvidence(status="unknown", provenance="legacy_adapter"))


def _legacy_durable(raw: Mapping[str, Any]) -> DurableEvidence:
    source = raw.get("durable") if isinstance(raw.get("durable"), Mapping) else raw
    source = dict(source)
    # The existing engine performs strict boolean validation.  Validate legacy
    # aliases here so malformed observations become UNKNOWN, never coercions.
    for field in ("submission_intent", "result_exists", "completion_authority",
                  "delivery_uncertain", "terminal_unknown", "attempt_open", "budget_reserved"):
        if field in source and source[field] is not None:
            _strict_bool(source[field], field)
    state = source.get("status", source.get("scheduler_state", source.get("attempt_state")))
    if not isinstance(state, str) or not state or len(state) > 128:
        raise DurableIdentityAdapterError("durable_status_invalid")
    attempt_state = source.get("attempt_state")
    if attempt_state is not None and (not isinstance(attempt_state, str) or len(attempt_state) > 128):
        raise DurableIdentityAdapterError("attempt_state_invalid")
    if attempt_state in {"delivery_uncertain", "unknown_delivery"}:
        source["delivery_uncertain"] = True
    if attempt_state == "terminal_unknown":
        source["terminal_unknown"] = True
        source["delivery_uncertain"] = True
    # Presence is significant: an explicitly supplied null (or any other
    # scalar/list) is not an absent optional field.  Result identity is a
    # trusted boundary and must therefore be an object with a complete,
    # explicitly typed identity.
    if "result_identity" in source:
        _validate_result_identity(source["result_identity"])
    return DurableEvidence.from_mapping(source)


def normalize_legacy_durable_task(raw: Mapping[str, Any]) -> LegacyNormalization:
    """Normalize one legacy row without reading or mutating durable storage."""
    if not isinstance(raw, Mapping):
        raise DurableIdentityAdapterError("legacy_task_not_object")
    source_digest = digest(raw)
    refs = ("legacy-task:" + source_digest,)
    try:
        identity = TaskIdentity(**_identity_values(raw))
        durable = _legacy_durable(raw)
    except (DurableIdentityAdapterError, ReconciliationError, TypeError, ValueError) as exc:
        reason = str(exc) or "legacy_identity_invalid"
        return LegacyNormalization(_synthetic_snapshot(raw), False, reason, refs, source_digest)
    snapshot = TaskSnapshot(identity, durable)
    refs = refs + ("identity:" + digest(identity.to_dict()), "durable:" + digest(durable.to_dict()))
    return LegacyNormalization(snapshot, True, None, tuple(sorted(refs)), source_digest)


def _validate_result_identity(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise DurableIdentityAdapterError("result_identity_not_object")
    if "identity" in record:
        nested = record["identity"]
        if not isinstance(nested, Mapping):
            raise DurableIdentityAdapterError("result_identity_not_object")
        source = nested
    else:
        source = record
    required = ("task_id", "run_token", "attempt_id", "fencing_token", "ownership_epoch",
                "idempotency_key", "consumer")
    for field in required:
        value = source.get(field)
        if field in {"attempt_id", "fencing_token", "ownership_epoch"}:
            _strict_int(value, "result_" + field)
        else:
            _bounded_text(value, "result_" + field)
    for field in ("parent_task_id", "parent_run_token"):
        if field in source and source[field] is not None:
            _bounded_text(source[field], "result_" + field)


def normalize_legacy_result_records(
    records: Iterable[Mapping[str, Any]] | None, *, require_identity: bool = False
) -> tuple[Mapping[str, Any], ...]:
    """Copy bounded result observations; malformed/duplicate identity is rejected."""
    if records is None:
        return ()
    normalized: list[Mapping[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise DurableIdentityAdapterError("legacy_result_not_object")
        if require_identity:
            _validate_result_identity(record)
        normalized.append(dict(record))
    return tuple(normalized)


def collect_authoritative_attempt_evidence(
    task: LegacyNormalization | Mapping[str, Any],
    attempts: Iterable[Mapping[str, Any]] | None = None,
    results: Iterable[Mapping[str, Any]] | None = None,
    authority: Iterable[Mapping[str, Any]] | None = None,
) -> AttemptEvidence:
    """Collect caller-supplied evidence; this function has no authority itself."""
    task_norm = task if isinstance(task, LegacyNormalization) else normalize_legacy_durable_task(task)
    attempt_rows = normalize_legacy_result_records(attempts)
    result_rows = normalize_legacy_result_records(results, require_identity=True)
    authority_rows = normalize_legacy_result_records(authority)
    conflicts: set[str] = set()
    if not task_norm.supported:
        conflicts.add(task_norm.reason_code or "legacy_identity_invalid")
    expected = task_norm.snapshot.identity.to_dict()
    # Attempt/host/audit rows may corroborate identity, but they can never
    # supply a missing field or transfer authority.  Any supplied identity
    # field must agree exactly with the normalized task identity.
    for label, rows in (("attempt", attempt_rows), ("authority", authority_rows)):
        for row in rows:
            source = _raw_identity(row)
            aliases = {
                "repository": ("repository", "repo"), "task_id": ("task_id", "id"),
                "attempt_id": ("attempt_id", "attempt", "attempt_identity"),
            }
            for field, names in aliases.items():
                supplied = next((source[name] for name in names if name in source), None)
                if supplied is not None and supplied != expected.get(field):
                    conflicts.add(f"{label}_identity_conflict")
            for field in ("issue", "run_token", "fencing_token", "idempotency_key", "consumer",
                          "parent_task_id", "parent_run_token", "ownership_epoch"):
                if field in source and source[field] != expected.get(field):
                    conflicts.add(f"{label}_identity_conflict")
    identities = [digest(row.get("identity", row)) for row in result_rows]
    if len(identities) != len(set(identities)):
        conflicts.add("duplicate_result_identity")
    refs = list(task_norm.evidence_refs)
    if attempt_rows:
        refs.append("attempts:" + digest(attempt_rows))
    if result_rows:
        refs.append("results:" + digest(result_rows))
    if authority_rows:
        refs.append("authority:" + digest(authority_rows))
    return AttemptEvidence(attempt_rows, result_rows, authority_rows, tuple(sorted(conflicts)), tuple(sorted(set(refs))))


def build_reconciliation_snapshot(
    task_raw: Mapping[str, Any],
    *,
    attempt_records: Iterable[Mapping[str, Any]] | None = None,
    result_records: Iterable[Mapping[str, Any]] | None = None,
    authority_records: Iterable[Mapping[str, Any]] | None = None,
) -> tuple[LegacyNormalization, AttemptEvidence]:
    """Build an immutable reconciliation input; no durable store access occurs."""
    normalized = normalize_legacy_durable_task(task_raw)
    evidence = collect_authoritative_attempt_evidence(
        normalized, attempt_records, result_records, authority_records
    )
    return normalized, evidence


def _adapter_unknown(normalized: LegacyNormalization, reason: str, refs: Iterable[str]) -> ReconciliationDecision:
    snapshot = normalized.snapshot
    evidence_refs = tuple(sorted(set((*normalized.evidence_refs, *refs))))
    payload = {
        "adapter": ADAPTER_VERSION,
        "task_id": snapshot.identity.task_id,
        "source_digest": normalized.source_digest,
        "reason_code": reason,
        "evidence_refs": evidence_refs,
    }
    return ReconciliationDecision(
        decision_id=digest(payload), task_id=snapshot.identity.task_id or "legacy-unknown",
        status=DecisionStatus.UNKNOWN, reason_code=reason, evidence_refs=evidence_refs,
        identity_match=False, confidence="high", required_action="refresh_authoritative_identity",
        human_gate=False, safe_to_retry=False, policy_version=ADAPTER_VERSION,
        observed_at=snapshot.durable.observed_at,
    )


def _with_adapter_refs(decision: ReconciliationDecision, refs: Iterable[str]) -> ReconciliationDecision:
    merged = tuple(sorted(set((*decision.evidence_refs, *refs))))
    payload = decision.to_dict()
    payload["evidence_refs"] = list(merged)
    payload["adapter"] = ADAPTER_VERSION
    return replace(decision, decision_id=digest(payload), evidence_refs=merged)


def reconcile_legacy_task(
    task_raw: Mapping[str, Any],
    *,
    result_records: Iterable[Mapping[str, Any]] | None = None,
    external: ExternalEvidence | Mapping[str, Any] | None = None,
    attempt_records: Iterable[Mapping[str, Any]] | None = None,
    authority_records: Iterable[Mapping[str, Any]] | None = None,
) -> ReconciliationDecision:
    """Reconcile a legacy row, failing closed until identity provenance is trusted."""
    try:
        normalized, evidence = build_reconciliation_snapshot(
            task_raw, attempt_records=attempt_records, result_records=result_records,
            authority_records=authority_records,
        )
    except DurableIdentityAdapterError as exc:
        normalized = normalize_legacy_durable_task(task_raw)
        return _adapter_unknown(normalized, str(exc), normalized.evidence_refs)
    if not normalized.supported:
        return _adapter_unknown(normalized, normalized.reason_code or "legacy_identity_invalid", evidence.evidence_refs)
    if evidence.conflicts:
        return _adapter_unknown(normalized, "conflicting_legacy_evidence", (*evidence.evidence_refs, *evidence.conflicts))
    decision = reconcile_task(
        normalized.snapshot, evidence.results, external,
        policy_version=ADAPTER_VERSION,
    )
    return _with_adapter_refs(decision, evidence.evidence_refs)


def read_legacy_json(path: str | os.PathLike[str], *, max_bytes: int = _MAX_RECORD_BYTES) -> Mapping[str, Any]:
    """Read one private regular file with bounded TOCTOU checks; never writes."""
    target = Path(path)
    try:
        named_before = target.lstat()
        if stat.S_ISLNK(named_before.st_mode) or not stat.S_ISREG(named_before.st_mode):
            raise DurableIdentityAdapterError("legacy_path_not_regular")
        flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                 | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        fd = os.open(target, flags)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= max_bytes:
                raise DurableIdentityAdapterError("legacy_file_bounds_invalid")
            data = bytearray()
            while len(data) < before.st_size:
                chunk = os.read(fd, min(65536, before.st_size - len(data)))
                if not chunk:
                    raise DurableIdentityAdapterError("legacy_file_truncated")
                data.extend(chunk)
            if os.read(fd, 1):
                raise DurableIdentityAdapterError("legacy_file_overlong")
            after = os.fstat(fd)
            named_after = target.lstat()
            # ``st_ctime_ns`` is creation time on Windows and can differ
            # between a descriptor and its pathname without a replacement;
            # inode/device/size/mode/mtime still provide the bounded identity
            # check while remaining portable to the CI host.
            stamp_fields = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_nlink", "st_size", "st_mtime_ns")
            if os.name != "nt":
                stamp_fields += ("st_ctime_ns",)
            stamp = lambda value: tuple(getattr(value, name) for name in stamp_fields)
            # Compare the pathname observation taken before open with the
            # descriptor identity as well as the post-read observations.  A
            # replacement between lstat() and open() must fail closed even if
            # the replacement is itself a regular, bounded file.
            if (stamp(named_before) != stamp(before)
                    or stamp(before) != stamp(after)
                    or stamp(after) != stamp(named_after)):
                raise DurableIdentityAdapterError("legacy_file_changed_during_read")
        finally:
            os.close(fd)
        value = json.loads(bytes(data))
    except DurableIdentityAdapterError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise DurableIdentityAdapterError("legacy_file_unreadable") from exc
    if not isinstance(value, Mapping):
        raise DurableIdentityAdapterError("legacy_task_not_object")
    return dict(value)

