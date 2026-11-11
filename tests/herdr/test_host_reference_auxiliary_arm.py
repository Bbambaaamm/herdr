"""Static ordering contract for the pinned stage-two Hermes bootstrap.

This test is deliberately not proof of privileged root publication or
security against arbitrary in-process Python monkeypatching.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "agent-stack/bin/agent-hermes-policy-run"


def test_authenticated_stage2_arms_auxiliary_denial_before_cli_import():
    source = STAGE2.read_text()
    authenticated = source.index(
        "reference_binding = reference_module.HostCredentialReference(**authenticated_reference)"
    )
    grant_check = source.index(
        'raise ValueError("authenticated host reference mismatches signed grant")'
    )
    arm = source.index("reference_module.arm_host_reference_process(reference_binding)")
    admitted = source.index("guard._admitted_host_reference = reference_binding")
    cli = source.index('hermes_main_module = importlib.import_module("hermes_cli.main")')
    assert authenticated < grant_check < arm < admitted < cli


def test_stage2_does_not_arm_without_private_reference():
    source = STAGE2.read_text()
    private_branch = source.index("if private_sdk_policy is not None:", source.index("reference_binding = None"))
    arm = source.index("reference_module.arm_host_reference_process(reference_binding)")
    elif_branch = source.index("elif authenticated_reference is not None:", private_branch)
    assert private_branch < arm < elif_branch
