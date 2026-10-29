import copy
import os
import importlib.util
from pathlib import Path
import pytest
from herdr.operation_readiness import Lifetimes, ReadinessError, capacity, require_new_failure_evidence


@pytest.fixture
def canonical_queue(tmp_path):
    import json
    from herdr.evidence import binding
    from types import SimpleNamespace
    queue=tmp_path/'queue'
    for state in ('running','blocked','failed','done','pending'):(queue/state).mkdir(parents=True)
    task={'id':'original','run_token':'same-run','idempotency_key':'same-key',
          'attempt_id':0,'fencing_token':8,'attempt_state':'verification_pending'}
    path=queue/'running/original.json';path.write_text(json.dumps(task))
    return SimpleNamespace(queue=queue,path=path,task=task,expected=binding(task))


@pytest.mark.parametrize('moment',['enumeration','open','read','content-version'])
def test_task_observation_revalidates_only_changed_snapshot(canonical_queue,monkeypatch,moment):
    import json
    from herdr import operation_readiness as r
    f=canonical_queue;target=f.queue/'blocked'/f.path.name;events=[]
    stat,open_,read=os.stat,os.open,os.read
    def move():
        if not events:f.path.rename(target);events.append(True)
    def observe_stat(path,*args,**kwargs):
        result=stat(path,*args,**kwargs)
        if moment=='enumeration' and str(path)==f.path.name:move()
        return result
    def observe_open(path,*args,**kwargs):
        if moment=='open' and str(path)==f.path.name:move()
        return open_(path,*args,**kwargs)
    def observe_read(fd,size):
        result=read(fd,size)
        if not events and moment in ('read','content-version'):
            if moment=='read':move()
            else:
                replacement=f.path.with_suffix('.tmp');replacement.write_text(json.dumps(f.task))
                replacement.replace(f.path);events.append(True)
        return result
    monkeypatch.setattr(os,'stat',observe_stat);monkeypatch.setattr(os,'open',observe_open);monkeypatch.setattr(os,'read',observe_read)
    path,task=r.observe_task(f.queue,f.task['id'],f.expected,owner=os.geteuid())
    assert events==[True] and task==f.task
    assert path==(f.path if moment=='content-version' else target)


@pytest.mark.parametrize('fault',['missing','duplicate','symlink','hardlink','fifo','writable',
    'corrupt','oversize','task','run','fence','attempt'])
def test_task_observation_denies_stable_unsafe_state(canonical_queue,fault):
    import json
    from herdr.operation_readiness import observe_task
    f=canonical_queue;other=f.queue/'blocked'/f.path.name
    if fault=='missing':f.path.unlink()
    elif fault=='duplicate':other.write_bytes(f.path.read_bytes())
    elif fault=='symlink':f.path.rename(other);f.path.symlink_to(other)
    elif fault=='hardlink':os.link(f.path,other)
    elif fault=='fifo':f.path.unlink();os.mkfifo(f.path)
    elif fault=='writable':f.path.chmod(0o666)
    elif fault=='corrupt':f.path.write_bytes(b'{broken')
    elif fault=='oversize':f.path.write_bytes(b' '*(1048576+1))
    else:
        field={'task':'id','run':'run_token','fence':'fencing_token','attempt':'attempt_id'}[fault]
        f.task[field]=99 if field in ('fencing_token','attempt_id') else 'other'
        f.path.write_text(json.dumps(f.task))
    with pytest.raises((ReadinessError,ValueError)):
        observe_task(f.queue,'original',f.expected,owner=os.geteuid())


def test_task_snapshot_retry_is_bounded_and_read_only(canonical_queue,monkeypatch):
    from herdr import operation_readiness as r
    f=canonical_queue;original=os.stat;changes=[];body=f.path.read_bytes()
    def changing(path,*args,**kwargs):
        result=original(path,*args,**kwargs)
        if str(path)==f.path.name:
            info=f.path.stat();os.utime(f.path,ns=(info.st_atime_ns,info.st_mtime_ns+1))
            marker=f.queue/'running'/('marker'+str(len(changes)));marker.touch();changes.append(marker)
        return result
    monkeypatch.setattr(os,'stat',changing)
    with pytest.raises(r.SnapshotChanged):r.observe_task(f.queue,'original',f.expected,owner=os.geteuid())
    assert len(changes)==3 and f.path.read_bytes()==body


def test_task_queue_alias_and_untrusted_binding_are_denied(canonical_queue,tmp_path):
    from herdr.operation_readiness import observe_task
    f=canonical_queue;alias=tmp_path/'alias';alias.symlink_to(f.queue,target_is_directory=True)
    with pytest.raises(OSError):observe_task(alias,'original',f.expected,owner=os.geteuid())
    with pytest.raises(ReadinessError):observe_task(f.queue,'../original',f.expected,owner=os.geteuid())
    with pytest.raises(ReadinessError):observe_task(f.queue,'original',{},owner=os.geteuid())


def test_independent_lifetimes_cover_grant_and_complete_work():
    life=Lifetimes(grant_seconds=2700,work_seconds=1800,preparation_seconds=600,cleanup_seconds=300)
    assert life.credential_seconds()==3330
    assert Lifetimes(1200,1800,600,300).credential_seconds()==2730
    life.require_admin(2730)
    with pytest.raises(ReadinessError, match="administrator_window"):
        life.require_admin(2729)


