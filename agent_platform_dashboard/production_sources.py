"""Exporter-only fixed read projections. Never imported by the HTTP application."""
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import os
import math
from pathlib import Path
import selectors
import signal
import sqlite3
import subprocess
import tempfile
import time
from urllib.parse import quote

from . import production_contract as c
from .production_io import read, regular

SAFE_ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
            'HOME': '/nonexistent', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
            'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0'}
QUEUE_PATH = '/var/lib/agent-platform-herdr/queue.json'
CODEX_USAGE_PATH = '/var/lib/agent-platform-herdr/codex-usage.json'
MODEL_ROUTING_PATH = '/var/lib/agent-platform-herdr/model-routing.json'
ADMISSION_PATH = '/var/lib/agent-platform-herdr/admission.jsonl'
RELEASE_PATH = '/var/lib/agent-platform-herdr/deployed-release.json'
SWARM_PATH = '/var/lib/agent-platform-herdr/swarm.json'
SWARM_FALLBACK_PATH = '/var/lib/agent-platform-herdr/agent-stack-swarm.json'
SWARM_FRESH_SECONDS = 90


class StaleSource(ValueError):
    pass


def command(argv, *, env=None, limit=65536, timeout=3):
    """Bound bytes while draining; no communicate() allocation of unlimited output."""
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, env=SAFE_ENV if env is None else env,
                               start_new_session=True, close_fds=True)
    deadline = time.monotonic() + timeout
    result = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                left = deadline - time.monotonic()
                c.need(left > 0)
                if not selector.select(left):
                    raise ValueError('source_timeout')
                chunk = os.read(process.stdout.fileno(), min(8192, limit + 1 - len(result)))
                if not chunk:
                    break
                result.extend(chunk)
                c.need(len(result) <= limit)
        c.need(process.wait(timeout=max(0.01, deadline - time.monotonic())) == 0)
        return bytes(result)
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=1)
        process.stdout.close()


MAX_DATABASE_BYTES = 64 * 1024 * 1024


def _same_file(before, after):
    return (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)


def _sidecar(stack, path):
    try:
        stack.enter_context(regular(path))
        return True
    except FileNotFoundError:
        return False


@contextmanager
def _clean_wal_copy(path, fd, before):
    """Copy a checkpointed WAL main file without touching its read-only source."""
    c.need(0 < before.st_size <= MAX_DATABASE_BYTES)
    with tempfile.TemporaryDirectory(prefix='agent-platform-router-') as folder:
        copied = os.path.join(folder, 'router.db')
        target = os.open(copied, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600)
        offset = 0
        try:
            with os.fdopen(target, 'wb') as stream:
                while offset < before.st_size:
                    chunk = os.pread(fd, min(1024 * 1024, before.st_size - offset), offset)
                    c.need(bool(chunk))
                    stream.write(chunk)
                    offset += len(chunk)
                stream.flush()
            c.need(offset == before.st_size and _same_file(before, os.fstat(fd)))
            with ExitStack() as check:
                c.need(not _sidecar(check, path + '-wal') and not _sidecar(check, path + '-shm'))
            yield copied
        except BaseException:
            if offset < before.st_size:
                try:
                    os.close(target)
                except OSError:
                    pass
            raise


@contextmanager
def _authorized(path, table, columns):
    connection = sqlite3.connect('file:' + quote(path, safe='/') + '?mode=ro', uri=True, timeout=0.25)
    try:
        connection.execute('PRAGMA query_only=ON')
        connection.execute('PRAGMA trusted_schema=OFF')
        c.need(connection.execute('PRAGMA query_only').fetchone() == (1,))
        c.need(connection.execute('PRAGMA trusted_schema').fetchone() == (0,))
        c.need(connection.execute('SELECT type FROM sqlite_schema WHERE name=?', (table,)).fetchone() == ('table',))
        # table names are module constants, never supplied by config or HTTP.
        c.need(columns <= {r[1] for r in connection.execute('PRAGMA table_info(' + table + ')')})
        deadline = time.monotonic() + 1
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        allowed_functions = {'count', 'sum', 'max', 'min', 'coalesce', 'typeof'}
        def authorize(action, arg1, arg2, database, trigger):
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ and arg1 == table and arg2 in columns and database == 'main' and trigger is None:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and arg2 in allowed_functions:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        connection.set_authorizer(authorize)
        yield connection
    finally:
        connection.close()


