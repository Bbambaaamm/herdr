"""One-shot descriptor custody in the existing root launch-plan authority.

Only an exact approved, protected host launcher can redeem a still-live plan.
No command is executed by root. The receiver validates every transferred inode
and its unchanged root-approved mount plan before invoking bubblewrap.
"""
from __future__ import annotations
import array
import json
import os
from pathlib import Path
import re
import socket
import struct
import time
from datetime import UTC, datetime

from .security import InvocationIdentity, canonical_json_bytes

VERSION = 'herdr-native-fd-handoff-1'
ENTRYPOINT = 'agent-stack/bin/agent-herdr-fd-launch'
SOCKET_PATH = Path('/run/herdr-launch-authority/native-fds.sock')
MAX_PENDING = 16
# Bounded pane dispatch plus descriptor redemption after the host binds a plan.
REDEMPTION_SECONDS = 15


def _close(fds):
    for fd in fds:
        os.close(fd)


class DescriptorCustody:
    def __init__(self):
        self.pending = {}

    def prune(self):
        for key, row in list(self.pending.items()):
            if time.monotonic() >= row['deadline']:
                self.pending.pop(key)
                _close(row['fds'])

    def require_capacity(self):
        from .launch_plan_issuer import require
        self.prune()
        require(len(self.pending) < MAX_PENDING, 'native descriptor custody is full')

    def stage(self, request, peer, issuer, raw, fds, deadline):
        from .launch_plan_issuer import _digest, require
        self.require_capacity()
        key = _digest(request['proposal']['plan']['identity'])
        require(key not in self.pending and time.monotonic() < deadline,
                'native descriptor custody identity or deadline changed')
        copies = []
        try:
            for fd in fds:
                duplicate = os.dup(fd)
                copies.append(duplicate)
                os.set_inheritable(duplicate, False)
            handoff = raw['private_launch']['plan_handoff']['timeout_seconds']
            grant_expiry = datetime.fromisoformat(request['grant']['expires_at'])
            grant_deadline = time.monotonic() + (grant_expiry - datetime.now(UTC)).total_seconds()
            binding_deadline = min(deadline + handoff, grant_deadline - REDEMPTION_SECONDS)
            require(time.monotonic() < binding_deadline,
                    'native descriptor grant leaves no dispatch interval')
            self.pending[key] = {'request': json.loads(canonical_json_bytes(request)),
                'peer': peer, 'issuer': issuer, 'raw': raw, 'fds': copies,
                'deadline': min(deadline + handoff + REDEMPTION_SECONDS, grant_deadline),
                'binding_deadline': binding_deadline,
                'request_deadline': deadline, 'active': False}
            return key
        except BaseException:
            _close(copies)
            raise

    def activate(self, key):
        from .launch_plan_issuer import require
        row = self.pending[key]
        require(not row['active'], 'native descriptor custody already committed')
        row['active'] = True

    def reconcile(self, key):
        # A rename can succeed before fsync/reply fails. Never discard the
        # only held descriptors of an exact visible no-replace plan.
        from . import launch_plan_issuer as authority
        from .private_mount_plan import ApprovedPrivateMountPlan
        row = self.pending[key]
        proposal = row['request']['proposal']
        try:
            plan = ApprovedPrivateMountPlan.read(authority.publication.AUTHORITY_ROOT / (key + '.json'),
                InvocationIdentity.from_dict(proposal['plan']['identity']))
            plan.authorize(proposal['plan']['descriptors'], proposal['argv'])
        except FileNotFoundError:
            self.cancel(key)
        except (OSError, ValueError, authority.SecurityError):
            # Inspection uncertainty cannot authorize transfer. Retain bounded
            # inactive custody until exact redemption inspection or expiry.
            pass
        else:
            self.activate(key)

    def cancel(self, key):
        row = self.pending.pop(key)
        _close(row['fds'])

    def redeem(self, connection):
        from . import launch_plan_issuer as authority
        authority.require(os.geteuid() == 0, 'root native descriptor authority required')
        self.prune()
        issuer, raw = authority._policy()
        peer = authority._peer(connection, issuer, raw)
        connection.settimeout(issuer['request_timeout_seconds'])
        request, incoming = authority._receive(connection, peer, minimum_fds=0)
        try:
            authority.require(not incoming and set(request) == {
                'schema_version', 'identity_sha256', 'plan_sha256'} and request['schema_version'] == VERSION
                and all(isinstance(request[k], str) and re.fullmatch('[a-f0-9]{64}', request[k])
                        for k in ('identity_sha256', 'plan_sha256')), 'closed native descriptor request required')
        finally:
            _close(incoming)
        key = request['identity_sha256']
        authority.require(key in self.pending, 'native descriptors unavailable; reconcile existing plan')
        row = self.pending[key]
        proposal = row['request']['proposal']
        authority.require((issuer, raw) == (row['issuer'], row['raw'])
                and request['plan_sha256'] == authority._digest(proposal['plan']),
                'native descriptor authority changed')
        argv = authority._proc_bytes(peer[0], 'cmdline', 32768).rstrip(b'\0').decode().split('\0')
        expected = {'schema_version': 'herdr-private-mount-plan-1',
            'authority': str(authority.publication.AUTHORITY_ROOT / (key + '.json')),
            'authority_sha256': request['plan_sha256'], 'entries': proposal['plan']['descriptors'],
            'transport': VERSION}
        def unique(pairs):
            result = {}
            for name, value in pairs:
                authority.require(name not in result, 'duplicate native launcher field')
                result[name] = value
            return result
        authority.require(len(argv) >= 7 and argv[4] == ENTRYPOINT
                and json.loads(argv[5], object_pairs_hook=unique) == expected and argv[6:] == proposal['argv'],
                'exact approved native descriptor launcher required')
        from .launch_environment import process_environment
        from .policy_launch import IDENTITY_ENV
        environment = process_environment(peer[0])
        authority.require(all(environment.get(name) == str(proposal['plan']['identity'][field])
                              for field, name in IDENTITY_ENV.items()),
                          'native descriptor launcher identity differs')
        authority.require(authority._host_peer(*row['peer'][:3], issuer, raw) == row['peer'],
                          'native descriptor owner changed')
        from .private_mount_plan import ApprovedPrivateMountPlan
        plan = ApprovedPrivateMountPlan.read(Path(expected['authority']),
                                             InvocationIdentity.from_dict(proposal['plan']['identity']))
        plan.authorize(proposal['plan']['descriptors'], proposal['argv'])
        if not row['active']:
            self.activate(key)
        authority._validate(row['request'], row['fds'], row['peer'], raw)
        authority.require(authority._policy() == (issuer, raw)
                and authority._peer(connection, issuer, raw) == peer
                and authority._host_peer(*row['peer'][:3], issuer, raw) == row['peer']
                and time.monotonic() < row['deadline'], 'native descriptor admission expired or changed')
        # Consume before the syscall: a lost reply never permits another send.
        self.pending.pop(key)
        try:
            answer = canonical_json_bytes({'schema_version': VERSION, 'identity_sha256': key,
                'plan_sha256': request['plan_sha256'], 'descriptor_count': len(row['fds'])})
            connection.settimeout(max(0.001, row['deadline'] - time.monotonic()))
            authority.require(connection.sendmsg([answer], [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                        array.array('i', row['fds']))]) == len(answer), 'native descriptor reply lost; reconcile')
        finally:
            _close(row['fds'])

    def close(self):
        for row in self.pending.values():
            _close(row['fds'])
        self.pending.clear()


