#!/usr/bin/env python3
"""Fail-closed execution-ownership boundary for agent-stack-ensure.

This module is an observation/evaluation boundary, not a scheduler and not a
new authority. It reads existing host evidence only:

* the project supervisor state file and the process identity recorded in it,
* the supervisor's own lock files (``flock`` ownership),
* the native durable TaskGraph queue (pending/running/uncertain blocked tasks),
* side processes recorded by the last supervised launch,
* the host consumer policy/budget contract,
* optionally a caller-supplied interactive owner identity.

It never starts, stops, resumes or rewrites a task, checkpoint or supervisor
state. When the existing authority does not expose an atomic interactive-start
reservation API, ``reserve_interactive_start`` denies every request instead of
inventing a TOCTOU fallback.

First dependency-safe slice: Herdr supervised-consumer observation and the
``agent-stack-ensure`` start gate. Other consumers are intentionally untouched.
"""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

HOME = Path("/home/agentops")
DEFAULT_HERDR_STATE_DIR = HOME / ".local/state/agent-stack/herdr-development"
DEFAULT_TASKS_ROOT = HOME / ".local/state/agent-stack/tasks"

HERDR_CONSUMER = "Herdr"
HERDR_REPOSITORY = "Bbambaaamm/herdr"
HERDR_CONFIG_CONSUMER = "herdr"
HERDR_POLICY_PROFILE = "herdr-core"
# Existing supervisor command budget; the guard detects drift instead of
# defining a new budget. See herdr-development/supervisor.py --run-budget.
EXISTING_SUPERVISOR_BUDGET_SECONDS = 1500
SUPERVISOR_LOCK_NAMES = ("supervisor.lock", "cycle.lock", "bootstrap.lock")

DECISION_SKIPPED_SUPERVISOR_OWNED = "SKIPPED_SUPERVISOR_OWNED"
DECISION_BLOCKED_RECONCILIATION = "BLOCKED_RECONCILIATION_REQUIRED"
DECISION_BLOCKED_UNKNOWN = "BLOCKED_OWNER_UNKNOWN"
DECISION_BLOCKED_ATTEMPT = "BLOCKED_ACTIVE_ATTEMPT"
DECISION_BLOCKED_POLICY = "BLOCKED_POLICY"
DECISION_RESTORED_INTERACTIVE = "RESTORED_INTERACTIVE"

SUPERVISOR_STATUSES = frozenset(
    {"STARTING", "RUNNING", "CONTINUING", "WAITING",
     "HUMAN_BLOCKED", "COMPLETE", "PAUSED", "ERROR"}
)
# Live supervisor ownership states written by the existing supervisor.py:
# STARTING before the first cycle, RUNNING while a cycle is active, and
# CONTINUING between accepted non-terminal cycles. WAITING is also owned but
# not actively executing (handled separately because cycle.lock is released).
SUPERVISED_ACTIVE_STATES = frozenset({"STARTING", "RUNNING", "CONTINUING"})
SUPERVISED_WAITING_STATES = frozenset({"WAITING"})
RECONCILIATION_STATES = frozenset({"PAUSED", "HUMAN_BLOCKED", "COMPLETE"})
UNKNOWN_STATES = frozenset({"ERROR"})

BOUNDED_BYTES_LIMIT = 131072


