"""Canonical host-data binding only; disposable actual scheduler journals, no execution."""
import copy
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent-stack/bin"))
import agent_durable_children as children
import herdr.scheduler as scheduling
from herdr.scheduler import AuditLog, DynamicChildScheduler, SchedulerBudget, SchedulerError
from herdr.security import InvocationIdentity
from herdr.taskgraph import LifecycleState, TaskGraph


def graph():
    return TaskGraph.parse_planner_output({
        "envelope": {"issue": "Bbambaaamm/herdr#9", "spec_hash": "sha256:" + "a" * 64,
            "graph_version": "1.1.0", "created_at": "2026-10-21T00:00:00+00:00",
            "planner": "host-data-test", "max_nodes": 3, "max_depth": 2, "max_fanout": 1,
            "policy_profile": "quantlab-paper"},
        "nodes": [{"id": "root", "parent_id": None, "type": "task", "role": "reader",
            "objective": "Preserve the canonical root rather than replacing it",
            "inputs": [{"artifact_ref": "public", "nested": {"a": [1, None, True]}}],
            "expected_outputs": [{"kind": "evidence", "nested": ["exact"]}],
            "dependencies": [], "priority": 7, "resource_class": "small",
            "model_policy": {"provider": "none", "model": "external", "fallback_model": None},
            "tools": ["read_file", "herdr_submit_result"], "permissions": ["repo:read"],
            "timeout_seconds": 137, "max_attempts": 2}]})


def identity():
    return InvocationIdentity(consumer="github:Bbambaaamm/herdr", agent_id="ordinary-agent",
        parent_agent_id="coordinator", parent_task_id="coordinator:coordinator",
        task_id="root", run_token="ordinary-run", fencing_token=37)


def binding():
    return dict(task_id="root", run_token="ordinary-run", idempotency_key="ordinary-key",
        agent_name="ordinary-agent", pane_id="ordinary-pane", marker="ordinary-marker",
        repo="Bbambaaamm/herdr", issue="9", role="reader",
        tools=("read_file", "herdr_submit_result"), permissions=("repo:read",),
        policy_profile="quantlab-paper")


def descriptor(**changes):
    g = graph()
    values = dict(graph=g, graph_sha256=g.graph_hash(), identity=identity(),
        idempotency_key="ordinary-key", repo="Bbambaaamm/herdr", issue="9",
        pane_id="ordinary-pane", marker="ordinary-marker")
    values.update(changes)
    return scheduling.CanonicalParentAdmission(**values)


def scheduler(path, maximum=8):
    return DynamicChildScheduler(audit_log=AuditLog(path), clock=lambda: 1000.0,
        budget=SchedulerBudget(max_global_concurrency=2, max_per_repo=2, max_per_issue=2,
            max_dag_nodes=maximum, max_dag_depth=8, max_dag_fanout=8),
        completion_authority=object())


def submitted(tmp_path):
    live = scheduler(tmp_path / "scheduler.jsonl")
    live.submit(graph(), repo="Bbambaaamm/herdr", issue="9")
    live.audit_log.flush()
    return live


def test_canonical_pending_root_adopts_actual_ordinary_identity_without_replacement(tmp_path):
    live = submitted(tmp_path)
    before = live._tasks["root"].node.to_json()
    # On the unchanged baseline, use its real old API to reproduce its
    # external-parent-attempt-mismatch. No fake binding or private mutation.
    arguments = {} if not hasattr(scheduling, "CanonicalParentAdmission") else {
        "canonical_parent": descriptor()}
    rec = live.register_external_parent_attempt(**binding(), **arguments)
    assert rec.node.to_json() == before
    assert rec.state is LifecycleState.RUNNING
    assert (rec.run_token, rec.idempotency_key, rec.fencing_token) == (
        "ordinary-run", "ordinary-key", 37)
    assert rec.parent_task_id is None and rec.parent_agent_id is None
    assert rec.canonical_parent["admission"]["identity"] == identity().to_json()
    assert [e["event"] for e in live.audit_log.replay()] == [
        "submit", "graph_submit", "claim", "execution_session_bound"]


def adopt(live, **changes):
    arguments = binding()
    arguments.update(changes)
    return live.register_external_parent_attempt(canonical_parent=descriptor(), **arguments)


def cold(live):
    live.audit_log.flush()
    restored = scheduler(live.audit_log._path)
    restored.replay()
    return restored


