"""Actual local Git metadata; physical check/commit seam is a separate selector."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest
from herdr.work_cycle import WorkContractError, WorkCycle, WorkPhase
import herdr.work_hygiene as hygiene


def local_git(root):
    """Explicit unit-only reader; physical selector retains canonical read_only_git."""
    def read(args):
        env={"PATH":"/usr/bin:/bin","HOME":"/nonexistent","GIT_CONFIG_NOSYSTEM":"1",
             "GIT_CONFIG_GLOBAL":"/dev/null","GIT_OPTIONAL_LOCKS":"0","LC_ALL":"C"}
        return subprocess.run(["/usr/bin/git","--no-optional-locks","--no-replace-objects",
            "-c","core.fsmonitor=false","-C",str(root),*args],env=env,capture_output=True,text=True,check=True).stdout
    return read


def config(root, key, value, *, add=False):
    return local_git(root)(["config","--local",*( ["--add"] if add else []),key,value])


@pytest.fixture
def actual_clone(tmp_path, monkeypatch):
    source=tmp_path/"source";source.mkdir();git=local_git(source)
    git(["init","-q","-b","main"]);config(source,"user.name","Git contract")
    config(source,"user.email","git-contract@example.invalid")
    (source/"sentinel.txt").write_text("unchanged\n");git(["add","."]);git(["commit","-qm","baseline"])
    root=tmp_path/"workspace"
    local_git(tmp_path)(["clone","--no-hardlinks","--no-checkout","--template=",str(source),str(root)])
    git=local_git(root);git(["remote","set-url","origin","https://github.com/org/repo.git"])
    git(["checkout","-qb","herdr/ordinary"]);(root/".git/hooks").mkdir(exist_ok=True)
    config(root,"user.name","Git contract");config(root,"user.email","git-contract@example.invalid")
    monkeypatch.setattr(hygiene,"read_only_git",local_git)
    return root


def policy(root):
    return SimpleNamespace(config_sha256=hashlib.sha256((root/".git/config").read_bytes()).hexdigest(),
                           hooks_root=str(root/".git/hooks"), hooks=())


def checked(root, *, repo="org/repo"):
    return hygiene._local_repository_inputs(policy(root),root,repo=repo,branch="herdr/ordinary")


def test_actual_clone_origin_and_tracking_are_metadata_not_commit_inputs(actual_clone):
    root=actual_clone;before=(root/".git/config").read_bytes();head=local_git(root)(["rev-parse","HEAD"])
    _,metadata,common,selected=checked(root)
    assert metadata==common==root/".git"
    assert selected=={"core.filemode":"true","user.name":"Git contract","user.email":"git-contract@example.invalid"}
    assert all(not key.startswith(("remote.","branch.")) for key in selected)
    assert (root/".git/config").read_bytes()==before and local_git(root)(["rev-parse","HEAD"])==head


def test_actual_committer_uses_the_shared_frozen_metadata_contract(actual_clone,tmp_path):
    root=actual_clone;committer=hygiene.HostLocalCommitter.__new__(hygiene.HostLocalCommitter)
    committer.policy=policy(root);committer.storage=tmp_path/"host";committer.runtime_storage=tmp_path/"scratch"
    committer.workspace_identity=f"{root.stat().st_dev}:{root.stat().st_ino}"
    committer.completion_plan={"repo":"org/repo"};committer.draft=SimpleNamespace(branch="herdr/ordinary")
    assert committer._repository(SimpleNamespace(root=root))[3]==checked(root)[3]


def test_legacy_originless_policy_remains_accepted(actual_clone):
    root=actual_clone;local_git(root)(["remote","remove","origin"])
    assert checked(root,repo=None)[3]["user.name"]=="Git contract"


@pytest.mark.parametrize("key,value",[
    ("remote.origin.url","http://github.com/org/repo.git"),
    ("remote.origin.url","https://github.com/other/repo.git"),
    ("remote.origin.url","https://user:secret@github.com/org/repo.git"),
    ("remote.origin.url","file:///tmp/repo"),
    ("remote.origin.fetch","+refs/*:refs/*"),
    ("remote.origin.pushurl","https://github.com/org/repo.git"),
    ("remote.other.url","https://github.com/org/repo.git"),
    ("remote.origin.promisor","true"),("remote.origin.partialclonefilter","blob:none"),
    ("include.path","/nonexistent/unapproved-config"),
    ("includeIf.gitdir:/tmp/.path","/nonexistent/unapproved-config"),
    ("filter.test.clean","cat"),("core.fsmonitor","true"),("core.sshcommand","false"),
    ("core.repositoryformatversion","1"),("core.bare","true"),
    ("extensions.worktreeconfig","true"),("extensions.partialclone","origin"),
    ("protocol.file.allow","always"),("url.file:///tmp/.insteadof","https://github.com/"),
    ("credential.helper","!false"),("commit.gpgsign","true"),("commit.template","/tmp/template"),
    ("branch.main.remote","other"),("branch.main.merge","refs/tags/tag"),
    ("branch.main.merge","refs/heads/../unsafe"),("branch.main.rebase","true"),
])
def test_unapproved_richer_config_remains_denied(actual_clone,key,value):
    config(actual_clone,key,value)
    with pytest.raises((WorkContractError,subprocess.CalledProcessError)):
        checked(actual_clone)


@pytest.mark.parametrize("key",["user.name","core.filemode","core.repositoryformatversion",
    "remote.origin.url","remote.origin.fetch","branch.main.remote","branch.main.merge","core.hookspath"])
def test_duplicate_keys_are_denied_even_when_values_match(actual_clone,key):
    value=local_git(actual_clone)(["config","--local","--get",key]).strip() if key!="core.hookspath" else str(actual_clone/".git/hooks")
    if key=="core.hookspath":config(actual_clone,key,value)
    config(actual_clone,key,value,add=True)
    with pytest.raises(WorkContractError,match="duplicate"):
        checked(actual_clone)


@pytest.mark.parametrize("missing",["remote.origin.url","remote.origin.fetch","branch.main.merge","branch.main.remote"])
def test_partial_origin_or_tracking_contract_is_denied(actual_clone,missing):
    local_git(actual_clone)(["config","--local","--unset-all",missing])
    with pytest.raises(WorkContractError):checked(actual_clone)


def test_git_reference_validator_and_bounded_tracking_are_used(actual_clone,monkeypatch):
    original=hygiene.read_only_git;calls=[]
    def tracked(root):
        git=original(root)
        def call(args):calls.append(args);return git(args)
        return call
    monkeypatch.setattr(hygiene,"read_only_git",tracked)
    checked(actual_clone)
    assert ["check-ref-format","refs/heads/main"] in calls
    config(actual_clone,"branch.bad..name.remote","origin")
    config(actual_clone,"branch.bad..name.merge","refs/heads/main")
    with pytest.raises(subprocess.CalledProcessError):checked(actual_clone)
    local_git(actual_clone)(["config","--local","--remove-section","branch.bad..name"])
    for n in range(32):
        config(actual_clone,f"branch.extra{n}.remote","origin")
        config(actual_clone,f"branch.extra{n}.merge","refs/heads/main")
    with pytest.raises(WorkContractError,match="bounded"):checked(actual_clone)


def test_frozen_config_drift_is_denied(actual_clone):
    root=actual_clone;old=policy(root);config(root,"user.name","changed after approval")
    with pytest.raises(WorkContractError,match="policy changed"):
        hygiene._local_repository_inputs(old,root,repo="org/repo")


def test_config_parser_inode_swap_is_denied(actual_clone,monkeypatch):
    root=actual_clone;old=policy(root);original=hygiene.read_only_git
    def reader(path):
        git=original(path)
        def read(args):
            result=git(args)
            if args==["config","--local","--null","--list"]:
                target=root/".git/config";other=target.with_name("replacement")
                other.write_bytes(target.read_bytes());other.replace(target)
            return result
        return read
    monkeypatch.setattr(hygiene,"read_only_git",reader)
    with pytest.raises(WorkContractError,match="during parsing"):
        hygiene._local_repository_inputs(old,root,repo="org/repo")


@pytest.mark.parametrize("failure",["origin","hook","config-sha","hygiene-sha"])
def test_fresh_prepare_denies_before_cycle_or_budget(actual_clone,tmp_path,monkeypatch,failure):
    from tests.herdr.test_work_contract_host import factory_fixture
    from tests.herdr.test_check_runner import environment
    import herdr.work_contract_host as host
    factory,root,plan,grant,log=factory_fixture(tmp_path/"factory")
    local_git(root)(["branch","-m","herdr/ordinary"])
    config(root,"remote.origin.url","https://github.com/org/repo.git")
    config(root,"remote.origin.fetch","+refs/heads/*:refs/remotes/origin/*")
    env=replace(environment(),executables=(*environment().executables,"/usr/bin/git"))
    frozen=hygiene.LocalCommitPolicy("repo-policy-1",env,policy(root).config_sha256,str(root/".git/hooks"),())
    if failure=="origin":
        config(root,"remote.origin.url","https://github.com/other/repo.git")
        frozen=replace(frozen,config_sha256=policy(root).config_sha256)
    elif failure=="hook":
        hook=root/".git/hooks/pre-commit";hook.write_text("#!/bin/sh\ntrue\n");hook.chmod(0o700)
    elif failure=="config-sha":config(root,"user.name","drift")
    factory.local_commit_policy=frozen;factory.environment=env
    plan=replace(plan,environment_sha256=env.hash,hygiene_sha256=frozen.hash)
    if failure=="hygiene-sha":plan=replace(plan,hygiene_sha256="f"*64)
    factory.approve=lambda **kw:plan
    monkeypatch.setattr(host,"WorkCycle",lambda *a,**kw:pytest.fail("no work plan publication before preflight"))
    monkeypatch.setattr(host,"HostCheckRunner",lambda *a,**kw:pytest.fail("no baseline runner before preflight"))
    factory.budget_authority=SimpleNamespace(open=lambda **kw:pytest.fail("no budget open before preflight"))
    with pytest.raises(WorkContractError):
        factory.prepare(identity=plan.identity,workspace=root,grant=grant,spec_sha256=plan.spec_sha256)
    assert log.replay()==[]


def test_fresh_prepare_uses_same_contract_before_first_runner(actual_clone,tmp_path,monkeypatch):
    from tests.herdr.test_work_contract_host import factory_fixture
    from tests.herdr.test_check_runner import environment
    import herdr.work_contract_host as host
    factory,root,plan,grant,log=factory_fixture(tmp_path/"factory")
    local_git(root)(["branch","-m","herdr/ordinary"])
    config(root,"remote.origin.url","https://github.com/org/repo.git")
    config(root,"remote.origin.fetch","+refs/heads/*:refs/remotes/origin/*")
    env=replace(environment(),executables=(*environment().executables,"/usr/bin/git"))
    frozen=hygiene.LocalCommitPolicy("repo-policy-1",env,policy(root).config_sha256,str(root/".git/hooks"),())
    factory.local_commit_policy=frozen;factory.environment=env
    plan=replace(plan,environment_sha256=env.hash,hygiene_sha256=frozen.hash)
    factory.approve=lambda **kw:plan
    class AtFirstRunner(Exception):pass
    monkeypatch.setattr(host,"HostCheckRunner",lambda *a,**kw:(_ for _ in ()).throw(AtFirstRunner()))
    with pytest.raises(AtFirstRunner):
        factory.prepare(identity=plan.identity,workspace=root,grant=grant,spec_sha256=plan.spec_sha256)
    assert log.replay()==[]


def test_actual_clone_check_hygiene_slot_and_cold_result(boundary_workspace,monkeypatch):
    """Primary runs only this selector in approved physical /opt layout, no SDK."""
    from tests.herdr import test_work_handoff as handoff
    from tests.herdr.test_work_hygiene import fixture as original_fixture
    from herdr.check_runner import HostCheckRunner
    from herdr.result_submission import submit,payload_for_slot
    from herdr.evidence import EvidenceError
    original_reader=hygiene.read_only_git
    def clone(work,branch):
        source=work.parent/"clone-source";work.rename(source)
        local_git(work.parent)(["clone","--no-hardlinks","--no-checkout","--template=",str(source),str(work)])
        git=local_git(work);git(["remote","set-url","origin","https://github.com/org/repo.git"])
        git(["checkout","-q",branch]);(work/".git/hooks").mkdir(exist_ok=True);config(work,"user.name","Physical contract")
        config(work,"user.email","physical@example.invalid")
    def clone_fixture(*args,**kwargs):return original_fixture(*args,**kwargs,repository_setup=clone)
    monkeypatch.setattr(handoff,"fixture",clone_fixture)
    port,cycle,guard,result,task,plan,observations,log=handoff.ready(boundary_workspace,monkeypatch)
    assert hygiene.read_only_git is original_reader
    assert local_git(cycle.root)(["config","--local","--get","remote.origin.url"]).strip()=="https://github.com/org/repo.git"
    port.prepare_request(cycle,"clone-request",{"pr_number":None})
    runner=HostCheckRunner(handoff.committer_policy(port),boundary_workspace/"host/checks",git=cycle.git)
    outcome=cycle.request_verification("clone-request",runner)
    response=port.complete(cycle,"clone-request",outcome)
    assert cycle.phase is WorkPhase.HANDOFF and len(observations)==1
    assert submit(guard,response["submission"])["submitted"]
    payload=json.loads(result.read_bytes())
    assert payload==payload_for_slot(cycle.plan.identity,port.slot,response["submission"])
    checker=port.result_authority.verifier(task,payload,plan,work_plan_sha256=cycle.plan.hash)
    monkeypatch.setattr("herdr.work_result_receipt.verify_invocation_session",lambda *a:pytest.fail("cold result must not restart SDK"))
    assert checker(task)==task["execution_session"]["invocation_policy"]
    before=log._path.read_bytes();restored=WorkCycle(cycle.plan,cycle.root,log,git=cycle.git)
    assert port.committer(restored).to_json()==response["submission"]["evidence"][0]["herdr_completion"]["artifact"]
    shutil.rmtree(cycle.root)
    assert port.committer(restored).to_json()==response["submission"]["evidence"][0]["herdr_completion"]["artifact"]
    assert log._path.read_bytes()==before and submit(guard,response["submission"])["submitted"]


from tests.herdr.test_work_hygiene import boundary_workspace
