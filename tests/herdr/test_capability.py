"""Contract tests for the offline capability registry."""
import json
from dataclasses import replace

import pytest

from herdr.capability import (
    CapabilityDescriptor, CapabilityError, CapabilityRegistry, CapabilityRequirement,
    CapabilityScope, DataClass, DataPolicy, Egress, ExecutorDescriptor, Feature, Health,
    ProviderDescriptor, Reason, RegistrySnapshot, Retention, RuntimeStateSnapshot, Latency, MAX_INTEGER,
    Training, VERSION, requirement_from_v1_model_policy,
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
                            (DataClass.INTERNAL,), ("text",), ("text",), 100, 8192,
                            Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED)
    req = CapabilityRequirement("reason", ("tools",), ("text",), ("text",),
                                ("search",), ("repo:read",), "us-east", DataClass.INTERNAL,
                                Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED,
                                1024, 512, 256, 50)
    states = tuple(RuntimeStateSnapshot(x.id, "2026-10-02T10:00:00+00:00", 30,
                                        Health.HEALTHY, 2, 20, None, registry.snapshot.hash,
                                        req.hash)
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
                    replace(child, max_egress=Egress.GLOBAL),
                    replace(child, max_retention=Retention.INDEFINITE),
                    replace(child, training=Training.ALLOWED),
                    replace(child, output_modalities=("image",))):
        assert not widened.is_subset_of(parent)
        with pytest.raises(CapabilityError, match="escalates"):
            widened.require_subset_of(parent)


def test_hard_constraint_beats_preference_and_cost():
    registry, scope, req, states = fixture()
    req = replace(req, preferred_providers=("a",))
    states = tuple(replace(state, requirement_hash=req.hash) for state in states)
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
            Health.DEGRADED, 1, 1, "ghp_" + "A" * 24, "a" * 64, "b" * 64,
        )


def test_runtime_ttl_is_bounded_and_never_overflows():
    with pytest.raises(CapabilityError, match="bounded"):
        RuntimeStateSnapshot("a-runtime", "2026-10-02T10:00:00+00:00", 10 ** 12,
                             Health.HEALTHY, 1, 1, None, "a" * 64, "b" * 64)
    near_max = RuntimeStateSnapshot("a-runtime", "9999-12-31T23:59:59+00:00", 30,
                                    Health.HEALTHY, 1, 1, None, "a" * 64, "b" * 64)
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
                            ("text",), ("text",), 100, 8192,
                            Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED)
    req = CapabilityRequirement("reason", ("tools",), ("text",), ("text",), ("search",),
                                ("repo:read",), "us-east", DataClass.INTERNAL,
                                Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED,
                                1024, 512, 256, 50)
    states = tuple(RuntimeStateSnapshot(x.id, "2026-10-02T10:00:00+00:00", 30,
                                        Health.HEALTHY, 2, 20, None, registry.snapshot.hash,
                                        req.hash)
                   for x in executors)
    found = registry.candidates(req, scope, states, at=NOW)
    assert len(found.matches) == 4
    assert all(m.provenance.registry_hash == found.registry_hash for m in found.matches)


def test_required_ucl_capability_dimensions_are_typed():
    required = (
        "reasoning", "coding", "vision", "audio", "realtime", "research",
        "computer_use", "ocr_document", "tool_use", "structured_output", "mcp", "a2a",
    )
    assert tuple(Feature(x).value for x in required) == required


def test_legacy_tools_feature_normalizes_before_hash_and_matching():
    registry, scope, req, states = fixture()
    cap = registry.snapshot.capabilities[0]
    assert cap.features == (Feature.JSON, Feature.TOOL_USE)
    assert replace(cap, features=("json", "tool_use")).hash == cap.hash
    canonical = replace(req, features=("tool_use",))
    canonical_states = tuple(replace(state, requirement_hash=canonical.hash) for state in states)
    assert result(registry, scope, canonical, canonical_states).matches


def test_delegated_data_policy_limits_are_closed_and_enforced():
    registry, scope, req, states = fixture()
    restrictive = replace(scope, max_egress=Egress.NONE, max_retention=Retention.ZERO)
    assert restrictive.is_subset_of(scope)
    denied = result(registry, restrictive, req, states)
    assert denied.matches == ()
    assert denied.rejections[0].reason == Reason.DATA_POLICY_DENIED

    with pytest.raises(CapabilityError, match="escalates"):
        replace(scope, max_egress=Egress.GLOBAL).require_subset_of(scope)
    with pytest.raises(CapabilityError, match="escalates"):
        replace(scope, max_retention=Retention.INDEFINITE).require_subset_of(scope)
    with pytest.raises(CapabilityError, match="escalates"):
        replace(scope, training=Training.ALLOWED).require_subset_of(scope)


