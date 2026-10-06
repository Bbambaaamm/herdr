"""Real Unix peer credentials and durable host phase, without provider calls."""
import json
import os
import socket
import struct
import threading
from types import SimpleNamespace
import pytest

from herdr.bootstrap_authority import inspect_peer
from herdr.work_authority import WorkAuthorityClient, dispatch_work_connection
from herdr.work_contract_host import HostWorkContractFactory, WorkInvocationGuard
from herdr.security import PolicyDenied, ProviderRequest
from herdr.capability import DataClass,Egress,Retention,Training
from tests.herdr.test_work_contract_host import factory_fixture

def owner_for(factory,grant):
    peer=inspect_peer(os.getpid())
    receipt=SimpleNamespace(peer_pid=peer.pid,process_start_ticks=peer.start_ticks,
                            python_device=peer.exe_device,python_inode=peer.exe_inode)
    observed=[]
    # The mount port is explicit here; real physical verification is tested by
    # the installed bootstrap probe and namespace suite, never a model marker.
    mount=SimpleNamespace(verify_mounted=lambda pid,sealed:observed.append((pid,sealed)))
    launch=SimpleNamespace(_published_bootstrap_receipt=receipt,mount=mount,sealed="sealed-fixture",
                           identity=grant.identity,grant=grant)
    return SimpleNamespace(launch=launch,work_authority=factory.authorize_invocation),observed

def test_actual_ipc_guard_stops_after_pass_recorded_by_another_host_entry_point(tmp_path,monkeypatch):
    factory,root,plan,grant,log=factory_fixture(tmp_path)
    factory.prepare(identity=grant.identity,workspace=root,grant=grant,spec_sha256=plan.spec_sha256)
    owner,observed=owner_for(factory,grant)
    path=tmp_path/"authority.sock"
    monkeypatch.setattr("herdr.work_authority.SOCKET_PATH",path)
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(path));listener.listen(4);listener.settimeout(5)
    os.chmod(path,0o600);errors=[]
    def server():
        try:
            for _ in range(3):
                connection,_=listener.accept()
                assert dispatch_work_connection(owner,connection)
        except BaseException as exc:errors.append(exc)
    thread=threading.Thread(target=server,daemon=True);thread.start()
    try:
        guard=WorkInvocationGuard(grant,work_authority=WorkAuthorityClient())
        request=ProviderRequest("provider-a","eu-central",DataClass.INTERNAL,Egress.REGION_BOUND,
                                Retention.LIMITED,Training.EXCLUDED)
        guard.authorize_provider(request)
        (root/"result.py").write_text("def approved():\n    return 3\n\ndef foreign():\n    return 2\n")
        separate=HostWorkContractFactory(approve=factory.approve,environment=factory.environment,
            storage=factory.storage,audit_log=log,git=factory.git)
        separate.recover(identity=plan.identity,workspace=root,spec_sha256=plan.spec_sha256,
                         grant_sha256=grant.hash,plan_sha256=plan.hash)
        separate.verify(plan.identity)
        with pytest.raises(PolicyDenied,match="work_phase"):guard.authorize_provider(request)
        with pytest.raises(PolicyDenied,match="work_phase"):
            guard.authorize_tool_call("read_file",{"path":str(root/"result.py")})
        thread.join(5)
        assert not thread.is_alive() and not errors
        assert len(observed)==3
        assert factory.cycle(plan.identity).phase.value=="hygiene"
    finally:
        listener.close()
        if thread.is_alive():thread.join(5)

def test_changed_identity_on_real_peer_is_denied_without_host_phase_or_effect(tmp_path):
    factory,root,plan,grant,log=factory_fixture(tmp_path)
    factory.prepare(identity=grant.identity,workspace=root,grant=grant,spec_sha256=plan.spec_sha256)
    owner,observed=owner_for(factory,grant)
    original=log._path.read_bytes()
    left,right=socket.socketpair()
    identity=grant.identity.to_json();identity["run_token"]="foreign"
    right.sendall(json.dumps({"op":"work-authorize","identity":identity,"grant_sha256":grant.hash,
                             "kind":"provider","tool":None}).encode()+b"\n")
    assert dispatch_work_connection(owner,left)
    assert right.recv(128)==b"denied\n"
    right.close()
    assert log._path.read_bytes()==original and len(observed)==1

def test_irrelevant_uid_retains_connection_for_original_bootstrap_broker(tmp_path):
    factory,root,plan,grant,log=factory_fixture(tmp_path)
    owner,_=owner_for(factory,grant)
    left,right=socket.socketpair()
    class ForeignUid:
        closed=False
        def getsockopt(self,*args):return struct.pack("3i",os.getpid(),os.geteuid()+1,os.getegid())
        def close(self):self.closed=True;left.close()
    connection=ForeignUid()
    try:
        assert dispatch_work_connection(owner,connection) is False
        assert not connection.closed
        left.sendall(b"original-broker-still-owns-connection")
        assert right.recv(128)==b"original-broker-still-owns-connection"
    finally:left.close();right.close()


@pytest.mark.parametrize("budgeted",[True,False])
def test_actual_peer_request_ceiling_requires_a_bound_host_budget(tmp_path,budgeted):
    from tests.herdr.test_work_budget_configuration import approved_factory
    factory,root,plan,grant,cycle,raw,allocation,quote=approved_factory(tmp_path)
    owner,observed=owner_for(factory,grant)
    if budgeted:owner.work_budget=factory.budget_effect
    route={key:quote[key] for key in ("provider","model","api_mode","base_url")}
    original=factory.budget_authority.audit_log._path.read_bytes()
    left,right=socket.socketpair()
    try:
        right.sendall(json.dumps({"op":"work-budget","identity":grant.identity.to_json(),
            "grant_sha256":grant.hash,"action":"ceiling","payload":route}).encode()+b"\n")
        assert dispatch_work_connection(owner,left)
        response=right.recv(8192)
        if budgeted:
            assert json.loads(response)=={"output_token_field":"max_tokens","max_output_tokens":100}
            assert len(observed)==2
        else:
            assert response==b"denied\n" and len(observed)==1
        assert factory.budget_authority.audit_log._path.read_bytes()==original
    finally:
        left.close();right.close()
