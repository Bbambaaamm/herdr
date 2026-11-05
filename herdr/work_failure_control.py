"""Host-approved failure disposition on the existing work cycle and ledger."""
from dataclasses import asdict
from .evidence import digest
from .work_cycle import CheckResult, WorkPhase, require
from .work_budget import Failure,FailureKind,BudgetBlocked
from .work_planning import closed

def bind_repair(factory,raw):
    if raw is None:
        factory.repair_policy=None
        return
    closed(raw,("version","reason_code","paths","max_changed_lines","failure_outputs"),"bounded host repair policy")
    require(type(raw["version"]) is int and raw["version"]==1
            and isinstance(raw["reason_code"],str) and 1<=len(raw["reason_code"])<=64
            and isinstance(raw["paths"],list) and 1<=len(raw["paths"])<=8
            and len(set(raw["paths"]))==len(raw["paths"])
            and all(isinstance(path,str) and 1<=len(path)<=1024 for path in raw["paths"])
            and type(raw["max_changed_lines"]) is int and 1<=raw["max_changed_lines"]<=200,
            "finite repair profile required")
    require(isinstance(raw["failure_outputs"],list) and 1<=len(raw["failure_outputs"])<=32
            and all(isinstance(value,str) and len(value)==64 and set(value)<=set("0123456789abcdef")
                    for value in raw["failure_outputs"]),"approved failure classifier required")
    factory.repair_policy=dict(raw)

def after_verification(factory,cycle,outcome,*,new_request):
    if factory.budget_authority is None or outcome["status"]!="failed" or not new_request:
        return outcome
    allocation=factory.allocations[digest(cycle.plan.identity.to_json())]
    failed=[CheckResult(**raw) for raw in cycle.verified_checks.values()
            if raw["exit_code"]!=0 or raw["truncated"]]
    if not failed and cycle.repair_context is not None and outcome["tree_sha256"]==digest(cycle.repair_context["tree"]):
        authority=factory.budget_authority
        with authority._serialized():
            authority._stop_for_allocation(authority._state(),allocation.allocation_id,
                "same_failure_without_changed_code",cycle.plan.identity)
        return {**outcome,"next_action":"work_stopped","stop_reason":"same_failure_without_changed_code"}
    if len(failed)!=1 or failed[0].truncated or failed[0].exit_code!=1:
        return {**outcome,"next_action":"host_typed_failure_disposition_required"}
    check=failed[0]
    policy=getattr(factory,"repair_policy",None)
    if policy is None or check.output_sha256 not in policy["failure_outputs"]:
        return {**outcome,"next_action":"host_typed_failure_disposition_required"}
    failure=Failure(FailureKind.IMPLEMENTATION,"approved_check_failed",
                    check.hash,check.tree_sha256,check.output_sha256)
    factory.budget_authority.record_failure(allocation.allocation_id,failure)
    policy=getattr(factory,"repair_policy",None)
    if policy is None:
        return outcome
    proposal=digest({"failure":check.hash,"approved_repair":policy,"plan":cycle.plan.hash})
    try:
        permit=cycle.reopen_repair(allocation_id=allocation.allocation_id,failure=failure,
            reason_code=policy["reason_code"],diff_sha256=proposal,changed_files=len(policy["paths"]),
            changed_lines=policy["max_changed_lines"],repair_paths=policy["paths"])
    except BudgetBlocked as exc:
        return {**outcome,"next_action":"work_stopped","stop_reason":exc.reason_code}
    return {**outcome,"next_action":"approved_bounded_repair","repair_permit_sha256":permit.event_sha256,
            "implementation_attempt":permit.attempt}
