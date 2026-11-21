"""Read-only bridge tests: provider usage observations -> swarm telemetry.

Every case is offline and fixture-driven.  No SDK, socket, subprocess, model
call, budget reservation, settlement, routing or admission transition is
exercised.  The tests prove the bridge invariants at the existing telemetry
boundary: measured rows project the provider prompt total without charging a
cache bucket twice, partial/unknown rows never become zero, and a confirmed
cost survives on a partial row.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from herdr.provider_usage import (
    ApiMode,
    DeliveryOutcome,
    PricingObservation,
    UsageFieldError,
    UsageObservation,
    UsageStatus,
    observe_usage,
)
from herdr.telemetry import CostUnknownReason, EventType, TelemetryError, TelemetryEvent
from herdr.usage_telemetry import (
    TELEMETRY_USAGE_FIELDS,
    project_usage_telemetry,
    telemetry_usage_fields,
    usage_telemetry_event,
)

PRICING = PricingObservation(
    pricing_version="anthropic-2026-11-01",
    input_microusd_per_million=3_000_000,
    output_microusd_per_million=15_000_000,
    cache_read_microusd_per_million=300_000,
    cache_write_microusd_per_million=3_750_000,
)


def fixture_dir() -> Path:
    return Path(__file__).with_name("fixtures")


def load_fixture(name: str) -> dict:
    return json.loads((fixture_dir() / name).read_text(encoding="utf-8"))


def make_event(observation) -> TelemetryEvent:
    return usage_telemetry_event(
        observation,
        sequence=1,
        timestamp="2026-11-19T07:00:00Z",
        issue="53",
        task_id="task-1",
        agent_id="agent-1",
        role="coding",
        attempt=0,
    )


def test_measured_anthropic_projects_prompt_total_without_double_charging_cache():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-1", pricing=PRICING, usage=usage,
    )
    projection = project_usage_telemetry(observed)
    assert projection.status == "measured"
    assert projection.input_tokens == 1750
    assert projection.cached_tokens == 750
    assert projection.output_tokens == 200
    assert projection.cache_read_tokens == 500
    assert projection.cache_write_tokens == 250
    # Telemetry input is the provider prompt total; subtracting the cache sum
    # yields exactly the adapter's uncached input, so no bucket is charged twice.
    assert projection.input_tokens - projection.cached_tokens == observed.input_tokens == 1000
    assert projection.estimated_cost_microusd == 7088
    assert projection.actual_cost_microusd is None
    assert projection.cost_unknown_reason is CostUnknownReason.PROVIDER_NOT_REPORTED

    event = make_event(observed)
    assert event.input_tokens == 1750
    assert event.cached_tokens == 750
    assert event.actual_cost_microusd is None
    assert event.cost_unknown_reason is CostUnknownReason.PROVIDER_NOT_REPORTED
    assert TelemetryEvent.from_json(event.to_json()) == event


def test_measured_openai_prompt_total_includes_cached_and_explicit_write():
    usage = load_fixture("openai_success.json")["usage"]
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-2", pricing=PRICING, usage=usage,
    )
    projection = project_usage_telemetry(observed)
    assert projection.input_tokens == 1000
    assert projection.cached_tokens == 200
    assert projection.cache_read_tokens == 200
    assert projection.cache_write_tokens == 0
    assert projection.input_tokens - projection.cached_tokens == observed.input_tokens == 800
    assert projection.estimated_cost_microusd == 4710
    event = make_event(observed)
    assert event.cached_tokens == 200
    assert TelemetryEvent.from_json(event.to_json()) == event


def test_partial_observation_projects_no_token_totals_and_stays_unknown():
    usage = load_fixture("codex_success.json")["usage"]
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="codex_responses",
        request_id="req-3", pricing=PRICING, usage=usage,
    )
    assert observed.status is UsageStatus.PARTIAL
    projection = project_usage_telemetry(observed)
    assert projection.input_tokens is None
    assert projection.output_tokens is None
    assert projection.cached_tokens is None
    assert projection.actual_cost_microusd is None
    assert projection.cost_unknown_reason is not None
    # A partial row with no confirmed cost is economically unknown, and the
    # projection never renders it as a concrete zero.
    assert projection.status == "partial"
    assert projection.cost_state == "unknown"
    event = make_event(observed)
    assert event.input_tokens is None
    assert event.actual_cost_microusd is None
    assert event.cost_unknown_reason is not None
    assert TelemetryEvent.from_json(event.to_json()) == event


def test_partial_observation_preserves_confirmed_actual_cost():
    usage = load_fixture("codex_success.json")["usage"]
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="codex_responses",
        request_id="req-3", pricing=PRICING, usage=usage, actual_cost_microusd=42,
    )
    assert observed.status is UsageStatus.PARTIAL
    assert observed.actual_cost_microusd == 42
    projection = project_usage_telemetry(observed)
    # The confirmed cost is not discarded, but the incomplete token row is not
    # rendered as a concrete total either.
    assert projection.actual_cost_microusd == 42
    assert projection.cost_unknown_reason is None
    assert projection.input_tokens is None
    event = make_event(observed)
    assert event.actual_cost_microusd == 42
    assert event.input_tokens is None
    assert TelemetryEvent.from_json(event.to_json()) == event


def test_unknown_observation_is_never_rendered_as_zero():
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-4", pricing=PRICING, usage=None,
    )
    assert observed.status is UsageStatus.UNKNOWN
    projection = project_usage_telemetry(observed)
    assert projection.input_tokens is None
    assert projection.output_tokens is None
    assert projection.cached_tokens is None
    assert projection.actual_cost_microusd is None
    assert projection.estimated_cost_microusd is None
    assert projection.cost_unknown_reason is CostUnknownReason.TOKEN_USAGE_MISSING
    event = make_event(observed)
    assert event.actual_cost_microusd is None
    assert event.cost_unknown_reason is CostUnknownReason.TOKEN_USAGE_MISSING
    assert TelemetryEvent.from_json(event.to_json()) == event


def test_contradictory_cache_evidence_is_unknown_at_the_boundary():
    usage = {
        "prompt_tokens": 100,
        "completion_tokens": 10,
        "prompt_tokens_details": {"cached_tokens": 500},
    }
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-7", pricing=PRICING, usage=usage,
    )
    assert observed.status is UsageStatus.UNKNOWN
    assert "provider_malformed" in observed.unknown_reasons
    projection = project_usage_telemetry(observed)
    assert projection.input_tokens is None
    assert projection.actual_cost_microusd is None
    assert projection.cost_unknown_reason is CostUnknownReason.TOKEN_USAGE_MISSING
    assert make_event(observed).actual_cost_microusd is None


def test_telemetry_usage_fields_are_exact_contract_subset():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-8", pricing=PRICING, usage=usage,
    )
    fields = telemetry_usage_fields(observed)
    assert set(fields) == set(TELEMETRY_USAGE_FIELDS)
    assert set(fields) <= set(TelemetryEvent.__dataclass_fields__)


def test_retry_attempts_project_independently_without_dedupe():
    first = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-9", attempt_index=0, delivery="timeout", usage=None, pricing=PRICING,
    )
    second = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-9", attempt_index=1,
        usage=load_fixture("anthropic_success.json")["usage"], pricing=PRICING,
    )
    left = project_usage_telemetry(first)
    right = project_usage_telemetry(second)
    assert left.attempt_index == 0
    assert right.attempt_index == 1
    assert left.input_tokens is None
    assert right.input_tokens == 1750
    assert left.observation_id != right.observation_id


def test_projection_is_stateless_and_repeatable():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-10", pricing=PRICING, usage=usage,
    )
    before = observed.to_json()
    assert project_usage_telemetry(observed) == project_usage_telemetry(observed)
    assert observed.to_json() == before


def test_non_billable_route_authority_remains_unavailable():
    with pytest.raises(UsageFieldError):
        observe_usage(
            provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
            request_id="req-11", pricing=PRICING, usage=None, non_billable=True,
        )


# ------------------------------------------------- telemetry identity contract
# The adapter's provider token (herdr/provider_usage.py ``_token``) rejects only
# empty, whitespace, backslash and NUL; the telemetry contract
# (herdr/telemetry.py ``_TOKEN``) is the closed character class
# ``[A-Za-z0-9._:/@+-]``.  Identifiers such as ``provider;evil`` therefore pass
# the adapter but are rejected by telemetry: a provider/model that the adapter
# accepts but telemetry rejects must fail closed at the bridge, never be silently
# dropped or coerced into another row.
_ADAPTER_ONLY_PROVIDER = "provider;evil"
_ADAPTER_ONLY_MODEL = "model;evil"


def test_adapter_only_identity_is_rejected_at_the_telemetry_boundary():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider=_ADAPTER_ONLY_PROVIDER, model=_ADAPTER_ONLY_MODEL,
        api_mode="anthropic_messages", request_id="req-20", pricing=PRICING, usage=usage,
    )
    # The adapter accepted the identifier; telemetry must reject the projection.
    assert observed.provider == _ADAPTER_ONLY_PROVIDER
    assert observed.model == _ADAPTER_ONLY_MODEL
    with pytest.raises(TelemetryError):
        telemetry_usage_fields(observed)
    with pytest.raises(TelemetryError):
        make_event(observed)


def test_adapter_only_identity_is_rejected_for_every_observed_status():
    for kwargs in (
        {"usage": None},
        {"usage": load_fixture("codex_success.json")["usage"]},
        {"usage": load_fixture("anthropic_success.json")["usage"]},
    ):
        observed = observe_usage(
            provider=_ADAPTER_ONLY_PROVIDER, model=_ADAPTER_ONLY_MODEL,
            api_mode="anthropic_messages", request_id="req-21", pricing=PRICING, **kwargs,
        )
        with pytest.raises(TelemetryError):
            make_event(observed)


def test_adapter_only_identity_is_rejected_in_direct_construction():
    # A caller can build UsageObservation directly (it is a public dataclass), so
    # the bridge guard must not depend on observe_usage having normalized it.
    observed = UsageObservation(
        schema_version="provider-usage-observation-1",
        provider=_ADAPTER_ONLY_PROVIDER,
        model=_ADAPTER_ONLY_MODEL,
        api_mode=ApiMode.ANTHROPIC_MESSAGES,
        request_id="req-22",
        attempt_index=0,
        delivery=DeliveryOutcome.DELIVERED,
        status=UsageStatus.MEASURED,
        input_tokens=1,
        output_tokens=1,
        cache_read_tokens=0,
        cache_write_tokens=0,
        pricing=PRICING,
        estimated_cost_microusd=1,
        cost_unknown_reason=CostUnknownReason.PROVIDER_NOT_REPORTED,
    )
    with pytest.raises(TelemetryError):
        make_event(observed)


def test_telemetry_safe_identity_still_projects():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-23", pricing=PRICING, usage=usage,
    )
    event = make_event(observed)
    assert event.provider == "anthropic"
    assert event.model == "claude-opus-4-6"


def test_adapter_only_identity_is_rejected_by_direct_projection_not_only_the_event_path():
    # Independent exact-head review finding: ``telemetry_usage_fields`` was
    # guarded, but ``project_usage_telemetry`` still returned a UsageTelemetry
    # whose ``to_json()`` emitted the same adapter-only identity.  The projection
    # value object itself must fail closed, so a direct caller cannot serialize a
    # row that telemetry would reject.
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider=_ADAPTER_ONLY_PROVIDER,
        model=_ADAPTER_ONLY_MODEL,
        api_mode="anthropic_messages",
        request_id="req-24",
        pricing=PRICING,
        usage=usage,
    )
    assert observed.provider == _ADAPTER_ONLY_PROVIDER
    with pytest.raises(TelemetryError):
        project_usage_telemetry(observed)


# ------------------------------------------------- bounded observation reference
# Follow-up #1 of docs/architecture/PROVIDER_USAGE_OBSERVATION.md section 6: a
# usage row must be addressable without a prompt, response, credential or free
# text.  The closed telemetry schema therefore carries an optional bounded
# ``usage_observation_id`` digest reference, populated by the bridge from the
# source observation.  It never widens the schema to arbitrary metadata and it
# never changes budget/settlement/routing authority.

def test_telemetry_usage_fields_expose_the_bounded_observation_reference():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-30", pricing=PRICING, usage=usage,
    )
    fields = telemetry_usage_fields(observed)
    assert fields["usage_observation_id"] == observed.observation_id
    assert len(fields["usage_observation_id"]) == 64
    # No prompt, response or free-text field enters the reference contract.
    assert set(fields) == set(TELEMETRY_USAGE_FIELDS)


def test_usage_reference_is_present_for_partial_and_unknown_rows():
    partial = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-31", pricing=PRICING,
        usage=load_fixture("anthropic_missing_cache.json")["usage"],
    )
    unknown = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-32", pricing=PRICING, usage=None,
    )
    assert partial.status is not None and partial.observation_id
    for observed in (partial, unknown):
        projection = project_usage_telemetry(observed)
        assert projection.usage_observation_id == observed.observation_id
        event = make_event(observed)
        assert event.usage_observation_id == observed.observation_id


def test_usage_reference_round_trips_through_the_telemetry_event():
    usage = load_fixture("openai_success.json")["usage"]
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-33", pricing=PRICING, usage=usage,
    )
    event = make_event(observed)
    raw = event.to_json()
    assert raw["usage_observation_id"] == observed.observation_id
    restored = TelemetryEvent.from_json(raw)
    assert restored.usage_observation_id == observed.observation_id
    assert restored.event_id == event.event_id


def test_projection_without_reference_omits_the_key_from_its_payload():
    """A projection with no reference keeps the pre-reference canonical shape.

    Serializing an explicit null would change the payload a consumer hashed
    before the optional field existed.  This covers the UsageTelemetry boundary
    specifically, so removing its omission guard cannot pass unnoticed.
    """
    from herdr.usage_telemetry import UsageTelemetry
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-35", pricing=PRICING, usage=usage,
    )
    projection = UsageTelemetry(
        observation_id=observed.observation_id,
        provider=observed.provider,
        model=observed.model,
        api_mode=observed.api_mode.value,
        request_id=observed.request_id,
        attempt_index=observed.attempt_index,
        delivery=observed.delivery.value,
        status=observed.status.value,
        cost_state=observed.cost_state,
        cost_unknown_reason=CostUnknownReason.PROVIDER_NOT_REPORTED,
        usage_observation_id=None,
    )
    assert projection.usage_observation_id is None
    assert "usage_observation_id" not in projection.to_json()


def test_malformed_usage_reference_fails_closed_at_both_boundaries():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-34", pricing=PRICING, usage=usage,
    )
    fields = telemetry_usage_fields(observed)
    # Direct construction of an otherwise valid projection with a non-digest
    # reference fails.  ``cost_unknown_reason`` is supplied so the failure is
    # caused by the reference guard itself, not by an unrelated validation.
    from herdr.usage_telemetry import UsageTelemetry
    def projection(reference):
        return UsageTelemetry(
            observation_id=observed.observation_id,
            provider=observed.provider,
            model=observed.model,
            api_mode=observed.api_mode.value,
            request_id=observed.request_id,
            attempt_index=observed.attempt_index,
            delivery=observed.delivery.value,
            status=observed.status.value,
            cost_state=observed.cost_state,
            cost_unknown_reason=CostUnknownReason.PROVIDER_NOT_REPORTED,
            usage_observation_id=reference,
        )

    valid = projection(observed.observation_id)
    assert valid.to_json()["usage_observation_id"] == observed.observation_id
    with pytest.raises(TelemetryError):
        projection("not-a-digest")
    # A 40-char Git-style hex value is not a SHA-256 digest and must fail too.
    with pytest.raises(TelemetryError):
        projection("a" * 40)
    # Direct construction of the telemetry event with a non-digest fails too.
    with pytest.raises(TelemetryError):
        TelemetryEvent(
            sequence=1,
            timestamp="2026-11-21T00:00:00Z",
            event_type=EventType.MODEL_ROUTE,
            issue="53",
            task_id="task-1",
            attempt=0,
            agent_id="agent-1",
            role="coding",
            **{**fields, "usage_observation_id": "../escape"},
        )
    # The event boundary enforces the same exact SHA-256 rule.
    with pytest.raises(TelemetryError):
        TelemetryEvent(
            sequence=1,
            timestamp="2026-11-21T00:00:00Z",
            event_type=EventType.MODEL_ROUTE,
            issue="53",
            task_id="task-1",
            attempt=0,
            agent_id="agent-1",
            role="coding",
            **{**fields, "usage_observation_id": "a" * 40},
        )
    # An absent reference stays valid (optional field; omission is not a failure).
    absent = TelemetryEvent(
        sequence=1,
        timestamp="2026-11-21T00:00:00Z",
        event_type=EventType.MODEL_ROUTE,
        issue="53",
        task_id="task-1",
        attempt=0,
        agent_id="agent-1",
        role="coding",
        **{k: v for k, v in fields.items() if k != "usage_observation_id"},
    )
    assert absent.usage_observation_id is None
    assert TelemetryEvent.from_json(absent.to_json()).usage_observation_id is None
