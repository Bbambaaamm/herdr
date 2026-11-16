"""Physical private-network IPC with actual host-side dispatch_work_connection.

The mount verifier is an explicit fixture: this is NOT full root-owned
HostBootstrap or managed-child durable completion acceptance.
No providers, real credentials, root changes or model calls.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
from types import SimpleNamespace

from herdr.bootstrap_authority import inspect_peer
from herdr.work_authority import dispatch_work_connection
from tests.herdr.test_work_contract_host import factory_fixture

def test_actual_host_dispatch_with_real_process_identity_across_netns(tmp_path):
    factory, root, plan, grant, log = factory_fixture(tmp_path)
    factory.prepare(
        identity=grant.identity, workspace=root, grant=grant,
        spec_sha256=plan.spec_sha256,
    )
    endpoint = tmp_path / "broker.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(endpoint))
    listener.listen(2)
    listener.settimeout(8)
    pinned = os.open(endpoint, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
    observed = []
    errors = []
    allow_called = []
    receipt = SimpleNamespace(peer_pid=None)
    fake_mount = SimpleNamespace(
        verify_mounted=lambda pid, sealed: observed.append((pid, sealed)),
    )
    launch = SimpleNamespace(
        _published_bootstrap_receipt=receipt,
        mount=fake_mount, sealed="fixture-sealed",
        identity=grant.identity, grant=grant,
    )
    def phase_authority(identity, digest, *, kind, tool):
        allow_called.append((kind, tool))
        return factory.authorize_invocation(identity, digest, kind=kind, tool=tool)
    owner = SimpleNamespace(launch=launch, work_authority=phase_authority)

    def broker():
        try:
            conn, _ = listener.accept()
            peer_pid, peer_uid, peer_gid = __import__("struct").unpack(
                "3i", conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
            )
            assert peer_uid == os.geteuid()
            assert peer_gid == os.getegid()
            peer = inspect_peer(peer_pid)
            receipt.peer_pid = peer_pid
            receipt.process_start_ticks = peer.start_ticks
            receipt.python_device = peer.exe_device
            receipt.python_inode = peer.exe_inode
            assert dispatch_work_connection(owner, conn) is True
            invalid_conn, _ = listener.accept()
            assert dispatch_work_connection(owner, invalid_conn) is True
        except BaseException as exc:
            errors.append(repr(exc))

    thread = threading.Thread(target=broker, daemon=True)
    thread.start()
    child = """
import json,os,sys,socket
sys.path.insert(0,sys.argv[1])
from herdr.security import InvocationIdentity
from herdr.work_authority import WorkAuthorityClient
from herdr.security import PolicyDenied
identity=InvocationIdentity.from_dict(json.loads(sys.argv[2]))
assert os.readlink('/proc/self/ns/net') != sys.argv[3]
assert WorkAuthorityClient()(identity,sys.argv[4],kind='tool',tool='read_file')
try:
    WorkAuthorityClient()(identity,'f'*64,kind='tool',tool='read_file')
except PolicyDenied:
    pass
else:
    raise AssertionError('wrong signed grant was accepted')
print('REAL_HOST_DISPATCH_IPC_OK')
"""
    command = [
        "/usr/bin/bwrap", "--ro-bind", "/", "/",
        "--unshare-user", "--unshare-pid", "--unshare-net",
        "--disable-userns", "--cap-drop", "ALL",
        "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
        "--tmpfs", "/run", "--dir", "/run/herdr-policy",
        "--ro-bind-fd", str(pinned),
        "/run/herdr-policy/bootstrap-authority.sock",
        "--", sys.executable, "-I", "-B", "-c", child,
        str(Path(__file__).resolve().parents[2]),
        json.dumps(grant.identity.to_json()),
        os.readlink("/proc/self/ns/net"), grant.hash,
    ]
    try:
        result = subprocess.run(
            command, pass_fds=(pinned,), capture_output=True,
            text=True, timeout=18,
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        thread.join(timeout=8)
        assert result.returncode == 0, result.stderr[-1800:]
        assert "REAL_HOST_DISPATCH_IPC_OK" in result.stdout
        assert errors == []
        assert len(observed) >= 1
        assert allow_called == [("tool", "read_file")]
        assert factory.cycle(plan.identity).phase.value == "work"
    finally:
        os.close(pinned)
        listener.close()