@contextmanager
def readonly(path, table, columns):
    """Read a SQLite source without mutating it; copy a clean WAL checkpoint privately."""
    with regular(path) as (fd, before):
        c.need(before.st_size <= MAX_DATABASE_BYTES)
        if os.pread(fd, 20, 0)[18:20] == b'\x02\x02':
            with ExitStack() as sidecars:
                present = tuple(_sidecar(sidecars, path + suffix) for suffix in ('-wal', '-shm'))
                if any(present):
                    c.need(all(present))
                    with _authorized(path, table, columns) as connection:
                        yield connection
                else:
                    with _clean_wal_copy(path, fd, before) as copied:
                        with _authorized(copied, table, columns) as connection:
                            yield connection
        else:
            with _authorized(path, table, columns) as connection:
                yield connection
        c.need(_same_file(before, os.stat(path, follow_symlinks=False)))


ROUTER_COLUMNS = {'id', 'task_id', 'started_at', 'ended_at', 'input_tokens', 'output_tokens',
                  'cost_usd', 'actual_model', 'provider', 'fallback_used', 'success', 'duration_s'}
ROUTER_SQL = '''SELECT task_id,actual_model,provider,count(*),
CASE WHEN count(input_tokens)=count(*) THEN sum(input_tokens) END,
CASE WHEN count(output_tokens)=count(*) THEN sum(output_tokens) END,
CASE WHEN count(cost_usd)=count(*) THEN sum(cost_usd) END,
sum(coalesce(fallback_used,0)),
sum(CASE WHEN success=1 THEN 1 ELSE 0 END),
CASE WHEN count(duration_s)=count(*) THEN sum(duration_s) END,
max(coalesce(ended_at,started_at)) FROM
(SELECT id,task_id,actual_model,provider,started_at,ended_at,input_tokens,output_tokens,
        cost_usd,fallback_used,success,duration_s
 FROM requests ORDER BY id DESC LIMIT 1000)
GROUP BY task_id,actual_model,provider LIMIT 51'''


def router(path, profile):
    with readonly(path, 'requests', ROUTER_COLUMNS) as db:
        records = db.execute(ROUTER_SQL).fetchall()
    c.need(len(records) <= 50)
    rows, timestamps = [], []
    for task, model, provider, count, inputs, outputs, cost, fallbacks, successes, duration, stamp in records:
        c.need(cost is None or type(cost) in (int, float) and 0 <= cost < 10**8)
        c.need(duration is None or type(duration) in (int, float) and 0 <= duration < 10**9)
        c.need(type(stamp) in (int, float) and 0 <= stamp < 2**53)
        last_used_at = stamp
        item = dict(task_id=None if task is None else c.identity(profile, task),
                    actual_model=model, provider=provider, requests=count,
                    input_tokens=inputs, output_tokens=outputs,
                    cost_microusd=None if cost is None else round(cost * 1000000),
                    fallback_count=fallbacks, successful_requests=successes,
                    duration_ms=None if duration is None else round(duration * 1000),
                    last_used_at=last_used_at)
        c.row('router', item)
        rows.append(item)
        timestamps.append(int(last_used_at))
    return rows, max(timestamps, default=None)


SEARCH_COLUMNS = {
    'id', 'started_at', 'ended_at', 'route_mode', 'actual_provider', 'fallback_provider',
    'fallback_used', 'duration_ms', 'result_count', 'extract_count', 'success', 'cost_usd'
}
SEARCH_SQL = '''SELECT route_mode,actual_provider,fallback_provider,count(*),
sum(CASE WHEN success=1 THEN 1 ELSE 0 END),
sum(duration_ms),max(duration_ms),sum(coalesce(fallback_used,0)),
CASE WHEN count(cost_usd)=count(*) THEN sum(cost_usd) END,
sum(result_count),sum(extract_count),max(coalesce(ended_at,started_at)) FROM
(SELECT id,started_at,ended_at,route_mode,actual_provider,fallback_provider,
        fallback_used,duration_ms,result_count,extract_count,success,cost_usd
 FROM searches ORDER BY id DESC LIMIT 1000)
GROUP BY route_mode,actual_provider,fallback_provider LIMIT 51'''


