"""Closed production snapshot schema; no I/O or fixture fallback."""
import hashlib
import json
import math

PROFILES = ('majak', 'quantlab')
KINDS = ('herdr', 'kanban', 'router', 'search', 'git', 'tests', 'queue', 'codex',
         'admission', 'release', 'swarm')
SOURCE_PAIRS = tuple(
    (profile, kind)
    for profile in PROFILES
    for kind in KINDS
    if (kind != 'codex' or profile == 'majak')
    and (kind != 'admission' or profile == 'quantlab')
    and (kind != 'release' or profile == 'quantlab')
    and (kind != 'swarm' or profile == 'quantlab')
)
MAX_BYTES = 131072


def need(ok):
    if not ok:
        raise ValueError('invalid_metadata')


def keys(value, names):
    need(type(value) is dict and set(value) == set(names.split()))


def number(value):
    return type(value) is int and 0 <= value < 2**53


def timestamp(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value < 2**53


def hex_id(value, lengths=(64,)):
    return type(value) is str and len(value) in lengths and all(c in '0123456789abcdef' for c in value)


def identifier(value, limit=128):
    return (value is None or type(value) is str and 0 < len(value) <= limit
            and all(c.isascii() and (c.isalnum() or c in '-_./:') for c in value))


def display_text(value, limit=160):
    return (value is None or type(value) is str and 0 < len(value) <= limit
            and all(ord(c) >= 32 and ord(c) != 127 for c in value))


def identity(profile, value):
    need(profile in PROFILES and type(value) is str and 0 < len(value) <= 256)
    return hashlib.sha256((profile + '\0' + value).encode()).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        need(key not in out)
        out[key] = value
    return out


def reject(_):
    raise ValueError('invalid_metadata')


def parse(data, limit=MAX_BYTES):
    need(type(data) is bytes and len(data) <= limit)
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=reject)
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError('invalid_metadata') from None


