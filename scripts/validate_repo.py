from pathlib import Path
import json
import sys

required = [
    "README.md",
    "docs/architecture/OVERVIEW.md",
    "docs/CONSUMERS.md",
    "docs/VERSIONING_AND_DEPLOYMENT.md",
    "docs/migration/QUANTLAB_LINEAGE.md",
    "configs/consumers/quantlab.yaml",
    "configs/consumers/majak.yaml",
    "configs/consumers/heating.yaml",
    "provenance/source-capture-20260926.txt",
    "provenance/external-runtime-dependency.txt",
    "provenance/quantlab-lineage/LINEAGE.json",
    "provenance/CANONICAL_SOURCE_MANIFEST.sha256",
    "agent_platform_dashboard",
    "tests/agent_platform_dashboard",
    "tests/test_observability_contract.py",
    "agent-stack",
    "integrations/search-router",
    "runtime",
    "package.json",
    "package-lock.json",
    "deploy/agent_platform/production/launch.py",
]
missing = [p for p in required if not Path(p).exists()]
if missing:
    print("Missing required repository contract paths:", *missing, sep="\n- ")
    sys.exit(1)

launch = Path("deploy/agent_platform/production/launch.py")
if launch.parts != ("deploy", "agent_platform", "production", "launch.py"):
    print("Canonical deploy layout is invalid.")
    sys.exit(1)

dep = Path("provenance/external-runtime-dependency.txt").read_text(encoding="utf-8")
if "binary_sha256=" not in dep or "secrets_included" in dep:
    print("External runtime dependency provenance is incomplete.")
    sys.exit(1)

lineage = json.loads(Path("provenance/quantlab-lineage/LINEAGE.json").read_text())
if lineage["platform_baseline"]["commit"] != "41179635c8654a60c5d9234acccb6e91b2028b72":
    print("Unexpected platform lineage.")
    sys.exit(1)
if lineage["search_router"]["commit"] != "3c1dac1c1d96693cf0903b80acdfc169e391a58d":
    print("Unexpected Search Router lineage.")
    sys.exit(1)

package = json.loads(Path("package.json").read_text())
if package.get("packageManager") != "npm@11.17.0":
    print("Unexpected npm version contract.")
    sys.exit(1)

print("HERDR_REPOSITORY_CONTRACT_OK")
