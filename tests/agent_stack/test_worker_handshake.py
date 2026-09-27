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
    worker.RUNNING = tmp_path / "running"
    worker.DONE = tmp_path / "done"
    worker.BLOCKED = tmp_path / "blocked"
    worker.FAILED = tmp_path / "failed"
    worker.RESULTS = tmp_path / "results"
    worker.LOGS = tmp_path / "logs"
    for path in (
        worker.PENDING,
        worker.RUNNING,
        worker.DONE,
        worker.BLOCKED,
        worker.FAILED,
        worker.RESULTS,
        worker.LOGS,
    ):
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
    running = worker.RUNNING
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
    running = worker.RUNNING
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
    running = worker.RUNNING
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


def test_task_session_identity_is_bound_to_run_token(tmp_path):
    configure_paths(tmp_path)
    first = base_task()
    first["routing"] = {"selected_agent": "quantlab-hermes"}
    first["run_token"] = "run-a"
    second = dict(first)
    second["run_token"] = "run-b"

    first_identity = worker._task_session_identity(first)
    assert first_identity == worker._task_session_identity(first)
    assert first_identity != worker._task_session_identity(second)
    assert first_identity[0].startswith("quantlab-hermes-task-")
    assert first_identity[1].startswith("durable-")
    assert "task-1" not in first_identity[1]


