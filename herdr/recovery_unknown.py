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
from datetime import datetime

from .evidence import EvidenceError, binding, canonical, digest
from .security import SecurityError
from .host_configuration import _read_configuration
from .policy_launch import _verify_root_owned_ancestry

DECISIONS = Path("/etc/herdr/recovery-terminal-unknown")
POLICY = Path("/etc/herdr/host-policy.json")
TERMINAL_STATE = "terminal_unknown"
VOLATILE = {"observed_execution", "not_before", "delivery_reconcile_count"}
MAX_BYTES = 8 * 1024 * 1024
RETIREMENT_MARKER_FIELDS = {
    "schema_version", "retirement_decision_sha256", "terminal_decision_sha256",
    "authorization_reference", "reason", "issued_at_epoch", "fencing_token",
}
TERMINAL_RECEIPT_FIELDS = {
    "schema_version", "decision_sha256", "evidence_sha256",
    "decision_issued_at_epoch", "original_task_sha256",
    "original_task_bytes_hex", "after_task", "budget_ledgers",
    "work_events_sha256", "classification", "task_acceptance",
}
RETIREMENT_RECEIPT_FIELDS = {
    "schema_version", "retirement_decision_sha256",
    "terminal_decision_sha256", "terminal_evidence_sha256",
    "terminal_receipt_sha256", "original_task_sha256",
    "original_task_bytes_hex", "after_task", "budget_ledgers",
    "work_events_sha256", "result", "classification",
    "task_acceptance", "accounting", "automatic_retry_allowed",
}
LATE_EVIDENCE_FIELDS = {
    "schema_version", "retirement_event_sha256", "result_sha256",
    "result_status", "reconciled_at", "verification_status",
    "completion_bundle_hash", "work_events_sha256",
}
LATE_EVIDENCE_MUTABLE_FIELDS = {
    "attempt_state", "watchdog_blocker", "recovery_action",
    "delivery_reconcile_pending", "watchdog_resolution",
    "watchdog_resolved_at", "result_status", "finished_at",
    "completion_level", "completion_bundle_hash", "verification_status",
    "verification_failures", "verification_resolution",
    "verification_next_action", "not_before", "watchdog_cleanup_blocker",
    "last_error", "terminal_unknown_late_evidence",
}


def need(value, reason):
    if not value:
        raise EvidenceError("terminal_unknown_" + reason)


def task_name(value):
    need(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value),
         "task_identity")
    return value


def decision_path(task_id):
    return DECISIONS / (task_name(task_id) + ".json")


def retirement_path(task_id):
    return DECISIONS / (task_name(task_id) + ".retirement.json")


def _retirement_marker(task):
    marker = task.get("terminal_unknown_retirement") if isinstance(task, dict) else None
    if marker is None:
        return None
    need(type(marker) is dict and set(marker) == RETIREMENT_MARKER_FIELDS
         and marker["schema_version"] == "herdr-terminal-unknown-retirement-marker-1",
         "retirement_marker_schema")
    for key in ("retirement_decision_sha256", "terminal_decision_sha256"):
        need(type(marker[key]) is str and re.fullmatch("[0-9a-f]{64}", marker[key]),
             "retirement_marker_digest")
    need(type(marker["authorization_reference"]) is str
         and 0 < len(marker["authorization_reference"]) <= 128,
         "retirement_marker_authorization")
    need(type(marker["reason"]) is str and marker["reason"] == marker["reason"].strip()
         and 0 < len(marker["reason"]) <= 512, "retirement_marker_reason")
    need(type(marker["issued_at_epoch"]) is int and marker["issued_at_epoch"] > 0
         and type(marker["fencing_token"]) is int and marker["fencing_token"] > 0,
         "retirement_marker_identity")
    return marker


def _authorized_retirement_marker(task):
    marker = _retirement_marker(task)
    if marker is None:
        return None
    decision, decision_sha = load_retirement_decision(task_name(task.get("id")))
    need(marker["retirement_decision_sha256"] == decision_sha
         and marker["terminal_decision_sha256"] == decision["terminal_decision_sha256"]
         and marker["authorization_reference"] == decision["approval_reference"]
         and marker["reason"] == decision["reason"]
         and marker["issued_at_epoch"] == decision["issued_at_epoch"]
         and marker["fencing_token"] == decision["expected_fencing_token"],
         "retirement_marker_authorization_changed")
    return marker


