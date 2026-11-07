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
        }


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
    failure = classify_failure(
        status_code=observation.status_code,
        message=observation.message,
        model_known=observation.model_known,
    )
    record = scheduler.record_for(task_id)
    if identity.task_id != task_id or record.run_token != identity.run_token:
        raise RoutingIntegrationError("recovery identity is not bound to task record")
    if record.lease is None or record.lease.fencing_token != identity.fencing_token:
        raise RoutingIntegrationError("recovery fence is stale")
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
    scheduler.audit_log.append_if_absent(
        transition.audit_event(),
        identity_fields=(
            "event", "task_id", "run_token", "attempt",
            "failed_executor", "source_decision_sha256",
        ),
    )
    return transition
