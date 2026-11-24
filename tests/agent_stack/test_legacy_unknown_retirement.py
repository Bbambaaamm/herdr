"""Synthetic recovery-only suite. No live queue, provider or approval used."""
import hashlib
import json
import os
from pathlib import Path
import time

import pytest
from herdr.evidence import EvidenceError
from herdr import recovery_unknown as guarded
from herdr import legacy_unknown_review as review
from herdr import legacy_unknown_retirement as retired


@pytest.fixture
def fx(tmp_path, monkeypatch):
    root = tmp_path / "tasks"
    for name in ("blocked", "results", "logs", "pending", "running"):
        (root / name).mkdir(parents=True, mode=0o700)
    task = {
        "id": retired.TASK_ID, "repo": review.REPOSITORY, "issue": 53,
        "kind": "github_root_orchestration", "attempt_state": "blocked",
        "attempt_id": 0, "attempts": 0, "delivery_reconcile_count": 12,
        "run_token": "original", "idempotency_key": "episode",
        "execution_session": {"pane_id": "w4:p5", "cleanup_status": "closed"},
        "prompt": "SECRET NOT TO LEAK"
    }
    result = {
        "task_id": retired.TASK_ID, "run_token": "original",
        "status": "blocked", "blocker": "delivery_uncertain_requires_recovery"
    }
    files = [
        root / "blocked" / (retired.TASK_ID + ".json"),
        root / "results" / (retired.TASK_ID + ".json"),
        root / "logs" / (retired.TASK_ID + ".worker.log"),
    ]
    originals = (json.dumps(task).encode(), json.dumps(result).encode(), b"log")
    for path, content in zip(files, originals):
        path.write_bytes(content)
        path.chmod(0o600)
    for key, value in (
        ("TASK_SHA256", originals[0]), ("RESULT_SHA256", originals[1]),
        ("LOG_SHA256", originals[2])
    ):
        monkeypatch.setattr(review, key, hashlib.sha256(value).hexdigest())
        monkeypatch.setattr(retired, key, hashlib.sha256(value).hexdigest())
    decisions = tmp_path / "decisions"
    decisions.mkdir(mode=0o700)
    old_snapshot = guarded.snapshot

    def snapshot(path, **kwargs):
        if Path(path) in (decisions / retired.DECISION_FILE,
                          decisions / retired.ACTIVATION_FILE):
            kwargs["owner"] = os.geteuid()
            kwargs["protected"] = False
        return old_snapshot(path, **kwargs)

    monkeypatch.setattr(guarded, "snapshot", snapshot)
    monkeypatch.setattr(guarded, "DECISIONS", decisions)
    proposal = {
        "schema_version": retired.SCHEMA,
        "action": "retire_legacy_unknown_intake_blocker",
        "task_id": retired.TASK_ID,
        "original_task_sha256": retired.TASK_SHA256,
        "original_result_sha256": retired.RESULT_SHA256,
        "original_log_sha256": retired.LOG_SHA256,
        "review_evidence_sha256": retired.REVIEW_EVIDENCE_SHA256,
        "issued_at_epoch": int(time.time()) - 3,
        "expires_at_epoch": int(time.time()) + 120,
        "approval_reference": "test-independent-reviewed-approval",
        "writer_scope": "reviewed_writers_quiesced_and_locked",
        "billing_disposition": "preserved_unknown",
    }
    decision = decisions / retired.DECISION_FILE
    decision.write_bytes(json.dumps(proposal, sort_keys=True).encode())
    decision.chmod(0o644)  # Production root-owned 0644: queue UID can read, never write.
    return root, files, originals, decision, proposal


def apply(fx):
    root, *_ = fx
    return retired.apply(root, active_workers=lambda: set())


def activate(fx):
    """Synthetic root-post-apply attestation. Never tests a real protected host."""
    root, _, _, decision, proposal = fx
    dsha = hashlib.sha256(decision.read_bytes()).hexdigest()
    receipt = root / "results" / (retired.RECEIPT_NAME + dsha + ".json")
    raw = receipt.read_bytes()
    activation = {
        "schema_version": "herdr-legacy-unknown-activation-v1",
        "action": "activate_verified_legacy_retirement",
        "task_id": retired.TASK_ID,
        "decision_sha256": dsha,
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "original_task_sha256": retired.TASK_SHA256,
        "original_result_sha256": retired.RESULT_SHA256,
        "issued_at_epoch": int(time.time()),
        "verification_reference": "separate-host-operator-confirmation",
        "accounting": "preserved_unknown",
    }
    path = decision.parent / retired.ACTIVATION_FILE
    path.write_bytes(json.dumps(activation, sort_keys=True).encode())
    path.chmod(0o644)
    return path


