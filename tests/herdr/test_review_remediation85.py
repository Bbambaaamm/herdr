"""Negative host boundaries, real closed result submission, and durable rejection."""
import copy
import hashlib
import json
import sys
from pathlib import Path
import pytest
from herdr.evidence import EvidenceError, EvidenceMissing, EvidenceUnavailable, accept_artifact, digest
from herdr.verification_binding import commit_footer, verify_commit_binding
from herdr.result_candidate import completion_candidate
from herdr.child_evidence import ChildCompletionAuthority
from herdr.scheduler import AuditLog, DynamicChildScheduler, SchedulerError
from tests.herdr.test_evidence import fixture, run_git, launch_fixture
from tests.herdr.test_scope_evidence import scoped
from tests.herdr.test_child_evidence import scheduler_fixture
from herdr.workspace import _real_git

@pytest.mark.parametrize("fault",["spec","policy","run","fence","attempt","missing","duplicate","boolean"])
def test_commit_review_cannot_be_rebound_to_another_frozen_task(tmp_path,fault):
    task,result,plan,store,path,proof=fixture(tmp_path)
    artifact=__import__("herdr.evidence",fromlist=["parse_artifact"]).parse_artifact(result["artifact"])
    message=run_git(path,"show","-s","--format=%B","HEAD")
    original={"sha":artifact.commit_sha,"commit":{"message":message}}
    assert verify_commit_binding(plan,artifact,original)["spec_hash"]==plan["spec_hash"]
    other=copy.deepcopy(plan)
    if fault in {"spec","policy"}:other[fault+"_hash"]="f"*64
    elif fault in {"run","fence","attempt"}:
        field={"run":"run_token","fence":"fencing_token","attempt":"attempt"}[fault]
        other["identity"][field]="different" if fault=="run" else 3
    elif fault=="missing":original["commit"]["message"]="old already green commit"
    elif fault=="duplicate":original["commit"]["message"]+="\n"+commit_footer(plan)
    else:original["commit"]["message"]=message.replace('"attempt":1','"attempt":true')
    with pytest.raises(EvidenceError):verify_commit_binding(other,artifact,original)

def test_missing_criterion_and_hidden_shared_contract_change_deny_before_collector(tmp_path,monkeypatch):
    task,result,plan,store,path,proof=scoped(tmp_path)
    monkeypatch.setattr("herdr.evidence.read_only_git",_real_git)
    monkeypatch.setattr("herdr.evidence.verify_invocation_session",launch_fixture)
    policy=plan["scope_policy"]
    policy["acceptance_ids"].append("second-required")
    plan["plan_hash"]=digest({k:v for k,v in plan.items() if k not in {"plan_hash","baseline"}})
    with pytest.raises(EvidenceError,match="omits frozen"):
        accept_artifact(task,result,plan,store,path,lambda *a:pytest.fail("no collector"))
    policy["acceptance_ids"].pop()
    policy.update(version=2,shared_contract_keys=["api:v1"],
        shared_contracts=[{"key":"api:v1","path":"result.txt",
                         "base_sha256":hashlib.sha256(b"before").hexdigest()}])
    plan["plan_hash"]=digest({k:v for k,v in plan.items() if k not in {"plan_hash","baseline"}})
    assert result["scope_self_check"]["shared_contract_changes"]==[]
    with pytest.raises(EvidenceError,match="changes a frozen shared"):
        accept_artifact(task,result,plan,store,path,lambda *a:pytest.fail("no collector"))
    assert not list(store.root.glob("accepted-*"))

@pytest.mark.parametrize("fault",["nan","infinity","deep","huge"])
def test_noncanonical_result_is_a_typed_permanent_rejection(fault):
    raw={"status":"completed","evidence":[{"claim":"PASS"}],"summary":"ok"}
    if fault in {"nan","infinity"}:raw["additional"]=float("nan" if fault=="nan" else "inf")
    elif fault=="huge":raw["additional"]="x"*1048577
    else:
        value=[];raw["additional"]=value
        for _ in range(17):value.append([]);value=value[0]
    with pytest.raises(EvidenceError):completion_candidate(raw)

