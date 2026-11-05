"""Compatibility is decided from retained host state, never task-field absence alone."""
from copy import deepcopy
import pytest
from herdr.evidence import EvidenceError, EvidenceStore, binding, digest
from herdr.work_cycle import WorkContractError
from herdr.scheduler import CanonicalParentAdmission, DynamicChildScheduler, AuditLog
from herdr.taskgraph import TaskGraph, TaskGraphEnvelope, GRAPH_VERSION
from herdr.security import InvocationIdentity
from tests.agent_stack.test_active_durable_children import setup


def completion_module():
    import agent_completion_evidence
    return agent_completion_evidence


def reject_configuration(monkeypatch):
    import herdr.work_configuration as configuration
    calls = []
    def unavailable(*args, **kwargs):
        calls.append(True)
        raise WorkContractError('configuration unavailable')
    monkeypatch.setattr(configuration, '_read_configuration', unavailable)
    return calls


def test_genuine_retained_legacy_replay_needs_no_host_configuration(tmp_path, monkeypatch, setup):
    worker, recovery, task, path, scheduler, child, lease = setup
    parent = scheduler._tasks[task['id']]
    assert parent.canonical_parent is None
    calls = reject_configuration(monkeypatch)
    assert completion_module().child_completion_for_replay(tmp_path, scheduler) is None
    assert calls == []


@pytest.mark.parametrize('field', ['child_completion_contracts', 'work_contract_version', 'work_budget_version',
                                  'child_work_contract_version', 'child_work_budget_version'])
def test_present_null_modern_marker_cannot_select_legacy_port(tmp_path, monkeypatch, field, setup):
    worker, recovery, task, path, scheduler, child, lease = setup
    task[field] = None
    module = completion_module()
    monkeypatch.setattr('herdr.host_configuration.read_canonical_parent', lambda *args: task)
    calls = reject_configuration(monkeypatch)
    with pytest.raises((EvidenceError, WorkContractError)):
        module.child_completion_for_replay(tmp_path, scheduler)
    assert calls == [True]


@pytest.mark.parametrize('remove', [('work_contract_version',),
                                  ('child_completion_contracts',),
                                  ('work_contract_version', 'child_completion_contracts')])
def test_removed_modern_fields_do_not_match_original_frozen_spec(tmp_path, monkeypatch, remove, setup):
    worker, recovery, task, path, scheduler, child, lease = setup
    module = completion_module()
    original = dict(task, repo=scheduler._tasks[task['id']].repo, work_contract_version=1, child_completion_contracts={'version': 4})
    store = EvidenceStore(tmp_path / 'verification')
    store.publish('plan', digest(binding(task)),
                  {'identity': binding(task), 'spec_hash': module.spec_digest(original)})
    edited = deepcopy(original)
    for key in remove:
        del edited[key]
    monkeypatch.setattr('herdr.host_configuration.read_canonical_parent', lambda *args: edited)
    reject_configuration(monkeypatch)
    with pytest.raises((EvidenceError, WorkContractError)):
        module.child_completion_for_replay(tmp_path, scheduler)


def test_existing_frozen_child_policy_cannot_downgrade(tmp_path, monkeypatch, setup):
    worker, recovery, task, path, scheduler, child, lease = setup
    module = completion_module()
    parent = scheduler._tasks[task['id']]
    from herdr.child_completion_policy import policy_key
    EvidenceStore(tmp_path / 'verification').publish(
        'plan', policy_key(parent.repo, parent.id, parent.run_token), {'retained': True})
    calls = reject_configuration(monkeypatch)
    with pytest.raises(EvidenceError, match='cannot replay as legacy'):
        module.child_completion_for_replay(tmp_path, scheduler)
    assert calls == []


@pytest.mark.parametrize('missing_task', [False, True])
def test_actual_canonical_parent_binding_forbids_missing_markers_downgrade(tmp_path, monkeypatch, setup, missing_task):
    worker, recovery, task, path, legacy_scheduler, child, lease = setup
    legacy = legacy_scheduler._tasks[task['id']]
    task = deepcopy(task)
    identity = InvocationIdentity(consumer='github:' + legacy.repo,
        agent_id=legacy.execution_agent, parent_agent_id=legacy.execution_agent,
        parent_task_id=legacy.id, task_id=legacy.id, run_token=legacy.run_token,
        fencing_token=1)
    graph = TaskGraph(TaskGraphEnvelope(issue=legacy.repo + '#' + str(legacy.issue),
        spec_hash='a' * 64, graph_version=GRAPH_VERSION,
        created_at='2026-10-23T00:00:00Z', planner='fixture'), (legacy.node,))
    canonical = CanonicalParentAdmission(graph=graph, graph_sha256=graph.graph_hash(),
        identity=identity, idempotency_key=legacy.idempotency_key, repo=legacy.repo,
        issue=str(legacy.issue), pane_id=legacy.execution_pane, marker=legacy.execution_marker)
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / 'canonical-events.jsonl'))
    scheduler.submit(graph, repo=canonical.repo, issue=canonical.issue)
    node = graph.nodes[0]
    parent = scheduler.register_external_parent_attempt(task_id=identity.task_id,
        run_token=identity.run_token, idempotency_key=canonical.idempotency_key,
        agent_name=identity.agent_id, pane_id=canonical.pane_id, marker=canonical.marker,
        repo=canonical.repo, issue=canonical.issue, role=node.role, tools=node.tools,
        permissions=node.permissions, policy_profile=graph.envelope.policy_profile,
        canonical_parent=canonical)
    assert parent.canonical_parent is not None
    replayed = DynamicChildScheduler(audit_log=AuditLog(tmp_path / 'canonical-events.jsonl'))
    replayed.replay()
    assert replayed._tasks[identity.task_id].canonical_parent == parent.canonical_parent
    scheduler = replayed
    # The retained graph record still requires original admission even if every
    # mutable task marker has disappeared and no completion plan was published.
    for key in ('work_contract_version', 'work_budget_version', 'child_completion_contracts'):
        task.pop(key, None)
    monkeypatch.setattr('herdr.host_configuration.read_canonical_parent',
                        lambda *args: None if missing_task else task)
    calls = reject_configuration(monkeypatch)
    with pytest.raises((EvidenceError, WorkContractError)):
        completion_module().child_completion_for_replay(tmp_path, scheduler)
    assert calls == ([] if missing_task else [True])



def test_retained_legacy_without_canonical_parent_file_keeps_original_port(tmp_path, monkeypatch, setup):
    worker, recovery, task, path, scheduler, child, lease = setup
    monkeypatch.setattr('herdr.host_configuration.read_canonical_parent', lambda *args: None)
    calls = reject_configuration(monkeypatch)
    assert completion_module().child_completion_for_replay(tmp_path, scheduler) is None
    assert calls == []
