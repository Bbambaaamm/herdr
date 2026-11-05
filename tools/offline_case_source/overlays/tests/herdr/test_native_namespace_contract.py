"""Data-only native proof contract checks; no namespace or SDK execution."""
import pytest

from herdr.case_roster import NONCE
from herdr.child_ownership import OwnershipError
from herdr.ownership_release import required_namespace_kind
from herdr.scheduler import (AuditLog, CanonicalParentAdmission, ChildProposal,
                             DynamicChildScheduler, SchedulerError)
from herdr.security import InvocationIdentity
from herdr.taskgraph import TaskGraph


def native_scheduler(tmp_path):
    source = {
        "envelope": {"issue": "Bbambaaamm/herdr#190", "spec_hash": "sha256:" + "a" * 64,
            "graph_version": "1.1.0", "created_at": "2026-10-21T00:00:00+00:00",
            "planner": "proof-test", "max_nodes": 2, "max_depth": 2, "max_fanout": 1,
            "policy_profile": "quantlab-paper"},
        "nodes": [{"id": "root-" + NONCE, "parent_id": None, "type": "task",
            "role": "reader", "objective": "Retain admitted root binding",
            "inputs": [], "expected_outputs": [], "dependencies": [], "priority": 1,
            "resource_class": "small", "model_policy": {"provider": "none", "model": "external",
                "fallback_model": None}, "tools": ["read_file", "herdr_submit_result"],
            "permissions": ["repo:read"], "timeout_seconds": 137, "max_attempts": 1}]}
    graph = TaskGraph.parse_planner_output(source)
    identity = InvocationIdentity("github:Bbambaaamm/herdr", "root-agent", "coordinator",
        "coordinator:coordinator", source["nodes"][0]["id"], "root-run", 37)
    def make():
        return DynamicChildScheduler(audit_log=AuditLog(tmp_path / "scheduler.jsonl"),
            clock=lambda: 1000.0, completion_authority=object())
    live = make()
    live.submit(graph, repo="Bbambaaamm/herdr", issue="190")
    descriptor = CanonicalParentAdmission(graph, graph.graph_hash(), identity, "root-key",
        "Bbambaaamm/herdr", "190", "root-pane", "root-marker")
    live.register_external_parent_attempt(task_id=identity.task_id, run_token=identity.run_token,
        idempotency_key="root-key", agent_name=identity.agent_id, pane_id="root-pane",
        marker="root-marker", repo="Bbambaaamm/herdr", issue="190", role="reader",
        tools=("read_file", "herdr_submit_result"), permissions=("repo:read",),
        policy_profile="quantlab-paper", canonical_parent=descriptor)
    proposal = ChildProposal("reader", ("read_file", "herdr_submit_result"), "reader",
        ("read_file",), child_task="Bounded child", child_model="external",
        child_fallback_model=None, parent_permissions=("repo:read",),
        child_permissions=("repo:read",))
    child = live.delegate_child(identity.task_id, identity.run_token, "one", proposal)
    live.dispatch(task_ids={child.id}, managed_start=True)
    rec = live._tasks[child.id]
    marker = "child-" + rec.run_token
    assert live.record_child_pane_intent(rec.id, rec.run_token, rec.agent_id,
        rec.fencing_token, rec.idempotency_key, marker)
    assert live.bind_pre_delivery_pane(rec.id, rec.run_token, rec.agent_id, "child-pane", marker)
    assert required_namespace_kind(live, rec) == "native"
    return live, rec, make


def v2_proof():
    return {"version": 2, "pid": 43, "start_ticks": 101,
        "namespace": "pid:[222]", "init_pid": 42, "init_start_ticks": 100}


def v3_proof():
    return {"version": 3, "kind": "native-preparation-v2", "role": "child",
        "pid": 43, "start_ticks": 101, "namespace": "pid:[222]",
        "init_pid": 43, "init_start_ticks": 101,
        "roster_sha256": "a" * 64, "context_sha256": "b" * 64,
        "runtime_sha256": "c" * 64, "preparer_source_sha256": "d" * 64}


def test_native_record_denies_generic_v2_without_event(tmp_path):
    live, rec, _ = native_scheduler(tmp_path)
    before = len(live.audit_log.replay())
    with pytest.raises(OwnershipError, match="namespace_proof_kind_mismatch"):
        live.record_namespace_lifetime(rec.id, v2_proof())
    assert len(live.audit_log.replay()) == before


def test_native_replay_denies_generic_v2_substitution(tmp_path):
    live, rec, make = native_scheduler(tmp_path)
    live.audit_log.append({"event": "child_namespace_lifetime", "task_id": rec.id,
        "run_token": rec.run_token, "fencing_token": rec.fencing_token,
        "idempotency_key": rec.idempotency_key, "proof": v2_proof()})
    live.audit_log.flush()
    with pytest.raises(OwnershipError, match="namespace_proof_kind_mismatch"):
        make().replay()


