"""Typed disposable Work audit + real Unix peers, never physical/native proof.

Mount verification is an explicit component adapter. Native checks, external
connections and all non-Git process launches are tripwired. No factory.prepare,
model, operational allocation/reservation, live queue or SDK is exercised.
"""
import dataclasses
import hashlib
import itertools
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest
from herdr.check_runner import CheckEnvironment, HostCheckRunner
from herdr.evidence import canonical, digest
from herdr.host_work_denial import (describe_denial, validate_denial, validate_denial_events,
    MAX_DENIALS, MAX_FRAMES, OPERATIONS, ERROR_TYPES)
from herdr.security import ToolRule, RiskClass, PolicyDenied
from herdr.work_authority import dispatch_work_connection
from herdr.work_contract_host import HostWorkContractFactory
from herdr.work_cycle import WorkCycle, WorkContractError, require
from tests.herdr.test_security import grant as make_grant
from tests.herdr.test_work_cycle import setup, trusted_git
from tests.herdr.test_work_authority import owner_for

PEER = {"pid": 123, "start_ticks": 456, "exe_device": 1, "exe_inode": 789}
DENIAL = {"operation": "work-verify", "error_type": "WorkContractError",
          "frames": [{"source": "work_cycle", "line": 35}], "peer": PEER}


@pytest.fixture(autouse=True)
def no_effects(monkeypatch):
    def denied(*args, **kwargs): raise AssertionError("component attempted a forbidden effect")
    real_popen = subprocess.Popen
    def local_git_only(args, *a, **kw):
        assert isinstance(args, (list, tuple)) and Path(args[0]).name == "git", "non-Git process forbidden"
        return real_popen(args, *a, **kw)
    monkeypatch.setattr(subprocess, "Popen", local_git_only)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(HostCheckRunner, "__call__", denied)


@pytest.fixture
def prepared(tmp_path):
    _, workspace, template, audit = setup(tmp_path)
    original = make_grant(workspace)
    rule = ToolRule("herdr_verify_work", RiskClass.READ,
        allowed_arg_keys=("request_id", "handoff"), requires_sandbox=True)
    grant = dataclasses.replace(original, identity=template.identity,
        scope=dataclasses.replace(original.scope, tools=(*original.scope.tools, "herdr_verify_work")),
        tool_rules=(*original.tool_rules, rule))
    executable = Path(sys.executable).resolve(strict=True)
    environment = CheckEnvironment("non-executing-host-denial-1",
        ((str(executable), hashlib.sha256(executable.read_bytes()).hexdigest()),), (str(executable),))
    plan = dataclasses.replace(template, grant_sha256=grant.hash, environment_sha256=environment.hash)
    audit.append({"event": "work_plan", "work_cycle": grant.identity.to_json(),
        "plan_sha256": plan.hash, "plan": json.loads(canonical(plan.to_json()))})
    audit.flush()
    def no_approval(**kwargs): pytest.fail("recovery/observation must not request approval")
    factory = HostWorkContractFactory(approve=no_approval, environment=environment,
        storage=tmp_path/"host"/"checks", audit_log=audit, git=trusted_git(workspace))
    factory.recover(identity=grant.identity, workspace=workspace, spec_sha256=plan.spec_sha256,
        grant_sha256=grant.hash, plan_sha256=plan.hash)
    return factory, workspace, plan, grant, audit


def events(audit):
    return [row for row in audit.replay() if row.get("event") == "work_host_denial"]


def request(grant, operation="work-verify"):
    value = {"op": operation, "identity": grant.identity.to_json(), "grant_sha256": grant.hash}
    if operation == "work-verify": value["request_id"] = "component-request"
    if operation == "work-budget": value.update(action="status", payload={})
    if operation == "work-authorize": value.update(kind="provider", tool=None)
    if operation == "work-sdk-observation": value["observation"] = {
        "phase": "sdk_agent_init", "outcome": "failed", "error_type": "TypeError"}
    if operation == "external-knowledge-query": value.update(provider_id="unit", request={})
    return value


def dispatch(owner, value, *, facade=None):
    left, right = socket.socketpair()
    try:
        right.sendall(json.dumps(value).encode() + b"\n")
        result = dispatch_work_connection(owner, left if facade is None else facade(left))
        if result is False: return False
        assert left.fileno() == -1
        return right.recv(128)
    finally: left.close(); right.close()


