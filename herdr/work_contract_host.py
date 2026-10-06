"""Host composition ports for the existing worker/runtime; never model config."""
from pathlib import Path
import threading
import re
import contextvars
from contextlib import contextmanager

from .evidence import digest
from .security import InvocationGuard, InvocationIdentity, PolicyDenied, SecurityGrant
from .scheduler import AuditLog
from .work_cycle import WorkCycle, WorkPhase, WorkPlan, require
from .check_runner import CheckEnvironment, HostCheckRunner

class HostWorkContractFactory:
    def __init__(self, *, approve, environment, storage, audit_log, git=None, budget_authority=None, budget_binding=None):
        require(callable(approve) and isinstance(environment,CheckEnvironment)
                and isinstance(audit_log,AuditLog),"host work authority required")
        self.approve,self.environment,self.storage,self.audit_log=approve,environment,Path(storage),audit_log
        self.git=git
        self.budget_authority,self.budget_binding=budget_authority,budget_binding
        self.allocations={}
        self.cycles={}
        self.handoffs={}
        self._lock=threading.RLock()

    def _refresh(self,identity):
        found=self.cycles.get(digest(identity.to_json()))
        require(found is not None,"work contract unavailable")
        cycle,runner=found
        restored=WorkCycle(cycle.plan,cycle.root,self.audit_log,git=self.git,budget_authority=self.budget_authority)
        # Retain references already held by the worker while refreshing durable
        # state written by another host entry point.
        cycle.__dict__.update(restored.__dict__)
        allocation=self.allocations.get(digest(identity.to_json()))
        if self.budget_authority is not None and allocation is not None:
            from .work_budget import reconcile_known_hygiene
            reconcile_known_hygiene(self.budget_authority,allocation,cycle)
        return cycle,runner

    def prepare(self, *, identity, workspace, grant, spec_sha256):
        with self._lock:
            require(isinstance(identity,InvocationIdentity) and isinstance(grant,SecurityGrant)
                    and grant.identity==identity,"work authority identity mismatch")
            require(grant.is_active(),"work authority expired")
            root=Path(workspace).resolve(strict=True)
            require(root==Path(grant.workspace_root).resolve(strict=True),"exact granted worktree required")
            log_path=self.audit_log._path.resolve()
            for path in grant.runtime_assurance.writable_roots:
                require(not log_path.is_relative_to(Path(path).resolve()),"work audit is worker writable")
            from .work_cycle import IntentInfoRequired
            try:
                plan=self.approve(identity=identity,workspace=root,grant=grant,spec_sha256=spec_sha256)
            except IntentInfoRequired:
                self.audit_log.append({"event":"task_work_info_required", "identity":identity.to_json(),
                    "spec_sha256":spec_sha256, "code":"info_required", "next_action":"resolve_material_intent"})
                raise
            require(isinstance(plan,WorkPlan) and plan.identity==identity and plan.grant_sha256==grant.hash
                    and plan.spec_sha256==spec_sha256 and plan.environment_sha256==self.environment.hash,
                    "approved work contract binding mismatch")
            if plan.planning is not None:
                plan.planning.require_binding(plan, grant)
            from .work_lifetime import check_wall_seconds, require_grant_lifetime
            request=check_wall_seconds(plan,getattr(self,"local_commit_policy",None))
            require(request<=900,"complete host request exceeds bound")
            require_grant_lifetime(grant,check_wall_seconds(plan)+900)
            runner=HostCheckRunner(self.environment,self.storage,git=self.git)
            from .work_lifetime import bounded_host_request
            cycle=WorkCycle(plan,root,self.audit_log,git=self.git,budget_authority=self.budget_authority)
            allocation=None
            if self.budget_authority is not None:
                from .work_budget import BudgetAllocation,BudgetedCheckRunner
                for quote in getattr(self,"budget_quotes",{}).values():
                    require(quote["provider"] in grant.scope.providers
                            and quote["max_tokens"]<=grant.scope.max_context_tokens
                            and quote["max_cost_microusd"]<=grant.scope.max_cost_microusd,
                            "model quote exceeds the consumer grant")
                require(callable(self.budget_binding), 'host budget binding required')
                approved=self.budget_binding(identity=identity,workspace=root,grant=grant,spec_sha256=spec_sha256)
                require(isinstance(approved,BudgetAllocation) and approved.consumer==identity.consumer, 'exact approved budget required')
                allocation=self.budget_authority.open(consumer=approved.consumer,work_key=approved.work_key,
                    lineage_key=approved.lineage_key,authorization_reference=approved.authorization_reference)
                require(allocation==approved and plan.budget_reference==allocation.hash, 'work budget binding mismatch')
                from .work_budget import reserve_host_phase_overhead
                reserve_host_phase_overhead(self.budget_authority,allocation,plan,"baseline")
                with bounded_host_request(check_wall_seconds(plan)):
                    cycle.start(BudgetedCheckRunner(self.budget_authority,allocation,runner,'baseline',
                        host_overhead_seconds=120,phase_key="baseline"))
                if cycle.phase is WorkPhase.WORK:
                    self.budget_authority.begin_implementation(allocation_id=allocation.allocation_id,identity=identity,plan_sha256=plan.hash)
                self.allocations[digest(identity.to_json())]=allocation
                runner=BudgetedCheckRunner(self.budget_authority,allocation,runner,'verification',host_overhead_seconds=120)
            else:
                with bounded_host_request(check_wall_seconds(plan)):
                    cycle.start(runner)
            self.cycles[digest(identity.to_json())]=(cycle,runner)
            return cycle

    def recover(self,*,identity,workspace,spec_sha256,grant_sha256,plan_sha256):
        with self._lock:
            records=[event for event in self.audit_log.replay() if
                     event.get("work_cycle")==identity.to_json() and event.get("event")=="work_plan"]
            require(records,"persisted host work contract missing")
            plan=WorkPlan.from_json(records[0]["plan"])
            require(plan.identity==identity and plan.hash==plan_sha256 and plan.spec_sha256==spec_sha256
                    and plan.grant_sha256==grant_sha256 and plan.environment_sha256==self.environment.hash,
                    "recovered work authority mismatch")
            cycle=WorkCycle(plan,Path(workspace),self.audit_log,git=self.git,budget_authority=self.budget_authority)
            runner=None if cycle.phase in {WorkPhase.HANDOFF,WorkPhase.FINISHED} else HostCheckRunner(
                self.environment,self.storage,git=self.git)
            if self.budget_authority is not None:
                from .work_budget import BudgetedCheckRunner
                allocation=self.budget_authority.find_allocation(plan.budget_reference)
                self.allocations[digest(identity.to_json())]=allocation
                from .work_budget import reconcile_known_hygiene
                reconcile_known_hygiene(self.budget_authority,allocation,cycle)
                if runner is not None: runner=BudgetedCheckRunner(self.budget_authority,allocation,runner,'verification',host_overhead_seconds=120)
            self.cycles[digest(identity.to_json())]=(cycle,runner)
            return cycle

    def before_completion(self,identity,result):
        from .evidence import parse_artifact
        from .result_candidate import completion_candidate
        with self._lock:
            cycle,runner=self._refresh(identity)
            candidate=completion_candidate(result,workspace=cycle.root)
            require(Path(candidate.get("artifact_workspace","")).is_absolute()
                    and Path(candidate["artifact_workspace"])==cycle.root,
                    "result escaped approved worktree")
            if cycle.phase in {WorkPhase.WORK,WorkPhase.VERIFY}:
                require(runner is not None,"verification runner unavailable")
                cycle.verify(runner)
            cycle.committed(parse_artifact(candidate.get("artifact")))
            return cycle

    def require_model_work(self,identity,grant_sha256,**kwargs):
        with self._lock:
            try:
                cycle,_=self._refresh(identity)
            except Exception as exc:
                raise PolicyDenied("work_phase_unavailable") from exc
            if cycle.plan.grant_sha256!=grant_sha256 or not cycle.implementation_allowed():
                raise PolicyDenied("work_phase_forbids_implementation")

    def authorize_invocation(self, identity, grant_sha256, *, kind, tool=None):
        with self._lock:
            cycle,_=self._refresh(identity)
            require(cycle.plan.grant_sha256==grant_sha256,"work invocation grant changed")
            if cycle.phase is WorkPhase.WORK:
                if kind=="tool" and tool=="herdr_submit_result":
                    raise PolicyDenied("work_result_requires_host_handoff")
                if self.budget_authority is not None:
                    allocation=self.allocations.get(digest(identity.to_json()))
                    require(allocation is not None,'active work budget missing')
                    self.budget_authority.require_active(allocation.allocation_id,identity)
                return True
            if kind=="tool" and tool=="herdr_verify_work" and cycle.phase in {WorkPhase.VERIFY,WorkPhase.HYGIENE,WorkPhase.HANDOFF}:
                return True
            raise PolicyDenied("work_phase_forbids_invocation")

    def verify_request(self, identity, grant_sha256, request_id, handoff=None):
        from .work_lifetime import bounded_host_request, check_wall_seconds
        with self._lock:
            cycle,_=self._refresh(identity)
            seconds=check_wall_seconds(cycle.plan,getattr(self,"local_commit_policy",None))
            with bounded_host_request(seconds):
                return self._verify_request(identity,grant_sha256,request_id,handoff)

    def _verify_request(self, identity, grant_sha256, request_id, handoff=None):
        with self._lock:
            require(isinstance(request_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request_id),
                    "bounded verification request identity required")
            cycle, runner = self._refresh(identity)
            require(cycle.plan.grant_sha256 == grant_sha256, "verification invocation grant changed")
            require(runner is not None or request_id in cycle.verification_requests,
                    "verification runner unavailable")
            if self.budget_authority is not None:
                from .work_budget import reserve_host_phase_overhead
                phase_key="verification:"+request_id
                reserve_host_phase_overhead(self.budget_authority,self.allocations[digest(identity.to_json())],
                    cycle.plan,phase_key,require_existing=cycle.phase in {WorkPhase.HANDOFF,WorkPhase.FINISHED})
                if runner is not None:runner.phase_key=phase_key
            port = self.handoffs.get(digest(identity.to_json()))
            if port is not None:
                port.prepare_request(cycle, request_id, handoff)
            elif handoff is not None:
                raise PolicyDenied("work_handoff_authority_unavailable")
            new_request=request_id not in cycle.verification_requests
            outcome = cycle.request_verification(request_id, runner)
            from .work_failure_control import after_verification
            outcome=after_verification(self,cycle,outcome,new_request=new_request)
            return port.complete(cycle, request_id, outcome) if port is not None else outcome

    def budget_effect(self,identity,grant_sha256,action,payload):
        if action=="status":
            return {"required":self.budget_authority is not None}
        require(self.budget_authority is not None,"host model budget is unavailable")
        from .work_budget_configuration import model_effect
        return model_effect(self,identity,grant_sha256,action,payload)

    def bind_handoff(self, identity, port):
        from .work_handoff import HostWorkHandoff
        require(isinstance(port, HostWorkHandoff) and port.identity == identity, "host handoff binding required")
        self.handoffs[digest(identity.to_json())] = port

    def cycle(self,identity):
        with self._lock:
            return self._refresh(identity)[0]

    def verify(self,identity):
        with self._lock:
            cycle,runner=self._refresh(identity)
            require(runner is not None,"verification runner unavailable")
            cycle.verify(runner)
            return cycle

