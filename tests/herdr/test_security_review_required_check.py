"""Offline adversarial tests for the future trusted GitHub merge status gate."""
import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "scripts/herdr_security_review_check.py"
spec = importlib.util.spec_from_file_location("herdr_security_review_check", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
HEAD = "a" * 40
OTHER = "b" * 40


def clean_summary(sha=HEAD, **overrides):
    value = {
        "code_review": {
            "commit_sha": sha, "has_any_findings": False,
            "has_unresolved_findings": False, "status": "completed",
        },
        "security_review": {
            "commit_sha": sha, "has_any_findings": False,
            "has_unresolved_findings": False, "status": "completed",
        },
    }
    for key, change in overrides.items():
        value[key].update(change)
    return (gate.SUMMARY_PREFIX + json.dumps(value, sort_keys=True)
            + " -->\nSecure review emitted by Codex bot.")


def snapshot(sha=HEAD):
    pr = {
        "number": 255, "state": "open", "draft": False,
        "head": {"sha": sha, "repo": {"full_name": gate.REPOSITORY}},
        "base": {"ref": "main", "sha": OTHER,
                 "repo": {"full_name": gate.REPOSITORY}},
    }
    return {
        "pr": pr,
        "pr_after": copy.deepcopy(pr),
        "checks": [
            {"id": 100, "name": "Herdr contract", "head_sha": sha,
             "status": "completed", "conclusion": "success",
             "details_url": "https://github.com/Bbambaaamm/herdr/actions/runs/12345/job/99",
             "app": {"id": 15368}},
            {"id": 200, "name": "GitGuardian Security Checks",
             "head_sha": sha, "status": "completed", "conclusion": "success",
             "app": {"id": 46505}},
        ],
        "ci_runs": {"12345": {
            "id": 12345, "workflow_id": gate.CI_WORKFLOW_ID,
            "path": gate.CI_WORKFLOW, "head_sha": sha,
            "event": "pull_request", "status": "completed",
            "conclusion": "success",
            "repository": {"full_name": gate.REPOSITORY}
        }},
        "protected_changed": False,
        "threads": {"nodes": [], "has_next_page": False},
        "reviews": [
            {"id": 900, "state": "COMMENTED",
             "submitted_at": "2026-11-25T12:00:00Z",
             "commit_id": sha, "user": {"login": gate.CODEX, "type": "Bot"}},
        ],
        "comments": [{
            "id": 903,
            "created_at": "2026-11-25T12:00:01Z",
            "updated_at": "2026-11-25T12:00:01Z",
            "user": {"login": gate.CODEX, "type": "Bot"},
            "body": clean_summary(sha),
        }],
    }


def test_verified_exact_head_clean_independent_review_passes():
    assert gate.check_snapshot(snapshot(), sha=HEAD) == HEAD


@pytest.mark.parametrize("mutation,reason", [
    (lambda s: s["pr"]["head"].update(sha=OTHER), "pr-identity-changed"),
    (lambda s: s["pr_after"]["head"].update(sha=OTHER), "pr-identity-changed"),
    (lambda s: s["pr_after"]["base"].update(sha=HEAD), "pr-base-changed-during-review"),
    (lambda s: s["pr"].update(draft=True), "pr-identity-changed"),
    (lambda s: s["pr"]["base"].update(ref="foreign"), "pr-identity-changed"),
    (lambda s: s.update(protected_changed=True), "trusted-merge-gate-source-changed"),
    (lambda s: s["checks"][0].update(app={"id": 999}), "required-check-missing"),
    (lambda s: s["checks"][0].update(head_sha=OTHER), "required-check-missing"),
    (lambda s: s["checks"][0].update(details_url="https://github.com/Bbambaaamm/herdr/actions/runs/999"), "ci-run-untrusted-origin"),
    (lambda s: s["ci_runs"]["12345"].update(workflow_id=100), "ci-run-untrusted-origin"),
    (lambda s: s["ci_runs"]["12345"].update(path=".github/workflows/untrusted.yml"), "ci-run-untrusted-origin"),
    (lambda s: s["ci_runs"]["12345"].update(head_sha=OTHER), "ci-run-untrusted-origin"),
    (lambda s: s["ci_runs"]["12345"].update(event="workflow_dispatch"), "ci-run-untrusted-origin"),
    (lambda s: s["checks"][0].update(details_url="https://dashboard.gitguardian.com"), "ci-run-reference-invalid"),
    (lambda s: s["checks"][1].update(conclusion="failure"), "required-check-not-green"),
    (lambda s: s["checks"].append({
        "id": 201, "name": "GitGuardian Security Checks",
        "head_sha": HEAD, "status": "in_progress",
        "conclusion": None, "app": {"id": 46505}}), "required-check-not-green"),
    (lambda s: s["threads"]["nodes"].append({"is_resolved": False}),
     "unresolved-review-thread"),
    (lambda s: s["threads"].update(has_next_page=True), "review-threads-incomplete"),
    (lambda s: s["comments"][0]["user"].update(login="Bbambaaamm"),
     "codex-review-missing"),
    (lambda s: s["comments"][0]["user"].update(type="User"),
     "codex-review-missing"),
    (lambda s: s["comments"][0].update(body="Codex Review: Didn't find any major issues."),
     "codex-current-review-not-clean"),
    (lambda s: s["comments"][0].update(body=clean_summary(OTHER)),
     "codex-review-not-clean"),
    (lambda s: s["comments"][0].update(body=clean_summary(
        HEAD, security_review={"has_any_findings": True})), "codex-review-not-clean"),
    (lambda s: s["reviews"].append({
        "id": 901, "state": "CHANGES_REQUESTED",
        "submitted_at": "2026-11-25T12:01:00Z",
        "user": {"login": "reviewer", "type": "User"}}), "changes-requested-outstanding"),
    (lambda s: s["reviews"].append({
        "id": 901, "state": "COMMENTED",
        "commit_id": HEAD,
        "submitted_at": "2026-11-25T12:05:00Z",
        "user": {"login": gate.CODEX, "type": "Bot"}}),
     "codex-summary-before-current-review"),
])
def test_fail_closed_against_incomplete_or_forged_evidence(mutation, reason):
    s = snapshot()
    mutation(s)
    with pytest.raises(gate.GateDenied, match=reason):
        gate.check_snapshot(s, sha=HEAD)


def test_latest_unresolved_bot_comment_is_not_ignored():
    s = snapshot()
    s["comments"].append({
        "id": 904, "created_at": "2026-11-25T12:03:00Z",
        "user": {"login": gate.CODEX, "type": "Bot"},
        "body": "P2: unsafe workflow",
    })
    with pytest.raises(gate.GateDenied, match="codex-current-review-not-clean"):
        gate.check_snapshot(s, sha=HEAD)


def test_missing_security_review_is_not_equivalent_to_clean():
    s = snapshot()
    parsed = {"code_review": {
        "commit_sha": HEAD, "has_any_findings": False,
        "has_unresolved_findings": False, "status": "completed",
    }, "security_review": {
        "commit_sha": None, "has_any_findings": None,
        "has_unresolved_findings": None, "status": None,
    }}
    s["comments"][0]["body"] = (gate.SUMMARY_PREFIX
                                   + json.dumps(parsed) + " -->\n")
    with pytest.raises(gate.GateDenied, match="codex-review-not-clean"):
        gate.check_snapshot(s, sha=HEAD)


def test_review_thread_pagination_and_check_pagination_denied():
    s = snapshot()
    s["threads"]["nodes"] = [{"is_resolved": True}] * 100
    with pytest.raises(gate.GateDenied, match="thread-window-unbounded"):
        gate.check_snapshot(s, sha=HEAD)


def test_typed_duplicate_json_and_github_event_injection_denied():
    with pytest.raises(gate.GateDenied, match="duplicate-json-key"):
        gate.parse_json(b'{"x":1,"x":2}')
    with pytest.raises(gate.GateDenied, match="event-is-not-pull-request"):
        gate.select_number({"issue": {"number": 22}})
    with pytest.raises(gate.GateDenied, match="manual-pr-number-invalid"):
        gate.select_number({"inputs": {"pr_number": "1;exit 0"}})
    assert gate.select_number({"inputs": {"pr_number": "259"}}) == 259


def test_workflow_never_executes_untrusted_checkout():
    workflow = (SOURCE.parents[1] / ".github/workflows/herdr-security-review.yml").read_text()
    assert "pull_request_target:" in workflow
    assert "pull_request_review:" not in workflow
    assert "pull_request_review_comment:" not in workflow
    assert "persist-credentials: false" in workflow
    assert "ref: main" in workflow
    assert "statuses: write" not in workflow
    assert "python3 scripts/herdr_security_review_check.py" in workflow
    assert "pull_request.head.sha" not in workflow


def test_summary_requires_known_bot_protocol_and_both_clean_reviews():
    assert gate.summary(clean_summary(), HEAD)
    assert not gate.summary("APPROVED", HEAD)
    with pytest.raises(gate.GateDenied, match="codex-summary-ambiguous"):
        gate.summary(clean_summary() + gate.SUMMARY_HEADER, HEAD)
    with pytest.raises(gate.GateDenied, match="duplicate-json-key"):
        body = clean_summary().replace('"commit_sha": "' + HEAD + '"',
                                       '"commit_sha": "' + HEAD +
                                       '", "commit_sha": "' + HEAD + '"')
        gate.summary(body, HEAD)



def test_canonical_pr_number_and_source_paths_only():
    class FakeAPI:
        def request(self, path, **kwargs):
            assert path.startswith("/repos/" + gate.REPOSITORY)
            if "/pulls/255" in path:
                return {"number": 256, "head": {"sha": HEAD}}
            raise AssertionError(path)
    with pytest.raises(gate.GateDenied, match="pr-response-invalid"):
        gate.build_snapshot(FakeAPI(), 255)


def test_api_rejects_untrusted_paths_without_network():
    api = gate.GithubAPI("x" * 30)
    with pytest.raises(gate.GateDenied, match="github-path-invalid"):
        api.request("/repos/Bbambaaamm/herdr/../other")
    with pytest.raises(gate.GateDenied, match="github-path-invalid"):
        api.request("/graphql\nAuthorization: forged")





def test_advisory_workflow_has_no_status_write_credentials():
    workflow = (SOURCE.parents[1] / ".github/workflows/herdr-security-review.yml").read_text()
    assert "statuses: write" not in workflow
    assert "statuses: read" not in workflow
    assert "Trusted security status publisher" not in workflow
    assert "Read-only advisory security evidence" in workflow
    assert "pull_request_review:" not in workflow
    assert "pull_request_review_comment:" not in workflow


def test_untrusted_ci_workflow_cannot_supersede_legitimate_ci():
    s = snapshot()
    s["checks"].append({
        "id": 20000, "name": "Herdr contract", "head_sha": HEAD,
        "status": "completed", "conclusion": "success",
        "details_url": "https://github.com/Bbambaaamm/herdr/actions/runs/99999",
        "app": {"id": 15368},
    })
    s["ci_runs"]["99999"] = {
        "id": 99999, "workflow_id": 99999,
        "path": ".github/workflows/attacker.yml", "head_sha": HEAD,
        "event": "pull_request", "status": "completed",
        "conclusion": "success",
        "repository": {"full_name": gate.REPOSITORY},
    }
    with pytest.raises(gate.GateDenied, match="ci-run-untrusted-origin"):
        gate.check_snapshot(s, sha=HEAD)


def test_fork_identity_fails_before_any_publishing():
    s = snapshot()
    s["pr"]["head"]["repo"]["full_name"] = "attacker/fork"
    with pytest.raises(gate.GateDenied, match="pr-identity-changed"):
        gate.check_snapshot(s, sha=HEAD)
    assert not hasattr(gate, "publish")


def test_review_changes_cannot_leave_stale_success_authorization():
    s = snapshot()
    assert gate.check_snapshot(s, sha=HEAD) == HEAD
    s["reviews"].append({
        "id": 1000, "state": "CHANGES_REQUESTED",
        "submitted_at": "2026-11-25T12:20:00Z",
        "user": {"login": "human", "type": "User"},
    })
    with pytest.raises(gate.GateDenied, match="changes-requested-outstanding"):
        gate.check_snapshot(s, sha=HEAD)
    assert not hasattr(gate, "publish")