def search(path, profile):
    with readonly(path, 'searches', SEARCH_COLUMNS) as db:
        records = db.execute(SEARCH_SQL).fetchall()
    c.need(len(records) <= 50)
    rows, timestamps = [], []
    for mode, provider, fallback_provider, count, successes, duration, maximum, fallbacks, cost, results, extracts, stamp in records:
        c.need(type(duration) in (int, float) and 0 <= duration < 10**12)
        c.need(type(maximum) in (int, float) and 0 <= maximum <= duration)
        c.need(cost is None or type(cost) in (int, float) and 0 <= cost < 10**8)
        c.need(type(stamp) in (int, float) and 0 <= stamp < 2**53)
        last_used_at = stamp
        item = dict(
            route_mode=mode, provider=provider, fallback_provider=fallback_provider,
            searches=count, successful_searches=successes,
            duration_ms=round(duration), max_duration_ms=round(maximum),
            fallback_count=fallbacks,
            cost_microusd=None if cost is None else round(cost * 1000000),
            result_count=results, extract_count=extracts, last_used_at=last_used_at,
        )
        c.row('search', item)
        rows.append(item)
        timestamps.append(int(last_used_at))
    return rows, max(timestamps, default=None)


def kanban(source, profile):
    with readonly(source['path'], 'tasks', {'id', 'status', 'current_run_id', 'created_at'}) as db:
        records = db.execute('SELECT id,status,current_run_id,created_at FROM tasks ORDER BY created_at DESC,id LIMIT 51').fetchall()
    c.need(len(records) <= 50)
    rows, timestamps = [], []
    for task, status, run, stamp in records:
        item = dict(task_id=c.identity(profile, task), status=status, run_id=run)
        c.row('kanban', item)
        c.need(c.number(stamp))
        rows.append(item)
        timestamps.append(stamp)
    return rows, max(timestamps, default=None)


def git(path, profile):
    # Explicit registry path; never use git discovery from process cwd.
    c.need(Path(path).is_dir() and Path(path).resolve().as_posix() == path)
    args = ['/usr/bin/git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', '-C', path]
    commit = command(args + ['rev-parse', '--verify', 'HEAD'], limit=128).decode('ascii').strip()
    dirty = bool(command(args + ['status', '--porcelain=v1', '-z', '--untracked-files=normal', '--ignore-submodules=all']))
    item = dict(commit=commit, dirty=dirty)
    c.row('git', item)
    return [item], None


def tests(path, profile):
    raw = c.parse(read(path, 4096), 4096)
    c.keys(raw, 'version profile observed_at passed failed artifact_digest')
    c.need(type(raw['version']) is int and raw['version'] == 1 and raw['profile'] == profile and c.number(raw['observed_at']))
    item = {k: raw[k] for k in ('passed', 'failed', 'artifact_digest')}
    c.row('tests', item)
    return [item], raw['observed_at']


def queue_payload(path):
    c.need(path == QUEUE_PATH)
    return c.parse(read(path, c.MAX_BYTES), c.MAX_BYTES)


def queue_from_payload(raw, profile):
    c.need(profile in c.PROFILES)
    version = raw.get('version') if type(raw) is dict else None
    if version == 2:
        c.keys(raw, 'version profile observed_at tasks')
        c.need(raw['profile'] == 'quantlab' and profile == 'quantlab'
               and c.number(raw['observed_at']) and type(raw['tasks']) is list
               and len(raw['tasks']) <= 50)
        rows = list(raw['tasks'])
    elif version == 3:
        c.keys(raw, 'version observed_at tasks')
        c.need(c.number(raw['observed_at']) and type(raw['tasks']) is list
               and len(raw['tasks']) <= 100)
        target_repo = {
            'quantlab': 'Bbambaaamm/Autonomous-Quant-Lab',
            'majak': 'Bbambaaamm/dotacni-majak',
        }[profile]
        rows = [item for item in raw['tasks'] if item.get('repo') == target_repo]
        c.need(len(rows) <= 50)
    else:
        raise ValueError('invalid_metadata')
    for item in raw['tasks']:
        c.row('queue', item)
    c.need(len({r['task_id'] for r in raw['tasks']}) == len(raw['tasks']))
    return rows, raw['observed_at']


def queue(path, profile):
    return queue_from_payload(queue_payload(path), profile)



def _swarm_stamp(value):
    c.need(type(value) in (int, float, str) and type(value) is not bool)
    try:
        stamp = float(value)
    except (TypeError, ValueError):
        raise ValueError('invalid_metadata') from None
    c.need(math.isfinite(stamp) and 0 <= stamp < 2**53)
    return int(stamp)