class WorkInvocationGuard(InvocationGuard):
    """Install in the same physical executor using an authenticated host port."""
    def __init__(self,grant,*,work_authority,**kwargs):
        require(callable(work_authority),"host work phase authority required")
        super().__init__(grant,**kwargs)
        self.work_authority=work_authority
        self._host_result=contextvars.ContextVar("herdr-host-result",default=None)

    def authorize_provider(self,request,**kwargs):
        self.work_authority(self.grant.identity,self.grant.hash,kind="provider",tool=None)
        return super().authorize_provider(request,**kwargs)

    def authorize_tool_call(self,tool,args,**kwargs):
        if self.canonical_tool(tool)=="herdr_submit_result" and self._host_result.get()==digest(args):
            # Only the internal verification handler holds this exact payload context.
            return super().authorize_tool_call(tool,args,**kwargs)
        self.work_authority(self.grant.identity,self.grant.hash,kind="tool",tool=self.canonical_tool(tool))
        return super().authorize_tool_call(tool,args,**kwargs)

    def budget_required(self):
        transport=getattr(self.work_authority,"effect",None)
        if not callable(transport):return False  # Explicit in-process historical/test port.
        answer=transport(self.grant.identity,self.grant.hash,"status",{})
        if set(answer)!={"required"} or type(answer["required"]) is not bool:
            raise PolicyDenied("work_budget_status_invalid")
        return answer["required"]

    def model_request_ceiling(self,payload):
        answer=self.work_authority.effect(self.grant.identity,self.grant.hash,"ceiling",payload)
        if (not isinstance(answer,dict) or set(answer)!={"output_token_field","max_output_tokens"}
                or answer["output_token_field"] not in ("max_tokens","max_completion_tokens")
                or type(answer["max_output_tokens"]) is not int or not 1<=answer["max_output_tokens"]<=4096):
            raise PolicyDenied("model_quote_ceiling_invalid")
        return answer

    def start_model_effect(self,payload):
        if not self.budget_required():return None
        receipt=self.work_authority.effect(self.grant.identity,self.grant.hash,"start",payload)
        from .work_lifetime import require_grant_lifetime
        from .evidence import EvidenceError
        try:
            require(isinstance(receipt,dict) and set(receipt)=={"operation_id","quote_sha256","max_work_ms"}
                    and type(receipt["max_work_ms"]) is int and 1<=receipt["max_work_ms"]<=900000,
                    "bounded model request lease required")
            require_grant_lifetime(self.grant,(receipt["max_work_ms"]+999)//1000)
        except EvidenceError as exc:
            raise PolicyDenied("model_grant_lifetime_insufficient") from exc
        return receipt

    def returned_model_effect(self,receipt):
        if receipt is not None:
            return self.work_authority.effect(self.grant.identity,self.grant.hash,"returned",
                                             {"operation_id":receipt["operation_id"]})

    def deny_unbudgeted_auxiliary(self):
        if self.budget_required():raise PolicyDenied("auxiliary_budget_profile_unsupported")

    def verify_work(self, request_id, handoff=None, *, consume_approval=True):
        args = {"request_id": request_id}
        if handoff is not None: args["handoff"] = handoff
        self.authorize_tool_call("herdr_verify_work", args, consume_approval=consume_approval)
        verifier = getattr(self.work_authority, "verify", None)
        if not callable(verifier):
            raise PolicyDenied("work_verification_unavailable")
        return verifier(self.grant.identity, self.grant.hash, request_id, handoff=handoff) if handoff is not None else verifier(self.grant.identity, self.grant.hash, request_id)

    @contextmanager
    def host_result_submission(self, raw):
        token=self._host_result.set(digest(raw))
        try:yield
        finally:self._host_result.reset(token)
