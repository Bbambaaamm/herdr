"""Host-frozen child completion contracts, consumed by bridge and recovery.

The model may propose a child but cannot author this protected contract or
change its kind, specification, baseline, checks or acceptance criteria.
"""
from __future__ import annotations
import copy
import re
from pathlib import Path
from .child_evidence import ChildCompletionAuthority
from .evidence import (EvidenceError, EvidenceStore, binding, canonical, digest,
                       validate_criteria, validate_plan)
from .scope_evidence import validate_scope_policy

SHA = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = "Bbambaaamm/herdr"
REVIEWER = "chatgpt-codex-connector[bot]"
CHECKS = ["Herdr contract", "GitGuardian Security Checks"]

def require(ok, reason):
    if not ok:
        raise EvidenceError(reason)

def validate_contracts(value):
    require(isinstance(value, dict) and set(value) == {"version", "base_sha", "children"}
        and type(value["version"]) is int and value["version"] in {1, 2, 3}
        and isinstance(value["base_sha"], str) and GIT_SHA.fullmatch(value["base_sha"]),
        "closed preapproved child contracts required")
    children = value["children"]
    require(isinstance(children, dict) and 1 <= len(children) <= 128
        and len(canonical(value)) <= 131072, "child contracts exceed bound")
    for spec, entry in children.items():
        require(isinstance(spec, str) and SHA.fullmatch(spec)
            and isinstance(entry, dict) and isinstance(entry.get("kind"),str)
            and entry["kind"] in {"coding", "research", "review"},
            "child contract specification or kind invalid")
        kind = entry["kind"]
        fields = {"kind", "criteria"} | ({"work_contract_version"} if value["version"] in {2,3} and kind == "coding" else set())
        if value["version"]==3 and kind=="coding":fields.add("work_budget_version")
        require("work_budget_version" not in fields or type(entry.get("work_budget_version")) is int
                and entry["work_budget_version"]==1,"new child cumulative budget required")
        require(set(entry) == fields
            and ("work_contract_version" not in fields or type(entry["work_contract_version"]) is int
                 and entry["work_contract_version"] == 1),
            "child contract has unknown fields")
        if kind != "coding":
            validate_criteria(kind, entry["criteria"])
        elif "criteria" in entry:
            validate_scope_policy(entry["criteria"])

def policy_key(repo, task_id, run_token):
    return digest({"type":"host-child-completion-policy-v1", "repo":repo,
                   "task_id":task_id, "run_token":run_token})

def validate_policy(value):
    names = {"version", "repo", "parent", "parent_spec_hash", "contracts",
             "workspace_root", "environment", "baseline", "policy_hash"}
    require(isinstance(value, dict) and set(value) == names
        and type(value["version"]) is int and value["version"] == 1
        and value["repo"] == REPO
        and isinstance(value["parent_spec_hash"], str) and SHA.fullmatch(value["parent_spec_hash"]),
        "host child policy binding invalid")
    parent = value["parent"]
    require(isinstance(parent, dict) and set(parent) ==
        {"id", "run_token", "idempotency_key", "attempt", "fencing_token"},
        "host child policy parent binding invalid")
    require(binding({"id":parent["id"], "run_token":parent["run_token"],
        "idempotency_key":parent["idempotency_key"], "attempt_id":parent["attempt"],
        "fencing_token":parent["fencing_token"]}) == parent,
        "host child policy parent identity invalid")
    validate_contracts(value["contracts"])
    workspace = value["workspace_root"]
    require(isinstance(workspace, str) and Path(workspace).is_absolute()
        and ".." not in Path(workspace).parts, "host child workspace root invalid")
    environment, baseline = value["environment"], value["baseline"]
    require(isinstance(environment, dict) and set(environment) ==
        {"collector", "ci_workflow_blob_sha", "ci_workflow_id", "github_actions_app_id"}
        and environment["collector"] == "github-api-v1"
        and isinstance(environment["ci_workflow_blob_sha"], str)
        and GIT_SHA.fullmatch(environment["ci_workflow_blob_sha"])
        and type(environment["ci_workflow_id"]) is int and environment["ci_workflow_id"] == 367993725
        and type(environment["github_actions_app_id"]) is int and environment["github_actions_app_id"] == 15368,
        "trusted child validation definition invalid")
    require(isinstance(baseline, list) and len(baseline) <= 2
        and all(isinstance(row,dict) and row.get("name") in CHECKS
            and row.get("head_sha")==value["contracts"]["base_sha"] for row in baseline)
        and len({row["name"] for row in baseline})==len(baseline)
        and len(canonical(value)) <= 262144, "host child policy bound")
    require(value["policy_hash"] == digest({k:v for k,v in value.items() if k != "policy_hash"}),
        "host child policy changed")

