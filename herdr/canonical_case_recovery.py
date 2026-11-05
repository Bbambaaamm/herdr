"""Nonsemantic terminal cleanup of the one actually delivered case child.

Uses original scheduler events and HostOwnershipRelease. No success/result,
parent dependency, new grant, retry, counter reset or acceptance is produced.
"""
from herdr.security import InvocationIdentity
from herdr.evidence import canonical, digest
from herdr.scheduler import SchedulerError


def validate_retirement(scheduler, event, *, inspect_root=True):
    from herdr.child_evidence import child_identity
    from herdr.ownership_release import required_namespace_kind, validate_recorded_namespace_lifetime
    keys = {"event", "identity", "idempotency_key", "binding", "closure_sha256", "reason"}
    if not (type(event) is dict and set(event) == keys and event["event"] == "case_execution_retired"
            and event["reason"] == "offline-case-fenced-and-observed-empty"):
        raise SchedulerError("closed case retirement event required")
    identity = InvocationIdentity.from_dict(event["identity"])
    rec = scheduler.record_for(identity.task_id)
    if required_namespace_kind(scheduler, rec) != "native":
        raise SchedulerError("native case retirement requires admitted child")
    validate_recorded_namespace_lifetime(scheduler, rec, rec.namespace_lifetime)
    if not (child_identity(rec) == identity and rec.idempotency_key == event["idempotency_key"]
            and rec.delegation_key and rec.execution_sandbox_verified and rec.namespace_lifetime
            and rec.economic_delivery_attempted is True and rec.result_status is None
            and rec.result_artifact_sha256 is None):
        raise SchedulerError("canonical delivered child retirement binding changed")
    if inspect_root:
        root = scheduler.ownership_registry.root if scheduler.ownership_registry is not None else None
        if root is None: raise SchedulerError("original ownership registry required")
        parent = scheduler.ownership_parent
        require_root_release(root, parent, rec, event)
    return rec


def retire_fenced_execution(scheduler, task_id, binding):
    from herdr.child_evidence import child_identity
    from herdr.canonical_case_claim import root_metadata
    rec = scheduler.record_for(task_id)
    if rec.attempt_state == "terminal" and rec.cleanup_complete: return
    closure = root_metadata("closure", binding)
    event = {"event": "case_execution_retired", "identity": child_identity(rec).to_json(),
        "idempotency_key": rec.idempotency_key, "binding": binding,
        "closure_sha256": digest(closure), "reason": "offline-case-fenced-and-observed-empty"}
    validate_retirement(scheduler, event)
    scheduler.audit_log.append(event)
    scheduler.audit_log.flush()
    apply_retirement(scheduler, event)


def apply_retirement(scheduler, event):
    from herdr.taskgraph import LifecycleState
    # Replay revalidates canonical fields only. BOTH generic original ownership
    # release and admission release have deny-only hooks below which re-read the
    # immutable root receipt and actual task-scoped budget stops before release.
    # Static replay must not require a live original host or expired launch grant.
    rec = validate_retirement(scheduler, event, inspect_root=False)
    rec.state = LifecycleState.CANCELLED
    rec.attempt_state = "terminal"
    rec.cleanup_complete = True
    rec.lease = None
    rec.blocker = event["reason"]
    scheduler._claims.pop(rec.id, None)


