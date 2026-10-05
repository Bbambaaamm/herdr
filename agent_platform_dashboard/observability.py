"""Truthful, bounded Machine City observability from sanitized production sources."""
import hashlib

INVENTORY = {
    'runtime_swarm': ('quantlab', 'swarm'),
    'model_routing': ('majak', 'codex'),
    'router': ('*', 'router'),
    'legacy_search_router': ('*', 'search'),
    'release': ('quantlab', 'release'),
    'fabric': None,
    'tool_fabric': None,
    'search_verifier': None,
    'prompt_runtime': None,
    'human_event': None,
    'eval_shadow': None,
    'budget': None,
    'context_skill': None,
    'semantic_guard': None,
    'mcp_a2a_specialist': None,
    'reviewer': None,
    'approval_hitl': None,
    'policy_registry': None,
    'provider_health': None,
    'circuit_breaker': None,
    'evidence_acceptance': None,
    'execution_plan': None,
    'work_protocol': None,
    'route_decision_trace': None,
    'verification_baseline': None,
    'route_policy_history': None,
}
AXES = (
    'observed_live_execution',
    'delivery_reconciliation',
    'settled_control_cycle',
    'verified_artifact',
    'integrated_change',
    'deployed_version',
)
FRESH_SECONDS = 90
NODE_LIMIT = 6


def item(
    id, value=None, unit='state', window='snapshot',
    source='producer_unavailable', freshness='unavailable',
    source_age_seconds=None, covered=0, denominator=0,
    reason='producer_unavailable', evidence_hash=None,
):
    result = dict(
        id=id, value=value, unit=unit, window=window, source=source,
        freshness=freshness, source_age_seconds=source_age_seconds,
        coverage=dict(covered=covered, denominator=denominator), reason=reason,
    )
    if evidence_hash is not None:
        result['evidence_hash'] = evidence_hash
    return result


def _state(source, now):
    if source is None:
        return 'unavailable', None, 'producer_unavailable'
    if source['status'] != 'available':
        return 'unavailable', None, source['reason']
    stamp = source['data_at'] if source['data_at'] is not None else source['observed_at']
    observed_age = max(0, int(now - source['observed_at']))
    data_age = max(0, int(now - stamp))
    age = max(observed_age, data_age)
    return ('stale' if age > FRESH_SECONDS else 'fresh'), age, None


def _profile_scoped_item(id, unit='state'):
    return item(id, unit=unit, reason='profile_scoped')


def _inventory(snapshot, now, visible_profiles):
    sources = {(row['profile'], row['kind']): row for row in snapshot['sources']}
    rows = []
    for id, binding in INVENTORY.items():
        if binding is None:
            rows.append(dict(
                id=id, status='UNKNOWN', reason='producer_unavailable',
                source='producer_unavailable', freshness='unavailable',
                source_age_seconds=None, coverage={'covered': 0, 'denominator': 0},
            ))
            continue
        profile, kind = binding
        if profile != '*':
            if profile not in visible_profiles:
                rows.append(dict(
                    id=id, status='UNKNOWN', reason='profile_scoped',
                    source='producer_unavailable', freshness='unavailable',
                    source_age_seconds=None, coverage={'covered': 0, 'denominator': 0},
                ))
                continue
            selected = [sources.get((profile, kind))]
            source_name = profile + '/' + kind
        else:
            selected = [sources.get((p, kind)) for p in visible_profiles]
            source_name = kind
        selected = [row for row in selected if row is not None]
        denominator = len(visible_profiles) if profile == '*' else 1
        available = [row for row in selected if row['status'] == 'available']
        states = [_state(row, now) for row in selected]
        ages = [age for _fresh, age, _reason in states if age is not None]
        freshness = (
            'stale' if any(fresh == 'stale' for fresh, _age, _reason in states)
            else 'fresh' if available and all(fresh == 'fresh' for fresh, _age, _reason in states if fresh != 'unavailable')
            else 'unknown' if available
            else 'unavailable'
        )
        reason = None
        if not available:
            reasons = [row['reason'] for row in selected if row['reason'] != 'ok']
            reason = reasons[0] if reasons and len(set(reasons)) == 1 else 'producer_unavailable'
        elif len(available) < denominator:
            reason = 'partial_source_coverage'
        if id == 'model_routing' and available:
            routing = available[0]['rows'][0] if len(available[0]['rows']) == 1 else None
            if routing is None or routing.get('routing_status') != 'available':
                reason = 'routing_unavailable'
                available = []
                freshness = 'unavailable'
        rows.append(dict(
            id=id, status='available' if available else 'UNKNOWN',
            reason=reason, source=source_name, freshness=freshness,
            source_age_seconds=max(ages) if ages else None,
            coverage={'covered': len(available), 'denominator': denominator},
        ))
    return rows


