"""Review regressions across physical state, bounded receipts and cold entry points."""
from dataclasses import replace
from types import SimpleNamespace
import contextvars
import json
import os
from pathlib import Path
import pytest

from herdr.evidence import canonical, digest
from herdr.work_cycle import WorkContractError, WorkCycle, WorkPhase, CheckResult
from tests.herdr.test_work_cycle import setup, runner, git, edit
from tests.herdr.test_work_hygiene import boundary_workspace, fixture
from tests.herdr.test_work_handoff import ready

@pytest.mark.parametrize("mutation",["change","delete","create"])
def test_ignored_foreign_path_is_part_of_scope_inventory(tmp_path,mutation):
    cycle,root,plan,log=setup(tmp_path)
    (root/".gitignore").write_text("ignored-*\n")
    git(root,"add",".gitignore");git(root,"commit","-qm","ignore policy")
    plan=replace(plan,base_sha=git(root,"rev-parse","HEAD"))
    cycle=WorkCycle(plan,root,log,git=cycle.git)
    path=root/"ignored-foreign";path.write_text("original")
    cycle.start(runner)
    if mutation=="delete":path.unlink()
    elif mutation=="create":(root/"ignored-new").write_text("foreign")
    else:path.write_text("changed")
    edit(root)
    with pytest.raises(WorkContractError,match="escaped approved"):cycle.verify(runner)
    assert cycle.phase is not WorkPhase.HYGIENE

