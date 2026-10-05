import importlib.util
import hashlib
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "agent-stack" / "bin"
sys.path.insert(0, str(BIN))

loader = SourceFileLoader("agent_task_worker", str(BIN / "agent-task-worker"))
spec = importlib.util.spec_from_loader(loader.name, loader)
worker = importlib.util.module_from_spec(spec)
loader.exec_module(worker)


def _policy_file(tmp_path):
    path = tmp_path / "policy"
    path.write_text("policy", encoding="utf-8")
    return path


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
        "idempotency_key": "task-key",
    }


def test_existing_herdr_task_gets_explicit_consumer_scope():
    task = base_task()
    task["safety_profile"] = "herdr-core"
    worker.ensure_parent_scope(task)
    assert task["parent_role"] == "writer"
    assert task["worktree_root"] == "/home/agentops/workspaces/herdr/worktrees"
    assert set(task["parent_tools"]) == {"read_file", "search_files", "patch", "write_file", "herdr_delegate_child", "herdr_submit_result"}
    assert task["parent_permissions"] == ["workspace-write"]


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


def test_child_prompt_requires_admitted_attempt_and_preserves_identity(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["parent_task_id"] = "parent"
    task["execution_session"] = {"agent_name": "child-agent"}
    with pytest.raises(RuntimeError, match="durable_child_admission_identity_missing"):
        worker.prepare_attempt(task)
    with pytest.raises(RuntimeError, match="durable_child_admission_identity_missing"):
        worker.run_prompt(task)
    task.update(run_token="child-run", idempotency_key="attempt-key",
                fencing_token=7, delegation_key="research")
    worker.prepare_attempt(task)
    assert task["run_token"] == "child-run"
    assert task["idempotency_key"] == "attempt-key"
    assert task["attempts"] == 0
    assert "artifact_sha256" in worker.prompt_text(task)


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

    pending = worker.BLOCKED / task_path.name
    saved = json.loads(pending.read_text(encoding="utf-8"))
    assert saved["attempts"] == 0
    assert saved["run_token"] == token
    assert saved["attempt_state"] == "delivery_uncertain"
    assert saved["delivery_reconcile_pending"] is True
    assert saved["observed_execution"]["state"] == "unavailable"
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
    worker.freeze_plan(worker.ROOT, task)
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


def test_block_task_quarantines_until_task_pane_cleanup(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    task["execution_session"] = {"owned_pane": True, "pane_id": "owned-pane"}
    running = worker.RUNNING / "task-1.json"
    running.write_text(json.dumps(task), encoding="utf-8")
    monkeypatch.setattr(worker, "cleanup_task_session", lambda current: False)

    worker.block_task(running, task, "needs-human", "blocked safely")

    quarantined = worker.BLOCKED / "task-1.json"
    saved = json.loads(quarantined.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "delivery_uncertain"
    assert saved["watchdog_cleanup_blocker"] == "task_session_cleanup_failed"
    assert "result_status" not in saved and "finished_at" not in saved
    result = json.loads(worker.result_path("task-1").read_text(encoding="utf-8"))
    assert result["status"] == "blocked" and result["run_token"] == task["run_token"]


def test_empty_session_result_placeholder_materializes_interactive_blocker(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    running = worker.RUNNING / "task-1.json"
    running.write_text(json.dumps(task), encoding="utf-8")
    worker.result_path(task["id"]).touch()

    worker.block_task(running, task, "agent_interactive_input_required", "input required")

    assert (worker.BLOCKED / running.name).is_file()
    result = json.loads(worker.result_path(task["id"]).read_text(encoding="utf-8"))
    assert result["blocker"] == "agent_interactive_input_required"
    assert result["run_token"] == task["run_token"]
    from importlib.machinery import SourceFileLoader
    intake_loader = SourceFileLoader("agent_github_intake_blocker_test", str(BIN / "agent-github-intake"))
    intake_spec = importlib.util.spec_from_loader(intake_loader.name, intake_loader)
    intake = importlib.util.module_from_spec(intake_spec)
    intake_loader.exec_module(intake)
    intake.RESULTS = worker.RESULTS
    assert intake.result_for(task["id"])["blocker"] == "agent_interactive_input_required"


def test_block_task_preserves_nonregular_result_path(tmp_path):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    running = worker.RUNNING / "task-1.json"
    running.write_text(json.dumps(task), encoding="utf-8")
    target = tmp_path / "evidence.json"
    target.write_text("trusted", encoding="utf-8")
    worker.result_path(task["id"]).symlink_to(target)

    worker.block_task(running, task, "agent_interactive_input_required", "input required")

    assert worker.result_path(task["id"]).is_symlink()
    assert target.read_text(encoding="utf-8") == "trusted"
    saved = json.loads((worker.BLOCKED / running.name).read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "delivery_uncertain"


def test_finish_defers_terminal_move_until_task_pane_cleanup(tmp_path, monkeypatch):
    # This suite isolates lifecycle cleanup; completion acceptance is tested separately.
    monkeypatch.setattr(worker, "verify_completion", lambda *args:
                        {"level":"verified_worker_result", "bundle_hash":"a"*64})
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    task["execution_session"] = {
        "owned_pane": True, "pane_id": "owned-pane",
        "agent_name": "task-agent", "pane_marker": "marker",
        "session_name": "marker",
    }
    running = worker.RUNNING / "task-1.json"
    running.write_text(json.dumps(task), encoding="utf-8")
    worker.write_json(worker.result_path("task-1"), {
        "task_id": "task-1", "run_token": task["run_token"],
        "status": "completed", "blocker": None,
    })
    monkeypatch.setattr(worker, "cleanup_task_session", lambda current: False)

    worker.finish(running, task, "settled")

    assert running.exists()
    assert not (worker.DONE / running.name).exists()
    saved = json.loads(running.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "delivery_uncertain"
    assert saved["watchdog_cleanup_blocker"] == "task_session_cleanup_failed"
    assert saved["run_token"] == task["run_token"]


def test_finish_cleans_task_pane_before_terminal_move(tmp_path, monkeypatch):
    # This suite isolates lifecycle cleanup; completion acceptance is tested separately.
    monkeypatch.setattr(worker, "verify_completion", lambda *args:
                        {"level":"verified_worker_result", "bundle_hash":"a"*64})
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    task["execution_session"] = {"owned_pane": True, "pane_id": "owned-pane"}
    running = worker.RUNNING / "task-1.json"
    running.write_text(json.dumps(task), encoding="utf-8")
    worker.write_json(worker.result_path("task-1"), {
        "task_id": "task-1", "run_token": task["run_token"],
        "status": "completed", "blocker": None,
    })
    calls = []
    def cleanup(current):
        calls.append("cleanup")
        current["execution_session"]["closed_at"] = "now"
        return True
    monkeypatch.setattr(worker, "cleanup_task_session", cleanup)

    worker.finish(running, task, "settled")

    assert calls == ["cleanup"]
    done = json.loads((worker.DONE / "task-1.json").read_text(encoding="utf-8"))
    assert done["attempt_state"] == "done"
    assert done["execution_session"]["closed_at"] == "now"


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

    pending = worker.BLOCKED / task_path.name
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


def test_exact_owned_session_observation_does_not_complete_attempt(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["run_token"] = "owned-run"
    agent, marker = worker._task_session_identity(task)
    task["execution_session"] = dict(agent_name=agent, session_name=marker,
                                     pane_marker=marker, pane_id="pane-1")
    task["attempt_state"] = "delivery_uncertain"
    monkeypatch.setattr(worker, "_pane_has_marker", lambda pane, value: pane == "pane-1" and value == marker)
    monkeypatch.setattr(worker, "_herdr_json", lambda *args, **kwargs: {"result": {
        "agent": {"pane_id": "pane-1", "agent_status": "done"}}})
    assert worker.observe_task_execution(task) == "settled"
    assert task["attempt_state"] == "delivery_uncertain"
    task["execution_session"]["agent_name"] = "wrong-agent"
    assert worker.observe_task_execution(task) == "unavailable"


def test_finish_reconciles_snapshot_over_zero_byte_result_placeholder(tmp_path, monkeypatch):
    # This suite isolates lifecycle cleanup; completion acceptance is tested separately.
    monkeypatch.setattr(worker, "verify_completion", lambda *args:
                        {"level":"verified_worker_result", "bundle_hash":"a"*64})
    configure_paths(tmp_path)
    task = base_task()
    task["run_token"] = "snapshot-run"
    task["completion_evidence"] = {"kind": "herdr_swarm_snapshot"}
    running = worker.RUNNING / f"{task['id']}.json"
    worker.RUNNING.mkdir(parents=True, exist_ok=True)
    worker.DONE.mkdir(parents=True, exist_ok=True)
    worker.BLOCKED.mkdir(parents=True, exist_ok=True)
    worker.RESULTS.mkdir(parents=True, exist_ok=True)
    running.write_text(json.dumps(task), encoding="utf-8")
    rp = worker.result_path(task["id"])
    rp.touch()
    assert rp.stat().st_size == 0

    monkeypatch.setattr(worker, "reconcile_completion_evidence", lambda payload: (
        worker.write_json(rp, {
            "task_id": payload["id"], "run_token": payload["run_token"],
            "status": "completed", "evidence": ["snapshot"], "blocker": None,
        }) or True
    ))
    monkeypatch.setattr(worker, "cleanup_task_session", lambda payload: True)
    monkeypatch.setattr(worker, "defer_for_active_children", lambda *args, **kwargs: False)
    worker._finish_locked(running, task, "done", True)
    assert (worker.DONE / running.name).exists()
    assert json.loads(rp.read_text())["status"] == "completed"


def test_create_task_session_uses_fresh_owned_pane_and_named_chat(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    task["run_token"] = "isolated-run"

    calls = []
    boundary_events = []
    def start_bridge(task, session):
        boundary_events.append("bridge_outside_sandbox")
        session.update(bridge_pid=123, bridge_socket="@test")
    def sandbox_command(*args, **kwargs):
        boundary_events.append("sandbox_command")
        return ["bwrap", "/bin/bash"]
    monkeypatch.setattr(worker, "start_bridge", start_bridge)
    policy = tmp_path / "policy"
    policy.write_text("policy", encoding="utf-8")
    monkeypatch.setattr(worker, "frozen_policy", lambda: policy)
    monkeypatch.setattr(worker, "sandbox_command", sandbox_command)
    monkeypatch.setattr(worker, "verify_sandbox", lambda *args, **kwargs: True)
    monkeypatch.setattr(worker, "inner_pid", lambda *args, **kwargs: 123)
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"persistent-pane"})

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
        if args[:2] == ["pane", "run"]:
            return {"result": {}}
        if args[:2] == ["pane", "process-info"]:
            return {"result": {"process_info": {"shell_pid": 123}}}
        if args[:2] == ["agent", "start"]:
            return {"result": {"agent": {"name": args[2]}}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    session = worker.create_task_session(task)
    assert boundary_events == ["bridge_outside_sandbox", "sandbox_command"]

    assert session["coordinator_agent"] == "quantlab-hermes"
    assert session["coordinator_pane_id"] == "persistent-pane"
    assert session["pane_id"] == "owned-task-pane"
    assert session["agent_name"] != "quantlab-hermes"
    assert session["sandbox_verified"] is True
    att = session["sandbox_attestation"]
    assert att["authority"] == "agent-task-worker" and att["kind"] == "bwrap"
    assert att["task_id"] == task["id"] and att["run_token"] == task["run_token"]
    assert att["pane_id"] == session["pane_id"] and att["marker"] == session["pane_marker"]
    assert att["sandbox_pid"] == 123
    assert att["policy_sha256"] == hashlib.sha256(policy.read_bytes()).hexdigest()
    split = next(call for call in calls if call[:2] == ["pane", "split"])
    assert ["--pane", "persistent-pane"] == split[2:4]
    assert "--env" in split
    assert split[split.index("--env") + 1] == f"{worker.TASK_PANE_ENV}={session['session_name']}"
    assert f"HERDR_DURABLE_TASK_ID={task['id']}" in split
    assert f"HERDR_DURABLE_RUN_TOKEN={task['run_token']}" in split
    assert f"HERDR_DURABLE_AGENT={session['agent_name']}" in split
    path_env = next(value for value in split if value.startswith(f"PATH={worker.POLICY_BIN}:"))
    assert str(worker.AGENT_BIN) in path_env
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
    assert "/home/agentops/worktrees/herdr/" not in prompt
    assert "/home/agentops/workspaces/herdr/worktrees/" in prompt


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
        "pane_marker": "durable-deadbeef",
        "coordinator_pane_id": "persistent-pane",
        "owned_pane": True,
    }
    calls = []

    monkeypatch.setattr(worker, "_herdr_json", lambda args, **kw: {
        "result": {"panes": [{"pane_id": "owned-task-pane"}]}} if args[:2] == ["pane", "list"]
        else {"result": {"agent": {"name": task["execution_session"]["agent_name"],
                                    "pane_id": "owned-task-pane"}}})
    monkeypatch.setattr(worker, "_pane_has_marker", lambda pane, marker: True)
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane: calls.append(pane) or True)
    worker.cleanup_task_session(task)

    assert calls == ["owned-task-pane"]
    assert task["execution_session"]["cleanup_status"] == "closed"
    assert task["execution_session"]["pane_id"] != task["execution_session"]["coordinator_pane_id"]


@pytest.mark.parametrize("case", ["reused", "wrong_agent", "wrong_marker", "absent", "exact"])
def test_task_cleanup_requires_live_identity(tmp_path, monkeypatch, case):
    configure_paths(tmp_path)
    task = base_task()
    task["execution_session"] = {
        "owned_pane": True, "pane_id": "pane-1", "agent_name": "task-agent",
        "pane_marker": "task-marker", "coordinator_pane_id": "coordinator",
    }
    closed = []
    monkeypatch.setattr(worker, "_herdr_json", lambda args, **kw: {
        "result": {"panes": [] if case == "absent" else [{"pane_id": "pane-1"}]}}
        if args[:2] == ["pane", "list"] else
        {"result": {"agent": {"name": "other" if case == "wrong_agent" else "task-agent",
                              "pane_id": "other-pane" if case == "reused" else "pane-1"}}})
    monkeypatch.setattr(worker, "_pane_has_marker", lambda pane, marker: case != "wrong_marker")
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane: closed.append(pane) or True)
    assert worker.cleanup_task_session(task) is (case in {"absent", "exact"})
    assert closed == (["pane-1"] if case == "exact" else [])


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
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"persistent-pane"})

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
        if args[:2] == ["pane", "list"]:
            return {"result": {"panes": [{"pane_id": "orphan-pane"}]}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(
        worker, "_find_marked_task_panes", lambda marker, workspace_id: ("orphan-pane",)
    )
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: closed.append(pane_id) or True)
    monkeypatch.setattr(worker, "_pane_has_marker", lambda pane, marker: pane == "orphan-pane")

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
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"persistent-pane"})

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
        if args[:2] == ["pane", "list"]:
            return {"result": {"panes": [{"pane_id": "orphan-pane"}]}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(
        worker,
        "_find_marked_task_panes",
        lambda marker, workspace_id: ("persistent-pane", "orphan-pane"),
    )
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: closed.append(pane_id) or True)
    monkeypatch.setattr(worker, "_pane_has_marker", lambda pane, marker: pane == "orphan-pane")

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
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"persistent-pane"})

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
        "pane_marker": "durable-deadbeef",
        "pane_id": "owned-task-pane",
        "owned_pane": True,
    }
    task_path = worker.PENDING / "task-1.json"
    task_path.write_text(json.dumps(task), encoding="utf-8")
    def cleanup_herdr(args, *, timeout_seconds=30.0):
        if args[:2] == ["pane", "list"]:
            return {"result": {"panes": [{"pane_id": "owned-task-pane"}]}}
        if args[:2] == ["agent", "get"]:
            return {"result": {"agent": {
                "name": "quantlab-hermes-task-deadbeef",
                "pane_id": "owned-task-pane",
            }}}
        raise AssertionError(args)
    monkeypatch.setattr(worker, "_herdr_json", cleanup_herdr)
    monkeypatch.setattr(worker, "_pane_has_marker",
                        lambda pane, marker: pane == "owned-task-pane" and marker == "durable-deadbeef")
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: False)

    assert worker.cleanup_task_session_if_safe(task) is False

    blocked_path = worker.BLOCKED / task_path.name
    blocked = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert blocked["attempt_state"] == "delivery_uncertain"
    assert blocked["watchdog_cleanup_blocker"] == "task_session_cleanup_failed"
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
        "pane_marker": "durable-live",
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
    def cleanup_herdr(args, *, timeout_seconds=30.0):
        if args[:2] == ["pane", "list"]:
            return {"result": {"panes": [{"pane_id": "owned-pane"}]}}
        if args[:2] == ["agent", "get"]:
            return {"result": {"agent": {"name": "task-agent", "pane_id": "owned-pane"}}}
        raise AssertionError(args)
    monkeypatch.setattr(worker, "_herdr_json", cleanup_herdr)
    monkeypatch.setattr(worker, "_pane_has_marker",
                        lambda pane, marker: pane == "owned-pane" and marker == "durable-live")
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: False)

    assert worker.cleanup_task_session_if_safe(task) is False

    blocked_path = worker.BLOCKED / "task-1.json"
    assert blocked_path.exists()
    saved = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert saved["attempt_state"] == "delivery_uncertain"
    assert saved["watchdog_blocker"] == "task_session_cleanup_failed"
    assert saved["watchdog_cleanup_blocker"] == "task_session_cleanup_failed"
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
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"persistent-pane"})

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
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"persistent-pane"})

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
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"persistent-pane"})
    closed = []
    monkeypatch.setattr(worker, "start_bridge", lambda task, session: None)
    monkeypatch.setattr(worker, "frozen_policy", lambda: _policy_file(tmp_path))
    monkeypatch.setattr(worker, "sandbox_command", lambda *args, **kwargs: ["bwrap", "/bin/bash"])
    monkeypatch.setattr(worker, "verify_sandbox", lambda *args, **kwargs: True)
    monkeypatch.setattr(worker, "inner_pid", lambda *args, **kwargs: 123)

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
        if args[:2] == ["pane", "run"]:
            return {"result": {}}
        if args[:2] == ["pane", "process-info"]:
            return {"result": {"process_info": {"shell_pid": 123}}}
        if args[:2] == ["agent", "start"]:
            return {"result": {"agent": {"name": "wrong-agent", "pane_id": "owned-pane"}}}
        if args[:2] == ["pane", "list"]:
            return {"result": {"panes": [{"pane_id": "owned-pane"}]}}
        raise AssertionError(args)

    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    monkeypatch.setattr(worker, "_close_owned_pane", lambda pane_id: closed.append(pane_id) or True)
    monkeypatch.setattr(worker, "_pane_has_marker", lambda pane, marker: True)

    try:
        worker.create_task_session(task)
    except RuntimeError as exc:
        assert str(exc) == "task_session_cleanup_failed"
    else:
        raise AssertionError("wrong agent identity must fail closed")

    assert closed == []


