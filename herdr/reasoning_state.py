"""Pure task-local reasoning-state contracts for Execution Fabric (#95).

This module intentionally owns no durable store, scheduler, memory, permission
or final completion authority. It materializes a bounded current projection
from host-validated append-only events. A future #95 ExecutionEvent stream may
persist these events; replay must remain deterministic.

LongHarness-inspired working evidence is not #85 EvidenceBundle and is not
#105 long-term memory.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Iterable

from .context import SecretRedactor, SourceRef, SourceState
from .security import InvocationIdentity

VERSION = 1
MAX_EVENTS = 2048
MAX_EVIDENCE = 256
MAX_CLAIMS = 256
MAX_GAPS = 128
MAX_SOURCES = 16
MAX_TEXT_BYTES = 8192
MAX_REASON_BYTES = 512

_ID = re.compile(r"[A-Za-z0-9._:-]{1,128}")
_REASON = re.compile(r"[A-Za-z0-9._:-]{1,128}")


class ReasoningStateError(ValueError):
    """Bounded fail-closed contract error without source bytes."""


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise ReasoningStateError(code)


def _text(value: object, code: str, maximum: int = MAX_TEXT_BYTES) -> str:
    _need(isinstance(value, str) and value and "\0" not in value
          and len(value.encode("utf-8")) <= maximum, code)
    _need(SecretRedactor().redact(value) == value, code + "_secret")
    return value


def _identifier(value: object, code: str) -> str:
    _need(isinstance(value, str) and _ID.fullmatch(value) is not None, code)
    return value


def _reason(value: object) -> str:
    _need(isinstance(value, str) and _REASON.fullmatch(value) is not None
          and len(value.encode("utf-8")) <= MAX_REASON_BYTES, "reason_code")
    return value


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ReasoningStateError("reasoning_state_not_canonical") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _source_json(source: SourceRef) -> dict[str, object]:
    value = asdict(source)
    value["data_class"] = source.data_class.value
    value["state"] = source.state.value
    return value


def _source_from_json(value: object) -> SourceRef:
    _need(isinstance(value, dict), "source_ref_schema")
    try:
        return SourceRef(**value)
    except (TypeError, ValueError) as exc:
        raise ReasoningStateError("source_ref_schema") from exc


class EvidenceLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"


class ClaimState(StrEnum):
    SUPPORTED = "SUPPORTED"
    CONTESTED = "CONTESTED"
    UNKNOWN = "UNKNOWN"


class ReasoningEventKind(StrEnum):
    EVIDENCE_ADDED = "evidence_added"
    EVIDENCE_RETRACTED = "evidence_retracted"
    CLAIM_UPSERTED = "claim_upserted"
    GAP_UPSERTED = "gap_upserted"
    GAP_RESOLVED = "gap_resolved"


@dataclass(frozen=True)
class WorkingEvidenceEntry:
    evidence_id: str
    statement: str
    sources: tuple[SourceRef, ...]
    state: EvidenceLifecycle = EvidenceLifecycle.ACTIVE
    superseded_by: str | None = None
    reason_code: str = "accepted_candidate"

    def __post_init__(self) -> None:
        _identifier(self.evidence_id, "evidence_id")
        _text(self.statement, "evidence_statement")
        object.__setattr__(self, "sources", tuple(self.sources))
        _need(1 <= len(self.sources) <= MAX_SOURCES
              and all(isinstance(source, SourceRef) for source in self.sources),
              "evidence_sources")
        object.__setattr__(self, "state", EvidenceLifecycle(self.state))
        if self.superseded_by is not None:
            _identifier(self.superseded_by, "superseded_by")
        _reason(self.reason_code)
        _need((self.state is EvidenceLifecycle.SUPERSEDED) == (self.superseded_by is not None),
              "evidence_supersession_binding")

    @property
    def statement_sha256(self) -> str:
        return hashlib.sha256(self.statement.encode("utf-8")).hexdigest()

    def to_json(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "statement": self.statement,
            "statement_sha256": self.statement_sha256,
            "sources": [_source_json(source) for source in self.sources],
            "state": self.state.value,
            "superseded_by": self.superseded_by,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class ConclusionClaim:
    claim_id: str
    statement: str
    state: ClaimState
    evidence_ids: tuple[str, ...]
    reason_code: str

    def __post_init__(self) -> None:
        _identifier(self.claim_id, "claim_id")
        _text(self.statement, "claim_statement")
        object.__setattr__(self, "state", ClaimState(self.state))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        _need(len(self.evidence_ids) <= 64
              and len(set(self.evidence_ids)) == len(self.evidence_ids)
              and all(isinstance(item, str) and _ID.fullmatch(item) for item in self.evidence_ids),
              "claim_evidence_ids")
        _reason(self.reason_code)
        _need(self.state is ClaimState.UNKNOWN or bool(self.evidence_ids),
              "claim_support_required")

    @property
    def statement_sha256(self) -> str:
        return hashlib.sha256(self.statement.encode("utf-8")).hexdigest()

    def to_json(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "statement_sha256": self.statement_sha256,
            "state": self.state.value,
            "evidence_ids": list(self.evidence_ids),
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class OpenGap:
    gap_id: str
    question: str
    reason_code: str

    def __post_init__(self) -> None:
        _identifier(self.gap_id, "gap_id")
        _text(self.question, "gap_question", maximum=4096)
        _reason(self.reason_code)

    def to_json(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReasoningEvent:
    identity: InvocationIdentity
    sequence: int
    kind: ReasoningEventKind
    data: bytes | dict[str, object]

    def __post_init__(self) -> None:
        _need(isinstance(self.identity, InvocationIdentity), "reasoning_event_identity")
        _need(type(self.sequence) is int and 1 <= self.sequence <= MAX_EVENTS,
              "reasoning_event_sequence")
        object.__setattr__(self, "kind", ReasoningEventKind(self.kind))
        _need(isinstance(self.data, dict), "reasoning_event_data")
        normalized = self._validate_data(dict(self.data))
        raw = _canonical(normalized)
        _need(len(raw) <= 131072, "reasoning_event_bytes")
        object.__setattr__(self, "data", raw)

    def _validate_data(self, data: dict[str, object]) -> dict[str, object]:
        if self.kind is ReasoningEventKind.EVIDENCE_ADDED:
            expected = {"evidence_id", "statement", "sources", "supersedes", "reason_code"}
            _need(set(data) == expected, "evidence_added_schema")
            _identifier(data["evidence_id"], "evidence_id")
            _text(data["statement"], "evidence_statement")
            _reason(data["reason_code"])
            raw_sources = data["sources"]
            _need(isinstance(raw_sources, list) and 1 <= len(raw_sources) <= MAX_SOURCES,
                  "evidence_sources")
            sources = tuple(_source_from_json(item) for item in raw_sources)
            _need(all(source.state in {SourceState.VERIFIED, SourceState.UNVERIFIED}
                      for source in sources), "active_evidence_source_state")
            raw_supersedes = data["supersedes"]
            _need(isinstance(raw_supersedes, list) and len(raw_supersedes) <= 16
                  and len(set(raw_supersedes)) == len(raw_supersedes)
                  and all(isinstance(item, str) and _ID.fullmatch(item) for item in raw_supersedes),
                  "evidence_supersedes")
            return {
                "evidence_id": data["evidence_id"],
                "statement": data["statement"],
                "sources": [_source_json(source) for source in sources],
                "supersedes": list(raw_supersedes),
                "reason_code": data["reason_code"],
            }

        if self.kind is ReasoningEventKind.EVIDENCE_RETRACTED:
            _need(set(data) == {"evidence_id", "reason_code"}, "evidence_retracted_schema")
            _identifier(data["evidence_id"], "evidence_id")
            _reason(data["reason_code"])
            return data

        if self.kind is ReasoningEventKind.CLAIM_UPSERTED:
            expected = {"claim_id", "statement", "state", "evidence_ids", "reason_code"}
            _need(set(data) == expected, "claim_upserted_schema")
            _identifier(data["claim_id"], "claim_id")
            _text(data["statement"], "claim_statement")
            try:
                state = ClaimState(data["state"])
            except (TypeError, ValueError) as exc:
                raise ReasoningStateError("claim_state") from exc
            raw_ids = data["evidence_ids"]
            _need(isinstance(raw_ids, list) and len(raw_ids) <= 64
                  and len(set(raw_ids)) == len(raw_ids)
                  and all(isinstance(item, str) and _ID.fullmatch(item) for item in raw_ids),
                  "claim_evidence_ids")
            _need(state is ClaimState.UNKNOWN or bool(raw_ids), "claim_support_required")
            _reason(data["reason_code"])
            return {**data, "state": state.value, "evidence_ids": list(raw_ids)}

        if self.kind is ReasoningEventKind.GAP_UPSERTED:
            _need(set(data) == {"gap_id", "question", "reason_code"}, "gap_upserted_schema")
            _identifier(data["gap_id"], "gap_id")
            _text(data["question"], "gap_question", maximum=4096)
            _reason(data["reason_code"])
            return data

        if self.kind is ReasoningEventKind.GAP_RESOLVED:
            _need(set(data) == {"gap_id", "reason_code"}, "gap_resolved_schema")
            _identifier(data["gap_id"], "gap_id")
            _reason(data["reason_code"])
            return data

        raise ReasoningStateError("reasoning_event_kind")

    @classmethod
    def evidence_added(cls, identity: InvocationIdentity, sequence: int, *,
                       evidence_id: str, statement: str, sources: Iterable[SourceRef],
                       supersedes: Iterable[str] = (), reason_code: str = "accepted_candidate") -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.EVIDENCE_ADDED, {
            "evidence_id": evidence_id,
            "statement": statement,
            "sources": [_source_json(source) for source in tuple(sources)],
            "supersedes": list(supersedes),
            "reason_code": reason_code,
        })

    @classmethod
    def evidence_retracted(cls, identity: InvocationIdentity, sequence: int, *,
                           evidence_id: str, reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.EVIDENCE_RETRACTED, {
            "evidence_id": evidence_id, "reason_code": reason_code,
        })

    @classmethod
    def claim_upserted(cls, identity: InvocationIdentity, sequence: int, *,
                       claim_id: str, statement: str, state: ClaimState,
                       evidence_ids: Iterable[str] = (), reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.CLAIM_UPSERTED, {
            "claim_id": claim_id,
            "statement": statement,
            "state": ClaimState(state).value,
            "evidence_ids": list(evidence_ids),
            "reason_code": reason_code,
        })

    @classmethod
    def gap_upserted(cls, identity: InvocationIdentity, sequence: int, *,
                     gap_id: str, question: str, reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.GAP_UPSERTED, {
            "gap_id": gap_id, "question": question, "reason_code": reason_code,
        })

    @classmethod
    def gap_resolved(cls, identity: InvocationIdentity, sequence: int, *,
                     gap_id: str, reason_code: str) -> "ReasoningEvent":
        return cls(identity, sequence, ReasoningEventKind.GAP_RESOLVED, {
            "gap_id": gap_id, "reason_code": reason_code,
        })

    def to_json(self) -> dict[str, object]:
        return {
            "version": VERSION,
            "identity": self.identity.to_json(),
            "sequence": self.sequence,
            "kind": self.kind.value,
            "data": json.loads(self.data),
        }

    @classmethod
    def from_json(cls, value: object) -> "ReasoningEvent":
        _need(isinstance(value, dict)
              and set(value) == {"version", "identity", "sequence", "kind", "data"}
              and value["version"] == VERSION, "reasoning_event_schema")
        try:
            identity = InvocationIdentity.from_dict(value["identity"])
            return cls(identity, value["sequence"], ReasoningEventKind(value["kind"]), value["data"])
        except ReasoningStateError:
            raise
        except (TypeError, ValueError) as exc:
            raise ReasoningStateError("reasoning_event_schema") from exc


@dataclass(frozen=True)
class ReasoningProjection:
    identity: InvocationIdentity
    last_sequence: int
    evidence: tuple[WorkingEvidenceEntry, ...]
    claims: tuple[ConclusionClaim, ...]
    open_gaps: tuple[OpenGap, ...]

    def __post_init__(self) -> None:
        _need(isinstance(self.identity, InvocationIdentity), "reasoning_projection_identity")
        _need(type(self.last_sequence) is int and 1 <= self.last_sequence <= MAX_EVENTS,
              "reasoning_projection_sequence")
        for field_name, typ, maximum in (
            ("evidence", WorkingEvidenceEntry, MAX_EVIDENCE),
            ("claims", ConclusionClaim, MAX_CLAIMS),
            ("open_gaps", OpenGap, MAX_GAPS),
        ):
            values = tuple(getattr(self, field_name))
            object.__setattr__(self, field_name, values)
            _need(len(values) <= maximum and all(isinstance(item, typ) for item in values),
                  "reasoning_projection_bound")

    @property
    def active_evidence(self) -> tuple[WorkingEvidenceEntry, ...]:
        return tuple(item for item in self.evidence if item.state is EvidenceLifecycle.ACTIVE)

    @property
    def supported_claims(self) -> tuple[ConclusionClaim, ...]:
        return tuple(item for item in self.claims if item.state is ClaimState.SUPPORTED)

    def to_json(self) -> dict[str, object]:
        return {
            "version": VERSION,
            "identity": self.identity.to_json(),
            "last_sequence": self.last_sequence,
            "evidence": [item.to_json() for item in self.evidence],
            "claims": [item.to_json() for item in self.claims],
            "open_gaps": [item.to_json() for item in self.open_gaps],
        }

    @property
    def hash(self) -> str:
        return _digest(self.to_json())


def _downgrade_claims(claims: dict[str, ConclusionClaim], retired: set[str]) -> None:
    for claim_id, claim in tuple(claims.items()):
        if claim.state is ClaimState.SUPPORTED and retired.intersection(claim.evidence_ids):
            remaining = tuple(item for item in claim.evidence_ids if item not in retired)
            claims[claim_id] = replace(
                claim,
                state=ClaimState.UNKNOWN,
                evidence_ids=remaining,
                reason_code="support_retired",
            )


def materialize(events: Iterable[ReasoningEvent]) -> ReasoningProjection:
    """Deterministically materialize current state from host-validated events."""
    items = tuple(events)
    _need(1 <= len(items) <= MAX_EVENTS and all(isinstance(event, ReasoningEvent) for event in items),
          "reasoning_events_bound")
    identity = items[0].identity
    evidence: dict[str, WorkingEvidenceEntry] = {}
    claims: dict[str, ConclusionClaim] = {}
    gaps: dict[str, OpenGap] = {}

    for expected, event in enumerate(items, start=1):
        _need(event.identity == identity, "reasoning_identity_changed")
        _need(event.sequence == expected, "reasoning_sequence_gap")
        data = json.loads(event.data)

        if event.kind is ReasoningEventKind.EVIDENCE_ADDED:
            evidence_id = data["evidence_id"]
            _need(evidence_id not in evidence, "duplicate_evidence_id")
            supersedes = tuple(data["supersedes"])
            _need(evidence_id not in supersedes, "evidence_self_supersession")
            for old_id in supersedes:
                _need(old_id in evidence and evidence[old_id].state is EvidenceLifecycle.ACTIVE,
                      "superseded_evidence_not_active")
            sources = tuple(_source_from_json(value) for value in data["sources"])
            entry = WorkingEvidenceEntry(
                evidence_id=evidence_id,
                statement=data["statement"],
                sources=sources,
                reason_code=data["reason_code"],
            )
            evidence[evidence_id] = entry
            retired: set[str] = set()
            for old_id in supersedes:
                old = evidence[old_id]
                evidence[old_id] = replace(
                    old,
                    state=EvidenceLifecycle.SUPERSEDED,
                    superseded_by=evidence_id,
                    reason_code="superseded",
                )
                retired.add(old_id)
            _downgrade_claims(claims, retired)

        elif event.kind is ReasoningEventKind.EVIDENCE_RETRACTED:
            evidence_id = data["evidence_id"]
            _need(evidence_id in evidence and evidence[evidence_id].state is EvidenceLifecycle.ACTIVE,
                  "retracted_evidence_not_active")
            evidence[evidence_id] = replace(
                evidence[evidence_id],
                state=EvidenceLifecycle.RETRACTED,
                superseded_by=None,
                reason_code=data["reason_code"],
            )
            _downgrade_claims(claims, {evidence_id})

        elif event.kind is ReasoningEventKind.CLAIM_UPSERTED:
            ids = tuple(data["evidence_ids"])
            _need(all(item in evidence and evidence[item].state is EvidenceLifecycle.ACTIVE for item in ids),
                  "claim_nonactive_evidence")
            state = ClaimState(data["state"])
            if state is ClaimState.SUPPORTED:
                _need(bool(ids), "claim_support_required")
                _need(all(source.state is SourceState.VERIFIED
                          for item in ids for source in evidence[item].sources),
                      "supported_claim_unverified_source")
            claim = ConclusionClaim(
                claim_id=data["claim_id"],
                statement=data["statement"],
                state=state,
                evidence_ids=ids,
                reason_code=data["reason_code"],
            )
            claims[claim.claim_id] = claim
            _need(len(claims) <= MAX_CLAIMS, "reasoning_claim_bound")

        elif event.kind is ReasoningEventKind.GAP_UPSERTED:
            gap = OpenGap(data["gap_id"], data["question"], data["reason_code"])
            gaps[gap.gap_id] = gap
            _need(len(gaps) <= MAX_GAPS, "reasoning_gap_bound")

        elif event.kind is ReasoningEventKind.GAP_RESOLVED:
            gap_id = data["gap_id"]
            _need(gap_id in gaps, "resolved_gap_missing")
            del gaps[gap_id]

        _need(len(evidence) <= MAX_EVIDENCE, "reasoning_evidence_bound")

    return ReasoningProjection(
        identity=identity,
        last_sequence=len(items),
        evidence=tuple(evidence[key] for key in sorted(evidence)),
        claims=tuple(claims[key] for key in sorted(claims)),
        open_gaps=tuple(gaps[key] for key in sorted(gaps)),
    )