def swarm(path, profile):
    c.need(profile == 'quantlab' and path in (SWARM_PATH, SWARM_FALLBACK_PATH))
    raw = c.parse(read(path, c.MAX_BYTES), c.MAX_BYTES)
    required = {'tasks', 'edges', 'agents', 'repo', 'issue', 'observed_at', 'version', 'paper_only'}
    canonical = required | {'policy_profiles', 'graph_latency', 'clock_snapshot', 'ts'}
    c.need(type(raw) is dict and set(raw) in (required, canonical))
    c.need((raw['version'] == 1 and set(raw) == required)
           or (raw['version'] == 'v1.2.0' and set(raw) == canonical))
    c.need(type(raw['paper_only']) is bool)
    c.need(type(raw['repo']) is str and c.identifier(raw['repo'], 160))
    c.need(type(raw['issue']) is str and c.identifier(raw['issue'], 64))
    if raw['repo'] == 'Bbambaaamm/Autonomous-Quant-Lab':
        c.need(raw['paper_only'] is True)
    c.need(type(raw['tasks']) is list and len(raw['tasks']) <= 100)
    c.need(type(raw['edges']) is list and len(raw['edges']) <= 200)
    c.need(type(raw['agents']) is list and len(raw['agents']) <= 100)

    allowed_task = {
        'task_id', 'state', 'role', 'tools', 'permissions', 'timeout_seconds',
        'max_attempts', 'dependencies', 'parent_task_id', 'parent_agent_id',
        'agent_id', 'fencing_token', 'model', 'fallback_model', 'attempts',
        'attempt', 'blocker', 'policy_profile', 'paper_only', 'telemetry', 'ts',
        'child_ids', 'completed_at', 'created_at', 'event_ref', 'issue',
        'max_retries', 'repo', 'result_sha', 'updated_at',
    }
    tasks = []
    derived_edges = set()
    profiles = set()
    for item in raw['tasks']:
        c.need(type(item) is dict and {'task_id', 'state', 'role', 'dependencies'} <= set(item)
               and set(item) <= allowed_task)
        task_id = item['task_id']
        c.need(c.identifier(task_id, 256))
        parent_task_id = item.get('parent_task_id')
        parent_agent_id = item.get('parent_agent_id')
        agent_id = item.get('agent_id')
        dependencies = item.get('dependencies')
        c.need(type(dependencies) is list and len(dependencies) <= 64)
        for dep in dependencies:
            c.need(c.identifier(dep, 256))
            derived_edges.add((dep, task_id, 'dependency'))
        if parent_task_id is not None:
            c.need(c.identifier(parent_task_id, 256))
            derived_edges.add((parent_task_id, task_id, 'parent'))
        for optional in (parent_agent_id, agent_id):
            c.need(optional is None or c.identifier(optional, 256))
        profile_value = item.get('policy_profile')
        if profile_value is not None:
            c.need(c.identifier(profile_value, 64))
            profiles.add(profile_value)
        result_sha = item.get('result_sha')
        c.need(result_sha is None or c.hex_id(result_sha))
        task = {
            'task_id': task_id,
            'parent_task_id': parent_task_id,
            'parent_agent_id': parent_agent_id,
            'agent_id': agent_id,
            'state': item['state'],
            'role': item['role'],
            'model': item.get('model'),
            'fallback_model': item.get('fallback_model'),
            'attempt': item.get('attempts', item.get('attempt', 0)),
            'max_attempts': item.get('max_attempts', item.get('max_retries', 1)),
            'blocker': item.get('blocker'),
            'fencing_token': item.get('fencing_token', 0),
            'dependencies': list(dependencies),
            'result_sha': result_sha,
        }
        tasks.append(task)
    c.need(len({task['task_id'] for task in tasks}) == len(tasks))
    task_ids = {task['task_id'] for task in tasks}
    tasks_by_id = {task['task_id']: task for task in tasks}
    c.need(all(edge[0] in task_ids and edge[1] in task_ids for edge in derived_edges))

    raw_edges = set()
    for edge in raw['edges']:
        c.keys(edge, 'from to kind')
        c.need(c.identifier(edge['from'], 256) and c.identifier(edge['to'], 256)
               and edge['kind'] in ('parent', 'dependency'))
        raw_edges.add((edge['from'], edge['to'], edge['kind']))
    c.need(raw_edges == derived_edges)

    safe_agent_fields = {
        'agent_id', 'event_ref', 'fallback_model', 'fencing_token', 'holder',
        'issue', 'lease_until', 'model', 'parent_agent_id', 'parent_task_id',
        'repo', 'role', 'state', 'task_id',
    }
    scheduler_snapshot = raw['version'] == 'v1.2.0'
    agents = []
    seen_agent_ids = set()
    seen_agent_tasks = set()
    running_agent_tasks = set()
    for item in raw['agents']:
        c.need(type(item) is dict and set(item) <= safe_agent_fields)
        agent_id = item.get('agent_id')
        task_id = item.get('task_id')
        agent_state = item.get('state')
        c.need(c.identifier(agent_id, 256) and c.identifier(task_id, 256))
        c.need(agent_id not in seen_agent_ids and task_id not in seen_agent_tasks)
        seen_agent_ids.add(agent_id)
        seen_agent_tasks.add(task_id)
        parent_task_id = item.get('parent_task_id')
        parent_agent_id = item.get('parent_agent_id')
        c.need(parent_task_id is None or c.identifier(parent_task_id, 256))
        c.need(parent_agent_id is None or c.identifier(parent_agent_id, 256))
        fencing_token = item.get('fencing_token', 0)
        c.need(c.number(fencing_token))
        task = tasks_by_id.get(task_id)
        c.need(task is not None and task['agent_id'] == agent_id)
        c.need(task['parent_task_id'] == parent_task_id and task['parent_agent_id'] == parent_agent_id)
        c.need(task['fencing_token'] == fencing_token)
        if scheduler_snapshot:
            c.need(agent_state == task['state'])
        else:
            c.need(agent_state == 'running' and task['state'] == 'running')
        if agent_state == 'running':
            c.need(task['state'] == 'running')
            running_agent_tasks.add(task_id)
            agents.append({
                'agent_id': agent_id,
                'task_id': task_id,
                'state': 'running',
                'parent_task_id': parent_task_id,
                'parent_agent_id': parent_agent_id,
                'fencing_token': fencing_token,
            })
    expected_agent_tasks = {
        task['task_id'] for task in tasks
        if task['state'] == 'running' and task['agent_id'] is not None
    }
    c.need(running_agent_tasks == expected_agent_tasks)
    if scheduler_snapshot:
        expected_raw_agents = {
            task['task_id'] for task in tasks if task['agent_id'] is not None
        }
        c.need(seen_agent_tasks == expected_raw_agents)
    else:
        c.need(seen_agent_tasks == expected_agent_tasks)

    raw_profiles = raw.get('policy_profiles')
    if raw_profiles is not None:
        c.need(type(raw_profiles) is list and len(raw_profiles) <= 16)
        for profile_value in raw_profiles:
            c.need(c.identifier(profile_value, 64))
            profiles.add(profile_value)
    if raw['paper_only'] is True:
        profiles.add('quantlab-paper')

    repo = raw['repo']
    issue = raw['issue']
    snapshot = {
        'version': 1,
        'repo': repo,
        'issue': issue,
        'paper_only': raw['paper_only'],
        'policy_profiles': sorted(profiles),
        'agents': sorted(agents, key=lambda item: (item['task_id'], item['agent_id'])),
        'tasks': sorted(tasks, key=lambda item: item['task_id']),
        'edges': [
            {'from_task': left, 'to_task': right, 'kind': kind}
            for left, right, kind in sorted(derived_edges)
        ],
    }
    c.row('swarm', snapshot)
    return [snapshot], _swarm_stamp(raw['observed_at'])