def test_startup_time_is_in_validated_proof_and_cold_replay(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    def slow(check,root,plan,tree):
        return replace(runner(check,root,plan,tree),duration_ms=(check.timeout_seconds+9)*1000)
    cycle.start(slow);edit(root);cycle.verify(slow)
    cold=WorkCycle(plan,root,log,git=cycle.git)
    assert cold.phase is WorkPhase.HYGIENE
    proof=replace(runner(plan.checks[0],root,plan,"a"*64),duration_ms=913000)
    assert proof.duration_ms==913000
    with pytest.raises(WorkContractError):replace(proof,duration_ms=913001)

def test_late_foreign_index_is_preserved_by_final_cas(boundary_workspace,monkeypatch):
    import herdr.work_hygiene as module
    committer,cycle,work,log=fixture(boundary_workspace)
    original=module.publish_file;foreign=[]
    def race(fd,name,raw,**kwargs):
        if name=="index" and not foreign:
            (work/"foreign.txt").write_text("foreign staged after validation")
            git(work,"add","foreign.txt")
            foreign.append((work/".git/index").read_bytes())
        return original(fd,name,raw,**kwargs)
    monkeypatch.setattr(module,"publish_file",race)
    with pytest.raises(Exception):committer(cycle)
    assert foreign and (work/".git/index").read_bytes()==foreign[0]
    assert git(work,"diff","--cached","--name-only").splitlines()==["foreign.txt","result.py"]
    assert cycle.phase is WorkPhase.HYGIENE

def test_many_long_check_ids_fit_the_sealed_handoff_transport(boundary_workspace,monkeypatch):
    from herdr.check_runner import HostCheckRunner
    port,cycle,guard,result,task,plan,observed,log=ready(boundary_workspace,monkeypatch)
    port.prepare_request(cycle,"original",{"pr_number":None})
    outcome=cycle.request_verification("original",HostCheckRunner(port.committer.policy.environment,
        boundary_workspace/"host"/"checks",git=cycle.git))
    # A transport-sized stress fixture preserves the real sealed host artifact.
    many={**outcome,"checks":[{**outcome["checks"][0],"check_id":str(i).zfill(64)} for i in range(32)]}
    many["evidence_sha256"]=digest(many["checks"])
    response=port.complete(cycle,"original",many)
    assert len(canonical(response))<=8191 and response["check_count"]==32
    assert response["evidence_sha256"]==many["evidence_sha256"] and "checks" not in response

def test_work_registry_consumes_one_shot_approval_once(tmp_path,monkeypatch):
    from herdr.security import ApprovalEvidence, RiskClass, ToolRule, canonical_digest
    from herdr.work_contract_host import WorkInvocationGuard
    from herdr.work_tool import register_work_tool,TOOL
    from herdr.policy_launch import IDENTITY_ENV
    from tests.herdr.test_security import grant,assurance
    raw={"request_id":"one"}
    item=grant(tmp_path,tools=(TOOL,),rules=(ToolRule(TOOL,RiskClass.READ,("request_id","handoff"),
        requires_sandbox=True),),approval_required_for=(RiskClass.READ,))
    item=replace(item,approvals=(ApprovalEvidence("once",item.identity,TOOL,
        canonical_digest({"tool":TOOL,"args":raw})),))
    consumed=[]
    def consume(*args):consumed.append(args);return "consumed" if len(consumed)==1 else "replayed"
    class Transport:
        def __call__(self,*a,**kw):return True
        def verify(self,*a,**kw):return {"status":"failed"}
    guard=WorkInvocationGuard(item,work_authority=Transport(),approval_consumer=consume)
    entries={}
    class Registry:
        def get_entry(self,name):return entries.get(name)
        def register(self,**kw):entries[kw["name"]]=SimpleNamespace(**kw)
        def restore_registration(self,*args):pass
    install=SimpleNamespace(guard=guard,installed=True,finalizers=[])
    authorization=contextvars.ContextVar("test-work-authorization",default=None)
    register_work_tool(install,Registry(),authorization,lambda t,a:canonical_digest({"tool":t,"args":a}))
    monkeypatch.setenv("HERDR_DURABLE_SANDBOX","1")
    for field,key in IDENTITY_ENV.items():monkeypatch.setenv(key,str(getattr(item.identity,field)))
    assert json.loads(entries[TOOL].handler(raw))=={"status":"failed"}
    assert len(consumed)==1
    # The SDK already consumed the same approval: handler and internal verify
    # revalidate it without spending it again.
    authorization.set((item.hash,TOOL,canonical_digest({"tool":TOOL,"args":raw})))
    assert json.loads(entries[TOOL].handler(raw))=={"status":"failed"} and len(consumed)==1

def test_cold_watchdog_uses_original_work_receipt_without_live_sdk(boundary_workspace,monkeypatch):
    import importlib.util
    from importlib.machinery import SourceFileLoader
    from herdr.check_runner import HostCheckRunner
    from herdr.work_contract_host import HostWorkContractFactory
    from agent_completion_evidence import store_for
    from herdr.evidence import binding
    from tests.agent_stack import test_watchdog_recovery as helpers
    port,cycle,guard,result,task,plan,observed,log=ready(boundary_workspace,monkeypatch)
    port.prepare_request(cycle,"watchdog-original",{"pr_number":None})
    outcome=cycle.request_verification("watchdog-original",HostCheckRunner(port.committer.policy.environment,
        boundary_workspace/"host"/"checks",git=cycle.git))
    port.deliver(cycle,"watchdog-original")
    payload=json.loads(result.read_bytes())
    assert "artifact_workspace" not in payload
    cold=HostWorkContractFactory(approve=lambda **kw:pytest.fail("no new admission"),
        environment=port.committer.policy.environment,storage=boundary_workspace/"host"/"checks",
        audit_log=log,git=cycle.git)
    cold.result_authority=port.result_authority
    recovered=cold.recover(identity=cycle.plan.identity,workspace=cycle.root,
        spec_sha256=cycle.plan.spec_sha256,grant_sha256=cycle.plan.grant_sha256,plan_sha256=cycle.plan.hash)
    helpers.configure_paths(boundary_workspace/"watchdog")
    recovery=helpers.recovery
    store_for(recovery.ROOT,task).publish("plan",digest(binding(task)),plan)
    loader=SourceFileLoader("review86_cold_worker",str(Path(__file__).parents[2]/"agent-stack/bin/agent-task-worker"))
    spec=importlib.util.spec_from_loader(loader.name,loader);worker=importlib.util.module_from_spec(spec);loader.exec_module(worker)
    task["kind"]="github_issue_slice";task["work_contract_version"]=1
    task["completion_plan"]=plan
    task["work_contract"]={"version":1,"plan_sha256":cycle.plan.hash}
    monkeypatch.setattr(worker,"_recover_root_work_cycle",lambda task:(cold,recovered))
    monkeypatch.setattr(recovery,"_worker_bridge",lambda:worker)
    monkeypatch.setattr("herdr.work_result_receipt.verify_invocation_session",
                        lambda *a:pytest.fail("watchdog cannot require SDK"))
    calls=[]
    # GitHub is a read-only acceptance fixture. The watchdog's real worker,
    # cold WorkCycle, original receipt and invocation verifier are exercised.
    def accepted(root,current,payload,*,invocation_verifier):
        calls.append(invocation_verifier(current))
        return {"level":"verified_worker_result","bundle_hash":"a"*64}
    monkeypatch.setattr(worker,"verify_completion",accepted)
    monkeypatch.setattr(recovery,"cleanup_task_owned_pane",lambda task:True)
    path=recovery.RUNNING/(task["id"]+".json");helpers.write_task(path,task)
    recovery._terminalize_from_result_locked(path,task,payload,0,True)
    assert len(calls)==1 and calls[0]==task["execution_session"]["invocation_policy"]
    assert recovered.phase is WorkPhase.FINISHED and task["work_contract"]["phase"]=="finished"
    assert (recovery.DONE/path.name).exists()

def test_actual_wire_response_uses_the_same_unicode_bytes_as_preflight(boundary_workspace,monkeypatch):
    import socket
    from tests.herdr.test_work_authority import owner_for
    from herdr.work_authority import dispatch_work_connection
    port,cycle,guard,result,task,plan,observed,log=ready(boundary_workspace,monkeypatch)
    owner,_=owner_for(SimpleNamespace(authorize_invocation=lambda *a,**kw:True),guard.grant)
    outcome={"status":"pass","submission":{"narrative":"ž"*1200,"artifact_fixture":"a"*1500}}
    assert len(json.dumps(outcome).encode())>8192 and len(canonical(outcome))<8192
    callbacks=[]
    owner.work_verify=lambda *a,**kw:callbacks.append(kw) or outcome
    left,right=socket.socketpair()
    request={"op":"work-verify","identity":guard.grant.identity.to_json(),"grant_sha256":guard.grant.hash,
             "request_id":"unicode","handoff":{"pr_number":None,"scope_claim":{"narrative":"ž"*1200}}}
    encoded=json.dumps(request).encode()+b"\n";assert len(encoded)<8192
    right.sendall(encoded)
    assert dispatch_work_connection(owner,left)
    response=right.recv(8193);right.close()
    assert response==canonical(outcome)+b"\n" and len(callbacks)==1

def test_short_grant_blocks_factory_before_baseline_effect(tmp_path,monkeypatch):
    from datetime import UTC,datetime,timedelta
    from tests.herdr.test_work_contract_host import factory_fixture
    factory,root,plan,grant,log=factory_fixture(tmp_path)
    grant=replace(grant,expires_at=(datetime.now(UTC)+timedelta(seconds=30)).isoformat())
    factory.approve=lambda **kw:replace(plan,grant_sha256=grant.hash)
    monkeypatch.setattr("herdr.check_runner.HostCheckRunner.__call__",
                        lambda *a:pytest.fail("insufficient grant cannot run baseline"))
    with pytest.raises(WorkContractError,match="lifetime"):
        factory.prepare(identity=grant.identity,workspace=root,grant=grant,spec_sha256=plan.spec_sha256)
    assert log.replay()==[]

def test_short_grant_blocks_socket_before_verification_callback(boundary_workspace,monkeypatch):
    from datetime import UTC,datetime,timedelta
    import socket
    from tests.herdr.test_work_authority import owner_for
    from herdr.work_authority import dispatch_work_connection
    port,cycle,guard,result,task,plan,observed,log=ready(boundary_workspace,monkeypatch)
    grant=replace(guard.grant,expires_at=(datetime.now(UTC)+timedelta(seconds=30)).isoformat())
    owner,_=owner_for(SimpleNamespace(authorize_invocation=lambda *a,**kw:True),grant)
    owner.work_verify=lambda *a,**kw:pytest.fail("insufficient grant cannot commit")
    left,right=socket.socketpair()
    right.sendall(canonical({"op":"work-verify","identity":grant.identity.to_json(),"grant_sha256":grant.hash,
                            "request_id":"short"})+b"\n")
    assert dispatch_work_connection(owner,left)
    assert right.recv(8193)==b"denied\n";right.close()

def test_modifying_hook_allows_new_immutable_reverification_intent(boundary_workspace,monkeypatch):
    from herdr.check_runner import HostCheckRunner
    port,cycle,guard,result,task,plan,observed,log=ready(boundary_workspace,monkeypatch,
        hook='found=0; while IFS= read -r row; do case "$row" in \'# formatter changed tested content\') found=1;; esac; done < result.py; if [ "$found" = 0 ]; then printf \'\\n# formatter changed tested content\\n\' >> result.py; fi')
    oracle=HostCheckRunner(port.committer.policy.environment,boundary_workspace/"host"/"checks",git=cycle.git)
    port.prepare_request(cycle,"before-hook",{"pr_number":None})
    outcome=cycle.request_verification("before-hook",oracle)
    with pytest.raises(ValueError,match="invalidated"):port.complete(cycle,"before-hook",outcome)
    assert cycle.phase is WorkPhase.VERIFY and cycle.verification_open and not cycle.verified_checks
    # Explicit trusted formatter-repair fixture: the disposable hook never
    # promotes content automatically. These exact new bytes need a fresh oracle.
    with (cycle.root/"result.py").open("a") as stream:stream.write("\n# formatter changed tested content\n")
    port.prepare_request(cycle,"after-hook",{"pr_number":None})
    repeated=cycle.request_verification("after-hook",oracle)
    assert repeated["status"]=="pass" and cycle.phase is WorkPhase.HYGIENE
    assert result.read_bytes()==b"" and git(cycle.root,"rev-parse","HEAD")==cycle.plan.base_sha

    response=port.complete(cycle,"after-hook",repeated)
    assert response["status"]=="pass" and cycle.phase is WorkPhase.HANDOFF
    assert git(cycle.root,"rev-parse","HEAD")!=cycle.plan.base_sha
    retired=[e for e in cycle._events() if e["event"]=="work_local_commit_invalidated"]
    assert len(retired)==1
    cold=WorkCycle(cycle.plan,cycle.root,log,git=cycle.git)
    assert cold.phase is WorkPhase.HANDOFF


def test_actual_client_preserves_canonical_unicode_request(tmp_path,monkeypatch):
    import socket,threading
    from herdr.work_authority import WorkAuthorityClient,dispatch_work_connection
    from tests.herdr.test_work_authority import owner_for
    from tests.herdr.test_security import grant
    from herdr.security import ToolRule,RiskClass
    item=grant(tmp_path,tools=("herdr_verify_work",),rules=(ToolRule("herdr_verify_work",RiskClass.READ,
        ("request_id","handoff"),requires_sandbox=True),))
    owner,_=owner_for(SimpleNamespace(authorize_invocation=lambda *a,**kw:True),item)
    seen=[]
    owner.work_verify=lambda *a,**kw:seen.append(kw["handoff"]) or {"status":"failed"}
    path=tmp_path/"unicode.sock";monkeypatch.setattr("herdr.work_authority.SOCKET_PATH",path)
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(path));listener.listen(1)
    def server():
        connection,_=listener.accept();dispatch_work_connection(owner,connection)
    thread=threading.Thread(target=server,daemon=True);thread.start()
    handoff={"pr_number":None,"scope_claim":{"narrative":"ž"*1400}}
    assert len(canonical(handoff))<4096 and len(json.dumps(handoff).encode())>8192
    try:
        assert WorkAuthorityClient().verify(item.identity,item.hash,"unicode",handoff)=={"status":"failed"}
        thread.join(5);assert not thread.is_alive() and seen==[handoff]
    finally:listener.close()


