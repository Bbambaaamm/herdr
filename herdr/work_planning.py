"""Immutable planning data. Admission and evidence remain host authorities."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .evidence import canonical, digest
from .security import InvocationIdentity, SecurityGrant
from .work_cycle import IntentInfoRequired, require, relative

SHA = re.compile(r"^[0-9a-f]{64}$")
GIT = re.compile(r"^[0-9a-f]{40}$")


def closed(value, keys, name):
    require(isinstance(value, dict) and set(value) == set(keys), name + " schema invalid")
    return value


def strings(value, name, *, maximum=128, width=2048, empty=True):
    require(isinstance(value, (list, tuple)) and len(value) <= maximum
            and (empty or bool(value))
            and all(isinstance(x, str) and 0 < len(x) <= width and "\0" not in x
                    for x in value) and len(set(value)) == len(value), name + " invalid")
    return tuple(value)


def sha(value, name):
    require(isinstance(value, str) and SHA.fullmatch(value), name + " digest invalid")
    return value


def bounded(value):
    # Bound depth/nodes before canonical serialization, including hostile model data.
    nodes = 0
    def visit(item, depth=0):
        nonlocal nodes
        nodes += 1
        require(nodes <= 12000 and depth <= 16, "planning data exceeds bound")
        require(item is None or type(item) in (str, int, bool, list, tuple, dict),
                "planning data is not closed JSON")
        if isinstance(item, dict):
            require(all(isinstance(k, str) and len(k) <= 128 for k in item), "planning key invalid")
            for child in item.values():
                visit(child, depth + 1)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child, depth + 1)
        elif type(item) is int:
            require(-(2**63) <= item < 2**63, "planning integer exceeds bound")
        elif isinstance(item, str):
            require(len(item) <= 8192 and "\0" not in item, "planning text exceeds bound")
    visit(value)
    raw = canonical(value)
    require(len(raw) <= 131072, "planning artifact exceeds bound")
    return raw


class DiscoveryRecord:
    """Host-observed targeted inventory; uninspected behavior stays UNKNOWN."""
    __slots__ = ("_raw",)

    def __init__(self, value):
        bounded(value)
        closed(value, ("version", "identity", "base_sha", "inspected_files", "symbols",
                       "facts", "evidence_refs", "unknowns", "expansion_reason"), "discovery")
        require(type(value["version"]) is int and value["version"] == 1, "discovery version invalid")
        InvocationIdentity.from_dict(value["identity"])
        require(isinstance(value["base_sha"], str) and GIT.fullmatch(value["base_sha"]),
                "discovery needs exact base")
        inventory = value["inspected_files"]
        require(isinstance(inventory, dict) and 1 <= len(inventory) <= 128,
                "targeted discovery inventory required")
        for path, content_hash in inventory.items():
            relative(path); sha(content_hash, "inspected file")
        require(isinstance(value["symbols"], dict) and set(value["symbols"]) <= set(inventory),
                "discovery symbols escaped inspected files")
        for names in value["symbols"].values():
            strings(names, "inspected symbols", width=256)
        strings(value["facts"], "observed facts", width=2048)
        strings(value["evidence_refs"], "discovery evidence", empty=False, width=1024)
        strings(value["unknowns"], "discovery unknowns")
        reason = value["expansion_reason"]
        require(reason is None or isinstance(reason, str) and 0 < len(reason) <= 512,
                "discovery expansion needs a reason")
        self._raw = bounded(value)

    def to_json(self):
        return json.loads(self._raw)

    @property
    def hash(self):
        return digest(self.to_json())


class PlanArtifact:
    """Versioned outcome contract, not a tool sequence or executable runbook."""
    __slots__ = ("_raw",)

    def __init__(self, value):
        bounded(value)
        closed(value, ("version", "identity", "spec_sha256", "base_sha", "discovery",
                       "goal", "allowed_files", "tools", "permissions", "constraints",
                       "assumptions", "uncertainties", "acceptance", "verification",
                       "expected_artifact", "stop_condition", "team", "runbook",
                       "orientation", "prompt_plan", "clarification", "decomposition"), "plan artifact")
        require(type(value["version"]) is int and value["version"] == 1, "plan artifact version invalid")
        identity = InvocationIdentity.from_dict(value["identity"])
        sha(value["spec_sha256"], "plan spec")
        require(isinstance(value["base_sha"], str) and GIT.fullmatch(value["base_sha"]),
                "plan needs exact base")
        discovery = DiscoveryRecord(value["discovery"])
        require(discovery.to_json()["identity"] == identity.to_json()
                and discovery.to_json()["base_sha"] == value["base_sha"], "discovery binding changed")
        for key in ("goal", "expected_artifact", "stop_condition"):
            require(isinstance(value[key], str) and 0 < len(value[key]) <= 4096,
                    key + " required")
        for key in ("constraints", "assumptions", "uncertainties", "tools", "permissions"):
            strings(value[key], key, width=2048)
        files = strings(value["allowed_files"], "planned files", maximum=256, width=1024, empty=False)
        for path in files:
            relative(path)
        criteria = strings(value["acceptance"], "planned acceptance", width=64, empty=False)
        oracle = closed(value["verification"],
                        ("dimensions", "prebuild_review_required", "accepted_review_ref"), "verification contract")
        require(type(oracle["prebuild_review_required"]) is bool, "review policy must be explicit")
        if oracle["accepted_review_ref"] is not None:
            sha(oracle["accepted_review_ref"], "accepted prebuild evidence")
        require(not oracle["prebuild_review_required"] or oracle["accepted_review_ref"] is not None,
                "independent prebuild evidence required")
        dimensions = oracle["dimensions"]
        require(isinstance(dimensions, list) and 1 <= len(dimensions) <= 32,
                "bounded verification dimensions required")
        ids = set()
        for dimension in dimensions:
            closed(dimension, ("id", "hard", "check_ids"), "oracle dimension")
            require(isinstance(dimension["id"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", dimension["id"])
                    and dimension["id"] not in ids and type(dimension["hard"]) is bool,
                    "oracle dimension invalid")
            ids.add(dimension["id"])
            strings(dimension["check_ids"], "dimension checks", width=64, empty=False)
        require(any(x["hard"] for x in dimensions), "hard acceptance minimum required")
        self._team(value["team"], files, value["tools"], value["permissions"])
        if value["runbook"] is not None:
            runbook = closed(value["runbook"], ("profile", "version", "sha256", "advisory"), "runbook")
            require(runbook["advisory"] is True and isinstance(runbook["profile"], str)
                    and 0 < len(runbook["profile"]) <= 64 and isinstance(runbook["version"], str)
                    and 0 < len(runbook["version"]) <= 64, "runbook cannot confer authority")
            sha(runbook["sha256"], "runbook")
        if value["orientation"] is not None:
            orientation = closed(value["orientation"], ("inspected_files", "facts", "uninspected_areas", "unknowns", "read_only"), "orientation")
            require(orientation["read_only"] is True, "orientation cannot write")
            require(set(strings(orientation["inspected_files"], "orientation files", width=1024))
                    <= set(discovery.to_json()["inspected_files"]), "orientation claims uninspected files")
            for key in ("facts", "uninspected_areas", "unknowns"):
                strings(orientation[key], "orientation " + key)
        if value["prompt_plan"] is not None:
            prompt = closed(value["prompt_plan"], ("version", "sha256", "spec_sha256", "acceptance_sha256"), "prompt reference")
            require(isinstance(prompt["version"], str) and 0 < len(prompt["version"]) <= 64,
                    "prompt version required")
            sha(prompt["sha256"], "prompt plan")
            require(prompt["spec_sha256"] == value["spec_sha256"]
                    and prompt["acceptance_sha256"] == digest(list(criteria)), "stale prompt contract")
        clarification = closed(value["clarification"], ("status", "reason", "material"), "clarification")
        require(clarification["status"] in {"resolved", "bounded_assumption", "info_required"}
                and type(clarification["material"]) is bool and isinstance(clarification["reason"], str)
                and 0 < len(clarification["reason"]) <= 2048, "typed clarification required")
        require(clarification["status"] != "bounded_assumption" or
                not clarification["material"] and bool(value["assumptions"]), "material ambiguity cannot be assumed")
        if clarification["status"] == "info_required":
            raise IntentInfoRequired("intent_info_required: " + clarification["reason"])
        if value["decomposition"] is not None:
            decomposition = closed(value["decomposition"], ("reason", "new_evidence_ref", "spec_sha256", "budget_reference"), "decomposition")
            require(isinstance(decomposition["reason"], str) and 0 < len(decomposition["reason"]) <= 512,
                    "decomposition reason required")
            sha(decomposition["new_evidence_ref"], "decomposition evidence")
            require(decomposition["spec_sha256"] == value["spec_sha256"]
                    and decomposition["budget_reference"] == value["team"]["budget_reference"],
                    "decomposition cannot renew objective or budget")
        self._raw = bounded(value)

    @staticmethod
    def _team(team, files, tools, permissions):
        closed(team, ("topology", "nodes", "edges", "integration_owner", "concurrency", "budget_reference"), "team plan")
        require(team["topology"] in {"SINGLE", "SEQUENTIAL", "PARALLEL", "ORCHESTRATOR_WORKERS", "GENERATOR_VERIFIER"},
                "unsupported topology")
        require(type(team["concurrency"]) is int and 1 <= team["concurrency"] <= 32, "finite team concurrency required")
        sha(team["budget_reference"], "shared team budget")
        nodes = team["nodes"]
        require(isinstance(nodes, list) and 1 <= len(nodes) <= 32, "bounded team nodes required")
        node_ids, writes = set(), {}
        for node in nodes:
            closed(node, ("id", "role_ref", "write_files", "decision_scope", "tools", "permissions"), "team node")
            require(isinstance(node["id"], str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", node["id"])
                    and node["id"] not in node_ids, "team node identity invalid")
            node_ids.add(node["id"])
            if node["role_ref"] is not None:
                sha(node["role_ref"], "role profile")
            paths = strings(node["write_files"], "node write files", maximum=256, width=1024)
            require(set(paths) <= set(files) and set(strings(node["tools"], "node tools")) <= set(tools)
                    and set(strings(node["permissions"], "node permissions")) <= set(permissions),
                    "team node escaped plan authority")
            strings(node["decision_scope"], "decision scope", width=256)
            writes[node["id"]] = set(paths)
        require(team["integration_owner"] in node_ids and team["concurrency"] <= len(nodes),
                "explicit integration owner and bounded concurrency required")
        if team["topology"] == "SINGLE":
            require(len(nodes) == 1 and team["concurrency"] == 1 and team["edges"] == [],
                    "simple task cannot silently fan out")
        if team["topology"] == "SEQUENTIAL":
            require(team["concurrency"] == 1, "sequential work cannot run concurrently")
        if team["concurrency"] > 1:
            ordered = list(writes)
            require(all(not writes[a] & writes[b] for i, a in enumerate(ordered) for b in ordered[i+1:]),
                    "parallel writers overlap")
        edges = team["edges"]
        require(isinstance(edges, list) and len(edges) <= 128, "bounded handoff edges required")
        graph = {node: [] for node in node_ids}
        seen = set()
        for edge in edges:
            closed(edge, ("from", "to", "handoff_schema", "gate_refs"), "handoff edge")
            require(edge["from"] in node_ids and edge["to"] in node_ids and edge["from"] != edge["to"]
                    and (edge["from"], edge["to"]) not in seen and edge["handoff_schema"] == "herdr-handoff-1",
                    "handoff edge invalid")
            strings(edge["gate_refs"], "edge gates", width=128)
            seen.add((edge["from"], edge["to"])); graph[edge["from"]].append(edge["to"])
        visiting, visited = set(), set()
        def walk(node):
            require(node not in visiting, "team dependency cycle")
            if node in visited:
                return
            visiting.add(node)
            for child in graph[node]:
                walk(child)
            visiting.remove(node); visited.add(node)
        for node in node_ids:
            walk(node)

    def to_json(self):
        return json.loads(self._raw)

    @property
    def hash(self):
        return digest(self.to_json())

    @property
    def hard_check_ids(self):
        return frozenset(check for dimension in self.to_json()["verification"]["dimensions"]
                         if dimension["hard"] for check in dimension["check_ids"])

    def require_binding(self, plan, grant=None):
        value = self.to_json()
        require(value["identity"] == plan.identity.to_json() and value["spec_sha256"] == plan.spec_sha256
                and value["base_sha"] == plan.base_sha and tuple(value["acceptance"]) == plan.criteria
                and set(value["allowed_files"]) == {x.path for x in plan.files}
                and value["team"]["budget_reference"] == plan.budget_reference, "planning/work binding mismatch")
        checks = {x.id for x in plan.checks}
        require({check for dimension in value["verification"]["dimensions"] for check in dimension["check_ids"]} == checks,
                "oracle changed frozen checks")
        require({criterion for check in plan.checks if check.id in self.hard_check_ids for criterion in check.criterion_ids}
                == set(plan.criteria), "hard minima do not cover acceptance")
        if grant is not None:
            require(isinstance(grant, SecurityGrant) and grant.identity == plan.identity and grant.hash == plan.grant_sha256
                    and grant.is_active() and set(value["tools"]) <= set(grant.scope.tools)
                    and set(value["permissions"]) <= set(grant.scope.permissions), "plan exceeds current grant")
