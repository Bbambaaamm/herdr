"""Pre-delivery result retry never truncates or adopts another fenced slot."""
from dataclasses import replace
import os
from pathlib import Path
import pytest
from herdr.security import SecurityError
from herdr.result_submission import reserve_empty_result
from tests.herdr.test_security import identity


def test_empty_reservation_retry_preserves_inode_and_full_binding(tmp_path):
    path=tmp_path/"result.json";invocation=identity()
    assert reserve_empty_result(path,invocation,"key")==path
    inode=path.stat().st_ino
    assert reserve_empty_result(path,invocation,"key")==path
    assert path.stat().st_ino==inode and path.read_bytes()==b""
    assert path.stat().st_mode&0o777==0o600


@pytest.mark.parametrize("fault",["fence","run","task","agent","parent","key","bytes",
    "unlabelled","mode","hardlink","symlink","intent"])
def test_invalid_result_reservation_requires_reconciliation(tmp_path,fault):
    path=tmp_path/"result.json";invocation=identity();key="key"
    reserve_empty_result(path,invocation,key)
    if fault=="fence":invocation=replace(invocation,fencing_token=invocation.fencing_token+1)
    elif fault=="run":invocation=replace(invocation,run_token="different")
    elif fault=="task":invocation=replace(invocation,task_id="different")
    elif fault=="agent":invocation=replace(invocation,agent_id="different")
    elif fault=="parent":invocation=replace(invocation,parent_task_id="different",parent_agent_id="other")
    elif fault=="key":key="different"
    elif fault=="bytes":path.write_bytes(b"preserved-result")
    elif fault=="unlabelled":os.removexattr(path,"user.herdr.result_reservation")
    elif fault=="mode":path.chmod(0o644)
    elif fault=="hardlink":os.link(path,tmp_path/"alias")
    elif fault=="symlink":path=tmp_path/"alias";path.symlink_to(tmp_path/"result.json")
    else:os.setxattr(path,"user.herdr.result_submission",b"interrupted-intent")
    original=(tmp_path/"result.json").read_bytes()
    with pytest.raises((ValueError,OSError)):
        reserve_empty_result(path,invocation,key)
    assert (tmp_path/"result.json").read_bytes()==original


def test_reservation_xattr_failure_retains_unlabelled_slot_and_denies_retry(tmp_path,monkeypatch):
    path=tmp_path/"result.json"
    def fail(*args):raise OSError("injected disk full")
    monkeypatch.setattr(os,"setxattr",fail)
    with pytest.raises(OSError,match="disk full"):reserve_empty_result(path,identity(),"key")
    assert path.exists() and path.read_bytes()==b""
    with pytest.raises(OSError):reserve_empty_result(path,identity(),"key")


def test_reservation_does_not_follow_mutable_parent_alias(tmp_path):
    parent=tmp_path/"parent";parent.mkdir()
    alias=tmp_path/"alias";alias.symlink_to(parent,target_is_directory=True)
    with pytest.raises(ValueError,match="symlinks"):
        reserve_empty_result(alias/"result.json",identity(),"key")
    assert not list(parent.iterdir())


@pytest.mark.parametrize("fault",[None,"bytes","intent","binding","mode","link","read-race","name","parent-alias"])
def test_fd_launcher_rechecks_late_same_uid_result_mutation(tmp_path,fault):
    import json,subprocess,sys,importlib.util
    from herdr.result_submission import ResultSlot,reservation_binding
    from herdr.private_mount_plan import PinnedLaunchPath
    path=reserve_empty_result(tmp_path/"result.json",identity(),"key")
    slot=ResultSlot.bind(path,identity(),"key")
    pin=PinnedLaunchPath(path,directory=False,expected=(slot.device,slot.inode),
                         reservation=reservation_binding(slot))
    try:
        descriptor=pin.descriptor()
        code="import os,sys;from pathlib import Path;p=Path(sys.argv[1]);action=sys.argv[2];"+{
            None:"pass", "read-race":"pass", "bytes":"p.write_bytes(b'late-write')",
            "intent":"os.setxattr(p,'user.herdr.result_submission',b'late-intent')",
            "binding":"os.setxattr(p,'user.herdr.result_reservation',b'changed')",
            "mode":"p.chmod(0o644)", "link":"os.link(p,str(p)+'.link')",
            "name":"p.rename(p.with_name('moved'));p.touch(mode=0o600)",
            "parent-alias":"d=p.parent;m=d.with_name(d.name+'.moved');d.rename(m);d.symlink_to(m,target_is_directory=True)"}[fault]
        subprocess.run([sys.executable,"-I","-c",code,str(path),str(fault)],check=True)
        if fault and fault!="read-race":
            with pytest.raises((ValueError,OSError,SecurityError)):pin.descriptor()
        root=Path(__file__).resolve().parents[2]
        spec=importlib.util.spec_from_file_location("reservation_fd_launcher",root/"agent-stack/bin/agent_durable_sandbox.py")
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        launcher=module._POLICY_FD_LAUNCHER
        if fault=="read-race":
            launcher=("import os\nfrom pathlib import Path\n_original=os.getxattr\n"
                "def _late(fd,name):\n"
                f" Path({str(path)!r}).write_bytes(b'write-during-check')\n"
                " return _original(fd,name)\nos.getxattr=_late\n"+launcher)
        proc=subprocess.run([sys.executable,"-I","-S","-c",launcher,
            json.dumps([descriptor]),"/usr/bin/bwrap","--bind-fd",str(pin.fd),str(path),"--","/bin/true"],
            capture_output=True,timeout=5)
        assert proc.returncode!=0
        expected=b"policy_fd_result_reservation_changed" if fault else b"policy_fd_private_plan_required"
        assert expected in proc.stderr
    finally:pin.close()


