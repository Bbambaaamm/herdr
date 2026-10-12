"""Automatic issuance by the existing root plan authority, for trusted hosts.

Only root-approved host entrypoints in non-delegated service cgroups may ask.
UID equality, a proposal, a signature supplied by a worker, or a digest is not
authorization. The host keeps its existing admission/parent/fence authority.
"""
from __future__ import annotations

import array
import ctypes
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import struct
import time

from . import host_configuration as host, launch_plan_publication as publication
from .launch_plan_handoff import MAX_PROPOSAL, VERSION as PROPOSAL_VERSION
from .policy_launch import (BUNDLE_TARGET, CODE_TARGET, _open_relative,
                           _verify_root_owned_ancestry, process_start_ticks)
from .security import InvocationIdentity, SecurityError, SecurityGrant, canonical_json_bytes
from .private_profile_namespace import PrivateProfileError

CONFIGURATION = Path("/etc/herdr/launch-plan-issuer.json")
SOCKET_PATH = Path("/run/herdr-launch-authority/issuer.sock")
VERSION = "herdr-automatic-launch-plan-1"
MAX_REQUEST = 196608
MAX_FDS = 96
HOST_ENTRYPOINT = "agent-stack/bin/agent-herdr-host-entrypoint"


def require(ok, reason):
    if not ok:
        raise SecurityError(reason)


def protect_host_process():
    """Protect the host's channel and memory against same-UID ptrace/proc theft."""
    libc = ctypes.CDLL(None, use_errno=True)
    require(libc.prctl(4, 0, 0, 0, 0) == 0 and libc.prctl(3, 0, 0, 0, 0) == 0,
            "non-dumpable trusted host required")


def _digest(value):
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_uid, info.st_mode, info.st_nlink,
            info.st_size, info.st_ctime_ns, info.st_mtime_ns)


def _read(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 < before.st_size <= limit, "bounded exclusive record required")
        raw = os.read(fd, limit + 1)
        require(len(raw) == before.st_size and not os.read(fd, 1)
                and _stamp(before) == _stamp(os.fstat(fd)) == _stamp(Path(path).lstat()),
                "record changed during read")
        return raw, before
    finally:
        os.close(fd)


def _policy():
    issuer = host._read_configuration(CONFIGURATION)
    require(set(issuer) == {"schema_version", "host_policy_sha256", "host_cgroups",
                            "entrypoints", "request_timeout_seconds"}
            and issuer["schema_version"] == VERSION, "closed automatic issuer policy required")
    require(type(issuer["request_timeout_seconds"]) is int
            and 1 <= issuer["request_timeout_seconds"] <= 60, "finite issuer deadline required")
    groups = issuer["host_cgroups"]
    require(isinstance(groups, list) and 1 <= len(groups) <= 8 and len(set(groups)) == len(groups)
            and all(isinstance(x, str) and re.fullmatch(r"/system\.slice/[A-Za-z0-9_.@:-]+\.service", x)
                    for x in groups), "exact non-delegated host service cgroups required")
    raw = host._read_configuration(host.HOST_POLICY_CONFIG)
    require(_digest(raw) == issuer["host_policy_sha256"] and raw.get("schema_version") == 2
            and type(raw.get("host_uid")) is int and raw["host_uid"] > 0,
            "current private host policy pin required")
    handoff = raw["private_launch"].get("plan_handoff", {})
    require(handoff.get("automatic_issuer") is True, "automatic issuance is not enabled")
    entries = issuer["entrypoints"]
    require(isinstance(entries, list) and 1 <= len(entries) <= 16 and len(set(entries)) == len(entries)
            and all(isinstance(x, str) and x in raw["code"]["files"]
                    and x.startswith(("agent-stack/bin/", "scripts/")) for x in entries)
            and HOST_ENTRYPOINT in raw["code"]["files"], "approved host entrypoint inventory required")
    return issuer, raw


