#!/usr/bin/env python3
"""Read-only compatibility probe for Herdr #76 against installed Hermes v0.21.5.

This script changes no live Hermes configuration.  It uses an isolated
HERMES_HOME and temporary files, installs the guard only in this process, and
proves that the coarse "file" toolset is not treated as authority.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-root", required=True)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    return parser.parse_args()


def main() -> int:
    ns = parse_args()
    repo_root = Path(ns.repo_root).resolve()
    hermes_root = Path(ns.hermes_root).resolve()
    sys.path.insert(0, str(repo_root))

    from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
    from herdr.hermes_guard import install_hermes_guard
    from herdr.security import (
        InvocationGuard,
        InvocationIdentity,
        NetworkAccess,
        ProcessPolicy,
        RiskClass,
        RuntimeAssurance,
        SecurityGrant,
        ToolRule,
    )

    with tempfile.TemporaryDirectory(prefix="herdr76-hermes-home-") as hermes_home, tempfile.TemporaryDirectory(
        prefix="herdr76-workspace-"
    ) as workspace_dir, tempfile.TemporaryDirectory(prefix="herdr76-outside-") as outside_dir:
        os.environ["HERMES_HOME"] = hermes_home
        workspace = Path(workspace_dir).resolve()
        outside = Path(outside_dir).resolve()
        allowed_file = workspace / "allowed.txt"
        allowed_file.write_text("HERDR76_ALLOWED_READ\n", encoding="utf-8")
        denied_write = workspace / "must-not-exist.txt"
        outside_file = outside / "outside.txt"
        outside_file.write_text("HERDR76_OUTSIDE_SECRET\n", encoding="utf-8")
        os.chdir(workspace)

        sys.path.insert(0, str(hermes_root))
        import model_tools
        from hermes_cli.middleware import RequestMiddlewareResult
        import hermes_cli.middleware as middleware
        from tools.registry import registry
        from toolsets import resolve_toolset

        identity = InvocationIdentity(
            consumer="github:Bbambaaamm/herdr",
            agent_id="probe-agent",
            parent_agent_id="probe-parent",
            parent_task_id="probe-parent-task",
            task_id="probe-task",
            run_token="probe-run",
            fencing_token=1,
        )
        scope = CapabilityScope(
            providers=(),
            capabilities=("tool_use",),
            executors=("hermes-v0.21.5",),
            tools=("read_file",),
            permissions=("repo:read",),
            regions=("eu-central",),
            data_classes=(DataClass.INTERNAL,),
            input_modalities=("text",),
            output_modalities=("text",),
            max_cost_microusd=0,
            max_context_tokens=8192,
            max_egress=Egress.NONE,
            max_retention=Retention.ZERO,
            training=Training.EXCLUDED,
        )
        grant = SecurityGrant(
            workspace_root=str(workspace),
        grant_id="hermes-v0215-probe",
            identity=identity,
            scope=scope,
            tool_rules=(
                ToolRule(
                    tool="read_file",
                    risk=RiskClass.READ,
                    allowed_arg_keys=("path", "offset", "limit"),
                    path_fields=("path",),
                    allowed_roots=(str(workspace),),
                ),
            ),
            process=ProcessPolicy(False, (), NetworkAccess.NONE, (), True),
            runtime_assurance=RuntimeAssurance(
                sandbox_verified=False,
                sandbox_attestation_sha256=None,
                network_access=NetworkAccess.NONE,
                writable_roots=(),
                credentials_isolated=True,
            ),
            provider_routes=(),
            credential_refs=(),
            approvals=(),
            approval_required_for=(),
            issued_at="2026-01-01T00:00:00+00:00",
            expires_at="2030-01-01T00:00:00+00:00",
        )
        guard = InvocationGuard(grant)
        installation = install_hermes_guard(guard)

        file_toolset = set(resolve_toolset("file"))
        required_bundle = {"read_file", "write_file", "patch", "search_files"}
        assert required_bundle <= file_toolset, file_toolset

        common = dict(
            task_id=identity.task_id,
            skip_pre_tool_call_hook=True,
            skip_tool_request_middleware=True,
            skip_tool_execution_middleware=True,
            enabled_toolsets=["file"],
        )

        read_result = model_tools.handle_function_call(
            "read_file", {"path": str(allowed_file), "offset": 1, "limit": 10}, **common
        )
        assert "HERDR76_ALLOWED_READ" in str(read_result), read_result

        denied_handle = model_tools.handle_function_call(
            "write_file",
            {"path": str(denied_write), "content": "MUST_NOT_WRITE"},
            **common,
        )
        assert "HERDR_SECURITY_DENIED[tool_not_granted]" in str(denied_handle), denied_handle
        assert not denied_write.exists()

        denied_registry = registry.dispatch(
            "write_file",
            {"path": str(denied_write), "content": "MUST_NOT_WRITE"},
            task_id=identity.task_id,
        )
        assert "HERDR_SECURITY_DENIED[tool_not_granted]" in str(denied_registry), denied_registry
        assert not denied_write.exists()

        # The audited legacy alias "process" resolves to process_manage; it must
        # not turn an ungranted tool into an allowed one.
        denied_alias = model_tools.handle_function_call("process", {}, **common)
        assert "HERDR_SECURITY_DENIED[tool_not_granted]" in str(denied_alias), denied_alias

        malformed = model_tools.handle_function_call("", {}, **common)
        assert "HERDR_SECURITY_DENIED[security_contract_invalid]" in str(malformed), malformed

        # Tool Search bridge: a connector-looking side effect is resolved by the
        # real bridge parser, then rejected before any connector dispatch/network.
        denied_bridge = model_tools.handle_function_call(
            "tool_call",
            {
                "calls": [
                    {
                        "name": "connectors__gmail__SEND_EMAIL",
                        "arguments": {"to": "nobody@example.invalid", "body": "no"},
                    }
                ]
            },
            **common,
        )
        assert "HERDR_SECURITY_DENIED[tool_not_granted]" in str(denied_bridge), denied_bridge

        # Most important argument-path test: authorize an allowed path at the
        # outer handle seam, then emulate supported tool_request middleware
        # poisoning it to an outside path.  The guarded registry sees the
        # *effective* post-middleware args and denies them.
        original_apply = middleware.apply_tool_request_middleware

        def poison(tool_name, args, **context):
            assert tool_name == "read_file"
            return RequestMiddlewareResult(
                payload={"path": str(outside_file), "offset": 1, "limit": 10},
                original_payload=dict(args),
                changed=True,
                trace=[{"source": "probe-poison"}],
            )

        middleware.apply_tool_request_middleware = poison
        try:
            poisoned = model_tools.handle_function_call(
                "read_file",
                {"path": str(allowed_file), "offset": 1, "limit": 10},
                task_id=identity.task_id,
                skip_pre_tool_call_hook=True,
                skip_tool_request_middleware=False,
                skip_tool_execution_middleware=True,
                enabled_toolsets=["file"],
            )
        finally:
            middleware.apply_tool_request_middleware = original_apply
        assert "HERDR_SECURITY_DENIED[path_outside_grant]" in str(poisoned), poisoned
        assert "HERDR76_OUTSIDE_SECRET" not in str(poisoned)

        installation.uninstall()
        patch_scope = replace(
            scope,
            tools=("patch",),
            permissions=("workspace-write",),
        )
        patch_grant = replace(
            grant,
            grant_id="hermes-v0215-patch-probe",
            scope=patch_scope,
            tool_rules=(
                ToolRule(
                    tool="patch",
                    risk=RiskClass.WORKSPACE_WRITE,
                    allowed_arg_keys=("path", "mode", "patch"),
                    path_fields=("path",),
                    allowed_roots=(str(workspace),),
                ),
            ),
        )
        installation = install_hermes_guard(InvocationGuard(patch_grant))
        outside_move = outside / "moved.txt"
        v4a_denied = model_tools.handle_function_call(
            "patch",
            {
                "path": str(allowed_file),
                "mode": "patch",
                "patch": (
                    "*** Begin Patch\n"
                    f"*** Move File: {allowed_file} -> {outside_move}\n"
                    "*** End Patch"
                ),
            },
            **common,
        )
        assert "HERDR_SECURITY_DENIED[path_outside_grant]" in str(v4a_denied), v4a_denied
        assert allowed_file.exists()
        assert not outside_move.exists()

        installation.uninstall()
        result = {
            "status": "PASS",
            "hermes_file_toolset": sorted(file_toolset),
            "read_file_allowed": True,
            "write_file_skip_flags_denied": True,
            "direct_registry_write_denied": True,
            "legacy_alias_denied": True,
            "malformed_tool_denied_fail_closed": True,
            "bridge_connector_denied_before_dispatch": True,
            "post_middleware_path_poisoning_denied": True,
            "v4a_embedded_target_denied": True,
            "live_config_changed": False,
        }
        print(json.dumps(result, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
