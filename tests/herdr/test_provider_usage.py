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
    billable_cost_microusd,
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
    # uncached input 1000 * 3 + cache read 500 * 0.3 + cache write 250 * 3.75
    # + output 200 * 15 = 3000 + 150 + 937.5 + 3000
    assert observed.estimated_cost_microusd == 7088


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
    # uncached 800 * 3 + cache read 200 * 0.3 + cache write 0 * 3.75
    # + output 150 * 15 = 2400 + 60 + 0 + 2250
    assert observed.estimated_cost_microusd == 4710


def test_codex_missing_cache_write_metadata_is_partial_not_measured():
    usage = load_fixture("codex_success.json")["usage"]
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="codex_responses",
        request_id="req-3", pricing=PRICING, usage=usage,
    )
    assert observed.status is UsageStatus.PARTIAL
    assert observed.input_tokens is None
    assert observed.cache_read_tokens == 100
    assert observed.output_tokens == 150
    assert observed.cache_write_tokens is None
    assert observed.unknown_reasons == ("provider_omitted",)
    assert observed.estimated_cost_microusd is None
    # The unknown cache write is never reported as zero: uncached input is unknown.
    assert observed.coverage["input"] is False


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


def test_retry_keeps_both_attempts_and_marks_only_delivered_as_billable():
    first = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-5", attempt_index=0, delivery="timeout", usage=None, pricing=PRICING)
    second = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-5", attempt_index=1,
        usage=load_fixture("anthropic_success.json")["usage"], pricing=PRICING)
    billable = select_billable([first, second])
    assert set(billable) == {("req-5", 0), ("req-5", 1)}
    assert billable[("req-5", 0)].cost_state == "unknown"
    assert billable[("req-5", 1)].status is UsageStatus.MEASURED
    aggregate = UsageAggregate().add(first).add(second)
    assert aggregate.observations == 2
    assert aggregate.measured_observations == 1
    assert aggregate.billable_attempts == 1


def test_fallback_keeps_original_attempt_and_delivered_route():
    original = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-6", attempt_index=0, delivery="timeout", usage=None, pricing=PRICING)
    fallback = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-6", attempt_index=1,
        usage=load_fixture("openai_success.json")["usage"], pricing=PRICING)
    billable = select_billable([original, fallback])
    assert set(billable) == {("req-6", 0), ("req-6", 1)}
    assert billable[("req-6", 0)].provider == "anthropic"
    assert billable[("req-6", 1)].provider == "openai"
    assert billable[("req-6", 1)].status is UsageStatus.MEASURED


def test_uncertain_delivery_remains_visible_after_a_delivered_retry():
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
    assert set(billable) == {("req-7", 0), ("req-7", 1)}
    assert billable[("req-7", 0)].cost_state == "unknown"
    assert billable[("req-7", 1)].delivery is DeliveryOutcome.DELIVERED


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


def test_unverified_non_billable_route_cannot_turn_missing_usage_into_zero():
    with pytest.raises(UsageFieldError, match="non-billable route authority"):
        observe_usage(
            provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
            request_id="req-9", usage=None, pricing=PRICING, non_billable=True,
            non_billable_route="internal-shadow",
        )
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-9", usage=None, pricing=PRICING,
    )
    assert observed.status is UsageStatus.UNKNOWN
    assert observed.actual_cost_microusd is None
    assert observed.estimated_cost_microusd is None
    aggregate = UsageAggregate().add(observed)
    assert aggregate.unknown_observations == 1
    assert aggregate.input_tokens == 0
    assert aggregate.unknown_cost_observations == 1


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


def test_cache_buckets_cannot_exceed_the_provider_input_total():
    # chat/codex prompt total includes cached tokens: cached 900 + written 200
    # exceeds the reported 1000 prompt total, so the row is malformed evidence.
    usage = {"prompt_tokens": 1000, "completion_tokens": 5,
             "prompt_tokens_details": {"cached_tokens": 900,
                                       "cache_write_tokens": 200}}
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-13", pricing=PRICING, usage=usage)
    assert observed.status is UsageStatus.UNKNOWN
    assert observed.input_tokens is None
    assert observed.cache_read_tokens is None
    assert observed.cache_write_tokens is None
    assert observed.output_tokens is None
    assert "provider_malformed" in observed.unknown_reasons


