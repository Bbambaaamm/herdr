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
    if snapshot.get("active_stops"):
        raise RoutingIntegrationError("active budget stop blocks routing")
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


def record_managed_route(scheduler: Any, route: ManagedRoute) -> bool:
    """Append one idempotent routing audit event to the existing scheduler log."""
    record = scheduler.record_for(route.routing_input.task_id)
    if record.node.id != route.routing_input.task_id:
        raise RoutingIntegrationError("scheduler record identity mismatch")
    if record.policy_profile != route.routing_input.policy_profile:
        raise RoutingIntegrationError("scheduler policy profile mismatch")
    if record.state is not LifecycleState.PENDING:
        raise RoutingIntegrationError("routing selection must precede dispatch")
    return scheduler.audit_log.append_if_absent(
        route.audit_event(),
        identity_fields=("event", "task_id", "attempt", "decision_sha256"),
    )