def test_cost_estimate_is_bound_to_exact_requirement():
    registry, scope, req, states = fixture()
    larger = replace(req, min_input_tokens=req.min_input_tokens + 1)
    found = result(registry, scope, larger, states)
    assert found.matches == ()
    assert {item.reason for item in found.rejections} == {Reason.PRICE_UNKNOWN}

    rebound = tuple(replace(state, requirement_hash=larger.hash) for state in states)
    assert result(registry, scope, larger, rebound).matches


def test_combined_directional_floors_must_fit_context_window_and_grant():
    registry, scope, req, states = fixture()

    # Each directional floor fits independently, but the combined request does
    # not fit the capability's 8192-token shared context window.
    too_large_for_cap = replace(
        req,
        min_context_tokens=None,
        min_input_tokens=7000,
        min_output_tokens=2000,
    )
    found = result(registry, scope, too_large_for_cap, states)
    assert found.matches == ()
    assert found.rejections[0].reason == Reason.LIMIT_EXCEEDED

    # The capability can fit this pair, but a narrower delegated grant cannot.
    narrower_grant = replace(scope, max_context_tokens=4096)
    too_large_for_grant = replace(
        req,
        min_context_tokens=None,
        min_input_tokens=3000,
        min_output_tokens=2000,
    )
    found = result(registry, narrower_grant, too_large_for_grant, states)
    assert found.matches == ()
    assert found.rejections[0].reason == Reason.POLICY_DENIED


@pytest.mark.parametrize("direction", ["input", "output"])
def test_directional_floor_rejects_unknown_shared_context(direction):
    registry, scope, req, states = fixture()
    cap = replace(registry.snapshot.capabilities[0], context_tokens=None)
    registry.reload(RegistrySnapshot((cap,), registry.snapshot.providers, registry.snapshot.executors))
    directional = replace(req, min_context_tokens=None,
                          min_input_tokens=512 if direction == "input" else None,
                          min_output_tokens=256 if direction == "output" else None)
    fresh_states = tuple(replace(state, registry_hash=registry.snapshot.hash,
                                requirement_hash=directional.hash) for state in states)
    found = result(registry, scope, directional, fresh_states)
    assert not found.matches
    assert {item.reason for item in found.rejections} == {Reason.LIMIT_UNKNOWN}


@pytest.mark.parametrize("credential", ["ghp_" + "A" * 24, "AIza" + "A" * 30])
def test_runtime_executor_identity_rejects_credentials_in_both_construction_paths(credential):
    _, _, _, states = fixture()
    with pytest.raises(CapabilityError, match="secret-like"):
        replace(states[0], executor_id=credential)
    with pytest.raises(CapabilityError, match="secret-like"):
        RuntimeStateSnapshot.from_dict({**states[0].to_json(), "executor_id": credential})

@pytest.mark.parametrize("declared,maximum,allowed", [
    ("interactive", "interactive", True),
    ("standard", "interactive", False),
    ("batch", "standard", False),
    ("interactive", "batch", True),
    ("batch", None, True),
])
def test_latency_ceiling_is_a_hard_constraint(declared, maximum, allowed):
    registry, scope, req, states = fixture()
    cap = replace(registry.snapshot.capabilities[0], latency=declared)
    registry.reload(RegistrySnapshot((cap,), registry.snapshot.providers, registry.snapshot.executors))
    req = replace(req, max_latency=maximum, preferred_providers=("a",))
    assert CapabilityRequirement.from_dict(req.to_json()).hash == req.hash
    states = tuple(replace(s, registry_hash=registry.snapshot.hash, requirement_hash=req.hash) for s in states)
    found = result(registry, scope, req, states)
    assert bool(found.matches) is allowed
    if not allowed:
        assert {r.reason for r in found.rejections} == {Reason.LATENCY_EXCEEDED}


@pytest.mark.parametrize("field", ["capabilities", "providers", "executors"])
@pytest.mark.parametrize("malformed", [None, 1, "bad", {}])
def test_malformed_reload_collections_preserve_snapshot(field, malformed):
    registry, _, _, _ = fixture()
    previous = registry.snapshot
    raw = previous.to_json()
    raw[field] = malformed
    with pytest.raises(CapabilityError, match="must be an array"):
        registry.reload(raw)
    assert registry.snapshot is previous


def test_numeric_contract_bounds_preserve_hashability():
    registry, scope, req, states = fixture()
    cap = registry.snapshot.capabilities[0]
    assert replace(cap, context_tokens=MAX_INTEGER).hash
    for value in (MAX_INTEGER + 1, 10 ** 5000):
        for factory in (
            lambda: replace(cap, context_tokens=value),
            lambda: replace(scope, max_cost_microusd=value),
            lambda: replace(req, min_input_tokens=value),
            lambda: replace(states[0], remaining_requests=value),
        ):
            with pytest.raises(CapabilityError, match="bounded"):
                factory()
