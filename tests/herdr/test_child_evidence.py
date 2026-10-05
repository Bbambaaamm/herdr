"""No lifecycle doubles: child artifacts must pass the shared semantic gate."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest
from herdr.child_evidence import (AcceptedChildReceipt,ChildCompletionAuthority,child_identity,
                                  child_task,child_spec)
from herdr.evidence import (EvidenceError,EvidenceMissing,binding,digest)
from herdr.scheduler import AuditLog,ChildProposal,DynamicChildScheduler,SchedulerError
from tests.herdr.test_evidence import fixture,launch_fixture
from herdr.workspace import _real_git

def artifact_fixture(tmp_path,monkeypatch):
    task,result,plan,store,path,proof=fixture(tmp_path)
    node=SimpleNamespace(id="task",objective="bounded repair",role="writer",
        tools=("write_file",),permissions=("workspace-write",))
    info=path.stat()
    rec=SimpleNamespace(node=node,run_token="run",idempotency_key="a"*64,attempts=1,
        fencing_token=2,repo="Bbambaaamm/herdr",issue="85",parent_task_id="parent",
        parent_agent_id="parent-agent",agent_id="worker",execution_agent="worker",
        execution_pane="pane",execution_marker="marker",execution_sandbox_verified=True,
        execution_sandbox_attestation={},worktree_identity=f"{path}|{info.st_dev}:{info.st_ino}",
        ownership=None,owned_write_mounts=None)
    plan["identity"]=binding(child_task(rec))
    plan["spec_hash"]=child_spec(rec)
    plan["plan_hash"]=digest({k:v for k,v in plan.items() if k not in {"plan_hash","baseline"}})
    result.update(artifact_workspace=str(path))
    monkeypatch.setattr("herdr.evidence.read_only_git",_real_git)
    monkeypatch.setattr("herdr.evidence.verify_invocation_session",launch_fixture)
    return rec,result,plan,store,path,proof

def test_child_semantic_gate_uses_exact_real_artifact_and_replays_after_cleanup(tmp_path,monkeypatch):
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    calls=[]
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,
        collector=lambda *args:calls.append(args) or proof)
    authority.prepare(rec)
    receipt=authority.verify(rec,result)
    receipt.validate(rec,digest(result))
    assert receipt.level=="verified_worker_result" and len(calls)==1
    shutil.rmtree(path)
    assert authority.verify(rec,result)==receipt and len(calls)==1

def test_worker_claimed_producer_and_hash_do_not_create_verified_child(tmp_path,monkeypatch):
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    result["evidence"]=[{"producer":"trusted-ci","passed":True,"review":"PASS"}]
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,
        collector=lambda *a:(_ for _ in ()).throw(EvidenceMissing("exact head review pending")))
    authority.prepare(rec)
    with pytest.raises(EvidenceMissing):
        authority.verify(rec,result)
    assert not list(store.root.glob("accepted-*"))

def test_child_artifact_from_replaced_pinned_worktree_is_rejected(tmp_path,monkeypatch):
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,
        collector=lambda *a:pytest.fail("replaced workspace must not collect evidence"))
    authority.prepare(rec)
    old=path.with_name("original")
    path.rename(old)
    shutil.copytree(old,path)
    with pytest.raises(EvidenceError,match="replaced"):
        authority.verify(rec,result)

def test_child_checkbox_only_sandbox_proof_never_publishes_semantic_receipt(tmp_path,monkeypatch):
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    monkeypatch.undo()
    monkeypatch.setattr("herdr.evidence.read_only_git",_real_git)
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,
        collector=lambda *a:pytest.fail("missing physical proof must precede collector"))
    authority.prepare(rec)
    with pytest.raises(EvidenceError,match="sealed physical"):
        authority.verify(rec,result)

def test_changed_child_specification_does_not_reuse_old_plan(tmp_path,monkeypatch):
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,collector=lambda *a:proof)
    authority.prepare(rec)
    rec.node.objective="another task"
    with pytest.raises(EvidenceError,match="specification"):
        authority.verify(rec,result)

def scheduler_fixture(tmp_path,authority=None):
    scheduler=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"scheduler.jsonl"),completion_authority=authority)
    scheduler.register_external_parent_attempt(task_id="parent",run_token="parent-run",idempotency_key="parent-key",
        agent_name="parent-agent",pane_id="parent-pane",marker="parent-marker",repo="org/repo",
        issue="85",role="writer",tools=("read_file",),permissions=(),policy_profile="default")
    child=scheduler.delegate_child("parent","parent-run","key",
        ChildProposal("writer",("read_file",),"reader",("read_file",),child_task="inspect"))
    lease=scheduler.dispatch(task_ids={child.id})[0]
    rec=scheduler._tasks[child.id]
    evidence=[{"producer":"model","passed":True}]
    checksum=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    return scheduler,rec,lease,evidence,checksum

def test_scheduler_denies_unverified_completed_child_without_releasing_lease(tmp_path):
    scheduler,rec,lease,evidence,checksum=scheduler_fixture(tmp_path)
    assert not scheduler.publish_child_result(rec.id,rec.run_token,lease.agent_id,lease.fencing_token,
        rec.idempotency_key,checksum,evidence,result_payload={"evidence":evidence,"passed":True})
    assert rec.state.value=="running" and rec.lease==lease and rec.completion_receipt is None
    assert not any(x["event"]=="child_result" for x in scheduler.audit_log.replay())

def test_blocked_child_can_report_bounded_failure_without_claiming_verified_result(tmp_path):
    scheduler,rec,lease,evidence,checksum=scheduler_fixture(tmp_path)
    assert scheduler.publish_child_result(rec.id,rec.run_token,lease.agent_id,lease.fencing_token,
        rec.idempotency_key,checksum,evidence,status="blocked")
    assert rec.state.value=="blocked" and rec.completion_receipt is None

def test_replay_rejects_forged_receipt_and_missing_modern_semantic_evidence(tmp_path):
    class Authority(ChildCompletionAuthority):
        def __init__(self): pass
        def verify(self,rec,payload):
            return AcceptedChildReceipt(2,child_identity(rec).to_json(),digest(payload),"a"*64,
                "b"*64,child_spec(rec),"c"*64,"verified_worker_result")
    scheduler,rec,lease,evidence,checksum=scheduler_fixture(tmp_path,Authority())
    payload={"artifact":"host approved reference"}
    assert scheduler.publish_child_result(rec.id,rec.run_token,lease.agent_id,lease.fencing_token,
        rec.idempotency_key,checksum,evidence,result_payload=payload)
    assert rec.completion_receipt["result_payload_sha256"]==digest(payload)
    events=scheduler.audit_log.replay()
    for mutate in ("missing","identity","spec"):
        changed=json.loads(json.dumps(events))
        last=changed[-1]
        if mutate=="missing": last.pop("completion_receipt")
        elif mutate=="identity": last["completion_receipt"]["identity"]["run_token"]="other-run"
        else: last["completion_receipt"]["spec_sha256"]="f"*64
        log=tmp_path/("forged-"+mutate+".jsonl")
        log.write_text("".join(json.dumps(x)+"\n" for x in changed))
        with pytest.raises(SchedulerError,match="receipt"):
            DynamicChildScheduler(audit_log=AuditLog(log)).replay()


def test_historical_self_claimed_done_is_readable_but_not_promoted_to_verified(tmp_path):
    class Authority(ChildCompletionAuthority):
        def __init__(self): pass
        def verify(self,rec,payload):
            return AcceptedChildReceipt(2,child_identity(rec).to_json(),digest(payload),"a"*64,
                "b"*64,child_spec(rec),"c"*64,"verified_worker_result")
    scheduler,rec,lease,evidence,checksum=scheduler_fixture(tmp_path,Authority())
    assert scheduler.publish_child_result(rec.id,rec.run_token,lease.agent_id,lease.fencing_token,
        rec.idempotency_key,checksum,evidence,result_payload={})
    events=scheduler.audit_log.replay()
    for event in events:
        event.pop("completion_contract_version",None)
        event.pop("completion_receipt",None)
    log=tmp_path/"historical.jsonl"
    log.write_text("".join(json.dumps(x)+"\n" for x in events))
    replay=DynamicChildScheduler(audit_log=AuditLog(log))
    replay.replay()
    child=replay._tasks[rec.id]
    assert child.state.value=="done" and child.completion_receipt is None
    row=next(x for x in replay.snapshot()["tasks"] if x["task_id"]==rec.id)
    assert row["completion_level"]=="legacy_unverified_result"

def test_accepted_terminal_child_cannot_replay_modified_result_payload(tmp_path):
    class Authority(ChildCompletionAuthority):
        def __init__(self): pass
        def verify(self,rec,payload):
            return AcceptedChildReceipt(2,child_identity(rec).to_json(),digest(payload),"a"*64,
                "b"*64,child_spec(rec),"c"*64,"verified_worker_result")
    scheduler,rec,lease,evidence,checksum=scheduler_fixture(tmp_path,Authority())
    result={"task_id":rec.id,"run_token":rec.run_token,"fencing_token":lease.fencing_token,
        "idempotency_key":rec.idempotency_key,"status":"completed","evidence":evidence,
        "artifact_sha256":checksum,"artifact":{"commit_sha":"a"*40}}
    assert scheduler.publish_child_result(rec.id,rec.run_token,lease.agent_id,lease.fencing_token,
        rec.idempotency_key,checksum,evidence,result_payload=result)
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"agent-stack/bin"))
    from agent_durable_children import publish_exact_child_result
    path=tmp_path/"child.result.json"
    path.write_text(json.dumps(result))
    assert publish_exact_child_result(scheduler,rec,path)=="completed"
    result["artifact"]["commit_sha"]="b"*40
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError,match="accepted semantic receipt"):
        publish_exact_child_result(scheduler,rec,path)

def test_child_crash_after_acceptance_cannot_change_payload_before_scheduler_receipt(tmp_path,monkeypatch):
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,collector=lambda *a:proof)
    authority.prepare(rec)
    original=authority.verify(rec,result)
    # Accepted evidence is durable, but the scheduler's child_result event was not appended.
    recreated=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,
        collector=lambda *a:pytest.fail("immutable accepted receipt must be reused"))
    result["worker_summary"]="changed after acceptance"
    with pytest.raises(EvidenceError,match="payload changed"):
        recreated.verify(rec,result)
    result.pop("worker_summary")
    assert recreated.verify(rec,result)==original


def test_owned_child_specification_invalidates_old_semantic_plan(tmp_path,monkeypatch):
    from herdr.child_ownership import ChildOwnership,WriteScope,FrozenContract
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    rec.ownership=ChildOwnership((WriteScope("file","result.txt"),),(),(),
        (FrozenContract("api",1,"d"*64,rec.parent_task_id),),rec.parent_task_id,"artifact://handoff/task")
    original_spec=child_spec(rec)
    plan["spec_hash"]=original_spec
    plan["plan_hash"]=digest({k:v for k,v in plan.items() if k not in {"plan_hash","baseline"}})
    authority=ChildCompletionAuthority(store=store,approve=lambda **kwargs:plan,collector=lambda *a:proof)
    authority.prepare(rec)
    receipt=authority.verify(rec,result)
    assert receipt.spec_sha256==original_spec
    rec.ownership=replace(rec.ownership,write_scope=(WriteScope("file","other.txt"),))
    with pytest.raises(EvidenceError,match="specification changed"):authority.verify(rec,result)
    with pytest.raises(EvidenceError,match="binding"):receipt.validate(rec)


def test_parent_barrier_replays_registry_and_rejects_stale_accepted_child(tmp_path):
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"agent-stack/bin"))
    from agent_durable_children import (ensure_attempt_directory,initialize_parent_scheduler,
        all_children_terminal,replay_host_scheduler)
    from herdr.child_ownership import OwnershipRegistry,FrozenContract
    from tests.herdr.test_child_ownership import parent,ownership,proposal
    tmp_path.chmod(0o700)
    owner=parent()
    store=OwnershipRegistry(tmp_path,verify_contract=lambda *args:True)
    contract=FrozenContract("api",1,"a"*64,owner.task_id)
    store.publish_contract(owner,contract,"host fixture")
    class Authority(ChildCompletionAuthority):
        # Semantic-port fixture for the actual durable barrier/registry path.
        # Shared acceptance with real committed Git artifacts is tested above.
        def __init__(self):pass
        def verify(self,rec,payload):
            return AcceptedChildReceipt(2,child_identity(rec).to_json(),digest(payload),
                "b"*64,"c"*64,child_spec(rec),"d"*64,"verified_worker_result")
    authority=Authority()
    directory=ensure_attempt_directory(tmp_path,owner.task_id,owner.run_token)
    item=initialize_parent_scheduler(directory,completion_authority=authority,
        ownership_registry=store,ownership_parent=owner,task_id=owner.task_id,
        run_token=owner.run_token,idempotency_key="root-key",agent_name=owner.agent_id,
        pane_id="parent-pane",marker="marker",repo=owner.consumer.removeprefix("github:"),
        issue="85",role="writer",tools=("read_file","write_file"),permissions=("workspace-write",),
        policy_profile="test")
    assert item.completion_authority is authority and item.ownership_registry is store
    node=item.delegate_child(owner.task_id,owner.run_token,"scoped-reader",
        proposal(owner,ownership(owner,shared=(contract,)),writing=False))
    item.dispatch(task_ids={node.id},managed_start=True)
    rec=item._tasks[node.id]
    payload={"fixture":"trusted host port only"};evidence=[{"artifact":"fixture"}]
    evidence_hash=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    assert item.publish_child_result(rec.id,rec.run_token,rec.agent_id,rec.fencing_token,
        rec.idempotency_key,evidence_hash,evidence,result_payload=payload)
    assert all_children_terminal(tmp_path,owner.task_id,owner.run_token)
    accepted_identity=child_identity(rec)
    raw=(directory/"scheduler.jsonl").read_bytes()
    restored=replay_host_scheduler(tmp_path,directory/"scheduler.jsonl")
    assert restored.ownership_parent==owner
    assert restored._tasks[node.id].run_token==accepted_identity.run_token
    store.publish_contract(owner,replace(contract,version=2,contract_sha256="e"*64),"host fixture")
    assert not all_children_terminal(tmp_path,owner.task_id,owner.run_token)
    assert (directory/"scheduler.jsonl").read_bytes()==raw
    assert store.snapshot()["reservations"][rec.ownership_reservation]["state"]=="quarantined"

def test_protected_accepted_handoff_keeps_candidate_history_and_requires_cleanup(tmp_path,monkeypatch):
    from herdr.handoff import HandoffEnvelope
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    rec.id=rec.node.id
    rec.policy_profile="default"
    rec.namespace_lifetime=None
    evidence=[{"report":"candidate","handoff_details":{"out_of_scope":["deployment"]}}]
    result["evidence"]=evidence
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,collector=lambda *a:proof)
    authority.prepare(rec)
    rec.completion_receipt=authority.verify(rec,result).to_json()
    rec.result_status="completed"
    rec.result_artifact_sha256=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    rec.result_handoff=HandoffEnvelope.submitted_child(rec,evidence=evidence).to_json()
    candidate=json.loads(json.dumps(rec.result_handoff))
    rec.cleanup_complete=False
    assert authority.accepted_handoff(rec) is None
    rec.cleanup_complete=True
    projected=authority.accepted_handoff(rec)
    assert projected["current_state"]=="COMPLETE" and projected["out_of_scope"]==["deployment"]
    assert projected["next_action"]=="parent_synthesis_and_integration"
    assert projected["base_sha256"]==digest({"git_commit":plan["base_sha"]})
    assert any(ref["ref"]=="accepted-bundle:"+rec.completion_receipt["bundle_sha256"]
               for ref in projected["evidence_refs"])
    assert rec.result_handoff==candidate and candidate["current_state"]=="UNKNOWN"
    rec.node.objective="another specification"
    with pytest.raises(EvidenceError):authority.accepted_handoff(rec)
