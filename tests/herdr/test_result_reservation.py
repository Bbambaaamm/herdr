"""Pre-delivery result retry never truncates or adopts another fenced slot."""
from dataclasses import replace
import os
from pathlib import Path
import pytest
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
