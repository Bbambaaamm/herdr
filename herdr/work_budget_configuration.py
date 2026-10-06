"""Protected budget admission and pre-effect SDK reservations for one lineage."""
from dataclasses import asdict
from pathlib import Path
import re
import time
from .evidence import digest
from .work_planning import bounded, closed
from .work_cycle import require, WorkPhase
from .work_budget import BudgetAllocation, BudgetLimits, Demand, Usage, WorkBudgetAuthority, BudgetBlocked

def parse_allocation(raw):
    closed(raw, ("allocation_id","consumer","work_key","lineage_key","authorization_reference","limits",
                 "parent_allocation_id","series_plan_sha256"), "approved work allocation")
    require(isinstance(raw["limits"],dict),"approved finite limits required")
    return BudgetAllocation(**{**raw,"limits":BudgetLimits(**raw["limits"])})

def bind_budget(factory, raw, *, storage, writable_roots=(), recovery=False):
    bounded(raw)
    closed(raw, {"version","allocation","ancestors","model_quotes"} | ({"repair"} if "repair" in raw else set()), "approved cumulative budget")
    require(type(raw["version"]) is int and raw["version"]==1,"budget policy version unsupported")
    selected=parse_allocation(raw["allocation"])
    require(isinstance(raw["ancestors"],list) and len(raw["ancestors"])<=32,
            "bounded budget ancestry required")
    ancestors=[parse_allocation(row) for row in raw["ancestors"]]
    rows={row.allocation_id:row for row in (*ancestors,selected)}
    require(len(rows)==len(ancestors)+1 and all(row.consumer==selected.consumer
            and row.lineage_key==selected.lineage_key for row in rows.values()),
            "budget lineage is conflicting")
    chain=(*ancestors,selected)
    require(len({row.work_key for row in chain})==len(chain),"budget ancestry work key is ambiguous")
    for index,row in enumerate(chain):
        expected=None if index==0 else chain[index-1].allocation_id
        require(row.parent_allocation_id==expected,"declared budget ancestry is not the exact parent chain")
    # The immutable host work key, rather than a task/session/name, locates the ledger.
    from .work_configuration import _private_directory, _audit
    directory=Path(storage)/"work-budget"/selected.lineage_key
    for writable in writable_roots:
        require(not directory.is_relative_to(Path(writable).resolve()),"budget authority is worker writable")
    _private_directory(directory,base=Path(storage))
    def authorize(**kwargs):
        found=next((row for row in rows.values() if row.work_key==kwargs["work_key"]),None)
        require(found is not None,"budget allocation is not host approved")
        return found
    require(not recovery or (directory/"events.jsonl").is_file(),"original cumulative budget unavailable")
    authority=WorkBudgetAuthority(audit_log=_audit(directory/"events.jsonl"),authorize=authorize)
    for row in (*ancestors,selected):
        if recovery:
            require(authority.find_allocation(row.hash)==row,"original cumulative allocation changed")
            continue
        persisted=authority.open(consumer=row.consumer,work_key=row.work_key,lineage_key=row.lineage_key,
                       authorization_reference=row.authorization_reference)
        require(persisted==row,"declared cumulative allocation differs from original")
    require(isinstance(raw["model_quotes"],list) and len(raw["model_quotes"])<=16,"bounded model quotes required")
    quotes={}
    for quote in raw["model_quotes"]:
        closed(quote,("provider","model","api_mode","base_url","max_request_bytes","max_output_tokens",
                     "max_tokens","max_cost_microusd","max_work_ms"),"host model quote")
        for key in ("provider","model","api_mode","base_url"):
            require(isinstance(quote[key],str) and 1<=len(quote[key])<=1024,"exact quoted route required")
        for key in ("max_request_bytes","max_output_tokens","max_tokens","max_work_ms"):
            require(type(quote[key]) is int and 1<=quote[key]<=1000000,"finite model ceiling required")
        require(type(quote["max_cost_microusd"]) is int and 0<=quote["max_cost_microusd"]<=10**12,
                "unknown price cannot be zero")
        require(quote["api_mode"]=="chat_completions" and quote["max_work_ms"]<=900000
                and quote["max_tokens"]>=quote["max_request_bytes"]+quote["max_output_tokens"],
                "unsupported or insufficient text-route ceiling")
        key=(quote["provider"],quote["model"],quote["api_mode"],quote["base_url"])
        require(key not in quotes,"duplicate model price quote")
        quotes[key]=dict(quote)
    factory.budget_authority=authority
    factory.budget_binding=lambda **kwargs:selected
    factory.budget_quotes=quotes
    factory.budget_definition=raw
    from .work_failure_control import bind_repair
    bind_repair(factory,raw.get("repair"))
    return selected

