"""Real disposable Git/export/publication; synthetic namespace launch only.

No factory_fixture, HostCheckRunner.__call__, bootstrap, hook, SDK or bwrap runs.
The original collector selectors/caps and all hygiene validators remain real.
Root must execute only this module in its guarded unprivileged unit workspace.
"""
import base64
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from types import SimpleNamespace

import pytest

import agent_platform_dashboard.production_sources as projections
from herdr import check_runner, evidence, work_hygiene as hygiene
from herdr.check_runner import CheckEnvironment, HostCheckRunner
from herdr.evidence import EvidenceUnavailable, digest
from herdr.scheduler import AuditLog
from herdr.security import InvocationIdentity
from herdr.work_cycle import CheckResult, FileScope, ValidationCheck, WorkContractError, WorkCycle, WorkPhase, WorkPlan
from herdr.work_hygiene import HostLocalCommitter, LocalCommitPolicy
from herdr.workspace import ArtifactRef, WorkspaceManager

GIT = "/usr/bin/git"
OLD_CAP, DEFAULT_CAP, INDEX_CAP = 65536, 1048576, 2097152
MAX_FRAME = 4 * 1048576


class PipeProcess:
    """Nonnumeric PID cannot accidentally address any kernel process/group."""
    def __init__(self, data, status, owner):
        assert len(data) <= MAX_FRAME
        self.pid = object()
        self.returncode = None
        self.status = status
        self.stop = threading.Event()
        self.error = None
        reader, writer = os.pipe()
        os.set_blocking(writer, False)
        self.stdout = os.fdopen(reader, "rb", buffering=0)
        def write():
            try:
                remaining = memoryview(data)
                while remaining and not self.stop.is_set():
                    try:written = os.write(writer, remaining[:8192])
                    except BlockingIOError:
                        self.stop.wait(0.002);continue
                    assert written > 0
                    remaining = remaining[written:]
            except BrokenPipeError:
                pass
            except BaseException as error:
                self.error = error
            finally:os.close(writer)
        self.writer = threading.Thread(target=write, daemon=True)
        owner.processes[self.pid] = self
        self.writer.start()

    def wait(self, timeout):
        self.writer.join(timeout)
        assert not self.writer.is_alive(), "finite pipe writer did not stop"
        assert self.error is None
        self.returncode = self.status
        return self.returncode


class ProcessOS:
    """Module-local facade; fake process controls never delegate to real OS."""
    def __init__(self, owner):self.owner = owner
    def __getattr__(self, name):return getattr(os, name)
    def killpg(self, pid, sig):
        assert not isinstance(pid, int) and pid in self.owner.processes
        assert sig == 9
        self.owner.processes[pid].stop.set()
        self.owner.signals.append(pid)
    def kill(self, *args):raise AssertionError("unexpected fake kill syscall")
    def getpgid(self, *args):raise AssertionError("unexpected fake getpgid syscall")
    def waitpid(self, *args):raise AssertionError("unexpected fake waitpid syscall")


