"""Bounded v2 transaction documents; validation never authorizes replay."""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from herdr.release import ReleaseError, canonical_json
from agent_platform_dashboard.production_io import regular

FILE_MAX = 131072
MARKER_MAX = 4096
FILE_COUNT = 17
AUTHORITY_MAX = 256 * 1024
PATH_MAX = 1024
# Sixteen ordinary files plus the marker, independently base64 encoded.
BASE64_MAX = 16 * (4 * ((FILE_MAX + 2) // 3)) + 4 * ((MARKER_MAX + 2) // 3)
# JSON escapes can use six bytes per path character; metadata and envelope
# budgets are explicit, independently enforced by serialized document limits.
ENVELOPE_MAX = FILE_COUNT * (6 * PATH_MAX + 256) + 64 * 1024
BACKUP_MAX = BASE64_MAX + AUTHORITY_MAX + ENVELOPE_MAX
JOURNAL_MAX = BACKUP_MAX + 8192
EVIDENCE_MAX = 512 * 1024
# Retained backup/journal plus atomic siblings, evidence and fs block slack.
RESERVE_BYTES = 2 * (BACKUP_MAX + JOURNAL_MAX) + EVIDENCE_MAX + 65536
ROOT_UID = ROOT_GID = 0
KEYS = {'version', 'previous', 'systemd_authority', 'baseline_health',
        'services', 'direct_health', 'public_health', 'public_root', 'files'}
HEX64 = re.compile(r'[0-9a-f]{64}')


def need(ok, reason):
    if not ok:
        raise ReleaseError('transaction_' + reason)


def stamp(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def aggregate_ancestors(path):
    for parent in Path(path).parents:
        s = parent.lstat()
        need(stat.S_ISDIR(s.st_mode) and s.st_uid == ROOT_UID
             and not s.st_mode & 0o022, 'aggregate_ancestor')


def bounded_read(path, maximum, *, aggregate=False):
    """No-follow ancestor walk, bounded bytes, stable FD AND named identity."""
    if aggregate:
        aggregate_ancestors(path)
    with regular(str(path), private=aggregate) as (fd, before):
        need(before.st_nlink == 1 and 0 <= before.st_size <= maximum,
             'file_size_or_links')
        if aggregate:
            need(before.st_uid == ROOT_UID and before.st_gid == ROOT_GID
                 and stat.S_IMODE(before.st_mode) == 0o600, 'aggregate_authority')
        data = bytearray()
        while len(data) <= before.st_size:
            chunk = os.read(fd, min(65536, before.st_size + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        need(len(data) == before.st_size and stamp(os.fstat(fd)) == stamp(before),
             'file_changed')
        # Re-open through the no-follow ancestor walk, rather than stat through
        # a potentially substituted parent symlink.
        with regular(str(path), private=aggregate) as (_, named):
            need(stamp(named) == stamp(before), 'named_file_changed')
        if aggregate:
            aggregate_ancestors(path)
        return bytes(data), stat.S_IMODE(before.st_mode), before.st_uid, before.st_gid


def decode(data, maximum):
    need(type(data) is bytes and 0 < len(data) <= maximum, 'document_size')
    depth = punctuation = 0
    quoted = escaped = False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (123,91):
            depth += 1
            punctuation += 1
            need(depth <= 64, 'json_depth')
        elif byte in (125,93):
            depth -= 1
        elif byte in (44,58):
            punctuation += 1
        need(punctuation <= 65536, 'json_items')
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'duplicate_json_key')
            value[key] = item
        return value
    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda _: need(False, 'json_constant'))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ReleaseError('transaction_invalid_json') from exc


def authority_shape(authority, units):
    """Closed shape of captured v1 authority; never interprets commands."""
    from deploy.herdr.cutover.systemd_authority import COMMANDS
    def path(value):
        need(type(value) is str and len(value) <= PATH_MAX and value.startswith('/')
             and str(Path(value)) == value and '..' not in Path(value).parts, 'authority_path')
    def facts(row, root=False):
        need(type(row) is dict and set(row) in ({'uid','gid','mode','sha256'}, {'uid','gid','mode','link'}),
             'authority_facts')
        need(all(type(row[k]) is int and 0 <= row[k] <= 2**32-1 for k in ('uid','gid'))
             and row['uid'] in (ROOT_UID,1001), 'authority_owner')
        if root:
            need(row['uid'] == ROOT_UID, 'authority_root_owner')
        need(type(row['mode']) is int and 0 <= row['mode'] <= 0o777, 'authority_mode')
        if 'link' in row:
            path(row['link'])
        else:
            need(not row['mode'] & 0o022 and type(row['sha256']) is str
                 and HEX64.fullmatch(row['sha256']), 'authority_digest')
    facts(authority['host_policy'], root=True)
    for row in authority['units'].values():
        need(type(row) is dict and set(row) == set(COMMANDS) | {
            'WorkingDirectory','User','Group','Environment','fragment','dropins'}, 'unit_shape')
        facts(row['fragment'], root=True)
        need('link' not in row['fragment'], 'unit_fragment_link')
        for key in ('WorkingDirectory','User','Group'):
            need(type(row[key]) is str and len(row[key]) <= PATH_MAX, 'unit_property')
        for key in (*COMMANDS, 'Environment'):
            need(type(row[key]) is list and len(row[key]) <= 128, 'unit_collection')
            if key == 'Environment':
                need(all(type(v) is str and len(v) <= 4096 for v in row[key]), 'unit_environment')
            else:
                for command in row[key]:
                    need(type(command) is list and 0 < len(command) <= 128
                         and all(type(v) is str and len(v) <= 8192 for v in command), 'unit_command')
                    path(command[0])
        need(type(row['dropins']) is dict and len(row['dropins']) <= 3, 'unit_dropins')
        for name, value in row['dropins'].items():
            path(name)
            facts(value, root=True)
    expected = {'herdr','hermes','majak','quantlab','agent-codex-usage-export',
                'hermes-offsite-prepare','hermes-offsite-sync'}
    need({Path(p).name for p in authority['external_runtimes']} == expected, 'external_entrypoints')
    for name, value in authority['external_runtimes'].items():
        path(name)
        facts(value)
    dependencies = authority['dependencies']
    if authority['mode'] == 'standard':
        need(dependencies is None, 'standard_dependencies')
    else:
        need(type(dependencies) is dict and set(dependencies) == {'files','trees'}
             and type(dependencies['files']) is dict and 0 < len(dependencies['files']) <= 64
             and type(dependencies['trees']) is dict and len(dependencies['trees']) <= 4,
             'capacity_dependencies')
        for name, value in dependencies['files'].items():
            path(name)
            facts(value)
        for name, value in dependencies['trees'].items():
            path(name)
            need(type(value) is dict and set(value) == {'entries','sha256'}
                 and type(value['entries']) is int and 0 < value['entries'] <= 1024
                 and type(value['sha256']) is str and HEX64.fullmatch(value['sha256']), 'dependency_tree')


class Contract:
    def __init__(self, api):
        self.api = api
        paths = [api[k] for k in ('PUBLIC_STATE', 'BRIDGE', 'SNAPSHOT', 'NGINX_ROUTE')]
        paths += [api['CONSUMER_DIR'] / (name + '.yaml') for name in api['CONSUMERS']]
        paths += [api['UNIT_DIR'] / name for name in api['UNITS']]
        paths += [api['UNIT_DIR'] / 'agent-stack-watchdog.service.d/126-capacity-repair.conf',
                  api['watchdog_fence_path']()]
        need(len(paths) == FILE_COUNT and len(set(paths)) == FILE_COUNT, 'capture_set')
        self.limits = {str(p): MARKER_MAX if p == api['PUBLIC_STATE'] else FILE_MAX for p in paths}
        need(all(len(p) <= PATH_MAX and Path(p).is_absolute() for p in self.limits), 'capture_paths')

    def validate(self, document, *, journal=False):
        need(type(document) is dict and set(document) == KEYS | ({'authority_backup'} if journal else set()),
             'document_type')
        need(type(document['version']) is int and document['version'] == 2, 'version')
        previous = document['previous']
        need(type(previous) is str and len(previous) <= PATH_MAX
             and str(Path(previous)) == previous and '..' not in Path(previous).parts
             and (Path(previous) == self.api['LEGACY'] or Path(previous).parent == self.api['RELEASES']),
             'previous_path')
        need(type(document['baseline_health']) is str
             and document['baseline_health'] in ('healthy', 'degraded'), 'baseline_health')
        need(type(document['services']) is dict and set(document['services']) == set(self.api['UNITS'])
             and all(type(v) is str and v in ('active', 'inactive', 'failed', 'activating', 'deactivating')
                     for v in document['services'].values()), 'services')
        for key in ('direct_health', 'public_health', 'public_root'):
            value = document[key]
            need(value is None or type(value) is str and len(value) <= 16, 'health_value')
        authority = document['systemd_authority']
        need(type(authority) is dict and type(authority.get('mode')) is str
             and authority.get('mode') in ('standard', 'capacity_rc6')
             and len(canonical_json(authority)) <= AUTHORITY_MAX, 'authority_size_or_type')
        need(set(authority) == {'version', 'mode', 'units', 'dependencies', 'host_policy', 'external_runtimes'}
             and type(authority['version']) is int and authority['version'] == 1
             and type(authority['units']) is dict and set(authority['units']) == set(self.api['UNITS'])
             and type(authority['host_policy']) is dict
             and (authority['dependencies'] is None or type(authority['dependencies']) is dict)
             and type(authority['external_runtimes']) is dict
             and len(authority['external_runtimes']) == 7, 'authority_schema')
        authority_shape(authority, self.api['UNITS'])
        need(type(document['files']) is dict and set(document['files']) == set(self.limits), 'files_set')
        restored = {}
        for name, value in document['files'].items():
            fence = str(self.api['watchdog_fence_path']())
            dropin = str(self.api['UNIT_DIR'] / 'agent-stack-watchdog.service.d/126-capacity-repair.conf')
            required = ({str(self.api['UNIT_DIR']/unit) for unit in self.api['UNITS']}
                        | {str(self.api['NGINX_ROUTE'])})
            if Path(previous) != self.api['LEGACY']:
                required |= {str(self.api['PUBLIC_STATE'])} | {
                    str(self.api['CONSUMER_DIR']/(p+'.yaml')) for p in self.api['CONSUMERS']}
            need(name != fence or value is None, 'initial_fence_present')
            need(name != dropin or (value is not None) == (authority['mode']=='capacity_rc6'),
                 'override_presence')
            if value is None:
                need(name not in required, 'required_snapshot_missing')
                restored[Path(name)] = None
                continue
            need(type(value) is list and len(value) == 4, 'file_record')
            encoded, mode, uid, gid = value
            need(type(encoded) is str and len(encoded) <= 4 * ((self.limits[name]+2)//3), 'base64_size')
            need(type(mode) is int and 0 <= mode <= 0o777 and not mode & 0o022
                 and all(type(v) is int and 0 <= v <= 2**32-1 for v in (uid, gid)), 'file_metadata')
            telemetry = name in (str(self.api['BRIDGE']), str(self.api['SNAPSHOT']))
            need(uid == (1001 if telemetry else ROOT_UID), 'snapshot_owner')
            try:
                raw = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ReleaseError('transaction_invalid_base64') from exc
            need(len(raw) <= self.limits[name] and base64.b64encode(raw).decode('ascii') == encoded,
                 'noncanonical_or_oversize_base64')
            restored[Path(name)] = (raw, mode, uid, gid)
        if journal:
            ref = document['authority_backup']
            need(type(ref) is dict and set(ref) == {'path', 'sha256'}
                 and type(ref['path']) is str and len(ref['path']) <= PATH_MAX
                 and Path(ref['path']).parent == self.api['STATE_DIR']
                 and re.fullmatch(r'[0-9]+-baseline-authority\.json', Path(ref['path']).name)
                 and type(ref['sha256']) is str and HEX64.fullmatch(ref['sha256']), 'backup_reference')
        need(len(canonical_json(document)) <= (JOURNAL_MAX if journal else BACKUP_MAX), 'document_size')
        return restored

    def serialize(self, document, *, journal=False):
        try:
            self.validate(document, journal=journal)
            data = canonical_json(document)
        except (TypeError, RecursionError, OverflowError) as exc:
            raise ReleaseError('transaction_invalid_document') from exc
        # Exercise the exact reader's JSON and restore validation before write.
        self.validate(decode(data, JOURNAL_MAX if journal else BACKUP_MAX), journal=journal)
        return data

    def read(self, path, *, journal=False, expected_sha256=None):
        data = bounded_read(path, JOURNAL_MAX if journal else BACKUP_MAX, aggregate=True)[0]
        if expected_sha256 is not None:
            need(hashlib.sha256(data).hexdigest() == expected_sha256, 'hash_mismatch')
        document = decode(data, JOURNAL_MAX if journal else BACKUP_MAX)
        self.validate(document, journal=journal)
        if journal:
            ref = document['authority_backup']
            backup = self.read(Path(ref['path']), expected_sha256=ref['sha256'])
            need({k: v for k, v in document.items() if k != 'authority_backup'} == backup,
                 'journal_backup_mismatch')
        return document

    def plan(self, previous, report, snapshots, units, backup):
        captured = {**snapshots, **units}
        need(set(map(str, captured)) == set(self.limits), 'files_set')
        for p, value in captured.items():
            need(value is None or type(value) is tuple and len(value) == 4
                 and type(value[0]) is bytes and len(value[0]) <= self.limits[str(p)],
                 'raw_snapshot_size_or_type')
        files = {str(p): None if v is None else [base64.b64encode(v[0]).decode('ascii'), *v[1:]]
                 for p, v in captured.items()}
        document = dict(version=2, previous=str(previous), systemd_authority=report['systemd_authority'],
                        baseline_health=report.get('baseline_health', 'healthy'), services=report['services'],
                        direct_health=report['direct_health'], public_health=report['public_health'],
                        public_root=report.get('public_root'), files=files)
        raw = self.serialize(document)
        ref = dict(path=str(backup), sha256=hashlib.sha256(raw).hexdigest())
        journal = {**document, 'authority_backup': ref}
        journal_raw = self.serialize(journal, journal=True)
        return document, raw, journal, journal_raw


def capacity(api, archive, candidate_allocation=256*1024**2):
    """Same reserve for planning/apply; observe only, never run maintenance."""
    size = archive.lstat().st_size
    need(0 < size <= 64*1024**2, 'archive_size')
    need(type(candidate_allocation) is int and 0 <= candidate_allocation <= 320*1024**2,
         'candidate_allocation')
    backups = Path('/home/agentops/backups/hermes')
    candidates = []
    for p in backups.glob('hermes-backup-auto-*.zip'):
        need(len(candidates) < 4096, 'backup_inventory_limit')
        candidates.append(p)
    newest = max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None
    peak = max(512*1024**2, newest.stat().st_size if newest else 0)*3 + 1024**3
    extra = 2*size + 3*candidate_allocation + RESERVE_BYTES
    required = max(12*1024**3 + extra, 10*1024**3 + 128*1024**2 + peak + extra)
    observations = []
    for path in (api['STATE_DIR'], api['INCOMING_DIR'], api['RELEASES'], Path('/tmp'), backups):
        while not path.exists():
            path = path.parent
        v = os.statvfs(path)
        available = v.f_bavail*v.f_frsize
        need(available >= required and v.f_favail >= 32768, 'capacity_insufficient')
        observations.append(dict(available_bytes=available, free_inodes=v.f_favail))
    return dict(required_bytes=required, transaction_reserve_bytes=RESERVE_BYTES,
                backup_preparation_peak_bytes=peak, observations=observations)
