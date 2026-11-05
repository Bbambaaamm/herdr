"""Bounded child handoff data; never a grant or execution authority."""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from .child_ownership import ChildOwnership, FrozenContract, OwnershipError, name, sha, require
from .context import SecretRedactor
from .security import InvocationIdentity


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def child_spec_digest(rec):
    spec = {"repo": rec.repo, "issue": rec.issue, "parent_task_id": rec.parent_task_id,
            "parent_agent_id": rec.parent_agent_id, "objective": rec.node.objective,
            "role": rec.node.role, "tools": list(rec.node.tools),
            "permissions": list(rec.node.permissions), "worktree_identity": rec.worktree_identity}
    if rec.ownership is not None:
        spec["ownership_sha256"] = rec.ownership.hash
    return digest(spec)


def child_identity(rec):
    return InvocationIdentity("github:" + rec.repo, rec.agent_id, rec.parent_agent_id,
                              rec.parent_task_id, rec.id, rec.run_token, rec.fencing_token)


@dataclass(frozen=True)
class HandoffRef:
    ref: str
    sha256: str
    def __post_init__(self):
        name(self.ref, 768)
        sha(self.sha256)
    def to_json(self):
        return {"ref": self.ref, "sha256": self.sha256}
    @classmethod
    def from_json(cls, value):
        require(isinstance(value, dict) and set(value) == {"ref", "sha256"}, "handoff_ref_schema")
        return cls(**value)


