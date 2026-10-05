"""Host-approved, offline single-process checks in disposable namespaces.

No host home, runtime credentials, inherited environment, writable source, or
subprocess creation is exposed. More permissive environments need their own
approved implementation; this runner never weakens an unsupported profile.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time

from .evidence import EvidenceUnavailable, canonical, digest, network_denial_filter
from .policy_launch import FrozenTree
from .work_cycle import CheckResult, require, tree_snapshot

_MARKER=b"HERDR_CHECK_ATTESTATION "
_BOOTSTRAP = r"""
import hashlib,json,os,resource,sys
cfg=json.loads(sys.argv[1])
rows={}
for line in open('/proc/self/mountinfo'):
    fields=line.split(' - ',1)[0].split()
    rows[fields[4]]=set(fields[5].split(','))
assert 'ro' in rows['/'] and 'ro' in rows['/workspace'] and 'ro' in rows['/dev']
assert not any('rw' in modes and path.startswith('/workspace/') for path,modes in rows.items())
st=os.stat('/workspace')
assert [st.st_dev,st.st_ino]==cfg['workspace_inode']
for kind,expected in cfg['host_namespaces'].items():
    assert os.readlink('/proc/self/ns/'+kind)!=expected
assert not os.path.exists('/home/agentops') and not os.path.exists('/root')
assert os.environ.get('HERDR_CHECK_PARENT_SECRET') is None
assert not os.path.exists('/run/herdr-policy')
resource.setrlimit(resource.RLIMIT_AS,(cfg['memory_bytes'],cfg['memory_bytes']))
resource.setrlimit(resource.RLIMIT_CPU,(cfg['cpu_seconds'],cfg['cpu_seconds']))
resource.setrlimit(resource.RLIMIT_FSIZE,(cfg['scratch_file_bytes'],cfg['scratch_file_bytes']))
resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
proof={'version':1,'profile_sha256':cfg['profile_sha256'],'tree_sha256':cfg['tree_sha256'],
       'workspace_inode':[st.st_dev,st.st_ino],
       'namespaces':{kind:os.readlink('/proc/self/ns/'+kind) for kind in cfg['host_namespaces']},
       'network':'none','process_creation':'denied','writable_roots':['/tmp'],
       'memory_bytes':cfg['memory_bytes'],'scratch_bytes':cfg['scratch_bytes'],
       'cpu_seconds':cfg['cpu_seconds']}
