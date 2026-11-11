"""P0 fail-closed network admission tests; no providers or host changes."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr.host_reference_egress import require_network_isolated_host_reference
from herdr.security import NetworkAccess, PolicyDenied

ROOT = Path(__file__).resolve().parents[2]


def grant(network, verified=True):
    return SimpleNamespace(runtime_assurance=SimpleNamespace(
        network_access=network, sandbox_verified=verified,
    ))


@pytest.mark.parametrize("value", [
    NetworkAccess.GLOBAL, "global", "none", None, object(),
])
def test_global_or_untyped_network_is_denied(value):
    with pytest.raises(PolicyDenied, match="host_reference_native_network_isolation_required"):
        require_network_isolated_host_reference(grant(value))


@pytest.mark.parametrize("verified", [False, None, "True"])
def test_unverified_sandbox_is_denied(verified):
    with pytest.raises(PolicyDenied, match="host_reference_native_network_isolation_required"):
        require_network_isolated_host_reference(grant(NetworkAccess.NONE, verified))


def test_missing_assurance_is_denied():
    with pytest.raises(PolicyDenied, match="host_reference_native_network_isolation_required"):
        require_network_isolated_host_reference(SimpleNamespace())


def test_verified_no_network_grant_passes_only_this_gate():
    # This test proves only a guard predicate, NOT actual sandbox isolation.
    require_network_isolated_host_reference(grant(NetworkAccess.NONE, True))


def test_native_stage2_egress_gate_precedes_sdk_reference_arm_and_cli_import():
    src = (ROOT / "agent-stack/bin/agent-hermes-policy-run").read_text()
    check = src.index("egress_module.require_network_isolated_host_reference(grant)")
    arm = src.index("reference_module.arm_host_reference_process(reference_binding)")
    cli = src.index('hermes_main_module = importlib.import_module("hermes_cli.main")')
    assert check < arm < cli


def test_private_profile_network_architecture_remains_blocked():
    # Evidence of an architectural gap; fail-closed stage2 must remain until
    # a separately reviewed private broker redesign physically isolates net.
    src = (ROOT / "agent-stack/bin/agent_durable_sandbox.py").read_text()
    assert "Keep the host network namespace" in src
    assert "require_network_isolated_host_reference(grant)" in (
        ROOT / "agent-stack/bin/agent-hermes-policy-run").read_text()
