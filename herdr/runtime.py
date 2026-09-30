"""Real Herdr child-agent runtime bridge for scheduler issue #3.

The bridge is deliberately narrow: policy-governed canary work, Hermes
children only, owned panes only, and fail-closed Herdr admission.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from herdr.admission import (
    AdmissionControl,
    AgentIdentity,
    AuditLog as AdmissionAuditLog,
    DenyDecision as AdmissionDenyDecision,
    ResourceUsage,
    TaskGraphSpec,
)
from herdr.taskgraph import GRAPH_VERSION, TaskGraphEnvelope
from herdr.telemetry import TelemetryStore
from herdr.consumer_policies import policy_for_profile
from herdr.scheduler import (
    AuditLog,
    DenyDecision,
    DynamicChildScheduler,
    SchedulerBudget,
    SubtaskProposal,
    TaskGraph,
    TaskNode,
    _Lease,
)

HERDR_CONTEXT_BLOCKER = "herdr_runtime_context_required"
DEFAULT_SNAPSHOT = Path("/var/lib/agent-platform-herdr/swarm.json")
DEFAULT_TELEMETRY = Path("/var/lib/agent-platform-herdr/telemetry.jsonl")
DEFAULT_ADMISSION_AUDIT = Path("/var/lib/agent-platform-herdr/admission.jsonl")
DEFAULT_ADMISSION_REGISTRY = Path("/var/lib/agent-platform-herdr/admission-registry.json")
DEFAULT_PROFILE = "quantlab"
MAX_PROMPT_CHARS = 1200


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class HerdrRunner(Protocol):
    def run(self, args: Sequence[str], timeout_seconds: float = 30.0) -> CommandResult: ...


@dataclass
class SubprocessHerdrRunner:
    executable: str = "herdr"
    env: Mapping[str, str] | None = None

    def run(self, args: Sequence[str], timeout_seconds: float = 30.0) -> CommandResult:
        proc = subprocess.run(  # noqa: S603 - fixed executable + argument vector
            [self.executable, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=dict(self.env) if self.env is not None else None,
        )
        return CommandResult(proc.returncode, proc.stdout, proc.stderr)


class HerdrRuntimeError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _json_result(result: CommandResult, action: str) -> dict[str, object]:
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"{action} failed"
        raise HerdrRuntimeError("herdr_command_failed", detail[-1000:])
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HerdrRuntimeError("herdr_invalid_json", action) from exc
    if not isinstance(parsed, dict):
        raise HerdrRuntimeError("herdr_invalid_json", action)
    return parsed


def _pane_id(payload: Mapping[str, object]) -> str:
    result = payload.get("result")
    if not isinstance(result, Mapping):
        raise HerdrRuntimeError("herdr_invalid_response", "missing result")
    pane = result.get("pane")
    if not isinstance(pane, Mapping):
        raise HerdrRuntimeError("herdr_invalid_response", "missing pane")
    pane_id = pane.get("pane_id")
    if not isinstance(pane_id, str) or not pane_id:
        raise HerdrRuntimeError("herdr_invalid_response", "missing pane_id")
    return pane_id


def _agent_status(value: object) -> str | None:
    if isinstance(value, Mapping):
        direct = value.get("agent_status")
        if isinstance(direct, str):
            return direct
        for nested in value.values():
            found = _agent_status(nested)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _agent_status(nested)
            if found is not None:
                return found
    return None


def host_resources_allow_spawn() -> bool:
    """Conservative Linux host-pressure preflight; admission remains authoritative."""
    try:
        cpus = os.cpu_count() or 0
        load1 = os.getloadavg()[0]
        meminfo: dict[str, int] = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            value = int(raw.strip().split()[0]) * 1024
            meminfo[key] = value
        total = meminfo["MemTotal"]
        available = meminfo["MemAvailable"]
    except (OSError, ValueError, KeyError):
        return False
    if cpus <= 0 or total <= 0 or available < 0 or available > total:
        return False
    minimum_available = max(2 * 1024**3, total // 5)
    return load1 <= 1.5 * cpus and available >= minimum_available


def _read_cpu_sample() -> tuple[int, int]:
    line = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0]
    fields = [int(value) for value in line.split()[1:]]
    if len(fields) < 4:
        raise ValueError("cpu sample")
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
    return sum(fields), idle


def _cpu_utilization_fraction() -> float:
    total1, idle1 = _read_cpu_sample()
    time.sleep(0.05)
    total2, idle2 = _read_cpu_sample()
    total_delta = total2 - total1
    idle_delta = idle2 - idle1
    if total_delta <= 0 or idle_delta < 0:
        raise ValueError("cpu delta")
    return min(1.0, max(0.0, 1.0 - idle_delta / total_delta))


def scheduler_resource_usage(
    scheduler: DynamicChildScheduler,
    started_at: float,
    current_task_id: str,
) -> ResourceUsage:
    """Build fail-closed admission telemetry from durable scheduler + Linux host state."""
    snapshot = scheduler.snapshot()
    tasks = snapshot.get("tasks")
    if not isinstance(tasks, list):
        raise HerdrRuntimeError("invalid_scheduler_snapshot", "tasks missing")

    queue_depth = 0
    for row in tasks:
        if not isinstance(row, Mapping):
            raise HerdrRuntimeError("invalid_scheduler_snapshot", "task row invalid")
        state = row.get("state")
        if state in {"planned", "ready", "pending"}:
            queue_depth += 1

    try:
        cpus = os.cpu_count() or 0
        load1 = float(os.getloadavg()[0])
        meminfo: dict[str, int] = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            meminfo[key] = int(raw.strip().split()[0]) * 1024
        total = meminfo["MemTotal"]
        available = meminfo["MemAvailable"]
        swap_total = meminfo.get("SwapTotal", 0)
        swap_free = meminfo.get("SwapFree", 0)
        cpu_fraction = _cpu_utilization_fraction()
    except (OSError, ValueError, KeyError) as exc:
        raise HerdrRuntimeError("resource_telemetry_unavailable", "host telemetry unavailable") from exc

    if cpus <= 0 or total <= 0:
        raise HerdrRuntimeError("resource_telemetry_unavailable", "invalid host capacity")
    ram_fraction = min(1.0, max(0.0, 1.0 - (available / total)))
    swap_risk = 0.0 if swap_total <= 0 else min(1.0, max(0.0, 1.0 - swap_free / swap_total))
    return ResourceUsage(
        active_agents=0,
        agents_per_repo={},
        agents_per_issue={},
        cpu=cpu_fraction,
        ram=ram_fraction,
        queue_depth=queue_depth,
        elapsed_seconds=max(0.0, time.monotonic() - started_at),
        swap_risk=swap_risk,
        load1=load1,
        logical_cpus=cpus,
        total_ram_bytes=total,
        mem_available_bytes=available,
    )


@dataclass
class AdmissionRegistry:
    """Cross-runtime durable child-slot registry with lease-based crash recovery."""

    path: Path = DEFAULT_ADMISSION_REGISTRY

    def _read(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HerdrRuntimeError("admission_registry_invalid", "cannot read registry") from exc
        if not isinstance(raw, dict) or raw.get("version") != 1 or not isinstance(raw.get("entries"), list):
            raise HerdrRuntimeError("admission_registry_invalid", "invalid registry schema")
        entries: list[dict[str, object]] = []
        for item in raw["entries"]:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("agent_id"), str)
                or not isinstance(item.get("repo"), str)
                or not isinstance(item.get("issue"), str)
                or not isinstance(item.get("task_id"), str)
                or not isinstance(item.get("fencing_token"), int)
                or not isinstance(item.get("lease_until"), (int, float))
            ):
                raise HerdrRuntimeError("admission_registry_invalid", "invalid registry entry")
            entries.append(dict(item))
        return entries

    def _write(self, entries: Sequence[Mapping[str, object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                {"version": 1, "entries": list(entries)},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        tmp.chmod(0o640)
        tmp.replace(self.path)
        self.path.chmod(0o640)

    def _lock_fd(self) -> int:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(self.path.suffix + ".lock")
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o640)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd

    def reserve(
        self,
        admission: AdmissionControl,
        identity: AgentIdentity,
        spec: TaskGraphSpec,
        usage: ResourceUsage,
        child_tools: Sequence[str],
        lease: _Lease,
        *,
        now: float | None = None,
    ) -> None:
        moment = time.time() if now is None else now
        fd = self._lock_fd()
        try:
            entries = [
                entry
                for entry in self._read()
                if float(entry["lease_until"]) > moment
                and entry["agent_id"] != lease.agent_id
            ]
            registry_repo: dict[str, int] = {}
            registry_issue: dict[tuple[str, str], int] = {}
            for entry in entries:
                repo = str(entry["repo"])
                issue = str(entry["issue"])
                registry_repo[repo] = registry_repo.get(repo, 0) + 1
                key = (repo, issue)
                registry_issue[key] = registry_issue.get(key, 0) + 1

            combined = ResourceUsage(
                active_agents=max(usage.active_agents, len(entries)),
                agents_per_repo={
                    **usage.agents_per_repo,
                    identity.repo: max(
                        usage.agents_per_repo.get(identity.repo, 0),
                        registry_repo.get(identity.repo, 0),
                    ),
                },
                agents_per_issue={
                    **usage.agents_per_issue,
                    (identity.repo, identity.issue): max(
                        usage.agents_per_issue.get((identity.repo, identity.issue), 0),
                        registry_issue.get((identity.repo, identity.issue), 0),
                    ),
                },
                cpu=usage.cpu,
                ram=usage.ram,
                queue_depth=usage.queue_depth,
                elapsed_seconds=usage.elapsed_seconds,
                swap_risk=usage.swap_risk,
                load1=usage.load1,
                logical_cpus=usage.logical_cpus,
                total_ram_bytes=usage.total_ram_bytes,
                mem_available_bytes=usage.mem_available_bytes,
            )
            decision = admission.check(identity, spec, combined, child_tools)
            if isinstance(decision, AdmissionDenyDecision):
                raise HerdrRuntimeError("child_admission_denied", decision.reason.value)
            entries.append(
                {
                    "agent_id": lease.agent_id,
                    "repo": identity.repo,
                    "issue": identity.issue,
                    "task_id": lease.task_id,
                    "fencing_token": lease.fencing_token,
                    "lease_until": lease.lease_until,
                }
            )
            self._write(entries)
        finally:
            os.close(fd)

    def release(self, agent_id: str, *, now: float | None = None) -> None:
        moment = time.time() if now is None else now
        fd = self._lock_fd()
        try:
            entries = [
                entry
                for entry in self._read()
                if float(entry["lease_until"]) > moment and entry["agent_id"] != agent_id
            ]
            self._write(entries)
        finally:
            os.close(fd)


@dataclass
class _OwnedChild:
    lease: _Lease
    pane_id: str
    prompt: str


class HerdrChildRuntime:
    def __init__(
        self,
        scheduler: DynamicChildScheduler,
        runner: HerdrRunner,
        *,
        cwd: Path,
        snapshot_path: Path = DEFAULT_SNAPSHOT,
        env: Mapping[str, str] | None = None,
        host_guard: Callable[[], bool] = host_resources_allow_spawn,
        admission: AdmissionControl | None = None,
        admission_registry: AdmissionRegistry | None = None,
        resource_usage_factory: Callable[
            [DynamicChildScheduler, float, str], ResourceUsage
        ] = scheduler_resource_usage,
        snapshot_heartbeat_seconds: float = 30.0,
    ) -> None:
        self.scheduler = scheduler
        self.runner = runner
        self.cwd = cwd.resolve()
        self.snapshot_path = snapshot_path
        self.env = dict(env if env is not None else os.environ)
        self.host_guard = host_guard
        self.admission = admission or AdmissionControl(
            audit_log=AdmissionAuditLog(DEFAULT_ADMISSION_AUDIT),
            consumer_policy_hook=policy_for_profile(
                self.env.get("HERDR_PROFILE", DEFAULT_PROFILE)
            ),
        )
        self.admission_registry = admission_registry or AdmissionRegistry()
        self.resource_usage_factory = resource_usage_factory
        if snapshot_heartbeat_seconds <= 0:
            raise ValueError("snapshot_heartbeat_seconds must be positive")
        self.snapshot_heartbeat_seconds = float(snapshot_heartbeat_seconds)
        self._started_at = time.monotonic()
        self._owned_panes: set[str] = set()
        self._reserved_agents: set[str] = set()
        self._reservation_panes: dict[str, str | None] = {}
        self._skill_checked = False

    def _require_context(self) -> None:
        if self.env.get("HERDR_ENV") != "1" or not self.env.get("HERDR_PANE_ID"):
            raise HerdrRuntimeError(
                HERDR_CONTEXT_BLOCKER,
                "live child control is allowed only from a Herdr-managed parent pane",
            )

    def prepare(self) -> None:
        self._require_context()
        if not self.host_guard():
            raise HerdrRuntimeError("resource_pressure", "host-pressure gate denied child spawn")
        skill = self.runner.run(["--skill"], timeout_seconds=10.0)
        if skill.returncode != 0 or "name: herdr" not in skill.stdout:
            raise HerdrRuntimeError("herdr_skill_unavailable", "cannot verify Herdr control skill")
        self._skill_checked = True

    def _assert_prepared(self) -> None:
        self._require_context()
        if not self._skill_checked:
            raise HerdrRuntimeError("herdr_skill_required", "prepare() must run before control")

    def _admit_child(self, lease: _Lease) -> None:
        """Admit one immutable scheduler node before any child pane/process exists."""
        self._assert_prepared()
        try:
            node = self.scheduler.task_node(lease.task_id)
        except KeyError as exc:
            raise HerdrRuntimeError("unknown_child_task", lease.task_id) from exc
        parent_id = node.parent_id
        if not parent_id:
            raise HerdrRuntimeError("child_parent_required", lease.task_id)
        try:
            parent = self.scheduler.task_node(parent_id)
        except KeyError as exc:
            raise HerdrRuntimeError("unknown_child_parent", parent_id) from exc

        context = self.scheduler.task_context(lease.task_id)
        node_count, max_depth, max_fanout = self.scheduler.graph_dimensions()
        usage = self.resource_usage_factory(
            self.scheduler,
            self._started_at,
            lease.task_id,
        )
        identity = AgentIdentity(
            role=node.role,
            repo=context["repo"],
            issue=context["issue"],
            parent_role=parent.role,
            parent_tools=frozenset(parent.tools),
            paper_only=context["policy_profile"] == "quantlab-paper",
        )
        spec = TaskGraphSpec(
            node_count=node_count,
            max_depth=max_depth,
            max_fanout=max_fanout,
            root_task=parent_id,
        )
        self.admission_registry.reserve(
            self.admission,
            identity,
            spec,

            usage,
            node.tools,
            lease,
            now=self.scheduler.current_time(),
        )
        self._reserved_agents.add(lease.agent_id)
        self._reservation_panes[lease.agent_id] = None

    def _create_pane(self, index: int) -> str:
        self._assert_prepared()
        direction = "right" if index % 2 == 0 else "down"
        payload = _json_result(
            self.runner.run(
                [
                    "pane",
                    "split",
                    "--current",
                    "--direction",
                    direction,
                    "--cwd",
                    str(self.cwd),
                    "--no-focus",
                ]
            ),
            "pane split",
        )
        pane_id = _pane_id(payload)
        self._owned_panes.add(pane_id)
        return pane_id

    def _start_agent(self, lease: _Lease, pane_id: str) -> None:
        self._assert_prepared()
        result = self.runner.run(
            [
                "agent",
                "start",
                lease.agent_id,
                "--kind",
                "hermes",
                "--pane",
                pane_id,
                "--timeout",
                "60000",
                "--",
                "-p",
                DEFAULT_PROFILE,
                "chat",
                "-t",
                "bot_room",
                "--max-turns",
                "1",
                "--run-budget",
                "600",
            ],
            timeout_seconds=75.0,
        )
        _json_result(result, "agent start")

    def _prompt_and_complete(self, child: _OwnedChild) -> tuple[str, bool]:
        if len(child.prompt) > MAX_PROMPT_CHARS:
            raise HerdrRuntimeError("prompt_too_large", child.lease.task_id)
        result = self.runner.run(
            [
                "agent",
                "prompt",
                child.lease.agent_id,
                child.prompt,
                "--wait",
                "--timeout",
                str(
                    int(
                        min(
                            3600.0,
                            max(1.0, self.scheduler.budget.claim_ttl_seconds),
                        )
                        * 1000
                    )
                ),
            ],
            timeout_seconds=3605.0,
        )
        payload = _json_result(result, "agent prompt")
        status = _agent_status(payload)
        if status not in {"idle", "done"}:
            raise HerdrRuntimeError(
                "child_not_settled",
                f"{child.lease.agent_id} settled with status={status!r}",
            )
        committed = self.scheduler.complete(
            child.lease.task_id,
            f"herdr-settled:{child.lease.agent_id}:f{child.lease.fencing_token}",
            agent_id=child.lease.agent_id,
            fencing_token=child.lease.fencing_token,
        )
        return child.lease.task_id, committed

    def cleanup(self) -> None:
        failures: list[str] = []
        closed: set[str] = set()
        for pane_id in sorted(self._owned_panes, reverse=True):
            result = self.runner.run(["pane", "close", pane_id], timeout_seconds=15.0)
            if result.returncode != 0:
                failures.append(pane_id)
            else:
                closed.add(pane_id)
        self._owned_panes.clear()

        release_failures: list[str] = []
        for agent_id in sorted(self._reserved_agents):
            pane_id = self._reservation_panes.get(agent_id)
            if pane_id is not None and pane_id not in closed:
                continue
            try:
                self.admission_registry.release(
                    agent_id,
                    now=self.scheduler.current_time(),
                )
            except HerdrRuntimeError:
                release_failures.append(agent_id)
        self._reserved_agents.clear()
        self._reservation_panes.clear()

        if failures or release_failures:
            detail = ",".join(sorted(failures + release_failures))
            raise HerdrRuntimeError("child_cleanup_failed", detail)

    def run_parallel(self, leases: Sequence[_Lease], prompts: Mapping[str, str]) -> dict[str, bool]:
        self.prepare()
        if not leases:
            raise HerdrRuntimeError("no_child_leases", "scheduler produced no child work")
        if len(leases) > self.scheduler.budget.max_global_concurrency:
            raise HerdrRuntimeError("global_concurrency_limit", "lease batch exceeds budget")

        children: list[_OwnedChild] = []
        try:
            for index, lease in enumerate(leases):
                if lease.task_id not in prompts:
                    raise HerdrRuntimeError("missing_prompt", lease.task_id)
                self._admit_child(lease)
                pane_id = self._create_pane(index)
                self._reservation_panes[lease.agent_id] = pane_id
                self._start_agent(lease, pane_id)
                children.append(_OwnedChild(lease, pane_id, prompts[lease.task_id]))

            # Evidence while all real Herdr children exist and scheduler leases are active.
            self.scheduler.export_snapshot(self.snapshot_path)

            results: dict[str, bool] = {}
            with ThreadPoolExecutor(max_workers=len(children)) as executor:
                future_map = {
                    executor.submit(self._prompt_and_complete, child): child for child in children
                }
                pending = set(future_map)
                while pending:
                    completed, pending = wait(
                        pending,
                        timeout=self.snapshot_heartbeat_seconds,
                        return_when=FIRST_COMPLETED,
                    )
                    # Keep the runtime-owned snapshot fresh while real children
                    # still exist. The periodic Agent Stack materializer must
                    # never become authoritative merely because a long prompt
                    # outlives the dashboard freshness window.
                    self.scheduler.export_snapshot(self.snapshot_path)
                    for future in completed:
                        task_id, committed = future.result()
                        results[task_id] = committed
            self.scheduler.export_snapshot(self.snapshot_path)
            return results
        finally:
            self.cleanup()


def build_two_child_canary(
    *,
    parent_agent_id: str,
    audit_path: Path,
    clock: Callable[[], float],
    telemetry_store: TelemetryStore | None = None,
) -> tuple[DynamicChildScheduler, _Lease, list[_Lease], dict[str, str]]:
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
        telemetry_store=telemetry_store,
    )
    parent = TaskNode(
        id="runtime-canary-parent",
        parent_id=None,
        type="task",
        role="reader",
        objective="coordinate safe read-only child canary",
        inputs=[{"artifact_ref": "fixture"}],
        expected_outputs=[{"kind": "result"}],
        dependencies=(),
        priority=1,
        resource_class="small",
        model_policy={"model": "laguna", "fallback_model": "longcat"},
        tools=(),
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
                planner="herdr-runtime-canary@1.0",
                max_nodes=64,
                max_depth=4,
                max_fanout=6,
                policy_profile="quantlab-paper",
            ),
            nodes=(parent,),
        ),
        repo="Bbambaaamm/herdr",
        issue="3",
    )
    parent_lease = scheduler.bind_external_parent(parent.id, parent_agent_id)
    child_nodes: list[TaskNode] = []
    for label in ("a", "b"):
        child = scheduler.spawn_child(
            parent.id,
            SubtaskProposal(
                parent_role="reader",
                parent_tools=(),
                child_role="reader",
                child_tools=(),
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
        leases[0].task_id: (
            "PAPER-only canary A. Do not use tools, network, files, Git, or spawn agents. "
            "Reply exactly: CANARY-A"
        ),
        leases[1].task_id: (
            "PAPER-only canary B. Do not use tools, network, files, Git, or spawn agents. "
            "Reply exactly: CANARY-B"
        ),
    }
    return scheduler, parent_lease, leases, prompts


def run_live_two_child_canary(
    *,
    parent_agent_id: str,
    cwd: Path,
    snapshot_path: Path = DEFAULT_SNAPSHOT,
    telemetry_path: Path = DEFAULT_TELEMETRY,
) -> dict[str, object]:
    clock = __import__("time").time
    audit_path = Path.home() / ".local/state/agent-stack/herdr-swarm-canary-events.jsonl"
    telemetry_store = TelemetryStore(telemetry_path)
    scheduler, parent_lease, leases, prompts = build_two_child_canary(
        parent_agent_id=parent_agent_id,
        audit_path=audit_path,
        clock=clock,
        telemetry_store=telemetry_store,
    )
    runtime = HerdrChildRuntime(
        scheduler,
        SubprocessHerdrRunner(env=os.environ),
        cwd=cwd,
        snapshot_path=snapshot_path,
    )
    child_results = runtime.run_parallel(leases, prompts)
    scheduler.complete(
        parent_lease.task_id,
        "two-child-canary-complete",
        agent_id=parent_lease.agent_id,
        fencing_token=parent_lease.fencing_token,
    )
    final_snapshot = scheduler.export_snapshot(snapshot_path)
    return {
        "status": "completed",
        "child_results": child_results,
        "snapshot": final_snapshot,
        "telemetry": str(telemetry_path),
    }


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument("--canary", action="store_true")
    parser.add_argument("--parent-agent", default="quantlab-hermes")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--telemetry", type=Path, default=DEFAULT_TELEMETRY)
    args = parser.parse_args()
    if not args.canary:
        parser.error("--canary is required")
    try:
        result = run_live_two_child_canary(
            parent_agent_id=args.parent_agent,
            cwd=args.cwd,
            snapshot_path=args.snapshot,
            telemetry_path=args.telemetry,
        )
    except HerdrRuntimeError as exc:
        print(json.dumps({"status": "blocked", "blocker": exc.code, "detail": exc.detail}))
        return 2
    snapshot = result["snapshot"]
    if not isinstance(snapshot, Mapping):
        raise HerdrRuntimeError("invalid_snapshot", "canary did not return a mapping")
    print(
        json.dumps(
            {
                "status": "completed",
                "agents": len(snapshot["agents"]),
                "tasks": len(snapshot["tasks"]),
                "edges": len(snapshot["edges"]),
                "snapshot": str(args.snapshot),
                "telemetry": str(args.telemetry),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