def retired(root, task):
    """True only while the exact root-authorized retired state remains valid."""
    try:
        return _retirement_inspection(Path(root), task_name(task.get("id")), task) is not None
    except (EvidenceError, OSError, TypeError, ValueError):
        return False


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


def blocks_intake(root, task):
    """Release intake only while a complete protected retirement chain validates."""
    if not held(task):
        return False
    return not (retired(root, task) or late_evidence_reconciled(root, task))


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


def load_retirement_decision(task_id):
    raw, _ = snapshot(retirement_path(task_id), owner=0, maximum=131072, protected=True)
    value = _json(raw)
    fields = {
        "schema_version", "action", "task_id", "binding_sha256",
        "expected_state_sha256", "terminal_decision_sha256",
        "expected_event_commitment_sha256", "expected_fencing_token",
        "reason", "issued_at_epoch",
        "expires_at_epoch", "approval_reference", "writer_scope",
    }
    need(type(value) is dict and set(value) == fields
         and value["schema_version"] == "herdr-terminal-unknown-retirement-decision-1"
         and value["action"] == "terminal_unknown_retire_active_blocker"
         and value["task_id"] == task_id
         and value["writer_scope"] == "reviewed_writers_quiesced_and_locked",
         "retirement_decision_schema")
    for key in ("binding_sha256", "expected_state_sha256",
                "terminal_decision_sha256", "expected_event_commitment_sha256"):
        need(type(value[key]) is str and re.fullmatch("[0-9a-f]{64}", value[key]),
             "retirement_decision_digest")
    need(type(value["expected_fencing_token"]) is int
         and value["expected_fencing_token"] > 0, "retirement_fencing_token")
    need(type(value["reason"]) is str and value["reason"] == value["reason"].strip()
         and 0 < len(value["reason"]) <= 512, "retirement_reason")
    need(type(value["approval_reference"]) is str
         and 0 < len(value["approval_reference"]) <= 128,
         "retirement_approval_reference")
    need(all(type(value[k]) is int for k in ("issued_at_epoch", "expires_at_epoch"))
         and 0 < value["expires_at_epoch"] - value["issued_at_epoch"] <= 3600,
         "retirement_decision_lifetime")
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


def _retirement_receipt_path(root, task_id, retirement_decision_sha):
    return (Path(root) / "results" /
            (task_id + ".watchdog-terminal-unknown-retirement-" +
             retirement_decision_sha + ".json"))


def _retirement_event_commitment(receipt):
    """Hash every event field without circularly hashing the decision digest."""
    value = copy.deepcopy(receipt)
    need(type(value) is dict and set(value) == RETIREMENT_RECEIPT_FIELDS,
         "retirement_receipt_schema")
    value["retirement_decision_sha256"] = None
    marker = value.get("after_task", {}).get("terminal_unknown_retirement")
    need(type(marker) is dict and set(marker) == RETIREMENT_MARKER_FIELDS,
         "retirement_marker_schema")
    marker["retirement_decision_sha256"] = None
    return digest(value)


def _terminal_state_invariants(task, terminal_sha, *, retired_state):
    need(type(task) is dict and task.get("attempt_state") == TERMINAL_STATE,
         "retirement_terminal_state_required")
    need(task.get("delivery_terminal_unknown") == {
        "schema_version": "herdr-terminal-unknown-marker-1",
        "decision_sha256": terminal_sha,
        "classification": "UNKNOWN",
        "accounting": "preserved_unknown",
    }, "retirement_terminal_marker_changed")
    need(not task.get("result_status") and not task.get("finished_at")
         and not task.get("completion_bundle_hash")
         and task.get("verification_status") != "accepted",
         "retirement_existing_terminal_evidence")
    if retired_state:
        need(task.get("automatic_retry_allowed") is False
             and task.get("recovery_action") ==
                 "terminal_unknown_retired_await_verified_late_evidence",
             "retirement_state_invariants")
    else:
        need("terminal_unknown_retirement" not in task,
             "retirement_original_task_changed")


