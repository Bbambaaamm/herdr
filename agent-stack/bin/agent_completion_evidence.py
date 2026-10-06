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
                            EvidenceStore, accept_artifact, binding, digest, validate_criteria, EVIDENCE_VERSION)

GH = Path("/home/agentops/.local/bin/gh")
BOT = "chatgpt-codex-connector[bot]"
# These identities are verified GitHub application IDs, not result producer names.
CHECK_APPS = {"Herdr contract": 15368, "GitGuardian Security Checks": 46505}
POLICY = {"version": "worker-completion-v2", "repo": "Bbambaaamm/herdr",
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
    if "Herdr contract" not in plan["required_checks"]:
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


def _check_effective_reviews(reviews: list) -> None:
    effective = {}
    for row in sorted(reviews, key=lambda r: (r.get("submitted_at") or "", r.get("id", 0))):
        if row.get("state") not in {"APPROVED", "CHANGES_REQUESTED"}:
            continue
        actor = row.get("user", {}).get("login")
        if not isinstance(actor, str) or not actor:
            raise EvidenceUnavailable("review authority is unavailable")
        effective[actor] = row["state"]
    if "CHANGES_REQUESTED" in effective.values():
        raise EvidenceMissing("pull request has outstanding requested changes")


def _pr_binding(pr: dict) -> tuple:
    return (pr.get("head", {}).get("sha"), pr.get("base", {}).get("sha"),
            pr.get("head", {}).get("repo", {}).get("full_name"),
            pr.get("base", {}).get("repo", {}).get("full_name"),
            pr.get("base", {}).get("ref"))


def _collect_github(plan: dict, artifact, number):
    if type(number) is not int or number <= 0:
        raise EvidenceError("immutable pull request reference is required")
    repo = plan["repo"]
    pr = github(f"repos/{repo}/pulls/{number}")
    if (pr.get("head", {}).get("repo", {}).get("full_name") != repo
            or pr.get("base", {}).get("repo", {}).get("full_name") != repo
            or pr.get("head", {}).get("sha") != artifact.commit_sha
            or pr.get("base", {}).get("sha") != artifact.base_sha
            or pr.get("base", {}).get("ref") != "main"):
        raise EvidenceError("pull request repository, commit or baseline mismatch")
    initial_binding = _pr_binding(pr)
    from herdr.verification_binding import verify_commit_binding
    specification_binding = verify_commit_binding(plan, artifact,
        github(f"repos/{repo}/commits/{artifact.commit_sha}"))
    checks = collect_checks(repo, artifact.commit_sha, plan["required_checks"],
                            require_success=True)
    verify_workflow(plan, artifact, checks)
    if _unresolved_threads(repo, number):
        raise EvidenceMissing("pull request has unresolved review findings")
    reviews = github(f"repos/{repo}/pulls/{number}/reviews?per_page=100")
    _check_effective_reviews(reviews)
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
    latest_reviews = github(f"repos/{repo}/pulls/{number}/reviews?per_page=100")
    _check_effective_reviews(latest_reviews)
    if _unresolved_threads(repo, number):
        raise EvidenceMissing("pull request acquired unresolved review findings during collection")
    if any(r.get("commit_id") == artifact.commit_sha
           and r.get("user", {}).get("login") == BOT
           and r.get("submitted_at", "") > clean["created_at"]
           and r.get("state") in {"COMMENTED", "CHANGES_REQUESTED"}
           for r in latest_reviews):
        raise EvidenceMissing("newer exact-commit review must be reconciled")
    # A rerun can supersede a previously green check during review collection.
    checks = collect_checks(repo, artifact.commit_sha, plan["required_checks"],
                            require_success=True)
    verify_workflow(plan, artifact, checks)
    latest_comments = github(f"repos/{repo}/issues/{number}/comments?per_page=100")
    retained = [row for row in latest_comments if row.get("id") == clean["id"]]
    if len(retained) != 1 or retained[0] != clean:
        raise EvidenceMissing("selected independent review changed or disappeared")
    for row in latest_comments:
        if row.get("id", 0) <= clean["id"] or row.get("user", {}).get("login") != BOT:
            continue
        body = row.get("body", "")
        match = re.search(r"\*\*Reviewed commit:\*\*\s*\x60([0-9a-f]{10,40})\x60", body)
        if match and artifact.commit_sha.startswith(match.group(1)):
            raise EvidenceMissing("newer conversation review must be reconciled")
    latest = github(f"repos/{repo}/pulls/{number}")
    if _pr_binding(latest) != initial_binding:
        raise EvidenceError("pull request changed during evidence collection; replan is required")
    return {"source": "github-api", "checks": checks,
            "review": {"actor": BOT, "commit_sha": artifact.commit_sha,
                       "comment_id": clean["id"], "created_at": clean["created_at"],
                       "body_digest": digest(clean["body"]),
                       "specification_binding": specification_binding,
                       "repository": repo, "pull_request": number}}


def collect_github(plan: dict, artifact, number):
    try:
        return _collect_github(plan, artifact, number)
    except EvidenceError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise EvidenceUnavailable("GitHub validation data is invalid") from exc


def collect_local_handoff(plan, artifact, number):
    """Read-only PR discovery for an exact host-observed local commit."""
    if number is None:
        rows = github(f"repos/{plan['repo']}/commits/{artifact.commit_sha}/pulls?per_page=100")
        if not isinstance(rows, list) or len(rows) > 100:
            raise EvidenceUnavailable("associated PR window exceeds local handoff bound")
        matching = [row for row in rows if isinstance(row, dict)
                    and _pr_binding(row) == (artifact.commit_sha, artifact.base_sha,
                         plan["repo"], plan["repo"], "main")]
        if not matching:
            raise EvidenceMissing("exact local artifact awaits its parent-published pull request")
        if len(matching) != 1 or type(matching[0].get("number")) is not int:
            raise EvidenceError("local artifact has ambiguous pull request association")
        number = matching[0]["number"]
    return collect_github(plan, artifact, number)


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
    keys=("repo", "issue", "kind", "prompt", "completion_kind", "spec_hash", "completion_contract", "completion_evidence", "child_completion_contracts")
    if "work_contract_version" in task:
        keys+=("work_contract_version",)
    if "child_work_contract_version" in task:
        keys+=("child_work_contract_version",)
    return digest({k:task.get(k) for k in keys})


def typed_policy(kind: str) -> dict:
    if kind == "coding":
        return POLICY
    return {"version": "typed-completion-v2", "kind": kind,
            "reviewer": None if kind == "control" else BOT,
            "criteria": "declared-artifact-schema-and-independent-review" if kind != "control"
                        else "summary-and-next-action-only"}


def advertise_plan(task: dict, plan: dict) -> None:
    task["completion_plan"] = {k: plan[k] for k in
                              ("kind", "identity", "plan_hash", "spec_hash", "policy_hash")}
    for key in ("base_sha", "required_checks", "reviewer", "criteria", "scope_policy"):
        if key in plan:
            task["completion_plan"][key] = plan[key]


def verification_applies(task: dict) -> bool:
    # A persisted plan remains binding even if a trusted task edit changes repo.
    return (task.get("repo") == POLICY["repo"] or completion_kind(task) == "control"
            or bool(task.get("completion_plan")))


def completion_instructions(task: dict) -> str:
    if not verification_applies(task):
        return "\nHost policy: this consumer currently retains legacy unverified completion; do not claim verified worker result, integration or deployment.\n"
    kind = completion_kind(task)
    plan = task.get("completion_plan") or {}
    common = ("\nHOST COMPLETION VERIFICATION:\n"
              "- The host accepts results against a plan frozen before dispatch. Model prose and producer labels cannot waive it.\n"
              "- Completed worker result, integration, deployment, and control cycle are distinct levels.\n")
    if kind == "control":
        return common + ("- This is a control cycle. Submit nonempty summary and evidence=[{herdr_control:{version:1,next_action:<nonempty text>}}] through herdr_submit_result. Its completion does not satisfy an implementation or its dependencies.\n")
    if kind == "coding" and task.get("work_contract_version") == 1:
        return common + ("- Use herdr_verify_work(request_id, handoff) for the frozen host oracle and exact local commit. "
            "handoff declares pr_number (null while awaiting the parent PR) and scope_claim when required. "
            "The host preserves repository hooks, seals the tested bytes and automatically submits the immutable local result. "
            "PASS forbids further implementation. Preserve the worktree while independent CI/review/integration is pending.\n"
            "- Frozen completion plan: " + json.dumps(plan, sort_keys=True) + "\n")
    from herdr.verification_binding import commit_footer
    footer = (commit_footer(plan) if {"identity","spec_hash","policy_hash","base_sha"} <= set(plan)
              else "<host must freeze and advertise this exact attempt before dispatch>")
    artifact = {
        "task_id": task.get("id"), "attempt": plan.get("identity", {}).get("attempt"),
        "base_sha": plan.get("base_sha"), "commit_sha": "<full exact commit>",
        "result_sha": "<ArtifactRef sealed content digest>", "changed_files": ["<exact changed paths>"],
        "branch": "<issue branch>",
    }
    return common + (
        "- Use the existing herdr.workspace.WorkspaceManager.seal and ArtifactRef for the committed clean worktree.\n"
        "- If the frozen plan declares scope_policy, also supply scope_self_check bound to spec_hash and exact result_sha; account for every changed file and acceptance criterion. BLOCK/REPLAN cannot claim completed.\n"
        "- Use herdr_submit_result(status, evidence, summary). Put exactly one structured evidence item {herdr_completion:{version:1,artifact:<ArtifactRef>,artifact_workspace:<absolute verified issue worktree>,pr_number:<integer>,scope_self_check:<only if required>}}. Artifact fields: "
        + json.dumps(artifact, sort_keys=True) + "\n"
        "- Keep the published artifact/workspace until host acceptance. Missing or unavailable CI/review means verification_pending on this same attempt, not another implementation.\n"
        "- The reviewed commit must contain this exact immutable footer: " + footer + "\n"
        "- Frozen validation plan: " + json.dumps(plan, sort_keys=True) + "\n"
        "- Research/review use their declared report schema and exact independent artifact review; do not invent compilation, factual certainty, integration, or deployment evidence.\n")


def freeze_plan(root: Path, task: dict) -> None:
    if not verification_applies(task):
        return
    kind = completion_kind(task)
    if kind not in {"coding", "control", "research", "review"}:
        raise EvidenceError(f"typed {kind} immutable completion contract is not configured")
    if kind != "control" and task.get("repo") != POLICY["repo"]:
        raise EvidenceError("consumer verification policy is not configured")
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
        freeze_child_completion_contracts(root, task, old)
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
        required = list(CHECK_APPS) if kind == "coding" else ["GitGuardian Security Checks"]
        plan.update(base_sha=base, workspace_root="/home/agentops/worktrees",
                    required_checks=required, reviewer=BOT)
        if kind == "coding":
            if criteria is not None:
                from herdr.scope_evidence import validate_scope_policy
                validate_scope_policy(criteria)
                plan["scope_policy"] = criteria
            environment.update(ci_workflow=POLICY["workflow"], github_actions_app_id=15368,
                               ci_workflow_id=POLICY["workflow_id"], ci_workflow_blob_sha=workflow_blob(task["repo"], base))
        else:
            plan["criteria"] = criteria
    plan["plan_hash"] = digest(plan)
    plan["baseline"] = (list(collect_checks(task["repo"], base, plan["required_checks"],
                                            require_success=False).values())
                        if kind != "control" else [])
    store.publish("plan", key, plan)
    advertise_plan(task, plan)
    freeze_child_completion_contracts(root, task, plan)


def verify_completion(root: Path, task: dict, result: dict, *, invocation_verifier=None) -> dict:
    from herdr.result_candidate import completion_candidate
    from herdr.evidence import canonical
    original_result = result
    result = completion_candidate(result, workspace=task.get("workspace") if invocation_verifier is not None else None)
    kind = completion_kind(task)
    if kind not in {"coding", "control", "research", "review"}:
        raise EvidenceError(f"typed {kind} immutable completion contract is not configured")
    if kind in {"research", "review"}:
        validate_criteria(kind, task.get("completion_contract"))
    store = store_for(root, task)
    identity = binding(task)
    try:
        plan = store.read("plan", digest(identity))
    except EvidenceMissing as exc:
        raise EvidenceError("immutable predispatch completion plan is missing") from exc
    if (plan.get("identity") != identity or plan.get("kind") != kind
            or plan.get("spec_hash") != spec_digest(task)
            or plan.get("policy_hash") != digest(typed_policy(kind))):
        raise EvidenceError("completion specification or policy changed")
    if kind == "control":
        if (not isinstance(result.get("summary"), str) or not result["summary"].strip()
                or not isinstance(result.get("next_action"), str) or not result["next_action"].strip()):
            raise EvidenceError("immutable control cycle requires summary and next action")
        key = digest({"identity": identity, "plan_hash": plan["plan_hash"]})
        previous, legacy = store.lookup_acceptance(identity, plan["plan_hash"])
        if previous is not None:
            if (previous.get("version") != EVIDENCE_VERSION
                    or previous.get("identity") != identity or previous.get("plan_hash") != plan["plan_hash"]
                    or previous.get("kind") != "control" or previous.get("level") != "control_cycle"
                    or previous.get("spec_hash") != plan["spec_hash"]
                    or previous.get("policy_hash") != plan["policy_hash"]
                    or previous.get("proof", {}).get("result_digest") != digest(original_result)):
                raise EvidenceError("immutable control outcome publication conflict")
            if legacy:
                store.publish("accepted", key, previous)
            return {**previous, "bundle_hash": digest(previous)}
        bundle = {"version": EVIDENCE_VERSION, "identity": identity, "repo": task.get("repo"),
                  "level": "control_cycle", "kind": "control", "spec_hash": plan["spec_hash"],
                  "policy_hash": plan["policy_hash"], "plan_hash": plan["plan_hash"],
                  "baseline": plan["baseline"], "environment": plan["environment"],
                  "proof": {"source": "host-schema-v1", "result_digest": digest(original_result)},
                  "integration": None, "deployment": None}
        return {**bundle, "bundle_hash": store.publish("accepted", key, bundle)}
    workspace = result.get("artifact_workspace")
    if not isinstance(workspace, str) or not Path(workspace).is_absolute():
        raise EvidenceError("immutable artifact workspace is missing")
    collector = collect_local_handoff if invocation_verifier is not None else collect_github
    return accept_artifact(task, result, plan, store, Path(workspace), collector,
                           result_payload_sha256=digest(original_result) if invocation_verifier is not None else None,
                           invocation_verifier=invocation_verifier)


def record_verification_failure(task: dict, exc: EvidenceError) -> bool:
    """Return whether this exact attempt can wait for transient evidence."""
    waiting = isinstance(exc, (EvidenceMissing, EvidenceUnavailable))
    task["attempt_state"] = "verification_pending" if waiting else "blocked"
    task["result_status"] = "verification_pending" if waiting else "blocked"
    task["verification_status"] = exc.code
    task["last_error"] = str(exc)
    task["verification_resolution"] = "waiting_for_evidence" if waiting else "needs_replan"
    task["verification_next_action"] = (
        "Reconcile missing CI/review/transport evidence for this same attempt."
        if waiting else
        "Replan the rejected artifact or changed specification under trusted policy; "
        "preserve this attempt and its immutable evidence. Automatic redispatch is forbidden."
    )
    if not waiting:
        task.pop("not_before", None)
    return waiting

def freeze_child_completion_contracts(root, task, parent_plan):
    """Persist only protected host-approved child contracts before root dispatch."""
    from herdr.child_completion_policy import freeze_policy, validate_contracts, validate_policy, policy_key
    contracts=task.get("child_completion_contracts")
    if contracts is None:
        return
    validate_contracts(contracts)
    if task.get("child_work_contract_version") is not None:
        if (type(task["child_work_contract_version"]) is not int or task["child_work_contract_version"] != 1
                or contracts["version"] != 2):
            raise EvidenceError("new coding-child admission requires the versioned work catalogue")
    if task.get("repo")!=POLICY["repo"]:
        raise EvidenceError("child completion consumer verification policy is not configured")
    base=contracts["base_sha"]
    if parent_plan.get("base_sha") is not None and parent_plan["base_sha"]!=base:
        raise EvidenceError("child baseline differs from frozen parent plan")
    store=store_for(root,task)
    try:
        old=store.read("plan",policy_key(task["repo"],task["id"],task["run_token"]))
    except EvidenceMissing:
        old=None
    if old is not None:
        validate_policy(old)
        if (old["parent"]!=binding(task) or old["parent_spec_hash"]!=spec_digest(task)
                or old["contracts"]!=contracts):
            raise EvidenceError("immutable child completion policy changed")
        return
    environment={"collector":"github-api-v1","ci_workflow_blob_sha":workflow_blob(task["repo"],base),
        "ci_workflow_id":POLICY["workflow_id"],"github_actions_app_id":15368}
    baseline=list(collect_checks(task["repo"],base,list(CHECK_APPS),require_success=False).values())
    freeze_policy(store_for(root,task),task,parent_spec_hash=spec_digest(task),
        contracts=contracts,environment=environment,baseline=baseline)

def child_completion_for_root(task_file, identity, *, factory):
    from herdr.child_completion_policy import authority_for_parent
    from herdr.policy_launch import HostPolicyLaunchFactory
    if not isinstance(factory,HostPolicyLaunchFactory) or factory.parent_grant is None:
        raise EvidenceError("authenticated host child completion factory required")
    task=getattr(factory,"verified_parent_task",None)
    path=Path(task_file)
    if (not isinstance(task,dict) or path.resolve(strict=True)!=path
            or path.parent.parent!=factory.task_store_root or task.get("id")!=identity["task_id"]
            or task.get("run_token")!=identity["run_token"]):
        raise EvidenceError("canonical authenticated parent completion binding required")
    if task.get("child_completion_contracts") is None:
        # Keep authenticated delegation available; absence of an acceptance
        # policy never authorizes an unverified completed implementation.
        return None
    return authority_for_parent(store_for(factory.task_store_root,task),task,
        parent_spec_hash=spec_digest(task),collector=collect_github,
        parent_identity=factory.parent_grant.identity)

def child_completion_for_replay(root, scheduler):
    """Restore the same frozen source ports; do not grant, dispatch or call a model."""
    from herdr.child_completion_policy import authority_for_parent
    from herdr.host_configuration import read_canonical_parent
    parents=[rec for rec in scheduler._tasks.values() if rec.parent_task_id is None]
    if len(parents)!=1:
        return None
    parent=parents[0]
    task=read_canonical_parent(root,parent.id,parent.run_token)
    if task is None or task.get("child_completion_contracts") is None:
        return None
    return authority_for_parent(store_for(root,task),task,parent_spec_hash=spec_digest(task),
        collector=collect_github,parent_identity=scheduler.ownership_parent)
