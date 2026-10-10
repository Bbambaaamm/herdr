"""Opt-in host composition; no root publication, provider call or live queue."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timedelta,UTC
import hashlib
from pathlib import Path

import pytest

from herdr import host_configuration as config
from herdr.policy_launch import ApprovedImmutableTree,PreparedPolicyLaunch
from herdr.security import SecurityError
from tests.herdr.test_host_configuration import approved_config
from tests.herdr.test_trusted_profile_handoff import approved_profile


def private_config(tmp_path,monkeypatch):
    raw,workspace,parent=approved_config(tmp_path,monkeypatch)
    approved,_=approved_profile(tmp_path)
    from herdr.host_bootstrap import SHIM_SOURCE,PYTHON_TARGET,PYTHON_EXECUTABLE
    cli="agent-stack/policy-bin/herdr"
    code=Path(raw["code"]["source"])
    target=code/cli;target.parent.mkdir(parents=True,exist_ok=True)
    body=(Path(__file__).resolve().parents[2]/cli).read_bytes();target.write_bytes(body)
    raw["code"]["files"][cli]=hashlib.sha256(body).hexdigest()
    raw["code"]["executable_files"]=[cli,SHIM_SOURCE]
    definition=next(row for row in raw["runtime"] if row["target"]==str(PYTHON_TARGET))
    target=Path(definition["source"])/PYTHON_EXECUTABLE
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b"fixture-python")
    definition["files"][PYTHON_EXECUTABLE]=hashlib.sha256(b"fixture-python").hexdigest()
    definition["executable_files"]=[PYTHON_EXECUTABLE]
    raw["schema_version"]=2
    raw["private_launch"]={
        "profile":{"name":approved.name,"source":str(approved.source),"files":dict(approved.files)},
        "credential_approval":{
            "schema_version":"herdr-profile-credential-approval-1",
            "profile_sha256":approved.identity["manifest_sha256"],
            "valid_until":(datetime.now(UTC)+timedelta(hours=2)).isoformat(),
            "minimum_ttl_seconds":1860}}
    monkeypatch.setattr(config,"_read_configuration",lambda path:deepcopy(raw))
    return raw,workspace,parent,approved


def test_root_composition_selects_immutable_trees_and_exact_host_profile(tmp_path,monkeypatch):
    raw,workspace,parent,approved=private_config(tmp_path,monkeypatch)
    factory=config.build_host_policy_factory()
    assert isinstance(factory.code,ApprovedImmutableTree)
    assert all(isinstance(tree,ApprovedImmutableTree) for tree in factory.runtime)
    assert factory.approved_profile.identity==approved.identity
    assert factory.code.executable_files==tuple(raw["code"]["executable_files"])
    assert factory.profile_preflight(approved.name) is True
    with pytest.raises(SecurityError,match="profile changed"):
        factory.profile_preflight("foreign")
    # Actual mutable fixture sources cannot be used as a private runtime.
    with pytest.raises(SecurityError,match="root protected"):
        factory.prepare(identity=parent.identity,workspace=workspace,
                        tools=parent.scope.tools,permissions=parent.scope.permissions)


@pytest.mark.parametrize("approved,mode,valid",[(True,0o555,True),(False,0o444,True),
    (True,0o444,False),(False,0o555,False),(True,0o500,False)])
def test_immutable_approval_enforces_real_execute_bits_and_closes_on_failure(tmp_path,monkeypatch,approved,mode,valid):
    import os
    from types import SimpleNamespace
    from herdr.policy_launch import FrozenTree,CODE_TARGET
    source=tmp_path/"source";source.mkdir();file=source/"entry.py";file.write_bytes(b"approved=True\n");file.chmod(mode)
    closed=[]
    def attach(*args,**kwargs):
        fd=os.open(source,os.O_RDONLY|os.O_DIRECTORY)
        info=os.fstat(fd)
        frozen=FrozenTree(source,CODE_TARGET,fd,info.st_dev,info.st_ino,"a"*64,
            (("entry.py",hashlib.sha256(file.read_bytes()).hexdigest()),))
        original=frozen.close
        def close():closed.append(fd);original()
        frozen.close=close
        return frozen
    # Only the independently tested root-protected attachment is a double.
    # Execute bits and descriptor cleanup use actual filesystem operations.
    monkeypatch.setattr(FrozenTree,"attach_immutable",attach)
    tree=ApprovedImmutableTree(source,CODE_TARGET,{"entry.py":hashlib.sha256(file.read_bytes()).hexdigest()},
        executable_files=("entry.py",) if approved else ())
    if valid:tree.freeze(tmp_path,()).close()
    else:
        with pytest.raises(SecurityError,match="executable mode"):tree.freeze(tmp_path,())
    assert len(closed)==1


@pytest.mark.parametrize("approved",[True,False])
def test_immutable_execute_inventory_survives_later_verify(tmp_path,monkeypatch,approved):
    import os
    from herdr.policy_launch import FrozenTree,CODE_TARGET
    source=tmp_path/"source";source.mkdir();entry=source/"entry.py";entry.write_bytes(b"stable")
    entry.chmod(0o555 if approved else 0o444)
    digest=hashlib.sha256(entry.read_bytes()).hexdigest()
    def attach(*args,**kwargs):
        fd=os.open(source,os.O_RDONLY|os.O_DIRECTORY);info=os.fstat(fd)
        return FrozenTree(source,CODE_TARGET,fd,info.st_dev,info.st_ino,"a"*64,(("entry.py",digest),))
    monkeypatch.setattr(FrozenTree,"attach_immutable",attach) # Unit root-attachment double only.
    tree=ApprovedImmutableTree(source,CODE_TARGET,{"entry.py":digest},
        executable_files=("entry.py",) if approved else ()).freeze(tmp_path,())
    try:
        tree.verify()
        entry.chmod(0o444 if approved else 0o555)
        with pytest.raises(SecurityError,match="executable mode"):tree.verify()
    finally:tree.close()


@pytest.mark.parametrize("approved",[True,False])
def test_cold_source_recovery_rejects_mode_only_change(tmp_path,monkeypatch,approved):
    from types import SimpleNamespace
    from herdr import policy_launch as launch
    from herdr.private_mount_plan import ApprovedPrivateMountPlan
    from herdr.security import canonical_json_bytes
    _,_,parent,_=private_config(tmp_path,monkeypatch)
    source=tmp_path/"retained";source.mkdir();entry=source/"entry.py"
    entry.write_bytes(b"stable retained bytes");entry.chmod(0o555 if approved else 0o444)
    files={"entry.py":hashlib.sha256(entry.read_bytes()).hexdigest()}
    info=source.stat();target=str(launch.CODE_TARGET)
    proof={"identity":parent.identity.to_json(),
        "tree_identities":{target:{"device":info.st_dev,"inode":info.st_ino}},
        "immutable_sources":{"mount_plan":{"authority":"/unit-authority"},"executables":{},
            "trees":{target:{"source":str(source),
                "manifest_sha256":hashlib.sha256(canonical_json_bytes(files)).hexdigest(),
                "executable_files":["entry.py"] if approved else []}}}}
    # Only root publication checks are unit doubles; recovery hashing and
    # execute-bit verification read actual files, including the changed mode.
    monkeypatch.setattr(ApprovedPrivateMountPlan,"read",classmethod(lambda cls,*args:
        SimpleNamespace(evidence=lambda:proof["immutable_sources"]["mount_plan"])))
    monkeypatch.setattr(launch,"_verify_root_owned_ancestry",lambda path:None)
    monkeypatch.setattr(launch,"_verify_immutable_entry",lambda info:None)
    launch.verify_retained_immutable_sources(proof)
    entry.chmod(0o444 if approved else 0o555)
    with pytest.raises(SecurityError,match="retained immutable executable mode"):
        launch.verify_retained_immutable_sources(proof)


@pytest.mark.parametrize("fault",["missing-cli","unapproved-cli","missing-python","unapproved-python"])
def test_private_host_requires_approved_executable_inventory(tmp_path,monkeypatch,fault):
    raw,_,_,_=private_config(tmp_path,monkeypatch)
    from herdr.host_bootstrap import PYTHON_TARGET,PYTHON_EXECUTABLE
    python=next(row for row in raw["runtime"] if row["target"]==str(PYTHON_TARGET))
    if fault=="missing-cli":del raw["code"]["files"]["agent-stack/policy-bin/herdr"]
    elif fault=="unapproved-cli":raw["code"]["executable_files"].remove("agent-stack/policy-bin/herdr")
    elif fault=="missing-python":del python["files"][PYTHON_EXECUTABLE]
    else:python["executable_files"].remove(PYTHON_EXECUTABLE)
    with pytest.raises(SecurityError):config.build_host_policy_factory()


@pytest.mark.parametrize("fault",["missing-private","legacy-private","extra-private",
    "extra-profile","profile-digest","extra-credential","credential-kind","ttl-bool",
    "ttl-small","expiry-naive","expiry-malformed"])
def test_private_host_schema_rejects_unapproved_extensions(tmp_path,monkeypatch,fault):
    raw,workspace,parent,approved=private_config(tmp_path,monkeypatch)
    private=raw["private_launch"];approval=private["credential_approval"]
    if fault=="missing-private":del raw["private_launch"]
    elif fault=="legacy-private":raw["schema_version"]=1
    elif fault=="extra-private":private["approve_from_task"]=True
    elif fault=="extra-profile":private["profile"]["prompt"]="untrusted"
    elif fault=="profile-digest":approval["profile_sha256"]="0"*64
    elif fault=="extra-credential":approval["token"]="not-a-real-token"
    elif fault=="credential-kind":approval["schema_version"]="worker-self-approval"
    elif fault=="ttl-bool":approval["minimum_ttl_seconds"]=True
    elif fault=="ttl-small":approval["minimum_ttl_seconds"]=0
    elif fault=="expiry-naive":approval["valid_until"]="2026-10-10T12:00:00"
    else:approval["valid_until"]="not-a-date"
    with pytest.raises(SecurityError):config.build_host_policy_factory()


@pytest.mark.parametrize("fault",["expired","insufficient","profile-drift","policy-drift"])
def test_private_credential_preflight_rechecks_current_root_approval(tmp_path,monkeypatch,fault):
    raw,workspace,parent,approved=private_config(tmp_path,monkeypatch)
    factory=config.build_host_policy_factory()
    if fault in {"expired","insufficient"}:
        raw["private_launch"]["credential_approval"]["valid_until"]=(
            datetime.now(UTC)+timedelta(seconds=-1 if fault=="expired" else 100)).isoformat()
        factory=config.build_host_policy_factory()
        with pytest.raises(SecurityError,match="expired or insufficient"):
            factory.profile_preflight(approved.name)
    else:
        if fault=="profile-drift":raw["private_launch"]["profile"]["files"][".env"]="0"*64
        else:raw["grant_ttl_seconds"]=100
        with pytest.raises(SecurityError,match="policy changed"):
            factory.profile_preflight(approved.name)


def test_retained_parent_verifier_runs_again_before_child_profile_preflight(tmp_path,monkeypatch):
    raw,workspace,parent,approved=private_config(tmp_path,monkeypatch)
    observed=[]
    current=[parent,approved.identity]
    factory=config.build_host_policy_factory(parent_grant=parent,
        retained_parent_verify=lambda:observed.append("verify") or tuple(current))
    child=replace(parent.identity,agent_id="child",task_id="child-task",
                  parent_agent_id=parent.identity.agent_id,parent_task_id=parent.identity.task_id)
    # The production parent/profile gate executes before prepare() can inspect
    # credentials or allocate mounts. Physical signed evidence is tested elsewhere.
    monkeypatch.setattr(factory,"prepare",lambda **kwargs:observed.append("prepare") or "child")
    assert factory.prepare_child(identity=child,workspace=workspace,
        tools=("read_file",),permissions=("repo:read",))=="child"
    assert observed==["verify","prepare"]
    current[1]={**approved.identity,"manifest_sha256":"0"*64}
    with pytest.raises(SecurityError,match="verified retained parent"):
        factory.prepare_child(identity=child,workspace=workspace,
            tools=("read_file",),permissions=("repo:read",))
    assert observed==["verify","prepare","verify"]
    current[1]=approved.identity
    current[0]=replace(parent,grant_id="rotated-parent")
    with pytest.raises(SecurityError,match="verified retained parent"):
        factory.prepare_child(identity=child,workspace=workspace,
            tools=("read_file",),permissions=("repo:read",))


def test_cross_process_child_composition_revalidates_canonical_parent(tmp_path,monkeypatch):
    raw,workspace,parent,approved=private_config(tmp_path,monkeypatch)
    called=[]
    proof={"approved_profile":approved.identity}
    def verified(path,identity):
        called.append((path,identity.copy()))
        return {"id":"parent"},parent,proof
    monkeypatch.setattr(config,"_verified_parent",verified)
    route={"task_id":"parent","run_token":"run","agent":"parent-agent","pane":"p","marker":"m"}
    path=Path(raw["task_store_root"])/"running/parent.json"
    factory=config.child_factory_for_root(path,route)
    assert factory.retained_parent_verify()==(parent,approved.identity)
    assert len(called)==2
    # External mutation cannot change the route captured by the verifier.
    route["task_id"]="attacker"
    factory.retained_parent_verify()
    assert called[-1][1]["task_id"]=="parent"


def test_missing_root_plan_denies_command_before_any_spawn(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from herdr.private_mount_plan import ApprovedPrivateMountPlan
    from tests.herdr.test_policy_launch import grant
    workspace=tmp_path/"work";workspace.mkdir()
    mount=SimpleNamespace(private_mount_plan=None,private_mount_request=None)
    launch=PreparedPolicyLaunch(mount,grant(workspace),None,"test")
    launch.private_profile_snapshot=SimpleNamespace(name="quantlab")
    calls=[]
    def builder():
        calls.append("build-request")
        mount.private_mount_request={"bounded":"fixture"}
        raise RuntimeError("durable_private_mount_plan_unapproved")
    def denied(cls,path,identity):
        calls.append("root-read")
        raise SecurityError("root issuer unavailable")
    monkeypatch.setattr(ApprovedPrivateMountPlan,"read",classmethod(denied))
    with pytest.raises(SecurityError,match="issuer unavailable"):
        launch.prepare_private_command(builder)
    assert calls==["build-request","root-read"]


def test_unrelated_builder_failure_never_attempts_root_approval(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from herdr.private_mount_plan import ApprovedPrivateMountPlan
    from tests.herdr.test_policy_launch import grant
    workspace=tmp_path/"work";workspace.mkdir()
    launch=PreparedPolicyLaunch(SimpleNamespace(private_mount_plan=None),grant(workspace),None,"test")
    launch.private_profile_snapshot=SimpleNamespace(name="quantlab")
    monkeypatch.setattr(ApprovedPrivateMountPlan,"read",classmethod(
        lambda *args:pytest.fail("unrelated failures must not approve")))
    with pytest.raises(RuntimeError,match="unrelated"):
        launch.prepare_private_command(lambda:(_ for _ in ()).throw(RuntimeError("unrelated")))


@pytest.mark.parametrize("cleanup_fault",[False,True])
def test_private_child_failed_preparation_cleans_fresh_policy_even_if_pin_close_fails(tmp_path,monkeypatch,cleanup_fault):
    from types import SimpleNamespace
    from importlib.machinery import SourceFileLoader
    from herdr.runtime import HerdrChildRuntime
    from tests.policy_launch_fakes import FakePreparedPolicyLaunch
    from tests.herdr.test_security import identity
    runtime=HerdrChildRuntime.__new__(HerdrChildRuntime)
    runtime.cwd=tmp_path;runtime.snapshot_path=tmp_path/"snapshot.json";runtime.env={}
    launch=FakePreparedPolicyLaunch(identity());launch.private_profile_snapshot=SimpleNamespace(name="quantlab")
    def deny(builder):raise SecurityError("injected missing root plan")
    launch.prepare_private_command=deny
    runtime._policy_launches={"task":launch};runtime._policy_panes={}
    runtime._private_sandbox_commands={};runtime._managed_launch_panes=set()
    runtime._owned_write_pins={}
    runtime.scheduler=SimpleNamespace(_tasks={"task":SimpleNamespace(idempotency_key="key")})
    policy=tmp_path/"fresh-policy"
    def freeze():policy.write_text("allocated policy");return policy
    original=SourceFileLoader.exec_module
    def load(loader,module):
        if loader.name=="private_child_command":module.frozen_policy=freeze
        else:original(loader,module)
    monkeypatch.setattr(SourceFileLoader,"exec_module",load)
    with pytest.raises(SecurityError,match="missing root plan"):
        runtime._prepare_private_child_command("task","/bin/true")
    assert policy.exists()
    if cleanup_fault:
        def fail():raise OSError("injected owned pin cleanup")
        runtime._owned_write_pins["task"]=SimpleNamespace(close=fail)
        with pytest.raises(OSError,match="owned pin cleanup"):runtime._cleanup_policy_launch("task")
    else:runtime._cleanup_policy_launch("task")
    assert not policy.exists() and launch.events[-1]==("closed",)
