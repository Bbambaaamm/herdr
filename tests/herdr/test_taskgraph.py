"""Acceptance tests for Herdr v1.1 TaskGraph schema + deterministic planner
contract (issue #230).

Maps 1:1 to the issue acceptance criteria:
  [ ] same planner output → same graph hash
  [ ] invalid DAG fail-closed
  [ ] restart recovery from durable storage
  [ ] child node cannot exceed parent policy
  [ ] task payload contains no secrets
  [ ] unit + persistence + malformed-input tests
  [ ] deterministic graph hash (deterministic, repeatable)

Bounded isolated provider- and consumer-neutral orchestration slice.
"""

from __future__ import annotations

import json

import pytest

from herdr.taskgraph import (
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_FANOUT,
    DEFAULT_MAX_NODES,
    GraphValidationError,
    LifecycleState,
    PersistentTaskGraph,
    TaskGraph,
    TaskGraphEnvelope,
    TaskNode,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------
def _env(tmp_path, spec="spec-v1.0") -> TaskGraphEnvelope:
    return TaskGraphEnvelope(
        issue="230",
        spec_hash="sha256:" + "a" * 64,
        graph_version="1.1.0",
        created_at="2026-09-26T14:19:07Z",
        planner="herdr-planner@1.1.0",
        max_nodes=DEFAULT_MAX_NODES,
        max_depth=DEFAULT_MAX_DEPTH,
        max_fanout=DEFAULT_MAX_FANOUT,
        policy_profile="default",
    )


def _root_node() -> dict:
    return {
        "id": "root",
        "parent_id": None,
        "type": "task",
        "role": "planner",
        "objective": "Plan alpha research",
        "inputs": [{"universe": "SPY"}],
        "expected_outputs": [{"plan": "graph"}],
        "dependencies": [],
        "priority": 1,
        "resource_class": "small",
        "model_policy": {"model": "gpt-4o-mini"},
        "tools": ["search", "compute", "review"],
        "permissions": ["read_data", "write_artifacts"],
    }


def _child_node(parent_id: str = "root", **overrides) -> dict:
    base = {
        "id": "child",
        "parent_id": parent_id,
        "type": "task",
        "role": "worker",
        "objective": "Execute research step",
        "inputs": [{"step": 1}],
        "expected_outputs": [{"result": "data"}],
        "dependencies": [parent_id],
        "priority": 1,
        "resource_class": "small",
        "model_policy": {"model": "gpt-4o-mini"},
        "tools": ["search"],
        "permissions": ["read_data"],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Acceptance #1: same planner output → same graph hash (deterministic)
# ---------------------------------------------------------------------------
def test_deterministic_graph_hash_same_output_same_hash(tmp_path):
    """Acceptance #1 + documented hash determinism: identical planner output
    MUST yield an identical graph hash, across two independent builds."""
    env = _env(tmp_path)
    node_dicts = [_root_node(), _child_node()]

    graph_a = TaskGraph.from_planner_output(env, node_dicts)
    graph_b = TaskGraph.from_planner_output(env, node_dicts)

    assert graph_a.graph_hash() == graph_b.graph_hash()
    # hash is a stable 64-char hex sha256
    assert len(graph_a.graph_hash()) == 64
    assert all(c in "0123456789abcdef" for c in graph_a.graph_hash())


def test_graph_hash_changes_with_topology(tmp_path):
    """Acceptance #1 (negative): a *different* graph must produce a different
    hash — proves the hash is structural, not accidental."""
    env = _env(tmp_path)
    g_a = TaskGraph.from_planner_output(env, [_root_node(), _child_node()])
    g_b = TaskGraph.from_planner_output(
        env, [_root_node(), _child_node(objective="different objective")]
    )
    assert g_a.graph_hash() != g_b.graph_hash()


# ---------------------------------------------------------------------------
# Acceptance #2: invalid DAG fail-closed
# ---------------------------------------------------------------------------
def test_invalid_dag_cycle_fail_closed(tmp_path):
    """Cycle detection → GraphValidationError (fail-closed)."""
    env = _env(tmp_path)
    a = _root_node()
    b = _child_node(parent_id="a", id="b", dependencies=["a"])
    a = {**a, "id": "a", "dependencies": ["b"]}
    with pytest.raises(GraphValidationError, match="cycle"):
        TaskGraph.from_planner_output(env, [a, b])


def test_invalid_dag_unknown_dependency_fail_closed(tmp_path):
    """Unknown dependency → rejected."""
    env = _env(tmp_path)
    root = _root_node()
    child = _child_node(dependencies=["does-not-exist"])
    with pytest.raises(GraphValidationError, match="unknown dependency"):
        TaskGraph.from_planner_output(env, [root, child])


def test_invalid_dag_duplicate_node_fail_closed(tmp_path):
    """Duplicate node id → rejected."""
    env = _env(tmp_path)
    root = _root_node()
    with pytest.raises(GraphValidationError, match="duplicate node id"):
        TaskGraph.from_planner_output(env, [root, _root_node()])


def test_invalid_dag_self_dependency_fail_closed(tmp_path):
    env = _env(tmp_path)
    root = {**_root_node(), "dependencies": ["root"]}
    with pytest.raises(GraphValidationError, match="self-dependency"):
        TaskGraph.from_planner_output(env, [root])


# ---------------------------------------------------------------------------
# Acceptance #3: restart recovery from durable storage
# ---------------------------------------------------------------------------
def test_restart_recovery_reconstructs_state(tmp_path):
    """Acceptance #3: after persist → crash-simulated-reopen, replay must
    reconstruct the exact graph (same hash) + current node state."""
    env = _env(tmp_path)
    graph = TaskGraph.from_planner_output(env, [_root_node(), _child_node()])

    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(graph)
    # simulate state transitions (durable)
    store.set_node_state("root", LifecycleState.DONE)
    store.set_node_state("child", LifecycleState.RUNNING)

    # Simulate crash: new store instance reads the same append-only log.
    store2 = PersistentTaskGraph(log)
    recovered_graph, recovered_state = store2.replay()

    assert recovered_graph.graph_hash() == graph.graph_hash()
    assert recovered_state["root"] == LifecycleState.DONE
    assert recovered_state["child"] == LifecycleState.RUNNING
    # envelope preserved
    assert recovered_graph.envelope.spec_hash == env.spec_hash
    assert recovered_graph.envelope.policy_profile == "default"


def test_restart_recovery_durable_cancelled(tmp_path):
    """Acceptance: cancellation is durable — survives restart."""
    env = _env(tmp_path)
    graph = TaskGraph.from_planner_output(env, [_root_node(), _child_node()])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(graph)
    store.cancel_node("child", "manual escalation")

    store2 = PersistentTaskGraph(log)
    _, state = store2.replay()
    assert state["child"] == LifecycleState.CANCELLED


def test_persistent_store_malformed_event_fail_closed(tmp_path):
    """Malformed input (corrupt event log line) → fail-closed."""
    log = tmp_path / "events.jsonl"
    log.write_text("{not valid json}\n", encoding="utf-8")
    store = PersistentTaskGraph(log)
    with pytest.raises(GraphValidationError, match="malformed event"):
        store.replay()


# ---------------------------------------------------------------------------
# Acceptance #4: child node cannot exceed parent policy
# ---------------------------------------------------------------------------
def test_child_permission_escalation_fail_closed(tmp_path):
    """Acceptan #4: child tools/permissions must be a subset of parent's."""
    env = _env(tmp_path)
    root = _root_node()  # tools/permissions = parent
    # child attempts to escalate: extra tool + extra permission
    child = _child_node(
        tools=["search", "deploy"],  # 'deploy' not in parent tools
        permissions=["read_data", "write_live_orders"],  # 'write_live_orders' extra
    )
    with pytest.raises(GraphValidationError, match="escalation"):
        TaskGraph.from_planner_output(env, [root, child])


def test_child_subsets_parent_ok(tmp_path):
    """Positive case: child within parent's allowlist is accepted."""
    env = _env(tmp_path)
    root = _root_node()
    child = _child_node(tools=["search"], permissions=["read_data"])
    graph = TaskGraph.from_planner_output(env, [root, child])
    assert len(graph.nodes) == 2


# ---------------------------------------------------------------------------
# Acceptance #5: task payload contains no secrets
# ---------------------------------------------------------------------------
def test_task_payload_no_secrets_fail_closed(tmp_path):
    """Acceptance #5: secret-like keys in payload → rejected (fail-closed)."""
    env = _env(tmp_path)
    root = _root_node()
    bad_node = {
        **_root_node(),
        "id": "leaky",
        "parent_id": "root",
        "permissions": ["read_data"],
        "inputs": [{"apikey": "sk-live-..."}],  # secret-like key
    }
    with pytest.raises(GraphValidationError, match="secrets detected"):
        TaskGraph.from_planner_output(env, [root, bad_node])


def test_task_payload_secret_scan_method(tmp_path):
    """Unit test for the secret-scan guard."""
    node = TaskNode(
        id="n",
        parent_id=None,
        type="task",
        role="planner",
        objective="ok",
        inputs=[{"universe": "SPY"}],
        expected_outputs=[],
        dependencies=(),
        priority=1,
        resource_class="small",
        model_policy={"model": "gpt-4o"},
        tools=("read",),
        permissions=("read_data",),
    )
    assert node.payload_secret_hits() == []
    # Now mutate into a frozen-dataclass copy with a secret key
    leaky = TaskNode(
        id="n",
        parent_id=None,
        type="task",
        role="planner",
        objective="ok",
        inputs=[{"secret_token": "x"}],
        expected_outputs=[],
        dependencies=(),
        priority=1,
        resource_class="small",
        model_policy={},
        tools=("read",),
        permissions=(),
    )
    assert leaky.payload_secret_hits()  # non-empty → secret detected


# ---------------------------------------------------------------------------
# Acceptance #6: bounded max nodes/depth/fanout
# ---------------------------------------------------------------------------
def test_bounded_max_nodes_rejected(tmp_path):
    """Planner trying to emit a graph larger than max_nodes → fail-closed."""
    env = TaskGraphEnvelope(
        issue="230",
        spec_hash="s",
        graph_version="1.1.0",
        created_at="2026-09-26T00:00:00Z",
        planner="p",
        max_nodes=2,
        max_depth=16,
        max_fanout=16,
    )
    nodes = []
    for i in range(3):
        nodes.append(
            {
                "id": f"n{i}",
                "parent_id": None,
                "type": "task",
                "role": "planner",
                "objective": "o",
                "inputs": [],
                "expected_outputs": [],
                "dependencies": [],
                "priority": 1,
                "resource_class": "small",
                "model_policy": {"model": "m"},
                "tools": ["t"],
                "permissions": ["p"],
            }
        )
    with pytest.raises(GraphValidationError, match="max_nodes"):
        TaskGraph.from_planner_output(env, nodes)


def test_bounded_max_depth_rejected(tmp_path):
    """Depth chain exceeding max_depth → fail-closed."""
    env = TaskGraphEnvelope(
        issue="230",
        spec_hash="s",
        graph_version="1.1.0",
        created_at="2026-09-26T00:00:00Z",
        planner="p",
        max_nodes=64,
        max_depth=2,
        max_fanout=16,
    )
    base = {
        "type": "task",
        "role": "worker",
        "objective": "o",
        "inputs": [],
        "expected_outputs": [],
        "dependencies": [],
        "priority": 1,
        "resource_class": "small",
        "model_policy": {"model": "m"},
        "tools": ["t"],
        "permissions": ["p"],
    }
    nodes = [{**base, "id": "r", "parent_id": None}]
    nodes.append({**base, "id": "c1", "parent_id": "r"})
    nodes.append({**base, "id": "c2", "parent_id": "c1"})  # depth 3 > 2
    with pytest.raises(GraphValidationError, match="max_depth"):
        TaskGraph.from_planner_output(env, nodes)


def test_bounded_max_fanout_rejected(tmp_path):
    """A parent with more children than max_fanout → fail-closed."""
    env = TaskGraphEnvelope(
        issue="230",
        spec_hash="s",
        graph_version="1.1.0",
        created_at="2026-09-26T00:00:00Z",
        planner="p",
        max_nodes=64,
        max_depth=16,
        max_fanout=2,
    )
    base = {
        "type": "task",
        "role": "worker",
        "objective": "o",
        "inputs": [],
        "expected_outputs": [],
        "dependencies": [],
        "priority": 1,
        "resource_class": "small",
        "model_policy": {"model": "m"},
        "tools": ["t"],
        "permissions": ["p"],
    }
    nodes = [{**base, "id": "root", "parent_id": None}]
    for i in range(3):
        nodes.append({**base, "id": f"c{i}", "parent_id": "root"})  # 3 > 2
    with pytest.raises(GraphValidationError, match="max_fanout"):
        TaskGraph.from_planner_output(env, nodes)


# ---------------------------------------------------------------------------
# Acceptance #7 (documented JSON schema / typed contract)
# ---------------------------------------------------------------------------
def test_graph_hash_is_deterministic_across_process(tmp_path):
    """Documented contract: the graph hash is a pure function of the
    canonical (sorted-key) JSON of envelope + nodes.  Verify by re-serializing
    externally."""
    env = _env(tmp_path)
    nodes = [_root_node(), _child_node()]
    graph = TaskGraph.from_planner_output(env, nodes)

    payload = {
        "envelope": env.to_canonical_json(),
        "nodes": [graph._canonical_node_repr(n) for n in graph.nodes],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    import hashlib

    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert graph.graph_hash() == expected


def test_envelope_policy_profile(tmp_path):
    """The envelope carries the consumer policy profile in the canonical contract."""
    env = _env(tmp_path)
    assert env.policy_profile == "default"


def test_graph_edges_derived(tmp_path):
    """Edges (parent→child and dependency) are derived deterministically."""
    env = _env(tmp_path)
    graph = TaskGraph.from_planner_output(env, [_root_node(), _child_node()])
    edges = graph.edges()
    assert ("root", "child") in edges


# ---------------------------------------------------------------------------
# Remediation evidence for reviewer BLOCK (fail-closed validation/recovery)
# ---------------------------------------------------------------------------


def test_parent_id_cycle_fail_closed(tmp_path):
    """Acceptance #2: a parent_id cycle (not a dependencies cycle) must be
    rejected by _depth_of — infinite recursion / stack-overflow otherwise."""
    env = _env(tmp_path)
    a = _root_node()
    a["id"] = "a"
    a["parent_id"] = "b"
    a["dependencies"] = []
    b = _root_node()
    b["id"] = "b"
    b["parent_id"] = "a"
    b["dependencies"] = []
    with pytest.raises(GraphValidationError, match="parent_id cycle"):
        TaskGraph.from_planner_output(env, [a, b])


def test_replay_unknown_event_type_fail_closed(tmp_path):
    """Recovery defect: unknown event types in the log must be rejected
    (fail-closed), not silently ignored."""
    env = _env(tmp_path)
    graph = TaskGraph.from_planner_output(env, [_root_node(), _child_node()])
    log = tmp_path / "events.jsonl"
    store = PersistentTaskGraph(log)
    store.persist_graph(graph)
    # Append an unknown event type after valid entries
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": "bogus_event", "payload": "test"}) + "\n")
    store2 = PersistentTaskGraph(log)
    with pytest.raises(GraphValidationError, match="unknown event type"):
        store2.replay()


def test_scan_for_secrets_detects_access_key(tmp_path):
    """Secret-handling: 'access_key' must be detected (was missing from
    _SECRET_FRAGMENTS)."""
    env = _env(tmp_path)
    leaky = {
        **_root_node(),
        "id": "leaky",
        "inputs": [{"access_key": "AKIAIOSFODNN7EXAMPLE"}],
    }
    with pytest.raises(GraphValidationError, match="secrets detected"):
        TaskGraph.from_planner_output(env, [leaky])