def test_actual_cold_replay_preserves_node_graph_caps_identity_and_session(tmp_path):
    live = submitted(tmp_path)
    rec = adopt(live)
    restored = cold(live)
    after = restored._tasks["root"]
    assert after.node.to_json() == graph().nodes[0].to_json()
    assert after.node.model_policy["fallback_model"] is None
    assert after.canonical_parent == rec.canonical_parent
    assert after.canonical_parent["admission"]["identity"] == identity().to_json()
    assert (after.lease, after.run_token, after.idempotency_key, after.fencing_token,
        after.execution_agent, after.execution_pane, after.execution_marker) == (
        rec.lease, "ordinary-run", "ordinary-key", 37, "ordinary-agent", "ordinary-pane", "ordinary-marker")
    assert after.parent_task_id is after.parent_agent_id is None
    assert (restored._plan_max_nodes, restored._plan_max_depth, restored._plan_max_fanout) == (3, 2, 1)


@pytest.mark.parametrize("restore", [False, True])
def test_exact_repeat_never_appends_another_claim_or_session(tmp_path, restore):
    live = submitted(tmp_path)
    adopt(live)
    if restore:
        live = cold(live)
    before = live.audit_log._path.read_bytes()
    result = adopt(live)
    assert result is live._tasks["root"]
    assert live.audit_log._path.read_bytes() == before
    assert len([e for e in live.audit_log.replay() if e["event"] == "claim"]) == 1


def test_actual_fence_replaces_planning_lease_without_dispatch_or_new_fence(tmp_path, monkeypatch):
    live = submitted(tmp_path)
    planned = live._tasks["root"].lease
    assert planned.agent_id != identity().agent_id and planned.fencing_token != 37
    def forbidden(*args, **kwargs):
        pytest.fail("adoption cannot dispatch or allocate another fence")
    monkeypatch.setattr(live, "dispatch", forbidden)
    monkeypatch.setattr(live, "_next_fencing_token", forbidden)
    rec = adopt(live)
    assert rec.lease.holder == "external" and rec.lease.fencing_token == 37
    assert live._next_fencing_token_value >= 38
    assert cold(live)._next_fencing_token_value >= 38


@pytest.mark.parametrize("field,value", [
    ("task_id", "foreign"), ("run_token", "foreign"), ("idempotency_key", "foreign"),
    ("agent_name", "foreign"), ("pane_id", "foreign"), ("marker", "foreign"),
    ("repo", "foreign/repo"), ("issue", "10"), ("role", "writer"),
    ("tools", ("read_file",)), ("permissions", ("workspace-write",)),
    ("policy_profile", "foreign")])
def test_request_drift_denied_before_mutation(tmp_path, field, value):
    live = submitted(tmp_path)
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError):
        adopt(live, **{field: value})
    assert live.audit_log._path.read_bytes() == before
    assert live._tasks["root"].state is LifecycleState.PENDING


@pytest.mark.parametrize("field,value", [
    ("consumer", "github:foreign/repo"), ("task_id", "foreign"),
    ("run_token", "other-run"), ("fencing_token", 38), ("agent_id", "other-agent"),
    ("parent_agent_id", "other-coordinator"), ("parent_task_id", "coordinator:other")])
def test_identity_drift_denied_after_actual_replay(tmp_path, field, value):
    live = submitted(tmp_path)
    adopt(live)
    live = cold(live)
    changed = replace(identity(), **{field: value})
    parent = descriptor(identity=changed)
    request = binding()
    request.update(task_id=changed.task_id, run_token=changed.run_token, agent_name=changed.agent_id)
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError):
        live.register_external_parent_attempt(canonical_parent=parent, **request)
    assert live.audit_log._path.read_bytes() == before


@pytest.mark.parametrize("change", ["key", "pane", "marker", "node", "envelope", "digest"])
def test_canonical_descriptor_drift_rejected_on_repeat(tmp_path, change):
    live = submitted(tmp_path)
    adopt(live)
    live = cold(live)
    request = binding()
    if change in {"key", "pane", "marker"}:
        field = {"key": "idempotency_key", "pane": "pane_id", "marker": "marker"}[change]
        parent = descriptor(**{field: "different"})
        request[field] = "different"
    elif change == "digest":
        parent = descriptor(graph_sha256="0" * 64)
    else:
        raw = descriptor().to_json()["graph"]
        if change == "node":
            raw["nodes"][0]["inputs"][0]["nested"]["a"].append("different")
        else:
            raw["envelope"]["max_nodes"] = 4
        g = TaskGraph.parse_planner_output(raw)
        parent = descriptor(graph=g, graph_sha256=g.graph_hash())
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError):
        live.register_external_parent_attempt(canonical_parent=parent, **request)
    assert live.audit_log._path.read_bytes() == before


