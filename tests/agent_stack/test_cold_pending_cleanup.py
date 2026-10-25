from pathlib import Path
from importlib.machinery import SourceFileLoader
import importlib.util,json,signal
from types import SimpleNamespace
import pytest
REPO=Path(__file__).resolve().parents[2]
def load(name,file):
 loader=SourceFileLoader(name,str(REPO/'agent-stack/bin'/file));spec=importlib.util.spec_from_loader(name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m);return m
worker=load('cold_pending_worker','agent-task-worker');recovery=load('cold_pending_recovery','agent-stack-recovery')
@pytest.fixture(autouse=True)
def bounded_case():
 old=signal.getsignal(signal.SIGALRM)
 def timeout(*args):raise TimeoutError('bounded cold-cleanup component deadline')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(5)
 try:yield
 finally:signal.alarm(0);signal.signal(signal.SIGALRM,old)

def configure(tmp,monkeypatch):
 from herdr.evidence import EvidenceUnavailable
 import socket,subprocess
 monkeypatch.setattr(socket.socket,'connect',lambda *a,**kw:pytest.fail('no network'))
 monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('no process'))
 for m in (worker,recovery):
  m.ROOT=tmp
  for key in ('RUNNING','DONE','BLOCKED','FAILED','RESULTS'):
   setattr(m,key,tmp/key.lower());getattr(m,key).mkdir(exist_ok=True)
 worker.PENDING=tmp/'pending';worker.PENDING.mkdir();worker.LOGS=tmp/'logs';worker.LOGS.mkdir()
 task={'id':'synthetic-crash-root','repo':'Bbambaaamm/herdr','issue':0,'work_contract_version':1}
 worker.prepare_attempt(task);task['execution_session']={'owned_pane':True,'pane_id':'synthetic'}
 path=worker.RUNNING/(task['id']+'.json');worker.write_json(path,task)
 payload={'task_id':task['id'],'run_token':task['run_token'],'status':'completed','summary':'synthetic local artifact','next_action':'await external review','repo':task['repo'],'blocker':None,'evidence':[{'producer':'synthetic-artifact','passed':True}]}
 worker.write_json(worker.result_path(task['id']),payload)
 def pending(*a,**kw):raise EvidenceUnavailable('synthetic external review unavailable')
 monkeypatch.setattr(worker,'_verify_root_completion',pending)
 calls=[];monkeypatch.setattr(worker,'cleanup_task_session',lambda task:calls.append(task['attempt_state']) or True)
 # Crash after the real pending write, before the finish wrapper can close.
 worker._finish_locked(path,task,'',True)
 path=worker.BLOCKED/path.name;task=json.loads(path.read_bytes());task.pop('not_before',None);worker.write_json(path,task)
 assert task['attempt_state']=='verification_pending' and calls==[]
 monkeypatch.setattr(recovery,'_worker_bridge',lambda:worker)
 monkeypatch.setattr(recovery,'active_worker_tasks',lambda:set())
 monkeypatch.setattr(recovery,'cleanup_task_owned_pane',lambda task:pytest.fail('must use original worker cleanup, not legacy pane-only path'))
 monkeypatch.setattr(worker,'prepare_attempt',lambda *a,**kw:pytest.fail('no new attempt'))
 monkeypatch.setattr(worker,'create_task_session',lambda *a,**kw:pytest.fail('no new SDK'))
 monkeypatch.setattr(worker,'run_prompt',lambda *a,**kw:pytest.fail('no redispatch'))
 return task,path,payload,calls

def test_cold_worker_pending_same_attempt_runs_original_cleanup(tmp_path,monkeypatch):
 task,path,payload,calls=configure(tmp_path,monkeypatch);binding={k:task[k] for k in ('id','run_token','idempotency_key','attempt_id','fencing_token')};before=worker.result_path(task['id']).read_bytes()
 assert worker._main_with_epoch(path)==0
 saved=json.loads(path.read_bytes())
 assert {k:saved[k] for k in binding}==binding and worker.result_path(task['id']).read_bytes()==before
 assert calls==['verification_pending']

def test_watchdog_reconcile_pending_same_attempt_runs_original_cleanup(tmp_path,monkeypatch):
 task,path,payload,calls=configure(tmp_path,monkeypatch);before=worker.result_path(task['id']).read_bytes();token=task['run_token']
 recovery.reconcile_verification_pending()
 saved=json.loads(path.read_bytes());assert saved['run_token']==token and saved['attempt_state']=='verification_pending'
 assert worker.result_path(task['id']).read_bytes()==before
 assert calls==['verification_pending']

@pytest.mark.parametrize('guard',['delivery_uncertain','active_children'])
def test_existing_ambiguous_or_active_child_guard_preserves_session(tmp_path,monkeypatch,guard):
 task,path,payload,calls=configure(tmp_path,monkeypatch)
 if guard=='delivery_uncertain':task['attempt_state']='delivery_uncertain'
 else:task['watchdog_blocker']='active_durable_children'
 assert worker.cleanup_task_session_if_safe(task) is True and calls==[]

def test_existing_recovery_active_child_transition_never_closes_or_reexecutes(tmp_path,monkeypatch):
 task,path,payload,calls=configure(tmp_path,monkeypatch);token=task['run_token']
 monkeypatch.setattr(recovery,'_worker_bridge',lambda:pytest.fail('no parent verification/close before children terminal'))
 recovery._terminalize_from_result_locked(path,task,payload,0,False)
 saved=json.loads(path.read_bytes());assert saved['run_token']==token and saved['watchdog_blocker']=='active_durable_children'
 assert saved['attempt_state']=='result_ready' and calls==[]


