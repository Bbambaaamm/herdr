"""Strict fixture metadata and scope contracts, without filesystem sources."""
from dataclasses import asdict, replace
import json

import pytest

from agent_platform_dashboard import contracts as c, fixtures as f


def scope(profile='a', board='b'):
    return c.Scope('1' * 64, board * 64, '2' * 64, profile * 64, 'majak')


def snapshot():
    return c.Snapshot(1, 100, '3' * 64, (
        c.AgentRow(scope(), '4' * 64, 'working'),
        c.TaskRow(scope(), '5' * 64, '6' * 64, 'running'),
        c.RouterRow(scope(), '7' * 64, 'nous', 'fixture-free', None, 12, None, 'baseline'),
        c.RepoRow(scope(), '8' * 64, '9' * 40, False),
        c.ReportRow(scope(), 'a' * 64, 'passed', 35, 0, 'b' * 64),
    ))


def encoded(s=None):
    s = snapshot() if s is None else s
    return json.dumps({'version': s.version, 'observed_at': s.observed_at,
                       'source_version': s.source_version,
                       'rows': [dict(kind=c.KINDS[type(row)], **asdict(row)) for row in s.rows]}).encode()


def test_roundtrip_and_unknown_cost():
    assert f.decode_snapshot(encoded()) == snapshot()
    assert snapshot().rows[2].cost_microusd is None


@pytest.mark.parametrize('name', ['prompt', 'args', 'output', 'memory', 'credentials', 'send_token',
                                  'error_message', 'diff', 'remote_uri', 'title'])
def test_sensitive_fields_fail_closed(name):
    raw = json.loads(encoded())
    raw['rows'][0][name] = 'PRIVATE<script>'
    with pytest.raises(c.Invalid) as caught:
        f.decode_snapshot(json.dumps(raw).encode())
    assert 'PRIVATE' not in str(caught.value)


@pytest.mark.parametrize(
    'bad',
    [b'{', b'[]', b'{"version":1,"version":1}', b'NaN', b' ' * 65537],
    ids=('truncated', 'array', 'duplicate-key', 'nan', 'oversized'),
)
def test_malformed_duplicate_and_oversized_json(bad):
    with pytest.raises(c.Invalid):
        f.decode_snapshot(bad)


@pytest.mark.parametrize('field,value', [('input_tokens', True), ('output_tokens', -1),
    ('cost_microusd', -1), ('provider', 'secret'), ('model', '<script>'), ('reason', 'raw error')])
def test_strict_router_fields(field, value):
    with pytest.raises(c.Invalid):
        replace(snapshot().rows[2], **{field: value})


def test_scope_and_row_bounds():
    with pytest.raises(c.Invalid):
        replace(scope(), board_name='../../')
    with pytest.raises(c.Invalid):
        replace(scope(), profile_id='unknown')
    with pytest.raises(c.Invalid):
        replace(snapshot(), rows=snapshot().rows * 50)
    with pytest.raises(c.Invalid):
        replace(snapshot(), rows=(snapshot().rows[0],) * 2)
    with pytest.raises(c.Invalid):
        replace(snapshot(), version=True)


def test_projection_is_grant_scoped_with_stale_and_clock_unknown():
    s = snapshot()
    other = replace(s.rows[0], scope=scope('c'))
    s = replace(s, rows=s.rows + (other,))
    grant = c.Grant('d' * 64, (scope(),), 200)
    result = c.project(s, grant, now=131)
    assert result['stale'] is True and result['availability'] == 'stale'
    assert len(result['rows']) == 5
    assert c.project(s, grant, now=99)['availability'] == 'unknown'
    assert c.project(s, grant, now=100)['stale'] is False
    with pytest.raises(c.Invalid):
        c.project(s, grant, now=200)
    with pytest.raises(c.Invalid):
        c.project(s, None, now=101)


def test_raw_path_strings_are_not_fixture_inputs():
    for data in ('/home/live.db', '../snapshot.json', b'file:///tmp/symlink', bytearray(encoded())):
        with pytest.raises(c.Invalid):
            f.decode_snapshot(data)


def test_hard_row_limit_and_explicit_empty_snapshot():
    base = snapshot().rows[0]
    rows = tuple(replace(base, record_id=f'{i:064x}') for i in range(200))
    assert len(replace(snapshot(), rows=rows).rows) == 200
    with pytest.raises(c.Invalid):
        replace(snapshot(), rows=rows + (replace(base, record_id='f'*64),))
    empty = replace(snapshot(), rows=())
    assert f.decode_snapshot(encoded(empty)) == empty


def test_forged_types_and_unknown_nested_fields_deny():
    raw = json.loads(encoded())
    raw['rows'][0]['scope']['path'] = '../escape'
    with pytest.raises(c.Invalid):
        f.decode_snapshot(json.dumps(raw).encode())
    class Forged(c.AgentRow):
        pass
    with pytest.raises(c.Invalid):
        Forged(scope(), 'f'*64, 'idle')
