"""Negative tests for review-only Hermes patch, no SDK/provider calls."""
import dataclasses
import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "integrations/hermes-patches/agent/host_reference.py"
spec = importlib.util.spec_from_file_location("candidate_host_reference", CANDIDATE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def reference(**changes):
    args = dict(provider="nous", entry_id="approved-1",
                credential_ref="pool:nous:approved-1",
                endpoint="https://inference-api.nousresearch.com/v1",
                api_mode="chat_completions", model="Hermes-4:free",
                profile_sha256="a"*64, projection_sha256="b"*64,
                grant_hash="c"*64, workspace="/home/agentops/worktrees/test",
                fence="7", lineage="approved-parent-task", tag="host_reference")
    args.update(changes)
    return module.HostCredentialReference(**args)

def test_nonsecret_immutable_binding():
    ref = reference()
    pool = module.ReferencePool("nous", ref.credential_ref, ref.entry_id, ref)
    module.validate_reference_runtime(ref, provider="nous", model=ref.model,
                                      base_url=ref.endpoint, api_mode=ref.api_mode,
                                      api_key=None, pool=pool)
    assert not hasattr(ref, "api_key") and not hasattr(pool, "runtime_api_key")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.model = "other:free"

@pytest.mark.parametrize("change", [
    {"provider": "openai"}, {"entry_id": "../bad"},
    {"credential_ref": "pool:nous:another"}, {"endpoint": "https://attacker.invalid"},
    {"api_mode": "anthropic_messages"}, {"model": "Hermes-4"},
    {"profile_sha256": "bad"}, {"projection_sha256": "0"*64+"a"},
    {"grant_hash": "A"*64}, {"workspace": "/tmp/../etc"},
    {"fence": "-1"}, {"fence": "007"}, {"lineage": ""},
    {"tag": "other"}, {"model": 7},
])
def test_invalid_reference_denied(change):
    with pytest.raises(module.HostReferenceDenied):
        reference(**change)

@pytest.mark.parametrize("change", [
    {"provider": "other"}, {"model": "different:free"},
    {"base_url": "https://example.invalid"}, {"api_mode": "other"},
    {"api_key": "SECRET"},
])
def test_sdk_route_and_raw_credential_denied(change):
    ref = reference()
    pool = module.ReferencePool("nous", ref.credential_ref, ref.entry_id, ref)
    kwargs = dict(provider="nous", model=ref.model, base_url=ref.endpoint,
                  api_mode=ref.api_mode, api_key="", pool=pool)
    kwargs.update(change)
    with pytest.raises(module.HostReferenceDenied):
        module.validate_reference_runtime(ref, **kwargs)

def test_forged_pool_and_distinct_reference_denied():
    ref = reference()
    with pytest.raises(module.HostReferenceDenied):
        module.ReferencePool("nous", "pool:nous:other", ref.entry_id, ref)
    pool = module.ReferencePool("nous", ref.credential_ref, ref.entry_id, ref)
    with pytest.raises(module.HostReferenceDenied):
        module.validate_reference_runtime(reference(), provider="nous", model=ref.model,
                                          base_url=ref.endpoint, api_mode=ref.api_mode,
                                          api_key=None, pool=pool)

def test_extra_or_missing_authenticated_fields_denied():
    with pytest.raises(TypeError):
        module.HostCredentialReference(provider="nous")
    with pytest.raises(TypeError):
        module.HostCredentialReference(**{**dataclasses.asdict(reference()), "extra": "bad"})
