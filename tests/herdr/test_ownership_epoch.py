"""Real kernel flock/process custody regressions, without production changes."""
import fcntl
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import pytest
from herdr.child_ownership import OwnershipError
from herdr.ownership_epoch import custodial_command, legacy_admission_guard
from herdr.ownership_inventory import LegacyOwnershipInventory


def ready(process):
    assert select.select([process.stdout], [], [], 5)[0], "custodian did not become ready"
    line = process.stdout.readline()
    assert line.startswith("READY"), line
    return line


def dead(pid):
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError):
        return True
    return raw.split(") ", 1)[1].split()[0] == "Z"


def wait_dead(pids):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if all(dead(pid) for pid in pids):
            return
        time.sleep(.02)
    assert all(dead(pid) for pid in pids)


def descendants(pid):
    found = []
    todo = [pid]
    while todo:
        current = todo.pop()
        try:
            children = [int(x) for x in Path(f"/proc/{current}/task/{current}/children").read_text().split()]
        except FileNotFoundError:
            children = []
        found.extend(children)
        todo.extend(children)
        assert len(found) <= 32
    return found


def test_preopened_legacy_fd_cannot_admit_after_coordinator_exit(tmp_path):
    path = tmp_path / "worker.lock"
    old_fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    child = None
    try:
        with legacy_admission_guard(tmp_path) as binding:
            code = (
                "import os,time;"
                "print('READY '+str(os.getpid()),flush=True);"
                "print([os.readlink('/proc/self/fd/'+x) for x in os.listdir('/proc/self/fd')"
                " if x not in {'0','1','2'} and os.path.exists('/proc/self/fd/'+x)],flush=True);"
                "time.sleep(60)"
            )
            child = subprocess.Popen(custodial_command([sys.executable, "-I", "-c", code], binding),
                                     stdout=subprocess.PIPE, text=True)
            line = ready(child)
            target = int(line.split()[1])
            descriptors = child.stdout.readline()
            assert "worker.lock" not in descriptors
        # The coordinator's own shared FD is now closed. Namespace custody alone
        # excludes this already-open old fd (the pre-upgrade binary's protocol).
        with pytest.raises(BlockingIOError):
            fcntl.flock(old_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        child.kill()
        child.wait(timeout=5)
        wait_dead([target])
        fcntl.flock(old_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        os.close(old_fd)


def test_existing_legacy_worker_blocks_new_admission_and_namespace_start(tmp_path):
    path = tmp_path / "worker.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    held = os.fstat(fd)
    binding = {"root": str(tmp_path), "device": held.st_dev, "inode": held.st_ino}
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(OwnershipError, match="legacy_worker_active"):
            with legacy_admission_guard(tmp_path):
                pytest.fail("admission overlapped legacy coordinator")
        denied = subprocess.run(custodial_command(
            [sys.executable, "-I", "-c", "print('MUST_NOT_EXECUTE')"], binding),
            capture_output=True, text=True, timeout=5)
        assert denied.returncode != 0 and "MUST_NOT_EXECUTE" not in denied.stdout
    finally:
        os.close(fd)


def test_custodian_rejects_replaced_lock_inode_before_any_effect(tmp_path):
    with legacy_admission_guard(tmp_path) as binding:
        (tmp_path / "worker.lock").rename(tmp_path / "retained.lock")
        (tmp_path / "worker.lock").touch(mode=0o600)
        denied = subprocess.run(custodial_command(
            [sys.executable, "-I", "-c", "print('MUST_NOT_EXECUTE')"], binding),
            capture_output=True, text=True, timeout=5)
        assert denied.returncode != 0 and "MUST_NOT_EXECUTE" not in denied.stdout


def test_actual_pid_namespace_dies_with_custodian_including_grandchild(tmp_path):
    if not Path("/usr/bin/bwrap").is_file():
        pytest.skip("physical PID namespace regression requires bubblewrap")
    child = None
    with legacy_admission_guard(tmp_path) as binding:
        code = ("import subprocess,sys,time;"
                "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(60)']);"
                "print('READY',flush=True);time.sleep(60)")
        command = ["/usr/bin/bwrap", "--ro-bind", "/", "/", "--unshare-pid",
                   "--die-with-parent", "--proc", "/proc", "--",
                   "/usr/bin/python3", "-I", "-c", code]
        child = subprocess.Popen(custodial_command(command, binding), stdout=subprocess.PIPE, text=True)
        try:
            ready(child)
            owned = descendants(child.pid)
            assert len(owned) >= 3, owned
            child.kill()
            child.wait(timeout=5)
            wait_dead(owned)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)


@pytest.mark.parametrize("state", ["running", "blocked", "pending"])
@pytest.mark.parametrize("epoch", [None, {"version": 1, "run_token": "old", "fencing_token": 7}])
def test_old_parent_without_child_ledger_blocks_new_writer(tmp_path, state, epoch):
    directory = tmp_path / state
    directory.mkdir(mode=0o700)
    task = {"id": "legacy-parent", "attempt_state": "accepted",
            "run_token": "current", "fencing_token": 7}
    if epoch is not None:
        task["ownership_epoch"] = epoch
    (directory / "parent.json").write_text(json.dumps(task))
    with pytest.raises(OwnershipError, match="legacy_parent_active"):
        LegacyOwnershipInventory(tmp_path)({"reservations": {}})


def test_current_host_parent_and_terminal_old_parent_allow_inventory(tmp_path):
    directory = tmp_path / "running"
    directory.mkdir(mode=0o700)
    (directory / "new.json").write_text(json.dumps({
        "run_token": "new", "attempt_state": "accepted", "fencing_token": 9,
        "ownership_epoch": {"version": 1, "run_token": "new", "fencing_token": 9}}))
    (directory / "terminal.json").write_text(json.dumps({
        "run_token": "old", "attempt_state": "terminal", "fencing_token": 7}))
    assert LegacyOwnershipInventory(tmp_path)({"reservations": {}}) is True
