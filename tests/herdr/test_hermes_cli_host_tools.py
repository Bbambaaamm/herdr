"""Host-handler identity resolution; synthetic ports, never worker acceptance."""
from contextvars import ContextVar,copy_context
from dataclasses import replace
import json,socket,subprocess,types
import pytest
from herdr import delegation_tool,external_knowledge_tool,result_submission,work_tool
from herdr.hermes_guard import GuardInstallation,_call_digest
from herdr.hermes_cli_identity import CLIInvocationBinding
from herdr.policy_launch import IDENTITY_ENV
from herdr.security import PolicyDenied,RiskClass,ToolRule
from herdr.work_contract_host import WorkInvocationGuard
from test_hermes_cli_identity import guard,fixture_types,prepare

class Registry:
    def __init__(self):self.entries={}
    def get_entry(self,name):return self.entries.get(name)
    def register(self,*,name,handler,**kwargs):
        assert name not in self.entries
        self.entries[name]=types.SimpleNamespace(handler=handler)
    def restore_registration(self,name,current,previous):
        if self.entries.get(name) is current:self.entries.pop(name);return True
        return False

@pytest.fixture(autouse=True)
def no_external_effects(monkeypatch):
    def deny(*args,**kwargs):raise AssertionError('network/process forbidden')
    for name in ('connect','connect_ex','sendto'):monkeypatch.setattr(socket.socket,name,deny)
    monkeypatch.setattr(socket,'create_connection',deny);monkeypatch.setattr(socket,'getaddrinfo',deny)
    monkeypatch.setattr(subprocess,'Popen',deny)

def setup(tmp_path,monkeypatch,tool,role):
    item=guard(tmp_path,task='root-task' if role=='root' else 'managed-child-task',
               agent_id='root-agent' if role=='root' else 'child-agent',
               parent_task_id='root-task',parent_agent_id='root-agent')
    effects=[]
    class Authority:
        def __call__(self,*args,**kwargs):return True
        def verify(self,identity,digest,request_id,**kwargs):
            effects.append(('verify',identity,request_id));return {'component_effect_only':True}
        def external_knowledge(self,identity,digest,provider_id,request):
            from herdr.external_knowledge import KnowledgeResponse,KnowledgeSourceResult
            effects.append(('knowledge',identity,request.query))
            return KnowledgeResponse(request.request_id,'completed','component-only',tuple(KnowledgeSourceResult(source,'ok',1,answer='component-only') for source in request.sources),False)
    authority=Authority()
    if tool=='work':
        module=work_tool;raw={'request_id':'component_verify'}
        rule=ToolRule(module.TOOL,RiskClass.READ,('request_id',),requires_sandbox=True)
    elif tool=='delegation':
        module=delegation_tool;raw={'key':'unit-key','role':'reader','objective':'Inspect','prompt':'Synthetic component only'}
        rule=ToolRule(module.TOOL,RiskClass.DELEGATION,module.ARGUMENTS,requires_sandbox=True)
        monkeypatch.setattr(module,'_client_delegate',lambda args:effects.append(('delegate',item.grant.identity,args)) or {'component_effect_only':True})
    elif tool=='result':
        module=result_submission;raw={'status':'blocked','evidence':[{'component':'identity-only'}]}
        destination=tmp_path/'bound-result.json';destination.touch(mode=0o600)
        slot=module.ResultSlot.bind(destination,item.grant.identity,'unit-result-key')
        rule=ToolRule(module.TOOL,RiskClass.RESULT_SUBMISSION,module.ARGUMENTS,allowed_roots=(str(tmp_path),),requires_sandbox=True,result_slot=slot)
        original=module.submit
        def submit(*args,**kwargs):
            answer=original(*args,**kwargs);effects.append(('result',item.grant.identity,answer));return answer
        monkeypatch.setattr(module,'submit',submit)
    else:
        module=external_knowledge_tool;raw={'provider_id':'unit','query':'Synthetic evidence','sources':['mail']}
        rule=ToolRule(module.TOOL,RiskClass.READ,module.ARGUMENTS,requires_sandbox=True)
        monkeypatch.setattr('herdr.work_authority.WorkAuthorityClient',lambda:authority)
    grant=replace(item.grant,scope=replace(item.grant.scope,tools=(module.TOOL,)),tool_rules=(rule,))
    item=WorkInvocationGuard(grant,work_authority=authority)
    binding=CLIInvocationBinding(item);installation=GuardInstallation(item,cli_invocation_binding=binding)
    registry=Registry();context=ContextVar('component-authorized',default=None)
    for field,key in IDENTITY_ENV.items():monkeypatch.setenv(key,str(getattr(grant.identity,field)))
    for key,value in {'HERDR_DURABLE_SANDBOX':'1','HERDR_DURABLE_TASK_ID':grant.identity.task_id,
                      'HERDR_DURABLE_RUN_TOKEN':grant.identity.run_token,'HERDR_DURABLE_AGENT':grant.identity.agent_id,
                      'HERDR_DURABLE_MARKER':'unit-marker','HERDR_PANE_ID':'unit-pane'}.items():monkeypatch.setenv(key,value)
    getattr(module,{'work':'register_work_tool','delegation':'register_delegation_tool','result':'register_result_tool','knowledge':'register_external_knowledge_tool'}[tool])(installation,registry,context,_call_digest)
    return item,binding,installation,registry.get_entry(module.TOOL).handler,raw,effects

