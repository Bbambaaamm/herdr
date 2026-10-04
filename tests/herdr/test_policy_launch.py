from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from herdr.policy_launch import FrozenTree, PolicyMount, CODE_TARGET, BUNDLE_TARGET, RUNTIME_TARGETS, IDENTITY_ENV
from herdr.security import InvocationIdentity, SecurityError, NetworkAccess, stage_policy_bundle, load_policy_bundle
from tests.herdr.test_security import grant

def frozen(tmp_path, *, target=CODE_TARGET, files=None):
    source = tmp_path / ("source-" + uuid.uuid4().hex)
    source.mkdir()
    content = {"module.py": b"approved = True\n"} if files is None else files
    for name, raw in content.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    storage = tmp_path / "store"
    storage.mkdir(exist_ok=True)
    tree = FrozenTree.create(source, target=target, storage=storage,
                             files={name: hashlib.sha256(raw).hexdigest() for name, raw in content.items()})
    return source, tree

def test_snapshot_is_independent_of_mutable_source_and_detects_added_code(tmp_path):
    source, tree = frozen(tmp_path, files={"pkg/__init__.py": b"x=1"})
    try:
        (source / "pkg/__init__.py").write_text("x=2")
        tree.verify()
        assert (tree.path / "pkg/__init__.py").read_text() == "x=1"
        tree.path.chmod(0o700)
        (tree.path / "injected.py").write_text("execute()")
        with pytest.raises(SecurityError, match="unexpected frozen file"):
            tree.verify()
        (tree.path / "injected.py").unlink()
    finally:
        tree.cleanup_after_pane_closed()

@pytest.mark.parametrize("kind", ["symlink", "fifo", "digest", "ancestor", "worker-write", "bytes"])
def test_snapshot_rejects_unsafe_or_unapproved_sources(tmp_path, kind):
    source = tmp_path / "source"
    source.mkdir()
    storage = tmp_path / "store"
    storage.mkdir()
    body = b"approved"
    name = "code.py"
    if kind == "symlink":
        (source / name).symlink_to("/etc/passwd")
    elif kind == "fifo":
        os.mkfifo(source / name)
    elif kind == "ancestor":
        (source / "package").symlink_to(storage, target_is_directory=True)
        name = "package/code.py"
        (storage / "code.py").write_bytes(body)
    else:
        (source / name).write_bytes(body)
    expected = "a"*64 if kind == "digest" else hashlib.sha256(body).hexdigest()
    with pytest.raises((SecurityError, OSError)):
        FrozenTree.create(source, target=CODE_TARGET, storage=storage, files={name: expected},
                          writable_roots=(tmp_path,) if kind == "worker-write" else (),
                          max_bytes=1 if kind == "bytes" else 1024)
    assert not list(storage.glob("herdr-policy-frozen-*"))

@pytest.mark.parametrize("name", ["../outside", "a/../../outside", "/absolute", "a//b", "a\\b"])
def test_snapshot_rejects_traversal(tmp_path, name):
    source = tmp_path / "source"
    source.mkdir()
    storage = tmp_path / "store"
    storage.mkdir()
    with pytest.raises(SecurityError):
        FrozenTree.create(source, target=CODE_TARGET, storage=storage, files={name: "a"*64})
    assert not list(storage.glob("herdr-policy-frozen-*"))

