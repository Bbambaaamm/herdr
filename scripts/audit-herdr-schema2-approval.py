#!/usr/bin/env python3
"""Inspect root-owned schema-2 readiness only. Exit 2 until authority exists."""
import json
from pathlib import Path
import sys

if not sys.flags.isolated or not sys.dont_write_bytecode:
    raise SystemExit("isolated interpreter -I -B required")
sys.path.insert(0, str(Path(__file__).resolve(strict=True).parents[1]))
from herdr.schema2_approval_audit import read_current
from herdr.security import SecurityError

if __name__ == "__main__":
    try:
        report = read_current()
    except (OSError, ValueError, SecurityError) as exc:
        print(json.dumps({"status": "ROOT_PREFLIGHT_BLOCKED", "error": type(exc).__name__}))
        raise SystemExit(2)
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["status"] == "STATIC_GATES_PASS_NATIVE_E2E_PENDING" else 2)
