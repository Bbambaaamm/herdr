from __future__ import annotations

import importlib.util
import json
import os
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

from herdr.security import InvocationIdentity

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "agent-stack" / "bin"
sys.path.insert(0, str(BIN))

loader = SourceFileLoader("external_knowledge_worker_authority", str(BIN / "agent-task-worker"))
spec = importlib.util.spec_from_loader(loader.name, loader)
worker = importlib.util.module_from_spec(spec)
loader.exec_module(worker)


def configure(tmp_path):
    worker.ROOT = tmp_path
    worker.PENDING = tmp_path / "pending"
    worker.RUNNING = tmp_path / "running"
    worker.DONE = tmp_path / "done"
    worker.BLOCKED = tmp_path / "blocked"
    worker.FAILED = tmp_path / "failed"
    for path in (
        worker.PENDING, worker.RUNNING, worker.DONE, worker.BLOCKED, worker.FAILED
    ):
        path.mkdir(parents=True, exist_ok=True)


def identity():
    return InvocationIdentity(
        consumer="github:Example/project",
        agent_id="task-agent",
        parent_agent_id="parent-agent",
        parent_task_id="parent-task",
        task_id="task-1",
        run_token="run-1",
        fencing_token=7,
    )


def task_document(item, grant_sha):
    return {
        "id": item.task_id,
        "repo": "Example/project",
        "run_token": item.run_token,
        "fencing_token": item.fencing_token,
        "execution_session": {
            "agent_name": item.agent_id,
            "sandbox_verified": True,
            "sandbox_pid": os.getpid(),
            "economic_delivery_attempted": True,
            "launch_identity": item.to_json(),
            "invocation_policy": {"grant_sha256": grant_sha},
        },
    }


def publish(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    path.chmod(0o600)


def test_root_external_knowledge_authority_requires_exact_running_attempt(tmp_path):
    configure(tmp_path)
    item = identity()
    grant_sha = "a" * 64
    path = worker.RUNNING / f"{item.task_id}.json"
    document = task_document(item, grant_sha)
    publish(path, document)

    assert worker.external_knowledge_task_authority(
        item, grant_sha, "provider", object()
    )

    changed = dict(document)
    changed["fencing_token"] = item.fencing_token + 1
    publish(path, changed)
    assert not worker.external_knowledge_task_authority(
        item, grant_sha, "provider", object()
    )

    publish(path, document)
    path.rename(worker.DONE / path.name)
    assert not worker.external_knowledge_task_authority(
        item, grant_sha, "provider", object()
    )


def test_root_external_knowledge_authority_requires_verified_live_session(tmp_path):
    configure(tmp_path)
    item = identity()
    grant_sha = "b" * 64
    path = worker.RUNNING / f"{item.task_id}.json"
    document = task_document(item, grant_sha)

    for field, value in (
        ("sandbox_verified", False),
        ("economic_delivery_attempted", False),
        ("sandbox_pid", 0),
        ("closed_at", "now"),
    ):
        candidate = json.loads(json.dumps(document))
        candidate["execution_session"][field] = value
        publish(path, candidate)
        assert not worker.external_knowledge_task_authority(
            item, grant_sha, "provider", object()
        )

    publish(path, document)
    assert not worker.external_knowledge_task_authority(
        item, "c" * 64, "provider", object()
    )
