"""Exact optional model intent across tool/CLI/client/closed bridge/proposal.

All model names are inert inputs. Only disposable scheduler journals are used;
no native runtime, SDK, provider, economic authority or live task is invoked.
"""
import argparse
from contextvars import ContextVar
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from herdr import delegation_tool as tool
from herdr.hermes_guard import GuardInstallation, _call_digest
from herdr.scheduler import AuditLog, DynamicChildScheduler, SchedulerError
from herdr.security import (SecurityError, InvocationGuard, InvocationIdentity, NetworkAccess,
    ProcessPolicy, RuntimeAssurance, SecurityGrant, ToolRule, RiskClass)
from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
from tests.agent_stack import test_durable_child_bridge as bridge_test

child=bridge_test.bridge
server=bridge_test.server
MODEL='fixture-provider/fixture-model:free'
FALLBACK='fixture-provider/fixture-fallback:free'
IDENTITY={'task_id':'parent','run_token':'run-1','agent':'parent-agent','pane':'parent-pane','marker':'marker'}
MODEL_KEYS={'model','fallback_model'}



class Registry:
    def __init__(self):self.entries={}
    def get_entry(self,name):return self.entries.get(name)
    def register(self,*,name,handler,**kwargs):
        assert name not in self.entries
        self.entries[name]=argparse.Namespace(handler=handler)
    def restore_registration(self,name,current,previous):
        if self.entries.get(name) is current:self.entries.pop(name);return True
        return False


def installed(tmp_path,monkeypatch,allowed=None):
    # Synthetic typed grant only; no signer, crypto fixture, provider or authority.
    identity=InvocationIdentity('github:Bbambaaamm/herdr','parent-agent','outer-agent',
        'outer-task','parent','run-1',9)
    scope=CapabilityScope(providers=(),capabilities=('reasoning',),executors=('hermes-runtime',),
        tools=(tool.TOOL,),permissions=(),regions=('eu-central',),data_classes=(DataClass.INTERNAL,),
        input_modalities=('text',),output_modalities=('text',),max_cost_microusd=0,
        max_context_tokens=8192,max_egress=Egress.REGION_BOUND,max_retention=Retention.LIMITED,
        training=Training.EXCLUDED)
    grant=SecurityGrant(workspace_root=str(tmp_path),grant_id='fixture-grant',identity=identity,
        scope=scope,tool_rules=(ToolRule(tool=tool.TOOL,risk=RiskClass.DELEGATION,
            allowed_arg_keys=tool.ARGUMENTS if allowed is None else allowed,requires_sandbox=True),),
        process=ProcessPolicy(False,(),NetworkAccess.NONE),
        runtime_assurance=RuntimeAssurance(sandbox_verified=True,sandbox_attestation_sha256='a'*64,
            network_access=NetworkAccess.NONE,writable_roots=(),credentials_isolated=True),
        provider_routes=(),credential_refs=(),approvals=(),approval_required_for=(),
        issued_at='2026-01-01T00:00:00+00:00',expires_at='2030-01-01T00:00:00+00:00')
    installation=GuardInstallation(InvocationGuard(grant),surface={});registry=Registry()
    from herdr.policy_launch import IDENTITY_ENV
    for field,key in IDENTITY_ENV.items():monkeypatch.setenv(key,str(getattr(identity,field)))
    for key,value in {'HERDR_DURABLE_SANDBOX':'1','HERDR_DURABLE_TASK_ID':identity.task_id,
        'HERDR_DURABLE_RUN_TOKEN':identity.run_token,'HERDR_DURABLE_AGENT':identity.agent_id,
        'HERDR_DURABLE_MARKER':'fixture-marker','HERDR_PANE_ID':'fixture-pane'}.items():
        monkeypatch.setenv(key,value)
    tool.register_delegation_tool(installation,registry,ContextVar('fixture-call',default=None),_call_digest)
    return installation,registry


