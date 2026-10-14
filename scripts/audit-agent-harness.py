#!/usr/bin/env python3
"""Read-only audit for the VS Code + Hermes CVM Harness v2026.10.1."""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

MARKER = "## VS Code + Hermes CVM Harness v2026.10.1"
HERMES_ROOT = Path.home() / ".hermes"
HERMES_AGENT_ROOT = Path(
    os.environ.get("HERMES_AGENT_ROOT", str(HERMES_ROOT / "hermes-agent"))
)
HERMES_PYTHON = HERMES_AGENT_ROOT / "venv" / "bin" / "python"
HOOK = str(HERMES_ROOT / "agent-hooks" / "cvm-evidence-gate.py")
HARD_TOOL_LIMIT = 100
IDEAL_TOOL_LIMIT = 80
APPROVED_UNMAPPED_TOOLS = {"tool_search", "tool_describe", "tool_call"}
COMMAND_TIMEOUT_SECONDS = 30

FINGERPRINT_HELPER = textwrap.dedent(
    """
    import hashlib
    import json
    from hermes_cli.prompt_size import _build_inspection_agent, _tool_name
    from agent.system_prompt import build_system_prompt_parts
    from tools.registry import registry

    agent = _build_inspection_agent("cli")
    parts = build_system_prompt_parts(agent)
    stable = parts.get("stable", "")
    tools = getattr(agent, "tools", None) or []
    canonical_tools = json.dumps(
        tools, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    mapping = registry.get_tool_to_toolset_map()
    unmapped = sorted(_tool_name(tool) for tool in tools if not mapping.get(_tool_name(tool)))
    print(json.dumps({
        "stable_sha256": hashlib.sha256(stable.encode("utf-8")).hexdigest(),
        "stable_bytes": len(stable.encode("utf-8")),
        "tool_schema_sha256": hashlib.sha256(canonical_tools).hexdigest(),
        "tool_schema_bytes_canonical": len(canonical_tools),
        "tool_count": len(tools),
        "unmapped_tool_names": unmapped,
    }, sort_keys=True))
    """
)


def run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            text=True,
            capture_output=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
            env=env,
            cwd=None if cwd is None else str(cwd),
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            args=args,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=f"timeout after {COMMAND_TIMEOUT_SECONDS}s",
        )


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


def profile_home(profile: str | None) -> Path:
    return HERMES_ROOT if profile is None else HERMES_ROOT / "profiles" / profile


def runtime_fingerprint(profile: str | None) -> dict:
    if not HERMES_PYTHON.is_file():
        raise RuntimeError(f"Hermes inspection interpreter missing: {HERMES_PYTHON}")
    env = os.environ.copy()
    env["HERMES_HOME"] = str(profile_home(profile))
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    p = run(
        [str(HERMES_PYTHON), "-c", FINGERPRINT_HELPER],
        env=env,
        cwd=HERMES_AGENT_ROOT,
    )
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return json.loads(p.stdout)


def hook_is_allowlisted(profile: str | None) -> bool:
    p = run(hcmd(profile, "hooks", "list"))
    if p.returncode:
        return False
    return any(
        HOOK in line and "allowed" in line.lower() and "not allowed" not in line.lower()
        for line in p.stdout.splitlines()
    )


