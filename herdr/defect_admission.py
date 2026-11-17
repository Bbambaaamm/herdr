"""Deterministic defect-observation normalization and admission decisions.

Proposal-only bridge for #100 (single Event/Trigger owner) and #53 (sole
autonomous backlog root): an authenticated defect observation is normalized,
fingerprinted, deduplicated and classified into a bounded admission decision.

This module never dispatches work, never writes the budget ledger and never
authorizes execution.  The resulting TaskProposal payload is handed to the
existing Herdr admission path (AdmissionControl / TaskGraph); a decision here is
a request, not authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from collections.abc import Mapping
import fcntl
import re
from types import MappingProxyType

from .admission import AuditLog
from .evidence import digest

SCHEMA = "herdr-defect-admission-1"
MAX_EVIDENCE = 4
MAX_SUBJECT = 4
MAX_REVISION = 64
DEFAULT_MAX_REPAIRS = 3

_SHA = re.compile(r"[a-f0-9]{40}")
_REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}/[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./@-]{0,127}")


class DefectError(ValueError):
    """Invalid observation or context."""


class DefectSource(StrEnum):
    CI_CHECK = "github-actions-check"
    REVIEW_COMMENT = "pull-request-review"
    VALIDATION = "deterministic-validation"
    SECURITY_SCAN = "security-scanner"
    RUNTIME_TELEMETRY = "runtime-telemetry"
    DEPENDENT_PR = "dependent-pr-conflict"
    EVIDENCE_STALENESS = "stale-evidence"
    UNTRUSTED_TEXT = "untrusted-text"


class DefectCategory(StrEnum):
    TEST_REGRESSION = "test_regression"
    REVIEW_FINDING = "review_finding"
    VALIDATION_FAILURE = "validation_failure"
    SECURITY_FINDING = "security_finding"
    RUNTIME_ERROR = "runtime_error"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    STALE_EVIDENCE = "stale_evidence"
    UNCLASSIFIED = "unclassified"


class DefectDisposition(StrEnum):
    ADMIT = "ADMIT"
    NO_ACTION = "NO_ACTION"
    DENY = "DENY"
    BLOCKED = "BLOCKED"
    CREDENTIAL_GATE = "CREDENTIAL_GATE"
    HUMAN_GATE = "HUMAN_GATE"
    UNKNOWN = "UNKNOWN"


# A source may only carry categories it can actually observe.  Anything else is
# a forged/misrouted observation and is denied, not silently re-labelled.
SOURCE_CATEGORIES: dict[DefectSource, frozenset[DefectCategory]] = {
    # A CI observation from the #100 adapter only proves "this exact revision
    # failed a required check"; it does not prove a test regression without
    # per-test evidence, so that category is not claimable here.
    DefectSource.CI_CHECK: frozenset({DefectCategory.VALIDATION_FAILURE}),
    DefectSource.REVIEW_COMMENT: frozenset({DefectCategory.REVIEW_FINDING}),
    DefectSource.VALIDATION: frozenset({
        DefectCategory.VALIDATION_FAILURE, DefectCategory.TEST_REGRESSION,
    }),
    DefectSource.SECURITY_SCAN: frozenset({DefectCategory.SECURITY_FINDING}),
    DefectSource.RUNTIME_TELEMETRY: frozenset({
        DefectCategory.RUNTIME_ERROR, DefectCategory.STALE_EVIDENCE,
    }),
    DefectSource.DEPENDENT_PR: frozenset({DefectCategory.DEPENDENCY_CONFLICT}),
    DefectSource.EVIDENCE_STALENESS: frozenset({DefectCategory.STALE_EVIDENCE}),
    DefectSource.UNTRUSTED_TEXT: frozenset({DefectCategory.UNCLASSIFIED}),
}

# Categories that must stop for an operator regardless of any other gate.
HUMAN_CATEGORIES = frozenset({DefectCategory.SECURITY_FINDING})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DefectError(message)


def _token(value: object, pattern: re.Pattern[str] = _TOKEN) -> str:
    _require(type(value) is str and pattern.fullmatch(value) is not None, "invalid identifier")
    return str(value)


@dataclass(frozen=True)
class DefectObservation:
    """One authenticated defect observation, pinned to an exact source revision."""

    source: DefectSource
    category: DefectCategory
    repository: str
    commit_sha: str
    ref: str
    subject: tuple[str, ...]
    observed_at: int
    evidence_sha256: tuple[str, ...] = ()
    workflow: str = ""
    check_run_id: str = ""
    event_revision: str = ""

    def __post_init__(self) -> None:
        _require(type(self.source) is DefectSource and type(self.category) is DefectCategory,
                 "invalid observation type")
        _require(self.category in SOURCE_CATEGORIES[self.source],
                 "source cannot observe this category")
        _token(self.repository, _REPO)
        _token(self.commit_sha, _SHA)
        _require(type(self.ref) is str and _REF.fullmatch(self.ref) is not None,
                 "invalid ref")
        _require(type(self.subject) is tuple and 1 <= len(self.subject) <= MAX_SUBJECT,
                 "invalid subject")
        for part in self.subject:
            _token(part)
        _require(type(self.observed_at) is int and 0 <= self.observed_at <= 253402300799,
                 "invalid timestamp")
        _require(type(self.evidence_sha256) is tuple
                 and len(self.evidence_sha256) <= MAX_EVIDENCE, "invalid evidence")
        _require(bool(self.evidence_sha256) or self.source is DefectSource.UNTRUSTED_TEXT,
                 "known defect requires evidence")
        for ref in self.evidence_sha256:
            _token(ref, re.compile(r"[a-f0-9]{64}"))
        for value in (self.workflow, self.check_run_id):
            _require(type(value) is str and len(value) <= 128, "invalid identifier field")
        _require(type(self.event_revision) is str and 0 < len(self.event_revision) <= MAX_REVISION,
                 "invalid event revision")

    @property
    def fingerprint(self) -> str:
        """Semantic defect identity.

        ``workflow`` and ``check_run_id`` participate because the #100 CI adapter
        proves only "this exact revision failed a required check": two different
        required checks failing on the same revision are two distinct defects and
        must not be collapsed into one durable record.  Redelivery of one check
        run still maps to one identity.
        """
        return digest([SCHEMA, self.source, self.repository, self.commit_sha,
                       self.category, self.subject, self.workflow,
                       self.check_run_id])

    @property
    def deduplication_id(self) -> str:
        """Delivery identity: a redelivered webhook is the same event."""
        return digest([self.fingerprint, self.workflow, self.check_run_id,
                       self.event_revision, self.observed_at])


@dataclass(frozen=True)
class DefectContext:
    """Injected, observable decision inputs.  No live probes, no ledger writes.

    Every risk-relevant field is required: an unobserved budget, credential,
    capacity or repair state must never silently read as healthy and fall
    through to ADMIT.
    """

    repository_authorized: bool
    already_resolved: bool
    active_repairs: int
    repeat_count: int
    budget_state: str
    credentials_state: str
    capacity_ok: bool
    max_repairs: int = DEFAULT_MAX_REPAIRS
    task_id: str | None = None

    def __post_init__(self) -> None:
        _require(type(self.repository_authorized) is bool
                 and type(self.already_resolved) is bool
                 and type(self.capacity_ok) is bool, "invalid flag")
        for name, allowed in (("budget_state", {"OK", "EXHAUSTED", "UNKNOWN"}),
                              ("credentials_state", {"OK", "MISSING", "UNKNOWN"})):
            # Only states with an explicit decision branch are accepted; an
            # unhandled state must fail closed rather than fall through to ADMIT.
            _require(getattr(self, name) in allowed, f"invalid {name}")
        _require(type(self.active_repairs) is int and self.active_repairs >= 0, "invalid repair count")
        _require(type(self.repeat_count) is int and self.repeat_count >= 0, "invalid repeat count")
        _require(type(self.max_repairs) is int and self.max_repairs > 0, "invalid repair ceiling")
        if self.task_id is not None:
            _token(self.task_id)


@dataclass(frozen=True)
class DefectDecision:
    disposition: DefectDisposition
    fingerprint: str
    commit_sha: str
    reasons: tuple[str, ...] = ()
    task_class: str | None = None
    proposal: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require(type(self.disposition) is DefectDisposition, "invalid disposition")
        _token(self.fingerprint, re.compile(r"[a-f0-9]{64}"))
        _token(self.commit_sha, _SHA)
        _require(type(self.reasons) is tuple, "invalid reasons")
        # Deep-freeze the payload: a later mutation must not be able to turn a
        # validated proposal into an authorization.
        object.__setattr__(self, "proposal", MappingProxyType(dict(self.proposal)))
        if self.disposition is DefectDisposition.ADMIT:
            # The ADMIT contract is part of the payload, not just the summary:
            # a proposal never authorizes execution, submits a task or spends.
            _require(self.proposal.get("authorizes_execution") is False
                     and self.proposal.get("task_proposals_submitted") == 0
                     and self.proposal.get("budget_operations") == 0,
                     "ADMIT proposal violates the proposal-only contract")


def decide_defect_admission(
    observation: DefectObservation, context: DefectContext
) -> DefectDecision:
    """Ordered, fail-closed classification.  First match wins."""
    fingerprint = observation.fingerprint

    def outcome(disposition: DefectDisposition, *reasons: str) -> DefectDecision:
        return DefectDecision(disposition, fingerprint, observation.commit_sha, tuple(reasons))

    if observation.source is DefectSource.UNTRUSTED_TEXT:
        return outcome(DefectDisposition.DENY, "untrusted_source")
    if not context.repository_authorized:
        return outcome(DefectDisposition.DENY, "repository_not_authorized")
    if context.credentials_state == "MISSING":
        return outcome(DefectDisposition.CREDENTIAL_GATE, "credentials_missing")
    if context.credentials_state == "UNKNOWN":
        return outcome(DefectDisposition.UNKNOWN, "credentials_unknown")
    if context.budget_state == "EXHAUSTED":
        return outcome(DefectDisposition.BLOCKED, "budget_exhausted")
    if context.budget_state == "UNKNOWN":
        return outcome(DefectDisposition.UNKNOWN, "budget_unknown")
    if not context.capacity_ok:
        return outcome(DefectDisposition.BLOCKED, "capacity_below_floor")
    if observation.category in HUMAN_CATEGORIES:
        return outcome(DefectDisposition.HUMAN_GATE, "category_requires_operator")
    if context.already_resolved:
        return outcome(DefectDisposition.NO_ACTION, "already_resolved")
    if context.active_repairs >= 1:
        return outcome(DefectDisposition.NO_ACTION, "repair_already_active")
    if context.repeat_count >= context.max_repairs:
        return outcome(DefectDisposition.BLOCKED, "no_progress_ceiling")
    return DefectDecision(
        DefectDisposition.ADMIT, fingerprint, observation.commit_sha,
        ("eligible",), task_class=observation.category.value,
        proposal={
            "schema_version": SCHEMA,
            "fingerprint": fingerprint,
            "commit_sha": observation.commit_sha,
            "repository": observation.repository,
            "ref": observation.ref,
            "task_class": observation.category.value,
            "graph": {"node_count": 1, "max_depth": 1, "max_fanout": 0,
                      "root_task": "defect-repair"},
            "role": "repair",
            "paper_only": True,
            "authorizes_execution": False,
            "task_proposals_submitted": 0,
            "budget_operations": 0,
        },
    )


class DecisionJournal:
    """Durable, idempotent decision record over the existing admission audit log.

    Dedup key is (fingerprint, commit_sha, disposition): a redelivered event for
    the same source revision creates no second record, while a regression on a
    new revision is a new record.
    """

    EVENT = "defect_admission_decision"

    def __init__(self, log: AuditLog) -> None:
        self._log = log

    def record(self, decision: DefectDecision) -> tuple[dict, bool]:
        """Append-if-absent under an inter-process lock.

        Concurrent deliveries of the same decision must yield exactly one
        durable record, not one per caller.
        """
        path = self._log.path
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = path.parent / f".{path.name}.lock"
        with lock_path.open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                prior = self.prior(decision)
                if prior is not None:
                    return prior, False
                record = self._log.append({
                    "event": self.EVENT,
                    "fingerprint": decision.fingerprint,
                    "commit_sha": decision.commit_sha,
                    "disposition": decision.disposition.value,
                    "reasons": list(decision.reasons),
                    "task_class": decision.task_class,
                })
                return record, True
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def prior(self, decision: DefectDecision) -> dict | None:
        latest = None
        for row in self._log.replay():
            if row.get("event") != self.EVENT:
                continue
            if (row.get("fingerprint") == decision.fingerprint
                    and row.get("commit_sha") == decision.commit_sha
                    and row.get("disposition") == decision.disposition.value):
                latest = row
        return latest

    def latest_for(self, fingerprint: str) -> dict | None:
        latest = None
        for row in self._log.replay():
            if row.get("event") == self.EVENT and row.get("fingerprint") == fingerprint:
                latest = row
        return latest


def approval_is_stale(approval: dict, commit_sha: str) -> bool:
    """An approval pins one source revision; a changed HEAD invalidates it."""
    _token(commit_sha, _SHA)
    _require(type(approval) is dict, "invalid approval")
    return approval.get("commit_sha") != commit_sha


def admission_summary(decisions) -> dict:
    """Aggregate without inventing counts: unknown inputs stay UNKNOWN."""
    counts: dict[str, int] = {}
    unknown = 0
    for decision in decisions:
        if type(decision) is not DefectDecision:
            unknown += 1
            continue
        key = decision.disposition.value
        counts[key] = counts.get(key, 0) + 1
    return {"schema_version": SCHEMA, "dispositions": counts,
            "unparsed": "UNKNOWN" if unknown else 0,
            "task_proposals_submitted": 0, "budget_operations": 0,
            "execution_authorized": False}