def _validate_terminal_receipt(
        root, task_id, terminal, terminal_sha, after_task, ledgers, events):
    path = (Path(root) / "results" /
            (task_id + ".watchdog-terminal-unknown-" + terminal_sha + ".json"))
    raw, _ = snapshot(path, maximum=MAX_BYTES)
    receipt = _json(raw)
    need(type(receipt) is dict and set(receipt) == TERMINAL_RECEIPT_FIELDS
         and receipt["schema_version"] ==
             "herdr-terminal-unknown-recovery-receipt-1"
         and receipt["decision_sha256"] == terminal_sha
         and receipt["evidence_sha256"] == terminal["evidence_sha256"]
         and receipt["decision_issued_at_epoch"] == terminal["issued_at_epoch"]
         and receipt["classification"] == "UNKNOWN"
         and receipt["task_acceptance"] == "UNKNOWN"
         and receipt["after_task"] == after_task
         and receipt["budget_ledgers"] == ledgers
         and receipt["work_events_sha256"] == events,
         "retirement_terminal_receipt_changed")
    try:
        original_raw = bytes.fromhex(receipt["original_task_bytes_hex"])
    except (TypeError, ValueError) as exc:
        raise EvidenceError(
            "terminal_unknown_terminal_original_task_encoding") from exc
    original = _json(original_raw)
    need(canonical(original) + b"\n" == original_raw
         and hashlib.sha256(original_raw).hexdigest() ==
             receipt["original_task_sha256"]
         and original.get("id") == task_id
         and digest(binding(original)) == terminal["binding_sha256"]
         and stable_state(original) == terminal["expected_state_sha256"],
         "retirement_terminal_history_changed")
    return raw, receipt, original


def _work_events_raw(root, task):
    storage = _policy(Path(root))
    path = (storage / "work-contracts" / digest(binding(task)) / "events.jsonl")
    raw, _ = snapshot(path)
    return raw


def late_work_events_sha256(root, task):
    """Hash the exact current work log for a protected late-evidence marker."""
    return hashlib.sha256(_work_events_raw(root, task)).hexdigest()


def _event_rows(raw):
    rows = []
    for line in raw.splitlines(keepends=True):
        need(line.endswith(b"\n"), "late_work_event_line")
        row = _json(line[:-1])
        need(type(row) is dict and canonical(row) + b"\n" == line,
             "late_work_event_encoding")
        rows.append(row)
    return rows