@pytest.mark.parametrize("value", [None, {}, "approval", object()])
def test_present_untyped_canonical_mode_never_falls_back_to_legacy(tmp_path, value):
    live = submitted(tmp_path)
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError):
        live.register_external_parent_attempt(canonical_parent=value, **binding())
    assert live.audit_log._path.read_bytes() == before


def test_descriptor_recomputes_hash_after_mutable_graph_reference_changes(tmp_path):
    live = submitted(tmp_path)
    parent = descriptor()
    parent.graph.envelope = replace(parent.graph.envelope, max_nodes=4)
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError, match="digest"):
        live.register_external_parent_attempt(canonical_parent=parent, **binding())
    assert live.audit_log._path.read_bytes() == before


def test_no_canonical_mode_can_reinterpret_legacy_external_node(tmp_path):
    live = scheduler(tmp_path / "scheduler.jsonl")
    live.register_external_parent_attempt(**binding())
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError):
        adopt(live)
    assert live.audit_log._path.read_bytes() == before


def test_already_dispatched_root_cannot_be_adopted(tmp_path):
    live = submitted(tmp_path)
    live.dispatch(task_ids={"root"})
    live.audit_log.flush()
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError):
        adopt(live)
    assert live.audit_log._path.read_bytes() == before


def rewrite(live, change):
    events = live.audit_log.replay()
    change(events)
    live.audit_log._path.write_text("".join(json.dumps(e) + "\n" for e in events))


@pytest.mark.parametrize("fault", ["null", "unknown", "bool_limit", "missing_limit", "digest",
    "identity_fence", "claim_run", "claim_key", "claim_fence", "claim_agent", "claim_holder",
    "claim_status", "lease_nan", "session_run", "session_agent", "session_pane", "session_marker",
    "missing_session", "graph_hash", "graph_caps", "node", "repeat_claim", "outside_claim"])
def test_present_canonical_journal_drift_fails_closed(tmp_path, fault):
    live = submitted(tmp_path)
    adopt(live)
    def change(events):
        claim = events[2]
        payload = claim["canonical_parent"]
        if fault == "null": claim["canonical_parent"] = None
        elif fault == "unknown": payload["unexpected"] = True
        elif fault == "bool_limit": payload["limits"]["max_nodes"] = True
        elif fault == "missing_limit": del payload["limits"]["max_nodes"]
        elif fault == "digest": payload["admission"]["graph_sha256"] = "0" * 64
        elif fault == "identity_fence": payload["admission"]["identity"]["fencing_token"] = 38
        elif fault == "lease_nan": claim["lease_until"] = float("nan")
        elif fault.startswith("claim_"):
            key = {"claim_run": "run_token", "claim_key": "idempotency_key", "claim_fence": "fencing_token",
                "claim_agent": "agent_id", "claim_holder": "holder", "claim_status": "attempt_state"}[fault]
            claim[key] = 38 if key == "fencing_token" else "foreign"
        elif fault.startswith("session_"):
            key = {"session_run": "run_token", "session_agent": "agent_name", "session_pane": "pane_id",
                "session_marker": "marker"}[fault]
            events[3][key] = "foreign"
        elif fault == "missing_session": events.pop()
        elif fault == "graph_hash": events[1]["graph_hash"] = "0" * 64
        elif fault == "graph_caps": events[1]["max_nodes"] = 4
        elif fault == "node": events[0]["inputs"][0]["nested"]["a"].append("foreign")
        elif fault == "repeat_claim": events.insert(3, copy.deepcopy(claim))
        elif fault == "outside_claim": events[3]["canonical_parent"] = payload
    rewrite(live, change)
    with pytest.raises((SchedulerError, ValueError, TypeError)):
        cold(live)


def initialized(tmp_path, monkeypatch=None, phase=None):
    directory = children.ensure_attempt_directory(tmp_path, "root", "ordinary-run")
    with children.parent_attempt_guard(tmp_path, "root", "ordinary-run"):
        result = children.initialize_parent_scheduler(directory,
            completion_authority=object(), canonical_parent=descriptor(), **binding())
    return directory, result


