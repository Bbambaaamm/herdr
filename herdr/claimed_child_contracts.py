"""Host-derived child data in the ORIGINAL protected parent work admission.

This module never grants, claims, dispatches, opens a budget or executes a tool.
The protected parent definition is authority; a returned dictionary is not.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import re

from .child_evidence import child_scope_spec
from .child_ownership import ChildOwnership
from .evidence import binding, canonical, digest
from .security import InvocationIdentity
from .work_cycle import require
from .work_planning import bounded, closed

FIELD = "managed_children"


def _claim(task, identity):
    require(isinstance(identity, InvocationIdentity), "actual claimed parent identity required")
    route = task.get("routing")
    require(isinstance(route, dict) and isinstance(route.get("selected_agent"), str)
            and route["selected_agent"], "finalized host route required for managed child data")
    bounded(route)
    coordinator = route["selected_agent"]
    require(isinstance(coordinator, str) and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", coordinator)
            and identity.consumer == "github:" + task["repo"]
            and identity.task_id == task["id"] and identity.run_token == task["run_token"]
            and identity.fencing_token == task["fencing_token"]
            and identity.parent_agent_id == coordinator
            and identity.parent_task_id == "coordinator:" + coordinator,
            "derived child parent claim or route changed")
    session = task.get("execution_session") or {}
    for key in ("launch_identity",):
        if session.get(key) is not None:
            require(InvocationIdentity.from_dict(session[key]) == identity,
                    "derived child authenticated parent changed")
    return {"coordinator": coordinator, "decision": deepcopy(route)}


def _budget(parent_definition, child_definition):
    """Validate the already approved allocation DATA; do not open the authority."""
    from .work_budget_configuration import parse_allocation
    parent = parent_definition.get("budget")
    child = child_definition.get("budget")
    require(isinstance(parent, dict) and isinstance(child, dict), "managed child needs original cumulative budget data")
    pa, ca = parse_allocation(parent["allocation"]), parse_allocation(child["allocation"])
    require(child["version"] == parent["version"] == 1
            and child["ancestors"] == [*parent["ancestors"], parent["allocation"]]
            and ca.parent_allocation_id == pa.allocation_id
            and ca.consumer == pa.consumer and ca.lineage_key == pa.lineage_key
            and ca.authorization_reference == pa.authorization_reference
            and ca.series_plan_sha256 == pa.series_plan_sha256,
            "managed child budget is not the original parent lineage")
    for key, value in asdict(pa.limits).items():
        found = getattr(ca.limits, key)
        require(type(found) is type(value) and (found <= value if type(value) is int else found == value),
                "managed child limit exceeds the parent approval")
    quotes = parent["model_quotes"]
    require(isinstance(quotes, list) and len(quotes) == 1 and child["model_quotes"] == quotes,
            "managed child quote differs from the original parent route")
    quote = quotes[0]
    require(isinstance(quote, dict) and isinstance(quote.get("model"), str), "exact parent model quote required")
    return {"parent_allocation_sha256": pa.hash, "allocation_sha256": ca.hash,
            "model_policy": {"model": quote["model"], "fallback_model": None}}


def derive(definition, task, identity):
    """Pure closed projection from a protected template and an ACTUAL host claim."""
    if FIELD not in definition:
        return None
    require(task.get("child_completion_contracts") is None,
            "static and derived child catalogues cannot be combined")
    template = closed(definition[FIELD], ("version", "children"), "managed child templates")
    require(type(template["version"]) is int and template["version"] == 1
            and isinstance(template["children"], list) and 1 <= len(template["children"]) <= 8,
            "bounded managed child templates required")
    bounded(template)
    route = _claim(task, identity)
    from .taskgraph import TaskGraph
    reviewed = definition.get("reviewed_graph")
    require(isinstance(reviewed, dict), "managed children require original reviewed parent graph")
    graph = TaskGraph.parse_planner_output(reviewed["graph"])
    require(graph.graph_hash() == reviewed["graph_sha256"] and len(graph.nodes) == 1
            and graph.nodes[0].id == task["id"]
            and graph.envelope.max_nodes >= 1 + len(template["children"])
            and graph.envelope.max_fanout >= len(template["children"])
            and graph.envelope.max_depth >= 2,
            "managed child data exceeds the original graph limits")
    parent_root = Path(task["workspace"])
    require(parent_root.is_absolute() and ".." not in parent_root.parts,
            "original parent worktree required")
    parent_tools, parent_permissions = set(task["parent_tools"]), set(task["parent_permissions"])
    require("herdr_delegate_child" in parent_tools and "herdr_verify_work" in parent_tools,
            "managed child tools are not in the original parent scope")
    rows, keys = {}, set()
    for raw in template["children"]:
        item = closed(raw, ("key", "objective", "role", "tools", "permissions", "worktree_identity",
                            "ownership", "completion", "work_definition"), "managed child template")
        key = item["key"]
        require(isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", key) and key not in keys,
                "unique bounded child declaration required")
        keys.add(key)
        require(isinstance(item["objective"], str) and 1 <= len(item["objective"]) <= 1200
                and isinstance(item["role"], str) and 1 <= len(item["role"]) <= 32,
                "bounded child intent required")
        for name, parent in (("tools", parent_tools), ("permissions", parent_permissions)):
            value = item[name]
            require(isinstance(value, list) and value == sorted(set(value))
                    and all(isinstance(x, str) and x for x in value) and set(value) <= parent,
                    "managed child scope exceeds parent approval")
        require("herdr_verify_work" in item["tools"]
                and ("herdr_submit_result" in item["tools"]) == ("herdr_submit_result" in parent_tools),
                "managed child effective result tools differ from canonical delegation")
        try:
            logical, stamp = item["worktree_identity"].rsplit("|", 1)
            device, inode = map(int, stamp.split(":")); child_root = Path(logical)
        except (AttributeError, ValueError, TypeError):
            require(False, "pinned child worktree data required")
        require(child_root.is_absolute() and ".." not in child_root.parts
                and child_root != parent_root and child_root.is_relative_to(parent_root)
                and device >= 0 and inode > 0, "child worktree is outside the parent grant root")
        ownership = ChildOwnership.from_json(item["ownership"])
        require(ownership.integration_owner == identity.task_id, "child ownership differs from parent integration owner")
        data = {"repo": task["repo"], "issue": str(task.get("issue") or ""),
            "parent_task_id": identity.task_id, "parent_agent_id": identity.agent_id,
            "objective": item["objective"], "role": item["role"], "tools": item["tools"],
            "permissions": item["permissions"], "worktree_identity": item["worktree_identity"]}
        spec = child_scope_spec(data, ownership)
        require(spec not in rows, "ambiguous managed child scope")
        completion = item["completion"]
        from .child_completion_policy import validate_contracts
        validate_contracts({"version": 3, "base_sha": definition["base_sha"], "children": {spec: completion}})
        require(completion["kind"] == "coding", "derived child templates support original coding work only")
        work = deepcopy(item["work_definition"])
        require(isinstance(work, dict) and FIELD not in work
                and work.get("base_sha") == definition["base_sha"] and work.get("mode") == "repair"
                and isinstance(work.get("planning"), dict)
                and set(work["planning"]["tools"]) == set(item["tools"])
                and set(work["planning"]["permissions"]) == set(item["permissions"]),
                "child work definition differs from approved scope")
        required={"spec_version","policy_version","base_sha","files","criteria","checks","budget_reference",
                  "mode","baseline_omission_reason","phases","prerequisite_commits","purpose","baseline_policy",
                  "discovery_files","planning","hygiene","budget"}
        closed(work, required | ({"reviewed_graph"} if "reviewed_graph" in work else set()), "approved child work definition")
        budget = _budget(definition, work)
        from .delegation_tool import _arguments
        _arguments({"key":key,"role":item["role"],"objective":item["objective"],
            "prompt":"host-managed-child-preflight","tool":item["tools"],"permission":item["permissions"],
            "cwd":str(child_root),"ownership":ownership.to_json(),**budget["model_policy"]})
        rows[spec] = {"key": key, "scope": data, "ownership_sha256": ownership.hash,
                      "completion": deepcopy(completion), "work_definition": work, **budget}
    from agent_completion_evidence import spec_digest
    return {"version": 1, "parent": binding(task), "spec_sha256": spec_digest(task),
            "identity": identity.to_json(), "route": route, "template_sha256": digest(template), "children": rows}


def retained(admission, task, *, identity=None):
    """Recheck ORIGINAL data only, without filesystem/workspace or budget effects."""
    expected = admission.get(FIELD)
    if FIELD not in admission:
        require(FIELD not in admission["definition"], "derived child admission is missing")
        return None
    require(isinstance(expected, dict), "derived child admission is malformed")
    original = InvocationIdentity.from_dict(expected.get("identity"))
    require(identity is None or identity == original, "derived child parent grant changed")
    actual = derive(admission["definition"], task, original)
    require(canonical(actual) == canonical(expected), "original derived child admission changed")
    return deepcopy(expected)


def contracts(derived, base_sha):
    return {"version": 3, "base_sha": base_sha,
            "children": {key: deepcopy(row["completion"]) for key, row in derived["children"].items()}}
