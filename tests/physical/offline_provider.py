"""Provider-response fixture for the ordinary native pilot (never real inference).

The ordinary launcher, SDK, authority, tools, budget, verification and result slot
remain unchanged. Only the remote provider is represented by this local TLS peer.
"""
import hashlib
import json
import re
from pathlib import Path

FILES=('agent_platform_dashboard/production_sources.py','agent_platform_dashboard/production_contract.py',
       'tests/agent_platform_dashboard/test_production.py','provenance/CANONICAL_SOURCE_MANIFEST.sha256')


def fixture_edits(originals):
    # A predetermined golden fixture only. The live task's workspace is untouched.
    changed=dict(originals)
    s=changed[FILES[0]]
    before="    c.need(type(raw) is dict and raw['version'] == 1\n           and type(raw['fabrics']) is list and len(raw['fabrics']) <= 16)"
    after="    c.keys(raw, 'version fabrics')\n    c.need(type(raw['version']) is int and raw['version'] == 1\n           and type(raw['fabrics']) is list and len(raw['fabrics']) <= 16)"
    assert s.count(before)==1
    s=s.replace(before,after)
    before="    measured, unavailable = [], []\n    for fabric in raw['fabrics']:"
    assert s.count(before)==1
    s=s.replace(before,"    measured, unavailable = [], []\n    seen_ids = set()\n    for fabric in raw['fabrics']:")
    assert s.count('            seen_ids = set()')==1
    changed[FILES[0]]=s.replace('            seen_ids = set()\n','')
    s=changed[FILES[1]]
    before="        need(len({json.dumps(r, sort_keys=True) for r in source['rows']}) == len(source['rows']))\n    return value"
    after="        need(len({json.dumps(r, sort_keys=True) for r in source['rows']}) == len(source['rows']))\n    legacy = {pair for pair in SOURCE_PAIRS if pair[1] not in {'metrics', 'route', 'lifecycle'}}\n    need(seen in (set(SOURCE_PAIRS), legacy, legacy | {('quantlab', 'metrics')}))\n    return value"
    assert s.count(before)==1
    changed[FILES[1]]=s.replace(before,after)
    # The frozen external oracle checks the fixture delta independently. No
    # producer measurement, unavailable value or business scope is replaced.
    manifest=[]
    for line in changed[FILES[3]].splitlines():
        digest,name=line.split('  ',1)
        if name in changed and name!=FILES[3]:digest=hashlib.sha256(changed[name].encode()).hexdigest()
        manifest.append((digest,name))
    changed[FILES[3]]=''.join(digest+'  '+name+'\n' for digest,name in sorted(manifest))
    return {name:body for name,body in changed.items() if body!=originals[name]}