def freeze_policy(store, task, *, parent_spec_hash, contracts, environment, baseline):
    require(isinstance(store, EvidenceStore) and task.get("repo") == REPO,
        "host child completion consumer unavailable")
    validate_contracts(contracts)
    value = {"version":1, "repo":task["repo"], "parent":binding(task),
        "parent_spec_hash":parent_spec_hash, "contracts":copy.deepcopy(contracts),
        "workspace_root":task.get("worktree_root") or "/home/agentops/worktrees",
        "environment":copy.deepcopy(environment), "baseline":copy.deepcopy(baseline)}
    value["policy_hash"] = digest(value)
    validate_policy(value)
    store.publish("plan", policy_key(task["repo"], task["id"], task["run_token"]), value)
    return value

def build_authority(store, policy, *, collector):
    require(isinstance(store, EvidenceStore) and callable(collector), "host child authority ports missing")
    validate_policy(policy)
    policy = copy.deepcopy(policy)
    store.protect_from((Path(policy["workspace_root"]),))
    def approve(*, task, spec_sha256):
        parent = policy["parent"]
        require(task.get("repo") == policy["repo"] and task.get("parent_task_id") == parent["id"]
            and task.get("parent_run_token") == parent["run_token"],
            "child differs from frozen parent attempt")
        entry = policy["contracts"]["children"].get(spec_sha256)
        require(entry is not None, "child specification lacks preapproved completion contract")
        kind = entry["kind"]
        plan = {"version":1, "identity":binding(task), "repo":policy["repo"],
            "kind":kind, "spec_hash":spec_sha256, "policy_hash":policy["policy_hash"],
            "base_sha":policy["contracts"]["base_sha"], "workspace_root":policy["workspace_root"],
            "required_checks":list(CHECKS) if kind == "coding" else ["GitGuardian Security Checks"],
            "reviewer":REVIEWER, "environment":copy.deepcopy(policy["environment"])}
        if kind != "coding":
            plan["criteria"] = copy.deepcopy(entry["criteria"])
        elif "criteria" in entry:
            plan["scope_policy"] = copy.deepcopy(entry["criteria"])
        plan["plan_hash"] = digest(plan)
        plan["baseline"] = [copy.deepcopy(row) for row in policy["baseline"]
                            if row.get("name") in plan["required_checks"]]
        validate_plan(plan)
        return plan
    authority = ChildCompletionAuthority(store=store, approve=approve, collector=collector)
    authority.work_contracts = copy.deepcopy(policy["contracts"])
    return authority

def authority_for_parent(store, task, *, parent_spec_hash, collector, parent_identity=None):
    policy = store.read("plan", policy_key(task["repo"], task["id"], task["run_token"]))
    validate_policy(policy)
    require(policy["parent"] == binding(task) and policy["parent_spec_hash"] == parent_spec_hash
        and policy["contracts"] == task.get("child_completion_contracts"),
        "frozen parent child contracts changed")
    if parent_identity is not None:
        require(parent_identity.consumer == "github:"+policy["repo"]
            and parent_identity.task_id == task["id"] and parent_identity.run_token == task["run_token"]
            and parent_identity.fencing_token == task["fencing_token"],
            "child completion differs from authenticated parent")
    return build_authority(store, policy, collector=collector)