@pytest.mark.parametrize("case,after_start,expected_close", [
    ("absent", False, False),
    ("exact", False, True),
    ("wrong_marker", False, False),
    ("reused_pane", False, False),
    ("exact", True, True),
    ("wrong_agent", True, False),
    ("wrong_pane", True, False),
    ("wrong_marker", True, False),
])
def test_setup_failure_cleanup_proves_pane_identity(
        tmp_path, monkeypatch, case, after_start, expected_close):
    configure_paths(tmp_path)
    task = base_task()
    task.update(workspace=str(tmp_path / "workspace"), run_token="setup-run",
                routing={"selected_agent": "quantlab-hermes"})
    closed = []
    monkeypatch.setattr(worker, "start_bridge", lambda *args: None)
    monkeypatch.setattr(worker, "frozen_policy", lambda: _policy_file(tmp_path))
    monkeypatch.setattr(worker, "sandbox_command", lambda *args, **kw: ["bwrap"])
    monkeypatch.setattr(worker, "verify_sandbox", lambda *args, **kw: True)
    monkeypatch.setattr(worker, "inner_pid", lambda *args, **kw: 123)
    monkeypatch.setattr(worker, "_pane_has_marker",
                        lambda pane, marker: case != "wrong_marker")
    monkeypatch.setattr(worker, "_close_owned_pane",
                        lambda pane: closed.append(pane) or True)
    def fake_herdr_json(args, *, timeout_seconds=30.0):
        if args[:2] == ["agent", "get"]:
            if args[2] == "quantlab-hermes":
                return {"result": {"agent": {"agent": "hermes", "pane_id": "coordinator",
                                              "workspace_id": "w2"}}}
            return {"result": {"agent": {"name": "other-agent" if case == "wrong_agent"
                                              else args[2], "pane_id": "other-pane" if
                                              case == "wrong_pane" else "owned-pane"}}}
        if args[:2] == ["pane", "split"]:
            return {"result": {"pane": {"pane_id": "owned-pane"}}}
        if args[:2] == ["pane", "list"]:
            lists.append(True)
            return {"result": {"panes": ([{"pane_id": "owned-pane"}]
                       if case == "reused_pane" else []) if len(lists) == 1 else
                       ([] if case == "absent" else [{"pane_id": "owned-pane"}])}}
        if args[:2] == ["pane", "run"]:
            return {"result": {}}
        if args[:2] == ["pane", "process-info"]:
            return {"result": {"process_info": {"shell_pid": 123}}}
        if args[:2] == ["agent", "start"]:
            raise RuntimeError("start failed")
        raise AssertionError(args)
    lists = []
    monkeypatch.setattr(worker, "_herdr_json", fake_herdr_json)
    if not after_start:
        monkeypatch.setattr(worker, "start_bridge",
                            lambda *args: (_ for _ in ()).throw(RuntimeError("bridge failed")))
    expected = "start failed" if after_start else "bridge failed"
    if case not in {"absent", "exact"}:
        expected = "task_session_cleanup_failed"
    with pytest.raises(RuntimeError, match=expected):
        worker.create_task_session(task)
    assert closed == (["owned-pane"] if expected_close else [])


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

