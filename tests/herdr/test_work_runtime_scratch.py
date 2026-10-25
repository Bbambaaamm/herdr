"""Scratch ports on real directories/Git; no process or isolation PASS is mocked.

Prepare uses an explicit host-approved omitted baseline. Runtime-copy tests stop
before the execution boundary; they do not claim native namespace acceptance.
"""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"agent-stack"/"bin"))
from agent_completion_evidence import spec_digest, store_for
from herdr import work_configuration as config
from herdr.check_runner import CheckEnvironment, HostCheckRunner
from herdr.check_runtime import FrozenCheckRuntime
from herdr.evidence import binding, digest
from herdr.result_submission import ResultSlot, TOOL, ARGUMENTS
from herdr.security import ToolRule, RiskClass
from herdr.work_contract_host import HostWorkContractFactory
from herdr.work_cycle import WorkContractError, WorkPhase
from herdr.work_hygiene import HostLocalCommitter
from herdr.workspace import WorkspaceManager
from tests.herdr.test_host_configuration import approved_config
from tests.herdr.test_security import grant as template_grant
from tests.herdr.test_work_cycle import setup, git, trusted_git, runner, edit
from tests.herdr.test_work_planning import artifact


def private(path):
    path.mkdir(mode=0o700, parents=True)
    return path


def profile(tmp_path, *, hygiene=False):
    tool = tmp_path/"host-tool"
    tool.write_bytes(b"approved component runtime\n")
    tool.chmod(0o700)
    files = [(str(tool), hashlib.sha256(tool.read_bytes()).hexdigest())]
    executables = [str(tool)]
    if hygiene:
        target = Path("/usr/bin/git").resolve(strict=True)
        files.append((str(target), hashlib.sha256(target.read_bytes()).hexdigest()))
        executables.append("/usr/bin/git")
    return CheckEnvironment("scratch-component-1", tuple(files), tuple(executables))


def configured(tmp_path, monkeypatch, *, scratch=True, hygiene=False, prepare=True):
    raw, _, _ = approved_config(tmp_path, monkeypatch)
    _, root, old, _ = setup(tmp_path/"actual",
        baseline_policy="host-approved-omission",
        baseline_omission_reason="Component test stops before native execution")
    environment = profile(tmp_path, hygiene=hygiene)
    granted = replace(template_grant(root), identity=old.identity)
    branch = WorkspaceManager(root).branch_name(86, old.identity.task_id, 1, old.base_sha)
    git(root, "branch", "-m", branch)
    task = {"id":old.identity.task_id, "run_token":old.identity.run_token,
        "fencing_token":old.identity.fencing_token, "attempt_id":1,
        "idempotency_key":"scratch-component", "repo":"org/repo", "kind":"coding",
        "prompt":"Component-only frozen task", "workspace":str(root),
        "work_contract_version":1, "completion_plan":{"base_sha":old.base_sha}}
    plan = replace(old, spec_sha256=spec_digest(task), grant_sha256=granted.hash,
                   environment_sha256=environment.hash)
    planning = artifact(plan, root)
    planning["tools"] = ["read_file"]; planning["permissions"] = ["repo:read"]
    planning["team"]["nodes"][0].update(tools=["read_file"], permissions=["repo:read"])
    for key in ("version", "identity", "spec_sha256", "base_sha", "discovery"):
        planning.pop(key)
    definition = json.loads(json.dumps(plan.to_json()))
    for key in ("version", "identity", "spec_sha256", "grant_sha256", "environment_sha256"):
        definition.pop(key)
    definition.update(discovery_files=["result.py"], planning=planning)
    if hygiene:
        definition["hygiene"] = {"version":"scratch-hygiene-1",
            "config_sha256":hashlib.sha256((root/".git/config").read_bytes()).hexdigest(),
            "hooks_root":str(root/".git/hooks"), "hooks":[],
            "timeout_seconds":60, "output_bytes":65536, "max_processes":8}
    raw["templates"] = {granted.identity.consumer:granted.to_json()}
    raw["work_contracts"] = {"version":1, "environment":asdict(environment),
        "plans":{spec_digest(task):definition}, "review_records":{}}
    if scratch:
        raw["work_contracts"]["runtime_scratch"] = {
            "check_storage":str(private(tmp_path/"scratch-check")),
            "commit_storage":str(private(tmp_path/"scratch-commit"))}
    monkeypatch.setattr(config, "_read_configuration", lambda _:deepcopy(raw))
    # Exercise real disposable Git bytes, without invoking the native Git sandbox.
    monkeypatch.setattr("herdr.evidence.read_only_git", trusted_git)
    monkeypatch.setattr("herdr.work_hygiene.read_only_git", trusted_git)
    factory = config.build_root_work_factory(Path(raw["task_store_root"]), task, git=trusted_git(root))
    cycle = None if not prepare else factory.prepare(identity=granted.identity, workspace=root,
        grant=granted, spec_sha256=spec_digest(task))
    return raw, task, factory, cycle, granted, root