def test_canonical_initializer_stages_real_graph_and_exact_existing_claim(tmp_path):
    directory, live = initialized(tmp_path)
    events = live.audit_log.replay()
    assert [e["event"] for e in events] == ["submit", "graph_submit", "claim", "execution_session_bound"]
    document = json.loads((directory / children.INITIALIZATION).read_text())
    assert document["state"] == "committed" and "ledger" not in document
    assert document["canonical_parent"] == live._tasks["root"].canonical_parent
    restored = cold(live)
    assert restored._tasks["root"].node.to_json() == graph().nodes[0].to_json()
    assert restored._tasks["root"].canonical_parent == document["canonical_parent"]
    before = live.audit_log._path.read_bytes()
    assert adopt(restored).fencing_token == 37
    assert live.audit_log._path.read_bytes() == before


@pytest.mark.parametrize("phase", ["pending", "ledger", "sentinel", "committed"])
def test_canonical_initialization_recovers_exact_publication_crash(tmp_path, monkeypatch, phase):
    directory = children.ensure_attempt_directory(tmp_path, "root", "ordinary-run")
    atomic, mark = children._atomic_control_file, children.mark_ledger_required
    def crash_atomic(path, raw):
        atomic(path, raw)
        state = json.loads(raw).get("state") if path.name == children.INITIALIZATION else None
        if (phase == "pending" and state == "pending" or phase == "ledger" and path.name == "scheduler.jsonl"
                or phase == "committed" and state == "committed"):
            raise SystemExit("disposable crash after durable publication")
    def crash_mark(path):
        mark(path)
        if phase == "sentinel":
            raise SystemExit("disposable crash after sentinel")
    with monkeypatch.context() as patch:
        patch.setattr(children, "_atomic_control_file", crash_atomic)
        patch.setattr(children, "mark_ledger_required", crash_mark)
        with pytest.raises(SystemExit):
            initialized(tmp_path)
    with children.parent_attempt_guard(tmp_path, "root", "ordinary-run"):
        pass
    live = scheduler(directory / "scheduler.jsonl")
    live.replay()
    assert live._tasks["root"].fencing_token == 37
    assert live._tasks["root"].canonical_parent["admission"]["identity"] == identity().to_json()
    assert len([e for e in live.audit_log.replay() if e["event"] == "claim"]) == 1
    assert json.loads((directory / children.INITIALIZATION).read_text())["state"] == "committed"


@pytest.mark.parametrize("artifact", ["scheduler.jsonl", "scheduler.required"])
def test_committed_canonical_initialization_does_not_recreate_lost_artifact(tmp_path, artifact):
    directory, live = initialized(tmp_path)
    (directory / artifact).unlink()
    with children.parent_attempt_guard(tmp_path, "root", "ordinary-run", reconcile_results=True) as terminal:
        assert not terminal
    assert not (directory / artifact).exists()


@pytest.mark.parametrize("fault", ["wrong_run", "ledger_digest", "extra_event", "canonical_null",
    "canonical_graph", "canonical_identity", "claim_identity"])
def test_pending_canonical_initialization_conflict_never_overwrites_ledger(tmp_path, monkeypatch, fault):
    directory = children.ensure_attempt_directory(tmp_path, "root", "ordinary-run")
    atomic = children._atomic_control_file
    def crash(path, raw):
        atomic(path, raw)
        if path.name == "scheduler.jsonl":
            raise SystemExit("disposable crash before sentinel")
    with monkeypatch.context() as patch:
        patch.setattr(children, "_atomic_control_file", crash)
        with pytest.raises(SystemExit):
            initialized(tmp_path)
    path = directory / children.INITIALIZATION
    doc = json.loads(path.read_text())
    if fault == "wrong_run": doc["run_token"] = "different"
    elif fault == "ledger_digest": doc["ledger_sha256"] = "different"
    elif fault == "extra_event":
        with (directory / "scheduler.jsonl").open("a") as h: h.write('{"event":"foreign"}\n')
    elif fault == "canonical_null": doc["canonical_parent"] = None
    elif fault == "canonical_graph": doc["canonical_parent"]["admission"]["graph_sha256"] = "0" * 64
    elif fault == "canonical_identity": doc["canonical_parent"]["admission"]["identity"]["parent_agent_id"] = "foreign"
    elif fault == "claim_identity":
        events = [json.loads(row) for row in doc["ledger"].splitlines()]
        events[2]["fencing_token"] = 38
        doc["ledger"] = "".join(json.dumps(e) + "\n" for e in events)
        import hashlib
        doc["ledger_sha256"] = hashlib.sha256(doc["ledger"].encode()).hexdigest()
    path.write_text(json.dumps(doc))
    before = (directory / "scheduler.jsonl").read_bytes()
    with pytest.raises((SchedulerError, ValueError, TypeError)):
        with children.parent_attempt_guard(tmp_path, "root", "ordinary-run"):
            pass
    assert (directory / "scheduler.jsonl").read_bytes() == before
    assert not children.ledger_required(directory)


