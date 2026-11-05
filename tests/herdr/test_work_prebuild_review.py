"""Pre-build review artifact binds the actual frozen contract content."""
from copy import deepcopy
import json
import os
import shutil
import tempfile
from pathlib import Path
import pytest
from herdr.evidence import EvidenceError, digest, inspect_typed_artifact, parse_artifact, validate_criteria
from tests.herdr.test_evidence import typed_fixture, run_git
from herdr.workspace import ArtifactRef, WorkspaceManager

@pytest.fixture
def boundary_workspace():
    base = Path(os.environ.get("HERDR_BOUNDARY_TEST_ROOT", "/home/agentops/tmp"))
    if not base.is_dir():
        pytest.skip("physical Git boundary workspace unavailable")
    directory = Path(tempfile.mkdtemp(prefix="prebuild-contract-", dir=base))
    try:
        yield directory
    finally:
        shutil.rmtree(directory)

def review(tmp_path):
    task, result, plan, store, path, proof = typed_fixture(tmp_path, "review")
    definition = {"base_sha": plan["criteria"]["target_commit"], "planning": {"goal": "Repair approved behavior"}}
    target = {"spec_sha256": "a"*64, "definition": definition}
    plan["base_sha"] = run_git(path, "rev-parse", "HEAD")
    criteria = {**plan["criteria"], "schema": "review-contract-report-v1",
                "target_contract": target, "target_contract_sha256": digest(target)}
    report = {"version": 1, "kind": "review", "target_commit": criteria["target_commit"],
              "target_contract_sha256": digest(target), "summary": "Assessed frozen outcome and oracle",
              "verdict": "pass", "findings": []}
    plan["criteria"] = criteria
    (path/criteria["report_path"]).write_text(json.dumps(report))
    run_git(path, "add", criteria["report_path"]); run_git(path, "commit", "-qm", "contract review")
    manager = WorkspaceManager(path, worktrees_dir=path.parent, artifacts_dir=tmp_path/"contract-artifacts")
    artifact = manager.seal(ArtifactRef(task["id"], 1, plan["base_sha"], plan["base_sha"], "", (), "task"), path)
    return plan, artifact, path, report

def test_actual_committed_review_contains_exact_contract_binding(boundary_workspace):
    plan, artifact, path, report = review(boundary_workspace)
    validate_criteria("review", plan["criteria"])
    evidence = inspect_typed_artifact(plan, artifact, path)
    assert evidence["coverage"]["target_contract_sha256"] == plan["criteria"]["target_contract_sha256"]
    assert evidence["coverage"]["verdict"] == "pass"

@pytest.mark.parametrize("fault", ["contract", "base", "hash", "unknown", "oversized"])
def test_unrelated_or_mutated_prebuild_target_is_rejected(tmp_path, fault):
    plan, artifact, path, report = review(tmp_path)
    criteria = plan["criteria"]
    if fault == "contract": criteria["target_contract"]["definition"]["planning"]["goal"] = "Different objective"
    if fault == "base": criteria["target_commit"] = "f"*40
    if fault == "hash": criteria["target_contract_sha256"] = "f"*64
    if fault == "unknown": criteria["permission"] = "deploy"
    if fault == "oversized": criteria["target_contract"]["definition"]["planning"]["goal"] = "x"*9000
    with pytest.raises(EvidenceError): validate_criteria("review", criteria)

def test_review_of_other_contract_does_not_pass_structure_check(boundary_workspace):
    plan, artifact, path, report = review(boundary_workspace)
    target = plan["criteria"]["target_contract"]
    target["definition"]["planning"]["goal"] = "Other task"
    plan["criteria"]["target_contract_sha256"] = digest(target)
    validate_criteria("review", plan["criteria"])
    with pytest.raises(EvidenceError, match="declared target"):
        inspect_typed_artifact(plan, artifact, path)
