"""Disposable host audit/Unix peers and real pinned formatter; no model or auth."""
import dataclasses
import importlib.util
import itertools
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from herdr.sdk_observation import (
    ERROR_TYPES, MAX_OBSERVATIONS, PHASES, error_type, observe_failures,
    report_failure, validate_observation,
)
from herdr.hermes_guard import GuardInstallation, _install_sdk_observation_formatter
from herdr.security import PolicyDenied
from herdr.work_authority import WorkAuthorityClient, dispatch_work_connection
from herdr.work_contract_host import HostWorkContractFactory, WorkInvocationGuard
from tests.herdr.test_work_authority import owner_for
from tests.herdr.test_work_contract_host import factory_fixture

OBS = {"phase": "sdk_agent_init", "outcome": "failed", "error_type": "TypeError"}


def prepared(tmp_path):
    factory, root, plan, grant, log = factory_fixture(tmp_path)
    factory.prepare(identity=grant.identity, workspace=root, grant=grant,
                    spec_sha256=plan.spec_sha256)
    return factory, root, plan, grant, log


def observation_events(log):
    return [row for row in log.replay() if row["event"] == "work_sdk_observation"]


def dispatch(owner, request):
    left, right = socket.socketpair()
    try:
        right.sendall(json.dumps(request).encode() + b"\n")
        assert dispatch_work_connection(owner, left)
        return right.recv(128)
    finally:
        left.close()
        right.close()


def request_for(grant, observation=None):
    return {"op": "work-sdk-observation", "identity": grant.identity.to_json(),
            "grant_sha256": grant.hash, "observation": OBS if observation is None else observation}


@pytest.mark.parametrize("bad", [
    None, [], {"phase": "sdk_agent_init"}, {**OBS, "message": "unit-secret"},
    {**OBS, "phase": "provider=unit-secret"}, {**OBS, "outcome": "pass"},
    {**OBS, "error_type": "unit-secret"}, {**OBS, "error_type": 1},
    {**OBS, "phase": True},
])
def test_closed_observation_schema(bad):
    with pytest.raises(ValueError, match="closed SDK observation"):
        validate_observation(bad)


def test_error_classifier_never_reads_text_or_dynamic_class_name():
    class Secret(Exception):
        def __str__(self):
            pytest.fail("exception text must never be inspected")
    assert error_type(Secret()) == "UnknownError"
    assert error_type(PermissionError("unit-secret")) == "PermissionError"
    assert error_type(TypeError("unit-secret")) == "TypeError"
    assert error_type(PolicyDenied("unit-secret")) == "PolicyDenied"


@pytest.mark.parametrize("failure", [RuntimeError, TimeoutError, SystemExit])
def test_diagnostic_failure_cannot_replace_original_exception(failure):
    original = TypeError("original unit-secret")
    def unavailable(row):
        raise failure("diagnostic unit-secret")
    guard = SimpleNamespace(observe_sdk=unavailable)
    @observe_failures(guard, "sdk_agent_init")
    def invoke():
        raise original
    with pytest.raises(TypeError) as caught:
        invoke()
    assert caught.value is original
    assert report_failure(guard, "sdk_agent_init", original) is False


def test_observation_preserves_all_success_return_values_without_reporting():
    guard = SimpleNamespace(observe_sdk=lambda row: pytest.fail("success is not an error"))
    value = object()
    @observe_failures(guard, "sdk_middleware")
    def invoke(argument):
        assert argument is value
        return value
    assert invoke(value) is value


def test_existing_audit_binding_flush_duplicate_and_restart(tmp_path, monkeypatch):
    factory, root, plan, grant, log = prepared(tmp_path)
    before = log.replay()
    phase = factory.cycles[next(iter(factory.cycles))][0].phase
    calls = []
    real_sync = os.fsync
    def synced(fd):
        calls.append(os.fstat(fd).st_mode)
        return real_sync(fd)
    monkeypatch.setattr(os, "fsync", synced)
    assert factory.observe_sdk(grant.identity, grant.hash, OBS)
    rows = observation_events(log)
    assert rows == [{"event": "work_sdk_observation", "work_cycle": grant.identity.to_json(),
                     "plan_sha256": plan.hash, "grant_sha256": grant.hash,
                     "provenance": "sdk_observed", "observation_index": 1, "observation": OBS}]
    assert len(calls) == 2
    raw = log._path.read_bytes()
    calls.clear()
    assert factory.observe_sdk(grant.identity, grant.hash, dict(OBS))
    assert log._path.read_bytes() == raw and len(calls) == 2
    assert factory.cycles[next(iter(factory.cycles))][0].phase is phase
    assert log.replay()[:-1] == before
    restored = HostWorkContractFactory(approve=factory.approve, environment=factory.environment,
        storage=factory.storage, audit_log=log, git=factory.git)
    restored.recover(identity=grant.identity, workspace=root, spec_sha256=plan.spec_sha256,
                     grant_sha256=grant.hash, plan_sha256=plan.hash)
    assert restored.observe_sdk(grant.identity, grant.hash, dict(OBS))
    assert log._path.read_bytes() == raw


