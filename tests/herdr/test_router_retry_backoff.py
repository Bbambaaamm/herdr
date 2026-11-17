"""Offline retry-timing, taxonomy and cooldown contracts for Router v5.

These tests are deterministic and never contact a provider.  They assert the
security invariants (bounded wait, deadline clamp, fail-closed terminal kinds,
per-provider isolation) rather than expected log text.
"""
from pathlib import Path

import pytest

from herdr.fallback_recovery import (
    ProviderFailureObservation,
    RecoveryAction,
    decide_managed_fallback,
)
from herdr.routing import (
    RETRY_WAIT_CAP_SECONDS,
    FailureKind,
    FailureScope,
    RetryGuidance,
    RoutingError,
    bounded_backoff,
    classify_failure,
    normalize_reset_timestamp,
    parse_retry_after,
    plan_retry,
)
from herdr.security import PolicyDenied, ProviderCircuitBreaker
from tests.herdr.test_fallback_recovery import _attestation, _scheduled
from tests.herdr.test_scheduler_routing import ALLOCATION

AT = 1_800_000_000.0


# --- Retry-After normalization ------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("60", 60.0),
        (60, 60.0),
        (0, 0.0),
        ("0", 0.0),
    ],
)
def test_retry_after_accepts_delta_seconds(value, expected):
    assert parse_retry_after(value, at=AT) == expected


def test_retry_after_accepts_http_date():
    from email.utils import format_datetime
    from datetime import UTC, datetime, timedelta

    target = datetime.fromtimestamp(AT, UTC) + timedelta(seconds=45)
    assert parse_retry_after(format_datetime(target, usegmt=True), at=AT) == pytest.approx(45.0)


@pytest.mark.parametrize("value", [None, "", "   ", "soon", "1e9", "-5", True, 901, "999999"])
def test_retry_after_rejects_unusable_values(value):
    assert parse_retry_after(value, at=AT) is None


def test_retry_after_past_date_is_unusable_not_negative():
    assert parse_retry_after("Mon, 01 Jan 1990 00:00:00 GMT", at=AT) is None


def test_retry_after_is_capped():
    assert parse_retry_after(str(int(RETRY_WAIT_CAP_SECONDS)), at=AT) == RETRY_WAIT_CAP_SECONDS
    assert parse_retry_after(str(int(RETRY_WAIT_CAP_SECONDS) + 1), at=AT) is None


# --- reset timestamp normalization -------------------------------------------

def test_reset_timestamp_accepts_epoch_and_iso():
    from datetime import UTC, datetime

    assert normalize_reset_timestamp(str(AT + 30), at=AT) == 30.0
    assert normalize_reset_timestamp(AT + 30, at=AT) == 30.0
    iso = datetime.fromtimestamp(AT, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert normalize_reset_timestamp(iso, at=AT) == pytest.approx(0.0, abs=1.0)
    later = datetime.fromtimestamp(AT + 30, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert normalize_reset_timestamp(later, at=AT) == pytest.approx(30.0, abs=1.0)


@pytest.mark.parametrize("value", [None, "", "later", True, AT - 10])
def test_reset_timestamp_rejects_unusable_values(value):
    assert normalize_reset_timestamp(value, at=AT) is None


def test_reset_timestamp_requires_timezone():
    assert normalize_reset_timestamp("2026-11-17T00:00:30", at=AT) is None


def test_reset_timestamp_naive_iso_is_not_silently_assumed_utc():
    # A naive timestamp is ambiguous; treating it as UTC would fabricate a wait.
    assert normalize_reset_timestamp("2026-11-17T00:00:30", at=AT) is None


# --- bounded backoff ----------------------------------------------------------

def test_backoff_is_bounded_and_deterministic():
    first = bounded_backoff(1, seed="task:exec")
    assert first == bounded_backoff(1, seed="task:exec")
    assert 1.0 <= first <= 2.0
    for attempt in range(1, 12):
        assert 0.0 < bounded_backoff(attempt, seed="t") <= 61.0


def test_backoff_cap_is_never_exceeded_even_at_high_attempt():
    assert bounded_backoff(99, seed="x") <= 61.0


def test_backoff_rejects_invalid_attempt():
    with pytest.raises(RoutingError):
        bounded_backoff(0)


# --- plan_retry ---------------------------------------------------------------

def test_plan_retry_prefers_explicit_retry_after():
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED, retry_after="60", reset_at=str(AT + 30),
        at=AT, attempt=1,
    )
    assert guidance.retryable is True
    assert guidance.wait_seconds == 60.0
    assert guidance.source == "retry_after"


def test_plan_retry_uses_reset_timestamp_when_no_retry_after():
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED, reset_at=str(AT + 120), at=AT, attempt=1,
    )
    assert guidance.retryable is True
    assert guidance.wait_seconds == 120.0
    assert guidance.source == "reset_timestamp"


