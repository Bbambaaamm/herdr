"""Herdr v1.2 consumer-neutral scheduler with dependency-aware dispatch,
leases plus monotonic fencing, bounded dynamic child proposals, and
fail-closed restart/replay recovery.

Adapted from the Autonomous-Quant-Lab PR #244 scheduler/runtime candidate
(head 7adf513) and ported to use the canonical herdr v1.1 TaskNode/TaskGraph
contract from herdr/taskgraph.py (issue #2).

Consumer safety policies (QuantLab PAPER-only, live-trading denial, etc.)
are carried through a configurable ConsumerPolicy hook, not hard-coded into
Herdr core.
"""

from __future__ import annotations

import json
import os
import hashlib
import uuid
import re
import subprocess
import threading
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Protocol

from herdr.telemetry import CostUnknownReason, EventType, TelemetryStore, new_event
from herdr.taskgraph import (
    GRAPH_VERSION,
    GraphValidationError,
    LifecycleState,
    TaskGraph,
    TaskGraphEnvelope,
    TaskNode,
)

from herdr.child_ownership import ChildOwnership, OwnershipRegistry, OwnershipError

HERE = Path(__file__).resolve().parent
EVENT_LOG_NAME = "herdr-scheduler-events.jsonl"
SWARM_SNAPSHOT_NAME = "swarm.json"


# ---------------------------------------------------------------------------
# Denial taxonomy — generic reasons only, no consumer-specific constants
# ---------------------------------------------------------------------------


class DenyReason(StrEnum):
    DAG_NODE_LIMIT = "dag_node_limit"
    DAG_DEPTH_LIMIT = "dag_depth_limit"
    DAG_FANOUT_LIMIT = "dag_fanout_limit"
    DAG_CYCLE = "dag_cycle"
    CHILD_TOOL_ESCALATION = "child_tool_escalation"
    CHILD_PERMISSION_ESCALATION = "child_permission_escalation"
    CHILD_ROLE_ESCALATION = "child_role_escalation"
    TOOL_NOT_IN_ROLE_ALLOWLIST = "tool_not_in_role_allowlist"
    NON_SPAWNABLE_ROLE = "non_spawnable_role"
    PER_ISSUE_LIMIT = "per_issue_limit"
    PER_REPO_LIMIT = "per_repo_limit"
    GLOBAL_CONCURRENCY_LIMIT = "global_concurrency_limit"
    STALE_FENCE = "stale_fence"
    ALREADY_CLAIMED = "already_claimed"
    UNKNOWN_TASK = "unknown_task"
    CONSUMER_POLICY_DENIED = "consumer_policy_denied"
    RECORD_EMPTY = "record_empty"


class AllowDecision:
    def __init__(self, model: str = "laguna", fallback_model: str = "longcat") -> None:
        self.model = model
        self.fallback_model = fallback_model

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"AllowDecision(model={self.model!r}, fallback_model={self.fallback_model!r})"


