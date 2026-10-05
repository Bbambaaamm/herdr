"""Work contracts on actual Git/artifacts and the existing append-only audit."""
from dataclasses import asdict, replace
from pathlib import Path
import hashlib
import json
import subprocess

import pytest

from herdr.evidence import canonical, digest
from herdr.scheduler import AuditLog
from herdr.security import InvocationIdentity
from herdr.work_cycle import (CheckResult, FileScope, ValidationCheck, WorkContractError,
                             WorkCycle, WorkMode, WorkPhase, WorkPlan, tree_snapshot)
from herdr.workspace import ArtifactRef, WorkspaceManager, _real_git

def git(root, *args):
    return subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,check=True).stdout.strip()

def trusted_git(root):
    command=_real_git(root)
    command.raw=lambda args: subprocess.run(["git","-C",str(root),*args],capture_output=True,check=True).stdout
    return command

def setup(tmp_path, **overrides):
    root = tmp_path/"work"/"task"
    root.mkdir(parents=True)
    git(root,"init","-q")
    git(root,"config","user.name","Contract test")
    git(root,"config","user.email","test@example.invalid")
    (root/"result.py").write_text("def approved():\n    return 1\n\ndef foreign():\n    return 2\n")
    (root/"foreign.txt").write_text("keep")
    git(root,"add",".")
    git(root,"commit","-qm","baseline")
    base = git(root,"rev-parse","HEAD")
    identity = InvocationIdentity("github:org/repo","worker","parent","parent-task","task","run",1)
    plan = WorkPlan(identity,"spec-1","a"*64,"policy-1",base,(FileScope("result.py"),),
        ("behavior",),(ValidationCheck("tests",("/usr/bin/python3","result.py"),("behavior",)),),
        "b"*64,"c"*64,"d"*64,**overrides)
    log = AuditLog(tmp_path/"host"/"audit.jsonl")
    cycle = WorkCycle(plan,root,log,git=trusted_git(root))
    return cycle,root,plan,log

def runner(check,root,plan,tree):
    return CheckResult(check.id,plan.hash,plan.environment_sha256,tree,0,"e"*64,False,1,"f"*64)

def edit(root):
    (root/"result.py").write_text("def approved():\n    return 3\n\ndef foreign():\n    return 2\n")

def seal(cycle,root,tmp_path):
    git(root,"add","--","result.py")
    git(root,"commit","-qm","bounded repair")
    manager=WorkspaceManager(root,git=trusted_git(root),worktrees_dir=root.parent,artifacts_dir=tmp_path/"host"/"artifacts")
    draft=ArtifactRef(cycle.plan.identity.task_id,1,cycle.plan.base_sha,cycle.plan.base_sha,"",(),"task")
    return manager.seal(draft,root)