def request(**policy):
    return {'operation':'delegate',**IDENTITY,'key':'model-intent','role':'reader',
            'objective':'Inspect frozen evidence','prompt':'Read frozen evidence',
            'tool':['read_file'],'permission':[],'cwd':'','ownership':None,**policy}


def arguments(**policy):
    return {'key':'model-intent','role':'reader','objective':'Inspect frozen evidence',
            'prompt':'Read frozen evidence','tool':['read_file'],'permission':[],**policy}


class Wire:
    def __init__(self):
        self.requests=[]
        payload=json.dumps({'ok':True,'result':{'task_id':'fixture-child'},'error':None}).encode()
        self.response=len(payload).to_bytes(4,'big')+payload
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def settimeout(self,value):assert value==3600
    def connect(self,name):assert name=='\0unit-model-intent'
    def sendall(self,body):
        length=int.from_bytes(body[:4],'big');assert length==len(body)-4
        self.requests.append(json.loads(body[4:]))
    def recv(self,n):
        part=self.response[:n];self.response=self.response[n:];return part


def client_environment(monkeypatch):
    for key,value in {'HERDR_DURABLE_SANDBOX':'1','HERDR_DURABLE_BRIDGE_SOCKET':'@unit-model-intent',
        'HERDR_DURABLE_TASK_ID':'parent','HERDR_DURABLE_RUN_TOKEN':'run-1',
        'HERDR_DURABLE_AGENT':'parent-agent','HERDR_PANE_ID':'parent-pane',
        'HERDR_DURABLE_MARKER':'marker'}.items():monkeypatch.setenv(key,value)


@pytest.mark.parametrize('policy',[{}, {'model':MODEL}, {'fallback_model':None},
    {'model':MODEL,'fallback_model':None},{'model':MODEL,'fallback_model':FALLBACK}])
def test_schema_handler_codec_and_closed_bridge_preserve_exact_presence(policy,monkeypatch):
    args=arguments(**policy)
    schema=tool.SCHEMA['parameters']
    assert schema['additionalProperties'] is False
    for key in policy:
        expected={'type':'string' if key=='model' else ['string','null'],'minLength':1,'maxLength':256}
        assert schema['properties'][key]==expected
    checked=tool._arguments(args)
    assert {k:checked[k] for k in MODEL_KEYS if k in checked}==policy
    client_environment(monkeypatch);wire=Wire()
    monkeypatch.setattr(child.socket,'socket',lambda *a:wire)
    assert child.client_delegate(argparse.Namespace(**checked))=={'task_id':'fixture-child'}
    sent=wire.requests[0]
    assert {k:sent[k] for k in MODEL_KEYS if k in sent}==policy
    received=server.validate_request(sent,IDENTITY)
    assert {k:vars(received)[k] for k in MODEL_KEYS if k in vars(received)}==policy


BAD_POLICIES=[{'model':None},{'model':True},{'model':7},{'model':[]},{'model':''},
    {'model':' '},{'model':'x\0y'},{'model':'x'*257},{'fallback_model':True},
    {'fallback_model':7},{'fallback_model':{}},{'fallback_model':''},
    {'fallback_model':' '},{'fallback_model':'x\0y'},{'fallback_model':'x'*257}]


@pytest.mark.parametrize('policy',BAD_POLICIES,ids=['model-null','model-bool','model-int','model-list',
    'model-empty','model-blank','model-NUL','model-long','fallback-bool','fallback-int',
    'fallback-dict','fallback-empty','fallback-blank','fallback-NUL','fallback-long'])
def test_invalid_policy_denied_at_tool_client_and_bridge_before_transport(policy,monkeypatch):
    with pytest.raises((SecurityError,ValueError)):tool._arguments(arguments(**policy))
    client_environment(monkeypatch)
    monkeypatch.setattr(child.socket,'socket',lambda *a:pytest.fail('invalid policy reached transport'))
    with pytest.raises((SecurityError,ValueError)):child.client_delegate(argparse.Namespace(**arguments(**policy)))
    with pytest.raises((SecurityError,ValueError)):server.validate_request(request(**policy),IDENTITY)


