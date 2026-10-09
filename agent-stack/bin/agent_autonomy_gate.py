#!/usr/bin/env python3
"""Read-only capacity gate for autonomous Herdr work.

This never authorizes a model invocation, GitHub write, retry or release.
Durable admission, cumulative budget and result reconciliation remain
authoritative. Only blocks new dispatch while staging is unsafe.
"""
from __future__ import annotations

import os

HERDR_REPOSITORY = "Bbambaaamm/herdr"
MIN_ROOT_FREE_BYTES = 10 * 1024 ** 3


def disk_headroom_blocker(repo: object, consumer: object) -> str | None:
    """Return a bounded reason or None; unknown disk state fails closed."""
    if repo != HERDR_REPOSITORY and consumer != "herdr":
        return None
    try:
        disk = os.statvfs("/")
        free = disk.f_bavail * disk.f_frsize
        if disk.f_frsize <= 0 or free < 0:
            return "autonomy_disk_capacity_unavailable"
    except (OSError, AttributeError, ValueError, OverflowError):
        return "autonomy_disk_capacity_unavailable"
    if free < MIN_ROOT_FREE_BYTES:
        return "autonomy_disk_headroom_insufficient"
    return None
