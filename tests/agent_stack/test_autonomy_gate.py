"""Capacity-based autonomous activation must fail closed without spending tokens."""
import sys
from pathlib import Path
from types import SimpleNamespace

BIN = Path(__file__).resolve().parents[2] / "agent-stack" / "bin"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

import agent_autonomy_gate as gate


def test_low_headroom_blocks_only_herdr(monkeypatch):
    monkeypatch.setattr(gate.os, "statvfs",
                        lambda _: SimpleNamespace(f_frsize=4096, f_bavail=3))
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == (
        "autonomy_disk_headroom_insufficient"
    )
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "wrong") == (
        "autonomy_disk_headroom_insufficient"
    )
    assert gate.disk_headroom_blocker("other/repo", "herdr") == (
        "autonomy_disk_headroom_insufficient"
    )
    assert gate.disk_headroom_blocker("other/repo", "other") is None


def test_high_headroom_permits_herdr_scheduler_preflight_only(monkeypatch):
    monkeypatch.setattr(gate.os, "statvfs",
                        lambda _: SimpleNamespace(f_frsize=4096,
                                                   f_bavail=gate.MIN_ROOT_FREE_BYTES // 4096))
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") is None


def test_unavailable_or_invalid_capacity_fails_closed(monkeypatch):
    def unavailable(_):
        raise OSError("mount unavailable")
    monkeypatch.setattr(gate.os, "statvfs", unavailable)
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == (
        "autonomy_disk_capacity_unavailable"
    )
    monkeypatch.setattr(gate.os, "statvfs",
                        lambda _: SimpleNamespace(f_frsize=0, f_bavail=1))
    assert gate.disk_headroom_blocker("Bbambaaamm/herdr", "herdr") == (
        "autonomy_disk_capacity_unavailable"
    )
