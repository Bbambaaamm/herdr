"""Offline adapters. Supplied digest pins must come from the caller's trusted channel."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import math
import re

from . import operation_readiness
from .operational_incidents import (
    Detail, IncidentType as Kind, Observation, Scope, Source, State, epoch, require, token,
)
from .reconciliation import TaskSnapshot, reconcile_task
from .taskgraph import _strict_json_loads

MAX_INPUT_BYTES = 65536


def _object(raw, fields, *, pin=None):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_INPUT_BYTES, "invalid input length")
    sha = hashlib.sha256(raw).hexdigest()
    if pin is not None:
        require(pin == sha, "input evidence digest mismatch")
    try:
        result = _strict_json_loads(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        require(False, "invalid JSON evidence")
    require(type(result) is dict and (fields is None or set(result) == fields),
            "unexpected evidence fields")
    return result, sha


def _pinned(raw, pin, fields):
    require(type(pin) is str and len(pin) == 64, "missing upstream verification pin")
    return _object(raw, fields, pin=pin)


def _build_projection(raw, pin):
    data, sha = _pinned(raw, pin, None)
    count = data.get("candidate_count")
    require(type(count) is int and 0 <= count <= 32, "invalid build candidate count")
    if set(data) == {"candidate_count", "visibility"}:
        visibility = data["visibility"]
        require(visibility in ("UNKNOWN", "PARTIAL", "OBSERVED"), "invalid build visibility")
    else:
        require(data.get("schema_version") in ("herdr-build-lifecycle-observation-v1",
                                               "herdr-build-host-evidence-observation-v1")
                and data.get("cleanup_authorized") is False
                and data.get("deletion_performed") is False, "invalid lifecycle observation")
        rows = data.get("candidates")
        require(type(rows) is list and len(rows) == count
                and all(type(row) is dict and row.get("can_delete") is False
                        and row.get("cleanup_authorized") is False for row in rows),
                "invalid lifecycle candidates")
        visibility = "PARTIAL" if any(row.get("measurement_complete") is True for row in rows) else "UNKNOWN"
    return count, visibility, sha


def _observation(source, kind, scope, subject, rev, at, now, state, detail, sha, *, task=None, facts=()):
    return Observation(source, kind, scope, subject, rev, at, now, state, detail, sha, task, facts)


def capacity_snapshot(raw, scope, *, now, max_age, build_input=None):
    """Project already-read publisher bytes. See read_capacity for the host boundary."""
    fields = {"ready", "available_bytes", "required_bytes", "missing_bytes", "margin_bytes",
              "capacity_warning", "checked_at_epoch", "model_calls", "cleanup_performed"}
    row, sha = _object(raw, fields)
    checked = row["checked_at_epoch"]
    require(type(checked) in (int, float) and 0 <= checked <= epoch(now)
            and math.isfinite(checked), "invalid capacity observation time")
    require(type(max_age) is int and 0 < max_age <= 86400, "invalid capacity freshness policy")
    require(type(row["ready"]) is bool and type(row["capacity_warning"]) is bool
            and type(row["model_calls"]) is int and row["model_calls"] == 0
            and row["cleanup_performed"] is False, "invalid capacity report flags")
    for key in ("available_bytes", "required_bytes", "missing_bytes", "margin_bytes"):
        require(type(row[key]) is int and -(2**63) < row[key] < 2**63, "invalid capacity counter")
    expected = operation_readiness.capacity(row["available_bytes"], floor=row["required_bytes"],
                                             start_guard=0, warning_margin=268435456)
    require(all(row[k] == v for k, v in expected.items()), "inconsistent capacity counters")
    refs = (sha,)
    facts = (("available_bytes", row["available_bytes"]), ("required_bytes", row["required_bytes"]))
    if build_input is not None:
        count, visibility, digest = _build_projection(*build_input)
        refs += (digest,)
        facts += (("build_count", count), ("build_visibility", visibility))
    for kind, triggered, detail in (
        (Kind.CAPACITY_BELOW_FLOOR, not row["ready"], Detail.BELOW_FLOOR),
        (Kind.CAPACITY_GROWTH_WARNING, row["ready"] and row["capacity_warning"], Detail.GROWTH_WARNING),
    ):
        if now - checked > max_age:
            state, detail = State.UNKNOWN, Detail.UNKNOWN
        elif triggered:
            state = State.OPEN
        else:
            state, detail = State.RESOLVED, Detail.READY
        yield _observation(Source.CAPACITY, kind, scope, ("root-filesystem",), "local",
                           int(checked), now, state, detail, refs, facts=facts)


def read_capacity(scope, *, now, max_age, build_input=None):
    try:
        raw = operation_readiness.read_capacity_report()
    except (OSError, AttributeError, operation_readiness.ReadinessError):
        return (_observation(Source.CAPACITY, Kind.CAPACITY_BELOW_FLOOR, scope,
                             ("root-filesystem",), "local", now, now, State.UNKNOWN,
                             Detail.UNKNOWN, ()),)
    return tuple(capacity_snapshot(raw, scope, now=now, max_age=max_age, build_input=build_input))


def backup(raw, pin, scope, *, target, revision, now):
    row, sha = _pinned(raw, pin, {"target", "revision", "at", "state"})
    require(row["target"] == target and row["revision"] == revision, "backup identity mismatch")
    states = {
        "AUTH_FAILED": Detail.AUTH_FAILED, "TARGET_UNAVAILABLE": Detail.TARGET_UNAVAILABLE,
        "UPLOAD_UNVERIFIED": Detail.UPLOAD_UNVERIFIED, "RESTORE_UNVERIFIED": Detail.RESTORE_UNVERIFIED,
        "BACKUP_VERIFIED": Detail.BACKUP_VERIFIED, "UNKNOWN": Detail.UNKNOWN,
    }
    require(isinstance(row["state"], str) and row["state"] in states, "invalid backup state")
    detail = states[row["state"]]
    for kind in (Kind.BACKUP_AUTH_FAILURE, Kind.BACKUP_RESTORE_UNVERIFIED):
        if detail is Detail.BACKUP_VERIFIED:
            state = State.RESOLVED
        elif kind is Kind.BACKUP_AUTH_FAILURE:
            state = State.OPEN if detail is Detail.AUTH_FAILED else State.UNKNOWN
        else:
            state = State.UNKNOWN if detail is Detail.UNKNOWN else State.OPEN
        yield _observation(Source.BACKUP, kind, scope, (target,), revision, row["at"],
                           now, state, detail, (sha,))


def github_ci(raw, pin, scope, *, expected_head, expected_pr, now):
    fields = {"repo", "pr", "head", "workflow_id", "run_id", "job_id", "at", "result"}
    row, sha = _pinned(raw, pin, fields)
    require(row["repo"] == scope.project and row["head"] == expected_head
            and row["pr"] == expected_pr, "CI scope or HEAD mismatch")
    require(type(expected_pr) is int and expected_pr > 0, "invalid expected PR")
    require(isinstance(expected_head, str) and re.fullmatch(r"[0-9a-f]{40}", expected_head),
            "invalid CI commit")
    for k in ("pr", "workflow_id", "run_id", "job_id"):
        require(type(row[k]) is int and 0 < row[k] < 2**63, "invalid CI object ID")
    results = {
        "failure": (State.OPEN, Detail.CI_FAILURE), "success": (State.RESOLVED, Detail.CI_SUCCESS),
        "skipped": (State.UNKNOWN, Detail.CI_SKIPPED), "cancelled": (State.UNKNOWN, Detail.CI_CANCELLED),
        "pending": (State.UNKNOWN, Detail.CI_PENDING), "unavailable": (State.UNKNOWN, Detail.UNKNOWN),
    }
    require(isinstance(row["result"], str) and row["result"] in results, "invalid CI result")
    state, detail = results[row["result"]]
    rev = hashlib.sha256(f"{expected_head}:{row['run_id']}:{row['job_id']}".encode()).hexdigest()
    return _observation(Source.CI, Kind.CI_VALIDATION_FAILED, scope,
                        (str(expected_pr), str(row["workflow_id"])), rev,
                        row["at"], now, state, detail, (sha,),
                        facts=(("head", expected_head), ("run_id", row["run_id"]), ("job_id", row["job_id"])))


def worker(raw, pin, scope, *, task_id, expected_fence, now):
    fields = {"task", "at", "heartbeat_missing", "lease_expires", "parent_ack"}
    row, sha = _pinned(raw, pin, fields)
    require(isinstance(row["task"], Mapping), "invalid task snapshot")
    snapshot = TaskSnapshot.from_mapping(row["task"])
    ident = snapshot.identity
    require(ident.consumer == scope.consumer and ident.repository == scope.project
            and ident.task_id == task_id, "worker scope mismatch")
    require(type(expected_fence) is int and 0 <= expected_fence < 2**63, "invalid expected fence")
    require(ident.fencing_token is None or ident.fencing_token < 2**63, "invalid observed fence")
    require(row["heartbeat_missing"] is None or type(row["heartbeat_missing"]) is bool,
            "unknown heartbeat value")
    require(row["parent_ack"] is None or type(row["parent_ack"]) is bool, "unknown ACK value")
    expiration = row["lease_expires"]
    if expiration is not None:
        epoch(expiration)
    at = epoch(row["at"])
    decision = reconcile_task(snapshot)
    durable = snapshot.durable
    revision = str(ident.fencing_token) if ident.fencing_token is not None else "unknown-fence"
    if ident.fencing_token is None:
        kind, state, detail = Kind.FENCING_CONFLICT, State.UNKNOWN, Detail.UNKNOWN
    elif ident.fencing_token != expected_fence:
        kind, state, detail = Kind.FENCING_CONFLICT, State.OPEN, Detail.FENCING_CONFLICT
    elif durable.delivery_uncertain or durable.terminal_unknown or decision.status.value == "RECOVERY_REQUIRED":
        kind, state, detail = Kind.DURABLE_RESULT_UNCERTAIN, State.OPEN, Detail.DELIVERY_UNCERTAIN
    elif row["parent_ack"] is False:
        kind, state, detail = Kind.DURABLE_RESULT_UNCERTAIN, State.OPEN, Detail.PARENT_ACK_PENDING
    elif durable.status in {"done", "failed", "cancelled"} and row["parent_ack"] is True:
        kind, state, detail = Kind.WORKER_STALLED, State.RESOLVED, Detail.TERMINAL
    elif expiration is not None and expiration <= at:
        kind, state, detail = Kind.LEASE_EXPIRED, State.OPEN, Detail.LEASE_EXPIRED
    elif row["heartbeat_missing"] is True:
        kind, state, detail = Kind.WORKER_STALLED, State.OPEN, Detail.HEARTBEAT_MISSING
    elif expiration is not None and row["heartbeat_missing"] is False and row["parent_ack"] is True:
        kind, state, detail = Kind.WORKER_STALLED, State.RESOLVED, Detail.ACTIVE_LEASE
    else:
        kind, state, detail = Kind.WORKER_STALLED, State.UNKNOWN, Detail.UNKNOWN
    return _observation(Source.WORKER, kind, scope, (task_id,), revision, at, now,
                        state, detail, (sha,), task=task_id)
