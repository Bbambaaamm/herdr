#!/usr/bin/env python3
"""Protected-branch GitHub review status evaluator.

Runs ONLY from trusted default-branch code; treats PR content and API
responses as untrusted data. No PR checkout or arbitrary shell execution.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY = "Bbambaaamm/herdr"
CONTEXT = "Herdr security review"
CI_WORKFLOW = ".github/workflows/ci.yml"
CI_WORKFLOW_ID = 367993725
CI_RUN_URL = re.compile(
    r"https://github\.com/Bbambaaamm/herdr/actions/runs/([1-9][0-9]*)"
    r"(?:/job/[1-9][0-9]*)?\Z"
)
CODEX = "chatgpt-codex-connector[bot]"
APPS = {"Herdr contract": 15368, "GitGuardian Security Checks": 46505}
SUMMARY_HEADER = "<!-- codex-pull-request-review-summary -->"
SUMMARY_PREFIX = SUMMARY_HEADER + "\n<!-- codex-review-state:v1 "
PROTECTED_FILES = (
    ".github/workflows/ci.yml",
    ".github/workflows/herdr-security-review.yml",
    "scripts/herdr_security_review_check.py",
)
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_RECORDS = 100


class GateDenied(Exception):
    """A missing, stale, forged or incomplete review blocks merge."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise GateDenied(reason)


def unique_object(pairs: list[tuple[str, Any]]) -> dict:
    value = {}
    for key, item in pairs:
        require(key not in value, "duplicate-json-key")
        value[key] = item
    return value


def parse_json(payload: bytes, maximum: int = 1_000_000) -> Any:
    require(type(payload) is bytes and 0 < len(payload) <= maximum, "json-size-invalid")
    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise GateDenied("json-invalid") from exc


def instant(value: Any) -> datetime:
    require(type(value) is str and len(value) <= 48, "review-time-invalid")
    try:
        time = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateDenied("review-time-invalid") from exc
    require(time.tzinfo is not None, "review-time-without-timezone")
    return time.astimezone(timezone.utc)


def summary(body: Any, exact_sha: str) -> bool:
    """Only a closed machine-readable clean CODEX summary counts as PASS."""
    if type(body) is not str or not body.startswith(SUMMARY_PREFIX):
        return False
    require(len(body.encode("utf-8")) <= 65536, "codex-summary-too-large")
    encoded, sep, _ = body[len(SUMMARY_PREFIX):].partition(" -->\n")
    require(bool(sep) and "\n" not in encoded and "\r" not in encoded,
            "codex-summary-framing-invalid")
    require(body.count(SUMMARY_HEADER) == 1 and body.count("codex-review-state:v1 ") == 1,
            "codex-summary-ambiguous")
    state = parse_json(encoded.encode("utf-8"), 16000)
    require(type(state) is dict and set(state) == {"code_review", "security_review"},
            "codex-summary-schema-invalid")
    for key in ("code_review", "security_review"):
        value = state[key]
        require(type(value) is dict and set(value) == {
            "commit_sha", "has_any_findings", "has_unresolved_findings", "status"
        }, "codex-summary-review-schema-invalid")
        require(value["commit_sha"] == exact_sha and value["status"] == "completed"
                and value["has_any_findings"] is False
                and value["has_unresolved_findings"] is False,
                "codex-review-not-clean")
    return True


def one_page(rows: Any, label: str) -> list:
    require(type(rows) is list and len(rows) < MAX_RECORDS,
            f"{label}-window-unbounded")
    return rows


def select_number(event: dict) -> int:
    """Never derive a PR number from executable PR-controlled code."""
    require(type(event) is dict, "event-invalid")
    number = None
    if type(event.get("pull_request")) is dict:
        number = event["pull_request"].get("number")
    elif type(event.get("issue")) is dict:
        require(type(event["issue"].get("pull_request")) is dict,
                "event-is-not-pull-request")
        number = event["issue"].get("number")
    elif type(event.get("inputs")) is dict:
        value = event["inputs"].get("pr_number")
        require(type(value) is str and value.isascii() and value.isdecimal(),
                "manual-pr-number-invalid")
        number = int(value)
    require(type(number) is int and 0 < number <= 2**31 - 1, "pr-number-invalid")
    return number


def _identity(pr: dict, sha: str) -> None:
    require(type(pr) is dict
            and pr.get("state") == "open" and pr.get("draft") is False
            and type(pr.get("number")) is int and pr["number"] > 0
            and pr.get("base", {}).get("ref") == "main"
            and pr.get("base", {}).get("repo", {}).get("full_name") == REPOSITORY
            and pr.get("head", {}).get("repo", {}).get("full_name") == REPOSITORY
            and pr.get("head", {}).get("sha") == sha, "pr-identity-changed")


