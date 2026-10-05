import hashlib,json,multiprocessing,os
from dataclasses import replace
from pathlib import Path
import pytest
from herdr.child_ownership import (ChildOwnership,DecisionScope,FrozenContract,OwnershipError,
    OwnershipRegistry,WriteScope)
from herdr.security import InvocationIdentity
from herdr.scheduler import AuditLog,ChildProposal,DynamicChildScheduler,SchedulerError
from herdr.taskgraph import LifecycleState

def parent(task="root-task",consumer="github:example/repo",run="root-run",fence=9):
    return InvocationIdentity(consumer,"root-agent","coordinator","coordinator-task",task,run,fence)

def child(owner,task="child-one",run="child-run",fence=10):
    return InvocationIdentity(owner.consumer,"agent-"+task,owner.agent_id,owner.task_id,task,run,fence)

def ownership(owner,*,files=(),decisions=(),shared=(),hard=(),handoff="handoff/artifact"):
    return ChildOwnership(tuple(WriteScope("file",key) for key in files),
        tuple(decisions),tuple(hard),tuple(shared),owner.task_id,handoff)

def registry(tmp_path,**kwargs):
    tmp_path.chmod(0o700)
    return OwnershipRegistry(tmp_path,**kwargs)

def test_closed_finite_ownership_and_casefolded_ancestor_collisions():
    owner=parent()
    a=ownership(owner,files=("src/module.py",),decisions=(DecisionScope("api/schema",1,"a"*64),))
    b=ownership(owner,files=("different.py",),decisions=(DecisionScope("api/schema",2,"b"*64),))
    assert a.conflict(b)=="decision_scope_conflict"
    directory=replace(a,write_scope=(WriteScope("directory","SRC"),),decision_scope=())
    assert directory.conflict(ownership(owner,files=("src/nested/code.py",)))=="write_scope_conflict"
    assert a.hash==ChildOwnership.from_json(json.loads(json.dumps(a.to_json()))).hash
    with pytest.raises(OwnershipError):WriteScope("file","../outside")
    with pytest.raises(OwnershipError):ChildOwnership.from_json({**a.to_json(),"new_authority":True})
    with pytest.raises(OwnershipError):replace(a,write_scope=("scalar",))

def test_durable_claim_replays_without_rebinding_and_needs_host_release(tmp_path):
    store=registry(tmp_path);owner=parent();identity=child(owner)
    scope=ownership(owner,files=("src/one.py",))
    key=store.reserve(owner,identity.task_id,scope)
    restored=registry(tmp_path)
    assert restored.reserve(owner,identity.task_id,scope)==key
    restored.bind_claim(key,identity)
    assert registry(tmp_path).require_current(key,identity)
    with pytest.raises(OwnershipError,match="rebind"):
        restored.bind_claim(key,replace(identity,run_token="different"))
    with pytest.raises(OwnershipError,match="idempotency_conflict"):
        restored.reserve(owner,identity.task_id,replace(scope,handoff_ref="other-artifact"))
    with pytest.raises(OwnershipError,match="host_release"):
        restored.release(key,identity,{"model_prose":"DONE"})

def test_unknown_writers_serialize_but_parallel_reads_share_without_writes(tmp_path):
    store=registry(tmp_path);owner=parent()
    store.reserve(owner,"reader-one",None,read_only=True)
    store.reserve(owner,"reader-two",None,read_only=True)
    with pytest.raises(OwnershipError,match="unknown_serialize"):
        store.reserve(owner,"unknown-writer",None)
    with pytest.raises(OwnershipError,match="unknown_serialize"):
        store.reserve(owner,"declared-writer",ownership(owner,files=("src/one.py",)))

def test_conflicting_contract_decision_blocks_even_with_disjoint_worktrees(tmp_path):
    store=registry(tmp_path);owner=parent()
    decision=DecisionScope("shared/schema",1,"a"*64)
    store.reserve(owner,"first",ownership(owner,files=("client/api.py",),decisions=(decision,)))
    second=parent(task="other-root")
    with pytest.raises(OwnershipError,match="decision_scope_conflict"):
        store.reserve(second,"second",ownership(second,files=("server/schema.py",),decisions=(decision,)))

