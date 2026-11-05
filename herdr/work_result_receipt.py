"""Private host observation of a sealed local result before the SDK exits."""
from pathlib import Path
import copy
from .evidence import (EvidenceError, EvidenceStore, binding, canonical, digest, invocation_identity,
                       parse_artifact, validate_plan, verify_committed_bytes, verify_invocation_session, read_only_git)
from .policy_launch import validate_policy_evidence
from .result_candidate import completion_candidate
from .workspace import WorkspaceManager

class WorkResultAuthority:
    def __init__(self, store):
        if not isinstance(store, EvidenceStore):
            raise EvidenceError("private host result authority required")
        self.store = store

    def _key(self, task, plan):
        validate_plan(plan)
        if plan["identity"] != binding(task):
            raise EvidenceError("result receipt plan differs from original attempt")
        return digest({"identity": binding(task), "plan_hash": plan["plan_hash"]})

    def capture(self, task, payload, plan, *, cycle, origin_request_key=None):
        """Use a live peer or its original protected pre-oracle observation."""
        from .work_cycle import WorkCycle, WorkPhase
        if (not isinstance(cycle, WorkCycle) or cycle.phase is not WorkPhase.HANDOFF
                or cycle.plan.identity != invocation_identity(task)
                or cycle.plan.spec_sha256 != plan["spec_hash"]
                or cycle.plan.hygiene_sha256 is None):
            raise EvidenceError("result observation requires the host-verified committed work cycle")
        work_plan_sha256 = cycle.plan.hash
        if set(payload) != {"task_id", "run_token", "fencing_token", "idempotency_key", "status", "evidence", "artifact_sha256", "summary"}:
            raise EvidenceError("result observation needs the exact closed SDK slot payload")
        key = self._key(task, plan)
        candidate = completion_candidate(payload, workspace=task["workspace"])
        artifact = parse_artifact(candidate.get("artifact"))
        if (payload.get("status") != "completed" or artifact.task_id != task["id"]
                or artifact.attempt != binding(task)["attempt"] or artifact.base_sha != plan["base_sha"]):
            raise EvidenceError("result receipt needs the exact completed local artifact")
        root = Path(plan["workspace_root"])
        workspace = Path(task["workspace"])
        if not workspace.is_absolute() or workspace == root or not workspace.is_relative_to(root):
            raise EvidenceError("result receipt worktree differs from frozen root")
        if canonical(cycle.artifact) != canonical(artifact.to_json()):
            raise EvidenceError("result observation differs from host work artifact")
        expected = {"task_id":task["id"], "run_token":task["run_token"],
                    "fencing_token":task["fencing_token"], "idempotency_key":task["idempotency_key"]}
        if any(payload.get(name) != value for name,value in expected.items()):
            raise EvidenceError("result observation differs from bound result inode payload")
        self.store.protect_from((root, workspace))
        origin = None
        if origin_request_key is None:
            before = verify_invocation_session(task)
        else:
            request = self.store.read("work-handoff-intent", origin_request_key)
            request_id = request.get("request")
            if (request.get("version") != 1 or request.get("identity") != cycle.plan.identity.to_json()
                    or request.get("work_plan") != cycle.plan.hash
                    or (cycle.verification_requests.get(request_id) or {}).get("status") != "pass"
                    or canonical(request.get("launch_policy")) != canonical(task["execution_session"]["invocation_policy"])):
                raise EvidenceError("original authenticated work request is missing or changed")
            before = validate_policy_evidence(request["launch_policy"], identity=cycle.plan.identity)
            origin = {"request_key":origin_request_key, "request_sha256":digest(request), "request_id":request_id}
        if before["grant_sha256"] != cycle.plan.grant_sha256:
            raise EvidenceError("result observation grant differs from work cycle")
        manager = WorkspaceManager(workspace, git=read_only_git(workspace), worktrees_dir=root,
                                   artifacts_dir=self.store.root/"receipt-artifacts")
        manager.verify(artifact, workspace)
        verify_committed_bytes(artifact, workspace, manager.git)
        after = verify_invocation_session(task) if origin is None else self.store.read("work-handoff-intent", origin_request_key)["launch_policy"]
        if canonical(before) != canonical(after):
            raise EvidenceError("physical invocation changed during result observation")
        receipt = {"version": 1, "identity": binding(task), "invocation": invocation_identity(task).to_json(),
                   "plan_hash": plan["plan_hash"], "spec_hash": plan["spec_hash"], "policy_hash": plan["policy_hash"],
                   "work_plan_sha256": work_plan_sha256, "result_payload_sha256": digest(payload),
                   "artifact": artifact.to_json(), "workspace": str(workspace),
                   "launch_policy": before, "level": "verified_local_artifact"}
        if origin is not None:
            receipt["origin_request"] = origin
        return self.store.publish("work-result", key, receipt)

    def verifier(self, task, payload, plan, *, work_plan_sha256):
        """Read the same immutable observation; it grants no new invocation."""
        key = self._key(task, plan)
        receipt = self.store.read("work-result", key)
        candidate = completion_candidate(payload, workspace=task["workspace"])
        artifact = parse_artifact(candidate.get("artifact"))
        expected = {"version": 1, "identity": binding(task), "invocation": invocation_identity(task).to_json(),
                    "plan_hash": plan["plan_hash"], "spec_hash": plan["spec_hash"], "policy_hash": plan["policy_hash"],
                    "work_plan_sha256": work_plan_sha256, "result_payload_sha256": digest(payload),
                    "artifact": artifact.to_json(), "workspace": str(task["workspace"]),
                    "launch_policy": (task["execution_session"] or {}).get("invocation_policy"),
                    "level": "verified_local_artifact"}
        if "origin_request" in receipt:
            origin = receipt["origin_request"]
            if not isinstance(origin, dict) or set(origin) != {"request_key","request_sha256","request_id"}:
                raise EvidenceError("original host work observation is invalid")
            request = self.store.read("work-handoff-intent", origin["request_key"])
            if (digest(request) != origin["request_sha256"] or request.get("request") != origin["request_id"]
                    or request.get("identity") != expected["invocation"] or request.get("work_plan") != work_plan_sha256
                    or canonical(request.get("launch_policy")) != canonical(expected["launch_policy"])):
                raise EvidenceError("original host work observation changed")
            expected["origin_request"] = origin
        if canonical(receipt) != canonical(expected):
            raise EvidenceError("original physical result observation changed")
        policy = validate_policy_evidence(receipt["launch_policy"], identity=invocation_identity(task))
        original_identity = copy.deepcopy(expected["identity"])
        def verify(current):
            if binding(current) != original_identity or canonical(current["execution_session"]["invocation_policy"]) != canonical(policy):
                raise EvidenceError("result observation was reused for another invocation")
            return policy
        return verify