def _late_work_event_inspection(raw, baseline_sha256, task, result):
    boundaries, position = [0], 0
    for line in raw.splitlines(keepends=True):
        need(line.endswith(b"\n"), "late_work_event_line")
        position += len(line)
        boundaries.append(position)
    matches = [offset for offset in boundaries
               if hashlib.sha256(raw[:offset]).hexdigest() == baseline_sha256]
    need(len(matches) == 1, "late_work_event_baseline")
    prefix, suffix = raw[:matches[0]], raw[matches[0]:]
    current_sha256 = hashlib.sha256(raw).hexdigest()
    contract = task.get("work_contract")
    need(type(contract) is dict
         and type(contract.get("identity")) is dict
         and type(contract.get("plan_sha256")) is str
         and re.fullmatch("[0-9a-f]{64}", contract["plan_sha256"]),
         "late_work_contract_identity")
    identity, plan_sha256 = contract["identity"], contract["plan_sha256"]

    if not suffix:
        bundle = None
        if contract.get("phase") == "finished":
            prefix_rows = _event_rows(prefix)
            need(bool(prefix_rows), "late_work_handoff_missing")
            last = prefix_rows[-1]
            need(set(last) == {"event", "work_cycle", "plan_sha256",
                               "bundle_sha256"}
                 and last["event"] == "work_handoff"
                 and last["work_cycle"] == identity
                 and last["plan_sha256"] == plan_sha256
                 and type(last["bundle_sha256"]) is str
                 and re.fullmatch("[0-9a-f]{64}", last["bundle_sha256"]),
                 "late_work_handoff_changed")
            bundle = last["bundle_sha256"]
        return {"work_events_sha256": current_sha256,
                "appended_event_count": 0,
                "completion_bundle_hash": bundle,
                "completion_complete": bundle is not None}

    rows = _event_rows(suffix)
    for row in rows:
        need(row.get("work_cycle") == identity
             and row.get("plan_sha256") == plan_sha256,
             "late_work_event_identity")

    index, checks, tree_sha256, passed = 0, set(), None, False
    while index < len(rows) and rows[index].get("event") == "work_check":
        row = rows[index]
        need(set(row) == {"event", "work_cycle", "plan_sha256", "check"},
             "late_work_check_schema")
        from .work_cycle import CheckResult
        proof = CheckResult(**row["check"])
        need(type(proof.check_id) is str and 0 < len(proof.check_id) <= 128
             and proof.check_id not in checks
             and proof.plan_sha256 == plan_sha256
             and (contract.get("environment_sha256") is None
                  or proof.environment_sha256 ==
                     contract["environment_sha256"])
             and not proof.truncated,
             "late_work_check_changed")
        if tree_sha256 is None:
            tree_sha256 = proof.tree_sha256
        need(proof.tree_sha256 == tree_sha256, "late_work_check_tree_changed")
        checks.add(proof.check_id)
        index += 1

    if index < len(rows) and rows[index].get("event") == "work_pass":
        row = rows[index]
        need(set(row) == {"event", "work_cycle", "plan_sha256", "tree_sha256"}
             and type(row["tree_sha256"]) is str
             and re.fullmatch("[0-9a-f]{64}", row["tree_sha256"])
             and (tree_sha256 is None or tree_sha256 == row["tree_sha256"]),
             "late_work_pass_changed")
        tree_sha256 = row["tree_sha256"]
        passed = True
        index += 1
    need(not checks or passed, "late_work_pass_missing")

    need(index < len(rows) and rows[index].get("event") == "work_commit",
         "late_work_commit_missing")
    commit = rows[index]
    need(set(commit) == {"event", "work_cycle", "plan_sha256",
                         "commit_sha", "artifact"},
         "late_work_commit_schema")
    from .evidence import parse_artifact
    artifact = parse_artifact(commit["artifact"])
    attempt = task.get("attempt_id", task.get("attempts", 0))
    need(artifact.task_id == task.get("id")
         and artifact.attempt == attempt
         and artifact.commit_sha == commit["commit_sha"],
         "late_work_commit_changed")
    from .result_candidate import completion_candidate
    candidate = completion_candidate(result)
    need(candidate.get("artifact") == commit["artifact"],
         "late_work_result_artifact_changed")
    index += 1

    need(index == len(rows) - 1
         and rows[index].get("event") == "work_handoff",
         "late_work_handoff_missing")
    handoff = rows[index]
    need(set(handoff) == {"event", "work_cycle", "plan_sha256",
                          "bundle_sha256"}
         and type(handoff["bundle_sha256"]) is str
         and re.fullmatch("[0-9a-f]{64}", handoff["bundle_sha256"]),
         "late_work_handoff_changed")
    return {"work_events_sha256": current_sha256,
            "appended_event_count": len(rows),
            "completion_bundle_hash": handoff["bundle_sha256"],
            "completion_complete": True}


def _timestamp(value):
    if type(value) is not str or not value or len(value) > 128:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _late_execution_session_transition(before, after):
    if before == after:
        return True
    if (type(before) is not dict or type(after) is not dict
            or before.get("owned_pane") is not True
            or before.get("closed_at")):
        return False
    expected = copy.deepcopy(before)
    expected.pop("cleanup_error", None)
    status = after.get("cleanup_status")
    closed_at = after.get("closed_at")
    if status in {"already_absent", "closed"} and _timestamp(closed_at):
        expected["closed_at"] = closed_at
        expected["cleanup_status"] = status
    elif status == "superseded_identity_proven" and _timestamp(closed_at):
        evidence = after.get("cleanup_evidence")
        if (after.get("superseded_at") != closed_at
                or type(evidence) is not dict
                or set(evidence) != {"version", "expected_agent_absent",
                                     "current_pane_unbound",
                                     "ownership_marker_absent",
                                     "shell_started_after_session_seconds",
                                     "current_pane_close_performed"}
                or evidence["version"] != 1
                or evidence["expected_agent_absent"] is not True
                or evidence["current_pane_unbound"] is not True
                or evidence["ownership_marker_absent"] is not True
                or evidence["current_pane_close_performed"] is not False
                or type(evidence["shell_started_after_session_seconds"]) is not int
                or evidence["shell_started_after_session_seconds"] < 0):
            return False
        expected["superseded_at"] = closed_at
        expected["closed_at"] = closed_at
        expected["cleanup_status"] = status
        expected["cleanup_evidence"] = evidence
    else:
        return False
    return after == expected


