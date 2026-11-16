"""Fail-closed source inventory preflight, without any model or bootstrap."""
import json
from pathlib import Path

import pytest

from herdr.hermes_preflight import (
    HermesSourcePreflightError, preflight_pinned_hermes_source,
)


def inventory(tmp_path, names):
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({"files": names}))
    return path


def test_preflight_requires_all_exact_source_paths(tmp_path):
    root = tmp_path / "runtime"
    (root / "agent").mkdir(parents=True)
    (root / "agent/__init__.py").write_text("")
    path = inventory(tmp_path, ["agent/__init__.py", "agent/host_reference.py"])
    with pytest.raises(
        HermesSourcePreflightError,
        match=r"PINNED_HERMES_SOURCE_FILE_MISSING: agent/host_reference.py",
    ):
        preflight_pinned_hermes_source(path, root)
    (root / "agent/host_reference.py").write_text("candidate only")
    assert preflight_pinned_hermes_source(path, root) == {
        "status": "PRESENCE_PASS_ONLY", "count": 2,
    }


@pytest.mark.parametrize("name", [
    "../outside.py", "/etc/passwd", "agent//bad.py", "agent/./bad.py",
    "agent/../bad.py", "agent\\bad.py",
])
def test_preflight_denies_noncanonical_inventory_path(tmp_path, name):
    root = tmp_path / "runtime"
    root.mkdir()
    with pytest.raises(HermesSourcePreflightError, match="INVENTORY_INVALID"):
        preflight_pinned_hermes_source(inventory(tmp_path, [name]), root)


def test_preflight_denies_symlink_or_missing_file(tmp_path):
    root = tmp_path / "runtime"
    root.mkdir()
    (root / "alias.py").symlink_to("/etc/passwd")
    with pytest.raises(HermesSourcePreflightError, match="NOT_REGULAR"):
        preflight_pinned_hermes_source(inventory(tmp_path, ["alias.py"]), root)


def test_historical_rc6_missing_host_reference_is_detected():
    root = Path("/opt/herdr/releases/p0-5035d92-test/hermes")
    inventory_path = Path(__file__).resolve().parents[2] / "herdr/hermes_source_inventory.json"
    if not root.exists():
        pytest.skip("historical staging Hermes not mounted")
    if (root / "agent/host_reference.py").exists():
        pytest.skip("historical Hermes changed; review pin provenance")
    with pytest.raises(
        HermesSourcePreflightError,
        match="PINNED_HERMES_SOURCE_FILE_MISSING: agent/host_reference.py",
    ):
        preflight_pinned_hermes_source(inventory_path, root)
