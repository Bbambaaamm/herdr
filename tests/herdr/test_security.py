from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
from herdr import security
from herdr.approval_broker import ApprovalLedger, serve_approvals
from herdr.security import (
    ApprovalEvidence,
    ContentProvenance,
    InvocationGuard,
    InvocationIdentity,
    NetworkAccess,
    PolicyDenied,
    ProcessPolicy,
    ProviderRequest,
    ProviderRoute,
    RiskClass,
    RuntimeAssurance,
    SecurityError,
    SecurityGrant,
    SignedGrantEnvelope,
    TaintRestrictions,
    ToolRule,
    canonical_digest,
    canonical_json_bytes,
    sign_grant,
    stage_policy_bundle,
    load_policy_bundle,
    verify_signed_grant,
)


def identity(**changes):
    base = dict(
        consumer="github:Bbambaaamm/herdr",
        agent_id="child-agent",
        parent_agent_id="parent-agent",
        parent_task_id="parent-task",
        task_id="child-task",
        run_token="run-1",
        fencing_token=7,
    )
    base.update(changes)
    return InvocationIdentity(**base)


def scope(*, tools=("read_file",), providers=("provider-a",), permissions=("repo:read",)):
    return CapabilityScope(
        providers=providers,
        capabilities=("reasoning",),
        executors=("hermes-runtime",),
        tools=tools,
        permissions=permissions,
        regions=("eu-central",),
        data_classes=(DataClass.INTERNAL,),
        input_modalities=("text",),
        output_modalities=("text",),
        max_cost_microusd=1000,
        max_context_tokens=8192,
        max_egress=Egress.REGION_BOUND,
        max_retention=Retention.LIMITED,
        training=Training.EXCLUDED,
    )


def route(provider="provider-a"):
    return ProviderRoute(
        provider=provider,
        base_url=f"https://{provider}.example.invalid/v1",
        api_mode="openai",
        regions=("eu-central",),
        data_classes=(DataClass.INTERNAL,),
        max_egress=Egress.REGION_BOUND,
        max_retention=Retention.LIMITED,
        training=Training.EXCLUDED,
    )


def grant(
    tmp_path,
    *,
    tools=("read_file",),
    risks=None,
    providers=("provider-a",),
    process=None,
    runtime=None,
    approvals=(),
    approval_required_for=(),
    rules=None,
):
    risks = risks or {}
    risks = {**{"write_file": RiskClass.WORKSPACE_WRITE, "patch": RiskClass.WORKSPACE_WRITE,
                "terminal": RiskClass.PROCESS, "execute_code": RiskClass.PROCESS}, **risks}
    if rules is None:
        rules = tuple(
            ToolRule(
                tool=tool,
                risk=risks.get(tool, RiskClass.READ),
                allowed_arg_keys=(
                    ("path", "offset", "limit")
                    if tool == "read_file"
                    else ("path", "content")
                ),
                path_fields=("path",),
                allowed_roots=(str(tmp_path),),
                requires_process=tool in {"terminal", "execute_code"},
                requires_sandbox=tool in {"terminal", "execute_code"},
            )
            for tool in tools
        )
    process = process or ProcessPolicy(False, (), NetworkAccess.NONE)
    runtime = runtime or assurance()
    return SecurityGrant(
        workspace_root=str(tmp_path),
        grant_id="grant-1",
        identity=identity(),
        scope=scope(tools=tools, providers=providers),
        tool_rules=rules,
        process=process,
        runtime_assurance=runtime,
        provider_routes=tuple(route(item) for item in providers),
        credential_refs=(),
        approvals=tuple(approvals),
        approval_required_for=tuple(approval_required_for),
        issued_at="2026-01-01T00:00:00+00:00",
        expires_at="2030-01-01T00:00:00+00:00",
    )


def assurance(**changes):
    raw = dict(
        sandbox_verified=True,
        sandbox_attestation_sha256="a" * 64,
        network_access=NetworkAccess.NONE,
        writable_roots=(),
        credentials_isolated=True,
    )
    raw.update(changes)
    return RuntimeAssurance(**raw)