def test_authenticated_verifier_denial_is_durable_before_original_denial_and_close(prepared, monkeypatch):
    factory, workspace, plan, grant, audit = prepared
    owner, mounts = owner_for(factory, grant)
    def verifier(*a, **kw): require(False, "unit-secret-request-and-key")
    owner.work_verify = verifier
    order = []
    original = audit.flush
    def synced(**kwargs):
        original(**kwargs); order.append("synced")
    monkeypatch.setattr(audit, "flush", synced)
    class Observed:
        def __init__(self, real): self.real = real
        def getsockopt(self, *a): return self.real.getsockopt(*a)
        def settimeout(self, *a): return self.real.settimeout(*a)
        def recv(self, *a): return self.real.recv(*a)
        def sendall(self, value):
            assert value == b"denied\n" and events(audit)
            order.append("denied"); self.real.sendall(value)
        def close(self): order.append("closed"); self.real.close()
    assert dispatch(owner, request(grant), facade=Observed) == b"denied\n"
    assert order == ["synced", "denied", "closed"] and len(mounts) == 1
    row, = events(audit)
    assert row["work_cycle"] == grant.identity.to_json() and row["plan_sha256"] == plan.hash
    assert row["grant_sha256"] == grant.hash and row["denial"]["operation"] == "work-verify"
    assert row["denial"]["error_type"] == "WorkContractError"
    assert any(x["source"] == "work_cycle" for x in row["denial"]["frames"])
    assert "unit-secret" not in audit._path.read_text() and "/dev/shm" not in json.dumps(row["denial"])


@pytest.mark.parametrize("operation", ["work-authorize", "work-budget", "work-verify", "work-sdk-observation"])
def test_recognized_authenticated_operation_denial_is_descriptive(prepared, operation):
    factory, workspace, plan, grant, audit = prepared
    owner, _ = owner_for(factory, grant)
    def denied(*a, **kw): raise TypeError("unit-secret")
    owner.work_budget = owner.work_verify = owner.work_observe = denied
    before = factory.cycles[digest(grant.identity.to_json())][0]
    phase, requests = before.phase, dict(before.verification_requests)
    assert dispatch(owner, request(grant, operation)) == b"denied\n"
    row, = events(audit)
    assert row["denial"]["operation"] == operation
    assert before.phase is phase and before.verification_requests == requests


@pytest.mark.parametrize("fault", ["uid", "pid", "ticks", "exe", "mount", "expired", "identity", "grant",
                                  "unknown_op", "extra", "missing_binding"])
def test_prebinding_or_closed_schema_denial_never_observes(prepared, monkeypatch, fault):
    factory, workspace, plan, grant, audit = prepared
    owner, _ = owner_for(factory, grant)
    value = request(grant)
    owner.work_verify = lambda *a, **kw: pytest.fail("invalid request reached callback")
    if fault == "pid": owner.launch._published_bootstrap_receipt.peer_pid += 1
    if fault == "ticks": owner.launch._published_bootstrap_receipt.process_start_ticks += 1
    if fault == "exe": owner.launch._published_bootstrap_receipt.python_inode += 1
    if fault == "mount": owner.launch.mount.verify_mounted = lambda *a: require(False, "unit-mount")
    if fault == "expired": monkeypatch.setattr(type(grant), "is_active", lambda self: False)
    if fault == "identity": value["identity"]["run_token"] = "foreign"
    if fault == "grant": value["grant_sha256"] = "f"*64
    if fault == "unknown_op": value["op"] = "unit-secret-operation"
    if fault == "extra": value["unit-secret"] = "untrusted-payload"
    if fault == "missing_binding": value.pop("identity")
    class Foreign:
        def __init__(self, real): self.real = real
        def getsockopt(self, *a): return struct.pack("3i", os.getpid(), os.geteuid()+1, os.getegid())
        def close(self): pytest.fail("foreign connection ownership changed")
    raw = audit._path.read_bytes()
    result = dispatch(owner, value, facade=Foreign if fault == "uid" else None)
    assert result is False if fault in {"uid", "pid"} else result == b"denied\n"
    assert audit._path.read_bytes() == raw


