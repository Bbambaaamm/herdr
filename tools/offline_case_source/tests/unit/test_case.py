"""Inert composed-path tests. No native host operation is used."""
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
import reference_support
from unittest.mock import patch

from offline_case.case import (BUDGET, CASE, CLEANUP, DEADLINE, NONCE, PROFILE,
    PROFILE_SOURCE, OBSERVER, OBSERVER_SOURCE, PREP, PREP_SOURCE, HOST_PROFILE, REQUIRED_FREE, TIMER, BASELINE, BASELINE_STATE, EXECUTOR,
    OPERATOR_PROFILE, CaseDriver, Denied, canonical, parse, pinned_bytes, plan, sha,
    validate_authority, validate_build)

ROOT = Path(__file__).resolve().parents[2]
BASE = reference_support.accepted_root()
BUILD = parse((ROOT / "integration-manifest.json").read_bytes(), 4194304)
INPUTS = {key: key.encode() for key in ("config", "projection", "runtime", "host_selector")}
INPUTS["profile_source"] = (ROOT / "overlays/worker-profile.apparmor").read_bytes()
INPUTS["observer_source"] = (ROOT / "overlays/observer-profile.apparmor").read_bytes()
INPUTS["prep_source"] = (ROOT / "overlays/trusted-preparation.apparmor").read_bytes()
INPUTS["host_profile_source"] = (ROOT / "overlays/host-profile.apparmor").read_bytes()
INPUTS["operator_source"] = (ROOT / "overlays/operator-profile.apparmor").read_bytes()
COMPILED = b"independently compiled fixture policy"


def authority():
    return dict(schema=2, purpose="SINGLE_OFFLINE_PHYSICAL_CASE", nonce=NONCE,
        operator_profile=OPERATOR_PROFILE,
        operator_source_sha256=sha(INPUTS["operator_source"]),
        operator_compiled_sha256=sha(b"compiled operator fixture policy"),
        case_unit=CASE, cleanup_unit=CLEANUP, cleanup_timer=TIMER, profile=PROFILE,
        profile_source_sha256=PROFILE_SOURCE, baseline_sha256=BASELINE,
        observer=OBSERVER, observer_source_sha256=OBSERVER_SOURCE,
        observer_compiled_sha256=sha(b"compiled observer fixture policy"),
        preparer=PREP, prep_source_sha256=PREP_SOURCE,
        prep_compiled_sha256=sha(b"compiled preparation fixture policy"),
        host_profile=HOST_PROFILE,
        host_profile_source_sha256=sha(INPUTS["host_profile_source"]),
        host_compiled_sha256=sha(b"compiled host fixture policy"),
        baseline_state_sha256=BASELINE_STATE, executor=EXECUTOR,
        build_sha256=sha(canonical(BUILD)),
        driver_sha256=BUILD["files"]["offline_case/driver.py"],
        payload_sha256=BUILD["files"]["offline_case/payload.py"],
        compiled_profile_sha256=sha(COMPILED),
        config_sha256=sha(INPUTS["config"]),
        projection_sha256=sha(INPUTS["projection"]),
        runtime_sha256=sha(INPUTS["runtime"]), boot_id="fixture-boot",
        host_selector_sha256=sha(INPUTS["host_selector"]),
        challenge="a" * 64, not_before=DEADLINE - 3600, deadline=DEADLINE,
        budget=copy.deepcopy(BUDGET))


class Custody:
    def __init__(self, a=None):
        self.a = a or authority()
        self.records = []
        self.used = False
        self.current = None

    def authority(self): return self.a
    def state(self): return self.current
    def consumed(self, _): return self.used
    def consume(self, _, binding):
        if self.used: raise Denied("replay")
        self.used = True
        self.records.append(("consume", binding))
    def save(self, state):
        self.current = state
        self.records.append(("save", state["phase"]))