def model_effect(factory,identity,grant_sha256,action,payload):
    """Exact observed SDK response releases concurrency; missing usage stays held."""
    bounded(payload)
    with factory._lock:
        cycle,_=factory._refresh(identity)
        require(cycle.plan.grant_sha256==grant_sha256,"model budget grant changed")
        allocation=factory.allocations.get(digest(identity.to_json()))
        require(allocation is not None,"model work budget unavailable")
        authority=factory.budget_authority
        if action=="start":
            require(cycle.phase is WorkPhase.WORK,"model implementation has ended")
            closed(payload,("request_id","provider","model","api_mode","base_url","request_sha256",
                            "request_bytes","output_tokens"),"physical SDK budget request")
            require(isinstance(payload["request_id"],str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}",payload["request_id"]),
                    "stable SDK request identity required")
            quote=factory.budget_quotes.get(tuple(payload[key] for key in ("provider","model","api_mode","base_url")))
            require(quote is not None,"trusted finite price quote unavailable")
            require(isinstance(payload["request_sha256"],str) and re.fullmatch(r"[0-9a-f]{64}",payload["request_sha256"])
                    and type(payload["request_bytes"]) is int and 0<payload["request_bytes"]<=quote["max_request_bytes"]
                    and type(payload["output_tokens"]) is int and 0<payload["output_tokens"]<=quote["max_output_tokens"],
                    "model request exceeds approved quote")
            # Do not rename an uncertain delivery into another economic execution.
            with authority._serialized():
                state=authority._state()
                require(not any(row["usage"] is None and row["started"]
                    and allocation.allocation_id in authority._ancestors(state,row["allocation_id"])
                    for row in state["operations"].values()),"uncertain model effect requires original reconciliation")
            semantic=digest({"sdk_request":payload["request_id"],"identity":identity.to_json(),
                             "plan":cycle.plan.hash,"request":payload["request_sha256"]})
            operation=authority.reserve(allocation_id=allocation.allocation_id,semantic_key=semantic,
                identity=identity,plan_sha256=cycle.plan.hash,provider=payload["provider"],
                demand=Demand(quote["max_work_ms"],1,quote["max_tokens"],quote["max_cost_microusd"]))
            require(authority.claim_start(operation),"model effect already started; reconcile original")
            return {"operation_id":operation,"quote_sha256":digest(quote),"max_work_ms":quote["max_work_ms"]}
        closed(payload,("operation_id",),"original SDK effect completion")
        require(action=="returned","unknown delivery cannot release its reservation")
        record=authority.reconcile(payload["operation_id"])
        require(record["started"] and record["identity"]==identity.to_json()
                and record["plan_sha256"]==cycle.plan.hash,"returned effect binding changed")
        if record["usage"] is not None:
            return {"settled":True,"unknown_measurements":["work_ms","tokens","cost_microusd"]}
        # SDK transport return is observable; provider billing/token usage is not
        # a trusted host measurement. Retain those reserved ceilings explicitly.
        proof=digest({"original_operation":payload["operation_id"],"observed":"physical-sdk-transport-return"})
        authority.settle(payload["operation_id"],Usage(None,1,None,None,proof))
        return {"settled":True,"unknown_measurements":["work_ms","tokens","cost_microusd"]}