def _late_task_history_transition(retired_task, task, expected_state):
    before, after = copy.deepcopy(retired_task), copy.deepcopy(task)
    before_contract = before.pop("work_contract", None)
    after_contract = after.pop("work_contract", None)
    before_session = before.pop("execution_session", None)
    after_session = after.pop("execution_session", None)
    for field in LATE_EVIDENCE_MUTABLE_FIELDS:
        before.pop(field, None)
        after.pop(field, None)
    if before != after:
        return False
    if before_contract != after_contract:
        if expected_state != "done" or type(before_contract) is not dict:
            return False
        expected_contract = copy.deepcopy(before_contract)
        expected_contract["phase"] = "finished"
        if after_contract != expected_contract:
            return False
    return _late_execution_session_transition(before_session, after_session)


def _retirement_inspection(root, task_id, task, *, late_result=None):
    root = Path(root)
    marker = _authorized_retirement_marker(task)
    if marker is None:
        return None
    retirement, retirement_sha = load_retirement_decision(task_id)
    terminal, terminal_sha = load_decision(task_id)
    need(marker["retirement_decision_sha256"] == retirement_sha
         and marker["terminal_decision_sha256"] == terminal_sha
         and retirement["terminal_decision_sha256"] == terminal_sha,
         "retirement_decision_chain_changed")
    need(task.get("id") == task_id
         and task.get("fencing_token") == retirement["expected_fencing_token"]
         and digest(binding(task)) == retirement["binding_sha256"],
         "retirement_task_binding_changed")
    _terminal_state_invariants(task, terminal_sha, retired_state=True)

    path = _retirement_receipt_path(root, task_id, retirement_sha)
    raw, _ = snapshot(path, maximum=MAX_BYTES)
    receipt = _json(raw)
    need(type(receipt) is dict and set(receipt) == RETIREMENT_RECEIPT_FIELDS
         and receipt["schema_version"] ==
             "herdr-terminal-unknown-retirement-receipt-1"
         and receipt["retirement_decision_sha256"] == retirement_sha
         and receipt["terminal_decision_sha256"] == terminal_sha
         and receipt["terminal_evidence_sha256"] == terminal["evidence_sha256"]
         and receipt["classification"] == "UNKNOWN"
         and receipt["task_acceptance"] == "UNKNOWN"
         and receipt["accounting"] == "preserved_unknown"
         and receipt["automatic_retry_allowed"] is False
         and receipt["after_task"] == task,
         "retirement_receipt_changed")
    need(_retirement_event_commitment(receipt) ==
         retirement["expected_event_commitment_sha256"],
         "retirement_event_commitment_changed")

    try:
        original_raw = bytes.fromhex(receipt["original_task_bytes_hex"])
    except (TypeError, ValueError) as exc:
        raise EvidenceError("terminal_unknown_retirement_original_task_encoding") from exc
    need(hashlib.sha256(original_raw).hexdigest() ==
         receipt["original_task_sha256"], "retirement_original_task_digest_changed")
    original_task = _json(original_raw)
    need(canonical(original_task) + b"\n" == original_raw
         and original_task.get("id") == task_id
         and digest(binding(original_task)) == retirement["binding_sha256"]
         and stable_state(original_task) == retirement["expected_state_sha256"]
         and original_task.get("fencing_token") == retirement["expected_fencing_token"],
         "retirement_original_task_changed")
    _terminal_state_invariants(original_task, terminal_sha, retired_state=False)

    storage = _policy(root)
    baseline_events = terminal["work_events_sha256"]
    late_work = {"work_events_sha256": baseline_events,
                 "appended_event_count": 0,
                 "completion_bundle_hash": None,
                 "completion_complete": False}
    if late_result is None:
        result, ledgers, events = _observations(root, storage, task)
        need(result == terminal["result"]
             and events == baseline_events,
             "retirement_result_slot_changed")
    else:
        result_path = root / "results" / (task_id + ".json")
        result_raw, result_info = snapshot(result_path, maximum=1048576)
        result_value = _json(result_raw)
        need(type(late_result) is dict and result_value == late_result
             and result_info.st_dev == terminal["result"]["device"]
             and result_info.st_ino == terminal["result"]["inode"]
             and len(result_raw) > 0,
             "retirement_late_result_slot_changed")
        ledgers = _ledgers(storage, task)
        event_raw = _work_events_raw(root, task)
        late_work = _late_work_event_inspection(
            event_raw, baseline_events, task, late_result)
    need(ledgers == terminal["budget_ledgers"]
         and receipt["result"] == terminal["result"]
         and receipt["budget_ledgers"] == ledgers
         and receipt["work_events_sha256"] == baseline_events,
         "retirement_evidence_chain_changed")

    terminal_raw, _, _ = _validate_terminal_receipt(
        root, task_id, terminal, terminal_sha, original_task, ledgers,
        baseline_events)
    need(hashlib.sha256(terminal_raw).hexdigest() ==
         receipt["terminal_receipt_sha256"],
         "retirement_terminal_receipt_changed")

    outcome = {
        "operationally_retired": True,
        "retirement_decision_sha256": retirement_sha,
        "terminal_decision_sha256": terminal_sha,
        "authorization_reference": marker["authorization_reference"],
        "reason": marker["reason"],
        "issued_at_epoch": marker["issued_at_epoch"],
        "fencing_token": marker["fencing_token"],
        "event_sha256": hashlib.sha256(raw).hexdigest(),
        "event_commitment_sha256":
            retirement["expected_event_commitment_sha256"],
    }
    if late_result is not None:
        outcome.update({
            "work_events_sha256": late_work["work_events_sha256"],
            "appended_work_event_count": late_work["appended_event_count"],
            "work_completion_bundle_hash":
                late_work["completion_bundle_hash"],
            "work_completion_complete": late_work["completion_complete"],
        })
    return outcome


