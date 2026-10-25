"""Admission of an explicitly reviewed Git base; no provider or auth calls."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"agent-stack/bin"))
import agent_completion_evidence as completion
from herdr import work_configuration as config
from herdr.work_cycle import WorkContractError

@pytest.fixture
def reviewed(tmp_path,monkeypatch):
    queue=tmp_path/"tasks";queue.mkdir()
    workspace=tmp_path/"workspace";workspace.mkdir()
    task={"id":"reviewed-base-node","run_token":"r"*32,"attempt_id":1,"attempts":1,
          "fencing_token":1,"idempotency_key":"unit-key","repo":"Bbambaaamm/herdr",
          "issue":77,"kind":"coding","completion_kind":"coding","workspace":str(workspace),
          "prompt":"Synthetic reviewed-base unit contract","spec_hash":"a"*64,
          "work_contract_version":1,"work_budget_version":1,"completion_base_version":1}
    definition={"base_sha":"b"*40,"completion_base":{"version":1,
                "remote_ref":"refs/remotes/origin/feat/issue77-machine-city-complete"}}
    raw={"task_store_root":str(queue),"work_contracts":{"version":1,"environment":{},
          "plans":{completion.spec_digest(task):definition},"review_records":{}}}
    monkeypatch.setattr(config,"_read_configuration",lambda path:deepcopy(raw))
    return queue,workspace,task,definition,raw

def test_protected_review_selects_exact_feature_ref(reviewed):
    root,_,task,definition,_=reviewed
    assert config.approved_completion_base(root,task)==(
        "refs/remotes/origin/feat/issue77-machine-city-complete","b"*40)

@pytest.mark.parametrize("ref",["HEAD","origin/main","refs/heads/main",
    "refs/remotes/upstream/main","refs/remotes/origin/../main",
    "refs/remotes/origin/a..b","refs/remotes/origin/a//b",
    "refs/remotes/origin/a.lock","refs/remotes/origin/.private",
    "refs/remotes/origin/main\n--output=/tmp/invalid"])
def test_noncanonical_or_expression_refs_rejected(reviewed,ref):
    root,_,task,definition,_=reviewed
    definition["completion_base"]["remote_ref"]=ref
    with pytest.raises(WorkContractError):config.approved_completion_base(root,task)

@pytest.mark.parametrize("field,value",[
    ("completion_base_version",True),("completion_base_version",2),
    ("work_contract_version",None),("work_contract_version",True),
    ("work_budget_version",None),("work_budget_version",True)])
def test_version_marker_is_strict_before_selection(reviewed,field,value):
    root,_,task,definition,raw=reviewed
    task[field]=value
    raw["work_contracts"]["plans"]={completion.spec_digest(task):definition}
    with pytest.raises(WorkContractError):config.approved_completion_base(root,task)

def test_scope_lookup_uses_exact_specification(reviewed):
    root,_,task,_,_=reviewed
    task["prompt"]="Different unapproved unit specification"
    with pytest.raises(WorkContractError):config.approved_completion_base(root,task)

def test_queue_binding_cannot_be_moved(reviewed,tmp_path):
    _,_,task,_,_=reviewed
    different=tmp_path/"different";different.mkdir()
    with pytest.raises(WorkContractError):config.approved_completion_base(different,task)

@pytest.mark.parametrize("mutation",["missing","unknown-field","bad-sha","bad-version"])
def test_invalid_protected_base_rejected(reviewed,mutation):
    root,_,task,definition,_=reviewed
    if mutation=="missing":definition.pop("completion_base")
    elif mutation=="unknown-field":definition["completion_base"]["self_approved"]=True
    elif mutation=="bad-sha":definition["base_sha"]="not-a-commit"
    else:definition["completion_base"]["version"]=True
    with pytest.raises(WorkContractError):config.approved_completion_base(root,task)

def test_base_marker_is_part_of_spec_digest(reviewed):
    _,_,task,_,_=reviewed
    with_marker=completion.spec_digest(task)
    legacy=dict(task);legacy.pop("completion_base_version")
    assert completion.spec_digest(legacy)!=with_marker

def freeze_ports(monkeypatch,expected_git):
    calls=[];published=[]
    class Store:
        def read(self,*args):raise completion.EvidenceMissing("unit absent")
        def publish(self,kind,key,value):published.append(deepcopy(value))
    monkeypatch.setattr(completion,"store_for",lambda *args:Store())
    def git(argv,**kwargs):
        calls.append(argv)
        return SimpleNamespace(stdout=expected_git+"\n",returncode=0)
    monkeypatch.setattr(completion.subprocess,"run",git)
    monkeypatch.setattr(completion,"workflow_blob",lambda *args:"c"*40)
    monkeypatch.setattr(completion,"collect_checks",lambda *args,**kwargs:{})
    monkeypatch.setattr(completion,"freeze_child_completion_contracts",lambda *args:None)
    return calls,published

def test_freeze_uses_protected_ref_and_preserves_exact_base(reviewed,monkeypatch):
    root,_,task,_,_=reviewed
    calls,published=freeze_ports(monkeypatch,"b"*40)
    completion.freeze_plan(root,task)
    assert calls and calls[0][-3:]==["rev-parse","--verify",
        "refs/remotes/origin/feat/issue77-machine-city-complete^{commit}"]
    assert len(published)==1 and published[0]["base_sha"]=="b"*40

def test_moved_reviewed_ref_is_denied_before_plan_publication(reviewed,monkeypatch):
    root,_,task,_,_=reviewed
    calls,published=freeze_ports(monkeypatch,"d"*40)
    with pytest.raises(completion.EvidenceError):completion.freeze_plan(root,task)
    assert calls and published==[]

def test_legacy_origin_main_path_remains_unchanged(reviewed,monkeypatch):
    root,_,task,_,_=reviewed
    task.pop("completion_base_version")
    calls,published=freeze_ports(monkeypatch,"e"*40)
    completion.freeze_plan(root,task)
    assert calls[0][-2:]==["rev-parse","origin/main"]
    assert len(published)==1 and published[0]["base_sha"]=="e"*40

def actual_git_workspace(workspace):
    import os,subprocess
    def git(*args):
        return subprocess.run(["/usr/bin/git","-c","core.hooksPath=/dev/null","-C",
                               str(workspace),*args],capture_output=True,text=True,check=True).stdout.strip()
    git("init","-q")
    git("config","user.name","Unit Test")
    git("config","user.email","unit@example.invalid")
    (workspace/"value.txt").write_text("first\n")
    git("add","value.txt");git("commit","-qm","first")
    return git,git("rev-parse","HEAD")

def test_real_git_accepts_reviewed_feature_without_origin_main(reviewed,monkeypatch):
    root,workspace,task,definition,_=reviewed
    real_run=completion.subprocess.run
    git,base=actual_git_workspace(workspace)
    definition["base_sha"]=base
    git("update-ref",definition["completion_base"]["remote_ref"],base)
    _,published=freeze_ports(monkeypatch,"unused")
    monkeypatch.setattr(completion.subprocess,"run",real_run)
    completion.freeze_plan(root,task)
    assert len(published)==1 and published[0]["base_sha"]==base

def test_real_git_ref_movement_cannot_retarget_approval(reviewed,monkeypatch):
    root,workspace,task,definition,_=reviewed
    real_run=completion.subprocess.run
    git,base=actual_git_workspace(workspace)
    definition["base_sha"]=base
    (workspace/"value.txt").write_text("second\n")
    git("add","value.txt");git("commit","-qm","second")
    git("update-ref",definition["completion_base"]["remote_ref"],git("rev-parse","HEAD"))
    _,published=freeze_ports(monkeypatch,"unused")
    monkeypatch.setattr(completion.subprocess,"run",real_run)
    with pytest.raises(completion.EvidenceError):completion.freeze_plan(root,task)
    assert published==[]

def test_protected_selection_does_not_use_a_task_supplied_ref(reviewed):
    root,_,task,definition,_=reviewed
    task["completion_base_ref"]="refs/remotes/origin/unreviewed"
    assert config.approved_completion_base(root,task)[0]==definition["completion_base"]["remote_ref"]

def configured_base(tmp_path,monkeypatch):
    from dataclasses import asdict
    from herdr.evidence import digest
    from herdr.work_budget import BudgetAllocation,BudgetLimits
    from tests.herdr.test_reviewed_graph_host import configured
    raw,task,definition,graph,grant,git=configured(tmp_path,monkeypatch)
    task.update(completion_base_version=1,work_budget_version=1)
    definition["completion_base"]={"version":1,"remote_ref":"refs/remotes/origin/unit-review"}
    key=digest({"unit-only-reviewed-base":str(tmp_path)})
    allocation=BudgetAllocation(key,grant.identity.consumer,key,key,"a"*64,
        BudgetLimits(1000,10000,1,1,0,1,1,1,1,max_implementation_attempts=1,attempt_override_reference="a"*64))
    definition["budget"]={"version":1,"allocation":asdict(allocation),"ancestors":[],"model_quotes":[]}
    raw["work_contracts"]["plans"]={completion.spec_digest(task):definition}
    return raw,task,definition,graph,grant,git

def test_real_factory_preserves_graph_and_budget_and_filters_base_metadata(tmp_path,monkeypatch):
    from herdr.taskgraph import PersistentTaskGraph
    from tests.herdr.test_reviewed_graph_host import graph_path
    raw,task,definition,graph,grant,git=configured_base(tmp_path,monkeypatch)
    factory=config.build_root_work_factory(Path(raw["task_store_root"]),task,git=git)
    persisted,_=PersistentTaskGraph(graph_path(raw,task)).replay()
    assert persisted.graph_hash()==graph.graph_hash()
    assert factory.budget_authority is not None
    plan=factory.approve(identity=grant.identity,workspace=Path(task["workspace"]),
        grant=grant,spec_sha256=completion.spec_digest(task))
    assert plan.base_sha==definition["base_sha"]
    assert "completion_base" not in plan.to_json()

def test_unapproved_base_stops_before_graph_and_budget_publication(tmp_path,monkeypatch):
    from tests.herdr.test_reviewed_graph_host import graph_path
    raw,task,definition,_,_,git=configured_base(tmp_path,monkeypatch)
    definition["completion_base"]["remote_ref"]="HEAD"
    with pytest.raises(WorkContractError):
        config.build_root_work_factory(Path(raw["task_store_root"]),task,git=git)
    assert not graph_path(raw,task).exists()
    assert not list((Path(raw["storage"])/"work-budget").glob("*/events.jsonl"))
