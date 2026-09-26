#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOTS = (
    Path("agent_platform_dashboard"),
    Path("tests"),
    Path("agent-stack"),
    Path("deploy"),
    Path("runtime"),
    Path("integrations"),
    Path("scripts"),
)
FILES = (Path("package.json"), Path("package-lock.json"))
OUTPUT = Path("provenance/CANONICAL_SOURCE_MANIFEST.sha256")

entries: list[tuple[str, str]] = []
for root in ROOTS:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or "node_modules" in path.parts:
            continue
        if path == OUTPUT:
            continue
        entries.append((hashlib.sha256(path.read_bytes()).hexdigest(), path.as_posix()))
for path in FILES:
    entries.append((hashlib.sha256(path.read_bytes()).hexdigest(), path.as_posix()))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("".join(f"{digest}  {path}\n" for digest, path in sorted(entries)))
print(f"HERDR_SOURCE_MANIFEST_OK files={len(entries)}")
