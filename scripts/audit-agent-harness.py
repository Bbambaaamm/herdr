#!/usr/bin/env python3
"""Read-only audit for the VS Code + Hermes CVM Harness v2026.10.1."""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

MARKER = "## VS Code + Hermes CVM Harness v2026.10.1"
HOOK = str(Path.home() / ".hermes" / "agent-hooks" / "cvm-evidence-gate.py")
IDEAL_TOOL_LIMIT = 80
HERMES_ROOT = Path.home() / ".hermes"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def hcmd(profile: str | None, *args: str) -> list[str]:
    return ["hermes", *([] if profile is None else ["-p", profile]), *args]


def get_config(profile: str | None, key: str) -> tuple[int, str]:
    p = run(hcmd(profile, "config", "get", key))
    return p.returncode, (p.stdout or p.stderr).strip()


def prompt_snapshot(profile: str | None) -> dict:
    p = run(hcmd(profile, "prompt-size", "--platform", "cli", "--json"))
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return json.loads(p.stdout)


def stable_section(snapshot: dict) -> list:
    return next((s for s in snapshot.get("sections", []) if s[0].startswith("stable")), [])


def profile_home(profile: str | None) -> Path:
    return HERMES_ROOT if profile is None else HERMES_ROOT / "profiles" / profile


def audit_profile(profile: str | None) -> tuple[dict, list[str]]:
    label = profile or "default"
    home = profile_home(profile)
    issues: list[str] = []
    first, second = prompt_snapshot(profile), prompt_snapshot(profile)
    tools = first.get("tools", {})
    tool_count = int(tools.get("count", -1))
    stable = stable_section(first)
    prefix_stable = tools == second.get("tools", {}) and stable == stable_section(second)

    soul = home / "SOUL.md"
    marker_present = soul.is_file() and MARKER in soul.read_text(encoding="utf-8")
    if not marker_present:
        issues.append(f"{label}: harness marker missing from SOUL.md")
    if tool_count < 0 or tool_count > IDEAL_TOOL_LIMIT:
        issues.append(f"{label}: active tool schemas={tool_count}, limit={IDEAL_TOOL_LIMIT}")
    if not prefix_stable:
        issues.append(f"{label}: stable prompt/tool snapshot changed across consecutive offline probes")

    hard_rc, hard = get_config(profile, "tool_loop_guardrails.hard_stop_enabled")
    if hard_rc or hard.lower() != "true":
        issues.append(f"{label}: interactive hard-stop guard is not enabled")

    hook_rc, hook_cfg = get_config(profile, "hooks.pre_verify")
    if hook_rc or HOOK not in hook_cfg:
        issues.append(f"{label}: CVM pre_verify hook is not configured")
    hook_list = run(hcmd(profile, "hooks", "list"))
    hook_allowed = hook_list.returncode == 0 and HOOK in hook_list.stdout and "allowed" in hook_list.stdout
    if not hook_allowed:
        issues.append(f"{label}: CVM pre_verify hook is not allowlisted")

    auto_rc, auto = get_config(profile, "hooks_auto_accept")
    if auto_rc or auto.lower() != "false":
        issues.append(f"{label}: hooks_auto_accept must remain false")

    env_path = home / ".env"
    env_mode = None
    if env_path.exists():
        env_mode = stat.S_IMODE(env_path.stat().st_mode)
        if env_mode & 0o077:
            issues.append(f"{label}: .env permissions are broader than owner-only")

    return {
        "profile": label,
        "tool_count": tool_count,
        "tool_schema_bytes": tools.get("json_bytes"),
        "stable_section": stable,
        "prefix_stable_observed": prefix_stable,
        "harness_marker": marker_present,
        "hard_stop_enabled": hard_rc == 0 and hard.lower() == "true",
        "pre_verify_hook_configured": hook_rc == 0 and HOOK in hook_cfg,
        "pre_verify_hook_allowlisted": hook_allowed,
        "hooks_auto_accept": None if auto_rc else auto.lower() == "true",
        "env_mode_octal": None if env_mode is None else oct(env_mode),
    }, issues


def main() -> int:
    profiles: list[str | None] = [None]
    root = HERMES_ROOT / "profiles"
    if root.is_dir():
        profiles += sorted(
            p.name for p in root.iterdir()
            if p.is_dir() and (p / "config.yaml").is_file() and (p / "SOUL.md").is_file()
        )

    results, issues = [], []
    for profile in profiles:
        result, found = audit_profile(profile)
        results.append(result)
        issues.extend(found)

    hook = Path(HOOK)
    hook_mode = stat.S_IMODE(hook.stat().st_mode) if hook.exists() else None
    hook_executable = hook.is_file() and os.access(hook, os.X_OK)
    if not hook_executable:
        issues.append("CVM hook script is missing or not executable")

    stale_rc, _ = get_config(None, "code_execution.max_tool_calls")
    stale_key_removed = stale_rc != 0
    if not stale_key_removed:
        issues.append("obsolete code_execution.max_tool_calls is still configured")

    report = {
        "harness": "v2026.10.1",
        "ideal_tool_limit": IDEAL_TOOL_LIMIT,
        "profiles": results,
        "hook": {"path": HOOK, "mode_octal": None if hook_mode is None else oct(hook_mode),
                 "executable": hook_executable},
        "obsolete_code_execution_max_tool_calls_removed": stale_key_removed,
        "issues": issues,
        "gate_status": "PASS" if not issues else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
