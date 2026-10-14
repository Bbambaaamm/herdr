"""Real descriptor IPC; root/host-peer authority remains explicit doubles."""
import array
import json
import os
import socket
import threading
import ctypes
from pathlib import Path
import subprocess
import sys
import errno
from types import SimpleNamespace

import pytest
from herdr import launch_plan_issuer as issuer, native_fd_handoff as transfer
from herdr.security import SecurityError, canonical_json_bytes
from tests.herdr.test_launch_plan_issuer import configure, run_server, RootOS
from tests.herdr.test_launch_plan_handoff import live


@pytest.fixture
def prepared(live, monkeypatch, request):
    raw, policy, approvals, listener = configure(live, monkeypatch)
    custody = transfer.DescriptorCustody()
    original = issuer.issue_request
    monkeypatch.setattr(issuer, 'issue_request', lambda connection: original(connection, custody=custody))
    ambiguous = getattr(request, 'param', None) == 'post-rename-error'
    if ambiguous:
        publish = issuer.publication._publish_approved_launch_plan
        def visible_then_failed(*args, **kwargs):
            publish(*args, **kwargs)
            raise OSError('fixture post-rename fsync/reply failure')
        monkeypatch.setattr(issuer.publication, '_publish_approved_launch_plan', visible_then_failed)
    thread, errors, results = run_server(listener)
    try:
        live.launch.prepare_private_command(live.builder)
        thread.join(5)
        assert not thread.is_alive()
        if ambiguous: assert errors and 'error' in results[0]
        else: assert not errors and results[0]['published']
    finally:
        listener.close(); thread.join(5)
    assert len(custody.pending) == 1
    key = next(iter(custody.pending))
    row = custody.pending[key]
    proposal = row['request']['proposal']
    envelope = live.launch.mount.private_mount_plan.authorize(proposal['plan']['descriptors'], proposal['argv'])
    envelope['transport'] = transfer.VERSION
    argv = ['pinned-python', '-I', '-B', 'approved-wrapper', transfer.ENTRYPOINT,
            json.dumps(envelope, separators=(',', ':')), *proposal['argv']]
    monkeypatch.setattr(transfer, 'os', RootOS())
    monkeypatch.setattr(issuer, '_proc_bytes', lambda *args: '\0'.join(argv).encode())
    monkeypatch.setattr(issuer, '_host_peer', lambda *args: row['peer'])
    from herdr import launch_environment
    from herdr.policy_launch import IDENTITY_ENV
    monkeypatch.setattr(launch_environment, 'process_environment', lambda pid: {
        name: str(proposal['plan']['identity'][field]) for field, name in IDENTITY_ENV.items()})
    try:
        yield SimpleNamespace(custody=custody, key=key, row=row, envelope=envelope, argv=argv,
                              live=live, policy=policy, raw=raw, proposal=proposal)
    finally:
        custody.close()


def packet(p):
    return {'schema_version': transfer.VERSION, 'identity_sha256': p.key,
            'plan_sha256': issuer._digest(p.proposal['plan'])}


