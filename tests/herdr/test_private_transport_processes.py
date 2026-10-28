"""Real processes, fresh Unix channels, no authentication/provider HTTP."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

ROOT = str(Path(__file__).resolve().parents[2])


def test_http_exec_uses_devnull_and_a_fresh_protected_authenticated_channel():
    code = r'''
import ctypes, json, os, socket, subprocess, sys
sys.path.insert(0, sys.argv[1])
from herdr import host_model_transport as h
h._protect_process()
original = subprocess.Popen
observations = []
child_code = r"""
import json,os,sys,time
sys.path.insert(0,sys.argv[1])
from herdr import host_model_transport as h
# Simulate a slow interpreter startup, when an observer could pre-open stdin.
time.sleep(.25)
def fake(request):
    assert request['credential']=='fixture-secret'
    time.sleep(.4)
    return {'kind':'http_response','http_status':200,'body':{'answer':'fixture-only'}}
h._request_http=fake
h._http_child(sys.argv[2],int(sys.argv[3]),float(sys.argv[4]))
"""
observer_code = r"""
import json,os,sys,time
pid=int(sys.argv[1]);preopened=None;denied=False
until=time.monotonic()+3
while time.monotonic()<until:
    try:
        fd=os.open('/proc/'+str(pid)+'/fd/0',os.O_RDONLY|os.O_NONBLOCK)
        if preopened is None:preopened=fd
        else:os.close(fd)
    except PermissionError:
        denied=True
        break
    except FileNotFoundError:
        pass
    time.sleep(.01)
raw=os.read(preopened,1024) if preopened is not None else b''
if preopened is not None:os.close(preopened)
print(json.dumps({'preopened_bytes':len(raw),'protected_fd_denied':denied}))
"""
def launch(argv, **kwargs):
    assert kwargs['stdin']==kwargs['stdout']==kwargs['stderr']==subprocess.DEVNULL
    child = original([sys.executable,'-I','-B','-c',child_code,sys.argv[1],*argv[-3:]],**kwargs)
    observer = original([sys.executable,'-I','-B','-c',observer_code,str(child.pid)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
    observations.append(observer)
    return child
h.subprocess.Popen=launch
answer=h._perform_http('fixture-secret',{'model':'fixture:free'},5)
assert answer=={'kind':'http_response','http_status':200,'body':{'answer':'fixture-only'}}
for observer in observations:
    out,err=observer.communicate(timeout=5)
    assert observer.returncode==0,err
    observed=json.loads(out)
    assert observed['preopened_bytes']==0 and observed['protected_fd_denied']
print(json.dumps({'fresh_channel_passed':True,'observers':len(observations),'provider_http_requests':0}))
'''
    code = "import os\nif os.geteuid()==0:os.setgroups([]);os.setgid(1001);os.setuid(1001)\n" + code
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code, ROOT],
        capture_output=True, text=True, timeout=15, env={"PATH":"/usr/bin:/bin","LANG":"C.UTF-8"})
    assert result.returncode == 0, result.stderr[-3000:]
    assert json.loads(result.stdout) == {"fresh_channel_passed":True,"observers":1,"provider_http_requests":0}


def test_root_client_pin_rejects_mutable_path_and_symlink(tmp_path):
    from herdr.parent_github_transport import _root_client_identity
    from herdr.evidence import EvidenceError
    script=tmp_path/'gh';script.write_text('#!/bin/sh\nexit 0\n');script.chmod(0o755)
    with pytest.raises((EvidenceError,OSError)):_root_client_identity(script)
    alias=tmp_path/'alias';alias.symlink_to('/usr/bin/git')
    with pytest.raises((EvidenceError,OSError)):_root_client_identity(alias)

@pytest.mark.skipif(os.geteuid()!=0,reason="cross-user root publication boundary requires administrator")
def test_root_broker_executes_only_original_publisher_pid(tmp_path):
    import secrets
    import socket
    from types import SimpleNamespace
    from herdr.parent_github_peer import serve_parent_transport
    from tests.herdr.test_parent_github_transport import permit
    from dataclasses import asdict
    p=permit()
    address='herdr-parent-'+secrets.token_hex(24)
    code=r"""
