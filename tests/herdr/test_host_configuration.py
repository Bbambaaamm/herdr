from dataclasses import replace
from pathlib import Path
import hashlib,json,os
import pytest
from herdr import host_configuration as config
from herdr.policy_launch import CODE_TARGET,RUNTIME_TARGETS,HostPolicyLaunchFactory
from herdr.security import SecurityError
from tests.herdr.test_security import grant,identity

def approved_config(tmp_path,monkeypatch):
    workspace=tmp_path/"worker";workspace.mkdir()
    storage=tmp_path/"store";storage.mkdir(mode=0o700)
    task_root=tmp_path/"tasks";task_root.mkdir()
    definitions=[]
    for number,target in enumerate((CODE_TARGET,*sorted(RUNTIME_TARGETS))):
        source=tmp_path/f"code-{number}";source.mkdir()
        body=b"approved=True\n";(source/"module.py").write_bytes(body)
        definitions.append(dict(source=str(source),target=str(target),
            files={"module.py":hashlib.sha256(body).hexdigest()},executable_files=[],
            max_bytes=1048576,max_file_bytes=1048576))
    from herdr.host_bootstrap import SHIM_SOURCE,STAGE1_SOURCE,STAGE2_SOURCE
    code=Path(definitions[0]["source"])
    for name in (SHIM_SOURCE,STAGE1_SOURCE,STAGE2_SOURCE):
        body=(Path(__file__).resolve().parents[2]/name).read_bytes()
        target=code/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        definitions[0]["files"][name]=hashlib.sha256(body).hexdigest()
    template=grant(workspace)
    raw=dict(schema_version=1,host_uid=os.geteuid(),code=definitions[0],runtime=definitions[1:],
        storage=str(storage),task_store_root=str(task_root),
        templates={template.identity.consumer:template.to_json()},grant_ttl_seconds=300)
    monkeypatch.setattr(config,"_read_configuration",lambda path:raw)
    return raw,workspace,template

def test_actual_host_factory_freezes_approved_bytes_and_scopes_identity(tmp_path,monkeypatch):
    raw,workspace,template=approved_config(tmp_path,monkeypatch)
    factory=config.build_host_policy_factory()
    current=identity(task_id="new-root",agent_id="new-agent",run_token="new-run",fencing_token=9)
    launch=factory.prepare(identity=current,workspace=workspace,tools=("read_file",),permissions=("repo:read",))
    try:
        assert isinstance(factory,HostPolicyLaunchFactory)
        assert launch.identity==current
        assert launch.grant.workspace_root==str(workspace)
        assert launch.grant.approvals==()
        assert launch.grant.parent_grant_hash is None
        assert (launch.mount.code.path/"module.py").read_bytes()==b"approved=True\n"
        assert factory.task_store_root==Path(raw["task_store_root"])
    finally:launch.cleanup_after_pane_closed()
    assert set(Path(raw["storage"]).iterdir()) == {Path(raw["storage"])/".ownership.lock"}

@pytest.mark.parametrize("fault",["consumer","outside","tools","permission","stale"])
def test_root_authorization_denies_before_host_files_are_created(tmp_path,monkeypatch,fault):
    raw,workspace,template=approved_config(tmp_path,monkeypatch)
    if fault=="stale":raw["templates"][template.identity.consumer]=replace(template,expires_at="2026-01-02T00:00:00+00:00").to_json()
    factory=config.build_host_policy_factory()
    current=identity(consumer="github:foreign") if fault=="consumer" else identity()
    target=tmp_path if fault=="outside" else workspace
    with pytest.raises(SecurityError):
        factory.prepare(identity=current,workspace=target,
            tools=("terminal",) if fault=="tools" else ("read_file",),
            permissions=("external",) if fault=="permission" else ("repo:read",))
    assert not list(Path(raw["storage"]).iterdir())

