"""Actual peer-bound budget IPC and offline commit charged before effect."""
from dataclasses import replace
import os,socket,threading
import pytest
from herdr.evidence import digest
from herdr.work_authority import WorkAuthorityClient,dispatch_work_connection
from herdr.security import PolicyDenied
from herdr.work_budget import BudgetAllocation,BudgetLimits,WorkBudgetAuthority,BudgetedCheckRunner
from herdr.scheduler import AuditLog
from tests.herdr.test_work_authority import owner_for
from tests.herdr.test_work_budget_configuration import approved_factory,model_request
from tests.herdr.test_work_hygiene import boundary_workspace

def test_actual_unix_budget_peer_reserves_before_callback_and_reconciles_original(tmp_path,monkeypatch):
    factory,root,plan,grant,cycle,raw,allocation,quote=approved_factory(tmp_path)
    owner,observed=owner_for(factory,grant);owner.work_budget=factory.budget_effect
    path=tmp_path/"budget.sock";monkeypatch.setattr("herdr.work_authority.SOCKET_PATH",path)
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    listener.bind(str(path));listener.listen(4);listener.settimeout(5);os.chmod(path,0o600)
    errors=[]
    def serve():
        try:
            for _ in range(4):
                connection,_=listener.accept();assert dispatch_work_connection(owner,connection)
        except Exception as exc:errors.append(exc)
    thread=threading.Thread(target=serve);thread.start();client=WorkAuthorityClient()
    try:
        assert client.effect(grant.identity,grant.hash,"status",{})=={"required":True}
        receipt=client.effect(grant.identity,grant.hash,"start",model_request(quote))
        state=factory.budget_authority.snapshot(allocation.allocation_id)
        assert state["inflight"]==1 and state["charged_upper_bounds"]["model_calls"]==1
        with pytest.raises(PolicyDenied):
            client.effect(grant.identity,grant.hash,"start",model_request(quote,"renamed:1"))
        client.effect(grant.identity,grant.hash,"returned",{"operation_id":receipt["operation_id"]})
    finally:
        thread.join(5);listener.close()
    assert not thread.is_alive() and not errors
    assert factory.budget_authority.snapshot(allocation.allocation_id)["inflight"]==0
    assert len(observed)>=4

@pytest.mark.parametrize("changed_hook",[False,True])
def test_actual_hygiene_uses_existing_budget_and_never_reserves_second_commit(boundary_workspace,monkeypatch,changed_hook):
    import tests.herdr.test_work_hygiene as hygiene
    from tests.herdr.test_work_handoff import ready,committer_policy
    from herdr.check_runner import HostCheckRunner
    captured={}
    original=hygiene.factory_fixture
    def admitted(root):
        factory,workspace,plan,grant,log=original(root)
        allocation=BudgetAllocation(digest("hygiene-allocation"),grant.identity.consumer,digest("work"),
            digest("lineage"),digest("approval"),BudgetLimits(1000000,1000000,5,10000,1000,1,1,1,1))
        authority=WorkBudgetAuthority(audit_log=AuditLog(root/"host"/"budget.jsonl"),authorize=lambda **kw:allocation)
        factory.budget_authority=authority;factory.budget_binding=lambda **kw:allocation
        captured.update(authority=authority,allocation=allocation)
        return factory,workspace,replace(plan,budget_reference=allocation.hash),grant,log
    monkeypatch.setattr(hygiene,"factory_fixture",admitted)
    hook='found=0; while IFS= read -r row; do case "$row" in \'# formatted\') found=1;; esac; done < result.py; if [ "$found" = 0 ]; then printf \'\\n# formatted\\n\' >> result.py; fi' if changed_hook else "true"
    port,cycle,guard,result,task,plan,observations,log=ready(boundary_workspace,monkeypatch,hook=hook)
    authority,allocation=captured["authority"],captured["allocation"]
    port.budget_authority=authority;port.budget_allocation=allocation
    port.prepare_request(cycle,"original",{"pr_number":None})
    runner=BudgetedCheckRunner(authority,allocation,
        HostCheckRunner(committer_policy(port),boundary_workspace/"host"/"checks",git=cycle.git),"verification")
    outcome=cycle.request_verification("original",runner)
    if changed_hook:
        with pytest.raises(ValueError,match="invalidated"):port.complete(cycle,"original",outcome)
        assert authority.snapshot(allocation.allocation_id)["inflight"]==0
        with (cycle.root/"result.py").open("a") as stream:stream.write("\n# formatted\n")
        port.prepare_request(cycle,"reverified",{"pr_number":None})
        outcome=cycle.request_verification("reverified",runner)
    request="reverified" if changed_hook else "original"
    response=port.complete(cycle,request,outcome)
    before=authority.audit_log._path.read_bytes()
    assert port.complete(cycle,request,outcome)==response
    assert authority.audit_log._path.read_bytes()==before
    state=authority.snapshot(allocation.allocation_id)
    assert state["inflight"]==0 and state["implementation_attempts"]==1
    events=authority.audit_log.replay()
    hygiene_ops=[row for row in events if row.get("kind")=="reserve" and row.get("operation_kind")=="hygiene"]
    # The schema's authoritative event name is checked below.
    assert len([row for row in events if row.get("operation_kind")=="hygiene"])==(2 if changed_hook else 1)