print('HERDR_CHECK_ATTESTATION '+json.dumps(proof,sort_keys=True,separators=(',',':')),flush=True)
os.execv(cfg['command'][0],cfg['command'])
"""

@dataclass(frozen=True)
class CheckEnvironment:
    version: str
    system_files: tuple[tuple[str,str], ...]
    executables: tuple[str, ...]
    role: str = "validation"
    network: str = "none"
    process_creation: str = "denied"
    memory_bytes: int = 536_870_912
    scratch_bytes: int = 16_777_216
    scratch_file_bytes: int = 1_048_576

    def __post_init__(self):
        object.__setattr__(self,"system_files",tuple(tuple(x) for x in self.system_files))
        object.__setattr__(self,"executables",tuple(self.executables))
        require(isinstance(self.version,str) and 1<=len(self.version)<=64,"environment version required")
        require(self.role=="validation" and self.network=="none" and self.process_creation=="denied",
                "unsupported check isolation profile")
        require(self.system_files and len(self.system_files)<=256 and
            len({x[0] for x in self.system_files})==len(self.system_files),"approved system input manifest required")
        for path,sha in self.system_files:
            require(isinstance(path,str) and Path(path).is_absolute() and ".." not in Path(path).parts
                and isinstance(sha,str) and len(sha)==64 and set(sha)<=set("0123456789abcdef"),
                "approved system input invalid")
        require(self.executables and len(self.executables)<=32 and
                set(self.executables)<={x[0] for x in self.system_files},"approved executables required")
        for name,limit,minimum,maximum in (("memory_bytes",self.memory_bytes,16_777_216,2_147_483_648),
            ("scratch_bytes",self.scratch_bytes,1_048_576,67_108_864),
            ("scratch_file_bytes",self.scratch_file_bytes,1024,self.scratch_bytes)):
            require(type(limit) is int and minimum<=limit<=maximum,"check resource bound invalid")

    @property
    def hash(self):
        return digest(asdict(self))

    def verify_inputs(self):
        for path,expected in self.system_files:
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            try:
                import stat
                info=os.fstat(fd)
                require(stat.S_ISREG(info.st_mode) and info.st_size<=268_435_456,"system input not a bounded regular file")
                hasher=hashlib.sha256()
                remaining=info.st_size
                while remaining:
                    chunk=os.read(fd,min(remaining,1_048_576))
                    require(bool(chunk),"system input shortened")
                    hasher.update(chunk)
                    remaining-=len(chunk)
                require(not os.read(fd,1) and hasher.hexdigest()==expected,"approved system input changed")
            finally:
                os.close(fd)

class HostCheckRunner:
    def __init__(self, environment, storage, *, git=None):
        require(isinstance(environment,CheckEnvironment),"host environment required")
        self.environment,self.storage,self.git=environment,Path(storage),git
        self.storage.mkdir(mode=0o700,parents=True,exist_ok=True)
        require(not self.storage.is_symlink() and self.storage.stat().st_mode&0o077==0,
                "check storage must be host private")
        self.environment.verify_inputs()

    def __call__(self,check,root,plan,tree_sha256):
        require(plan.environment_sha256==self.environment.hash,"approved check environment mismatch")
        executable=str(Path(check.command[0]).resolve(strict=True))
        require(executable in self.environment.executables,"check executable not approved")
        require("/usr/bin/python3" in self.environment.executables or
                str(Path("/usr/bin/python3").resolve()) in self.environment.executables,
                "fixed bootstrap interpreter not approved")
        require(plan.checks and check in plan.checks,"check not in frozen plan")
        require(Path("/usr/bin/bwrap").is_file(),"required isolation unavailable")
        self.environment.verify_inputs()
        snapshot=tree_snapshot(root,git=self.git)
        require(digest(snapshot)==tree_sha256,"check source tree changed")
        for path,sha in check.protected_inputs:
            require(snapshot.get(path,{}).get("sha256")==sha,"verification input changed")
        require(not self.storage.resolve().is_relative_to(Path(root).resolve()),"check storage is worker writable")
        frozen=FrozenTree.create(Path(root),target=Path("/workspace"),
            files={name:item["sha256"] for name,item in snapshot.items()},storage=self.storage,
            writable_roots=(Path(root),),executable_files=[name for name,item in snapshot.items() if item["mode"]==0o755],
            max_bytes=67_108_864,max_file_bytes=67_108_864)
        fd=None
        try:
            fd=network_denial_filter(deny_process_creation=True)
            cfg={"workspace_inode":[frozen.device,frozen.inode],"tree_sha256":tree_sha256,
                 "host_namespaces":{kind:os.readlink("/proc/self/ns/"+kind) for kind in ("pid","mnt","net")},
                 "profile_sha256":self.environment.hash,
                 "memory_bytes":self.environment.memory_bytes,"scratch_bytes":self.environment.scratch_bytes,
                 "scratch_file_bytes":self.environment.scratch_file_bytes,"cpu_seconds":check.timeout_seconds,
                 "command":[executable,*check.command[1:]]}
            argv=["/usr/bin/bwrap","--die-with-parent","--unshare-pid","--unshare-net","--unshare-ipc",
                "--unshare-uts","--cap-drop","ALL","--tmpfs","/","--ro-bind","/usr","/usr",
                "--ro-bind","/lib","/lib","--ro-bind","/lib64","/lib64","--symlink","usr/bin","/bin",
                "--dir","/home","--dir","/run","--dir","/etc","--dir","/workspace","--proc","/proc","--dev","/dev","--remount-ro","/dev",
                "--size",str(self.environment.scratch_bytes),"--tmpfs","/tmp","--remount-ro","/",
                "--ro-bind-fd",str(frozen.fd),"/workspace","--chdir","/workspace",
                "--clearenv","--setenv","PATH","/usr/bin:/bin","--setenv","HOME","/tmp",
                "--setenv","TMPDIR","/tmp","--setenv","PYTHONDONTWRITEBYTECODE","1",
                "--setenv","PYTHONNOUSERSITE","1","--setenv","LANG","C.UTF-8",
                "--seccomp",str(fd),"--",str(Path("/usr/bin/python3").resolve()),"-I","-S","-c",
                _BOOTSTRAP,canonical(cfg).decode()]
            result=self._execute(argv,check,(fd,frozen.fd))
            frozen.verify()
            self.environment.verify_inputs()
            first,separator,output=result[0].partition(b"\n")
            require(separator and first.startswith(_MARKER),"physical check attestation unavailable")
            require(len(first)<=8192,"physical check attestation exceeds bound")
            require(len(output)<=check.output_bytes or result[2],"check output exceeds declared bound")
            proof=json.loads(first[len(_MARKER):])
            require(proof.get("profile_sha256")==self.environment.hash and
                    proof.get("tree_sha256")==tree_sha256 and
                    proof.get("workspace_inode")==cfg["workspace_inode"],"physical check attestation mismatch")
            return CheckResult(check.id,plan.hash,self.environment.hash,tree_sha256,result[1],
                hashlib.sha256(output).hexdigest(),result[2],result[3],digest(proof))
        except (OSError,subprocess.SubprocessError) as exc:
            raise EvidenceUnavailable("required check isolation unavailable") from exc
        finally:
            if fd is not None:
                os.close(fd)
            frozen.cleanup_after_pane_closed()

    @staticmethod
    def _execute(argv,check,pass_fds):
        process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            env={"PATH":"/usr/bin:/bin","LANG":"C.UTF-8"},start_new_session=True,close_fds=True,pass_fds=pass_fds)
        started=time.monotonic()
        data=bytearray()
        limited=False
        deadline=started+check.timeout_seconds
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ)
                while True:
                    left=deadline-time.monotonic()
                    if left<=0 or not selector.select(left):
                        limited=True
                        break
                    chunk=os.read(process.stdout.fileno(),min(8192,check.output_bytes+8193-len(data)))
                    if not chunk:
                        break
                    data.extend(chunk)
                    header=data.find(b"\n")
                    if (header>=0 and len(data)-header-1>check.output_bytes) or len(data)>check.output_bytes+8192:
                        limited=True
                        break
            if limited:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait(timeout=2)
            else:
                try:
                    process.wait(timeout=max(.01,deadline-time.monotonic()))
                except subprocess.TimeoutExpired:
                    limited=True
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait(timeout=2)
            return bytes(data),124 if limited else process.returncode,limited,int((time.monotonic()-started)*1000)
        finally:
            try:
                os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=2)
            process.stdout.close()
