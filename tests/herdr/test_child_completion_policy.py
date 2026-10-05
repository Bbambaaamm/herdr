"""Actual frozen host child policy/provider, with no model or runtime execution.

Git and ArtifactRef use the real fixture; source-collector and launch evidence
are explicit transport fixtures here, with physical suites kept separate.
"""
import copy
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from herdr.child_completion_policy import (freeze_policy, build_authority, authority_for_parent,
                                           validate_contracts, policy_key)
from herdr.child_evidence import ChildCompletionAuthority, child_spec, child_task
from herdr.evidence import EvidenceError, EvidenceMissing, digest, binding
from herdr.host_configuration import read_canonical_parent
from herdr.policy_launch import HostPolicyLaunchFactory
from herdr.security import InvocationIdentity, SecurityError
from tests.herdr.test_child_evidence import artifact_fixture

BIN=Path(__file__).resolve().parents[2]/"agent-stack/bin"
sys.path.insert(0,str(BIN))
import agent_completion_evidence as host

def fixture(tmp_path,monkeypatch,kind="coding"):
    rec,result,_,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    rec.parent_run_token="parent-run"
    scope={"version":1,"files":[{"path":"result.txt","subtree":False}],
           "acceptance_ids":["functional"],"shared_contract_keys":[]}
    criteria=scope if kind=="coding" else (
        {"schema":"research-report-v1","report_path":"reports/research/result.json","sections":["findings"]}
        if kind=="research" else {"schema":"review-report-v1","report_path":"reports/review/result.json",
                                 "target_commit":result["artifact"]["base_sha"]})
    contracts={"version":1,"base_sha":result["artifact"]["base_sha"],
               "children":{child_spec(rec):{"kind":kind,"criteria":criteria}}}
    task={"id":"parent","run_token":"parent-run","idempotency_key":"parent-key","attempt_id":0,
          "fencing_token":9,"repo":"Bbambaaamm/herdr","kind":"github_root_orchestration",
          "workspace":str(path),"worktree_root":str(path.parent),"child_completion_contracts":contracts}
    env={"collector":"github-api-v1","ci_workflow_blob_sha":"f"*40,
         "ci_workflow_id":367993725,"github_actions_app_id":15368}
    baseline=[{"name":name,"head_sha":contracts["base_sha"],"status":"missing"} for name in host.CHECK_APPS]
    policy=freeze_policy(store,task,parent_spec_hash=host.spec_digest(task),contracts=contracts,
                         environment=env,baseline=baseline)
    return rec,result,store,path,task,policy

@pytest.mark.parametrize("kind",["coding","research","review"])
def test_exact_preapproved_node_kind_freezes_before_any_collector(tmp_path,monkeypatch,kind):
    rec,_,store,_,task,policy=fixture(tmp_path,monkeypatch,kind)
    authority=authority_for_parent(store,task,parent_spec_hash=host.spec_digest(task),
        collector=lambda *a:pytest.fail("predispatch must not collect candidate evidence"))
    assert isinstance(authority,ChildCompletionAuthority)
    authority.prepare(rec)
    plan=store.read("plan",digest(binding(child_task(rec))))
    assert plan["kind"]==kind and plan["base_sha"]==policy["contracts"]["base_sha"]
    assert plan["spec_hash"]==child_spec(rec) and plan["policy_hash"]==policy["policy_hash"]
    assert ("scope_policy" in plan)==(kind=="coding")
    assert plan["required_checks"]==(list(host.CHECK_APPS) if kind=="coding" else ["GitGuardian Security Checks"])
    assert plan["identity"]==binding(child_task(rec))

@pytest.mark.parametrize("changed",["objective","role","tools","permissions","worktree","parent-run"])
def test_unapproved_child_cannot_reinterpret_host_policy(tmp_path,monkeypatch,changed):
    rec,_,store,path,task,policy=fixture(tmp_path,monkeypatch)
    authority=build_authority(store,policy,collector=lambda *a:pytest.fail("before candidate collector"))
    if changed=="objective":rec.node.objective="another task"
    elif changed=="role":rec.node.role="research"
    elif changed=="tools":rec.node.tools=("terminal",)
    elif changed=="permissions":rec.node.permissions=("production-write",)
    elif changed=="worktree":rec.worktree_identity=str(path)+"|0:1"
    else:rec.parent_run_token="different-run"
    before=set(store.root.iterdir())
    with pytest.raises(EvidenceError):authority.prepare(rec)
    assert set(store.root.iterdir())==before

def test_missing_real_source_evidence_does_not_become_verified(tmp_path,monkeypatch):
    rec,result,store,_,_,policy=fixture(tmp_path,monkeypatch)
    result["evidence"]=[{"producer":"ci","passed":True,"review":"PASS"}]
    authority=build_authority(store,policy,collector=lambda *a:(_ for _ in ()).throw(EvidenceMissing("CI pending")))
    authority.prepare(rec)
    # A mandatory actual scope report is required before even consulting CI.
    with pytest.raises(EvidenceError):authority.verify(rec,result)
    assert not list(store.root.glob("accepted-*"))