def test_frozen_contract_change_quarantines_existing_claim_and_candidate(tmp_path):
    owner=parent()
    verifier=lambda caller,contract,evidence:evidence=="host-frozen-evidence" and caller.task_id==owner.task_id
    store=registry(tmp_path,verify_contract=verifier)
    first=FrozenContract("shared/schema",1,"a"*64,owner.task_id)
    with pytest.raises(OwnershipError,match="host_contract"):
        registry(tmp_path).publish_contract(owner,first,"model-authority")
    store.publish_contract(owner,first,"host-frozen-evidence")
    reader=ownership(owner,shared=(first,));identity=child(owner)
    key=store.reserve(owner,identity.task_id,reader);store.bind_claim(key,identity)
    assert store.require_current(key,identity)
    second=replace(first,version=2,contract_sha256="b"*64)
    store.publish_contract(owner,second,"host-frozen-evidence")
    assert store.snapshot()["reservations"][key]["state"]=="quarantined"
    with pytest.raises(OwnershipError):store.require_current(key,identity)
    with pytest.raises(OwnershipError):store.reserve(owner,identity.task_id,reader)
    with pytest.raises(OwnershipError,match="single_owner"):
        store.publish_contract(replace(owner,run_token="new-run"),replace(second,version=3),"host-frozen-evidence")

def test_shared_contract_authority_is_scoped_to_consumer(tmp_path):
    a,b=parent(consumer="github:first/repo"),parent(consumer="github:second/repo")
    store=registry(tmp_path,verify_contract=lambda *args:True)
    refa=FrozenContract("shared/schema",1,"a"*64,a.task_id)
    refb=FrozenContract("shared/schema",1,"b"*64,b.task_id)
    store.publish_contract(a,refa,"host");store.publish_contract(b,refb,"host")
    store.reserve(a,"read-a",ownership(a,shared=(refa,)))
    store.reserve(b,"read-b",ownership(b,shared=(refb,)))
    assert len(store.snapshot()["contracts"])==2

def test_private_registry_rejects_foreign_modes_symlinks_and_directory_replacement(tmp_path):
    store=registry(tmp_path);owner=parent()
    store.reserve(owner,"child",ownership(owner))
    path=tmp_path/"child-ownership"/"registry.json";path.chmod(0o644)
    with pytest.raises(OwnershipError,match="private_file"):store.snapshot()
    path.chmod(0o600)
    lock=tmp_path/"child-ownership"/"registry.lock";lock.unlink()
    lock.symlink_to(path)
    with pytest.raises(OSError):store.snapshot()
    lock.unlink()
    original=tmp_path/"child-ownership";original.rename(tmp_path/"old-private-registry")
    original.mkdir(mode=0o700)
    with pytest.raises(OwnershipError,match="private_directory"):store.snapshot()

def _concurrent_claim(root,owner,task,ready,start,results):
    store=OwnershipRegistry(root)
    scope=ownership(owner,files=(task+".py",),decisions=(DecisionScope("api/schema",1,"a"*64),))
    ready.put(task);start.wait(10)
    try:
        store.reserve(owner,task,scope);results.put("claimed")
    except OwnershipError as exc:results.put(str(exc))

def test_actual_processes_serialize_shared_decision_before_claim(tmp_path):
    registry(tmp_path)
    context=multiprocessing.get_context("fork")
    ready,results=context.Queue(),context.Queue();start=context.Event()
    processes=[context.Process(target=_concurrent_claim,args=(tmp_path,parent(),task,ready,start,results))
        for task in ("first","second")]
    for process in processes:process.start()
    for _ in processes:ready.get(timeout=10)
    start.set()
    found=[results.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(10)
        assert process.exitcode==0
    assert sorted(found)==["claimed","decision_scope_conflict"]

def scheduler(tmp_path,owner,store):
    item=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
        ownership_registry=store,ownership_parent=owner)
    item.register_external_parent_attempt(task_id=owner.task_id,run_token=owner.run_token,
        idempotency_key="root-key",agent_name=owner.agent_id,pane_id="pane",marker="marker",
        repo=owner.consumer.removeprefix("github:"),issue="82",role="writer",
        tools=("read_file","write_file"),permissions=("workspace-write",),policy_profile="test")
    return item

