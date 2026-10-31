"""Inert claimed-data/CAS/replay components; no SDK/native/budget opens."""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import importlib.util
import ast
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"agent-stack/bin"))
from agent_completion_evidence import spec_digest, store_for, freeze_derived_child_contracts
from herdr import claimed_child_contracts as derived
from herdr import work_configuration as configuration
from herdr.child_completion_policy import authority_for_parent,policy_key
from herdr.child_evidence import child_spec,child_task
from herdr.child_ownership import ChildOwnership
from herdr.evidence import EvidenceStore,EvidenceError,binding,digest
from herdr.security import InvocationIdentity,ToolRule,RiskClass
from herdr.taskgraph import TaskGraph
from herdr.work_budget import BudgetLimits,BudgetAllocation
from herdr.work_cycle import WorkContractError,WorkPlan
from herdr.work_hygiene import LocalCommitPolicy
from tests.herdr.test_work_cycle import setup,git,trusted_git
from tests.herdr.test_check_runner import environment
from tests.herdr.test_work_planning import artifact
from tests.herdr.test_security import grant as synthetic_grant

ROOT_TOOLS=sorted(["herdr_delegate_child","herdr_submit_result","herdr_verify_work","write_file"])
CHILD_TOOLS=sorted(set(ROOT_TOOLS)-{"herdr_delegate_child"})


def claim_identity(task):
    worker=Path(__file__).resolve().parents[2]/"agent-stack/bin/agent-task-worker"
    tree=ast.parse(worker.read_bytes());names={"_task_session_identity","_claimed_root_identity"}
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    scope={"hashlib":hashlib}
    exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(worker),"exec"),scope)
    return scope["_claimed_root_identity"](task)


def definition(plan,root,tools,permissions,policy,budget):
    data=json.loads(json.dumps(plan.to_json()))
    for key in ("version","identity","spec_sha256","grant_sha256","environment_sha256","hygiene_sha256"):
        data.pop(key,None)
    planning=artifact(plan,root)
    planning["tools"]=tools;planning["permissions"]=permissions
    planning["team"]["nodes"][0].update(tools=tools,permissions=permissions)
    for key in ("version","identity","spec_sha256","base_sha","discovery"):planning.pop(key)
    raw=asdict(policy);raw.pop("environment")
    data.update(planning=planning,discovery_files=["result.py"],hygiene=raw,budget=deepcopy(budget))
    return json.loads(json.dumps(data))


@pytest.fixture
def prepared(tmp_path):
    _,root,old,unused=setup(tmp_path/"source")
    git(root,"branch","-m","herdr/root")
    (root/".git/info/exclude").write_text(".stage3-child/\n")
    child=root/".stage3-child/repo";child.parent.mkdir()
    git(root,"clone","--no-hardlinks","--no-checkout","--template=",str(root),str(child))
    git(child,"checkout","-q","herdr/root");git(child,"branch","-m","herdr/child")
    git(child,"remote","set-url","origin","https://github.com/Bbambaaamm/herdr.git")
    git(child,"config","user.name","Child data test");git(child,"config","user.email","data@example.invalid")
    (child/".git/hooks").mkdir(exist_ok=True)
    task={"id":"root","run_token":"run-1","fencing_token":7,"idempotency_key":"original-key","attempt_id":1,
        "repo":"Bbambaaamm/herdr","issue":9,"kind":"coding","prompt":"Bounded component fixture",
        "spec_hash":"sha256:"+"1"*64,"workspace":str(root),"worktree_root":str(root.parent),
        "safety_profile":"herdr-core","agent":"quantlab-hermes","routing":{"selected_agent":"quantlab-hermes"},
        "parent_role":"writer","parent_tools":ROOT_TOOLS,"parent_permissions":["workspace-write"],
        "work_contract_version":1,"work_budget_version":1,"completion_plan":{"base_sha":old.base_sha}}
    identity=claim_identity(task)
    limits=BudgetLimits(1800000,2100000,4,500000,0,2,0,1,1)
    parent=BudgetAllocation("a"*64,"github:Bbambaaamm/herdr","b"*64,"c"*64,"d"*64,limits)
    allocation=BudgetAllocation("e"*64,parent.consumer,"f"*64,parent.lineage_key,parent.authorization_reference,
        replace(limits,max_model_calls=2),parent.allocation_id)
    quote={"provider":"provider-a","model":"fixture-model","api_mode":"chat_completions",
        "base_url":"https://fixture.invalid/v1","max_request_bytes":4096,"max_output_tokens":1024,
        "max_tokens":5120,"max_cost_microusd":0,"max_work_ms":450000}
    pb={"version":1,"allocation":asdict(parent),"ancestors":[],"model_quotes":[quote]}
    cb={"version":1,"allocation":asdict(allocation),"ancestors":[asdict(parent)],"model_quotes":[quote]}
    env=environment();env=replace(env,executables=(*env.executables,"/usr/bin/git"))
    def policy(where):return LocalCommitPolicy("repo-policy-1",env,
        hashlib.sha256((where/".git/config").read_bytes()).hexdigest(),str(where/".git/hooks"),())
    pp,cp=policy(root),policy(child)
    plan=replace(old,identity=identity,spec_sha256=spec_digest(task),environment_sha256=env.hash,
                 budget_reference=parent.hash,hygiene_sha256=pp.hash)
    child_identity=InvocationIdentity(parent.consumer,"child-agent",identity.agent_id,task["id"],
        "root-child-synthetic","child-run",8)
    child_plan=replace(plan,identity=child_identity,budget_reference=allocation.hash,hygiene_sha256=cp.hash)
    child_definition=definition(child_plan,child,CHILD_TOOLS,["workspace-write"],cp,cb)
    parent_definition=definition(plan,root,ROOT_TOOLS,["workspace-write"],pp,pb)
    node={"type":"task","id":task["id"],"parent_id":None,"role":task["parent_role"],"dependencies":[],
        "priority":0,"resource_class":"standard","permissions":task["parent_permissions"],"timeout_seconds":2100,
        "max_attempts":1,"objective":task["prompt"],"inputs":[],"expected_outputs":[{"kind":"candidate_commit"}],
        "model_policy":{"model":"fixture-model","fallback_model":None},"tools":ROOT_TOOLS}
    graph={"envelope":{"issue":"Bbambaaamm/herdr#9","spec_hash":task["spec_hash"],"graph_version":"1.1.0",
        "created_at":"2026-10-23T00:00:00+00:00","planner":"inert-component","max_nodes":2,"max_depth":2,
        "max_fanout":1,"policy_profile":"herdr-core"},"nodes":[node]}
    parent_definition["reviewed_graph"]={"version":1,"graph":graph,"graph_sha256":TaskGraph.parse_planner_output(graph).graph_hash()}
    ownership={"write_scope":[{"kind":"file","key":"result.py"}],"decision_scope":[],"hard_dependencies":[],
        "shared_dependencies":[],"integration_owner":task["id"],"handoff_ref":"stage3-child"}
    criteria={"version":1,"files":[{"path":"result.py","subtree":False}],"acceptance_ids":list(plan.criteria),"shared_contract_keys":[]}
    template={"key":"stage3-child","objective":"Bounded child fixture","role":"writer","tools":CHILD_TOOLS,
        "permissions":["workspace-write"],"worktree_identity":str(child)+f"|{child.stat().st_dev}:{child.stat().st_ino}",
        "ownership":ownership,"completion":{"kind":"coding","criteria":criteria,"work_contract_version":1,
            "work_budget_version":1},"work_definition":child_definition}
    parent_definition["managed_children"]={"version":1,"children":[template]}
    return SimpleNamespace(task=task,identity=identity,definition=parent_definition,root=root,child=child,
        environment=env,plan=plan,child_identity=child_identity,parent_budget=pb,child_budget=cb,tmp=tmp_path)