def sandbox_module():
    path = Path(__file__).resolve().parents[2] / "agent-stack/bin/agent_durable_sandbox.py"
    spec = importlib.util.spec_from_file_location("policy_launch_test_sandbox", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def mount(tmp_path):
    _, code = frozen(tmp_path)
    runtime = [frozen(tmp_path, target=target)[1] for target in sorted(RUNTIME_TARGETS)]
    stage = stage_policy_bundle(tmp_path / "store" / ("grant-" + uuid.uuid4().hex))
    return PolicyMount(stage, code, runtime)

def cleanup(item):
    item.stage.close()
    item.stage.path.unlink(missing_ok=True)
    for tree in (item.code, *item.runtime):
        tree.cleanup_after_pane_closed()

def test_policy_mount_requires_both_exact_runtime_snapshots(tmp_path):
    item = mount(tmp_path)
    try:
        with pytest.raises(SecurityError, match="immutable Hermes/Python"):
            PolicyMount(item.stage, item.code, ())
        rows = item.descriptors()
        assert {x["target"] for x in rows} == {str(CODE_TARGET), str(BUNDLE_TARGET), *map(str,RUNTIME_TARGETS)}
        assert len(rows) == 4
    finally:
        cleanup(item)

@pytest.mark.parametrize("mutation", ["inode", "target", "duplicate", "unused"])
def test_fd_launcher_rejects_ambiguous_or_changed_mounts(tmp_path, mutation):
    item = mount(tmp_path)
    try:
        rows = item.descriptors()
        if mutation == "inode":
            rows[0]["inode"] += 1
        elif mutation == "target":
            rows[0]["target"] += "/wrong"
        elif mutation == "duplicate":
            rows.append(dict(rows[0]))
        args = ["/usr/bin/bwrap"]
        for row in item.descriptors()[:(-1 if mutation == "unused" else None)]:
            args += ["--ro-bind-fd", str(row["fd"]), row["target"]]
        code = sandbox_module()._POLICY_FD_LAUNCHER
        result = subprocess.run(["/usr/bin/python3","-I","-S","-c",code,json.dumps(rows),*args],
                                capture_output=True, timeout=5)
        assert result.returncode != 0
        assert b"policy_fd_" in result.stderr
    finally:
        cleanup(item)

@pytest.mark.parametrize("shadow",[False,True])
def test_actual_bwrap_seals_same_inode_after_mount_and_denies_writes(tmp_path, monkeypatch,shadow):
    sandbox = sandbox_module()
    if not sandbox.BWRAP.is_file():
        pytest.skip("bwrap prerequisite unavailable")
    workspace = tmp_path / "worktrees" / "workspace"
    workspace.mkdir(parents=True)
    config, releases = tmp_path / "config", tmp_path / "releases"
    config.mkdir()
    releases.mkdir()
    monkeypatch.setattr(sandbox,"HERDR_CONFIG",config)
    monkeypatch.setattr(sandbox,"HERDR_RELEASES",releases)
    monkeypatch.setattr(sandbox,"DEFAULT_WRITABLE",())
    real = tmp_path / "herdr"
    real.write_text("#!/bin/sh\nexit 0\n")
    real.chmod(0o755)
    policy = tmp_path / "cli-policy"
    policy.write_text("#!/bin/sh\nexit 2\n")
    policy.chmod(0o555)
    mine = tmp_path / "results" / "child-task.result.json"
    mine.parent.mkdir()
    mine.touch()
    item = mount(tmp_path)
    fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    info = os.fstat(fd)
    pin = sandbox.PinnedWorktree(workspace, fd, info.st_dev, info.st_ino, workspace.parent)
    marker = "policy-probe-" + uuid.uuid4().hex
    planned = grant(workspace)
    identity = planned.identity
    env = {**os.environ, "HERDR_DURABLE_TASK_PANE":marker,
           **{key:str(getattr(identity,field)) for field,key in IDENTITY_ENV.items()}}
    args = sandbox.command(workspace, real, writable=(mine,), policy=policy,
                           child_workspace_writable=True, pinned_worktree=pin, policy_mount=item)
    if shadow:
        unrelated=tmp_path/"unrelated-shadow.py"
        unrelated.write_text("unrelated = True")
        index=args.index("--")
        args[index:index]=["--ro-bind",str(unrelated),str(CODE_TARGET/"module.py")]
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE, env=env)
    try:
        pid = None
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail(process.stderr.read(8192).decode())
            rows = []
            for proc in Path("/proc").iterdir():
                if not proc.name.isdigit():
                    continue
                try:
                    with (proc / "environ").open("rb") as stream:
                        raw = stream.read(262145)
                    if ("HERDR_DURABLE_TASK_PANE="+marker).encode() in raw.split(b"\0"):
                        rows.append({"pid":int(proc.name)})
                except OSError:
                    pass
            pid = sandbox.inner_pid({"foreground_processes":rows}, marker)
            if pid:
                break
            time.sleep(0.02)
        assert pid
        if shadow:
            assert not sandbox.verify(pid,real,marker,policy=policy,pinned_worktree=pin,
                                      child_workspace_writable=True,policy_mount=item)
            with pytest.raises(SecurityError,match="unexpected mount"):
                item.verify_mounted(pid)
            assert os.fstat(item.stage.fd).st_size==0
            return
        assert sandbox.verify(pid,real,marker,policy=policy,pinned_worktree=pin,
                              child_workspace_writable=True,policy_mount=item)
        attestation={"task_id":identity.task_id,"run_token":identity.run_token,"sandbox_pid":pid}
        wrong = replace(identity, run_token="different")
        with pytest.raises(SecurityError, match="process identity"):
            item.seal(pid, replace(planned,identity=wrong),identity=wrong,attestation=attestation,
                      tools=planned.scope.tools,permissions=planned.scope.permissions,
                      private_key=Ed25519PrivateKey.generate(),key_id="ephemeral-test")
        assert os.fstat(item.stage.fd).st_size == 0
        bound, sealed = item.seal(pid,planned,identity=identity,attestation=attestation,
                                 tools=planned.scope.tools,permissions=planned.scope.permissions,
                                 private_key=Ed25519PrivateKey.generate(),key_id="ephemeral-test")
        assert not bound.runtime_assurance.credentials_isolated
        assert bound.runtime_assurance.network_access == NetworkAccess.GLOBAL
        inside = Path(f"/proc/{pid}/root") / str(BUNDLE_TARGET).lstrip("/")
        assert inside.stat().st_ino == item.stage.inode == sealed.inode
        assert load_policy_bundle(inside,identity).hash == bound.hash
        from herdr.policy_launch import PreparedPolicyLaunch, process_start_ticks, verify_retained_policy_evidence
        retained = PreparedPolicyLaunch(item,bound,None,"probe")
        retained.sealed,retained._process_start_ticks = sealed,process_start_ticks(pid)
        proof = retained.evidence()
        assert verify_retained_policy_evidence(proof,identity=identity,pid=pid,attestation=attestation).hash == bound.hash
        for field in ("bundle_inode","process_start_ticks"):
            changed = json.loads(json.dumps(proof))
            changed[field] += 1
            with pytest.raises(SecurityError):
                verify_retained_policy_evidence(changed,identity=identity,pid=pid,attestation=attestation)
        changed = json.loads(json.dumps(proof))
        changed["tree_identities"][str(CODE_TARGET)]["inode"] += 1
        with pytest.raises(SecurityError):
            verify_retained_policy_evidence(changed,identity=identity,pid=pid,attestation=attestation)
        with pytest.raises(SecurityError,match="attestation"):
            verify_retained_policy_evidence(proof,identity=identity,pid=pid,attestation={**attestation,"run_token":"foreign"})
        script = """import json,pathlib,sys
result=pathlib.Path(sys.argv[1]); observed={}
for target in sys.argv[2:]:
    try:
        pathlib.Path(target).write_text("tamper")
        observed[target]=True
    except OSError:
        observed[target]=False
result.write_text(json.dumps(observed))
"""
        targets = [str(BUNDLE_TARGET), str(CODE_TARGET / "module.py"),
                   *(str(target / "module.py") for target in sorted(RUNTIME_TARGETS)),
                   str(item.code.path / "module.py")]
        process.stdin.write((shlex.join(["/usr/bin/python3","-I","-S","-c",script,str(mine),*targets])+"\n").encode())
        process.stdin.flush()
        observed = None
        for _ in range(100):
            try:
                observed=json.loads(mine.read_text())
                break
            except ValueError:
                time.sleep(0.01)
        assert observed == dict.fromkeys(targets,False)
        item.verify_mounted(pid,sealed)
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        pin.close()
        cleanup(item)


