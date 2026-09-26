from pathlib import Path
import sys

required = [
    "README.md",
    "docs/architecture/OVERVIEW.md",
    "docs/CONSUMERS.md",
    "docs/VERSIONING_AND_DEPLOYMENT.md",
    "configs/consumers/quantlab.yaml",
    "configs/consumers/majak.yaml",
    "configs/consumers/heating.yaml",
    "provenance/source-capture-20260926.txt",
    "provenance/external-runtime-dependency.txt",
    "agent_platform_dashboard",
    "deploy/agent_platform/production/launch.py",
]
missing = [p for p in required if not Path(p).exists()]

launch = Path("deploy/agent_platform/production/launch.py")
if launch.exists() and launch.parts != ("deploy", "agent_platform", "production", "launch.py"):
    missing.append("canonical deploy/agent_platform/production layout")
if missing:
    print("Missing required repository contract paths:", *missing, sep="\n- ")
    sys.exit(1)

dep = Path("provenance/external-runtime-dependency.txt").read_text(encoding="utf-8")
if "binary_sha256=" not in dep or "secrets_included" in dep:
    print("External runtime dependency provenance is incomplete.")
    sys.exit(1)

print("HERDR_REPOSITORY_CONTRACT_OK")
