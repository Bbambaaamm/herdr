"""Finite UID 1001 control transport for the single offline case.

This module is source only.  The host policy must separately whitelist this
exact entrypoint, its unit, and the canonical offline work definition before
it can be installed.  Import and construction have no host effects.
"""
from __future__ import annotations

import os
import hashlib
import socket
import stat
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve(strict=True).parents[1]))

from offline_case.admission import (HOST_POLICY, HOST_SCRIPT, HOST_UID, MAX_PACKET,
                                    OPERATIONS, SELECTOR, SOCKET, _process_read,
                                    _read_exact)
from offline_case.case import NONCE, Denied, canonical, parse, pinned_bytes, require, sha
from offline_case.case import HOST_PROFILE, OPERATOR_PROFILE

ROOT = Path("/opt/agent-platform/herdr-offline-03414499dd0d1986")
CASE_UNIT = "herdr-offline-03414499dd0d1986.service"
OPERATOR_UNIT = "herdr-offline-operator-03414499dd0d1986.service"
CLEANUP_UNIT = "herdr-offline-cleanup-03414499dd0d1986.service"
OPERATOR_LABEL = OPERATOR_PROFILE + " (enforce)"


class RejectedRequest(Denied):
    """A pre-dispatch protocol rejection cannot have changed canonical state."""
DRIVER_COMMAND = (b"/usr/bin/python3.14", b"-I", b"-B", b"-c",
    b'import sys; sys.path.insert(0,"/opt/agent-platform/herdr-offline-03414499dd0d1986"); from offline_case.driver import main; main(["--execute"])')
CLEANUP_COMMAND = (b"/usr/bin/python3.14", b"-I", b"-B", b"-c",
    b'import sys; sys.path.insert(0,"/opt/agent-platform/herdr-offline-03414499dd0d1986"); from offline_case.driver import main; main(["--cleanup"])')


def canonical_components(task_id, run_token, *, recovery=False, api=None):
    """Construct the actual host policy, named admission, registry, and work.

    A caller must already hold the canonical claimed attempt.  This function
    does not create a root lease or a second grant issuer.
    """
    if api is None:
        from herdr.host_configuration import (HOST_POLICY_CONFIG, _read_configuration,
                                              read_canonical_parent, build_host_policy_factory)
        from herdr.admission import (AdmissionControl, AuditLog as AdmissionAuditLog,
                                     PlanBudget)
        from herdr.consumer_policies import policy_for_profile
        from herdr.runtime import (AdmissionRegistry, DEFAULT_ADMISSION_REGISTRY,
                                   DEFAULT_ADMISSION_AUDIT)
        from herdr.work_configuration import build_root_work_factory
        from herdr.security import InvocationIdentity
        from types import SimpleNamespace
        api = SimpleNamespace(HOST_POLICY_CONFIG=HOST_POLICY_CONFIG,
            _read_configuration=_read_configuration, read_canonical_parent=read_canonical_parent,
            build_host_policy_factory=build_host_policy_factory,
            AdmissionControl=AdmissionControl, AdmissionAuditLog=AdmissionAuditLog,
            PlanBudget=PlanBudget, policy_for_profile=policy_for_profile,
            AdmissionRegistry=AdmissionRegistry, DEFAULT_ADMISSION_REGISTRY=DEFAULT_ADMISSION_REGISTRY,
            DEFAULT_ADMISSION_AUDIT=DEFAULT_ADMISSION_AUDIT,
            build_root_work_factory=build_root_work_factory,
            InvocationIdentity=InvocationIdentity)
    raw = api._read_configuration(api.HOST_POLICY_CONFIG)
    require(os.geteuid() == HOST_UID and raw["host_uid"] == HOST_UID,
            "canonical host UID required")
    root = Path(raw["task_store_root"])
    task = api.read_canonical_parent(root, task_id, run_token)
    require(type(task) is dict and task.get("attempt_state") in {"dispatching", "accepted"}
            and task.get("id") == task_id and task.get("run_token") == run_token
            and type(task.get("fencing_token")) is int and task["fencing_token"] > 0,
            "current canonical root claim required")
    routing = task.get("routing") if type(task.get("routing")) is dict else {}
    coordinator = str(routing.get("selected_agent") or task.get("agent") or "quantlab-hermes")
    value = hashlib.sha256(f"{coordinator}:{task_id}:{run_token}".encode()).hexdigest()
    prefix = coordinator[:13].rstrip("-_") or "task"
    agent = f"{prefix}-t-{value[:16]}"
    require(len(agent) <= 32, "canonical agent name invalid")
    identity = api.InvocationIdentity(consumer="github:" + str(task["repo"]),
        agent_id=agent, parent_agent_id=coordinator,
        parent_task_id="coordinator:" + coordinator, task_id=task_id,
        run_token=run_token, fencing_token=task["fencing_token"])
    factory = api.build_host_policy_factory(configuration_path=api.HOST_POLICY_CONFIG)
    control = api.AdmissionControl(budget=api.PlanBudget(),
        audit_log=api.AdmissionAuditLog(api.DEFAULT_ADMISSION_AUDIT),
        consumer_policy_hook=api.policy_for_profile(task["safety_profile"]))
    registry = api.AdmissionRegistry(path=api.DEFAULT_ADMISSION_REGISTRY)
    work = api.build_root_work_factory(root, task,
        configuration_path=api.HOST_POLICY_CONFIG, recovery=recovery,
        claimed_identity=None if recovery else identity)
    require(work.budget_authority is not None and
            raw == api._read_configuration(api.HOST_POLICY_CONFIG),
            "canonical budget or policy changed")
    return {"root": root, "task": task, "identity": identity, "factory": factory,
            "admission_control": control, "admission_registry": registry,
            "work_factory": work}