def factory_for(tmp_path, item, authorize, parent=None):
    from herdr.policy_launch import ApprovedTree, HostPolicyLaunchFactory
    definitions=[]
    for tree in (item.code,*item.runtime):
        definitions.append(ApprovedTree(tree.path,tree.target,dict(tree.files)))
    return HostPolicyLaunchFactory(code=definitions[0],runtime=tuple(definitions[1:]),
                                   storage=tmp_path/"store",authorize=authorize,parent_grant=parent)

@pytest.mark.parametrize("fault",["none","identity","tools","permissions","workspace"])
def test_host_factory_rejects_missing_or_escalated_grant_before_copy(tmp_path,fault):
    item=mount(tmp_path)
    workspace=tmp_path/"worker"
    workspace.mkdir()
    planned=grant(workspace)
    identity=planned.identity
    value=planned
    if fault=="none":value=None
    elif fault=="identity":value=replace(planned,identity=replace(identity,run_token="foreign-run"))
    elif fault=="workspace":value=grant(tmp_path/"foreign")
    factory=factory_for(tmp_path,item,lambda **kw:value)
    before=set((tmp_path/"store").iterdir())
    try:
        with pytest.raises(SecurityError):
            factory.prepare(identity=identity,workspace=workspace,
                            tools=() if fault=="tools" else planned.scope.tools,
                            permissions=() if fault=="permissions" else planned.scope.permissions)
        assert set((tmp_path/"store").iterdir())==before
    finally:cleanup(item)