def admission(p):
    return {"version":1,"identity":binding(p.task),"spec_sha256":spec_digest(p.task),
        "definition":deepcopy(p.definition),"environment":asdict(p.environment),
        "managed_children":derived.derive(p.definition,p.task,p.identity)}


def test_original_leaf_has_exact_bytes_no_null_field(prepared):
    p=prepared;definition=deepcopy(p.definition);definition.pop("managed_children")
    old={"version":1,"identity":binding(p.task),"spec_sha256":spec_digest(p.task),"definition":definition,
         "environment":asdict(p.environment)}
    before=json.dumps(old,sort_keys=True).encode()
    assert derived.derive(definition,None,None) is None
    assert derived.retained(old,p.task) is None
    assert json.dumps(old,sort_keys=True).encode()==before and "managed_children" not in old


def test_derive_does_not_change_task_spec_or_source_approval(prepared,monkeypatch):
    p=prepared;before=json.dumps([p.task,p.definition],sort_keys=True);original=spec_digest(p.task)
    from herdr.work_budget import WorkBudgetAuthority
    monkeypatch.setattr(WorkBudgetAuthority,"open",lambda *a,**kw:pytest.fail("derivation cannot open budget"))
    result=derived.derive(p.definition,p.task,p.identity)
    assert len(result["children"])==1 and result["identity"]==p.identity.to_json()
    assert json.dumps([p.task,p.definition],sort_keys=True)==before and spec_digest(p.task)==original
    row=next(iter(result["children"].values()))
    assert row["scope"]["parent_agent_id"]==p.identity.agent_id and row["key"]=="stage3-child"
    assert row["model_policy"]=={"model":"fixture-model","fallback_model":None}


@pytest.mark.parametrize("fault",["run","fence","route","model-route","fallback-route","route-missing","agent","template","limits","quote","ancestry","path","tools","result-tool","depth","key","spec"])
def test_claim_route_template_or_scope_drift_is_denied(prepared,fault):
    p=prepared;old=admission(p);task=deepcopy(p.task)
    if fault=="run":task["run_token"]="other"
    elif fault=="fence":task["fencing_token"]+=1
    elif fault=="route":task["routing"]["selected_agent"]="another"
    elif fault=="model-route":task["routing"]["model"]="another-model"
    elif fault=="fallback-route":task["routing"]["fallback_model"]="unapproved"
    elif fault=="route-missing":task.pop("routing")
    elif fault=="agent":task["execution_session"]={"launch_identity":replace(p.identity,agent_id="other").to_json()}
    else:
        item=old["definition"]["managed_children"]["children"][0]
        if fault=="template":item["objective"]="Different work"
        elif fault=="limits":item["work_definition"]["budget"]["allocation"]["limits"]["max_model_calls"]=5
        elif fault=="quote":item["work_definition"]["budget"]["model_quotes"][0]["model"]="other-model"
        elif fault=="ancestry":item["work_definition"]["budget"]["ancestors"]=[]
        elif fault=="path":item["worktree_identity"]="/outside|1:2"
        elif fault=="tools":item["tools"]=sorted([*item["tools"],"terminal"])
        elif fault=="result-tool":item["tools"].remove("herdr_submit_result")
        elif fault=="depth":
            graph=old["definition"]["reviewed_graph"]["graph"];graph["envelope"]["max_depth"]=1
            old["definition"]["reviewed_graph"]["graph_sha256"]=TaskGraph.parse_planner_output(graph).graph_hash()
        elif fault=="key":item["key"]="other-declaration"
        elif fault=="spec":task["prompt"]="Changed root task"
    with pytest.raises((WorkContractError,EvidenceError,ValueError)):
        derived.retained(old,task,identity=p.identity)


def test_protected_store_CAS_blocks_same_claim_route_change(prepared):
    p=prepared;store=EvidenceStore(p.tmp/"protected");first=admission(p);key=digest(binding(p.task))
    store.publish("plan",key,first)
    before={x.name:x.read_bytes() for x in store.root.iterdir() if x.is_file()}
    task=deepcopy(p.task);task["routing"]["selected_agent"]="other-coordinator"
    identity=claim_identity(task);second=deepcopy(first)
    second["managed_children"]=derived.derive(p.definition,task,identity)
    with pytest.raises(EvidenceError):store.publish("plan",key,second)
    assert before=={x.name:x.read_bytes() for x in store.root.iterdir() if x.is_file()}


def parent_plan(p):
    value={"version":1,"identity":binding(p.task),"repo":p.task["repo"],"kind":"coding","base_sha":p.plan.base_sha,
        "spec_hash":spec_digest(p.task),"policy_hash":"f"*64,"workspace_root":str(p.root.parent),
        "required_checks":["Herdr contract","GitGuardian Security Checks"],"reviewer":"chatgpt-codex-connector[bot]",
        "environment":{"collector":"github-api-v1","ci_workflow_blob_sha":"1"*40,"ci_workflow_id":367993725,
            "github_actions_app_id":15368}}
    value["plan_hash"]=digest(value);value["baseline"]=[]
    return value


@pytest.mark.parametrize("consumer_fault",[None,"static-identical","static-changed","parent-missing",
    "parent-admission-missing","marker-missing","marker-null","marker-changed","record-missing",
    "record-null","old-wrong-child-admission","cold-marker-missing","cold-marker-null","cold-marker-changed",
    "cold-parent-missing","cold-marker-and-parent-missing","cold-admission-marker-missing",
    "cold-admission-marker-null","cold-definition-drift","cold-environment-drift"])