def _proc_bytes(pid, name, limit=262144):
    with open(f"/proc/{pid}/{name}", "rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "peer process metadata exceeds bound")
    return raw


def _peer(connection, issuer, raw):
    pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    require(uid == raw["host_uid"] and pid > 0, "issuer caller is not the configured host")
    ticks = process_start_ticks(pid)
    require(Path(f"/proc/{pid}").stat().st_uid == 0, "issuer caller must be non-dumpable")
    for name in ("mnt", "pid", "user", "cgroup", "net", "time"):
        require(os.readlink(f"/proc/{pid}/ns/{name}") == os.readlink(f"/proc/self/ns/{name}"),
                "sandbox callers cannot issue host plans")
    groups = _proc_bytes(pid, "cgroup", 8192).decode().splitlines()
    require(len(groups) == 1 and groups[0].startswith("0::")
            and groups[0][3:] in issuer["host_cgroups"], "caller is outside the approved host service")
    group = Path("/sys/fs/cgroup") / groups[0][3:].lstrip("/")
    _verify_root_owned_ancestry(group)
    for control in ("cgroup.procs", "cgroup.threads"):
        info = (group / control).lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022,
                "host service migration is delegated")
    from .host_bootstrap import PYTHON_TARGET, PYTHON_EXECUTABLE
    python = next(x for x in raw["runtime"] if x["target"] == str(PYTHON_TARGET))
    executable = Path(python["source"]) / PYTHON_EXECUTABLE
    code = Path(raw["code"]["source"])
    argv = _proc_bytes(pid, "cmdline", 32768).rstrip(b"\0").decode().split("\0")
    require(len(argv) >= 5 and argv[:4] == [str(executable), "-I", "-B", str(code / HOST_ENTRYPOINT)]
            and argv[4] in issuer["entrypoints"], "exact approved host launcher required")
    actual, expected = Path(f"/proc/{pid}/exe").stat(), executable.stat()
    require((actual.st_dev, actual.st_ino) == (expected.st_dev, expected.st_ino),
            "host interpreter inode differs")
    from .launch_environment import process_environment, require_clean_environment
    env = process_environment(pid)
    require_clean_environment(env)
    require(not any(key.startswith("PYTHON") for key in env), "host Python environment is not closed")
    require(process_start_ticks(pid) == ticks, "issuer peer process changed")
    return pid, uid, gid, ticks


def _receive(connection, peer):
    descriptors = []
    try:
        body, ancillary, flags, _ = connection.recvmsg(
            MAX_REQUEST + 1, socket.CMSG_SPACE(MAX_FDS * array.array("i").itemsize) + socket.CMSG_SPACE(12),
            getattr(socket, "MSG_CMSG_CLOEXEC", 0))
        # Collect every received FD before validating unrelated ancillary data,
        # so malformed metadata cannot leak later SCM_RIGHTS descriptors.
        for level, kind, data in ancillary:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                values = array.array("i")
                values.frombytes(data[:len(data) - len(data) % values.itemsize])
                descriptors.extend(values)
        credentials = []
        for level, kind, data in ancillary:
            require(level == socket.SOL_SOCKET, "unexpected issuer ancillary level")
            if kind == socket.SCM_RIGHTS:
                require(len(data) % array.array("i").itemsize == 0, "malformed issuer descriptors")
            elif kind == socket.SCM_CREDENTIALS:
                require(len(data) == 12, "malformed issuer credentials")
                credentials.append(struct.unpack("3i", data))
            else:
                raise SecurityError("unexpected issuer ancillary message")
        require(not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC) and 0 < len(body) <= MAX_REQUEST
                and 1 <= len(descriptors) <= MAX_FDS and credentials == [peer[:3]],
                "bounded authenticated issuer packet required")
        value = json.loads(body)
        require(isinstance(value, dict) and canonical_json_bytes(value) == body,
                "canonical issuer request required")
        return value, descriptors
    except BaseException:
        for fd in descriptors:
            os.close(fd)
        raise


def _grant(request, raw, profile):
    grant = SecurityGrant.from_dict(request["grant"])
    require(grant.is_active(), "current host grant required")
    ceiling = SecurityGrant.from_dict(raw["templates"].get(grant.identity.consumer, {}))
    require(ceiling.is_active(), "current consumer ceiling required")
    comparison = replace(grant, parent_grant_hash=ceiling.hash,
                         identity=replace(grant.identity, parent_agent_id=ceiling.identity.agent_id,
                                          parent_task_id=ceiling.identity.task_id),
                         tool_rules=tuple(replace(rule, result_slot=None) if rule.tool == "herdr_submit_result"
                                          else rule for rule in grant.tool_rules))
    comparison.require_logical_subset_of(ceiling)
    require(not grant.approvals and (datetime.fromisoformat(grant.expires_at) -
            datetime.fromisoformat(grant.issued_at)).total_seconds() <= raw["grant_ttl_seconds"],
            "host grant exceeds issuance policy")
    parent = request["parent_grant"]
    if parent is None:
        require(grant.parent_grant_hash is None, "root grant has delegated parent authority")
    else:
        parent = SecurityGrant.from_dict(parent)
        require(parent.is_active(), "active delegated parent required")
        grant.require_logical_subset_of(parent)
    approved, expiry, floor = host._private_profile(raw["private_launch"])
    require(profile == approved.identity and expiry >= datetime.now(UTC) + timedelta(
            seconds=max(floor, raw["grant_ttl_seconds"] + 60)), "current profile approval required")
    return grant


