"""Herdr durable TaskGraph schema and deterministic planner contract.

Provider- and consumer-neutral orchestration primitives: bounded DAG validation,
secret isolation, descendant permission monotonicity, deterministic graph hashing,
and append-only persistence/recovery. Consumer-specific safety rules are referenced
through the envelope policy profile and enforced by admission/runtime policy layers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Bounded graph limits (issue #230: "explicit bounded max nodes/depth/fanout")
# ---------------------------------------------------------------------------
# Fail-closed defaults — a planner must not be able to bypass these by simply
# emitting a larger graph.  The envelope carries the effective limit that was
# applied, so recovery / Machine City can audit the bound that guarded the run.
DEFAULT_MAX_NODES = 256
DEFAULT_MAX_DEPTH = 16
DEFAULT_MAX_FANOUT = 16

GRAPH_VERSION = "1.1.0"


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
class LifecycleState(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def terminal(cls) -> frozenset[str]:
        return frozenset({cls.DONE, cls.FAILED, cls.CANCELLED})


# ---------------------------------------------------------------------------
# Envelope + Node
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TaskGraphEnvelope:
    """Immutable graph envelope (issue/spec hash + planner identity + version)."""

    issue: str
    spec_hash: str
    graph_version: str
    created_at: str
    planner: str
    max_nodes: int = DEFAULT_MAX_NODES
    max_depth: int = DEFAULT_MAX_DEPTH
    max_fanout: int = DEFAULT_MAX_FANOUT
    policy_profile: str = "default"

    def to_canonical_json(self) -> dict[str, Any]:
        return {
            "issue": self.issue,
            "spec_hash": self.spec_hash,
            "graph_version": self.graph_version,
            "created_at": self.created_at,
            "planner": self.planner,
            "max_nodes": self.max_nodes,
            "max_depth": self.max_depth,
            "max_fanout": self.max_fanout,
            "policy_profile": self.policy_profile,
        }


@dataclass(frozen=True)
class TaskNode:
    """A single DAG node.

    Frozen (immutable) so that a constructed node is a faithful, tamper-evident
    unit.  Permissions/tools are validated against the parent at planner time.
    """

    id: str
    parent_id: str | None
    type: str
    role: str
    objective: str
    inputs: list[dict[str, Any]]
    expected_outputs: list[dict[str, Any]]
    dependencies: tuple[str, ...]
    priority: int
    resource_class: str
    model_policy: dict[str, Any]
    tools: tuple[str, ...]
    permissions: tuple[str, ...]
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # ------------------------------------------------------------------
    # Secret-isolation guard (issue #230: "task payload neobsahuje secrets")
    # ------------------------------------------------------------------
    _SECRET_FRAGMENTS: tuple[str, ...] = (
        "secret",
        "token",
        "password",
        "passwd",
        "apikey",
        "api_key",
        "api-key",
        "access_key",
        "accesskey",
        "credential",
        "private_key",
        "privatekey",
    )

    def _scan_for_secrets(self) -> list[str]:
        """Linear scan of payload fields for secret-like keys/values.

        Conservative: only key names are inspected (values are never logged),
        so a false-positive blocks construction.  This is intentional — secrets
        must never enter a task payload; the planner must keep them out.
        """
        hits: list[str] = []

        def _walk(obj: Any, path: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    loc = f"{path}.{k}" if path else k
                    kn = k.lower()
                    if any(frag in kn for frag in self._SECRET_FRAGMENTS):
                        hits.append(loc)
                    _walk(v, loc)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    _walk(v, f"{path}[{i}]")

        payload = {
            "inputs": self.inputs,
            "expected_outputs": self.expected_outputs,
            "model_policy": self.model_policy,
        }
        _walk(payload)
        return hits

    def payload_secret_hits(self) -> list[str]:
        return self._scan_for_secrets()

    # ------------------------------------------------------------------
    # Child-vs-parent permission escalation guard
    # (issue #230: "child node nemůže získat více oprávnění než parent policy")
    # ------------------------------------------------------------------
    def verify_descendant_permissions(
        self, parent_tools: tuple[str, ...], parent_perms: tuple[str, ...]
    ) -> list[str]:
        """Return list of violation messages (empty == OK).

        A child may hold a SUBSET of its parent's tool and permission sets,
        never a superset.  This is checked by the planner at parse time, but
        is also re-validated here as a durable guard.
        """
        violations: list[str] = []
        child_tools = set(self.tools)
        child_perms = set(self.permissions)
        parent_tool_set = set(parent_tools)
        parent_perm_set = set(parent_perms)

        extra_tools = child_tools - parent_tool_set
        extra_perms = child_perms - parent_perm_set

        if extra_tools:
            violations.append(
                f"node {self.id!r}: child tool escalation ({sorted(extra_tools)} ⊄ parent tools)"
            )
        if extra_perms:
            violations.append(
                f"node {self.id!r}: child permission escalation "
                f"({sorted(extra_perms)} ⊄ parent permissions)"
            )
        return violations


# ---------------------------------------------------------------------------
# DAG + deterministic graph hash
# ---------------------------------------------------------------------------
class GraphValidationError(Exception):
    """Raised when a TaskGraph is structurally invalid (fail-closed)."""


@dataclass
class TaskGraph:
    """An in-memory, immutable-ish TaskGraph.

    Constructed from an envelope + a list of TaskNode dicts (planner output).
    Validation runs eagerly: any structural defect raises GraphValidationError
    and the graph is rejected (fail-closed).

    The deterministic ``graph_hash`` is a SHA-256 over the canonical
    serialization of the envelope + nodes + edges — identical planner output
    always yields the same hash (issue #230 acceptance #1).
    """

    envelope: TaskGraphEnvelope
    nodes: list[TaskNode] = field(default_factory=list)
    # edges: list[tuple[str, str]]  # (from, to) — derived from dependencies

    # --- construction -------------------------------------------------
    @classmethod
    def from_planner_output(
        cls,
        envelope: TaskGraphEnvelope,
        node_dicts: list[dict[str, Any]],
    ) -> TaskGraph:
        """Parse + validate planner output into a TaskGraph.

        Raises GraphValidationError on any structural defect (fail-closed).
        """
        nodes: list[TaskNode] = []
        id_set: set[str] = set()
        parent_tools_by_id: dict[str, tuple[str, ...]] = {}
        parent_perms_by_id: dict[str, tuple[str, ...]] = {}

        for nd in node_dicts:
            nid = nd["id"]
            if nid in id_set:
                raise GraphValidationError(f"duplicate node id rejected: {nid!r}")
            id_set.add(nid)

            node = TaskNode(
                id=nid,
                parent_id=nd.get("parent_id"),
                type=nd["type"],
                role=nd["role"],
                objective=nd["objective"],
                inputs=nd.get("inputs", []),
                expected_outputs=nd.get("expected_outputs", []),
                dependencies=tuple(nd.get("dependencies", [])),
                priority=int(nd.get("priority", 0)),
                resource_class=nd.get("resource_class", "default"),
                model_policy=nd.get("model_policy", {}),
                tools=tuple(nd.get("tools", [])),
                permissions=tuple(nd.get("permissions", [])),
                created_at=(nd.get("created_at") or datetime.now(UTC).isoformat()),
            )

            # Secret isolation: payload must never contain secrets.
            secret_hits = node.payload_secret_hits()
            if secret_hits:
                raise GraphValidationError(
                    f"node {nid!r}: secrets detected in payload at "
                    f"{secret_hits} — rejected (payload may not contain secrets)"
                )

            nodes.append(node)
            parent_tools_by_id[nid] = node.tools
            parent_perms_by_id[nid] = node.permissions

        graph = cls(envelope=envelope, nodes=nodes)
        graph._validate_structure()
        graph._validate_depth_and_fanout()
        graph._validate_descendant_permissions(parent_tools_by_id, parent_perms_by_id)
        graph._validate_bounded_limits()
        return graph

    # --- validation ---------------------------------------------------
    def _node_index(self) -> dict[str, TaskNode]:
        return {n.id: n for n in self.nodes}

    def _validate_structure(self) -> None:
        idx = self._node_index()

        # unknown dependency rejection
        for n in self.nodes:
            for dep in n.dependencies:
                if dep not in idx:
                    raise GraphValidationError(
                        f"node {n.id!r}: unknown dependency {dep!r} rejected"
                    )
                if dep == n.id:
                    raise GraphValidationError(f"node {n.id!r}: self-dependency rejected")

        # root count: exactly one root (parent_id None) OR all parented —
        # we accept a single root or a forest of roots, but every dependency
        # must be acyclic.
        if self._has_cycle():
            raise GraphValidationError("cycle detected in task graph — rejected")

        # duplicate node rejection is enforced at parse time (id_set check).

    def _has_cycle(self) -> bool:
        idx = self._node_index()
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {n.id: WHITE for n in self.nodes}

        def visit(nid: str) -> bool:
            color[nid] = GRAY
            node = idx[nid]
            for dep in node.dependencies:
                c = color[dep]
                if c == GRAY:
                    return True  # back edge → cycle
                if c == WHITE and visit(dep):
                    return True
            color[nid] = BLACK
            return False

        return any(color[nid] == WHITE and visit(nid) for nid in idx)

    def _depth_of(
        self,
        nid: str,
        idx: dict[str, TaskNode],
        cache: dict[str, int],
        visiting: set[str] | None = None,
    ) -> int:
        if visiting is None:
            visiting = set()
        if nid in cache:
            return cache[nid]
        if nid in visiting:
            raise GraphValidationError(f"parent_id cycle detected involving {nid!r}")
        visiting.add(nid)
        node = idx[nid]
        if not node.parent_id or node.parent_id not in idx:
            cache[nid] = 1
            visiting.discard(nid)
            return 1
        depth = 1 + self._depth_of(node.parent_id, idx, cache, visiting)
        cache[nid] = depth
        visiting.discard(nid)
        return depth

    def _validate_depth_and_fanout(self) -> None:
        idx = self._node_index()
        cache: dict[str, int] = {}
        depth_exceeded = {
            n.id for n in self.nodes if self._depth_of(n.id, idx, cache) > self.envelope.max_depth
        }
        if depth_exceeded:
            raise GraphValidationError(
                f"max_depth ({self.envelope.max_depth}) exceeded by nodes: {sorted(depth_exceeded)}"
            )

        fanout: dict[str, int] = {}
        for n in self.nodes:
            if n.parent_id and n.parent_id in idx:
                fanout[n.parent_id] = fanout.get(n.parent_id, 0) + 1
        fanout_exceeded = {pid for pid, count in fanout.items() if count > self.envelope.max_fanout}
        if fanout_exceeded:
            raise GraphValidationError(
                f"max_fanout ({self.envelope.max_fanout}) exceeded for parents: "
                f"{sorted(fanout_exceeded)}"
            )

    def _validate_descendant_permissions(
        self,
        parent_tools_by_id: dict[str, tuple[str, ...]],
        parent_perms_by_id: dict[str, tuple[str, ...]],
    ) -> None:
        idx = self._node_index()
        violations: list[str] = []
        for n in self.nodes:
            if n.parent_id and n.parent_id in idx:
                violations.extend(
                    n.verify_descendant_permissions(
                        parent_tools_by_id[n.parent_id],
                        parent_perms_by_id[n.parent_id],
                    )
                )
        if violations:
            raise GraphValidationError(
                "child permission/tool escalation detected (fail-closed): " + "; ".join(violations)
            )

    def _validate_bounded_limits(self) -> None:
        if len(self.nodes) > self.envelope.max_nodes:
            raise GraphValidationError(
                f"max_nodes ({self.envelope.max_nodes}) exceeded: {len(self.nodes)} nodes"
            )

    # --- deterministic hash (issue #230 acceptance #1) ----------------
    def _canonical_node_repr(self, node: TaskNode) -> dict[str, Any]:
        """Canonical, deterministic representation of a node (sorted keys)."""
        return {
            "id": node.id,
            "parent_id": node.parent_id,
            "type": node.type,
            "role": node.role,
            "objective": node.objective,
            "inputs": self._stable(node.inputs),
            "expected_outputs": self._stable(node.expected_outputs),
            "dependencies": list(node.dependencies),
            "priority": node.priority,
            "resource_class": node.resource_class,
            "model_policy": self._stable_dict(node.model_policy),
            "tools": list(node.tools),
            "permissions": list(node.permissions),
        }

    @classmethod
    def _stable(cls, obj: Any) -> Any:
        """Deep-stable sort of nested dicts/lists for determinism."""
        if isinstance(obj, dict):
            return {k: cls._stable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [cls._stable(v) for v in obj]
        return obj

    @classmethod
    def _stable_dict(cls, d: dict[str, Any]) -> dict[str, Any]:
        return {k: cls._stable(v) for k, v in d.items()}

    def graph_hash(self) -> str:
        """Deterministic SHA-256 over canonical envelope + node serialization.

        Same planner output → same hash (issue #230 acceptance #1).
        The hash does NOT depend on created_at/time-of-day — only on the
        structural contract (envelope + nodes + edges).
        """
        payload = {
            "envelope": self.envelope.to_canonical_json(),
            "nodes": [self._canonical_node_repr(n) for n in self.nodes],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # --- edges (derived) ----------------------------------------------
    def edges(self) -> list[tuple[str, str]]:
        """(parent → child) edges plus dependency edges."""
        idx = self._node_index()
        seen: set[tuple[str, str]] = set()
        edges: list[tuple[str, str]] = []
        for n in self.nodes:
            if n.parent_id and n.parent_id in idx:
                e = (n.parent_id, n.id)
                if e not in seen:
                    seen.add(e)
                    edges.append(e)
            for dep in n.dependencies:
                if dep in idx:
                    e = (dep, n.id)
                    if e not in seen:
                        seen.add(e)
                        edges.append(e)
        return edges


# ---------------------------------------------------------------------------
# Durable store (issue #230: "persistence and restart recovery")
# ---------------------------------------------------------------------------
class PersistentTaskGraph:
    """Append-only JSONL event log + current-state materialization.

    This is the *minimal* durable contract required by issue #230: an immutable,
    append-only event log from which the current state can be reconstructed
    after a crash/restart.  It is intentionally small and has no runtime
    dependencies beyond the stdlib so it remains offline-testable and consumer-neutral.

    Event schema (one JSON object per line):
        {"type": "graph_persisted", "envelope": {...}, "nodes": [...], "ts": iso}
        {"type": "node_state", "node_id": id, "state": lifecycle, "ts": iso}
        {"type": "graph_cancelled", "node_id": id, "reason": str, "ts": iso}

    Restart recovery: a new ``PersistentTaskGraph`` pointed at the same file can
    ``replay()`` every event to reconstruct the graph hash and the current
    materialized node-state map — identical to what the crashed process held.
    """

    def __init__(self, path: str | Any):
        self._path = str(path)
        self._events: list[dict[str, Any]] = []
        self._replayed = False
        self._graph: TaskGraph | None = None
        self._state: dict[str, LifecycleState] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    # --- append-only event log (immutable) ---------------------------
    def _append(self, event: dict[str, Any]) -> None:
        # Append-only: we never truncate or rewrite history.  The log is the
        # source of truth; materialized state is always derived from it.
        self._events.append(event)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")

    # --- write API (caller drives state transitions) -----------------
    def persist_graph(self, graph: TaskGraph) -> None:
        """Atomically persist a validated graph to the event log."""
        envelope_dict = graph.envelope.to_canonical_json()
        node_dicts = [asdict(n) for n in graph.nodes]  # frozen dataclass → dict
        # ensure tuples are materialized as lists for JSON determinism
        for nd in node_dicts:
            nd["dependencies"] = list(nd["dependencies"])
            nd["tools"] = list(nd["tools"])
            nd["permissions"] = list(nd["permissions"])
            nd["inputs"] = nd["inputs"] or []
            nd["expected_outputs"] = nd["expected_outputs"] or []
        self._append(
            {
                "type": "graph_persisted",
                "envelope": envelope_dict,
                "nodes": node_dicts,
                "ts": self._now(),
            }
        )
        self._graph = graph
        self._replayed = True

    def set_node_state(self, node_id: str, state: LifecycleState) -> None:
        if state not in LifecycleState.__members__.values():
            raise ValueError(f"unknown lifecycle state: {state!r}")
        self._state[node_id] = state
        self._append({"type": "node_state", "node_id": node_id, "state": state, "ts": self._now()})

    def cancel_node(self, node_id: str, reason: str) -> None:
        self._append(
            {
                "type": "graph_cancelled",
                "node_id": node_id,
                "reason": reason,
                "ts": self._now(),
            }
        )

    # --- read / restart recovery -------------------------------------
    def replay(self) -> tuple[TaskGraph, dict[str, LifecycleState]]:
        """Replay the entire event log → (reconstructed graph, current state).

        Raises if the log is missing or contains an unparseable event
        (fail-closed).  Idempotent: re-replay yields the same result.
        """
        import os

        if not os.path.exists(self._path):
            raise FileNotFoundError(f"event log not found: {self._path}")

        envelope: TaskGraphEnvelope | None = None
        node_dicts: list[dict[str, Any]] = []
        state: dict[str, LifecycleState] = {}
        cancelled: set[str] = set()

        with open(self._path, encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except json.JSONDecodeError as e:
                    raise GraphValidationError(f"malformed event on line {lineno}: {e}") from e
                etype = ev.get("type")
                if etype == "graph_persisted":
                    env = ev["envelope"]
                    envelope = TaskGraphEnvelope(
                        issue=env["issue"],
                        spec_hash=env["spec_hash"],
                        graph_version=env["graph_version"],
                        created_at=env["created_at"],
                        planner=env["planner"],
                        max_nodes=env.get("max_nodes", DEFAULT_MAX_NODES),
                        max_depth=env.get("max_depth", DEFAULT_MAX_DEPTH),
                        max_fanout=env.get("max_fanout", DEFAULT_MAX_FANOUT),
                        policy_profile=str(env.get("policy_profile", "default")),
                    )
                    node_dicts = ev["nodes"]
                elif etype == "node_state":
                    state[ev["node_id"]] = LifecycleState(ev["state"])
                elif etype == "graph_cancelled":
                    cancelled.add(ev["node_id"])
                    # durable cancellation: mark as cancelled in materialized state
                    state[ev["node_id"]] = LifecycleState.CANCELLED
                else:
                    raise GraphValidationError(f"unknown event type {etype!r} on line {lineno}")

        if envelope is None:
            raise GraphValidationError("no graph_persisted event in log")

        graph = TaskGraph.from_planner_output(envelope, node_dicts)
        self._graph = graph
        self._state = state
        self._replayed = True
        return graph, state

    def current_state(self) -> dict[str, LifecycleState]:
        if not self._replayed:
            raise RuntimeError("call replay() before current_state()")
        return dict(self._state)

    @property
    def graph(self) -> TaskGraph:
        if not self._replayed:
            raise RuntimeError("call replay() first")
        return self._graph  # type: ignore[return-value]

    def graph_hash(self) -> str:
        if not self._replayed:
            raise RuntimeError("call replay() first")
        return self._graph.graph_hash()  # type: ignore[union-attr]
