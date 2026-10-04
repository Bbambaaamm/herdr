"""Immutable derived experience memory. Trial/budget/evidence authority stays external."""
from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import fcntl
import secrets
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields, replace
from enum import StrEnum
from pathlib import Path
from typing import Callable

from .context import (ContextError, SecretRedactor, SourceRef, SourceState, bounded_text,
                      canonical, digest, hash_value, require, token)
from .capability import DataClass

MAX_RECORD = 65_536
MAX_RECORDS = 256


class TrialOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    UNCERTAIN = "uncertain"
    UNUSABLE = "unusable"


class Applicability(StrEnum):
    COMPARABLE = "same_conditions"
    REVIEW_CHANGED = "review_changed_conditions"
    UNVERIFIED = "unverified_note"
    STALE = "stale"
    UNAVAILABLE = "source_unavailable"
    CONFLICT = "conflicting_evidence"


@dataclass(frozen=True)
class Conditions:
    code: str
    model: str
    context: str
    policy: str
    evaluator: str
    corpus: str
    scope: str

    def __post_init__(self):
        for field in fields(self):
            token(getattr(self, field.name))

    @property
    def fingerprint(self):
        # Provider session and task IDs deliberately do not change factual conditions.
        return digest(asdict(self))


@dataclass(frozen=True)
class Experience:
    id: str
    project: str
    task_class: str
    series: str
    variant: str
    attempt: int
    hypothesis: str
    conditions: Conditions
    outcome: TrialOutcome
    baseline: float | None
    measured: float | None
    samples: int
    limitations: str
    evidence: tuple[SourceRef, ...]
    summary: str
    state: SourceState = SourceState.UNVERIFIED
    unusable_reason: str | None = None
    # View metadata only. Persisted JSON and content hash omit this field.
    publication_digest: str | None = None

    def __post_init__(self):
        if self.publication_digest is not None:
            hash_value(self.publication_digest)
        for key in ("id", "project", "task_class", "series", "variant"):
            token(getattr(self, key))
        require(type(self.attempt) is int and 0 < self.attempt <= 2**31, "experience_attempt")
        bounded_text(self.hypothesis, 2048)
        bounded_text(self.limitations, 4096, empty=True)
        bounded_text(self.summary, 16_384)
        require(isinstance(self.conditions, Conditions), "experience_conditions")
        object.__setattr__(self, "outcome", TrialOutcome(self.outcome))
        object.__setattr__(self, "state", SourceState(self.state))
        require(type(self.samples) is int and 0 <= self.samples <= 1_000_000_000, "sample_count")
        for value in (self.baseline, self.measured):
            require(value is None or type(value) in {int, float} and math.isfinite(value), "experience_measurement")
        require(isinstance(self.evidence, (list, tuple)) and 0 < len(self.evidence) <= 16
                and all(isinstance(x, SourceRef) and x.project == self.project for x in self.evidence),
                "experience_evidence")
        require(all(x.holdout_series is None or x.holdout_series == self.series for x in self.evidence),
                "experience_holdout_series")
        object.__setattr__(self, "evidence", tuple(self.evidence))
        if self.unusable_reason is not None:
            token(self.unusable_reason)
            require(self.outcome == TrialOutcome.UNUSABLE, "infrastructure_is_not_candidate_failure")
        if self.outcome == TrialOutcome.UNUSABLE:
            require(self.unusable_reason is not None, "unusable_reason_required")
        if self.state == SourceState.VERIFIED:
            require(all(x.state == SourceState.VERIFIED for x in self.evidence)
                    and (self.outcome not in {TrialOutcome.SUCCESS, TrialOutcome.FAILURE} or self.samples > 0),
                    "verified_experience_evidence")
        require(len(canonical(self.to_json())) <= MAX_RECORD, "experience_size")

    def to_json(self):
        raw = asdict(self)
        raw.pop("publication_digest")
        return raw

    @classmethod
    def from_dict(cls, raw):
        require(isinstance(raw, dict) and set(raw) == {x.name for x in fields(cls) if x.name != "publication_digest"}, "experience_schema")
        raw = dict(raw)
        raw["conditions"] = Conditions(**raw["conditions"])
        raw["evidence"] = tuple(SourceRef(**x) for x in raw["evidence"])
        return cls(**raw)

    @property
    def hash(self):
        return digest(self.to_json())

    def derived(self, redactor):
        raw = self.to_json()
        for key in ("hypothesis", "summary", "limitations"):
            raw[key] = redactor.redact(raw[key])
        # Metadata cannot be silently rewritten into a different identity/reference.
        require(canonical(redactor.tree(raw)) == canonical(raw), "secret_memory_metadata")
        # Original evidence remains unchanged; summaries cannot edit its sources.
        return Experience.from_dict(raw)