def verification_task(tmp_path, kind="coding"):
    configure_paths(tmp_path)
    task = base_task()
    task["completion_kind"] = kind
    worker.prepare_attempt(task)
    path = worker.RUNNING / f"{task['id']}.json"
    path.write_text(json.dumps(task))
    result = {"task_id": task["id"], "run_token": task["run_token"],
              "status": "completed", "summary": "worker claim only",
              "next_action": "continue", "repo": task["repo"], "blocker": None,
              "evidence": [{"producer": "trusted-ci", "passed": True}]}
    worker.write_json(worker.result_path(task["id"]), result)
    return task, path, result


def test_completed_coding_without_host_proof_is_not_done_or_retried(tmp_path):
    task, path, result = verification_task(tmp_path)
    identity = (task["run_token"], task["idempotency_key"], task["attempts"])
    worker.finish(path, task, "claims completed")
    saved = json.loads((worker.BLOCKED / path.name).read_text())
    assert saved["attempt_state"] == "blocked"
    assert saved["verification_resolution"] == "needs_replan"
    assert saved["verification_status"] == "evidence_invalid"
    assert (saved["run_token"], saved["idempotency_key"], saved["attempts"]) == identity
    assert not list(worker.DONE.iterdir())
    assert json.loads(worker.result_path(task["id"]).read_text()) == result