def exchange(p, request=None, incoming=()):
    sender, receiver = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    sender.settimeout(3); receiver.settimeout(3)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    rights = [] if not incoming else [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', incoming))]
    sender.sendmsg([canonical_json_bytes(request or packet(p))], rights)
    try:
        p.custody.redeem(receiver)
        return issuer._receive(sender, p.row['peer'])
    finally:
        sender.close(); receiver.close()


def test_root_custody_transfers_exact_fds_once_and_keeps_originals(prepared):
    p = prepared
    copies = list(p.row['fds'])
    answer, received = exchange(p)
    try:
        assert answer == {**packet(p), 'descriptor_count': len(received)}
        assert len(received) == len(p.proposal['plan']['descriptors'])
        for entry, fd in zip(p.proposal['plan']['descriptors'], received):
            st = os.fstat(fd)
            assert (st.st_dev, st.st_ino) == (entry['device'], entry['inode'])
            assert not os.get_inheritable(fd)
        assert not p.custody.pending
        for fd in copies:
            with pytest.raises(OSError): os.fstat(fd)
        for entry in p.proposal['plan']['descriptors']: os.fstat(entry['fd'])
        with pytest.raises(SecurityError, match='unavailable'): exchange(p)
    finally:
        for fd in received: os.close(fd)


@pytest.mark.parametrize('fault', ['plan', 'identity', 'extra-field', 'version', 'role', 'argv', 'owner', 'policy', 'root-plan', 'expiry', 'environment'])
def test_invalid_or_withdrawn_redemption_never_delivers_fds(prepared, monkeypatch, fault):
    p = prepared; request = packet(p)
    if fault == 'plan': request['plan_sha256'] = '0' * 64
    elif fault == 'identity': request['identity_sha256'] = '0' * 64
    elif fault == 'extra-field': request['unapproved'] = True
    elif fault == 'version': request['schema_version'] = 'wrong'
    elif fault == 'role': p.argv[4] = 'agent-stack/bin/agent-task-worker'
    elif fault == 'argv': p.argv[-1] = 'unapproved-command'
    elif fault == 'owner': monkeypatch.setattr(issuer, '_host_peer', lambda *args: (*p.row['peer'][:3], -1))
    elif fault == 'policy': p.policy['request_timeout_seconds'] = 2
    elif fault == 'root-plan': p.live.launch.mount.private_mount_plan.path.unlink()
    elif fault == 'expiry': p.row['deadline'] = 0
    else:
        from herdr import launch_environment
        monkeypatch.setattr(launch_environment, 'process_environment', lambda pid: {})
    with pytest.raises((SecurityError, OSError, ValueError)): exchange(p, request)


def test_unexpected_received_rights_are_closed_before_denial(prepared):
    p = prepared
    fd = p.row['fds'][0]
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(SecurityError, match='closed native'): exchange(p, incoming=(fd,))
    assert len(os.listdir('/proc/self/fd')) == before
    assert len(p.custody.pending) == 1


def test_expiry_and_shutdown_close_only_custody_copies(prepared):
    p = prepared; copies = list(p.row['fds'])
    p.row['deadline'] = 0; p.custody.prune()
    assert not p.custody.pending
    for fd in copies:
        with pytest.raises(OSError): os.fstat(fd)
    for entry in p.proposal['plan']['descriptors']: os.fstat(entry['fd'])


def test_capacity_is_bounded_before_another_publication(prepared, monkeypatch):
    monkeypatch.setattr(transfer, 'MAX_PENDING', 1)
    with pytest.raises(SecurityError, match='full'): prepared.custody.require_capacity()


def test_lost_reply_consumes_custody_and_closes_all_copies(prepared):
    p = prepared; copies = list(p.row['fds'])
    sender, receiver = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    sender.send(canonical_json_bytes(packet(p))); sender.close()
    try:
        with pytest.raises(OSError): p.custody.redeem(receiver)
    finally: receiver.close()
    assert not p.custody.pending
    for fd in copies:
        with pytest.raises(OSError): os.fstat(fd)
    assert p.live.launch.mount.private_mount_plan.path.exists()


def test_actual_unprivileged_process_cannot_redeem():
    if os.geteuid() == 0: pytest.skip('ordinary-user root refusal requires non-root')
    with pytest.raises(SecurityError, match='root native'): transfer.DescriptorCustody().redeem(None)


def test_actual_client_checks_plan_and_received_fd_inventory(prepared, monkeypatch):
    p = prepared
    sender, receiver = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    for endpoint in (sender, receiver):
        endpoint.settimeout(3); endpoint.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    monkeypatch.setattr(transfer, '_connect', lambda timeout: (sender, p.row['peer']))  # Root endpoint UID only is doubled.
    errors = []
    def serve():
        try: p.custody.redeem(receiver)
        except Exception as error: errors.append(error)
        finally: receiver.close()
    thread = threading.Thread(target=serve); thread.start()
    received = []
    try:
        received = transfer.receive_descriptors(p.envelope, p.proposal['argv'])
        assert len(received) == len(p.proposal['plan']['descriptors'])
        thread.join(5); assert not thread.is_alive() and not errors
    finally:
        for fd in received: os.close(fd)
        sender.close(); thread.join(5)


def test_custody_survives_original_issuance_deadline_for_reconciliation(prepared, monkeypatch):
    p = prepared
    original = p.row['request_deadline']
    handoff = p.raw['private_launch']['plan_handoff']['timeout_seconds']
    assert p.row['binding_deadline'] == pytest.approx(original + handoff)
    assert p.row['deadline'] == pytest.approx(original + handoff + transfer.REDEMPTION_SECONDS)
    monkeypatch.setattr(transfer, 'time', SimpleNamespace(monotonic=lambda: original + 0.1))
    p.custody.prune()
    assert p.key in p.custody.pending
    _, received = exchange(p)
    for fd in received: os.close(fd)
    assert not p.custody.pending


@pytest.mark.parametrize('prepared', ['post-rename-error'], indirect=True)
def test_ambiguous_visible_plan_keeps_redeemable_custody(prepared):
    p = prepared
    assert p.row['active'] and p.live.launch.mount.private_mount_plan.path.exists()
    _, received = exchange(p)
    for fd in received: os.close(fd)
    assert not p.custody.pending


def test_host_resume_after_fixed_reconciliation_window_does_not_launch(live, monkeypatch):
    from herdr import launch_plan_handoff as handoff
    _, _, _, listener = configure(live, monkeypatch)
    client = live.launch.private_plan_handoff.automatic_issuer
    original = client.issue
    clock = [issuer.time.monotonic()]
    def delayed(*args, **kwargs):
        original(*args, **kwargs)
        clock[0] = live.launch._private_issuer_reconciliation_deadline + 1
    monkeypatch.setattr(client, 'issue', delayed)
    monkeypatch.setattr(handoff, 'time', SimpleNamespace(monotonic=lambda:clock[0],sleep=lambda seconds:None))
    thread, errors, _ = run_server(listener)
    try:
        with pytest.raises(SecurityError, match='timed out'):
            live.launch.prepare_private_command(live.builder)
        thread.join(5)
        assert not thread.is_alive() and not errors
        assert live.launch.mount.private_mount_plan is None and live.launch.sealed is None
        assert len(list(live.plans.glob('*.json'))) == 1
    finally: listener.close();thread.join(5)


@pytest.mark.parametrize('boundary', [3, 4])
def test_late_verification_failure_removes_only_unpublished_stages(live, monkeypatch, boundary):
    _, _, approvals, listener = configure(live, monkeypatch)
    original = issuer._validate; calls = []
    def withdrawn(*args):
        calls.append(1)
        if len(calls) == boundary: raise SecurityError('fixture late withdrawal')
        return original(*args)
    monkeypatch.setattr(issuer, '_validate', withdrawn)
    thread, errors, _ = run_server(listener)
    try:
        with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
        thread.join(5)
        assert not thread.is_alive() and errors
        assert not list(approvals.glob('.automatic-*'))
        assert not list(live.plans.glob('.launch-plan-*')) and not list(live.plans.glob('*.json'))
        assert len(list(approvals.glob('*.json'))) == (0 if boundary == 3 else 1)
    finally: listener.close();thread.join(5)


@pytest.mark.parametrize('fail_at', [1, 2])
def test_fd_duplication_failure_precedes_irreversible_publication(live, monkeypatch, fail_at):
    _, _, approvals, listener = configure(live, monkeypatch)
    custody = transfer.DescriptorCustody()
    original = issuer.issue_request
    monkeypatch.setattr(issuer, 'issue_request', lambda connection: original(connection, custody=custody))
    copies = []
    class ExhaustedOS(RootOS):
        def dup(self, fd):
            if len(copies) + 1 == fail_at: raise OSError(errno.EMFILE, 'fixture FD pressure')
            duplicate = os.dup(fd); copies.append(duplicate); return duplicate
    monkeypatch.setattr(transfer, 'os', ExhaustedOS())
    thread, errors, _ = run_server(listener)
    try:
        with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
        thread.join(5)
        assert not thread.is_alive() and errors
        assert not list(approvals.glob('*.json')) and not list(live.plans.glob('*.json'))
        assert not custody.pending
        for fd in copies:
            with pytest.raises(OSError): os.fstat(fd)
    finally: listener.close();thread.join(5);custody.close()


def test_plan_publication_failure_cancels_staged_custody(live, monkeypatch):
    _, _, _, listener = configure(live, monkeypatch)
    custody = transfer.DescriptorCustody(); copies = []
    original = issuer.issue_request
    stage = custody.stage
    def observed_stage(*args):
        key = stage(*args); copies.extend(custody.pending[key]['fds']); return key
    monkeypatch.setattr(custody, 'stage', observed_stage)
    monkeypatch.setattr(issuer, 'issue_request', lambda connection: original(connection, custody=custody))
    def denied(*args, **kwargs): raise OSError('fixture plan publication failure')
    monkeypatch.setattr(issuer.publication, '_publish_approved_launch_plan', denied)
    thread, errors, _ = run_server(listener)
    try:
        with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
        thread.join(5)
        assert not thread.is_alive() and errors and copies and not custody.pending
        assert not list(live.plans.glob('*.json'))
        for fd in copies:
            with pytest.raises(OSError): os.fstat(fd)
    finally: listener.close();thread.join(5);custody.close()


@pytest.mark.skipif(sys.platform != 'linux' or os.geteuid() == 0,
                    reason='actual non-root Linux memory protection required')
def test_kernel_transfers_fd_between_protected_processes_without_proc_access(tmp_path):
    # Only the IPC socket is inherited. The private data FD crosses SCM_RIGHTS;
    # both sender and receiver stay non-dumpable throughout the transfer.
    private = tmp_path / 'private'; private.write_bytes(b'protected descriptor fixture')
    fd = os.open(private, os.O_PATH | os.O_CLOEXEC)
    sender, receiver = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    program = r'''
import array,ctypes,json,os,socket,sys
libc=ctypes.CDLL(None,use_errno=True)
assert libc.prctl(4,0,0,0,0)==0 and libc.prctl(3,0,0,0,0)==0
try: os.open(sys.argv[2],os.O_PATH)
except PermissionError: pass
else: raise SystemExit('protected parent was readable')
with socket.socket(fileno=int(sys.argv[1])) as channel:
    body,ancillary,flags,_=channel.recvmsg(32,socket.CMSG_SPACE(16),socket.MSG_CMSG_CLOEXEC)
    assert body==b'approved' and not flags & (socket.MSG_TRUNC|socket.MSG_CTRUNC) and len(ancillary)==1
    level,kind,rights=ancillary[0];assert (level,kind)==(socket.SOL_SOCKET,socket.SCM_RIGHTS)
    fds=array.array('i');fds.frombytes(rights);assert len(fds)==1
    try:
        opened=os.open('/proc/self/fd/'+str(fds[0]),os.O_RDONLY|os.O_CLOEXEC)
        try: assert os.read(opened,128)==b'protected descriptor fixture'
        finally: os.close(opened)
        assert libc.prctl(3,0,0,0,0)==0
        print(json.dumps({'non_dumpable':True,'received_inode':os.fstat(fds[0]).st_ino}))
    finally: os.close(fds[0])
'''
    libc = ctypes.CDLL(None, use_errno=True)
    previous = libc.prctl(3, 0, 0, 0, 0)
    child = None
    try:
        assert libc.prctl(4, 0, 0, 0, 0) == 0
        child = subprocess.Popen([sys.executable, '-I', '-B', '-c', program,
            str(receiver.fileno()), f'/proc/{os.getpid()}/fd/{fd}'],
            pass_fds=(receiver.fileno(),), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        receiver.close()
        sender.sendmsg([b'approved'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [fd]))])
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == 0, stderr
        assert json.loads(stdout) == {'non_dumpable':True,'received_inode':os.fstat(fd).st_ino}
        assert libc.prctl(3, 0, 0, 0, 0) == 0
    finally:
        if child is not None and child.poll() is None: child.kill();child.communicate(timeout=5)
        assert libc.prctl(4, previous, 0, 0, 0) == 0
        sender.close();receiver.close();os.close(fd)


