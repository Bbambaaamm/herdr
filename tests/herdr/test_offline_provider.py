import importlib.util
import json
from pathlib import Path
import pytest


def load(name):
    p=Path(__file__).resolve().parents[1]/'physical'/name
    spec=importlib.util.spec_from_file_location('physical_fixture',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture():
    m=load('offline_provider.py');f=object.__new__(m.ProviderFixture)
    f.edits={'agent_platform_dashboard/production_contract.py':'fixture-only'}
    f.scope_claim=None;f.turn=0;f.complete=False
    return m,f


def payload():
    return {'model':'meituan/longcat-2.0:free','tools':[{'type':'function','function':{'name':name}} for name in ('read_file','write_file','herdr_verify_work','herdr_submit_result')],'messages':[]}


def calls(answer):
    return answer['choices'][0]['message'].get('tool_calls',[])


def test_fixture_only_responds_through_disclosed_sdk_tools_and_exact_host_submission():
    m,f=fixture();p=payload()
    reads=calls(f.answer(p));assert len(reads)==len(m.FILES)
    assert all(c['function']['name']=='read_file' for c in reads)
    assert calls(f.answer(p))[0]['function']['name']=='write_file'
    verify=calls(f.answer(p))[0]
    assert verify['function']['name']=='herdr_verify_work'
    assert json.loads(verify['function']['arguments'])['handoff']=={'pr_number':None}
    submission={'status':'completed','evidence':[{'fixture':'host-generated'}],'summary':'local fixture'}
    p['messages']=[{'role':'tool','content':json.dumps({'result':{'status':'pass','submission':submission}})}]
    result=calls(f.answer(p))[0]
    assert result['function']['name']=='herdr_submit_result'
    assert json.loads(result['function']['arguments'])==submission
    assert not calls(f.answer(p)) and f.complete


def test_failed_or_absent_actual_verification_cannot_be_faked_as_accepted():
    _,f=fixture();f.turn=3
    p=payload();p['messages']=[{'role':'tool','content':json.dumps({'status':'failed'})}]
    with pytest.raises(ValueError,match='did_not_pass'):f.answer(p)


def test_fixture_never_adds_missing_tools_or_unbounded_turns():
    _,f=fixture();p=payload();p['tools']=[]
    with pytest.raises(ValueError,match='tools_missing'):f.answer(p)
    f.turn=8
    with pytest.raises(ValueError,match='turn_limit'):f.answer(payload())


def test_fixture_custody_rejects_symlink_without_chowning_target(tmp_path,monkeypatch):
    m=load('offline_pilot.py');root=tmp_path/'root';root.mkdir();target=tmp_path/'outside';target.write_text('keep');(root/'alias').symlink_to(target)
    changed=[];monkeypatch.setattr(m.os,'chown',lambda path,*args:changed.append(Path(path)))
    with pytest.raises(RuntimeError,match='unexpected_link'):m.user_tree(root)
    assert target not in changed and target.read_text()=='keep'


def test_native_snapshot_read_does_not_reject_or_change_old_access_time(tmp_path):
    import os
    m=load('offline_pilot.py');source=tmp_path/'binary';source.write_bytes(b'fixture-native-source')
    old=1_000_000_000;os.utime(source,ns=(old,source.stat().st_mtime_ns))
    assert m.read_native_snapshot(source,owner=os.geteuid())==b'fixture-native-source'
    assert source.stat().st_atime_ns==old


def test_native_snapshot_still_rejects_a_content_version_change(tmp_path,monkeypatch):
    import os
    m=load('offline_pilot.py');source=tmp_path/'binary';source.write_bytes(b'fixture-native-source')
    original=m.os.read;changed=False
    def read(fd,size):
        nonlocal changed
        data=original(fd,size)
        if not changed:
            changed=True;stamp=source.stat();os.utime(source,ns=(stamp.st_atime_ns,stamp.st_mtime_ns+1))
        return data
    monkeypatch.setattr(m.os,'read',read)
    with pytest.raises(RuntimeError,match='snapshot_changed'):m.read_native_snapshot(source,owner=os.geteuid())


def test_frozen_browser_environment_is_config_not_a_credential():
    m=load('offline_pilot.py')
    value=b'# nonsecret profile setting\nAGENT_BROWSER_EXECUTABLE_PATH=/home/agentops/.local/bin/chromium-with-playwright-libs\n'
    assert m.safe_profile_environment(value)==value.split(b'\n',1)[1]
    for invalid in (b'NOUS_API_KEY=private\n',b'LD_PRELOAD=/tmp/injection\n',b'AGENT_BROWSER_EXECUTABLE_PATH=$(unsafe)\n',value+value):
        with pytest.raises(RuntimeError,match='environment_.*denied'):m.safe_profile_environment(invalid)


def test_retained_preparation_never_replaces_changed_or_foreign_file(tmp_path):
    import os
    m=load('reconcile_offline_preparation.py');p=tmp_path/'retained';p.write_bytes(b'keep');p.chmod(0o600)
    m.exact_file(p,b'keep',owner=os.geteuid())
    with pytest.raises(RuntimeError,match='retained_preparation_file_changed'):m.exact_file(p,b'new',owner=os.geteuid())
    p.chmod(0o644)
    with pytest.raises(RuntimeError,match='retained_preparation_file_changed'):m.exact_file(p,b'keep',owner=os.geteuid())
    assert p.read_bytes()==b'keep'


def test_retained_preparation_does_not_follow_a_file_alias(tmp_path):
    import os
    m=load('reconcile_offline_preparation.py');target=tmp_path/'target';target.write_bytes(b'keep');alias=tmp_path/'alias';alias.symlink_to(target)
    with pytest.raises(RuntimeError,match='retained_preparation_file_changed'):m.exact_file(alias,b'keep',owner=os.geteuid())
    assert target.read_bytes()==b'keep'


def test_profile_inventory_uses_approved_manifest_including_sdk_policy(tmp_path):
    import hashlib
    m=load('offline_pilot.py');names=['profile.yaml','config.yaml','SOUL.md','herdr-sdk-policy.json']
    expected={}
    for name in names:
        (tmp_path/name).write_bytes(b'approved fixture');expected[name]=hashlib.sha256(b'approved fixture').hexdigest()
    assert {p.name for p in m.frozen_profile_members(tmp_path,expected)}==set(names)
    (tmp_path/'SOUL.md').write_bytes(b'changed')
    with pytest.raises(RuntimeError,match='profile_source_changed'):m.frozen_profile_members(tmp_path,expected)
    (tmp_path/'unexpected').write_bytes(b'new')
    with pytest.raises(RuntimeError,match='profile_inventory_changed'):m.frozen_profile_members(tmp_path,expected)


def test_late_fixture_clock_binding_only_accepts_unsigned_fixture_credentials():
    import base64,time
    m=load('reconcile_offline_preparation.py')
    encode=lambda v:base64.urlsafe_b64encode(json.dumps(v).encode()).decode().rstrip('=')
    token=encode({'alg':'HS256','typ':'JWT'})+'.'+encode({'sub':'a-real-account','scope':'invoke','exp':1})+'.Zml4dHVyZQ'
    with pytest.raises(RuntimeError,match='synthetic_fixture_credential_required'):
        m.synthetic_credential_after_delay({'providers':{'nous':{'agent_key':token}}},time.time())


def test_late_fixture_clock_starts_at_readiness_and_keeps_original_untouched():
    import base64
    m=load('reconcile_offline_preparation.py');encode=lambda v:base64.urlsafe_b64encode(json.dumps(v).encode()).decode().rstrip('=')
    old=encode({'alg':'HS256','typ':'JWT'})+'.'+encode({'sub':'herdr-offline-fixture','scope':'invoke','exp':1})+'.Zml4dHVyZQ'
    original={'providers':{'nous':{'agent_key':old}}}
    entry,key,expiry=m.synthetic_credential_after_delay(original,1_000_000)
    assert expiry==1_007_200 and entry['agent_key']==entry['access_token']==key and key!=old
    assert original['providers']['nous']['agent_key']==old and all('refresh' not in k.lower() for k in entry)
    claims=json.loads(base64.urlsafe_b64decode(key.split('.')[1]+'=='))
    assert claims=={'sub':'herdr-offline-fixture','scope':'invoke','exp':expiry}


@pytest.fixture
def offline_handoff_observer(tmp_path):
    """Execute the real physical observer loop with private files and a clock."""
    import ast
    from types import SimpleNamespace
    from herdr import operation_readiness as readiness
    from herdr.evidence import binding
    source=Path(__file__).resolve().parents[1]/'physical/offline_pilot.py'
    tree=ast.parse(source.read_text())
    inner=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inner')
    loop=next(n for n in ast.walk(inner) if isinstance(n,ast.While))
    need=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='need')
    queue=tmp_path/'queue';task_id='observer-original'
    for state in ('pending','running','blocked','failed','done','results'):
        (queue/state).mkdir(parents=True)
    clock=SimpleNamespace(now=0,sleeps=0)
    task={'id':task_id,'run_token':'same-run','idempotency_key':'same-key',
          'attempt_id':0,'fencing_token':8,'attempt_state':'verification_pending','execution_session':{}}
    expected=binding(task)

    def invoke(directory='blocked',closed=True,release=False,result=b'{}',other=None,move=False):
        if closed:task['execution_session']['closed_at']='fixture-closed'
        path=queue/directory/(task_id+'.json')
        path.write_text(json.dumps(task))
        if other:(queue/other/path.name).write_text(json.dumps(task))
        result_path=queue/'results'/path.name
        if result is not None:result_path.write_bytes(result)
        def sleep(seconds):
            clock.now+=1;clock.sleeps+=1
            assert clock.sleeps<=3,'observer reset its original deadline'
            if release:
                task['execution_session']['closed_at']='fixture-closed'
                path.write_text(json.dumps(task));result_path.write_text('{}')
            if move and directory=='pending' and path.exists():
                path.rename(queue/'blocked'/path.name)
        ns={'Path':lambda value:queue,'TASK':task_id,'json':json,
            'process':SimpleNamespace(poll=lambda:None),
            'time':SimpleNamespace(monotonic=lambda:clock.now,sleep=sleep),
            'deadline':3,'passed':False,'root':tmp_path,
            'readiness':SimpleNamespace(observe_task=readiness.observe_task,
                SnapshotChanged=readiness.SnapshotChanged,
                read_host_task_identity=lambda p:expected)}
        exec(compile(ast.Module(body=[need,loop],type_ignores=[]),str(source),'exec'),ns)
        return ns['passed']
    return SimpleNamespace(invoke=invoke,task=task,clock=clock,queue=queue)


