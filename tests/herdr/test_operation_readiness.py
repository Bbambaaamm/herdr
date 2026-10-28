import copy
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
           'work_tools_verified':True,'validation_verified':True,'result_accepted':True,
           'provider_http_requests':0,'authentication_http_requests':0,'fixture_only':True}
    require_offline_acceptance(proof,'frozen',now_epoch=1001)
    for field in ('ordinary_worker_used','actual_sdk_used','host_ipc_used','work_tools_verified','validation_verified','result_accepted','fixture_only'):
        with pytest.raises(ReadinessError):require_offline_acceptance(dict(proof,**{field:False}),'frozen',now_epoch=1001)
    for field,value in [('composition_sha256','different'),('checked_at_epoch',-90000),('provider_http_requests',1),('authentication_http_requests',True)]:
        with pytest.raises(ReadinessError):require_offline_acceptance(dict(proof,**{field:value}),'frozen',now_epoch=1001)
