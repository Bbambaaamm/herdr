"""Actual disposable DCS journal round-trips; no native, completion or model calls."""
import copy
import json

import pytest

from herdr.scheduler import AuditLog, ChildProposal, DenyDecision, DynamicChildScheduler, SchedulerBudget, SchedulerError
from herdr.taskgraph import TaskGraph


def graph():
    return TaskGraph.parse_planner_output({
        'envelope':{'issue':'Bbambaaamm/herdr#129','spec_hash':'sha256:'+'a'*64,
            'graph_version':'1.1.0','created_at':'2026-10-21T00:00:00+00:00','planner':'roundtrip-test',
            'max_nodes':2,'max_depth':2,'max_fanout':1,'policy_profile':'quantlab-paper'},
        'nodes':[{'id':'root','parent_id':None,'type':'task','role':'reader',
            'objective':'Keep the admitted semantic node exactly',
            'inputs':[{'artifact_ref':'fixture','metadata':{'public':[1,None,True]}}],
            'expected_outputs':[{'kind':'evidence','shape':{'nested':['exact']}}],
            'dependencies':[],'priority':7,'resource_class':'small',
            'model_policy':{'model':'external','fallback_model':None,'provider':'none','limits':{'calls':0}},
            'tools':['read_file','herdr_submit_result'],'permissions':['repo:read'],
            'timeout_seconds':137,'max_attempts':2}]})


def scheduler(path,*,maximum=8):
    # This suite never calls completion. Supplying an unused completion object
    # keeps the reduced public-source local cache independent of unrelated
    # artifact/GitHub collection imports; actual DCS and journal APIs are used.
    return DynamicChildScheduler(budget=SchedulerBudget(max_global_concurrency=2,max_per_repo=2,
        max_per_issue=2,max_dag_nodes=maximum,max_dag_depth=8,max_dag_fanout=8),
        audit_log=AuditLog(path),clock=lambda:1000.0,completion_authority=object())


def submit(path):
    live=scheduler(path);live.submit(graph(),repo='Bbambaaamm/herdr',issue='129')
    return live


def proposal():
    return ChildProposal('reader',('read_file','herdr_submit_result'),'reader',('read_file',),
        child_task='Keep inherited child semantics',child_model='external',child_fallback_model=None,
        parent_permissions=('repo:read',),child_permissions=('repo:read',))


def replay(live,*,maximum=8):
    live.audit_log.flush();cold=scheduler(live.audit_log._path,maximum=maximum);cold.replay();return cold


def rewrite(live,change):
    live.audit_log.flush();events=live.audit_log.replay();change(events)
    live.audit_log._path.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf-8')


def test_submit_dispatch_replay_preserves_complete_canonical_node_and_claim(tmp_path):
    live=submit(tmp_path/'scheduler.jsonl');live.dispatch(task_ids={'root'})
    before=live._tasks['root'];cold=replay(live);after=cold._tasks['root']
    assert after.node.to_json()==before.node.to_json()
    assert after.model_used==before.model_used and after.fallback_used is before.fallback_used is None
    assert all(getattr(after,key)==getattr(before,key) for key in
        ('run_token','idempotency_key','fencing_token','agent_id','lease','parent_task_id','parent_agent_id'))


def test_persisted_nested_semantics_are_detached_from_caller_and_export(tmp_path):
    admitted=graph();live=scheduler(tmp_path/'scheduler.jsonl')
    expected=copy.deepcopy(admitted.nodes[0].to_json());live.submit(admitted)
    exported=admitted.nodes[0].to_json();exported['inputs'][0]['metadata']['public'].append('changed')
    exported['model_policy']['limits']['calls']=999
    assert replay(live)._tasks['root'].node.to_json()==expected


def test_spawn_child_replay_preserves_inherited_semantics_and_disabled_fallback(tmp_path):
    live=submit(tmp_path/'scheduler.jsonl');child=live.spawn_child('root',proposal())
    assert not isinstance(child,DenyDecision)
    cold=replay(live);record=cold._tasks[child.id]
    assert record.node.to_json()==child.to_json()
    assert record.fallback_used is None and record.node.model_policy['fallback_model'] is None


def test_external_parent_replay_preserves_exact_semantic_node_without_graph_limits(tmp_path):
    live=scheduler(tmp_path/'scheduler.jsonl')
    parent=live.register_external_parent_attempt(task_id='external-root',run_token='run',idempotency_key='key',
        agent_name='external-agent',pane_id='pane',marker='marker',repo='Bbambaaamm/herdr',issue='129',
        role='reader',tools=('read_file',),permissions=('repo:read',),policy_profile='quantlab-paper')
    cold=replay(live)
    assert cold._tasks[parent.node.id].node.to_json()==parent.node.to_json()
    assert (cold._plan_max_nodes,cold._plan_max_depth,cold._plan_max_fanout)==(8,8,8)


