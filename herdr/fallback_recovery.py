"""Bounded, durable Router v5 fallback decisions.

This module is deliberately an adapter around the existing routing, scheduler,
budget and audit authorities.  It performs no provider calls and creates no
second ledger or scheduler.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Any

_SHA = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]{1,256}$")

from .routing import (
    FailureKind,
    FailureScope,
    ScopeAttestation,
    classify_failure,
)
from .scheduler_routing import ManagedExecutionHandoff, ManagedRoute, RoutingIntegrationError
from .security import InvocationIdentity


class RecoveryAction(StrEnum):
    FALLBACK = "fallback"
    RECONCILE = "reconcile"
    BLOCK = "block"
    TERMINATE = "terminate"


@dataclass(frozen=True)
class ProviderFailureObservation:
    executor_id: str
    status_code: int | None = None
    message: str = ""
    delivery_uncertain: bool = False
    model_known: bool | None = None
    scope: FailureScope | None = None
    scope_attestation: ScopeAttestation | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.executor_id, str) or not _TOKEN.fullmatch(self.executor_id):
            raise RoutingIntegrationError("failure executor_id required")
        if type(self.delivery_uncertain) is not bool:
            raise RoutingIntegrationError("delivery_uncertain must be boolean")
        if self.status_code is not None and (
            type(self.status_code) is not int or not 100 <= self.status_code <= 599
        ):
            raise RoutingIntegrationError("invalid provider status code")
        if not isinstance(self.message, str):
            raise RoutingIntegrationError("failure message must be text")
        object.__setattr__(
            self,
            "scope",
            FailureScope(self.scope) if self.scope is not None else None,
        )
        if self.scope_attestation is not None and not isinstance(
            self.scope_attestation, ScopeAttestation
        ):
            raise RoutingIntegrationError("typed scope attestation required")


@dataclass(frozen=True)
class FallbackTransition:
    version: int
    action: RecoveryAction
    task_id: str
    run_token: str
    attempt: int
    fencing_token: int
    failed_executor: str
    failure: FailureKind
    failure_scope: FailureScope
    fallback_count: int
    max_fallbacks: int
    reconciliation_required: bool
    source_decision_sha256: str
    next_decision_sha256: str | None = None
    handoff: ManagedExecutionHandoff | None = None

    def __post_init__(self) -> None:
        if self.version != 1:
            raise RoutingIntegrationError("unsupported fallback transition version")
        if type(self.attempt) is not int or self.attempt < 1:
            raise RoutingIntegrationError("fallback attempt must be positive")
        if type(self.fallback_count) is not int or not 0 <= self.fallback_count <= 16:
            raise RoutingIntegrationError("fallback count must be bounded")
        if type(self.max_fallbacks) is not int or not 0 <= self.max_fallbacks <= 16:
            raise RoutingIntegrationError("max fallbacks must be bounded")
        object.__setattr__(self, "action", RecoveryAction(self.action))
        object.__setattr__(self, "failure", FailureKind(self.failure))
        object.__setattr__(self, "failure_scope", FailureScope(self.failure_scope))
        if not isinstance(self.source_decision_sha256, str) or not _SHA.fullmatch(self.source_decision_sha256):
            raise RoutingIntegrationError("source decision digest required")
        if self.next_decision_sha256 is not None and not _SHA.fullmatch(self.next_decision_sha256):
            raise RoutingIntegrationError("next decision digest malformed")
        if type(self.reconciliation_required) is not bool:
            raise RoutingIntegrationError("reconciliation_required must be boolean")
        if self.action is RecoveryAction.FALLBACK and self.handoff is None:
            raise RoutingIntegrationError("fallback transition requires a handoff")
        if self.action is not RecoveryAction.FALLBACK and self.handoff is not None:
            raise RoutingIntegrationError("non-fallback transition cannot carry a handoff")

    def audit_event(self) -> dict[str, Any]:
        handoff = None
        if self.handoff is not None:
            handoff = {
                name: getattr(self.handoff, name)
                for name in (
                    "version", "task_id", "run_token", "attempt", "fencing_token",
                    "consumer", "agent_id", "parent_task_id", "parent_agent_id",
                    "policy_profile", "policy_version", "decision_sha256",
                    "selected_executor", "selected_provider", "selected_model",
                    "registry_hash", "requirement_hash", "parent_scope_hash",
                    "policy_hash", "budget_allocation_id",
                )
            }
        return {
            "event": "managed_fallback_transition",
            "version": self.version,
            "action": self.action.value,
            "task_id": self.task_id,
            "run_token": self.run_token,
            "attempt": self.attempt,
            "fencing_token": self.fencing_token,
            "failed_executor": self.failed_executor,
            "failure": self.failure.value,
            "failure_scope": self.failure_scope.value,
            "fallback_count": self.fallback_count,
            "max_fallbacks": self.max_fallbacks,
            "reconciliation_required": self.reconciliation_required,
            "source_decision_sha256": self.source_decision_sha256,
            "next_decision_sha256": self.next_decision_sha256,
            "handoff": handoff,
        }

    @classmethod
    def from_audit_event(cls, event: dict[str, Any]) -> "FallbackTransition":
        if event.get("event") != "managed_fallback_transition":
            raise RoutingIntegrationError("not a fallback transition event")
        handoff_payload = event.get("handoff")
        handoff = None
        if handoff_payload is not None:
            if not isinstance(handoff_payload, dict):
                raise RoutingIntegrationError("fallback replay handoff malformed")
            handoff = ManagedExecutionHandoff(**handoff_payload)
        return cls(
            version=event["version"], action=event["action"], task_id=event["task_id"],
            run_token=event["run_token"], attempt=event["attempt"],
            fencing_token=event["fencing_token"], failed_executor=event["failed_executor"],
            failure=event["failure"], failure_scope=event["failure_scope"],
            fallback_count=event["fallback_count"], max_fallbacks=event["max_fallbacks"],
            reconciliation_required=event["reconciliation_required"],
            source_decision_sha256=event["source_decision_sha256"],
            next_decision_sha256=event.get("next_decision_sha256"), handoff=handoff,
        )


def _trusted_candidate_scope(
    observation: ProviderFailureObservation,
    *,
    registry_hash: str,
    requirement_hash: str,
) -> bool:
    return (
        observation.scope is FailureScope.CANDIDATE_LOCAL
        and observation.scope_attestation is not None
        and observation.scope_attestation.executor_id == observation.executor_id
        and observation.scope_attestation.scope is FailureScope.CANDIDATE_LOCAL
        and observation.scope_attestation.verifies(registry_hash, requirement_hash)
    )


def _validate_source_route(
    scheduler: Any,
    *,
    task_id: str,
    route: ManagedRoute,
    identity: InvocationIdentity,
    registry: Any,
    requirement: Any,
    policy: Any,
    budget_gate: Any,
    budget_allocation_id: str,
    expected_registry_hash: str,
    expected_requirement_hash: str,
    policy_version: str,
) -> Any:
    record = scheduler.record_for(task_id)
    if route.routing_input.task_id != task_id:
        raise RoutingIntegrationError("stale routing decision task binding")
    if not isinstance(identity, InvocationIdentity):
        raise RoutingIntegrationError("typed recovery identity required")
    if identity.task_id != task_id or identity.consumer != "github:" + record.repo:
        raise RoutingIntegrationError("recovery consumer/task binding is stale")
    if record.run_token is None or identity.run_token != record.run_token:
        raise RoutingIntegrationError("recovery run binding is stale")
    fence = record.lease.fencing_token if record.lease is not None else record.fencing_token
    if fence is None or identity.fencing_token != fence:
        raise RoutingIntegrationError("recovery fence is stale")
    if record.agent_id is None or identity.agent_id != record.agent_id:
        raise RoutingIntegrationError("recovery agent binding is stale")
    if record.parent_task_id != identity.parent_task_id or record.parent_agent_id != identity.parent_agent_id:
        raise RoutingIntegrationError("recovery parent binding is stale")
    if route.routing_input.attempt != record.attempts + 1:
        raise RoutingIntegrationError("stale routing decision attempt")
    if route.routing_input.registry_hash != expected_registry_hash or registry.snapshot.hash != expected_registry_hash:
        raise RoutingIntegrationError("stale routing decision registry")
    if route.routing_input.requirement_hash != expected_requirement_hash or requirement.hash != expected_requirement_hash:
        raise RoutingIntegrationError("stale routing decision requirement")
    if route.routing_input.parent_scope_hash != policy.hash:
        raise RoutingIntegrationError("stale routing decision policy")
    if route.routing_input.policy_version != policy_version:
        raise RoutingIntegrationError("stale routing decision policy version")
    if route.routing_input.budget_allocation_id != budget_allocation_id:
        raise RoutingIntegrationError("stale routing decision budget")
    # This reuses the existing authoritative TaskNode/registry/policy/model
    # binding and WorkBudgetAuthority gate without issuing execution.
    scheduler.prepare_managed_execution_handoff(
        route,
        identity=identity,
        registry=registry,
        requirement=requirement,
        policy=policy,
        budget_gate=budget_gate,
    )
    return record


def decide_managed_fallback(
    scheduler: Any,
    *,
    task_id: str,
    route: ManagedRoute,
    observation: ProviderFailureObservation,
    identity: Any,
    registry: Any,
    requirement: Any,
    policy: Any,
    runtime_state: Any,
    at: str,
    policy_version: str,
    budget_gate: Any,
    budget_allocation_id: str,
    expected_registry_hash: str,
    expected_requirement_hash: str,
    fallback_count: int,
    max_fallbacks: int,
) -> FallbackTransition:
    """Classify one offline provider observation and choose one bounded action.

    Unknown delivery is held for reconciliation.  Terminal policy/budget
    failures and untrusted scopes are fail-closed.  Only an explicitly
    attested candidate-local, retryable failure may select another route.
    """
    if route.decision.selected_executor is None:
        raise RoutingIntegrationError("fallback source route has no authorized executor")
    if observation.executor_id != route.decision.selected_executor:
        raise RoutingIntegrationError("failure executor differs from authorized route")
    failure = classify_failure(
        status_code=observation.status_code,
        message=observation.message,
        model_known=observation.model_known,
    )
    record = _validate_source_route(
        scheduler,
        task_id=task_id,
        route=route,
        identity=identity,
        registry=registry,
        requirement=requirement,
        policy=policy,
        budget_gate=budget_gate,
        budget_allocation_id=budget_allocation_id,
        expected_registry_hash=expected_registry_hash,
        expected_requirement_hash=expected_requirement_hash,
        policy_version=policy_version,
    )
    source_digest = route.decision_sha256
    if observation.delivery_uncertain:
        transition = FallbackTransition(
            1, RecoveryAction.RECONCILE, task_id, identity.run_token, route.routing_input.attempt,
            identity.fencing_token, observation.executor_id, failure, FailureScope.UNKNOWN,
            fallback_count, max_fallbacks, True, source_digest,
        )
    elif failure in (FailureKind.POLICY_DENIED, FailureKind.BUDGET_EXCEEDED, FailureKind.UNKNOWN):
        transition = FallbackTransition(
            1, RecoveryAction.BLOCK, task_id, identity.run_token, route.routing_input.attempt,
            identity.fencing_token, observation.executor_id, failure, FailureScope.UNKNOWN,
            fallback_count, max_fallbacks, False, source_digest,
        )
    elif not _trusted_candidate_scope(
        observation,
        registry_hash=expected_registry_hash,
        requirement_hash=expected_requirement_hash,
    ):
        transition = FallbackTransition(
            1, RecoveryAction.BLOCK, task_id, identity.run_token, route.routing_input.attempt,
            identity.fencing_token, observation.executor_id, failure,
            observation.scope or FailureScope.UNKNOWN, fallback_count, max_fallbacks,
            False, source_digest,
        )
    elif fallback_count >= max_fallbacks or route.routing_input.attempt >= record.node.max_attempts:
        transition = FallbackTransition(
            1, RecoveryAction.TERMINATE, task_id, identity.run_token, route.routing_input.attempt,
            identity.fencing_token, observation.executor_id, failure,
            FailureScope.CANDIDATE_LOCAL, fallback_count, max_fallbacks, False, source_digest,
        )
    else:
        next_route = scheduler.select_managed_route(
            task_id,
            registry=registry,
            requirement=requirement,
            policy=policy,
            runtime_state=runtime_state,
            at=at,
            policy_version=policy_version,
            budget_gate=budget_gate,
            budget_allocation_id=budget_allocation_id,
            identity=identity,
            expected_registry_hash=expected_registry_hash,
            expected_requirement_hash=expected_requirement_hash,
            failed_executors={observation.executor_id: failure},
            failed_scopes={observation.executor_id: FailureScope.CANDIDATE_LOCAL},
            scope_attestations={observation.executor_id: observation.scope_attestation},
            attempt=route.routing_input.attempt + 1,
        )
        handoff = scheduler.prepare_managed_execution_handoff(
            next_route,
            identity=identity,
            registry=registry,
            requirement=requirement,
            policy=policy,
            budget_gate=budget_gate,
        )
        transition = FallbackTransition(
            1, RecoveryAction.FALLBACK, task_id, identity.run_token,
            next_route.routing_input.attempt, identity.fencing_token,
            observation.executor_id, failure, FailureScope.CANDIDATE_LOCAL,
            fallback_count + 1, max_fallbacks, False, source_digest,
            next_route.decision_sha256, handoff,
        )
    event = transition.audit_event()
    try:
        authoritative_event = scheduler.audit_log.append_or_get_strict(
            event,
            identity_fields=(
                "event", "task_id", "run_token", "attempt",
                "failed_executor", "source_decision_sha256",
            ),
        )
    except Exception as exc:
        raise RoutingIntegrationError("fallback replay conflict") from exc
    if authoritative_event != event:
        # A concurrent/restarted caller receives only the durable authoritative
        # result; it cannot publish a newly computed conflicting transition.
        return FallbackTransition.from_audit_event(authoritative_event)
    return transition