@pytest.mark.parametrize('directory',['running','blocked'])
@pytest.mark.parametrize('closed,release',[(True,False),(False,True)])
def test_offline_observer_accepts_same_closed_handoff(
        offline_handoff_observer,directory,closed,release):
    f=offline_handoff_observer
    assert f.invoke(directory=directory,closed=closed,release=release)
    assert f.clock.sleeps==(0 if closed else 1)


@pytest.mark.parametrize('state',[
    'terminal_unknown','delivery_uncertain','failed','blocked','working'])
def test_offline_observer_rejects_other_blockers(offline_handoff_observer,state):
    f=offline_handoff_observer;f.task['attempt_state']=state
    with pytest.raises(RuntimeError,match='ordinary_fixture_worker_stopped'):
        f.invoke()
    assert f.clock.sleeps==0


@pytest.mark.parametrize('result',[b'',None])
def test_offline_observer_waits_for_nonempty_result(offline_handoff_observer,result):
    f=offline_handoff_observer
    assert f.invoke(result=result,release=True) and f.clock.sleeps==1


def test_offline_observer_cleanup_wait_keeps_deadline(offline_handoff_observer):
    f=offline_handoff_observer
    assert not f.invoke(closed=False) and f.clock.sleeps==3


@pytest.mark.parametrize('other',['running','pending','done','failed'])
def test_offline_observer_rejects_duplicate_canonical_task(offline_handoff_observer,other):
    f=offline_handoff_observer
    with pytest.raises(RuntimeError,match='canonical task count'):
        f.invoke(other=other)


