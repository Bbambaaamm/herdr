"""Pre-effect re-admission consumes another bounded attempt in the original ledger."""
from copy import deepcopy
from dataclasses import replace
import pytest

from herdr.evidence import digest
from herdr.scheduler import AuditLog
from herdr.work_budget import BudgetBlocked, Demand, Usage, WorkBudgetAuthority
from herdr.work_cycle import WorkContractError, WorkPhase
from herdr.work_budget_configuration import bind_budget
from herdr.work_pre_effect_readmission import definition_digest
from tests.herdr.test_work_budget import authority, allocation, begin, h, identity, reserve
from tests.herdr.test_work_budget_configuration import approved_factory, model_request

def decision(previous, **kwargs):
    return {"previous_attempt_sha256": previous["event_sha256"],
            "approval_sha256": h("immutable host approval")}

def next_identity():
    return identity(agent_id="replacement-worker", run_token="replacement-run", fencing_token=2)

def test_pre_effect_readmission_retains_allocation_history_and_unknown_holds(tmp_path):
    auth, alloc, log = authority(tmp_path)
    first = begin(auth, alloc)
    overhead = reserve(auth, alloc, "overhead", demand=Demand(100, 0, 0, 0), operation_kind="host-overhead")
    auth.claim_start(overhead)
    auth.settle(overhead, Usage(None, 0, 0, 0, h("unknown overhead")))
    original = log._path.read_bytes()
    second = begin(auth, alloc, identity=next_identity(), plan_sha256=h("new admitted plan"),
                   pre_effect_approval=decision)
    assert first.attempt == 1 and second.attempt == 2
    assert log._path.read_bytes().startswith(original)
    state = auth.snapshot(alloc.allocation_id)
    assert state["implementation_attempts"] == 2
    assert state["charged_upper_bounds"]["work_ms"] == 100
    assert state["unknown_measurements"] == ["work_ms"]
    restored = WorkBudgetAuthority(audit_log=AuditLog(log._path),
                                  authorize=lambda **kw: pytest.fail("no new allowance"),
                                  clock_ms=lambda: 1001)
    before = log._path.read_bytes()
    assert begin(restored, alloc, identity=next_identity(), plan_sha256=h("new admitted plan"),
                 pre_effect_approval=decision) == second
    assert log._path.read_bytes() == before
    assert restored.find_allocation(alloc.hash) == alloc
    assert restored.snapshot(alloc.allocation_id)["implementation_attempts"] == 2

def test_new_native_identity_without_host_approval_remains_blocked(tmp_path):
    auth, alloc, log = authority(tmp_path)
    begin(auth, alloc)
    with pytest.raises(BudgetBlocked, match="approved work plan"):
        begin(auth, alloc, identity=next_identity(), plan_sha256=h("new plan"))
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"] == 1

@pytest.mark.parametrize("phase", ["reserved", "started", "returned"])
def test_model_reservation_even_if_returned_forbids_pre_effect_readmission(tmp_path, phase):
    auth, alloc, log = authority(tmp_path)
    begin(auth, alloc)
    operation = reserve(auth, alloc)
    if phase != "reserved":
        auth.claim_start(operation)
    if phase == "returned":
        auth.settle(operation, Usage(None, 1, None, None, h("transport returned")))
    with pytest.raises(BudgetBlocked, match="model reservation"):
        begin(auth, alloc, identity=next_identity(), plan_sha256=h("new plan"),
              pre_effect_approval=decision)
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"] == 1
    assert auth.reconcile(operation)["operation_id"] == operation

@pytest.mark.parametrize("changes", [
    {"task_id": "alias"}, {"consumer": "github:other/repo"},
    {"fencing_token": 3}, {"run_token": "run"}, {"parent_task_id": "other-parent"}])
def test_readmission_cannot_rename_the_work_or_skip_native_fencing(tmp_path, changes):
    auth, alloc, log = authority(tmp_path)
    begin(auth, alloc)
    with pytest.raises(BudgetBlocked):
        begin(auth, alloc, identity=replace(next_identity(), **changes), plan_sha256=h("new plan"),
              pre_effect_approval=decision)
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"] == 1

