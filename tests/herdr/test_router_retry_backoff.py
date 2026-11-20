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


@pytest.mark.parametrize("value", [None, "", "   ", "soon", "1e9", "-5", True])
def test_retry_after_rejects_unusable_values(value):
    assert parse_retry_after(value, at=AT) is None


def test_retry_after_past_date_is_unusable_not_negative():
    assert parse_retry_after("Mon, 01 Jan 1990 00:00:00 GMT", at=AT) is None


def test_retry_after_is_returned_unbounded():
    """The cap is applied by plan_retry, never by the parser.

    Returning a shortened wait here would turn an over-cap provider hint into an
    earlier, unauthorised attempt.
    """
    assert parse_retry_after(str(int(RETRY_WAIT_CAP_SECONDS)), at=AT) == RETRY_WAIT_CAP_SECONDS
    assert parse_retry_after("901", at=AT) == 901.0
    assert parse_retry_after("999999", at=AT) == 999999.0


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
    assert transition.retry is not None
    assert transition.retry.retryable is False
    assert transition.retry.source == "deadline_exceeded"


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
    from datetime import UTC, datetime, timedelta

    transition, kwargs = _decision(tmp_path)
    base = datetime.fromisoformat(kwargs["at"].replace("Z", "+00:00"))
    reset_iso = (base + timedelta(seconds=45)).isoformat()
    transition, _ = _decision(tmp_path, reset_at=reset_iso)
    assert transition.action is RecoveryAction.FALLBACK
    assert transition.retry is not None
    assert transition.retry.wait_seconds == pytest.approx(45.0)
    restored = type(transition).from_audit_event(transition.audit_event())
    assert restored.retry == transition.retry
    assert restored.action is RecoveryAction.FALLBACK


def test_managed_fallback_without_timing_uses_bounded_backoff(tmp_path):
    transition, _ = _decision(tmp_path)
    assert transition.action is RecoveryAction.FALLBACK
    assert transition.retry is not None
    assert transition.retry.source == "backoff"
    assert 0.0 < transition.retry.wait_seconds <= 61.0


# --- E4 review regressions ---------------------------------------------------


def test_over_cap_retry_after_is_terminal_not_shortened():
    """A 901 s hint must not become a 1 s attempt."""
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED,
        retry_after="901",
        at=AT,
        attempt=1,
        deadline=AT + 1000.0,
    )
    assert guidance.retryable is False
    assert guidance.wait_seconds is None
    assert guidance.source == "deadline_exceeded"


def test_over_deadline_retry_after_is_terminal():
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED,
        retry_after="60",
        at=AT,
        attempt=1,
        deadline=AT + 30.0,
    )
    assert guidance.retryable is False
    assert guidance.source == "deadline_exceeded"


def test_over_cap_reset_hint_is_terminal_even_inside_a_deadline():
    """The truncated value must not become an earlier attempt (E4 P1)."""
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED,
        reset_at=AT + 4500.0,
        at=AT,
        attempt=1,
        deadline=AT + 1000.0,
    )
    assert guidance.retryable is False
    assert guidance.source == "deadline_exceeded"


def test_retry_after_preferred_over_reset_timestamp():
    guidance = plan_retry(
        failure=FailureKind.RATE_LIMITED,
        retry_after="60",
        reset_at=AT + 300.0,
        at=AT,
        attempt=1,
    )
    assert guidance.retryable is True
    assert guidance.source == "retry_after"
    assert guidance.wait_seconds == pytest.approx(60.0)


def test_retry_guidance_from_json_rejects_string_boolean():
    with pytest.raises(RoutingError):
        RetryGuidance.from_json({"retryable": "false", "wait_seconds": None, "source": "none"})
    with pytest.raises(RoutingError):
        RetryGuidance.from_json({"retryable": True, "wait_seconds": "5", "source": "backoff"})


def test_retry_guidance_rejects_non_retryable_wait():
    with pytest.raises(RoutingError):
        RetryGuidance(False, 5.0, "none")


def test_breaker_rejects_non_finite_reference_time():
    from herdr.security import ProviderCircuitBreaker, SecurityError

    breaker = ProviderCircuitBreaker()
    with pytest.raises(SecurityError):
        breaker.open("openai", "rate_limited", now=float("nan"))
    assert breaker.reason("openai") is None


