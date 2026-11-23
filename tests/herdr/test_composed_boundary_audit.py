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
            "risk_classes": ["external_side_effect"],
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
             "args_sha256": "e" * 64, "seq": 0, "consumed": True,
             "grant_sha256": parent_grant},
        ],
    }
    evidence = {
        "schema_version": audit.SCHEMA_EVIDENCE,
        "action_trace_sha256": _digest(action_trace),
        "approval_ledger_sha256": _digest(approval_ledger),
        "reviewer": {"actor_id": "quantlab-codex", "independent": True,
                     "result": "accepted"},
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


def _rebind_evidence(bundle):
    """Keep reviewer evidence bound to the artifacts a test mutated."""
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])


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


def test_approved_child_write_outside_composed_scope():
    bundle = _bundle()
    child_grant = bundle["graph"]["nodes"][1]["grant_sha256"]
    bundle["policy"]["grants"][child_grant]["write_roots"] = ["/ws"]
    bundle["policy"]["grants"][child_grant]["risk_classes"] = ["workspace_write"]
    bundle["policy"]["grants"][child_grant]["approvals"] = [
        {"approval_id": "ap-child", "tool": "write_file"}]
    bundle["graph"]["nodes"][1]["tools"] = ["write_file"]
    bundle["graph"]["nodes"][1]["permissions"] = ["workspace_write"]
    bundle["action_trace"]["steps"].append(
        {"seq": 2, "node_id": "child", "tool": "write_file",
         "args_sha256": "1" * 64, "risk_class": "workspace_write",
         "write_paths": ["/etc/other"]})
    bundle["approval_ledger"]["entries"].append(
        {"approval_id": "ap-child", "node_id": "child", "tool": "write_file",
         "args_sha256": "1" * 64, "seq": 0, "consumed": True,
         "grant_sha256": child_grant})
    # The child action has a valid tool, risk class, and approval; its write
    # still escapes the composed grant scope.
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "composed_write_scope_exceeded" in out.violations
    assert "action_step_tool_not_permitted" not in out.violations
    assert "unknown_risk_class" not in out.violations
    assert "high_risk_action_without_approval" not in out.violations


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
    _rebind_evidence(bundle)
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
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "child_write_scope_exceeds_parent" in out.violations


def test_approval_must_precede_the_action_it_authorizes():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"][0]["seq"] = 5
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_after_action" in out.violations


def test_high_risk_action_without_approval_is_a_violation():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"] = []
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "high_risk_action_without_approval" in out.violations


def test_stale_permission_after_policy_epoch_change():
    bundle = _bundle()
    bundle["policy"]["epoch"] = 2
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "stale_permission_epoch" in out.violations


def test_two_agents_with_interacting_writes_conflict():
    bundle = _bundle()
    sibling_grant = "4" * 64
    bundle["policy"]["grants"][sibling_grant] = {
        "identity_sha256": "5" * 64, "credential_refs": [],
        "write_roots": ["/ws"], "risk_classes": ["workspace_write"],
        "approvals": [{"approval_id": "ap-sibling", "tool": "write_file"}]}
    bundle["graph"]["nodes"].append(
        {"id": "sibling", "parent_id": None, "role": "worker",
         "grant_sha256": sibling_grant, "tools": ["write_file"],
         "permissions": ["workspace_write"]})
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["action_trace"]["steps"].append(
        {"seq": 2, "node_id": "sibling", "tool": "write_file",
         "args_sha256": "6" * 64, "risk_class": "workspace_write",
         "write_paths": ["/ws/out"]})
    bundle["approval_ledger"]["entries"].append(
        {"approval_id": "ap-sibling", "node_id": "sibling", "tool": "write_file",
         "args_sha256": "6" * 64, "seq": 0, "consumed": True,
         "grant_sha256": sibling_grant})
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "concurrent_interacting_writes" in out.violations
    assert "action_step_tool_not_permitted" not in out.violations
    assert "unknown_risk_class" not in out.violations
    assert "high_risk_action_without_approval" not in out.violations


def test_false_accepted_approval_is_rejected():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"][0]["approval_id"] = "ap-forged"
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "false_accepted_approval" in out.violations