@pytest.mark.parametrize('value',[0,-1,True,2.5])
def test_lifetime_configuration_cannot_be_silently_coerced(value):
    with pytest.raises(ReadinessError):Lifetimes(value,1800,600,300).credential_seconds()


def test_capacity_maintenance_does_not_authorize_admission():
    status=capacity(100, floor=100,start_guard=10,preparation_peak=5,growth_allowance=3,warning_margin=20)
    assert status['missing_bytes']==18 and not status['ready']
    assert capacity(118,floor=100,start_guard=10,preparation_peak=5,growth_allowance=3)['ready']
    assert capacity(118,floor=100,start_guard=10,preparation_peak=5,growth_allowance=3)['capacity_warning']


def test_same_failure_without_new_evidence_stops_preparation_loop():
    old={'reason_code':'credential_ttl','evidence_sha256':'original'}
    with pytest.raises(ReadinessError,match='reconciliation'):require_new_failure_evidence(old,dict(old))
    require_new_failure_evidence(old,dict(old,evidence_sha256='new-readiness-observation'))


def test_pilot_scope_configuration_keeps_authorized_budget(tmp_path):
    spec=importlib.util.spec_from_file_location('pilot',Path(__file__).resolve().parents[2]/'deploy/herdr/approved_pilot.py')
    pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)
    value={'runtime':{'root':str(tmp_path),'home':str(tmp_path/'home'),'code':str(tmp_path/'code'),
                     'python':'/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11','sdk':'/opt/herdr/releases/p0-5035d92-test/hermes'},
           'pilot':{'task_id':'issue77-validation-repair-20261026','model':'meituan/longcat-2.0:free',
                    'previous_model':'meituan/longcat-2.5-preview:free','base_commit':'frozen',
                    'max_model_calls':62,'max_cost_microusd':0,'administrator_window_seconds':540000},
           'lifetimes':{'grant_seconds':2700,'work_seconds':1800,'preparation_seconds':600,'cleanup_seconds':300,'skew_seconds':30},
           'capacity':{'floor':9663676416,'start_guard':134217728}}
    pilot.configure(value)
    assert pilot.REQUIRED_CREDENTIAL_SECONDS==3330 and pilot.STORE==tmp_path/'home/.local/state/herdr-policy-approved38'
    for field,changed in [('max_model_calls',63),('max_cost_microusd',1),('administrator_window_seconds',540001),('model','other-model')]:
        altered=copy.deepcopy(value);altered['pilot'][field]=changed
        with pytest.raises(RuntimeError):pilot.configure(altered)
    for field,changed in [('grant_seconds',2699),('work_seconds',1801),('preparation_seconds',599),('cleanup_seconds',299)]:
        altered=copy.deepcopy(value);altered['lifetimes'][field]=changed
        with pytest.raises(RuntimeError):pilot.configure(altered)


def test_entire_offline_cycle_is_bound_to_same_composition():
    from herdr.operation_readiness import require_offline_acceptance
    proof={'schema_version':'herdr-ordinary-offline-acceptance-1','composition_sha256':'frozen',
           'checked_at_epoch':1000,'ordinary_worker_used':True,'actual_sdk_used':True,'host_ipc_used':True,
           'work_tools_verified':True,'validation_verified':True,'local_result_accepted':True,
           'external_provider_http_requests':0,'external_authentication_http_requests':0,'fixture_only':True}
    require_offline_acceptance(proof,'frozen',now_epoch=1001)
    for field in ('ordinary_worker_used','actual_sdk_used','host_ipc_used','work_tools_verified','validation_verified','local_result_accepted','fixture_only'):
        with pytest.raises(ReadinessError):require_offline_acceptance(dict(proof,**{field:False}),'frozen',now_epoch=1001)
    for field,value in [('composition_sha256','different'),('checked_at_epoch',-90000),('external_provider_http_requests',1),('external_authentication_http_requests',True)]:
        with pytest.raises(ReadinessError):require_offline_acceptance(dict(proof,**{field:value}),'frozen',now_epoch=1001)


@pytest.mark.skipif(os.geteuid()!=0,reason='cross-user protected-file observation requires administrator')
def test_protected_read_accepts_access_time_change_for_an_unprivileged_reader():
    import subprocess
    import sys
    import tempfile
    with tempfile.TemporaryDirectory(prefix='herdr-protected-atime-',dir='/var/lib') as folder:
        root=Path(folder);source=root/'marker';source.write_bytes(b'protected-observation')
        source.chmod(0o444);os.utime(source,ns=(1_000_000_000,source.stat().st_mtime_ns));before=source.stat()
        root.chmod(0o555)
        module=Path(__file__).resolve().parents[2]/'herdr/operation_readiness.py'
        code="import importlib.util,sys;spec=importlib.util.spec_from_file_location('readiness_atime',sys.argv[1]);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);assert m.read_protected(sys.argv[2])==b'protected-observation';print('PASS')"
        def drop():os.setgroups([]);os.setgid(1001);os.setuid(1001)
        result=subprocess.run([sys.executable,'-I','-B','-c',code,str(module),str(source)],preexec_fn=drop,
                              capture_output=True,text=True,timeout=10,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
        assert result.returncode==0,result.stderr
        after=source.stat()
        assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
