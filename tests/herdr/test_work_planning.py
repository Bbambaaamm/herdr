"""Planning records on real Git and durable phase replay; no model dispatch."""
from copy import deepcopy
from dataclasses import replace
import hashlib

import pytest

from herdr.evidence import digest
from herdr.work_cycle import WorkCycle, WorkContractError, WorkPhase, WorkPlan, ValidationCheck
from herdr.work_planning import DiscoveryRecord, PlanArtifact
from tests.herdr.test_work_cycle import setup, runner, edit, trusted_git


def artifact(plan, root):
    return {
        "version": 1, "identity": plan.identity.to_json(), "spec_sha256": plan.spec_sha256,
        "base_sha": plan.base_sha,
        "discovery": {"version": 1, "identity": plan.identity.to_json(), "base_sha": plan.base_sha,
            "inspected_files": {"result.py": hashlib.sha256((root/"result.py").read_bytes()).hexdigest()},
            "symbols": {"result.py": ["approved", "foreign"]},
            "facts": ["The inspected Python file defines approved and foreign."],
            "evidence_refs": ["git-base:" + plan.base_sha], "unknowns": ["uninspected paths"],
            "expansion_reason": None},
        "goal": "Repair the requested behavior", "allowed_files": ["result.py"],
        "tools": ["read_file", "write_file", "herdr_submit_result"], "permissions": ["repo:read", "repo:write"],
        "constraints": ["Preserve foreign work"], "assumptions": [], "uncertainties": [],
        "acceptance": list(plan.criteria),
        "verification": {"dimensions": [{"id": "correctness", "hard": True, "check_ids": ["tests"]}],
            "prebuild_review_required": False, "accepted_review_ref": None},
        "expected_artifact": "Committed ArtifactRef plus accepted EvidenceBundle",
        "stop_condition": "Stop BUILD after hard acceptance passes",
        "team": {"topology": "SINGLE", "nodes": [{"id": "worker", "role_ref": None,
            "write_files": ["result.py"], "decision_scope": ["requested behavior"],
            "tools": ["read_file", "write_file", "herdr_submit_result"], "permissions": ["repo:read", "repo:write"]}],
            "edges": [], "integration_owner": "worker", "concurrency": 1,
            "budget_reference": plan.budget_reference},
        "runbook": None, "orientation": None, "prompt_plan": None,
        "clarification": {"status": "resolved", "reason": "Acceptance is explicit", "material": False},
        "decomposition": None,
    }


def planned(tmp_path):
    _, root, plan, log = setup(tmp_path)
    plan = replace(plan, planning=artifact(plan, root))
    return WorkCycle(plan, root, log, git=trusted_git(root)), root, plan, log


def test_planning_is_immutable_and_preserves_legacy_work_plan_hash(tmp_path):
    _, root, legacy, _ = setup(tmp_path)
    raw = artifact(legacy, root)
    immutable = PlanArtifact(raw)
    before = immutable.hash
    raw["goal"] = "Unapproved change"
    exported = immutable.to_json(); exported["goal"] = "Another unapproved change"
    assert immutable.hash == before
    modern = replace(legacy, planning=immutable)
    assert modern.to_json()["version"] == 2
    assert WorkPlan.from_json(modern.to_json()).hash == modern.hash
    assert legacy.to_json()["version"] == 1 and "planning" not in legacy.to_json()
    assert WorkPlan.from_json(legacy.to_json()).hash == legacy.hash


def test_discovery_and_auto_plan_gate_precede_baseline_and_first_work(tmp_path):
    cycle, root, plan, log = planned(tmp_path)
    assert not cycle.implementation_allowed()
    def check(*args):
        assert [x["event"] for x in log.replay()] == ["work_plan", "work_discovery", "work_plan_gate"]
        assert cycle.phase is WorkPhase.PLAN_GATE and not cycle.implementation_allowed()
        return runner(*args)
    cycle.start(check)
    assert cycle.phase is WorkPhase.WORK
    edit(root); cycle.verify(runner)
    assert cycle.phase is WorkPhase.HYGIENE and not cycle.implementation_allowed()
    resumed = WorkCycle(plan, root, log, git=trusted_git(root))
    assert resumed.phase is WorkPhase.HYGIENE and not resumed.implementation_allowed()


@pytest.mark.parametrize("last_event", ["work_discovery", "work_plan_gate"])
def test_restart_cannot_skip_or_duplicate_discovery_plan_gate(tmp_path, last_event):
    cycle, root, plan, log = planned(tmp_path)
    cycle._record("plan", plan=plan.to_json())
    cycle._record("discovery", discovery=plan.planning.to_json()["discovery"])
    if last_event == "work_plan_gate":
        cycle._record("plan_gate", planning_sha256=plan.planning.hash, grant_sha256=plan.grant_sha256,
                      budget_reference=plan.budget_reference, verdict="auto_admitted")
    resumed = WorkCycle(plan, root, log, git=trusted_git(root))
    assert not resumed.implementation_allowed()
    resumed.start(runner)
    events = [x["event"] for x in log.replay()]
    assert events.count("work_discovery") == events.count("work_plan_gate") == events.count("work_plan") == 1
    assert resumed.phase is WorkPhase.WORK


def test_baseline_without_required_plan_gate_is_rejected_on_replay(tmp_path):
    _, root, plan, log = planned(tmp_path)
    log.append({"event": "work_baseline", "work_cycle": plan.identity.to_json(), "plan_sha256": plan.hash,
                "tree": {}, "checks": [], "omission": None}); log.flush()
    with pytest.raises(WorkContractError, match="baseline replay"):
        WorkCycle(plan, root, log, git=trusted_git(root))


