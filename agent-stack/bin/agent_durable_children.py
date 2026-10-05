"""Read the scheduler's durable child ledger for one parent attempt."""

import hashlib
import fcntl
import json
import os
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from herdr.scheduler import AuditLog, DynamicChildScheduler, SchedulerError
from herdr.taskgraph import LifecycleState
from herdr.runtime import AdmissionRegistry, HerdrChildRuntime, SubprocessHerdrRunner

LEDGER_REQUIRED = "scheduler.required"
# Child evidence is a compact JSON envelope. Bound hostile files before decoding
# so replay cannot grow memory with an untrusted result path.
MAX_CHILD_RESULT_BYTES = 128 * 1024


def attempt_directory(root: Path, parent_task_id: str, run_token: str) -> Path:
    return root / "durable-children" / hashlib.sha256(
        f"{parent_task_id}:{run_token}".encode()).hexdigest()


def _require_real_directory(directory: Path) -> None:
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise NotADirectoryError(f"not a real directory: {directory}")


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(directory, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def ensure_attempt_directory(root: Path, parent_task_id: str, run_token: str) -> Path:
    """Create and persist the directory entries for one parent attempt."""
    _require_real_directory(root)
    container = root / "durable-children"
    container.mkdir(mode=0o700, exist_ok=True)
    _require_real_directory(container)
    _fsync_directory(root)
    directory = attempt_directory(root, parent_task_id, run_token)
    directory.mkdir(mode=0o700, exist_ok=True)
    _require_real_directory(directory)
    _fsync_directory(container)
    _fsync_directory(directory)
    return directory


def mark_ledger_required(directory: Path) -> None:
    """Persist that this attempt initialized a durable child scheduler."""
    fd = os.open(directory / LEDGER_REQUIRED,
                 os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(directory)



INITIALIZATION = "scheduler.initialization.json"
MAX_INITIALIZATION_BYTES = 1024 * 1024


def _atomic_control_file(path: Path, payload: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
        _fsync_directory(path.parent)
    finally:
        staged.unlink(missing_ok=True)


def _read_control_file(path: Path) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_INITIALIZATION_BYTES:
            raise SchedulerError("invalid scheduler initialization file")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read(MAX_INITIALIZATION_BYTES + 1)
        if len(raw) > MAX_INITIALIZATION_BYTES:
            raise SchedulerError("oversized scheduler initialization file")
        return raw
    finally:
        if fd >= 0:
            os.close(fd)


def _initialization(directory: Path, parent_task_id: str, run_token: str):
    try:
        document = json.loads(_read_control_file(directory / INITIALIZATION))
    except FileNotFoundError:
        return None
    if (not isinstance(document, dict) or document.get("schema") != 1
            or document.get("parent_task_id") != parent_task_id or document.get("run_token") != run_token
            or document.get("state") not in {"pending", "committed"}):
        raise SchedulerError("scheduler initialization identity mismatch")
    expected = {"schema", "parent_task_id", "run_token", "state", "ledger_sha256"}
    if document["state"] == "pending":
        expected.add("ledger")
    if set(document) != expected or not isinstance(document["ledger_sha256"], str):
        raise SchedulerError("invalid scheduler initialization envelope")
    if document["state"] == "pending":
        if not isinstance(document["ledger"], str):
            raise SchedulerError("invalid scheduler initialization ledger")
        raw = document["ledger"].encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != document["ledger_sha256"]:
            raise SchedulerError("scheduler initialization digest mismatch")
        events = [json.loads(line) for line in raw.splitlines()]
        if (len(events) != 3 or [event.get("event") for event in events] !=
                ["submit", "claim", "execution_session_bound"]
                or any(event.get("task_id") != parent_task_id for event in events)
                or events[1].get("run_token") != run_token or events[2].get("run_token") != run_token
                or events[1].get("attempt_state") != "accepted"
                or not events[1].get("idempotency_key")
                or not all(events[2].get(key) for key in ("agent_name", "pane_id", "marker"))
                or events[0].get("agent_id") != events[1].get("agent_id")
                or events[1].get("agent_id") != events[2].get("agent_name")):
            raise SchedulerError("invalid scheduler parent initialization events")
    return document


def initialization_pending(directory: Path, parent_task_id: str, run_token: str) -> bool:
    document = _initialization(directory, parent_task_id, run_token)
    return document is not None and document["state"] == "pending"


def repair_initialization(directory: Path, parent_task_id: str, run_token: str) -> None:
    """Finish only an authenticated initial parent ledger, while bridge.lock is held.

    A committed initialization can never repair missing/corrupt scheduler state.
    No child may be admitted until the committed marker is durably published.
    """
    document = _initialization(directory, parent_task_id, run_token)
    if document is None or document["state"] == "committed":
        return
    ledger = directory / "scheduler.jsonl"
    raw = document["ledger"].encode("utf-8")
    if os.path.lexists(ledger):
        if _read_control_file(ledger) != raw:
            raise SchedulerError("pending initialization conflicts with scheduler ledger")
    else:
        _atomic_control_file(ledger, raw)
    mark_ledger_required(directory)
    committed = {key: value for key, value in document.items() if key != "ledger"}
    committed["state"] = "committed"
    _atomic_control_file(directory / INITIALIZATION,
                         json.dumps(committed, sort_keys=True, allow_nan=False).encode("utf-8"))


def initialize_parent_scheduler(directory: Path, *, ownership_registry=None, ownership_parent=None, **binding) -> DynamicChildScheduler:
    """Stage the whole parent registration before publishing either required artifact."""
    ledger = directory / "scheduler.jsonl"
    if os.path.lexists(ledger) or ledger_required(directory) or os.path.lexists(directory / INITIALIZATION):
        raise SchedulerError("scheduler initialization is not empty")
    fd, name = tempfile.mkstemp(prefix=".scheduler-stage-", dir=directory)
    os.close(fd)
    stage = Path(name)
    try:
        scheduler = DynamicChildScheduler(audit_log=AuditLog(stage),
            ownership_registry=ownership_registry, ownership_parent=ownership_parent)
        scheduler.register_external_parent_attempt(**binding)
        raw = _read_control_file(stage)
        document = {"schema": 1, "parent_task_id": binding["task_id"], "run_token": binding["run_token"],
                    "state": "pending", "ledger_sha256": hashlib.sha256(raw).hexdigest(),
                    "ledger": raw.decode("utf-8")}
        _atomic_control_file(directory / INITIALIZATION,
                             json.dumps(document, sort_keys=True, allow_nan=False).encode("utf-8"))
        repair_initialization(directory, binding["task_id"], binding["run_token"])
        scheduler.audit_log = AuditLog(ledger)
        return scheduler
    finally:
        stage.unlink(missing_ok=True)


def ledger_required(directory: Path) -> bool:
    return os.path.lexists(directory / LEDGER_REQUIRED)


def publish_exact_child_result(scheduler: DynamicChildScheduler, rec, result_path: Path) -> str | None:
    """Publish only a result bound to this delegated child's current attempt."""
    try:
        _require_real_directory(result_path.parent)
        fd = os.open(result_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                     getattr(os, "O_NONBLOCK", 0))
    except FileNotFoundError:
        return None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("child result is not a regular file")
        if info.st_size > MAX_CHILD_RESULT_BYTES:
            raise ValueError("child result exceeds size limit")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read(MAX_CHILD_RESULT_BYTES + 1)
        if len(raw) > MAX_CHILD_RESULT_BYTES:
            raise ValueError("child result exceeds size limit")
    finally:
        if fd >= 0:
            os.close(fd)
    result = json.loads(raw.decode("utf-8", errors="strict"))
    if not isinstance(result, dict):
        raise ValueError("child result invalid")
    evidence = result.get("evidence")
    if (not isinstance(evidence, list) or not evidence
            or result.get("task_id") != rec.node.id
            or result.get("run_token") != rec.run_token
            or result.get("fencing_token") != rec.fencing_token
            or result.get("idempotency_key") != rec.idempotency_key):
        raise ValueError("child result identity/evidence mismatch")
    try:
        evidence_sha = hashlib.sha256(json.dumps(evidence, sort_keys=True,
            ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
    except (TypeError, ValueError):
        raise ValueError("child result evidence invalid") from None
    if result.get("artifact_sha256") != evidence_sha or result.get("status") not in {
        "completed", "blocked", "failed"
    }:
        raise ValueError("child result evidence/status mismatch")
    if rec.state is LifecycleState.RUNNING:
        if not scheduler.publish_child_result(rec.node.id, rec.run_token, rec.agent_id,
                                              rec.fencing_token, rec.idempotency_key,
                                              evidence_sha, evidence,
                                              status=result["status"]):
            raise ValueError("child result publication denied")
    if (rec.attempt_state != "terminal" or rec.result_status != result["status"]
            or rec.result_artifact_sha256 != evidence_sha):
        raise ValueError("child result not durably terminal")
    return rec.result_status


def replay_host_scheduler(root: Path, ledger: Path) -> DynamicChildScheduler:
    """Restore host ownership ports from protected canonical reservation intents.

    Reading this intent does not issue a grant or start work. Replay verifies
    its full parent/claim bindings against the already reserved private store.
    """
    from herdr.security import InvocationIdentity
    from herdr.child_ownership import OwnershipRegistry
    from herdr.ownership_inventory import LegacyOwnershipInventory
    audit = AuditLog(ledger)
    owners = {}
    for event in audit.replay():
        if event.get("event") == "child_ownership_reserved":
            owner = InvocationIdentity.from_dict(event.get("parent"))
            owners[json.dumps(owner.to_json(),sort_keys=True)] = owner
    if len(owners) > 1:
        raise SchedulerError("multiple ownership parents in one attempt ledger")
    owner = next(iter(owners.values()),None)
    registry = None if owner is None else OwnershipRegistry(root,verify_legacy=LegacyOwnershipInventory(root))
    scheduler = DynamicChildScheduler(audit_log=audit,ownership_registry=registry,ownership_parent=owner)
    scheduler.replay()
    if any(rec.ownership is not None and rec.ownership_reservation is None
           for rec in scheduler._tasks.values()):
        raise SchedulerError("declared ownership lacks protected reservation")
    return scheduler


def reconcile_child_results(root: Path, parent_task_id: str, run_token: str) -> None:
    """Under bridge.lock, consume exact result files from this attempt's ledger."""
    directory = attempt_directory(root, parent_task_id, run_token)
    ledger = directory / "scheduler.jsonl"
    if not ledger.is_file():
        return
    try:
        scheduler = replay_host_scheduler(root,ledger)
        events = scheduler.audit_log.replay()
        parent = scheduler._tasks.get(parent_task_id)
        children = [rec for rec in scheduler._tasks.values()
                    if rec.delegation_key is not None and
                    rec.parent_task_id == parent_task_id and
                    rec.parent_run_token == run_token]
        spawned = [event for event in events if event.get("event") == "spawn_child"]
        if (parent is None or parent.run_token != run_token or
                not any(event.get("event") == "submit" and
                        event.get("task_id") == parent_task_id for event in events) or
                {rec.id for rec in children} != {event.get("child_id") for event in spawned} or
                len(children) != len(spawned) or any(
                    event.get("parent_id") != parent_task_id or
                    event.get("parent_run_token") != run_token for event in spawned)):
            return
        for rec in children:
            if (rec.state is not LifecycleState.RUNNING or not rec.pre_delivery_pane_creation_attempted
                    or rec.pre_delivery_agent_start_attempted and rec.economic_delivery_attempted is not False):
                continue
            try:
                runner = SubprocessHerdrRunner(os.environ.get(
                    "HERDR_REAL_BINARY", "/home/agentops/.local/bin/herdr"))
                runtime = HerdrChildRuntime(scheduler, runner, cwd=root,
                    snapshot_path=directory / "swarm.json", admission_registry=AdmissionRegistry())
                runtime.recover_interrupted_child_start(rec.id)
            except (OSError, ValueError, TypeError, KeyError, RuntimeError):
                # Retain exact intent when ownership is absent, ambiguous or unavailable.
                continue
        for rec in children:
            if rec.attempt_state == "terminal" or rec.state is not LifecycleState.RUNNING:
                continue
            path = directory / "results" / f"{rec.node.id}.result.json"
            try:
                publish_exact_child_result(scheduler, rec, path)
            except (OSError, ValueError, TypeError, KeyError):
                # A malformed or mismatched result remains quarantined.
                continue
        for rec in children:
            if rec.attempt_state != "terminal" or rec.cleanup_complete:
                continue
            try:
                runner = SubprocessHerdrRunner(os.environ.get(
                    "HERDR_REAL_BINARY", "/home/agentops/.local/bin/herdr"))
                runtime = HerdrChildRuntime(
                    scheduler, runner, cwd=root,
                    snapshot_path=directory / "swarm.json",
                    admission_registry=AdmissionRegistry())
                if rec.pre_delivery_failure and not rec.execution_pane:
                    if rec.pre_delivery_pane_creation_attempted:
                        runtime.recover_interrupted_child_start(rec.id)
                        continue
                    runtime.admission_registry.release(
                        rec.agent_id, now=scheduler.current_time(),
                        task_id=rec.id, fencing_token=rec.fencing_token)
                    scheduler.mark_pre_delivery_cleanup_complete(rec.id)
                    continue
                if rec.pre_delivery_failure:
                    runtime.cleanup_bound_pre_delivery(rec.id)
                else:
                    runtime.cleanup_bound_child(rec.id)
                scheduler.mark_pre_delivery_cleanup_complete(rec.id) if rec.pre_delivery_failure else scheduler.mark_child_cleanup_complete(rec.id)
            except (OSError, ValueError, TypeError, KeyError, RuntimeError):
                # Retain the terminal result, but never open the parent gate.
                continue
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError):
        return


@contextmanager
def parent_attempt_guard(root: Path, parent_task_id: str, run_token: str, *,
                         reconcile_results: bool = False):
    """Serialize child claims with parent attempt transitions."""
    if not parent_task_id or not run_token:
        yield False
        return
    directory = ensure_attempt_directory(root, parent_task_id, run_token)
    with (directory / "bridge.lock").open("a+") as handle:
        _fsync_directory(directory)
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            repair_initialization(directory, parent_task_id, run_token)
            if reconcile_results:
                reconcile_child_results(root, parent_task_id, run_token)
            yield all_children_terminal(root, parent_task_id, run_token, lock_held=True)
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def all_children_terminal(root: Path, parent_task_id: str, run_token: str, *,
                          lock_held: bool = False) -> bool:
    """Fail closed on a missing identity or an incomplete/corrupt existing ledger."""
    if not parent_task_id or not run_token:
        return False
    directory = attempt_directory(root, parent_task_id, run_token)
    ledger = directory / "scheduler.jsonl"
    if not directory.exists():
        return True
    try:
        if initialization_pending(directory, parent_task_id, run_token):
            return False
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        return False
    if ledger.is_file() and not ledger_required(directory):
        return False
    if not ledger.is_file():
        return lock_held and not os.path.lexists(ledger) and not ledger_required(directory)
    try:
        scheduler = replay_host_scheduler(root,ledger)
        events = scheduler.audit_log.replay()
        parent = scheduler._tasks.get(parent_task_id)
        if not events or not any(e.get("event") == "submit" and
                                 e.get("task_id") == parent_task_id for e in events) or (
                                     parent is None or parent.run_token != run_token):
            return False
        children = [rec for rec in scheduler._tasks.values()
                    if rec.delegation_key is not None and
                    rec.parent_task_id == parent_task_id and
                    rec.parent_run_token == run_token]
        # A spawn event that failed to reconstruct is an unresolved child.
        spawned = [e for e in events if e.get("event") == "spawn_child"]
        if len(children) != len(spawned) or any(
            e.get("parent_id") != parent_task_id or
            e.get("parent_run_token") != run_token for e in spawned
        ):
            return False
        for rec in children:
            if rec.ownership is not None and rec.result_status == "completed":
                scheduler._require_current_ownership(rec)
        return all(rec.attempt_state == "terminal" and
                   (bool(rec.pre_delivery_failure) and rec.cleanup_complete or
                    rec.result_status in {"completed", "blocked", "failed"} and
                    (not rec.execution_pane or rec.cleanup_complete)) and rec.lease is None and
                   rec.state in {LifecycleState.DONE, LifecycleState.FAILED,
                                 LifecycleState.BLOCKED} for rec in children)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError):
        return False
