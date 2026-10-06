"""Owned local commits with normal hooks confined to a disposable repository.

Only content-addressed objects and the exact owned ref/index are published.
No hook receives the live Git metadata, host home, credentials or a network.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import zlib

from .check_runner import CheckEnvironment, HostCheckRunner
from .evidence import canonical, digest, network_denial_filter, read_only_git, verify_committed_bytes
from .policy_launch import _open_relative
from .work_cycle import require, WorkPhase, tree_snapshot
from .evidence import EvidenceUnavailable, parse_artifact
from .workspace import ArtifactRef, WorkspaceManager
from .work_lifetime import require_work_time

_BOOTSTRAP = r"""
import base64,hashlib,json,os,resource,shutil,socket,stat,subprocess,sys
cfg=json.loads(sys.argv[1])
assert os.getuid()==65534 and os.getgid()==65534
resource.setrlimit(resource.RLIMIT_AS,(cfg['memory_bytes'],cfg['memory_bytes']))
resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,67108864))
resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
resource.setrlimit(resource.RLIMIT_NPROC,(cfg['max_processes'],cfg['max_processes']))
resource.setrlimit(resource.RLIMIT_CPU,(cfg['timeout'],cfg['timeout']))
rows={}
for line in open('/proc/self/mountinfo'):
    fields=line.split(' - ',1)[0].split();rows[fields[4]]=set(fields[5].split(','))
assert 'ro' in rows['/'] and 'rw' in rows['/workspace']
for path in ('/input','/workspace/.git/hooks','/workspace/.git/config',cfg['object_source']):
    assert 'ro' in rows[path]
assert not os.path.exists('/home/agentops/.hermes') and not os.path.exists('/root')
namespaces={kind:os.readlink('/proc/self/ns/'+kind) for kind in cfg['host_namespaces']}
assert all(value!=cfg['host_namespaces'][kind] for kind,value in namespaces.items())
try: socket.socket()
except PermissionError: pass
else: raise AssertionError('network syscall filter unavailable')
proof={'version':1,'role':'hygiene','policy_sha256':cfg['policy_sha256'],
       'tree_sha256':cfg['tree_sha256'],'namespaces':namespaces,'uid':os.getuid(),
       'network':'none','workspace_bytes':134217728,'max_processes':cfg['max_processes'],
       'memory_bytes_per_process':cfg['memory_bytes']}
print('HERDR_HYGIENE_ATTESTATION '+json.dumps(proof,sort_keys=True,separators=(',',':')),flush=True)
for name in os.listdir('/input'):
    if name=='.git': continue
    source='/input/'+name
    if os.path.isdir(source):shutil.copytree(source,name)
    else:shutil.copyfile(source,name);os.chmod(name,os.stat(source).st_mode&0o777)
for name in os.listdir('/input/.git'):
    if name in ('config','hooks'):continue
    source='/input/.git/'+name;target='.git/'+name
    if os.path.isdir(source):shutil.copytree(source,target)
    else:shutil.copyfile(source,target)
def git(*args):
    result=subprocess.run(['/usr/bin/git','--no-replace-objects',*args],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode:
        sys.stdout.buffer.write(result.stdout)
        raise SystemExit(result.returncode)
    return result.stdout
git('read-tree',cfg['base'])
open('.git/herdr-paths','wb').write(b'\0'.join(x.encode() for x in cfg['changed'])+b'\0')
git('add','--pathspec-from-file=.git/herdr-paths','--pathspec-file-nul')
open('.git/herdr-message','w').write(cfg['message'])
output=git('commit','-F','.git/herdr-message')
names=git('ls-files','--cached','--others','-z').decode().split('\0')
seen={name for name in names if name}
changed=seen!=set(cfg['inventory'])
for name,row in cfg['inventory'].items():
    try:
        info=os.lstat(name)
        changed=changed or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode)!=row['mode']
        raw=open(name,'rb').read(67108865)
        changed=changed or hashlib.sha256(raw).hexdigest()!=row['sha256']
    except OSError:changed=True
if changed:
    print('HERDR_HYGIENE_EXPORT '+json.dumps({'status':'changed'}),flush=True)
    raise SystemExit(0)
