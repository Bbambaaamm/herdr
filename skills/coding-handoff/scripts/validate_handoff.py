import json, sys
data = json.load(sys.stdin)
required = {"base_revision", "acceptance", "changed_paths", "checks", "unresolved"}
if not isinstance(data, dict) or set(data) != required:
    raise SystemExit(1)
if not isinstance(data["base_revision"], str) or len(data["base_revision"]) != 40:
    raise SystemExit(1)
if not all(isinstance(data[k], list) for k in required - {"base_revision"}):
    raise SystemExit(1)
print("handoff_shape_valid")
