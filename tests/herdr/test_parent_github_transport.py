"""Parent transport/reader components: fixed client argv, bounded processes and private data."""
from dataclasses import replace
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import SimpleNamespace
import json
import os
import resource
import sys
import time

import pytest

from herdr.evidence import EvidenceError, EvidenceUnavailable
from herdr.parent_publication import ParentPublicationPermit
from herdr.parent_github_transport import GitHubParentTransport, _bounded_process

ROOT = Path(__file__).resolve().parents[2]


def permit():
    return ParentPublicationPermit({"id":"test", "run_token":"original",
        "idempotency_key":"original-key","attempt":1,"fencing_token":1},
        "org/repo","a"*64,"b"*64,"c"*40,"review/base","herdr/result",int(time.time())+300)


def transport(tmp_path):
    return GitHubParentTransport(repo="org/repo",scratch=tmp_path/"transport",
        gh=Path(sys.executable),home=tmp_path/"parent-home")


def test_http_observation_uses_fixed_repo_branches_and_complete_bounded_query(tmp_path,monkeypatch):
    client=transport(tmp_path);p=permit();calls=[]
    def api(permit,method,path,**kwargs):
        calls.append((method,path,kwargs))
        if "/git/ref/heads/" in path:
            return None if path.endswith("herdr/result") else {"object":{"sha":p.base_sha}}
        return []
    monkeypatch.setattr(client,"_api",api)
    assert client.observe(p,SimpleNamespace(commit_sha="d"*40)) == {
        "base_sha":p.base_sha,"head_sha":None,"pull_requests":[]}
    assert all(m=="GET" and path.startswith("repos/org/repo/") for m,path,_ in calls)
    assert "head=org%3Aherdr%2Fresult" in calls[-1][1]
    assert calls[1][2]["missing"] is True


@pytest.mark.parametrize("http,status,missing,expected",[
    (200,0,False,{}),(201,0,False,{}),(404,1,True,None),
    (403,1,False,"denied"),(200,1,False,"denied")])
def test_http_status_is_structured_and_error_body_is_not_exported(tmp_path,monkeypatch,http,status,missing,expected):
    client=transport(tmp_path);seen=[]
    def run(permit,argv,**kwargs):
        seen.append((argv,kwargs))
        return status,("HTTP/2.0 "+str(http)+" test\r\nX-Header: value\r\n\r\n{}").encode()
    monkeypatch.setattr(client,"_run",run)
    if expected=="denied":
        with pytest.raises(EvidenceUnavailable):client._api(permit(),"GET","repos/org/repo/test",missing=missing)
    else:
        assert client._api(permit(),"GET","repos/org/repo/test",missing=missing)==expected
    assert seen[0][0][1:]==["api","--hostname","github.com","--method","GET","--include","repos/org/repo/test"]


def test_create_pr_sends_one_closed_json_request_on_stdin(tmp_path,monkeypatch):
    client=transport(tmp_path);calls=[]
    def run(p,argv,**kwargs):
        calls.append((argv,kwargs))
        return 0,b"HTTP/2.0 201 Created\n\n{}"
    monkeypatch.setattr(client,"_run",run)
    request={"title":"test","body":"local PASS","base":"review/base","head":"herdr/result"}
    client.create_pull_request(permit(),SimpleNamespace(commit_sha="d"*40),request)
    assert len(calls)==1
    assert json.loads(calls[0][1]["data"])==request
    assert calls[0][0][-2:]==["--input","-"]


def test_git_push_uses_only_a_new_bare_repo_fixed_url_and_empty_remote_lease(tmp_path,monkeypatch):
    client=transport(tmp_path);p=permit();artifact=SimpleNamespace(commit_sha="d"*40)
    calls=[]
    def run(permit,argv,**kwargs):
        calls.append((argv,kwargs))
        if "rev-parse" in argv:return 0,(artifact.commit_sha+"\n").encode()
        if "rev-list" in argv:return 0,(artifact.commit_sha+" "+p.base_sha+"\n").encode()
        return 0,b""
    monkeypatch.setattr(client,"_run",run)
    client.push(p,artifact,b"# test bundle")
    assert len([a for a,_ in calls if "push" in a])==1
    push=next(a for a,_ in calls if "push" in a)
    assert "--force-with-lease=refs/heads/herdr/result:" in push
    assert artifact.commit_sha+":refs/heads/herdr/result" in push
    assert "https://github.com/org/repo.git" in push
    for argv,options in calls:
        bare=Path(argv[argv.index("-C")+1])
        assert bare.is_relative_to(client.scratch) and bare.name=="repository.git"
        assert options["cwd"]!=ROOT and "core.hooksPath=/dev/null" in argv
    assert client.env["GIT_CONFIG_GLOBAL"]=="/dev/null"
    assert client.env["GIT_CONFIG_NOSYSTEM"]=="1"
    assert client.env["HOME"]==str(tmp_path/"parent-home")