def test_missing_operator_approval_keeps_blocker(fx):
    root, files, _, decision, _ = fx
    decision.unlink()
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))
    with pytest.raises(FileNotFoundError):
        apply(fx)
    assert not list((root / "results").glob("*.legacy-unknown-retirement-*"))


def test_approved_retirement_is_one_shot_and_originals_unchanged(fx):
    root, files, original, _, _ = fx
    task = json.loads(files[0].read_bytes())
    assert guarded.blocks_intake(root, task)
    first = apply(fx)
    assert first["status"] == "legacy_unknown_prepared_pending_root_activation"
    assert first["task_outcome"] == "UNKNOWN"
    assert first["accounting_mutated"] is False
    assert not retired.retired(root, task)
    assert guarded.blocks_intake(root, task)
    assert apply(fx)["status"] == "already_prepared_pending_root_activation"
    activate(fx)
    assert retired.retired(root, task)
    assert guarded.blocks_intake(root, task) is False
    second = apply(fx)
    assert second["status"] == "already_retired"
    assert all(p.read_bytes() == b for p, b in zip(files, original))
    receipts = list((root / "results").glob(retired.RECEIPT_NAME + "*.json"))
    assert len(receipts) == 1
    event = json.loads(receipts[0].read_bytes())
    assert event["task_outcome"] == "UNKNOWN"
    assert not event["automatic_retry_allowed"]
    assert not event["new_economic_attempt_authorized"]
    assert "SECRET" not in receipts[0].read_text()


@pytest.mark.parametrize("key,value", [
    ("billing_disposition", "settled"),
    ("review_evidence_sha256", "e" * 64),
    ("original_task_sha256", "f" * 64),
    ("writer_scope", "unreviewed"),
    ("action", "approve_retry"),
    ("expires_at_epoch", 1),
])
def test_invalid_root_decision_rejected(fx, key, value):
    root, files, _, decision, payload = fx
    payload[key] = value
    decision.write_text(json.dumps(payload))
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))
    with pytest.raises(EvidenceError):
        apply(fx)


def test_live_worker_holds(fx):
    root, *_ = fx
    with pytest.raises(EvidenceError, match="active_worker"):
        retired.apply(root, active_workers=lambda: {"/fake-worker"})
    assert not list((root / "results").glob(retired.RECEIPT_NAME + "*.json"))


@pytest.mark.parametrize("folder", ["pending", "running"])
def test_active_copy_holds(fx, folder):
    root, files, *_ = fx
    (root / folder / files[0].name).write_bytes(files[0].read_bytes())
    with pytest.raises(EvidenceError, match="parallel_root_work"):
        apply(fx)


@pytest.mark.parametrize("index", range(3))
def test_modified_original_blocks_even_with_valid_approval(fx, index):
    root, files, originals, *_ = fx
    files[index].write_bytes(originals[index] + b"x")
    with pytest.raises(EvidenceError, match="source_changed"):
        apply(fx)


def test_missing_receipt_does_not_unlock_intake(fx):
    root, files, *_ = fx
    task = json.loads(files[0].read_bytes())
    assert guarded.blocks_intake(root, task)
    assert retired.retired(root, task) is False


def test_changed_receipt_blocks_intake(fx):
    root, files, *_ = fx
    task = json.loads(files[0].read_bytes())
    apply(fx)
    receipt = next((root / "results").glob(retired.RECEIPT_NAME + "*.json"))
    data = json.loads(receipt.read_bytes())
    data["new_economic_attempt_authorized"] = True
    receipt.write_text(json.dumps(data))
    assert guarded.blocks_intake(root, task)
    with pytest.raises(EvidenceError, match="conflicting_receipt"):
        apply(fx)


def test_interrupted_before_completion_replays_existing_receipt(fx, monkeypatch):
    root, files, *_ = fx
    original_evidence = retired._evidence
    count = 0

    def interrupted(*args):
        nonlocal count
        count += 1
        if count == 2:
            raise EvidenceError("simulated_after_fsync_crash")
        return original_evidence(*args)

    monkeypatch.setattr(retired, "_evidence", interrupted)
    with pytest.raises(EvidenceError, match="simulated_after_fsync_crash"):
        apply(fx)
    monkeypatch.setattr(retired, "_evidence", original_evidence)
    assert apply(fx)["status"] == "already_prepared_pending_root_activation"
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))
    activate(fx)
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes())) is False


def test_double_acquire_lock_holds(fx):
    root, *_ = fx
    with guarded.queue_lock(root, "recovery.lock"):
        with pytest.raises(EvidenceError, match="writer_active"):
            apply(fx)


@pytest.mark.parametrize("folder", ["pending", "running"])
def test_other_active_episode_for_same_root_holds(fx, folder):
    root, files, *_ = fx
    new = json.loads(files[0].read_bytes())
    new["id"] = "github-herdr-issue-53-future-admission"
    (root / folder / "different-episode.json").write_bytes(json.dumps(new).encode())
    with pytest.raises(EvidenceError, match="parallel_root_work"):
        apply(fx)


