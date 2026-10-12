from __future__ import annotations

import os
import shutil
import socket
import subprocess
import threading
from pathlib import Path

import pytest


def test_physical_namespace_hides_provider_and_credentials_but_keeps_guarded_broker(
    tmp_path,
):
    """Physical proof of the external-knowledge credential/network boundary.

    This mirrors the relevant production namespace rule: /run and the worker
    HOME are private, and only the authenticated Herdr authority socket is
    reintroduced. The external provider daemon socket is deliberately not
    mounted into the worker.
    """
    bwrap = shutil.which("bwrap")
    if not bwrap:
        pytest.skip("bubblewrap unavailable")

    probe = subprocess.run(
        [bwrap, "--ro-bind", "/", "/", "--unshare-pid", "--", "/bin/true"],
        capture_output=True,
    )
    if probe.returncode:
        pytest.skip("host user namespace policy denies bubblewrap")

    host = tmp_path / "host"
    host.mkdir()
    credentials = host / ".azure"
    credentials.mkdir()
    (credentials / "marker").write_text("host-credential-marker")

    broker = host / "broker.sock"
    provider = host / "provider.sock"
    errors = []

    broker_listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    provider_listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        broker_listener.bind(str(broker))
        provider_listener.bind(str(provider))
        os.chmod(broker, 0o600)
        os.chmod(provider, 0o600)
        broker_listener.listen(1)
        broker_listener.settimeout(5)

        def serve_broker():
            try:
                connection, _ = broker_listener.accept()
                with connection:
                    assert connection.recv(64) == b"guarded-probe\n"
                    connection.sendall(b"guarded-ok\n")
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=serve_broker)
        thread.start()

        script = r"""
import os
import socket

assert not os.path.exists("/run/herdr-external-knowledge/provider.sock")
assert not os.path.exists("/home/agentops/.azure")
assert not os.path.exists("/home/agentops/.azure/marker")
assert os.path.exists("/run/herdr-policy/bootstrap-authority.sock")

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
    client.settimeout(5)
    client.connect("/run/herdr-policy/bootstrap-authority.sock")
    client.sendall(b"guarded-probe\n")
    assert client.recv(64) == b"guarded-ok\n"
"""
        result = subprocess.run(
            [
                bwrap,
                "--ro-bind", "/", "/",
                "--unshare-pid",
                "--unshare-net",
                "--tmpfs", "/run",
                "--dir", "/run/herdr-policy",
                "--dir", "/run/herdr-external-knowledge",
                "--tmpfs", "/home/agentops",
                "--ro-bind", str(broker), "/run/herdr-policy/bootstrap-authority.sock",
                "--",
                "/usr/bin/python3", "-I", "-c", script,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        thread.join(6)

        assert result.returncode == 0, result.stderr
        assert not thread.is_alive() and not errors
    finally:
        broker_listener.close()
        provider_listener.close()
