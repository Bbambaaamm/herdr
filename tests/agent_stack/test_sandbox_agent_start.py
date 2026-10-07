"""Guarded native launch transport tests; the owned native probe tests real namespaces."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import shlex

import pytest

ROOT = Path(__file__).resolve().parents[2]


def sandbox_module():
    loader = importlib.machinery.SourceFileLoader(
        "sandbox_agent_start_test", str(ROOT / "agent-stack/bin/agent_durable_sandbox.py"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def setup_transport(monkeypatch, *, fault=None):
    module = sandbox_module()
    clock = [0.0]
    calls = []
    state = {"launched": False, "polled": 0, "boundaries": 0}
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(module.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    # Unit doubles only: the owned probe uses real TTY/namespace verification.
    monkeypatch.setattr(module, "inner_pid", lambda info, marker: os.getpid())
    original_readlink = module.os.readlink
    def readlink(path):
        result = original_readlink(path)
        return result + "-changed" if fault == "namespace" and state["launched"] else result
    monkeypatch.setattr(module.os, "readlink", readlink)
    monkeypatch.setattr(module, "_terminal_input_ready", lambda pid, marker: not (fault == "canonical" and state["launched"]))
    def prompt(invoke, pane, marker, **kwargs):
        reader = kwargs["_instance_reader"]
        assert reader({}, marker)[0] == os.getpid()
        calls.append(("inner-prompt-proof",))
        if fault == "prompt":
            raise RuntimeError("durable_pane_prompt_unverified")
    monkeypatch.setattr(module, "verify_pane_prompt", prompt)
    def boundary():
        state["boundaries"] += 1
        if fault == "boundary" or fault == "lost-boundary" and state["launched"]:
            return False
        return True
    def invoke(args, **kwargs):
        calls.append(tuple(args))
        assert 0 < kwargs["timeout_seconds"] <= 10
        if args[:2] == ["pane", "get"]:
            state["polled"] += 1
            detected = None
            if state["launched"] and fault != "timeout" and state["polled"] >= 4:
                detected = "codex" if fault == "kind" else "hermes"
            return {"result": {"pane": {"pane_id": "owned",
                    "terminal_id": "changed" if fault == "terminal" and state["launched"] else "terminal",
                    "agent": "hermes" if fault == "busy" else detected}}}
        if args[:2] == ["pane", "process-info"]:
            return {"result": {"process_info": {}}}
        if args[:2] == ["pane", "run"]:
            state["launched"] = True
            if fault == "native-error":
                raise RuntimeError("native input unavailable")
            return {"result": {}} if fault == "ack" else None
        if args[:2] in (["agent", "rename"], ["agent", "get"]):
            return {"result": {"agent": {"name": "wrong" if fault == "name" else "owned-agent",
                "pane_id": "wrong" if fault == "pane" else "owned",
                "terminal_id": "terminal", "agent": "hermes",
                "agent_status": "blocked" if fault == "blocked" else "unknown" if fault == "not-ready" else "idle"}}}
        pytest.fail(f"unexpected native command {args[:2]}")
    return module, invoke, boundary, calls, state


def launch(module, invoke, boundary, args=None):
    return module.start_sandbox_agent(invoke, "owned", "marker", os.getpid(),
        "owned-agent", ["chat", "--in", "/path with spaces"] if args is None else args,
        verify_boundary=boundary, timeout_seconds=0.2)


def test_launch_once_proves_prompt_and_names_actual_detected_agent(monkeypatch):
    module, invoke, boundary, calls, state = setup_transport(monkeypatch)
    reply = launch(module, invoke, boundary)
    launches = [c for c in calls if c[:2] == ("pane", "run")]
    assert len(launches) == 1
    assert shlex.split(launches[0][3]) == ["exec", "/run/herdr-bootstrap/hermes",
                                         "chat", "--in", "/path with spaces"]
    assert calls.index(("inner-prompt-proof",)) < calls.index(launches[0])
    assert ("agent", "rename", "owned", "owned-agent") in calls
    assert calls[-1] == ("agent", "get", "owned-agent")
    assert not any(c[:2] == ("agent", "start") for c in calls)
    assert reply["result"]["agent"]["pane_id"] == "owned"
    assert state["boundaries"] >= 6


@pytest.mark.parametrize("fault,error,inputs", [
    ("boundary", "boundary_unverified", 0), ("prompt", "prompt_unverified", 0),
    ("busy", "pane_busy", 0), ("ack", "input_unacknowledged", 1),
    ("native-error", "native input unavailable", 1),
    ("lost-boundary", "boundary_unverified", 1), ("terminal", "pane_changed", 1),
    ("kind", "kind_mismatch", 1), ("name", "identity_unverified", 1),
    ("pane", "identity_unverified", 1), ("timeout", "launch_unverified", 1),
    ("canonical", "launch_unverified", 1), ("not-ready", "launch_unverified", 1),
    ("blocked", "startup_blocked", 1), ("namespace", "process_changed", 1),
])
def test_failure_never_resends_launch_or_uses_bare_shell_fallback(monkeypatch, fault, error, inputs):
    module, invoke, boundary, calls, state = setup_transport(monkeypatch, fault=fault)
    with pytest.raises(RuntimeError, match=error):
        launch(module, invoke, boundary)
    assert len([c for c in calls if c[:2] == ("pane", "run")]) == inputs
    assert not any(c[:2] == ("agent", "start") for c in calls)


@pytest.mark.parametrize("args", [["chat", "line\nbreak"], ["chat", "a"*4096], [1]])
def test_invalid_closed_argv_is_rejected_before_native_effect(monkeypatch, args):
    module, invoke, boundary, calls, state = setup_transport(monkeypatch)
    with pytest.raises(RuntimeError, match="launch_invalid"):
        launch(module, invoke, boundary, args)
    assert calls == []