def test_anthropic_cache_buckets_are_not_part_of_uncached_input():
    # Anthropic reports uncached input plus independent cache buckets, so a cache
    # bucket larger than input_tokens is valid evidence, not a contradiction.
    usage = {"input_tokens": 100, "output_tokens": 5, "cache_read_input_tokens": 900,
             "cache_creation_input_tokens": 200}
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-13b", pricing=PRICING, usage=usage)
    assert observed.status is UsageStatus.MEASURED
    assert observed.input_tokens == 100
    assert observed.cache_read_tokens == 900
    assert observed.cache_write_tokens == 200
    expected = (100 * 3_000_000 + 900 * 300_000 + 200 * 3_750_000
                + 5 * 15_000_000 + 999_999) // 1_000_000
    assert observed.estimated_cost_microusd == expected


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


def test_partial_confirmed_cost_is_not_lost_when_token_buckets_are_incomplete():
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id="req-partial-cost", pricing=PRICING,
        usage=load_fixture("anthropic_missing_cache.json")["usage"],
        actual_cost_microusd=42)
    aggregate = UsageAggregate().add(observed)
    assert observed.status is UsageStatus.PARTIAL
    assert observed.actual_cost_microusd == billable_cost_microusd(observed) == aggregate.actual_cost_microusd == 42
    assert aggregate.unknown_cost_observations == 0
    assert aggregate.input_tokens == aggregate.output_tokens == 0


def test_unknown_delivery_rejects_a_claimed_confirmed_cost():
    with pytest.raises(UsageFieldError, match="unknown observation cannot carry confirmed actual cost"):
        observe_usage(
            provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
            request_id="req-unknown-cost", pricing=PRICING, usage=None,
            delivery=DeliveryOutcome.UNCERTAIN, actual_cost_microusd=42)


def test_unknown_reasons_and_notes_are_closed_and_bounded():
    with pytest.raises(UsageFieldError):
        observe_usage(
            provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
            request_id="req-18", usage=None, unknown_reasons=["not_a_reason"])
    with pytest.raises(UsageFieldError):
        observe_usage(
            provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
            request_id="req-19", usage=None, notes=["x" * 257])


# ------------------------------------------------- cache hit parametrization
# The same economic call expressed at different cache hit ratios must never charge
# the cached tokens twice: the normalized input bucket is uncached input, and the
# cache buckets are billed once at their own rate.
@pytest.mark.parametrize("hit", [0.0, 0.5, 0.9, 1.0])
@pytest.mark.parametrize("api_mode", ["chat_completions", "codex_responses"])
def test_openai_cache_hit_ratios_never_double_count(api_mode, hit):
    prompt_total, output = 1000, 100
    cached = round(prompt_total * hit)
    if api_mode == "chat_completions":
        usage = {"prompt_tokens": prompt_total, "completion_tokens": output,
                 "prompt_tokens_details": {"cached_tokens": cached},
                 "cache_write_tokens": 0}
    else:
        usage = {"input_tokens": prompt_total, "output_tokens": output,
                 "input_tokens_details": {"cached_tokens": cached,
                                          "cache_write_tokens": 0}}
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode=api_mode,
        request_id=f"hit-{api_mode}-{hit}", pricing=PRICING, usage=usage)
    assert observed.status is UsageStatus.MEASURED
    assert observed.input_tokens == prompt_total - cached
    assert observed.cache_read_tokens == cached
    assert observed.cache_write_tokens == 0
    expected = ((prompt_total - cached) * 3_000_000 + cached * 300_000
                + output * 15_000_000)
    assert observed.estimated_cost_microusd == (expected + 999_999) // 1_000_000