def check_snapshot(snapshot: dict, *, sha: str) -> str:
    """Pure independently testable gate; all inputs fetched from GitHub."""
    require(type(snapshot) is dict and SHA.fullmatch(sha) is not None, "snapshot-invalid")
    _identity(snapshot["pr"], sha)
    rows = one_page(snapshot["checks"], "check")
    for name, app_id in APPS.items():
        matches = [row for row in rows if type(row) is dict
                   and row.get("name") == name and row.get("head_sha") == sha
                   and row.get("app", {}).get("id") == app_id
                   and type(row.get("id")) is int]
        require(bool(matches), "required-check-missing-" + name)
        latest = max(matches, key=lambda row: row["id"])
        require(latest.get("status") == "completed"
                and latest.get("conclusion") == "success",
                "required-check-not-green-" + name)
        if name == "Herdr contract":
            url = latest.get("details_url")
            require(type(url) is str, "ci-run-reference-invalid")
            match = CI_RUN_URL.fullmatch(url)
            require(match is not None, "ci-run-reference-invalid")
            runs = snapshot.get("ci_runs")
            require(type(runs) is dict, "ci-run-evidence-missing")
            run = runs.get(match.group(1))
            require(type(run) is dict
                    and type(run.get("id")) is int
                    and str(run["id"]) == match.group(1)
                    and run.get("workflow_id") == CI_WORKFLOW_ID
                    and run.get("path") == CI_WORKFLOW
                    and run.get("head_sha") == sha
                    and run.get("event") in ("pull_request", "push")
                    and run.get("repository", {}).get("full_name") == REPOSITORY
                    and run.get("status") == "completed"
                    and run.get("conclusion") == "success",
                    "ci-run-untrusted-origin")

    changed = snapshot["protected_changed"]
    require(changed is False, "trusted-merge-gate-source-changed")
    threads = snapshot["threads"]
    require(type(threads) is dict and threads.get("has_next_page") is False,
            "review-threads-incomplete")
    nodes = one_page(threads.get("nodes"), "thread")
    require(all(type(row) is dict and row.get("is_resolved") is True
                for row in nodes), "unresolved-review-thread")

    reviews = one_page(snapshot["reviews"], "review")
    effective = {}
    codex_times = []
    for item in reviews:
        require(type(item) is dict, "review-invalid")
        actor = item.get("user", {}).get("login")
        state = item.get("state")
        if actor == CODEX and item.get("commit_id") == sha:
            codex_times.append(instant(item.get("submitted_at")))
        if state in ("APPROVED", "CHANGES_REQUESTED"):
            require(type(actor) is str and bool(actor), "review-actor-invalid")
            observed = (instant(item.get("submitted_at")), item.get("id", 0))
            if actor not in effective or observed > effective[actor][0]:
                effective[actor] = (observed, state)
    require(not any(x[1] == "CHANGES_REQUESTED" for x in effective.values()),
            "changes-requested-outstanding")

    # A complete independent machine summary is required. Generic prose,
    # bot "COMMENTED" reviews and user-authored imitations never authorize.
    comments = one_page(snapshot["comments"], "comment")
    candidates = []
    for item in comments:
        require(type(item) is dict, "comment-invalid")
        author = item.get("user")
        if (type(author) is dict and author.get("login") == CODEX
                and author.get("type") == "Bot"):
            time = instant(item.get("updated_at", item.get("created_at")))
            candidates.append((time, item))
    require(bool(candidates), "codex-review-missing")
    candidates.sort(key=lambda pair: (pair[0], pair[1].get("id", 0)))
    stamp, last = candidates[-1]
    require(summary(last.get("body"), sha), "codex-current-review-not-clean")
    require(not codex_times or stamp >= max(codex_times),
            "codex-summary-before-current-review")
    _identity(snapshot["pr_after"], sha)
    require(snapshot["pr_after"]["base"].get("sha")
            == snapshot["pr"]["base"].get("sha"),
            "pr-base-changed-during-review")
    return sha


