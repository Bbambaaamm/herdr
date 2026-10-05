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


def inventory_ledger(tmp_path, scope, *, writing=True, claimed=True):
    directory=tmp_path/"durable-children"/("0"*64)
    directory.mkdir(mode=0o700,parents=True)
    directory.parent.chmod(0o700)
    owner=parent()
    store=registry(tmp_path)
    item=scheduler(directory,owner,store)
    node=item.delegate_child(owner.task_id,owner.run_token,"inventory-child",
                             proposal(owner,scope,writing=writing))
    if claimed:
        assert len(item.dispatch(task_ids={node.id},managed_start=True))==1
    item.audit_log.flush()
    (directory/"graph.jsonl").rename(directory/"scheduler.jsonl")
    return directory,store,item,node


@pytest.mark.parametrize("claimed",[False,True])
def test_host_inventory_quarantines_unknown_legacy_writers_even_before_claim(tmp_path,claimed):
    from herdr.ownership_inventory import LegacyOwnershipInventory
    _,store,item,node=inventory_ledger(tmp_path,None,claimed=claimed)
    inventory=LegacyOwnershipInventory(tmp_path)
    assert inventory(store.snapshot()) is False
    other=parent(task="another-parent")
    guarded=OwnershipRegistry(tmp_path,verify_legacy=inventory)
    with pytest.raises(OwnershipError,match="legacy_writer_quarantined"):
        guarded.reserve(other,"new-child",ownership(other,files=("different.py",)))
    assert item._tasks[node.id].run_token is not None if claimed else item._tasks[node.id].run_token is None


def test_inventory_matches_actual_full_claim_and_rejects_forged_registry_identity(tmp_path):
    from herdr.ownership_inventory import LegacyOwnershipInventory
    directory,store,item,node=inventory_ledger(tmp_path,ownership(parent(),files=("owned.py",)))
    inventory=LegacyOwnershipInventory(tmp_path)
    data=store.snapshot()
    assert inventory(data) is True
    row=next(iter(data["reservations"].values()))
    row["identity"]["run_token"]="foreign-run"
    assert inventory(data) is False
    # A model result and cleanup observation cannot substitute for the claim.
    row["state"]="released"
    assert inventory(data) is False


def test_inventory_allows_only_explicit_read_tools_without_registry_metadata(tmp_path):
    from herdr.ownership_inventory import LegacyOwnershipInventory
    _,store,_,_=inventory_ledger(tmp_path,None,writing=False)
    assert LegacyOwnershipInventory(tmp_path)(store.snapshot()) is True


@pytest.mark.parametrize("fault",["symlink","hardlink","writable","missing_required","duplicate_key","corrupt"])
def test_host_inventory_rejects_unsafe_or_corrupt_canonical_ledgers(tmp_path,fault):
    from herdr.ownership_inventory import LegacyOwnershipInventory
    directory,store,_,_=inventory_ledger(tmp_path,ownership(parent(),files=("owned.py",)))
    path=directory/"scheduler.jsonl"
    if fault=="symlink":
        path.rename(directory/"saved-ledger");path.symlink_to(directory/"saved-ledger")
    elif fault=="hardlink":
        os.link(path,directory/"extra-link")
    elif fault=="writable":
        path.chmod(0o666)
    elif fault=="missing_required":
        path.unlink();(directory/"scheduler.required").write_text("")
    elif fault=="duplicate_key":
        path.write_text('{"event":"submit","event":"claim"}\n')
    else:
        path.write_text("{partial")
    with pytest.raises(OwnershipError):
        LegacyOwnershipInventory(tmp_path)(store.snapshot())