def test_host_result_context_is_exact_and_direct_model_cannot_pin_slot(boundary_workspace,monkeypatch):
    from herdr.work_contract_host import WorkInvocationGuard
    from herdr.security import PolicyDenied
    from herdr.result_submission import submit
    port,cycle,original,result,task,plan,observed,log=ready(boundary_workspace,monkeypatch)
    calls=[]
    class ProtectedPhase:
        def __call__(self,*a,kind,tool):
            calls.append(tool)
            if tool=="herdr_submit_result":raise PolicyDenied("work_phase_forbids_invocation")
            return True
    guard=WorkInvocationGuard(original.grant,work_authority=ProtectedPhase())
    raw={"status":"blocked","evidence":[{"fixture":"host-original"}],"summary":"original"}
    with pytest.raises(PolicyDenied):submit(guard,raw)
    assert result.read_bytes()==b""
    with guard.host_result_submission(raw):
        with pytest.raises(PolicyDenied):submit(guard,{**raw,"summary":"model substitution"})
        assert result.read_bytes()==b""
        assert submit(guard,raw)["submitted"]
    with pytest.raises(PolicyDenied):submit(guard,raw)
    assert json.loads(result.read_bytes())["summary"]=="original"


def test_host_elapsed_time_blocks_metadata_publication_before_effect(tmp_path,monkeypatch):
    import herdr.work_lifetime as lifetime
    from herdr.work_hygiene import publish_file,directory_fd
    now=[10.0];monkeypatch.setattr(lifetime.time,"monotonic",lambda:now[0])
    target=tmp_path/"owned-ref";target.write_bytes(b"base\n")
    fd=directory_fd(tmp_path)
    try:
        with pytest.raises(WorkContractError,match="deadline"):
            with lifetime.bounded_host_request(130):
                now[0]=141.0
                publish_file(fd,"owned-ref",b"new\n",expected=b"base\n")
        assert target.read_bytes()==b"base\n" and not (tmp_path/"owned-ref.lock").exists()
    finally:os.close(fd)


