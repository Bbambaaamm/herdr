from __future__ import annotations

import json
from dataclasses import replace

import pytest

from herdr.telemetry import (
    CostUnknownReason,
    EventType,
    PricingEntry,
    PricingRegistry,
    TelemetryError,
    TelemetryEvent,
    TelemetryStore,
    materialize,
    new_event,
)

TS = "2026-09-27T06:00:00+00:00"


def event(**overrides) -> TelemetryEvent:
    data = {
        "event_type": EventType.TASK_STATE,
        "issue": "6",
        "task_id": "task-6",
        "agent_id": "agent-1",
        "role": "worker",
        "timestamp": TS,
        "state": "running",
    }
    data.update(overrides)
    return new_event(**data)


def test_pricing_registry_estimates_integer_microusd() -> None:
    registry = PricingRegistry(
        [
            PricingEntry(
                provider="provider-a",
                model="model-a",
                version="2026-09-27",
                input_microusd_per_million=2_000_000,
                output_microusd_per_million=8_000_000,
                cached_microusd_per_million=500_000,
            )
        ]
    )
    cost, reason = registry.estimate(
        provider="provider-a",
        model="model-a",
        version="2026-09-27",
        input_tokens=1_000,
        output_tokens=250,
        cached_tokens=200,
    )
    assert cost == 3_700
    assert reason is None


def test_pricing_unknown_reasons_are_explicit() -> None:
    registry = PricingRegistry()
    cost, reason = registry.estimate(
        provider="provider-a", model="model-a", version="v1",
        input_tokens=1, output_tokens=1,
    )
    assert cost is None
    assert reason is CostUnknownReason.PRICING_MISSING
    cost2, reason2 = registry.estimate(
        provider="provider-a", model="model-a", version="v1",
        input_tokens=None, output_tokens=1,
    )
    assert cost2 is None
    assert reason2 is CostUnknownReason.TOKEN_USAGE_MISSING


def test_unknown_actual_cost_requires_reason() -> None:
    with pytest.raises(TelemetryError, match="cost_unknown_reason"):
        event(cost_unknown_reason=None)


def test_known_cost_requires_pricing_version_and_no_unknown_reason() -> None:
    with pytest.raises(TelemetryError, match="pricing_version"):
        event(actual_cost_microusd=12, cost_unknown_reason=None)
    with pytest.raises(TelemetryError, match="known actual cost"):
        event(
            actual_cost_microusd=12,
            pricing_version="v1",
            cost_unknown_reason=CostUnknownReason.PROVIDER_NOT_REPORTED,
        )
    ok = event(
        actual_cost_microusd=12,
        pricing_version="v1",
        cost_unknown_reason=None,
    )
    assert ok.actual_cost_microusd == 12


def test_fallback_is_explicit_event() -> None:
    with pytest.raises(TelemetryError, match="fallback_chain"):
        event(event_type=EventType.MODEL_FALLBACK)
    fallback = event(
        event_type=EventType.MODEL_FALLBACK,
        provider="provider-a",
        model="model-b",
        fallback_chain=("model-a", "model-b"),
    )
    assert fallback.fallback_chain == ("model-a", "model-b")


def test_closed_schema_rejects_prompt_credentials_and_tool_args() -> None:
    raw = event().to_json()
    raw["prompt"] = "PRIVATE"
    with pytest.raises(TelemetryError, match="unknown telemetry fields"):
        TelemetryEvent.from_json(raw)
    raw2 = event().to_json()
    raw2["credential"] = "SECRET"
    with pytest.raises(TelemetryError, match="unknown telemetry fields"):
        TelemetryEvent.from_json(raw2)
    with pytest.raises(TelemetryError, match="tool name"):
        event(
            event_type=EventType.TOOL_CALL,
            tool_names=("write_file --path /secret --token abc",),
        )


def test_append_assigns_monotonic_sequence_and_event_id(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    first = store.append(event())
    second = store.append(event(state="done"))
    assert (first.sequence, second.sequence) == (1, 2)
    assert len(first.event_id) == 64
    assert store.read() == (first, second)


def test_event_id_detects_mutation() -> None:
    raw = event().to_json()
    raw["state"] = "done"
    with pytest.raises(TelemetryError, match="event_id mismatch"):
        TelemetryEvent.from_json(raw)


def test_materialized_replay_is_deterministic_and_aggregated(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    store.append(
        event(
            event_type=EventType.MODEL_ROUTE,
            provider="provider-a",
            model="model-a",
            input_tokens=100,
            output_tokens=20,
            cached_tokens=10,
            model_latency_ms=75,
            actual_cost_microusd=42,
            pricing_version="price-v1",
            cost_unknown_reason=None,
        )
    )
    store.append(
        event(
            event_type=EventType.MODEL_FALLBACK,
            provider="provider-b",
            model="model-b",
            fallback_chain=("model-a", "model-b"),
            input_tokens=50,
            output_tokens=10,
            model_latency_ms=25,
        )
    )
    store.append(event(state="done", result_sha="a" * 64))
    a = store.materialize().to_json()
    b = materialize(store.read()).to_json()
    assert a == b
    assert a["last_sequence"] == 3
    assert a["tasks"]["task-6"]["state"] == "done"
    assert a["tasks"]["task-6"]["result_sha"] == "a" * 64
    issue = a["by_issue"]["6"]
    assert issue["events"] == 3
    assert issue["input_tokens"] == 150
    assert issue["output_tokens"] == 30
    assert issue["actual_cost_microusd"] == 42
    assert issue["unknown_cost_events"] == 2
    assert issue["fallbacks"] == 1
    assert issue["latency_ms_total"] == 100
    assert issue["latency_samples"] == 2


def test_aggregates_split_by_agent_model_and_day() -> None:
    events = [
        replace(event(), sequence=1, model="m1", agent_id="a1"),
        replace(event(), sequence=2, model="m2", agent_id="a2"),
    ]
    view = materialize(events)
    assert set(view.by_agent) == {"a1", "a2"}
    assert set(view.by_model) == {"m1", "m2"}
    assert set(view.by_day) == {"2026-09-27"}


def test_ordering_fails_closed() -> None:
    events = [replace(event(), sequence=2), replace(event(), sequence=1)]
    with pytest.raises(TelemetryError, match="strictly increasing"):
        materialize(events)


def test_read_since_and_sse_are_bounded_read_only_stream(tmp_path) -> None:
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    store.append(event())
    store.append(event(state="review"))
    store.append(event(state="done"))
    tail = store.read_since(1, limit=1)
    assert len(tail) == 1
    assert tail[0].sequence == 2
    sse = store.sse_since(1, limit=2)
    assert "id: 2\n" in sse
    assert "id: 3\n" in sse
    assert "event: herdr\n" in sse
    assert "prompt" not in sse.lower()
    assert "credential" not in sse.lower()


def test_store_rejects_out_of_order_persisted_log(tmp_path) -> None:
    path = tmp_path / "telemetry.jsonl"
    e2 = replace(event(), sequence=2)
    e1 = replace(event(), sequence=1)
    path.write_text(
        json.dumps(e2.to_json(), sort_keys=True) + "\n"
        + json.dumps(e1.to_json(), sort_keys=True) + "\n"
    )
    with pytest.raises(TelemetryError, match="strictly increasing"):
        TelemetryStore(path).read()