@pytest.mark.parametrize("fault",["unknown","schema-bool","uid","ttl","runtime","consumer","storage-mode","storage-symlink"])
def test_closed_host_composition_configuration_denies_invalid_authority(tmp_path,monkeypatch,fault):
    raw,workspace,template=approved_config(tmp_path,monkeypatch)
    if fault=="unknown":raw["task_prompt"]="cannot configure host"
    elif fault=="schema-bool":raw["schema_version"]=True
    elif fault=="uid":raw["host_uid"]=os.geteuid()+1
    elif fault=="ttl":raw["grant_ttl_seconds"]=0
    elif fault=="runtime":raw["runtime"]=raw["runtime"][:1]
    elif fault=="consumer":raw["templates"]={"github:foreign":template.to_json()}
    elif fault=="storage-mode":Path(raw["storage"]).chmod(0o755)
    else:
        target=tmp_path/"store-link";target.symlink_to(raw["storage"],target_is_directory=True);raw["storage"]=str(target)
    with pytest.raises(SecurityError):config.build_host_policy_factory()

def test_real_configuration_rejects_mutable_parent_even_if_payload_claims_root(tmp_path):
    target=tmp_path/"host.json";target.write_text(json.dumps({"schema_version":1}))
    with pytest.raises(SecurityError,match="untrusted"):config._read_configuration(target)

def test_child_factory_requires_current_canonical_session_before_verification(tmp_path,monkeypatch):
    raw,workspace,template=approved_config(tmp_path,monkeypatch)
    running=Path(raw["task_store_root"])/"running";running.mkdir()
    path=running/"parent.json"
    path.write_text(json.dumps(dict(id="parent",run_token="run-1",repo="Bbambaaamm/herdr",
        fencing_token=7,execution_session=dict(agent_name="parent-agent",pane_id="pane",pane_marker="marker"))))
    path.chmod(0o600)
    with pytest.raises(SecurityError,match="authenticated parent"):
        config.child_factory_for_root(path,dict(task_id="parent",run_token="run-1",agent="parent-agent",pane="pane",marker="marker"))
    with pytest.raises(SecurityError,match="current parent"):
        config.child_factory_for_root(path,dict(task_id="parent",run_token="run-1",agent="foreign",pane="pane",marker="marker"))


def test_current_consumer_restriction_cannot_be_bypassed_by_retained_parent(tmp_path,monkeypatch):
    raw,workspace,template=approved_config(tmp_path,monkeypatch)
    old_rule=template.tool_rules[0]
    parent=replace(template,credential_refs=("pool:provider-a:retired",))
    with pytest.raises(SecurityError,match="credential references"):
        config.build_host_policy_factory(parent_grant=parent)
    parent=template
    restricted=replace(template,tool_rules=(replace(old_rule,allowed_arg_keys=("path",)),))
    raw["templates"][template.identity.consumer]=restricted.to_json()
    with pytest.raises(SecurityError,match="argument ceiling"):
        config.build_host_policy_factory(parent_grant=parent)


@pytest.mark.parametrize("fault", ["none", "symlink", "directory-inode", "foreign-identity"])
def test_dead_host_cleanup_reclaims_only_owned_launch_container(tmp_path, monkeypatch, fault):
    import os, stat
    raw, workspace, template = approved_config(tmp_path, monkeypatch)
    factory = config.build_host_policy_factory()
    current = identity(task_id="orphan", agent_id="orphan-agent", run_token="orphan-run", fencing_token=12)
    outside = tmp_path / "foreign"; outside.mkdir(); (outside / "keep").write_text("preserve")
    pid = os.fork()
    if pid == 0:
        try:
            factory.prepare(identity=current,workspace=workspace,tools=("read_file",),permissions=("repo:read",))
            os._exit(0)
        except BaseException:
            import traceback; traceback.print_exc()
            os._exit(3)
    _, status = os.waitpid(pid,0)
    assert os.waitstatus_to_exitcode(status) == 0
    storage = Path(raw["storage"]); directory, = storage.glob("launch-*")
    record, = storage.glob("ownership-*.json")
    assert record.stat().st_mode & 0o777 == 0o600
    original_inode = directory.stat().st_ino
    if fault == "symlink":
        (directory / "unowned-link").symlink_to(outside, target_is_directory=True)
        with pytest.raises(SecurityError): factory.cleanup_orphan(current)
        assert directory.exists() and record.exists()
        (directory / "unowned-link").unlink()
    elif fault == "directory-inode":
        original = storage / "held-original"
        directory.rename(original); directory.mkdir(mode=0o700)
        (directory / "keep").write_text("foreign replacement")
        with pytest.raises(SecurityError): factory.cleanup_orphan(current)
        assert (directory / "keep").read_text() == "foreign replacement" and record.exists()
        (directory / "keep").unlink(); directory.rmdir(); original.rename(directory)
    elif fault == "foreign-identity":
        assert not factory.cleanup_orphan(identity(task_id="different", agent_id="orphan-agent", run_token="orphan-run", fencing_token=12))
        assert directory.stat().st_ino == original_inode and record.exists()
    assert factory.cleanup_orphan(current)
    assert not directory.exists() and not record.exists()
    assert not factory.cleanup_orphan(current)
    assert (outside / "keep").read_text() == "preserve"