import ctypes,json,os,sys,time
sys.path.insert(0,sys.argv[1])
os.setgroups([]);os.setgid(1001);os.setuid(1001)
from herdr.host_model_transport import _protect_process
_protect_process()
from herdr.parent_publication import ParentPublicationPermit
from herdr.parent_github_peer import GitHubParentTransportProxy
from types import SimpleNamespace
p=ParentPublicationPermit(**json.loads(sys.argv[4]))
c=GitHubParentTransportProxy(permit=p,address=sys.argv[2],root_pid=int(sys.argv[3]))
time.sleep(.3)
a=SimpleNamespace(commit_sha='d'*40)
assert c.observe(p,a)['base_sha']==p.base_sha
c.push(p,a,b'fixture-only-bundle')
c.create_pull_request(p,a,{'base':p.base_branch,'head':p.head_branch,'title':'fixture','body':'fixture'})
print('PASS')
"""
    calls=[]
    def observe(*args):
        assert os.geteuid()==0
        calls.append('observe')
        return {'base_sha':p.base_sha}
    client=SimpleNamespace(observe=observe,
        push=lambda *args:calls.append('push'),
        create_pull_request=lambda *args:calls.append('pr'))
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as listener:
        listener.bind('\0'+address);listener.listen(4)
        child=subprocess.Popen([sys.executable,'-I','-B','-c',code,ROOT,address,str(os.getpid()),json.dumps(asdict(p))],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
        # Another process of the same UID knows the public address and exact
        # permit hash, but its request must never reach the transport.
        attack=r"""