def test_n_node_graph_denied_without_truncation_or_publication(tmp_path):
    raw = descriptor().to_json()["graph"]
    extra = copy.deepcopy(raw["nodes"][0])
    extra.update(id="child", parent_id="root", dependencies=["root"])
    raw["nodes"].append(extra)
    g = TaskGraph.parse_planner_output(raw)
    parent = descriptor(graph=g, graph_sha256=g.graph_hash())
    directory = children.ensure_attempt_directory(tmp_path, "root", "ordinary-run")
    with pytest.raises(SchedulerError, match="exactly one root"):
        with children.parent_attempt_guard(tmp_path, "root", "ordinary-run"):
            children.initialize_parent_scheduler(directory,
                completion_authority=object(), canonical_parent=parent, **binding())
    assert not any((directory / name).exists() for name in
        ("scheduler.jsonl", "scheduler.required", children.INITIALIZATION))
    assert len(g.nodes) == 2


def test_data_only_binding_does_not_activate_execution_or_budget(tmp_path, monkeypatch):
    import subprocess
    from herdr.work_budget import WorkBudgetAuthority
    def forbidden(*args, **kwargs):
        pytest.fail("canonical binding cannot start native/provider or budget work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(WorkBudgetAuthority, "__init__", forbidden)
    directory, live = initialized(tmp_path)
    assert cold(live)._tasks["root"].run_token == "ordinary-run"


@pytest.mark.parametrize("fault", ["identity_missing", "identity_bool_fence", "identity_zero_fence",
    "identity_unknown", "graph_unknown", "version_bool"])
def test_closed_canonical_identity_payload_cannot_fall_back(tmp_path, fault):
    live = submitted(tmp_path)
    adopt(live)
    def change(events):
        data = events[2]["canonical_parent"]["admission"]
        if fault == "identity_missing": del data["identity"]["parent_task_id"]
        elif fault == "identity_bool_fence": data["identity"]["fencing_token"] = True
        elif fault == "identity_zero_fence": data["identity"]["fencing_token"] = 0
        elif fault == "identity_unknown": data["identity"]["extra"] = "unknown"
        elif fault == "graph_unknown": data["graph"]["extra"] = "unknown"
        elif fault == "version_bool": data["version"] = True
    rewrite(live, change)
    with pytest.raises(SchedulerError):
        cold(live)


@pytest.mark.parametrize("fault", ["removed_mode", "changed_parent", "changed_caps", "extra_prefix"])
def test_committed_canonical_prefix_cannot_be_reinterpreted_as_legacy(tmp_path, fault):
    directory, live = initialized(tmp_path)
    def change(events):
        if fault == "removed_mode": del events[2]["canonical_parent"]
        elif fault == "changed_parent":
            events[2]["canonical_parent"]["admission"]["identity"]["parent_task_id"] = "foreign"
        elif fault == "changed_caps": events[1]["max_nodes"] = 2
        else: events.insert(0, {"event": "foreign"})
    rewrite(live, change)
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError, match="prefix"):
        with children.parent_attempt_guard(tmp_path, "root", "ordinary-run"):
            pass
    assert live.audit_log._path.read_bytes() == before


def test_committed_prefix_validation_is_bounded_and_allows_child_journal_growth(tmp_path):
    directory, live = initialized(tmp_path)
    # This is only the control-prefix reader test. The tail is not claimed to
    # be a valid scheduler history or accepted child result.
    with live.audit_log._path.open("ab") as handle:
        handle.write(b"x" * (children.MAX_INITIALIZATION_BYTES + 1))
    doc = children._initialization(directory, "root", "ordinary-run")
    assert doc["state"] == "committed"
    assert len(children._canonical_initial_prefix(directory)) < children.MAX_INITIALIZATION_BYTES


