"""Build guard and evidence invariants; no npm install or model calls."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/build-hermes-web-tui-candidate.py"
AUDIT = ROOT / "docs/evidence/hermes_web_tui_rc7_candidate.audit.json"


def module():
    loader = importlib.machinery.SourceFileLoader("herdr_web_tui_candidate", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    result = importlib.util.module_from_spec(spec)
    loader.exec_module(result)
    return result


def test_candidate_commit_and_lock_pins_are_exact():
    loaded = module()
    assert loaded.EXPECTED_HEAD == "ef0342358f6421efb4ce919ba859d69940ca13b7"
    assert loaded.UV_SHA == "5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590"
    assert loaded.NPM_SHA == "193a3a3703499eb7c4b4ce48d3ba1e9dae2be62a48315c1e7ea9545e8be4a067"


def test_build_refuses_existing_scratch_before_npm(tmp_path):
    result = subprocess.run([
        sys.executable, "-I", "-B", str(SCRIPT),
        "--hermes-checkout", str(ROOT),
        "--scratch", str(tmp_path),
    ], capture_output=True, text=True, timeout=12)
    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["status"] == "BLOCKED"
    assert data["approved_for_release"] is False
    assert data["model_calls"] == 0
    assert data["wheel_status"] == "BLOCKED_REQUIRES_APPROVED_NIX_BUILD"


def test_evidence_retains_wheel_nogo_and_repeat_sha():
    result = json.loads(AUDIT.read_text())
    assert result["status"] == "WEB_TUI_CANDIDATE_VERIFIED_ONLY"
    assert result["approved_for_release"] is False
    assert result["model_calls"] == 0
    assert result["wheel_status"] == "BLOCKED_REQUIRES_APPROVED_NIX_BUILD"
    assert result["npm_install_scripts"] == "disabled"
    assert result["web_tui_reproducible"] is True
    assert result["artifacts_sha256"] == {
        "web": "b428a9b4560367d89ef33607ef250c6c8ccebaf0ed2675fc0b2b0a49a9951c4f",
        "tui": "bdf7e5be3d65a359e1e04de8ddb285521162b217fd7a24683957571a848df0f8",
    }


def test_nix_wheel_guard_remains_unmodified():
    document = (ROOT / "docs/operations/HERMES_WEB_TUI_WHEEL_RC7.md").read_text()
    assert "HERMES_NIX_BUILD" in document
    assert "wheel_status" in AUDIT.read_text()
    script = SCRIPT.read_text()
    assert 'env.pop("HERMES_NIX_BUILD", None)' in script
    assert "--ignore-scripts" in script
