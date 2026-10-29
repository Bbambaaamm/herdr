"""Administrative UNKNOWN for the existing durable recovery, never task success.

A root-owned operator decision is an input to recovery, not a second queue or
budget ledger. Default automation only holds such a task. Applying the decision
requires the explicit recovery command; it never collects, settles, or replays.
"""
from contextlib import ExitStack, contextmanager
from pathlib import Path
import copy
import ctypes
import fcntl
import hashlib
import json
import os
import re
import stat
import time
import uuid

from .evidence import EvidenceError, binding, canonical, digest
from .security import SecurityError
from .host_configuration import _read_configuration
from .policy_launch import _verify_root_owned_ancestry

DECISIONS = Path("/etc/herdr/recovery-terminal-unknown")
POLICY = Path("/etc/herdr/host-policy.json")
TERMINAL_STATE = "terminal_unknown"
VOLATILE = {"observed_execution", "not_before", "delivery_reconcile_count"}
MAX_BYTES = 8 * 1024 * 1024


def need(value, reason):
    if not value:
        raise EvidenceError("terminal_unknown_" + reason)


def task_name(value):
    need(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value),
         "task_identity")
    return value


def decision_path(task_id):
    return DECISIONS / (task_name(task_id) + ".json")


def held(task):
    """Fail closed on a marker or even an invalid pending operator decision."""
    if not isinstance(task, dict):
        return False
    if task.get("attempt_state") == TERMINAL_STATE or "delivery_terminal_unknown" in task:
        return True
    try:
        path = decision_path(task.get("id"))
        os.lstat(path)
        return True
    except (EvidenceError, FileNotFoundError):
        return False  # Existing callers validate malformed/non-task inputs.
    except OSError:
        return True


def stable_state(task):
    value = copy.deepcopy(task)
    for field in VOLATILE:
        value.pop(field, None)
    # Observational PID can change during watchdog retries. The original run,
    # fence, bridge identity, sandbox and grant remain part of the binding.
    if isinstance(value.get("execution_session"), dict):
        value["execution_session"].pop("bridge_pid", None)
    return digest(value)


def _json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            need(key not in value, "duplicate_json_field")
            value[key] = item
        return value
    try:
        return json.loads(raw, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError) as exc:
        raise EvidenceError("terminal_unknown_invalid_json") from exc


def _directory(path):
    path = Path(path)
    need(path.is_absolute() and ".." not in path.parts, "absolute_directory")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = nxt
        return fd
    except BaseException:
        os.close(fd)
        raise


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def snapshot(path, *, owner=None, maximum=MAX_BYTES, protected=False):
    path = Path(path)
    if protected:
        _verify_root_owned_ancestry(path.parent)
    directory = _directory(path.parent)
    fd = None
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                     dir_fd=directory)
        before = os.fstat(fd)
        owner = os.geteuid() if owner is None else owner
        need(stat.S_ISREG(before.st_mode) and before.st_uid == owner
             and before.st_nlink == 1 and not before.st_mode & 0o022
             and before.st_size <= maximum, "unsafe_snapshot")
        raw = bytearray()
        while len(raw) <= maximum:
            block = os.read(fd, min(65536, maximum + 1 - len(raw)))
            if not block:
                break
            raw.extend(block)
        named = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        need(len(raw) == before.st_size and _stamp(before) == _stamp(os.fstat(fd)) == _stamp(named),
             "snapshot_changed")
        return bytes(raw), before
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


