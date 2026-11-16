"""Negative-only RC7 scratch gate; local evidence cannot authorize deployment."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/rc7_acceptance_preflight.py"

def load():
    spec = importlib.util.spec_from_file_location("rc7_scratch_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def fixtures(tmp_path):
    source = {
        "schema_version": "herdr-hermes-runtime-candidate-audit-1",
        "hermes_commit": "ef0342358f6421efb4ce919ba859d69940ca13b7",
        "status": "VERIFIED_CANDIDATE_ONLY",
    }
    hashes = {}
    for key, name in (("web", "hermes-web-candidate.tar"),
                      ("tui", "hermes-tui-candidate.tar")):
        blob = tmp_path / name
        blob.write_bytes(key.encode())
        hashes[key] = __import__("hashlib").sha256(key.encode()).hexdigest()
    artifact = {
        "schema_version": "herdr-hermes-web-tui-build-1",
        "commit": source["hermes_commit"],
        "npm_lock_sha256": "a" * 64,
        "artifacts_sha256": hashes,
        "web_tui_reproducible": True,
    }
    supply = {
        "schema_version": "herdr-rc7-supply-chain-audit-1",
        "source_commit": source["hermes_commit"],
        "npm_lock_sha256": artifact["npm_lock_sha256"],
        "npm_audit": {
            "all-workspaces": {
                "counts": {"critical": 3, "high": 6, "moderate": 9, "low": 9}
            }
        },
    }
    return source, artifact, supply

def test_valid_candidate_always_nogo(tmp_path):
    m = load()
    source, artifact, supply = fixtures(tmp_path)
    report = m.assess(artifact, supply, source, tmp_path)
    assert report["state"] == "NO_GO"
    assert report["can_publish"] is False
    assert report["can_call_model"] is False
    assert report["can_queue_autonomous_issues"] is False
    assert report["archive_digest_matches"] == {"web": True, "tui": True}
    assert "UNTRIAGED_CRITICAL_HIGH_NPM_ADVISORIES" in report["blockers"]
    assert len(report["blockers"]) >= 6

def test_tampered_artifact_is_detected_without_grant(tmp_path):
    m = load()
    source, artifact, supply = fixtures(tmp_path)
    (tmp_path / "hermes-web-candidate.tar").write_bytes(b"tampered")
    report = m.assess(artifact, supply, source, tmp_path)
    assert report["archive_digest_matches"]["web"] is False
    assert report["state"] == "NO_GO"
    assert "FRONTEND_ARTIFACT_DIGEST_MISMATCH" in report["blockers"]

def test_fake_zero_advisories_still_not_release_approval(tmp_path):
    m = load()
    source, artifact, supply = fixtures(tmp_path)
    counts = supply["npm_audit"]["all-workspaces"]["counts"]
    counts.update(critical=0, high=0)
    report = m.assess(artifact, supply, source, tmp_path)
    assert report["state"] == "NO_GO"
    assert "SIGNED_ROOT_OWNED_RC7_SCHEMA2_APPROVAL_MISSING" in report["blockers"]

def test_mismatched_source_is_denied(tmp_path):
    m = load()
    source, artifact, supply = fixtures(tmp_path)
    supply["source_commit"] = "b" * 40
    import pytest
    with pytest.raises(ValueError, match="source commit"):
        m.assess(artifact, supply, source, tmp_path)

def test_evidence_symlinks_rejected(tmp_path):
    m = load()
    real = tmp_path / "audit.json"
    real.write_text("{}")
    alias = tmp_path / "alias.json"
    alias.symlink_to(real)
    import pytest
    with pytest.raises(ValueError, match="non-regular"):
        m.read_json(alias)

def test_no_go_cli_exit_code_even_for_valid_scratch(tmp_path):
    source, artifact, supply = fixtures(tmp_path)
    for name, data in (("source", source), ("artifact", artifact), ("supply", supply)):
        (tmp_path / (name + ".json")).write_text(json.dumps(data))
    result = subprocess.run([
        sys.executable, "-I", "-B", str(SCRIPT),
        "--source-evidence", str(tmp_path / "source.json"),
        "--artifact-evidence", str(tmp_path / "artifact.json"),
        "--supply-evidence", str(tmp_path / "supply.json"),
        "--artifact-dir", str(tmp_path),
    ], capture_output=True, text=True, timeout=10)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["can_publish"] is False
