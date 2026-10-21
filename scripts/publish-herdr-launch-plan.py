#!/usr/bin/env python3
"""Publish one independently approved launch plan; never a worker/installer hook."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herdr.launch_plan_publication import publish_approved_launch_plan

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--publish", action="store_true", help="Requires a privileged operator; never replaces an old plan")
    args = parser.parse_args()
    print(json.dumps(publish_approved_launch_plan(args.configuration, publish=args.publish), sort_keys=True))