def _argv(plan, argv, workspace, profile):
    """Closed native pane grammar; no literal host writes or arbitrary command."""
    publication._shape(plan, argv, InvocationIdentity.from_dict(plan["identity"]))
    end = argv.index("--")
    require(argv[end + 1:] == ["/bin/bash", "--noprofile", "--norc", "-i"], "native pane command required")
    arities = {"--ro-bind": 2, "--bind-fd": 2, "--ro-bind-fd": 2, "--ro-bind-data": 2,
               "--tmpfs": 1, "--dev": 1, "--proc": 1, "--dir": 1, "--chdir": 1,
               "--remount-ro": 1, "--setenv": 2, "--unsetenv": 1,
               "--unshare-pid": 0, "--unshare-net": 0, "--die-with-parent": 0}
    public = {"HOME": "/home/agentops", "PATH": "/run/herdr/policy-code/agent-stack/policy-bin:/usr/bin:/bin",
              "HERDR_DURABLE_SANDBOX": "1"}
    operations, index = [], 1
    while index < end:
        op = argv[index]
        require(op in arities and index + arities[op] < end, "unsupported automatic mount operation")
        values = tuple(argv[index + 1:index + 1 + arities[op]])
        if op == "--ro-bind": require(values == ("/", "/"), "unexpected literal mount")
        if op == "--setenv": require(len(values) == 2 and public.get(values[0]) == values[1], "non-public launch environment")
        if op == "--unsetenv": require(values[0] not in public, "required public environment cannot be unset")
        if op == "--chdir": require(values == (workspace,), "launch workspace differs")
        if op in {"--dir", "--tmpfs", "--remount-ro"}: require(publication._target(values[0]), "non-canonical mount target")
        operations.append((op, values)); index += 1 + arities[op]
    required = {("--ro-bind", ("/", "/")), ("--dev", ("/dev",)), ("--proc", ("/proc",)),
                ("--unshare-pid", ()), ("--die-with-parent", ()),
                ("--chdir", (workspace,)), ("--tmpfs", ("/tmp",)),
                ("--tmpfs", ("/run",)), ("--tmpfs", ("/home/agentops",)),
                ("--tmpfs", ("/home/agentops/.config/herdr",)), ("--tmpfs", ("/opt/agent-platform",))}
    require(required <= set(operations) and operations[:3] == [
                ("--ro-bind", ("/", "/")), ("--dev", ("/dev",)), ("--unshare-pid", ())]
            and sum(op == "--ro-bind" for op, _ in operations) == 1
            and operations[-1] == ("--remount-ro", ("/home/agentops",))
            and all(op != "--dev" or values == ("/dev",) for op, values in operations)
            and all(op != "--proc" or values == ("/proc",) for op, values in operations),
            "complete native private namespace required")
    for op, values in required:
        require(operations.count((op, values)) == 1, "duplicate namespace operation")
    from .private_mount_plan import isolated_destination_anchor
    anchors = {Path("/home/agentops"), Path("/tmp"), Path("/run"),
               Path("/opt/agent-platform"), isolated_destination_anchor(workspace)}
    for entry in plan["descriptors"]:
        if entry["kind"] == "reserved-result": anchors.add(isolated_destination_anchor(entry["target"]))
    for op, values in operations:
        if op in {"--dir", "--tmpfs", "--remount-ro"}:
            require(any(Path(values[0]) == root or root in Path(values[0]).parents for root in anchors),
                    "namespace construction outside private anchors")
    for index, (op, values) in enumerate(operations):
        if op not in {"--bind-fd", "--ro-bind-fd", "--ro-bind-data"}: continue
        target = Path(values[1])
        require(not any(later in {"--tmpfs", "--dev", "--proc", "--ro-bind"}
                        and (Path(args[-1]) == target or Path(args[-1]) in target.parents)
                        for later, args in operations[index + 1:]), "approved FD hidden by a later mount")
    require(all(sum(op == "--setenv" and values == (key, value) for op, values in operations) == 1
                for key, value in public.items()), "complete public environment required")
    return {int(values[0]): op for op, values in operations if op.endswith("-fd") or op == "--ro-bind-data"}


