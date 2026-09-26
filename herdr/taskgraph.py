"""Herdr v1.1 durable TaskGraph contract.

Canonical implementation for Bbambaaamm/herdr#2, migrated from the former
Autonomous-Quant-Lab#230 prototype after architecture hardening.

This module is deliberately consumer-agnostic. Consumer safety policies (for
example QuantLab PAPER-only) stay in the consumer repository and are carried
through tool/permission allowlists rather than hard-coded into Herdr core.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, ClassVar

GRAPH_VERSION = "1.1.0"

HARD_MAX_NODES = 256
HARD_MAX_DEPTH = 16
HARD_MAX_FANOUT = 16
HARD_MAX_TIMEOUT_SECONDS = 86_400
HARD_MAX_ATTEMPTS = 10

DEFAULT_MAX_NODES = 256
DEFAULT_MAX_DEPTH = 16
DEFAULT_MAX_FANOUT = 16
DEFAULT_TIMEOUT_SECONDS = 1_800
DEFAULT_MAX_ATTEMPTS = 1


class GraphValidationError(ValueError):
    """Planner/taskgraph data violated the fail-closed contract."""


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
    def terminal(cls) -> frozenset["LifecycleState"]:
        return frozenset({cls.DONE, cls.FAILED, cls.CANCELLED})


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _require_text(value: Any, field: str, *, max_len: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise GraphValidationError(f"{field} must be a non-empty string <= {max_len} chars")
    return value


def _validate_utc_timestamp(value: Any, field: str) -> str:
    value = _require_text(value, field, max_len=128)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GraphValidationError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise GraphValidationError(f"{field} must be UTC with an explicit offset")
    return value


def _validate_spec_hash(value: Any) -> str:
    value = _require_text(value, "envelope.spec_hash", max_len=80)
    raw = value.removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", raw):
        raise GraphValidationError("envelope.spec_hash must be lowercase SHA-256 hex")
    return value


def _validate_json(value: Any, path: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GraphValidationError(f"{path} contains a non-finite number")
        return
    if isinstance(value, list):
        for idx, item in enumerate(value):
            _validate_json(item, f"{path}[{idx}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise GraphValidationError(f"{path} contains a non-string object key")
            _validate_json(item, f"{path}.{key}")
        return
    raise GraphValidationError(f"{path} contains non-JSON type {type(value).__name__}")


_SECRET_KEY_FRAGMENTS = (
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

_SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
)


def _secret_hits(value: Any, path: str = "payload") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            normalized = key.lower()
            if any(fragment in normalized for fragment in _SECRET_KEY_FRAGMENTS):
                hits.append(child)
            hits.extend(_secret_hits(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            hits.extend(_secret_hits(item, f"{path}[{idx}]"))
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in _SECRET_VALUE_PATTERNS):
            hits.append(path)
    return hits


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _canonical_json(value: Any) -> str:
    _validate_json(value, "canonical")
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


@dataclass(frozen=True)
class TaskGraphEnvelope:
    issue: str
    spec_hash: str
    graph_version: str
    created_at: str
    planner: str
    max_nodes: int = DEFAULT_MAX_NODES
    max_depth: int = DEFAULT_MAX_DEPTH
    max_fanout: int = DEFAULT_MAX_FANOUT
    policy_profile: str = "default"

    def __post_init__(self) -> None:
        _require_text(self.issue, "envelope.issue", max_len=256)
        _validate_spec_hash(self.spec_hash)
        if self.graph_version != GRAPH_VERSION:
            raise GraphValidationError(
                f"unsupported graph_version {self.graph_version!r}; expected {GRAPH_VERSION!r}"
            )
        _validate_utc_timestamp(self.created_at, "envelope.created_at")
        _require_text(self.planner, "envelope.planner", max_len=256)
        _require_text(self.policy_profile, "envelope.policy_profile", max_len=128)
        limits = (
            ("max_nodes", self.max_nodes, HARD_MAX_NODES),
            ("max_depth", self.max_depth, HARD_MAX_DEPTH),
            ("max_fanout", self.max_fanout, HARD_MAX_FANOUT),
        )
        for name, value, hard_max in limits:
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= hard_max:
                raise GraphValidationError(
                    f"envelope.{name} must be an integer in 1..{hard_max}"
                )

    @classmethod
    def from_dict(cls, value: Any) -> "TaskGraphEnvelope":
        if not isinstance(value, dict):
            raise GraphValidationError("envelope must be an object")
        allowed = {
            "issue",
            "spec_hash",
            "graph_version",
            "created_at",
            "planner",
            "max_nodes",
            "max_depth",
            "max_fanout",
            "policy_profile",
        }
        unknown = set(value) - allowed
        if unknown:
            raise GraphValidationError(f"envelope contains unknown fields: {sorted(unknown)}")
        required = {"issue", "spec_hash", "graph_version", "created_at", "planner"}
        missing = required - set(value)
        if missing:
            raise GraphValidationError(f"envelope missing required fields: {sorted(missing)}")
        try:
            return cls(
                issue=value["issue"],
                spec_hash=value["spec_hash"],
                graph_version=value["graph_version"],
                created_at=value["created_at"],
                planner=value["planner"],
                max_nodes=value.get("max_nodes", DEFAULT_MAX_NODES),
                max_depth=value.get("max_depth", DEFAULT_MAX_DEPTH),
                max_fanout=value.get("max_fanout", DEFAULT_MAX_FANOUT),
                policy_profile=value.get("policy_profile", "default"),
            )
        except (TypeError, ValueError) as exc:
            if isinstance(exc, GraphValidationError):
                raise
            raise GraphValidationError(f"invalid envelope: {type(exc).__name__}") from exc

    def to_json(self) -> dict[str, Any]:
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

    def to_hash_json(self) -> dict[str, Any]:
        """Structural envelope. created_at is intentionally operational metadata."""
        value = self.to_json()
        value.pop("created_at")
        return value


@dataclass(frozen=True)
class TaskNode:
    id: str
    parent_id: str | None
    type: str
    role: str
    objective: str
    inputs: tuple[Mapping[str, Any], ...] | list[dict[str, Any]]
    expected_outputs: tuple[Mapping[str, Any], ...] | list[dict[str, Any]]
    dependencies: tuple[str, ...]
    priority: int
    resource_class: str
    model_policy: Mapping[str, Any] | dict[str, Any]
    tools: tuple[str, ...]
    permissions: tuple[str, ...]
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_attempts: int = DEFAULT_MAX_ATTEMPTS

    SECRET_KEY_FRAGMENTS: ClassVar[tuple[str, ...]] = _SECRET_KEY_FRAGMENTS

    def __post_init__(self) -> None:
        _require_text(self.id, "node.id", max_len=256)
        if self.parent_id is not None:
            _require_text(self.parent_id, "node.parent_id", max_len=256)
        _require_text(self.type, "node.type", max_len=128)
        _require_text(self.role, "node.role", max_len=128)
        _require_text(self.objective, "node.objective", max_len=16_384)
        _require_text(self.resource_class, "node.resource_class", max_len=128)
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise GraphValidationError("node.priority must be an integer")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, int)
            or not 1 <= self.timeout_seconds <= HARD_MAX_TIMEOUT_SECONDS
        ):
            raise GraphValidationError(
                f"node.timeout_seconds must be an integer in 1..{HARD_MAX_TIMEOUT_SECONDS}"
            )
        if (
            isinstance(self.max_attempts, bool)
            or not isinstance(self.max_attempts, int)
            or not 1 <= self.max_attempts <= HARD_MAX_ATTEMPTS
        ):
            raise GraphValidationError(
                f"node.max_attempts must be an integer in 1..{HARD_MAX_ATTEMPTS}"
            )
        for name, values in (
            ("dependencies", self.dependencies),
            ("tools", self.tools),
            ("permissions", self.permissions),
        ):
            if any(not isinstance(item, str) or not item for item in values):
                raise GraphValidationError(f"node.{name} must contain non-empty strings")
            if len(set(values)) != len(values):
                raise GraphValidationError(f"node.{name} must not contain duplicates")
        if not isinstance(self.inputs, (list, tuple)) or not all(
            isinstance(x, Mapping) for x in self.inputs
        ):
            raise GraphValidationError("node.inputs must be an array of objects")
        if not isinstance(self.expected_outputs, (list, tuple)) or not all(
            isinstance(x, Mapping) for x in self.expected_outputs
        ):
            raise GraphValidationError("node.expected_outputs must be an array of objects")
        if not isinstance(self.model_policy, Mapping):
            raise GraphValidationError("node.model_policy must be an object")
        payload = {
            "inputs": [dict(item) for item in self.inputs],
            "expected_outputs": [dict(item) for item in self.expected_outputs],
            "model_policy": dict(self.model_policy),
        }
        _validate_json(payload, f"node[{self.id}].payload")
        hits = _secret_hits(payload, f"node[{self.id}].payload")
        if hits:
            raise GraphValidationError(
                f"node {self.id!r}: secret-like material rejected at {sorted(set(hits))}"
            )
        object.__setattr__(self, "inputs", tuple(_freeze_json(item) for item in payload["inputs"]))
        object.__setattr__(
            self,
            "expected_outputs",
            tuple(_freeze_json(item) for item in payload["expected_outputs"]),
        )
        object.__setattr__(self, "model_policy", _freeze_json(payload["model_policy"]))

    @classmethod
    def from_dict(cls, value: Any) -> "TaskNode":
        if not isinstance(value, dict):
            raise GraphValidationError("node must be an object")
        allowed = {
            "id",
            "parent_id",
            "type",
            "role",
            "objective",
            "inputs",
            "expected_outputs",
            "dependencies",
            "priority",
            "resource_class",
            "model_policy",
            "tools",
            "permissions",
            "timeout_seconds",
            "max_attempts",
        }
        unknown = set(value) - allowed
        if unknown:
            raise GraphValidationError(
                f"node {value.get('id', '<unknown>')!r} contains unknown fields: {sorted(unknown)}"
            )
        required = {
            "id",
            "parent_id",
            "type",
            "role",
            "objective",
            "inputs",
            "expected_outputs",
            "dependencies",
            "priority",
            "resource_class",
            "model_policy",
            "tools",
            "permissions",
        }
        missing = required - set(value)
        if missing:
            raise GraphValidationError(
                f"node {value.get('id', '<unknown>')!r} missing required fields: {sorted(missing)}"
            )
        for field_name in ("dependencies", "tools", "permissions"):
            if not isinstance(value[field_name], list):
                raise GraphValidationError(f"node.{field_name} must be an array")
        try:
            return cls(
                id=value["id"],
                parent_id=value["parent_id"],
                type=value["type"],
                role=value["role"],
                objective=value["objective"],
                inputs=value["inputs"],
                expected_outputs=value["expected_outputs"],
                dependencies=tuple(value["dependencies"]),
                priority=value["priority"],
                resource_class=value["resource_class"],
                model_policy=value["model_policy"],
                tools=tuple(value["tools"]),
                permissions=tuple(value["permissions"]),
                timeout_seconds=value.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
                max_attempts=value.get("max_attempts", DEFAULT_MAX_ATTEMPTS),
            )
        except (TypeError, ValueError) as exc:
            if isinstance(exc, GraphValidationError):
                raise
            raise GraphValidationError(
                f"node {value.get('id', '<unknown>')!r} has malformed field types"
            ) from exc

    def verify_descendant_permissions(self, parent: "TaskNode") -> None:
        extra_tools = set(self.tools) - set(parent.tools)
        extra_permissions = set(self.permissions) - set(parent.permissions)
        if extra_tools or extra_permissions:
            details: list[str] = []
            if extra_tools:
                details.append(f"tools={sorted(extra_tools)}")
            if extra_permissions:
                details.append(f"permissions={sorted(extra_permissions)}")
            raise GraphValidationError(
                f"node {self.id!r}: child escalation above parent {parent.id!r}: "
                + ", ".join(details)
            )

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "type": self.type,
            "role": self.role,
            "objective": self.objective,
            "inputs": _thaw_json(self.inputs),
            "expected_outputs": _thaw_json(self.expected_outputs),
            "dependencies": list(self.dependencies),
            "priority": self.priority,
            "resource_class": self.resource_class,
            "model_policy": _thaw_json(self.model_policy),
            "tools": list(self.tools),
            "permissions": list(self.permissions),
            "timeout_seconds": self.timeout_seconds,
            "max_attempts": self.max_attempts,
        }

    def to_hash_json(self) -> dict[str, Any]:
        value = self.to_json()
        value["dependencies"] = sorted(self.dependencies)
        value["tools"] = sorted(self.tools)
        value["permissions"] = sorted(self.permissions)
        return value


@dataclass(frozen=True)
class NodeRuntimeState:
    lifecycle: LifecycleState = LifecycleState.PENDING
    attempt: int = 0
    lease_id: str | None = None
    lease_expires_at: str | None = None

    def validate_for(self, node: TaskNode) -> None:
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int):
            raise GraphValidationError("runtime attempt must be an integer")
        if not 0 <= self.attempt <= node.max_attempts:
            raise GraphValidationError(
                f"runtime attempt for {node.id!r} must be in 0..{node.max_attempts}"
            )
        if (self.lease_id is None) != (self.lease_expires_at is None):
            raise GraphValidationError("lease_id and lease_expires_at must be set together")
        if self.lease_id is not None:
            _require_text(self.lease_id, "runtime.lease_id", max_len=256)
            _validate_utc_timestamp(self.lease_expires_at, "runtime.lease_expires_at")

    def to_json(self) -> dict[str, Any]:
        return {
            "lifecycle": self.lifecycle.value,
            "attempt": self.attempt,
            "lease_id": self.lease_id,
            "lease_expires_at": self.lease_expires_at,
        }

    @classmethod
    def from_dict(cls, value: Any, node: TaskNode) -> "NodeRuntimeState":
        if not isinstance(value, dict):
            raise GraphValidationError("runtime must be an object")
        unknown = set(value) - {"lifecycle", "attempt", "lease_id", "lease_expires_at"}
        if unknown:
            raise GraphValidationError(f"runtime contains unknown fields: {sorted(unknown)}")
        try:
            state = cls(
                lifecycle=LifecycleState(value["lifecycle"]),
                attempt=value.get("attempt", 0),
                lease_id=value.get("lease_id"),
                lease_expires_at=value.get("lease_expires_at"),
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise GraphValidationError(f"invalid runtime state for node {node.id!r}") from exc
        state.validate_for(node)
        return state


@dataclass
class TaskGraph:
    envelope: TaskGraphEnvelope
    nodes: tuple[TaskNode, ...]

    @classmethod
    def parse_planner_output(cls, value: Any) -> "TaskGraph":
        if not isinstance(value, dict):
            raise GraphValidationError("planner output must be an object")
        unknown = set(value) - {"envelope", "nodes"}
        if unknown:
            raise GraphValidationError(f"planner output contains unknown fields: {sorted(unknown)}")
        if "envelope" not in value or "nodes" not in value:
            raise GraphValidationError("planner output requires envelope and nodes")
        envelope = TaskGraphEnvelope.from_dict(value["envelope"])
        return cls.from_planner_output(envelope, value["nodes"])

    @classmethod
    def from_planner_output(
        cls, envelope: TaskGraphEnvelope, node_dicts: Any
    ) -> "TaskGraph":
        if not isinstance(node_dicts, list):
            raise GraphValidationError("nodes must be an array")
        if not node_dicts:
            raise GraphValidationError("nodes must contain at least one node")
        if len(node_dicts) > envelope.max_nodes:
            raise GraphValidationError(
                f"max_nodes ({envelope.max_nodes}) exceeded: {len(node_dicts)} nodes"
            )
        nodes = tuple(TaskNode.from_dict(value) for value in node_dicts)
        graph = cls(envelope=envelope, nodes=nodes)
        graph._validate()
        return graph

    def _index(self) -> dict[str, TaskNode]:
        result: dict[str, TaskNode] = {}
        for node in self.nodes:
            if node.id in result:
                raise GraphValidationError(f"duplicate node id rejected: {node.id!r}")
            result[node.id] = node
        return result

    def _validate(self) -> None:
        idx = self._index()
        for node in self.nodes:
            if node.parent_id is not None:
                if node.parent_id == node.id:
                    raise GraphValidationError(f"node {node.id!r}: self-parent rejected")
                if node.parent_id not in idx:
                    raise GraphValidationError(
                        f"node {node.id!r}: unknown parent {node.parent_id!r} rejected"
                    )
            for dep in node.dependencies:
                if dep == node.id:
                    raise GraphValidationError(f"node {node.id!r}: self-dependency rejected")
                if dep not in idx:
                    raise GraphValidationError(
                        f"node {node.id!r}: unknown dependency {dep!r} rejected"
                    )
        self._validate_dependency_dag(idx)
        self._validate_hierarchy(idx)
        for node in self.nodes:
            if node.parent_id is not None:
                node.verify_descendant_permissions(idx[node.parent_id])

    def _validate_dependency_dag(self, idx: dict[str, TaskNode]) -> None:
        white, gray, black = 0, 1, 2
        color = {node_id: white for node_id in idx}

        def visit(node_id: str) -> None:
            color[node_id] = gray
            for dep in idx[node_id].dependencies:
                if color[dep] == gray:
                    raise GraphValidationError("dependency cycle detected")
                if color[dep] == white:
                    visit(dep)
            color[node_id] = black

        for node_id in idx:
            if color[node_id] == white:
                visit(node_id)

    def _validate_hierarchy(self, idx: dict[str, TaskNode]) -> None:
        cache: dict[str, int] = {}

        def depth(node_id: str, visiting: set[str]) -> int:
            if node_id in cache:
                return cache[node_id]
            if node_id in visiting:
                raise GraphValidationError("parent hierarchy cycle detected")
            visiting.add(node_id)
            parent_id = idx[node_id].parent_id
            result = 1 if parent_id is None else 1 + depth(parent_id, visiting)
            visiting.remove(node_id)
            cache[node_id] = result
            return result

        fanout: dict[str, int] = {}
        for node in self.nodes:
            if depth(node.id, set()) > self.envelope.max_depth:
                raise GraphValidationError(
                    f"max_depth ({self.envelope.max_depth}) exceeded by node {node.id!r}"
                )
            if node.parent_id is not None:
                fanout[node.parent_id] = fanout.get(node.parent_id, 0) + 1
        over = sorted(
            parent for parent, count in fanout.items() if count > self.envelope.max_fanout
        )
        if over:
            raise GraphValidationError(
                f"max_fanout ({self.envelope.max_fanout}) exceeded for parents: {over}"
            )

    def graph_hash(self) -> str:
        payload = {
            "envelope": self.envelope.to_hash_json(),
            "nodes": [node.to_hash_json() for node in sorted(self.nodes, key=lambda n: n.id)],
        }
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

    def dependency_edges(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            sorted((dep, node.id) for node in self.nodes for dep in node.dependencies)
        )

    def hierarchy_edges(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            sorted(
                (node.parent_id, node.id)
                for node in self.nodes
                if node.parent_id is not None
            )
        )

    def to_planner_json(self) -> dict[str, Any]:
        return {
            "envelope": self.envelope.to_json(),
            "nodes": [node.to_json() for node in self.nodes],
        }


class _DuplicateKey(ValueError):
    pass


def _strict_json_loads(raw: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise _DuplicateKey(key)
            result[key] = value
        return result

    def bad_constant(value: str) -> None:
        raise ValueError(value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)


class PersistentTaskGraph:
    """Single-writer append-only JSONL log for one TaskGraph.

    Complete events are fsync'd. A final non-newline-terminated fragment is
    treated as a torn crash-tail and ignored during replay; malformed complete
    events fail closed. Every runtime event is bound to the graph hash.
    """

    def __init__(self, path: str | os.PathLike[str]):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._graph: TaskGraph | None = None
        self._state: dict[str, NodeRuntimeState] = {}

    def _append(self, event: dict[str, Any]) -> None:
        payload = (_canonical_json(event) + "\n").encode("utf-8")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            fd = os.open(self._path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("short write to taskgraph event log")
                    view = view[written:]
                os.fsync(fd)
            finally:
                os.close(fd)

    def _require_loaded(self) -> TaskGraph:
        if self._graph is None:
            raise RuntimeError("persist_graph() or replay() must be called first")
        return self._graph

    def persist_graph(self, graph: TaskGraph) -> None:
        if self._path.exists() and self._path.stat().st_size:
            raise GraphValidationError("taskgraph log is already initialized")
        event = {
            "type": "graph_persisted",
            "graph_hash": graph.graph_hash(),
            "graph": graph.to_planner_json(),
            "ts": _utc_now(),
        }
        self._append(event)
        self._graph = graph
        self._state = {node.id: NodeRuntimeState() for node in graph.nodes}

    def set_node_runtime(self, node_id: str, runtime: NodeRuntimeState) -> None:
        graph = self._require_loaded()
        idx = graph._index()
        if node_id not in idx:
            raise GraphValidationError(f"runtime event references unknown node {node_id!r}")
        runtime.validate_for(idx[node_id])
        event = {
            "type": "node_runtime",
            "graph_hash": graph.graph_hash(),
            "node_id": node_id,
            "runtime": runtime.to_json(),
            "ts": _utc_now(),
        }
        self._append(event)
        self._state[node_id] = runtime

    def set_node_state(self, node_id: str, state: LifecycleState) -> None:
        graph = self._require_loaded()
        if node_id not in self._state:
            raise GraphValidationError(f"runtime event references unknown node {node_id!r}")
        current = self._state[node_id]
        self.set_node_runtime(
            node_id,
            NodeRuntimeState(
                lifecycle=state,
                attempt=current.attempt,
                lease_id=current.lease_id,
                lease_expires_at=current.lease_expires_at,
            ),
        )

    def cancel_node(self, node_id: str, reason: str) -> None:
        graph = self._require_loaded()
        if node_id not in self._state:
            raise GraphValidationError(f"cancel event references unknown node {node_id!r}")
        _require_text(reason, "cancel.reason", max_len=2048)
        if _secret_hits(reason, "cancel.reason"):
            raise GraphValidationError("cancel.reason contains secret-like material")
        current = self._state[node_id]
        runtime = NodeRuntimeState(
            lifecycle=LifecycleState.CANCELLED,
            attempt=current.attempt,
            lease_id=None,
            lease_expires_at=None,
        )
        runtime.validate_for(graph._index()[node_id])
        self._append(
            {
                "type": "node_cancelled",
                "graph_hash": graph.graph_hash(),
                "node_id": node_id,
                "runtime": runtime.to_json(),
                "reason": reason,
                "ts": _utc_now(),
            }
        )
        self._state[node_id] = runtime

    def replay(self) -> tuple[TaskGraph, dict[str, NodeRuntimeState]]:
        if not self._path.exists():
            raise FileNotFoundError(f"event log not found: {self._path}")
        raw = self._path.read_bytes()
        if not raw:
            raise GraphValidationError("event log is empty")
        complete = raw
        if not raw.endswith(b"\n"):
            cut = raw.rfind(b"\n")
            complete = b"" if cut < 0 else raw[: cut + 1]
        if not complete:
            raise GraphValidationError("event log contains no complete events")

        graph: TaskGraph | None = None
        graph_hash: str | None = None
        state: dict[str, NodeRuntimeState] = {}
        graph_seen = False

        for lineno, line in enumerate(complete.splitlines(), 1):
            if not line.strip():
                continue
            try:
                event = _strict_json_loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError, _DuplicateKey) as exc:
                raise GraphValidationError(f"malformed complete event on line {lineno}") from exc
            if not isinstance(event, dict):
                raise GraphValidationError(f"event on line {lineno} must be an object")
            _validate_utc_timestamp(event.get("ts"), f"event[{lineno}].ts")
            etype = event.get("type")
            if etype == "graph_persisted":
                if graph_seen:
                    raise GraphValidationError("multiple graph_persisted events in one log")
                if lineno != 1:
                    raise GraphValidationError("graph_persisted must be the first event")
                graph = TaskGraph.parse_planner_output(event.get("graph"))
                graph_hash = graph.graph_hash()
                if event.get("graph_hash") != graph_hash:
                    raise GraphValidationError("persisted graph hash mismatch")
                state = {node.id: NodeRuntimeState() for node in graph.nodes}
                graph_seen = True
                continue

            if not graph_seen or graph is None or graph_hash is None:
                raise GraphValidationError("runtime event precedes graph_persisted")
            if event.get("graph_hash") != graph_hash:
                raise GraphValidationError(f"event on line {lineno} targets a different graph hash")
            node_id = event.get("node_id")
            idx = graph._index()
            if node_id not in idx:
                raise GraphValidationError(
                    f"event on line {lineno} references unknown node {node_id!r}"
                )
            if etype == "node_runtime":
                state[node_id] = NodeRuntimeState.from_dict(event.get("runtime"), idx[node_id])
            elif etype == "node_cancelled":
                runtime = NodeRuntimeState.from_dict(event.get("runtime"), idx[node_id])
                if runtime.lifecycle is not LifecycleState.CANCELLED:
                    raise GraphValidationError("node_cancelled event must materialize cancelled state")
                reason = _require_text(event.get("reason"), "cancel.reason", max_len=2048)
                if _secret_hits(reason, "cancel.reason"):
                    raise GraphValidationError("cancel.reason contains secret-like material")
                state[node_id] = runtime
            else:
                raise GraphValidationError(f"unknown event type {etype!r} on line {lineno}")

        if graph is None:
            raise GraphValidationError("no graph_persisted event in log")
        self._graph = graph
        self._state = state
        return graph, dict(state)

    def current_state(self) -> dict[str, NodeRuntimeState]:
        self._require_loaded()
        return dict(self._state)

    @property
    def graph(self) -> TaskGraph:
        return self._require_loaded()

    def graph_hash(self) -> str:
        return self._require_loaded().graph_hash()
