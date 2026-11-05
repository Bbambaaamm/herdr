"""Extracted original worker identity and read-only held task custody.
The historical reader returns no launch-capable parent port. Cleanup only.
"""
from pathlib import Path
import hashlib,json,os,stat
from contextlib import contextmanager
from dataclasses import dataclass
from herdr.security import InvocationIdentity, SecurityError
from herdr.host_configuration import require

def task_session_identity(task: dict) -> tuple[str, str]:
    run_token = str(task.get("run_token") or "")
    if not run_token:
        raise RuntimeError("task session requires run_token")
    routing = task.get("routing") if isinstance(task.get("routing"), dict) else {}
    coordinator = str(
        routing.get("selected_agent") or task.get("agent") or "quantlab-hermes"
    )
    digest = hashlib.sha256(
        f"{coordinator}:{task['id']}:{run_token}".encode("utf-8")
    ).hexdigest()
    # Herdr agent names are capped at 32 characters. Keep a readable,
    # coordinator-derived prefix and bind uniqueness to the full coordinator,
    # task id and run token through a 64-bit digest suffix.
    prefix = coordinator[:13].rstrip("-_") or "task"
    agent_name = f"{prefix}-t-{digest[:16]}"
    if len(agent_name) > 32:
        raise RuntimeError("task session agent name exceeds Herdr limit")
    return agent_name, f"durable-{digest[:20]}"

def claimed_root_identity(task):
    from herdr.security import InvocationIdentity
    routing = task.get("routing") if isinstance(task.get("routing"), dict) else {}
    coordinator = str(routing.get("selected_agent") or task.get("agent") or "quantlab-hermes")
    agent, marker = task_session_identity(task)
    identity = InvocationIdentity(consumer="github:"+str(task["repo"]), agent_id=agent,
        parent_agent_id=coordinator, parent_task_id="coordinator:"+coordinator,
        task_id=str(task["id"]), run_token=str(task["run_token"]), fencing_token=task["fencing_token"])
    return identity

def _read_historical_task(root, task_id, run_token):
    """Read a protected current/terminal root task without editing its state."""
    import re
    require(isinstance(task_id,str) and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}",task_id)
            and isinstance(run_token,str) and 0<len(run_token)<=128,
            "canonical parent identity invalid")
    root=Path(root)
    require(root.is_absolute() and root.resolve(strict=True)==root,"canonical task root invalid")
    info=root.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.geteuid() and not info.st_mode&0o022,
            "canonical task root untrusted")
    found=[]
    root_fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        for state in ("running","blocked","pending","done","failed"):
            try:
                directory=os.open(state,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=root_fd)
            except FileNotFoundError:
                continue
            try:
                state_info=os.fstat(directory)
                require(state_info.st_uid==os.geteuid() and not state_info.st_mode&0o022,
                        "canonical task state untrusted")
                try:
                    fd=os.open(task_id+".json",os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,dir_fd=directory)
                except FileNotFoundError:
                    continue
                try:
                    before=os.fstat(fd)
                    require(stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid()
                            and not before.st_mode&0o077 and before.st_nlink==1
                            and 0<before.st_size<=1048576,"canonical parent task untrusted")
                    raw=b""
                    while len(raw)<=1048576:
                        chunk=os.read(fd,min(65536,1048577-len(raw)))
                        if not chunk:break
                        raw+=chunk
                    after=os.fstat(fd)
                    named=os.stat(task_id+".json",dir_fd=directory,follow_symlinks=False)
                    stamp=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_mode,x.st_uid,x.st_nlink)
                    require(stamp(before)==stamp(after)==stamp(named) and len(raw)==before.st_size,
                            "canonical parent changed during read")
                    def unique(pairs):
                        result={}
                        for key,value in pairs:
                            require(key not in result,"canonical parent duplicate field")
                            result[key]=value
                        return result
                    task=json.loads(raw,object_pairs_hook=unique)
                    require(isinstance(task,dict) and task.get("id")==task_id,"canonical parent identity invalid")
                    if task.get("run_token")==run_token:
                        found.append(task)
                finally:
                    os.close(fd)
            finally:
                os.close(directory)
        require(len(found)<=1,"canonical parent attempt ambiguous")
        return found[0] if found else None
    finally:
        os.close(root_fd)


@dataclass(frozen=True)
class HeldTask:
    task: dict


def read_held_task(root, task_id, run_token):
    task = _read_historical_task(root, task_id, run_token)
    require(task is not None, "original held attempt unavailable")
    return HeldTask(task)


def read_replay_task(root, task_id, run_token):
    """Preserve legacy reader; only this consumed case gets historical data."""
    from herdr.host_configuration import read_canonical_parent
    try: return read_canonical_parent(root, task_id, run_token)
    except SecurityError as error:
        require(str(error) == "terminal_unknown_requires_operator_reconciliation" and
            task_id.endswith("03414499dd0d1986968b2393d44275d0"), "original held parent remains denied")
        held = read_held_task(root, task_id, run_token)
        identity = claimed_root_identity(held.task)
        journal = attempt_journal({"root": Path(root), "identity": identity, "recovery": True})
        row = journal.read_once("single-case-root-admit")
        require((row["task_id"], row["run_token"], row["fencing_token"]) ==
            (task_id, run_token, identity.fencing_token), "held original case admission differs")
        return held.task


