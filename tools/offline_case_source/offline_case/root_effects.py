"""Closed UID0 effect pump for the existing authenticated host transport.

No arbitrary command, unit or output path is accepted. The original issuer's
approved plan remains authoritative. Root requests are monotonically chained,
consumed before effects and never replayed, including after an uncertain reply.
Historical stop/holder observations use captured ownership and survive expiry.
"""
from __future__ import annotations
from pathlib import Path
import os
import stat
import time

from .case import CASE, NONCE, HOST_PROFILE, require, sha, canonical, parse, pinned_bytes

SUFFIX = NONCE[:16]
BASE = Path("/opt/agent-platform/herdr-offline-" + SUFFIX)
CONTEXT = Path("/var/lib/herdr-offline-observer-" + SUFFIX + "/contexts")
ROLE_UNITS = {role: "herdr-offline-" + role + "-" + SUFFIX + ".service" for role in ("root", "child")}
ACTIONS = frozenset({"PUBLISH_ROOT_ROSTER", "VERIFY_NATIVE_SOURCE", "START_NATIVE_PREPARATION", "OBSERVE_CASE_UNIT", "OBSERVE_CLOSURE"})


def validate_effect(packet, binding, *, previous, sequence):
    require(type(packet) is dict and set(packet) == {"schema", "sequence", "previous_sha256",
        "binding", "request", "request_sha256"} and packet["schema"] == "canonical-case-root-effect-1"
        and type(packet["sequence"]) is int and packet["sequence"] == sequence
        and packet["previous_sha256"] == previous and packet["binding"] == binding
        and packet["request_sha256"] == sha(canonical({k: v for k, v in packet.items()
                                                       if k != "request_sha256"})),
        "root effect sequence or digest changed")
    request = packet["request"]
    require(type(request) is dict and request.get("kind") in ACTIONS and
            request.get("binding") == binding and request.get("role") in {"root", "child", "case"},
            "unknown finite root action")
    fields = {"PUBLISH_ROOT_ROSTER": {"kind", "role", "binding", "identity", "workspace", "marker",
        "pane_id", "shell_pid", "controller_pid", "controller_start_ticks"},
        "VERIFY_NATIVE_SOURCE": {"kind", "role", "binding", "identity", "pane_id", "shell_pid", "controller_pid",
            "controller_start_ticks", "plan_sha256", "grant_sha256"},
        "START_NATIVE_PREPARATION": {"kind", "role", "binding", "identity", "plan_sha256", "grant_sha256",
            "pane_id", "shell_pid", "record_sha256"},
        "OBSERVE_CASE_UNIT": {"kind", "role", "binding", "claim"},
        "OBSERVE_CLOSURE": {"kind", "role", "binding", "roster", "namespaces"}}
    require(set(request) == fields[request["kind"]] and
            (request["role"] == "case") == (request["kind"] in {"OBSERVE_CASE_UNIT", "OBSERVE_CLOSURE"}) and
            (request["kind"] != "PUBLISH_ROOT_ROSTER" or request["role"] == "root"),
            "closed root action required")
    return request