def test_actual_closed_sdk_submission_reaches_host_control_acceptance(tmp_path):
    from tests.herdr.test_result_submission import setup
    from herdr.result_submission import submit
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"agent-stack"/"bin"))
    import agent_completion_evidence as host
    guard,result_path=setup(tmp_path)
    task={"id":guard.grant.identity.task_id,"run_token":guard.grant.identity.run_token,
        "fencing_token":guard.grant.identity.fencing_token,"attempt_id":1,"idempotency_key":"result-key",
        "repo":host.POLICY["repo"],"kind":"github_root_orchestration","workspace":str(tmp_path/"workspace"),
        "prompt":"Coordinate only"}
    root=tmp_path/"host-control"
    host.freeze_plan(root,task)
    submit(guard,{"status":"completed","summary":"Control result",
        "evidence":[{"herdr_control":{"version":1,"next_action":"Await accepted implementation"}}]})
    raw=json.loads(result_path.read_text())
    accepted=host.verify_completion(root,task,raw)
    assert accepted["level"]=="control_cycle" and accepted["integration"] is None
    assert accepted["proof"]["result_digest"]==digest(raw)
    assert host.verify_completion(root,task,raw)==accepted

def candidate(rec,evidence,checksum):
    return {"task_id":rec.id,"run_token":rec.run_token,"fencing_token":rec.fencing_token,
            "idempotency_key":rec.idempotency_key,"status":"completed",
            "artifact_sha256":checksum,"evidence":evidence,"summary":"candidate"}

@pytest.mark.parametrize("fault",["permanent","missing","unavailable","unconfigured"])
def test_permanent_child_refusal_settles_and_replays_but_transient_keeps_lease(tmp_path,fault):
    class Authority(ChildCompletionAuthority):
        def __init__(self):pass
        def verify(self,rec,payload):
            error={"permanent":EvidenceError,"missing":EvidenceMissing,"unavailable":EvidenceUnavailable}[fault]
            raise error("host evidence failure")
    scheduler,rec,lease,evidence,checksum=scheduler_fixture(tmp_path,None if fault=="unconfigured" else Authority())
    payload=candidate(rec,evidence,checksum)
    accepted=scheduler.publish_child_result(rec.id,rec.run_token,lease.agent_id,lease.fencing_token,
        rec.idempotency_key,checksum,evidence,result_payload=payload)
    if fault in {"missing","unavailable"}:
        assert not accepted and rec.lease==lease and rec.state.value=="running"
        assert not any(e["event"]=="child_result" for e in scheduler.audit_log.replay())
        return
    assert accepted and rec.state.value=="blocked" and rec.lease is None
    assert rec.completion_receipt is None and not rec.cleanup_complete
    assert rec.completion_failure["result_payload_sha256"]==digest(payload)
    replay=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"scheduler.jsonl"))
    replay.replay()
    assert replay._tasks[rec.id].completion_failure==rec.completion_failure
    events=scheduler.audit_log.replay()
    events[-1]["completion_failure"]["identity"]["fencing_token"]+=1
    log=tmp_path/"forged-rejection.jsonl"
    log.write_text("".join(json.dumps(e)+"\n" for e in events))
    with pytest.raises(SchedulerError,match="rejection"):
        DynamicChildScheduler(audit_log=AuditLog(log)).replay()

@pytest.mark.parametrize("fault",["edited","deleted","superseded"])
def test_review_comment_is_revalidated_at_final_collection(monkeypatch,fault):
    from tests.agent_stack.test_completion_collector import proof_fixture,install_transport
    import agent_completion_evidence as host
    artifact,plan,pr,checks,comment=proof_fixture()
    install_transport(monkeypatch,artifact,plan,pr,checks,comment)
    original=host.github;reads=0
    def api(path):
        nonlocal reads
        result=original(path)
        if "/issues/" in path:
            reads+=1
            if reads==2:
                if fault=="deleted":return []
                if fault=="edited":return [{**comment,"body":"Review now blocks this candidate"}]
                return [comment,{**comment,"id":comment["id"]+1,"body":"Blocking finding\n**Reviewed commit:** "+chr(96)+artifact.commit_sha+chr(96)}]
        return result
    monkeypatch.setattr(host,"github",api)
    with pytest.raises(EvidenceMissing):host.collect_github(plan,artifact,4)


