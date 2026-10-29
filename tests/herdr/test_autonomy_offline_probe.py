"""False-green regressions for the advisory #184 offline acceptance entrypoint."""
import importlib.util
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/probe-herdr-autonomy-offline.py"
spec = importlib.util.spec_from_file_location("autonomy_offline_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
SOURCE = {"head": "a" * 40, "tree": "b" * 40, "tracked_bytes_sha256": "c" * 64}


def junit():
    suite = ET.Element("testsuite")
    for selector in dict.fromkeys(s for group in probe.CASES.values() for s in group):
        path, *parts = selector.split("::")
        name = path.removesuffix(".py").replace("/", ".")
        if len(parts) == 2:
            name += "." + parts[0]
        ET.SubElement(suite, "testcase", classname=name, name=parts[-1])
    return suite


def evaluate(suite, code=0, after=SOURCE):
    return probe.evaluate_junit(ET.tostring(suite), code, SOURCE, after)


def test_complete_component_evidence_cannot_claim_native_or_live_autonomy():
    report = evaluate(junit())
    assert report["status"] == "OFFLINE_CONTRACTS_PASSED"
    assert report["verified_gates"] == report["required_gates"] == 14
    assert report["evidence_level"] == "offline_component_contracts"
    for field in ("full_autonomy_verified", "native_sdk_cycle_verified",
                  "live_dispatch_authorized", "merge_authorized", "deployment_authorized"):
        assert report[field] is False
    assert report["historical_cost_and_tokens"] == "UNKNOWN"


@pytest.mark.parametrize("tag", ["skipped", "error", "failure"])
def test_success_exit_cannot_hide_xfail_skip_or_failed_required_test(tag):
    suite = junit()
    ET.SubElement(suite[0], tag)
    report = evaluate(suite)
    assert report["status"] == "BLOCKED"
    assert report["gates"]["duplicate_event"]["status"] == "BLOCKED"


def test_partial_junit_and_deselected_required_test_never_pass():
    suite = junit()
    suite.remove(suite[0])
    assert evaluate(suite)["status"] == "BLOCKED"
    assert probe.evaluate_junit(b"<testsuite", 0, SOURCE, SOURCE)["junit_parse_error"]
    assert probe.evaluate_junit(b"<testsuite />", 0, SOURCE, SOURCE)["status"] == "BLOCKED"


@pytest.mark.parametrize("code", [1, 2, 3, 4, 5, 124, -9])
def test_collection_failure_interruption_or_timeout_cannot_use_partial_passes(code):
    report = evaluate(junit(), code=code)
    assert report["verified_gates"] == 14
    assert report["status"] == "BLOCKED"


@pytest.mark.parametrize("field", list(SOURCE))
def test_posttest_source_head_tree_or_byte_drift_invalidates_report(field):
    report = evaluate(junit(), after={**SOURCE, field: "changed"})
    assert report["source_unchanged"] is False
    assert report["status"] == "BLOCKED"


def test_posttest_uninspectable_checkout_is_not_same_source():
    assert evaluate(junit(), after={"inspection_failed": True})["status"] == "BLOCKED"


def test_duplicate_result_cannot_cover_missing_or_repeat_a_required_test():
    suite = junit()
    ET.SubElement(suite, "testcase", **suite[0].attrib)
    report = evaluate(suite)
    assert report["duplicate_testcase"] is True
    assert report["status"] == "BLOCKED"


def test_every_reported_parameter_variant_must_pass():
    suite = junit()
    original = suite[0]
    name = original.get("name")
    original.set("name", name + "[one]")
    variant = ET.SubElement(suite, "testcase", classname=original.get("classname"), name=name + "[two]")
    assert evaluate(suite)["status"] == "OFFLINE_CONTRACTS_PASSED"
    ET.SubElement(variant, "skipped")
    assert evaluate(suite)["status"] == "BLOCKED"


def test_wrong_class_or_similar_test_name_cannot_cover_required_selector():
    suite = junit()
    suite[0].set("name", suite[0].get("name") + "_not_the_test")
    assert evaluate(suite)["status"] == "BLOCKED"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True).stdout


def test_source_inventory_rejects_dirty_untracked_and_changed_oracle(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Offline fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    (tmp_path / "oracle.py").write_text("assert True\n")
    git(tmp_path, "add", "oracle.py")
    git(tmp_path, "commit", "-qm", "baseline")
    before = probe.source_snapshot(tmp_path)
    assert before == probe.source_snapshot(tmp_path)
    (tmp_path / "oracle.py").write_text("assert False\n")
    with pytest.raises(ValueError, match="clean"):
        probe.source_snapshot(tmp_path)
    git(tmp_path, "add", "oracle.py")
    git(tmp_path, "commit", "-qm", "changed oracle")
    after = probe.source_snapshot(tmp_path)
    assert before["tracked_bytes_sha256"] != after["tracked_bytes_sha256"]
    (tmp_path / "extra.py").write_text("unreviewed\n")
    with pytest.raises(ValueError, match="clean"):
        probe.source_snapshot(tmp_path)