def _physical(plan, argv, grant, profile, fds, raw):
    require(len(fds) == len(plan["descriptors"]), "complete held FD inventory required")
    operations = _argv(plan, argv, grant.workspace_root, profile)
    from .owned_write_mounts import _mount_id
    workspace_fds = [fd for entry, fd in zip(plan["descriptors"], fds)
                     if entry["target"] == grant.workspace_root and entry["kind"] == "directory"]
    require(len(workspace_fds) == 1, "one exact workspace source required")
    workspace_info = os.fstat(workspace_fds[0])
    workspace_mount = _mount_id(workspace_fds[0])
    roots = []
    try:
        for definition in (raw["code"], *raw["runtime"]):
            roots.append(host._tree(definition, immutable=True).freeze(Path(raw["storage"]), ()))
        known = {str(tree.target): tree for tree in roots}
        seen = set(); result_count = 0; workspace_count = 0; special = set()
        profile_root = f"/home/agentops/.hermes/profiles/{profile['name']}/"
        profiles = set()
        for entry, fd in zip(plan["descriptors"], fds):
            info = os.fstat(fd); target = entry["target"]; kind = entry["kind"]
            require((info.st_dev, info.st_ino) == (entry["device"], entry["inode"]), "received FD source differs")
            original = Path(entry["source"]).stat()
            require((original.st_dev, original.st_ino) == (info.st_dev, info.st_ino),
                    "caller FD number does not name the received source")
            require((stat.S_ISDIR(info.st_mode) if kind == "directory" else stat.S_ISSOCK(info.st_mode)
                     if kind == "socket" else stat.S_ISREG(info.st_mode)), "received FD type differs")
            if target in known:
                tree = known[target]
                require((info.st_dev, info.st_ino) == (tree.device, tree.inode)
                        and operations[entry["fd"]] == "--ro-bind-fd", "immutable source differs from root policy")
                seen.add(target)
            elif kind == "sealed-profile-data":
                require(target.startswith(profile_root), "foreign sealed profile target")
                name = target[len(profile_root):]
                from .private_profile_namespace import SealedProfileInput
                require(profile["files"].get(name) == entry["sha256"]
                        and operations[entry["fd"]] == "--ro-bind-data", "unapproved profile input")
                SealedProfileInput(name, fd, entry["size"], entry["sha256"]).verify()
                profiles.add(name)
            elif kind == "reserved-result":
                require(operations[entry["fd"]] == "--bind-fd" and info.st_uid == raw["host_uid"]
                        and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600 and info.st_size == 0,
                        "empty private result required")
                binding = entry["reservation"]
                readable = os.open(f"/proc/self/fd/{fd}", os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
                try:
                    require(os.getxattr(readable, "user.herdr.result_reservation") == canonical_json_bytes(binding)
                            and "user.herdr.result_submission" not in os.listxattr(readable), "result reservation differs")
                finally: os.close(readable)
                from .private_mount_plan import coherent_result_fd
                current = coherent_result_fd(target, (info.st_dev, info.st_ino))
                from .owned_write_mounts import _mount_id
                try: require(_mount_id(current) == _mount_id(fd), "result mount attachment differs")
                finally: os.close(current)
                rules = [x for x in grant.tool_rules if x.tool == "herdr_submit_result"]
                require(len(rules) == 1 and rules[0].result_slot is not None
                        and rules[0].result_slot.to_json() == {k: v for k, v in binding.items() if k != "schema_version"},
                        "result is not bound to the admitted grant")
                result_count += 1
            elif kind == "directory" and target == "/run/herdr-bootstrap":
                require(info.st_uid == raw["host_uid"] and operations[entry["fd"]] == "--ro-bind-fd",
                        "bootstrap transport differs")
                from .host_bootstrap import SHIM_SOURCE, STAGE1_SOURCE
                require(set(os.listdir(fd)) == {"hermes", "agent-hermes-policy-stage1", "immutable-trees.json"},
                        "bootstrap transport inventory differs")
                for name, source_name in (("hermes", SHIM_SOURCE), ("agent-hermes-policy-stage1", STAGE1_SOURCE)):
                    child = _open_relative(fd, name)
                    try:
                        value = os.fstat(child)
                        require(value.st_size <= 4194304 and hashlib.sha256(os.pread(child, value.st_size, 0)).hexdigest()
                                == dict(known[str(CODE_TARGET)].files)[source_name], "bootstrap transport bytes differ")
                    finally: os.close(child)
                child = _open_relative(fd, "immutable-trees.json")
                try:
                    require(os.fstat(child).st_size <= 65536, "bootstrap proof exceeds bound")
                    proof = json.loads(os.pread(child, 65537, 0))
                    require(proof == {"schema_version": "herdr-policy-bootstrap-1",
                            "authority": "herdr-host-frozen-tree", "identity": grant.identity.to_json(),
                            "trees": {target: {"device": tree.device, "inode": tree.inode,
                                "source_digest": tree.source_digest, "snapshot_kind": "host-frozen-copy"}
                                for target, tree in known.items()}}, "bootstrap transport proof differs")
                finally: os.close(child)
                special.add(target)
            elif kind == "socket" and target == "/run/herdr-policy/bootstrap-authority.sock":
                require(info.st_uid == raw["host_uid"] and operations[entry["fd"]] == "--ro-bind-fd",
                        "bootstrap channel differs")
                special.add(target)
            elif target == str(BUNDLE_TARGET):
                require(kind == "file" and info.st_uid == raw["host_uid"] and info.st_nlink == 1
                        and stat.S_IMODE(info.st_mode) == 0o600 and info.st_size == 0
                        and operations[entry["fd"]] == "--ro-bind-fd", "unsealed bundle source differs")
                special.add(target)
            elif kind == "file" and target in {"/home/agentops/.local/bin/herdr", "/home/agentops/.local/bin/hermes"}:
                original = _open_relative(known[str(CODE_TARGET)].fd, "agent-stack/policy-bin/herdr")
                try:
                    source = os.fstat(original)
                    require((info.st_dev, info.st_ino) == (source.st_dev, source.st_ino)
                            and operations[entry["fd"]] == "--ro-bind-fd", "CLI source differs")
                finally: os.close(original)
                special.add(target)
            else:
                require(kind in {"directory", "file"} and info.st_uid == raw["host_uid"]
                        and (target == grant.workspace_root or Path(grant.workspace_root) in Path(target).parents),
                        "unapproved writable source")
                from .private_mount_plan import coherent_result_fd, isolated_destination_anchor
                isolated_destination_anchor(target)
                relative = Path(target).relative_to(grant.workspace_root)
                require(all(name not in {".git", ".herdr"} and not name.startswith(".herdr-")
                            for name in relative.parts), "owned control path denied")
                if target != grant.workspace_root:
                    require(not info.st_mode & 0o022 and info.st_dev == workspace_info.st_dev
                            and _mount_id(fd) == workspace_mount, "owned write source is untrusted or crosses a mount")
                if kind == "file":
                    require(info.st_nlink == 1 and operations[entry["fd"]] == "--bind-fd",
                            "exclusive owned write file required")
                named = Path(target).stat()
                require((named.st_dev, named.st_ino) == (info.st_dev, info.st_ino)
                        and Path(target).resolve(strict=True) == Path(target), "workspace attachment differs")
                from .owned_write_mounts import _mount_id
                current = (coherent_result_fd(target, (info.st_dev, info.st_ino)) if kind == "file" else
                           os.open(target, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC))
                try: require(_mount_id(current) == _mount_id(fd), "workspace mount attachment differs")
                finally: os.close(current)
                if target == grant.workspace_root: workspace_count += 1
                if operations[entry["fd"]] == "--bind-fd":
                    require(any(rule.tool in {"write_file", "patch"} and any(
                        Path(target) == Path(root) or Path(root) in Path(target).parents for root in rule.allowed_roots)
                        for rule in grant.tool_rules), "write mount exceeds host grant")
        require(seen == set(known) and profiles == set(profile["files"]) and result_count == 1
                and workspace_count == 1 and special == {str(BUNDLE_TARGET), "/run/herdr-bootstrap",
                    "/run/herdr-policy/bootstrap-authority.sock", "/home/agentops/.local/bin/herdr"},
                "incomplete approved launch sources")
    finally:
        for tree in roots: tree.close()


def _validate(request, fds, peer, raw):
    require(set(request) == {"schema_version", "proposal", "grant", "parent_grant", "policy_sha256",
                             "deadline_monotonic_ns"}
            and request["schema_version"] == VERSION and request["policy_sha256"] == _digest(raw),
            "closed issuer request with current policy required")
    proposal = request["proposal"]
    require(isinstance(proposal, dict) and set(proposal) == {"schema_version", "plan", "argv", "grant_sha256",
            "approved_profile", "owner_pid", "owner_start_ticks", "valid_until"}
            and proposal["schema_version"] == PROPOSAL_VERSION
            and proposal["owner_pid"] == peer[0] and proposal["owner_start_ticks"] == peer[3],
            "live caller-bound proposal required")
    grant = _grant(request, raw, proposal["approved_profile"])
    require(proposal["grant_sha256"] == grant.hash and proposal["valid_until"] == grant.expires_at
            and proposal["plan"]["identity"] == grant.identity.to_json(), "proposal grant binding differs")
    name = _digest(grant.identity.to_json()) + ".json"
    path = Path(raw["private_launch"]["plan_handoff"]["proposal_directory"]) / name
    body, info = _read(path, MAX_PROPOSAL)
    require(info.st_uid == peer[1] and stat.S_IMODE(info.st_mode) == 0o400
            and body == canonical_json_bytes(proposal), "proposal evidence differs")
    require(all(entry["source"] == f"/proc/{peer[0]}/fd/{entry['fd']}"
                for entry in proposal["plan"]["descriptors"]), "foreign process FD source")
    _physical(proposal["plan"], proposal["argv"], grant, proposal["approved_profile"], fds, raw)
    return grant, name


def issue_request(connection):
    """One bounded root operation. No admission queue, provider or retry exists."""
    require(os.geteuid() == 0, "automatic issuance requires the root plan authority")
    started = time.monotonic()
    issuer, raw = _policy()
    peer = _peer(connection, issuer, raw)
    maximum_deadline = started + issuer["request_timeout_seconds"]
    require(time.monotonic() < maximum_deadline, "issuer setup deadline expired")
    connection.settimeout(maximum_deadline - time.monotonic())
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    request, fds = _receive(connection, peer)
    try:
        requested_deadline = request.get("deadline_monotonic_ns")
        require(type(requested_deadline) is int and 0 < requested_deadline < 1 << 63,
                "bounded caller deadline required")
        deadline = requested_deadline / 1_000_000_000
        require(started < deadline <= maximum_deadline and time.monotonic() < deadline,
                "issuer caller deadline expired or exceeds its bound")
        grant, name = _validate(request, fds, peer, raw)
        def live_authority():
            require(_policy() == (issuer, raw) and _peer(connection, issuer, raw) == peer,
                    "issuer authority changed during source verification")
            # Check the caller's clock after expensive policy/peer reads.
            require(time.monotonic() < deadline, "issuer caller deadline expired")
        def current():
            live_authority()
            _validate(request, fds, peer, raw)
            live_authority()
        current()
        now = datetime.now(UTC)
        ticket = {"schema_version": publication.TICKET_VERSION, "plan": request["proposal"]["plan"],
                  "argv": request["proposal"]["argv"], "not_before": now.isoformat(),
                  "expires_at": min(now + timedelta(seconds=issuer["request_timeout_seconds"]),
                                    datetime.fromisoformat(grant.expires_at)).isoformat()}
        _verify_root_owned_ancestry(publication.APPROVAL_ROOT)
        from .runtime_publication import _rename_without_replacement
        parent = os.open(publication.APPROVAL_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            import uuid
            stage = ".automatic-" + uuid.uuid4().hex
            fd = os.open(stage, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=parent)
            with os.fdopen(fd, "wb") as stream:
                stream.write(canonical_json_bytes(ticket)); stream.flush()
                os.fchmod(stream.fileno(), 0o400); publication._root_owner(os.fstat(stream.fileno()))
                os.fsync(stream.fileno())
            current()
            _rename_without_replacement(parent, stage, name); os.fsync(parent)
        finally: os.close(parent)
        result = publication._publish_approved_launch_plan(publication.APPROVAL_ROOT / name,
                                                          publish=True, before_publish=current)
        return {"schema_version": VERSION, "identity_sha256": name[:-5],
                "plan_sha256": result["plan_sha256"], "published": True}
    finally:
        for fd in fds: os.close(fd)


class AutomaticLaunchPlanClient:
    def __init__(self, policy_sha256, timeout_seconds):
        require(isinstance(policy_sha256, str) and re.fullmatch(r"[a-f0-9]{64}", policy_sha256)
                and type(timeout_seconds) is int and 1 <= timeout_seconds <= 60, "bounded automatic issuer client required")
        self.policy_sha256, self.timeout_seconds = policy_sha256, timeout_seconds

    def issue(self, launch, published, *, deadline=None):
        now = time.monotonic()
        if deadline is None:
            deadline = now + self.timeout_seconds
        require(type(deadline) in (int, float) and now < deadline <= now + self.timeout_seconds,
                "automatic issuance deadline expired or exceeds its bound")
        def remaining():
            value = deadline - time.monotonic()
            require(value > 0, "automatic issuance deadline expired")
            return value
        launch.private_plan_handoff._verify_proposal(published)
        proposal = json.loads(published[1])
        request = {"schema_version": VERSION, "proposal": proposal, "grant": launch.grant.to_json(),
                   "parent_grant": launch._parent.to_json() if launch._parent is not None else None,
                   "policy_sha256": self.policy_sha256,
                   "deadline_monotonic_ns": int(deadline * 1_000_000_000)}
        body = canonical_json_bytes(request)
        require(len(body) <= MAX_REQUEST, "issuer request exceeds bound")
        with _connect_issuer(remaining()) as connection:
            connection.settimeout(remaining())
            rights = array.array("i", [entry["fd"] for entry in proposal["plan"]["descriptors"]])
            require(connection.sendmsg([body], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, rights)]) == len(body),
                    "issuer packet delivery incomplete")
            connection.settimeout(remaining())
            answer = connection.recv(4097)
            require(0 < len(answer) <= 4096, "bounded issuer response required")
            result = json.loads(answer)
            require(result == {"schema_version": VERSION, "identity_sha256": _digest(launch.identity.to_json()),
                               "plan_sha256": _digest(proposal["plan"]), "published": True},
                    "automatic launch-plan issuance denied")
        launch.private_plan_handoff._verify_proposal(published)


