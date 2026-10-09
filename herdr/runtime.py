"""Real Herdr child-agent runtime bridge for scheduler issue #3.

The bridge is deliberately narrow: policy-governed canary work, Hermes
children only, owned panes only, and fail-closed Herdr admission.
"""

from __future__ import annotations
from .launch_environment import sanitize_environment

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import time
import stat
from collections.abc import Callable, Iterable, Mapping, Sequence
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
from herdr.taskgraph import GRAPH_VERSION, TaskGraphEnvelope, LifecycleState
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
_CHILD_FILE_TOOLS = frozenset({
    "read_file", "search_files", "write_file", "patch",
})
_CHILD_RUNTIME_PERMISSIONS = frozenset({"workspace-write"})


def _child_toolsets(tools: Iterable[str], *, allow_delegation: bool = False) -> str:
    """Map admitted capabilities to an explicit Hermes model-tool allowlist."""
    selected = frozenset(tools)
    if "herdr_delegate_child" in selected and not allow_delegation:
        raise HerdrRuntimeError("child_nested_delegation_unavailable", "child-bound transport required")
    if selected - (_CHILD_FILE_TOOLS | {"herdr_delegate_child", "herdr_submit_result", "herdr_verify_work"}):
        raise HerdrRuntimeError("child_toolset_unmapped", ",".join(sorted(selected)))
    # Hermes has toolset-level (not per-tool) filtering. The file bundle is
    # constrained further by the OS workspace mount below. Empty legacy canary
    # tasks get the zero-tool bot_room bundle.
    groups = (["file"] if selected & _CHILD_FILE_TOOLS else [])
    if "herdr_delegate_child" in selected: groups.append("herdr_delegation")
    if "herdr_submit_result" in selected: groups.append("herdr_result")
    if "herdr_verify_work" in selected: groups.append("herdr_work")
    return ",".join(groups) if groups else "bot_room"


def _validate_child_permissions(permissions: Iterable[str]) -> None:
    """Fail closed unless every admitted permission has a runtime enforcement."""
    selected = frozenset(permissions)
    unknown = selected - _CHILD_RUNTIME_PERMISSIONS
    if unknown:
        raise HerdrRuntimeError("child_permission_unmapped", ",".join(sorted(unknown)))


def _bounded_json_object(path: Path, *, max_bytes: int = 1024 * 1024) -> dict[str, object]:
    """Read a small trusted control JSON without following a replacement symlink."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise HerdrRuntimeError("child_provider_preflight_failed", str(path)) from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > max_bytes:
            raise HerdrRuntimeError("child_provider_preflight_failed", str(path))
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise HerdrRuntimeError("child_provider_preflight_failed", str(path))
    finally:
        if fd >= 0:
            os.close(fd)
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HerdrRuntimeError("child_provider_preflight_failed", str(path)) from exc
    if not isinstance(value, dict):
        raise HerdrRuntimeError("child_provider_preflight_failed", str(path))
    return value


def _nous_auth_expiry_epoch(profile_config: Path) -> float | None:
    """Return the durable Nous inference-key expiry without exposing token bytes."""
    profile_dir = profile_config.parent
    candidates = [profile_dir / "auth.json"]
    if profile_dir.parent.name == "profiles":
        candidates.append(profile_dir.parent.parent / "auth.json")
    for auth_path in candidates:
        if not auth_path.is_file():
            continue
        store = _bounded_json_object(auth_path)
        providers = store.get("providers")
        state = providers.get("nous") if isinstance(providers, dict) else None
        if not isinstance(state, dict):
            continue
        raw = state.get("agent_key_expires_at") or state.get("expires_at")
        if not isinstance(raw, str) or not raw.strip():
            continue
        try:
            parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.timestamp()
        except ValueError:
            continue
    return None


def _nous_min_child_ttl_seconds(env: Mapping[str, str]) -> int:
    """Mirror Hermes' runtime-provider floor plus a handoff margin."""
    raw = str(env.get("HERMES_NOUS_MIN_KEY_TTL_SECONDS", "1800") or "1800").strip()
    try:
        configured = int(raw)
    except ValueError as exc:
        raise HerdrRuntimeError("child_provider_preflight_failed", "invalid-nous-min-ttl") from exc
    if configured < 0 or configured > 86400:
        raise HerdrRuntimeError("child_provider_preflight_failed", "invalid-nous-min-ttl")
    return max(60, configured) + 60


def _trusted_hermes_profile_preflight(profile: str, *, executable: str, env: Mapping[str, str]) -> None:
    """Refresh/validate provider auth outside the managed child sandbox.

    The child profile itself stays read-only so model-visible file tools never gain
    credential-store write authority. For Nous, require a pool key safely above
    Hermes' own runtime minimum TTL; only then can child startup avoid the
    auth-store writer/refresh path inside the read-only sandbox.
    """
    if not profile or not executable or not Path(executable).is_absolute():
        raise HerdrRuntimeError("child_provider_preflight_invalid", profile or "missing-profile")
    binary = Path(executable)
    if not binary.is_file():
        raise HerdrRuntimeError("child_provider_preflight_invalid", str(binary))
    base_env = sanitize_environment(dict(env))
    base_env.setdefault("HOME", "/home/agentops")

    def run_checked(args: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [str(binary), "-p", profile, *args], check=False, capture_output=True,
                text=True, timeout=timeout, env=base_env)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HerdrRuntimeError("child_provider_preflight_failed", profile) from exc

    provider_proc = run_checked(["config", "get", "model.provider"], timeout=15.0)
    provider = provider_proc.stdout.strip() if provider_proc.returncode == 0 else ""
    if not provider or any(ch.isspace() for ch in provider):
        raise HerdrRuntimeError("child_provider_preflight_failed", profile)

    config_proc = run_checked(["config", "path"], timeout=15.0)
    config_text = config_proc.stdout.strip() if config_proc.returncode == 0 else ""
    profile_config = Path(config_text) if config_text else Path()
    if not config_text or not profile_config.is_absolute() or profile_config.name != "config.yaml":
        raise HerdrRuntimeError("child_provider_preflight_failed", provider)

    def require_logged_in() -> None:
        status_proc = run_checked(["auth", "status", provider], timeout=30.0)
        status_lines = {line.strip().lower() for line in status_proc.stdout.splitlines()}
        if status_proc.returncode != 0 or f"{provider.lower()}: logged in" not in status_lines:
            raise HerdrRuntimeError("child_provider_preflight_failed", provider)

    require_logged_in()
    if provider.lower() != "nous":
        return

    threshold = time.time() + _nous_min_child_ttl_seconds(base_env)
    expiry = _nous_auth_expiry_epoch(profile_config)
    if expiry is None or expiry < threshold:
        refresh_proc = run_checked(["auth", "refresh", provider], timeout=45.0)
        if refresh_proc.returncode != 0:
            raise HerdrRuntimeError("child_provider_preflight_failed", provider)
        require_logged_in()
        expiry = _nous_auth_expiry_epoch(profile_config)
    if expiry is None or expiry < threshold:
        raise HerdrRuntimeError("child_provider_preflight_failed", provider)


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
            env=sanitize_environment(
                dict(self.env) if self.env is not None else dict(os.environ)),
        )
        return CommandResult(proc.returncode, proc.stdout, proc.stderr)


