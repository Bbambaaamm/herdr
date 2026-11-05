"""Root executor has no authority ledger and accepts only the pinned publisher."""
from dataclasses import replace
from types import SimpleNamespace
import base64
import time
import pytest

from herdr.parent_github_peer import execute_request
from herdr.evidence import EvidenceError
from tests.herdr.test_parent_github_transport import permit


def invoke(method, **values):
    p=permit()
    calls=[]
    client=SimpleNamespace(observe=lambda *args:calls.append(('observe',args)) or {'base_sha':p.base_sha},
        push=lambda *args:calls.append(('push',args)),
        create_pull_request=lambda *args:calls.append(('create_pull_request',args)))
    request={'method':method,'permit':p.hash,'commit_sha':'d'*40,**values}
    return p,client,calls,request


def test_executor_preserves_existing_transport_methods_and_permit():
    p,c,calls,r=invoke('observe')
    assert execute_request(r,permit=p,transport=c)=={'base_sha':p.base_sha}
    assert calls[0][0]=='observe'
    p,c,calls,r=invoke('push',bundle=base64.b64encode(b'bounded-bundle').decode())
    execute_request(r,permit=p,transport=c)
    assert calls[0][1][2]==b'bounded-bundle'


@pytest.mark.parametrize('change',[{'method':'shell'},{'permit':'other'},{'commit_sha':'--upload-pack=evil'},
    {'argv':['sh']},{'budget':{'model_calls':999}},{'url':'https://example.invalid'}])
def test_executor_rejects_new_authority_or_commands(change):
    p,c,calls,r=invoke('observe')
    with pytest.raises(EvidenceError):execute_request(dict(r,**change),permit=p,transport=c)
    assert calls==[]


def test_executor_rejects_other_branches_before_external_effect():
    body={'title':'review','body':'public','base':'main','head':'other'}
    p,c,calls,r=invoke('create_pull_request',request=body)
    with pytest.raises(EvidenceError):execute_request(r,permit=p,transport=c)
    assert calls==[]
    body.update(base=p.base_branch,head=p.head_branch)
    execute_request(r,permit=p,transport=c)
    assert len(calls)==1
    with pytest.raises(EvidenceError):execute_request(r,permit=replace(p,expires_at_epoch=int(time.time())-1),transport=c)
