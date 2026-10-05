"""Cumulative work limits in the existing Herdr AuditLog, never a second queue."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict,dataclass
from enum import StrEnum
import fcntl
import os
from pathlib import Path
import re
import stat
import threading
import time

from .evidence import EvidenceError,canonical,digest
from .scheduler import AuditLog
from .security import InvocationIdentity

_SHA=re.compile(r"^[0-9a-f]{64}$")
_TOKEN=re.compile(r"^[A-Za-z0-9._:/@+-]{1,256}$")
_RESOURCES=("work_ms","model_calls","tokens","cost_microusd")
_COUNTERS=("search_episodes","candidate_executions","candidate_depth","candidate_revisions",
           "statistical_repetitions","tool_fallbacks","plan_revisions","delivery_reconciliations")
_LOCKS={}
_LOCKS_GUARD=threading.Lock()
_ACTIVE_SERIALIZATIONS=threading.local()

def _after_fork():
    global _LOCKS,_LOCKS_GUARD,_ACTIVE_SERIALIZATIONS
    for fd in getattr(_ACTIVE_SERIALIZATIONS,"descriptors",{}).values():
        try: os.close(fd)
        except OSError: pass
    _LOCKS={}
    _LOCKS_GUARD=threading.Lock()
    _ACTIVE_SERIALIZATIONS=threading.local()

os.register_at_fork(after_in_child=_after_fork)

class BudgetBlocked(EvidenceError):
    code="work_budget_blocked"
    def __init__(self,message):
        super().__init__(message)
        self.reason_code=re.sub("[^a-z0-9]+","_",message.lower()).strip("_")[:128]

def require(ok,reason):
    if not ok: raise BudgetBlocked(reason)

def sha(value):
    require(isinstance(value,str) and _SHA.fullmatch(value),"budget reference invalid")
    return value

def token(value):
    require(isinstance(value,str) and _TOKEN.fullmatch(value),"audit-safe budget token required")
    return value

def integer(value,maximum=10**15,minimum=0):
    require(type(value) is int and minimum<=value<=maximum,"finite budget integer required")
    return value

class FailureKind(StrEnum):
    IMPLEMENTATION="implementation"
    BASELINE="baseline"
    FLAKY="flaky"
    PROVIDER="provider"
    TOOL="tool"
    DEPENDENCY="dependency"
    POLICY="policy"
    TRANSPORT="transport"

class StopScope(StrEnum):
    TASK="task"
    EXECUTOR="executor"
    PROVIDER="provider"
    CONSUMER="consumer"

@dataclass(frozen=True)
class BudgetLimits:
    max_work_ms: int
    max_elapsed_ms: int
    max_model_calls: int
    max_tokens: int
    max_cost_microusd: int
    max_concurrency: int
    max_fallbacks: int
    max_variants: int
    max_trials: int
    max_implementation_attempts: int=3
    consumer_policy_version: str="work-budget-1"
    attempt_override_reference: str|None=None
    max_search_episodes: int=0
    max_candidate_executions: int=0
    max_candidate_depth: int=0
    max_candidate_revisions: int=0
    max_statistical_repetitions: int=0
    max_tool_fallbacks: int=1
    max_plan_revisions: int=1
    max_delivery_reconciliations: int=64

    def __post_init__(self):
        for name in ("max_work_ms","max_elapsed_ms","max_model_calls","max_tokens"):
            integer(getattr(self,name),minimum=1)
        integer(self.max_cost_microusd)
        for name in ("max_concurrency","max_variants","max_trials"):
            integer(getattr(self,name),maximum=256,minimum=1)
        integer(self.max_fallbacks,maximum=32)
        integer(self.max_implementation_attempts,maximum=10,minimum=1)
        token(self.consumer_policy_version)
        for key in _COUNTERS:
            integer(getattr(self,"max_"+key),maximum=4096)
        if self.max_implementation_attempts!=3:
            sha(self.attempt_override_reference)

@dataclass(frozen=True)
class BudgetAllocation:
    allocation_id: str
    consumer: str
    work_key: str
    lineage_key: str
    authorization_reference: str
    limits: BudgetLimits
    parent_allocation_id: str|None=None
    series_plan_sha256: str|None=None

    def __post_init__(self):
        for value in (self.allocation_id,self.work_key,self.lineage_key,self.authorization_reference): sha(value)
        token(self.consumer)
        require(isinstance(self.limits,BudgetLimits),"typed approved limits required")
        if self.series_plan_sha256 is not None: sha(self.series_plan_sha256)
        if self.parent_allocation_id is not None:
            sha(self.parent_allocation_id)
            require(self.parent_allocation_id!=self.allocation_id,"cyclic budget lineage")
    @property
    def hash(self):
        raw=asdict(self)
        if self.limits.consumer_policy_version=="work-budget-1":
            for key in _COUNTERS: raw["limits"].pop("max_"+key)
        return digest(raw)

@dataclass(frozen=True)
class Demand:
    work_ms: int
    model_calls: int
    tokens: int
    cost_microusd: int|None
    def __post_init__(self):
        integer(self.work_ms,minimum=1)
        integer(self.model_calls)
        integer(self.tokens)
        if self.cost_microusd is not None: integer(self.cost_microusd)

@dataclass(frozen=True)
class Usage:
    work_ms: int|None
    model_calls: int|None
    tokens: int|None
    cost_microusd: int|None
    proof_sha256: str
    def __post_init__(self):
        for name in _RESOURCES:
            if getattr(self,name) is not None: integer(getattr(self,name))
        sha(self.proof_sha256)

@dataclass(frozen=True)
class Failure:
    kind: FailureKind
    error_code: str
    check_sha256: str
    tree_sha256: str
    redacted_output_sha256: str
    def __post_init__(self):
        require(isinstance(self.kind,FailureKind),"typed failure required")
        token(self.error_code)
        for value in (self.check_sha256,self.tree_sha256,self.redacted_output_sha256): sha(value)
    @property
    def fingerprint(self):
        return digest({"kind":self.kind,"code":self.error_code,"output":self.redacted_output_sha256})

@dataclass(frozen=True)
class RepairPermit:
    allocation_id: str
    identity: InvocationIdentity
    plan_sha256: str
    failure_check_sha256: str
    attempt: int
    reason_code: str
    diff_sha256: str
    event_sha256: str

class WorkBudgetAuthority:
    """A serialized projection/extension of the scheduler's existing audit.

    Only a host authorizer supplies allocations. Worker names, session IDs and
    provider IDs do not select or replenish allocations. All parallel child
    reservations are charged to their ancestors before execution.
    """
    def __init__(self,*,audit_log,authorize,clock_ms=None):
        require(isinstance(audit_log,AuditLog) and callable(authorize),"existing host audit authority required")
        self.audit_log,self.authorize=audit_log,authorize
        self._last_append_ms=0
        self._projection=None
        self._projection_stamp=None
        self.clock_ms=clock_ms or (lambda:int(time.time()*1000))
        path=audit_log._path.absolute()
        require(not path.is_symlink(),"budget audit symlink denied")
        path.parent.mkdir(parents=True,exist_ok=True)
        parent=path.parent.stat()
        require(parent.st_uid==os.geteuid() and parent.st_mode & 0o022 == 0,
                "budget audit parent must be host-owned and not worker writable")
        self.parent_identity=(parent.st_dev,parent.st_ino)
        self.lock_path=path.with_name(path.name+".budget.lock")
        with _LOCKS_GUARD:
            self.thread_lock=_LOCKS.setdefault(str(path),threading.RLock())

    @contextmanager
    def _serialized(self):
        key=str(self.audit_log._path.absolute())
        with _LOCKS_GUARD:
            thread_lock=_LOCKS.setdefault(key,threading.RLock())
        with thread_lock:
            active=getattr(_ACTIVE_SERIALIZATIONS,"paths",set())
            key=str(self.audit_log._path.absolute())
            if key in active:
                # Composition may call another public budget method while
                # already holding this exact audit's process lock.
                parent=self.audit_log._path.parent.stat()
                require((parent.st_dev,parent.st_ino)==self.parent_identity
                    and parent.st_mode & 0o022 == 0 and not self.audit_log._path.is_symlink(),
                    "nested budget audit authority changed")
                self.audit_log.flush()
                yield
                return
            fd=os.open(self.lock_path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
            try:
                require(stat.S_ISREG(os.fstat(fd).st_mode),"budget lock must be regular")
                fcntl.flock(fd,fcntl.LOCK_EX)
                parent=self.audit_log._path.parent.stat()
                require((parent.st_dev,parent.st_ino)==self.parent_identity
                        and parent.st_mode & 0o022 == 0,"budget audit parent changed")
                path=self.audit_log._path
                require(not path.is_symlink(),"budget audit symlink denied")
                if path.exists():
                    held=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
                    try: require(stat.S_ISREG(os.fstat(held).st_mode),"budget audit must be regular")
                    finally: os.close(held)
                self.audit_log.flush()
                if path.exists():
                    require(path.stat().st_size<=8_388_608,"budget audit exceeds finite lineage bound")
                active.add(key)
                _ACTIVE_SERIALIZATIONS.paths=active
                descriptors=getattr(_ACTIVE_SERIALIZATIONS,"descriptors",{})
                descriptors[key]=fd
                _ACTIVE_SERIALIZATIONS.descriptors=descriptors
                try:
                    yield
                finally:
                    active.remove(key)
                    descriptors.pop(key,None)
            finally:
                fcntl.flock(fd,fcntl.LOCK_UN)
                os.close(fd)

    def _now(self,state=None):
        now=integer(self.clock_ms(),maximum=10**16,minimum=1)
        if state is not None:
            require(now>=state["last_ms"],"host clock regressed; new work blocked")
        return now

    def _append(self,event_kind,**data):
        now=self._now()
        require(now>=self._last_append_ms,"host clock regressed; new work blocked")
        event={"event":"work_budget_"+event_kind,"version":1,"at_ms":now,**data}
        self._last_append_ms=now
        require(len(canonical(event))<=131072,"budget event exceeds bound")
        event["event_sha256"]=digest(event)
        self.audit_log.append(event)
        self.audit_log.flush()
        if self._projection is not None:
            self._projection=self._state_checked(events=[event],state=deepcopy(self._projection))
            self._projection_stamp=self._stamp()
        return event["event_sha256"]

    def _stamp(self):
        path=self.audit_log._path
        if not path.exists(): return None
        info=path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid==os.geteuid() and info.st_nlink==1
                and info.st_mode & 0o022==0,"budget audit authority invalid")
        return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)

    def _state(self):
        try:
            stamp=self._stamp()
            if self._projection is not None and stamp==self._projection_stamp:
                return deepcopy(self._projection)
            before=time.monotonic()
            state=self._state_checked()
            require(time.monotonic()-before<=1.0,"budget cold replay exceeds bounded reconciliation window")
            require(self._stamp()==stamp,"budget audit changed during projection")
            self._projection,self._projection_stamp=deepcopy(state),stamp
            return state
        except BudgetBlocked:
            raise
        except (KeyError,TypeError,ValueError,RecursionError) as exc:
            raise BudgetBlocked("budget audit schema invalid") from exc

    def _state_checked(self,*,events=None,state=None):
        started=time.monotonic()
        if state is None: state={"allocations":{},"operations":{},"attempts":{},"failures":{},"alternatives":{},
               "stops":{},"variants":{},"trials":{},"instabilities":{},"counters":{},"last_ms":0}
        if events is None: events=self.audit_log.replay()
        require(len(events)<=8192,"budget lineage audit event count exceeded")
        for event in events:
            require(time.monotonic()-started<=1.0,"budget projection exceeds bounded reconciliation window")
            require(isinstance(event,dict) and len(canonical(event))<=131072,"budget audit event exceeds bound")
            name=event.get("event","")
            if not isinstance(name,str) or not name.startswith("work_budget_"): continue
            require(event.get("version")==1 and type(event.get("version")) is int
                and event.get("event_sha256")==digest({k:v for k,v in event.items() if k!="event_sha256"}),
                "budget audit integrity invalid")
            at=integer(event.get("at_ms"),maximum=10**16,minimum=1)
            require(at>=state["last_ms"],"budget audit clock invalid")
            state["last_ms"]=at
            kind=name.removeprefix("work_budget_")
            if kind=="allocation":
                raw=event["allocation"]
                allocation=BudgetAllocation(**{**raw,"limits":BudgetLimits(**raw["limits"])})
                old=state["allocations"].get(allocation.allocation_id)
                require(old is None,"duplicate budget allocation")
                require(not any(x["allocation"].consumer==allocation.consumer
                    and x["allocation"].work_key==allocation.work_key for x in state["allocations"].values()),
                    "work budget reset by alias")
                if allocation.parent_allocation_id is not None:
                    require(allocation.parent_allocation_id in state["allocations"],"budget ancestor missing")
                    parent=state["allocations"][allocation.parent_allocation_id]["allocation"]
                    require(parent.consumer==allocation.consumer and parent.lineage_key==allocation.lineage_key
                            and (parent.series_plan_sha256 is None or parent.series_plan_sha256==allocation.series_plan_sha256),
                            "budget ancestor identity mismatch")
                state["allocations"][allocation.allocation_id]={"allocation":allocation,"created_ms":at}
            elif kind=="reserve":
                key=event["operation_id"]
                require(key not in state["operations"],"operation reservation repeated")
                allocation_id=event["allocation_id"]
                require(allocation_id in state["allocations"],"operation allocation missing")
                demand=Demand(**event["demand"])
                identity=InvocationIdentity.from_dict(event["identity"])
                require(demand.cost_microusd is not None
                        and identity.consumer==state["allocations"][allocation_id]["allocation"].consumer,
                        "operation authorization replay invalid")
                for name in ("operation_id","allocation_id","semantic_key","plan_sha256"): sha(event[name])
                for name in ("provider","operation_kind"): token(event[name])
                require(key==digest({"allocation_id":allocation_id,"semantic_key":event["semantic_key"]}),
                        "economic operation identity invalid")
                self._available(state,allocation_id,at,identity,event["provider"])
                self._require_resources(state,allocation_id,demand)
                variant=event.get("variant_sha256")
                trial=event.get("trial_sha256")
                if state["allocations"][allocation_id]["allocation"].series_plan_sha256 is not None:
                    require(variant is not None and trial is not None,"finite series operation requires its authorized trial")
                if variant is not None:
                    self._require_series(state,allocation_id,variant,trial)
                state["operations"][key]={**event,"usage":None,"settlement_sha256":None,
                    "started":False,"check_result":None}
            elif kind=="start":
                op=state["operations"].get(event["operation_id"])
                require(op is not None and not op["started"] and op["usage"] is None,"operation start replay invalid")
                op["started"]=True
            elif kind=="settle":
                op=state["operations"].get(event["operation_id"])
                require(op is not None and op["usage"] is None,"operation settlement replay invalid")
                usage=Usage(**event["usage"])
                raw=event.get("check_result")
                if raw is not None:
                    from .work_cycle import CheckResult
                    check=CheckResult(**raw)
                    require(check.hash==usage.proof_sha256 and check.plan_sha256==op["plan_sha256"],
                            "durable check result binding invalid")
                    op["check_result"]=raw
                op["usage"],op["settlement_sha256"]=event["usage"],event["event_sha256"]
            elif kind=="counter":
                self._validate_counter(state,event)
                state["counters"][event["counter_id"]]=event
            elif kind=="attempt":
                allocation_id=event["allocation_id"]
                require(allocation_id in state["allocations"],"implementation allocation missing")
                identity=InvocationIdentity.from_dict(event["identity"])
                require(identity.consumer==state["allocations"][allocation_id]["allocation"].consumer,
                        "implementation consumer mismatch")
                sha(event["plan_sha256"]);token(event["reason_code"])
                attempts=state["attempts"].setdefault(allocation_id,[])
                self._validate_attempt(state,allocation_id,attempts,event)
                require(type(event["attempt"]) is int and event["attempt"]==len(attempts)+1,
                        "implementation attempts reset")
                attempts.append(event)
            elif kind=="failure":
                failure=Failure(**{**event["failure"],"kind":FailureKind(event["failure"]["kind"])})
                require(event["allocation_id"] in state["allocations"],"failure allocation missing")
                old=state["failures"].setdefault(event["allocation_id"],[])
                require(not any(x["typed"].check_sha256==failure.check_sha256 for x in old),
                        "failure evidence duplicate")
                old.append({**event,"typed":failure})
            elif kind=="alternative":
                allocation_id=event["allocation_id"]
                require(allocation_id in state["allocations"],"alternative allocation missing")
                kind=FailureKind(event["kind"])
                self._validate_alternative(state,allocation_id,kind,event)
                key=(allocation_id,event["kind"])
                state["alternatives"].setdefault(key,[]).append(event)
            elif kind=="variant":
                self._validate_series_marker(state,event,trial=False)
                state["variants"][(event["allocation_id"],event["variant_sha256"])]=event
            elif kind=="trial":
                self._validate_series_marker(state,event,trial=True)
                state["trials"][(event["allocation_id"],event["trial_sha256"])]=event
            elif kind=="instability":
                key=event["alternative_sha256"]
                require(key not in state["instabilities"] and any(x["event_sha256"]==key
                    and x["kind"]==FailureKind.FLAKY.value for rows in state["alternatives"].values() for x in rows),
                    "flaky rerun evidence invalid")
                for name in ("first_check_sha256","rerun_check_sha256","tree_sha256"): sha(event[name])
                require(type(event["unstable"]) is bool,"flaky stability state invalid")
                state["instabilities"][key]=event
            elif kind=="stop":
                stop=event["stop"]
                require(stop["stop_id"] not in state["stops"],"stop identity reused")
                StopScope(stop["scope"])
                sha(stop["stop_id"])
                if stop.get("allocation_id") is not None:
                    require(stop["allocation_id"] in state["allocations"],"stop allocation missing")
                for name in ("target","source","reason_code","resume_condition"): token(stop[name])
                state["stops"][stop["stop_id"]]={**stop,"active":True}
            elif kind=="resume":
                stop=state["stops"].get(event["stop_id"])
                require(stop is not None and stop["active"],"resume replay invalid")
                stop["active"]=False
            else: raise BudgetBlocked("unknown budget audit event")
        self._last_append_ms=state["last_ms"]
        return state

    @staticmethod
    def _ancestors(state,allocation_id):
        rows=[]
        while allocation_id is not None:
            require(allocation_id in state["allocations"] and allocation_id not in rows,"budget lineage invalid")
            rows.append(allocation_id)
            allocation_id=state["allocations"][allocation_id]["allocation"].parent_allocation_id
        return rows

    def open(self,*,consumer,work_key,lineage_key,authorization_reference):
        token(consumer)
        for value in (work_key,lineage_key,authorization_reference): sha(value)
        with self._serialized():
            state=self._state()
            for row in state["allocations"].values():
                current=row["allocation"]
                if current.consumer==consumer and current.work_key==work_key:
                    require(current.lineage_key==lineage_key and current.authorization_reference==authorization_reference,
                            "existing work budget authority changed")
                    return current
            proposed=self.authorize(consumer=consumer,work_key=work_key,lineage_key=lineage_key,
                                    authorization_reference=authorization_reference)
            require(isinstance(proposed,BudgetAllocation) and proposed.consumer==consumer
                    and proposed.work_key==work_key and proposed.lineage_key==lineage_key
                    and proposed.authorization_reference==authorization_reference,"host budget authorization missing")
            self._now(state)
            if proposed.parent_allocation_id is not None:
                parent=state["allocations"].get(proposed.parent_allocation_id)
                require(parent is not None and parent["allocation"].consumer==consumer
                    and parent["allocation"].lineage_key==lineage_key
                    and (parent["allocation"].series_plan_sha256 is None
                         or parent["allocation"].series_plan_sha256==proposed.series_plan_sha256),
                    "child budget lineage mismatch")
            self._append("allocation",allocation=asdict(proposed))
            return proposed

    def _charged(self,state,allocation_id):
        total={key:0 for key in _RESOURCES}
        inflight=0
        unknown=set()
        for op in state["operations"].values():
            if allocation_id not in self._ancestors(state,op["allocation_id"]): continue
            usage=op["usage"]
            if usage is None: inflight+=1
            for key in _RESOURCES:
                actual=None if usage is None else usage[key]
                total[key]+=op["demand"][key] if actual is None else actual
                if usage is not None and actual is None: unknown.add(key)
        return total,inflight,unknown

    def _available(self,state,allocation_id,now,identity=None,provider=None):
        for ancestor in self._ancestors(state,allocation_id):
            row=state["allocations"][ancestor]
            require(now-row["created_ms"]<=row["allocation"].limits.max_elapsed_ms,"elapsed work budget exhausted")
        for stop in state["stops"].values():
            if not stop["active"]: continue
            if stop.get("allocation_id") in self._ancestors(state,allocation_id):
                raise BudgetBlocked("new work stopped by cumulative allocation policy")
            scope=stop["scope"]
            matches=(scope=="consumer" and stop["target"]==state["allocations"][allocation_id]["allocation"].consumer
                or identity is not None and scope=="task" and stop["target"]==identity.task_id
                or identity is not None and scope=="executor" and stop["target"]==identity.agent_id
                or provider is not None and scope=="provider" and stop["target"]==provider)
            require(not matches,"new work stopped by scoped policy")

    def reserve(self,*,allocation_id,semantic_key,identity,plan_sha256,provider,demand,operation_kind="model",
                variant_sha256=None,trial_sha256=None):
        for value in (allocation_id,semantic_key,plan_sha256): sha(value)
        token(provider);token(operation_kind)
        require(isinstance(identity,InvocationIdentity) and isinstance(demand,Demand),"typed operation reservation required")
        require(demand.cost_microusd is not None,"unknown price cannot satisfy a financial ceiling")
        operation_id=digest({"allocation_id":allocation_id,"semantic_key":semantic_key})
        with self._serialized():
            state=self._state()
            old=state["operations"].get(operation_id)
            binding={"allocation_id":allocation_id,"semantic_key":semantic_key,"identity":identity.to_json(),
                "plan_sha256":plan_sha256,"provider":provider,"demand":asdict(demand),"operation_kind":operation_kind,
                "variant_sha256":variant_sha256,"trial_sha256":trial_sha256}
            if old is not None:
                require(all(old[key]==value for key,value in binding.items()),"same economic operation changed; reconcile original")
                return operation_id
            now=self._now(state)
            self._available(state,allocation_id,now,identity,provider)
            allocation=state["allocations"][allocation_id]["allocation"]
            require(allocation.consumer==identity.consumer,"operation consumer differs from allocation")
            if allocation.series_plan_sha256 is not None:
                require(variant_sha256 is not None and trial_sha256 is not None,
                        "finite series operation requires its authorized trial")
            if variant_sha256 is not None:
                self._require_series(state,allocation_id,variant_sha256,trial_sha256)
            else:
                require(trial_sha256 is None,"trial requires its authorized variant")
            try:
                self._require_resources(state,allocation_id,demand)
            except BudgetBlocked as exc:
                self._stop_for_allocation(state,allocation_id,exc.reason_code,identity)
                raise
            self._append("reserve",operation_id=operation_id,**binding)
            return operation_id

    def settle(self,operation_id,usage,*,check_result=None):
        sha(operation_id)
        require(isinstance(usage,Usage),"host measured usage required")
        if check_result is not None:
            from .work_cycle import CheckResult
            require(isinstance(check_result,CheckResult) and check_result.hash==usage.proof_sha256,
                    "typed measured check result required")
        with self._serialized():
            state=self._state()
            op=state["operations"].get(operation_id)
            require(op is not None,"unknown operation cannot be settled")
            if op["usage"] is not None:
                require(op["usage"]==asdict(usage) and op["check_result"]==
                        (asdict(check_result) if check_result is not None else None),"operation usage cannot be overwritten")
                return op["settlement_sha256"]
            self._now(state)
            require(check_result is None or check_result.plan_sha256==op["plan_sha256"],
                    "measured checker plan changed")
            result=self._append("settle",operation_id=operation_id,usage=asdict(usage),
                                check_result=asdict(check_result) if check_result is not None else None)
            if any(getattr(usage,key) is not None and getattr(usage,key)>op["demand"][key] for key in _RESOURCES):
                self._stop_for_allocation(state,op["allocation_id"],"measured_usage_exceeded_reservation",
                                          InvocationIdentity.from_dict(op["identity"]))
            return result

    def claim_start(self,operation_id):
        """One durable pre-effect claim. Duplicate callers only reconcile."""
        sha(operation_id)
        with self._serialized():
            state=self._state()
            op=state["operations"].get(operation_id)
            require(op is not None,"operation reservation missing")
            if op["started"] or op["usage"] is not None: return False
            self._available(state,op["allocation_id"],self._now(state),
                            InvocationIdentity.from_dict(op["identity"]),op["provider"])
            self._append("start",operation_id=operation_id)
            return True

    def reconcile(self,operation_id):
        sha(operation_id)
        with self._serialized():
            state=self._state()
            op=state["operations"].get(operation_id)
            require(op is not None,"unknown economic operation")
            # Stops/exhaustion never authorize another reservation or effect.
            return {key:op[key] for key in ("operation_id","identity","provider","plan_sha256","usage","started","check_result")}

    def record_failure(self,allocation_id,failure):
        sha(allocation_id)
        require(isinstance(failure,Failure),"host check failure required")
        with self._serialized():
            state=self._state()
            require(allocation_id in state["allocations"],"failure allocation missing")
            self._now(state)
            old=state["failures"].get(allocation_id,[])
            same=next((x["typed"] for x in old if x["typed"].check_sha256==failure.check_sha256),None)
            if same is not None:
                require(same==failure,"checker failure cannot be overwritten")
                return failure.fingerprint
            self._append("failure",allocation_id=allocation_id,failure=asdict(failure))
            return failure.fingerprint

    @staticmethod
    def _failure(state,allocation_id,check_sha256):
        found=next((x["typed"] for x in state["failures"].get(allocation_id,[])
                    if x["typed"].check_sha256==check_sha256),None)
        require(found is not None,"new host checker failure required")
        return found

    def _validate_attempt(self,state,allocation_id,attempts,event):
        allocation=state["allocations"][allocation_id]["allocation"]
        require(len(attempts)<allocation.limits.max_implementation_attempts,
                "implementation_attempts_exhausted")
        require(all(x["plan_sha256"]==event["plan_sha256"] for x in attempts),
                "repair cannot replace the approved work plan")
        if attempts:
            sha(event["failure_check_sha256"]);sha(event["diff_sha256"])
            integer(event["changed_files"],maximum=8,minimum=1)
            integer(event["changed_lines"],maximum=200,minimum=1)
            require(event["reason_code"]!="initial","repair reason required")
            failure=self._failure(state,allocation_id,event["failure_check_sha256"])
            require(failure.kind is FailureKind.IMPLEMENTATION,"repair requires implementation failure")
            require(not any(x["failure_check_sha256"]==event["failure_check_sha256"] for x in attempts),
                    "same failure without new evidence cannot reopen work")
            require(not any(x["typed"].check_sha256!=failure.check_sha256
                and x["typed"].fingerprint==failure.fingerprint
                and x["typed"].tree_sha256==failure.tree_sha256 for x in state["failures"].get(allocation_id,[])),
                "same error on unchanged code stops blind retry")
        else:
            require(event["failure_check_sha256"] is None and event["diff_sha256"] is None
                    and event["reason_code"]=="initial" and event["changed_files"]==event["changed_lines"]==0,
                    "first implementation starts once under the approved plan")

    @staticmethod
    def _permit(event):
        return RepairPermit(event["allocation_id"],InvocationIdentity.from_dict(event["identity"]),
            event["plan_sha256"],event["failure_check_sha256"],event["attempt"],
            event["reason_code"],event["diff_sha256"],event["event_sha256"])

    def begin_implementation(self,*,allocation_id,identity,plan_sha256,reason_code="initial",
                             failure_check_sha256=None,diff_sha256=None,changed_files=0,changed_lines=0):
        sha(allocation_id);sha(plan_sha256);token(reason_code)
        require(isinstance(identity,InvocationIdentity),"admitted implementation identity required")
        with self._serialized():
            state=self._state()
            require(allocation_id in state["allocations"],"implementation allocation missing")
            attempts=state["attempts"].get(allocation_id,[])
            event={"allocation_id":allocation_id,"identity":identity.to_json(),
                "plan_sha256":plan_sha256,"attempt":len(attempts)+1,"reason_code":reason_code,
                "failure_check_sha256":failure_check_sha256,"diff_sha256":diff_sha256,
                "changed_files":changed_files,"changed_lines":changed_lines}
            previous=next((x for x in attempts if x["identity"]==event["identity"]
                           and x["failure_check_sha256"]==failure_check_sha256),None)
            if previous is not None:
                require(all(previous[k]==v for k,v in event.items() if k!="attempt"),"repair evidence changed")
                return self._permit(previous)
            now=self._now(state)
            self._available(state,allocation_id,now,identity)
            allocation=state["allocations"][allocation_id]["allocation"]
            require(identity.consumer==allocation.consumer,"implementation consumer mismatch")
            try:
                self._validate_attempt(state,allocation_id,attempts,event)
            except BudgetBlocked as exc:
                self._stop_for_allocation(state,allocation_id,exc.reason_code,identity)
                raise
            event_sha=self._append("attempt",**event)
            return self._permit({**event,"event_sha256":event_sha})

    def validate_repair_permit(self,permit,cycle,*,historical=False):
        from .work_cycle import CheckResult,WorkPhase
        require(isinstance(permit,RepairPermit) and permit.attempt>1,"typed host repair permit required")
        require(permit.identity==cycle.plan.identity and permit.plan_sha256==cycle.plan.hash,
                "repair permit belongs to another work contract")
        with self._serialized():
            state=self._state()
            events=state["attempts"].get(permit.allocation_id,[])
            event=next((x for x in events if x["event_sha256"]==permit.event_sha256),None)
            require(event is not None and self._permit(event)==permit,"repair permit not in durable host audit")
            allocation=state["allocations"][permit.allocation_id]["allocation"]
            require(cycle.plan.budget_reference==allocation.hash,"repair budget differs from work plan")
            failure=self._failure(state,permit.allocation_id,permit.failure_check_sha256)
            checks=[CheckResult(**x["check"]) for x in cycle._events() if x["event"]=="work_check"]
            require(any(x.hash==failure.check_sha256 and x.plan_sha256==cycle.plan.hash
                and x.tree_sha256==failure.tree_sha256 and (x.exit_code!=0 or x.truncated) for x in checks),
                "repair requires the exact failed approved work checker")
            if not historical:
                self._available(state,permit.allocation_id,self._now(state),permit.identity)

    def _validate_alternative(self,state,allocation_id,kind,event):
        for name in ("contract_sha256","grant_sha256","failure_check_sha256","approval_sha256"): sha(event[name])
        require(kind in {FailureKind.FLAKY,FailureKind.TOOL,FailureKind.DEPENDENCY,FailureKind.PROVIDER},
                "error kind does not permit an alternative")
        failure=self._failure(state,allocation_id,event["failure_check_sha256"])
        require(failure.kind is kind,"alternative failure kind mismatch")
        rows=state["alternatives"].get((allocation_id,kind.value),[])
        cap=state["allocations"][allocation_id]["allocation"].limits.max_fallbacks if kind is FailureKind.PROVIDER else 1
        require(len(rows)<cap,"alternative budget exhausted")
        require(not any(x["failure_check_sha256"]==event["failure_check_sha256"] for x in rows),
                "same failure cannot authorize a second alternative")
        if kind is FailureKind.PROVIDER:
            for ancestor in self._ancestors(state,allocation_id):
                count=sum(len(values) for (child,k),values in state["alternatives"].items()
                          if k==kind.value and ancestor in self._ancestors(state,child))
                require(count<state["allocations"][ancestor]["allocation"].limits.max_fallbacks,
                        "cumulative provider fallback budget exhausted")
            sha(event.get("original_operation_id"))
            op=state["operations"].get(event["original_operation_id"])
            require(op is not None and op["allocation_id"]==allocation_id
                    and op["usage"] is not None and event.get("pre_delivery_proven") is True,
                    "uncertain provider operation must reconcile without fallback")
        if kind is FailureKind.TOOL:
            for ancestor in self._ancestors(state,allocation_id):
                require(self._counter_used(state,ancestor,"tool_fallbacks") <
                        state["allocations"][ancestor]["allocation"].limits.max_tool_fallbacks,
                        "cumulative tool_fallbacks exhausted")
        if kind is FailureKind.DEPENDENCY:
            require(event.get("workspace_local") is True,"dependency change must remain workspace local")
        if kind is FailureKind.FLAKY:
            require(event.get("same_tree_sha256")==failure.tree_sha256,"flaky rerun changed code")

    def one_alternative(self,*,allocation_id,kind,contract_sha256,grant_sha256,failure_check_sha256,
                        host_approval,original_operation_id=None,pre_delivery_proven=False,
                        workspace_local=False,same_tree_sha256=None):
        sha(allocation_id)
        require(isinstance(kind,FailureKind) and callable(host_approval),"host alternative authority required")
        event={"allocation_id":allocation_id,"kind":kind.value,"contract_sha256":contract_sha256,
            "grant_sha256":grant_sha256,"failure_check_sha256":failure_check_sha256,
            "original_operation_id":original_operation_id,"pre_delivery_proven":pre_delivery_proven,
            "workspace_local":workspace_local,"same_tree_sha256":same_tree_sha256}
        # The host must bind exact criteria/environment/grant/route and known pre-delivery proof.
        approval=host_approval(dict(event))
        sha(approval)
        event["approval_sha256"]=approval
        with self._serialized():
            state=self._state()
            now=self._now(state)
            self._available(state,allocation_id,now)
            self._validate_alternative(state,allocation_id,kind,event)
            return self._append("alternative",**event)

    def record_flaky_rerun(self,*,alternative_sha256,rerun_check,host_approval):
        from .work_cycle import CheckResult
        sha(alternative_sha256)
        require(isinstance(rerun_check,CheckResult) and callable(host_approval),"host flaky checker required")
        with self._serialized():
            state=self._state()
            old=state["instabilities"].get(alternative_sha256)
            if old is not None:
                require(old["rerun_check_sha256"]==rerun_check.hash,"flaky result cannot be replaced")
                return old["unstable"]
            alternative=next((x for rows in state["alternatives"].values() for x in rows
                if x["event_sha256"]==alternative_sha256 and x["kind"]==FailureKind.FLAKY.value),None)
            require(alternative is not None,"flaky alternative missing")
            first=self._failure(state,alternative["allocation_id"],alternative["failure_check_sha256"])
            require(rerun_check.plan_sha256==alternative["contract_sha256"]
                    and rerun_check.tree_sha256==first.tree_sha256
                    and host_approval(first,rerun_check) is True,"flaky rerun contract changed")
            unstable=rerun_check.exit_code==0 and not rerun_check.truncated or rerun_check.output_sha256!=first.redacted_output_sha256
            self._append("instability",alternative_sha256=alternative_sha256,
                first_check_sha256=first.check_sha256,rerun_check_sha256=rerun_check.hash,
                tree_sha256=first.tree_sha256,unstable=unstable)
            if unstable: self._stop_for_allocation(state,alternative["allocation_id"],"flaky_instability")
            return unstable

    def _counter_used(self,state,allocation_id,kind):
        values=[row["quantity"] for row in state["counters"].values() if row["counter"]==kind
                and allocation_id in self._ancestors(state,row["allocation_id"])]
        used=max(values,default=0) if kind=="candidate_depth" else sum(values)
        if kind=="tool_fallbacks":
            used+=sum(len(rows) for (child,k),rows in state["alternatives"].items()
                      if k==FailureKind.TOOL.value and allocation_id in self._ancestors(state,child))
        return used

    def _validate_counter(self,state,event):
        allocation_id=event["allocation_id"]
        require(allocation_id in state["allocations"],"counter allocation missing")
        kind=event["counter"]
        require(kind in _COUNTERS,"unknown lifecycle counter")
        quantity=integer(event["quantity"],maximum=4096,minimum=1)
        for name in ("counter_id","semantic_key","approval_sha256"):sha(event[name])
        require(event["counter_id"]==digest({"allocation":allocation_id,"kind":kind,"semantic":event["semantic_key"]}),
                "counter identity changed")
        require(event["counter_id"] not in state["counters"],"counter repeated")
        for ancestor in self._ancestors(state,allocation_id):
            used=self._counter_used(state,ancestor,kind)
            proposed=max(used,quantity) if kind=="candidate_depth" else used+quantity
            require(proposed<=getattr(state["allocations"][ancestor]["allocation"].limits,"max_"+kind),
                    "cumulative "+kind+" exhausted")

    def charge_counter(self,*,allocation_id,counter,semantic_key,quantity=1,host_approval):
        """Host lifecycle markers; they never authorize search or another effect."""
        sha(allocation_id);sha(semantic_key)
        require(counter in _COUNTERS and callable(host_approval),"host counter authority required")
        event={"allocation_id":allocation_id,"counter":counter,"semantic_key":semantic_key,"quantity":quantity,
               "counter_id":digest({"allocation":allocation_id,"kind":counter,"semantic":semantic_key})}
        with self._serialized():
            state=self._state()
            old=state["counters"].get(event["counter_id"])
            if old is not None:
                require(all(old[key]==value for key,value in event.items()),"counter replay changed")
                return old["event_sha256"]
            self._available(state,allocation_id,self._now(state))
            event["approval_sha256"]=sha(host_approval(dict(event)))
            try:
                self._validate_counter(state,event)
            except BudgetBlocked as exc:
                if "exhausted" in str(exc):self._stop_for_allocation(state,allocation_id,exc.reason_code)
                raise
            return self._append("counter",**event)

    def _require_resources(self,state,allocation_id,demand):
        for ancestor in self._ancestors(state,allocation_id):
            used,inflight,_=self._charged(state,ancestor)
            limits=state["allocations"][ancestor]["allocation"].limits
            require(inflight<limits.max_concurrency,"parallel work budget exhausted")
            for key in _RESOURCES:
                require(used[key]+getattr(demand,key)<=getattr(limits,"max_"+key),
                        "cumulative "+key+" budget exhausted")

    def _count_markers(self,state,allocation_id,kind):
        return sum(1 for (child,_),row in state[kind].items()
                   if allocation_id in self._ancestors(state,child))

    def _validate_series_marker(self,state,event,*,trial):
        allocation_id=event["allocation_id"]
        require(allocation_id in state["allocations"],"series allocation missing")
        sha(event["variant_sha256"]);sha(event["plan_sha256"]);sha(event["approval_sha256"])
        series=state["allocations"][allocation_id]["allocation"].series_plan_sha256
        require(series is None or series==event["plan_sha256"],"finite series plan cannot change")
        if trial:
            sha(event["trial_sha256"]);token(event["reason_code"])
            require((allocation_id,event["variant_sha256"]) in state["variants"],"authorized variant missing")
            require((allocation_id,event["trial_sha256"]) not in state["trials"],"trial identity reused")
        else:
            require((allocation_id,event["variant_sha256"]) not in state["variants"],"variant identity reused")
        for ancestor in self._ancestors(state,allocation_id):
            limit=state["allocations"][ancestor]["allocation"].limits
            require(self._count_markers(state,ancestor,"trials" if trial else "variants")
                    < (limit.max_trials if trial else limit.max_variants),
                    "cumulative series trial budget exhausted" if trial else "cumulative series variant budget exhausted")

    def declare_variant(self,*,allocation_id,variant_sha256,plan_sha256,host_approval):
        return self._series_marker(allocation_id,variant_sha256,plan_sha256,host_approval)

    def begin_trial(self,*,allocation_id,variant_sha256,trial_sha256,plan_sha256,reason_code,host_approval):
        return self._series_marker(allocation_id,variant_sha256,plan_sha256,host_approval,
                                   trial_sha256=trial_sha256,reason_code=reason_code)

    def _series_marker(self,allocation_id,variant_sha256,plan_sha256,host_approval,**trial):
        sha(allocation_id);sha(variant_sha256);sha(plan_sha256)
        require(callable(host_approval),"bounded series host authority required")
        event={"allocation_id":allocation_id,"variant_sha256":variant_sha256,
               "plan_sha256":plan_sha256,**trial}
        with self._serialized():
            state=self._state()
            is_trial=bool(trial)
            key=(allocation_id,trial["trial_sha256"] if is_trial else variant_sha256)
            old=state["trials" if is_trial else "variants"].get(key)
            if old is not None:
                require(all(old[k]==v for k,v in event.items()),"series identity changed")
                return old["event_sha256"]
            self._available(state,allocation_id,self._now(state))
            event["approval_sha256"]=sha(host_approval(dict(event)))
            self._validate_series_marker(state,event,trial=is_trial)
            return self._append("trial" if is_trial else "variant",**event)

    def _require_series(self,state,allocation_id,variant,trial):
        sha(variant);sha(trial)
        variant_row=state["variants"].get((allocation_id,variant))
        trial_row=state["trials"].get((allocation_id,trial))
        require(variant_row is not None and trial_row is not None
                and trial_row["variant_sha256"]==variant
                and trial_row["plan_sha256"]==variant_row["plan_sha256"],
                "operation lacks its authorized finite series trial")

    def _stop_for_allocation(self,state,allocation_id,reason,identity=None):
        allocation=state["allocations"][allocation_id]["allocation"]
        scope=StopScope.TASK if identity is not None else StopScope.CONSUMER
        target=identity.task_id if identity is not None else allocation.consumer
        stop_id=digest({"allocation_id":allocation_id,"reason":reason,"scope":scope,"target":target})
        if stop_id not in state["stops"]:
            self._append("stop",stop={"stop_id":stop_id,"scope":scope.value,"target":target,
                "source":"work-budget-authority","reason_code":reason,"resume_condition":"host-review-and-remaining-budget",
                "allocation_id":allocation_id})

    def stop(self,*,stop_id,scope,target,source,reason_code,resume_condition):
        sha(stop_id)
        require(isinstance(scope,StopScope),"typed stop scope required")
        for value in (target,source,reason_code,resume_condition): token(value)
        with self._serialized():
            state=self._state();self._now(state)
            if stop_id in state["stops"]:
                require(all(state["stops"][stop_id].get(key)==value for key,value in
                    {"scope":scope.value,"target":target,"source":source,"reason_code":reason_code,
                     "resume_condition":resume_condition}.items()),"stop identity changed")
                return
            self._append("stop",stop={"stop_id":stop_id,"scope":scope.value,"target":target,
                "source":source,"reason_code":reason_code,"resume_condition":resume_condition})

    def resume(self,*,stop_id,allocation_id,identity,valid_grant_sha256,host_approval):
        for value in (stop_id,allocation_id,valid_grant_sha256): sha(value)
        require(isinstance(identity,InvocationIdentity) and callable(host_approval),"host resume authority required")
        with self._serialized():
            state=self._state()
            stop=state["stops"].get(stop_id)
            require(stop is not None and stop["active"],"active scoped stop required")
            allocation=state["allocations"].get(allocation_id)
            require(allocation is not None and allocation["allocation"].consumer==identity.consumer,
                    "resume allocation identity mismatch")
            if stop.get("allocation_id") is not None:
                require(stop["allocation_id"] in self._ancestors(state,allocation_id),"resume stop allocation mismatch")
            scope=StopScope(stop["scope"])
            expected={StopScope.TASK:identity.task_id,StopScope.EXECUTOR:identity.agent_id,
                      StopScope.CONSUMER:identity.consumer}
            require(scope is StopScope.PROVIDER or stop["target"]==expected[scope],"resume stop scope mismatch")
            require(len(state["attempts"].get(allocation_id,[])) <
                    allocation["allocation"].limits.max_implementation_attempts,"implementation attempts exhausted")
            now=self._now(state)
            require(host_approval(stop,identity,valid_grant_sha256) is True,"resume conditions or grant not valid")
            # Check remaining limits without resetting any consumption.
            for ancestor in self._ancestors(state,allocation_id):
                row=state["allocations"][ancestor]
                used,inflight,_=self._charged(state,ancestor)
                limits=row["allocation"].limits
                require(now-row["created_ms"]<=limits.max_elapsed_ms,"elapsed work budget exhausted")
                require(all(used[key]<getattr(limits,"max_"+key) or key=="cost_microusd"
                    and used[key]==0 and limits.max_cost_microusd==0 for key in _RESOURCES),
                    "work budget exhausted")
            self._append("resume",stop_id=stop_id,allocation_id=allocation_id,
                         identity=identity.to_json(),valid_grant_sha256=valid_grant_sha256)

    def require_active(self,allocation_id,identity,provider=None):
        sha(allocation_id)
        require(isinstance(identity,InvocationIdentity),"exact active budget identity required")
        with self._serialized():
            state=self._state()
            require(state["allocations"][allocation_id]["allocation"].consumer==identity.consumer,
                    "active work consumer mismatch")
            self._available(state,allocation_id,self._now(state),identity,provider)

    def find_allocation(self,reference):
        sha(reference)
        with self._serialized():
            state=self._state()
            found=next((row["allocation"] for row in state["allocations"].values()
                        if row["allocation"].hash==reference),None)
            require(found is not None,"durable budget reference missing")
            return found

    def snapshot(self,allocation_id):
        sha(allocation_id)
        with self._serialized():
            state=self._state()
            require(allocation_id in state["allocations"],"budget allocation missing")
            used,inflight,unknown=self._charged(state,allocation_id)
            return {"version":1,"allocation_id":allocation_id,"charged_upper_bounds":used,
                "inflight":inflight,"unknown_measurements":sorted(unknown),
                "implementation_attempts":len(state["attempts"].get(allocation_id,[])),
                "fallbacks":sum(len(rows) for (child,kind),rows in state["alternatives"].items()
                    if kind==FailureKind.PROVIDER.value and allocation_id in self._ancestors(state,child)),
                "variants":self._count_markers(state,allocation_id,"variants"),
                "trials":self._count_markers(state,allocation_id,"trials"),
                "instabilities":[x for x in state["instabilities"].values()
                    if any(a["event_sha256"]==x["alternative_sha256"] for a in
                           state["alternatives"].get((allocation_id,FailureKind.FLAKY.value),[]))],
                "counters":{kind:self._counter_used(state,allocation_id,kind) for kind in _COUNTERS},
                "implementation_retries":sum(max(0,len(rows)-1) for child,rows in state["attempts"].items()
                    if allocation_id in self._ancestors(state,child)),
                "active_stops":[x for x in state["stops"].values() if x["active"]]}


class BudgetedCheckRunner:
    """Physical checks share the same budget, including baseline and holdout."""
    def __init__(self,authority,allocation,runner,purpose,*,variant_sha256=None,trial_sha256=None):
        require(isinstance(authority,WorkBudgetAuthority) and isinstance(allocation,BudgetAllocation)
                and callable(runner),"host budgeted checker required")
        token(purpose)
        self.authority,self.allocation,self.runner,self.purpose=authority,allocation,runner,purpose
        self.variant_sha256,self.trial_sha256=variant_sha256,trial_sha256

    def __call__(self,check,root,plan,tree):
        from .work_cycle import CheckResult
        state=self.authority.snapshot(self.allocation.allocation_id)
        semantic=digest({"purpose":self.purpose,"plan":plan.hash,"tree":tree,"check":check.id,
                         "implementation_attempt":state["implementation_attempts"]})
        operation=self.authority.reserve(allocation_id=self.allocation.allocation_id,
            semantic_key=semantic,identity=plan.identity,plan_sha256=plan.hash,provider="offline-check",
            demand=Demand((check.timeout_seconds+13)*1000,0,0,0),operation_kind="check",
            variant_sha256=self.variant_sha256,trial_sha256=self.trial_sha256)
        if not self.authority.claim_start(operation):
            old=self.authority.reconcile(operation)
            require(old["check_result"] is not None,"check execution uncertain; reconcile exact invocation")
            return CheckResult(**old["check_result"])
        result=self.runner(check,root,plan,tree)
        require(isinstance(result,CheckResult) and result.plan_sha256==plan.hash
                and result.tree_sha256==tree,"physical budgeted checker result invalid")
        self.authority.settle(operation,Usage(result.duration_ms,0,0,0,result.hash),check_result=result)
        return result


@dataclass(frozen=True)
class ModelReservation:
    semantic_key: str
    demand: Demand
    provider: str

class BudgetModelPort:
    """Host-selected economic call IDs and quotes before the physical SDK call."""
    def __init__(self,*,authority,allocation,identity,plan_sha256,grant_sha256,quote,
                 variant_sha256=None,trial_sha256=None):
        require(isinstance(authority,WorkBudgetAuthority) and isinstance(allocation,BudgetAllocation)
                and isinstance(identity,InvocationIdentity) and callable(quote),"host model budget port required")
        sha(plan_sha256);sha(grant_sha256)
        self.authority,self.allocation,self.identity=authority,allocation,identity
        self.plan_sha256,self.grant_sha256,self.quote=plan_sha256,grant_sha256,quote
        self.variant_sha256,self.trial_sha256=variant_sha256,trial_sha256

    def _authorize(self,request,guard,cycle):
        from .security import InvocationGuard,ProviderRequest
        from .work_cycle import WorkCycle
        require(isinstance(guard,InvocationGuard) and isinstance(cycle,WorkCycle)
                and isinstance(request,ProviderRequest),"physical model policy and work cycle required")
        require(guard.grant.identity==self.identity and guard.grant.hash==self.grant_sha256
                and cycle.plan.identity==self.identity and cycle.plan.hash==self.plan_sha256
                and cycle.plan.budget_reference==self.allocation.hash
                and cycle.plan.grant_sha256==self.grant_sha256 and cycle.implementation_allowed(),
                "model grant or work phase invalid")
        guard.authorize_provider(request)

    def reserve(self,request,*,guard,cycle):
        self._authorize(request,guard,cycle)
        selected=self.quote(request)
        require(isinstance(selected,ModelReservation) and selected.provider==request.provider,
                "trusted model price upper bound and matching route required")
        return self.authority.reserve(allocation_id=self.allocation.allocation_id,
            semantic_key=selected.semantic_key,identity=self.identity,plan_sha256=self.plan_sha256,
            provider=selected.provider,demand=selected.demand,
            variant_sha256=self.variant_sha256,trial_sha256=self.trial_sha256)

    def begin_effect(self,operation_id,request,*,guard,cycle):
        # Expiry/revocation/work phase are rechecked at the actual SDK seam.
        self._authorize(request,guard,cycle)
        old=self.authority.reconcile(operation_id)
        require(old["identity"]==self.identity.to_json() and old["plan_sha256"]==self.plan_sha256
                and old["provider"]==request.provider,"physical model operation binding changed")
        require(self.authority.claim_start(operation_id),"model operation already started; reconcile original")
        return self.authority.reconcile(operation_id)

    def reconcile(self,operation_id):
        return self.authority.reconcile(operation_id)
