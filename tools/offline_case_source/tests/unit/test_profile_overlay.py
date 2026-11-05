"""Inert profile source and reciprocal observer boundary checks."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ProfileOverlay(unittest.TestCase):
    def test_worker_source_and_all_current_consumers_share_exact_pin(self):
        worker = (ROOT / "overlays/worker-profile.apparmor").read_bytes()
        digest = hashlib.sha256(worker).hexdigest()
        self.assertEqual(digest, "42c8d021a856eb5e9c59b9f335695f296ea17b91eb3a04044ca6ef0e7bdf6d62")
        for source in ("overlays/herdr/credential_isolation.py", "native/case_roster.py",
                       "observer/case_roster.py", "offline_case/case.py"):
            self.assertIn(digest, (ROOT / source).read_text())
        self.assertEqual((ROOT.parents[1] / "herdr/credential_isolation.py").read_bytes(),
                         (ROOT / "overlays/herdr/credential_isolation.py").read_bytes())

    def test_worker_drops_capability_and_forbids_profile_escape(self):
        worker = (ROOT / "overlays/worker-profile.apparmor").read_text()
        for rule in ("audit deny capability,", "audit deny change_profile,", "deny userns,",
                     "ptrace (readby) peer=herdr-offline-observer-03414499dd0d1986,"):
            self.assertIn(rule, worker)
        self.assertNotIn("#include <abstractions/base>", worker)

    def test_observer_operator_and_host_reciprocal_peers(self):
        worker = (ROOT / "overlays/worker-profile.apparmor").read_text()
        observer = (ROOT / "overlays/observer-profile.apparmor").read_text()
        host = (ROOT / "overlays/host-profile.apparmor").read_text()
        operator = (ROOT / "overlays/operator-profile.apparmor").read_text()
        self.assertIn("ptrace (read) peer=herdr189-reference-lifetime,", observer)
        self.assertIn("ptrace (read) peer=herdr-offline-controller-03414499dd0d1986,", observer)
        self.assertIn("ptrace (readby) peer=herdr-offline-observer-03414499dd0d1986,", host)
        self.assertIn("ptrace (readby) peer=herdr-offline-observer-03414499dd0d1986,", worker)
        self.assertIn("ptrace (readby) peer=herdr-offline-operator-03414499dd0d1986,", observer)
        self.assertIn("ptrace (read) peer=**,", operator)
        self.assertIn("audit deny ptrace (read, trace, tracedby),", host)
        self.assertIn("audit deny ptrace (trace, tracedby),", observer)


if __name__ == "__main__": unittest.main()
