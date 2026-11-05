"""Same-authority, read-only credential-boundary evidence helper.

No grant/provider/budget/fence operation is exposed. The sole method observes
one of TWO existing admitted identities through immutable custody evidence.
Imports are inert. Linux metadata operations run only in the explicit root
observer entrypoint under its separately approved profile.
"""
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import struct
import time

from .case_roster import (CONTEXT_ROOT, SOCKET_PATH, ROSTER_PATH, Roster, OBSERVER_LABEL,
                        WORKER_LABEL, SUFFIX, canonical, digest, decode, exact, hex64, require, load_roster)

VERSION = "herdr-offline-observer-2"
MAX_PACKET = 65536
REQUEST_KEYS = {"v", "role", "context_sha256", "pid", "start_ticks", "mounts_sha256", "profile_sha256"}


def normalized_rows(rows):
    require(type(rows) is dict and len(rows) <= 4096 and all(type(k) is str for k in rows), "bounded_mount_rows_required")
    return {k: sorted(v) for k, v in rows.items()}


def process_request(raw, peer, ops):
    """The only protocol operation. All authority/context comes from root storage."""
    require(type(raw) is bytes and 0 < len(raw) <= 4096, "bounded_observer_request_required")
    request = decode(raw); exact(request, REQUEST_KEYS)
    require(request["v"] == VERSION and request["role"] in ("root", "child")
        and all(hex64(request[k]) for k in ("context_sha256", "mounts_sha256", "profile_sha256"))
        and type(request["pid"]) is int and request["pid"] > 0
        and type(request["start_ticks"]) is int and request["start_ticks"] > 0,
        "invalid_observer_request")
    roster = ops.roster()
    roster.live(now=ops.now(), boot_id=ops.boot_id())
    ops.case_live(roster)
    doc = roster.document; slot = roster.slot(request["role"])
    require(peer == (doc["controller"]["pid"], 1001, 1001), "exact_controller_peer_required")
    controller = ops.controller()
    require(controller == doc["controller"], "controller_pid_start_exe_or_cgroup_changed")
    ops.verify_observer(doc["observer"])
    context = ops.context(request["role"])
    require(digest(context) == request["context_sha256"] and
        context["schema"] == "herdr-observer-context-2" and context["roster_sha256"] == roster.sha256
        and context["identity"] == slot["identity"] and context["role"] == request["role"]
        and context["workspace"] == slot["workspace"] and context["unit"] == slot["unit"],
        "canonical_existing_custody_context_changed")
    _, selected_role, selected_context, _, _ = ops.metadata().locate(request["pid"])
    require(selected_role == request["role"] and selected_context == context, "target_not_recorded_for_role")
    require(datetime.now(UTC) < datetime.fromisoformat(context["grant_expires_at"]), "original_grant_expired")
    if request["role"] == "child":
        parent = ops.context("root")
        bound_parent = ops.parent_grant(context)
        require(bound_parent.hash == context["parent_grant_hash"] and
                bound_parent.identity.to_json() == parent["identity"] and bound_parent.is_active(),
                "canonical_parent_sealed_grant_changed")
    plan = ops.original_plan(context)
    require(plan.sha256 == context["plan_sha256"], "original_root_plan_changed")
    before = ops.target(request["pid"], slot, context)
    require(before["start_ticks"] == request["start_ticks"] and before["uid"] == before["gid"] == 1001
        and before["label"] == WORKER_LABEL + " (enforce)", "target_process_identity_changed")
    rows = ops.mount_rows(request["pid"])
    require(digest(normalized_rows(rows)) == request["mounts_sha256"], "host_and_root_mount_observation_differ")
    plan.verify_mounted(request["pid"], rows)
    approved = context["approved_profile"]
    require(approved["manifest_sha256"] == request["profile_sha256"], "protected_profile_context_changed")
    require(ops.identity_environment(request["pid"], slot["identity"], slot["marker"]), "process_fence_or_run_identity_changed")
    # This is the accepted direct observer/evaluator with the narrow new
    # source pin. It measures profile/raw_data, namespaces, runtime files,
    # aliases, safe projection, environment, FDs and every live descendant.
    decision = ops.observe_direct(request["pid"], approved, rows, slot["workspace"])
    require(type(decision) is bool, "observer_decision_type_invalid")
    after = ops.target(request["pid"], slot, context)
    require(after == before and ops.controller() == controller
        and ops.roster().sha256 == roster.sha256 and ops.context(request["role"]) == context,
        "observation_context_changed")
    kernel = ops.worker_kernel()
    source = ops.observer_source_sha256()
    require(kernel["source_sha256"] == doc["worker_source_sha256"]
        and kernel["loaded_sha256"] == ops.loaded_worker_sha256()
        and source == digest(doc["observer"]["files"]), "observer_source_or_kernel_binding_changed")
    return {"v": VERSION, "request_sha256": hashlib.sha256(raw).hexdigest(),
        "roster_sha256": roster.sha256, "context_sha256": digest(context), "role": request["role"],
        "pid": request["pid"], "start_ticks": before["start_ticks"],
        "identity_sha256": digest(slot["identity"]), "plan_sha256": context["plan_sha256"],
        "profile_sha256": request["profile_sha256"], "mounts_sha256": request["mounts_sha256"],
        "worker_source_sha256": kernel["source_sha256"], "loaded_worker_sha256": kernel["loaded_sha256"],
        "observer_source_sha256": source, "observer_loaded_sha256": doc["observer"]["loaded_sha256"],
        "observer_pid": ops.self_pid(), "observer_start_ticks": ops.self_ticks(),
        "credentials_isolated": decision}