@dataclass(frozen=True)
class HandoffEnvelope:
    identity: InvocationIdentity
    spec_sha256: str
    base_sha256: str | None
    from_role: str
    to_role: str
    current_state: str
    artifact_refs: tuple[HandoffRef, ...]
    evidence_refs: tuple[HandoffRef, ...]
    accepted_decisions: tuple[FrozenContract, ...]
    ownership: ChildOwnership | None
    assumptions: tuple[str, ...]
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    policy_refs: tuple[str, ...]
    remaining_criteria: tuple[str, ...]
    risks_blockers: tuple[str, ...]
    next_action: str
    not_owned: tuple[str, ...]
    out_of_scope: tuple[str, ...]

    def __post_init__(self):
        require(isinstance(self.identity, InvocationIdentity), "handoff_identity")
        sha(self.spec_sha256)
        if self.base_sha256 is not None:
            sha(self.base_sha256)
        for value in (self.from_role, self.to_role):
            name(value, 128)
        require(self.current_state in {"PARTIAL", "COMPLETE", "BLOCKED", "CONFLICT", "UNKNOWN"},
                "handoff_state")
        for field in ("artifact_refs", "evidence_refs", "accepted_decisions"):
            values = getattr(self, field)
            typ = FrozenContract if field == "accepted_decisions" else HandoffRef
            require(isinstance(values, tuple) and len(values) <= 32 and all(isinstance(v, typ) for v in values)
                    and len(set(values)) == len(values), "handoff_reference_bound")
        require(len({v.key for v in self.accepted_decisions}) == len(self.accepted_decisions),
                "handoff_decision_conflict")
        require(self.ownership is None or isinstance(self.ownership, ChildOwnership), "handoff_ownership")
        for field in ("assumptions", "unknowns", "contradictions", "policy_refs", "remaining_criteria",
                      "risks_blockers", "not_owned", "out_of_scope"):
            values = getattr(self, field)
            require(isinstance(values, tuple) and len(values) <= 32, "handoff_text_bound")
            for value in values:
                require(isinstance(value, str) and 0 < len(value.encode()) <= 512
                        and SecretRedactor().redact(value) == value
                        and not any(ord(c) < 32 for c in value), "handoff_safe_text")
        require(isinstance(self.next_action, str) and 0 < len(self.next_action.encode()) <= 512
                and SecretRedactor().redact(self.next_action) == self.next_action
                and not any(ord(c) < 32 for c in self.next_action), "handoff_next_action")
        require(not self.contradictions or self.current_state in {"CONFLICT", "UNKNOWN"},
                "handoff_unresolved_contradiction")
        require(self.current_state != "COMPLETE" or not (
                self.remaining_criteria or self.contradictions or self.unknowns),
                "handoff_incomplete_claim")
        require(len(json.dumps(self.to_json(), sort_keys=True).encode()) <= 32768, "handoff_bytes")

    def to_json(self):
        from dataclasses import asdict
        value = {key: list(getattr(self, key)) for key in (
            "assumptions", "unknowns", "contradictions", "policy_refs", "remaining_criteria",
            "risks_blockers", "not_owned", "out_of_scope")}
        value.update(version=1, identity=self.identity.to_json(), spec_sha256=self.spec_sha256,
            base_sha256=self.base_sha256, from_role=self.from_role, to_role=self.to_role,
            current_state=self.current_state, artifact_refs=[x.to_json() for x in self.artifact_refs],
            evidence_refs=[x.to_json() for x in self.evidence_refs],
            accepted_decisions=[asdict(x) for x in self.accepted_decisions],
            ownership=self.ownership.to_json() if self.ownership else None, next_action=self.next_action)
        return value

    @classmethod
    def from_json(cls, value):
        require(isinstance(value, dict) and set(value) == {"version", *cls.__dataclass_fields__}
                and type(value["version"]) is int and value["version"] == 1, "handoff_closed_schema")
        fields = {k: v for k, v in value.items() if k != "version"}
        fields["identity"] = InvocationIdentity.from_dict(fields["identity"])
        fields["ownership"] = (ChildOwnership.from_json(fields["ownership"])
                               if fields["ownership"] is not None else None)
        for key, parser in (("artifact_refs", HandoffRef.from_json), ("evidence_refs", HandoffRef.from_json),
                            ("accepted_decisions", lambda x: FrozenContract(**x))):
            require(isinstance(fields[key], list) and len(fields[key]) <= 32, "handoff_reference_bound")
            fields[key] = tuple(parser(x) for x in fields[key])
        for key in ("assumptions", "unknowns", "contradictions", "policy_refs", "remaining_criteria",
                    "risks_blockers", "not_owned", "out_of_scope"):
            require(isinstance(fields[key], list) and len(fields[key]) <= 32, "handoff_text_bound")
            fields[key] = tuple(fields[key])
        return cls(**fields)

    def require_binding(self, rec, *, base_sha256=None):
        require(self.identity == child_identity(rec) and self.spec_sha256 == child_spec_digest(rec)
                and self.base_sha256 == base_sha256 and self.from_role == rec.node.role
                and self.ownership == rec.ownership, "handoff_stale_binding")
        expected = HandoffRef(f"scheduler-result:{rec.id}:{rec.run_token}", rec.result_artifact_sha256)
        require(expected in self.artifact_refs and expected in self.evidence_refs, "handoff_result_binding")
    def require_current(self, rec, *, base_sha256=None, registry=None):
        self.require_binding(rec,base_sha256=base_sha256)
        for ref in self.accepted_decisions:
            require(registry is not None, "handoff_decision_authority_missing")
            row = registry.snapshot()["contracts"].get(registry.contract_key(self.identity.consumer, ref.key))
            from dataclasses import asdict
            require(row is not None and row["contract"] == asdict(ref), "handoff_decision_unverified")
        if rec.ownership is not None:
            require(registry is not None, "handoff_ownership_authority_missing")
            verifier=(registry.require_result_current if rec.cleanup_complete else registry.require_current)
            verifier(rec.ownership_reservation, self.identity)

    @classmethod
    def submitted_child(cls, rec, *, to_role="parent", evidence=None):
        from dataclasses import replace
        ref = HandoffRef(f"scheduler-result:{rec.id}:{rec.run_token}", rec.result_artifact_sha256)
        envelope = cls(child_identity(rec), child_spec_digest(rec), None, rec.node.role, to_role,
            "UNKNOWN" if rec.result_status == "completed" else "BLOCKED", (ref,), (ref,), (),
            rec.ownership, (), ("semantic_acceptance", "git_base"), (),
            ("consumer-profile:" + rec.policy_profile,), ("host_validation",),
            (() if rec.result_status == "completed" else ("child_result_" + rec.result_status,)),
            "host_verify_then_parent_synthesis", (), ())
        details = [item["handoff_details"] for item in (evidence or [])
                   if isinstance(item,dict) and "handoff_details" in item]
        require(len(details)<=1,"handoff_details_ambiguous")
        if not details:
            return envelope
        raw=details[0]
        allowed={"assumptions","unknowns","contradictions","remaining_criteria",
                 "risks_blockers","not_owned","out_of_scope","next_action"}
        require(isinstance(raw,dict) and set(raw)<=allowed,"handoff_details_closed_schema")
        updates={}
        for key,value in raw.items():
            if key=="next_action":
                updates[key]=value
            else:
                require(isinstance(value,list) and len(value)<=32,"handoff_text_bound")
                updates[key]=tuple(value)
        updates["unknowns"]=tuple(dict.fromkeys((*envelope.unknowns,*updates.get("unknowns",()))))
        if updates.get("contradictions"):
            updates["current_state"]="CONFLICT"
        elif updates.get("remaining_criteria"):
            updates["current_state"]="PARTIAL"
        return replace(envelope,**updates)