def test_event_limit_is_retained_across_restart_and_duplicates_still_ack(tmp_path):
    factory, root, plan, grant, log = prepared(tmp_path)
    rows = [{"phase": phase, "outcome": "failed", "error_type": kind}
            for phase, kind in itertools.product(sorted(PHASES), sorted(ERROR_TYPES))]
    for row in rows[:MAX_OBSERVATIONS]:
        assert factory.observe_sdk(grant.identity, grant.hash, row)
    raw = log._path.read_bytes()
    with pytest.raises(Exception, match="limit reached"):
        factory.observe_sdk(grant.identity, grant.hash, rows[MAX_OBSERVATIONS])
    restored = HostWorkContractFactory(approve=factory.approve, environment=factory.environment,
        storage=factory.storage, audit_log=log, git=factory.git)
    restored.recover(identity=grant.identity, workspace=root, spec_sha256=plan.spec_sha256,
                     grant_sha256=grant.hash, plan_sha256=plan.hash)
    assert restored.observe_sdk(grant.identity, grant.hash, rows[0])
    with pytest.raises(Exception, match="limit reached"):
        restored.observe_sdk(grant.identity, grant.hash, rows[MAX_OBSERVATIONS])
    assert log._path.read_bytes() == raw


def test_duplicate_sync_failure_propagates_without_new_entry(tmp_path, monkeypatch):
    factory, root, plan, grant, log = prepared(tmp_path)
    factory.observe_sdk(grant.identity, grant.hash, OBS)
    raw = log._path.read_bytes()
    def failed(fd):
        raise OSError("unit-only failed sync")
    monkeypatch.setattr(os, "fsync", failed)
    with pytest.raises(OSError):
        factory.observe_sdk(grant.identity, grant.hash, OBS)
    assert log._path.read_bytes() == raw


@pytest.mark.parametrize("fault", ["identity", "grant", "extra", "metadata"])
def test_invalid_real_peer_observations_do_not_write_audit(tmp_path, fault):
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_observe = factory.observe_sdk
    request = request_for(grant)
    if fault == "identity": request["identity"]["run_token"] = "foreign"
    if fault == "grant": request["grant_sha256"] = "f" * 64
    if fault == "extra": request["message"] = "unit-secret"
    if fault == "metadata": request["observation"] = {**OBS, "outcome": "pass"}
    raw = log._path.read_bytes()
    assert dispatch(owner, request) == b"denied\n"
    assert log._path.read_bytes() == raw


def test_real_peer_ack_only_after_audit_sync_and_two_mount_checks(tmp_path, monkeypatch):
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_observe = factory.observe_sdk
    synced = []
    actual = log.flush
    def flush(**kwargs):
        actual(**kwargs)
        synced.append(True)
    monkeypatch.setattr(log, "flush", flush)
    assert dispatch(owner, request_for(grant)) == b"observation-ok\n"
    assert synced == [True] and len(observed) == 2
    assert len(observation_events(log)) == 1


def test_peer_drift_after_durable_record_denies_ack_not_an_effect(tmp_path, monkeypatch):
    from herdr.bootstrap_authority import inspect_peer
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_observe = factory.observe_sdk
    peer = inspect_peer(os.getpid())
    values = iter([peer, dataclasses.replace(peer, start_ticks=peer.start_ticks + 1)])
    monkeypatch.setattr("herdr.work_authority.inspect_peer", lambda pid: next(values))
    phase = factory.cycles[next(iter(factory.cycles))][0].phase
    assert dispatch(owner, request_for(grant)) == b"denied\n"
    assert len(observation_events(log)) == 1
    assert factory.cycles[next(iter(factory.cycles))][0].phase is phase


def test_expired_grant_denies_without_observation(tmp_path, monkeypatch):
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_observe = factory.observe_sdk
    monkeypatch.setattr(type(grant), "is_active", lambda self: False)
    raw = log._path.read_bytes()
    assert dispatch(owner, request_for(grant)) == b"denied\n"
    assert log._path.read_bytes() == raw