def test_plan_retry_falls_back_to_bounded_backoff():
    guidance = plan_retry(failure=FailureKind.PROVIDER_UNAVAILABLE, at=AT, attempt=2, seed="s")
    assert guidance.retryable is True
    assert guidance.source == "backoff"
    assert 0.0 < guidance.wait_seconds <= 61.0


def test_plan_retry_clamps_to_task_deadline():
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED, retry_after="600",
        at=AT, attempt=1, deadline=AT + 100,
    )
    assert guidance.retryable is False
    assert guidance.source == "deadline_exceeded"


def test_plan_retry_waits_until_deadline_when_guidance_fits():
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED, retry_after="30",
        at=AT, attempt=1, deadline=AT + 100,
    )
    assert guidance.retryable is True
    assert guidance.wait_seconds == 30.0


def test_plan_retry_is_terminal_for_authorization_and_budget_kinds():
    # A denied policy/budget/identity grants no alternative candidate, so no
    # wait is legal and the decision must fail closed.
    for failure in (
        FailureKind.POLICY_DENIED,
        FailureKind.BUDGET_EXCEEDED,
        FailureKind.AUTH_INVALID,
        FailureKind.UNKNOWN,
    ):
        guidance = plan_retry(failure=failure, retry_after="1", at=AT, attempt=1)
        assert guidance.retryable is False
        assert guidance.source == "none"
        assert guidance.wait_seconds is None


def test_plan_retry_allows_another_approved_candidate_for_capability_gaps():
    # These are candidate-local: the approved portfolio may still hold a
    # better-fitting model, so a bounded wait is legal.
    for failure in (
        FailureKind.CONTEXT_LIMIT,
        FailureKind.TOOL_INCOMPATIBLE,
        FailureKind.CAPABILITY_MISMATCH,
        FailureKind.INSUFFICIENT_CREDITS,
    ):
        guidance = plan_retry(failure=failure, at=AT, attempt=1)
        assert guidance.retryable is True
        assert guidance.source == "backoff"


def test_plan_retry_expired_deadline_is_terminal():
    assert plan_retry(
        failure=FailureKind.RATE_LIMITED, at=AT, attempt=1, deadline=AT,
    ).retryable is False


def test_plan_retry_rejects_invalid_reference_time():
    with pytest.raises(RoutingError):
        plan_retry(failure=FailureKind.RATE_LIMITED, at=0.0, attempt=1)
    with pytest.raises(RoutingError):
        plan_retry(failure=FailureKind.RATE_LIMITED, at=AT, attempt=0)


def test_retry_guidance_round_trips_through_json():
    guidance = plan_retry(failure=FailureKind.RATE_LIMITED, retry_after="60", at=AT, attempt=1)
    restored = RetryGuidance.from_json(guidance.to_json())
    assert restored == guidance


def test_retry_guidance_rejects_retryable_without_wait():
    with pytest.raises(RoutingError):
        RetryGuidance(True, None, "backoff")


# --- taxonomy -----------------------------------------------------------------

@pytest.mark.parametrize(
    ("status", "message", "expected"),
    [
        (401, "invalid api key", FailureKind.AUTH_INVALID),
        (403, "forbidden", FailureKind.POLICY_DENIED),
        (429, "rate limit", FailureKind.RATE_LIMITED),
        (429, "daily quota exhausted", FailureKind.RATE_LIMIT_QUOTA),
        (429, "quota exceeded", FailureKind.RATE_LIMIT_QUOTA),
        (500, "internal server error", FailureKind.PROVIDER_SERVER_ERROR),
        (502, "bad gateway", FailureKind.PROVIDER_UNAVAILABLE),
        (503, "service unavailable", FailureKind.PROVIDER_UNAVAILABLE),
        (None, "context window exceeded", FailureKind.CONTEXT_LIMIT),
        (None, "tool call not supported", FailureKind.TOOL_INCOMPATIBLE),
        (None, "request timed out", FailureKind.TRANSPORT_TIMEOUT),
        (404, "model not found", FailureKind.MODEL_NOT_FOUND),
    ],
)
def test_failure_taxonomy_distinguishes_recovery_budgets(status, message, expected):
    assert classify_failure(status_code=status, message=message, model_known=False) is expected


def test_transient_and_quota_rate_limits_are_not_the_same_event():
    transient = classify_failure(status_code=429, message="rate limit", model_known=True)
    quota = classify_failure(status_code=429, message="daily quota exhausted", model_known=True)
    assert transient is FailureKind.RATE_LIMITED
    assert quota is FailureKind.RATE_LIMIT_QUOTA
    assert transient is not quota