def row(kind, value):
    fields = {'herdr': 'agent status', 'kanban': 'task_id run_id status',
              'router': ('task_id actual_model provider requests input_tokens output_tokens '
                         'cost_microusd fallback_count successful_requests duration_ms last_used_at'),
              'search': ('route_mode provider fallback_provider searches successful_searches '
                         'duration_ms max_duration_ms fallback_count cost_microusd result_count '
                         'extract_count last_used_at'),
              'git': 'commit dirty', 'tests': 'passed failed artifact_digest',
              'queue': ('task_id repo issue issue_title issue_open scheduler_state status attempts '
                        'max_attempts not_before updated_at agent kind blocker pr_number'),
              'admission': ('event reason role repo issue node_count max_depth max_fanout '
                            'child_tools_count agents_after observed_at'),
              'release': 'tag commit config_sha256 deployed_at',
              'swarm': 'version repo issue issue_state paper_only policy_profiles agents runtime_status runtime_agents tasks edges',
              'codex': ('used_percent window_minutes resets_at ordinary_usage_allowed has_credits '
                        'credits_unlimited credits_balance reset_credits_available lifetime_tokens '
                        'peak_daily_tokens longest_running_turn_sec current_streak_days '
                        'longest_streak_days daily limit_history routing_status routing_policy_version '
                        'routing_observed_at routing_soft_limit_pct routing_hard_limit_pct routing_decisions '
                        'routing_free routing_sol routing_astra routing_astra_escalations routing_premium_denied '
                        'last_route_at last_route_tier last_route_model last_route_reason')}
    if kind == 'queue':
        legacy = set(fields[kind].replace(' repo', '').split())
        current = set(fields[kind].split())
        need(type(value) is dict and set(value) in (legacy, current))
    elif kind == 'swarm':
        legacy = set('version repo issue issue_state paper_only policy_profiles agents tasks edges'.split())
        current = set(fields[kind].split())
        need(type(value) is dict and set(value) in (legacy, current))
    else:
        keys(value, fields[kind])
    if kind == 'herdr':
        need(value['agent'] in ('majak-hermes', 'majak-codex', 'quantlab-hermes', 'quantlab-codex'))
        need(value['status'] in ('idle', 'working', 'blocked', 'done', 'unknown'))
    elif kind == 'kanban':
        need(hex_id(value['task_id']))
        need(value['run_id'] is None or number(value['run_id']))
        need(value['status'] in ('todo', 'triage', 'ready', 'running', 'blocked', 'done', 'cancelled', 'unknown'))
    elif kind == 'router':
        need(value['task_id'] is None or hex_id(value['task_id']))
        need(type(value['actual_model']) is str and identifier(value['actual_model'])
             and type(value['provider']) is str and identifier(value['provider'], 64))
        need(number(value['requests']))
        need(timestamp(value['last_used_at']))
        need(all(v is None or number(v) for k, v in value.items()
                 if k not in ('task_id', 'actual_model', 'provider', 'requests', 'last_used_at')))
    elif kind == 'search':
        need(value['route_mode'] in ('fast', 'deep', 'browser'))
        need(type(value['provider']) is str and identifier(value['provider'])
             and (value['fallback_provider'] is None or identifier(value['fallback_provider'])))
        need(number(value['searches']) and number(value['successful_searches'])
             and value['successful_searches'] <= value['searches'])
        need(number(value['duration_ms']) and number(value['max_duration_ms'])
             and value['max_duration_ms'] <= value['duration_ms'])
        need(number(value['fallback_count']) and value['fallback_count'] <= value['searches'])
        need(value['cost_microusd'] is None or number(value['cost_microusd']))
        need(number(value['result_count']) and number(value['extract_count']))
        need(timestamp(value['last_used_at']))
    elif kind == 'git':
        need(hex_id(value['commit'], (40, 64)) and type(value['dirty']) is bool)
    elif kind == 'queue':
        need(type(value['task_id']) is str and identifier(value['task_id'])
             and (value['issue'] is None or number(value['issue'])))
        repo = value.get('repo')
        need(repo is None or identifier(repo, 160))
        expected_agent = {
            None: 'quantlab-hermes',
            'Bbambaaamm/Autonomous-Quant-Lab': 'quantlab-hermes',
            'Bbambaaamm/dotacni-majak': 'dotacni-majak-hermes',
        }.get(repo)
        need(expected_agent is not None)
        need(display_text(value['issue_title']) and type(value['issue_open']) is bool)
        need(value['scheduler_state'] is None or identifier(value['scheduler_state'], 64))
        need(value['status'] in ('pending', 'running', 'blocked', 'done', 'failed'))
        need(number(value['attempts']) and number(value['max_attempts'])
             and (value['not_before'] is None or number(value['not_before'])))
        need(number(value['updated_at']) and value['agent'] == expected_agent)
        need(type(value['kind']) is str and identifier(value['kind'], 64))
        need(value['blocker'] is None or type(value['blocker']) is str and identifier(value['blocker']))
        need(value['pr_number'] is None or number(value['pr_number']))
    elif kind == 'admission':
        need(value['event'] in ('allow', 'deny'))
        need(value['reason'] is None or identifier(value['reason'], 64))
        need(identifier(value['role'], 32) and identifier(value['repo'], 128)
             and identifier(value['issue'], 64))
        for name in ('node_count', 'max_depth', 'max_fanout', 'child_tools_count'):
            need(number(value[name]))
        need(value['agents_after'] is None or number(value['agents_after']))
        need(number(value['observed_at']))
        if value['event'] == 'deny':
            need(value['reason'] is not None and value['agents_after'] is None)
        else:
            need(value['reason'] is None and value['agents_after'] is not None)
    elif kind == 'release':
        need(type(value['tag']) is str and identifier(value['tag'], 64)
             and value['tag'].startswith('v'))
        need(hex_id(value['commit'], (40,)) and hex_id(value['config_sha256']))
        need(number(value['deployed_at']))
    elif kind == 'swarm':
        need(value['version'] == 1 and identifier(value['repo'], 160)
             and identifier(value['issue'], 64))
        need(value['issue_state'] in ('open', 'closed', 'unknown'))
        need(type(value['paper_only']) is bool)
        if value['repo'] == 'Bbambaaamm/Autonomous-Quant-Lab':
            need(value['paper_only'] is True)
        need(type(value['policy_profiles']) is list and len(value['policy_profiles']) <= 16
             and len(set(value['policy_profiles'])) == len(value['policy_profiles'])
             and all(identifier(item, 64) for item in value['policy_profiles']))
        need(type(value['tasks']) is list and len(value['tasks']) <= 100)
        task_ids = set()
        tasks_by_id = {}
        for task in value['tasks']:
            legacy_task = set('task_id parent_task_id parent_agent_id agent_id state role model fallback_model attempt max_attempts blocker fencing_token dependencies result_sha'.split())
            current_task = legacy_task | {'attempt_state', 'delivery_reconcile_count'}
            need(type(task) is dict and set(task) in (legacy_task, current_task))
            need(identifier(task['task_id'], 256) and task['task_id'] not in task_ids)
            task_ids.add(task['task_id'])
            tasks_by_id[task['task_id']] = task
            need(task['parent_task_id'] is None or identifier(task['parent_task_id'], 256))
            need(task['parent_agent_id'] is None or identifier(task['parent_agent_id'], 256))
            need(task['agent_id'] is None or identifier(task['agent_id'], 256))
            need(task['state'] in ('pending', 'ready', 'running', 'blocked', 'review', 'done', 'failed', 'cancelled'))
            need(identifier(task['role'], 64))
            need(task['model'] is None or identifier(task['model'], 128))
            need(task['fallback_model'] is None or identifier(task['fallback_model'], 128))
            need(number(task['attempt']) and number(task['max_attempts'])
                 and task['attempt'] <= task['max_attempts'])
            attempt_state = task.get('attempt_state')
            need(attempt_state is None or attempt_state in (
                'dispatching', 'accepted', 'working', 'delivery_uncertain', 'verifying',
                'completed', 'done', 'blocked', 'failed', 'retry_scheduled'))
            need(number(task.get('delivery_reconcile_count', 0)))
            need(task['blocker'] is None or identifier(task['blocker'], 128))
            need(number(task['fencing_token']))
            need(type(task['dependencies']) is list and len(task['dependencies']) <= 64
                 and len(set(task['dependencies'])) == len(task['dependencies'])
                 and all(identifier(dep, 256) for dep in task['dependencies']))
            need(task['result_sha'] is None or hex_id(task['result_sha']))

        need(type(value['agents']) is list and len(value['agents']) <= 100)
        agent_ids = set()
        agent_tasks = set()
        for agent in value['agents']:
            keys(agent, 'agent_id task_id state parent_task_id parent_agent_id fencing_token')
            need(identifier(agent['agent_id'], 256) and agent['agent_id'] not in agent_ids)
            need(identifier(agent['task_id'], 256) and agent['task_id'] not in agent_tasks)
            agent_ids.add(agent['agent_id'])
            agent_tasks.add(agent['task_id'])
            need(agent['state'] == 'running')
            need(agent['parent_task_id'] is None or identifier(agent['parent_task_id'], 256))
            need(agent['parent_agent_id'] is None or identifier(agent['parent_agent_id'], 256))
            need(number(agent['fencing_token']))
            task = tasks_by_id.get(agent['task_id'])
            need(task is not None and task['state'] == 'running'
                 and task['agent_id'] == agent['agent_id']
                 and task['parent_task_id'] == agent['parent_task_id']
                 and task['parent_agent_id'] == agent['parent_agent_id']
                 and task['fencing_token'] == agent['fencing_token'])
        expected_agent_tasks = {
            task['task_id'] for task in value['tasks']
            if task['state'] == 'running' and task['agent_id'] is not None
        }
        need(agent_tasks == expected_agent_tasks)

        runtime_status = value.get('runtime_status', 'unavailable')
        runtime_agents = value.get('runtime_agents', [])
        need(runtime_status in ('available', 'unavailable', 'not_applicable'))
        need(type(runtime_agents) is list and len(runtime_agents) <= 16)
        runtime_ids = set()
        for runtime_agent in runtime_agents:
            keys(runtime_agent, 'agent_id status task_id')
            need(type(runtime_agent['agent_id']) is str
                 and identifier(runtime_agent['agent_id'], 256)
                 and runtime_agent['agent_id'] not in runtime_ids)
            runtime_ids.add(runtime_agent['agent_id'])
            need(runtime_agent['status'] in ('idle', 'working', 'blocked', 'done', 'unknown'))
            matches = [task for task in value['tasks']
                       if task['agent_id'] == runtime_agent['agent_id']
                       and task['state'] in ('pending', 'ready', 'running', 'blocked', 'review')]
            need(runtime_agent['task_id'] is None or
                 type(runtime_agent['task_id']) is str and len(matches) == 1
                 and matches[0]['task_id'] == runtime_agent['task_id'])
        if runtime_status != 'available':
            need(runtime_agents == [])

        need(type(value['edges']) is list and len(value['edges']) <= 200)
        edges = set()
        for edge in value['edges']:
            keys(edge, 'from_task to_task kind')
            need(identifier(edge['from_task'], 256) and identifier(edge['to_task'], 256)
                 and edge['kind'] in ('parent', 'dependency'))
            need(edge['from_task'] in task_ids and edge['to_task'] in task_ids)
            key = (edge['from_task'], edge['to_task'], edge['kind'])
            need(key not in edges)
            edges.add(key)
    elif kind == 'codex':
        need(number(value['used_percent']) and value['used_percent'] <= 100)
        need(value['window_minutes'] is None or number(value['window_minutes']))
        need(value['resets_at'] is None or number(value['resets_at']))
        need(type(value['ordinary_usage_allowed']) is bool and type(value['has_credits']) is bool
             and type(value['credits_unlimited']) is bool)
        need(value['credits_balance'] is None or type(value['credits_balance']) is str
             and len(value['credits_balance']) <= 32
             and all(ch in '0123456789.-' for ch in value['credits_balance']))
        for name in ('reset_credits_available', 'lifetime_tokens', 'peak_daily_tokens',
                     'longest_running_turn_sec', 'current_streak_days', 'longest_streak_days'):
            need(value[name] is None or number(value[name]))
        need(type(value['daily']) is list and len(value['daily']) <= 45)
        previous_day = ''
        for item in value['daily']:
            keys(item, 'day tokens')
            need(type(item['day']) is str and len(item['day']) == 10
                 and item['day'][4] == '-' and item['day'][7] == '-' and number(item['tokens']))
            need(previous_day < item['day'])
            previous_day = item['day']
        need(type(value['limit_history']) is list and len(value['limit_history']) <= 288)
        previous_at = -1
        for item in value['limit_history']:
            keys(item, 'at used_percent')
            need(number(item['at']) and number(item['used_percent']) and item['used_percent'] <= 100)
            need(previous_at < item['at'])
            previous_at = item['at']
        need(value['routing_status'] in ('available', 'unavailable'))
        routing_numbers = (
            'routing_observed_at', 'routing_soft_limit_pct', 'routing_hard_limit_pct',
            'routing_decisions', 'routing_free', 'routing_sol', 'routing_astra',
            'routing_astra_escalations', 'routing_premium_denied', 'last_route_at',
        )
        if value['routing_status'] == 'available':
            need(identifier(value['routing_policy_version'], 64))
            need(all(number(value[name]) for name in routing_numbers[:-1]))
            need(value['routing_soft_limit_pct'] < value['routing_hard_limit_pct'] <= 100)
            need(value['routing_free'] + value['routing_sol'] + value['routing_astra']
                 <= value['routing_decisions'])
            need(value['routing_astra_escalations'] <= value['routing_astra'])
            need(value['last_route_at'] is None or number(value['last_route_at']))
            need(value['last_route_tier'] is None or value['last_route_tier'] in ('free', 'sol', 'astra'))
            need(identifier(value['last_route_model']) and identifier(value['last_route_reason']))
        else:
            need(value['routing_policy_version'] is None)
            need(all(value[name] is None for name in routing_numbers))
            need(value['last_route_tier'] is None and value['last_route_model'] is None
                 and value['last_route_reason'] is None)
    else:
        need(number(value['passed']) and number(value['failed']) and hex_id(value['artifact_digest']))


