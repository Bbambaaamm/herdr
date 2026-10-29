#!/usr/bin/env python3
"""Reproduce #184 offline contract gates; never authorize or claim live autonomy."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import xml.etree.ElementTree as ET


SCHEMA = "herdr-offline-autonomy-contracts-1"
# Existing regressions remain the oracle. This is a test entrypoint, not another
# scheduler, queue, policy engine, economic ledger or result-acceptance authority.
CASES = {
    "duplicate_event": (
        "tests/agent_stack/test_github_intake.py::GitHubIntakeTests::test_same_approval_direct_replay_is_exclusive_and_unchanged",
        "tests/agent_stack/test_github_intake_faults.py::IntakeFollowupTests::test_concurrent_same_approval_publishes_exactly_one_complete_task",
    ),
    "restart_recovery": (
        "tests/agent_stack/test_canonical_parent_binding.py::test_actual_cold_replay_preserves_node_graph_caps_identity_and_session",
        "tests/herdr/test_parent_publication.py::test_parent_publishes_one_exact_result_and_replay_has_no_effects",
    ),
    "ambiguous_delivery": (
        "tests/herdr/test_parent_publication.py::test_lost_remote_reply_reconciles_without_repeating_the_effect",
        "tests/agent_stack/test_terminal_unknown_recovery.py::test_dispatch_worker_intake_and_export_hold_terminal_unknown",
    ),
    "budget_exhaustion": (
        "tests/herdr/test_work_budget.py::test_parent_children_atomically_reserve_last_shared_capacity",
        "tests/herdr/test_work_budget.py::test_changed_work_authorization_cannot_refill_same_key",
    ),
    "invalid_grant": (
        "tests/herdr/test_security.py::test_alias_and_task_identity_cannot_expand_grant",
        "tests/herdr/test_security.py::test_signed_grant_is_canonical_bound_to_identity_and_tamper_evident",
    ),
    "expired_approval": (
        "tests/agent_stack/test_github_intake.py::GitHubIntakeTests::test_edited_or_expired_or_unbounded_approval_is_denied",
        "tests/herdr/test_parent_publication.py::test_expired_permit_cannot_start_publication",
    ),
    "worker_crash": (
        "tests/herdr/test_scheduler.py::test_lost_worker_reclaim_without_double_commit",
        "tests/herdr/test_scheduler.py::test_expired_lease_cannot_commit_before_reclaim",
    ),
    "provider_outage": (
        "tests/herdr/test_work_budget.py::test_unknown_provider_delivery_cannot_escalate_or_fallback",
        "tests/herdr/test_work_budget.py::test_scoped_provider_stop_leaves_independent_provider_and_reconciliation_available",
    ),
    "implementation_test_failure": (
        "tests/herdr/test_work_cycle.py::test_wrong_expected_failure_is_not_repair_permission",
        "tests/herdr/test_reviewer.py::test_failed_validator_is_blocked",
    ),
    "independent_review_rejection": (
        "tests/herdr/test_reviewer.py::test_reviewer_must_be_independent",
        "tests/herdr/test_reviewer.py::test_model_block_remains_block",
    ),
    "exact_artifact": (
        "tests/herdr/test_reviewer.py::test_new_artifact_invalidates_old_review_record",
        "tests/herdr/test_parent_publication.py::test_exported_bundle_contains_the_verified_commit_and_imports_in_an_independent_bare_repo",
    ),
    "no_merge_or_deploy": (
        "tests/herdr/test_scheduler.py::test_operator_role_is_not_auto_spawnable",
        "tests/herdr/test_parent_publication.py::test_non_handoff_phase_cannot_trigger_an_oracle_or_publish",
    ),
    "no_duplicate_economic_effect": (
        "tests/herdr/test_work_budget.py::test_pre_effect_claim_is_durable_and_duplicate_start_only_reconciles",
        "tests/herdr/test_work_budget.py::test_uncertain_operation_retains_inflight_capacity_and_identity",
    ),
    "consumer_isolation": (
        "tests/agent_stack/test_github_intake.py::GitHubIntakeTests::test_task_index_scopes_same_issue_number_by_repository",
        "tests/agent_stack/test_github_intake.py::GitHubIntakeTests::test_repo_scoped_prior_evidence_does_not_cross_consumers",
    ),
}


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
         "-C", str(root), *args], check=True, capture_output=True, timeout=30,
    ).stdout


def source_snapshot(root: Path) -> dict:
    """Bind all tracked bytes, paths and Git modes, including the test oracle."""
    if git(root, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("source checkout must be clean, including untracked files")
    digest = hashlib.sha256()
    entries = git(root, "ls-files", "--stage", "-z").split(b"\0")
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, _, stage = metadata.split()
        if mode not in (b"100644", b"100755") or stage != b"0":
            raise ValueError("regular stage-zero source files required")
        relative = Path(os.fsdecode(raw_path))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("source path escaped checkout")
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.resolve().is_relative_to(root) is False:
            raise ValueError("source alias or missing file")
        digest.update(metadata + b"\t" + raw_path + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return {"head": git(root, "rev-parse", "HEAD").decode().strip(),
            "tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
            "tracked_bytes_sha256": digest.hexdigest()}


def evaluate_junit(raw: bytes, returncode: int, before: dict, after: dict) -> dict:
    """No missing selector, skip, xfail, failure or source drift may turn green."""
    rows = []
    parse_error = False
    try:
        if len(raw) > 10 * 1024 * 1024:
            raise ValueError("oversized JUnit")
        rows = list(ET.fromstring(raw).iter("testcase"))
    except (ET.ParseError, ValueError):
        parse_error = True
    seen = set()
    duplicate = False
    for row in rows:
        identity = (row.get("classname"), row.get("name"))
        duplicate |= identity in seen
        seen.add(identity)
    gates = {}
    for case, selectors in CASES.items():
        matching = []
        complete = True
        for selector in selectors:
            path, *parts = selector.split("::")
            classname = path.removesuffix(".py").replace("/", ".")
            if len(parts) == 2:
                classname += "." + parts[0]
            name = parts[-1]
            found = [r for r in rows if r.get("classname") == classname and
                     (r.get("name") == name or (r.get("name") or "").startswith(name + "["))]
            complete &= bool(found)
            matching.extend(found)
        gates[case] = {"status": "PASS" if complete and all(
            not any(r.find(tag) is not None for tag in ("failure", "error", "skipped"))
            for r in matching) else "BLOCKED", "tests": len(matching),
            "selectors": list(selectors)}
    passed = (not parse_error and not duplicate and bool(rows) and returncode == 0
              and before == after and all(g["status"] == "PASS" for g in gates.values()))
    return {"schema_version": SCHEMA,
            "status": "OFFLINE_CONTRACTS_PASSED" if passed else "BLOCKED",
            "gates": gates, "verified_gates": sum(g["status"] == "PASS" for g in gates.values()),
            "required_gates": len(CASES), "testcases": len(rows),
            "pytest_exit_code": returncode, "junit_parse_error": parse_error,
            "duplicate_testcase": duplicate, "source_unchanged": before == after,
            "source_before": before, "source_after": after,
            "evidence_level": "offline_component_contracts",
            "full_autonomy_verified": False, "native_sdk_cycle_verified": False,
            "live_dispatch_authorized": False, "merge_authorized": False,
            "deployment_authorized": False,
            "historical_cost_and_tokens": "UNKNOWN"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    evidence = args.evidence_dir.absolute()
    if os.name != "posix" or os.geteuid() == 0:
        parser.error("run as an unprivileged Linux user with the existing test dependencies")
    if evidence.resolve().is_relative_to(root):
        parser.error("evidence must be outside the source checkout")
    before = source_snapshot(root)
    evidence.mkdir(mode=0o700, parents=False, exist_ok=False)
    selectors = list(dict.fromkeys(s for group in CASES.values() for s in group))
    # Preserve the selected Python dependency runtime (including offline zip
    # installations), not PYTHONPATH or arbitrary extra pytest CLI options.
    code = ("import json,sys;sys.path[:]=json.loads(sys.argv.pop(1));"
            "import pytest;raise SystemExit(pytest.main(sys.argv[1:]))")
    command = [sys.executable, "-I", "-B", "-c", code,
               json.dumps([str(root), *sys.path]), "-q", "-p", "no:cacheprovider",
               "-o", "addopts=", "-o", "xfail_strict=true", "-o", "junit_family=xunit2",
               "--basetemp=" + str(evidence / "scratch"),
               "--junitxml=" + str(evidence / "junit.xml"), *selectors]
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    # No live queue, administrator, model, GitHub publication or service entrypoint
    # is invoked here. Selected existing tests use disposable, offline fixtures.
    with (evidence / "pytest.log").open("xb") as log:
        process = subprocess.Popen(command, cwd=root, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            returncode = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            returncode = 124
    try:
        after = source_snapshot(root)
    except (ValueError, OSError, subprocess.SubprocessError):
        after = {"inspection_failed": True}
    junit = evidence / "junit.xml"
    raw = junit.read_bytes() if junit.is_file() else b""
    report = evaluate_junit(raw, returncode, before, after)
    report["junit_sha256"] = hashlib.sha256(raw).hexdigest()
    report["log_sha256"] = hashlib.sha256((evidence / "pytest.log").read_bytes()).hexdigest()
    with (evidence / "report.json").open("x", encoding="utf-8") as output:
        json.dump(report, output, sort_keys=True, indent=2)
        output.write("\n")
    print(json.dumps({k: report[k] for k in ("schema_version", "status", "verified_gates",
        "required_gates", "testcases", "source_unchanged", "full_autonomy_verified")}))
    return 0 if report["status"] == "OFFLINE_CONTRACTS_PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