@dataclass(frozen=True)
class Recall:
    record: Experience
    applicability: Applicability
    reason: str
    changed_conditions: tuple[str, ...]
    comparable_trial_exists: bool
    authority: str = "derived_context_data"


class ExperienceMemory:
    def __init__(self, records):
        require(isinstance(records, (list, tuple)) and len(records) <= MAX_RECORDS
                and all(isinstance(x, Experience) for x in records), "memory_limit")
        require(len({x.id for x in records}) == len(records), "duplicate_experience")
        self.records = tuple(sorted(records, key=lambda x: x.id))

    def retrieve(self, *, project, task_class, conditions: Conditions, allowed_classes,
                 source_available: Callable[[SourceRef], bool], role="worker", series=None, limit=4):
        token(project)
        token(task_class)
        require(isinstance(conditions, Conditions) and type(limit) is int and 0 < limit <= 8,
                "retrieval_limit")
        require(role in {"worker", "experimenter", "evaluator"}, "retrieval_role")
        classes = {DataClass(x) for x in allowed_classes}
        candidates = []
        for record in self.records:
            if record.project != project or record.task_class != task_class:
                continue
            if any(x.data_class not in classes for x in record.evidence):
                continue
            # Never expose private evaluation answers through derived summaries.
            if any(x.holdout_series is not None and (role != "evaluator" or x.holdout_series != series)
                   for x in record.evidence):
                continue
            changed = tuple(x.name for x in fields(Conditions)
                            if getattr(conditions, x.name) != getattr(record.conditions, x.name))
            state = Applicability.COMPARABLE if not changed else Applicability.REVIEW_CHANGED
            if record.state != SourceState.VERIFIED:
                state = {SourceState.UNVERIFIED: Applicability.UNVERIFIED,
                         SourceState.STALE: Applicability.STALE,
                         SourceState.CONFLICT: Applicability.CONFLICT,
                         SourceState.UNAVAILABLE: Applicability.UNAVAILABLE}[record.state]
            if any(x.state == SourceState.CONFLICT for x in record.evidence):
                state = Applicability.CONFLICT
            elif any(x.state == SourceState.STALE for x in record.evidence):
                state = Applicability.STALE
            elif any(x.state == SourceState.UNAVAILABLE for x in record.evidence):
                state = Applicability.UNAVAILABLE
            elif any(x.state != SourceState.VERIFIED for x in record.evidence):
                state = Applicability.UNVERIFIED
            try:
                available = all(source_available(x) is True for x in record.evidence)
            except Exception:
                available = False
            if not available:
                state = Applicability.UNAVAILABLE
            comparable = (not changed and state == Applicability.COMPARABLE
                          and record.outcome in {TrialOutcome.SUCCESS, TrialOutcome.FAILURE})
            reason = ("comparable_prior_trial_requires_review" if comparable else
                      "changed_conditions_allow_review_with_new_trial_reason" if changed else
                      "experience_" + state.value)
            candidates.append(Recall(record, state, reason, changed, comparable))
        # Relevant comparables first; bounded metadata retrieval never executes a trial.
        candidates.sort(key=lambda x: (not x.comparable_trial_exists,
                                      x.applicability != Applicability.REVIEW_CHANGED,
                                      len(x.changed_conditions), x.record.id))
        return tuple(candidates[:limit])