def test_replayed_approval_is_rejected():
    bundle = _bundle()
    replay = dict(bundle["approval_ledger"]["entries"][0])
    replay["node_id"] = "child"
    replay["grant_sha256"] = bundle["graph"]["nodes"][1]["grant_sha256"]
    bundle["approval_ledger"]["entries"].append(replay)
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
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
    del bundle["policy"]["grants"]["a" * 64]["identity_sha256"]
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "UNKNOWN"
    assert "grant_identity_sha256_invalid" in out.unknowns


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
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_not_consumed" in out.violations


def test_approval_seq_equal_to_action_seq_is_rejected():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"][0]["seq"] = 1
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
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
    assert "approval_bound_to_multiple_actions" in out.violations


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
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
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
         "args_sha256": "e" * 64, "seq": 0, "consumed": True,
         "grant_sha256": parent_grant})
    bundle["evidence"]["approval_ledger_sha256"] = _digest(bundle["approval_ledger"])
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_bound_to_multiple_actions" in out.violations


def test_single_approval_entry_matching_two_actions_is_rejected():
    bundle = _bundle()
    second = dict(bundle["action_trace"]["steps"][0])
    second["seq"] = 0
    second["write_paths"] = ["/ws/out2"]
    bundle["action_trace"]["steps"].append(second)
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_bound_to_multiple_actions" in out.violations


def test_unknown_risk_class_is_not_silently_unapproved():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"] = []
    bundle["action_trace"]["steps"][0]["risk_class"] = "UNCLASSIFIED"
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "unknown_risk_class" in out.violations


def test_missing_risk_class_is_not_silently_unapproved():
    bundle = _bundle()
    bundle["approval_ledger"]["entries"] = []
    del bundle["action_trace"]["steps"][0]["risk_class"]
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "action_step_risk_class_invalid" in out.violations


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
        _rebind_evidence(local)
        out = _audit(local)
        assert out.status == "VIOLATION", risk
        assert "high_risk_action_without_approval" in out.violations, risk


def test_evidence_without_reviewer_is_not_covered():
    bundle = _bundle()
    del bundle["evidence"]["reviewer"]
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "evidence_reviewer_invalid" in out.violations


def test_evidence_reviewer_must_be_independent():
    bundle = _bundle()
    bundle["evidence"]["reviewer"]["independent"] = False
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "evidence_reviewer_not_independent" in out.violations


def test_evidence_without_review_result_is_not_covered():
    bundle = _bundle()
    del bundle["evidence"]["artifact_result_sha256"]
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "evidence_review_result_invalid" in out.violations


def test_evidence_not_bound_to_approval_ledger_is_rejected():
    bundle = _bundle()
    bundle["evidence"]["approval_ledger_sha256"] = "9" * 64
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "evidence_approval_ledger_reference_mismatch" in out.violations


def test_action_without_write_paths_is_unknown():
    bundle = _bundle()
    del bundle["action_trace"]["steps"][0]["write_paths"]
    bundle["evidence"]["action_trace_sha256"] = _digest(bundle["action_trace"])
    out = _audit(bundle)
    assert out.status == "UNKNOWN"
    assert "action_step_write_paths_missing" in out.unknowns


def test_role_graph_cycle_is_rejected():
    bundle = _bundle()
    bundle["graph"]["nodes"][0]["parent_id"] = "child"
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "graph_role_cycle" in out.violations


@pytest.mark.parametrize("artifact,code", [
    ("graph", "graph_node_identity_invalid"),
    ("policy", "policy_grant_invalid"),
])
def test_malformed_structure_returns_specific_violation(artifact, code):
    bundle = _bundle()
    if artifact == "graph":
        bundle["graph"]["nodes"].append({"id": "parent"})
    else:
        bundle["policy"]["grants"]["a" * 64] = "not-an-object"
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert code in out.violations


@pytest.mark.parametrize("artifact", audit.ARTIFACTS)
@pytest.mark.parametrize("schema", [None, "foreign-schema"])
def test_schema_version_is_required_and_supported(artifact, schema):
    bundle = _bundle()
    if schema is None:
        del bundle[artifact]["schema_version"]
    else:
        bundle[artifact]["schema_version"] = schema
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "UNKNOWN"
    assert f"{artifact}_schema_unsupported" in out.unknowns