def test_live_original_host_cannot_be_cold_reaped(tmp_path,monkeypatch):
    from herdr.launch_ownership import cleanup_orphan
    raw,workspace,template=approved_config(tmp_path,monkeypatch)
    factory=config.build_host_policy_factory()
    current=identity(task_id="still-live",agent_id="agent",run_token="run",fencing_token=14)
    launch=factory.prepare(identity=current,workspace=workspace,tools=("read_file",),permissions=("repo:read",))
    try:
        with pytest.raises(SecurityError,match="still alive"):
            cleanup_orphan(Path(raw["storage"]),current)
        assert launch._ownership.directory.exists()
        # A lost runtime map can still find this exact private host object.
        assert factory.cleanup_orphan(current)
        assert launch._ownership is None
    finally:
        if launch._ownership is not None: launch.cleanup_after_pane_closed()

def test_enabled_consumer_worktree_ceiling_is_inside_its_parent_workspace():
    consumers=json.loads((Path(__file__).resolve().parents[2]/
        "agent-stack/config/github-intake-consumers.json").read_text())["consumers"]
    for item in consumers:
        if not item.get("enabled") or not item.get("worktree_root"):continue
        assert Path(item["workspace"]) in Path(item["worktree_root"]).parents,item["repository"]

def test_canonical_nested_child_worktree_passes_actual_factory_parent_ceiling(tmp_path,monkeypatch):
    from herdr.security import InvocationIdentity
    raw,workspace,parent=approved_config(tmp_path,monkeypatch)
    child_workspace=workspace/"worktrees"/"child";child_workspace.mkdir(parents=True)
    factory=config.build_host_policy_factory(parent_grant=parent)
    child=InvocationIdentity(parent.identity.consumer,"child-agent",parent.identity.agent_id,
        parent.identity.task_id,"child-task","child-run",parent.identity.fencing_token+1)
    launch=factory.prepare_child(identity=child,workspace=child_workspace,
        tools=parent.scope.tools,permissions=parent.scope.permissions)
    try:
        launch.grant.require_logical_subset_of(parent)
        assert launch.grant.workspace_root==str(child_workspace)
    finally:launch.cleanup_after_pane_closed()