@pytest.mark.parametrize("base_branch",[None,"review/approved"])
def test_producer_persist_original_authority_child_factory_and_cold_replay(prepared,monkeypatch,consumer_fault,base_branch):
    p=prepared;task_root=p.tmp/"task-state";task_root.mkdir(mode=0o700);storage=p.tmp/"storage";storage.mkdir(mode=0o700)
    original_bytes=json.dumps(p.task,sort_keys=True);original_spec=spec_digest(p.task)
    raw={"task_store_root":str(task_root),"storage":str(storage),"work_contracts":{"version":1,
        "environment":asdict(p.environment),"plans":{original_spec:deepcopy(p.definition)},"review_records":{}}}
    raw=json.loads(json.dumps(raw))  # Match the actual JSON configuration reader.
    monkeypatch.setattr(configuration,"_read_configuration",lambda path:deepcopy(raw))
    monkeypatch.setattr(configuration,"build_host_policy_factory",lambda **kw:SimpleNamespace(writable_roots=(str(p.root),)))
    events=[]
    monkeypatch.setattr(configuration,"_graph_admission",lambda *a,**kw:events.append("original-graph-port-double"))
    import herdr.work_budget_configuration as budgets
    def bind_budget(factory,definition,**kwargs):
        events.append("budget-binding-port-double");factory.budget_authority=object()
        factory.budget_definition=deepcopy(definition)
        return budgets.parse_allocation(definition["allocation"])
    monkeypatch.setattr(budgets,"bind_budget",bind_budget)
    store=store_for(task_root,p.task)
    frozen=parent_plan(p)
    if base_branch is not None:
        frozen["base_branch"]=base_branch
        frozen["plan_hash"]=digest({k:v for k,v in frozen.items() if k not in {"plan_hash","baseline"}})
    store.publish("plan",digest(binding(p.task)),frozen)
    import agent_completion_evidence as completion
    original_freeze=completion.freeze_derived_child_contracts
    def frozen(*args,**kw):events.append("freeze-derived-policy");return original_freeze(*args,**kw)
    monkeypatch.setattr(completion,"freeze_derived_child_contracts",frozen)
    factory=configuration.build_root_work_factory(task_root,p.task,git=trusted_git(p.root),claimed_identity=p.identity)
    assert events.index("freeze-derived-policy")<events.index("budget-binding-port-double")
    persisted=configuration.original_derived_children(task_root,p.task,identity=p.identity)
    assert persisted==factory.host_admission["managed_children"]
    assert json.dumps(p.task,sort_keys=True)==original_bytes and spec_digest(p.task)==original_spec
    authority=authority_for_parent(store,p.task,parent_spec_hash=original_spec,parent_identity=p.identity,
        collector=lambda *a:pytest.fail("no external evidence collected"),admitted_children=persisted)
    # Actual canonical scheduler data/claim/ownership; no native pane or budget authority.
    from herdr.scheduler import DynamicChildScheduler,AuditLog,CanonicalParentAdmission,ChildProposal
    from herdr.child_ownership import OwnershipRegistry
    from herdr.taskgraph import LifecycleState,TaskNode
    graph=TaskGraph.parse_planner_output(p.definition["reviewed_graph"]["graph"])
    ownership_root=p.tmp/"ownership";ownership_root.mkdir(mode=0o700)
    scheduler=DynamicChildScheduler(audit_log=AuditLog(p.tmp/"canonical-graph.jsonl"),clock=lambda:1000.,
        completion_authority=authority,ownership_registry=OwnershipRegistry(ownership_root),ownership_parent=p.identity)
    scheduler.submit(graph,repo=p.task["repo"],issue=str(p.task["issue"]))
    parent_data=CanonicalParentAdmission(graph,graph.graph_hash(),p.identity,p.task["idempotency_key"],
        p.task["repo"],str(p.task["issue"]),"inert-pane","inert-marker")
    scheduler.register_external_parent_attempt(task_id=p.task["id"],run_token=p.task["run_token"],
        idempotency_key=p.task["idempotency_key"],agent_name=p.identity.agent_id,pane_id="inert-pane",marker="inert-marker",
        repo=p.task["repo"],issue=str(p.task["issue"]),role=p.task["parent_role"],tools=ROOT_TOOLS,
        permissions=p.task["parent_permissions"],policy_profile="herdr-core",canonical_parent=parent_data)
    row=next(iter(persisted["children"].values()));scope=row["scope"]
    proposal=ChildProposal(parent_role=p.task["parent_role"],parent_tools=ROOT_TOOLS,
        parent_permissions=p.task["parent_permissions"],child_role=scope["role"],child_task=scope["objective"],
        child_tools=scope["tools"],child_permissions=scope["permissions"],child_model=row["model_policy"]["model"],
        child_fallback_model=None,worktree_identity=scope["worktree_identity"],
        ownership=ChildOwnership.from_json(p.definition["managed_children"]["children"][0]["ownership"]))
    node=scheduler.delegate_child(p.task["id"],p.task["run_token"],row["key"],proposal)
    assert isinstance(node,TaskNode)
    claims=scheduler.dispatch(task_ids={node.id},managed_start=True);assert len(claims)==1
    rec=scheduler._tasks[node.id]
    p.child_identity=InvocationIdentity("github:"+rec.repo,rec.agent_id,rec.parent_agent_id,rec.parent_task_id,
        rec.id,rec.run_token,rec.fencing_token)
    assert rec.state is LifecycleState.RUNNING and rec.run_token and rec.idempotency_key
    assert scheduler.ownership_registry.require_current(rec.ownership_reservation,p.child_identity)
    authority.prepare(rec);assert authority.modern_work(rec)
    monkeypatch.setattr("herdr.host_configuration.read_canonical_parent",lambda *args:deepcopy(p.task))
    approved=authority.store.read("plan",digest(binding(child_task(rec))))
    child_task_data=authority._work_task(rec,approved)
    assert approved.get("base_branch")==base_branch
    assert child_task_data["completion_plan"].get("base_branch")==base_branch
    cold_authority=authority_for_parent(store,p.task,parent_spec_hash=original_spec,parent_identity=p.identity,
        collector=lambda *a:pytest.fail("cold preparation cannot collect GitHub"),admitted_children=persisted)
    assert cold_authority.approve(task=child_task(rec),spec_sha256=child_spec(rec))==approved
    assert child_task_data["derived_parent_admission_sha256"]==digest(persisted)
    without_marker=dict(child_task_data);without_marker.pop("derived_parent_admission_sha256")
    assert spec_digest(child_task_data)==spec_digest(without_marker)
    expected=next(iter(persisted["children"].values()))["work_definition"]
    if consumer_fault is not None and not consumer_fault.startswith("cold-"):
        current=deepcopy(expected)
        if consumer_fault!="static-identical":current["purpose"]="later-static-definition"
        raw["work_contracts"]["plans"][child_spec(rec)]=current
        before_budget=events.count("budget-binding-port-double")
        if consumer_fault=="parent-missing":
            monkeypatch.setattr("herdr.host_configuration.read_canonical_parent",lambda *args:None)
        elif consumer_fault=="parent-admission-missing":
            directory=storage/"work-contracts"/digest(binding(p.task))/"admission"
            (directory/("plan-"+digest(binding(p.task))+".json")).unlink()
        elif consumer_fault=="marker-missing":child_task_data.pop("derived_parent_admission_sha256")
        elif consumer_fault=="marker-null":child_task_data["derived_parent_admission_sha256"]=None
        elif consumer_fault=="marker-changed":child_task_data["derived_parent_admission_sha256"]="0"*64
        elif consumer_fault in {"record-missing","record-null"}:
            original_read=configuration._original_work_admission
            def altered(*args,**kwargs):
                directory,value=original_read(*args,**kwargs);value=deepcopy(value)
                if consumer_fault=="record-missing":value.pop("managed_children")
                else:value["managed_children"]=None
                return directory,value
            monkeypatch.setattr(configuration,"_original_work_admission",altered)
        if consumer_fault=="old-wrong-child-admission":
            directory=storage/"work-contracts"/digest(binding(child_task_data))/"admission"
            configuration._private_directory(directory,base=storage)
            EvidenceStore(directory).publish("plan",digest(binding(child_task_data)),{
                "version":1,"identity":binding(child_task_data),"spec_sha256":child_spec(rec),
                "definition":current,"environment":raw["work_contracts"]["environment"]})
        with pytest.raises((WorkContractError,EvidenceError,ValueError,OSError)):
            configuration.build_root_work_factory(task_root,child_task_data,spec_sha256=child_spec(rec),
                git=trusted_git(p.child),recovery=consumer_fault=="old-wrong-child-admission")
        assert events.count("budget-binding-port-double")==before_budget
        return
    child_factory=configuration.build_root_work_factory(task_root,child_task_data,spec_sha256=child_spec(rec),git=trusted_git(p.child))
    assert child_factory.host_admission["definition"]==expected
    assert child_factory.host_admission["derived_parent_admission_sha256"]==digest(persisted)
    assert child_factory.budget_definition==expected["budget"]
    risks={"write_file":RiskClass.WORKSPACE_WRITE,"herdr_delegate_child":RiskClass.DELEGATION,
           "herdr_verify_work":RiskClass.READ,"herdr_submit_result":RiskClass.RESULT_SUBMISSION}
    def rules(tools,where):
        args={"write_file":("path","content"),"herdr_delegate_child":(),
              "herdr_verify_work":("request_id","handoff"),"herdr_submit_result":("status","evidence","summary")}
        return tuple(ToolRule(tool,risks[tool],args[tool],
            path_fields=("path",) if tool=="write_file" else (),allowed_roots=(str(where),),
            requires_sandbox=tool!="write_file") for tool in tools)
    parent_grant=synthetic_grant(p.root,tools=tuple(ROOT_TOOLS),rules=rules(ROOT_TOOLS,p.root))
    parent_grant=replace(parent_grant,identity=p.identity,scope=replace(parent_grant.scope,permissions=("workspace-write",)))
    child_grant=replace(parent_grant,identity=p.child_identity,workspace_root=str(p.child),
        scope=replace(parent_grant.scope,tools=tuple(CHILD_TOOLS)),tool_rules=rules(CHILD_TOOLS,p.child),
        parent_grant_hash=parent_grant.hash)
    child_grant.require_logical_subset_of(parent_grant)
    # Source-only admission reader fixture: synthetic seal event, never physical acceptance.
    child_factory.audit_log.append({"event":"host_delegated_write_sealed", "identity":p.child_identity.to_json(),
        "grant_sha256":child_grant.hash, "spec_sha256":child_spec(rec)})
    child_factory.audit_log.flush()
    approved_work=child_factory.approve(identity=p.child_identity,workspace=p.child,grant=child_grant,spec_sha256=child_spec(rec))
    assert isinstance(approved_work,WorkPlan) and approved_work.identity==p.child_identity
    assert approved_work.spec_sha256==child_spec(rec) and approved_work.grant_sha256==child_grant.hash
    assert not list(store.root.glob("accepted-*"))
    saved=deepcopy(factory.host_admission)
    raw.pop("work_contracts");shutil.rmtree(p.root)
    # Cold metadata replay: original template/claim only; no workspace, new catalogue or allocation.
    cold=configuration.build_root_work_factory(task_root,p.task,recovery=True)
    assert cold.host_admission==saved
    assert configuration.original_derived_children(task_root,p.task,identity=p.identity)==persisted
    if consumer_fault is not None:
        before_budget=events.count("budget-binding-port-double")
        if consumer_fault in {"cold-marker-missing","cold-marker-and-parent-missing"}:
            child_task_data.pop("derived_parent_admission_sha256")
        elif consumer_fault=="cold-marker-null":child_task_data["derived_parent_admission_sha256"]=None
        elif consumer_fault=="cold-marker-changed":child_task_data["derived_parent_admission_sha256"]="0"*64
        if consumer_fault in {"cold-parent-missing","cold-marker-and-parent-missing"}:
            monkeypatch.setattr("herdr.host_configuration.read_canonical_parent",lambda *args:None)
        if consumer_fault.startswith("cold-admission-") or consumer_fault in {"cold-definition-drift","cold-environment-drift"}:
            child_directory=storage/"work-contracts"/digest(binding(child_task_data))/"admission"
            original_read=EvidenceStore.read
            def changed_child_admission(store,*args,**kwargs):
                value=original_read(store,*args,**kwargs)
                if store.root==child_directory:
                    value=deepcopy(value)
                    if consumer_fault=="cold-admission-marker-missing":value.pop("derived_parent_admission_sha256")
                    elif consumer_fault=="cold-admission-marker-null":value["derived_parent_admission_sha256"]=None
                    elif consumer_fault=="cold-definition-drift":value["definition"]["purpose"]="not-original"
                    else:value["environment"]["max_processes"]=987
                return value
            monkeypatch.setattr(EvidenceStore,"read",changed_child_admission)
        with pytest.raises((WorkContractError,EvidenceError,ValueError,OSError)):
            configuration.build_root_work_factory(task_root,child_task_data,recovery=True,spec_sha256=child_spec(rec))
        assert events.count("budget-binding-port-double")==before_budget
        return
    cold_child=configuration.build_root_work_factory(task_root,child_task_data,recovery=True,spec_sha256=child_spec(rec))
    assert cold_child.host_admission==child_factory.host_admission
    fresh=authority_for_parent(EvidenceStore(store.root),p.task,parent_spec_hash=original_spec,
        collector=lambda *a:pytest.fail("cold pending child cannot invent PR"),parent_identity=p.identity,
        admitted_children=persisted)
    assert fresh.modern_work(rec) and not list(store.root.glob("accepted-*"))
    replayed=DynamicChildScheduler(audit_log=AuditLog(p.tmp/"canonical-graph.jsonl"),clock=lambda:1000.,
        completion_authority=fresh,ownership_registry=OwnershipRegistry(ownership_root),ownership_parent=p.identity)
    assert replayed.replay()>=1
    cold_rec=replayed._tasks[rec.id]
    assert (cold_rec.id,cold_rec.run_token,cold_rec.fencing_token,cold_rec.delegation_key)==(
        rec.id,rec.run_token,rec.fencing_token,rec.delegation_key)
    assert cold_rec.node.model_policy==rec.node.model_policy and cold_rec.state is not LifecycleState.DONE
    assert fresh.modern_work(cold_rec) and not list(store.root.glob("accepted-*"))
    assert replayed.ownership_registry.require_current(cold_rec.ownership_reservation,p.child_identity)
    rec.delegation_key="other"
    with pytest.raises(EvidenceError,match="declaration"):fresh.modern_work(rec)
    rec.delegation_key=next(iter(persisted["children"].values()))["key"]
    rec.node=replace(rec.node,model_policy={"model":"fixture-model","fallback_model":"unapproved"})
    with pytest.raises(EvidenceError,match="model policy"):fresh.modern_work(rec)


