"""Physical private-network IPC with actual host dispatcher and PolicyMount verification.

Four pin sources are synthetic temporary immutable trees; no root-owned
HostBootstrap signature/continuation or child durable-result ACK claimed.
No providers, real credentials, root changes or model calls.
"""
import json
import os
from pathlib import Path
import pytest
import socket
import subprocess
import sys
import threading
import shutil
from types import SimpleNamespace

from herdr.bootstrap_authority import inspect_peer
from herdr.work_authority import dispatch_work_connection
from tests.herdr.test_work_contract_host import factory_fixture
from herdr.work_contract_host import HostWorkContractFactory
from test_work_cycle import seal
from tests.herdr.test_policy_launch import mount as synthetic_mount, cleanup

@pytest.mark.skipif(not Path("/usr/bin/bwrap").is_file(), reason="Bubblewrap unavailable")
def test_real_dispatch_with_actual_mount_verifier_across_netns(tmp_path):
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
    policy_mount = synthetic_mount(tmp_path)
    descriptors = policy_mount.descriptors()
    workspace_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    observed = []
    errors = []
    allow_called = []
    receipt = SimpleNamespace(peer_pid=None)
    def verify_mount(pid, sealed):
        # Use real PolicyMount verifier against /proc/<pid>/mountinfo;
        # sealed policy digest is intentionally checked by full bootstrap,
        # not this local unsiged synthetic bundle fixture.
        rows = policy_mount.verify_mounted(pid)
        assert all("ro" in rows[entry["target"]] for entry in descriptors)
        observed.append((pid, tuple(entry["inode"] for entry in descriptors)))
        return rows
    actual_mount = SimpleNamespace(verify_mounted=verify_mount)
    launch = SimpleNamespace(
        _published_bootstrap_receipt=receipt,
        mount=actual_mount, sealed=None,
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
from pathlib import Path
Path(sys.argv[5]).joinpath('result.py').write_text(
    'def approved():\\n    return 3\\n\\ndef foreign():\\n    return 2\\n')
print('REAL_HOST_DISPATCH_IPC_OK')
"""
    command = [
        "/usr/bin/bwrap", "--ro-bind", "/", "/",
        "--unshare-user", "--unshare-pid", "--unshare-net",
        "--disable-userns", "--cap-drop", "ALL",
        "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
        "--tmpfs", "/run", "--dir", "/run/herdr", "--dir", "/run/herdr-policy",
        *(argument for row in descriptors
          for argument in ("--ro-bind-fd", str(row["fd"]), row["target"])),
        "--ro-bind-fd", str(pinned), "/run/herdr-policy/bootstrap-authority.sock",
        "--bind-fd", str(workspace_fd), str(root),
        "--", sys.executable, "-I", "-B", "-c", child,
        str(Path(__file__).resolve().parents[2]),
        json.dumps(grant.identity.to_json()),
        os.readlink("/proc/self/ns/net"), grant.hash, str(root),
    ]
    try:
        result = subprocess.run(
            command, pass_fds=(pinned, workspace_fd, *(row["fd"] for row in descriptors)), capture_output=True,
            text=True, timeout=18,
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        thread.join(timeout=8)
        if result.returncode and (
            "Operation not permitted" in result.stderr
            or "Creating new namespace failed" in result.stderr
        ):
            pytest.skip("unprivileged namespaces disabled on test runner")
        assert result.returncode == 0, result.stderr[-1800:]
        assert "REAL_HOST_DISPATCH_IPC_OK" in result.stdout
        assert errors == []
        assert len(observed) >= 1
        assert allow_called == [("tool", "read_file")]
        cycle = factory.cycle(plan.identity)
        assert cycle.phase.value == "work"
        # A real sandbox child wrote the bounded workspace result. Continue
        # via the real host work-verification and persisted handoff ledger.
        assert (root / "result.py").read_text().startswith("def approved():\n    return 3")
        factory.verify(plan.identity)
        assert cycle.phase.value == "hygiene"
        artifact = seal(cycle, root, tmp_path)
        factory.before_completion(plan.identity, {
            "artifact_workspace": str(root),
            "artifact": artifact.to_json(),
        })
        cycle.handed_off("f" * 64)
        shutil.rmtree(root)
        recovered_factory = HostWorkContractFactory(
            approve=lambda **kw: (_ for _ in ()).throw(
                AssertionError("recovery must not replan")),
            environment=factory.environment, storage=factory.storage,
            audit_log=log,
        )
        recovered = recovered_factory.recover(
            identity=plan.identity, workspace=root,
            spec_sha256=plan.spec_sha256, grant_sha256=grant.hash,
            plan_sha256=plan.hash,
        )
        recovered.committed(artifact)
        recovered.handed_off("f" * 64)
        assert recovered.phase.value == "finished"
    finally:
        os.close(workspace_fd)
        os.close(pinned)
        listener.close()
        cleanup(policy_mount)
