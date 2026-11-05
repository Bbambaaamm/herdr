"""Herdr v1.7: Swarm admission control, permissions & resource budgets (#8).

Fail-closed and consumer-neutral. stdlib-only so the contract is fully offline-testable.

Invariants enforced by AdmissionControl.check():
  * Planner cannot bypass limits by emitting a larger graph (node/depth/fanout).
  * Child may never escalate tools or permissions beyond parent.
  * Resource pressure blocks a heavy spawn *before* it starts.
  * Consumer-specific safety is explicit policy input; missing policy denies.
  * Every denial is durably audited (append-only JSONL) — visible in Machine City.
  * Cancellation is durable: a cancel record is appended and replayable.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from math import isfinite
from pathlib import Path
from types import MappingProxyType

# Consumer-specific rules live in herdr.consumer_policies.

# Role-based tool allowlist. A child tool set must be a *subset* of the role
# allowlist AND a subset of the parent's tool set. Operator-role tools (push,
# deploy) require independent authorization — they are never auto-spawned.
def _reader_tools() -> frozenset[str]:
    return frozenset(
        {
            "read_file",
            "herdr_submit_result",
            "read",
            "search_files",
            "grep",
            "web_search",
            "web_extract",
            "herdr_external_knowledge",
            "git_status",
            "git_log",
        }
    )


def _writer_tools() -> frozenset[str]:
    return _reader_tools().union(
        {
            "patch",
            "write_file",
            "delete_file",
            "git_add",
            "git_commit",
            "herdr_verify_work",
        }
    )


def _operator_tools() -> frozenset[str]:
    return _writer_tools().union({"git_push", "deploy", "git_merge"})


ROLE_TOOL_ALLOWLIST: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "reader": _reader_tools(),
        "writer": _writer_tools(),
        "operator": _operator_tools(),
    }
)

# Operator role = manual/gated only. Never auto-spawned by the dynamic swarm.
AUTO_SPAWNABLE_ROLES: frozenset[str] = frozenset({"reader", "writer"})

# Explicit role hierarchy for permission-subset enforcement (child may never
# escalate above parent). Higher number = more 권한이 많음 (more 권한).
ROLE_LEVELS: Mapping[str, int] = {
    "reader": 0,
    "writer": 1,
    "operator": 2,
}


class DenyReason(StrEnum):
    """Machine-readable denial reasons (audited + visible in Machine City)."""

    # Planner / graph limits.
    PLANNER_GRAPH_TOO_LARGE = "planner_graph_too_large"
    DAG_NODE_LIMIT = "dag_node_limit"
    DAG_DEPTH_LIMIT = "dag_depth_limit"
    DAG_FANOUT_LIMIT = "dag_fanout_limit"
    INVALID_GRAPH_SPEC = "invalid_graph_spec"

    # Agent caps.
    GLOBAL_AGENT_LIMIT = "global_agent_limit"
    PER_REPO_AGENT_LIMIT = "per_repo_agent_limit"
    PER_ISSUE_AGENT_LIMIT = "per_issue_agent_limit"

    # Resource budgets / pressure.
    CPU_BUDGET = "cpu_budget"
    RAM_BUDGET = "ram_budget"
    TASK_TIME_BUDGET = "task_time_budget"
    QUEUE_BACKPRESSURE = "queue_backpressure"
    RESOURCE_PRESSURE = "resource_pressure"
    INVALID_RESOURCE_TELEMETRY = "invalid_resource_telemetry"

    # Permission / tool escalation (fail-closed).
    TOOL_ESCALATION = "tool_escalation"
    PERMISSION_ESCALATION = "permission_escalation"
    TOOL_NOT_IN_ROLE_ALLOWLIST = "tool_not_in_role_allowlist"
    NON_SPAWNABLE_ROLE = "non_spawnable_role"

    # Consumer policy hook.
    CONSUMER_POLICY = "consumer_policy"


# --------------------------------------------------------------------------- #
# Value objects.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PlanBudget:
    """Conservative, fail-closed admission ceilings for the dynamic swarm.

    These are *admission-time* caps. They complement (never replace) the
    runtime resource guards in Settings (worker_soft_rss_mb,
    market_job_min_available_mb, etc.) — see AGENTS.md runtime architecture
    contract.

    Values set here match the reviewed config approved for Herdr v1.7
    (#8); planner/child cannot change them.
    """

    max_global_agents: int = 4
    max_agents_per_repo: int = 4
    max_agents_per_issue: int = 3
    max_dag_nodes: int = 64
    max_dag_depth: int = 4
    max_dag_fanout: int = 6
    max_cpu: float = 0.80  # fraction of host CPU (0..1)
    max_ram: float = 0.85  # fraction of host RAM (0..1)
    max_task_seconds: int = 1800
    max_task_seconds_hard_cap: int = 3600
    max_queue_depth: int = 64
    role_tool_allowlist: Mapping[str, frozenset[str]] = field(
        default_factory=lambda: ROLE_TOOL_ALLOWLIST
    )

    def __post_init__(self) -> None:
        frozen = {str(role): frozenset(tools) for role, tools in self.role_tool_allowlist.items()}
        object.__setattr__(self, "role_tool_allowlist", MappingProxyType(frozen))


@dataclass(frozen=True)
class TaskGraphSpec:
    """Static description of a proposed Herdr TaskGraph/plan.

    node_count/max_depth/max_fanout are validated against PlanBudget so a
    planner cannot bypass limits by emitting a larger graph output.
    """

    node_count: int
    max_depth: int
    max_fanout: int
    root_task: str = "root"


@dataclass(frozen=True)
class AgentIdentity:
    """Who is requesting the spawn (fail-closed identity model)."""

    role: str
    repo: str
    issue: str
    parent_role: str | None = None
    parent_tools: frozenset[str] = field(default_factory=frozenset)
    paper_only: bool = True

    @property
    def parent_role_or_none(self) -> str | None:
        return self.parent_role

    @property
    def parent_tools_or_empty(self) -> frozenset[str]:
        return self.parent_tools if self.parent_tools else frozenset()


@dataclass
class ResourceUsage:
    """Current, observed swarm + host pressure (injected — offline-testable).

    A real deployment would source this from Settings runtime guards + host
    metrics; admission consumes the snapshot, never the live probe.
    """

    active_agents: int = 0
    agents_per_repo: Mapping[str, int] = field(default_factory=dict)
    agents_per_issue: Mapping[tuple[str, str], int] = field(default_factory=dict)
    cpu: float = 0.0
    ram: float = 0.0
    queue_depth: int = 0
    elapsed_seconds: float = 0.0
    swap_risk: float = 0.0  # 0..1, from host snapshot (used for heavy spawn gate)
    load1: float = 0.0  # 1-min load, used for heavy spawn gate
    logical_cpus: int = 1  # used for heavy spawn gate
    total_ram_bytes: int = 0  # used for heavy spawn gate
    mem_available_bytes: int = 0  # used for heavy spawn gate


@dataclass(frozen=True)
class DenyDecision:
    denied: bool
    reason: DenyReason
    detail: str

    def __bool__(self) -> bool:  # deny is falsy
        return False


@dataclass(frozen=True)
class AllowDecision:
    denied: bool
    agents_after: int
    budget_utilization: Mapping[str, float]

    def __bool__(self) -> bool:  # allow is truthy
        return True


Decision = AllowDecision | DenyDecision
ConsumerPolicyHook = Callable[[AgentIdentity, Sequence[str]], str | None]


# --------------------------------------------------------------------------- #
# Audit log (append-only JSONL — durable denials + durable cancellation).
# --------------------------------------------------------------------------- #


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class AuditLog:
    """Append-only JSONL log. Each record is one line (one event)."""

    def __init__(self, path: str | Path) -> None:
        self.path: Path = Path(path)

    def append(self, event: Mapping[str, object]) -> dict[str, object]:
        record: dict[str, object] = {
            "ts": _now_iso(),
            "event": event["event"],
        }
        record.update(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, sort_keys=True, default=str, allow_nan=False)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        self.path.chmod(0o640)
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
                    # Append-only log is tamper-evident: corrupt line blocks
                    # replay rather than silently dropping an audit event.
                    raise
        return events


# --------------------------------------------------------------------------- #
# Admission controller.
# --------------------------------------------------------------------------- #


@dataclass
class AdmissionControl:
    """Fail-closed swarm admission gate (#8, parent #1)."""

    budget: PlanBudget = field(default_factory=PlanBudget)
    audit_log: AuditLog | None = None
    consumer_policy_hook: ConsumerPolicyHook | None = None

    def __post_init__(self) -> None:
        if self.audit_log is None:
            raise ValueError("fail-closed admission requires an audit sink")

    # -- helpers ----------------------------------------------------------- #
    def _deny(
        self, reason: DenyReason, detail: str, audit_ctx: Mapping[str, object]
    ) -> DenyDecision:
        safe_detail = detail
        safe_ctx = dict(audit_ctx)
        decision = DenyDecision(denied=True, reason=reason, detail=safe_detail)
        audit_log = self.audit_log
        if audit_log is None:
            raise RuntimeError("admission audit sink disappeared after initialization")
        audit_log.append(
            {
                "event": "deny",
                "reason": reason.value,
                "detail": safe_detail,
                **{f"admit:{k}": v for k, v in safe_ctx.items()},
            }
        )
        return decision

    def _allow(
        self,
        agents_after: int,
        utilization: Mapping[str, float],
        audit_ctx: Mapping[str, object],
    ) -> AllowDecision:
        decision = AllowDecision(
            denied=False, agents_after=agents_after, budget_utilization=utilization
        )
        if self.audit_log is not None:
            self.audit_log.append(
                {
                    "event": "allow",
                    "agents_after": agents_after,
                    "utilization": utilization,
                    **{f"admit:{k}": v for k, v in audit_ctx.items()},
                }
            )
        return decision

    # -- public API -------------------------------------------------------- #
    def check(
        self,
        identity: AgentIdentity,
        spec: TaskGraphSpec,
        usage: ResourceUsage,
        child_tools: Sequence[str],
    ) -> Decision:
        """Admit a proposed Herdr swarm spawn.

        Ordered, fail-closed checks. The *first* failure short-circuits with a
        DenyDecision; success returns an AllowDecision. A planner cannot bypass
        limits by emitting a larger graph.
        """
        audit_ctx = {
            "role": identity.role,
            "repo": identity.repo,
            "issue": identity.issue,
            "node_count": spec.node_count,
            "max_depth": spec.max_depth,
            "max_fanout": spec.max_fanout,
            "child_tools_count": len(child_tools),
        }

        # 1. Planner/graph limits — malformed dimensions fail closed.
        if spec.node_count <= 0 or spec.max_depth <= 0 or spec.max_fanout < 0:
            return self._deny(
                DenyReason.INVALID_GRAPH_SPEC,
                ("graph dimensions must satisfy node_count>0, max_depth>0 and max_fanout>=0"),
                audit_ctx,
            )

        # Runaway gate (8x) fires before the regular limit so a truly runaway
        # graph is reported as PLANNER_GRAPH_TOO_LARGE, not just over-limit.
        if spec.node_count > self.budget.max_dag_nodes * 8:
            return self._deny(
                DenyReason.PLANNER_GRAPH_TOO_LARGE,
                f"planner graph output node_count={spec.node_count} rejected as runaway",
                {**audit_ctx, "budget_node_limit": self.budget.max_dag_nodes},
            )
        if spec.node_count > self.budget.max_dag_nodes:
            return self._deny(
                DenyReason.DAG_NODE_LIMIT,
                f"planner graph node_count={spec.node_count} > "
                f"max_dag_nodes={self.budget.max_dag_nodes}",
                {**audit_ctx, "budget_node_limit": self.budget.max_dag_nodes},
            )
        if spec.max_depth > self.budget.max_dag_depth:
            return self._deny(
                DenyReason.DAG_DEPTH_LIMIT,
                f"graph max_depth={spec.max_depth} > max_dag_depth={self.budget.max_dag_depth}",
                {**audit_ctx, "budget_depth_limit": self.budget.max_dag_depth},
            )
        if spec.max_fanout > self.budget.max_dag_fanout:
            return self._deny(
                DenyReason.DAG_FANOUT_LIMIT,
                f"graph max_fanout={spec.max_fanout} > max_danout={self.budget.max_dag_fanout}",
                {**audit_ctx, "budget_fanout_limit": self.budget.max_dag_fanout},
            )

        # 2. Agent caps (global / repo / issue).
        if usage.active_agents >= self.budget.max_global_agents:
            return self._deny(
                DenyReason.GLOBAL_AGENT_LIMIT,
                f"active_agents={usage.active_agents} >= "
                f"max_global_agents={self.budget.max_global_agents}",
                {**audit_ctx, "budget": self.budget.max_global_agents},
            )
        repo_agents = usage.agents_per_repo.get(identity.repo, 0)
        if repo_agents >= self.budget.max_agents_per_repo:
            return self._deny(
                DenyReason.PER_REPO_AGENT_LIMIT,
                f"repo agents={repo_agents} >= per_repo limit={self.budget.max_agents_per_repo}",
                {**audit_ctx, "budget": self.budget.max_agents_per_repo},
            )
        issue_key = (identity.repo, identity.issue)
        issue_agents = usage.agents_per_issue.get(issue_key, 0)
        if issue_agents >= self.budget.max_agents_per_issue:
            return self._deny(
                DenyReason.PER_ISSUE_AGENT_LIMIT,
                f"issue agents={issue_agents} >= "
                f"per_issue limit={self.budget.max_agents_per_issue}",
                {**audit_ctx, "budget": self.budget.max_agents_per_issue},
            )

        # 3. Resource telemetry is untrusted input: malformed/non-finite
        #    snapshots fail closed before any arithmetic or admission decision.
        finite_values = (
            usage.cpu,
            usage.ram,
            usage.swap_risk,
            usage.load1,
            usage.elapsed_seconds,
        )
        invalid_counts = (
            usage.active_agents < 0
            or usage.queue_depth < 0
            or any(value < 0 for value in usage.agents_per_repo.values())
            or any(value < 0 for value in usage.agents_per_issue.values())
        )
        invalid_host = (
            usage.logical_cpus <= 0
            or usage.total_ram_bytes <= 0
            or usage.mem_available_bytes < 0
            or usage.mem_available_bytes > usage.total_ram_bytes
        )
        invalid_floats = (
            not all(isfinite(float(value)) for value in finite_values)
            or not 0.0 <= usage.cpu <= 1.0
            or not 0.0 <= usage.ram <= 1.0
            or not 0.0 <= usage.swap_risk <= 1.0
            or usage.load1 < 0.0
            or usage.elapsed_seconds < 0.0
        )
        if invalid_host:
            return self._deny(
                DenyReason.RESOURCE_PRESSURE,
                "required host resource telemetry is missing or inconsistent",
                audit_ctx,
            )
        if invalid_counts or invalid_floats:
            return self._deny(
                DenyReason.INVALID_RESOURCE_TELEMETRY,
                "resource telemetry is non-finite, out of range, or negative",
                audit_ctx,
            )

        # Host-level pressure (config-backed, auditable). Fail-closed:
        # deny when load average exceeds 1.5x the logical CPU count, OR
        # free memory is below the safe threshold (2 GiB or 20% of RAM).
        if usage.load1 > 1.5 * usage.logical_cpus:
            return self._deny(
                DenyReason.RESOURCE_PRESSURE,
                f"load1={usage.load1:.2f} > 1.5 * logical_cpus={usage.logical_cpus}",
                {**audit_ctx, "load1": usage.load1, "logical_cpus": usage.logical_cpus},
            )
        mem_threshold = max(2 * 1024**3, usage.total_ram_bytes // 5)  # 2 GiB or 20% RAM
        if usage.mem_available_bytes < mem_threshold > 0:
            return self._deny(
                DenyReason.RESOURCE_PRESSURE,
                f"mem_available={usage.mem_available_bytes} B < threshold={mem_threshold} B "
                f"(max(2 GiB, 20% of {usage.total_ram_bytes} B))",
                {
                    **audit_ctx,
                    "mem_available_bytes": usage.mem_available_bytes,
                    "mem_threshold_bytes": mem_threshold,
                },
            )
        #    3b. Swarm-level CPU/RAM fraction + queue depth + task time.
        if usage.cpu >= self.budget.max_cpu:
            return self._deny(
                DenyReason.CPU_BUDGET,
                f"cpu={usage.cpu:.2f} >= max_cpu={self.budget.max_cpu:.2f}",
                {**audit_ctx, "budget": self.budget.max_cpu},
            )
        if usage.ram >= self.budget.max_ram:
            return self._deny(
                DenyReason.RAM_BUDGET,
                f"ram={usage.ram:.2f} >= max_ram={self.budget.max_ram:.2f}",
                {**audit_ctx, "budget": self.budget.max_ram},
            )
        if usage.queue_depth >= self.budget.max_queue_depth:
            return self._deny(
                DenyReason.QUEUE_BACKPRESSURE,
                f"queue_depth={usage.queue_depth} >= limit={self.budget.max_queue_depth}",
                {**audit_ctx, "budget": self.budget.max_queue_depth},
            )
        if usage.elapsed_seconds >= self.budget.max_task_seconds:
            return self._deny(
                DenyReason.TASK_TIME_BUDGET,
                f"elapsed={usage.elapsed_seconds:.0f}s >= "
                f"default_limit={self.budget.max_task_seconds}s",
                {**audit_ctx, "budget": self.budget.max_task_seconds},
            )
        if usage.elapsed_seconds >= self.budget.max_task_seconds_hard_cap:
            return self._deny(
                DenyReason.TASK_TIME_BUDGET,
                f"elapsed={usage.elapsed_seconds:.0f}s >= "
                f"hard_cap={self.budget.max_task_seconds_hard_cap}s",
                {**audit_ctx, "budget": self.budget.max_task_seconds_hard_cap},
            )

        # 4. Role must be auto-spawnable.
        if identity.role not in AUTO_SPAWNABLE_ROLES:
            return self._deny(
                DenyReason.NON_SPAWNABLE_ROLE,
                f"role={identity.role!r} is not auto-spawnable "
                f"(allowed: {sorted(AUTO_SPAWNABLE_ROLES)})",
                {**audit_ctx},
            )

        # 5. Consumer-specific policy is mandatory and may only tighten admission.
        #    The hook receives sanitized identity + requested tool names and returns
        #    a bounded reason code, or None to continue with platform checks.
        if self.consumer_policy_hook is None:
            return self._deny(
                DenyReason.CONSUMER_POLICY,
                "explicit consumer policy is required",
                {**audit_ctx, "consumer_reason": "consumer_policy_required"},
            )
        consumer_reason = self.consumer_policy_hook(identity, tuple(child_tools))
        if consumer_reason is not None:
            safe_reason = (
                consumer_reason
                if isinstance(consumer_reason, str)
                and 0 < len(consumer_reason) <= 64
                and all(
                    ch.isascii() and (ch.isalnum() or ch in "-_:/")
                    for ch in consumer_reason
                )
                else "invalid_consumer_policy_reason"
            )
            return self._deny(
                DenyReason.CONSUMER_POLICY,
                "consumer-specific policy denied dynamic child spawn",
                {**audit_ctx, "consumer_reason": safe_reason},
            )

        # 6. Tool allowlist — fail-closed on any unknown / out-of-role tool.
        role_tools = self.budget.role_tool_allowlist.get(identity.role, frozenset())
        child_set = frozenset(child_tools)
        unknown_to_role = child_set - role_tools
        if unknown_to_role:
            return self._deny(
                DenyReason.TOOL_NOT_IN_ROLE_ALLOWLIST,
                f"child tools not in role {identity.role!r} allowlist: {sorted(unknown_to_role)}",
                {**audit_ctx, "unknown_tools": sorted(unknown_to_role)},
            )

        # 7. Child may never escalate tools or permissions beyond parent.
        parent_tools = identity.parent_tools_or_empty
        parent_role = identity.parent_role_or_none
        if parent_role is not None:
            escalations = child_set - parent_tools
            if escalations:
                return self._deny(
                    DenyReason.TOOL_ESCALATION,
                    f"child escalated tools beyond parent: {sorted(escalations)}",
                    {**audit_ctx, "parent_tools_count": len(parent_tools)},
                )
        if parent_role is not None and ROLE_LEVELS.get(identity.role, -1) > ROLE_LEVELS.get(
            parent_role, -1
        ):
            return self._deny(
                DenyReason.PERMISSION_ESCALATION,
                f"child role={identity.role!r} (level {ROLE_LEVELS.get(identity.role, -1)}) > "
                f"parent role {parent_role!r} (level {ROLE_LEVELS.get(parent_role, -1)}); "
                f"child may not escalate permissions",
                {**audit_ctx, "parent_role": parent_role},
            )

        utilization = {
            "agents": usage.active_agents / self.budget.max_global_agents,
            "cpu": usage.cpu,
            "ram": usage.ram,
            "queue": usage.queue_depth / self.budget.max_queue_depth,
            "elapsed_fraction": usage.elapsed_seconds / self.budget.max_task_seconds,
        }
        return self._allow(
            agents_after=usage.active_agents + 1,
            utilization=utilization,
            audit_ctx=audit_ctx,
        )

    # -- durable cancellation --------------------------------------------- #
    def cancel(self, task_id: str, reason: str) -> dict[str, object]:
        """Durably record a cancellation (survives restart)."""
        record: dict[str, object] = {
            "event": "cancel",
            "task_id": task_id,
            "reason": reason,
        }
        if self.audit_log is not None:
            return self.audit_log.append(record)
        return record
