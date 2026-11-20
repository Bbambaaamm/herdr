"""Cost-aware comparison tests: read-only, synthetic quotes, no models."""
from dataclasses import replace

import pytest

from herdr.routing import (
    RoutingDecision, RoutingError, compare_cost_aware_shadow,
    select_route,
)
from tests.herdr.test_capability import NOW, fixture


def inputs():
    registry, scope, req, states = fixture()
    req = replace(req, preferred_providers=("a",))
    costs = {"a-runtime": 40, "b-runtime": 5}
    states = tuple(replace(
        state, requirement_hash=req.hash,
        estimated_cost_microusd=costs[state.executor_id],
    ) for state in states)
    return registry, scope, req, states


def compare(registry, scope, req, states, qualities=None):
    return compare_cost_aware_shadow(
        registry, req, scope, states, at=NOW,
        policy_version="router-v5-policy-1",
        synthetic_quality_pass=qualities or {
            "a-runtime": True, "b-runtime": True,
        },
    )


def test_cost_shadow_preserves_default_route_and_reports_synthetic_gap():
    registry, scope, req, states = inputs()
    original = select_route(
        registry, req, scope, states, at=NOW,
        policy_version="router-v5-policy-1",
    )
    assert original.selected_executor == "a-runtime"
    report = compare(registry, scope, req, states)
    assert report.status == "SYNTHETIC_COMPARISON_ONLY"
    assert report.baseline_decision_sha256 == original.digest
    assert report.baseline_executor_id == "a-runtime"
    assert report.shadow_executor_id == "b-runtime"
    assert report.baseline_quote_microusd == 40
    assert report.shadow_quote_microusd == 5
    assert report.hypothetical_quote_gap_microusd == 35
    assert report.to_json()["actual_cost_savings_microusd"] is None
    assert report.to_json()["actual_token_savings"] is None
    assert report.to_json()["may_execute"] is False
    assert not isinstance(report, RoutingDecision)
    assert select_route(
        registry, req, scope, states, at=NOW,
        policy_version="router-v5-policy-1",
    ) == original


def test_synthetic_quality_gate_prevents_cheapest_when_declared_failing():
    registry, scope, req, states = inputs()
    report = compare(registry, scope, req, states, {
        "a-runtime": True, "b-runtime": False,
    })
    assert report.shadow_executor_id == "a-runtime"
    assert report.hypothetical_quote_gap_microusd == 0


def test_all_quality_denied_is_blocked_not_a_routing_decision():
    registry, scope, req, states = inputs()
    report = compare(registry, scope, req, states, {
        "a-runtime": False, "b-runtime": False,
    })
    assert report.status == "BLOCKED_NO_QUALITY_PASS"
    assert report.shadow_executor_id is None


@pytest.mark.parametrize("qualities", [
    {"a-runtime": True}, {"a-runtime": True, "b-runtime": 1},
    {"a-runtime": True, "b-runtime": True, "c-runtime": True},
])
def test_incomplete_or_untyped_shadow_quality_is_rejected(qualities):
    registry, scope, req, states = inputs()
    with pytest.raises(RoutingError, match="exactly cover"):
        compare(registry, scope, req, states, qualities)


def test_unknown_price_blocks_shadow_and_is_never_treated_as_free():
    registry, scope, req, states = inputs()
    # Remove the cost ceilings so the ordinary eligibility filter admits
    # a provider with unknown price; the shadow optimizer must still deny it.
    scope = replace(scope, max_cost_microusd=None)
    req = replace(req, max_cost_microusd=None)
    states = tuple(replace(
        state,
        requirement_hash=req.hash,
        estimated_cost_microusd=None if state.executor_id == "a-runtime" else 5,
    ) for state in states)
    report = compare(registry, scope, req, states)
    assert report.status == "BLOCKED_UNKNOWN_QUOTE"
    assert report.shadow_executor_id is None
    assert report.hypothetical_quote_gap_microusd is None


def test_budget_filter_runs_before_shadow_cost_selection():
    registry, scope, req, states = inputs()
    states = (replace(states[0], estimated_cost_microusd=60), states[1])
    with pytest.raises(RoutingError, match="exactly cover"):
        compare(registry, scope, req, states)
    report = compare(registry, scope, req, states, {
        "b-runtime": True,
    })
    assert report.baseline_executor_id == "b-runtime"
    assert report.shadow_executor_id == "b-runtime"
    assert report.hypothetical_quote_gap_microusd == 0


def test_shadow_has_no_economic_side_effect_or_provider_io(monkeypatch):
    registry, scope, req, states = inputs()
    import socket
    def blocked(*_args, **_kwargs):
        raise AssertionError("network/side effect forbidden")
    monkeypatch.setattr(socket, "create_connection", blocked)
    report = compare(registry, scope, req, states)
    assert report.status == "SYNTHETIC_COMPARISON_ONLY"