def test_reservation_checker_rejects_mutation_during_metadata_read(tmp_path,monkeypatch):
    from herdr.result_submission import ResultSlot,reservation_binding,verify_empty_reservation_fd
    path=reserve_empty_result(tmp_path/"result.json",identity(),"key")
    binding=reservation_binding(ResultSlot.bind(path,identity(),"key"))
    original=os.getxattr
    def late(fd,name):path.write_bytes(b"write during check");return original(fd,name)
    monkeypatch.setattr(os,"getxattr",late)
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC)
    try:
        with pytest.raises(ValueError,match="during check"):verify_empty_reservation_fd(fd,binding)
    finally:os.close(fd)


def test_complete_reserved_result_launcher_reaches_exec_with_exact_plan(tmp_path,monkeypatch):
    """Actual full launcher grammar; only root-record ownership and exec are doubles."""
    import hashlib,json,stat,sys
    from types import SimpleNamespace
    from herdr.result_submission import ResultSlot,reservation_binding
    from herdr.private_mount_plan import PinnedLaunchPath,request_for,VERSION,AUTHORITY_ROOT
    from herdr.policy_launch import IDENTITY_ENV
    from tests.herdr.test_private_profile_fd_bridge import bridge_module,fixture_snapshot
    sandbox=bridge_module();_,_,profile=fixture_snapshot(tmp_path)
    work=tmp_path/"workspace";work.mkdir()
    result=reserve_empty_result(tmp_path/"result.json",identity(),"key")
    slot=ResultSlot.bind(result,identity(),"key")
    workspace=PinnedLaunchPath(work,directory=True)
    pinned=PinnedLaunchPath(result,directory=False,reservation=reservation_binding(slot))
    raw_open,raw_close,raw_stat,raw_fstat=os.open,os.close,os.lstat,os.fstat
    opened=set();authority_fds=set();calls=[]
    try:
        entries=[workspace.descriptor(),pinned.descriptor(),*profile.fd_descriptors()]
        mounts=profile.mount_arguments()
        argv=["/usr/bin/bwrap","--ro-bind","/","/","--unshare-pid","--unshare-net",
            "--proc","/proc","--tmpfs","/tmp",*mounts[:-2],
            "--dir",str(work),"--chdir",str(work),"--bind-fd",str(workspace.fd),str(work),
            "--bind-fd",str(pinned.fd),str(result),*mounts[-2:],"--","/bin/true"]
        canonical=lambda value:json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
        plan=request_for(identity(),entries,argv);record=tmp_path/"approved-record";record.write_bytes(canonical(plan))
        authority=AUTHORITY_ROOT/(hashlib.sha256(canonical(identity().to_json())).hexdigest()+".json")
        envelope={"schema_version":VERSION,"authority":str(authority),
                  "authority_sha256":hashlib.sha256(canonical(plan)).hexdigest(),"entries":entries}
        fields=("st_dev","st_ino","st_size","st_mtime_ns","st_ctime_ns","st_uid","st_mode")
        def root_info(info,kind):
            value=SimpleNamespace(**{key:getattr(info,key) for key in fields})
            value.st_uid=0;value.st_mode=kind|(0o444 if kind==stat.S_IFREG else 0o755)
            return value
        def named(path,*args,**kwargs):
            if Path(path)==authority:return root_info(raw_stat(record),stat.S_IFREG)
            if str(path) in (str(AUTHORITY_ROOT),str(AUTHORITY_ROOT.parent)):
                return root_info(raw_stat(tmp_path),stat.S_IFDIR)
            return raw_stat(path,*args,**kwargs)
        def open_fd(path,*args,**kwargs):
            approved=Path(path)==authority if isinstance(path,(str,Path)) else False
            fd=raw_open(record if approved else path,*args,**kwargs);opened.add(fd)
            if approved:authority_fds.add(fd)
            return fd
        def close_fd(fd):opened.discard(fd);authority_fds.discard(fd);return raw_close(fd)
        def held(fd):
            info=raw_fstat(fd)
            return root_info(info,stat.S_IFREG) if fd in authority_fds else info
        with monkeypatch.context() as patch:
            patch.setattr(os,"open",open_fd);patch.setattr(os,"close",close_fd)
            patch.setattr(os,"lstat",named);patch.setattr(os,"fstat",held)
            patch.setattr(os,"execv",lambda file,args:calls.append((file,args)))
            patch.setattr(sys,"argv",["launcher",json.dumps(envelope),*argv])
            for field,key in IDENTITY_ENV.items():patch.setenv(key,str(getattr(identity(),field)))
            exec(sandbox._POLICY_FD_LAUNCHER,{})
        assert len(calls)==1 and calls[0][0]=="/usr/bin/bwrap"
        assert "--unshare-net" in calls[0][1] and calls[0][1][-1]=="/bin/true"
        assert result.read_bytes()==b""
    finally:
        for fd in opened:raw_close(fd)
        workspace.close();pinned.close();profile.close()