def test_native_v3_record_and_replay_keep_admitted_kind(tmp_path, monkeypatch):
    from herdr import native_lifetime
    live, rec, make = native_scheduler(tmp_path)
    proof = v3_proof()
    validated = []
    def checked(value):
        validated.append(value)
        return dict(value)
    monkeypatch.setattr(native_lifetime, "validate_namespace_lifetime", checked)
    live.record_namespace_lifetime(rec.id, proof)
    live.audit_log.flush()
    restored = make()
    restored.replay()
    assert restored._tasks[rec.id].namespace_lifetime == proof
    assert validated == [proof, proof]


@pytest.mark.parametrize("proof", [None, v2_proof()])
def test_native_release_requires_root_closure_without_retirement(tmp_path, monkeypatch, proof):
    from herdr.ownership_release import HostOwnershipRelease
    from herdr.ownership_inventory import LegacyOwnershipInventory
    from herdr.child_evidence import child_identity
    import hashlib
    live, rec, _ = native_scheduler(tmp_path)
    owner = InvocationIdentity.from_dict(live._tasks[rec.parent_task_id].canonical_parent["admission"]["identity"])
    rec.ownership_reservation = "reserved"
    live.audit_log.append({"event": "child_ownership_reserved", "task_id": rec.id,
        "reservation": "reserved", "parent": owner.to_json(), "ownership_sha256": None})
    # The host reader replays real events; the release gate is tested after a
    # data-only terminal cleanup projection, without kernel observations.
    live.audit_log.flush()
    events = live.audit_log.replay()
    directory = tmp_path / "durable-children" / hashlib.sha256(
        f"{owner.task_id}:{owner.run_token}".encode()).hexdigest()
    directory.mkdir(parents=True)
    monkeypatch.setattr(LegacyOwnershipInventory, "_directory", lambda self, fd: None)
    monkeypatch.setattr(LegacyOwnershipInventory, "_events", lambda self, fd: (events, None))
    from herdr import canonical_case_recovery
    calls = []
    def deny(*args):
        calls.append(True)
        raise SchedulerError("root closure unavailable")
    monkeypatch.setattr(canonical_case_recovery, "require_root_release", deny)
    # A real terminal record is produced by replaying a cleanup event below.
    # Reaching the root guard, even with no retirement event, is the property.
    rec.attempt_state = "terminal"
    rec.cleanup_complete = True
    rec.lease = None
    rec.namespace_lifetime = proof
    monkeypatch.setattr(DynamicChildScheduler, "replay", lambda self: self._tasks.update(live._tasks))
    assert HostOwnershipRelease(tmp_path)(child_identity(rec), {"parent": owner.to_json()}) is False
    assert calls == [True]


@pytest.mark.parametrize("proof,expected", [(v2_proof(), False), (v3_proof(), True)])
def test_native_release_requires_v3_after_root_closure(tmp_path, monkeypatch, proof, expected):
    from herdr.ownership_release import HostOwnershipRelease
    from herdr.ownership_inventory import LegacyOwnershipInventory
    from herdr.child_evidence import child_identity
    from herdr import canonical_case_recovery
    from herdr import native_lifetime
    import hashlib
    live, rec, _ = native_scheduler(tmp_path)
    owner = InvocationIdentity.from_dict(live._tasks[rec.parent_task_id].canonical_parent["admission"]["identity"])
    rec.ownership_reservation = "reserved"
    rec.attempt_state = "terminal"
    rec.cleanup_complete = True
    rec.lease = None
    rec.namespace_lifetime = proof
    rec.execution_sandbox_verified = True
    rec.execution_sandbox_attestation = {"sandbox_pid": 43}
    events = [{"event": "child_ownership_reserved", "task_id": rec.id,
        "reservation": "reserved", "parent": owner.to_json(), "ownership_sha256": None}]
    directory = tmp_path / "durable-children" / hashlib.sha256(
        f"{owner.task_id}:{owner.run_token}".encode()).hexdigest()
    directory.mkdir(parents=True)
    monkeypatch.setattr(LegacyOwnershipInventory, "_directory", lambda self, fd: None)
    monkeypatch.setattr(LegacyOwnershipInventory, "_events", lambda self, fd: (events, None))
    monkeypatch.setattr(DynamicChildScheduler, "replay", lambda self: self._tasks.update(live._tasks))
    monkeypatch.setattr(canonical_case_recovery, "require_root_release", lambda *args: {"complete": True})
    monkeypatch.setattr(native_lifetime, "validate_namespace_lifetime", lambda value: dict(value))
    monkeypatch.setattr(native_lifetime, "namespace_exited", lambda value: True)
    assert HostOwnershipRelease(tmp_path)(child_identity(rec), {"parent": owner.to_json()}) is expected


def test_native_retirement_rejects_v2_substitution(tmp_path):
    from herdr.canonical_case_recovery import validate_retirement
    from herdr.child_evidence import child_identity
    live, rec, _ = native_scheduler(tmp_path)
    rec.namespace_lifetime = v2_proof()
    event = {"event": "case_execution_retired", "identity": child_identity(rec).to_json(),
        "idempotency_key": rec.idempotency_key, "binding": {},
        "closure_sha256": "a" * 64,
        "reason": "offline-case-fenced-and-observed-empty"}
    with pytest.raises(OwnershipError, match="namespace_proof_kind_mismatch"):
        validate_retirement(live, event, inspect_root=False)
