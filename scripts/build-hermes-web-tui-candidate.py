#!/usr/bin/env python3
"""Build independently reviewed Hermes web/TUI artifacts in an isolated scratch tree.

This produces NON-PUBLISHABLE web/TUI candidate archives only. Hermes wheel
building is intentionally delegated to the upstream Nix/uv2nix derivation;
never spoof HERMES_NIX_BUILD or bypass setup.py's distribution guard.

No model calls, host policy, active release, queue or service mutations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

EXPECTED_HEAD = "ef0342358f6421efb4ce919ba859d69940ca13b7"
UV_SHA = "5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590"
NPM_SHA = "193a3a3703499eb7c4b4ce48d3ba1e9dae2be62a48315c1e7ea9545e8be4a067"


class CandidateBuildDenied(ValueError):
    pass


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def source_preflight(checkout: Path) -> dict[str, str]:
    checkout = checkout.resolve(strict=True)
    head = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        text=True, timeout=10).strip()
    if head != EXPECTED_HEAD:
        raise CandidateBuildDenied("HERMES_CANDIDATE_COMMIT_MISMATCH")
    if subprocess.check_output(
        ["git", "-C", str(checkout), "status", "--porcelain=v1"],
        timeout=10).strip():
        raise CandidateBuildDenied("HERMES_CANDIDATE_WORKTREE_DIRTY")
    for name, expected in (("uv.lock", UV_SHA), ("package-lock.json", NPM_SHA)):
        if sha(checkout / name) != expected:
            raise CandidateBuildDenied("HERMES_CANDIDATE_LOCKFILE_MISMATCH:" + name)
    setup = (checkout / "setup.py").read_text()
    if "HERMES_NIX_BUILD" not in setup or "_GuardedBdistWheel" not in setup:
        raise CandidateBuildDenied("HERMES_WHEEL_BUILD_POLICY_UNVERIFIED")
    return {"commit": head, "uv_lock_sha256": UV_SHA, "npm_lock_sha256": NPM_SHA}


def run(command: list[str], *, cwd: Path, log: Path, offline: bool = True,
        timeout: int = 600) -> None:
    env = os.environ.copy()
    env.pop("HERMES_NIX_BUILD", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["NPM_CONFIG_AUDIT"] = "false"
    env["NPM_CONFIG_FUND"] = "false"
    env["NPM_CONFIG_OFFLINE"] = "true" if offline else "false"
    with log.open("w") as output:
        result = subprocess.run(
            command, cwd=cwd, env=env, stdout=output,
            stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if result.returncode:
        raise CandidateBuildDenied(
            "BUILD_STEP_FAILED:" + command[0] + ":" + str(result.returncode))


def tar_archived(source: Path, member: str, destination: Path) -> str:
    subprocess.run([
        "tar", "-C", str(source), "--sort=name", "--mtime=@0",
        "--owner=0", "--group=0", "--numeric-owner",
        "-cf", str(destination), member,
    ], check=True, timeout=60)
    return sha(destination)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-checkout", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--allow-npm-registry", action="store_true",
                        help="Allow dependency downloads from npm registry; no lifecycle scripts")
    args = parser.parse_args(argv)
    report = {
        "schema_version": "herdr-hermes-web-tui-build-1",
        "status": "BLOCKED",
        "approved_for_release": False,
        "wheel_status": "BLOCKED_REQUIRES_APPROVED_NIX_BUILD",
        "model_calls": 0,
    }
    try:
        origin = args.hermes_checkout.resolve(strict=True)
        scratch = args.scratch.resolve(strict=False)
        if scratch.exists():
            raise CandidateBuildDenied("SCRATCH_MUST_NOT_EXIST")
        if scratch == origin or origin in scratch.parents or scratch in origin.parents:
            raise CandidateBuildDenied("SCRATCH_ORIGIN_OVERLAP")
        report.update(source_preflight(origin))
        for tool in ("npm", "node", "tar", "git"):
            if shutil.which(tool) is None:
                raise CandidateBuildDenied("REQUIRED_BUILD_TOOL_MISSING:" + tool)
        scratch.mkdir(parents=True, mode=0o700)
        source = scratch / "source"
        source.mkdir()
        evidence = scratch / "evidence"
        evidence.mkdir()
        artifacts = scratch / "artifacts"
        artifacts.mkdir()
        archive = scratch / "tracked-source.tar"
        with archive.open("wb") as handle:
            subprocess.run(
                ["git", "-C", str(origin), "archive", "HEAD"],
                stdout=handle, check=True, timeout=60)
        subprocess.run(["tar", "-C", str(source), "-xf", str(archive)],
                       check=True, timeout=60)
        for name, expected in (("uv.lock", UV_SHA), ("package-lock.json", NPM_SHA)):
            if sha(source / name) != expected:
                raise CandidateBuildDenied("EXTRACTED_LOCKFILE_MISMATCH:" + name)
        npm_cmd = ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"]
        if not args.allow_npm_registry:
            npm_cmd.append("--offline")
        run(npm_cmd, cwd=source, log=evidence / "npm-ci.log",
            offline=not args.allow_npm_registry)
        hashes = {}
        for label, workspace, relative in (
            ("web", "web", "hermes_cli/web_dist"),
            ("tui", "ui-tui", "ui-tui/dist"),
        ):
            run(["npm", "run", "build", "--workspace", workspace],
                cwd=source, log=evidence / (label + "-build.log"))
            target = source / relative
            if not target.is_dir():
                raise CandidateBuildDenied("BUILD_OUTPUT_MISSING:" + label)
            if label == "web" and not (target / "index.html").is_file():
                raise CandidateBuildDenied("WEB_ENTRY_MISSING")
            if label == "tui" and not (target / "entry.js").is_file():
                raise CandidateBuildDenied("TUI_ENTRY_MISSING")
            output = artifacts / ("hermes-" + label + "-candidate.tar")
            hashes[label] = tar_archived(source, relative, output)
        for label, workspace, relative in (
            ("web", "web", "hermes_cli/web_dist"),
            ("tui", "ui-tui", "ui-tui/dist"),
        ):
            run(["npm", "run", "build", "--workspace", workspace],
                cwd=source, log=evidence / (label + "-build-repeat.log"))
            repeated = evidence / (label + "-repeat.tar")
            again = tar_archived(source, relative, repeated)
            repeated.unlink()
            if again != hashes[label]:
                raise CandidateBuildDenied("NONDETERMINISTIC_BUILD:" + label)
        report.update(status="WEB_TUI_CANDIDATE_VERIFIED_ONLY",
                      artifacts_sha256=hashes,
                      npm_install_scripts="disabled",
                      web_tui_reproducible=True,
                      wheel_status="BLOCKED_REQUIRES_APPROVED_NIX_BUILD")
    except (Exception, SystemExit) as exc:
        report.update(status="BLOCKED", reason=type(exc).__name__ + ": " + str(exc)[:200])
    if "scratch" in locals() and scratch.exists() and scratch.is_dir():
        (scratch / "candidate-build.audit.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "WEB_TUI_CANDIDATE_VERIFIED_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