def factory_ports(p,monkeypatch,definition=None):
    task_root=p.tmp/"task-state";task_root.mkdir(mode=0o700)
    storage=p.tmp/"storage";storage.mkdir(mode=0o700)
    selected=deepcopy(p.definition if definition is None else definition)
    raw=json.loads(json.dumps({"task_store_root":str(task_root),"storage":str(storage),
        "work_contracts":{"version":1,"environment":asdict(p.environment),
            "plans":{spec_digest(p.task):selected},"review_records":{}}}))
    monkeypatch.setattr(configuration,"_read_configuration",lambda path:deepcopy(raw))
    monkeypatch.setattr(configuration,"build_host_policy_factory",lambda **kw:SimpleNamespace(writable_roots=(str(p.root),)))
    events=[]
    monkeypatch.setattr(configuration,"_graph_admission",lambda *a,**kw:events.append("graph-port-double"))
    import herdr.work_budget_configuration as budgets
    def bind_budget(factory,definition,**kwargs):
        events.append("budget-port-double");factory.budget_authority=object()
    monkeypatch.setattr(budgets,"bind_budget",bind_budget)
    store_for(task_root,p.task).publish("plan",digest(binding(p.task)),parent_plan(p))
    return task_root,storage,raw,events


def test_actual_leaf_factory_preserves_original_admission_bytes_and_replay(prepared,monkeypatch):
    p=prepared;leaf=deepcopy(p.definition);leaf.pop("managed_children")
    task_root,storage,raw,events=factory_ports(p,monkeypatch,leaf)
    before=json.dumps(p.task,sort_keys=True)
    factory=configuration.build_root_work_factory(task_root,p.task,git=trusted_git(p.root))
    expected={"version":1,"identity":binding(p.task),"spec_sha256":spec_digest(p.task),
        "definition":raw["work_contracts"]["plans"][spec_digest(p.task)],
        "environment":raw["work_contracts"]["environment"]}
    assert factory.host_admission==expected and derived.FIELD not in expected
    admission_path=storage/"work-contracts"/digest(binding(p.task))/"admission"
    original_files={x.name:x.read_bytes() for x in admission_path.iterdir() if x.is_file()}
    old_serialization=EvidenceStore(p.tmp/"old-serialization")
    old_serialization.publish("plan",digest(binding(p.task)),expected)
    assert original_files=={x.name:x.read_bytes() for x in old_serialization.root.iterdir() if x.is_file()}
    assert configuration.original_derived_children(task_root,p.task) is None
    raw.pop("work_contracts");shutil.rmtree(p.root)
    recovered=configuration.build_root_work_factory(task_root,p.task,recovery=True)
    assert recovered.host_admission==expected
    assert original_files=={x.name:x.read_bytes() for x in admission_path.iterdir() if x.is_file()}
    assert json.dumps(p.task,sort_keys=True)==before


