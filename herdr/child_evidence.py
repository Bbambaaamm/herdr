"""Shared #85 semantic gate for admitted durable children."""
from dataclasses import asdict,dataclass
from pathlib import Path
import os
import stat
import errno

from .evidence import (EvidenceError,EvidenceMissing,EvidenceUnavailable,EvidenceStore,accept_artifact,binding,
                       canonical,digest,validate_plan)
from .security import InvocationIdentity

HOST_CHILD_COMPLETION_AUTHORITY = None

def child_workspace(rec):
    try:
        logical,raw=rec.worktree_identity.rsplit("|",1)
        device,inode=map(int,raw.split(":"))
        path=Path(logical)
        if not path.is_absolute() or ".." in path.parts or device<0 or inode<=0:
            raise ValueError()
        return path,device,inode
    except (ValueError,AttributeError,TypeError) as exc:
        raise EvidenceError("exact pinned child worktree required") from exc

def require_child_workspace(rec):
    path,device,inode=child_workspace(rec)
    flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC
    fd=None
    try:
        if len(path.parts)>128:
            raise EvidenceError("pinned child worktree path exceeds bound")
        fd=os.open("/",flags)
        for part in path.parts[1:]:
            child=os.open(part,flags,dir_fd=fd)
            os.close(fd)
            fd=child
        held=os.fstat(fd)
        if not stat.S_ISDIR(held.st_mode) or (held.st_dev,held.st_ino)!=(device,inode):
            raise EvidenceError("pinned child worktree replaced")
    except OSError as exc:
        if exc.errno in {errno.ENOENT,errno.ENOTDIR,errno.ELOOP,errno.ESTALE,errno.EACCES,errno.EPERM}:
            raise EvidenceError("pinned child worktree missing, replaced or inaccessible; replan required") from exc
        raise EvidenceUnavailable("pinned child worktree temporarily unavailable") from exc
    finally:
        if fd is not None:
            os.close(fd)

def child_task(rec):
    attestation=rec.execution_sandbox_attestation or {}
    task = {"id":rec.node.id,"run_token":rec.run_token,"idempotency_key":rec.idempotency_key,
        "attempt_id":rec.attempts,"fencing_token":rec.fencing_token,"repo":rec.repo,
        "issue":rec.issue,"parent_task_id":rec.parent_task_id,"parent_agent_id":rec.parent_agent_id,
        "execution_session":{"agent_name":rec.execution_agent,"pane_id":rec.execution_pane,
            "pane_marker":rec.execution_marker,"sandbox_pid":attestation.get("sandbox_pid"),
            "sandbox_verified":rec.execution_sandbox_verified,"sandbox_attestation":attestation,
            "invocation_policy":attestation.get("invocation_policy")},
        "parent_run_token":getattr(rec,"parent_run_token",None),
        "objective":rec.node.objective,"role":rec.node.role,
        "tools":list(rec.node.tools),"permissions":list(rec.node.permissions),
        "worktree_identity":rec.worktree_identity}
    if rec.ownership is not None:
        task["ownership"] = rec.ownership.to_json()
        task["owned_write_mounts"] = None if rec.owned_write_mounts is None else [dict(x) for x in rec.owned_write_mounts]
    return task

def child_scope_spec(task, ownership=None):
    spec={key:task[key] for key in ("repo","issue","parent_task_id","parent_agent_id",
        "objective","role","tools","permissions","worktree_identity")}
    if ownership is not None:
        spec["ownership_sha256"] = ownership.hash
    return digest(spec)

def child_spec(rec):
    return child_scope_spec(child_task(rec),rec.ownership)

def child_identity(rec):
    return InvocationIdentity("github:"+rec.repo,rec.agent_id,rec.parent_agent_id,
        rec.parent_task_id,rec.node.id,rec.run_token,rec.fencing_token)