assert not os.listdir('.git/objects/pack')
objects={}
total=0
for directory in os.listdir('.git/objects'):
    if directory in ('info','pack'):continue
    assert len(directory)==2 and all(x in '0123456789abcdef' for x in directory)
    for name in os.listdir('.git/objects/'+directory):
        assert len(name)==38 and all(x in '0123456789abcdef' for x in name)
        path='.git/objects/'+directory+'/'+name;info=os.lstat(path)
        assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=67108864
        raw=open(path,'rb').read(67108865);total+=len(raw)
        assert total<=67108864 and len(objects)<4096
        objects[directory+'/'+name]=base64.b64encode(raw).decode()
index=open('.git/index','rb').read(2097153);assert len(index)<=2097152
result={'status':'committed','commit':git('rev-parse','HEAD').decode().strip(),
        'objects':objects,'index':base64.b64encode(index).decode()}
print('HERDR_HYGIENE_EXPORT '+json.dumps(result,sort_keys=True,separators=(',',':')),flush=True)
"""

@dataclass(frozen=True)
class LocalCommitPolicy:
    version: str
    environment: CheckEnvironment
    config_sha256: str
    hooks_root: str
    hooks: tuple[tuple[str, str], ...]
    timeout_seconds: int = 60
    output_bytes: int = 65536
    max_processes: int = 8

    def __post_init__(self):
        object.__setattr__(self, "hooks", tuple(tuple(x) for x in self.hooks))
        require(isinstance(self.version, str) and 1 <= len(self.version) <= 64
                and isinstance(self.environment, CheckEnvironment), "local commit environment required")
        require(re.fullmatch("[0-9a-f]{64}", self.config_sha256 or "")
                and Path(self.hooks_root).is_absolute(), "frozen repository commit policy required")
        require(len(self.hooks) <= 32 and len(dict(self.hooks)) == len(self.hooks),
                "bounded repository hook inventory required")
        for name, content in self.hooks:
            require(re.fullmatch("[A-Za-z0-9_-]{1,64}", name)
                    and re.fullmatch("[0-9a-f]{64}", content), "hook input invalid")
        require(type(self.timeout_seconds) is int and 1 <= self.timeout_seconds <= 120
                and type(self.output_bytes) is int and 1024 <= self.output_bytes <= 16777216
                and type(self.max_processes) is int and 8 <= self.max_processes <= 32,
                "local commit resource bounds required")
        require("/usr/bin/git" in self.environment.executables, "commit Git runtime is not approved")

    @property
    def hash(self):
        return digest(asdict(self))


def private_file(path, limit):
    require_work_time()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
                "bounded regular Git input required")
        raw = bytearray()
        while len(raw) <= limit:
            require_work_time()
            part = os.read(fd, min(65536, limit + 1 - len(raw)))
            if not part: break
            raw.extend(part)
        after = os.fstat(fd)
        stamp = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
        require(stamp(before) == stamp(after) and len(raw) == before.st_size,
                "Git input changed during read")
        return bytes(raw)
    finally:
        os.close(fd)


def verified_config_values(common,git,expected):
    """Keep the approved inode pinned around the separate Git config parser."""
    path=common/"config"
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=1048576,
                "bounded repository config required")
        config=os.read(fd,1048577)
        require(len(config)==before.st_size and hashlib.sha256(config).hexdigest()==expected,
                "repository commit policy changed")
        values=git(["config","--local","--null","--list"]).split("\0")
        stamp=lambda x:(x.st_dev,x.st_ino,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
        require(stamp(before)==stamp(os.fstat(fd))==stamp(path.lstat()),
                "repository config changed during parsing")
        os.lseek(fd,0,os.SEEK_SET)
        require(os.read(fd,1048577)==config,"repository config changed during parsing")
        return values
    finally:os.close(fd)

def directory_fd(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve(strict=True) == path, "canonical Git directory required")
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)


def publish_file(parent, name, raw, *, expected=None):
    """Normal exclusive Git lock protocol, one literal name, durable rename."""
    require("/" not in name and name not in {".", ".."}, "literal metadata name required")
    require_work_time()
    lock = name + ".lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
    try:
        if expected is not None:
            current = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            try:
                require(os.read(current, len(expected) + 1) == expected, "owned Git ref changed")
            finally: os.close(current)
        pending = memoryview(raw)
        while pending:
            require_work_time()
            written = os.write(fd, pending)
            require(written > 0, "metadata write made no progress")
            pending = pending[written:]
        os.fsync(fd)
        os.rename(lock, name, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(fd)
        try: os.unlink(lock, dir_fd=parent)
        except FileNotFoundError: pass


class HostLocalCommitter:
    def __init__(self, policy, storage, draft, *, completion_plan, workspace_identity):
        require(isinstance(policy, LocalCommitPolicy) and isinstance(draft, ArtifactRef)
                and not draft.result_sha and draft.commit_sha == draft.base_sha, "host local commit draft required")
        require(isinstance(completion_plan, dict) and completion_plan["identity"]["id"] == draft.task_id
                and completion_plan["identity"]["attempt"] == draft.attempt
                and completion_plan["base_sha"] == draft.base_sha, "commit completion binding mismatch")
        self.policy, self.storage, self.draft = policy, Path(storage), draft
        self.completion_plan, self.workspace_identity = completion_plan, workspace_identity
        self.storage.mkdir(mode=0o700, parents=True, exist_ok=True)
        require(self.storage.resolve(strict=True) == self.storage and self.storage.stat().st_mode & 0o077 == 0,
                "host commit storage must be private")

    def _repository(self, cycle):
        info = cycle.root.lstat()
        require(f"{info.st_dev}:{info.st_ino}" == self.workspace_identity
                and not self.storage.is_relative_to(cycle.root), "local commit workspace ownership changed")
        git = read_only_git(cycle.root)
        require(git(["symbolic-ref", "--short", "HEAD"]).strip() == self.draft.branch
                and self.draft.branch.startswith("herdr/"), "local commit requires the exact owned branch")
        metadata = Path(git(["rev-parse", "--absolute-git-dir"]).strip())
        common = Path(git(["rev-parse", "--path-format=absolute", "--git-common-dir"]).strip())
        for path in (metadata, common): directory_fd_close(path)
        values = verified_config_values(common,git,self.policy.config_sha256)
        selected = {}
        allowed = {"user.name", "user.email", "core.filemode", "core.autocrlf", "core.commentchar", "commit.cleanup"}
        for row in filter(None, values):
            key, separator, value = row.partition("\n")
            require(separator and not key.startswith(("include.", "includeif.", "filter."))
                    and key not in {"core.fsmonitor", "commit.gpgsign", "commit.template"},
                    "repository commit policy needs an approved richer profile")
            structural={"core.repositoryformatversion":"0","core.bare":"false","core.logallrefupdates":"true"}
            require(key in allowed or key=="core.hookspath" or key in structural and value==structural[key],
                    "repository commit policy needs an approved richer profile")
            if key in allowed:
                require(key not in selected, "duplicate commit policy key")
                selected[key] = value
            if key == "core.hookspath":
                actual = Path(value) if Path(value).is_absolute() else cycle.root/value
                require(actual.resolve(strict=True) == Path(self.policy.hooks_root), "configured hook root differs")
        require(selected.get("user.name") and selected.get("user.email"), "repository commit author policy missing")
        if not any(row.startswith("core.hookspath\n") for row in values):
            require(Path(self.policy.hooks_root) == common/"hooks", "default repository hook root differs")
        return git, metadata, common, selected

    def _hooks(self):
        fd = directory_fd(self.policy.hooks_root)
        result = {}
        try:
            for name in os.listdir(fd):
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if name.endswith(".sample") or not info.st_mode & 0o111: continue
                require(name in dict(self.policy.hooks), "unfrozen executable hook")
                handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                try:
                    st = os.fstat(handle)
                    require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_size <= 1048576,
                            "hook is not a bounded regular input")
                    raw = os.read(handle, 1048577)
                    after = os.fstat(handle)
                    stamp = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
                    require(stamp(st) == stamp(after), "repository hook changed while reading")
                    require(len(raw) == st.st_size and hashlib.sha256(raw).hexdigest() == dict(self.policy.hooks)[name],
                            "repository hook changed")
                    result[name] = raw
                finally: os.close(handle)
            require(set(result) == set(dict(self.policy.hooks)), "approved repository hook missing")
            return result
        finally: os.close(fd)

    def __call__(self, cycle):
        require(cycle.plan.identity.task_id == self.draft.task_id and cycle.plan.base_sha == self.draft.base_sha
                and cycle.plan.hygiene_sha256 == self.policy.hash, "local commit work binding mismatch")
        if cycle.phase in {WorkPhase.HANDOFF, WorkPhase.FINISHED}:
            return parse_artifact(cycle.artifact)
        require(cycle.phase is WorkPhase.HYGIENE and cycle.plan.identity.task_id == self.draft.task_id
                and cycle.plan.base_sha == self.draft.base_sha
                and cycle.plan.hygiene_sha256 == self.policy.hash, "local commit work binding mismatch")
        git, metadata, common, configuration = self._repository(cycle)
        source = cycle.verify_scope()
        require(digest(source) == cycle.verified_tree, "local commit tree differs from tested bytes")
        hooks = self._hooks(); self.policy.environment.verify_inputs()
        events=cycle._events()
        retired={e["private_repository"] for e in events if e["event"]=="work_local_commit_invalidated"}
        old = [e for e in events if e["event"] == "work_local_commit_ready" and e["private_repository"] not in retired]
        pending = [e for e in events if e["event"] == "work_local_commit_requested" and e["private_repository"] not in retired]
        if old:
            record = old[-1]; private = Path(record["private_repository"])
            require(private.parent == self.storage and private.resolve(strict=True) == private,
                    "local commit recovery source changed")
            commit = record["commit_sha"]
        elif pending:
            record = pending[-1]; private = Path(record["private_repository"])
            require(private.parent == self.storage and private.resolve(strict=True) == private,
                    "local commit recovery source changed")
            try:
                require(private_file(private/"work"/".git"/"objects"/"info"/"alternates", 4096)
                        == (str(common/"objects")+"\n").encode(), "hook changed object source")
                commit = read_only_git(private/"work")(["rev-parse", "HEAD"]).strip()
                require(commit != self.draft.base_sha
                        and read_only_git(private/"work")(["rev-parse", "HEAD^"]).strip() == self.draft.base_sha,
                        "interrupted local commit has no proven result")
                require(tree_snapshot(private/"work", git=read_only_git(private/"work")) == source,
                        "interrupted hook changed tested inputs")
            except Exception as exc:
                raise EvidenceUnavailable("local commit delivery unknown; do not repeat hooks") from exc
            cycle._record("local_commit_ready", private_repository=str(private), commit_sha=commit,
                          tree_sha256=cycle.verified_tree, policy_sha256=self.policy.hash)
        else:
            require(git(["rev-parse", "HEAD"]).strip() == self.draft.base_sha, "local commit base changed")
            require(not git(["diff", "--cached", "--name-only", "-z", self.draft.base_sha]),
                    "foreign staged work must be preserved")
            private = Path(tempfile.mkdtemp(prefix="commit-", dir=self.storage))
            work = private/"work"; work.mkdir(mode=0o700)
            approved = private/"hooks"; approved.mkdir(mode=0o700)
            directory = directory_fd(cycle.root)
            try:
                for name, row in source.items():
                    require_work_time()
                    handle = _open_relative(directory, name)
                    try:
                        data = bytearray()
                        while len(data) <= 67108864:
                            require_work_time()
                            part = os.read(handle, 65536)
                            if not part: break
                            data.extend(part)
                        require(hashlib.sha256(data).hexdigest() == row["sha256"], "commit source changed")
                    finally: os.close(handle)
                    target = work/name; target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data); target.chmod(row["mode"])
            finally: os.close(directory)
            for name, data in hooks.items():
                (approved/name).write_bytes(data); (approved/name).chmod(0o500)
            from .verification_binding import commit_footer
            cfg = {"timeout": self.policy.timeout_seconds, "configuration": configuration,
                   "memory_bytes":self.policy.environment.memory_bytes, "max_processes":self.policy.max_processes,
                   "policy_sha256":self.policy.hash, "tree_sha256":cycle.verified_tree, "inventory":source,
                   "host_namespaces":{kind:os.readlink("/proc/self/ns/"+kind) for kind in ("pid","mnt","net")},
                   "object_source":str(common/"objects"),
                   "branch": self.draft.branch, "base": self.draft.base_sha,
                   "changed": sorted(name for name in set(source)|set(cycle.baseline)
                                     if source.get(name) != cycle.baseline.get(name)),
                   "message": cycle.plan.purpose + "\n\n" + commit_footer(self.completion_plan) + "\n"}
            require(cfg["changed"], "empty local commit is not an implementation artifact")
            dotgit = work/".git"; (dotgit/"objects"/"info").mkdir(parents=True, mode=0o700)
            (dotgit/"hooks").mkdir(mode=0o700)
            (dotgit/"objects"/"pack").mkdir(mode=0o700)
            branch = dotgit/"refs"/"heads"/self.draft.branch
            branch.parent.mkdir(parents=True, mode=0o700); branch.write_text(self.draft.base_sha+"\n")
            (dotgit/"HEAD").write_text("ref: refs/heads/"+self.draft.branch+"\n")
            (dotgit/"objects"/"info"/"alternates").write_text(str(common/"objects")+"\n")
            lines = ["[core]", "repositoryformatversion = 0", "bare = false", "logallrefupdates = true",
                     "hooksPath = /workspace/.git/hooks"]
            for key, value in configuration.items():
                section, name = key.split(".", 1)
                require(not any(ord(character) < 32 for character in value), "commit config contains control bytes")
                lines.extend(["["+section+"]", name+" = "+json.dumps(value, ensure_ascii=False)])
            (dotgit/"config").write_text("\n".join(lines)+"\n"); (dotgit/"config").chmod(0o400)
            (private/"index-original").write_bytes(private_file(metadata/"index", 2097152))
            cycle._record("local_commit_requested", private_repository=str(private),
                          tree_sha256=cycle.verified_tree, policy_sha256=self.policy.hash)
            # Alternates use the same canonical path inside the isolated namespace.
            objects = directory_fd(common/"objects"); work_fd = directory_fd(work); hooks_fd = directory_fd(approved)
            config_fd = os.open(dotgit/"config", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            filter_fd = network_denial_filter()
            runtime = None
            try:
                from .check_runtime import FrozenCheckRuntime
                runtime = FrozenCheckRuntime(self.policy.environment,self.storage,writable_roots=(cycle.root,))
                argv = ["/usr/bin/bwrap", "--die-with-parent", "--unshare-user", "--uid", "65534", "--gid", "65534",
                        "--disable-userns", "--unshare-pid", "--unshare-net", "--unshare-ipc",
                        "--unshare-uts", "--cap-drop", "ALL", "--tmpfs", "/", *runtime.arguments(),
                        "--dir", "/home", "--dir", "/run", "--dir", "/etc", "--proc", "/proc",
                        "--dev", "/dev", "--remount-ro", "/dev", "--dir", "/empty-template",
                        "--dir", str(common/"objects"), "--dir", "/workspace", "--dir", "/input",
                        "--size", "16777216", "--tmpfs", "/tmp", "--remount-ro", "/",
                        "--ro-bind-fd", str(objects), str(common/"objects"),
                        "--ro-bind-fd", str(work_fd), "/input",
                        "--size", "134217728", "--tmpfs", "/workspace",
                        "--ro-bind-fd", str(hooks_fd), "/workspace/.git/hooks",
                        "--ro-bind-fd", str(config_fd), "/workspace/.git/config",
                        "--chdir", "/workspace", "--clearenv",
                        "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp",
                        "--setenv", "GIT_CONFIG_NOSYSTEM", "1", "--setenv", "GIT_CONFIG_GLOBAL", "/dev/null",
                        "--setenv", "GIT_LITERAL_PATHSPECS", "1", "--setenv", "LANG", "C.UTF-8",
                        "--seccomp", str(filter_fd), "--", "/usr/bin/python3", "-I", "-S", "-c", _BOOTSTRAP, canonical(cfg).decode()]
                output, status, limited, duration = HostCheckRunner._execute(
                    argv, self.policy, (objects, work_fd, hooks_fd, config_fd, filter_fd,runtime.fd))
                runtime.verify()
                require(status == 0 and not limited, "normal repository commit or hook failed in approved profile")
            finally:
                for handle in (objects, work_fd, hooks_fd, config_fd, filter_fd): os.close(handle)
                if runtime is not None: runtime.close()
            first, separator, tail = output.partition(b"\n")
            require(separator and first.startswith(b"HERDR_HYGIENE_ATTESTATION ") and len(first)<=8192,
                    "physical hygiene attestation unavailable")
            proof=json.loads(first[len(b"HERDR_HYGIENE_ATTESTATION "):])
            require(proof.get("policy_sha256")==self.policy.hash and proof.get("tree_sha256")==cycle.verified_tree
                    and proof.get("uid")==65534 and proof.get("max_processes")==self.policy.max_processes,
                    "physical hygiene attestation differs")
            rows=[row[len(b"HERDR_HYGIENE_EXPORT "):] for row in tail.splitlines()
                  if row.startswith(b"HERDR_HYGIENE_EXPORT ")]
            require(rows, "bounded hygiene export unavailable")
            exported=json.loads(rows[-1])
            if exported=={"status":"changed"}:
                cycle._record("local_commit_invalidated", private_repository=str(private),
                              tree_sha256=cycle.verified_tree, policy_sha256=self.policy.hash)
                cycle._record("invalidate", reason="commit_hook_changed_tested_content")
                cycle.verified_tree,cycle.verified_checks,cycle.phase=None,{},WorkPhase.VERIFY
                cycle.verification_open=True
                raise ValueError("commit hook invalidated tested content")
            require(set(exported)=={"status","commit","objects","index"} and exported["status"]=="committed"
                    and re.fullmatch("[0-9a-f]{40}",exported["commit"])
                    and isinstance(exported["objects"],dict) and len(exported["objects"])<=4096,
                    "hygiene export contract invalid")
            import base64
            total=0
            for name,value in exported["objects"].items():
                require(re.fullmatch("[0-9a-f]{2}/[0-9a-f]{38}",name) and isinstance(value,str),
                        "hygiene object export invalid")
                raw=base64.b64decode(value,validate=True);total+=len(raw)
                require(total<=67108864,"hygiene objects exceed bound")
                target=dotgit/"objects"/name;target.parent.mkdir(mode=0o700,exist_ok=True)
                with target.open("xb") as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
            index=base64.b64decode(exported["index"],validate=True)
            require(len(index)<=2097152,"hygiene index exceeds bound")
            (dotgit/"index").write_bytes(index)
            (dotgit/"refs"/"heads"/self.draft.branch).write_text(exported["commit"]+"\n")
            self.policy.environment.verify_inputs()
            commit = read_only_git(work)(["rev-parse", "HEAD"]).strip()
            require(read_only_git(work)(["rev-parse", "HEAD^"]).strip() == self.draft.base_sha, "hook changed commit ancestry")
            private_tree = tree_snapshot(work, git=read_only_git(work))
            if private_tree != source:
                cycle._record("local_commit_invalidated", private_repository=str(private),
                              tree_sha256=cycle.verified_tree, policy_sha256=self.policy.hash)
                cycle._record("invalidate", reason="commit_hook_changed_tested_content")
                cycle.verified_tree, cycle.verified_checks, cycle.phase = None, {}, WorkPhase.VERIFY
                cycle.verification_open = True
                raise ValueError("commit hook invalidated tested content")
            require(self._hooks() == hooks and cycle.verify_scope() == source, "commit inputs changed during hygiene")
            cycle._record("local_commit_ready", private_repository=str(private), commit_sha=commit,
                          tree_sha256=cycle.verified_tree, policy_sha256=self.policy.hash)
        work = private/"work"
        require(private_file(work/".git"/"objects"/"info"/"alternates", 4096)
                == (str(common/"objects")+"\n").encode(), "hook changed object source")
        require(not any((work/".git"/"objects"/"pack").iterdir()), "packed private outputs need another approved profile")
        private_git = read_only_git(work)
        private_manager = WorkspaceManager(work, git=private_git, worktrees_dir=work.parent,
                                           artifacts_dir=private/"artifacts")
        private_artifact = private_manager.seal(self.draft, work)
        require(private_artifact.commit_sha == commit, "private commit changed during recovery")
        verify_committed_bytes(private_artifact, work, private_git)
        from .verification_binding import verify_commit_binding
        verify_commit_binding(self.completion_plan, private_artifact,
                              {"sha": commit, "commit": {"message": private_git(["log", "-1", "--format=%B"])}})
        require(cycle.verify_scope() == source and digest(source) == cycle.verified_tree,
                "commit recovery tree changed")
        original_index = private_file(private/"index-original", 2097152)
        new_index = private_file(work/".git"/"index", 2097152)
        validated_index = private_file(metadata/"index", 2097152)
        require(validated_index in {original_index, new_index}, "foreign index changes must be preserved")
        self._publish_objects(work/".git"/"objects", common/"objects")
        ref = common/"refs"/"heads"/self.draft.branch
        parent = directory_fd(ref.parent)
        try:
            current = git(["rev-parse", "HEAD"]).strip()
            require(current in {self.draft.base_sha, commit}, "owned branch advanced during local commit")
            if current == self.draft.base_sha:
                # Managed worktree refs are loose, created by WorkspaceManager.
                publish_file(parent, ref.name, (commit+"\n").encode(),
                             expected=(self.draft.base_sha+"\n").encode())
        finally: os.close(parent)
        parent = directory_fd(metadata)
        try: publish_file(parent, "index", new_index, expected=validated_index)
        finally: os.close(parent)
        manager = WorkspaceManager(cycle.root, git=git, worktrees_dir=cycle.root.parent,
                                   artifacts_dir=self.storage/"artifacts")
        require_work_time()
        sealed = manager.seal(self.draft, cycle.root)
        verify_committed_bytes(sealed, cycle.root, git)
        cycle.committed(sealed)
        return sealed

    @staticmethod
    def _publish_objects(source, target):
        total = count = 0
        for directory in source.iterdir():
            if directory.name in {"info", "pack"}: continue
            require(re.fullmatch("[0-9a-f]{2}", directory.name) and directory.is_dir() and not directory.is_symlink(),
                    "private object directory invalid")
            destination = target/directory.name
            destination.mkdir(mode=0o700, exist_ok=True)
            parent = directory_fd(destination)
            try:
                for item in directory.iterdir():
                    require_work_time()
                    require(re.fullmatch("[0-9a-f]{38}", item.name), "private object name invalid")
                    compressed = private_file(item, 67108864)
                    decoder = zlib.decompressobj()
                    raw = decoder.decompress(compressed, 67108865)
                    total += len(raw); count += 1
                    require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
                            and total <= 67108864 and count <= 4096
                            and hashlib.sha1(raw).hexdigest() == directory.name+item.name,
                            "bounded content-addressed object required")
                    header, separator, content = raw.partition(b"\0")
                    kind, space, size = header.partition(b" ")
                    require(separator and space and kind in {b"blob", b"tree", b"commit"}
                            and size.isdigit() and int(size) == len(content), "Git object payload invalid")
                    from .evidence import EvidenceStore
                    fd, temporary = tempfile.mkstemp(prefix=".herdr-object-", dir=destination)
                    try:
                        pending = memoryview(compressed)
                        while pending:
                            require_work_time()
                            written = os.write(fd, pending); require(written > 0, "object write stalled")
                            pending = pending[written:]
                        os.fchmod(fd, 0o444); os.fsync(fd)
                        try:
                            EvidenceStore._exclusive_publish(Path(temporary), destination/item.name)
                        except FileExistsError:
                            existing = private_file(destination/item.name, 67108864)
                            old = zlib.decompressobj(); decoded = old.decompress(existing, 67108865)
                            require(old.eof and not old.unused_data and not old.unconsumed_tail
                                    and hashlib.sha1(decoded).hexdigest() == directory.name+item.name,
                                    "existing content-addressed object differs")
                        os.fsync(parent)
                    finally:
                        os.close(fd)
                        try: os.unlink(temporary)
                        except FileNotFoundError: pass
            finally: os.close(parent)


def directory_fd_close(path):
    fd = directory_fd(path); os.close(fd)
