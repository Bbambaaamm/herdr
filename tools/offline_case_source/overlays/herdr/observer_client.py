"""Protected host-only observer client. SDK self-observation stays direct.

Caller context only selects an admitted slot; it cannot mint authority. The
root peer independently checks controller, target, plan and all measurements.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import os
from pathlib import Path
import socket
import stat
import struct

from .case_roster import ROSTER_PATH, CONTEXT_ROOT, SOCKET_PATH, Roster, canonical, decode, digest, require, exact, load_roster
from .trusted_observer import VERSION, normalized_rows

_BOUND = ContextVar("herdr_exact_observer_context", default=None)


@contextmanager
def bound_observer(*, role, identity, pid, start_ticks):
    require(role in ("root", "child") and type(pid) is int and pid > 0
        and type(start_ticks) is int and start_ticks > 0, "real_bound_process_identity_required")
    token = _BOUND.set((role, identity.to_json(), pid, start_ticks))
    try: yield
    finally: _BOUND.reset(token)


class LinuxClientOps:
    def __init__(self):
        from herdr.security import InvocationIdentity
        from .prep_entry import protected_json
        self.identity_type, self.read_json = InvocationIdentity, protected_json
    def roster(self): return load_roster(self.read_json, self.identity_type)
    def context(self, role):
        value = self.read_json(Path(CONTEXT_ROOT) / (role + ".json")); roster = self.roster()
        require(value["slot_sha256"] == digest(roster.slot(role)) and
            value["child_projection_sha256"] == roster.projection_sha256(role), "original_slot_projection_changed")
        return value
    def exchange(self, payload, roster):
        # An immutable root-owned parent prevents a same-UID process from
        # replacing this pathname. Group write on the socket permits connect,
        # never directory replacement or approval edits.
        directory = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            for component in Path(SOCKET_PATH).parts[1:-1]:
                opened = os.open(component, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
                os.close(directory); directory = opened
                st = os.fstat(directory)
                require(st.st_uid == 0 and not st.st_mode & 0o022, "observer_socket_ancestry_untrusted")
            before = os.stat("observer.sock", dir_fd=directory, follow_symlinks=False)
            require(stat.S_ISSOCK(before.st_mode) and before.st_uid == 0 and before.st_gid == 1001
                and stat.S_IMODE(before.st_mode) == 0o660, "exact_root_observer_socket_required")
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            try:
                connection.settimeout(2)
                connection.connect(SOCKET_PATH)
                peer = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                label = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERSEC, 1025)
                require(type(label) is bytes and 0 < len(label) <= 1024, "bounded_observer_peer_label_required")
                label = label[:-1] if label.endswith(b"\0") else label
                require(b"\0" not in label and label.decode("utf-8", "strict") ==
                    roster.document["observer"]["profile"], "exact_observer_peer_label_required")
                after = os.stat("observer.sock", dir_fd=directory, follow_symlinks=False)
                require(peer[0] > 0 and peer[1:] == (0, 0) and
                    (before.st_dev, before.st_ino, before.st_uid, before.st_gid, before.st_mode) ==
                    (after.st_dev, after.st_ino, after.st_uid, after.st_gid, after.st_mode),
                    "observer_peer_or_socket_changed")
                self.peer_pid = peer[0]
                require(connection.send(payload) == len(payload), "observer_request_uncertain")
                answer, ancillary, flags, _ = connection.recvmsg(65537, 0)
                require(not flags and not ancillary and len(answer) <= 65536, "observer_reply_invalid")
                return answer
            finally: connection.close()
        finally: os.close(directory)


def observe_from_host(pid, approved, rows, admitted_workspace, *, ops=None):
    """Return False on EVERY unsupported/unbound/changed/unknown response.

    There is deliberately no direct read fallback for external callers.
    """
    try:
        bound = _BOUND.get()
        require(pid != os.getpid(), "host_only_bound_observer_required")
        if bound is None:
            from .observed_proc import rpc
            measured, context = rpc(pid, "", "locate")
            role = context["role"]
            # The same authenticated root context yields the initial PID/ticks
            # through a separate metadata packet; it does not grant authority.
            bound = (role, context["identity"], pid, measured["start_ticks"])
        role, identity, expected_pid, ticks = bound
        require(pid == expected_pid, "bound_target_pid_changed")
        ops = LinuxClientOps() if ops is None else ops
        roster = ops.roster(); slot = roster.slot(role); context = ops.context(role)
        require(slot["identity"] == identity and slot["workspace"] == admitted_workspace
            and context["roster_sha256"] == roster.sha256 and context["identity"] == identity
            and context["approved_profile"] == approved, "exact_admitted_host_context_required")
        request = {"v": VERSION, "role": role, "context_sha256": digest(context),
            "pid": pid, "start_ticks": ticks, "mounts_sha256": digest(normalized_rows(rows)),
            "profile_sha256": approved["manifest_sha256"]}
        payload = canonical(request)
        reply = decode(ops.exchange(payload, roster))
        expected = {"v": VERSION, "request_sha256": hashlib.sha256(payload).hexdigest(),
            "roster_sha256": roster.sha256, "context_sha256": digest(context), "role": role,
            "pid": pid, "start_ticks": ticks, "identity_sha256": digest(identity),
            "plan_sha256": context["plan_sha256"], "profile_sha256": approved["manifest_sha256"],
            "mounts_sha256": request["mounts_sha256"], "worker_source_sha256": roster.document["worker_source_sha256"],
            "observer_source_sha256": digest(roster.document["observer"]["files"]),
            "observer_loaded_sha256": roster.document["observer"]["loaded_sha256"]}
        exact(reply, set(expected) | {"credentials_isolated", "loaded_worker_sha256", "observer_pid", "observer_start_ticks"})
        # The loaded worker digest is pinned by the SAME root-owned kernel
        # approval that the host preflight/retained verifier uses, not supplied
        # by the SDK or inferred from a profile name.
        expected_loaded = ops.read_json(Path("/etc/herdr/worker-confinement.json"))["loaded_sha256"]
        require(reply["loaded_worker_sha256"] == expected_loaded and
            reply["observer_pid"] == ops.peer_pid and type(reply["observer_start_ticks"]) is int
            and reply["observer_start_ticks"] > 0 and
            all(reply[k] == v for k, v in expected.items()) and
            type(reply["credentials_isolated"]) is bool and
            ops.roster().sha256 == roster.sha256 and ops.context(role) == context,
            "observer_evidence_binding_changed")
        return reply["credentials_isolated"]
    except Exception:
        return False
