#!/usr/bin/env python3
"""Explicit release operator helper; never called by workers or installers."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herdr.runtime_publication import publish_reviewed_runtime

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--publish", action="store_true",
                        help="Create a new immutable version; requires a privileged release operator")
    args = parser.parse_args()
    print(json.dumps(publish_reviewed_runtime(args.configuration, publish=args.publish), sort_keys=True))