def retirement_inspection(root, task, *, late_result=None):
    """Validate the protected retirement chain, optionally with exact late evidence."""
    return _retirement_inspection(
        Path(root), task_name(task.get("id")), task,
        late_result=late_result)


def _late_evidence_inspection(root, task):
    root, task_id = Path(root), task_name(task.get("id"))
    late = task.get("terminal_unknown_late_evidence")
    need(type(late) is dict and set(late) == LATE_EVIDENCE_FIELDS
         and late["schema_version"] ==
             "herdr-terminal-unknown-late-evidence-1"
         and type(late["retirement_event_sha256"]) is str
         and re.fullmatch("[0-9a-f]{64}", late["retirement_event_sha256"])
         and type(late["result_sha256"]) is str
         and re.fullmatch("[0-9a-f]{64}", late["result_sha256"])
         and type(late["work_events_sha256"]) is str
         and re.fullmatch("[0-9a-f]{64}", late["work_events_sha256"])
         and type(late["result_status"]) is str
         and type(late["reconciled_at"]) is str,
         "late_evidence_marker_schema")

    marker = _authorized_retirement_marker(task)
    need(marker is not None, "late_evidence_retirement_marker")
    receipt_path = _retirement_receipt_path(
        root, task_id, marker["retirement_decision_sha256"])
    receipt_raw, _ = snapshot(receipt_path, maximum=MAX_BYTES)
    receipt = _json(receipt_raw)
    need(type(receipt) is dict and set(receipt) == RETIREMENT_RECEIPT_FIELDS
         and type(receipt["after_task"]) is dict,
         "late_evidence_retirement_receipt")
    retired_task = receipt["after_task"]

    result_path = root / "results" / (task_id + ".json")
    result_raw, _ = snapshot(result_path, maximum=1048576)
    result = _json(result_raw)
    status = result.get("status")
    blocker = str(result.get("blocker") or "").strip().lower()
    expected_state = (
        "blocked" if blocker not in {"", "none", "null"}
        else "done" if status == "completed"
        else "failed" if status == "failed"
        else "blocked")

    history = _retirement_inspection(
        root, task_id, retired_task, late_result=result)
    need(history is not None
         and late["retirement_event_sha256"] == history["event_sha256"]
         and late["result_sha256"] == digest(result)
         and late["work_events_sha256"] ==
             history["work_events_sha256"],
         "late_evidence_history_changed")
    if expected_state == "done":
        need(history["work_completion_complete"] is True
             and history["work_completion_bundle_hash"] ==
                 task.get("completion_bundle_hash"),
             "late_evidence_work_completion_changed")
    else:
        need(history["appended_work_event_count"] == 0
             and history["work_completion_complete"] is False,
             "late_evidence_unexpected_work_completion")

    need(_late_task_history_transition(
             retired_task, task, expected_state)
         and task.get("terminal_unknown_retirement") ==
             retired_task.get("terminal_unknown_retirement")
         and task.get("delivery_terminal_unknown") ==
             retired_task.get("delivery_terminal_unknown")
         and task.get("automatic_retry_allowed") is False,
         "late_evidence_task_history_changed")

    need(result.get("task_id") == task_id
         and result.get("run_token") == task.get("run_token")
         and status in {"completed", "blocked", "failed"}
         and task.get("result_status") == status
         and late["result_status"] == status
         and task.get("watchdog_resolution") == "exact_durable_result"
         and late["reconciled_at"] == task.get("watchdog_resolved_at")
         and type(task.get("finished_at")) is str
         and "delivery_reconcile_pending" not in task
         and "recovery_action" not in task,
         "late_evidence_transition_changed")
    need(task.get("attempt_state") == expected_state,
         "late_evidence_terminal_state_changed")
    if expected_state == "done":
        need(task.get("verification_status") == "accepted"
             and type(task.get("completion_bundle_hash")) is str
             and bool(task["completion_bundle_hash"]),
             "late_evidence_verification_missing")
    need(late["verification_status"] == task.get("verification_status")
         and late["completion_bundle_hash"] ==
             task.get("completion_bundle_hash"),
         "late_evidence_verification_changed")
    return {
        "late_evidence_reconciled": True,
        "retirement_event_sha256": history["event_sha256"],
        "result_sha256": late["result_sha256"],
        "result_status": status,
    }


