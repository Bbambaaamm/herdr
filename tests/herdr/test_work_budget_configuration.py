"""Actual host admission/effect ports and finite SDK deadline, without provider calls."""
from dataclasses import asdict,replace
from types import SimpleNamespace
from pathlib import Path
import signal
import time
import pytest
from herdr.evidence import digest
from herdr.security import PolicyDenied
from herdr.work_budget import BudgetAllocation,BudgetLimits,BudgetBlocked
from herdr.work_budget_configuration import bind_budget
from herdr.work_model_deadline import model_deadline,validate_text_request
from herdr.work_cycle import WorkPhase, WorkContractError
from tests.herdr.test_work_contract_host import factory_fixture

def approved_factory(tmp_path,*,repair=False):
    factory,root,original,grant,log=factory_fixture(tmp_path)
    limits=BudgetLimits(1000000,1000000,5,100000,100000,2,1,1,1)
    allocation=BudgetAllocation(digest("allocation"),grant.identity.consumer,digest("stable-work"),
        digest("lineage"),digest("authorization"),limits)
    quote={"provider":"provider-a","model":"quoted-text-model","api_mode":"chat_completions",
           "base_url":"https://quote.invalid/v1","max_request_bytes":4096,"max_output_tokens":100,
           "max_tokens":5000,"max_cost_microusd":1000,"max_work_ms":1000}
    raw={"version":1,"allocation":asdict(allocation),"ancestors":[],"model_quotes":[quote]}
    if repair:raw["repair"]={"version":1,"reason_code":"approved_behavior_repair",
                            "paths":["result.py"],"max_changed_lines":20,"failure_outputs":[original.checks[0].expected_baseline_output_sha256]}
    plan=replace(original,budget_reference=allocation.hash)
    factory.approve=lambda **kwargs:plan
    (tmp_path/"private").mkdir(mode=0o700)
    bind_budget(factory,raw,storage=tmp_path/"private",writable_roots=(root,))
    cycle=factory.prepare(identity=grant.identity,workspace=root,grant=grant,spec_sha256=plan.spec_sha256)
    return factory,root,plan,grant,cycle,raw,allocation,quote

def model_request(quote,request_id="sdk:1"):
    return {"request_id":request_id,**{key:quote[key] for key in ("provider","model","api_mode","base_url")},
            "request_sha256":digest("request"),"request_bytes":100,"output_tokens":50}

def test_real_baseline_budget_and_pre_effect_model_reservation_survive_restart(tmp_path):
    factory,root,plan,grant,cycle,raw,allocation,quote=approved_factory(tmp_path)
    state=factory.budget_authority.snapshot(allocation.allocation_id)
    assert state["implementation_attempts"]==1 and state["charged_upper_bounds"]["work_ms"]>0
    first=factory.budget_effect(grant.identity,grant.hash,"start",model_request(quote))
    with pytest.raises((BudgetBlocked,WorkContractError),match="uncertain"):
        factory.budget_effect(grant.identity,grant.hash,"start",model_request(quote,"new-session:1"))
    from herdr.work_contract_host import HostWorkContractFactory
    restored=HostWorkContractFactory(approve=lambda **kw:pytest.fail("cold recovery cannot replan"),
        environment=factory.environment,storage=factory.storage,audit_log=factory.audit_log,git=factory.git)
    bind_budget(restored,raw,storage=tmp_path/"private",writable_roots=(root,),recovery=True)
    recovered=restored.recover(identity=grant.identity,workspace=root,spec_sha256=plan.spec_sha256,
        grant_sha256=grant.hash,plan_sha256=plan.hash)
    assert recovered.phase is WorkPhase.WORK
    with pytest.raises((BudgetBlocked,WorkContractError),match="uncertain"):
        restored.budget_effect(grant.identity,grant.hash,"start",model_request(quote,"renamed:1"))
    result=restored.budget_effect(grant.identity,grant.hash,"returned",{"operation_id":first["operation_id"]})
    assert set(result["unknown_measurements"])=={"work_ms","tokens","cost_microusd"}
    state=restored.budget_authority.snapshot(allocation.allocation_id)
    assert state["implementation_attempts"]==1 and state["inflight"]==0
    assert state["charged_upper_bounds"]["tokens"]==5000
    assert restored.budget_effect(grant.identity,grant.hash,"returned",
        {"operation_id":first["operation_id"]})==result

