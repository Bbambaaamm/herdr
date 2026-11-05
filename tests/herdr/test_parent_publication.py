"""Parent publication uses real host oracle/commit/receipt; GitHub is a transport fixture.

The original SDK launch observation is the explicit fixture from test_work_handoff.
No model, credential or live GitHub operation is performed by this suite.
"""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import json
import os
import shutil
import subprocess
import threading

import pytest

from herdr.check_runner import HostCheckRunner
from herdr.evidence import EvidenceError, EvidenceMissing, EvidenceStore, EvidenceUnavailable, digest
from herdr.parent_publication import ParentArtifactPublisher, ParentPublicationPermit
from herdr.result_submission import payload_for_slot
from herdr.work_contract_host import HostWorkContractFactory
from herdr.work_cycle import WorkPhase
from tests.herdr.test_work_handoff import ready, boundary_workspace


class Remote:
    def __init__(self, base):
        self.base = base
        self.head = None
        self.prs = []
        self.pushes = 0
        self.creates = 0
        self.observations = 0
        self.push_fault = None
        self.create_fault = None
        self.bundle = None

    def observe(self, permit, artifact):
        self.observations += 1
        return deepcopy({"base_sha": self.base, "head_sha": self.head, "pull_requests": self.prs})

    def row(self, permit, artifact, number=42):
        return {"number": number, "repo": permit.repo, "base_sha": permit.base_sha,
            "base_branch": permit.base_branch, "head_sha": artifact.commit_sha,
            "head_branch": permit.head_branch, "state": "open"}

    def push(self, permit, artifact, bundle):
        self.pushes += 1
        self.bundle = bundle
        if self.push_fault != "before":
            self.head = artifact.commit_sha
        if self.push_fault:
            raise TimeoutError("fixture lost push response")

    def create_pull_request(self, permit, artifact, request):
        self.creates += 1
        assert request["base"] == permit.base_branch and request["head"] == permit.head_branch
        assert "Independent CI and review remain required" in request["body"]
        if self.create_fault != "before":
            self.prs.append(self.row(permit, artifact))
        if self.create_fault:
            raise TimeoutError("fixture lost PR response")


@pytest.fixture
def publication(boundary_workspace, monkeypatch):
    from herdr.evidence import parse_artifact
    from herdr.result_candidate import completion_candidate
    port, cycle, guard, result, task, plan, observations, log = ready(boundary_workspace, monkeypatch)
    port.prepare_request(cycle, "publish-original", {"pr_number": None})
    outcome = cycle.request_verification("publish-original", HostCheckRunner(
        port.committer.policy.environment, boundary_workspace/"host"/"checks", git=cycle.git))
    response = port.complete(cycle, "publish-original", outcome)
    payload = payload_for_slot(cycle.plan.identity, port.slot, response["submission"])
    factory = HostWorkContractFactory(approve=lambda **kw: pytest.fail("publication cannot readmit work"),
        environment=port.committer.policy.environment, storage=boundary_workspace/"host"/"checks",
        audit_log=log, git=cycle.git)
    factory.result_authority = port.result_authority
    factory.recover(identity=cycle.plan.identity, workspace=cycle.root,
        spec_sha256=cycle.plan.spec_sha256, grant_sha256=cycle.plan.grant_sha256,
        plan_sha256=cycle.plan.hash)
    artifact = parse_artifact(completion_candidate(payload, workspace=task["workspace"])["artifact"])
    permit = ParentPublicationPermit(plan["identity"], plan["repo"], plan["spec_hash"],
        plan["plan_hash"], plan["base_sha"], "main", artifact.branch, 2000,
        "Implement this component's approved bounded repair and regression coverage.")
    remote = Remote(artifact.base_sha)
    store = EvidenceStore(boundary_workspace/"host"/"parent-publication")
    publisher = ParentArtifactPublisher(permit=permit, receipt_store=store, transport=remote, clock=lambda: 1000)
    def forbidden(*a, **kw):
        pytest.fail("publication cannot start/restart SDK, oracle, or completion verification")
    monkeypatch.setattr("herdr.work_result_receipt.verify_invocation_session", forbidden)
    monkeypatch.setattr(factory, "before_completion", forbidden)
    before = log._path.read_bytes()
    return SimpleNamespace(publisher=publisher, remote=remote, factory=factory, task=task,
        payload=payload, plan=plan, artifact=artifact, permit=permit, store=store, log=log,
        audit_before=before, root=boundary_workspace)


def publish(p):
    return p.publisher.publish(task=p.task, payload=p.payload, plan=p.plan, factory=p.factory)