@pytest.mark.parametrize("hit", [0.0, 0.5, 0.9, 1.0])
def test_anthropic_cache_hit_ratios_and_cache_write(hit):
    total_input, cache_write, output = 1000, 250, 100
    cache_read = round((total_input - cache_write) * hit)
    uncached = total_input - cache_write - cache_read
    usage = {"input_tokens": uncached, "output_tokens": output,
             "cache_read_input_tokens": cache_read,
             "cache_creation_input_tokens": cache_write}
    observed = observe_usage(
        provider="anthropic", model="claude-opus-4-6", api_mode="anthropic_messages",
        request_id=f"hit-anthropic-{hit}", pricing=PRICING, usage=usage)
    assert observed.status is UsageStatus.MEASURED
    assert observed.input_tokens == uncached
    assert observed.cache_read_tokens == cache_read
    assert observed.cache_write_tokens == cache_write
    expected = (uncached * 3_000_000 + cache_read * 300_000
                + cache_write * 3_750_000 + output * 15_000_000)
    assert observed.estimated_cost_microusd == (expected + 999_999) // 1_000_000


def test_full_cache_hit_charges_no_uncached_input_rate():
    # Regression guard for the double-subtraction defect: at a 100% hit the whole
    # prompt total is charged at the cache-read rate only.
    prompt_total, output = 1000, 100
    usage = {"prompt_tokens": prompt_total, "completion_tokens": output,
             "prompt_tokens_details": {"cached_tokens": prompt_total},
             "cache_write_tokens": 0}
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="hit-full", pricing=PRICING, usage=usage)
    assert observed.input_tokens == 0
    assert observed.estimated_cost_microusd == (
        prompt_total * 300_000 + output * 15_000_000 + 999_999) // 1_000_000


def test_zero_cache_hit_charges_the_full_prompt_total():
    prompt_total, output = 1000, 100
    usage = {"prompt_tokens": prompt_total, "completion_tokens": output,
             "prompt_tokens_details": {"cached_tokens": 0},
             "cache_write_tokens": 0}
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="hit-zero", pricing=PRICING, usage=usage)
    assert observed.input_tokens == prompt_total
    assert observed.estimated_cost_microusd == (
        prompt_total * 3_000_000 + output * 15_000_000 + 999_999) // 1_000_000


# ------------------------------------------------- uncertain delivery economics
def test_uncertain_delivery_cost_is_unknown_never_zero():
    usage = {"prompt_tokens": 1000, "completion_tokens": 10,
             "prompt_tokens_details": {"cached_tokens": 0},
             "cache_write_tokens": 0}
    uncertain = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-uncertain", attempt_index=0, pricing=PRICING,
        usage=usage, delivery=DeliveryOutcome.UNCERTAIN)
    billable = select_billable([uncertain])
    assert set(billable) == {("req-uncertain", 0)}
    row = billable[("req-uncertain", 0)]
    assert row.status is UsageStatus.UNKNOWN
    assert row.cost_state == "unknown"
    assert row.actual_cost_microusd is None
    assert billable_cost_microusd(row) is None
    assert billable_cost_microusd(row) != 0
    payload = row.to_json()
    assert payload["cost_state"] == "unknown"
    assert payload["actual_cost_microusd"] is None


def test_billable_cost_helper_keeps_measured_and_unknown_distinct():
    usage = {"prompt_tokens": 10, "completion_tokens": 1,
             "prompt_tokens_details": {"cached_tokens": 0},
             "cache_write_tokens": 0}
    measured = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-cost-1", pricing=PRICING, usage=usage)
    unknown = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-cost-2", pricing=PRICING, usage=None)
    assert billable_cost_microusd(measured) == measured.estimated_cost_microusd
    assert billable_cost_microusd(unknown) is None
    assert unknown.cost_state == "unknown"


