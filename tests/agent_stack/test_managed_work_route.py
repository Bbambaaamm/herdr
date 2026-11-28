"""Exercise the ordinary canonical claim and its immutable routing evidence."""
from dataclasses import replace
from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from herdr.evidence import EvidenceStore, digest
from herdr.managed_work_routing import authorize_managed_effect, bind_managed_work_route
from herdr.work_cycle import WorkContractError
from tests.agent_stack.test_canonical_parent_binding import children, descriptor, binding
from tests.herdr.test_scheduler_routing import route_kwargs, task_node
from tests.herdr.test_work_budget import allocation, authority
from herdr.work_budget import reserve_host_phase_overhead


def test_canonical_work_route_is_issued_and_revalidated_for_same_attempt(tmp_path, monkeypatch):
    args = route_kwargs()
    parent = descriptor()
    node = task_node(task_id=parent.identity.task_id)
    graph = replace(parent.graph, nodes=(node,), envelope=replace(parent.graph.envelope, policy_profile="default"))
    parent = replace(parent, graph=graph, graph_sha256=graph.graph_hash())
    identity = parent.identity
    init = dict(binding(), role=node.role, tools=node.tools, permissions=node.permissions, policy_profile="default")
    directory = children.ensure_attempt_directory(tmp_path, identity.task_id, identity.run_token)
    children.initialize_parent_scheduler(directory, canonical_parent=parent, **init)
    task = {"id":identity.task_id, "run_token":identity.run_token, "idempotency_key":parent.idempotency_key,
            "fencing_token":identity.fencing_token, "attempt_id":0,
            "execution_session":{"launch_identity":identity.to_json()}}
    (tmp_path / "running").mkdir()
    running = tmp_path / "running" / (identity.task_id + ".json")
    running.write_text(json.dumps(task))
    now = datetime.now(timezone.utc).isoformat()
    definition = {"managed_routing": {"registry":args["registry"].snapshot.to_json(),
        "scope":args["policy"].to_json(), "requirement":args["requirement"].to_json(),
        "runtime_state":[replace(row, observed_at=now).to_json() for row in args["runtime_state"]]}}
    approved = replace(allocation(max_work_ms=300000, max_elapsed_ms=300000), consumer=identity.consumer)
    budget, _, _ = authority(tmp_path / "budget", approved)
    reserve_host_phase_overhead(budget, approved, SimpleNamespace(identity=identity, hash="e"*64), "baseline")
    snapshot = budget.snapshot(approved.allocation_id)
    assert snapshot["unknown_measurements"] == ["work_ms"]
    assert snapshot["charged_upper_bounds"]["work_ms"] == 120000
    factory = SimpleNamespace(task_store_root=tmp_path, host_admission={"definition":definition},
        host_configuration_path=tmp_path / "policy", budget_authority=budget,
        allocations={digest(identity.to_json()):approved},
        result_authority=SimpleNamespace(store=EvidenceStore(tmp_path / "evidence")))
    monkeypatch.setattr("herdr.work_configuration._original_work_admission",
                        lambda *_: (None, factory.host_admission))
    grant = SimpleNamespace(identity=identity, hash="d"*64, is_active=lambda:True,
                            scope=SimpleNamespace(providers=("a",), executors=("a-runtime",)))
    launch = SimpleNamespace(grant=grant)
    with pytest.raises(WorkContractError, match="managed route unavailable"):
        authorize_managed_effect(factory, identity, grant.hash, "a", "logical-spec")
    bind_managed_work_route(factory, task, launch, parent)
    selected = authorize_managed_effect(factory, identity, grant.hash, "a", "logical-spec")
    assert selected.attempt == 1 and selected.selected_model != node.model_policy["model"]
    assert selected.decision_sha256 == factory.issued_work_route.decision_sha256
    monkeypatch.setattr("herdr.scheduler.DynamicChildScheduler.select_managed_route",
                        lambda *a, **kw: pytest.fail("replay must retain the issued decision"))
    bind_managed_work_route(factory, task, launch, parent)
    assert authorize_managed_effect(factory, identity, grant.hash, "a", "logical-spec") == selected
    running.write_text(json.dumps(dict(task, fencing_token=task["fencing_token"]+1)))
    with pytest.raises(WorkContractError, match="no longer owns"):
        authorize_managed_effect(factory, identity, grant.hash, "a", "logical-spec")



