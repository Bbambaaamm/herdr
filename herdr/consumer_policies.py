"""Consumer-specific Herdr admission policy overlays.

Core admission remains provider/consumer neutral. These overlays are selected
explicitly by runtime profile; unknown profiles fail closed.
"""
from __future__ import annotations

from collections.abc import Sequence

from .admission import AgentIdentity, ConsumerPolicyHook

SECRET_INDICATORS = (
    "api_key",
    "api_secret",
    "secret_key",
    "private_key",
    "client_secret",
    "token",
    "password",
)

EXTERNAL_NETWORK_MUTATION_SUFFIXES = (".post", ".put", ".patch", ".upload")

QUANTLAB_LIVE_TOOL_PREFIXES = (
    "alpaca-order",
    "alpaca-position",
    "alpaca-sse",
    "broker",
    "live-broker",
    "trade",
    "execution",
    "risk-engine",
    "alpaca",
)

QUANTLAB_PROTECTED_PATHS = (
    "backend/src/quantlab/trading.py",
    "backend/src/quantlab/phase4.py",
    "backend/src/quantlab/security.py",
)


def allow_all_consumer_policy(
    identity: AgentIdentity, tools: Sequence[str]
) -> str | None:
    """Test/local policy only; production runtimes select a named profile."""
    return None


def base_consumer_policy(identity: AgentIdentity, tools: Sequence[str]) -> str | None:
    for tool in tools:
        lowered = tool.lower()
        if any(indicator in lowered for indicator in SECRET_INDICATORS):
            return "secret_access"
        if any(lowered.endswith(suffix) for suffix in EXTERNAL_NETWORK_MUTATION_SUFFIXES):
            return "external_network_policy"
    return None


def quantlab_paper_policy(
    identity: AgentIdentity, tools: Sequence[str]
) -> str | None:
    if identity.paper_only is not True:
        return "paper_only_required"
    common = base_consumer_policy(identity, tools)
    if common is not None:
        return common
    for tool in tools:
        lowered = tool.lower()
        if any(lowered.startswith(prefix) for prefix in QUANTLAB_LIVE_TOOL_PREFIXES):
            return "live_trading_tool"
        if any(path in lowered for path in QUANTLAB_PROTECTED_PATHS):
            return "protected_path"
    return None


def _unknown_policy(profile: str) -> ConsumerPolicyHook:
    def deny_unknown(identity: AgentIdentity, tools: Sequence[str]) -> str | None:
        return "unknown_consumer_profile"
    return deny_unknown


def policy_for_profile(profile: str) -> ConsumerPolicyHook:
    policies: dict[str, ConsumerPolicyHook] = {
        "quantlab": quantlab_paper_policy,
        "quantlab-paper": quantlab_paper_policy,
        "majak": base_consumer_policy,
        "heating": base_consumer_policy,
    }
    return policies.get(profile, _unknown_policy(profile))