def test_parent_publishes_one_exact_result_and_replay_has_no_effects(publication):
    p = publication
    receipt = publish(p)
    assert receipt["pull_request"] == 42
    assert p.remote.pushes == p.remote.creates == 1
    intent = p.publisher._read("pr-intent")
    assert p.permit.public_summary in intent["request"]["body"]
    assert "run_token" not in intent["request"]["body"]
    assert p.remote.bundle.startswith(b"# v2 git bundle\n")
    assert p.log._path.read_bytes() == p.audit_before
    assert p.factory.cycle(p.factory.cycles[next(iter(p.factory.cycles))][0].plan.identity).phase is WorkPhase.HANDOFF
    observations = p.remote.observations
    shutil.rmtree(Path(p.task["workspace"]))
    p.factory = None
    p.publisher.clock = lambda: 3000
    assert publish(p) == receipt
    assert p.remote.observations == observations
    assert p.remote.pushes == p.remote.creates == 1


@pytest.mark.parametrize("effect", ["push", "create"])
@pytest.mark.parametrize("delivered", [False, True])
def test_lost_remote_reply_reconciles_without_repeating_the_effect(publication, effect, delivered):
    p = publication
    setattr(p.remote, effect+"_fault", "after" if delivered else "before")
    with pytest.raises(TimeoutError):
        publish(p)
    setattr(p.remote, effect+"_fault", None)
    if delivered:
        assert publish(p)["pull_request"] == 42
        assert p.remote.pushes == p.remote.creates == 1
    else:
        with pytest.raises(EvidenceError, match="unknown"):
            publish(p)
        assert getattr(p.remote, "pushes" if effect == "push" else "creates") == 1
    assert p.log._path.read_bytes() == p.audit_before


@pytest.mark.parametrize("fault", ["base", "head", "closed", "ambiguous"])
def test_changed_or_ambiguous_remote_target_never_creates_or_pushes(publication, fault):
    p = publication
    if fault == "base":
        p.remote.base = "e"*40
    elif fault == "head":
        p.remote.head = "e"*40
    else:
        p.remote.head = p.artifact.commit_sha
        p.remote.prs = [p.remote.row(p.permit, p.artifact)]
        if fault == "closed":
            p.remote.prs[0]["state"] = "closed"
        else:
            p.remote.prs.append(p.remote.row(p.permit, p.artifact, 43))
    with pytest.raises(EvidenceError):
        publish(p)
    assert p.remote.pushes == p.remote.creates == 0


def test_existing_exact_pr_is_adopted_without_another_publication(publication):
    p = publication
    p.remote.head = p.artifact.commit_sha
    p.remote.prs = [p.remote.row(p.permit, p.artifact)]
    assert publish(p)["pull_request"] == 42
    assert p.remote.pushes == p.remote.creates == 0


@pytest.mark.parametrize("fault", ["payload", "task", "plan", "artifact", "receipt"])
def test_forged_or_rebound_local_result_stops_before_remote_observation(publication, fault):
    p = publication
    if fault == "payload":
        p.payload["summary"] += " changed"
    elif fault == "task":
        p.task["run_token"] = "other"
    elif fault == "plan":
        p.plan["base_branch"] = "review/foreign"
        p.plan["plan_hash"] = digest({k:v for k,v in p.plan.items() if k not in {"plan_hash", "baseline"}})
    elif fault == "artifact":
        p.payload["evidence"][0]["herdr_completion"]["artifact"]["commit_sha"] = "e"*40
    else:
        for f in p.factory.result_authority.store.root.glob("work-result-*.json"):
            f.unlink()
    with pytest.raises((EvidenceError, ValueError)):
        publish(p)
    assert p.remote.observations == p.remote.pushes == p.remote.creates == 0


def test_expired_permit_cannot_start_publication(publication):
    p = publication
    p.publisher.clock = lambda: 2000
    with pytest.raises(EvidenceError, match="expired"):
        publish(p)
    assert p.remote.observations == p.remote.pushes == p.remote.creates == 0


def test_renewing_a_permit_cannot_reset_an_unknown_publication_intent(publication):
    p = publication
    p.remote.push_fault = "before"
    with pytest.raises(TimeoutError):
        publish(p)
    p.remote.push_fault = None
    p.publisher = ParentArtifactPublisher(permit=replace(p.permit, expires_at_epoch=3000),
        receipt_store=p.store, transport=p.remote, clock=lambda:1000)
    with pytest.raises(EvidenceError, match="candidate changed"):
        publish(p)
    assert p.remote.pushes == 1 and p.remote.creates == 0


def test_remote_callback_cannot_change_the_captured_local_result(publication):
    p = publication
    original_hash = digest(p.payload)
    observe = p.remote.observe
    def changing(*args):
        p.payload["summary"] = "caller changed this after entering publication"
        return observe(*args)
    p.remote.observe = changing
    receipt = publish(p)
    assert receipt["result_payload_sha256"] == original_hash
    with pytest.raises(EvidenceError):
        publish(p)
    assert p.remote.pushes == p.remote.creates == 1


