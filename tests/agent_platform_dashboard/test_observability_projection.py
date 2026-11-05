"""Read-model authority and replay tests over sanitized production-shaped rows."""
from copy import deepcopy

import pytest

from agent_platform_dashboard import production_contract as c
from agent_platform_dashboard.observability import build


def available(snapshot, profile, kind, rows, stamp=100):
    source = next(s for s in snapshot['sources'] if (s['profile'], s['kind']) == (profile, kind))
    source.update(status='available', reason='ok', rows=rows, data_at=stamp)


def replay():
    snapshot = c.unavailable(200)
    task = dict(task_id='task-1', parent_task_id=None, parent_agent_id=None,
                agent_id=None, state='done', role='builder', model=None,
                fallback_model=None, attempt=1, max_attempts=2, blocker=None,
                fencing_token=1, dependencies=[], result_sha='a' * 64,
                attempt_state='done', delivery_reconcile_count=0)
    swarm = dict(version=1, repo='Bbambaaamm/herdr', issue='77', issue_state='open',
                 paper_only=False, policy_profiles=[], agents=[], runtime_status='available',
                 runtime_agents=[], tasks=[task], edges=[])
    available(snapshot, 'quantlab', 'swarm', [swarm], 190)
    available(snapshot, 'quantlab', 'release', [dict(tag='v1.0', commit='b' * 40,
               config_sha256='c' * 64, deployed_at=10)], 10)
    router = dict(task_id=None, actual_model='model', provider='provider', requests=3,
                  input_tokens=0, output_tokens=None, cost_microusd=0,
                  fallback_count=0, successful_requests=3, duration_ms=1, last_used_at=190)
    available(snapshot, 'majak', 'router', [router], 190)
    snapshot['observability'] = build(snapshot)
    return snapshot


def by_id(rows):
    return {row['id']: row for row in rows}


def test_lifecycle_authority_is_separate_and_replay_is_deterministic():
    snapshot = replay()
    decoded = c.decode(c.encode(snapshot))
    assert decoded['observability'] == build(deepcopy(snapshot))
    lifecycle = by_id(decoded['observability']['lifecycle'])
    assert lifecycle['observed_live_execution']['value'] == 0
    assert lifecycle['delivery_reconciliation']['value'] == 0
    assert lifecycle['settled_control_cycle']['value'] == 1
    for axis in ('verified_artifact', 'integrated_change'):
        assert lifecycle[axis]['value'] is None
        assert lifecycle[axis]['reason'] == 'producer_unavailable'
        assert 'evidence_hash' not in lifecycle[axis]
    assert lifecycle['deployed_version']['value'] == 'v1.0'
    assert lifecycle['deployed_version']['evidence_hash'] == 'b' * 40
    assert lifecycle['deployed_version']['freshness'] == 'stale'
    assert lifecycle['deployed_version']['reason'] == 'global_release_not_task_bound'
    assert lifecycle['deployed_version']['source_age_seconds'] == 190
    assert len(c.encode(snapshot)) <= c.MAX_BYTES


def test_request_weighted_partial_coverage_zero_and_unknown():
    snapshot = replay()
    metrics = by_id(snapshot['observability']['metrics'])
    assert metrics['majak.router.input_tokens']['value'] == 0
    assert metrics['majak.router.input_tokens']['coverage'] == {'covered': 3, 'denominator': 3}
    assert metrics['majak.router.cost_microusd']['value'] == 0
    assert metrics['majak.router.output_tokens']['value'] is None
    assert metrics['majak.router.output_tokens']['reason'] == 'measurement_missing'
    router = next(s for s in snapshot['sources'] if s['profile'] == 'majak' and s['kind'] == 'router')
    router['rows'].append({**router['rows'][0], 'provider': 'other', 'requests': 7,
                           'input_tokens': None, 'cost_microusd': None})
    metrics = by_id(build(snapshot)['metrics'])
    assert metrics['majak.router.cost_microusd']['coverage'] == {'covered': 3, 'denominator': 10}
    assert metrics['majak.router.cost_microusd']['value'] == 0
    assert metrics['majak.router.cost_microusd']['reason'] == 'measurement_missing'


