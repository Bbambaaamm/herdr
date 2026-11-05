"""Actual corrupt-file boundaries, bounded migration and cold child rejection."""
import errno
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

from herdr.evidence import EvidenceStore, EvidenceError, EvidenceUnavailable, digest
from herdr.child_evidence import ChildCompletionAuthority, require_child_workspace
from herdr.scheduler import DynamicChildScheduler
from tests.herdr.test_child_evidence import artifact_fixture, scheduler_fixture
from tests.herdr.test_accepted_index import record

@pytest.mark.parametrize("kind", ["plan", "accepted"])
@pytest.mark.parametrize("fault", ["fifo", "directory", "hardlink", "mode", "symlink"])
def test_corrupt_flat_records_are_rejected_without_blocking(tmp_path, kind, fault):
    store=EvidenceStore(tmp_path/"store")
    key="a"*64; path=store._path(kind,key)
    if fault=="fifo":
        os.mkfifo(path,0o600)
    elif fault=="directory":
        path.mkdir(mode=0o700)
    else:
        store._publish(kind,key,{"value":1},register_index=False)
        if fault=="hardlink": os.link(path,tmp_path/"alias")
        elif fault=="mode": path.chmod(0o644)
        else:
            original=path.with_name("original");path.rename(original);path.symlink_to(original)
    program = """
from pathlib import Path
import sys
from herdr.evidence import EvidenceStore, EvidenceError, EvidenceUnavailable
try:
    EvidenceStore(Path(sys.argv[1])).read(sys.argv[2],sys.argv[3])
except EvidenceUnavailable:
    raise
except EvidenceError:
    print("PERMANENT_DENIAL")
else:
    raise AssertionError("corrupt record admitted")
"""
    result=subprocess.run([sys.executable,"-c",program,str(store.root),kind,key],
                          text=True,capture_output=True,timeout=5)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=="PERMANENT_DENIAL"

def test_fifo_in_legacy_migration_cannot_hold_writer_lock_or_hide_repaired_original(tmp_path):
    store=EvidenceStore(tmp_path/"store")
    identity,payload,key,legacy=record(17)
    path=store._path("accepted",legacy);os.mkfifo(path,0o600)
    program = """
from pathlib import Path
import json,sys
from herdr.evidence import EvidenceStore,EvidenceError,EvidenceUnavailable
try:
    EvidenceStore(Path(sys.argv[1])).lookup_acceptance(json.loads(sys.argv[2]),sys.argv[3])
except EvidenceUnavailable:
    raise
except EvidenceError:
    print("PERMANENT_DENIAL")
else:
    raise AssertionError("corrupt migration record admitted")
"""
    result=subprocess.run([sys.executable,"-c",program,str(store.root),json.dumps(identity),payload["plan_hash"]],
                          text=True,capture_output=True,timeout=5)
    assert result.returncode==0 and result.stdout.strip()=="PERMANENT_DENIAL",result.stderr
    path.unlink()
    store._publish("accepted",legacy,payload,register_index=False)
    assert EvidenceStore(store.root).lookup_acceptance(identity,payload["plan_hash"])==(payload,True)

@pytest.mark.parametrize("fault", ["deleted", "leaf-symlink", "ancestor-symlink"])
def test_missing_or_redirected_child_pin_is_permanent_before_collection(tmp_path,monkeypatch,fault):
    rec,result,plan,store,path,proof=artifact_fixture(tmp_path,monkeypatch)
    authority=ChildCompletionAuthority(store=store,approve=lambda **kw:plan,
        collector=lambda *args:pytest.fail("lost worktree must never collect evidence"))
    authority.prepare(rec)
    if fault=="deleted":
        import shutil
        shutil.rmtree(path)
    elif fault=="leaf-symlink":
        old=path.with_name("original");path.rename(old);path.symlink_to(old,target_is_directory=True)
    else:
        old=path.parent.with_name(path.parent.name+"-original")
        path.parent.rename(old);path.parent.symlink_to(old,target_is_directory=True)
    with pytest.raises(EvidenceError,match="missing, replaced or inaccessible") as caught:
        authority.verify(rec,result)
    assert not isinstance(caught.value,EvidenceUnavailable)

def test_transient_child_pin_io_retains_current_attempt(tmp_path,monkeypatch):
    root=tmp_path/"tree";root.mkdir();info=root.stat()
    class Rec: worktree_identity=f"{root}|{info.st_dev}:{info.st_ino}"
    monkeypatch.setattr(os,"open",lambda *args,**kwargs:(_ for _ in ()).throw(OSError(errno.EIO,"temporary device outage")))
    with pytest.raises(EvidenceUnavailable):require_child_workspace(Rec())

def test_cold_completed_result_with_lost_worktree_persists_rejection_and_releases_lease(tmp_path):
    # Only the authority port is a fixture; pin reading, exact-result publication
    # and durable scheduler replay use their production implementation.
    class Authority(ChildCompletionAuthority):
        def __init__(self):pass
        def verify(self,rec,payload):
            require_child_workspace(rec)
            pytest.fail("missing pin cannot reach semantic collection")
    missing=tmp_path/"removed-tree";missing.mkdir();info=missing.stat()
    scheduler,rec,lease,evidence,checksum=scheduler_fixture(tmp_path,Authority(),
        worktree_identity=f"{missing}|{info.st_dev}:{info.st_ino}")
    missing.rmdir()
    payload={"task_id":rec.id,"run_token":rec.run_token,"fencing_token":rec.fencing_token,
             "idempotency_key":rec.idempotency_key,"status":"completed",
             "evidence":evidence,"artifact_sha256":checksum}
    path=tmp_path/"candidate.result.json";path.write_text(json.dumps(payload));path.chmod(0o600)
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"agent-stack/bin"))
    from agent_durable_children import publish_exact_child_result
    assert publish_exact_child_result(scheduler,rec,path)=="blocked"
    assert rec.state.value=="blocked" and rec.lease is None and rec.completion_receipt is None
    assert rec.completion_failure["result_payload_sha256"]==digest(payload)
    restored=DynamicChildScheduler(audit_log=scheduler.audit_log);restored.replay()
    recovered=restored._tasks[rec.id]
    assert recovered.completion_failure==rec.completion_failure and recovered.lease is None
    assert publish_exact_child_result(restored,recovered,path)=="blocked"

def test_atomic_publication_never_exposes_a_temporary_hardlink(tmp_path,monkeypatch):
    store=EvidenceStore(tmp_path/"store");key="f"*64
    operation=store._exclusive_publish
    observed=[]
    def observe(source,destination):
        operation(source,destination)
        assert not Path(source).exists()
        observed.append(Path(destination).stat().st_nlink)
        assert store.read("plan",key)=={"value":1}
    monkeypatch.setattr(store,"_exclusive_publish",observe)
    store.publish("plan",key,{"value":1})
    assert observed==[1]
