#!/usr/bin/env python3
"""Bounded advisory harness observations; never an execution/acceptance grant."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import textwrap
import time

MARKER = "## VS Code + Hermes CVM Harness v2026.10.1"
REQUIRED_RULE = "Contract -> Plan -> Act -> Evidence -> Gate"
HERMES_ROOT = Path.home() / ".hermes"
HERMES_AGENT_ROOT = Path(os.environ.get("HERMES_AGENT_ROOT", str(HERMES_ROOT / "hermes-agent")))
HERMES_PYTHON = HERMES_AGENT_ROOT / "venv/bin/python"
HOOK = str(HERMES_ROOT / "agent-hooks/cvm-evidence-gate.py")
HARD_TOOL_LIMIT, IDEAL_TOOL_LIMIT = 100, 80
MAX_COMMAND_BYTES, MAX_FILE_BYTES, MAX_REPORT_BYTES, MAX_PROFILES = 65536, 65536, 65536, 16
COMMAND_TIMEOUT_SECONDS = 30
APPROVED_UNMAPPED_TOOLS = {"tool_search", "tool_describe", "tool_call"}
FINGERPRINT_KEYS = {"stable_sha256", "stable_bytes", "tool_schema_sha256", "tool_schema_bytes_canonical",
                    "tool_count", "unmapped_tool_names", "rendered_rule_present"}

FINGERPRINT_HELPER = textwrap.dedent('''
    import hashlib, json
    from hermes_cli.prompt_size import _build_inspection_agent, _tool_name
    from agent.system_prompt import build_system_prompt_parts
    from tools.registry import registry
    agent = _build_inspection_agent("cli")
    parts = build_system_prompt_parts(agent)
    if not isinstance(parts, dict) or not isinstance(parts.get("stable"), str) or not parts["stable"].strip():
        raise ValueError("stable_tier_unavailable")
    stable = parts["stable"]
    tools = getattr(agent, "tools", None)
    if not isinstance(tools, list) or len(tools) > 4096 or len(stable.encode("utf-8")) > 1048576:
        raise ValueError("inspection_bounds")
    canonical_tools = json.dumps(tools, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(canonical_tools) > 1048576: raise ValueError("schema_bounds")
    mapping = registry.get_tool_to_toolset_map()
    unmapped = sorted(_tool_name(tool) for tool in tools if not mapping.get(_tool_name(tool)))
    normalized = " ".join(stable.replace("→", "->").split())
    print(json.dumps({"stable_sha256": hashlib.sha256(stable.encode("utf-8")).hexdigest(),
        "stable_bytes": len(stable.encode("utf-8")), "tool_schema_sha256": hashlib.sha256(canonical_tools).hexdigest(),
        "tool_schema_bytes_canonical": len(canonical_tools), "tool_count": len(tools),
        "unmapped_tool_names": unmapped,
        "rendered_rule_present": MARKER in stable and REQUIRED_RULE in normalized}, sort_keys=True))
''').replace("MARKER in stable", repr(MARKER) + " in stable").replace("REQUIRED_RULE in normalized", repr(REQUIRED_RULE) + " in normalized")


def run(args, *, env=None, cwd=None):
    """POSIX owned process group; bounded concurrent capture, kill/reap on limit."""
    if os.name != "posix" or not all(hasattr(os, name) for name in ("waitid", "WNOWAIT", "WEXITED", "WNOHANG", "P_PID")):
        return subprocess.CompletedProcess(args, 126, "", "unsupported_platform")
    process = None
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    failure = None
    anchor_lost = False
    cleanup_failed = False
    try:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, cwd=cwd, start_new_session=True, close_fds=True)
        deadline = time.monotonic() + COMMAND_TIMEOUT_SECONDS
        with selectors.DefaultSelector() as selector:
            for name in buffers:
                stream = getattr(process, name)
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map() and failure is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    failure = "command_timeout";break
                for key, _ in selector.select(min(remaining, 0.1)):
                    try:
                        data = os.read(key.fd, min(4096, MAX_COMMAND_BYTES + 1 - len(buffers[key.data])))
                    except BlockingIOError:
                        continue
                    if not data:
                        selector.unregister(key.fileobj);continue
                    buffers[key.data].extend(data)
                    if len(buffers[key.data]) > MAX_COMMAND_BYTES:
                        failure = "command_output_limit";break
            if failure is None:
                # Keep the leader as an unreaped PID/PGID anchor even on success.
                # Reaping first would permit the numeric group identity to recycle.
                while True:
                    exited = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if exited is not None and exited.si_pid == process.pid:break
                    if time.monotonic() >= deadline:
                        failure = "command_timeout";break
                    time.sleep(0.01)
        if failure:
            return subprocess.CompletedProcess(args, 124, "", failure)
        stdout = bytes(buffers["stdout"]).decode("utf-8")
        stderr = bytes(buffers["stderr"]).decode("utf-8")
    except ChildProcessError:
        anchor_lost = True
        return subprocess.CompletedProcess(args, 124, "", "command_unavailable")
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(args, 124, "", "command_unavailable")
    finally:
        if process is not None:
            # Fence the still-anchored group even if descendants closed pipes
            # and the leader exited successfully. Never signal a recycled PGID.
            if not anchor_lost:
                try:os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:pass
                except OSError:cleanup_failed = True
            try:process.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):cleanup_failed = True
            for name in buffers:
                stream = getattr(process, name)
                if stream is not None:stream.close()
    if cleanup_failed or type(process.returncode) is not int:
        return subprocess.CompletedProcess(args, 124, "", "command_cleanup_unknown")
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)


def hcmd(profile, *args):
    return ["hermes", *([] if profile is None else ["-p", profile]), *args]


def bounded_json(text):
    if type(text) is not str or len(text.encode("utf-8")) > MAX_COMMAND_BYTES:
        raise ValueError("response_bounds")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:raise ValueError("duplicate_field")
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique)


def get_config(profile, key):
    response = run(hcmd(profile, "config", "get", key))
    return response.returncode, (response.stdout or response.stderr).strip()


def config_status(code, value):
    if type(value) is not str or len(value.encode("utf-8")) > MAX_COMMAND_BYTES:return "UNKNOWN"
    text = value.strip().lower()
    if text in {"not set", "not configured", "<not set>"}:return "NOT_CONFIGURED"
    if text.startswith(("unknown config key:", "unsupported config key:")):return "UNSUPPORTED_KEY"
    return "PASS" if code == 0 else "UNKNOWN"


def prompt_snapshot(profile):
    response = run(hcmd(profile, "prompt-size", "--platform", "cli", "--json"))
    if response.returncode:raise ValueError("snapshot_unavailable")
    return bounded_json(response.stdout)


def profile_home(profile):
    return HERMES_ROOT if profile is None else HERMES_ROOT / "profiles" / profile


def runtime_fingerprint(profile):
    if not HERMES_PYTHON.is_file():raise ValueError("interpreter_unavailable")
    env = os.environ.copy();env["HERMES_HOME"] = str(profile_home(profile))
    env.pop("PYTHONPATH", None);env.pop("PYTHONHOME", None)
    response = run([str(HERMES_PYTHON), "-c", FINGERPRINT_HELPER], env=env, cwd=HERMES_AGENT_ROOT)
    if response.returncode:raise ValueError("fingerprint_unavailable")
    return bounded_json(response.stdout)


def hook_allowlist_status(profile):
    response = run(hcmd(profile, "hooks", "list"))
    if response.returncode:return "UNKNOWN"
    text = response.stdout
    if type(text) is not str or len(text.encode("utf-8")) > MAX_COMMAND_BYTES:return "UNKNOWN"
    # Exact Hermes text grammar: event heading + exact unqualified command.
    event, found, parsed = None, [], False
    for line in text.splitlines():
        heading = re.fullmatch(r"  \[([a-z_]+)\]", line)
        if heading:event = heading[1];parsed = True;continue
        row = re.fullmatch(r"    - (.+) \(timeout=[0-9]+(?:\.[0-9]+)?s, (✓ allowed|✗ not allowlisted)\)", line)
        if row:
            if event is None:return "UNKNOWN"
            if event == "pre_verify" and row[1] == HOOK:found.append(row[2] == "✓ allowed")
        elif line.strip() and not (re.fullmatch(r"Configured shell hooks \([0-9]+ total\):", line)
                or re.fullmatch(r"      approved_at: [0-9T:+Z. -]{1,80}", line)):
            # Unknown headings/rows must never inherit the previous event.
            return "UNKNOWN"
    if len(found) > 1:return "UNKNOWN"
    if found:return "PASS" if found[0] else "FAIL"
    return "FAIL" if parsed else "UNKNOWN"


def hook_is_allowlisted(profile):
    return hook_allowlist_status(profile) == "PASS"


def configured_hook(code, value):
    status = config_status(code, value)
    if status != "PASS":return status
    try:parsed = bounded_json(value)
    except (ValueError, TypeError):parsed = value.strip()
    if type(parsed) is str:return "PASS" if parsed == HOOK else "FAIL"
    rows = parsed if type(parsed) is list else [parsed]
    if len(rows) > 32:return "UNKNOWN"
    commands = []
    for row in rows:
        if type(row) is str:commands.append(row)
        elif type(row) is dict and set(row) <= {"command", "timeout"} and type(row.get("command")) is str:
            commands.append(row["command"])
        else:return "UNKNOWN"
    return "PASS" if commands.count(HOOK) == 1 else "FAIL"


def read_soul(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE_BYTES:raise ValueError("soul_bounds")
        data = os.read(fd, MAX_FILE_BYTES + 1)
        after = os.fstat(fd)
        if len(data) > MAX_FILE_BYTES or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("soul_changed")
        return data.decode("utf-8")
    finally:os.close(fd)


def fingerprint_valid(value):
    return (type(value) is dict and set(value) == FINGERPRINT_KEYS
        and all(type(value[k]) is str and re.fullmatch("[0-9a-f]{64}", value[k]) for k in ("stable_sha256", "tool_schema_sha256"))
        and value["stable_sha256"] != hashlib.sha256(b"").hexdigest()
        and all(type(value[k]) is int and 0 < value[k] <= 1048576 for k in ("stable_bytes", "tool_schema_bytes_canonical"))
        and type(value["tool_count"]) is int and 0 <= value["tool_count"] <= 4096
        and type(value["rendered_rule_present"]) is bool
        and type(value["unmapped_tool_names"]) is list and len(value["unmapped_tool_names"]) <= 4096
        and all(type(name) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{0,127}", name) for name in value["unmapped_tool_names"]))


def audit_profile(profile):
    # Never expose host paths, raw profile/model/tool names, prompts or errors.
    home = profile_home(profile);checks = {};warnings = []
    def check(name, status):checks[name] = {"status": status}
    def regular(path):return path.is_file() and not path.is_symlink()
    check("config", "PASS" if regular(home / "config.yaml") else "FAIL")
    marker = False
    try:
        soul = home / "SOUL.md"
        if not regular(soul):raise ValueError("soul_missing")
        marker = MARKER in read_soul(soul)
        check("soul", "PASS" if marker else "FAIL")
    except (OSError, UnicodeError, ValueError):check("soul", "FAIL")
    result = {"checks": checks, "prefix_stable_observed": False, "tool_schema_stable_observed": False,
              "rendered_rule_present": False, "pre_verify_hook_allowlisted": False}
    if checks["config"]["status"] == "FAIL" or checks["soul"]["status"] == "FAIL":
        return result, ["required_profile_file"], warnings
    try:
        snapshot = prompt_snapshot(profile);first = runtime_fingerprint(profile);second = runtime_fingerprint(profile)
        valid = fingerprint_valid(first) and fingerprint_valid(second)
        prefix = valid and all(first[k] == second[k] for k in ("stable_sha256", "stable_bytes"))
        schema = valid and all(first[k] == second[k] for k in ("tool_schema_sha256", "tool_schema_bytes_canonical", "tool_count", "unmapped_tool_names"))
        rendered = valid and first["rendered_rule_present"] and second["rendered_rule_present"]
        count = snapshot.get("tools", {}).get("count") if type(snapshot) is dict and type(snapshot.get("tools")) is dict else None
        count_ok = type(count) is int and 0 <= count <= HARD_TOOL_LIMIT and valid and count == first["tool_count"] == second["tool_count"]
        check("stable_fingerprint", "PASS" if prefix else "FAIL")
        check("schema_fingerprint", "PASS" if schema else "FAIL")
        check("rendered_rule", "PASS" if rendered else "FAIL")
        check("tool_count", "PASS" if count_ok else "FAIL")
        check("unmapped_tools", "PASS" if valid and not (set(first["unmapped_tool_names"]) | set(second["unmapped_tool_names"])) - APPROVED_UNMAPPED_TOOLS else "FAIL")
        result.update(prefix_stable_observed=prefix, tool_schema_stable_observed=schema, rendered_rule_present=rendered)
        if valid:
            result.update(stable_sha256=first["stable_sha256"], stable_bytes=first["stable_bytes"], tool_schema_sha256=first["tool_schema_sha256"], tool_count=count if type(count) is int else None)
        if count_ok and count > IDEAL_TOOL_LIMIT:warnings.append("tool_count_above_ideal")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RuntimeError):
        check("runtime_probe", "UNKNOWN")
    for key, name, expected in [("tool_loop_guardrails.hard_stop_enabled", "hard_stop", "true"), ("hooks_auto_accept", "hooks_auto_accept", "false")]:
        code, value = get_config(profile, key);status = config_status(code, value)
        check(name, status if status != "PASS" else "PASS" if value.lower() == expected else "FAIL")
    code, value = get_config(profile, "hooks.pre_verify");check("hook_config", configured_hook(code, value))
    allowed = hook_allowlist_status(profile);check("hook_allowlist", allowed)
    result["pre_verify_hook_allowlisted"] = allowed == "PASS"
    code, value = get_config(profile, "code_execution.max_tool_calls");status = config_status(code, value)
    check("obsolete_key", "PASS" if status == "NOT_CONFIGURED" else "FAIL" if status == "PASS" else status)
    try:
        info = (home / ".env").lstat()
        check("env_metadata", "PASS" if stat.S_ISREG(info.st_mode) and not stat.S_IMODE(info.st_mode) & 0o077 else "FAIL")
    except FileNotFoundError:check("env_metadata", "NOT_CONFIGURED")
    except OSError:check("env_metadata", "UNKNOWN")
    return result, [key for key, row in checks.items() if row["status"] == "FAIL"], warnings


def main():
    profiles = [None];inventory = "PASS"
    try:
        root = HERMES_ROOT / "profiles"
        if root.is_symlink():raise ValueError("profile_alias")
        if root.exists():
            for entry_index, child in enumerate(root.iterdir()):
                if entry_index >= 128:raise ValueError("profile_inventory_limit")
                if child.is_symlink():raise ValueError("profile_alias")
                if child.is_dir():
                    if len(profiles) > MAX_PROFILES:raise ValueError("profile_limit")
                    if not re.fullmatch("[A-Za-z0-9][A-Za-z0-9._-]{0,63}", child.name):raise ValueError("profile_name")
                    profiles.append(child.name)
        profiles = [None, *sorted(profiles[1:])]
    except (OSError, ValueError):inventory = "UNKNOWN"
    results = [];issues = [];warnings = []
    for index, profile in enumerate(profiles):
        label = "default" if profile is None else f"profile-{index}"
        try:result, found, noted = audit_profile(profile)
        except (OSError, UnicodeError, ValueError, TypeError, KeyError, RuntimeError):
            result, found, noted = {"checks": {"profile_probe": {"status": "UNKNOWN"}}}, [], []
        result["profile"] = label;results.append(result)
        issues.extend({"profile": label, "check": code} for code in found)
        warnings.extend({"profile": label, "check": code} for code in noted)
    try:
        info = Path(HOOK).lstat()
        metadata = "PASS" if stat.S_ISREG(info.st_mode) and os.access(HOOK, os.X_OK) and not stat.S_IMODE(info.st_mode) & 0o077 else "FAIL"
    except OSError:metadata = "FAIL"
    # No reviewed hook content/effective-behavior proof was supplied by PR150.
    # Executability or a self-declared hash cannot manufacture that evidence.
    hook = {"metadata_status": metadata, "behavior_status": "UNKNOWN"}
    effective_policy, runtime_identity = "UNKNOWN", "UNKNOWN"
    statuses = [inventory, metadata, hook["behavior_status"], effective_policy, runtime_identity, *(row["status"] for result in results for row in result["checks"].values())]
    status = "FAIL" if "FAIL" in statuses else "UNKNOWN" if any(s != "PASS" for s in statuses) else "PASS"
    report = {"schema": "herdr-harness-observations-1", "harness": "v2026.10.1", "profiles": results,
        "profile_inventory_status": inventory, "hook": hook, "issues": issues, "warnings": warnings,
        "gate_status": status, "effective_policy_status": effective_policy, "runtime_identity_status": runtime_identity,
        "execution_authorized": False, "full_issue149_verified": False}
    output = json.dumps(report, sort_keys=True, ensure_ascii=True)
    if len(output.encode("utf-8")) > MAX_REPORT_BYTES:
        output = json.dumps({"schema": "herdr-harness-observations-1", "gate_status": "UNKNOWN", "reason": "report_limit", "execution_authorized": False})
        status = "UNKNOWN"
    print(output)
    return {"PASS": 0, "FAIL": 1, "UNKNOWN": 2}[status]


if __name__ == "__main__":
    sys.exit(main())
