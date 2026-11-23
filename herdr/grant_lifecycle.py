"""Read-only host grant expiry readiness and bounded renewal comparison.

This never creates, signs, extends or publishes an authorization. Root-owned
operator approvals are outside this module, and validity cannot be inferred
from these reports.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from .security import SecurityError, SecurityGrant


class GrantLifecycleError(SecurityError):
    """A proposed renewal violates the retained security ceiling."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise GrantLifecycleError(reason)


def _timestamp(value: str) -> datetime:
    try:
        moment = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise GrantLifecycleError("invalid_grant_timestamp") from exc
    _require(moment.tzinfo is not None, "timezone_aware_grant_required")
    return moment.astimezone(UTC)


def expiry_report(policy: dict[str, Any], *, at: datetime | None = None,
                  warn_before: timedelta = timedelta(hours=48)) -> dict[str, Any]:
    """Generate a deterministic, redacted expiry report without any renewal side effect."""
    moment = at if at is not None else datetime.now(UTC)
    _require(isinstance(moment, datetime) and moment.tzinfo is not None,
             "timezone_aware_clock_required")
    _require(timedelta(0) < warn_before <= timedelta(days=7),
             "bounded_warning_horizon_required")
    _require(type(policy) is dict and type(policy.get("templates")) is dict,
             "closed_host_templates_required")
    templates = policy["templates"]
    _require(len(templates) <= 32, "bounded_host_consumers_required")
    entries = []
    for consumer, raw in sorted(templates.items()):
        _require(type(consumer) is str and type(raw) is dict,
                 "malformed_host_consumer")
        try:
            grant = SecurityGrant.from_dict(raw)
        except (SecurityError, ValueError, TypeError, KeyError) as exc:
            raise GrantLifecycleError("malformed_host_grant") from exc
        _require(grant.identity.consumer == consumer,
                 "host_grant_consumer_mismatch")
        expiry = _timestamp(grant.expires_at)
        issued = _timestamp(grant.issued_at)
        _require(issued < expiry, "invalid_grant_interval")
        remaining = int((expiry - moment.astimezone(UTC)).total_seconds())
        status = "expired" if remaining <= 0 else (
            "expiring" if remaining <= warn_before.total_seconds() else "current")
        entries.append({"consumer": consumer, "status": status,
                        "expires_at": expiry.isoformat(),
                        "remaining_seconds": remaining})
    return {"status": "action_required" if any(x["status"] != "current" for x in entries)
            else "current", "consumers": entries}


def validate_narrow_renewal(current: dict[str, Any], proposed: dict[str, Any],
                            consumer: str, *, at: datetime | None = None,
                            max_lifetime: timedelta = timedelta(hours=24)) -> SecurityGrant:
    """Validate a *review candidate*, never infer authority from an expired grant.

    A trusted root issuer must independently establish current authorization,
    origin, reviewer approval and publication after this purely mechanical check.
    """
    moment = at if at is not None else datetime.now(UTC)
    _require(isinstance(moment, datetime) and moment.tzinfo is not None,
             "timezone_aware_clock_required")
    _require(timedelta(0) < max_lifetime <= timedelta(days=7),
             "bounded_renewal_lifetime_required")
    _require(type(current) is dict and type(proposed) is dict
             and type(current.get("templates")) is dict
             and type(proposed.get("templates")) is dict,
             "closed_host_policy_required")
    before, after = current["templates"], proposed["templates"]
    _require(consumer in before and consumer in after,
             "renewal_requires_existing_consumer")
    _require(set(before) == set(after), "renewal_consumer_set_changed")
    _require(all(after[key] == value for key, value in before.items() if key != consumer),
             "unrelated_consumer_changed")
    _require({key: value for key, value in current.items() if key != "templates"}
             == {key: value for key, value in proposed.items() if key != "templates"},
             "unrelated_host_configuration_changed")
    try:
        old = SecurityGrant.from_dict(before[consumer])
        new = SecurityGrant.from_dict(after[consumer])
    except (SecurityError, ValueError, TypeError, KeyError) as exc:
        raise GrantLifecycleError("malformed_renewal_grant") from exc
    _require(old.identity.consumer == consumer == new.identity.consumer,
             "renewal_consumer_identity_changed")
    _require(old.parent_grant_hash is None and new.parent_grant_hash is None
             and not new.approvals, "renewal_requires_root_operator_authority")
    start, end = _timestamp(new.issued_at), _timestamp(new.expires_at)
    _require(start <= moment.astimezone(UTC) < end
             and end - start <= max_lifetime,
             "renewal_lifetime_outside_bounds")
    _require(new.workspace_root == old.workspace_root
             and new.process == old.process
             and new.runtime_assurance == old.runtime_assurance
             and new.provider_routes == old.provider_routes
             and new.credential_refs == old.credential_refs
             and new.tool_rules == old.tool_rules
             and new.approval_required_for == old.approval_required_for
             and new.schema_version == old.schema_version,
             "renewal_security_boundary_changed")
    _require(new.scope.is_subset_of(old.scope), "renewal_scope_expanded")
    _require(new.identity.agent_id == old.identity.agent_id
             and new.identity.parent_agent_id == old.identity.parent_agent_id
             and new.identity.parent_task_id == old.identity.parent_task_id
             and new.identity.task_id == old.identity.task_id
             and new.identity.fencing_token >= old.identity.fencing_token,
             "renewal_identity_changed")
    return new


