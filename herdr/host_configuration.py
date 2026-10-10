"""Trusted standalone composition of host launch factories.

Production uses a fixed root-owned configuration outside repositories. It
contains approved hashes and policy ceilings, never raw provider credentials.
Missing or writable configuration denies before a pane or provider is touched.
"""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime,timedelta,UTC
import json,os,stat,uuid
from pathlib import Path
from .policy_launch import (ApprovedTree, ApprovedImmutableTree, ApprovedProfile,
                           HostPolicyLaunchFactory,CODE_TARGET,RUNTIME_TARGETS)
from .security import SecurityError,SecurityGrant,InvocationIdentity

HOST_POLICY_CONFIG=Path("/etc/herdr/host-policy.json")
# Complete pinned Hermes source, venv and Python manifests exceed 2 MiB.
# Keep the root-owned, stable-reader input bounded at 4 MiB.
MAX_CONFIG=4194304

def require(ok,reason):
    if not ok:raise SecurityError(reason)

def _read_configuration(path):
    path=Path(path)
    require(path.is_absolute() and ".." not in path.parts,"absolute fixed host configuration required")
    for parent in reversed(path.parents):
        info=parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022,
                "host configuration parent is untrusted")
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid==0 and not before.st_mode&0o022
                and 0<before.st_size<=MAX_CONFIG,"host configuration is untrusted")
        raw=b""
        while len(raw)<=MAX_CONFIG:
            chunk=os.read(fd,min(65536,MAX_CONFIG+1-len(raw)))
            if not chunk:break
            raw+=chunk
        after=os.fstat(fd);named=path.lstat()
        stamp=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_mode,x.st_uid)
        require(stamp(before)==stamp(after)==stamp(named) and len(raw)==before.st_size,
                "host configuration changed during read")
        parsed=json.loads(raw)
        require(isinstance(parsed,dict),"host configuration object required")
        return parsed
    finally:os.close(fd)

def _tree(raw, *, immutable=False):
    require(isinstance(raw,dict) and set(raw)=={"source","target","files","executable_files","max_bytes","max_file_bytes"},
            "closed approved host tree schema required")
    require(isinstance(raw["source"],str) and Path(raw["source"]).is_absolute()
            and isinstance(raw["target"],str) and Path(raw["target"]).is_absolute(),
            "absolute approved source/target required")
    require(isinstance(raw["executable_files"],list)
            and all(isinstance(name,str) for name in raw["executable_files"])
            and set(raw["executable_files"])<=set(raw["files"]),
            "approved executable inventory invalid")
    if immutable:
        return ApprovedImmutableTree(Path(raw["source"]),Path(raw["target"]),raw["files"],
            raw["max_bytes"],raw["max_file_bytes"])
    return ApprovedTree(Path(raw["source"]),Path(raw["target"]),raw["files"],
        tuple(raw["executable_files"]),raw["max_bytes"],raw["max_file_bytes"])


def _private_profile(raw):
    """The same root policy approves profile bytes and their credential window.

    The release operator validates/refreshed credentials before publishing this
    approval. Workers only check the current approval window; they never refresh
    credentials or self-approve changed file hashes. Native/provider validation
    is a separate acceptance gate, not implied by this offline preflight.
    """
    require(isinstance(raw,dict) and set(raw)=={"profile","credential_approval"},
            "closed private host policy required")
    definition=raw["profile"]
    require(isinstance(definition,dict) and set(definition)=={"name","source","files"},
            "closed private profile approval required")
    require(isinstance(definition["source"],str),"private profile source invalid")
    profile=ApprovedProfile(definition["name"],Path(definition["source"]),definition["files"])
    approval=raw["credential_approval"]
    require(isinstance(approval,dict) and set(approval)=={
        "schema_version","profile_sha256","valid_until","minimum_ttl_seconds"}
        and approval["schema_version"]=="herdr-profile-credential-approval-1"
        and approval["profile_sha256"]==profile.identity["manifest_sha256"],
        "credential approval profile binding mismatch")
    require(type(approval["minimum_ttl_seconds"]) is int
            and 60<=approval["minimum_ttl_seconds"]<=86400,
            "finite credential approval floor required")
    require(isinstance(approval["valid_until"],str),"credential approval expiry invalid")
    try:expiry=datetime.fromisoformat(approval["valid_until"])
    except ValueError as exc:raise SecurityError("credential approval expiry invalid") from exc
    require(expiry.tzinfo is not None,"credential approval expiry must be timezone aware")
    return profile,expiry,approval["minimum_ttl_seconds"]

