"""Read the scheduler's durable child ledger for one parent attempt."""

import hashlib
import fcntl
import json
import os
import stat
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from herdr.scheduler import AuditLog, DynamicChildScheduler
from herdr.taskgraph import LifecycleState
from herdr.runtime import AdmissionRegistry, HerdrChildRuntime, SubprocessHerdrRunner

LEDGER_REQUIRED = "scheduler.required"


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


def ledger_required(directory: Path) -> bool:
    return os.path.lexists(directory / LEDGER_REQUIRED)


def publish_exact_child_result(scheduler: DynamicChildScheduler, rec, result_path: Path) -> str | None:
    """Publish only a result bound to this delegated child's current attempt."""
    try:
        _require_real_directory(result_path.parent)
        if not stat.S_ISREG(result_path.lstat().st_mode):
            raise ValueError("child result is not a regular file")
    except FileNotFoundError:
        return None
    result = json.loads(result_path.read_text(encoding="utf-8"))
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


def reconcile_child_results(root: Path, parent_task_id: str, run_token: str) -> None:
    """Under bridge.lock, consume exact result files from this attempt's ledger."""
    directory = attempt_directory(root, parent_task_id, run_token)
    ledger = directory / "scheduler.jsonl"
    if not ledger.is_file():
        return
    try:
        scheduler = DynamicChildScheduler(audit_log=AuditLog(ledger))
        scheduler.replay()
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
                        # Split may have created an unidentified pane.
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
    if ledger.is_file() and not ledger_required(directory):
        return False
    if not ledger.is_file():
        return lock_held and not os.path.lexists(ledger) and not ledger_required(directory)
    try:
        scheduler = DynamicChildScheduler(audit_log=AuditLog(ledger))
        scheduler.replay()
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
        return all(rec.attempt_state == "terminal" and
                   (bool(rec.pre_delivery_failure) and rec.cleanup_complete or
                    rec.result_status in {"completed", "blocked", "failed"} and
                    (not rec.execution_pane or rec.cleanup_complete)) and rec.lease is None and
                   rec.state in {LifecycleState.DONE, LifecycleState.FAILED,
                                 LifecycleState.BLOCKED} for rec in children)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError):
        return False