@pytest.mark.parametrize("fault", ["peer", "mount", "expired", "grant_object", "identity"])
def test_postcallback_peer_exit_or_grant_drift_keeps_earlier_authenticated_failure(prepared, monkeypatch, fault):
    factory, workspace, plan, grant, audit = prepared
    owner, mounts = owner_for(factory, grant)
    import herdr.work_authority as module
    original_peer = module.inspect_peer(os.getpid())
    active = [True]
    monkeypatch.setattr(type(grant), "is_active", lambda self, *args: active[0])
    def verifier(*a, **kw):
        if fault == "peer": monkeypatch.setattr(module, "inspect_peer", lambda pid: dataclasses.replace(original_peer, start_ticks=original_peer.start_ticks+1))
        if fault == "mount": owner.launch.mount.verify_mounted = lambda *a: require(False, "unit-mount")
        if fault == "expired": active[0] = False
        if fault == "grant_object": owner.launch.grant = dataclasses.replace(grant)
        if fault == "identity": owner.launch.identity = dataclasses.replace(grant.identity, run_token="foreign")
        raise TypeError("unit-secret")
    owner.work_verify = verifier
    original_peer_metadata = {key: getattr(original_peer, key) for key in PEER}
    original_identity, original_grant_hash = grant.identity.to_json(), grant.hash
    assert dispatch(owner, request(grant)) == b"denied\n"
    row, = events(audit)
    assert row["denial"]["error_type"] == "TypeError"
    assert row["denial"]["peer"] == original_peer_metadata
    assert row["work_cycle"] == original_identity and row["grant_sha256"] == original_grant_hash
    assert row["provenance"] == "host_authenticated_request"


@pytest.mark.parametrize("fault", ["append", "flush", "observer"])
def test_failed_observation_keeps_original_denial_and_connection_close(prepared, monkeypatch, fault):
    factory, workspace, plan, grant, audit = prepared
    owner, _ = owner_for(factory, grant)
    def verifier(*a, **kw): raise TypeError("original-unit-secret")
    owner.work_verify = verifier
    def unavailable(*a, **kw): raise SystemExit("observer-unit-secret")
    monkeypatch.setattr(audit if fault != "observer" else factory,
        fault if fault != "observer" else "observe_host_denial", unavailable)
    assert dispatch(owner, request(grant)) == b"denied\n"


def test_historical_callback_port_is_not_rejected_or_observed(prepared):
    factory, workspace, plan, grant, audit = prepared
    owner, _ = owner_for(factory, grant)
    owner.work_authority = lambda *a, **kw: True
    def verifier(*a, **kw): raise TypeError("legacy unit-secret")
    owner.work_verify = verifier
    raw = audit._path.read_bytes()
    assert dispatch(owner, request(grant)) == b"denied\n" and audit._path.read_bytes() == raw


def test_busy_factory_lock_does_not_delay_denial(prepared):
    factory, workspace, plan, grant, audit = prepared
    owner, _ = owner_for(factory, grant)
    entered, release = threading.Event(), threading.Event()
    def hold():
        with factory._lock:
            entered.set(); release.wait(2)
    thread = threading.Thread(target=hold); thread.start()
    assert entered.wait(1)
    def verifier(*a, **kw): raise TypeError("unit-secret")
    owner.work_verify = verifier
    began = time.monotonic()
    try:
        assert dispatch(owner, request(grant)) == b"denied\n"
        assert time.monotonic()-began < .5 and events(audit) == []
    finally: release.set(); thread.join(2)
    assert not thread.is_alive()


def test_exact_classes_and_actual_project_codes_only_no_exception_text_or_spoofed_path():
    class Secret(Exception):
        def __str__(self): pytest.fail("exception text read")
        def __getattribute__(self, name):
            if name in {"args", "__traceback__"}: pytest.fail("custom exception attribute read")
            return super().__getattribute__(name)
    import herdr.work_handoff as actual
    space = {}
    exec(compile("def fake():\n raise Secret('unit-secret')\n", actual.__file__, "exec"), {"Secret": Secret}, space)
    try: space["fake"]()
    except Secret as error: value = describe_denial("work-verify", error, SimpleNamespace(**PEER))
    assert value == {"operation": "work-verify", "error_type": "UnknownError", "frames": [], "peer": PEER}
    try: require(False, "unit-secret")
    except WorkContractError as error: value = describe_denial("work-verify", error, SimpleNamespace(**PEER))
    assert value["error_type"] == "WorkContractError" and value["frames"] == [{"source": "work_cycle", "line": 35}]
    assert "unit-secret" not in json.dumps(value)