@pytest.mark.parametrize('extra',[{'provider':'self-approved'},{'api_base':'http://invalid'},
    {'model_policy':{'model':MODEL}},{'no_fallback':True}])
def test_unknown_route_or_policy_arguments_remain_closed(extra):
    with pytest.raises((SecurityError,ValueError)):tool._arguments(arguments(**extra))
    with pytest.raises(ValueError,match='schema'):server.validate_request(request(**extra),IDENTITY)


@pytest.mark.parametrize('policy',[{'model':'x'*256,'fallback_model':None},
    {'model':MODEL,'fallback_model':'y'*256}])
def test_policy_string_bounds_are_exact_and_null_is_not_omission(policy):
    checked=tool._arguments(arguments(**policy))
    assert {k:checked[k] for k in policy}==policy
    result=server.validate_request(request(**policy),IDENTITY)
    assert {k:vars(result)[k] for k in policy}==policy


def test_real_guard_allows_new_data_only_when_host_rule_explicitly_grants_names(tmp_path,monkeypatch):
    installation,registry=installed(tmp_path,monkeypatch)
    seen=[]
    monkeypatch.setattr(tool,'_client_delegate',lambda value:seen.append(value) or {'task_id':'child'})
    try:
        args={**arguments(),'model':MODEL,'fallback_model':None}
        assert json.loads(registry.get_entry(tool.TOOL).handler(args))=={'task_id':'child'}
        assert seen[0]['model']==MODEL and seen[0]['fallback_model'] is None
    finally:installation.uninstall()


@pytest.mark.parametrize('policy',[{'model':MODEL},{'fallback_model':None}])
def test_legacy_host_rule_does_not_gain_new_arguments_implicitly(tmp_path,monkeypatch,policy):
    old_arguments=tuple(k for k in tool.ARGUMENTS if k not in MODEL_KEYS)
    installation,registry=installed(tmp_path,monkeypatch,allowed=old_arguments)
    seen=[]
    monkeypatch.setattr(tool,'_client_delegate',lambda value:seen.append(value) or {'task_id':'child'})
    try:
        result=json.loads(registry.get_entry(tool.TOOL).handler({**arguments(),**policy}))
        assert 'error' in result and seen==[]
        assert json.loads(registry.get_entry(tool.TOOL).handler(arguments()))=={'task_id':'child'}
    finally:installation.uninstall()


@pytest.mark.parametrize('flags,policy',[
 ([],{}),(['--model',MODEL],{'model':MODEL}),
 (['--model',MODEL,'--no-fallback'],{'model':MODEL,'fallback_model':None}),
 (['--fallback-model',FALLBACK],{'fallback_model':FALLBACK}),
])
def test_actual_cli_parser_preserves_omission_and_explicit_no_fallback(monkeypatch,capsys,flags,policy):
    monkeypatch.setenv('HERDR_DURABLE_BRIDGE_SOCKET','@unit-model-intent')
    monkeypatch.setattr(child.sys,'argv',['agent-durable-child','--key','k','--role','reader',
        '--objective','Inspect','--prompt','Read',*flags])
    seen=[]
    monkeypatch.setattr(child,'client_delegate',lambda args:seen.append(vars(args).copy()) or {'task_id':'child'})
    assert child.main()==0
    assert {k:seen[0][k] for k in MODEL_KEYS if k in seen[0]}==policy
    assert json.loads(capsys.readouterr().out)=={'task_id':'child'}


def test_cli_fallback_flags_are_mutually_exclusive_before_client(monkeypatch):
    monkeypatch.setattr(child.sys,'argv',['agent-durable-child','--key','k','--role','reader',
        '--objective','Inspect','--prompt','Read','--fallback-model',FALLBACK,'--no-fallback'])
    monkeypatch.setattr(child,'client_delegate',lambda *a:pytest.fail('conflicting choices reached client'))
    with pytest.raises(SystemExit) as failure:child.main()
    assert failure.value.code==2


