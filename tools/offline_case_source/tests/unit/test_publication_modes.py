"""Inert source publication contract; never installs a file."""
import json
import unittest
from pathlib import Path
import reference_support

from offline_case.case import COMPOSED_CORE, INSTALL_ROOT, Denied, validate_build
from offline_case.publisher import expected_modes
from offline_case.publication import existing_runtime, render_host_unit


ROOT = Path(__file__).resolve().parents[2]
BASE = reference_support.accepted_root()


class PublicationModes(unittest.TestCase):
    def test_host_unit_uses_root_owned_pinned_system_interpreter(self):
        unit = (ROOT / "units/herdr-offline-host-03414499dd0d1986.service").read_text()
        profile = (ROOT / "overlays/host-profile.apparmor").read_text()
        policy = json.loads(json.dumps(reference_support.runtime_policy()).encode())
        host_python = existing_runtime(policy)["executable"]
        self.assertEqual(unit.encode(), render_host_unit(policy))
        self.assertIn("ExecStart=" + host_python + " -I -B ", unit)
        runtime_root = host_python.rsplit("/bin/", 1)[0]
        self.assertIn(runtime_root + "/ r,", profile)
        self.assertIn(runtime_root + "/** rmix,", profile)
        admission = (ROOT / "offline_case/admission.py").read_text()
        self.assertIn('sha(pinned_bytes(Path(exe), root_owned=True))', admission)
        self.assertNotIn(INSTALL_ROOT + "/runtime/python/bin/python3.11", unit)

    def test_stage_one_and_host_entries_retain_execute_mode(self):
        build = json.loads((ROOT / "integration-manifest.json").read_bytes())
        validate_build(build, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        modes = expected_modes(build)
        self.assertEqual(build["installed_modes"], modes)
        self.assertEqual(modes["data"], 0o444)
        self.assertEqual(modes["executable"], 0o555)
        for path in ("agent-stack/policy-bin/hermes",
                     "agent-stack/bin/agent-hermes-policy-stage1",
                     "agent-stack/bin/agent-herdr-host-entrypoint",
                     "agent-stack/bin/offline-case-host-entry"):
            self.assertIn(COMPOSED_CORE + "/" + path,
                          modes["executable_targets"])
        self.assertNotIn(INSTALL_ROOT + "/offline_case/driver.py",
                         modes["executable_targets"])

    def test_changed_installed_mode_denies_source_admission(self):
        build = json.loads((ROOT / "integration-manifest.json").read_bytes())
        for changed in ({**build["installed_modes"], "executable": 0o444},
                        {**build["installed_modes"], "executable_targets": []}):
            with self.assertRaises(Denied):
                validate_build({**build, "installed_modes": changed},
                               reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")


if __name__ == "__main__":
    unittest.main()
