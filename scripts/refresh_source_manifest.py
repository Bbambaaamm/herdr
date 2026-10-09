#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import stat

ROOTS = (
    Path("herdr"),
    Path("skills"),
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
    Path("docs/architecture/A2A_GATEWAY_71.md"),
    Path("docs/architecture/AGENT_SKILLS.md"),
    Path("docs/architecture/CONTEXT_MEMORY.md"),
    Path("docs/architecture/INVOCATION_POLICY_LAUNCH.md"),
    Path("docs/architecture/IMMUTABLE_PROFILE_NAMESPACE_129.md"),
    Path("docs/architecture/PROFILE_HANDOFF_132.md"),
    Path("docs/architecture/COMPLETION_EVIDENCE.md"),
    Path("docs/architecture/PROMPT_RUNTIME.md"),

    Path("docs/architecture/WORK_NODE_CONTRACT.md"),
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
    if path.parts[:1] == ("skills",):
        # Skill hashes bind exact resource bytes, including binary assets and
        # text line endings; their contract is independent of filename suffix.
        manifest_path = Path(*path.parts[:2]) / "manifest.json"
        if path != manifest_path:
            manifest = json.loads(manifest_path.read_bytes())
            relative = path.relative_to(manifest_path.parent).as_posix()
            entry = next((x for x in manifest["files"] if x["path"] == relative), None)
            if entry is None or entry["size"] != len(data) or entry["sha256"] != hashlib.sha256(data).hexdigest():
                raise ValueError(f"Undeclared or changed skill source file: {path}")
        return data
    if path.suffix in TEXT_SUFFIXES or not path.suffix:
        data.decode("utf-8")
        return data.replace(b"\r\n", b"\n")
    if path.suffix != ".webp":
        raise ValueError(f"Unclassified manifest file type: {path}")
    return data

entries: list[tuple[str, str]] = []
for root in ROOTS:
    if root == Path("skills") and (root.exists() or root.is_symlink()) and not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError(f"Non-directory skill source root: {root}")
    for path in sorted(root.rglob("*")):
        if root == Path("skills"):
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise ValueError(f"Nonregular skill source entry: {path}")
        elif not path.is_file():
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
