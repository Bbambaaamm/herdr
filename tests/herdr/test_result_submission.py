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
