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
from dataclasses import asdict, dataclass, field, fields, replace
from enum import StrEnum
from pathlib import Path
from typing import Callable

from .context import (ContextError, ContextItem, MemoryClass, SecretRedactor, SourceRef, SourceState, bounded_text,
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

    @staticmethod
    def propose(**inputs):
        """Project a host-accepted outcome into unverified proposal data only."""
        return build_memory_proposal(**inputs)

    @staticmethod
    def recall_proposals(proposals, **inputs):
        """Recall bounded proposals against separately supplied current host pins."""
        return recall_memory_proposals(proposals, **inputs)

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


MAX_PROPOSAL_BYTES = 16_384
MAX_PROPOSAL_CATALOG_BYTES = 262_144
MAX_ACCEPTED_MEMORY_BYTES = 2_000_000


class ProposalKind(StrEnum):
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass(frozen=True)
class AcceptedMemoryBinding:
    """Host input from independently established acceptance, not a worker claim.

    Construction and hashes do not authenticate an outcome. The trusted caller
    supplies these pins independently of the candidate and accepted-record bytes.
    This API never looks up, publishes or changes an EvidenceStore record.
    """
    project: str
    repo: str
    task_id: str
    run_token: str
    idempotency_key: str
    attempt: int
    fencing_token: int
    plan_hash: str
    result_sha256: str
    commit_sha: str
    bundle_hash: str

    def __post_init__(self):
        for name in ("project", "repo", "task_id", "run_token", "idempotency_key"):
            token(getattr(self, name))
        for name in ("attempt", "fencing_token"):
            value = getattr(self, name)
            require(type(value) is int and 0 <= value <= 2**31, "memory_acceptance_identity")
        for name in ("plan_hash", "result_sha256", "bundle_hash"):
            hash_value(getattr(self, name))
        require(isinstance(self.commit_sha, str) and len(self.commit_sha) == 40
                and all(x in "0123456789abcdef" for x in self.commit_sha), "memory_acceptance_commit")

    def identity(self):
        return {"id": self.task_id, "run_token": self.run_token,
                "idempotency_key": self.idempotency_key, "attempt": self.attempt,
                "fencing_token": self.fencing_token}


def _proposal_sources(sources, project):
    # Reserve one of ContextItem's sixteen refs for the unverified derived body.
    require(isinstance(sources, (list, tuple)) and 0 < len(sources) <= 15
            and all(type(x) is SourceRef for x in sources), "memory_proposal_sources")
    require(len({x.uri for x in sources}) == len(sources), "duplicate_memory_source")
    require(all(x.project == project and x.data_class == DataClass.PUBLIC
                and x.holdout_series is None and x.state == SourceState.VERIFIED for x in sources),
            "memory_proposal_source_not_public_current")
    return tuple(sorted(sources, key=lambda x: x.uri))


@dataclass(frozen=True)
class MemoryProposal:
    """Bounded derived lesson. It grants neither verified truth nor promotion."""
    id: str
    kind: ProposalKind
    task_class: str
    origin: AcceptedMemoryBinding
    sources: tuple[SourceRef, ...]
    summary: str
    state: SourceState = field(default=SourceState.UNVERIFIED, init=False)
    authority: str = field(default="derived_context_data", init=False)

    def __post_init__(self):
        token(self.id)
        token(self.task_class)
        require(type(self.origin) is AcceptedMemoryBinding, "host_memory_acceptance_binding")
        try:
            object.__setattr__(self, "kind", ProposalKind(self.kind))
        except (TypeError, ValueError) as exc:
            raise ContextError("memory_proposal_kind") from exc
        object.__setattr__(self, "sources", _proposal_sources(self.sources, self.origin.project))
        require(any(x.sha256 == self.origin.result_sha256
                    and x.revision == self.origin.commit_sha for x in self.sources),
                "memory_proposal_result_source")
        bounded_text(self.summary, 8192)
        require(len(canonical(self.to_json())) <= MAX_PROPOSAL_BYTES, "memory_proposal_bytes")

    def to_json(self):
        return asdict(self)

    @property
    def hash(self):
        return digest(self.to_json())

    def derived(self, redactor):
        require(isinstance(redactor, SecretRedactor), "host_redactor")
        raw = self.to_json()
        raw.pop("summary")
        require(canonical(redactor.tree(raw)) == canonical(raw), "secret_memory_proposal_metadata")
        return replace(self, summary=redactor.redact(self.summary))


def build_memory_proposal(*, accepted_record, binding, sources, id, kind, task_class,
                          summary, redactor):
    """Pure projection of a bounded immutable host snapshot; no acceptance gate.

    The bytes are the canonical stored accepted payload, without the returned
    bundle_hash wrapper. Their digest must match the independently supplied host
    binding. No raw record/proof bytes are retained in the proposal or exposed.
    """
    require(type(binding) is AcceptedMemoryBinding, "host_memory_acceptance_binding")
    require(type(accepted_record) is bytes and 0 < len(accepted_record) <= MAX_ACCEPTED_MEMORY_BYTES,
            "memory_accepted_record_bound")
    require(hashlib.sha256(accepted_record).hexdigest() == binding.bundle_hash,
            "memory_accepted_record_digest")
    try:
        raw = json.loads(accepted_record)
        require(type(raw) is dict and canonical(raw) == accepted_record,
                "memory_accepted_record_canonical")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ContextError("memory_accepted_record_encoding") from exc
    artifact = raw.get("artifact")
    require(type(raw.get("version")) is int and raw["version"] == 2
            and raw.get("level") == "verified_worker_result" and raw.get("repo") == binding.repo
            and canonical(raw.get("identity")) == canonical(binding.identity())
            and raw.get("plan_hash") == binding.plan_hash,
            "memory_accepted_record_binding")
    require(type(artifact) is dict and artifact.get("task_id") == binding.task_id
            and type(artifact.get("attempt")) is int and artifact["attempt"] == binding.attempt
            and artifact.get("result_sha") == binding.result_sha256
            and artifact.get("commit_sha") == binding.commit_sha,
            "memory_accepted_artifact_binding")
    return MemoryProposal(id, kind, task_class, binding, sources, summary).derived(redactor)


@dataclass(frozen=True)
class ProposalRecall:
    proposal_hash: str
    sources: tuple[SourceRef, ...]
    applicability: Applicability
    reason: str
    proposal: MemoryProposal | None
    authority: str = field(default="derived_context_data", init=False)

    def to_json(self):
        return asdict(self)

    def context_item(self, redactor):
        """Use the existing optional derived-context path, never host controls."""
        require(self.proposal is not None
                and self.reason == "memory_proposal_requires_independent_admission",
                "memory_proposal_unavailable")
        proposal = self.proposal.derived(redactor)
        raw = canonical(proposal.to_json())
        sha = hashlib.sha256(raw).hexdigest()
        summary = replace(proposal.sources[0], uri="herdr://derived/" + sha,
                          sha256=sha, state=SourceState.UNVERIFIED)
        item = ContextItem("memory-proposal-" + sha, MemoryClass.EPISODIC,
                           (summary, *proposal.sources), len(raw), "optional_memory_proposal",
                           derived_summary=True)
        return item, raw


def recall_memory_proposals(proposals, *, project, task_class, current_bindings,
                            current_sources, redactor, limit=4, byte_budget=65_536):
    """Pure optional recall with no loader, writes, promotion or policy mutation.

    Current bindings and sources are host snapshots, not candidate-selected data.
    Missing, retracted (omitted), stale, conflicting or private support returns
    provenance with no lesson body. A valid lesson remains UNVERIFIED.
    """
    token(project)
    token(task_class)
    require(isinstance(redactor, SecretRedactor), "host_redactor")
    require(type(limit) is int and 0 < limit <= 8 and type(byte_budget) is int
            and 2 <= byte_budget <= MAX_PROPOSAL_CATALOG_BYTES, "memory_proposal_recall_limit")
    require(isinstance(proposals, (list, tuple)) and len(proposals) <= MAX_RECORDS
            and all(type(x) is MemoryProposal for x in proposals), "memory_proposal_catalog")
    require(len({(x.origin.project, x.id) for x in proposals}) == len(proposals),
            "duplicate_memory_proposal")
    require(len(canonical([x.to_json() for x in proposals])) <= MAX_PROPOSAL_CATALOG_BYTES,
            "memory_proposal_catalog_bytes")
    require(isinstance(current_bindings, (list, tuple)) and len(current_bindings) <= MAX_RECORDS
            and all(type(x) is AcceptedMemoryBinding for x in current_bindings),
            "host_memory_acceptance_catalog")
    bindings = {(x.project, x.task_id): x for x in current_bindings}
    require(len(bindings) == len(current_bindings), "duplicate_memory_acceptance")
    require(isinstance(current_sources, (list, tuple)) and len(current_sources) <= MAX_RECORDS
            and all(type(x) is SourceRef for x in current_sources), "host_memory_source_catalog")
    sources = {(x.project, x.uri): x for x in current_sources}
    require(len(sources) == len(current_sources), "duplicate_current_memory_source")
    output = []
    used = 2  # Canonical output array brackets, plus commas between rows below.
    for original in sorted(proposals, key=lambda x: (x.id, x.hash)):
        if original.origin.project != project or original.task_class != task_class:
            continue
        proposal = original.derived(redactor)
        state, reason = Applicability.UNVERIFIED, "memory_proposal_requires_independent_admission"
        if bindings.get((project, proposal.origin.task_id)) != proposal.origin:
            state, reason = Applicability.UNAVAILABLE, "accepted_outcome_not_current"
        else:
            for source in proposal.sources:
                current = sources.get((project, source.uri))
                if current is None:
                    state, reason = Applicability.UNAVAILABLE, "memory_source_unavailable"
                elif current.data_class != DataClass.PUBLIC or current.holdout_series is not None:
                    state, reason = Applicability.UNAVAILABLE, "memory_source_private"
                elif (current.sha256, current.revision) != (source.sha256, source.revision):
                    state, reason = Applicability.STALE, "memory_source_changed"
                elif current.state != SourceState.VERIFIED:
                    state, reason = {
                        SourceState.STALE: (Applicability.STALE, "memory_source_stale"),
                        SourceState.CONFLICT: (Applicability.CONFLICT, "memory_source_conflict"),
                        SourceState.UNAVAILABLE: (Applicability.UNAVAILABLE, "memory_source_unavailable"),
                        SourceState.UNVERIFIED: (Applicability.UNVERIFIED, "memory_source_unverified"),
                    }[current.state]
                if reason != "memory_proposal_requires_independent_admission":
                    break
        row = ProposalRecall(original.hash, proposal.sources, state, reason,
                             proposal if reason == "memory_proposal_requires_independent_admission" else None)
        size = len(canonical(row.to_json())) + bool(output)
        if used + size > byte_budget:
            continue
        output.append(row)
        used += size
        if len(output) == limit:
            break
    return tuple(output)


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