def audit_profile(profile: str | None) -> tuple[dict, list[str], list[str]]:
    label = profile or "default"
    home = profile_home(profile)
    issues: list[str] = []
    warnings: list[str] = []

    try:
        snapshot = prompt_snapshot(profile)
        first = runtime_fingerprint(profile)
        second = runtime_fingerprint(profile)
    except Exception as exc:
        return {
            "profile": label,
            "probe_error": str(exc),
        }, [f"{label}: offline runtime probe failed: {exc}"], warnings

    tools = snapshot.get("tools", {})
    tool_count = int(tools.get("count", -1))
    prefix_stable = (
        first.get("stable_sha256") == second.get("stable_sha256")
        and first.get("stable_bytes") == second.get("stable_bytes")
    )
    tool_schema_stable = (
        first.get("tool_schema_sha256") == second.get("tool_schema_sha256")
        and first.get("tool_count") == second.get("tool_count")
    )

    soul = home / "SOUL.md"
    marker_present = soul.is_file() and MARKER in soul.read_text(encoding="utf-8")
    if not marker_present:
        issues.append(f"{label}: harness marker missing from SOUL.md")
    if tool_count < 0 or tool_count > HARD_TOOL_LIMIT:
        issues.append(
            f"{label}: active tool schemas={tool_count}, hard limit={HARD_TOOL_LIMIT}"
        )
    elif tool_count > IDEAL_TOOL_LIMIT:
        warnings.append(
            f"{label}: active tool schemas={tool_count}, above ideal target={IDEAL_TOOL_LIMIT}"
        )
    if tool_count != int(first.get("tool_count", -2)):
        issues.append(
            f"{label}: prompt-size tool count disagrees with canonical schema probe"
        )
    if not prefix_stable:
        issues.append(
            f"{label}: stable prompt SHA-256 changed across consecutive offline probes"
        )
    if not tool_schema_stable:
        issues.append(
            f"{label}: canonical tool-schema SHA-256 changed across consecutive offline probes"
        )
    unmapped_tools = set(first.get("unmapped_tool_names", []))
    unexpected_unmapped = sorted(unmapped_tools - APPROVED_UNMAPPED_TOOLS)
    if unexpected_unmapped:
        issues.append(
            f"{label}: unexpected tool schemas are outside the canonical toolset map: "
            + ", ".join(unexpected_unmapped)
        )

    hard_rc, hard = get_config(profile, "tool_loop_guardrails.hard_stop_enabled")
    if hard_rc or hard.lower() != "true":
        issues.append(f"{label}: interactive hard-stop guard is not enabled")

    hook_rc, hook_cfg = get_config(profile, "hooks.pre_verify")
    if hook_rc or HOOK not in hook_cfg:
        issues.append(f"{label}: CVM pre_verify hook is not configured")
    hook_allowed = hook_is_allowlisted(profile)
    if not hook_allowed:
        issues.append(f"{label}: CVM pre_verify hook is not allowlisted")

    auto_rc, auto = get_config(profile, "hooks_auto_accept")
    if auto_rc or auto.lower() != "false":
        issues.append(f"{label}: hooks_auto_accept must remain false")

    stale_rc, _ = get_config(profile, "code_execution.max_tool_calls")
    stale_key_removed = stale_rc != 0
    if not stale_key_removed:
        issues.append(
            f"{label}: obsolete code_execution.max_tool_calls is still configured"
        )

    env_path = home / ".env"
    env_mode = None
    if env_path.exists():
        env_mode = stat.S_IMODE(env_path.stat().st_mode)
        if env_mode & 0o077:
            issues.append(f"{label}: .env permissions are broader than owner-only")

    return {
        "profile": label,
        "model": snapshot.get("model"),
        "tool_count": tool_count,
        "tool_schema_bytes": tools.get("json_bytes"),
        "hard_tool_limit_pass": 0 <= tool_count <= HARD_TOOL_LIMIT,
        "ideal_tool_target_pass": 0 <= tool_count <= IDEAL_TOOL_LIMIT,
        "toolsets_breakdown": snapshot.get("toolsets_breakdown", []),
        "unmapped_tool_names": sorted(unmapped_tools),
        "unmapped_tools_are_approved_meta_tools": not unexpected_unmapped,
        "stable_sha256": first.get("stable_sha256"),
        "stable_bytes": first.get("stable_bytes"),
        "tool_schema_sha256": first.get("tool_schema_sha256"),
        "prefix_stable_observed": prefix_stable,
        "tool_schema_stable_observed": tool_schema_stable,
        "harness_marker": marker_present,
        "hard_stop_enabled": hard_rc == 0 and hard.lower() == "true",
        "pre_verify_hook_configured": hook_rc == 0 and HOOK in hook_cfg,
        "pre_verify_hook_allowlisted": hook_allowed,
        "hooks_auto_accept": None if auto_rc else auto.lower() == "true",
        "obsolete_code_execution_max_tool_calls_removed": stale_key_removed,
        "env_mode_octal": None if env_mode is None else oct(env_mode),
    }, issues, warnings


def main() -> int:
    profiles: list[str | None] = [None]
    root = HERMES_ROOT / "profiles"
    if root.is_dir():
        profiles += sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and (p / "config.yaml").is_file() and (p / "SOUL.md").is_file()
        )

    results: list[dict] = []
    issues: list[str] = []
    warnings: list[str] = []
    for profile in profiles:
        result, found, noted = audit_profile(profile)
        results.append(result)
        issues.extend(found)
        warnings.extend(noted)

    hook = Path(HOOK)
    hook_mode = stat.S_IMODE(hook.stat().st_mode) if hook.exists() else None
    hook_executable = hook.is_file() and os.access(hook, os.X_OK)
    hook_owner_only = hook_mode is not None and hook_mode & 0o077 == 0
    if not hook_executable:
        issues.append("CVM hook script is missing or not executable")
    if hook_mode is not None and not hook_owner_only:
        issues.append("CVM hook permissions are broader than owner-only")

    max_tools = max(
        (r.get("tool_count", -1) for r in results if isinstance(r.get("tool_count"), int)),
        default=-1,
    )
    report = {
        "harness": "v2026.10.1",
        "hard_tool_limit": HARD_TOOL_LIMIT,
        "ideal_tool_target": IDEAL_TOOL_LIMIT,
        "max_active_tool_schemas_observed": max_tools,
        "profiles": results,
        "hook": {
            "path": HOOK,
            "mode_octal": None if hook_mode is None else oct(hook_mode),
            "executable": hook_executable,
            "owner_only": hook_owner_only,
        },
        "warnings": warnings,
        "issues": issues,
        "gate_status": "PASS" if not issues else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
