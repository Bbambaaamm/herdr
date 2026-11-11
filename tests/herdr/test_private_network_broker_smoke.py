"""Physical proof of pathname Unix broker across a separately isolated netns.

Fixture-only: a private socket and a local TCP listener, never a real host
broker, production grant, credential, provider or work queue.
"""
from __future__ import annotations

import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading

import pytest


@pytest.mark.skipif(not Path("/usr/bin/bwrap").is_file(), reason="bwrap unavailable")
def test_isolated_netns_preserves_exact_pinned_unix_broker_and_denies_tcp(tmp_path):
    source = tmp_path / "s"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(source))
    listener.listen(1)
    listener.settimeout(6)
    fd = os.open(source, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("127.0.0.1", 0))
    tcp.listen(1)
    tcp.settimeout(2)
    port = tcp.getsockname()[1]
    messages = []

    def serve():
        try:
            client, _ = listener.accept()
            with client:
                payload = client.recv(80)
                peer = client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
                messages.append((payload, peer))
                client.sendall(b"BROKER_AUTH_TEST_OK")
        except Exception as exc:
            messages.append((type(exc).__name__, b""))

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    child = '''
import os,socket,subprocess,sys
c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
c.settimeout(3)
c.connect("/run/herdr-policy/bootstrap-authority.sock")
c.sendall(b"PINNED_FD_TEST_ONLY")
assert c.recv(80)==b"BROKER_AUTH_TEST_OK"
c.close()
def connect_tcp():
    x=socket.create_connection(("127.0.0.1",PORT),timeout=.5)
    x.close()
    raise AssertionError("unexpected host TCP access")
try:
    connect_tcp()
except OSError:
    pass
grandchild=subprocess.run([sys.executable,"-I","-B","-c",
    "import socket;socket.create_connection(('127.0.0.1',PORT),timeout=.5)"],
    capture_output=True,timeout=3)
assert grandchild.returncode!=0, "child subprocess reached TCP"
assert os.readlink("/proc/self/ns/net")!=HOST_NET
print("PINNED_UNIX_BROKER_ACROSS_NETNS_PASS")
'''.replace("PORT", str(port)).replace("HOST_NET", repr(os.readlink("/proc/self/ns/net")))
    args = [
        "/usr/bin/bwrap", "--ro-bind", "/", "/", "--unshare-net",
        "--unshare-pid", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
        "--tmpfs", "/run", "--dir", "/run/herdr-policy",
        "--ro-bind-fd", str(fd), "/run/herdr-policy/bootstrap-authority.sock",
        "--", sys.executable, "-I", "-B", "-c", child,
    ]
    try:
        process = subprocess.run(
            args, pass_fds=(fd,), capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=15,
        )
        worker.join(timeout=6)
        assert process.returncode == 0, process.stderr[-1200:]
        assert "PINNED_UNIX_BROKER_ACROSS_NETNS_PASS" in process.stdout
        assert len(messages) == 1 and messages[0][0] == b"PINNED_FD_TEST_ONLY"
        peer_pid, peer_uid, peer_gid = struct.unpack("3i", messages[0][1])
        # Host listener observes the originating UID and a real child PID,
        # even when the worker runs in an isolated network namespace.
        assert peer_pid > 0 and peer_uid == os.geteuid() and peer_gid == os.getegid()
        tcp.settimeout(.3)
        with pytest.raises(socket.timeout):
            tcp.accept()
    finally:
        os.close(fd)
        listener.close()
        tcp.close()