@pytest.mark.parametrize("fault",["missing","null","definition-missing","static","identity","version","row"])
def test_approved_template_cannot_downgrade_or_accept_partial_record(prepared,fault):
    p=prepared;old=admission(p)
    if fault=="missing":old.pop("managed_children")
    elif fault=="null":old["managed_children"]=None
    elif fault=="definition-missing":old["definition"].pop("managed_children")
    elif fault=="static":p.task["child_completion_contracts"]={"unexpected":"mixed"}
    elif fault=="identity":old["managed_children"]["identity"]["agent_id"]="other"
    elif fault=="version":old["managed_children"]["version"]=2
    elif fault=="row":old["managed_children"]["children"].clear()
    with pytest.raises((WorkContractError,EvidenceError,ValueError)):
        derived.retained(old,p.task,identity=p.identity)


def test_durable_admission_failure_prevents_child_policy_and_budget_binding(prepared,monkeypatch):
    p=prepared;task_root,storage,raw,events=factory_ports(p,monkeypatch)
    original=EvidenceStore.publish
    def fail_before_publish(store,*args,**kwargs):
        if store.root.name=="admission":raise OSError("inert disk failure")
        return original(store,*args,**kwargs)
    monkeypatch.setattr(EvidenceStore,"publish",fail_before_publish)
    with pytest.raises(OSError,match="inert disk failure"):
        configuration.build_root_work_factory(task_root,p.task,git=trusted_git(p.root),claimed_identity=p.identity)
    assert events==[]
    with pytest.raises(Exception):
        store_for(task_root,p.task).read("plan",policy_key(p.task["repo"],p.task["id"],p.task["run_token"]))
    assert not list((storage/"work-contracts").glob("*/admission/plan-*.json"))


def test_claim_drift_cannot_open_new_budget_after_original_admission(prepared,monkeypatch):
    p=prepared;task_root,storage,raw,events=factory_ports(p,monkeypatch)
    configuration.build_root_work_factory(task_root,p.task,git=trusted_git(p.root),claimed_identity=p.identity)
    original_count=events.count("budget-port-double")
    wrong=replace(p.identity,run_token="different-claim")
    with pytest.raises(WorkContractError,match="claim or route"):
        configuration.build_root_work_factory(task_root,p.task,git=trusted_git(p.root),claimed_identity=wrong)
    assert events.count("budget-port-double")==original_count
    original=configuration.original_derived_children(task_root,p.task,identity=p.identity)
    assert original["identity"]==p.identity.to_json()


def test_cold_replay_missing_original_parent_never_downgrades_existing_child_policy(prepared,monkeypatch):
    p=prepared;root=p.tmp/"replay";root.mkdir(mode=0o700)
    import agent_completion_evidence as completion
    monkeypatch.setattr("herdr.host_configuration.read_canonical_parent",lambda *a:None)
    parent=SimpleNamespace(parent_task_id=None, repo=p.task['repo'], id=p.task['id'], run_token=p.task['run_token'], canonical_parent=None)
    scheduler=SimpleNamespace(_tasks={"root":parent},ownership_parent=p.identity)
    assert completion.child_completion_for_replay(root,scheduler) is None
    assert not (root/"verification").exists()
    store=store_for(root,p.task);store.publish("plan",digest(binding(p.task)),parent_plan(p))
    freeze_derived_child_contracts(root,p.task,admission(p))
    before={x.name:x.read_bytes() for x in store.root.iterdir() if x.is_file()}
    with pytest.raises(EvidenceError,match="original canonical parent"):
        completion.child_completion_for_replay(root,scheduler)
    assert before=={x.name:x.read_bytes() for x in store.root.iterdir() if x.is_file()}


