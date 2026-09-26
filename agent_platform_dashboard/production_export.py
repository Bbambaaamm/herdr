"""Explicit one-shot exporter CLI. No import-time work, retries or serving loop."""
import os
from pathlib import PurePosixPath
import sys
import time

from . import production_contract as c
from . import production_sources as sources
from .production_io import publication, publish, read


def path(value):
    c.need(type(value) is str and value.startswith('/') and len(value) <= 1024
           and str(PurePosixPath(value)) == value and '..' not in PurePosixPath(value).parts)
    return value


def configuration(raw):
    c.keys(raw, 'version output profiles herdr')
    c.need(type(raw['version']) is int and raw['version'] == 1)
    path(raw['output'])
    c.need(PurePosixPath(raw['output']).name == 'snapshot.json')
    if raw['herdr'] is not None:
        path(raw['herdr'])
    c.keys(raw['profiles'], 'majak quantlab')
    all_paths = []
    for profile, settings in raw['profiles'].items():
        c.need(type(settings) is dict)
        names = set(settings)
        legacy = {'router', 'kanban', 'git', 'tests'}
        extended = legacy | {'search'}
        c.need(names in (legacy, extended))
        if names == legacy:
            settings['search'] = None
        for kind, value in settings.items():
            if value is None:
                continue
            if kind == 'kanban':
                c.keys(value, 'path board_id source_epoch')
                c.need(c.hex_id(value['board_id']) and c.hex_id(value['source_epoch']))
                value = value['path']
            path(value)
            all_paths.append(value)
    c.need(len(all_paths) == len(set(all_paths)))  # no accidental cross-profile aliases
    c.need(raw['output'] not in all_paths and raw['output'] != raw['herdr'])
    return raw


def collect(config, now):
    configuration(config)
    c.need(c.number(now))
    snapshot = c.unavailable(now)
    adapters = {'router': sources.router, 'search': sources.search,
                'kanban': sources.kanban, 'git': sources.git,
                'tests': sources.tests, 'queue': sources.queue, 'codex': sources.codex}
    for source in snapshot['sources']:
        profile, kind = source['profile'], source['kind']
        if kind == 'herdr':
            setting = config['herdr']
        elif kind == 'queue':
            setting = sources.QUEUE_PATH
        elif kind == 'codex':
            setting = sources.CODEX_USAGE_PATH
        else:
            setting = config['profiles'][profile][kind]
        if setting is None:
            continue
        try:
            if kind == 'herdr':
                rows, data_at = sources.herdr(setting, profile, now)
            else:
                rows, data_at = adapters[kind](setting, profile)
            c.need(data_at is None or data_at <= now)
            if kind == 'codex' and (data_at is None or not 0 <= now - data_at <= 900):
                source.update(rows=[], data_at=None, status='unavailable', reason='stale')
                continue
            source.update(rows=rows, data_at=data_at, status='available', reason='ok')
            if kind in ('herdr', 'queue', 'codex'):
                c.need(data_at is not None)
                source['observed_at'] = data_at
            if kind == 'tests':
                c.need(data_at is not None and 0 <= now - data_at <= 86400)
            if kind == 'kanban':
                source.update(board_id=setting['board_id'], source_epoch=setting['source_epoch'])
            c.validate(snapshot)
        except sources.NotConfigured:
            source.update(rows=[], data_at=None, status='unavailable', reason='not_configured', board_id=None, source_epoch=None)
        except Exception:
            source.update(rows=[], data_at=None, status='unavailable', reason='source_failed', board_id=None, source_epoch=None)
    return snapshot


def load_config(filename):
    return configuration(c.parse(read(filename, 16384, owner=0), 16384))


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        c.need(len(args) == 2 and args[0] == '--config' and os.geteuid() != 0)
        config = load_config(args[1])
        with publication(config['output']) as target:
            publish(target, c.encode(collect(config, int(time.time()))))
        return 0
    except Exception:
        print('export_unavailable', file=sys.stderr)
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