def test_child_factory_requires_accepted_parent_grant(tmp_path):
    item=mount(tmp_path)
    planned=grant(tmp_path)
    factory=factory_for(tmp_path,item,lambda **kw:planned)
    try:
        with pytest.raises(SecurityError,match="accepted host parent grant"):
            factory.prepare_child(identity=planned.identity,workspace=tmp_path,
                                  tools=planned.scope.tools,permissions=planned.scope.permissions)
    finally:cleanup(item)

def test_approved_source_manifest_is_copied_and_immutable(tmp_path):
    from herdr.policy_launch import ApprovedTree
    files={"module.py":"a"*64}
    definition=ApprovedTree(tmp_path,CODE_TARGET,files)
    files["module.py"]="b"*64
    assert definition.files["module.py"]=="a"*64
    with pytest.raises(TypeError):definition.files["module.py"]="c"*64

def test_factory_copy_failure_cleans_only_its_own_unmounted_snapshots(tmp_path):
    item=mount(tmp_path)
    workspace=tmp_path/"worker"
    workspace.mkdir()
    planned=grant(workspace)
    factory=factory_for(tmp_path,item,lambda **kw:planned)
    broken=dict(factory.runtime[1].files)
    broken["module.py"]="a"*64
    from herdr.policy_launch import ApprovedTree
    factory.runtime=(*factory.runtime[:1],replace(factory.runtime[1],files=broken))
    before=set((tmp_path/"store").iterdir())
    try:
        with pytest.raises(SecurityError,match="approved bytes"):
            factory.prepare(identity=planned.identity,workspace=workspace,
                            tools=planned.scope.tools,permissions=planned.scope.permissions)
        assert set((tmp_path/"store").iterdir())==before
    finally:cleanup(item)

def test_root_session_cannot_select_policy_authority_from_task_fields(tmp_path,monkeypatch):
    from tests.agent_stack.test_worker_handshake import worker
    calls=[]
    def herdr(args,**kw):
        calls.append(args)
        assert args[:2]==["agent","get"]
        return {"result":{"agent":{"kind":"hermes","pane_id":"coordinator","workspace_id":"workspace"}}}
    monkeypatch.setattr(worker,"_herdr_json",herdr)
    monkeypatch.setattr(worker,"HOST_POLICY_LAUNCH_FACTORY",None)
    task={"id":"root-task","repo":"Bbambaaamm/herdr","run_token":"root-run","fencing_token":1,
          "workspace":str(tmp_path),"policy_launch_factory":"model-selected",
          "security_grant":{"tools":["terminal"]}}
    with pytest.raises(RuntimeError,match="task_invocation_policy_missing"):
        worker.create_task_session(task)
    assert len(calls)==1