def require_root_release(root, parent, rec, event=None):
    """Read authoritative historical records; creates no execution authority."""
    from .canonical_case_claim import read_held_task, attempt_journal, root_metadata, claimed_root_identity
    from .work_configuration import build_root_work_factory
    from .work_budget import StopScope
    from .child_evidence import child_identity
    nonce = "03414499dd0d1986968b2393d44275d0"
    identity = child_identity(rec)
    if not (isinstance(parent, InvocationIdentity) and parent.task_id.endswith(nonce) and
            identity.parent_task_id == parent.task_id and identity.parent_agent_id == parent.agent_id and
            rec.parent_run_token == parent.run_token):
        raise SchedulerError("exact original case parent required for release")
    task = read_held_task(root, parent.task_id, parent.run_token).task
    if claimed_root_identity(task) != parent:
        raise SchedulerError("historical case parent identity changed")
    journal = attempt_journal({"root": root, "identity": parent, "recovery": True})
    admitted = journal.read_once("single-case-root-admit")
    binding = admitted["binding"]
    if (admitted["task_id"], admitted["run_token"], admitted["fencing_token"]) != (
            parent.task_id, parent.run_token, parent.fencing_token):
        raise SchedulerError("original consumed root claim changed")
    fence = journal.read_once("case-fenced")
    journal.read_once("case-fence-intent")
    closure = root_metadata("closure", binding)
    identities = [parent.to_json(), identity.to_json()]
    if not (fence == {"binding": binding, "identities": identities} and
        closure["namespaces"]["child"] == rec.namespace_lifetime and
        closure["observation"] == {"fenced": True, "case_cgroup_empty": True, "descendants": [],
            "fds": [], "maps": [], "profile_holders": [], "complete": True, "boot_id": binding["boot_id"]}):
        raise SchedulerError("complete exact root holder closure unavailable")
    rows = []
    for role in ("root", "child"):
        chosen = None
        for phase in ("sdk-ready", "sealed", "prepared-command"):
            try: chosen = journal.read_once(role + "-launch-" + phase); break
            except FileNotFoundError: pass
        if chosen is not None: rows.append(chosen)
    if not (len(rows) == 2 and [row["identity"] for row in rows] == identities and
            digest(rows) == closure["roster_sha256"]):
        raise SchedulerError("historical root closure roster changed")
    if event is not None and not (event["binding"] == binding and
            event["identity"] == identity.to_json() and event["idempotency_key"] == rec.idempotency_key and
            event["closure_sha256"] == digest(closure)):
        raise SchedulerError("retirement event differs from immutable root proof")
    # Recovery factory reopens ONLY original admitted allocations; approve() is
    # explicitly disabled in recovery. No signer, fresh grant or prepare occurs.
    work = build_root_work_factory(root, task, recovery=True)
    allocation = work.budget_definition["allocation"]["allocation_id"]
    stops = work.budget_authority.snapshot(allocation)["active_stops"]
    for selected in identities:
        stop_id = digest({"binding": binding, "identity": selected})
        if not any(row["stop_id"] == stop_id and row["scope"] == StopScope.TASK.value and
                   row["target"] == selected["task_id"] for row in stops):
            raise SchedulerError("original case task-scoped budget stop missing")
    return closure


def require_case_admission_release(entry):
    """Deny-only hook in original AdmissionRegistry.release for this nonce only."""
    from pathlib import Path
    from .host_configuration import _read_configuration, HOST_POLICY_CONFIG
    from .canonical_case_claim import read_held_task, claimed_root_identity
    from .ownership_inventory import LegacyOwnershipInventory, _InventoryAudit
    from .scheduler import DynamicChildScheduler
    from agent_durable_children import attempt_directory
    import os
    nonce = "03414499dd0d1986968b2393d44275d0"
    if nonce not in entry["task_id"]: return
    selector = _read_configuration(Path("/etc/herdr/offline-case-host.json"))
    root = Path(_read_configuration(HOST_POLICY_CONFIG)["task_store_root"])
    task = read_held_task(root, selector["task_id"], selector["run_token"]).task
    parent = claimed_root_identity(task)
    directory = attempt_directory(root, parent.task_id, parent.run_token)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        inventory = LegacyOwnershipInventory(root)
        inventory._directory(fd)
        events, _ = inventory._events(fd)
    finally: os.close(fd)
    scheduler = DynamicChildScheduler(audit_log=_InventoryAudit(events)); scheduler.replay()
    rec = scheduler.record_for(entry["task_id"])
    from .ownership_release import required_namespace_kind, validate_recorded_namespace_lifetime
    if required_namespace_kind(scheduler, rec) != "native":
        raise SchedulerError("case admission release lacks admitted native child")
    if rec.namespace_lifetime is not None:
        validate_recorded_namespace_lifetime(scheduler, rec, rec.namespace_lifetime)
    if not (rec.agent_id == entry["agent_id"] and rec.fencing_token == entry["fencing_token"] and
            rec.attempt_state == "terminal" and rec.cleanup_complete and rec.lease is None):
        raise SchedulerError("case admission release lacks original terminal cleanup")
    retired = [row for row in events if row.get("event") == "case_execution_retired" and
               row.get("identity", {}).get("task_id") == rec.id]
    if len(retired) > 1: raise SchedulerError("ambiguous case retirement evidence")
    require_root_release(root, parent, rec, retired[0] if retired else None)
