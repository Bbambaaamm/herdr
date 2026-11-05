import base64
import importlib.util
import json
from pathlib import Path
import time
import pytest


def helper():
    p=Path(__file__).resolve().parents[2]/'deploy/herdr/existing_credential_snapshot.py'
    spec=importlib.util.spec_from_file_location('snapshot',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def token(until):
    body=base64.urlsafe_b64encode(json.dumps({'exp':until}).encode()).decode().rstrip('=')
    return 'fixture.'+body+'.fixture'


def test_selected_key_is_only_provider_credential_and_refresh_material_is_absent():
    m=helper();key=token(int(time.time())+3600)
    entry={'id':'synthetic-entry','agent_key':key,'access_token':'old-unselected','refresh_token':'never-copy',
           'nested':{'refresh_token':'never-copy-nested','public':'preserved'}}
    store=m.minimal_store(entry,key)
    assert store['providers']['nous']['agent_key']==store['providers']['nous']['access_token']==key
    assert m.strip_refresh(store)==store
    assert 'never-copy' not in json.dumps(store)
    assert set(store['providers'])==set(store['credential_pool'])=={'nous'}


@pytest.mark.parametrize('key',['opaque-invalid',token(1),''])
def test_expired_or_unrelated_keys_are_denied(key):
    with pytest.raises(AssertionError):helper().minimal_store({'id':'fixture','agent_key':key},key)


def test_private_snapshot_creation_never_overwrites(tmp_path):
    m=helper();p=tmp_path/'auth.json';m.write_private(p,b'original')
    assert p.stat().st_mode & 0o777==0o600
    with pytest.raises(FileExistsError):m.write_private(p,b'replacement')
    assert p.read_bytes()==b'original'