@pytest.mark.parametrize("custom", [False, True])
def test_prepare_and_cold_recover_keep_authority_and_select_check_port(tmp_path, monkeypatch, custom):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch, scratch=custom)
    selected = Path(raw["work_contracts"]["runtime_scratch"]["check_storage"]) if custom else factory.storage
    assert factory.check_storage == selected
    assert cycle.phase is WorkPhase.WORK
    assert factory.cycles[digest(granted.identity.to_json())][1].storage == selected
    audit = factory.audit_log._path.read_bytes()
    recovered = config.build_root_work_factory(Path(raw["task_store_root"]), task, recovery=True, git=trusted_git(root))
    restored = recovered.recover(identity=granted.identity, workspace=root,
        spec_sha256=spec_digest(task), grant_sha256=granted.hash, plan_sha256=cycle.plan.hash)
    assert restored.phase is WorkPhase.WORK
    assert recovered.cycles[digest(granted.identity.to_json())][1].storage == selected
    assert recovered.storage == factory.storage
    assert recovered.result_authority.store.root == factory.result_authority.store.root
    assert recovered.audit_log._path.read_bytes() == audit
    assert factory.storage.parent.is_relative_to(Path(raw["storage"]))


@pytest.mark.parametrize("fault", ["unknown", "missing", "relative", "alias", "mode", "file", "owner", "workspace", "grant"])
def test_host_scratch_validation_is_closed_private_and_separate_from_binding(tmp_path, monkeypatch, fault):
    check = private(tmp_path/"check"); commit = private(tmp_path/"commit")
    workspace = private(tmp_path/"workspace")
    data = {"check_storage":str(check), "commit_storage":str(commit)}
    writable = ()
    if fault == "unknown": data["task_path"] = str(check)
    elif fault == "missing": data.pop("commit_storage")
    elif fault == "relative": data["check_storage"] = "relative"
    elif fault == "alias":
        alias = tmp_path/"alias"; alias.symlink_to(check, target_is_directory=True); data["check_storage"] = str(alias)
    elif fault == "mode": check.chmod(0o750)
    elif fault == "file": check.rmdir(); check.write_bytes(b"not a directory")
    elif fault == "owner": monkeypatch.setattr(config.os, "geteuid", lambda:check.stat().st_uid+1)
    elif fault == "workspace": data["check_storage"] = str(private(workspace/"scratch"))
    elif fault == "grant": writable = (check,)
    with pytest.raises((WorkContractError, OSError)):
        config._runtime_scratch({"work_contracts":{"runtime_scratch":data}}, workspace, writable)


@pytest.mark.parametrize("name", ["check_storage", "commit_storage"])
def test_actual_grant_write_binding_rechecked_before_baseline_or_new_audit(tmp_path, monkeypatch, name):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch)
    before = factory.audit_log._path.read_bytes()
    target = raw["work_contracts"]["runtime_scratch"][name]
    changed = replace(granted, runtime_assurance=replace(granted.runtime_assurance, writable_roots=(target,)))
    with pytest.raises(WorkContractError, match="scratch is worker writable"):
        factory.prepare(identity=changed.identity, workspace=root, grant=changed, spec_sha256=spec_digest(task))
    assert factory.audit_log._path.read_bytes() == before