def test_actual_worker_cached_factory_rechecks_route_before_session_or_child_effect(prepared,monkeypatch):
    p=prepared;task_root,storage,raw,events=factory_ports(p,monkeypatch)
    factory=configuration.build_root_work_factory(task_root,p.task,git=trusted_git(p.root),claimed_identity=p.identity)
    worker=Path(__file__).resolve().parents[2]/"agent-stack/bin/agent-task-worker"
    tree=ast.parse(worker.read_bytes());names={"_root_work_factory","_task_session_identity","_claimed_root_identity"}
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    scope={"hashlib":hashlib,"EvidenceError":EvidenceError,"ROOT":task_root,
        "HOST_WORK_CONTRACT_FACTORY":None,"HOST_WORK_FACTORIES":{digest(binding(p.task)):factory}}
    exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(worker),"exec"),scope)
    assert scope["_root_work_factory"](p.task) is factory
    before=list(events);changed=deepcopy(p.task);changed["routing"]["selected_agent"]="other-coordinator"
    with pytest.raises(WorkContractError,match="grant changed"):
        scope["_root_work_factory"](changed)
    assert events==before and scope["HOST_WORK_FACTORIES"][digest(binding(p.task))] is factory


@pytest.mark.parametrize("length",[30,32,33])
def test_template_role_matches_actual_canonical_wire_parser(prepared,length):
    from herdr.delegation_tool import _arguments
    from herdr.security import SecurityError
    p=prepared;data=deepcopy(p.definition);item=data["managed_children"]["children"][0];item["role"]="r"*length
    wire={"key":item["key"],"role":item["role"],"objective":item["objective"],"prompt":"bounded actual wire",
        "tool":item["tools"],"permission":item["permissions"],"cwd":str(p.child),"ownership":item["ownership"],
        "model":"fixture-model","fallback_model":None}
    if length>32:
        with pytest.raises((WorkContractError,SecurityError)):
            derived.derive(data,p.task,p.identity)
        with pytest.raises(SecurityError):_arguments(wire)
    else:
        assert derived.derive(data,p.task,p.identity) and _arguments(wire)["role"]==item["role"]


@pytest.mark.parametrize("field",["tools","permissions"])
@pytest.mark.parametrize("count",[63,64,65])
def test_template_scope_count_matches_actual_canonical_wire_parser(prepared,field,count):
    from herdr.delegation_tool import _arguments
    from herdr.security import SecurityError
    p=prepared;data=deepcopy(p.definition);task=deepcopy(p.task);item=data["managed_children"]["children"][0]
    original=list(item[field]);item[field]=sorted(original+["extra-"+str(i) for i in range(count-len(original))])
    task["parent_"+field]=sorted(set(task["parent_"+field])|set(item[field]))
    item["work_definition"]["planning"][field]=list(item[field])
    wire={"key":item["key"],"role":item["role"],"objective":item["objective"],"prompt":"bounded actual wire",
        "tool":item["tools"],"permission":item["permissions"],"cwd":str(p.child),"ownership":item["ownership"],
        "model":"fixture-model","fallback_model":None}
    if count>64:
        with pytest.raises(SecurityError):_arguments(wire)
        with pytest.raises(SecurityError):derived.derive(data,task,p.identity)
    else:assert _arguments(wire) and derived.derive(data,task,p.identity)


@pytest.mark.parametrize("field",["tools","permissions"])
@pytest.mark.parametrize("name",["x"*128,"x"*129,"bad\x00name"])
def test_template_scope_name_matches_actual_canonical_wire_parser(prepared,field,name):
    from herdr.delegation_tool import _arguments
    from herdr.security import SecurityError
    p=prepared;data=deepcopy(p.definition);task=deepcopy(p.task);item=data["managed_children"]["children"][0]
    item[field]=sorted([*item[field],name]);task["parent_"+field]=sorted([*task["parent_"+field],name])
    item["work_definition"]["planning"][field]=list(item[field])
    wire={"key":item["key"],"role":item["role"],"objective":item["objective"],"prompt":"bounded actual wire",
        "tool":item["tools"],"permission":item["permissions"],"cwd":str(p.child),"ownership":item["ownership"],
        "model":"fixture-model","fallback_model":None}
    if len(name)>128 or "\x00" in name:
        with pytest.raises(SecurityError):_arguments(wire)
        with pytest.raises((SecurityError,WorkContractError)):derived.derive(data,task,p.identity)
    else:assert _arguments(wire) and derived.derive(data,task,p.identity)


def test_legacy_static_child_and_cold_admission_unchanged_without_parent_template(prepared,monkeypatch):
    p=prepared;leaf=deepcopy(p.definition);leaf.pop("managed_children")
    task_root,storage,raw,events=factory_ports(p,monkeypatch,leaf)
    configuration.build_root_work_factory(task_root,p.task,git=trusted_git(p.root))
    spec="f"*64;definition=deepcopy(p.definition["managed_children"]["children"][0]["work_definition"])
    raw["work_contracts"]["plans"][spec]=definition
    task={"id":"legacy-static-child","run_token":"old-static-run","fencing_token":8,"attempt_id":1,
        "idempotency_key":"legacy-key","repo":p.task["repo"],"parent_task_id":p.task["id"],
        "parent_run_token":p.task["run_token"],"workspace":str(p.child),"work_contract_version":1,
        "work_budget_version":1,"completion_plan":{"base_sha":p.plan.base_sha}}
    monkeypatch.setattr("herdr.host_configuration.read_canonical_parent",lambda *args:deepcopy(p.task))
    actual=configuration.build_root_work_factory(task_root,task,git=trusted_git(p.child),spec_sha256=spec)
    expected={"version":1,"identity":binding(task),"spec_sha256":spec,"definition":definition,
              "environment":raw["work_contracts"]["environment"]}
    assert actual.host_admission==expected and "derived_parent_admission_sha256" not in task
    directory=storage/"work-contracts"/digest(binding(task))/"admission"
    before={x.name:x.read_bytes() for x in directory.iterdir() if x.is_file()}
    raw.pop("work_contracts");shutil.rmtree(p.root)
    cold=configuration.build_root_work_factory(task_root,task,recovery=True,spec_sha256=spec)
    assert cold.host_admission==expected
    assert before=={x.name:x.read_bytes() for x in directory.iterdir() if x.is_file()}


