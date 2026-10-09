from __future__ import annotations

import json
import types
from contextvars import ContextVar

import pytest

from herdr import external_knowledge_tool
from herdr.external_knowledge import (
    KnowledgeResponse,
    KnowledgeSourceResult,
)
from herdr.external_knowledge_tool import ARGUMENTS, TOOL, TOOLSET
from herdr.hermes_guard import GuardInstallation, _call_digest
from herdr.policy_launch import IDENTITY_ENV
from herdr.security import InvocationGuard, RiskClass, SecurityError, ToolRule
from tests.herdr.test_security import grant


class Registry:
    def __init__(self):
        self.entries = {}

    def get_entry(self, name):
        return self.entries.get(name)

    def register(self, *, name, handler, toolset, **_kwargs):
        assert name not in self.entries
        self.entries[name] = types.SimpleNamespace(handler=handler, toolset=toolset)

    def restore_registration(self, name, current, _previous):
        if self.entries.get(name) is current:
            self.entries.pop(name)
            return True
        return False


class FakeAuthority:
    def __init__(self):
        self.calls = []

    def external_knowledge(self, identity, grant_sha256, provider_id, request):
        self.calls.append((identity, grant_sha256, provider_id, request))
        return KnowledgeResponse(
            request.request_id,
            "completed",
            "evidence",
            tuple(
                KnowledgeSourceResult(source, "ok", 1, answer=f"{source}:evidence")
                for source in request.sources
            ),
            False,
        )


def installed(tmp_path, monkeypatch):
    rule = ToolRule(
        TOOL,
        RiskClass.READ,
        ARGUMENTS,
        requires_sandbox=True,
    )
    item = grant(tmp_path, tools=(TOOL,), providers=(), rules=(rule,))
    guard = InvocationGuard(item)
    installation = GuardInstallation(guard, surface={})
    registry = Registry()
    context = ContextVar("test_external_knowledge_authorized", default=None)
    fake = FakeAuthority()
    monkeypatch.setattr(
        "herdr.work_authority.WorkAuthorityClient",
        lambda: fake,
    )
    for field, key in IDENTITY_ENV.items():
        monkeypatch.setenv(key, str(getattr(item.identity, field)))
    monkeypatch.setenv("HERDR_DURABLE_SANDBOX", "1")
    external_knowledge_tool.register_external_knowledge_tool(
        installation, registry, context, _call_digest
    )
    return installation, registry, fake


def arguments():
    return {
        "provider_id": "corp",
        "query": "Find prior repair evidence",
        "sources": ["mail", "chat"],
    }


def test_registered_tool_is_read_only_host_bridge_and_preserves_sources(tmp_path, monkeypatch):
    installation, registry, fake = installed(tmp_path, monkeypatch)
    entry = registry.get_entry(TOOL)
    assert entry.toolset == TOOLSET
    assert not installation.guard.grant.process.enabled
    result = json.loads(entry.handler(arguments()))
    assert result["status"] == "completed"
    assert [row["source"] for row in result["sources"]] == ["mail", "chat"]
    assert len(fake.calls) == 1
    identity, grant_sha, provider_id, request = fake.calls[0]
    assert identity == installation.guard.grant.identity
    assert grant_sha == installation.guard.grant.hash
    assert provider_id == "corp"
    assert request.query == arguments()["query"]
    installation.uninstall()
    assert registry.get_entry(TOOL) is None


@pytest.mark.parametrize(
    "case",
    ["identity", "sandbox", "unknown", "oversized", "duplicate", "inactive"],
)
def test_direct_handler_cannot_bypass_guard_or_schema(tmp_path, monkeypatch, case):
    installation, registry, fake = installed(tmp_path, monkeypatch)
    raw = arguments()
    handler = registry.get_entry(TOOL).handler
    if case == "identity":
        monkeypatch.setenv("HERDR_POLICY_FENCING_TOKEN", "999")
    elif case == "sandbox":
        monkeypatch.setenv("HERDR_DURABLE_SANDBOX", "0")
    elif case == "unknown":
        raw["endpoint"] = "https://forbidden.invalid"
    elif case == "oversized":
        raw["query"] = "x" * 4097
    elif case == "duplicate":
        raw["sources"] = ["mail", "mail"]
    elif case == "inactive":
        installation.uninstall()
    assert "error" in json.loads(handler(raw))
    assert fake.calls == []
    installation.uninstall()


@pytest.mark.parametrize(
    "risk,process,sandbox,args",
    [
        (RiskClass.CREDENTIAL_USE, False, True, ARGUMENTS),
        (RiskClass.READ, True, True, ARGUMENTS),
        (RiskClass.READ, False, False, ARGUMENTS),
        (RiskClass.READ, False, True, ("query", "sources")),
    ],
)
def test_external_knowledge_rule_is_fixed_read_only_sandbox_contract(
    tmp_path, risk, process, sandbox, args
):
    with pytest.raises(SecurityError):
        grant(
            tmp_path,
            tools=(TOOL,),
            providers=(),
            rules=(
                ToolRule(
                    TOOL,
                    risk,
                    args,
                    requires_process=process,
                    requires_sandbox=sandbox,
                ),
            ),
        )


def test_runtime_toolset_maps_only_explicit_external_knowledge():
    from herdr.runtime import _child_toolsets, HerdrRuntimeError

    assert _child_toolsets((TOOL,)) == TOOLSET
    assert _child_toolsets(("read_file", TOOL)) == f"file,{TOOLSET}"
    with pytest.raises(HerdrRuntimeError, match="child_toolset_unmapped"):
        _child_toolsets(("external_knowledge",))