@pytest.mark.parametrize("bad", [None, {}, {**DENIAL, "message": "unit-secret"},
    {**DENIAL, "operation": "unknown"}, {**DENIAL, "error_type": "unit-secret"},
    {**DENIAL, "frames": [{"source": "/secret/path", "line": 1}]},
    {**DENIAL, "frames": [{"source": "work_cycle", "line": True}]},
    {**DENIAL, "frames": [{"source": "work_cycle", "line": 0}]},
    {**DENIAL, "frames": [*DENIAL["frames"]]*(MAX_FRAMES+1)},
    {**DENIAL, "peer": {**PEER, "pid": True}}, {**DENIAL, "peer": {**PEER, "exe_inode": 0}},
    {**DENIAL, "peer": {**PEER, "path": "/unit-secret"}}])
def test_closed_denial_schema(bad):
    with pytest.raises(ValueError): validate_denial(bad)


def restore(factory, workspace, plan, grant):
    result = HostWorkContractFactory(approve=factory.approve, environment=factory.environment,
        storage=factory.storage, audit_log=factory.audit_log, git=factory.git)
    cycle = result.recover(identity=grant.identity, workspace=workspace, spec_sha256=plan.spec_sha256,
        grant_sha256=grant.hash, plan_sha256=plan.hash)
    return result, cycle


def test_existing_audit_dedup_sync_recover_and_no_phase_budget_or_retry_effect(prepared, monkeypatch):
    factory, workspace, plan, grant, audit = prepared
    def effect(*a, **kw): pytest.fail("observation attempted refresh/budget/approval")
    monkeypatch.setattr(factory, "_refresh", effect)
    class NoBudget:
        def __getattribute__(self, name): return effect()
    factory.budget_authority = NoBudget()
    before = factory.cycles[digest(grant.identity.to_json())][0]
    phase, requests = before.phase, dict(before.verification_requests)
    syncs, actual = [], audit.flush
    def synced(**kwargs): actual(**kwargs); syncs.append(kwargs)
    monkeypatch.setattr(audit, "flush", synced)
    assert factory.observe_host_denial(grant.identity, grant.hash, DENIAL)
    raw = audit._path.read_bytes()
    copied = validate_denial(DENIAL); copied["frames"][0]["line"] = 99
    assert events(audit)[0]["denial"] == DENIAL
    assert factory.observe_host_denial(grant.identity, grant.hash, dict(DENIAL))
    restored, cycle = restore(factory, workspace, plan, grant)
    assert restored.observe_host_denial(grant.identity, grant.hash, DENIAL)
    assert audit._path.read_bytes() == raw and len(events(audit)) == 1
    assert syncs == [{"sync_existing": True}]*3
    assert before.phase is phase and before.verification_requests == requests and cycle.phase is phase


def test_limit_survives_restart_but_existing_record_still_syncs(prepared):
    factory, workspace, plan, grant, audit = prepared
    values = [{"operation": op, "error_type": kind, "frames": [], "peer": PEER}
        for op, kind in itertools.product(sorted(OPERATIONS), sorted(ERROR_TYPES))]
    for value in values[:MAX_DENIALS]: assert factory.observe_host_denial(grant.identity, grant.hash, value)
    restored, _ = restore(factory, workspace, plan, grant)
    raw = audit._path.read_bytes()
    assert restored.observe_host_denial(grant.identity, grant.hash, values[0])
    with pytest.raises(WorkContractError, match="limit reached"):
        restored.observe_host_denial(grant.identity, grant.hash, values[MAX_DENIALS])
    assert audit._path.read_bytes() == raw and len(events(audit)) == MAX_DENIALS