def test_repeated_readmission_cannot_refill_implementation_limit(tmp_path):
    auth, alloc, log = authority(tmp_path, allocation(max_implementation_attempts=2, attempt_override_reference=h("explicit lower limit")))
    begin(auth, alloc)
    begin(auth, alloc, identity=next_identity(), plan_sha256=h("new plan"), pre_effect_approval=decision)
    with pytest.raises(BudgetBlocked, match="implementation_attempts_exhausted"):
        begin(auth, alloc, identity=replace(next_identity(), run_token="third", fencing_token=3),
              plan_sha256=h("third plan"), pre_effect_approval=decision)
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"] == 2

def configured_readmission(factory, raw, alloc, plan, grant):
    previous = [e for e in factory.budget_authority.audit_log.replay()
                if e["event"] == "work_budget_attempt"][-1]
    current = replace(grant.identity, run_token="next-run", fencing_token=grant.identity.fencing_token + 1,
                      agent_id="next-worker")
    next_grant = replace(grant, identity=current)
    next_plan = replace(plan, identity=current, grant_sha256=next_grant.hash)
    definition = {"base_sha": next_plan.base_sha, "budget": raw, "scope": "same approved fixture"}
    rule = {"version": 1, "source_attempt_sha256": previous["event_sha256"],
            "source_identity": previous["identity"], "source_plan_sha256": previous["plan_sha256"],
            "source_failed_task_sha256": digest("exact closed pre-effect task"),
            "authority_reference": digest("operator approved activation"),
            "spec_sha256": next_plan.spec_sha256, "base_sha": next_plan.base_sha,
            "definition_sha256": definition_digest(definition),
            "next_fencing_token": current.fencing_token}
    raw["pre_effect_readmission"] = rule
    factory.host_admission = {"spec_sha256": plan.spec_sha256, "definition": definition}
    factory.approve = lambda **kwargs: next_plan
    return next_plan, next_grant, rule

def test_real_host_prepare_and_sdk_budget_port_after_bounded_readmission(tmp_path):
    factory, root, plan, grant, cycle, raw, alloc, quote = approved_factory(tmp_path)
    original = factory.budget_authority.audit_log._path.read_bytes()
    next_plan, next_grant, rule = configured_readmission(factory, raw, alloc, plan, grant)
    bind_budget(factory, raw, storage=tmp_path/"private", writable_roots=(root,))
    next_cycle = factory.prepare(identity=next_grant.identity, workspace=root, grant=next_grant,
                                 spec_sha256=next_plan.spec_sha256)
    assert next_cycle.phase is WorkPhase.WORK
    state = factory.budget_authority.snapshot(alloc.allocation_id)
    assert state["implementation_attempts"] == 2
    assert factory.budget_authority.audit_log._path.read_bytes().startswith(original)
    effect = factory.budget_effect(next_grant.identity, next_grant.hash, "start", model_request(quote))
    assert factory.budget_authority.reconcile(effect["operation_id"])["identity"] == next_grant.identity.to_json()
    state = factory.budget_authority.snapshot(alloc.allocation_id)
    assert state["charged_upper_bounds"]["model_calls"] == 1
    assert state["charged_upper_bounds"]["cost_microusd"] == quote["max_cost_microusd"]
    from herdr.work_contract_host import HostWorkContractFactory
    recovered = HostWorkContractFactory(approve=lambda **kw: pytest.fail("recovery cannot replan"),
        environment=factory.environment, storage=factory.storage, audit_log=factory.audit_log, git=factory.git)
    recovered.host_admission = factory.host_admission
    bind_budget(recovered, raw, storage=tmp_path/"private", writable_roots=(root,), recovery=True)
    recovered.recover(identity=next_grant.identity, workspace=root, spec_sha256=next_plan.spec_sha256,
                      grant_sha256=next_grant.hash, plan_sha256=next_plan.hash)
    with pytest.raises((BudgetBlocked, WorkContractError), match="uncertain"):
        recovered.budget_effect(next_grant.identity, next_grant.hash, "start", model_request(quote, "another"))
    assert recovered.budget_authority.snapshot(alloc.allocation_id)["implementation_attempts"] == 2

