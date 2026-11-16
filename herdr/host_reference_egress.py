"""Fail-closed native egress admission for a host-authenticated Hermes reference.

Distinct from Hermes SDK checks. A signed/observed RuntimeAssurance must
already originate from the protected Herdr sandbox admission. A value in
this object is NOT proof of kernel isolation on its own.
"""
from __future__ import annotations

from .security import NetworkAccess, PolicyDenied


def require_network_isolated_host_reference(grant) -> None:
    """Deny any host-reference activation with host/global network access.

    Until the native broker is redesigned for an independent network
    namespace, this gate deliberately prevents live host-reference mode.
    """
    assurance = getattr(grant, "runtime_assurance", None)
    network = getattr(assurance, "network_access", None)
    verified = getattr(assurance, "sandbox_verified", None)
    if (type(network) is not NetworkAccess
            or network is not NetworkAccess.NONE
            or verified is not True):
        raise PolicyDenied("host_reference_native_network_isolation_required")