class RootEffectPump:
    def __init__(self, build, transport, effects=None):
        from .native import LinuxEffects
        self.build, self.transport, self.io = build, transport, effects or LinuxEffects()

    @staticmethod
    def publish_caller(selector):
        """Root's own immutable peer facts; SO_PEERCRED/SO_PEERSEC remain decisive.

        UID1001 cannot dereference UID0 /proc/exe under ordinary Linux DAC.
        The exact root driver publishes its own measurement to the existing
        root-owned metadata directory; no execution/admission authority is added.
        """
        from .admission import _process_read
        from .case import OPERATOR_PROFILE
        from .host_service import ROOT, DRIVER_COMMAND, CLEANUP_COMMAND, OPERATOR_UNIT, CLEANUP_UNIT
        require(os.geteuid() == 0, "root caller projection requires UID0")
        pid = os.getpid()
        base = Path("/proc") / str(pid)
        def start():
            raw = _process_read(base / "stat", 8192)
            require(b") " in raw, "caller identity unavailable")
            return int(raw.rsplit(b") ", 1)[1].split()[19])
        ticks = start()
        label = _process_read(base / "attr/current", 256).decode().strip()
        cgroup = _process_read(base / "cgroup", 8192).decode().splitlines()
        require(label == OPERATOR_PROFILE + " (enforce)" and cgroup in
                (["0::/system.slice/" + OPERATOR_UNIT], ["0::/system.slice/" + CLEANUP_UNIT]),
                "exact root operator context required")
        unit, expected = ((OPERATOR_UNIT, DRIVER_COMMAND) if cgroup[0].endswith(OPERATOR_UNIT)
                          else (CLEANUP_UNIT, CLEANUP_COMMAND))
        command = _process_read(base / "cmdline", 4096)
        require(command.endswith(b"\0") and tuple(command.split(b"\0")[:-1]) == expected and
                os.readlink(base / "exe") == "/usr/bin/python3.14", "root driver executable changed")
        build = parse(pinned_bytes(ROOT / "integration-manifest.json", root_owned=True), 262144)
        row = {"schema": "canonical-case-root-caller-1", "pid": pid, "start_ticks": ticks,
            "boot_id": _process_read(Path("/proc/sys/kernel/random/boot_id"), 128).decode().strip(),
            "label": label, "exe": "/usr/bin/python3.14",
            "exe_sha256": sha(pinned_bytes(Path("/usr/bin/python3.14"), root_owned=True)),
            "command": [x.decode() for x in expected], "cgroup": cgroup[0],
            "unit_sha256": sha(pinned_bytes(Path("/etc/systemd/system") / unit, root_owned=True)),
            "build_sha256": sha(canonical(build))}
        require(row["unit_sha256"] == build["files"]["units/" + unit] and
                row["build_sha256"] == selector["build_sha256"] and start() == ticks,
                "root caller source binding changed")
        pump = RootEffectPump.__new__(RootEffectPump)
        name = "caller-" + str(pid) + "-" + str(ticks)
        old = pump._read(name)
        if old is None: pump._write(name, row)
        else: require(old == row, "root caller projection replaced")

    def _read(self, name):
        try: return parse(pinned_bytes(CONTEXT / (name + ".json"), root_owned=True), 262144)
        except FileNotFoundError: return None

    def _write(self, name, value):
        # The directory is an exact root-owned component metadata directory.
        fd = os.open(CONTEXT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            require(info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o750,
                    "root metadata custody changed")
            raw = canonical(value)
            require(0 < len(raw) <= 262144, "root metadata bound exceeded")
            out = os.open(name + ".json", os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                          os.O_NOFOLLOW | os.O_CLOEXEC, 0o640, dir_fd=fd)
            try:
                os.fchown(out, 0, 1001)
                require(os.write(out, raw) == len(raw), "root metadata write uncertain")
                os.fsync(out)
            finally: os.close(out)
            os.fsync(fd)
        finally: os.close(fd)

    def _metadata(self, kind, binding, value):
        row = {"schema": "canonical-case-root-metadata-1", "kind": kind,
               "binding": binding, "value": value}
        row["projection_sha256"] = sha(canonical(row))
        existing = self._read(kind)
        if existing is not None:
            require(existing == row, "root historical projection changed")
        else: self._write(kind, row)
        return value

    def publish_case_phase(self, state, authority, used):
        """RootCustody's nonsecret projection; original private marker remains authority."""
        require(os.geteuid() == 0 and state["binding"] == used and
            sha(canonical(authority)) == used["authority_sha256"], "original consumed phase binding changed")
        old = self._read("case-phase")
        revision = 1 if old is None else old["revision"] + 1
        row = {"schema": "canonical-case-phase-projection-1", "state": state,
               "authority": authority, "used": used, "revision": revision}
        row["projection_sha256"] = sha(canonical(row))
        directory = os.open(CONTEXT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(directory)
            require(info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o750, "root metadata directory changed")
            name = ".phase-" + str(revision)
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o640, dir_fd=directory)
            try:
                raw = canonical(row)
                os.fchown(fd, 0, 1001)
                require(len(raw) <= 65536 and os.write(fd, raw) == len(raw), "phase projection uncertain")
                os.fsync(fd)
            finally: os.close(fd)
            os.replace(name, "case-phase.json", src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally: os.close(directory)

    def require_births(self, binding):
        row = self._read("case-phase")
        require(self._read("scope-fenced") is None and row is not None and row["used"] == binding and
            row["state"]["binding"] == binding and row["state"]["phase"] in {"ADMITTED", "ARMED", "PREPARED", "START_INTENT"} and
            sha(canonical(row["authority"])) == binding["authority_sha256"] and
            row["authority"]["not_before"] <= time.time() < row["authority"]["deadline"],
            "original root scope fenced, expired or changed before effect")

    def perform(self, packet, binding):
        require(os.geteuid() == 0, "root effect requires UID0")
        previous = "0" * 64
        for sequence in range(1, 17):
            old = self._read("effect-" + str(sequence))
            if old is None: break
            previous = sha(canonical(old["packet"]))
        else: raise ValueError("root sequence exhausted")
        request = validate_effect(packet, binding, previous=previous, sequence=sequence)
        if request["kind"] in {"PUBLISH_ROOT_ROSTER", "VERIFY_NATIVE_SOURCE", "START_NATIVE_PREPARATION"}:
            self.require_births(binding)
        # Persist before opening a PTY, writing a roster/unit or asking systemd.
        # A torn/missing outcome is UNKNOWN and cannot repeat the action.
        self._write("effect-" + str(sequence), {"binding": binding, "packet": packet})
        self.active_challenge = packet["request_sha256"]
        if request["kind"] == "VERIFY_NATIVE_SOURCE": return self._startup_source(request, "child-parent-startup-source")
        if request["kind"] == "PUBLISH_ROOT_ROSTER": return self._publish_roster(request)
        if request["kind"] == "START_NATIVE_PREPARATION": return self._prepare_role(request)
        if request["kind"] == "OBSERVE_CASE_UNIT": return self._case_unit(request)
        return self.closure(binding, request["roster"], request["namespaces"])

    def _plan(self, request):
        from herdr.security import InvocationIdentity
        from herdr.private_mount_plan import ApprovedPrivateMountPlan, AUTHORITY_ROOT
        identity = InvocationIdentity.from_dict(request["identity"])
        plan = ApprovedPrivateMountPlan.read(AUTHORITY_ROOT / (sha(canonical(identity.to_json())) + ".json"), identity)
        require(plan.sha256 == request["plan_sha256"], "actual root-published plan changed")
        return identity, plan

    def _stdio(self, pid):
        require(type(pid) is int and pid > 0, "owned pane PID required")
        before = self.io.process_start_ticks(pid)
        rows = {}
        for number in range(3):
            fd = os.open(f"/proc/{pid}/fd/{number}", os.O_PATH | os.O_CLOEXEC)
            try:
                info = os.fstat(fd)
                link = os.readlink(f"/proc/{pid}/fd/{number}")
                require(stat.S_ISCHR(info.st_mode) and link.startswith("/dev/pts/") and
                        link.removeprefix("/dev/pts/").isdecimal(), "actual pane PTY required")
                rows[str(number)] = {"path": link, "device": info.st_dev, "inode": info.st_ino,
                                     "rdev": info.st_rdev}
            finally: os.close(fd)
        require(len({tuple(row.values()) for row in rows.values()}) == 1 and
                self.io.process_start_ticks(pid) == before, "pane terminal changed")
        return rows

    def _publish_roster(self, request):
        from herdr.security import InvocationIdentity
        from herdr.case_roster import Roster, VERSION, ROSTER_PATH, CONTROLLER_LABEL, WORKER_SOURCE
        from herdr.host_configuration import _read_configuration
        require(self.transport.last_peer == (request["controller_pid"], request["controller_start_ticks"]),
                "roster controller differs from authenticated host peer")
        identity = InvocationIdentity.from_dict(request["identity"])
        layout = _read_configuration(Path("/etc/herdr/offline-" + SUFFIX + "/native-layout.json"))
        require(set(layout) == {"schema", "observer", "preparer", "controller_source_sha256", "native_sha256"} and
                layout["schema"] == "canonical-offline-native-layout-1", "unissued native source layout")
        policy_raw = pinned_bytes(Path("/etc/herdr/host-policy.json"), maximum=4194304, root_owned=True)
        authority = _read_configuration(Path("/var/lib/herdr-offline-" + SUFFIX + "/authority.json"))
        from .publication import render_native_layout
        require(layout == render_native_layout(parse(policy_raw, 4194304), self.build["files"], authority),
                "exact existing runtime/helper source publication differs from root approval")
        source = BASE / "overlays/host-profile.apparmor"
        require(sha(pinned_bytes(source, root_owned=True)) == layout["controller_source_sha256"],
                "host profile source changed")
        pid = request["controller_pid"]
        exe = os.readlink(f"/proc/{pid}/exe")
        selector = self.transport.selector
        require(exe == selector["host_executable"], "controller executable changed")
        controller = {"uid": 1001, "gid": 1001, "pid": pid,
            "start_ticks": request["controller_start_ticks"], "exe_sha256": selector["host_executable_sha256"],
            "cgroup": "/system.slice/" + selector["host_unit"], "profile": CONTROLLER_LABEL,
            "source_sha256": layout["controller_source_sha256"],
            "loaded_sha256": self.io.loaded_profile_sha256(CONTROLLER_LABEL)}
        require(CONTROLLER_LABEL == HOST_PROFILE and controller["loaded_sha256"] == authority["host_compiled_sha256"],
                "same original host model/observer controller profile required")
        document = {"schema": VERSION, "nonce": NONCE, "case_binding": request["binding"],
            "not_before": authority["not_before"], "deadline": authority["deadline"],
            "host_policy_sha256": sha(policy_raw), "controller": controller,
            "observer": layout["observer"], "preparer": layout["preparer"], "worker_source_sha256": WORKER_SOURCE,
            "slots": {"root": {"identity": identity.to_json(), "workspace": request["workspace"],
                "marker": request["marker"], "unit": ROLE_UNITS["root"], "stdio": self._stdio(request["shell_pid"])}}}
        roster = Roster.parse(canonical(document), InvocationIdentity)
        # Root writes exactly the configured immutable ROOT base. Later CHILD
        # append remains solely the original custody's actual claimed child path.
        self._publish_absolute(Path(ROSTER_PATH), roster.raw)
        self._startup_source(request, "root-startup-source")
        self._metadata("root-roster", request["binding"], {"roster_sha256": roster.sha256,
            "identity": identity.to_json()})
        from herdr.unit_templates import render_units
        observer = "herdr-offline-observer-" + SUFFIX + ".service"
        content = render_units(roster)[observer].encode()
        self._publish_absolute(Path("/run/systemd/system") / observer, content)
        self.io.run("/usr/bin/systemctl", "daemon-reload", timeout=10)
        self.io.run("/usr/bin/systemctl", "start", observer, timeout=30)
        socket_path = Path("/run/herdr-offline-" + SUFFIX + "/observer.sock")
        until = time.monotonic() + 30
        while not self.io.exists(socket_path):
            require(time.monotonic() < until, "authenticated observer readiness uncertain")
            time.sleep(.05)
        info = socket_path.lstat()
        require(stat.S_ISSOCK(info.st_mode) and info.st_uid == 0 and info.st_gid == 1001 and
                stat.S_IMODE(info.st_mode) == 0o660, "original observer socket boundary changed")
        pid = int(self._unit(observer, "MainPID"))
        self._metadata("observer-control-unit", request["binding"], {"unit": observer,
            "source_sha256": sha(content), "main_pid": pid,
            "main_start_ticks": self.io.process_start_ticks(pid),
            "invocation_id": self._unit(observer, "InvocationID"),
            "cgroup": list(self.io.identity(Path("/sys/fs/cgroup/system.slice") / observer))})
        return roster.sha256

    def _startup_source(self, request, kind):
        from herdr.case_roster import load_roster
        from herdr.security import InvocationIdentity
        from herdr.host_configuration import _read_configuration
        from herdr.launch_environment import require_clean_spawn_source
        from offline_case.native_source import NATIVE_SHA256
        require(kind in {"root-startup-source", "child-parent-startup-source"} and
                self.transport.last_peer == (request["controller_pid"], request["controller_start_ticks"]),
                "startup source differs from authenticated controller")
        roster = load_roster(_read_configuration, InvocationIdentity)
        slot = roster.slot("root")
        require(slot["identity"] == request["identity"] and roster.document["case_binding"] == request["binding"] and
                self._stdio(request["shell_pid"]) == slot["stdio"], "startup source outside original ROOT slot")
        pid = request["shell_pid"]
        current, ticks = self._guard_native_ancestry(pid, request["controller_pid"], request["controller_start_ticks"])
        root_context_sha256 = None
        if kind == "child-parent-startup-source":
            self._plan(request)
            context = self._read("root")
            require(context is not None and context["identity"] == slot["identity"] and
                    context["plan_sha256"] == request["plan_sha256"], "original root custody changed")
            root_context_sha256 = sha(canonical(context))
        return self._metadata(kind, request["binding"], {"identity": slot["identity"],
            "pane_id": request["pane_id"], "shell_pid": pid, "shell_start_ticks": ticks,
            "controller_pid": current, "controller_start_ticks": request["controller_start_ticks"],
            "roster_sha256": roster.sha256, "native_sha256": NATIVE_SHA256,
            "challenge": self.active_challenge, "root_grant_sha256": request.get("grant_sha256"),
            "plan_sha256": request.get("plan_sha256"), "root_context_sha256": root_context_sha256})

    def _guard_native_ancestry(self, pid, controller_pid, controller_start_ticks):
        from herdr.launch_environment import require_clean_spawn_source
        ticks = self.io.process_start_ticks(pid)
        current, visited = pid, set()
        for _ in range(32):
            require(current not in visited and current > 1, "startup source does not descend from original controller")
            visited.add(current)
            if current == controller_pid: break
            raw = self.io.read(Path("/proc") / str(current) / "stat", 8192)
            current = int(raw.rsplit(b")", 1)[1].split()[1])
        else: raise ValueError("owned native ancestry bound exceeded")
        require(self.io.process_start_ticks(current) == controller_start_ticks, "controller PID reused")
        # THE ACTUAL ORIGINAL GUARD, UID0; no raw environment crosses back to
        # the controller, no root_direct_scope shim and no all-true predicate.
        require_clean_spawn_source(pid)
        require(self.io.process_start_ticks(pid) == ticks, "startup source changed during original guard")
        return current, ticks

    def _publish_absolute(self, path, raw):
        # Fixed destinations only; request packets never provide these paths.
        allowed = {Path("/etc/herdr/offline-" + SUFFIX + "/roster.json"),
                   *(Path("/run/systemd/system") / unit for unit in (*ROLE_UNITS.values(), "herdr-offline-observer-" + SUFFIX + ".service"))}
        require(path in allowed and type(raw) is bytes and len(raw) <= 262144, "fixed root destination required")
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(directory)
            require(info.st_uid == 0 and not info.st_mode & 0o022, "root destination ancestry untrusted")
            fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o444, dir_fd=directory)
            try:
                require(os.write(fd, raw) == len(raw), "root publication uncertain")
                os.fsync(fd)
            finally: os.close(fd)
            os.fsync(directory)
        finally: os.close(directory)

    def _prepare_role(self, request):
        from herdr.security import InvocationIdentity
        from herdr.case_roster import Roster, ROSTER_PATH, load_roster
        from herdr.host_configuration import _read_configuration
        from herdr.unit_templates import render_units
        identity, plan = self._plan(request)
        roster = load_roster(_read_configuration, InvocationIdentity)
        role = request["role"]
        require(role in ROLE_UNITS and (role != "root" or roster.slot("root")["identity"] == identity.to_json()),
                "foreign native role")
        if role == "child":
            require("child" not in roster.roles and identity.parent_task_id == roster.slot("root")["identity"]["task_id"],
                    "child cannot be preclaimed or appended twice")
            # Rendering-only view from ACTUAL published child plan/identity and
            # independently measured PTY. It is never published as the roster.
            view = roster.document
            targets = [row["target"] for row in _read_configuration(plan.path)["descriptors"]
                       if row["kind"] == "directory" and row["target"].endswith("/workspace")]
            require(len(targets) == 1, "one canonical child workspace required")
            view["slots"]["child"] = {"identity": identity.to_json(), "workspace": targets[0],
                "unit": ROLE_UNITS["child"], "stdio": self._stdio(request["shell_pid"]),
                "marker": "child-" + identity.run_token}
            roster = Roster.parse(canonical(view), InvocationIdentity)
        unit = ROLE_UNITS[role]
        rendered = render_units(roster)
        content = rendered[unit].encode()
        self._publish_absolute(Path("/run/systemd/system") / unit, content)
        # Scope is exactly two prospective source units. No existing unit or
        # policy is edited. The manager reload/start is a future operational gate.
        self.io.run("/usr/bin/systemctl", "daemon-reload", timeout=10)
        self.io.run("/usr/bin/systemctl", "start", unit, timeout=45)
        until = time.monotonic() + 45
        while self._read(role + ".runtime") is None:
            require(time.monotonic() < until, "native setup reply uncertain; never restart")
            time.sleep(.05)
        self._capture_role(role, request["binding"], sha(content))
        if role == "root":
            observer_unit = "herdr-offline-observer-" + SUFFIX + ".service"
            pid = int(self._unit(observer_unit, "MainPID"))
            self._metadata("observer-control-unit", request["binding"], {
                "unit": observer_unit, "source_sha256": sha(rendered[observer_unit].encode()),
                "main_pid": pid, "main_start_ticks": self.io.process_start_ticks(pid),
                "invocation_id": self._unit(observer_unit, "InvocationID"),
                "cgroup": list(self.io.identity(Path("/sys/fs/cgroup/system.slice") / observer_unit))})
        return {"unit": unit, "identity": identity.to_json(), "plan_sha256": plan.sha256}

    def _unit(self, unit, property):
        require(unit in {*ROLE_UNITS.values(), CASE, "herdr-offline-observer-" + SUFFIX + ".service"}, "foreign unit observation")
        require(property in {"InvocationID", "MainPID", "ControlGroup", "ActiveState"}, "foreign unit property")
        return self.io.run("/usr/bin/systemctl", "show", unit, "--property=" + property, "--value", timeout=10).strip()

    def _capture_role(self, role, binding, source_sha256):
        unit = ROLE_UNITS[role]
        runtime = self._read(role + ".runtime")
        context = self._read(role)
        require(runtime is not None and context is not None and runtime["unit"] == unit,
                "canonical native runtime receipt missing")
        group = Path("/sys/fs/cgroup/system.slice") / unit
        require(list(self.io.identity(group)) == context["cgroup_identity"] and
                self._unit(unit, "ControlGroup") == "/system.slice/" + unit, "role cgroup changed")
        pid = int(self._unit(unit, "MainPID"))
        value = {"role": role, "unit": unit, "binding": binding, "source_sha256": source_sha256,
            "cgroup": context["cgroup_identity"], "invocation_id": self._unit(unit, "InvocationID"),
            "main_pid": pid, "main_start_ticks": self.io.process_start_ticks(pid),
            "runtime": runtime, "context_sha256": sha(canonical(context))}
        self._metadata(role + "-unit", binding, value)

    def _case_unit(self, request):
        from .native import CLAIM, BOUND
        claim, bound = self.io.owned(CLAIM), self.io.owned(BOUND)
        require(claim["binding"] == request["binding"] and claim["unit"] == CASE and
                bound["claim_sha256"] == sha(canonical(claim)) and
                self._unit(CASE, "InvocationID") == bound["invocation_id"] and
                self.io.process_start_ticks(bound["main_pid"]) == bound["main_start_ticks"],
                "actual original root unit-bound receipt changed")
        return self._metadata("case-unit", request["binding"], {**bound, "unit": CASE,
            "source_sha256": claim["fragment_sha256"]})

    def stop_roles(self, binding):
        """Historical owned-role stop. No live grant, roster expiry or host needed."""
        for role, unit in ROLE_UNITS.items():
            receipt = self._read(role + "-unit")
            if receipt is None:
                # A start without a durable owned receipt is UNKNOWN. Never
                # adopt a same-name unit or stop an unproven cgroup.
                require(self._unit(unit, "ActiveState") == "inactive", "unbound role unit may be live")
                continue
            value = receipt["value"]
            require(receipt["binding"] == binding and value["unit"] == unit and
                    self._unit(unit, "InvocationID") == value["invocation_id"], "owned role invocation changed")
            if self._unit(unit, "ActiveState") in {"active", "activating"}:
                require(self._unit(unit, "MainPID") == str(value["main_pid"]) and
                    self.io.process_start_ticks(value["main_pid"]) == value["main_start_ticks"],
                    "owned role main PID/start changed")
            group = Path("/sys/fs/cgroup/system.slice") / unit
            if self.io.exists(group):
                require(tuple(value["cgroup"]) == self.io.identity(group), "owned role cgroup replaced")
                self.io.stop_cgroup(group, tuple(value["cgroup"]))
            self.io.run("/usr/bin/systemctl", "stop", unit, timeout=30)
            require(self._unit(unit, "ActiveState") == "inactive", "owned role stop unknown")

    def observe_historical(self, binding):
        """Default cleanup diagnostic after host loss; never releases a resource.

        Reconstructs only original root-owned custody/unit facts. The canonical
        economic fence still has to be proved by UID1001 original budget replay
        before retirement, so this outcome deliberately does not assert it.
        """
        from .historical_holders import observe_closed
        phase = self._read("case-phase")
        require(phase is not None and phase["used"] == binding and
                phase["state"]["phase"] in {"FENCE_INTENT", "STOP_INTENT", "RETAINED_UNKNOWN"},
                "historical observation before root birth fence")
        roster, namespaces = [], {"root": None, "child": None}
        for role in ("root", "child"):
            context, runtime = self._read(role), self._read(role + ".runtime")
            if context is None:
                require(runtime is None and self._read(role + "-unit") is None,
                        "partial historical scope is unknown")
                continue
            require(runtime is not None, "historical native custody incomplete")
            roster.append({"binding": binding, "role": role, "identity": context["identity"],
                "prepared_grant_sha256": context["grant_sha256"], "plan_sha256": context["plan_sha256"],
                "sandbox_pid": runtime["pid"]})
            namespaces[role] = {"pid": runtime["pid"], "start_ticks": runtime["start_ticks"],
                "namespace": runtime["namespace"], "context_sha256": sha(canonical(context))}
        value = observe_closed(binding, roster, namespaces, self.io, self._read)
        value["observation"]["fenced"] = False
        value["outcome"] = "ROOT_HOLDER_SCAN_ONLY_CANONICAL_FENCE_UNCONFIRMED"
        return self._metadata("historical-observation", binding, value)

    def closure(self, binding, roster, namespaces):
        """Complete root scan is separate from live execution metadata RPC."""
        from .historical_holders import observe_closed
        value = observe_closed(binding, roster, namespaces, self.io, self._read)
        return self._metadata("closure", binding, value)
