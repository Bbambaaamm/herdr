import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BIN = Path(__file__).resolve().parents[2] / "agent-stack" / "bin"
sys.path.insert(0, str(BIN))
import agent_completion_evidence as collector
from herdr.evidence import EvidenceError, EvidenceMissing, EvidenceUnavailable
from herdr.workspace import ArtifactRef


def proof_fixture():
    head, base = "a" * 40, "b" * 40
    artifact = ArtifactRef("task", 1, base, head, "c" * 64, ("result.py",), "result")
    plan = {"repo": "Bbambaaamm/herdr", "required_checks": list(collector.CHECK_APPS),
            "environment": {"ci_workflow_blob_sha": "f" * 40}}
    pr = {"head": {"sha": head, "repo": {"full_name": plan["repo"]}},
          "base": {"sha": base, "repo": {"full_name": plan["repo"]}, "ref": "main"}}
    checks = {"check_runs": [
        {"name": name, "head_sha": head, "app": {"id": app},
         "id": i, "status": "completed", "conclusion": "success",
         "details_url": f"https://github.com/{plan['repo']}/actions/runs/7"}
        for i, (name, app) in enumerate(collector.CHECK_APPS.items(), 1)
    ]}
    comment = {"id": 8, "user": {"login": collector.BOT, "type": "Bot"},
               "body": f"Codex Review: Didn't find any major issues. Bravo.\n**Reviewed commit:** \x60{head[:10]}\x60",
               "created_at": "2026-10-03T20:00:00Z"}
    plan.update(identity={"id":"task","run_token":"run","attempt":1,
                "idempotency_key":"key","fencing_token":2},
                spec_hash="d"*64,policy_hash="e"*64,base_sha=base)
    return artifact, plan, pr, checks, comment


def install_transport(monkeypatch, artifact, plan, pr, checks, comment, *, resolved=None, reviews=()):
    calls = []
    def api(path):
        calls.append(path)
        if "/contents/" in path:
            return {"sha": plan["environment"]["ci_workflow_blob_sha"]}
        if "/actions/runs/" in path:
            return {"id": 7, "workflow_id": collector.POLICY["workflow_id"],
                    "path": collector.POLICY["workflow"], "head_sha": artifact.commit_sha,
                    "repository": {"full_name": plan["repo"]}, "event": "pull_request", "conclusion": "success"}
        if "/pulls/" in path and path.endswith("/reviews?per_page=100"):
            return list(reviews)
        if "/pulls/" in path:
            return pr
        if "check-runs" in path:
            return checks
        if "/issues/" in path:
            return [comment]
        if "/commits/" in path:
            from herdr.verification_binding import commit_footer
            return {"sha": resolved or artifact.commit_sha,
                    "commit":{"message":"Candidate\n\n"+commit_footer(plan)}}
        raise AssertionError(path)
    monkeypatch.setattr(collector, "github", api)
    monkeypatch.setattr(collector, "_unresolved_threads", lambda *a: False)
    return calls


def test_collector_verifies_actual_application_identity_and_full_resolved_commit(monkeypatch):
    artifact, plan, pr, checks, comment = proof_fixture()
    calls = install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    proof = collector.collect_github(plan, artifact, 4)
    assert proof["source"] == "github-api"
    assert proof["review"]["actor"] == collector.BOT
    assert proof["review"]["commit_sha"] == artifact.commit_sha
    assert proof["review"]["comment_id"] == 8
    assert any(path.endswith(artifact.commit_sha[:10]) for path in calls)
    assert {n: r["app_id"] for n, r in proof["checks"].items()} == collector.CHECK_APPS


@pytest.mark.parametrize("fault", ["worker_producer", "wrong_project", "different_commit",
                                   "different_base", "wrong_bot", "stale_review",
                                   "new_findings", "pending_ci"])