def main() -> int:
    """Stable root-owned host-policy read, no secrets, no mutations."""
    import json
    from .host_configuration import HOST_POLICY_CONFIG, _read_configuration
    try:
        report = expiry_report(_read_configuration(HOST_POLICY_CONFIG))
    except (SecurityError, OSError, ValueError, TypeError):
        print("HOST_GRANT_LIFECYCLE_BLOCKED")
        return 2
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["status"] == "current" else 1


if __name__ == "__main__":
    raise SystemExit(main())


def fleet_report(policy: dict[str, Any], intake: dict[str, Any], *,
                 at: datetime | None = None) -> dict[str, Any]:
    """Read-only cross-project observability; intake is NOT a grant authority.

    Repository identities come from intake metadata only. Every missing grant
    remains missing, even if a project was enabled or its issue was approved.
    """
    _require(type(intake) is dict and type(intake.get("consumers")) is list
             and intake.get("schema_version") == 1,
             "closed_intake_inventory_required")
    rows = intake["consumers"]
    _require(len(rows) <= 32, "bounded_intake_inventory_required")
    base = expiry_report(policy, at=at)
    grants = {row["consumer"]: row for row in base["consumers"]}
    observed = set()
    projects = []
    for row in rows:
        _require(type(row) is dict and type(row.get("enabled")) is bool
                 and type(row.get("consumer")) is str
                 and type(row.get("repository")) is str,
                 "invalid_intake_project")
        name = row["consumer"]
        repository = row["repository"]
        _require(name and repository.count("/") == 1
                 and not any(char.isspace() for char in repository),
                 "invalid_intake_project_identity")
        canonical = "github:" + repository
        _require(name not in observed and canonical not in observed,
                 "duplicate_project_identity")
        observed.update((name, canonical))
        grant = grants.get(canonical)
        projects.append({"project": name, "consumer": canonical,
                         "enabled": row["enabled"],
                         "status": grant["status"] if grant else "missing",
                         "expires_at": grant["expires_at"] if grant else None})
    projects.sort(key=lambda row: row["consumer"])
    tracked = {row["consumer"] for row in projects}
    orphan = sorted(set(grants) - tracked)
    attention = any(row["enabled"] and row["status"] != "current"
                    for row in projects) or bool(orphan)
    return {"status": "action_required" if attention else "current",
            "projects": projects, "untracked_grants": orphan}


def assess_renewal_eligibility(policy: dict[str, Any], consumer: str,
                               *, at: datetime | None = None,
                               min_remaining: timedelta = timedelta(minutes=30)) -> str:
    """Non-authoritative preflight before an independently approved renewal.

    Returns status only. Eligibility CANNOT authorize issuance or publication.
    Rejects a missing/expired base grant even when an old document exists.
    """
    moment = at if at is not None else datetime.now(UTC)
    _require(type(consumer) is str and bool(consumer), "consumer_required")
    _require(timedelta(0) < min_remaining <= timedelta(hours=48),
             "bounded_renewal_window_required")
    report = expiry_report(policy, at=moment,
                           warn_before=min_remaining)
    current = next((x for x in report["consumers"]
                    if x["consumer"] == consumer), None)
    if current is None:
        return "missing_authority"
    if current["status"] == "expired":
        return "expired_requires_fresh_operator_authority"
    if current["status"] == "expiring":
        return "candidate_requires_active_preapproval"
    return "no_renewal_due"
