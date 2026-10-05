"""Durable, concurrent limits use the existing audit rather than a parallel queue."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path

import pytest

from herdr.evidence import digest
from herdr.scheduler import AuditLog
from herdr.security import InvocationIdentity
from herdr.work_budget import (BudgetAllocation,BudgetBlocked,BudgetLimits,Demand,Failure,
    FailureKind,StopScope,Usage,WorkBudgetAuthority)
from herdr.work_cycle import CheckResult

def h(value):
    return hashlib.sha256(str(value).encode()).hexdigest()

def identity(**changes):
    return replace(InvocationIdentity("github:org/repo","worker","parent","parent-task","task","run",1),**changes)

def limits(**changes):
    return replace(BudgetLimits(10000,100000,10,1000,1000,2,1,2,3),**changes)

def allocation(label="work",parent=None,series_plan_sha256=None,**changes):
    return BudgetAllocation(h("allocation:"+label),"github:org/repo",h("work:"+label),
        h("lineage"),h("authorization:"+label),limits(**changes),parent,series_plan_sha256)

def authority(tmp_path,alloc=None,clock=None):
    alloc=alloc or allocation()
    log=AuditLog(tmp_path/"host"/"audit.jsonl")
    auth=WorkBudgetAuthority(audit_log=log,authorize=lambda **kw:alloc,clock_ms=clock or (lambda:1000))
    admitted=auth.open(consumer=alloc.consumer,work_key=alloc.work_key,lineage_key=alloc.lineage_key,
        authorization_reference=alloc.authorization_reference)
    assert admitted==alloc
    return auth,alloc,log

def reserve(auth,alloc,key="operation",**changes):
    args=dict(allocation_id=alloc.allocation_id,semantic_key=h(key),identity=identity(),
        plan_sha256=h("plan"),provider="provider-a",demand=Demand(100,1,100,100))
    args.update(changes)
    return auth.reserve(**args)

def settle(auth,operation,**changes):
    args=dict(work_ms=100,model_calls=1,tokens=100,cost_microusd=100,proof_sha256=h(operation))
    args.update(changes)
    return auth.settle(operation,Usage(**args))

def failure(kind=FailureKind.IMPLEMENTATION,label="check",tree="tree",output="error"):
    return Failure(kind,"checker_failed",h(label),h(tree),h(output))

def begin(auth,alloc,**changes):
    args=dict(allocation_id=alloc.allocation_id,identity=identity(),plan_sha256=h("plan"))
    args.update(changes)
    return auth.begin_implementation(**args)

def test_restart_session_provider_and_requeue_preserve_consumption(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc)
    settle(auth,op)
    resumed=WorkBudgetAuthority(audit_log=AuditLog(log._path),authorize=lambda **kw:pytest.fail("no budget refill"),
        clock_ms=lambda:1001)
    assert resumed.open(consumer=alloc.consumer,work_key=alloc.work_key,lineage_key=alloc.lineage_key,
        authorization_reference=alloc.authorization_reference)==alloc
    reserve(resumed,alloc,"second",identity=identity(agent_id="new-session",task_id="renamed-task"),
        provider="provider-b")
    state=resumed.snapshot(alloc.allocation_id)
    assert state["charged_upper_bounds"]["model_calls"]==2 and state["inflight"]==1
    with pytest.raises(BudgetBlocked,match="reconcile original"):
        reserve(resumed,alloc,identity=identity(agent_id="new-session"),provider="provider-b")
    assert resumed.reconcile(op)["identity"]==identity().to_json()

def test_changed_work_authorization_cannot_refill_same_key(tmp_path):
    auth,alloc,log=authority(tmp_path)
    with pytest.raises(BudgetBlocked,match="authority changed"):
        auth.open(consumer=alloc.consumer,work_key=alloc.work_key,lineage_key=h("new"),
            authorization_reference=h("new auth"))

def test_unknown_price_blocks_before_any_economic_reservation(tmp_path):
    auth,alloc,log=authority(tmp_path)
    with pytest.raises(BudgetBlocked,match="unknown price"):
        reserve(auth,alloc,demand=Demand(100,1,10,None))
    assert auth.snapshot(alloc.allocation_id)["inflight"]==0

def test_missing_measured_usage_is_explicit_and_never_zero(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc)
    auth.settle(op,Usage(None,None,None,None,h("terminal effect proof")))
    state=auth.snapshot(alloc.allocation_id)
    assert state["unknown_measurements"]==["cost_microusd","model_calls","tokens","work_ms"]
    assert state["charged_upper_bounds"]=={"work_ms":100,"model_calls":1,"tokens":100,"cost_microusd":100}

def test_uncertain_operation_retains_inflight_capacity_and_identity(tmp_path):
    auth,alloc,log=authority(tmp_path,allocation(max_concurrency=1))
    op=reserve(auth,alloc)
    with pytest.raises(BudgetBlocked,match="parallel"):
        reserve(auth,alloc,"replacement")
    assert auth.reconcile(op)["usage"] is None
    assert reserve(auth,alloc)==op
    assert auth.snapshot(alloc.allocation_id)["inflight"]==1

def test_parent_children_atomically_reserve_last_shared_capacity(tmp_path):
    parent=allocation(max_concurrency=1)
    auth,parent,log=authority(tmp_path,parent)
    children=[allocation("child-"+str(i),parent.allocation_id) for i in range(2)]
    for child in children:
        auth.authorize=lambda child=child,**kw:child
        auth.open(consumer=child.consumer,work_key=child.work_key,lineage_key=child.lineage_key,
            authorization_reference=child.authorization_reference)
    def compete(child):
        other=WorkBudgetAuthority(audit_log=AuditLog(log._path),authorize=lambda **kw:child,clock_ms=lambda:1000)
        try: return reserve(other,child,child.allocation_id)
        except BudgetBlocked: return None
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(compete,children))
    assert sum(x is not None for x in results)==1
    assert auth.snapshot(parent.allocation_id)["charged_upper_bounds"]["tokens"]==100
    assert auth.snapshot(parent.allocation_id)["inflight"]==1

def test_child_cannot_exceed_own_limit_even_when_parent_has_room(tmp_path):
    auth,parent,log=authority(tmp_path)
    child=allocation("child",parent.allocation_id,max_tokens=50)
    auth.authorize=lambda **kw:child
    auth.open(consumer=child.consumer,work_key=child.work_key,lineage_key=child.lineage_key,
        authorization_reference=child.authorization_reference)
    with pytest.raises(BudgetBlocked,match="tokens"):
        reserve(auth,child)

def test_settlement_is_immutable_and_idempotent(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc)
    proof=settle(auth,op)
    assert settle(auth,op)==proof
    with pytest.raises(BudgetBlocked,match="overwritten"):
        settle(auth,op,tokens=0)
    assert len([x for x in log.replay() if x["event"]=="work_budget_settle"])==1

def test_actual_usage_over_quote_is_preserved_and_stops_new_work(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc)
    settle(auth,op,tokens=150)
    assert auth.snapshot(alloc.allocation_id)["charged_upper_bounds"]["tokens"]==150
    with pytest.raises(BudgetBlocked,match="stopped"):
        reserve(auth,alloc,"new")
    assert auth.reconcile(op)["usage"]["tokens"]==150

def test_default_three_attempts_include_initial_and_cannot_reset_on_restart(tmp_path):
    auth,alloc,log=authority(tmp_path)
    first=begin(auth,alloc)
    assert first.attempt==1 and begin(auth,alloc)==first
    for number in (2,3):
        f=failure(label=number,tree=number,output=number)
        auth.record_failure(alloc.allocation_id,f)
        permit=begin(auth,alloc,reason_code="fix_checker",failure_check_sha256=f.check_sha256,
            diff_sha256=h(number),changed_files=1,changed_lines=3)
        assert permit.attempt==number
    auth=WorkBudgetAuthority(audit_log=AuditLog(log._path),authorize=lambda **kw:alloc,clock_ms=lambda:1000)
    f=failure(label=4,tree=4)
    auth.record_failure(alloc.allocation_id,f)
    with pytest.raises(BudgetBlocked,match="attempts_exhausted"):
        begin(auth,alloc,identity=identity(agent_id="renamed",task_id="rename"),reason_code="fix_checker",
            failure_check_sha256=f.check_sha256,diff_sha256=h(4),changed_files=1,changed_lines=3)
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"]==3

def test_nondefault_attempt_limit_needs_versioned_host_reference():
    with pytest.raises(BudgetBlocked,match="reference"):
        limits(max_implementation_attempts=4)
    assert limits(max_implementation_attempts=4,consumer_policy_version="consumer-exception-2",
        attempt_override_reference=h("explicit reviewed exception")).max_implementation_attempts==4

def test_same_error_unchanged_tree_blocks_even_with_new_check_id(tmp_path):
    auth,alloc,log=authority(tmp_path)
    begin(auth,alloc)
    f=failure()
    auth.record_failure(alloc.allocation_id,f)
    begin(auth,alloc,reason_code="repair",failure_check_sha256=f.check_sha256,
        diff_sha256=h("edit"),changed_files=1,changed_lines=2)
    again=failure(label="another observation")
    auth.record_failure(alloc.allocation_id,again)
    with pytest.raises(BudgetBlocked,match="unchanged code"):
        begin(auth,alloc,reason_code="repair",failure_check_sha256=again.check_sha256,
            diff_sha256=h("edit-again"),changed_files=1,changed_lines=2)

@pytest.mark.parametrize("kind",[FailureKind.BASELINE,FailureKind.FLAKY,FailureKind.PROVIDER,
    FailureKind.TOOL,FailureKind.DEPENDENCY,FailureKind.POLICY,FailureKind.TRANSPORT])
def test_nonimplementation_failure_cannot_spend_implementation_retry(tmp_path,kind):
    auth,alloc,log=authority(tmp_path)
    begin(auth,alloc)
    f=failure(kind)
    auth.record_failure(alloc.allocation_id,f)
    with pytest.raises(BudgetBlocked,match="implementation failure"):
        begin(auth,alloc,reason_code="stronger_model",failure_check_sha256=f.check_sha256,
            diff_sha256=h("edit"),changed_files=1,changed_lines=2)

def test_small_diff_and_new_check_are_required_before_repair(tmp_path):
    auth,alloc,log=authority(tmp_path)
    begin(auth,alloc)
    with pytest.raises(BudgetBlocked,match="checker failure"):
        begin(auth,alloc,reason_code="repair",failure_check_sha256=h("invented"),
            diff_sha256=h("edit"),changed_files=1,changed_lines=2)
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"]==1

def alternative(auth,alloc,kind=FailureKind.TOOL,**changes):
    f=failure(kind)
    auth.record_failure(alloc.allocation_id,f)
    args=dict(allocation_id=alloc.allocation_id,kind=kind,contract_sha256=h("plan"),
        grant_sha256=h("grant"),failure_check_sha256=f.check_sha256,host_approval=lambda event:h(event))
    args.update(changes)
    return auth.one_alternative(**args)

def test_tool_alternative_once_preserves_exact_contract_and_permissions(tmp_path):
    auth,alloc,log=authority(tmp_path)
    proof=alternative(auth,alloc)
    assert len(proof)==64
    with pytest.raises(BudgetBlocked,match="alternative budget"):
        alternative(auth,alloc)

def test_dependency_alternative_is_once_and_workspace_local(tmp_path):
    auth,alloc,log=authority(tmp_path)
    with pytest.raises(BudgetBlocked,match="workspace local"):
        alternative(auth,alloc,FailureKind.DEPENDENCY)
    alternative(auth,alloc,FailureKind.DEPENDENCY,workspace_local=True)
    with pytest.raises(BudgetBlocked,match="alternative budget"):
        alternative(auth,alloc,FailureKind.DEPENDENCY,workspace_local=True)

def test_unknown_provider_delivery_cannot_escalate_or_fallback(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc)
    with pytest.raises(BudgetBlocked,match="reconcile"):
        alternative(auth,alloc,FailureKind.PROVIDER,original_operation_id=op,pre_delivery_proven=True)
    assert auth.reconcile(op)["usage"] is None
    settle(auth,op,model_calls=0,tokens=0,cost_microusd=0)
    alternative(auth,alloc,FailureKind.PROVIDER,original_operation_id=op,pre_delivery_proven=True)
    assert auth.snapshot(alloc.allocation_id)["fallbacks"]==1

def test_flaky_one_same_code_rerun_records_instability_and_does_not_auto_pass(tmp_path):
    auth,alloc,log=authority(tmp_path)
    proof=alternative(auth,alloc,FailureKind.FLAKY,same_tree_sha256=h("tree"))
    rerun=CheckResult("tests",h("plan"),h("environment"),h("tree"),0,h("pass"),False,1,h("isolation"))
    assert auth.record_flaky_rerun(alternative_sha256=proof,rerun_check=rerun,
        host_approval=lambda *a:True) is True
    state=auth.snapshot(alloc.allocation_id)
    assert state["instabilities"][0]["unstable"] is True and state["active_stops"]
    with pytest.raises(BudgetBlocked,match="stopped"):
        reserve(auth,alloc,"unproven-pass")

def test_scoped_provider_stop_leaves_independent_provider_and_reconciliation_available(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc)
    auth.stop(stop_id=h("stop"),scope=StopScope.PROVIDER,target="provider-a",source="consumer-policy",
        reason_code="provider_unavailable",resume_condition="provider_health_and_valid_grant")
    with pytest.raises(BudgetBlocked,match="stopped"):
        reserve(auth,alloc,"new")
    reserve(auth,alloc,"independent",provider="provider-b")
    assert auth.reconcile(op)["operation_id"]==op

def test_resume_revalidates_grant_and_preserves_old_consumption(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc);settle(auth,op)
    stop_id=h("stop")
    auth.stop(stop_id=stop_id,scope=StopScope.TASK,target="task",source="consumer-policy",
        reason_code="revoked_approval",resume_condition="fresh_approval")
    with pytest.raises(BudgetBlocked,match="grant not valid"):
        auth.resume(stop_id=stop_id,allocation_id=alloc.allocation_id,identity=identity(),
            valid_grant_sha256=h("expired"),host_approval=lambda *a:False)
    auth.resume(stop_id=stop_id,allocation_id=alloc.allocation_id,identity=identity(),
        valid_grant_sha256=h("fresh"),host_approval=lambda *a:True)
    assert auth.snapshot(alloc.allocation_id)["charged_upper_bounds"]["model_calls"]==1
    reserve(auth,alloc,"after-resume")

def test_clock_regression_and_elapsed_deadline_block_new_work_but_preserve_reconciliation(tmp_path):
    clock=[1000]
    auth,alloc,log=authority(tmp_path,clock=lambda:clock[0])
    op=reserve(auth,alloc)
    clock[0]=999
    with pytest.raises(BudgetBlocked,match="regressed"):
        reserve(auth,alloc,"new")
    clock[0]=101001
    with pytest.raises(BudgetBlocked,match="elapsed"):
        reserve(auth,alloc,"new")
    assert auth.reconcile(op)["usage"] is None

def test_series_caps_survive_restart_rename_and_duplicate_delivery(tmp_path):
    auth,alloc,log=authority(tmp_path,allocation(max_variants=1,max_trials=1,series_plan_sha256=h("series plan")))
    variant=h("variant");trial=h("baseline trial")
    v=auth.declare_variant(allocation_id=alloc.allocation_id,variant_sha256=variant,
        plan_sha256=h("series plan"),host_approval=lambda event:h(event))
    assert auth.declare_variant(allocation_id=alloc.allocation_id,variant_sha256=variant,
        plan_sha256=h("series plan"),host_approval=lambda event:pytest.fail("must reuse marker"))==v
    auth.begin_trial(allocation_id=alloc.allocation_id,variant_sha256=variant,trial_sha256=trial,
        plan_sha256=h("series plan"),reason_code="planned_baseline",host_approval=lambda event:h(event))
    reserve(auth,alloc,variant_sha256=variant,trial_sha256=trial)
    restarted=WorkBudgetAuthority(audit_log=AuditLog(log._path),authorize=lambda **kw:alloc,clock_ms=lambda:1000)
    with pytest.raises(BudgetBlocked,match="variant budget"):
        restarted.declare_variant(allocation_id=alloc.allocation_id,variant_sha256=h("renamed"),
            plan_sha256=h("series plan"),host_approval=lambda event:h(event))
    with pytest.raises(BudgetBlocked,match="trial budget"):
        restarted.begin_trial(allocation_id=alloc.allocation_id,variant_sha256=variant,trial_sha256=h("holdout"),
            plan_sha256=h("series plan"),reason_code="holdout",host_approval=lambda event:h(event))
    assert restarted.snapshot(alloc.allocation_id)["trials"]==1

def test_free_holdout_still_consumes_tokens_calls_time_and_parent_capacity(tmp_path):
    auth,alloc,log=authority(tmp_path,allocation(max_model_calls=1))
    op=reserve(auth,alloc,demand=Demand(100,1,100,0));settle(auth,op,cost_microusd=0)
    with pytest.raises(BudgetBlocked,match="model_calls"):
        reserve(auth,alloc,"holdout",demand=Demand(100,1,1,0))

def test_corrupted_audit_cannot_invent_price_or_reset_attempts(tmp_path):
    auth,alloc,log=authority(tmp_path)
    reserve(auth,alloc);begin(auth,alloc)
    events=log.replay()
    for change in ("price","attempt"):
        altered=json.loads(json.dumps(events))
        event=next(x for x in altered if x["event"]==("work_budget_reserve" if change=="price" else "work_budget_attempt"))
        if change=="price": event["demand"]["cost_microusd"]=None
        else: event["attempt"]=0
        event["event_sha256"]=digest({k:v for k,v in event.items() if k!="event_sha256"})
        other=tmp_path/"host"/(change+".jsonl")
        other.write_text("".join(json.dumps(x)+"\n" for x in altered))
        with pytest.raises(BudgetBlocked):
            WorkBudgetAuthority(audit_log=AuditLog(other),authorize=lambda **kw:alloc,
                clock_ms=lambda:1000).snapshot(alloc.allocation_id)

def test_pre_effect_claim_is_durable_and_duplicate_start_only_reconciles(tmp_path):
    auth,alloc,log=authority(tmp_path)
    op=reserve(auth,alloc)
    assert auth.claim_start(op) is True
    restarted=WorkBudgetAuthority(audit_log=AuditLog(log._path),authorize=lambda **kw:alloc,clock_ms=lambda:1000)
    assert restarted.claim_start(op) is False
    assert restarted.reconcile(op)["started"] is True
    assert restarted.reconcile(op)["usage"] is None

def _process_reservation(path,alloc,ready,go,result,label):
    auth=WorkBudgetAuthority(audit_log=AuditLog(Path(path)),authorize=lambda **kw:alloc,clock_ms=lambda:1000)
    ready.put(label)
    go.wait(10)
    try: result.put(reserve(auth,alloc,label))
    except BudgetBlocked: result.put(None)

def test_separate_processes_atomically_compete_for_final_capacity(tmp_path):
    import multiprocessing
    auth,alloc,log=authority(tmp_path,allocation(max_concurrency=1))
    context=multiprocessing.get_context("fork")
    ready,result,go=context.Queue(),context.Queue(),context.Event()
    processes=[context.Process(target=_process_reservation,
        args=(str(log._path),alloc,ready,go,result,str(i))) for i in range(2)]
    for process in processes: process.start()
    for _ in processes: ready.get(timeout=10)
    go.set()
    outcomes=[result.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(10)
        assert process.exitcode==0
    assert sum(x is not None for x in outcomes)==1
    assert auth.snapshot(alloc.allocation_id)["inflight"]==1

def budget_factory_fixture(tmp_path):
    from tests.herdr.test_work_contract_host import factory_fixture
    factory,root,plan,granted,log=factory_fixture(tmp_path)
    alloc=allocation(max_work_ms=1000000,max_elapsed_ms=1000000)
    auth=WorkBudgetAuthority(audit_log=log,authorize=lambda **kwargs:alloc)
    plan=replace(plan,budget_reference=alloc.hash)
    factory.approve=lambda **kwargs:plan
    factory.budget_authority=auth
    factory.budget_binding=lambda **kwargs:alloc
    return factory,root,plan,granted,log

def repair_cycle(tmp_path):
    from tests.herdr.test_work_cycle import setup,trusted_git,runner
    from herdr.work_cycle import WorkCycle
    _,root,template,log=setup(tmp_path)
    alloc=allocation(max_work_ms=1000000)
    auth=WorkBudgetAuthority(audit_log=log,authorize=lambda **kw:alloc,clock_ms=lambda:1000)
    auth.open(consumer=alloc.consumer,work_key=alloc.work_key,lineage_key=alloc.lineage_key,
        authorization_reference=alloc.authorization_reference)
    plan=replace(template,budget_reference=alloc.hash)
    cycle=WorkCycle(plan,root,log,git=trusted_git(root),budget_authority=auth)
    cycle.start(runner)
    auth.begin_implementation(allocation_id=alloc.allocation_id,identity=plan.identity,plan_sha256=plan.hash)
    return cycle,auth,alloc,root,log

def test_failed_work_cycle_reopens_only_with_new_checker_proof_and_durable_permit(tmp_path):
    from tests.herdr.test_work_cycle import runner,edit,trusted_git
    from herdr.work_cycle import WorkContractError,WorkCycle,WorkPhase
    cycle,auth,alloc,root,log=repair_cycle(tmp_path)
    edit(root)
    with pytest.raises(WorkContractError,match="check failed"):
        cycle.verify(lambda *a:replace(runner(*a),exit_code=1))
    proof=CheckResult(**cycle.verified_checks["tests"])
    with pytest.raises(WorkContractError,match="approved repair"):
        cycle.verify(lambda *a:pytest.fail("no unapproved second check"))
    observed=Failure(FailureKind.IMPLEMENTATION,"test_failed",proof.hash,proof.tree_sha256,proof.output_sha256)
    permit=cycle.reopen_repair(allocation_id=alloc.allocation_id,failure=observed,reason_code="fix_return_value",
        diff_sha256=h("approved two-line patch"),changed_files=1,changed_lines=2,repair_paths=("result.py",))
    assert permit.attempt==2 and cycle.implementation_allowed()
    restored=WorkCycle(cycle.plan,root,log,git=trusted_git(root),budget_authority=auth)
    assert restored.phase is WorkPhase.WORK
    (root/"result.py").write_text("def approved():\n    return 4\n\ndef foreign():\n    return 2\n")
    restored.verify(runner)
    assert restored.phase is WorkPhase.HYGIENE
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"]==2
    with pytest.raises(WorkContractError):
        restored.reopen_repair(allocation_id=alloc.allocation_id,failure=observed,
            reason_code="more_features",diff_sha256=h("extra"),changed_files=1,changed_lines=2,repair_paths=("result.py",))

def test_replayed_repair_cannot_forge_budget_permit_or_ignore_missing_authority(tmp_path):
    from tests.herdr.test_work_cycle import runner,edit,trusted_git
    from herdr.work_cycle import WorkContractError,WorkCycle
    cycle,auth,alloc,root,log=repair_cycle(tmp_path)
    edit(root)
    with pytest.raises(WorkContractError):
        cycle.verify(lambda *a:replace(runner(*a),exit_code=1))
    proof=CheckResult(**cycle.verified_checks["tests"])
    observed=Failure(FailureKind.IMPLEMENTATION,"test_failed",proof.hash,proof.tree_sha256,proof.output_sha256)
    cycle.reopen_repair(allocation_id=alloc.allocation_id,failure=observed,reason_code="repair",
        diff_sha256=h("patch"),changed_files=1,changed_lines=2,repair_paths=("result.py",))
    with pytest.raises(WorkContractError,match="budget authority"):
        WorkCycle(cycle.plan,root,log,git=trusted_git(root))
    altered=log.replay()
    next(x for x in altered if x["event"]=="work_repair")["permit"]["event_sha256"]=h("fake")
    log._path.write_text("".join(json.dumps(x)+"\n" for x in altered))
    with pytest.raises(BudgetBlocked,match="durable host audit"):
        WorkCycle(cycle.plan,root,log,git=trusted_git(root),budget_authority=auth)

def test_budgeted_physical_check_replay_uses_sealed_same_result_without_second_execution(tmp_path):
    from tests.herdr.test_work_cycle import runner
    from herdr.work_budget import BudgetedCheckRunner
    cycle,auth,alloc,root,log=repair_cycle(tmp_path)
    calls=[]
    wrapped=BudgetedCheckRunner(auth,alloc,lambda *a:calls.append(a) or runner(*a),"verification")
    tree=h("fixed tree")
    first=wrapped(cycle.plan.checks[0],root,cycle.plan,tree)
    same=BudgetedCheckRunner(WorkBudgetAuthority(audit_log=AuditLog(log._path),
        authorize=lambda **kw:alloc,clock_ms=lambda:1000),alloc,
        lambda *a:pytest.fail("never run a settled physical check twice"),"verification")
    assert same(cycle.plan.checks[0],root,cycle.plan,tree)==first and len(calls)==1
    assert auth.snapshot(alloc.allocation_id)["charged_upper_bounds"]["work_ms"]==1

def test_model_policy_quote_pre_effect_claim_stop_and_unknown_response_no_escalation(tmp_path):
    from herdr.work_budget import BudgetModelPort,ModelReservation
    from herdr.security import InvocationGuard,ProviderRequest
    from herdr.capability import DataClass,Egress,Retention,Training
    from tests.herdr.test_security import grant
    factory_fixture=budget_factory_fixture
    factory,root,plan,granted,log=factory_fixture(tmp_path)
    cycle=factory.prepare(identity=plan.identity,workspace=root,grant=granted,spec_sha256=plan.spec_sha256)
    auth=factory.budget_authority
    alloc=factory.allocations[digest(plan.identity.to_json())]
    guard=InvocationGuard(granted)
    port=BudgetModelPort(authority=auth,allocation=alloc,identity=cycle.plan.identity,
        plan_sha256=cycle.plan.hash,grant_sha256=granted.hash,
        quote=lambda request:ModelReservation(h("semantic implementation call"),Demand(100,1,100,100),request.provider))
    request=ProviderRequest("provider-a","eu-central",DataClass.INTERNAL,Egress.REGION_BOUND,
        Retention.LIMITED,Training.EXCLUDED)
    operation=port.reserve(request,guard=guard,cycle=cycle)
    port.begin_effect(operation,request,guard=guard,cycle=cycle)
    restarted=BudgetModelPort(authority=WorkBudgetAuthority(audit_log=AuditLog(log._path),
        authorize=lambda **kw:alloc,clock_ms=auth.clock_ms),allocation=alloc,identity=cycle.plan.identity,
        plan_sha256=cycle.plan.hash,grant_sha256=granted.hash,quote=port.quote)
    assert restarted.reserve(request,guard=guard,cycle=cycle)==operation
    with pytest.raises(BudgetBlocked,match="reconcile original"):
        restarted.begin_effect(operation,request,guard=guard,cycle=cycle)
    cycle.phase=__import__("herdr.work_cycle",fromlist=["WorkPhase"]).WorkPhase.HYGIENE
    with pytest.raises(BudgetBlocked,match="work phase"):
        restarted.reserve(request,guard=guard,cycle=cycle)
    assert port.reconcile(operation)["usage"] is None

def test_budget_stop_survives_task_rename_in_same_allocation(tmp_path):
    auth,alloc,log=authority(tmp_path,allocation(max_model_calls=1))
    op=reserve(auth,alloc)
    settle(auth,op)
    with pytest.raises(BudgetBlocked,match="model_calls"):
        reserve(auth,alloc,"over-budget")
    with pytest.raises(BudgetBlocked,match="allocation policy"):
        auth.require_active(alloc.allocation_id,identity(task_id="renamed-task"))

def test_legacy_retry_audit_rows_keep_original_counter_meaning(tmp_path):
    log=AuditLog(tmp_path/"host"/"audit.jsonl")
    log.append({"event":"retry","task_id":"historical","attempts":4,"max_attempts":4})
    log.flush()
    alloc=allocation()
    auth=WorkBudgetAuthority(audit_log=log,authorize=lambda **kw:alloc,clock_ms=lambda:1000)
    auth.open(consumer=alloc.consumer,work_key=alloc.work_key,lineage_key=alloc.lineage_key,
        authorization_reference=alloc.authorization_reference)
    assert log.replay()[0]=={"event":"retry","task_id":"historical","attempts":4,"max_attempts":4}
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"]==0


def test_changed_stage_authorization_and_expired_grant_deny_at_actual_model_start(tmp_path,monkeypatch):
    from datetime import UTC,datetime,timedelta
    from herdr.work_budget import BudgetModelPort,ModelReservation
    from herdr.security import InvocationGuard,ProviderRequest,PolicyDenied
    from herdr.capability import DataClass,Egress,Retention,Training
    factory_fixture=budget_factory_fixture
    factory,root,plan,granted,log=factory_fixture(tmp_path)
    cycle=factory.prepare(identity=plan.identity,workspace=root,grant=granted,spec_sha256=plan.spec_sha256)
    auth=factory.budget_authority
    alloc=factory.allocations[digest(plan.identity.to_json())]
    guard=InvocationGuard(granted)
    port=BudgetModelPort(authority=auth,allocation=alloc,identity=plan.identity,
        plan_sha256=plan.hash,grant_sha256=granted.hash,
        quote=lambda req:ModelReservation(h("call"),Demand(100,1,100,100),req.provider))
    req=ProviderRequest("provider-a","eu-central",DataClass.INTERNAL,Egress.REGION_BOUND,
        Retention.LIMITED,Training.EXCLUDED)
    op=port.reserve(req,guard=guard,cycle=cycle)
    auth.stop(stop_id=h("revoked"),scope=StopScope.TASK,target=plan.identity.task_id,
        source="host-policy",reason_code="approval_revoked",resume_condition="review")
    with pytest.raises(BudgetBlocked,match="stopped"):
        port.begin_effect(op,req,guard=guard,cycle=cycle)
    assert not auth.reconcile(op)["started"]
    # Neither an altered grant nor PASS can reuse the pending reservation.
    monkeypatch.setattr("herdr.security.SecurityGrant.is_active",lambda self,at=None:False)
    with pytest.raises(PolicyDenied,match="grant_expired"):
        port.begin_effect(op,req,guard=guard,cycle=cycle)
    assert not auth.reconcile(op)["started"]

def test_broken_symlink_audit_and_malformed_replay_never_start_new_work(tmp_path):
    auth,alloc,log=authority(tmp_path)
    log._path.unlink()
    log._path.symlink_to(tmp_path/"missing"/"redirect.jsonl")
    with pytest.raises(BudgetBlocked,match="symlink"):
        reserve(auth,alloc)
    assert not (tmp_path/"missing").exists()

def test_host_clock_regression_between_check_and_append_does_not_publish_invalid_event(tmp_path):
    values=iter([1000,1000,1001,999])
    auth,alloc,log=authority(tmp_path,clock=lambda:next(values))
    with pytest.raises(BudgetBlocked,match="regressed"):
        reserve(auth,alloc)
    assert len(log.replay())==1


def test_repair_claimed_small_patch_cannot_change_unapproved_path_or_exceed_lines(tmp_path):
    from tests.herdr.test_work_cycle import runner,edit
    from herdr.work_cycle import WorkContractError
    cycle,auth,alloc,root,log=repair_cycle(tmp_path)
    edit(root)
    with pytest.raises(WorkContractError):
        cycle.verify(lambda *a:replace(runner(*a),exit_code=1))
    proof=CheckResult(**cycle.verified_checks["tests"])
    observed=Failure(FailureKind.IMPLEMENTATION,"test_failed",proof.hash,proof.tree_sha256,proof.output_sha256)
    cycle.reopen_repair(allocation_id=alloc.allocation_id,failure=observed,reason_code="repair",
        diff_sha256=h("two-line proposal"),changed_files=1,changed_lines=2,repair_paths=("result.py",))
    (root/"result.py").write_text("".join("changed_"+str(i)+"=1\n" for i in range(25)))
    with pytest.raises(WorkContractError,match="line budget"):
        cycle.verify(lambda *a:pytest.fail("oversized repair never reaches checker"))
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"]==2


def test_finite_series_cannot_bypass_trials_by_switching_operation_purpose(tmp_path):
    auth,alloc,log=authority(tmp_path,allocation(series_plan_sha256=h("series plan")))
    for purpose in ("model","baseline","repair","review","holdout"):
        with pytest.raises(BudgetBlocked,match="authorized trial"):
            reserve(auth,alloc,purpose,operation_kind=purpose)
    assert auth.snapshot(alloc.allocation_id)["inflight"]==0

def test_child_cannot_escape_parent_series_by_renaming_to_repair(tmp_path):
    auth,parent,log=authority(tmp_path,allocation(series_plan_sha256=h("series plan")))
    child=allocation("child",parent.allocation_id)
    auth.authorize=lambda **kw:child
    with pytest.raises(BudgetBlocked,match="lineage mismatch"):
        auth.open(consumer=child.consumer,work_key=child.work_key,lineage_key=child.lineage_key,
            authorization_reference=child.authorization_reference)

def test_same_audit_composition_reenters_without_second_flock_or_duplicate_effect(tmp_path):
    auth,alloc,log=authority(tmp_path)
    second=WorkBudgetAuthority(audit_log=AuditLog(log._path),authorize=lambda **kw:alloc,clock_ms=lambda:1000)
    with auth._serialized():
        with second._serialized():
            op=reserve(second,alloc)
            assert auth.snapshot(alloc.allocation_id)["inflight"]==1
            assert second.claim_start(op) is True
        assert auth.claim_start(op) is False
    assert len([x for x in log.replay() if x["event"]=="work_budget_start"])==1

def test_fork_does_not_inherit_permission_to_skip_parent_process_flock(tmp_path):
    import multiprocessing
    import queue
    auth,alloc,log=authority(tmp_path,allocation(max_concurrency=1))
    context=multiprocessing.get_context("fork")
    ready,result,go=context.Queue(),context.Queue(),context.Event()
    with auth._serialized():
        child=context.Process(target=_process_reservation,
            args=(str(log._path),alloc,ready,go,result,"forked"))
        child.start()
        ready.get(timeout=10)
        go.set()
        with pytest.raises(queue.Empty):
            result.get(timeout=0.1)
        operation=reserve(auth,alloc,"parent")
    assert result.get(timeout=10) is None
    child.join(10)
    assert child.exitcode==0 and auth.snapshot(alloc.allocation_id)["inflight"]==1

def _has_inherited_budget_descriptor(path,result):
    import os
    opened=[]
    for value in Path("/proc/self/fd").iterdir():
        try: opened.append(os.readlink(value))
        except OSError: pass
    result.put(path in opened)

def test_forked_helper_cannot_keep_parent_budget_lock_alive_after_parent_exit(tmp_path):
    import multiprocessing
    auth,alloc,log=authority(tmp_path)
    context=multiprocessing.get_context("fork")
    result=context.Queue()
    with auth._serialized():
        child=context.Process(target=_has_inherited_budget_descriptor,args=(str(auth.lock_path),result))
        child.start()
        assert result.get(timeout=10) is False
        child.join(10)
        assert child.exitcode==0


def test_four_planned_candidates_do_not_spend_implementation_retry_allowance(tmp_path):
    alloc=allocation(consumer_policy_version="work-budget-2",max_candidate_executions=4,max_search_episodes=1)
    auth,alloc,log=authority(tmp_path,alloc)
    approval=lambda event:h("approved-marker")
    auth.charge_counter(allocation_id=alloc.allocation_id,counter="search_episodes",semantic_key=h("episode"),host_approval=approval)
    for number in range(4):
        auth.charge_counter(allocation_id=alloc.allocation_id,counter="candidate_executions",
                            semantic_key=h(("candidate",number)),host_approval=approval)
    state=auth.snapshot(alloc.allocation_id)
    assert state["counters"]["candidate_executions"]==4
    assert state["implementation_attempts"]==state["implementation_retries"]==0
    restored=WorkBudgetAuthority(audit_log=AuditLog(log._path),authorize=lambda **kwargs:pytest.fail("no refill"),clock_ms=lambda:1001)
    assert restored.snapshot(alloc.allocation_id)["counters"]==state["counters"]
    with pytest.raises(BudgetBlocked,match="candidate_executions exhausted"):
        restored.charge_counter(allocation_id=alloc.allocation_id,counter="candidate_executions",
                                semantic_key=h("renamed-fifth"),host_approval=approval)
    # Exact original marker remains an idempotent reconciliation.
    restored.charge_counter(allocation_id=alloc.allocation_id,counter="candidate_executions",
                            semantic_key=h(("candidate",0)),host_approval=approval)

def test_child_candidate_slots_and_depth_respect_parent_ceiling(tmp_path):
    parent=allocation("parent",consumer_policy_version="work-budget-2",max_candidate_executions=1,max_candidate_depth=2)
    child1=allocation("child1",parent.allocation_id,consumer_policy_version="work-budget-2",max_candidate_executions=2,max_candidate_depth=3)
    child2=allocation("child2",parent.allocation_id,consumer_policy_version="work-budget-2",max_candidate_executions=2,max_candidate_depth=3)
    rows={row.work_key:row for row in (parent,child1,child2)}
    log=AuditLog(tmp_path/"host"/"audit.jsonl")
    auth=WorkBudgetAuthority(audit_log=log,authorize=lambda **kwargs:rows[kwargs["work_key"]],clock_ms=lambda:1000)
    for row in rows.values():
        auth.open(consumer=row.consumer,work_key=row.work_key,lineage_key=row.lineage_key,authorization_reference=row.authorization_reference)
    def take(row):
        try:
            return auth.charge_counter(allocation_id=row.allocation_id,counter="candidate_executions",
                                       semantic_key=h("planned"),host_approval=lambda event:h("approval"))
        except BudgetBlocked:return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(take,(child1,child2)))
    assert sum(value is not None for value in outcomes)==1
    assert auth.snapshot(parent.allocation_id)["counters"]["candidate_executions"]==1
    with pytest.raises(BudgetBlocked,match="candidate_depth exhausted"):
        auth.charge_counter(allocation_id=child1.allocation_id,counter="candidate_depth",quantity=3,
                            semantic_key=h("deeper"),host_approval=lambda event:h("approval"))

def test_historical_allocation_hash_omits_new_counter_defaults(tmp_path):
    alloc=allocation()
    original=asdict(alloc)
    for key in list(original["limits"]):
        if key in {"max_search_episodes","max_candidate_executions","max_candidate_depth","max_candidate_revisions",
                   "max_statistical_repetitions","max_tool_fallbacks","max_plan_revisions","max_delivery_reconciliations"}:
            original["limits"].pop(key)
    assert alloc.hash==digest(original)
    log=AuditLog(tmp_path/"host"/"audit.jsonl")
    auth=WorkBudgetAuthority(audit_log=log,authorize=lambda **kwargs:alloc,clock_ms=lambda:1000)
    event={"event":"work_budget_allocation","version":1,"at_ms":1000,"allocation":original}
    event["event_sha256"]=digest(event)
    log.append(event);log.flush()
    assert auth.find_allocation(alloc.hash)==alloc

def test_live_projection_does_not_rescan_history_and_external_change_is_verified(tmp_path,monkeypatch):
    auth,alloc,log=authority(tmp_path,allocation(max_concurrency=1))
    calls=[]
    original=log.replay
    monkeypatch.setattr(log,"replay",lambda:calls.append(True) or original())
    for number in range(7):
        operation=reserve(auth,alloc,("operation",number))
        settle(auth,operation)
    assert calls==[] and auth.snapshot(alloc.allocation_id)["charged_upper_bounds"]["model_calls"]==7
    records=original()
    records[0]["allocation"]["limits"]["max_tokens"]=1000000
    log._path.write_text("".join(json.dumps(row)+"\n" for row in records))
    with pytest.raises(BudgetBlocked,match="integrity"):
        auth.snapshot(alloc.allocation_id)
    assert len(calls)==1
