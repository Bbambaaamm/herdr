import hashlib
import json
import os
from contextvars import ContextVar
from dataclasses import replace
from pathlib import Path
import pytest
from herdr.result_submission import ResultSlot, TOOL, TOOLSET, ARGUMENTS, submit, register_result_tool
from herdr.security import InvocationGuard, ToolRule, RiskClass, PolicyDenied, SecurityError
from herdr.hermes_guard import GuardInstallation, _call_digest
from herdr.policy_launch import IDENTITY_ENV
from tests.herdr.test_security import grant, identity
from tests.herdr.test_delegation_tool import Registry

def setup(tmp_path):
    workspace=tmp_path/"workspace";workspace.mkdir()
    result=tmp_path/"private-result.json";result.touch(mode=0o600)
    slot=ResultSlot.bind(result,identity(),"result-key")
    rule=ToolRule(TOOL,RiskClass.RESULT_SUBMISSION,ARGUMENTS,allowed_roots=(str(tmp_path),),
                  requires_sandbox=True,result_slot=slot)
    g=grant(workspace,tools=(TOOL,),rules=(rule,))
    return InvocationGuard(g),result

def value():
    return {"status":"completed","evidence":[{"path":"checked-artifact","checked":True}],"summary":"submitted"}

def test_read_only_agent_submits_without_general_write_or_process_permission(tmp_path):
    guard,result=setup(tmp_path)
    assert not guard.grant.process.enabled and "write_file" not in guard.grant.scope.tools
    answer=submit(guard,value());payload=json.loads(result.read_bytes())
    assert answer["acceptance"]=="requires_shared_85_acceptance"
    assert payload["task_id"]==guard.grant.identity.task_id
    assert payload["run_token"]==guard.grant.identity.run_token
    assert payload["fencing_token"]==guard.grant.identity.fencing_token
    assert payload["idempotency_key"]=="result-key"
    assert answer["evidence_sha256"]==payload["artifact_sha256"]
    assert submit(guard,value())==answer
    with pytest.raises(PolicyDenied,match="already_submitted"):
        submit(guard,{**value(),"summary":"different"})
    with pytest.raises(PolicyDenied,match="not_granted"):
        guard.authorize_tool("write_file",{"path":str(tmp_path/"other"),"content":"no"})
    assert not (tmp_path/"other").exists()

@pytest.mark.parametrize("fault",["replacement","symlink","hardlink","mode","foreign-identity"])
def test_slot_cannot_authorize_replaced_or_foreign_inode(tmp_path,fault):
    guard,result=setup(tmp_path)
    if fault=="replacement":
        result.rename(tmp_path/"old");result.touch(mode=0o600)
    if fault=="symlink":
        result.unlink();other=tmp_path/"other";other.write_text("preserve");result.symlink_to(other)
    if fault=="hardlink":os.link(result,tmp_path/"link")
    if fault=="mode":result.chmod(0o644)
    if fault=="foreign-identity":
        with pytest.raises(SecurityError,match="identity/root"):
            replace(guard.grant,identity=replace(guard.grant.identity,fencing_token=999))
        return
    with pytest.raises((PolicyDenied,OSError)):submit(guard,value())
    if fault=="symlink":assert (tmp_path/"other").read_text()=="preserve"

@pytest.mark.parametrize("fault",["destination","identity","empty","status","oversized","secret"])
def test_submission_arguments_do_not_choose_authority_or_hide_secrets(tmp_path,fault):
    guard,result=setup(tmp_path);raw=value()
    if fault=="destination":raw["path"]=str(tmp_path/"other")
    if fault=="identity":raw["task_id"]="foreign"
    if fault=="empty":raw["evidence"]=[]
    if fault=="status":raw["status"]="DONE"
    if fault=="oversized":raw["summary"]="x"*8193
    if fault=="secret":raw["evidence"]=[{"api_key":"do-not-export"}]
    with pytest.raises((ValueError,PolicyDenied)):submit(guard,raw)
    assert result.read_bytes()==b""

