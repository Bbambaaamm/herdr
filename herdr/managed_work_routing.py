"""Router v5 admission for the existing authenticated ordinary work launcher."""
import json
from dataclasses import fields
from datetime import datetime, timezone

from .capability import CapabilityRegistry, CapabilityRequirement, CapabilityScope, RuntimeStateSnapshot
from .evidence import EvidenceMissing, binding, digest
from .routing import RoutingDecision
from .scheduler_routing import ManagedRoute, RoutingInput
from .scheduler import AuditLog, DynamicChildScheduler
from .work_cycle import require
from .work_planning import closed


def bind_managed_work_route(factory, task, launch, parent):
    """Issue once under the existing parent journal lock, then recheck on use."""
    definition = factory.host_admission["definition"]
    inputs = definition.get("managed_routing")
    policy = parent.graph.nodes[0].model_policy if parent is not None else {}
    managed = policy.get("routing_v5", {}).get("enabled") is True
    if inputs is None and not managed:
        return
    require(managed and inputs is not None, "reviewed managed routing inputs required")
    from agent_durable_children import _read_control_file, attempt_directory, ledger_required, parent_attempt_guard
    from .work_configuration import _original_work_admission

    closed(inputs, ("registry", "requirement", "scope", "runtime_state"), "managed routing inputs")
    registry = CapabilityRegistry(inputs["registry"])
    requirement = CapabilityRequirement.from_dict(inputs["requirement"])
    scope = CapabilityScope.from_dict(inputs["scope"])
    observations = tuple(RuntimeStateSnapshot.from_dict(row) for row in inputs["runtime_state"])
    root = factory.task_store_root
    grant = launch.grant
    identity = grant.identity
    directory = attempt_directory(root, identity.task_id, identity.run_token)
    route_policy = policy["routing_v5"]
    allocation = factory.allocations[digest(identity.to_json())]
    attempt_binding = binding(task)
    route_attempt = attempt_binding["attempt"] + 1

    def read_scheduler():
        require(ledger_required(directory) and (directory / "scheduler.jsonl").is_file(),
                "original managed attempt journal unavailable")
        scheduler = DynamicChildScheduler(audit_log=AuditLog(directory / "scheduler.jsonl"))
        scheduler.replay()
        record = scheduler.record_for(identity.task_id)
        require(record.canonical_parent and record.canonical_parent["admission"] == parent.to_json()
                and record.idempotency_key == attempt_binding["idempotency_key"]
                and grant.is_active(), "managed work authority changed")
        return scheduler

    def handoff_for(scheduler, route):
        return scheduler.prepare_managed_execution_handoff(route, identity=identity,
            registry=registry, requirement=requirement, policy=scope, budget_gate=factory.budget_authority)

    with parent_attempt_guard(root, identity.task_id, identity.run_token):
        scheduler = read_scheduler()
        key = digest({"managed_route": attempt_binding})
        store = factory.result_authority.store
        try:
            original_record = store.read("plan", key)
        except EvidenceMissing:
            original_record = None
        if original_record is None:
            route = scheduler.select_managed_route(identity.task_id, registry=registry,
                requirement=requirement, policy=scope, runtime_state=observations,
                at=datetime.now(timezone.utc).isoformat(), policy_version=route_policy["policy_version"],
                budget_gate=factory.budget_authority, budget_allocation_id=allocation.allocation_id,
                identity=identity, expected_registry_hash=route_policy["registry_hash"],
                expected_requirement_hash=route_policy["requirement_hash"], attempt=route_attempt)
        else:
            event = original_record["routing"]
            route = ManagedRoute(RoutingInput(**{f.name: event[f.name] for f in fields(RoutingInput)}),
                                 RoutingDecision.from_json(event["decision"]))
            require(route.routing_input.attempt == route_attempt
                    and route.routing_input.budget_allocation_id == allocation.allocation_id,
                    "retained managed routing attempt changed")
        issued = handoff_for(scheduler, route)
        require(issued.selected_provider in grant.scope.providers
                and tuple(grant.scope.executors) == (issued.selected_executor,),
                "managed route differs from sealed launch")
        receipt = {"identity": attempt_binding, "role": parent.graph.nodes[0].role, "grant_sha256": grant.hash,
                   "graph_sha256": parent.graph_sha256, "routing": route.audit_event()}
        if original_record is None:
            store.publish("plan", key, receipt)
        require(store.read("plan", key) == receipt, "managed decision receipt changed")

    def authorize(caller, grant_sha256, *, provider=None, model=None):
        require(caller == identity and grant_sha256 == grant.hash, "managed route grant mismatch")
        with parent_attempt_guard(root, identity.task_id, identity.run_token):
            current_task = json.loads(_read_control_file(root / "running" / (identity.task_id + ".json")))
            require(binding(current_task) == attempt_binding
                    and current_task.get("execution_session", {}).get("launch_identity") == identity.to_json()
                    and not current_task["execution_session"].get("closed_at"),
                    "ordinary task no longer owns managed attempt")
            _, original = _original_work_admission(root, current_task, factory.host_configuration_path)
            require(original == factory.host_admission and binding(task) == attempt_binding
                    and factory.allocations.get(digest(identity.to_json())) == allocation,
                    "managed work admission changed")
            require(store.read("plan", key) == receipt, "managed decision receipt changed")
            current = handoff_for(read_scheduler(), route)
            at = datetime.now(timezone.utc).isoformat()
            require(current == issued and any(row.executor_id == issued.selected_executor
                    and row.is_fresh(at) for row in observations), "managed route expired or changed")
            current.authorize_identity(identity=caller, provider=provider, model=model)
            current.assert_dispatchable(at)
            return current

    factory.managed_work_route = authorize
    factory.issued_work_route = issued


def authorize_managed_effect(factory, identity, grant_sha256, provider, model):
    definition = getattr(factory, "host_admission", {}).get("definition", {})
    if "managed_routing" not in definition:
        return None
    authorize = getattr(factory, "managed_work_route", None)
    require(callable(authorize), "managed route unavailable for this attempt")
    require(isinstance(provider, str) and provider and isinstance(model, str) and model,
            "exact managed model and provider required")
    return authorize(identity, grant_sha256, provider=provider, model=model)