@pytest.mark.parametrize('present,expected',[(False,'longcat'),(True,None)])
@pytest.mark.parametrize('event_type',['submit','spawn_child'])
def test_legacy_absent_fallback_default_is_distinct_from_explicit_null(tmp_path,present,expected,event_type):
    live=submit(tmp_path/'scheduler.jsonl')
    if event_type=='spawn_child':child=live.spawn_child('root',proposal())
    def legacy(events):
        for event in events:
            if event.get('event')==event_type:
                event.pop('model_policy',None)
                if present:event['fallback_model']=None
                else:event.pop('fallback_model',None)
    rewrite(live,legacy);cold=replay(live)
    task='root' if event_type=='submit' else child.id
    assert cold._tasks[task].node.model_policy['fallback_model']==expected
    if present:assert cold._tasks[task].fallback_used is None


@pytest.mark.parametrize('bad',[None,[],"not-a-policy"])
def test_present_malformed_complete_policy_never_falls_back_to_legacy(tmp_path,bad):
    live=submit(tmp_path/'scheduler.jsonl')
    rewrite(live,lambda events:events[0].update(model_policy=bad))
    with pytest.raises((SchedulerError,ValueError),match='policy'):replay(live)


@pytest.mark.parametrize('field,value',[('model','other-route'),('fallback_model','longcat')])
def test_complete_policy_cannot_disagree_with_record_route_projection(tmp_path,field,value):
    live=submit(tmp_path/'scheduler.jsonl')
    rewrite(live,lambda events:events[0].update({field:value}))
    with pytest.raises(SchedulerError,match='policy'):replay(live)


def test_replay_keeps_admitted_graph_limits_under_wider_constructor(tmp_path):
    live=submit(tmp_path/'scheduler.jsonl');cold=replay(live)
    assert (cold._plan_max_nodes,cold._plan_max_depth,cold._plan_max_fanout)==(2,2,1)
    first=cold.spawn_child('root',proposal());assert not isinstance(first,DenyDecision)
    assert isinstance(cold.spawn_child('root',proposal()),DenyDecision)


def test_replayed_graph_limits_cannot_widen_current_constructor_budget(tmp_path):
    live=submit(tmp_path/'scheduler.jsonl');cold=replay(live,maximum=1)
    assert cold._plan_max_nodes==1 and isinstance(cold.spawn_child('root',proposal()),DenyDecision)


def test_legacy_graph_limits_restore_existing_claims_but_deny_new_delegation(tmp_path):
    live=submit(tmp_path/'scheduler.jsonl');live.dispatch(task_ids={'root'})
    def legacy(events):
        for event in events:
            if event.get('event')=='graph_submit':
                for key in ('max_nodes','max_depth','max_fanout'):event.pop(key,None)
    rewrite(live,legacy);cold=replay(live)
    assert cold._tasks['root'].lease==live._tasks['root'].lease
    assert cold._tasks['root'].run_token==live._tasks['root'].run_token
    assert isinstance(cold.spawn_child('root',proposal()),DenyDecision)


def test_legacy_node_count_cannot_authorize_children_without_retained_submits(tmp_path):
    live=submit(tmp_path/'scheduler.jsonl')
    def corrupt(events):
        event=next(x for x in events if x.get('event')=='graph_submit')
        for key in ('max_nodes','max_depth','max_fanout'):event.pop(key,None)
        event['node_count']=999
    rewrite(live,corrupt)
    with pytest.raises(SchedulerError,match='legacy graph node limit'):replay(live)


@pytest.mark.parametrize('limits',[{'max_nodes':2},{'max_nodes':True,'max_depth':2,'max_fanout':1},
    {'max_nodes':2,'max_depth':0,'max_fanout':1},{'max_nodes':2,'max_depth':2,'max_fanout':'1'}])
def test_partial_or_malformed_new_graph_limits_fail_closed(tmp_path,limits):
    live=submit(tmp_path/'scheduler.jsonl')
    def corrupt(events):
        event=next(x for x in events if x.get('event')=='graph_submit')
        for key in ('max_nodes','max_depth','max_fanout'):event.pop(key,None)
        event.update(limits)
    rewrite(live,corrupt)
    with pytest.raises(SchedulerError,match='graph.*limit'):replay(live)
