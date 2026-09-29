"""Production path never falls back to fixtures or runs collectors in a request."""
import json

import pytest

from agent_platform_dashboard.production_contract import SOURCE_PAIRS, decode, unavailable


def test_closed_snapshot_rejects_sensitive_fields():
    value = unavailable(100)
    value['prompt'] = 'PRIVATE'
    with pytest.raises(ValueError):
        decode(json.dumps(value).encode())


def test_unavailable_is_not_zero():
    value = decode(json.dumps(unavailable(100)).encode())
    assert len(value['sources']) == 17
    assert all(s['status'] == 'unavailable' and s['rows'] == [] for s in value['sources'])

import base64
import hashlib
import os
from pathlib import Path
import socket
import sqlite3
import subprocess

from agent_platform_dashboard import production_contract as c
from agent_platform_dashboard import production_io as io
from agent_platform_dashboard import production_sources as sources
from agent_platform_dashboard.production_auth import ITERATIONS
from agent_platform_dashboard.production_export import collect, configuration
from agent_platform_dashboard.production_herdr import sanitize
from agent_platform_dashboard.production_web import Application, provider_roles

pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Linux production boundary tests')


@pytest.fixture
def auth():
    password = hashlib.sha256(b'synthetic unit test only').hexdigest().encode()
    salt = '01' * 16
    record = dict(version=1, username='michal', salt=salt,
                  verifier=hashlib.pbkdf2_hmac('sha256', password, bytes.fromhex(salt), ITERATIONS).hex(), profiles=['majak'])
    return record, 'Basic ' + base64.b64encode(b'michal:' + password).decode()


def request(app, authorization=None, path='/agent-platform/', method='GET'):
    result = []
    body = app(dict(HTTP_HOST='127.0.0.1:3010', HTTP_AUTHORIZATION=authorization, PATH_INFO=path,
                    REQUEST_METHOD=method, QUERY_STRING=''), lambda status, headers: result.append((status, headers)))
    return result[0][0], dict(result[0][1]), b''.join(body)


def snapshot_file(tmp_path, now=100):
    path = tmp_path / 'snapshot.json'
    with io.publication(str(path)) as target:
        io.publish(target, c.encode(c.unavailable(now)))
    return path


@pytest.mark.parametrize('path', ['/agent-platform/', '/agent-platform/api/v1/overview', '/agent-platform/health', '/agent-platform/style.css'])
def test_every_route_needs_auth(tmp_path, auth, path):
    app = Application(str(snapshot_file(tmp_path)), auth[0], now=lambda: 100)
    status, headers, body = request(app, path=path)
    assert status.startswith('401') and 'WWW-Authenticate' in headers
    assert b'synthetic' not in body


