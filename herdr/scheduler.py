"""Herdr v1.2: Dependency-aware scheduler + dynamic child-agent lifecycle (#3).

Fail-closed, PAPER-only, offline-testable (stdlib + Herdr imports).

The scheduler consumes a TaskGraph (#2-style DAG) and:
  * validates planner graph output against hard caps (node/depth/fanout) so a
    planner cannot bypass limits by emitting a bigger graph;
  * resolves a READY queue from satisfied prerequisites — a dependent node
    cannot start before its prerequisite PASSED;
  * enforces max global/per-repo/per-issue concurrency before any spawn;
  * acquires a per-task lease (fencing) so a lost worker's task is reclaimed
    idempotently with no double commit (completion is SHA-keyed);
  * routes child-subtask proposals through a fail-closed PolicyGate (child tools
    ⊆ parent tools; no role escalation; PAPER-only; no live-broker / protected
    path / secret / external-network tools);
  * records the chosen model + fallback in per-task telemetry;
  * supports bounded retry/backoff (cap at max_retries) and blocker propagation
    (a FAILED prereq BLOCKEDs dependents);
  * persists lifecycle + denial/cancel events to an append-only JSONL audit log
    (crash/restart recovery via replay; durable cancellation).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

# --------------------------------------------------------------------------- #
# PAPER-only safety policy (fail-closed). Mirrors the conservative guard from
# #8; kept inline here so #3 is self-contained (herdr/ package is not yet
# merged into origin/main).
# --------------------------------------------------------------------------- #

LIVE_TRADING_TOOL_PREFIXES: tuple[str, ...] = (
    "alpaca-order",
    "alpaca-position",
    "alpaca-sse",
    "broker",
    "live-broker",
    "trade",
    "execution",
    "risk-engine",
)

PROTECTED_PATH_PREFIXES: tuple[str, ...] = (
    "backend/src/quantlab/trading.py",
    "backend/src/quantlab/phase4.py",
    "backend/src/quantlab/security.py",
)

SECRET_INDICATORS: tuple[str, ...] = (
    "api_key",
    "api_secret",
    "secret_key",
    "private_key",
    "client_secret",
    "password",
    "alpaca_key_id",
    "alpaca_secret_key",
    "api_admin_token",
)

EXTERNAL_NETWORK_TOOL_SUFFIXES: tuple[str, ...] = (
    ".post",
    ".put",
    ".patch",
    ".upload",
)

# Role-based tool allowlist. Reader tools ⊆ writer tools ⊆ operator tools.
# Operator tools (push/deploy/merge) are never auto-spawned.
_READER_TOOLS = frozenset(
    {
        "read_file",
        "read",
        "search_files",
        "grep",
        "web_search",
        "web_extract",
        "git_status",
        "git_log",
    }
)
_WRITER_TOOLS = _READER_TOOLS.union({"patch", "write_file", "delete_file", "git_add", "git_commit"})
_OPERATOR_TOOLS = _WRITER_TOOLS.union({"git_push", "deploy", "git_merge"})

ROLE_TOOL_ALLOWLIST: Mapping[str, frozenset[str]] = {
    "reader": _READER_TOOLS,
    "writer": _WRITER_TOOLS,
    "operator": _OPERATOR_TOOLS,
}

AUTO_SPAWNABLE_ROLES: frozenset[str] = frozenset({"reader", "writer"})

# Role ranking for permission-escalation checks.
_ROLE_RANK: Mapping[str, int] = {"reader": 0, "writer": 1, "operator": 2}


class DenyReason(StrEnum):
    """Machine-readable denial reasons — audited + visible in Machine City."""

    CHILD_TOOL_ESCALATION = "child_tool_escalation"
    CHILD_ROLE_ESCALATION = "child_role_escalation"
    NON_SPAWNABLE_ROLE = "non_spawnable_role"
    TOOL_NOT_IN_ROLE_ALLOWLIST = "tool_not_in_role_allowlist"
    LIVE_TRADING_TOOL = "live_trading_tool"
    PROTECTED_PATH = "protected_path"
    SECRET_ACCESS = "secret_access"  # noqa: S105 -- denial reason, not a credential
    NETWORK_POLICY = "network_policy"
    PLANNER_GRAPH_TOO_LARGE = "planner_graph_too_large"
    DAG_NODE_LIMIT = "dag_node_limit"
    DAG_DEPTH_LIMIT = "dag_depth_limit"
    DAG_FANOUT_LIMIT = "dag_fanout_limit"
    DAG_CYCLE = "dag_cycle"
    GLOBAL_CONCURRENCY_LIMIT = "global_concurrency_limit"
    PER_REPO_LIMIT = "per_repo_limit"
    PER_ISSUE_LIMIT = "per_issue_limit"
    RETRY_EXHAUSTED = "retry_exhausted"
    UNKNOWN_PARENT = "unknown_parent"
    PARENT_NOT_RUNNING = "parent_not_running"
    UNKNOWN_DEPENDENCY = "unknown_dependency"
    DUPLICATE_TASK = "duplicate_task"
    STALE_FENCE = "stale_fence"


# --------------------------------------------------------------------------- #
# Task model (#2 TaskGraph-style DAG).
# --------------------------------------------------------------------------- #


class LifecycleState(StrEnum):
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"  # terminal success
    FAILED = "failed"  # terminal after retries exhausted
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class SubtaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class TaskNode:
    """A single unit of work in a Herdr TaskGraph (DAG node)."""

    node_id: str
    task: str
    prereqs: tuple[str, ...] = ()
    role: str = "reader"
    tools: tuple[str, ...] = ()
    model: str = "default"
    fallback_model: str = "default-fallback"
    parent_node: str | None = None
    parent_task_id: str | None = None
    parent_agent_id: str | None = None
    agent_id: str | None = None
    fencing_token: int = 0
    max_seconds: int = 300
    max_retries: int = 3
    backoff_base: float = 2.0
    paper_only: bool = True
    repo: str = ""
    issue: str = ""


@dataclass(frozen=True)
class TaskGraph:
    """Immutable plan submitted by the planner (#2 semantics)."""

    nodes: tuple[TaskNode, ...]
    name: str = "plan"
    repo: str = ""
    issue: str = ""

    @property
    def root_id(self) -> str:
        return self.nodes[0].node_id if self.nodes else ""

    @property
    def by_id(self) -> dict[str, TaskNode]:
        return {n.node_id: n for n in self.nodes}

    def successors(self, node_id: str) -> list[str]:
        """Node IDs that directly depend on node_id."""
        return [n.node_id for n in self.nodes if node_id in n.prereqs]

    def node_count(self) -> int:
        return len(self.nodes)

    def max_depth(self) -> int:
        """Longest dependency/lineage path. Raises on cycles or unknown parents."""
        if not self.nodes:
            return 0
        memo: dict[str, int] = {}
        by_id = self.by_id

        def predecessors(node: TaskNode) -> tuple[str, ...]:
            ordered = list(node.prereqs)
            parent = node.parent_task_id or node.parent_node
            if parent and parent not in ordered:
                ordered.append(parent)
            return tuple(ordered)

        def depth(node_id: str, stack: tuple[str, ...]) -> int:
            if node_id in memo:
                return memo[node_id]
            if node_id in stack:
                raise ValueError(f"Cycle in DAG at {node_id}")
            node = by_id[node_id]
            parents = predecessors(node)
            if not parents:
                memo[node_id] = 1
                return 1
            unknown = [p for p in parents if p not in by_id]
            if unknown:
                raise ValueError(f"Unknown predecessor(s) for {node_id}: {unknown}")
            d = 1 + max(depth(p, stack + (node_id,)) for p in parents)
            memo[node_id] = d
            return d

        return max(depth(n.node_id, ()) for n in self.nodes)

    def max_fanout(self) -> int:
        """Max unique direct children/dependents of any single node."""
        if not self.nodes:
            return 0
        counts = {n.node_id: 0 for n in self.nodes}
        seen: set[tuple[str, str]] = set()
        for node in self.nodes:
            parents = list(node.prereqs)
            parent = node.parent_task_id or node.parent_node
            if parent and parent not in parents:
                parents.append(parent)
            for source in parents:
                edge = (source, node.node_id)
                if source in counts and edge not in seen:
                    seen.add(edge)
                    counts[source] += 1
        return max(counts.values()) if counts else 0

    def has_cycle(self) -> bool:
        try:
            self.max_depth()
            return False
        except ValueError:
            return True


@dataclass(frozen=True)
class SubtaskProposal:
    """A child-requested subtask → Herdr policy decision (fail-closed default).

    The scheduler never trusts the caller-provided parent role/tools for a real
    spawn: :meth:`spawn_child` rebinds them to the authoritative parent task.
    """

    parent_role: str
    parent_tools: tuple[str, ...]
    child_role: str
    child_tools: tuple[str, ...]
    child_task: str = ""
    paper_only: bool = True
    child_model: str = ""
    child_fallback_model: str = ""
    parent_task_id: str = ""
    dependencies: tuple[str, ...] = ()
    repo: str = ""
    issue: str = ""


@dataclass(frozen=True)
class SchedulerBudget:
    """Conservative admission + scheduling caps for the dynamic swarm.

    Scheduler-time ceilings complement (never replace) the runtime resource
    guards in Settings (worker_soft_rss_mb, market_job_min_available_mb, etc.).
    """

    max_global_concurrency: int = 4
    max_per_repo: int = 4
    max_per_issue: int = 3
    max_dag_nodes: int = 64
    max_dag_depth: int = 4
    max_dag_fanout: int = 6
    claim_ttl_seconds: float = 60.0
    default_model: str = "default"
    default_fallback_model: str = "default-fallback"


# --------------------------------------------------------------------------- #
# Audit log (append-only JSONL — durable lifecycle/deny/cancel events).
# --------------------------------------------------------------------------- #


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class AuditLog:
    """Append-only JSONL. Each line = one event. Corrupt line blocks replay."""

    def __init__(self, path: str | Path) -> None:
        self.path: Path = Path(path)

    def append(self, event: Mapping[str, object]) -> dict[str, object]:
        record: dict[str, object] = {"ts": _now_iso(), "event": event["event"]}
        record.update(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, sort_keys=True, default=str)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return record

    def replay(self) -> list[dict[str, object]]:
        events: list[dict[str, object]] = []
        if not self.path.exists():
            return events
        with self.path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    events.append(json.loads(raw))
                except json.JSONDecodeError:
                    raise  # tamper-evident: corrupt line must not be silently dropped
        return events


def _result_sha(result: str | bytes) -> str:
    m = hashlib.sha256()
    m.update(result if isinstance(result, bytes) else result.encode())
    return m.hexdigest()


def _herdr_agent_name(task_id: str, fencing_token: int, issue: str = "") -> str:
    """Return one deterministic, bounded Herdr-valid attempt identity."""
    issue_slug = re.sub(r"[^a-z0-9]", "", issue.lower())[:6] or "task"
    task_slug = re.sub(r"[^a-z0-9]", "", task_id.lower())[:8] or "task"
    digest = hashlib.sha256(f"{task_id}|{fencing_token}|{issue}".encode()).hexdigest()[:6]
    return f"q{issue_slug}-{task_slug}-{digest}-f{fencing_token}"[:32]


def _is_herdr_agent_name(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", value))


def _int_value(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _float_value(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value)


def _node_json(node: TaskNode) -> str:
    """Canonical node payload persisted in the append-only audit stream."""
    return json.dumps(
        {
            "node_id": node.node_id,
            "task": node.task,
            "prereqs": list(node.prereqs),
            "role": node.role,
            "tools": list(node.tools),
            "model": node.model,
            "fallback_model": node.fallback_model,
            "parent_node": node.parent_node,
            "parent_task_id": node.parent_task_id,
            "parent_agent_id": node.parent_agent_id,
            "agent_id": node.agent_id,
            "fencing_token": node.fencing_token,
            "max_seconds": node.max_seconds,
            "max_retries": node.max_retries,
            "backoff_base": node.backoff_base,
            "paper_only": node.paper_only,
            "repo": node.repo,
            "issue": node.issue,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _node_from_json(raw: object) -> TaskNode:
    """Restore a node exactly or fail closed on incomplete/corrupt metadata."""
    if not isinstance(raw, str):
        raise ValueError("task_added event missing canonical node payload")
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("node_id"), str):
        raise ValueError("task_added event has invalid canonical node payload")
    return TaskNode(
        node_id=data["node_id"],
        task=str(data.get("task", "")),
        prereqs=tuple(str(x) for x in data.get("prereqs", [])),
        role=str(data.get("role", "reader")),
        tools=tuple(str(x) for x in data.get("tools", [])),
        model=str(data.get("model", "default")),
        fallback_model=str(data.get("fallback_model", "default-fallback")),
        parent_node=data.get("parent_node"),
        parent_task_id=data.get("parent_task_id"),
        parent_agent_id=data.get("parent_agent_id"),
        agent_id=data.get("agent_id"),
        fencing_token=int(data.get("fencing_token", 0)),
        max_seconds=int(data.get("max_seconds", 300)),
        max_retries=int(data.get("max_retries", 3)),
        backoff_base=float(data.get("backoff_base", 2.0)),
        paper_only=data.get("paper_only") is True,
        repo=str(data.get("repo", "")),
        issue=str(data.get("issue", "")),
    )


# --------------------------------------------------------------------------- #
# Fail-closed policy gate for child-subtask proposals (#8 policy, inline).
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DenyDecision:
    denied: bool = True
    reason: DenyReason = DenyReason.LIVE_TRADING_TOOL
    detail: str = ""

    def __bool__(self) -> bool:
        return False


@dataclass(frozen=True)
class AllowDecision:
    denied: bool = False
    model: str = ""
    fallback_model: str = ""
    budget_utilization: Mapping[str, float] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return True


Decision = AllowDecision | DenyDecision


def _tool_is_denied(tool: str) -> DenyReason | None:
    lowered = tool.lower()
    if any(lowered.startswith(p) for p in LIVE_TRADING_TOOL_PREFIXES):
        return DenyReason.LIVE_TRADING_TOOL
    if any(p in lowered for p in PROTECTED_PATH_PREFIXES):
        return DenyReason.PROTECTED_PATH
    if any(p in lowered for p in SECRET_INDICATORS):
        return DenyReason.SECRET_ACCESS
    if any(lowered.endswith(s) for s in EXTERNAL_NETWORK_TOOL_SUFFIXES):
        return DenyReason.NETWORK_POLICY
    return None


class PolicyGate:
    """Fail-closed gate for a child agent requesting to spawn a subtask.

    * child role rank may not exceed parent role rank (no permission escalation)
    * child tools must be a subset of parent tools AND the child's role allowlist
    * child role must be auto-spawnable
    * PAPER-only: live-broker / protected-path / secret / network tools denied
    A child agent may never expand the tool/permission set available to it.
    """

    @staticmethod
    def evaluate(proposal: SubtaskProposal) -> Decision:
        # PAPER-only safety hooks FIRST (fail-closed): live-broker / protected-path /
        # secret / external-network tools are denied regardless of role/allowlist.
        if proposal.paper_only is not True:
            return DenyDecision(
                reason=DenyReason.LIVE_TRADING_TOOL,
                detail="subtask must be PAPER-only (paper_only=False refused)",
            )
        for tool in proposal.child_tools:
            denied = _tool_is_denied(tool)
            if denied is not None:
                return DenyDecision(
                    reason=denied,
                    detail=f"tool={tool!r} denied by PAPER-only/safety policy ({denied.value})",
                )

        # Role escalation check: child may never escalate permissions beyond parent.
        parent_rank = _ROLE_RANK.get(proposal.parent_role, -1)
        child_rank = _ROLE_RANK.get(proposal.child_role, -1)
        if child_rank < 0 or parent_rank < 0:
            return DenyDecision(
                reason=DenyReason.NON_SPAWNABLE_ROLE,
                detail=(
                    f"unknown role parent={proposal.parent_role!r} child={proposal.child_role!r}"
                ),
            )
        if child_rank > parent_rank:
            return DenyDecision(
                reason=DenyReason.CHILD_ROLE_ESCALATION,
                detail=(
                    f"child role={proposal.child_role!r} rank={child_rank} > "
                    f"parent role={proposal.parent_role!r} rank={parent_rank}"
                ),
            )
        if proposal.child_role not in AUTO_SPAWNABLE_ROLES:
            return DenyDecision(
                reason=DenyReason.NON_SPAWNABLE_ROLE,
                detail=f"role={proposal.child_role!r} is not auto-spawnable",
            )

        child_set = frozenset(proposal.child_tools)
        parent_set = frozenset(proposal.parent_tools)
        role_tools = ROLE_TOOL_ALLOWLIST.get(proposal.child_role, frozenset())

        # Child tools must be within the role allowlist.
        if child_set - role_tools:
            return DenyDecision(
                reason=DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST,
                detail=(
                    f"tools not in role allowlist {proposal.child_role!r}: "
                    f"{sorted(child_set - role_tools)}"
                ),
            )
        # Child may never escalate beyond parent, including an empty parent toolset.
        if child_set - parent_set:
            return DenyDecision(
                reason=DenyReason.CHILD_TOOL_ESCALATION,
                detail=f"child tools beyond parent: {sorted(child_set - parent_set)}",
            )
        return AllowDecision(
            model=proposal.child_model or "default",
            fallback_model=proposal.child_fallback_model or "default-fallback",
        )


# --------------------------------------------------------------------------- #
# Scheduler.
# --------------------------------------------------------------------------- #


@dataclass
class _TaskRecord:
    node: TaskNode
    state: LifecycleState = LifecycleState.PLANNED
    attempts: int = 0
    model_used: str = ""
    fallback_used: str = ""
    result_sha: str | None = None
    telemetry: list[dict[str, object]] = field(default_factory=list)
    children: list[str] = field(default_factory=list)
    agent_id: str = ""
    fencing_token: int = 0
    blocker: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0
    completed_at: float | None = None
    last_event_ref: int = 0


@dataclass
class _Lease:
    task_id: str
    holder: str
    agent_id: str
    lease_until: float
    fencing_token: int
    state: LifecycleState = LifecycleState.RUNNING


class DynamicChildScheduler:
    """Dependency-aware scheduler + dynamic child lifecycle (#3).

    Offline-testable: ``clock`` and ``audit_log`` are injected.
    """

    def __init__(
        self,
        budget: SchedulerBudget | None = None,
        clock: Callable[[], float] = time.time,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.budget = budget or SchedulerBudget()
        self._clock = clock
        self.audit_log = audit_log
        self._tasks: dict[str, _TaskRecord] = {}
        self._claims: dict[str, _Lease] = {}
        self._repo: str = ""
        self._issue: str = ""
        self._submitted: list[dict[str, object]] = []
        self._fencing_counter: int = 0
        self._event_seq: int = 0

    def task_node(self, task_id: str) -> TaskNode:
        """Return immutable task metadata for runtime admission or fail closed."""
        record = self._tasks.get(task_id)
        if record is None:
            raise KeyError(task_id)
        return record.node

    def graph_dimensions(self) -> tuple[int, int, int]:
        """Return current graph node/depth/fanout dimensions for admission."""
        if not self._tasks:
            return (0, 0, 0)
        graph = TaskGraph(
            nodes=tuple(self._tasks[key].node for key in sorted(self._tasks)),
            repo=self._repo,
            issue=self._issue,
        )
        return (graph.node_count(), graph.max_depth(), graph.max_fanout())

    # -- plan submission (planner output bounded by caps) ------------------- #
    @staticmethod
    def _node_to_payload(node: TaskNode) -> dict[str, object]:
        return {
            "node_id": node.node_id,
            "task": node.task,
            "prereqs": list(node.prereqs),
            "role": node.role,
            "tools": list(node.tools),
            "model": node.model,
            "fallback_model": node.fallback_model,
            "parent_node": node.parent_node,
            "parent_task_id": node.parent_task_id,
            "parent_agent_id": node.parent_agent_id,
            "agent_id": node.agent_id,
            "fencing_token": node.fencing_token,
            "max_seconds": node.max_seconds,
            "max_retries": node.max_retries,
            "backoff_base": node.backoff_base,
            "paper_only": node.paper_only,
            "repo": node.repo,
            "issue": node.issue,
        }

    @staticmethod
    def _node_from_payload(data: Mapping[str, object]) -> TaskNode:
        return TaskNode(
            node_id=str(data["node_id"]),
            task=str(data.get("task", "")),
            prereqs=_str_tuple(data.get("prereqs", [])),
            role=str(data.get("role", "reader")),
            tools=_str_tuple(data.get("tools", [])),
            model=str(data.get("model", "default")),
            fallback_model=str(data.get("fallback_model", "default-fallback")),
            parent_node=(str(data["parent_node"]) if data.get("parent_node") else None),
            parent_task_id=(str(data["parent_task_id"]) if data.get("parent_task_id") else None),
            parent_agent_id=(str(data["parent_agent_id"]) if data.get("parent_agent_id") else None),
            agent_id=(str(data["agent_id"]) if data.get("agent_id") else None),
            fencing_token=_int_value(data.get("fencing_token"), 0),
            max_seconds=_int_value(data.get("max_seconds"), 300),
            max_retries=_int_value(data.get("max_retries"), 3),
            backoff_base=_float_value(data.get("backoff_base"), 2.0),
            paper_only=data.get("paper_only") is True,
            repo=str(data.get("repo", "")),
            issue=str(data.get("issue", "")),
        )

    @staticmethod
    def _scoped_node(node: TaskNode, repo: str, issue: str) -> TaskNode:
        return TaskNode(
            node_id=node.node_id,
            task=node.task,
            prereqs=node.prereqs,
            role=node.role,
            tools=node.tools,
            model=node.model,
            fallback_model=node.fallback_model,
            parent_node=node.parent_node,
            parent_task_id=node.parent_task_id or node.parent_node,
            parent_agent_id=node.parent_agent_id,
            agent_id=node.agent_id,
            fencing_token=node.fencing_token,
            max_seconds=node.max_seconds,
            max_retries=node.max_retries,
            backoff_base=node.backoff_base,
            paper_only=node.paper_only,
            repo=node.repo or repo,
            issue=node.issue or issue,
        )

    def _reject(self, reason: DenyReason, detail: str, **caps: object) -> None:
        """Audit + raise a plan-validation failure (fail-closed)."""
        self._audit("deny", {"reason": reason.value, "detail": detail, **caps})
        raise ValueError(f"DAG rejected: {reason.value} — {detail}")

    def submit(self, graph: TaskGraph, repo: str = "", issue: str = "") -> str:
        """Validate and durably stage an immutable scheduler plan."""
        ids = [n.node_id for n in graph.nodes]
        if len(ids) != len(set(ids)):
            self._reject(DenyReason.DUPLICATE_TASK, "duplicate task node ids")
        known = set(ids)
        for node in graph.nodes:
            unknown = sorted(set(node.prereqs) - known)
            if unknown:
                self._reject(
                    DenyReason.UNKNOWN_DEPENDENCY,
                    f"task={node.node_id} has unknown prerequisites={unknown}",
                )
            parent = node.parent_task_id or node.parent_node
            if parent and parent not in known:
                self._reject(
                    DenyReason.UNKNOWN_PARENT,
                    f"task={node.node_id} references unknown parent={parent!r}",
                )
            if node.paper_only is not True:
                self._reject(
                    DenyReason.LIVE_TRADING_TOOL,
                    f"task={node.node_id} requested paper_only=False",
                )
        if graph.has_cycle():
            self._reject(DenyReason.DAG_CYCLE, f"cycle in graph {graph.name}")
        if graph.node_count() > self.budget.max_dag_nodes:
            self._reject(
                DenyReason.DAG_NODE_LIMIT,
                f"node_count={graph.node_count()} > max_dag_nodes={self.budget.max_dag_nodes}",
                budget=self.budget.max_dag_nodes,
            )
        if graph.max_depth() > self.budget.max_dag_depth:
            self._reject(
                DenyReason.DAG_DEPTH_LIMIT,
                f"max_depth={graph.max_depth()} > max_dag_depth={self.budget.max_dag_depth}",
                budget=self.budget.max_dag_depth,
            )
        if graph.max_fanout() > self.budget.max_dag_fanout:
            self._reject(
                DenyReason.DAG_FANOUT_LIMIT,
                f"max_fanout={graph.max_fanout()} > max_dag_fanout={self.budget.max_dag_fanout}",
                budget=self.budget.max_dag_fanout,
            )

        self._repo = repo or graph.repo
        self._issue = issue or graph.issue
        now = self._clock()
        scoped_nodes = tuple(
            self._scoped_node(node, self._repo, self._issue) for node in graph.nodes
        )
        for node in scoped_nodes:
            self._tasks[node.node_id] = _TaskRecord(
                node=node,
                state=LifecycleState.PLANNED,
                created_at=now,
                updated_at=now,
            )
        event = {
            "graph": graph.name,
            "repo": self._repo,
            "issue": self._issue,
            "node_count": len(scoped_nodes),
            "root": scoped_nodes[0].node_id if scoped_nodes else "",
            "nodes": [self._node_to_payload(node) for node in scoped_nodes],
        }
        self._submitted.append({"event": "submit", **event})
        audit = self._audit("submit", event)
        if audit is not None:
            seq = _int_value(audit.get("event_seq"), 0)
            for rec in self._tasks.values():
                rec.last_event_ref = seq
        return scoped_nodes[0].node_id if scoped_nodes else ""

    def submit_taskgraph_contract(self, graph: object, repo: str = "") -> str:
        """Narrow duck-typed adapter for the #2 durable TaskGraph contract.

        #2 may not yet be merged into the same branch, so this intentionally
        avoids importing it. Missing required attributes fail closed.
        """
        envelope = getattr(graph, "envelope", None)
        raw_nodes = getattr(graph, "nodes", None)
        if envelope is None or raw_nodes is None:
            raise ValueError("invalid #2 TaskGraph contract: envelope/nodes missing")
        issue = str(getattr(envelope, "issue", ""))
        paper_only = getattr(envelope, "paper_only", False)
        if paper_only is not True:
            self._reject(DenyReason.LIVE_TRADING_TOOL, "#2 graph is not PAPER-only")

        nodes: list[TaskNode] = []
        for raw in raw_nodes:
            model_policy = raw.model_policy or {}
            if not isinstance(model_policy, Mapping):
                raise ValueError("invalid #2 model_policy")
            model = str(
                model_policy.get("model")
                or model_policy.get("primary")
                or self.budget.default_model
            )
            fallback = str(
                model_policy.get("fallback_model")
                or model_policy.get("fallback")
                or self.budget.default_fallback_model
            )
            parent = raw.parent_id
            nodes.append(
                TaskNode(
                    node_id=str(raw.id),
                    task=str(raw.objective),
                    prereqs=tuple(str(x) for x in raw.dependencies),
                    role=str(raw.role),
                    tools=tuple(str(x) for x in raw.tools),
                    model=model,
                    fallback_model=fallback,
                    parent_node=(str(parent) if parent else None),
                    parent_task_id=(str(parent) if parent else None),
                    paper_only=True,
                    repo=repo,
                    issue=issue,
                )
            )
        return self.submit(
            TaskGraph(nodes=tuple(nodes), name="taskgraph-v1", repo=repo, issue=issue),
            repo=repo,
            issue=issue,
        )

    # -- dependency resolution + ready queue ------------------------------- #
    def _prereqs_satisfied(self, rec: _TaskRecord) -> bool:
        return all(
            self._tasks[p].state == LifecycleState.DONE
            for p in rec.node.prereqs
            if p in self._tasks
        )

    def _any_prereq_failed(self, rec: _TaskRecord) -> bool:
        return any(
            self._tasks[p].state
            in (LifecycleState.FAILED, LifecycleState.CANCELLED, LifecycleState.BLOCKED)
            for p in rec.node.prereqs
            if p in self._tasks
        )

    def ready(self) -> list[TaskNode]:
        """Return every dependency-ready node; concurrency is enforced at dispatch."""
        ready: list[TaskNode] = []
        for rec in self._tasks.values():
            if rec.state != LifecycleState.PLANNED:
                continue
            if rec.node.prereqs and not self._prereqs_satisfied(rec):
                if self._any_prereq_failed(rec):
                    rec.state = LifecycleState.BLOCKED
                    rec.blocker = "prerequisite_failed"
                    rec.updated_at = self._clock()
                    audit = self._audit(
                        "blocked",
                        {
                            "task_id": rec.node.node_id,
                            "reason": rec.blocker,
                            "prereqs": list(rec.node.prereqs),
                        },
                    )
                    if audit is not None:
                        rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
                continue
            ready.append(rec.node)
        ready.sort(key=lambda n: n.node_id)
        return ready

    def _scope_counts(self) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
        repo_counts: dict[str, int] = {}
        issue_counts: dict[tuple[str, str], int] = {}
        for task_id in self._claims:
            rec = self._tasks.get(task_id)
            if rec is None:
                continue
            repo = rec.node.repo or self._repo
            issue = rec.node.issue or self._issue
            repo_counts[repo] = repo_counts.get(repo, 0) + 1
            issue_key = (repo, issue)
            issue_counts[issue_key] = issue_counts.get(issue_key, 0) + 1
        return repo_counts, issue_counts

    def _can_dispatch(self, node: TaskNode) -> tuple[bool, str | None]:
        if len(self._claims) >= self.budget.max_global_concurrency:
            return False, DenyReason.GLOBAL_CONCURRENCY_LIMIT.value
        repo_counts, issue_counts = self._scope_counts()
        repo = node.repo or self._repo
        issue = node.issue or self._issue
        if repo_counts.get(repo, 0) >= self.budget.max_per_repo:
            return False, DenyReason.PER_REPO_LIMIT.value
        if issue_counts.get((repo, issue), 0) >= self.budget.max_per_issue:
            return False, DenyReason.PER_ISSUE_LIMIT.value
        return True, None

    # -- dispatch (concurrency caps + lease/fencing) ----------------------- #
    def dispatch(self, now: float | None = None) -> list[_Lease]:
        """Claim ready nodes with authoritative agent identity + fencing."""
        moment = now if now is not None else self._clock()
        leases: list[_Lease] = []
        for node in self.ready():
            allowed, reason = self._can_dispatch(node)
            rec = self._tasks[node.node_id]
            if not allowed:
                rec.blocker = reason
                rec.updated_at = moment
                # Global cap means nothing else can run in this batch.
                if reason == DenyReason.GLOBAL_CONCURRENCY_LIMIT.value:
                    break
                continue
            if rec.state != LifecycleState.PLANNED:
                continue
            rec.blocker = None
            self._fencing_counter += 1
            fence = self._fencing_counter
            agent_id = _herdr_agent_name(node.node_id, fence, node.issue or self._issue)
            parent_agent_id = node.parent_agent_id
            if node.parent_task_id and not parent_agent_id:
                parent = self._tasks.get(node.parent_task_id)
                parent_agent_id = parent.agent_id if parent is not None else None
            lease_until = moment + min(node.max_seconds, self.budget.claim_ttl_seconds)
            lease = _Lease(
                task_id=node.node_id,
                holder=agent_id,
                agent_id=agent_id,
                lease_until=lease_until,
                fencing_token=fence,
                state=LifecycleState.RUNNING,
            )
            rec.state = LifecycleState.RUNNING
            rec.agent_id = agent_id
            rec.fencing_token = fence
            rec.model_used = node.model
            rec.fallback_used = node.fallback_model
            rec.updated_at = moment
            rec.node = TaskNode(
                node_id=node.node_id,
                task=node.task,
                prereqs=node.prereqs,
                role=node.role,
                tools=node.tools,
                model=node.model,
                fallback_model=node.fallback_model,
                parent_node=node.parent_node,
                parent_task_id=node.parent_task_id,
                parent_agent_id=parent_agent_id,
                agent_id=agent_id,
                fencing_token=fence,
                max_seconds=node.max_seconds,
                max_retries=node.max_retries,
                backoff_base=node.backoff_base,
                paper_only=node.paper_only,
                repo=node.repo,
                issue=node.issue,
            )
            self._claims[node.node_id] = lease
            telemetry: dict[str, object] = {
                "event": "dispatch",
                "agent_id": agent_id,
                "parent_agent_id": parent_agent_id,
                "parent_task_id": node.parent_task_id,
                "model": node.model,
                "fallback_model": node.fallback_model,
                "leased_at": moment,
                "lease_until": lease_until,
                "fencing_token": fence,
            }
            rec.telemetry.append(telemetry)
            audit = self._audit(
                "dispatch",
                {
                    "task_id": node.node_id,
                    **telemetry,
                    "role": node.role,
                    "repo": node.repo or self._repo,
                    "issue": node.issue or self._issue,
                    "dependencies": list(node.prereqs),
                },
            )
            if audit is not None:
                rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
            leases.append(lease)
        return leases

    def _concurrency_cap(self) -> int:
        return self.budget.max_global_concurrency

    def bind_external_parent(self, task_id: str, agent_id: str, now: float | None = None) -> _Lease:
        """Bind a scheduler root to the already-running Herdr coordinator."""
        rec = self._tasks.get(task_id)
        if rec is None:
            raise ValueError(f"unknown external parent task: {task_id}")
        if rec.state != LifecycleState.PLANNED or task_id in self._claims:
            raise ValueError(f"external parent task is not claimable: {task_id}")
        if rec.node.parent_task_id or rec.node.parent_node:
            raise ValueError("only a root task may bind an external coordinator")
        if rec.node.paper_only is not True:
            raise ValueError("external coordinator binding requires PAPER-only task")
        if not _is_herdr_agent_name(agent_id):
            raise ValueError("external coordinator agent_id is not Herdr-valid")
        if any(claim.agent_id == agent_id for claim in self._claims.values()):
            raise ValueError("external coordinator agent_id is already claimed")
        if rec.node.prereqs and not self._prereqs_satisfied(rec):
            raise ValueError("external parent prerequisites are not satisfied")

        allowed, reason = self._can_dispatch(rec.node)
        if not allowed:
            rec.blocker = reason
            raise ValueError(f"external parent admission denied: {reason}")

        moment = now if now is not None else self._clock()
        self._fencing_counter += 1
        fence = self._fencing_counter
        lease_until = moment + min(rec.node.max_seconds, self.budget.claim_ttl_seconds)
        lease = _Lease(
            task_id=task_id,
            holder=agent_id,
            agent_id=agent_id,
            lease_until=lease_until,
            fencing_token=fence,
        )
        rec.state = LifecycleState.RUNNING
        rec.agent_id = agent_id
        rec.fencing_token = fence
        rec.model_used = rec.node.model
        rec.fallback_used = rec.node.fallback_model
        rec.updated_at = moment
        payload = self._node_to_payload(rec.node)
        payload["agent_id"] = agent_id
        payload["fencing_token"] = fence
        rec.node = self._node_from_payload(payload)
        self._claims[task_id] = lease
        telemetry: dict[str, object] = {
            "event": "dispatch",
            "agent_id": agent_id,
            "parent_agent_id": None,
            "parent_task_id": None,
            "model": rec.node.model,
            "fallback_model": rec.node.fallback_model,
            "leased_at": moment,
            "lease_until": lease_until,
            "fencing_token": fence,
            "external_parent": True,
        }
        rec.telemetry.append(telemetry)
        audit = self._audit(
            "dispatch",
            {
                "task_id": task_id,
                **telemetry,
                "role": rec.node.role,
                "repo": rec.node.repo or self._repo,
                "issue": rec.node.issue or self._issue,
                "dependencies": list(rec.node.prereqs),
            },
        )
        if audit is not None:
            rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
        return lease

    # -- completion (idempotent via SHA + fencing, no double commit) ------- #
    def complete(
        self,
        task_id: str,
        result: str,
        *,
        agent_id: str | None = None,
        fencing_token: int | None = None,
        model_used: str | None = None,
    ) -> bool:
        """Commit only from the currently leased worker/fence.

        Missing or stale worker identity is rejected fail-closed. Replaying an
        already committed identical result remains an idempotent no-op.
        """
        rec = self._tasks.get(task_id)
        if rec is None:
            return False
        sha = _result_sha(result)
        if rec.state == LifecycleState.DONE and rec.result_sha == sha:
            return False

        lease = self._claims.get(task_id)
        lease_expired = lease is not None and self._clock() > lease.lease_until
        if (
            lease is None
            or lease_expired
            or agent_id is None
            or fencing_token is None
            or agent_id != lease.agent_id
            or fencing_token != lease.fencing_token
        ):
            rec.telemetry.append(
                {
                    "event": "complete_denied",
                    "reason": "stale_worker_completion",
                    "agent_id": agent_id,
                    "fencing_token": fencing_token,
                }
            )
            audit = self._audit(
                "deny",
                {
                    "reason": "stale_worker_completion",
                    "detail": f"task_id={task_id} completion did not match active lease",
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "fencing_token": fencing_token,
                    "active_agent_id": lease.agent_id if lease else None,
                    "active_fencing_token": lease.fencing_token if lease else None,
                },
            )
            if audit is not None:
                rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
            return False

        moment = self._clock()
        rec.result_sha = sha
        rec.state = LifecycleState.DONE
        rec.model_used = model_used or rec.model_used
        rec.blocker = None
        rec.updated_at = moment
        rec.completed_at = moment
        rec.telemetry.append(
            {
                "event": "complete",
                "result_sha": sha,
                "model": rec.model_used,
                "agent_id": agent_id,
                "fencing_token": fencing_token,
                "completed_at": moment,
            }
        )
        self._claims.pop(task_id, None)
        audit = self._audit(
            "complete",
            {
                "task_id": task_id,
                "result_sha": sha,
                "agent_id": agent_id,
                "fencing_token": fencing_token,
                "completed_at": moment,
            },
        )
        if audit is not None:
            rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
        return True

    # -- failure / retry / backoff / blocker propagation ------------------- #
    def fail(self, task_id: str, reason: str = "worker_failed") -> bool:
        rec = self._tasks.get(task_id)
        if rec is None:
            return False
        rec.attempts += 1
        rec.updated_at = self._clock()
        self._claims.pop(task_id, None)
        if rec.attempts > rec.node.max_retries:
            rec.state = LifecycleState.FAILED
            rec.blocker = DenyReason.RETRY_EXHAUSTED.value
            audit = self._audit(
                "failed",
                {
                    "task_id": task_id,
                    "reason": DenyReason.RETRY_EXHAUSTED.value,
                    "detail": reason,
                    "attempts": rec.attempts,
                },
            )
            if audit is not None:
                rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
            self._propagate_blocker(task_id)
            return False

        rec.state = LifecycleState.PLANNED
        rec.blocker = None
        audit = self._audit(
            "retry",
            {"task_id": task_id, "attempts": rec.attempts, "reason": reason},
        )
        if audit is not None:
            rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
        return True

    def _propagate_blocker(self, task_id: str) -> None:
        for dep in self.successors(task_id):
            tgt = self._tasks.get(dep)
            if tgt is not None and tgt.state == LifecycleState.PLANNED:
                tgt.state = LifecycleState.BLOCKED
                tgt.blocker = f"failed_prereq:{task_id}"
                tgt.updated_at = self._clock()
                audit = self._audit(
                    "blocked",
                    {
                        "reason": "blocker_propagation",
                        "detail": f"blocked by terminal prereq {task_id}",
                        "task_id": dep,
                        "prereq": task_id,
                    },
                )
                if audit is not None:
                    tgt.last_event_ref = _int_value(audit.get("event_seq"), 0)

    def successors(self, task_id: str) -> list[str]:
        return sorted(r.node.node_id for r in self._tasks.values() if task_id in r.node.prereqs)

    # -- child-subtask proposal → real bounded TaskNode (#3 dynamic fanout) #
    def evaluate_child_proposal(self, proposal: SubtaskProposal) -> Decision:
        """Policy-only evaluation retained for callers that only need a decision."""
        decision = PolicyGate.evaluate(proposal)
        if isinstance(decision, AllowDecision):
            self._audit(
                "subtask_allow",
                {
                    "task": proposal.child_task,
                    "model": decision.model,
                    "fallback_model": decision.fallback_model,
                },
            )
        else:
            self._audit(
                "deny",
                {
                    "reason": decision.reason.value,
                    "detail": decision.detail,
                    "task": proposal.child_task,
                },
            )
        return decision

    def _spawn_deny(
        self, reason: DenyReason, detail: str, *, parent_task_id: str, child_task: str
    ) -> DenyDecision:
        self._audit(
            "deny",
            {
                "reason": reason.value,
                "detail": detail,
                "parent_task_id": parent_task_id,
                "task": child_task,
            },
        )
        return DenyDecision(reason=reason, detail=detail)

    def _lineage_depth(self, task_id: str) -> int:
        depth = 0
        current: str | None = task_id
        seen: set[str] = set()
        while current:
            if current in seen:
                raise ValueError(f"parent lineage cycle at {current}")
            seen.add(current)
            rec = self._tasks.get(current)
            if rec is None:
                break
            depth += 1
            current = rec.node.parent_task_id or rec.node.parent_node
        return depth

    def spawn_child(
        self,
        parent_task_id: str,
        proposal: SubtaskProposal,
        *,
        dependencies: tuple[str, ...] | None = None,
    ) -> TaskNode | DenyDecision:
        """Promote an ALLOWED child proposal into a durable scheduler TaskNode.

        Parent role/tools/agent identity come from scheduler state, never from
        caller-controlled proposal fields.
        """
        parent = self._tasks.get(parent_task_id)
        if parent is None:
            return self._spawn_deny(
                DenyReason.UNKNOWN_PARENT,
                "child spawn references an unknown parent task",
                parent_task_id=parent_task_id,
                child_task=proposal.child_task,
            )
        lease = self._claims.get(parent_task_id)
        if parent.state != LifecycleState.RUNNING or lease is None:
            return self._spawn_deny(
                DenyReason.PARENT_NOT_RUNNING,
                "child spawn requires an actively leased parent task",
                parent_task_id=parent_task_id,
                child_task=proposal.child_task,
            )

        canonical = SubtaskProposal(
            parent_role=parent.node.role,
            parent_tools=parent.node.tools,
            child_role=proposal.child_role,
            child_tools=proposal.child_tools,
            child_task=proposal.child_task,
            paper_only=proposal.paper_only and parent.node.paper_only,
            child_model=proposal.child_model,
            child_fallback_model=proposal.child_fallback_model,
            parent_task_id=parent_task_id,
            dependencies=dependencies if dependencies is not None else proposal.dependencies,
            repo=parent.node.repo or self._repo,
            issue=parent.node.issue or self._issue,
        )
        decision = PolicyGate.evaluate(canonical)
        if isinstance(decision, DenyDecision):
            return self._spawn_deny(
                decision.reason,
                decision.detail,
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )
        if not isinstance(decision, AllowDecision):
            raise TypeError("policy gate returned an unknown decision type")

        deps = tuple(dict.fromkeys(canonical.dependencies))
        unknown = sorted(set(deps) - set(self._tasks))
        if unknown:
            return self._spawn_deny(
                DenyReason.UNKNOWN_DEPENDENCY,
                f"unknown child dependencies={unknown}",
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )
        if len(self._tasks) >= self.budget.max_dag_nodes:
            return self._spawn_deny(
                DenyReason.DAG_NODE_LIMIT,
                f"node_count={len(self._tasks)} >= max_dag_nodes={self.budget.max_dag_nodes}",
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )
        if len(parent.children) >= self.budget.max_dag_fanout:
            return self._spawn_deny(
                DenyReason.DAG_FANOUT_LIMIT,
                (
                    f"parent fanout={len(parent.children)} >= "
                    f"max_dag_fanout={self.budget.max_dag_fanout}"
                ),
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )
        if self._lineage_depth(parent_task_id) + 1 > self.budget.max_dag_depth:
            return self._spawn_deny(
                DenyReason.DAG_DEPTH_LIMIT,
                f"child depth exceeds max_dag_depth={self.budget.max_dag_depth}",
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )

        identity_payload = json.dumps(
            {
                "parent_task_id": parent_task_id,
                "task": canonical.child_task,
                "role": canonical.child_role,
                "tools": list(canonical.child_tools),
                "dependencies": list(deps),
                "repo": canonical.repo,
                "issue": canonical.issue,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        child_id = (
            f"child:{parent_task_id}:{hashlib.sha256(identity_payload.encode()).hexdigest()[:12]}"
        )
        existing = self._tasks.get(child_id)
        if existing is not None:
            return existing.node

        child = TaskNode(
            node_id=child_id,
            task=canonical.child_task or f"subtask:{child_id}",
            prereqs=deps,
            role=canonical.child_role,
            tools=canonical.child_tools,
            model=decision.model or self.budget.default_model,
            fallback_model=decision.fallback_model or self.budget.default_fallback_model,
            parent_node=parent_task_id,
            parent_task_id=parent_task_id,
            parent_agent_id=parent.agent_id,
            max_seconds=min(parent.node.max_seconds, 1800),
            max_retries=parent.node.max_retries,
            backoff_base=parent.node.backoff_base,
            paper_only=True,
            repo=canonical.repo,
            issue=canonical.issue,
        )
        candidate = TaskGraph(
            nodes=tuple(rec.node for rec in self._tasks.values()) + (child,),
            name="dynamic-child-candidate",
            repo=self._repo,
            issue=self._issue,
        )
        if candidate.has_cycle():
            return self._spawn_deny(
                DenyReason.DAG_CYCLE,
                "dynamic child would introduce a DAG cycle",
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )
        if candidate.max_depth() > self.budget.max_dag_depth:
            return self._spawn_deny(
                DenyReason.DAG_DEPTH_LIMIT,
                (
                    f"dynamic child DAG depth={candidate.max_depth()} > "
                    f"max={self.budget.max_dag_depth}"
                ),
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )
        if candidate.max_fanout() > self.budget.max_dag_fanout:
            return self._spawn_deny(
                DenyReason.DAG_FANOUT_LIMIT,
                (
                    f"dynamic child DAG fanout={candidate.max_fanout()} > "
                    f"max={self.budget.max_dag_fanout}"
                ),
                parent_task_id=parent_task_id,
                child_task=canonical.child_task,
            )
        now = self._clock()
        rec = _TaskRecord(
            node=child,
            state=LifecycleState.PLANNED,
            created_at=now,
            updated_at=now,
        )
        self._tasks[child_id] = rec
        parent.children.append(child_id)
        parent.updated_at = now
        audit = self._audit(
            "subtask_spawned",
            {
                "task_id": child_id,
                "parent_task_id": parent_task_id,
                "parent_agent_id": parent.agent_id,
                "node": self._node_to_payload(child),
            },
        )
        if audit is not None:
            rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
            parent.last_event_ref = rec.last_event_ref
        return child

    # -- lost-worker reclaim (lease timeout + fencing) --------------------- #
    def reclaim(self, holder: str, now: float | None = None) -> list[str]:
        moment = now if now is not None else self._clock()
        reclaimed: list[str] = []
        for task_id, lease in list(self._claims.items()):
            if lease.holder != holder or lease.lease_until > moment:
                continue
            rec = self._tasks[task_id]
            rec.state = LifecycleState.PLANNED
            rec.blocker = None
            rec.updated_at = moment
            self._claims.pop(task_id, None)
            audit = self._audit(
                "reclaim",
                {
                    "task_id": task_id,
                    "agent_id": lease.agent_id,
                    "fencing_token": lease.fencing_token,
                    "lease_until": lease.lease_until,
                },
            )
            if audit is not None:
                rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
            reclaimed.append(task_id)
        return reclaimed

    # -- authoritative telemetry snapshot (Machine City source of truth) --- #
    def snapshot(self) -> dict[str, object]:
        """Return a deterministic, read-only scheduler/agent/DAG snapshot."""
        tasks: list[dict[str, object]] = []
        agents: list[dict[str, object]] = []
        edges: set[tuple[str, str, str]] = set()

        for task_id in sorted(self._tasks):
            rec = self._tasks[task_id]
            node = rec.node
            lease = self._claims.get(task_id)
            parent_task_id = node.parent_task_id or node.parent_node
            if parent_task_id:
                edges.add((parent_task_id, task_id, "parent"))
            for dep in node.prereqs:
                edges.add((dep, task_id, "dependency"))

            attempt = rec.attempts + (1 if rec.agent_id else 0)
            row: dict[str, object] = {
                "task_id": task_id,
                "parent_task_id": parent_task_id,
                "agent_id": rec.agent_id or None,
                "parent_agent_id": node.parent_agent_id or None,
                "state": rec.state.value,
                "dependencies": list(node.prereqs),
                "role": node.role,
                "model": rec.model_used or node.model,
                "fallback_model": rec.fallback_used or node.fallback_model,
                "attempt": attempt,
                "max_retries": node.max_retries,
                "fencing_token": rec.fencing_token,
                "blocker": rec.blocker,
                "child_ids": sorted(rec.children),
                "repo": node.repo or self._repo,
                "issue": node.issue or self._issue,
                "paper_only": node.paper_only,
                "result_sha": rec.result_sha,
                "created_at": rec.created_at,
                "updated_at": rec.updated_at,
                "completed_at": rec.completed_at,
                "event_ref": rec.last_event_ref,
            }
            if lease is not None:
                row["lease"] = {
                    "holder": lease.holder,
                    "agent_id": lease.agent_id,
                    "lease_until": lease.lease_until,
                    "fencing_token": lease.fencing_token,
                }
            tasks.append(row)
            if rec.agent_id:
                agents.append(
                    {
                        "agent_id": rec.agent_id,
                        "parent_agent_id": node.parent_agent_id or None,
                        "task_id": task_id,
                        "parent_task_id": parent_task_id,
                        "state": rec.state.value,
                        "role": node.role,
                        "model": rec.model_used or node.model,
                        "fallback_model": rec.fallback_used or node.fallback_model,
                        "repo": node.repo or self._repo,
                        "issue": node.issue or self._issue,
                        "fencing_token": rec.fencing_token,
                        "event_ref": rec.last_event_ref,
                    }
                )

        edge_rows = [
            {"from": src, "to": dst, "kind": kind}
            for src, dst, kind in sorted(edges, key=lambda item: (item[0], item[1], item[2]))
        ]
        return {
            "version": 1,
            "observed_at": self._clock(),
            "repo": self._repo,
            "issue": self._issue,
            "paper_only": True,
            "tasks": tasks,
            "agents": sorted(agents, key=lambda row: str(row["agent_id"])),
            "edges": edge_rows,
        }

    def export_snapshot(self, path: str | Path) -> dict[str, object]:
        """Atomically write the authoritative snapshot for a read-only consumer."""
        payload = self.snapshot()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        tmp.chmod(0o640)
        tmp.replace(target)
        target.chmod(0o640)
        return payload

    # -- durable cancellation (survives restart) --------------------------- #
    def cancel(self, task_id: str, reason: str) -> bool:
        rec = self._tasks.get(task_id)
        if rec is None:
            return False
        rec.state = LifecycleState.CANCELLED
        rec.blocker = reason
        rec.updated_at = self._clock()
        self._claims.pop(task_id, None)
        audit = self._audit("cancel", {"task_id": task_id, "reason": reason})
        if audit is not None:
            rec.last_event_ref = _int_value(audit.get("event_seq"), 0)
        self._propagate_blocker(task_id)
        return True

    # -- crash/restart recovery ------------------------------------------- #
    def replay(self, events: Iterable[Mapping[str, object]] | None = None) -> int:
        """Losslessly restore plan/task/lease/fence state or fail closed."""
        if events is None:
            if self.audit_log is None:
                return 0
            events = self.audit_log.replay()
        event_list = list(events)
        self._tasks.clear()
        self._claims.clear()
        self._repo = ""
        self._issue = ""
        self._fencing_counter = 0
        self._event_seq = 0
        applied = 0

        for ev in event_list:
            kind = str(ev.get("event", ""))
            seq = _int_value(ev.get("event_seq"), 0)
            self._event_seq = max(self._event_seq, seq)

            if kind == "submit":
                nodes = ev.get("nodes")
                if not isinstance(nodes, list):
                    raise ValueError("replay fail-closed: submit event missing durable nodes")
                self._repo = str(ev.get("repo", ""))
                self._issue = str(ev.get("issue", ""))
                now = _float_value(ev.get("clock"), 0.0)
                for raw in nodes:
                    if not isinstance(raw, Mapping):
                        raise ValueError("replay fail-closed: invalid node payload")
                    node = self._node_from_payload(raw)
                    self._tasks[node.node_id] = _TaskRecord(
                        node=node,
                        state=LifecycleState.PLANNED,
                        created_at=now,
                        updated_at=now,
                        last_event_ref=seq,
                    )
                applied += 1
                continue

            if kind == "subtask_spawned":
                raw = ev.get("node")
                if not isinstance(raw, Mapping):
                    raise ValueError("replay fail-closed: child event missing node payload")
                node = self._node_from_payload(raw)
                parent_task_id = str(ev.get("parent_task_id", ""))
                parent = self._tasks.get(parent_task_id)
                if parent is None:
                    raise ValueError(f"replay fail-closed: child parent missing {parent_task_id!r}")
                self._tasks[node.node_id] = _TaskRecord(
                    node=node,
                    state=LifecycleState.PLANNED,
                    created_at=_float_value(ev.get("clock"), 0.0),
                    updated_at=_float_value(ev.get("clock"), 0.0),
                    last_event_ref=seq,
                )
                if node.node_id not in parent.children:
                    parent.children.append(node.node_id)
                parent.last_event_ref = seq
                applied += 1
                continue

            task_id_obj = ev.get("task_id")
            if not isinstance(task_id_obj, str):
                # Pure policy deny/allow events may not refer to a staged task.
                if kind in {"deny", "subtask_allow"}:
                    applied += 1
                    continue
                raise ValueError(f"replay fail-closed: {kind!r} missing task_id")
            task_id = task_id_obj
            rec = self._tasks.get(task_id)
            if rec is None:
                if kind == "deny":
                    applied += 1
                    continue
                raise ValueError(
                    f"replay fail-closed: {kind!r} references unknown task {task_id!r}"
                )

            rec.last_event_ref = seq
            event_clock = _float_value(ev.get("clock"), rec.updated_at)
            rec.updated_at = event_clock
            if kind == "dispatch":
                agent_id = str(ev.get("agent_id", ""))
                fence = _int_value(ev.get("fencing_token"), 0)
                lease_until = _float_value(ev.get("lease_until"), 0.0)
                if not agent_id or fence <= 0 or lease_until <= 0:
                    raise ValueError("replay fail-closed: incomplete dispatch lease identity")
                rec.state = LifecycleState.RUNNING
                rec.agent_id = agent_id
                rec.fencing_token = fence
                rec.model_used = str(ev.get("model", rec.node.model))
                rec.fallback_used = str(ev.get("fallback_model", rec.node.fallback_model))
                node_payload = self._node_to_payload(rec.node)
                node_payload["agent_id"] = agent_id
                node_payload["fencing_token"] = fence
                node_payload["parent_agent_id"] = (
                    ev.get("parent_agent_id") or rec.node.parent_agent_id
                )
                rec.node = self._node_from_payload(node_payload)
                self._claims[task_id] = _Lease(
                    task_id=task_id,
                    holder=agent_id,
                    agent_id=agent_id,
                    lease_until=lease_until,
                    fencing_token=fence,
                )
                self._fencing_counter = max(self._fencing_counter, fence)
            elif kind == "complete":
                rec.state = LifecycleState.DONE
                rec.result_sha = str(ev.get("result_sha", "")) or None
                self._claims.pop(task_id, None)
            elif kind == "retry":
                rec.state = LifecycleState.PLANNED
                rec.attempts = _int_value(ev.get("attempts"), rec.attempts)
                rec.blocker = None
                self._claims.pop(task_id, None)
            elif kind == "failed":
                rec.state = LifecycleState.FAILED
                rec.attempts = _int_value(ev.get("attempts"), rec.attempts)
                rec.blocker = str(ev.get("reason", "worker_failed"))
                self._claims.pop(task_id, None)
            elif kind == "blocked":
                rec.state = LifecycleState.BLOCKED
                rec.blocker = str(ev.get("reason", "blocked"))
            elif kind == "reclaim":
                rec.state = LifecycleState.PLANNED
                rec.blocker = None
                self._claims.pop(task_id, None)
                self._fencing_counter = max(
                    self._fencing_counter, _int_value(ev.get("fencing_token"), 0)
                )
            elif kind == "cancel":
                rec.state = LifecycleState.CANCELLED
                rec.blocker = str(ev.get("reason", "cancelled"))
                self._claims.pop(task_id, None)
            elif kind == "deny":
                pass
            else:
                raise ValueError(f"replay fail-closed: unknown event kind {kind!r}")
            applied += 1
        return applied

    # -- helpers ---------------------------------------------------------- #
    def _audit(self, event: str, payload: Mapping[str, object]) -> dict[str, object]:
        self._event_seq += 1
        full: dict[str, object] = {
            "event": event,
            "event_seq": self._event_seq,
            "clock": self._clock(),
            **payload,
        }
        if self.audit_log is not None:
            return self.audit_log.append(full)
        return full

    def utilization(self) -> Mapping[str, float]:
        repo_counts, issue_counts = self._scope_counts()
        return {
            "agents": len(self._claims) / self.budget.max_global_concurrency,
            "repo_peak": max(repo_counts.values(), default=0) / self.budget.max_per_repo,
            "issue_peak": max(issue_counts.values(), default=0) / self.budget.max_per_issue,
            "dag_nodes": len(self._tasks),
            "dag_nodes_limit": self.budget.max_dag_nodes,
        }
