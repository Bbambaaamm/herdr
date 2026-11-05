"""Read-only source eligibility; all capacity observations are synthetic."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from herdr import autonomy_gate as gate


@pytest.mark.parametrize("available,expected", [
    (0, "autonomy_disk_headroom_insufficient"),
    (10737418239, "autonomy_disk_headroom_insufficient"),
    (10737418240, None),
    (10737418241, None),
])
def test_available_byte_boundary_is_ten_gib_not_the_physical_case_floor(monkeypatch, available, expected):
    observe = Mock(return_value=SimpleNamespace(f_frsize=1, f_bavail=available))
    monkeypatch.setattr(gate.os, "statvfs", observe, raising=False)
    assert gate.MIN_ROOT_FREE_BYTES == 10737418240
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == expected
    observe.assert_called_once_with("/")


@pytest.mark.parametrize("repo,consumer", [
    ("Bbambaaamm/herdr", "other"), ("other/repository", "herdr"), (None, "herdr"),
])
def test_either_herdr_identity_keeps_the_gate_in_scope(monkeypatch, repo, consumer):
    monkeypatch.setattr(gate.os, "statvfs", lambda _: SimpleNamespace(f_frsize=4096, f_bavail=1), raising=False)
    assert gate.disk_headroom_blocker(repo, consumer) == "autonomy_disk_headroom_insufficient"


def test_other_consumers_do_not_observe_capacity(monkeypatch):
    observe = Mock(side_effect=AssertionError("unrelated consumer must be unchanged"))
    monkeypatch.setattr(gate.os, "statvfs", observe, raising=False)
    assert gate.disk_headroom_blocker("other/repository", "other") is None
    assert gate.disk_headroom_blocker(None, None) is None
    observe.assert_not_called()


@pytest.mark.parametrize("fragment,available", [
    (0, 100000000000), (-1, -100000000000), (4096, -1),
    (True, 10737418240), (1, True), (1.0, 10737418240),
    (1, 10737418240.0), (1, float("nan")), (float("inf"), 1),
    ("4096", 100000000000), (1, "10737418240"), (None, 1), (1, None),
])
def test_invalid_observations_never_become_sufficient_capacity(monkeypatch, fragment, available):
    monkeypatch.setattr(gate.os, "statvfs", lambda _: SimpleNamespace(f_frsize=fragment, f_bavail=available), raising=False)
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == "autonomy_disk_capacity_unavailable"


@pytest.mark.parametrize("error", [OSError, PermissionError, ValueError, TypeError, OverflowError, AttributeError])
def test_unavailable_uninspectable_and_malformed_observations_fail_closed(monkeypatch, error):
    def observe(_):
        raise error("synthetic observation failure")
    monkeypatch.setattr(gate.os, "statvfs", observe, raising=False)
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == "autonomy_disk_capacity_unavailable"


def test_missing_statvfs_and_missing_fields_fail_closed(monkeypatch):
    monkeypatch.delattr(gate.os, "statvfs", raising=False)
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == "autonomy_disk_capacity_unavailable"
    monkeypatch.setattr(gate.os, "statvfs", lambda _: SimpleNamespace(f_frsize=4096), raising=False)
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == "autonomy_disk_capacity_unavailable"


def test_non_reserved_available_blocks_are_used(monkeypatch):
    # Reserved/free blocks cannot substitute for bytes available to the worker.
    monkeypatch.setattr(gate.os, "statvfs", lambda _: SimpleNamespace(
        f_frsize=4096, f_bavail=1, f_bfree=10**12, f_bsize=10**12), raising=False)
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == "autonomy_disk_headroom_insufficient"