def test_actual_owned_inode_observation_replays_and_cannot_rebind(tmp_path):
    from contextlib import closing
    from herdr.owned_write_mounts import OwnedWritePins
    from tests.herdr.test_host_policy_launch import sandbox_module
    sandbox=sandbox_module()
    workspace=tmp_path/"worktree";workspace.mkdir()
    (workspace/"owned.py").write_text("original")
    fd=os.open(workspace,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW)
    info=os.fstat(fd)
    pin=sandbox.PinnedWorktree(workspace,fd,info.st_dev,info.st_ino,tmp_path)
    owner=parent();store=registry(tmp_path);item=scheduler(tmp_path,owner,store)
    scope=ownership(owner,files=("owned.py",))
    candidate=replace(proposal(owner,scope),worktree_identity=pin.identity)
    node=item.delegate_child(owner.task_id,owner.run_token,"pins",candidate)
    item.dispatch(task_ids={node.id},managed_start=True)
    try:
        with OwnedWritePins(scope,pin) as pins:
            item.bind_owned_write_mounts(node.id,pins)
            expected=pins.evidence()
            item.bind_owned_write_mounts(node.id,pins)
        rec=item._tasks[node.id]
        assert rec.owned_write_mounts==tuple(expected)
        snapshot=next(x for x in item.snapshot()["tasks"] if x["task_id"]==node.id)
        assert snapshot["owned_write_mounts"]==expected and snapshot["ownership_sha256"]==scope.hash
        restored=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
            ownership_registry=store,ownership_parent=owner)
        restored.replay()
        assert restored._tasks[node.id].owned_write_mounts==tuple(expected)
        events=item.audit_log.replay()
        bad=dict(events[-1]);bad["mounts"]=[{**expected[0],"inode":expected[0]["inode"]+1}]
        item.audit_log.append(bad);item.audit_log.flush()
        fresh=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
            ownership_registry=store,ownership_parent=owner)
        with pytest.raises(SchedulerError,match="owned mount replay changed"):
            fresh.replay()
    finally:
        pin.close()


def test_owned_mount_evidence_cannot_omit_add_or_mistype_declared_inode():
    from herdr.owned_write_mounts import validate_owned_mount_evidence
    scope=ownership(parent(),files=("src/owned.py",))
    good=[{"key":"src/owned.py","kind":"file","device":1,"inode":2}]
    assert validate_owned_mount_evidence(scope,good)==tuple(good)
    for bad in [[],[{**good[0],"key":"src/foreign.py"}],
                [{**good[0],"inode":True}],[good[0],good[0]],[{**good[0],"fd":3}]]:
        with pytest.raises(OwnershipError):
            validate_owned_mount_evidence(scope,bad)


@pytest.mark.parametrize("already_bound",[False,True])
def test_cold_replay_recovers_crash_after_claim_flush_without_redelivery(tmp_path,monkeypatch,already_bound):
    owner=parent();store=registry(tmp_path);item=scheduler(tmp_path,owner,store)
    scope=ownership(owner,files=("src/one.py",))
    node=item.delegate_child(owner.task_id,owner.run_token,"recover-bind",proposal(owner,scope))
    original=store.bind_claim
    def interrupted(key,identity):
        if already_bound:original(key,identity)
        raise OSError("crash after durable claim flush")
    with monkeypatch.context() as fault:
        fault.setattr(store,"bind_claim",interrupted)
        with pytest.raises(OSError,match="durable claim"):
            item.dispatch(task_ids={node.id},managed_start=True)
    rec=item._tasks[node.id]
    raw=(tmp_path/"graph.jsonl").read_bytes()
    restored=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
        ownership_registry=store,ownership_parent=owner)
    restored.replay()
    identity=InvocationIdentity(owner.consumer,rec.agent_id,owner.agent_id,owner.task_id,
        rec.id,rec.run_token,rec.fencing_token)
    assert store.require_current(rec.ownership_reservation,identity)
    assert restored._tasks[node.id].run_token==rec.run_token
    assert restored.dispatch(task_ids={node.id},managed_start=True)==[]
    assert (tmp_path/"graph.jsonl").read_bytes()==raw
    # Repeating cold replay on a fresh process retains the same single claim.
    second=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
        ownership_registry=store,ownership_parent=owner)
    second.replay()
    assert second._tasks[node.id].run_token==rec.run_token
    assert store.snapshot()["reservations"][rec.ownership_reservation]["identity"]==identity.to_json()