def test_handoff_refuses_dispatch_before_not_before_and_allows_after():
    from herdr.scheduler_routing import ManagedExecutionHandoff, RoutingIntegrationError

    base = dict(
        version=1, task_id="task-1", run_token="run-1", attempt=2, fencing_token=1,
        consumer="github:r", agent_id="agent-1", parent_task_id=None, parent_agent_id=None,
        policy_profile="herdr-tenant", policy_version="v1",
        decision_sha256="a" * 64, selected_executor="e", selected_provider="p",
        selected_model="m", registry_hash="b" * 64, requirement_hash="c" * 64,
        parent_scope_hash="d" * 64, policy_hash="d" * 64, budget_allocation_id="e" * 64,
    )
    handoff = ManagedExecutionHandoff(**base, not_before="2030-01-01T00:00:30+00:00")
    with pytest.raises(RoutingIntegrationError):
        handoff.assert_dispatchable("2030-01-01T00:00:00+00:00")
    handoff.assert_dispatchable("2030-01-01T00:00:30+00:00")
    handoff.assert_dispatchable("2030-01-01T00:01:00+00:00")
    legacy = ManagedExecutionHandoff(**base)
    legacy.assert_dispatchable("2030-01-01T00:00:00+00:00")


def test_managed_fallback_records_not_before_on_handoff(tmp_path):
    from herdr.scheduler_routing import RoutingIntegrationError

    transition, _ = _decision(tmp_path, retry_after="60")
    assert transition.handoff is not None
    assert transition.handoff.not_before is not None
    with pytest.raises(RoutingIntegrationError):
        transition.handoff.assert_dispatchable("2000-01-01T00:00:00+00:00")


def test_managed_fallback_terminates_on_over_cap_hint(tmp_path):
    transition, _ = _decision(tmp_path, retry_after="4500")
    assert transition.action is RecoveryAction.TERMINATE
    assert transition.retry is not None
    assert transition.retry.retryable is False


def test_legacy_audit_event_without_retry_replays_without_conflict(tmp_path):
    from herdr.fallback_recovery import normalize_transition_event
    from herdr.scheduler import AuditLog

    log = AuditLog(tmp_path / "audit.jsonl")
    identity = (
        "event", "task_id", "run_token", "attempt",
        "failed_executor", "source_decision_sha256",
    )
    legacy = {
        "event": "managed_fallback_transition",
        "task_id": "task-legacy",
        "run_token": "run-legacy",
        "attempt": 2,
        "failed_executor": "exec-legacy",
        "source_decision_sha256": "a" * 64,
        "handoff": None,
    }
    log.append_or_get_strict(legacy, identity_fields=identity)
    modern = normalize_transition_event(legacy)
    assert modern == legacy
    assert log.append_or_get_strict(modern, identity_fields=identity, normalize=normalize_transition_event) == legacy


def test_restored_handoff_preserves_not_before(tmp_path):
    """Replay must not make an unready handoff dispatchable (E4 P1)."""
    from herdr.scheduler_routing import RoutingIntegrationError

    transition, _ = _decision(tmp_path, retry_after="120")
    restored = type(transition).from_audit_event(transition.audit_event())
    assert restored.handoff is not None
    assert restored.handoff.not_before == transition.handoff.not_before
    with pytest.raises(RoutingIntegrationError):
        restored.handoff.assert_dispatchable("2000-01-01T00:00:00+00:00")


def test_different_transition_still_conflicts(tmp_path):
    from herdr.fallback_recovery import normalize_transition_event
    from herdr.scheduler import AuditLog

    log = AuditLog(tmp_path / "audit.jsonl")
    identity = (
        "event", "task_id", "run_token", "attempt",
        "failed_executor", "source_decision_sha256",
    )
    stored = normalize_transition_event({
        "event": "managed_fallback_transition",
        "task_id": "task-x",
        "run_token": "run-x",
        "attempt": 2,
        "failed_executor": "exec-x",
        "source_decision_sha256": "a" * 64,
        "handoff": None,
    })
    log.append_or_get_strict(stored, identity_fields=identity)
    changed = dict(stored)
    changed["action"] = "terminate"
    with pytest.raises(Exception):
        log.append_or_get_strict(changed, identity_fields=identity, normalize=normalize_transition_event)


def test_legacy_fallback_event_without_retry_replays_as_redecide(tmp_path):
    """E4 P1: a pre-timing durable fallback must not crash or dispatch."""
    from herdr.scheduler_routing import RoutingIntegrationError

    transition, _ = _decision(tmp_path, retry_after="60")
    legacy = transition.audit_event()
    legacy.pop("retry", None)
    legacy.pop("not_before", None)
    legacy["handoff"] = {
        key: value for key, value in legacy["handoff"].items() if key != "not_before"
    }
    restored = type(transition).from_audit_event(legacy)
    assert restored.action is RecoveryAction.FALLBACK
    assert restored.retry is not None
    assert restored.retry.retryable is False
    assert restored.retry.source == "unknown"
    with pytest.raises(RoutingIntegrationError):
        restored.handoff.assert_dispatchable("2000-01-01T00:00:00+00:00")


