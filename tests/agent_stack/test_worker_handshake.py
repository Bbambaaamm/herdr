import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "agent-stack" / "bin"
sys.path.insert(0, str(BIN))

loader = SourceFileLoader("agent_task_worker", str(BIN / "agent-task-worker"))
spec = importlib.util.spec_from_loader(loader.name, loader)
worker = importlib.util.module_from_spec(spec)
loader.exec_module(worker)


def configure_paths(tmp_path):
    worker.ROOT = tmp_path
    worker.PENDING = tmp_path / "pending"
    worker.DONE = tmp_path / "done"
    worker.BLOCKED = tmp_path / "blocked"
    worker.FAILED = tmp_path / "failed"
    worker.RESULTS = tmp_path / "results"
    worker.LOGS = tmp_path / "logs"
    for path in (worker.PENDING, worker.DONE, worker.BLOCKED, worker.FAILED, worker.RESULTS, worker.LOGS):
        path.mkdir(parents=True, exist_ok=True)


def base_task():
    return {
        "id": "task-1",
        "issue": 3,
        "repo": "Bbambaaamm/herdr",
        "attempts": 0,
        "max_attempts": 4,
        "prompt": "safe test",
    }


def test_prepare_attempt_reuses_identity_during_reconciliation(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    token = task["run_token"]
    key = task["idempotency_key"]

    task["attempt_state"] = "delivery_uncertain"
    worker.prepare_attempt(task)

    assert task["run_token"] == token
    assert task["idempotency_key"] == key
    assert task["attempts"] == 0


def test_delivery_uncertain_does_not_increment_execution_attempt(tmp_path):
    configure_paths(tmp_path)
    running = tmp_path / "running"
    running.mkdir()
    task_path = running / "task-1.json"
    task = base_task()
    worker.prepare_attempt(task)
    token = task["run_token"]
    task_path.write_text(json.dumps(task), encoding="utf-8")

    worker.defer_delivery_reconciliation(task_path, task, "ambiguous")

    pending = worker.PENDING / task_path.name
    saved = json.loads(pending.read_text(encoding="utf-8"))
    assert saved["attempts"] == 0
    assert saved["run_token"] == token
    assert saved["attempt_state"] == "delivery_uncertain"
    assert saved["delivery_reconcile_count"] == 1


def write_valid_swarm(path):
    snapshot = {
        "version": 1,
        "paper_only": True,
        "agents": [
            {
                "agent_id": "quantlab-hermes",
                "task_id": "runtime-canary-parent",
                "state": "done",
                "fencing_token": 1,
            },
            {
                "agent_id": "child-a",
                "task_id": "child-a-task",
                "parent_agent_id": "quantlab-hermes",
                "parent_task_id": "runtime-canary-parent",
                "state": "done",
                "fencing_token": 2,
            },
            {
                "agent_id": "child-b",
                "task_id": "child-b-task",
                "parent_agent_id": "quantlab-hermes",
                "parent_task_id": "runtime-canary-parent",
                "state": "done",
                "fencing_token": 3,
            },
        ],
        "edges": [
            {"from": "runtime-canary-parent", "to": "child-a-task", "kind": "parent"},
            {"from": "runtime-canary-parent", "to": "child-b-task", "kind": "parent"},
        ],
    }
    path.write_text(json.dumps(snapshot), encoding="utf-8")


def evidence_task(snapshot_path):
    task = base_task()
    worker.prepare_attempt(task)
    task["completion_evidence"] = {
        "kind": "herdr_swarm_snapshot",
        "path": str(snapshot_path),
        "parent_agent_id": "quantlab-hermes",
        "parent_task_id": "runtime-canary-parent",
        "min_children": 2,
    }
    return task


def test_trusted_swarm_evidence_synthesizes_result(tmp_path):
    configure_paths(tmp_path)
    snapshot = tmp_path / "swarm.json"
    write_valid_swarm(snapshot)
    task = evidence_task(snapshot)

    assert worker.reconcile_completion_evidence(task) is True

    result = json.loads(worker.result_path(task["id"]).read_text(encoding="utf-8"))
    assert result["status"] == "completed"
    assert result["run_token"] == task["run_token"]
    assert result["blocker"] is None


def test_finish_uses_trusted_evidence_without_redispatch(tmp_path):
    configure_paths(tmp_path)
    running = tmp_path / "running"
    running.mkdir()
    snapshot = tmp_path / "swarm.json"
    write_valid_swarm(snapshot)
    task = evidence_task(snapshot)
    task_path = running / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")

    worker.finish(task_path, task, "settled")

    done = worker.DONE / task_path.name
    saved = json.loads(done.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "done"
    assert saved["attempts"] == 0
    result = json.loads(worker.result_path(task["id"]).read_text(encoding="utf-8"))
    assert result["status"] == "completed"


def test_finish_without_result_defers_same_attempt(tmp_path):
    configure_paths(tmp_path)
    running = tmp_path / "running"
    running.mkdir()
    task = base_task()
    worker.prepare_attempt(task)
    token = task["run_token"]
    task_path = running / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")

    worker.finish(task_path, task, "settled but no result")

    pending = worker.PENDING / task_path.name
    saved = json.loads(pending.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "delivery_uncertain"
    assert saved["attempts"] == 0
    assert saved["run_token"] == token
    assert saved["delivery_reconcile_count"] == 1