def test_create_task_session_uses_fresh_owned_pane_and_named_chat(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"

    calls = []

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        calls.append(list(args))
        if args[:2] == ["agent", "get"]:
            return {
                "result": {
                    "agent": {
                        "agent": "hermes",
                        "name": "quantlab-hermes",
                        "pane_id": "persistent-pane",
                    }
                }
            }
        if args[:2] == ["pane", "split"]:
            return {"result": {"pane": {"pane_id": "owned-task-pane"}}}
        if args[:2] == ["agent", "start"]:
            return {"result": {"agent": {"name": args[2]}}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    session = worker.create_task_session(task)

    assert session["coordinator_agent"] == "quantlab-hermes"
    assert session["coordinator_pane_id"] == "persistent-pane"
    assert session["pane_id"] == "owned-task-pane"
    assert session["agent_name"] != "quantlab-hermes"
    split = next(call for call in calls if call[:2] == ["pane", "split"])
    assert ["--pane", "persistent-pane"] == split[2:4]
    start = next(call for call in calls if call[:2] == ["agent", "start"])
    assert start[2] == session["agent_name"]
    assert "--continue" in start
    assert start[start.index("--continue") + 1] == session["session_name"]
    assert "--create-if-missing" in start
    assert "--in" in start
    assert start[start.index("--in") + 1] == task["workspace"]


def test_create_task_session_refuses_coordinator_pane_reuse(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"
    subprocess_calls = []

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {
                "result": {
                    "agent": {
                        "agent": "hermes",
                        "name": "quantlab-hermes",
                        "pane_id": "persistent-pane",
                    }
                }
            }
        if args[:2] == ["pane", "split"]:
            return {"result": {"pane": {"pane_id": "persistent-pane"}}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(
        worker.subprocess,
        "run",
        lambda cmd, **_kwargs: subprocess_calls.append(list(cmd)),
    )

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "task_session_pane_not_isolated"
    else:
        raise AssertionError("coordinator pane reuse must fail closed")
    assert subprocess_calls == []


def test_create_task_session_closes_owned_pane_after_invalid_agent_start(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"
    subprocess_calls = []

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {
                "result": {
                    "agent": {
                        "agent": "hermes",
                        "name": "quantlab-hermes",
                        "pane_id": "persistent-pane",
                    }
                }
            }
        if args[:2] == ["pane", "split"]:
            return {"result": {"pane": {"pane_id": "owned-pane"}}}
        if args[:2] == ["agent", "start"]:
            return {"result": {"agent": {"name": "unexpected-agent"}}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(
        worker.subprocess,
        "run",
        lambda cmd, **_kwargs: subprocess_calls.append(list(cmd))
        or worker.subprocess.CompletedProcess(cmd, 0, stdout="", stderr=""),
    )

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "task_session_agent_start_invalid"
    else:
        raise AssertionError("invalid agent start response must fail closed")
    assert subprocess_calls == [
        [str(worker.HERDR), "pane", "close", "owned-pane"]
    ]


def test_run_prompt_targets_task_session_never_persistent_coordinator(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["run_token"] = "isolated-run"
    task["routing"] = {
        "selected_agent": "quantlab-hermes",
        "executor_agent": "quantlab-hermes",
        "tier": "free",
        "model": "nous-adaptive-free",
    }
    task["execution_session"] = {
        "agent_name": "quantlab-hermes-task-deadbeef",
        "session_name": "durable-deadbeef",
        "pane_id": "owned-task-pane",
        "coordinator_agent": "quantlab-hermes",
        "owned_pane": True,
    }
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = list(cmd)
        return worker.subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(worker.subprocess, "run", fake_run)
    rc, output = worker.run_prompt(task)

    assert rc == 0
    assert output == "ok"
    assert seen["cmd"][1:4] == [
        "agent",
        "prompt",
        "quantlab-hermes-task-deadbeef",
    ]
    assert "quantlab-hermes" not in seen["cmd"][3:4]
    prompt = worker.prompt_text(task)
    assert "isolated durable-task session quantlab-hermes-task-deadbeef" in prompt
    assert "persistent coordinator chat is control-plane only" in prompt


def test_run_prompt_fails_closed_without_isolated_session(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    task["run_token"] = "missing-session"
    task["routing"] = {"selected_agent": "quantlab-hermes"}

    try:
        worker.run_prompt(task)
    except RuntimeError as exc:
        assert str(exc) == "task_session_isolation_missing"
    else:
        raise AssertionError("run_prompt must not fall back to persistent coordinator")


def test_cleanup_closes_only_owned_task_pane(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "agent_name": "quantlab-hermes-task-deadbeef",
        "session_name": "durable-deadbeef",
        "pane_id": "owned-task-pane",
        "coordinator_pane_id": "persistent-pane",
        "owned_pane": True,
    }
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return worker.subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(worker.subprocess, "run", fake_run)
    worker.cleanup_task_session(task)

    assert calls == [[str(worker.HERDR), "pane", "close", "owned-task-pane"]]
    assert task["execution_session"]["cleanup_status"] == "closed"
    assert task["execution_session"]["pane_id"] != task["execution_session"]["coordinator_pane_id"]


def test_cleanup_refuses_persistent_coordinator_pane(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "agent_name": "invalid-task-agent",
        "pane_id": "persistent-pane",
        "coordinator_pane_id": "persistent-pane",
        "owned_pane": True,
    }

    def unexpected_run(*_args, **_kwargs):
        raise AssertionError("persistent coordinator pane must never be closed")

    monkeypatch.setattr(worker.subprocess, "run", unexpected_run)
    worker.cleanup_task_session(task)

    session = task["execution_session"]
    assert session["cleanup_status"] == "refused"
    assert "coordinator" in session["cleanup_error"]
    assert "closed_at" not in session


def test_cleanup_failure_is_recorded_without_masking_task_state(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "agent_name": "task-agent",
        "pane_id": "owned-pane",
        "coordinator_pane_id": "persistent-pane",
        "owned_pane": True,
    }

    def timeout(*_args, **_kwargs):
        raise worker.subprocess.TimeoutExpired("herdr", 15)

    monkeypatch.setattr(worker.subprocess, "run", timeout)
    worker.cleanup_task_session(task)

    session = task["execution_session"]
    assert session["cleanup_status"] == "close_failed"
    assert "closed_at" not in session


def test_delivery_reconciliation_keeps_owned_session_alive(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    task["attempt_state"] = "delivery_uncertain"
    task["execution_session"] = {
        "agent_name": "task-agent",
        "pane_id": "owned-pane",
        "coordinator_pane_id": "persistent-pane",
        "owned_pane": True,
    }
    task_path = worker.PENDING / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")

    def unexpected_run(*_args, **_kwargs):
        raise AssertionError("ambiguous attempt session must remain alive")

    monkeypatch.setattr(worker.subprocess, "run", unexpected_run)
    worker.finalize_task_session(task)

    saved = json.loads(task_path.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "delivery_uncertain"
    assert "closed_at" not in saved["execution_session"]


def test_terminal_task_closes_and_persists_owned_session(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    task["attempt_state"] = "done"
    task["execution_session"] = {
        "agent_name": "task-agent",
        "pane_id": "owned-pane",
        "coordinator_pane_id": "persistent-pane",
        "owned_pane": True,
    }
    task_path = worker.DONE / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")

    monkeypatch.setattr(
        worker.subprocess,
        "run",
        lambda cmd, **_kwargs: worker.subprocess.CompletedProcess(
            cmd, 0, stdout="", stderr=""
        ),
    )
    worker.finalize_task_session(task)

    saved = json.loads(task_path.read_text(encoding="utf-8"))
    assert saved["execution_session"]["cleanup_status"] == "closed"
    assert saved["execution_session"]["closed_at"]


def test_new_semantic_attempt_discards_previous_session_metadata(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "agent_name": "old-task-agent",
        "session_name": "durable-old",
        "pane_id": "old-pane",
        "owned_pane": True,
        "closed_at": "2026-09-27T00:00:00+00:00",
    }

    worker.prepare_attempt(task)

    assert "execution_session" not in task
    assert task["run_token"]


def test_new_semantic_attempt_refuses_unclosed_previous_session(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "agent_name": "old-task-agent",
        "pane_id": "old-pane",
        "coordinator_pane_id": "persistent-pane",
        "owned_pane": True,
    }

    try:
        worker.prepare_attempt(task)
    except RuntimeError as exc:
        assert str(exc) == "previous_task_session_not_closed"
    else:
        raise AssertionError("a live previous task session must block a new attempt")
    assert "run_token" not in task
