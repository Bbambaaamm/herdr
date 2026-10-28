import importlib.util
import json
from pathlib import Path
import pytest


def load(name):
    p=Path(__file__).resolve().parents[1]/'physical'/name
    spec=importlib.util.spec_from_file_location('physical_fixture',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture():
    m=load('offline_provider.py');f=object.__new__(m.ProviderFixture)
    f.edits={'agent_platform_dashboard/production_contract.py':'fixture-only'}
    f.scope_claim=None;f.turn=0;f.complete=False
    return m,f


def payload():
    return {'model':'meituan/longcat-2.0:free','tools':[{'type':'function','function':{'name':name}} for name in ('read_file','write_file','herdr_verify_work','herdr_submit_result')],'messages':[]}


def calls(answer):
    return answer['choices'][0]['message'].get('tool_calls',[])


def test_fixture_only_responds_through_disclosed_sdk_tools_and_exact_host_submission():
    m,f=fixture();p=payload()
    reads=calls(f.answer(p));assert len(reads)==len(m.FILES)
    assert all(c['function']['name']=='read_file' for c in reads)
    assert calls(f.answer(p))[0]['function']['name']=='write_file'
    verify=calls(f.answer(p))[0]
    assert verify['function']['name']=='herdr_verify_work'
    assert json.loads(verify['function']['arguments'])['handoff']=={'pr_number':None}
    submission={'status':'completed','evidence':[{'fixture':'host-generated'}],'summary':'local fixture'}
    p['messages']=[{'role':'tool','content':json.dumps({'result':{'status':'pass','submission':submission}})}]
    result=calls(f.answer(p))[0]
    assert result['function']['name']=='herdr_submit_result'
    assert json.loads(result['function']['arguments'])==submission
    assert not calls(f.answer(p)) and f.complete


def test_failed_or_absent_actual_verification_cannot_be_faked_as_accepted():
    _,f=fixture();f.turn=3
    p=payload();p['messages']=[{'role':'tool','content':json.dumps({'status':'failed'})}]
    with pytest.raises(ValueError,match='did_not_pass'):f.answer(p)


def test_fixture_never_adds_missing_tools_or_unbounded_turns():
    _,f=fixture();p=payload();p['tools']=[]
    with pytest.raises(ValueError,match='tools_missing'):f.answer(p)
    f.turn=8
    with pytest.raises(ValueError,match='turn_limit'):f.answer(payload())


def test_fixture_custody_rejects_symlink_without_chowning_target(tmp_path,monkeypatch):
    m=load('offline_pilot.py');root=tmp_path/'root';root.mkdir();target=tmp_path/'outside';target.write_text('keep');(root/'alias').symlink_to(target)
    changed=[];monkeypatch.setattr(m.os,'chown',lambda path,*args:changed.append(Path(path)))
    with pytest.raises(RuntimeError,match='unexpected_link'):m.user_tree(root)
    assert target not in changed and target.read_text()=='keep'


def test_native_snapshot_read_does_not_reject_or_change_old_access_time(tmp_path):
    import os
    m=load('offline_pilot.py');source=tmp_path/'binary';source.write_bytes(b'fixture-native-source')
    old=1_000_000_000;os.utime(source,ns=(old,source.stat().st_mtime_ns))
    assert m.read_native_snapshot(source,owner=os.geteuid())==b'fixture-native-source'
    assert source.stat().st_atime_ns==old


def test_native_snapshot_still_rejects_a_content_version_change(tmp_path,monkeypatch):
    import os
    m=load('offline_pilot.py');source=tmp_path/'binary';source.write_bytes(b'fixture-native-source')
    original=m.os.read;changed=False
    def read(fd,size):
        nonlocal changed
        data=original(fd,size)
        if not changed:
            changed=True;stamp=source.stat();os.utime(source,ns=(stamp.st_atime_ns,stamp.st_mtime_ns+1))
        return data
    monkeypatch.setattr(m.os,'read',read)
    with pytest.raises(RuntimeError,match='snapshot_changed'):m.read_native_snapshot(source,owner=os.geteuid())
