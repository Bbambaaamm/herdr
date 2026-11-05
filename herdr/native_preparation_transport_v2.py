"""Same-authority v2 roster dispatch. No new issuer or grant authority."""
import array
import hashlib
import os
from pathlib import Path
import socket
import stat
import struct
import time
from .case_roster import Roster, ROSTER_PATH, CONTEXT_ROOT, SUFFIX, capture_context, canonical, digest, load_roster
from .preparation_contract import VERSION, validate_request, derive_record, native_argv


def dispatch_existing_custody(custody, connection):
    peer = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    if peer[1] != 0: return custody.redeem(connection)
    return redeem_root_preparation(custody, connection, peer)


def root_roster(authority):
    roster = load_roster(authority.host._read_configuration, authority.InvocationIdentity)
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    roster.live(now=time.time(), boot_id=boot)
    base = Path("/var/lib/herdr-offline-" + SUFFIX)
    auth = authority.host._read_configuration(base / "authority.json")
    used = authority.host._read_configuration(base / ("used-" + roster.document["nonce"] + ".json"))
    state = authority.host._read_configuration(base / "state.json")
    binding = roster.document["case_binding"]
    authority.require(digest(auth) == binding["authority_sha256"] and used == binding and
        state["binding"] == binding and state["phase"] in {"ADMITTED", "PREPARED", "START_INTENT"} and
        type(auth["deadline"]) in (int, float) and roster.document["deadline"] <= auth["deadline"],
        "original consumed case binding unavailable")
    return roster


def root_peer(authority, peer, roster, role, identity_sha256=None):
    pid, uid, gid = peer
    authority.require(uid == gid == 0 and pid > 0, "root preparation peer required")
    before = authority.process_start_ticks(pid)
    unit = "herdr-offline-" + role + "-" + SUFFIX + ".service"; prep = roster.document["preparer"]
    if role == "root": authority.require(set(roster.document["slots"]) == {"root"}, "initial root-only base required")
    argv = authority._proc_bytes(pid, "cmdline", 32768).rstrip(b"\0").decode().split("\0")
    authority.require(argv == native_argv(roster, role, identity_sha256), "exact roster native entry required")
    label = authority._proc_bytes(pid, "attr/current", 1024).decode().strip()
    groups = authority._proc_bytes(pid, "cgroup", 4096).decode().splitlines()
    authority.require(label == prep["profile"] + " (enforce)" and
        groups == ["0::/system.slice/" + unit], "owned preparation domain differs")
    from .policy_launch import _verify_root_owned_ancestry
    def immutable(name, expected):
        name = Path(name); _verify_root_owned_ancestry(name.parent)
        raw, info = authority._read(name, 16777216)
        authority.require(info.st_uid == 0 and not info.st_mode & 0o022 and
            hashlib.sha256(raw).hexdigest() == expected, "immutable preparation source differs")
        return info
    python = immutable(prep["python"], prep["python_sha256"])
    executable = os.stat(f"/proc/{pid}/exe")
    authority.require((executable.st_dev, executable.st_ino) == (python.st_dev, python.st_ino), "preparation interpreter changed")
    for name, value in prep["files"].items(): immutable(Path(prep["entrypoint"]).parent / name, value)
    immutable(Path(ROSTER_PATH).parent / "preparer.apparmor", prep["source_sha256"])
    from .credential_isolation import KERNEL_PROFILES, _read_bounded
    loaded = []
    for count, base in enumerate(KERNEL_PROFILES.iterdir()):
        authority.require(count < 4096, "profile inventory bound")
        if base.is_dir() and _read_bounded(base / "name", 256).strip() == prep["profile"].encode():
            loaded.append(hashlib.sha256(_read_bounded(base / "raw_data", 16777216)).hexdigest())
    authority.require(loaded == [prep["loaded_sha256"]] and authority.process_start_ticks(pid) == before,
                      "compiled preparation policy or peer changed")
    fd = os.open(Path("/sys/fs/cgroup/system.slice") / unit, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd); return (pid, uid, gid, before, info.st_dev, info.st_ino)
    finally: os.close(fd)


