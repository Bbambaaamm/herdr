"""Synthetic recovery tests; never inspect or mutate the live queue/provider."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

from herdr import recovery_unknown as unknown
from herdr.evidence import EvidenceError, binding, canonical, digest
from herdr.security import SecurityError

SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE / "agent-stack/bin"))


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
            "work_contract_version": 1,
            "work_contract": {"phase": "work", "identity": identity,
                              "plan_sha256": "1" * 64},
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


def authorize_retirement(p, *, reason="operator retired active blocker; UNKNOWN retained"):
    report = unknown.inspect(p["root"], p["task"]["id"])
    terminal_decision_sha = unknown.hashlib.sha256(p["approval"].read_bytes()).hexdigest()
    decision = {
        "schema_version": "herdr-terminal-unknown-retirement-decision-1",
        "action": "terminal_unknown_retire_active_blocker",
        "task_id": p["task"]["id"],
        "binding_sha256": report["binding_sha256"],
        "expected_state_sha256": report["expected_state_sha256"],
        "terminal_decision_sha256": terminal_decision_sha,
        "expected_fencing_token": 7,
        "reason": reason,
        "issued_at_epoch": int(time.time()) - 1,
        "expires_at_epoch": int(time.time()) + 100,
        "approval_reference": "synthetic-retirement-approval",
        "writer_scope": "reviewed_writers_quiesced_and_locked",
    }
    task = json.loads(p["path"].read_bytes())
    terminal_receipt = next(
        path for path in (p["root"] / "results").glob(
            "*.watchdog-terminal-unknown-*.json")
        if "retirement" not in path.name)
    after = copy.deepcopy(task)
    after["automatic_retry_allowed"] = False
    after["recovery_action"] = (
        "terminal_unknown_retired_await_verified_late_evidence")
    after["terminal_unknown_retirement"] = {
        "schema_version": "herdr-terminal-unknown-retirement-marker-1",
        "retirement_decision_sha256": "0" * 64,
        "terminal_decision_sha256": terminal_decision_sha,
        "authorization_reference": decision["approval_reference"],
        "reason": reason,
        "issued_at_epoch": decision["issued_at_epoch"],
        "fencing_token": decision["expected_fencing_token"],
    }
    event = {
        "schema_version": "herdr-terminal-unknown-retirement-receipt-1",
        "retirement_decision_sha256": "0" * 64,
        "terminal_decision_sha256": terminal_decision_sha,
        "terminal_evidence_sha256": p["decision"]["evidence_sha256"],
        "terminal_receipt_sha256":
            unknown.hashlib.sha256(terminal_receipt.read_bytes()).hexdigest(),
        "original_task_sha256":
            unknown.hashlib.sha256(p["path"].read_bytes()).hexdigest(),
        "original_task_bytes_hex": p["path"].read_bytes().hex(),
        "after_task": after,
        "budget_ledgers": report["budget_ledgers"],
        "work_events_sha256": report["work_events_sha256"],
        "result": report["result"],
        "classification": "UNKNOWN",
        "task_acceptance": "UNKNOWN",
        "accounting": "preserved_unknown",
        "automatic_retry_allowed": False,
    }
    decision["expected_event_commitment_sha256"] = (
        unknown._retirement_event_commitment(event))
    approval = put(unknown.retirement_path(p["task"]["id"]), decision)
    p.update(retirement_decision=decision, retirement_approval=approval)
    return decision


def retire(p, *, active_workers=lambda: set()):
    return unknown.retire(p["root"], p["task"]["id"], active_workers=active_workers)


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


def test_operator_retirement_releases_only_cross_task_intake_blocker(prepared):
    p = prepared
    apply(p)
    authorize_retirement(p)
    terminal_receipt = next(
        path for path in (p["root"] / "results").glob("*.watchdog-terminal-unknown-*.json")
        if "retirement" not in path.name)
    immutable = {key: p[key].read_bytes() for key in ("result", "events", "ledger")}
    immutable["terminal_receipt"] = terminal_receipt.read_bytes()
    outcome = retire(p)
    assert outcome == {
        "status": "terminal_unknown_retired",
        "task_id": "synthetic-185",
        "task_acceptance": "UNKNOWN",
        "accounting": "preserved_unknown",
        "automatic_retry_allowed": False,
        "accounting_mutated": False,
        "event_sha256": outcome["event_sha256"],
    }
    task = json.loads(p["path"].read_bytes())
    assert task["attempt_state"] == "terminal_unknown"
    assert task["automatic_retry_allowed"] is False
    assert task["delivery_terminal_unknown"]["classification"] == "UNKNOWN"
    assert task["delivery_terminal_unknown"]["accounting"] == "preserved_unknown"
    assert not any(key in task for key in
                   ("result_status", "finished_at", "completion_bundle_hash"))
    assert unknown.held(task) is True
    assert unknown.retired(p["root"], task) is True
    assert unknown.blocks_intake(p["root"], task) is False
    tampered = copy.deepcopy(task)
    tampered["terminal_unknown_retirement"]["reason"] = "forged reason"
    assert unknown.retired(p["root"], tampered) is False
    assert unknown.blocks_intake(p["root"], tampered) is True
    report = unknown.inspect(p["root"], p["task"]["id"])
    assert report["schema_version"] == "herdr-terminal-unknown-inspection-2"
    assert report["task_acceptance"] == "UNKNOWN"
    assert report["accounting"] == "preserved_unknown"
    assert report["automatic_retry_allowed"] is False
    assert report["operational_retirement"] == {
        "operationally_retired": True,
        "retirement_decision_sha256":
            report["operational_retirement"]["retirement_decision_sha256"],
        "terminal_decision_sha256":
            report["operational_retirement"]["terminal_decision_sha256"],
        "authorization_reference": "synthetic-retirement-approval",
        "reason": "operator retired active blocker; UNKNOWN retained",
        "issued_at_epoch": p["retirement_decision"]["issued_at_epoch"],
        "fencing_token": 7,
        "event_sha256": report["operational_retirement"]["event_sha256"],
        "event_commitment_sha256":
            p["retirement_decision"]["expected_event_commitment_sha256"],
    }
    assert {key: p[key].read_bytes() for key in ("result", "events", "ledger")} == {
        key: immutable[key] for key in ("result", "events", "ledger")}
    assert terminal_receipt.read_bytes() == immutable["terminal_receipt"]
    stamps = {path: (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes())
              for path in p["root"].rglob("*.json")}
    assert retire(p)["status"] == "already_terminal_unknown_retired"
    assert stamps == {path: (path.stat().st_ino, path.stat().st_mtime_ns, path.read_bytes())
                      for path in stamps}


def test_interrupted_retirement_resumes_only_exact_durable_event(prepared, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    original = unknown._write
    def crash(path, raw, **kwargs):
        if path == p["path"]:
            raise OSError("synthetic crash after retirement event")
        return original(path, raw, **kwargs)
    monkeypatch.setattr(unknown, "_write", crash)
    before = p["path"].read_bytes()
    with pytest.raises(OSError):
        retire(p)
    assert p["path"].read_bytes() == before
    receipts = list((p["root"] / "results").glob(
        "*.watchdog-terminal-unknown-retirement-*.json"))
    assert len(receipts) == 1
    event = receipts[0].read_bytes()
    monkeypatch.setattr(unknown, "_write", original)
    assert retire(p)["status"] == "terminal_unknown_retired"
    assert receipts[0].read_bytes() == event


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


@pytest.mark.parametrize("change", [
    "wrong_fence", "changed_state", "changed_ledger", "changed_terminal_receipt",
    "expired", "empty_reason", "wrong_terminal_decision", "active_worker",
])
def test_retirement_rejects_stale_unauthorized_or_changed_inputs(
        prepared, change, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    workers = lambda: set()
    if change == "wrong_fence":
        decision = copy.deepcopy(p["retirement_decision"])
        decision["expected_fencing_token"] = 8
        put(p["retirement_approval"], decision)
    elif change == "changed_state":
        task = json.loads(p["path"].read_bytes())
        task["permission_grant"]["tools"].append("write_file")
        put(p["path"], task)
    elif change == "changed_ledger":
        put(p["ledger"], p["ledger"].read_bytes() + b"{}\n")
    elif change == "changed_terminal_receipt":
        receipt = next(
            path for path in (p["root"] / "results").glob(
                "*.watchdog-terminal-unknown-*.json")
            if "retirement" not in path.name)
        value = json.loads(receipt.read_bytes())
        value["classification"] = "PASS"
        put(receipt, value)
    elif change in {"expired", "empty_reason", "wrong_terminal_decision"}:
        decision = copy.deepcopy(p["retirement_decision"])
        if change == "expired":
            decision.update(issued_at_epoch=1, expires_at_epoch=2)
        elif change == "empty_reason":
            decision["reason"] = ""
        else:
            decision["terminal_decision_sha256"] = "0" * 64
        put(p["retirement_approval"], decision)
    elif change == "active_worker":
        workers = lambda: {"synthetic-worker"}
    before = p["path"].read_bytes()
    with pytest.raises((EvidenceError, OSError)):
        retire(p, active_workers=workers)
    assert p["path"].read_bytes() == before
    assert not list((p["root"] / "results").glob(
        "*.watchdog-terminal-unknown-retirement-*.json"))


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
    monkeypatch.setattr(intake, "ROOT", p["root"])
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


def test_retired_unknown_still_blocks_its_execution_but_not_new_intake(
        prepared, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    retire(p)
    task = json.loads(p["path"].read_bytes())
    dispatcher = script("agent-task-dispatcher")
    monkeypatch.setattr(dispatcher, "PENDING", p["root"] / "pending")
    pending = put(p["root"] / "pending/synthetic-185.json", task)
    assert dispatcher.due_tasks() == []
    assert dispatcher._launch_with_epoch(pending) == 1
    worker = script("agent-task-worker")
    monkeypatch.setattr(worker, "ROOT", p["root"])
    for function in (worker.prepare_attempt, worker.run_prompt):
        with pytest.raises(EvidenceError, match="terminal_unknown"):
            function(task)
    intake = script("agent-github-intake")
    monkeypatch.setattr(intake, "ROOT", p["root"])
    monkeypatch.setattr(intake, "result_for", lambda _: {})
    records = [{"task": task, "path": p["path"], "state": "blocked"}]
    assert intake.intervention_blocker(records) is None
    assert unknown.held(task) is True
    assert unknown.blocks_intake(p["root"], task) is False


def test_retired_unknown_allows_only_existing_exact_late_result_verifier(
        prepared, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    retire(p)
    recovery = script("agent-stack-recovery")
    monkeypatch.setattr(recovery, "BLOCKED", p["root"] / "blocked")
    monkeypatch.setattr(recovery, "ROOT", p["root"])
    task = json.loads(p["path"].read_bytes())
    guard_calls = []
    @contextmanager
    def guard(root, task_id, run_token, *, reconcile_results):
        guard_calls.append((root, task_id, run_token, reconcile_results))
        yield True
    monkeypatch.setattr(recovery, "parent_attempt_guard", guard)
    with recovery.parent_transition_guard(task) as terminal:
        assert terminal is True
    assert guard_calls == [(recovery.ROOT, task["id"], task["run_token"], True)]
    exact = {"task_id": p["task"]["id"], "run_token": p["task"]["run_token"],
             "status": "completed"}
    observed = []
    monkeypatch.setattr(recovery, "ensure_live_task_bridge",
                        lambda *args: pytest.fail("retirement cannot restart a bridge"))
    monkeypatch.setattr(recovery, "matching_result", lambda task: (exact, "exact"))
    monkeypatch.setattr(recovery, "terminalize_from_result",
                        lambda path, task, result, age:
                        observed.append((path, task["id"], result, age)))
    recovery.reconcile_watchdog_blocked_tasks()
    assert observed == [(p["path"], p["task"]["id"], exact, 0)]


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
    monkeypatch.setattr(recovery, "ROOT", p["root"])
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


def test_visible_terminal_marker_reestablishes_task_directory_durability(prepared, monkeypatch):
    p = prepared
    real_sync = unknown.os.fsync
    failed = []
    def fail_task_directory(fd):
        if Path(os.readlink("/proc/self/fd/" + str(fd))) == p["path"].parent:
            failed.append("blocked")
            raise OSError("synthetic task directory fsync failure")
        return real_sync(fd)
    monkeypatch.setattr(unknown.os, "fsync", fail_task_directory)
    with pytest.raises(OSError, match="task directory"):
        apply(p)
    assert json.loads(p["path"].read_bytes())["attempt_state"] == "terminal_unknown"
    preserved = {f: (f.stat().st_ino, f.stat().st_mtime_ns, f.read_bytes())
                 for f in [p["path"], p["result"], p["events"], p["ledger"],
                           *list((p["root"] / "results").glob("*.watchdog-terminal-unknown-*.json"))]}
    monkeypatch.setattr(unknown, "_write", lambda *a, **kw:
                        pytest.fail("idempotent durability repair cannot rewrite task or receipt"))
    with pytest.raises(OSError, match="task directory"):
        apply(p)
    assert failed == ["blocked", "blocked"]
    durable = []
    def observed_sync(fd):
        if Path(os.readlink("/proc/self/fd/" + str(fd))) == p["path"].parent:
            durable.append("blocked")
        return real_sync(fd)
    monkeypatch.setattr(unknown.os, "fsync", observed_sync)
    assert apply(p)["status"] == "already_terminal_unknown"
    assert durable == ["blocked"]
    assert preserved == {f: (f.stat().st_ino, f.stat().st_mtime_ns, f.read_bytes()) for f in preserved}


@pytest.mark.parametrize("field", [
    "unknown_field", "terminal_evidence_sha256", "terminal_receipt_sha256",
    "original_task_sha256", "original_task_bytes_hex", "budget_ledgers",
    "work_events_sha256", "result",
])
def test_retirement_receipt_tamper_reblocks_every_entrypoint(prepared, field):
    p = prepared
    apply(p)
    authorize_retirement(p)
    retire(p)
    receipt = next((p["root"] / "results").glob(
        "*.watchdog-terminal-unknown-retirement-*.json"))
    value = json.loads(receipt.read_bytes())
    if field == "unknown_field":
        value["unreviewed"] = True
    elif field in {"terminal_evidence_sha256", "terminal_receipt_sha256",
                   "original_task_sha256", "work_events_sha256"}:
        value[field] = "0" * 64
    elif field == "original_task_bytes_hex":
        value[field] = "00"
    elif field == "budget_ledgers":
        value[field] = []
    elif field == "result":
        value[field]["inode"] += 1
    put(receipt, value)
    task = json.loads(p["path"].read_bytes())
    assert unknown.retired(p["root"], task) is False
    assert unknown.blocks_intake(p["root"], task) is True
    with pytest.raises((EvidenceError, OSError)):
        unknown.inspect(p["root"], task["id"])
    with pytest.raises((EvidenceError, OSError)):
        retire(p)


@pytest.mark.parametrize("change", [
    "missing_retirement_receipt", "terminal_receipt", "result",
    "budget_ledger", "work_events", "attempt_state", "automatic_retry",
    "delivery_marker", "result_status", "finished_at", "completion_bundle",
    "verification_status", "fencing_token", "permission_grant",
])
def test_retired_state_or_anchored_evidence_tamper_reblocks_intake(
        prepared, change):
    p = prepared
    apply(p)
    authorize_retirement(p)
    retire(p)
    task = json.loads(p["path"].read_bytes())
    if change == "missing_retirement_receipt":
        next((p["root"] / "results").glob(
            "*.watchdog-terminal-unknown-retirement-*.json")).unlink()
    elif change == "terminal_receipt":
        receipt = next(
            path for path in (p["root"] / "results").glob(
                "*.watchdog-terminal-unknown-*.json")
            if "retirement" not in path.name)
        value = json.loads(receipt.read_bytes())
        value["classification"] = "PASS"
        put(receipt, value)
    elif change == "result":
        put(p["result"], {"task_id": task["id"], "run_token": task["run_token"],
                          "status": "completed"})
    elif change == "budget_ledger":
        put(p["ledger"], p["ledger"].read_bytes() + b"{}\n")
    elif change == "work_events":
        put(p["events"], p["events"].read_bytes() + b'{"event":"work_result"}\n')
    else:
        if change == "attempt_state": task["attempt_state"] = "done"
        if change == "automatic_retry": task["automatic_retry_allowed"] = True
        if change == "delivery_marker":
            task["delivery_terminal_unknown"]["classification"] = "PASS"
        if change == "result_status": task["result_status"] = "completed"
        if change == "finished_at": task["finished_at"] = "later"
        if change == "completion_bundle": task["completion_bundle_hash"] = "a" * 64
        if change == "verification_status": task["verification_status"] = "accepted"
        if change == "fencing_token": task["fencing_token"] += 1
        if change == "permission_grant":
            task["permission_grant"]["tools"].append("write_file")
        put(p["path"], task)
    current = json.loads(p["path"].read_bytes())
    assert unknown.retired(p["root"], current) is False
    assert unknown.blocks_intake(p["root"], current) is True


def test_verified_late_evidence_has_separate_exact_state_and_history(
        prepared, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    retire(p)
    retired_bytes = p["path"].read_bytes()
    ledger_bytes, events_bytes = p["ledger"].read_bytes(), p["events"].read_bytes()
    task = json.loads(retired_bytes)
    artifact = {
        "task_id": task["id"], "attempt": task["attempt_id"],
        "base_sha": "a" * 40, "commit_sha": "b" * 40,
        "result_sha": "c" * 64, "changed_files": ["reviewed.py"],
        "branch": "codex/synthetic-185",
    }
    exact = {
        "task_id": task["id"], "run_token": task["run_token"],
        "status": "completed", "blocker": None, "artifact": artifact,
    }
    original_inode = p["result"].stat().st_ino
    put(p["result"], exact)
    assert p["result"].stat().st_ino == original_inode

    recovery = script("agent-stack-recovery")
    for name in ("ROOT", "BLOCKED", "DONE", "FAILED", "RESULTS"):
        target = p["root"] if name == "ROOT" else p["root"] / name.lower()
        monkeypatch.setattr(recovery, name, target)
    @contextmanager
    def guard(root, task_id, run_token, *, reconcile_results):
        assert (root, task_id, run_token, reconcile_results) == (
            p["root"], task["id"], task["run_token"], True)
        yield True
    class Worker:
        ROOT = None
        @staticmethod
        def modern_work_contract(value):
            return True
        @staticmethod
        def _verify_root_completion(value, result):
            assert result == exact
            identity = value["work_contract"]["identity"]
            plan = value["work_contract"]["plan_sha256"]
            tree = "d" * 64
            rows = [
                {"event": "work_check", "work_cycle": identity,
                 "plan_sha256": plan, "check": {
                     "check_id": "reviewed-check", "plan_sha256": plan,
                     "environment_sha256": "e" * 64,
                     "tree_sha256": tree, "exit_code": 0,
                     "output_sha256": "f" * 64, "truncated": False,
                     "duration_ms": 12, "isolation_sha256": "0" * 64}},
                {"event": "work_pass", "work_cycle": identity,
                 "plan_sha256": plan, "tree_sha256": tree},
                {"event": "work_commit", "work_cycle": identity,
                 "plan_sha256": plan, "commit_sha": artifact["commit_sha"],
                 "artifact": artifact},
                {"event": "work_handoff", "work_cycle": identity,
                 "plan_sha256": plan, "bundle_sha256": "b" * 64},
            ]
            put(p["events"], p["events"].read_bytes() +
                b"".join(canonical(row) + b"\n" for row in rows))
            value["work_contract"]["phase"] = "finished"
            return {"level": "root_verified", "bundle_hash": "b" * 64}
    monkeypatch.setattr(recovery, "parent_attempt_guard", guard)
    monkeypatch.setattr(recovery, "_worker_bridge", lambda: Worker())
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda value: True)
    recovery.terminalize_from_result(p["path"], task, exact, 0)

    final_path = p["root"] / "done" / p["path"].name
    final = json.loads(final_path.read_bytes())
    assert final["attempt_state"] == "done"
    assert final["automatic_retry_allowed"] is False
    assert final["delivery_terminal_unknown"]["classification"] == "UNKNOWN"
    assert final["delivery_terminal_unknown"]["accounting"] == "preserved_unknown"
    assert final["terminal_unknown_late_evidence"]["result_status"] == "completed"
    assert unknown.retired(p["root"], final) is False
    try:
        late_inspection = unknown._late_evidence_inspection(p["root"], final)
    except Exception as exc:
        pytest.fail(repr(exc))
    assert late_inspection["late_evidence_reconciled"] is True
    assert unknown.late_evidence_reconciled(p["root"], final) is True
    assert unknown.blocks_intake(p["root"], final) is False
    assert p["ledger"].read_bytes() == ledger_bytes
    assert p["events"].read_bytes().startswith(events_bytes)
    assert p["events"].read_bytes() != events_bytes

    tampered_events = p["events"].read_bytes().replace(
        b'"bundle_sha256":"' + b"b" * 64 + b'"',
        b'"bundle_sha256":"' + b"c" * 64 + b'"')
    put(p["events"], tampered_events)
    assert unknown.late_evidence_reconciled(p["root"], final) is False
    put(p["events"], events_bytes + p["events"].read_bytes()[len(events_bytes):].replace(
        b'"bundle_sha256":"' + b"c" * 64 + b'"',
        b'"bundle_sha256":"' + b"b" * 64 + b'"'))

    tampered = copy.deepcopy(final)
    tampered["permission_grant"]["tools"].append("write_file")
    assert unknown.late_evidence_reconciled(p["root"], tampered) is False
    assert unknown.blocks_intake(p["root"], tampered) is True


def test_actual_absent_pane_cleanup_is_the_only_accepted_session_delta(
        monkeypatch):
    recovery = script("agent-stack-recovery")
    before = {
        "owned_pane": True, "pane_id": "%177", "pane_marker": "owned-marker",
        "coordinator_pane_id": "%1", "bridge_pid": 0,
        "cleanup_error": "old observation",
    }
    after = copy.deepcopy(before)
    monkeypatch.setattr(recovery, "_pane_presence", lambda pane_id: False)
    assert recovery.cleanup_task_owned_pane({"execution_session": after}) is True
    assert after["cleanup_status"] == "already_absent"
    assert unknown._late_execution_session_transition(before, after) is True
    tampered = copy.deepcopy(after)
    tampered["sandbox_pid"] = 999
    assert unknown._late_execution_session_transition(before, tampered) is False


def test_failed_result_with_blocker_uses_blocked_precedence_and_reconciles(
        prepared, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    retire(p)
    task = json.loads(p["path"].read_bytes())
    exact = {
        "task_id": task["id"], "run_token": task["run_token"],
        "status": "failed", "blocker": "user_action_required",
    }
    put(p["result"], exact)
    recovery = script("agent-stack-recovery")
    for name in ("ROOT", "BLOCKED", "DONE", "FAILED", "RESULTS"):
        target = p["root"] if name == "ROOT" else p["root"] / name.lower()
        monkeypatch.setattr(recovery, name, target)

    @contextmanager
    def guard(*args, **kwargs):
        yield True

    monkeypatch.setattr(recovery, "parent_attempt_guard", guard)
    monkeypatch.setattr(
        recovery, "_worker_bridge",
        lambda: pytest.fail("blocked failed result cannot invoke verifier"))
    monkeypatch.setattr(recovery, "cleanup_task_owned_pane", lambda value: True)
    recovery.terminalize_from_result(p["path"], task, exact, 0)

    final = json.loads((p["root"] / "blocked" / p["path"].name).read_bytes())
    assert final["result_status"] == "failed"
    assert final["attempt_state"] == "blocked"
    assert unknown.late_evidence_reconciled(p["root"], final) is True
    assert unknown.blocks_intake(p["root"], final) is False


def test_failed_late_verifier_preserves_exact_retired_state(
        prepared, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    retire(p)
    original = p["path"].read_bytes()
    task = json.loads(original)
    exact = {
        "task_id": task["id"], "run_token": task["run_token"],
        "status": "completed", "blocker": None,
    }
    put(p["result"], exact)
    recovery = script("agent-stack-recovery")
    monkeypatch.setattr(recovery, "ROOT", p["root"])
    monkeypatch.setattr(recovery, "BLOCKED", p["root"] / "blocked")
    @contextmanager
    def guard(*args, **kwargs):
        yield True
    class Worker:
        ROOT = None
        @staticmethod
        def modern_work_contract(value):
            return True
        @staticmethod
        def _verify_root_completion(value, result):
            raise EvidenceError("synthetic late verifier rejection")
    monkeypatch.setattr(recovery, "parent_attempt_guard", guard)
    monkeypatch.setattr(recovery, "_worker_bridge", lambda: Worker())
    monkeypatch.setattr(
        recovery, "cleanup_task_owned_pane",
        lambda value: pytest.fail("cleanup cannot run after verifier rejection"))
    recovery.terminalize_from_result(p["path"], task, exact, 0)
    assert p["path"].read_bytes() == original
    current = json.loads(original)
    assert unknown.blocks_intake(p["root"], current) is True
    assert not list((p["root"] / "done").iterdir())


def test_expired_retry_after_durable_retirement_intent_fails_closed(
        prepared, monkeypatch):
    p = prepared
    apply(p)
    authorize_retirement(p)
    original_write = unknown._write
    def crash(path, raw, **kwargs):
        if path == p["path"]:
            raise OSError("synthetic crash after exact retirement intent")
        return original_write(path, raw, **kwargs)
    monkeypatch.setattr(unknown, "_write", crash)
    with pytest.raises(OSError):
        retire(p)
    monkeypatch.setattr(unknown, "_write", original_write)
    monkeypatch.setattr(
        unknown.time, "time",
        lambda: p["retirement_decision"]["expires_at_epoch"] + 1)
    with pytest.raises(EvidenceError, match="retirement_approval_expired"):
        retire(p)
    current = json.loads(p["path"].read_bytes())
    assert "terminal_unknown_retirement" not in current
    assert unknown.blocks_intake(p["root"], current) is True


@pytest.mark.parametrize("field", [
    "extra", "original_task_sha256", "original_task_bytes_hex",
    "original_task_binding", "decision_issued_at_epoch", "evidence_sha256",
    "budget_ledgers", "work_events_sha256",
])
def test_retire_rejects_inexact_terminal_receipt_before_any_write(
        prepared, field):
    p = prepared
    apply(p)
    authorize_retirement(p)
    terminal_receipt = next(
        path for path in (p["root"] / "results").glob(
            "*.watchdog-terminal-unknown-*.json")
        if "retirement" not in path.name)
    value = json.loads(terminal_receipt.read_bytes())
    if field == "extra":
        value["unreviewed"] = True
    elif field in {"original_task_sha256", "evidence_sha256",
                   "work_events_sha256"}:
        value[field] = "0" * 64
    elif field == "original_task_bytes_hex":
        value[field] = "00"
    elif field == "original_task_binding":
        original = json.loads(bytes.fromhex(
            value["original_task_bytes_hex"]))
        original["permission_grant"]["tools"].append("write_file")
        raw = canonical(original) + b"\n"
        value["original_task_bytes_hex"] = raw.hex()
        value["original_task_sha256"] = (
            unknown.hashlib.sha256(raw).hexdigest())
    elif field == "decision_issued_at_epoch":
        value[field] += 1
    elif field == "budget_ledgers":
        value[field] = []
    put(terminal_receipt, value)
    task_before = p["path"].read_bytes()
    result_names_before = sorted(
        path.name for path in (p["root"] / "results").iterdir())
    with pytest.raises((EvidenceError, OSError)):
        retire(p)
    assert p["path"].read_bytes() == task_before
    assert sorted(path.name for path in (
        p["root"] / "results").iterdir()) == result_names_before
    assert not list((p["root"] / "results").glob(
        "*.watchdog-terminal-unknown-retirement-*.json"))