def late_evidence_reconciled(root, task):
    try:
        return _late_evidence_inspection(root, task) is not None
    except (EvidenceError, OSError, TypeError, ValueError):
        return False


def inspect(root, task_id):
    """Read-only preparation; no approval/configuration file is created."""
    root, task_id = Path(root), task_name(task_id)
    storage = _policy(root)
    _, _, _, task = _task(root, task_id)
    result, ledgers, events = _observations(root, storage, task)
    marker = task.get("delivery_terminal_unknown")
    retirement = _retirement_inspection(root, task_id, task)
    return {"schema_version": "herdr-terminal-unknown-inspection-2", "task_id": task_id,
            "binding_sha256": digest(binding(task)), "expected_state_sha256": stable_state(task),
            "result": result, "budget_ledgers": ledgers, "work_events_sha256": events,
            "decision_present": os.path.lexists(decision_path(task_id)),
            "retirement_decision_present": os.path.lexists(retirement_path(task_id)),
            "task_acceptance": ("UNKNOWN" if isinstance(marker, dict) else None),
            "accounting": (marker.get("accounting") if isinstance(marker, dict) else None),
            "automatic_retry_allowed": task.get("automatic_retry_allowed"),
            "operational_retirement": retirement,
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


def retire(root, task_id, *, active_workers):
    """Retire only the cross-task intake blocker; UNKNOWN remains immutable."""
    root, task_id = Path(root), task_name(task_id)
    need(callable(active_workers), "worker_observer_required")
    retirement, retirement_sha = load_retirement_decision(task_id)
    terminal, terminal_sha = load_decision(task_id)
    need(retirement["terminal_decision_sha256"] == terminal_sha,
         "retirement_terminal_decision_changed")
    storage = _policy(root)
    with ExitStack() as locks:
        for name in ("recovery.lock", "dispatcher.lock", "worker.loop.lock"):
            locks.enter_context(queue_lock(root, name))
        path, raw, stamp, task = _task(root, task_id)
        marker = _authorized_retirement_marker(task)
        receipt_path = _retirement_receipt_path(root, task_id, retirement_sha)
        if marker is not None:
            need(marker["retirement_decision_sha256"] == retirement_sha
                 and marker["terminal_decision_sha256"] == terminal_sha,
                 "retirement_marker_changed")
            inspection = _retirement_inspection(root, task_id, task)
            need(inspection is not None
                 and inspection["retirement_decision_sha256"] == retirement_sha,
                 "retirement_receipt_changed")
            directory = _directory(path.parent)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return {"status": "already_terminal_unknown_retired", "task_id": task_id,
                    "task_acceptance": "UNKNOWN", "accounting": "preserved_unknown",
                    "automatic_retry_allowed": False, "accounting_mutated": False}
        need(retirement["issued_at_epoch"] <= time.time() < retirement["expires_at_epoch"],
             "retirement_approval_expired")
        need(digest(binding(task)) == retirement["binding_sha256"],
             "retirement_decision_identity")
        need(stable_state(task) == retirement["expected_state_sha256"],
             "retirement_approved_state_changed")
        need(task.get("fencing_token") == retirement["expected_fencing_token"],
             "retirement_fence_changed")
        terminal_marker = task.get("delivery_terminal_unknown")
        need(task.get("attempt_state") == TERMINAL_STATE
             and terminal_marker == {
                 "schema_version": "herdr-terminal-unknown-marker-1",
                 "decision_sha256": terminal_sha,
                 "classification": "UNKNOWN",
                 "accounting": "preserved_unknown",
             }, "retirement_terminal_state_required")
        need(not task.get("result_status") and not task.get("finished_at")
             and not task.get("completion_bundle_hash")
             and task.get("verification_status") != "accepted",
             "retirement_existing_terminal_evidence")
        from agent_durable_children import ensure_attempt_directory
        children = ensure_attempt_directory(root, task_id, task["run_token"])
        locks.enter_context(queue_lock(children, "bridge.lock"))
        need(set(os.listdir(children)) <= {"bridge.lock"},
             "retirement_child_ledger_requires_reconciliation")
        need(not active_workers(), "retirement_worker_active")
        bridge_pid = (task.get("execution_session") or {}).get("bridge_pid", 0)
        need(type(bridge_pid) is int and bridge_pid >= 0
             and (bridge_pid == 0 or not Path("/proc", str(bridge_pid)).exists()),
             "retirement_bridge_active")
        result, ledgers, events = _observations(root, storage, task)
        need(result == terminal["result"] and ledgers == terminal["budget_ledgers"]
             and events == terminal["work_events_sha256"],
             "retirement_approved_inputs_changed")
        terminal_receipt_raw, _, _ = _validate_terminal_receipt(
            root, task_id, terminal, terminal_sha, task, ledgers, events)
        after = copy.deepcopy(task)
        after["automatic_retry_allowed"] = False
        after["recovery_action"] = "terminal_unknown_retired_await_verified_late_evidence"
        after["terminal_unknown_retirement"] = {
            "schema_version": "herdr-terminal-unknown-retirement-marker-1",
            "retirement_decision_sha256": retirement_sha,
            "terminal_decision_sha256": terminal_sha,
            "authorization_reference": retirement["approval_reference"],
            "reason": retirement["reason"],
            "issued_at_epoch": retirement["issued_at_epoch"],
            "fencing_token": retirement["expected_fencing_token"],
        }
        receipt = {
            "schema_version": "herdr-terminal-unknown-retirement-receipt-1",
            "retirement_decision_sha256": retirement_sha,
            "terminal_decision_sha256": terminal_sha,
            "terminal_evidence_sha256": terminal["evidence_sha256"],
            "terminal_receipt_sha256": hashlib.sha256(terminal_receipt_raw).hexdigest(),
            "original_task_sha256": hashlib.sha256(raw).hexdigest(),
            "original_task_bytes_hex": raw.hex(),
            "after_task": after,
            "budget_ledgers": ledgers,
            "work_events_sha256": events,
            "result": result,
            "classification": "UNKNOWN",
            "task_acceptance": "UNKNOWN",
            "accounting": "preserved_unknown",
            "automatic_retry_allowed": False,
        }
        need(_retirement_event_commitment(receipt) ==
             retirement["expected_event_commitment_sha256"],
             "retirement_event_not_authorized")
        receipt_bytes = canonical(receipt) + b"\n"
        try:
            _write(receipt_path, receipt_bytes, exclusive=True)
        except FileExistsError:
            old, _ = snapshot(receipt_path, maximum=MAX_BYTES)
            need(old == receipt_bytes,
                 "interrupted_retirement_receipt_requires_reconciliation")
            directory = _directory(receipt_path.parent)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        current, current_stamp = snapshot(path, maximum=1048576)
        need(current == raw and _stamp(current_stamp) == _stamp(stamp),
             "task_changed_before_retirement")
        need(_observations(root, storage, task) == (result, ledgers, events),
             "inputs_changed_before_retirement")
        current_terminal_receipt, _, _ = _validate_terminal_receipt(
            root, task_id, terminal, terminal_sha, task, ledgers, events)
        need(current_terminal_receipt == terminal_receipt_raw,
             "terminal_receipt_changed_before_retirement")
        _write(path, canonical(after) + b"\n")
        return {"status": "terminal_unknown_retired", "task_id": task_id,
                "task_acceptance": "UNKNOWN", "accounting": "preserved_unknown",
                "automatic_retry_allowed": False, "accounting_mutated": False,
                "event_sha256": hashlib.sha256(receipt_bytes).hexdigest()}