def test_recovered_claim_stays_quarantined_when_frozen_contract_changed(tmp_path,monkeypatch):
    owner=parent();store=registry(tmp_path,verify_contract=lambda *args:True)
    old=FrozenContract("api/schema",1,"a"*64,owner.task_id)
    store.publish_contract(owner,old,"host")
    item=scheduler(tmp_path,owner,store)
    scope=ownership(owner,shared=(old,),files=("one.py",))
    node=item.delegate_child(owner.task_id,owner.run_token,"stale-bind",proposal(owner,scope))
    with monkeypatch.context() as fault:
        fault.setattr(store,"bind_claim",lambda *args:(_ for _ in ()).throw(OSError("crash")))
        with pytest.raises(OSError):item.dispatch(task_ids={node.id},managed_start=True)
    store.publish_contract(owner,replace(old,version=2,contract_sha256="b"*64),"host")
    restored=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
        ownership_registry=store,ownership_parent=owner)
    restored.replay()
    rec=restored._tasks[node.id]
    row=store.snapshot()["reservations"][rec.ownership_reservation]
    assert row["state"]=="quarantined" and row["identity"]["run_token"]==rec.run_token
    with pytest.raises(OwnershipError):restored._require_current_ownership(rec)
    assert restored.dispatch(task_ids={node.id},managed_start=True)==[]


def test_claim_replay_never_adopts_modified_global_reservation(tmp_path,monkeypatch):
    owner=parent();store=registry(tmp_path);item=scheduler(tmp_path,owner,store)
    node=item.delegate_child(owner.task_id,owner.run_token,"bad-bind",
        proposal(owner,ownership(owner,files=("one.py",))))
    with monkeypatch.context() as fault:
        fault.setattr(store,"bind_claim",lambda *args:(_ for _ in ()).throw(OSError("crash")))
        with pytest.raises(OSError):item.dispatch(task_ids={node.id},managed_start=True)
    rec=item._tasks[node.id]
    with store._transaction() as data:
        data["reservations"][rec.ownership_reservation]["ownership"]["handoff_ref"]="different"
    restored=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"),
        ownership_registry=store,ownership_parent=owner)
    with pytest.raises(OwnershipError,match="replay_reservation"):restored.replay()


def test_owned_late_result_without_registry_cannot_become_terminal(tmp_path):
    owner=parent();store=registry(tmp_path);item=scheduler(tmp_path,owner,store)
    node=item.delegate_child(owner.task_id,owner.run_token,"unbound-late",
        proposal(owner,ownership(owner,files=("one.py",))))
    item.dispatch(task_ids={node.id},managed_start=True);rec=item._tasks[node.id]
    raw=(tmp_path/"graph.jsonl").read_bytes()
    no_registry=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"graph.jsonl"))
    no_registry.replay()
    result=[{"artifact":"candidate"}]
    hashed=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    assert not no_registry.publish_child_result(rec.id,rec.run_token,rec.agent_id,
        rec.fencing_token,rec.idempotency_key,hashed,result)
    assert no_registry._tasks[rec.id].state is LifecycleState.RUNNING
    assert (tmp_path/"graph.jsonl").read_bytes()==raw


def test_protected_recovery_restores_full_registry_parent_binding(tmp_path):
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"agent-stack/bin"))
    from agent_durable_children import replay_host_scheduler
    owner=parent();store=registry(tmp_path);item=scheduler(tmp_path,owner,store)
    node=item.delegate_child(owner.task_id,owner.run_token,"recover-registry",
        proposal(owner,ownership(owner,files=("one.py",))))
    item.dispatch(task_ids={node.id},managed_start=True);rec=item._tasks[node.id]
    restored=replay_host_scheduler(tmp_path,tmp_path/"graph.jsonl")
    assert restored.ownership_parent==owner and restored.ownership_registry is not None
    identity=InvocationIdentity(owner.consumer,rec.agent_id,owner.agent_id,owner.task_id,
        rec.id,rec.run_token,rec.fencing_token)
    assert restored.ownership_registry.require_current(rec.ownership_reservation,identity)
    assert restored.dispatch(task_ids={node.id},managed_start=True)==[]