def build_host_policy_factory(*,parent_grant=None,configuration_path=HOST_POLICY_CONFIG,
                              retained_parent_verify=None):
    """Only executable host entrypoints select this configuration path."""
    raw=_read_configuration(configuration_path)
    required={"schema_version","host_uid","code","runtime","storage","templates",
              "grant_ttl_seconds","task_store_root"}
    version=raw.get("schema_version")
    private=type(version) is int and version==2
    if private:required=required|{"private_launch"}
    require(set(raw) in (required,required|{"work_contracts"})
            and type(version) is int and version in (1,2),
            "closed host composition schema required")
    require(type(raw["host_uid"]) is int and raw["host_uid"]==os.geteuid(),"host configuration UID mismatch")
    require(type(raw["grant_ttl_seconds"]) is int and 1<=raw["grant_ttl_seconds"]<=3600,
            "finite host grant lifetime required")
    code=_tree(raw["code"],immutable=private)
    runtime=tuple(_tree(x,immutable=private) for x in raw["runtime"])
    require(code.target==CODE_TARGET and len(runtime)==2 and {x.target for x in runtime}==RUNTIME_TARGETS,
            "exact approved host code/runtime inventory required")
    if private:
        from .host_bootstrap import SHIM_SOURCE,STAGE1_SOURCE,STAGE2_SOURCE,PYTHON_TARGET,PYTHON_EXECUTABLE
        python=next(tree for tree in runtime if tree.target==PYTHON_TARGET)
        require({SHIM_SOURCE,STAGE1_SOURCE,STAGE2_SOURCE,"agent-stack/policy-bin/herdr"} <= set(code.files),
                "complete private runtime entrypoints required")
        python_raw=next(row for row in raw["runtime"] if row["target"]==str(PYTHON_TARGET))
        require({SHIM_SOURCE,"agent-stack/policy-bin/herdr"} <= set(raw["code"]["executable_files"])
                and PYTHON_EXECUTABLE in python.files and PYTHON_EXECUTABLE in python_raw["executable_files"],
                "private executable entrypoint approval required")
    templates=raw["templates"]
    require(isinstance(templates,dict) and 1<=len(templates)<=32,"bounded consumer policies required")
    grants={consumer:SecurityGrant.from_dict(value) for consumer,value in templates.items()}
    require(all(value.identity.consumer==consumer and value.parent_grant_hash is None
                for consumer,value in grants.items()),"consumer root policy mismatch")
    storage=Path(raw["storage"]);task_root=Path(raw["task_store_root"])
    require(storage.is_absolute() and task_root.is_absolute(),"absolute private host storage required")
    require(storage.resolve(strict=True)==storage and task_root.resolve(strict=True)==task_root,
            "host storage cannot use symlinks")
    info=storage.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.geteuid() and not info.st_mode&0o077,
            "private host launch storage unavailable")
    require(parent_grant is None or isinstance(parent_grant,SecurityGrant),"verified parent grant required")
    if parent_grant is not None:
        ceiling=grants.get(parent_grant.identity.consumer)
        require(ceiling is not None and ceiling.is_active(),"current consumer policy unavailable")
        # Compare logical capabilities under the current ceiling. Physical
        # result slots belong to the original full identity, which is verified
        # separately; they cannot be copied onto this synthetic identity.
        comparison=replace(parent_grant,parent_grant_hash=ceiling.hash,
            tool_rules=tuple(replace(rule,result_slot=None) if rule.tool=="herdr_submit_result" else rule
                             for rule in parent_grant.tool_rules),
            identity=replace(parent_grant.identity,parent_agent_id=ceiling.identity.agent_id,
                             parent_task_id=ceiling.identity.task_id))
        comparison.require_logical_subset_of(ceiling)
    def authorize(*,identity,workspace,tools,permissions):
        require(isinstance(identity,InvocationIdentity),"exact host invocation identity required")
        template=grants.get(identity.consumer)
        require(template is not None and template.is_active(),"current consumer authority unavailable")
        source=parent_grant or template
        require(source.identity.consumer==identity.consumer and source.is_active(),"parent consumer authority unavailable")
        workspace=Path(workspace).resolve(strict=True)
        allowed=Path(source.workspace_root)
        require(workspace==allowed or allowed in workspace.parents,"workspace outside host policy")
        require(set(tools)<=set(source.scope.tools) and set(permissions)<=set(source.scope.permissions),
                "requested tools/permissions exceed host ceiling")
        rules=[]
        for rule in source.tool_rules:
            if rule.tool not in tools:continue
            if rule.path_fields:
                require(any(workspace==Path(root) or Path(root) in workspace.parents for root in rule.allowed_roots),
                        "requested file root exceeds approved rule")
                rule=replace(rule,allowed_roots=(str(workspace),))
            if rule.tool == "herdr_submit_result":
                rule=replace(rule,result_slot=None)
            rules.append(rule)
        now=datetime.now(UTC);expiry=min(now+timedelta(seconds=raw["grant_ttl_seconds"]),
                                        datetime.fromisoformat(source.expires_at))
        grant=replace(source,grant_id="host-"+uuid.uuid4().hex,identity=identity,
            workspace_root=str(workspace),scope=replace(source.scope,tools=tuple(tools),permissions=tuple(permissions)),
            tool_rules=tuple(rules),approvals=(),issued_at=now.isoformat(),expires_at=expiry.isoformat(),
            parent_grant_hash=parent_grant.hash if parent_grant is not None else None)
        if parent_grant is not None:grant.require_logical_subset_of(parent_grant)
        return grant
    options={}
    if private:
        profile,_,_=_private_profile(raw["private_launch"])
        def preflight(name):
            current=_read_configuration(configuration_path)
            require(current==raw,"host private policy changed before profile seal")
            approved,expiry,floor=_private_profile(current["private_launch"])
            require(name==profile.name and approved.identity==profile.identity,
                    "host private profile changed before seal")
            require(expiry>=datetime.now(UTC)+timedelta(seconds=max(floor,raw["grant_ttl_seconds"]+60)),
                    "host credential approval is expired or insufficient")
            return True
        options=dict(approved_profile=profile,profile_preflight=preflight,
                     parent_approved_profile=profile if parent_grant is not None else None,
                     retained_parent_verify=retained_parent_verify)
    factory=HostPolicyLaunchFactory(code=code,runtime=runtime,storage=storage,authorize=authorize,
        writable_roots=tuple(x.workspace_root for x in grants.values()),parent_grant=parent_grant,
        **options)
    factory.task_store_root=task_root
    return factory

