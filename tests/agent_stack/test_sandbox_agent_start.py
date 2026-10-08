"""Guarded native launch transport tests; the owned native probe tests real namespaces."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import shlex
import subprocess,sys
from dataclasses import replace
from herdr.bootstrap_authority import BootstrapContinuation,inspect_peer
from herdr.security import InvocationIdentity

import pytest

OWNED_PROCESSES = []
@pytest.fixture(autouse=True)
def close_owned_processes():
    yield
    for process in OWNED_PROCESSES:
        if process.poll() is None:
            process.kill()
            os.waitpid(process.pid, 0)
            process.returncode = -9
        process.stdin.close()
    OWNED_PROCESSES.clear()


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
    child = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import sys;sys.stdin.read()"],
        stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        env={**os.environ,"HERDR_DURABLE_TASK_PANE":"marker","HERDR_DURABLE_SANDBOX":"1"})
    OWNED_PROCESSES.append(child)
    peer=inspect_peer(child.pid)
    identity=InvocationIdentity("test-consumer","owned-agent","parent","parent-task","task","run",1)
    receipt=BootstrapContinuation(identity.to_json(),peer.pid,peer.start_ticks,
        *("a"*64 for _ in range(5)),peer.exe_device,peer.exe_inode)
    def bootstrap_peer(*,timeout_seconds):
        assert 0<timeout_seconds<=10
        if fault=="bootstrap-denied": raise RuntimeError("authenticated continuation unavailable")
        if fault=="bootstrap-agent": return replace(receipt,identity={**dict(receipt.identity),"agent_id":"foreign"})
        if fault=="bootstrap-parent": return replace(receipt,peer_pid=os.getpid())
        if fault=="bootstrap-reused": return replace(receipt,process_start_ticks=receipt.process_start_ticks+1)
        return receipt
    state["bootstrap_peer"]=bootstrap_peer
    state["receipt"]=receipt
    state["child"]=child
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


def launch(module, invoke, boundary, args=None, *, bootstrap_peer=None):
    return module.start_sandbox_agent(invoke, "owned", "marker", os.getpid(),
        "owned-agent", ["chat", "--in", "/path with spaces"] if args is None else args,
        verify_boundary=boundary, bootstrap_peer=bootstrap_peer, timeout_seconds=0.2)


def test_launch_once_proves_prompt_and_names_actual_detected_agent(monkeypatch):
    module, invoke, boundary, calls, state = setup_transport(monkeypatch)
    reply = launch(module, invoke, boundary, bootstrap_peer=state["bootstrap_peer"])
    launches = [c for c in calls if c[:2] == ("pane", "run")]
    assert len(launches) == 1
    assert shlex.split(launches[0][3]) == ["/run/herdr-bootstrap/hermes",
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
    ("bootstrap-denied", "continuation unavailable", 1),
    ("bootstrap-agent", "bootstrap_peer_unverified", 1),
    ("bootstrap-parent", "bootstrap_peer_unverified", 1),
    ("bootstrap-reused", "bootstrap_peer_unverified", 1),
])
def test_failure_never_resends_launch_or_uses_bare_shell_fallback(monkeypatch, fault, error, inputs):
    module, invoke, boundary, calls, state = setup_transport(monkeypatch, fault=fault)
    with pytest.raises(RuntimeError, match=error):
        launch(module, invoke, boundary, bootstrap_peer=state["bootstrap_peer"])
    assert len([c for c in calls if c[:2] == ("pane", "run")]) == inputs
    assert not any(c[:2] == ("agent", "start") for c in calls)


@pytest.mark.parametrize("args", [["chat", "line\nbreak"], ["chat", "a"*4096], [1]])
def test_invalid_closed_argv_is_rejected_before_native_effect(monkeypatch, args):
    module, invoke, boundary, calls, state = setup_transport(monkeypatch)
    with pytest.raises(RuntimeError, match="launch_invalid"):
        launch(module, invoke, boundary, args, bootstrap_peer=state["bootstrap_peer"])
    assert calls == []


def test_readiness_requires_a_typed_live_authenticated_child(monkeypatch):
    module,invoke,boundary,calls,state=setup_transport(monkeypatch)
    receipt=state["receipt"]
    expected=module._authenticated_agent_instance(receipt,os.getpid(),"marker","owned-agent")
    assert expected is not None and expected[0]==state["child"].pid
    assert module._authenticated_agent_instance({},os.getpid(),"marker","owned-agent") is None
    assert module._authenticated_agent_instance(receipt,os.getpid(),"foreign","owned-agent") is None
    assert module._authenticated_agent_instance(receipt,os.getpid()+1,"marker","owned-agent") is None
    assert module._authenticated_agent_instance(receipt,os.getpid(),"marker","foreign") is None
    assert module._authenticated_agent_instance(replace(receipt,python_inode=receipt.python_inode+1),
                                               os.getpid(),"marker","owned-agent") is None
    original=module.os.readlink
    monkeypatch.setattr(module.os,"readlink",lambda path: original(path)+("-foreign" if path==f"/proc/{receipt.peer_pid}/ns/mnt" else ""))
    assert module._authenticated_agent_instance(receipt,os.getpid(),"marker","owned-agent") is None


def test_bootstrap_callback_is_required_before_native_input(monkeypatch):
    module,invoke,boundary,calls,state=setup_transport(monkeypatch)
    with pytest.raises(RuntimeError,match="launch_invalid"):
        launch(module,invoke,boundary)
    assert calls==[]


def test_named_profile_runtime_masks_do_not_include_credentials_or_aliases(tmp_path):
    module = sandbox_module()
    root = tmp_path / ".hermes"
    profile = root / "profiles" / "quantlab"
    for parent in (root, profile):
        for name in ("sessions", "cache", "logs"):
            (parent / name).mkdir(parents=True)
        (parent / "config.yaml").write_text("approved")
        (parent / ".env").write_text("approved")
    actual = module._ephemeral_sdk_runtime_dirs(tmp_path)
    assert profile / "sessions" in actual
    assert profile / "cache" in actual
    assert profile / "logs" in actual
    assert all(p.name in {"sessions", "cache", "logs", ".cache"} for p in actual)


@pytest.mark.parametrize("runtime_name", ["sessions", "cache", "logs"])
@pytest.mark.parametrize("target_exists", [True, False])
def test_runtime_masks_reject_nested_runtime_alias(tmp_path, runtime_name, target_exists):
    module = sandbox_module()
    profile = tmp_path / ".hermes" / "profiles" / "quantlab"
    profile.mkdir(parents=True)
    workspace = tmp_path / "task-workspace"
    if target_exists:
        workspace.mkdir()
    (profile / runtime_name).symlink_to(workspace, target_is_directory=True)
    with pytest.raises(RuntimeError, match="runtime_alias_unverified"):
        module._ephemeral_sdk_runtime_dirs(tmp_path)


def test_runtime_masks_reject_global_cache_alias(tmp_path):
    module = sandbox_module()
    workspace = tmp_path / "task-workspace"
    workspace.mkdir()
    (tmp_path / ".cache").symlink_to(workspace, target_is_directory=True)
    with pytest.raises(RuntimeError, match="runtime_alias_unverified"):
        module._ephemeral_sdk_runtime_dirs(tmp_path)


@pytest.mark.parametrize("target_exists", [True, False])
def test_runtime_masks_reject_named_profile_alias(tmp_path, target_exists):
    module = sandbox_module()
    profiles = tmp_path / ".hermes" / "profiles"
    profiles.mkdir(parents=True)
    workspace = tmp_path / "task-workspace"
    if target_exists:
        workspace.mkdir()
        (workspace / "config.yaml").write_text("untrusted")
    (profiles / "quantlab").symlink_to(workspace, target_is_directory=True)
    with pytest.raises(RuntimeError, match="profile_alias_unverified"):
        module._ephemeral_sdk_runtime_dirs(tmp_path)


def test_runtime_masks_reject_profile_root_alias(tmp_path):
    module = sandbox_module()
    root = tmp_path / ".hermes"
    root.mkdir()
    outside = tmp_path / "foreign"
    outside.mkdir()
    (root / "profiles").symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="profile_alias_unverified"):
        module._ephemeral_sdk_runtime_dirs(tmp_path)



@pytest.mark.parametrize("missing", ["sessions", "cache", "logs"])
def test_named_profile_runtime_requires_preprovisioned_mountpoint(tmp_path, missing):
    module = sandbox_module()
    root = tmp_path / ".hermes"
    profile = root / "profiles" / "quantlab"
    profile.mkdir(parents=True)
    for name in ("sessions", "cache", "logs"):
        if name != missing:
            (profile / name).mkdir()
    with pytest.raises(RuntimeError, match="profile_runtime_missing"):
        module._ephemeral_sdk_runtime_dirs(tmp_path)


def test_shell_command_has_fixed_byte_limit_before_pane_delivery():
    module = sandbox_module()
    minimal = module.shell_command(["/usr/bin/bwrap", "--", "/bin/true"])
    assert "exec /usr/bin/bwrap" in minimal
    oversized = ["/usr/bin/bwrap", "--setenv", "MANY_PROFILES", "x" * 40000]
    with pytest.raises(RuntimeError, match="shell_command_too_large"):
        module.shell_command(oversized)
