#!/usr/bin/env python3
"""Validate package contents. Lint success does not approve a skill for execution."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herdr.skills import SkillError, lint_package


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packages", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        for package in args.packages:
            print(json.dumps(lint_package(package), sort_keys=True))
    except (SkillError, OSError) as exc:
        print(f"skill_validation_failed:{exc}", file=sys.stderr)
        return 78
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