def test_authenticated_snapshot_only_scope_and_no_collectors(tmp_path, auth, monkeypatch):
    app = Application(str(snapshot_file(tmp_path)), auth[0], now=lambda: 100)
    def forbidden(*args, **kwargs):
        pytest.fail('live collector in HTTP')
    monkeypatch.setattr(sqlite3, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    status, _, body = request(app, auth[1], '/agent-platform/api/v1/overview')
    assert status == '200 OK'
    data = json.loads(body)
    assert len(data['sources']) == 7 and {s['profile'] for s in data['sources']} == {'majak'}
    assert 'fixture' not in data
    assert request(app, auth[1])[0] == '200 OK'
    assert request(app, auth[1], method='POST')[0].startswith('405')
    assert request(app, auth[1], '/agent-platform/../secret')[0].startswith('404')


@pytest.mark.parametrize('now', [99, 191])
def test_stale_future_no_fixture_fallback(tmp_path, auth, now):
    app = Application(str(snapshot_file(tmp_path)), auth[0], now=lambda: now)
    assert request(app, auth[1])[0].startswith('503')


def test_replay_and_invalid_snapshot_fail_closed(tmp_path, auth):
    path = snapshot_file(tmp_path)
    app = Application(str(path), auth[0], now=lambda: 101)
    assert request(app, auth[1])[0] == '200 OK'
    path.write_bytes(c.encode(c.unavailable(99)))
    assert request(app, auth[1])[0].startswith('503')
    path.write_bytes(b'{"prompt":"PRIVATE"}')
    assert request(app, auth[1])[0].startswith('503')


def test_io_nofollow_bounds_fifo_permissions_and_lock(tmp_path):
    path = snapshot_file(tmp_path)
    with io.publication(str(path)):
        with pytest.raises(BlockingIOError):
            with io.publication(str(path)):
                pass
    link = tmp_path / 'link'; link.symlink_to(path)
    with pytest.raises(OSError):
        io.read(str(link), 1000)
    parent = tmp_path / 'alias'; parent.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(OSError):
        io.read(str(parent / 'snapshot.json'), 10000)
    fifo = tmp_path / 'fifo'; os.mkfifo(fifo)
    with pytest.raises(ValueError):
        io.read(str(fifo), 1000)
    with pytest.raises(ValueError):
        io.read(str(path), 2)
    path.chmod(0o666)
    with pytest.raises(ValueError):
        io.read(str(path), 10000)


def test_atomic_failure_preserves_previous_and_baseexception_releases(tmp_path, monkeypatch):
    path = snapshot_file(tmp_path)
    before = path.read_bytes()
    def fail(*args, **kwargs):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        with io.publication(str(path)) as target:
            with monkeypatch.context() as patch:
                patch.setattr(os, 'replace', fail)
                io.publish(target, b'new')
    assert path.read_bytes() == before
    with io.publication(str(path)):
        pass
    assert not list(tmp_path.glob('.snapshot.json.*'))


def router_db(path, *, wal=False):
    db = sqlite3.connect(path)
    if wal:
        assert db.execute('PRAGMA journal_mode=WAL').fetchone() == ('wal',)
    db.execute('CREATE TABLE requests(id INTEGER PRIMARY KEY,task_id TEXT,started_at REAL,ended_at REAL,input_tokens INTEGER,output_tokens INTEGER,cost_usd REAL,prompt TEXT,error_message TEXT,actual_model TEXT,provider TEXT,fallback_used INTEGER,success INTEGER,duration_s REAL)')
    db.execute("INSERT INTO requests VALUES(1,'task',10,11,3,4,NULL,'PRIVATE','SECRET','model-a','nous',0,1,1.0)")
    db.commit(); db.close()


def test_clean_wal_without_sidecars_uses_private_copy(tmp_path):
    path = tmp_path / 'router.db'
    router_db(path, wal=True)
    assert path.read_bytes()[18:20] == b'\x02\x02'
    assert not Path(str(path) + '-wal').exists() and not Path(str(path) + '-shm').exists()
    before = path.read_bytes()
    rows, stamp = sources.router(str(path), 'majak')
    assert rows[0]['requests'] == 1 and stamp == 11
    assert path.read_bytes() == before
    assert not Path(str(path) + '-wal').exists() and not Path(str(path) + '-shm').exists()
    Path(str(path) + '-wal').write_bytes(b'partial')
    with pytest.raises(ValueError):
        sources.router(str(path), 'majak')


def test_sql_ro_authorizer_aggregate_unknown_cost_profile_isolation(tmp_path):
    path = tmp_path / 'router.db'; router_db(path)
    before = path.read_bytes()
    a, stamp = sources.router(str(path), 'majak')
    b, _ = sources.router(str(path), 'quantlab')
    assert a[0]['task_id'] != b[0]['task_id']
    assert a[0]['cost_microusd'] is None and a[0]['input_tokens'] == 3 and stamp == 11
    assert 'PRIVATE' not in json.dumps(a)
    with sources.readonly(str(path), 'requests', sources.ROUTER_COLUMNS) as db:
        for sql in ('DELETE FROM requests', 'SELECT prompt FROM requests', 'PRAGMA query_only=OFF', 'ATTACH DATABASE ":memory:" AS other'):
            with pytest.raises(sqlite3.DatabaseError):
                db.execute(sql)
    assert path.read_bytes() == before


def search_db(path):
    db = sqlite3.connect(path)
    db.execute(
        'CREATE TABLE searches('
        'id INTEGER PRIMARY KEY,started_at REAL,ended_at REAL,route_mode TEXT,'
        'actual_provider TEXT,fallback_provider TEXT,fallback_used INTEGER,duration_ms INTEGER,'
        'result_count INTEGER,extract_count INTEGER,success INTEGER,cost_usd REAL,'
        'query_hash TEXT,query_chars INTEGER)'
    )
    db.execute(
        "INSERT INTO searches VALUES(1,10,11,'fast','exa-keyless','exa-keyless',1,125,5,0,1,0.0,'PRIVATEHASH',99)"
    )
    db.commit(); db.close()


def test_search_projection_exposes_operational_metrics_not_query_metadata(tmp_path):
    path = tmp_path / 'search.db'; search_db(path)
    before = path.read_bytes()
    rows, stamp = sources.search(str(path), 'majak')
    assert rows == [dict(
        route_mode='fast', provider='exa-keyless', fallback_provider='exa-keyless',
        searches=1, successful_searches=1, duration_ms=125, max_duration_ms=125,
        fallback_count=1, cost_microusd=0, result_count=5, extract_count=0,
        last_used_at=11,
    )]
    assert stamp == 11 and 'PRIVATEHASH' not in json.dumps(rows)
    with sources.readonly(str(path), 'searches', sources.SEARCH_COLUMNS) as db:
        with pytest.raises(sqlite3.DatabaseError):
            db.execute('SELECT query_hash FROM searches')
    assert path.read_bytes() == before


def test_search_projection_accepts_no_fallback_and_tracks_provider_recency(tmp_path):
    path = tmp_path / 'search.db'; search_db(path)
    db = sqlite3.connect(path)
    db.execute(
        "INSERT INTO searches VALUES(2,20,21,'deep','parallel-keyless',NULL,0,200,8,3,1,NULL,'PRIVATEHASH2',88)"
    )
    db.commit(); db.close()
    before = path.read_bytes()
    rows, stamp = sources.search(str(path), 'majak')
    assert stamp == 21
    assert {(row['provider'], row['last_used_at']) for row in rows} == {
        ('exa-keyless', 11), ('parallel-keyless', 21),
    }
    assert next(row for row in rows if row['provider'] == 'parallel-keyless')['fallback_provider'] is None
    assert path.read_bytes() == before


def test_provider_recency_is_required_by_the_published_contract():
    value = c.unavailable(100)
    source = next(item for item in value['sources'] if item['profile'] == 'majak' and item['kind'] == 'search')
    source.update(status='available', reason='ok', data_at=11, rows=[dict(
        route_mode='fast', provider='exa-keyless', fallback_provider=None,
        searches=1, successful_searches=1, duration_ms=10, max_duration_ms=10,
        fallback_count=0, cost_microusd=0, result_count=1, extract_count=0,
    )])
    with pytest.raises(ValueError):
        c.decode(json.dumps(value).encode())


def test_provider_recency_preserves_subsecond_ordering():
    value = c.unavailable(100)
    source = next(item for item in value['sources'] if item['profile'] == 'majak' and item['kind'] == 'router')
    source.update(status='available', reason='ok', data_at=11, rows=[dict(
        task_id=None, actual_model='model-a', provider='provider-a', requests=1,
        input_tokens=1, output_tokens=1, cost_microusd=0, fallback_count=0,
        successful_requests=1, duration_ms=10, last_used_at=11.125,
    )])
    assert c.decode(c.encode(value))['sources'][2]['rows'][0]['last_used_at'] == 11.125


def test_server_fallback_separates_current_and_historical_providers():
    source = dict(kind='search', status='available', rows=[
        dict(provider='historical-provider', last_used_at=10),
        dict(provider='current-provider', last_used_at=11.5),
        dict(provider='historical-provider', last_used_at=9),
    ])
    assert provider_roles(source) == ('current-provider', ('historical-provider',))
    assert provider_roles(dict(kind='router', status='available', rows=[])) == (None, ())
    assert provider_roles(dict(kind='git', status='available', rows=[])) is None


@pytest.mark.parametrize('kind,field', [
    ('router', 'actual_model'), ('router', 'provider'), ('search', 'provider'),
])
def test_current_provider_identity_is_never_null(kind, field):
    if kind == 'router':
        row = dict(task_id=None, actual_model='model-a', provider='provider-a', requests=1,
                   input_tokens=1, output_tokens=1, cost_microusd=0, fallback_count=0,
                   successful_requests=1, duration_ms=10, last_used_at=11)
    else:
        row = dict(route_mode='fast', provider='provider-a', fallback_provider=None,
                   searches=1, successful_searches=1, duration_ms=10, max_duration_ms=10,
                   fallback_count=0, cost_microusd=0, result_count=1, extract_count=0,
                   last_used_at=11)
    row[field] = None
    with pytest.raises(ValueError):
        c.row(kind, row)


def test_kanban_real_projection_and_missing_schema(tmp_path):
    path = tmp_path / 'kanban.db'
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE tasks(id TEXT,status TEXT,current_run_id INTEGER,created_at INTEGER,body TEXT)')
    db.execute("INSERT INTO tasks VALUES('task','running',2,10,'PRIVATE')")
    db.commit(); db.close()
    rows, stamp = sources.kanban({'path': str(path)}, 'majak')
    assert rows == [dict(task_id=c.identity('majak', 'task'), status='running', run_id=2)] and stamp == 10
    with pytest.raises(ValueError):
        sources.router(str(path), 'majak')


def test_codex_usage_projection_is_sanitized_bounded_and_global(tmp_path, monkeypatch):
    path = tmp_path / 'codex-usage.json'
    payload = {
        'version': 1,
        'observed_at': 100,
        'rate_limit': {
            'used_percent': 82, 'window_minutes': 10080, 'resets_at': 200,
            'ordinary_usage_allowed': True, 'has_credits': False,
            'credits_unlimited': False, 'credits_balance': '0',
            'reset_credits_available': 0,
        },
        'usage': {
            'lifetime_tokens': 123456789, 'peak_daily_tokens': 9000000,
            'longest_running_turn_sec': 1234, 'current_streak_days': 7,
            'longest_streak_days': 9,
            'daily': [{'day': '2026-09-24', 'tokens': 1000},
                      {'day': '2026-09-25', 'tokens': 2000}],
        },
        'limit_history': [{'at': 90, 'used_percent': 79},
                          {'at': 100, 'used_percent': 82}],
    }
    path.write_text(json.dumps(payload))
    monkeypatch.setattr(sources, 'CODEX_USAGE_PATH', str(path))
    rows, stamp = sources.codex(str(path), 'majak')
    assert stamp == 100 and len(rows) == 1
    row = rows[0]
    assert row['used_percent'] == 82 and row['lifetime_tokens'] == 123456789
    assert row['daily'][-1] == {'day': '2026-09-25', 'tokens': 2000}
    assert row['limit_history'][-1] == {'at': 100, 'used_percent': 82}
    assert 'account' not in json.dumps(row).lower()
    with pytest.raises(ValueError):
        sources.codex(str(path), 'quantlab')


def test_queue_projection_is_bounded_sanitized_and_quantlab_only(tmp_path, monkeypatch):
    path = tmp_path / 'queue.json'
    row = dict(task_id='issue190-soak24-20260926', issue=190,
               issue_title='Soak acceptance', issue_open=True, scheduler_state='active',
               status='pending', attempts=0, max_attempts=8,
               not_before=200, updated_at=100, agent='quantlab-hermes',
               kind='scheduled_acceptance', blocker=None, pr_number=None)
    payload = dict(version=2, profile='quantlab', observed_at=100, tasks=[row])
    path.write_text(json.dumps(payload))
    monkeypatch.setattr(sources, 'QUEUE_PATH', str(path))
    rows, stamp = sources.queue(str(path), 'quantlab')
    assert rows == [row] and stamp == 100
    assert 'prompt' not in json.dumps(rows) and 'PRIVATE' not in json.dumps(rows)
    with pytest.raises(ValueError):
        sources.queue(str(path), 'majak')
    payload['tasks'][0]['prompt'] = 'PRIVATE'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.queue(str(path), 'quantlab')


def test_queue_collect_and_staleness_are_fail_closed(tmp_path, monkeypatch):
    path = tmp_path / 'queue.json'
    row = dict(task_id='issue190-prepare-20260926', issue=190,
               issue_title='Prepare acceptance', issue_open=True, scheduler_state='active',
               status='running', attempts=1, max_attempts=8,
               not_before=None, updated_at=100, agent='quantlab-hermes',
               kind='scheduled_acceptance', blocker=None, pr_number=240)
    path.write_text(json.dumps(dict(version=2, profile='quantlab', observed_at=100, tasks=[row])))
    monkeypatch.setattr(sources, 'QUEUE_PATH', str(path))
    value = collect(config(tmp_path), 191)
    queue_source = next(s for s in value['sources'] if s['kind'] == 'queue')
    assert queue_source['profile'] == 'quantlab' and queue_source['status'] == 'available'
    assert queue_source['observed_at'] == 100 and queue_source['rows'] == [row]
    projected = c.project(value, ('quantlab',), 191)
    queue_source = next(s for s in projected['sources'] if s['kind'] == 'queue')
    assert queue_source['status'] == 'unavailable' and queue_source['reason'] == 'stale'
    assert queue_source['rows'] == []



def swarm_payload():
    return {
        'version': 'v1.2.0',
        'repo': 'Bbambaaamm/herdr',
        'issue': '7',
        'observed_at': '100.5',
        'paper_only': False,
        'policy_profiles': ['default'],
        'graph_latency': 0.1,
        'clock_snapshot': 100.5,
        'ts': '100.5',
        'agents': [
            {
                'agent_id': 'herdr-parent',
                'task_id': 'root',
                'state': 'running',
                'parent_task_id': None,
                'parent_agent_id': None,
                'fencing_token': 1,
            },
            {
                'agent_id': 'herdr-child',
                'task_id': 'child',
                'state': 'done',
                'parent_task_id': 'root',
                'parent_agent_id': 'herdr-parent',
                'fencing_token': 2,
            },
        ],
        'tasks': [
            {
                'task_id': 'root',
                'state': 'running',
                'role': 'planner',
                'tools': ['read_file'],
                'permissions': ['repo:read'],
                'timeout_seconds': 30,
                'max_attempts': 3,
                'dependencies': [],
                'parent_task_id': None,
                'parent_agent_id': None,
                'agent_id': 'herdr-parent',
                'fencing_token': 1,
                'model': 'model-a',
                'fallback_model': 'model-b',
                'attempts': 1,
                'blocker': None,
                'policy_profile': 'default',
                'paper_only': False,
                'telemetry': [],
                'ts': '100.0',
            },
            {
                'task_id': 'child',
                'state': 'done',
                'role': 'reader',
                'tools': ['read_file'],
                'permissions': ['repo:read'],
                'timeout_seconds': 30,
                'max_attempts': 2,
                'dependencies': [],
                'parent_task_id': 'root',
                'parent_agent_id': 'herdr-parent',
                'agent_id': 'herdr-child',
                'fencing_token': 2,
                'model': 'model-a',
                'fallback_model': 'model-b',
                'attempts': 1,
                'blocker': None,
                'policy_profile': 'default',
                'paper_only': False,
                'telemetry': [],
                'ts': '100.4',
                'result_sha': 'a' * 64,
            },
        ],
        'edges': [{'from': 'root', 'to': 'child', 'kind': 'parent'}],
    }


def test_swarm_projection_is_atomic_bounded_and_sanitized(tmp_path, monkeypatch):
    path = tmp_path / 'swarm.json'
    payload = swarm_payload()
    path.write_text(json.dumps(payload))
    monkeypatch.setattr(sources, 'SWARM_PATH', str(path))
    rows, stamp = sources.swarm(str(path), 'quantlab')
    assert stamp == 100 and len(rows) == 1
    snapshot = rows[0]
    assert len(payload['agents']) == 2
    assert snapshot['repo'] == 'Bbambaaamm/herdr'
    assert snapshot['issue'] == '7'
    assert snapshot['policy_profiles'] == ['default']
    assert snapshot['agents'] == [{
        'agent_id': 'herdr-parent',
        'task_id': 'root',
        'state': 'running',
        'parent_task_id': None,
        'parent_agent_id': None,
        'fencing_token': 1,
    }]
    assert snapshot['edges'] == [
        {'from_task': 'root', 'to_task': 'child', 'kind': 'parent'}
    ]
    assert [task['task_id'] for task in snapshot['tasks']] == ['child', 'root']
    serialized = json.dumps(snapshot)
    assert 'tools' not in serialized and 'permissions' not in serialized
    assert 'prompt' not in serialized and 'telemetry' not in serialized
    with pytest.raises(ValueError):
        sources.swarm(str(path), 'majak')


def test_swarm_raw_edge_mismatch_and_sensitive_task_field_fail_closed(tmp_path, monkeypatch):
    path = tmp_path / 'swarm.json'
    monkeypatch.setattr(sources, 'SWARM_PATH', str(path))
    payload = swarm_payload()
    payload['edges'] = []
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.swarm(str(path), 'quantlab')

    payload = swarm_payload()
    payload['tasks'][1]['prompt'] = 'PRIVATE'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.swarm(str(path), 'quantlab')

    payload = swarm_payload()
    payload['repo'] = 'Bbambaaamm/Autonomous-Quant-Lab'
    payload['paper_only'] = False
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.swarm(str(path), 'quantlab')

    payload = swarm_payload()
    del payload['paper_only']
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.swarm(str(path), 'quantlab')



def test_scheduler_historical_agent_state_must_match_task(tmp_path, monkeypatch):
    path = tmp_path / 'swarm.json'
    monkeypatch.setattr(sources, 'SWARM_PATH', str(path))
    payload = swarm_payload()
    payload['agents'][1]['state'] = 'running'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.swarm(str(path), 'quantlab')


def test_swarm_agents_must_match_running_task_identity(tmp_path, monkeypatch):
    path = tmp_path / 'swarm.json'
    monkeypatch.setattr(sources, 'SWARM_PATH', str(path))
    payload = swarm_payload()
    payload['agents'][0]['task_id'] = 'child'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.swarm(str(path), 'quantlab')

def test_collect_marks_only_swarm_unavailable_when_full_snapshot_budget_would_overflow(tmp_path, monkeypatch):
    large_tasks = []
    for index in range(100):
        suffix = f"{index:03d}"
        large_tasks.append({
            'task_id': ('task-' + suffix + '-' + 'x' * 240)[:256],
            'parent_task_id': None,
            'parent_agent_id': None,
            'agent_id': None,
            'state': 'done',
            'role': 'r' * 64,
            'model': 'm' * 128,
            'fallback_model': 'f' * 128,
            'attempt': 1,
            'max_attempts': 1,
            'blocker': 'b' * 128,
            'fencing_token': 0,
            'dependencies': [],
            'result_sha': 'a' * 64,
        })
    large_swarm = {
        'version': 1,
        'repo': 'Bbambaaamm/herdr',
        'issue': '48',
        'paper_only': False,
        'policy_profiles': ['default'],
        'agents': [],
        'tasks': large_tasks,
        'edges': [],
    }
    c.row('swarm', large_swarm)
    monkeypatch.setattr(sources, 'swarm', lambda path, profile: ([large_swarm], 100))
    snapshot = collect(config(tmp_path), 100)
    swarm_source = next(source for source in snapshot['sources'] if source['kind'] == 'swarm')
    assert swarm_source['status'] == 'unavailable'
    assert swarm_source['reason'] == 'source_failed'
    assert swarm_source['rows'] == []
    encoded = c.encode(snapshot)
    assert len(encoded) <= c.MAX_BYTES


def test_swarm_collect_and_staleness_are_fail_closed(tmp_path, monkeypatch):
    path = tmp_path / 'swarm.json'
    path.write_text(json.dumps(swarm_payload()))
    monkeypatch.setattr(sources, 'SWARM_PATH', str(path))
    value = collect(config(tmp_path), 101)
    swarm_source = next(s for s in value['sources'] if s['kind'] == 'swarm')
    assert swarm_source['profile'] == 'quantlab'
    assert swarm_source['status'] == 'available'
    assert swarm_source['observed_at'] == 100
    assert swarm_source['rows'][0]['tasks'][0]['task_id'] == 'child'

    projected = c.project(value, ('quantlab',), 191)
    swarm_source = next(s for s in projected['sources'] if s['kind'] == 'swarm')
    assert swarm_source['status'] == 'unavailable'
    assert swarm_source['reason'] == 'stale'
    assert swarm_source['rows'] == []


def config(tmp_path):
    return dict(version=1, output=str(tmp_path / 'snapshot.json'), herdr=None,
                profiles={p: dict(router=None, search=None, kanban=None, git=None, tests=None) for p in c.PROFILES})


def test_release_projection_is_fixed_bounded_and_sanitized(tmp_path, monkeypatch):
    path = tmp_path / 'deployed-release.json'
    payload = dict(version=1, tag='v0.2.0-rc.2', commit='a' * 40,
                   config_sha256='b' * 64, deployed_at=100)
    path.write_text(json.dumps(payload))
    monkeypatch.setattr(sources, 'RELEASE_PATH', str(path))
    rows, stamp = sources.release(str(path), 'quantlab')
    assert rows == [{key: payload[key] for key in ('tag', 'commit', 'config_sha256', 'deployed_at')}]
    assert stamp == 100 and 'version' not in rows[0]
    with pytest.raises(ValueError):
        sources.release(str(path), 'majak')
    payload['prompt'] = 'PRIVATE'
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        sources.release(str(path), 'quantlab')



def test_export_configuration_accepts_legacy_profile_shape_during_search_rollout(tmp_path):
    cfg = dict(version=1, output=str(tmp_path / 'snapshot.json'), herdr=None,
               profiles={p: dict(router=None, kanban=None, git=None, tests=None) for p in c.PROFILES})
    normalized = configuration(cfg)
    assert all(settings['search'] is None for settings in normalized['profiles'].values())
    assert all(set(settings) == {'router', 'search', 'kanban', 'git', 'tests'}
               for settings in normalized['profiles'].values())

def test_export_partial_failure_and_zero_different(tmp_path):
    cfg = config(tmp_path)
    path = tmp_path / 'router.db'; router_db(path)
    cfg['profiles']['majak']['router'] = str(path)
    cfg['profiles']['quantlab']['router'] = str(tmp_path / 'missing.db')
    value = collect(cfg, 100)
    a = next(s for s in value['sources'] if s['profile'] == 'majak' and s['kind'] == 'router')
    b = next(s for s in value['sources'] if s['profile'] == 'quantlab' and s['kind'] == 'router')
    assert a['status'] == 'available' and b['status'] == 'unavailable' and not Path(cfg['profiles']['quantlab']['router']).exists()
    cfg['profiles']['quantlab']['router'] = str(path)
    with pytest.raises(ValueError):
        configuration(cfg)


def test_herdr_sanitizer_uses_explicit_pane_binding_and_drops_raw():
    raw = dict(id='cli:agent:list', result=dict(type='agent_list', agents=[dict(name='majak-hermes', agent_status='working', pane_id='p1', cwd='PRIVATE', terminal_title='SECRET')]))
    binding = {'majak-hermes': dict(profile='majak', pane_id='p1')}
    result = sanitize(json.dumps(raw).encode(), 100, binding)
    assert result['agents'] == [dict(agent='majak-hermes', status='working')]
    assert 'PRIVATE' not in json.dumps(result)
    binding['majak-hermes']['pane_id'] = 'p2'
    with pytest.raises(ValueError):
        sanitize(json.dumps(raw).encode(), 100, binding)


def test_command_output_bound_timeout_and_clean_environment():
    assert sources.command(['/usr/bin/printf', 'ok']) == b'ok'
    with pytest.raises(ValueError):
        sources.command(['/usr/bin/printf', 'oversized'], limit=2)
    with pytest.raises(ValueError):
        sources.command(['/usr/bin/sleep', '3'], timeout=0.1)
    env = sources.command(['/usr/bin/env'])
    assert b'HERMES' not in env and b'HERDR' not in env and b'API_KEY' not in env


@pytest.mark.parametrize('field', ['prompt', 'tool_args', 'memory', 'credentials', 'send_token', 'error_message', 'remote_uri'])
def test_sensitive_keys_rejected_at_source_and_row(field):
    value = c.unavailable(100)
    value['sources'][0][field] = 'PRIVATE'
    with pytest.raises(ValueError):
        c.decode(json.dumps(value).encode())


def test_copy_context_isolation(tmp_path, auth):
    from contextvars import copy_context
    a = Application(str(snapshot_file(tmp_path)), auth[0], now=lambda: 100)
    b = Application(a.snapshot_path, dict(auth[0], profiles=['quantlab']), now=lambda: 100)
    for app, expected in ((a, 'majak'), (b, 'quantlab'), (a, 'majak')):
        response = copy_context().run(request, app, auth[1], '/agent-platform/api/v1/overview')
        assert {s['profile'] for s in json.loads(response[2])['sources']} == {expected}


def test_empty_router_is_measured_zero_not_unavailable(tmp_path):
    path = tmp_path / 'router.db'; router_db(path)
    db = sqlite3.connect(path); db.execute('DELETE FROM requests'); db.commit(); db.close()
    cfg = config(tmp_path); cfg['profiles']['majak']['router'] = str(path)
    source = next(s for s in collect(cfg, 100)['sources'] if s['profile'] == 'majak' and s['kind'] == 'router')
    assert source['status'] == 'available' and source['rows'] == [] and source['data_at'] is None


def test_report_identity_staleness_and_closed_fields(tmp_path):
    path = tmp_path / 'result.json'
    value = dict(version=1, profile='majak', observed_at=10, passed=25, failed=0, artifact_digest='a'*64)
    path.write_text(json.dumps(value))
    assert sources.tests(str(path), 'majak')[0][0]['passed'] == 25
    with pytest.raises(ValueError):
        sources.tests(str(path), 'quantlab')
    cfg = config(tmp_path); cfg['profiles']['majak']['tests'] = str(path)
    result = collect(cfg, 90000)
    assert next(s for s in result['sources'] if s['profile']=='majak' and s['kind']=='tests')['status']=='unavailable'
    value['error_message'] = 'PRIVATE'; path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        sources.tests(str(path), 'majak')


def test_window_and_row_limit_fail_closed(tmp_path):
    path = tmp_path / 'router.db'; router_db(path)
    db = sqlite3.connect(path)
    db.executemany('INSERT INTO requests(id,task_id) VALUES(?,?)', [(i, str(i)) for i in range(2, 53)])
    db.commit(); db.close()
    with pytest.raises(ValueError):
        sources.router(str(path), 'majak')


def test_source_baseexception_not_swallowed(tmp_path, monkeypatch):
    cfg = config(tmp_path); cfg['profiles']['majak']['git'] = str(tmp_path)
    def fail(*args):
        raise KeyboardInterrupt
    monkeypatch.setattr(sources, 'git', fail)
    with pytest.raises(KeyboardInterrupt):
        collect(cfg, 100)


def test_credential_derivation_and_admin_refusal_without_generation(monkeypatch):
    from agent_platform_dashboard import production_credentials as credentials
    password = hashlib.sha256(b'isolated synthetic material').hexdigest()
    value = credentials.material(password, bytes(16))
    assert password not in json.dumps(value) and value['profiles'] == ['majak','quantlab']
    def forbidden(*args):
        pytest.fail('generation before admin approval')
    monkeypatch.setattr(credentials.secrets, 'token_urlsafe', forbidden)
    monkeypatch.setattr(os, 'geteuid', lambda: 1000)
    assert credentials.main(['--confirm','/etc/agent-platform/credentials']) == 78


def test_bad_json_types_duplicate_and_unbounded_denied():
    for raw in (b'{"version":1,"version":1}', b'NaN', b'null', b' '*131073):
        with pytest.raises(ValueError):
            c.decode(raw)


def test_auth_wrong_and_forwarded_identity_no_bypass(tmp_path, auth):
    app = Application(str(snapshot_file(tmp_path)), auth[0], now=lambda:100)
    for header in ('Bearer PRIVATE', 'Basic $$$', 'Basic '+base64.b64encode(b'michal:'+b'x'*32).decode()):
        assert request(app, header)[0].startswith('401')
    status, _, _ = app.response(dict(HTTP_HOST='127.0.0.1:3010', HTTP_X_REMOTE_USER='michal', REQUEST_METHOD='GET', PATH_INFO='/agent-platform/'))
    assert status.startswith('401')


def test_production_template_boundaries():
    import configparser
    bundle = Path(__file__).resolve().parents[2] / 'deploy/agent_platform/production'
    for role in ('web','export','herdr'):
        unit = configparser.ConfigParser(interpolation=None)
        unit.optionxform=str
        unit.read(bundle/f'agent-platform-{role}.service.in')
        service=unit['Service']
        assert service['User'] != 'root' and service['Restart']=='no'
        assert service['ProtectSystem']=='strict' and service['NoNewPrivileges']=='yes'
        assert service['ProtectKernelTunables']=='yes' and service['ProtectKernelModules']=='yes'
        assert service['ProtectControlGroups']=='yes' and service['RestrictNamespaces']=='yes'
        assert service['RestrictSUIDSGID']=='yes' and service['LockPersonality']=='yes'
        assert service['StandardOutput']=='null'
    web=(bundle/'agent-platform-web.service.in').read_text()
    assert 'SocketBindAllow=ipv4:tcp:3010' in web and 'ProtectHome=yes' in web
    export=(bundle/'agent-platform-export.service.in').read_text()
    assert 'Wants=agent-platform-herdr.service' in export and 'After=agent-platform-herdr.service' in export
    common=(bundle/'nginx-location-common.conf.in').read_text()
    assert 'auth_basic_user_file' in common and 'Authorization $http_authorization' in common
    assert 'proxy_pass http://127.0.0.1:3010;' in common and 'proxy_next_upstream off' in common
    server=(bundle/'nginx-server.conf.in').read_text()
    assert 'location / {' not in server and 'location ^~ /agent-platform/' in server
    assert 'listen ' not in server
    maintenance=(bundle/'nginx-maintenance.conf.in').read_text()
    assert 'location = /agent-platform {' in maintenance
    assert 'location ^~ /agent-platform/' in maintenance
    assert 'location @agent_platform_unavailable' in maintenance
    assert 'return 503' in maintenance and 'proxy_pass' not in maintenance


def test_herdr_partial_bindings_do_not_claim_other_profile_zero(tmp_path):
    raw = dict(id='cli:agent:list', result=dict(type='agent_list', agents=[dict(name='majak-hermes', agent_status='working', pane_id='p1')]))
    sanitized = sanitize(json.dumps(raw).encode(), 100, {'majak-hermes': dict(profile='majak', pane_id='p1')})
    assert sanitized['profiles'] == ['majak']
    path=tmp_path/'herdr.json'; path.write_text(json.dumps(sanitized))
    cfg=config(tmp_path); cfg['herdr']=str(path)
    rows={s['profile']:s for s in collect(cfg, 100)['sources'] if s['kind']=='herdr'}
    assert rows['majak']['status']=='available'
    assert rows['quantlab']['status']=='unavailable' and rows['quantlab']['reason']=='not_configured'
    assert rows['quantlab']['rows']==[] and rows['quantlab']['data_at'] is None
    sanitized['profiles'].append('quantlab'); path.write_text(json.dumps(sanitized))
    with pytest.raises(ValueError):
        sources.herdr(str(path),'quantlab',100)


def test_real_nonseekable_terminal_confirmation_and_output(capsys):
    import pty
    from agent_platform_dashboard.production_credentials import terminal
    master,slave=pty.openpty()
    try:
        with terminal(os.ttyname(slave)) as (reader,writer):
            assert not reader.seekable() and not writer.seekable()
            os.write(master,b'CREATE michal\n')
            assert reader.readline(80).strip()=='CREATE michal'
            writer.write('synthetic display sentinel\n'); writer.flush()
            output=os.read(master,4096)
            if b'synthetic display sentinel' not in output:
                output+=os.read(master,4096)
            assert b'synthetic display sentinel' in output
        assert capsys.readouterr().out==''
    finally:
        os.close(master); os.close(slave)


def test_credential_setup_success_tty_only_no_real_generation(tmp_path,monkeypatch,capsys):
    from contextlib import contextmanager
    from io import StringIO
    from types import SimpleNamespace
    from agent_platform_dashboard import production_credentials as cred
    destination=tmp_path/'credentials'
    original_path=Path
    monkeypatch.setattr(cred,'Path',lambda value: destination if value=='/etc/agent-platform/credentials' else original_path(value))
    monkeypatch.setattr(os,'geteuid',lambda:0)
    monkeypatch.setattr(os,'fstat',lambda fd:SimpleNamespace(st_uid=0,st_mode=0o40700))
    monkeypatch.setattr(os,'chown',lambda *args:None)
    monkeypatch.setattr(os,'fchown',lambda *args:None)
    monkeypatch.setattr(cred.grp,'getgrnam',lambda name:SimpleNamespace(gr_gid=os.getgid()))
    monkeypatch.setattr(cred.secrets,'token_urlsafe',lambda count:'T'*48)
    monkeypatch.setattr(cred.secrets,'token_bytes',lambda count:bytes(count))
    calls=[]
    def openssl(argv,**kwargs):
        assert argv==['/usr/bin/openssl','passwd','-6','-stdin']
        assert kwargs['input']==b'T'*48+b'\n'
        assert 'T'*48 not in str(argv) and 'T'*48 not in str(kwargs['env'])
        calls.append(argv)
        return SimpleNamespace(stdout=b'$6$synthetic-test-only\n')
    monkeypatch.setattr(cred.subprocess,'run',openssl)
    output=StringIO()
    @contextmanager
    def fake_terminal():
        yield StringIO('CREATE michal\n'),output
    monkeypatch.setattr(cred,'terminal',fake_terminal)
    assert cred.main(['--confirm',str(destination)])==0
    assert output.getvalue().count('T'*48)==1 and len(calls)==1
    assert 'T'*48 not in (destination/'auth.json').read_text()
    assert 'T'*48 not in (destination/'htpasswd').read_text()
    assert capsys.readouterr().out==''
    assert cred.main(['--confirm',str(destination)])==78
    assert output.getvalue().count('T'*48)==1 and len(calls)==1


def test_git_allowlist_read_projection_real_temp_repo(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir()
    subprocess.run(['/usr/bin/git','init','-q',str(repo)],check=True)
    item=repo/'tracked.txt'; item.write_text('synthetic PRIVATE content')
    subprocess.run(['/usr/bin/git','-C',str(repo),'add','tracked.txt'],check=True)
    subprocess.run(['/usr/bin/git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@localhost','commit','-qm','synthetic'],check=True)
    clean,_=sources.git(str(repo),'majak')
    assert clean[0]['dirty'] is False
    item.write_text('changed synthetic content')
    dirty,_=sources.git(str(repo),'majak')
    assert dirty[0]['dirty'] is True and dirty[0]['commit']==clean[0]['commit']
    assert 'content' not in json.dumps(dirty) and 'tracked.txt' not in json.dumps(dirty)


def test_file_exact_limit_is_allowed(tmp_path):
    file=tmp_path/'metadata'; file.write_bytes(b'x'*4096)
    assert io.read(str(file),4096)==b'x'*4096


def test_cli_preflight_default_denied_without_listener(monkeypatch):
    from agent_platform_dashboard import production_web as web
    from agent_platform_dashboard import production_export as exporter
    from agent_platform_dashboard import production_herdr as bridge
    def forbidden(*args,**kwargs):
        pytest.fail('unexpected startup')
    monkeypatch.setattr(socket,'socket',forbidden)
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    assert web.main([])==78 and exporter.main([])==78 and bridge.main([])==78


def test_startup_requires_fresh_mandatory_profile_sources(auth, monkeypatch):
    from agent_platform_dashboard import production_web as web
    value=c.unavailable(100)
    cfg=dict(version=1,snapshot='/snapshot.json',auth='/auth.json')
    def reader(path,limit,**kwargs):
        if path=='/config.json':
            assert kwargs['owner']==0
            return json.dumps(cfg).encode()
        if path=='/auth.json':
            assert kwargs['owner']==0 and kwargs['private']
            return json.dumps(auth[0]).encode()
        assert path=='/snapshot.json'
        return c.encode(value)
    monkeypatch.setattr(web,'read',reader)
    monkeypatch.setattr(web.time,'time',lambda:100)
    with pytest.raises(ValueError):
        web.load('/config.json')
    for source in value['sources']:
        if source['profile']=='majak' and source['kind'] in ('herdr','router'):
            source.update(status='available',reason='ok')
            if source['kind']=='herdr':
                source['rows']=[dict(agent='majak-hermes',status='working')]
    assert isinstance(web.load('/config.json'),Application)
    monkeypatch.setattr(web.time,'time',lambda:191)
    with pytest.raises(ValueError):
        web.load('/config.json')


def test_startup_requires_deployed_release_identity_for_quantlab(auth, monkeypatch):
    from agent_platform_dashboard import production_web as web
    value = c.unavailable(100)
    auth_record = dict(auth[0], profiles=['majak', 'quantlab'])
    cfg = dict(version=1, snapshot='/snapshot.json', auth='/auth.json')
    for source in value['sources']:
        if source['kind'] in ('herdr', 'router'):
            source.update(status='available', reason='ok')
            if source['kind'] == 'herdr':
                source['rows'] = [dict(agent=source['profile'] + '-hermes', status='working')]
    def reader(path, limit, **kwargs):
        if path == '/config.json':
            return json.dumps(cfg).encode()
        if path == '/auth.json':
            return json.dumps(auth_record).encode()
        return c.encode(value)
    monkeypatch.setattr(web, 'read', reader)
    monkeypatch.setattr(web.time, 'time', lambda: 100)
    with pytest.raises(ValueError):
        web.load('/config.json')
    release = next(source for source in value['sources'] if source['kind'] == 'release')
    release.update(status='available', reason='ok', data_at=100,
                   rows=[dict(tag='v0.2.0-rc.2', commit='a' * 40,
                              config_sha256='b' * 64, deployed_at=100)])
    assert isinstance(web.load('/config.json'), Application)


def test_machine_city_shell_assets_and_csp(tmp_path, auth):
    app = Application(str(snapshot_file(tmp_path)), auth[0], now=lambda: 100)
    status, headers, body = request(app, auth[1], '/agent-platform/')
    assert status == '200 OK' and b'id="machine-scene"' in body
    assert b'machine-city.js' in body and b'SERVER_FALLBACK' not in body
    assert "script-src 'self'" in headers['Content-Security-Policy']
    for path, marker in (('/agent-platform/machine-city.css', b'.film-view'),
                         ('/agent-platform/machine-city.js', b'WebGLRenderer'),
                         ('/agent-platform/machine-city-background.webp', b'RIFF')):
        status, _, body = request(app, auth[1], path)
        assert status == '200 OK' and marker in body


def test_router_projection_exposes_only_bounded_operational_model_metadata(tmp_path):
    path = tmp_path / 'router.db'; router_db(path)
    rows, _ = sources.router(str(path), 'majak')
    assert rows == [dict(task_id=c.identity('majak', 'task'), actual_model='model-a',
                        provider='nous', requests=1, input_tokens=3, output_tokens=4,
                        cost_microusd=None, fallback_count=0, successful_requests=1,
                        duration_ms=1000, last_used_at=11)]
    assert 'PRIVATE' not in json.dumps(rows) and 'SECRET' not in json.dumps(rows)
