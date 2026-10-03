"""Host-only GitHub collector and durable worker completion adapter."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agent_platform_dashboard.production_sources import command as github_command
from herdr.evidence import (EvidenceError, EvidenceMissing, EvidenceUnavailable,
                            EvidenceStore, accept_artifact, binding, digest, validate_criteria)

GH = Path("/home/agentops/.local/bin/gh")
BOT = "chatgpt-codex-connector[bot]"
# These identities are verified GitHub application IDs, not result producer names.
CHECK_APPS = {"Herdr contract": 15368, "GitGuardian Security Checks": 46505}
POLICY = {"version": "worker-completion-v1", "repo": "Bbambaaamm/herdr",
          "checks": CHECK_APPS, "reviewer": BOT, "workflow": ".github/workflows/ci.yml", "workflow_id": 367993725}


def github(path: str):
    try:
        output = github_command([str(GH), "api", "--hostname", "github.com", "--paginate", path],
                                timeout=45, limit=8_000_000, env=os.environ.copy()).decode("utf-8")
        decoder = json.JSONDecoder()
        pages = []
        remaining = output.strip()
        while remaining:
            value, end = decoder.raw_decode(remaining)
            pages.append(value)
            remaining = remaining[end:].strip()
        if not isinstance(pages, list) or not pages:
            raise EvidenceUnavailable("GitHub returned no evidence")
        if not all(isinstance(page, (list, dict)) for page in pages):
            raise EvidenceUnavailable("invalid GitHub evidence shape")
        if isinstance(pages[0], list):
            return [row for page in pages for row in page]
        if len(pages) == 1:
            return pages[0]
        if all(isinstance(p, dict) and "check_runs" in p for p in pages):
            return {"check_runs": [c for p in pages for c in p["check_runs"]]}
        raise EvidenceUnavailable("unsupported GitHub evidence pagination")
    except (OSError, subprocess.SubprocessError, ValueError, TypeError) as exc:
        raise EvidenceUnavailable("GitHub evidence collection failed") from exc


def _collect_checks(repo: str, sha: str, required: list[str], *, require_success: bool):
    raw = github(f"repos/{repo}/commits/{sha}/check-runs?per_page=100")
    rows = raw.get("check_runs")
    if not isinstance(rows, list):
        raise EvidenceUnavailable("check runs are unavailable")
    selected = {}
    for name in required:
        candidates = [r for r in rows if r.get("name") == name
                      and r.get("head_sha") == sha
                      and r.get("app", {}).get("id") == CHECK_APPS[name]]
        if not candidates:
            if require_success:
                raise EvidenceMissing(f"required check is missing: {name}")
            selected[name] = {"name": name, "head_sha": sha, "status": "missing"}
            continue
        row = max(candidates, key=lambda r: r["id"])
        if require_success and (row.get("status") != "completed"
                                or row.get("conclusion") != "success"):
            raise EvidenceMissing(f"required check has not passed: {name}")
        selected[name] = {k: row.get(k) for k in
                          ("id", "name", "head_sha", "status", "conclusion", "details_url")}
        selected[name]["app_id"] = row["app"]["id"]
    return selected


def collect_checks(repo: str, sha: str, required: list[str], *, require_success: bool):
    try:
        return _collect_checks(repo, sha, required, require_success=require_success)
    except EvidenceError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise EvidenceUnavailable("check run data is invalid") from exc


def workflow_blob(repo: str, sha: str) -> str:
    raw = github(f"repos/{repo}/contents/{POLICY['workflow']}?ref={sha}")
    blob = raw.get("sha") if isinstance(raw, dict) else None
    if not isinstance(blob, str) or not re.fullmatch(r"[0-9a-f]{40}", blob):
        raise EvidenceUnavailable("validation workflow version is unavailable")
    return blob


def verify_workflow(plan: dict, artifact, checks: dict) -> None:
    if not plan["required_checks"]:
        return
    expected = plan.get("environment", {}).get("ci_workflow_blob_sha")
    if (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{40}", expected)
            or workflow_blob(plan["repo"], artifact.base_sha) != expected
            or workflow_blob(plan["repo"], artifact.commit_sha) != expected):
        raise EvidenceError("validation workflow changed; trusted replan is required")
    row = checks["Herdr contract"]
    match = re.fullmatch(r"https://github\.com/" + re.escape(plan["repo"])
                         + r"/actions/runs/([1-9][0-9]*)(?:/job/[1-9][0-9]*)?",
                         row.get("details_url") or "")
    if not match:
        raise EvidenceError("check has no trusted workflow run reference")
    run = github(f"repos/{plan['repo']}/actions/runs/{match.group(1)}")
    if (run.get("id") != int(match.group(1))
            or run.get("workflow_id") != POLICY["workflow_id"]
            or run.get("path") != POLICY["workflow"]
            or run.get("head_sha") != artifact.commit_sha
            or run.get("repository", {}).get("full_name") != plan["repo"]
            or run.get("event") not in {"pull_request", "push"}
            or run.get("conclusion") != "success"):
        raise EvidenceError("CI run origin or validation definition mismatch")
    row["workflow"] = {k: run[k] for k in ("id", "workflow_id", "path", "head_sha", "event")}
    row["workflow"]["blob_sha"] = expected


def _unresolved_threads(repo: str, number: int) -> bool:
    owner, name = repo.split("/")
    query = """query($owner:String!,$name:String!,$number:Int!){
      repository(owner:$owner,name:$name){pullRequest(number:$number){
        reviewThreads(first:100){nodes{isResolved} pageInfo{hasNextPage}}}}}"""
    try:
        output = github_command(
            [str(GH), "api", "--hostname", "github.com", "graphql", "-f", f"query={query}", "-f", f"owner={owner}",
             "-f", f"name={name}", "-F", f"number={number}"],
            timeout=45, limit=1_000_000, env=os.environ.copy())
        raw = json.loads(output)["data"]["repository"]["pullRequest"]["reviewThreads"]
        if raw["pageInfo"]["hasNextPage"]:
            raise EvidenceUnavailable("review thread window is incomplete")
        if not isinstance(raw["nodes"], list) or any(
                type(row.get("isResolved")) is not bool for row in raw["nodes"]):
            raise EvidenceUnavailable("review thread state is invalid")
        return any(not row["isResolved"] for row in raw["nodes"])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise EvidenceUnavailable("review thread collection failed") from exc


def _collect_github(plan: dict, artifact, number):
    if type(number) is not int or number <= 0:
        raise EvidenceMissing("a pull request reference is required")
    repo = plan["repo"]
    pr = github(f"repos/{repo}/pulls/{number}")
    if (pr.get("head", {}).get("repo", {}).get("full_name") != repo
            or pr.get("base", {}).get("repo", {}).get("full_name") != repo
            or pr.get("head", {}).get("sha") != artifact.commit_sha
            or pr.get("base", {}).get("sha") != artifact.base_sha
            or pr.get("base", {}).get("ref") != "main"):
        raise EvidenceError("pull request repository, commit or baseline mismatch")
    checks = collect_checks(repo, artifact.commit_sha, plan["required_checks"],
                            require_success=True)
    verify_workflow(plan, artifact, checks)
    if _unresolved_threads(repo, number):
        raise EvidenceMissing("pull request has unresolved review findings")
    reviews = github(f"repos/{repo}/pulls/{number}/reviews?per_page=100")
    comments = github(f"repos/{repo}/issues/{number}/comments?per_page=100")
    # Codex publishes its clean review as a bot-authored conversation comment.
    # Resolve the reported abbreviated commit through GitHub to bind the full SHA.
    candidates = []
    for row in comments:
        if row.get("user", {}).get("login") != BOT or row.get("user", {}).get("type") != "Bot":
            continue
        body = row.get("body", "")
        match = re.search(r"\*\*Reviewed commit:\*\*\s*\x60([0-9a-f]{10,40})\x60", body)
        if not body.startswith("Codex Review: Didn't find any major issues.") or not match:
            continue
        if not artifact.commit_sha.startswith(match.group(1)):
            continue
        resolved = github(f"repos/{repo}/commits/{match.group(1)}")
        if resolved.get("sha") == artifact.commit_sha:
            candidates.append(row)
    if not candidates:
        raise EvidenceMissing("independent exact-commit review has not passed")
    clean = max(candidates, key=lambda r: r["id"])
    if any(r.get("commit_id") == artifact.commit_sha
           and r.get("user", {}).get("login") == BOT
           and r.get("submitted_at", "") > clean["created_at"]
           and r.get("state") in {"COMMENTED", "CHANGES_REQUESTED"}
           for r in reviews):
        raise EvidenceMissing("newer exact-commit review must be reconciled")
    return {"source": "github-api", "checks": checks,
            "review": {"actor": BOT, "commit_sha": artifact.commit_sha,
                       "comment_id": clean["id"], "created_at": clean["created_at"],
                       "body_digest": digest(clean["body"]),
                       "repository": repo, "pull_request": number}}


def collect_github(plan: dict, artifact, number):
    try:
        return _collect_github(plan, artifact, number)
    except EvidenceError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise EvidenceUnavailable("GitHub validation data is invalid") from exc


def store_for(root: Path, task: dict) -> EvidenceStore:
    store = EvidenceStore(root / "verification")
    # #82 exposes the workspace, caches and worktrees to the child. Every plan
    # and accepted bundle must stay outside all of those writable paths.
    store.protect_from(tuple(Path(p) for p in (
        task.get("workspace", "/home/agentops/workspaces/herdr"),
        "/home/agentops/worktrees", "/home/agentops/.hermes", "/home/agentops/.cache")))
    return store


def completion_kind(task: dict) -> str:
    if task.get("kind") == "github_root_orchestration":
        return "control"
    evidence = task.get("completion_evidence")
    if isinstance(evidence, dict) and evidence.get("kind") == "herdr_swarm_snapshot":
        return "control"
    kind = task.get("completion_kind", "coding")
    if not isinstance(kind, str):
        raise EvidenceError("completion kind is invalid")
    return kind


def spec_digest(task: dict) -> str:
    return digest({k: task.get(k) for k in
                   ("repo", "issue", "kind", "prompt", "completion_kind", "spec_hash", "completion_contract", "completion_evidence")})


def typed_policy(kind: str) -> dict:
    if kind == "coding":
        return POLICY
    return {"version": "typed-completion-v1", "kind": kind,
            "reviewer": None if kind == "control" else BOT,
            "criteria": "declared-artifact-schema-and-independent-review" if kind != "control"
                        else "summary-and-next-action-only"}


def advertise_plan(task: dict, plan: dict) -> None:
    task["completion_plan"] = {k: plan[k] for k in
                              ("kind", "identity", "plan_hash", "spec_hash", "policy_hash")}
    for key in ("base_sha", "required_checks", "reviewer", "criteria"):
        if key in plan:
            task["completion_plan"][key] = plan[key]


def completion_instructions(task: dict) -> str:
    kind = completion_kind(task)
    plan = task.get("completion_plan") or {}
    common = ("\nHOST COMPLETION VERIFICATION:\n"
              "- The host accepts results against a plan frozen before dispatch. Model prose and producer labels cannot waive it.\n"
              "- Completed worker result, integration, deployment, and control cycle are distinct levels.\n")
    if kind == "control":
        return common + ("- This is a control cycle. Supply nonempty summary and next_action; its completion does not satisfy an implementation or its dependencies.\n")
    artifact = {
        "task_id": task.get("id"), "attempt": plan.get("identity", {}).get("attempt"),
        "base_sha": plan.get("base_sha"), "commit_sha": "<full exact commit>",
        "result_sha": "<ArtifactRef sealed content digest>", "changed_files": ["<exact changed paths>"],
        "branch": "<issue branch>",
    }
    return common + (
        "- Use the existing herdr.workspace.WorkspaceManager.seal and ArtifactRef for the committed clean worktree.\n"
        "- Add artifact, absolute artifact_workspace, and numeric pr_number to the result JSON. Artifact fields: "
        + json.dumps(artifact, sort_keys=True) + "\n"
        "- Keep the published artifact/workspace until host acceptance. Missing or unavailable CI/review means verification_pending on this same attempt, not another implementation.\n"
        "- Frozen validation plan: " + json.dumps(plan, sort_keys=True) + "\n"
        "- Research/review use their declared report schema and exact independent artifact review; do not invent compilation, factual certainty, integration, or deployment evidence.\n")


def freeze_plan(root: Path, task: dict) -> None:
    kind = completion_kind(task)
    if kind not in {"coding", "control", "research", "review"}:
        raise EvidenceMissing(f"typed {kind} completion contract is not configured")
    if kind != "control" and task.get("repo") != POLICY["repo"]:
        raise EvidenceMissing("consumer verification policy is not configured")
    criteria = task.get("completion_contract")
    if kind in {"research", "review"}:
        validate_criteria(kind, criteria)
    store = store_for(root, task)
    identity = binding(task)
    key = digest(identity)
    try:
        old = store.read("plan", key)
    except EvidenceMissing:
        old = None
    spec_hash = spec_digest(task)
    policy_hash = digest(typed_policy(kind))
    if old is not None:
        if (old["identity"] != identity or old["spec_hash"] != spec_hash
                or old["policy_hash"] != policy_hash or old["kind"] != kind):
            raise EvidenceError("immutable completion plan changed")
        advertise_plan(task, old)
        return
    environment = {"collector": "host-control-v1" if kind == "control" else "github-api-v1",
                   "python": sys.version.split()[0]}
    plan = {"version": 1, "identity": identity, "repo": task.get("repo"), "kind": kind,
            "spec_hash": spec_hash, "policy_hash": policy_hash, "environment": environment}
    if kind == "control":
        plan["criteria"] = {"summary": "nonempty", "next_action": "nonempty",
                            "completion_level": "control_cycle"}
    else:
        workspace = Path(task.get("workspace", "")).resolve()
        try:
            proc = subprocess.run(["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                                   "-c", "core.hooksPath=/dev/null", "-C", str(workspace),
                                   "rev-parse", "origin/main"],
                                  text=True, capture_output=True, check=True, timeout=15)
            base = proc.stdout.strip()
            if not re.fullmatch(r"[0-9a-f]{40}", base):
                raise EvidenceError("baseline is invalid")
        except (OSError, subprocess.SubprocessError) as exc:
            raise EvidenceUnavailable("trusted baseline is unavailable") from exc
        required = list(CHECK_APPS) if kind == "coding" else []
        plan.update(base_sha=base, workspace_root="/home/agentops/worktrees",
                    required_checks=required, reviewer=BOT)
        if kind == "coding":
            environment.update(ci_workflow=POLICY["workflow"], github_actions_app_id=15368,
                               ci_workflow_id=POLICY["workflow_id"], ci_workflow_blob_sha=workflow_blob(task["repo"], base))
        else:
            plan["criteria"] = criteria
    plan["plan_hash"] = digest(plan)
    plan["baseline"] = (list(collect_checks(task["repo"], base, plan["required_checks"],
                                            require_success=False).values())
                        if kind == "coding" else [])
    store.publish("plan", key, plan)
    advertise_plan(task, plan)


def verify_completion(root: Path, task: dict, result: dict) -> dict:
    kind = completion_kind(task)
    if kind not in {"coding", "control", "research", "review"}:
        raise EvidenceMissing(f"typed {kind} completion contract is not configured")
    if kind in {"research", "review"}:
        validate_criteria(kind, task.get("completion_contract"))
    store = store_for(root, task)
    identity = binding(task)
    plan = store.read("plan", digest(identity))
    if (plan.get("identity") != identity or plan.get("kind") != kind
            or plan.get("spec_hash") != spec_digest(task)
            or plan.get("policy_hash") != digest(typed_policy(kind))):
        raise EvidenceError("completion specification or policy changed")
    if kind == "control":
        if (not isinstance(result.get("summary"), str) or not result["summary"].strip()
                or not isinstance(result.get("next_action"), str) or not result["next_action"].strip()):
            raise EvidenceMissing("control cycle requires summary and next action")
        key = digest({"identity": identity, "plan_hash": plan["plan_hash"], "result_hash": digest(result)})
        bundle = {"version": 1, "identity": identity, "repo": task.get("repo"),
                  "level": "control_cycle", "kind": "control", "spec_hash": plan["spec_hash"],
                  "policy_hash": plan["policy_hash"], "plan_hash": plan["plan_hash"],
                  "baseline": plan["baseline"], "environment": plan["environment"],
                  "proof": {"source": "host-schema-v1", "result_digest": digest(result)},
                  "integration": None, "deployment": None}
        return {**bundle, "bundle_hash": store.publish("accepted", key, bundle)}
    if not (task.get("execution_session") or {}).get("sandbox_verified"):
        raise EvidenceError("trusted publication requires a verified worker sandbox")
    workspace = result.get("artifact_workspace")
    if not isinstance(workspace, str) or not Path(workspace).is_absolute():
        raise EvidenceMissing("artifact workspace is missing")
    return accept_artifact(task, result, plan, store, Path(workspace), collect_github)