def test_missing_and_unavailable_evidence_keep_one_attempt(tmp_path, monkeypatch):
    from herdr.evidence import EvidenceMissing, EvidenceUnavailable
    for failure in (EvidenceMissing("review pending"), EvidenceUnavailable("CI unavailable")):
        task, path, result = verification_task(tmp_path)
        monkeypatch.setattr(worker, "verify_completion",
                            lambda *a: (_ for _ in ()).throw(failure))
        worker.finish(path, task, "")
        saved = json.loads((worker.BLOCKED / path.name).read_text())
        assert saved["verification_status"] == failure.code
        assert saved["attempts"] == 0
        assert saved["run_token"] == task["run_token"]
        (worker.BLOCKED / path.name).unlink()


def test_verified_worker_result_does_not_claim_integration_or_deployment(tmp_path, monkeypatch):
    task, path, result = verification_task(tmp_path)
    monkeypatch.setattr(worker, "verify_completion", lambda *a:
                        {"level": "verified_worker_result", "bundle_hash": "a" * 64,
                         "integration": None, "deployment": None})
    worker.finish(path, task, "")
    saved = json.loads((worker.DONE / path.name).read_text())
    assert saved["completion_level"] == "verified_worker_result"
    assert saved["completion_bundle_hash"] == "a" * 64
    assert "deployed" not in saved and "merged" not in saved
    assert saved["attempts"] == 0


def test_control_cycle_is_labelled_and_never_promoted_to_verified_implementation(tmp_path):
    task, path, result = verification_task(tmp_path)
    task["kind"] = "github_root_orchestration"
    worker.freeze_plan(worker.ROOT, task)
    worker.finish(path, task, "")
    saved = json.loads((worker.DONE / path.name).read_text())
    assert saved["completion_level"] == "control_cycle"
    assert saved["verification_status"] == "accepted"
    assert "artifact" not in saved
    assert saved["attempts"] == 0


def test_unconfigured_research_criteria_fail_closed_without_fictitious_build(tmp_path):
    task, path, result = verification_task(tmp_path, "research")
    worker.finish(path, task, "")
    saved = json.loads((worker.BLOCKED / path.name).read_text())
    assert saved["verification_status"] == "evidence_invalid"
    assert "research" in saved["last_error"]
    assert saved["attempts"] == 0


def test_pending_verification_main_reuses_publication_without_dispatch(tmp_path, monkeypatch):
    task, path, result = verification_task(tmp_path)
    task["attempt_state"] = "verification_pending"
    path.write_text(json.dumps(task))
    monkeypatch.setattr(worker, "LOCK", tmp_path / "worker.lock")
    calls = []
    monkeypatch.setattr(worker, "finish", lambda *args: calls.append(args))
    monkeypatch.setattr(worker, "prepare_attempt",
                        lambda *a: (_ for _ in ()).throw(AssertionError("duplicate attempt")))
    assert worker.main(path) == 0
    assert len(calls) == 1
    assert calls[0][1]["run_token"] == task["run_token"]
    assert json.loads(worker.result_path(task["id"]).read_text()) == result


def test_absent_blocker_spellings_cannot_bypass_completion_evidence(tmp_path):
    for blocker in (None, "", "none", " null ", "NONE"):
        task, path, result = verification_task(tmp_path)
        result["blocker"] = blocker
        worker.write_json(worker.result_path(task["id"]), result)
        worker.finish(path, task, "")
        saved = json.loads((worker.BLOCKED / path.name).read_text())
        assert saved["attempt_state"] == "blocked"
        assert saved["verification_resolution"] == "needs_replan"
        assert saved["verification_status"] == "evidence_invalid"
        assert not list(worker.DONE.iterdir())
        assert json.loads(worker.result_path(task["id"]).read_text()) == result
        (worker.BLOCKED / path.name).unlink()

def test_control_cycle_without_predispatch_plan_stays_unverified(tmp_path):
    task, path, result = verification_task(tmp_path)
    task["kind"] = "github_root_orchestration"
    worker.finish(path, task, "")
    saved = json.loads((worker.BLOCKED / path.name).read_text())
    assert saved["verification_status"] == "evidence_invalid"
    assert not list(worker.DONE.iterdir())


def test_control_evidence_is_retained_and_restart_reuses_immutable_bundle(tmp_path):
    task, path, result = verification_task(tmp_path)
    task["kind"] = "github_root_orchestration"
    worker.freeze_plan(worker.ROOT, task)
    from agent_completion_evidence import verify_completion
    first = verify_completion(worker.ROOT, task, result)
    second = verify_completion(worker.ROOT, task, result)
    assert first == second and first["level"] == "control_cycle"
    assert len(list((worker.ROOT / "verification").glob("accepted-*"))) == 1
    assert first["integration"] is None and first["deployment"] is None
    task["prompt"] = "changed specification"
    from herdr.evidence import EvidenceError
    import pytest
    with pytest.raises(EvidenceError, match="specification"):
        verify_completion(worker.ROOT, task, result)

def test_worker_prompt_exposes_frozen_criteria_and_limited_completion_level(tmp_path):
    task, path, result = verification_task(tmp_path)
    task["kind"] = "github_root_orchestration"
    worker.freeze_plan(worker.ROOT, task)
    prompt = worker.prompt_text(task)
    assert "HOST COMPLETION VERIFICATION" in prompt
    assert "does not satisfy an implementation" in prompt
    assert task["completion_plan"]["kind"] == "control"
    assert len(task["completion_plan"]["plan_hash"]) == 64


