from __future__ import annotations

import json

import pytest

from herdr.taskgraph import (
    GRAPH_VERSION,
    GraphValidationError,
    LifecycleState,
    NodeRuntimeState,
    PersistentTaskGraph,
    TaskGraph,
    TaskGraphEnvelope,
)


def envelope(**overrides):
    data = {
        "issue": "Bbambaaamm/herdr#2",
        "spec_hash": "sha256:" + "a" * 64,
        "graph_version": GRAPH_VERSION,
        "created_at": "2026-09-27T00:00:00+00:00",
        "planner": "herdr-planner@1.1.0",
        "max_nodes": 256,
        "max_depth": 16,
        "max_fanout": 16,
        "policy_profile": "quantlab-paper",
    }
    data.update(overrides)
    return TaskGraphEnvelope.from_dict(data)


def node(node_id="root", parent_id=None, **overrides):
    data = {
        "id": node_id,
        "parent_id": parent_id,
        "type": "task",
        "role": "planner" if parent_id is None else "worker",
        "objective": f"objective {node_id}",
        "inputs": [{"artifact_ref": "fixture"}],
        "expected_outputs": [{"kind": "result"}],
        "dependencies": [],
        "priority": 1,
        "resource_class": "small",
        "model_policy": {"model": "fixture-model"},
        "tools": ["read", "review"] if parent_id is None else ["read"],
        "permissions": ["repo:read", "artifact:write"] if parent_id is None else ["repo:read"],
        "timeout_seconds": 120,
        "max_attempts": 3,
    }
    data.update(overrides)
    return data


def graph(nodes=None, env=None):
    return TaskGraph.from_planner_output(env or envelope(), nodes or [node()])


def test_hash_is_structural_and_order_independent():
    a = graph([node("root"), node("child", "root", dependencies=["root"])])
    later = envelope(created_at="2026-09-27T01:00:00+00:00")
    b = graph([node("child", "root", dependencies=["root"]), node("root")], later)
    assert a.graph_hash() == b.graph_hash()


def test_hash_normalizes_set_like_fields():
    a = graph([node(tools=["read", "review"], permissions=["repo:read", "artifact:write"])])
    b = graph([node(tools=["review", "read"], permissions=["artifact:write", "repo:read"])])
    assert a.graph_hash() == b.graph_hash()



def test_payload_is_deeply_immutable_after_validation():
    g = graph([node()])
    before = g.graph_hash()
    with pytest.raises(TypeError):
        g.nodes[0].inputs[0]["artifact_ref"] = "changed"
    with pytest.raises(TypeError):
        g.nodes[0].model_policy["model"] = "changed"
    assert g.graph_hash() == before

def test_planner_output_strict_parser():
    payload = {"envelope": envelope().to_json(), "nodes": [node()]}
    parsed = TaskGraph.parse_planner_output(payload)
    assert parsed.envelope.issue == "Bbambaaamm/herdr#2"
    with pytest.raises(GraphValidationError, match="unknown fields"):
        TaskGraph.parse_planner_output({**payload, "surprise": True})
    with pytest.raises(GraphValidationError, match="missing required"):
        TaskGraph.parse_planner_output({"envelope": payload["envelope"], "nodes": [{"id": "x"}]})


def test_hard_limits_cannot_be_inflated_by_planner():
    with pytest.raises(GraphValidationError, match="max_nodes"):
        envelope(max_nodes=257)
    with pytest.raises(GraphValidationError, match="max_depth"):
        envelope(max_depth=17)
    with pytest.raises(GraphValidationError, match="max_fanout"):
        envelope(max_fanout=17)


def test_unknown_parent_fails_closed_and_cannot_bypass_permissions():
    with pytest.raises(GraphValidationError, match="unknown parent"):
        graph([node("child", "ghost", tools=["deploy"], permissions=["admin"])])


def test_parent_hierarchy_cycle_fails_closed():
    with pytest.raises(GraphValidationError, match="hierarchy cycle"):
        graph([node("a", "b"), node("b", "a")])


def test_dependency_cycle_fails_closed():
    with pytest.raises(GraphValidationError, match="dependency cycle"):
        graph([node("a", dependencies=["b"]), node("b", dependencies=["a"])])


def test_parent_hierarchy_is_not_implicitly_dependency_dag():
    g = graph([node("parent", dependencies=["child"]), node("child", "parent")])
    assert g.hierarchy_edges() == (("parent", "child"),)
    assert g.dependency_edges() == (("child", "parent"),)


def test_child_cannot_escalate_tools_or_permissions():
    with pytest.raises(GraphValidationError, match="escalation"):
        graph([node("root"), node("child", "root", tools=["deploy"], permissions=["admin"])])


def test_depth_and_fanout_are_bounded():
    env = envelope(max_depth=2, max_fanout=1)
    with pytest.raises(GraphValidationError, match="max_depth"):
        graph([node("a"), node("b", "a"), node("c", "b")], env)
    with pytest.raises(GraphValidationError, match="max_fanout"):
        graph([node("a"), node("b", "a"), node("c", "a")], env)


