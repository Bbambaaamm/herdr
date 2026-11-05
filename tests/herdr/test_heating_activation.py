from dataclasses import replace
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path

import pytest

from deploy.herdr.cutover import activate_heating as activation
from herdr.security import (
    CapabilityScope,
    Egress,
    InvocationIdentity,
    NetworkAccess,
    ProcessPolicy,
    ProviderRoute,
    Retention,
    RiskClass,
    RuntimeAssurance,
    SecurityGrant,
    ToolRule,
    Training,
)


def rule(tool, risk, root=()):
    arguments = {
        "read_file": ("limit", "offset", "path"),
        "search_files": ("context", "path", "pattern"),
        "patch": ("mode", "patch", "path"),
        "write_file": ("content", "path"),
        "herdr_verify_work": ("handoff", "request_id"),
        "herdr_submit_result": ("evidence", "status", "summary"),
    }[tool]
    return ToolRule(
        tool, risk, arguments,
        path_fields=("path",) if tool in {"read_file", "search_files", "patch", "write_file"} else (),
        allowed_roots=tuple(root), requires_sandbox=True,
    )


def source_grant(workspace):
    tools = activation.TOOLS
    rules = (
        rule("read_file", RiskClass.READ, (workspace,)),
        rule("search_files", RiskClass.READ, (workspace,)),
        rule("patch", RiskClass.WORKSPACE_WRITE, (workspace,)),
        rule("write_file", RiskClass.WORKSPACE_WRITE, (workspace,)),
        rule("herdr_verify_work", RiskClass.READ),
        rule("herdr_submit_result", RiskClass.RESULT_SUBMISSION, (str(activation.RESULTS),)),
    )
    return SecurityGrant(
        grant_id="source-grant",
        workspace_root=str(workspace),
        identity=InvocationIdentity(
            activation.SOURCE_CONSUMER, "host-policy-template", "host-policy-root",
            "host-policy-root", "host-policy-template", "source-run", 1,
        ),
        scope=CapabilityScope(
            capabilities=("coding",), tools=tools, permissions=("workspace-write",),
            providers=("nous",), executors=("hermes",),
            input_modalities=("text",), output_modalities=("text",),
            data_classes=("internal",), regions=("provider-unspecified",),
            max_egress=Egress.GLOBAL, max_retention=Retention.INDEFINITE,
            training=Training.ALLOWED, max_context_tokens=1000, max_cost_microusd=0,
        ),
        tool_rules=rules,
        process=ProcessPolicy(False, (), NetworkAccess.NONE),
        runtime_assurance=RuntimeAssurance(False, None, NetworkAccess.NONE, (), True),
        provider_routes=(ProviderRoute(
            "nous", "https://example.test/v1", "openai", ("provider-unspecified",),
            ("internal",), Egress.GLOBAL, Retention.INDEFINITE, Training.ALLOWED,
            ("pool:nous:test",),
        ),),
        credential_refs=("pool:nous:test",), approvals=(), approval_required_for=(),
        issued_at="2026-10-01T00:00:00+00:00",
        expires_at="2026-10-02T00:00:00+00:00",
    )


def policy(tmp_path, monkeypatch):
    workspace = tmp_path / "source-workspace"
    workspace.mkdir()
    grant = source_grant(workspace)
    monkeypatch.setattr(activation.pwd, "getpwnam", lambda _: type("P", (), {"pw_uid": 1001})())
    return {
        "schema_version": 1,
        "host_uid": 1001,
        "code": {"source": "/old", "target": "/run/herdr/policy-code", "files": {},
                 "executable_files": [], "max_bytes": activation.MAX_CODE_BYTES,
                 "max_file_bytes": activation.MAX_CODE_FILE_BYTES},
        "runtime": [{}, {}],
        "storage": str(tmp_path / "storage"),
        "templates": {activation.SOURCE_CONSUMER: grant.to_json()},
        "grant_ttl_seconds": 900,
        "task_store_root": str(activation.TASK_ROOT),
    }


def immutable_release(tmp_path):
    release = tmp_path / "v0.3.0-rc.29-0123456789ab"
    (release / "herdr").mkdir(parents=True)
    bodies = {
        "RELEASE.json": b"{}\n",
        "MANIFEST.sha256": b"manifest\n",
        "herdr/new_runtime.py": b"VALUE = 1\n",
        "agent-entry": b"#!/bin/sh\n",
    }
    for name, body in bodies.items():
        path = release / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        path.chmod(0o555 if name == "agent-entry" else 0o444)
    return release, bodies


def test_plan_adds_only_repository_tools_and_complete_release_inventory(tmp_path, monkeypatch):
    raw = policy(tmp_path, monkeypatch)
    release, bodies = immutable_release(tmp_path)
    monkeypatch.setattr(activation, "WORKSPACE", tmp_path / "heating")
    monkeypatch.setattr(activation, "RESULTS", tmp_path / "tasks" / "results")
    issued = datetime(2026, 11, 6, tzinfo=UTC)
    identity = {"tag": "v0.3.0-rc.29", "commit": "0123456789abcdef" * 2 + "01234567"}
    planned, desired, total = activation.planned_policy(raw, release, identity, issued)

    assert set(planned["templates"]) == {activation.SOURCE_CONSUMER, activation.CONSUMER}
    assert set(desired.scope.tools) == set(activation.TOOLS)
    assert "herdr_delegate_child" not in desired.scope.tools
    assert not desired.process.enabled
    assert desired.identity.consumer == activation.CONSUMER
    assert desired.workspace_root == str(activation.WORKSPACE)
    assert desired.expires_at == (issued + timedelta(hours=168)).isoformat()
    assert planned["code"]["source"] == str(release)
    assert set(planned["code"]["files"]) == set(bodies)
    assert planned["code"]["executable_files"] == ([] if os.name == "nt" else ["agent-entry"])
    assert total == sum(map(len, bodies.values()))
    for name, body in bodies.items():
        assert planned["code"]["files"][name] == hashlib.sha256(body).hexdigest()
    for item in desired.tool_rules:
        if item.tool in {"read_file", "search_files", "patch", "write_file"}:
            assert item.allowed_roots == (str(activation.WORKSPACE),)


def test_conflicting_existing_heating_policy_is_rejected(tmp_path, monkeypatch):
    raw = policy(tmp_path, monkeypatch)
    release, _ = immutable_release(tmp_path)
    monkeypatch.setattr(activation, "WORKSPACE", tmp_path / "heating")
    monkeypatch.setattr(activation, "RESULTS", tmp_path / "tasks" / "results")
    raw["templates"][activation.CONSUMER] = raw["templates"][activation.SOURCE_CONSUMER]
    identity = {"tag": "v0.3.0-rc.29", "commit": "0" * 40}
    with pytest.raises(activation.ActivationError, match="heating_policy_drift"):
        activation.planned_policy(raw, release, identity, datetime(2026, 11, 6, tzinfo=UTC))


def test_release_inventory_rejects_writable_files(tmp_path):
    release, _ = immutable_release(tmp_path)
    (release / "herdr/new_runtime.py").chmod(0o644)
    with pytest.raises(activation.ActivationError, match="release_tree_not_immutable"):
        activation.release_inventory(release)
