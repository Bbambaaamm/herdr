"""Separate trusted-init proof; kernel case is a disposable component only."""
import ast
import copy
import os
from pathlib import Path
import stat
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def module():
    if sys.platform == "linux":
        from herdr import ownership_release
        return ownership_release
    # Windows cannot import the Unix ownership package. Execute the exact
    # module body with only its two relative dependency imports substituted;
    # OS observations below are synthetic metadata, never kernel acceptance.
    source = ROOT / "herdr/ownership_release.py"
    tree = ast.parse(source.read_bytes())
    tree.body = [node for node in tree.body
                 if not isinstance(node, ast.ImportFrom) or not node.level]
    loaded = types.ModuleType("namespace_proof_v2_portable")
    class OwnershipError(ValueError):
        pass
    def require(ok, code):
        if not ok:
            raise OwnershipError(code)
    loaded.OwnershipError = OwnershipError
    loaded.require = require
    exec(compile(tree, str(source), "exec"), loaded.__dict__)
    return loaded


@pytest.fixture
def observations(module, monkeypatch):
    payload = {"pid": 43, "start_ticks": 101, "ppid": 42, "ids": (43, 2),
               "uids": (1001,) * 4, "cgroup": b"0::/owned-unit\n",
               "namespace": "pid:[222]", "mount_namespace": "mnt:[333]",
               "executable": (10, 30)}
    init = dict(payload, pid=42, start_ticks=100, ppid=41, ids=(42, 1), executable=(10, 20))
    values = {43: payload, 42: init}
    calls = []
    def snapshot(pid):
        calls.append(pid)
        return copy.deepcopy(values[pid])
    info = types.SimpleNamespace(st_dev=10, st_ino=20, st_uid=0,
        st_nlink=1, st_mode=stat.S_IFREG | 0o755)
    closes = []
    monkeypatch.setattr(module, "_process_snapshot", snapshot)
    monkeypatch.setattr(module, "_open_trusted_bwrap", lambda: (99, (10, 20)))
    monkeypatch.setattr(module, "os", types.SimpleNamespace(getuid=lambda:1001,
        readlink=lambda path:"pid:[111]" if str(path).endswith("/pid") else "mnt:[112]",
        fstat=lambda fd:info, close=closes.append))
    monkeypatch.setattr(module, "Path", lambda path:types.SimpleNamespace(lstat=lambda:info))
    return values, calls, closes, info


def test_capture_actual_verified_payload_has_separate_init(module, observations):
    values, calls, closes, _ = observations
    proof = module.capture_namespace_lifetime(43)
    assert proof == {"version":2, "pid":43, "start_ticks":101,
        "namespace":"pid:[222]", "init_pid":42, "init_start_ticks":100}
    assert calls == [43,42,43,42] and closes == [99]
    assert module.validate_namespace_lifetime(proof) == proof


@pytest.mark.parametrize("fault", ["payload_pid1", "wrong_init_pid", "wrong_init_executable",
    "wrong_uid", "wrong_cgroup", "wrong_pidns", "wrong_mntns", "init_not_pid1",
    "host_pidns", "changed_payload_ticks", "changed_init_ticks", "writable_binary"])
def test_capture_denies_untrusted_or_changing_binding(module, observations, monkeypatch, fault):
    values, calls, closes, info = observations
    if fault == "payload_pid1": values[43]["ids"] = (43,1)
    elif fault == "wrong_init_pid": values[42]["ppid"] = 43
    elif fault == "wrong_init_executable": values[42]["executable"] = (10,21)
    elif fault == "wrong_uid": values[42]["uids"] = (1002,) * 4
    elif fault == "wrong_cgroup": values[42]["cgroup"] = b"0::/another-unit\n"
    elif fault == "wrong_pidns": values[42]["namespace"] = "pid:[444]"
    elif fault == "wrong_mntns": values[42]["mount_namespace"] = "mnt:[444]"
    elif fault == "init_not_pid1": values[42]["ids"] = (42,3)
    elif fault == "host_pidns": values[43]["namespace"] = "pid:[111]"
    elif fault == "writable_binary": info.st_mode |= 0o020
    else:
        original = module._process_snapshot
        target = 43 if fault == "changed_payload_ticks" else 42
        def changed(pid):
            result = original(pid)
            if len(calls) >= 3 and pid == target:
                result["start_ticks"] += 1
            return result
        monkeypatch.setattr(module, "_process_snapshot", changed)
    with pytest.raises(module.OwnershipError):
        module.capture_namespace_lifetime(43)