def validate(value):
    keys(value, 'version generated_at sources observability')
    need(type(value['version']) is int and value['version'] == 1 and number(value['generated_at']))
    need(type(value['sources']) is list and len(value['sources']) == len(SOURCE_PAIRS))
    seen = set()
    for source in value['sources']:
        keys(source, 'profile kind observed_at data_at status reason rows board_id source_epoch')
        profile, kind = source['profile'], source['kind']
        need(type(profile) is str and profile in PROFILES and type(kind) is str and kind in KINDS)
        need((profile, kind) in SOURCE_PAIRS and (profile, kind) not in seen)
        seen.add((profile, kind))
        need(number(source['observed_at']) and source['observed_at'] <= value['generated_at'])
        need(source['data_at'] is None or number(source['data_at']))
        need(source['status'] in ('available', 'unavailable'))
        need(source['reason'] in ('ok', 'not_configured', 'source_failed', 'stale'))
        need(type(source['rows']) is list and len(source['rows']) <= 50)
        need((source['status'] == 'available') == (source['reason'] == 'ok'))
        if source['status'] == 'unavailable':
            need(source['rows'] == [] and source['data_at'] is None)
        for name in ('board_id', 'source_epoch'):
            need(source[name] is None or hex_id(source[name]))
        if kind == 'kanban' and source['status'] == 'available':
            need(hex_id(source['board_id']) and hex_id(source['source_epoch']))
        if kind != 'kanban':
            need(source['board_id'] is None and source['source_epoch'] is None)
        for item in source['rows']:
            row(kind, item)
            if kind == 'herdr':
                need(item['agent'].startswith(profile + '-'))
            if kind == 'queue':
                repo = item.get('repo')
                if profile == 'quantlab':
                    need(repo in (None, 'Bbambaaamm/Autonomous-Quant-Lab'))
                else:
                    need(repo == 'Bbambaaamm/dotacni-majak')
            if kind == 'admission':
                need(profile == 'quantlab')
            if kind == 'release':
                need(profile == 'quantlab')
            if kind == 'swarm':
                need(profile == 'quantlab')
        need(len({json.dumps(r, sort_keys=True) for r in source['rows']}) == len(source['rows']))
    observability(value['observability'])
    return value


