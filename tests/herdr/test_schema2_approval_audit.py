"""No privileged publication or credential output in schema-2 readiness."""
import copy
import hashlib
from pathlib import Path

import pytest

from herdr.schema2_approval_audit import evaluate, read_current, _protected_directory
from herdr.security import canonical_json_bytes
from herdr import schema2_approval_audit as audit


def sample():
    host = {"schema_version": 1, "templates": {"private-credential": "DO_NOT_OUTPUT"}}
    issuer = {"schema_version": "herdr-automatic-launch-plan-1",
              "request_timeout_seconds": 30,
              "host_policy_sha256": hashlib.sha256(canonical_json_bytes(host)).hexdigest()}
    return host, issuer


def test_current_schema1_remains_blocked_even_with_correct_issuer_pin():
    host, issuer = sample()
    report = evaluate(host, issuer, authority_root_exists=True)
    assert report["status"] == "ROOT_PREFLIGHT_BLOCKED"
    assert report["checks"]["issuer_pin"] is True
    assert report["checks"]["host_schema_2"] is False
    assert report["native_root_child_result_accepted"] is False
    assert report["publication_authorized"] is False
    assert "DO_NOT_OUTPUT" not in str(report)


@pytest.mark.parametrize("bad", [0, True, 61, None, "30"])
def test_issuer_deadlines_fail_closed(bad):
    host, issuer = sample()
    issuer["request_timeout_seconds"] = bad
    assert not evaluate(host, issuer, authority_root_exists=True)["checks"]["issuer_timeout"]


def test_issuer_host_pin_cannot_be_manufactured_from_changed_host_policy():
    host, issuer = sample()
    host["schema_version"] = 2
    assert not evaluate(host, issuer, authority_root_exists=True)["checks"]["issuer_pin"]


def test_false_publication_record_never_passes_validation():
    host, issuer = sample()
    host["schema_version"] = 2
    host["private_launch"] = {"runtime_publication": {
        "version": "fake", "approval_sha256": "0" * 64,
        "trees": {"code": {"manifest_sha256": "0" * 64}}}}
    report = evaluate(host, issuer, authority_root_exists=True,
                      publication_record={"record_sha256": "0" * 64})
    assert report["status"] == "ROOT_PREFLIGHT_BLOCKED"
    assert not report["checks"]["runtime_publication_record"]


def test_read_current_only_uses_existing_root_validator(monkeypatch):
    host, issuer = sample()
    paths = {"host-policy.json": host, "launch-plan-issuer.json": issuer}
    calls = []
    def protected(path):
        calls.append(str(path))
        return copy.deepcopy(paths[str(path).rsplit("/", 1)[-1]])
    monkeypatch.setattr(audit, "_read_configuration", protected)
    from herdr import launch_plan_issuer
    def denied():
        raise launch_plan_issuer.SecurityError("schema2 required")
    monkeypatch.setattr(launch_plan_issuer, "_policy", denied)
    result = read_current(authority_root=Path("/not-a-real-root-owned-herdr-namespace"))
    assert result["status"] == "ROOT_PREFLIGHT_BLOCKED"
    assert not result["checks"]["native_issuer_policy"]
    assert calls == ["/etc/herdr/host-policy.json", "/etc/herdr/launch-plan-issuer.json"]


def test_no_default_acceptance_even_if_every_structural_check_passed(monkeypatch):
    host, issuer = sample()
    host["schema_version"] = 2
    host["private_launch"] = {"plan_handoff": {"automatic_issuer": True},
                              "runtime_publication": {"version":"reviewed", "approval_sha256": "a"*64,
                                                      "trees": {"code":{"manifest_sha256":"b"*64}}}}
    issuer["host_policy_sha256"] = hashlib.sha256(canonical_json_bytes(host)).hexdigest()
    from datetime import UTC, datetime, timedelta
    monkeypatch.setattr(audit, "_private_profile", lambda value: (
        None, datetime.now(UTC) + timedelta(days=1), 60))
    monkeypatch.setattr(audit, "validate_publication_record", lambda *a, **kw: True)
    report = evaluate(host, issuer, authority_root_exists=True, publication_record={"reviewed":True})
    assert report["status"] == "STATIC_GATES_PASS_NATIVE_E2E_PENDING"
    assert report["native_root_child_result_accepted"] is False
    assert report["publication_authorized"] is False


def test_symlinked_authority_directory_is_never_accepted(tmp_path):
    actual = tmp_path / "inside"
    actual.mkdir()
    alias = tmp_path / "link"
    alias.symlink_to(actual, target_is_directory=True)
    assert _protected_directory(alias) is False


def test_expired_credential_window_does_not_pass_static_readiness(monkeypatch):
    host, issuer = sample()
    host["schema_version"] = 2
    host["grant_ttl_seconds"] = 300
    host["private_launch"] = {"plan_handoff": {"automatic_issuer": True}}
    from datetime import datetime, UTC, timedelta
    monkeypatch.setattr(audit, "_private_profile",
                        lambda value: (None, datetime.now(UTC) + timedelta(seconds=30), 60))
    result = evaluate(host, issuer, authority_root_exists=True)
    assert result["checks"]["profile_credential_approval"] is False


def test_checked_in_proposal_is_not_an_authorization():
    import json
    path = Path(__file__).resolve().parents[2] / "configs/schema2-approval-bundle.proposal.json"
    raw = json.loads(path.read_text())
    assert raw["authority_granted"] is False
    assert raw["deploy_allowed"] is False
    assert raw["state"] == "NOT_APPROVED_NOT_PUBLISHED"
    assert all(value is None for value in raw["source_authorities"]["runtime_approval"].values())
    assert raw["source_authorities"]["host_policy"]["approved_schema2_policy_sha256"] is None
    assert raw["source_authorities"]["profile_approval"]["root_approved_profile_manifest_sha256"] is None
    assert raw["source_authorities"]["one_shot_operator_canary"]["native_root_child_result_accepted"] is False