def test_managed_child_denies_without_host_factory_before_split_or_provider(tmp_path,monkeypatch):
    from herdr.runtime import HerdrChildRuntime,PreDeliveryFailure,AdmissionRegistry
    from herdr.scheduler import DynamicChildScheduler,AuditLog,ChildProposal
    scheduler=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"events"))
    scheduler.register_external_parent_attempt(task_id="parent-task",run_token="parent-run",
        idempotency_key="parent-key",agent_name="parent-agent",pane_id="parent-pane",marker="marker",
        repo="Bbambaaamm/herdr",issue="82",role="writer",tools=("read_file",),
        permissions=(),policy_profile="default")
    child=scheduler.delegate_child("parent-task","parent-run","inspect",
        ChildProposal("writer",("read_file",),"reader",("read_file",),child_task="inspect"))
    lease=scheduler.dispatch(task_ids={child.id})[0]
    class Runner:
        executable="/bin/true"
        def run(self,*args,**kwargs):raise AssertionError("No live mutation is allowed without policy")
    runtime=HerdrChildRuntime(scheduler,Runner(),cwd=tmp_path,
                             admission_registry=AdmissionRegistry(tmp_path/"registry"))
    monkeypatch.setattr(runtime,"prepare",lambda:None)
    monkeypatch.setattr(runtime,"_admit_child",lambda lease:None)
    monkeypatch.setattr(runtime,"_preflight_child_provider",lambda:pytest.fail("provider accessed without grant"))
    record=scheduler._tasks[child.id]
    with pytest.raises(PreDeliveryFailure,match="child_invocation_policy_missing"):
        runtime.run_managed_child(lease,"inspect",run_token=record.run_token,
                                  idempotency_key=record.idempotency_key)
    assert not record.execution_pane
    assert record.pre_delivery_failure

def test_root_fencing_is_monotonic_and_reconciliation_retains_identity(tmp_path,monkeypatch):
    from tests.agent_stack.test_worker_handshake import worker
    monkeypatch.setattr(worker,"archive_previous_result",lambda *args:None)
    task={"id":"root-task","attempts":0}
    worker.prepare_attempt(task)
    token,fence=task["run_token"],task["fencing_token"]
    task["attempt_state"]="delivery_uncertain"
    worker.prepare_attempt(task)
    assert (task["run_token"],task["fencing_token"])==(token,fence)
    task["attempt_state"]="retry_scheduled"
    task["attempts"]=1
    worker.prepare_attempt(task)
    assert task["fencing_token"]==fence+1 and task["run_token"]!=token

def test_policy_mount_rejects_writable_runtime_descendant_before_access(tmp_path,monkeypatch):
    import herdr.policy_launch as module
    item=mount(tmp_path)
    try:
        monkeypatch.setattr(module,"mount_rows",lambda pid:{
            str(BUNDLE_TARGET):{"ro"}, str(CODE_TARGET):{"ro"},
            str(CODE_TARGET/"injected"):{"rw"}})
        # The first bundle inode lookup is an unrelated mount in the host;
        # validate the directory rule directly by placing code first.
        original=item.descriptors
        monkeypatch.setattr(item,"descriptors",lambda:sorted(original(),key=lambda x:x["kind"]=="file"))
        with pytest.raises(SecurityError,match="unexpected mount below"):
            item.verify_mounted(os.getpid())
    finally:cleanup(item)


