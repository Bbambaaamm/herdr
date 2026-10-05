"""Host namespace lifetime and actual canonical writer-release boundary."""
import json
import os
import select
import subprocess
import sys
from pathlib import Path
import pytest
from herdr.child_ownership import OwnershipError
from herdr.ownership_release import capture_namespace_lifetime, namespace_exited, HostOwnershipRelease
from tests.herdr.test_child_ownership import parent, registry, scheduler, ownership, proposal


def start_namespace():
    if not Path("/usr/bin/bwrap").is_file():
        pytest.skip("physical namespace lifetime test requires bubblewrap")
    process = subprocess.Popen(["/usr/bin/bwrap", "--ro-bind", "/", "/", "--unshare-pid",
        "--die-with-parent", "--proc", "/proc", "--", "/usr/bin/python3", "-I", "-c",
        "import time;print('READY',flush=True);time.sleep(60)"],
        stdout=subprocess.PIPE, text=True)
    assert select.select([process.stdout], [], [], 5)[0]
    assert process.stdout.readline().strip() == "READY"
    todo = [process.pid]
    init = None
    while todo:
        pid = todo.pop()
        try:
            ids = next(line.split()[1:] for line in Path(f"/proc/{pid}/status").read_text().splitlines()
                       if line.startswith("NSpid:"))
            if len(ids) >= 2 and ids[-1] == "1":
                init = pid
                break
            todo.extend(int(x) for x in Path(f"/proc/{pid}/task/{pid}/children").read_text().split())
        except FileNotFoundError:
            continue
    assert init is not None
    return process, init


def test_actual_namespace_lifetime_is_not_released_while_init_is_alive():
    process, init = start_namespace()
    try:
        proof = capture_namespace_lifetime(init)
        assert not namespace_exited(proof)
        process.terminate()
        process.wait(timeout=5)
        assert namespace_exited(proof)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_host_process_cannot_claim_namespace_init_proof():
    with pytest.raises(OwnershipError, match="namespace_init"):
        capture_namespace_lifetime(os.getpid())


def test_actual_writer_release_waits_for_kernel_namespace_exit(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent-stack/bin"))
    from agent_durable_children import (ensure_attempt_directory, replay_host_scheduler,
                                       mark_ledger_required, all_children_terminal)
    from herdr.owned_write_mounts import OwnedWritePins
    from agent_durable_sandbox import PinnedWorktree
    import hashlib
    owner = parent()
    store = registry(tmp_path, verify_release=HostOwnershipRelease(tmp_path))
    directory = ensure_attempt_directory(tmp_path, owner.task_id, owner.run_token)
    item = scheduler(directory, owner, store)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "owned.py").write_text("original")
    fd = os.open(workspace, os.O_PATH | os.O_DIRECTORY)
    held = os.fstat(fd)
    pin = PinnedWorktree(workspace, fd, held.st_dev, held.st_ino)
    process, init = start_namespace()
    try:
        from dataclasses import replace
        node = item.delegate_child(owner.task_id, owner.run_token, "writer-exit",
            replace(proposal(owner, ownership(owner, files=("owned.py",))), worktree_identity=pin.identity))
        item.dispatch(task_ids={node.id}, managed_start=True)
        rec = item._tasks[node.id]
        marker = f"child-{rec.run_token}"
        assert item.record_child_pane_intent(rec.id, rec.run_token, rec.agent_id,
            rec.fencing_token, rec.idempotency_key, marker)
        assert item.bind_pre_delivery_pane(rec.id, rec.run_token, rec.agent_id, "child-pane", marker)
        with OwnedWritePins(rec.ownership, pin) as pins:
            item.bind_owned_write_mounts(rec.id, pins)
        item.record_namespace_lifetime(rec.id, capture_namespace_lifetime(init))
        assert item.attest_execution_sandbox(rec.id, rec.run_token, rec.agent_id, "child-pane", marker,
            sandbox_pid=init, policy_sha256="a"*64)
        (directory / "graph.jsonl").rename(directory / "scheduler.jsonl")
        item.audit_log._path = directory / "scheduler.jsonl"
        mark_ledger_required(directory)
        evidence = [{"result": "candidate"}]
        hashed = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        assert item.publish_child_result(rec.id, rec.run_token, rec.agent_id, rec.fencing_token,
            rec.idempotency_key, hashed, evidence)
        assert item.mark_child_cleanup_complete(rec.id)
        assert not item.release_child_ownership(rec.id)
        assert not all_children_terminal(tmp_path,owner.task_id,owner.run_token)
        with pytest.raises(OwnershipError, match="not_quiescent"):
            item._require_current_ownership(rec, result=True)
        process.terminate()
        process.wait(timeout=5)
        assert item.release_child_ownership(rec.id)
        assert all_children_terminal(tmp_path,owner.task_id,owner.run_token)
        item._require_current_ownership(rec, result=True)
        replay = replay_host_scheduler(tmp_path, directory / "scheduler.jsonl")
        assert replay._tasks[rec.id].namespace_lifetime == rec.namespace_lifetime
        assert replay.dispatch(task_ids={rec.id}, managed_start=True) == []
        replay._require_current_ownership(replay._tasks[rec.id], result=True)
        with pytest.raises(OwnershipError):
            replay._require_current_ownership(replay._tasks[rec.id])
    finally:
        pin.close()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
