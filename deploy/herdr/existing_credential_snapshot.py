from pathlib import Path
import os,sys,json,hashlib,tempfile,subprocess,base64,time,copy,stat
SDK='/opt/herdr/releases/p0-5035d92-test/hermes';SITE=SDK+'/venv/lib/python3.11/site-packages';P='/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11';MODEL='meituan/longcat-2.0:free'
def expiry(token):
 try:
  part=token.split('.')[1];return int(json.loads(base64.urlsafe_b64decode(part+'='*((-len(part))%4)))['exp'])
 except Exception:return 0
def strip_refresh(value):
 if isinstance(value,dict):return {k:strip_refresh(v) for k,v in value.items() if 'refresh' not in k.lower()}
 if isinstance(value,list):return [strip_refresh(v) for v in value]
 return value
def minimal_store(entry,key,version=1):
 from datetime import datetime,timezone
 assert entry.get('id') and key and key in (entry.get('agent_key'),entry.get('access_token'))
 until=expiry(key);assert until>time.time()
 end=datetime.fromtimestamp(until,timezone.utc).isoformat()
 state={'access_token':key,'agent_key':key,'expires_at':end,'agent_key_expires_at':end,'inference_base_url':'https://inference-api.nousresearch.com/v1'}
 if entry.get('scope'):state['scope']=entry['scope']
 return {'version':version,'active_provider':'nous','providers':{'nous':state},'credential_pool':{'nous':[strip_refresh(entry)]}}
def write_private(path,data):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 try:
  view=memoryview(data)
  while view:n=os.write(fd,view);assert n>0;view=view[n:]
  os.fsync(fd)
 finally:os.close(fd)
