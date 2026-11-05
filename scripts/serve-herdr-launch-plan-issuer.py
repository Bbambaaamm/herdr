#!/usr/bin/env python3
"""Operator-started extension of the existing root-owned plan authority.

Run only from an approved immutable code release and pinned interpreter.
Installation/activation requires the existing privileged release approval.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve(strict=True).parents[1]))
from herdr.launch_plan_issuer import serve

if __name__ == "__main__":
    serve()
