"""Exact package-local native executable input and prospective root target.

The builder alone reads the frozen reference copy. Runtime operations consume
only the checked compact package; no host pathname is a fallback source.
"""
from pathlib import Path
import stat
from .case import pinned_bytes, require, sha

NATIVE_RELATIVE = "native/herdr"
NATIVE_TARGET = Path("/opt/agent-platform/herdr-offline-03414499dd0d1986/native/herdr")
NATIVE_BYTES = 26207464
NATIVE_SHA256 = "2a02fed16beb651ef006e1d43f048f652ca4dc58ad053cd2d44450563d5c54b7"


def native_source_bytes(package_root, *, root_owned=False, installed=False):
    source = Path(package_root) / NATIVE_RELATIVE
    info = source.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
            stat.S_IMODE(info.st_mode) == (0o555 if installed else 0o444) and
            info.st_size == NATIVE_BYTES, "package native input metadata changed")
    raw = pinned_bytes(source, maximum=NATIVE_BYTES, root_owned=root_owned)
    require(len(raw) == NATIVE_BYTES and sha(raw) == NATIVE_SHA256,
            "package native input changed")
    return raw