def test_non_handoff_phase_cannot_trigger_an_oracle_or_publish(publication, monkeypatch):
    p = publication
    monkeypatch.setattr(p.factory, "cycle", lambda identity: SimpleNamespace(phase=WorkPhase.WORK))
    with pytest.raises(EvidenceError, match="already committed"):
        publish(p)
    assert p.remote.observations == p.remote.pushes == p.remote.creates == 0


def test_publication_lock_prevents_concurrent_duplicate_effects(publication):
    p = publication
    entered, release = threading.Event(), threading.Event()
    original = p.remote.observe
    def held(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    p.remote.observe = held
    errors = []
    def first():
        try:
            publish(p)
        except BaseException as exc:
            errors.append(exc)
    thread = threading.Thread(target=first)
    thread.start()
    assert entered.wait(5)
    try:
        with pytest.raises(EvidenceUnavailable):
            publish(p)
    finally:
        release.set()
        thread.join(10)
    assert not thread.is_alive() and not errors
    assert p.remote.pushes == p.remote.creates == 1


def test_exported_bundle_contains_the_verified_commit_and_imports_in_an_independent_bare_repo(publication):
    p = publication
    publish(p)
    env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    def git(where, *args):
        z = subprocess.run(["/usr/bin/git", "-C", str(where), *args], env=env,
            capture_output=True, timeout=20)
        assert z.returncode == 0, z.stderr
        return z.stdout.decode().strip()
    bare = p.root/"host"/"independent.git"
    bare.mkdir(mode=0o700)
    git(bare, "init", "--bare", "--template=")
    # This miniature source fixture is host-created and has no credentials.
    # Only the baseline is preloaded; the new commit must come from the bundle.
    git(bare, "-c", "protocol.file.allow=always", "fetch", "--no-tags", p.task["workspace"],
        p.artifact.base_sha+":refs/heads/base")
    bundle = p.root/"host"/"result.bundle"
    bundle.write_bytes(p.remote.bundle)
    git(bare, "-c", "protocol.file.allow=always", "fetch", "--no-tags", str(bundle),
        "HEAD:refs/heads/result")
    assert git(bare, "rev-parse", "refs/heads/result") == p.artifact.commit_sha
    assert git(bare, "rev-parse", "refs/heads/base") == p.artifact.base_sha


def test_parent_host_command_uses_original_worker_recovery_and_leaves_acceptance_to_worker(publication, monkeypatch, capsys):
    from importlib.machinery import SourceFileLoader
    from importlib.util import spec_from_loader, module_from_spec
    from tests.herdr.test_parent_github_transport import reader
    p = publication
    command = reader()
    p.task["work_contract_version"] = 1
    result = p.root / "host" / "command-result.json"
    result.write_text(json.dumps(p.payload)); result.chmod(0o600)
    parent_store = p.root / "host" / "canonical-tasks"
    parent_store.mkdir(mode=0o700)
    from agent_completion_evidence import store_for
    from herdr.evidence import binding
    store_for(parent_store,p.task).publish("plan",digest(binding(p.task)),p.plan)
    calls = []
    native_load = SourceFileLoader.exec_module
    def worker_load(loader, module):
        if loader.name != "herdr_parent_original_worker":
            return native_load(loader, module)
        module.ROOT = parent_store
        module.result_path = lambda task_id: result
        def recover(task):
            assert task == p.task
            calls.append("original-protected-recovery")
            return p.factory, p.factory.cycle(next(iter(p.factory.cycles.values()))[0].plan.identity)
        module._recover_root_work_cycle = recover
    monkeypatch.setattr(SourceFileLoader,"exec_module",worker_load)
    monkeypatch.setattr(command,"load_permit",lambda path:(p.permit,{"gh":"/parent/guarded-gh","home":"/parent/home"}))
    monkeypatch.setattr(command,"read_canonical_parent",lambda *args:deepcopy(p.task))
    monkeypatch.setattr(command,"GitHubParentTransport",lambda **kwargs:p.remote)
    # The fixture uses a finite test clock, outside the production command's wall clock.
    original_publisher = command.ParentArtifactPublisher
    monkeypatch.setattr(command,"ParentArtifactPublisher",lambda **kw:original_publisher(**kw,clock=lambda:1000))
    command.main(["--permit","/host-approved/test.json"])
    report = json.loads(capsys.readouterr().out)
    assert report["pull_request"] == 42 and report["completion_level"] == "reviewable_pull_request"
    assert report["semantic_acceptance"] is False and report["sdk_started"] is False
    assert calls == ["original-protected-recovery"]
    assert p.remote.pushes == p.remote.creates == 1
    assert p.log._path.read_bytes() == p.audit_before