def test_unknown_started_reservation_and_phase_remain_unchanged(tmp_path):
    from tests.herdr.test_work_budget_configuration import approved_factory
    factory, root, plan, grant, cycle, raw, allocation, quote = approved_factory(tmp_path)
    route = {key: quote[key] for key in ("provider", "model", "api_mode", "base_url")}
    factory.budget_effect(grant.identity, grant.hash, "start", dict(route,
        request_id="observe-unknown", request_sha256="a" * 64, request_bytes=100, output_tokens=100))
    before = factory.budget_authority.snapshot(allocation.allocation_id)
    audit = factory.budget_authority.audit_log._path.read_bytes()
    phase = cycle.phase
    assert before["inflight"] == 1
    factory.observe_sdk(grant.identity, grant.hash, OBS)
    assert factory.budget_authority.snapshot(allocation.allocation_id) == before
    assert factory.budget_authority.audit_log._path.read_bytes() == audit
    assert cycle.phase is phase
    assert not {"delivered", "not_delivered", "pass", "settled"} & observation_events(factory.audit_log)[0].keys()


def test_missing_callback_and_failed_sync_never_ack(tmp_path, monkeypatch):
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    assert dispatch(owner, request_for(grant)) == b"denied\n"
    assert observation_events(log) == []
    host_denials = [row for row in log.replay() if row["event"] == "work_host_denial"]
    assert len(host_denials) == 1 and host_denials[0]["denial"]["operation"] == "work-sdk-observation"
    owner.work_observe = factory.observe_sdk
    monkeypatch.setattr(log, "flush", lambda **kwargs: (_ for _ in ()).throw(OSError("unit sync")))
    assert dispatch(owner, request_for(grant)) == b"denied\n"


def test_lost_ack_short_transport_no_retry_and_durable_duplicate(tmp_path, monkeypatch):
    import herdr.work_authority as transport
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_observe = factory.observe_sdk
    real_verify = owner.launch.mount.verify_mounted
    def verify(pid, sealed):
        real_verify(pid, sealed)
        if len(observed) == 2: time.sleep(.2)
    owner.launch.mount.verify_mounted = verify
    path = tmp_path / "observation.sock"
    monkeypatch.setattr(transport, "SOCKET_PATH", path)
    monkeypatch.setattr(transport, "_SDK_OBSERVATION_TIMEOUT_SECONDS", .05)
    assert transport._WORK_REQUEST_TIMEOUT_SECONDS == 60
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(2); listener.settimeout(2)
    accepted = []
    errors = []
    def serve():
        try:
            for _ in range(2):
                connection, _ = listener.accept()
                accepted.append(True)
                assert dispatch_work_connection(owner, connection)
        except BaseException as error: errors.append(error)
    thread = threading.Thread(target=serve, daemon=True); thread.start()
    client = WorkAuthorityClient()
    began = time.monotonic()
    try:
        assert client.observe(grant.identity, grant.hash, OBS) is False
        assert time.monotonic() - began < .5
        time.sleep(.25)
        assert len(accepted) == 1 and len(observation_events(log)) == 1
        assert client.observe(grant.identity, grant.hash, OBS) is True
        thread.join(2)
        assert not thread.is_alive() and not errors and len(accepted) == 2
        assert len(observation_events(log)) == 1
    finally:
        listener.close(); thread.join(2)


def test_formatter_observation_preserves_original_return_and_uninstalls(monkeypatch):
    module = SimpleNamespace()
    value = object()
    original = lambda error: value
    module.agent_init_failure_message = original
    package = SimpleNamespace(cli_chat_error_copy=module)
    monkeypatch.setitem(sys.modules, "hermes_cli", package)
    events = []
    guard = SimpleNamespace(work_authority=SimpleNamespace(observe=True),
                            observe_sdk=lambda row: events.append(row) or True)
    # Installation requires a callable transport, not a truthy marker.
    guard.work_authority.observe = lambda *args: True
    installation = GuardInstallation(guard)
    _install_sdk_observation_formatter(installation, guard)
    try:
        assert module.agent_init_failure_message(TypeError("unit-secret")) is value
        assert events == [OBS] and "unit-secret" not in json.dumps(events)
        def unavailable(row):
            raise TimeoutError("unit-secret diagnostic failure")
        guard.observe_sdk = unavailable
        assert module.agent_init_failure_message(TypeError("unit-secret")) is value
    finally:
        installation.uninstall()
    assert module.agent_init_failure_message is original