def check_request(packet, selector):
    require(type(packet) is dict and set(packet) == {"schema", "operation", "case",
            "task_id", "run_token", "fencing_token", "binding", "arguments",
            "request_sha256"} and packet["schema"] == 1 and
            packet["operation"] in OPERATIONS and packet["case"] == NONCE and
            all(packet[key] == selector[key] for key in
                ("task_id", "run_token", "fencing_token")) and
            type(packet["binding"]) is dict and
            packet["binding"].get("nonce") == NONCE and
            packet["binding"].get("build_sha256") == selector["build_sha256"] and
            type(packet["arguments"]) is dict and
            packet["request_sha256"] == sha(canonical({k: v for k, v in packet.items()
                                                     if k != "request_sha256"})),
            "foreign or malformed host request")


def check_peer(connection, build):
    raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
    require(len(raw) == 12, "host client credentials unavailable")
    pid, uid, _gid = struct.unpack("3i", raw)
    require(pid > 1 and uid == 0, "root operator peer required")
    base = Path("/proc") / str(pid)
    before = _process_read(base / "stat", 8192)
    require(b") " in before and len(before.rsplit(b") ", 1)[1].split()) > 19,
            "operator start identity unavailable")
    ticks = int(before.rsplit(b") ", 1)[1].split()[19])
    label = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERSEC, 256).rstrip(b"\0")
    require(ticks > 0 and label == OPERATOR_LABEL.encode(), "untrusted operator label")
    cgroup = _process_read(base / "cgroup", 8192).decode().splitlines()
    require(cgroup in (["0::/system.slice/" + OPERATOR_UNIT],
                       ["0::/system.slice/" + CLEANUP_UNIT]),
            "operator outside exact owned unit")
    unit, command = ((OPERATOR_UNIT, DRIVER_COMMAND) if cgroup[0].endswith(OPERATOR_UNIT)
                     else (CLEANUP_UNIT, CLEANUP_COMMAND))
    command_line = _process_read(base / "cmdline", 4096)
    require(command_line.endswith(b"\0") and
            tuple(command_line.split(b"\0")[:-1]) == command,
            "operator command changed")
    from offline_case.root_effects import CONTEXT
    caller = parse(pinned_bytes(CONTEXT / ("caller-" + str(pid) + "-" + str(ticks) + ".json"),
                               root_owned=True), 4096)
    require(set(caller) == {"schema", "pid", "start_ticks", "boot_id", "label", "exe",
            "exe_sha256", "command", "cgroup", "unit_sha256", "build_sha256"} and
            caller["schema"] == "canonical-case-root-caller-1" and caller["pid"] == pid and
            caller["start_ticks"] == ticks and caller["label"] == OPERATOR_LABEL and
            caller["exe"] == "/usr/bin/python3.14" and caller["command"] == [x.decode() for x in command] and
            caller["cgroup"] == cgroup[0] and caller["build_sha256"] == sha(canonical(build)) and
            caller["boot_id"] == _process_read(Path("/proc/sys/kernel/random/boot_id"), 128).decode().strip() and
            caller["exe_sha256"] == sha(pinned_bytes(Path("/usr/bin/python3.14"), root_owned=True)) and
            caller["unit_sha256"] == build["files"]["units/" + unit],
            "exact root-owned caller projection changed")
    require(sha(pinned_bytes(ROOT / "offline_case/driver.py", root_owned=True)) ==
            build["files"]["offline_case/driver.py"] and
            sha(pinned_bytes(Path("/etc/systemd/system") / unit, root_owned=True)) ==
            build["files"]["units/" + unit],
            "operator script or unit fragment changed")
    after = _process_read(base / "stat", 8192)
    require(b") " in after and len(after.rsplit(b") ", 1)[1].split()) > 19 and
            int(after.rsplit(b") ", 1)[1].split()[19]) == ticks,
            "operator replaced during peer check")
    return pid, ticks