class LinuxObserverOps:
    """Actual bounded metadata adapter, no subprocess/service/provider functions."""
    def __init__(self, protected_json, identity_type):
        self.read_json = protected_json
        self.identity_type = identity_type
        self._metadata = None
    def metadata(self):
        if self._metadata is None:
            from .metadata_provider import MetadataOps
            self._metadata = MetadataOps(self)
        return self._metadata
    def now(self): return time.time()
    def boot_id(self): return self.read_bounded(Path("/proc/sys/kernel/random/boot_id"), 128).decode().strip()
    def roster(self): return load_roster(self.read_json, self.identity_type)
    def context(self, role):
        require(role in ("root", "child"), "unknown_observer_role")
        value = self.read_json(Path(CONTEXT_ROOT) / (role + ".json"))
        roster = self.roster()
        require(value["slot_sha256"] == digest(roster.slot(role)) and
            value["child_projection_sha256"] == roster.projection_sha256(role), "original_slot_projection_changed")
        return value
    def case_live(self, roster):
        base = Path("/var/lib/herdr-offline-" + SUFFIX)
        state = self.read_json(base / "state.json")
        authority = self.read_json(base / "authority.json")
        binding = roster.document["case_binding"]
        require(state["binding"] == binding and digest(authority) == binding["authority_sha256"] and
            state["phase"] in {"ADMITTED", "PREPARED", "START_INTENT"} and
            type(authority["deadline"]) in (int, float) and roster.document["deadline"] <= authority["deadline"],
            "case_fenced_or_authority_changed")
    def self_pid(self): return os.getpid()
    def self_ticks(self): return self.ticks(os.getpid())
    @staticmethod
    def read_bounded(path, bound):
        # /proc/PID/root is intentionally a kernel cross-process reference;
        # the accepted observer validates its entire private namespace view.
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        try:
            raw = os.read(fd, bound + 1)
            require(len(raw) <= bound, "kernel_metadata_bound")
            return raw
        finally: os.close(fd)
    def ticks(self, pid):
        raw = self.read_bounded(Path(f"/proc/{pid}/stat"), 65536)
        require(raw.startswith(str(pid).encode() + b" ("), "proc_pid_identity_changed")
        return int(raw.rsplit(b")", 1)[1].split()[19])
    def controller(self):
        from herdr import launch_plan_issuer as authority
        roster = self.roster(); expected = roster.document["controller"]
        issuer, policy = authority._policy()
        require(authority._digest(policy) == roster.document["host_policy_sha256"], "original_policy_changed")
        peer = authority._host_peer(expected["pid"], 1001, 1001, issuer, policy)
        require(peer[3] == expected["start_ticks"], "original_controller_reused")
        pid = expected["pid"]; before = self.ticks(pid)
        info = Path(f"/proc/{pid}").stat()
        fd = os.open(f"/proc/{pid}/exe", os.O_RDONLY | os.O_CLOEXEC)
        try:
            h = hashlib.sha256(); total = 0
            while True:
                raw = os.read(fd, 65536)
                if not raw: break
                total += len(raw); require(total <= 16777216, "controller_executable_bound"); h.update(raw)
        finally: os.close(fd)
        groups = self.read_bounded(Path(f"/proc/{pid}/cgroup"), 4096).decode().splitlines()
        require(len(groups) == 1 and groups[0].startswith("0::"), "canonical_controller_cgroup_required")
        require(self.ticks(pid) == before, "controller_changed_during_inspection")
        label = self.read_bounded(Path(f"/proc/{pid}/attr/current"), 1024).decode().strip()
        require(label == expected["profile"] + " (enforce)" and
            self.loaded_profile_sha256(expected["profile"]) == expected["loaded_sha256"],
            "controller_compiled_profile_changed")
        from .prep_entry import protected_bytes
        require(hashlib.sha256(protected_bytes(Path(ROSTER_PATH).parent / "controller.apparmor")).hexdigest()
            == expected["source_sha256"], "controller_profile_source_changed")
        return {"uid": info.st_uid, "gid": info.st_gid, "pid": pid, "start_ticks": before,
                "exe_sha256": h.hexdigest(), "cgroup": groups[0][3:], "profile": expected["profile"],
                "loaded_sha256": expected["loaded_sha256"], "source_sha256": expected["source_sha256"]}
    def verify_observer(self, expected):
        require(os.geteuid() == os.getegid() == 0 and
            self.read_bounded(Path("/proc/self/attr/current"), 1024).decode().strip()
            == expected["profile"] + " (enforce)", "exact_root_observer_domain_required")
        status = dict(line.split(":", 1) for line in self.read_bounded(Path("/proc/self/status"), 65536).decode().splitlines() if ":" in line)
        allowed = (1 << 19) | (1 << 2)  # CAP_SYS_PTRACE, CAP_DAC_READ_SEARCH only
        require(status.get("NoNewPrivs", "").strip() == "1" and
            all(int(status[name].strip(), 16) & ~allowed == 0 for name in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"))
            and int(status["CapEff"].strip(), 16) & (1 << 19), "readonly_observer_capability_boundary_changed")
        require(self.loaded_profile_sha256(expected["profile"]) == expected["loaded_sha256"],
                "observer_compiled_profile_changed")
        from .prep_entry import protected_bytes
        require(hashlib.sha256(protected_bytes(Path(ROSTER_PATH).parent / "observer.apparmor")).hexdigest()
            == expected["source_sha256"], "observer_profile_source_changed")
        require(self.read_bounded(Path("/proc/self/cgroup"), 4096).decode().splitlines() ==
            ["0::/system.slice/herdr-offline-observer-" + SUFFIX + ".service"], "owned_observer_unit_required")
        interpreter = Path(expected["python"])
        actual, wanted = Path("/proc/self/exe").stat(), interpreter.stat()
        require((actual.st_dev, actual.st_ino) == (wanted.st_dev, wanted.st_ino)
            and hashlib.sha256(protected_bytes(interpreter, 16777216)).hexdigest() == expected["python_sha256"],
            "observer_interpreter_changed")
        self.observer_source_sha256()
    def loaded_profile_sha256(self, label):
        from herdr.credential_isolation import KERNEL_PROFILES
        found = []
        for number, base in enumerate(KERNEL_PROFILES.iterdir()):
            require(number < 4096, "profile_inventory_bound")
            if base.is_dir() and self.read_bounded(base / "name", 256).strip() == label.encode():
                found.append(hashlib.sha256(self.read_bounded(base / "raw_data", 16777216)).hexdigest())
        require(len(found) == 1, "loaded_profile_missing_or_ambiguous")
        return found[0]
    def original_plan(self, context):
        from herdr.private_mount_plan import ApprovedPrivateMountPlan, AUTHORITY_ROOT
        identity = self.identity_type.from_dict(context["identity"])
        plan = ApprovedPrivateMountPlan.read(AUTHORITY_ROOT / (digest(identity.to_json()) + ".json"), identity)
        plan.authorize(context["plan"]["descriptors"], context["argv"])
        return plan
    def parent_grant(self, context):
        from herdr.security import SecurityGrant
        return SecurityGrant.from_dict(context["parent_grant"])
    def target(self, pid, slot, context):
        group = "/system.slice/" + slot["unit"]
        base = Path("/sys/fs/cgroup") / group.lstrip("/")
        fd = os.open(base, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            require([info.st_dev, info.st_ino] == context["cgroup_identity"], "owned_target_cgroup_replaced")
            procs = os.open("cgroup.procs", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            try: raw = os.read(procs, 65537)
            finally: os.close(procs)
            require(len(raw) <= 65536 and str(pid).encode() in raw.split(), "target_not_in_owned_unit")
        finally: os.close(fd)
        before = self.ticks(pid)
        require(self.read_bounded(Path(f"/proc/{pid}/cgroup"), 4096).decode().splitlines() == ["0::" + group],
                "target_cgroup_changed")
        info = Path(f"/proc/{pid}").stat()
        label = self.read_bounded(Path(f"/proc/{pid}/attr/current"), 1024).decode().strip()
        namespaces = {name: os.readlink(f"/proc/{pid}/ns/{name}") for name in ("pid", "mnt", "net", "user")}
        require(all(value != os.readlink("/proc/self/ns/" + key) for key, value in namespaces.items())
            and self.ticks(pid) == before, "private_target_namespace_or_pid_changed")
        return {"uid": info.st_uid, "gid": info.st_gid, "start_ticks": before,
                "label": label, "namespaces": namespaces, "cgroup_identity": context["cgroup_identity"]}
    def mount_rows(self, pid):
        from herdr.policy_launch import mount_rows
        return mount_rows(pid)
    def identity_environment(self, pid, identity, marker):
        from herdr.policy_launch import IDENTITY_ENV
        raw = self.read_bounded(Path(f"/proc/{pid}/environ"), 262144)
        pairs = raw.rstrip(b"\0").split(b"\0"); values = {}
        for item in pairs:
            require(b"=" in item, "malformed_process_environment")
            key, value = item.split(b"=", 1)
            require(key not in values, "duplicate_process_environment_key"); values[key] = value
        return all(values.get(name.encode()) == str(identity[field]).encode() for field, name in IDENTITY_ENV.items()) and \
            values.get(b"HERDR_DURABLE_TASK_PANE") == marker.encode()
    def observe_direct(self, pid, approved, rows, workspace):
        from herdr.credential_isolation import _observe_sdk_credentials_direct
        return _observe_sdk_credentials_direct(pid, approved, rows, workspace)
    def worker_kernel(self):
        from herdr.credential_isolation import _approved_confinement
        record = _approved_confinement()
        return {"source_sha256": record["source_sha256"], "loaded_sha256": record["loaded_sha256"]}
    def loaded_worker_sha256(self): return self.loaded_profile_sha256(WORKER_LABEL)
    def observer_source_sha256(self):
        expected = self.roster().document["observer"]
        base = Path(expected["entrypoint"]).parent
        for relative, value in expected["files"].items():
            from .prep_entry import protected_bytes
            require(hashlib.sha256(protected_bytes(base / relative)).hexdigest() == value,
                    "root_observer_source_changed")
        return digest(expected["files"])


def serve(ops, *, socket_factory=socket.socket):
    """Bounded owned socket, no target mutation and no secret exception text."""
    roster = ops.roster(); ops.verify_observer(roster.document["observer"])
    listener = socket_factory(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    inode = None
    try:
        require(not os.path.lexists(SOCKET_PATH), "preexisting_observer_socket_unknown")
        listener.bind(SOCKET_PATH)
        os.chown(SOCKET_PATH, 0, 1001); os.chmod(SOCKET_PATH, 0o660)
        info = os.lstat(SOCKET_PATH); inode = (info.st_dev, info.st_ino)
        listener.listen(2); listener.settimeout(0.2)
        count = 0
        while ops.now() < roster.document["deadline"] and count < 32768:
            try: connection, _ = listener.accept()
            except socket.timeout: continue
            count += 1
            with connection:
                connection.settimeout(2)
                try:
                    peer = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                    require(peer == (roster.document["controller"]["pid"], 1001, 1001), "wrong_observer_peer")
                    raw, ancillary, flags, _ = connection.recvmsg(8193, 0)
                    require(not ancillary and not flags and len(raw) <= 8192, "observer_packet_invalid")
                    from herdr.observed_proc import root_direct_scope
                    with root_direct_scope():
                        from herdr.bootstrap_self_observation import PREFLIGHT, KERNEL_REQUEST, process_preflight, process_kernel_request
                        version = decode(raw).get("v")
                        if version == PREFLIGHT:
                            reply = process_preflight(raw, peer, ops)
                        elif version == KERNEL_REQUEST:
                            reply = process_kernel_request(raw, peer, ops)
                        elif version == "herdr-offline-metadata-2":
                            from .metadata_provider import process_metadata
                            reply = process_metadata(raw, peer, ops.metadata())
                        else:
                            reply = process_request(raw, peer, ops)
                except Exception:
                    reply = {"v": VERSION, "error": "OBSERVATION_UNKNOWN"}
                encoded = canonical(reply)
                if len(encoded) > MAX_PACKET:
                    encoded = canonical({"v": VERSION, "error": "OBSERVATION_UNKNOWN"})
                try: require(connection.send(encoded) == len(encoded), "observer_reply_uncertain")
                except OSError: pass
    finally:
        listener.close()
        if inode is not None:
            info = os.lstat(SOCKET_PATH)
            require((info.st_dev, info.st_ino) == inode, "observer_socket_replaced")
            os.unlink(SOCKET_PATH)
