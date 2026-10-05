"""Host-configured admission, actual checks, and original-proof cold recovery."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import shutil
import sys
import json
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"agent-stack"/"bin"))
from agent_completion_evidence import spec_digest
from herdr import work_configuration as config
from herdr.work_cycle import IntentInfoRequired, WorkContractError, WorkPhase
from herdr.work_planning import PlanArtifact, bounded
from tests.herdr.test_host_configuration import approved_config
from tests.herdr.test_work_contract_host import factory_fixture
from tests.herdr.test_work_planning import artifact
from tests.herdr.test_work_cycle import seal

def configured(tmp_path, monkeypatch, *, budget=None):
    raw, unused, unused_grant = approved_config(tmp_path, monkeypatch)
    factory, root, old_plan, grant, old_log = factory_fixture(tmp_path/"actual")
    task = {"id": grant.identity.task_id, "run_token": grant.identity.run_token,
            "fencing_token": grant.identity.fencing_token, "idempotency_key": "original-key",
            "attempt_id": 1, "repo": "Bbambaaamm/herdr", "kind": "coding",
            "prompt": "Repair the approved function only", "workspace": str(root),
            "work_contract_version": 1, "completion_plan": {"base_sha": old_plan.base_sha}}
    if budget is not None:task["work_budget_version"]=1
    plan = replace(old_plan, spec_sha256=spec_digest(task))
    if budget is not None:
        from herdr.work_budget_configuration import parse_allocation
        plan=replace(plan,budget_reference=parse_allocation(budget["allocation"]).hash)
    planning = artifact(plan, root)
    planning["tools"] = ["read_file"]; planning["permissions"] = ["repo:read"]
    planning["team"]["nodes"][0].update(tools=["read_file"], permissions=["repo:read"])
    for key in ("version", "identity", "spec_sha256", "base_sha", "discovery"): planning.pop(key)
    definition = json.loads(json.dumps(plan.to_json()))
    for key in ("version", "identity", "spec_sha256", "grant_sha256", "environment_sha256"): definition.pop(key)
    definition.update(discovery_files=["result.py"], planning=planning)
    if budget is not None:definition["budget"]=deepcopy(budget)
    raw["templates"] = {grant.identity.consumer: grant.to_json()}
    raw["work_contracts"] = {"version": 1, "environment": asdict(factory.environment),
                            "plans": {spec_digest(task): definition}, "review_records": {}}
    monkeypatch.setattr(config, "_read_configuration", lambda path: deepcopy(raw))
    work = config.build_root_work_factory(Path(raw["task_store_root"]), task, git=factory.git)
    cycle = work.prepare(identity=grant.identity, workspace=root, grant=grant, spec_sha256=spec_digest(task))
    return raw, task, work, cycle, grant, root

def test_actual_config_discovery_baseline_and_original_finished_admission_after_cleanup(tmp_path, monkeypatch):
    raw, task, work, cycle, grant, root = configured(tmp_path, monkeypatch)
    assert cycle.phase is WorkPhase.WORK
    assert "approved" in cycle.plan.planning.to_json()["discovery"]["symbols"]["result.py"]
    (root/"result.py").write_text("def approved():\n    return 3\n\ndef foreign():\n    return 2\n")
    work.verify(grant.identity)
    reference = seal(cycle, root, tmp_path)
    work.before_completion(grant.identity, {"artifact_workspace": str(root), "artifact": reference.to_json()})
    cycle.handed_off("f"*64)
    shutil.rmtree(root); raw.pop("work_contracts")
    recovered = config.build_root_work_factory(Path(raw["task_store_root"]), task, recovery=True)
    restored = recovered.recover(identity=grant.identity, workspace=root, spec_sha256=spec_digest(task),
        grant_sha256=grant.hash, plan_sha256=cycle.plan.hash)
    restored.committed(reference); restored.handed_off("f"*64)
    assert restored.phase is WorkPhase.FINISHED
    with pytest.raises(WorkContractError, match="cannot authorize"):
        recovered.approve(identity=grant.identity, workspace=root, grant=grant, spec_sha256=spec_digest(task))
    for path in (Path(raw["storage"])/"work-contracts").rglob("*"):
        if path.is_dir(): assert path.stat().st_mode & 0o077 == 0

@pytest.mark.parametrize("fault", ["spec", "fence", "missing-proof", "ancestor-mode"])
def test_cold_recovery_cannot_change_original_admission(tmp_path, monkeypatch, fault):
    raw, task, work, cycle, grant, root = configured(tmp_path, monkeypatch)
    if fault == "spec": task["prompt"] = "Different objective"
    if fault == "fence": task["fencing_token"] += 1
    if fault == "missing-proof": shutil.rmtree(work.storage.parent/"admission")
    if fault == "ancestor-mode": (Path(raw["storage"])/"work-contracts").chmod(0o755)
    with pytest.raises((WorkContractError, OSError)):
        config.build_root_work_factory(Path(raw["task_store_root"]), task, recovery=True)

def test_material_missing_intent_has_stable_typed_code_before_work(tmp_path):
    from tests.herdr.test_work_cycle import setup
    _, root, plan, log = setup(tmp_path); raw = artifact(plan, root)
    raw["clarification"].update(status="info_required", material=True)
    with pytest.raises(IntentInfoRequired) as raised: PlanArtifact(raw)
    assert raised.value.code == "info_required" and log.replay() == []

def test_planning_integer_is_bounded_before_serialization():
    with pytest.raises(WorkContractError, match="integer"): bounded({"value": 10**10000})
