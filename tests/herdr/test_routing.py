"""Focused Router v5 contract regressions (offline only)."""
from dataclasses import replace

import pytest

from herdr.capability import Health
from herdr.routing import (
    FailureKind,
    RoutingDecision,
    RoutingError,
    bounded_fallback,
    classify_failure,
    select_route,
)
from tests.herdr.test_capability import NOW, fixture


def test_deterministic_decision_and_versioned_payload():
    registry, scope, requirement, states = fixture()
    decision = select_route(
        registry, requirement, scope, states, at=NOW, policy_version="router-v5-policy-1"
    )
    assert decision.selected_provider == "a"
    assert decision.selected_model == "logical-spec"
    assert decision.selected_executor == "a-runtime"
    assert decision.schema_version == "1.0.0"
    assert RoutingDecision.from_json(decision.to_json()).digest == decision.digest

    reversed_states = tuple(reversed(states))
    again = select_route(
        registry, requirement, scope, reversed_states, at=NOW, policy_version="router-v5-policy-1"
    )
    assert again.to_json() == decision.to_json()


def test_bounded_fallback_keeps_registry_constraints_and_stops():
    registry, scope, requirement, states = fixture()
    decision = bounded_fallback(
        registry, requirement, scope, states, at=NOW,
        policy_version="router-v5-policy-1",
        failed_executors={"a-runtime": FailureKind.PROVIDER_UNAVAILABLE},
        max_attempts=2,
    )
    assert decision.selected_provider == "b"
    assert decision.selected_executor == "b-runtime"
    assert "bounded_fallback" in decision.reasons
    assert decision.rejected_candidates[-1].failure is FailureKind.PROVIDER_UNAVAILABLE
    assert decision.attempted_fallbacks == ("a-runtime",)

    changed_states = tuple(
        replace(state, health=Health.UNAVAILABLE, reason_code="maintenance")
        if state.executor_id == "a-runtime" else state
        for state in states
    )
    changed = bounded_fallback(
        registry, requirement, scope, changed_states, at=NOW,
        policy_version="router-v5-policy-1",
        failed_executors={"a-runtime": FailureKind.PROVIDER_UNAVAILABLE},
        max_attempts=2,
    )
    assert changed.selected_executor == "b-runtime"

    exhausted = bounded_fallback(
        registry, requirement, scope, states, at=NOW,
        policy_version="router-v5-policy-1",
        failed_executors={
            "a-runtime": FailureKind.PROVIDER_UNAVAILABLE,
            "b-runtime": FailureKind.RATE_LIMITED,
        },
        max_attempts=2,
    )
    assert exhausted.selected_executor is None
    assert exhausted.attempts == 2
    reverse = bounded_fallback(
        registry, requirement, scope, states, at=NOW,
        policy_version="router-v5-policy-1",
        failed_executors={
            "b-runtime": FailureKind.RATE_LIMITED,
            "a-runtime": FailureKind.PROVIDER_UNAVAILABLE,
        },
        max_attempts=2,
    )
    assert reverse.to_json() == exhausted.to_json()
    terminal_event = exhausted.to_telemetry_event(
        sequence=3, timestamp="2026-10-02T10:00:12+00:00", issue="79",
        task_id="router-test-exhausted", attempt=2, agent_id="hermes", role="router",
    )
    assert terminal_event.event_type.value == "model_fallback"
    assert terminal_event.fallback_chain == ("a-runtime", "b-runtime")

    with pytest.raises(RoutingError, match="compatible"):
        bounded_fallback(
            registry, requirement, scope, states, at=NOW,
            policy_version="router-v5-policy-1",
            failed_executors={"ghost-runtime": FailureKind.PROVIDER_UNAVAILABLE},
            max_attempts=2,
        )

    denied_scope = replace(scope, providers=("ghost-provider",), executors=("ghost-runtime",))
    denied = bounded_fallback(
        registry, requirement, denied_scope, states, at=NOW,
        policy_version="router-v5-policy-1",
        failed_executors={},
        max_attempts=2,
    )
    assert denied.selected_executor is None
    assert denied.failure is FailureKind.POLICY_DENIED
    with pytest.raises(RoutingError, match="compatible"):
        bounded_fallback(
            registry, requirement, denied_scope, states, at=NOW,
            policy_version="router-v5-policy-1",
            failed_executors={"a-runtime": FailureKind.PROVIDER_UNAVAILABLE},
            max_attempts=2,
        )

    mixed_states = tuple(
        replace(
            state,
            health=Health.UNAVAILABLE,
            reason_code="maintenance",
        ) if state.executor_id == "a-runtime" else replace(
            state,
            estimated_cost_microusd=200,
            requirement_hash=requirement.hash,
        )
        for state in states
    )
    mixed_a = bounded_fallback(
        registry, requirement, scope, mixed_states, at=NOW,
        policy_version="router-v5-policy-1",
        failed_executors={"a-runtime": FailureKind.PROVIDER_UNAVAILABLE},
        max_attempts=2,
    )
    mixed_b = bounded_fallback(
        registry, requirement, scope, mixed_states, at=NOW,
        policy_version="router-v5-policy-1",
        failed_executors={"a-runtime": FailureKind.PROVIDER_UNAVAILABLE},
        max_attempts=2,
    )
    assert mixed_a.failure is FailureKind.BUDGET_EXCEEDED
    assert mixed_a.to_json() == mixed_b.to_json()


