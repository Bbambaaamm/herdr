"""Same-key semantic model binding, using only disposable real scheduler journals.

No runtime/admission authority, native process, provider, model transport or
economic budget is constructed. Model strings are inert fixture identifiers.
"""
from dataclasses import replace

import pytest

from herdr.scheduler import AuditLog, ChildProposal, DynamicChildScheduler, SchedulerError


PARENT_RUN = "a" * 32
KEY = "normalization-implementation"


def scheduler(path):
    return DynamicChildScheduler(
        audit_log=AuditLog(path), clock=lambda: 1000.0,
        completion_authority=object())  # unused; no completion is invoked


def proposal(model="fixture-primary-a", fallback=None):
    return ChildProposal(
        parent_role="reader", parent_tools=("read_file",),
        child_role="reader", child_tools=("read_file",),
        child_task="Check the frozen normalization contract",
        child_model=model, child_fallback_model=fallback,
        parent_permissions=(), child_permissions=())


def admitted_parent(tmp_path):
    live = scheduler(tmp_path / "scheduler.jsonl")
    live.register_external_parent_attempt(
        task_id="root", run_token=PARENT_RUN, idempotency_key="b" * 64,
        agent_name="fixture-parent", pane_id="fixture-pane", marker="fixture-marker",
        repo="Bbambaaamm/herdr", issue="9", role="reader", tools=("read_file",),
        permissions=(), policy_profile="quantlab-paper")
    return live


def effect_snapshot(live):
    live.audit_log.flush()
    return (
        live.audit_log._path.read_bytes(),
        len(live._tasks), len(live._claims),
        live._next_fencing_token_value, live._next_agent_id_value,
        {key: rec.node.to_json() for key, rec in live._tasks.items()})


def child_with_optional_replay(tmp_path, original, replayed):
    live = admitted_parent(tmp_path)
    child = live.delegate_child("root", PARENT_RUN, KEY, original)
    if replayed:
        live.audit_log.flush()
        cold = scheduler(live.audit_log._path)
        cold.replay()
        live = cold
    return live, live.task_node(child.id)


@pytest.mark.parametrize("replayed", [False, True], ids=["live", "journal-replay"])
@pytest.mark.parametrize("fallback", [None, "fixture-fallback"], ids=["no-fallback", "fallback"])
def test_exact_same_key_model_policy_reuses_only_retained_node(tmp_path, replayed, fallback):
    original = proposal(fallback=fallback)
    live, child = child_with_optional_replay(tmp_path, original, replayed)
    before = effect_snapshot(live)
    got = live.delegate_child("root", PARENT_RUN, KEY, original)
    assert got is child
    assert got.model_policy["model"] == original.child_model
    assert got.model_policy["fallback_model"] == fallback
    if fallback is None:
        assert got.model_policy["fallback_model"] is None
        assert live._tasks[got.id].fallback_used is None
    assert effect_snapshot(live) == before


@pytest.mark.parametrize("replayed", [False, True], ids=["live", "journal-replay"])
@pytest.mark.parametrize("old_model,old_fallback,new_model,new_fallback", [
    ("fixture-primary-a", None, "fixture-primary-b", None),
    ("fixture-primary-a", None, "fixture-primary-a", "fixture-fallback"),
    ("fixture-primary-a", "fixture-fallback", "fixture-primary-a", None),
    ("fixture-primary-a", "fixture-fallback", "fixture-primary-a", "fixture-other-fallback"),
], ids=["model-drift", "enable-fallback", "disable-fallback", "fallback-drift"])
def test_changed_same_key_model_policy_fails_before_any_new_effect(
        tmp_path, replayed, old_model, old_fallback, new_model, new_fallback):
    original = proposal(old_model, old_fallback)
    live, child = child_with_optional_replay(tmp_path, original, replayed)
    before = effect_snapshot(live)
    with pytest.raises(SchedulerError, match="delegation key reused with different identity or work"):
        live.delegate_child("root", PARENT_RUN, KEY, proposal(new_model, new_fallback))
    assert live.task_node(child.id) is child
    assert effect_snapshot(live) == before


@pytest.mark.parametrize("field,value", [
    ("child_task", "different objective"), ("child_tools", ()),
    ("child_permissions", ("workspace-write",)),
])
def test_existing_same_key_intent_guards_are_preserved(tmp_path, field, value):
    original = proposal()
    live, _ = child_with_optional_replay(tmp_path, original, False)
    before = effect_snapshot(live)
    with pytest.raises(SchedulerError, match="delegation key reused with different identity or work"):
        live.delegate_child("root", PARENT_RUN, KEY, replace(original, **{field: value}))
    assert effect_snapshot(live) == before


def test_distinct_key_does_not_rewrite_previous_model_policy(tmp_path):
    live = admitted_parent(tmp_path)
    first = live.delegate_child("root", PARENT_RUN, KEY, proposal())
    # The existing consumer policy admits these inert fixture proposals. This
    # does not grant a model route; host model/economic admission is elsewhere.
    second = live.delegate_child("root", PARENT_RUN, "different-work", proposal("fixture-primary-b"))
    assert first.id != second.id
    assert first.model_policy == {"model": "fixture-primary-a", "fallback_model": None}
    assert second.model_policy == {"model": "fixture-primary-b", "fallback_model": None}