def live_swarm(profile, now, max_age=SWARM_FRESH_SECONDS):
    c.need(profile == 'quantlab' and c.number(now) and c.number(max_age) and max_age >= 0)
    stale = False
    # Scheduler/runtime owns SWARM_PATH. Prefer it whenever it is fresh so a
    # live TaskGraph cannot be masked by the periodic Agent Stack fallback.
    # The fallback is a separate file and is considered only after the primary
    # becomes stale/unavailable.
    for path in dict.fromkeys((SWARM_PATH, SWARM_FALLBACK_PATH)):
        try:
            rows, stamp = swarm(path, profile)
        except (OSError, ValueError):
            continue
        if stamp > now:
            continue
        if now - stamp <= max_age:
            return rows, stamp
        stale = True
    if stale:
        raise StaleSource('stale')
    raise ValueError('swarm_unavailable')

def _tail_regular(path, limit=65536):
    with regular(path) as (fd, info):
        c.need(info.st_size >= 0)
        start = max(0, info.st_size - limit)
        data = os.pread(fd, min(limit, info.st_size), start)
        if start:
            split = data.find(b'\n')
            data = b'' if split < 0 else data[split + 1:]
        if data and not data.endswith(b'\n'):
            split = data.rfind(b'\n')
            data = b'' if split < 0 else data[:split + 1]
        return data, int(info.st_mtime)