@pytest.mark.parametrize("fault", ["identity", "grant"])
def test_factory_binding_denies_before_append(prepared, fault):
    factory, workspace, plan, grant, audit = prepared
    raw = audit._path.read_bytes()
    identity = dataclasses.replace(grant.identity, run_token="foreign") if fault == "identity" else grant.identity
    with pytest.raises(WorkContractError):
        factory.observe_host_denial(identity, "f"*64 if fault == "grant" else grant.hash, DENIAL)
    assert audit._path.read_bytes() == raw


@pytest.mark.parametrize("fault", ["plan", "grant", "index", "provenance", "extra", "frame", "duplicate", "overflow"])
def test_cold_replay_rejects_malformed_or_over_limit_host_metadata(prepared, fault):
    factory, workspace, plan, grant, audit = prepared
    factory.observe_host_denial(grant.identity, grant.hash, DENIAL)
    rows = audit.replay(); row = rows[-1]
    if fault == "plan": row["plan_sha256"] = "f"*64
    if fault == "grant": row["grant_sha256"] = "f"*64
    if fault == "index": row["denial_index"] = True
    if fault == "provenance": row["provenance"] = "PASS"
    if fault == "extra": row["secret"] = "unit-secret"
    if fault == "frame": row["denial"]["frames"][0]["source"] = "/unit-secret/path"
    if fault == "duplicate": rows.append({**row, "denial_index": 2})
    if fault == "overflow":
        for index in range(2, MAX_DENIALS+2):
            rows.append({**row, "denial_index": index, "denial": {**DENIAL,
                "frames": [{"source": "work_cycle", "line": index}]}})
    audit._path.write_text("".join(json.dumps(value)+"\n" for value in rows))
    with pytest.raises(WorkContractError): WorkCycle(plan, workspace, audit, git=factory.git)


def test_failed_directory_sync_duplicate_completes_durability_without_republish(prepared, monkeypatch):
    factory, workspace, plan, grant, audit = prepared
    original, calls = os.fsync, []
    def fail_directory(fd):
        calls.append(True)
        if len(calls) == 2: raise OSError("unit directory sync")
        return original(fd)
    monkeypatch.setattr(os, "fsync", fail_directory)
    with pytest.raises(OSError): factory.observe_host_denial(grant.identity, grant.hash, DENIAL)
    raw, inode = audit._path.read_bytes(), audit._path.stat().st_ino
    calls.clear()
    monkeypatch.setattr(os, "fsync", lambda fd: (calls.append(True), original(fd))[1])
    assert factory.observe_host_denial(grant.identity, grant.hash, DENIAL)
    assert len(calls) == 2 and audit._path.read_bytes() == raw and audit._path.stat().st_ino == inode


def test_existing_deadline_not_extended_to_record_diagnostic(prepared, monkeypatch):
    factory, workspace, plan, grant, audit = prepared
    import herdr.work_lifetime as lifetime
    token = lifetime._DEADLINE.set(time.monotonic()-1)
    raw = audit._path.read_bytes()
    try:
        with pytest.raises(WorkContractError): factory.observe_host_denial(grant.identity, grant.hash, DENIAL)
    finally: lifetime._DEADLINE.reset(token)
    assert audit._path.read_bytes() == raw


def test_unknown_exception_metaclass_hash_and_equality_are_never_invoked():
    called = []
    class HostileType(type):
        def __hash__(cls): called.append("hash"); raise AssertionError("custom hash invoked")
        def __eq__(cls, other): called.append("eq"); raise AssertionError("custom equality invoked")
    class Secret(Exception, metaclass=HostileType):
        def __str__(self): raise AssertionError("exception text read")
    error = Secret("unit-secret")
    value = describe_denial("work-verify", error, SimpleNamespace(**PEER))
    assert value == {"operation": "work-verify", "error_type": "UnknownError", "frames": [], "peer": PEER}
    assert called == []


def test_unknown_exception_traceback_property_is_never_invoked():
    called = []
    class Secret(Exception):
        @property
        def __traceback__(self): called.append("property"); raise AssertionError("custom property invoked")
        def __getattribute__(self, name):
            if name == "__traceback__": called.append("getattribute"); raise AssertionError("custom getter invoked")
            return super().__getattribute__(name)
    error = Secret("unit-secret")
    value = describe_denial("work-verify", error, SimpleNamespace(**PEER))
    assert value == {"operation": "work-verify", "error_type": "UnknownError", "frames": [], "peer": PEER}
    assert called == []
