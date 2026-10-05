"""Physical owned-write boundaries; no provider or semantic acceptance claims."""
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from contextlib import contextmanager
import pytest
from herdr.child_ownership import ChildOwnership,WriteScope,OwnershipError
from herdr.owned_write_mounts import OwnedWritePins

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("owned_mount_sandbox",ROOT/"agent-stack/bin/agent_durable_sandbox.py")
sandbox=importlib.util.module_from_spec(spec);sys.modules[spec.name]=sandbox;spec.loader.exec_module(sandbox)

def contract(*scopes):
    return ChildOwnership(tuple(WriteScope(*item) for item in scopes),(),(),(),"parent","artifact://handoff/child")

@contextmanager
def pin(root):
    fd=os.open(root,os.O_PATH|os.O_DIRECTORY|os.O_CLOEXEC);info=os.fstat(fd)
    held=sandbox.PinnedWorktree(root,fd,info.st_dev,info.st_ino,root.parent)
    try:yield held
    finally:held.close()

def test_owned_mount_descriptors_pin_only_declared_files_and_directories(tmp_path):
    (tmp_path/"own.py").write_text("own")
    (tmp_path/"lib").mkdir()
    (tmp_path/"foreign.py").write_text("foreign")
    with pin(tmp_path) as root,OwnedWritePins(contract(("file","own.py"),("directory","lib")),root) as owned:
        assert set(owned.roots)=={str(tmp_path/"own.py"),str(tmp_path/"lib")}
        assert len(owned.descriptors())==2
        assert all(row["source"].startswith("/proc/") for row in owned.descriptors())
    with pytest.raises(OwnershipError,match="closed"):owned.verify()

@pytest.mark.parametrize("kind",["symlink","ancestor-symlink","hardlink","fifo","public-write","git","depth"])
def test_unsafe_owned_targets_deny_without_widening(tmp_path,kind):
    (tmp_path/"own").write_text("own");key="own";typ="file"
    if kind=="symlink":
        (tmp_path/"link").symlink_to(tmp_path/"own");key="link"
    elif kind=="ancestor-symlink":
        (tmp_path/"outside").mkdir();(tmp_path/"outside/file").write_text("x")
        (tmp_path/"link").symlink_to(tmp_path/"outside");key="link/file"
    elif kind=="hardlink":os.link(tmp_path/"own",tmp_path/"alias")
    elif kind=="fifo":os.mkfifo(tmp_path/"pipe");key="pipe"
    elif kind=="public-write":(tmp_path/"own").chmod(0o666)
    elif kind=="git":(tmp_path/".git").mkdir();key=".git";typ="directory"
    else:key="/".join(["deep"]*17);typ="directory"
    with pin(tmp_path) as root,pytest.raises((OwnershipError,OSError)):
        OwnedWritePins(contract((typ,key)),root)

@pytest.mark.parametrize("ancestor",[False,True])
def test_named_target_replacement_is_detected_before_mount(tmp_path,ancestor):
    (tmp_path/"lib").mkdir();(tmp_path/"lib/own.py").write_text("old")
    with pin(tmp_path) as root,OwnedWritePins(contract(("file","lib/own.py")),root) as owned:
        old=tmp_path/"lib" if ancestor else tmp_path/"lib/own.py"
        old.rename(old.with_name("retained"))
        if ancestor:(tmp_path/"lib").mkdir()
        (tmp_path/"lib/own.py").write_text("new")
        with pytest.raises(OwnershipError,match="binding_changed"):owned.descriptors()

def test_new_declared_file_is_host_created_and_fsynced_only_on_explicit_policy(tmp_path):
    (tmp_path/"lib").mkdir()
    with pin(tmp_path) as root:
        with pytest.raises(OwnershipError,match="target_missing"):
            OwnedWritePins(contract(("file","lib/new.py")),root)
        assert not (tmp_path/"lib/new.py").exists()
        with OwnedWritePins(contract(("file","lib/new.py")),root,create_files=True) as owned:
            assert owned.mounts[0].created
            assert (tmp_path/"lib/new.py").stat().st_mode&0o777==0o600
            assert (tmp_path/"lib/new.py").read_bytes()==b""

@pytest.mark.parametrize("kind",["file","directory"])
def test_actual_kernel_allows_owned_write_and_denies_foreign_sibling(kind,monkeypatch):
    if not sandbox.BWRAP.is_file():
        pytest.skip("actual kernel test requires installed bubblewrap; host launch still denies without it")
    # Keep workspace/results outside sandbox tmpfs and worktree-root masking.
    with tempfile.TemporaryDirectory(prefix=".owned-kernel-",dir=ROOT) as temporary:
        base=Path(temporary);worktrees=base/"worktrees";workspace=worktrees/"child"
        workspace.mkdir(parents=True);(workspace/"lib").mkdir()
        target=workspace/"lib/own.py";target.write_text("old")
        foreign=workspace/"foreign.py";foreign.write_text("foreign")
        result=base/"results/child.result.json";result.parent.mkdir();result.write_bytes(b"")
        native=base/"native";native.write_text("approved");policy=base/"policy";policy.write_text("approved")
        config=base/"config";config.mkdir();releases=base/"releases";releases.mkdir()
        monkeypatch.setattr(sandbox,"HERDR_CONFIG",config);monkeypatch.setattr(sandbox,"HERDR_RELEASES",releases)
        class TestMount:
            # Test-only descriptor adapter: this test establishes kernel file
            # scope, and does not claim authenticated policy/bootstrap evidence.
            def descriptors(self):return []
        scope=(kind,"lib/own.py" if kind=="file" else "lib")
        with pin(workspace) as root,OwnedWritePins(contract(scope),root) as owned:
            args=sandbox.command(workspace,native,writable=(result,),policy=policy,
                child_workspace_writable=False,pinned_worktree=root,policy_mount=TestMount(),owned_write_pins=owned)
            args=args[:args.index("--")+1]+["/usr/bin/python3","-I","-c",
                "from pathlib import Path;import errno;"
                "p=Path("+repr(str(target))+");p.write_text('changed');"
                "q=Path("+repr(str(foreign))+");"
                "\ntry:q.write_text('escape')\nexcept OSError as exc:assert exc.errno in (errno.EROFS,errno.EACCES)\nelse:raise AssertionError('foreign write succeeded')\n"]
            done=subprocess.run(args,capture_output=True,text=True,timeout=20)
            assert done.returncode==0,done.stderr
            assert target.read_text()=="changed" and foreign.read_text()=="foreign"
