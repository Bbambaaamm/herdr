"""One host-approved re-admission after a proven pre-effect activation failure."""
from copy import deepcopy
import re
from .evidence import digest
from .security import InvocationIdentity
from .work_cycle import WorkPlan, require
from .work_planning import bounded, closed, sha

def definition_digest(definition):
    value = deepcopy(definition)
    value["budget"].pop("pre_effect_readmission", None)
    return digest(value)

def bind_pre_effect_readmission(factory, raw, allocation):
    if raw is None:
        factory.pre_effect_readmission = None
        return
    bounded(raw)
    closed(raw, ("version", "source_attempt_sha256", "source_identity",
                 "source_plan_sha256", "source_failed_task_sha256",
                 "authority_reference", "spec_sha256", "base_sha",
                 "definition_sha256", "next_fencing_token"), "host pre-effect re-admission")
    require(type(raw["version"]) is int and raw["version"] == 1,
            "unsupported pre-effect re-admission version")
    for name in ("source_attempt_sha256", "source_plan_sha256", "source_failed_task_sha256",
                 "authority_reference", "spec_sha256", "definition_sha256"):
        sha(raw[name], name)
    require(isinstance(raw["base_sha"], str) and re.fullmatch(r"[0-9a-f]{40}", raw["base_sha"]),
            "exact accepted re-admission base required")
    source = InvocationIdentity.from_dict(raw["source_identity"])
    require(allocation.parent_allocation_id is None and source.consumer == allocation.consumer
            and type(raw["next_fencing_token"]) is int
            and raw["next_fencing_token"] == source.fencing_token + 1,
            "one bounded root re-admission required")
    authority = factory.budget_authority
    with authority._serialized():
        state = authority._state()
        previous = next((event for event in state["attempts"].get(allocation.allocation_id, [])
                         if event["event_sha256"] == raw["source_attempt_sha256"]), None)
        require(previous is not None and previous["identity"] == source.to_json()
                and previous["plan_sha256"] == raw["source_plan_sha256"],
                "original implementation history unavailable")
    approval = deepcopy(raw)
    def approve(*, plan, previous, identity, plan_sha256):
        current = InvocationIdentity.from_dict(identity)
        require(isinstance(plan, WorkPlan) and plan.identity == current and plan.hash == plan_sha256
                and plan.spec_sha256 == approval["spec_sha256"]
                and plan.base_sha == approval["base_sha"],
                "re-admission work contract differs from host approval")
        require(previous["event_sha256"] == approval["source_attempt_sha256"]
                and previous["identity"] == source.to_json()
                and previous["plan_sha256"] == approval["source_plan_sha256"],
                "pre-effect approval cannot authorize another attempt")
        require(current.consumer == source.consumer and current.task_id == source.task_id
                and current.parent_agent_id == source.parent_agent_id
                and current.parent_task_id == source.parent_task_id
                and current.fencing_token == approval["next_fencing_token"]
                and current.run_token != source.run_token,
                "pre-effect approval belongs to another native invocation")
        admitted = getattr(factory, "host_admission", None)
        require(isinstance(admitted, dict) and admitted["spec_sha256"] == approval["spec_sha256"]
                and definition_digest(admitted["definition"]) == approval["definition_sha256"],
                "re-admission host definition changed")
        return {"previous_attempt_sha256": previous["event_sha256"],
                "approval_sha256": digest({"host_approval": approval,
                                           "identity": identity, "plan_sha256": plan_sha256})}
    factory.pre_effect_readmission = approve
