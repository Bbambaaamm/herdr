"""Hermes candidate metadata invariants; no model calls or root publication."""
from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "agent-stack/bin/agent-hermes-policy-run"
AUDIT = ROOT / "scripts/audit-hermes-runtime-candidate.py"
EXPECTED_HEAD = "ef0342358f6421efb4ce919ba859d69940ca13b7"
EXPECTED_LOCK = "5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590"


def launcher():
    loader = importlib.machinery.SourceFileLoader("test_pinned_hermes_candidate", str(SOURCE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.HERMES_INVENTORY_PATH = ROOT / "herdr/hermes_source_inventory.json"
    return module


def test_committed_candidate_inventory_and_executor_agree():
    module = launcher()
    inventory = module._hermes_source_inventory()
    assert inventory["revision"] == EXPECTED_HEAD == module.HERMES_HEAD
    assert inventory["version"] == "0.21.5"
    assert len(inventory["files"]) == 1821
    assert inventory["files"] == sorted(set(inventory["files"]), key=lambda s: s.encode())
    assert "agent/host_reference.py" in inventory["files"]
    for name in (
        "hermes_platform/host/runtime.py",
        "plugins/browser/browser_use/provider.py",
        "gateway/__init__.py",
        "cron/__init__.py",
        "tui_gateway/__init__.py",
        "acp_adapter/__init__.py",
        "providers/__init__.py",
    ):
        assert name in inventory["files"]
    assert inventory["source_sha256"] == module.HERMES_SOURCE_SHA256
    assert hashlib.sha256(module.HERMES_INVENTORY_PATH.read_bytes()).hexdigest() == (
        module.HERMES_INVENTORY_SHA256
    )
    expected = hashlib.sha256(
        b"herdr-hermes-executor-v2\0"
        + bytes.fromhex(module.HERMES_SOURCE_SHA256)
        + bytes.fromhex(module.PYTHON_SHA256)
        + bytes.fromhex(module.PYTHON_STDLIB_SHA256)
        + bytes.fromhex(module.SITE_SHA256)
    ).hexdigest()
    assert module.HERMES_EXECUTOR == f"hermes:0.21.5:sha256:{expected}"


def test_audit_rejects_missing_runtime_without_publication(tmp_path):
    result = subprocess.run(
        [
            sys.executable, "-I", "-B", str(AUDIT),
            "--repo-root", str(ROOT),
            "--runtime-root", str(tmp_path),
        ],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["status"] == "BLOCKED"
    assert data["approved_for_publication"] is False
    assert data["provider_calls"] == 0
    assert data["independent_security_review"] is False


def test_lockfile_digest_is_unchanged_in_audit_contract():
    source = AUDIT.read_text()
    assert EXPECTED_HEAD in source
    assert EXPECTED_LOCK in source
    assert "approved_for_publication" in source
    assert "VERIFIED_CANDIDATE_ONLY" in source