def test_terminal_denial_wins_over_status_heuristic():
    assert classify_failure(status_code=404, message="model not found: budget exceeded") is (
        FailureKind.BUDGET_EXCEEDED
    )


# --- provider circuit breaker -------------------------------------------------

def test_breaker_cooldown_expires_and_is_per_provider():
    breaker = ProviderCircuitBreaker()
    breaker.open("provider-a", "rate_limited", cooldown_seconds=60, now=AT)
    with pytest.raises(PolicyDenied):
        breaker.require_closed("provider-a", now=AT + 1)
    breaker.require_closed("provider-b", now=AT + 1)  # unrelated provider unaffected
    assert breaker.eligible_at("provider-a", now=AT + 1) == AT + 60
    assert breaker.reason("provider-a", now=AT + 59) == "rate_limited"
    assert breaker.reason("provider-a", now=AT + 60) is None
    breaker.require_closed("provider-a", now=AT + 60)


def test_breaker_rejects_out_of_range_cooldown():
    with pytest.raises(Exception):
        ProviderCircuitBreaker(default_cooldown_seconds=-1.0)
    breaker = ProviderCircuitBreaker()
    with pytest.raises(Exception):
        breaker.open("p", "reason", cooldown_seconds=RETRY_WAIT_CAP_SECONDS + 1, now=AT)


# --- managed fallback wiring --------------------------------------------------

def _decision(tmp_path, *, deadline=None, **observation_kwargs):
    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)
    attestation = _attestation(
        "a-runtime", kwargs["registry"].snapshot.hash, kwargs["requirement"].hash
    )
    observation = ProviderFailureObservation(
        executor_id="a-runtime",
        status_code=429,
        message="rate limit",
        scope=FailureScope.CANDIDATE_LOCAL,
        scope_attestation=attestation,
        **observation_kwargs,
    )
    transition = decide_managed_fallback(
        scheduler,
        task_id=node.id,
        route=route,
        observation=observation,
        identity=ident,
        registry=kwargs["registry"],
        requirement=kwargs["requirement"],
        policy=kwargs["policy"],
        runtime_state=kwargs["runtime_state"],
        at=kwargs["at"],
        deadline=deadline,
        policy_version=kwargs["policy_version"],
        budget_gate=kwargs["budget_gate"],
        budget_allocation_id=ALLOCATION,
        expected_registry_hash=kwargs["expected_registry_hash"],
        expected_requirement_hash=kwargs["expected_requirement_hash"],
        fallback_count=0,
        max_fallbacks=1,
    )
    return transition, kwargs


def test_managed_fallback_carries_retry_guidance(tmp_path):
    transition, _ = _decision(tmp_path, retry_after="60")
    assert transition.action is RecoveryAction.FALLBACK
    assert transition.retry is not None
    assert transition.retry.retryable is True
    assert transition.retry.wait_seconds == 60.0
    assert transition.retry.source == "retry_after"


def test_managed_fallback_terminates_when_guidance_exceeds_deadline(tmp_path):
    from datetime import UTC, datetime, timedelta

    _, kwargs = _decision(tmp_path)
    base = datetime.fromisoformat(kwargs["at"].replace("Z", "+00:00"))
    deadline = (base + timedelta(seconds=10)).isoformat()
    transition, _ = _decision(tmp_path, retry_after="600", deadline=deadline)
    assert transition.action is RecoveryAction.TERMINATE
    assert transition.handoff is None
    assert transition.retry is None


def test_managed_fallback_waits_when_guidance_fits_deadline(tmp_path):
    from datetime import UTC, datetime, timedelta

    _, kwargs = _decision(tmp_path)
    base = datetime.fromisoformat(kwargs["at"].replace("Z", "+00:00"))
    deadline = (base + timedelta(seconds=120)).isoformat()
    transition, _ = _decision(tmp_path, retry_after="60", deadline=deadline)
    assert transition.action is RecoveryAction.FALLBACK
    assert transition.retry is not None
    assert transition.retry.retryable is True
    assert transition.retry.wait_seconds == 60.0


def test_managed_fallback_retry_survives_audit_round_trip(tmp_path):
    transition, _ = _decision(tmp_path, reset_at="2026-11-17T00:01:00Z")
    restored = type(transition).from_audit_event(transition.audit_event())
    assert restored.retry == transition.retry
    assert restored.action is RecoveryAction.FALLBACK


def test_managed_fallback_without_timing_uses_bounded_backoff(tmp_path):
    transition, _ = _decision(tmp_path)
    assert transition.action is RecoveryAction.FALLBACK
    assert transition.retry is not None
    assert transition.retry.source == "backoff"
    assert 0.0 < transition.retry.wait_seconds <= 61.0
