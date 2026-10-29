"""One approved ordinary run; static preparation and auth precede admission."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, re, ssl, subprocess, sys, time, urllib.request
def _readiness():
    # Do not initialize herdr from the operations bundle. The native worker's
    # complete package is loaded from the independently pinned runtime C.
    import importlib.util
    name='_herdr_operations_readiness'
    if name not in sys.modules:
        path=Path(__file__).resolve().parents[2]/'herdr/operation_readiness.py'
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        spec.loader.exec_module(module)
    return sys.modules[name]


# Set only after validating the protected composition in configure().
R=H=C=STORE=None
P=MODEL=OLD_MODEL=TASK=BASE=None
STOP_FLOOR=START_GUARD=REQUIRED_CREDENTIAL_SECONDS=None
QUEUE_DIRS=('done','durable-children','blocked','running','pending','logs','attempts','failed','verification','results')
COMPOSITION=None


def configure(composition):
    global R,H,C,P,MODEL,OLD_MODEL,TASK,STORE,BASE,STOP_FLOOR,START_GUARD,REQUIRED_CREDENTIAL_SECONDS,COMPOSITION
    readiness=_readiness();Lifetimes=readiness.Lifetimes;require=readiness.require
    runtime, pilot = composition['runtime'], composition['pilot']
    require(set(runtime)=={'root','home','code','python','sdk'}, 'runtime_schema')
    require(set(pilot)=={'task_id','model','previous_model','base_commit','max_model_calls','max_cost_microusd','administrator_window_seconds'}, 'pilot_schema')
    require(pilot['max_model_calls']==62 and pilot['max_cost_microusd']==0 and pilot['administrator_window_seconds']==540000,
            'approved_economic_and_administrator_scope_changed')
    require(pilot['task_id']=='issue77-validation-repair-20261026' and pilot['model']=='meituan/longcat-2.0:free', 'approved_pilot_changed')
    R,H,C = (Path(runtime[k]) for k in ('root','home','code'))
    require(all(p.is_absolute() and '..' not in p.parts for p in (R,H,C)), 'runtime_paths')
    require(runtime['python']=='/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11' and runtime['sdk']=='/opt/herdr/releases/p0-5035d92-test/hermes','unreviewed_shared_runtime')
    P=runtime['python'];MODEL=pilot['model'];OLD_MODEL=pilot['previous_model'];TASK=pilot['task_id'];BASE=pilot['base_commit']
    STORE=H/'.local/state/herdr-policy-approved38'
    STOP_FLOOR=composition['capacity']['floor'];START_GUARD=composition['capacity']['start_guard']
    require(STOP_FLOOR==9663676416 and START_GUARD==134217728,'approved_capacity_gate_changed')
    life=Lifetimes(**composition['lifetimes'])
    require(life.work_seconds==1800 and life.grant_seconds==2700 and life.preparation_seconds==600 and life.cleanup_seconds==300,
            'approved_execution_lifetimes_changed')
    REQUIRED_CREDENTIAL_SECONDS=life.credential_seconds()
    COMPOSITION=composition


def drop():
    os.setgroups([]);os.setgid(1001);os.setuid(1001)

def save(path,value,mode=0o600,owner=0):
    temporary=path.with_suffix(path.suffix+'.new')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,sort_keys=True,separators=(',',':'))
            stream.flush();os.fsync(stream.fileno())
        os.chmod(temporary,mode);os.chown(temporary,owner,1001)
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()

def once(path,value):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(value,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())

def admin_deadline():
    values={}
    for node in ast.parse(Path('/usr/local/sbin/herdr-admin48').read_text()).body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('FROM','UNTIL'):
            values[node.targets[0].id]=ast.literal_eval(node.value)
    approval=json.loads((R/'approved38-human-approval.json').read_bytes())
    assert values['UNTIL']-values['FROM']==540000 and values['UNTIL']==approval['root_until_epoch']
    assert time.time()+1200<values['UNTIL'],'complete bounded unit must fit original administrator window'
    return values['UNTIL']

def original_budget():
    paths=list((H/'.local/state/herdr-policy-approved35/work-budget').glob('*/events.jsonl'))
    assert len(paths)==1
    return hashlib.sha256(paths[0].read_bytes()).hexdigest()

def check():
    assert os.geteuid()==0
    admin_deadline()
    prepared=json.loads((R/'approved38-source-and-scripts-prepared.json').read_bytes())
    for name,sha in prepared['files'].items():
        path=C/name;info=path.lstat()
        assert info.st_uid==0 and not info.st_mode&0o222 and info.st_nlink==1
        assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    for name,sha in prepared['scripts'].items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest()==sha
    assert original_budget()==prepared['previous_budget_sha256']
    previous37=list((H/'.local/state/herdr-policy-approved37/work-budget').glob('*/events.jsonl'));assert len(previous37)==1 and hashlib.sha256(previous37[0].read_bytes()).hexdigest()==prepared['previous37_budget_sha256']
    assert hashlib.sha256((R/'resume-task-reviewed-approved38.json').read_bytes()).hexdigest()==prepared['task_seed_sha256']
    assert not list(STORE.glob('work-budget/*/events.jsonl'))
    assert not (R/'approved38-unit-start-intent.json').exists()
    assert subprocess.check_output(['/usr/bin/systemctl','show','herdr-taskgraph77-approved35.service','--property=MainPID','--value'],text=True).strip()=='0'
    def git(args):
        return subprocess.check_output(['/usr/bin/git',*args],cwd=H/'worktrees/pilot/workspace',preexec_fn=drop,env={'HOME':str(H),'PATH':'/usr/bin:/bin'},text=True).strip()
    assert git(['rev-parse','HEAD'])==BASE and not git(['status','--porcelain'])
    fs=os.statvfs('/');assert fs.f_bavail*fs.f_frsize>=STOP_FLOOR+START_GUARD
    approval=json.loads((R/'approved38-human-approval.json').read_bytes())
    assert approval['approved'] and approval['max_additional_model_calls']==62 and approval['model']==MODEL and approval['max_cost_microusd']==0
    return prepared

def public_model_readiness():
    from decimal import Decimal
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    with opener.open('https://inference-api.nousresearch.com/v1/models',timeout=10) as response:
        assert response.status==200
        raw=response.read(2097153);assert len(raw)<=2097152
    rows=[row for row in json.loads(raw)['data'] if row.get('id')==MODEL]
    assert len(rows)==1
    selected=rows[0]
    for key in ('prompt','completion','input_cache_read'):
        price=selected['pricing'].get(key,'0')
        assert type(price) is str and re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',price) and Decimal(price)==0
    assert selected['context_length']>=557056
    assert selected['top_provider']['max_completion_tokens']>=32768
    assert {'tools','max_tokens'}<=set(selected['supported_parameters'])
    proof={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'model':MODEL,'selected_row_sha256':hashlib.sha256(json.dumps(selected,sort_keys=True).encode()).hexdigest(),'pricing':selected['pricing'],'context_length':selected['context_length'],'authenticated':False,'model_calls':0,'max_cost_microusd':0}
    once(R/('approved38-public-model-readiness-'+str(time.time_ns())+'.json'),proof)
    return proof

def prepare_queue():
    queue=H/'.local/state/agent-stack/tasks'
    receipt=R/'approved38-queue-prepared.json'
    if receipt.exists():
        assert json.loads(receipt.read_bytes())['fresh_identity']==json.loads((R/'same-identity-approved38.json').read_bytes())['identity']
        return queue
    seed_path=R/'resume-task-reviewed-approved38.json'
    prepared_path=R/'approved38-source-and-scripts-prepared.json'
    seed_bytes=seed_path.read_bytes()
    prepared=json.loads(prepared_path.read_bytes())
    assert prepared['task_seed_sha256']==hashlib.sha256(seed_bytes).hexdigest()
    task=json.loads(seed_bytes)
    assert task['model']==MODEL and task['fencing_token']==json.loads((R/'same-identity-approved38.json').read_bytes())['identity']['fencing_token']
    assert queue.resolve(strict=True)==queue
    preserved=R/'approved37-original-queue-preserved-before-approved38'
    assert not preserved.exists()
    os.rename(queue,preserved)
    queue.mkdir(mode=0o700);os.chown(queue,1001,1001)
    for name in QUEUE_DIRS:
        path=queue/name;path.mkdir(mode=0o700);os.chown(path,1001,1001)
    now=datetime.now(timezone.utc).isoformat()
    task['attempt_started_at']=task['dispatch_claimed_at']=now
    save(seed_path,task,0o600,1001)
    pending=queue/'pending'/(TASK+'.json')
    save(pending,task,0o600,1001)
    actual=seed_path.read_bytes()
    assert pending.read_bytes()==actual
    prepared['task_seed_sha256']=hashlib.sha256(actual).hexdigest()
    save(prepared_path,prepared,0o444)
    save(receipt,{'original_queue':str(preserved),'fresh_identity':json.loads((R/'same-identity-approved38.json').read_bytes())['identity'],'model_calls':0})
    return queue

def prepare_auth():
    # The fresh login is maintained only by the official SDK outside this run.
    # This child can select an existing key but cannot contact any network.
    import uuid,stat
    output=Path('/dev/shm')/('herdr38-existing-auth-'+uuid.uuid4().hex)
    helper=Path(__file__).with_name('existing_credential_snapshot.py')
    result=subprocess.run([P,'-I','-B',str(helper),'--snapshot-existing-login',str(output),'--required-validity-seconds',str(REQUIRED_CREDENTIAL_SECONDS)],preexec_fn=drop,
        env={'HOME':'/home/agentops','PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},cwd='/home/agentops',capture_output=True,text=True,timeout=65)
    save(R/'approved38-current-existing-auth-child-status.json',{'returncode':result.returncode,'private_snapshot':str(output),'auth_http_requests':0,'model_calls':0},0o400)
    assert result.returncode==0,'existing authentication unavailable; no renewal or model call attempted'
    public=json.loads(result.stdout.splitlines()[-1])
    assert public['snapshot_ready'] and public['snapshot_selection_verified'] and public['refresh_material_excluded'] and public['original_login_files_unchanged']
    def private_file(name):
        path=output/name;info=path.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid==1001 and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1 and 0<info.st_size<1048576
        return path.read_bytes()
    info=json.loads(private_file('auth-info.json'));body=private_file('auth.json');store=json.loads(body)
    assert set(store['providers'])=={'nous'} and set(store['credential_pool'])=={'nous'}
    def no_refresh(value):
        if isinstance(value,dict):return all('refresh' not in k.lower() and no_refresh(v) for k,v in value.items())
        if isinstance(value,list):return all(no_refresh(v) for v in value)
        return True
    assert no_refresh(store) and info['credential_valid_until_epoch']-time.time()>=REQUIRED_CREDENTIAL_SECONDS
    key=store['providers']['nous']['agent_key']
    assert hashlib.sha256(key.encode()).hexdigest()==info['expected_api_key_sha256']
    target=R/'approved38-current-existing-auth.json';assert not target.exists()
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    with os.fdopen(fd,'wb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
    auth={k:v for k,v in info.items() if k!='expected_api_key_sha256'}
    assert auth['standard_renewal_performed'] is False and auth['auth_httpx_requests']==0 and auth['model_calls_performed']==0
    save(R/'approved38-auth-existing-prepared.json',auth,0o400)
    return auth

def prepare_profile(auth):
    profile=R/'profiles-approved38-final/quantlab'
    raw=json.loads((R/'etc-approved38/host-policy.json').read_bytes())
    if not profile.exists():
        source=Path(raw['private_launch']['profile']['source'])
        profile.mkdir(parents=True,mode=0o755)
        for path in source.iterdir():
            assert path.is_file() and not path.is_symlink()
            body=(R/'approved38-current-existing-auth.json').read_bytes() if path.name=='auth.json' else path.read_bytes().replace(OLD_MODEL.encode(),MODEL.encode())
            fd=os.open(profile/path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
            with os.fdopen(fd,'wb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
        profile.chmod(0o555);profile.parent.chmod(0o555)
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in profile.iterdir()}
    assert MODEL.encode() in (profile/'config.yaml').read_bytes()
    sys.path.insert(0,str(C))
    from herdr.policy_launch import ApprovedProfile
    from herdr.work_budget_configuration import parse_allocation
    from herdr.evidence import binding
    approved=ApprovedProfile('quantlab',profile,files)
    end=datetime.fromtimestamp(auth['credential_valid_until_epoch'],timezone.utc).isoformat()
    raw['private_launch']['profile']={'name':'quantlab','source':str(profile),'files':files}
    raw['private_launch']['credential_approval'].update(profile_sha256=approved.identity['manifest_sha256'],valid_until=end)
    raw['grant_ttl_seconds']=2700
    for template in raw['templates'].values():
        template['issued_at']=datetime.now(timezone.utc).isoformat();template['expires_at']=end
    plan=next(iter(raw['work_contracts']['plans'].values()))
    plan['budget']['allocation']['authorization_reference']=hashlib.sha256((R/'approved38-human-approval.json').read_bytes()).hexdigest()
    assert plan['budget']['allocation']['limits']['max_elapsed_ms']==1800000
    save(R/'approved38-model-window.json',{'max_elapsed_ms':1800000,'root_until_epoch':admin_deadline(),'clock_starts':'canonical_host_admission'},0o644)
    allocation=parse_allocation(plan['budget']['allocation'])
    plan['budget_reference']=allocation.hash;plan['planning']['team']['budget_reference']=allocation.hash
    task=json.loads((R/'resume-task-reviewed-approved38.json').read_bytes())
    save(R/'same-identity-approved38.json',{'identity':binding(task),'approval_sha256':hashlib.sha256((R/'approved38-human-approval.json').read_bytes()).hexdigest()},0o644)
    return raw

def publish(raw):
    from herdr.evidence import digest
    save(R/'etc-approved38/host-policy.json',raw,0o640)
    issuer=json.loads((R/'etc-approved38/launch-plan-issuer.json').read_bytes())
    issuer['host_policy_sha256']=digest(raw)
    save(R/'etc-approved38/launch-plan-issuer.json',issuer,0o640)

def preflight(mode):
    result=subprocess.run(['/usr/bin/unshare','--mount','--fork',P,'-I','-B',str(Path(__file__).parent/'native_pilot/preflight.py'),COMPOSITION['_path'],COMPOSITION['_sha256'],mode],capture_output=True,text=True,timeout=150)
    path=R/('approved38-preflight-'+mode+'-outer-private.log');path.write_text(result.stdout+result.stderr);path.chmod(0o600)
    assert result.returncode==0,'pre-admission readiness denied: '+mode
    return json.loads((R/('approved38-preflight-'+mode+'-private.json')).read_bytes())

def bind_remaining_window(raw):
    from herdr.work_budget_configuration import parse_allocation
    plan=next(iter(raw['work_contracts']['plans'].values()))
    duration=min(plan['budget']['allocation']['limits']['max_elapsed_ms'],1800000,int((admin_deadline()-time.time()-300)*1000))
    assert duration>=900000, 'minimum fifteen-minute work window and cleanup must fit'
    plan['budget']['allocation']['limits']['max_elapsed_ms']=duration
    allocation=parse_allocation(plan['budget']['allocation'])
    plan['budget_reference']=allocation.hash;plan['planning']['team']['budget_reference']=allocation.hash
    save(R/'approved38-model-window.json',{'max_elapsed_ms':duration,'root_until_epoch':admin_deadline(),'clock_starts':'canonical_host_admission'},0o644)
    publish(raw)
    return duration

def renewed_pending_task(seed,pending,now):
    import copy
    assert type(seed)is dict and type(pending)is dict and seed==pending
    assert type(now)is str and datetime.fromisoformat(now).tzinfo is not None
    assert seed['id']==TASK and seed['model']==MODEL and seed['fencing_token']==8
    task=copy.deepcopy(seed)
    task['attempt_started_at']=task['dispatch_claimed_at']=now
    before={k:v for k,v in seed.items() if k not in ('attempt_started_at','dispatch_claimed_at')}
    after={k:v for k,v in task.items() if k not in ('attempt_started_at','dispatch_claimed_at')}
    assert before==after
    return task

def refresh_pending_start_clock():
    from herdr.evidence import binding
    assert not list(STORE.glob('work-budget/*/events.jsonl')) and not (R/'approved38-unit-start-intent.json').exists()
    seed_path=R/'resume-task-reviewed-approved38.json'
    pending=H/'.local/state/agent-stack/tasks/pending'/(TASK+'.json')
    seed_bytes=seed_path.read_bytes();pending_bytes=pending.read_bytes();assert seed_bytes==pending_bytes
    seed=json.loads(seed_bytes);task=renewed_pending_task(seed,json.loads(pending_bytes),datetime.now(timezone.utc).isoformat())
    assert binding(seed)==binding(task)==json.loads((R/'same-identity-approved38.json').read_bytes())['identity']
    prepared_path=R/'approved38-source-and-scripts-prepared.json';prepared=json.loads(prepared_path.read_bytes())
    assert prepared['task_seed_sha256']==hashlib.sha256(seed_bytes).hexdigest()
    save(R/'approved38-before-admission-clock.json',{'task':seed,'prepared_metadata':prepared},0o400)
    assert seed_path.read_bytes()==seed_bytes and pending.read_bytes()==pending_bytes
    save(seed_path,task,0o600,1001);save(pending,task,0o600,1001)
    actual=seed_path.read_bytes();assert pending.read_bytes()==actual and json.loads(actual)==task
    prepared['task_seed_sha256']=hashlib.sha256(actual).hexdigest()
    prepared['admission_clock_only_fields']=['attempt_started_at','dispatch_claimed_at']
    save(prepared_path,prepared,0o444)

def prepare_existing():
    prepared=check()
    sys.path.insert(0,str(C))
    from herdr.work_configuration import _reviewed_graph
    raw=json.loads((R/'etc-approved38/host-policy.json').read_bytes())
    task=json.loads((R/'resume-task-reviewed-approved38.json').read_bytes())
    for definition in raw['work_contracts']['plans'].values():_reviewed_graph(definition,task)
    public_model_readiness();prepare_queue()
    auth=prepare_auth();raw=prepare_profile(auth);publish(raw)
    derived=preflight('derive');ref=derived['credential_ref']
    for template in raw['templates'].values():
        template['credential_refs']=[ref]
        for route in template['provider_routes']:
            assert route['provider']=='nous';route['credential_refs']=[ref]
    publish(raw)
    proof=preflight('require-bound')
    assert proof['selected_credential_matches_grant'] and proof['actual_guard_credential_binding_passed'] and proof['host_transport_credential_matches_sdk'] and proof['result_slot_checked']
    refresh_pending_start_clock()
    duration=bind_remaining_window(raw)
    assert not list(STORE.glob('work-budget/*/events.jsonl'))
    assert original_budget()==prepared['previous_budget_sha256']
    admin_deadline()
    assert os.statvfs('/').f_bavail*os.statvfs('/').f_frsize>=STOP_FLOOR+START_GUARD
    return prepared,duration

def main():
    prepared,duration=prepare_existing()
    once(R/'approved38-unit-start-intent.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'automatic_retry_allowed':False,'budget_admission':'ordinary_host_work_factory'})
    command=['/usr/bin/systemd-run','--unit=herdr-taskgraph77-approved38','--property=RuntimeMaxSec='+str(min(2100,int(admin_deadline()-time.time()-30))),'--property=TimeoutStopSec=15','--property=KillMode=control-group','--property=Restart=no','/usr/bin/unshare','--mount','--pid','--fork','--mount-proc',P,'-I','-B',str(Path(__file__).parent/'native_pilot/init.py'),COMPOSITION['_path'],COMPOSITION['_sha256']]
    result=subprocess.run(command,capture_output=True,text=True,timeout=20)
    save(R/'approved38-start-result.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr},0o600)
    assert result.returncode==0,'inspect original service start; never repeat'
    print(json.dumps({'started':True,'unit':'herdr-taskgraph77-approved38.service','source_commit':prepared['source_commit'],'model':MODEL,'budget_admission':'ordinary_host_work_factory','max_model_calls':62,'max_cost_microusd':0,'max_seconds_from_canonical_admission':duration//1000,'previous_unknown_reservation_held':True,'automatic_retry_allowed':False}),flush=True)

def cli():
    import argparse
    readiness=_readiness();load_composition=readiness.load_composition;Lifetimes=readiness.Lifetimes;capacity=readiness.capacity
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--composition',required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--offline-proof')
    parser.add_argument('--offline-sha256')
    args=parser.parse_args()
    value=load_composition(args.composition,args.sha256)
    configure(value)
    COMPOSITION['_path']=str(Path(args.composition));COMPOSITION['_sha256']=args.sha256
    Lifetimes(**value['lifetimes']).require_admin(admin_deadline()-time.time())
    prepared=check()
    fs=os.statvfs('/')
    status=capacity(fs.f_bavail*fs.f_frsize,**value['capacity'])
    assert status['ready'], 'capacity_admission_denied'
    if args.check:
        print(json.dumps({'composition_verified':True,'source_commit':prepared['source_commit'],
                          'capacity':status,'required_credential_seconds':REQUIRED_CREDENTIAL_SECONDS,
                          'model_calls':0,'admission_performed':False}))
    else:
        assert args.offline_proof and args.offline_sha256, 'full_ordinary_offline_acceptance_required'
        body=readiness.read_protected(args.offline_proof)
        assert hashlib.sha256(body).hexdigest()==args.offline_sha256, 'offline_proof_changed'
        readiness.require_offline_acceptance(json.loads(body),args.sha256,now_epoch=time.time())
        main()

if __name__=='__main__':cli()