@pytest.mark.parametrize('role',('root','managed-child'))
@pytest.mark.parametrize('tool',('work','delegation','result','knowledge'))
def test_live_host_handlers_resolve_identity_without_rewriting_sdk_args(tmp_path,monkeypatch,tool,role):
    item,binding,installation,handler,raw,effects=setup(tmp_path,monkeypatch,tool,role)
    CLI,Agent=fixture_types();original=json.loads(json.dumps(raw))
    try:
        with binding.factory(CLI,Agent):
            cli,agent=prepare(binding,CLI,Agent,session='sdk-session')
            with binding.turn(agent,cli.session_id):
                token=binding.begin_tool(agent,cli.session_id)
                try:answer=json.loads(handler(raw,task_id=cli.session_id))
                finally:binding.end_tool(token)
                assert 'error' not in answer
                assert len(effects)==1 and effects[0][1]==item.grant.identity
                assert raw==original and cli.session_id==agent.session_id=='sdk-session'
                assert cli.session_id!=item.grant.identity.task_id
    finally:installation.uninstall()

@pytest.mark.parametrize('role',('root','managed-child'))
@pytest.mark.parametrize('tool',('work','delegation','result','knowledge'))
@pytest.mark.parametrize('fault',('out-of-turn','wrong-session','host-task-spoof','copied-stale','grant-swap','uninstall'))
def test_host_handler_binding_failures_precede_host_effect(tmp_path,monkeypatch,tool,role,fault):
    item,binding,installation,handler,raw,effects=setup(tmp_path,monkeypatch,tool,role)
    CLI,Agent=fixture_types()
    try:
        with binding.factory(CLI,Agent):
            cli,agent=prepare(binding,CLI,Agent,session='sdk-session')
            if fault=='out-of-turn':answer=handler(raw,task_id=cli.session_id)
            else:
                with binding.turn(agent,cli.session_id):
                    token=binding.begin_tool(agent,cli.session_id)
                    try:
                        if fault=='copied-stale':context=copy_context()
                        else:
                            if fault=='grant-swap':item.grant=replace(item.grant,grant_id='changed')
                            if fault=='uninstall':installation.uninstall()
                            task='foreign-session' if fault=='wrong-session' else item.grant.identity.task_id if fault=='host-task-spoof' else cli.session_id
                            answer=handler(raw,task_id=task)
                    finally:binding.end_tool(token)
                if fault=='copied-stale':answer=context.run(handler,raw,task_id=cli.session_id)
            assert 'error' in json.loads(answer) and effects==[]
            if tool=='result':assert (tmp_path/'bound-result.json').read_bytes()==b''
    finally:installation.uninstall()

def test_legacy_installation_keeps_exact_caller_semantics(tmp_path):
    installation=GuardInstallation(guard(tmp_path))
    assert installation.resolve_caller_task_id(None) is None
    assert installation.resolve_caller_task_id('unchanged-session')=='unchanged-session'