@pytest.mark.parametrize("replacement", ["none", "inode", "symlink", "ancestor_symlink"])
def test_owned_pre_delivery_recovery_reopens_exact_durable_worktree(tmp_path, monkeypatch, replacement):
    import sys
    from importlib.machinery import SourceFileLoader
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent-stack/bin"))
    import agent_durable_children as recovery
    from herdr.runtime import AdmissionRegistry, CommandResult, HerdrChildRuntime
    from herdr import policy_launch, owned_write_mounts

    owner = parent()
    store = registry(tmp_path)
    directory = recovery.ensure_attempt_directory(tmp_path, owner.task_id, owner.run_token)
    item = scheduler(directory, owner, store)
    work_parent = tmp_path / "worktrees"
    workspace = work_parent / "child"
    workspace.mkdir(parents=True)
    target = workspace / "owned.py"
    target.write_text("original")
    info = workspace.stat()
    identity = f"{workspace}|{info.st_dev}:{info.st_ino}"
    scope = ownership(owner, files=("owned.py",))
    node = item.delegate_child(owner.task_id, owner.run_token, "interrupted-owned",
        replace(proposal(owner, scope), worktree_identity=identity))
    item.dispatch(task_ids={node.id}, managed_start=True)
    rec = item._tasks[node.id]
    item.bind_child_prompt(node.id, "bounded work")
    marker = f"child-{rec.run_token}"
    assert item.record_child_pane_intent(rec.id, rec.run_token, rec.agent_id,
        rec.fencing_token, rec.idempotency_key, marker)
    assert item.bind_pre_delivery_pane(rec.id, rec.run_token, rec.agent_id, "owned-pane", marker)
    fd = os.open(workspace, os.O_PATH | os.O_DIRECTORY)
    from agent_durable_sandbox import PinnedWorktree
    pin = PinnedWorktree(workspace, fd, info.st_dev, info.st_ino)
    try:
        with owned_write_mounts.OwnedWritePins(scope, pin) as pins:
            item.bind_owned_write_mounts(rec.id, pins)
    finally:
        pin.close()
    assert item.attest_execution_sandbox(rec.id, rec.run_token, rec.agent_id, "owned-pane", marker,
        sandbox_pid=321, policy_sha256="a"*64)
    item.mark_pre_delivery_agent_start(rec.id)
    (directory / "graph.jsonl").rename(directory / "scheduler.jsonl")
    recovery.mark_ledger_required(directory)

    if replacement in {"inode", "symlink"}:
        workspace.rename(work_parent / "retained")
        if replacement == "inode":
            workspace.mkdir()
        else:
            workspace.symlink_to(work_parent / "retained", target_is_directory=True)
    elif replacement == "ancestor_symlink":
        work_parent.rename(tmp_path / "retained-parent")
        work_parent.symlink_to(tmp_path / "retained-parent", target_is_directory=True)
    closed, verified, pins_seen = [], [], []
    class Runner:
        def run(self, args, timeout_seconds=30):
            if args[:2] == ["pane", "list"]:
                return CommandResult(0, '{"result":{"panes":[{"pane_id":"owned-pane"}]}}', "")
            if args[:2] == ["agent", "get"]:
                return CommandResult(1, '{"error":{"code":"agent_not_found"}}', "")
            if args[:2] == ["pane", "process-info"]:
                return CommandResult(0, '{"result":{"process_info":{"shell_pid":123}}}', "")
            if args[:2] == ["pane", "close"]:
                closed.append(args[2])
                return CommandResult(0, "{}", "")
            raise AssertionError(args)
    runner = Runner()
    monkeypatch.setattr(recovery, "SubprocessHerdrRunner", lambda *a: runner)
    monkeypatch.setattr(recovery, "AdmissionRegistry",
                        lambda: AdmissionRegistry(tmp_path / "admission.json"))
    original_runtime = recovery.HerdrChildRuntime
    def runtime(*args, **kwargs):
        retained = kwargs["pinned_worktree"]
        retained.verify()
        pins_seen.append(retained.fd)
        assert retained.identity == identity
        from tests.policy_launch_fakes import FakeHostPolicyLaunchFactory
        kwargs["policy_launch_factory"] = FakeHostPolicyLaunchFactory()
        return original_runtime(*args, **kwargs)
    monkeypatch.setattr(recovery, "HerdrChildRuntime", runtime)
    monkeypatch.setattr(HerdrChildRuntime, "_verify_created_pane_marker", lambda *a: None)
    original_load = SourceFileLoader.exec_module
    def load(loader, module):
        if loader.name == "agent_durable_sandbox_verify":
            module.inner_pid = lambda process, supplied: 321
        else:
            original_load(loader, module)
    monkeypatch.setattr(SourceFileLoader, "exec_module", load)
    def retained_policy(proof, *, identity: object, pid, attestation, require_bootstrap, **kw):
        assert identity.task_id == rec.id and pid == 321 and not require_bootstrap
    monkeypatch.setattr(policy_launch, "verify_retained_policy_evidence", retained_policy)
    monkeypatch.setattr(policy_launch, "mount_rows", lambda pid: [])
    def verify_mounts(logical, rows, pid, mounts):
        assert logical == workspace and pid == 321
        actual = target.stat()
        assert rows[0]["device"] == actual.st_dev and rows[0]["inode"] == actual.st_ino
        verified.append(logical)
    monkeypatch.setattr(owned_write_mounts, "verify_owned_mount_evidence", verify_mounts)

    recovery.reconcile_child_results(tmp_path, owner.task_id, owner.run_token)
    restored = recovery.replay_host_scheduler(tmp_path, directory / "scheduler.jsonl")
    recovered = restored._tasks[rec.id]
    if replacement == "none":
        assert closed == ["owned-pane"] and verified == [workspace]
        assert recovered.cleanup_complete and recovered.pre_delivery_failure
        # This retained-pin transport test deliberately stubs physical proofs.
        # It must not open acceptance without a real namespace lifetime.
        assert not recovery.all_children_terminal(tmp_path, owner.task_id, owner.run_token)
        for descriptor in pins_seen:
            with pytest.raises(OSError):
                os.fstat(descriptor)
    else:
        assert not closed and not verified and not pins_seen
        assert not recovered.cleanup_complete
        assert not recovery.all_children_terminal(tmp_path, owner.task_id, owner.run_token)
    events = restored.audit_log.replay()
    assert sum(e.get("event") == "claim" and e.get("task_id") == rec.id for e in events) == 1
    assert not any(e.get("event") == "child_prompt_delivery_attempted" for e in events)
    assert (recovered.run_token, recovered.fencing_token, recovered.idempotency_key) == (
        rec.run_token, rec.fencing_token, rec.idempotency_key)


