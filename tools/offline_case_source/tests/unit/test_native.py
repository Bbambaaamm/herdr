"""Inert tests of the concrete Linux command/cgroup decision seam."""
import unittest
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from offline_case.case import CASE, Denied, OBSERVER, PREP, PROFILE, HOST_PROFILE, OPERATOR_PROFILE
from offline_case.native import (BOUND, CLAIM, CGROUP, LinuxEffects, NativeHost, POLICY_PROFILES,
                                 PROFILE_LIST, SYSTEMCTL)
from offline_case.case import BUDGET, sha
from offline_case.case import canonical
from offline_case.admission import HOST_UNIT

BUILD = {"files": {"units/" + CASE: sha(b"fragment"),
                   "units/" + HOST_UNIT: sha(b"host fragment")}}


class Effects:
    def __init__(self):
        self.calls = []
        self.cgroup = (11, 29)
        self.state = "inactive"
        self.records = {}
        self.started = "0"
        self.fail_bound = False
        self.fail_start = False
        self.main_pid = 0
        self.main_ticks = 400

    def unit(self, name, key):
        self.calls.append(("unit", name, key))
        if name == HOST_UNIT:
            if key == "FragmentPath": return "/etc/systemd/system/" + HOST_UNIT
            if key == "ActiveState": return "active"
            if key == "MainPID": return "900"
        if key == "ActiveState": return self.state
        if key == "ControlGroup": return "/system.slice/" + CASE
        if key == "FragmentPath": return "/etc/systemd/system/" + CASE
        if key == "InvocationID": return "a" * 32
        if key == "ExecMainStartTimestampMonotonic": return self.started
        if key == "MainPID": return str(self.main_pid)
        raise AssertionError(key)

    def identity(self, path):
        self.calls.append(("identity", path))
        return self.cgroup

    def process_start_ticks(self, pid):
        if pid == 900: return 500
        assert pid == self.main_pid
        return self.main_ticks

    def stop_cgroup(self, path, identity):
        self.calls.append(("kill", path, identity))
        self.state = "inactive"

    def run(self, *argv, timeout):
        self.calls.append(("run", argv, timeout))
        if argv == (SYSTEMCTL, "start", CASE):
            if self.fail_start: raise RuntimeError("start denied")
            self.state, self.started, self.main_pid = "active", "200", 123
        elif argv == (SYSTEMCTL, "stop", CASE):
            self.state, self.main_pid = "inactive", 0
        else: raise AssertionError(argv)
        return ""

    def owned(self, name): return self.records.get(name)
    def monotonic_usec(self): return 100
    def publish_owned(self, name, record):
        self.calls.append(("publish", name))
        if name == BOUND and self.fail_bound:
            self.fail_bound = False
            raise RuntimeError("crash after start")
        if name in self.records: raise Denied("duplicate ownership receipt")
        self.records[name] = record

    def exists(self, path): return self.state == "active"
    def holder_snapshot(self):
        self.calls.append(("scan",))
        return (), (1, 2)


class ExistingAdmission:
    def __init__(self, identity):
        self.identity = identity
    def _pump(self):
        return SimpleNamespace(stop_roles=lambda binding: None, _read=lambda name: None)
    def cgroup_identity(self, binding):
        return self.identity
    def claim_unit(self, unit, binding): pass
    def bind_cgroup(self, binding, identity): self.identity = identity
    def run(self, binding, budget):
        assert budget == BUDGET
        return {"binding": binding, "completed": True, "root": True,
                "managed_children": 1}


