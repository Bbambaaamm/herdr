from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from herdr.external_knowledge_tool import ARGUMENTS, TOOL
from herdr.runtime import HerdrChildRuntime
from herdr.scheduler import (
    AuditLog,
    ChildProposal,
    DynamicChildScheduler,
    LifecycleState,
)
from herdr.security import InvocationIdentity, RiskClass, ToolRule
from tests.herdr.test_security import grant


def fixture(tmp_path):
    scheduler = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "events.jsonl"))
    scheduler.register_external_parent_attempt(
        task_id="parent",
        run_token="parent-run",
        idempotency_key="parent-key",
        agent_name="parent-agent",
        pane_id="parent-pane",
        marker="parent-marker",
        repo="Example/project",
        issue="1",
        role="reader",
        tools=(TOOL,),
        permissions=(),
        policy_profile="default",
    )
    child = scheduler.delegate_child(
        "parent",
        "parent-run",
        "knowledge",
        ChildProposal(
            "reader",
            (TOOL,),
            "reader",
            (TOOL,),
            child_task="research",
        ),
    )
    lease = scheduler.dispatch(task_ids={child.id})[0]
    rec = scheduler._tasks[child.id]
    rec.fencing_token = lease.fencing_token
    rec.execution_agent = lease.agent_id
    rec.execution_pane = "child-pane"
    rec.execution_marker = "child-" + rec.run_token
    rec.execution_sandbox_verified = True
    rec.economic_delivery_attempted = True
    identity = InvocationIdentity(
        consumer="github:" + rec.repo,
        agent_id=lease.agent_id,
        parent_agent_id=rec.parent_agent_id,
        parent_task_id=rec.parent_task_id,
        task_id=rec.id,
        run_token=rec.run_token,
        fencing_token=lease.fencing_token,
    )
    rule = ToolRule(TOOL, RiskClass.READ, ARGUMENTS, requires_sandbox=True)
    item = replace(
        grant(tmp_path, tools=(TOOL,), providers=(), rules=(rule,)),
        identity=identity,
    )
    proof = {"invocation_policy": {"grant_sha256": item.hash}}
    runtime = SimpleNamespace(
        scheduler=scheduler,
        _policy_launches={rec.id: SimpleNamespace(grant=item)},
        _sandbox_proofs={"child-pane": proof},
    )
    return runtime, scheduler, rec, lease, item, identity


def allowed(runtime, item, identity):
    return HerdrChildRuntime._external_knowledge_child_authority(
        runtime, identity, item.hash, "provider", object()
    )


def test_child_external_knowledge_requires_exact_running_fenced_session(tmp_path):
    runtime, _scheduler, rec, lease, item, identity = fixture(tmp_path)
    assert allowed(runtime, item, identity)

    rec.fencing_token += 1
    assert not allowed(runtime, item, identity)
    rec.fencing_token = lease.fencing_token

    rec.state = LifecycleState.DONE
    assert not allowed(runtime, item, identity)
    rec.state = LifecycleState.RUNNING

    rec.economic_delivery_attempted = False
    assert not allowed(runtime, item, identity)


def test_child_external_knowledge_requires_live_lease_and_same_grant(tmp_path):
    runtime, scheduler, rec, lease, item, identity = fixture(tmp_path)
    assert allowed(runtime, item, identity)

    rec.lease = replace(lease, lease_until=scheduler.current_time() - 1)
    assert not allowed(runtime, item, identity)
    rec.lease = lease

    assert not HerdrChildRuntime._external_knowledge_child_authority(
        runtime, identity, "f" * 64, "provider", object()
    )

    runtime._sandbox_proofs["child-pane"]["invocation_policy"]["grant_sha256"] = "e" * 64
    assert not allowed(runtime, item, identity)
