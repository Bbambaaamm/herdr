"""Deterministic incident projection over bounded, admitted observations."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from enum import StrEnum
import json
import re

from .evidence import canonical, digest

SCHEMA = "herdr-operational-incidents-1"
MAX_EVENTS = 4096
_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}")
_CHECK_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_CHECK_ID = re.compile(r"[1-9][0-9]{0,18}")
_CHECK_NAME_MAX = 128
_SHA = re.compile(r"[a-f0-9]{64}")
_REPO = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}/[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}")


class IncidentError(ValueError):
    """Invalid evidence or conflicting observations."""


class Source(StrEnum):
    CAPACITY = "capacity-watch"
    BACKUP = "backup-report"
    CI = "github-ci"
    WORKER = "worker-snapshot"


class IncidentType(StrEnum):
    CAPACITY_BELOW_FLOOR = "CAPACITY_BELOW_FLOOR"
    CAPACITY_GROWTH_WARNING = "CAPACITY_GROWTH_WARNING"
    BACKUP_AUTH_FAILURE = "BACKUP_AUTH_FAILURE"
    BACKUP_RESTORE_UNVERIFIED = "BACKUP_RESTORE_UNVERIFIED"
    CI_VALIDATION_FAILED = "CI_VALIDATION_FAILED"
    WORKER_STALLED = "WORKER_STALLED"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    FENCING_CONFLICT = "FENCING_CONFLICT"
    DURABLE_RESULT_UNCERTAIN = "DURABLE_RESULT_UNCERTAIN"


class State(StrEnum):
    OPEN = "OPEN"
    UNKNOWN = "UNKNOWN"
    RESOLVED = "RESOLVED"


SOURCE_TYPES = {
    Source.CAPACITY: {IncidentType.CAPACITY_BELOW_FLOOR, IncidentType.CAPACITY_GROWTH_WARNING},
    Source.BACKUP: {IncidentType.BACKUP_AUTH_FAILURE, IncidentType.BACKUP_RESTORE_UNVERIFIED},
    Source.CI: {IncidentType.CI_VALIDATION_FAILED},
    Source.WORKER: {
        IncidentType.WORKER_STALLED, IncidentType.LEASE_EXPIRED,
        IncidentType.FENCING_CONFLICT, IncidentType.DURABLE_RESULT_UNCERTAIN,
    },
}


def require(condition, message):
    if not condition:
        raise IncidentError(message)


def token(value, pattern=_NAME):
    require(isinstance(value, str) and pattern.fullmatch(value), "invalid identifier")
    return value


def epoch(value):
    require(type(value) is int and 0 <= value <= 253402300799, "invalid timestamp")
    return value


def check_identity(scope, subject, job_name):
    """Stable identity of one *defined* CI check.

    Derived from the scope, the pull request, the workflow definition and the
    job's defined name only — never from the per-run ``job_id``/``run_id`` (those
    fragment one red PR into N records) and never from the per-run evidence
    digest (it changes on every run).  A re-run of the same check keeps its
    identity, and two different checks cannot collide.

    A full SHA-256 over the canonical inputs is used rather than a readable
    slug: job names are free text, so any rendering ("unit tests" vs
    "unit-tests", or two long names sharing a prefix) can collide, while a
    digest cannot.  The pull request and workflow are required to be canonical
    positive integers, which is what makes the bridge's ``refs/pull/<pr>/head``
    well formed by construction.
    """
    require(type(scope) is Scope, "invalid check scope")
    # Exactly two parts: the pull request and the workflow definition.  Extra
    # parts would be silently dropped from the identity, so two hand-built
    # observations could share one check_id and one defect fingerprint.
    require(type(subject) is tuple and len(subject) == 2, "invalid check subject")
    pr, workflow = subject[0], subject[1]
    require(type(pr) is str and _CHECK_ID.fullmatch(pr) is not None,
            "invalid check pull request")
    require(type(workflow) is str and _CHECK_ID.fullmatch(workflow) is not None,
            "invalid check workflow")
    require(type(job_name) is str and 0 < len(job_name) <= _CHECK_NAME_MAX,
            "invalid CI check name")
    value = digest([SCHEMA, "ci-check", asdict(scope), pr, workflow, job_name])
    require(_CHECK_TOKEN.fullmatch(value) is not None, "invalid CI check identity")
    return value


def timestamp(seconds):
    return datetime.fromtimestamp(epoch(seconds), UTC).isoformat()


@dataclass(frozen=True)
class Scope:
    consumer: str
    project: str

    def __post_init__(self):
        token(self.consumer)
        token(self.project, _REPO)


class Detail(StrEnum):
    BELOW_FLOOR = "BELOW_FLOOR"
    GROWTH_WARNING = "GROWTH_WARNING"
    READY = "READY"
    AUTH_FAILED = "AUTH_FAILED"
    TARGET_UNAVAILABLE = "TARGET_UNAVAILABLE"
    UPLOAD_UNVERIFIED = "UPLOAD_UNVERIFIED"
    RESTORE_UNVERIFIED = "RESTORE_UNVERIFIED"
    BACKUP_VERIFIED = "BACKUP_VERIFIED"
    UNKNOWN = "UNKNOWN"
    CI_FAILURE = "CI_FAILURE"
    CI_SUCCESS = "CI_SUCCESS"
    CI_SKIPPED = "CI_SKIPPED"
    CI_CANCELLED = "CI_CANCELLED"
    CI_PENDING = "CI_PENDING"
    ACTIVE_LEASE = "ACTIVE_LEASE"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    FENCING_CONFLICT = "FENCING_CONFLICT"
    HEARTBEAT_MISSING = "HEARTBEAT_MISSING"
    DELIVERY_UNCERTAIN = "DELIVERY_UNCERTAIN"
    PARENT_ACK_PENDING = "PARENT_ACK_PENDING"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True)
class Observation:
    source: Source
    kind: IncidentType
    scope: Scope
    subject: tuple[str, ...]
    revision: str
    event_at: int
    observed_at: int
    state: State
    detail: Detail
    evidence_sha256: tuple[str, ...]
    task_id: str | None = None
    facts: tuple[tuple[str, int | str], ...] = ()

    def __post_init__(self):
        require(type(self.source) is Source and type(self.kind) is IncidentType
                and self.kind in SOURCE_TYPES[self.source] and type(self.scope) is Scope
                and type(self.state) is State and type(self.detail) is Detail, "invalid observation type")
        require(type(self.subject) is tuple and 1 <= len(self.subject) <= 4, "invalid subject")
        for part in self.subject:
            token(part)
        token(self.revision)
        require(epoch(self.event_at) <= epoch(self.observed_at), "event occurs after observation")
        require(type(self.evidence_sha256) is tuple and len(self.evidence_sha256) <= 4
                and (self.evidence_sha256 or self.state is State.UNKNOWN), "missing or excessive evidence")
        for ref in self.evidence_sha256:
            token(ref, _SHA)
        if self.task_id is not None:
            require(self.source is Source.WORKER, "unexpected task identity")
            token(self.task_id)
        allowed = {
            Source.CAPACITY: {"available_bytes", "required_bytes", "build_count", "build_visibility"},
            Source.CI: {"head", "run_id", "job_id", "job_name"},
            Source.BACKUP: set(), Source.WORKER: set(),
        }[self.source]
        require(type(self.facts) is tuple and len(self.facts) <= len(allowed), "invalid facts")
        seen = set()
        for fact in self.facts:
            require(type(fact) is tuple and len(fact) == 2, "invalid fact")
            key, value = fact
            require(type(key) is str and key in allowed and key not in seen, "unexpected fact")
            seen.add(key)
            if key == "build_visibility":
                require(value in ("UNKNOWN", "PARTIAL", "OBSERVED"), "invalid visibility")
            elif key == "head":
                token(value, re.compile(r"[a-f0-9]{40}"))
            elif key == "job_name":
                require(type(value) is str and 0 < len(value) <= _CHECK_NAME_MAX,
                        "invalid CI check name")
            else:
                require(type(value) is int and 0 <= value < 2**63, "invalid fact counter")

    @property
    def correlation_id(self):
        return digest([SCHEMA, self.source, asdict(self.scope), self.subject])

    @property
    def incident_id(self):
        return digest([self.correlation_id, self.kind, self.revision])

    @property
    def check_id(self):
        """Stable identity of the *defined* CI check (CI observations only).

        ``incident_id`` and ``correlation_id`` are intentionally untouched: the
        first stays the per-source state transition, the second the whole
        (source, scope, subject) group.  Neither identifies one failing check.
        """
        if self.source is not Source.CI:
            raise IncidentError("check identity requires a CI observation")
        facts = dict(self.facts)
        if "job_name" not in facts:
            raise IncidentError("CI observation lacks a stable check name")
        return check_identity(self.scope, self.subject, facts["job_name"])

    @property
    def event_id(self):
        value = asdict(self)
        del value["observed_at"]
        return digest(value)


@dataclass(frozen=True)
class OperationalIncident:
    current: Observation
    history: tuple[Observation, ...]

    def to_dict(self):
        current = self.current
        payload = asdict(current)
        payload.update(schema_version=SCHEMA, incident_id=current.incident_id,
                       correlation_id=current.correlation_id, deduplication_id=current.event_id,
                       event_at=timestamp(current.event_at), observed_at=timestamp(current.observed_at),
                       severity="warning" if current.kind is IncidentType.CAPACITY_GROWTH_WARNING else "high",
                       trust="publisher-observed" if current.source is Source.CAPACITY else "caller-pinned",
                       history=[{"event_id": row.event_id, "event_at": timestamp(row.event_at),
                                 "state": row.state, "detail": row.detail,
                                 "evidence_sha256": row.evidence_sha256} for row in self.history])
        if current.source is Source.CI:
            payload["check_id"] = current.check_id
        return payload


def correlate(observations):
    """Pure replay over the existing evidence input. No admission or ledger write."""
    groups = {}
    for index, row in enumerate(observations):
        require(index < MAX_EVENTS and type(row) is Observation, "invalid or oversized observation batch")
        events = groups.setdefault(row.incident_id, {})
        prior = events.get(row.event_id)
        if prior is None or row.observed_at < prior.observed_at:
            events[row.event_id] = row
    for key in sorted(groups):
        rows = sorted(groups[key].values(), key=lambda row: (row.event_at, row.event_id))
        latest = [row for row in rows if row.event_at == rows[-1].event_at]
        if len(latest) != 1:
            raise IncidentError("conflicting state at the same source time")
        if rows[-1].state is not State.RESOLVED or any(row.state is State.OPEN for row in rows):
            yield OperationalIncident(rows[-1], tuple(rows))


def report(observations):
    entries = []
    for incident in correlate(observations):
        state = incident.current.state
        action = "REQUEST_HUMAN_REVIEW" if state is State.OPEN else (
            "COLLECT_EVIDENCE" if state is State.UNKNOWN else "OBSERVE")
        entries.append({
            "incident": incident.to_dict(),
            "diagnosis": {"state": "CLEANUP_BLOCKED" if incident.current.source is Source.CAPACITY
                          and state is not State.RESOLVED else state},
            "proposal": {"action": action, "authorizes_execution": False},
        })
    return canonical({"schema_version": SCHEMA, "incidents": entries, "model_calls": 0,
                      "task_proposals_submitted": 0, "budget_operations": 0,
                      "cleanup_authorized": False}) + b"\n"


def publish_report(store, observations):
    """Explicit export to the caller's existing host-owned evidence store."""
    payload = json.loads(report(observations))
    return store.publish("operational-report", digest(payload), payload)
