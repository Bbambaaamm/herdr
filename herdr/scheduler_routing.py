"""P1-A read-only Router v5 integration for managed TaskGraph nodes.

This adapter binds the existing Router v5 decision to a real TaskNode and the
existing scheduler/budget authorities. It never creates a lease, reservation,
provider registry, or execution permission.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .capability import (
    CapabilityRegistry,
    CapabilityRequirement,
    CapabilityScope,
    RuntimeStateSnapshot,
)
from .evidence import digest
from .routing import FailureKind, FailureScope, RoutingDecision, select_route
from .security import InvocationIdentity
from .taskgraph import LifecycleState, TaskNode

_SHA = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]{1,256}$")


class RoutingIntegrationError(ValueError):
    """A managed routing input or handoff is invalid."""


class BudgetGate(Protocol):
    """The existing WorkBudgetAuthority surface used as a read-only gate."""

    def require_active(self, allocation_id: str, identity: InvocationIdentity, provider: str | None = None) -> None: ...
    def snapshot(self, allocation_id: str) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class RoutingInput:
    task_id: str
    attempt: int
    policy_profile: str
    policy_version: str
    capability_id: str
    parent_scope_hash: str
    task_tools_sha256: str
    task_permissions_sha256: str
    registry_hash: str
    requirement_hash: str
    budget_allocation_id: str
    budget_snapshot_sha256: str

    def __post_init__(self) -> None:
        for name in ("task_id", "policy_profile", "policy_version", "capability_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _TOKEN.fullmatch(value):
                raise RoutingIntegrationError(f"{name} must be a safe token")
        if type(self.attempt) is not int or not 1 <= self.attempt <= 16:
            raise RoutingIntegrationError("attempt must be bounded")
        for name in (
            "parent_scope_hash",
            "task_tools_sha256",
            "task_permissions_sha256",
            "registry_hash",
            "requirement_hash",
            "budget_allocation_id",
            "budget_snapshot_sha256",
        ):
            if not isinstance(getattr(self, name), str) or not _SHA.fullmatch(getattr(self, name)):
                raise RoutingIntegrationError(f"{name} must be lowercase sha256")


@dataclass(frozen=True)
class ManagedRoute:
    routing_input: RoutingInput
    decision: RoutingDecision

    def __post_init__(self) -> None:
        if self.decision.registry_hash != self.routing_input.registry_hash:
            raise RoutingIntegrationError("decision registry hash differs from routing input")
        if self.decision.requirement_hash != self.routing_input.requirement_hash:
            raise RoutingIntegrationError("decision requirement hash differs from routing input")
        if self.decision.policy_version != self.routing_input.policy_version:
            raise RoutingIntegrationError("decision policy version differs from routing input")

    @property
    def decision_sha256(self) -> str:
        return self.decision.digest

    def audit_event(self) -> dict[str, Any]:
        return {
            "event": "routing_decision",
            "version": 1,
            "task_id": self.routing_input.task_id,
            "attempt": self.routing_input.attempt,
            "policy_profile": self.routing_input.policy_profile,
            "policy_version": self.routing_input.policy_version,
            "capability_id": self.routing_input.capability_id,
            "parent_scope_hash": self.routing_input.parent_scope_hash,
            "task_tools_sha256": self.routing_input.task_tools_sha256,
            "task_permissions_sha256": self.routing_input.task_permissions_sha256,
            "registry_hash": self.routing_input.registry_hash,
            "requirement_hash": self.routing_input.requirement_hash,
            "budget_allocation_id": self.routing_input.budget_allocation_id,
            "budget_snapshot_sha256": self.routing_input.budget_snapshot_sha256,
            "decision_sha256": self.decision_sha256,
            "decision": self.decision.to_json(),
        }


def _require_active_budget(
    budget_gate: BudgetGate,
    allocation_id: str,
    identity: InvocationIdentity,
    provider: str | None = None,
) -> None:
    # This is the existing WorkBudgetAuthority method; no fallback authority or
    # alternate calling path is allowed when the authoritative gate rejects.
    budget_gate.require_active(allocation_id, identity, provider)


def _validate_budget_snapshot(
    budget_gate: BudgetGate,
    allocation_id: str,
) -> tuple[Mapping[str, Any], str]:
    snapshot = budget_gate.snapshot(allocation_id)
    if not isinstance(snapshot, Mapping):
        raise RoutingIntegrationError("authoritative budget snapshot required")
    if snapshot.get("version") != 1 or snapshot.get("allocation_id") != allocation_id:
        raise RoutingIntegrationError("budget snapshot identity mismatch")
    # Provider- and scope-specific stops are filtered by the authoritative
    # WorkBudgetAuthority.require_active call below.  The snapshot is
    # informational here; treating any unrelated stop as global would deny
    # otherwise eligible routes and would create a second budget authority.
    if snapshot.get("unknown_measurements"):
        raise RoutingIntegrationError("unknown budget measurement blocks routing")
    return snapshot, digest(dict(snapshot))


def build_routing_input(
    *,
    task: TaskNode,
    registry: CapabilityRegistry,
    requirement: CapabilityRequirement,
    policy: CapabilityScope,
    policy_version: str,
    policy_profile: str,
    budget_gate: BudgetGate,
    budget_allocation_id: str,
    identity: InvocationIdentity,
    expected_registry_hash: str,
    expected_requirement_hash: str,
    attempt: int = 1,
) -> RoutingInput:
    """Build a trusted, read-only input from an opted-in managed TaskNode."""
    routing_policy = task.model_policy.get("routing_v5")
    if not isinstance(routing_policy, Mapping) or routing_policy.get("enabled") is not True:
        raise RoutingIntegrationError("dynamic routing is not enabled for this task")
    declared_profile = routing_policy.get("policy_profile")
    if not isinstance(declared_profile, str) or declared_profile != policy_profile:
        raise RoutingIntegrationError("routing policy profile mismatch")
    declared_registry_hash = routing_policy.get("registry_hash")
    if not isinstance(declared_registry_hash, str) or not _SHA.fullmatch(declared_registry_hash):
        raise RoutingIntegrationError("authoritative registry hash missing")
    declared_scope_hash = routing_policy.get("scope_hash")
    declared_requirement_hash = routing_policy.get("requirement_hash")
    declared_tools_hash = routing_policy.get("requirement_tools_sha256")
    declared_permissions_hash = routing_policy.get("requirement_permissions_sha256")
    for name, value in (
        ("scope_hash", declared_scope_hash),
        ("requirement_hash", declared_requirement_hash),
        ("requirement_tools_sha256", declared_tools_hash),
        ("requirement_permissions_sha256", declared_permissions_hash),
    ):
        if not isinstance(value, str) or not _SHA.fullmatch(value):
            raise RoutingIntegrationError(f"authoritative {name} missing")
    capability_id = routing_policy.get("capability_id")
    if capability_id != requirement.capability_id:
        raise RoutingIntegrationError("routing capability does not match authoritative requirement")
    if declared_requirement_hash != requirement.hash:
        raise RoutingIntegrationError("requirement is not bound to authoritative TaskNode")
    if declared_scope_hash != policy.hash:
        raise RoutingIntegrationError("scope is not bound to authoritative TaskNode")
    if declared_tools_hash != digest(sorted(requirement.tools)):
        raise RoutingIntegrationError("requirement tools are not bound to authoritative TaskNode")
    if declared_permissions_hash != digest(sorted(requirement.permissions)):
        raise RoutingIntegrationError("requirement permissions are not bound to authoritative TaskNode")
    declared_policy_version = routing_policy.get("policy_version")
    if not isinstance(declared_policy_version, str) or declared_policy_version != policy_version:
        raise RoutingIntegrationError("routing policy version mismatch")
    if registry.snapshot.hash != expected_registry_hash or registry.snapshot.hash != declared_registry_hash:
        raise RoutingIntegrationError("stale registry snapshot")
    if requirement.hash != expected_requirement_hash:
        raise RoutingIntegrationError("changed requirement hash")
    if not isinstance(policy, CapabilityScope):
        raise RoutingIntegrationError("typed parent scope required")
    if not set(requirement.tools) <= set(task.tools):
        raise RoutingIntegrationError("requirement tools exceed TaskNode tools")
    if not set(requirement.permissions) <= set(task.permissions):
        raise RoutingIntegrationError("requirement permissions exceed TaskNode permissions")
    if not set(requirement.tools) <= set(policy.tools) or not set(requirement.permissions) <= set(policy.permissions):
        raise RoutingIntegrationError("requirement exceeds parent consumer policy")
    if not isinstance(identity, InvocationIdentity) or identity.task_id != task.id:
        raise RoutingIntegrationError("routing identity must bind to task node")
    _snapshot, snapshot_sha256 = _validate_budget_snapshot(budget_gate, budget_allocation_id)
    _require_active_budget(budget_gate, budget_allocation_id, identity)
    return RoutingInput(
        task_id=task.id,
        attempt=attempt,
        policy_profile=policy_profile,
        policy_version=policy_version,
        capability_id=requirement.capability_id,
        parent_scope_hash=policy.hash,
        task_tools_sha256=digest(sorted(task.tools)),
        task_permissions_sha256=digest(sorted(task.permissions)),
        registry_hash=registry.snapshot.hash,
        requirement_hash=requirement.hash,
        budget_allocation_id=budget_allocation_id,
        budget_snapshot_sha256=snapshot_sha256,
    )


def select_managed_task_route(
    *,
    task: TaskNode,
    registry: CapabilityRegistry,
    requirement: CapabilityRequirement,
    policy: CapabilityScope,
    runtime_state: Sequence[RuntimeStateSnapshot],
    at: str,
    policy_version: str,
    policy_profile: str,
    budget_gate: BudgetGate,
    budget_allocation_id: str,
    identity: InvocationIdentity,
    expected_registry_hash: str,
    expected_requirement_hash: str,
    failed_executors: Mapping[str, FailureKind] | None = None,
    failed_scopes: Mapping[str, FailureScope] | None = None,
    attempt: int = 1,
) -> ManagedRoute:
    """Select a route without dispatching or reserving an economic operation."""
    routing_input = build_routing_input(
        task=task,
        registry=registry,
        requirement=requirement,
        policy=policy,
        policy_version=policy_version,
        policy_profile=policy_profile,
        budget_gate=budget_gate,
        budget_allocation_id=budget_allocation_id,
        identity=identity,
        expected_registry_hash=expected_registry_hash,
        expected_requirement_hash=expected_requirement_hash,
        attempt=attempt,
    )
    decision = select_route(
        registry,
        requirement,
        policy,
        runtime_state,
        at=at,
        policy_version=policy_version,
        max_attempts=task.max_attempts,
        failed_executors=failed_executors,
        failed_scopes=failed_scopes,
    )
    if decision.selected_provider is not None:
        _require_active_budget(
            budget_gate,
            budget_allocation_id,
            identity,
            provider=decision.selected_provider,
        )
    return ManagedRoute(routing_input, decision)


@dataclass(frozen=True)
class ManagedExecutionHandoff:
    """Immutable, single-route handoff to the existing host execution gate."""

    version: int
    task_id: str
    run_token: str
    attempt: int
    fencing_token: int
    consumer: str
    parent_task_id: str | None
    parent_agent_id: str | None
    policy_profile: str
    policy_version: str
    decision_sha256: str
    selected_executor: str
    selected_provider: str
    selected_model: str
    registry_hash: str
    requirement_hash: str
    parent_scope_hash: str
    policy_hash: str
    budget_allocation_id: str

    def __post_init__(self) -> None:
        if self.version != 1:
            raise RoutingIntegrationError("unsupported execution handoff version")
        for name in ("task_id", "run_token", "consumer", "policy_profile", "policy_version",
                     "selected_executor", "selected_provider", "selected_model"):
            if not isinstance(getattr(self, name), str) or not _TOKEN.fullmatch(getattr(self, name)):
                raise RoutingIntegrationError(f"{name} must be a safe token")
        for name in ("decision_sha256", "registry_hash", "requirement_hash",
                     "parent_scope_hash", "policy_hash", "budget_allocation_id"):
            if not isinstance(getattr(self, name), str) or not _SHA.fullmatch(getattr(self, name)):
                raise RoutingIntegrationError(f"{name} must be lowercase sha256")
        for name in ("parent_task_id", "parent_agent_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not _TOKEN.fullmatch(value)):
                raise RoutingIntegrationError(f"{name} must be a safe token or null")
        if type(self.attempt) is not int or not 1 <= self.attempt <= 16:
            raise RoutingIntegrationError("handoff attempt must be bounded")
        if type(self.fencing_token) is not int or self.fencing_token <= 0:
            raise RoutingIntegrationError("handoff fencing token must be positive")
        if self.policy_hash != self.parent_scope_hash:
            raise RoutingIntegrationError("handoff policy hash is not the parent scope hash")

    def authorize_identity(
        self,
        *,
        identity: InvocationIdentity,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        """Revalidate the immutable handoff identity and selected route."""
        if not isinstance(identity, InvocationIdentity):
            raise RoutingIntegrationError("typed invocation identity required")
        if provider is not None and provider != self.selected_provider:
            raise RoutingIntegrationError("execution handoff provider mismatch")
        if model is not None and model != self.selected_model:
            raise RoutingIntegrationError("execution handoff model mismatch")
        expected = {
            "consumer": self.consumer,
            "task_id": self.task_id,
            "run_token": self.run_token,
            "fencing_token": self.fencing_token,
            "parent_task_id": self.parent_task_id,
            "parent_agent_id": self.parent_agent_id,
        }
        for name, value in expected.items():
            if getattr(identity, name) != value:
                raise RoutingIntegrationError("execution handoff identity mismatch")

    def authorize(
        self,
        *,
        identity: InvocationIdentity,
        budget_gate: BudgetGate,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        """Revalidate identity, selected route and current provider budget."""
        self.authorize_identity(identity=identity, provider=provider, model=model)
        _require_active_budget(budget_gate, self.budget_allocation_id, identity, self.selected_provider)


def build_execution_handoff(
    *,
    scheduler: Any,
    route: ManagedRoute,
    identity: InvocationIdentity,
    registry: CapabilityRegistry,
    requirement: CapabilityRequirement,
    policy: CapabilityScope,
    budget_gate: BudgetGate,
) -> ManagedExecutionHandoff:
    """Bind one selected route to an existing scheduler record and budget gate."""
    record = scheduler.record_for(route.routing_input.task_id)
    _validate_authoritative_route_binding(record, route)
    if not isinstance(identity, InvocationIdentity) or identity.task_id != record.node.id:
        raise RoutingIntegrationError("handoff identity is not bound to scheduler record")
    if identity.consumer != "github:" + record.repo:
        raise RoutingIntegrationError("handoff consumer is not bound to scheduler record")
    if record.run_token is None or identity.run_token != record.run_token:
        raise RoutingIntegrationError("handoff run token is not bound to scheduler record")
    fence = record.lease.fencing_token if record.lease is not None else record.fencing_token
    if fence is None or identity.fencing_token != fence:
        raise RoutingIntegrationError("handoff fencing token is not bound to scheduler record")
    if record.parent_task_id != identity.parent_task_id or record.parent_agent_id != identity.parent_agent_id:
        raise RoutingIntegrationError("handoff parent identity is not bound to scheduler record")
    decision = route.decision
    if any(value is None for value in (decision.selected_model, decision.selected_provider, decision.selected_executor)):
        raise RoutingIntegrationError("only a successful route can be handed off")
    if registry.snapshot.hash != route.routing_input.registry_hash or requirement.hash != route.routing_input.requirement_hash:
        raise RoutingIntegrationError("handoff capability evidence is stale")
    if policy.hash != route.routing_input.parent_scope_hash:
        raise RoutingIntegrationError("handoff policy evidence is stale")
    capabilities = {item.id: item for item in registry.snapshot.capabilities}
    providers = {item.id: item for item in registry.snapshot.providers}
    executors = {item.id: item for item in registry.snapshot.executors}
    capability_desc = capabilities.get(requirement.capability_id)
    provider_desc = providers.get(decision.selected_provider)
    executor_desc = executors.get(decision.selected_executor)
    if (capability_desc is None or provider_desc is None or executor_desc is None
            or executor_desc.provider_id != decision.selected_provider
            or executor_desc.capability_id != requirement.capability_id
            or capability_desc.spec_id != decision.selected_model
            or requirement.capability_id not in provider_desc.capability_refs
            or decision.selected_provider not in policy.providers
            or decision.selected_executor not in policy.executors):
        raise RoutingIntegrationError("handoff selected capability/model is not authorized")
    _require_active_budget(budget_gate, route.routing_input.budget_allocation_id, identity, decision.selected_provider)
    return ManagedExecutionHandoff(
        version=1,
        task_id=route.routing_input.task_id,
        run_token=identity.run_token,
        attempt=route.routing_input.attempt,
        fencing_token=identity.fencing_token,
        consumer=identity.consumer,
        parent_task_id=identity.parent_task_id,
        parent_agent_id=identity.parent_agent_id,
        policy_profile=route.routing_input.policy_profile,
        policy_version=route.routing_input.policy_version,
        decision_sha256=route.decision_sha256,
        selected_executor=decision.selected_executor,
        selected_provider=decision.selected_provider,
        selected_model=decision.selected_model,
        registry_hash=route.routing_input.registry_hash,
        requirement_hash=route.routing_input.requirement_hash,
        parent_scope_hash=route.routing_input.parent_scope_hash,
        policy_hash=policy.hash,
        budget_allocation_id=route.routing_input.budget_allocation_id,
    )


def _validate_authoritative_route_binding(record: Any, route: ManagedRoute) -> None:
    """Prove the route was built from the scheduler's exact TaskNode bindings."""
    node = getattr(record, "node", None)
    if not isinstance(node, TaskNode) or node.id != route.routing_input.task_id:
        raise RoutingIntegrationError("route is not bound to authoritative TaskNode")
    routing_policy = node.model_policy.get("routing_v5")
    if not isinstance(routing_policy, Mapping) or routing_policy.get("enabled") is not True:
        raise RoutingIntegrationError("route TaskNode has no authoritative routing binding")
    expected = {
        "policy_profile": route.routing_input.policy_profile,
        "policy_version": route.routing_input.policy_version,
        "capability_id": route.routing_input.capability_id,
        "scope_hash": route.routing_input.parent_scope_hash,
        "requirement_hash": route.routing_input.requirement_hash,
        "registry_hash": route.routing_input.registry_hash,
    }
    for key, value in expected.items():
        if routing_policy.get(key) != value:
            raise RoutingIntegrationError("route is not bound to authoritative TaskNode")
    if route.routing_input.task_tools_sha256 != digest(sorted(node.tools)):
        raise RoutingIntegrationError("route task tools are not bound to authoritative TaskNode")
    if route.routing_input.task_permissions_sha256 != digest(sorted(node.permissions)):
        raise RoutingIntegrationError("route task permissions are not bound to authoritative TaskNode")


def record_managed_route(scheduler: Any, route: ManagedRoute) -> bool:
    """Append one idempotent routing audit event to the existing scheduler log."""
    record = scheduler.record_for(route.routing_input.task_id)
    if record.node.id != route.routing_input.task_id:
        raise RoutingIntegrationError("scheduler record identity mismatch")
    _validate_authoritative_route_binding(record, route)
    if record.policy_profile != route.routing_input.policy_profile:
        raise RoutingIntegrationError("scheduler policy profile mismatch")
    if record.state is not LifecycleState.PENDING:
        raise RoutingIntegrationError("routing selection must precede dispatch")
    return scheduler.audit_log.append_if_absent(
        route.audit_event(),
        identity_fields=("event", "task_id", "attempt", "decision_sha256"),
    )
