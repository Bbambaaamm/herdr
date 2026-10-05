"""Real offline Git/hook execution and exact owned publication/recovery."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import pytest

from herdr.work_hygiene import HostLocalCommitter, LocalCommitPolicy
from herdr.work_cycle import WorkContractError, WorkCycle, WorkPhase, WorkPlan
from herdr.workspace import ArtifactRef, WorkspaceManager
from tests.herdr.test_work_contract_host import factory_fixture
from tests.herdr.test_work_cycle import git

@pytest.fixture
def boundary_workspace():
    base = Path(os.environ.get("HERDR_BOUNDARY_TEST_ROOT", "/home/agentops/tmp"))
    if not base.is_dir(): pytest.skip("physical Git boundary workspace unavailable")
    target = Path(tempfile.mkdtemp(prefix="local-hygiene-", dir=base))
    try: yield target
    finally: shutil.rmtree(target)

def fixture(root, hook=None, *, grant_transform=None, defer_verify=False):
    factory, work, plan, grant, log = factory_fixture(root)
    branch = WorkspaceManager(work).branch_name(86, plan.identity.task_id, 1, plan.base_sha)
    git(work, "branch", "-m", branch)
    hooks = work/".git"/"hooks"
    if hook is not None:
        (hooks/"pre-commit").write_text("#!/bin/sh\nset -eu\n"+hook+"\n"); (hooks/"pre-commit").chmod(0o700)
    manifest = () if hook is None else (("pre-commit", hashlib.sha256((hooks/"pre-commit").read_bytes()).hexdigest()),)
    executable = "/usr/bin/git"
    environment = replace(factory.environment,
        system_files=(*factory.environment.system_files, (executable, hashlib.sha256(Path(executable).read_bytes()).hexdigest())),
        executables=(*factory.environment.executables, executable))
    policy = LocalCommitPolicy("repo-policy-1", environment,
        hashlib.sha256((work/".git"/"config").read_bytes()).hexdigest(), str(hooks), manifest)
    if grant_transform is not None:
        grant = grant_transform(grant)
    plan = replace(plan, grant_sha256=grant.hash, environment_sha256=environment.hash, hygiene_sha256=policy.hash)
    factory.environment = environment; factory.approve = lambda **kwargs: plan
    cycle = factory.prepare(identity=plan.identity, workspace=work, grant=grant, spec_sha256=plan.spec_sha256)
    (work/"result.py").write_text("def approved():\n    return 3\n\ndef foreign():\n    return 2\n")
    if not defer_verify:
        factory.verify(plan.identity)
    completion = {"identity": {"id": plan.identity.task_id, "run_token": plan.identity.run_token,
        "attempt": 1, "idempotency_key": "original", "fencing_token": plan.identity.fencing_token},
        "base_sha": plan.base_sha, "spec_hash": plan.spec_sha256, "policy_hash": "f"*64}
    draft = ArtifactRef(plan.identity.task_id, 1, plan.base_sha, plan.base_sha, "", (), branch)
    info = work.stat()
    committer = HostLocalCommitter(policy, root/"host"/"commits", draft,
                                  completion_plan=completion, workspace_identity=f"{info.st_dev}:{info.st_ino}")
    return committer, cycle, work, log

def test_actual_local_commit_is_same_tested_content_and_never_repeated(boundary_workspace):
    committer, cycle, work, log = fixture(boundary_workspace)
    assert WorkPlan.from_json(cycle.plan.to_json()).hash == cycle.plan.hash
    artifact = committer(cycle)
    assert artifact.changed_files == ("result.py",) and cycle.phase is WorkPhase.HANDOFF
    assert git(work, "status", "--porcelain") == ""
    message = git(work, "log", "-1", "--format=%B")
    assert "Herdr-Verification-Binding: " in message
    restored = WorkCycle(cycle.plan, work, log)
    before = log._path.read_bytes()
    assert committer(restored) == artifact
    shutil.rmtree(work)
    assert committer(restored) == artifact and log._path.read_bytes() == before

def test_hook_changes_invalidate_pass_without_publishing_or_touching_foreign_work(boundary_workspace):
    committer, cycle, work, log = fixture(boundary_workspace, "printf 'hook changed content' >> foreign.txt")
    with pytest.raises(ValueError, match="invalidated"): committer(cycle)
    assert cycle.phase is WorkPhase.VERIFY and cycle.verified_tree is None
    assert (work/"foreign.txt").read_text() == "keep"
    assert git(work, "rev-parse", "HEAD") == cycle.plan.base_sha
    restored = WorkCycle(cycle.plan, work, log)
    assert restored.phase is WorkPhase.VERIFY and not restored.implementation_allowed()

def test_hook_cannot_disable_other_hooks_or_read_host_home(boundary_workspace):
    committer, cycle, work, log = fixture(boundary_workspace,
        "test ! -e /home/agentops/.hermes\ngit config --local core.hooksPath /dev/null")
    with pytest.raises(WorkContractError, match="hook failed"): committer(cycle)
    assert git(work, "rev-parse", "HEAD") == cycle.plan.base_sha
    assert (work/"foreign.txt").read_text() == "keep"

def test_restart_after_ref_commit_reuses_result_without_running_hooks_again(boundary_workspace, monkeypatch):
    committer, cycle, work, log = fixture(boundary_workspace)
    import herdr.work_hygiene as module
    original = module.publish_file
    def interrupted(parent, name, raw, **kwargs):
        if name == "index": raise OSError("simulated crash after exact ref publication")
        return original(parent, name, raw, **kwargs)
    monkeypatch.setattr(module, "publish_file", interrupted)
    with pytest.raises(OSError): committer(cycle)
    head = git(work, "rev-parse", "HEAD")
    assert head != cycle.plan.base_sha
    monkeypatch.setattr(module, "publish_file", original)
    restored = WorkCycle(cycle.plan, work, log)
    artifact = committer(restored)
    assert artifact.commit_sha == head and git(work, "status", "--porcelain") == ""
    assert len([e for e in log.replay() if e["event"] == "work_local_commit_requested"]) == 1

def test_foreign_staging_and_changed_hook_policy_stop_before_local_effect(boundary_workspace):
    committer, cycle, work, log = fixture(boundary_workspace)
    (work/".git"/"config").write_text((work/".git"/"config").read_text()+"\n[commit]\ncleanup = strip\n")
    with pytest.raises(WorkContractError, match="policy changed"): committer(cycle)
    assert not list(committer.storage.iterdir())
    assert git(work, "rev-parse", "HEAD") == cycle.plan.base_sha

def test_real_hook_process_limit_is_enforced_by_kernel(boundary_workspace):
    hook = """/usr/bin/python3 - <<'HOOK'
import errno,os
reader,writer=os.pipe()
children=[]
try:
    for _ in range(16):
        try:pid=os.fork()
        except OSError as exc:
            assert exc.errno==errno.EAGAIN
            break
        if pid==0:
            os.close(writer)
            os.read(reader,1)
            os._exit(0)
        children.append(pid)
    assert len(children)<8, "kernel process limit missing"
finally:
    os.close(writer);os.close(reader)
    for pid in children:os.waitpid(pid,0)
HOOK"""
    committer,cycle,work,log=fixture(boundary_workspace,hook)
    artifact=committer(cycle)
    assert cycle.phase is WorkPhase.HANDOFF and artifact.changed_files==("result.py",)
    assert git(work,"status","--porcelain")==""


def test_foreign_staged_content_is_preserved_and_prevents_hygiene(boundary_workspace):
    committer,cycle,work,log=fixture(boundary_workspace)
    (work/"foreign.txt").write_text("foreign staged change")
    git(work,"add","--","foreign.txt")
    before=git(work,"diff","--cached")
    with pytest.raises(WorkContractError,match="foreign staged|approved work scope"):committer(cycle)
    assert git(work,"diff","--cached")==before
    assert not list(committer.storage.iterdir())
