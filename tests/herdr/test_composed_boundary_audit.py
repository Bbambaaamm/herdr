"""Offline fixtures for the read-only composed-execution boundary audit."""
import copy

import pytest

from herdr import composed_boundary_audit as audit
from herdr.security import canonical_digest


def _digest(artifact):
    return canonical_digest(artifact)


def _bundle():
    parent_grant = "a" * 64
    child_grant = "b" * 64
    grants = {
        parent_grant: {
            "identity_sha256": "c" * 64,
            "credential_refs": ["cred:workspace"],
            "write_roots": ["/ws"],
            "risk_classes": ["EXTERNAL_SIDE_EFFECT"],
            "approvals": [{"approval_id": "ap-parent", "tool": "terminal"}],
        },
        child_grant: {
            "identity_sha256": "d" * 64,
            "credential_refs": [],
            "write_roots": ["/ws"],
            "risk_classes": [],
            "approvals": [],
        },
    }
    policy = {"schema_version": audit.SCHEMA_POLICY, "epoch": 1, "grants": grants}
    graph = {
        "schema_version": audit.SCHEMA_GRAPH,
        "epoch": 1,
        "policy_sha256": _digest(policy),
        "nodes": [
            {"id": "parent", "parent_id": None, "role": "lead",
             "grant_sha256": parent_grant, "tools": ["terminal"], "permissions": ["read"]},
            {"id": "child", "parent_id": "parent", "role": "worker",
             "grant_sha256": child_grant, "tools": [], "permissions": []},
        ],
    }
    action_trace = {
        "schema_version": audit.SCHEMA_ACTION_TRACE,
        "graph_sha256": _digest(graph),
        "steps": [
            {"seq": 1, "node_id": "parent", "tool": "terminal",
             "args_sha256": "e" * 64, "risk_class": "external_side_effect",
             "write_paths": ["/ws/out"]},
        ],
    }
    approval_ledger = {
        "schema_version": audit.SCHEMA_APPROVAL_LEDGER,
        "graph_sha256": _digest(graph),
        "entries": [
            {"approval_id": "ap-parent", "node_id": "parent", "tool": "terminal",
             "args_sha256": "e" * 64, "seq": 2, "consumed": True,
             "grant_sha256": parent_grant},
        ],
    }
    evidence = {
        "schema_version": audit.SCHEMA_EVIDENCE,
        "action_trace_sha256": _digest(action_trace),
        "reviewer": {"actor_id": "quantlab-codex", "independent": True},
        "artifact_result_sha256": "f" * 64,
    }
    return {
        "graph": graph,
        "policy": policy,
        "action_trace": action_trace,
        "approval_ledger": approval_ledger,
        "evidence": evidence,
    }


def _digests(bundle):
    return {name: _digest(artifact) for name, artifact in bundle.items()}


def _audit(bundle):
    digests = _digests(bundle)
    return audit.audit_composed_boundaries(
        digests["graph"], digests["policy"], digests["action_trace"],
        digests["approval_ledger"], digests["evidence"], **copy.deepcopy(bundle))


def test_covered_baseline_is_not_authority():
    out = _audit(_bundle())
    assert out.status == "COVERED"
    assert out.violations == ()
    payload = out.to_json()
    assert payload["authoritative"] is False
    assert payload["native_e2e_accepted"] is False
    assert payload["metrics"]["steps_total"] == 1


def test_digests_without_artifacts_are_unknown_never_pass():
    digests = _digests(_bundle())
    out = audit.audit_composed_boundaries(digests["graph"], digests["policy"],
                                          digests["action_trace"],
                                          digests["approval_ledger"], digests["evidence"])
    assert out.status == "UNKNOWN"
    assert len(out.unknowns) == 5
    assert all(name.endswith("_artifact_missing") for name in out.unknowns)


@pytest.mark.parametrize("name", ["graph", "policy", "action_trace", "approval_ledger", "evidence"])
def test_malformed_digest_is_unknown(name):
    bundle = _bundle()
    digests = _digests(bundle)
    digests[name] = "not-a-digest"
    out = audit.audit_composed_boundaries(
        digests["graph"], digests["policy"], digests["action_trace"],
        digests["approval_ledger"], digests["evidence"], **copy.deepcopy(bundle))
    assert out.status == "UNKNOWN"
    assert f"{name}_digest_malformed" in out.unknowns