def test_stale_and_missing_producers_are_not_success():
    snapshot = replay()
    swarm = next(s for s in snapshot['sources'] if s['kind'] == 'swarm')
    swarm['data_at'] = 1
    model = build(snapshot)
    assert by_id(model['lifecycle'])['settled_control_cycle']['freshness'] == 'stale'
    inventory = by_id(model['inventory'])
    assert inventory['runtime_swarm']['source_age_seconds'] == 199
    assert inventory['search_verifier']['status'] == 'UNKNOWN'
    assert inventory['search_verifier']['reason'] == 'producer_unavailable'
    assert inventory['legacy_search_router']['status'] == 'UNKNOWN'
    assert inventory['search_verifier']['coverage'] == {'covered': 0, 'denominator': 0}
    empty = c.unavailable(200)['observability']
    assert all(row['value'] is None for row in empty['lifecycle'])
    assert all(row['value'] is None for row in empty['metrics'])


def test_profile_projection_masks_other_profile_release_and_inventory():
    snapshot = replay()
    projected = c.project(snapshot, ('majak',), 200)
    lifecycle = by_id(projected['observability']['lifecycle'])
    assert lifecycle['deployed_version']['value'] is None
    assert lifecycle['deployed_version']['reason'] == 'profile_scoped'
    assert 'evidence_hash' not in lifecycle['deployed_version']
    assert all(metric['source'].startswith('majak/') or metric['source'] == 'producer_unavailable'
               for metric in projected['observability']['metrics'])
    inventory = by_id(projected['observability']['inventory'])
    assert inventory['runtime_swarm']['status'] == 'UNKNOWN'
    assert inventory['router']['status'] == 'available'
    assert inventory['router']['coverage'] == {'covered': 1, 'denominator': 1}


def test_closed_observability_schema_rejects_extra_payload():
    snapshot = replay()
    snapshot['observability']['metrics'][0]['prompt'] = 'forbidden'
    try:
        c.encode(snapshot)
    except ValueError:
        pass
    else:
        raise AssertionError('unbounded metric field accepted')

def test_request_time_projection_reages_truth_from_authorized_sources():
    snapshot = replay()
    projected = c.project(snapshot, ('quantlab',), 400)
    lifecycle = by_id(projected['observability']['lifecycle'])
    assert lifecycle['settled_control_cycle']['value'] is None
    assert lifecycle['settled_control_cycle']['freshness'] == 'unavailable'
    assert lifecycle['settled_control_cycle']['reason'] == 'stale'
    assert lifecycle['settled_control_cycle']['source_age_seconds'] is None
    assert lifecycle['deployed_version']['value'] is None
    assert lifecycle['deployed_version']['freshness'] == 'unavailable'
    assert lifecycle['deployed_version']['reason'] == 'stale'
    assert lifecycle['verified_artifact']['value'] is None
    assert lifecycle['integrated_change']['value'] is None


def test_inventory_distinguishes_legacy_search_from_missing_search_verifier():
    snapshot = replay()
    search = dict(route_mode='fast', provider='legacy-provider', fallback_provider=None,
                  searches=2, successful_searches=2, duration_ms=20, max_duration_ms=12,
                  fallback_count=0, cost_microusd=None, result_count=4, extract_count=0,
                  last_used_at=190)
    available(snapshot, 'majak', 'search', [search], 190)
    model = build(snapshot)
    inventory = by_id(model['inventory'])
    assert inventory['legacy_search_router']['status'] == 'available'
    assert inventory['search_verifier']['status'] == 'UNKNOWN'
    assert inventory['search_verifier']['reason'] == 'producer_unavailable'
    metrics = by_id(model['metrics'])
    assert metrics['majak.legacy_search.searches']['value'] == 2
    assert metrics['majak.legacy_search.cost_microusd']['value'] is None
    assert metrics['majak.legacy_search.cost_microusd']['coverage'] == {
        'covered': 0, 'denominator': 2,
    }


