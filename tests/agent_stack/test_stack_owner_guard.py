"""Fail-closed owner-guard regression suite for issue #53 (G1-G12).

The first dependency-safe slice covers the Herdr supervised-consumer gate in
agent-stack-ensure. Production recovery/reconciliation (R1-R8) is deliberately
not implemented here and is not claimed by these tests.
"""
import contextlib
import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import errno
import shutil
import stat
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = ROOT / "agent-stack" / "bin" / "agent_stack_owner_guard.py"
ENSURE_PATH = ROOT / "agent-stack" / "bin" / "agent-stack-ensure"
HERDR_STATE = Path("/home/agentops/.local/state/agent-stack/herdr-development")

_counter = 0


def load_module(name, path):
    global _counter
    _counter += 1
    unique = f"{name}_{_counter}"
    loader = importlib.machinery.SourceFileLoader(unique, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


@pytest.fixture()
def guard():
    return load_module("owner_guard_test", GUARD_PATH)


def base_evidence(guard, **over):
    values = dict(
        consumer="Herdr",
        repo_identity="Bbambaaamm/herdr",
        execution_owner="none",
        supervised=True,
        supervisor_alive=False,
        decision_state="PAUSED",
        policy_hash="c" * 64,
        policy_profile=guard.HERDR_POLICY_PROFILE,
        expected_profile=guard.HERDR_POLICY_PROFILE,
        configured_consumer="herdr",
        configured_repository="Bbambaaamm/herdr",
        budget_seconds=1500,
        expected_budget_seconds=1500,
        fence_states={
            "supervisor.lock": "FREE",
            "cycle.lock": "FREE",
            "bootstrap.lock": "FREE",
        },
        active_attempts=(),
        live_side_children=(),
        checkpoint_digest="a" * 64,
        sampled_at="2026-11-24T00:00:00+00:00",
        source_digest="b" * 64,
        observed_generation="gen-1",
        fence="supervisor.lock=FREE;cycle.lock=FREE;bootstrap.lock=FREE",
    )
    values.update(over)
    return guard.OwnerEvidence(**values)


def obs_dict(guard, **over):
    """Internal observation shape consumed by build_owner_evidence."""
    values = dict(
        agent_id="herdr-hermes",
        consumer="Herdr",
        repository="Bbambaaamm/herdr",
        supervised=True,
        state="PAUSED",
        supervisor_alive=False,
        recorded_identity=None,
        observed_identity=None,
        decision_state=None,
        checkpoint_digest="a" * 64,
        fence_states={
            "supervisor.lock": "FREE",
            "cycle.lock": "FREE",
            "bootstrap.lock": "FREE",
        },
        budget_seconds=1500,
        expected_budget_seconds=1500,
        policy_hash="c" * 64,
        policy_profile=guard.HERDR_POLICY_PROFILE,
        expected_profile=guard.HERDR_POLICY_PROFILE,
        configured_consumer="herdr",
        configured_repository="Bbambaaamm/herdr",
        active_attempts=(),
        live_side_children=(),
        interactive_owner=None,
        sampled_at="2026-11-24T00:00:00+00:00",
    )
    values.update(over)
    return values


def write_json(path, value, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, mode)


def write_policy(repo_root, profile="herdr-core", consumer="herdr",
                 repository="Bbambaaamm/herdr"):
    path = repo_root / "configs" / "consumers" / "herdr.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["schema_version: 1"]
    if consumer is not None:
        lines.append(f"consumer: {consumer}")
    if repository is not None:
        lines.append(f"repository: {repository}")
    lines.extend([
        f"policy_profile: {profile}",
        "hard_invariants:",
        "  - no_direct_main_write",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


@contextlib.contextmanager
def held_lock(path):
    fd = os.open(str(path), os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def make_host(guard, tmp_path, *, state="RUNNING", start_ticks=None,
              command_sha256=None, budget_seconds=1500, profile="herdr-core",
              consumer="herdr", repository="Bbambaaamm/herdr",
              pending=(), running=(), uncertain_blocked=(), side_processes=(),
              checkpoint=b'{"task": "fixture"}'):
    """Build a synthetic but host-verified Herdr supervisor authority tree."""
    pid = os.getpid()
    identity = guard.process_identity(pid)
    if identity is None:
        pytest.skip("no live process identity available")
    recorded = {
        "pid": pid,
        "start_ticks": identity["start_ticks"],
        "command_sha256": identity["command_sha256"],
        "session": identity["session"],
    }
    if start_ticks is not None:
        recorded["start_ticks"] = str(start_ticks)
    if command_sha256 is not None:
        recorded["command_sha256"] = str(command_sha256)

    state_dir = tmp_path / "state"
    job = state_dir / "20260101T000000000000Z"
    job.mkdir(parents=True, mode=0o700)
    (job / "checkpoint.json").write_bytes(checkpoint)
    os.chmod(job / "checkpoint.json", 0o600)
    checkpoint_sha = hashlib.sha256(checkpoint).hexdigest()
    write_json(state_dir / "supervisor.json", {
        "supervisor": recorded,
        "state": state,
        "current_job": str(job),
        "decision": {"status": state, "checkpoint_sha256": checkpoint_sha},
    })
    write_json(job / "launch.json", {
        "budget_seconds": budget_seconds,
        "max_turns": 120,
        "side_processes": list(side_processes),
        "exit_code": 0,
    })
    for name in guard.SUPERVISOR_LOCK_NAMES:
        lock = state_dir / name
        lock.write_bytes(b"")
        os.chmod(lock, 0o600)

    repo_root = tmp_path / "repo"
    write_policy(repo_root, profile=profile, consumer=consumer, repository=repository)
    tasks_root = tmp_path / "tasks"
    for folder, items in (("pending", pending), ("running", running),
                          ("blocked", uncertain_blocked)):
        directory = tasks_root / folder
        directory.mkdir(parents=True, exist_ok=True)
        for index, task in enumerate(items):
            write_json(directory / f"task-{index}.json", task)
    return {
        "state_dir": state_dir,
        "job": job,
        "repo_root": repo_root,
        "tasks_root": tasks_root,
        "identity": identity,
        "recorded": recorded,
    }


class FakeAtomicAuthority:
    """Reference implementation of the atomic reservation seam for fixtures.

    The production slice supplies no authority, so real reservation calls deny.
    This fake exists only to prove the guard contract (one token, generation
    binding, replay idempotency) and is not deployed.
    """

    def __init__(self, root, approved_token="owner-token"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.fence = self.root / "interactive.start.fence"
        self.receipts = self.root / "receipts.json"
        self.approved = approved_token
        self.current_generation = "gen-1"

    def reserve(self, *, consumer, repository, observed_generation, operator_authority):
        fd = os.open(str(self.fence), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            receipts = {}
            if self.receipts.exists():
                receipts = json.loads(self.receipts.read_text(encoding="utf-8"))
            request = hashlib.sha256(json.dumps({
                "consumer": consumer, "repository": repository,
                "observed_generation": observed_generation,
                "operator_authority": operator_authority,
            }, sort_keys=True).encode("utf-8")).hexdigest()
            if observed_generation != self.current_generation:
                return SimpleNamespace(
                    granted=False, token=None, replay=False,
                    reason="generation_changed", observed_generation=observed_generation,
                )
            if request in receipts:
                stored = receipts[request]
                return SimpleNamespace(
                    granted=True, token=stored["token"], replay=True,
                    reason="already_reserved", observed_generation=observed_generation,
                )
            if operator_authority != self.approved:
                return SimpleNamespace(
                    granted=False, token=None, replay=False,
                    reason="operator_authority_rejected",
                    observed_generation=observed_generation,
                )
            token = "tok-" + hashlib.sha256(
                (request + str(len(receipts))).encode("utf-8")
            ).hexdigest()[:16]
            receipts[request] = {"token": token, "observed_generation": observed_generation}
            temporary = self.receipts.with_suffix(".tmp")
            temporary.write_text(json.dumps(receipts), encoding="utf-8")
            os.replace(temporary, self.receipts)
            return SimpleNamespace(
                granted=True, token=token, replay=False,
                reason="reserved", observed_generation=observed_generation,
            )
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)


def active_evidence(guard, **over):
    values = dict(decision_state="RUNNING", supervisor_alive=True,
                  fence_states={"supervisor.lock": "HELD", "cycle.lock": "HELD",
                                "bootstrap.lock": "FREE"})
    values.update(over)
    return base_evidence(guard, **values)


def interactive_evidence(guard):
    return base_evidence(
        guard,
        supervised=False,
        execution_owner="interactive",
        decision_state=None,
        expected_profile=None,
        fence_states={},
    )


# --------------------------------------------------------------------------
# G1: PAUSED + panel absent => BLOCKED_RECONCILIATION_REQUIRED, agent.start 0x
# --------------------------------------------------------------------------

def test_g1_paused_is_reconciliation_not_start(guard):
    decision = guard.evaluate_ownership(base_evidence(guard))
    assert decision.code == guard.DECISION_BLOCKED_RECONCILIATION
    assert guard.plan_agent_start(base_evidence(guard), None) == guard.DECISION_BLOCKED_RECONCILIATION


def test_g1_ensure_calls_agent_start_zero_times(guard, monkeypatch, tmp_path):
    ensure = load_module("ensure_g1", ENSURE_PATH)
    monkeypatch.setattr(ensure.owner_guard, "collect_herdr_observation",
                        lambda *a, **k: obs_dict(guard))
    monkeypatch.setattr(ensure, "list_agents", lambda: [])
    monkeypatch.setattr(ensure, "log", lambda message: None)
    monkeypatch.setattr(ensure, "GUARD_AUDIT_LOG", tmp_path / "audit.jsonl")
    calls = []

    def fake_run(args, timeout=30):
        calls.append(list(args))
        return ensure.subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(ensure, "run", fake_run)
    group = {"label": "Herdr", "repository": "Bbambaaamm/herdr"}
    spec = {"tab": "Hermes", "name": "herdr-hermes", "kind": "hermes",
            "args": ["-p", "quantlab", "chat"]}
    action = ensure.ensure_agent("w4", spec, group)
    assert action == guard.DECISION_BLOCKED_RECONCILIATION
    assert not any("agent" in call and "start" in call for call in calls)


@pytest.mark.skipif(not (HERDR_STATE / "supervisor.json").exists(),
                    reason="real Herdr supervisor state is host-specific")
def test_g1_real_host_paused_incident_blocks_and_preserves_evidence(guard, tmp_path):
    job = HERDR_STATE / "20261122T170339139503Z"
    protected = ("checkpoint.json", "continuation.json",
                 "unaccepted-continuation.json", "return-code.json")
    before = {name: hashlib.sha256((job / name).read_bytes()).hexdigest()
              for name in protected if (job / name).exists()}

    decision = guard.decide_herdr_agent_start(
        "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
        audit_path=tmp_path / "audit.jsonl",
    )

    after = {name: hashlib.sha256((job / name).read_bytes()).hexdigest()
             for name in protected if (job / name).exists()}
    assert before == after
    assert decision.code == guard.DECISION_BLOCKED_RECONCILIATION
    assert decision.evidence.checkpoint_digest == before.get("checkpoint.json")
    records = [json.loads(line) for line in
               (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert records[-1]["event"] == guard.DECISION_BLOCKED_RECONCILIATION
    assert records[-1]["consumer"] == "Herdr"
    assert records[-1]["operation"] == "agent.start"
    assert records[-1]["actor"] == "agent-stack-watchdog"
    assert records[-1]["decision_digest"]


# --------------------------------------------------------------------------
# G2: supervisor RUNNING + panel absent => SKIPPED_SUPERVISOR_OWNED, 0x
# --------------------------------------------------------------------------

def test_g2_active_supervisor_with_held_fence_is_skipped(guard, tmp_path):
    host = make_host(guard, tmp_path, state="RUNNING")
    with held_lock(host["state_dir"] / "supervisor.lock"):
        evidence = guard.get_execution_ownership(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=host["state_dir"], repo_root=host["repo_root"],
            tasks_root=host["tasks_root"],
        )
        decision = guard.evaluate_ownership(evidence)
    assert evidence.execution_owner == "supervised"
    assert evidence.supervisor_alive is True
    assert decision.code == guard.DECISION_SKIPPED_SUPERVISOR_OWNED


def test_g2_ensure_skips_without_start(guard, monkeypatch, tmp_path):
    ensure = load_module("ensure_g2", ENSURE_PATH)
    monkeypatch.setattr(ensure.owner_guard, "collect_herdr_observation", lambda *a, **k: obs_dict(
        guard, state="RUNNING", supervisor_alive=True,
        decision_state="RUNNING",
        fence_states={"supervisor.lock": "HELD", "cycle.lock": "HELD",
                      "bootstrap.lock": "FREE"},
    ))
    monkeypatch.setattr(ensure, "list_agents", lambda: [])
    monkeypatch.setattr(ensure, "log", lambda message: None)
    monkeypatch.setattr(ensure, "GUARD_AUDIT_LOG", tmp_path / "audit.jsonl")
    calls = []

    def fake_run(args, timeout=30):
        calls.append(list(args))
        return ensure.subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(ensure, "run", fake_run)
    group = {"label": "Herdr", "repository": "Bbambaaamm/herdr"}
    spec = {"tab": "Hermes", "name": "herdr-hermes", "kind": "hermes", "args": []}
    action = ensure.ensure_agent("w4", spec, group)
    assert action == guard.DECISION_SKIPPED_SUPERVISOR_OWNED
    assert calls == []


# --------------------------------------------------------------------------
# G3: missing/corrupt/symlink/oversize authority evidence => fail closed, 0x
# --------------------------------------------------------------------------

def test_g3_invalid_supervisor_evidence_fails_closed(guard, tmp_path):
    repo_root = tmp_path / "repo"
    write_policy(repo_root)
    tasks_root = tmp_path / "tasks"
    tasks_root.mkdir()

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    with pytest.raises(guard.GuardObservationError):
        guard.get_execution_ownership(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=state_dir, repo_root=repo_root, tasks_root=tasks_root,
        )
    assert guard.decide_herdr_agent_start(
        "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
        state_dir=state_dir, repo_root=repo_root, tasks_root=tasks_root,
        audit_path=tmp_path / "audit.jsonl",
    ).code == guard.DECISION_BLOCKED_UNKNOWN

    corrupt = state_dir / "corrupt.json"
    corrupt.write_bytes(b"this is not json")
    os.symlink(corrupt, state_dir / "supervisor.json")
    with pytest.raises(guard.GuardObservationError) as symlink_error:
        guard.get_execution_ownership(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=state_dir, repo_root=repo_root, tasks_root=tasks_root,
        )
    assert symlink_error.value.reason == "symlink"
    state_dir.joinpath("supervisor.json").unlink()

    oversize = tmp_path / "oversize.json"
    oversize.write_bytes(b"x" * (guard.BOUNDED_BYTES_LIMIT + 1))
    os.replace(oversize, state_dir / "supervisor.json")
    with pytest.raises(guard.GuardObservationError) as oversize_error:
        guard.get_execution_ownership(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=state_dir, repo_root=repo_root, tasks_root=tasks_root,
        )
    assert oversize_error.value.reason == "oversize"
    state_dir.joinpath("supervisor.json").unlink()

    write_json(state_dir / "supervisor.json", {"state": "NOT_A_STATE"})
    with pytest.raises(guard.GuardObservationError) as state_error:
        guard.get_execution_ownership(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=state_dir, repo_root=repo_root, tasks_root=tasks_root,
        )
    assert state_error.value.reason == "supervisor_state_invalid"


# --------------------------------------------------------------------------
# G4: pending/running/uncertain durable task or live side child => 0x
# --------------------------------------------------------------------------

def test_g4_pending_durable_attempt_blocks(guard, tmp_path):
    host = make_host(guard, tmp_path, state="RUNNING",
                     pending=[{"id": "task-1", "repo": "Bbambaaamm/herdr"}])
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = guard.decide_herdr_agent_start(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=host["state_dir"], repo_root=host["repo_root"],
            tasks_root=host["tasks_root"], audit_path=tmp_path / "audit.jsonl",
        )
    assert decision.code == guard.DECISION_BLOCKED_ATTEMPT
    assert decision.evidence.active_attempts


def test_g4_live_side_child_blocks(guard, tmp_path):
    host = make_host(guard, tmp_path, state="RUNNING",
                     side_processes=[host_identity := guard.process_identity(os.getpid())])
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = guard.decide_herdr_agent_start(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=host["state_dir"], repo_root=host["repo_root"],
            tasks_root=host["tasks_root"], audit_path=tmp_path / "audit.jsonl",
        )
    assert decision.code == guard.DECISION_BLOCKED_ATTEMPT
    assert str(os.getpid()) in decision.evidence.live_side_children
    assert host_identity is not None


# --------------------------------------------------------------------------
# G5: stale PID identity is never accepted as the supervisor
# --------------------------------------------------------------------------

def test_g5_stale_pid_with_wrong_start_ticks_is_not_authority(guard, tmp_path):
    host = make_host(guard, tmp_path, state="RUNNING", start_ticks="1")
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = guard.decide_herdr_agent_start(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=host["state_dir"], repo_root=host["repo_root"],
            tasks_root=host["tasks_root"], audit_path=tmp_path / "audit.jsonl",
        )
    assert decision.code == guard.DECISION_BLOCKED_UNKNOWN
    assert decision.reason == "stale_supervisor_identity"
    assert decision.evidence.supervisor_alive is False


def test_g5_command_sha_mismatch_is_not_authority(guard, tmp_path):
    host = make_host(guard, tmp_path, state="WAITING", command_sha256="0" * 64)
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = guard.decide_herdr_agent_start(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=host["state_dir"], repo_root=host["repo_root"],
            tasks_root=host["tasks_root"], audit_path=tmp_path / "audit.jsonl",
        )
    assert decision.code == guard.DECISION_BLOCKED_UNKNOWN
    assert guard.identity_matches(host["recorded"], host["identity"]) is False
    assert guard.identity_matches(
        {**host["recorded"], "command_sha256": host["identity"]["command_sha256"]},
        host["identity"],
    ) is True


# --------------------------------------------------------------------------
# G6-G8: atomic reservation seam (fake existing authority in fixtures)
# --------------------------------------------------------------------------

def test_g6_concurrent_watchdog_runs_grant_one_token(guard, tmp_path):
    authority = FakeAtomicAuthority(tmp_path / "authority")
    barrier = threading.Barrier(2)
    results = []

    def worker():
        barrier.wait()
        results.append(guard.reserve_interactive_start(
            "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority,
        ))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert len(results) == 2
    tokens = {result.token for result in results if result.granted}
    assert len(tokens) == 1
    evidence = interactive_evidence(guard)
    plans = [guard.plan_agent_start(evidence, result) for result in results]
    assert plans.count("start") == 1
    assert plans.count("already-reserved") == 1


def test_g7_snapshot_to_reserve_generation_race_denies(guard, tmp_path):
    authority = FakeAtomicAuthority(tmp_path / "authority")
    granted = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority,
    )
    assert granted.granted is True
    authority.current_generation = "gen-2"
    raced = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority,
    )
    assert raced.granted is False
    assert guard.plan_agent_start(interactive_evidence(guard), raced) != "start"


def test_g8_replay_same_request_after_restart_does_not_start_twice(guard, tmp_path):
    authority = FakeAtomicAuthority(tmp_path / "authority")
    first = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority,
    )
    replay = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority,
    )
    assert first.granted and replay.granted
    assert first.token == replay.token
    assert replay.replay is True
    evidence = interactive_evidence(guard)
    plans = [guard.plan_agent_start(evidence, first),
             guard.plan_agent_start(evidence, replay)]
    assert plans.count("start") == 1
    assert plans.count("already-reserved") == 1


def test_g8_no_atomic_authority_api_denies_instead_of_improvising(guard, tmp_path):
    denied = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token",
        audit_path=tmp_path / "audit.jsonl",
    )
    assert denied.granted is False
    assert denied.code == guard.DECISION_BLOCKED_UNKNOWN
    assert denied.reason == "no_atomic_authority_api"


# --------------------------------------------------------------------------
# G9: hard policy/budget/fence mismatch => deny, no fallback model
# --------------------------------------------------------------------------

def test_g9_hard_policy_budget_and_fence_mismatches_deny(guard, tmp_path):
    profile = guard.evaluate_ownership(
        active_evidence(guard, policy_profile="other-profile"))
    assert profile.code == guard.DECISION_BLOCKED_POLICY

    budget = guard.evaluate_ownership(
        active_evidence(guard, budget_seconds=9999, expected_budget_seconds=1500))
    assert budget.code == guard.DECISION_BLOCKED_POLICY

    wrong_policy_host = make_host(guard, tmp_path, state="RUNNING",
                                  repository="Other/repo")
    with held_lock(wrong_policy_host["state_dir"] / "supervisor.lock"):
        wrong_policy = guard.decide_herdr_agent_start(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=wrong_policy_host["state_dir"],
            repo_root=wrong_policy_host["repo_root"],
            tasks_root=wrong_policy_host["tasks_root"],
            audit_path=tmp_path / "audit.jsonl",
        )
    assert wrong_policy.code == guard.DECISION_BLOCKED_POLICY
    assert wrong_policy.reason == "host_policy_identity_mismatch"

    missing_fence = guard.evaluate_ownership(base_evidence(
        guard, decision_state="RUNNING", supervisor_alive=True,
        fence_states={"supervisor.lock": "MISSING", "cycle.lock": "FREE",
                      "bootstrap.lock": "FREE"},
    ))
    assert missing_fence.code == guard.DECISION_BLOCKED_UNKNOWN

    not_held = guard.evaluate_ownership(base_evidence(
        guard, decision_state="RUNNING", supervisor_alive=True,
        fence_states={"supervisor.lock": "FREE", "cycle.lock": "FREE",
                      "bootstrap.lock": "FREE"},
    ))
    assert not_held.code == guard.DECISION_BLOCKED_UNKNOWN

    orphan = guard.evaluate_ownership(base_evidence(
        guard, decision_state="ERROR", supervisor_alive=False,
        fence_states={"supervisor.lock": "HELD", "cycle.lock": "FREE",
                      "bootstrap.lock": "FREE"},
    ))
    assert orphan.code == guard.DECISION_BLOCKED_UNKNOWN

    for decision in (profile, budget, wrong_policy, missing_fence, not_held, orphan):
        assert guard.plan_agent_start(decision.evidence, None) != "start"


# --------------------------------------------------------------------------
# G10: clean interactive authority + acquired fence => exactly one start
# --------------------------------------------------------------------------

def test_g10_interactive_clean_authority_starts_once_then_zero(guard, tmp_path):
    authority = FakeAtomicAuthority(tmp_path / "authority")
    evidence = interactive_evidence(guard)
    decision = guard.evaluate_ownership(evidence)
    assert decision.code == guard.DECISION_RESTORED_INTERACTIVE
    reservation = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority,
    )
    assert reservation.granted is True
    assert guard.plan_agent_start(evidence, reservation, agent_present=False) == "start"
    assert guard.plan_agent_start(evidence, reservation, agent_present=True) == "healthy"


# --------------------------------------------------------------------------
# Independent review follow-ups: real supervisor states, negative inventory
# fixtures, fail-closed missing evidence, exact policy identity and coverage
# of every Herdr start path before the healthy short-circuit.
# --------------------------------------------------------------------------

def _review_decide(guard, host, audit_path):
    return guard.decide_herdr_agent_start(
        "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
        state_dir=host["state_dir"], repo_root=host["repo_root"],
        tasks_root=host["tasks_root"], audit_path=audit_path)


def test_review_running_and_continuing_are_real_end_to_end(guard, tmp_path):
    for index, state in enumerate(("RUNNING", "CONTINUING")):
        host = make_host(guard, tmp_path / f"state-{index}", state=state)
        with held_lock(host["state_dir"] / "supervisor.lock"):
            decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
        assert decision.code == guard.DECISION_SKIPPED_SUPERVISOR_OWNED
        assert decision.reason == "supervisor_owns_consumer"


def test_review_waiting_live_supervisor_is_owned(guard, tmp_path):
    host = make_host(guard, tmp_path, state="WAITING")
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_SKIPPED_SUPERVISOR_OWNED
    assert decision.reason == "supervisor_waiting"


def test_review_waiting_live_pid_without_held_fence_fails_closed(guard, tmp_path):
    host = make_host(guard, tmp_path / "waiting-free", state="WAITING")
    # Recorded PID is live, but supervisor.lock is FREE: no owner claim.
    decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_BLOCKED_UNKNOWN
    assert decision.reason == "supervisor_fence_not_held"


def test_review_legacy_continue_state_fails_closed(guard, tmp_path):
    host = make_host(guard, tmp_path)
    write_json(host["state_dir"] / "supervisor.json", {
        "supervisor": host["recorded"], "state": "CONTINUE",
        "current_job": str(host["job"]),
        "decision": {"status": "CONTINUE"},
    })
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_BLOCKED_UNKNOWN
    assert str(decision.reason).startswith("observation_failed:")


def test_review_unreadable_native_inventory_fails_closed(guard, tmp_path):
    corrupt = make_host(guard, tmp_path / "corrupt")
    (corrupt["tasks_root"] / "pending" / "bad.json").write_text(
        "{not-json", encoding="utf-8")
    symlinked = make_host(guard, tmp_path / "symlink")
    target = symlinked["tasks_root"] / "pending" / "real.json"
    target.write_text("{}", encoding="utf-8")
    (symlinked["tasks_root"] / "pending" / "link.json").symlink_to(target)
    missing = make_host(guard, tmp_path / "missing")
    shutil.rmtree(missing["tasks_root"])
    for host in (corrupt, symlinked, missing):
        with held_lock(host["state_dir"] / "supervisor.lock"):
            decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
        assert decision.code == guard.DECISION_BLOCKED_UNKNOWN
        assert str(decision.reason).startswith("observation_failed:")


def test_review_running_and_uncertain_blocked_negative_fixtures(guard, tmp_path):
    running_host = make_host(guard, tmp_path / "running",
                             running=[{"id": "task-r", "repo": "Bbambaaamm/herdr"}])
    with held_lock(running_host["state_dir"] / "supervisor.lock"):
        running = _review_decide(guard, running_host, tmp_path / "audit.jsonl")
    assert running.code == guard.DECISION_BLOCKED_ATTEMPT
    assert running.reason == "durable_active_attempt"

    blocked_host = make_host(guard, tmp_path / "blocked", uncertain_blocked=[{
        "id": "task-b", "repo": "Bbambaaamm/herdr", "state": "BLOCKED",
        "diagnostics": {"watchdog_blocker": "uncertain"},
    }])
    with held_lock(blocked_host["state_dir"] / "supervisor.lock"):
        blocked = _review_decide(guard, blocked_host, tmp_path / "audit.jsonl")
    assert blocked.code == guard.DECISION_BLOCKED_ATTEMPT
    assert blocked.reason == "durable_active_attempt"


def test_review_host_policy_identity_missing_is_blocked(guard, tmp_path):
    host = make_host(guard, tmp_path, consumer=None, repository=None)
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_BLOCKED_POLICY
    assert decision.reason == "host_policy_identity_missing"


@pytest.mark.parametrize("damage,reason", [
    ("repo", "repo_root_missing"),
    ("policy", "host_policy_missing"),
    ("invalid_policy", "host_policy_invalid"),
    ("native_root", "native_tasks_root_missing"),
    ("native_dir", "native_pending_missing"),
])
def test_review_observation_reasons_are_specific_and_safe(guard, tmp_path, damage, reason):
    host = make_host(guard, tmp_path / "host")
    policy = host["repo_root"] / "configs" / "consumers" / "herdr.yaml"
    if damage == "repo":
        shutil.rmtree(host["repo_root"])
    elif damage == "policy":
        policy.unlink()
    elif damage == "invalid_policy":
        policy.write_bytes(b"secret-path /private/token\xff")
    elif damage == "native_root":
        shutil.rmtree(host["tasks_root"])
    else:
        (host["tasks_root"] / "pending").rmdir()
    decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_BLOCKED_UNKNOWN
    assert decision.reason == "observation_failed:" + reason
    assert "/private/token" not in (tmp_path / "audit.jsonl").read_text()


def test_review_unreadable_policy_has_safe_reason(guard, monkeypatch, tmp_path):
    host = make_host(guard, tmp_path / "host")
    original = guard._bounded_bytes
    def unreadable_policy(path, limit=guard.BOUNDED_BYTES_LIMIT):
        if Path(path).name == "herdr.yaml":
            raise guard.GuardObservationError("unreadable")
        return original(path, limit)
    monkeypatch.setattr(guard, "_bounded_bytes", unreadable_policy)
    decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_BLOCKED_UNKNOWN
    assert decision.reason == "observation_failed:host_policy_unreadable"


def _audit_once(guard, path, **overrides):
    values = dict(event="BLOCKED_OWNER_UNKNOWN", actor="watchdog", consumer="Herdr",
                  operation="agent.start", reason="missing_evidence",
                  decision_digest="d" * 64, audit_path=path)
    values.update(overrides)
    return guard.emit_audit(**values)


def test_review_audit_is_bounded_rotated_and_jsonl(guard, tmp_path):
    path = tmp_path / "audit.jsonl"
    for index in range(400):
        _audit_once(guard, path, extra={"observed_generation": str(index)})
    backup = Path(str(path) + ".1")
    assert backup.exists()
    for file in (path, backup):
        assert file.stat().st_size <= guard.AUDIT_MAX_BYTES
        assert all(json.loads(line)["event"] == "BLOCKED_OWNER_UNKNOWN"
                   for line in file.read_text().splitlines())
    assert json.loads(path.read_text().splitlines()[-1])["observed_generation"] == "399"


def test_review_audit_concurrent_writers_preserve_lines(guard, tmp_path):
    path = tmp_path / "audit.jsonl"
    threads = [threading.Thread(target=lambda index=i: _audit_once(
        guard, path, extra={"observed_generation": str(index)})) for i in range(30)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert {record["observed_generation"] for record in records} == {
        str(index) for index in range(30)}


def test_review_audit_rejects_symlink_and_oversized_entry(guard, tmp_path):
    target = tmp_path / "target"
    target.write_text("untouched")
    path = tmp_path / "audit.jsonl"
    path.symlink_to(target)
    with pytest.raises(guard.GuardObservationError):
        _audit_once(guard, path)
    assert target.read_text() == "untouched"
    path.unlink()
    with pytest.raises(guard.GuardObservationError, match="audit_entry_oversize"):
        _audit_once(guard, path, reason="x" * guard.AUDIT_ENTRY_MAX_BYTES)
    assert not path.exists()


def test_review_audit_failed_write_rolls_back_and_blocks(guard, monkeypatch, tmp_path):
    path = tmp_path / "audit.jsonl"
    _audit_once(guard, path)
    before = path.read_bytes()
    original = guard.os.write
    def disk_full(fd, data):
        if data.startswith(b'{"actor"'):
            original(fd, data[:8])
            raise OSError(errno.ENOSPC, "full")
        return original(fd, data)
    monkeypatch.setattr(guard.os, "write", disk_full)
    with pytest.raises(guard.GuardObservationError, match="audit_write_failed"):
        _audit_once(guard, path)
    assert path.read_bytes() == before


@pytest.mark.parametrize("generation", ["", ".1"])
@pytest.mark.parametrize("bad_tail", [b'{"interrupted":', b'{"valid":true}', b'not json\n', b'{}\n' + b'x' * 4097 + b'\n'])
def test_review_audit_refuses_malformed_existing_generation(
    guard, tmp_path, generation, bad_tail
):
    path = tmp_path / "audit.jsonl"
    _audit_once(guard, path)
    original = path.read_bytes()
    target = Path(str(path) + generation)
    seeded = original + bad_tail if not generation else b'{"prior":true}\n' + bad_tail
    target.write_bytes(seeded)
    with pytest.raises(guard.GuardObservationError, match="audit_file_invalid"):
        _audit_once(guard, path)
    assert target.read_bytes() == seeded
    if generation:
        assert path.read_bytes() == original
    assert all(file.stat().st_size <= guard.AUDIT_MAX_BYTES
               for file in (path, target))


def test_review_audit_concurrent_writers_refuse_interrupted_tail(guard, tmp_path):
    path = tmp_path / "audit.jsonl"
    _audit_once(guard, path)
    truncated = path.read_bytes() + b'{"interrupted":'
    path.write_bytes(truncated)
    errors = []
    barrier = threading.Barrier(8)

    def append():
        barrier.wait()
        try:
            _audit_once(guard, path)
        except guard.GuardObservationError as exc:
            errors.append(exc.reason)

    threads = [threading.Thread(target=append) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert errors == ["audit_file_invalid"] * 8
    assert path.read_bytes() == truncated


@pytest.mark.parametrize("swap_after_lock", [False, True])
def test_review_audit_parent_swap_stays_on_pinned_directory(
    guard, monkeypatch, tmp_path, swap_after_lock
):
    parent = tmp_path / "active"
    parent.mkdir()
    moved = tmp_path / "moved"
    outside = tmp_path / "outside"
    outside.mkdir()
    path = parent / "audit.jsonl"

    def swap():
        parent.rename(moved)
        parent.symlink_to(outside, target_is_directory=True)

    if swap_after_lock:
        original_flock = guard.fcntl.flock

        def swap_on_lock(fd, operation):
            result = original_flock(fd, operation)
            if operation & guard.fcntl.LOCK_EX:
                swap()
            return result

        monkeypatch.setattr(guard.fcntl, "flock", swap_on_lock)
    else:
        original_open = guard.os.open

        def swap_before_lock(file, flags, *args, **kwargs):
            if file == "audit.jsonl.lock":
                swap()
            return original_open(file, flags, *args, **kwargs)

        monkeypatch.setattr(guard.os, "open", swap_before_lock)

    _audit_once(guard, path)
    assert len((moved / "audit.jsonl").read_text().splitlines()) == 1
    assert not (outside / "audit.jsonl").exists()
    assert not (outside / "audit.jsonl.lock").exists()


@pytest.mark.parametrize("generation", ["", ".1"])
def test_review_audit_fifo_refused_without_affecting_other_audit(
    guard, tmp_path, generation
):
    path = tmp_path / "audit.jsonl"
    os.mkfifo(str(path) + generation)
    with pytest.raises(guard.GuardObservationError):
        _audit_once(guard, path)
    other = tmp_path / "other.jsonl"
    _audit_once(guard, other, consumer="Other")
    assert json.loads(other.read_text())["consumer"] == "Other"


def test_review_audit_first_append_syncs_directory_and_fails_closed(
    guard, monkeypatch, tmp_path
):
    path = tmp_path / "audit.jsonl"
    original_fsync = guard.os.fsync
    synced = []

    def record_fsync(fd):
        mode = guard.os.fstat(fd).st_mode
        synced.append("directory" if stat.S_ISDIR(mode) else "file")
        return original_fsync(fd)

    monkeypatch.setattr(guard.os, "fsync", record_fsync)
    _audit_once(guard, path)
    assert synced == ["file", "directory"]

    failing = tmp_path / "failing.jsonl"

    def fail_directory_sync(fd):
        if stat.S_ISDIR(guard.os.fstat(fd).st_mode):
            raise OSError(errno.EIO, "directory sync failed")
        return original_fsync(fd)

    monkeypatch.setattr(guard.os, "fsync", fail_directory_sync)
    with pytest.raises(guard.GuardObservationError, match="audit_write_failed"):
        _audit_once(guard, failing)
    assert failing.read_bytes() == b""


def test_review_audit_missing_parent_is_refused(guard, tmp_path):
    path = tmp_path / "missing" / "audit.jsonl"
    with pytest.raises(guard.GuardObservationError, match="audit_path_invalid"):
        _audit_once(guard, path)
    assert not path.parent.exists()


def test_review_audit_recovers_interrupted_rotation(guard, tmp_path):
    path = tmp_path / "audit.jsonl"
    backup = tmp_path / "audit.jsonl.1"
    temporary = tmp_path / "audit.jsonl.tmp"
    backup.write_text('{"prior":true}\n')
    temporary.write_text('{"interrupted":true}\n')
    _audit_once(guard, path)
    assert backup.read_text() == '{"prior":true}\n'
    assert not temporary.exists()
    assert json.loads(path.read_text())["event"] == "BLOCKED_OWNER_UNKNOWN"


@pytest.mark.parametrize("site", [
    "supervisor", "checkpoint", "continuation", "unaccepted", "launch",
    "policy", "pending", "running", "blocked", "supervisor_lock",
    "cycle_lock", "bootstrap_lock",
])
def test_review_evidence_fifo_does_not_stall_stack_consumers(guard, tmp_path, site):
    host = make_host(guard, tmp_path / "host", state="PAUSED")
    paths = {
        "supervisor": host["state_dir"] / "supervisor.json",
        "checkpoint": host["job"] / "checkpoint.json",
        "continuation": host["job"] / "continuation.json",
        "unaccepted": host["job"] / "unaccepted-continuation.json",
        "launch": host["job"] / "launch.json",
        "policy": host["repo_root"] / "configs/consumers/herdr.yaml",
        "pending": host["tasks_root"] / "pending/task-0.json",
        "running": host["tasks_root"] / "running/task-0.json",
        "blocked": host["tasks_root"] / "blocked/task-0.json",
        "supervisor_lock": host["state_dir"] / "supervisor.lock",
        "cycle_lock": host["state_dir"] / "cycle.lock",
        "bootstrap_lock": host["state_dir"] / "bootstrap.lock",
    }
    target = paths[site]
    target.unlink(missing_ok=True)
    os.mkfifo(target)
    script = """
import importlib.machinery, importlib.util, json, sys
from pathlib import Path
def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module
ensure = load('fifo_ensure', sys.argv[1])
state, repo, tasks, audit = map(Path, sys.argv[2:])
collector = ensure.owner_guard.collect_herdr_observation
ensure.owner_guard.collect_herdr_observation = lambda agent_id, **kw: collector(
    agent_id, state_dir=state, repo_root=repo, tasks_root=tasks)
ensure.GUARD_AUDIT_LOG = audit
ensure.LOG = audit.with_suffix('.log')
ensure.list_agents = lambda: []
ensure.list_tabs = lambda: [{'workspace_id': 'w', 'label': 'Codex', 'tab_id': 't'}]
ensure.list_panes = lambda _: [{'tab_id': 't', 'pane_id': 'p'}]
starts = []
def fake_run(args, timeout=30):
    starts.append(args[args.index('start') + 1])
    return ensure.subprocess.CompletedProcess(args, 0, stdout='', stderr='')
ensure.run = fake_run
spec = lambda name: {'name': name, 'tab': 'Codex', 'kind': 'codex', 'args': []}
herdr = ensure.ensure_agent('w', spec('herdr-codex'),
                           {'label': 'Herdr', 'repository': 'Bbambaaamm/herdr'})
other = ensure.ensure_agent('w', spec('majak-codex'), {'label': 'Majak'})
print(json.dumps({'herdr': herdr, 'other': other, 'starts': starts}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(ENSURE_PATH), str(host["state_dir"]),
         str(host["repo_root"]), str(host["tasks_root"]), str(tmp_path / "audit.jsonl")],
        capture_output=True, text=True, timeout=5, check=True,
    )
    result = json.loads(completed.stdout.splitlines()[-1])
    assert result["herdr"].startswith("BLOCKED_")
    assert result["other"] == "restored"
    assert result["starts"] == ["majak-codex"]


def test_review_guard_precedes_healthy_short_circuit(guard, monkeypatch, tmp_path):
    ensure = load_module("ensure_g11_healthy", ENSURE_PATH)
    ensure.STATE = tmp_path / "state"
    ensure.LOG = tmp_path / "ensure.log"
    ensure.GUARD_AUDIT_LOG = tmp_path / "audit.jsonl"
    healthy = {"herdr-hermes", "herdr-codex"}
    ensure.list_agents = lambda: [
        {"name": name, "interactive_ready": True, "agent_status": "idle"}
        for name in healthy
    ]
    started = []

    def fake_run(args, timeout=30):
        started.append(list(args))
        return ensure.subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(ensure, "run", fake_run)
    monkeypatch.setattr(ensure.owner_guard, "collect_herdr_observation",
                        lambda *a, **k: obs_dict(guard, state="PAUSED"))
    codex_spec = {"tab": "Codex", "name": "herdr-codex", "kind": "codex", "args": []}
    hermes_spec = {"tab": "Hermes", "name": "herdr-hermes", "kind": "hermes",
                   "args": ["-p", "quantlab", "chat"]}
    group = {"label": "Herdr", "cwd": "/tmp/herdr",
             "repository": "Bbambaaamm/herdr", "agents": [codex_spec, hermes_spec]}
    assert ensure.ensure_agent("wid", codex_spec, group) == \
        guard.DECISION_BLOCKED_RECONCILIATION
    assert ensure.ensure_agent("wid", hermes_spec, group) == \
        guard.DECISION_BLOCKED_RECONCILIATION
    assert started == []

    def interactive_observation(*args, **kwargs):
        return ensure.owner_guard.build_owner_evidence(obs_dict(
            guard, supervised=False,
            interactive_owner={"owner": "human"},
            state=None, decision_state=None))

    monkeypatch.setattr(ensure.owner_guard, "get_execution_ownership",
                        interactive_observation)
    assert ensure.ensure_agent("wid", hermes_spec, group) == "healthy"
    assert started == []


# --------------------------------------------------------------------------
# G11: Herdr block does not stop independent consumers
# --------------------------------------------------------------------------

@pytest.mark.parametrize("fault", ["corrupt_current", "corrupt_backup", "invalid_path",
                                    "enospc", "malformed_evidence", "herdr_checkout",
                                    "herdr_agent_failure"])
def test_g11_main_isolates_herdr_faults_across_all_consumers(
        guard, monkeypatch, tmp_path, capfd, fault):
    ensure = load_module("ensure_g11_fault", ENSURE_PATH)
    monkeypatch.setattr(ensure, "STATE", tmp_path / "state")
    monkeypatch.setattr(ensure, "LOG", tmp_path / "ensure.log")
    audit = tmp_path / "audit.jsonl"
    if fault == "invalid_path":
        audit = tmp_path / "missing-parent" / "audit.jsonl"
    monkeypatch.setattr(ensure, "GUARD_AUDIT_LOG", audit)
    ensure.STATE.mkdir()
    marker = ensure.STATE / "independent-state.json"
    marker.write_bytes(b"independent state unchanged\n")
    boot = tmp_path / "herdr-autostart.log"
    boot.write_bytes(b"existing boot marker\n")
    monkeypatch.setattr(ensure, "HERDR_BOOT_LOG", boot)
    monkeypatch.setattr(ensure, "ensure_desktop_commander", lambda: None)
    monkeypatch.setattr(ensure, "ensure_herdr_server", lambda: None)
    visited = []

    def checkout(cwd, repository, repo_url):
        if fault == "herdr_checkout" and repository == "Bbambaaamm/herdr":
            raise RuntimeError("private checkout detail must not appear")

    monkeypatch.setattr(ensure, "ensure_repo_checkout", checkout)
    monkeypatch.setattr(ensure, "ensure_workspace", lambda label, cwd: visited.append(label) or label)
    monkeypatch.setattr(ensure, "ensure_tabs", lambda *args: None)
    monkeypatch.setattr(ensure, "list_tabs", lambda: [
        {"workspace_id": label, "label": tab, "tab_id": label + tab}
        for label in visited for tab in ("Codex", "Hermes", "Sol", "Astra")])
    monkeypatch.setattr(ensure, "list_panes", lambda wid: [
        {"tab_id": wid + tab, "pane_id": wid + tab + "pane"}
        for tab in ("Codex", "Hermes", "Sol", "Astra")])
    def observation(*args, **kwargs):
        value = obs_dict(guard, state="PAUSED")
        if fault == "malformed_evidence":
            value["fence_states"] = 7
        return value

    monkeypatch.setattr(ensure.owner_guard, "collect_herdr_observation", observation)
    independently_missing = {"majak-codex", "loxxess-hermes", "heating-hermes"}
    healthy = {s["name"] for g in ensure.DESIRED for s in g["agents"]
               if g["label"] != "Herdr" and s["name"] not in independently_missing}
    healthy_before = healthy.copy()
    start_calls = []
    monkeypatch.setattr(ensure, "list_agents", lambda: [
        {"name": name, "interactive_ready": True, "agent_status": "idle"}
        for name in sorted(healthy)])

    def fake_run(args, timeout=30):
        if list(args)[:2] == [ensure.HERDR, "agent"] and "start" in args:
            name = args[args.index("start") + 1]
            start_calls.append(name)
            healthy.add(name)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(ensure, "run", fake_run)
    if fault == "herdr_agent_failure":
        original_ensure_agent = ensure.ensure_agent

        def failed_agent(wid, spec, group):
            if group["label"] == "Herdr":
                raise RuntimeError("private agent detail must not appear")
            return original_ensure_agent(wid, spec, group)

        monkeypatch.setattr(ensure, "ensure_agent", failed_agent)
    original = b'{"existing":"record"}\n{invalid json}\n'
    if fault == "corrupt_current":
        audit.write_bytes(original)
    elif fault == "corrupt_backup":
        (tmp_path / "audit.jsonl.1").write_bytes(original)
    elif fault == "enospc":
        def full_disk(*args):
            raise OSError(errno.ENOSPC, "private disk detail")
        monkeypatch.setattr(ensure.owner_guard, "_append_bounded_audit", full_disk)

    ensure.main()

    assert visited == [g["label"] for g in ensure.DESIRED
                       if not (fault == "herdr_checkout" and g["label"] == "Herdr")]
    assert set(start_calls) == independently_missing
    assert all(not name.startswith("herdr-") for name in start_calls)
    assert healthy_before <= healthy
    assert marker.read_bytes() == b"independent state unchanged\n"
    assert boot.read_bytes() == b"existing boot marker\n"
    if fault == "corrupt_current":
        assert audit.read_bytes() == original
    if fault == "corrupt_backup":
        assert (tmp_path / "audit.jsonl.1").read_bytes() == original
    output = capfd.readouterr()
    assert "private" not in output.out + output.err
    if fault != "herdr_checkout":
        assert "Herdr owner guard unavailable" in output.err


def test_g11_guard_log_failure_does_not_stop_other_consumers(
        guard, monkeypatch, tmp_path):
    ensure = load_module("ensure_g11_log", ENSURE_PATH)
    group = next(g for g in ensure.DESIRED if g["label"] == "Herdr")
    spec = group["agents"][0]
    monkeypatch.setattr(ensure.owner_guard, "collect_herdr_observation",
                        lambda *a, **k: obs_dict(guard, state="PAUSED"))
    monkeypatch.setattr(ensure, "GUARD_AUDIT_LOG", tmp_path / "audit.jsonl")
    monkeypatch.setattr(ensure, "log", lambda message: (_ for _ in ()).throw(
        OSError(errno.ENOSPC, "full")))
    assert ensure.ensure_agent("wid", spec, group) == guard.DECISION_BLOCKED_RECONCILIATION


def test_g11_herdr_block_is_isolated_from_other_consumers(guard, monkeypatch, tmp_path):
    ensure = load_module("ensure_g11", ENSURE_PATH)
    ensure.DESIRED = [
        {"label": "Majak", "cwd": "/tmp/majak", "agents": [
            {"tab": "Codex", "name": "majak-codex", "kind": "codex", "args": []},
            {"tab": "Hermes", "name": "majak-hermes", "kind": "hermes",
             "args": ["-p", "majak", "chat"]},
        ]},
        {"label": "Herdr", "cwd": "/tmp/herdr", "repository": "Bbambaaamm/herdr",
         "repo_url": "https://github.com/Bbambaaamm/herdr.git", "agents": [
            {"tab": "Codex", "name": "herdr-codex", "kind": "codex", "args": []},
            {"tab": "Hermes", "name": "herdr-hermes", "kind": "hermes",
             "args": ["-p", "quantlab", "chat"]},
        ]},
    ]
    started = set()
    calls = []
    monkeypatch.setattr(ensure, "STATE", tmp_path / "state")
    monkeypatch.setattr(ensure, "LOG", tmp_path / "ensure.log")
    monkeypatch.setattr(ensure, "GUARD_AUDIT_LOG", tmp_path / "audit.jsonl")
    ensure.STATE.mkdir(parents=True, exist_ok=True)
    seeded_state_marker = ensure.STATE / "seeded-majak-state.json"
    seeded_state_marker.write_text('{"consumer":"majak","marker":"untouched"}\n',
                                   encoding="utf-8")
    seeded_herdr_boot = tmp_path / "herdr-autostart.log"
    seeded_herdr_boot.write_text("majak-independent herdr boot marker\n",
                                 encoding="utf-8")
    seeded_dc_boot = tmp_path / "desktop-commander-autostart.log"
    seeded_dc_boot.write_text("majak-independent dc boot marker\n",
                              encoding="utf-8")
    monkeypatch.setattr(ensure, "HERDR_BOOT_LOG", seeded_herdr_boot)
    monkeypatch.setattr(ensure, "DC_BOOT_LOG", seeded_dc_boot)
    monkeypatch.setattr(ensure, "ensure_desktop_commander", lambda: None)
    monkeypatch.setattr(ensure, "ensure_herdr_server", lambda: None)
    monkeypatch.setattr(ensure, "ensure_repo_checkout", lambda *a: None)
    monkeypatch.setattr(ensure, "ensure_workspace", lambda label, cwd: "wid")
    monkeypatch.setattr(ensure, "ensure_tabs", lambda *a: None)
    monkeypatch.setattr(ensure, "list_agents", lambda: [
        {"name": name, "interactive_ready": True, "agent_status": "idle"}
        for name in started
    ])
    monkeypatch.setattr(ensure, "list_tabs", lambda: [
        {"workspace_id": "wid", "label": "Codex", "tab_id": "t1"},
        {"workspace_id": "wid", "label": "Hermes", "tab_id": "t2"},
    ])
    monkeypatch.setattr(ensure, "list_panes", lambda workspace_id: [
        {"tab_id": "t1", "pane_id": "p1"},
        {"tab_id": "t2", "pane_id": "p2"},
    ])
    monkeypatch.setattr(ensure.owner_guard, "collect_herdr_observation",
                        lambda *a, **k: obs_dict(guard, state="PAUSED"))

    def fake_run(args, timeout=30):
        calls.append(list(args))
        if "agent" in args and "start" in args:
            started.add(args[args.index("start") + 1])
        return ensure.subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(ensure, "run", fake_run)
    ensure.main()

    assert ensure.STATE == tmp_path / "state"
    assert ensure.STATE.is_dir()
    assert ensure.HERDR_BOOT_LOG.parent == tmp_path
    assert ensure.DC_BOOT_LOG.parent == tmp_path
    assert seeded_state_marker.read_text() == \
        '{"consumer":"majak","marker":"untouched"}\n'
    assert seeded_herdr_boot.read_text() == "majak-independent herdr boot marker\n"
    assert seeded_dc_boot.read_text() == "majak-independent dc boot marker\n"

    log_lines = (tmp_path / "ensure.log").read_text(encoding="utf-8").splitlines()
    assert any("=== ensure start ===" in line for line in log_lines)
    assert any("herdr-hermes: BLOCKED_RECONCILIATION_REQUIRED" in line
               for line in log_lines)
    assert not any("majak-" in line and ("BLOCKED_" in line or "owner_guard" in line)
                   for line in log_lines)

    audit_records = [json.loads(line) for line in
                     (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
                     if line.strip()]
    assert audit_records
    assert {record["consumer"] for record in audit_records} == {"Herdr"}
    assert all(record["operation"] == "agent.start" for record in audit_records)
    blocked_events = [record for record in audit_records
                      if record["event"] == guard.DECISION_BLOCKED_RECONCILIATION]
    assert len(blocked_events) >= 2

    assert "herdr-hermes" not in started
    assert "herdr-codex" not in started
    assert {"majak-codex", "majak-hermes"} <= started
    assert not any("herdr-" in call for call in calls
                   if "agent" in call and "start" in call)


@pytest.mark.parametrize("scenario,expected", [
    ("paused", "BLOCKED_RECONCILIATION_REQUIRED"),
    ("unknown", "BLOCKED_OWNER_UNKNOWN"),
    ("missing_policy", "BLOCKED_OWNER_UNKNOWN"),
    ("missing_native_root", "BLOCKED_OWNER_UNKNOWN"),
    ("missing_native_dir", "BLOCKED_OWNER_UNKNOWN"),
])
def test_g11_fake_cli_sandbox_isolates_consumers(guard, tmp_path, scenario, expected):
    """Real subprocess CLI: no Herdr starts for each uncertain host state."""
    ensure = load_module("ensure_g11_cli", ENSURE_PATH)
    cli = tmp_path / "herdr-fake"
    state_file = tmp_path / "fake-state.json"
    calls_file = tmp_path / "fake-calls.jsonl"
    cli.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "Path(os.environ['FAKE_CALLS']).open('a').write(json.dumps(args) + '\\n')\n"
        "state_path = Path(os.environ['FAKE_STATE'])\n"
        "state = json.loads(state_path.read_text()) if state_path.exists() else {'started': []}\n"
        "def emit(obj):\n"
        "    print(json.dumps(obj))\n"
        "if args[:2] == ['workspace', 'list']:\n"
        "    emit({'result': {'workspaces': [\n"
        "        {'workspace_id': 'w4', 'label': 'Majak'},\n"
        "        {'workspace_id': 'w4', 'label': 'Herdr'},\n"
        "    ]}})\n"
        "elif args[:2] == ['tab', 'list']:\n"
        "    emit({'result': {'tabs': [\n"
        "        {'workspace_id': 'w4', 'label': 'Codex', 'tab_id': 't1'},\n"
        "        {'workspace_id': 'w4', 'label': 'Hermes', 'tab_id': 't2'},\n"
        "    ]}})\n"
        "elif args[:2] == ['pane', 'list']:\n"
        "    emit({'result': {'panes': [\n"
        "        {'workspace_id': 'w4', 'tab_id': 't1', 'pane_id': 'p1'},\n"
        "        {'workspace_id': 'w4', 'tab_id': 't2', 'pane_id': 'p2'},\n"
        "    ]}})\n"
        "elif args[:2] == ['agent', 'list']:\n"
        "    emit({'result': {'agents': [\n"
        "        {'name': n, 'interactive_ready': True, 'agent_status': 'idle'}\n"
        "        for n in state.get('started', [])]}})\n"
        "elif 'start' in args:\n"
        "    name = args[args.index('start') + 1]\n"
        "    state.setdefault('started', []).append(name)\n"
        "    state_path.write_text(json.dumps(state))\n"
        "    print('')\n"
        "else:\n"
        "    print('')\n",
        encoding="utf-8",
    )
    os.chmod(cli, 0o755)
    ensure.HERDR = cli
    ensure.ENV = dict(ensure.ENV, FAKE_STATE=str(state_file), FAKE_CALLS=str(calls_file))
    ensure.DESIRED = [
        {"label": "Majak", "cwd": "/tmp/majak", "agents": [
            {"tab": "Codex", "name": "majak-codex", "kind": "codex", "args": []},
            {"tab": "Hermes", "name": "majak-hermes", "kind": "hermes",
             "args": ["-p", "majak", "chat"]}]},
        {"label": "Herdr", "cwd": "/tmp/herdr", "repository": "Bbambaaamm/herdr",
         "repo_url": "https://github.com/Bbambaaamm/herdr.git", "agents": [
            {"tab": "Codex", "name": "herdr-codex", "kind": "codex", "args": []},
            {"tab": "Hermes", "name": "herdr-hermes", "kind": "hermes",
             "args": ["-p", "quantlab", "chat"]}]},
    ]
    ensure.STATE = tmp_path / "state"
    ensure.LOG = tmp_path / "ensure.log"
    ensure.GUARD_AUDIT_LOG = tmp_path / "audit.jsonl"
    ensure.STATE.mkdir(parents=True, exist_ok=True)
    seeded_state_marker = ensure.STATE / "seeded-majak-state.json"
    seeded_state_marker.write_text('{"consumer":"majak","marker":"untouched"}\n',
                                   encoding="utf-8")
    seeded_herdr_boot = tmp_path / "herdr-autostart.log"
    seeded_herdr_boot.write_text("majak-independent herdr boot marker\n",
                                 encoding="utf-8")
    seeded_dc_boot = tmp_path / "desktop-commander-autostart.log"
    seeded_dc_boot.write_text("majak-independent dc boot marker\n",
                              encoding="utf-8")
    ensure.HERDR_BOOT_LOG = seeded_herdr_boot
    ensure.DC_BOOT_LOG = seeded_dc_boot
    ensure.ensure_desktop_commander = lambda: None
    ensure.ensure_herdr_server = lambda: None
    ensure.ensure_repo_checkout = lambda *args: None
    host = make_host(guard, tmp_path / "host", state="ERROR" if scenario == "unknown" else "PAUSED")
    if scenario == "missing_policy":
        (host["repo_root"] / "configs" / "consumers" / "herdr.yaml").unlink()
    elif scenario == "missing_native_root":
        shutil.rmtree(host["tasks_root"])
    elif scenario == "missing_native_dir":
        (host["tasks_root"] / "pending").rmdir()
    collector = ensure.owner_guard.collect_herdr_observation
    ensure.owner_guard.collect_herdr_observation = lambda agent_id, **kwargs: collector(
        agent_id, state_dir=host["state_dir"], repo_root=host["repo_root"],
        tasks_root=host["tasks_root"])

    ensure.main()
    assert (tmp_path / "state").is_dir()
    assert ensure.HERDR_BOOT_LOG.parent == tmp_path
    assert ensure.DC_BOOT_LOG.parent == tmp_path
    assert seeded_state_marker.read_text() == \
        '{"consumer":"majak","marker":"untouched"}\n'
    assert seeded_herdr_boot.read_text() == "majak-independent herdr boot marker\n"
    assert seeded_dc_boot.read_text() == "majak-independent dc boot marker\n"

    log_lines = (tmp_path / "ensure.log").read_text(encoding="utf-8").splitlines()
    assert any("=== ensure start ===" in line for line in log_lines)
    assert any(f"herdr-codex: {expected}" in line
               for line in log_lines)
    assert not any("majak-" in line and ("BLOCKED_" in line or "owner_guard" in line)
                   for line in log_lines)

    audit_records = [json.loads(line) for line in
                     (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
                     if line.strip()]
    assert audit_records
    assert {record["consumer"] for record in audit_records} == {"Herdr"}
    blocked_events = [record for record in audit_records
                      if record["event"] == expected]
    assert len(blocked_events) >= 2

    started = json.loads(state_file.read_text())["started"]
    assert "herdr-hermes" not in started
    assert "herdr-codex" not in started
    assert {"majak-codex", "majak-hermes"} <= set(started)
    start_calls = [json.loads(line) for line in calls_file.read_text().splitlines()
                   if "start" in json.loads(line)]
    assert not [call for call in start_calls if len(call) >= 3 and
                call[:2] == ["agent", "start"] and call[2].startswith("herdr-")]


# --------------------------------------------------------------------------
# G12: active release path is the deployment boundary
# --------------------------------------------------------------------------

def test_g12_real_active_release_path_and_nonactive_copy(guard):
    active = Path("/opt/herdr/current/agent-stack/bin/agent-stack-ensure")
    if not active.is_file():
        pytest.skip("active /opt/herdr/current release is host-specific")
    release_dir = Path("/opt/herdr/current").resolve()
    assert release_dir.is_dir()
    assert str(release_dir).startswith("/opt/herdr/releases/")

    expected = None
    for line in (release_dir / "MANIFEST.sha256").read_text(
            encoding="utf-8").splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[1].strip() == "agent-stack/bin/agent-stack-ensure":
            expected = parts[0]
    assert expected is not None
    active_sha = hashlib.sha256(active.read_bytes()).hexdigest()
    assert active_sha == expected

    # Owner-verified RC6 payload identity, pinned independently of the branch
    # manifest so a development checkout cannot masquerade as deployment.
    release_json = json.loads((release_dir / "RELEASE.json").read_text(encoding="utf-8"))
    assert release_json["tag"] == "v0.3.0-router-v5-p1d-rc6"
    assert release_json["commit"] == "8d8ad50375557b7ac77348e6475cb455682f4a9a"

    watchdog = (ROOT / "agent-stack" / "bin" / "agent-stack-watchdog").read_text(encoding="utf-8")
    assert 'BIN_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"' in watchdog
    assert 'ENSURE="$BIN_DIR/agent-stack-ensure"' in watchdog

    local = Path("/home/agentops/.local/bin/agent-stack-ensure")
    assert local.exists()
    assert local.resolve() != active.resolve()
    assert hashlib.sha256(local.resolve().read_bytes()).hexdigest() != active_sha

    # A guard-only command through a non-active copy must not deploy anything.
    before = hashlib.sha256(active.read_bytes()).hexdigest()
    decision = guard.evaluate_ownership(base_evidence(guard))
    after = hashlib.sha256(active.read_bytes()).hexdigest()
    assert decision.code == guard.DECISION_BLOCKED_RECONCILIATION
    assert before == after == active_sha


def test_scope_ensure_has_no_generic_resume_or_checkpoint_writer():
    source = ENSURE_PATH.read_text(encoding="utf-8").lower()
    assert "resume" not in source
    assert "--resume-reviewed" not in source
    assert "checkpoint.json" not in source

# Copilot follow-up: guard initialization and audit locking must not
# prevent independent consumers from continuing.
@pytest.mark.parametrize("broken_source", [None, "this is not python!\n",
                                           "raise RuntimeError('import exploded')\n"])
def test_guard_import_failure_is_isolated_to_herdr(tmp_path, broken_source, monkeypatch):
    folder = tmp_path / "agent-stack" / "bin"
    folder.mkdir(parents=True)
    fake_ensure = folder / "agent-stack-ensure"
    fake_ensure.write_bytes(ENSURE_PATH.read_bytes())
    if broken_source is not None:
        (folder / "agent_stack_owner_guard.py").write_text(broken_source)
    ensure = load_module("ensure_broken_guard", fake_ensure)
    assert ensure.owner_guard is None
    monkeypatch.setattr(ensure, "healthy_agent_names", lambda: {"majak-hermes"})
    monkeypatch.setattr(ensure, "log", lambda message: None)
    assert ensure.ensure_agent("irrelevant", {"name": "herdr-hermes"},
                               {"label": "Herdr"}) == "BLOCKED_OWNER_UNKNOWN"
    assert ensure.ensure_agent("irrelevant", {"name": "majak-hermes"},
                               {"label": "Majak"}) == "healthy"


def test_audit_lock_deadline_with_real_other_process(guard, tmp_path):
    import time
    audit = tmp_path / "audit.jsonl"
    sidecar = str(audit) + ".lock"
    script = ("import fcntl,os,sys,time; "
              "fd=os.open(sys.argv[1], os.O_RDWR|os.O_CREAT,0o600); "
              "fcntl.flock(fd,fcntl.LOCK_EX); "
              "print('LOCKED',flush=True); time.sleep(4)")
    holder = subprocess.Popen([sys.executable, "-c", script, sidecar],
                              stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "LOCKED"
        start = time.monotonic()
        with pytest.raises(guard.GuardObservationError) as e:
            _audit_once(guard, audit)
        elapsed = time.monotonic() - start
        assert e.value.reason == "audit_lock_timeout"
        assert 0.4 <= elapsed < 2.0
    finally:
        holder.terminate()
        holder.wait(timeout=3)


@pytest.mark.parametrize("state", ["STARTING", "RUNNING", "WAITING"])
@pytest.mark.parametrize("aux_status", ["MISSING", "UNREADABLE"])
def test_live_supervisor_needs_readable_auxiliary_fences(guard, state, aux_status):
    fences = {"supervisor.lock": "HELD", "cycle.lock": "FREE",
              "bootstrap.lock": aux_status}
    result = guard.evaluate_ownership(base_evidence(
        guard, decision_state=state, supervisor_alive=True, fence_states=fences))
    assert result.code == guard.DECISION_BLOCKED_UNKNOWN
    assert result.reason == "auxiliary_fence_unavailable"


def test_copilot_durable_child_blocker_is_visible_in_decision_and_audit(guard, tmp_path):
    host = make_host(
        guard, tmp_path, state="RUNNING",
        uncertain_blocked=[{"id": "parent-child", "repo": "Bbambaaamm/herdr",
                            "attempt_state": "result_ready",
                            "watchdog_blocker": "active_durable_children"}])
    audit = tmp_path / "owner-audit.jsonl"
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = guard.decide_herdr_agent_start(
            "Herdr", "Bbambaaamm/herdr", "herdr-hermes",
            state_dir=host["state_dir"], repo_root=host["repo_root"],
            tasks_root=host["tasks_root"], audit_path=audit)
    assert decision.code == guard.DECISION_BLOCKED_ATTEMPT
    assert "blocked/task-0.json" in decision.evidence.active_attempts
    record = json.loads(audit.read_text().splitlines()[-1])
    assert record["event"] == guard.DECISION_BLOCKED_ATTEMPT
    assert record["reason"] == "durable_active_attempt"


@pytest.mark.parametrize("changed", [
    {"consumer": "OtherConsumer"},
    {"repository": "other/repository"},
    {"observed_generation": "gen-old"},
    {"token": None},
    {"code": "BLOCKED_OWNER_UNKNOWN"},
])
def test_copilot_reservation_requires_exact_identity_generation_token_and_code(
    guard, tmp_path, changed
):
    from dataclasses import replace
    authority = FakeAtomicAuthority(tmp_path / "authority")
    evidence = interactive_evidence(guard)
    approved = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority)
    assert guard.plan_agent_start(evidence, approved) == "start"
    mismatched = replace(approved, **changed)
    assert guard.plan_agent_start(evidence, mismatched) == guard.DECISION_BLOCKED_UNKNOWN


def test_copilot_reservation_requires_matching_evidence_generation(guard, tmp_path):
    authority = FakeAtomicAuthority(tmp_path / "authority")
    approved = guard.reserve_interactive_start(
        "Herdr", "Bbambaaamm/herdr", "gen-1", "owner-token", authority=authority)
    from dataclasses import replace
    evidence = replace(interactive_evidence(guard), observed_generation="gen-2")
    assert guard.plan_agent_start(evidence, approved) == guard.DECISION_BLOCKED_UNKNOWN


@pytest.mark.parametrize("text_field", [
    "prompt", "last_error", "issue", "description",
])
def test_copilot_blocked_free_text_does_not_create_false_attempt(
    guard, tmp_path, text_field
):
    host = make_host(guard, tmp_path, state="RUNNING", uncertain_blocked=[{
        "id": "terminal-blocked", "repo": "Bbambaaamm/herdr",
        "attempt_state": "blocked", text_field: "unknown uncertain delivery",
    }])
    hits = guard._native_attempt_hits(host["tasks_root"], "Bbambaaamm/herdr")
    assert hits == ()
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_SKIPPED_SUPERVISOR_OWNED


@pytest.mark.parametrize("field,value", [
    ("attempt_state", "delivery_uncertain"),
    ("attempt_state", "terminal_unknown"),
    ("watchdog_blocker", "orphaned_running_unknown_delivery"),
    ("watchdog_blocker", "delivery_uncertain_requires_recovery"),
    ("watchdog_blocker", "active_durable_children"),
])
def test_copilot_structured_blocked_state_is_durable_attempt(
    guard, tmp_path, field, value
):
    host = make_host(guard, tmp_path, state="RUNNING", uncertain_blocked=[{
        "id": "held", "repo": "Bbambaaamm/herdr",
        "prompt": "ordinary work", field: value,
    }])
    with held_lock(host["state_dir"] / "supervisor.lock"):
        decision = _review_decide(guard, host, tmp_path / "audit.jsonl")
    assert decision.code == guard.DECISION_BLOCKED_ATTEMPT
    assert decision.evidence.active_attempts == ("blocked/task-0.json",)
