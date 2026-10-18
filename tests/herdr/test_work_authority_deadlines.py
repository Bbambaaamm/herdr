"""Real Unix transport; physical mount verification is an explicit delayed adapter."""
import json
import os
import socket
import threading
import time

import pytest

from herdr.security import PolicyDenied
from herdr.work_authority import WorkAuthorityClient, dispatch_work_connection
from tests.herdr.test_work_authority import owner_for
from tests.herdr.test_work_budget_configuration import approved_factory


def test_budget_status_waits_for_both_physical_checks(tmp_path, monkeypatch):
    factory, root, plan, grant, cycle, raw, allocation, quote = approved_factory(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_budget = factory.budget_effect
    original_verify = owner.launch.mount.verify_mounted
    def slow_verify(pid, sealed):
        original_verify(pid, sealed)
        time.sleep(3)
    owner.launch.mount.verify_mounted = slow_verify
    original = factory.budget_authority.audit_log._path.read_bytes()
    path = tmp_path / 's'
    monkeypatch.setattr('herdr.work_authority.SOCKET_PATH', path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(1); listener.settimeout(10)
    errors = []
    def serve():
        try:
            connection, _ = listener.accept()
            assert dispatch_work_connection(owner, connection)
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        assert WorkAuthorityClient().effect(grant.identity, grant.hash, 'status', {}) == {'required': True}
        thread.join(10)
        assert not thread.is_alive() and not errors
        assert len(observed) == 2
        assert factory.budget_authority.audit_log._path.read_bytes() == original
    finally:
        listener.close(); thread.join(10)


@pytest.mark.parametrize('budget', [True, False])
def test_whole_response_deadline_stops_slow_chunks_without_retry(tmp_path, monkeypatch, budget):
    import herdr.work_authority as transport
    factory, root, plan, grant, cycle, raw, allocation, quote = approved_factory(tmp_path)
    path = tmp_path / 's'
    monkeypatch.setattr(transport, 'SOCKET_PATH', path)
    monkeypatch.setattr(transport, '_WORK_REQUEST_TIMEOUT_SECONDS', .12)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(2); listener.settimeout(2)
    requests = []
    response = b'{"required":true}\n' if budget else b'work-ok\n'
    def serve():
        connection, _ = listener.accept()
        with connection:
            requests.append(connection.recv(8193))
            for byte in response:
                try: connection.sendall(bytes([byte]))
                except OSError: break
                time.sleep(.05)
    thread = threading.Thread(target=serve, daemon=True); thread.start()
    began = time.monotonic()
    try:
        with pytest.raises(PolicyDenied, match='work_budget_unavailable' if budget else 'work_authority_unavailable'):
            if budget:
                WorkAuthorityClient().effect(grant.identity, grant.hash, 'status', {})
            else:
                WorkAuthorityClient()(grant.identity, grant.hash, kind='provider')
        assert time.monotonic() - began < 1.5
        thread.join(2)
        assert not thread.is_alive() and len(requests) == 1
    finally:
        listener.close(); thread.join(2)


@pytest.mark.parametrize('response', [b'x' * 8193, b'{"required":true}', b'[]\n'])
def test_invalid_budget_frames_are_denied_without_retry(tmp_path, monkeypatch, response):
    import herdr.work_authority as transport
    factory, root, plan, grant, cycle, raw, allocation, quote = approved_factory(tmp_path)
    path = tmp_path / 's'
    monkeypatch.setattr(transport, 'SOCKET_PATH', path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(1); listener.settimeout(2)
    requests = []
    def serve():
        connection, _ = listener.accept()
        with connection:
            requests.append(connection.recv(8193))
            connection.sendall(response)
    thread = threading.Thread(target=serve, daemon=True); thread.start()
    try:
        with pytest.raises(PolicyDenied):
            WorkAuthorityClient().effect(grant.identity, grant.hash, 'status', {})
        thread.join(2)
        assert not thread.is_alive() and len(requests) == 1
    finally:
        listener.close(); thread.join(2)


def test_response_timeout_keeps_original_started_model_reservation(tmp_path, monkeypatch):
    import herdr.work_authority as transport
    factory, root, plan, grant, cycle, raw, allocation, quote = approved_factory(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_budget = factory.budget_effect
    original_verify = owner.launch.mount.verify_mounted
    def delay_after_reservation(pid, sealed):
        original_verify(pid, sealed)
        if len(observed) == 2: time.sleep(.3)
    owner.launch.mount.verify_mounted = delay_after_reservation
    path = tmp_path / 's'
    monkeypatch.setattr(transport, 'SOCKET_PATH', path)
    monkeypatch.setattr(transport, '_WORK_REQUEST_TIMEOUT_SECONDS', .12)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(1); listener.settimeout(2)
    accepted = []
    def serve():
        connection, _ = listener.accept()
        accepted.append(True)
        assert dispatch_work_connection(owner, connection)
    thread = threading.Thread(target=serve, daemon=True); thread.start()
    route = {key: quote[key] for key in ('provider','model','api_mode','base_url')}
    payload = dict(route, request_id='deadline-start', request_sha256='a' * 64,
                   request_bytes=100, output_tokens=100)
    try:
        with pytest.raises(PolicyDenied, match='work_budget_unavailable'):
            WorkAuthorityClient().effect(grant.identity, grant.hash, 'start', payload)
        thread.join(2)
        assert not thread.is_alive() and len(accepted) == 1
        events = [json.loads(line) for line in factory.budget_authority.audit_log._path.read_bytes().splitlines()]
        operations = [event for event in events if event['event']=='work_budget_reserve' and event['operation_kind']=='model']
        assert len(operations) == 1
        operation = factory.budget_authority.reconcile(operations[0]['operation_id'])
        assert operation['started'] and operation['usage'] is None
        state = factory.budget_authority.snapshot(allocation.allocation_id)
        assert state['inflight'] == 1 and state['charged_upper_bounds']['model_calls'] == 1
    finally:
        listener.close(); thread.join(2)
