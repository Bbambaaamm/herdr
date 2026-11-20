#!/usr/bin/env python3
"""Inspect explicitly named scratch build directories; no filesystem changes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Support -I without importing an untrusted current working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herdr.build_lifecycle import BuildInventoryError, inventory


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--name", action="append", required=True)
    parser.add_argument("--max-entries", type=int, default=20000)
    parser.add_argument("--max-depth", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        report = inventory(
            args.root, tuple(args.name), max_entries=args.max_entries,
            max_depth=args.max_depth,
        )
    except (BuildInventoryError, ValueError, OSError) as error:
        print(json.dumps({
            "schema_version": "herdr-build-lifecycle-observation-v1",
            "state": "BLOCKED",
            "reason": str(error)[:140],
            "cleanup_authorized": False,
            "deletion_performed": False,
            "model_calls": 0,
        }, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