def test_collector_rejects_untrusted_or_stale_evidence(monkeypatch, fault):
    artifact, plan, pr, checks, comment = proof_fixture()
    resolved, reviews = None, ()
    if fault == "worker_producer":
        checks["check_runs"][0]["app"]["id"] = 1
    elif fault == "wrong_project":
        pr["head"]["repo"]["full_name"] = "other/project"
    elif fault == "different_commit":
        pr["head"]["sha"] = "d" * 40
    elif fault == "different_base":
        pr["base"]["sha"] = "d" * 40
    elif fault == "wrong_bot":
        comment["user"] = {"login": "worker", "type": "User"}
    elif fault == "stale_review":
        resolved = "d" * 40
    elif fault == "pending_ci":
        checks["check_runs"][0]["conclusion"] = None
    else:
        reviews = ({"commit_id": artifact.commit_sha, "user": {"login": collector.BOT},
                    "submitted_at": "2026-10-03T21:00:00Z", "state": "COMMENTED"},)
    install_transport(monkeypatch, artifact, plan, pr, checks, comment,
                      resolved=resolved, reviews=reviews)
    with pytest.raises(EvidenceError):
        collector.collect_github(plan, artifact, 4)


def test_collector_rejects_unresolved_threads(monkeypatch):
    artifact, plan, pr, checks, comment = proof_fixture()
    install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    monkeypatch.setattr(collector, "_unresolved_threads", lambda *a: True)
    with pytest.raises(EvidenceMissing, match="unresolved"):
        collector.collect_github(plan, artifact, 4)


def test_old_cli_paginated_json_is_parsed_without_slurp(monkeypatch):
    calls = []
    pages = '[{"id":1}]\n[{"id":2}]\n'
    def process(args, **kwargs):
        calls.append(args)
        return pages.encode()
    monkeypatch.setattr(collector, "github_command", process)
    assert collector.github("repos/Bbambaaamm/herdr/issues/81/comments") == [{"id": 1}, {"id": 2}]
    assert "--slurp" not in calls[0]
    assert calls[0][calls[0].index("--hostname") + 1] == "github.com"


@pytest.mark.parametrize("stdout", ["", "partial{", "null"])
def test_missing_malformed_transport_is_unavailable(monkeypatch, stdout):
    monkeypatch.setattr(collector, "github_command", lambda *a, **k: stdout.encode())
    with pytest.raises(EvidenceUnavailable):
        collector.github("repos/Bbambaaamm/herdr/issues/81/comments")


def test_actual_worker_replays_host_bundle_after_crash_without_recollection(tmp_path, monkeypatch):
    import importlib.util
    from importlib.machinery import SourceFileLoader
    import test_worker_handshake as handshake
    from herdr.evidence import binding, digest
    helper_path = Path(__file__).resolve().parents[1] / "herdr" / "test_evidence.py"
    spec = importlib.util.spec_from_file_location("physical_evidence_fixture", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    from herdr.workspace import _real_git
    monkeypatch.setattr("herdr.evidence.read_only_git", _real_git)
    monkeypatch.setattr("herdr.evidence.verify_invocation_session",helper.launch_fixture)
    task, result, plan, store, workspace, proof = helper.fixture(tmp_path)
    task["workspace"] = str(workspace)
    result.update(task_id=task["id"], run_token=task["run_token"], status="completed",
                  summary="result committed", blocker=None, artifact_workspace=str(workspace))
    handshake.configure_paths(store.root.parent)
    worker = handshake.worker
    path = worker.RUNNING / "task.json"
    path.write_text(json.dumps(task))
    worker.write_json(worker.result_path(task["id"]), result)
    plan["spec_hash"] = collector.spec_digest(task)
    plan["policy_hash"] = digest(collector.typed_policy("coding"))
    plan["plan_hash"] = digest({k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}})
    from herdr.verification_binding import commit_binding
    bound_spec=commit_binding(plan)
    proof["review"]["specification_binding"]={**bound_spec,"binding_sha256":digest(bound_spec)}
    store.publish("plan", digest(binding(task)), plan)
    calls = []
    monkeypatch.setattr(collector, "collect_github", lambda *a: calls.append(a) or proof)
    original_move = worker.move
    def interrupted_move(path, target):
        if target == worker.DONE:
            raise OSError("restart after bundle publication")
        return original_move(path, target)
    monkeypatch.setattr(worker, "move", interrupted_move)
    with pytest.raises(OSError):
        worker.finish(path, task, "completed")
    assert len(calls) == 1
    assert len(list(store.root.glob("accepted-*"))) == 1
    saved = json.loads(path.read_text())
    monkeypatch.setattr(worker, "move", original_move)
    worker.finish(path, saved, "restart reconciliation")
    done = json.loads((worker.DONE / path.name).read_text())
    assert done["completion_level"] == "verified_worker_result"
    assert done["attempt_id"] == 1
    assert done["run_token"] == task["run_token"]
    assert len(calls) == 1

