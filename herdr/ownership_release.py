"""Host-only proof that a claimed PID namespace has ceased to execute."""
from __future__ import annotations
import os
import re
import stat
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


def _process_snapshot(pid):
    state, ticks = process_identity(pid)
    root = Path(f"/proc/{pid}")
    with (root / "status").open("rb") as stream:
        status = stream.read(131073)
    require(len(status) <= 131072, "ownership_namespace_status")
    rows = {line.split(":", 1)[0]: line.split()[1:]
            for line in status.decode().splitlines() if ":" in line}
    ids = tuple(int(value) for value in rows.get("NSpid", ()))
    uids = tuple(int(value) for value in rows.get("Uid", ()))
    with (root / "stat").open("rb") as stream:
        raw = stream.read(8193)
    require(len(raw) <= 8192 and b") " in raw, "ownership_namespace_stat")
    fields = raw.rsplit(b") ", 1)[1].split()
    require(len(fields) >= 20, "ownership_namespace_stat")
    with (root / "cgroup").open("rb") as stream:
        cgroup = stream.read(65537)
    require(0 < len(cgroup) <= 65536, "ownership_namespace_cgroup")
    executable = (root / "exe").stat()
    after_state, after_ticks = process_identity(pid)
    require(state not in {"Z", "X", "x"} and after_state not in {"Z", "X", "x"}
            and ticks == int(fields[19]) == after_ticks, "ownership_namespace_changed")
    return {"pid": pid, "start_ticks": ticks, "ppid": int(fields[1]),
            "ids": ids, "uids": uids, "cgroup": cgroup,
            "namespace": os.readlink(root / "ns/pid"),
            "mount_namespace": os.readlink(root / "ns/mnt"),
            "executable": (executable.st_dev, executable.st_ino)}


def _open_trusted_bwrap():
    path = Path("/usr/bin/bwrap")
    require(path.resolve(strict=True) == path, "ownership_namespace_bwrap_path")
    for directory in path.parents:
        info = directory.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0
                and not info.st_mode & 0o022, "ownership_namespace_bwrap_ancestor")
    fd = os.open(path, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                and info.st_mode & 0o111 and not info.st_mode & 0o022,
                "ownership_namespace_bwrap_source")
        return fd, (info.st_dev, info.st_ino)
    except BaseException:
        os.close(fd)
        raise


def capture_namespace_lifetime(pid):
    """Bind an already-verified payload to its actual trusted bwrap PID1."""
    require(type(pid) is int and pid > 0, "ownership_namespace_pid")
    payload = _process_snapshot(pid)
    require(2 <= len(payload["ids"]) <= 32 and payload["ids"][-1] > 1,
            "ownership_namespace_payload_required")
    require(payload["namespace"] != os.readlink("/proc/self/ns/pid")
            and payload["mount_namespace"] != os.readlink("/proc/self/ns/mnt"),
            "ownership_namespace_host")
    init_pid = payload["ppid"]
    require(init_pid > 0 and init_pid != pid, "ownership_namespace_parent")
    fd, executable = _open_trusted_bwrap()
    try:
        init = _process_snapshot(init_pid)
        require(len(init["ids"]) == len(payload["ids"]) and init["ids"][-1] == 1,
                "ownership_namespace_init_required")
        require(init["ppid"] > 0 and init["ppid"] not in {pid, init_pid},
                "ownership_namespace_parent")
        require(init["executable"] == executable, "ownership_namespace_init_executable")
        require(init["namespace"] == payload["namespace"]
                and init["mount_namespace"] == payload["mount_namespace"]
                and init["cgroup"] == payload["cgroup"]
                and init["uids"] == payload["uids"] == (os.getuid(),) * 4,
                "ownership_namespace_binding")
        require(_process_snapshot(pid) == payload and _process_snapshot(init_pid) == init,
                "ownership_namespace_changed")
        held = os.fstat(fd)
        named = Path("/usr/bin/bwrap").lstat()
        require(stat.S_ISREG(held.st_mode) and held.st_uid == 0 and held.st_nlink == 1
                and held.st_mode & 0o111 and not held.st_mode & 0o022,
                "ownership_namespace_bwrap_source")
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) == executable,
                "ownership_namespace_bwrap_changed")
        return {"version": 2, "pid": pid, "start_ticks": payload["start_ticks"],
                "namespace": payload["namespace"], "init_pid": init_pid,
                "init_start_ticks": init["start_ticks"]}
    finally:
        os.close(fd)


def validate_namespace_lifetime(value):
    require(isinstance(value, dict) and type(value.get("version")) is int
            and value["version"] in (1, 2), "ownership_namespace_proof")
    keys = {"version", "pid", "start_ticks", "namespace"}
    if value["version"] == 2:
        keys |= {"init_pid", "init_start_ticks"}
        require(type(value.get("init_pid")) is int and value["init_pid"] > 0
                and value["init_pid"] != value.get("pid")
                and type(value.get("init_start_ticks")) is int
                and value["init_start_ticks"] > 0, "ownership_namespace_proof")
    require(set(value) == keys
            and type(value["pid"]) is int and value["pid"] > 0
            and type(value["start_ticks"]) is int and value["start_ticks"] > 0
            and isinstance(value["namespace"], str)
            and re.fullmatch(r"pid:\[[0-9]+\]", value["namespace"]), "ownership_namespace_proof")
    return dict(value)


def namespace_exited(value):
    value = validate_namespace_lifetime(value)
    pid = value["init_pid"] if value["version"] == 2 else value["pid"]
    start_ticks = value["init_start_ticks"] if value["version"] == 2 else value["start_ticks"]
    try:
        state, ticks = process_identity(pid)
    except (FileNotFoundError, ProcessLookupError):
        return True
    # The init's exit kills/reaps the entire PID namespace before its PID is
    # reusable. A reused PID cannot keep the original namespace alive.
    return ticks != start_ticks or state == "Z"


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
                # V2 keeps pid bound to the attested payload; only its separately
                # captured trusted init determines whole-namespace retirement.
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