@pytest.mark.parametrize("fault", ["source", "definition", "spec", "base", "fence"])
def test_host_rule_is_bound_to_original_history_and_exact_new_contract(tmp_path, fault):
    factory, root, plan, grant, cycle, raw, alloc, quote = approved_factory(tmp_path)
    next_plan, next_grant, rule = configured_readmission(factory, raw, alloc, plan, grant)
    if fault == "source": rule["source_attempt_sha256"] = digest("foreign prior attempt")
    elif fault == "definition": rule["definition_sha256"] = digest("other definition")
    elif fault == "spec": rule["spec_sha256"] = digest("other spec")
    elif fault == "base": rule["base_sha"] = "f" * 40
    else: rule["next_fencing_token"] += 1
    with pytest.raises((BudgetBlocked, WorkContractError)):
        bind_budget(factory, raw, storage=tmp_path/"private", writable_roots=(root,))
        factory.prepare(identity=next_grant.identity, workspace=root, grant=next_grant,
                        spec_sha256=next_plan.spec_sha256)
    assert factory.budget_authority.snapshot(alloc.allocation_id)["implementation_attempts"] == 1
    assert not any(e.get("operation_kind") == "model" for e in factory.budget_authority.audit_log.replay())

def test_unsettled_host_operation_forbids_readmission(tmp_path):
    auth, alloc, log = authority(tmp_path)
    begin(auth, alloc)
    overhead = reserve(auth, alloc, "inflight-host", demand=Demand(100, 0, 0, 0),
                       operation_kind="host-overhead")
    with pytest.raises(BudgetBlocked, match="inflight operation"):
        begin(auth, alloc, identity=next_identity(), plan_sha256=h("new plan"),
              pre_effect_approval=decision)
    assert auth.reconcile(overhead)["operation_id"] == overhead
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"] == 1

def test_host_approval_cannot_change_on_idempotent_replay(tmp_path):
    auth, alloc, log = authority(tmp_path)
    begin(auth, alloc)
    kwargs = dict(identity=next_identity(), plan_sha256=h("new plan"))
    begin(auth, alloc, **kwargs, pre_effect_approval=decision)
    original = log._path.read_bytes()
    changed = lambda previous, **kw: {"previous_attempt_sha256": previous["event_sha256"],
                                      "approval_sha256": h("different approval")}
    with pytest.raises(BudgetBlocked, match="evidence changed"):
        begin(auth, alloc, **kwargs, pre_effect_approval=changed)
    assert log._path.read_bytes() == original

def test_implementation_repair_after_readmission_uses_latest_plan_and_remaining_attempt(tmp_path):
    from tests.herdr.test_work_budget import failure
    auth, alloc, log = authority(tmp_path)
    begin(auth, alloc)
    next_plan = h("new plan")
    begin(auth, alloc, identity=next_identity(), plan_sha256=next_plan,
          pre_effect_approval=decision)
    observed = failure()
    auth.record_failure(alloc.allocation_id, observed)
    repaired = begin(auth, alloc, identity=next_identity(), plan_sha256=next_plan,
                     reason_code="fix_checker", failure_check_sha256=observed.check_sha256,
                     diff_sha256=h("bounded repair"), changed_files=1, changed_lines=3)
    assert repaired.attempt == 3
    assert auth.snapshot(alloc.allocation_id)["implementation_attempts"] == 3

def test_one_host_rule_cannot_authorize_a_third_native_invocation(tmp_path):
    factory, root, plan, grant, cycle, raw, alloc, quote = approved_factory(tmp_path)
    next_plan, next_grant, rule = configured_readmission(factory, raw, alloc, plan, grant)
    bind_budget(factory, raw, storage=tmp_path/"private", writable_roots=(root,))
    factory.prepare(identity=next_grant.identity, workspace=root, grant=next_grant,
                    spec_sha256=next_plan.spec_sha256)
    third_identity = replace(next_grant.identity, run_token="third-native-run", fencing_token=3)
    third_grant = replace(next_grant, identity=third_identity)
    third_plan = replace(next_plan, identity=third_identity, grant_sha256=third_grant.hash)
    factory.approve = lambda **kwargs: third_plan
    with pytest.raises(WorkContractError, match="another attempt"):
        factory.prepare(identity=third_identity, workspace=root, grant=third_grant,
                        spec_sha256=third_plan.spec_sha256)
    assert factory.budget_authority.snapshot(alloc.allocation_id)["implementation_attempts"] == 2
