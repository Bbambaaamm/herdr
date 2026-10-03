"""Physical artifact, publication and host/worker boundary regressions."""
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from herdr.evidence import (EvidenceError, EvidenceMissing, EvidenceUnavailable,
                            EvidenceStore, accept_artifact, binding, canonical, digest)
from herdr.workspace import ArtifactRef, WorkspaceManager


@pytest.fixture(autouse=True)
def trusted_fixture_git(monkeypatch, request):
    if request.node.name.startswith("test_actual"):
        return
    from herdr.workspace import _real_git
    monkeypatch.setattr("herdr.evidence.read_only_git", _real_git)


def run_git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], text=True,
                          capture_output=True, check=True).stdout.strip()


def fixture(tmp_path):
    root = tmp_path / "worktrees"
    path = root / "task"
    path.mkdir(parents=True)
    run_git(path, "init", "-q")
    run_git(path, "config", "user.email", "test@example.invalid")
    run_git(path, "config", "user.name", "Evidence test")
    (path / "result.txt").write_text("before")
    run_git(path, "add", ".")
    run_git(path, "commit", "-qm", "baseline")
    base = run_git(path, "rev-parse", "HEAD")
    (path / "result.txt").write_text("verified bytes")
    run_git(path, "commit", "-qam", "result")
    commit = run_git(path, "rev-parse", "HEAD")
    task = {"id": "task", "run_token": "run", "attempt_id": 1,
            "idempotency_key": "a" * 64, "fencing_token": 2,
            "repo": "Bbambaaamm/herdr",
            "execution_session": {"agent_name": "worker", "sandbox_verified": True}}
    manager = WorkspaceManager(path, worktrees_dir=root, artifacts_dir=tmp_path / "artifacts")
    draft = ArtifactRef("task", 1, base, commit, "", (), "task")
    artifact = manager.seal(draft, path)
    plan = {"version": 1, "identity": binding(task), "repo": task["repo"], "kind": "coding",
            "spec_hash": "b" * 64, "policy_hash": "c" * 64, "base_sha": base,
            "workspace_root": str(root), "required_checks": ["tests"],
            "reviewer": "chatgpt-codex-connector[bot]", "environment": {"collector": "test"}}
    plan["plan_hash"] = digest(plan)
    plan["baseline"] = [{"head_sha": base, "status": "completed"}]
    result = {"artifact": artifact.to_json(), "pr_number": 4}
    store = EvidenceStore(tmp_path / "host" / "verification")
    proof = {"source": "github-api", "checks": {"tests": {"head_sha": commit, "id": 7}},
             "review": {"actor": plan["reviewer"], "commit_sha": commit, "comment_id": 8}}
    return task, result, plan, store, path, proof


def test_real_artifact_acceptance_is_pinned_and_restart_is_idempotent(tmp_path):
    task, result, plan, store, path, proof = fixture(tmp_path)
    calls = []
    def collect(*args):
        calls.append(args)
        return proof
    first = accept_artifact(task, result, plan, store, path, collect)
    assert first["level"] == "verified_worker_result"
    assert first["integration"] is None and first["deployment"] is None
    assert first["identity"] == binding(task)
    assert len(first["bundle_hash"]) == 64
    # Simulate restart after accepted evidence fsync, before worker task move.
    second = accept_artifact(task, result, plan, EvidenceStore(store.root), path, collect)
    assert second == first
    assert len(calls) == 1
    # Workspace cleanup does not erase or require re-producing accepted evidence.
    shutil.rmtree(path)
    assert accept_artifact(task, result, plan, store, path, collect) == first
    assert len(calls) == 1


@pytest.mark.parametrize("field,value", [
    ("task_id", "other"), ("attempt", 2), ("base_sha", "d" * 40),
])
def test_wrong_artifact_identity_is_rejected(tmp_path, field, value):
    task, result, plan, store, path, proof = fixture(tmp_path)
    result["artifact"][field] = value
    with pytest.raises(EvidenceError):
        accept_artifact(task, result, plan, store, path, lambda *a: proof)
    assert not list(store.root.glob("accepted-*"))


def test_changed_workspace_or_changed_during_collection_is_rejected(tmp_path):
    task, result, plan, store, path, proof = fixture(tmp_path)
    def collect(*args):
        (path / "result.txt").write_text("changed during verification")
        return proof
    with pytest.raises(EvidenceError):
        accept_artifact(task, result, plan, store, path, collect)
    assert not list(store.root.glob("accepted-*"))


@pytest.mark.parametrize("change", ["origin", "reviewer", "commit", "plan", "attempt"])
def test_forged_origin_stale_review_and_plan_are_rejected(tmp_path, change):
    task, result, plan, store, path, proof = fixture(tmp_path)
    if change == "origin":
        proof["source"] = "worker-text"
    elif change == "reviewer":
        proof["review"]["actor"] = "different-worker-name"
    elif change == "commit":
        proof["review"]["commit_sha"] = "e" * 40
    elif change == "plan":
        plan["required_checks"] = ["fake-check"]
    else:
        task["run_token"] = "other"
    with pytest.raises(EvidenceError):
        accept_artifact(task, result, plan, store, path, lambda *a: proof)
    assert not list(store.root.glob("accepted-*"))


