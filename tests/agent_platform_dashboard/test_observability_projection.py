"""Read-model authority and replay tests over sanitized production-shaped rows."""
from copy import deepcopy

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
    assert lifecycle['settled_control_cycle']['freshness'] == 'stale'
    assert lifecycle['settled_control_cycle']['source_age_seconds'] == 210
    assert lifecycle['deployed_version']['freshness'] == 'stale'
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

