"""Host-only construction of #76 grants from admitted, typed authority.

Call this in the scheduler after admission and physical runtime observation.
Never pass a model response, prompt, or tool arguments into this interface.
"""
from __future__ import annotations

from dataclasses import dataclass

from herdr.capability import CapabilityScope, RegistrySnapshot
from herdr.security import (
    ApprovalEvidence, InvocationIdentity, ProcessPolicy, ProviderRoute,
    RiskClass, RuntimeAssurance, SecurityError, SecurityGrant, ToolRule,
)


@dataclass(frozen=True)
class BrokerRoute:
    """Host broker inventory for an exact provider transport and opaque refs."""

    provider: str
    base_url: str
    api_mode: str
    credential_refs: tuple[str, ...]


@dataclass(frozen=True)
class HostGrantContext:
    """Trusted scheduler identity and lifetime; never built from agent content."""

    grant_id: str
    workspace_root: str
    identity: InvocationIdentity
    issued_at: str
    expires_at: str
    approvals: tuple[ApprovalEvidence, ...] = ()
    approval_required_for: tuple[RiskClass, ...] = ()


def build_host_grant(
    *, context: HostGrantContext, scope: CapabilityScope,
    tool_rules: tuple[ToolRule, ...], process: ProcessPolicy,
    parent: SecurityGrant | None, registry: RegistrySnapshot,
    broker_inventory: tuple[BrokerRoute, ...],
    assurance: RuntimeAssurance,
) -> SecurityGrant:
    """Derive routes from registry policy and broker inventory, then validate delegation.

    The broker must separately bind each *effective request-local* credential
    after any refresh to one of these signed refs. A route's singleton ref is
    never evidence of which key was actually selected.
    """
    if not isinstance(context, HostGrantContext) or not isinstance(context.identity, InvocationIdentity):
        raise SecurityError("trusted scheduler context required")
    if not isinstance(scope, CapabilityScope) or not isinstance(process, ProcessPolicy):
        raise SecurityError("admitted typed scope and process policy required")
    if not isinstance(assurance, RuntimeAssurance) or not isinstance(registry, RegistrySnapshot):
        raise SecurityError("typed runtime observation and registry required")
    if not isinstance(broker_inventory, tuple) or any(not isinstance(x, BrokerRoute) for x in broker_inventory):
        raise SecurityError("typed host broker inventory required")
    if parent is not None and not isinstance(parent, SecurityGrant):
        raise SecurityError("exact typed parent grant required")
    providers = {item.id: item for item in registry.providers}
    capabilities = {item.id: item for item in registry.capabilities}
    executors = {item.id: item for item in registry.executors}
    inventory = {item.provider: item for item in broker_inventory}
    if len(inventory) != len(broker_inventory) or set(inventory) != set(scope.providers):
        raise SecurityError("broker inventory must exactly cover admitted providers")
    if not set(scope.providers) <= set(providers) or not set(scope.capabilities) <= set(capabilities):
        raise SecurityError("admitted provider/capability absent from registry")
    if not set(scope.executors) <= set(executors):
        raise SecurityError("admitted executor absent from registry")
    for executor_id in scope.executors:
        executor = executors[executor_id]
        if (executor.provider_id not in scope.providers
                or executor.capability_id not in scope.capabilities):
            raise SecurityError("admitted executor is outside provider/capability scope")
        if not set(scope.tools) <= set(executor.tools):
            raise SecurityError("admitted tools exceed executor metadata")
    routes = []
    refs = set()
    for provider_id in scope.providers:
        provider = providers[provider_id]
        broker = inventory[provider_id]
        selected_caps = [capabilities[executors[e].capability_id] for e in scope.executors
                         if executors[e].provider_id == provider_id]
        modes = {executors[e].transport_mode for e in scope.executors
                 if executors[e].provider_id == provider_id}
        if modes != {broker.api_mode} or broker.api_mode not in provider.transport_modes:
            raise SecurityError("broker API mode differs from registry executor")
        regions = set(scope.regions) & set(provider.data_policy.regions)
        classes = set(scope.data_classes) & set(provider.data_policy.data_classes)
        for capability in selected_caps:
            regions &= set(capability.data_policy.regions)
            classes &= set(capability.data_policy.data_classes)
            if (list(type(scope.max_egress)).index(capability.data_policy.egress) >
                    list(type(scope.max_egress)).index(scope.max_egress)
                    or list(type(scope.max_retention)).index(capability.data_policy.retention) >
                    list(type(scope.max_retention)).index(scope.max_retention)
                    or capability.data_policy.training != scope.training):
                raise SecurityError("registry capability data policy exceeds admitted scope")
        if len(regions) != 1 or len(classes) != 1:
            raise SecurityError("provider region or data class is ambiguous")
        if (list(type(scope.max_egress)).index(provider.data_policy.egress) >
                list(type(scope.max_egress)).index(scope.max_egress)
                or list(type(scope.max_retention)).index(provider.data_policy.retention) >
                list(type(scope.max_retention)).index(scope.max_retention)
                or provider.data_policy.training != scope.training):
            raise SecurityError("registry provider data policy exceeds admitted scope")
        route = ProviderRoute(
            provider=provider_id, base_url=broker.base_url, api_mode=broker.api_mode,
            regions=tuple(regions), data_classes=tuple(classes),
            max_egress=provider.data_policy.egress,
            max_retention=provider.data_policy.retention,
            training=provider.data_policy.training,
            credential_refs=broker.credential_refs,
        )
        routes.append(route)
        refs.update(route.credential_refs)
    grant = SecurityGrant(
        grant_id=context.grant_id, workspace_root=context.workspace_root,
        identity=context.identity, scope=scope, tool_rules=tool_rules,
        process=process, runtime_assurance=assurance,
        provider_routes=tuple(routes), credential_refs=tuple(sorted(refs)),
        approvals=context.approvals, approval_required_for=context.approval_required_for,
        issued_at=context.issued_at, expires_at=context.expires_at,
        parent_grant_hash=parent.hash if parent is not None else None,
    )
    if parent is not None:
        grant.require_subset_of(parent)
    return grant
