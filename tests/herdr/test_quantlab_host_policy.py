"""Offline contract tests: proposed QuantLab authority must fail closed."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from herdr.quantlab_host_policy import (
    CONSUMER, QuantLabPolicyDenied, validate_quantlab_template,
)
from tests.herdr.test_heating_activation import source_grant


NOW = datetime(2026, 11, 23, 14, 0, tzinfo=UTC)


def policy_fixture(tmp_path):
    workspace = tmp_path / "quantlab"
    workspace.mkdir()
    results = tmp_path / "results"
    results.mkdir()
    base = source_grant(str(workspace))
    rules = tuple(
        replace(rule, allowed_roots=(str(results),))
        if rule.tool == "herdr_submit_result" else rule
        for rule in base.tool_rules
    )
    grant = replace(
        base,
        workspace_root=str(workspace),
        identity=replace(base.identity, consumer=CONSUMER),
        tool_rules=rules,
        issued_at=(NOW - timedelta(minutes=5)).isoformat(),
        expires_at=(NOW + timedelta(hours=12)).isoformat(),
    )
    return {
        "schema_version": 1, "host_uid": 1001,
        "templates": {CONSUMER: grant.to_json()},
    }, workspace, results, grant


def validate(document, workspace, results):
    return validate_quantlab_template(
        document, at=NOW, workspace=workspace, results=results,
    )


def test_approved_bounded_paper_only_template_passes(tmp_path):
    document, workspace, results, grant = policy_fixture(tmp_path)
    accepted = validate(document, workspace, results)
    assert accepted.hash == grant.hash
    assert accepted.scope.max_cost_microusd == 0
    assert not accepted.process.enabled


@pytest.mark.parametrize("fault, reason", [
    ("missing", "quantlab_template_missing"),
    ("expired", "quantlab_grant_expired_or_not_yet_active"),
    ("future", "quantlab_grant_expired_or_not_yet_active"),
    ("unbounded", "quantlab_grant_lifetime_unbounded"),
    ("identity", "quantlab_consumer_identity_mismatch"),
    ("outside", "quantlab_workspace_mismatch"),
    ("extra_permission", "quantlab_permissions_exceed_approved_scope"),
    ("paid", "quantlab_paid_execution_forbidden"),
    ("provider", "malformed_quantlab_grant"),
    ("process", "quantlab_process_execution_forbidden"),
    ("file_root", "malformed_quantlab_grant"),
    ("result_root", "quantlab_result_root_excessive"),
    ("sandbox", "quantlab_unsandboxed_tool_forbidden"),
    ("extra_tool", "malformed_quantlab_grant"),
    ("schema_bool", "unsupported_host_policy_schema"),
])
def test_invalid_templates_denied_before_any_execution(tmp_path, fault, reason):
    document, workspace, results, grant = policy_fixture(tmp_path)
    if fault == "missing":
        document["templates"].clear()
    elif fault == "schema_bool":
        document["schema_version"] = True
    else:
        if fault == "expired":
            grant = replace(grant, expires_at=(NOW - timedelta(seconds=1)).isoformat())
        elif fault == "future":
            grant = replace(grant, issued_at=(NOW + timedelta(seconds=1)).isoformat())
        elif fault == "unbounded":
            grant = replace(grant, expires_at=(NOW + timedelta(days=8)).isoformat())
        elif fault == "identity":
            grant = replace(grant, identity=replace(grant.identity, consumer="github:foreign"))
        elif fault == "outside":
            grant = replace(grant, workspace_root=str(tmp_path))
        elif fault == "extra_permission":
            grant = replace(grant, scope=replace(grant.scope, permissions=("workspace-write", "external")))
        elif fault == "paid":
            grant = replace(grant, scope=replace(grant.scope, max_cost_microusd=100))
        elif fault == "process":
            grant = replace(grant, process=replace(grant.process, enabled=True))
        elif fault in ("result_root", "sandbox"):
            target = "read_file" if fault != "result_root" else "herdr_submit_result"
            rules = tuple(
                replace(rule, allowed_roots=(str(tmp_path),))
                if rule.tool == target and fault != "sandbox" else
                replace(rule, requires_sandbox=False)
                if rule.tool == target and fault == "sandbox" else rule
                for rule in grant.tool_rules
            )
            grant = replace(grant, tool_rules=rules)
        document["templates"][CONSUMER] = grant.to_json()
        if fault == "provider":
            document["templates"][CONSUMER]["scope"]["providers"].append("other")
        elif fault == "file_root":
            for rule in document["templates"][CONSUMER]["tool_rules"]:
                if rule["tool"] == "read_file":
                    rule["allowed_roots"] = [str(tmp_path)]
        elif fault == "extra_tool":
            document["templates"][CONSUMER]["scope"]["tools"].append("terminal")
    with pytest.raises(QuantLabPolicyDenied, match=reason):
        validate(document, workspace, results)


def test_no_authority_created_by_validating_other_consumers(tmp_path):
    document, workspace, results, grant = policy_fixture(tmp_path)
    document["templates"] = {"github:Bbambaaamm/heating": grant.to_json()}
    with pytest.raises(QuantLabPolicyDenied, match="quantlab_template_missing"):
        validate(document, workspace, results)
    assert not (tmp_path / "policy-activation").exists()


def test_trusted_cli_refuses_missing_template(monkeypatch, tmp_path, capsys):
    from herdr import host_configuration, quantlab_host_policy
    document, _, _, _ = policy_fixture(tmp_path)
    document["templates"] = {}
    monkeypatch.setattr(host_configuration, "_read_configuration", lambda path: document)
    assert quantlab_host_policy.main() == 1
    assert capsys.readouterr().out.strip() == "QUANTLAB_HOST_POLICY_BLOCKED"


def test_trusted_cli_refuses_untrusted_policy_read(monkeypatch, capsys):
    from herdr import host_configuration, quantlab_host_policy
    monkeypatch.setattr(host_configuration, "_read_configuration",
                        lambda path: (_ for _ in ()).throw(PermissionError("unsafe")))
    assert quantlab_host_policy.main() == 1
    assert capsys.readouterr().out.strip() == "QUANTLAB_HOST_POLICY_BLOCKED"
