"""Real host oracle/Git/result slot; physical launch port is an explicit fixture."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"agent-stack"/"bin"))
import pytest
from herdr.evidence import EvidenceError, EvidenceStore, binding, digest
from herdr.result_submission import ResultSlot, TOOL, ARGUMENTS, submit, payload_for_slot
from herdr.security import ToolRule, RiskClass, PolicyDenied
from herdr.work_contract_host import WorkInvocationGuard
from herdr.work_handoff import HostWorkHandoff
from herdr.work_cycle import WorkCycle, WorkPhase
from tests.herdr.test_evidence import launch_fixture
from tests.herdr.test_work_hygiene import boundary_workspace, fixture

def ready(root, monkeypatch, *, hook="true"):
    result = root/"host-result.json"; result.touch(mode=0o600)
    grants = []
    def bind(grant):
        slot = ResultSlot.bind(result, grant.identity, "original")
        rule = ToolRule(TOOL, RiskClass.RESULT_SUBMISSION, ARGUMENTS, requires_sandbox=True,
                        result_slot=slot, allowed_roots=(str(root),))
        verify = ToolRule("herdr_verify_work", RiskClass.READ, ("request_id","handoff"), requires_sandbox=True)
        grant = replace(grant, scope=replace(grant.scope, tools=(*grant.scope.tools, TOOL, "herdr_verify_work")),
                        tool_rules=(*grant.tool_rules, rule, verify))
        grants.append(grant)
        return grant
    committer, cycle, work, log = fixture(root, hook, grant_transform=bind, defer_verify=True)
    (root/"host").chmod(0o700); log._path.chmod(0o600)
    identity = cycle.plan.identity; grant = grants[0]
    task = {"id":identity.task_id, "run_token":identity.run_token, "fencing_token":identity.fencing_token,
            "attempt_id":1, "idempotency_key":"original", "repo":"org/repo", "workspace":str(work),
            "parent_task_id":identity.parent_task_id, "parent_agent_id":identity.parent_agent_id,
            "execution_session":{"agent_name":identity.agent_id, "sandbox_verified":True}}
    plan = {"version":1, "identity":binding(task), "repo":task["repo"], "kind":"coding",
            "base_sha":cycle.plan.base_sha, "spec_hash":cycle.plan.spec_sha256, "policy_hash":"f"*64,
            "workspace_root":str(work.parent), "required_checks":["tests"],
            "reviewer":"chatgpt-codex-connector[bot]", "environment":{"collector":"test"}}
    plan["plan_hash"] = digest(plan); plan["baseline"]=[]
    committer.completion_plan = deepcopy(plan)
    policy = {**launch_fixture(task), "grant_sha256":cycle.plan.grant_sha256}
    task["execution_session"]["invocation_policy"] = deepcopy(policy)
    observations=[]
    def observe(current):
        observations.append(binding(current))
        return deepcopy(current["execution_session"]["invocation_policy"])
    monkeypatch.setattr("herdr.work_result_receipt.verify_invocation_session", observe)
    monkeypatch.setattr("herdr.work_handoff.verify_invocation_session", observe)
    port = HostWorkHandoff(identity=identity, task=task, completion_plan=plan,
        store=EvidenceStore(root/"host"/"results"), slot=grant.tool_rules[-2].result_slot, committer=committer)
    guard = WorkInvocationGuard(grant, work_authority=lambda *a,**kw: True)
    return port, cycle, guard, result, task, plan, observations, log

def test_exact_local_result_capture_and_slot_delivery_survive_sdk_exit_without_repeat(boundary_workspace, monkeypatch):
    port, cycle, guard, result, task, plan, observations, log = ready(boundary_workspace, monkeypatch)
    port.prepare_request(cycle, "same-request", {"pr_number":None})
    from herdr.check_runner import HostCheckRunner
    runner = HostCheckRunner(committer_policy(port), boundary_workspace/"host"/"checks", git=cycle.git)
    outcome = cycle.request_verification("same-request", runner)
    response = port.complete(cycle, "same-request", outcome)
    assert cycle.phase is WorkPhase.HANDOFF and len(observations)==1
    assert submit(guard, response["submission"])["submitted"]
    payload = json.loads(result.read_bytes())
    assert payload == payload_for_slot(cycle.plan.identity, port.slot, response["submission"])
    checker = port.result_authority.verifier(task, payload, plan, work_plan_sha256=cycle.plan.hash)
    monkeypatch.setattr("herdr.work_result_receipt.verify_invocation_session",
                        lambda *a:pytest.fail("later reconciliation cannot require or restart the SDK"))
    assert checker(task)==task["execution_session"]["invocation_policy"]
    before = log._path.read_bytes()
    restored = WorkCycle(cycle.plan, cycle.root, log, git=cycle.git)
    assert port.committer(restored).to_json()==response["submission"]["evidence"][0]["herdr_completion"]["artifact"]
    assert log._path.read_bytes()==before
    with pytest.raises(EvidenceError):
        port.prepare_request(restored, "same-request", {"pr_number":12})
    assert submit(guard, response["submission"])["submitted"]

@pytest.mark.parametrize("change",["payload","plan","work-plan","policy","identity"])
def test_result_observation_cannot_be_rebound(boundary_workspace, monkeypatch, change):
    port, cycle, guard, result, task, plan, observations, log = ready(boundary_workspace, monkeypatch)
    port.prepare_request(cycle, "proof", {"pr_number":4})
    from herdr.check_runner import HostCheckRunner
    outcome = cycle.request_verification("proof", HostCheckRunner(committer_policy(port), boundary_workspace/"host"/"checks", git=cycle.git))
    response = port.complete(cycle, "proof", outcome)
    payload = payload_for_slot(cycle.plan.identity, port.slot, response["submission"])
    work_hash=cycle.plan.hash
    if change=="payload": payload["summary"]="changed"
    if change=="plan": plan["policy_hash"]="b"*64
    if change=="work-plan": work_hash="b"*64
    if change=="policy": task["execution_session"]["invocation_policy"]["code_sha256"]="b"*64
    if change=="identity": task["run_token"]="foreign"
    with pytest.raises(EvidenceError):
        port.result_authority.verifier(task,payload,plan,work_plan_sha256=work_hash)

def test_missing_scope_declaration_is_rejected_before_commit(boundary_workspace, monkeypatch):
    port, cycle, guard, result, task, plan, observations, log = ready(boundary_workspace, monkeypatch)
    port.plan["scope_policy"]={"version":1,"files":[{"path":"result.py","subtree":False}],
                             "acceptance_ids":["behavior"],"shared_contract_keys":[]}
    before=log._path.read_bytes()
    with pytest.raises(EvidenceError):port.prepare_request(cycle,"no-scope",{"pr_number":None})
    assert log._path.read_bytes()==before and cycle.phase is WorkPhase.WORK and result.read_bytes()==b""


def committer_policy(port):
    return port.committer.policy.environment

@pytest.mark.parametrize("interrupted_slot", [False, True])
def test_cold_host_recovers_commit_before_slot_delivery_after_sdk_loss(boundary_workspace, monkeypatch, interrupted_slot):
    from types import SimpleNamespace
    from herdr.work_contract_host import HostWorkContractFactory
    from herdr.work_configuration import bind_root_handoff, recover_host_handoff
    from herdr.work_result_receipt import WorkResultAuthority
    from herdr.check_runner import HostCheckRunner
    from tests.herdr.test_work_cycle import git
    from agent_completion_evidence import store_for
    port, cycle, guard, result, task, plan, observations, log = ready(boundary_workspace, monkeypatch)
    factory = HostWorkContractFactory(approve=lambda **kw:cycle.plan,
        environment=port.committer.policy.environment, storage=boundary_workspace/"host"/"checks",
        audit_log=log, git=cycle.git)
    factory.local_commit_policy=port.committer.policy
    factory.result_authority=port.result_authority
    factory.task_store_root=boundary_workspace
    store_for(boundary_workspace,task).publish("plan",digest(binding(task)),plan)
    original=bind_root_handoff(factory,task,SimpleNamespace(grant=guard.grant),cycle)
    original.prepare_request(cycle,"interrupted-after-commit",{"pr_number":None})
    cycle.request_verification("interrupted-after-commit",HostCheckRunner(factory.environment,
        factory.storage,git=cycle.git))
    artifact=original.committer(cycle)
    assert result.read_bytes()==b"" and cycle.phase is WorkPhase.HANDOFF
    if interrupted_slot:
        import os
        native_write = os.write
        slot_stat = result.stat()
        written = []
        def interrupt_write(fd, data):
            current = os.fstat(fd)
            if (current.st_dev, current.st_ino) == (slot_stat.st_dev, slot_stat.st_ino):
                if written:
                    raise OSError("simulated process loss during original slot publication")
                written.append(native_write(fd, data[:37]))
                return written[-1]
            return native_write(fd, data)
        with monkeypatch.context() as interruption:
            interruption.setattr("herdr.result_submission.os.write", interrupt_write)
            with pytest.raises(OSError, match="simulated process loss"):
                original.deliver(cycle, "interrupted-after-commit")
        assert written == [37] and len(result.read_bytes()) == 37
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.read_bytes())
    before=log._path.read_bytes()
    def no_live(*args):pytest.fail("SDK died; host must not call or restart it")
    monkeypatch.setattr("herdr.work_handoff.verify_invocation_session",no_live)
    monkeypatch.setattr("herdr.work_result_receipt.verify_invocation_session",no_live)
    restored=HostWorkContractFactory(approve=lambda **kw:pytest.fail("no re-admission"),
        environment=factory.environment,storage=factory.storage,audit_log=log,git=cycle.git)
    restored.local_commit_policy=factory.local_commit_policy
    restored.result_authority=WorkResultAuthority(EvidenceStore(port.store.root))
    restored.task_store_root=boundary_workspace
    current=restored.recover(identity=cycle.plan.identity,workspace=cycle.root,
        spec_sha256=cycle.plan.spec_sha256,grant_sha256=cycle.plan.grant_sha256,plan_sha256=cycle.plan.hash)
    resumed=recover_host_handoff(restored,task,current,plan)
    payload=resumed.deliver(current,"interrupted-after-commit")
    assert json.loads(result.read_bytes())==payload
    assert resumed.deliver(current,"interrupted-after-commit")==payload
    assert log._path.read_bytes()==before
    assert git(cycle.root,"rev-parse","HEAD")==artifact.commit_sha
    assert current.phase is WorkPhase.HANDOFF
    with pytest.raises(PolicyDenied):restored.authorize_invocation(current.plan.identity,
        current.plan.grant_sha256,kind="provider")


def test_modern_child_port_runs_baseline_and_recovers_original_local_candidate(boundary_workspace, monkeypatch):
    """Actual child authority and host effects; launch transport is a fixture."""
    from types import SimpleNamespace
    from herdr.child_evidence import ChildCompletionAuthority, child_identity, child_spec, child_task
    from herdr.work_contract_host import HostWorkContractFactory
    from herdr.scheduler import AuditLog
    from agent_completion_evidence import store_for
    from tests.herdr.test_work_cycle import git
    port, old_cycle, guard, result, task, completion, observations, old_log = ready(boundary_workspace, monkeypatch)
    identity = old_cycle.plan.identity
    workspace = old_cycle.root
    info = workspace.stat()
    rec = SimpleNamespace(node=SimpleNamespace(id=identity.task_id, objective="Repair approved behavior",
        role="writer", tools=guard.grant.scope.tools, permissions=("workspace-write",)),
        run_token=identity.run_token, idempotency_key="original", attempts=1,
        fencing_token=identity.fencing_token, repo=task["repo"], issue="86",
        parent_task_id=identity.parent_task_id, parent_agent_id=identity.parent_agent_id,
        agent_id=identity.agent_id, execution_agent=identity.agent_id, execution_pane="child-pane",
        execution_marker="child-marker", execution_sandbox_verified=True,
        execution_sandbox_attestation={"invocation_policy":task["execution_session"]["invocation_policy"]},
        worktree_identity=f"{workspace}|{info.st_dev}:{info.st_ino}", ownership=None, owned_write_mounts=None)
    assert child_identity(rec) == identity
    spec = child_spec(rec)
    approved = replace(old_cycle.plan, spec_sha256=spec)
    # The actual child port sees the clean baseline, before the child edits.
    (workspace/"result.py").write_text(git(workspace, "show", approved.base_sha+":result.py")+"\n")
    log = AuditLog(boundary_workspace/"host"/"child-events.jsonl")
    factory = HostWorkContractFactory(approve=lambda **kwargs:approved,
        environment=port.committer.policy.environment, storage=boundary_workspace/"host"/"child-checks",
        audit_log=log, git=old_cycle.git)
    factory.local_commit_policy=port.committer.policy
    factory.result_authority=port.result_authority
    factory.task_store_root=boundary_workspace
    completion=deepcopy(completion)
    completion["spec_hash"]=spec
    completion["plan_hash"]=digest({key:value for key,value in completion.items() if key not in {"plan_hash","baseline"}})
    authority=ChildCompletionAuthority(store=store_for(boundary_workspace,child_task(rec)),
        approve=lambda **kwargs:completion, collector=lambda *args:pytest.fail("no CI fixture required for local handoff"))
    authority.work_contracts={"version":2,"children":{spec:{"kind":"coding","work_contract_version":1}}}
    authority.prepare(rec)
    requested=[]
    def config_fixture(root, current, **kwargs):
        requested.append((root,current,kwargs))
        assert root==boundary_workspace and kwargs["spec_sha256"]==spec
        return factory
    monkeypatch.setattr("herdr.work_configuration.build_root_work_factory",config_fixture)
    bootstrap=SimpleNamespace()
    launch=SimpleNamespace(grant=guard.grant,mount=SimpleNamespace(bootstrap=bootstrap))
    actual=authority.prepare_work(rec,launch)
    cycle=factory.cycle(identity)
    baseline = [event for event in log.replay() if event.get("event") == "work_baseline"]
    assert cycle.phase is WorkPhase.WORK and len(requested)==1
    assert len(baseline)==1 and baseline[0]["checks"][0]["exit_code"]==1
    assert bootstrap.work_authority==factory.authorize_invocation
    assert bootstrap.work_verify==factory.verify_request
    (workspace/"result.py").write_text("def approved():\n    return 3\n\ndef foreign():\n    return 2\n")
    response=bootstrap.work_verify(identity,guard.grant.hash,"child-original",{"pr_number":None})
    cycle=factory.cycle(identity)
    assert cycle.phase is WorkPhase.HANDOFF and result.read_bytes()==b""
    artifact=response["submission"]["evidence"][0]["herdr_completion"]["artifact"]
    before=log._path.read_bytes()
    monkeypatch.setattr("herdr.work_handoff.verify_invocation_session",
                        lambda *args:pytest.fail("recovery cannot require a live child SDK"))
    assert authority.recover_local_result(rec,result)
    payload=json.loads(result.read_bytes())
    assert payload["evidence"][0]["herdr_completion"]["artifact"]==json.loads(json.dumps(artifact))
    assert authority.recover_local_result(rec,result) and log._path.read_bytes()==before
    assert git(workspace,"rev-parse","HEAD")==artifact["commit_sha"]
    with pytest.raises(PolicyDenied):
        bootstrap.work_authority(identity,guard.grant.hash,kind="provider")
