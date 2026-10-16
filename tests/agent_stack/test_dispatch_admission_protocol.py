"""Real process/epoch handoff, with explicit offline child command fixtures."""
import fcntl
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[2]
BIN = SOURCE / 'agent-stack/bin'


def load_dispatcher(root):
    sys.path[:0] = [str(SOURCE), str(BIN)]
    loader = SourceFileLoader('dispatch_admission_protocol_test', str(BIN / 'agent-task-dispatcher'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    for name in ('pending', 'running', 'blocked', 'logs', 'results'):
        (root / name).mkdir(exist_ok=True)
    module.ROOT = root
    module.PENDING = root / 'pending'
    module.RUNNING = root / 'running'
    module.LOG = root / 'dispatch.log'
    # Only host process discovery and command selection are explicit doubles.
    # The source launch path, nonce, parent-death fence and kernel locks are real.
    module.worker_running = lambda: False
    return module


def task_file(root, **extra):
    path = root / 'pending/one.json'
    path.write_text(json.dumps({'id': 'one', 'attempts': 1, 'fencing_token': 0, **extra}))
    return path


def wait_file(path, process=None, timeout=10):
    deadline = time.monotonic() + timeout
    while not path.exists():
        if process is not None:
            assert process.poll() is None, 'owned fixture process exited before readiness'
        assert time.monotonic() < deadline, 'bounded fixture readiness timeout'
        time.sleep(.01)


def dead(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()[0] == 'Z'
    except FileNotFoundError:
        return True


def wait_dead(pid):
    deadline = time.monotonic() + 5
    while not dead(pid):
        assert time.monotonic() < deadline, 'owned child retained resources after parent death'
        time.sleep(.01)


def test_retained_attempt_fields_do_not_acknowledge_new_process(tmp_path):
    dispatcher = load_dispatcher(tmp_path)
    pending = task_file(tmp_path, run_token='retained-attempt', ownership_epoch={'version': 1},
                        fencing_token=7)
    dispatcher.host_entrypoint_command = lambda *a, **kw: [sys.executable, '-I', '-c',
        'import time;time.sleep(.2);raise SystemExit(3)']
    assert dispatcher.launch(pending) == 1
    retained = json.loads((tmp_path / 'running/one.json').read_text())
    assert retained['run_token'] == 'retained-attempt' and retained['fencing_token'] == 7
    assert not list((tmp_path / 'blocked').iterdir())
    assert 'dispatch_admission' not in retained


@pytest.mark.parametrize('late_admission', [False, True])
def test_timeout_reaps_owned_child_with_epoch_held_and_never_resets_identity(tmp_path, monkeypatch, late_admission):
    dispatcher = load_dispatcher(tmp_path)
    pending = task_file(tmp_path)
    dispatcher.ADMISSION_TIMEOUT = .05
    program = r'''import fcntl,json,os,signal,sys,time
from pathlib import Path
root=Path(sys.argv[1])
def stop(*args):
    fd=os.open(root/'worker.lock',os.O_RDWR)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:(root/'epoch-held-at-stop').write_text('held')
        else:raise RuntimeError('dispatcher released guard before reaping child')
    finally:os.close(fd)
    if sys.argv[2]=='late':
        path=root/'running/one.json';data=json.loads(path.read_text())
        data.update(run_token='late-owned-attempt',fencing_token=1)
        path.write_text(json.dumps(data))
    raise SystemExit(0)
signal.signal(signal.SIGTERM,stop)
(root/'ready').write_text(str(os.getpid()))
time.sleep(60)
'''
    dispatcher.host_entrypoint_command = lambda *a, **kw: [sys.executable, '-I', '-c', program,
        str(tmp_path), 'late' if late_admission else 'none']
    actual_popen = subprocess.Popen
    children = []
    def spawn_ready(*a, **kw):
        process = actual_popen(*a, **kw)
        children.append(process)
        wait_file(tmp_path / 'ready', process)
        return process
    monkeypatch.setattr(dispatcher.subprocess, 'Popen', spawn_ready)
    try:
        assert dispatcher.launch(pending) == 1
        assert children[0].poll() is not None
        assert (tmp_path / 'epoch-held-at-stop').read_text() == 'held'
        if late_admission:
            kept = json.loads((tmp_path / 'running/one.json').read_text())
            assert kept['run_token'] == 'late-owned-attempt' and kept['fencing_token'] == 1
            assert not list((tmp_path / 'blocked').iterdir())
        else:
            kept = json.loads((tmp_path / 'blocked/one.json').read_text())
            assert kept['fencing_token'] == 0 and 'run_token' not in kept
            assert kept['automatic_retry_allowed'] is False
    finally:
        for process in children:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


def test_disappearance_between_exists_and_read_is_a_queue_transition(tmp_path, monkeypatch):
    dispatcher = load_dispatcher(tmp_path)
    pending = task_file(tmp_path)
    running = dispatcher.RUNNING / pending.name
    statuses = iter([None, None, 0])
    monkeypatch.setattr(dispatcher.subprocess, 'Popen',
        lambda *a, **kw: SimpleNamespace(pid=os.getpid(), poll=lambda: next(statuses)))
    dispatcher.host_entrypoint_command = lambda *a, **kw: ['/explicit-process-double']
    actual_read = Path.read_text
    moved = []
    def read_after_move(path, *a, **kw):
        if path == running and not moved:
            moved.append(True)
            os.replace(path, pending)
        return actual_read(path, *a, **kw)
    monkeypatch.setattr(Path, 'read_text', read_after_move)
    assert dispatcher.launch(pending) == 0
    assert pending.exists() and not running.exists()


COORDINATOR = r'''import importlib.util,json,sys
from pathlib import Path
from importlib.machinery import SourceFileLoader
source=Path(sys.argv[1]);root=Path(sys.argv[2]);sys.path[:0]=[str(source),str(source/'agent-stack/bin')]
loader=SourceFileLoader('own_dispatcher',str(source/'agent-stack/bin/agent-task-dispatcher'))
spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
m.ROOT=root;m.PENDING=root/'pending';m.RUNNING=root/'running';m.LOG=root/'dispatch.log'
m.ADMISSION_TIMEOUT=60;m.worker_running=lambda:False
m.host_entrypoint_command=lambda *a,**kw:[sys.executable,'-I','-B',str(root/'child.py'),str(source),str(root)]
raise SystemExit(m.launch(root/'pending/one.json'))
'''

CHILD = r'''import fcntl,importlib.util,json,os,sys,time
from pathlib import Path
from importlib.machinery import SourceFileLoader
source=Path(sys.argv[1]);root=Path(sys.argv[2]);sys.path[:0]=[str(source),str(source/'agent-stack/bin')]
(root/'child-pid').write_text(str(os.getpid()))
if not (root/'admit').exists():time.sleep(60)
from herdr.ownership_epoch import legacy_admission_guard
loader=SourceFileLoader('actual_admitting_worker',str(source/'agent-stack/bin/agent-task-worker'))
spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
with legacy_admission_guard(root):
    loop=os.open(root/'worker.loop.lock',os.O_CREAT|os.O_RDWR,0o600)
    fcntl.flock(loop,fcntl.LOCK_EX|fcntl.LOCK_NB)
    path=root/'running/one.json';task=json.loads(path.read_text())
    m.acknowledge_dispatch_admission(path,task)
    (root/'ack-ready').write_text('acknowledged')
    time.sleep(60)
'''


@pytest.mark.parametrize('admit', [False, True])
def test_real_parent_death_fence_hands_over_only_after_actual_worker_ack(tmp_path, admit):
    load_dispatcher(tmp_path)
    task_file(tmp_path, run_token='retained-identity', ownership_epoch={'version': 1}, fencing_token=7)
    (tmp_path / 'coordinator.py').write_text(COORDINATOR)
    (tmp_path / 'child.py').write_text(CHILD)
    if admit:
        (tmp_path / 'admit').touch()
    coordinator = subprocess.Popen([sys.executable, '-I', '-B', str(tmp_path / 'coordinator.py'),
        str(SOURCE), str(tmp_path)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    child_pid = None
    try:
        wait_file(tmp_path / 'child-pid', coordinator)
        child_pid = int((tmp_path / 'child-pid').read_text())
        if admit:
            wait_file(tmp_path / 'ack-ready')
            assert coordinator.wait(timeout=5) == 0, coordinator.stderr.read().decode()
            assert not dead(child_pid), 'acknowledged worker still depended on exited dispatcher'
            task = json.loads((tmp_path / 'running/one.json').read_text())
            assert task['dispatch_admission']['pid'] == child_pid
            assert len(task['dispatch_admission']['nonce']) == 32
            assert 'dispatch_admission_nonce' not in task and 'dispatch_admission_parent_pid' not in task
            assert task['run_token'] == 'retained-identity' and task['fencing_token'] == 7
            fd = os.open(tmp_path / 'worker.lock', os.O_RDWR)
            try:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(fd)
        else:
            coordinator.kill()
            coordinator.wait(timeout=5)
            wait_dead(child_pid)
    finally:
        if coordinator.poll() is None:
            coordinator.kill()
            coordinator.wait(timeout=5)
        if child_pid is not None and not dead(child_pid):
            os.kill(child_pid, signal.SIGKILL)
            wait_dead(child_pid)
        coordinator.stderr.close()