def test_permanently_invalid_evidence_requires_replan_without_endless_reconciliation(tmp_path, monkeypatch):
    from herdr.evidence import EvidenceError
    task, path, result = verification_task(tmp_path)
    monkeypatch.setattr(worker, "verify_completion",
                        lambda *a: (_ for _ in ()).throw(EvidenceError("pinned workflow changed")))
    worker.finish(path, task, "")
    blocked = worker.BLOCKED / path.name
    saved = json.loads(blocked.read_text())
    assert saved["attempt_state"] == "blocked"
    assert saved["verification_resolution"] == "needs_replan"
    assert "Replan" in saved["verification_next_action"]
    assert "not_before" not in saved
    assert saved["run_token"] == task["run_token"]
    monkeypatch.setattr(worker, "LOCK", tmp_path / "worker.lock")
    monkeypatch.setattr(worker, "prepare_attempt",
                        lambda *a: (_ for _ in ()).throw(AssertionError("economic redispatch")))
    assert worker.main(blocked) == 0
    assert json.loads(worker.result_path(task["id"]).read_text()) == result


def test_control_cycle_cannot_publish_conflicting_outcomes_for_one_attempt(tmp_path):
    from agent_completion_evidence import verify_completion
    from herdr.evidence import EvidenceError
    import pytest
    task, path, result = verification_task(tmp_path)
    task["kind"] = "github_root_orchestration"
    worker.freeze_plan(worker.ROOT, task)
    first = verify_completion(worker.ROOT, task, result)
    result["summary"] = "contradictory second result"
    with pytest.raises(EvidenceError, match="immutable"):
        verify_completion(worker.ROOT, task, result)
    assert len(list((worker.ROOT / "verification").glob("accepted-*"))) == 1


def test_control_upgrade_preserves_legacy_outcome_and_rejects_rewrite(tmp_path):
    from agent_completion_evidence import verify_completion
    from herdr.evidence import EvidenceStore, binding, digest, EvidenceError
    import pytest
    task, path, result = verification_task(tmp_path)
    task["kind"] = "github_root_orchestration"
    worker.freeze_plan(worker.ROOT, task)
    first = verify_completion(worker.ROOT, task, result)
    store = EvidenceStore(worker.ROOT / "verification")
    plan_hash = first["plan_hash"]
    payload = {k: v for k, v in first.items() if k != "bundle_hash"}
    old_key = digest({"identity": binding(task), "plan_hash": plan_hash, "result_hash": digest(result)})
    new_key = digest({"identity": binding(task), "plan_hash": plan_hash})
    store.publish("accepted", old_key, payload)
    store._path("accepted", new_key).unlink()
    assert verify_completion(worker.ROOT, task, result) == first
    result["summary"] = "rewritten after upgrade"
    with pytest.raises(EvidenceError, match="conflict"):
        verify_completion(worker.ROOT, task, result)
    assert store.read("accepted", old_key) == payload


def test_incomplete_control_publication_is_replan_not_missing_late_evidence(tmp_path):
    for field in ("summary", "next_action"):
        task, path, result = verification_task(tmp_path)
        task["kind"] = "github_root_orchestration"
        worker.freeze_plan(worker.ROOT, task)
        result.pop(field)
        worker.write_json(worker.result_path(task["id"]), result)
        worker.finish(path, task, "")
        saved = json.loads((worker.BLOCKED / path.name).read_text())
        assert saved["verification_status"] == "evidence_invalid"
        assert saved["verification_resolution"] == "needs_replan"
        assert saved["attempts"] == 0
        (worker.BLOCKED / path.name).unlink()


def test_predispatch_outage_retries_same_unexecuted_attempt(tmp_path, monkeypatch):
    from herdr.evidence import EvidenceUnavailable
    configure_paths(tmp_path)
    monkeypatch.setattr(worker, "LOCK", tmp_path / "worker.lock")
    task = base_task()
    path = worker.RUNNING / "task-1.json"
    worker.write_json(path, task)
    calls = []
    def unavailable(root, task):
        calls.append((task["run_token"], task["idempotency_key"], task["attempt_id"]))
        raise EvidenceUnavailable("baseline service offline")
    monkeypatch.setattr(worker, "freeze_plan", unavailable)
    monkeypatch.setattr(worker, "create_task_session",
                        lambda *a: (_ for _ in ()).throw(AssertionError("economic dispatch")))
    assert worker.main(path) == 0
    pending = worker.PENDING / path.name
    first = json.loads(pending.read_text())
    assert first["completion_plan_pending"] and first["attempts"] == 0
    assert first["attempt_state"] == "retry_scheduled"
    assert not worker.result_path("task-1").exists()
    assert worker.main(pending) == 0
    second = json.loads(pending.read_text())
    assert first["run_token"] == second["run_token"]
    assert calls[0] == calls[1]
    assert not list(worker.BLOCKED.iterdir())


def test_worker_cleanup_failure_retains_completed_publication_for_recovery(tmp_path, monkeypatch):
    task, path, result = verification_task(tmp_path)
    task["execution_session"] = {"owned_pane": True, "pane_id": "pane"}
    monkeypatch.setattr(worker, "verify_completion", lambda *a:
                        {"level": "verified_worker_result", "bundle_hash": "a" * 64})
    monkeypatch.setattr(worker, "cleanup_task_session", lambda *a: False)
    worker.finish(path, task, "")
    assert worker.cleanup_task_session_if_safe(task) is False
    blocked = worker.BLOCKED / path.name
    saved = json.loads(blocked.read_text())
    assert saved["watchdog_blocker"] == "task_session_cleanup_failed"
    assert saved["verification_status"] == "accepted"
    assert json.loads(worker.result_path(task["id"]).read_text()) == result
    assert not list(worker.RESULTS.glob("*.previous-*.json"))


def test_other_consumer_completion_remains_explicitly_unverified(tmp_path):
    task, path, result = verification_task(tmp_path)
    task["repo"] = "Bbambaaamm/Autonomous-Quant-Lab"
    worker.finish(path, task, "")
    saved = json.loads((worker.DONE / path.name).read_text())
    assert saved["completion_level"] == "legacy_unverified_result"
    assert saved["completion_bundle_hash"] is None
    assert saved["verification_status"] == "legacy_unverified"



