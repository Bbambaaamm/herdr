"""Inert checks of the SDK05 and default runtime composition boundary."""
import ast
import hashlib
import json
import unittest
from pathlib import Path
import reference_support

from offline_case.case import canonical, validate_build
from offline_case.publication import render_host_unit


ROOT = Path(__file__).resolve().parents[2]
SDK_MAP = None
RUNTIME = None


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class SourceRebase(unittest.TestCase):
    def setUp(self):
        self.build = json.loads((ROOT / "integration-manifest.json").read_bytes())

    def test_closed_source_and_immutable_accepted_inputs(self):
        validate_build(self.build, reference_support.package_root(), baseline=reference_support.package_root() / "accepted-source")
        self.assertEqual((len(self.build["files"]), len(self.build["core_files"])), (104, 475))
        self.assertEqual(self.build["baseline_index_sha256"],
                         digest((ROOT / "accepted-source-index.json").read_bytes()))

    def test_original_core_and_sdk_are_retained_exactly(self):
        origin = reference_support.accepted_root()
        package = reference_support.package_root()
        index = json.loads((ROOT / "runtime-input-index.json").read_bytes())
        for name, row in index["files"].items():
            self.assertEqual(digest((package / "accepted-source" / name).read_bytes()),
                             row["sha256"], name)
            self.assertEqual((package / "accepted-source" / name).read_bytes(),
                             (origin / name).read_bytes(), name)

    def test_canonical_manifest_is_an_explicit_pinned_overlay(self):
        name = "provenance/CANONICAL_SOURCE_MANIFEST.sha256"
        overlay = "overlays/" + name
        expected = "4f4e310f5701e845586bdac08215f743f82bacbcb707f4b04dec579c1e0f5a41"
        self.assertEqual(digest((reference_support.repo_root() / name).read_bytes()), expected)
        self.assertEqual(self.build["files"][overlay], expected)
        self.assertEqual(self.build["overlay_targets"]["composed-core/" + name], overlay)
        self.assertEqual(self.build["core_files"][name], expected)
        self.assertEqual(digest((reference_support.package_root() / "composed-core" / name).read_bytes()), expected)
        self.assertEqual(digest((ROOT / "canonical-core-index.json").read_bytes()),
                         "07341cbd524b30d42a4e06d105ae9c174b185fd7988ceb9c7010acd7db3406a5")

    def test_materializer_uses_replaced_entrypoint_byte(self):
        name = "agent-stack/bin/offline-case-host-entry"
        overlay = ROOT / self.build["overlay_targets"]["composed-core/" + name]
        actual = reference_support.package_root() / "composed-core" / name
        self.assertEqual(actual.read_bytes(), overlay.read_bytes())
        self.assertEqual(digest(actual.read_bytes()), self.build["core_files"][name])
        self.assertNotEqual(actual.read_bytes(), (reference_support.repo_root() / name).read_bytes())

    def test_fixed_host_entry_and_posix_unit_follow_final_bytes(self):
        tree = ast.parse((ROOT / "overlays/agent-stack/bin/offline-case-host-entry").read_bytes())
        assignment, = (node for node in tree.body if isinstance(node, ast.Assign)
                       and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                       and node.targets[0].id == "EXPECTED_PACKAGE")
        pins = ast.literal_eval(assignment.value)
        required = {name for name in self.build["files"]
                    if name.startswith("offline_case/") and name.endswith(".py")}
        required.update({"core_bridge.py", "native_preparation.py",
                         "native_preparation_transport.py", "prep_entry.py", "trusted_prepare.py"})
        required.update(name for name in self.build["files"]
                        if name.startswith(("native/", "observer/")) and name.endswith(".py"))
        self.assertEqual(set(pins), required)
        for name, expected in pins.items():
            self.assertEqual(expected, digest((ROOT / name).read_bytes()), name)
        policy = reference_support.runtime_policy()
        unit = (ROOT / "units/herdr-offline-host-03414499dd0d1986.service").read_bytes()
        self.assertEqual(unit, render_host_unit(policy))
        self.assertNotIn(b"\\opt\\", unit)
        request = json.loads((ROOT / "host-policy-request.json").read_bytes())
        self.assertEqual(request["candidate_binding"]["build_sha256"],
                         digest(canonical(self.build)))
        self.assertEqual(request["exact_future_issuer_policy_diff"]["code_files_sha256"],
                         digest(canonical(self.build["core_files"])))


if __name__ == "__main__":
    unittest.main()