class HerdrRuntimeError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class PreDeliveryFailure(HerdrRuntimeError):
    """A managed child failed before runner.run(agent prompt) was invoked."""

    def __init__(self, reason: str, *, cleanup_complete: bool) -> None:
        super().__init__("child_pre_delivery_failed", reason)
        self.cleanup_complete = cleanup_complete


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
    """Cross-runtime durable child-slot registry requiring explicit release."""

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
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(
                {"version": 1, "entries": list(entries)},
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n")
            handle.flush()
            os.fchmod(handle.fileno(), 0o640)
            os.fsync(handle.fileno())
        tmp.replace(self.path)
        self.path.chmod(0o640)
        directory_fd = os.open(self.path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

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
        fd = self._lock_fd()
        try:
            existing = self._read()
            if any(entry["agent_id"] == lease.agent_id and
                   (entry["task_id"], entry["fencing_token"]) !=
                   (lease.task_id, lease.fencing_token) for entry in existing):
                raise HerdrRuntimeError("child_admission_identity_conflict", lease.agent_id)
            entries = [
                entry
                for entry in existing
                if entry["agent_id"] != lease.agent_id
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

    def release(self, agent_id: str, *, now: float | None = None,
                task_id: str | None = None, fencing_token: int | None = None) -> None:
        if (task_id is None) != (fencing_token is None):
            raise HerdrRuntimeError("admission_release_unproven", agent_id)
        fd = self._lock_fd()
        try:
            entries = self._read()
            entries = [entry for entry in entries if not (
                entry["agent_id"] == agent_id and
                (task_id is None or
                 (entry["task_id"], entry["fencing_token"]) == (task_id, fencing_token)))]
            self._write(entries)
        finally:
            os.close(fd)


@dataclass
class _OwnedChild:
    lease: _Lease
    pane_id: str
    prompt: str


from herdr.policy_launch import HostPolicyLaunchFactory, PreparedPolicyLaunch
from herdr.security import InvocationIdentity

class HerdrChildRuntime:
    def __init__(
        self,
        scheduler: DynamicChildScheduler,
        runner: HerdrRunner,
        *,
        cwd: Path,
        pinned_worktree: object | None = None,
        policy_launch_factory: HostPolicyLaunchFactory | None = None,
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
        self.cwd = Path(cwd).absolute() if pinned_worktree is not None else cwd.resolve()
        self.pinned_worktree = pinned_worktree
        self.policy_launch_factory = policy_launch_factory
        self._policy_launches: dict[str, PreparedPolicyLaunch] = {}
        self._managed_launch_panes: set[str] = set()
        self._owned_write_pins = {}
        self._policy_panes: dict[str, PreparedPolicyLaunch] = {}
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
        self._sandbox_proofs: dict[str, dict[str, object]] = {}
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
        _child_toolsets(node.tools)
        _validate_child_permissions(node.permissions)
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
            paper_only=context["policy_profile"] in {"quantlab", "quantlab-paper"},
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

    def _preflight_child_provider(self) -> None:
        """Trusted host-side credential refresh before the read-only child profile starts."""
        if not isinstance(self.runner, SubprocessHerdrRunner):
            return
        profile = self.env.get("HERDR_HERMES_PROFILE", DEFAULT_PROFILE)
        binary = self.env.get("HERDR_HERMES_BINARY", "/home/agentops/.local/bin/hermes")
        _trusted_hermes_profile_preflight(profile, executable=binary, env=self.env)

    def _create_pane(self, index: int, marker: str | None = None,
                     policy_env: Mapping[str, str] | None = None) -> str:
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
                    *(["--env", f"HERDR_DURABLE_TASK_PANE={marker}"] if marker else []),
                    *(part for key, value in (policy_env or {}).items()
                      for part in ("--env", f"{key}={value}")),
                    "--no-focus",
                ]
            ),
            "pane split",
        )
        pane_id = _pane_id(payload)
        self._owned_panes.add(pane_id)
        return pane_id

    def _get_agent_optional(self, target: str) -> Mapping[str, object] | None:
        """Return a live agent, or None only for Herdr's typed agent_not_found."""
        result = self.runner.run(["agent", "get", target], timeout_seconds=10.0)
        if result.returncode == 0:
            payload = _json_result(result, "agent get")
            agent = (payload.get("result") or {}).get("agent")
            if not isinstance(agent, Mapping):
                raise HerdrRuntimeError("child_agent_get_invalid", target)
            return agent
        channel = result.stdout if result.stdout and not result.stderr else (
            result.stderr if result.stderr and not result.stdout else "")
        try:
            payload = json.loads(channel) if channel and len(channel.encode()) <= 131072 else None
        except json.JSONDecodeError:
            payload = None
        if (
            result.returncode == 1
            and isinstance(payload, Mapping)
            and isinstance(payload.get("error"), Mapping)
            and payload["error"].get("code") == "agent_not_found"
        ):
            return None
        _json_result(result, "agent get")
        raise AssertionError("unreachable")

    def _wait_for_started_agent(self, lease: _Lease, pane_id: str,
                                *, timeout_seconds: float = 60.0) -> None:
        deadline = time.monotonic() + timeout_seconds
        renamed = False
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise HerdrRuntimeError("child_agent_not_ready", lease.agent_id)
            agent = self._get_agent_optional(pane_id)
            if agent is None:
                time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
                continue
            if agent.get("pane_id") != pane_id:
                raise HerdrRuntimeError("child_wrong_pane", pane_id)
            kind = str(agent.get("agent") or agent.get("kind") or "")
            if kind != "hermes":
                raise HerdrRuntimeError("child_agent_kind_mismatch", kind or "unknown")
            if agent.get("name") != lease.agent_id:
                if renamed:
                    raise HerdrRuntimeError("child_agent_rename_unstable", lease.agent_id)
                _json_result(
                    self.runner.run(["agent", "rename", pane_id, lease.agent_id],
                                    timeout_seconds=min(10.0, remaining)),
                    "agent rename",
                )
                renamed = True
                continue
            status = (_agent_status(agent) or str(agent.get("status") or "")).lower()
            if status == "blocked":
                raise HerdrRuntimeError("child_agent_blocked", lease.agent_id)
            if status in {"idle", "done", "unknown"}:
                return
            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))

    def _start_agent(self, lease: _Lease, pane_id: str) -> None:
        self._assert_prepared()
        node = self.scheduler.task_node(lease.task_id)
        toolsets = _child_toolsets(node.tools)
        _validate_child_permissions(node.permissions)
        hermes_args = ["-p", self.env.get("HERDR_HERMES_PROFILE", DEFAULT_PROFILE),
                       "chat", "--toolsets", toolsets, "--max-turns", "1",
                       "--run-budget", "600"]
        launch = self._policy_launches.get(lease.task_id)
        record = self.scheduler._tasks[lease.task_id]
        if (pane_id in self._managed_launch_panes
                or record.execution_pane == pane_id and record.execution_marker):
            proof = self._sandbox_proofs.get(pane_id)
            if (not isinstance(launch, PreparedPolicyLaunch)
                    or self._policy_panes.get(pane_id) is not launch
                    or not isinstance(proof, dict)
                    or proof.get("invocation_policy") is None
                    or type(proof.get("sandbox_pid")) is not int
                    or not record.execution_marker):
                raise HerdrRuntimeError("child_invocation_policy_missing", lease.task_id)
            import importlib.util
            from importlib.machinery import SourceFileLoader
            sandbox_file = Path(__file__).resolve().parents[1] / "agent-stack/bin/agent_durable_sandbox.py"
            loader = SourceFileLoader("agent_durable_sandbox_start", str(sandbox_file))
            spec = importlib.util.spec_from_loader(loader.name, loader)
            sandbox = importlib.util.module_from_spec(spec)
            loader.exec_module(sandbox)
            def invoke(args, *, timeout_seconds):
                result = self.runner.run(args, timeout_seconds=timeout_seconds)
                if args[:2] == ["pane", "run"]:
                    if not (result.returncode == 0 and result.stdout == result.stderr == ""):
                        raise HerdrRuntimeError("child_agent_input_unacknowledged", pane_id)
                    return None
                return _json_result(result, "child sandbox agent")
            try:
                payload = sandbox.start_sandbox_agent(
                    invoke, pane_id, record.execution_marker, proof["sandbox_pid"],
                    lease.agent_id, hermes_args,
                    verify_boundary=lambda: (
                        hashlib.sha256(Path(proof["policy_file"]).read_bytes()).hexdigest()
                        == proof["policy_sha256"]
                        and sandbox.verify(
                            proof["sandbox_pid"], Path(proof["real_binary"]),
                            record.execution_marker, policy=proof["policy_file"],
                            attempts=1, pinned_worktree=self.pinned_worktree,
                            child_workspace_writable=self._child_workspace_writable(lease.task_id),
                            policy_mount=launch.mount,
                            **({"private_profile_snapshot": launch.private_profile_snapshot}
                               if getattr(launch, "private_profile_snapshot", None)
                               is not None else {}))),
                    bootstrap_peer=lambda *, timeout_seconds: launch.mount.bootstrap.confirm(
                        timeout_seconds=timeout_seconds),
                    timeout_seconds=60.0)
            except RuntimeError as exc:
                raise HerdrRuntimeError("child_agent_start_unverified", str(exc)) from exc
        else:
            result = self.runner.run(
                ["agent", "start", lease.agent_id, "--kind", "hermes", "--pane", pane_id,
                 "--timeout", "60000", "--", *hermes_args], timeout_seconds=75.0)
            payload = _json_result(result, "agent start")
        started = (payload.get("result") or {}).get("agent")
        if not isinstance(started, Mapping) or started.get("name") != lease.agent_id:
            raise HerdrRuntimeError("child_agent_start_mismatch", lease.agent_id)
        if started.get("pane_id") and started["pane_id"] != pane_id:
            raise HerdrRuntimeError("child_wrong_pane", pane_id)

    def _verify_live_child(self, agent_id: str, pane_id: str, marker: str,
                           *, require_sandbox: bool = False,
                           require_owned: bool = True,
                           require_bootstrap: bool = True,
                           allow_absent_agent_before_prompt: bool = False) -> str:
        if require_owned and pane_id not in self._owned_panes:
            raise HerdrRuntimeError("child_pane_unowned", pane_id)
        result=self.runner.run(["agent","get",agent_id])
        missing=False
        if allow_absent_agent_before_prompt:
            matching=[rec for rec in self.scheduler._tasks.values()
                if (rec.agent_id,rec.execution_agent,rec.execution_pane,rec.execution_marker)==
                   (agent_id,agent_id,pane_id,marker)]
            if (not require_sandbox or require_bootstrap or len(matching)!=1
                    or matching[0].economic_delivery_attempted is not False):
                raise HerdrRuntimeError("child_cleanup_unproven",pane_id)
            try:
                channel = result.stdout if not result.stderr else result.stderr if not result.stdout else ""
                raw=json.loads(channel) if result.returncode == 1 and 0 < len(channel)<=131072 else None
            except (TypeError,ValueError):raw=None
            missing=(isinstance(raw,dict) and isinstance(raw.get("error"),dict)
                     and raw["error"].get("code")=="agent_not_found")
        if missing:
            agent=None
        else:
            payload=_json_result(result,"agent get")
            agent=(payload.get("result") or {}).get("agent")
            if (not isinstance(agent,Mapping) or agent.get("name")!=agent_id or agent.get("pane_id")!=pane_id):
                raise HerdrRuntimeError("child_wrong_pane",agent_id)
        info = _json_result(self.runner.run(["pane", "process-info", "--pane", pane_id]),
                            "pane process-info")
        process = (info.get("result") or {}).get("process_info")
        if not isinstance(process, Mapping):
            raise HerdrRuntimeError("child_marker_missing", pane_id)
        # Managed children run behind a bwrap PID/mount boundary. Prove the
        # marker on an inner process when such a namespace exists; retain the
        # legacy shell-marker path for the older read-only canary runtime.
        marker_ok = False
        try:
            import importlib.util
            from importlib.machinery import SourceFileLoader
            sandbox_file = Path(__file__).resolve().parents[1] / "agent-stack/bin/agent_durable_sandbox.py"
            loader = SourceFileLoader("agent_durable_sandbox_verify", str(sandbox_file))
            spec = importlib.util.spec_from_loader(loader.name, loader)
            sandbox = importlib.util.module_from_spec(spec)
            loader.exec_module(sandbox)
            inner = sandbox.inner_pid(dict(process), marker)
            if inner:
                marker_ok = True
            elif not require_sandbox:
                # If any pane foreground process is already in a non-host PID
                # or mount namespace, this is a managed sandbox and failure to
                # prove the exact inner marker is fatal. Only the legacy
                # unsandboxed canary may fall back to the shell marker.
                host_pid_ns = os.readlink("/proc/self/ns/pid")
                host_mnt_ns = os.readlink("/proc/self/ns/mnt")
                namespaced = False
                for row in process.get("foreground_processes") or []:
                    if not isinstance(row, Mapping):
                        continue
                    try:
                        pid = int(row.get("pid") or 0)
                        if pid > 0 and (
                            os.readlink(f"/proc/{pid}/ns/pid") != host_pid_ns
                            or os.readlink(f"/proc/{pid}/ns/mnt") != host_mnt_ns
                        ):
                            namespaced = True
                            break
                    except (OSError, TypeError, ValueError):
                        continue
                if not namespaced:
                    shell_pid = int(process.get("shell_pid") or 0)
                    environ = Path(f"/proc/{shell_pid}/environ").read_bytes().split(b"\0")
                    marker_ok = f"HERDR_DURABLE_TASK_PANE={marker}".encode() in environ
        except (OSError, ValueError, TypeError):
            marker_ok = False
        if not marker_ok:
            raise HerdrRuntimeError("child_sandbox_missing" if require_sandbox
                                    else "child_marker_missing", pane_id)
        if require_sandbox and (require_bootstrap or allow_absent_agent_before_prompt):
            matching=[rec for rec in self.scheduler._tasks.values()
                      if (rec.agent_id,rec.execution_agent,rec.execution_pane,rec.execution_marker)
                         ==(agent_id,agent_id,pane_id,marker)]
            if len(matching)!=1:
                raise HerdrRuntimeError("child_bootstrap_identity_missing",pane_id)
            rec=matching[0]
            proof=rec.execution_sandbox_attestation
            if not rec.execution_sandbox_verified or not isinstance(proof,dict):
                raise HerdrRuntimeError("child_bootstrap_proof_missing",pane_id)
            from .policy_launch import verify_retained_policy_evidence
            from .security import InvocationIdentity,SecurityError
            identity=InvocationIdentity(consumer="github:"+rec.repo,agent_id=rec.agent_id,
                parent_agent_id=rec.parent_agent_id,parent_task_id=rec.parent_task_id,
                task_id=rec.id,run_token=rec.run_token,fencing_token=rec.fencing_token)
            original={key:proof[key] for key in ("authority","task_id","run_token","sandbox_pid",
                      "fencing_token","agent_name","pane_id","marker","worktree_identity",
                      "ownership_sha256","owned_write_mounts")
                      if key in proof}
            try:
                verify_retained_policy_evidence(proof.get("invocation_policy"),identity=identity,
                    pid=proof.get("sandbox_pid"),attestation=original,require_bootstrap=require_bootstrap)
                if rec.ownership is not None:
                    from .owned_write_mounts import validate_owned_mount_evidence,verify_owned_mount_evidence
                    from .policy_launch import mount_rows
                    if (self.pinned_worktree is None or self.pinned_worktree.identity!=rec.worktree_identity
                            or original.get("ownership_sha256")!=rec.ownership.hash
                            or rec.owned_write_mounts is None):
                        raise SecurityError("retained owned mount binding missing")
                    rows=validate_owned_mount_evidence(rec.ownership,original.get("owned_write_mounts"))
                    if rows!=rec.owned_write_mounts:
                        raise SecurityError("retained owned mount evidence changed")
                    verify_owned_mount_evidence(self.pinned_worktree.logical,rows,
                        proof["sandbox_pid"],mount_rows(proof["sandbox_pid"]))
            except (SecurityError,OSError,ValueError,TypeError) as exc:
                raise HerdrRuntimeError("child_bootstrap_unverified",pane_id) from exc
        return "not-created" if missing else str(agent.get("agent_status") or agent.get("status") or "").lower()

    def _child_result_writable(self, task_id: str) -> tuple[Path, ...]:
        """Create one durable, regular result target; never expose sibling results writable."""
        result_dir = self.snapshot_path.parent / "results"
        result_dir.mkdir(parents=True, exist_ok=True)
        target = result_dir / f"{task_id}.result.json"
        flags = (os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_CLOEXEC
                 | getattr(os, "O_NOFOLLOW", 0))
        try:
            fd = os.open(target, flags, 0o600)
        except FileExistsError as exc:
            raise HerdrRuntimeError("child_result_target_exists", str(target)) from exc
        try:
            mode = os.fstat(fd).st_mode
            if not stat.S_ISREG(mode):
                raise HerdrRuntimeError("child_result_target_invalid", str(target))
            os.fchmod(fd, 0o600)
            os.fsync(fd)
        finally:
            os.close(fd)
        directory_fd = os.open(result_dir, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                               | getattr(os, "O_NOFOLLOW", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return (target,)

    def _sandbox_child_pane(self, pane_id: str, marker: str, real: str,
                            task_id: str) -> Path:
        import importlib.util
        from importlib.machinery import SourceFileLoader
        sandbox_file = Path(__file__).resolve().parents[1] / "agent-stack/bin/agent_durable_sandbox.py"
        loader = SourceFileLoader("agent_durable_sandbox_runtime", str(sandbox_file))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        sandbox = importlib.util.module_from_spec(spec)
        loader.exec_module(sandbox)
        launch = self._policy_launches.get(task_id)
        if not isinstance(launch, PreparedPolicyLaunch):
            raise HerdrRuntimeError("child_invocation_policy_missing", task_id)
        private_snapshot = getattr(launch, "private_profile_snapshot", None)
        approved_name = self.env.get("HERDR_HERMES_PROFILE", DEFAULT_PROFILE)
        if private_snapshot is not None and private_snapshot.name != approved_name:
            raise HerdrRuntimeError("child_approved_profile_identity_mismatch", task_id)
        self._policy_panes[pane_id] = launch
        policy = sandbox.frozen_policy()
        try:
            writable = self._child_result_writable(task_id)
            launch.bind_result_slot(writable[0],self.scheduler._tasks[task_id].idempotency_key)
            deadline = time.monotonic() + 10.0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise HerdrRuntimeError("child_pane_input_unready", pane_id)
                info = _json_result(self.runner.run(
                    ["pane", "process-info", "--pane", pane_id],
                    timeout_seconds=min(10.0, remaining)), "child shell process-info")
                process_info = (info.get("result") or {}).get("process_info")
                if sandbox.pane_input_ready(
                        dict(process_info) if isinstance(process_info, Mapping) else {}, marker):
                    if time.monotonic() <= deadline:
                        break
                time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
            def invoke(args, *, timeout_seconds):
                result = self.runner.run(args, timeout_seconds=timeout_seconds)
                if args[:2] == ["pane", "run"]:
                    if not (result.returncode == 0 and result.stdout == result.stderr == ""):
                        raise HerdrRuntimeError("child_sandbox_start_unverified", pane_id)
                    return None
                return _json_result(result, "child native readiness")
            try:
                sandbox.verify_pane_prompt(invoke, pane_id, marker,
                                          timeout_seconds=max(0.001, deadline - time.monotonic()))
            except RuntimeError as exc:
                raise HerdrRuntimeError("child_pane_prompt_unverified", pane_id) from exc
            # Do not carry profile path checks across the pane-readiness wait.
            # The sealed launcher revalidates the runtime targets once more
            # immediately before the bwrap exec, and verify() attests mounts.
            sandbox_args = sandbox.command(
                self.cwd,
                Path(real),
                writable=writable,
                policy=policy,
                child_workspace_writable=self._child_workspace_writable(task_id),
                pinned_worktree=self.pinned_worktree,
                policy_mount=launch.mount,
                owned_write_pins=self._owned_write_pins.get(task_id),
                admission_root=(self.scheduler.ownership_registry.root
                                if getattr(self.scheduler, "ownership_registry", None) is not None else None),
                **({"private_profile_snapshot": private_snapshot,
                    "hermes_profile": approved_name} if private_snapshot is not None else {}),
            )
            invoke(["pane", "run", pane_id, sandbox.shell_command(sandbox_args)],
                   timeout_seconds=15.0)
            deadline = time.monotonic() + 10.0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise HerdrRuntimeError("child_sandbox_unverified", pane_id)
                info = _json_result(self.runner.run(
                    ["pane", "process-info", "--pane", pane_id],
                    timeout_seconds=min(10.0, remaining)), "child sandbox process-info")
                process_info = (info.get("result") or {}).get("process_info")
                sandbox_pid = sandbox.inner_pid(
                    dict(process_info) if isinstance(process_info, Mapping) else {}, marker)
                if sandbox_pid and sandbox.verify(
                        sandbox_pid, Path(real), marker, policy=policy, attempts=1,
                        pinned_worktree=self.pinned_worktree,
                        child_workspace_writable=self._child_workspace_writable(task_id),
                        policy_mount=launch.mount, owned_write_pins=self._owned_write_pins.get(task_id),
                        **({"private_profile_snapshot": private_snapshot}
                           if private_snapshot is not None else {})):
                    if time.monotonic() <= deadline:
                        break
                time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
            record = self.scheduler._tasks[task_id]
            node = self.scheduler.task_node(task_id)
            attestation = {"authority": "herdr-runtime", "task_id": task_id,
                           "run_token": record.run_token, "sandbox_pid": sandbox_pid,
                           "fencing_token": record.fencing_token, "agent_name": record.agent_id,
                           "pane_id": pane_id, "marker": marker,
                           "worktree_identity": record.worktree_identity}
            if private_snapshot is not None:
                attestation["approved_profile"] = private_snapshot.identity
            if record.ownership is not None:
                if record.owned_write_mounts is None:
                    raise HerdrRuntimeError("child_owned_mount_proof_missing",task_id)
                attestation.update(ownership_sha256=record.ownership.hash,
                    owned_write_mounts=[dict(x) for x in record.owned_write_mounts])
            if getattr(self.scheduler,"ownership_registry",None) is not None:
                from .ownership_release import capture_namespace_lifetime
                self.scheduler.record_namespace_lifetime(task_id,capture_namespace_lifetime(sandbox_pid))
            policy_evidence = launch.seal(sandbox_pid, attestation, tools=node.tools,
                                          permissions=node.permissions)
            pins=self._owned_write_pins.pop(task_id,None)
            if pins is not None:pins.close()
            self._sandbox_proofs[pane_id] = {
                "invocation_policy": policy_evidence,
                "sandbox_pid": sandbox_pid,
                "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
                "policy_file": policy, "real_binary": real,
            }
            return policy
        except BaseException:
            policy.unlink(missing_ok=True)
            raise

    def _child_workspace_writable(self, task_id: str) -> bool:
        if self.scheduler._tasks[task_id].ownership is not None:return False
        node = self.scheduler.task_node(task_id)
        write_tools = {"write_file", "write", "patch"}
        return (node.role in {"writer", "reviewer"}
                and "workspace-write" in node.permissions
                and bool(write_tools.intersection(node.tools)))

    def cleanup_bound_child(self, task_id: str) -> None:
        """Close a previously bound durable child after exact result reconciliation."""
        rec = self.scheduler._tasks.get(task_id)
        if rec is None:
            raise HerdrRuntimeError("unknown_child_task", task_id)
        pane_id = str(rec.execution_pane or "")
        if pane_id:
            if (rec.execution_agent != rec.agent_id or not rec.execution_marker
                    or not rec.run_token or not rec.idempotency_key
                    or not rec.fencing_token):
                raise HerdrRuntimeError("child_cleanup_unproven", pane_id)
            listed = _json_result(self.runner.run(["pane", "list"]), "pane list")
            panes = (listed.get("result") or {}).get("panes")
            if not isinstance(panes, list):
                raise HerdrRuntimeError("child_cleanup_unproven", pane_id)
            present = any(isinstance(row, Mapping) and row.get("pane_id") == pane_id
                          for row in panes)
            if present:
                agent = str(rec.execution_agent or "")
                marker = str(rec.execution_marker or "")
                if not agent or not marker or agent != rec.agent_id:
                    raise HerdrRuntimeError("child_cleanup_unproven", pane_id)
                self._verify_live_child(agent, pane_id, marker, require_sandbox=True,
                                        require_owned=False,require_bootstrap=False)
            else:
                self._cleanup_policy_launch(rec.id, pane_id)
                self.admission_registry.release(
                    rec.agent_id, now=self.scheduler.current_time(),
                    task_id=rec.id, fencing_token=rec.fencing_token)
                return
            result = self.runner.run(["pane", "close", pane_id], timeout_seconds=15.0)
            if result.returncode != 0:
                listed = _json_result(self.runner.run(["pane", "list"]), "pane list")
                panes = (listed.get("result") or {}).get("panes")
                if not isinstance(panes, list):
                    raise HerdrRuntimeError("child_cleanup_unproven", pane_id)
                if any(isinstance(row, Mapping) and row.get("pane_id") == pane_id for row in panes):
                    raise HerdrRuntimeError("child_cleanup_failed", pane_id)
        self._cleanup_policy_launch(rec.id, pane_id)
        if rec.agent_id:
            self.admission_registry.release(
                rec.agent_id, now=self.scheduler.current_time(),
                task_id=rec.id, fencing_token=rec.fencing_token)

    def _cleanup_policy_launch(self, task_id, pane_id=None):
        self._managed_launch_panes.discard(pane_id)
        pins=self._owned_write_pins.pop(task_id,None)
        if pins is not None:pins.close()
        record = self.scheduler._tasks.get(task_id)
        launch = self._policy_launches.get(task_id) or self._policy_panes.get(pane_id)
        if launch is not None:
            launch.cleanup_after_pane_closed()
            self._policy_launches.pop(task_id, None)
            self._policy_panes.pop(pane_id, None)
        elif record is not None:
            factory=self.policy_launch_factory
            if factory is None:
                from .host_configuration import build_host_policy_factory
                factory=build_host_policy_factory()
            if not isinstance(factory,HostPolicyLaunchFactory):
                raise HerdrRuntimeError("child_cleanup_policy_missing",task_id)
            from .security import InvocationIdentity
            identity=InvocationIdentity(consumer="github:"+record.repo, agent_id=record.agent_id,
                parent_agent_id=record.parent_agent_id, parent_task_id=record.parent_task_id,
                task_id=record.id, run_token=record.run_token, fencing_token=record.fencing_token)
            factory.cleanup_orphan(identity)

    def _verify_created_pane_marker(self, pane_id: str, marker: str) -> None:
        info = _json_result(self.runner.run(["pane", "process-info", "--pane", pane_id]),
                            "child pane process-info")
        process = (info.get("result") or {}).get("process_info")
        try:
            pid = int(process.get("shell_pid") or 0) if isinstance(process, Mapping) else 0
            environ = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0") if pid > 0 else []
        except (OSError, TypeError, ValueError):
            environ = []
        if f"HERDR_DURABLE_TASK_PANE={marker}".encode() not in environ:
            raise HerdrRuntimeError("child_cleanup_unproven", pane_id)

    def cleanup_managed_pre_delivery(self, lease: _Lease, pane_id: str | None,
                                     marker: str, *, agent_start_attempted: bool) -> None:
        """Close only a missing or live, exactly identified created pane."""
        if not pane_id:
            raise HerdrRuntimeError("child_cleanup_unproven", lease.task_id)
        listed = _json_result(self.runner.run(["pane", "list"]), "pane list")
        panes = (listed.get("result") or {}).get("panes")
        if not isinstance(panes, list):
            raise HerdrRuntimeError("child_cleanup_unproven", pane_id)
        present = any(isinstance(row, Mapping) and row.get("pane_id") == pane_id
                      for row in panes)
        if present:
            if pane_id not in self._owned_panes or not marker:
                raise HerdrRuntimeError("child_cleanup_unproven", pane_id)
            self._verify_created_pane_marker(pane_id, marker)
            if agent_start_attempted:
                record=self.scheduler._tasks.get(lease.task_id)
                self._verify_live_child(lease.agent_id,pane_id,marker,require_sandbox=True,
                    require_bootstrap=False,allow_absent_agent_before_prompt=(
                        record is not None and record.economic_delivery_attempted is False))
            result = self.runner.run(["pane", "close", pane_id], timeout_seconds=15.0)
            if result.returncode != 0:
                listed = _json_result(self.runner.run(["pane", "list"]), "pane list")
                remaining = (listed.get("result") or {}).get("panes")
                if (not isinstance(remaining, list) or any(
                        isinstance(row, Mapping) and row.get("pane_id") == pane_id
                        for row in remaining)):
                    raise HerdrRuntimeError("child_cleanup_failed", pane_id)
        self._cleanup_policy_launch(lease.task_id, pane_id)
        self._owned_panes.discard(pane_id)
        self.admission_registry.release(
            lease.agent_id, now=self.scheduler.current_time(),
            task_id=lease.task_id, fencing_token=lease.fencing_token)
        self._reserved_agents.discard(lease.agent_id)
        self._reservation_panes.pop(lease.agent_id, None)

    def _find_pre_delivery_pane(self, rec) -> str | None:
        """Discover only the unique pane matching all durable split identity fields."""
        listed = _json_result(self.runner.run(["pane", "list"]), "pane list")
        panes = (listed.get("result") or {}).get("panes")
        if (not isinstance(panes, list) or len(panes) > 4096
                or any(not isinstance(row, Mapping) or not isinstance(row.get("pane_id"), str)
                       or not row["pane_id"] for row in panes)):
            raise HerdrRuntimeError("child_cleanup_unproven", rec.id)
        expected = {
            f"HERDR_DURABLE_TASK_PANE={rec.execution_marker}",
            f"HERDR_DURABLE_TASK_ID={rec.id}",
            f"HERDR_DURABLE_RUN_TOKEN={rec.run_token}",
            f"HERDR_DURABLE_FENCING_TOKEN={rec.fencing_token}",
            f"HERDR_DURABLE_IDEMPOTENCY_KEY={rec.idempotency_key}",
        }
        matches = []
        for row in panes:
            pane = row["pane_id"]
            info = _json_result(self.runner.run(["pane", "process-info", "--pane", pane]),
                                "pane process-info")
            process = (info.get("result") or {}).get("process_info")
            pid = int(process.get("shell_pid") or 0) if isinstance(process, Mapping) else 0
            if pid <= 0:
                raise HerdrRuntimeError("child_cleanup_unproven", pane)
            with Path(f"/proc/{pid}/environ").open("rb") as handle:
                raw = handle.read(262145)
            if len(raw) > 262144:
                raise HerdrRuntimeError("child_cleanup_unproven", pane)
            environ = {entry.decode("utf-8", errors="replace") for entry in raw.split(bytes([0]))}
            if expected <= environ:
                matches.append(pane)
        if not matches and rec.pane_split_started is False:
            # A versioned, fsynced pre-effect marker proves no split was invoked.
            # The parent bridge lock stops the original effect before recovery.
            return None
        if len(matches) != 1:
            raise HerdrRuntimeError("child_cleanup_unproven", rec.id)
        return matches[0]

    def recover_interrupted_child_start(self, task_id: str) -> None:
        rec = self.scheduler._tasks[task_id]
        if (not rec.pre_delivery_pane_creation_attempted
                or rec.pre_delivery_agent_start_attempted and rec.economic_delivery_attempted is not False
                or rec.execution_agent != rec.agent_id or rec.execution_marker != f"child-{rec.run_token}"
                or (rec.state is not LifecycleState.RUNNING and not rec.pre_delivery_failure)):
            raise HerdrRuntimeError("child_cleanup_unproven", task_id)
        if not rec.execution_pane:
            pane = self._find_pre_delivery_pane(rec)
            if pane is None:
                if rec.pane_split_started is not False:
                    raise HerdrRuntimeError("child_cleanup_unproven", task_id)
            elif not self.scheduler.bind_recovered_pre_delivery_pane(task_id, pane):
                raise HerdrRuntimeError("child_cleanup_unproven", task_id)
        if rec.state is LifecycleState.RUNNING:
            if not self.scheduler.fail_child_pre_delivery(
                    task_id, rec.run_token, rec.agent_id, rec.fencing_token, rec.idempotency_key,
                    "child start interrupted before agent invocation", cleanup_complete=False,
                    pane_creation_attempted=True):
                raise HerdrRuntimeError("child_pre_delivery_audit_denied", task_id)
        if rec.execution_pane is None and rec.pane_split_started is False:
            self._cleanup_policy_launch(task_id)
            self.admission_registry.release(rec.agent_id,now=self.scheduler.current_time(),
                task_id=rec.id,fencing_token=rec.fencing_token)
        else:
            self.cleanup_bound_pre_delivery(task_id)
        if not self.scheduler.mark_pre_delivery_cleanup_complete(task_id):
            raise HerdrRuntimeError("child_cleanup_unproven", task_id)

    def cleanup_bound_pre_delivery(self, task_id: str) -> None:
        rec = self.scheduler._tasks[task_id]
        if not rec.pre_delivery_failure or not rec.execution_pane or not all((
                rec.execution_agent, rec.execution_marker, rec.fencing_token,
                rec.run_token, rec.idempotency_key)):
            raise HerdrRuntimeError("child_cleanup_unproven", task_id)
        self._owned_panes.add(rec.execution_pane)
        lease = _Lease(task_id=task_id, agent_id=rec.agent_id, holder="reconcile",
                       fencing_token=rec.fencing_token, lease_until=0)
        self.cleanup_managed_pre_delivery(
            lease, rec.execution_pane, rec.execution_marker,
            agent_start_attempted=rec.pre_delivery_agent_start_attempted)

    def run_managed_child(self, lease: _Lease, prompt: str, *,
                          run_token: str, idempotency_key: str) -> str:
        """Deliver once through the durable scheduler; UI status is observation only."""
        real = getattr(self.runner, "executable", "")
        marker = f"child-{run_token}"
        policy_bin = Path(__file__).resolve().parents[1] / "agent-stack/policy-bin"
        policy_env = {
            "HERDR_DURABLE_TASK_ID": lease.task_id,
            "HERDR_DURABLE_RUN_TOKEN": run_token,
            "HERDR_DURABLE_FENCING_TOKEN": str(lease.fencing_token),
            "HERDR_DURABLE_IDEMPOTENCY_KEY": idempotency_key,
            "HERDR_DURABLE_MARKER": marker,
            "HERDR_REAL_BINARY": real,
            "PATH": f"{policy_bin}:{self.env.get('PATH', os.environ.get('PATH', ''))}",
        }
        delivery_started = False
        agent_start_attempted = False
        pane_creation_attempted = False
        pane_id = None
        try:
            record = self.scheduler._tasks.get(lease.task_id)
            if (record is not None and record.worktree_identity and
                    (self.pinned_worktree is None or
                     self.pinned_worktree.identity != record.worktree_identity)):
                raise HerdrRuntimeError("child_worktree_identity_mismatch", lease.task_id)
            if not real or not Path(real).is_absolute():
                raise HerdrRuntimeError("real_herdr_required", "managed child needs real binary")
            if not isinstance(self.policy_launch_factory, HostPolicyLaunchFactory):
                raise HerdrRuntimeError("child_invocation_policy_missing", lease.task_id)
            approved_profile = getattr(self.policy_launch_factory, "approved_profile", None)
            if (approved_profile is not None
                    and approved_profile.name != self.env.get("HERDR_HERMES_PROFILE", DEFAULT_PROFILE)):
                raise HerdrRuntimeError("child_approved_profile_identity_mismatch", lease.task_id)
            record = self.scheduler._tasks[lease.task_id]
            node = self.scheduler.task_node(lease.task_id)
            context = self.scheduler.task_context(lease.task_id)
            identity = InvocationIdentity(consumer="github:" + context["repo"],
                                          agent_id=lease.agent_id,
                                          parent_agent_id=str(record.parent_agent_id or ""),
                                          parent_task_id=str(record.parent_task_id or ""),
                                          task_id=lease.task_id, run_token=run_token,
                                          fencing_token=lease.fencing_token)
            if not self.scheduler.record_child_pane_intent(
                    lease.task_id, run_token, lease.agent_id, lease.fencing_token, idempotency_key, marker):
                raise HerdrRuntimeError("child_pane_intent_denied", lease.task_id)
            self.prepare()
            self._admit_child(lease)
            launch_arguments={}
            if record.ownership is not None:
                from .owned_write_mounts import OwnedWritePins
                if (self.scheduler.ownership_registry is None or
                        self.policy_launch_factory.parent_grant is None or
                        self.policy_launch_factory.parent_grant.identity!=self.scheduler.ownership_parent):
                    raise HerdrRuntimeError("child_ownership_host_binding_missing",lease.task_id)
                self.scheduler._require_current_ownership(record)
                pins=OwnedWritePins(record.ownership,self.pinned_worktree)
                self._owned_write_pins[lease.task_id]=pins
                self.scheduler.bind_owned_write_mounts(record.id,pins)
                launch_arguments["owned_write_roots"]=pins.roots
            launch = self.policy_launch_factory.prepare_child(identity=identity,workspace=self.cwd,
                tools=node.tools,permissions=node.permissions,**launch_arguments)
            if not isinstance(launch, PreparedPolicyLaunch) or launch.identity != identity:
                raise HerdrRuntimeError("child_invocation_policy_identity_mismatch", lease.task_id)
            approved_snapshot = getattr(launch, "private_profile_snapshot", None)
            if (approved_snapshot is not None
                    and approved_snapshot.name != self.env.get("HERDR_HERMES_PROFILE", DEFAULT_PROFILE)):
                raise HerdrRuntimeError("child_approved_profile_identity_mismatch", lease.task_id)
            from .child_evidence import ChildCompletionAuthority
            authority=self.scheduler.completion_authority
            if not isinstance(authority,ChildCompletionAuthority):
                raise HerdrRuntimeError("child_completion_authority_missing",lease.task_id)
            authority.prepare(record)
            authority.preflight_work(record,launch)
            self._policy_launches[lease.task_id] = launch
            policy_env.update(launch.environment())
            # Host-approved profiles completed credential preflight inside
            # HostPolicyLaunchFactory.prepare_child() BEFORE their memfd seal.
            if getattr(launch, "private_profile_snapshot", None) is None:
                self._preflight_child_provider()
            def inspect_startup_source():
                source = _json_result(self.runner.run(["pane","process-info","--current"]),
                                      "pane startup source")
                process_source = (source.get("result") or {}).get("process_info")
                if not isinstance(process_source, Mapping):
                    raise HerdrRuntimeError("child_startup_source_missing",lease.task_id)
                return process_source.get("shell_pid")
            launch.verify_spawn_source(inspect_startup_source)
            if not self.scheduler.mark_child_split_started(
                    lease.task_id,run_token,lease.agent_id,lease.fencing_token,idempotency_key):
                raise HerdrRuntimeError("child_split_intent_denied",lease.task_id)
            pane_creation_attempted = True
            pane_id = self._create_pane(0, marker, policy_env)
            self._managed_launch_panes.add(pane_id)
            self._reservation_panes[lease.agent_id] = pane_id
            if not self.scheduler.bind_pre_delivery_pane(lease.task_id, run_token,
                                                          lease.agent_id, pane_id, marker):
                raise HerdrRuntimeError("child_bind_denied", lease.task_id)
            policy = self._sandbox_child_pane(pane_id, marker, real, lease.task_id)
            proof = self._sandbox_proofs.get(pane_id)
            if (
                not isinstance(proof, Mapping)
                or not self.scheduler.attest_execution_sandbox(
                    lease.task_id,
                    run_token,
                    lease.agent_id,
                    pane_id,
                    marker,
                    sandbox_pid=int(proof.get("sandbox_pid") or 0),
                    policy_sha256=str(proof.get("policy_sha256") or ""),
                    invocation_policy=proof.get("invocation_policy"),
                )
            ):
                raise HerdrRuntimeError("child_sandbox_attestation_denied", lease.task_id)
            work_port = authority.prepare_work(record, launch)
            def publish_continuation(evidence):
                accepted = self.scheduler.attest_execution_sandbox(
                    lease.task_id,run_token,lease.agent_id,pane_id,marker,
                    sandbox_pid=int(proof["sandbox_pid"]),policy_sha256=str(proof["policy_sha256"]),
                    invocation_policy=evidence)
                if accepted and work_port is not None:
                    work_port.task["execution_session"] = authority._work_task(record, work_port.plan)["execution_session"]
                return accepted
            launch.set_continuation_sink(publish_continuation)
            launch.arm_bootstrap()
            self.scheduler.mark_pre_delivery_agent_start(lease.task_id)
            agent_start_attempted = True
            self._start_agent(lease, pane_id)
            proof["invocation_policy"]=launch.confirm_bootstrap()
            launch.verify_bootstrap()
            self._verify_live_child(lease.agent_id, pane_id, marker, require_sandbox=True)
            if not self.scheduler.bind_execution_session(lease.task_id, run_token,
                                                         lease.agent_id, pane_id, marker):
                raise HerdrRuntimeError("child_bind_denied", lease.task_id)
            if not self.scheduler.authorize_child_delivery(lease.task_id, run_token,
                                                           lease.agent_id, lease.fencing_token,
                                                           idempotency_key):
                raise HerdrRuntimeError("child_delivery_denied", lease.task_id)
            self.scheduler.execution_verifier = (
                lambda agent, pane, bound_marker: self._verify_live_child(
                    agent, pane, bound_marker, require_sandbox=True))
            if not prompt or len(prompt) > MAX_PROMPT_CHARS:
                raise HerdrRuntimeError("invalid_child_prompt", lease.task_id)
            timeout = int(min(3600.0, max(1.0, self.scheduler.budget.claim_ttl_seconds - 30.0)))
            if not self.scheduler.mark_child_delivery_started(
                    lease.task_id,run_token,lease.agent_id,lease.fencing_token,idempotency_key):
                raise HerdrRuntimeError("child_delivery_already_started",lease.task_id)
            delivery_started = True
            result = self.runner.run(["agent", "prompt", lease.agent_id, prompt,
                                      "--wait", "--timeout", str(timeout * 1000)],
                                     timeout_seconds=timeout + 5.0)
            _json_result(result, "agent prompt")
            status = self._verify_live_child(lease.agent_id, pane_id, marker,
                                             require_sandbox=True)
            if status in {"done", "idle"}:
                self.scheduler.observe_execution(lease.task_id, run_token, "settled",
                                                  "herdr_agent_get+pane_marker",
                                                  agent_name=lease.agent_id, pane_id=pane_id,
                                                  marker=marker)
                return "settled"
            state = "working" if status in {"working", "busy"} else "unavailable"
            self.scheduler.observe_execution(lease.task_id, run_token, state,
                                              "herdr_agent_get+pane_marker",
                                              agent_name=lease.agent_id, pane_id=pane_id,
                                              marker=marker)
            return state
        except Exception as exc:
            if not delivery_started:
                reason = f"{type(exc).__name__}: {exc}"[:1024]
                if not self.scheduler.fail_child_pre_delivery(
                        lease.task_id, run_token, lease.agent_id, lease.fencing_token,
                        idempotency_key, reason, cleanup_complete=False,
                        pane_creation_attempted=pane_creation_attempted):
                    raise HerdrRuntimeError("child_pre_delivery_audit_denied", lease.task_id) from exc
                cleaned = False
                try:
                    if pane_id is None:
                        if not pane_creation_attempted:
                            self._cleanup_policy_launch(lease.task_id)
                            self.admission_registry.release(
                                lease.agent_id, now=self.scheduler.current_time(),
                                task_id=lease.task_id, fencing_token=lease.fencing_token)
                        else:
                            raise HerdrRuntimeError("child_cleanup_unproven", lease.task_id)
                    else:
                        self.cleanup_managed_pre_delivery(
                            lease, pane_id, marker,
                            agent_start_attempted=agent_start_attempted)
                    cleaned = self.scheduler.mark_pre_delivery_cleanup_complete(lease.task_id)
                except Exception:
                    pass
                raise PreDeliveryFailure(reason, cleanup_complete=cleaned) from exc
            raise
        finally:
            pins=self._owned_write_pins.pop(lease.task_id,None)
            if pins is not None:pins.close()
            if "policy" in locals():
                try:
                    policy.unlink(missing_ok=True)
                except OSError:
                    pass

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