@pytest.mark.parametrize("artifact", ["graph", "policy"])
@pytest.mark.parametrize("epoch", [None, -1, True, "2"])
def test_epoch_must_be_valid(artifact, epoch):
    bundle = _bundle()
    if epoch is None:
        del bundle[artifact]["epoch"]
    else:
        bundle[artifact]["epoch"] = epoch
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "UNKNOWN"
    assert f"{artifact}_epoch_invalid" in out.unknowns


def test_graph_policy_epoch_mismatch_is_a_violation():
    bundle = _bundle()
    bundle["policy"]["epoch"] = 2
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "graph_policy_epoch_mismatch" in out.violations


@pytest.mark.parametrize("value,code", [
    (None, "node_tools_missing"),
    ("terminal", "node_tools_invalid"),
    ([], "action_step_tool_not_permitted"),
])
def test_step_tool_must_be_in_node_tools(value, code):
    bundle = _bundle()
    if value is None:
        del bundle["graph"]["nodes"][0]["tools"]
    else:
        bundle["graph"]["nodes"][0]["tools"] = value
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == ("UNKNOWN" if value is None or value == "terminal" else "VIOLATION")
    assert code in (out.unknowns + out.violations)


def test_approval_inventory_must_bind_same_tool():
    bundle = _bundle()
    bundle["policy"]["grants"]["a" * 64]["approvals"][0]["tool"] = "shell"
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_inventory_tool_mismatch" in out.violations


def test_dot_alias_write_path_is_invalid():
    bundle = _bundle()
    bundle["action_trace"]["steps"][0]["write_paths"] = ["/ws/./out"]
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "action_step_write_path_invalid" in out.violations


def test_narrower_child_write_root_is_allowed():
    bundle = _bundle()
    bundle["policy"]["grants"]["b" * 64]["write_roots"] = ["/ws/sub"]
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "COVERED"


def test_child_root_is_within_filesystem_root():
    bundle = _bundle()
    bundle["policy"]["grants"]["a" * 64]["write_roots"] = ["/"]
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "COVERED"


@pytest.mark.parametrize("value,status,code", [
    (None, "UNKNOWN", "review_result_missing"),
    ("pending", "UNKNOWN", "review_result_invalid"),
    ("rejected", "VIOLATION", "review_result_rejected"),
])
def test_reviewer_result_is_typed(value, status, code):
    bundle = _bundle()
    if value is None:
        del bundle["evidence"]["reviewer"]["result"]
    else:
        bundle["evidence"]["reviewer"]["result"] = value
    out = _audit(bundle)
    assert out.status == status
    assert code in (out.unknowns + out.violations)


@pytest.mark.parametrize("artifact", ["action_trace", "approval_ledger"])
@pytest.mark.parametrize("seq", [-1, True, "0"])
def test_sequences_reject_negative_bool_and_noninteger(artifact, seq):
    bundle = _bundle()
    row = bundle[artifact]["steps" if artifact == "action_trace" else "entries"][0]
    row["seq"] = seq
    _rebind_evidence(bundle)
    out = _audit(bundle)
    code = "action_step_seq_invalid" if artifact == "action_trace" else "approval_entry_malformed"
    assert out.status == "VIOLATION"
    assert code in out.violations


@pytest.mark.parametrize("artifact,field,code", [
    ("policy", "identity_sha256", "grant_identity_sha256_invalid"),
    ("policy", "credential_refs", "grant_credential_refs_invalid"),
    ("policy", "write_roots", "grant_write_roots_invalid"),
    ("policy", "risk_classes", "grant_risk_classes_invalid"),
    ("policy", "approvals", "grant_approvals_invalid"),
    ("graph", "role", "node_role_invalid"),
    ("graph", "permissions", "node_permissions_invalid"),
    ("action_trace", "tool", "action_step_tool_invalid"),
    ("action_trace", "args_sha256", "action_step_args_sha256_invalid"),
])
def test_missing_required_field_is_never_covered(artifact, field, code):
    bundle = _bundle()
    row = (bundle["policy"]["grants"]["a" * 64] if artifact == "policy"
           else bundle["graph"]["nodes"][0] if artifact == "graph"
           else bundle["action_trace"]["steps"][0])
    del row[field]
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status != "COVERED"
    assert code in (out.unknowns + out.violations)


