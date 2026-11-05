"""Component-only managed delivery: no native server, SDK, authority or provider.

The runtime method is real; launch/scheduler/runner boundaries are inert doubles.
The public CLI is loaded as a module and its validation functions are real.
"""
import ast
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import herdr.runtime as R
from herdr.child_evidence import ChildCompletionAuthority
from herdr.evidence import canonical, digest, validate_plan
from herdr.hermes_terminal_transport import (
    MAX_NATIVE_PROMPT_BYTES, encode_native_prompt,
)


ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "herdr/runtime.py").is_file():
    ROOT = Path(R.__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent-stack/bin"))
CLI_PATH = ROOT / "agent-stack/bin/agent-durable-child"
loader = importlib.machinery.SourceFileLoader("managed_prompt_cli", str(CLI_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
C = importlib.util.module_from_spec(spec)
loader.exec_module(C)


@pytest.fixture(autouse=True)
def deny_external_effects(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("component test attempted external execution or network")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(subprocess, "Popen", deny)


def plan_and_record():
    rec = SimpleNamespace(node=SimpleNamespace(id="child", objective="write child artifact",
        role="writer", tools=("write_file", "herdr_verify_work"), permissions=("workspace-write",)),
        run_token="a" * 32, idempotency_key="b" * 64, attempts=1, fencing_token=2,
        repo="Bbambaaamm/herdr", issue="78", parent_task_id="parent", parent_agent_id="parent-agent",
        parent_run_token="c" * 32, execution_sandbox_attestation=None, execution_agent="child-agent",
        execution_pane="pane-child", execution_marker="marker-child", execution_sandbox_verified=False,
        worktree_identity="", ownership=None)
    plan = {"version": 1, "identity": {"task_id": rec.node.id, "run_token": rec.run_token,
        "fencing_token": rec.fencing_token}, "repo": rec.repo, "kind": "coding",
        "spec_hash": "1" * 64, "policy_hash": "2" * 64, "base_sha": "3" * 40,
        "baseline": [], "workspace_root": "/synthetic/child", "required_checks": ["fixture-check"],
        "reviewer": "chatgpt-codex-connector[bot]", "environment": {}}
    plan["plan_hash"] = digest({k: v for k, v in plan.items() if k != "baseline"})
    validate_plan(plan)
    authority = object.__new__(ChildCompletionAuthority)
    authority.store = SimpleNamespace(read=Mock(return_value=plan))
    authority.modern_work = Mock(return_value=True)
    return plan, rec, authority


def full_prompt():
    plan, rec, authority = plan_and_record()
    business = "Produce the one declared child artifact and run the original host verification."
    header = C._delivery_prompt(business, Path("/unused/result"), rec.node.id,
        rec.run_token, rec.fencing_token, rec.idempotency_key)
    instructions = authority.instructions(rec)
    assert canonical(plan).decode() in instructions
    return header + instructions, plan


def test_original_composed_1200_gate_is_red_for_valid_complete_plan():
    text, plan = full_prompt()
    assert len(text) > R.MAX_PROMPT_CHARS == 1200
    with pytest.raises(ValueError, match="old gate"):
        if len(text) > 1200:
            raise ValueError("old gate rejects the valid frozen plan")
    framed = R._managed_prompt_transport(text, modern=True)
    assert framed == encode_native_prompt(text)
    assert framed[6:-6] == text
    assert canonical(plan).decode() in framed
    assert framed.count("\x1b[200~") == framed.count("\x1b[201~") == 1


@pytest.mark.parametrize("text", ["x" * (65536 - 12), "é" * ((65536 - 12) // 2),
    "漢" * ((65536 - 12) // 3), "ok\n\tUnicode 🧪"])
def test_modern_actual_utf8_envelope_bound_and_exact_preservation(text):
    result = R._managed_prompt_transport(text, modern=True)
    assert result == encode_native_prompt(text)
    assert result[6:-6] == text
    assert len(result.encode("utf-8")) <= MAX_NATIVE_PROMPT_BYTES


@pytest.mark.parametrize("text", ["x" * (65536 - 11), "é" * (65536 // 2),
    "bad\x1b[200~", "bad\r", "bad\x00", "bad\x7f", "bad\ud800", ""])
def test_invalid_composed_payload_denied_by_original_encoder(text):
    with pytest.raises(Exception):
        R._managed_prompt_transport(text, modern=True)


def test_legacy_remains_raw_1200_and_mode_is_typed():
    text = "x" * 1200
    assert R._managed_prompt_transport(text, modern=False) == text
    with pytest.raises(R.HerdrRuntimeError):
        R._managed_prompt_transport(text + "x", modern=False)
    with pytest.raises(R.HerdrRuntimeError):
        R._managed_prompt_transport(text, modern=1)


def cli_preflight(monkeypatch, tmp_path):
    constructor = Mock(return_value=SimpleNamespace(_tasks={}, _next_fencing_token_value=1,
        budget=SimpleNamespace(max_dag_nodes=256)))
    monkeypatch.setattr(C, "DynamicChildScheduler", constructor)
    monkeypatch.setattr(C, "AuditLog", lambda path: ("inert-audit", path))
    monkeypatch.setattr(C, "ledger_required", lambda directory: False)
    return constructor


def test_business_1200_accepted_modern_1201_denied_before_any_scheduler(monkeypatch, tmp_path):
    constructor = cli_preflight(monkeypatch, tmp_path)
    C._validate_delivery_prompt("x" * 1200, tmp_path, "child", modern=True)
    assert constructor.call_count == 1
    constructor.reset_mock()
    with pytest.raises(ValueError, match="business prompt"):
        C._validate_delivery_prompt("x" * 1201, tmp_path, "child", modern=True)
    constructor.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_actual_delegate_rejects_business_1201_before_state_path(monkeypatch):
    forbidden = Mock(side_effect=AssertionError("state path must not be touched"))
    monkeypatch.setattr(C, "_required_env", forbidden)
    args = SimpleNamespace(key="one-child", objective="write artifact", prompt="x" * 1201)
    with pytest.raises(ValueError, match="business prompt"):
        C._delegate_pinned(args, None, "", {"id": "parent", "run_token": "a" * 32},
            "", "", "", SimpleNamespace(logical=Path("/synthetic/child")))
    forbidden.assert_not_called()


def test_legacy_preview_includes_header_and_replay_fence(monkeypatch, tmp_path):
    constructor = cli_preflight(monkeypatch, tmp_path)
    C._validate_delivery_prompt("small", tmp_path, "child")
    with pytest.raises(ValueError, match="managed child prompt exceeds maximum length"):
        C._validate_delivery_prompt("x" * 1200, tmp_path, "child")
    existing = SimpleNamespace(run_token="r" * 32, idempotency_key="k" * 64, fencing_token=999)
    scheduler = constructor.return_value
    scheduler._tasks["child"] = existing
    C._validate_delivery_prompt("x" * 1200, tmp_path, "child", modern=True)
    assert list(tmp_path.iterdir()) == []


def runtime_fixture(monkeypatch, *, modern=True, runner_error=None, intent=True):
    events = []
    _, rec, authority = plan_and_record()
    rec.ownership = None
    authority.modern_work = Mock(return_value=modern)
    authority.prepare = Mock(side_effect=lambda record: events.append("completion-prepare"))
    authority.preflight_work = Mock(side_effect=lambda record, launch: events.append("work-preflight"))
    authority.prepare_work = Mock(return_value=None)
    class Launch:
        private_profile_snapshot = SimpleNamespace(name="quantlab")
        def environment(self): return {}
        def verify_spawn_source(self, observer): events.append("source")
        def set_continuation_sink(self, sink): self.sink = sink
        def arm_bootstrap(self): events.append("arm")
        def confirm_bootstrap(self): return {"test-only": True}
        def verify_bootstrap(self): events.append("bootstrap")
    class Factory:
        approved_profile = SimpleNamespace(name="quantlab")
        def prepare_child(self, **kwargs):
            events.append("launch-prepare")
            result = Launch()
            result.identity = kwargs["identity"]
            return result
    monkeypatch.setattr(R, "HostPolicyLaunchFactory", Factory)
    monkeypatch.setattr(R, "PreparedPolicyLaunch", Launch)
    scheduler = SimpleNamespace(_tasks={"child": rec}, completion_authority=authority,
        budget=SimpleNamespace(claim_ttl_seconds=60),
        task_node=lambda task_id: rec.node, task_context=lambda task_id: {"repo": rec.repo},
        current_time=lambda: 0.0)
    for name in ("record_child_pane_intent", "mark_child_split_started", "bind_pre_delivery_pane",
        "attest_execution_sandbox", "bind_execution_session", "authorize_child_delivery",
        "mark_pre_delivery_agent_start", "observe_execution", "mark_pre_delivery_cleanup_complete"):
        setattr(scheduler, name, Mock(side_effect=lambda *a, _n=name, **k: events.append(_n) or True))
    scheduler.mark_child_delivery_started = Mock(side_effect=lambda *a: events.append("delivery-intent") or intent)
    scheduler.fail_child_pre_delivery = Mock(side_effect=lambda *a, **k: events.append("failure-audit") or True)
    def run(args, **kwargs):
        events.append("prompt")
        if runner_error: raise runner_error
        return R.CommandResult(0, "{}", "")
    runtime = object.__new__(R.HerdrChildRuntime)
    runtime.scheduler = scheduler
    runtime.runner = SimpleNamespace(executable="/synthetic/herdr", run=Mock(side_effect=run))
    runtime.env = {}
    runtime.cwd = Path("/synthetic/child")
    runtime.policy_launch_factory = Factory()
    runtime.pinned_worktree = None
    runtime._policy_launches = {}
    runtime._owned_write_pins = {}
    runtime._reservation_panes = {}
    runtime._managed_launch_panes = set()
    runtime._sandbox_proofs = {"pane-child": {"sandbox_pid": 123, "policy_sha256": "a" * 64,
        "invocation_policy": {"test-only": True}}}
    runtime.prepare = Mock(side_effect=lambda: events.append("runtime-prepare"))
    runtime._admit_child = Mock(side_effect=lambda lease: events.append("admit"))
    runtime._prepare_private_child_command = Mock()
    runtime._create_pane = Mock(return_value="pane-child")
    runtime._sandbox_child_pane = Mock(return_value=SimpleNamespace(unlink=lambda **kwargs: None))
    runtime._start_agent = Mock(side_effect=lambda *a: events.append("start"))
    runtime._verify_live_child = Mock(return_value="idle")
    runtime._cleanup_policy_launch = Mock()
    runtime.cleanup_managed_pre_delivery = Mock()
    runtime.admission_registry = SimpleNamespace(release=Mock())
    lease = SimpleNamespace(task_id="child", agent_id="child-agent", fencing_token=2)
    return runtime, lease, scheduler, events


def test_actual_runtime_sends_one_exact_modern_frame_after_intent(monkeypatch):
    runtime, lease, scheduler, events = runtime_fixture(monkeypatch)
    text, _ = full_prompt()
    assert runtime.run_managed_child(lease, text, run_token="a" * 32, idempotency_key="b" * 64) == "settled"
    runtime.runner.run.assert_called_once()
    argv = runtime.runner.run.call_args.args[0]
    assert argv[:3] == ["agent", "prompt", "child-agent"]
    assert argv[3] == encode_native_prompt(text)
    assert argv[3][6:-6] == text
    assert events.index("delivery-intent") < events.index("prompt")
    assert events.count("start") == events.count("prompt") == 1


@pytest.mark.parametrize("text", ["x" * 65525, "bad\r", "bad\x1b", "bad\ud800"])
def test_actual_runtime_denies_bad_composed_input_before_any_start_or_intent(monkeypatch, text):
    runtime, lease, scheduler, events = runtime_fixture(monkeypatch)
    with pytest.raises(R.PreDeliveryFailure):
        runtime.run_managed_child(lease, text, run_token="a" * 32, idempotency_key="b" * 64)
    assert events == ["failure-audit", "mark_pre_delivery_cleanup_complete"]
    scheduler.record_child_pane_intent.assert_not_called()
    runtime.prepare.assert_not_called()
    runtime.policy_launch_factory  # an inert double, never called
    runtime._create_pane.assert_not_called()
    runtime._start_agent.assert_not_called()
    runtime.runner.run.assert_not_called()


def test_actual_runtime_legacy_delivery_stays_raw(monkeypatch):
    runtime, lease, _, _ = runtime_fixture(monkeypatch, modern=False)
    runtime.run_managed_child(lease, "legacy", run_token="a" * 32, idempotency_key="b" * 64)
    assert runtime.runner.run.call_args.args[0][3] == "legacy"


def test_intent_denial_and_lost_ack_never_retry_prompt(monkeypatch):
    runtime, lease, _, events = runtime_fixture(monkeypatch, intent=False)
    with pytest.raises(R.PreDeliveryFailure):
        runtime.run_managed_child(lease, "modern", run_token="a" * 32, idempotency_key="b" * 64)
    runtime.runner.run.assert_not_called()
    runtime, lease, scheduler, events = runtime_fixture(monkeypatch, runner_error=TimeoutError("dummy lost ack"))
    with pytest.raises(TimeoutError):
        runtime.run_managed_child(lease, "modern", run_token="a" * 32, idempotency_key="b" * 64)
    runtime.runner.run.assert_called_once()
    scheduler.mark_child_delivery_started.assert_called_once()
    scheduler.fail_child_pre_delivery.assert_not_called()
    assert events.count("prompt") == 1


def test_all_cli_projection_seams_and_plain_prompt_binding_are_explicit():
    tree = ast.parse(CLI_PATH.read_text())
    delegate = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_delegate_pinned")
    helper_calls = [n for n in ast.walk(delegate) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == "_managed_prompt_transport"]
    assert len(helper_calls) == 2  # locked preview, then complete frozen instructions
    assert all(isinstance(n, ast.Expr) for n in ast.walk(delegate)
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
        and n.value in helper_calls)
    bind = next(n for n in ast.walk(delegate) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "bind_child_prompt")
    assert isinstance(bind.args[1], ast.Name) and bind.args[1].id == "delivery_prompt"
    delivered = next(n for n in ast.walk(delegate) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "run_managed_child")
    assert isinstance(delivered.args[1], ast.Name) and delivered.args[1].id == "delivery_prompt"



def run_actual_composed_cli_block(monkeypatch, *, newly_claimed=True, oversized=False):
    """Execute the exact final composition/delivery block, with inert boundaries.

    Earlier admission/claim logic is not executed or represented as verified.
    This checks that the final frozen plan is validated before binding/start,
    and that a replay cannot call the runtime a second time.
    """
    tree = ast.parse(CLI_PATH.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_delegate_pinned")
    parent_guard = next(n for n in function.body if isinstance(n, ast.With))
    body = parent_guard.body
    start = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "delivery_prompt" for t in n.targets))
    stop = next(i for i, n in enumerate(body[start:], start) if isinstance(n, ast.If)
        and ast.unparse(n.test).startswith("rec.result_evidence_canonical"))
    plan, rec, authority = plan_and_record()
    if oversized:
        plan["environment"] = {"synthetic-long-field": "x" * 65536}
        plan["plan_hash"] = digest({k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}})
        validate_plan(plan)
    authority.prepare = Mock()
    events = []
    fake_runtime = SimpleNamespace(run_managed_child=Mock(side_effect=lambda *a, **k: events.append("run")))
    constructor = Mock(return_value=fake_runtime)
    scheduler = SimpleNamespace(completion_authority=authority,
        bind_child_prompt=Mock(side_effect=lambda *a: events.append("bind")))
    args = SimpleNamespace(prompt="Produce the one declared child artifact and run the original host verification.")
    env = dict(vars(C))
    env.update(args=args, result_path=Path("/unused/result"), child=SimpleNamespace(id="child"),
        rec=rec, scheduler=scheduler, newly_claimed=newly_claimed, runner=object(),
        child_cwd=Path("/synthetic/child"), pinned=object(), policy_launch_factory=object(),
        directory=Path("/synthetic/attempt"), pane="parent-pane",
        task={"safety_profile": "quantlab"}, HerdrChildRuntime=constructor,
        AdmissionRegistry=Mock(return_value=object()))
    rec.lease = object()
    execute = lambda: exec(compile(ast.Module(body=body[start:stop], type_ignores=[]),
        str(CLI_PATH), "exec"), env)
    return execute, scheduler, constructor, fake_runtime, events, plan


def test_actual_final_cli_block_preserves_full_plan_and_plain_binding(monkeypatch):
    execute, scheduler, constructor, runtime, events, plan = run_actual_composed_cli_block(monkeypatch)
    execute()
    assert events == ["bind", "run"]
    constructor.assert_called_once()
    runtime.run_managed_child.assert_called_once()
    bound = scheduler.bind_child_prompt.call_args.args[1]
    assert len(bound) > 1200
    assert canonical(plan).decode() in bound
    assert "\x1b" not in bound
    assert runtime.run_managed_child.call_args.args[1] == bound


def test_actual_final_cli_block_denies_oversized_frozen_plan_before_binding_or_start(monkeypatch):
    execute, scheduler, constructor, runtime, events, _ = run_actual_composed_cli_block(monkeypatch, oversized=True)
    with pytest.raises(Exception):
        execute()
    assert events == []
    scheduler.bind_child_prompt.assert_not_called()
    constructor.assert_not_called()
    runtime.run_managed_child.assert_not_called()


def test_actual_final_cli_replayed_claim_never_starts_runtime(monkeypatch):
    execute, scheduler, constructor, runtime, events, _ = run_actual_composed_cli_block(monkeypatch, newly_claimed=False)
    execute()
    assert events == ["bind"]
    constructor.assert_not_called()
    runtime.run_managed_child.assert_not_called()
