from types import SimpleNamespace

import pytest

from herdr.policy_launch import (
    HostPolicyLaunchFactory,
    PreparedPolicyLaunch,
    require_approved_profile_binding,
)
from herdr.security import SecurityError


def _objects(*, schema2=True, snapshot=True, identity=None, mounted=True):
    approved_identity = {"name": "quantlab", "manifest_sha256": "a" * 64}
    snapshot_identity = identity or approved_identity
    factory = object.__new__(HostPolicyLaunchFactory)
    factory.approved_profile = (
        SimpleNamespace(name="quantlab", identity=approved_identity) if schema2 else None
    )
    grant = SimpleNamespace(identity=SimpleNamespace(token="host"))
    launch = object.__new__(PreparedPolicyLaunch)
    launch.grant = grant
    launch.mount = SimpleNamespace()
    if snapshot:
        launch.private_profile_snapshot = SimpleNamespace(
            name="quantlab", identity=snapshot_identity
        )
        if mounted:
            launch.mount.private_profile_snapshot = launch.private_profile_snapshot
    else:
        launch.private_profile_snapshot = None
    return factory, launch


def test_schema1_preserves_legacy_caller_path():
    factory, launch = _objects(schema2=False, snapshot=False)
    assert require_approved_profile_binding(factory, launch, "quantlab") is None


def test_schema2_accepts_exact_host_profile_and_mount_binding():
    factory, launch = _objects()
    assert require_approved_profile_binding(factory, launch, "quantlab") is launch.private_profile_snapshot


@pytest.mark.parametrize(
    "kwargs",
    [
        {"snapshot": False},
        {"identity": {"name": "quantlab", "manifest_sha256": "b" * 64}},
        {"mounted": False},
    ],
)
def test_schema2_rejects_incomplete_or_stale_profile_binding(kwargs):
    factory, launch = _objects(**kwargs)
    with pytest.raises(SecurityError):
        require_approved_profile_binding(factory, launch, "quantlab")


def test_schema1_rejects_task_selected_private_snapshot():
    factory, launch = _objects(schema2=False, snapshot=True)
    with pytest.raises(SecurityError):
        require_approved_profile_binding(factory, launch, "quantlab")