def test_signed_grant_is_canonical_bound_to_identity_and_tamper_evident(tmp_path):
    item = grant(tmp_path)
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    envelope = sign_grant(item, key, key_id="ephemeral-1")
    assert verify_signed_grant(
        envelope,
        public,
        expected_identity=item.identity,
        now=datetime(2026, 10, 4, tzinfo=UTC),
    ).hash == item.hash

    with pytest.raises(SecurityError, match="identity/fence"):
        verify_signed_grant(
            envelope,
            public,
            expected_identity=replace(item.identity, fencing_token=8),
            now=datetime(2026, 10, 4, tzinfo=UTC),
        )

    wrong = Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    with pytest.raises(SecurityError, match="authentication"):
        verify_signed_grant(envelope, wrong, expected_identity=item.identity)
    with pytest.raises(SecurityError, match="not active"):
        verify_signed_grant(envelope, public, expected_identity=item.identity,
                            now=datetime(2031, 1, 1, tzinfo=UTC))
    malformed = envelope.to_json()
    malformed["signature"] = "!" * 88
    with pytest.raises(SecurityError, match="encoding"):
        SignedGrantEnvelope.from_dict(malformed)

    bad_algorithm = envelope.to_json()
    bad_algorithm["algorithm"] = "hmac-sha256"
    with pytest.raises(SecurityError, match="unsupported"):
        SignedGrantEnvelope.from_dict(bad_algorithm)
    wrong_key_id = envelope.to_json()
    wrong_key_id["key_id"] = "other-host-key"
    with pytest.raises(SecurityError, match="authentication"):
        verify_signed_grant(SignedGrantEnvelope.from_dict(wrong_key_id), public,
                            expected_identity=item.identity)

    raw = envelope.to_json()
    raw["grant"]["tool_rules"][0]["allowed_arg_keys"].append("mode")
    tampered = SignedGrantEnvelope.from_dict(raw)
    with pytest.raises(SecurityError, match="authentication"):
        verify_signed_grant(
            tampered,
            public,
            expected_identity=item.identity,
            now=datetime(2026, 10, 4, tzinfo=UTC),
        )


