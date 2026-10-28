import copy
import os
import importlib.util
from pathlib import Path
import pytest
from herdr.operation_readiness import Lifetimes, ReadinessError, capacity, require_new_failure_evidence


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
