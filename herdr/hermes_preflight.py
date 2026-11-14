"""Bounded read-only Hermes source-presence preflight for native bootstrap.

Presence alone does NOT attest provenance; exact source digests, executable
identity and immutable mount roots must still be verified by stage1/stage2.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import stat


class HermesSourcePreflightError(ValueError):
    pass


def preflight_pinned_hermes_source(inventory_path: Path, hermes_root: Path) -> dict:
    inventory_path = Path(inventory_path)
    hermes_root = Path(hermes_root)
    raw = inventory_path.read_bytes()
    if len(raw) > 1_048_576:
        raise HermesSourcePreflightError("PINNED_HERMES_INVENTORY_OVERSIZED")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise HermesSourcePreflightError("PINNED_HERMES_INVENTORY_INVALID") from exc
    names = data.get("files") if type(data) is dict else None
    if type(names) is not list or not 1 <= len(names) <= 10_000:
        raise HermesSourcePreflightError("PINNED_HERMES_INVENTORY_INVALID")
    if (any(type(item) is not str for item in names)
            or names != sorted(set(names))):
        raise HermesSourcePreflightError("PINNED_HERMES_INVENTORY_INVALID")
    for name in names:
        rel = PurePosixPath(name)
        if (not name or name.startswith("/") or "\\" in name or
                any(part in (".", "..", "") for part in name.split("/")) or
                rel.as_posix() != name):
            raise HermesSourcePreflightError("PINNED_HERMES_INVENTORY_INVALID")
        target = hermes_root / name
        try:
            info = target.lstat()
        except FileNotFoundError as exc:
            raise HermesSourcePreflightError(
                f"PINNED_HERMES_SOURCE_FILE_MISSING: {name}") from exc
        if not stat.S_ISREG(info.st_mode):
            raise HermesSourcePreflightError(
                f"PINNED_HERMES_SOURCE_FILE_NOT_REGULAR: {name}")
    return {"status": "PRESENCE_PASS_ONLY", "count": len(names)}
