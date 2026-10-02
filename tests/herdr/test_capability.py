"""Contract tests for the offline capability registry."""
import json
from dataclasses import replace

import pytest

from herdr.capability import (
    CapabilityDescriptor, CapabilityError, CapabilityRegistry, CapabilityRequirement,
    CapabilityScope, DataClass, DataPolicy, Egress, ExecutorDescriptor, Health,
    ProviderDescriptor, Reason, RegistrySnapshot, Retention, RuntimeStateSnapshot,
    Training, requirement_from_v1_model_policy,
)
from herdr.taskgraph import TaskNode

NOW = "2026-10-02T10:00:10+00:00"


def policy():
    return DataPolicy(("us-east",), (DataClass.INTERNAL,), Egress.REGION_BOUND,
                      Retention.LIMITED, Training.EXCLUDED)


def fixture():
    cap = CapabilityDescriptor("reason", "1", "logical-spec", ("tools", "json"),
                               ("text",), ("text",), 8192, 4096, 2048, "standard", policy())
    providers = tuple(ProviderDescriptor(x, "1", ("reason",), "prices-1", policy(),
                                         ("http",), ("stateless",)) for x in ("a", "b"))
    executors = tuple(ExecutorDescriptor(f"{x}-runtime", "1", x, "reason", "python",
                                         "adapter", "http", "stateless", ("search",))
                      for x in ("a", "b"))
    registry = CapabilityRegistry(RegistrySnapshot((cap,), providers, executors))
    scope = CapabilityScope(("a", "b"), ("reason",), ("a-runtime", "b-runtime"),
                            ("search",), ("repo:read",), ("us-east",),
                            (DataClass.INTERNAL,), ("text",), ("text",), 100, 8192)
    req = CapabilityRequirement("reason", ("tools",), ("text",), ("text",),
                                ("search",), ("repo:read",), "us-east", DataClass.INTERNAL,
                                Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED,
                                1024, 512, 256, 50)
    states = tuple(RuntimeStateSnapshot(x.id, "2026-10-02T10:00:00+00:00", 30,
                                        Health.HEALTHY, 2, 20, None, registry.snapshot.hash)
                   for x in executors)
    return registry, scope, req, states


def result(registry=None, scope=None, req=None, states=None, at=NOW):
    r, p, q, s = fixture()
    return (registry or r).candidates(req or q, scope or p, s if states is None else states, at=at)


def test_multiple_providers_and_pinned_provenance():
    registry, scope, req, states = fixture()
    found = result(registry, scope, req, states)
    assert json.loads(json.dumps(found.to_json()))["registry_hash"] == registry.snapshot.hash
    assert [x.provider_id for x in found.matches] == ["a", "b"]
    for match in found.matches:
        assert match.provenance.registry_hash == registry.snapshot.hash
        assert match.provenance.capability_hash == registry.snapshot.capabilities[0].hash
        provider = next(x for x in registry.snapshot.providers if x.id == match.provider_id)
        executor = next(x for x in registry.snapshot.executors if x.id == match.executor_id)
        assert match.provenance.provider_hash == provider.hash
        assert match.provenance.executor_hash == executor.hash


def test_scope_serialization_is_schema_versioned():
    _, scope, _, _ = fixture()
    assert scope.to_json()["schema_version"] == VERSION
    assert CapabilityScope.from_dict(scope.to_json()).hash == scope.hash
    with pytest.raises(CapabilityError, match="schema"):
        replace(scope, schema_version="2.0.0")


def test_duplicate_ids_and_schema_versions_rejected():
    registry, _, _, _ = fixture()
    cap = registry.snapshot.capabilities[0]
    with pytest.raises(CapabilityError, match="duplicate"):
        RegistrySnapshot((cap, cap), (), ())
    with pytest.raises(CapabilityError, match="schema"):
        replace(cap, schema_version="2.0.0")
    with pytest.raises(CapabilityError, match="schema"):
        registry.reload({**registry.snapshot.to_json(), "schema_version": "2.0.0"})


def test_canonical_hash_normalization_semantic_change_and_runtime_exclusion():
    registry, _, _, states = fixture()
    cap = registry.snapshot.capabilities[0]
    raw = cap.to_json()
    assert CapabilityDescriptor.from_dict(dict(reversed(list(raw.items())))).hash == cap.hash
    assert replace(cap, features=("json", "tools")).hash == cap.hash
    assert replace(cap, max_output_tokens=1024).hash != cap.hash
    before = registry.snapshot.hash
    replace(states[0], remaining_requests=0, health=Health.DEGRADED, reason_code="limited")
    assert registry.snapshot.hash == before
    with pytest.raises(CapabilityError):
        ProviderDescriptor.from_dict({**registry.snapshot.providers[0].to_json(), "health": "healthy"})


def test_failed_reload_keeps_last_good_snapshot():
    registry, _, _, _ = fixture()
    before = registry.snapshot.hash
    bad = registry.snapshot.to_json()
    bad["executors"][0]["provider_id"] = "ghost"
    with pytest.raises(CapabilityError):
        registry.reload(bad)
    assert registry.snapshot.hash == before
    assert len(registry.snapshot.executors) == 2