def _connect_issuer(timeout_seconds):
    _verify_root_owned_ancestry(SOCKET_PATH.parent)
    info = SOCKET_PATH.lstat()
    require(stat.S_ISSOCK(info.st_mode) and info.st_uid == 0, "root issuer endpoint required")
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        connection.settimeout(timeout_seconds)
        connection.connect(str(SOCKET_PATH))
        require(struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1] == 0
                and _stamp(SOCKET_PATH.lstat()) == _stamp(info), "issuer endpoint changed")
        return connection
    except BaseException:
        connection.close()
        raise


def serve():
    require(os.geteuid() == 0, "automatic issuance requires root")
    _, raw = _policy()
    import sys
    from .host_bootstrap import PYTHON_TARGET, PYTHON_EXECUTABLE
    python = next(row for row in raw["runtime"] if row["target"] == str(PYTHON_TARGET))
    require(sys.flags.isolated and sys.dont_write_bytecode
            and Path(sys.executable) == Path(python["source"]) / PYTHON_EXECUTABLE
            and Path(__file__).resolve(strict=True) == Path(raw["code"]["source"]) / "herdr/launch_plan_issuer.py",
            "immutable isolated issuer entrypoint required")
    for definition in (raw["code"], *raw["runtime"]):
        tree = host._tree(definition, immutable=True).freeze(Path(raw["storage"]), ())
        tree.close()
    _verify_root_owned_ancestry(SOCKET_PATH.parent)
    require(not os.path.lexists(SOCKET_PATH), "issuer socket already exists; reconcile explicitly")
    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        listener.bind(str(SOCKET_PATH)); os.chmod(SOCKET_PATH, 0o666)
        listener.listen(8)
        while True:
            connection, _ = listener.accept()
            with connection:
                try:
                    result = issue_request(connection)
                except (SecurityError, PrivateProfileError, OSError, ValueError, KeyError, TypeError, StopIteration):
                    result = {"schema_version": VERSION, "error": "launch-plan issuance denied"}
                try: connection.send(canonical_json_bytes(result))
                except OSError: pass
