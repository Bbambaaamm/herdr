"""Actual committed artifact acceptance and scope/refusal/replay regressions."""
import copy
import pytest

from herdr.evidence import accept_artifact, digest, EvidenceError
from herdr.scope_evidence import ScopeError, ScopeReplan, ScopeBlocked, validate_scope_policy
from tests.herdr.test_evidence import fixture, launch_fixture
from herdr.workspace import _real_git


@pytest.fixture(autouse=True)
def host_fixture(monkeypatch):
    # Scope tests use real Git bytes with a host launch port; actual kernel and
    # installed SDK/bootstrap boundaries have separate physical test suites.
    monkeypatch.setattr("herdr.evidence.verify_invocation_session", launch_fixture)
    monkeypatch.setattr("herdr.evidence.read_only_git", _real_git)


def scoped(tmp_path):
    task, result, plan, store, workspace, proof = fixture(tmp_path)
    policy = {"version": 1, "files": [{"path": "result.txt", "subtree": False}],
              "acceptance_ids": ["functional"], "shared_contract_keys": []}
    plan["scope_policy"] = policy
    plan["plan_hash"] = digest({k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}})
    report = {"version": 1, "spec_sha256": plan["spec_hash"],
              "artifact_sha256": result["artifact"]["result_sha"],
              "changed_groups": [{"files": ["result.txt"], "symbols": [], "resources": [],
                                  "acceptance_ids": ["functional"], "justification": "Implement required output."}],
              "unrelated_changes": [], "unexpected_side_effects": [],
              "followups_not_implemented": ["Separate optional cleanup."],
              "shared_contract_changes": [], "verdict": "IN_SCOPE"}
    result["scope_self_check"] = report
    return task, result, plan, store, workspace, proof


def test_scoped_real_artifact_keeps_evidence_and_replays_without_collector(tmp_path):
    task, result, plan, store, workspace, proof = scoped(tmp_path)
    first = accept_artifact(task, result, plan, store, workspace, lambda *a: proof)
    assert first["scope_self_check"]["report_sha256"] == digest(result["scope_self_check"])
    assert first["scope_self_check"]["report"]["followups_not_implemented"]
    again = accept_artifact(task, result, plan, store, workspace,
                           lambda *a: pytest.fail("accepted result must not repeat checks"))
    assert again == first


@pytest.mark.parametrize("change", ["missing", "artifact", "spec", "coverage", "criterion",
                                    "scope", "duplicate", "extra", "unjustified", "contract"])
def test_forged_or_unrelated_scope_denies_before_ci(tmp_path, change):
    task, result, plan, store, workspace, proof = scoped(tmp_path)
    report = result["scope_self_check"]
    if change == "missing": result.pop("scope_self_check")
    elif change == "artifact": report["artifact_sha256"] = "e" * 64
    elif change == "spec": report["spec_sha256"] = "e" * 64
    elif change == "coverage": report["changed_groups"][0]["files"] = ["missing.txt"]
    elif change == "criterion": report["changed_groups"][0]["acceptance_ids"] = ["invented"]
    elif change == "scope":
        plan["scope_policy"]["files"] = [{"path": "other.txt", "subtree": False}]
        plan["plan_hash"] = digest({k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}})
    elif change == "duplicate": report["changed_groups"].append(copy.deepcopy(report["changed_groups"][0]))
    elif change == "extra": report["new_authority"] = True
    elif change == "unjustified": report["changed_groups"][0]["justification"] = " "
    else: report["shared_contract_changes"] = [{"key": "unknown", "previous_sha256": "a"*64, "next_sha256": "b"*64}]
    with pytest.raises(ScopeError):
        accept_artifact(task, result, plan, store, workspace, lambda *a: pytest.fail("denied before collector"))
    assert not list(store.root.glob("accepted-*"))


@pytest.mark.parametrize("change,exception", [("unrelated", ScopeReplan), ("replan", ScopeReplan),
                                             ("contract", ScopeReplan), ("block", ScopeBlocked),
                                             ("side_effect", ScopeBlocked)])
def test_scope_replan_block_are_distinct_from_functional_failure(tmp_path, change, exception):
    task, result, plan, store, workspace, proof = scoped(tmp_path)
    report = result["scope_self_check"]
    if change == "unrelated": report["unrelated_changes"] = ["Optional unrelated cleanup."]
    elif change == "replan": report["verdict"] = "REPLAN_REQUIRED"
    elif change == "block": report["verdict"] = "BLOCK"
    elif change == "side_effect": report["unexpected_side_effects"] = ["Unplanned external write."]
    else:
        plan["scope_policy"]["shared_contract_keys"]=["api:v1"]
        plan["plan_hash"]=digest({k:v for k,v in plan.items() if k not in {"plan_hash","baseline"}})
        report["shared_contract_changes"] = [{"key": "api:v1", "previous_sha256": "a"*64, "next_sha256": "b"*64}]
    with pytest.raises(exception):
        accept_artifact(task, result, plan, store, workspace, lambda *a: pytest.fail("scope refused before CI"))
    assert not list(store.root.glob("accepted-*"))


def test_restart_cannot_replace_accepted_scope_narrative(tmp_path):
    task, result, plan, store, workspace, proof = scoped(tmp_path)
    accept_artifact(task, result, plan, store, workspace, lambda *a: proof)
    result["scope_self_check"]["changed_groups"][0]["justification"] = "Different accepted narrative"
    with pytest.raises(EvidenceError, match="binding"):
        accept_artifact(task, result, plan, store, workspace, lambda *a: proof)


def test_scope_mutation_during_collection_has_no_published_acceptance(tmp_path):
    task, result, plan, store, workspace, proof = scoped(tmp_path)
    def collect(*args):
        result["scope_self_check"]["followups_not_implemented"].append("Changed after initial scope check.")
        return proof
    with pytest.raises(EvidenceError, match="changed during"):
        accept_artifact(task, result, plan, store, workspace, collect)
    assert not list(store.root.glob("accepted-*"))


@pytest.mark.parametrize("bad", ["../escape", ".git/config", "/absolute", "a//b", "a/./b", "a:b", "a\\b"])
def test_frozen_scope_rejects_unsafe_paths(bad):
    with pytest.raises(ScopeError):
        validate_scope_policy({"version": 1, "files": [{"path": bad, "subtree": True}],
                               "acceptance_ids": ["functional"], "shared_contract_keys": []})


def test_malformed_scope_json_is_bounded_before_encoding(tmp_path):
    task, result, plan, store, workspace, proof = scoped(tmp_path)
    loop = []
    loop.append(loop)
    result["scope_self_check"]["changed_groups"] = loop
    with pytest.raises(ScopeError, match="structural"):
        accept_artifact(task, result, plan, store, workspace, lambda *a: proof)
    assert not list(store.root.glob("accepted-*"))
