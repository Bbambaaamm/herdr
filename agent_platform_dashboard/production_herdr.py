"""Separate one-shot status bridge; only the fixed Herdr agent-list command."""
import os
from pathlib import PurePosixPath
import stat
import sys
import time

from . import production_contract as c
from .production_export import path
from .production_io import directory, publication, publish, read, regular
from .production_sources import SAFE_ENV, command


def sanitize(data, now, bindings):
    raw = c.parse(data, 65536)
    c.keys(raw, 'id result')
    c.need(raw['id'] == 'cli:agent:list')
    c.keys(raw['result'], 'agents type')
    c.need(raw['result']['type'] == 'agent_list')
    agents = raw['result']['agents']
    c.need(type(agents) is list and len(agents) <= 64)
    c.need(type(bindings) is dict and 1 <= len(bindings) <= 4)
    for name, binding in bindings.items():
        c.keys(binding, 'profile pane_id')
        c.need(binding['profile'] in c.PROFILES and name in (binding['profile'] + '-hermes', binding['profile'] + '-codex')
               and type(binding['pane_id']) is str and 0 < len(binding['pane_id']) <= 64)
    rows = []
    for agent in agents:
        # Raw Herdr envelope can contain cwd/title. Drop those before publishing.
        c.need(type(agent) is dict and type(agent.get('name')) in (str, type(None)))
        if agent['name'] not in bindings:
            continue
        c.need(agent.get('pane_id') == bindings[agent['name']]['pane_id'])
        item = dict(agent=agent['name'], status=agent.get('agent_status'))
        c.row('herdr', item)
        rows.append(item)
    c.need(len(rows) == len({r['agent'] for r in rows}) == len(bindings))
    return dict(version=1, observed_at=now, profiles=sorted({b['profile'] for b in bindings.values()}), agents=rows)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        c.need(len(args) == 2 and args[0] == '--config' and os.geteuid() != 0)
        config = c.parse(read(args[1], 4096, owner=0), 4096)
        c.keys(config, 'binary socket output bindings')
        for value in (config[k] for k in ('binary', 'socket', 'output')):
            path(value)
        with regular(config['binary']) as (_, info):
            c.need(info.st_uid == 0)
        socket_path = PurePosixPath(config['socket'])
        with directory(str(socket_path.parent)) as parent:
            c.need(stat.S_ISSOCK(os.stat(socket_path.name, dir_fd=parent, follow_symlinks=False).st_mode))
        environment = dict(SAFE_ENV, HERDR_ENV='1', HERDR_SOCKET_PATH=config['socket'])
        with publication(config['output']) as target:
            result = sanitize(command([config['binary'], 'agent', 'list'], env=environment), int(time.time()), config['bindings'])
            import json
            publish(target, json.dumps(result, sort_keys=True, separators=(',', ':')).encode())
        return 0
    except Exception:
        print('herdr_status_unavailable', file=sys.stderr)
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