def observability(model):
    from .observability import AXES, INVENTORY
    keys(model, 'version lifecycle metrics inventory')
    need(type(model['version']) is int and model['version'] == 1)
    need(type(model['lifecycle']) is list and len(model['lifecycle']) == len(AXES)
         and [r.get('id') for r in model['lifecycle']] == list(AXES))
    need(type(model['metrics']) is list and len(model['metrics']) <= 128)
    need(type(model['inventory']) is list and len(model['inventory']) == len(INVENTORY)
         and [r.get('id') for r in model['inventory']] == list(INVENTORY))
    ids = set()
    for metric in model['lifecycle'] + model['metrics']:
        need(type(metric) is dict and set(metric) in (
            set('id value unit window source freshness source_age_seconds coverage reason'.split()),
            set('id value unit window source freshness source_age_seconds coverage reason evidence_hash'.split())))
        need(identifier(metric['id'], 80) and metric['id'] not in ids)
        ids.add(metric['id'])
        need(metric['value'] is None or type(metric['value']) in (int, bool)
             and (type(metric['value']) is bool or number(metric['value']))
             or type(metric['value']) is str and identifier(metric['value'], 80))
        need(identifier(metric['unit'], 32) and identifier(metric['window'], 32)
             and identifier(metric['source'], 80))
        need(metric['freshness'] in ('fresh', 'stale', 'unavailable', 'unknown'))
        need(metric['source_age_seconds'] is None or number(metric['source_age_seconds']))
        keys(metric['coverage'], 'covered denominator')
        need(number(metric['coverage']['covered']) and number(metric['coverage']['denominator'])
             and metric['coverage']['covered'] <= metric['coverage']['denominator'])
        need(metric['reason'] is None or identifier(metric['reason'], 64))
        if 'evidence_hash' in metric:
            need(hex_id(metric['evidence_hash'], (40, 64)))
    for row in model['inventory']:
        keys(row, 'id status reason source freshness source_age_seconds coverage')
        need(row['id'] in INVENTORY and row['status'] in ('available', 'UNKNOWN'))
        need(row['reason'] is None or identifier(row['reason'], 64))
        need(identifier(row['source'], 80))
        need(row['freshness'] in ('fresh', 'stale', 'unavailable', 'unknown'))
        need(row['source_age_seconds'] is None or number(row['source_age_seconds']))
        keys(row['coverage'], 'covered denominator')
        need(number(row['coverage']['covered']) and number(row['coverage']['denominator'])
             and row['coverage']['covered'] <= row['coverage']['denominator'])