@pytest.mark.parametrize("field", ["idempotency_key", "pane_id", "marker"])
@pytest.mark.parametrize("control", ["\x00", "\n", "\x7f", "\x85"])
def test_canonical_only_strings_reject_controls(field, control):
    parent = descriptor(**{field: "host" + control + "data"})
    with pytest.raises(SchedulerError):
        parent.to_json()


@pytest.mark.parametrize("field,value", [("schema", True), ("ledger_sha256", "A" * 64),
    ("ledger_sha256", "0" * 63), ("ledger_sha256", "not-a-digest")])
def test_canonical_committed_wrapper_is_typed_before_ledger_read(tmp_path, monkeypatch, field, value):
    directory, _ = initialized(tmp_path)
    path = directory / children.INITIALIZATION
    doc = json.loads(path.read_text())
    doc[field] = value
    path.write_text(json.dumps(doc))
    def forbidden(*args):
        pytest.fail("malformed canonical wrapper must fail before reading ledger")
    monkeypatch.setattr(children, "_canonical_initial_prefix", forbidden)
    with pytest.raises(SchedulerError):
        children._initialization(directory, "root", "ordinary-run")


def test_canonical_data_export_and_bound_record_do_not_alias_caller_graph(tmp_path):
    parent = descriptor()
    exported = parent.to_json()
    exported["graph"]["nodes"][0]["inputs"][0]["nested"]["a"].append("export mutation")
    assert parent.to_json()["graph"]["nodes"][0] == graph().nodes[0].to_json()
    live = submitted(tmp_path)
    record = live.register_external_parent_attempt(canonical_parent=parent, **binding())
    exported = parent.to_json()
    exported["identity"]["parent_task_id"] = "foreign"
    exported["graph"]["nodes"][0]["inputs"][0]["nested"]["a"].append("other")
    assert record.canonical_parent["admission"] == parent.to_json()
    assert cold(live)._tasks["root"].canonical_parent == record.canonical_parent


@pytest.mark.parametrize("restore_first", [False, True])
def test_canonical_root_survives_actual_dynamic_child_journal_and_cold_replay(tmp_path, restore_first):
    directory, live = initialized(tmp_path)
    initial = children._canonical_initial_prefix(directory)
    if restore_first:
        live = cold(live)
    proposal = scheduling.ChildProposal(parent_role="reader",
        parent_tools=("read_file", "herdr_submit_result"), child_role="reader",
        child_tools=("read_file",), parent_permissions=("repo:read",), child_permissions=(),
        child_task="Inspect a public fixture", child_model="external", child_fallback_model=None)
    child = live.delegate_child("root", "ordinary-run", "real-child-key", proposal)
    assert not isinstance(child, scheduling.DenyDecision)
    live.audit_log.flush()
    assert len([e for e in live.audit_log.replay() if e["event"] == "submit"]) == 1
    assert len([e for e in live.audit_log.replay() if e["event"] == "spawn_child"]) == 1
    assert children._canonical_initial_prefix(directory) == initial
    assert children._initialization(directory, "root", "ordinary-run")["state"] == "committed"
    restored = cold(live)
    assert restored._tasks["root"].node.to_json() == graph().nodes[0].to_json()
    assert restored._tasks[child.id].node.to_json() == child.to_json()
    before = live.audit_log._path.read_bytes()
    assert adopt(restored).fencing_token == 37
    same = restored.delegate_child("root", "ordinary-run", "real-child-key", proposal)
    assert same.id == child.id
    assert live.audit_log._path.read_bytes() == before
    assert (restored._plan_max_nodes, restored._plan_max_depth, restored._plan_max_fanout) == (3, 2, 1)


def test_canonical_admission_rejects_foreign_preclaim_submit_not_only_extra_graph(tmp_path):
    live = submitted(tmp_path)
    events = live.audit_log.replay()
    foreign = copy.deepcopy(events[0])
    foreign.update(id="foreign", task_id="foreign")
    live.audit_log.append(foreign)
    live.audit_log.flush()
    before = live.audit_log._path.read_bytes()
    with pytest.raises(SchedulerError):
        adopt(live)
    assert live.audit_log._path.read_bytes() == before