def test_uncertain_delivery_never_suppresses_a_delivered_fallback_cost():
    usage = {"prompt_tokens": 1000, "completion_tokens": 10,
             "prompt_tokens_details": {"cached_tokens": 0},
             "cache_write_tokens": 0}
    uncertain = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-uncertain-fallback", attempt_index=0, pricing=PRICING,
        usage=usage, delivery=DeliveryOutcome.UNCERTAIN)
    delivered = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-uncertain-fallback", attempt_index=1, pricing=PRICING,
        usage=usage, delivery=DeliveryOutcome.DELIVERED)
    billable = select_billable([uncertain, delivered])
    assert set(billable) == {("req-uncertain-fallback", 0), ("req-uncertain-fallback", 1)}
    assert billable[("req-uncertain-fallback", 0)].cost_state == "unknown"
    assert billable[("req-uncertain-fallback", 1)].delivery is DeliveryOutcome.DELIVERED
    assert billable_cost_microusd(billable[("req-uncertain-fallback", 1)]) == (
        1000 * 3_000_000 + 10 * 15_000_000 + 999_999) // 1_000_000


def test_non_billable_requires_verified_route_authority():
    # No named route in this adapter is an authenticated non-billable grant.
    with pytest.raises(UsageFieldError):
        observe_usage(provider="openai", model="gpt-5.3-codex",
                      api_mode="chat_completions", request_id="req-nb",
                      pricing=PRICING, usage={"prompt_tokens": 10, "completion_tokens": 1},
                      non_billable=True)
    with pytest.raises(UsageFieldError):
        observe_usage(provider="openai", model="gpt-5.3-codex",
                      api_mode="chat_completions", request_id="req-nb",
                      pricing=PRICING, usage={"prompt_tokens": 10, "completion_tokens": 1},
                      non_billable=True, non_billable_route="   ")
    with pytest.raises(UsageFieldError, match="non-billable route authority"):
        observe_usage(provider="openai", model="gpt-5.3-codex",
                      api_mode="chat_completions", request_id="req-nb",
                      pricing=PRICING, usage=None, non_billable=True,
                      non_billable_route="internal-shadow", delivery=DeliveryOutcome.UNCERTAIN)


def test_non_billable_cannot_override_positive_cost_or_uncertain_delivery():
    base = dict(provider="openai", model="gpt-5.3-codex",
                api_mode="chat_completions", request_id="req-nb2", pricing=PRICING,
                usage={"prompt_tokens": 10, "completion_tokens": 1,
                       "prompt_tokens_details": {"cached_tokens": 0},
                       "cache_write_tokens": 0})
    with pytest.raises(UsageFieldError, match="non-billable route authority"):
        observe_usage(**base, actual_cost_microusd=42, non_billable=True,
                      non_billable_route="internal-shadow")
    with pytest.raises(UsageFieldError, match="non-billable route authority"):
        observe_usage(**base, delivery=DeliveryOutcome.UNCERTAIN,
                      non_billable=True, non_billable_route="internal-shadow")
    with pytest.raises(UsageFieldError, match="non-billable route authority"):
        UsageObservation(
            schema_version="provider-usage-observation-1", provider="openai",
            model="gpt-5.3-codex", api_mode="chat_completions", request_id="req-nb2",
            attempt_index=0, delivery=DeliveryOutcome.DELIVERED,
            status=UsageStatus.NON_BILLABLE, unknown_reasons=("non_billable_route",),
        )
    with pytest.raises(UsageFieldError, match="zero cost requires"):
        observe_usage(**base, actual_cost_microusd=0)
    with pytest.raises(UsageFieldError, match="non-billable route authority"):
        observe_usage(**base, cost_unknown_reason=CostUnknownReason.NON_BILLABLE)


def test_replayed_observation_is_idempotent():
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-replay", pricing=PRICING,
        usage={"prompt_tokens": 1000, "completion_tokens": 100,
               "prompt_tokens_details": {"cached_tokens": 0},
               "cache_write_tokens": 0})
    once = UsageAggregate().add(observed)
    twice = once.add(observed)
    assert twice == once
    assert twice.observations == 1
    assert twice.input_tokens == 1000
    assert twice.actual_cost_microusd == once.actual_cost_microusd
    # A distinct event with the same economics is still counted.
    other = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-replay-2", pricing=PRICING,
        usage={"prompt_tokens": 1000, "completion_tokens": 100,
               "prompt_tokens_details": {"cached_tokens": 0},
               "cache_write_tokens": 0})
    assert twice.add(other).observations == 2