def test_future_producer_inventory_is_explicit_unknown_not_zero_or_pass():
    inventory = by_id(c.unavailable(200)['observability']['inventory'])
    for name in (
        'fabric', 'tool_fabric', 'search_verifier', 'prompt_runtime', 'human_event',
        'eval_shadow', 'budget', 'context_skill', 'semantic_guard',
        'mcp_a2a_specialist', 'reviewer', 'approval_hitl', 'policy_registry',
        'provider_health', 'circuit_breaker', 'evidence_acceptance',
        'execution_plan', 'work_protocol', 'route_decision_trace',
        'verification_baseline', 'route_policy_history',
    ):
        assert inventory[name]['status'] == 'UNKNOWN'
        assert inventory[name]['reason'] == 'producer_unavailable'
        assert inventory[name]['coverage'] == {'covered': 0, 'denominator': 0}

def test_router_node_metrics_are_bounded_and_have_node_denominators():
    snapshot = replay()
    router = next(s for s in snapshot['sources'] if s['profile'] == 'majak' and s['kind'] == 'router')
    base = router['rows'][0]
    router['rows'] = [
        {**base, 'task_id': ('%064x' % index), 'requests': index + 1,
         'input_tokens': 10 * (index + 1), 'output_tokens': 5 * (index + 1),
         'cost_microusd': 100 * (index + 1), 'duration_ms': 20 * (index + 1),
         'fallback_count': index % 2, 'last_used_at': 190 - index}
        for index in range(8)
    ]
    metrics = by_id(build(snapshot)['metrics'])
    coverage = metrics['majak.router.node_coverage']
    assert coverage['value'] == 6
    assert coverage['coverage'] == {'covered': 6, 'denominator': 8}
    assert coverage['reason'] == 'bounded_recent_nodes'
    node_rows = [row for key, row in metrics.items() if key.startswith('majak.node.')]
    assert len(node_rows) == 6 * 6
    assert all(row['coverage']['denominator'] > 0 for row in node_rows)
    assert all(len(row['id']) <= 80 for row in node_rows)

def test_future_metrics_are_unknown_not_zero_or_pass():
    metrics = by_id(c.unavailable(200)['observability']['metrics'])
    for name in (
        'fabric.session_lag_ms', 'tool_fabric.loaded_full_schemas',
        'search_verifier.verified_success', 'prompt_runtime.context_tokens',
        'human_event.interventions', 'eval_shadow.verified_cost_microusd',
        'budget.remaining_microusd', 'context_skill.bundle_hash',
        'semantic_guard.denials', 'evidence_acceptance.verified_artifacts',
        'execution_plan.verify_iterations', 'mcp_a2a_specialist.events',
        'reviewer.outcome', 'approval_hitl.awaiting', 'route_decision_trace.routes',
    ):
        assert metrics[name]['value'] is None
        assert metrics[name]['reason'] == 'producer_unavailable'
        assert metrics[name]['freshness'] == 'unavailable'
        assert metrics[name]['coverage'] == {'covered': 0, 'denominator': 0}


def test_observability_stays_within_snapshot_bound_at_router_node_limit():
    snapshot = replay()
    for profile in ('majak', 'quantlab'):
        router = next(s for s in snapshot['sources'] if s['profile'] == profile and s['kind'] == 'router')
        base = {
            'task_id': None, 'actual_model': 'model', 'provider': 'provider',
            'requests': 1, 'input_tokens': 1, 'output_tokens': 1,
            'cost_microusd': 1, 'fallback_count': 0, 'successful_requests': 1,
            'duration_ms': 1, 'last_used_at': 190,
        }
        router.update(status='available', reason='ok', data_at=190)
        router['rows'] = [
            {**base, 'task_id': ('%064x' % (index + (100 if profile == 'quantlab' else 0))),
             'last_used_at': 190 - index}
            for index in range(50)
        ]
    snapshot['observability'] = build(snapshot)
    encoded = c.encode(snapshot)
    assert len(encoded) <= c.MAX_BYTES
    assert len(snapshot['observability']['metrics']) <= 128


