#!/usr/bin/env python3
"""Fail-closed read-only RC7 acceptance preflight.

Intentionally NEVER grants a release/publish/queue/model authority. Root
verification and independently signed release approval must take place in
the existing Herdr host boundary, not in this scratch audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys

MAX_JSON_BYTES = 131072
FILES = {
    "web": "hermes-web-candidate.tar",
    "tui": "hermes-tui-candidate.tar",
}

def read_json(path: Path) -> dict:
    if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("non-regular evidence source")
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("evidence too large")
    record = json.loads(path.read_bytes())
    if not isinstance(record, dict):
        raise ValueError("invalid evidence object")
    return record

def sha(path: Path) -> str:
    if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("non-regular archive")
    d = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            d.update(block)
    return d.hexdigest()

def assess(artifact_evidence: dict, supply_evidence: dict,
           source_evidence: dict, artifact_dir: Path) -> dict:
    if (artifact_evidence.get("schema_version") != "herdr-hermes-web-tui-build-1"
            or supply_evidence.get("schema_version") != "herdr-rc7-supply-chain-audit-1"
            or source_evidence.get("schema_version") != "herdr-hermes-runtime-candidate-audit-1"):
        raise ValueError("unsupported or missing evidence schema")
    expected_commit = "ef0342358f6421efb4ce919ba859d69940ca13b7"
    if (artifact_evidence.get("commit") != expected_commit
            or supply_evidence.get("source_commit") != expected_commit
            or source_evidence.get("hermes_commit") != expected_commit):
        raise ValueError("source commit mismatch between evidence")
    if (artifact_evidence.get("npm_lock_sha256")
            != supply_evidence.get("npm_lock_sha256")):
        raise ValueError("npm lockfile provenance mismatch")
    verified = artifact_evidence.get("artifacts_sha256")
    if not isinstance(verified, dict) or set(verified) != set(FILES):
        raise ValueError("incomplete archive evidence")
    archive_checks = {}
    for key, name in FILES.items():
        expected = verified[key]
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("invalid archive digest")
        actual = sha(artifact_dir / name)
        archive_checks[key] = actual == expected
    counts = supply_evidence.get("npm_audit", {}).get("all-workspaces", {}).get("counts", {})
    vulnerability_counts = {
        key: counts.get(key) for key in ("critical", "high", "moderate", "low")
    }
    if any(type(value) is not int or value < 0 for value in vulnerability_counts.values()):
        raise ValueError("invalid advisory counters")
    blockers = []
    if not all(archive_checks.values()):
        blockers.append("FRONTEND_ARTIFACT_DIGEST_MISMATCH")
    if not artifact_evidence.get("web_tui_reproducible"):
        blockers.append("FRONTEND_REPRODUCIBILITY_UNVERIFIED")
    if source_evidence.get("status") != "VERIFIED_CANDIDATE_ONLY":
        blockers.append("SDK_SOURCE_SITE_NOT_VERIFIED")
    if any(vulnerability_counts[k] for k in ("critical", "high")):
        blockers.append("UNTRIAGED_CRITICAL_HIGH_NPM_ADVISORIES")
    # These independent root-owned gates are NEVER satisfied by local JSON.
    blockers += [
        "APPROVED_NIX_WHEEL_AND_COMPLETE_ASSET_CLOSURE_MISSING",
        "INDEPENDENT_EXACT_HEAD_SECURITY_ACCEPTANCE_MISSING",
        "SIGNED_ROOT_OWNED_RC7_SCHEMA2_APPROVAL_MISSING",
        "NATIVE_ROOT_CHILD_DURABLE_PARENT_ACK_E2E_MISSING",
        "OPERATOR_CANARY_AND_ROLLBACK_AUTHORIZATION_MISSING",
    ]
    return {
        "schema_version": "herdr-rc7-scratch-preflight-1",
        "state": "NO_GO",
        "can_publish": False,
        "can_call_model": False,
        "can_queue_autonomous_issues": False,
        "commit": expected_commit,
        "archive_digest_matches": archive_checks,
        "vulnerability_counts": vulnerability_counts,
        "blockers": blockers,
    }

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-evidence", type=Path, required=True)
    p.add_argument("--artifact-evidence", type=Path, required=True)
    p.add_argument("--supply-evidence", type=Path, required=True)
    p.add_argument("--artifact-dir", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        report = assess(
            read_json(args.artifact_evidence),
            read_json(args.supply_evidence),
            read_json(args.source_evidence),
            args.artifact_dir,
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        report = {
            "schema_version": "herdr-rc7-scratch-preflight-1",
            "state": "BLOCKED_INVALID_EVIDENCE",
            "reason": type(exc).__name__,
            "can_publish": False,
            "can_call_model": False,
            "can_queue_autonomous_issues": False,
        }
        print(json.dumps(report, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return 3  # never convert local evidence into release authorization

if __name__ == "__main__":
    raise SystemExit(main())
