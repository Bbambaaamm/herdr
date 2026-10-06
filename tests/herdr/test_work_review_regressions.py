"""Adversarial regressions for PR 111's independent review."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import socket
import threading
import pytest

from herdr.security import PolicyDenied
from herdr.work_cycle import WorkContractError, WorkPhase
from herdr.work_authority import WorkAuthorityClient
from tests.herdr.test_check_runner import physical, environment
from tests.herdr.test_work_contract_host import factory_fixture
from tests.herdr.test_work_hygiene import fixture, boundary_workspace
from tests.herdr.test_work_cycle import git

def test_unlisted_runtime_file_is_absent_from_actual_oracle(tmp_path):
    # A file physically present beside an approved library must not enter the
    # namespace merely because its containing host directory exists.
    profile=environment()
    declared={path for path,sha in profile.system_files}
    target=next((path for path in Path("/usr/lib").rglob("*.so*")
                 if path.is_file() and not path.is_symlink() and str(path) not in declared),None)
    assert target is not None, "adversarial host library fixture unavailable"
    proof,root,host,check,plan=physical(tmp_path,("/usr/bin/python3","-c",
        "from pathlib import Path; assert not Path("+repr(str(target))+").exists()"))
    assert proof.exit_code==0 and not proof.truncated

def test_runtime_arguments_bind_only_declared_copies(tmp_path):
    from herdr.check_runtime import FrozenCheckRuntime
    profile=environment()
    (tmp_path/"private").mkdir(mode=0o700)
    runtime=FrozenCheckRuntime(profile,tmp_path/"private",writable_roots=(tmp_path/"work",))
    try:
        arguments=runtime.arguments()
        sources=[arguments[i+1] for i,item in enumerate(arguments) if item=="--ro-bind"]
        targets=[arguments[i+2] for i,item in enumerate(arguments) if item=="--ro-bind"]
        assert set(targets)=={path for path,sha in profile.system_files}
        assert all(source.startswith("/proc/self/fd/"+str(runtime.fd)+"/") for source in sources)
        assert not {"/usr/lib","/lib","/lib64"} & set(targets)
        assert all((runtime.tree.path/path.lstrip("/")).stat().st_mode&0o222==0 for path in targets)
        runtime.verify()
    finally: runtime.close()

@pytest.mark.parametrize("key",["hooks.contractFlag","commit.signoff","core.attributesFile"])
def test_unknown_repository_policy_blocks_before_hook_or_ref_effect(boundary_workspace,key):
    committer,cycle,work,log=fixture(boundary_workspace,repository_config={key:"required"})
    before=log._path.read_bytes()
    with pytest.raises(WorkContractError,match="approved richer profile"):committer(cycle)
    assert git(work,"rev-parse","HEAD")==cycle.plan.base_sha
    assert log._path.read_bytes()==before and list(committer.storage.iterdir())==[]

def test_work_cannot_pin_completion_slot_before_host_handoff(tmp_path):
    factory,root,plan,grant,log=factory_fixture(tmp_path)
    factory.prepare(identity=grant.identity,workspace=root,grant=grant,spec_sha256=plan.spec_sha256)
    slot=tmp_path/"result.json";slot.write_bytes(b"")
    with pytest.raises(PolicyDenied,match="work_result_requires_host_handoff"):
        factory.authorize_invocation(grant.identity,grant.hash,kind="tool",tool="herdr_submit_result")
    assert slot.read_bytes()==b"" and factory.cycle(grant.identity).phase is WorkPhase.WORK
    assert factory.authorize_invocation(grant.identity,grant.hash,kind="tool",tool="herdr_verify_work")

def test_oversized_verification_handoff_is_bounded_denial_before_socket(tmp_path,monkeypatch):
    from tests.herdr.test_security import identity
    monkeypatch.setattr("herdr.work_authority.socket.socket",
        lambda *a,**kw:pytest.fail("oversized request cannot reach a socket"))
    with pytest.raises(PolicyDenied,match="work_verification_denied"):
        WorkAuthorityClient().verify(identity(),"a"*64,"original",{"details":"x"*10000})

@pytest.mark.parametrize("response",[b'{"status":"pass"}',b"x"*8193])
def test_truncated_or_oversized_real_socket_response_is_bounded_denial(tmp_path,monkeypatch,response):
    from tests.herdr.test_security import identity
    path=tmp_path/"host.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH",path)
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    listener.bind(str(path));listener.listen(1);listener.settimeout(5)
    errors=[]
    def serve():
        try:
            connection,_=listener.accept()
            with connection:
                request=bytearray()
                while not request.endswith(b"\n"): request.extend(connection.recv(1024))
                assert json.loads(request)["op"]=="work-verify"
                connection.sendall(response)
        except Exception as exc:errors.append(exc)
    thread=threading.Thread(target=serve);thread.start()
    try:
        with pytest.raises(PolicyDenied,match="work_verification_denied"):
            WorkAuthorityClient().verify(identity(),"a"*64,"original")
    finally:
        thread.join(5);listener.close()
    assert not thread.is_alive() and not errors

@pytest.mark.parametrize("mutation",["inplace","replace","aba"])
def test_config_change_during_git_parser_blocks_before_commit(boundary_workspace,monkeypatch,mutation):
    import herdr.work_hygiene as module
    committer,cycle,work,log=fixture(boundary_workspace)
    original=module.read_only_git
    config=work/".git/config";approved=config.read_bytes()
    def boundary(root):
        run=original(root)
        def invoke(args):
            if args==["config","--local","--null","--list"]:
                changed=approved.replace(b"herdr-test@example.invalid",b"other@example.invalid")
                if changed==approved:changed=approved+b"\n[user]\nemail = other@example.invalid\n"
                if mutation=="replace":
                    replacement=config.with_name("config.review");replacement.write_bytes(changed);replacement.replace(config)
                else:config.write_bytes(changed)
                result=run(args)
                if mutation=="aba":config.write_bytes(approved)
                return result
            return run(args)
        return invoke
    monkeypatch.setattr(module,"read_only_git",boundary)
    before=log._path.read_bytes()
    with pytest.raises(WorkContractError,match="config changed during parsing"):committer(cycle)
    assert git(work,"rev-parse","HEAD")==cycle.plan.base_sha
    assert log._path.read_bytes()==before and list(committer.storage.iterdir())==[]

def test_actual_host_factory_preflight_accepts_unbound_child_rule_then_requires_physical_slot(boundary_workspace,tmp_path,monkeypatch):
    from types import SimpleNamespace
    from tests.herdr.test_work_handoff import ready
    from tests.herdr.test_host_configuration import approved_config
    from herdr.host_configuration import build_host_policy_factory
    from herdr.work_configuration import preflight_handoff
    port,cycle,guard,result,task,plan,observations,log=ready(boundary_workspace,monkeypatch)
    raw,unused,template=approved_config(tmp_path,monkeypatch)
    ceiling=replace(guard.grant,tool_rules=tuple(replace(rule,result_slot=None)
        if rule.tool=="herdr_submit_result" else rule for rule in guard.grant.tool_rules))
    raw["templates"]={guard.grant.identity.consumer:ceiling.to_json()}
    parent=guard.grant
    factory=build_host_policy_factory(parent_grant=parent)
    child=replace(parent.identity,agent_id="new-child",parent_agent_id=parent.identity.agent_id,
                  parent_task_id=parent.identity.task_id,task_id="new-child-task",run_token="new-child-run")
    launch=factory.prepare_child(identity=child,workspace=cycle.root,
        tools=parent.scope.tools,permissions=parent.scope.permissions)
    host=SimpleNamespace(local_commit_policy=port.committer.policy)
    try:
        rule=next(rule for rule in launch.grant.tool_rules if rule.tool=="herdr_submit_result")
        assert rule.result_slot is None
        preflight_handoff(host,launch,plan,require_slot=False)
        with pytest.raises(WorkContractError,match="immutable result"):preflight_handoff(host,launch,plan)
        slot=boundary_workspace/"child-result.json";slot.touch(mode=0o600)
        launch.bind_result_slot(slot,"child-original")
        preflight_handoff(host,launch,plan)
    finally:launch.cleanup_after_pane_closed()

def test_total_oracle_deadline_includes_each_namespace_startup(tmp_path):
    from herdr.scheduler import AuditLog
    from herdr.work_cycle import WorkCycle
    from tests.herdr.test_work_cycle import setup,runner
    original,root,plan,log=setup(tmp_path)
    checks=tuple(replace(plan.checks[0],id="check-"+str(i),timeout_seconds=120) for i in range(7))
    plan=replace(plan,checks=checks)
    cycle=WorkCycle(plan,root,AuditLog(tmp_path/"long-checks.jsonl"),git=original.git)
    cycle.start(runner)
    with pytest.raises(WorkContractError,match="aggregate time"):
        cycle.request_verification("long-host-request",lambda *a:pytest.fail("over-budget request cannot execute"))
