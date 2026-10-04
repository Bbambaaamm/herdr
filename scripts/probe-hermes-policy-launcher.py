#!/usr/bin/env python3
"""Offline same-process bootstrap probe for Herdr #76.

No live provider or credential is used. Hermes runs only --version with an
isolated HERMES_HOME. The second launch intentionally supplies a stale fence
and must fail before Hermes starts.
"""
from __future__ import annotations

import argparse
import json
import os
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-root", required=True)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    return parser.parse_args()


def main() -> int:
    ns = parse_args()
    repo = Path(ns.repo_root).resolve()
    hermes = Path(ns.hermes_root).resolve()
    sys.path.insert(0, str(repo))

    from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
    from herdr.security import (
        InvocationIdentity,
        NetworkAccess,
        ProcessPolicy,
        RiskClass,
        RuntimeAssurance,
        SecurityGrant,
        ToolRule,
        stage_policy_bundle,
    )

    identity = InvocationIdentity(
        consumer="github:Bbambaaamm/herdr",
        agent_id="launcher-probe-agent",
        parent_agent_id="launcher-probe-parent",
        parent_task_id="launcher-probe-parent-task",
        task_id="launcher-probe-task",
        run_token="launcher-probe-run",
        fencing_token=11,
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
        workspace_root=str(repo),
        grant_id="launcher-probe-grant",
        identity=identity,
        scope=scope,
        tool_rules=(
            ToolRule(
                "read_file",
                RiskClass.READ,
                ("path", "offset", "limit"),
                ("path",),
                (str(repo),),
            ),
        ),
        process=ProcessPolicy(False, (), NetworkAccess.NONE),
        runtime_assurance=RuntimeAssurance(
            True, "a" * 64, NetworkAccess.NONE, (), True
        ),
        provider_routes=(),
        credential_refs=(),
        approvals=(),
        approval_required_for=(),
        issued_at="2026-01-01T00:00:00+00:00",
        expires_at="2030-01-01T00:00:00+00:00",
    )
    with tempfile.TemporaryDirectory(prefix="herdr76-launcher-") as root:
        root_path = Path(root)
        bundle = root_path / "grant.bundle.json"
        with stage_policy_bundle(bundle) as stage:
            stage.seal(grant, Ed25519PrivateKey.generate(), key_id="probe-key",
                       expected_identity=identity, expected_attestation_sha256="a" * 64)
        env = dict(os.environ)
        env["HERMES_HOME"] = str(root_path / "hermes-home")
        env.pop("PYTHONPATH", None)
        fields = {
            "consumer": "HERDR_POLICY_CONSUMER", "agent_id": "HERDR_POLICY_AGENT_ID",
            "parent_agent_id": "HERDR_POLICY_PARENT_AGENT_ID",
            "parent_task_id": "HERDR_POLICY_PARENT_TASK_ID",
            "task_id": "HERDR_POLICY_TASK_ID", "run_token": "HERDR_POLICY_RUN_TOKEN",
            "fencing_token": "HERDR_POLICY_FENCING_TOKEN",
        }
        for name, env_name in fields.items():
            env[env_name] = str(getattr(identity, name))
        loader = (
            "import importlib.machinery, importlib.util, pathlib; "
            "loader=importlib.machinery.SourceFileLoader('policy_bootstrap', '",
            str(repo / "agent-stack/bin/agent-hermes-policy-run"),
            "'); spec=importlib.util.spec_from_loader(loader.name,loader); m=importlib.util.module_from_spec(spec); loader.exec_module(m); "
            "raise SystemExit(m.bootstrap(['--version'], bundle_path=pathlib.Path('",
            str(bundle), "'), policy_code_root=pathlib.Path('", str(repo),
            "'), hermes_root=pathlib.Path('", str(hermes), "')))"
        )
        def invoke(fence: int) -> subprocess.CompletedProcess[str]:
            env[fields["fencing_token"]] = str(fence)
            return subprocess.run([str(hermes / "venv/bin/python"), "-c", "".join(loader)],
                                  env=env, text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, timeout=60, check=False)
        good = invoke(identity.fencing_token)
        assert good.returncode == 0, good.stdout
        assert "Hermes" in good.stdout, good.stdout
        stale = invoke(identity.fencing_token + 1)
        assert stale.returncode != 0, stale.stdout
        assert "identity/fence mismatch" in stale.stdout, stale.stdout
        assert "Hermes Agent v" not in stale.stdout, stale.stdout
        print(json.dumps({"status": "PASS", "same_process_bootstrap": True,
                          "stale_fence_rejected_before_hermes": True,
                          "secret_fd_used": False, "live_provider_used": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