def test_actual_pinned_formatter_fresh_process_no_network_or_credentials(tmp_path):
    sdk = Path("/opt/herdr/releases/p0-5035d92-test/hermes")
    target = sdk / "hermes_cli/cli_chat_error_copy.py"
    if not target.is_file():
        pytest.skip("pinned SDK is not installed on this host")
    script = r"""
import importlib.util,json,socket,sys,types
from pathlib import Path
def denied(*args,**kwargs): raise AssertionError("network is forbidden")
socket.socket.connect=denied
socket.getaddrinfo=denied
sys.path.insert(0,sys.argv[1])
spec=importlib.util.spec_from_file_location("actual_formatter",sys.argv[2])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from herdr.hermes_guard import GuardInstallation,_install_sdk_observation_formatter
events=[]
guard=types.SimpleNamespace(work_authority=types.SimpleNamespace(observe=lambda *a:True),
    observe_sdk=lambda row:events.append(row) or True)
sys.modules["hermes_cli"]=types.SimpleNamespace(cli_chat_error_copy=module)
original=module.agent_init_failure_message
error=TypeError("dummy-api-key-NEVER-IN-AUDIT")
expected=original(error)
installation=GuardInstallation(guard)
_install_sdk_observation_formatter(installation,guard)
try:
    actual=module.agent_init_failure_message(error)
    assert actual==expected and "dummy-api-key-NEVER-IN-AUDIT" in actual
    assert events==[{"phase":"sdk_agent_init","outcome":"failed","error_type":"TypeError"}]
    assert "dummy-api-key" not in json.dumps(events)
finally:installation.uninstall()
assert module.agent_init_failure_message is original
print(json.dumps({"formatter_preserved":True,"metadata_only":True,"network_attempts":0}))
"""
    result = subprocess.run([sys.executable, "-B", "-c", script,
        str(Path(__file__).resolve().parents[2]), str(target)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"formatter_preserved": True, "metadata_only": True,
                                       "network_attempts": 0}


def test_prebootstrap_observation_does_not_get_a_new_authority(tmp_path):
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.launch._published_bootstrap_receipt = None
    owner.work_observe = lambda *args: pytest.fail("unauthenticated callback")
    raw = log._path.read_bytes()
    left, right = socket.socketpair()
    try:
        assert dispatch_work_connection(owner, left) is False
        assert left.fileno() >= 0
        assert log._path.read_bytes() == raw and observed == []
    finally:
        left.close(); right.close()


@pytest.mark.parametrize("fault", ["plan", "grant", "index", "provenance", "extra", "duplicate"])
def test_replay_rejects_tampered_observation_without_reinterpreting_phase(tmp_path, fault):
    from herdr.work_cycle import WorkCycle, WorkContractError
    factory, root, plan, grant, log = prepared(tmp_path)
    factory.observe_sdk(grant.identity, grant.hash, OBS)
    rows = log.replay()
    row = rows[-1]
    if fault == "plan": row["plan_sha256"] = "f" * 64
    if fault == "grant": row["grant_sha256"] = "f" * 64
    if fault == "index": row["observation_index"] = True
    if fault == "provenance": row["provenance"] = "network-attested"
    if fault == "extra": row["secret"] = "unit-only"
    if fault == "duplicate":
        rows.append({**row, "observation_index": 2})
    log._path.write_text("".join(json.dumps(value) + "\n" for value in rows))
    with pytest.raises(WorkContractError):
        WorkCycle(plan, root, log, git=factory.git)


def test_failed_first_directory_sync_is_completed_by_duplicate_without_republish(tmp_path, monkeypatch):
    factory, root, plan, grant, log = prepared(tmp_path)
    owner, observed = owner_for(factory, grant)
    owner.work_observe = factory.observe_sdk
    real_sync = os.fsync
    calls = []
    def fail_directory(fd):
        calls.append(True)
        if len(calls) == 2: raise OSError("unit directory sync")
        return real_sync(fd)
    monkeypatch.setattr(os, "fsync", fail_directory)
    assert dispatch(owner, request_for(grant)) == b"denied\n"
    assert len(observation_events(log)) == 1
    raw, inode = log._path.read_bytes(), log._path.stat().st_ino
    calls.clear()
    monkeypatch.setattr(os, "fsync", lambda fd: (calls.append(True), real_sync(fd))[1])
    assert dispatch(owner, request_for(grant)) == b"observation-ok\n"
    assert len(calls) == 2
    assert log._path.read_bytes() == raw and log._path.stat().st_ino == inode


def test_missing_optional_formatter_preserves_legacy_installation(monkeypatch):
    monkeypatch.setitem(sys.modules, "hermes_cli", SimpleNamespace())
    guard = SimpleNamespace(work_authority=SimpleNamespace(observe=lambda *args: True))
    installation = GuardInstallation(guard)
    _install_sdk_observation_formatter(installation, guard)
    installation.uninstall()