class Boundary:
    """Exact namespace argv -> actual private Git, never a native launcher."""
    def __init__(self, root, monkeypatch):
        self.root = root.resolve()
        self.home = self.root / "home";self.home.mkdir()
        self.empty_hooks = self.root / "empty-hooks";self.empty_hooks.mkdir()
        self.processes = {};self.signals = [];self.filters = set()
        self.launches = 0;self.frames = [];self.captures = [];self.fault = None
        self.environment = {"PATH": "/usr/bin:/bin", "HOME": str(self.home), "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "GIT_LITERAL_PATHSPECS": "1"}
        # A synthetic launcher availability observation; no file is installed.
        real_path_type = type(Path())
        class LaunchPath(real_path_type):
            def is_file(self):
                return True if str(self) == "/usr/bin/bwrap" else super().is_file()
        monkeypatch.setattr(evidence, "Path", LaunchPath)
        monkeypatch.setattr(evidence, "network_denial_filter", self.filter_fd)
        monkeypatch.setattr(hygiene, "network_denial_filter", self.filter_fd)
        self.original_command = evidence.artifact_command
        monkeypatch.setattr(evidence, "artifact_command", self.metadata_launch)
        os_facade = ProcessOS(self)
        monkeypatch.setattr(check_runner, "os", os_facade)
        monkeypatch.setattr(projections, "os", os_facade)
        constants = {name: getattr(subprocess, name) for name in ("PIPE", "STDOUT", "DEVNULL", "TimeoutExpired", "SubprocessError")}
        monkeypatch.setattr(check_runner, "subprocess", SimpleNamespace(Popen=self.hygiene_launch, **constants))
        monkeypatch.setattr(projections, "subprocess", SimpleNamespace(Popen=self.git_launch, **constants))

    def owned(self, root):
        root = Path(root).resolve(strict=True)
        assert root.is_dir() and root.is_relative_to(self.root)
        return root

    def git(self, root, *args, check=True):
        root = self.owned(root)
        assert args and not set(args) & {"push", "fetch", "pull", "ls-remote", "submodule", "remote"}
        # These are the ONLY real child processes in the tests: fixed Git, owned
        # synthetic repos, private environment, explicit empty hooks, no network.
        command = [GIT, "--no-optional-locks", "--no-replace-objects", "-c", "core.hooksPath="+str(self.empty_hooks),
            "-c", "core.fsmonitor=false", "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-C", str(root), *args]
        result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
            env=self.environment, timeout=10, check=False)
        assert len(result.stdout) <= 2_000_000 and len(result.stderr) <= 65536
        if check:assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
        return result

    def filter_fd(self, **kwargs):
        # Never loaded: a launch-boundary input descriptor, not kernel evidence.
        fd = os.open(os.devnull, os.O_RDONLY)
        self.filters.add(fd)
        return fd

    def metadata_launch(self, argv, *, limit, timeout, pass_fds):
        assert limit == 2_000_000 and 0 < timeout <= 30 and len(pass_fds) == 1
        fd = pass_fds[0];assert fd in self.filters
        prefix = ["/usr/bin/bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
            "--unshare-pid", "--unshare-net", "--seccomp", str(fd), "--tmpfs", "/tmp", "--clearenv",
            "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp", "--"]
        assert argv[:len(prefix)] == prefix
        inner = argv[len(prefix):]
        assert inner[:9] == [GIT, "--no-optional-locks", "--no-replace-objects", "-c", "core.fsmonitor=false",
            "-c", "core.hooksPath=/dev/null", "-c", "diff.external="]
        assert inner[9] == "-C";self.owned(inner[10])
        # Preserve the real bounded metadata collector. Its Popen below gets
        # only inner Git, then emits actual Git bytes through the finite pipe.
        return self.original_command(inner, limit=limit, timeout=timeout)

    def git_launch(self, argv, **kwargs):
        assert argv[:10] == [GIT, "--no-optional-locks", "--no-replace-objects", "-c", "core.fsmonitor=false",
            "-c", "core.hooksPath=/dev/null", "-c", "diff.external=", "-C"]
        self.owned(argv[10])
        assert kwargs["start_new_session"] and kwargs["close_fds"]
        assert kwargs["env"] == projections.SAFE_ENV and kwargs["pass_fds"] == ()
        # Execute the exact protected read-only Git command, with a private
        # fixture HOME. The shared stdlib subprocess module is never patched.
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
            env=self.environment, timeout=10, check=False)
        assert len(result.stdout) <= 2_000_000 and len(result.stderr) <= 65536
        return PipeProcess(result.stdout, result.returncode, self)

    def hygiene_launch(self, argv, **kwargs):
        assert argv[0] == "/usr/bin/bwrap" and argv[-2] == hygiene._BOOTSTRAP
        assert kwargs["start_new_session"] and kwargs["close_fds"]
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
        cfg = json.loads(argv[-1]);fds = kwargs["pass_fds"]
        assert len(fds) == 6 and fds[4] in self.filters
        assert cfg["changed"] == ["result.py"] and cfg["max_processes"] == 8
        assert cfg["timeout"] == 60 and cfg["memory_bytes"] <= 536870912
        input_root = self.owned(os.readlink("/proc/self/fd/"+str(fds[1])))
        objects = self.owned(os.readlink("/proc/self/fd/"+str(fds[0])))
        self.owned(os.readlink("/proc/self/fd/"+str(fds[2])))
        config = Path(os.readlink("/proc/self/fd/"+str(fds[3]))).resolve(strict=True)
        assert config.is_relative_to(self.root) and config.is_file()
        self.owned(os.readlink("/proc/self/fd/"+str(fds[5])))
        expected = ["/usr/bin/bwrap", "--die-with-parent", "--unshare-user", "--uid", "65534", "--gid", "65534",
            "--disable-userns", "--unshare-pid", "--unshare-net", "--unshare-ipc", "--unshare-uts",
            "--cap-drop", "ALL", "--tmpfs", "/", "--dir", "/usr", "--dir", "/usr/bin",
            "--ro-bind", f"/proc/self/fd/{fds[5]}/usr/bin/git", GIT,
            "--dir", "/home", "--dir", "/run", "--dir", "/etc", "--proc", "/proc", "--dev", "/dev",
            "--remount-ro", "/dev", "--dir", "/empty-template", "--dir", str(objects), "--dir", "/workspace",
            "--dir", "/input", "--size", "16777216", "--tmpfs", "/tmp", "--remount-ro", "/",
            "--ro-bind-fd", str(fds[0]), str(objects), "--ro-bind-fd", str(fds[1]), "/input",
            "--size", "134217728", "--tmpfs", "/workspace",
            "--ro-bind-fd", str(fds[2]), "/workspace/.git/hooks",
            "--ro-bind-fd", str(fds[3]), "/workspace/.git/config", "--chdir", "/workspace", "--clearenv",
            "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp",
            "--setenv", "GIT_CONFIG_NOSYSTEM", "1", "--setenv", "GIT_CONFIG_GLOBAL", "/dev/null",
            "--setenv", "GIT_LITERAL_PATHSPECS", "1", "--setenv", "LANG", "C.UTF-8",
            "--seccomp", str(fds[4]), "--", str(Path("/usr/bin/python3").resolve()),
            "-I", "-S", "-c", hygiene._BOOTSTRAP, argv[-1]]
        assert argv == expected
        self.launches += 1
        producer = self.root / ("producer-"+str(self.launches))
        shutil.copytree(input_root, producer)
        # Do not execute _BOOTSTRAP, copied hooks or arbitrary configured code.
        self.git(producer, "read-tree", cfg["base"])
        self.git(producer, "add", "--", *cfg["changed"])
        self.git(producer, "commit", "-qm", cfg["message"])
        commit = self.git(producer, "rev-parse", "HEAD").stdout.decode().strip()
        objects = {}
        for item in (producer/".git/objects").glob("??/*"):
            assert item.is_file() and item.parent.name not in {"info", "pack"}
            objects[item.parent.name+"/"+item.name] = base64.b64encode(item.read_bytes()).decode()
        index = (producer/".git/index").read_bytes()
        exported = {"status": "committed", "commit": commit, "objects": objects,
            "index": base64.b64encode(index).decode()}
        if self.fault == "oversized_index":exported["index"] = base64.b64encode(b"x"*(INDEX_CAP+1)).decode()
        if self.fault == "malformed_export":exported["unexpected"] = True
        proof = {"policy_sha256": cfg["policy_sha256"], "tree_sha256": cfg["tree_sha256"],
            "uid": 65534, "max_processes": cfg["max_processes"]}
        # Synthetic launch receipt only. It is never physical isolation evidence.
        frame = b"HERDR_HYGIENE_ATTESTATION "+json.dumps(proof).encode()+b"\nHERDR_HYGIENE_EXPORT "+json.dumps(exported,sort_keys=True,separators=(",", ":")).encode()+b"\n"
        self.captures.append({"index": index, "commit": commit})
        self.frames.append({"index_bytes": len(index), "encoded_index_bytes": len(base64.b64encode(index)), "frame_bytes": len(frame)})
        return PipeProcess(frame, 0, self)

    def assert_reaped(self):
        for process in self.processes.values():
            assert not process.writer.is_alive() and process.stdout.closed


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    value = Boundary(tmp_path, monkeypatch)
    yield value
    value.assert_reaped()