def prepare(output, required_validity_seconds):
 assert type(required_validity_seconds)is int and required_validity_seconds>0
 assert os.geteuid()==1001 and output.is_absolute() and not output.exists()
 output.mkdir(mode=0o700);global_home=Path('/home/agentops');root=global_home/'.hermes';seen={}
 with tempfile.TemporaryDirectory(prefix='herdr38-source-auth-',dir='/dev/shm') as temporary:
  home=Path(temporary)/'home';profile=home/'.hermes/profiles/quantlab';profile.mkdir(parents=True,mode=0o700)
  for suffix in ['', 'shared','profiles/quantlab']:
   source=root/suffix/'auth.json'
   if not source.is_file():continue
   actual=source.resolve(strict=True);assert actual==root or root in actual.parents;data=source.read_bytes();seen[actual]=hashlib.sha256(data).hexdigest();target=home/'.hermes'/suffix/'auth.json';target.parent.mkdir(parents=True,exist_ok=True,mode=0o700);write_private(target,data)
  shared_source=root/'shared/nous_auth.json'
  if shared_source.is_file():
   actual=shared_source.resolve(strict=True);assert root in actual.parents;data=shared_source.read_bytes();seen[actual]=hashlib.sha256(data).hexdigest();target=home/'.hermes/shared/nous_auth.json';target.parent.mkdir(parents=True,exist_ok=True,mode=0o700);write_private(target,data)
  worker=r"""from pathlib import Path
import os,sys,json,hashlib,socket,subprocess,base64,time,contextlib,runpy
class NetworkForbidden(RuntimeError):pass
def denied(*a,**k):raise NetworkForbidden('offline-existing-credential')
socket.create_connection=denied;socket.getaddrinfo=denied;socket.socket.connect=denied;socket.socket.connect_ex=denied;socket.socket.sendto=denied;subprocess.Popen=denied
sys.path[:0]=['/opt/herdr/releases/p0-5035d92-test/hermes','/opt/herdr/releases/p0-5035d92-test/hermes/venv/lib/python3.11/site-packages']
import httpx
httpx.Client.send=denied
out=Path(sys.argv[1]);helpers=runpy.run_path(sys.argv[2],run_name='snapshot_functions')
with open(out/'private-sdk-diagnostic.txt','w') as diagnostic:
 with contextlib.redirect_stdout(diagnostic),contextlib.redirect_stderr(diagnostic):
  from hermes_cli import auth
  from agent.credential_pool import load_pool
  pool=load_pool('nous');selected=pool.select(model='meituan/longcat-2.0:free');assert selected and selected.runtime_api_key, 'existing_runtime_credential_unavailable'
  key=selected.runtime_api_key
  assert selected.runtime_base_url.rstrip('/')=='https://inference-api.nousresearch.com/v1'
  ends=helpers['expiry'](key);assert ends-time.time()>=int(sys.argv[3]), 'existing_runtime_credential_validity_insufficient'
  store=helpers['minimal_store'](selected.to_dict(),key,getattr(auth,'AUTH_STORE_VERSION',1))
  helpers['write_private'](out/'auth.json',(json.dumps(store,sort_keys=True,separators=(',',':'))+'\n').encode())
  info={'credential_valid_until_epoch':ends,'expected_api_key_sha256':hashlib.sha256(key.encode()).hexdigest(),'standard_renewal_performed':False,'auth_httpx_requests':0,'model_calls_performed':0,'credentials_printed':False}
  helpers['write_private'](out/'auth-info.json',(json.dumps(info,sort_keys=True)+'\n').encode())
print(json.dumps({'snapshot_ready':True,'auth_http_requests':0,'model_calls':0}))
"""
  env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':str(home),'HERMES_HOME':str(profile),'HERMES_PROFILE':'quantlab','HERMES_MANAGED_DIR':str(home/'absent-managed-sentinel'),'LANG':'C.UTF-8'}
  result=subprocess.run([P,'-I','-B','-c',worker,str(output),__file__,str(required_validity_seconds)],env=env,cwd=str(profile),capture_output=True,text=True,timeout=30)
  write_private(output/'worker-stdout-private.txt',result.stdout.encode());write_private(output/'worker-stderr-private.txt',result.stderr.encode());assert all(hashlib.sha256(p.read_bytes()).hexdigest()==value for p,value in seen.items());assert result.returncode==0
  assert all(hashlib.sha256(p.read_bytes()).hexdigest()==value for p,value in seen.items())
  info=json.loads((output/'auth-info.json').read_bytes());assert info['credential_valid_until_epoch']-time.time()>=required_validity_seconds
  # Independent SDK selection in a home containing only the minimal snapshot.
  checkhome=Path(temporary)/'check-home';checkhome.mkdir(mode=0o700)
  verify=r"""from pathlib import Path
import os,sys,json,hashlib,socket,subprocess
class NetworkForbidden(RuntimeError):pass
def denied(*a,**k):raise NetworkForbidden('snapshot-verification')
socket.create_connection=denied;socket.getaddrinfo=denied;socket.socket.connect=denied;socket.socket.connect_ex=denied;socket.socket.sendto=denied;subprocess.Popen=denied
sys.path[:0]=['/opt/herdr/releases/p0-5035d92-test/hermes','/opt/herdr/releases/p0-5035d92-test/hermes/venv/lib/python3.11/site-packages']
import httpx;httpx.Client.send=denied
from agent.credential_pool import load_pool
from hermes_cli import auth
creds=auth.resolve_nous_runtime_credentials(timeout_seconds=5,force_refresh=False)
p=Path(sys.argv[1]);info=json.loads((p/'auth-info.json').read_bytes());pool=load_pool('nous');selected=pool.select(model='meituan/longcat-2.0:free');assert selected and selected.runtime_api_key==creds['api_key'] and hashlib.sha256(selected.runtime_api_key.encode()).hexdigest()==info['expected_api_key_sha256']
store=json.loads((p/'auth.json').read_bytes())
def clean(v):
 if isinstance(v,dict):return all('refresh' not in k.lower() and clean(x) for k,x in v.items())
 if isinstance(v,list):return all(clean(x) for x in v)
 return True
assert clean(store) and set(store['providers'])=={'nous'} and set(store['credential_pool'])=={'nous'}
print(json.dumps({'snapshot_selection_verified':True,'auth_http_requests':0,'model_calls':0}))
"""
  env.update(HOME=str(checkhome),HERMES_HOME=str(output),HERMES_MANAGED_DIR=str(checkhome/'absent-managed-sentinel'))
  checked=subprocess.run([P,'-I','-B','-c',verify,str(output)],env=env,cwd=str(output),capture_output=True,text=True,timeout=30)
  write_private(output/'selection-stdout-private.txt',checked.stdout.encode());write_private(output/'selection-stderr-private.txt',checked.stderr.encode());assert checked.returncode==0
  final=json.loads((output/'auth.json').read_bytes());assert final==strip_refresh(final)
  return {'snapshot_ready':True,'snapshot_selection_verified':True,'refresh_material_excluded':True,'original_login_files_unchanged':True,'auth_http_requests':0,'model_calls':0}
if __name__=='__main__':
 assert len(sys.argv)==5 and sys.argv[1]=='--snapshot-existing-login' and sys.argv[3]=='--required-validity-seconds'
 try:print(json.dumps(prepare(Path(sys.argv[2]),int(sys.argv[4])),sort_keys=True))
 except BaseException as error:print(json.dumps({'snapshot_ready':False,'error_type':type(error).__name__,'auth_http_requests':0,'model_calls':0}));raise SystemExit(1)
