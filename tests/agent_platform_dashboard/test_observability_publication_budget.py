"""Canonical publication limits with full valid histories and inert collectors."""
from copy import deepcopy
import json
import os

import pytest

from agent_platform_dashboard import production_contract as c
from agent_platform_dashboard import observability as obs


NOW = 1000


def wire(value, *, ascii=True):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=ascii, allow_nan=False).encode()


def histories():
    result = {}
    for profile in c.PROFILES:
        for kind in ('router', 'search'):
            rows = []
            for index in range(50):
                if kind == 'router':
                    row = dict(task_id=f'{index:064x}', actual_model='m' * 128,
                        provider='p' * 64, requests=20, input_tokens=100,
                        output_tokens=50, cost_microusd=10, fallback_count=0,
                        successful_requests=20, duration_ms=1000, last_used_at=NOW)
                else:
                    row = dict(route_mode=('fast', 'deep', 'browser')[index % 3],
                        provider='p' * 124 + f'{index:04d}', fallback_provider='f' * 128,
                        searches=20, successful_searches=20, duration_ms=1000,
                        max_duration_ms=50, fallback_count=0, cost_microusd=10,
                        result_count=100, extract_count=0, last_used_at=NOW)
                c.row(kind, row)
                rows.append(row)
            result[(profile, kind)] = rows
    return result


def dense_snapshot():
    snapshot = c.unavailable(NOW)
    history = histories()
    for source in snapshot['sources']:
        key = source['profile'], source['kind']
        if key in history:
            source.update(status='available', reason='ok', rows=history[key], data_at=NOW)
    c.validate(snapshot)
    return snapshot


def swarm_row(count=75):
    tasks = [dict(task_id=f'task-{i}', parent_task_id=None, parent_agent_id=None,
        agent_id=None, state='done', role='builder', model=None, fallback_model=None,
        attempt=1, max_attempts=2, blocker=None, fencing_token=1, dependencies=[],
        result_sha='a' * 64, attempt_state='done', delivery_reconcile_count=0)
        for i in range(count)]
    row = dict(version=1, repo='Bbambaaamm/herdr', issue='198', issue_state='open',
        paper_only=False, policy_profiles=[], agents=[], runtime_status='available',
        runtime_agents=[], tasks=tasks, edges=[])
    c.row('swarm', row)
    return row


def queue_payload(*, escaped=False):
    rows = []
    for profile, repo, agent in (
        ('majak', 'Bbambaaamm/dotacni-majak', 'dotacni-majak-hermes'),
        ('quantlab', 'Bbambaaamm/Autonomous-Quant-Lab', 'quantlab-hermes'),
    ):
        for index in range(50):
            row = dict(task_id=(f'{profile}-{index:02d}-' + 'x' * 128)[:128],
                repo=repo, issue=index, issue_title=('Ž' if escaped else 'T') * 160,
                issue_open=True, scheduler_state='s' * 64, status='pending', attempts=0,
                max_attempts=1, not_before=None, updated_at=NOW, agent=agent,
                kind='k' * 64, blocker='b' * 128, pr_number=None)
            c.row('queue', row)
            rows.append(row)
    payload = dict(version=3, observed_at=NOW, tasks=rows)
    assert len(wire(payload, ascii=False)) <= c.MAX_BYTES
    return payload


def test_full_two_profile_histories_publish_without_losing_source_rows():
    assert c.MAX_BYTES == 131072
    snapshot = dense_snapshot()
    original = deepcopy(snapshot['sources'])
    source_only = {k: v for k, v in snapshot.items() if k != 'observability'}
    assert len(wire(source_only)) == 97671 < c.MAX_BYTES
    snapshot['observability'] = obs.build(snapshot)
    assert len(c.encode(snapshot)) <= c.MAX_BYTES
    assert snapshot['sources'] == original
    metrics = snapshot['observability']['metrics']
    coverage = next(m for m in metrics if m['id'] == 'observability.metric_coverage')
    assert coverage['value'] is None and coverage['reason'] == 'publication_byte_budget'
    assert coverage['coverage']['covered'] == len(metrics) - 1
    assert coverage['coverage']['covered'] < coverage['coverage']['denominator']
    for profile in c.PROFILES:
        selected = {m['id'].split('.')[2] for m in metrics if m['id'].startswith(profile + '.node.')}
        node_coverage = next(m for m in metrics if m['id'] == profile + '.router.node_coverage')
        assert node_coverage['value'] == node_coverage['coverage']['covered'] == len(selected)
        assert node_coverage['coverage']['denominator'] == 50
    assert obs.build(snapshot) == snapshot['observability']