def test_registry_reclaims_more_than_1024_terminal_claims_without_resurrection(tmp_path):
    owner = parent()
    store = registry(tmp_path, verify_release=lambda identity, evidence: evidence == {"host": "verified"})
    first = None
    for number in range(1030):
        task = f"finished-{number}"
        scope = ownership(owner, files=(task + ".py",))
        key = store.reserve(owner, task, scope)
        identity = child(owner, task)
        store.bind_claim(key, identity)
        store.release(key, identity, {"host": "verified"})
        if number == 0:
            first = (key, identity, scope)
    assert len(store.snapshot()["reservations"]) < 1024
    key, identity, scope = first
    assert store.retired_reservation(key)["identity"] == identity.to_json()
    with pytest.raises(OwnershipError, match="stale_or_released"):
        store.reserve(owner, identity.task_id, scope)
    with pytest.raises(OwnershipError):
        store.bind_claim(key, identity)
    # Cold ledger binding can recover history, never turn it into a new grant.
    store.reconcile_claim(key, owner, identity.task_id, scope, identity)
    assert store.require_result_current(key, identity)
    with pytest.raises(OwnershipError):
        store.require_current(key, identity)


def test_release_archive_survives_crash_before_active_index_commit(tmp_path, monkeypatch):
    owner = parent()
    store = registry(tmp_path, verify_release=lambda *_: True)
    monkeypatch.setattr(store, "MAX_RECORDS", 2)
    for task in ("old-one", "old-two"):
        key = store.reserve(owner, task, ownership(owner))
        identity = child(owner, task)
        store.bind_claim(key, identity)
        store.release(key, identity, {})
    original = store._write
    monkeypatch.setattr(store, "_write", lambda *a: (_ for _ in ()).throw(SystemExit("after archive fsync")))
    with pytest.raises(SystemExit):
        store.reserve(owner, "next", ownership(owner))
    monkeypatch.setattr(store, "_write", original)
    with pytest.raises(OwnershipError, match="stale_or_released"):
        store.reserve(owner, "old-one", ownership(owner))
    store.reserve(owner, "next", ownership(owner))
    assert list(store.snapshot()["reservations"].values())[0]["task_id"] == "next"