@pytest.mark.parametrize("repository", [
    "Bbambaaamm/Autonomous-Quant-Lab",
    "Bbambaaamm/dotacni-majak",
    "Bbambaaamm/herdr",
])
def test_enabled_consumer_narrowing_retains_coding_handoff_for_root_and_child(
        tmp_path, monkeypatch, repository):
    from types import SimpleNamespace
    from herdr.security import InvocationIdentity, RiskClass, ToolRule
    from herdr.work_configuration import preflight_handoff
    from herdr.work_hygiene import LocalCommitPolicy
    from tests.herdr.test_check_runner import environment

    consumers=json.loads((Path(__file__).resolve().parents[2]/
        "agent-stack/config/github-intake-consumers.json").read_text())["consumers"]
    consumer=next(item for item in consumers if item["repository"]==repository)
    assert consumer["enabled"]
    raw,workspace,template=approved_config(tmp_path,monkeypatch)
    # The host allows verification, but intake must actually request it:
    # host configuration deliberately narrows both scope and rules.
    ceiling_tools=tuple(dict.fromkeys((*consumer["parent_tools"],"herdr_verify_work")))
    special={"herdr_delegate_child","herdr_verify_work","herdr_submit_result"}
    file_tools=tuple(tool for tool in ceiling_tools if tool not in special)
    rules=(*grant(workspace,tools=file_tools).tool_rules,
        ToolRule(tool="herdr_delegate_child",risk=RiskClass.DELEGATION,
            allowed_arg_keys=("key","role","objective","prompt","tool","permission","cwd","ownership"),
            requires_sandbox=True),
        ToolRule(tool="herdr_verify_work",risk=RiskClass.READ,
            allowed_arg_keys=("request_id","handoff"),requires_sandbox=True),
        ToolRule(tool="herdr_submit_result",risk=RiskClass.RESULT_SUBMISSION,
            allowed_arg_keys=("status","evidence","summary"),
            allowed_roots=(str(workspace),),requires_sandbox=True))
    template=grant(workspace,tools=ceiling_tools,rules=rules)
    template=replace(template,
        identity=replace(template.identity,consumer="github:"+repository),
        scope=replace(template.scope,permissions=tuple(consumer["parent_permissions"])),
        tool_rules=rules)
    raw["templates"]={template.identity.consumer:template.to_json()}
    profile=environment()
    profile=replace(profile,executables=(*profile.executables,"/usr/bin/git"))
    work=SimpleNamespace(local_commit_policy=LocalCommitPolicy(
        "consumer-handoff-test",profile,"0"*64,str(tmp_path/"hooks"),()))
    factory=config.build_host_policy_factory()
    parent=factory.prepare(identity=template.identity,workspace=workspace,
        tools=tuple(consumer["parent_tools"]),
        permissions=tuple(consumer["parent_permissions"]))
    try:
        preflight_handoff(work,parent,{"kind":"coding"},require_slot=False)
        child_workspace=workspace/"worktrees"/"child"
        child_workspace.mkdir(parents=True)
        child_identity=InvocationIdentity(parent.identity.consumer,"nested-agent",
            parent.identity.agent_id,parent.identity.task_id,"nested-task",
            "nested-run",parent.identity.fencing_token+1)
        child_factory=config.build_host_policy_factory(parent_grant=parent.grant)
        child=child_factory.prepare_child(identity=child_identity,
            workspace=child_workspace,
            tools=tuple(tool for tool in parent.grant.scope.tools if tool!="herdr_delegate_child"),
            permissions=parent.grant.scope.permissions)
        try:
            child.grant.require_logical_subset_of(parent.grant)
            preflight_handoff(work,child,{"kind":"coding"},require_slot=False)
        finally:child.cleanup_after_pane_closed()
    finally:parent.cleanup_after_pane_closed()

@pytest.mark.parametrize("payload_bytes", [3500000,4194305])
def test_protected_reader_supports_complete_runtime_manifest_with_a_finite_bound(
        tmp_path,monkeypatch,payload_bytes):
    from types import SimpleNamespace
    path=tmp_path/"host-policy.json"
    path.write_text(json.dumps({"inventory": "x"*payload_bytes}))
    path.chmod(0o600)
    original_lstat=Path.lstat
    original_fstat=os.fstat
    protected={path,*path.parents}
    def protected_metadata(info):
        # Simulate only trusted ownership; size and stable inode/timestamps
        # still come from the actual file and reader syscalls.
        names=("st_dev","st_ino","st_size","st_mtime_ns","st_ctime_ns","st_mode")
        raw={name:getattr(info,name) for name in names}
        raw.update(st_uid=0,st_mode=info.st_mode&~0o022)
        return SimpleNamespace(**raw)
    def trusted_lstat(target,*args,**kwargs):
        info=original_lstat(target,*args,**kwargs)
        return protected_metadata(info) if target in protected else info
    monkeypatch.setattr(Path,"lstat",trusted_lstat)
    monkeypatch.setattr(os,"fstat",lambda fd:protected_metadata(original_fstat(fd)))
    if payload_bytes==3500000:
        assert len(config._read_configuration(path)["inventory"])==payload_bytes
    else:
        with pytest.raises(SecurityError,match="host configuration is untrusted"):
            config._read_configuration(path)
