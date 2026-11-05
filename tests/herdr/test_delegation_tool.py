import json
import os
import socket
import threading
import types
from contextvars import ContextVar
from dataclasses import replace

import pytest

from herdr import delegation_tool
from herdr.delegation_tool import TOOL, TOOLSET, ARGUMENTS
from herdr.hermes_guard import GuardInstallation, _call_digest
from herdr.policy_launch import IDENTITY_ENV
from herdr.security import InvocationGuard, RiskClass, SecurityError, ToolRule
from tests.herdr.test_security import grant


class Registry:
    def __init__(self): self.entries = {}
    def get_entry(self, name): return self.entries.get(name)
    def register(self, *, name, handler, toolset, **kwargs):
        assert name not in self.entries
        self.entries[name] = types.SimpleNamespace(handler=handler, toolset=toolset)
    def restore_registration(self, name, current, previous):
        if self.entries.get(name) is current:
            self.entries.pop(name); return True
        return False


def installed(tmp_path, monkeypatch):
    g = grant(tmp_path, tools=(TOOL,), rules=(ToolRule(
        tool=TOOL, risk=RiskClass.DELEGATION, allowed_arg_keys=ARGUMENTS, requires_sandbox=True),))
    guard = InvocationGuard(g)
    installation = GuardInstallation(guard, surface={})
    registry = Registry(); context = ContextVar("test_delegate_authorized", default=None)
    for field, key in IDENTITY_ENV.items():
        monkeypatch.setenv(key, str(getattr(g.identity, field)))
    for key, value in {"HERDR_DURABLE_SANDBOX":"1", "HERDR_DURABLE_TASK_ID":g.identity.task_id,
        "HERDR_DURABLE_RUN_TOKEN":g.identity.run_token, "HERDR_DURABLE_AGENT":g.identity.agent_id,
        "HERDR_DURABLE_MARKER":"isolated-marker", "HERDR_PANE_ID":"isolated-pane"}.items():
        monkeypatch.setenv(key, value)
    delegation_tool.register_delegation_tool(installation, registry, context, _call_digest)
    return installation, registry, context


def arguments():
    return {"key":"read-evidence", "role":"reader", "objective":"Inspect", "prompt":"Read findings"}


def test_registered_tool_uses_real_bounded_socket_client_and_returns_result_without_process_grant(tmp_path, monkeypatch):
    installation, registry, _ = installed(tmp_path, monkeypatch)
    assert not installation.guard.grant.process.enabled
    name = "@herdr-unit-" + os.urandom(8).hex()
    monkeypatch.setenv("HERDR_DURABLE_BRIDGE_SOCKET", name)
    received = []; failure = []
    expected = {"task_id":"child", "evidence":[{"answer":"ř" * 80000}], "evidence_sha256":"a"*64}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind("\0" + name[1:]); listener.listen(1); listener.settimeout(5)
        def broker():
            try:
                with listener.accept()[0] as connection:
                    def exact(n):
                        output = bytearray()
                        while len(output) < n:
                            chunk = connection.recv(n - len(output))
                            if not chunk: raise AssertionError("closed")
                            output.extend(chunk)
                        return bytes(output)
                    size = int.from_bytes(exact(4), "big")
                    received.append(json.loads(exact(size)))
                    payload = json.dumps({"ok":True, "result":expected, "error":None}, ensure_ascii=False).encode()
                    assert len(payload) > 131072
                    connection.sendall(len(payload).to_bytes(4,"big") + payload)
            except Exception as exc: failure.append(exc)
        thread = threading.Thread(target=broker); thread.start()
        result = json.loads(registry.get_entry(TOOL).handler(arguments()))
        thread.join(6)
    assert not thread.is_alive() and not failure
    assert result == expected and len(received) == 1
    assert received[0]["operation"] == "delegate"
    assert received[0]["task_id"] == installation.guard.grant.identity.task_id
    assert received[0]["tool"] == [] and received[0]["permission"] == []
    installation.uninstall()
    assert registry.get_entry(TOOL) is None