def _admission_timestamp(value):
    c.need(type(value) is str and 1 <= len(value) <= 64)
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('invalid_metadata') from None
    c.need(parsed.tzinfo is not None)
    stamp = int(parsed.astimezone(timezone.utc).timestamp())
    c.need(c.number(stamp))
    return stamp


def admission(path, profile):
    c.need(profile == 'quantlab' and path == ADMISSION_PATH)
    raw, file_mtime = _tail_regular(path)
    rows = []
    for line in raw.splitlines():
        event = c.parse(line, 8192)
        c.need(type(event) is dict and event.get('event') in ('allow', 'deny', 'cancel'))
        if event['event'] == 'cancel':
            continue
        observed_at = _admission_timestamp(event.get('ts'))
        row = {
            'event': event['event'],
            'reason': event.get('reason') if event['event'] == 'deny' else None,
            'role': event.get('admit:role'),
            'repo': event.get('admit:repo'),
            'issue': event.get('admit:issue'),
            'node_count': event.get('admit:node_count'),
            'max_depth': event.get('admit:max_depth'),
            'max_fanout': event.get('admit:max_fanout'),
            'child_tools_count': event.get('admit:child_tools_count'),
            'agents_after': event.get('agents_after') if event['event'] == 'allow' else None,
            'observed_at': observed_at,
        }
        c.row('admission', row)
        rows.append(row)
    rows = rows[-50:]
    return rows, (rows[-1]['observed_at'] if rows else file_mtime)


def release(path, profile):
    c.need(profile == 'quantlab' and path == RELEASE_PATH)
    value = c.parse(read(path, 4096), 4096)
    c.keys(value, 'version tag commit config_sha256 deployed_at')
    c.need(value['version'] == 1)
    row = {name: value[name] for name in ('tag', 'commit', 'config_sha256', 'deployed_at')}
    c.row('release', row)
    return [row], row['deployed_at']


def _routing_summary(now):
    empty = {
        'routing_status': 'unavailable', 'routing_policy_version': None,
        'routing_observed_at': None, 'routing_soft_limit_pct': None,
        'routing_hard_limit_pct': None, 'routing_decisions': None,
        'routing_free': None, 'routing_sol': None, 'routing_astra': None,
        'routing_astra_escalations': None, 'routing_premium_denied': None,
        'last_route_at': None, 'last_route_tier': None,
        'last_route_model': None, 'last_route_reason': None,
    }
    try:
        raw = c.parse(read(MODEL_ROUTING_PATH, 65536), 65536)
        c.keys(raw, 'version observed_at policy totals recent')
        c.need(type(raw['version']) is int and raw['version'] == 1
               and c.number(raw['observed_at']) and raw['observed_at'] <= now)
        policy, totals, recent = raw['policy'], raw['totals'], raw['recent']
        c.keys(policy, 'version soft_limit_pct hard_limit_pct')
        c.keys(totals, 'decisions free sol astra astra_escalations premium_denied')
        c.need(c.identifier(policy['version'], 64))
        c.need(c.number(policy['soft_limit_pct']) and c.number(policy['hard_limit_pct'])
               and policy['soft_limit_pct'] < policy['hard_limit_pct'] <= 100)
        for value in totals.values():
            c.need(c.number(value))
        c.need(totals['free'] + totals['sol'] + totals['astra'] <= totals['decisions'])
        c.need(type(recent) is list and len(recent) <= 200)
        last = recent[-1] if recent else None
        if last is not None:
            legacy_keys = set(
                'at task_id issue attempt tier model selected_agent reason '
                'complexity_score codex_used_percent'.split()
            )
            v11_keys = legacy_keys | {
                'delivery_reconcile_count', 'coordinator_agent',
                'executor_agent', 'routing_scope',
            }
            c.need(type(last) is dict and set(last) in (legacy_keys, v11_keys))
            c.need(c.number(last['at']) and c.identifier(last['task_id'])
                   and (last['issue'] is None or c.number(last['issue']))
                   and c.number(last['attempt']) and last['tier'] in ('free', 'sol', 'astra')
                   and c.identifier(last['model']) and c.identifier(last['selected_agent'])
                   and c.identifier(last['reason'])
                   and type(last['complexity_score']) in (int, float)
                   and 0 <= last['complexity_score'] <= 1
                   and (last['codex_used_percent'] is None or c.number(last['codex_used_percent'])
                        and last['codex_used_percent'] <= 100))
            if set(last) == v11_keys:
                c.need(c.number(last['delivery_reconcile_count'])
                       and c.identifier(last['coordinator_agent'])
                       and c.identifier(last['executor_agent'])
                       and last['routing_scope'] == 'child_node')
        return {
            'routing_status': 'available', 'routing_policy_version': policy['version'],
            'routing_observed_at': raw['observed_at'], 'routing_soft_limit_pct': policy['soft_limit_pct'],
            'routing_hard_limit_pct': policy['hard_limit_pct'], 'routing_decisions': totals['decisions'],
            'routing_free': totals['free'], 'routing_sol': totals['sol'], 'routing_astra': totals['astra'],
            'routing_astra_escalations': totals['astra_escalations'],
            'routing_premium_denied': totals['premium_denied'],
            'last_route_at': None if last is None else last['at'],
            'last_route_tier': None if last is None else last['tier'],
            'last_route_model': None if last is None else last['model'],
            'last_route_reason': None if last is None else last['reason'],
        }
    except (FileNotFoundError, OSError, ValueError, KeyError, TypeError, UnicodeError):
        return empty


