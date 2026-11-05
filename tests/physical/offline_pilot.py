"""Bounded ordinary-worker acceptance in a private mount/PID/network namespace.

--prepare-clean-inputs CASE --case-sha256 SHA --run-token NONCE is a
unprivileged, data-only preparation mode for a fresh synthetic case. It does
not invoke this historical pilot, allocate a budget or establish physical PASS.

Only the external Nous responses are supplied by a local TLS fixture. No real
login or GitHub credentials enter this environment. Passing this proof is local
handoff acceptance, not inference, publication, final task DONE or rollout.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import http.server
import importlib.util
import json
import os
import runpy
import shutil
import signal
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time

P='/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11'
SDK=Path('/opt/herdr/releases/p0-5035d92-test/hermes')
TASK='issue77-validation-repair-20261026'
QUEUES=('done','durable-children','blocked','running','pending','logs','attempts','failed','verification','results')


def need(ok,reason):
    if not ok:raise RuntimeError(reason)


def write(path,body,mode=0o600,owner=0):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as stream:
        stream.write(body);stream.flush();os.fsync(stream.fileno())
    os.chown(path,owner,1001)


def json_file(path,value,mode=0o600,owner=0):
    write(path,(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode(),mode,owner)


def user_tree(path):
    for member in [path,*path.rglob('*')]:
        need(not member.is_symlink(),'fixture_unexpected_link')
        os.chown(member,1001,1001)


def safe_profile_environment(body):
    # This frozen pilot permits only a browser executable hint, never provider,
    # authentication, loader or process-control overrides. Drop comments.
    fields={}
    for line in body.decode('utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        key,separator,value=line.partition('=')
        need(separator and key=='AGENT_BROWSER_EXECUTABLE_PATH' and key not in fields,
             'fixture_profile_environment_field_denied')
        need(value=='/home/agentops/.local/bin/chromium-with-playwright-libs',
             'fixture_profile_environment_value_denied')
        fields[key]=value
    return ''.join(key+'='+value+'\n' for key,value in sorted(fields.items())).encode()



def frozen_profile_members(source, expected):
    # Use the already approved manifest, not a second hand-written inventory.
    need(isinstance(expected,dict) and set(expected)=={p.name for p in source.iterdir()},'fixture_profile_inventory_changed')
    members=[]
    for name,sha in sorted(expected.items()):
        need(name not in {'.','..'} and '/' not in name and name,'fixture_profile_name_denied')
        p=source/name;info=p.lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'fixture_profile_member')
        # The real login is never copied or exported by this fixture.
        if name!='auth.json':need(hashlib.sha256(p.read_bytes()).hexdigest()==sha,'fixture_profile_source_changed')
        members.append(p)
    return members


def snapshot_stamp(info):
    # Reading can legitimately update atime. It cannot change these identity,
    # content-version or permission fields without invalidating the snapshot.
    return (info.st_dev,info.st_ino,info.st_uid,info.st_gid,info.st_mode,info.st_nlink,
            info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def read_native_snapshot(source, *, owner=1001):
    fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_NOATIME)
    try:
        opened=os.fstat(fd)
        need(stat.S_ISREG(opened.st_mode) and opened.st_uid==owner and opened.st_nlink==1
             and 0<opened.st_size<33554432,'native_binary_snapshot_denied')
        data=bytearray()
        while len(data)<opened.st_size:
            part=os.read(fd,min(1048576,opened.st_size-len(data)))
            need(bool(part),'native_snapshot_shortened');data.extend(part)
        need(not os.read(fd,1) and snapshot_stamp(opened)==snapshot_stamp(os.fstat(fd)),'native_snapshot_changed')
        return bytes(data)
    finally:os.close(fd)


def snapshot_live(root):
    home=root/'home-diagnostic15/agentops'
    paths=[root/'resume-task-reviewed-approved38.json',root/'approved38-source-and-scripts-prepared.json',
           root/'approved38-human-approval.json',root/'etc-approved38/host-policy.json',
           home/'.local/state/agent-stack/tasks/pending'/(TASK+'.json')]
    for version in (35,37):paths.extend((home/f'.local/state/herdr-policy-approved{version}/work-budget').glob('*/events.jsonl'))
    need(len(paths)==7,'original_evidence_set_changed')
    return {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def prepare_fixture(composition_path, composition_sha, output):
    need(os.geteuid()==0,'administrator_required')
    helpers=runpy.run_path(str(Path(__file__).resolve().parents[2]/'deploy/herdr/approved_pilot.py'))
    readiness=helpers['_readiness']();cfg=readiness.load_composition(composition_path,composition_sha)
    root=Path(cfg['runtime']['root']);home=root/'home-diagnostic15/agentops';code=Path(cfg['runtime']['code'])
    before=snapshot_live(root)
    need(not list((home/'.local/state/herdr-policy-approved38').glob('work-budget/*/events.jsonl'))
         and not (root/'approved38-unit-start-intent.json').exists(),'original_attempt_already_started')
    output.mkdir(mode=0o700)
    copied=output/'root';copied.mkdir(mode=0o755)
    test_home=copied/'home-diagnostic15/agentops'
    for directory in ('.local/bin','.local/state/herdr','.local/state/agent-stack/tasks','.config/gh','.config/herdr',
                      '.hermes/profiles/quantlab','worktrees/pilot'):
        (test_home/directory).mkdir(parents=True,exist_ok=True,mode=0o700)
    for name in ('herdr','hermes'):
        source=home/'.local/bin'/name;info=source.lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'native_fixture_binary_alias')
        data=read_native_snapshot(source)
        if name=='herdr':need(data[:4]==b'\x7fELF','native_binary_format_changed')
        if name=='hermes':need(b'coordinator_hermes_cli.py' in data and len(data)<512,'native_hermes_wrapper_changed')
        write(test_home/'.local/bin'/name,data,0o555,1001)
    # Original GitHub keys and host guard configuration are deliberately absent.
    (test_home/'.local/bin/gh').symlink_to('/usr/local/libexec/herdr-heating-guard/gh')
    detection=home/'.local/state/herdr/agent-detection'
    if detection.exists():shutil.copytree(detection,test_home/'.local/state/herdr/agent-detection',symlinks=True)
    workspace=test_home/'worktrees/pilot/workspace'
    shutil.copytree(home/'worktrees/pilot/workspace',workspace,symlinks=True,
                    ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','node_modules'))
    # A private original object database preserves the exact base commit; no
    # hardlinks, shared writable Git directories or alternate object stores.
    need(not (workspace/'.git/objects/info/alternates').exists(),'fixture_shared_git_objects')
    gh=test_home/'.local/bin/gh';gh.unlink();user_tree(test_home);gh.symlink_to('/usr/local/libexec/herdr-heating-guard/gh')
    for directory in QUEUES:(test_home/'.local/state/agent-stack/tasks'/directory).mkdir(mode=0o700);os.chown(test_home/'.local/state/agent-stack/tasks'/directory,1001,1001)
    task=json.loads((root/'resume-task-reviewed-approved38.json').read_bytes())
    need(task['fencing_token']==8 and task['attempts']==0 and task['attempt_id']==0,'fixture_task_identity_drift')
    now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    task['attempt_started_at']=task['dispatch_claimed_at']=now
    json_file(copied/'resume-task-reviewed-approved38.json',task,owner=1001)
    json_file(test_home/'.local/state/agent-stack/tasks/pending'/(TASK+'.json'),task,owner=1001)
    for name in ('same-identity-approved38.json','approved38-queue-prepared.json','coordinator_hermes_cli.py','approved38-watch.py'):
        shutil.copyfile(root/name,copied/name);(copied/name).chmod(0o444)
    for version in (35,37):
        src=home/f'.local/state/herdr-policy-approved{version}/work-budget'
        shutil.copytree(src,test_home/f'.local/state/herdr-policy-approved{version}/work-budget')
        user_tree(test_home/f'.local/state/herdr-policy-approved{version}')
    prepared=json.loads((root/'approved38-source-and-scripts-prepared.json').read_bytes())
    source_record=json.loads(Path(str(code)+'.source.json').read_bytes())
    prepared.update(files=source_record['files'],source_commit=source_record['source_commit'],source_path=str(code),
                    scripts={},task_seed_sha256=hashlib.sha256((copied/'resume-task-reviewed-approved38.json').read_bytes()).hexdigest())
    # The protected composition covers all versioned entrypoints. Historical
    # legacy script hashes remain in the untouched original preparation receipt.
    json_file(copied/'approved38-source-and-scripts-prepared.json',prepared,0o444)
    approval=json.loads((root/'approved38-human-approval.json').read_bytes())
    gate={}
    import ast
    for node in ast.parse(Path('/usr/local/sbin/herdr-admin48').read_bytes()).body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('FROM','UNTIL'):gate[node.targets[0].id]=ast.literal_eval(node.value)
    need(gate['UNTIL']-gate['FROM']==540000,'administrator_window_changed')
    approval['root_until_epoch']=gate['UNTIL'];approval['max_root_window_seconds']=540000
    json_file(copied/'approved38-human-approval.json',approval)
    raw=json.loads((root/'etc-approved38/host-policy.json').read_bytes())
    raw['code'].update(source=str(code),files=source_record['files'],executable_files=source_record['executable_files'])
    # A nonsecret, unsigned invoke token is accepted only by the isolated local
    # responder. It can never authorize a real Nous request.
    sys.path[:0]=[str(SDK),str(SDK/'venv/lib/python3.11/site-packages')]
    from hermes_cli import auth
    scope=auth.NOUS_INFERENCE_INVOKE_SCOPE
    encode=lambda obj:base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip('=')
    token=encode({'alg':'HS256','typ':'JWT'})+'.'+encode({'sub':'herdr-offline-fixture','exp':int(time.time())+7200,'scope':scope})+'.Zml4dHVyZQ'
    snapshot=runpy.run_path(str(code/'deploy/herdr/existing_credential_snapshot.py'))
    body=json.dumps(snapshot['minimal_store']({'id':'ab19ef','source':'device_code','credential_type':'oauth',
                      'agent_key':token,'access_token':token,'scope':scope},token),sort_keys=True).encode()
    source_profile=Path(raw['private_launch']['profile']['source'])
    base=copied/'profiles-offline-base/quantlab';base.mkdir(parents=True)
    for source in frozen_profile_members(source_profile,raw['private_launch']['profile']['files']):
        payload=body if source.name=='auth.json' else source.read_bytes().replace(b'meituan/longcat-2.5-preview:free',b'meituan/longcat-2.0:free')
        if source.name=='.env':payload=safe_profile_environment(payload)
        write(base/source.name,payload,0o444)
        write(test_home/'.hermes/profiles/quantlab'/source.name,payload,owner=1001)
    base.chmod(0o555);base.parent.chmod(0o555)
    write(test_home/'.hermes/auth.json',body,owner=1001)
    raw['private_launch']['profile']['source']=str(root/'profiles-offline-base/quantlab')
    raw['private_launch']['profile']['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in base.iterdir()}
    (copied/'etc-approved38').mkdir(mode=0o750);os.chown(copied/'etc-approved38',0,1001)
    for directory in ('launch-plan-approvals','launch-plans','heating-github-guard'):(copied/'etc-approved38'/directory).mkdir(mode=0o755)
    json_file(copied/'etc-approved38/host-policy.json',raw,0o640)
    shutil.copyfile(root/'etc-approved38/launch-plan-issuer.json',copied/'etc-approved38/launch-plan-issuer.json')
    (copied/'private-routing-diagnostic15').mkdir(mode=0o700);os.chown(copied/'private-routing-diagnostic15',1001,1001)
    (copied/'fake-guard').mkdir()
    json_file(output/'input-proof.json',{'original_sha256':before,'composition_sha256':composition_sha,
              'runtime_commit':source_record['source_commit'],'fixture_only':True,'real_credentials_copied':False,
              'model_calls':0,'real_queue_modified':False})
    need(snapshot_live(root)==before,'original_changed_during_fixture_preparation')
    return cfg,token


def mount(args):
    result=subprocess.run(['/usr/bin/mount',*map(str,args)],capture_output=True,timeout=20)
    need(result.returncode==0,'fixture_private_mount_failed')


def inner(composition_path,composition_sha,output):
    helpers=runpy.run_path(str(Path(__file__).resolve().parents[2]/'deploy/herdr/approved_pilot.py'))
    readiness=helpers['_readiness']();cfg=readiness.load_composition(composition_path,composition_sha)
    root=Path(cfg['runtime']['root']);code=Path(cfg['runtime']['code'])
    need(os.geteuid()==0 and [name for _,name in socket.if_nameindex()]==['lo'],'isolated_fixture_network_required')
    mount(['--make-rprivate','/'])
    mount(['--bind',output/'root',root])
    mount(['--bind',root/'home-diagnostic15','/home'])
    mount(['--bind',root/'fake-guard','/etc/herdr/heating-github-guard'])
    # Trust only the local provider responder inside this namespace. No host CA,
    # hosts file, global mount or production login is changed.
    mount(['-t','tmpfs','-o','mode=755,size=1048576','tmpfs','/etc/ssl'])
    Path('/etc/ssl/certs').mkdir()
    for target in ('/etc/ssl/cert.pem','/etc/ssl/certs/ca-certificates.crt'):
        Path(target).touch();mount(['--bind',output/'tls/cert.pem',target])
    mount(['--bind',output/'hosts','/etc/hosts'])
    result=subprocess.run(['/usr/sbin/ip','link','set','dev','lo','up'],capture_output=True,timeout=10)
    need(result.returncode==0,'fixture_loopback_unavailable')
    need(all(line.split()[1]!='00000000' for line in Path('/proc/net/route').read_text().splitlines()[1:]),'fixture_external_route_present')
    provider=runpy.run_path(str(Path(__file__).with_name('offline_provider.py')))
    workspace=Path('/home/agentops/worktrees/pilot/workspace')
    originals={name:(workspace/name).read_text() for name in provider['FILES']}
    response_fixture=provider['ProviderFixture'](originals)
    # Scope declarations are sourced from the frozen plan after host admission;
    # no independent review or functional acceptance is invented by this fixture.
    observations={'mock_http_requests':0,'errors':[]}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send_json(self,status,value):
            data=json.dumps(value,separators=(',',':')).encode()
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if self.path!='/v1/models':return self.send_json(404,{})
            return self.send_json(200,{'data':[{'id':'meituan/longcat-2.0:free','pricing':{'prompt':'0','completion':'0','input_cache_read':'0'},'context_length':1048576,'top_provider':{'max_completion_tokens':131072},'supported_parameters':['tools','max_tokens']}]})
        def do_POST(self):
            observations['mock_http_requests']+=1
            try:
                need(self.path=='/v1/chat/completions','fixture_http_path')
                size=int(self.headers.get('Content-Length','0'));need(0<size<=524288,'fixture_request_bound')
                bearer=self.headers.get('Authorization','')
                need(bearer.startswith('Bearer '),'fixture_authentication_header_required')
                claim=bearer[7:].split('.')[1];claims=json.loads(base64.urlsafe_b64decode(claim+'='*((-len(claim))%4)))
                need(claims.get('sub')=='herdr-offline-fixture','fixture_real_credential_denied')
                payload=json.loads(self.rfile.read(size))
                need(payload.get('model')=='meituan/longcat-2.0:free','fixture_model_changed')
                if response_fixture.turn==2:
                    reader="from pathlib import Path;import sys,json;sys.path[:0]=[sys.argv[1],sys.argv[1]+'/agent-stack/bin'];from agent_completion_evidence import store_for;from herdr.evidence import binding,digest;q=Path('/home/agentops/.local/state/agent-stack/tasks');t=json.loads((q/'running'/'issue77-validation-repair-20261026.json').read_bytes());p=store_for(q,t).read('plan',digest(binding(t)));print(json.dumps({'scope_policy':p.get('scope_policy')}))"
                    def drop():os.setgroups([]);os.setgid(1001);os.setuid(1001)
                    observed=subprocess.run([P,'-I','-B','-c',reader,str(code)],preexec_fn=drop,
                        capture_output=True,text=True,timeout=15,env={'PATH':'/usr/bin:/bin','HOME':'/home/agentops','LANG':'C.UTF-8'})
                    need(observed.returncode==0,'fixture_scope_plan_unavailable')
                    plan=json.loads(observed.stdout)
                    if plan.get('scope_policy') is not None:
                        policy=plan['scope_policy']
                        response_fixture.scope_claim={'version':1,'changed_groups':[{
                            'files':list(response_fixture.edits),'symbols':['metrics','validate'],'resources':[],
                            'acceptance_ids':policy['acceptance_ids'],'justification':'Predetermined offline transport/tool fixture only.'}],
                            'unrelated_changes':[],'unexpected_side_effects':[],'followups_not_implemented':[],
                            'shared_contract_changes':[],'verdict':'IN_SCOPE'}
                return self.send_json(200,response_fixture.answer(payload))
            except BaseException as error:
                observations['errors'].append(type(error).__name__)
                return self.send_json(400,{'error':{'type':'fixture_response_stopped'}})
    server=http.server.ThreadingHTTPServer(('127.0.0.1',443),Handler)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(str(output/'tls/cert.pem'),str(output/'tls/key.pem'))
    server.socket=context.wrap_socket(server.socket,server_side=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    helpers['configure'](cfg)
    # Function globals belong to runpy's dictionary, not this caller's wrapper.
    configured=helpers['configure'].__globals__
    configured['COMPOSITION']['_path']=str(composition_path);configured['COMPOSITION']['_sha256']=composition_sha
    configured['prepare_existing']()
    json_file(output/'preparation-completed.json',{'canonical_preparation_passed':True,'model_admission_not_yet_started':True,'external_authentication_http_requests':0})
    command=[P,'-I','-B',str(code/'deploy/herdr/native_pilot/init.py'),str(composition_path),composition_sha]
    log=(output/'native-private.log').open('xb')
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    passed=False
    try:
        # Resolve the observer's identity contract from the pinned worker code.
        sys.path.insert(0,str(code))
        deadline=time.monotonic()+780
        while process.poll() is None and time.monotonic()<deadline:
            queue=Path('/home/agentops/.local/state/agent-stack/tasks')
            result_path=queue/'results'/(TASK+'.json')
            expected=readiness.read_host_task_identity(root/'same-identity-approved38.json')
            try:
                task_path,task=readiness.observe_task(queue,TASK,expected)
            except readiness.SnapshotChanged:
                time.sleep(.05)
                continue
            waiting=(task_path.parent.name in ('running','blocked')
                     and task.get('attempt_state')=='verification_pending')
            if task_path.parent.name=='failed' or (task_path.parent.name=='blocked' and not waiting):
                raise RuntimeError('ordinary_fixture_worker_stopped')
            if (waiting and task.get('execution_session',{}).get('closed_at')
                    and result_path.exists() and result_path.stat().st_size):
                passed=True;break
            time.sleep(.2)
        need(passed and response_fixture.complete and not observations['errors'],'complete_ordinary_local_handoff_unavailable')
        json_file(output/'local-handoff-observed.json',{'ordinary_worker_used':True,'actual_sdk_used':True,'host_ipc_used':True,
                  'work_tools_verified':True,'validation_verified':True,'local_result_observed':True,
                  'fixture_only':True,'mock_provider_http_requests':observations['mock_http_requests'],
                  'external_provider_http_requests':0,'external_authentication_http_requests':0,
                  'composition_sha256':composition_sha,'checked_at_epoch':time.time(),
                  'final_task_done_claimed':False,'result_sha256':hashlib.sha256(result_path.read_bytes()).hexdigest()})
        return 0
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
        server.shutdown();server.server_close();log.close()
        json_file(output/'transport-observations.json',dict(observations,fixture_only=True,external_provider_http_requests=0))



# Fresh preparation is deliberately a data-only mode. The legacy pilot below
# still consumes its original protected composition; its authority is not reused.
def _closed_object(value, keys, reason):
    need(type(value) is dict and set(value) == set(keys), reason)


def _fixture_relative(name):
    from pathlib import PurePosixPath
    import re
    need(type(name) is str and len(name) <= 128
         and re.fullmatch(r'[A-Za-z0-9_./-]+', name) is not None,
         'clean_case_path_denied')
    path = PurePosixPath(name)
    need(not path.is_absolute() and path.as_posix() == name
         and all(part not in ('', '.', '..') and not part.startswith('.')
                 for part in name.split('/')),
         'clean_case_path_denied')
    return name


def read_clean_case(path, expected_sha256):
    import re
    need(type(expected_sha256) is str and re.fullmatch('[0-9a-f]{64}', expected_sha256),
         'clean_case_digest_required')
    path = Path(path).absolute()
    need(path.resolve(strict=True) == path and not path.is_symlink(),
         'clean_case_alias_denied')
    info = path.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
         and 0 < info.st_size <= 65536, 'clean_case_file_denied')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        # Windows 3.13 lstat reports creation time in ctime while fstat reports
        # change time. Compare each version through the same API; bind the
        # handle to the named file by every other stable identity field.
        cross_stamp = lambda value: snapshot_stamp(value)[:-1] if os.name=='nt' else snapshot_stamp(value)
        need(cross_stamp(info) == cross_stamp(before), 'clean_case_changed')
        raw = bytearray()
        while len(raw) <= 65536:
            part = os.read(fd, min(8192, 65537-len(raw)))
            if not part:
                break
            raw.extend(part)
        after, named = os.fstat(fd), path.lstat()
        need(snapshot_stamp(before) == snapshot_stamp(after)
             and snapshot_stamp(info) == snapshot_stamp(named)
             and cross_stamp(after) == cross_stamp(named) and len(raw) == before.st_size,
             'clean_case_changed')
    finally:
        os.close(fd)
    need(hashlib.sha256(raw).hexdigest() == expected_sha256, 'clean_case_digest_changed')
    def closed_pairs(pairs):
        value = {}
        for key, item in pairs:
            need(key not in value, 'clean_case_duplicate_field')
            value[key] = item
        return value
    case = json.loads(raw, object_pairs_hook=closed_pairs,
                      parse_constant=lambda value: need(False, 'clean_case_nonfinite'))
    _closed_object(case, ('schema_version', 'case_id', 'consumer', 'source_main',
                         'files', 'edits', 'check', 'limits'), 'clean_case_schema')
    need(case['schema_version'] == 'herdr-offline-clean-case-1'
         and case['case_id'] == 'arithmetic-v1'
         and case['consumer'] == 'github:Bbambaaamm/herdr'
         and case['source_main'] == '5fbabd5864d2f74f5c4658aa6e5f577967e88ffa',
         'clean_case_identity_denied')
    files, edits = case['files'], case['edits']
    need(type(files) is dict and 1 <= len(files) <= 16
         and type(edits) is dict and 1 <= len(edits) <= len(files),
         'clean_case_inventory_denied')
    total = 0
    for name, body in files.items():
        _fixture_relative(name)
        need(type(body) is str and 0 < len(body.encode()) <= 8192,
             'clean_case_content_bound')
        total += len(body.encode())
    need(total <= 32768, 'clean_case_content_bound')
    for name, body in edits.items():
        _fixture_relative(name)
        need(name in files and type(body) is str and 0 < len(body.encode()) <= 8192
             and body != files[name], 'clean_case_edit_denied')
    check = case['check']
    _closed_object(check, ('id', 'script', 'expected_baseline_exit',
                          'expected_baseline_stdout', 'expected_pass_stdout'),
                   'clean_case_check_schema')
    need(check['id'] == 'arithmetic' and type(check['script']) is str and check['script'] in files
         and check['script'] not in edits and check['script'].endswith('.py')
         and type(check['expected_baseline_exit']) is int
         and check['expected_baseline_exit'] == 1,
         'clean_case_check_denied')
    need(all(type(check[key]) is str and 0 < len(check[key]) <= 1024
             for key in ('expected_baseline_stdout', 'expected_pass_stdout'))
         and check['expected_baseline_stdout'] != check['expected_pass_stdout'],
         'clean_case_check_denied')
    expected_limits = {
        'max_external_model_calls': 0, 'max_external_auth_calls': 0,
        'max_external_github_calls': 0, 'max_cost_microusd': 0,
        'max_local_fixture_requests': 16, 'max_work_seconds': 900,
        'max_envelope_seconds': 1800, 'max_managed_children': 1,
    }
    need(type(case['limits']) is dict and case['limits'] == expected_limits
         and all(type(value) is int for value in case['limits'].values()),
         'clean_case_limits_denied')
    return case


def prepare_clean_inputs(path, expected_sha256, run_token):
    """Return a proposal, never queue state, policy, a grant or an allowance.

    Pure preparation neither consumes a historical Work nor creates authority.
    The approved physical envelope must still bind its own absolute deadlines,
    protected admission, immutable runtime, profile, grant and actual evidence.
    """
    import re
    need(type(run_token) is str and re.fullmatch('[0-9a-f]{32}', run_token),
         'clean_case_fresh_nonce_required')
    case = read_clean_case(path, expected_sha256)
    source = Path(__file__).resolve().parents[2]
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from herdr.security import (InvocationIdentity, canonical_json_bytes as canonical,
                                canonical_digest as digest)
    task_id = 'offline188-' + run_token
    workspace = '/home/agentops/worktrees/' + task_id + '/workspace'
    task = {
        'id': task_id, 'run_token': run_token, 'idempotency_key': 'fixture:' + task_id,
        'fencing_token': 1, 'attempt_id': 0, 'attempts': 0,
        'repo': 'Bbambaaamm/herdr', 'kind': 'coding',
        'workspace': workspace, 'work_contract_version': 1, 'work_budget_version': 1,
        'prompt': 'Repair add in arithmetic.py only. Run the frozen arithmetic check. '
                  'Stop after verified local handoff; do not publish or deploy.',
    }
    root_identity = InvocationIdentity(
        consumer=case['consumer'], agent_id='fixture-parent',
        parent_agent_id='fixture-supervisor', parent_task_id='offline188-envelope',
        task_id=task_id, run_token=run_token, fencing_token=1)
    child_identity = InvocationIdentity(
        consumer=case['consumer'], agent_id='fixture-child',
        parent_agent_id=root_identity.agent_id, parent_task_id=task_id,
        task_id=task_id+'-child', run_token=run_token, fencing_token=1)
    tools = ['read_file', 'write_file', 'herdr_verify_work', 'herdr_submit_result']
    proposal = {
        'schema_version': 'herdr-offline-clean-inputs-1',
        'case_sha256': expected_sha256, 'source_main': case['source_main'],
        'status': 'PROPOSAL_ONLY_NOT_ADMITTED',
        'task_seed': task,
        'root_identity': root_identity.to_json(),
        'managed_child_identity': child_identity.to_json(),
        'graph_shape': {'node_count': 2, 'max_depth': 2, 'max_fanout': 1},
        'workspace_files': case['files'],
        'workspace_sha256': digest(case['files']),
        'provider_edits': case['edits'],
        'write_files': sorted(case['edits']),
        'tools': tools, 'permissions': ['repo:read', 'repo:write'],
        'check': case['check'], 'limits': case['limits'],
        'authority_created': False, 'budget_allocated': False,
        'credentials_created': False, 'queue_written': False,
        'physical_acceptance': 'NOT_ESTABLISHED',
        'execution_requirements': [
            'Protected existing Herdr admission and one original budget lineage',
            'Immutable code/runtime/profile with a real root issuer and managed child',
            'Private HOME/network/IPC before any SDK import; synthetic credentials only',
            'Original absolute grant/work/envelope deadlines bound once at admission',
            'Existing trusted result verifier and original-worker cold recovery',
        ],
    }
    # This digest is integrity only. It is not an approval or acceptance receipt.
    proposal['proposal_sha256'] = digest(proposal)
    return json.loads(canonical(proposal))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--composition',type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--inner',action='store_true')
    parser.add_argument('--prepare-clean-inputs',type=Path)
    parser.add_argument('--case-sha256')
    parser.add_argument('--run-token')
    args=parser.parse_args()
    if args.prepare_clean_inputs is not None:
        need(not any((args.composition,args.sha256,args.output,args.inner)), 'clean_case_mode_is_data_only')
        need(not hasattr(os,'geteuid') or os.geteuid()!=0, 'clean_case_preparation_must_be_unprivileged')
        print(json.dumps(prepare_clean_inputs(args.prepare_clean_inputs,args.case_sha256,args.run_token),sort_keys=True))
        return 0
    need(args.case_sha256 is None and args.run_token is None
         and args.composition is not None and args.sha256 is not None and args.output is not None,
         'closed_legacy_fixture_invocation_required')
    if args.inner:return inner(args.composition,args.sha256,args.output)
    cfg,token=prepare_fixture(args.composition,args.sha256,args.output)
    tls=args.output/'tls';tls.mkdir(mode=0o700)
    result=subprocess.run(['/usr/bin/openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
          '-subj','/CN=inference-api.nousresearch.com','-addext','subjectAltName=DNS:inference-api.nousresearch.com',
          '-addext','basicConstraints=critical,CA:TRUE','-keyout',str(tls/'key.pem'),'-out',str(tls/'cert.pem')],capture_output=True,timeout=15)
    need(result.returncode==0,'fixture_certificate_creation_failed');(tls/'key.pem').chmod(0o600)
    write(args.output/'hosts',b'127.0.0.1 localhost inference-api.nousresearch.com\n::1 localhost\n',0o444)
    before=json.loads((args.output/'input-proof.json').read_bytes())['original_sha256']
    command=['/usr/bin/unshare','--mount','--net','--pid','--fork','--mount-proc',P,'-I','-B',str(Path(__file__).resolve()),
             '--composition',str(args.composition),'--sha256',args.sha256,'--output',str(args.output),'--inner']
    log=(args.output/'isolated-private.log').open('xb')
    try:
        completed=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=880)
    finally:log.close()
    need(snapshot_live(Path(cfg['runtime']['root']))==before,'original_changed_during_offline_cycle')
    print(json.dumps({'fixture':str(args.output),'isolated_exit':completed.returncode,
          'original_inputs_unchanged':True,'external_model_calls':0,'business_pr_created':False,
          'local_handoff_observed':(args.output/'local-handoff-observed.json').exists(),
          'full_task_done':False,'automatic_retry_allowed':False}),flush=True)
    return completed.returncode


if __name__=='__main__':raise SystemExit(main())
