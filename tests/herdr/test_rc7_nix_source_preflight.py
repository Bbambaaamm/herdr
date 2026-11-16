"""Offline preflight and proposed manual Nix workflow are fail-closed."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/rc7_hermes_nix_source_preflight.py"
WORKFLOW = ROOT / ".github/workflows/rc7-nix-wheel-review.yml"

def load():
    spec = importlib.util.spec_from_file_location("rc7_nix_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_real_local_candidate_exact_source():
    source = Path("/home/agentops/tmp/hermes-host-reference-sdk-132-20261111")
    if not source.is_dir():
        pytest.skip("author's hermes candidate not available on this runner")
    result = load().source_check(source, ROOT)
    assert result["status"] == "EXACT_SOURCE_CANDIDATE_ONLY"
    assert result["source_files"] == 1821
    assert result["approved_for_release"] is False
    assert result["may_call_model"] is False

def test_different_commit_is_denied(tmp_path):
    with pytest.raises((ValueError, Exception)):
        load().source_check(tmp_path, ROOT)

def test_nix_workflow_requires_manual_reviewed_runner_and_never_publishes():
    text = WORKFLOW.read_text()
    assert "workflow_dispatch:" in text
    assert "self-hosted" in text
    assert "herdr-nix-reviewed" in text
    assert "environment: rc7-nix-build-review" in text
    assert "RC7_REVIEWED_HERMES_REPOSITORY" in text
    assert "nix build" in text
    assert "scripts/rc7_hermes_nix_source_preflight.py" in text
    assert "git push" not in text and "systemctl" not in text
    assert "HERMES_NIX_BUILD=1" not in text
    assert "provider" not in text.lower() or "NO_MODEL_CALLS" in text

def test_source_contract_refuses_overriding_expected_pins():
    module = load()
    assert module.COMMIT == "ef0342358f6421efb4ce919ba859d69940ca13b7"
    assert module.UV == "5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590"
    assert module.FLAKE == "ac924684836cd3676fce5338149daf2d4003208b278156078889125923c901c8"
