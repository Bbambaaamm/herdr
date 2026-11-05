"""Inert checks of the isolated import and exact candidate installation map."""
import ast
import hashlib
import importlib.machinery
import json
import subprocess
import sys
import unittest
from pathlib import Path
import reference_support
from unittest.mock import patch

from offline_case.case import COMPOSED_CORE, INSTALL_ROOT, Denied, canonical, pinned_bytes, validate_build
from offline_case.case import sha


ROOT = Path(__file__).resolve().parents[2]
BASE = reference_support.accepted_root()


class SourceComposition(unittest.TestCase):
    def test_future_policy_request_describes_final_executed_bytes(self):
        build = json.loads((ROOT / "integration-manifest.json").read_text())
        request = json.loads((ROOT / "host-policy-request.json").read_text())
        binding = request["candidate_binding"]
        self.assertEqual(binding["build_sha256"], hashlib.sha256(canonical(build)).hexdigest())
        self.assertEqual(binding["dispatcher_sha256"],
                         build["core_files"]["herdr/offline_case_host.py"])
        self.assertEqual(binding["host_entry_sha256"],
                         build["core_files"]["agent-stack/bin/offline-case-host-entry"])
        self.assertEqual(request["exact_future_issuer_policy_diff"]["code_files_sha256"],
                         hashlib.sha256(canonical(build["core_files"])).hexdigest())

    def test_host_entrypoint_pins_every_executed_package_byte(self):
        build = json.loads((ROOT / "integration-manifest.json").read_text())
        entry = ROOT / "overlays/agent-stack/bin/offline-case-host-entry"
        tree = ast.parse(entry.read_bytes())
        assignment, = (node for node in tree.body if isinstance(node, ast.Assign)
                       and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                       and node.targets[0].id == "EXPECTED_PACKAGE")
        pins = ast.literal_eval(assignment.value)
        required = {name for name in build["files"] if name.startswith("offline_case/") and name.endswith(".py")}
        required.update({"core_bridge.py", "native_preparation.py", "native_preparation_transport.py",
                         "prep_entry.py", "trusted_prepare.py"})
        required.update(name for name in build["files"]
                        if name.startswith(("native/", "observer/")) and name.endswith(".py"))
        self.assertEqual(set(pins), required)
        for name in required:
            self.assertEqual(pins[name], build["files"][name])
            self.assertEqual(pins[name], sha(pinned_bytes(ROOT / name)))
        # The source manifest alone cannot rescue a stale hardcoded entry pin.
        changed = dict(build["files"], **{"offline_case/case.py": "0" * 64})
        with self.assertRaises(Denied):
            validate_build({**build, "files": changed}, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        original = pinned_bytes(entry)
        corrupted = original.replace(pins["offline_case/case.py"].encode(), b"0" * 64, 1)
        self.assertNotEqual(corrupted, original)
        mutated = ast.parse(corrupted)
        assignment, = (node for node in mutated.body if isinstance(node, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "EXPECTED_PACKAGE" for t in node.targets))
        self.assertNotEqual(ast.literal_eval(assignment.value)["offline_case/case.py"],
                            build["files"]["offline_case/case.py"])

    def test_isolated_preparer_import_path_is_a_string(self):
        source = (ROOT / "prep_entry.py").read_text()
        tree = ast.parse(source)
        assignments = [node for node in ast.walk(tree)
                       if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Subscript) and
                           isinstance(target.value, ast.Attribute) and
                           target.value.attr == "path" for target in node.targets)]
        self.assertTrue(any("str(Path(code['source']))" in ast.unparse(node).replace('"', "'")
                            for node in assignments))
        code = ("import importlib.machinery,sys; "
                f"sys.path[:0]=[{str(ROOT)!r}]; "
                "assert importlib.machinery.PathFinder.find_spec('trusted_prepare',sys.path) is not None")
        result = subprocess.run([sys.executable, "-I", "-B", "-c", code],
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=5)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_every_candidate_byte_has_one_exact_destination(self):
        build = json.loads((ROOT / "integration-manifest.json").read_text())
        validate_build(build, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertEqual(set(build["files"]), set(build["install_targets"]))
        self.assertEqual(len(set(build["install_targets"].values())), len(build["files"]))
        self.assertEqual(build["install_targets"]["core_bridge.py"],
                         INSTALL_ROOT + "/core_bridge.py")
        self.assertEqual(build["install_targets"]["overlays/herdr/launch_plan_issuer.py"],
                         COMPOSED_CORE + "/herdr/launch_plan_issuer.py")
        self.assertEqual(build["metadata_install_targets"]["integration-manifest.json"],
                         INSTALL_ROOT + "/integration-manifest.json")
        self.assertEqual(build["core_files"]["herdr/offline_case_host.py"],
                         build["files"]["overlays/herdr/offline_case_host.py"])
        for changed in ({"install_targets": {**build["install_targets"],
                         "core_bridge.py": "/tmp/unpinned.py"}},
                        {"install_targets": {k: v for k, v in build["install_targets"].items()
                         if k != "core_bridge.py"}}):
            with self.assertRaises(Denied):
                validate_build({**build, **changed}, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        changed_core = dict(build["core_files"])
        changed_core["herdr/offline_case_host.py"] = "0" * 64
        with self.assertRaises(Denied):
            validate_build({**build, "core_files": changed_core}, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")


if __name__ == "__main__":
    unittest.main()