class Native(unittest.TestCase):
    def test_original_claim_precedes_owned_unit_start(self):
        io = Effects()
        binding = {"boot_id": "fixture"}
        class Refuse(ExistingAdmission):
            def claim_unit(self, unit, binding): raise Denied("canonical preparation absent")
        host = NativeHost(io, Refuse(None), build=BUILD)
        with self.assertRaises(Denied): host.start_case(CASE, binding, BUDGET)
        self.assertNotIn(CLAIM, io.records)
        self.assertFalse(any(row[0] == "run" for row in io.calls))

    @staticmethod
    def planned(io, admission, binding):
        # These tests isolate owned systemd/cgroup recovery after an earlier
        # issuer plan; plan validation itself has separate negative coverage.
        host = NativeHost(io, admission, build=BUILD)
        host.planned = {"binding": binding}
        host.plan_approved = True
        host.plan_window_end = __import__("time").time() + 100
        host.custody_deadline_ns = __import__("time").monotonic_ns() + 100_000_000_000
        return host

    def test_owned_host_stops_only_after_local_retirement(self):
        class HostEffects:
            def __init__(self): self.state, self.calls = "active", []
            def unit(self, name, property):
                self.calls.append(("unit", name, property))
                self.assert_name(name)
                return ("/etc/systemd/system/" + HOST_UNIT if property == "FragmentPath"
                        else self.state)
            def assert_name(self, name):
                if name != HOST_UNIT: raise AssertionError("foreign unit")
            def run(self, *args, timeout):
                self.calls.append(("run", args))
                if args != (SYSTEMCTL, "stop", HOST_UNIT): raise AssertionError(args)
                self.state = "inactive"
        io = HostEffects()
        host = NativeHost(effects=io, build={"files": {
            "units/" + CASE: sha(b"case"), "units/" + HOST_UNIT: sha(b"host")}})
        with patch("offline_case.native.pinned_bytes", return_value=b"host"):
            self.assertTrue(host.stop_host_if_retired())
        self.assertEqual([row for row in io.calls if row[0] == "run"],
                         [("run", (SYSTEMCTL, "stop", HOST_UNIT))])

    def test_loaded_policy_hash_comes_from_kernel_raw_data(self):
        class Entry:
            name = "fixture"
            def is_dir(self, *, follow_symlinks): return not follow_symlinks
        io = LinuxEffects()
        io.read = lambda path, maximum: (b"herdr189-reference-lifetime\n"
                 if path == POLICY_PROFILES / "fixture/name" else b"compiled fixture bytes")
        with patch("offline_case.native.os.scandir", return_value=[Entry()]):
            self.assertEqual(io.loaded_profile_sha256("herdr189-reference-lifetime"),
                             hashlib.sha256(b"compiled fixture bytes").hexdigest())

    def test_host_kernel_gate_uses_measured_bytes(self):
        class Kernel:
            def read(self, path, maximum):
                if path == PROFILE_LIST:
                    return (PROFILE + " (enforce)\n" + OBSERVER + " (enforce)\n" + PREP + " (enforce)\n" + HOST_PROFILE + " (enforce)\n").encode()
                assert path == Path("/proc/self/attr/current")
                return (OPERATOR_PROFILE + " (enforce)\n").encode()
            def loaded_profile_sha256(self, profile):
                assert profile in {PROFILE, OBSERVER, PREP, HOST_PROFILE, OPERATOR_PROFILE}
                return {PROFILE: "a" * 64, OBSERVER: "b" * 64, PREP: "c" * 64,
                        HOST_PROFILE: "d" * 64, OPERATOR_PROFILE: "e" * 64}[profile]
        host = NativeHost(Kernel())
        binding = {"nonce": "fixture"}
        a = {"compiled_profile_sha256": "a" * 64, "observer_compiled_sha256": "b" * 64,
             "prep_compiled_sha256": "c" * 64, "host_compiled_sha256": "d" * 64,
             "operator_compiled_sha256": "e" * 64}
        self.assertEqual(host.verify_kernel(a, binding)
                         ["loaded_sha256"], "a" * 64)
        with self.assertRaises(Denied):
            host.verify_kernel(dict(a, compiled_profile_sha256="b" * 64), binding)
        with self.assertRaises(Denied):
            host.verify_kernel(dict(a, observer_compiled_sha256="a" * 64), binding)
        with self.assertRaises(Denied):
            host.verify_kernel(dict(a, host_compiled_sha256="a" * 64), binding)

    def test_missing_accepted_bridge_refuses_before_effects(self):
        io = Effects()
        io.loaded_profile_sha256 = lambda profile: "a" * 64
        host = NativeHost(io)
        with patch("offline_case.native.os.geteuid", return_value=0):
            with self.assertRaises(Denied):
                host.preflight({"operator_compiled_sha256": "a" * 64}, {},
                               Path("/opt/agent-platform/herdr-offline-03414499dd0d1986"))
        self.assertEqual(io.calls, [])

    def test_stale_cgroup_never_receives_kill_or_stop(self):
        io = Effects()
        binding = {"boot_id": "fixture"}
        host = self.planned(io, ExistingAdmission((11, 29)), binding)
        host.start_case(CASE, binding, BUDGET)
        io.cgroup = (11, 28)
        with patch("offline_case.native.pinned_bytes", return_value=b"fragment"):
            with self.assertRaises(Denied): host.stop_owned(CASE, binding)
        self.assertFalse(any(row[0] == "kill" or row[0] == "run" and row[1][1] == "stop"
                             for row in io.calls))

    def test_exact_owned_cgroup_stopped_through_fixed_command(self):
        io = Effects()
        binding = {"boot_id": "fixture"}
        admission = ExistingAdmission(None)
        host = self.planned(io, admission, binding)
        host.start_case(CASE, binding, BUDGET)
        recovered = NativeHost(io, admission, build=BUILD)
        with patch("offline_case.native.pinned_bytes", return_value=b"fragment"):
            self.assertTrue(recovered.stop_owned(CASE, binding))
        self.assertIn(("kill", CGROUP, (11, 29)), io.calls)
        self.assertIn(("run", (SYSTEMCTL, "stop", CASE), 30), io.calls)

    def test_crash_after_start_recovers_only_postclaim_invocation(self):
        io = Effects(); io.fail_bound = True
        binding = {"boot_id": "fixture"}
        host = self.planned(io, ExistingAdmission(None), binding)
        with self.assertRaisesRegex(RuntimeError, "crash after start"):
            host.start_case(CASE, binding, BUDGET)
        self.assertIn(CLAIM, io.records)
        self.assertNotIn(BOUND, io.records)
        recovered = NativeHost(io, build=BUILD)
        with patch("offline_case.native.pinned_bytes", return_value=b"fragment"):
            self.assertTrue(recovered.stop_owned(CASE, binding))
        self.assertIn(BOUND, io.records)
        self.assertIn(("kill", CGROUP, (11, 29)), io.calls)

    def test_old_invocation_cannot_be_adopted(self):
        io = Effects(); io.fail_bound = True
        binding = {"boot_id": "fixture"}
        with self.assertRaises(RuntimeError):
            self.planned(io, ExistingAdmission(None), binding).start_case(CASE, binding, BUDGET)
        io.started = "99"
        with patch("offline_case.native.pinned_bytes", return_value=b"fragment"):
            with self.assertRaises(Denied): NativeHost(io, build=BUILD).stop_owned(CASE, binding)
        self.assertNotIn(BOUND, io.records)
        self.assertFalse(any(row[0] == "kill" for row in io.calls))

    def test_start_failure_keeps_claim_but_has_no_owned_cgroup(self):
        io = Effects(); io.fail_start = True
        binding = {"boot_id": "fixture"}
        with self.assertRaises(RuntimeError):
            self.planned(io, ExistingAdmission(None), binding).start_case(CASE, binding, BUDGET)
        self.assertIn(CLAIM, io.records)
        with patch("offline_case.native.pinned_bytes", return_value=b"fragment"):
            self.assertTrue(NativeHost(io, build=BUILD).stop_owned(CASE, binding))
        self.assertFalse(any(row[0] == "kill" for row in io.calls))

    def test_torn_bound_receipt_never_allows_stop(self):
        io = Effects()
        binding = {"boot_id": "fixture"}
        self.planned(io, ExistingAdmission(None), binding).start_case(CASE, binding, BUDGET)
        io.records[BOUND] = {"schema": 1, "claim_sha256": "0" * 64}
        with patch("offline_case.native.pinned_bytes", return_value=b"fragment"):
            with self.assertRaises(Denied): NativeHost(io, build=BUILD).stop_owned(CASE, binding)
        self.assertFalse(any(row[0] == "kill" for row in io.calls))

    def test_reused_main_pid_denies_kill(self):
        io = Effects()
        binding = {"boot_id": "fixture"}
        self.planned(io, ExistingAdmission(None), binding).start_case(CASE, binding, BUDGET)
        io.main_ticks = 401
        with patch("offline_case.native.pinned_bytes", return_value=b"fragment"):
            with self.assertRaises(Denied): NativeHost(io, build=BUILD).stop_owned(CASE, binding)
        self.assertFalse(any(row[0] == "kill" for row in io.calls))

    def test_independent_closure_requires_canonical_complete_observation(self):
        io = Effects()
        binding = {"boot_id": "fixture"}
        class Bridge(ExistingAdmission):
            def observe_all(self, binding):
                return {"fenced": True, "case_cgroup_empty": True,
                        "descendants": [], "fds": [], "maps": [],
                        "profile_holders": [], "complete": True,
                        "boot_id": binding["boot_id"]}
        bridge = Bridge(None)
        host = NativeHost(io, bridge, build=BUILD)
        self.assertEqual(host.observe_all(binding)["profile_holders"], [])
        bridge.observe_all = lambda binding: {"complete": False}
        with self.assertRaises(Denied): host.observe_all(binding)

    def test_exact_host_control_identity_is_not_a_case_holder(self):
        class Entry:
            def __init__(self, name, path): self.name, self.path = name, path
        class Scan:
            def __init__(self, entries): self.entries = entries
            def __enter__(self): return iter(self.entries)
            def __exit__(self, *_): return False
        def scandir(path):
            if str(path) == "/proc":
                return Scan([Entry("900", "/proc/900"), Entry("901", "/proc/901"),
                             Entry("902", "/proc/902")])
            if str(path) in {"/proc/900/fd", "/proc/901/fd", "/proc/902/fd"}: return Scan([])
            raise AssertionError(path)
        def stat_line(ticks):
            fields = ["0"] * 22
            fields[19] = str(ticks)
            return ("1 (synthetic) " + " ".join(fields)).encode()
        reads = []
        bad_label = [False]
        stacked = [False]
        def read(path, maximum):
            value = str(path)
            reads.append(value)
            if value.endswith("/stat"): return stat_line(500 if "/900/" in value else 600 if "/901/" in value else 700)
            if value.endswith("/attr/current"):
                return (("unconfined" if bad_label[0] and "/900/" in value else
                         "herdr-offline-host-03414499dd0d1986" if "/900/" in value
                         else (PROFILE + "//&unpriv_bwrap" if stacked[0] else PROFILE)
                         if "/901/" in value else "unconfined") + " (enforce)\n").encode()
            if value.endswith("/cgroup"):
                return ("0::/system.slice/" + (HOST_UNIT if "/900/" in value else CASE if "/901/" in value else "other.service") + "\n").encode()
            if value.endswith("/maps"):
                return (b"/opt/agent-platform/herdr-offline-03414499dd0d1986/offline_case/host_service.py"
                        if "/900/" in value else b"/run/herdr-bootstrap" if "/901/" in value else b"")
            if value.endswith("/mountinfo"): return b""
            raise AssertionError(value)
        io = LinuxEffects()
        io.read = read
        with patch("offline_case.native.os.scandir", side_effect=scandir):
            holders, pids = io.holder_snapshot()
            self.assertEqual((holders, pids), (((900, 500), (901, 600)), (900, 901, 902)))
            self.assertTrue(any("/proc/900/maps" in path for path in reads))
            self.assertTrue(any("/proc/902/maps" in path for path in reads))
            stacked[0] = True
            self.assertEqual(io.holder_snapshot()[0], ((900, 500), (901, 600)))
            stacked[0] = False
            bad_label[0] = True
            self.assertEqual(io.holder_snapshot()[0], ((900, 500), (901, 600)))
            bad_label[0] = False

    def test_foreign_process_transferred_fd_blocks_retirement(self):
        class Entry:
            def __init__(self, name, path): self.name, self.path = name, path
        class Scan:
            def __init__(self, entries): self.entries = entries
            def __enter__(self): return iter(self.entries)
            def __exit__(self, *_): return False
        def scandir(path):
            if str(path) == "/proc": return Scan([Entry("902", "/proc/902")])
            if str(path) == "/proc/902/fd": return Scan([Entry("7", "/proc/902/fd/7")])
            raise AssertionError(path)
        def read(path, maximum):
            name = str(path)
            if name.endswith("/stat"):
                fields = ["0"] * 22; fields[19] = "700"
                return ("902 (synthetic) " + " ".join(fields)).encode()
            if name.endswith("/attr/current"): return b"unconfined\n"
            if name.endswith("/cgroup"): return b"0::/system.slice/other.service\n"
            if name.endswith(("/maps", "/mountinfo")): return b""
            raise AssertionError(name)
        io = LinuxEffects(); io.read = read
        with patch("offline_case.native.os.scandir", side_effect=scandir), \
             patch("offline_case.native.os.readlink", return_value="/run/herdr-bootstrap/private"):
            self.assertEqual(io.holder_snapshot()[0], ((902, 700),))
        def unreadable(path, maximum):
            if str(path) == "/proc/902/maps": raise PermissionError("foreign maps unavailable")
            return read(path, maximum)
        io.read = unreadable
        with patch("offline_case.native.os.scandir", side_effect=scandir):
            with self.assertRaises(PermissionError): io.holder_snapshot()

    def test_control_host_cannot_retain_private_fd_and_unknown_candidate_denies(self):
        class Entry:
            def __init__(self, name, path): self.name, self.path = name, path
        class Scan:
            def __init__(self, entries): self.entries = entries
            def __enter__(self): return iter(self.entries)
            def __exit__(self, *_): return False
        def stat_line(ticks):
            fields = ["0"] * 22; fields[19] = str(ticks)
            return ("1 (synthetic) " + " ".join(fields)).encode()
        def scandir(path):
            if str(path) == "/proc": return Scan([Entry("900", "/proc/900"), Entry("901", "/proc/901")])
            if str(path) == "/proc/900/fd": return Scan([Entry("4", "/proc/900/fd/4")])
            if str(path) == "/proc/901/fd": return Scan([])
            raise AssertionError(path)
        def read(path, maximum):
            value = str(path)
            if value.endswith("/stat"): return stat_line(500 if "/900/" in value else 600)
            if value.endswith("/attr/current"):
                return ((HOST_PROFILE if "/900/" in value else PROFILE) + " (enforce)\n").encode()
            if value.endswith("/cgroup"):
                return ("0::/system.slice/" + (HOST_UNIT if "/900/" in value else CASE) + "\n").encode()
            if value.endswith("/maps") or value.endswith("/mountinfo"): return b""
            raise AssertionError(value)
        io = LinuxEffects(); io.read = read
        with patch("offline_case.native.os.scandir", side_effect=scandir), \
             patch("offline_case.native.os.readlink", return_value="/run/herdr-bootstrap/private"):
            self.assertEqual(io.holder_snapshot()[0], ((900, 500), (901, 600)))
        def inaccessible(path, maximum):
            if str(path) == "/proc/901/maps": raise PermissionError("inaccessible worker")
            return read(path, maximum)
        io.read = inaccessible
        with patch("offline_case.native.os.scandir", side_effect=scandir), \
             patch("offline_case.native.os.readlink", return_value="/dev/null"):
            with self.assertRaises(PermissionError): io.holder_snapshot()



if __name__ == "__main__": unittest.main()
