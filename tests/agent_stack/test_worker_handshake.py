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
    for path in (worker.PENDING, worker.RUNNING, worker.DONE, worker.BLOCKED, worker.FAILED, worker.RESULTS, worker.LOGS):
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
    running.mkdir(exist_ok=True)
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
    running.mkdir(exist_ok=True)
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
    running.mkdir(exist_ok=True)
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
    assert first_identity[0].startswith("quantlab-herm-t-")
    assert len(first_identity[0]) <= 32
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
                        "workspace_id": "w2",
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
    assert "--env" in split
    assert split[split.index("--env") + 1] == f"{worker.TASK_PANE_ENV}={session['session_name']}"
    start = next(call for call in calls if call[:2] == ["agent", "start"])
    assert start[2] == session["agent_name"]
    assert "--continue" in start
    assert start[start.index("--continue") + 1] == session["session_name"]
    assert "--create-if-missing" in start
    assert "--in" in start
    assert start[start.index("--in") + 1] == task["workspace"]


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


def test_herdr_core_prompt_has_generic_backlog_contract(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    task.update(
        {
            "repo": "Bbambaaamm/herdr",
            "workspace": "/home/agentops/workspaces/herdr",
            "safety_profile": "herdr-core",
            "hermes_profile": "quantlab",
            "run_token": "herdr-root-run",
            "routing": {
                "selected_agent": "herdr-hermes",
                "tier": "profile-default",
                "model": "profile-router",
            },
            "execution_session": {
                "agent_name": "herdr-hermes-t-deadbeef",
                "session_name": "durable-herdr",
                "pane_id": "owned-herdr-pane",
                "coordinator_agent": "herdr-hermes",
                "owned_pane": True,
            },
        }
    )

    prompt = worker.prompt_text(task)
    assert "repository Bbambaaamm/herdr" in prompt
    assert "Root issue #53 is orchestration authority" in prompt
    assert "PAPER-only, PIT/causality" not in prompt
    assert "status=blocked only when the whole safe backlog cannot progress" in prompt
    assert "/home/agentops/worktrees/herdr/" in prompt
    assert "/home/agentops/workspaces/herdr/worktrees/" not in prompt


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


def test_persist_current_task_updates_running_task(tmp_path):
    configure_paths(tmp_path)
    worker.RUNNING = tmp_path / "running"
    worker.RUNNING.mkdir(exist_ok=True)
    task = base_task()
    task["attempt_state"] = "accepted"
    task_path = worker.RUNNING / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")

    task["marker"] = "persisted"
    worker.persist_current_task(task)

    saved = json.loads(task_path.read_text(encoding="utf-8"))
    assert saved["marker"] == "persisted"


def test_cleanup_preserves_delivery_uncertain_session(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    calls = []
    monkeypatch.setattr(worker, "cleanup_task_session", lambda task: calls.append(task["attempt_state"]))
    task = base_task()
    task["attempt_state"] = "delivery_uncertain"

    worker.cleanup_task_session_if_safe(task)
    assert calls == []

    task["attempt_state"] = "blocked"
    worker.cleanup_task_session_if_safe(task)
    assert calls == ["blocked"]


def test_block_task_makes_session_cleanup_safe(tmp_path):
    configure_paths(tmp_path)
    running = tmp_path / "running"
    running.mkdir(exist_ok=True)
    task = base_task()
    worker.prepare_attempt(task)
    task["attempt_state"] = "delivery_uncertain"
    task_path = running / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")

    worker.block_task(task_path, task, "bounded_recovery_exhausted", "bounded recovery exhausted")

    blocked = worker.BLOCKED / task_path.name
    saved = json.loads(blocked.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "blocked"
    assert saved["result_status"] == "blocked"


def test_ambiguous_split_reconciles_and_closes_marked_pane(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"
    closed = []

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {
                "result": {
                    "agent": {
                        "agent": "hermes",
                        "name": "quantlab-hermes",
                        "pane_id": "persistent-pane",
                        "workspace_id": "w2",
                    }
                }
            }
        if args[:2] == ["pane", "split"]:
            raise RuntimeError("lost split response")
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(
        worker, "_find_marked_task_panes", lambda marker, workspace_id: ("orphan-pane",)
    )
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: closed.append(pane_id) or True)

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "lost split response"
    else:
        raise AssertionError("split failure must propagate after cleanup")

    assert closed == ["orphan-pane"]


def test_ambiguous_split_never_closes_marked_coordinator(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"
    closed = []

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {
                "result": {
                    "agent": {
                        "agent": "hermes",
                        "pane_id": "persistent-pane",
                        "workspace_id": "w2",
                    }
                }
            }
        if args[:2] == ["pane", "split"]:
            raise RuntimeError("lost split response")
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(
        worker,
        "_find_marked_task_panes",
        lambda marker, workspace_id: ("persistent-pane", "orphan-pane"),
    )
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: closed.append(pane_id) or True)

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "lost split response"
    else:
        raise AssertionError("split failure must propagate after safe cleanup")

    assert closed == ["orphan-pane"]


def test_unreconciled_split_fails_closed(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {
                "result": {
                    "agent": {
                        "agent": "hermes",
                        "pane_id": "persistent-pane",
                        "workspace_id": "w2",
                    }
                }
            }
        if args[:2] == ["pane", "split"]:
            raise RuntimeError("split response unknown")
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(
        worker,
        "_find_marked_task_panes",
        lambda marker, workspace_id: (_ for _ in ()).throw(RuntimeError("pane list unavailable")),
    )

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc).startswith("task_session_split_uncertain:")
    else:
        raise AssertionError("unreconciled split must fail closed")


def test_cleanup_failure_blocks_retry_and_preserves_attempt_identity(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    token = task["run_token"]
    key = task["idempotency_key"]
    task["attempt_state"] = "retry_scheduled"
    task["execution_session"] = {
        "agent_name": "quantlab-hermes-task-deadbeef",
        "session_name": "durable-deadbeef",
        "pane_id": "owned-task-pane",
        "owned_pane": True,
    }
    task_path = worker.PENDING / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: False)

    assert worker.cleanup_task_session_if_safe(task) is False

    blocked_path = worker.BLOCKED / task_path.name
    blocked = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert blocked["attempt_state"] == "blocked"
    assert blocked["run_token"] == token
    assert blocked["idempotency_key"] == key
    result = json.loads(worker.result_path("task-1").read_text(encoding="utf-8"))
    assert result["blocker"] == "task_session_cleanup_failed"
    assert result["run_token"] == token


def test_cleanup_without_owned_pane_id_fails_closed(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "agent_name": "task-agent",
        "session_name": "durable-missing-pane",
        "owned_pane": True,
    }

    assert worker.cleanup_task_session(task) is False
    assert task["execution_session"]["cleanup_status"] == "close_unproven"


def test_cleanup_failure_blocks_even_completed_task(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["attempt_state"] = "done"
    task["execution_session"] = {
        "agent_name": "task-agent",
        "session_name": "durable-live",
        "pane_id": "owned-pane",
        "owned_pane": True,
    }
    done_path = worker.DONE / "task-1.json"
    done_path.write_text(json.dumps(task), encoding="utf-8")
    worker.write_json(
        worker.result_path("task-1"),
        {
            "task_id": "task-1",
            "run_token": "old-token",
            "status": "completed",
        },
    )
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: False)

    assert worker.cleanup_task_session_if_safe(task) is False

    blocked_path = worker.BLOCKED / "task-1.json"
    assert blocked_path.exists()
    saved = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "blocked"
    assert saved["watchdog_blocker"] == "task_session_cleanup_failed"
    assert not done_path.exists()
    result = json.loads(worker.result_path("task-1").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert result["blocker"] == "task_session_cleanup_failed"
    assert list(worker.RESULTS.glob("task-1.attempt0.previous-*.json"))


def test_ambiguous_split_without_marker_never_retries(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "ambiguous-run"

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {
                "result": {
                    "agent": {
                        "agent": "hermes",
                        "name": "quantlab-hermes",
                        "pane_id": "persistent-pane",
                        "workspace_id": "w2",
                    }
                }
            }
        if args[:2] == ["pane", "split"]:
            raise RuntimeError("transport_lost")
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(worker, "_find_marked_task_panes", lambda marker, workspace_id: ())

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "task_session_split_uncertain:no_marked_pane_found"
    else:
        raise AssertionError("ambiguous pane creation must fail closed")


def test_prepare_attempt_refuses_unclosed_owned_session(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "agent_name": "task-agent",
        "session_name": "durable-live",
        "pane_id": "owned-pane",
        "owned_pane": True,
    }

    try:
        worker.prepare_attempt(task)
    except RuntimeError as exc:
        assert str(exc) == "previous_task_session_not_closed"
    else:
        raise AssertionError("new attempt must not start while prior owned pane is live")


def test_parse_herdr_json_skips_non_json_brace_noise():
    proc = worker.subprocess.CompletedProcess(
        ["herdr"], 0, stdout='{"result":{"ok":true}}\n{not-json\n', stderr=""
    )
    parsed = worker._parse_herdr_json(proc, "test")
    assert parsed == {"result": {"ok": True}}


def test_create_task_session_rejects_non_isolated_split(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {"result": {"agent": {
                "agent": "hermes",
                "name": "quantlab-hermes",
                "pane_id": "persistent-pane",
                "workspace_id": "w2",
            }}}
        if args[:2] == ["pane", "split"]:
            return {"result": {"pane": {"pane_id": "persistent-pane"}}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: True)

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "task_session_split_uncertain:coordinator_pane_reused"
    else:
        raise AssertionError("task session must never reuse the coordinator pane")


def test_create_task_session_rejects_wrong_started_agent(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"
    closed = []

    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            return {"result": {"agent": {
                "agent": "hermes",
                "name": "quantlab-hermes",
                "pane_id": "persistent-pane",
                "workspace_id": "w2",
            }}}
        if args[:2] == ["pane", "split"]:
            return {"result": {"pane": {"pane_id": "owned-pane"}}}
        if args[:2] == ["agent", "start"]:
            return {"result": {"agent": {"name": "wrong-agent", "pane_id": "owned-pane"}}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: closed.append(pane_id) or True)

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "task_session_agent_start_invalid"
    else:
        raise AssertionError("wrong agent identity must fail closed")

    assert closed == ["owned-pane"]


def test_task_session_agent_name_respects_herdr_limit_for_all_coordinators(tmp_path):
    configure_paths(tmp_path)
    names = []
    for coordinator in ("quantlab-hermes", "dotacni-majak-hermes"):
        task = base_task()
        task["routing"] = {"selected_agent": coordinator}
        task["run_token"] = "same-run-token"
        agent_name, session_name = worker._task_session_identity(task)
        assert 1 <= len(agent_name) <= 32
        assert agent_name[0].islower()
        assert all(ch.islower() or ch.isdigit() or ch in "_-" for ch in agent_name)
        assert len(session_name) <= 32
        names.append(agent_name)

    assert names[0] != names[1]
