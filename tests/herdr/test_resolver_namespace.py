"""Public DNS only: no credential access, provider calls or host mutation."""
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from herdr import resolver_namespace as resolver
from herdr.security import SecurityError


def test_real_host_source_is_independently_verified_and_kernel_sealed():
    target, body = resolver.read_host_resolver()
    snapshot = resolver.ResolverSnapshot.create()
    fd = snapshot.data.fd
    try:
        entry = snapshot.descriptor()
        assert entry['target'] == target and os.pread(fd, resolver.MAX_BYTES + 1, 0) == body
        resolver.verify_host_descriptor(entry, fd, host_uid=os.geteuid())
        for mutate in (lambda: os.write(fd, b'forged'), lambda: os.ftruncate(fd, 0)):
            with pytest.raises(OSError) as denied:
                mutate()
            assert denied.value.errno == errno.EPERM
        assert snapshot.descriptor() == entry
    finally:
        snapshot.close(); snapshot.close()
    with pytest.raises(OSError): os.fstat(fd)


def test_resolver_service_must_not_share_worker_uid(monkeypatch):
    monkeypatch.setattr(resolver.pwd, 'getpwnam', lambda name: SimpleNamespace(pw_uid=1001))
    with pytest.raises(SecurityError, match='worker identity'):
        resolver._owners(1001)


@pytest.mark.parametrize('fault', ['target', 'digest', 'size', 'zero', 'oversize', 'unsealed', 'host-drift'])
def test_descriptor_requires_exact_host_bytes_and_seals(monkeypatch, fault):
    snapshot = resolver.ResolverSnapshot.create()
    fd = snapshot.data.fd
    extra = None
    try:
        entry = snapshot.descriptor()
        if fault == 'target': entry['target'] = '/etc/passwd'
        elif fault == 'digest': entry['sha256'] = '0' * 64
        elif fault == 'size': entry['size'] += 1
        elif fault == 'zero': entry['size'] = 0
        elif fault == 'oversize': entry['size'] = resolver.MAX_BYTES + 1
        elif fault == 'unsealed':
            extra = os.memfd_create('unsealed-resolver', os.MFD_ALLOW_SEALING)
            os.write(extra, os.pread(fd, resolver.MAX_BYTES + 1, 0)); fd = extra
        elif fault == 'host-drift':
            monkeypatch.setattr(resolver, 'read_host_resolver', lambda **kwargs: (entry['target'], b'changed'))
        with pytest.raises((SecurityError, OSError)):
            resolver.verify_host_descriptor(entry, fd, host_uid=os.geteuid())
    finally:
        if extra is not None: os.close(extra)
        snapshot.close()


@pytest.mark.parametrize('fault', ['owner', 'writable', 'symlink', 'fifo', 'oversize', 'parent-link'])
def test_source_walk_rejects_untrusted_or_nonregular_input(tmp_path, monkeypatch, fault):
    """Only root UID metadata is doubled; actual no-follow opens and modes remain real."""
    root = tmp_path / 'host'; root.mkdir()
    etc = root / 'etc'; etc.mkdir()
    source = etc / 'resolv.conf'
    if fault == 'symlink': source.symlink_to('/etc/passwd')
    elif fault == 'fifo': os.mkfifo(source)
    elif fault == 'parent-link':
        other = root / 'other'; other.mkdir()
        etc.rmdir(); etc.symlink_to(other, target_is_directory=True)
        source.write_bytes(b'nameserver 127.0.0.53\n')
    else: source.write_bytes(b'x' * (resolver.MAX_BYTES + 1) if fault == 'oversize' else b'nameserver 127.0.0.53\n')
    if fault == 'writable': source.chmod(0o666)
    actual_open, actual_fstat = os.open, os.fstat
    def rooted_open(path, flags, *args, **kwargs):
        return actual_open(root if path == '/' else path, flags, *args, **kwargs)
    def root_metadata(fd):
        info = actual_fstat(fd)
        values = {key: getattr(info, key) for key in dir(info) if key.startswith('st_')}
        values['st_uid'] = 1001 if fault == 'owner' else 0
        return SimpleNamespace(**values)
    monkeypatch.setattr(resolver.os, 'open', rooted_open)
    monkeypatch.setattr(resolver.os, 'fstat', root_metadata)
    with pytest.raises((SecurityError, OSError)):
        resolver._trusted_read('/etc/resolv.conf', {0})


@pytest.mark.parametrize('flags', [{'rw'}, {'ro', 'rw'}, {'ro', '__stacked__'}, set()])
def test_mounted_verifier_rejects_write_or_stacked_mount_before_open(flags):
    snapshot = resolver.ResolverSnapshot.create()
    try:
        entry = snapshot.descriptor()
        with pytest.raises(SecurityError, match='read only'):
            resolver.verify_mounted(entry, os.getpid(), {entry['target']: flags})
    finally: snapshot.close()


@pytest.mark.parametrize('restore', [False, True])
def test_actual_private_run_keeps_only_sealed_dns(tmp_path, restore):
    if not Path('/usr/bin/bwrap').is_file(): pytest.skip('bubblewrap unavailable')
    snapshot = resolver.ResolverSnapshot.create()
    try:
        entry = snapshot.descriptor()
        if not restore and not entry['target'].startswith('/run/'):
            pytest.skip('regular /etc resolver is unaffected by the /run mask')
        sentinel = tmp_path / 'sentinel'; sentinel.write_text('host runtime must stay hidden')
        check = '''import errno,hashlib,os,sys
assert not os.path.exists('/run/sentinel')
try: body=open('/etc/resolv.conf','rb').read()
except FileNotFoundError:
    assert sys.argv[1]=='missing'
else:
    assert sys.argv[1]=='restored'
    assert hashlib.sha256(body).hexdigest()==sys.argv[2]
    try: open('/etc/resolv.conf','wb')
    except OSError as error: assert error.errno==errno.EROFS
    else: raise AssertionError('resolver writable')
'''
        args = ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--dev', '/dev', '--unshare-pid',
                '--unshare-net', '--die-with-parent', '--proc', '/proc',
                '--ro-bind', str(tmp_path), '/run', '--tmpfs', '/run']
        if restore:
            args += snapshot.parent_args() + ['--ro-bind-data', str(entry['fd']), entry['target']]
        args += ['--', sys.executable, '-I', '-S', '-c', check,
                 'restored' if restore else 'missing', entry['sha256']]
        result = subprocess.run(args, pass_fds=(entry['fd'],), capture_output=True, timeout=15)
        if result.returncode and any(text in result.stderr for text in
                (b'Operation not permitted', b'Creating new namespace failed')):
            pytest.skip('unprivileged bwrap disabled by runner')
        assert result.returncode == 0, result.stderr.decode(errors='replace')
    finally: snapshot.close()


def test_resolver_data_cannot_use_profile_only_launcher_exception():
    from tests.herdr.test_policy_launch import sandbox_module
    snapshot = resolver.ResolverSnapshot.create()
    try:
        entry = snapshot.descriptor()
        args = ['/usr/bin/python3', '-I', '-S', '-c', sandbox_module()._POLICY_FD_LAUNCHER,
                json.dumps([entry]), '/usr/bin/bwrap', '--ro-bind', '/', '/', '--tmpfs', '/run',
                *snapshot.parent_args(), '--ro-bind-data', str(entry['fd']), entry['target'], '--', '/bin/true']
        result = subprocess.run(args, pass_fds=(entry['fd'],), capture_output=True, timeout=10)
        assert result.returncode != 0 and b'policy_fd_resolver_manifest_invalid' in result.stderr
    finally: snapshot.close()