def test_worker_evidence_labels_are_never_consumed(tmp_path):
    task, result, plan, store, path, proof = fixture(tmp_path)
    result["evidence"] = {"producer": "trusted-ci", "passed": True, "signed": True}
    with pytest.raises(EvidenceUnavailable):
        accept_artifact(task, result, plan, store, path,
                      lambda *a: (_ for _ in ()).throw(EvidenceUnavailable("CI offline")))
    assert not list(store.root.glob("accepted-*"))


def test_exclusive_atomic_publication_and_invalid_partial_records(tmp_path, monkeypatch):
    store = EvidenceStore(tmp_path / "host")
    key = "a" * 64
    payload = {"value": 1}
    real_link = os.link
    monkeypatch.setattr(os, "link", lambda *a, **k: (_ for _ in ()).throw(OSError("crash before publish")))
    with pytest.raises(OSError):
        store.publish("accepted", key, payload)
    with pytest.raises(EvidenceMissing):
        store.read("accepted", key)
    assert not list(store.root.glob(".publication-*"))
    monkeypatch.setattr(os, "link", real_link)
    store.publish("accepted", key, payload)
    assert store.publish("accepted", key, payload) == digest(payload)
    with pytest.raises(EvidenceError, match="immutable"):
        store.publish("accepted", key, {"value": 2})
    assert store.read("accepted", key) == payload
    store._path("accepted", key).write_text('{"payload":')
    with pytest.raises(EvidenceError, match="encoding"):
        store.read("accepted", key)


def test_store_cannot_be_inside_writable_workspace(tmp_path):
    store = EvidenceStore(tmp_path / "workspace" / "verification")
    with pytest.raises(EvidenceError, match="overlaps"):
        store.protect_from((tmp_path / "workspace",))


def test_actual_read_only_sandbox_cannot_forge_host_evidence(tmp_path):
    bwrap = shutil.which("bwrap")
    if not bwrap:
        pytest.skip("bubblewrap is not installed on this test host")
    # /tmp is masked by the production sandbox, so put a dedicated fixture on
    # the host filesystem for this physical mount-boundary test.
    base = Path(os.environ.get("HERDR_BOUNDARY_TEST_ROOT", "/home/agentops/tmp"))
    if not base.is_dir() or not os.access(base, os.W_OK):
        pytest.skip("physical boundary fixture root is unavailable")
    import tempfile
    with tempfile.TemporaryDirectory(prefix="evidence-boundary-", dir=base) as directory:
        host = Path(directory)
        workspace = host / "workspace"
        workspace.mkdir()
        store = EvidenceStore(host / "protected")
        key = "a" * 64
        store.publish("accepted", key, {"accepted": True})
        target = store._path("accepted", key)
        child = """import pathlib,sys
target=pathlib.Path(sys.argv[1]); workspace=pathlib.Path(sys.argv[2])
(workspace/'worker-output').write_text('allowed')
for path in (target, target.parent/'forged.json'):
    try:
        path.write_text('forged')
    except OSError:
        pass
    else:
        raise SystemExit('worker wrote protected evidence')
"""
        proc = subprocess.run([bwrap, "--ro-bind", "/", "/", "--bind", str(workspace), str(workspace),
                               "--unshare-pid", "--", sys.executable, "-c", child,
                               str(target), str(workspace)], text=True, capture_output=True)
        if "Operation not permitted" in proc.stderr or "Creating new namespace failed" in proc.stderr:
            pytest.skip("this test host denies user namespaces")
        assert proc.returncode == 0, proc.stderr
        assert (workspace / "worker-output").read_text() == "allowed"
        assert store.read("accepted", key) == {"accepted": True}
        assert not (store.root / "forged.json").exists()


def test_actual_git_filters_cannot_write_host_evidence(tmp_path):
    from herdr.evidence import read_only_git
    import tempfile
    base = Path(os.environ.get("HERDR_BOUNDARY_TEST_ROOT", "/home/agentops/tmp"))
    if not shutil.which("bwrap") or not base.is_dir() or not os.access(base, os.W_OK):
        pytest.skip("physical artifact verifier fixture root is unavailable")
    with tempfile.TemporaryDirectory(prefix="git-evidence-boundary-", dir=base) as directory:
        task, result, plan, store, workspace, proof = fixture(Path(directory))
        target = store.root / "protected-record"
        target.write_text("original")
        malicious = Path(directory) / "clean-filter.py"
        malicious.write_text("""import pathlib,sys
try:
    pathlib.Path(sys.argv[1]).write_text('forged')
except OSError:
    pass
sys.stdout.buffer.write(sys.stdin.buffer.read() + b"filter-executed")
""")
        (workspace / ".gitattributes").write_text("result.txt filter=attack\n")
        run_git(workspace, "config", "filter.attack.clean", f"/usr/bin/python3 {malicious} {target}")
        try:
            filtered = read_only_git(workspace)(["hash-object", "--path=result.txt", str(workspace / "result.txt")])
        except EvidenceUnavailable:
            pytest.skip("this test host cannot execute the read-only verifier namespace")
        unfiltered = run_git(workspace, "hash-object", "--no-filters", str(workspace / "result.txt"))
        assert filtered.strip() != unfiltered
        assert target.read_text() == "original"
        (workspace / ".gitattributes").unlink()
        # The clean filter remains configured and can run again during real
        # artifact verification, but the immutable host record stays protected.
        accepted = accept_artifact(task, result, plan, store, workspace, lambda *a: proof)
        assert accepted["level"] == "verified_worker_result"
        assert target.read_text() == "original"