def test_conflicting_observations_for_one_transport_attempt_fail_closed():
    base = dict(provider="openai", model="gpt-5.3-codex",
                api_mode="chat_completions", request_id="req-conflict",
                attempt_index=0, pricing=PRICING,
                usage={"prompt_tokens": 10, "completion_tokens": 5,
                       "prompt_tokens_details": {"cached_tokens": 0},
                       "cache_write_tokens": 0})
    first = observe_usage(**base, actual_cost_microusd=15)
    revised = observe_usage(**base, actual_cost_microusd=16)
    once = UsageAggregate().add(first)
    assert once.add(first) == once
    with pytest.raises(UsageFieldError, match="conflicting observation"):
        once.add(revised)
    with pytest.raises(UsageFieldError, match="conflicting observation"):
        select_billable([first, revised])


def test_two_delivered_attempts_are_both_retained_independent_of_input_order():
    base = dict(provider="openai", model="gpt-5.3-codex",
                api_mode="chat_completions", request_id="req-two-delivered",
                pricing=PRICING,
                usage={"prompt_tokens": 10, "completion_tokens": 5,
                       "prompt_tokens_details": {"cached_tokens": 0},
                       "cache_write_tokens": 0})
    first = observe_usage(**base, attempt_index=0, actual_cost_microusd=15)
    second = observe_usage(**base, attempt_index=1, actual_cost_microusd=20)
    selected = select_billable([first, second])
    assert selected == select_billable([second, first])
    assert set(selected) == {("req-two-delivered", 0), ("req-two-delivered", 1)}
    aggregate = UsageAggregate().add(selected[("req-two-delivered", 0)]).add(
        selected[("req-two-delivered", 1)])
    assert aggregate.billable_attempts == 2
    assert aggregate.actual_cost_microusd == 35


def test_uncertain_attempt_remains_unknown_after_known_cost_fallback():
    base = dict(provider="openai", model="gpt-5.3-codex",
                api_mode="chat_completions", request_id="req-uncertain-known",
                pricing=PRICING)
    uncertain = observe_usage(**base, attempt_index=0,
                              delivery=DeliveryOutcome.UNCERTAIN)
    delivered = observe_usage(
        **base, attempt_index=1, actual_cost_microusd=15,
        usage={"prompt_tokens": 10, "completion_tokens": 5,
               "prompt_tokens_details": {"cached_tokens": 0},
               "cache_write_tokens": 0})
    selected = select_billable([uncertain, delivered])
    assert set(selected) == {("req-uncertain-known", 0), ("req-uncertain-known", 1)}
    aggregate = UsageAggregate().add(selected[("req-uncertain-known", 0)]).add(
        selected[("req-uncertain-known", 1)])
    assert aggregate.actual_cost_microusd == 15
    assert aggregate.unknown_cost_observations == 1
    assert aggregate.unknown_observations == 1


def test_from_json_rejects_tampered_derived_fields():
    observed = observe_usage(
        provider="openai", model="gpt-5.3-codex", api_mode="chat_completions",
        request_id="req-tamper", pricing=PRICING,
        usage={"prompt_tokens": 100, "completion_tokens": 10,
               "prompt_tokens_details": {"cached_tokens": 0},
               "cache_write_tokens": 0})
    payload = observed.to_json()
    assert UsageObservation.from_json(payload) == observed
    with pytest.raises(UsageFieldError):
        UsageObservation.from_json({**payload, "coverage": {**payload["coverage"],
                                                           "input": False}})
    with pytest.raises(UsageFieldError):
        UsageObservation.from_json({**payload, "cost_state": "measured"
                                    if observed.cost_state != "measured" else "unknown"})
