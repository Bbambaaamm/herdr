#!/usr/bin/env python3
"""Read-only exact Hermes source/venv candidate verifier; never grants publication.

No model/provider calls, no writes. The actual stage2 verifier is authoritative
for source/inventory digests and importable surface. This is only an audit aid.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

EXPECTED_UV_LOCK_SHA256 = "5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590"
EXPECTED_HERMES_COMMIT = "ef0342358f6421efb4ce919ba859d69940ca13b7"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--runtime-root", type=Path, required=True)
    p.add_argument("--sdk-source-checkout", type=Path)
    args = p.parse_args(argv)
    repo = args.repo_root.resolve(strict=True)
    root = args.runtime_root.resolve(strict=True)
    report = {
        "schema_version": "herdr-hermes-runtime-candidate-audit-1",
        "status": "BLOCKED",
        "approved_for_publication": False,
        "independent_security_review": False,
        "provider_calls": 0,
    }
    try:
        launcher = repo / "agent-stack/bin/agent-hermes-policy-run"
        loader = importlib.machinery.SourceFileLoader(
            "herdr_runtime_pin_audit_launcher", str(launcher))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        module.HERMES_INVENTORY_PATH = repo / "herdr/hermes_source_inventory.json"

        inventory = module._hermes_source_inventory()
        if inventory["revision"] != EXPECTED_HERMES_COMMIT:
            raise ValueError("candidate source revision differs")
        if not (root / "venv/lib/python3.11/site-packages").is_dir():
            raise ValueError("candidate site-packages absent")
        executor = module._verify_hermes_build(root)
        if executor != module.HERMES_EXECUTOR:
            raise ValueError("candidate executor identity differs")
        site = root / "venv/lib/python3.11/site-packages"
        site_digest = module._digest_site_packages(site)
        if site_digest != module.SITE_SHA256:
            raise ValueError("candidate site-packages differ")
        report.update(
            status="VERIFIED_CANDIDATE_ONLY",
            source_count=len(inventory["files"]),
            hermes_commit=inventory["revision"],
            source_sha256=inventory["source_sha256"],
            inventory_sha256=module.HERMES_INVENTORY_SHA256,
            site_sha256=site_digest,
            executor_id=executor,
        )
        if args.sdk_source_checkout is not None:
            source = args.sdk_source_checkout.resolve(strict=True)
            revision = subprocess.check_output(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                text=True, timeout=8).strip()
            if revision != EXPECTED_HERMES_COMMIT:
                raise ValueError("Hermes checkout head differs")
            lock = source / "uv.lock"
            actual = hashlib.sha256(lock.read_bytes()).hexdigest()
            if actual != EXPECTED_UV_LOCK_SHA256:
                raise ValueError("Hermes uv.lock differs")
            report["uv_lock_sha256"] = actual
            uv = shutil.which("uv")
            if uv is None:
                raise ValueError("uv missing for local dependency check")
            result = subprocess.run(
                [uv, "pip", "check", "--python", str(root / "venv/bin/python")],
                capture_output=True, text=True, timeout=45,
            )
            if result.returncode:
                raise ValueError("local uv pip check failed")
            report["uv_pip_check"] = "PASS"
    except (Exception, SystemExit) as exc:
        report.update(status="BLOCKED", reason=type(exc).__name__ + ": " + str(exc)[:240])
        print(json.dumps(report, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