def proposal(owner,scope,*,writing=True):
    return ChildProposal("writer",("read_file","write_file"),"writer" if writing else "reader",
        ("write_file",) if writing else ("read_file",),child_task="Bounded work",
        parent_permissions=("workspace-write",),child_permissions=("workspace-write",) if writing else (),
        ownership=scope)

def test_scheduler_retains_ownership_in_claim_and_replay_before_delivery(tmp_path):
    owner=parent();store=registry(tmp_path);item=scheduler(tmp_path,owner,store)
    scope=ownership(owner,files=("src/one.py",))
    node=item.delegate_child(owner.task_id,owner.run_token,"one",proposal(owner,scope))
    lease,=item.dispatch(task_ids={node.id},managed_start=True)
    rec=item._tasks[node.id]
    assert rec.ownership==scope and rec.ownership_reservation
    identity=InvocationIdentity(owner.consumer,rec.agent_id,owner.agent_id,owner.task_id,
        rec.id,rec.run_token,rec.fencing_token)
    assert store.require_current(rec.ownership_reservation,identity)
    restored=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
        ownership_registry=store,ownership_parent=owner)
    restored.replay()
    assert restored._tasks[node.id].ownership==scope
    assert restored._tasks[node.id].ownership_reservation==rec.ownership_reservation
    assert restored.dispatch(task_ids={node.id},managed_start=True)==[]
    with pytest.raises(SchedulerError,match="different identity"):
        restored.delegate_child(owner.task_id,owner.run_token,"one",
            proposal(owner,replace(scope,handoff_ref="changed")))

def test_scheduler_blocks_conflicting_decisions_before_another_claim(tmp_path):
    owner=parent();store=registry(tmp_path);item=scheduler(tmp_path,owner,store)
    decision=DecisionScope("api/schema",1,"a"*64)
    first=item.delegate_child(owner.task_id,owner.run_token,"one",proposal(owner,
        ownership(owner,files=("one.py",),decisions=(decision,))))
    second=item.delegate_child(owner.task_id,owner.run_token,"two",proposal(owner,
        ownership(owner,files=("two.py",),decisions=(decision,))))
    assert len(item.dispatch(managed_start=True))==1
    assert sum(rec.state is LifecycleState.RUNNING for rec in item._tasks.values()
        if rec.parent_task_id is not None)==1
    pending=next(rec for rec in item._tasks.values() if rec.parent_task_id is not None and rec.state is LifecycleState.PENDING)
    assert pending.blocker=="decision_scope_conflict" and pending.run_token is None

def test_scheduler_invalidates_publication_after_frozen_input_changes(tmp_path):
    owner=parent();store=registry(tmp_path,verify_contract=lambda *args:True)
    first=FrozenContract("api/schema",1,"a"*64,owner.task_id)
    store.publish_contract(owner,first,"host")
    item=scheduler(tmp_path,owner,store)
    node=item.delegate_child(owner.task_id,owner.run_token,"one",
        proposal(owner,ownership(owner,shared=(first,)),writing=False))
    item.dispatch(task_ids={node.id},managed_start=True);rec=item._tasks[node.id]
    store.publish_contract(owner,replace(first,version=2,contract_sha256="b"*64),"host")
    evidence=[{"artifact":"handoff"}];sha=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    assert not item.publish_child_result(rec.id,rec.run_token,rec.agent_id,rec.fencing_token,
        rec.idempotency_key,sha,evidence)
    assert rec.state is LifecycleState.RUNNING and rec.result_evidence_canonical is None

def test_failed_registry_write_leaves_no_private_temporary_or_false_claim(tmp_path,monkeypatch):
    import os
    store=registry(tmp_path);owner=parent()
    def fail(*_):raise OSError("injected disk failure")
    with monkeypatch.context() as fault:
        fault.setattr(os,"write",fail)
        with pytest.raises(OSError,match="disk failure"):
            store.reserve(owner,"child",ownership(owner))
    assert list(store.directory.glob(".registry-*"))==[]
    assert store.snapshot()["reservations"]=={}
    assert store.reserve(owner,"child",ownership(owner))
