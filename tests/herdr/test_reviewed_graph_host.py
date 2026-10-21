"""Protected graph host composition with real disposable evidence and journals only."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"agent-stack/bin"))
from agent_completion_evidence import spec_digest
from herdr import work_configuration as config
from herdr.evidence import EvidenceStore, binding, digest
from herdr.taskgraph import TaskGraph, PersistentTaskGraph, LifecycleState
from herdr.work_cycle import WorkContractError
from tests.herdr.test_host_configuration import approved_config
from tests.herdr.test_work_contract_host import factory_fixture
from tests.herdr.test_work_planning import artifact


def configured(tmp_path, monkeypatch, *, graph=True, budget=False):
    raw, _, _ = approved_config(tmp_path, monkeypatch)
    old, workspace, template, grant, _ = factory_fixture(tmp_path/"actual")
    task = dict(id=grant.identity.task_id, run_token=grant.identity.run_token,
        fencing_token=grant.identity.fencing_token, idempotency_key="ordinary-key", attempt_id=1,
        repo="org/repo", issue=9, kind="coding", prompt="Synthetic unit contract only",
        workspace=str(workspace), work_contract_version=1, spec_hash="a"*64,
        parent_role="writer", parent_tools=["read_file"], parent_permissions=["repo:read"],
        safety_profile="quantlab-paper", completion_plan={"base_sha":template.base_sha})
    plan=replace(template,spec_sha256=spec_digest(task))
    planning=artifact(plan,workspace)
    planning["tools"]=["read_file"];planning["permissions"]=["repo:read"]
    planning["team"]["nodes"][0].update(tools=["read_file"],permissions=["repo:read"])
    for key in ("version","identity","spec_sha256","base_sha","discovery"):planning.pop(key)
    definition=json.loads(json.dumps(plan.to_json()))
    for key in ("version","identity","spec_sha256","grant_sha256","environment_sha256"):definition.pop(key)
    definition.update(discovery_files=["result.py"],planning=planning)
    g=TaskGraph.parse_planner_output({"envelope":{"issue":"org/repo#9","spec_hash":"a"*64,
        "graph_version":"1.1.0","created_at":"2026-10-21T00:00:00+00:00","planner":"unit-host",
        "max_nodes":2,"max_depth":2,"max_fanout":1,"policy_profile":"quantlab-paper"},
        "nodes":[{"id":task["id"],"parent_id":None,"type":"task","role":"writer",
          "objective":"Synthetic host composition only", "inputs":[{"nested":[1,None]}],
          "expected_outputs":[{"kind":"evidence"}],"dependencies":[],"priority":7,
          "resource_class":"small","model_policy":{"model":"external","fallback_model":None},
          "tools":["read_file"],"permissions":["repo:read"],"timeout_seconds":300,"max_attempts":1}]})
    if graph:definition["reviewed_graph"]={"version":1,"graph_sha256":g.graph_hash(),"graph":g.to_planner_json()}
    if budget:definition["budget"]={"unit-only-ordering-tripwire":True}
    raw["templates"]={grant.identity.consumer:grant.to_json()}
    raw["work_contracts"]={"version":1,"environment":asdict(old.environment),
        "plans":{spec_digest(task):definition},"review_records":{}}
    monkeypatch.setattr(config,"_read_configuration",lambda path:deepcopy(raw))
    return raw,task,definition,g,grant,old.git


def graph_path(raw,task):
    return Path(raw["storage"])/"work-contracts"/digest(binding(task))/"taskgraph.jsonl"


def test_actual_pending_graph_is_durable_before_budget_bind(tmp_path,monkeypatch):
    raw,task,definition,g,grant,git=configured(tmp_path,monkeypatch,budget=True)
    reached=[]
    def budget_tripwire(*args,**kwargs):
        saved,states=PersistentTaskGraph(graph_path(raw,task)).replay()
        assert saved.graph_hash()==g.graph_hash()
        assert states[task["id"]].lifecycle is LifecycleState.PENDING
        assert EvidenceStore(graph_path(raw,task).parent/"admission").read("plan",digest(binding(task)))["definition"]==definition
        reached.append(True)
    monkeypatch.setattr("herdr.work_budget_configuration.bind_budget",budget_tripwire)
    config.build_root_work_factory(Path(raw["task_store_root"]),task,git=git)
    assert reached==[True]


def build(raw,task,git,**kwargs):
    return config.build_root_work_factory(Path(raw["task_store_root"]),task,git=git,**kwargs)


def sealed_task(task,grant):
    # Structural sealed-policy data in this unit fixture is not physical proof
    # or authorization; production receives this from the actual launch seal.
    from herdr.policy_launch import CODE_TARGET,RUNTIME_TARGETS
    att=dict(task_id=task["id"],run_token=task["run_token"],fencing_token=task["fencing_token"],
        pane_id="ordinary-pane",marker="ordinary-marker",sandbox_pid=123)
    grant=replace(grant,runtime_assurance=replace(grant.runtime_assurance,sandbox_attestation_sha256=digest(att)))
    proof=dict(schema_version="herdr-policy-launch-2",grant_sha256=grant.hash,
        bundle_sha256="b"*64,bundle_device=1,bundle_inode=2,code_sha256="c"*64,
        runtime_sha256={str(t):"d"*64 for t in RUNTIME_TARGETS},identity=grant.identity.to_json(),
        sandbox_attestation_sha256=digest(att),process_start_ticks=123,
        tree_identities={str(t):dict(device=1,inode=i+1) for i,t in enumerate((CODE_TARGET,*RUNTIME_TARGETS))})
    task["execution_session"]=dict(agent_name=grant.identity.agent_id,pane_id="ordinary-pane",
        pane_marker="ordinary-marker",session_name="ordinary-marker",owned_pane=True,sandbox_verified=True,
        launch_identity=grant.identity.to_json(),sandbox_attestation=att,invocation_policy=proof)
    return SimpleNamespace(grant=grant),proof


@pytest.mark.parametrize("fault",["version","hash","business-spec","task","repo","issue","profile","role","tools","permissions","extra","multiple"])
def test_unapproved_graph_rejected_before_any_budget_port(tmp_path,monkeypatch,fault):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch,budget=True)
    value=d["reviewed_graph"]
    if fault=="version":value["version"]=True
    elif fault=="hash":value["graph_sha256"]="f"*64
    elif fault=="extra":value["authority"]=True
    elif fault=="business-spec":task["spec_hash"]="f"*64;raw["work_contracts"]["plans"]={spec_digest(task):d}
    else:
        body=value["graph"];node=body["nodes"][0]
        if fault=="task":node["id"]="foreign"
        elif fault=="repo":body["envelope"]["issue"]="foreign/repo#9"
        elif fault=="issue":body["envelope"]["issue"]="org/repo#10"
        elif fault=="profile":body["envelope"]["policy_profile"]="foreign"
        elif fault=="role":node["role"]="reader"
        elif fault=="tools":node["tools"]=["write_file"]
        elif fault=="permissions":node["permissions"]=["workspace-write"]
        elif fault=="multiple":
            child=deepcopy(node);child.update(id="child",parent_id=node["id"],dependencies=[node["id"]]);body["nodes"].append(child)
        value["graph_sha256"]=TaskGraph.parse_planner_output(body).graph_hash()
    def forbidden(*args,**kwargs):pytest.fail("budget port reached after graph denial")
    monkeypatch.setattr("herdr.work_budget_configuration.bind_budget",forbidden)
    with pytest.raises((WorkContractError,ValueError)):build(raw,task,git)


def test_host_graph_metadata_is_not_a_workplan_keyword(tmp_path,monkeypatch):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git)
    cycle=work.prepare(identity=grant.identity,workspace=Path(task["workspace"]),grant=grant,spec_sha256=spec_digest(task))
    assert "reviewed_graph" not in cycle.plan.to_json()
    assert work.host_admission["definition"]["reviewed_graph"]==d["reviewed_graph"]


def test_graph_and_original_admission_survive_interruption_before_budget(tmp_path,monkeypatch):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch,budget=True)
    def interrupted(*args,**kwargs):
        if not kwargs.get("recovery"):raise RuntimeError("unit interruption before budget")
    monkeypatch.setattr("herdr.work_budget_configuration.bind_budget",interrupted)
    with pytest.raises(RuntimeError,match="unit interruption"):build(raw,task,git)
    original=graph_path(raw,task).read_bytes()
    raw.pop("work_contracts")
    recovered=build(raw,task,git,recovery=True)
    assert recovered.host_admission["definition"]==d
    assert graph_path(raw,task).read_bytes()==original


@pytest.mark.parametrize("fault",["missing","partial","wrong","public-mode","symlink"])
def test_recovery_never_recreates_or_overwrites_original_graph(tmp_path,monkeypatch,fault):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    build(raw,task,git);path=graph_path(raw,task)
    if fault=="missing":path.unlink()
    elif fault=="partial":path.write_bytes(path.read_bytes()+b'{"partial":')
    elif fault=="wrong":
        body=json.loads(path.read_text());body["graph"]["nodes"][0]["objective"]="foreign";path.write_text(json.dumps(body)+"\n")
    elif fault=="public-mode":path.chmod(0o644)
    else:
        target=path.with_suffix(".saved");path.rename(target);path.symlink_to(target)
    before=path.read_bytes() if path.exists() else None
    with pytest.raises((WorkContractError,ValueError,OSError)):build(raw,task,git,recovery=True)
    assert (path.read_bytes() if path.exists() else None)==before


def test_post_seal_actual_registration_and_repeat_recheck_are_exact(tmp_path,monkeypatch):
    from agent_durable_children import attempt_directory
    from herdr.scheduler import AuditLog,DynamicChildScheduler
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,proof=sealed_task(task,grant)
    parent=config.bind_reviewed_parent(work,task,launch)
    ledger=attempt_directory(Path(raw["task_store_root"]),task["id"],task["run_token"])/"scheduler.jsonl"
    before=ledger.read_bytes()
    assert config.bind_reviewed_parent(work,task,launch,evidence=proof,recheck=True).to_json()==parent.to_json()
    assert ledger.read_bytes()==before
    scheduler=DynamicChildScheduler(audit_log=AuditLog(ledger));scheduler.replay();rec=scheduler._tasks[task["id"]]
    assert rec.node.to_json()==g.nodes[0].to_json()
    assert (rec.run_token,rec.fencing_token,rec.idempotency_key)==(task["run_token"],task["fencing_token"],task["idempotency_key"])
    assert rec.canonical_parent["admission"]["identity"]==grant.identity.to_json()
    assert rec.parent_task_id is None and rec.parent_agent_id is None


@pytest.mark.parametrize("fault",["run","fence","key","pane","marker","parent","scope","unsealed","attestation","grant"])
def test_cross_process_original_admission_and_live_binding_drift_denied(tmp_path,monkeypatch,fault):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,proof=sealed_task(task,grant)
    config.bind_reviewed_parent(work,task,launch)
    session=task["execution_session"]
    if fault=="run":task["run_token"]="foreign"
    elif fault=="fence":task["fencing_token"]+=1
    elif fault=="key":task["idempotency_key"]="foreign"
    elif fault=="pane":session["pane_id"]="foreign"
    elif fault=="marker":session["pane_marker"]="foreign"
    elif fault=="parent":session["launch_identity"]["parent_agent_id"]="foreign"
    elif fault=="scope":task["parent_tools"]=["write_file"]
    elif fault=="unsealed":session["sandbox_verified"]=False
    elif fault=="attestation":session["sandbox_attestation"]["sandbox_pid"]+=1
    else:launch.grant=grant
    with pytest.raises((WorkContractError,ValueError,RuntimeError)):
        config.reviewed_parent_admission(Path(raw["task_store_root"]),task,grant=launch.grant)


def test_bridge_read_uses_original_admission_not_current_catalogue_or_budget(tmp_path,monkeypatch):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,_=sealed_task(task,grant)
    config.bind_reviewed_parent(work,task,launch)
    raw.pop("work_contracts")
    def forbidden(*args,**kwargs):pytest.fail("bridge read opened budget or factory")
    monkeypatch.setattr(config,"build_root_work_factory",forbidden)
    monkeypatch.setattr("herdr.work_budget_configuration.bind_budget",forbidden)
    parent=config.reviewed_parent_admission(Path(raw["task_store_root"]),task,grant=launch.grant)
    assert parent.graph.graph_hash()==g.graph_hash()


def test_missing_original_admission_is_not_reapproved_from_task_json(tmp_path,monkeypatch):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    task["reviewed_graph"]=d["reviewed_graph"]
    launch,_=sealed_task(task,grant)
    with pytest.raises(WorkContractError,match="original work admission"):
        config.reviewed_parent_admission(Path(raw["task_store_root"]),task,grant=launch.grant)


def test_unsealed_attempt_denial_does_not_create_execution_ledger(tmp_path,monkeypatch):
    from agent_durable_children import attempt_directory
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,_=sealed_task(task,grant);task["execution_session"]["sandbox_verified"]=False
    with pytest.raises(WorkContractError):config.bind_reviewed_parent(work,task,launch)
    assert not (attempt_directory(Path(raw["task_store_root"]),task["id"],task["run_token"])/"scheduler.jsonl").exists()


def child_call(raw,task,launch,monkeypatch):
    import argparse
    from importlib.machinery import SourceFileLoader
    from importlib.util import spec_from_loader,module_from_spec
    from herdr.policy_launch import HostPolicyLaunchFactory
    from tests.agent_stack.test_durable_child_bridge import _test_pin
    path=Path(raw["task_store_root"])/"running"/(task["id"]+".json")
    path.parent.mkdir(exist_ok=True);task["attempt_state"]="accepted";path.write_text(json.dumps(task));path.chmod(0o600)
    monkeypatch.setenv("HERDR_DURABLE_TASK_FILE",str(path))
    loader=SourceFileLoader("reviewed_child_composition",str(Path(__file__).resolve().parents[2]/"agent-stack/bin/agent-durable-child"))
    module=module_from_spec(spec_from_loader(loader.name,loader));loader.exec_module(module)
    factory=HostPolicyLaunchFactory.__new__(HostPolicyLaunchFactory);factory.parent_grant=launch.grant
    reached=[]
    class NoNativeRuntime:
        def __init__(self,scheduler,*args,**kwargs):self.scheduler=scheduler
        def run_managed_child(self,lease,*args,**kwargs):reached.append(self.scheduler._tasks[lease.task_id])
    monkeypatch.setattr(module,"HerdrChildRuntime",NoNativeRuntime)
    args=argparse.Namespace(key="read-only",role="reader",objective="Read-only unit composition",
        prompt="Read the unit fixture",tool=["read_file"],permission=[],ownership=None)
    with _test_pin(Path(task["workspace"]),Path(task["workspace"]).parent) as held:
        result=module._delegate_pinned(args,None,Path("/bin/true"),task,
            task["execution_session"]["pane_id"],launch.grant.identity.agent_id,
            task["execution_session"]["pane_marker"],held,policy_launch_factory=factory)
    return result,reached


def test_actual_bridge_revalidates_original_graph_and_preserves_canonical_parent(tmp_path,monkeypatch):
    from agent_durable_children import attempt_directory
    from herdr.scheduler import AuditLog,DynamicChildScheduler
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,_=sealed_task(task,grant);parent=config.bind_reviewed_parent(work,task,launch)
    raw.pop("work_contracts")
    result,reached=child_call(raw,task,launch,monkeypatch)
    assert len(reached)==1 and result["task_id"]==reached[0].id
    ledger=attempt_directory(Path(raw["task_store_root"]),task["id"],task["run_token"])/"scheduler.jsonl"
    scheduler=DynamicChildScheduler(audit_log=AuditLog(ledger));scheduler.replay()
    assert scheduler._tasks[task["id"]].canonical_parent["admission"]==parent.to_json()
    assert scheduler._tasks[task["id"]].node.to_json()==g.nodes[0].to_json()
    assert len([e for e in scheduler.audit_log.replay() if e["event"]=="claim" and e["task_id"]==task["id"]])==1


@pytest.mark.parametrize("fault",["no-ledger","missing-admission","stripped-marker"])
def test_actual_bridge_never_late_initializes_or_falls_back_from_canonical(tmp_path,monkeypatch,fault):
    from agent_durable_children import attempt_directory
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,_=sealed_task(task,grant)
    if fault!="no-ledger":config.bind_reviewed_parent(work,task,launch)
    if fault=="missing-admission":
        for path in (graph_path(raw,task).parent/"admission").glob("*.json"):path.unlink()
    if fault=="stripped-marker":task.pop("work_contract_version")
    from herdr.scheduler import SchedulerError
    with pytest.raises((WorkContractError,SchedulerError,ValueError,RuntimeError)):
        child_call(raw,task,launch,monkeypatch)
    ledger=attempt_directory(Path(raw["task_store_root"]),task["id"],task["run_token"])/"scheduler.jsonl"
    assert not ledger.exists() if fault=="no-ledger" else not any(
        json.loads(line).get("event")=="spawn_child" for line in ledger.read_text().splitlines())


def callback(task,work,launch,persist):
    # Execute the actual nested worker callback, with the actual graph guard.
    import ast
    source=Path(__file__).resolve().parents[2]/"agent-stack/bin/agent-task-worker"
    node=next(n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef) and n.name=="publish_continuation")
    namespace=dict(task=task,work_factory=work,launch=launch,session=task["execution_session"],
        bind_reviewed_parent=config.bind_reviewed_parent,persist_execution_session=persist)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),"exec"),namespace)
    return namespace["publish_continuation"]


def test_final_worker_continuation_denial_cannot_persist_or_ack_changed_scope(tmp_path,monkeypatch):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,proof=sealed_task(task,grant);config.bind_reviewed_parent(work,task,launch)
    saved=deepcopy(task["execution_session"]["invocation_policy"]);calls=[]
    send=callback(task,work,launch,lambda task:calls.append(True))
    changed=deepcopy(proof);changed["identity"]["parent_agent_id"]="foreign"
    from herdr.security import SecurityError
    with pytest.raises(SecurityError):send(changed)
    assert calls==[] and task["execution_session"]["invocation_policy"]==saved
    assert send(proof) is True and calls==[True]


def test_worker_seal_graph_bind_prepare_and_ack_order():
    import ast
    source=Path(__file__).resolve().parents[2]/"agent-stack/bin/agent-task-worker"
    tree=ast.parse(source.read_text());create=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="create_task_session")
    calls=[n for n in ast.walk(create) if isinstance(n,ast.Call)]
    positions=lambda name:[n.lineno for n in calls if (isinstance(n.func,ast.Name) and n.func.id==name) or (isinstance(n.func,ast.Attribute) and n.func.attr==name)]
    assert positions("seal")[0] < positions("bind_reviewed_parent")[0] < positions("prepare")[-1]
    cb=next(n for n in ast.walk(create) if isinstance(n,ast.FunctionDef) and n.name=="publish_continuation")
    check=next(n for n in ast.walk(cb) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="bind_reviewed_parent")
    assign=next(n for n in ast.walk(cb) if isinstance(n,ast.Assign))
    assert check.lineno < assign.lineno < positions("persist_execution_session")[-2]


def test_task_json_cannot_select_or_approve_a_graph(tmp_path,monkeypatch):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch,graph=False)
    task["reviewed_graph"]={"version":1,"graph_sha256":g.graph_hash(),"graph":g.to_planner_json()}
    work=build(raw,task,git)
    assert "reviewed_graph" not in work.host_admission["definition"]
    assert not graph_path(raw,task).exists()
    launch,_=sealed_task(task,grant)
    assert config.reviewed_parent_admission(Path(raw["task_store_root"]),task,grant=launch.grant) is None


def test_bridge_private_admission_checks_precede_store_constructor(tmp_path,monkeypatch):
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    build(raw,task,git);launch,_=sealed_task(task,grant)
    directory=graph_path(raw,task).parent/"admission";directory.chmod(0o755)
    def forbidden(*args,**kwargs):pytest.fail("untrusted admission path reached EvidenceStore constructor")
    monkeypatch.setattr(config,"EvidenceStore",forbidden)
    with pytest.raises(WorkContractError,match="not private"):
        config.reviewed_parent_admission(Path(raw["task_store_root"]),task,grant=launch.grant)


def test_final_continuation_never_recreates_missing_canonical_ledger(tmp_path,monkeypatch):
    from agent_durable_children import attempt_directory
    raw,task,d,g,grant,git=configured(tmp_path,monkeypatch)
    work=build(raw,task,git);launch,proof=sealed_task(task,grant);config.bind_reviewed_parent(work,task,launch)
    directory=attempt_directory(Path(raw["task_store_root"]),task["id"],task["run_token"])
    ledger=directory/"scheduler.jsonl";ledger.unlink();calls=[]
    with pytest.raises(RuntimeError):callback(task,work,launch,lambda task:calls.append(True))(proof)
    assert not ledger.exists() and calls==[]