class GuardObservationError(Exception):
    """Evidence was missing, unreadable, corrupt, symlinked or inconsistent."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class OwnerEvidence:
    """Host-verified ownership evidence (contract shape plus guard facts)."""

    consumer: str
    repo_identity: str
    execution_owner: str
    task_id: Optional[str] = None
    run_id: Optional[str] = None
    attempt: Optional[str] = None
    fence: Optional[str] = None
    lease_identity: Optional[str] = None
    policy_hash: Optional[str] = None
    decision_state: Optional[str] = None
    checkpoint_digest: Optional[str] = None
    sampled_at: Optional[str] = None
    source_digest: Optional[str] = None
    # Extended guard facts. The fields above remain the external contract.
    supervised: bool = False
    supervisor_alive: Optional[bool] = None
    expected_profile: Optional[str] = None
    policy_profile: Optional[str] = None
    configured_consumer: Optional[str] = None
    configured_repository: Optional[str] = None
    budget_seconds: Optional[int] = None
    expected_budget_seconds: Optional[int] = None
    fence_states: Mapping[str, str] = field(default_factory=dict)
    active_attempts: tuple = ()
    live_side_children: tuple = ()


@dataclass(frozen=True)
class GuardDecision:
    code: str
    reason: str
    evidence: OwnerEvidence
    audit_event: str
    audit_digest: str


@dataclass(frozen=True)
class StartReservation:
    granted: bool
    code: str
    token: Optional[str]
    observed_generation: str
    replay: bool
    reason: str


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _bounded_bytes(path: Path, limit: int = BOUNDED_BYTES_LIMIT) -> bytes:
    """Read a regular file without following a final symlink."""
    try:
        fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        reason = "symlink" if getattr(exc, "errno", None) == errno.ELOOP else "unreadable"
        raise GuardObservationError(reason)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise GuardObservationError("not_regular")
        if info.st_size > limit:
            raise GuardObservationError("oversize")
        data = os.read(fd, limit + 1)
        if len(data) > limit:
            raise GuardObservationError("oversize")
        return data
    finally:
        os.close(fd)


def read_bounded_json(path: Path) -> tuple[bytes, dict]:
    raw = _bounded_bytes(path)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise GuardObservationError("corrupt_json")
    if not isinstance(value, dict):
        raise GuardObservationError("not_object")
    return raw, value


def process_identity(pid: object) -> Optional[dict]:
    """Identity fields that cannot be forged by a stale PID reuse.

    Mirrors the supervisor's identity check: pid + /proc start_ticks + the
    SHA-256 of the full cmdline. A JSON state file alone is never authority.
    """
    try:
        numeric = int(str(pid))
    except (TypeError, ValueError):
        return None
    if numeric <= 0:
        return None
    proc = Path("/proc", str(numeric))
    try:
        raw_stat = (proc / "stat").read_bytes()
        fields = raw_stat.rsplit(b") ", 1)[1].split()
        if not fields or fields[0] == b"Z":
            return None
        cmdline = (proc / "cmdline").read_bytes()
        return {
            "pid": numeric,
            "start_ticks": fields[19].decode("ascii", errors="replace"),
            "command_sha256": hashlib.sha256(cmdline).hexdigest(),
            "session": int(fields[3]),
        }
    except (OSError, IndexError, ValueError):
        return None


def identity_matches(recorded: object, observed: object) -> bool:
    if not isinstance(recorded, dict) or not isinstance(observed, dict):
        return False
    for key in ("pid", "start_ticks", "command_sha256"):
        if str(recorded.get(key)) != str(observed.get(key)):
            return False
    return True


def lock_state(path: Path) -> str:
    """Return HELD/FREE/MISSING without creating the file."""
    try:
        fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return "MISSING"
    except OSError:
        return "UNREADABLE"
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "HELD"
        except OSError:
            return "UNREADABLE"
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        return "FREE"
    finally:
        os.close(fd)


def _parse_consumer_policy(raw: bytes) -> dict:
    values: dict[str, str] = {}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise GuardObservationError("policy_not_utf8")
    for line in text.splitlines():
        match = re.match(r"\s*(consumer|repository|policy_profile)\s*:\s*(\S+)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _native_attempt_entry(directory: Path):
    """Yield (name, task) for one inventory directory, failing closed."""
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink() or not path.is_file():
            raise GuardObservationError("native_attempt_entry_invalid")
        _, task = read_bounded_json(path)
        yield path.name, task


def _native_inventory_dir(root: Path, name: str) -> Path:
    directory = root / name
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise GuardObservationError("native_" + name + "_invalid")
    if not directory.is_dir():
        raise GuardObservationError("native_" + name + "_missing")
    return directory


def _native_attempt_hits(tasks_root: Path, repository: str) -> tuple:
    """Existing durable admission evidence. No new queue, no retry.

    Missing, unreadable, symlinked, oversized or malformed native inventory is
    unknown owner evidence and fails closed instead of being skipped.
    """
    root = Path(tasks_root)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise GuardObservationError("native_tasks_root_invalid")
    if not root.is_dir():
        raise GuardObservationError("native_tasks_root_missing")
    hits = []
    for folder in ("pending", "running"):
        for name, task in _native_attempt_entry(_native_inventory_dir(root, folder)):
            if task.get("repo") == repository:
                hits.append(folder + "/" + name)
    for name, task in _native_attempt_entry(_native_inventory_dir(root, "blocked")):
        blob = canonical_json(task).lower()
        if task.get("repo") == repository and ("uncertain" in blob or "unknown" in blob):
            hits.append("blocked/" + name)
    return tuple(hits)


def _live_side_children(launch: Mapping[str, Any]) -> tuple:
    children = []
    side = launch.get("side_processes") if isinstance(launch, Mapping) else None
    for item in side or ():
        if not isinstance(item, dict):
            continue
        observed = process_identity(item.get("pid"))
        if observed is not None and identity_matches(item, observed):
            children.append(str(item.get("pid")))
    return tuple(children)


def _current_job_path(state_dir: Path, value: object) -> Optional[Path]:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute() or path.is_symlink():
        raise GuardObservationError("current_job_invalid")
    resolved = path.resolve()
    state_resolved = state_dir.resolve()
    if resolved != state_resolved and state_resolved not in resolved.parents:
        raise GuardObservationError("current_job_outside_state")
    if not resolved.is_dir():
        raise GuardObservationError("current_job_missing")
    return resolved


def collect_herdr_observation(
    agent_id: str,
    *,
    state_dir: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    tasks_root: Optional[Path] = None,
) -> dict:
    """Collect existing Herdr supervisor/admission facts. Read-only."""
    state_dir = Path(state_dir) if state_dir is not None else DEFAULT_HERDR_STATE_DIR
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(repo_root)
    tasks_root = Path(tasks_root) if tasks_root is not None else DEFAULT_TASKS_ROOT

    _, supervisor = read_bounded_json(state_dir / "supervisor.json")
    state = supervisor.get("state")
    if not isinstance(state, str) or state not in SUPERVISOR_STATUSES:
        raise GuardObservationError("supervisor_state_invalid")
    recorded = supervisor.get("supervisor")
    if not isinstance(recorded, dict):
        raise GuardObservationError("supervisor_identity_missing")
    observed_identity = process_identity(recorded.get("pid"))
    alive = observed_identity is not None and identity_matches(recorded, observed_identity)

    job_path = _current_job_path(state_dir, supervisor.get("current_job"))

    decision = supervisor.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    expected_checkpoint = decision.get("checkpoint_sha256")
    checkpoint_digest = None
    if job_path is not None and (job_path / "checkpoint.json").exists():
        checkpoint_digest = hashlib.sha256(
            _bounded_bytes(job_path / "checkpoint.json")
        ).hexdigest()
    elif expected_checkpoint:
        raise GuardObservationError("checkpoint_missing")
    if expected_checkpoint and checkpoint_digest != expected_checkpoint:
        raise GuardObservationError("checkpoint_digest_mismatch")

    # Preserve-by-reading evidence: never rewritten by this collector.
    emergency_digest = None
    unaccepted_digest = None
    if job_path is not None:
        continuation = job_path / "continuation.json"
        unaccepted = job_path / "unaccepted-continuation.json"
        if continuation.exists():
            emergency_digest = hashlib.sha256(_bounded_bytes(continuation)).hexdigest()
        if unaccepted.exists():
            unaccepted_digest = hashlib.sha256(_bounded_bytes(unaccepted)).hexdigest()

    fence_states = {name: lock_state(state_dir / name) for name in SUPERVISOR_LOCK_NAMES}

    budget_seconds = None
    max_turns = None
    side_children: tuple = ()
    if job_path is not None and (job_path / "launch.json").exists():
        _, launch = read_bounded_json(job_path / "launch.json")
        if isinstance(launch.get("budget_seconds"), int):
            budget_seconds = launch["budget_seconds"]
        if isinstance(launch.get("max_turns"), int):
            max_turns = launch["max_turns"]
        side_children = _live_side_children(launch)

    config_path = repo_root / "configs" / "consumers" / "herdr.yaml"
    config_raw = _bounded_bytes(config_path)
    policy_values = _parse_consumer_policy(config_raw)
    if not policy_values:
        raise GuardObservationError("host_policy_unavailable")
    policy_hash = hashlib.sha256(config_raw).hexdigest()

    active_attempts = _native_attempt_hits(tasks_root, HERDR_REPOSITORY)

    return {
        "agent_id": str(agent_id),
        "run_id": job_path.name if job_path is not None else None,
        "consumer": HERDR_CONSUMER,
        "repository": HERDR_REPOSITORY,
        "supervised": True,
        "state": state,
        "supervisor_alive": alive,
        "recorded_identity": recorded,
        "observed_identity": observed_identity,
        "decision_state": decision.get("status"),
        "decision_checkpoint_sha256": expected_checkpoint,
        "checkpoint_digest": checkpoint_digest,
        "emergency_paused_digest": emergency_digest,
        "unaccepted_waiting_digest": unaccepted_digest,
        "fence_states": fence_states,
        "budget_seconds": budget_seconds,
        "max_turns": max_turns,
        "expected_budget_seconds": EXISTING_SUPERVISOR_BUDGET_SECONDS,
        "policy_hash": policy_hash,
        "policy_profile": policy_values.get("policy_profile"),
        "configured_consumer": policy_values.get("consumer"),
        "configured_repository": policy_values.get("repository"),
        "expected_profile": HERDR_POLICY_PROFILE,
        "active_attempts": active_attempts,
        "live_side_children": side_children,
        "interactive_owner": None,
        "sampled_at": utcnow_iso(),
    }


def build_owner_evidence(observation: Mapping[str, Any]) -> OwnerEvidence:
    state = observation.get("state")
    supervised = observation.get("supervised") is True
    owner = "unknown"
    if supervised:
        if state in SUPERVISED_ACTIVE_STATES and observation.get("supervisor_alive") is True:
            owner = "supervised"
        elif (
            state in SUPERVISED_WAITING_STATES
            and observation.get("supervisor_alive") is True
        ):
            owner = "supervised"
        elif state in RECONCILIATION_STATES:
            owner = "none"
        elif state in UNKNOWN_STATES:
            owner = "unknown"
        else:
            owner = "unknown"
    elif observation.get("interactive_owner"):
        owner = "interactive"
    else:
        owner = "none"

    fence_states = dict(observation.get("fence_states") or {})
    fence = ";".join(f"{name}={fence_states.get(name, 'MISSING')}" for name in SUPERVISOR_LOCK_NAMES)
    lease_identity = None
    recorded_identity = observation.get("recorded_identity")
    if isinstance(recorded_identity, dict):
        lease_identity = digest({
            "pid": recorded_identity.get("pid"),
            "start_ticks": recorded_identity.get("start_ticks"),
            "command_sha256": recorded_identity.get("command_sha256"),
        })

    core = {
        "consumer": observation.get("consumer"),
        "repo_identity": observation.get("repository"),
        "execution_owner": owner,
        "decision_state": state,
        "checkpoint_digest": observation.get("checkpoint_digest"),
        "policy_hash": observation.get("policy_hash"),
        "fence": fence,
        "lease_identity": lease_identity,
        "sampled_at": observation.get("sampled_at"),
    }

    return OwnerEvidence(
        consumer=str(observation.get("consumer") or ""),
        repo_identity=str(observation.get("repository") or ""),
        execution_owner=owner,
        run_id=str(observation.get("run_id") or "") or None,
        fence=fence or None,
        lease_identity=lease_identity,
        policy_hash=observation.get("policy_hash"),
        decision_state=str(state) if isinstance(state, str) else None,
        checkpoint_digest=observation.get("checkpoint_digest"),
        sampled_at=observation.get("sampled_at"),
        source_digest=digest(core),
        supervised=supervised,
        supervisor_alive=observation.get("supervisor_alive"),
        expected_profile=observation.get("expected_profile"),
        policy_profile=observation.get("policy_profile"),
        configured_consumer=observation.get("configured_consumer"),
        configured_repository=observation.get("configured_repository"),
        budget_seconds=observation.get("budget_seconds"),
        expected_budget_seconds=observation.get("expected_budget_seconds"),
        fence_states=fence_states,
        active_attempts=tuple(observation.get("active_attempts") or ()),
        live_side_children=tuple(observation.get("live_side_children") or ()),
    )


def get_execution_ownership(
    consumer: str,
    repository: str,
    agent_id: str,
    *,
    state_dir: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    tasks_root: Optional[Path] = None,
    interactive_owner: Optional[Mapping[str, Any]] = None,
) -> OwnerEvidence:
    """Host-verified ownership evidence for the existing Herdr authority.

    Raises GuardObservationError when evidence is missing/corrupt so callers
    can fail closed. Other consumers are out of scope for this slice.
    """
    if consumer != HERDR_CONSUMER or repository != HERDR_REPOSITORY:
        raise GuardObservationError("unsupported_consumer")
    observation = collect_herdr_observation(
        agent_id, state_dir=state_dir, repo_root=repo_root, tasks_root=tasks_root
    )
    observation["interactive_owner"] = interactive_owner
    return build_owner_evidence(observation)


def _decision(code: str, reason: str, evidence: OwnerEvidence) -> GuardDecision:
    return GuardDecision(
        code=code,
        reason=reason,
        evidence=evidence,
        audit_event=code,
        audit_digest=digest({"code": code, "reason": reason, "source_digest": evidence.source_digest}),
    )


def evaluate_ownership(evidence: OwnerEvidence) -> GuardDecision:
    """Pure fail-closed evaluation. Never performs I/O or starts anything."""
    if (
        not evidence.consumer
        or not evidence.repo_identity
        or evidence.execution_owner not in {"supervised", "interactive", "none", "unknown"}
    ):
        return _decision(DECISION_BLOCKED_UNKNOWN, "invalid_owner_evidence", evidence)

    # Durable PAUSED/HUMAN_BLOCKED/COMPLETE decisions win before any retry logic.
    if evidence.supervised and evidence.decision_state in RECONCILIATION_STATES:
        return _decision(
            DECISION_BLOCKED_RECONCILIATION,
            "supervisor_" + str(evidence.decision_state).lower(),
            evidence,
        )

    if evidence.active_attempts:
        return _decision(DECISION_BLOCKED_ATTEMPT, "durable_active_attempt", evidence)
    if evidence.live_side_children:
        return _decision(DECISION_BLOCKED_ATTEMPT, "live_side_child", evidence)

    if (
        evidence.configured_consumer != HERDR_CONFIG_CONSUMER
        or evidence.configured_repository != HERDR_REPOSITORY
    ):
        reason = (
            "host_policy_identity_missing"
            if evidence.configured_consumer is None
            or evidence.configured_repository is None
            else "host_policy_identity_mismatch"
        )
        return _decision(DECISION_BLOCKED_POLICY, reason, evidence)
    if evidence.expected_profile and evidence.policy_profile != evidence.expected_profile:
        return _decision(DECISION_BLOCKED_POLICY, "host_policy_profile_mismatch", evidence)
    if (
        evidence.budget_seconds is not None
        and evidence.expected_budget_seconds is not None
        and evidence.budget_seconds != evidence.expected_budget_seconds
    ):
        return _decision(DECISION_BLOCKED_POLICY, "budget_contract_mismatch", evidence)

    if evidence.supervised:
        fences = dict(evidence.fence_states or {})
        supervisor_lock = fences.get("supervisor.lock", "MISSING")
        state = evidence.decision_state
        if supervisor_lock == "MISSING":
            return _decision(DECISION_BLOCKED_UNKNOWN, "supervisor_fence_missing", evidence)
        if state in SUPERVISED_ACTIVE_STATES:
            if evidence.supervisor_alive is not True:
                return _decision(DECISION_BLOCKED_UNKNOWN, "stale_supervisor_identity", evidence)
            if supervisor_lock != "HELD":
                return _decision(DECISION_BLOCKED_UNKNOWN, "supervisor_fence_not_held", evidence)
            return _decision(DECISION_SKIPPED_SUPERVISOR_OWNED, "supervisor_owns_consumer", evidence)
        if state in SUPERVISED_WAITING_STATES:
            if evidence.supervisor_alive is not True:
                return _decision(DECISION_BLOCKED_UNKNOWN, "stale_supervisor_identity", evidence)
            if supervisor_lock != "HELD":
                return _decision(
                    DECISION_BLOCKED_UNKNOWN, "supervisor_fence_not_held", evidence)
            return _decision(
                DECISION_SKIPPED_SUPERVISOR_OWNED, "supervisor_waiting", evidence)
        if supervisor_lock == "HELD":
            return _decision(DECISION_BLOCKED_UNKNOWN, "orphan_supervisor_fence", evidence)
        if state in UNKNOWN_STATES or state is None:
            return _decision(DECISION_BLOCKED_UNKNOWN, "supervisor_state_unknown", evidence)
        return _decision(DECISION_BLOCKED_UNKNOWN, "supervisor_state_unhandled", evidence)

    if evidence.execution_owner == "interactive":
        return _decision(DECISION_RESTORED_INTERACTIVE, "interactive_owner_verified", evidence)
    return _decision(DECISION_BLOCKED_UNKNOWN, "interactive_authority_missing", evidence)


def emit_audit(
    *,
    event: str,
    actor: str,
    consumer: str,
    operation: str,
    reason: str,
    decision_digest: str,
    audit_path: Optional[Path] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> dict:
    record = {
        "event": event,
        "actor": actor,
        "consumer": consumer,
        "operation": operation,
        "reason": reason,
        "decision_digest": decision_digest,
        "observed_utc": utcnow_iso(),
    }
    for key in ("observed_generation", "reservation_token_sha256"):
        if extra and key in extra and isinstance(extra[key], str):
            record[key] = extra[key]
    if audit_path is not None:
        path = Path(audit_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    return record


def decide_herdr_agent_start(
    consumer: str,
    repository: str,
    agent_id: str,
    *,
    state_dir: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    tasks_root: Optional[Path] = None,
    audit_path: Optional[Path] = None,
    actor: str = "agent-stack-watchdog",
    operation: str = "agent.start",
) -> GuardDecision:
    """Observe, evaluate and audit. Missing evidence fails closed to 0 starts."""
    try:
        evidence = get_execution_ownership(
            consumer, repository, agent_id,
            state_dir=state_dir, repo_root=repo_root, tasks_root=tasks_root,
        )
    except GuardObservationError as exc:
        evidence = OwnerEvidence(
            consumer=str(consumer), repo_identity=str(repository), execution_owner="unknown",
            sampled_at=utcnow_iso(), source_digest=digest({"failed_reason": exc.reason}),
        )
        decision = _decision(DECISION_BLOCKED_UNKNOWN, "observation_failed:" + exc.reason, evidence)
    else:
        decision = evaluate_ownership(evidence)
    emit_audit(
        event=decision.audit_event, actor=actor, consumer=decision.evidence.consumer,
        operation=operation, reason=decision.reason, decision_digest=decision.audit_digest,
        audit_path=audit_path,
    )
    return decision


def reserve_interactive_start(
    consumer: str,
    repository: str,
    observed_generation: str,
    operator_authority: str,
    *,
    authority: Any = None,
    audit_path: Optional[Path] = None,
    actor: str = "agent-stack-watchdog",
    operation: str = "agent.start",
) -> StartReservation:
    """Atomic reservation seam over an existing authority.

    Without a supplied atomic authority this denies the request. It does not
    create a lock, a lease or a scheduler, and it does not validate by hand.
    """
    generation = str(observed_generation or "")
    token_input = str(operator_authority or "")
    request_digest = digest({
        "consumer": str(consumer),
        "repository": str(repository),
        "observed_generation": generation,
        "operator_authority_sha256": hashlib.sha256(token_input.encode("utf-8")).hexdigest(),
    })

    def denied(code: str, reason: str) -> StartReservation:
        emit_audit(
            event=code, actor=actor, consumer=str(consumer), operation=operation,
            reason=reason, decision_digest=request_digest, audit_path=audit_path,
            extra={"observed_generation": generation} if generation else None,
        )
        return StartReservation(False, code, None, generation, False, reason)

    if not consumer or not repository or not generation or not token_input:
        return denied(DECISION_BLOCKED_UNKNOWN, "incomplete_reservation_request")
    if authority is None:
        return denied(DECISION_BLOCKED_UNKNOWN, "no_atomic_authority_api")

    try:
        result = authority.reserve(
            consumer=str(consumer), repository=str(repository),
            observed_generation=generation, operator_authority=token_input,
        )
    except Exception:
        return denied(DECISION_BLOCKED_UNKNOWN, "authority_error")

    granted = bool(getattr(result, "granted", False))
    token = getattr(result, "token", None)
    replay = bool(getattr(result, "replay", False))
    returned_generation = getattr(result, "observed_generation", generation)
    if granted:
        if not isinstance(token, str) or not token:
            return denied(DECISION_BLOCKED_UNKNOWN, "authority_token_missing")
        if str(returned_generation) != generation:
            return denied(DECISION_BLOCKED_UNKNOWN, "authority_generation_mismatch")
        emit_audit(
            event=DECISION_RESTORED_INTERACTIVE, actor=actor, consumer=str(consumer),
            operation=operation, reason="atomic_reservation_granted", decision_digest=request_digest,
            audit_path=audit_path,
            extra={"observed_generation": generation,
                   "reservation_token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest()},
        )
        return StartReservation(True, DECISION_RESTORED_INTERACTIVE, token, generation, replay,
                                "atomic_reservation_granted")
    reason = str(getattr(result, "reason", "") or "authority_denied")
    return denied(DECISION_BLOCKED_UNKNOWN, "authority_denied:" + reason[:120])


def plan_agent_start(
    evidence: OwnerEvidence,
    reservation: Optional[StartReservation],
    *,
    agent_present: bool = False,
) -> str:
    """Map evidence + atomic reservation to exactly one start decision."""
    if agent_present:
        return "healthy"
    decision = evaluate_ownership(evidence)
    if decision.code != DECISION_RESTORED_INTERACTIVE:
        return decision.code
    if reservation is None or not reservation.granted:
        return DECISION_BLOCKED_UNKNOWN
    if reservation.replay:
        return "already-reserved"
    return "start"