def root_write_helper():
    source = Path(__file__).resolve().parents[2] / 'agent-stack/bin/agent-task-worker'
    tree = ast.parse(source.read_bytes())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_root_self_write_pins')
    scope = {'Path': Path}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
    return scope[node.name]


def test_parent_self_pins_use_original_host_scope_and_keep_logical_delegation(prepared):
    from herdr.private_mount_plan import PinnedLaunchPath
    p = prepared
    pin = PinnedLaunchPath(p.root, directory=True)
    grant = SimpleNamespace(process=SimpleNamespace(enabled=False), tool_rules=('logical ceiling unchanged',))
    launch = SimpleNamespace(identity=p.identity, private_profile_snapshot=object(), grant=grant,
                             mount=SimpleNamespace(private_workspace_pin=pin))
    try:
        pins = root_write_helper()(SimpleNamespace(host_admission=admission(p)), p.task, launch)
        try:
            assert pins.roots == (str(p.root / 'result.py'),)
            pins.verify()
            assert grant.tool_rules == ('logical ceiling unchanged',)
        finally:
            pins.close()
    finally:
        pin.close()


@pytest.mark.parametrize('fault', ['spec', 'identity', 'process', 'profile', 'subtree', 'child-overlap'])
def test_parent_self_pins_reject_authority_drift_and_child_overlap(prepared, fault):
    p = prepared
    old = admission(p)
    grant = SimpleNamespace(process=SimpleNamespace(enabled=fault == 'process'))
    launch = SimpleNamespace(identity=p.identity, private_profile_snapshot=None if fault == 'profile' else object(),
                             grant=grant, mount=SimpleNamespace(private_workspace_pin=None))
    if fault == 'spec': old['spec_sha256'] = '0' * 64
    elif fault == 'identity': old['identity']['run_token'] = 'foreign'
    elif fault in {'subtree', 'child-overlap'}:
        old['definition']['files'] = [{'path': '.stage3-child/repo/result.py' if fault == 'child-overlap' else 'result.py',
                                       'subtree': fault == 'subtree'}]
        old['managed_children'] = derived.derive(old['definition'], p.task, p.identity)
    with pytest.raises((RuntimeError, WorkContractError)):
        root_write_helper()(SimpleNamespace(host_admission=old), p.task, launch)


@pytest.mark.parametrize('fault', [None, 'fence', 'expired', 'ownership', 'admission', 'parent', 'inode', 'scope', 'key', 'model', 'idempotency'])
def test_original_child_context_rechecks_claim_and_owned_pins_at_seal(prepared, monkeypatch, fault):
    """Host admission/proof/lease readers are doubles; file pins and ownership parsing are real."""
    from herdr.private_mount_plan import PinnedLaunchPath
    from herdr.owned_write_mounts import OwnedWritePins
    from herdr.child_ownership import OwnershipError
    from herdr.policy_launch import PreparedPolicyLaunch
    from herdr.security import SecurityError
    from herdr.scheduler import Lease, AuditLog
    from herdr.taskgraph import LifecycleState
    import herdr.host_configuration as hc
    import herdr.policy_launch as pl
    import agent_durable_children as dc
    p = prepared; original = admission(p); spec, row = next(iter(original['managed_children']['children'].items()))
    own = ChildOwnership.from_json(p.definition['managed_children']['children'][0]['ownership'])
    pin = PinnedLaunchPath(p.child, directory=True)
    try:
        with OwnedWritePins(own, pin) as pins: mounted = tuple(pins.evidence())
        ci = p.child_identity
        rec = SimpleNamespace(node=SimpleNamespace(id=ci.task_id, model_policy=row['model_policy'], **{k: row['scope'][k]
            for k in ('objective', 'role', 'tools', 'permissions')}), id=ci.task_id,
            run_token=ci.run_token, delegation_key=row['key'], idempotency_key='child-key', attempts=1, fencing_token=ci.fencing_token,
            repo=p.task['repo'], issue=str(p.task['issue']), parent_task_id=ci.parent_task_id,
            parent_agent_id=ci.parent_agent_id, parent_run_token=p.task['run_token'], agent_id=ci.agent_id,
            execution_sandbox_attestation=None, execution_agent=ci.agent_id, execution_pane='child-pane',
            execution_marker='child-marker', execution_sandbox_verified=False,
            worktree_identity=row['scope']['worktree_identity'], ownership=own, owned_write_mounts=mounted,
            state=LifecycleState.RUNNING, lease=Lease(ci.task_id, ci.agent_id, 'host', ci.fencing_token, 1000))
        from herdr.child_evidence import child_task
        task = child_task(rec)
        task.update(workspace=str(p.child), delegation_key=row['key'], model_policy=row['model_policy'],
                    derived_parent_admission_sha256=digest(original['managed_children']))
        state = p.tmp / 'state'; state.mkdir(); (state / 'child-ownership').mkdir()
        factory = SimpleNamespace(host_task=task, task_store_root=state, host_configuration_path=state/'host.json',
            host_admission={'spec_sha256': spec, 'definition': row['work_definition'], 'environment': original['environment']},
            audit_log=AuditLog(state/'audit.jsonl'))
        parent = deepcopy(p.task); parent['execution_session'] = {'sandbox_pid': 123,
            'invocation_policy': {}, 'sandbox_attestation': {}}
        pg = replace(synthetic_grant(p.root, tools=('write_file',)), identity=p.identity)
        cg = replace(synthetic_grant(p.child, tools=('write_file',)), identity=ci, parent_grant_hash=pg.hash,
            tool_rules=tuple(replace(r, allowed_roots=(str(p.child/'result.py'),))
                             for r in synthetic_grant(p.child, tools=('write_file',)).tool_rules))
        launch = object.__new__(PreparedPolicyLaunch)
        launch._parent=pg; launch.grant=cg; launch._delegated_writes=None; launch._private_key=object(); launch.sealed=None
        launch.mount=SimpleNamespace(private_workspace_pin=pin)
        fresh = deepcopy(original)
        monkeypatch.setattr(hc, 'read_canonical_parent', lambda *a: parent)
        monkeypatch.setattr(configuration, '_original_work_admission', lambda *a: (state, fresh))
        verified = [pg]
        monkeypatch.setattr(pl, 'verify_retained_policy_evidence', lambda *a, **k: verified[0])
        scheduler = SimpleNamespace(_tasks={ci.task_id: rec}, current_time=lambda: 1,
                                    _require_current_ownership=lambda r: None)
        monkeypatch.setattr(dc, 'replay_host_scheduler', lambda *a: scheduler)
        configuration._bind_original_delegated_writes(factory, launch)
        authority = launch._delegated_writes
        if fault == 'key': rec.delegation_key = 'foreign'
        elif fault == 'model': rec.node.model_policy = {'model': 'foreign', 'fallback_model': None}
        elif fault == 'idempotency': rec.idempotency_key = 'foreign'
        elif fault == 'fence': rec.fencing_token += 1
        elif fault == 'expired': rec.lease = replace(rec.lease, lease_until=0)
        elif fault == 'ownership': rec.ownership = replace(own, handoff_ref='foreign')
        elif fault == 'admission': fresh['spec_sha256'] = '0'*64
        elif fault == 'parent': verified[0] = replace(pg, grant_id='foreign')
        elif fault == 'inode':
            (p.child/'result.py').rename(p.child/'old-result.py'); (p.child/'result.py').write_text('replacement')
        elif fault == 'scope': cg = replace(cg, tool_rules=tuple(replace(r, allowed_roots=(str(p.child),)) for r in cg.tool_rules))
        if fault is None:
            assert authority.validated_roots(cg, pg) == (str(p.child/'result.py'),)
            authority.record_sealed(cg, pg)
            event, = factory.audit_log.replay()
            assert event['grant_sha256'] == cg.hash and event['parent_grant_sha256'] == pg.hash
            assert event['admission_sha256'] == digest(original) and event['ownership_sha256'] == own.hash
        else:
            with pytest.raises((SecurityError, WorkContractError, OwnershipError, OSError)):
                authority.validated_roots(cg, pg)
            assert factory.audit_log.replay() == []
    finally:
        pin.close()