def test_actual_registered_handler_rechecks_identity_and_uninstall_ownership(tmp_path,monkeypatch):
    guard,result=setup(tmp_path);installation=GuardInstallation(guard,surface={});registry=Registry()
    for field,key in IDENTITY_ENV.items():monkeypatch.setenv(key,str(getattr(guard.grant.identity,field)))
    monkeypatch.setenv("HERDR_DURABLE_SANDBOX","1")
    register_result_tool(installation,registry,ContextVar("authorized",default=None),_call_digest)
    handler=registry.get_entry(TOOL).handler
    assert registry.get_entry(TOOL).toolset==TOOLSET
    assert "error" in json.loads(handler(value(),task_id="foreign"))
    monkeypatch.setenv("HERDR_POLICY_FENCING_TOKEN","999")
    assert "error" in json.loads(handler(value()))
    monkeypatch.setenv("HERDR_POLICY_FENCING_TOKEN",str(guard.grant.identity.fencing_token))
    assert json.loads(handler(value()))["submitted"]
    installation.uninstall()
    assert registry.get_entry(TOOL) is None and "error" in json.loads(handler(value()))

def test_signed_slot_roundtrip_and_no_scope_escalation(tmp_path):
    guard,result=setup(tmp_path)
    from herdr.security import SecurityGrant
    assert SecurityGrant.from_dict(guard.grant.to_json())==guard.grant
    with pytest.raises(SecurityError,match="identity/root"):
        replace(guard.grant,tool_rules=(replace(guard.grant.tool_rules[0],allowed_roots=(str(tmp_path/"outside"),)),))

def test_actual_private_result_bind_mount_with_read_only_workspace(tmp_path):
    import subprocess,sys,shutil
    if not shutil.which("bwrap"):pytest.skip("bubblewrap unavailable")
    probe=subprocess.run(["bwrap","--ro-bind","/","/","--unshare-pid","--","/bin/true"],capture_output=True)
    if probe.returncode:pytest.skip("user namespace unavailable")
    guard,result=setup(tmp_path)
    sibling=tmp_path/"sibling";sibling.write_text("preserve")
    workspace=Path(guard.grant.workspace_root)
    declaration=tmp_path/"grant.json";declaration.write_text(json.dumps(guard.grant.to_json()))
    repo=Path(__file__).resolve().parents[2]
    program="""import sys,json
sys.path.insert(0,sys.argv[1])
from herdr.security import SecurityGrant,InvocationGuard
from herdr.result_submission import submit
g=SecurityGrant.from_dict(json.load(open(sys.argv[2])))
answer=submit(InvocationGuard(g),{"status":"completed","evidence":[{"artifact":"actual-bound-inode"}]})
assert answer["submitted"]
for name in sys.argv[3:]:
 try:
  open(name,"w").write("escape")
 except OSError: pass
 else: raise AssertionError("foreign write permitted")
print("BOUND_RESULT_PASS")
"""
    completed=subprocess.run(["bwrap","--ro-bind","/","/","--unshare-pid","--unshare-net",
        "--bind",str(result),str(result),"--",sys.executable,"-c",program,str(repo),str(declaration),
        str(sibling),str(workspace/"escape")],text=True,capture_output=True,timeout=20)
    assert completed.returncode==0,completed.stderr
    assert "BOUND_RESULT_PASS" in completed.stdout
    assert json.loads(result.read_text())["idempotency_key"]=="result-key"
    assert sibling.read_text()=="preserve" and not (workspace/"escape").exists()