def test_last_moment_binding_still_allows_delayed_pane_fd_redemption(prepared, monkeypatch):
    p = prepared
    binding = p.live.launch._private_handoff_state[1]
    assert p.row['deadline'] >= binding + transfer.REDEMPTION_SECONDS - 0.001
    clock = [binding - 0.01]
    from herdr import launch_plan_handoff as handoff
    monkeypatch.setattr(handoff, 'time', SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(transfer, 'time', SimpleNamespace(monotonic=lambda: clock[0]))
    p.live.launch.verify_private_handoff()
    clock[0] += 5  # pane dispatch starts after the binding window has ended
    p.custody.prune()
    assert p.key in p.custody.pending
    _, received = exchange(p)
    for fd in received: os.close(fd)
    assert not p.custody.pending


def test_dispatch_reserve_never_extends_grant_or_stages_expiring_grant(prepared, monkeypatch):
    from datetime import UTC, datetime, timedelta
    from copy import deepcopy
    p = prepared
    request = deepcopy(p.row['request'])
    p.custody.cancel(p.key)
    now = transfer.time.monotonic()
    expiry = datetime.now(UTC) + timedelta(seconds=transfer.REDEMPTION_SECONDS + 5)
    request['grant']['expires_at'] = expiry.isoformat()
    key = p.custody.stage(request, p.row['peer'], p.row['issuer'], p.raw,
                         [entry['fd'] for entry in p.proposal['plan']['descriptors']], now + 60)
    row = p.custody.pending[key]
    assert row['binding_deadline'] == pytest.approx(now + 5, abs=0.05)
    assert row['deadline'] == pytest.approx(now + transfer.REDEMPTION_SECONDS + 5, abs=0.05)
    assert row['deadline'] - row['binding_deadline'] == pytest.approx(transfer.REDEMPTION_SECONDS)
    p.custody.cancel(key)
    request['grant']['expires_at'] = (datetime.now(UTC) + timedelta(seconds=1)).isoformat()
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(SecurityError, match='no dispatch interval'):
        p.custody.stage(request, p.row['peer'], p.row['issuer'], p.raw,
                       [entry['fd'] for entry in p.proposal['plan']['descriptors']], now + 60)
    assert not p.custody.pending and len(os.listdir('/proc/self/fd')) == before
