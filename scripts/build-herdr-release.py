#!/usr/bin/env python3
"""Build one deterministic release archive from an annotated Herdr tag."""
from argparse import ArgumentParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from herdr.release import ReleaseError, build_release  # noqa: E402


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build_release(ROOT, args.tag, args.commit, args.output.resolve())
    except (OSError, ReleaseError, ValueError) as exc:
        print(f"release_build_failed:{exc}", file=sys.stderr)
        return 78
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