class Host:
    def __init__(self, *, fail=None, holders=False):
        self.calls, self.fail, self.holders = [], fail, holders

    def record(self, name):
        self.calls.append(name)
        if self.fail == name: raise RuntimeError(name)

    def capacity(self): return REQUIRED_FREE
    def boot_id(self): return "fixture-boot"
    def root_inputs(self): return INPUTS.copy()
    def admit(self, _, binding):
        self.record("admit")
        return {"binding": binding, "kind": "CANONICAL_RUNNING_ROOT_CLAIM",
                "task_id": "fixture-task", "run_token": "fixture-run",
                "fencing_token": 1, "task_sha256": "a" * 64,
                "work_catalogue_sha256": "b" * 64}
    def arm_cleanup(self, *_): self.record("arm_cleanup")
    def cleanup_armed(self, *_): self.record("cleanup_armed"); return True
    def prepare(self, a, binding):
        self.record("prepare")
        return {"binding": binding, "sdk_imported": False,
                "setup_fds_closed": True, "setup_paths_hidden": True}
    def plan(self, a, binding):
        self.record("plan")
        return {"binding": binding, "identity": {"task_id": "fixture-task",
                "run_token": "fixture-run", "fencing_token": 1},
                "plan_sha256": "c" * 64, "grant_hash": "d" * 64,
                "grant_expires_at": "2026-11-04T17:43:08+00:00",
                "custody_deadline_monotonic_ns": __import__("time").monotonic_ns() +
                    60_000_000_000}
    def approve_plan(self, a, binding, proof):
        self.record("approve_plan")
        return {"binding": binding, "plan_sha256": proof["plan_sha256"],
                "approval_sha256": "e" * 64}
    def verify_kernel(self, a, binding):
        self.record("verify_kernel")
        return {"binding": binding, "profile": PROFILE,
                "loaded_sha256": a["compiled_profile_sha256"],
                "observer": OBSERVER,
                "observer_loaded_sha256": a["observer_compiled_sha256"],
                "preparer": PREP,
                "prep_loaded_sha256": a["prep_compiled_sha256"],
                "host_profile": HOST_PROFILE,
                "host_loaded_sha256": a["host_compiled_sha256"],
                "enforce": True, "observed": True}
    def start_case(self, _, binding, budget):
        self.record("start_case")
        assert budget == BUDGET
        return {"binding": binding, "completed": True, "root": True,
            "managed_children": 1, "outcome": "SDK_GUARDED_FIXTURE_INGRESS_ONLY",
            "semantic_child_acceptance": "NOT_ESTABLISHED",
            "parent_dependency": "NOT_ESTABLISHED", "E2E184": "NOT_ESTABLISHED"}
    def complete_case(self, binding, budget):
        self.record("complete_case")
        assert budget == BUDGET
        return {"binding": binding, "completed": True, "root": True,
                "managed_children": 1}
    def fence(self, *_): self.record("fence"); return True
    def stop_owned(self, *_): self.record("stop_owned"); return True
    def observe_all(self, *_):
        self.record("observe_all")
        return {"fenced": True, "case_cgroup_empty": True,
            "descendants": [], "fds": [],
            "maps": [], "profile_holders": ["unknown"] if self.holders else [],
            "complete": True, "boot_id": "fixture-boot"}
    def retire_owned(self, *_): self.record("retire_owned"); return True