def prepared(boundary, *, padding=0, cap=None):
    root = boundary.root / "work";root.mkdir()
    boundary.git(root, "init", "-q")
    boundary.git(root, "config", "user.name", "Disposable source fixture")
    boundary.git(root, "config", "user.email", "fixture@example.invalid")
    (root/"result.py").write_text("def approved():\n    return 1\n")
    (root/"foreign.txt").write_text("preserve exact foreign bytes\n")
    for n in range(padding):(root/(f"padding-{n:04d}-"+"x"*64+".txt")).write_text("unchanged\n")
    boundary.git(root, "add", ".");boundary.git(root, "commit", "-qm", "baseline")
    base = boundary.git(root, "rev-parse", "HEAD").stdout.decode().strip()
    identity = InvocationIdentity("github:org/repo", "worker", "parent", "parent-task", "task", "run", 1)
    branch = WorkspaceManager(root).branch_name(86, identity.task_id, 1, base)
    boundary.git(root, "branch", "-m", branch)
    environment = CheckEnvironment("synthetic-launch-git-1", ((GIT, hashlib.sha256(Path(GIT).read_bytes()).hexdigest()),), (GIT,))
    kwargs = {} if cap is None else {"output_bytes": cap}
    policy = LocalCommitPolicy("repo-policy-1", environment, hashlib.sha256((root/".git/config").read_bytes()).hexdigest(), str(root/".git/hooks"), (), **kwargs)
    plan = WorkPlan(identity, "spec-1", "a"*64, "policy-1", base, (FileScope("result.py"),),
        ("behavior",), (ValidationCheck("tests", (GIT, "--version"), ("behavior",)),),
        "b"*64, environment.hash, "d"*64, hygiene_sha256=policy.hash)
    log = AuditLog(boundary.root/"host/audit.jsonl")
    def git(args):return boundary.git(root,*args).stdout.decode()
    git.raw = lambda args:boundary.git(root,*args).stdout
    cycle = WorkCycle(plan, root, log, git=git)
    def synthetic_check(check, work, approved, tree):
        return CheckResult(check.id, approved.hash, approved.environment_sha256, tree, 0, "e"*64, False, 1, "f"*64)
    cycle.start(synthetic_check)
    (root/"result.py").write_text("def approved():\n    return 3\n")
    cycle.verify(synthetic_check)
    assert cycle.phase is WorkPhase.HYGIENE
    completion = {"identity": {"id": identity.task_id, "run_token": identity.run_token, "attempt": 1,
        "idempotency_key": "original", "fencing_token": identity.fencing_token},
        "base_sha": base, "spec_hash": plan.spec_sha256, "policy_hash": "f"*64}
    draft = ArtifactRef(identity.task_id,1,base,base,"",(),branch)
    info = root.stat()
    committer = HostLocalCommitter(policy,boundary.root/"host/commits",draft,
        completion_plan=completion,workspace_identity=f"{info.st_dev}:{info.st_ino}")
    return SimpleNamespace(committer=committer,cycle=cycle,root=root,log=log,policy=policy,plan=plan)


