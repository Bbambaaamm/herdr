#!/usr/bin/env python3
"""Validate package contents. Lint success does not approve a skill for execution."""
import argparse
import json
from pathlib import Path
import sys
import stat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herdr.skills import SkillError, lint_package


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packages", nargs="*", type=Path)
    parser.add_argument("--all", dest="package_root", type=Path,
                        help="Lint every direct package directory, rejecting non-directory entries")
    args = parser.parse_args()
    try:
        packages = list(args.packages)
        if args.package_root is not None:
            if not stat.S_ISDIR(args.package_root.lstat().st_mode):
                raise SkillError("package_root_not_directory")
            for package in sorted(args.package_root.iterdir()):
                if not stat.S_ISDIR(package.lstat().st_mode):
                    raise SkillError("package_entry_not_directory")
                packages.append(package)
        if not packages:
            raise SkillError("no_packages")
        for package in packages:
            print(json.dumps(lint_package(package), sort_keys=True))
    except (SkillError, OSError) as exc:
        print(f"skill_validation_failed:{exc}", file=sys.stderr)
        return 78
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