def routing_replay(*, routing_at=1000, codex_at=1000, reason='bounded_reason'):
    snapshot = c.unavailable(1000)
    row = dict(
        used_percent=0, window_minutes=10080, resets_at=2000,
        ordinary_usage_allowed=True, has_credits=False, credits_unlimited=False,
        credits_balance='0', reset_credits_available=0, lifetime_tokens=0,
        peak_daily_tokens=0, longest_running_turn_sec=0, current_streak_days=0,
        longest_streak_days=0, daily=[], limit_history=[],
        routing_status='available', routing_policy_version='bounded-policy',
        routing_observed_at=routing_at, routing_soft_limit_pct=70,
        routing_hard_limit_pct=90, routing_decisions=2, routing_free=1,
        routing_sol=1, routing_astra=0, routing_astra_escalations=0,
        routing_premium_denied=0, last_route_at=routing_at,
        last_route_tier='sol', last_route_model='bounded-model',
        last_route_reason=reason,
    )
    source = next(s for s in snapshot['sources'] if (s['profile'], s['kind']) == ('majak', 'codex'))
    source.update(status='available', reason='ok', rows=[row], data_at=codex_at,
                  observed_at=codex_at)
    return snapshot, source, row


@pytest.mark.parametrize('length', [80, 81, 128])
def test_long_valid_source_reason_cannot_suppress_snapshot_or_be_silently_truncated(length):
    snapshot, source, row = routing_replay(reason='r' * length)
    c.row('codex', row)
    original = deepcopy(source)
    snapshot['observability'] = build(snapshot)
    decoded = c.decode(c.encode(snapshot))
    metric = by_id(decoded['observability']['metrics'])['majak.model_routing.last_route_reason']
    assert source == original
    decoded_source = next(s for s in decoded['sources'] if (s['profile'], s['kind']) == ('majak', 'codex'))
    assert decoded_source['rows'][0]['last_route_reason'] == 'r' * length
    assert metric['value'] == ('r' * length if length == 80 else None)
    assert metric['reason'] == (None if length == 80 else 'reason_over_bound')
    assert metric['coverage'] == {'covered': 1 if length == 80 else 0, 'denominator': 1}


def test_source_and_metric_reason_bounds_remain_strict():
    snapshot, _, row = routing_replay(reason='r' * 129)
    with pytest.raises(ValueError):
        c.row('codex', row)
    snapshot, _, _ = routing_replay()
    snapshot['observability'] = build(snapshot)
    by_id(snapshot['observability']['metrics'])['majak.model_routing.last_route_reason']['value'] = 'r' * 81
    with pytest.raises(ValueError):
        c.encode(snapshot)


@pytest.mark.parametrize('routing_age,codex_age', [(0, 0), (90, 0), (91, 0), (999, 0), (10, 100)])
def test_embedded_routing_metrics_and_inventory_use_oldest_relevant_timestamp(routing_age, codex_age):
    snapshot, _, _ = routing_replay(routing_at=1000 - routing_age, codex_at=1000 - codex_age)
    model = build(snapshot)
    routing_metrics = [m for m in model['metrics'] if m['id'].startswith('majak.model_routing.')]
    expected_age = max(routing_age, codex_age)
    expected_freshness = 'stale' if expected_age > 90 else 'fresh'
    assert len(routing_metrics) == 8
    for metric in routing_metrics:
        assert metric['source_age_seconds'] == expected_age
        assert metric['freshness'] == expected_freshness
    inventory = by_id(model['inventory'])['model_routing']
    assert inventory['status'] == 'available'
    assert inventory['source_age_seconds'] == expected_age
    assert inventory['freshness'] == expected_freshness


def test_embedded_routing_missing_preserves_explicit_reason_for_all_metrics_and_inventory():
    snapshot, _, row = routing_replay()
    row['routing_status'] = 'unavailable'
    for key in tuple(row):
        if key.startswith('routing_') and key != 'routing_status' or key.startswith('last_route_'):
            row[key] = None
    c.row('codex', row)
    snapshot['observability'] = build(snapshot)
    c.decode(c.encode(snapshot))
    metrics = [m for m in snapshot['observability']['metrics'] if m['id'].startswith('majak.model_routing.')]
    assert len(metrics) == 8
    assert all(m['value'] is None and m['freshness'] == 'unavailable'
               and m['reason'] == 'routing_unavailable' for m in metrics)
    inventory = by_id(snapshot['observability']['inventory'])['model_routing']
    assert inventory['status'] == 'UNKNOWN' and inventory['reason'] == 'routing_unavailable'


