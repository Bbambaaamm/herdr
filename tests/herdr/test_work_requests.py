"""Actual oracle request, durable result and interruption without reexecution."""
from dataclasses import replace
from pathlib import Path
import json
import socket
import threading
import pytest

from herdr.evidence import digest
from herdr.security import PolicyDenied, RiskClass, ToolRule
from herdr.work_cycle import WorkContractError, WorkCycle, WorkPhase
from herdr.work_authority import WorkAuthorityClient, dispatch_work_connection
from herdr.work_contract_host import WorkInvocationGuard
from tests.herdr.test_work_authority import owner_for
from tests.herdr.test_work_contract_host import factory_fixture

def ready(tmp_path):
    factory, root, plan, grant, log = factory_fixture(tmp_path)
    rule = ToolRule("herdr_verify_work", RiskClass.READ, ("request_id",), requires_sandbox=True)
    grant = replace(grant, scope=replace(grant.scope, tools=(*grant.scope.tools, "herdr_verify_work")),
                    tool_rules=(*grant.tool_rules, rule))
    plan = replace(plan, grant_sha256=grant.hash)
    factory.approve = lambda **kwargs: plan
    factory.prepare(identity=plan.identity, workspace=root, grant=grant, spec_sha256=plan.spec_sha256)
    return factory, root, plan, grant, log

def test_actual_authenticated_oracle_pass_is_idempotent_and_ends_sdk_work(tmp_path, monkeypatch):
    factory, root, plan, grant, log = ready(tmp_path)
    (root/"result.py").write_text("def approved():\n    return 3\n\ndef foreign():\n    return 2\n")
    owner, observed = owner_for(factory, grant)
    owner.work_verify = factory.verify_request
    path = tmp_path/"oracle.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH", path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path)); listener.listen(4); listener.settimeout(5)
    errors = []
    def serve():
        try:
            for _ in range(5):
                connection, _ = listener.accept()
                assert dispatch_work_connection(owner, connection)
        except BaseException as exc: errors.append(exc)
    thread = threading.Thread(target=serve, daemon=True); thread.start()
    try:
        guard = WorkInvocationGuard(grant, work_authority=WorkAuthorityClient())
        first = guard.verify_work("verification-1")
        assert first["status"] == "pass" and first["tree_sha256"] == factory.cycle(plan.identity).verified_tree
        assert guard.verify_work("verification-1") == first
        with pytest.raises(PolicyDenied, match="work_phase"):
            guard.authorize_tool_call("read_file", {"path": str(root/"result.py")})
        thread.join(5)
        assert not thread.is_alive() and not errors
        assert len(observed) == 7  # Five admissions plus two post-oracle mount rechecks.
        events = [e["event"] for e in log.replay()]
        assert events.count("work_verification_requested") == events.count("work_check") == 1
        assert events.count("work_verification_finished") == events.count("work_pass") == 1
    finally:
        listener.close()
        if thread.is_alive(): thread.join(5)

def test_failed_oracle_does_not_reopen_build_or_admit_another_request(tmp_path):
    factory, root, plan, grant, log = ready(tmp_path)
    answer = factory.verify_request(plan.identity, grant.hash, "failed-1")
    assert answer["status"] == "failed" and answer["checks"][0]["exit_code"] == 1
    assert factory.verify_request(plan.identity, grant.hash, "failed-1") == answer
    with pytest.raises(WorkContractError): factory.verify_request(plan.identity, grant.hash, "retry-without-permit")
    assert factory.cycle(plan.identity).phase is WorkPhase.VERIFY
    with pytest.raises(PolicyDenied): factory.authorize_invocation(plan.identity, grant.hash, kind="provider")

def test_crash_after_verification_intent_keeps_unknown_and_cannot_rerun(tmp_path):
    factory, root, plan, grant, log = ready(tmp_path)
    cycle = factory.cycle(plan.identity)
    from herdr.work_cycle import tree_snapshot
    cycle._record("verification_requested", request_id="interrupted", tree_sha256=digest(tree_snapshot(root, git=factory.git)))
    recovered = WorkCycle(plan, root, log, git=factory.git)
    def never(*args): pytest.fail("unknown delivery must not execute again")
    assert recovered.request_verification("interrupted", never)["status"] == "unknown"
    with pytest.raises(WorkContractError): recovered.request_verification("rename-is-not-retry-authority", never)
    assert not recovered.implementation_allowed()

def test_foreign_grant_cannot_launch_oracle(tmp_path):
    factory, root, plan, grant, log = ready(tmp_path)
    before = log._path.read_bytes()
    with pytest.raises(WorkContractError):
        factory.verify_request(plan.identity, "f"*64, "foreign")
    assert log._path.read_bytes() == before