def canonical_components(task_id, run_token, *, recovery=False):
    """Actual factories under configured host UID; no effect during root preflight."""
    from herdr.host_configuration import (HOST_POLICY_CONFIG, _read_configuration,
        read_canonical_parent, build_host_policy_factory)
    from herdr.work_configuration import build_root_work_factory
    from herdr.admission import AdmissionControl, AuditLog, PlanBudget
    from herdr.runtime import AdmissionRegistry, DEFAULT_ADMISSION_REGISTRY, DEFAULT_ADMISSION_AUDIT
    from herdr.consumer_policies import policy_for_profile
    raw = _read_configuration(HOST_POLICY_CONFIG)
    require(os.geteuid() == 1001 == raw["host_uid"], "canonical host UID1001 required")
    if not recovery:
        require(type(raw.get("private_launch")) is dict and
                raw["private_launch"].get("self_observation") == "authenticated-root-kernel-v1",
                "original authenticated root kernel SDK self-observation required")
    root = Path(raw["task_store_root"])
    task = (read_held_task(root, task_id, run_token).task if recovery else
            read_canonical_parent(root, task_id, run_token))
    require(task is not None and (recovery or task.get("attempt_state") in {"dispatching", "accepted"}),
            "actual original root claim required")
    identity = claimed_root_identity(task)
    factory = build_host_policy_factory(configuration_path=HOST_POLICY_CONFIG)
    work = build_root_work_factory(root, task, configuration_path=HOST_POLICY_CONFIG,
        recovery=recovery, claimed_identity=None if recovery else identity)
    require(work.budget_authority is not None, "original cumulative budget unavailable")
    control = AdmissionControl(budget=PlanBudget(), audit_log=AuditLog(DEFAULT_ADMISSION_AUDIT),
        consumer_policy_hook=policy_for_profile(task["safety_profile"]))
    registry = AdmissionRegistry(path=DEFAULT_ADMISSION_REGISTRY)
    require(raw == _read_configuration(HOST_POLICY_CONFIG), "canonical host policy changed")
    return dict(root=root, task=task, identity=identity, factory=factory, work_factory=work,
        admission_control=control, admission_registry=registry, policy=raw, recovery=recovery)


def attempt_journal(parts):
    from agent_durable_children import attempt_directory, ensure_attempt_directory
    from core_bridge import DurableLaunchJournal
    directory = attempt_directory(parts["root"], parts["identity"].task_id, parts["identity"].run_token)
    if not parts.get("recovery", True):
        ensure_attempt_directory(parts["root"], parts["identity"].task_id, parts["identity"].run_token)
    return DurableLaunchJournal(directory)


@contextmanager
def operation_guard(parts):
    """Same worker exclusion as original root launch; never creates an attempt."""
    import fcntl
    target = parts["root"] / "worker.loop.lock"
    fd = os.open(target, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 1001 and
                info.st_nlink == 1 and not info.st_mode & 0o077, "original worker lock untrusted")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def persist_task(parts, task):
    """Original worker's exact update fields and fence checks; no shadow task."""
    from agent_durable_children import _atomic_control_file
    root = parts["root"]
    current = _read_historical_task(root, task["id"], task["run_token"])
    require(current is not None, "canonical task disappeared")
    for field in ("id", "run_token", "idempotency_key", "attempts", "fencing_token"):
        require(current.get(field) == task.get(field), "canonical session identity changed")
    found = [root / state / (task["id"] + ".json") for state in
             ("running", "pending", "done", "blocked", "failed")
             if (root / state / (task["id"] + ".json")).exists()]
    require(len(found) == 1 and found[0].parent.name == "running", "startup task no longer running")
    for name in ("execution_session", "work_contract", "task_file"):
        if name in task: current[name] = task[name]
    # Existing durable atomic no-follow/control writer. No new authoritative store.
    _atomic_control_file(found[0], json.dumps(current, sort_keys=True, allow_nan=False).encode())


def root_metadata(kind, binding):
    """Historical data, not an execution grant; valid after deadline/host death."""
    from herdr.host_configuration import _read_configuration
    from offline_case.case import canonical, sha
    require(kind in {"case-unit", "closure"}, "unknown historical projection")
    base = Path("/var/lib/herdr-offline-observer-03414499dd0d1986/contexts")
    row = _read_configuration(base / (kind + ".json"))
    require(row.get("schema") == "canonical-case-root-metadata-1" and
            row.get("kind") == kind and row.get("binding") == binding and
            row.get("projection_sha256") == sha(canonical({k: v for k, v in row.items()
                                                           if k != "projection_sha256"})),
            "historical root metadata binding changed")
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    require(boot == binding["boot_id"], "historical projection boot changed")
    return row["value"]


def require_case_births(root, task):
    """Additional deny-only gate on existing retained-parent delegation path."""
    identity = claimed_root_identity(task)
    if not identity.task_id.endswith("03414499dd0d1986968b2393d44275d0"):
        return
    from .host_configuration import _read_configuration
    try:
        _read_configuration(Path("/var/lib/herdr-offline-observer-03414499dd0d1986/contexts/scope-fenced.json"))
    except FileNotFoundError:
        pass
    else:
        raise SecurityError("irreversible original root expiry fence")
    journal = attempt_journal({"root": Path(root), "identity": identity, "recovery": True})
    admitted = journal.read_once("single-case-root-admit")
    require(admitted["task_id"] == identity.task_id and admitted["run_token"] == identity.run_token,
            "original case admission unavailable")
    try: journal.read_once("case-fence-intent")
    except FileNotFoundError: return
    raise SecurityError("original case births fenced")