@pytest.mark.parametrize("fault", ["symlink", "hardlink", "public", "corrupt", "identity"])
def test_retired_history_tamper_denies_replay_and_new_admission(tmp_path, monkeypatch, fault):
    owner = parent()
    store = registry(tmp_path, verify_release=lambda *_: True)
    monkeypatch.setattr(store, "MAX_RECORDS", 1)
    key = store.reserve(owner, "old", ownership(owner))
    identity = child(owner, "old")
    store.bind_claim(key, identity)
    store.release(key, identity, {})
    store.reserve(owner, "next", ownership(owner))
    path = store.directory / ("released-" + key + ".json")
    if fault == "symlink":
        path.rename(store.directory / "real-history")
        path.symlink_to(store.directory / "real-history")
    elif fault == "hardlink":
        os.link(path, store.directory / "alias")
    elif fault == "public":
        path.chmod(0o644)
    elif fault == "corrupt":
        path.write_text("{partial")
    else:
        value = json.loads(path.read_text())
        value["identity"]["parent_task_id"] = "foreign"
        path.write_text(json.dumps(value))
    with pytest.raises((OwnershipError, OSError, ValueError)):
        store.reconcile_claim(key, owner, "old", ownership(owner), identity)
    with pytest.raises((OwnershipError, OSError, ValueError)):
        store.reserve(owner, "old", ownership(owner))


def test_production_release_reads_exact_protected_terminal_and_cleanup_truth(tmp_path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent-stack/bin"))
    from agent_durable_children import ensure_attempt_directory
    from herdr.ownership_release import HostOwnershipRelease
    owner = parent()
    store = registry(tmp_path, verify_release=HostOwnershipRelease(tmp_path))
    directory = ensure_attempt_directory(tmp_path, owner.task_id, owner.run_token)
    item = scheduler(directory, owner, store)
    node = item.delegate_child(owner.task_id, owner.run_token, "read-only-terminal",
        proposal(owner, ownership(owner), writing=False))
    item.dispatch(task_ids={node.id}, managed_start=True)
    rec = item._tasks[node.id]
    marker = f"child-{rec.run_token}"
    assert item.record_child_pane_intent(rec.id, rec.run_token, rec.agent_id,
        rec.fencing_token, rec.idempotency_key, marker)
    assert item.bind_pre_delivery_pane(rec.id, rec.run_token, rec.agent_id, "child-pane", marker)
    (directory / "graph.jsonl").rename(directory / "scheduler.jsonl")
    item.audit_log._path = directory / "scheduler.jsonl"
    evidence = [{"answer": "submitted"}]
    digest = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert item.publish_child_result(rec.id, rec.run_token, rec.agent_id, rec.fencing_token,
                                    rec.idempotency_key, digest, evidence, status="blocked")
    assert not item.release_child_ownership(rec.id)
    assert item.mark_child_cleanup_complete(rec.id)
    assert item.release_child_ownership(rec.id)
    item._require_current_ownership(rec, result=True)
    with pytest.raises(OwnershipError):
        item._require_current_ownership(rec)
    row = store.snapshot()["reservations"][rec.ownership_reservation]
    assert row["state"] == "released"
    assert not HostOwnershipRelease(tmp_path)(
        child(owner, rec.id, run="foreign"), {"parent": owner.to_json()})