@pytest.mark.parametrize("failure",["write","fsync"])
def test_partial_submission_replays_same_candidate_on_exact_inode(tmp_path,monkeypatch,failure):
    import herdr.result_submission as module
    guard,result=setup(tmp_path);before=result.stat()
    real_write,real_fsync=os.write,os.fsync
    calls=0
    def write(fd,payload):
        nonlocal calls
        if os.fstat(fd).st_ino != before.st_ino:return real_write(fd,payload)
        calls+=1
        if calls==1:return real_write(fd,payload[:19])
        if failure=="write":raise OSError("simulated full filesystem")
        return real_write(fd,payload)
    def fsync(fd):
        if failure=="fsync" and os.fstat(fd).st_ino==before.st_ino and os.fstat(fd).st_size:
            raise OSError("simulated interrupted commit")
        return real_fsync(fd)
    monkeypatch.setattr(module.os,"write",write)
    monkeypatch.setattr(module.os,"fsync",fsync)
    with pytest.raises(OSError):submit(guard,value())
    partial=result.read_bytes()
    assert partial
    monkeypatch.setattr(module.os,"write",real_write)
    monkeypatch.setattr(module.os,"fsync",real_fsync)
    assert submit(guard,value())["submitted"]
    assert result.stat().st_ino==before.st_ino
    assert json.loads(result.read_bytes())["status"]=="completed"
    with pytest.raises(PolicyDenied,match="already_submitted"):
        submit(guard,{**value(),"summary":"different"})

def test_delegated_result_inode_fits_parent_without_other_sibling_mounts(tmp_path):
    from herdr.security import InvocationIdentity, RuntimeAssurance
    from herdr.context import digest
    parent,result=setup(tmp_path)
    g=parent.grant
    child_id=InvocationIdentity(g.identity.consumer,"child-agent",g.identity.agent_id,
        g.identity.task_id,"child-task","child-run",g.identity.fencing_token+1)
    child_result=tmp_path/"child-result.json";child_result.touch(mode=0o600)
    child_slot=ResultSlot.bind(child_result,child_id,"child-key")
    child=replace(g,identity=child_id,parent_grant_hash=g.hash,
        tool_rules=(replace(g.tool_rules[0],result_slot=child_slot),),
        runtime_assurance=replace(g.runtime_assurance,writable_roots=(str(child_result),)))
    child.require_subset_of(g)
    forbidden=tmp_path/"other-result.json";forbidden.touch()
    with pytest.raises(SecurityError,match="runtime assurance"):
        replace(child,runtime_assurance=replace(child.runtime_assurance,
            writable_roots=(str(child_result),str(forbidden)))).require_subset_of(g)
    with pytest.raises(SecurityError,match="runtime assurance"):
        replace(child,runtime_assurance=replace(child.runtime_assurance,
            writable_roots=(str(tmp_path),))).require_subset_of(g)


@pytest.mark.parametrize("prefix",[1,5,19])
def test_partial_result_intent_denies_different_candidate_with_same_prefix(tmp_path,monkeypatch,prefix):
    import herdr.result_submission as module
    guard,result=setup(tmp_path);inode=result.stat().st_ino
    actual=os.write;calls=0
    def interrupted(fd,data):
        nonlocal calls
        calls+=1
        if calls==1:return actual(fd,data[:prefix])
        raise OSError("interrupt original candidate")
    monkeypatch.setattr(module.os,"write",interrupted)
    with pytest.raises(OSError):submit(guard,value())
    retained=result.read_bytes()
    assert len(retained)==prefix
    monkeypatch.setattr(module.os,"write",actual)
    with pytest.raises(PolicyDenied,match="already_submitted"):
        submit(guard,{**value(),"summary":"different candidate"})
    assert result.read_bytes()==retained and result.stat().st_ino==inode
    assert submit(guard,value())["submitted"]

def test_result_intent_survives_failure_before_first_payload_byte(tmp_path,monkeypatch):
    import herdr.result_submission as module
    guard,result=setup(tmp_path);actual=os.fsync
    def interrupted(fd):raise OSError("intent fsync uncertain")
    monkeypatch.setattr(module.os,"fsync",interrupted)
    with pytest.raises(OSError):submit(guard,value())
    assert result.read_bytes()==b""
    monkeypatch.setattr(module.os,"fsync",actual)
    with pytest.raises(PolicyDenied,match="already_submitted"):
        submit(guard,{**value(),"summary":"different candidate"})
    assert submit(guard,value())["submitted"]