def retained(case):
    return {"head": (case.root/".git/refs/heads"/case.committer.draft.branch).read_bytes(),
        "index": (case.root/".git/index").read_bytes(), "foreign": (case.root/"foreign.txt").read_bytes()}


def test_real_large_index_export_default_and_replay(boundary):
    case = prepared(boundary,padding=400)
    artifact = case.committer(case.cycle)
    assert case.policy.output_bytes == DEFAULT_CAP
    frame = boundary.frames[0]
    assert frame["encoded_index_bytes"] > OLD_CAP and OLD_CAP < frame["frame_bytes"] < DEFAULT_CAP
    assert artifact.changed_files == ("result.py",) and case.cycle.phase is WorkPhase.HANDOFF
    assert (case.root/".git/index").read_bytes() == boundary.captures[0]["index"]
    assert artifact.commit_sha == boundary.captures[0]["commit"]
    assert boundary.git(case.root,"status","--porcelain").stdout == b""
    assert boundary.git(case.root,"show",artifact.commit_sha+":result.py").stdout == (case.root/"result.py").read_bytes()
    assert int(boundary.git(case.root,"rev-list","--count",artifact.base_sha+"..HEAD").stdout) == 1
    before = case.log._path.read_bytes()
    restored = WorkCycle(case.plan,case.root,case.log)
    assert case.committer(restored) == artifact
    assert boundary.launches == 1 and case.log._path.read_bytes() == before