def test_legacy_pending_worker_path_keeps_existing_behavior(tmp_path,monkeypatch):
 task,path,payload,calls=configure(tmp_path,monkeypatch);task.pop('work_contract_version');worker.write_json(path,task)
 assert worker._main_with_epoch(path)==0 and calls==[]
 assert json.loads(path.read_bytes())['attempt_state']=='verification_pending'

def test_legacy_pending_watchdog_path_keeps_existing_behavior(tmp_path,monkeypatch):
 from herdr.evidence import EvidenceUnavailable
 task,path,payload,calls=configure(tmp_path,monkeypatch);task.pop('work_contract_version');worker.write_json(path,task)
 def waiting(*a,**kw):raise EvidenceUnavailable('synthetic legacy external evidence pending')
 monkeypatch.setattr(recovery,'verify_completion',waiting)
 recovery.reconcile_verification_pending()
 assert calls==[] and json.loads(path.read_bytes())['attempt_state']=='verification_pending'


def test_authoritative_active_child_guard_without_old_blocker_never_closes(tmp_path,monkeypatch):
 from contextlib import contextmanager
 task,path,payload,calls=configure(tmp_path,monkeypatch)
 assert task.get('watchdog_blocker')!='active_durable_children'
 @contextmanager
 def active(task):yield False
 monkeypatch.setattr(worker,'parent_transition_guard',active)
 worker.finish(path,task,'')
 saved=json.loads(path.read_bytes())
 assert saved['watchdog_blocker']=='active_durable_children' and saved['attempt_state']=='result_ready'
 assert calls==[] and worker.result_path(task['id']).exists()

@pytest.mark.parametrize('lane',['cold-worker','watchdog'])
def test_cleanup_failure_retains_exact_result_and_same_attempt(tmp_path,monkeypatch,lane):
 task,path,payload,calls=configure(tmp_path,monkeypatch);before=worker.result_path(task['id']).read_bytes();token=task['run_token']
 monkeypatch.setattr(worker,'cleanup_task_session',lambda task:False)
 if lane=='cold-worker':assert worker._main_with_epoch(path)==0
 else:recovery.reconcile_verification_pending()
 saved=json.loads(path.read_bytes())
 assert saved['run_token']==token and saved['watchdog_blocker']=='task_session_cleanup_failed'
 assert saved['verification_status']=='evidence_unavailable' and worker.result_path(task['id']).read_bytes()==before
 assert not saved['execution_session'].get('closed_at')


def original_child_modules():
 import agent_durable_children
 directory=Path(agent_durable_children.__file__).resolve().parent
 def source(name,file):
  loader=SourceFileLoader(name,str(directory/file));spec=importlib.util.spec_from_loader(name,loader);module=importlib.util.module_from_spec(spec);loader.exec_module(module);return module
 return source('cold_bridge_source','agent-durable-bridge'),source('cold_child_source','agent-durable-child')

def test_actual_bridge_selects_blocked_canonical_task_and_parent_context_denies_before_native(tmp_path,monkeypatch):
 task,path,payload,calls=configure(tmp_path,monkeypatch);bridge,child=original_child_modules()
 assert bridge._current_task_file(tmp_path,task['id'],task['run_token'])==path.resolve()
 task['execution_session'].update(agent_name='synthetic-agent',pane_marker='synthetic-marker',session_name='synthetic-marker')
 worker.write_json(path,task)
 for key,value in {'HERDR_DURABLE_TASK_ID':task['id'],'HERDR_DURABLE_RUN_TOKEN':task['run_token'],'HERDR_DURABLE_TASK_FILE':str(path),'HERDR_DURABLE_AGENT':'synthetic-agent','HERDR_DURABLE_MARKER':'synthetic-marker','HERDR_DURABLE_TASK_PANE':'synthetic-marker','HERDR_PANE_ID':'synthetic'}.items():monkeypatch.setenv(key,value)
 runner=SimpleNamespace(run=lambda *a,**kw:pytest.fail('pending parent must deny before native call'))
 with pytest.raises(ValueError,match='parent task attempt/session mismatch'):child._parent_context(runner)

def test_actual_locked_delegation_rechecks_pending_canonical_state_before_scheduler_or_delivery(tmp_path,monkeypatch):
 task,path,payload,calls=configure(tmp_path,monkeypatch);bridge,child=original_child_modules()
 stale=dict(task,attempt_state='accepted')
 monkeypatch.setenv('HERDR_DURABLE_TASK_FILE',str(path))
 args=SimpleNamespace(key='fresh-child',objective='synthetic read',prompt='read synthetic',ownership=None,role='reader',tool=['read_file'],permission=[])
 runner=SimpleNamespace(run=lambda *a,**kw:pytest.fail('no native child delivery'))
 with pytest.raises(ValueError,match='parent attempt changed during delegation'):
  child._delegate_pinned(args,runner,'/synthetic/not-executed',stale,'pane','agent','marker',SimpleNamespace(logical=tmp_path/'work'))
 assert not list(tmp_path.rglob('scheduler.jsonl'))
 assert calls==[]
