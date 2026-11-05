"""Root-only Linux effects for the one owned offline case.

Construction is inert.  The admission bridge must be the already authorised
Herdr work session; this module never issues a grant or reservation itself.
"""
from __future__ import annotations

import os
import hashlib
import subprocess
import stat
import time
from pathlib import Path

from .case import (BUDGET, CASE, CLEANUP, DEADLINE, PROFILE, OBSERVER, PREP, HOST_PROFILE, REQUIRED_FREE,
                   TIMER, OPERATOR, Denied, canonical, parse, pinned_bytes, require, sha)
from .admission import HOST_UNIT
from .case import OPERATOR_PROFILE

SYSTEMCTL = "/usr/bin/systemctl"
CGROUP = Path("/sys/fs/cgroup/system.slice") / CASE
PROFILE_LIST = Path("/sys/kernel/security/apparmor/profiles")
POLICY_PROFILES = Path("/sys/kernel/security/apparmor/policy/profiles")
OWNERSHIP = Path("/var/lib/herdr-offline-03414499dd0d1986")
CLAIM = "unit-claim-03414499dd0d1986.json"
BOUND = "unit-bound-03414499dd0d1986.json"


class LinuxEffects:
    """Replace only this syscall boundary in inert tests."""

    def run(self, *args, timeout=30):
        result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=timeout, check=False,
                                env={"PATH": "/usr/bin:/usr/sbin", "LANG": "C"})
        require(result.returncode == 0 and len(result.stdout) <= 1048576 and
                len(result.stderr) <= 1048576, "owned command failed")
        return result.stdout.decode("utf-8", "strict")

    def read(self, path: Path, maximum=1048576):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            chunks, size = [], 0
            while True:
                part = os.read(fd, min(65536, maximum + 1 - size))
                if not part:
                    break
                chunks.append(part); size += len(part)
                require(size <= maximum, "observation oversized")
            return b"".join(chunks)
        finally:
            os.close(fd)

    def capacity(self):
        info = os.statvfs("/")
        return info.f_bavail * info.f_frsize

    def exists(self, path: Path):
        return os.path.lexists(path)

    def loaded_profile_sha256(self, profile):
        """Measure kernel exported compiled bytes, including ambiguity checks."""
        found = []
        for entry in os.scandir(POLICY_PROFILES):
            require(entry.is_dir(follow_symlinks=False), "non-directory kernel policy entry")
            location = POLICY_PROFILES / entry.name
            if self.read(location / "name", 256).strip() == profile.encode():
                found.append(hashlib.sha256(self.read(location / "raw_data", 16_777_216)).hexdigest())
        require(len(found) == 1, "loaded profile bytes unavailable or ambiguous")
        return found[0]

    def identity(self, path: Path):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            return info.st_dev, info.st_ino
        finally:
            os.close(fd)

    def stop_cgroup(self, path: Path, identity):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            require((info.st_dev, info.st_ino) == tuple(identity), "owned cgroup replaced")
            kill = os.open("cgroup.kill", os.O_WRONLY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                require(self.identity(path) == tuple(identity), "owned cgroup changed")
                require(os.write(kill, b"1") == 1, "cgroup kill incomplete")
            finally:
                os.close(kill)
        finally:
            os.close(fd)

    def unit(self, name, property):
        require(name in {CASE, CLEANUP, TIMER, OPERATOR, HOST_UNIT} and
                property in {"ActiveState", "FragmentPath", "ControlGroup", "MainPID",
                             "ExecMainStartTimestampMonotonic", "InvocationID"},
                "foreign unit query")
        output = self.run(SYSTEMCTL, "show", name, "--property=" + property,
                          "--value", timeout=10).strip()
        require("\n" not in output, "ambiguous unit property")
        return output

    def _ownership_dir(self):
        fd = os.open(OWNERSHIP, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        info = os.fstat(fd)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and
                stat.S_IMODE(info.st_mode) == 0o700, "owned receipt directory changed")
        return fd

    def publish_owned(self, name, record):
        """One exclusive, durable subordinate receipt; never an admission grant."""
        require(name in {CLAIM, BOUND} and type(record) is dict, "foreign ownership receipt")
        fd = self._ownership_dir()
        try:
            raw = canonical(record)
            require(0 < len(raw) <= 4096, "ownership receipt oversized")
            item = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                           os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=fd)
            try:
                require(os.write(item, raw) == len(raw), "ownership receipt short write")
                os.fsync(item)
            finally:
                os.close(item)
            os.fsync(fd)
        finally:
            os.close(fd)

    def owned(self, name):
        require(name in {CLAIM, BOUND}, "foreign ownership receipt")
        try:
            return parse(pinned_bytes(OWNERSHIP / name, maximum=4096, root_owned=True), 4096)
        except FileNotFoundError:
            return None

    def monotonic_usec(self):
        return time.monotonic_ns() // 1000

    def process_start_ticks(self, pid):
        require(type(pid) is int and pid > 0, "invalid owned process ID")
        raw = self.read(Path("/proc") / str(pid) / "stat", 8192)
        require(b") " in raw and len(raw.rsplit(b") ", 1)[1].split()) > 19,
                "owned process identity unavailable")
        ticks = int(raw.rsplit(b") ", 1)[1].split()[19])
        require(ticks > 0, "owned process start identity invalid")
        return ticks

    def holder_snapshot(self):
        """Conservative complete host scan; any inaccessible or changing task denies retirement."""
        with os.scandir("/proc") as stream:
            pids = sorted(int(entry.name) for entry in stream if entry.name.isdecimal())
        require(len(pids) <= 8192, "process inventory exceeds bound")
        holders = []
        markers = (b"/run/herdr-bootstrap", b"/run/herdr/policy-code",
                   b"/run/herdr-policy", b"/opt/agent-platform/herdr-offline-03414499dd0d1986")
        for pid in pids:
            base = Path("/proc") / str(pid)
            before = self.read(base / "stat", 8192)
            require(b") " in before and len(before.rsplit(b") ", 1)[1].split()) > 19,
                    "process start identity unavailable")
            ticks = int(before.rsplit(b") ", 1)[1].split()[19])
            label = self.read(base / "attr/current", 4096).strip()
            cgroup = self.read(base / "cgroup", 65536)
            maps = self.read(base / "maps", 8_388_608)
            mounts = self.read(base / "mountinfo", 8_388_608)
            fd_dir = base / "fd"
            with os.scandir(fd_dir) as stream:
                links = sorted(os.readlink(entry.path).encode("utf-8", "surrogateescape")
                               for entry in stream)
            require(len(links) <= 4096, "process descriptor inventory exceeds bound")
            after = self.read(base / "stat", 8192)
            require(b") " in after and len(after.rsplit(b") ", 1)[1].split()) > 19 and
                    int(after.rsplit(b") ", 1)[1].split()[19]) == ticks and ticks > 0,
                    "process changed during holder scan")
            if (label.startswith(PROFILE.encode()) or
                    b"/system.slice/" + CASE.encode() in cgroup or
                    any(marker in data for marker in markers
                        for data in (maps, mounts, *links))):
                holders.append((pid, ticks))
        return tuple(holders), tuple(pids)