def exchange_one(connection, selector, dispatch, *, peer_check):
    """Authenticate a single request before invoking the canonical dispatcher."""
    connection.settimeout(5)
    try:
        first = peer_check(connection)
        size = struct.unpack("!I", _read_exact(connection, 4))[0]
        packet = parse(_read_exact(connection, size), MAX_PACKET)
        check_request(packet, selector)
        require(peer_check(connection) == first, "operator changed during request")
    except (Denied, OSError, ValueError, UnicodeError, struct.error) as exc:
        raise RejectedRequest("unauthenticated or malformed host request") from exc
    try:
        value = dispatch(packet)
    except Denied as exc:
        value = {"denied": str(exc)[:256]}
    answer = canonical({"schema": 1, "request_sha256": packet["request_sha256"],
                        "value": value})
    require(len(answer) <= MAX_PACKET, "host reply oversized")
    try:
        connection.sendall(struct.pack("!I", len(answer)) + answer)
    except OSError:
        # Delivery is uncertain. The original request remains consumed by its
        # canonical fence; a later request may only reconcile or retire it.
        return


def serve(selector, build, dispatch, *, socket_factory=socket.socket, limit_seconds=1800):
    """One request per connection, finite lifetime, no unattended daemon."""
    require(os.geteuid() == HOST_UID and 0 < limit_seconds <= 1800,
            "exact finite host service required")
    require(not os.path.lexists(SOCKET), "preexisting host socket")
    listener = socket_factory(socket.AF_UNIX, socket.SOCK_STREAM | socket.SOCK_CLOEXEC)
    deadline = time.monotonic() + limit_seconds
    owned_socket = None
    try:
        listener.bind(str(SOCKET))
        info = os.stat(SOCKET, follow_symlinks=False)
        require(stat.S_ISSOCK(info.st_mode) and info.st_uid == HOST_UID,
                "host socket identity unavailable")
        owned_socket = (info.st_dev, info.st_ino)
        os.chmod(SOCKET, 0o600)
        listener.listen(2)
        while time.monotonic() < deadline:
            listener.settimeout(min(5, max(0.01, deadline - time.monotonic())))
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            with connection:
                try:
                    exchange_one(connection, selector, dispatch,
                                 peer_check=lambda conn: check_peer(conn, build))
                except RejectedRequest:
                    continue
        # A host process has a finite lifetime and is never restarted here.
        # Independent root cleanup uses historical metadata after host loss.
        raise RuntimeError("host control lifetime ended before owned retirement")
    finally:
        listener.close()
        if owned_socket is not None:
            info = os.stat(SOCKET, follow_symlinks=False)
            require(stat.S_ISSOCK(info.st_mode) and info.st_uid == HOST_UID and
                    (info.st_dev, info.st_ino) == owned_socket,
                    "host socket replaced during shutdown")
            os.unlink(SOCKET)