@pytest.mark.parametrize("bad_parent",[True,False])
def test_changed_bundle_head_or_parent_stops_before_push(tmp_path,monkeypatch,bad_parent):
    client=transport(tmp_path);p=permit();artifact=SimpleNamespace(commit_sha="d"*40);effects=[]
    def run(permit,argv,**kwargs):
        effects.append(argv)
        if "rev-parse" in argv:return 0,((artifact.commit_sha if bad_parent else "e"*40)+"\n").encode()
        if "rev-list" in argv:return 0,(artifact.commit_sha+" "+"e"*40+"\n").encode()
        return 0,b""
    monkeypatch.setattr(client,"_run",run)
    with pytest.raises(EvidenceError):client.push(p,artifact,b"bundle")
    assert not any("push" in a for a in effects)


def test_transport_storage_cannot_overlap_worker_write_roots(tmp_path):
    client=transport(tmp_path)
    with pytest.raises(EvidenceError):client.protect_from((tmp_path,))
    client.protect_from((tmp_path/"worker",))


def test_process_output_and_timeout_are_bounded_without_returning_private_stderr(tmp_path):
    env={"PATH":"/usr/bin:/bin","HOME":"/tmp"}
    with pytest.raises(EvidenceUnavailable):
        _bounded_process([sys.executable,"-I","-B","-c","import sys;sys.stderr.write('private-marker'*10000)"],
            env=env,cwd=tmp_path,output_limit=1024)
    with pytest.raises(EvidenceUnavailable):
        _bounded_process([sys.executable,"-I","-B","-c","import time;time.sleep(10)"],
            env=env,cwd=tmp_path,timeout=0.25)
    code,out=_bounded_process([sys.executable,"-I","-B","-c",
        "import sys;data=sys.stdin.buffer.read();sys.stdout.buffer.write(data)"],
        env=env,cwd=tmp_path,data=b'{"bounded":true}',timeout=5)
    assert code==0 and out==b'{"bounded":true}'


def test_successful_parent_client_does_not_leave_a_detached_helper_running(tmp_path):
    child=tmp_path/"child.pid"
    command=("import subprocess,sys;from pathlib import Path;"
        "p=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(30)'],"
        "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
        "Path("+repr(str(child))+").write_text(str(p.pid))")
    code,_=_bounded_process([sys.executable,"-I","-B","-c",command],
        env={"PATH":"/usr/bin:/bin","HOME":"/tmp"},cwd=tmp_path,timeout=5)
    assert code==0
    pid=int(child.read_text())
    for _ in range(20):
        status=Path("/proc",str(pid),"status")
        if not status.exists() or "State:\tZ" in status.read_text():
            break
        time.sleep(0.05)
    else:
        pytest.fail("owned helper survived client completion")


def test_transport_preserves_a_stricter_inherited_resource_limit(tmp_path):
    old = resource.getrlimit(resource.RLIMIT_NOFILE)
    finite = [x for x in old if x != resource.RLIM_INFINITY]
    bound = min([128, *finite])
    resource.setrlimit(resource.RLIMIT_NOFILE, (bound, old[1]))
    try:
        code, out = _bounded_process([sys.executable, "-I", "-B", "-c",
            "import resource; print(resource.getrlimit(resource.RLIMIT_NOFILE)[0])"],
            env={"PATH":"/usr/bin:/bin","HOME":"/tmp"}, cwd=tmp_path, timeout=5)
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, old)
    assert code == 0 and int(out) == bound


def reader():
    loader=SourceFileLoader("parent_publication_reader_component",
        str(ROOT/"scripts/publish-herdr-parent-result.py"))
    module=module_from_spec(spec_from_loader(loader.name,loader));loader.exec_module(module)
    return module


@pytest.mark.parametrize("fault",[None,"duplicate","symlink","hardlink","public","fifo"])
def test_parent_result_reader_checks_actual_private_file_metadata(tmp_path,fault):
    module=reader();path=tmp_path/"result.json"
    if fault=="fifo":
        os.mkfifo(path)
    else:
        path.write_text('{"value":1}');path.chmod(0o600)
        if fault=="duplicate":path.write_text('{"value":1,"value":2}')
        elif fault=="symlink":
            target=tmp_path/"source";path.rename(target);path.symlink_to(target)
        elif fault=="hardlink":os.link(path,tmp_path/"second")
        elif fault=="public":path.chmod(0o644)
    if fault is None:assert module.read_private_json(path)=={"value":1}
    else:
        with pytest.raises((EvidenceError,OSError)):
            module.read_private_json(path)


@pytest.mark.parametrize("marker",[None,True,False,"1"])
def test_parent_command_rejects_noncanonical_work_marker_before_recovery(tmp_path,monkeypatch,marker):
    module=reader();p=permit()
    monkeypatch.setattr(module,"load_permit",lambda path:(p,{"gh":"/parent/gh","home":"/parent/home"}))
    task={"id":"test","run_token":"original","idempotency_key":"original-key",
        "attempt_id":1,"fencing_token":1,"work_contract_version":marker}
    monkeypatch.setattr(module,"read_canonical_parent",lambda *args:task)
    native=SourceFileLoader.exec_module
    def load(loader,worker):
        if loader.name!="herdr_parent_original_worker":return native(loader,worker)
        worker.ROOT=tmp_path
        worker._recover_root_work_cycle=lambda *a:pytest.fail("invalid marker reached recovery")
    monkeypatch.setattr(SourceFileLoader,"exec_module",load)
    with pytest.raises(EvidenceError,match="modern parent task"):
        module.main(["--permit","/root-approved/component.json"])

