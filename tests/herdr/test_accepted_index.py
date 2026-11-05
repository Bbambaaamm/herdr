"""Bounded real-file history migration, durable intents and private index boundaries."""
import copy
import json
import os
from pathlib import Path
import pytest
from herdr.evidence import EvidenceStore,EvidenceError,EvidenceUnavailable,digest
from herdr.accepted_index import AcceptedIndex

def record(number):
    identity={"id":f"task-{number}","run_token":"run","attempt":1,"idempotency_key":"key","fencing_token":2}
    payload={"version":2,"identity":identity,"repo":"org/repo","kind":"control","level":"control_cycle",
             "plan_hash":"a"*64,"spec_hash":"b"*64,"policy_hash":"c"*64,"baseline":[],
             "environment":{"collector":"host-schema-v1"},"proof":{"source":"host-schema-v1","result_digest":digest(number)},
             "integration":None,"deployment":None}
    key=digest({"identity":identity,"plan_hash":payload["plan_hash"]})
    legacy=digest({"identity":identity,"plan_hash":payload["plan_hash"],"result_hash":digest(number)})
    return identity,payload,key,legacy

def test_10001_legacy_documents_migrate_in_bounded_restartable_batches_and_new_attempt_stays_available(tmp_path,monkeypatch):
    store=EvidenceStore(tmp_path/"history")
    for number in range(10001):
        _,payload,_,legacy=record(number)
        store._publish("accepted",legacy,payload,register_index=False)
    identity,payload,key,legacy=record(10000)
    original=EvidenceStore.read;reads=0;passes=0
    def read(self,*args):
        nonlocal reads
        reads+=1
        return original(self,*args)
    monkeypatch.setattr(EvidenceStore,"read",read)
    for _ in range(1000):
        reads=0;passes+=1
        try:
            result,is_legacy=EvidenceStore(store.root).lookup_acceptance(identity,payload["plan_hash"])
            break
        except EvidenceUnavailable as exc:
            assert "migration" in str(exc)
            assert reads<=512
            checkpoint=json.loads((store.root/".acceptance-index"/"migration.json").read_text())
            assert checkpoint["cookie"]>0 and not checkpoint["complete"]
    else:pytest.fail("durable migration did not finish")
    assert passes>1 and result==payload and is_legacy
    assert len(list(store.root.glob("accepted-*")))==10001
    store.publish("accepted",key,payload)
    reads=0
    assert EvidenceStore(store.root).lookup_acceptance(identity,payload["plan_hash"])==(payload,False)
    assert reads<=2
    fresh,new,key,_=record(10001)
    store.publish("accepted",key,new)
    reads=0
    assert EvidenceStore(store.root).lookup_acceptance(fresh,new["plan_hash"])==(new,False)
    assert reads<=2 and len(list(store.root.glob("accepted-*")))==10003

def test_exact_fsynced_intent_recovers_after_flat_bundle_publication_failure_without_replacing_candidate(tmp_path,monkeypatch):
    store=EvidenceStore(tmp_path/"store");identity,payload,key,_=record(1)
    original=EvidenceStore._exclusive_publish
    def fail(*args,**kwargs):
        raise OSError("crash before flat publication")
    monkeypatch.setattr(EvidenceStore,"_exclusive_publish",staticmethod(fail))
    with pytest.raises(EvidenceUnavailable):store.publish("accepted",key,payload)
    assert not list(store.root.glob("accepted-*"))
    monkeypatch.setattr(EvidenceStore,"_exclusive_publish",staticmethod(original))
    assert EvidenceStore(store.root).lookup_acceptance(identity,payload["plan_hash"])==(payload,False)
    changed=copy.deepcopy(payload);changed["proof"]["result_digest"]="f"*64
    with pytest.raises(EvidenceError,match="conflicting"):
        store.publish("accepted",key,changed)
    assert store.read("accepted",key)==payload

@pytest.mark.parametrize("fault",["symlink","hardlink","mode","encoding","address","checkpoint"])
def test_private_index_corruption_is_permanent_and_never_hides_an_original_bundle(tmp_path,fault):
    store=EvidenceStore(tmp_path/"store");identity,payload,key,_=record(1)
    store.publish("accepted",key,payload)
    path=AcceptedIndex(store).receipt_path(key)
    if fault=="symlink":
        path.rename(tmp_path/"saved");path.symlink_to(tmp_path/"saved")
    elif fault=="hardlink":os.link(path,tmp_path/"extra")
    elif fault=="mode":path.chmod(0o644)
    elif fault=="encoding":path.write_text("{")
    elif fault=="address":
        value=json.loads(path.read_text());value["address"]="f"*64;path.write_text(json.dumps(value,sort_keys=True,separators=(",",":")))
    else:(store.root/".acceptance-index"/"migration.json").write_text("{}")
    with pytest.raises(EvidenceError):
        EvidenceStore(store.root).lookup_acceptance(identity,payload["plan_hash"])
    assert store.read("accepted",key)==payload
