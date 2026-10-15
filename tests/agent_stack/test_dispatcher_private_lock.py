"""Real kernel lock/guard regression for the ordinary dispatcher's cold queue."""
import fcntl
import importlib.util
import json
import os
import stat
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE))
from herdr.ownership_epoch import legacy_admission_guard


@pytest.fixture
def dispatcher(tmp_path, monkeypatch):
    loader = SourceFileLoader('dispatcher_private_lock_test',
        str(SOURCE / 'agent-stack/bin/agent-task-dispatcher'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'PENDING', tmp_path / 'pending')
    monkeypatch.setattr(module, 'RUNNING', tmp_path / 'running')
    monkeypatch.setattr(module, 'LOG', tmp_path / 'dispatch.log')
    # Only process discovery is doubled: all open/stat/flock calls and the
    # worker's admission guard below use real files and kernel locks.
    original_run = subprocess.run
    def run(args, **kwargs):
        if args[:3] == ['/usr/bin/pgrep', '-f', '[a]gent-task-worker']:
            return SimpleNamespace(returncode=1)
        return original_run(args, **kwargs)
    monkeypatch.setattr(module.subprocess, 'run', run)
    return module


def test_fresh_queue_under_normal_umask_passes_actual_worker_guard(dispatcher):
    previous = os.umask(0o022)
    try:
        assert dispatcher.worker_running() is False
    finally:
        os.umask(previous)
    lock = dispatcher.ROOT / 'worker.lock'
    info = lock.stat()
    assert stat.S_IMODE(info.st_mode) == 0o600
    with legacy_admission_guard(dispatcher.ROOT) as binding:
        assert binding['inode'] == info.st_ino
        assert dispatcher.worker_running() is True
    assert dispatcher.worker_running() is False
    assert lock.stat().st_ino == info.st_ino


@pytest.mark.parametrize('shared', [False, True])
def test_existing_kernel_lock_prevents_another_dispatch(dispatcher, shared):
    fd = os.open(dispatcher.ROOT / 'worker.lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_SH if shared else fcntl.LOCK_EX)
        assert dispatcher.worker_running() is True
    finally:
        os.close(fd)
    assert dispatcher.worker_running() is False


@pytest.mark.parametrize('kind', ['public', 'writable', 'hardlink', 'symlink', 'fifo'])
def test_unsafe_existing_lock_denied_before_task_claim(dispatcher, kind):
    lock = dispatcher.ROOT / 'worker.lock'
    if kind == 'fifo':
        os.mkfifo(lock, 0o600)
    elif kind == 'symlink':
        target = dispatcher.ROOT / 'foreign'
        target.write_bytes(b'preserve')
        lock.symlink_to(target)
    else:
        lock.write_bytes(b'preserve')
        lock.chmod(0o644 if kind == 'public' else 0o666 if kind == 'writable' else 0o600)
        if kind == 'hardlink':
            os.link(lock, dispatcher.ROOT / 'alias')
    dispatcher.PENDING.mkdir()
    dispatcher.RUNNING.mkdir()
    task = dispatcher.PENDING / 'one.json'
    original = b'{"id":"one","attempts":1,"fencing_token":0}\n'
    task.write_bytes(original)
    before = lock.lstat()
    with pytest.raises((OSError, RuntimeError)):
        dispatcher.launch(task)
    assert task.read_bytes() == original
    assert not list(dispatcher.RUNNING.iterdir())
    assert lock.lstat().st_ino == before.st_ino
    assert stat.S_IMODE(lock.lstat().st_mode) == stat.S_IMODE(before.st_mode)
    if kind != 'fifo':
        assert lock.read_bytes() == b'preserve'


@pytest.mark.parametrize('kind', ['symlink', 'writable'])
def test_unsafe_root_denied(dispatcher, kind):
    if kind == 'symlink':
        target = dispatcher.ROOT / 'actual'
        target.mkdir()
        alias = dispatcher.ROOT / 'alias'
        alias.symlink_to(target, target_is_directory=True)
        dispatcher.ROOT = alias
    else:
        dispatcher.ROOT.chmod(0o777)
    with pytest.raises(RuntimeError, match='worker_lock_root'):
        dispatcher.worker_running()
    assert not (dispatcher.ROOT / 'worker.lock').exists()


def test_replaced_inode_is_denied(dispatcher, monkeypatch):
    original_flock = fcntl.flock
    def replace(fd, operation):
        original_flock(fd, operation)
        path = dispatcher.ROOT / 'worker.lock'
        path.rename(dispatcher.ROOT / 'retained-original')
        other = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        os.close(other)
    monkeypatch.setattr(dispatcher.fcntl, 'flock', replace)
    with pytest.raises(RuntimeError, match='worker_lock_changed'):
        dispatcher.worker_running()


@pytest.mark.parametrize('status', [0, 2])
def test_process_discovery_preserves_spawn_race_and_denies_errors(dispatcher, monkeypatch, status):
    monkeypatch.setattr(dispatcher.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=status))
    if status == 0:
        assert dispatcher.worker_running() is True
    else:
        with pytest.raises(RuntimeError, match='worker_process_probe_failed'):
            dispatcher.worker_running()
    assert not (dispatcher.ROOT / 'worker.lock').exists()


def test_real_child_admission_after_dispatcher_creates_lock(dispatcher):
    assert dispatcher.worker_running() is False
    program = """import json, sys
from herdr.ownership_epoch import legacy_admission_guard
with legacy_admission_guard(sys.argv[1]) as binding:
    print(json.dumps(binding))
"""
    result = subprocess.run([sys.executable, '-c', program, str(dispatcher.ROOT)],
        cwd=SOURCE, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['inode'] == (dispatcher.ROOT / 'worker.lock').stat().st_ino


@pytest.mark.parametrize('change', ['chmod', 'hardlink'])
def test_metadata_changed_during_acquisition_denied_before_claim(dispatcher, monkeypatch, change):
    dispatcher.PENDING.mkdir()
    dispatcher.RUNNING.mkdir()
    task = dispatcher.PENDING / 'one.json'
    original = b'{"id":"one","attempts":1,"fencing_token":0}\n'
    task.write_bytes(original)
    actual_flock = fcntl.flock
    def acquire_then_change(fd, operation):
        actual_flock(fd, operation)
        lock = dispatcher.ROOT / 'worker.lock'
        if change == 'chmod':
            lock.chmod(0o644)
        else:
            os.link(lock, dispatcher.ROOT / 'another-name')
    monkeypatch.setattr(dispatcher.fcntl, 'flock', acquire_then_change)
    with pytest.raises(RuntimeError, match='worker_lock_metadata'):
        dispatcher.launch(task)
    assert task.read_bytes() == original
    assert not list(dispatcher.RUNNING.iterdir())