class ExperienceStore:
    """Host-only content-addressed records; no overwrite or original evidence mutation."""
    def __init__(self, path: Path, *, writable_roots, redactor: SecretRedactor):
        require(isinstance(redactor, SecretRedactor), "host_redactor")
        path = Path(path)
        require(".." not in path.parts, "memory_path")
        path = path.absolute()
        require(path.name not in {"", ".", ".."}, "memory_path")
        for root in writable_roots:
            root = Path(root).resolve()
            require(path != root and root not in path.parents, "memory_worker_writable")
        # Walk every existing ancestor without following any symlink.
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for component in path.parts[1:-1]:
                next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            try:
                os.mkdir(path.name, 0o700, dir_fd=fd)
            except FileExistsError:
                pass
            self.fd = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        finally:
            os.close(fd)
        try:
            for root in writable_roots:
                root = Path(root).resolve()
                require(path != root and root not in path.parents, "memory_worker_writable")
            st = os.fstat(self.fd)
            require(st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == 0o700, "memory_permissions")
            self.redactor = redactor
            self._mutex = threading.RLock()
            self._lock_fd = os.open(".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                                    0o600, dir_fd=self.fd)
            lock_stat = os.fstat(self._lock_fd)
            require(stat.S_ISREG(lock_stat.st_mode) and stat.S_IMODE(lock_stat.st_mode) == 0o600
                    and lock_stat.st_uid == os.getuid(), "memory_lock")
        except BaseException:
            if hasattr(self, "_lock_fd"):
                os.close(self._lock_fd)
            os.close(self.fd)
            raise

    def close(self):
        if self.fd >= 0:
            os.close(self._lock_fd)
            os.close(self.fd)
            self.fd = -1

    @contextmanager
    def _locked(self):
        with self._mutex:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)

    def _read(self, name):
        require(name.endswith(".json") and len(name) == 69, "memory_entry")
        hash_value(name[:-5])
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_RECORD
                    and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o400, "memory_entry")
            raw = os.read(fd, MAX_RECORD + 1)
            require(hashlib.sha256(raw).hexdigest() == name[:-5], "memory_digest")
            record = Experience.from_dict(json.loads(raw))
            require(canonical(record.to_json()) == raw, "memory_canonical")
            record.derived(self.redactor)  # Revalidate metadata against active credentials.
            return record  # Internal publication checks retain the original stored digest.
        finally:
            os.close(fd)

    def _load(self):
        names = sorted(os.listdir(self.fd))
        require(len(names) <= MAX_RECORDS + 33, "memory_limit")
        records = []
        for name in names:
            if name == ".lock":
                continue
            if re_staging(name):
                st = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
                require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid()
                        and st.st_size <= MAX_RECORD, "memory_staging")
                # No writer can be live while the cross-process lock is held.
                os.unlink(name, dir_fd=self.fd)
                continue
            records.append(self._read(name))
        require(len(records) <= MAX_RECORDS, "memory_limit")
        return ExperienceMemory(tuple(records))

    def load(self):
        with self._locked():
            return ExperienceMemory(tuple(replace(x.derived(self.redactor), publication_digest=x.hash)
                                          for x in self._load().records))

    def append(self, record: Experience):
        require(isinstance(record, Experience), "typed_experience")
        claimed_publication = record.publication_digest
        record = record.derived(self.redactor)
        with self._locked():
            current = self._load()
            previous = next((x for x in current.records if x.id == record.id), None)
            if previous is not None:
                if previous.hash == record.hash:
                    require(claimed_publication is None or claimed_publication == previous.hash,
                            "experience_immutable_conflict")
                    return previous.hash
                # Check the entire current redacted view against stored bytes;
                # the claimed digest by itself never authorizes idempotence.
                require(claimed_publication == previous.hash
                        and previous.derived(self.redactor).to_json() == record.to_json(),
                        "experience_immutable_conflict")
                return previous.hash
            require(claimed_publication is None, "unknown_memory_publication")
            require(len(current.records) < MAX_RECORDS, "memory_limit")
            raw = canonical(record.to_json())
            name = hashlib.sha256(raw).hexdigest() + ".json"
            staging = ".record-" + secrets.token_hex(16) + ".tmp"
            fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=self.fd)
            try:
                offset = 0
                while offset < len(raw):
                    written = os.write(fd, raw[offset:])
                    require(written > 0, "memory_write")
                    offset += written
                os.fchmod(fd, 0o400)
                os.fsync(fd)
                # Only a fully flushed immutable inode becomes a record entry.
                os.link(staging, name, src_dir_fd=self.fd, dst_dir_fd=self.fd, follow_symlinks=False)
                os.fsync(self.fd)
            finally:
                os.close(fd)
                os.unlink(staging, dir_fd=self.fd)
                os.fsync(self.fd)
            return record.hash


def re_staging(name):
    return (name.startswith(".record-") and name.endswith(".tmp") and len(name) == 44
            and all(x in "0123456789abcdef" for x in name[8:-4]))
