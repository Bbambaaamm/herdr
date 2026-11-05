"""Bounded aggregate case unit; actual workers use separate owned PTY units.

This is not a worker or dispatcher. Its identity anchors the original case unit
receipt while canonical ROOT/CHILD execute via their independently pinned prep.
"""
import signal
import time
from .case import require


def main():
    import os
    from pathlib import Path
    from herdr.host_configuration import _read_configuration
    from .case import NONCE
    require(os.geteuid() == 0, "root case anchor required")
    base = Path("/var/lib/herdr-offline-03414499dd0d1986")
    state = _read_configuration(base / "state.json")
    authority = _read_configuration(base / "authority.json")
    require(state["phase"] == "START_INTENT" and state["binding"]["nonce"] == NONCE,
            "consumed original case start intent required")
    remaining = int(authority["deadline"] - time.time())
    require(0 < remaining <= 1800, "finite case anchor deadline required")
    signal.alarm(remaining)
    while time.time() < authority["deadline"]:
        signal.pause()
    raise SystemExit(1)
