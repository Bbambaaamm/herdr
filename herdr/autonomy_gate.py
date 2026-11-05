"""Read-only eligibility gate for new autonomous Herdr intake and dispatch.

This grants no execution, retry, budget, publication or deployment authority.
The separate physical-case capacity floor and margin remain unchanged.
"""
from __future__ import annotations

import os

HERDR_REPOSITORY = "Bbambaaamm/herdr"
MIN_ROOT_FREE_BYTES = 10 * 1024**3


def disk_headroom_blocker(repo: object, consumer: object) -> str | None:
    """Use non-reserved available bytes on /; unknown capacity fails closed."""
    if repo != HERDR_REPOSITORY and consumer != "herdr":
        return None
    try:
        disk = os.statvfs("/")
        fragment, available = disk.f_frsize, disk.f_bavail
        # Reject booleans, strings, floats/NaN and incomplete observations rather
        # than coercing them into an apparently sufficient capacity.
        if type(fragment) is not int or type(available) is not int or fragment <= 0 or available < 0:
            return "autonomy_disk_capacity_unavailable"
        free = available * fragment
    except (OSError, AttributeError, TypeError, ValueError, OverflowError):
        return "autonomy_disk_capacity_unavailable"
    if free < MIN_ROOT_FREE_BYTES:
        return "autonomy_disk_headroom_insufficient"
    return None