def typed_fixture(tmp_path, kind, fault=None):
    task, result, plan, store, path, proof = fixture(tmp_path)
    report_path = f"reports/{kind}/report.json"
    plan["base_sha"] = run_git(path, "rev-parse", "HEAD")
    if kind == "research":
        criteria = {"schema": "research-report-v1", "report_path": report_path, "sections": ["architecture"]}
        report = {"version": 1, "kind": kind, "sections": [
            {"id": "architecture", "summary": "Declared scope", "sources": [
                {"url": "https://example.org/source", "title": "Primary reference"}]}]}
        if fault == "missing_section":
            report["sections"] = []
        elif fault == "invalid_source":
            report["sections"][0]["sources"][0]["url"] = "file:///private"
    else:
        criteria = {"schema": "review-report-v1", "report_path": report_path, "target_commit": "d" * 40}
        report = {"version": 1, "kind": kind, "target_commit": "d" * 40, "summary": "Inspected declared target",
                  "verdict": "block", "findings": [{"priority": "P2", "summary": "Concrete defect"}]}
        if fault == "wrong_target":
            report["target_commit"] = "e" * 40
        elif fault == "contradictory_pass":
            report["verdict"] = "pass"
    (path / report_path).parent.mkdir(parents=True)
    (path / report_path).write_text(json.dumps(report))
    run_git(path, "add", report_path)
    run_git(path, "commit", "-qm", "typed output")
    commit = run_git(path, "rev-parse", "HEAD")
    manager = WorkspaceManager(path, worktrees_dir=path.parent, artifacts_dir=tmp_path / "artifacts")
    artifact = manager.seal(ArtifactRef(task["id"], 1, plan["base_sha"], commit, "", (), "task"), path)
    result["artifact"] = artifact.to_json()
    plan.update(kind=kind, required_checks=["GitGuardian Security Checks"], criteria=criteria)
    plan["plan_hash"] = digest({k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}})
    proof["checks"] = {"GitGuardian Security Checks": {"head_sha": commit, "app_id": 46505, "status": "completed", "conclusion": "success"}}
    proof["review"]["commit_sha"] = commit
    return task, result, plan, store, path, proof


@pytest.mark.parametrize("kind", ["research", "review"])
def test_typed_artifact_has_own_criteria_without_fictitious_build(tmp_path, kind):
    task, result, plan, store, path, proof = typed_fixture(tmp_path, kind)
    accepted = accept_artifact(task, result, plan, store, path, lambda *a: proof)
    assert accepted["kind"] == kind
    assert set(accepted["proof"]["checks"]) == {"GitGuardian Security Checks"}
    assert accepted["typed_validation"]["report_path"] == f"reports/{kind}/report.json"
    assert accepted["level"] == "verified_worker_result"
    assert accepted["integration"] is None and accepted["deployment"] is None
    if kind == "review":
        assert accepted["typed_validation"]["coverage"]["verdict"] == "block"


@pytest.mark.parametrize("kind,fault", [("research", "missing_section"), ("research", "invalid_source"),
                                        ("review", "wrong_target"), ("review", "contradictory_pass")])
def test_typed_artifact_rejects_wrong_content_and_review_target(tmp_path, kind, fault):
    task, result, plan, store, path, proof = typed_fixture(tmp_path, kind, fault)
    with pytest.raises(EvidenceError):
        accept_artifact(task, result, plan, store, path, lambda *a: proof)
    assert not list(store.root.glob("accepted-*"))

def test_research_cannot_smuggle_code_changes_under_report_criteria(tmp_path):
    task, result, plan, store, path, proof = typed_fixture(tmp_path, "research")
    (path / "implementation.py").write_text("unexpected_code = True")
    run_git(path, "add", "implementation.py")
    run_git(path, "commit", "-qm", "unrelated implementation")
    manager = WorkspaceManager(path, worktrees_dir=path.parent, artifacts_dir=tmp_path / "artifacts")
    artifact = manager.seal(ArtifactRef(task["id"], 1, plan["base_sha"],
                            run_git(path, "rev-parse", "HEAD"), "", (), "task"), path)
    result["artifact"] = artifact.to_json()
    proof["review"]["commit_sha"] = artifact.commit_sha
    with pytest.raises(EvidenceError, match="cannot carry implementation"):
        accept_artifact(task, result, plan, store, path, lambda *a: proof)
    assert not list(store.root.glob("accepted-*"))