def load_decision(task_id):
    raw, _ = snapshot(decision_path(task_id), owner=0, maximum=131072, protected=True)
    value = _json(raw)
    fields = {"schema_version", "action", "task_id", "binding_sha256", "expected_state_sha256",
              "evidence_sha256", "budget_ledgers", "work_events_sha256", "result",
              "issued_at_epoch", "expires_at_epoch", "approval_reference", "writer_scope"}
    need(type(value) is dict and set(value) == fields
         and value["schema_version"] == "herdr-terminal-unknown-decision-1"
         and value["action"] == "terminal_unknown_preserve_accounting"
         and value["task_id"] == task_id
         and value["writer_scope"] == "reviewed_writers_quiesced_and_locked", "decision_schema")
    for key in ("binding_sha256", "expected_state_sha256", "evidence_sha256", "work_events_sha256"):
        need(type(value[key]) is str and re.fullmatch("[0-9a-f]{64}", value[key]), "decision_digest")
    need(type(value["approval_reference"]) is str and 0 < len(value["approval_reference"]) <= 128,
         "approval_reference")
    need(all(type(value[k]) is int for k in ("issued_at_epoch", "expires_at_epoch"))
         and 0 < value["expires_at_epoch"] - value["issued_at_epoch"] <= 3600, "decision_lifetime")
    need(type(value["result"]) is dict and set(value["result"]) ==
         {"device", "inode", "bytes", "sha256", "mtime_ns", "ctime_ns"}
         and all(type(value["result"][k]) is int and value["result"][k] >= 0
                 for k in ("device", "inode", "bytes", "mtime_ns", "ctime_ns"))
         and value["result"]["bytes"] == 0
         and value["result"]["sha256"] == hashlib.sha256(b"").hexdigest(), "result_binding")
    need(type(value["budget_ledgers"]) is list and 1 <= len(value["budget_ledgers"]) <= 1024,
         "budget_binding")
    for row in value["budget_ledgers"]:
        need(type(row) is dict and set(row) == {"path", "sha256", "bytes"}
             and type(row["path"]) is str
             and re.fullmatch(r"work-budget/[0-9a-f]{64}/events.jsonl", row["path"])
             and type(row["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", row["sha256"])
             and type(row["bytes"]) is int and 0 < row["bytes"] <= MAX_BYTES, "budget_binding")
    need(len({r["path"] for r in value["budget_ledgers"]}) == len(value["budget_ledgers"]),
         "duplicate_budget_binding")
    return value, hashlib.sha256(raw).hexdigest()


def _task(root, task_id):
    locations = [root / state / (task_id + ".json")
                 for state in ("blocked", "pending", "running", "done", "failed")]
    present = [p for p in locations if os.path.lexists(p)]
    need(len(present) == 1 and present[0].parent.name == "blocked", "canonical_blocked_task_required")
    raw, info = snapshot(present[0], maximum=1048576)
    value = _json(raw)
    need(type(value) is dict and value.get("id") == task_id, "task_identity")
    return present[0], raw, info, value


def _policy(root):
    value = _read_configuration(POLICY)
    need(root.is_absolute() and root.resolve(strict=True) == root, "queue_path")
    need(value.get("host_uid") == os.geteuid()
         and Path(value.get("task_store_root", "")) == root, "host_policy_scope")
    storage = Path(value["storage"])
    need(storage.is_absolute() and storage.resolve(strict=True) == storage, "storage_scope")
    return storage


def _ledgers(storage, task):
    folder = storage / "work-budget"
    expected_identities = (task["work_contract"]["identity"], binding(task))
    files = sorted(folder.glob("*/events.jsonl"))
    need(len(files) <= 1024, "ledger_inventory_bound")
    found, total = [], 0
    for path in files:
        need(re.fullmatch("[0-9a-f]{64}", path.parent.name), "ledger_path")
        raw, _ = snapshot(path)
        total += len(raw)
        need(total <= 64 * 1024 * 1024, "ledger_byte_bound")
        rows = [_json(line) for line in raw.splitlines() if line]
        need(all(type(r) is dict for r in rows), "ledger_record_schema")
        rows = [r.get("record", r) for r in rows]
        need(all(type(r) is dict for r in rows), "ledger_record_schema")
        if any(r.get("identity", r.get("work_cycle")) in expected_identities for r in rows):
            found.append({"path": str(path.relative_to(storage)),
                          "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    need(bool(found), "original_budget_ledger_required")
    return found


def _observations(root, storage, task):
    result_path = root / "results" / (task["id"] + ".json")
    raw, info = snapshot(result_path, maximum=1048576)
    need(raw == b"", "empty_original_result_required")
    result = {"device": info.st_dev, "inode": info.st_ino, "bytes": len(raw),
              "mtime_ns": info.st_mtime_ns, "ctime_ns": info.st_ctime_ns,
              "sha256": hashlib.sha256(raw).hexdigest()}
    path = storage / "work-contracts" / digest(binding(task)) / "events.jsonl"
    events_raw, _ = snapshot(path)
    events = [_json(line) for line in events_raw.splitlines() if line]
    need(all(type(r) is dict for r in events), "work_record_schema")
    events = [r.get("record", r) for r in events]
    need(all(type(r) is dict for r in events), "work_record_schema")
    need([r.get("event") for r in events] ==
         ["work_plan", "work_discovery", "work_plan_gate", "work_baseline"],
         "baseline_only_recovery_scope")
    return result, _ledgers(storage, task), hashlib.sha256(events_raw).hexdigest()


@contextmanager
def queue_lock(root, name):
    directory = _directory(root)
    fd = None
    try:
        info = os.fstat(directory)
        need(info.st_uid == os.geteuid() and not info.st_mode & 0o022, "queue_owner")
        fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                     0o600, dir_fd=directory)
        info = os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
             and not info.st_mode & 0o022 and info.st_nlink == 1, "lock_identity")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise EvidenceError("terminal_unknown_writer_active") from None
        named = os.stat(name, dir_fd=directory, follow_symlinks=False)
        need((info.st_dev, info.st_ino) == (named.st_dev, named.st_ino), "lock_changed")
        yield
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


def _write(path, raw, *, exclusive=False):
    directory = _directory(path.parent)
    temporary = ".terminal-unknown-" + uuid.uuid4().hex
    try:
        info = os.fstat(directory)
        need(info.st_uid == os.geteuid() and not info.st_mode & 0o022, "output_directory_owner")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=directory)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            # Atomic no-replace publication has no two-link crash window.
            libc = ctypes.CDLL(None, use_errno=True)
            rename = getattr(libc, "renameat2", None)
            need(rename is not None, "exclusive_publication_unavailable")
            rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                               ctypes.c_char_p, ctypes.c_uint]
            rename.restype = ctypes.c_int
            if rename(directory, os.fsencode(temporary), directory,
                      os.fsencode(path.name), 1) != 0:
                code = ctypes.get_errno()
                raise OSError(code, os.strerror(code), path.name)
        else:
            os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass
        os.close(directory)