@pytest.mark.parametrize("phase", ["bridge", "sandbox", "agent"])
def test_canonical_queue_owns_session_before_worker_crash(tmp_path, monkeypatch, phase):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    task["workspace"] = str(tmp_path / "workspace")
    task["routing"] = {"selected_agent": "quantlab-hermes"}
    sidecar = tmp_path / "attempts" / "immutable-attempt.json"
    sidecar.parent.mkdir()
    task["task_file"] = str(sidecar)
    canonical = worker.RUNNING / (task["id"] + ".json")
    worker.write_json(canonical, task)
    policy = _policy_file(tmp_path)
    monkeypatch.setattr(worker, "frozen_policy", lambda: policy)
    monkeypatch.setattr(worker, "sandbox_command", lambda *a, **k: ["bwrap", "/bin/bash"])
    monkeypatch.setattr(worker, "verify_sandbox", lambda *a, **k: True)
    monkeypatch.setattr(worker, "inner_pid", lambda *a, **k: 123)
    monkeypatch.setattr(worker, "_setup_pane_ids", lambda: {"coordinator"})
    def crash_if(expected):
        recorded = json.loads(canonical.read_text())
        assert recorded["run_token"] == task["run_token"]
        assert recorded["execution_session"]["pane_id"] == "owned"
        assert json.loads(sidecar.read_text())["execution_session"]["pane_id"] == "owned"
        if phase == expected:
            raise SystemExit("simulated worker death")
    def bridge(current, session):
        crash_if("bridge")
        session.update(bridge_pid=1234, bridge_socket="@fixture",
                       bridge_task_id=current["id"], bridge_run_token=current["run_token"])
        worker.persist_execution_session(current)
    def herdr(args, **kwargs):
        if args[:2] == ["agent", "get"]:
            return {"result": {"agent": {"kind": "hermes", "pane_id": "coordinator", "workspace_id": "workspace"}}}
        if args[:2] == ["pane", "split"]:
            return {"result": {"pane": {"pane_id": "owned"}}}
        if args[:2] == ["pane", "run"]:
            crash_if("sandbox")
            return {"result": {}}
        if args[:2] == ["pane", "process-info"]:
            return {"result": {"process_info": {}}}
        if args[:2] == ["agent", "start"]:
            crash_if("agent")
        raise AssertionError(args)
    monkeypatch.setattr(worker, "start_bridge", bridge)
    monkeypatch.setattr(worker, "_herdr_json", herdr)
    with pytest.raises(SystemExit, match="worker death"):
        worker.create_task_session(task)
    recovered = json.loads(canonical.read_text())
    session = recovered["execution_session"]
    assert session["owned_pane"] and not session.get("closed_at")
    if phase != "bridge":
        assert session["bridge_pid"] == 1234 and session["policy_file"] == str(policy)
    if phase == "agent":
        assert session["sandbox_verified"] and session["agent_start_attempted"]
        assert session["sandbox_attestation"]["run_token"] == task["run_token"]
    # Recovery uses the actual canonical record, not the attempts sidecar.
    recovery_loader = SourceFileLoader("session_crash_recovery", str(BIN / "agent-stack-recovery"))
    recovery_spec = importlib.util.spec_from_loader(recovery_loader.name, recovery_loader)
    recovery = importlib.util.module_from_spec(recovery_spec)
    recovery_loader.exec_module(recovery)
    closed, stopped = [], []
    monkeypatch.setattr(recovery, "_pane_presence", lambda _: True)
    monkeypatch.setattr(recovery, "_pane_has_marker", lambda pane, marker: pane == "owned" and marker == session["pane_marker"])
    def close(args, **kwargs):
        closed.append(args)
        return worker.subprocess.CompletedProcess(args, 0, stdout="", stderr="")
    monkeypatch.setattr(recovery.subprocess, "run", close)
    monkeypatch.setattr(recovery, "stop_task_bridge", lambda current: stopped.append(current.get("bridge_pid")))
    assert recovery.cleanup_task_owned_pane(recovered)
    assert closed[0][-1] == "owned" and stopped
    assert recovered["execution_session"]["closed_at"]


@pytest.mark.parametrize("changed_field",["run_token","fencing_token"])
def test_session_publication_preserves_canonical_truth_and_rejects_another_attempt(tmp_path,changed_field):
    configure_paths(tmp_path)
    task = base_task()
    worker.prepare_attempt(task)
    sidecar = tmp_path / "attempts" / "attempt.json"
    sidecar.parent.mkdir()
    task["task_file"] = str(sidecar)
    task["execution_session"] = {"owned_pane": True, "pane_id": "owned"}
    canonical = worker.RUNNING / (task["id"] + ".json")
    current = dict(task, last_observation="authoritative-current", attempt_state="working")
    worker.write_json(canonical, current)
    worker.persist_execution_session(task)
    recorded = json.loads(canonical.read_text())
    assert recorded["last_observation"] == "authoritative-current"
    assert recorded["attempt_state"] == "working"
    original = canonical.read_bytes()
    task[changed_field] = "different-attempt" if changed_field=="run_token" else task["fencing_token"]+1
    with pytest.raises(RuntimeError, match="identity_changed"):
        worker.persist_execution_session(task)
    assert canonical.read_bytes() == original


def test_worker_session_writes_fsync_file_then_directory(tmp_path, monkeypatch):
    import os, stat
    observed = []
    original = os.fsync
    def fsync(fd):
        observed.append(os.fstat(fd).st_mode)
        original(fd)
    monkeypatch.setattr(worker.os, "fsync", fsync)
    worker.write_json(tmp_path / "record.json", {"session": "owned"})
    assert len(observed) == 2 and stat.S_ISREG(observed[0]) and stat.S_ISDIR(observed[1])
    assert (tmp_path / "record.json").stat().st_mode & 0o777 == 0o600
    assert not list(tmp_path.glob("*.tmp"))

@pytest.fixture(autouse=True)
def explicit_host_policy_for_worker_lifecycle_tests(monkeypatch):
    from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
    monkeypatch.setattr(worker, "HOST_POLICY_LAUNCH_FACTORY", FakeHostPolicyLaunchFactory())
    monkeypatch.setattr(worker, "HOST_POLICY_LAUNCHES", {})
    monkeypatch.setattr(worker, "_preflight_root_provider", lambda profile: None)
    original = worker.create_task_session
    def create(task, **kwargs):
        task.setdefault("fencing_token", 1)
        return original(task, **kwargs)
    monkeypatch.setattr(worker, "create_task_session", create)


def test_standalone_root_worker_loads_fixed_host_configuration_each_attempt(monkeypatch):
    from herdr import host_configuration
    from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
    factories=[]
    def build():
        item=FakeHostPolicyLaunchFactory();factories.append(item);return item
    monkeypatch.setattr(worker,"HOST_POLICY_LAUNCH_FACTORY",None)
    monkeypatch.setattr(host_configuration,"build_host_policy_factory",build)
    assert worker._root_policy_factory() is not worker._root_policy_factory()
    assert len(factories)==2

def test_root_host_provider_preflight_precedes_pane_creation_and_failure_cleans_launch(tmp_path,monkeypatch):
    configure_paths(tmp_path);task=base_task();worker.prepare_attempt(task)
    task["workspace"]=str(tmp_path)
    events=[]
    def control(args,**kwargs):
        events.append(tuple(args))
        assert args[:2]==["agent","get"]
        return {"result":{"agent":{"agent":"hermes","pane_id":"coordinator-pane","workspace_id":"workspace"}}}
    def preflight(profile):
        raise RuntimeError("host preflight denied")
    monkeypatch.setattr(worker,"_herdr_json",control)
    monkeypatch.setattr(worker,"_preflight_root_provider",preflight)
    with pytest.raises(RuntimeError,match="host preflight denied"):worker.create_task_session(task)
    launch=worker.HOST_POLICY_LAUNCH_FACTORY.created[0]
    assert launch.events==[("closed",)]
    assert worker.HOST_POLICY_LAUNCHES=={}
    assert len(events)==1