def _aggregate_rows(metrics, profile, kind, rows, freshness, age, source_reason):
    source = profile + '/' + kind
    if kind == 'router':
        denominator = sum(row['requests'] for row in rows) if rows is not None else 0
        fields = (
            ('input_tokens', 'tokens'),
            ('output_tokens', 'tokens'),
            ('cost_microusd', 'microusd'),
            ('duration_ms', 'ms'),
            ('fallback_count', 'fallbacks'),
            ('successful_requests', 'requests'),
        )
        metrics.append(item(
            profile + '.router.requests',
            denominator if rows is not None else None,
            'requests', 'router_history', source,
            freshness if rows is not None else 'unavailable', age,
            denominator, denominator,
            'no_requests' if rows is not None and denominator == 0 else source_reason if rows is None else None,
        ))
        for field, unit in fields:
            covered = (
                sum(row['requests'] for row in rows if row[field] is not None)
                if rows is not None else 0
            )
            value = (
                sum(row[field] for row in rows if row[field] is not None)
                if rows is not None and covered else None
            )
            metrics.append(item(
                profile + '.router.' + field, value, unit, 'router_history', source,
                freshness if rows is not None else 'unavailable', age,
                covered, denominator,
                'no_requests' if rows is not None and denominator == 0
                else 'measurement_missing' if rows is not None and covered < denominator
                else source_reason if rows is None else None,
            ))
        task_groups = {}
        for row in rows or ():
            task_id = row['task_id']
            if task_id is not None:
                task_groups.setdefault(task_id, []).append(row)
        ordered = sorted(
            task_groups,
            key=lambda task_id: (
                -max(row['last_used_at'] for row in task_groups[task_id]),
                task_id,
            ),
        )
        selected = ordered[:NODE_LIMIT]
        metrics.append(item(
            profile + '.router.node_coverage',
            len(selected) if rows is not None else None,
            'nodes', 'router_history', source,
            freshness if rows is not None else 'unavailable', age,
            len(selected), len(ordered),
            'bounded_recent_nodes' if len(selected) < len(ordered)
            else 'no_task_bound_requests' if rows is not None and not ordered
            else source_reason if rows is None else None,
        ))
        node_fields = (
            ('requests', 'requests'),
            ('input_tokens', 'tokens'),
            ('output_tokens', 'tokens'),
            ('cost_microusd', 'microusd'),
            ('duration_ms', 'ms'),
            ('fallback_count', 'fallbacks'),
        )
        for task_id in selected:
            group = task_groups[task_id]
            node_requests = sum(row['requests'] for row in group)
            node = hashlib.sha256(task_id.encode('utf-8')).hexdigest()[:24]
            for field, unit in node_fields:
                covered = (
                    node_requests if field == 'requests'
                    else sum(row['requests'] for row in group if row[field] is not None)
                )
                value = (
                    node_requests if field == 'requests'
                    else sum(row[field] for row in group if row[field] is not None)
                    if covered else None
                )
                metrics.append(item(
                    profile + '.node.' + node + '.router.' + field,
                    value, unit, 'router_history', source, freshness, age,
                    covered, node_requests,
                    'measurement_missing' if covered < node_requests else None,
                ))
    elif kind == 'search':
        denominator = sum(row['searches'] for row in rows) if rows is not None else 0
        metrics.append(item(
            profile + '.legacy_search.searches',
            denominator if rows is not None else None,
            'searches', 'legacy_search_history', source,
            freshness if rows is not None else 'unavailable', age,
            denominator, denominator,
            'no_searches' if rows is not None and denominator == 0 else source_reason if rows is None else None,
        ))
        for field, unit in (
            ('cost_microusd', 'microusd'),
            ('duration_ms', 'ms'),
            ('fallback_count', 'fallbacks'),
            ('successful_searches', 'searches'),
        ):
            covered = (
                sum(row['searches'] for row in rows if row[field] is not None)
                if rows is not None else 0
            )
            value = (
                sum(row[field] for row in rows if row[field] is not None)
                if rows is not None and covered else None
            )
            metrics.append(item(
                profile + '.legacy_search.' + field, value, unit,
                'legacy_search_history', source,
                freshness if rows is not None else 'unavailable', age,
                covered, denominator,
                'no_searches' if rows is not None and denominator == 0
                else 'measurement_missing' if rows is not None and covered < denominator
                else source_reason if rows is None else None,
            ))


