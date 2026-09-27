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
import subprocess
import threading
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Protocol

from herdr.taskgraph import (
    GRAPH_VERSION,
    GraphValidationError,
    LifecycleState,
    TaskGraph,
    TaskGraphEnvelope,
    TaskNode,
)

HERE = Path(__file__).resolve().parent
EVENT_LOG_NAME = "herdr-scheduler-events.jsonl"
SWARM_SNAPSHOT_NAME = "swarm.json"


# ---------------------------------------------------------------------------
# Denial taxonomy — generic reasons only, no consumer-specific constants
# ---------------------------------------------------------------------------


class DenyReason(StrEnum):
    DAG_NODE_LIMIT = "dag_node_limit"
    DAG_CYCLE = "dag_cycle"
    CHILD_TOOL_ESCALATION = "child_tool_escalation"
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
        "reader": frozenset({"read_file", "search_files", "read"}),
        "writer": frozenset(
            {"read_file", "search_files", "read", "patch", "write_file", "write"}
        ),
        "reviewer": frozenset(
            {
                "read_file",
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
        parent_prohibitive = set(proposal.parent_tools)
        if parent_prohibitive:
            outside_parent = child_tools - parent_prohibitive
            if outside_parent:
                return DenyDecision(
                    DenyReason.CHILD_TOOL_ESCALATION,
                    detail=f"child tools above parent: {sorted(outside_parent)}",
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
    child_permissions: tuple[str, ...] = ()


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
        if not self._buffer:
            return
        with self._lock:
            events = self._buffer
            self._buffer = []
        payload = (
            json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n" for e in events
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.writelines(payload)

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
    id: str | None = None  # set from node.id after submit

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
        self._tasks: dict[str, TaskRecord] = {}
        self._claims: dict[str, Lease] = {}
        self._next_agent_id_value: int = 1
        self._next_agent_id_lock = threading.Lock()
        self._next_fencing_token_value: int = 1
        self._next_fencing_token_lock = threading.Lock()
        self._repo_counter: dict[str, int] = defaultdict(int)
        self._repo_counter_lock = threading.Lock()
        self._graph_latency: float = 0.0

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
        if len(graph.nodes) > self.budget.max_dag_nodes:
            self._deny(
                DenyReason.DAG_NODE_LIMIT,
                detail=f"graph has {len(graph.nodes)} nodes; limit is {self.budget.max_dag_nodes}",
            )
            return
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
        contract: Mapping[str, object],
        *,
        repo: str = "Bbambaaamm/Autonomous-Quant-Lab",
        issue: str = "",
    ) -> None:
        """Submit from a generic envelope.nodes contract (TaskGraph230 adapter)."""
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
                graph_version=GRAPH_VERSION,
                created_at=datetime.now(UTC).isoformat(),
                planner=envelope_data.get("planner", "herdr-taskgraph230-adapter@1.0"),
                max_nodes=self.budget.max_dag_nodes,
                max_depth=self.budget.max_dag_depth,
                max_fanout=self.budget.max_dag_fanout,
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

    def dispatch(self, now: float | None = None) -> list[Lease]:
        now = now or self.clock()
        ready_nodes = sorted(self.ready(), key=lambda n: (n.priority, n.id))
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
                continue
            repo_ctx = rec.repo
            issue_ctx = rec.issue
            if used_repo[repo_ctx] >= self.budget.max_per_repo:
                rec.blocker = DenyReason.PER_REPO_LIMIT.value
                continue
            if issue_ctx and used_issue[issue_ctx] >= self.budget.max_per_issue:
                rec.blocker = DenyReason.PER_ISSUE_LIMIT.value
                continue
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
            rec.agent_id = lease.agent_id
            used_global += 1
            used_repo[repo_ctx] += 1
            if issue_ctx:
                used_issue[issue_ctx] += 1
            leases.append(lease)
            self.audit_log.append(
                {
                    "event": "claim",
                    "task_id": task_id,
                    "agent_id": lease.agent_id,
                    "fencing_token": lease.fencing_token,
                    "lease_until": lease.lease_until,
                    "ts": datetime.now(UTC).isoformat(),
                }
            )
        return leases

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
        self.audit_log.flush()
        # Propagate BLOCKED to dependents
        for other_id, other_rec in self._tasks.items():
            if (
                other_rec.state == LifecycleState.PENDING
                and task_id in other_rec.node.dependencies
            ):
                other_rec.state = LifecycleState.BLOCKED
                other_rec.blocker = f"prereq_failed:{task_id}"

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
            rec.telemetry.append(
                {
                    "event": "reclaim",
                    "ts": datetime.now(UTC).isoformat(),
                }
            )
        self.audit_log.append(
            {
                "event": "reclaim",
                "reclaimed": reclaimed,
                "ts": datetime.now(UTC).isoformat(),
            }
        )
        self.audit_log.flush()
        return reclaimed

    def cancel(self, task_id: str, reason: str = "manual-cancel") -> None:
        rec = self._tasks.get(task_id)
        if rec is None:
            return
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
        self.audit_log.flush()

    # -- child lifecycle -----------------------------------------------------

    def spawn_child(
        self,
        parent_id: str,
        proposal: ChildProposal,
    ) -> TaskNode | DenyDecision:
        decision = self.consumer_policy.evaluate_child_proposal(proposal)
        if not decision:
            self._deny(
                decision.reason,
                detail=f"child proposal denied for parent {parent_id}: {decision.reason.value}",
            )
            return decision
        parent_rec = self._tasks.get(parent_id)
        if parent_rec is None:
            deny = DenyDecision(
                DenyReason.UNKNOWN_TASK, detail=f"unknown parent: {parent_id}"
            )
            self._deny(deny.reason, deny.detail or "")
            return deny
        child_id = f"{parent_id}-child-{self._next_agent_id()}"
        child_node = TaskNode(
            id=child_id,
            parent_id=parent_id,
            type="task",
            role=proposal.child_role,
            objective=proposal.child_task,
            inputs=[{"artifact_ref": "fixture"}],
            expected_outputs=[{"kind": "result"}],
            dependencies=[],
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
        )
        self._tasks[child_id] = rec
        child_agent_id = f"agent-{self._next_agent_id()}"
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
                "repo": parent_rec.repo,
                "issue": parent_rec.issue,
                "policy_profile": parent_rec.policy_profile,
                "ts": str(self.clock()),
            }
        )
        self.audit_log.flush()
        return child_node

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
                    "paper_only": rec.policy_profile == "quantlab-paper",
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
            "paper_only": bool(self._tasks) and all(rec.policy_profile == "quantlab-paper" for rec in self._tasks.values()),
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
                "fail",
                "cancel",
                "reclaim",
                "spawn_child",
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
                if rec.lease is None:
                    rec.lease = Lease(
                        task_id=task_id,
                        agent_id=str(e.get("agent_id", "")),
                        holder=str(e.get("holder", "scheduler")),
                        fencing_token=int(e.get("fencing_token", 0)),
                        lease_until=float(e.get("lease_until", 0.0)),
                    )
                    rec.state = LifecycleState.RUNNING
                    rec.agent_id = rec.lease.agent_id
                    rec.fencing_token = rec.lease.fencing_token
            elif event_type == "complete":
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is not None:
                    rec.state = LifecycleState.DONE
                    if e.get("fencing_token") is not None:
                        rec.fencing_token = int(e["fencing_token"])
                    if e.get("agent_id"):
                        rec.agent_id = str(e["agent_id"])
            elif event_type == "fail":
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is not None:
                    rec.state = LifecycleState.FAILED
                    rec.attempts = int(e.get("attempts", 1))
            elif event_type == "cancel":
                task_id = str(e.get("task_id", ""))
                rec = self._tasks.get(task_id)
                if rec is not None:
                    rec.state = LifecycleState.CANCELLED
            elif event_type == "reclaim":
                pass
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
        return lease


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