class GithubAPI:
    def __init__(self, token: str):
        require(type(token) is str and len(token) >= 10, "github-token-unavailable")
        self.token = token

    def request(self, path: str, *, payload: dict | None = None) -> Any:
        require(type(path) is str and path.startswith("/")
                and ".." not in path and not any(c in path for c in "\r\n#"),
                "github-path-invalid")
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        # Never forward GitHub credentials to a redirect destination.
        # Canonical REST/GraphQL requests should not redirect.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise GateDenied("github-api-redirect-denied")

        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        req = urllib.request.Request("https://api.github.com" + path,
                                     data=data, headers=headers,
                                     method="POST" if data is not None else "GET")
        try:
            opener = urllib.request.build_opener(NoRedirect())
            with opener.open(req, timeout=20) as response:
                return parse_json(response.read(1_000_001))
        except (OSError, urllib.error.HTTPError) as exc:
            raise GateDenied("github-api-unavailable") from exc

    def graphql_threads(self, number: int) -> dict:
        query = """query($owner:String!,$name:String!,$number:Int!){
        repository(owner:$owner,name:$name){pullRequest(number:$number){
        reviewThreads(first:100){nodes{isResolved}pageInfo{hasNextPage}}}}}"""
        result = self.request("/graphql", payload={
            "query": query, "variables": {
                "owner": "Bbambaaamm", "name": "herdr", "number": number
            }
        })
        require(type(result) is dict and not result.get("errors"), "graphql-error")
        try:
            threads = result["data"]["repository"]["pullRequest"]["reviewThreads"]
            return {"nodes": [
                {"is_resolved": item["isResolved"]} for item in threads["nodes"]
            ], "has_next_page": threads["pageInfo"]["hasNextPage"]}
        except (KeyError, TypeError, AttributeError) as exc:
            raise GateDenied("graphql-thread-response-invalid") from exc


def build_snapshot(api: GithubAPI, number: int) -> tuple[dict, str]:
    repo = "/repos/" + REPOSITORY
    pr = api.request(f"{repo}/pulls/{number}")
    require(type(pr) is dict and type(pr.get("head")) is dict
            and type(pr.get("number")) is int and pr["number"] == number,
            "pr-response-invalid")
    sha = pr["head"].get("sha")
    require(type(sha) is str and SHA.fullmatch(sha) is not None, "head-sha-invalid")
    _identity(pr, sha)
    checks = api.request(f"{repo}/commits/{sha}/check-runs?per_page=100")
    require(type(checks) is dict and type(checks.get("total_count")) is int
            and checks["total_count"] < MAX_RECORDS,
            "check-window-incomplete")
    protected_changed = False
    for name in PROTECTED_FILES:
        left = api.request(f"{repo}/contents/{name}?ref={pr['base']['sha']}")
        right = api.request(f"{repo}/contents/{name}?ref={sha}")
        require(type(left) is dict and type(right) is dict
                and type(left.get("sha")) is str and type(right.get("sha")) is str,
                "protected-source-unavailable")
        if left["sha"] != right["sha"]:
            protected_changed = True
    # The Actions app ID is shared by ALL GitHub Actions workflows, including
    # untrusted PR additions. Only the specific trusted CI workflow/run counts.
    ci_runs = {}
    for row in checks["check_runs"]:
        if type(row) is dict and row.get("name") == "Herdr contract":
            url = row.get("details_url")
            match = CI_RUN_URL.fullmatch(url) if type(url) is str else None
            if match is not None:
                run_id = match.group(1)
                if run_id not in ci_runs:
                    ci_runs[run_id] = api.request(f"{repo}/actions/runs/{run_id}")
    data = {
        "pr": pr,
        "checks": checks["check_runs"],
        "ci_runs": ci_runs,
        "protected_changed": protected_changed,
        "threads": api.graphql_threads(number),
        "reviews": api.request(f"{repo}/pulls/{number}/reviews?per_page=100"),
        "comments": api.request(f"{repo}/issues/{number}/comments?per_page=100"),
        "pr_after": api.request(f"{repo}/pulls/{number}"),
    }
    return data, sha



def main() -> int:
    """Read-only advisory check. NEVER issue a GitHub merge authorization."""
    require(os.getenv("GITHUB_REPOSITORY") == REPOSITORY, "repository-invalid")
    require(os.getenv("GITHUB_REF") == "refs/heads/main"
            and os.getenv("GITHUB_EVENT_NAME") in {
                "pull_request_target", "issue_comment", "workflow_dispatch"
            }, "untrusted-workflow-source")
    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    require(event_path.is_file() and event_path.stat().st_size <= 131072,
            "event-file-invalid")
    number = select_number(parse_json(event_path.read_bytes(), 131072))
    api = GithubAPI(os.environ.get("GITHUB_TOKEN", ""))
    try:
        snapshot, sha = build_snapshot(api, number)
        check_snapshot(snapshot, sha=sha)
    except (GateDenied, KeyError, TypeError, ValueError, AttributeError) as exc:
        reason = str(exc) if isinstance(exc, GateDenied) else "invalid-github-evidence"
        print(json.dumps({"pass": False, "pr": number, "reason": reason}))
        return 1
    print(json.dumps({
        "pass": True, "advisory_only": True,
        "authorization_granted": False, "pr": number, "head_sha": sha,
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GateDenied, OSError, KeyError, TypeError, ValueError) as exc:
        print("HERDR_SECURITY_REVIEW_DENIED:", str(exc), file=sys.stderr)
        raise SystemExit(1)