def inspect(root, task_id):
    """Read-only preparation; no approval/configuration file is created."""
    root, task_id = Path(root), task_name(task_id)
    storage = _policy(root)
    _, _, _, task = _task(root, task_id)
    result, ledgers, events = _observations(root, storage, task)
    return {"schema_version": "herdr-terminal-unknown-inspection-1", "task_id": task_id,
            "binding_sha256": digest(binding(task)), "expected_state_sha256": stable_state(task),
            "result": result, "budget_ledgers": ledgers, "work_events_sha256": events,
            "decision_present": os.path.lexists(decision_path(task_id)),
            "activation_performed": False, "accounting_mutation_performed": False}


def apply(root, task_id, *, active_workers):
    """Explicit administrative delivery closure, not result acceptance."""
    root, task_id = Path(root), task_name(task_id)
    need(callable(active_workers), "worker_observer_required")
    decision, decision_sha = load_decision(task_id)
    storage = _policy(root)
    with ExitStack() as locks:
        for name in ("recovery.lock", "dispatcher.lock", "worker.loop.lock"):
            locks.enter_context(queue_lock(root, name))
        path, raw, stamp, task = _task(root, task_id)
        need(digest(binding(task)) == decision["binding_sha256"], "decision_identity")
        need(not task.get("parent_task_id") and task.get("work_contract_version") == 1,
             "root_modern_attempt_required")
        # Acquire the EXISTING child-claim lock without initialization/replay,
        # release, verification, or resource cleanup.
        from agent_durable_children import ensure_attempt_directory
        children = ensure_attempt_directory(root, task_id, task["run_token"])
        locks.enter_context(queue_lock(children, "bridge.lock"))
        need(set(os.listdir(children)) <= {"bridge.lock"}, "child_ledger_requires_separate_reconciliation")
        need(not active_workers(), "worker_active")
        bridge_pid = (task.get("execution_session") or {}).get("bridge_pid", 0)
        need(type(bridge_pid) is int and bridge_pid >= 0
             and (bridge_pid == 0 or not Path("/proc", str(bridge_pid)).exists()), "bridge_active")
        result, ledgers, events = _observations(root, storage, task)
        need(result == decision["result"] and ledgers == decision["budget_ledgers"]
             and events == decision["work_events_sha256"], "approved_inputs_changed")
        receipt_path = root / "results" / (task_id + ".watchdog-terminal-unknown-" + decision_sha + ".json")
        marker = task.get("delivery_terminal_unknown")
        if marker is not None:
            need(task.get("attempt_state") == TERMINAL_STATE
                 and marker == {"schema_version": "herdr-terminal-unknown-marker-1",
                                "decision_sha256": decision_sha, "classification": "UNKNOWN",
                                "accounting": "preserved_unknown"}, "terminal_marker_changed")
            receipt_raw, _ = snapshot(receipt_path, maximum=MAX_BYTES)
            receipt = _json(receipt_raw)
            need(receipt.get("decision_sha256") == decision_sha
                 and receipt.get("after_task") == task, "terminal_receipt_changed")
            # A visible marker can follow a failed task-directory fsync.
            # Re-establish durability before acknowledging the original decision.
            directory = _directory(path.parent)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return {"status": "already_terminal_unknown", "task_id": task_id,
                    "task_acceptance": "UNKNOWN", "accounting_mutated": False}
        need(decision["issued_at_epoch"] <= time.time() < decision["expires_at_epoch"], "approval_expired")
        need(task.get("attempt_state") == "delivery_uncertain"
             and task.get("delivery_reconcile_pending") is True
             and task.get("watchdog_blocker") == "delivery_uncertain_requires_recovery"
             and task["work_contract"].get("phase") == "work", "original_uncertain_state_required")
        need(stable_state(task) == decision["expected_state_sha256"], "approved_state_changed")
        need(not task.get("completion_bundle_hash") and task.get("verification_status") != "accepted"
             and not task.get("result_status") and not task.get("finished_at"),
             "existing_terminal_evidence_requires_reconciliation")
        after = copy.deepcopy(task)
        after.update(attempt_state=TERMINAL_STATE, delivery_reconcile_pending=False,
                     watchdog_blocker="terminal_unknown_delivery",
                     recovery_action="await_explicit_late_evidence_reconciliation")
        after["delivery_terminal_unknown"] = {
            "schema_version": "herdr-terminal-unknown-marker-1", "decision_sha256": decision_sha,
            "classification": "UNKNOWN", "accounting": "preserved_unknown"}
        # No result_status/finished_at/accepted flag: work acceptance stays unknown.
        receipt = {"schema_version": "herdr-terminal-unknown-recovery-receipt-1",
                   "decision_sha256": decision_sha, "evidence_sha256": decision["evidence_sha256"],
                   "decision_issued_at_epoch": decision["issued_at_epoch"],
                   "original_task_sha256": hashlib.sha256(raw).hexdigest(),
                   "original_task_bytes_hex": raw.hex(), "after_task": after,
                   "budget_ledgers": ledgers, "work_events_sha256": events,
                   "classification": "UNKNOWN", "task_acceptance": "UNKNOWN"}
        receipt_bytes = canonical(receipt) + b"\n"
        try:
            _write(receipt_path, receipt_bytes, exclusive=True)
        except FileExistsError:
            old, _ = snapshot(receipt_path, maximum=MAX_BYTES)
            need(old == receipt_bytes, "interrupted_receipt_requires_reconciliation")
            # A prior rename can be visible without a durable directory entry.
            # Re-establish the intent barrier even after an fsync failure/restart.
            directory = _directory(receipt_path.parent)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        # Recheck the exact task and all immutable inputs AFTER durable intent.
        current, current_stamp = snapshot(path, maximum=1048576)
        need(current == raw and _stamp(current_stamp) == _stamp(stamp), "task_changed_before_transition")
        need(_observations(root, storage, task) == (result, ledgers, events), "inputs_changed_before_transition")
        _write(path, canonical(after) + b"\n")
        return {"status": "terminal_unknown", "task_id": task_id, "task_acceptance": "UNKNOWN",
                "accounting_mutated": False, "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest()}
