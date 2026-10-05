"""Untrusted durable child result files stay bounded through recovery."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr.taskgraph import LifecycleState

import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent-stack/bin"))
from agent_durable_children import MAX_CHILD_RESULT_BYTES, publish_exact_child_result


def _fixture():
    evidence = ["exact evidence"]
    digest = hashlib.sha256(json.dumps(evidence, sort_keys=True,
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    rec = SimpleNamespace(
        node=SimpleNamespace(id="child"), run_token="run", fencing_token=3,
        idempotency_key="key", state=LifecycleState.DONE,
        attempt_state="terminal", result_status="completed",
        result_artifact_sha256=digest)
    result = dict(task_id="child", run_token="run", fencing_token=3,
                  idempotency_key="key", status="completed", evidence=evidence,
                  artifact_sha256=digest)
    return rec, result


@pytest.mark.parametrize("exact_limit", [False, True])
def test_child_result_accepts_normal_and_exact_limit(tmp_path, exact_limit):
    rec, result = _fixture()
    path = tmp_path / "result.json"
    if exact_limit:
        base = len(json.dumps({**result, "padding": ""}).encode())
        result["padding"] = "x" * (MAX_CHILD_RESULT_BYTES - base)
    from herdr.evidence import digest as payload_digest
    rec.completion_receipt={"result_payload_sha256":payload_digest(result)}
    path.write_text(json.dumps(result), encoding="utf-8")
    assert not exact_limit or path.stat().st_size == MAX_CHILD_RESULT_BYTES
    assert publish_exact_child_result(None, rec, path) == "completed"


def test_child_result_oversize_rejected_without_path_read(tmp_path, monkeypatch):
    rec, _ = _fixture()
    path = tmp_path / "result.json"
    with path.open("wb") as handle:
        handle.truncate(MAX_CHILD_RESULT_BYTES + 1)
    monkeypatch.setattr(Path, "read_text", lambda *args, **kwargs: pytest.fail("path read"))
    for _ in range(3):  # Recovery repeatedly encounters the same hostile file.
        with pytest.raises(ValueError, match="size limit"):
            publish_exact_child_result(None, rec, path)


def test_child_result_rejects_symlink_and_nonregular(tmp_path):
    rec, _ = _fixture()
    path = tmp_path / "result.json"
    assert publish_exact_child_result(None, rec, path) is None
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    path.symlink_to(target)
    with pytest.raises(OSError):
        publish_exact_child_result(None, rec, path)
    path.unlink()
    path.mkdir()
    with pytest.raises(ValueError, match="regular file"):
        publish_exact_child_result(None, rec, path)
