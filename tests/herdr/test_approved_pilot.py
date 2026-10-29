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


@pytest.fixture
def fresh_queue_preparation(tmp_path, monkeypatch):
    """Synthetic owned files; real preparation/refresh and identity code."""
    import hashlib
    from herdr.evidence import binding

    m = load()
    m.R = tmp_path / "approved"
    m.H = tmp_path / "private-home"
    m.STORE = tmp_path / "not-admitted"
    m.R.mkdir()
    queue = m.H / ".local/state/agent-stack/tasks"
    queue.mkdir(parents=True)
    (queue / "retained.marker").write_bytes(b"original queue evidence")
    seed = task()
    seed_path = m.R / "resume-task-reviewed-approved38.json"
    prepared_path = m.R / "approved38-source-and-scripts-prepared.json"

    def seed_files(pretty=False):
        raw = json.dumps(seed, indent=2 if pretty else None).encode()
        seed_path.write_bytes(raw)
        prepared_path.write_text(json.dumps({
            "task_seed_sha256": hashlib.sha256(raw).hexdigest(),
            "source_commit": "retained-source",
            "previous_budget_sha256": "preserved-budget-hash",
            "files": {"kept.py": "unchanged-source-hash"},
        }))
        (m.R / "same-identity-approved38.json").write_text(
            json.dumps({"identity": binding(seed)}))
        return raw

    seed_files()
    # Ownership changes are outside this unprivileged unit fixture. The actual
    # atomic JSON writer, seed/queue logic and canonical identity remain in use.
    monkeypatch.setattr(m.os, "chown", lambda *args, **kwargs: None)
    return m, seed, seed_path, prepared_path, queue, seed_files


@pytest.mark.parametrize("pretty", [False, True])
def test_first_queue_preparation_then_clock_refresh_preserves_seed_hash(
        fresh_queue_preparation, pretty):
    import hashlib
    from herdr.evidence import binding

    m, original, seed, prepared, queue, seed_files = fresh_queue_preparation
    seed_files(pretty)
    assert m.prepare_queue() == queue
    pending = queue / "pending" / (m.TASK + ".json")
    assert seed.read_bytes() == pending.read_bytes()
    m.refresh_pending_start_clock()

    actual = seed.read_bytes()
    assert pending.read_bytes() == actual
    metadata = json.loads(prepared.read_bytes())
    assert metadata["task_seed_sha256"] == hashlib.sha256(actual).hexdigest()
    after = json.loads(actual)
    assert binding(after) == binding(original)
    clock_fields = {"attempt_started_at", "dispatch_claimed_at"}
    assert {k: v for k, v in after.items() if k not in clock_fields} == {
        k: v for k, v in original.items() if k not in clock_fields}
    assert metadata["source_commit"] == "retained-source"
    assert metadata["previous_budget_sha256"] == "preserved-budget-hash"
    assert metadata["files"] == {"kept.py": "unchanged-source-hash"}
    assert (m.R / "approved37-original-queue-preserved-before-approved38" /
            "retained.marker").read_bytes() == b"original queue evidence"
    before_reentry = (seed.read_bytes(), pending.read_bytes(),
                      prepared.read_bytes())
    assert m.prepare_queue() == queue
    assert before_reentry == (seed.read_bytes(), pending.read_bytes(),
                              prepared.read_bytes())
    assert not (m.R / "approved38-unit-start-intent.json").exists()
    assert not list(m.STORE.glob("work-budget/*/events.jsonl"))


def test_changed_seed_hash_denies_before_replacing_the_original_queue(
        fresh_queue_preparation):
    m, _, seed, prepared, queue, _ = fresh_queue_preparation
    value = json.loads(prepared.read_bytes())
    value["task_seed_sha256"] = "0" * 64
    prepared.write_text(json.dumps(value))
    original = seed.read_bytes()
    with pytest.raises(AssertionError):
        m.prepare_queue()
    assert seed.read_bytes() == original
    assert (queue / "retained.marker").read_bytes() == b"original queue evidence"
    assert not (m.R / "approved37-original-queue-preserved-before-approved38").exists()
    assert not (m.R / "approved38-queue-prepared.json").exists()


def test_prepared_metadata_write_failure_never_acknowledges_or_replays_queue(
        fresh_queue_preparation, monkeypatch):
    m, _, _, prepared, _, _ = fresh_queue_preparation
    save = m.save

    def fail_metadata(path, *args, **kwargs):
        if path == prepared:
            raise OSError("synthetic prepared metadata persistence failure")
        return save(path, *args, **kwargs)

    monkeypatch.setattr(m, "save", fail_metadata)
    with pytest.raises(OSError, match="metadata persistence"):
        m.prepare_queue()
    assert not (m.R / "approved38-queue-prepared.json").exists()
    with pytest.raises(AssertionError):
        m.prepare_queue()
    assert (m.R / "approved37-original-queue-preserved-before-approved38" /
            "retained.marker").read_bytes() == b"original queue evidence"
    assert not (m.R / "approved38-unit-start-intent.json").exists()
    assert not list(m.STORE.glob("work-budget/*/events.jsonl"))
