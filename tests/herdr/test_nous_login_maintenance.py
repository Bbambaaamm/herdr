import base64
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest


def load():
    path=Path(__file__).resolve().parents[2]/'deploy/herdr/maintain_nous_login.py'
    spec=importlib.util.spec_from_file_location('maintain',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def key(until):
    body=base64.urlsafe_b64encode(json.dumps({'exp':until}).encode()).decode().rstrip('=')
    return 'fixture.'+body+'.fixture'


@pytest.mark.parametrize('original,renew',[ (10000,False),(4000,True),(1,True)])
def test_only_original_sdk_resolver_maintains_credentials_once(original,renew):
    m=load();calls=[]
    def resolve(**kwargs):
        calls.append(kwargs)
        return {'provider':'nous','base_url':'https://inference-api.nousresearch.com/v1','api_key':key(10000)}
    auth=SimpleNamespace(get_provider_auth_state=lambda provider:{'agent_key':key(original),'refresh_token':'private'},resolve_nous_runtime_credentials=resolve)
    result=m.maintain(auth,3330,now=lambda:1000)
    assert result['credential_ready'] and result['model_calls']==0 and result['credentials_exported'] is False
    assert len(calls)==1 and calls[0]['force_refresh']==renew
    assert 'private' not in json.dumps(result) and 'api_key' not in result


def test_invalid_grant_never_triggers_second_resolver_call():
    m=load();calls=[]
    def denied(**kwargs):
        calls.append(kwargs);raise RuntimeError('invalid_grant')
    auth=SimpleNamespace(get_provider_auth_state=lambda provider:{'agent_key':key(1)},resolve_nous_runtime_credentials=denied)
    with pytest.raises(RuntimeError):m.maintain(auth,3330,now=lambda:1000)
    assert len(calls)==1


def test_short_provider_token_does_not_silently_lower_required_lifetime():
    m=load()
    auth=SimpleNamespace(get_provider_auth_state=lambda p:{},resolve_nous_runtime_credentials=lambda **kw:{'provider':'nous','base_url':'https://inference-api.nousresearch.com/v1','api_key':key(2000)})
    result=m.maintain(auth,3330,now=lambda:1000)
    assert not result['credential_ready'] and result['required_validity_seconds']==3330