def test_actual_failed_check_opens_only_approved_small_repair_and_stops_blind_repeat(tmp_path):
    factory,root,plan,grant,cycle,raw,allocation,quote=approved_factory(tmp_path,repair=True)
    first=factory.verify_request(grant.identity,grant.hash,"failure-one")
    assert first["status"]=="failed" and first["next_action"]=="approved_bounded_repair"
    assert first["implementation_attempt"]==2 and cycle.phase is WorkPhase.WORK
    second=factory.verify_request(grant.identity,grant.hash,"failure-without-new-code")
    assert second["status"]=="failed" and second["next_action"]=="work_stopped"
    assert cycle.phase is WorkPhase.VERIFY
    assert factory.budget_authority.snapshot(allocation.allocation_id)["implementation_attempts"]==2
    with pytest.raises(PolicyDenied):factory.authorize_invocation(grant.identity,grant.hash,kind="provider")

def test_real_deadline_retains_unknown_operation_and_restores_process_timer():
    previous=signal.getsignal(signal.SIGALRM)
    with pytest.raises(PolicyDenied,match="reconcile_original"):
        with model_deadline(30):time.sleep(1)
    assert signal.getsignal(signal.SIGALRM)==previous and signal.getitimer(signal.ITIMER_REAL)==(0,0)

def test_text_quote_rejects_multimodal_multiple_outputs_and_route_poisoning():
    agent=SimpleNamespace(api_mode="chat_completions",model="quoted-text-model")
    request={"model":agent.model,"messages":[{"role":"user","content":"bounded text"}],"max_tokens":50}
    validate_text_request(request,agent)
    for invalid in ({**request,"n":2},{**request,"stream":True},{**request,"model":"expensive-other"},
                    {**request,"messages":[{"role":"user","content":[{"type":"image_url","image_url":"private"}]}]},
                    {**request,"max_completion_tokens":50}):
        with pytest.raises(WorkContractError):validate_text_request(invalid,agent)

def test_protected_host_catalogue_binds_budget_before_baseline_and_cold_recovery(tmp_path,monkeypatch):
    from tests.herdr.test_work_configuration import configured
    from herdr import work_configuration as config
    from agent_completion_evidence import spec_digest
    allocation=BudgetAllocation(digest("catalogue-allocation"),"github:org/repo",digest("catalogue-work"),
        digest("catalogue-lineage"),digest("catalogue-approval"),
        BudgetLimits(1000000,1000000,5,100000,0,2,0,1,1,consumer_policy_version="work-budget-2"))
    budget={"version":1,"allocation":asdict(allocation),"ancestors":[],"model_quotes":[]}
    raw,task,factory,cycle,grant,root=configured(tmp_path,monkeypatch,budget=budget)
    assert task["work_budget_version"]==1 and cycle.plan.budget_reference==allocation.hash
    before=factory.budget_authority.snapshot(allocation.allocation_id)
    assert before["implementation_attempts"]==1 and before["charged_upper_bounds"]["work_ms"]>0
    original=factory.budget_authority.audit_log._path.read_bytes()
    recovered=config.build_root_work_factory(Path(raw["task_store_root"]),task,recovery=True,git=factory.git)
    recovered.recover(identity=grant.identity,workspace=root,spec_sha256=spec_digest(task),
        grant_sha256=grant.hash,plan_sha256=cycle.plan.hash)
    assert recovered.budget_authority.snapshot(allocation.allocation_id)==before
    assert recovered.budget_authority.audit_log._path.read_bytes()==original

@pytest.mark.parametrize("version",[True,0,2,"1"])
def test_unknown_budget_marker_cannot_use_historical_admission(tmp_path,monkeypatch,version):
    from tests.herdr.test_work_configuration import configured
    from herdr import work_configuration as config
    raw,task,factory,cycle,grant,root=configured(tmp_path,monkeypatch)
    task["work_budget_version"]=version
    with pytest.raises(WorkContractError,match="version unsupported"):
        config.build_root_work_factory(Path(raw["task_store_root"]),task)

def test_sdk_guard_blocks_short_lived_grant_before_model_callback(tmp_path):
    from datetime import UTC,datetime,timedelta
    from tests.herdr.test_security import grant
    from herdr.work_contract_host import WorkInvocationGuard
    current=grant(tmp_path)
    current=replace(current,expires_at=(datetime.now(UTC)+timedelta(seconds=2)).isoformat())
    messages=[]
    class QuoteTransportFixture:
        def __call__(self,*args,**kwargs):return True
        def effect(self,identity,grant_hash,action,payload):
            assert identity==current.identity and grant_hash==current.hash
            messages.append(action)
            if action=="status":return {"required":True}
            return {"operation_id":"a"*64,"quote_sha256":"b"*64,"max_work_ms":60000}
    guard=WorkInvocationGuard(current,work_authority=QuoteTransportFixture())
    with pytest.raises(PolicyDenied,match="model_grant_lifetime_insufficient"):guard.start_model_effect({})
    assert messages==["status","start"]  # Reservation stays held; no paid callback is authorized.