def test_baseline_precedes_edits_and_every_criterion_has_exact_proof(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    assert not cycle.implementation_allowed()
    calls=[]
    def baseline(*args):
        calls.append((root/"result.py").read_text())
        return runner(*args)
    cycle.start(baseline)
    assert calls==["def approved():\n    return 1\n\ndef foreign():\n    return 2\n"]
    assert cycle.phase is WorkPhase.WORK
    edit(root)
    cycle.verify(runner)
    assert cycle.phase is WorkPhase.HYGIENE and not cycle.implementation_allowed()
    with pytest.raises(WorkContractError,match="already ended"):
        cycle.verify(runner)
    assert [x["event"] for x in log.replay()]==["work_plan","work_baseline","work_check","work_pass"]

def test_unrelated_baseline_failure_does_not_authorize_repair(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    def failure(*args):
        return replace(runner(*args),exit_code=1)
    with pytest.raises(WorkContractError,match="unanticipated"):
        cycle.start(failure)
    assert not cycle.implementation_allowed() and (root/"foreign.txt").read_text()=="keep"

def test_expected_failure_requires_predeclared_fingerprint(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    check=replace(plan.checks[0],expected_baseline_failure=True,expected_baseline_output_sha256="e"*64)
    plan=replace(plan,checks=(check,))
    cycle=WorkCycle(plan,root,log,git=trusted_git(root))
    def failure(*args):
        return replace(runner(*args),exit_code=1)
    cycle.start(failure)
    assert cycle.implementation_allowed()
    with pytest.raises(WorkContractError,match="fingerprint"):
        replace(check,expected_baseline_output_sha256=None)

def test_wrong_expected_failure_is_not_repair_permission(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    check=replace(plan.checks[0],expected_baseline_failure=True,expected_baseline_output_sha256="f"*64)
    cycle=WorkCycle(replace(plan,checks=(check,)),root,log,git=trusted_git(root))
    with pytest.raises(WorkContractError,match="unanticipated"):
        cycle.start(lambda *args: replace(runner(*args),exit_code=1))
    assert not cycle.implementation_allowed()

def test_explicit_baseline_omission_is_preserved_on_restart(tmp_path):
    cycle,root,plan,log=setup(tmp_path,baseline_omission_reason="host-approved external fixture unavailable",baseline_policy="host-approved-omission")
    cycle.start(lambda *a: pytest.fail("omitted baseline must not run"))
    resumed=WorkCycle(plan,root,log,git=trusted_git(root))
    assert resumed.phase is WorkPhase.WORK
    assert log.replay()[-1]["omission"]==plan.baseline_omission_reason

def test_dirty_foreign_files_are_preserved_and_block_initial_work(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    (root/"foreign.txt").write_text("foreign uncommitted work")
    with pytest.raises(WorkContractError,match="clean base"):
        cycle.start(runner)
    assert (root/"foreign.txt").read_text()=="foreign uncommitted work" and log.replay()==[]

def test_unintegrated_prerequisite_blocks_even_if_artifact_exists(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    git(root,"checkout","-qb","prerequisite")
    (root/"other.txt").write_text("separate prerequisite")
    git(root,"add",".")
    git(root,"commit","-qm","unintegrated")
    prerequisite=git(root,"rev-parse","HEAD")
    git(root,"checkout","-q","master")
    cycle=WorkCycle(replace(plan,prerequisite_commits=(prerequisite,)),root,log,git=trusted_git(root))
    with pytest.raises(WorkContractError,match="not integrated"):
        cycle.start(runner)
    assert not cycle.implementation_allowed()

def test_integrated_exact_prerequisite_allows_work(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle=WorkCycle(replace(plan,prerequisite_commits=(plan.base_sha,)),root,log,git=trusted_git(root))
    cycle.start(runner)
    assert cycle.implementation_allowed()

def test_scope_escape_rejects_without_changing_foreign_work(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    (root/"foreign.txt").write_text("out of scope")
    with pytest.raises(WorkContractError,match="scope"):
        cycle.verify(runner)
    assert (root/"foreign.txt").read_text()=="out of scope"

def test_symbol_scope_rejects_change_to_other_function(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle=WorkCycle(replace(plan,files=(FileScope("result.py",symbols=("approved",)),)),root,log,git=trusted_git(root))
    cycle.start(runner)
    edit(root)
    cycle.verify(runner)
    assert cycle.phase is WorkPhase.HYGIENE
    # Separate cycle to test unapproved symbol changes before PASS.
    other=tmp_path/"other"
    other.mkdir()
    cycle,root,plan,log=setup(other)
    cycle=WorkCycle(replace(plan,files=(FileScope("result.py",symbols=("approved",)),)),root,log,git=trusted_git(root))
    cycle.start(runner)
    (root/"result.py").write_text("def approved():\n    return 1\n\ndef foreign():\n    return 9\n")
    with pytest.raises(WorkContractError,match="symbol"):
        cycle.verify(runner)

@pytest.mark.parametrize("field,value",[("plan_sha256","f"*64),("environment_sha256","f"*64),("tree_sha256","f"*64)])
def test_check_receipt_from_wrong_inputs_is_rejected(tmp_path,field,value):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    edit(root)
    with pytest.raises(WorkContractError,match="mismatch"):
        cycle.verify(lambda *args: replace(runner(*args),**{field:value}))
    assert cycle.phase is WorkPhase.WORK

def test_check_mutation_invalidates_before_pass(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    edit(root)
    def mutate(*args):
        (root/"result.py").write_text("tampered")
        return runner(*args)
    with pytest.raises(WorkContractError,match="tested inputs"):
        cycle.verify(mutate)
    assert not any(x["event"]=="work_pass" for x in log.replay())

def test_commit_hook_content_change_invalidates_tests(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    edit(root)
    cycle.verify(runner)
    hook=root/".git"/"hooks"/"pre-commit"
    hook.write_text("#!/bin/sh\nprintf '\\n# hook rewrite\\n' >> result.py\ngit add -- result.py\n")
    hook.chmod(0o755)
    artifact=seal(cycle,root,tmp_path)
    with pytest.raises(WorkContractError,match="hook"):
        cycle.committed(artifact)
    assert cycle.phase is WorkPhase.VERIFY
    assert "hook rewrite" in (root/"result.py").read_text()
    assert not cycle.implementation_allowed()
    cycle.verify(runner)
    cycle.committed(artifact)
    assert cycle.phase is WorkPhase.HANDOFF

def test_restart_after_commit_replays_handoff_without_new_commit_or_checks(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    edit(root)
    cycle.verify(runner)
    artifact=seal(cycle,root,tmp_path)
    cycle.committed(artifact)
    commit=git(root,"rev-parse","HEAD")
    resumed=WorkCycle(plan,root,AuditLog(log._path),git=trusted_git(root))
    assert resumed.phase is WorkPhase.HANDOFF
    resumed.committed(artifact)
    resumed.handed_off("f"*64)
    final=WorkCycle(plan,root,log,git=trusted_git(root))
    final.committed(artifact)
    final.handed_off("f"*64)
    assert final.phase is WorkPhase.FINISHED
    assert git(root,"rev-parse","HEAD")==commit
    with pytest.raises(WorkContractError,match="differs"):
        final.handed_off("e"*64)

def test_restart_rejects_changed_spec_plan_mode_or_receipt(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    with pytest.raises(WorkContractError,match="plan changed"):
        WorkCycle(replace(plan,spec_sha256="f"*64),root,log,git=trusted_git(root))
    with pytest.raises(WorkContractError,match="experiment"):
        replace(plan,mode=WorkMode.EXPERIMENT)
    with pytest.raises(WorkContractError,match="every criterion"):
        replace(plan,criteria=("other",))
    edit(root)
    cycle.verify(runner)
    events=log.replay()
    events[-2]["check"]["environment_sha256"]="f"*64
    log._path.write_text("".join(json.dumps(x)+"\n" for x in events))
    with pytest.raises(WorkContractError,match="mismatch"):
        WorkCycle(plan,root,log,git=trusted_git(root))

def test_deleted_file_has_same_tested_tree_before_and_after_commit(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    (root/"result.py").unlink()
    before=tree_snapshot(root,git=trusted_git(root))
    cycle.verify(runner)
    artifact=seal(cycle,root,tmp_path)
    assert tree_snapshot(root,git=trusted_git(root))==before
    cycle.committed(artifact)
    assert cycle.phase is WorkPhase.HANDOFF

def test_simple_and_ordered_large_phase_templates_need_no_more_agents(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    assert plan.phases==("work","verify","handoff")
    large=replace(plan,phases=("discovery","architecture","data_model","work","verify","release","handoff"))
    assert large.identity==plan.identity
    with pytest.raises(WorkContractError,match="order"):
        replace(plan,phases=("verify","work","handoff"))

def test_symlink_input_never_reads_external_content(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    external=tmp_path/"credential"
    external.write_text("host secret")
    (root/"result.py").unlink()
    (root/"result.py").symlink_to(external)
    with pytest.raises(OSError):
        tree_snapshot(root,git=trusted_git(root))
    assert external.read_text()=="host secret"


def test_protected_verification_input_cannot_be_weakened_inside_approved_scope(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    check=replace(plan.checks[0],protected_inputs=(("result.py",hashlib.sha256((root/"result.py").read_bytes()).hexdigest()),))
    cycle=WorkCycle(replace(plan,checks=(check,)),root,log,git=trusted_git(root))
    cycle.start(runner)
    edit(root)
    with pytest.raises(WorkContractError,match="independent reviewed replan"):
        cycle.verify(runner)

def test_truncated_check_cannot_become_pass(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    edit(root)
    with pytest.raises(WorkContractError,match="check failed"):
        cycle.verify(lambda *args:replace(runner(*args),truncated=True))
    assert log.replay()[-1]["check"]["truncated"] is True

def test_duplicate_symbols_and_mode_change_cannot_bypass_symbol_scope(tmp_path):
    from herdr.work_cycle import python_symbols
    with pytest.raises(WorkContractError,match="duplicate"):
        python_symbols("def x(): pass\ndef x(): pass\n")
    cycle,root,plan,log=setup(tmp_path)
    cycle=WorkCycle(replace(plan,files=(FileScope("result.py",symbols=("approved",)),)),root,log,git=trusted_git(root))
    cycle.start(runner)
    (root/"result.py").chmod(0o755)
    with pytest.raises(WorkContractError,match="mode"):
        cycle.verify(runner)

def test_rollback_restores_only_host_attested_owned_edit_and_preserves_foreign_file(tmp_path):
    from herdr.work_cycle import OwnedChange
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    original=(root/"result.py").read_bytes()
    edit(root)
    owned=OwnedChange("result.py",hashlib.sha256(original).hexdigest(),
                     hashlib.sha256((root/"result.py").read_bytes()).hexdigest())
    (root/"foreign.txt").write_text("human work since task started")
    seen=[]
    def authority(identity,plan_hash,before,after):
        seen.append((identity,plan_hash))
        return (owned,)
    cycle.rollback_owned(authority)
    assert seen==[(plan.identity,plan.hash)]
    assert (root/"result.py").read_bytes()==original
    assert (root/"foreign.txt").read_text()=="human work since task started"
    assert cycle.phase is WorkPhase.BLOCKED
    assert WorkCycle(plan,root,log,git=trusted_git(root)).phase is WorkPhase.BLOCKED

def test_rollback_refuses_ambiguous_ownership_and_preserves_newer_bytes(tmp_path):
    from herdr.work_cycle import OwnedChange
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    edit(root)
    claimed=OwnedChange("result.py",cycle.baseline["result.py"]["sha256"],"f"*64)
    with pytest.raises(WorkContractError,match="ambiguous"):
        cycle.rollback_owned(lambda *a:(claimed,))
    assert "return 3" in (root/"result.py").read_text()
    with pytest.raises(WorkContractError,match="receipts"):
        cycle.rollback_owned(lambda *a:None)

def test_rollback_never_resets_committed_or_staged_work(tmp_path):
    from herdr.work_cycle import OwnedChange
    cycle,root,plan,log=setup(tmp_path)
    cycle.start(runner)
    edit(root)
    git(root,"add","result.py")
    with pytest.raises(WorkContractError,match="staged"):
        cycle.rollback_owned(lambda *a:pytest.fail("authority must not be called"))
    assert git(root,"diff","--cached","--name-only")=="result.py"

def test_serialized_plan_roundtrip_keeps_mode_and_exact_hash(tmp_path):
    cycle,root,plan,log=setup(tmp_path)
    raw=json.loads(canonical(plan.to_json()))
    assert WorkPlan.from_json(raw)==plan and WorkPlan.from_json(raw).hash==plan.hash
    raw["mode"]="experiment"
    with pytest.raises(WorkContractError,match="experiment"):
        WorkPlan.from_json(raw)
