from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from herdr.grant_lifecycle import (GrantLifecycleError, expiry_report,
                                  validate_narrow_renewal)
from tests.herdr.test_heating_activation import source_grant

NOW = datetime(2026, 11, 23, 16, 0, tzinfo=UTC)


def fixtures(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    base = source_grant(str(workspace))
    old = replace(base, issued_at=(NOW-timedelta(days=7)).isoformat(),
                  expires_at=(NOW-timedelta(hours=1)).isoformat())
    proposed = replace(old, grant_id="renewed-different-grant-id",
                       issued_at=NOW.isoformat(),
                       expires_at=(NOW+timedelta(hours=12)).isoformat(),
                       identity=replace(old.identity, run_token="new-run-token"))
    consumer=old.identity.consumer
    return ({"schema_version":1,"templates":{consumer:old.to_json()}},
            {"schema_version":1,"templates":{consumer:proposed.to_json()}},
            old, proposed, consumer)


def test_expired_consumer_is_reported_and_not_renewed(tmp_path):
    current, candidate, _, _, consumer = fixtures(tmp_path)
    report=expiry_report(current,at=NOW)
    assert report["status"] == "action_required"
    assert report["consumers"][0]["status"] == "expired"
    assert current["templates"][consumer] != candidate["templates"][consumer]


def test_current_and_expiring_boundaries(tmp_path):
    current, _, old, _, consumer=fixtures(tmp_path)
    current["templates"][consumer]=replace(old,expires_at=(NOW+timedelta(hours=47)).isoformat()).to_json()
    assert expiry_report(current,at=NOW)["consumers"][0]["status"] == "expiring"
    current["templates"][consumer]=replace(old,expires_at=(NOW+timedelta(days=3)).isoformat()).to_json()
    assert expiry_report(current,at=NOW)["consumers"][0]["status"] == "current"


def test_narrow_renewal_is_only_a_candidate_check(tmp_path):
    current, candidate, old, proposed, consumer = fixtures(tmp_path)
    validated=validate_narrow_renewal(current,candidate,consumer,at=NOW)
    assert validated.hash == proposed.hash
    assert current["templates"][consumer] == old.to_json()


@pytest.mark.parametrize("fault,reason",[
    ("global", "unrelated_host_configuration_changed"),
    ("other", "renewal_consumer_set_changed"),
    ("tools", "malformed_renewal_grant"),
    ("workspace", "malformed_renewal_grant"),
    ("long", "renewal_lifetime_outside_bounds"),
    ("no_consumer", "renewal_requires_existing_consumer"),
    ("rule", "renewal_security_boundary_changed"),
    ("identity", "renewal_identity_changed"),
    ("fencing", "malformed_renewal_grant"),
    ("approval_risk", "malformed_renewal_grant"),
])
def test_invalid_renewal_denied(tmp_path, fault, reason):
    current, candidate, old, proposed, consumer=fixtures(tmp_path)
    if fault == "global": candidate["host_uid"]=0
    elif fault == "other": candidate["templates"]["github:other"]={}
    elif fault == "tools":
        candidate["templates"][consumer]["scope"]["tools"].append("new_tool")
    elif fault == "workspace": candidate["templates"][consumer]["workspace_root"]="/tmp/foreign"
    elif fault == "long": candidate["templates"][consumer]["expires_at"]=(NOW+timedelta(days=2)).isoformat()
    elif fault == "no_consumer": del candidate["templates"][consumer]
    elif fault == "rule":
        candidate["templates"][consumer]["tool_rules"][0]["requires_sandbox"]=False
    elif fault == "identity": candidate["templates"][consumer]["identity"]["agent_id"]="other"
    elif fault == "fencing": candidate["templates"][consumer]["identity"]["fencing_token"]=0
    elif fault == "approval_risk": candidate["templates"][consumer]["approval_required_for"]=["workspace-write"]
    with pytest.raises(GrantLifecycleError,match=reason):
        validate_narrow_renewal(current,candidate,consumer,at=NOW)


def test_bad_warning_or_clock_fails_closed(tmp_path):
    current,*_=fixtures(tmp_path)
    with pytest.raises(GrantLifecycleError):expiry_report(current,at=NOW.replace(tzinfo=None))
    with pytest.raises(GrantLifecycleError):expiry_report(current,at=NOW,warn_before=timedelta(days=100))


def test_fleet_status_includes_missing_enabled_projects(tmp_path):
    from herdr.grant_lifecycle import fleet_report
    current, _, old, _, consumer = fixtures(tmp_path)
    projects={"schema_version": 1, "consumers": [
        {"consumer":"herdr", "repository":"Bbambaaamm/herdr", "enabled":True},
        {"consumer":"quantlab", "repository":"Bbambaaamm/Autonomous-Quant-Lab", "enabled":True},
        {"consumer":"majak", "repository":"Bbambaaamm/dotacni-majak", "enabled":False},
    ]}
    report=fleet_report(current,projects,at=NOW)
    assert report["status"] == "action_required"
    assert {x["project"]:x["status"] for x in report["projects"]} == {
        "herdr":"expired", "quantlab":"missing", "majak":"missing"}
    assert report["untracked_grants"] == []
    assert consumer in {x["consumer"] for x in report["projects"]}


def test_fleet_rejects_duplicate_intake_and_tracks_orphan_grants(tmp_path):
    from herdr.grant_lifecycle import fleet_report
    current, *_=fixtures(tmp_path)
    p={"schema_version":1, "consumers": [{"consumer":"alpha", "repository":"Org/alpha","enabled":True}]}
    assert fleet_report(current,p,at=NOW)["untracked_grants"] == ["github:Bbambaaamm/herdr"]
    p["consumers"].append(dict(p["consumers"][0]))
    with pytest.raises(GrantLifecycleError,match="duplicate_project_identity"):
        fleet_report(current,p,at=NOW)


def test_renewal_eligibility_requires_live_base_and_never_issues(tmp_path):
    from herdr.grant_lifecycle import assess_renewal_eligibility
    current, _, old, _, consumer=fixtures(tmp_path)
    assert assess_renewal_eligibility(current,consumer,at=NOW) == "expired_requires_fresh_operator_authority"
    assert assess_renewal_eligibility(current,"github:missing",at=NOW) == "missing_authority"
    current["templates"][consumer] = replace(old,expires_at=(NOW+timedelta(minutes=20)).isoformat()).to_json()
    assert assess_renewal_eligibility(current,consumer,at=NOW) == "candidate_requires_active_preapproval"
    current["templates"][consumer] = replace(old,expires_at=(NOW+timedelta(hours=5)).isoformat()).to_json()
    assert assess_renewal_eligibility(current,consumer,at=NOW) == "no_renewal_due"


def test_schema2_fleet_preflight_denies_schema1_and_missing_root_issuer(tmp_path):
    from herdr.grant_lifecycle import schema2_fleet_preflight
    raw, _, _, _, consumer = fixtures(tmp_path)
    inv={"schema_version":1,"consumers":[
        {"consumer":"herdr","repository":"Bbambaaamm/herdr","enabled":True},
        {"consumer":"quantlab","repository":"Bbambaaamm/Autonomous-Quant-Lab","enabled":True},
    ]}
    report=schema2_fleet_preflight(raw,inv,None,at=NOW)
    assert report["status"] == "blocked"
    assert "schema2_host_policy_required" in report["blockers"]
    assert "trusted_issuer_policy_required" in report["blockers"]
    assert "current_project_grants_missing_or_expiring" in report["blockers"]
    assert report["not_authorization"] is True
    assert consumer in report["project_gaps"]


def test_schema2_fleet_hash_mismatch_fails_even_with_structural_opt_in(tmp_path):
    from herdr.grant_lifecycle import schema2_fleet_preflight
    current, _, old, _, consumer=fixtures(tmp_path)
    current["schema_version"]=2
    current["templates"][consumer]=replace(old,
        issued_at=(NOW-timedelta(minutes=1)).isoformat(),
        expires_at=(NOW+timedelta(days=4)).isoformat()).to_json()
    current["private_launch"]={"runtime_publication":{"schema_version":"opaque"},
        "plan_handoff":{"automatic_issuer":True}}
    inv={"schema_version":1,"consumers":[
        {"consumer":"herdr","repository":"Bbambaaamm/herdr","enabled":True}]}
    issuer={"schema_version":"herdr-automatic-launch-plan-1", "host_policy_sha256":"0"*64}
    report=schema2_fleet_preflight(current,inv,issuer,at=NOW)
    assert report["status"] == "blocked"
    assert report["blockers"] == ["issuer_policy_hash_mismatch"]
    assert report["not_authorization"] is True