def test_two_fixture_operations_and_ambiguous_third_keep_separate_original_reservations(tmp_path):
    import threading
    from herdr import host_model_transport as transport
    from herdr.work_budget_configuration import model_effect
    from herdr.work_cycle import WorkPhase
    from tests.herdr.test_work_budget import identity as budget_identity

    caller = budget_identity()
    approved = allocation(max_tokens=20000)
    budget, _, _ = authority(tmp_path / "budget", approved)
    cycle = SimpleNamespace(phase=WorkPhase.WORK, plan=SimpleNamespace(hash="b"*64, grant_sha256="d"*64))
    selected = SimpleNamespace(budget_allocation_id=approved.allocation_id)
    model = "synthetic:free"
    endpoint = transport.ENDPOINT
    route = {"provider":"nous", "model":model, "api_mode":"chat_completions", "base_url":endpoint}
    quote = dict(route, max_tokens=2000, max_work_ms=100, max_output_tokens=100,
                 max_request_bytes=1900, max_cost_microusd=0)
    factory = SimpleNamespace(_lock=threading.RLock(), _refresh=lambda _: (cycle, None),
        allocations={digest(caller.to_json()):approved}, budget_authority=budget,
        managed_work_route=lambda *a, **kw:selected, storage=tmp_path,
        host_admission={"definition":{"managed_routing":{}}},
        budget_quotes={("nous",model,"chat_completions",endpoint):quote})
    response_dir = tmp_path / "model-transport"
    response_dir.mkdir(mode=0o700)
    operations = []
    def effect(action, payload):
        return model_effect(factory, caller, cycle.plan.grant_sha256, action, payload)
    for index in range(3):
        request = dict(route, request_id="request-"+str(index), request_sha256=digest(index),
                       request_bytes=72, output_tokens=8)
        op = effect("start",request)["operation_id"]
        operations.append(op)
        if index == 2:
            break
        link = dict(operation_id=op, identity=caller.to_json(), grant_sha256=cycle.plan.grant_sha256,
                    plan_sha256=cycle.plan.hash, allocation_id=approved.allocation_id)
        answer = {"kind":"http_response", "http_status":200, "body":{"model":model, "usage":{
            "prompt_tokens":4, "completion_tokens":3, "total_tokens":7,
            "prompt_tokens_details":{"cached_tokens":1}, "cache_write_tokens":0}}}
        meter = transport._managed_usage(answer, link, model, 1, 5, offline=True)
        assert meter["observation"]["actual_cost_microusd"] is None
        transport._write_once(response_dir / (op+".response.json"), {"binding":link,"result":answer,"metering":meter})
        assert effect("returned", {"operation_id":op}) == {"settled":True,"unknown_measurements":[]}
        assert budget.reconcile(op)["usage"]["tokens"] == 7
    assert len(set(operations)) == 3
    with pytest.raises(FileNotFoundError):
        effect("returned", {"operation_id":operations[-1]})
    # Delivered HTTPS data can confirm tokens while the actual charge remains unknown.
    link = dict(link, operation_id=operations[-1])
    meter = transport._managed_usage(answer, link, model, 1, 5, offline=False)
    transport._write_once(response_dir / (operations[-1]+".response.json"),
        {"binding":link,"result":answer,"metering":meter})
    assert effect("returned", {"operation_id":operations[-1]}) == {
        "settled":False,"unknown_measurements":["cost_microusd"]}
    with pytest.raises(WorkContractError, match="uncertain model effect"):
        effect("start", dict(request, request_id="no-redispatch"))
    assert budget.reconcile(operations[-1])["usage"] is None