def test_original_grant_reserves_host_phase_allowance_before_baseline(tmp_path,monkeypatch):
    from datetime import UTC,datetime,timedelta
    from tests.herdr.test_work_contract_host import factory_fixture
    factory,root,plan,item,log=factory_fixture(tmp_path)
    command_seconds=2*sum(c.timeout_seconds+13 for c in plan.checks)
    item=replace(item,expires_at=(datetime.now(UTC)+timedelta(seconds=command_seconds+20)).isoformat())
    factory.approve=lambda **kw:replace(plan,grant_sha256=item.hash)
    monkeypatch.setattr("herdr.check_runner.HostCheckRunner.__call__",lambda *a:pytest.fail("no effect"))
    with pytest.raises(WorkContractError,match="lifetime"):
        factory.prepare(identity=item.identity,workspace=root,grant=item,spec_sha256=plan.spec_sha256)
    assert log.replay()==[]


def test_crash_after_single_hook_invalidation_replays_verify_not_hygiene(boundary_workspace,monkeypatch):
    from herdr.check_runner import HostCheckRunner
    port,cycle,guard,result,task,plan,observed,log=ready(boundary_workspace,monkeypatch,
        hook="printf '\\n# formatter changed tested content\\n' >> result.py")
    oracle=HostCheckRunner(port.committer.policy.environment,boundary_workspace/"host"/"checks",git=cycle.git)
    port.prepare_request(cycle,"crash-after-invalidated",{"pr_number":None})
    outcome=cycle.request_verification("crash-after-invalidated",oracle)
    original=cycle._record
    def crash(kind,**data):
        original(kind,**data)
        if kind=="local_commit_invalidated":raise SystemExit("crash after durable retirement")
    monkeypatch.setattr(cycle,"_record",crash)
    with pytest.raises(SystemExit):port.complete(cycle,"crash-after-invalidated",outcome)
    cold=WorkCycle(cycle.plan,cycle.root,log,git=cycle.git)
    assert cold.phase is WorkPhase.VERIFY and cold.verification_open and not cold.verified_checks
    assert result.read_bytes()==b"" and git(cycle.root,"rev-parse","HEAD")==cycle.plan.base_sha
    monkeypatch.setattr(HostCheckRunner,"_execute",lambda *a:pytest.fail("cannot repeat hooks before new verification"))
    with pytest.raises(WorkContractError):port.committer(cold)