def test_changed_plan_or_prompt_invalidates_historical_work(tmp_path):
    cycle, root, plan, log = planned(tmp_path); cycle.start(runner)
    raw = plan.planning.to_json(); raw["goal"] = "Changed objective"
    changed = replace(plan, planning=raw)
    with pytest.raises(WorkContractError, match="changed during restart"):
        WorkCycle(changed, root, log, git=trusted_git(root))
    raw = plan.planning.to_json()
    raw["prompt_plan"] = {"version": "1", "sha256": "1"*64, "spec_sha256": "2"*64,
                           "acceptance_sha256": digest(list(plan.criteria))}
    with pytest.raises(WorkContractError, match="stale prompt"):
        PlanArtifact(raw)


@pytest.mark.parametrize("fault", ["identity", "base", "scope", "budget", "checks", "hard-coverage"])
def test_planning_cannot_change_frozen_work_binding(tmp_path, fault):
    _, root, plan, _ = setup(tmp_path); raw = artifact(plan, root)
    if fault == "identity": raw["identity"]["run_token"] = raw["discovery"]["identity"]["run_token"] = "foreign"
    if fault == "base": raw["base_sha"] = raw["discovery"]["base_sha"] = "1"*40
    if fault == "scope": raw["allowed_files"].append("foreign.txt")
    if fault == "budget": raw["team"]["budget_reference"] = "1"*64
    if fault == "checks": raw["verification"]["dimensions"][0]["check_ids"] = ["other"]
    if fault == "hard-coverage":
        raw["verification"]["dimensions"] = [{"id": "hard", "hard": True, "check_ids": ["missing"]},
                                            {"id": "soft", "hard": False, "check_ids": ["tests"]}]
    with pytest.raises(WorkContractError):
        replace(plan, planning=raw)


@pytest.mark.parametrize("fault", ["material-assumption", "info-required", "missing-review", "executable-runbook",
                                  "orientation-write", "uninspected-fact", "role-fanout", "depth", "unknown-key"])
def test_plan_gate_denies_material_or_authority_changes(tmp_path, fault):
    _, root, plan, _ = setup(tmp_path); raw = artifact(plan, root)
    if fault == "material-assumption":
        raw["assumptions"] = ["Hidden intent"]; raw["clarification"].update(status="bounded_assumption", material=True)
    if fault == "info-required": raw["clarification"].update(status="info_required", material=True)
    if fault == "missing-review": raw["verification"]["prebuild_review_required"] = True
    if fault == "executable-runbook":
        raw["runbook"] = {"profile": "release", "version": "1", "sha256": "1"*64, "advisory": False}
    if fault in {"orientation-write", "uninspected-fact"}:
        raw["orientation"] = {"inspected_files": ["foreign.txt"] if fault == "uninspected-fact" else ["result.py"],
            "facts": [], "uninspected_areas": ["rest"], "unknowns": ["rest"], "read_only": fault != "orientation-write"}
    if fault == "role-fanout": raw["team"]["nodes"].append({**raw["team"]["nodes"][0], "id": "extra"})
    if fault == "depth":
        nested = []
        for _ in range(18): nested = [nested]
        raw["assumptions"] = nested
    if fault == "unknown-key": raw["model_approved"] = True
    with pytest.raises(WorkContractError):
        PlanArtifact(raw)


@pytest.mark.parametrize("fault", ["overlap", "cycle", "budget-reset", "no-new-evidence"])
def test_team_and_decomposition_preserve_ownership_and_budget(tmp_path, fault):
    _, root, plan, _ = setup(tmp_path); raw = artifact(plan, root)
    if fault in {"overlap", "cycle"}:
        second = deepcopy(raw["team"]["nodes"][0]); second["id"] = "reviewer"
        raw["team"].update(topology="PARALLEL", concurrency=2, nodes=[raw["team"]["nodes"][0], second])
        if fault == "cycle":
            second["write_files"] = []
            raw["team"]["edges"] = [{"from": a, "to": b, "handoff_schema": "herdr-handoff-1", "gate_refs": []}
                                     for a, b in [("worker", "reviewer"), ("reviewer", "worker")]]
    else:
        raw["decomposition"] = {"reason": "New failure evidence", "new_evidence_ref": "" if fault == "no-new-evidence" else "1"*64,
                                "spec_sha256": plan.spec_sha256, "budget_reference": "2"*64}
    with pytest.raises(WorkContractError):
        PlanArtifact(raw)


def test_soft_improvement_never_overrides_failed_hard_minimum(tmp_path):
    _, root, legacy, log = setup(tmp_path)
    checks = (*legacy.checks, ValidationCheck("latency", ("/usr/bin/python3", "result.py"), legacy.criteria))
    raw = artifact(legacy, root)
    raw["verification"]["dimensions"].append({"id": "performance", "hard": False, "check_ids": ["latency"]})
    plan = replace(legacy, checks=checks, planning=raw)
    cycle = WorkCycle(plan, root, log, git=trusted_git(root)); cycle.start(runner); edit(root)
    cycle.verify(lambda check, *args: replace(runner(check, *args), exit_code=1 if check.id == "latency" else 0))
    assert cycle.phase is WorkPhase.HYGIENE
    other_log = type(log)(log._path.parent/"other.jsonl")
    failed = WorkCycle(plan, root, other_log, git=trusted_git(root))
    # Preserve clean baseline for another independent attempt fixture.
    from tests.herdr.test_work_cycle import git
    git(root, "restore", "result.py"); failed.start(runner); edit(root)
    with pytest.raises(WorkContractError, match="hard check failed"):
        failed.verify(lambda check, *args: replace(runner(check, *args), exit_code=1 if check.id == "tests" else 0))
    assert not failed.implementation_allowed()
