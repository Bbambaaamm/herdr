"""Additive dispatch in the EXISTING Herdr descriptor custody authority.

Proposed core overlay, never run here. Non-root clients retain the original
redeem implementation byte-for-byte. Root receives only the already staged
descriptor set after an exact separate root preparation record; it cannot
issue grants, widen a plan or register replacement descriptors.
"""
import array
import hashlib
import json
from pathlib import Path
import socket
import struct
import time

VERSION = "herdr-native-preparation-1"
APPROVAL = Path("/etc/herdr/native-preparation.json")
NONCE = "03414499dd0d1986"
PREP_CGROUP = "/system.slice/herdr-offline-" + NONCE + ".service"


def dispatch_existing_custody(custody, connection):
    """One-line additive hook at the existing fd-listener dispatch site."""
    peer = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    if peer[1] != 0:
        return custody.redeem(connection)
    return redeem_root_preparation(custody, connection, peer)


def _root_record(authority):
    record = authority.host._read_configuration(APPROVAL)
    authority.require(type(record) is dict and record.get("schema_version") == VERSION,
                      "native preparation is not approved")
    return record


def _root_peer(authority, peer, record):
    """Exact PID/start/exe/argv/cgroup/loaded label, checked again before send."""
    pid, uid, gid = peer
    authority.require(uid == gid == 0 and pid > 0, "root preparation peer required")
    start = authority.process_start_ticks(pid)
    command = authority._proc_bytes(pid, "cmdline", 32768).rstrip(b"\0").decode().split("\0")
    prep = record["preparer"]
    authority.require(command == record["native_argv"] and len(command) >= 5
        and command[1:3] == ["-I", "-B"] and command[3] == prep["entrypoint"]
        and command[4] == "--execute", "exact native preparation entrypoint required")
    label = authority._proc_bytes(pid, "attr/current", 1024).decode().strip()
    group = authority._proc_bytes(pid, "cgroup", 4096).decode().splitlines()
    authority.require(label == "herdr-offline-prep-" + NONCE + " (enforce)"
        and group == ["0::" + PREP_CGROUP], "exact owned preparation domain required")
    # Root configuration reader verifies every ancestry component and owner.
    # Source hashing below verifies the already root-published immutable files;
    # none is supplied by the worker and no code is imported from a request.
    from .policy_launch import _verify_root_owned_ancestry
    import os, stat
    def immutable(name, expected):
        path = Path(name)
        _verify_root_owned_ancestry(path.parent)
        raw, before = authority._read(path, 4_194_304)
        authority.require(before.st_uid == 0 and not before.st_mode & 0o022
            and stat.S_ISREG(before.st_mode) and hashlib.sha256(raw).hexdigest() == expected,
            "native preparation immutable source differs")
        return before
    script = immutable(prep["entrypoint"], prep["sha256"])
    interpreter = immutable(command[0], prep["python_sha256"])
    actual = os.stat(f"/proc/{pid}/exe")
    authority.require((actual.st_dev, actual.st_ino) == (interpreter.st_dev, interpreter.st_ino),
                      "native preparation interpreter inode differs")
    files = prep["files"]
    authority.require(type(files) is dict and set(files) == {
        "trusted_prepare.py", "native_preparation.py", "prep_entry.py"},
        "exact preparation module closure required")
    for name, digest in files.items(): immutable(Path(prep["entrypoint"]).parent / name, digest)
    immutable(Path(prep["entrypoint"]).parent / "overlays/trusted-preparation.apparmor", prep["profile_source_sha256"])
    # A same-name label is insufficient; measure exact loaded prep bytecode.
    from .credential_isolation import KERNEL_PROFILES, _read_bounded
    found = []
    for number, directory in enumerate(KERNEL_PROFILES.iterdir()):
        authority.require(number < 4096, "loaded profile inventory exceeds bound")
        if directory.is_dir() and _read_bounded(directory / "name", 256).strip() == prep["profile"].encode():
            found.append(hashlib.sha256(_read_bounded(directory / "raw_data", 16777216)).hexdigest())
    authority.require(found == [prep["loaded_sha256"]], "loaded preparation profile differs")
    authority.require(authority.process_start_ticks(pid) == start,
                      "native preparation peer changed")
    return (pid, uid, gid, start, label, tuple(group))


