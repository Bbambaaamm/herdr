"""Fail-closed offline admission check for operator-proposed QuantLab host grants.

This module NEVER creates, signs, renews or publishes a grant. The privileged
operator must supply the independently reviewed root-owned host-policy document.
Run before privileged activation and again against the installed bytes.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import re
from typing import Any

from herdr.security import SecurityGrant, SecurityError, RiskClass

CONSUMER = "github:Bbambaaamm/Autonomous-Quant-Lab"
WORKSPACE = Path("/home/agentops/workspaces/quantlab")
RESULTS = Path("/home/agentops/.local/state/agent-stack/tasks/results")
MAX_GRANT_HOURS = 168
PINNED_EXECUTOR = re.compile(r"^hermes:[0-9]+\.[0-9]+\.[0-9]+:sha256:[0-9a-f]{64}$")
TOOLS = frozenset({
    "read_file", "search_files", "patch", "write_file",
    "herdr_delegate_child", "herdr_verify_work", "herdr_submit_result",
})
WRITING_TOOLS = frozenset({"patch", "write_file"})
FILESYSTEM_TOOLS = frozenset({"read_file", "search_files", "patch", "write_file"})


class QuantLabPolicyDenied(SecurityError):
    """Safe denial; no model or file system mutation should follow."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise QuantLabPolicyDenied(reason)


def validate_quantlab_template(
    policy: dict[str, Any],
    *,
    at: datetime | None = None,
    workspace: Path = WORKSPACE,
    results: Path = RESULTS,
) -> SecurityGrant:
    """Validate a pre-approved root grant. Never infer approval from intake config."""
    moment = at if at is not None else datetime.now(UTC)
    require(moment.tzinfo is not None, "timezone_aware_clock_required")
    moment = moment.astimezone(UTC)
    require(workspace.is_absolute() and results.is_absolute(), "absolute_roots_required")
    require(workspace == Path(str(workspace)) and results == Path(str(results)),
            "invalid_roots")
    require(type(policy) is dict and type(policy.get("templates")) is dict,
            "closed_host_policy_required")
    require(type(policy.get("schema_version")) is int
            and policy["schema_version"] in (1, 2),
            "unsupported_host_policy_schema")
    require(type(policy.get("host_uid")) is int, "host_uid_required")
    raw = policy["templates"].get(CONSUMER)
    require(type(raw) is dict, "quantlab_template_missing")
    try:
        grant = SecurityGrant.from_dict(raw)
    except (SecurityError, TypeError, ValueError, KeyError) as exc:
        raise QuantLabPolicyDenied("malformed_quantlab_grant") from exc

    require(grant.identity.consumer == CONSUMER, "quantlab_consumer_identity_mismatch")
    require(grant.parent_grant_hash is None and not grant.approvals,
            "root_template_must_not_claim_delegation_or_approval")
    require(grant.is_active(moment), "quantlab_grant_expired_or_not_yet_active")
    expiration = datetime.fromisoformat(grant.expires_at).astimezone(UTC)
    require(expiration <= moment + timedelta(hours=MAX_GRANT_HOURS),
            "quantlab_grant_lifetime_unbounded")
    require(Path(grant.workspace_root) == workspace, "quantlab_workspace_mismatch")
    require(tuple(grant.scope.permissions) == ("workspace-write",),
            "quantlab_permissions_exceed_approved_scope")
    require(set(grant.scope.tools) <= TOOLS, "quantlab_tool_scope_excessive")
    require(set(grant.scope.tools) == TOOLS, "quantlab_required_tools_missing")
    require(set(grant.scope.providers) == {"nous"}
            and len(grant.scope.executors) == 1
            and PINNED_EXECUTOR.fullmatch(grant.scope.executors[0]) is not None,
            "quantlab_unapproved_provider_or_executor")
    require(grant.scope.max_cost_microusd == 0, "quantlab_paid_execution_forbidden")
    require(not grant.process.enabled, "quantlab_process_execution_forbidden")
    require(all(str(ref).startswith("pool:nous:") for ref in grant.credential_refs),
            "quantlab_credential_provider_unapproved")
    require(all(route.provider == "nous" for route in grant.provider_routes),
            "quantlab_provider_route_unapproved")

    rules = {rule.tool: rule for rule in grant.tool_rules}
    require(set(rules) == set(grant.scope.tools), "quantlab_tool_rule_mismatch")
    for name, rule in rules.items():
        require(rule.requires_sandbox, "quantlab_unsandboxed_tool_forbidden")
        require(not rule.requires_process, "quantlab_tool_process_forbidden")
        if name in FILESYSTEM_TOOLS:
            require(rule.path_fields and set(rule.allowed_roots) == {str(workspace)},
                    "quantlab_file_tool_root_excessive")
            require(rule.result_slot is None, "quantlab_file_result_slot_unapproved")
            require(rule.risk == (RiskClass.WORKSPACE_WRITE if name in WRITING_TOOLS
                                  else RiskClass.READ),
                    "quantlab_tool_risk_mismatch")
        elif name == "herdr_submit_result":
            require(set(rule.allowed_roots) == {str(results)},
                    "quantlab_result_root_excessive")
            require(rule.risk == RiskClass.RESULT_SUBMISSION,
                    "quantlab_result_risk_mismatch")
        elif name == "herdr_delegate_child":
            require(rule.risk == RiskClass.DELEGATION, "quantlab_delegation_risk_mismatch")
    return grant


def validate_policy_delta(current: dict[str, Any], proposed: dict[str, Any],
                          *, at: datetime | None = None,
                          workspace: Path = WORKSPACE,
                          results: Path = RESULTS) -> SecurityGrant:
    """Offline pre-publication gate: one added consumer, no policy-wide drift.

    Does not attest administrator approval, immutable release provenance,
    backup/rollback, or application to the root-owned path. Those remain
    mandatory independent operator gates.
    """
    require(type(current) is dict and type(proposed) is dict,
            "closed_policy_documents_required")
    old_templates = current.get("templates")
    new_templates = proposed.get("templates")
    require(type(old_templates) is dict and type(new_templates) is dict,
            "closed_host_policy_required")
    require(CONSUMER not in old_templates,
            "existing_quantlab_grant_requires_explicit_renewal_review")
    require(set(new_templates) == set(old_templates) | {CONSUMER},
            "unreviewed_consumer_change")
    require({key: value for key, value in proposed.items() if key != "templates"}
            == {key: value for key, value in current.items() if key != "templates"},
            "unreviewed_host_policy_change")
    require(all(new_templates[key] == value for key, value in old_templates.items()),
            "unreviewed_existing_consumer_change")
    return validate_quantlab_template(proposed, at=at, workspace=workspace,
                                      results=results)


def main() -> int:
    """Read-only preflight over the trusted, fixed, root-owned policy path."""
    from herdr.host_configuration import HOST_POLICY_CONFIG, _read_configuration

    try:
        policy = _read_configuration(HOST_POLICY_CONFIG)
        validated = validate_quantlab_template(policy)
    except (SecurityError, OSError, ValueError, TypeError, KeyError):
        print("QUANTLAB_HOST_POLICY_BLOCKED")
        return 1
    print("QUANTLAB_HOST_POLICY_VALID " + validated.hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
