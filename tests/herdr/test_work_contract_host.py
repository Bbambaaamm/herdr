"""Actual host contract/namespace integration plus the physical model guard."""
from dataclasses import replace
from pathlib import Path
import hashlib
import shutil

import pytest
from herdr.work_contract_host import HostWorkContractFactory, WorkInvocationGuard
from herdr.work_cycle import WorkContractError, WorkPhase
from herdr.security import PolicyDenied,ProviderRequest
from herdr.capability import DataClass,Egress,Retention,Training
from tests.herdr.test_security import grant
from test_work_cycle import setup,seal,trusted_git
from test_check_runner import environment

def factory_fixture(tmp_path):
    _,root,template,log=setup(tmp_path)
    profile=environment()
    planned=replace(grant(root),identity=template.identity)
    command=("/usr/bin/python3","-c",
        "import runpy,sys; value=runpy.run_path('result.py')['approved'](); "
        "print('fixed' if value==3 else 'baseline bug'); sys.exit(0 if value==3 else 1)")
    check=replace(template.checks[0],command=command,expected_baseline_failure=True,
                  expected_baseline_output_sha256=hashlib.sha256(b"baseline bug\n").hexdigest())
    plan=replace(template,grant_sha256=planned.hash,environment_sha256=profile.hash,checks=(check,))
    factory=HostWorkContractFactory(approve=lambda **kwargs:plan,environment=profile,
        storage=tmp_path/"host"/"checks",audit_log=log,git=trusted_git(root))
    return factory,root,plan,planned,log

def test_actual_baseline_check_pass_model_stop_commit_and_crash_handoff(tmp_path):
    factory,root,plan,planned,log=factory_fixture(tmp_path)
    cycle=factory.prepare(identity=planned.identity,workspace=root,grant=planned,spec_sha256=plan.spec_sha256)
    guard=WorkInvocationGuard(planned,work_authority=factory.require_model_work)
    request=ProviderRequest("provider-a","eu-central",DataClass.INTERNAL,Egress.REGION_BOUND,Retention.LIMITED,Training.EXCLUDED)
    guard.authorize_provider(request)
    (root/"result.py").write_text("def approved():\n    return 3\n\ndef foreign():\n    return 2\n")
    factory.verify(plan.identity)
    assert cycle.phase is WorkPhase.HYGIENE
    with pytest.raises(PolicyDenied,match="work_phase"):
        guard.authorize_provider(request)
    with pytest.raises(PolicyDenied,match="work_phase"):
        guard.authorize_tool_call("read_file",{"path":str(root/"result.py")})
    artifact=seal(cycle,root,tmp_path)
    factory.before_completion(plan.identity,{"artifact_workspace":str(root),"artifact":artifact.to_json()})
    cycle.handed_off("f"*64)
    shutil.rmtree(root)
    restored=HostWorkContractFactory(approve=lambda **kw:pytest.fail("accepted work must not be replanned"),
        environment=factory.environment,storage=factory.storage,audit_log=log)
    recovered=restored.recover(identity=plan.identity,workspace=root,spec_sha256=plan.spec_sha256,
        grant_sha256=planned.hash,plan_sha256=plan.hash)
    recovered.committed(artifact)
    recovered.handed_off("f"*64)
    assert recovered.phase is WorkPhase.FINISHED
    with pytest.raises(PolicyDenied,match="work_phase"):
        restored.require_model_work(plan.identity,planned.hash)
    assert list(factory.storage.iterdir())==[]

@pytest.mark.parametrize("fault",["identity","grant","spec","environment"])
def test_host_authorization_binding_cannot_be_changed_by_worker(tmp_path,fault):
    factory,root,plan,planned,log=factory_fixture(tmp_path)
    bad=replace(plan,**{"identity":replace(plan.identity,run_token="other-run")} if fault=="identity" else
                {"grant_sha256":"f"*64} if fault=="grant" else
                {"spec_sha256":"f"*64} if fault=="spec" else {"environment_sha256":"f"*64})
    factory.approve=lambda **kw:bad
    with pytest.raises(WorkContractError,match="binding"):
        factory.prepare(identity=planned.identity,workspace=root,grant=planned,spec_sha256=plan.spec_sha256)
    assert log.replay()==[]

def test_worker_writable_work_ledger_is_rejected_before_baseline(tmp_path):
    factory,root,plan,planned,log=factory_fixture(tmp_path)
    from herdr.scheduler import AuditLog
    factory.audit_log=AuditLog(root/"audit.jsonl")
    with pytest.raises(WorkContractError,match="worker writable"):
        # The actual host grant must enumerate the physical writable root.
        planned=replace(planned,runtime_assurance=replace(planned.runtime_assurance,writable_roots=(str(root),)))
        factory.prepare(identity=planned.identity,workspace=root,grant=planned,spec_sha256=plan.spec_sha256)