def _verified_parent(task_file,identity):
    """Resolve parent after stage-two publication, immediately before delegation."""
    from .policy_launch import verify_retained_policy_evidence
    raw=_read_configuration(HOST_POLICY_CONFIG)
    task_file=Path(task_file)
    expected_root=Path(raw["task_store_root"]).resolve(strict=True)
    require(task_file.resolve(strict=True)==task_file and task_file.parent.parent==expected_root,
            "parent task file outside canonical host store")
    fd=os.open(task_file,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==os.geteuid()
                and not info.st_mode&0o077 and info.st_nlink==1
                and 0<info.st_size<=1048576,"canonical task file untrusted")
        with os.fdopen(os.dup(fd),"rb") as stream:task=json.loads(stream.read(1048577))
        after=os.fstat(fd);named=task_file.lstat()
        stamp=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_mode,x.st_uid)
        require(stamp(info)==stamp(after)==stamp(named),"canonical task changed during grant read")
    finally:os.close(fd)
    session=task.get("execution_session")
    require(isinstance(session,dict) and task["id"]==identity["task_id"]
            and task["run_token"]==identity["run_token"]
            and session.get("agent_name")==identity["agent"] and session.get("pane_id")==identity["pane"]
            and session.get("pane_marker")==identity["marker"] and not session.get("closed_at"),
            "exact current parent session required")
    proof=session.get("invocation_policy");attestation=session.get("sandbox_attestation")
    require(isinstance(proof,dict) and isinstance(attestation,dict),"authenticated parent policy unavailable")
    parent_identity=InvocationIdentity.from_dict(proof["identity"])
    require(parent_identity.consumer=="github:"+task["repo"] and parent_identity.task_id==task["id"]
            and parent_identity.agent_id==identity["agent"] and parent_identity.run_token==task["run_token"]
            and parent_identity.fencing_token==task["fencing_token"],"parent grant identity changed")
    parent=verify_retained_policy_evidence(proof,identity=parent_identity,pid=int(session["sandbox_pid"]),
        attestation=attestation,require_bootstrap=True)
    return task,parent,proof