def test_caller_record_must_equal_original_task(fx):
    root, files, *_ = fx
    apply(fx)
    forged = json.loads(files[0].read_bytes())
    forged["attempts"] = 3
    assert not retired.retired(root, forged)


def test_no_foreign_episode_is_blocked(fx):
    root, files, *_ = fx
    other = json.loads(files[0].read_bytes())
    other["id"] = "other-repo-task"
    other["repo"] = "other/repository"
    other["issue"] = 53
    (root / "pending" / "other-repo-task.json").write_bytes(json.dumps(other).encode())
    assert apply(fx)["status"] == "legacy_unknown_prepared_pending_root_activation"


def test_replayed_approved_retirement_never_republishes(fx, monkeypatch):
    root, *_ = fx
    assert apply(fx)["status"] == "legacy_unknown_prepared_pending_root_activation"
    def forbidden(*_args, **_kwargs):
        raise AssertionError("existing receipt must not be written again")
    monkeypatch.setattr(guarded, "_write", forbidden)
    assert apply(fx)["status"] == "already_prepared_pending_root_activation"


def test_full_dry_run_is_read_only_and_does_not_unlock_intake(fx):
    root, files, originals, *_ = fx
    state = retired.apply(root, active_workers=lambda: set(), dry_run=True)
    assert state["status"] == "READY_FOR_SEPARATE_OPERATOR_APPLY"
    assert state["activation_performed"] is False
    assert all(p.read_bytes() == raw for p, raw in zip(files, originals))
    assert not list((root / "results").glob(retired.RECEIPT_NAME + "*.json"))
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))


def test_unbounded_active_inventory_fails_closed(fx):
    root, *_ = fx
    for k in range(1025):
        (root / "pending" / f"other-{k}.json").write_text("{}")
    with pytest.raises(EvidenceError, match="active_inventory_unbounded"):
        apply(fx)


def test_non_object_active_inventory_denies(fx):
    root, *_ = fx
    (root / "pending" / "untrusted.json").write_bytes(b"[]")
    with pytest.raises(EvidenceError, match="active_inventory_invalid"):
        apply(fx)

def test_new_approval_cannot_publish_second_retirement(fx):
    root, files, original, decision, payload = fx
    assert apply(fx)["status"] == "legacy_unknown_prepared_pending_root_activation"
    payload["approval_reference"] = "second-operator-approval"
    decision.write_text(json.dumps(payload))
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))
    with pytest.raises(EvidenceError, match="conflicting_historical_receipt"):
        apply(fx)
    assert len(list((root / "results").glob(retired.RECEIPT_NAME + "*.json"))) == 1
    assert all(p.read_bytes() == old for p, old in zip(files, original))

def test_forged_receipt_before_approval_does_not_unlock(fx):
    root, files, _, decision, payload = fx
    digest = hashlib.sha256(decision.read_bytes()).hexdigest()
    path = root / "results" / (retired.RECEIPT_NAME + digest + ".json")
    path.write_text('{"task_outcome":"DONE"}')
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))
    with pytest.raises(EvidenceError, match="conflicting_receipt"):
        apply(fx)

def test_queue_owned_receipt_without_root_activation_cannot_release_intake(fx):
    root, files, *_ = fx
    task = json.loads(files[0].read_bytes())
    assert apply(fx)['status'] == 'legacy_unknown_prepared_pending_root_activation'
    assert guarded.blocks_intake(root, task)
    assert not retired.retired(root, task)

def test_root_activation_wrong_receipt_digest_fails_closed(fx):
    root, files, *_ = fx
    apply(fx)
    activation = activate(fx)
    data = json.loads(activation.read_bytes())
    data['receipt_sha256'] = 'e' * 64
    activation.write_text(json.dumps(data))
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))

def test_root_activation_wrong_action_fails_closed(fx):
    root, files, *_ = fx
    apply(fx)
    activation = activate(fx)
    data = json.loads(activation.read_bytes())
    data['action'] = 'force_retry'
    activation.write_text(json.dumps(data))
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))

def test_root_activation_must_be_after_receipt(fx):
    root, files, *_ = fx
    apply(fx)
    activation = activate(fx)
    receipt = next((root / 'results').glob(retired.RECEIPT_NAME + '*.json'))
    os.utime(activation, ns=(receipt.stat().st_mtime_ns - 1000000000,
                             receipt.stat().st_mtime_ns - 1000000000))
    assert guarded.blocks_intake(root, json.loads(files[0].read_bytes()))

def test_root_decision_and_activation_fixtures_are_readable(fx):
    root, _, _, decision, _ = fx
    assert decision.stat().st_mode & 0o777 == 0o644
    apply(fx)
    activation = activate(fx)
    assert activation.stat().st_mode & 0o777 == 0o644
