"""Crash/replay contracts for optional ChatGPT proposal claims in existing intake."""
import copy
import importlib.machinery
import importlib.util
import json
from pathlib import Path

import pytest

from herdr.chatgpt_admission_binding import prepare_admission_binding
from test_chatgpt_admission_binding import fixture

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack/bin/agent-github-intake"


@pytest.fixture
def intake(tmp_path, monkeypatch):
    loader = importlib.machinery.SourceFileLoader("chatgpt_atomic_intake_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    root = tmp_path / "tasks"
    for name in ("pending", "running", "blocked", "done", "failed", "results", "logs"):
        (root / name).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(m, "ROOT", root)
    monkeypatch.setattr(m, "PENDING", root / "pending")
    monkeypatch.setattr(m, "RESULTS", root / "results")
    monkeypatch.setattr(m, "STATE", root / "github-intake-state.json")
    monkeypatch.setattr(m, "STAMP", root / "github-intake.stamp")
    monkeypatch.setattr(m, "LOG", root / "github-intake.log")
    return m


def inputs():
    args = fixture()
    binding = prepare_admission_binding(**args).evidence()
    consumer = {
        "consumer": "herdr", "repository": "Bbambaaamm/herdr",
        "mode": "root_only", "root_issue": 53,
    }
    issue = {"number": 53}
    return binding, args["root_admission"], consumer, issue, (
        "github-herdr-issue-53-approval-5400"
    )


def test_existing_state_transaction_records_claim_with_root_approval(intake):
    binding, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
    state = intake.load_state()
    row = state["Bbambaaamm/herdr#53"]
    assert row["admission_intent"]["state"] == "publication_pending"
    assert row["used_approvals"]["5400"] == task_id
    claim = row["proposal_consumptions"][binding["binding_sha256"]]
    assert claim["state"] == "publication_pending"
    assert claim["binding"] == binding
    assert not list(intake.PENDING.iterdir())


def test_published_claim_persists_and_replay_is_denied(intake):
    binding, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
        intake._mark_admission_published(consumer, issue, task_id, admission)
    row = intake.load_state()["Bbambaaamm/herdr#53"]
    assert row["admission_intent"]["state"] == "published"
    assert row["proposal_consumptions"][binding["binding_sha256"]]["state"] == "published"
    before = intake.STATE.read_bytes()
    with intake.intake_lock(), pytest.raises(intake.AdmissionDenied):
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
    assert intake.STATE.read_bytes() == before


def test_crash_after_intent_before_publication_fail_closed(intake):
    binding, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
    before = intake.STATE.read_bytes()
    with intake.intake_lock(), pytest.raises(intake.AdmissionDenied):
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
    assert intake.STATE.read_bytes() == before
    assert intake._requires_admission_reconciliation(
        intake.load_state()["Bbambaaamm/herdr#53"])


def test_second_root_approval_cannot_reconsume_same_proposal(intake):
    binding, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
        intake._mark_admission_published(consumer, issue, task_id, admission)
    new = {**binding, "root_approval_id": 5401}
    unsigned = {k: v for k, v in new.items() if k != "binding_sha256"}
    import hashlib
    new["binding_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    newer = {**admission, "approval_id": 5401}
    before = intake.STATE.read_bytes()
    with intake.intake_lock(), pytest.raises(intake.AdmissionDenied):
        intake._consume_admission(
            consumer, issue, "github-herdr-issue-53-approval-5401",
            newer, proposal_binding=new)
    assert intake.STATE.read_bytes() == before


def test_corrupt_claim_fails_closed_on_existing_state_load(intake):
    binding, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
    state = json.loads(intake.STATE.read_text())
    claim = state["Bbambaaamm/herdr#53"]["proposal_consumptions"][binding["binding_sha256"]]
    claim["binding"]["proposal_issue"] = 999
    intake.STATE.write_text(json.dumps(state))
    with pytest.raises(intake.AdmissionDenied):
        intake.load_state()


def test_merge_durable_claims_does_not_erase_consumption(intake):
    binding, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
        intake._mark_admission_published(consumer, issue, task_id, admission)
    snapshot = {"Bbambaaamm/herdr#53": {
        "repo": "Bbambaaamm/herdr", "issue": 53, "used_approvals": {},
    }}
    merged = intake._merge_durable_admissions(snapshot)["Bbambaaamm/herdr#53"]
    assert merged["proposal_consumptions"][binding["binding_sha256"]]["state"] == "published"
    assert merged["used_approvals"]["5400"] == task_id


def test_legacy_root_approval_still_has_no_proposal_claim(intake):
    _, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(consumer, issue, task_id, admission)
        intake._mark_admission_published(consumer, issue, task_id, admission)
    row = intake.load_state()["Bbambaaamm/herdr#53"]
    assert "proposal_consumptions" not in row
    assert row["admission_intent"]["state"] == "published"


def test_non_root_consumer_cannot_use_binding(intake):
    binding, admission, consumer, issue, task_id = inputs()
    consumer = {**consumer, "consumer": "loxxess"}
    before = intake.STATE.exists()
    with intake.intake_lock(), pytest.raises(intake.AdmissionDenied):
        intake._consume_admission(
            consumer, issue, task_id, admission, proposal_binding=binding)
    assert intake.STATE.exists() == before


def _queue_setup(intake, monkeypatch, admission):
    consumer = {
        "consumer": "herdr", "repository": "Bbambaaamm/herdr",
        "mode": "root_only", "root_issue": 53, "workspace": "/test/workspace",
        "safety_profile": "herdr-core", "hermes_profile": "quantlab",
        "coordinator_agent": "herdr-hermes", "priority_default": 60,
    }
    issue = {"number": 53, "title": "HERDR CONTROL", "body": "Root",
             "html_url": "https://github.com/Bbambaaamm/herdr/issues/53"}
    monkeypatch.setattr(intake, "approved_revision", lambda c, i: (issue, admission))
    monkeypatch.setattr(intake, "prior_evidence", lambda records: "none")
    monkeypatch.setattr(intake, "prompt_for", lambda *args: "Continue authorized root cycle.")
    monkeypatch.setattr(intake, "scan_remaining", lambda: 1.0)
    monkeypatch.setattr(intake, "disk_headroom_blocker", lambda *args: None)
    return consumer, issue


def test_optional_binding_queues_once_using_original_durable_publication(intake, monkeypatch):
    binding, admission, _, _, task_id = inputs()
    consumer, issue = _queue_setup(intake, monkeypatch, admission)
    with intake.intake_lock():
        actual = intake._queue_issue_locked(
            consumer, issue, [], proposal_binding=binding)
    assert actual == task_id
    stored = json.loads((intake.PENDING / (task_id + ".json")).read_text())
    assert stored["kind"] == "github_root_orchestration"
    assert stored["issue"] == 53
    assert stored["chatgpt_proposal_binding"] == binding
    assert stored["github_admission"] == admission
    state = intake.load_state()["Bbambaaamm/herdr#53"]
    assert state["admission_intent"]["state"] == "published"
    assert state["proposal_consumptions"][binding["binding_sha256"]]["state"] == "published"
    with intake.intake_lock(), pytest.raises(intake.AdmissionDenied):
        intake._queue_issue_locked(
            consumer, issue, [], proposal_binding=binding)
    assert len(list(intake.PENDING.glob("*.json"))) == 1


def test_publication_crash_keeps_both_durable_replay_barriers(intake, monkeypatch):
    binding, admission, _, _, task_id = inputs()
    consumer, issue = _queue_setup(intake, monkeypatch, admission)

    def fail_publish(*_):
        raise OSError("simulated crash after consumed approval")
    monkeypatch.setattr(intake, "publish_task", fail_publish)
    with intake.intake_lock(), pytest.raises(OSError):
        intake._queue_issue_locked(
            consumer, issue, [], proposal_binding=binding)
    row = intake.load_state()["Bbambaaamm/herdr#53"]
    assert row["admission_intent"]["state"] == "publication_pending"
    assert row["proposal_consumptions"][binding["binding_sha256"]]["state"] == "publication_pending"
    assert row["used_approvals"]["5400"] == task_id
    assert list(intake.PENDING.glob("*.json")) == []
    with intake.intake_lock(), pytest.raises(intake.AdmissionDenied):
        intake._queue_issue_locked(consumer, issue, [], proposal_binding=binding)


def test_repeated_content_under_different_issue_fails_closed(intake):
    binding, admission, consumer, issue, task_id = inputs()
    with intake.intake_lock():
        intake._consume_admission(consumer, issue, task_id, admission,
                                  proposal_binding=binding)
    new = {**binding, "proposal_issue": 301, "proposal_issue_id": 3010,
           "root_approval_id": 5401}
    unsigned = {k: v for k, v in new.items() if k != "binding_sha256"}
    import hashlib
    new["binding_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with intake.intake_lock(), pytest.raises(intake.AdmissionDenied):
        intake._consume_admission(
            consumer, issue, "github-herdr-issue-53-approval-5401",
            {**admission, "approval_id": 5401}, proposal_binding=new)
