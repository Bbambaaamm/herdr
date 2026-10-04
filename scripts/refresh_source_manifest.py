#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOTS = (
    Path("herdr"),
    Path("agent_platform_dashboard"),
    Path("tests"),
    Path("agent-stack"),
    Path("deploy"),
    Path("runtime"),
    Path("integrations"),
    Path("scripts"),
)
FILES = (
    Path("configs/consumers/herdr.yaml"),
    Path("docs/CONSUMERS.md"),
    Path("package.json"),
    Path("package-lock.json"),
    Path("requirements-mcp.txt"),
    Path("docs/architecture/MCP_GATEWAY.md"),
)
OUTPUT = Path("provenance/CANONICAL_SOURCE_MANIFEST.sha256")
TEXT_SUFFIXES = {
    ".txt", ".css", ".html", ".in", ".js", ".json", ".md", ".mjs", ".py",
    ".service", ".sh", ".sha256", ".yaml",
}


def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix in TEXT_SUFFIXES or not path.suffix:
        data.decode("utf-8")
        return data.replace(b"\r\n", b"\n")
    if path.suffix != ".webp":
        raise ValueError(f"Unclassified manifest file type: {path}")
    return data

entries: list[tuple[str, str]] = []
for root in ROOTS:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or "node_modules" in path.parts:
            continue
        if path == OUTPUT:
            continue
        entries.append((hashlib.sha256(canonical_bytes(path)).hexdigest(), path.as_posix()))
for path in FILES:
    entries.append((hashlib.sha256(canonical_bytes(path)).hexdigest(), path.as_posix()))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_bytes("".join(f"{digest}  {path}\n" for digest, path in sorted(entries)).encode("ascii"))
print(f"HERDR_SOURCE_MANIFEST_OK files={len(entries)}")