def test_offline_observer_does_not_accept_failed_verification_task(offline_handoff_observer):
    f=offline_handoff_observer
    with pytest.raises(RuntimeError,match='ordinary_fixture_worker_stopped'):
        f.invoke(directory='failed')


def test_offline_observer_does_not_accept_unexpected_done_task(offline_handoff_observer):
    f=offline_handoff_observer
    assert not f.invoke(directory='done') and f.clock.sleeps==3


def test_offline_observer_tracks_pending_to_blocked_handoff(offline_handoff_observer):
    f=offline_handoff_observer
    assert f.invoke(directory='pending',move=True) and f.clock.sleeps==1


@pytest.mark.parametrize('source,target',[('running','blocked'),('pending','running')])
def test_offline_observer_uses_same_atomic_transition_contract(offline_handoff_observer,monkeypatch,source,target):
    import os
    f=offline_handoff_observer;name=f.task['id']+'.json';moved=[];stat=os.stat
    def moving(path,*args,**kwargs):
        directory=Path(os.readlink('/proc/self/fd/'+str(kwargs['dir_fd']))) if 'dir_fd' in kwargs else Path(path).parent
        try:return stat(path,*args,**kwargs)
        finally:
            if str(path)==name and directory.name=='running' and not moved:
                (f.queue/source/name).rename(f.queue/target/name);moved.append(True)
    monkeypatch.setattr(os,'stat',moving)
    assert f.invoke(directory=source) and moved==[True] and f.clock.sleeps==0


@pytest.mark.parametrize('field,value',[('run_token','other'),('fencing_token',9),('attempt_id',1)])
def test_offline_observer_does_not_adopt_mutable_identity(offline_handoff_observer,field,value):
    f=offline_handoff_observer;f.task[field]=value
    with pytest.raises(RuntimeError,match='identity_changed'):f.invoke()
