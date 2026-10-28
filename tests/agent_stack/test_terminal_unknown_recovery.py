"""Synthetic recovery tests; never inspect or mutate the live queue/provider."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

from herdr import recovery_unknown as unknown
from herdr.evidence import EvidenceError, binding, canonical, digest
from herdr.security import SecurityError

SOURCE = Path(__file__).resolve().parents[2]


def script(name):
    loader = SourceFileLoader("unknown_test_" + name.replace("-", "_"),
                              str(SOURCE / "agent-stack/bin" / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    value = importlib.util.module_from_spec(spec)
    loader.exec_module(value)
    return value


def put(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else canonical(value) + b"\n")
    path.chmod(0o600)
    return path


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root, storage = tmp_path / "queue", tmp_path / "policy"
    for state in ("blocked", "pending", "running", "done", "failed", "results"):
        (root / state).mkdir(mode=0o700, parents=True, exist_ok=True)
    identity = {"task_id": "synthetic-185", "run_token": "original-run",
                "agent_id": "original-agent", "fencing_token": 7}
    task = {"id": "synthetic-185", "run_token": "original-run",
            "idempotency_key": "original-semantic-key", "attempt_id": 6, "attempts": 6,
            "fencing_token": 7, "attempt_state": "delivery_uncertain",
            "delivery_reconcile_pending": True,
            "watchdog_blocker": "delivery_uncertain_requires_recovery",
            "recovery_action": "await_exact_result_from_live_session",
            "work_contract_version": 1, "work_contract": {"phase": "work", "identity": identity},
            "execution_session": {"bridge_pid": 0, "sandbox_pid": 123,
                                  "pane_marker": "retained-marker"},
            "max_model_calls": 40, "max_cost_microusd": 10000000,
            "delivery_reconcile_count": 19, "observed_execution": {"state": "settled"},
            "permission_grant": {"tools": ["read_file"]},
            "not_before": "2000-01-01T00:00:00+00:00"}
    path = put(root / "blocked/synthetic-185.json", task)
    result = put(root / "results/synthetic-185.json", b"")
    events = put(storage / "work-contracts" / digest(binding(task)) / "events.jsonl",
                 b"".join(canonical({"event": event}) + b"\n" for event in
                          ("work_plan", "work_discovery", "work_plan_gate", "work_baseline")))
    ledger = put(storage / "work-budget" / ("a" * 64) / "events.jsonl",
                 b"".join(canonical({"record": row}) + b"\n" for row in [
                     {"event": "work_budget_attempt", "identity": identity},
                     {"event": "work_budget_reserve", "identity": identity,
                      "operation_id": "original-unknown", "demand": {"model_calls": 1, "cost_microusd": 0}},
                     {"event": "work_budget_start", "operation_id": "original-unknown"}]))
    decisions = tmp_path / "decisions"
    decisions.mkdir(mode=0o700)
    monkeypatch.setattr(unknown, "DECISIONS", decisions)
    monkeypatch.setattr(unknown, "_read_configuration", lambda _: {
        "host_uid": os.geteuid(), "task_store_root": str(root), "storage": str(storage)})
    # Unit fixtures have no privileged approval. Keep the real snapshot implementation
    # for all other files; root metadata/ancestry is tested separately.
    original_snapshot = unknown.snapshot
    def unit_snapshot(p, **kwargs):
        if Path(p).parent == decisions:
            kwargs.update(owner=os.geteuid(), protected=False)
        return original_snapshot(p, **kwargs)
    monkeypatch.setattr(unknown, "snapshot", unit_snapshot)
    report = unknown.inspect(root, task["id"])
    decision = {k: report[k] for k in
                ("task_id", "binding_sha256", "expected_state_sha256",
                 "result", "budget_ledgers", "work_events_sha256")}
    decision.update(schema_version="herdr-terminal-unknown-decision-1",
                    action="terminal_unknown_preserve_accounting", evidence_sha256="e" * 64,
                    issued_at_epoch=int(time.time()) - 1, expires_at_epoch=int(time.time()) + 100,
                    approval_reference="synthetic-operator-approval",
                    writer_scope="reviewed_writers_quiesced_and_locked")
    approval = put(unknown.decision_path(task["id"]), decision)
    return dict(root=root, storage=storage, task=task, path=path, result=result,
                events=events, ledger=ledger, decision=decision, approval=approval,
                real_snapshot=original_snapshot)


def apply(p):
    return unknown.apply(p["root"], p["task"]["id"], active_workers=lambda: set())


def test_terminal_unknown_preserves_exact_history_accounting_and_original_slot(prepared):
    p = prepared
    before = {key: p[key].read_bytes() for key in ("path", "result", "events", "ledger")}
    inode = p["result"].stat().st_ino
    assert apply(p)["status"] == "terminal_unknown"
    task = json.loads(p["path"].read_bytes())
    assert task["attempt_state"] == "terminal_unknown"
    assert task["delivery_reconcile_pending"] is False
    assert binding(task) == binding(p["task"])
    for key in p["task"]:
        if key not in {"attempt_state", "delivery_reconcile_pending", "watchdog_blocker", "recovery_action"}:
            assert task[key] == p["task"][key]
    assert not any(key in task for key in ("result_status", "finished_at", "completion_bundle_hash"))
    assert not list((p["root"] / "done").iterdir())
    assert not list((p["root"] / "failed").iterdir())
    assert not list((p["root"] / "pending").iterdir())
    assert p["result"].stat().st_ino == inode
    for key in ("result", "events", "ledger"):
        assert p[key].read_bytes() == before[key]
    receipt = json.loads(next((p["root"] / "results").glob("*.watchdog-terminal-unknown-*.json")).read_bytes())
    assert bytes.fromhex(receipt["original_task_bytes_hex"]) == before["path"]
    assert receipt["original_task_sha256"] == unknown.hashlib.sha256(before["path"]).hexdigest()
    assert receipt["task_acceptance"] == "UNKNOWN"
    assert receipt["after_task"] == task
    assert apply(p)["status"] == "already_terminal_unknown"
    # Idempotent handling does not replace the task, receipt, result or audit.
    stamps = {f: (f.stat().st_ino, f.stat().st_mtime_ns, f.read_bytes())
              for f in p["root"].rglob("*.json")}
    assert apply(p)["status"] == "already_terminal_unknown"
    assert stamps == {f: (f.stat().st_ino, f.stat().st_mtime_ns, f.read_bytes()) for f in stamps}


def test_interrupted_task_write_resumes_only_original_receipt(prepared, monkeypatch):
    p = prepared
    original = unknown._write
    def crash(path, raw, **kwargs):
        if path == p["path"]:
            raise OSError("synthetic crash after durable intent")
        return original(path, raw, **kwargs)
    monkeypatch.setattr(unknown, "_write", crash)
    before = p["path"].read_bytes()
    with pytest.raises(OSError):
        apply(p)
    assert p["path"].read_bytes() == before
    assert len(list((p["root"] / "results").glob("*.watchdog-terminal-unknown-*.json"))) == 1
    monkeypatch.setattr(unknown, "_write", original)
    assert apply(p)["status"] == "terminal_unknown"


@pytest.mark.parametrize("change", [
    "run", "fence", "attempt", "permission", "budget", "extra_budget", "events",
    "result", "nonempty_result", "child", "worker", "bridge", "expired", "foreign_queue",
    "already_accepted", "decision_duplicate_key", "boolean_time", "bad_result_schema",
])
def test_unapproved_or_active_inputs_fail_without_task_transition(prepared, change, monkeypatch):
    p = prepared
    task = copy.deepcopy(p["task"])
    workers = lambda: set()
    if change in {"run", "fence", "attempt", "permission", "already_accepted"}:
        if change == "run": task["run_token"] = "different-run"
        if change == "fence": task["fencing_token"] += 1
        if change == "attempt": task["attempt_id"] += 1
        if change == "permission": task["permission_grant"]["tools"].append("write_file")
        if change == "already_accepted": task["verification_status"] = "accepted"
        put(p["path"], task)
    elif change == "budget": put(p["ledger"], p["ledger"].read_bytes() + b"{}\n")
    elif change == "extra_budget":
        put(p["storage"] / "work-budget" / ("b" * 64) / "events.jsonl",
            {"identity": task["work_contract"]["identity"], "event": "work_budget_reserve"})
    elif change == "events": put(p["events"], p["events"].read_bytes() + b'{"event":"work_result"}\n')
    elif change == "result":
        original_inode = p["result"].stat().st_ino
        p["result"].rename(p["result"].with_name("retained-original-slot"))
        put(p["result"], b"")
        assert p["result"].stat().st_ino != original_inode
    elif change == "nonempty_result": put(p["result"], b'{"status":"completed"}')
    elif change == "child":
        from agent_durable_children import ensure_attempt_directory
        put(ensure_attempt_directory(p["root"], task["id"], task["run_token"]) / "child.json", {})
    elif change == "worker": workers = lambda: {"unrelated-worker"}
    elif change == "bridge":
        task["execution_session"]["bridge_pid"] = os.getpid();put(p["path"], task)
    elif change in {"expired", "boolean_time", "bad_result_schema"}:
        d = p["decision"]
        if change == "expired": d.update(issued_at_epoch=1, expires_at_epoch=2)
        if change == "boolean_time": d["issued_at_epoch"] = True
        if change == "bad_result_schema": d["result"]["inode"] = True
        put(p["approval"], d)
    elif change == "decision_duplicate_key":
        raw = p["approval"].read_bytes().rstrip()
        put(p["approval"], raw[:-1] + b',"action":"terminal_unknown_preserve_accounting"}')
    elif change == "foreign_queue":
        monkeypatch.setattr(unknown, "_read_configuration", lambda _: {
            "host_uid": os.geteuid(), "task_store_root": str(p["root"] / "other"),
            "storage": str(p["storage"])})
    before = p["path"].read_bytes()
    with pytest.raises((EvidenceError, OSError)):
        unknown.apply(p["root"], task["id"], active_workers=workers)
    assert p["path"].read_bytes() == before
    assert not list((p["root"] / "results").glob("*.watchdog-terminal-unknown-*.json"))


@pytest.mark.parametrize("name", ["recovery.lock", "dispatcher.lock", "worker.loop.lock"])
def test_another_writer_lock_blocks_transition(prepared, name):
    p = prepared
    import fcntl
    path = put(p["root"] / name, b"")
    with path.open("r+") as owner:
        fcntl.flock(owner, fcntl.LOCK_EX)
        before = p["path"].read_bytes()
        with pytest.raises(EvidenceError, match="writer_active"):
            apply(p)
        assert p["path"].read_bytes() == before


def test_named_symlinks_and_replaced_receipt_fail_closed(prepared):
    p = prepared
    real = p["ledger"].with_name("retained")
    p["ledger"].rename(real);p["ledger"].symlink_to(real)
    with pytest.raises(OSError): apply(p)
    p["ledger"].unlink();real.rename(p["ledger"])
    apply(p)
    receipt = next((p["root"] / "results").glob("*.watchdog-terminal-unknown-*.json"))
    original = receipt.read_bytes()
    value = json.loads(original);value["after_task"]["fencing_token"] += 1
    put(receipt, value)
    with pytest.raises(EvidenceError, match="terminal_receipt_changed"): apply(p)


def test_observation_drift_is_retained_but_semantic_drift_is_not(prepared):
    p = prepared
    task = copy.deepcopy(p["task"])
    task.update(observed_execution={"state": "settled", "at": "later"},
                delivery_reconcile_count=20, not_before="later")
    put(p["path"], task)
    assert apply(p)["status"] == "terminal_unknown"
    actual = json.loads(p["path"].read_bytes())
    assert actual["observed_execution"] == task["observed_execution"]


def test_protected_loader_rejects_agent_owned_approval_and_symlink(prepared):
    p = prepared
    # Real root ancestry rejects this ordinary-user directory, even though the
    # parser unit fixtures replace the privileged approval read above.
    with pytest.raises((EvidenceError, SecurityError, OSError, RuntimeError)):
        p["real_snapshot"](p["approval"], owner=0, maximum=131072, protected=True)
    alias = p["root"] / "alias"
    alias.symlink_to(p["path"])
    with pytest.raises(OSError): p["real_snapshot"](alias)
    p["path"].chmod(0o622)
    with pytest.raises(EvidenceError): p["real_snapshot"](p["path"])


def test_pending_operator_decision_holds_before_any_existing_recovery_effect(prepared, monkeypatch):
    p = prepared
    recovery = script("agent-stack-recovery")
    for state in ("BLOCKED", "RUNNING", "DONE", "FAILED", "RESULTS"):
        monkeypatch.setattr(recovery, state, p["root"] / state.lower())
    monkeypatch.setattr(recovery, "ROOT", p["root"])
    def forbidden(*args, **kwargs):
        raise AssertionError("automatic effect ran for held task")
    for name in ("ensure_live_task_bridge", "matching_result", "parent_transition_guard",
                 "cleanup_task_session", "execution_observation"):
        if hasattr(recovery, name): monkeypatch.setattr(recovery, name, forbidden)
    before = p["path"].read_bytes()
    recovery.reconcile_watchdog_blocked_tasks()
    recovery.reconcile_verification_pending()
    recovery.terminalize_from_result(p["path"], p["task"], {"status": "completed"}, 900)
    recovery.block_orphan(p["path"], p["task"], reason="synthetic", age_seconds=900)
    assert p["path"].read_bytes() == before


def test_dispatch_worker_intake_and_export_hold_terminal_unknown(prepared, monkeypatch):
    p = prepared
    apply(p)
    task = json.loads(p["path"].read_bytes())
    dispatcher = script("agent-task-dispatcher")
    monkeypatch.setattr(dispatcher, "PENDING", p["root"] / "pending")
    pending = put(p["root"] / "pending/synthetic-185.json", task)
    assert dispatcher.due_tasks() == []
    assert dispatcher._launch_with_epoch(pending) == 1
    pending.unlink()
    worker = script("agent-task-worker")
    monkeypatch.setattr(worker, "ROOT", p["root"])
    def forbidden(*args, **kwargs): raise AssertionError("worker side effect")
    monkeypatch.setattr(worker, "parent_transition_guard", forbidden)
    monkeypatch.setattr(worker, "acknowledge_dispatch_admission", forbidden)
    before = p["path"].read_bytes()
    assert worker._main_with_epoch(p["path"]) == 0
    for function in (worker.prepare_attempt, worker.run_prompt):
        with pytest.raises(EvidenceError): function(task)
    with pytest.raises(EvidenceError): worker.start_bridge(task, {})
    worker.retry(p["path"], task, "never retry")
    worker.finish(p["path"], task, "late payload")
    assert worker.cleanup_task_session_if_safe(task) is False
    assert p["path"].read_bytes() == before
    intake = script("agent-github-intake")
    records = [{"task": task, "path": p["path"], "state": "blocked"}]
    assert intake.intervention_blocker(records)[1] == "terminal_unknown_requires_operator_reconciliation"
    monkeypatch.setattr(intake, "approved_revision", forbidden)
    with pytest.raises(intake.AdmissionDenied):
        intake._queue_issue_locked({}, {}, records)
    with pytest.raises(intake.AdmissionDenied):
        intake.publish_task(p["root"] / "pending/new.json", task, {})
    exporter = script("agent-task-export")
    monkeypatch.setattr(exporter, "ROOT", p["root"])
    monkeypatch.setattr(exporter, "INTAKE", p["root"] / "github-intake-state.json")
    # The original task remains blocked; export never invents successful work.
    rows = exporter.rows() if hasattr(exporter, "rows") else exporter.task_rows()
    assert len(rows) == 1
    assert rows[0]["status"] == "blocked"
    assert rows[0]["blocker"] == "terminal_unknown_requires_operator_reconciliation"
    assert rows[0]["pr_number"] is None

def test_already_applied_decision_does_not_need_fresh_window(prepared, monkeypatch):
    p = prepared
    apply(p)
    monkeypatch.setattr(unknown.time, "time", lambda: p["decision"]["expires_at_epoch"] + 100)
    assert apply(p)["status"] == "already_terminal_unknown"


def test_interrupted_receipt_cannot_be_rebound_after_observation_drift(prepared, monkeypatch):
    p = prepared
    original = unknown._write
    def crash(path, raw, **kwargs):
        if path == p["path"]: raise OSError("synthetic interruption")
        return original(path, raw, **kwargs)
    monkeypatch.setattr(unknown, "_write", crash)
    with pytest.raises(OSError): apply(p)
    task = json.loads(p["path"].read_bytes());task["delivery_reconcile_count"] += 1
    put(p["path"], task)
    monkeypatch.setattr(unknown, "_write", original)
    with pytest.raises(EvidenceError, match="interrupted_receipt"): apply(p)
    assert json.loads(p["path"].read_bytes())["attempt_state"] == "delivery_uncertain"


def test_protected_decision_accepts_only_root_owned_metadata(prepared, monkeypatch):
    if os.geteuid() != 0:
        pytest.skip("privileged metadata test also run in a synthetic root-owned fixture")
    import tempfile
    p = prepared
    with tempfile.TemporaryDirectory(prefix="herdr-unknown-metadata-", dir="/run") as directory:
        root = Path(directory)
        root.chmod(0o755)
        monkeypatch.setattr(unknown, "DECISIONS", root)
        monkeypatch.setattr(unknown, "snapshot", p["real_snapshot"])
        path = put(unknown.decision_path(p["task"]["id"]), p["decision"])
        assert unknown.load_decision(p["task"]["id"])[0] == p["decision"]
        path.chmod(0o622)
        with pytest.raises(EvidenceError): unknown.load_decision(p["task"]["id"])
        path.chmod(0o600)
        os.chown(path, 1001, -1)
        with pytest.raises(EvidenceError): unknown.load_decision(p["task"]["id"])
        os.chown(path, 0, -1)
        alias = root / "retained"
        path.rename(alias);path.symlink_to(alias)
        with pytest.raises(OSError): unknown.load_decision(p["task"]["id"])

def test_uninspectable_decision_holds_all_automatic_entrypoints(prepared, monkeypatch):
    p = prepared
    original = unknown.os.lstat
    def denied(path, *args, **kwargs):
        if Path(path) == p["approval"]:
            raise PermissionError("synthetic protected decision")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(unknown.os, "lstat", denied)
    assert unknown.held(p["task"]) is True
    recovery = script("agent-stack-recovery")
    monkeypatch.setattr(recovery, "BLOCKED", p["root"] / "blocked")
    monkeypatch.setattr(recovery, "ensure_live_task_bridge",
                        lambda *args: pytest.fail("uninspectable decision did not hold"))
    before = p["path"].read_bytes()
    recovery.reconcile_watchdog_blocked_tasks()
    assert p["path"].read_bytes() == before


def test_resumed_intent_requires_successful_directory_sync_before_task_write(prepared, monkeypatch):
    p = prepared
    original_sync = unknown.os.fsync
    observations = []
    def fail_receipt_directory(fd):
        target = Path(os.readlink("/proc/self/fd/" + str(fd)))
        if target == p["root"] / "results":
            observations.append("results-sync-failed")
            raise OSError("synthetic results directory fsync failure")
        return original_sync(fd)
    monkeypatch.setattr(unknown.os, "fsync", fail_receipt_directory)
    original = p["path"].read_bytes()
    # First attempt publishes the intent's name but cannot confirm durability.
    with pytest.raises(OSError): apply(p)
    assert p["path"].read_bytes() == original
    assert list((p["root"] / "results").glob("*.watchdog-terminal-unknown-*.json"))
    # Retrying must not skip the same failed durability barrier.
    with pytest.raises(OSError): apply(p)
    assert p["path"].read_bytes() == original
    assert observations == ["results-sync-failed", "results-sync-failed"]
    def observe_sync(fd):
        if Path(os.readlink("/proc/self/fd/" + str(fd))) == p["root"] / "results":
            observations.append("results-durable")
        return original_sync(fd)
    original_write = unknown._write
    def observe_write(path, raw, **kwargs):
        if path == p["path"]:
            assert observations[-1] == "results-durable"
        return original_write(path, raw, **kwargs)
    monkeypatch.setattr(unknown.os, "fsync", observe_sync)
    monkeypatch.setattr(unknown, "_write", observe_write)
    assert apply(p)["status"] == "terminal_unknown"

@pytest.mark.parametrize("decision_only", [True, False])
def test_bridge_and_canonical_parent_composition_reject_unknown(prepared, monkeypatch, decision_only):
    p = prepared
    if not decision_only:
        apply(p)
        p["approval"].unlink()  # Persisted marker remains a hold independently.
    bridge = script("agent-durable-bridge")
    with pytest.raises(ValueError, match="terminal_unknown"):
        bridge._current_task_file(p["root"], p["task"]["id"], p["task"]["run_token"])
    from herdr.host_configuration import read_canonical_parent
    with pytest.raises(SecurityError, match="terminal_unknown"):
        read_canonical_parent(p["root"], p["task"]["id"], p["task"]["run_token"])


def test_empty_result_metadata_change_is_not_original_slot_generation(prepared):
    p = prepared
    info = p["result"].stat()
    os.utime(p["result"], ns=(info.st_atime_ns, info.st_mtime_ns + 1000000000))
    before = p["path"].read_bytes()
    with pytest.raises(EvidenceError, match="approved_inputs_changed"):
        apply(p)
    assert p["path"].read_bytes() == before