def test_parent_restart_cannot_change_frozen_contracts(tmp_path,monkeypatch):
    _,_,store,_,task,policy=fixture(tmp_path,monkeypatch)
    changed=copy.deepcopy(task)
    next(iter(changed["child_completion_contracts"]["children"].values()))["kind"]="research"
    with pytest.raises(EvidenceError):authority_for_parent(store,changed,
        parent_spec_hash=host.spec_digest(changed),collector=lambda *a:None)
    assert store.read("plan",policy_key(task["repo"],task["id"],task["run_token"]))==policy

@pytest.mark.parametrize("fault",["schema-bool","extra","missing-criteria","role-kind","too-many","bad-base"])
def test_closed_bounded_contracts_have_no_model_approval_fields(tmp_path,monkeypatch,fault):
    *_,task,_=fixture(tmp_path,monkeypatch)
    value=copy.deepcopy(task["child_completion_contracts"])
    if fault=="schema-bool":value["version"]=True
    elif fault=="extra":value["approved_by_model"]=True
    elif fault=="missing-criteria":next(iter(value["children"].values())).pop("criteria")
    elif fault=="role-kind":next(iter(value["children"].values()))["kind"]="reader"
    elif fault=="too-many":value["children"]={f"{n:064x}":{"kind":"coding","criteria":next(iter(value["children"].values()))["criteria"]} for n in range(129)}
    else:value["base_sha"]="abbreviated"
    with pytest.raises(EvidenceError):validate_contracts(value)

def test_actual_root_provider_constructs_same_durable_child_authority(tmp_path,monkeypatch):
    rec,_,store,_,task,_=fixture(tmp_path,monkeypatch)
    root=store.root.parent
    running=root/"running";running.mkdir()
    task_file=running/"parent.json";task_file.write_text(json.dumps(task));task_file.chmod(0o600)
    identity=InvocationIdentity("github:"+task["repo"],"parent-agent","coordinator","coordinator-task",
                               task["id"],task["run_token"],task["fencing_token"])
    factory=HostPolicyLaunchFactory.__new__(HostPolicyLaunchFactory)
    # Authenticated launch transport fixture, not a physical grant assertion.
    factory.parent_grant=SimpleNamespace(identity=identity)
    factory.task_store_root=root
    factory.verified_parent_task=task
    monkeypatch.setattr(host,"collect_github",lambda *a:pytest.fail("preparation is not result collection"))
    args={"task_id":"parent","run_token":"parent-run"}
    authority=host.child_completion_for_root(task_file,args,factory=factory)
    authority.prepare(rec)
    parent_rec=SimpleNamespace(id="parent",run_token="parent-run",parent_task_id=None)
    replay=host.child_completion_for_replay(root,SimpleNamespace(_tasks={"parent":parent_rec},
                                                               ownership_parent=identity))
    assert isinstance(replay,ChildCompletionAuthority)
    replay.prepare(rec)
    assert len(list(store.root.glob("plan-*")))==2
    # Stale parent/attempt cannot borrow the accepted source port.
    task["fencing_token"]=10
    with pytest.raises(EvidenceError):host.child_completion_for_root(task_file,args,factory=factory)

@pytest.mark.parametrize("fault",["symlink","hardlink","public","duplicate","ambiguous"])
def test_canonical_parent_source_rejects_untrusted_or_ambiguous_files(tmp_path,fault):
    root=tmp_path/"tasks";root.mkdir(mode=0o700)
    running=root/"running";running.mkdir()
    path=running/"parent.json"
    body='{"id":"parent","run_token":"run"}'
    path.write_text(body);path.chmod(0o600)
    if fault=="symlink":
        target=root/"original";path.rename(target);path.symlink_to(target)
    elif fault=="hardlink":os.link(path,root/"linked")
    elif fault=="public":path.chmod(0o644)
    elif fault=="duplicate":path.write_text('{"id":"parent","run_token":"run","run_token":"run"}')
    else:
        blocked=root/"blocked";blocked.mkdir()
        second=blocked/path.name;second.write_text(body);second.chmod(0o600)
    with pytest.raises((SecurityError,OSError)):read_canonical_parent(root,"parent","run")

def test_root_freeze_reuses_exact_child_policy_before_dispatch(tmp_path,monkeypatch):
    _,_,store,_,task,policy=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(host,"workflow_blob",lambda *a:"f"*40)
    monkeypatch.setattr(host,"collect_checks",lambda *a,**k:{r["name"]:r for r in policy["baseline"]})
    host.freeze_plan(store.root.parent,task)
    assert task["completion_plan"]["kind"]=="control"
    host.freeze_plan(store.root.parent,task)
    task["child_completion_contracts"]["base_sha"]="e"*40
    with pytest.raises(EvidenceError,match="changed"):host.freeze_plan(store.root.parent,task)
