#!/usr/bin/env python3
"""Strict offline source preflight BEFORE an authorized Nix/uv2nix build.

Validates exact Hermes source revision and the stage2 canonical source digest.
Does not authorize release, build effects, model calls or deployment.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

COMMIT = "ef0342358f6421efb4ce919ba859d69940ca13b7"
UV = "5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590"
NPM = "193a3a3703499eb7c4b4ce48d3ba1e9dae2be62a48315c1e7ea9545e8be4a067"
FLAKE = "ac924684836cd3676fce5338149daf2d4003208b278156078889125923c901c8"
BASE = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("nonregular or symlink source")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_check(source: Path, repo: Path = BASE) -> dict:
    if source.is_symlink() or not source.is_dir():
        raise ValueError("source must be a directory, not a symlink")
    rev = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True, timeout=12
    ).strip()
    if rev != COMMIT:
        raise ValueError("HERMES_SOURCE_REVISION_MISMATCH")
    dirty = subprocess.check_output(
        ["git", "-C", str(source), "status", "--porcelain=v1"],
        timeout=12,
    )
    if dirty:
        raise ValueError("HERMES_SOURCE_WORKTREE_DIRTY")
    for filename, expected in (("uv.lock", UV), ("package-lock.json", NPM), ("flake.lock", FLAKE)):
        if sha(source / filename) != expected:
            raise ValueError("HERMES_LOCKFILE_DRIFT:" + filename)
    inventory = json.loads((repo / "herdr/hermes_source_inventory.json").read_bytes())
    filenames = inventory.get("files")
    if (type(filenames) is not list or len(filenames) != 1821
            or filenames != sorted(set(filenames), key=os.fsencode)):
        raise ValueError("HERMES_SOURCE_INVENTORY_INVALID")
    d = hashlib.sha256()
    for name in filenames:
        rel = Path(name)
        if (rel.is_absolute() or ".." in rel.parts or not name
                or any(part in ("", ".") for part in name.split("/"))):
            raise ValueError("HERMES_SOURCE_PATH_UNSAFE")
        path = source / rel
        if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("HERMES_SOURCE_FILE_MISSING_OR_UNSAFE")
        d.update(os.fsencode(name) + b"\0")
        d.update(hashlib.sha256(path.read_bytes()).digest())
    source_digest = d.hexdigest()
    if source_digest != inventory.get("source_sha256"):
        raise ValueError("HERMES_SOURCE_DIGEST_MISMATCH")
    return {
        "schema_version": "herdr-rc7-nix-input-preflight-1",
        "status": "EXACT_SOURCE_CANDIDATE_ONLY",
        "hermes_commit": rev,
        "source_files": len(filenames),
        "source_sha256": source_digest,
        "flake_lock_sha256": FLAKE,
        "uv_lock_sha256": UV,
        "npm_lock_sha256": NPM,
        "approved_for_release": False,
        "may_call_model": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-source", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = source_check(args.hermes_source.resolve(strict=True))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "BLOCKED", "reason": type(error).__name__,
                          "approved_for_release": False, "may_call_model": False},
                         sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