def test_original_partition_excludes_only_admitted_child_across_baseline_and_cold_recovery(prepared):
    from herdr.private_mount_plan import PinnedLaunchPath
    from herdr.work_cycle import SnapshotPartition, WorkCycle, tree_snapshot
    from herdr.scheduler import AuditLog
    from tests.herdr.test_work_cycle import runner
    p=prepared; pin=PinnedLaunchPath(p.root,directory=True)
    pg=replace(synthetic_grant(p.root,tools=('write_file',)),identity=p.identity)
    try: partition=SnapshotPartition.capture(admission(p),p.task,p.identity,pin,pg)
    finally: pin.close()
    plan=replace(p.plan,grant_sha256=pg.hash,snapshot_partition=partition)
    assert WorkPlan.from_json(plan.to_json()).hash==plan.hash and plan.to_json()['version']==4
    with pytest.raises((WorkContractError,OSError)):
        tree_snapshot(p.root,git=trusted_git(p.root))
    before=tree_snapshot(p.root,git=trusted_git(p.root),partition=partition)
    assert 'result.py' in before and 'foreign.txt' in before
    assert not any(x.startswith('.stage3-child/') for x in before)
    log=AuditLog(p.tmp/'partition-audit.jsonl')
    cycle=WorkCycle(plan,p.root,log,git=trusted_git(p.root));cycle.start(runner)
    (p.child/'result.py').write_text('child own change')
    assert tree_snapshot(p.root,git=trusted_git(p.root),partition=partition)==before
    cold=WorkCycle(WorkPlan.from_json(plan.to_json()),p.root,log,git=trusted_git(p.root))
    cold.verify_scope()
    with (p.root/'.git/info/exclude').open('a') as out: out.write('ignored-foreign.txt\n')
    (p.root/'ignored-foreign.txt').write_text('foreign ignored bytes are still evidence')
    assert 'ignored-foreign.txt' in tree_snapshot(p.root,git=trusted_git(p.root),partition=partition)
    with pytest.raises(WorkContractError,match='escaped approved work scope'):cold.verify_scope()


@pytest.mark.parametrize('fault',['identity','spec','ownership','child-overlap','rename','symlink','mount'])
def test_partition_rejects_original_admission_or_named_inode_alias_drift(prepared,monkeypatch,fault):
    from herdr.private_mount_plan import PinnedLaunchPath
    from herdr.work_cycle import SnapshotPartition, tree_snapshot
    from herdr.security import SecurityError
    from herdr import owned_write_mounts
    p=prepared; old=admission(p); pin=PinnedLaunchPath(p.root,directory=True)
    pg=replace(synthetic_grant(p.root,tools=('write_file',)),identity=p.identity)
    try: partition=SnapshotPartition.capture(old,p.task,p.identity,pin,pg)
    finally: pin.close()
    if fault in {'identity','spec','ownership'}:
        if fault=='identity':old['identity']['run_token']='foreign'
        elif fault=='spec':old['spec_sha256']='0'*64
        else:next(iter(old['managed_children']['children'].values()))['ownership_sha256']='0'*64
        pin=PinnedLaunchPath(p.root,directory=True)
        try:
            with pytest.raises((SecurityError,WorkContractError,OSError)):
                SnapshotPartition.capture(old,p.task,p.identity,pin,pg)
        finally:pin.close()
        return
    if fault=='child-overlap':
        with pytest.raises(WorkContractError,match='overlaps parent'):
            replace(p.plan,grant_sha256=pg.hash,files=(type(p.plan.files[0])('.stage3-child/repo/result.py'),),snapshot_partition=partition)
        return
    if fault in {'rename','symlink'}:
        original=p.child.with_name('original');p.child.rename(original)
        if fault=='rename':p.child.mkdir()
        else:p.child.symlink_to(original,target_is_directory=True)
    else:
        actual=owned_write_mounts._mount_id
        monkeypatch.setattr(owned_write_mounts,'_mount_id',lambda fd:actual(fd)+1)
    with pytest.raises((SecurityError,WorkContractError,OSError)):
        tree_snapshot(p.root,git=trusted_git(p.root),partition=partition)


def test_partition_cannot_hide_parent_tracked_or_parent_writable_child_data(prepared):
    from herdr.private_mount_plan import PinnedLaunchPath
    from herdr.work_cycle import SnapshotPartition, tree_snapshot
    p=prepared; pin=PinnedLaunchPath(p.root,directory=True)
    grant=replace(synthetic_grant(p.root,tools=('write_file',)),identity=p.identity)
    try:
        for writable in (p.root,p.child,p.child/'result.py'):
            broad=replace(grant,runtime_assurance=replace(grant.runtime_assurance,writable_roots=(str(writable),)))
            with pytest.raises(WorkContractError,match='parent writable'):
                SnapshotPartition.capture(admission(p),p.task,p.identity,pin,broad)
        partition=SnapshotPartition.capture(admission(p),p.task,p.identity,pin,grant)
    finally:pin.close()
    actual=trusted_git(p.root)
    def indexed(args):
        if args==['ls-files','-z','--cached']:return actual(args)+'.stage3-child/repo/tracked.py\0'
        return actual(args)
    with pytest.raises(WorkContractError,match='parent tracked inventory'):
        tree_snapshot(p.root,git=indexed,partition=partition)
    check=replace(p.plan.checks[0],protected_inputs=(('.stage3-child/repo/result.py','a'*64),))
    with pytest.raises(WorkContractError,match='protected oracle input'):
        replace(p.plan,grant_sha256=grant.hash,checks=(check,),snapshot_partition=partition)