def test_retry_without_boundary_replays_as_redecide(tmp_path):
    """E4 P1: a retryable hint with no boundary cannot prove the wait elapsed."""
    from herdr.scheduler_routing import RoutingIntegrationError

    transition, _ = _decision(tmp_path, retry_after="60")
    event = transition.audit_event()
    event.pop("not_before", None)
    event["handoff"] = {
        key: value for key, value in event["handoff"].items() if key != "not_before"
    }
    restored = type(transition).from_audit_event(event)
    assert restored.retry is not None
    assert restored.retry.retryable is False
    assert restored.retry.source == "unknown"
    with pytest.raises(RoutingIntegrationError):
        restored.handoff.assert_dispatchable("2000-01-01T00:00:00+00:00")


def test_previous_format_without_wait_flag_replays_without_conflict(tmp_path):
    """E4 P1: a record written before waits_for_provider must still replay."""
    from herdr.fallback_recovery import normalize_transition_event
    from herdr.scheduler import AuditLog

    transition, _ = _decision(tmp_path, retry_after="60")
    legacy = transition.audit_event()
    legacy["handoff"] = {
        key: value for key, value in legacy["handoff"].items()
        if key != "waits_for_provider"
    }
    log = AuditLog(tmp_path / "replay.jsonl")
    identity = (
        "event", "task_id", "run_token", "attempt",
        "failed_executor", "source_decision_sha256",
    )
    stored = log.append_or_get_strict(
        legacy, identity_fields=identity, normalize=normalize_transition_event
    )
    newer = dict(legacy)
    newer["handoff"] = dict(legacy["handoff"], waits_for_provider=True)
    returned = log.append_or_get_strict(
        newer, identity_fields=identity, normalize=normalize_transition_event
    )
    assert returned == stored


def test_changed_wait_replays_the_durable_boundary(tmp_path):
    """E4 P1: a later weaker hint must not open an earlier retry window."""
    from herdr.fallback_recovery import ProviderFailureObservation, decide_managed_fallback
    from herdr.scheduler_routing import RoutingIntegrationError

    scheduler, node, ident, kwargs, route = _scheduled(tmp_path)

    def decide(**observation_kwargs):
        attestation = _attestation(
            "a-runtime", kwargs["registry"].snapshot.hash, kwargs["requirement"].hash
        )
        observation = ProviderFailureObservation(
            executor_id="a-runtime", status_code=429, message="rate limit",
            scope=FailureScope.CANDIDATE_LOCAL, scope_attestation=attestation,
            **observation_kwargs,
        )
        return decide_managed_fallback(
            scheduler, task_id=node.id, route=route, observation=observation,
            identity=ident, registry=kwargs["registry"], requirement=kwargs["requirement"],
            policy=kwargs["policy"], runtime_state=kwargs["runtime_state"],
            at=kwargs["at"], policy_version=kwargs["policy_version"],
            budget_gate=kwargs["budget_gate"], budget_allocation_id=ALLOCATION,
            expected_registry_hash=kwargs["expected_registry_hash"],
            expected_requirement_hash=kwargs["expected_requirement_hash"],
            fallback_count=0, max_fallbacks=1,
        )

    first = decide(retry_after="120")
    second = decide(retry_after="0")
    assert first.handoff is not None and second.handoff is not None
    assert second.handoff.not_before == first.handoff.not_before
    with pytest.raises(RoutingIntegrationError):
        second.handoff.assert_dispatchable("2000-01-01T00:00:00+00:00")


def test_retry_policy_change_does_not_break_replay(tmp_path):
    """Derived timing is not part of the decision identity (E4 P1)."""
    from herdr.fallback_recovery import normalize_transition_event
    from herdr.scheduler import AuditLog

    log = AuditLog(tmp_path / "audit.jsonl")
    identity = (
        "event", "task_id", "run_token", "attempt",
        "failed_executor", "source_decision_sha256",
    )
    legacy = {
        "event": "managed_fallback_transition",
        "task_id": "task-legacy",
        "run_token": "run-legacy",
        "attempt": 2,
        "failed_executor": "exec-legacy",
        "source_decision_sha256": "a" * 64,
        "handoff": None,
    }
    log.append_or_get_strict(legacy, identity_fields=identity)
    retried = dict(legacy)
    retried["retry"] = RetryGuidance(True, 300.0, "retry_after", raw="300").to_json()
    assert log.append_or_get_strict(
        retried, identity_fields=identity, normalize=normalize_transition_event
    ) == legacy