def test_recovery_revalidates_current_protected_scratch_path(tmp_path, monkeypatch):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch)
    check = Path(raw["work_contracts"]["runtime_scratch"]["check_storage"])
    original = tmp_path/"old-check"
    check.rename(original); check.symlink_to(original, target_is_directory=True)
    before = factory.audit_log._path.read_bytes()
    with pytest.raises(WorkContractError, match="symlinks"):
        config.build_root_work_factory(Path(raw["task_store_root"]), task, recovery=True)
    assert factory.audit_log._path.read_bytes() == before


def test_actual_runtime_copy_uses_selected_directory_and_cleans_only_copy(tmp_path):
    environment = profile(tmp_path)
    scratch = private(tmp_path/"scratch"); sentinel = scratch/"keep"
    sentinel.write_bytes(b"unrelated host state")
    runtime = FrozenCheckRuntime(environment, scratch, writable_roots=(tmp_path/"workspace",))
    copied = runtime.tree.path
    try:
        assert copied.parent == scratch
        name, sha = environment.system_files[0]
        assert (copied/name.lstrip("/")).read_bytes() == Path(name).read_bytes()
        runtime.verify()
    finally:
        runtime.close()
    assert not copied.exists() and sentinel.read_bytes() == b"unrelated host state"


def handoff(factory, task, cycle, granted, root, tmp_path):
    completion = {"identity":binding(task), "base_sha":cycle.plan.base_sha,
        "spec_hash":cycle.plan.spec_sha256, "policy_hash":"f"*64,
        "workspace_root":str(root.parent), "plan_hash":"a"*64}
    store_for(factory.task_store_root, task).publish("plan", digest(binding(task)), completion)
    result = tmp_path/"result.json"; result.touch(mode=0o600)
    slot = ResultSlot.bind(result, granted.identity, "scratch-component")
    rule = ToolRule(TOOL, RiskClass.RESULT_SUBMISSION, ARGUMENTS, requires_sandbox=True,
                    result_slot=slot, allowed_roots=(str(tmp_path),))
    launch = SimpleNamespace(grant=replace(granted, tool_rules=(*granted.tool_rules, rule),
        scope=replace(granted.scope, tools=(*granted.scope.tools, TOOL))))
    return config.bind_root_handoff(factory, task, launch, cycle), completion


@pytest.mark.parametrize("custom", [False, True])
def test_bind_and_recover_handoff_use_only_runtime_port_and_preserve_durable_commit_storage(tmp_path, monkeypatch, custom):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch, scratch=custom, hygiene=True)
    port, completion = handoff(factory, task, cycle, granted, root, tmp_path)
    durable = factory.storage.parent/"commits"
    selected = Path(raw["work_contracts"]["runtime_scratch"]["commit_storage"]) if custom else durable
    assert port.committer.storage == durable and port.committer.runtime_storage == selected
    keep = durable/"original-index"; keep.write_bytes(b"durable recovery preimage")
    if custom:
        selected.rmdir(); selected.mkdir(mode=0o700)  # disposable runtime vanished, authority did not
    audit = factory.audit_log._path.read_bytes()
    recovered = config.build_root_work_factory(Path(raw["task_store_root"]), task, recovery=True, git=trusted_git(root))
    restored = recovered.recover(identity=granted.identity, workspace=root,
        spec_sha256=spec_digest(task), grant_sha256=granted.hash, plan_sha256=cycle.plan.hash)
    resumed = config.recover_host_handoff(recovered, task, restored, completion)
    assert resumed.committer.storage == durable and resumed.committer.runtime_storage == selected
    assert keep.read_bytes() == b"durable recovery preimage"
    assert recovered.audit_log._path.read_bytes() == audit


