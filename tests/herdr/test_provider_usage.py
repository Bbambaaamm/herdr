"""Offline fixtures and invariants for the provider usage observation contract.

Every fixture is synthetic provider JSON on disk; no SDK, socket, subprocess,
model call or budget/telemetry transition is exercised.  The fixtures cover the
six required scenarios: successful calls, timeout, retry, fallback, uncertain
delivery and missing cache metadata.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from herdr.provider_usage import (
    DeliveryOutcome,
    PricingObservation,
    UsageAggregate,
    UsageFieldError,
    UsageObservation,
    UsageStatus,
    UsageStatus as Status,
    observe_usage,
    select_billable,
)
from herdr.telemetry import CostUnknownReason, PricingEntry, PricingRegistry

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


# ---------------------------------------------------------------- successful
def test_successful_anthropic_call_is_measured_with_cache_buckets():
    usage = load_fixture("anthropic_success.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-1", pricing=PRICING, usage=usage,
    )
    assert observed.status is UsageStatus.MEASURED
    assert observed.input_tokens == 1000
    assert observed.output_tokens == 200
    assert observed.cache_read_tokens == 500
    assert observed.cache_write_tokens == 250
    assert observed.coverage == {
        "input": True, "output": True, "cache_read": True, "cache_write": True}
    # 250 uncached * 3 + 500 * 0.3 + 250 * 3.75 + 200 * 15 = 750 + 150 + 937.5 + 3000
    assert observed.estimated_cost_microusd == 4838


def test_successful_openai_call_splits_cached_from_prompt_total():
    usage = load_fixture("openai_success.json")["usage"]
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-2", pricing=PRICING, usage=usage,
    )
    assert observed.status is UsageStatus.MEASURED
    assert observed.input_tokens == 800
    assert observed.cache_read_tokens == 200
    assert observed.output_tokens == 150
    assert observed.cache_write_tokens == 0
    assert observed.estimated_cost_microusd == 4110


def test_codex_missing_cache_write_metadata_is_partial_not_measured():
    usage = load_fixture("codex_success.json")["usage"]
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="codex_responses",
        request_id="req-3", pricing=PRICING, usage=usage,
    )
    assert observed.status is UsageStatus.PARTIAL
    assert observed.input_tokens == 400
    assert observed.cache_read_tokens == 100
    assert observed.output_tokens == 150
    assert observed.cache_write_tokens is None
    assert observed.unknown_reasons == ("provider_omitted",)
    assert observed.estimated_cost_microusd is None


# ------------------------------------------------------------------ failure
def test_timeout_is_unknown_and_never_zero_tokens():
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-4", attempt_index=0, delivery="timeout",
        usage=None, pricing=PRICING,
    )
    assert observed.status is UsageStatus.UNKNOWN
    assert observed.delivery is DeliveryOutcome.TIMEOUT
    assert observed.input_tokens is None and observed.output_tokens is None
    assert observed.estimated_cost_microusd is None
    assert observed.actual_cost_microusd is None
    assert observed.cost_unknown_reason is CostUnknownReason.TOKEN_USAGE_MISSING
    assert observed.unknown_reasons == ("transport_failed",)


def test_retry_superseded_attempt_is_not_billed_twice():
    first = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-5", attempt_index=0, delivery="timeout", usage=None, pricing=PRICING)
    second = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-5", attempt_index=1,
        usage=load_fixture("anthropic_success.json")["usage"], pricing=PRICING)
    billable = select_billable([first, second])
    assert list(billable) == ["req-5"]
    assert billable["req-5"].attempt_index == 1
    assert billable["req-5"].status is UsageStatus.MEASURED
    aggregate = UsageAggregate().add(first).add(second)
    assert aggregate.observations == 2
    assert aggregate.measured_observations == 1
    assert aggregate.billable_attempts == 1


def test_fallback_supersedes_the_original_route_only_after_delivery():
    original = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-6", attempt_index=0, delivery="timeout", usage=None, pricing=PRICING)
    fallback = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-6", attempt_index=1,
        usage=load_fixture("openai_success.json")["usage"], pricing=PRICING)
    billable = select_billable([original, fallback])
    assert billable["req-6"].provider == "openai"
    assert billable["req-6"].status is UsageStatus.MEASURED


def test_uncertain_delivery_is_never_counted_as_a_second_charge():
    uncertain = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-7", attempt_index=0, delivery="uncertain_delivery",
        usage=load_fixture("anthropic_success.json")["usage"], pricing=PRICING)
    delivered = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-7", attempt_index=1,
        usage=load_fixture("anthropic_success.json")["usage"], pricing=PRICING)
    assert uncertain.status is UsageStatus.UNKNOWN
    assert uncertain.delivery is DeliveryOutcome.UNCERTAIN
    assert uncertain.unknown_reasons == ("delivery_uncertain",)
    billable = select_billable([uncertain, delivered])
    assert list(billable) == ["req-7"]
    assert billable["req-7"].attempt_index == 1


def test_missing_cache_metadata_is_partial_and_explicit():
    usage = load_fixture("anthropic_missing_cache.json")["usage"]
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-8", pricing=PRICING, usage=usage,
    )
    assert observed.status is UsageStatus.PARTIAL
    assert observed.input_tokens == 700
    assert observed.output_tokens == 90
    assert observed.cache_read_tokens is None
    assert observed.cache_write_tokens is None
    assert observed.coverage["cache_read"] is False
    assert observed.unknown_reasons == ("provider_omitted",)
    # Missing cache buckets block the estimate: it must not be reported as zero.
    assert observed.estimated_cost_microusd is None


def test_non_billable_route_keeps_a_concrete_zero_and_no_unknown_tokens():
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-9", usage=None, pricing=PRICING, non_billable=True,
    )
    assert observed.status is UsageStatus.NON_BILLABLE
    assert observed.actual_cost_microusd == 0
    assert observed.estimated_cost_microusd == 0
    assert observed.cost_unknown_reason is None
    assert observed.unknown_reasons == ("non_billable_route",)
    aggregate = UsageAggregate().add(observed)
    assert aggregate.non_billable_observations == 1
    assert aggregate.input_tokens == 0
    assert aggregate.unknown_cost_observations == 0


# ------------------------------------------------------------- closed contract
def test_measured_status_rejects_missing_bucket_instead_of_zero():
    usage = {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 1}
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-10", pricing=PRICING, usage=usage)
    assert observed.status is UsageStatus.PARTIAL
    assert observed.cache_write_tokens is None
    with pytest.raises(UsageFieldError):
        UsageObservation(
            schema_version="provider-usage-observation-1", provider="anthropic",
            model="claude-opus-4-6", api_mode="anthropic_messages", request_id="req-10",
            attempt_index=0, delivery="delivered", status="measured",
            input_tokens=10, output_tokens=5, cache_read_tokens=1, cache_write_tokens=None,
            pricing=PRICING,
        )


def test_unknown_never_becomes_zero_aggregate():
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-11", usage=None, pricing=None)
    aggregate = UsageAggregate().add(observed)
    assert aggregate.unknown_observations == 1
    assert aggregate.input_tokens == 0
    assert aggregate.unknown_cost_observations == 1


def test_malformed_provider_value_is_unknown_not_zero():
    usage = {"input_tokens": "1_000", "output_tokens": 20}
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-12", pricing=PRICING, usage=usage)
    assert observed.status is UsageStatus.UNKNOWN
    assert observed.input_tokens is None
    assert observed.output_tokens is None
    assert "provider_malformed" in observed.unknown_reasons


def test_cache_buckets_cannot_exceed_input_tokens():
    usage = {"input_tokens": 100, "output_tokens": 5, "cache_read_input_tokens": 200,
             "cache_creation_input_tokens": 0}
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-13", pricing=PRICING, usage=usage)
    assert observed.status is UsageStatus.PARTIAL
    assert observed.input_tokens == 100
    assert observed.cache_read_tokens is None
    assert "provider_malformed" in observed.unknown_reasons


def test_actual_cost_without_a_reason_is_rejected_by_the_contract():
    with pytest.raises(UsageFieldError):
        UsageObservation(
            schema_version="provider-usage-observation-1", provider="anthropic",
            model="claude-opus-4-6", api_mode="anthropic_messages", request_id="req-14",
            attempt_index=0, delivery="delivered", status="measured",
            input_tokens=10, output_tokens=5, cache_read_tokens=0, cache_write_tokens=0,
            pricing=PRICING, actual_cost_microusd=0,
            cost_unknown_reason=CostUnknownReason.PROVIDER_NOT_REPORTED,
        )


def test_observation_json_roundtrip_is_stable_and_bounded():
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-15", pricing=PRICING,
        usage=load_fixture("anthropic_success.json")["usage"])
    payload = observed.to_json()
    assert payload["observation_id"] == observed.observation_id
    assert UsageObservation.from_json(payload) == observed
    with pytest.raises(UsageFieldError):
        UsageObservation.from_json({**payload, "observation_id": "0" * 64})
    with pytest.raises(UsageFieldError):
        UsageObservation.from_json({**payload, "unexpected": 1})


def test_pricing_resolves_from_the_existing_registry_without_new_rates():
    registry = PricingRegistry([PricingEntry(
        provider="anthropic", model="claude-opus-4-6", version="anthropic-2026-11-01",
        input_microusd_per_million=3_000, output_microusd_per_million=15_000,
        cached_microusd_per_million=300)])
    resolved = PricingObservation.from_registry(
        registry, provider="anthropic", model="claude-opus-4-6",
        pricing_version="anthropic-2026-11-01")
    assert resolved is not None
    assert resolved.input_microusd_per_million == 3_000
    assert PricingObservation.from_registry(
        registry, provider="anthropic", model="missing",
        pricing_version="anthropic-2026-11-01") is None


def test_aggregate_separates_partial_and_unknown_coverage():
    partial = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-16", pricing=PRICING,
        usage=load_fixture("anthropic_missing_cache.json")["usage"])
    unknown = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-17", usage=None, pricing=None)
    aggregate = UsageAggregate().add(partial).add(unknown)
    assert aggregate.observations == 2
    assert aggregate.partial_observations == 1
    assert aggregate.unknown_observations == 1
    assert aggregate.input_coverage == 1
    assert aggregate.output_coverage == 1
    assert aggregate.cache_read_coverage == 0
    assert aggregate.unknown_cost_observations == 2


def test_unknown_reasons_and_notes_are_closed_and_bounded():
    with pytest.raises(UsageFieldError):
        observe_usage(
            provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
            request_id="req-18", usage=None, unknown_reasons=["not_a_reason"])
    with pytest.raises(UsageFieldError):
        observe_usage(
            provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
            request_id="req-19", usage=None, notes=["x" * 257])
