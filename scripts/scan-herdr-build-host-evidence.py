#!/usr/bin/env python3
"""Read-only phase 2 host-evidence scan; no cleanup permission ever issued."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# -I excludes the script directory from imports: add only pinned project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from herdr.build_lifecycle import BuildInventoryError
from herdr.build_lifecycle_host_evidence import (
    BuildHostEvidenceError, host_evidence_scan,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--name", action="append", required=True)
    parser.add_argument("--max-entries", type=int, default=20000)
    parser.add_argument("--max-depth", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        result = host_evidence_scan(
            args.root, tuple(args.name), max_entries=args.max_entries,
            max_depth=args.max_depth,
        )
    except (BuildInventoryError, BuildHostEvidenceError, OSError, ValueError) as exc:
        print(json.dumps({
            "schema_version": "herdr-build-host-evidence-observation-v1",
            "status": "BLOCKED",
            "reason": type(exc).__name__,
            "cleanup_authorized": False,
            "deletion_performed": False,
            "model_calls": 0,
        }, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