import json,os,socket,struct,sys
os.setgroups([]);os.setgid(1001);os.setuid(1001)
c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect('\0'+sys.argv[1])
raw=json.dumps({'method':'observe','permit':sys.argv[2],'commit_sha':'d'*40}).encode()
c.sendall(struct.pack('!I',len(raw))+raw)
try:c.recv(1)
except (ConnectionResetError,BrokenPipeError):pass
"""
        attacker=subprocess.Popen([sys.executable,'-I','-B','-c',attack,address,p.hash],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
        try:
            assert serve_parent_transport(listener,child,permit=p,transport=client,timeout=10)==0
            out,err=child.communicate(timeout=3)
            assert out.strip()==b'PASS',err
            attacker.communicate(timeout=3)
            assert attacker.returncode==0
        finally:
            for process in (child,attacker):
                if process.poll() is None:process.kill()
                process.wait(timeout=3)
    assert calls==['observe','push','pr']


@pytest.mark.skipif(os.geteuid()!=0,reason="credential mount masking requires administrator")
def test_publisher_masks_credentials_before_dropping_uid_and_exec():
    """Exercise publish -> a real HOME rename -> the actual child masking code."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix='herdr-root-mount-race-',dir='/var/lib') as folder:
        root=Path(folder);root.chmod(0o755)
        home=root/'mutable-home';(home/'.config/gh').mkdir(parents=True,mode=0o755)
        for path in (home,home/'.config',home/'.config/gh'):
            os.chown(path,1001,1001);path.chmod(0o755)
        pins=root/'host-only-github-approved38';pins.mkdir(mode=0o700)
        gh=pins/'gh';gh.mkdir(mode=0o751);os.chown(gh,1001,1001)
        credential=gh/'hosts.yml';credential.write_text('NONSECRET_FIXTURE')
        os.chown(credential,1001,1001);credential.chmod(0o600)
        guard=pins/'guard';guard.mkdir(mode=0o755);(guard/'config').write_text('NONSECRET_GUARD')
        program=r"""
import ast,ctypes,json,os,secrets,signal,socket,stat,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
from dataclasses import asdict
CODE=Path(sys.argv[1]);ROOT=Path(sys.argv[2]);HOME=ROOT/'mutable-home'
PYTHON=sys.executable;COMPOSITION_PATH='/fixture-composition';COMPOSITION_SHA='fixture'
sys.path.insert(0,str(CODE))
from herdr import operation_readiness
import herdr.parent_github_transport as transport_module
original_client=transport_module.GitHubParentTransport
def checked_client(**kwargs):
    client=original_client(**kwargs)
    assert client.env['GH_CONFIG_DIR']==str(ROOT/'host-only-github-approved38/gh')
    assert not any(k in client.env for k in ('GH_TOKEN','GITHUB_TOKEN'))
    return client
transport_module.GitHubParentTransport=checked_client
from herdr.parent_publication import ParentPublicationPermit
_helpers={'_readiness':lambda:operation_readiness}
source=CODE/'deploy/herdr/native_pilot/host_action.py'
__file__=str(source)
nodes=ast.parse(source.read_text()).body
for name in ('environment','publisher_child','publish'):
    node=next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'))
child_function=ast.unparse(next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name=='publisher_child'))
real_sp=subprocess
def launch(argv,**kwargs):
    # Run the exact adversarial rename after publish's mounts, before child
    # masking. This is the vulnerable ordering identified by independent review.
    attack="import os,sys;h=sys.argv[1];os.setgroups([]);os.setgid(1001);os.setuid(1001);os.rename(h+'/.config',h+'/.config-moved');os.makedirs(h+'/.config/gh')"
    changed=real_sp.run([PYTHON,'-I','-B','-c',attack,str(HOME)],capture_output=True,text=True,timeout=5)
    assert changed.returncode==0,changed.stderr
    child_code=r'''
import ctypes,os,signal,stat,subprocess,sys
from pathlib import Path
ROOT=Path(sys.argv[1]);HOME=ROOT/'mutable-home';CODE=Path(sys.argv[3]);PYTHON=sys.executable
sys.path.insert(0,str(CODE))
def observed_exec(*args):
    assert os.geteuid()==1001
    for path in (HOME/'.config-moved/gh/hosts.yml',
                 ROOT/'host-only-github-approved38/gh/hosts.yml',
                 Path('/etc/herdr/heating-github-guard/config')):
        try:path.read_bytes()
        except (FileNotFoundError,PermissionError):pass
        else:raise AssertionError('credential mount survived HOME rename')
    print('MASKED',flush=True)
    raise SystemExit(0)
os.execve=observed_exec
'''+ '\n'+child_function+"\npublisher_child(Path('/fixture-permit'),int(sys.argv[2]))\n"
    return real_sp.Popen(['/usr/bin/unshare','--mount','--',PYTHON,'-I','-B','-c',
                         child_code,str(ROOT),str(os.getpid()),str(CODE)],**kwargs)
subprocess=SimpleNamespace(run=real_sp.run,Popen=launch)
p=ParentPublicationPermit({'id':'fixture','run_token':'original','idempotency_key':'original',
    'attempt':1,'fencing_token':1},'org/repo','a'*64,'b'*64,'c'*40,'review/base',
    'herdr/result',int(time.time())+60,'public fixture only')
value={'version':1,'permit':asdict(p),'transport':{'mode':'root-peer',
    'address':'herdr-parent-'+secrets.token_hex(24),'root_pid':os.getpid()}}
raise SystemExit(publish(value,{'HERDR_ENV':'1'}))
"""
        result=subprocess.run(['/usr/bin/unshare','--mount','--',sys.executable,'-I','-B','-c',
            program,ROOT,str(root)],capture_output=True,text=True,timeout=20,
            env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
        assert result.returncode==0,result.stderr[-4000:]
        assert result.stdout.strip()=='MASKED'
        assert credential.read_text()=='NONSECRET_FIXTURE'
