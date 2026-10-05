"""Exact local handoff, captured by the host before the SDK can exit."""
import copy
from pathlib import Path
from .evidence import EvidenceStore, EvidenceMissing, canonical, digest, verify_invocation_session
from .security import InvocationIdentity
from .work_cycle import require
from .work_hygiene import HostLocalCommitter
from .work_result_receipt import WorkResultAuthority
from .result_submission import ResultSlot, payload_for_slot
from .scope_evidence import bounded_json, verify_scope_self_check

class HostWorkHandoff:
    def __init__(self, *, identity, task, completion_plan, store, slot, committer):
        require(isinstance(identity, InvocationIdentity) and isinstance(store, EvidenceStore)
                and isinstance(slot, ResultSlot) and isinstance(committer, HostLocalCommitter),
                "protected host handoff authority required")
        self.identity, self.task, self.plan = identity, task, copy.deepcopy(completion_plan)
        self.store, self.slot, self.committer = store, slot, committer
        self.result_authority = WorkResultAuthority(store)
        store.protect_from((Path(task["workspace"]), Path(completion_plan["workspace_root"])))

    def _key(self, cycle, request_id):
        return digest({"identity": self.identity.to_json(), "work_plan": cycle.plan.hash, "request": request_id})

    def prepare_request(self, cycle, request_id, handoff):
        require(cycle.plan.identity == self.identity, "work handoff identity changed")
        require(sum(check.timeout_seconds for check in cycle.plan.checks) + self.committer.policy.timeout_seconds <= 900,
                "verification and hygiene exceed one bounded host request")
        key = self._key(cycle, request_id)
        try:
            old = self.store.read("work-handoff-intent", key)
        except EvidenceMissing:
            old = None
        if old is not None:
            require(handoff is None or canonical(old["handoff"]) == canonical(handoff),
                    "immutable handoff declaration changed")
            return old["handoff"]
        require(isinstance(handoff, dict) and set(handoff) <= {"pr_number", "scope_claim"}
                and "pr_number" in handoff and (handoff["pr_number"] is None
                    or type(handoff["pr_number"]) is int and 1 <= handoff["pr_number"] <= 2147483647),
                "closed local handoff declaration required")
        bounded_json(handoff)
        require(len(canonical(handoff)) <= 4096, "handoff declaration exceeds transport bound")
        scope = handoff.get("scope_claim")
        require((scope is not None) == ("scope_policy" in self.plan),
                "frozen scope claim is missing or unsolicited")
        if scope is not None:
            require(isinstance(scope, dict) and not set(scope) & {"spec_sha256", "artifact_sha256"},
                    "host binds scope claim to the exact sealed artifact")
        if scope is not None:
            from dataclasses import replace
            snapshot = cycle.verify_scope()
            changed = tuple(sorted(name for name in set(snapshot)|set(cycle.baseline)
                                   if snapshot.get(name) != cycle.baseline.get(name)))
            # This is declaration validation against an unsealed draft. The
            # returned scope proof is discarded; only the later sealed artifact
            # supplies the hash used in actual acceptance evidence.
            draft = replace(self.committer.draft, changed_files=changed)
            verify_scope_self_check(self.plan, draft, {**scope, "spec_sha256":self.plan["spec_hash"],
                                                     "artifact_sha256":draft.result_sha})
        from .work_cycle import WorkPhase
        require(cycle.phase is WorkPhase.WORK and not cycle.verified_checks,
                "new handoff intent must precede host verification")
        launch_policy = verify_invocation_session(self.task)
        require(launch_policy["grant_sha256"] == cycle.plan.grant_sha256, "work request grant changed")
        intent = {"version": 1, "identity": self.identity.to_json(),
                  "work_plan": cycle.plan.hash, "request": request_id, "handoff": handoff,
                  "launch_policy": launch_policy}
        self.store.publish("work-handoff-intent", key, intent)
        return handoff

    def complete(self, cycle, request_id, outcome):
        if outcome["status"] != "pass":
            return outcome
        key = self._key(cycle, request_id)
        intent = self.store.read("work-handoff-intent", key)
        declaration = intent["handoff"]
        artifact = self.committer(cycle)
        candidate = {"version": 2, "artifact": artifact.to_json(),
                     "pr_number": declaration["pr_number"]}
        if "scope_claim" in declaration:
            report = {**declaration["scope_claim"], "spec_sha256": self.plan["spec_hash"],
                      "artifact_sha256": artifact.result_sha}
            verify_scope_self_check(self.plan, artifact, report)
            candidate["scope_self_check"] = report
        raw = {"status": "completed", "evidence": [{"herdr_completion": candidate}],
               "summary": "Frozen host checks passed; exact local artifact awaits independent CI/review and integration."}
        require(len(canonical(raw)) <= 6144, "sealed result exceeds bounded work response")
        payload = payload_for_slot(self.identity, self.slot, raw)
        receipt = self.result_authority.capture(self.task, payload, self.plan, cycle=cycle, origin_request_key=key)
        result = {**outcome, "next_action": "submit_exact_local_handoff",
                  "submission": raw, "local_receipt_sha256": receipt}
        require(len(canonical(result)) <= 8191, "work handoff response exceeds bound")
        return result

    def deliver(self, cycle, request_id):
        """Resume the exact host-directed handoff without any model or hook retry."""
        from .result_submission import publish_slot_payload
        outcome = cycle.verification_requests.get(request_id)
        require(outcome is not None and outcome["status"] == "pass", "original verification must be proven")
        response = self.complete(cycle, request_id, outcome)
        payload = payload_for_slot(self.identity, self.slot, response["submission"])
        self.result_authority.verifier(self.task, payload, self.plan, work_plan_sha256=cycle.plan.hash)(self.task)
        publish_slot_payload(self.identity, self.slot, payload)
        return payload
