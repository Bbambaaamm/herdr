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
    "configs/consumers/herdr.yaml",
    "provenance/source-capture-20260926.txt",
    "provenance/external-runtime-dependency.txt",
    "provenance/quantlab-lineage/LINEAGE.json",
    "provenance/CANONICAL_SOURCE_MANIFEST.sha256",
    "herdr",
    "herdr/taskgraph.py",
    "herdr/external_knowledge.py",
    "tests/herdr/test_external_knowledge.py",
    "docs/architecture/EXTERNAL_KNOWLEDGE.md",
    "docs/architecture/TASKGRAPH.md",
    "docs/contracts/taskgraph-v1.1.schema.json",
    "agent_platform_dashboard",
    "tests/herdr",
    "tests/agent_platform_dashboard",
    "tests/test_observability_contract.py",
    "agent-stack",
    "integrations/search-router",
    "runtime",
    "package.json",
    "package-lock.json",
    "deploy/agent_platform/production/launch.py",
    "deploy/herdr/cutover/cutover.py",
    "deploy/herdr/external-knowledge.example.json",
    "herdr/external_knowledge_host.py",
    "herdr/external_knowledge_tool.py",
    "tests/herdr/test_external_knowledge_host.py",
    "tests/herdr/test_external_knowledge_tool.py",
    "tests/herdr/test_external_knowledge_work_bridge.py",
    "tests/herdr/test_external_knowledge_sandbox.py",
    "deploy/herdr/cutover/RUNBOOK.md",
    "deploy/herdr/cutover/legacy-quantlab-staging-01.sha256",
    "herdr/release.py",
    "scripts/build-herdr-release.py",
    ".github/workflows/release.yml",
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

for name in ("agent-platform-web.service", "agent-platform-export.service",
             "agent-platform-herdr.service"):
    template = Path("deploy/agent_platform/production") / f"{name}.in"
    runtime = Path("runtime") / name
    for path in (template, runtime):
        text = path.read_text(encoding="utf-8")
        if "/opt/herdr/current" not in text or "/opt/agent-platform/release" in text:
            print(f"Runtime unit bypasses atomic Herdr release symlink: {path}")
            sys.exit(1)

watchdog_source = Path("agent-stack/systemd/agent-stack-watchdog.service")
watchdog_template = Path(
    "deploy/agent_platform/production/agent-stack-watchdog.service.in"
)
watchdog_text = watchdog_source.read_text(encoding="utf-8")
if watchdog_text != watchdog_template.read_text(encoding="utf-8"):
    print("Watchdog source/template drift.")
    sys.exit(1)
for forbidden in (
    "/home/agentops/.local/bin/agent-stack-watchdog",
    "/home/agentops/.local/bin/agent-stack-ensure",
):
    if forbidden in watchdog_text:
        print(f"Watchdog bypasses atomic Herdr release: {forbidden}")
        sys.exit(1)
if "/opt/herdr/current/agent-stack/bin/agent-stack-watchdog" not in watchdog_text:
    print("Watchdog does not execute through /opt/herdr/current.")
    sys.exit(1)

installer_text = Path(
    "agent-stack/install-agent-stack-service.sh"
).read_text(encoding="utf-8")
if "/home/agentops/.local/share/agent-stack" in installer_text:
    print("Legacy installer can restore mutable watchdog ownership.")
    sys.exit(1)
if 'SCRIPT_DIR=' not in installer_text:
    print("Watchdog installer is not release-relative.")
    sys.exit(1)

dispatcher_text = Path(
    "agent-stack/bin/agent-task-dispatcher"
).read_text(encoding="utf-8")
if "/home/agentops/.local/bin/agent-task-worker" in dispatcher_text:
    print("Dispatcher bypasses immutable worker.")
    sys.exit(1)

maintenance_text = Path(
    "agent-stack/bin/hermes-maintenance"
).read_text(encoding="utf-8")
for forbidden in (
    '.local/bin/agent-codex-usage-export',
    '.local/bin/agent-task-dispatcher',
    '.local/bin/agent-task-export',
    '.local/bin/agent-github-intake',
    '.local/bin/hermes-offsite-prepare',
    '.local/bin/hermes-offsite-sync',
):
    if forbidden in maintenance_text:
        print(f"Maintenance bypasses immutable helper: {forbidden}")
        sys.exit(1)

offsite_text = Path(
    "agent-stack/bin/hermes-offsite-prepare"
).read_text(encoding="utf-8")
for forbidden in (
    '.local/bin/agent-stack-watchdog',
    '.local/bin/agent-stack-recovery',
    '.local/bin/agent-task-dispatcher',
):
    if forbidden in offsite_text:
        print(f"Off-site backup captures stale mutable runtime: {forbidden}")
        sys.exit(1)
for required in (
    "RELEASE.json",
    "MANIFEST.sha256",
    'TAR_ARGS+=(',
    '-C "$RELEASE_ROOT"',
    "COMPLETE immutable Herdr release",
):
    if required not in offsite_text:
        print(f"Off-site backup misses immutable runtime evidence: {required}")
        sys.exit(1)

release_workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")
if 'tags: ["v*"]' not in release_workflow or "build-herdr-release.py" not in release_workflow:
    print("Immutable release workflow contract is incomplete.")
    sys.exit(1)

print("HERDR_REPOSITORY_CONTRACT_OK")
