"""Actual SDK registered work-handler component; no CLI/agent/model startup."""
from pathlib import Path
import json,subprocess
import pytest
from test_hermes_cli_identity import guard
from test_hermes_cli_identity_sdk import SCRIPT,PINS,SDK,PYTHON

WORK_SCRIPT=SCRIPT.replace('binding=CLIInvocationBinding(item)','''from dataclasses import replace
from herdr.security import ToolRule,RiskClass
from herdr.policy_launch import IDENTITY_ENV
item.grant=replace(item.grant,scope=replace(item.grant.scope,tools=(*item.grant.scope.tools,"herdr_verify_work")),tool_rules=(*item.grant.tool_rules,ToolRule("herdr_verify_work",RiskClass.READ,("request_id",),requires_sandbox=True)))
for field,key in IDENTITY_ENV.items():os.environ[key]=str(getattr(item.grant.identity,field))
os.environ["HERDR_DURABLE_SANDBOX"]="1"
verify_calls=[]
def verify(identity,grant_hash,request_id,**kwargs):
    verify_calls.append((identity,request_id))
    return {"component_effect_only":True}
phase.verify=verify
binding=CLIInvocationBinding(item)''').replace('            result=dispatch("read_file",{"path":"component.txt","offset":1,"limit":10})','''            result=dispatch("herdr_verify_work",{"request_id":"component_verify"})
            assert json.loads(result.result).get("component_effect_only") is True, result.result
            assert verify_calls==[(item.grant.identity,"component_verify")]
            result=dispatch("read_file",{"path":"component.txt","offset":1,"limit":10})''')

@pytest.mark.parametrize('role',('root','managed-child'))
def test_actual_sdk_executor_registered_work_handler(tmp_path,role):
    if not SDK.is_dir() or not PYTHON.is_file():pytest.skip('fixed pinned Hermes SDK component is not installed')
    repo=Path(__file__).resolve().parents[2];home=tmp_path/'home';home.mkdir()
    item=guard(tmp_path/'allowed',task='root-task' if role=='root' else 'managed-child-task',
               agent_id='root-agent' if role=='root' else 'child-agent',parent_task_id='root-task',parent_agent_id='root-agent')
    result=subprocess.run([str(PYTHON),'-I','-B','-c',WORK_SCRIPT,str(repo),str(SDK),str(tmp_path),'work',json.dumps(item.grant.to_json()),json.dumps(PINS)],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=45,
        env={'PATH':'/usr/bin:/bin','HOME':str(home),'HERMES_HOME':str(home/'.hermes'),'HERMES_SAFE_MODE':'1',
             'HERMES_ENABLE_PROJECT_PLUGINS':'0','TERMINAL_ENV':'local','PYTHONDONTWRITEBYTECODE':'1','LANG':'C.UTF-8'})
    assert result.returncode==0,result.stderr
    observed=json.loads(result.stdout.splitlines()[-1])
    assert observed['actual_sdk_file_flow'] and observed['work_guard']
    assert observed['network_attempts']==0 and observed['blocked_local_bootstrap_attempts']==2
