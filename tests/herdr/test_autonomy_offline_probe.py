"""False-green regressions for the advisory #184 offline acceptance entrypoint."""
import importlib.util
from pathlib import Path
import subprocess
import os
import sys
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


def test_every_required_parameter_variant_must_be_present_and_pass():
    suite = junit()
    variants = [r for r in suite if r.get("name").startswith("test_lost_remote_reply_reconciles")]
    assert len(variants) == 4
    assert evaluate(suite)["status"] == "OFFLINE_CONTRACTS_PASSED"
    suite.remove(variants[0])
    assert evaluate(suite)["gates"]["ambiguous_delivery"]["status"] == "BLOCKED"
    suite = junit()
    variant = next(r for r in suite if r.get("name").endswith("[False-create]"))
    ET.SubElement(variant, "skipped")
    assert evaluate(suite)["status"] == "BLOCKED"


def test_wrong_class_or_similar_test_name_cannot_cover_required_selector():
    suite = junit()
    suite[0].set("name", suite[0].get("name") + "_not_the_test")
    assert evaluate(suite)["status"] == "BLOCKED"


def test_inherited_selection_overrides_and_explicit_plugins_are_removed(monkeypatch, tmp_path):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--deselect=secretly-missing-variant")
    monkeypatch.setenv("PYTEST_PLUGINS", "unapproved_plugin")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "0")
    monkeypatch.setenv("HERDR_UNRELATED_VALUE", "keep")
    monkeypatch.setenv("HERDR_BOUNDARY_TEST_ROOT", "/no-such-live-workspace")
    env = probe.test_environment(tmp_path / "private-boundary")
    assert "PYTEST_ADDOPTS" not in env and "PYTEST_PLUGINS" not in env
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert env["HERDR_UNRELATED_VALUE"] == "keep"
    assert env["HERDR_BOUNDARY_TEST_ROOT"] == str(tmp_path / "private-boundary")


def test_blocked_report_explains_skips_without_turning_them_into_success():
    suite = junit()
    ET.SubElement(suite[0], "skipped", message="physical Git boundary workspace unavailable")
    report = evaluate(suite)
    assert report["status"] == "BLOCKED"
    assert report["test_outcomes"] == {"failure": 0, "error": 0, "skipped": 1}
    assert report["blocked_gates"] == ["duplicate_event"]
    assert report["blocked_test_outcomes"][0]["reason"] == "physical Git boundary workspace unavailable"


@pytest.mark.skipif(os.name != "posix", reason="actual Linux process-group boundary")
@pytest.mark.parametrize("failure", ["interrupt", "timeout", "unexpected"])
def test_interruption_timeout_and_exception_kill_and_reap_actual_child(tmp_path, monkeypatch, failure):
    popen = subprocess.Popen
    children = []
    def start(*args, **kwargs):
        child = popen(*args, **kwargs)
        children.append(child)
        wait = child.wait
        first = True
        def interrupted(*args, **kwargs):
            nonlocal first
            if first:
                first = False
                if failure == "interrupt":
                    raise KeyboardInterrupt()
                if failure == "timeout":
                    raise subprocess.TimeoutExpired(child.args, 900)
                raise RuntimeError("supervisor failure")
            return wait(*args, **kwargs)
        child.wait = interrupted
        return child
    monkeypatch.setattr(probe.subprocess, "Popen", start)
    with (tmp_path / "child.log").open("wb") as log:
        args = ([sys.executable, "-c", "import time; time.sleep(60)"], tmp_path, os.environ.copy(), log)
        if failure == "unexpected":
            with pytest.raises(RuntimeError, match="supervisor"):
                probe.run_tests(*args)
        else:
            assert probe.run_tests(*args) == (130 if failure == "interrupt" else 124)
    assert len(children) == 1 and children[0].poll() is not None


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


def collection_log():
    return ("\n".join(dict.fromkeys(s for group in probe.CASES.values() for s in group)) + "\n").encode()


def test_collection_inventory_cannot_be_mistaken_for_executed_contracts():
    report = probe.evaluate_collection(collection_log(), 0, SOURCE, SOURCE)
    assert report["status"] == "COLLECTION_VALIDATED"
    assert report["schema_version"] != probe.SCHEMA
    assert report["evidence_level"] == "offline_test_collection"
    assert report["collection_only"] and report["collection_complete"]
    assert report["verified_gates"] == report["testcases"] == 0
    assert all(g["status"] == "NOT_EXECUTED" for g in report["gates"].values())
    assert report["full_autonomy_verified"] is report["live_dispatch_authorized"] is False


@pytest.mark.parametrize("fault", ["missing", "duplicate", "unexpected", "exit_code", "source_drift"])
def test_incomplete_or_rebound_collection_is_blocked(fault):
    raw = collection_log()
    code, after = 0, SOURCE
    if fault == "missing": raw = b"\n".join(raw.splitlines()[1:])
    elif fault == "duplicate": raw += raw.splitlines()[0] + b"\n"
    elif fault == "unexpected": raw += b"tests/foreign.py::test_not_authorized\n"
    elif fault == "exit_code": code = 2
    elif fault == "source_drift": after = {**SOURCE, "head": "changed"}
    report = probe.evaluate_collection(raw, code, SOURCE, after)
    assert report["status"] == "BLOCKED"
    assert report["verified_gates"] == report["testcases"] == 0