@pytest.mark.parametrize("fault", [None, "alias", "ancestor_uid", "ancestor_writable",
    "source_uid", "source_writable", "source_link"])
def test_root_bwrap_binary_source_is_actually_checked(module, monkeypatch, fault):
    ancestor = types.SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
    info = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o755, st_uid=0,
        st_nlink=1, st_dev=10, st_ino=20)
    if fault == "ancestor_uid": ancestor.st_uid=1001
    elif fault == "ancestor_writable": ancestor.st_mode |= 0o020
    elif fault == "source_uid": info.st_uid=1001
    elif fault == "source_writable": info.st_mode |= 0o020
    elif fault == "source_link": info.st_nlink=2
    path = types.SimpleNamespace(parents=[types.SimpleNamespace(lstat=lambda:ancestor)])
    path.resolve=lambda strict:path if fault != "alias" else object()
    closed=[]
    monkeypatch.setattr(module,"Path",lambda name:path)
    monkeypatch.setattr(module,"os",types.SimpleNamespace(O_PATH=1,O_NOFOLLOW=2,O_CLOEXEC=4,
        open=lambda p,flags:99,fstat=lambda fd:info,close=closed.append))
    if fault is None:
        assert module._open_trusted_bwrap()==(99,(10,20)) and not closed
    else:
        with pytest.raises(module.OwnershipError): module._open_trusted_bwrap()
        if fault.startswith("source_"): assert closed==[99]


@pytest.mark.parametrize("version", [1,2])
def test_v1_read_compatibility_and_v2_tracks_only_its_real_init(module, monkeypatch, version):
    proof={"version":version,"pid":43,"start_ticks":101,"namespace":"pid:[222]"}
    if version==2: proof.update(init_pid=42,init_start_ticks=100)
    calls=[]
    def current(pid):
        calls.append(pid)
        return "S", 100 if pid==42 else 101
    monkeypatch.setattr(module,"process_identity",current)
    assert module.validate_namespace_lifetime(proof)==proof
    assert not module.namespace_exited(proof)
    assert calls==[42 if version==2 else 43]
    monkeypatch.setattr(module,"process_identity",lambda pid:("Z",100 if pid==42 else 101))
    assert module.namespace_exited(proof)


@pytest.mark.parametrize("change", [{"version":True},{"version":3},{"init_pid":43},
    {"init_pid":True},{"init_start_ticks":0},{"unexpected":1},{"pid":False}])
def test_closed_v2_proof_rejects_ambiguity(module, change):
    proof={"version":2,"pid":43,"start_ticks":101,"namespace":"pid:[222]",
           "init_pid":42,"init_start_ticks":100}
    proof.update(change)
    with pytest.raises(module.OwnershipError): module.validate_namespace_lifetime(proof)