def test_committer_real_runtime_copy_reaches_execution_boundary_with_durable_preimage(tmp_path, monkeypatch):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch, hygiene=True)
    port, _ = handoff(factory, task, cycle, granted, root, tmp_path)
    edit(root); cycle.verify(runner)  # explicit synthetic check fixture, not an isolation attestation
    assert cycle.phase is WorkPhase.HYGIENE
    import herdr.check_runtime as module
    actual = module.FrozenCheckRuntime
    observed = []
    def copy(environment, storage, **kwargs):
        runtime = actual(environment, storage, **kwargs)
        observed.append((Path(storage), runtime.tree.path))
        return runtime
    class ExecutionBoundary(Exception): pass
    monkeypatch.setattr(module, "FrozenCheckRuntime", copy)
    def stop(*args):
        raise ExecutionBoundary("no process is executed by this component test")
    monkeypatch.setattr(HostCheckRunner, "_execute", stop)
    with pytest.raises(Exception) as stopped:
        port.committer(cycle)
    assert isinstance(stopped.value, ExecutionBoundary) or isinstance(stopped.value.__cause__, ExecutionBoundary)
    assert observed and observed[0][0] == factory.commit_runtime_storage
    assert not observed[0][1].exists()
    requested = [row for row in factory.audit_log.replay() if row["event"] == "work_local_commit_requested"]
    assert len(requested) == 1
    private_repo = Path(requested[0]["private_repository"])
    assert private_repo.parent == port.committer.storage
    assert (private_repo/"index-original").is_file()
    assert private_repo.exists()


@pytest.mark.parametrize("change", ["different", "legacy-to-custom", "custom-to-default"])
def test_recovery_cannot_change_original_scratch_mapping(tmp_path, monkeypatch, change):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch,
        scratch=change != "legacy-to-custom")
    before = factory.audit_log._path.read_bytes()
    if change == "custom-to-default":
        raw["work_contracts"].pop("runtime_scratch")
    elif change == "legacy-to-custom":
        raw["work_contracts"]["runtime_scratch"] = {
            "check_storage":str(private(tmp_path/"new-check")),
            "commit_storage":str(private(tmp_path/"new-commit"))}
    else:
        raw["work_contracts"]["runtime_scratch"]["check_storage"] = str(private(tmp_path/"new-check"))
    with pytest.raises(WorkContractError, match="original work runtime scratch changed"):
        config.build_root_work_factory(Path(raw["task_store_root"]), task, recovery=True)
    assert factory.audit_log._path.read_bytes() == before


def test_failed_prepare_admission_alone_cannot_establish_recoverable_work_plan(tmp_path, monkeypatch):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch, prepare=False)
    plan = factory.approve(identity=granted.identity, workspace=root, grant=granted,
                           spec_sha256=spec_digest(task))
    changed = replace(granted, runtime_assurance=replace(granted.runtime_assurance,
        writable_roots=(raw["work_contracts"]["runtime_scratch"]["check_storage"],)))
    with pytest.raises(WorkContractError, match="scratch is worker writable"):
        factory.prepare(identity=changed.identity, workspace=root, grant=changed, spec_sha256=spec_digest(task))
    assert factory.audit_log.replay() == []
    recovered = config.build_root_work_factory(Path(raw["task_store_root"]), task, recovery=True)
    with pytest.raises(WorkContractError, match="persisted host work contract missing"):
        recovered.recover(identity=granted.identity, workspace=root, spec_sha256=spec_digest(task),
                          grant_sha256=granted.hash, plan_sha256=plan.hash)
    assert recovered.audit_log.replay() == []


@pytest.mark.parametrize("bad", [None, {}, {"check_storage":"/check"},
    {"check_storage":"/check", "commit_storage":"/commit", "other":"/other"},
    {"check_storage":None, "commit_storage":"/commit"},
    {"check_storage":"relative", "commit_storage":"/commit"}])
def test_retained_scratch_mapping_is_closed_and_typed_even_for_graph_reader(bad):
    admitted = {"version":1, "identity":{}, "spec_sha256":"a"*64, "definition":{}, "environment":{},
                "runtime_scratch":bad}
    with pytest.raises(WorkContractError):
        config._admitted_scratch(admitted)


def test_original_canonical_parent_admission_reader_accepts_same_scratch_record(tmp_path, monkeypatch):
    raw, task, factory, cycle, granted, root = configured(tmp_path, monkeypatch)
    storage, admitted = config._original_work_admission(Path(raw["task_store_root"]), task,
                                                       factory.host_configuration_path)
    assert storage == factory.storage.parent
    assert digest(admitted) == digest(factory.host_admission)
    assert admitted["runtime_scratch"] == raw["work_contracts"]["runtime_scratch"]