@pytest.mark.parametrize("case", ["identity", "task", "sandbox", "unknown-args", "oversized", "duplicate-scope", "inactive"])
def test_direct_handler_cannot_bypass_identity_scope_schema_or_active_guard(tmp_path, monkeypatch, case):
    installation, registry, _ = installed(tmp_path, monkeypatch)
    args = arguments(); calls=[]
    monkeypatch.setattr(delegation_tool, "_client_delegate", lambda value: calls.append(value))
    handler = registry.get_entry(TOOL).handler
    if case == "identity": monkeypatch.setenv("HERDR_POLICY_FENCING_TOKEN","999")
    if case == "task": monkeypatch.setenv("HERDR_DURABLE_TASK_ID","other")
    if case == "sandbox": monkeypatch.setenv("HERDR_DURABLE_SANDBOX","0")
    if case == "unknown-args": args["command"] = "shell"
    if case == "oversized": args["prompt"] = "x" * 32769
    if case == "duplicate-scope": args["tool"] = ["read_file","read_file"]
    if case == "inactive": installation.uninstall()
    assert "error" in json.loads(handler(args)) and calls == []
    installation.uninstall()


def test_registration_cleanup_preserves_newer_owner(tmp_path, monkeypatch):
    installation, registry, _ = installed(tmp_path, monkeypatch)
    newer = types.SimpleNamespace(handler=lambda args: "newer")
    registry.entries[TOOL] = newer
    installation.uninstall()
    assert registry.get_entry(TOOL) is newer


@pytest.mark.parametrize("risk,process,sandbox", [(RiskClass.READ,False,True),
    (RiskClass.DELEGATION,True,True), (RiskClass.DELEGATION,False,False)])
def test_delegation_rule_cannot_be_reclassified_or_grant_generic_process(tmp_path,risk,process,sandbox):
    with pytest.raises(SecurityError):
        grant(tmp_path, tools=(TOOL,), rules=(ToolRule(tool=TOOL, risk=risk,
            allowed_arg_keys=ARGUMENTS, requires_process=process, requires_sandbox=sandbox),))


def test_closed_ownership_reaches_real_handler_with_exact_integration_owner(tmp_path,monkeypatch):
    from herdr.child_ownership import ChildOwnership,WriteScope
    installation,registry,_=installed(tmp_path,monkeypatch)
    owner=installation.guard.grant.identity
    scope=ChildOwnership((WriteScope("file","src/owned.py"),),(),(),(),owner.task_id,"artifact/handoff")
    args={**arguments(),"ownership":scope.to_json()}
    calls=[]
    monkeypatch.setattr(delegation_tool,"_client_delegate",lambda value:calls.append(value) or {"task_id":"child"})
    assert json.loads(registry.get_entry(TOOL).handler(args))=={"task_id":"child"}
    assert calls[0]["ownership"]==scope.to_json()
    calls.clear()
    wrong=replace(scope,integration_owner="foreign-parent")
    assert json.loads(registry.get_entry(TOOL).handler({**args,"ownership":wrong.to_json()}))=={
        "error":"delegation_integration_owner_mismatch"}
    assert calls==[]
    installation.uninstall()


def test_ownership_schema_and_handler_deny_unknown_or_scalar_scope_before_bridge(tmp_path,monkeypatch):
    from herdr.child_ownership import ChildOwnership
    from jsonschema import Draft202012Validator
    installation,registry,_=installed(tmp_path,monkeypatch)
    scope=ChildOwnership((),(),(),(),installation.guard.grant.identity.task_id,"artifact/handoff").to_json()
    args={**arguments(),"ownership":scope}
    assert Draft202012Validator(delegation_tool.SCHEMA["parameters"]).is_valid(args)
    calls=[]
    monkeypatch.setattr(delegation_tool,"_client_delegate",lambda value:calls.append(value))
    for bad in [{**scope,"write_scope":"src"}, {**scope,"new_authority":True},
                {**scope,"hard_dependencies":"child-id"}]:
        assert not Draft202012Validator(delegation_tool.SCHEMA["parameters"]).is_valid({**args,"ownership":bad})
        assert "error" in json.loads(registry.get_entry(TOOL).handler({**args,"ownership":bad}))
    assert calls==[]
    installation.uninstall()