def test_tampered_artifact_cannot_reuse_an_old_digest():
    bundle = _bundle()
    digests = _digests(bundle)
    bundle["graph"]["nodes"][0]["role"] = "supervisor"
    out = audit.audit_composed_boundaries(
        digests["graph"], digests["policy"], digests["action_trace"],
        digests["approval_ledger"], digests["evidence"], **copy.deepcopy(bundle))
    assert out.status == "VIOLATION"
    assert "graph_digest_mismatch" in out.violations


def test_individually_permitted_writes_can_compose_out_of_scope():
    bundle = _bundle()
    child_grant = bundle["graph"]["nodes"][1]["grant_sha256"]
    bundle["policy"]["grants"][child_grant]["write_roots"] = ["/ws"]
    bundle["action_trace"]["steps"].append(
        {"seq": 1, "node_id": "child", "tool": "write_file",
         "args_sha256": "1" * 64, "risk_class": "WORKSPACE_WRITE",
         "write_paths": ["/etc/other"]})
    # Rebind the trace to the mutated policy so only the composition rule fires.
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "composed_write_scope_exceeded" in out.violations


def test_credential_shared_by_independent_branches_is_a_leak():
    bundle = _bundle()
    sibling_grant = "2" * 64
    bundle["policy"]["grants"][sibling_grant] = {
        "identity_sha256": "3" * 64, "credential_refs": ["cred:workspace"],
        "write_roots": ["/ws"], "risk_classes": [], "approvals": []}
    bundle["graph"]["nodes"].append(
        {"id": "sibling", "parent_id": None, "role": "worker",
         "grant_sha256": sibling_grant, "tools": [], "permissions": []})
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "credential_shared_across_branches" in out.violations


def test_child_scope_must_be_a_subset_of_parent_scope():
    bundle = _bundle()
    child_grant = bundle["graph"]["nodes"][1]["grant_sha256"]
    bundle["policy"]["grants"][child_grant]["credential_refs"] = ["cred:workspace"]
    bundle["policy"]["grants"][child_grant]["write_roots"] = ["/ws", "/root"]
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "child_write_scope_exceeds_parent" in out.violations


def test_approval_must_precede_the_action_it_authorizes():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"][0]["seq"] = 0
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_after_action" in out.violations


def test_high_risk_action_without_approval_is_a_violation():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"] = []
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "high_risk_action_without_approval" in out.violations


def test_stale_permission_after_policy_epoch_change():
    bundle = _bundle()
    bundle["policy"]["epoch"] = 2
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "stale_permission_epoch" in out.violations


def test_two_agents_with_interacting_writes_conflict():
    bundle = _bundle()
    sibling_grant = "4" * 64
    bundle["policy"]["grants"][sibling_grant] = {
        "identity_sha256": "5" * 64, "credential_refs": [],
        "write_roots": ["/ws"], "risk_classes": [], "approvals": []}
    bundle["graph"]["nodes"].append(
        {"id": "sibling", "parent_id": None, "role": "worker",
         "grant_sha256": sibling_grant, "tools": [], "permissions": []})
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["action_trace"]["steps"].append(
        {"seq": 1, "node_id": "sibling", "tool": "write_file",
         "args_sha256": "6" * 64, "risk_class": "WORKSPACE_WRITE",
         "write_paths": ["/ws/out"]})
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "concurrent_interacting_writes" in out.violations


def test_false_accepted_approval_is_rejected():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"][0]["approval_id"] = "ap-forged"
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "false_accepted_approval" in out.violations


def test_replayed_approval_is_rejected():
    bundle = _bundle()
    replay = dict(bundle["approval_ledger"]["entries"][0])
    replay["node_id"] = "child"
    replay["grant_sha256"] = bundle["graph"]["nodes"][1]["grant_sha256"]
    bundle["approval_ledger"]["entries"].append(replay)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "replayed_approval" in out.violations


def test_reordered_cross_artifact_reference_is_detected():
    bundle = _bundle()
    bundle["action_trace"]["graph_sha256"] = "7" * 64
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "action_trace_graph_reference_mismatch" in out.violations