def publish_context(context):
    """Exclusive metadata receipt after original _validate; never an approval."""
    from .policy_launch import _verify_root_owned_ancestry
    _verify_root_owned_ancestry(Path(CONTEXT_ROOT).parent)
    try: os.mkdir(CONTEXT_ROOT, 0o750)
    except FileExistsError: pass
    directory = os.open(CONTEXT_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(directory)
        if info.st_uid != 0: raise ValueError("context directory owner differs")
        os.fchown(directory, 0, 1001); os.fchmod(directory, 0o750)
        fd = os.open(context["role"] + ".json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o640, dir_fd=directory)
        try:
            raw = canonical(context)
            if len(raw) > 262144 or os.write(fd, raw) != len(raw): raise ValueError("context receipt incomplete")
            os.fchown(fd, 0, 1001); os.fchmod(fd, 0o640); os.fsync(fd)
        finally: os.close(fd)
        os.fsync(directory)
    finally: os.close(directory)


def redeem_root_preparation(custody, connection, peer, *, authority=None):
    if authority is None:
        from . import launch_plan_issuer as authority
    issuer, policy = authority._policy(); roster = root_roster(authority)
    connection.settimeout(issuer["request_timeout_seconds"])
    request, incoming = authority._receive(connection, (*peer, 0), minimum_fds=0)
    try: authority.require(not incoming, "preparation cannot submit descriptors")
    finally:
        for fd in incoming: os.close(fd)
    role = validate_request(request, roster); stamp = root_peer(authority, peer, roster, role, request["identity_sha256"])
    key = request["identity_sha256"]; row = custody._claim(key, wait=True)
    authority.require(row is not None, "original custody absent; reconcile")
    try:
        authority.require((issuer, policy) == (row["issuer"], row["raw"]) and
            authority._digest(policy) == roster.document["host_policy_sha256"], "original policy changed")
        grant, _ = authority._validate(row["request"], row["fds"], row["peer"], policy)
        authority.require(authority._host_peer(*row["peer"][:3], issuer, policy) == row["peer"], "original host changed")
        proposal = row["request"]["proposal"]
        from .private_mount_plan import ApprovedPrivateMountPlan
        plan = ApprovedPrivateMountPlan.read(authority.publication.AUTHORITY_ROOT / (key + ".json"), grant.identity)
        plan.authorize(proposal["plan"]["descriptors"], proposal["argv"])
        if not row["active"]: custody.activate(key)
        authority._validate(row["request"], row["fds"], row["peer"], policy)
        if role == "child":
            authority.require("child" not in roster.roles and authority._digest(grant.identity.to_json()) == key,
                              "child append already consumed or identity changed")
            from .child_projection import child_document, measured_stdio, publish_child
            from .metadata_provider import MetadataOps
            root_context = authority.host._read_configuration(Path(CONTEXT_ROOT) / "root.json")
            parent = authority.SecurityGrant.from_dict(row["request"]["parent_grant"])
            extension = child_document(roster, grant=grant, parent_grant=parent, request=row["request"], peer=row["peer"],
                root_context=root_context, root_phase=MetadataOps(None).sdk_phase("root"), stdio=measured_stdio(peer[0], authority))
            # Durable one-shot data append under the SAME root authority. A
            # subsequent failure leaves it consumed/unknown, never replaceable.
            publish_child(extension)
            roster = roster.with_child(canonical(extension), authority.InvocationIdentity, root_context=root_context)
        context = capture_context(roster, role, row["request"], row["peer"])
        context["cgroup_identity"] = [stamp[4], stamp[5]]
        # Preserve the original custody's canonical binding activation and
        # all its deadline checks; the root path is not an alternate issuer.
        authority._validate(row["request"], row["fds"], row["peer"], policy)
        authority.require(plan.sha256 == request["plan_sha256"] == context["plan_sha256"], "original plan changed")
        record = derive_record(roster, role, identity=grant.identity.to_json(), plan=proposal["plan"],
            argv=proposal["argv"], grant_hash=grant.hash, expires_at=grant.expires_at, approved_profile=proposal["approved_profile"])
        authority.require(root_roster(authority).sha256 == roster.sha256 and root_peer(authority, peer, roster, role, key) == stamp
            and authority._policy() == (issuer, policy) and time.monotonic() < row["deadline"], "preparation context changed")
        publish_context(context)
        with custody._lock:
            authority.require(custody.pending.get(key) is row and not row["cancelled"], "custody withdrawn")
            custody.pending.pop(key)
        try:
            answer = authority.canonical_json_bytes({**request, "record": record,
                "context_sha256": digest(context), "descriptor_count": len(row["fds"])})
            connection.settimeout(max(0.001, row["deadline"] - time.monotonic()))
            authority.require(connection.sendmsg([answer], [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                array.array("i", row["fds"]))]) == len(answer), "delivery uncertain; reconcile")
        finally: custody._close_row(row)
    finally: custody._release(key, row)