@pytest.mark.parametrize('policy,expected',[({},('laguna','longcat')),
    ({'model':MODEL},(MODEL,'longcat')),
    ({'fallback_model':None},('laguna',None)),
    ({'model':MODEL,'fallback_model':None},(MODEL,None)),
    ({'model':MODEL,'fallback_model':FALLBACK},(MODEL,FALLBACK))])
def test_actual_closed_request_to_real_childproposal_and_scheduler_keeps_policy(
        tmp_path,monkeypatch,policy,expected):
    task,path=bridge_test._task(tmp_path);bridge_test._env(monkeypatch,path)
    monkeypatch.setattr(child,'_parent_context',lambda runner:(task,'parent-pane','parent-agent','marker'))
    delivered=[]
    class Runtime:
        def __init__(self,scheduler,*args,**kwargs):self.scheduler=scheduler
        def run_managed_child(self,lease,*args,**kwargs):
            delivered.append(self.scheduler.task_node(lease.task_id).model_policy.copy())
    monkeypatch.setattr(child,'HerdrChildRuntime',Runtime)
    args=server.validate_request(request(**policy),IDENTITY)
    first=child.delegate(args)
    assert delivered==[{'model':expected[0],'fallback_model':expected[1]}]
    second=child.delegate(args)
    assert second['task_id']==first['task_id'] and len(delivered)==1
    directory=path.parent.parent/'durable-children'/__import__('hashlib').sha256(b'parent:run-1').hexdigest()
    cold=DynamicChildScheduler(audit_log=AuditLog(directory/'scheduler.jsonl'));cold.replay()
    assert cold.task_node(first['task_id']).model_policy==delivered[0]
    for drift in [{'model':'fixture-other','fallback_model':expected[1]},
                  {'model':expected[0],'fallback_model':FALLBACK if expected[1] is None else None}]:
        before=(directory/'scheduler.jsonl').read_bytes()
        with pytest.raises(SchedulerError,match='delegation key reused with different identity or work'):
            child.delegate(server.validate_request(request(**drift),IDENTITY))
        assert (directory/'scheduler.jsonl').read_bytes()==before and len(delivered)==1



def test_registered_tool_actual_codec_closed_validator_and_real_proposal_compose(tmp_path,monkeypatch):
    task,path=bridge_test._task(tmp_path)
    installation,registry=installed(tmp_path,monkeypatch)
    bridge_test._env(monkeypatch,path)
    monkeypatch.setenv('HERDR_DURABLE_BRIDGE_SOCKET','@unit-model-intent')
    monkeypatch.setattr(child,'_parent_context',lambda runner:(task,'parent-pane','parent-agent','marker'))
    delivered=[]
    class Runtime:
        def __init__(self,scheduler,*args,**kwargs):self.scheduler=scheduler
        def run_managed_child(self,lease,*args,**kwargs):
            delivered.append(self.scheduler.task_node(lease.task_id).model_policy.copy())
    monkeypatch.setattr(child,'HerdrChildRuntime',Runtime)
    class HostWire(Wire):
        def sendall(self,body):
            size=int.from_bytes(body[:4],'big');assert size==len(body)-4
            received=json.loads(body[4:]);self.requests.append(received)
            validated=server.validate_request(received,IDENTITY)
            result=child.delegate(validated)
            payload=json.dumps({'ok':True,'result':result,'error':None}).encode()
            self.response=len(payload).to_bytes(4,'big')+payload
    wire=HostWire();monkeypatch.setattr(child.socket,'socket',lambda *a:wire)
    try:
        result=json.loads(registry.get_entry(tool.TOOL).handler(arguments(model=MODEL,fallback_model=None)))
        assert result.get('task_id','').startswith('parent-child-') and 'error' not in result
        assert delivered==[{'model':MODEL,'fallback_model':None}]
        assert wire.requests[0]['model']==MODEL and wire.requests[0]['fallback_model'] is None
        assert installation.guard.grant.scope.providers==() and installation.guard.grant.provider_routes==()
    finally:installation.uninstall()