@pytest.mark.parametrize("fault", ["workflow_path", "workflow_identity", "different_workflow_bytes", "different_run_head"])
def test_collector_pins_actual_ci_workflow_and_its_baseline_definition(monkeypatch, fault):
    artifact, plan, pr, checks, comment = proof_fixture()
    install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    old = collector.github
    def api(path):
        data = old(path)
        if "/actions/runs/" in path:
            if fault == "workflow_path": data["path"] = ".github/workflows/spoof.yml"
            elif fault == "workflow_identity": data["workflow_id"] = 1
            elif fault == "different_run_head": data["head_sha"] = "e" * 40
        if "/contents/" in path and fault == "different_workflow_bytes" and path.endswith(artifact.commit_sha):
            data["sha"] = "e" * 40
        return data
    monkeypatch.setattr(collector, "github", api)
    with pytest.raises(EvidenceError):
        collector.collect_github(plan, artifact, 4)


def test_malformed_check_collection_is_unavailable_without_execution_retry(monkeypatch):
    monkeypatch.setattr(collector, "github", lambda *a: {"check_runs": [None]})
    with pytest.raises(EvidenceUnavailable):
        collector.collect_checks("Bbambaaamm/herdr", "a" * 40, list(collector.CHECK_APPS), require_success=True)


def test_collector_rejects_a_pr_head_changed_during_collection(monkeypatch):
    from copy import deepcopy
    artifact, plan, pr, checks, comment = proof_fixture()
    install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    old = collector.github
    count = 0
    def api(path):
        nonlocal count
        data = deepcopy(old(path))
        if path.endswith("/pulls/4"):
            count += 1
            if count == 2:
                data["head"]["sha"] = "e" * 40
        return data
    monkeypatch.setattr(collector, "github", api)
    with pytest.raises(EvidenceError, match="changed during"):
        collector.collect_github(plan, artifact, 4)
    assert count == 2


@pytest.mark.parametrize("actor", [collector.BOT, "human-reviewer", "another-review-bot"])
def test_every_effective_requested_change_blocks_even_before_clean_comment(monkeypatch, actor):
    artifact, plan, pr, checks, comment = proof_fixture()
    reviews = [{"id": 1, "user": {"login": actor}, "state": "CHANGES_REQUESTED",
                "commit_id": "e" * 40, "submitted_at": "2026-10-03T19:00:00Z"},
               {"id": 2, "user": {"login": actor}, "state": "COMMENTED",
                "commit_id": artifact.commit_sha, "submitted_at": "2026-10-03T19:30:00Z"}]
    install_transport(monkeypatch, artifact, plan, pr, checks, comment, reviews=reviews)
    with pytest.raises(EvidenceMissing, match="outstanding"):
        collector.collect_github(plan, artifact, 4)


@pytest.mark.parametrize("state", ["APPROVED", "DISMISSED"])
def test_approved_or_dismissed_change_request_no_longer_blocks(monkeypatch, state):
    artifact, plan, pr, checks, comment = proof_fixture()
    reviews = [{"id": 1, "user": {"login": "reviewer"}, "state": "DISMISSED" if state == "DISMISSED" else "CHANGES_REQUESTED",
                "submitted_at": "2026-10-03T18:00:00Z"},
               {"id": 2, "user": {"login": "reviewer"}, "state": state,
                "submitted_at": "2026-10-03T19:00:00Z"}]
    install_transport(monkeypatch, artifact, plan, pr, checks, comment, reviews=reviews)
    assert collector.collect_github(plan, artifact, 4)["source"] == "github-api"


