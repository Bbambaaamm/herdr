"""Capacity Watcher to #100 diagnostic data, with no dispatch or credential use."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import os
import socket

from . import operation_readiness as readiness
from .capacity_attestor import MAX_ATTESTATION_AGE, MAX_RECEIPT_BYTES, RECEIPT_PATH, verify_receipt
from .evidence import canonical, digest
from .operational_adapters import MAX_INPUT_BYTES, capacity_snapshot
from .operational_incidents import (
    Detail, IncidentError, IncidentType, Observation, Scope, State, correlate, epoch, require,
    timestamp, token,
)

EVENT_SCHEMA = "herdr-capacity-event-1"
RECORD_SCHEMA = "herdr-capacity-record-1"
RECORD_KIND = "capacity-observation"
BLOCKED = "BLOCKED_PENDING_TRUST_ACCEPTANCE"
TASK_CLASS = "DIAGNOSE_STAGING_CAPACITY"
MAX_SAMPLES = 1024
MAX_AGE_SECONDS = 900


@dataclass(frozen=True)
class CapacityPolicy:
    """Expected server and consumer scope selected by the host-side caller."""

    server: str
    scope: Scope
    max_age: int = MAX_AGE_SECONDS

    def __post_init__(self):
        token(self.server)
        require(type(self.scope) is Scope and type(self.max_age) is int
                and 0 < self.max_age <= MAX_AGE_SECONDS, "invalid capacity event policy")


@dataclass(frozen=True)
class EventEnvelope:
    server: str
    scope: Scope
    incident_class: IncidentType
    event_at: int
    revision: str
    evidence: tuple[str, ...]
    correlation_key: str
    trust: str

    def to_dict(self):
        fields = {
            "schema_version": EVENT_SCHEMA, "source": "capacity-watch",
            "server": self.server, "scope": asdict(self.scope),
            "incident_class": self.incident_class, "event_at": timestamp(self.event_at),
            "observed_at": timestamp(self.event_at), "revision": self.revision,
            "evidence_sha256": self.evidence, "correlation_key": self.correlation_key,
            "trust": self.trust, "requested_task_class": TASK_CLASS,
        }
        event_id = digest(fields)
        return {**fields, "event_id": event_id, "digest": event_id, "idempotency_key": event_id}


@dataclass(frozen=True)
class TaskProposal:
    """Typed request for a human-reviewed diagnostic, with no execution parameters."""

    incident_id: str
    event_id: str
    idempotency_key: str
    server: str
    scope: Scope
    evidence_sha256: tuple[str, ...]

    def to_dict(self):
        return {
            "schema_version": "herdr-read-only-task-proposal-1",
            "task_class": TASK_CLASS, "incident_id": self.incident_id,
            "event_id": self.event_id, "idempotency_key": self.idempotency_key,
            "server": self.server, "scope": asdict(self.scope),
            "evidence_sha256": self.evidence_sha256,
            "operations": ("OBSERVE", "COLLECT_EVIDENCE", "GENERATE_REPORT", "REQUEST_HUMAN_REVIEW"),
            "host_admission_required": True, "authorizes_execution": False,
        }


@dataclass(frozen=True)
class _Sample:
    row: Observation
    envelope: EventEnvelope
    raw: bytes
    receipt: bytes | None
    build: tuple[bytes, str] | None


def _slot(policy, at):
    return digest([RECORD_SCHEMA, policy.server, asdict(policy.scope), at])


def _sample(policy, raw, receipt, *, now, build=None):
    """Decode already-read bytes. Receipt provenance comes from the enclosing read boundary."""
    row, _ = capacity_snapshot(raw, policy.scope, now=now, max_age=policy.max_age,
                               build_input=build)
    raw_hash = hashlib.sha256(raw).hexdigest()
    trusted = receipt is not None
    refs = row.evidence_sha256
    if trusted:
        data = verify_receipt(receipt, raw, row.event_at, dict(row.facts), policy.server, policy.scope)
        receipt = canonical(data)
        refs = (*refs, digest(data))
    # Freshness is a property of the projection. Preserve the measured state
    # in history when replaying an older, previously verified observation.
    below_floor = dict(row.facts)["available_bytes"] < dict(row.facts)["required_bytes"]
    row = replace(row, subject=("root-filesystem", policy.server),
                  observed_at=row.event_at, evidence_sha256=refs,
                  state=State.OPEN if below_floor else State.RESOLVED,
                  detail=Detail.BELOW_FLOOR if below_floor else Detail.READY)
    correlation = digest([EVENT_SCHEMA, policy.server, row.correlation_id])
    envelope = EventEnvelope(policy.server, row.scope, row.kind, row.event_at, raw_hash, refs,
                             correlation, "HOST_OWNED" if trusted else "PUBLISHER_OBSERVED")
    return _Sample(row, envelope, raw, receipt, build)


def _read_sample(policy, now, build=None):
    require(socket.gethostname() == policy.server, "capacity host identity mismatch")
    raw = readiness.read_capacity_report()
    try:
        receipt = readiness.read_protected(RECEIPT_PATH, limit=MAX_RECEIPT_BYTES)
    except (OSError, readiness.ReadinessError):
        receipt = None
    try:
        return _sample(policy, raw, receipt, now=now, build=build)
    except IncidentError:
        if receipt is None:
            raise
        return _sample(policy, raw, None, now=now, build=build)


def _fold(policy, samples, *, now):
    slots = {}
    for index, sample in enumerate(samples):
        require(index < MAX_SAMPLES, "too many capacity samples")
        at = sample.row.event_at
        earlier = slots.setdefault(at, sample)
        require(earlier.envelope.revision == sample.envelope.revision
                and earlier.build == sample.build, "conflicting capacity source revision")
        if earlier.receipt is None and sample.receipt is not None:
            slots[at] = sample
    if not slots:
        return _blocked()
    latest = slots[max(slots)]
    current = latest.row
    usable = (latest.receipt is not None
              and epoch(now) - current.event_at <= min(policy.max_age, MAX_ATTESTATION_AGE))
    history = [item.row for _, item in sorted(slots.items()) if item.receipt is not None
               and item.row.event_at < current.event_at]
    if not usable:
        current = replace(current, state=State.UNKNOWN, detail=Detail.UNKNOWN)
    rows = list(correlate([*history, current]))
    incident = rows[0].to_dict() if rows else None
    proposal = None
    if usable and current.state is State.OPEN:
        event = latest.envelope.to_dict()
        key = digest([TASK_CLASS, latest.envelope.correlation_key, current.incident_id])
        proposal = TaskProposal(current.incident_id, event["event_id"], key, policy.server,
                                current.scope, current.evidence_sha256).to_dict()
    return {
        "status": ("READ_ONLY_PROPOSAL" if proposal else "OBSERVE") if usable else BLOCKED,
        "event": latest.envelope.to_dict(), "incident": incident, "task_proposal": proposal,
        "requested_diagnostic": TASK_CLASS,
        "diagnostics": {
            "build_evidence": "ATTACHED" if latest.build is not None else "UNAVAILABLE",
            "lease_fencing": "UNKNOWN", "parent_ack": "UNKNOWN",
            "cleanup": "BLOCKED",
        },
        "model_calls": 0, "budget_operations": 0, "worker_dispatches": 0,
    }


def _blocked():
    return {
        "status": BLOCKED, "event": None, "incident": None, "task_proposal": None,
        "requested_diagnostic": TASK_CLASS, "diagnostics": {
            "build_evidence": "UNAVAILABLE", "lease_fencing": "UNKNOWN",
            "parent_ack": "UNKNOWN", "cleanup": "BLOCKED",
        },
        "model_calls": 0, "budget_operations": 0, "worker_dispatches": 0,
    }


def canary(policy, *, now, build=None):
    """One read-only host observation. No durable writes, provider or scheduler."""
    try:
        sample = _read_sample(policy, now, build)
        # Use the same fold for duplicate deliveries as for a single snapshot.
        result = _fold(policy, (sample,), now=now)
        require(canonical(result) == canonical(_fold(policy, (sample, sample), now=now)),
                "capacity replay diverged")
        return result
    except (OSError, AttributeError, readiness.ReadinessError, ValueError):
        return _blocked()


def record_host_observation(store, policy, *, now, build=None):
    """Explicit opt-in for the existing protected EvidenceStore, never used by canary."""
    sample = _read_sample(policy, now, build)
    require(sample.receipt is not None and now - sample.row.event_at <= min(policy.max_age, MAX_ATTESTATION_AGE),
            "fresh host receipt required for durable capacity publication")
    key = _slot(policy, sample.row.event_at)
    payload = {
        "schema_version": RECORD_SCHEMA, "server": policy.server, "scope": asdict(policy.scope),
        "raw": sample.raw.hex(),
        "receipt": sample.receipt.hex(),
        "build": [build[0].hex(), build[1]] if build is not None else None,
    }
    store.publish(RECORD_KIND, key, payload)
    return key


def replay_recorded(store, policy, *, now):
    """Replay all capacity records in the caller's existing protected evidence root."""
    prefix = RECORD_KIND + "-"
    suffix = ".json"
    keys = []
    with os.scandir(store.root) as entries:
        for index, entry in enumerate(entries):
            require(index < 8192, "capacity evidence directory exceeds replay bound")
            if entry.name.startswith(prefix) and entry.name.endswith(suffix):
                require(len(keys) < MAX_SAMPLES, "too many capacity record keys")
                keys.append(entry.name[len(prefix):-len(suffix)])
    samples = []
    for key in sorted(keys):
        data = store.read(RECORD_KIND, key)
        require(set(data) == {"schema_version", "server", "scope", "raw", "receipt", "build"}
                and data["schema_version"] == RECORD_SCHEMA, "invalid capacity record")
        if data["server"] != policy.server or data["scope"] != asdict(policy.scope):
            continue
        require(type(data["raw"]) is str and 0 < len(data["raw"]) <= 2 * MAX_INPUT_BYTES
                and type(data["receipt"]) is str and 0 < len(data["receipt"]) <= 2 * MAX_RECEIPT_BYTES,
                "invalid stored capacity evidence")
        raw, receipt = (bytes.fromhex(data[name]) for name in ("raw", "receipt"))
        build = data["build"]
        if build is not None:
            require(type(build) is list and len(build) == 2 and type(build[0]) is str
                    and 0 < len(build[0]) <= 2 * MAX_INPUT_BYTES and type(build[1]) is str,
                    "invalid stored build evidence")
            build = bytes.fromhex(build[0]), build[1]
        sample = _sample(policy, raw, receipt, now=now, build=build)
        require(key == _slot(policy, sample.row.event_at), "capacity record key mismatch")
        samples.append(sample)
    return _fold(policy, samples, now=now)
