from dataclasses import replace

import pytest

from herdr.capability import (
    CapabilityDescriptor, CapabilityScope, DataClass, DataPolicy, Egress,
    ExecutorDescriptor, ProviderDescriptor, RegistrySnapshot, Retention, Training,
)
from herdr.grant_factory import BrokerRoute, HostGrantContext, build_host_grant
PINNED_EXECUTOR = "hermes:0.21.5:sha256:" + "a" * 64

from herdr.security import (
    InvocationIdentity, NetworkAccess, ProcessPolicy, RiskClass,
    RuntimeAssurance, SecurityError, ToolRule,
)


def inputs(tmp_path):
    policy = DataPolicy(("eu-central",), (DataClass.INTERNAL,), Egress.REGION_BOUND,
                        Retention.LIMITED, Training.EXCLUDED)
    capability = CapabilityDescriptor("reason", "1", "spec", ("tool_use",),
                                      ("text",), ("text",), 8192, 4096, 2048,
                                      "standard", policy)
    provider = ProviderDescriptor("provider-a", "1", ("reason",), "prices-1",
                                  policy, ("openai",), ("stateless",))
    executor = ExecutorDescriptor(PINNED_EXECUTOR, "0.21.5", "provider-a", "reason",
                                  "python-3.11", "hermes-agent", "openai", "stateless", ("read_file",))
    registry = RegistrySnapshot((capability,), (provider,), (executor,))
    scope = CapabilityScope(("provider-a",), ("reason",), (PINNED_EXECUTOR,),
                            ("read_file",), ("repo:read",), ("eu-central",),
                            (DataClass.INTERNAL,), ("text",), ("text",), 1000, 8192,
                            Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED)
    identity = InvocationIdentity("github:owner/repo", "root", "scheduler", "schedule",
                                  "task", "run", 7)
    context = HostGrantContext("grant", str(tmp_path), identity,
                               "2026-01-01T00:00:00+00:00", "2030-01-01T00:00:00+00:00")
    broker = (BrokerRoute("provider-a", "https://provider.example.invalid/v1", "openai",
                          ("pool:provider-a:entry-1",)),)
    return dict(context=context, scope=scope, tool_rules=(ToolRule(
        "read_file", RiskClass.READ, ("path",), ("path",), (str(tmp_path),)),),
        process=ProcessPolicy(False, (), NetworkAccess.NONE), parent=None,
        registry=registry, broker_inventory=broker,
        assurance=RuntimeAssurance(False, None, NetworkAccess.NONE, (), True))


def test_host_factory_derives_route_and_exact_child_parent(tmp_path):
    kwargs = inputs(tmp_path)
    root = build_host_grant(**kwargs)
    assert root.parent_grant_hash is None
    assert root.provider_routes[0].base_url == kwargs["broker_inventory"][0].base_url
    assert root.credential_refs == ("pool:provider-a:entry-1",)
    child_identity = replace(kwargs["context"].identity, agent_id="child",
                             parent_agent_id="root", parent_task_id="task", task_id="child-task")
    child = build_host_grant(**{**kwargs, "context": replace(kwargs["context"], identity=child_identity),
                                "parent": root})
    assert child.parent_grant_hash == root.hash
    child.require_subset_of(root)
    with pytest.raises(SecurityError, match="child parent identity mismatch"):
        build_host_grant(**{**kwargs, "parent": root})


def test_host_factory_rejects_unregistered_or_unbrokered_authority(tmp_path):
    kwargs = inputs(tmp_path)
    with pytest.raises(SecurityError, match="exactly cover"):
        build_host_grant(**{**kwargs, "broker_inventory": ()})
    with pytest.raises(SecurityError, match="API mode"):
        build_host_grant(**{**kwargs, "broker_inventory": (
            replace(kwargs["broker_inventory"][0], api_mode="anthropic_messages"),)})
    with pytest.raises(SecurityError, match="absent from registry"):
        build_host_grant(**{**kwargs, "scope": replace(kwargs["scope"],
                                                        executors=("unregistered",))})
    with pytest.raises(SecurityError, match="secret material"):
        build_host_grant(**{**kwargs, "broker_inventory": (
            replace(kwargs["broker_inventory"][0],
                    credential_refs=("sk-abcdefghijklmnopqrstuvwxyz123456",)),)})


def test_host_factory_preserves_narrowest_capability_privacy_ceiling(tmp_path):
    kwargs = inputs(tmp_path)
    registry = kwargs["registry"]
    capability = replace(
        registry.capabilities[0],
        data_policy=DataPolicy(
            ("eu-central",), (DataClass.INTERNAL,), Egress.REGION_BOUND,
            Retention.ZERO, Training.EXCLUDED,
        ),
    )
    provider = replace(
        registry.providers[0],
        data_policy=DataPolicy(
            ("eu-central",), (DataClass.INTERNAL,), Egress.GLOBAL,
            Retention.INDEFINITE, Training.ALLOWED,
        ),
    )
    broader_scope = replace(
        kwargs["scope"], max_egress=Egress.GLOBAL,
        max_retention=Retention.INDEFINITE, training=Training.ALLOWED,
    )
    grant = build_host_grant(**{
        **kwargs,
        "scope": broader_scope,
        "registry": RegistrySnapshot((capability,), (provider,), registry.executors),
    })
    route = grant.provider_routes[0]
    assert route.max_egress is Egress.REGION_BOUND
    assert route.max_retention is Retention.ZERO
    assert route.training is Training.EXCLUDED


def test_narrow_scope_does_not_relabel_a_broader_provider_guarantee(tmp_path):
    kwargs=inputs(tmp_path);registry=kwargs["registry"]
    policy=replace(registry.providers[0].data_policy,egress=Egress.GLOBAL)
    broader=replace(registry.providers[0],data_policy=policy)
    with pytest.raises(SecurityError,match="exceeds admitted scope"):
        build_host_grant(**{**kwargs,"registry":RegistrySnapshot(registry.capabilities,(broader,),registry.executors)})
