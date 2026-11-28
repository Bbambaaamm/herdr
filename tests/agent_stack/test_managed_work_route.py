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
from tests.herdr.test_scheduler_routing import ALLOCATION, route_kwargs, task_node


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
    factory = SimpleNamespace(task_store_root=tmp_path, host_admission={"definition":definition},
        host_configuration_path=tmp_path / "policy", budget_authority=args["budget_gate"],
        allocations={digest(identity.to_json()):SimpleNamespace(allocation_id=ALLOCATION)},
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