@pytest.mark.skipif(sys.platform!="linux",reason="UNEXECUTED: real Linux namespace/epoch component")
def test_real_bash_payload_v2_trusted_reaper_custody(tmp_path):
    # Collection against baseline169 needs no new helper import. Baseline must
    # reproduce the real capture(BashPID2) denial; v2 must pass this exact case.
    import fcntl
    import select
    import shlex
    import shutil
    import signal
    import subprocess
    import time
    from herdr.ownership_epoch import legacy_admission_guard,custodial_command
    from herdr.ownership_release import capture_namespace_lifetime,namespace_exited
    executable=shutil.which("bwrap")
    if not executable:
        if os.environ.get("HERDR_REQUIRE_PID1_KERNEL")=="1":pytest.fail("required bwrap absent")
        pytest.skip("bwrap unavailable; no physical acceptance")
    source=ROOT/"agent-stack/bin/agent_durable_sandbox.py"
    command_node=next(node for node in ast.parse(source.read_bytes()).body
        if isinstance(node,ast.FunctionDef) and node.name=="command")
    assignment=next(node for node in command_node.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id=="args" for target in node.targets))
    branch=next(node.value for node in assignment.value.elts if isinstance(node,ast.Starred)
        and isinstance(node.value,ast.IfExp) and any(isinstance(value,ast.Name)
            and value.id=="admission_root" for value in ast.walk(node.value.test)))
    flags=eval(compile(ast.Expression(branch),str(source),"eval"),{"admission_root":"owned-epoch"})
    assert flags==["--die-with-parent"]
    epoch=tmp_path/"epoch";epoch.mkdir(mode=0o700)
    home=tmp_path/"home";home.mkdir();marker="proof-v2-component-"+str(os.getpid())
    command=[executable,"--unshare-user","--unshare-net","--unshare-pid",*flags,
        "--ro-bind","/","/","--tmpfs","/home","--tmpfs","/root","--tmpfs","/tmp",
        "--proc","/proc","--dev","/dev","--dir","/home/component","--clearenv",
        "--setenv","HOME","/home/component","--setenv","PATH","/usr/bin:/bin",
        "--setenv","HERDR_DURABLE_TASK_PANE",marker,"--chdir","/home/component",
        "--","/bin/bash","--noprofile","--norc","-i"]
    process=None;handle=lock=None
    def descendants(pid):
        found=[];todo=[pid]
        while todo:
            current=todo.pop()
            try:children=list(map(int,Path(f"/proc/{current}/task/{current}/children").read_text().split()))
            except (FileNotFoundError,ProcessLookupError):children=[]
            found.extend(children);todo.extend(children);assert len(found)<=32
        return found
    def alive(pid):
        try:return Path(f"/proc/{pid}/stat").read_text().rsplit(") ",1)[1].split()[0]!="Z"
        except (FileNotFoundError,ProcessLookupError):return False
    try:
        with legacy_admission_guard(epoch) as binding:
            process=subprocess.Popen(custodial_command(command,binding),stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={"HOME":str(home),"PATH":"/usr/bin:/bin"})
            handle=os.pidfd_open(process.pid)
            body="import subprocess,sys,time;subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(20)']);print('READY',flush=True);time.sleep(20)"
            process.stdin.write(("/usr/bin/python3 -u -I -c "+shlex.quote(body)+"\n").encode());process.stdin.flush()
            deadline=time.monotonic()+8
            while True:
                if process.poll() is not None:
                    error=process.stderr.read(8192).decode(errors="replace")
                    if os.environ.get("HERDR_REQUIRE_PID1_KERNEL")!="1" and ("Operation not permitted" in error or "Creating new namespace failed" in error):pytest.skip("unprivileged namespace denied")
                    pytest.fail("component startup failed: "+error)
                if select.select([process.stdout],[],[],.1)[0] and process.stdout.readline().strip()==b"READY":break
                assert time.monotonic()<deadline
        owned=descendants(process.pid);payloads=[]
        for pid in owned:
            status=Path(f"/proc/{pid}/status").read_text()
            ids=next((line.split()[1:] for line in status.splitlines() if line.startswith("NSpid:")),[])
            if len(ids)>=2 and ids[-1]=="2":payloads.append(pid)
        assert len(payloads)==1
        payload=payloads[0]
        assert Path(os.readlink(f"/proc/{payload}/exe")).resolve()==Path("/bin/bash").resolve()
        assert ("HERDR_DURABLE_TASK_PANE="+marker).encode() in Path(f"/proc/{payload}/environ").read_bytes().split(b"\0")
        proof=capture_namespace_lifetime(payload)
        assert proof["version"]==2 and proof["pid"]==payload and proof["init_pid"] in owned
        assert not namespace_exited(proof)
        lock=os.open(epoch/"worker.lock",os.O_RDWR)
        with pytest.raises(BlockingIOError):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        signal.pidfd_send_signal(handle,signal.SIGKILL);process.wait(timeout=5)
        deadline=time.monotonic()+5
        while not (namespace_exited(proof) and all(not alive(pid) for pid in owned)):
            assert time.monotonic()<deadline;time.sleep(.02)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    finally:
        if process is not None and process.poll() is None:
            if handle is not None:signal.pidfd_send_signal(handle,signal.SIGKILL)
            else:process.kill()  # Only this unreaped owned Popen if pidfd open failed.
            process.wait(timeout=5)
        if handle is not None:os.close(handle)
        if lock is not None:os.close(lock)
