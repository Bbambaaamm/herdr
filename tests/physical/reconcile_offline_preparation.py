"""Complete retained, pre-SDK fixture preparation; never redispatch a worker."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import os
import runpy
import stat
import subprocess
import sys
import time

BOOTSTRAP=Path('/opt/herdr/operations/a0c5371e10ab')
P='/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11'


def need(ok,reason):
    if not ok:raise RuntimeError(reason)


def exact_file(path,body,*,mode=0o600,owner=0):
    if path.exists():
        info=path.lstat();need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==owner and stat.S_IMODE(info.st_mode)==mode and path.read_bytes()==body,'retained_preparation_file_changed')
        return
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
    os.chown(path,owner,1001)


def complete(composition_path,composition_sha,output,new_composition):
    need(os.geteuid()==0,'administrator_required')
    sys.path.insert(0,str(BOOTSTRAP));from herdr.operation_readiness import load_composition
    cfg=load_composition(composition_path,composition_sha);need(Path(cfg['runtime']['code'])==BOOTSTRAP,'frozen_runtime_changed')
    need(output==Path('/var/lib/herdr-ordinary-offline-a0c5371-20261028'),'exact_retained_fixture_required')
    state=subprocess.check_output(['/usr/bin/systemctl','show','herdr-ordinary-offline-a0c5371-20261028.service','--property=MainPID','--value'],text=True)
    need(state.strip()=='0','original_preparation_still_running')
    helpers=runpy.run_path(str(Path(__file__).with_name('offline_pilot.py')))
    root=Path(cfg['runtime']['root']);live=root/'home-diagnostic15/agentops';saved=output/'root';home=saved/'home-diagnostic15/agentops'
    before=helpers['snapshot_live'](root)
    for base in (live,home):need(not list((base/'.local/state/herdr-policy-approved38').glob('work-budget/*/events.jsonl')),'economic_admission_already_started')
    need(not (output/'isolated-private.log').exists() and not (output/'preparation-completed.json').exists(),'original_inner_cycle_already_attempted')
    need(not (home/'.local/state/agent-stack/pilot-control-runtime-approved38').exists(),'native_cycle_already_started')
    seed=json.loads((root/'resume-task-reviewed-approved38.json').read_bytes());copy=json.loads((saved/'resume-task-reviewed-approved38.json').read_bytes())
    exclude={'attempt_started_at','dispatch_claimed_at'}
    need({k:v for k,v in seed.items() if k not in exclude}=={k:v for k,v in copy.items() if k not in exclude},'retained_task_identity_changed')
    need((home/'.local/state/agent-stack/tasks/pending'/('issue77-validation-repair-20261026.json')).read_bytes()==(saved/'resume-task-reviewed-approved38.json').read_bytes(),'retained_pending_seed_changed')
    for state in ('running','blocked','failed','done'):need(not list((home/'.local/state/agent-stack/tasks'/state).glob('*.json')),'retained_attempt_state_changed')
    for name in ('herdr','hermes'):
        need(hashlib.sha256(helpers['read_native_snapshot'](home/'.local/bin'/name)).digest()==hashlib.sha256(helpers['read_native_snapshot'](live/'.local/bin'/name)).digest(),'retained_native_source_changed')
    proof_code="""from pathlib import Path