def test_actual_closed_sdk_coding_candidate_reaches_child_gate_without_flat_fields(tmp_path,monkeypatch):
    # Real slot/inode, Git bytes, candidate decoder and child authority. This
    # fixture supplies host launch/GitHub ports; physical isolation has probes.
    from tests.herdr.test_child_evidence import artifact_fixture
    from tests.herdr import test_security
    from herdr.child_evidence import child_identity
    from herdr.result_submission import ResultSlot,TOOL,ARGUMENTS,submit
    from herdr.security import InvocationGuard,ToolRule,RiskClass
    rec,result,plan,store,workspace,proof=artifact_fixture(tmp_path,monkeypatch)
    result_path=tmp_path/"private-sdk-result.json";result_path.touch(mode=0o600)
    identity=child_identity(rec)
    monkeypatch.setattr(test_security,"identity",lambda:identity)
    slot=ResultSlot.bind(result_path,identity,rec.idempotency_key)
    rule=ToolRule(TOOL,RiskClass.RESULT_SUBMISSION,ARGUMENTS,
        allowed_roots=(str(tmp_path),),requires_sandbox=True,result_slot=slot)
    guard=InvocationGuard(test_security.grant(workspace,tools=(TOOL,),rules=(rule,)))
    authority=ChildCompletionAuthority(store=store,approve=lambda **kwargs:plan,collector=lambda *a:proof)
    authority.prepare(rec)
    submit(guard,{"status":"completed","summary":"Exact committed artifact",
        "evidence":[{"herdr_completion":{"version":1,
            "artifact":json.loads(json.dumps(result["artifact"])),"pr_number":result["pr_number"]}}]})
    payload=json.loads(result_path.read_text())
    assert "artifact" not in payload and "artifact_workspace" not in payload
    receipt=authority.verify(rec,payload)
    assert receipt.result_payload_sha256==digest(payload) and receipt.level=="verified_worker_result"

def test_permanent_watchdog_refusal_retries_cleanup_and_preserves_original_attempt(tmp_path,monkeypatch):
    from datetime import datetime,timezone
    from tests.agent_stack import test_watchdog_recovery as helper
    helper.configure_paths(tmp_path)
    recovery=helper.recovery
    task=helper.task(datetime.now(timezone.utc));task["kind"]="github_issue_slice"
    path=recovery.RUNNING/"task-1.json";helper.write_task(path,task)
    result={"task_id":task["id"],"run_token":task["run_token"],"status":"completed",
            "summary":"candidate","evidence":[{"claim":"PASS"}]}
    helper.write_task(recovery.RESULTS/path.name,result)
    monkeypatch.setattr(recovery,"verify_completion",
        lambda *args:(_ for _ in ()).throw(EvidenceError("frozen scope violated")))
    monkeypatch.setattr(recovery,"active_worker_tasks",lambda:set())
    calls=[]
    monkeypatch.setattr(recovery,"cleanup_task_owned_pane",lambda task:calls.append(task["run_token"]) or len(calls)>1)
    recovery.terminalize_from_result(path,task,result,0)
    blocked=recovery.BLOCKED/path.name
    first=json.loads(blocked.read_text())
    assert first["verification_resolution"]=="needs_replan_cleanup_pending"
    assert first["attempt_state"]=="delivery_uncertain" and "result_status" not in first
    recovery.reconcile_verification_pending()
    final=json.loads(blocked.read_text())
    assert calls==[task["run_token"],task["run_token"]]
    assert final["verification_resolution"]=="needs_replan" and final["attempt_state"]=="blocked"
    assert "watchdog_cleanup_blocker" not in final
    assert final["idempotency_key"]==task["idempotency_key"] and not list(recovery.DONE.iterdir())
    assert json.loads((recovery.RESULTS/path.name).read_text())==result