class NativeHost:
    """Concrete effect path with an injected existing Herdr admission session.

    An adapter supplied by the accepted Herdr runtime must implement admit,
    prepare, run and retire using its typed grants, PolicyLaunchFactory and
    bootstrap.  No local JSON file can provide these operations.
    """

    def __init__(self, effects=None, admission=None, *, input_paths=None, build=None):
        self.io = effects or LinuxEffects()
        self.build = build
        self.admission = admission
        self.input_paths = input_paths or {
            "profile_source": Path("/etc/herdr/worker-profile.apparmor"),
            "observer_source": Path("/etc/herdr/observer-profile.apparmor"),
            "prep_source": Path("/etc/herdr/trusted-preparation.apparmor"),
            "host_profile_source": Path("/etc/herdr/host-profile.apparmor"),
            "config": Path("/etc/herdr/worker-confinement.json"),
            "projection": Path("/etc/herdr/worker-projection.json"),
            "runtime": Path("/etc/herdr/worker-runtime.json"),
            "host_selector": Path("/etc/herdr/offline-case-host.json"),
            "operator_source": Path("/etc/herdr/operator-profile.apparmor")}
        self.owned_cgroup = None
        self.fragment_sha256 = (build["files"]["units/" + CASE] if build is not None else None)
        self.host_fragment_sha256 = (build["files"].get("units/" + HOST_UNIT) if build is not None else None)

    def capacity(self):
        return self.io.capacity()

    def boot_id(self):
        return self.io.read(Path("/proc/sys/kernel/random/boot_id"), 128).decode().strip()

    def root_inputs(self):
        require(set(self.input_paths) == {"profile_source", "observer_source", "prep_source", "host_profile_source", "config", "projection", "runtime", "host_selector", "operator_source"},
                "exact root inputs required")
        return {key: pinned_bytes(path, root_owned=True)
                for key, path in self.input_paths.items()}

    def preflight(self, authority, build, root):
        require(os.geteuid() == 0, "root execution required")
        require(self.io.loaded_profile_sha256(OPERATOR_PROFILE) == authority["operator_compiled_sha256"],
                "root operator compiled policy must match before any case effect")
        require(self.admission is not None and
                getattr(self.admission, "selector_sha256", None) ==
                authority["host_selector_sha256"] and
                self.admission.selector["host_compiled_sha256"] == authority["host_compiled_sha256"],
                "retained host selector differs from once-only authority")
        require(self.admission is not None and all(callable(getattr(self.admission, name, None))
                for name in ("admit", "prepare", "claim_unit",
                             "bind_cgroup", "run", "fence", "fenced", "started",
                             "cgroup_identity", "observe_all", "retire", "retired")),
                "accepted Herdr admission bridge unavailable")
        require(self.io.read(Path("/proc/self/attr/current"), 256).strip() ==
                (OPERATOR_PROFILE + " (enforce)").encode(),
                "trusted preparation is outside the exact observer domain")
        require(root == Path("/opt/agent-platform/herdr-offline-03414499dd0d1986") and
                root.resolve(strict=True) == root, "unapproved executable root")
        for name in (CASE, CLEANUP, TIMER, OPERATOR, HOST_UNIT):
            fragment = Path(self.io.unit(name, "FragmentPath"))
            require(fragment.is_absolute() and
                    sha(pinned_bytes(fragment, root_owned=True)) ==
                    build["files"]["units/" + name],
                    "owned unit fragment differs from pinned source")
        self.fragment_sha256 = build["files"]["units/" + CASE]
        require(self.io.unit(OPERATOR, "ActiveState") in {"activating", "active"} and
                self.io.unit(OPERATOR, "MainPID") == str(os.getpid()),
                "driver is outside its pinned owned operator unit")
        require(self.io.unit(CASE, "ActiveState") == "inactive", "case already active")
        require(self.io.unit(TIMER, "ActiveState") == "active",
                "independent cleanup timer must preexist attempt consumption")

    def arm_cleanup(self, cleanup, timer, deadline, binding):
        require((cleanup, timer, deadline) == (CLEANUP, TIMER, DEADLINE), "foreign cleanup")
        require(self.io.unit(TIMER, "ActiveState") == "active",
                "independent timer vanished after attempt consumption")
        from .outer_lifecycle import OuterLifecycle
        require(OuterLifecycle(self.build, self.io).arm(binding, deadline), "finite outer expiry not armed")

    def cleanup_armed(self, timer, binding):
        return timer == TIMER and self.io.unit(TIMER, "ActiveState") == "active"

    def admit(self, authority, binding):
        receipt = self.admission.admit(authority, binding)
        require(type(receipt) is dict and
                set(receipt) == {"binding", "kind", "task_id", "run_token",
                                 "fencing_token", "task_sha256", "work_catalogue_sha256"} and
                receipt["binding"] == binding and
                receipt["kind"] == "CANONICAL_RUNNING_ROOT_CLAIM" and
                all(receipt[key] == self.admission.selector[key] for key in
                    ("task_id", "run_token", "fencing_token")) and
                all(type(receipt[key]) is str and len(receipt[key]) == 64 and
                    all(char in "0123456789abcdef" for char in receipt[key]) for key in
                    ("task_sha256", "work_catalogue_sha256")),
                "canonical root claim or work catalogue unavailable")
        return receipt

    def prepare(self, authority, binding):
        # The bridge must use HostPolicyLaunchFactory.prepare and
        # prepare_child, then seal and arm/confirm their bootstraps against
        # observed processes.  A bare local claim cannot cross this seam.
        proof = self.admission.prepare(authority, binding)
        require(proof == {"binding": binding, "sdk_imported": False,
                          "setup_fds_closed": True, "setup_paths_hidden": True},
                "accepted launch preparation incomplete")
        return proof

    def verify_kernel(self, authority, binding):
        require(self.io.loaded_profile_sha256(OPERATOR_PROFILE) == authority["operator_compiled_sha256"],
                "root operator compiled policy differs from source approval")
        names = self.io.read(PROFILE_LIST, 1048576).decode("utf-8", "strict").splitlines()
        require(names.count(PROFILE + " (enforce)") == 1, "profile not enforced")
        require(names.count(OBSERVER + " (enforce)") == 1, "observer profile not enforced")
        require(names.count(PREP + " (enforce)") == 1, "preparation profile not enforced")
        require(names.count(HOST_PROFILE + " (enforce)") == 1, "host profile not enforced")
        require(self.io.read(Path("/proc/self/attr/current"), 256).strip() ==
                (OPERATOR_PROFILE + " (enforce)").encode(), "host observer label unavailable")
        require(self.io.loaded_profile_sha256(PROFILE) == authority["compiled_profile_sha256"],
                "kernel compiled policy differs from root approval")
        require(self.io.loaded_profile_sha256(OBSERVER) == authority["observer_compiled_sha256"],
                "kernel observer policy differs from root approval")
        require(self.io.loaded_profile_sha256(PREP) == authority["prep_compiled_sha256"],
                "kernel preparation policy differs from root approval")
        require(self.io.loaded_profile_sha256(HOST_PROFILE) == authority["host_compiled_sha256"],
                "kernel host policy differs from root approval")
        return {"binding": binding, "profile": PROFILE,
                "loaded_sha256": authority["compiled_profile_sha256"],
                "observer": OBSERVER,
                "observer_loaded_sha256": authority["observer_compiled_sha256"],
                "preparer": PREP,
                "prep_loaded_sha256": authority["prep_compiled_sha256"],
                "host_profile": HOST_PROFILE,
                "host_loaded_sha256": authority["host_compiled_sha256"],
                "enforce": True, "observed": True}

    def start_case(self, unit, binding, budget):
        require(unit == CASE and budget == BUDGET and
                self.io.unit(CASE, "ActiveState") == "inactive", "foreign or active case")
        require(self.fragment_sha256 is not None and
                self.io.owned(CLAIM) is None and self.io.owned(BOUND) is None,
                "owned unit already claimed or preflight absent")
        self.admission.claim_unit(CASE, binding)
        claim = {"schema": 1, "binding": binding, "unit": CASE,
                 "boot_id": binding["boot_id"], "fragment_sha256": self.fragment_sha256,
                 "before_start_usec": self.io.monotonic_usec()}
        self.io.publish_owned(CLAIM, claim)
        self.io.run(SYSTEMCTL, "start", CASE, timeout=10)
        require(self.io.unit(CASE, "ControlGroup") == "/system.slice/" + CASE,
                "case cgroup differs from owned unit")
        self.owned_cgroup = self.io.identity(CGROUP)
        invocation = self.io.unit(CASE, "InvocationID")
        require(len(invocation) == 32 and all(c in "0123456789abcdef" for c in invocation),
                "owned invocation ID unavailable")
        main_pid = self.io.unit(CASE, "MainPID")
        require(main_pid.isdecimal() and int(main_pid) > 0, "owned main PID unavailable")
        start_ticks = self.io.process_start_ticks(int(main_pid))
        self.io.publish_owned(BOUND, {"schema": 1, "claim_sha256": sha(canonical(claim)),
                                      "cgroup": list(self.owned_cgroup),
                                      "invocation_id": invocation, "main_pid": int(main_pid),
                                      "main_start_ticks": start_ticks})
        self.admission.bind_cgroup(binding, self.owned_cgroup)
        return self.admission.run(binding, budget)

    def _owned_identity(self, binding):
        claim = self.io.owned(CLAIM)
        require(type(claim) is dict and set(claim) == {"schema", "binding", "unit",
                "boot_id", "fragment_sha256", "before_start_usec"} and
                claim["schema"] == 1 and claim["binding"] == binding and
                claim["unit"] == CASE and claim["boot_id"] == binding["boot_id"] and
                type(claim["before_start_usec"]) is int and
                claim["before_start_usec"] > 0,
                "owned unit claim absent or changed")
        fragment = Path(self.io.unit(CASE, "FragmentPath"))
        require(self.fragment_sha256 is not None and
                claim["fragment_sha256"] == self.fragment_sha256 and
                fragment.is_absolute() and
                sha(pinned_bytes(fragment, root_owned=True)) == claim["fragment_sha256"],
                "owned unit fragment changed")
        bound = self.io.owned(BOUND)
        if bound is not None:
            require(type(bound) is dict and set(bound) == {"schema", "claim_sha256",
                    "cgroup", "invocation_id", "main_pid", "main_start_ticks"} and
                    bound["schema"] == 1 and
                    bound["claim_sha256"] == sha(canonical(claim)) and
                    type(bound["cgroup"]) is list and len(bound["cgroup"]) == 2 and
                    all(type(x) is int and x > 0 for x in bound["cgroup"]) and
                    type(bound["main_pid"]) is int and bound["main_pid"] > 0 and
                    type(bound["main_start_ticks"]) is int and bound["main_start_ticks"] > 0,
                    "owned cgroup receipt changed")
            require(self.io.unit(CASE, "InvocationID") == bound["invocation_id"],
                    "owned systemd invocation replaced")
            if self.io.unit(CASE, "ActiveState") == "active":
                require(self.io.unit(CASE, "MainPID") == str(bound["main_pid"]) and
                        self.io.process_start_ticks(bound["main_pid"]) == bound["main_start_ticks"],
                        "owned main PID reused or replaced")
            if not self.io.exists(CGROUP):
                require(self.io.unit(CASE, "ActiveState") == "inactive",
                        "owned cgroup disappeared while unit active")
                return None
            return tuple(bound["cgroup"])
        # Crash after systemctl start and before bind: adopt only the exact
        # one-shot unit invocation after the durable claim, never a stale PID.
        if not self.io.exists(CGROUP):
            require(self.io.unit(CASE, "ActiveState") == "inactive",
                    "unbound unit active without cgroup")
            return None
        require(self.io.unit(CASE, "ControlGroup") == "/system.slice/" + CASE,
                "unbound unit cgroup unknown")
        started = self.io.unit(CASE, "ExecMainStartTimestampMonotonic")
        require(started.isdecimal() and int(started) > claim["before_start_usec"],
                "unit did not start after durable claim")
        invocation = self.io.unit(CASE, "InvocationID")
        require(len(invocation) == 32 and all(c in "0123456789abcdef" for c in invocation),
                "unbound invocation ID unavailable")
        main_pid = self.io.unit(CASE, "MainPID")
        require(main_pid.isdecimal() and int(main_pid) > 0, "unbound main PID unavailable")
        start_ticks = self.io.process_start_ticks(int(main_pid))
        identity = self.io.identity(CGROUP)
        self.io.publish_owned(BOUND, {"schema": 1, "claim_sha256": sha(canonical(claim)),
                                      "cgroup": list(identity), "invocation_id": invocation,
                                      "main_pid": int(main_pid), "main_start_ticks": start_ticks})
        return identity

    def fence(self, binding):
        self.admission.fence(binding)
        return self.admission.fenced(binding) is True

    def stop_owned(self, unit, binding):
        require(unit == CASE, "foreign stop")
        if self.admission is not None:
            self.admission._pump().stop_roles(binding)
        identity = self._owned_identity(binding) if self.io.owned(CLAIM) is not None else None
        if identity is not None and self.admission is not None:
            receipt = self.admission._pump()._read("case-unit")
            require(receipt is None or (receipt["binding"] == binding and
                    tuple(receipt["value"]["cgroup"]) == identity),
                    "root-owned case cgroup differs from original bound unit")
        if identity is None:
            require(self.io.unit(CASE, "ActiveState") == "inactive",
                    "unowned or unknown case unit")
            return True
        require(type(identity) is tuple and len(identity) == 2 and
                self.io.identity(CGROUP) == identity, "owned cgroup identity unknown")
        self.io.stop_cgroup(CGROUP, identity)
        self.io.run(SYSTEMCTL, "stop", CASE, timeout=30)
        return self.io.unit(CASE, "ActiveState") == "inactive"

    def observe_all(self, binding):
        # Both global snapshots must agree. Any inaccessible process or
        # unexpected profile holder retains confinement for a later retry.
        if self.io.exists(CGROUP):
            identity = self._owned_identity(binding)
            require(self.io.identity(CGROUP) == identity, "case cgroup changed before closure")
            require(self.io.read(CGROUP / "cgroup.events", 4096).splitlines().count(b"populated 0") == 1,
                    "case cgroup not empty")
            require(self.io.read(CGROUP / "cgroup.procs", 4096).strip() == b"",
                    "case cgroup still has processes")
        if self.admission is not None:
            result = self.admission.observe_all(binding)
            require(result == {"fenced": True, "case_cgroup_empty": True,
                              "descendants": [], "fds": [], "maps": [],
                              "profile_holders": [], "complete": True,
                              "boot_id": binding["boot_id"]},
                    "accepted Herdr holder closure absent")
        return {"fenced": True, "case_cgroup_empty": True,
                "descendants": [], "fds": [], "maps": [],
                "profile_holders": [], "complete": True,
                "boot_id": binding["boot_id"]}

    def observe_historical(self, binding):
        return self.admission._pump().observe_historical(binding)

    def retire_owned(self, binding, observation):
        require(observation["complete"] is True and self.admission.fenced(binding) is True,
                "retirement before fence")
        self.admission.retire(binding, observation)
        return self.admission.retired(binding) is True

    def stop_host_if_retired(self):
        """Stop only the pinned owned host after durable local RETIRED state."""
        require(self.host_fragment_sha256 is not None, "host unit source pin missing")
        fragment = Path(self.io.unit(HOST_UNIT, "FragmentPath"))
        require(fragment.is_absolute() and
                sha(pinned_bytes(fragment, root_owned=True)) == self.host_fragment_sha256,
                "owned host unit fragment changed")
        state = self.io.unit(HOST_UNIT, "ActiveState")
        require(state in {"active", "inactive"}, "owned host state uncertain")
        if state == "active":
            self.io.run(SYSTEMCTL, "stop", HOST_UNIT, timeout=30)
        require(self.io.unit(HOST_UNIT, "ActiveState") == "inactive",
                "owned host stop uncertain")
        return True
