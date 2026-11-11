"""Candidate non-authorizing Hermes host-reference contract.

This file must never be imported by the active Herdr runtime or deployed to
Hermes without a separately approved SDK integration and exact source pin.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import re

class HostReferenceDenied(ValueError):
    """Invalid nonsecret host identity or runtime binding."""

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ENTRY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_ENDPOINT = "https://inference-api.nousresearch.com/v1"

def require(ok):
    if not ok:
        raise HostReferenceDenied("host reference identity mismatch")

@dataclass(frozen=True, slots=True)
class HostCredentialReference:
    provider: str
    entry_id: str
    credential_ref: str
    endpoint: str
    api_mode: str
    model: str
    profile_sha256: str
    projection_sha256: str
    grant_hash: str
    workspace: str
    fence: str
    lineage: str
    tag: str

    def __post_init__(self):
        names = ("provider", "entry_id", "credential_ref", "endpoint", "api_mode",
                 "model", "profile_sha256", "projection_sha256", "grant_hash",
                 "workspace", "fence", "lineage", "tag")
        require(all(type(getattr(self, n)) is str for n in names))
        require(self.provider == "nous" and self.endpoint == _ENDPOINT
                and self.api_mode == "chat_completions" and self.tag == "host_reference")
        require(_ENTRY.fullmatch(self.entry_id) is not None)
        require(self.credential_ref == "pool:nous:" + self.entry_id)
        require(0 < len(self.model) <= 256 and self.model.endswith(":free"))
        require(all(_SHA.fullmatch(x) for x in
                    (self.profile_sha256, self.projection_sha256, self.grant_hash)))
        require(self.workspace.startswith("/") and self.workspace != "/"
                and all(x not in ("", ".", "..") for x in self.workspace[1:].split("/")))
        require(self.fence.isascii() and self.fence.isdecimal()
                and 0 <= int(self.fence) < 2**63 and self.fence == str(int(self.fence)))
        require(0 < len(self.lineage) <= 512 and not any(
            ord(c) < 32 or ord(c) == 127 for c in self.lineage))

@dataclass(frozen=True, slots=True)
class ReferencePool:
    """Read-only nonsecret view; constructing one never conveys authority."""
    provider: str
    current_ref: str
    current_entry_id: str
    _binding: HostCredentialReference = field(repr=False, compare=False)

    def __post_init__(self):
        require(type(self._binding) is HostCredentialReference)
        require(type(self.provider) is str and type(self.current_ref) is str
                and type(self.current_entry_id) is str)
        require(self.provider == self._binding.provider
                and self.current_ref == self._binding.credential_ref
                and self.current_entry_id == self._binding.entry_id)

    def verify_binding(self, reference):
        require(type(reference) is HostCredentialReference
                and reference is self._binding
                and self.current_ref == reference.credential_ref
                and self.current_entry_id == reference.entry_id)

def validate_reference_runtime(reference, *, provider, model, base_url,
                               api_mode, api_key, pool):
    """Never an authorization: Herdr must also verify stage2/grant/fencing."""
    require(type(reference) is HostCredentialReference and type(pool) is ReferencePool)
    require(all(type(x) is str for x in (provider, model, base_url, api_mode)))
    require(provider == reference.provider and model == reference.model
            and base_url == reference.endpoint and api_mode == reference.api_mode)
    require(api_key is None or (type(api_key) is str and api_key == ""))
    pool.verify_binding(reference)


def runtime_for_host_reference(reference, *, model_override=None, runtime_override=None):
    """Return a credentialless fixed-route constructor envelope.

    Only an authenticated Herdr stage-two caller may supply this object.
    The SDK may not grant authority from this envelope; the host transport
    and WorkInvocationGuard must independently approve every model effect.
    """
    require(type(reference) is HostCredentialReference
            and model_override is None and runtime_override is None)
    pool = ReferencePool(reference.provider, reference.credential_ref,
                         reference.entry_id, reference)
    return {
        "model": reference.model,
        "provider": reference.provider,
        "requested_provider": reference.provider,
        "base_url": reference.endpoint,
        "api_mode": reference.api_mode,
        "api_key": None,
        "credential_pool": pool,
        "source": "host-reference",
    }


def assert_host_reference_runtime(agent):
    """Check the original immutable identity at every SDK effect boundary.

    The independently signed Herdr host guard must ALSO verify its own
    admitted reference and reject any missing/changed agent attribute.
    """
    binding = getattr(agent, "_host_reference", None)
    if binding is None:
        return
    require(type(binding) is HostCredentialReference)
    validate_reference_runtime(
        binding, provider=getattr(agent, "provider", None),
        model=getattr(agent, "model", None),
        base_url=getattr(agent, "base_url", None),
        api_mode=getattr(agent, "api_mode", None),
        api_key=getattr(agent, "api_key", None),
        pool=getattr(agent, "_credential_pool", None),
    )
    require(getattr(agent, "fallback_model", None) is None)


def deny_host_reference_mutation(agent):
    """No SDK failover, key rotation or model switch after host admission."""
    if getattr(agent, "_host_reference", None) is not None:
        assert_host_reference_runtime(agent)
        raise HostReferenceDenied("host reference forbids SDK route or credential mutation")


def deny_host_direct_provider_call(agent):
    """No direct SDK network path may carry a Herdr host reference.

    The independently authenticated Herdr WorkInvocationGuard must reserve
    and dispatch the effect using the host transport. Unwrapped SDK calls
    are denied *before* opening a socket, creating a client or emitting tokens.
    """
    if getattr(agent, "_host_reference", None) is not None:
        assert_host_reference_runtime(agent)
        raise HostReferenceDenied("host reference requires guarded host model transport")