class ProviderFixture:
    def __init__(self, originals, *, scope_claim=None):
        self.edits=fixture_edits(originals)
        self.scope_claim=scope_claim
        self.turn=0
        self.complete=False
        self.files=FILES
        self.workspace='/home/agentops/worktrees/pilot/workspace/'

    @classmethod
    def for_clean_case(cls, path, expected_sha256, run_token):
        # The case is a pinned synthetic data file, never live task/profile data.
        # Reuse preparation validation; do not accept caller-supplied edits/paths.
        import runpy
        pilot = runpy.run_path(str(Path(__file__).with_name('offline_pilot.py')))
        inputs = pilot['prepare_clean_inputs'](path, expected_sha256, run_token)
        result = object.__new__(cls)
        result.edits = dict(inputs['provider_edits'])
        result.files = tuple(inputs['workspace_files'])
        result.workspace = inputs['task_seed']['workspace'] + '/'
        result.scope_claim = None
        result.turn = 0
        result.complete = False
        return result

    @staticmethod
    def _tools(payload):
        return {row['function']['name'] for row in payload.get('tools',[]) if row.get('type')=='function'}

    def answer(self,payload):
        self.turn+=1
        if not 1<=self.turn<=8:raise ValueError('bounded_fixture_turn_limit')
        names=self._tools(payload)
        required={'read_file','write_file','herdr_verify_work','herdr_submit_result'}
        if not required<=names:raise ValueError('actual_sdk_required_tools_missing')
        workspace=getattr(self,'workspace','/home/agentops/worktrees/pilot/workspace/')
        if self.turn==1:
            calls=[('read_file',{'path':workspace+name,'offset':1,'limit':2000}) for name in getattr(self,'files',FILES)]
        elif self.turn==2:
            calls=[('write_file',{'path':workspace+name,'content':body}) for name,body in self.edits.items()]
        elif self.turn==3:
            handoff={'pr_number':None}
            if self.scope_claim is not None:handoff['scope_claim']=self.scope_claim
            calls=[('herdr_verify_work',{'request_id':'offline_validation_once','handoff':handoff})]
        elif self.turn==4:
            values=[]
            for row in payload.get('messages',[]):
                if row.get('role')=='tool':
                    content=row.get('content')
                    try:value=json.loads(content)
                    except (TypeError,ValueError):continue
                    def find(value):
                        if isinstance(value,dict):
                            if 'submission' in value:values.append(value)
                            else:
                                for child in value.values():find(child)
                        elif isinstance(value,list):
                            for child in value:find(child)
                    find(value)
            if len(values)!=1 or values[0].get('status')!='pass':raise ValueError('actual_host_validation_did_not_pass')
            calls=[('herdr_submit_result',values[0]['submission'])]
        else:
            self.complete=True
            calls=[]
        message={'role':'assistant','content':None if calls else 'OFFLINE FIXTURE: exact local handoff submitted.'}
        if calls:
            message['tool_calls']=[{'id':f'offline_{self.turn}_{i}','type':'function',
                'function':{'name':name,'arguments':json.dumps(args,separators=(',',':'))}} for i,(name,args) in enumerate(calls)]
        return {'id':f'offline-completion-{self.turn}','object':'chat.completion','created':1,
            'model':payload.get('model'),'choices':[{'index':0,'message':message,'finish_reason':'tool_calls' if calls else 'stop'}],
            'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}


class TeamFixture:
    """Transport fixture only; never an acceptance/receipt authority.

    The root proposes one protected child. Its response (including a GitHub
    acceptance gate) is not interpreted as semantic completion. Both roles
    still need actual host oracle submissions, checked by the supervisor.
    """
    @classmethod
    def for_proposal(cls, proposal, delegation):
        obj = cls(); obj.delegation = delegation; obj.delegated = False
        def role(workspace):
            fixture = object.__new__(ProviderFixture)
            fixture.edits = dict(proposal['provider_edits'])
            fixture.files = tuple(proposal['workspace_files'])
            fixture.workspace = workspace.rstrip('/') + '/'
            fixture.scope_claim = None; fixture.turn = 0; fixture.complete = False
            return fixture
        obj.root = role(proposal['task_seed']['workspace'])
        obj.child = role(delegation['cwd'])
        return obj

    @property
    def complete(self):
        return self.delegated and self.root.complete and self.child.complete

    def answer(self, payload):
        names = {item['function']['name'] for item in payload.get('tools', [])}
        if 'herdr_delegate_child' not in names:
            return self.child.answer(payload)
        if self.delegated:
            return self.root.answer(payload)
        self.delegated = True
        return {'id': 'offline-delegation', 'object': 'chat.completion', 'created': 1,
            'model': payload.get('model'), 'choices': [{'index': 0, 'message': {
                'role': 'assistant', 'content': None, 'tool_calls': [{
                    'id': 'offline_delegate_once', 'type': 'function', 'function': {
                        'name': 'herdr_delegate_child', 'arguments': json.dumps(self.delegation)}}]},
                'finish_reason': 'tool_calls'}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}}