def test_future_embedded_routing_timestamp_fails_closed_instead_of_clamping_to_fresh():
    snapshot, _, _ = routing_replay(routing_at=1001)
    snapshot['observability'] = build(snapshot)
    c.decode(c.encode(snapshot))
    metrics = [m for m in snapshot['observability']['metrics'] if m['id'].startswith('majak.model_routing.')]
    assert all(m['value'] is None and m['freshness'] == 'unavailable'
               and m['reason'] == 'routing_time_invalid' for m in metrics)
    inventory = by_id(snapshot['observability']['inventory'])['model_routing']
    assert inventory['status'] == 'UNKNOWN' and inventory['reason'] == 'routing_time_invalid'


def test_routing_profile_projection_cannot_leak_hidden_reason_or_policy():
    snapshot, _, _ = routing_replay(reason='private-reason' * 8)
    snapshot['observability'] = build(snapshot)
    projected = c.project(snapshot, ('quantlab',), 1000)
    assert not any(m['id'].startswith('majak.') for m in projected['observability']['metrics'])
    assert by_id(projected['observability']['inventory'])['model_routing']['reason'] == 'profile_scoped'
    assert 'private-reason' not in str(projected) and 'bounded-policy' not in str(projected)


@pytest.mark.parametrize('section', ['lifecycle', 'inventory'])
def test_malformed_observability_row_is_rejected_as_invalid_metadata(section):
    import json
    snapshot = c.unavailable(1000)
    snapshot['observability'][section][0] = None
    with pytest.raises(ValueError, match='invalid_metadata'):
        c.decode(json.dumps(snapshot).encode())


@pytest.mark.parametrize('field', ['id', 'unit', 'window', 'source'])
def test_observability_metric_required_labels_cannot_be_null(field):
    snapshot = c.unavailable(1000)
    snapshot['observability']['metrics'][0][field] = None
    with pytest.raises(ValueError):
        c.encode(snapshot)


@pytest.mark.parametrize('observed_at,data_at', [(100, 100), (99, 100), (100, 99)])
@pytest.mark.parametrize('path', ['request_projection', 'standalone_build'])
def test_future_router_source_cannot_remain_a_fresh_available_metric(observed_at, data_at, path):
    snapshot = c.unavailable(100)
    source = next(s for s in snapshot['sources'] if (s['profile'], s['kind']) == ('majak', 'router'))
    source.update(status='available', reason='ok', observed_at=observed_at, data_at=data_at,
        rows=[dict(task_id=None, actual_model='model', provider='provider', requests=1,
                   input_tokens=0, output_tokens=0, cost_microusd=0,
                   fallback_count=0, successful_requests=1, duration_ms=0, last_used_at=data_at)])
    snapshot['observability'] = build(snapshot)
    c.decode(c.encode(snapshot))
    before = deepcopy(snapshot)
    if path == 'request_projection':
        projected = c.project(snapshot, ('majak',), 99)
        selected_source = next(s for s in projected['sources'] if s['kind'] == 'router')
        assert selected_source['status'] == 'unavailable' and selected_source['rows'] == []
        model = projected['observability']
    else:
        model = build(snapshot, now=99, visible_profiles=('majak',))
    assert snapshot == before
    metric = by_id(model['metrics'])['majak.router.requests']
    assert metric['value'] is None and metric['freshness'] == 'unavailable'
    assert metric['reason'] == 'stale' and metric['coverage'] == {'covered': 0, 'denominator': 0}
    inventory = by_id(model['inventory'])['router']
    assert inventory['status'] == 'UNKNOWN' and inventory['freshness'] == 'unavailable'
    assert inventory['reason'] == 'stale' and inventory['coverage'] == {'covered': 0, 'denominator': 1}