def child_factory_for_root(task_file,identity):
    """Revalidate retained physical parent evidence for each child admission."""
    identity=dict(identity)
    task_file=Path(task_file)
    task,parent,proof=_verified_parent(task_file,identity)
    def retained_parent_verify():
        current,current_grant,current_proof=_verified_parent(task_file,identity)
        require(current_grant==parent,"retained parent grant changed before child admission")
        return current_grant,current_proof.get("approved_profile")
    factory=build_host_policy_factory(parent_grant=parent,
        retained_parent_verify=retained_parent_verify)
    factory.verified_parent_task=task
    return factory

def read_canonical_parent(root, task_id, run_token):
    """Read a protected current/terminal root task without editing its state."""
    import re
    require(isinstance(task_id,str) and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}",task_id)
            and isinstance(run_token,str) and 0<len(run_token)<=128,
            "canonical parent identity invalid")
    root=Path(root)
    require(root.is_absolute() and root.resolve(strict=True)==root,"canonical task root invalid")
    info=root.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.geteuid() and not info.st_mode&0o022,
            "canonical task root untrusted")
    found=[]
    root_fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        for state in ("running","blocked","pending","done","failed"):
            try:
                directory=os.open(state,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=root_fd)
            except FileNotFoundError:
                continue
            try:
                state_info=os.fstat(directory)
                require(state_info.st_uid==os.geteuid() and not state_info.st_mode&0o022,
                        "canonical task state untrusted")
                try:
                    fd=os.open(task_id+".json",os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,dir_fd=directory)
                except FileNotFoundError:
                    continue
                try:
                    before=os.fstat(fd)
                    require(stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid()
                            and not before.st_mode&0o077 and before.st_nlink==1
                            and 0<before.st_size<=1048576,"canonical parent task untrusted")
                    raw=b""
                    while len(raw)<=1048576:
                        chunk=os.read(fd,min(65536,1048577-len(raw)))
                        if not chunk:break
                        raw+=chunk
                    after=os.fstat(fd)
                    named=os.stat(task_id+".json",dir_fd=directory,follow_symlinks=False)
                    stamp=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_mode,x.st_uid,x.st_nlink)
                    require(stamp(before)==stamp(after)==stamp(named) and len(raw)==before.st_size,
                            "canonical parent changed during read")
                    def unique(pairs):
                        result={}
                        for key,value in pairs:
                            require(key not in result,"canonical parent duplicate field")
                            result[key]=value
                        return result
                    task=json.loads(raw,object_pairs_hook=unique)
                    require(isinstance(task,dict) and task.get("id")==task_id,"canonical parent identity invalid")
                    if task.get("run_token")==run_token:
                        found.append(task)
                finally:
                    os.close(fd)
            finally:
                os.close(directory)
        require(len(found)<=1,"canonical parent attempt ambiguous")
        return found[0] if found else None
    finally:
        os.close(root_fd)