def test_bundle_has_only_public_material_and_checks_attestation(tmp_path):
    item = grant(tmp_path)
    key = Ed25519PrivateKey.generate()
    root = tmp_path / "grant.bundle.json"
    with stage_policy_bundle(root) as stage:
        assert root.read_bytes() == b""
        with pytest.raises(SecurityError, match="empty"):
            load_policy_bundle(root, item.identity)
        before = (stage.device, stage.inode)
        sealed = stage.seal(item, key, key_id="host-1", expected_identity=item.identity,
                            expected_attestation_sha256="a" * 64)
        assert (sealed.device, sealed.inode) == before
        assert (root.stat().st_dev, root.stat().st_ino) == before
        assert sealed.sha256 == hashlib.sha256(root.read_bytes()).hexdigest()
        with pytest.raises(SecurityError, match="one-shot"):
            stage.seal(item, key, key_id="host-1", expected_identity=item.identity,
                       expected_attestation_sha256="a" * 64)
    private_bytes = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                      serialization.NoEncryption())
    assert private_bytes not in root.read_bytes()
    assert load_policy_bundle(root, item.identity, expected_attestation_sha256="a" * 64).hash == item.hash
    with pytest.raises(SecurityError, match="attestation"):
        load_policy_bundle(root, item.identity, expected_attestation_sha256="b" * 64)
    with pytest.raises(SecurityError, match="identity/fence"):
        load_policy_bundle(root, replace(item.identity, fencing_token=9), expected_attestation_sha256="a" * 64)
    with pytest.raises(SecurityError, match="identity/fence"):
        load_policy_bundle(root, replace(item.identity, agent_id="other"))
    raw = root.read_bytes()
    root.write_bytes(raw[:len(raw) // 2])
    with pytest.raises(SecurityError):
        load_policy_bundle(root, item.identity)
    root.write_bytes(raw + b"\n")
    with pytest.raises(SecurityError, match="canonical"):
        load_policy_bundle(root, item.identity)
    parsed = json.loads(raw)
    parsed["envelope"]["grant"]["grant_id"] = "tampered"
    root.write_bytes(canonical_json_bytes(parsed))
    with pytest.raises(SecurityError, match="authentication"):
        load_policy_bundle(root, item.identity)


def test_bundle_rejects_symlink_and_fifo(tmp_path):
    item = grant(tmp_path)
    target = tmp_path / "target"
    target.write_bytes(b"x")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(SecurityError, match="unavailable"):
        load_policy_bundle(link, item.identity)
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(SecurityError, match="regular file"):
        load_policy_bundle(fifo, item.identity)


def test_bundle_reads_opened_inode_after_path_replacement(tmp_path, monkeypatch):
    item = grant(tmp_path)
    key = Ed25519PrivateKey.generate()
    path = tmp_path / "bundle"
    with stage_policy_bundle(path) as stage:
        stage.seal(item, key, key_id="host", expected_identity=item.identity,
                   expected_attestation_sha256="a" * 64)
    original_read = security.os.read
    replaced = False

    def replace_path_after_open(fd, count):
        nonlocal replaced
        if not replaced:
            replaced = True
            path.rename(tmp_path / "original")
            path.write_bytes(b"untrusted replacement")
        return original_read(fd, count)

    monkeypatch.setattr(security.os, "read", replace_path_after_open)
    assert load_policy_bundle(path, item.identity).hash == item.hash
    assert replaced


def test_bundle_seal_requires_exact_attestation_and_identity(tmp_path):
    item = grant(tmp_path)
    with stage_policy_bundle(tmp_path / "bundle") as stage:
        with pytest.raises(SecurityError, match="identity/attestation"):
            stage.seal(item, Ed25519PrivateKey.generate(), key_id="host",
                       expected_identity=item.identity,
                       expected_attestation_sha256="b" * 64)
        with pytest.raises(SecurityError, match="one-shot"):
            stage.seal(item, Ed25519PrivateKey.generate(), key_id="host",
                       expected_identity=item.identity,
                       expected_attestation_sha256="a" * 64)


def test_file_rule_cannot_escape_signed_workspace(tmp_path):
    item = grant(tmp_path)
    with pytest.raises(SecurityError, match="workspace-scoped"):
        replace(item, tool_rules=(replace(item.tool_rules[0],
                                         allowed_roots=(str(tmp_path.parent),)),))


def test_read_only_grant_enforces_tool_and_path_arguments(tmp_path):
    item = grant(tmp_path)
    guard = InvocationGuard(item, assurance())
    inside = tmp_path / "inside.txt"
    outside = tmp_path.parent / "outside.txt"

    assert guard.authorize_tool("read_file", {"path": str(inside), "offset": 0}) == "read_file"
    with pytest.raises(PolicyDenied, match="tool_not_granted"):
        guard.authorize_tool("write_file", {"path": str(inside), "content": "x"})
    with pytest.raises(PolicyDenied, match="path_outside_grant"):
        guard.authorize_tool("read_file", {"path": str(outside)})
    with pytest.raises(PolicyDenied, match="tool_arg_not_granted"):
        guard.authorize_tool("read_file", {"path": str(inside), "mode": "write"})


def test_alias_and_task_identity_cannot_expand_grant(tmp_path):
    item = grant(tmp_path)
    guard = InvocationGuard(item, assurance(), aliases={"legacy_write": "write_file"})
    with pytest.raises(PolicyDenied, match="tool_not_granted"):
        guard.authorize_tool("legacy_write", {"path": str(tmp_path / "x"), "content": "x"})
    with pytest.raises(PolicyDenied, match="task_identity_mismatch"):
        guard.authorize_tool("read_file", {"path": str(tmp_path / "x")}, caller_task_id="other-task")


def test_raw_credentials_fail_closed_but_explicit_reference_can_be_granted(tmp_path):
    item = grant(tmp_path)
    guard = InvocationGuard(item, assurance())
    with pytest.raises(PolicyDenied, match="raw_credential_material_denied"):
        guard.authorize_tool("read_file", {"path": "ghp_" + "A" * 24})
    with pytest.raises(PolicyDenied, match="raw_credential_material_denied"):
        guard.authorize_tool("read_file", {"path": str(tmp_path / "x"), "api_key": "secret"})


def test_process_risk_cannot_omit_physical_requirements(tmp_path):
    item = grant(tmp_path)
    with pytest.raises(SecurityError, match="process tool requires"):
        replace(item, scope=scope(tools=("terminal",)),
                tool_rules=(ToolRule("terminal", RiskClass.PROCESS, ("command",)),))


def test_process_grant_cannot_disable_credential_isolation():
    with pytest.raises(SecurityError, match="credential isolation"):
        ProcessPolicy(
            True,
            ("terminal",),
            NetworkAccess.NONE,
            (),
            False,
        )


def test_process_grant_requires_real_sandbox_network_and_credential_boundary(tmp_path):
    rules = (
        ToolRule(
            "terminal",
            RiskClass.PROCESS,
            ("command",),
            requires_process=True,
            requires_sandbox=True,
        ),
    )
    item = grant(
        tmp_path,
        tools=("terminal",),
        providers=("provider-a",),
        rules=rules,
        process=ProcessPolicy(True, ("terminal",), NetworkAccess.NONE, (), True),
        approvals=(ApprovalEvidence("terminal-approval", identity(), "terminal",
                                    canonical_digest({"tool": "terminal", "args": {"command": "printf ok"}})),),
    )
    good = InvocationGuard(item, assurance(network_access=NetworkAccess.NONE))
    assert good.authorize_tool("terminal", {"command": "printf ok"}) == "terminal"

    with pytest.raises(PolicyDenied, match="network_ceiling_exceeded"):
        InvocationGuard(
            replace(
                item,
                runtime_assurance=assurance(
                    network_access=NetworkAccess.GLOBAL,
                ),
            )
        ).authorize_tool("terminal", {"command": "printf ok"})
    with pytest.raises(PolicyDenied, match="credential_boundary_unverified"):
        InvocationGuard(
            replace(
                item,
                runtime_assurance=assurance(
                    credentials_isolated=False,
                ),
            )
        ).authorize_tool("terminal", {"command": "printf ok"})
    with pytest.raises(PolicyDenied, match="filesystem_write_ceiling_exceeded"):
        InvocationGuard(
            replace(
                item,
                runtime_assurance=assurance(
                    writable_roots=(str(tmp_path),),
                ),
            )
        ).authorize_tool("terminal", {"command": "printf ok"})
    with pytest.raises(PolicyDenied, match="sandbox"):
        InvocationGuard(
            replace(
                item,
                runtime_assurance=RuntimeAssurance(
                    False, None, NetworkAccess.NONE, (), True
                ),
            )
        ).authorize_tool("terminal", {"command": "printf ok"})


def test_exact_approval_is_bound_to_identity_tool_args_and_single_use(tmp_path):
    args = {"path": str((tmp_path / "out.txt").resolve()), "content": "ok"}
    digest = canonical_digest({"tool": "write_file", "args": args})
    approval = ApprovalEvidence("approval-1", identity(), "write_file", digest)
    item = grant(
        tmp_path,
        tools=("write_file",),
        risks={"write_file": RiskClass.WORKSPACE_WRITE},
        approvals=(approval,),
        approval_required_for=(RiskClass.WORKSPACE_WRITE,),
    )
    ledger = ApprovalLedger(tmp_path / "host-approval.db")
    ledger.register(item)
    with pytest.raises(PolicyDenied, match="approval_authority_unavailable"):
        InvocationGuard(item, assurance(), approval_socket=tmp_path / "missing.sock").authorize_tool("write_file", args)
    guard = InvocationGuard(item, assurance(), approval_consumer=ledger.consume)
    assert guard.authorize_tool("write_file", args) == "write_file"
    with pytest.raises(PolicyDenied, match="approval_replayed"):
        guard.authorize_tool("write_file", args)

    fresh = InvocationGuard(item, assurance(), approval_consumer=ApprovalLedger(tmp_path / "host-approval.db").consume)
    with pytest.raises(PolicyDenied, match="approval_replayed"):
        fresh.authorize_tool("write_file", args)
    with pytest.raises(PolicyDenied, match="approval_required"):
        fresh.authorize_tool(
            "write_file",
            {"path": str((tmp_path / "other.txt").resolve()), "content": "ok"},
        )


def test_v4a_patch_authorizes_every_embedded_target(tmp_path):
    outside = tmp_path.parent / "outside.py"
    rule = ToolRule(
        "patch",
        RiskClass.WORKSPACE_WRITE,
        ("path", "mode", "patch"),
        ("path",),
        (str(tmp_path),),
    )
    item = grant(tmp_path, tools=("patch",), rules=(rule,))
    guard = InvocationGuard(item, assurance())
    dummy = str((tmp_path / "anchor.py").resolve())
    inside = str((tmp_path / "inside.py").resolve())

    allowed = {
        "path": dummy,
        "mode": "patch",
        "patch": (
            "*** Begin Patch\n"
            f"*** Add File: {inside}\n"
            "+ok\n"
            "*** End Patch"
        ),
    }
    assert guard.authorize_tool("patch", allowed) == "patch"

    escaped = {
        **allowed,
        "patch": (
            "*** Begin Patch\n"
            f"*** Update File: {inside}\n"
            "@@ x @@\n-old\n+new\n"
            f"*** Move File: {inside} -> {outside}\n"
            "*** End Patch"
        ),
    }
    with pytest.raises(PolicyDenied, match="path_outside_grant"):
        guard.authorize_tool("patch", escaped)

    # V4A mode has no top-level path requirement. Every effective header is
    # checked, including delete and both move endpoints.
    allowed.pop("path")
    assert guard.authorize_tool_call("patch", allowed)[1]["patch"].endswith("*** End Patch")
    pathless_rule = ToolRule("patch", RiskClass.WORKSPACE_WRITE, ("mode", "patch"), (), (str(tmp_path),))
    InvocationGuard(grant(tmp_path, tools=("patch",), rules=(pathless_rule,)), assurance()).authorize_tool("patch", allowed)
    for header in (f"*** Add File: {outside}", f"*** Delete File: {outside}",
                   f"*** Move File: {inside} -> {outside}",
                   f"*** Move File: {outside} -> {inside}"):
        with pytest.raises(PolicyDenied, match="path_outside_grant"):
            guard.authorize_tool("patch", {"mode": "patch", "patch": f"*** Begin Patch\n{header}\n+ok\n*** End Patch"})


def test_child_lifetime_and_credential_identity_constraints(tmp_path):
    parent_rule = ToolRule("custom_file", RiskClass.READ, ("path",), ("path",), (str(tmp_path),))
    parent = grant(tmp_path, tools=("custom_file",), rules=(parent_rule,))
    child_identity = identity(agent_id="grandchild", parent_agent_id=parent.identity.agent_id,
                              parent_task_id=parent.identity.task_id, task_id="grandchild-task")
    child = replace(parent, identity=child_identity, parent_grant_hash=parent.hash)
    child.require_subset_of(parent)
    with pytest.raises(SecurityError, match="lifetime"):
        replace(child, issued_at="2025-12-31T00:00:00+00:00").require_subset_of(parent)
    with pytest.raises(SecurityError, match="lifetime"):
        replace(child, expires_at="2031-01-01T00:00:00+00:00").require_subset_of(parent)
    with pytest.raises(SecurityError, match="weakens parent path constraint"):
        replace(child, tool_rules=(ToolRule("custom_file", RiskClass.READ, (), (), ()),)).require_subset_of(parent)
    credential_parent_rule = ToolRule(
        "custom_ref", RiskClass.READ, ("target", "credential_ref"), (), (), ("credential_ref",)
    )
    credential_parent = grant(tmp_path, tools=("custom_ref",), rules=(credential_parent_rule,))
    credential_child = replace(
        credential_parent,
        identity=child_identity,
        parent_grant_hash=credential_parent.hash,
        tool_rules=(ToolRule(
            "custom_ref", RiskClass.READ, ("target", "credential_ref"), (), (),
            ("credential_ref", "target"),
        ),),
    )
    # A child may add credential-reference constraints because that only narrows
    # authority, but it may never drop a parent constraint while keeping the
    # corresponding argument available.
    credential_child.require_subset_of(credential_parent)
    dropped_credential_constraint = replace(
        credential_child,
        tool_rules=(ToolRule(
            "custom_ref", RiskClass.READ, ("target", "credential_ref"), (), (), (),
        ),),
    )
    with pytest.raises(SecurityError, match="weakens parent credential constraint"):
        dropped_credential_constraint.require_subset_of(credential_parent)
    for raw in ("sk-abcdefghijklmnopqrstuvwxyz123456", "sha256:" + "a" * 64, "raw-secret"):
        with pytest.raises(SecurityError):
            replace(parent, credential_refs=(raw,))
        with pytest.raises(SecurityError):
            replace(route(), credential_refs=(raw,))
        with pytest.raises(SecurityError):
            ProviderRequest("provider-a", "eu-central", DataClass.INTERNAL, Egress.REGION_BOUND,
                            Retention.LIMITED, Training.EXCLUDED, raw)


def test_credential_ref_fields_are_explicit_opaque_authority(tmp_path):
    ref = "pool:provider-a:entry-1"
    rule = ToolRule(
        "custom_ref", RiskClass.READ, ("target", "auth"), (), (), ("auth",)
    )
    item = grant(tmp_path, tools=("custom_ref",), rules=(rule,), providers=())
    item = replace(item, credential_refs=(ref,))
    guard = InvocationGuard(item, assurance())
    assert guard.authorize_tool_call(
        "custom_ref", {"target": "x", "auth": ref}
    )[1]["auth"] == ref
    for args in (
        {"target": "x"},
        {"target": "x", "auth": None},
        {"target": "x", "auth": 7},
        {"target": "x", "auth": {}},
        {"target": "x", "auth": []},
        {"target": "x", "auth": ""},
        {"target": "x", "auth": "ghp_abcdefghijklmnopqrstuvwxyz123456"},
        {"target": "x", "auth": "pool:provider-a:other"},
    ):
        with pytest.raises(PolicyDenied, match="credential_ref"):
            guard.authorize_tool("custom_ref", args)


def test_approval_broker_survives_disconnected_response_client(tmp_path):
    import os,struct,threading
    first_finished=threading.Event()
    class Connection:
        def __init__(self, request, *, broken=False):
            self.request = request
            self.broken = broken
            self.sent = []
            self.timeout = None
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def settimeout(self, value):
            self.timeout = value
        def getsockopt(self,*args): return struct.pack('3i',os.getpid(),os.getuid(),os.getgid())
        def recv(self, size):
            data, self.request = self.request[:size], self.request[size:]
            return data
        def sendall(self, data):
            if self.broken:
                first_finished.set()
                raise BrokenPipeError("client closed")
            self.sent.append(data)

    class StopAccept(RuntimeError):
        pass

    item = grant(
        tmp_path,
        tools=("deploy_prod",),
        rules=(ToolRule("deploy_prod", RiskClass.EXTERNAL_SIDE_EFFECT, ("target",)),),
        approvals=(ApprovalEvidence(
            "broker-survive", identity(), "deploy_prod",
            canonical_digest({"tool": "deploy_prod", "args": {"target": "external"}}),
        ),),
        approval_required_for=(RiskClass.EXTERNAL_SIDE_EFFECT,),
    )
    ledger = ApprovalLedger(tmp_path / "broker.db")
    ledger.register(item)
    payload = canonical_json_bytes({
        "grant_hash": item.hash,
        "approval_id": "broker-survive",
        "tool": "deploy_prod",
        "args_sha256": item.approvals[0].args_sha256,
    }) + b"\n"
    first = Connection(payload, broken=True)
    second = Connection(payload)

    class Listener:
        def __init__(self):
            self.items = [first, second]
        def settimeout(self,value): pass
        def accept(self):
            if self.items:
                if len(self.items)==1: assert first_finished.wait(2)
                return self.items.pop(0), None
            raise StopAccept()

    with pytest.raises(StopAccept):
        serve_approvals(Listener(), ledger,peer_authorizer=lambda pid,sha: pid==os.getpid() and sha in (None,item.hash))
    # First request consumed the one-use evidence even though its response was
    # lost; the broker remained alive and answered the next client deterministically.
    assert second.sent == [b"replayed\n"]


def test_one_use_approval_is_atomic_under_concurrent_dispatch(tmp_path):
    args = {"target": "external-system"}
    digest = canonical_digest({"tool": "deploy_prod", "args": args})
    approval = ApprovalEvidence("approval-race", identity(), "deploy_prod", digest)
    rule = ToolRule("deploy_prod", RiskClass.EXTERNAL_SIDE_EFFECT, ("target",))
    item = grant(
        tmp_path,
        tools=("deploy_prod",),
        rules=(rule,),
        approvals=(approval,),
        approval_required_for=(RiskClass.EXTERNAL_SIDE_EFFECT,),
    )
    ledger = ApprovalLedger(tmp_path / "host-approval.db")
    ledger.register(item)
    guards = [InvocationGuard(item, assurance(), approval_consumer=ApprovalLedger(tmp_path / "host-approval.db").consume) for _ in range(2)]

    def invoke(guard):
        try:
            return guard.authorize_tool("deploy_prod", args)
        except PolicyDenied as exc:
            return exc.reason

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(invoke, guards))
    assert sorted(results) == ["approval_replayed", "deploy_prod"]


def test_approval_ledger_survives_fresh_process(tmp_path):
    ledger_path = tmp_path / "host-approval.db"
    item = grant(tmp_path, tools=("deploy_prod",),
                 rules=(ToolRule("deploy_prod", RiskClass.EXTERNAL_SIDE_EFFECT, ("target",)),),
                 approvals=(ApprovalEvidence("restart-approval", identity(), "deploy_prod",
                                             canonical_digest({"tool": "deploy_prod", "args": {"target": "external"}})),),
                 approval_required_for=(RiskClass.EXTERNAL_SIDE_EFFECT,))
    ledger = ApprovalLedger(ledger_path)
    ledger.register(item)
    assert ledger.consume(item.hash, "restart-approval", "deploy_prod", item.approvals[0].args_sha256) == "consumed"
    code = ("from herdr.approval_broker import ApprovalLedger; import sys; "
            "print(ApprovalLedger(sys.argv[1]).consume(*sys.argv[2:]))")
    result = subprocess.run([sys.executable, "-c", code, str(ledger_path), item.hash,
                             "restart-approval", "deploy_prod", item.approvals[0].args_sha256],
                            cwd=os.getcwd(), capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "replayed"


def test_known_side_effect_cannot_lose_risk_or_approval_gate(tmp_path):
    item = grant(tmp_path, tools=("write_file",))
    # Routine workspace edits remain possible inside the signed physical
    # sandbox; consumer policy may still request per-call approval.
    assert item.approval_required_for == ()
    with pytest.raises(SecurityError, match="risk cannot be reclassified"):
        replace(item, tool_rules=(replace(item.tool_rules[0], risk=RiskClass.READ),))

    external = ToolRule(
        "deploy_prod",
        RiskClass.EXTERNAL_SIDE_EFFECT,
        ("target",),
    )
    with pytest.raises(SecurityError, match="high-risk side-effect approval gate missing"):
        grant(
            tmp_path,
            tools=("deploy_prod",),
            rules=(external,),
            approval_required_for=(),
        )


def test_child_scope_must_be_mathematical_subset_including_runtime_edges(tmp_path):
    parent = grant(
        tmp_path,
        tools=("read_file", "write_file"),
        risks={"write_file": RiskClass.WORKSPACE_WRITE},
    )
    child = replace(
        grant(tmp_path, tools=("read_file",)),
        identity=identity(
            agent_id="grandchild-agent",
            parent_agent_id=parent.identity.agent_id,
            parent_task_id=parent.identity.task_id,
            task_id="grandchild",
        ),
        parent_grant_hash=parent.hash,
    )
    child.require_subset_of(parent)
    with pytest.raises(SecurityError, match="parent grant hash"):
        replace(child, parent_grant_hash="0" * 64).require_subset_of(parent)
    with pytest.raises(SecurityError, match="parent identity"):
        replace(
            child,
            identity=identity(
                agent_id="grandchild-agent",
                parent_agent_id=parent.identity.agent_id,
                parent_task_id="forged",
                task_id="grandchild",
            ),
        ).require_subset_of(parent)

    widened_scope = replace(child.scope, tools=("read_file", "patch"))
    widened = replace(
        child,
        scope=widened_scope,
        approval_required_for=(RiskClass.WORKSPACE_WRITE,),
        tool_rules=(
            child.tool_rules[0],
            ToolRule(
                "patch",
                RiskClass.WORKSPACE_WRITE,
                ("path",),
                ("path",),
                (str(tmp_path),),
            ),
        ),
    )
    with pytest.raises(Exception, match="escalates|missing"):
        widened.require_subset_of(parent)

    weakened_rule = replace(parent.tool_rules[1], risk=RiskClass.READ)
    with pytest.raises(SecurityError, match="risk cannot be reclassified"):
        replace(parent, identity=child.identity, parent_grant_hash=parent.hash,
                tool_rules=(parent.tool_rules[0], weakened_rule))


def test_child_cannot_drop_retained_parent_path_constraint(tmp_path):
    parent_rule = ToolRule(
        "custom_file",
        RiskClass.READ,
        ("path", "format"),
        ("path",),
        (str(tmp_path),),
    )
    parent = grant(tmp_path, tools=("custom_file",), rules=(parent_rule,))
    child_identity = identity(
        agent_id="grandchild-agent",
        parent_agent_id=parent.identity.agent_id,
        parent_task_id=parent.identity.task_id,
        task_id="grandchild",
    )
    child = replace(
        grant(
            tmp_path,
            tools=("custom_file",),
            rules=(
                ToolRule("custom_file", RiskClass.READ, ("path", "format"), (), ()),
            ),
        ),
        identity=child_identity,
        parent_grant_hash=parent.hash,
    )
    with pytest.raises(SecurityError, match="weakens parent path constraint"):
        child.require_subset_of(parent)

    narrowed = replace(
        child,
        tool_rules=(ToolRule("custom_file", RiskClass.READ, ("format",), (), ()),),
    )
    with pytest.raises(SecurityError, match="weakens parent path constraint"):
        narrowed.require_subset_of(parent)


def test_untrusted_content_can_only_restrict_not_grant(tmp_path):
    provenance = (ContentProvenance("web", "document-1", True),)
    taint = TaintRestrictions.from_untrusted_directives(
        provenance,
        {"deny_tools": ["read_file"], "deny_providers": []},
    )
    guard = InvocationGuard(grant(tmp_path), assurance())
    with pytest.raises(PolicyDenied, match="tainted_tool_denied"):
        guard.authorize_tool("read_file", {"path": str(tmp_path / "x")}, taint=taint)

    with pytest.raises(SecurityError, match="fields differ"):
        TaintRestrictions.from_untrusted_directives(
            provenance,
            {
                "deny_tools": [],
                "deny_providers": [],
                "allow_tools": ["write_file"],
            },
        )


def test_provider_data_route_and_breaker_isolate_only_target_provider(tmp_path):
    item = grant(tmp_path, providers=("provider-a", "provider-b"))
    guard = InvocationGuard(item, assurance())
    request_a = ProviderRequest(
        "provider-a",
        "eu-central",
        DataClass.INTERNAL,
        Egress.REGION_BOUND,
        Retention.LIMITED,
        Training.EXCLUDED,
    )
    request_b = replace(request_a, provider="provider-b")
    guard.authorize_provider(request_a)
    guard.authorize_provider(request_b)

    guard.breaker.open("provider-a", "compromised")
    with pytest.raises(PolicyDenied, match="provider_isolated"):
        guard.authorize_provider(request_a)
    guard.authorize_provider(request_b)

    with pytest.raises(PolicyDenied, match="provider_region_denied"):
        guard.authorize_provider(replace(request_b, region="us-east"))


def test_signed_envelope_round_trip_is_deterministic(tmp_path):
    item = grant(tmp_path)
    envelope = sign_grant(item, Ed25519PrivateKey.generate(), key_id="k1")
    encoded = json.dumps(envelope.to_json(), sort_keys=True, separators=(",", ":"))
    decoded = SignedGrantEnvelope.from_dict(json.loads(encoded))
    assert decoded.to_json() == envelope.to_json()
    assert decoded.grant.hash == item.hash


def test_approval_response_fragmentation_is_read_through_newline(monkeypatch, tmp_path):
    args = {"path": str((tmp_path / "out.txt").resolve()), "content": "ok"}
    digest = canonical_digest({"tool": "write_file", "args": args})
    item = grant(
        tmp_path, tools=("write_file",),
        approvals=(ApprovalEvidence("fragmented", identity(), "write_file", digest),),
        approval_required_for=(RiskClass.WORKSPACE_WRITE,),
    )

    class FakeSocket:
        def __init__(self, *unused):
            self.parts = [b"con", b"sum", b"ed", b"\n"]
        def __enter__(self): return self
        def __exit__(self, *unused): return False
        def settimeout(self, value): pass
        def connect(self, path): pass
        def sendall(self, data): assert data.endswith(b"\n")
        def recv(self, size): return self.parts.pop(0) if self.parts else b""

    monkeypatch.setattr(security.socket, "socket", FakeSocket)
    assert InvocationGuard(item, assurance(), approval_socket=tmp_path / "authority.sock").authorize_tool(
        "write_file", args
    ) == "write_file"

@pytest.mark.parametrize("field,value",[
    ("network_access",NetworkAccess.GLOBAL),
    ("writable_roots",("/tmp",)),
    ("credentials_isolated",False),
    ("sandbox_verified",False),
])
def test_child_runtime_assurance_cannot_widen_even_for_non_process_tool(tmp_path,field,value):
    parent=grant(tmp_path,tools=("custom_file",),
        rules=(ToolRule("custom_file",RiskClass.READ,()),),
        runtime=RuntimeAssurance(True,"a"*64,NetworkAccess.NONE,(),True))
    child_identity=identity(agent_id="child",parent_agent_id=parent.identity.agent_id,
                            parent_task_id=parent.identity.task_id,task_id="child-task")
    child=replace(parent,grant_id="child",identity=child_identity,parent_grant_hash=parent.hash,
                  runtime_assurance=replace(parent.runtime_assurance,sandbox_attestation_sha256="b"*64))
    child.require_subset_of(parent)
    changed=replace(child.runtime_assurance,**{field:value,
        **({"sandbox_attestation_sha256":None} if field=="sandbox_verified" else {})})
    with pytest.raises(SecurityError,match="runtime assurance"):
        replace(child,runtime_assurance=changed).require_subset_of(parent)

def test_approval_broker_real_stalled_peer_does_not_block_other_connection(tmp_path):
    import os,socket,threading,uuid
    from pathlib import Path
    path=Path("/tmp")/("herdr-approval-test-"+uuid.uuid4().hex+".sock")
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(path));listener.listen(8)
    stopped=threading.Event();calls=[]
    class Ledger:
        def consume(self,**kwargs): calls.append(kwargs);return "consumed"
    thread=threading.Thread(target=serve_approvals,args=(listener,Ledger()),
        kwargs={"stop_event":stopped,"peer_authorizer":lambda pid,sha:pid==os.getpid() and sha in (None,"host-grant")},
        daemon=True)
    thread.start();idle=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    try:
        idle.connect(str(path))
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
            client.settimeout(0.5);client.connect(str(path))
            client.sendall(canonical_json_bytes({"grant_hash":"host-grant","approval_id":"one",
                "tool":"approved","args_sha256":"a"*64})+bytes([10]))
            assert client.recv(64)==b"consumed\n"
        assert len(calls)==1 and thread.is_alive()
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
            client.settimeout(0.5);client.connect(str(path))
            client.sendall(canonical_json_bytes({"grant_hash":"another-grant","approval_id":"two",
                "tool":"approved","args_sha256":"b"*64})+bytes([10]))
            assert client.recv(64)==b"unavailable\n"
        assert len(calls)==1
    finally:
        idle.close();stopped.set();thread.join(3);listener.close();path.unlink(missing_ok=True)
    assert not thread.is_alive()

def test_approval_broker_requires_host_peer_authority(tmp_path):
    with pytest.raises(ValueError,match="host approval peer"):
        serve_approvals(None,ApprovalLedger(tmp_path/"a.db"))