@dataclass(frozen=True)
class AcceptedChildReceipt:
    version: int
    identity: dict
    result_payload_sha256: str
    bundle_sha256: str
    plan_sha256: str
    spec_sha256: str
    policy_sha256: str
    level: str

    def to_json(self):
        return asdict(self)

    def validate(self,rec,payload_sha256=None):
        if (type(self.version) is not int or self.version!=2 or self.identity!=child_identity(rec).to_json()
                or self.spec_sha256!=child_spec(rec) or self.level!="verified_worker_result"
                or any(not isinstance(x,str) or len(x)!=64 or set(x)-set("0123456789abcdef")
                    for x in (self.result_payload_sha256,self.bundle_sha256,self.plan_sha256,
                              self.spec_sha256,self.policy_sha256))
                or payload_sha256 is not None and self.result_payload_sha256!=payload_sha256):
            raise EvidenceError("accepted child receipt binding invalid")

class ChildCompletionAuthority:
    """Only host composition creates this port and its frozen plans.

    The worker result may reference an artifact and PR. Its evidence/producer
    labels do not create acceptance. Typed research/review criteria come from
    the host-approved plan, never from the role name alone.
    """
    def __init__(self,*,store,approve,collector):
        if not isinstance(store,EvidenceStore) or not callable(approve) or not callable(collector):
            raise EvidenceError("host child completion authority required")
        self.store,self.approve,self.collector=store,approve,collector
        self.work_contracts = None
        self.work_factories = {}

    def prepare_delegation(self, proposal, *, parent_task_id, parent_agent_id, repo, issue):
        """Add verification only for an exact protected modern coding scope."""
        from dataclasses import replace
        contracts=self.work_contracts
        if contracts is None or contracts["version"]==1 or "herdr_verify_work" in proposal.child_tools:
            return proposal
        if contracts["version"] not in (2,3):
            raise EvidenceError("child work catalogue version unsupported")
        candidate=replace(proposal,child_tools=tuple(sorted(
            set(proposal.child_tools)|{"herdr_verify_work"})))
        task=dict(repo=repo,issue=issue,parent_task_id=parent_task_id,
            parent_agent_id=parent_agent_id,objective=candidate.child_task,
            role=candidate.child_role,tools=list(candidate.child_tools),
            permissions=list(candidate.child_permissions),
            worktree_identity=candidate.worktree_identity)
        entry=contracts["children"].get(child_scope_spec(task,candidate.ownership))
        if entry is None or entry["kind"]!="coding" or entry["work_contract_version"]!=1:
            return proposal
        if "herdr_verify_work" not in proposal.parent_tools:
            raise EvidenceError("approved coding child needs verification in the parent scope")
        return candidate

    def prepare(self,rec):
        task=child_task(rec)
        key=digest(binding(task))
        try:
            old=self.store.read("plan",key)
        except EvidenceMissing:
            old=None
        plan=self.approve(task=task,spec_sha256=child_spec(rec))
        validate_plan(plan)
        if old is None:
            if (plan["identity"]!=binding(task) or plan["repo"]!=rec.repo
                    or plan["spec_hash"]!=child_spec(rec) or plan["kind"] not in {"coding","research","review"}):
                raise EvidenceError("child predispatch plan binding invalid")
            self.store.protect_from((child_workspace(rec)[0],))
            self.store.publish("plan",key,plan)
        else:
            validate_plan(old)
            if old["identity"]!=binding(task) or old["repo"]!=rec.repo or old["spec_hash"]!=child_spec(rec) or old["plan_hash"]!=plan["plan_hash"]:
                raise EvidenceError("child plan changed across restart")

    def modern_work(self, rec):
        contracts = self.work_contracts
        if contracts is None or contracts["version"] == 1:
            return False
        entry = contracts["children"].get(child_spec(rec))
        if entry is None:
            raise EvidenceError("child work lacks the exact protected contract")
        return entry["kind"] == "coding" and entry["work_contract_version"] == 1

    def _work_task(self, rec, plan):
        task = child_task(rec)
        if self.work_contracts["version"]==3:task["work_budget_version"]=1
        task.update(workspace=str(child_workspace(rec)[0]), work_contract_version=1,
                    completion_plan={"base_sha":plan["base_sha"]},
                    work_workspace_identity=f"{child_workspace(rec)[1]}:{child_workspace(rec)[2]}")
        return task

    def preflight_work(self,rec,launch):
        if not self.modern_work(rec):return None
        from .work_configuration import build_root_work_factory,preflight_handoff
        plan=self.store.read("plan",digest(binding(child_task(rec))))
        task=self._work_task(rec,plan)
        factory=build_root_work_factory(self.store.root.parent,task,spec_sha256=child_spec(rec))
        preflight_handoff(factory,launch,plan,require_slot=False)
        self.work_factories[digest(child_identity(rec).to_json())]=factory
        return factory

    def prepare_work(self, rec, launch):
        if not self.modern_work(rec):
            return None
        from .work_configuration import build_root_work_factory, bind_root_handoff, preflight_handoff
        plan = self.store.read("plan", digest(binding(child_task(rec))))
        task = self._work_task(rec, plan)
        factory = self.work_factories.get(digest(child_identity(rec).to_json())) or self.preflight_work(rec,launch)
        preflight_handoff(factory, launch, plan)
        cycle = factory.prepare(identity=child_identity(rec), workspace=Path(task["workspace"]),
                                grant=launch.grant, spec_sha256=child_spec(rec))
        port = bind_root_handoff(factory, task, launch, cycle)
        self.work_factories[digest(child_identity(rec).to_json())] = factory
        launch.mount.bootstrap.work_authority = factory.authorize_invocation
        launch.mount.bootstrap.work_verify = factory.verify_request
        launch.mount.bootstrap.work_budget = factory.budget_effect
        return port

    def recover_work(self, rec, plan):
        from .work_configuration import build_root_work_factory
        from .work_cycle import WorkPlan
        task = self._work_task(rec, plan)
        identity = child_identity(rec)
        key = digest(identity.to_json())
        factory = self.work_factories.get(key)
        if factory is None:
            factory = build_root_work_factory(self.store.root.parent, task, recovery=True,
                                             spec_sha256=child_spec(rec))
            self.work_factories[key] = factory
        if key not in factory.cycles:
            records = [row for row in factory.audit_log.replay() if
                       row.get("event") == "work_plan" and row.get("work_cycle") == identity.to_json()]
            if len(records) != 1:
                raise EvidenceError("original child work plan is missing or ambiguous")
            saved = WorkPlan.from_json(records[0]["plan"])
            factory.recover(identity=identity, workspace=Path(task["workspace"]),
                spec_sha256=child_spec(rec), grant_sha256=task["execution_session"]["invocation_policy"]["grant_sha256"],
                plan_sha256=saved.hash)
        return factory, task

    def recover_local_result(self, rec, result_path):
        if not self.modern_work(rec):
            return False
        from .work_configuration import recover_host_handoff
        from .work_cycle import WorkPhase
        plan = self.store.read("plan", digest(binding(child_task(rec))))
        factory, task = self.recover_work(rec, plan)
        cycle = factory.cycle(child_identity(rec))
        if cycle.phase not in {WorkPhase.HYGIENE, WorkPhase.HANDOFF}:
            return False
        port = recover_host_handoff(factory, task, cycle, plan)
        if Path(port.slot.path) != Path(result_path):
            raise EvidenceError("original child result slot path changed")
        requests = [key for key,value in cycle.verification_requests.items() if value is not None
                    and value["status"] == "pass" and value.get("tree_sha256") == cycle.verified_tree]
        if not requests:
            raise EvidenceError("original passed child handoff request is missing")
        port.deliver(cycle, requests[-1])
        return True

    def instructions(self,rec):
        task=child_task(rec)
        plan=self.store.read("plan",digest(binding(task)))
        validate_plan(plan)
        if self.modern_work(rec):
            return ("\nHOST CHILD WORK CONTRACT: Use herdr_verify_work with a stable request_id and a handoff declaration. "
                "The host runs the frozen oracle, preserves hooks, seals the exact tested local artifact and submits the original result. "
                "PASS ends implementation; pending independent CI/review never starts another economic attempt.\n"
                "Frozen completion plan: " + canonical(plan).decode() + "\n")
        artifact={"task_id":rec.node.id,"attempt":rec.attempts,"base_sha":plan["base_sha"],
            "commit_sha":"<exact result commit>","result_sha":"<sealed ArtifactRef SHA256>",
            "changed_files":["<exact changed files>"],"branch":"<isolated task branch>"}
        return ("\nHOST CHILD COMPLETION CONTRACT:\n"
            "- Lifecycle settlement is not verified completion. Preserve this attempt while CI/review is pending.\n"
            "- Submit through herdr_submit_result with exactly one evidence item {herdr_completion:{version:1,artifact:<ArtifactRef>,pr_number:<integer>,scope_self_check:<only when required>}}; the host derives the admitted workspace.\n"
            "- The reviewed commit must include this exact immutable footer: "+__import__("herdr.verification_binding",fromlist=["commit_footer"]).commit_footer(plan)+"\n"
            "- Worker evidence/producer labels cannot waive host validation.\n"
            "- A frozen scope_policy requires exact scope_self_check; unrelated or shared-contract changes require a revised host plan, never implicit scope expansion.\n"
            "- Artifact contract: "+canonical(artifact).decode()+"\n"
            "- Frozen plan: "+canonical(plan).decode()+"\n")

    def verify(self,rec,payload):
        if not isinstance(payload,dict):
            raise EvidenceError("complete child artifact payload required")
        try:
            encoded=canonical(payload)
            if len(encoded)>131072:
                raise ValueError()
            payload_hash=digest(payload)
        except (ValueError,TypeError,UnicodeError) as exc:
            raise EvidenceError("child result payload invalid or oversized") from exc
        task=child_task(rec)
        plan=self.store.read("plan",digest(binding(task)))
        validate_plan(plan)
        if plan["spec_hash"]!=child_spec(rec):
            raise EvidenceError("child specification changed")
        from .result_candidate import completion_candidate
        candidate=completion_candidate(payload,workspace=child_workspace(rec)[0])
        workspace=candidate.get("artifact_workspace")
        if (not isinstance(workspace,str) or not Path(workspace).is_absolute()
                or Path(workspace)!=child_workspace(rec)[0]):
            raise EvidenceError("child artifact workspace differs from admitted worktree")
        accepted,_=self.store.lookup_acceptance(binding(task),plan["plan_hash"])
        if accepted is None:
            require_child_workspace(rec)
        def collect(*args):
            require_child_workspace(rec)
            result=self.collector(*args)
            require_child_workspace(rec)
            return result
        work_factory = cycle = invocation_verifier = None
        if self.modern_work(rec):
            work_factory, work_task = self.recover_work(rec, plan)
            cycle = work_factory.before_completion(child_identity(rec), payload)
            invocation_verifier = work_factory.result_authority.verifier(
                work_task, payload, plan, work_plan_sha256=cycle.plan.hash)
            from agent_completion_evidence import collect_local_handoff
            def collect(*args):
                require_child_workspace(rec)
                result = collect_local_handoff(*args)
                require_child_workspace(rec)
                return result
        bundle=accept_artifact(task,candidate,plan,self.store,Path(workspace),collect,result_payload_sha256=payload_hash,
                               invocation_verifier=invocation_verifier)
        if cycle is not None:
            cycle.handed_off(bundle["bundle_hash"])
        receipt=AcceptedChildReceipt(2,child_identity(rec).to_json(),payload_hash,bundle["bundle_hash"],
            plan["plan_hash"],plan["spec_hash"],plan["policy_hash"],bundle["level"])
        receipt.validate(rec,payload_hash)
        return receipt

    def accepted_handoff(self,rec,*,registry=None):
        """Project protected acceptance separately from the historical candidate."""
        if rec.result_status!="completed" or not rec.cleanup_complete or rec.completion_receipt is None:
            return None
        from dataclasses import replace
        from .handoff import HandoffEnvelope,HandoffRef
        from .ownership_release import namespace_exited
        from .child_ownership import OwnershipError
        if getattr(rec,"namespace_lifetime",None) is not None and not namespace_exited(rec.namespace_lifetime):
            return None
        receipt=AcceptedChildReceipt(**rec.completion_receipt)
        receipt.validate(rec)
        task=child_task(rec)
        plan=self.store.read("plan",digest(binding(task)))
        validate_plan(plan)
        bundle,_=self.store.lookup_acceptance(binding(task),plan["plan_hash"])
        if (bundle is None or digest(bundle)!=receipt.bundle_sha256
                or bundle.get("result_payload_sha256")!=receipt.result_payload_sha256
                or bundle.get("spec_hash")!=receipt.spec_sha256
                or bundle.get("policy_hash")!=receipt.policy_sha256
                or bundle.get("level")!="verified_worker_result"
                or bundle.get("artifact",{}).get("base_sha")!=plan["base_sha"]):
            raise EvidenceError("accepted child handoff source binding invalid")
        candidate=HandoffEnvelope.from_json(rec.result_handoff)
        candidate.require_binding(rec)
        artifact=bundle["artifact"]
        base_hash=digest({"git_commit":artifact["base_sha"]})
        unknowns=tuple(x for x in candidate.unknowns if x not in {"semantic_acceptance","git_base"})
        remaining=tuple(x for x in candidate.remaining_criteria if x!="host_validation")
        state="COMPLETE" if not (unknowns or remaining or candidate.contradictions) else "UNKNOWN"
        accepted=replace(candidate,base_sha256=base_hash,current_state=state,
            artifact_refs=candidate.artifact_refs+(
                HandoffRef("git-base:"+artifact["base_sha"],base_hash),
                HandoffRef("git-artifact:"+artifact["commit_sha"],artifact["result_sha"])),
            evidence_refs=candidate.evidence_refs+(
                HandoffRef("accepted-bundle:"+receipt.bundle_sha256,receipt.bundle_sha256),),
            unknowns=unknowns,remaining_criteria=remaining,
            next_action="parent_synthesis_and_integration")
        try:
            accepted.require_current(rec,base_sha256=base_hash,registry=registry)
        except OwnershipError:
            return None
        return accepted.to_json()


