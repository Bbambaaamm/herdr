"""Host-only proof that a claimed PID namespace has ceased to execute."""
from __future__ import annotations
import os
import re
from pathlib import Path
from .child_ownership import OwnershipError, require
from .security import InvocationIdentity


def process_identity(pid):
    require(type(pid) is int and pid > 0, "ownership_namespace_pid")
    raw = Path(f"/proc/{pid}/stat").read_text()
    require(len(raw) <= 8192 and ") " in raw, "ownership_namespace_stat")
    fields = raw.rsplit(") ", 1)[1].split()
    require(len(fields) >= 20, "ownership_namespace_stat")
    return fields[0], int(fields[19])


def capture_namespace_lifetime(pid):
    _before_state, before_ticks = process_identity(pid)
    status = Path(f"/proc/{pid}/status").read_text()
    require(len(status) <= 131072, "ownership_namespace_status")
    ids = next((line.split()[1:] for line in status.splitlines() if line.startswith("NSpid:")), [])
    require(len(ids) >= 2 and ids[-1] == "1", "ownership_namespace_init_required")
    namespace = os.readlink(f"/proc/{pid}/ns/pid")
    require(namespace != os.readlink("/proc/self/ns/pid"), "ownership_namespace_host")
    state, ticks = process_identity(pid)
    require(state != "Z" and ticks == before_ticks
            and os.readlink(f"/proc/{pid}/ns/pid") == namespace, "ownership_namespace_changed")
    return {"version": 1, "pid": pid, "start_ticks": ticks, "namespace": namespace}


def validate_namespace_lifetime(value):
    require(isinstance(value, dict) and set(value) == {"version", "pid", "start_ticks", "namespace"}
            and type(value["version"]) is int and value["version"] == 1
            and type(value["pid"]) is int and value["pid"] > 0
            and type(value["start_ticks"]) is int and value["start_ticks"] > 0
            and isinstance(value["namespace"], str)
            and re.fullmatch(r"pid:\[[0-9]+\]", value["namespace"]), "ownership_namespace_proof")
    return dict(value)


def namespace_exited(value):
    value = validate_namespace_lifetime(value)
    try:
        state, ticks = process_identity(value["pid"])
    except (FileNotFoundError, ProcessLookupError):
        return True
    # The init's exit kills/reaps the entire PID namespace before its PID is
    # reusable. A reused PID cannot keep the original namespace alive.
    return ticks != value["start_ticks"] or state == "Z"


class HostOwnershipRelease:
    """Read canonical terminal/cleanup truth and the host-captured init lifetime."""
    def __init__(self, root):
        self.root = Path(root).absolute()

    def __call__(self, identity, evidence):
        from .ownership_inventory import LegacyOwnershipInventory, _InventoryAudit
        from .scheduler import DynamicChildScheduler
        import hashlib
        try:
            require(isinstance(identity, InvocationIdentity), "ownership_release_identity")
            require(isinstance(evidence, dict) and set(evidence) == {"parent"},
                    "ownership_release_evidence")
            parent = InvocationIdentity.from_dict(evidence["parent"])
            require((parent.consumer, parent.task_id, parent.agent_id) ==
                    (identity.consumer, identity.parent_task_id, identity.parent_agent_id),
                    "ownership_release_parent")
            name = hashlib.sha256(f"{parent.task_id}:{parent.run_token}".encode()).hexdigest()
            path = self.root / "durable-children" / name
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                inventory = LegacyOwnershipInventory(self.root)
                inventory._directory(fd)
                events, _ = inventory._events(fd)
            finally:
                os.close(fd)
            scheduler = DynamicChildScheduler(audit_log=_InventoryAudit(events))
            scheduler.replay()
            rec = scheduler._tasks.get(identity.task_id)
            require(rec is not None and rec.ownership_reservation and
                    rec.parent_run_token == parent.run_token and
                    rec.attempt_state == "terminal" and rec.cleanup_complete and rec.lease is None,
                    "ownership_release_terminal")
            actual = InvocationIdentity("github:" + rec.repo, rec.agent_id, rec.parent_agent_id,
                rec.parent_task_id, rec.id, rec.run_token, rec.fencing_token)
            require(actual == identity and any(e.get("event") == "child_ownership_reserved"
                    and e.get("parent") == parent.to_json() and e.get("task_id") == rec.id
                    for e in events), "ownership_release_binding")
            if rec.namespace_lifetime is not None:
                return (rec.execution_sandbox_verified and
                        (rec.execution_sandbox_attestation or {}).get("sandbox_pid") ==
                            rec.namespace_lifetime["pid"]
                        and namespace_exited(rec.namespace_lifetime))
            if scheduler._ownership_read_only(rec):
                return True
            # Versioned pre-effect/no-split state proves there was no namespace
            # or agent invocation. An old ambiguous split retains quarantine.
            return (bool(rec.pre_delivery_failure) and not rec.pre_delivery_agent_start_attempted
                    and rec.economic_delivery_attempted is not True and not rec.execution_pane
                    and (not rec.pre_delivery_pane_creation_attempted or rec.pane_split_started is False))
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            return False