def test_transport_prechecks_consume_the_original_request_deadline(tmp_path,monkeypatch):
    import socket
    import herdr.work_lifetime as lifetime
    from herdr.work_authority import dispatch_work_connection
    from tests.herdr.test_work_authority import owner_for
    from tests.herdr.test_security import grant
    from herdr.security import ToolRule,RiskClass
    item=grant(tmp_path,tools=("herdr_verify_work",),rules=(ToolRule("herdr_verify_work",RiskClass.READ,
        ("request_id","handoff"),requires_sandbox=True),))
    owner,_=owner_for(SimpleNamespace(authorize_invocation=lambda *a,**kw:True),item)
    owner.work_verify=lambda *a,**kw:pytest.fail("expired prechecks cannot invoke host effects")
    now=[10.0];monkeypatch.setattr(lifetime.time,"monotonic",lambda:now[0])
    owner.launch.mount.verify_mounted=lambda *a:now.__setitem__(0,911.0)
    left,right=socket.socketpair()
    right.sendall(canonical({"op":"work-verify","identity":item.identity.to_json(),
        "grant_sha256":item.hash,"request_id":"precheck"})+b"\n")
    with pytest.raises(WorkContractError,match="deadline"):dispatch_work_connection(owner,left)
    assert right.recv(8193)==b"denied\n";right.close()