def test_secret_like_keys_and_values_fail_closed():
    with pytest.raises(GraphValidationError, match="secret-like"):
        graph([node(inputs=[{"api_key": "value"}])])
    with pytest.raises(GraphValidationError, match="secret-like"):
        graph([node(inputs=[{"value": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"}])])


def test_non_finite_or_non_json_payload_fails_closed():
    with pytest.raises(GraphValidationError, match="non-finite"):
        graph([node(inputs=[{"value": float("nan")}])])
    with pytest.raises(GraphValidationError, match="non-JSON"):
        graph([node(inputs=[{"value": {1, 2}}])])


def test_runtime_metadata_is_typed_and_bounded():
    g = graph([node(max_attempts=2)])
    valid = NodeRuntimeState(LifecycleState.RUNNING, attempt=1)
    valid.validate_for(g.nodes[0])
    with pytest.raises(GraphValidationError, match="0..2"):
        NodeRuntimeState(LifecycleState.RUNNING, attempt=3).validate_for(g.nodes[0])
    with pytest.raises(GraphValidationError, match="set together"):
        NodeRuntimeState(LifecycleState.RUNNING, attempt=1, lease_id="lease").validate_for(g.nodes[0])


def test_persistence_replay_initializes_pending_and_recovers_runtime(tmp_path):
    g = graph([node("root"), node("child", "root")])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(g)
    assert store.current_state()["child"].lifecycle is LifecycleState.PENDING
    store.set_node_runtime(
        "child",
        NodeRuntimeState(
            LifecycleState.RUNNING,
            attempt=1,
            lease_id="lease-1",
            lease_expires_at="2026-09-27T01:00:00+00:00",
        ),
    )
    recovered, state = PersistentTaskGraph(log).replay()
    assert recovered.graph_hash() == g.graph_hash()
    assert state["root"].lifecycle is LifecycleState.PENDING
    assert state["child"].attempt == 1
    assert state["child"].lease_id == "lease-1"


def test_cancel_updates_materialized_state_immediately_and_after_restart(tmp_path):
    g = graph([node()])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(g)
    store.cancel_node("root", "operator request")
    assert store.current_state()["root"].lifecycle is LifecycleState.CANCELLED
    _, state = PersistentTaskGraph(log).replay()
    assert state["root"].lifecycle is LifecycleState.CANCELLED


def test_unknown_node_runtime_event_fails_before_write(tmp_path):
    store = PersistentTaskGraph(tmp_path / "events.jsonl")
    store.persist_graph(graph([node()]))
    with pytest.raises(GraphValidationError, match="unknown node"):
        store.set_node_state("ghost", LifecycleState.RUNNING)


def test_runtime_event_is_bound_to_graph_hash(tmp_path):
    g = graph([node()])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(g)
    event = {
        "type": "node_runtime",
        "graph_hash": "0" * 64,
        "node_id": "root",
        "runtime": NodeRuntimeState(LifecycleState.RUNNING).to_json(),
        "ts": "2026-09-27T00:00:00+00:00",
    }
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    with pytest.raises(GraphValidationError, match="different graph hash"):
        PersistentTaskGraph(log).replay()


def test_multiple_graph_records_fail_closed(tmp_path):
    g = graph([node()])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(g)
    with pytest.raises(GraphValidationError, match="already initialized"):
        store.persist_graph(g)


def test_malformed_complete_event_fails_but_torn_tail_is_ignored(tmp_path):
    g = graph([node()])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(g)
    with log.open("ab") as fh:
        fh.write(b'{"type":"node_runtime"')
    recovered, state = PersistentTaskGraph(log).replay()
    assert recovered.graph_hash() == g.graph_hash()
    assert state["root"].lifecycle is LifecycleState.PENDING

    clean = tmp_path / "bad.jsonl"
    store2 = PersistentTaskGraph(clean)
    store2.persist_graph(g)
    with clean.open("ab") as fh:
        fh.write(b'{broken}\n')
    with pytest.raises(GraphValidationError, match="malformed complete event"):
        PersistentTaskGraph(clean).replay()


def test_duplicate_json_keys_fail_closed(tmp_path):
    g = graph([node()])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(g)
    with log.open("ab") as fh:
        fh.write(b'{"type":"x","type":"y"}\n')
    with pytest.raises(GraphValidationError, match="malformed complete event"):
        PersistentTaskGraph(log).replay()


def test_empty_graph_and_string_list_fields_fail_closed():
    with pytest.raises(GraphValidationError, match="at least one node"):
        TaskGraph.from_planner_output(envelope(), [])
    bad = node()
    bad["tools"] = "read"
    with pytest.raises(GraphValidationError, match="tools must be an array"):
        graph([bad])


def test_spec_hash_must_be_canonical_lowercase():
    with pytest.raises(GraphValidationError, match="lowercase"):
        envelope(spec_hash="sha256:" + "A" * 64)


def test_cancel_reason_secret_pattern_is_rejected(tmp_path):
    store = PersistentTaskGraph(tmp_path / "events.jsonl")
    store.persist_graph(graph([node()]))
    with pytest.raises(GraphValidationError, match="secret-like"):
        store.cancel_node("root", "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456")