def test_incomplete_structure_is_unknown_not_safe():
    bundle = _bundle()
    del bundle["graph"]["nodes"]
    out = _audit(bundle)
    assert out.status in ("UNKNOWN", "VIOLATION")
    assert out.status != "COVERED"


def test_path_traversal_cannot_escape_a_granted_root():
    bundle = _bundle()
    bundle["action_trace"]["steps"].append(
        {"seq": 1, "node_id": "child", "tool": "write_file",
         "args_sha256": "2" * 64, "risk_class": "workspace_write",
         "write_paths": ["/ws/../etc/passwd"]})
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "composed_write_scope_exceeded" in out.violations


def test_ambiguous_normalized_write_path_is_rejected():
    bundle = _bundle()
    bundle["action_trace"]["steps"].append(
        {"seq": 1, "node_id": "child", "tool": "write_file",
         "args_sha256": "3" * 64, "risk_class": "workspace_write",
         "write_paths": ["/ws/../ws/out"]})
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "composed_write_scope_exceeded" in out.violations


def test_unconsumed_approval_is_a_violation():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"][0]["consumed"] = False
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_not_consumed" in out.violations


def test_approval_seq_equal_to_action_seq_is_rejected():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"][0]["seq"] = 0
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_after_action" in out.violations


def test_one_approval_cannot_cover_two_actions():
    bundle = _bundle()
    bundle["action_trace"]["steps"].append(
        {"seq": 2, "node_id": "parent", "tool": "terminal",
         "args_sha256": "e" * 64, "risk_class": "external_side_effect",
         "write_paths": ["/ws/out2"]})
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_after_action" in out.violations


def test_one_approval_entry_bound_to_two_actions_is_over_covered():
    bundle = _bundle()
    bundle["action_trace"]["steps"].append(
        {"seq": 2, "node_id": "parent", "tool": "terminal",
         "args_sha256": "e" * 64, "risk_class": "external_side_effect",
         "write_paths": ["/ws/out2"]})
    bundle["approval_ledger"]["entries"].append(
        {"approval_id": "ap-parent", "node_id": "parent", "tool": "terminal",
         "args_sha256": "e" * 64, "seq": 3, "consumed": True,
         "grant_sha256": bundle["graph"]["nodes"][0]["grant_sha256"]})
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "replayed_approval" in out.violations


def test_distinct_approval_ids_for_two_identical_actions():
    bundle = _bundle()
    bundle["action_trace"]["steps"].append(
        {"seq": 2, "node_id": "parent", "tool": "terminal",
         "args_sha256": "e" * 64, "risk_class": "external_side_effect",
         "write_paths": ["/ws/out2"]})
    parent_grant = bundle["graph"]["nodes"][0]["grant_sha256"]
    bundle["policy"]["grants"][parent_grant]["approvals"].append(
        {"approval_id": "ap-parent-2", "tool": "terminal"})
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["entries"].append(
        {"approval_id": "ap-parent-2", "node_id": "parent", "tool": "terminal",
         "args_sha256": "e" * 64, "seq": 3, "consumed": True,
         "grant_sha256": parent_grant})
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_bound_to_multiple_actions" in out.violations


def test_unknown_risk_class_is_not_silently_unapproved():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"] = []
    bundle["action_trace"]["steps"][0]["risk_class"] = "UNCLASSIFIED"
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "unknown_risk_class" in out.violations


def test_missing_risk_class_is_not_silently_unapproved():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"] = []
    del bundle["action_trace"]["steps"][0]["risk_class"]
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "unknown_risk_class" in out.violations


def test_every_known_risk_class_requires_approval():
    bundle = _bundle()
    for risk in ("read", "workspace_write", "delegation", "result_submission",
                 "process", "external_side_effect", "credential_use", "physical"):
        step = {"seq": 0, "node_id": "parent", "tool": "terminal",
                "args_sha256": "e" * 64, "risk_class": risk,
                "write_paths": ["/ws/out"]}
        local = copy.deepcopy(bundle)
        local["action_trace"]["steps"] = [step]
        local["approval_ledger"]["entries"] = []
        local["evidence"]["action_trace_sha256"] = _digest(local["action_trace"])
        out = _audit(local)
        assert out.status == "VIOLATION", risk
        assert "high_risk_action_without_approval" in out.violations, risk