@pytest.mark.parametrize("reason",["workspace outside host policy","requested tools/permissions exceed host ceiling"])
def test_deterministic_host_prepare_denial_has_permanent_policy_prefix(tmp_path,monkeypatch,reason):
    from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
    from herdr.security import SecurityError
    configure_paths(tmp_path);task=base_task();worker.prepare_attempt(task);task["workspace"]=str(tmp_path)
    calls=[]
    def control(args,**kwargs):
        calls.append(args);assert args[:2]==["agent","get"]
        return {"result":{"agent":{"kind":"hermes","pane_id":"coordinator","workspace_id":"workspace"}}}
    factory=FakeHostPolicyLaunchFactory()
    def denied(**kwargs):raise SecurityError(reason)
    monkeypatch.setattr(factory,"prepare",denied);monkeypatch.setattr(worker,"_herdr_json",control)
    with pytest.raises(RuntimeError,match="task_invocation_policy_denied"):
        worker.create_task_session(task,policy_launch_factory=factory)
    assert len(calls)==1 and not worker.HOST_POLICY_LAUNCHES


def _modern_root_session(task):
    task.update(run_token="root-run", fencing_token=9, routing={"selected_agent":"quantlab-hermes"})
    agent, marker = worker._task_session_identity(task)
    session = dict(agent_name=agent, session_name=marker, pane_marker=marker, pane_id="owned-pane",
        coordinator_agent="quantlab-hermes", coordinator_pane_id="coordinator", owned_pane=True,
        economic_delivery_attempted=False, sandbox_verified=True, sandbox_pid=123)
    task["execution_session"] = session
    session["launch_identity"] = worker._root_launch_identity(task).to_json()
    return session

@pytest.mark.parametrize("fault", [None, "foreign-agent", "foreign-coordinator", "foreign-fence"])
def test_cold_root_cleanup_uses_preseal_identity_without_invocation_proof(tmp_path, monkeypatch, fault):
    task = base_task(); session = _modern_root_session(task)
    monkeypatch.setattr(worker,"HOST_POLICY_LAUNCHES",{})
    cleaned = []
    from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
    factory = FakeHostPolicyLaunchFactory()
    factory.cleanup_orphan = lambda identity: cleaned.append(identity) or True
    monkeypatch.setattr(worker,"_root_policy_factory",lambda:factory)
    if fault=="foreign-agent": session["agent_name"]="foreign"
    if fault=="foreign-coordinator": session["coordinator_agent"]="foreign"
    if fault=="foreign-fence": session["launch_identity"]["fencing_token"]=10
    if fault:
        with pytest.raises((RuntimeError, ValueError)): worker._cleanup_prepared_root_launch(task)
        assert not cleaned
    else:
        worker._cleanup_prepared_root_launch(task)
        assert len(cleaned)==1 and cleaned[0].to_json()==session["launch_identity"]

@pytest.mark.parametrize("fault", [None, "stderr", "mixed", "transport", "prompt", "legacy", "pid", "proof", "marker", "foreign"])
def test_root_setup_absent_agent_cleanup_requires_full_pre_prompt_physical_proof(tmp_path, monkeypatch, fault):
    import subprocess
    from herdr import policy_launch
    task = base_task(); session = _modern_root_session(task)
    session["invocation_policy"] = {"identity":session["launch_identity"]}
    session["sandbox_attestation"] = {"physical":"fixture"}
    if fault=="prompt": session["economic_delivery_attempted"]=True
    if fault=="legacy": session.pop("economic_delivery_attempted")
    if fault=="foreign": session["launch_identity"]["fencing_token"]=10
    closed = []; checked = []
    monkeypatch.setattr(worker,"_pane_has_marker",lambda *args:fault!="marker")
    monkeypatch.setattr(worker,"_close_owned_pane",lambda pane:closed.append(pane) or True)
    def native(args,**kwargs):
        if args[:2]==["pane","list"]: return {"result":{"panes":[{"pane_id":"owned-pane"}]}}
        if args[:2]==["agent","get"]: raise RuntimeError("native absent")
        if args[:2]==["pane","process-info"]: return {"result":{"process_info":{"shell_pid":123}}}
        raise AssertionError(args)
    monkeypatch.setattr(worker,"_herdr_json",native)
    raw='{"error":{"code":"agent_not_found"}}'
    monkeypatch.setattr(worker.subprocess,"run",lambda *args,**kw:subprocess.CompletedProcess(args,
        2 if fault=="transport" else 1, "" if fault=="stderr" else raw, raw if fault in {"stderr","mixed"} else ""))
    monkeypatch.setattr(worker,"inner_pid",lambda *args:124 if fault=="pid" else 123)
    def verify(evidence,**kwargs):
        if fault=="proof": raise ValueError("changed physical proof")
        checked.append(kwargs)
    monkeypatch.setattr(policy_launch,"verify_retained_policy_evidence",verify)
    answer=worker._cleanup_setup_pane("owned-pane","coordinator",session["pane_marker"],session["agent_name"],True,set(),task=task)
    assert answer is (fault in {None,"stderr"})
    assert closed==(["owned-pane"] if answer else [])
    if answer:
        assert len(checked)==1 and checked[0]["require_bootstrap"] is False
        assert checked[0]["identity"].to_json()==session["launch_identity"]

def test_modern_root_prompt_intent_is_persisted_before_effect_and_never_repeats(tmp_path,monkeypatch):
    import subprocess
    configure_paths(tmp_path);task=base_task();session=_modern_root_session(task)
    monkeypatch.setattr(worker,"prompt_text",lambda task:"bounded work")
    events=[]
    monkeypatch.setattr(worker,"persist_execution_session",lambda task,**kw:events.append(("intent",task["execution_session"]["economic_delivery_attempted"])))
    monkeypatch.setattr(worker.subprocess,"run",lambda *args,**kw:events.append(("native",)) or subprocess.CompletedProcess(args,0,"ok",""))
    assert worker.run_prompt(task)==(0,"ok")
    assert events==[("intent",True),("native",)]
    with pytest.raises(RuntimeError,match="already_started"):worker.run_prompt(task)
    assert len(events)==2


def test_root_preparation_crash_retains_full_identity_before_any_resource(tmp_path,monkeypatch):
    from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
    configure_paths(tmp_path);task=base_task();worker.prepare_attempt(task)
    task["workspace"]=str(tmp_path);task["fencing_token"]=17
    calls=[]
    def native(args,**kw):
        calls.append(args);assert args[:2]==["agent","get"]
        return {"result":{"agent":{"kind":"hermes","pane_id":"coordinator","workspace_id":"workspace"}}}
    monkeypatch.setattr(worker,"_herdr_json",native)
    resources=tmp_path/"simulated-frozen-launch";factory=FakeHostPolicyLaunchFactory()
    def prepare(**kwargs):
        retained=json.loads((worker.RUNNING/(task["id"]+".json")).read_text())
        session=retained["execution_session"]
        assert session["launch_identity"]==kwargs["identity"].to_json()
        assert session["launch_intent_version"]==1
        assert session["pane_split_started"] is False and session["agent_start_attempted"] is False
        resources.write_text("prepared")
        raise SystemExit("simulated worker death after resource preparation")
    monkeypatch.setattr(factory,"prepare",prepare)
    with pytest.raises(SystemExit):worker.create_task_session(task,policy_launch_factory=factory)
    restored=json.loads((worker.RUNNING/(task["id"]+".json")).read_text())
    assert restored["run_token"]==task["run_token"] and restored["fencing_token"]==17
    assert resources.exists() and len(calls)==1
    cleaned=[]
    factory.cleanup_orphan=lambda identity:cleaned.append(identity.to_json()) or resources.unlink() or True
    monkeypatch.setattr(worker,"_root_policy_factory",lambda:factory)
    monkeypatch.setattr(worker,"HOST_POLICY_LAUNCHES",{})
    assert worker.cleanup_task_session(restored)
    assert not resources.exists() and cleaned==[restored["execution_session"]["launch_identity"]]
    assert restored["execution_session"]["cleanup_status"]=="closed_before_split"
    assert restored["run_token"]==task["run_token"] and restored["fencing_token"]==17

