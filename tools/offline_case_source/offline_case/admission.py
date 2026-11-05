"""Fixed, authenticated client of the existing UID 1001 Herdr host boundary.

The selector describes an already published host endpoint.  It grants nothing:
the host must independently check its canonical task, policy, budget and fence
for every operation.  Construction and import perform no host operation.
"""
from __future__ import annotations

import os
import socket
import struct
from pathlib import Path

from .case import CASE, NONCE, HOST_PROFILE, Denied, canonical, parse, pinned_bytes, require, sha

SELECTOR = Path("/etc/herdr/offline-case-host.json")
HOST_POLICY = Path("/etc/herdr/host-policy.json")
SOCKET = Path("/run/herdr-offline-host-03414499dd0d1986/control.sock")
HOST_UNIT = "herdr-offline-host-03414499dd0d1986.service"
HOST_SCRIPT = Path("/opt/agent-platform/herdr-offline-03414499dd0d1986/offline_case/host_service.py")
HOST_ENTRY = Path("/opt/agent-platform/herdr-offline-03414499dd0d1986/composed-core/agent-stack/bin/agent-herdr-host-entrypoint")
HOST_TARGET = "agent-stack/bin/offline-case-host-entry"
HOST_UID = 1001
MAX_PACKET = 16384
OPERATIONS = frozenset({"admit", "prepare", "claim_unit", "bind_cgroup", "run",
                        "fence", "fenced", "started", "cgroup_identity",
                        "observe_all", "retire", "retired"})


def _read_exact(connection, count):
    require(0 <= count <= MAX_PACKET, "bounded host response required")
    result = bytearray()
    while len(result) != count:
        part = connection.recv(count - len(result))
        require(bool(part), "uncertain host response")
        result.extend(part)
    return bytes(result)


