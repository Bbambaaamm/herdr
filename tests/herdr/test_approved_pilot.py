from pathlib import Path
import importlib.util,json,copy,pytest
ROOT=Path(__file__).resolve().parents[2]/'deploy/herdr'
def load():
 spec=importlib.util.spec_from_file_location('continuation_under_test',ROOT/'approved_pilot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.TASK='issue77-validation-repair-20261026';m.MODEL='meituan/longcat-2.0:free';return m
def task():
 return {'id':'issue77-validation-repair-20261026','model':'meituan/longcat-2.0:free','fencing_token':8,'run_token':'retained-token','attempt_started_at':'old','dispatch_claimed_at':'old','attempts':0,'attempt_id':0,'idempotency_key':'retained','tools':['read_file','write_file','patch','herdr_verify_work','herdr_submit_result'],'budget':{'model_calls':62,'cost':0},'payload':{'unchanged':True}}
def test_new_clock_preserves_complete_task_and_source_object():
 m=load();before=task();saved=copy.deepcopy(before);now='2026-10-28T01:00:00+00:00';after=m.renewed_pending_task(before,copy.deepcopy(before),now)
 assert before==saved
 assert {k:v for k,v in after.items() if k not in {'attempt_started_at','dispatch_claimed_at'}}=={k:v for k,v in saved.items() if k not in {'attempt_started_at','dispatch_claimed_at'}}
 assert after['attempt_started_at']==after['dispatch_claimed_at']==now
 after['payload']['unchanged']=False;assert before['payload']['unchanged'] is True
@pytest.mark.parametrize('field,value',[('model','another-model'),('run_token','new-token'),('fencing_token',9),('attempts',1),('budget',{'model_calls':63,'cost':0})])
def test_changed_pending_task_is_never_reconciled_as_only_a_clock(field,value):
 m=load();seed=task();pending=copy.deepcopy(seed);pending[field]=value
 with pytest.raises(AssertionError):m.renewed_pending_task(seed,pending,'2026-10-28T01:00:00+00:00')
@pytest.mark.parametrize('field,value',[('id','another-task'),('model','another-model'),('fencing_token',9)])
def test_unreviewed_identity_is_denied_even_when_both_files_match(field,value):
 m=load();seed=task();seed[field]=value
 with pytest.raises(AssertionError):m.renewed_pending_task(seed,copy.deepcopy(seed),'2026-10-28T01:00:00+00:00')
def test_naive_start_clock_is_rejected():
 m=load();seed=task()
 with pytest.raises(AssertionError):m.renewed_pending_task(seed,seed,'2026-10-28T01:00:00')
@pytest.mark.parametrize('window,remaining,allowed',[(540000,540000,True),(7200,7200,False),(540000,1200,False),(540000,1201,True)])
def test_only_approved_150_hour_gate_with_cleanup_time_is_accepted(tmp_path,monkeypatch,window,remaining,allowed):
 m=load();gate=tmp_path/'gate';start=1793140000;end=start+window;gate.write_text('FROM = '+str(start)+'\nUNTIL = '+str(end)+'\n')
 (tmp_path/'approved38-human-approval.json').write_text(json.dumps({'root_until_epoch':end}));m.R=tmp_path;real=Path
 monkeypatch.setattr(m,'Path',lambda p:gate if str(p)=='/usr/local/sbin/herdr-admin48' else real(p));monkeypatch.setattr(m.time,'time',lambda:end-remaining)
 if allowed:assert m.admin_deadline()==end
 else:
  with pytest.raises(AssertionError):m.admin_deadline()
@pytest.mark.parametrize('blocker',['ledger','start-intent'])
def test_clock_never_changes_after_economic_admission_or_start_intent(tmp_path,blocker):
 m=load();m.R=tmp_path;m.STORE=tmp_path/'store'
 if blocker=='ledger':
  file=m.STORE/'work-budget/retained/events.jsonl';file.parent.mkdir(parents=True);file.write_text('retained')
 else:(tmp_path/'approved38-unit-start-intent.json').write_text('{}')
 with pytest.raises(AssertionError):m.refresh_pending_start_clock()
 assert not (tmp_path/'approved38-before-admission-clock.json').exists()


def test_auth_child_uses_versioned_snapshot_with_derived_lifetime(tmp_path,monkeypatch):
    from types import SimpleNamespace
    m=load();m.R=tmp_path;m.P='/pinned/python';m.REQUIRED_CREDENTIAL_SECONDS=3330
    calls=[]
    def run(command,**kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=1,stdout='',stderr='')
    monkeypatch.setattr(m.subprocess,'run',run)
    monkeypatch.setattr(m,'save',lambda *args,**kwargs:None)
    with pytest.raises(AssertionError,match='authentication unavailable'):m.prepare_auth()
    assert len(calls)==1
    child=calls[0]
    assert child[3]==str(ROOT/'existing_credential_snapshot.py')
    assert child[-2:]==['--required-validity-seconds','3330']
    assert 'approved38-existing-credential-snapshot.py' not in child[3]
    assert not (tmp_path/'approved38-unit-start-intent.json').exists()