@pytest.mark.parametrize("fault",["split","unknown-split","start","prompt","legacy"])
def test_sessionless_root_cleanup_never_guesses_after_native_intent(tmp_path,monkeypatch,fault):
    configure_paths(tmp_path);task=base_task();session=_modern_root_session(task)
    task["task_file"]=str(worker.RUNNING/"task-1.json")
    session.update(pane_id="",launch_intent_version=1,pane_split_started=False,agent_start_attempted=False)
    if fault=="split":session["pane_split_started"]=True
    if fault=="unknown-split":session["pane_split_started"]=None
    if fault=="start":session["agent_start_attempted"]=True
    if fault=="prompt":session["economic_delivery_attempted"]=True
    if fault=="legacy":session.pop("launch_intent_version")
    monkeypatch.setattr(worker,"_cleanup_prepared_root_launch",lambda _:pytest.fail("ambiguous root resources released"))
    monkeypatch.setattr(worker,"_herdr_json",lambda *args,**kw:pytest.fail("empty pane guessed as native quiescence"))
    assert worker.cleanup_task_session(task) is False
    assert session["cleanup_status"]=="close_unproven" and "closed_at" not in session


def test_actual_root_setup_failure_passes_task_to_absent_agent_cleanup(tmp_path,monkeypatch):
    configure_paths(tmp_path);task=base_task();worker.prepare_attempt(task)
    task.update(workspace=str(tmp_path),parent_tools=["read_file","herdr_submit_result"],
                parent_permissions=["repo:read"],fencing_token=3)
    def native(args,**kw):
        if args[:2]==["agent","get"]:
            return {"result":{"agent":{"kind":"hermes","pane_id":"coordinator","workspace_id":"workspace"}}}
        if args[:2]==["pane","list"]:return {"result":{"panes":[{"pane_id":"coordinator"}]}}
        if args[:2]==["pane","split"]:return {"result":{"pane":{"pane_id":"owned"}}}
        if args[:2]==["pane","process-info"]:return {"result":{"process_info":{"shell_pid":123}}}
        if args[:2]==["pane","run"]:return {"result":{}}
        if args[:2]==["agent","start"]:raise RuntimeError("native start absent")
        raise AssertionError(args)
    monkeypatch.setattr(worker,"_herdr_json",native)
    monkeypatch.setattr(worker,"start_bridge",lambda *args:None)
    monkeypatch.setattr(worker,"stop_bridge",lambda *args:None)
    monkeypatch.setattr(worker,"frozen_policy",lambda:_policy_file(tmp_path))
    monkeypatch.setattr(worker,"sandbox_command",lambda *args,**kw:["/bin/true"])
    monkeypatch.setattr(worker,"inner_pid",lambda *args:123)
    monkeypatch.setattr(worker,"verify_sandbox",lambda *args,**kw:True)
    cleaned=[]
    def clean(*args,**kw):
        assert kw["task"] is task
        assert kw["task"]["execution_session"]["agent_start_attempted"] is True
        cleaned.append(args[0]);return True
    monkeypatch.setattr(worker,"_cleanup_setup_pane",clean)
    with pytest.raises(RuntimeError,match="native start absent"):
        worker.create_task_session(task)
    assert cleaned==["owned"] and task["execution_session"]["cleanup_status"]=="closed"

def test_quantlab_completion_prompt_matches_closed_result_tool(tmp_path):
    configure_paths(tmp_path);task=base_task()
    task["repo"]="Bbambaaamm/Autonomous-Quant-Lab"
    task["safety_profile"]="quantlab-paper"
    worker.prepare_attempt(task)
    rendered=worker.prompt_text(task)
    assert "Supply only status, evidence and summary" in rendered
    assert "Include keys:" not in rendered
    assert "herdr_submit_result" in rendered

def test_modern_work_contract_missing_host_authority_blocks_before_pane_creation(tmp_path,monkeypatch):
    configure_paths(tmp_path)
    task=base_task()
    task.update(work_contract_version=1,run_token="modern-run",workspace=str(tmp_path/"workspace"))
    monkeypatch.setattr(worker,"HOST_WORK_CONTRACT_FACTORY",None)
    monkeypatch.setattr(worker,"_herdr_json",lambda *a,**kw:pytest.fail("no pane or agent may be created"))
    with pytest.raises(RuntimeError,match="authority_missing"):
        worker.create_task_session(task)
    assert "execution_session" not in task

@pytest.mark.parametrize("version",[True,"1",2,0])
def test_unsupported_modern_contract_is_not_treated_as_legacy(tmp_path,monkeypatch,version):
    configure_paths(tmp_path)
    task=base_task()
    task.update(work_contract_version=version,run_token="modern-run",execution_session={"agent_name":"worker"})
    original_run=worker.subprocess.run
    def no_dispatch(argv,*args,**kwargs):
        if argv and str(argv[0])==str(worker.HERDR):
            pytest.fail("must not dispatch")
        return original_run(argv,*args,**kwargs)
    monkeypatch.setattr(worker.subprocess,"run",no_dispatch)
    with pytest.raises(RuntimeError,match="version_unsupported"):
        worker.run_prompt(task)

def test_modern_prompt_missing_or_finished_cycle_cannot_restart_implementation(tmp_path,monkeypatch):
    from dataclasses import replace
    from herdr.work_cycle import WorkCycle,WorkPhase
    from tests.herdr.test_work_cycle import setup,trusted_git
    configure_paths(tmp_path)
    task=base_task()
    task.update(work_contract_version=1,run_token="modern-run",execution_session={"agent_name":"worker"})
    monkeypatch.setattr(worker,"HOST_WORK_CYCLES",{})
    original_run=worker.subprocess.run
    def no_dispatch(argv,*args,**kwargs):
        if argv and str(argv[0])==str(worker.HERDR):
            pytest.fail("must not dispatch")
        return original_run(argv,*args,**kwargs)
    monkeypatch.setattr(worker.subprocess,"run",no_dispatch)
    with pytest.raises(RuntimeError,match="forbids_implementation"):
        worker.run_prompt(task)
    cycle,root,plan,log=setup(tmp_path/"contract")
    cycle.phase=WorkPhase.HYGIENE
    worker.HOST_WORK_CYCLES[(task["id"],task["run_token"])]=cycle
    task["work_contract"]={"plan_sha256":plan.hash}
    with pytest.raises(RuntimeError,match="forbids_implementation"):
        worker.run_prompt(task)

def test_legacy_completion_spec_digest_keeps_original_meaning():
    import agent_completion_evidence as completion
    from herdr.evidence import digest
    task=base_task()
    keys=("repo","issue","kind","prompt","completion_kind","spec_hash","completion_contract","completion_evidence","child_completion_contracts")
    assert completion.spec_digest(task)==digest({key:task.get(key) for key in keys})
    task["work_contract_version"]=1
    assert completion.spec_digest(task)!=digest({key:task.get(key) for key in keys})