def main():
    require(sys.argv == [str(HOST_SCRIPT)] and os.geteuid() == HOST_UID,
            "exact isolated host entry required")
    from offline_case.admission import NativeAdmission
    from offline_case.case import validate_build
    build = parse(pinned_bytes(ROOT / "integration-manifest.json", root_owned=True), 262144)
    validate_build(build, ROOT, baseline=ROOT / "accepted-source", root_owned=True, installed=True)
    selector = NativeAdmission.from_configuration(build=build).selector
    require(_process_read(Path("/proc/self/attr/current"), 256).strip() ==
            (HOST_PROFILE + " (enforce)").encode(), "host profile not enforced")
    require(sha(pinned_bytes(Path("/etc/herdr/host-profile.apparmor"), root_owned=True)) ==
            selector["host_profile_source_sha256"], "host profile source changed")
    from offline_case.native import LinuxEffects
    require(LinuxEffects().loaded_profile_sha256(HOST_PROFILE) ==
            selector["host_compiled_sha256"], "host loaded profile changed")
    require(sha(pinned_bytes(HOST_SCRIPT, root_owned=True)) ==
            selector["host_script_sha256"], "host script changed")
    raw_policy = pinned_bytes(HOST_POLICY, maximum=4_194_304, root_owned=True)
    require(sha(raw_policy) == selector["host_policy_sha256"],
            "canonical host policy changed")
    policy = parse(raw_policy, 4_194_304)
    code = policy.get("code")
    require(type(code) is dict and set(code) == {"source", "target", "files",
            "executable_files", "max_bytes", "max_file_bytes"} and
            type(code["files"]) is dict and 1 <= len(code["files"]) <= 4096 and
            type(code["max_bytes"]) is int and 0 < code["max_bytes"] <= 64_000_000 and
            type(code["max_file_bytes"]) is int and 0 < code["max_file_bytes"] <= 16_777_216,
            "bounded canonical source inventory required")
    source = Path(code["source"])
    require(source.is_absolute() and ".." not in source.parts and
            source.resolve(strict=True) == source and
            "herdr/offline_case_host.py" in code["files"],
            "complete canonical host source required")
    total = 0
    for name, digest in code["files"].items():
        require(type(name) is str and name and not name.startswith("/") and
                all(part not in ("", ".", "..") for part in name.split("/")) and
                type(digest) is str and len(digest) == 64,
                "canonical source member invalid")
        member = pinned_bytes(source / name, maximum=code["max_file_bytes"],
                              root_owned=True)
        total += len(member)
        require(total <= code["max_bytes"] and sha(member) == digest,
                "canonical source member changed")
    sys.path.insert(0, str(source))
    sys.path.insert(0, str(source / "agent-stack/bin"))
    # A canonical dispatcher must be included in the immutable host source
    # composition.  Loading an arbitrary plugin here would mint a new trust
    # boundary, so an absent publisher entry denies before opening the socket.
    from herdr.offline_case_host import dispatch
    serve(selector, build, dispatch)


if __name__ == "__main__":
    main()