def test_canonical_budget_accepts_exact_fit_and_bounds_one_byte_less(monkeypatch):
    assert c.MAX_BYTES == 131072
    snapshot = c.unavailable(NOW)
    original = deepcopy(snapshot)
    exact = len(c.encode(snapshot))
    monkeypatch.setattr(c, 'MAX_BYTES', exact)
    assert obs.build(snapshot) == original['observability']
    assert len(c.encode(snapshot)) == exact
    monkeypatch.setattr(c, 'MAX_BYTES', exact - 1)
    reduced = {**snapshot, 'observability': obs.build(snapshot)}
    assert len(c.encode(reduced)) <= exact - 1
    assert snapshot == original


def test_minimum_required_frame_fails_closed_without_altering_original_sources():
    snapshot = dense_snapshot()
    source = next(s for s in snapshot['sources'] if s['kind'] == 'swarm')
    source.update(status='available', reason='ok', rows=[swarm_row()], data_at=NOW)
    original = deepcopy(snapshot)
    assert len(wire({k: v for k, v in snapshot.items() if k != 'observability'})) == 124993
    with pytest.raises(ValueError):
        obs.build(snapshot)
    assert snapshot == original


def test_authorized_profile_projection_remains_bounded_without_regrowing_details():
    snapshot = dense_snapshot()
    snapshot['observability'] = obs.build(snapshot)
    before = deepcopy(snapshot)
    for profile in c.PROFILES:
        projected = c.project(snapshot, (profile,), NOW)
        assert len(wire(projected)) <= c.MAX_BYTES
        assert all(s['profile'] == profile for s in projected['sources'])
        assert projected['sources'] == [s for s in before['sources'] if s['profile'] == profile]
    assert snapshot == before


@pytest.fixture
def inert_exporter(monkeypatch):
    if os.name != 'posix':
        pytest.skip('Production collectors import the Linux fcntl boundary')
    from agent_platform_dashboard import production_export as export
    from agent_platform_dashboard import production_sources as sources
    history = histories()
    original = deepcopy(history)
    for name in ('QUEUE_PATH', 'CODEX_USAGE_PATH', 'ADMISSION_PATH', 'RELEASE_PATH', 'SWARM_PATH'):
        monkeypatch.setattr(sources, name, None)
    for kind in ('router', 'search'):
        monkeypatch.setattr(sources, kind,
            lambda path, profile, kind=kind: (deepcopy(history[(profile, kind)]), NOW))
    config = dict(version=1, output='/fixture/snapshot.json', herdr=None,
        profiles={profile: {kind: f'/fixture/{profile}/{kind}' if kind in ('router', 'search') else None
                  for kind in ('router', 'search', 'kanban', 'git', 'tests')}
                  for profile in c.PROFILES})
    yield export, sources, config, history
    assert history == original


@pytest.mark.parametrize('queues', ['unavailable', 'maximum_ascii', 'maximum_escaped'])
def test_real_collect_preserves_all_histories_and_shared_queue_failure_is_sticky(inert_exporter, monkeypatch, queues):
    export, sources, config, history = inert_exporter
    calls = []
    payload = queue_payload(escaped=queues == 'maximum_escaped') if queues != 'unavailable' else None
    original_payload = deepcopy(payload)
    if payload is not None:
        monkeypatch.setattr(sources, 'QUEUE_PATH', '/fixture/shared-queue')
        def load_once(path):
            calls.append(path)
            return payload
        monkeypatch.setattr(sources, 'queue_payload', load_once)
    snapshot = export.collect(config, NOW)
    assert len(c.encode(snapshot)) <= c.MAX_BYTES
    for source in snapshot['sources']:
        key = source['profile'], source['kind']
        if key in history:
            assert source['status'] == 'available' and source['rows'] == history[key]
        if source['kind'] == 'queue' and payload is not None:
            assert source['status'] == 'unavailable' and source['reason'] == 'source_failed'
            assert source['rows'] == [] and source['data_at'] is None
    assert len(calls) == (1 if payload is not None else 0)
    assert payload == original_payload


def test_real_collect_minimum_frame_rejects_only_new_swarm_and_preserves_prior_histories(inert_exporter, monkeypatch):
    export, sources, config, history = inert_exporter
    row = swarm_row()
    before = deepcopy(row)
    monkeypatch.setattr(sources, 'SWARM_PATH', '/fixture/swarm')
    monkeypatch.setattr(sources, 'live_swarm', lambda profile, now: ([row], NOW))
    snapshot = export.collect(config, NOW)
    assert len(c.encode(snapshot)) <= c.MAX_BYTES
    for source in snapshot['sources']:
        key = source['profile'], source['kind']
        if key in history:
            assert source['status'] == 'available' and source['rows'] == history[key]
        if source['kind'] == 'swarm':
            assert source['status'] == 'unavailable' and source['reason'] == 'source_failed'
            assert source['rows'] == [] and source['data_at'] is None
    assert row == before