import subprocess,os,json
subprocess.run(['/usr/bin/mount','--make-rprivate','/'],check=True)
subprocess.run(['/usr/bin/mount','--bind',__import__('sys').argv[1],'/home'],check=True)
os.setgroups([]);os.setgid(1001);os.setuid(1001)
base=['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-c','core.worktree=/home/agentops/worktrees/pilot/workspace','-C','/home/agentops/worktrees/pilot/workspace']
assert subprocess.check_output(base+['rev-parse','HEAD'],text=True).strip()=='687c0c5041d9871c5a2eb0d4a116673b09c85438'
assert not subprocess.check_output(base+['status','--porcelain'],text=True).strip()
print('PASS')
"""
    checked=subprocess.run(['/usr/bin/unshare','--mount','--fork',P,'-I','-B','-c',proof_code,str(saved/'home-diagnostic15')],capture_output=True,text=True,timeout=20)
    need(checked.returncode==0,'retained_workspace_not_clean_frozen_base')
    raw=json.loads((root/'etc-approved38/host-policy.json').read_bytes());source=Path(raw['private_launch']['profile']['source']);base=saved/'profiles-offline-base/quantlab'
    auth=(base/'auth.json').read_bytes();store=json.loads(auth);token=store['providers']['nous']['agent_key'];part=token.split('.')[1];claims=json.loads(base64.urlsafe_b64decode(part+'='*((-len(part))%4)))
    need(claims.get('sub')=='herdr-offline-fixture' and claims['exp']-time.time()>=3330,'retained_synthetic_credential_changed_or_short')
    def no_refresh(value):
        if isinstance(value,dict):return all('refresh' not in key.lower() and no_refresh(child) for key,child in value.items())
        if isinstance(value,list):return all(no_refresh(child) for child in value)
        return True
    need(no_refresh(store),'retained_auth_contains_refresh_material')
    intent=output/'reconciliation-intent.json'
    if intent.exists():
        prior=json.loads(intent.read_bytes())
        need(prior.get('composition_sha256')==composition_sha and prior.get('original_sha256')==before and prior.get('native_sdk_not_previously_started') is True,'prior_preparation_intent_changed')
        helpers['json_file'](output/'reconciliation-inventory-continuation.json',{'at_epoch':time.time(),'prior_intent_sha256':hashlib.sha256(intent.read_bytes()).hexdigest(),'original_sha256':before,'first_inner_cycle_not_started':True,'automatic_retry_allowed':False})
    else:helpers['json_file'](intent,{'at_epoch':time.time(),'composition_sha256':composition_sha,'original_sha256':before,'native_sdk_not_previously_started':True,'automatic_retry_allowed':False})
    for member in helpers['frozen_profile_members'](source,raw['private_launch']['profile']['files']):
        body=auth if member.name=='auth.json' else member.read_bytes().replace(b'meituan/longcat-2.5-preview:free',b'meituan/longcat-2.0:free')
        if member.name=='.env':body=helpers['safe_profile_environment'](body)
        exact_file(base/member.name,body,mode=0o444)
        exact_file(home/'.hermes/profiles/quantlab'/member.name,body,owner=1001)
    exact_file(home/'.hermes/auth.json',auth,owner=1001)
    base.chmod(0o555);base.parent.chmod(0o555)
    source_record=json.loads(Path(str(BOOTSTRAP)+'.source.json').read_bytes())
    raw['code'].update(source=str(BOOTSTRAP),files=source_record['files'],executable_files=source_record['executable_files'])
    raw['private_launch']['profile']['source']=str(root/'profiles-offline-base/quantlab')
    raw['private_launch']['profile']['files']={member.name:hashlib.sha256(member.read_bytes()).hexdigest() for member in base.iterdir()}
    etc=saved/'etc-approved38';etc.mkdir(mode=0o750);os.chown(etc,0,1001)
    for name in ('launch-plan-approvals','launch-plans','heating-github-guard'):(etc/name).mkdir(mode=0o755)
    helpers['json_file'](etc/'host-policy.json',raw,0o640)
    exact_file(etc/'launch-plan-issuer.json',(root/'etc-approved38/launch-plan-issuer.json').read_bytes(),mode=0o640)
    (saved/'private-routing-diagnostic15').mkdir(mode=0o700);os.chown(saved/'private-routing-diagnostic15',1001,1001);(saved/'fake-guard').mkdir()
    for relative in ('.hermes/hermes-agent','.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu'):
        target=home/relative;target.mkdir(parents=True,exist_ok=True);os.chown(target,1001,1001)
    # Bind the exact reconciliation recipe as part of the same runtime composition.
    for member in (Path(__file__).resolve(),Path(__file__).with_name('offline_pilot.py').resolve()):cfg['files'][str(member)]=hashlib.sha256(member.read_bytes()).hexdigest()
    body=(json.dumps(cfg,sort_keys=True,separators=(',',':'))+'\n').encode();exact_file(new_composition,body,mode=0o444)
    sha=hashlib.sha256(body).hexdigest()
    helpers['json_file'](output/'input-proof.json',{'original_sha256':before,'composition_sha256':sha,'runtime_commit':source_record['source_commit'],'fixture_only':True,'real_credentials_copied':False,'preparation_reconciled_without_recollection':True,'model_calls':0,'real_queue_modified':False})
    tls=output/'tls';tls.mkdir(mode=0o700)
    q=subprocess.run(['/usr/bin/openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=inference-api.nousresearch.com','-addext','subjectAltName=DNS:inference-api.nousresearch.com','-addext','basicConstraints=critical,CA:TRUE','-keyout',str(tls/'key.pem'),'-out',str(tls/'cert.pem')],capture_output=True,timeout=15)
    need(q.returncode==0,'fixture_certificate_creation_failed');(tls/'key.pem').chmod(0o600)
    exact_file(output/'hosts',b'127.0.0.1 localhost inference-api.nousresearch.com\n::1 localhost\n',mode=0o444)
    need(helpers['snapshot_live'](root)==before,'original_changed_during_reconciliation')
    return sha



def synthetic_credential_after_delay(previous,now):
    # These unsigned fixture-only credentials have no external authority. A real
    # Nous key can never enter this function or be refreshed by this recipe.
    token=previous['providers']['nous']['agent_key'];header,payload,signature=token.split('.')
    decode=lambda part:json.loads(base64.urlsafe_b64decode(part+'='*((-len(part))%4)))
    claims=decode(payload)
    need(decode(header)=={'alg':'HS256','typ':'JWT'} and signature=='Zml4dHVyZQ'
         and set(claims)=={'sub','scope','exp'} and claims['sub']=='herdr-offline-fixture','synthetic_fixture_credential_required')
    claims['exp']=int(now)+7200
    encode=lambda value:base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
    fresh=header+'.'+encode(claims)+'.'+signature
    return ({'id':'ab19ef','source':'device_code','credential_type':'oauth',
             'agent_key':fresh,'access_token':fresh,'scope':claims['scope']},fresh,claims['exp'])


def renewed_synthetic_store(previous,now):
    entry,fresh,expiry=synthetic_credential_after_delay(previous,now)
    helper=runpy.run_path(str(BOOTSTRAP/'deploy/herdr/existing_credential_snapshot.py'))
    store=helper['minimal_store'](entry,fresh)
    return json.dumps(store,sort_keys=True).encode(),expiry


def renew_synthetic_before_first_cycle(composition_path,composition_sha,output,new_composition):
    need(os.geteuid()==0 and output==Path('/var/lib/herdr-ordinary-offline-a0c5371-20261028'),'exact_root_fixture_required')
    sys.path.insert(0,str(BOOTSTRAP));from herdr.operation_readiness import load_composition
    cfg=load_composition(composition_path,composition_sha);root=Path(cfg['runtime']['root'])
    helpers=runpy.run_path(str(Path(__file__).with_name('offline_pilot.py')));before=helpers['snapshot_live'](root)
    need(not (output/'isolated-private.log').exists() and not (output/'preparation-completed.json').exists(),'first_inner_cycle_already_started')
    saved=output/'root';home=saved/'home-diagnostic15/agentops';base=saved/'profiles-offline-base/quantlab'
    for home_path in (home,root/'home-diagnostic15/agentops'):
        need(not list((home_path/'.local/state/herdr-policy-approved38').glob('work-budget/*/events.jsonl')),'economic_admission_already_started')
    old=(base/'auth.json').read_bytes();body,expiry=renewed_synthetic_store(json.loads(old),time.time())
    paths=[(base/'auth.json',0,0o444),(home/'.hermes/auth.json',1001,0o600),(home/'.hermes/profiles/quantlab/auth.json',1001,0o600)]
    for path,owner,mode in paths:exact_file(path,old,owner=owner,mode=mode)
    helpers['json_file'](output/'synthetic-credential-refresh-intent.json',{'at_epoch':time.time(),'previous_auth_sha256':hashlib.sha256(old).hexdigest(),'new_auth_sha256':hashlib.sha256(body).hexdigest(),'fixture_only':True,'external_http_requests':0,'automatic_retry_allowed':False})
    # The outer fixture directory is root-only; no worker has been admitted.
    def replace(path,previous,content,mode,owner=0):
        need(path.read_bytes()==previous and path.is_file() and not path.is_symlink(),'retained_fixture_changed')
        temporary=path.with_name('.synthetic-ready-'+__import__('uuid').uuid4().hex)
        exact_file(temporary,content,mode=mode,owner=owner);os.replace(temporary,path)
    for path,owner,mode in paths:replace(path,old,body,mode,owner)
    policy=saved/'etc-approved38/host-policy.json';old_policy=policy.read_bytes();raw=json.loads(old_policy)
    raw['private_launch']['profile']['files']['auth.json']=hashlib.sha256(body).hexdigest()
    replace(policy,old_policy,(json.dumps(raw,sort_keys=True,separators=(',',':'))+'\n').encode(),0o640)
    for member in (Path(__file__).resolve(),Path(__file__).with_name('offline_pilot.py').resolve()):cfg['files'][str(member)]=hashlib.sha256(member.read_bytes()).hexdigest()
    new_body=(json.dumps(cfg,sort_keys=True,separators=(',',':'))+'\n').encode();exact_file(new_composition,new_body,mode=0o444)
    sha=hashlib.sha256(new_body).hexdigest()
    need(helpers['snapshot_live'](root)==before,'original_changed_during_fixture_clock_binding')
    helpers['json_file'](output/'synthetic-credential-ready.json',{'composition_sha256':sha,'credential_valid_until_epoch':expiry,'fixture_only':True,'original_sha256':before,'external_http_requests':0,'first_inner_cycle_not_started':True})
    return sha


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--composition',type=Path,required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--new-composition',type=Path,required=True);parser.add_argument('--renew-synthetic-before-first-cycle',action='store_true');args=parser.parse_args()
    action=renew_synthetic_before_first_cycle if args.renew_synthetic_before_first_cycle else complete
    sha=action(args.composition,args.sha256,args.output,args.new_composition)
    print(json.dumps({'retained_preparation_reconciled':True,'composition':str(args.new_composition),'sha256':sha,'native_cycle_not_yet_started':True,'model_calls':0}),flush=True)


if __name__=='__main__':main()