def test_unknown_capability_and_unknown_data_fail_closed():
    _, _, req, _ = fixture()
    assert result(req=replace(req, capability_id="ghost")).rejections[0].reason == Reason.UNKNOWN_CAPABILITY
    assert result(req=replace(req, region=None)).rejections[0].reason == Reason.DATA_POLICY_UNKNOWN
    assert result(req=replace(req, training=None)).rejections[0].reason == Reason.DATA_POLICY_UNKNOWN
    registry, scope, _, states = fixture()
    cap = replace(registry.snapshot.capabilities[0], context_tokens=None)
    registry.reload(RegistrySnapshot((cap,), registry.snapshot.providers, registry.snapshot.executors))
    assert result(registry, scope, req, states).rejections[0].reason == Reason.LIMIT_UNKNOWN


def test_compound_scope_partial_order_and_escalation():
    _, parent, _, _ = fixture()
    child = replace(parent, providers=("a",), executors=("a-runtime",), tools=(),
                    regions=("us-east",), data_classes=(DataClass.INTERNAL,),
                    input_modalities=("text",), output_modalities=(),
                    max_cost_microusd=50, max_context_tokens=4096)
    assert child.is_subset_of(parent)
    for widened in (replace(child, providers=("a", "c")),
                    replace(child, tools=("deploy",)),
                    replace(child, regions=("eu",)),
                    replace(child, data_classes=(DataClass.PUBLIC,)),
                    replace(child, max_cost_microusd=101),
                    replace(child, max_context_tokens=None),
                    replace(child, output_modalities=("image",))):
        assert not widened.is_subset_of(parent)
        with pytest.raises(CapabilityError, match="escalates"):
            widened.require_subset_of(parent)


def test_hard_constraint_beats_preference_and_cost():
    registry, scope, req, states = fixture()
    req = replace(req, preferred_providers=("a",))
    states = (replace(states[0], estimated_cost_microusd=90), states[1])
    found = result(registry, scope, req, states)
    assert [x.provider_id for x in found.matches] == ["b"]
    assert found.rejections[0].reason == Reason.BUDGET_EXCEEDED


def test_runtime_freshness_missing_unknown_and_rate_limit():
    registry, scope, req, states = fixture()
    assert result(registry, scope, req, states, at="2026-10-02T10:00:30+00:00").rejections[0].reason == Reason.RUNTIME_STALE
    assert result(registry, scope, req, ()).rejections[0].reason == Reason.RUNTIME_MISSING
    changed = (replace(states[0], health=Health.UNKNOWN, reason_code="probe_failed"), states[1])
    assert result(registry, scope, req, changed).rejections[0].reason == Reason.RUNTIME_UNAVAILABLE
    changed = (replace(states[0], remaining_requests=None), states[1])
    assert result(registry, scope, req, changed).rejections[0].reason == Reason.RATE_LIMITED


def test_secret_like_descriptor_values_rejected():
    registry, _, _, _ = fixture()
    cap = registry.snapshot.capabilities[0]
    with pytest.raises(CapabilityError, match="secret-like"):
        replace(cap, features=("api_key",))
    with pytest.raises(CapabilityError, match="secret-like"):
        CapabilityDescriptor.from_dict({**cap.to_json(), "api_key": "x"})
    with pytest.raises(CapabilityError, match="secret-like"):
        replace(cap, spec_id="AIza" + "A" * 30)


def test_legacy_adapter_preserves_taskgraph_payload_and_scope():
    node = TaskNode.from_dict({"id": "root", "parent_id": None, "type": "task", "role": "worker",
        "objective": "test", "inputs": [], "expected_outputs": [], "dependencies": [],
        "priority": 1, "resource_class": "small",
        "model_policy": {"model": "a", "fallback_model": "b", "legacy_hint": "opaque"},
        "tools": ["search"], "permissions": ["repo:read"]})
    before = node.to_hash_json()
    req = requirement_from_v1_model_policy(node.model_policy, capability_id="reason",
                                           tools=node.tools, permissions=node.permissions)
    assert req.legacy_model_hints == ("a", "b")
    assert req.preferred_providers == ()
    assert req.tools == node.tools and req.permissions == node.permissions
    assert req.region is None and req.data_class is None
    assert node.to_hash_json() == before
    assert node.model_policy == before["model_policy"]


def test_legacy_adapter_preserves_opaque_model_strings():
    req = requirement_from_v1_model_policy(
        {"model": "Claude 3.5 Sonnet", "fallback_model": "vendor/model?mode=fast"},
        capability_id="reason")
    assert req.legacy_model_hints == ("Claude 3.5 Sonnet", "vendor/model?mode=fast")


def test_scope_allows_valid_identifiers_containing_token_substring():
    _, scope, _, _ = fixture()
    changed = replace(scope, providers=("tokenizer-local",), capabilities=("reason-tokenizer",))
    assert changed.providers == ("tokenizer-local",)
    assert changed.capabilities == ("reason-tokenizer",)


