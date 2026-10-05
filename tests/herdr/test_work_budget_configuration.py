"""Actual host admission/effect ports and finite SDK deadline, without provider calls."""
from dataclasses import asdict,replace
from types import SimpleNamespace
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
                            "paths":["result.py"],"max_changed_lines":20}
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