def _connect(timeout):
    from . import launch_plan_issuer as authority
    authority._verify_root_owned_ancestry(SOCKET_PATH.parent)
    info = SOCKET_PATH.lstat()
    import stat
    authority.require(stat.S_ISSOCK(info.st_mode) and info.st_uid == 0, 'root native descriptor endpoint required')
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        connection.settimeout(timeout)
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        connection.connect(str(SOCKET_PATH))
        peer = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        authority.require(peer[1] == 0 and authority._stamp(SOCKET_PATH.lstat()) == authority._stamp(info),
                          'native descriptor endpoint changed')
        return connection, (*peer, 0)
    except BaseException:
        connection.close()
        raise


def receive_descriptors(envelope, argv):
    from . import launch_plan_issuer as authority
    require = authority.require
    require(isinstance(envelope, dict) and envelope.get('transport') == VERSION,
            'explicit native descriptor transport required')
    path = Path(envelope['authority'])
    require(path.parent == authority.publication.AUTHORITY_ROOT
            and re.fullmatch('[a-f0-9]{64}\\.json', path.name), 'native descriptor plan path differs')
    from .private_mount_plan import ApprovedPrivateMountPlan
    # Authenticate the root record before asking for any descriptors.
    body, _ = authority._read(path, 65536)
    identity = InvocationIdentity.from_dict(json.loads(body)['identity'])
    plan = ApprovedPrivateMountPlan.read(path, identity)
    expected = plan.authorize(envelope['entries'], argv)
    require({k: v for k, v in envelope.items() if k != 'transport'} == expected,
            'native descriptor root plan differs')
    request = {'schema_version': VERSION, 'identity_sha256': path.stem,
               'plan_sha256': envelope['authority_sha256']}
    connection, peer = _connect(60)
    fds = []
    try:
        with connection:
            packet = canonical_json_bytes(request)
            require(connection.send(packet) == len(packet), 'native descriptor request incomplete')
            answer, fds = authority._receive(connection, peer)
        require(answer == {**request, 'descriptor_count': len(envelope['entries'])}
                and len(fds) == len(envelope['entries']), 'native descriptor response differs')
        return fds
    except BaseException:
        _close(fds)
        raise