def test_legacy_adapter_leaves_opaque_token_limit_keys_opaque():
    # A valid v1 model_policy may carry opaque token-limit keys; they must not be
    # misread as secret material by the compatibility adapter.
    req = requirement_from_v1_model_policy(
        {"model": "a", "fallback_model": "b", "max_tokens": 4096, "token_budget": 100},
        capability_id="reason")
    assert req.legacy_model_hints == ("a", "b")


def test_descriptor_rejects_directional_limit_above_context():
    registry, _, _, _ = fixture()
    cap = registry.snapshot.capabilities[0]
    with pytest.raises(CapabilityError, match="context_tokens"):
        replace(cap, context_tokens=100, max_input_tokens=1000)
    with pytest.raises(CapabilityError, match="context_tokens"):
        replace(cap, context_tokens=100, max_output_tokens=1000)
    # An unknown (null) context window keeps permissive directional handling.
    assert replace(cap, context_tokens=None, max_input_tokens=1000).max_input_tokens == 1000


def test_grant_context_ceiling_applies_to_directional_floors():
    registry, scope, req, states = fixture()
    narrow = replace(scope, max_context_tokens=512)
    # min_context_tokens is unset; the input floor alone must still respect the ceiling.
    r = replace(req, min_context_tokens=None, min_input_tokens=1024)
    found = result(registry, narrow, r, states)
    assert found.matches == ()
    assert found.rejections[0].reason == Reason.POLICY_DENIED


def test_runtime_observation_is_bound_to_exact_registry_snapshot():
    registry, scope, req, states = fixture()
    previous_hash = registry.snapshot.hash
    changed = replace(registry.snapshot.executors[0], version="2")
    registry.reload(RegistrySnapshot(
        registry.snapshot.capabilities,
        registry.snapshot.providers,
        (changed, registry.snapshot.executors[1]),
    ))
    assert registry.snapshot.hash != previous_hash
    stale = result(registry, scope, req, states)
    assert stale.matches == ()
    assert {item.reason for item in stale.rejections} == {Reason.RUNTIME_STALE}

    fresh_states = tuple(replace(state, registry_hash=registry.snapshot.hash) for state in states)
    fresh = result(registry, scope, req, fresh_states)
    assert [item.provider_id for item in fresh.matches] == ["a", "b"]


def test_direct_runtime_reason_code_rejects_secret_values():
    with pytest.raises(CapabilityError, match="secret-like"):
        RuntimeStateSnapshot(
            "a-runtime", "2026-10-02T10:00:00+00:00", 30,
            Health.DEGRADED, 1, 1, "ghp_" + "A" * 24, "a" * 64,
        )


def test_runtime_ttl_is_bounded_and_never_overflows():
    with pytest.raises(CapabilityError, match="bounded"):
        RuntimeStateSnapshot("a-runtime", "2026-10-02T10:00:00+00:00", 10 ** 12,
                             Health.HEALTHY, 1, 1, None, "a" * 64)
    near_max = RuntimeStateSnapshot("a-runtime", "9999-12-31T23:59:59+00:00", 30,
                                    Health.HEALTHY, 1, 1, None, "a" * 64)
    assert near_max.is_fresh("9999-12-31T23:59:59+00:00") is True
    assert near_max.is_fresh("9999-12-31T23:59:58+00:00") is False


def test_registry_hash_reused_across_all_provenance_records():
    cap = CapabilityDescriptor("reason", "1", "logical-spec", ("tools",), ("text",),
                               ("text",), 8192, 4096, 2048, "standard", policy())
    providers = tuple(ProviderDescriptor(x, "1", ("reason",), "prices-1", policy(),
                                         ("http",), ("stateless",)) for x in "abcd")
    executors = tuple(ExecutorDescriptor(f"{x}-runtime", "1", x, "reason", "python",
                                         "adapter", "http", "stateless", ("search",))
                      for x in "abcd")
    registry = CapabilityRegistry(RegistrySnapshot((cap,), providers, executors))
    scope = CapabilityScope(("a", "b", "c", "d"), ("reason",),
                            tuple(f"{x}-runtime" for x in "abcd"), ("search",),
                            ("repo:read",), ("us-east",), (DataClass.INTERNAL,),
                            ("text",), ("text",), 100, 8192)
    req = CapabilityRequirement("reason", ("tools",), ("text",), ("text",), ("search",),
                                ("repo:read",), "us-east", DataClass.INTERNAL,
                                Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED,
                                1024, 512, 256, 50)
    states = tuple(RuntimeStateSnapshot(x.id, "2026-10-02T10:00:00+00:00", 30,
                                        Health.HEALTHY, 2, 20, None, registry.snapshot.hash)
                   for x in executors)
    found = registry.candidates(req, scope, states, at=NOW)
    assert len(found.matches) == 4
    assert all(m.provenance.registry_hash == found.registry_hash for m in found.matches)