def test_consumed_approval_without_action_is_a_violation():
    bundle = _bundle()
    bundle["policy"]["grants"]["a" * 64]["approvals"].append(
        {"approval_id": "ap-orphan", "tool": "terminal"})
    bundle["approval_ledger"]["entries"].append(
        {"approval_id": "ap-orphan", "node_id": "parent", "tool": "terminal",
         "args_sha256": "1" * 64, "seq": 0, "consumed": True,
         "grant_sha256": "a" * 64})
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_consumed_without_action" in out.violations
    assert "approval_not_consumed" not in out.violations
    assert "replayed_approval" not in out.violations
    assert "false_accepted_approval" not in out.violations


def test_two_distinct_steps_cannot_share_sequence():
    bundle = _bundle()
    child_grant = "b" * 64
    bundle["graph"]["nodes"][1]["tools"] = ["read_file"]
    bundle["policy"]["grants"][child_grant]["approvals"] = [
        {"approval_id": "ap-child", "tool": "read_file"}]
    bundle["action_trace"]["steps"].append(
        {"seq": 1, "node_id": "child", "tool": "read_file",
         "args_sha256": "1" * 64, "risk_class": "read", "write_paths": []})
    bundle["approval_ledger"]["entries"].append(
        {"approval_id": "ap-child", "node_id": "child", "tool": "read_file",
         "args_sha256": "1" * 64, "seq": 0, "consumed": True,
         "grant_sha256": child_grant})
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "action_trace_seq_not_unique" in out.violations
    assert "high_risk_action_without_approval" not in out.violations


@pytest.mark.parametrize("risk", [None, "", [], {"risk": "read"}])
def test_invalid_risk_class_has_specific_violation(risk):
    bundle = _bundle()
    bundle["action_trace"]["steps"][0]["risk_class"] = risk
    bundle["approval_ledger"]["entries"] = []
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "action_step_risk_class_invalid" in out.violations
    assert "artifact_structure_incomplete" not in out.unknowns


def test_covered_result_binds_all_five_declared_digests():
    bundle = _bundle()
    out = _audit(bundle)
    assert out.status == "COVERED"
    assert out.digests == _digests(bundle)
    assert out.to_json()["digests"] == _digests(bundle)


def test_grant_risk_classes_restrict_action_even_with_approval():
    bundle = _bundle()
    bundle["policy"]["grants"]["a" * 64]["risk_classes"] = ["read"]
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "action_step_risk_class_not_permitted" in out.violations
    assert "high_risk_action_without_approval" not in out.violations


@pytest.mark.parametrize("risk", ["EXTERNAL_SIDE_EFFECT", "foreign_risk"])
def test_grant_risk_classes_require_canonical_names(risk):
    bundle = _bundle()
    bundle["policy"]["grants"]["a" * 64]["risk_classes"] = [risk]
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "grant_risk_class_invalid" in out.violations


def test_empty_grant_risk_classes_are_unrestricted():
    bundle = _bundle()
    bundle["policy"]["grants"]["a" * 64]["risk_classes"] = []
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "COVERED"


@pytest.mark.parametrize("across_grants", [False, True])
def test_approval_inventory_rejects_duplicate_ids(across_grants):
    bundle = _bundle()
    duplicate = {"approval_id": "ap-parent", "tool": "write_file"}
    grant = "b" * 64 if across_grants else "a" * 64
    bundle["policy"]["grants"][grant]["approvals"].append(duplicate)
    bundle["graph"]["policy_sha256"] = _digest(bundle["policy"])
    bundle["action_trace"]["graph_sha256"] = _digest(bundle["graph"])
    bundle["approval_ledger"]["graph_sha256"] = _digest(bundle["graph"])
    _rebind_evidence(bundle)
    out = _audit(bundle)
    assert out.status == "VIOLATION"
    assert "approval_inventory_duplicate_approval_id" in out.violations


def test_unknown_and_violation_results_bind_declared_digests():
    bundle = _bundle()
    digests = _digests(bundle)
    unknown = audit.audit_composed_boundaries(
        digests["graph"], digests["policy"], digests["action_trace"],
        digests["approval_ledger"], digests["evidence"])
    assert unknown.status == "UNKNOWN"
    assert unknown.digests == digests

    bundle["graph"]["nodes"][0]["role"] = "changed"
    violation = audit.audit_composed_boundaries(
        digests["graph"], digests["policy"], digests["action_trace"],
        digests["approval_ledger"], digests["evidence"], **bundle)
    assert violation.status == "VIOLATION"
    assert violation.digests == digests
