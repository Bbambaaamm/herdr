"""Real namespace/resource checks; no mocked process or isolation success."""
from dataclasses import replace
import hashlib
from pathlib import Path
import os

import pytest
from herdr.check_runner import CheckEnvironment, HostCheckRunner
from herdr.evidence import digest
from herdr.work_cycle import ValidationCheck, WorkContractError, tree_snapshot
from herdr.workspace import _real_git
from test_work_cycle import setup, runner

def environment():
    if not Path("/usr/bin/bwrap").is_file():
        pytest.skip("physical namespace runtime unavailable in this test environment")
    python=str(Path("/usr/bin/python3").resolve(strict=True))
    bwrap=str(Path("/usr/bin/bwrap").resolve(strict=True))
    from tests.runtime_closure import approved_runtime
    files,aliases,helpers=approved_runtime()
    return CheckEnvironment("offline-closure-2",files,(python,),runtime_aliases=aliases,runtime_executables=helpers)

def physical(tmp_path, command, **limits):
    cycle,root,plan,log=setup(tmp_path)
    profile=environment()
    check=ValidationCheck("tests",tuple(command),("behavior",),**limits)
    plan=replace(plan,checks=(check,),environment_sha256=profile.hash)
    host=HostCheckRunner(profile,tmp_path/"private",git=_real_git(root))
    proof=host(check,root,plan,digest(tree_snapshot(root,git=_real_git(root))))
    return proof,root,host,check,plan

def test_actual_namespace_denies_network_source_writes_host_secrets_and_forks(tmp_path,monkeypatch):
    monkeypatch.setenv("HERDR_CHECK_PARENT_SECRET","private parent secret")
    code="""
import errno,os,pathlib,socket,resource
assert os.environ.get('HERDR_CHECK_PARENT_SECRET') is None
assert not pathlib.Path('/home/agentops/.config').exists()
assert not pathlib.Path('/run/herdr-policy/grant.bundle.json').exists()
try:
    pathlib.Path('/workspace/result.py').write_text('damage')
except OSError as e:
    assert e.errno==errno.EROFS
else:
    raise AssertionError('source writable')
try:
    socket.socket()
except OSError as e:
    assert e.errno==errno.EPERM
else:
    raise AssertionError('network allowed')
try:
    os.fork()
except OSError as e:
    assert e.errno==errno.EPERM
else:
    raise AssertionError('fork allowed')
assert resource.getrlimit(resource.RLIMIT_AS)==(536870912,536870912)
pathlib.Path('/tmp/scratch').write_text('allowed ephemeral scratch')
print('physical boundary verified')
"""
    proof,root,host,check,plan=physical(tmp_path,("/usr/bin/python3","-c",code))
    assert proof.exit_code==0 and not proof.truncated and len(proof.isolation_sha256)==64
    assert proof.output_sha256==hashlib.sha256(b"physical boundary verified\n").hexdigest()
    assert "return 1" in (root/"result.py").read_text()
    assert list(host.storage.iterdir())==[]

def test_actual_timeout_keeps_finite_failure_and_cleans_owned_snapshot(tmp_path):
    proof,root,host,check,plan=physical(tmp_path,("/usr/bin/python3","-c","import time; time.sleep(20)"),timeout_seconds=1)
    assert proof.exit_code==124 and proof.truncated and proof.duration_ms<4000
    assert list(host.storage.iterdir())==[]

def test_actual_output_limit_is_failure_not_pass(tmp_path):
    proof,root,host,check,plan=physical(tmp_path,("/usr/bin/python3","-c","print('x'*200000)"),output_bytes=4096)
    assert proof.exit_code==124 and proof.truncated
    assert list(host.storage.iterdir())==[]

def test_actual_check_failure_retains_fingerprint_and_exit_code(tmp_path):
    proof,root,host,check,plan=physical(tmp_path,("/usr/bin/python3","-c","import sys; print('expected regression'); sys.exit(1)"))
    assert proof.exit_code==1 and not proof.truncated
    assert proof.output_sha256==hashlib.sha256(b"expected regression\n").hexdigest()

def test_unsupported_network_or_process_profile_is_never_silently_weakened():
    profile=environment()
    for field,value in (("network","global"),("process_creation","allowed")):
        with pytest.raises(WorkContractError,match="unsupported"):
            replace(profile,**{field:value})

def test_changed_approved_runtime_blocks_check(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    profile=environment()
    bad=replace(profile,system_files=((profile.system_files[0][0],"f"*64),*profile.system_files[1:]))
    with pytest.raises(WorkContractError,match="changed"):
        HostCheckRunner(bad,tmp_path/"private",git=_real_git(root))

def test_profile_mismatch_and_unapproved_command_rejected_before_execution(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    profile=environment()
    host=HostCheckRunner(profile,tmp_path/"private",git=_real_git(root))
    tree=digest(tree_snapshot(root,git=_real_git(root)))
    with pytest.raises(WorkContractError,match="environment"):
        host(plan.checks[0],root,plan,tree)
    check=replace(plan.checks[0],command=("/usr/bin/git","status"))
    plan=replace(plan,checks=(check,),environment_sha256=profile.hash)
    with pytest.raises(WorkContractError,match="executable"):
        host(check,root,plan,tree)
    assert list(host.storage.iterdir())==[]