class DenyDecision:
    def __init__(self, reason: DenyReason, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"DenyDecision(reason={self.reason.value!r}, detail={self.detail!r})"


# ---------------------------------------------------------------------------
# Consumer policy hook — fail-closed by default
# ---------------------------------------------------------------------------


class ConsumerPolicy(Protocol):
    def evaluate_child_proposal(
        self, proposal: "ChildProposal"
    ) -> AllowDecision | DenyDecision: ...


class _DefaultConsumerPolicy:
    ROLE_TOOL_ALLOWLIST: ClassVar[dict[str, set[str]]] = {
        "reader": frozenset({"herdr_submit_result", "read_file", "search_files", "read"}),
        "writer": frozenset(
            {"herdr_submit_result", "read_file", "search_files", "read", "patch", "write_file", "write"}
        ),
        "reviewer": frozenset(
            {
                "herdr_submit_result", "read_file",
                "search_files",
                "read",
                "patch",
                "write_file",
                "write",
                "review",
            }
        ),
    }
    ROLE_RANK: ClassVar[dict[str, int]] = {
        "reader": 1,
        "writer": 2,
        "reviewer": 3,
        "operator": 4,
    }
    SPAWNABLE_ROLES: ClassVar[frozenset[str]] = frozenset(
        {"reader", "writer", "reviewer"}
    )

    def evaluate_child_proposal(
        self, proposal: ChildProposal
    ) -> AllowDecision | DenyDecision:
        if proposal.child_role not in self.SPAWNABLE_ROLES:
            return DenyDecision(DenyReason.NON_SPAWNABLE_ROLE)
        child_tools = set(proposal.child_tools)
        if self.ROLE_RANK.get(proposal.child_role, 0) > self.ROLE_RANK.get(
            proposal.parent_role, 0
        ):
            return DenyDecision(
                DenyReason.CHILD_ROLE_ESCALATION,
                detail=f"child role {proposal.child_role} > parent role {proposal.parent_role}",
            )
        role_tools = self.ROLE_TOOL_ALLOWLIST.get(proposal.child_role, frozenset())
        outside_role = child_tools - role_tools
        if outside_role:
            return DenyDecision(
                DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST,
                detail=f"tools not in allowlist for {proposal.child_role}: {sorted(outside_role)}",
            )
        outside_parent = child_tools - set(proposal.parent_tools)
        if outside_parent:
            return DenyDecision(
                DenyReason.CHILD_TOOL_ESCALATION,
                detail=f"child tools above parent: {sorted(outside_parent)}",
            )
        outside_permissions = set(proposal.child_permissions) - set(proposal.parent_permissions)
        if outside_permissions:
            return DenyDecision(
                DenyReason.CHILD_PERMISSION_ESCALATION,
                detail=f"child permissions above parent: {sorted(outside_permissions)}",
            )
        if self.ROLE_RANK.get(proposal.child_role, 0) > self.ROLE_RANK.get(
            proposal.parent_role, 0
        ):
            return DenyDecision(
                DenyReason.CHILD_ROLE_ESCALATION,
                detail=f"child role {proposal.child_role} > parent role {proposal.parent_role}",
            )
        role_tools = self.ROLE_TOOL_ALLOWLIST.get(proposal.child_role, frozenset())
        outside_role = child_tools - role_tools
        if outside_role:
            return DenyDecision(
                DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST,
                detail=f"tools not in allowlist for {proposal.child_role}: {sorted(outside_role)}",
            )
        return AllowDecision(proposal.child_model, proposal.child_fallback_model)


# ---------------------------------------------------------------------------
# Budget and proposal types
# ---------------------------------------------------------------------------


@dataclass
class SchedulerBudget:
    max_global_concurrency: int = 4
    max_per_repo: int = 4
    max_per_issue: int = 3
    max_dag_nodes: int = 256
    max_dag_depth: int = 16
    max_dag_fanout: int = 6
    claim_ttl_seconds: float = 1800.0


@dataclass(frozen=True)
class ChildProposal:
    parent_role: str
    parent_tools: tuple[str, ...]
    child_role: str
    child_tools: tuple[str, ...]
    child_task: str = ""
    child_model: str = "laguna"
    child_fallback_model: str = "longcat"
    parent_permissions: tuple[str, ...] = ()
    child_permissions: tuple[str, ...] = ()
    worktree_identity: str = ""
    ownership: ChildOwnership | None = None

    def __post_init__(self):
        if self.ownership is not None and not isinstance(self.ownership,ChildOwnership):
            raise SchedulerError("typed child ownership required")


@dataclass(frozen=True)
class Lease:
    task_id: str
    agent_id: str
    holder: str
    fencing_token: int
    lease_until: float


# Compatibility names retained for the production runtime bridge while the
# canonical public contract uses ChildProposal and Lease.
SubtaskProposal = ChildProposal

@dataclass(frozen=True)
class _Lease:
    """Legacy positional lease shape used by older runtime tests/callers."""
    task_id: str
    holder: str
    agent_id: str
    lease_until: float
    fencing_token: int


class SchedulerError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


class AuditLog:
    """Append-only JSONL audit log for replay/recovery."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._buffer: list[dict[str, object]] = []

    def append(self, event: dict[str, object]) -> None:
        with self._lock:
            self._buffer.append(event)

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            events = self._buffer
            self._buffer = []
            payload = (json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n" for e in events)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.writelines(payload)
                fh.flush()
                os.fsync(fh.fileno())
            directory = os.open(self._path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)

    def replay(self) -> list[dict[str, object]]:
        if not self._path.exists():
            return list(self._buffer)
        with open(self._path, "r", encoding="utf-8") as fh:
            lines = [json.loads(line) for line in fh if line.strip()]
        return lines + list(self._buffer)

    def record_count(self) -> int:
        return len(self.replay())


# ---------------------------------------------------------------------------
# TaskRecord — runtime state per node
# ---------------------------------------------------------------------------


@dataclass
class TaskRecord:
    node: TaskNode
    state: LifecycleState = LifecycleState.PENDING
    lease: Lease | None = None
    fencing_token: int | None = None
    model_used: str | None = None
    fallback_used: str | None = None
    telemetry: list[dict[str, object]] = field(default_factory=list)
    attempts: int = 0
    blocker: str | None = None
    parent_task_id: str | None = None
    parent_agent_id: str | None = None
    agent_id: str | None = None
    repo: str = "default"
    issue: str = ""
    policy_profile: str = "default"
    submitted_at: float | None = None
    started_at: float | None = None
    id: str | None = None  # set from node.id after submit
    delegation_key: str | None = None
    idempotency_key: str | None = None
    parent_run_token: str | None = None
    run_token: str | None = None
    attempt_state: str = "dispatching"
    observed_execution: str = "unavailable"
    observation_source: str | None = None
    observed_at: str | None = None
    execution_agent: str | None = None
    execution_pane: str | None = None
    execution_marker: str | None = None
    execution_sandbox_verified: bool = False
    execution_sandbox_attestation: dict[str, object] | None = None
    worktree_identity: str = ""
    ownership: ChildOwnership | None = None
    ownership_reservation: str | None = None
    owned_write_mounts: tuple[dict, ...] | None = None
    cleanup_complete: bool = False
    pre_delivery_failure: str | None = None
    pre_delivery_agent_start_attempted: bool = False
    economic_delivery_attempted: bool | None = None
    pre_delivery_pane_creation_attempted: bool = False
    pane_split_started: bool | None = None
    delivery_prompt_sha256: str | None = None
    result_status: str | None = None
    result_artifact_sha256: str | None = None
    result_evidence_canonical: bytes | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", self.node.id)


# ---------------------------------------------------------------------------
# DynamicChildScheduler
# ---------------------------------------------------------------------------


class DynamicChildScheduler:
    """Dependency-aware scheduler with leases, fencing, child lifecycle,
    concurrency caps, replay/recovery, and deterministic snapshots.

    Adapted from Autonomous-Quant-Lab PR #244 (head 7adf513) and ported to
    the canonical herdr v1.1 TaskNode/TaskGraph contract.
    """

    def __init__(
        self,
        budget: SchedulerBudget | None = None,
        clock: Callable[[], float] | None = None,
        audit_log: AuditLog | None = None,
        consumer_policy: ConsumerPolicy | None = None,
        telemetry_store: TelemetryStore | None = None,
        execution_verifier: Callable[[str, str, str], str] | None = None,
        ownership_registry: OwnershipRegistry | None = None,
        ownership_parent=None,
    ) -> None:
        self.budget = budget or SchedulerBudget(
            max_global_concurrency=4,
            max_per_repo=4,
            max_per_issue=3,
            max_dag_nodes=256,
            max_dag_depth=16,
            max_dag_fanout=6,
            claim_ttl_seconds=1800.0,
        )
        self.clock = clock or __import__("time").time
        self.audit_log = audit_log or AuditLog(HERE / EVENT_LOG_NAME)
        self.consumer_policy = consumer_policy or _DefaultConsumerPolicy()
        self.telemetry_store = telemetry_store
        self.execution_verifier = execution_verifier
        from .security import InvocationIdentity
        if (ownership_registry is None) != (ownership_parent is None):
            raise SchedulerError("ownership registry and verified parent required together")
        if ownership_registry is not None and (not isinstance(ownership_registry,OwnershipRegistry)
                or not isinstance(ownership_parent,InvocationIdentity)):
            raise SchedulerError("typed host ownership authority required")
        self.ownership_registry,self.ownership_parent=ownership_registry,ownership_parent
        self._tasks: dict[str, TaskRecord] = {}
        self._claims: dict[str, Lease] = {}
        self._next_agent_id_value: int = 1
        self._next_agent_id_lock = threading.Lock()
        self._next_fencing_token_value: int = 1
        self._next_fencing_token_lock = threading.Lock()
        self._repo_counter: dict[str, int] = defaultdict(int)
        self._repo_counter_lock = threading.Lock()
        self._graph_latency: float = 0.0
        self._plan_max_nodes = self.budget.max_dag_nodes
        self._plan_max_depth = self.budget.max_dag_depth
        self._plan_max_fanout = self.budget.max_dag_fanout

    @staticmethod
    def _safe_telemetry_token(value: str | None, fallback: str) -> str | None:
        if value is None:
            return None
        if re.fullmatch(r"[A-Za-z0-9._:/@+-]{1,256}", value):
            return value
        return fallback

    @staticmethod
    def _telemetry_result_sha(result: str) -> str | None:
        return result if re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", result) else None

    def _emit_task_telemetry(
        self,
        rec: TaskRecord,
        event_type: EventType,
        *,
        state: str | None = None,
        reason: str | None = None,
        runtime_ms: int | None = None,
        queue_wait_ms: int | None = None,
        result_sha: str | None = None,
        retry_count: int = 0,
        blocker: str | None = None,
        moment: float | None = None,
    ) -> None:
        if self.telemetry_store is None:
            return
        agent_id = rec.agent_id or (rec.lease.agent_id if rec.lease is not None else None)
        if not rec.issue or agent_id is None:
            raise SchedulerError("telemetry requires issue and agent identity")
        observed_at = self.clock() if moment is None else moment
        self.telemetry_store.append(
            new_event(
                event_type=event_type,
                issue=rec.issue,
                task_id=rec.node.id,
                parent_task_id=rec.parent_task_id,
                agent_id=agent_id,
                role=rec.node.role,
                attempt=rec.attempts,
                timestamp=datetime.fromtimestamp(observed_at, UTC).isoformat(),
                state=state,
                reason=self._safe_telemetry_token(reason, "event"),
                runtime_ms=runtime_ms,
                queue_wait_ms=queue_wait_ms,
                result_sha=result_sha,
                retry_count=retry_count,
                blocker=self._safe_telemetry_token(blocker, "blocked"),
                cost_unknown_reason=CostUnknownReason.NON_BILLABLE,
            )
        )

    # -- submission ----------------------------------------------------------

    def submit(
        self,
        graph: TaskGraph,
        *,
        repo: str = "Bbambaaamm/Autonomous-Quant-Lab",
        issue: str = "",
    ) -> None:
        if not isinstance(graph, TaskGraph):
            raise SchedulerError("submit requires a TaskGraph")
        if not graph.nodes:
            self._deny(DenyReason.RECORD_EMPTY, "graph has no nodes")
            return
        effective_max_nodes = min(self.budget.max_dag_nodes, graph.envelope.max_nodes)
        effective_max_depth = min(self.budget.max_dag_depth, graph.envelope.max_depth)
        effective_max_fanout = min(self.budget.max_dag_fanout, graph.envelope.max_fanout)
        if len(graph.nodes) > effective_max_nodes:
            self._deny(
                DenyReason.DAG_NODE_LIMIT,
                detail=f"graph has {len(graph.nodes)} nodes; limit is {effective_max_nodes}",
            )
            return
        self._plan_max_nodes = min(self._plan_max_nodes, effective_max_nodes)
        self._plan_max_depth = min(self._plan_max_depth, effective_max_depth)
        self._plan_max_fanout = min(self._plan_max_fanout, effective_max_fanout)
        # Validate graph (catches cycles, unknown deps, etc.)
        try:
            graph._validate()
        except GraphValidationError as exc:
            raise SchedulerError(f"graph validation failed: {exc}") from exc
        now = datetime.now(UTC).isoformat()
        for node in graph.nodes:
            if node.id in self._tasks:
                raise SchedulerError(f"duplicate task id: {node.id}")
            rec = TaskRecord(
                node=node,
                parent_task_id=node.parent_id,
                repo=repo,
                issue=issue,
                policy_profile=graph.envelope.policy_profile,
                model_used=node.model_policy.get("model")
                if isinstance(node.model_policy, Mapping)
                else None,
                fallback_used=node.model_policy.get("fallback_model")
                if isinstance(node.model_policy, Mapping)
                else None,
            )
            rec.submitted_at = self.clock()
            self._tasks[node.id] = rec
            agent_id_str = f"agent-{self._next_agent_id()}"
            rec.lease = Lease(
                task_id=node.id,
                agent_id=agent_id_str,
                holder=agent_id_str,
                fencing_token=self._next_fencing_token(),
                lease_until=self.clock() + self.budget.claim_ttl_seconds,
            )
            self._claims[node.id] = rec.lease
            rec.state = LifecycleState.PENDING
            rec.agent_id = rec.lease.agent_id
            rec.fencing_token = rec.lease.fencing_token
            self._claims[node.id] = rec.lease
            rec.telemetry.append(
                {
                    "event": "submit",
                    "model": rec.model_used,
                    "fallback_model": rec.fallback_used,
                    "ts": now,
                }
            )
            self.audit_log.append(
                {
                    "event": "submit",
                    "task_id": node.id,
                    "repo": repo,
                    "issue": issue,
                    "agent_id": rec.agent_id,
                    "fencing_token": rec.fencing_token,
                    "parent_agent_id": None,
                    "dependencies": list(node.dependencies),
                    "parent_id": node.parent_id,
                    "model": rec.model_used,
                    "fallback_model": rec.fallback_used,
                    "telemetry": [],
                    "state": LifecycleState.PENDING.value,
                    "tools": list(node.tools),
                    "permissions": list(node.permissions),
                    "role": node.role,
                    "timeout_seconds": node.timeout_seconds,
                    "max_attempts": node.max_attempts,
                    "graph_version": GRAPH_VERSION,
                    "policy_profile": graph.envelope.policy_profile,
                    "ts": now,
                }
            )
            self._emit_task_telemetry(
                rec,
                EventType.TASK_STATE,
                state=LifecycleState.PENDING.value,
                moment=rec.submitted_at,
            )
        self.audit_log.append(
            {
                "event": "graph_submit",
                "repo": repo,
                "issue": issue,
                "node_count": len(graph.nodes),
                "graph_hash": graph.graph_hash(),
                "ts": now,
            }
        )

    def submit_taskgraph_contract(
        self,
        contract: TaskGraph | Mapping[str, object],
        *,
        repo: str = "Bbambaaamm/Autonomous-Quant-Lab",
        issue: str = "",
    ) -> None:
        """Submit canonical TaskGraph or a validated envelope.nodes mapping."""
        if isinstance(contract, TaskGraph):
            self.submit(contract, repo=repo, issue=issue or contract.envelope.issue)
            return
        if (
            not isinstance(contract, Mapping)
            or "envelope" not in contract
            or "nodes" not in contract
        ):
            raise SchedulerError(
                "submit_taskgraph_contract requires envelope.nodes contract"
            )
        nodes_data = contract["nodes"]
        if not isinstance(nodes_data, list) or not nodes_data:
            self._deny(DenyReason.RECORD_EMPTY, "contract has no nodes")
            return
        if len(nodes_data) > self.budget.max_dag_nodes:
            self._deny(
                DenyReason.DAG_NODE_LIMIT,
                detail=f"contract has {len(nodes_data)} nodes; limit is {self.budget.max_dag_nodes}",
            )
            return
        envelope_data = contract["envelope"]
        graph = TaskGraph(
            envelope=TaskGraphEnvelope(
                issue=envelope_data.get("issue", issue),
                spec_hash=envelope_data.get("spec_hash", "sha256:" + "0" * 64),
                graph_version=str(envelope_data.get("graph_version", GRAPH_VERSION)),
                created_at=str(envelope_data.get("created_at", datetime.now(UTC).isoformat())),
                planner=str(envelope_data.get("planner", "herdr-taskgraph-adapter@1.0")),
                max_nodes=int(envelope_data.get("max_nodes", self.budget.max_dag_nodes)),
                max_depth=int(envelope_data.get("max_depth", self.budget.max_dag_depth)),
                max_fanout=int(envelope_data.get("max_fanout", self.budget.max_dag_fanout)),
                policy_profile=str(envelope_data.get("policy_profile", "default")),
            ),
            nodes=tuple(
                self._tasknode_from_contract(n, repo, issue) for n in nodes_data
            ),
        )
        self.submit(graph, repo=repo, issue=issue)

    def _tasknode_from_contract(
        self, node_data: Mapping[str, object], repo: str, issue: str
    ) -> TaskNode:
        node_id = str(node_data.get("id", "unknown"))
        parent_id = node_data.get("parent_id")
        if parent_id is not None and not isinstance(parent_id, str):
            parent_id = None
        role = str(node_data.get("role", "reader"))
        tools = tuple(str(t) for t in node_data.get("tools", ()))
        permissions = tuple(str(p) for p in node_data.get("permissions", ()))
        model_policy = node_data.get("model_policy", {"model": "fixture-model"})
        if not isinstance(model_policy, Mapping):
            model_policy = {"model": str(model_policy)}
        objective = str(node_data.get("objective", f"task:{node_id}"))
        dependencies = tuple(str(d) for d in node_data.get("dependencies", ()))
        return TaskNode(
            id=node_id,
            parent_id=parent_id,
            type="task",
            role=role,
            objective=objective,
            inputs=[{"artifact_ref": "fixture"}],
            expected_outputs=[{"kind": "result"}],
            dependencies=dependencies,
            priority=int(node_data.get("priority", 1)),
            resource_class=str(node_data.get("resource_class", "small")),
            model_policy=model_policy,
            tools=tools,
            permissions=permissions,
            timeout_seconds=int(node_data.get("timeout_seconds", 1800)),
            max_attempts=int(node_data.get("max_attempts", 1)),
        )

    def current_time(self) -> float:
        """Return scheduler time so leases and external registries share one clock."""
        return self.clock()

    def task_node(self, task_id: str) -> TaskNode:
        record = self._tasks.get(task_id)
        if record is None:
            raise KeyError(task_id)
        return record.node

    def task_context(self, task_id: str) -> dict[str, str]:
        record = self._tasks.get(task_id)
        if record is None:
            raise KeyError(task_id)
        return {
            "repo": record.repo,
            "issue": record.issue,
            "policy_profile": record.policy_profile,
        }

    def graph_dimensions(self) -> tuple[int, int, int]:
        if not self._tasks:
            return (0, 0, 0)
        nodes = [record.node for record in self._tasks.values()]
        by_id = {node.id: node for node in nodes}
        depth_cache: dict[str, int] = {}

        def depth(node_id: str, visiting: set[str]) -> int:
            if node_id in depth_cache:
                return depth_cache[node_id]
            if node_id in visiting:
                raise SchedulerError("cycle in parent hierarchy")
            visiting.add(node_id)
            node = by_id[node_id]
            parent = node.parent_id
            value = 1 if parent is None else 1 + depth(parent, visiting)
            visiting.remove(node_id)
            depth_cache[node_id] = value
            return value

        fanout: dict[str, int] = defaultdict(int)
        for node in nodes:
            if node.parent_id is not None:
                fanout[node.parent_id] += 1
        return (
            len(nodes),
            max(depth(node.id, set()) for node in nodes),
            max(fanout.values(), default=0),
        )

    # -- dispatch -----------------------------------------------------------

    def ready(self) -> list[TaskNode]:
        ready_nodes: list[TaskNode] = []
        for task_id, rec in list(self._tasks.items()):
            if rec.state != LifecycleState.PENDING:
                continue
            deps = rec.node.dependencies
            if rec.ownership is not None and any(
                    dep not in self._tasks or self._tasks[dep].state is not LifecycleState.DONE
                    or self._tasks[dep].ownership is not None and not self._tasks[dep].cleanup_complete
                    for dep in rec.ownership.hard_dependencies):
                rec.blocker="ownership_hard_dependency_not_ready"
                continue
            if not deps:
                ready_nodes.append(rec.node)
                continue
            deps_met = all(
                d in self._tasks
                and self._tasks[d].state
                in (
                    LifecycleState.DONE,
                    LifecycleState.FAILED,
                    LifecycleState.CANCELLED,
                )
                for d in deps
            )
            if deps_met:
                ready_nodes.append(rec.node)
        return ready_nodes

    def dispatch(self, now: float | None = None, *, task_ids: set[str] | None = None,
                 managed_start: bool = False) -> list[Lease]:
        if type(managed_start) is not bool: raise SchedulerError("typed managed start flag required")
        now = now or self.clock()
        ready_nodes = sorted((n for n in self.ready() if task_ids is None or n.id in task_ids),
                             key=lambda n: (n.priority, n.id))
        if managed_start and any(self._tasks[n.id].delegation_key is None for n in ready_nodes):
            raise SchedulerError("managed start requires a delegated child")
        leases: list[Lease] = []
        used_global = 0
        used_repo: dict[str, int] = defaultdict(int)
        used_issue: dict[str, int] = defaultdict(int)
        for node in ready_nodes:
            task_id = node.id
            rec = self._tasks[task_id]
            if rec.state != LifecycleState.PENDING:
                continue
            if used_global >= self.budget.max_global_concurrency:
                rec.blocker = DenyReason.GLOBAL_CONCURRENCY_LIMIT.value
                self._emit_task_telemetry(
                    rec, EventType.BLOCKER, state=LifecycleState.BLOCKED.value,
                    blocker=rec.blocker, moment=now,
                )
                continue
            repo_ctx = rec.repo
            issue_ctx = rec.issue
            if used_repo[repo_ctx] >= self.budget.max_per_repo:
                rec.blocker = DenyReason.PER_REPO_LIMIT.value
                self._emit_task_telemetry(
                    rec, EventType.BLOCKER, state=LifecycleState.BLOCKED.value,
                    blocker=rec.blocker, moment=now,
                )
                continue
            if issue_ctx and used_issue[issue_ctx] >= self.budget.max_per_issue:
                rec.blocker = DenyReason.PER_ISSUE_LIMIT.value
                self._emit_task_telemetry(
                    rec, EventType.BLOCKER, state=LifecycleState.BLOCKED.value,
                    blocker=rec.blocker, moment=now,
                )
                continue
            conflict = self._ownership_conflict(rec)
            if conflict:
                rec.blocker=conflict
                continue
            if self.ownership_registry is not None and rec.parent_task_id is not None:
                if (rec.parent_task_id,rec.parent_agent_id, "github:"+rec.repo) != (
                        self.ownership_parent.task_id,self.ownership_parent.agent_id,self.ownership_parent.consumer):
                    raise SchedulerError("ownership parent differs from canonical graph")
                try:
                    key=self.ownership_registry.reserve(self.ownership_parent,rec.id,rec.ownership,
                        read_only=self._ownership_read_only(rec))
                except OwnershipError as exc:
                    rec.blocker=str(exc)
                    continue
                if rec.ownership_reservation not in (None,key):
                    raise SchedulerError("ownership reservation changed")
                if rec.ownership_reservation is None:
                    self.audit_log.append({"event":"child_ownership_reserved","task_id":rec.id,
                        "reservation":key,"parent":self.ownership_parent.to_json(),
                        "ownership_sha256":rec.ownership.hash if rec.ownership else None})
                    self.audit_log.flush()
                    rec.ownership_reservation=key
            if rec.lease is not None:
                lease = rec.lease
                lease = replace(lease, lease_until=now + self.budget.claim_ttl_seconds)
                rec.lease = lease
            else:
                agent_id = f"agent-{self._next_agent_id()}"
                lease = Lease(
                    task_id=task_id,
                    agent_id=agent_id,
                    holder=agent_id,
                    fencing_token=self._next_fencing_token(),
                    lease_until=now + self.budget.claim_ttl_seconds,
                )
                rec.lease = lease
            rec.state = LifecycleState.RUNNING
            rec.attempt_state = "accepted"
            if rec.run_token is None:
                rec.run_token = uuid.uuid4().hex
            if rec.delegation_key is not None and rec.idempotency_key is None:
                rec.idempotency_key = hashlib.sha256(
                    f"{task_id}:{rec.run_token}:economic-attempt".encode()
                ).hexdigest()
            rec.agent_id = lease.agent_id
            start = None
            if managed_start:
                from .security import InvocationIdentity
                identity = InvocationIdentity(consumer="github:"+rec.repo,agent_id=rec.agent_id,
                    parent_agent_id=rec.parent_agent_id,parent_task_id=rec.parent_task_id,
                    task_id=rec.id,run_token=rec.run_token,fencing_token=lease.fencing_token)
                start = {"version":1,"identity":identity.to_json(),"idempotency_key":rec.idempotency_key,
                         "marker":"child-"+rec.run_token}
                rec.pre_delivery_pane_creation_attempted = True
                rec.pane_split_started = False
                rec.execution_agent,rec.execution_marker=rec.agent_id,start["marker"]
            rec.started_at = now
            rec.blocker = None
            used_global += 1
            used_repo[repo_ctx] += 1
            if issue_ctx:
                used_issue[issue_ctx] += 1
            leases.append(lease)
            self.audit_log.append(
                {
                    "event": "claim",
                    **({"managed_start":start} if start is not None else {}),
                    "task_id": task_id,
                    "agent_id": lease.agent_id,
                    "holder": lease.holder,
                    "fencing_token": lease.fencing_token,
                    "lease_until": lease.lease_until,
                    "attempt_state": rec.attempt_state,
                    "run_token": rec.run_token,
                    "idempotency_key": rec.idempotency_key,
                    "ts": datetime.now(UTC).isoformat(),
                }
            )
            queue_wait_ms = (
                None
                if rec.submitted_at is None
                else int(max(0.0, now - rec.submitted_at) * 1000)
            )
            self._emit_task_telemetry(
                rec,
                EventType.TASK_STATE,
                state=LifecycleState.RUNNING.value,
                queue_wait_ms=queue_wait_ms,
                moment=now,
            )
        self.audit_log.flush()
        if self.ownership_registry is not None:
            from .security import InvocationIdentity
            for lease in leases:
                rec=self._tasks[lease.task_id]
                if rec.ownership_reservation is not None:
                    self.ownership_registry.bind_claim(rec.ownership_reservation,
                        InvocationIdentity("github:"+rec.repo,rec.agent_id,rec.parent_agent_id,
                            rec.parent_task_id,rec.id,rec.run_token,lease.fencing_token))
        return leases

    @staticmethod
    def _ownership_read_only(rec):
        return set(rec.node.tools)<={"read_file","search_files","herdr_submit_result"}

    def _ownership_conflict(self,rec):
        for other in self._tasks.values():
            if (other.id==rec.id or other.parent_task_id is None or other.repo!=rec.repo
                    or other.attempt_state=="dispatching" and other.state is LifecycleState.PENDING
                    or other.cleanup_complete):
                continue
            if rec.ownership is None or other.ownership is None:
                if not (self._ownership_read_only(rec) and self._ownership_read_only(other)):
                    return "ownership_unknown_serialize"
            else:
                conflict=rec.ownership.conflict(other.ownership)
                if conflict:return conflict
        return None

    def _require_current_ownership(self,rec):
        if self.ownership_registry is None:return
        from .security import InvocationIdentity
        if rec.ownership_reservation is None:
            raise SchedulerError("child ownership reservation missing")
        self.ownership_registry.require_current(rec.ownership_reservation,
            InvocationIdentity("github:"+rec.repo,rec.agent_id,rec.parent_agent_id,
                rec.parent_task_id,rec.id,rec.run_token,rec.fencing_token))

    # -- completion ----------------------------------------------------------

    def complete(
        self,
        task_id: str,
        result: str,
        *,
        agent_id: str | None = None,
        fencing_token: int | None = None,
        now: float | None = None,
    ) -> bool:
        now = now or self.clock()
        rec = self._tasks.get(task_id)
        if rec is None:
            self._deny(DenyReason.UNKNOWN_TASK, f"unknown task: {task_id}")
            return False
        if rec.delegation_key is not None:
            # Durable delegated work must use publish_child_result, which
            # checks exact attempt identity and artifact evidence.
            return False
        lease = rec.lease
        if lease is None:
            self._deny(DenyReason.RECORD_EMPTY, detail=f"no lease for task: {task_id}")
            return False
        if agent_id is not None and agent_id != lease.agent_id:
            return False
        if fencing_token is not None and fencing_token != lease.fencing_token:
            return False
        # Fail-closed: reject commits on expired leases
        if now >= lease.lease_until:
            self._deny(
                DenyReason.STALE_FENCE,
                detail=(
                    f"lease expired (lease_until={lease.lease_until:.3f}, now={now:.3f}) "
                    f"for task: {task_id}"
                ),
            )
            return False
        if rec.state in (
            LifecycleState.DONE,
            LifecycleState.FAILED,
            LifecycleState.CANCELLED,
        ):
            return False
        runtime_ms = (
            None
            if rec.started_at is None
            else int(max(0.0, now - rec.started_at) * 1000)
        )
        rec.state = LifecycleState.DONE
        rec.lease = None
        if agent_id is not None:
            rec.agent_id = agent_id
        if fencing_token is not None:
            rec.fencing_token = fencing_token
        self.audit_log.append(
            {
                "event": "complete",
                "task_id": task_id,
                "agent_id": agent_id,
                "fencing_token": fencing_token,
                "result": result,
                "state": LifecycleState.DONE.value,
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self._emit_task_telemetry(
            rec,
            EventType.TASK_STATE,
            state=LifecycleState.DONE.value,
            runtime_ms=runtime_ms,
            result_sha=self._telemetry_result_sha(result),
            moment=now,
        )
        self.audit_log.flush()
        self._mark_dependents_done(task_id)
        return True

    def _mark_dependents_done(self, completed_task_id: str) -> None:
        for task_id, rec in list(self._tasks.items()):
            if rec.state != LifecycleState.PENDING:
                continue
            if completed_task_id not in rec.node.dependencies:
                continue
            deps_met = all(
                d in self._tasks and self._tasks[d].state in (LifecycleState.DONE,)
                for d in rec.node.dependencies
            )
            if deps_met:
                rec.state = LifecycleState.PENDING

    def fail(self, task_id: str) -> None:
        rec = self._tasks.get(task_id)
        if rec is None:
            return
        now = self.clock()
        runtime_ms = (
            None
            if rec.started_at is None
            else int(max(0.0, now - rec.started_at) * 1000)
        )
        rec.state = LifecycleState.FAILED
        rec.attempts += 1
        self.audit_log.append(
            {
                "event": "fail",
                "task_id": task_id,
                "state": LifecycleState.FAILED.value,
                "attempts": rec.attempts,
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self._emit_task_telemetry(
            rec,
            EventType.TASK_STATE,
            state=LifecycleState.FAILED.value,
            runtime_ms=runtime_ms,
            retry_count=rec.attempts,
            moment=now,
        )
        self.audit_log.flush()
        # Propagate BLOCKED to dependents
        for other_id, other_rec in self._tasks.items():
            if (
                other_rec.state == LifecycleState.PENDING
                and task_id in other_rec.node.dependencies
            ):
                other_rec.state = LifecycleState.BLOCKED
                other_rec.blocker = f"prereq_failed:{task_id}"
                self._emit_task_telemetry(
                    other_rec,
                    EventType.BLOCKER,
                    state=LifecycleState.BLOCKED.value,
                    blocker=other_rec.blocker,
                    moment=now,
                )

    # -- fencing / reclaim ---------------------------------------------------

    def reclaim(self, holder: str, now: float | None = None) -> list[str]:
        """Reclaim tasks held by `holder` (e.g. a lost worker) at `now`.

        Fail-closed: only reclaim tasks whose lease belongs to `holder` and
        which are not yet terminal.  The reclaimed task gets a fresh lease
        with a strictly higher monotonic fencing token.
        """
        now = now or self.clock()
        reclaimed: list[str] = []
        for task_id, rec in list(self._tasks.items()):
            lease = rec.lease
            if lease is None or lease.holder != holder:
                continue
            if rec.state in (
                LifecycleState.DONE,
                LifecycleState.FAILED,
                LifecycleState.CANCELLED,
            ):
                continue
            if rec.delegation_key is not None or (rec.run_token and rec.attempt_state in {
                "accepted", "delivery_uncertain", "result_ready", "verifying"
            }):
                # An accepted economic prompt may still be running. Reclaiming
                # would make it eligible for another prompt delivery.
                continue
            reclaimed.append(task_id)
        if not reclaimed:
            return reclaimed
        for task_id in reclaimed:
            rec = self._tasks[task_id]
            rec.lease = Lease(
                task_id=task_id,
                agent_id=rec.agent_id or f"agent-{self._next_agent_id()}",
                holder=holder,
                fencing_token=self._next_fencing_token(),
                lease_until=now + self.budget.claim_ttl_seconds,
            )
            rec.state = LifecycleState.PENDING
            rec.blocker = None
            rec.submitted_at = now
            rec.started_at = None
            rec.telemetry.append(
                {
                    "event": "reclaim",
                    "ts": datetime.now(UTC).isoformat(),
                }
            )
            self._emit_task_telemetry(
                rec,
                EventType.RETRY,
                state=LifecycleState.PENDING.value,
                reason="worker_reclaim",
                retry_count=rec.attempts,
                moment=now,
            )
        self.audit_log.append(
            {
                "event": "reclaim",
                "reclaimed": reclaimed,
                "leases": {task_id: {
                    "agent_id": self._tasks[task_id].lease.agent_id,
                    "holder": self._tasks[task_id].lease.holder,
                    "fencing_token": self._tasks[task_id].lease.fencing_token,
                    "lease_until": self._tasks[task_id].lease.lease_until,
                } for task_id in reclaimed},
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self.audit_log.flush()
        return reclaimed

    def cancel(self, task_id: str, reason: str = "manual-cancel") -> None:
        rec = self._tasks.get(task_id)
        if rec is None:
            return
        now = self.clock()
        runtime_ms = (
            None
            if rec.started_at is None
            else int(max(0.0, now - rec.started_at) * 1000)
        )
        rec.state = LifecycleState.CANCELLED
        rec.lease = None
        rec.blocker = reason
        self.audit_log.append(
            {
                "event": "cancel",
                "task_id": task_id,
                "reason": reason,
                "state": LifecycleState.CANCELLED.value,
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self._emit_task_telemetry(
            rec,
            EventType.TASK_STATE,
            state=LifecycleState.CANCELLED.value,
            runtime_ms=runtime_ms,
            blocker=reason,
            moment=now,
        )
        self.audit_log.flush()

    # -- child lifecycle -----------------------------------------------------

    def spawn_child(
        self,
        parent_id: str,
        proposal: ChildProposal,
        *,
        delegation_key: str | None = None,
        parent_run_token: str | None = None,
    ) -> TaskNode | DenyDecision:
        parent_rec = self._tasks.get(parent_id)
        if parent_rec is None:
            deny = DenyDecision(
                DenyReason.UNKNOWN_TASK, detail=f"unknown parent: {parent_id}"
            )
            self._deny(deny.reason, deny.detail or "")
            return deny
        if delegation_key is not None:
            if not delegation_key.strip() or not parent_run_token:
                raise SchedulerError("delegation requires key and parent run_token")
            for existing in self._tasks.values():
                if existing.parent_task_id == parent_id and existing.delegation_key == delegation_key:
                    if (existing.parent_run_token != parent_run_token
                            or existing.node.objective != proposal.child_task
                            or existing.node.role != proposal.child_role
                            or existing.node.tools != tuple(proposal.child_tools)
                            or existing.node.permissions != tuple(proposal.child_permissions)):
                        raise SchedulerError("delegation key reused with different identity or work")
                    if (existing.worktree_identity != proposal.worktree_identity
                            or existing.ownership != proposal.ownership):
                        raise SchedulerError("delegation key reused with different identity or work")
                    return existing.node
            if parent_rec.state is not LifecycleState.RUNNING:
                raise SchedulerError("economic delegation requires a running durable parent")
            if parent_rec.run_token != parent_run_token:
                raise SchedulerError("economic delegation parent attempt mismatch")

        if proposal.ownership is not None:
            ownership=proposal.ownership
            if ownership.integration_owner!=parent_id:
                raise SchedulerError("child integration owner must be its durable parent")
            if any(dep==parent_id or dep not in self._tasks
                    or self._tasks[dep].repo!=parent_rec.repo for dep in ownership.hard_dependencies):
                raise SchedulerError("unknown or cyclic child hard dependency")
            if set(proposal.child_tools)&{"write_file","patch","write"} and not any(
                    scope.kind in {"file","directory"} for scope in ownership.write_scope):
                raise SchedulerError("write tool requires declared file ownership")
        canonical = replace(
            proposal,
            parent_role=parent_rec.node.role,
            parent_tools=tuple(parent_rec.node.tools),
            parent_permissions=tuple(parent_rec.node.permissions),
        )
        decision = self.consumer_policy.evaluate_child_proposal(canonical)
        if not decision:
            self._deny(
                decision.reason,
                detail=f"child proposal denied for parent {parent_id}: {decision.reason.value}",
            )
            return decision

        if len(self._tasks) >= self._plan_max_nodes:
            deny = DenyDecision(
                DenyReason.DAG_NODE_LIMIT,
                detail=f"dynamic node limit reached: {self._plan_max_nodes}",
            )
            self._deny(deny.reason, deny.detail)
            return deny

        parent_depth = 1
        cursor = parent_rec.node.parent_id
        seen = {parent_id}
        while cursor is not None:
            if cursor in seen:
                raise SchedulerError("cycle in parent hierarchy")
            seen.add(cursor)
            ancestor = self._tasks.get(cursor)
            if ancestor is None:
                raise SchedulerError(f"unknown parent in hierarchy: {cursor}")
            parent_depth += 1
            cursor = ancestor.node.parent_id
        if parent_depth + 1 > self._plan_max_depth:
            deny = DenyDecision(
                DenyReason.DAG_DEPTH_LIMIT,
                detail=f"dynamic child depth exceeds limit: {self._plan_max_depth}",
            )
            self._deny(deny.reason, deny.detail)
            return deny

        current_fanout = sum(
            1 for record in self._tasks.values() if record.node.parent_id == parent_id
        )
        if current_fanout >= self._plan_max_fanout:
            deny = DenyDecision(
                DenyReason.DAG_FANOUT_LIMIT,
                detail=f"dynamic child fanout limit reached: {self._plan_max_fanout}",
            )
            self._deny(deny.reason, deny.detail)
            return deny

        proposal = canonical
        child_id = (
            f"{parent_id}-child-{hashlib.sha256(f'{parent_id}:{parent_run_token}:{delegation_key}'.encode()).hexdigest()[:16]}"
            if delegation_key is not None else f"{parent_id}-child-{self._next_agent_id()}"
        )
        child_node = TaskNode(
            id=child_id,
            parent_id=parent_id,
            type="task",
            role=proposal.child_role,
            objective=proposal.child_task,
            inputs=([{"artifact_ref":"child-ownership:"+proposal.ownership.hash}]
                    if proposal.ownership else [{"artifact_ref":"fixture"}]),
            expected_outputs=([{"kind":"result","artifact_ref":proposal.ownership.handoff_ref}]
                    if proposal.ownership else [{"kind":"result"}]),
            dependencies=list(proposal.ownership.hard_dependencies) if proposal.ownership else [],
            priority=parent_rec.node.priority,
            resource_class=parent_rec.node.resource_class,
            model_policy={
                "model": proposal.child_model,
                "fallback_model": proposal.child_fallback_model,
            },
            tools=proposal.child_tools,
            permissions=proposal.child_permissions,
            timeout_seconds=parent_rec.node.timeout_seconds,
            max_attempts=parent_rec.node.max_attempts,
        )
        rec = TaskRecord(
            node=child_node,
            parent_task_id=parent_id,
            parent_agent_id=parent_rec.agent_id,
            repo=parent_rec.repo,
            issue=parent_rec.issue,
            policy_profile=parent_rec.policy_profile,
            model_used=proposal.child_model,
            fallback_used=proposal.child_fallback_model,
            delegation_key=delegation_key,
            parent_run_token=parent_run_token,
            worktree_identity=proposal.worktree_identity,
            ownership=proposal.ownership,
        )
        rec.submitted_at = self.clock()
        self._tasks[child_id] = rec
        child_agent_id = (
            f"hc-{hashlib.sha256(child_id.encode()).hexdigest()[:24]}"
            if delegation_key is not None else f"agent-{self._next_agent_id()}"
        )
        rec.lease = Lease(
            task_id=child_id,
            agent_id=child_agent_id,
            holder=child_agent_id,
            fencing_token=self._next_fencing_token(),
            lease_until=self.clock() + self.budget.claim_ttl_seconds,
        )
        self._claims[child_id] = rec.lease
        rec.agent_id = child_agent_id
        rec.fencing_token = rec.lease.fencing_token
        # NOTE: child remains PENDING until dispatched and completed by caller
        self._emit_task_telemetry(
            rec,
            EventType.TASK_STATE,
            state=LifecycleState.PENDING.value,
            moment=rec.submitted_at,
        )
        self.audit_log.append(
            {
                "event": "spawn_child",
                "child_id": child_id,
                "parent_id": parent_id,
                "parent_agent_id": parent_rec.agent_id or "",
                "model": proposal.child_model,
                "fallback_model": proposal.child_fallback_model,
                "agent_id": child_agent_id,
                "fencing_token": rec.lease.fencing_token,
                "holder": child_agent_id,
                "lease_until": rec.lease.lease_until,
                "child_role": proposal.child_role,
                "child_tools": list(proposal.child_tools),
                "child_permissions": list(proposal.child_permissions),
                "child_task": proposal.child_task,
                "delegation_key": delegation_key,
                "parent_run_token": parent_run_token,
                "worktree_identity": proposal.worktree_identity,
                "ownership":proposal.ownership.to_json() if proposal.ownership else None,
                "dependencies":list(child_node.dependencies),
                "inputs":child_node.to_json()["inputs"],"expected_outputs":child_node.to_json()["expected_outputs"],
                "repo": parent_rec.repo,
                "issue": parent_rec.issue,
                "policy_profile": parent_rec.policy_profile,
                "ts": str(self.clock()),
            }
        )
        self.audit_log.flush()
        return child_node

    def delegate_child(self, parent_id: str, parent_run_token: str,
                       delegation_key: str, proposal: ChildProposal) -> TaskNode | DenyDecision:
        """Admit and persist an economic child before any prompt is delivered."""
        return self.spawn_child(parent_id, proposal, delegation_key=delegation_key,
                                parent_run_token=parent_run_token)

    def bind_child_prompt(self, task_id: str, prompt: str) -> None:
        rec = self._tasks.get(task_id)
        if rec is None or rec.delegation_key is None or not prompt:
            raise SchedulerError("unknown economic child prompt")
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if rec.delivery_prompt_sha256 and rec.delivery_prompt_sha256 != digest:
            raise SchedulerError("delegation key reused with different prompt")
        if rec.delivery_prompt_sha256 is None:
            rec.delivery_prompt_sha256 = digest
            self.audit_log.append({"event": "child_prompt_bound", "task_id": task_id,
                                   "sha256": digest})
            self.audit_log.flush()

    def bind_owned_write_mounts(self,task_id,pins):
        from .owned_write_mounts import OwnedWritePins,validate_owned_mount_evidence
        from .security import InvocationIdentity
        rec=self._tasks.get(task_id)
        if (rec is None or rec.ownership is None or not isinstance(pins,OwnedWritePins)
                or pins.ownership_sha256!=rec.ownership.hash
                or pins.worktree.identity!=rec.worktree_identity):
            raise SchedulerError("owned mount observation differs from claimed child")
        self._require_current_ownership(rec)
        identity=InvocationIdentity("github:"+rec.repo,rec.agent_id,rec.parent_agent_id,
            rec.parent_task_id,rec.id,rec.run_token,rec.fencing_token)
        rows=validate_owned_mount_evidence(rec.ownership,pins.evidence())
        if rec.owned_write_mounts is not None:
            if rec.owned_write_mounts!=rows:
                raise SchedulerError("owned mount observation changed")
            return
        self.audit_log.append({"event":"child_owned_mounts_observed","identity":identity.to_json(),
            "ownership_sha256":rec.ownership.hash,"worktree_identity":rec.worktree_identity,
            "mounts":[dict(x) for x in rows]})
        self.audit_log.flush()
        rec.owned_write_mounts=rows

    def authorize_child_delivery(self, task_id: str, run_token: str,
                                 agent_id: str, fencing_token: int,
                                 idempotency_key: str) -> bool:
        """Gate economic prompt delivery on a claimed, durable child attempt."""
        rec = self._tasks.get(task_id)
        lease = rec.lease if rec else None
        allowed = bool(rec and rec.delegation_key and rec.parent_task_id
                       and rec.delivery_prompt_sha256
                       and rec.state is LifecycleState.RUNNING and lease
                       and lease.agent_id == agent_id
                       and lease.fencing_token == fencing_token
                       and self.clock() < lease.lease_until
                       and rec.run_token == run_token
                       and rec.idempotency_key == idempotency_key)
        if allowed:
            try:self._require_current_ownership(rec)
            except (OwnershipError,SchedulerError):allowed=False
        if not allowed:
            self.audit_log.append({"event": "economic_delivery_denied",
                                   "task_id": task_id, "ts": datetime.now(UTC).isoformat()})
            self.audit_log.flush()
        return allowed

    def bind_execution_session(self, task_id: str, run_token: str,
                               agent_name: str, pane_id: str, marker: str) -> bool:
        rec = self._tasks.get(task_id)
        if (rec is None or rec.state is not LifecycleState.RUNNING
                or rec.run_token != run_token or not all((agent_name, pane_id, marker))):
            return False
        identity = (agent_name, pane_id, marker)
        previous = (rec.execution_agent, rec.execution_pane, rec.execution_marker)
        partial_intent = (rec.pre_delivery_pane_creation_attempted and previous[1] is None
                          and previous[0] == agent_name and previous[2] == marker)
        if any(previous) and previous != identity and not partial_intent:
            return False
        rec.execution_agent, rec.execution_pane, rec.execution_marker = identity
        self.audit_log.append({"event": "execution_session_bound", "task_id": task_id,
                               "run_token": run_token, "agent_name": agent_name,
                               "pane_id": pane_id, "marker": marker,
                               "ts": datetime.now(UTC).isoformat()})
        self.audit_log.flush()
        return True

    @staticmethod
    def _bootstrap_upgrade_allowed(rec, previous, current):
        if (not rec.execution_sandbox_verified or not rec.pre_delivery_agent_start_attempted
                or rec.state is not LifecycleState.RUNNING):
            return False
        old,new=previous.get("invocation_policy"),current.get("invocation_policy")
        if (not isinstance(old,dict) or not isinstance(new,dict)
                or old.get("schema_version")!="herdr-policy-launch-2"
                or new.get("schema_version")!="herdr-policy-launch-3"):
            return False
        base={key:value for key,value in new.items() if key!="bootstrap"}
        base["schema_version"]="herdr-policy-launch-2"
        if base!=old: return False
        return ({key:value for key,value in previous.items()
                 if key not in {"verified_at","invocation_policy"}}
                =={key:value for key,value in current.items()
                   if key not in {"verified_at","invocation_policy"}})

    def attest_execution_sandbox(
        self,
        task_id: str,
        run_token: str,
        agent_name: str,
        pane_id: str,
        marker: str,
        *,
        sandbox_pid: int,
        policy_sha256: str,
        invocation_policy: dict | None = None,
    ) -> bool:
        """Persist host-produced bwrap proof for the exact bound child session.

        A pane binding is only identity/pre-delivery evidence. This attestation is
        recorded separately and only after the runtime has proven the bwrap
        PID/mount/policy boundary. Consumers such as the verification gate must
        require this flag/attestation rather than infer trust from UI settlement.
        """
        rec = self._tasks.get(task_id)
        identity = (agent_name, pane_id, marker)
        expected = (rec.execution_agent, rec.execution_pane, rec.execution_marker) if rec else (None, None, None)
        if (
            rec is None
            or rec.state is not LifecycleState.RUNNING
            or rec.run_token != run_token
            or rec.agent_id != agent_name
            or expected != identity
            or type(sandbox_pid) is not int
            or sandbox_pid <= 0
            or not isinstance(policy_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", policy_sha256) is None
        ):
            return False
        attestation = {
            "authority": "herdr-runtime",
            "kind": "bwrap",
            "task_id": task_id,
            "run_token": run_token,
            "agent_name": agent_name,
            "pane_id": pane_id,
            "marker": marker,
            "fencing_token": rec.fencing_token,
            "worktree_identity": rec.worktree_identity,
            "sandbox_pid": sandbox_pid,
            "policy_sha256": policy_sha256,
            "verified_at": datetime.now(UTC).isoformat(),
        }
        if rec.ownership is not None:
            if rec.owned_write_mounts is None:
                return False
            attestation.update(ownership_sha256=rec.ownership.hash,
                owned_write_mounts=[dict(x) for x in rec.owned_write_mounts])
        if invocation_policy is not None:
            from herdr.policy_launch import validate_policy_evidence
            from herdr.security import InvocationIdentity, SecurityError
            try:
                policy_identity = InvocationIdentity(
                    consumer="github:" + rec.repo, agent_id=rec.agent_id,
                    parent_agent_id=rec.parent_agent_id, parent_task_id=rec.parent_task_id,
                    task_id=rec.id, run_token=rec.run_token, fencing_token=rec.fencing_token)
                attestation["invocation_policy"] = validate_policy_evidence(
                    invocation_policy, identity=policy_identity)
            except (SecurityError, TypeError, ValueError):
                return False
        if not rec.execution_sandbox_verified and (
                attestation.get("invocation_policy") or {}).get("schema_version")=="herdr-policy-launch-3":
            return False
        if rec.execution_sandbox_verified:
            previous = rec.execution_sandbox_attestation or {}
            comparable = {k: previous.get(k) for k in attestation if k != "verified_at"}
            current = {k: v for k, v in attestation.items() if k != "verified_at"}
            if comparable == current:
                return True
            if not self._bootstrap_upgrade_allowed(rec,previous,attestation):
                return False
            self.audit_log.append({"event":"execution_bootstrap_attested","task_id":task_id,
                                   "run_token":run_token,"attestation":attestation})
            self.audit_log.flush()
            rec.execution_sandbox_attestation=json.loads(json.dumps(attestation))
            return True
        rec.execution_sandbox_verified = True
        rec.execution_sandbox_attestation = attestation
        self.audit_log.append({
            "event": "execution_sandbox_attested",
            "task_id": task_id,
            "run_token": run_token,
            "attestation": attestation,
        })
        self.audit_log.flush()
        return True

    def record_child_pane_intent(self, task_id: str, run_token: str, agent_id: str,
                                  fencing_token: int, idempotency_key: str, marker: str) -> bool:
        """Commit deterministic ownership before an external split can create a pane."""
        rec = self._tasks.get(task_id)
        if (rec is not None and rec.pre_delivery_pane_creation_attempted
                and rec.pane_split_started is False and rec.execution_pane is None
                and not rec.pre_delivery_agent_start_attempted and rec.state is LifecycleState.RUNNING
                and rec.lease is not None and marker == f"child-{run_token}"
                and (rec.run_token,rec.agent_id,rec.fencing_token,rec.idempotency_key,
                     rec.execution_agent,rec.execution_marker) ==
                    (run_token,agent_id,fencing_token,idempotency_key,agent_id,marker)):
            return True
        if (rec is None or rec.delegation_key is None or rec.state is not LifecycleState.RUNNING
                or rec.lease is None or rec.pre_delivery_pane_creation_attempted
                or any((rec.execution_agent, rec.execution_pane, rec.execution_marker))
                or marker != f"child-{run_token}"
                or (rec.run_token, rec.agent_id, rec.fencing_token, rec.idempotency_key) !=
                   (run_token, agent_id, fencing_token, idempotency_key)):
            return False
        self.audit_log.append({"event": "child_pane_creation_attempted", "task_id": task_id,
                               "run_token": run_token, "agent_id": agent_id,
                               "fencing_token": fencing_token, "idempotency_key": idempotency_key,
                               "marker": marker, "split_protocol_version": 1})
        self.audit_log.flush()
        rec.pre_delivery_pane_creation_attempted = True
        rec.pane_split_started = False
        rec.execution_agent, rec.execution_marker = agent_id, marker
        return True

    def mark_child_split_started(self, task_id, run_token, agent_id, fencing_token, idempotency_key):
        rec = self._tasks.get(task_id)
        if (rec is None or rec.state is not LifecycleState.RUNNING or rec.lease is None
                or not rec.pre_delivery_pane_creation_attempted or rec.pane_split_started is not False
                or rec.execution_pane is not None or rec.pre_delivery_agent_start_attempted
                or (rec.run_token, rec.agent_id, rec.fencing_token, rec.idempotency_key) !=
                   (run_token, agent_id, fencing_token, idempotency_key)):
            return False
        self.audit_log.append({"event":"child_pane_split_started", "split_protocol_version":1,
            "task_id":task_id,"run_token":run_token,"agent_id":agent_id,
            "fencing_token":fencing_token,"idempotency_key":idempotency_key})
        self.audit_log.flush()
        rec.pane_split_started = True
        return True

    def bind_recovered_pre_delivery_pane(self, task_id: str, pane_id: str) -> bool:
        rec = self._tasks.get(task_id)
        if (rec is None or not rec.pre_delivery_pane_creation_attempted
                or rec.pre_delivery_agent_start_attempted
                or not all((rec.run_token, rec.agent_id, rec.idempotency_key, rec.fencing_token))
                or rec.execution_agent != rec.agent_id
                or rec.execution_marker != f"child-{rec.run_token}"
                or not isinstance(pane_id, str) or not pane_id or len(pane_id) > 256
                or (rec.state is not LifecycleState.RUNNING and not rec.pre_delivery_failure)
                or rec.execution_pane not in {None, pane_id}):
            return False
        if rec.execution_pane == pane_id:
            return True
        self.audit_log.append({"event": "child_pane_recovered", "task_id": task_id,
                               "run_token": rec.run_token, "agent_id": rec.agent_id,
                               "fencing_token": rec.fencing_token, "idempotency_key": rec.idempotency_key,
                               "marker": rec.execution_marker, "pane_id": pane_id})
        self.audit_log.flush()
        rec.execution_pane = pane_id
        return True

    def bind_pre_delivery_pane(self, task_id: str, run_token: str,
                               agent_name: str, pane_id: str, marker: str) -> bool:
        """Persist a created pane before starting its agent, for safe recovery."""
        rec = self._tasks.get(task_id)
        if rec is None or rec.delegation_key is None or rec.agent_id != agent_name:
            return False
        return self.bind_execution_session(task_id, run_token, agent_name, pane_id, marker)

    def mark_pre_delivery_agent_start(self, task_id: str) -> None:
        rec = self._tasks[task_id]
        if not rec.execution_pane or rec.state is not LifecycleState.RUNNING:
            raise SchedulerError("child pane unavailable")
        if not rec.pre_delivery_agent_start_attempted:
            self.audit_log.append({"event": "child_agent_start_attempted", "task_id": task_id,
                                   "run_token": rec.run_token,"delivery_protocol_version":1,
                                   "agent_id":rec.agent_id,"fencing_token":rec.fencing_token,
                                   "idempotency_key":rec.idempotency_key})
            self.audit_log.flush()
            rec.pre_delivery_agent_start_attempted = True
            rec.economic_delivery_attempted = False

    def mark_child_delivery_started(self,task_id,run_token,agent_id,fencing_token,idempotency_key):
        rec=self._tasks.get(task_id)
        if (rec is None or rec.economic_delivery_attempted is not False
                or not rec.pre_delivery_agent_start_attempted
                or not self.authorize_child_delivery(task_id,run_token,agent_id,fencing_token,idempotency_key)):
            return False
        self.audit_log.append({"event":"child_prompt_delivery_attempted","task_id":task_id,
            "run_token":run_token,"agent_id":agent_id,"fencing_token":fencing_token,
            "idempotency_key":idempotency_key,"prompt_sha256":rec.delivery_prompt_sha256})
        self.audit_log.flush()
        rec.economic_delivery_attempted=True
        return True

    def fail_child_pre_delivery(self, task_id: str, run_token: str, agent_id: str,
                                fencing_token: int, idempotency_key: str,
                                reason: str, *, cleanup_complete: bool,
                                pane_creation_attempted: bool = False) -> bool:
        rec = self._tasks.get(task_id)
        lease = rec.lease if rec else None
        if (rec is None or rec.delegation_key is None or rec.state is not LifecycleState.RUNNING
                or lease is None or not reason or len(reason) > 1024
                or (rec.run_token, rec.agent_id, rec.fencing_token, rec.idempotency_key) !=
                   (run_token, agent_id, fencing_token, idempotency_key)
                or cleanup_complete
                or rec.pre_delivery_agent_start_attempted and rec.economic_delivery_attempted is not False
                ):
            return False
        pane_creation_attempted = pane_creation_attempted or rec.pre_delivery_pane_creation_attempted
        self.audit_log.append({"event": "child_pre_delivery_failed", "task_id": task_id,
                               "run_token": run_token, "agent_id": agent_id,
                               "fencing_token": fencing_token,
                               "idempotency_key": idempotency_key, "reason": reason,
                               "cleanup_complete": cleanup_complete,
                               "pane_creation_attempted": pane_creation_attempted,
                               "ts": datetime.now(UTC).isoformat()})
        self.audit_log.flush()
        rec.state = LifecycleState.BLOCKED
        rec.attempt_state = "terminal"
        rec.pre_delivery_failure = reason
        rec.pre_delivery_pane_creation_attempted = pane_creation_attempted
        rec.blocker = reason
        rec.cleanup_complete = False
        rec.lease = None
        self._claims.pop(task_id, None)
        return True

    def observe_execution(self, task_id: str, run_token: str, state: str,
                          source: str, *, agent_name: str | None = None,
                          pane_id: str | None = None, marker: str | None = None) -> bool:
        rec = self._tasks.get(task_id)
        if rec is None or state not in {"working", "blocked", "settled", "unavailable"} or not source:
            return False
        if rec.run_token != run_token or rec.state is not LifecycleState.RUNNING:
            return False
        if rec.delegation_key is not None and (
            not all((rec.execution_agent, rec.execution_pane, rec.execution_marker))
            or (agent_name, pane_id, marker) !=
            (rec.execution_agent, rec.execution_pane, rec.execution_marker)
        ):
            return False
        if rec.delegation_key is not None:
            if self.execution_verifier is None:
                return False
            try:
                live_status = self.execution_verifier(rec.execution_agent,
                                                       rec.execution_pane,
                                                       rec.execution_marker)
            except Exception:
                return False
            live_state = {"working": "working", "busy": "working",
                          "blocked": "blocked", "done": "settled",
                          "idle": "settled"}.get(live_status, "unavailable")
            if state != live_state:
                return False
        if not run_token:
            return False
        rec.observed_execution = state
        rec.observation_source = source
        rec.observed_at = datetime.now(UTC).isoformat()
        self.audit_log.append({"event": "execution_observed", "task_id": task_id,
                               "run_token": run_token, "state": state,
                               "source": source, "ts": rec.observed_at})
        self.audit_log.flush()
        return True

    def publish_child_result(self, task_id: str, run_token: str, agent_id: str,
                             fencing_token: int, idempotency_key: str,
                             artifact_sha256: str, evidence: list[object],
                             status: str = "completed") -> bool:
        rec = self._tasks.get(task_id)
        states = {"completed": LifecycleState.DONE,
                  "blocked": LifecycleState.BLOCKED,
                  "failed": LifecycleState.FAILED}
        if rec is None or rec.delegation_key is None or not run_token or status not in states:
            return False
        if rec.run_token != run_token or idempotency_key != rec.idempotency_key:
            return False
        if not isinstance(evidence, list) or not evidence:
            return False
        try:
            canonical = json.dumps(evidence, sort_keys=True, ensure_ascii=False,
                                   allow_nan=False).encode("utf-8")
        except (TypeError, ValueError):
            return False
        if len(canonical) > 262144 or artifact_sha256 != hashlib.sha256(canonical).hexdigest():
            return False
        lease = rec.lease
        if lease is None or lease.agent_id != agent_id or lease.fencing_token != fencing_token:
            return False
        # Managed claims are quarantined across lease expiry; the exact
        # run/fence/key still identifies a late result for this same attempt.
        if rec.state is not LifecycleState.RUNNING:
            return False
        try:self._require_current_ownership(rec)
        except (OwnershipError,SchedulerError):return False
        rec.state = states[status]
        rec.attempt_state = "terminal"
        rec.result_status = status
        rec.result_artifact_sha256 = artifact_sha256
        rec.result_evidence_canonical = canonical
        rec.fencing_token = fencing_token
        rec.lease = None
        self._claims.pop(task_id, None)
        self.audit_log.append({"event": "child_result", "task_id": task_id,
                               "agent_id": agent_id, "fencing_token": fencing_token,
                               "run_token": run_token, "idempotency_key": idempotency_key,
                               "artifact_sha256": artifact_sha256, "evidence": json.loads(canonical),
                               "status": status, "state": rec.state.value,
                               "ownership_sha256":rec.ownership.hash if rec.ownership else None,
                               "handoff_ref":rec.ownership.handoff_ref if rec.ownership else None,
                               "ts": datetime.now(UTC).isoformat()})
        self.audit_log.flush()
        if status == "completed":
            self._mark_dependents_done(task_id)
        return True

    def mark_child_cleanup_complete(self, task_id: str) -> bool:
        """Record cleanup only for the exact terminal, bound child attempt."""
        rec = self._tasks.get(task_id)
        if (rec is None or rec.delegation_key is None or rec.attempt_state != "terminal"
                or not all((rec.run_token, rec.fencing_token, rec.idempotency_key,
                            rec.execution_pane, rec.execution_agent, rec.execution_marker))
                or rec.execution_agent != rec.agent_id):
            return False
        if rec.cleanup_complete:
            return True
        self.audit_log.append({"event": "child_cleanup_complete", "task_id": task_id,
                               "run_token": rec.run_token, "fencing_token": rec.fencing_token,
                               "idempotency_key": rec.idempotency_key,
                               "agent_name": rec.execution_agent,
                               "pane_id": rec.execution_pane,
                               "marker": rec.execution_marker})
        self.audit_log.flush()
        rec.cleanup_complete = True
        return True

    def mark_pre_delivery_cleanup_complete(self, task_id: str) -> bool:
        rec = self._tasks.get(task_id)
        if rec is None or not rec.pre_delivery_failure or rec.attempt_state != "terminal":
            return False
        if rec.cleanup_complete:
            return True
        if rec.execution_pane:
            return self.mark_child_cleanup_complete(task_id)
        if rec.pre_delivery_pane_creation_attempted and rec.pane_split_started is not False:
            return False
        self.audit_log.append({"event": "child_pre_delivery_cleanup_complete",
                               "task_id": task_id, "run_token": rec.run_token,
                               "fencing_token": rec.fencing_token,
                               "idempotency_key": rec.idempotency_key})
        self.audit_log.flush()
        rec.cleanup_complete = True
        return True

    def evaluate_child_proposal(
        self, proposal: ChildProposal
    ) -> AllowDecision | DenyDecision:
        return self.consumer_policy.evaluate_child_proposal(proposal)

    # -- snapshot ------------------------------------------------------------

    def snapshot(self) -> dict[str, object]:
        tasks_snapshot: list[dict[str, object]] = []
        for task_id in sorted(self._tasks):
            rec = self._tasks[task_id]
            node = rec.node
            lease = rec.lease
            model_policy = node.model_policy
            tasks_snapshot.append(
                {
                    "task_id": task_id,
                    "state": rec.state.value,
                    "attempt_state": rec.attempt_state,
                    "result_status": rec.result_status,
                    "result_artifact_sha256": rec.result_artifact_sha256,
                    "observed_execution": rec.observed_execution,
                    "observation_source": rec.observation_source,
                    "observed_at": rec.observed_at,
                    "execution_agent": rec.execution_agent,
                    "execution_pane": rec.execution_pane,
                    "execution_marker": rec.execution_marker,
                    "execution_sandbox_verified": rec.execution_sandbox_verified,
                    "execution_sandbox_attestation": rec.execution_sandbox_attestation,
                    "worktree_identity": rec.worktree_identity,
                    "ownership_sha256": rec.ownership.hash if rec.ownership else None,
                    "ownership_reservation": rec.ownership_reservation,
                    "owned_write_mounts": [dict(x) for x in rec.owned_write_mounts] if rec.owned_write_mounts is not None else None,
                    "write_scope": [asdict(x) for x in rec.ownership.write_scope] if rec.ownership else None,
                    "decision_scope": [asdict(x) for x in rec.ownership.decision_scope] if rec.ownership else None,
                    "integration_owner": rec.ownership.integration_owner if rec.ownership else None,
                    "handoff_ref": rec.ownership.handoff_ref if rec.ownership else None,
                    "shared_dependencies": [asdict(x) for x in rec.ownership.shared_dependencies] if rec.ownership else None,
                    "cleanup_complete": rec.cleanup_complete,
                    "pre_delivery_failure": rec.pre_delivery_failure,
                    "pre_delivery_agent_start_attempted": rec.pre_delivery_agent_start_attempted,
                    "economic_delivery_attempted": rec.economic_delivery_attempted,
                    "pre_delivery_pane_creation_attempted": rec.pre_delivery_pane_creation_attempted,
                    "pane_split_started": rec.pane_split_started,
                    "run_token": rec.run_token,
                    "delegation_key": rec.delegation_key,
                    "idempotency_key": rec.idempotency_key,
                    "parent_run_token": rec.parent_run_token,
                    "role": node.role,
                    "tools": list(node.tools),
                    "permissions": list(node.permissions),
                    "timeout_seconds": node.timeout_seconds,
                    "max_attempts": node.max_attempts,
                    "dependencies": list(node.dependencies),
                    "parent_task_id": rec.parent_task_id,
                    "parent_agent_id": rec.parent_agent_id,
                    "agent_id": lease.agent_id if lease else rec.agent_id,
                    "fencing_token": lease.fencing_token
                    if lease
                    else rec.fencing_token or 0,
                    "model": rec.model_used
                    or (
                        model_policy.get("model")
                        if isinstance(model_policy, Mapping)
                        else None
                    ),
                    "fallback_model": rec.fallback_used
                    or (
                        model_policy.get("fallback_model")
                        if isinstance(model_policy, Mapping)
                        else None
                    ),
                    "attempts": rec.attempts,
                    "blocker": rec.blocker,
                    "policy_profile": rec.policy_profile,
                    "paper_only": rec.policy_profile in {"quantlab", "quantlab-paper"},
                    "telemetry": list(rec.telemetry),
                    "ts": str(self.clock()),
                }
            )
        edges: list[dict[str, object]] = []
        for task_id in sorted(self._tasks):
            node = self._tasks[task_id].node
            if node.parent_id is not None:
                edges.append({"from": node.parent_id, "to": task_id, "kind": "parent"})
            for dep in node.dependencies:
                edges.append({"from": dep, "to": task_id, "kind": "dependency"})
        agents_snapshot: list[dict[str, object]] = []
        for task_id in sorted(self._tasks):
            rec = self._tasks[task_id]
            lease = rec.lease
            agent_id = lease.agent_id if lease is not None else rec.agent_id
            if agent_id is not None:
                agents_snapshot.append(
                    {
                        "agent_id": agent_id,
                        "holder": lease.holder if lease is not None else None,
                        "fencing_token": (
                            lease.fencing_token
                            if lease is not None
                            else rec.fencing_token or 0
                        ),
                        "lease_until": lease.lease_until if lease is not None else None,
                        "task_id": task_id,
                        "state": rec.state.value,
                        "parent_agent_id": rec.parent_agent_id,
                        "parent_task_id": rec.parent_task_id,
                    }
                )
        return {
            "tasks": tasks_snapshot,
            "edges": edges,
            "agents": agents_snapshot,
            "policy_profiles": sorted({rec.policy_profile for rec in self._tasks.values()}),
            "paper_only": bool(self._tasks) and all(rec.policy_profile in {"quantlab", "quantlab-paper"} for rec in self._tasks.values()),
            "repo": next(iter(self._tasks.values())).repo if self._tasks else "",
            "issue": next(iter(self._tasks.values())).issue if self._tasks else "",
            "observed_at": str(self.clock()),
            "version": "v1.2.0",
            "graph_latency": self._graph_latency,
            "clock_snapshot": self.clock(),
            "ts": str(self.clock()),
        }

    def export_snapshot(self, target: Path) -> dict[str, object]:
        snapshot = self.snapshot()
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, sort_keys=True, indent=2)
            fh.write("\n")
        target.chmod(0o640)
        return snapshot

    # -- replay --------------------------------------------------------------

    def replay(self) -> int:
        events = self.audit_log.replay()
        applied = sum(
            1
            for e in events
            if e.get("event")
            in {
                "submit",
                "claim",
                "complete",
                "child_result",
                "child_cleanup_complete",
                "child_pre_delivery_cleanup_complete",
                "child_agent_start_attempted",
                "child_pane_creation_attempted",
                "child_pane_split_started",
                "child_pane_recovered",
                "child_pre_delivery_failed",
                "fail",
                "cancel",
                "reclaim",
                "spawn_child",
                "execution_observed",
                "execution_session_bound",
                "bind_parent",
                "child_prompt_bound",
            }
        )
        for e in events:
            event_type = e.get("event")
            if event_type == "submit":
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is None:
                    node = TaskNode(
                        id=task_id,
                        parent_id=str(e["parent_id"]) if e.get("parent_id") else None,
                        type=str(e.get("type", "agent")),
                        role=str(e.get("role", "reader")),
                        objective=str(e.get("objective", f"task {task_id}")),
                        inputs=e.get("inputs", ()),
                        expected_outputs=e.get("expected_outputs", ()),
                        dependencies=tuple(e.get("dependencies", [])),
                        priority=int(e.get("priority", 0)),
                        resource_class=str(e.get("resource_class", "standard")),
                        model_policy={
                            "model": str(e["model"]) if e.get("model") else "laguna",
                            "fallback_model": str(e["fallback_model"])
                            if e.get("fallback_model")
                            else "longcat",
                        },
                        tools=tuple(e.get("tools", [])),
                        permissions=tuple(e.get("permissions", [])),
                        timeout_seconds=int(e.get("timeout_seconds", 1800)),
                        max_attempts=int(e.get("max_attempts", 1)),
                    )
                    rec = TaskRecord(
                        node=node,
                        parent_task_id=str(e["parent_id"])
                        if e.get("parent_id")
                        else None,
                        parent_agent_id=str(e["parent_agent_id"])
                        if e.get("parent_agent_id")
                        else None,
                        repo=str(e.get("repo", "default")),
                        issue=str(e.get("issue", "")),
                        policy_profile=str(e.get("policy_profile", "default")),
                        model_used=str(e["model"]) if e.get("model") else None,
                        fallback_used=str(e["fallback_model"])
                        if e.get("fallback_model")
                        else None,
                    )
                    self._tasks[task_id] = rec
                rec.state = LifecycleState.PENDING
                rec.telemetry = list(e.get("telemetry", []))
                rec.model_used = str(e["model"]) if e.get("model") else rec.model_used
                rec.fallback_used = (
                    str(e["fallback_model"])
                    if e.get("fallback_model")
                    else rec.fallback_used
                )
                if e.get("agent_id"):
                    rec.agent_id = str(e["agent_id"])
                if e.get("fencing_token") is not None:
                    rec.fencing_token = int(e["fencing_token"])
                if e.get("parent_agent_id"):
                    rec.parent_agent_id = str(e["parent_agent_id"])
                if e.get("parent_id"):
                    rec.parent_task_id = str(e["parent_id"])
                if e.get("parent_task_id"):
                    rec.parent_task_id = str(e["parent_task_id"])
            elif event_type == "claim":
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is None:
                    continue
                rec.lease = Lease(
                        task_id=task_id,
                        agent_id=str(e.get("agent_id", "")),
                        holder=str(e.get("holder", "scheduler")),
                        fencing_token=int(e.get("fencing_token", 0)),
                        lease_until=float(e.get("lease_until", 0.0)),
                    )
                rec.state = LifecycleState.RUNNING
                rec.attempt_state = str(e.get("attempt_state", "accepted"))
                rec.run_token = str(e["run_token"]) if e.get("run_token") else rec.run_token
                rec.idempotency_key = str(e["idempotency_key"]) if e.get("idempotency_key") else rec.idempotency_key
                rec.agent_id = rec.lease.agent_id
                rec.fencing_token = rec.lease.fencing_token
                self._claims[task_id] = rec.lease
                if "managed_start" in e:
                    from .security import InvocationIdentity,SecurityError
                    start=e["managed_start"]
                    try:
                        expected=InvocationIdentity(consumer="github:"+rec.repo,agent_id=rec.agent_id,
                            parent_agent_id=rec.parent_agent_id,parent_task_id=rec.parent_task_id,
                            task_id=rec.id,run_token=rec.run_token,fencing_token=rec.fencing_token)
                        valid=(isinstance(start,dict) and set(start)=={"version","identity","idempotency_key","marker"}
                            and type(start["version"]) is int and start["version"]==1
                            and InvocationIdentity.from_dict(start["identity"])==expected
                            and start["idempotency_key"]==rec.idempotency_key
                            and start["marker"]=="child-"+rec.run_token
                            and rec.delegation_key is not None and not rec.pre_delivery_pane_creation_attempted)
                    except (SecurityError,ValueError,TypeError,KeyError):valid=False
                    if not valid:raise SchedulerError("invalid atomic managed claim intent")
                    rec.pre_delivery_pane_creation_attempted=True
                    rec.pane_split_started=False
                    rec.execution_agent,rec.execution_marker=rec.agent_id,start["marker"]
            elif event_type in {"complete", "child_result"}:
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is not None:
                    status = str(e.get("status", "completed"))
                    states = {"completed": LifecycleState.DONE,
                              "blocked": LifecycleState.BLOCKED,
                              "failed": LifecycleState.FAILED}
                    if status not in states:
                        raise SchedulerError("invalid durable child result status")
                    if event_type == "child_result":
                        try:
                            evidence = e["evidence"]
                            canonical = json.dumps(evidence, sort_keys=True,
                                                   ensure_ascii=False, allow_nan=False).encode("utf-8")
                            valid = (isinstance(evidence, list) and bool(evidence)
                                     and rec.delegation_key is not None
                                     and rec.lease is not None
                                     and rec.run_token == e.get("run_token")
                                     and rec.idempotency_key == e.get("idempotency_key")
                                     and rec.lease.agent_id == e.get("agent_id")
                                     and rec.lease.fencing_token == e.get("fencing_token")
                                     and hashlib.sha256(canonical).hexdigest() ==
                                     e.get("artifact_sha256"))
                        except (KeyError, TypeError, ValueError):
                            valid = False
                        if not valid:
                            raise SchedulerError("invalid durable child result evidence")
                    rec.state = states[status]
                    rec.attempt_state = "terminal"
                    rec.result_status = status if event_type == "child_result" else None
                    rec.result_artifact_sha256 = (str(e["artifact_sha256"])
                                                  if event_type == "child_result" else None)
                    rec.result_evidence_canonical = (json.dumps(e["evidence"], sort_keys=True,
                        ensure_ascii=False, allow_nan=False).encode("utf-8")
                        if event_type == "child_result" else None)
                    if rec.result_evidence_canonical is not None and len(rec.result_evidence_canonical) > 262144:
                        raise SchedulerError("durable child evidence exceeds limit")
                    rec.lease = None
                    self._claims.pop(task_id, None)
                    if e.get("fencing_token") is not None:
                        rec.fencing_token = int(e["fencing_token"])
                    if e.get("agent_id"):
                        rec.agent_id = str(e["agent_id"])
            elif event_type == "child_owned_mounts_observed":
                from .security import InvocationIdentity
                from .owned_write_mounts import validate_owned_mount_evidence
                identity=InvocationIdentity.from_dict(e.get("identity"))
                rec=self._tasks.get(identity.task_id)
                if (set(e)!={"event","identity","ownership_sha256","worktree_identity","mounts"}
                        or rec is None or rec.ownership is None or rec.ownership_reservation is None
                        or e["ownership_sha256"]!=rec.ownership.hash
                        or e["worktree_identity"]!=rec.worktree_identity
                        or identity.to_json()!=InvocationIdentity("github:"+rec.repo,rec.agent_id,
                            rec.parent_agent_id,rec.parent_task_id,rec.id,rec.run_token,rec.fencing_token).to_json()):
                    raise SchedulerError("owned mount replay binding mismatch")
                rows=validate_owned_mount_evidence(rec.ownership,e["mounts"])
                if rec.owned_write_mounts not in (None,rows):
                    raise SchedulerError("owned mount replay changed")
                rec.owned_write_mounts=rows
            elif event_type == "child_ownership_reserved":
                rec=self._tasks.get(e.get("task_id"))
                if rec is None or rec.parent_task_id is None:raise SchedulerError("ownership without child")
                from .security import InvocationIdentity
                parent=InvocationIdentity.from_dict(e["parent"])
                expected=OwnershipRegistry.key(parent,rec.id)
                if (e["reservation"]!=expected or parent.task_id!=rec.parent_task_id
                        or parent.agent_id!=rec.parent_agent_id or parent.consumer!="github:"+rec.repo
                        or e.get("ownership_sha256")!=(rec.ownership.hash if rec.ownership else None)
                        or rec.ownership_reservation not in (None,expected)):
                    raise SchedulerError("durable ownership reservation mismatch")
                rec.ownership_reservation=expected
            elif event_type == "fail":
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is not None:
                    rec.state = LifecycleState.FAILED
                    rec.lease = None
                    self._claims.pop(task_id, None)
                    rec.attempts = int(e.get("attempts", 1))
            elif event_type == "cancel":
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is not None:
                    rec.state = LifecycleState.CANCELLED
                    rec.lease = None
                    self._claims.pop(task_id, None)
            elif event_type == "reclaim":
                for task_id, lease_data in (e.get("leases") or {}).items():
                    rec = self._tasks.get(task_id)
                    if rec is None or rec.delegation_key is not None or (rec.run_token and rec.attempt_state in {
                        "accepted", "delivery_uncertain", "result_ready", "verifying"
                    }):
                        continue
                    rec.lease = Lease(task_id=task_id,
                                      agent_id=str(lease_data["agent_id"]),
                                      holder=str(lease_data["holder"]),
                                      fencing_token=int(lease_data["fencing_token"]),
                                      lease_until=float(lease_data["lease_until"]))
                    rec.state = LifecycleState.PENDING
                    rec.attempt_state = "retry_scheduled"
                    self._claims[task_id] = rec.lease
            elif event_type == "spawn_child":
                child_id = str(e.get("child_id", ""))
                rec = self._tasks.get(child_id)
                if rec is None:
                    node = TaskNode(
                        id=child_id,
                        parent_id=str(e.get("parent_id", ""))
                        if e.get("parent_id")
                        else None,
                        type=str(e.get("type", "task")),
                        role=str(e.get("child_role", "reader")),
                        objective=str(e.get("child_task", "")),
                        dependencies=tuple(e.get("dependencies", [])),
                        inputs=e.get("inputs", ()),
                        expected_outputs=e.get("expected_outputs", ()),
                        priority=int(e.get("priority", 0)),
                        resource_class=str(e.get("resource_class", "standard")),
                        model_policy={
                            "model": str(e.get("model", "laguna")),
                            "fallback_model": str(e.get("fallback_model", "longcat")),
                        },
                        tools=tuple(e.get("child_tools", [])),
                        permissions=tuple(e.get("child_permissions", [])),
                        timeout_seconds=int(e.get("timeout_seconds", 1800)),
                        max_attempts=int(e.get("max_attempts", 1)),
                    )
                    rec = TaskRecord(
                        node=node,
                        parent_task_id=str(e["parent_id"])
                        if e.get("parent_id")
                        else None,
                        parent_agent_id=str(e["parent_agent_id"])
                        if e.get("parent_agent_id")
                        else None,
                        repo=str(e.get("repo", "default")),
                        issue=str(e.get("issue", "")),
                        policy_profile=str(e.get("policy_profile", "default")),
                        model_used=str(e.get("model", "laguna")),
                        fallback_used=str(e.get("fallback_model", "longcat")),
                    )
                    self._tasks[child_id] = rec
                rec.model_used = str(e.get("model", rec.model_used or "laguna"))
                rec.delegation_key = str(e["delegation_key"]) if e.get("delegation_key") else None
                rec.parent_run_token = str(e["parent_run_token"]) if e.get("parent_run_token") else None
                identity = e.get("worktree_identity", "")
                if not isinstance(identity, str):
                    raise SchedulerError("invalid durable child worktree identity")
                rec.worktree_identity = identity
                raw_ownership=e.get("ownership")
                ownership=ChildOwnership.from_json(raw_ownership) if raw_ownership is not None else None
                if rec.ownership is not None and rec.ownership!=ownership:
                    raise SchedulerError("durable ownership changed during replay")
                if ownership is not None and (ownership.integration_owner!=rec.parent_task_id
                        or tuple(ownership.hard_dependencies)!=tuple(rec.node.dependencies)):
                    raise SchedulerError("durable ownership graph mismatch")
                rec.ownership=ownership
                rec.fallback_used = str(
                    e.get("fallback_model", rec.fallback_used or "longcat")
                )
                if e.get("parent_id"):
                    rec.parent_task_id = str(e["parent_id"])
                if e.get("parent_agent_id"):
                    rec.parent_agent_id = str(e["parent_agent_id"])
                if e.get("agent_id") and rec.lease is None:
                    rec.lease = Lease(
                        task_id=child_id,
                        agent_id=str(e.get("agent_id", "")),
                        holder=str(e.get("holder", str(e.get("agent_id", "")))),
                        fencing_token=int(e.get("fencing_token", 0)),
                        lease_until=float(e.get("lease_until", 0.0)),
                    )
                    self._claims[child_id] = rec.lease
                    rec.agent_id = rec.lease.agent_id
                    rec.fencing_token = rec.lease.fencing_token
            elif event_type == "execution_observed":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if rec is not None:
                    if rec.run_token == str(e.get("run_token", "")):
                        rec.observed_execution = str(e.get("state", "unavailable"))
                        rec.observation_source = str(e.get("source", ""))
                        rec.observed_at = str(e.get("ts", ""))
            elif event_type == "child_prompt_bound":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if rec is not None:
                    rec.delivery_prompt_sha256 = str(e.get("sha256", ""))
            elif event_type == "execution_session_bound":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if rec is not None and rec.run_token == str(e.get("run_token", "")):
                    rec.execution_agent = str(e.get("agent_name", ""))
                    rec.execution_pane = str(e.get("pane_id", ""))
                    rec.execution_marker = str(e.get("marker", ""))
            elif event_type in {"execution_sandbox_attested","execution_bootstrap_attested"}:
                rec = self._tasks.get(str(e.get("task_id", "")))
                attestation = e.get("attestation")
                if (
                    rec is None
                    or rec.run_token != str(e.get("run_token", ""))
                    or not isinstance(attestation, dict)
                    or attestation.get("authority") != "herdr-runtime"
                    or attestation.get("kind") != "bwrap"
                    or attestation.get("task_id") != rec.id
                    or attestation.get("run_token") != rec.run_token
                    or attestation.get("agent_name") != rec.execution_agent
                    or attestation.get("pane_id") != rec.execution_pane
                    or attestation.get("marker") != rec.execution_marker
                    or attestation.get("fencing_token") != rec.fencing_token
                    or attestation.get("worktree_identity") != rec.worktree_identity
                    or type(attestation.get("sandbox_pid")) is not int
                    or int(attestation.get("sandbox_pid", 0)) <= 0
                    or not isinstance(attestation.get("policy_sha256"), str)
                    or re.fullmatch(r"[0-9a-f]{64}", str(attestation.get("policy_sha256"))) is None
                    or not isinstance(attestation.get("verified_at"), str)
                ):
                    raise SchedulerError("invalid child sandbox attestation")
                if rec.ownership is not None:
                    from .owned_write_mounts import validate_owned_mount_evidence
                    if (rec.owned_write_mounts is None
                            or attestation.get("ownership_sha256")!=rec.ownership.hash
                            or validate_owned_mount_evidence(rec.ownership,attestation.get("owned_write_mounts"))
                               !=rec.owned_write_mounts):
                        raise SchedulerError("owned mount attestation replay mismatch")
                if "invocation_policy" in attestation:
                    from herdr.policy_launch import validate_policy_evidence
                    from herdr.security import InvocationIdentity, SecurityError
                    try:
                        validate_policy_evidence(attestation["invocation_policy"], identity=InvocationIdentity(
                            consumer="github:" + rec.repo, agent_id=rec.agent_id,
                            parent_agent_id=rec.parent_agent_id, parent_task_id=rec.parent_task_id,
                            task_id=rec.id, run_token=rec.run_token, fencing_token=rec.fencing_token))
                    except (SecurityError, TypeError, ValueError) as exc:
                        raise SchedulerError("invalid child invocation policy evidence") from exc
                if event_type=="execution_sandbox_attested" and (
                        attestation.get("invocation_policy") or {}).get("schema_version")=="herdr-policy-launch-3":
                    raise SchedulerError("bootstrap proof requires attested upgrade")
                if event_type=="execution_bootstrap_attested" and not self._bootstrap_upgrade_allowed(
                        rec,rec.execution_sandbox_attestation or {},attestation):
                    raise SchedulerError("invalid authenticated bootstrap upgrade")
                rec.execution_sandbox_verified = True
                rec.execution_sandbox_attestation = json.loads(json.dumps(attestation))
            elif event_type == "child_pane_creation_attempted":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if (rec is None or rec.delegation_key is None or rec.state is not LifecycleState.RUNNING
                        or rec.lease is None or rec.pre_delivery_pane_creation_attempted
                        or any((rec.execution_agent, rec.execution_pane, rec.execution_marker))
                        or (rec.run_token, rec.agent_id, rec.fencing_token, rec.idempotency_key) !=
                           (e.get("run_token"), e.get("agent_id"), e.get("fencing_token"), e.get("idempotency_key"))
                        or e.get("marker") != f"child-{rec.run_token}"):
                    raise SchedulerError("invalid child pane intent")
                version=e.get("split_protocol_version")
                if version is not None and (type(version) is not int or version != 1):
                    raise SchedulerError("invalid split protocol version")
                rec.pane_split_started = False if version == 1 else None
                rec.pre_delivery_pane_creation_attempted = True
                rec.execution_agent, rec.execution_marker = rec.agent_id, str(e["marker"])
            elif event_type == "child_pane_split_started":
                rec=self._tasks.get(str(e.get("task_id","")))
                if (rec is None or rec.state is not LifecycleState.RUNNING or rec.lease is None
                        or not rec.pre_delivery_pane_creation_attempted or rec.pane_split_started is not False
                        or rec.execution_pane is not None or rec.pre_delivery_agent_start_attempted
                        or type(e.get("split_protocol_version")) is not int or e["split_protocol_version"] != 1
                        or (rec.run_token,rec.agent_id,rec.fencing_token,rec.idempotency_key) !=
                           (e.get("run_token"),e.get("agent_id"),e.get("fencing_token"),e.get("idempotency_key"))):
                    raise SchedulerError("invalid or repeated split start")
                rec.pane_split_started=True
            elif event_type == "child_pane_recovered":
                rec = self._tasks.get(str(e.get("task_id", "")))
                pane = e.get("pane_id")
                if (rec is None or not rec.pre_delivery_pane_creation_attempted
                        or rec.pre_delivery_agent_start_attempted
                        or not isinstance(pane, str) or not pane or len(pane) > 256
                        or rec.execution_pane not in {None, pane}
                        or (rec.state is not LifecycleState.RUNNING and not rec.pre_delivery_failure)
                        or (rec.run_token, rec.agent_id, rec.fencing_token, rec.idempotency_key, rec.execution_marker) !=
                           (e.get("run_token"), e.get("agent_id"), e.get("fencing_token"), e.get("idempotency_key"),
                            e.get("marker"))):
                    raise SchedulerError("invalid recovered child pane evidence")
                rec.execution_pane = pane
            elif event_type == "child_agent_start_attempted":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if (rec is None or rec.run_token != e.get("run_token") or not rec.execution_pane
                        or rec.state is not LifecycleState.RUNNING or rec.pre_delivery_agent_start_attempted):
                    raise SchedulerError("invalid or repeated child agent start evidence")
                version=e.get("delivery_protocol_version")
                if version is not None and (type(version) is not int or version!=1):
                    raise SchedulerError("invalid child delivery protocol")
                if version==1 and (e.get("agent_id"),e.get("fencing_token"),e.get("idempotency_key"))!=(
                        rec.agent_id,rec.fencing_token,rec.idempotency_key):
                    raise SchedulerError("child agent start invocation identity changed")
                rec.pre_delivery_agent_start_attempted = True
                rec.economic_delivery_attempted=False if version==1 else None
            elif event_type == "child_prompt_delivery_attempted":
                rec=self._tasks.get(str(e.get("task_id","")))
                if (rec is None or rec.state is not LifecycleState.RUNNING
                    or rec.economic_delivery_attempted is not False or not rec.pre_delivery_agent_start_attempted
                    or (rec.run_token,rec.agent_id,rec.fencing_token,rec.idempotency_key,rec.delivery_prompt_sha256)!=
                        (e.get("run_token"),e.get("agent_id"),e.get("fencing_token"),e.get("idempotency_key"),e.get("prompt_sha256"))):
                    raise SchedulerError("invalid or repeated child prompt delivery")
                rec.economic_delivery_attempted=True
            elif event_type == "child_pre_delivery_failed":
                rec = self._tasks.get(str(e.get("task_id", "")))
                lease = rec.lease if rec else None
                reason = e.get("reason")
                if (rec is None or rec.delegation_key is None or rec.state is not LifecycleState.RUNNING
                        or lease is None or not isinstance(reason, str) or not reason
                        or (rec.run_token, rec.agent_id, rec.fencing_token, rec.idempotency_key) !=
                           (e.get("run_token"), e.get("agent_id"), e.get("fencing_token"),
                            e.get("idempotency_key"))
                        or not isinstance(e.get("cleanup_complete"), bool)
                        or e["cleanup_complete"]
                        or rec.pre_delivery_agent_start_attempted and rec.economic_delivery_attempted is not False
                        ):
                    raise SchedulerError("invalid child pre-delivery failure")
                rec.state = LifecycleState.BLOCKED
                rec.attempt_state = "terminal"
                rec.pre_delivery_failure = reason
                rec.pre_delivery_pane_creation_attempted = bool(e.get("pane_creation_attempted"))
                rec.blocker = reason
                rec.cleanup_complete = e["cleanup_complete"]
                rec.lease = None
                self._claims.pop(rec.node.id, None)
            elif event_type == "child_cleanup_complete":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if (rec is None or rec.delegation_key is None or rec.attempt_state != "terminal"
                        or not all((rec.execution_pane, rec.execution_agent,
                                    rec.execution_marker, rec.idempotency_key))
                        or rec.execution_agent != rec.agent_id
                        or (e.get("run_token"), e.get("fencing_token"),
                            e.get("idempotency_key"), e.get("agent_name"),
                            e.get("pane_id"), e.get("marker")) !=
                           (rec.run_token, rec.fencing_token, rec.idempotency_key,
                            rec.execution_agent, rec.execution_pane, rec.execution_marker)):
                    raise SchedulerError("invalid durable child cleanup evidence")
                rec.cleanup_complete = True
            elif event_type == "child_pre_delivery_cleanup_complete":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if (rec is None or not rec.pre_delivery_failure or rec.execution_pane
                        or rec.pre_delivery_pane_creation_attempted and rec.pane_split_started is not False
                        or rec.attempt_state != "terminal"
                        or (e.get("run_token"), e.get("fencing_token"),
                            e.get("idempotency_key")) !=
                           (rec.run_token, rec.fencing_token, rec.idempotency_key)):
                    raise SchedulerError("invalid pre-delivery cleanup evidence")
                rec.cleanup_complete = True
            elif event_type == "bind_parent":
                rec = self._tasks.get(str(e.get("task_id", "")))
                if rec is not None and rec.lease is not None:
                    rec.lease = replace(rec.lease, agent_id=str(e.get("agent_id", "")),
                                        holder="external",
                                        fencing_token=int(e.get("fencing_token", 0)))
                    rec.agent_id = rec.lease.agent_id
                    rec.fencing_token = rec.lease.fencing_token
                    self._claims[rec.node.id] = rec.lease
        max_fence = max((int(e.get("fencing_token") or 0) for e in events), default=0)
        max_fence = max(max_fence, max((rec.fencing_token or 0 for rec in self._tasks.values()), default=0))
        self._next_fencing_token_value = max(self._next_fencing_token_value, max_fence + 1)
        agent_numbers = [int(match.group(1)) for rec in self._tasks.values()
                         for match in [re.fullmatch(r"agent-(\d+)", rec.agent_id or "")]
                         if match]
        self._next_agent_id_value = max(self._next_agent_id_value,
                                        max(agent_numbers, default=0) + 1)
        return applied

    # -- internal helpers ----------------------------------------------------

    def _deny(self, reason: DenyReason, detail: str = "") -> None:
        self.audit_log.append(
            {
                "event": "deny",
                "reason": reason.value,
                "detail": detail,
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self.audit_log.flush()

    def _next_agent_id(self) -> int:
        with self._next_agent_id_lock:
            current = self._next_agent_id_value
            self._next_agent_id_value += 1
            return current

    def _next_fencing_token(self) -> int:
        with self._next_fencing_token_lock:
            current = self._next_fencing_token_value
            self._next_fencing_token_value += 1
            return current

    def bind_external_parent(
        self, task_id: str, agent_id: str, *, fencing_token: int = 0
    ) -> Lease:
        """Bind an external agent as the parent of an existing task."""
        rec = self._tasks.get(task_id)
        if rec is None:
            raise SchedulerError(f"unknown task: {task_id}")
        lease = Lease(
            task_id=task_id,
            agent_id=agent_id,
            holder="external",
            fencing_token=fencing_token or self._next_fencing_token(),
            lease_until=self.clock() + self.budget.claim_ttl_seconds,
        )
        rec.lease = lease
        rec.agent_id = agent_id
        rec.parent_agent_id = agent_id
        self._claims[task_id] = lease
        self.audit_log.append(
            {
                "event": "bind_parent",
                "task_id": task_id,
                "agent_id": agent_id,
                "fencing_token": lease.fencing_token,
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self._emit_task_telemetry(
            rec,
            EventType.TASK_STATE,
            state=rec.state.value,
            moment=self.clock(),
        )
        return lease

    def register_external_parent_attempt(
        self, *, task_id: str, run_token: str, idempotency_key: str,
        agent_name: str, pane_id: str, marker: str, repo: str, issue: str,
        role: str, tools: Sequence[str], permissions: Sequence[str],
        policy_profile: str,
    ) -> TaskRecord:
        """Durably bind an already running Agent Stack attempt to this scheduler."""
        if not all((task_id, run_token, idempotency_key, agent_name, pane_id,
                    marker, repo, role, policy_profile)):
            raise SchedulerError("external parent identity incomplete")
        existing = self._tasks.get(task_id)
        if existing is not None:
            if (existing.run_token, existing.idempotency_key,
                    existing.execution_agent, existing.execution_pane,
                    existing.execution_marker) != (run_token, idempotency_key,
                    agent_name, pane_id, marker):
                raise SchedulerError("external parent attempt mismatch")
            return existing
        node = TaskNode(id=task_id, parent_id=None, type="task", role=role,
                        objective=f"external durable attempt {task_id}",
                        inputs=[{"artifact_ref": "agent-stack-task"}],
                        expected_outputs=[{"kind": "result"}], dependencies=[],
                        priority=0, resource_class="standard",
                        model_policy={"model": "external"}, tools=tuple(tools),
                        permissions=tuple(permissions), timeout_seconds=3600,
                        max_attempts=1)
        rec = TaskRecord(node=node, state=LifecycleState.RUNNING,
                         repo=repo, issue=issue, policy_profile=policy_profile,
                         agent_id=agent_name, run_token=run_token,
                         idempotency_key=idempotency_key, attempt_state="accepted",
                         execution_agent=agent_name, execution_pane=pane_id,
                         execution_marker=marker)
        rec.lease = Lease(task_id, agent_name, "external", self._next_fencing_token(),
                          self.clock() + self.budget.claim_ttl_seconds)
        rec.fencing_token = rec.lease.fencing_token
        self._tasks[task_id] = rec
        self._claims[task_id] = rec.lease
        self.audit_log.append({"event": "submit", "task_id": task_id,
                               "repo": repo, "issue": issue, "role": role,
                               "tools": list(tools), "permissions": list(permissions),
                               "policy_profile": policy_profile,
                               "objective": node.objective, "agent_id": agent_name,
                               "fencing_token": rec.fencing_token})
        self.audit_log.append({"event": "claim", "task_id": task_id,
                               "agent_id": agent_name, "holder": "external",
                               "fencing_token": rec.fencing_token,
                               "lease_until": rec.lease.lease_until,
                               "run_token": run_token,
                               "idempotency_key": idempotency_key,
                               "attempt_state": "accepted"})
        self.audit_log.append({"event": "execution_session_bound", "task_id": task_id,
                               "run_token": run_token, "agent_name": agent_name,
                               "pane_id": pane_id, "marker": marker})
        self.audit_log.flush()
        return rec


# ---------------------------------------------------------------------------
# Canary convenience (consumer-specific — kept minimal, not in core API)
# ---------------------------------------------------------------------------

DEFAULT_SNAPSHOT = Path("/var/lib/agent-platform-herdr/swarm.json")


class HerdrRunner(Protocol):
    def run(self, args: Sequence[str], timeout_seconds: float = 30.0) -> Any: ...


@dataclass
class SubprocessHerdrRunner:
    executable: str = "herdr"
    env: Mapping[str, str] | None = None

    def run(self, args: Sequence[str], timeout_seconds: float = 30.0) -> Any:
        proc = subprocess.run(
            [self.executable, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=dict(self.env) if self.env is not None else None,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }


class HerdrRuntimeError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def build_two_child_canary(
    *,
    parent_agent_id: str,
    audit_path: Path,
    clock: Callable[[], float],
) -> tuple[DynamicChildScheduler, Lease, list[Lease], dict[str, str]]:
    scheduler = DynamicChildScheduler(
        budget=SchedulerBudget(
            max_global_concurrency=4,
            max_per_repo=4,
            max_per_issue=3,
            max_dag_nodes=64,
            max_dag_depth=4,
            max_dag_fanout=6,
            claim_ttl_seconds=1800.0,
        ),
        clock=clock,
        audit_log=AuditLog(audit_path),
    )
    parent = TaskNode(
        id="runtime-canary-parent",
        parent_id=None,
        type="task",
        role="reader",
        objective="coordinate safe read-only child canary",
        inputs=[{"artifact_ref": "fixture"}],
        expected_outputs=[{"kind": "result"}],
        dependencies=[],
        priority=1,
        resource_class="small",
        model_policy={"model": "laguna", "fallback_model": "longcat"},
        tools=("read_file",),
        permissions=("repo:read",),
        timeout_seconds=1800,
        max_attempts=1,
    )
    scheduler.submit(
        TaskGraph(
            envelope=TaskGraphEnvelope(
                issue="Bbambaaamm/herdr#3",
                spec_hash="sha256:" + "a" * 64,
                graph_version=GRAPH_VERSION,
                created_at=datetime.now(UTC).isoformat(),
                planner="herdr-canary-adapter@1.0",
                policy_profile="quantlab-paper",
            ),
            nodes=(parent,),
        ),
        repo="Bbambaaamm/herdr",
        issue="3",
    )
    child_nodes: list[TaskNode] = []
    for label in ("a", "b"):
        child = scheduler.spawn_child(
            "runtime-canary-parent",
            ChildProposal(
                parent_role="reader",
                parent_tools=("read_file",),
                child_role="reader",
                child_tools=("read_file",),
                child_task=f"safe-read-only-canary-{label}",
            ),
        )
        if isinstance(child, DenyDecision):
            raise HerdrRuntimeError("child_admission_denied", child.reason.value)
        child_nodes.append(child)
    leases = [
        lease
        for lease in scheduler.dispatch()
        if lease.task_id in {child.id for child in child_nodes}
    ]
    if len(leases) != 2:
        raise HerdrRuntimeError("two_child_dispatch_failed", f"leases={len(leases)}")
    prompts = {
        leases[0].task_id: "PAPER-only canary A",
        leases[1].task_id: "PAPER-only canary B",
    }
    parent_lease = scheduler._claims.get("runtime-canary-parent")
    if parent_lease is None:
        raise HerdrRuntimeError("parent_lease_missing", "no parent lease for canary")
    return scheduler, parent_lease, leases, prompts