def test_changes_requested_during_commit_resolution_prevents_acceptance(monkeypatch):
    artifact, plan, pr, checks, comment = proof_fixture()
    install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    old = collector.github
    count = 0
    def api(path):
        nonlocal count
        if path.endswith("/reviews?per_page=100"):
            count += 1
            if count == 2:
                return [{"id": 10, "user": {"login": "human"}, "state": "CHANGES_REQUESTED",
                         "submitted_at": "2026-10-03T20:10:00Z", "commit_id": artifact.commit_sha}]
        return old(path)
    monkeypatch.setattr(collector, "github", api)
    with pytest.raises(EvidenceMissing, match="outstanding"):
        collector.collect_github(plan, artifact, 4)
    assert count == 2


def test_new_unresolved_thread_during_collection_prevents_acceptance(monkeypatch):
    artifact, plan, pr, checks, comment = proof_fixture()
    install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    calls = []
    monkeypatch.setattr(collector, "_unresolved_threads", lambda *a: calls.append(1) or len(calls) == 2)
    with pytest.raises(EvidenceMissing, match="during collection"):
        collector.collect_github(plan, artifact, 4)


@pytest.mark.parametrize("missing", ["artifact", "artifact_workspace", "pr_number"])
def test_missing_immutable_coding_publication_fields_require_replan(tmp_path, monkeypatch, missing):
    import importlib.util
    from herdr.evidence import binding, digest
    from herdr.workspace import _real_git
    helper_path = Path(__file__).resolve().parents[1] / "herdr" / "test_evidence.py"
    spec = importlib.util.spec_from_file_location("immutable_publication_fixture", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    task, result, plan, store, workspace, proof = helper.fixture(tmp_path)
    task["workspace"] = str(workspace)
    result["artifact_workspace"] = str(workspace)
    plan["spec_hash"] = collector.spec_digest(task)
    plan["policy_hash"] = digest(collector.typed_policy("coding"))
    plan["plan_hash"] = digest({k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}})
    store.publish("plan", digest(binding(task)), plan)
    result.pop(missing)
    monkeypatch.setattr("herdr.evidence.read_only_git", _real_git)
    monkeypatch.setattr(collector, "github", lambda *a: (_ for _ in ()).throw(AssertionError("no remote lookup")))
    with pytest.raises(EvidenceError) as error:
        collector.verify_completion(store.root.parent, task, result)
    assert not isinstance(error.value, (EvidenceMissing, EvidenceUnavailable))


@pytest.mark.parametrize("fault", ["rerun_pending", "rerun_wrong_workflow"])
def test_required_checks_and_workflow_are_refreshed_at_final_gate(monkeypatch, fault):
    from copy import deepcopy
    artifact, plan, pr, checks, comment = proof_fixture()
    install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    old = collector.github
    counts = {"checks": 0, "workflow": 0}
    def api(path):
        data = deepcopy(old(path))
        if "check-runs" in path:
            counts["checks"] += 1
            if counts["checks"] == 2 and fault == "rerun_pending":
                row = deepcopy(data["check_runs"][0])
                row.update(id=20, status="in_progress", conclusion=None)
                data["check_runs"].append(row)
        if "/actions/runs/" in path:
            counts["workflow"] += 1
            if counts["workflow"] == 2 and fault == "rerun_wrong_workflow":
                data["workflow_id"] = 1
        return data
    monkeypatch.setattr(collector, "github", api)
    with pytest.raises(EvidenceError):
        collector.collect_github(plan, artifact, 4)
    assert counts["checks"] == 2


def test_herdr_policy_does_not_freeze_other_consumer_tasks(tmp_path):
    task = {"id": "quantlab-1", "repo": "Bbambaaamm/Autonomous-Quant-Lab",
            "kind": "github_issue_slice", "run_token": "run", "idempotency_key": "key"}
    assert not collector.verification_applies(task)
    collector.freeze_plan(tmp_path, task)
    assert not (tmp_path / "verification").exists()
    assert "legacy unverified" in collector.completion_instructions(task)
    task["completion_plan"] = {"plan_hash": "a" * 64}
    assert collector.verification_applies(task)
    with pytest.raises(EvidenceError, match="consumer verification policy"):
        collector.freeze_plan(tmp_path, task)


