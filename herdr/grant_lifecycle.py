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