def codex(path, profile):
    c.need(profile == 'majak' and path == CODEX_USAGE_PATH)
    raw = c.parse(read(path, 65536), 65536)
    c.keys(raw, 'version observed_at rate_limit usage limit_history')
    c.need(type(raw['version']) is int and raw['version'] == 1 and c.number(raw['observed_at']))
    rate, usage = raw['rate_limit'], raw['usage']
    c.keys(rate, 'used_percent window_minutes resets_at ordinary_usage_allowed has_credits credits_unlimited credits_balance reset_credits_available')
    c.keys(usage, 'lifetime_tokens peak_daily_tokens longest_running_turn_sec current_streak_days longest_streak_days daily')
    item = dict(
        used_percent=rate['used_percent'],
        window_minutes=rate['window_minutes'],
        resets_at=rate['resets_at'],
        ordinary_usage_allowed=rate['ordinary_usage_allowed'],
        has_credits=rate['has_credits'],
        credits_unlimited=rate['credits_unlimited'],
        credits_balance=rate['credits_balance'],
        reset_credits_available=rate['reset_credits_available'],
        lifetime_tokens=usage['lifetime_tokens'],
        peak_daily_tokens=usage['peak_daily_tokens'],
        longest_running_turn_sec=usage['longest_running_turn_sec'],
        current_streak_days=usage['current_streak_days'],
        longest_streak_days=usage['longest_streak_days'],
        daily=usage['daily'],
        limit_history=raw['limit_history'],
    )
    item.update(_routing_summary(int(time.time())))
    c.row('codex', item)
    return [item], raw['observed_at']


class NotConfigured(ValueError):
    pass


def herdr(path, profile, now):
    raw = c.parse(read(path, 8192), 8192)
    c.keys(raw, 'version observed_at profiles agents')
    c.need(type(raw['version']) is int and raw['version'] == 1 and c.number(raw['observed_at'])
           and 0 <= now - raw['observed_at'] <= 90 and type(raw['agents']) is list and len(raw['agents']) <= 4)
    c.need(type(raw['profiles']) is list and 1 <= len(raw['profiles']) <= 2
           and all(type(p) is str and p in c.PROFILES for p in raw['profiles'])
           and len(set(raw['profiles'])) == len(raw['profiles']))
    for item in raw['agents']:
        c.row('herdr', item)
    c.need({r['agent'].split('-')[0] for r in raw['agents']} == set(raw['profiles']))
    if profile not in raw['profiles']:
        raise NotConfigured('profile_not_configured')
    c.need(len({r['agent'] for r in raw['agents']}) == len(raw['agents']))
    return [r for r in raw['agents'] if r['agent'].startswith(profile + '-')], raw['observed_at']
