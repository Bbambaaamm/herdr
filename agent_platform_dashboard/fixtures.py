"""Bounded JSON byte adapter. No file paths, SQLite, network or live source helpers."""
from dataclasses import fields
import json

from . import contracts as c


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        c.need(key not in result, 'duplicate_key')
        result[key] = value
    return result


def _reject_constant(value):
    raise c.Invalid('invalid_json')


def _keys(raw, record):
    c.need(type(raw) is dict and set(raw) == {f.name for f in fields(record)}, 'unknown_fields')


def decode_snapshot(data):
    c.need(type(data) is bytes and len(data) <= 65536, 'fixture_size')
    try:
        raw = json.loads(data, object_pairs_hook=_pairs, parse_constant=_reject_constant)
        _keys(raw, c.Snapshot)
        c.need(type(raw['rows']) is list and len(raw['rows']) <= 200, 'row_limit')
        rows = []
        kinds = {v: k for k, v in c.KINDS.items()}
        for row in raw['rows']:
            c.need(type(row) is dict and type(row.get('kind')) is str and row['kind'] in kinds)
            record = kinds[row.pop('kind')]
            _keys(row, record)
            _keys(row['scope'], c.Scope)
            row['scope'] = c.Scope(**row['scope'])
            rows.append(record(**row))
        return c.Snapshot(raw['version'], raw['observed_at'], raw['source_version'], tuple(rows))
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        raise c.Invalid('invalid_fixture') from None
