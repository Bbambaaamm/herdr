#!/usr/bin/env python3
"""Read-only historical runtime publication inventory; never an approval."""
import json
from pathlib import Path
import sys
if not sys.flags.isolated or not sys.dont_write_bytecode:
    raise SystemExit('python -I -B required')
sys.path.insert(0, str(Path(__file__).resolve(strict=True).parents[1]))
from herdr.runtime_reuse_audit import audit_historical_publications
print(json.dumps(audit_historical_publications(), sort_keys=True))
