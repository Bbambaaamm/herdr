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