def _process_read(path, maximum):
    """Read virtual proc files, whose stat size is usually zero."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        pieces = bytearray()
        while len(pieces) <= maximum:
            part = os.read(fd, min(4096, maximum + 1 - len(pieces)))
            if not part:
                break
            pieces.extend(part)
        require(0 < len(pieces) <= maximum, "host process observation unavailable")
        return bytes(pieces)
    finally:
        os.close(fd)


class UnixHostTransport:
    """One finite request per connection with a kernel bound server identity."""

    def __init__(self, selector):
        self.selector = selector

    def _peer(self, connection):
        raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        require(len(raw) == 12, "host peer credentials unavailable")
        pid, uid, gid = struct.unpack("3i", raw)
        require(pid > 1 and uid == HOST_UID and gid == self.selector["host_gid"],
                "foreign host peer")
        base = Path("/proc") / str(pid)
        first = _process_read(base / "stat", 8192)
        require(b") " in first and len(first.rsplit(b") ", 1)[1].split()) > 19,
                "host start identity unavailable")
        ticks = int(first.rsplit(b") ", 1)[1].split()[19])
        require(ticks > 0, "host start identity invalid")
        label = _process_read(base / "attr/current", 256).strip().decode()
        cgroup = _process_read(base / "cgroup", 8192).decode()
        exe = os.readlink(base / "exe")
        command_raw = _process_read(base / "cmdline", 4096)
        require(command_raw.endswith(b"\0"), "host command unterminated")
        command = command_raw.split(b"\0")
        require(command[:-1] == [
            self.selector["host_executable"].encode(), b"-I", b"-B",
            str(HOST_ENTRY).encode(), HOST_TARGET.encode()], "host command source changed")
        require(label == self.selector["host_label"] + " (enforce)" and
                cgroup.splitlines() == ["0::/system.slice/" + HOST_UNIT] and
                exe == self.selector["host_executable"], "host process boundary changed")
        require(sha(pinned_bytes(Path(exe), root_owned=True)) ==
                self.selector["host_executable_sha256"], "host executable bytes changed")
        require(sha(pinned_bytes(HOST_ENTRY, root_owned=True)) ==
                self.selector["host_entry_sha256"] and
                sha(pinned_bytes(HOST_SCRIPT, root_owned=True)) ==
                self.selector["host_script_sha256"], "host server source changed")
        fragment = self.selector["host_unit_fragment"]
        require(sha(pinned_bytes(Path(fragment), root_owned=True)) ==
                self.selector["host_unit_sha256"], "host unit fragment changed")
        second = _process_read(base / "stat", 8192)
        require(b") " in second and len(second.rsplit(b") ", 1)[1].split()) > 19 and
                int(second.rsplit(b") ", 1)[1].split()[19]) == ticks,
                "host process replaced during peer check")
        return pid, ticks

    def exchange(self, packet):
        from .root_effects import RootEffectPump
        RootEffectPump.publish_caller(self.selector)
        raw = canonical(packet)
        require(len(raw) <= MAX_PACKET, "host request oversized")
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM | socket.SOCK_CLOEXEC)
        seconds = 900 if packet["operation"] in {"prepare", "run"} else 5
        connection.settimeout(seconds)
        try:
            connection.connect(str(SOCKET))
            before = self._peer(connection)
            self.last_peer = before
            connection.sendall(struct.pack("!I", len(raw)) + raw)
            size = struct.unpack("!I", _read_exact(connection, 4))[0]
            answer = parse(_read_exact(connection, size), MAX_PACKET)
            require(self._peer(connection) == before, "host peer changed during exchange")
            return answer
        finally:
            connection.close()


class NativeAdmission:
    """Twelve exact calls to the canonical host; no local grant or fake receipt."""

    def __init__(self, selector, transport=None, *, selector_sha256=None):
        self.selector = selector
        self.selector_sha256 = selector_sha256
        self.transport = transport or UnixHostTransport(selector)
        self.build = None
        self.pending_unit = None

    @classmethod
    def from_configuration(cls, *, build, selector_path=SELECTOR,
                           policy_path=HOST_POLICY, transport=None):
        selector_raw = pinned_bytes(selector_path, maximum=4096, root_owned=True)
        selector = parse(selector_raw, 4096)
        from .publication import existing_runtime, render_host_unit
        policy_raw = pinned_bytes(policy_path, maximum=4194304, root_owned=True)
        policy = parse(policy_raw, 4194304)
        approved_python = existing_runtime(policy)
        require(set(selector) == {"schema", "nonce", "case_unit", "socket", "host_unit",
                 "host_uid", "host_gid", "host_label", "host_executable",
                 "host_executable_sha256", "host_entry_sha256", "host_script_sha256", "host_unit_fragment",
                 "host_unit_sha256", "host_policy_sha256", "host_profile_source_sha256",
                 "host_compiled_sha256", "build_sha256",
                 "task_id", "run_token", "fencing_token"}, "closed host selector required")
        require(type(selector["schema"]) is int and selector["schema"] == 1 and
                selector["nonce"] == NONCE and selector["case_unit"] == CASE and
                selector["socket"] == str(SOCKET) and selector["host_unit"] == HOST_UNIT and
                type(selector["host_uid"]) is int and selector["host_uid"] == HOST_UID and
                type(selector["host_gid"]) is int and selector["host_gid"] > 0 and
                type(selector["fencing_token"]) is int and selector["fencing_token"] > 0 and
                selector["host_label"] == HOST_PROFILE and
                all(type(selector[k]) is str and selector[k] for k in
                    ("host_label", "host_executable", "task_id", "run_token")) and
                selector["host_executable"] == approved_python["executable"] and
                selector["host_executable_sha256"] == approved_python["executable_sha256"] and
                Path(selector["host_executable"]).is_absolute() and
                selector["host_unit_fragment"] == "/etc/systemd/system/" + HOST_UNIT and
                selector["build_sha256"] == sha(canonical(build)) and
                selector["host_entry_sha256"] == build["core_files"]["agent-stack/bin/agent-herdr-host-entrypoint"] and
                selector["host_script_sha256"] == build["files"]["offline_case/host_service.py"] and
                selector["host_unit_sha256"] == build["files"]["units/" + HOST_UNIT] and
                selector["host_unit_sha256"] == sha(render_host_unit(policy)) and
                selector["host_profile_source_sha256"] == build["files"]["overlays/host-profile.apparmor"] and
                selector["host_policy_sha256"] == sha(policy_raw) and
                all(type(selector[k]) is str and len(selector[k]) == 64 and
                    all(c in "0123456789abcdef" for c in selector[k]) for k in
                    ("host_executable_sha256", "host_entry_sha256", "host_script_sha256", "host_unit_sha256",
                    "host_policy_sha256", "host_profile_source_sha256",
                    "host_compiled_sha256", "build_sha256")),
                "host selector pin mismatch")
        value = cls(selector, transport, selector_sha256=sha(selector_raw))
        value.build = build
        return value

    def _call(self, operation, binding, **values):
        require(operation in OPERATIONS and type(binding) is dict and
                binding.get("nonce") == NONCE and
                binding.get("build_sha256") == self.selector["build_sha256"],
                "foreign host operation")
        packet = {"schema": 1, "operation": operation, "case": NONCE,
                  "task_id": self.selector["task_id"],
                  "run_token": self.selector["run_token"],
                  "fencing_token": self.selector["fencing_token"],
                  "binding": binding, "arguments": values}
        packet["request_sha256"] = sha(canonical(packet))
        answer = self.transport.exchange(packet)
        require(type(answer) is dict and set(answer) == {"schema", "request_sha256", "value"}
                and answer["schema"] == 1 and answer["request_sha256"] == packet["request_sha256"],
                "foreign or uncertain host reply")
        require(not (type(answer["value"]) is dict and "denied" in answer["value"]),
                "canonical host denied operation")
        return answer["value"]

    def admit(self, authority, binding): return self._call("admit", binding, authority=authority)
    def _pump(self):
        from .root_effects import RootEffectPump
        require(self.build is not None, "published build required for default effect pump")
        return RootEffectPump(self.build, self.transport)

    def prepare(self, authority, binding):
        self._pump().perform(self._call("prepare", binding, authority=authority, phase="begin"), binding)
        self._pump().perform(self._call("prepare", binding, authority=authority, phase="ticket"), binding)
        return self._call("prepare", binding, authority=authority, phase="seal")
    def claim_unit(self, unit, binding):
        self.pending_unit = self._call("claim_unit", binding, unit=unit)
        return self.pending_unit
    def bind_cgroup(self, binding, identity):
        require(self.pending_unit is not None, "original unit effect request required")
        self._pump().perform(self.pending_unit, binding)
        return self._call("bind_cgroup", binding, identity=list(identity))
    def run(self, binding, budget):
        self._pump().perform(self._call("run", binding, budget=budget, phase="root"), binding)
        self._pump().perform(self._call("run", binding, budget=budget, phase="child-ticket"), binding)
        ready = self._call("run", binding, budget=budget, phase="child-seal")
        require(type(ready) is dict and ready == {
            "binding": binding, "outcome": "BOOTSTRAP_CONTINUATION_ONLY",
            "root": True, "managed_children": 1},
            "guarded child bootstrap continuation unknown")
        return self._call("run", binding, budget=budget, phase="ingress")
    def fence(self, binding): return self._call("fence", binding)
    def fenced(self, binding): return self._call("fenced", binding)
    def started(self, binding): return self._call("started", binding)
    def cgroup_identity(self, binding):
        value = self._call("cgroup_identity", binding)
        require(value is None or type(value) is list and len(value) == 2 and
                all(type(v) is int and v > 0 for v in value), "invalid cgroup identity")
        return None if value is None else tuple(value)
    def observe_all(self, binding):
        self._pump().perform(self._call("observe_all", binding, phase="begin"), binding)
        return self._call("observe_all", binding, phase="complete")
    def retire(self, binding, observation):
        return self._call("retire", binding, observation=observation)
    def retired(self, binding): return self._call("retired", binding)