def test_failure_taxonomy_laguna_and_claude_credit_cases():
    assert classify_failure(
        status_code=404, message="model not found: laguna-s-2.1:free", model_known=False
    ) is FailureKind.MODEL_NOT_FOUND
    assert classify_failure(
        status_code=404, message="insufficient credits for Claude Opus 5.5", model_known=True
    ) is FailureKind.INSUFFICIENT_CREDITS
    assert classify_failure(status_code=429, message="rate limit") is FailureKind.RATE_LIMITED
    assert classify_failure(status_code=503, message="upstream unavailable") is FailureKind.PROVIDER_UNAVAILABLE
    assert classify_failure(message="policy denied") is FailureKind.POLICY_DENIED
    assert classify_failure(message="budget exceeded") is FailureKind.BUDGET_EXCEEDED
    assert classify_failure(status_code=418, message="opaque") is FailureKind.UNKNOWN
    assert classify_failure(status_code=429, message="policy denied by budget gate") is FailureKind.POLICY_DENIED
    assert classify_failure(status_code=404, message="model not found; budget exceeded") is FailureKind.BUDGET_EXCEEDED


def test_telemetry_projection_distinguishes_attempted_fallbacks():
    registry, scope, requirement, states = fixture()
    decision = select_route(
        registry, requirement, scope, states, at=NOW, policy_version="router-v5-policy-1",
        failed_executors={"a-runtime": FailureKind.RATE_LIMITED}, max_attempts=2,
    )
    event = decision.to_telemetry_event(
        sequence=1, timestamp="2026-10-02T10:00:10+00:00", issue="79",
        task_id="router-test", attempt=1, agent_id="hermes", role="router",
    )
    assert event.router_decision == decision.digest
    assert event.event_type.value == "model_fallback"
    assert event.fallback_chain == ("a-runtime",)
    assert event.blocker is None

    denied_scope = replace(scope, providers=("ghost-provider",), executors=("ghost-runtime",))
    denied = select_route(
        registry, requirement, denied_scope, states, at=NOW,
        policy_version="router-v5-policy-1",
    )
    denied_event = denied.to_telemetry_event(
        sequence=2, timestamp="2026-10-02T10:00:11+00:00", issue="79",
        task_id="router-test-denied", attempt=1, agent_id="hermes", role="router",
    )
    assert denied_event.event_type.value == "model_route"
    assert denied_event.fallback_chain == ()
    assert denied_event.blocker == "POLICY_DENIED"


def test_no_candidate_is_fail_closed_for_provider_unavailable():
    registry, scope, requirement, states = fixture()
    changed_states = tuple(
        replace(state, health=Health.UNAVAILABLE, reason_code="maintenance")
        for state in states
    )
    decision = select_route(
        registry, requirement, scope, changed_states, at=NOW, policy_version="router-v5-policy-1"
    )
    assert decision.selected_executor is None
    assert decision.failure is FailureKind.PROVIDER_UNAVAILABLE
    assert all(
        item.failure is FailureKind.PROVIDER_UNAVAILABLE
        for item in decision.rejected_candidates
    )