def proof_scheduler(tmp_path):
    from herdr.scheduler import DynamicChildScheduler,AuditLog,ChildProposal
    scheduler=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"proof-events"))
    scheduler.register_external_parent_attempt(task_id="parent-task",run_token="parent-run",
        idempotency_key="parent-key",agent_name="parent-agent",pane_id="parent-pane",marker="marker",
        repo="Bbambaaamm/herdr",issue="82",role="writer",tools=("read_file",),
        permissions=(),policy_profile="default")
    child=scheduler.delegate_child("parent-task","parent-run","inspect",
        ChildProposal("writer",("read_file",),"reader",("read_file",),child_task="inspect"))
    lease=scheduler.dispatch(task_ids={child.id})[0]
    record=scheduler._tasks[child.id]
    marker="child-"+record.run_token
    assert scheduler.bind_pre_delivery_pane(child.id,record.run_token,lease.agent_id,"child-pane",marker)
    identity=InvocationIdentity(consumer="github:"+record.repo,agent_id=record.agent_id,
        parent_agent_id=record.parent_agent_id,parent_task_id=record.parent_task_id,
        task_id=record.id,run_token=record.run_token,fencing_token=record.fencing_token)
    evidence={"schema_version":"herdr-policy-launch-2","grant_sha256":"a"*64,"bundle_sha256":"b"*64,
        "bundle_device":1,"bundle_inode":2,"code_sha256":"c"*64,
        "runtime_sha256":dict.fromkeys(map(str,RUNTIME_TARGETS),"d"*64),
        "tree_identities":{str(x):{"device":1,"inode":2} for x in (CODE_TARGET,*RUNTIME_TARGETS)},
        "process_start_ticks":123,
        "identity":identity.to_json(),"sandbox_attestation_sha256":"e"*64}
    return scheduler,record,marker,evidence

def test_policy_evidence_survives_restart_without_new_claim_or_shared_mutable_data(tmp_path):
    from herdr.scheduler import DynamicChildScheduler,AuditLog
    scheduler,record,marker,evidence=proof_scheduler(tmp_path)
    assert scheduler.attest_execution_sandbox(record.id,record.run_token,record.agent_id,
        "child-pane",marker,sandbox_pid=123,policy_sha256="f"*64,invocation_policy=evidence)
    expected=json.loads(json.dumps(evidence))
    evidence["identity"]["run_token"]="worker-mutation"
    assert record.execution_sandbox_attestation["invocation_policy"]==expected
    recovered=DynamicChildScheduler(audit_log=AuditLog(tmp_path/"proof-events"))
    recovered.replay()
    replayed=recovered._tasks[record.id]
    assert replayed.execution_sandbox_attestation["invocation_policy"]==expected
    assert (replayed.run_token,replayed.fencing_token,replayed.idempotency_key)==(
        record.run_token,record.fencing_token,record.idempotency_key)

@pytest.mark.parametrize("fault",["run","fence","parent","consumer","digest","runtime","extra","inode"])
def test_scheduler_rejects_malformed_or_cross_attempt_policy_evidence(tmp_path,fault):
    scheduler,record,marker,evidence=proof_scheduler(tmp_path)
    if fault=="run":evidence["identity"]["run_token"]="different"
    elif fault=="fence":evidence["identity"]["fencing_token"]+=1
    elif fault=="parent":evidence["identity"]["parent_task_id"]="different"
    elif fault=="consumer":evidence["identity"]["consumer"]="github:foreign"
    elif fault=="digest":evidence["bundle_sha256"]="invalid"
    elif fault=="runtime":evidence["runtime_sha256"].pop(next(iter(evidence["runtime_sha256"])))
    elif fault=="extra":evidence["untrusted_authority"]="root"
    elif fault=="inode":evidence["bundle_inode"]=True
    assert not scheduler.attest_execution_sandbox(record.id,record.run_token,record.agent_id,
        "child-pane",marker,sandbox_pid=123,policy_sha256="f"*64,invocation_policy=evidence)
    assert not record.execution_sandbox_verified

def test_policy_evidence_replay_rejects_tampering_in_the_protected_log(tmp_path):
    from herdr.scheduler import DynamicChildScheduler,AuditLog,SchedulerError
    scheduler,record,marker,evidence=proof_scheduler(tmp_path)
    assert scheduler.attest_execution_sandbox(record.id,record.run_token,record.agent_id,
        "child-pane",marker,sandbox_pid=123,policy_sha256="f"*64,invocation_policy=evidence)
    path=tmp_path/"proof-events"
    events=[json.loads(line) for line in path.read_text().splitlines()]
    event=next(event for event in events if event["event"]=="execution_sandbox_attested")
    event["attestation"]["invocation_policy"]["identity"]["run_token"]="foreign"
    path.write_text("".join(json.dumps(event)+"\n" for event in events))
    with pytest.raises(SchedulerError,match="invocation policy"):
        DynamicChildScheduler(audit_log=AuditLog(path)).replay()