def test_explicit_old_cap_preserves_ref_index_and_unknown_without_relaunch(boundary):
    case = prepared(boundary,padding=400,cap=OLD_CAP);before = retained(case)
    with pytest.raises(WorkContractError,match="hook failed"):
        case.committer(case.cycle)
    assert boundary.frames[0]["frame_bytes"] > OLD_CAP
    assert retained(case) == before and case.cycle.phase is WorkPhase.HYGIENE
    restored = WorkCycle(case.plan,case.root,case.log)
    with pytest.raises(EvidenceUnavailable,match="do not repeat hooks"):
        case.committer(restored)
    assert boundary.launches == 1 and retained(case) == before


@pytest.mark.parametrize("fault,cap,message", [("malformed_export",DEFAULT_CAP,"export contract"),
    ("oversized_index",MAX_FRAME,"index exceeds bound")])
def test_invalid_or_oversized_export_never_publishes_owned_ref_or_index(boundary,fault,cap,message):
    case=prepared(boundary,cap=cap);before=retained(case);boundary.fault=fault
    with pytest.raises(WorkContractError,match=message):case.committer(case.cycle)
    assert retained(case)==before and boundary.launches==1


@pytest.mark.parametrize("staged", [False, True])
def test_changed_policy_hash_and_foreign_changes_fail_before_launch(boundary, staged):
    case=prepared(boundary)
    wrong=HostLocalCommitter(replace(case.policy,output_bytes=1024),case.committer.storage,
        case.committer.draft,completion_plan=case.committer.completion_plan,workspace_identity=case.committer.workspace_identity)
    with pytest.raises(WorkContractError,match="binding mismatch"):wrong(case.cycle)
    (case.root/"foreign.txt").write_text("foreign bytes stay exact\n")
    if staged:boundary.git(case.root,"add","--","foreign.txt")
    before=retained(case)
    with pytest.raises(WorkContractError,match="foreign staged|approved work scope"):case.committer(case.cycle)
    assert retained(case)==before and boundary.launches==0


@pytest.mark.parametrize("extra,limited", [(0,False),(1,True)])
def test_real_collector_preserves_explicit_finite_output_boundary(boundary,monkeypatch,extra,limited):
    case=prepared(boundary)
    header=b"HERDR_HYGIENE_ATTESTATION {}\n"
    body=b"x"*(DEFAULT_CAP+extra)
    monkeypatch.setattr(check_runner,"subprocess",SimpleNamespace(Popen=lambda *a,**k:PipeProcess(header+body,0,boundary),
        DEVNULL=subprocess.DEVNULL,PIPE=subprocess.PIPE,STDOUT=subprocess.STDOUT,TimeoutExpired=subprocess.TimeoutExpired))
    output,status,truncated,_=HostCheckRunner._execute(["synthetic-launch"],replace(case.policy,output_bytes=DEFAULT_CAP),())
    assert truncated is limited and status==(124 if limited else 0)
    if not limited:assert output==header+body


@pytest.mark.parametrize("value", [True,1023,16777217,1.0])
def test_original_policy_range_stays_closed(boundary,value):
    case=prepared(boundary)
    with pytest.raises(WorkContractError,match="resource bounds"):
        replace(case.policy,output_bytes=value)


def test_fake_controls_reject_numeric_and_unknown_process_ids(boundary):
    control = ProcessOS(boundary)
    for invalid in (1, 123456, object()):
        with pytest.raises(AssertionError):control.killpg(invalid, 9)
    assert boundary.signals == []