def redeem_root_preparation(custody, connection, peer, *, authority=None):
    """Consume BEFORE SCM_RIGHTS, using the existing pending-row lock and caps."""
    if authority is None:
        from . import launch_plan_issuer as authority
    issuer, policy = authority._policy()
    record = _root_record(authority)
    peer_stamp = _root_peer(authority, peer, record)
    connection.settimeout(issuer["request_timeout_seconds"])
    request, incoming = authority._receive(connection, (*peer, 0), minimum_fds=0)
    try:
        authority.require(not incoming and type(request) is dict and set(request) == {
            "schema_version", "identity_sha256", "plan_sha256", "preparation_sha256"}
            and request["schema_version"] == VERSION,
            "closed native preparation request required")
    finally:
        for fd in incoming: authority.os.close(fd)
    key = request["identity_sha256"]
    authority.require(type(key) is str and authority.re.fullmatch("[0-9a-f]{64}", key),
                      "native preparation identity digest invalid")
    row = custody._claim(key, wait=True)
    authority.require(row is not None, "original native custody unavailable; reconcile")
    try:
        proposal = row["request"]["proposal"]
        authority.require((issuer, policy) == (row["issuer"], row["raw"])
            and record["identity"] == proposal["plan"]["identity"]
            and record["host_policy_sha256"] == authority._digest(policy)
            and request["plan_sha256"] == record["plan_sha256"] == authority._digest(proposal["plan"])
            and record["argv_sha256"] == authority._digest(proposal["argv"])
            and request["preparation_sha256"] == authority._digest(record),
            "original custody preparation binding differs")
        # All original admission/provider/template/workspace/physical checks
        # run unchanged. A fresh preparation approval cannot revive an expired
        # grant, old host policy, missing plan or stale original host process.
        authority._validate(row["request"], row["fds"], row["peer"], policy)
        authority.require(authority._host_peer(*row["peer"][:3], issuer, policy) == row["peer"],
                          "original native descriptor owner changed")
        from .private_mount_plan import ApprovedPrivateMountPlan
        identity = authority.InvocationIdentity.from_dict(proposal["plan"]["identity"])
        plan = ApprovedPrivateMountPlan.read(authority.publication.AUTHORITY_ROOT / (key + ".json"), identity)
        plan.authorize(proposal["plan"]["descriptors"], proposal["argv"])
        from datetime import UTC, datetime
        now = datetime.now(UTC)
        authority.require(datetime.fromisoformat(record["not_before"]) <= now <
            datetime.fromisoformat(record["expires_at"]) <=
            datetime.fromisoformat(row["request"]["grant"]["expires_at"]), "preparation authority expired")
        authority.require(authority._policy() == (issuer, policy)
            and _root_record(authority) == record and _root_peer(authority, peer, record) == peer_stamp
            and time.monotonic() < row["deadline"], "preparation admission changed")
        with custody._lock:
            authority.require(custody.pending.get(key) is row and not row["cancelled"],
                              "original native descriptor custody withdrawn")
            custody.pending.pop(key)
        # No retry after an uncertain send. The original pending record is
        # consumed and all held duplicates are closed regardless of outcome.
        try:
            answer = authority.canonical_json_bytes({**request, "descriptor_count": len(row["fds"])})
            connection.settimeout(max(0.001, row["deadline"] - time.monotonic()))
            authority.require(connection.sendmsg([answer], [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                array.array("i", row["fds"]))]) == len(answer), "preparation reply uncertain; reconcile")
        finally: custody._close_row(row)
    finally: custody._release(key, row)
