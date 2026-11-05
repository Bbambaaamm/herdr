"""Pure harness-audit fixtures: private HOME, mocked CLIs, no SDK/hook execution."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/audit-agent-harness.py"
RULE = "Contract -> Plan -> Act -> Evidence -> Gate"
MARKER = "## VS Code + Hermes CVM Harness v2026.10.1"


@pytest.fixture
def audit(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    override = os.environ.get("HERDR_HARNESS_AUDIT_SOURCE")
    source = Path(override) if override else SCRIPT
    if override:
        # RED comparison accepts ONLY the exact immutable flawed150 source,
        # never an arbitrary alternative oracle selected by the environment.
        assert hashlib.sha256(source.read_bytes()).hexdigest() == "adae4c69208dfd4ea907021a4fbd510598fbfbf8251f04e5f23461d6aac93a71"
    spec = importlib.util.spec_from_file_location("harness_audit_fixture", source)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    home = tmp_path / ".hermes";home.mkdir()
    (home / "config.yaml").write_text("{}")
    (home / "SOUL.md").write_text(MARKER + "\n" + RULE + "\n")
    hook = home / "agent-hooks/cvm-evidence-gate.py"
    hook.parent.mkdir();hook.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n");hook.chmod(0o700)
    module.HERMES_ROOT = home;module.HOOK = str(hook)
    # The fixture explicitly models POSIX owner-only metadata on Windows too.
    monkeypatch.setattr(module.stat, "S_IMODE", lambda _: 0o700)
    monkeypatch.setattr(module.os, "access", lambda *args: True)
    stable = (MARKER + "\n" + RULE).encode()
    fingerprint = {"stable_sha256": hashlib.sha256(stable).hexdigest(), "stable_bytes": len(stable),
        "tool_schema_sha256": "a"*64, "tool_schema_bytes_canonical": 64, "tool_count": 1,
        "unmapped_tool_names": [], "rendered_rule_present": True}
    snapshot = {"tools": {"count": 1, "json_bytes": 64}}
    monkeypatch.setattr(module, "prompt_snapshot", lambda _: copy.deepcopy(snapshot))
    monkeypatch.setattr(module, "runtime_fingerprint", lambda _: copy.deepcopy(fingerprint))
    def config(_, key):
        return {"tool_loop_guardrails.hard_stop_enabled": (0, "true"),
            "hooks.pre_verify": (0, str(hook)), "hooks_auto_accept": (0, "false"),
            "code_execution.max_tool_calls": (1, "not set")}[key]
    monkeypatch.setattr(module, "get_config", config)
    actual_run = module.run
    listing = {"text": f"Configured shell hooks (1 total):\n\n  [pre_verify]\n    - {hook} (timeout=10.0s, ✓ allowed)\n"}
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, listing["text"], ""))
    return SimpleNamespace(module=module, home=home, hook=hook, fingerprint=fingerprint, snapshot=snapshot, listing=listing, actual_run=actual_run)


def report(audit, capsys):
    code = audit.module.main()
    return code, json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("fault", ["omitted_profile", "empty_stable", "wrong_event", "arbitrary_executable", "disk_only_rule"])
def test_known_false_pass_is_blocked(audit, capsys, fault):
    if fault == "omitted_profile":
        profile = audit.home / "profiles/named";profile.mkdir(parents=True)
        (profile / "config.yaml").write_text("{}")
    elif fault == "empty_stable":
        audit.fingerprint.update(stable_sha256=hashlib.sha256(b"").hexdigest(), stable_bytes=0)
    elif fault == "wrong_event":
        audit.listing["text"] = audit.listing["text"].replace("[pre_verify]", "[post_llm_call]")
    elif fault == "disk_only_rule":
        audit.fingerprint["rendered_rule_present"] = False
    code, result = report(audit, capsys)
    if fault == "omitted_profile":
        assert len(result["profiles"]) == 2  # Never omit a profile missing SOUL.
        assert result["profiles"][1]["checks"]["soul"]["status"] == "FAIL"
    elif fault == "empty_stable":
        assert result["profiles"][0]["prefix_stable_observed"] is False
    elif fault == "wrong_event":
        assert result["profiles"][0]["pre_verify_hook_allowlisted"] is False
    elif fault == "arbitrary_executable":
        assert result["hook"].get("behavior_status", "PASS") == "UNKNOWN"
    else:
        assert result["profiles"][0].get("rendered_rule_present", True) is False
    assert code != 0 and result["gate_status"] != "PASS"



def test_valid_profile_controls_do_not_authorize_unknown_external_hook(audit, capsys):
    code, result = report(audit, capsys)
    profile = result["profiles"][0]
    for check in ("config", "soul", "stable_fingerprint", "schema_fingerprint", "rendered_rule", "tool_count", "unmapped_tools", "hard_stop", "hooks_auto_accept", "hook_config", "hook_allowlist", "obsolete_key"):
        assert profile["checks"][check]["status"] == "PASS"
    assert result["gate_status"] == result["hook"]["behavior_status"] == "UNKNOWN"
    assert code == 2 and result["execution_authorized"] is result["full_issue149_verified"] is False


@pytest.mark.parametrize("row,status", [
    ("wrong_event", "FAIL"), ("substring", "FAIL"), ("denied", "FAIL"),
    ("duplicate", "UNKNOWN"), ("contradiction", "UNKNOWN"), ("unheaded", "UNKNOWN"),
    ("unsupported", "UNKNOWN"), ("modified", "UNKNOWN"),
])
def test_exact_event_command_and_unambiguous_allowlist_are_required(audit, row, status):
    hook = str(audit.hook)
    line = f"    - {hook} (timeout=10.0s, ✓ allowed)\n"
    if row == "wrong_event":text = "  [post_llm_call]\n"+line+"  [pre_verify]\n"+line.replace("✓ allowed", "✗ not allowlisted")
    elif row == "substring":text = "  [pre_verify]\n"+line.replace(hook, hook+".disabled")
    elif row == "denied":text = "  [pre_verify]\n"+line.replace("✓ allowed", "✗ not allowlisted")
    elif row == "duplicate":text = "  [pre_verify]\n"+line+line
    elif row == "contradiction":text = "  [pre_verify]\n"+line+line.replace("✓ allowed", "✗ not allowlisted")
    elif row == "unheaded":text = line
    elif row == "modified":text = "  [pre_verify]\n"+line+"      ⚠ script modified since approval\n"
    else:text = f"{hook} allowed by an unknown schema"
    audit.listing["text"] = text
    assert audit.module.hook_allowlist_status(None) == status
    assert audit.module.hook_is_allowlisted(None) is False


@pytest.mark.parametrize("kind", ["scalar", "json_string", "json_list", "command_object"])
def test_supported_exact_hook_config_controls(audit, kind):
    value = {"scalar": str(audit.hook), "json_string": json.dumps(str(audit.hook)),
        "json_list": json.dumps([str(audit.hook)]), "command_object": json.dumps({"command": str(audit.hook), "timeout": 10})}[kind]
    assert audit.module.configured_hook(0, value) == "PASS"
    assert audit.module.configured_hook(0, str(audit.hook)+".disabled") == "FAIL"
    assert audit.module.configured_hook(0, json.dumps({"command": str(audit.hook), "matcher": "never"})) == "UNKNOWN"


@pytest.mark.parametrize("field,value", [
    ("unmapped_tool_names", ["unapproved_tool"]), ("unmapped_tool_names", ["ghp_abcdefgh"]),
    ("tool_schema_bytes_canonical", 65), ("tool_schema_sha256", "b"*64),
    ("stable_sha256", "b"*64), ("rendered_rule_present", False), ("tool_count", 2),
])
def test_second_probe_drift_cannot_reuse_first_sample_success(audit, monkeypatch, capsys, field, value):
    first = copy.deepcopy(audit.fingerprint);second = copy.deepcopy(first);second[field] = value
    monkeypatch.setattr(audit.module, "runtime_fingerprint", Mock(side_effect=[first, second]))
    code, result = report(audit, capsys)
    checks = result["profiles"][0]["checks"]
    assert code == 1 and result["gate_status"] == "FAIL"
    assert any(row["status"] == "FAIL" for row in checks.values())
    assert "ghp_abcdefgh" not in json.dumps(result)


@pytest.mark.parametrize("count", [True, "1", 1.0, -1, 101])
def test_tool_count_is_bounded_integer_not_a_coercion(audit, capsys, count):
    audit.snapshot["tools"]["count"] = count
    code, result = report(audit, capsys)
    assert code == 1 and result["profiles"][0]["checks"]["tool_count"]["status"] == "FAIL"


@pytest.mark.parametrize("response,status", [((1, "not set"), "NOT_CONFIGURED"),
    ((1, "Unknown config key: example"), "UNSUPPORTED_KEY"), ((124, "private failure"), "UNKNOWN")])
def test_missing_unsupported_and_unavailable_keys_remain_distinct(audit, monkeypatch, capsys, response, status):
    original = audit.module.get_config
    monkeypatch.setattr(audit.module, "get_config", lambda profile, key: response if key == "tool_loop_guardrails.hard_stop_enabled" else original(profile, key))
    code, result = report(audit, capsys)
    assert code == 2
    assert result["profiles"][0]["checks"]["hard_stop"]["status"] == status
    assert "private failure" not in json.dumps(result)


def test_error_output_and_profile_prompt_model_and_paths_are_not_reported(audit, monkeypatch, capsys):
    private = "ghp_abcdefgh /private/credential-profile account@example.invalid"
    named = audit.home / "profiles/ghp_abcdefgh";named.mkdir(parents=True)
    (named / "config.yaml").write_text("{}");(named / "SOUL.md").write_text(MARKER)
    audit.snapshot.update(model=private, toolsets_breakdown=[private]*10000)
    monkeypatch.setattr(audit.module, "runtime_fingerprint", Mock(side_effect=RuntimeError(private)))
    code, result = report(audit, capsys)
    encoded = json.dumps(result)
    assert code == 2 and private not in encoded and "ghp_abcdefgh" not in encoded
    assert str(audit.home) not in encoded and "probe_error" not in encoded
    assert len(encoded.encode()) <= audit.module.MAX_REPORT_BYTES


def test_env_is_metadata_only_and_profile_files_are_not_modified(audit, monkeypatch, capsys):
    private = audit.home / ".env";private.write_text("API_KEY=fixture-private-value")
    before = {p: p.read_bytes() for p in (private, audit.home/"config.yaml", audit.home/"SOUL.md", audit.hook)}
    original_open = audit.module.os.open
    def guarded(path, *args, **kwargs):
        assert Path(path) != private, "audit must never open .env values"
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(audit.module.os, "open", guarded)
    _, result = report(audit, capsys)
    assert "fixture-private-value" not in json.dumps(result)
    assert {p: p.read_bytes() for p in before} == before


def test_profile_missing_config_is_included_and_reported(audit, capsys):
    profile = audit.home / "profiles/named";profile.mkdir(parents=True)
    (profile/"SOUL.md").write_text(MARKER)
    code, result = report(audit, capsys)
    assert code == 1 and len(result["profiles"]) == 2
    assert result["profiles"][1]["checks"]["config"]["status"] == "FAIL"


def test_inventory_over_limit_is_incomplete_never_pass(audit, monkeypatch, capsys):
    monkeypatch.setattr(audit.module, "MAX_PROFILES", 1)
    for name in ("first", "second"):
        profile = audit.home/"profiles"/name;profile.mkdir(parents=True)
        (profile/"config.yaml").write_text("{}");(profile/"SOUL.md").write_text(MARKER)
    _, result = report(audit, capsys)
    assert result["profile_inventory_status"] == "UNKNOWN"
    assert result["gate_status"] != "PASS" and len(result["profiles"]) <= 2


def test_response_and_report_bounds_fail_closed(audit, monkeypatch, capsys):
    with pytest.raises(ValueError):audit.module.bounded_json("x"*(audit.module.MAX_COMMAND_BYTES+1))
    with pytest.raises(ValueError):audit.module.bounded_json('{"same":1,"same":2}')
    audit.listing["text"] = "x"*(audit.module.MAX_COMMAND_BYTES+1)
    assert audit.module.hook_allowlist_status(None) == "UNKNOWN"
    monkeypatch.setattr(audit.module, "MAX_REPORT_BYTES", 64)
    code, result = report(audit, capsys)
    assert code == 2 and result["reason"] == "report_limit"


@pytest.mark.parametrize("stable", [None, "", "   ", {}])
def test_actual_fingerprint_helper_rejects_absent_empty_or_wrong_stable_tier(audit, monkeypatch, stable):
    install_sdk_doubles(monkeypatch, {"stable": stable})
    with pytest.raises(ValueError, match="stable_tier_unavailable"):
        exec(compile(audit.module.FINGERPRINT_HELPER, "<actual-fingerprint-helper>", "exec"), {})


def install_sdk_doubles(monkeypatch, parts):
    import sys, types
    for name in ("hermes_cli", "agent", "tools"):
        package = types.ModuleType(name);package.__path__ = [];monkeypatch.setitem(sys.modules, name, package)
    prompt = types.ModuleType("hermes_cli.prompt_size")
    prompt._build_inspection_agent = lambda _: SimpleNamespace(tools=[{"function": {"name": "read_file"}}])
    prompt._tool_name = lambda _: "read_file"
    system = types.ModuleType("agent.system_prompt");system.build_system_prompt_parts = lambda _: parts
    registry = types.ModuleType("tools.registry");registry.registry = SimpleNamespace(get_tool_to_toolset_map=lambda: {"read_file": "file"})
    for name, module in [("hermes_cli.prompt_size", prompt), ("agent.system_prompt", system), ("tools.registry", registry)]:
        monkeypatch.setitem(sys.modules, name, module)


@pytest.mark.parametrize("rendered,expected", [(MARKER+"\n"+RULE, True),
    (MARKER+"\nContract → Plan → Act → Evidence → Gate", True), ("normal fallback prompt", False)])
def test_actual_helper_observes_rendered_rule_and_emits_only_fingerprints(audit, monkeypatch, capsys, rendered, expected):
    private = "\nfixture-private-prompt-ghp_abcdefgh"
    install_sdk_doubles(monkeypatch, {"stable": rendered+private})
    exec(compile(audit.module.FINGERPRINT_HELPER, "<actual-fingerprint-helper>", "exec"), {})
    output = capsys.readouterr().out;result = json.loads(output)
    assert result["rendered_rule_present"] is expected
    assert result["stable_sha256"] == hashlib.sha256((rendered+private).encode()).hexdigest()
    assert private not in output and "ghp_abcdefgh" not in output


@pytest.mark.parametrize("heading", [" [post_llm_call]", "  [post_llm_call] ", "  [post_llm_call", "different schema header"])
def test_unknown_heading_cannot_inherit_previous_pre_verify_event(audit, heading):
    audit.listing["text"] = f"  [pre_verify]\n{heading}\n    - {audit.hook} (timeout=5s, ✓ allowed)\n"
    assert audit.module.hook_allowlist_status(None) == "UNKNOWN"
    assert audit.module.hook_is_allowlisted(None) is False


@pytest.mark.parametrize("failure", ["stdout_limit", "stderr_limit", "timeout", "invalid_utf8", "cleanup_timeout", "none"])
def test_actual_capture_is_bounded_fixed_diagnostic_and_reaps_owned_process(audit, monkeypatch, failure):
    module = audit.module
    monkeypatch.setattr(module, "run", audit.actual_run)
    # Actual collector control flow with synthetic pipes/process/select effects.
    # No CLI, SDK, hook, native child or host process is executed.
    streams = {10: bytearray(b"valid"), 11: bytearray()}
    if failure == "stdout_limit":streams[10] = bytearray(b"x"*(module.MAX_COMMAND_BYTES+10))
    if failure == "stderr_limit":streams[11] = bytearray(b"private"*12000)
    if failure == "invalid_utf8":streams[10] = bytearray(b"\xffcredential")
    closed = [];events = [];current = {};child = {"alive": True}
    class Pipe:
        def __init__(self, number):self.number = number
        def fileno(self):return self.number
        def close(self):closed.append(self.number)
    class Process:
        pid = 43210
        returncode = None
        stdout, stderr = Pipe(10), Pipe(11)
        def poll(self):return self.returncode
        def wait(self, timeout):
            events.append(("wait", timeout))
            assert child["alive"] is False, "successful leader must not leave an owned group child"
            if failure == "cleanup_timeout":raise subprocess.TimeoutExpired("mock-cli", timeout)
            self.returncode = 0;return 0
    process = Process()
    class Selector:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def register(self, stream, _, data):current[stream.fileno()] = SimpleNamespace(fd=stream.fileno(), fileobj=stream, data=data)
        def unregister(self, stream):current.pop(stream.fileno())
        def get_map(self):return current
        def select(self, timeout):return [(key,1) for key in list(current.values())]
    def read(number, limit):
        assert 0 < limit <= 4096
        data = bytes(streams[number][:limit]);del streams[number][:limit];return data
    def kill_group(pid, sig):
        assert pid == process.pid
        child["alive"] = False;events.append(("kill", pid))
    fake_os = SimpleNamespace(name="posix", set_blocking=Mock(), read=read,
        waitid=lambda *args: SimpleNamespace(si_pid=process.pid), P_PID=1, WEXITED=2, WNOHANG=4, WNOWAIT=8,
        killpg=kill_group)
    monkeypatch.setattr(module, "os", fake_os)
    monkeypatch.setattr(module, "signal", SimpleNamespace(SIGKILL=9))
    monkeypatch.setattr(module, "selectors", SimpleNamespace(DefaultSelector=Selector, EVENT_READ=1))
    monkeypatch.setattr(module, "subprocess", SimpleNamespace(Popen=Mock(return_value=process),
        DEVNULL=-1, PIPE=-2, CompletedProcess=subprocess.CompletedProcess, TimeoutExpired=subprocess.TimeoutExpired))
    if failure == "timeout":
        ticks = iter([0,31]);monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: next(ticks)))
    result = module.run(["mock-cli"])
    assert set(closed) == {10,11} and any(e[0] == "wait" for e in events)
    if failure == "none":assert result.returncode == 0 and result.stdout == "valid"
    else:
        assert result.returncode != 0 and result.stdout == ""
        assert result.stderr in {"command_timeout", "command_output_limit", "command_unavailable", "command_cleanup_unknown"}
        assert "credential" not in result.stderr and "private" not in result.stderr
    # A successful leader may leave a child that already closed its pipes.
    # Kill the owned group before releasing/reaping its original PID anchor.
    assert ("kill",43210) in events
    assert events.index(("kill",43210)) < next(i for i,e in enumerate(events) if e[0] == "wait")
    module.subprocess.Popen.assert_called_once()
    assert module.subprocess.Popen.call_args.kwargs["start_new_session"] is True



def test_actual_helper_missing_stable_key_is_not_empty_hash_success(audit, monkeypatch):
    install_sdk_doubles(monkeypatch, {})
    with pytest.raises(ValueError, match="stable_tier_unavailable"):
        exec(compile(audit.module.FINGERPRINT_HELPER, "<actual-fingerprint-helper>", "exec"), {})


def test_obsolete_key_probe_failure_is_unknown_not_removed(audit, monkeypatch, capsys):
    original = audit.module.get_config
    monkeypatch.setattr(audit.module, "get_config", lambda profile, key:
        (124, "private unavailable") if key == "code_execution.max_tool_calls" else original(profile, key))
    code, result = report(audit, capsys)
    assert code == 2 and result["profiles"][0]["checks"]["obsolete_key"]["status"] == "UNKNOWN"
    assert "private unavailable" not in json.dumps(result)



def test_broad_env_permissions_are_a_failure_without_exposing_values(audit, monkeypatch, capsys):
    (audit.home/".env").write_text("API_KEY=fixture-private-value")
    monkeypatch.setattr(audit.module.stat, "S_IMODE", lambda _: 0o644)
    code, result = report(audit, capsys)
    assert code == 1 and result["profiles"][0]["checks"]["env_metadata"]["status"] == "FAIL"
    assert "fixture-private-value" not in json.dumps(result)


def test_oversized_soul_does_not_become_marker_success(audit, capsys):
    (audit.home/"SOUL.md").write_text(MARKER+"\n"+"x"*audit.module.MAX_FILE_BYTES)
    code, result = report(audit, capsys)
    assert code == 1 and result["profiles"][0]["checks"]["soul"]["status"] == "FAIL"