def build(snapshot, *, now=None, visible_profiles=None):
    """Build one deterministic read model. No task state is inferred from log text."""
    now = snapshot['generated_at'] if now is None else now
    visible_profiles = tuple(
        visible_profiles if visible_profiles is not None
        else sorted({row['profile'] for row in snapshot['sources']})
    )
    sources = {(row['profile'], row['kind']): row for row in snapshot['sources']}

    if 'quantlab' in visible_profiles:
        swarm = sources.get(('quantlab', 'swarm'))
        freshness, age, reason = _state(swarm, now)
        row = (
            swarm['rows'][0]
            if swarm and swarm['status'] == 'available' and len(swarm['rows']) == 1
            else None
        )
        tasks = row['tasks'] if row else []
        runtime = row.get('runtime_status', 'unavailable') if row else 'unavailable'
        lifecycle = [item(
            AXES[0],
            sum(agent['status'] == 'working' for agent in row.get('runtime_agents', []))
            if runtime == 'available' else None,
            'agents', source='quantlab/swarm',
            freshness=freshness if runtime == 'available' else 'unavailable',
            source_age_seconds=age,
            covered=1 if runtime == 'available' else 0, denominator=1,
            reason=None if runtime == 'available'
            else 'runtime_unavailable' if row else reason,
        )]
        reconciled = [task for task in tasks if 'delivery_reconcile_count' in task]
        reconciliation_known = row is not None and len(reconciled) == len(tasks)
        lifecycle.append(item(
            AXES[1],
            sum(task['delivery_reconcile_count'] for task in reconciled)
            if reconciliation_known else None,
            'reconciliations', source='quantlab/swarm',
            freshness=freshness if reconciliation_known else 'unknown',
            source_age_seconds=age, covered=len(reconciled), denominator=len(tasks),
            reason='no_tasks' if reconciliation_known and not tasks
            else None if reconciliation_known
            else 'field_unavailable' if row else reason,
        ))
        lifecycle.append(item(
            AXES[2],
            sum(task['state'] in ('done', 'failed', 'cancelled') for task in tasks)
            if row else None,
            'tasks', source='quantlab/swarm',
            freshness=freshness if row else 'unavailable',
            source_age_seconds=age,
            covered=len(tasks) if row else 0, denominator=len(tasks) if row else 0,
            reason='no_tasks' if row is not None and not tasks else None if row else reason,
        ))
    else:
        lifecycle = [
            _profile_scoped_item(AXES[0], 'agents'),
            _profile_scoped_item(AXES[1], 'reconciliations'),
            _profile_scoped_item(AXES[2], 'tasks'),
        ]

    lifecycle.extend((item(AXES[3]), item(AXES[4])))

    if 'quantlab' in visible_profiles:
        release = sources.get(('quantlab', 'release'))
        release_freshness, release_age, release_reason = _state(release, now)
        deployed = (
            release['rows'][0]
            if release and release['status'] == 'available' and len(release['rows']) == 1
            else None
        )
        lifecycle.append(item(
            AXES[5], deployed['tag'] if deployed else None, 'version',
            source='quantlab/release', freshness=release_freshness,
            source_age_seconds=release_age, covered=1 if deployed else 0, denominator=1,
            reason='global_release_not_task_bound' if deployed else release_reason,
            evidence_hash=deployed['commit'] if deployed else None,
        ))
    else:
        lifecycle.append(_profile_scoped_item(AXES[5], 'version'))

    metrics = []
    for profile in visible_profiles:
        for kind in ('router', 'search'):
            source = sources.get((profile, kind))
            freshness, age, source_reason = _state(source, now)
            rows = source['rows'] if source and source['status'] == 'available' else None
            _aggregate_rows(metrics, profile, kind, rows, freshness, age, source_reason)

    future_metrics = (
        ('fabric.session_lag_ms', 'ms'),
        ('tool_fabric.loaded_full_schemas', 'schemas'),
        ('search_verifier.verified_success', 'state'),
        ('prompt_runtime.context_tokens', 'tokens'),
        ('human_event.interventions', 'events'),
        ('eval_shadow.verified_cost_microusd', 'microusd'),
        ('budget.remaining_microusd', 'microusd'),
        ('context_skill.bundle_hash', 'hash'),
        ('semantic_guard.denials', 'events'),
        ('evidence_acceptance.verified_artifacts', 'artifacts'),
        ('execution_plan.verify_iterations', 'iterations'),
        ('mcp_a2a_specialist.events', 'events'),
        ('reviewer.outcome', 'state'),
        ('approval_hitl.awaiting', 'operations'),
        ('route_decision_trace.routes', 'routes'),
    )
    metrics.extend(item(id, unit=unit) for id, unit in future_metrics)

    if 'majak' in visible_profiles:
        codex = sources.get(('majak', 'codex'))
        freshness, age, source_reason = _state(codex, now)
        routing = (
            codex['rows'][0]
            if codex and codex['status'] == 'available' and len(codex['rows']) == 1
            and codex['rows'][0].get('routing_status') == 'available'
            else None
        )
        decisions = routing['routing_decisions'] if routing else 0
        for field, unit in (
            ('routing_decisions', 'decisions'),
            ('routing_free', 'decisions'),
            ('routing_sol', 'decisions'),
            ('routing_astra', 'decisions'),
            ('routing_astra_escalations', 'decisions'),
            ('routing_premium_denied', 'decisions'),
        ):
            metrics.append(item(
                'majak.model_routing.' + field,
                routing[field] if routing else None,
                unit, 'routing_history', 'majak/codex',
                freshness if routing else 'unavailable', age,
                decisions if routing else 0, decisions if routing else 0,
                'no_decisions' if routing and decisions == 0
                else source_reason if routing is None else None,
            ))
        metrics.append(item(
            'majak.model_routing.last_route_reason',
            routing['last_route_reason'] if routing and routing['last_route_reason'] else None,
            'reason', 'latest', 'majak/codex',
            freshness if routing else 'unavailable', age,
            1 if routing and routing['last_route_reason'] else 0,
            1 if routing else 0,
            'reason_unavailable' if routing and not routing['last_route_reason']
            else source_reason if routing is None else None,
        ))
        metrics.append(item(
            'majak.model_routing.policy_version',
            routing['routing_policy_version'] if routing else None,
            'version', 'current', 'majak/codex',
            freshness if routing else 'unavailable', age,
            1 if routing else 0, 1,
            source_reason if routing is None else None,
        ))

    return dict(
        version=1,
        lifecycle=lifecycle,
        metrics=metrics,
        inventory=_inventory(snapshot, now, set(visible_profiles)),
    )