def rejected_child_candidate(rec, payload, error):
    from .result_candidate import bounded_result
    bounded_result(payload)
    if (not isinstance(payload, dict) or payload.get("status") != "completed"
            or payload.get("task_id") != rec.node.id or payload.get("run_token") != rec.run_token
            or payload.get("fencing_token") != rec.fencing_token
            or payload.get("idempotency_key") != rec.idempotency_key):
        raise EvidenceError("rejected child candidate lacks exact attempt binding")
    document = {"version": 1, "identity": child_identity(rec).to_json(),
        "candidate_status": "completed", "level": "needs_replan",
        "result_payload_sha256": digest(payload), "artifact_sha256": payload.get("artifact_sha256"),
        "code": error.code, "reason": str(error)[:1024] or error.code}
    validate_child_rejection(rec, document)
    return document

def validate_child_rejection(rec, document):
    import re
    if (not isinstance(document, dict) or set(document) != {"version", "identity",
            "candidate_status", "level", "result_payload_sha256", "artifact_sha256", "code", "reason"}
            or type(document["version"]) is not int or document["version"] != 1
            or document["identity"] != child_identity(rec).to_json()
            or document["candidate_status"] != "completed" or document["level"] != "needs_replan"
            or any(not isinstance(document[k], str) or not re.fullmatch("[0-9a-f]{64}", document[k])
                   for k in ("result_payload_sha256", "artifact_sha256"))
            or not isinstance(document["code"], str) or not re.fullmatch("[a-z_]{1,128}", document["code"])
            or document["code"] in {"evidence_missing", "evidence_unavailable"}
            or not isinstance(document["reason"], str) or not 1 <= len(document["reason"]) <= 1024):
        raise EvidenceError("invalid permanent child rejection receipt")