def decode(data):
    try:
        return validate(parse(data))
    except (KeyError, TypeError, ValueError, RecursionError):
        raise ValueError('invalid_metadata') from None


def encode(value):
    data = json.dumps(validate(value), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    need(len(data) <= MAX_BYTES)
    return data


def unavailable(now):
    result = {'version': 1, 'generated_at': now, 'sources': [
        dict(profile=p, kind=k, observed_at=now, data_at=None, status='unavailable',
             reason='not_configured', rows=[], board_id=None, source_epoch=None)
        for p, k in SOURCE_PAIRS]}
    from .observability import build
    result['observability'] = build(result)
    return result


def project(value, profiles, now):
    validate(value)
    need(type(profiles) is tuple and profiles and len(set(profiles)) == len(profiles)
         and all(p in PROFILES for p in profiles) and number(now))
    result = parse(encode(value))
    result['sources'] = [source for source in result['sources'] if source['profile'] in profiles]
    # Rebuild from the authorized source subset at request time. This both
    # prevents cross-profile leakage and updates source_age/freshness instead
    # of replaying the exporter-time freshness label.
    from .observability import build
    result['observability'] = build(result, now=now, visible_profiles=profiles)
    for source in result['sources']:
        if not 0 <= now - source['observed_at'] <= 90:
            source.update(status='unavailable', reason='stale', rows=[], data_at=None)
    return result