@pytest.mark.parametrize("refusal",["IN_SCOPE","BLOCK","REPLAN_REQUIRED"])
def test_actual_worker_scope_acceptance_or_typed_permanent_refusal(tmp_path,monkeypatch,refusal):
    import copy
    import test_worker_handshake as handshake
    from tests.herdr.test_scope_evidence import scoped
    from tests.herdr.test_evidence import launch_fixture
    from herdr.evidence import binding,digest
    from herdr.workspace import _real_git
    monkeypatch.setattr("herdr.evidence.read_only_git",_real_git)
    monkeypatch.setattr("herdr.evidence.verify_invocation_session",launch_fixture)
    task,result,plan,store,workspace,proof=scoped(tmp_path)
    task["workspace"]=str(workspace)
    task["completion_contract"]=copy.deepcopy(plan["scope_policy"])
    plan["spec_hash"]=collector.spec_digest(task)
    plan["policy_hash"]=digest(collector.typed_policy("coding"))
    plan["plan_hash"]=digest({k:v for k,v in plan.items() if k not in {"plan_hash","baseline"}})
    result["scope_self_check"]["spec_sha256"]=plan["spec_hash"]
    result["scope_self_check"]["verdict"]=refusal
    result.update(task_id=task["id"],run_token=task["run_token"],status="completed",
        summary="Committed bounded result",blocker=None,artifact_workspace=str(workspace))
    from herdr.verification_binding import commit_binding
    bound_spec=commit_binding(plan)
    proof["review"]["specification_binding"]={**bound_spec,"binding_sha256":digest(bound_spec)}
    store.publish("plan",digest(binding(task)),plan)
    handshake.configure_paths(store.root.parent)
    worker=handshake.worker
    path=worker.RUNNING/"task.json";path.write_text(json.dumps(task))
    worker.write_json(worker.result_path(task["id"]),result)
    calls=[]
    monkeypatch.setattr(collector,"collect_github",lambda *args:calls.append(args) or proof)
    worker.finish(path,task,"completed")
    if refusal=="IN_SCOPE":
        done=json.loads((worker.DONE/path.name).read_text())
        assert done["completion_level"]=="verified_worker_result" and len(calls)==1
        assert done["run_token"]==task["run_token"] and done["fencing_token"]==task["fencing_token"]
    else:
        assert not (worker.DONE/path.name).exists()
        assert not list(store.root.glob("accepted-*")) and calls==[]
        saved=json.loads((worker.BLOCKED/path.name).read_text())
        expected="scope_blocked" if refusal=="BLOCK" else "scope_replan_required"
        assert saved["verification_status"]==expected
        assert saved["attempt_state"]=="blocked" and saved["verification_resolution"]=="needs_replan"
        assert saved["run_token"]==task["run_token"] and saved["fencing_token"]==task["fencing_token"]
        assert "Automatic redispatch is forbidden" in saved["verification_next_action"]


def test_worker_freezes_scope_before_dispatch_and_denies_changed_contract(tmp_path,monkeypatch):
    from tests.herdr.test_scope_evidence import scoped
    from tests.herdr.test_evidence import run_git
    from herdr.evidence import binding,digest
    task,result,plan,store,workspace,proof=scoped(tmp_path)
    task["workspace"]=str(workspace)
    task["completion_contract"]=plan["scope_policy"]
    run_git(workspace,"update-ref","refs/remotes/origin/main",plan["base_sha"])
    monkeypatch.setattr(collector,"workflow_blob",lambda *args:"f"*40)
    monkeypatch.setattr(collector,"collect_checks",lambda *args,**kwargs:{"tests":{"head_sha":plan["base_sha"],"status":"completed"}})
    collector.freeze_plan(store.root.parent,task)
    frozen=store.read("plan",digest(binding(task)))
    assert frozen["scope_policy"]==plan["scope_policy"]
    assert task["completion_plan"]["scope_policy"]==frozen["scope_policy"]
    assert "scope_self_check" in collector.completion_instructions(task)
    task["completion_contract"]["files"].append({"path":"unrelated.py","subtree":False})
    with pytest.raises(EvidenceError,match="immutable completion plan changed"):
        collector.freeze_plan(store.root.parent,task)
