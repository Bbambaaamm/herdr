"""Fixture-only actual WorkAuthorityClient across isolated network namespace."""
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading

from herdr.security import InvocationIdentity


def test_actual_work_authority_client_through_fd_pinned_socket(tmp_path):
    path = tmp_path / "authority.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    listener.listen(2)
    listener.settimeout(8)
    source_fd = os.open(path, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
    identity = InvocationIdentity(
        "github:Bbambaaamm/herdr", "network-probe-agent",
        "network-probe-parent", "network-probe-parent-task",
        "network-probe-task", "network-probe-run", 1,
    )
    received = []

    def host():
        try:
            with listener.accept()[0] as connection:
                connection.settimeout(4)
                raw = bytearray()
                while not raw.endswith(b"\n") and len(raw) < 8192:
                    data = connection.recv(1024)
                    if not data:
                        break
                    raw.extend(data)
                request = json.loads(raw)
                peer_pid, peer_uid, peer_gid = struct.unpack(
                    "3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
                )
                expected = {
                    "op": "work-authorize", "identity": identity.to_json(),
                    "grant_sha256": "a" * 64, "kind": "tool", "tool": "read_file",
                }
                received.append({
                    "equal": request == expected, "pid": peer_pid,
                    "uid": peer_uid, "gid": peer_gid,
                })
                connection.sendall(b"work-ok\n" if request == expected else b"denied\n")
        except BaseException as exc:
            received.append({"error": type(exc).__name__})

    thread = threading.Thread(target=host, daemon=True)
    thread.start()
    root = Path(__file__).resolve().parents[2]
    code = """
import json,os,sys,socket
sys.path.insert(0,sys.argv[1])
from herdr.security import InvocationIdentity
from herdr.work_authority import WorkAuthorityClient
identity=InvocationIdentity.from_dict(json.loads(sys.argv[2]))
assert WorkAuthorityClient()(identity, "a"*64, kind="tool", tool="read_file")
assert os.readlink("/proc/self/ns/net")!=sys.argv[3]
try:
    socket.create_connection(("127.0.0.1",int(sys.argv[4])),timeout=.4)
except OSError: pass
else: raise AssertionError("host TCP available")
print("WORK_AUTHORITY_ISOLATED_NETNS_PASS")
"""
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("127.0.0.1", 0))
    tcp.listen(1)
    tcp.settimeout(.5)
    command = [
        "/usr/bin/bwrap", "--ro-bind", "/", "/",
        "--unshare-user", "--unshare-pid", "--unshare-net",
        "--disable-userns", "--cap-drop", "ALL",
        "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
        "--tmpfs", "/run", "--dir", "/run/herdr-policy",
        "--ro-bind-fd", str(source_fd),
        "/run/herdr-policy/bootstrap-authority.sock",
        "--", sys.executable, "-I", "-B", "-c", code,
        str(root), json.dumps(identity.to_json()),
        os.readlink("/proc/self/ns/net"), str(tcp.getsockname()[1]),
    ]
    try:
        result = subprocess.run(
            command, pass_fds=(source_fd,), capture_output=True,
            text=True, timeout=16,
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        thread.join(timeout=8)
        assert result.returncode == 0, result.stderr[-1500:]
        assert "WORK_AUTHORITY_ISOLATED_NETNS_PASS" in result.stdout
        assert len(received) == 1 and received[0] == {
            "equal": True, "pid": received[0]["pid"],
            "uid": os.geteuid(), "gid": os.getegid(),
        }
        assert received[0]["pid"] > 0
        import pytest
        with pytest.raises(socket.timeout):
            tcp.accept()
    finally:
        os.close(source_fd)
        tcp.close()
        listener.close()