def test_protected_check_reservation_includes_host_work_time_and_holds_unknown(tmp_path):
    factory,root,plan,item,cycle,raw,allocation,quote=approved_factory(tmp_path)
    state=factory.budget_authority.snapshot(allocation.allocation_id)
    assert state["charged_upper_bounds"]["work_ms"]>120000
    assert "work_ms" in state["unknown_measurements"]


@pytest.mark.parametrize("fault",["orphan","skipped","reversed"])
def test_declared_ancestor_chain_rejected_before_creating_ledger(tmp_path,fault):
    factory,root,plan,item,cycle,raw,selected,quote=approved_factory(tmp_path)
    parent=replace(selected,allocation_id=digest("parent-id"),work_key=digest("parent-work"))
    middle=replace(selected,allocation_id=digest("middle-id"),work_key=digest("middle-work"),
                   parent_allocation_id=parent.allocation_id)
    child=replace(selected,parent_allocation_id=middle.allocation_id)
    ancestors=[parent,middle]
    if fault=="orphan":child=replace(child,parent_allocation_id=None)
    elif fault=="skipped":child=replace(child,parent_allocation_id=parent.allocation_id)
    else:ancestors=[middle,parent]
    target=tmp_path/"unadmitted";target.mkdir(mode=0o700)
    invalid={**raw,"allocation":asdict(child),"ancestors":[asdict(a) for a in ancestors]}
    with pytest.raises(WorkContractError,match="exact parent chain"):
        bind_budget(SimpleNamespace(),invalid,storage=target,writable_roots=(root,))
    assert list(target.iterdir())==[]

def test_exact_ancestor_chain_charges_the_declared_parent_ceiling(tmp_path):
    from herdr.work_budget import Demand
    factory,root,plan,item,cycle,raw,selected,quote=approved_factory(tmp_path)
    parent=replace(selected,allocation_id=digest("parent-id"),work_key=digest("parent-work"),
                   limits=replace(selected.limits,max_cost_microusd=5))
    child=replace(selected,parent_allocation_id=parent.allocation_id)
    target=tmp_path/"valid-chain";target.mkdir(mode=0o700)
    bound=SimpleNamespace()
    bind_budget(bound,{**raw,"allocation":asdict(child),"ancestors":[asdict(parent)]},
                storage=target,writable_roots=(root,))
    with pytest.raises(BudgetBlocked):
        bound.budget_authority.reserve(allocation_id=child.allocation_id,semantic_key=digest("parent-capped"),
            identity=item.identity,plan_sha256=plan.hash,provider="provider-a",demand=Demand(1,1,1,6))
    assert bound.budget_authority.snapshot(parent.allocation_id)["inflight"]==0


def test_caught_sdk_alarm_cannot_settle_overlong_original_operation(tmp_path):
    factory,root,plan,grant,cycle,raw,allocation,quote=approved_factory(tmp_path)
    original=factory.budget_effect(grant.identity,grant.hash,"start",model_request(quote))
    caught=[]
    with pytest.raises(PolicyDenied,match="reconcile_original"):
        with model_deadline(20):
            until=time.monotonic()+0.09
            while time.monotonic()<until:
                try:time.sleep(0.01)
                except OSError as exc:caught.append(exc)
    assert len(caught)>=2 and signal.getitimer(signal.ITIMER_REAL)==(0,0)
    assert factory.budget_authority.reconcile(original["operation_id"])["usage"] is None
    assert factory.budget_authority.snapshot(allocation.allocation_id)["inflight"]==1


def test_fresh_admission_rejects_changed_persisted_ancestor_limits(tmp_path):
    factory,root,plan,grant,cycle,raw,allocation,quote=approved_factory(tmp_path)
    parent=replace(allocation,allocation_id=digest("existing-parent"),work_key=digest("parent-work"),
                   limits=replace(allocation.limits,max_model_calls=10))
    child=replace(allocation,parent_allocation_id=parent.allocation_id)
    declared={**raw,"allocation":asdict(child),"ancestors":[asdict(parent)]}
    storage=tmp_path/"original-ancestor-ledger"
    storage.mkdir(mode=0o700)
    bind_budget(factory,declared,storage=storage,writable_roots=(root,))
    log=factory.budget_authority.audit_log
    before=log._path.read_bytes()
    tighter=replace(parent,limits=replace(parent.limits,max_model_calls=4))
    with pytest.raises((BudgetBlocked,WorkContractError),match="differs from original"):
        bind_budget(factory,{**declared,"ancestors":[asdict(tighter)]},storage=storage,writable_roots=(root,))
    assert log._path.read_bytes()==before
