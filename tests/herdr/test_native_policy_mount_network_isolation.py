"""Physical PolicyMount verification in an isolated network namespace.

Temporary signed-fixture source bytes, no root-owned release publication.
"""
from __future__ import annotations
import os
from pathlib import Path
import pytest
import subprocess
import sys

from tests.herdr.test_policy_launch import mount, cleanup

@pytest.mark.skipif(not Path("/usr/bin/bwrap").is_file(), reason="Bubblewrap unavailable")
def test_real_policy_mount_verify_mounted_with_separate_network(tmp_path):
    item = mount(tmp_path)
    descriptors = item.descriptors()
    net_host = os.readlink("/proc/self/ns/net")
    code = """
import os,sys,time
assert os.readlink('/proc/self/ns/net') != sys.argv[1]
print('MOUNT_NET_READY',flush=True)
time.sleep(5)
"""
    argv = [
        "/usr/bin/bwrap", "--ro-bind", "/", "/",
        "--unshare-user", "--unshare-pid", "--unshare-net",
        "--disable-userns", "--cap-drop", "ALL",
        "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", "/run",
        "--dir", "/run/herdr", "--dir", "/run/herdr-policy",
    ]
    for row in descriptors:
        argv.extend(["--ro-bind-fd", str(row["fd"]), row["target"]])
    argv += ["--", sys.executable, "-I", "-B", "-c", code, net_host]
    process = None
    try:
        process = subprocess.Popen(
            argv, pass_fds=tuple(item for item in (row["fd"] for row in descriptors)),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
        )
        line = process.stdout.readline()
        if not line:
            failure = process.stderr.read(1200)
            if "Operation not permitted" in failure or "Creating new namespace failed" in failure:
                pytest.skip("unprivileged namespaces disabled on test runner")
            pytest.fail(failure)
        assert line.strip() == "MOUNT_NET_READY", line
        # Bubblewrap starts an inner PID namespaced child. Verify its actual
        # /proc mount table and exact pinned inode identities, not a marker.
        children = Path(f"/proc/{process.pid}/task/{process.pid}/children").read_text().split()
        assert len(children) == 1, children
        child_pid = int(children[0])
        assert os.readlink(f"/proc/{child_pid}/ns/net") != net_host
        rows = item.verify_mounted(child_pid)
        assert all("ro" in rows[row["target"]] for row in descriptors)
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=6)
        cleanup(item)