class SingleCase(unittest.TestCase):
    def test_source_and_compiled_policy_are_independent(self):
        a = authority()
        self.assertNotEqual(a["profile_source_sha256"], a["compiled_profile_sha256"])
        host, custody = Host(), Custody(a)
        CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
            BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertEqual(custody.current["phase"], "RETIRED")
        bad = Custody(dict(a, profile_source_sha256=a["compiled_profile_sha256"]))
        with self.assertRaises(Denied):
            CaseDriver(bad, Host(), lambda: DEADLINE - 1800).start(
                BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")

    def test_manifest_derives_actual_bytes(self):
        validate_build(BUILD, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertEqual(BUILD["files"]["offline_case/driver.py"],
                         sha((ROOT / "offline_case/driver.py").read_bytes()))
        self.assertEqual(plan(BUILD)["status"], "DATA_ONLY_UNISSUED")
        altered = copy.deepcopy(BUILD)
        altered["files"]["offline_case/payload.py"] = "0" * 64
        with self.assertRaises(Denied): validate_build(altered, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")

    def test_retained_sdk_inventory_rejects_changed_late_file(self):
        from offline_case import runtime_inputs as module
        original = module.pinned_bytes
        late = reference_support.package_root() / "accepted-source/proposed/sdk-source/toolsets.py"
        def changed(path, maximum=16_777_216, *, root_owned=False):
            if path == late:
                return b"changed accepted runtime"
            return original(path, maximum, root_owned=root_owned)
        with patch.object(module, "pinned_bytes", side_effect=changed):
            with self.assertRaises(Denied):
                validate_build(BUILD, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")

    def test_exact_authority_and_no_effect_on_rejection(self):
        for change in ({"purpose": "BOUNDED_OFFLINE_EXECUTION"},
                       {"nonce": "68bed0e8"}, {"config_sha256": None},
                       {"driver_sha256": "0" * 64}, {"observer_compiled_sha256": None},
                       {"host_selector_sha256": "0" * 64},
                       {"deadline": DEADLINE + 1},
                       {"budget": dict(BUDGET, attempts=2)}, {"new": True}):
            a = authority(); a.update(change)
            host, custody = Host(), Custody(a)
            with self.assertRaises(Denied):
                CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                    BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
            self.assertEqual(host.calls, [])
            self.assertEqual(custody.records, [])
        with self.assertRaises(Denied):
            validate_authority(authority(), BUILD, now=DEADLINE, free=REQUIRED_FREE,
                               boot="fixture-boot")
        with self.assertRaises(Denied):
            validate_authority(authority(), BUILD, now=DEADLINE - 1800,
                               free=REQUIRED_FREE - 1, boot="fixture-boot")

    def test_composed_order_and_single_attempt(self):
        host, custody = Host(), Custody()
        result = CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
            BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertTrue(result["completed"])
        self.assertEqual(host.calls, ["arm_cleanup", "cleanup_armed", "admit",
            "prepare", "verify_kernel", "start_case", "fence", "stop_owned",
            "observe_all", "retire_owned"])
        phases = [value for kind, value in custody.records if kind == "save"]
        self.assertLess(phases.index("ARMED"), phases.index("ADMITTED"))
        self.assertLess(phases.index("ADMITTED"), phases.index("PREPARED"))
        self.assertLess(phases.index("PREPARED"), phases.index("START_INTENT"))
        self.assertEqual(custody.records[0][0], "consume")
        self.assertEqual(custody.current["phase"], "RETIRED")
        with self.assertRaises(Denied):
            CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")

    def test_host_stop_follows_durable_retired_receipt(self):
        custody = Custody()
        class RetiringHost(Host):
            def stop_host_if_retired(self):
                self.record("stop_host")
                if custody.current["phase"] != "RETIRED":
                    raise AssertionError("host stopped before durable retirement")
                return True
        host = RetiringHost()
        CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
            BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertEqual(host.calls[-2:], ["retire_owned", "stop_host"])

    def test_failure_consumes_attempt_and_retains_unknown_holders(self):
        for failure in ("admit", "arm_cleanup", "prepare", "verify_kernel", "start_case"):
            host, custody = Host(fail=failure), Custody()
            with self.assertRaises(RuntimeError):
                CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                    BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
            self.assertTrue(custody.used)
            self.assertNotIn("retire_owned", host.calls[:host.calls.index("fence")])
        host, custody = Host(holders=True), Custody()
        with self.assertRaises(Denied):
            CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertEqual(custody.current["phase"], "RETAINED_UNKNOWN")
        self.assertNotIn("retire_owned", host.calls)
        host.holders = False
        CaseDriver(custody, host, lambda: DEADLINE - 1800).cleanup()
        self.assertEqual(custody.current["phase"], "RETIRED")
        prior = list(host.calls)
        CaseDriver(custody, host, lambda: DEADLINE - 1800).cleanup()
        self.assertEqual(host.calls, prior)

    def test_cleanup_armed_before_admission_failure(self):
        host, custody = Host(fail="admit"), Custody()
        with self.assertRaises(RuntimeError):
            CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertLess(host.calls.index("arm_cleanup"), host.calls.index("admit"))
        self.assertNotIn("prepare", host.calls)
        self.assertTrue(custody.used)

    def test_false_admission_or_kernel_observation_blocks_worker(self):
        class BadAdmission(Host):
            def admit(self, a, binding):
                self.record("admit")
                return {"binding": binding, "exclusive": True, "fresh": True}
        class BadKernel(Host):
            def verify_kernel(self, a, binding):
                self.record("verify_kernel")
                return {"binding": binding, "profile": PROFILE,
                        "loaded_sha256": "0" * 64, "enforce": True, "observed": True}
        for host in (BadAdmission(), BadKernel()):
            custody = Custody()
            with self.assertRaises(Denied):
                CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                    BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
            self.assertNotIn("start_case", host.calls)
            self.assertTrue(custody.used)

    def test_preparation_proof_follows_owned_start_and_blocks_work(self):
        class BadPreparation(Host):
            def prepare(self, a, binding):
                self.record("prepare")
                return {"binding": binding, "sdk_imported": False,
                        "setup_fds_closed": True, "setup_paths_hidden": False}
        host, custody = BadPreparation(), Custody()
        with self.assertRaises(Denied):
            CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertLess(host.calls.index("admit"), host.calls.index("prepare"))
        self.assertNotIn("start_case", host.calls)
        self.assertTrue(custody.used)

    def test_changed_issuer_plan_denies_before_preparer_birth(self):
        class BadPlan(Host):
            def prepare(self, a, binding):
                self.record("prepare")
                raise Denied("changed original issuer plan")
        host, custody = BadPlan(), Custody()
        with self.assertRaises(Denied):
            CaseDriver(custody, host, lambda: DEADLINE - 1800).start(
                BUILD, root=reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertNotIn("start_case", host.calls)
        self.assertTrue(custody.used)

    def test_duplicate_json_denied(self):
        with self.assertRaises(Denied): parse(b'{"schema":1,"schema":2}')

    def test_pinned_file_alias_denied(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            (root / "source").write_bytes(b"valid")
            self.assertEqual(pinned_bytes(root / "source"), b"valid")
            with self.assertRaises(Denied):
                pinned_bytes(root / "source", root_owned=True)
            (root / "alias").symlink_to(root / "source")
            with self.assertRaises(OSError): pinned_bytes(root / "alias")
            (root / "hardlink").hardlink_to(root / "source")
            with self.assertRaises(Denied): pinned_bytes(root / "source")


if __name__ == "__main__": unittest.main()
