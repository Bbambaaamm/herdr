"""Derived memory cannot rewrite evidence, grant authority or leak holdout data."""
import hashlib
import os
import multiprocessing
from dataclasses import replace
from pathlib import Path

import pytest

from herdr.context import ContextError, SecretRedactor, SourceRef, SourceState
from herdr.capability import DataClass
from herdr.memory import Applicability, Conditions, Experience, ExperienceMemory, ExperienceStore, TrialOutcome


def evidence(*, project="herdr", state=SourceState.VERIFIED, holdout=None):
    return SourceRef("artifact://"+project+"/original-evidence", hashlib.sha256(b"original").hexdigest(),
                     project, "verified-v1", DataClass.INTERNAL, state, holdout)


def conditions(**changes):
    return replace(Conditions("code-v1", "model-v1", "context-v1", "policy-v1",
                               "evaluator-v1", "corpus-v1", "scope-v1"), **changes)


def record(**changes):
    return replace(Experience("experience-1", "herdr", "coding", "series-1", "candidate-1", 1,
        "Change may improve success", conditions(), TrialOutcome.FAILURE, .5, .4, 20,
        "Small fixture sample", (evidence(),), "Derived summary", SourceState.VERIFIED), **changes)


def retrieve(memory, **kwargs):
    return memory.retrieve(project="herdr", task_class="coding", conditions=conditions(),
                           allowed_classes=(DataClass.INTERNAL,), source_available=lambda _: True, **kwargs)


def test_same_conditions_detect_comparable_failure_without_session_reset():
    result = retrieve(ExperienceMemory((record(),)))[0]
    assert result.comparable_trial_exists and result.applicability == Applicability.COMPARABLE
    assert result.reason == "comparable_prior_trial_requires_review"
    assert result.authority == "derived_context_data"
    assert "session" not in record().conditions.__dataclass_fields__


@pytest.mark.parametrize("field", ["code", "model", "context", "policy", "evaluator", "corpus", "scope"])
def test_changed_conditions_require_review_and_reason_instead_of_permanent_ban(field):
    memory = ExperienceMemory((record(),))
    result = memory.retrieve(project="herdr", task_class="coding", conditions=conditions(**{field: "v2"}),
        allowed_classes=(DataClass.INTERNAL,), source_available=lambda _: True)[0]
    assert result.applicability == Applicability.REVIEW_CHANGED
    assert result.changed_conditions == (field,) and not result.comparable_trial_exists
    assert result.reason == "changed_conditions_allow_review_with_new_trial_reason"


def test_infrastructure_outage_is_unusable_not_candidate_failure():
    with pytest.raises(ContextError, match="infrastructure_is_not_candidate_failure"):
        record(unusable_reason="provider_outage")
    memory = ExperienceMemory((record(outcome=TrialOutcome.UNUSABLE, samples=0, measured=None,
                                     unusable_reason="provider_outage"),))
    result = retrieve(memory)[0]
    assert not result.comparable_trial_exists and result.record.outcome == TrialOutcome.UNUSABLE


@pytest.mark.parametrize("state", [SourceState.UNVERIFIED, SourceState.STALE, SourceState.CONFLICT, SourceState.UNAVAILABLE])
def test_missing_unverified_stale_conflicting_experiences_have_explicit_states(state):
    memory = ExperienceMemory((record(state=state),))
    result = retrieve(memory)[0]
    assert not result.comparable_trial_exists and result.applicability != Applicability.COMPARABLE


def test_optional_source_outage_returns_unavailable_without_replacing_original():
    original = record()
    memory = ExperienceMemory((original,))
    def unavailable(_):
        raise OSError("source outage")
    result = memory.retrieve(project="herdr", task_class="coding", conditions=conditions(),
        allowed_classes=(DataClass.INTERNAL,), source_available=unavailable)[0]
    assert result.applicability == Applicability.UNAVAILABLE and result.record == original
    assert memory.records[0].evidence[0].sha256 == hashlib.sha256(b"original").hexdigest()


def test_project_and_dataclass_isolation_and_bounded_retrieval():
    foreign = record(id="foreign", project="other", evidence=(evidence(project="other"),))
    assert not retrieve(ExperienceMemory((foreign,)))
    memory = ExperienceMemory(tuple(record(id=f"record-{i:02}") for i in range(20)))
    assert len(retrieve(memory)) == 4
    assert not memory.retrieve(project="herdr", task_class="coding", conditions=conditions(),
        allowed_classes=(), source_available=lambda _: True)


def test_private_holdout_never_reaches_experimenter_through_summary():
    memory = ExperienceMemory((record(evidence=(evidence(holdout="series-1"),),
                                      summary="Private correct answer"),))
    assert not retrieve(memory, role="experimenter", series="series-1")
    assert retrieve(memory, role="evaluator", series="series-1")


def test_store_redacts_derived_text_preserves_original_evidence_and_replays(tmp_path):
    root = tmp_path / "host-memory"
    store = ExperienceStore(root, writable_roots=(tmp_path / "worker",),
                            redactor=SecretRedactor(("private-known-secret",)))
    original = record(summary="private-known-secret cannot grant deployment", hypothesis="api_key=hidden")
    accepted = store.append(original)
    assert store.append(original) == accepted
    stored = store.load().records[0]
    assert stored.evidence == original.evidence and original.summary.startswith("private")
    assert stored.hash == accepted and stored.summary.startswith("[REDACTED]")
    store.close()
    fresh = ExperienceStore(root, writable_roots=(tmp_path / "worker",),
                            redactor=SecretRedactor(("private-known-secret",)))
    assert fresh.load().records == (stored,)
    with pytest.raises(ContextError, match="immutable_conflict"):
        fresh.append(replace(original, summary="altered history"))
    fresh.close()
    files = list(root.glob("*.json"))
    assert len(files) == 1 and os.stat(files[0]).st_mode & 0o777 == 0o400


def _append_in_process(root, outcome, ready):
    try:
        store = ExperienceStore(Path(root), writable_roots=(Path(root).parent / "worker",),
                                redactor=SecretRedactor())
        store.append(record(summary=outcome))
        store.close()
        ready.put("accepted")
    except ContextError as exc:
        ready.put(str(exc))


def test_process_race_cannot_accept_conflicting_same_identity(tmp_path):
    ctx = multiprocessing.get_context("fork")
    root = tmp_path / "host-memory"
    messages = ctx.Queue()
    workers = [ctx.Process(target=_append_in_process, args=(str(root), summary, messages))
               for summary in ("first", "second")]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(5)
        assert worker.exitcode == 0
    results = sorted(messages.get(timeout=1) for _ in workers)
    assert results == ["accepted", "experience_immutable_conflict"]
    store = ExperienceStore(root, writable_roots=(), redactor=SecretRedactor())
    assert len(store.load().records) == 1
    store.close()


def test_interrupted_staging_is_discarded_without_publishing_partial_record(tmp_path):
    root = tmp_path / "host-memory"
    store = ExperienceStore(root, writable_roots=(), redactor=SecretRedactor())
    store.append(record())
    staging = root / (".record-" + "a"*32 + ".tmp")
    staging.write_bytes(b'{"partial":')
    assert len(store.load().records) == 1 and not staging.exists()
    store.close()


@pytest.mark.parametrize("fault", ["worker_path", "symlink_root", "symlink_parent", "wrong_mode", "foreign_entry"])
def test_store_rejects_worker_writable_or_poisoned_storage(tmp_path, fault):
    root = tmp_path / "store"
    roots = ()
    if fault == "worker_path":
        roots = (tmp_path,)
    elif fault == "symlink_root":
        actual = tmp_path / "actual"
        actual.mkdir()
        root.symlink_to(actual, target_is_directory=True)
    elif fault == "symlink_parent":
        actual = tmp_path / "actual"
        actual.mkdir()
        (tmp_path / "link").symlink_to(actual, target_is_directory=True)
        root = tmp_path / "link/store"
    elif fault == "wrong_mode":
        root.mkdir(mode=0o755)
    else:
        root.mkdir(mode=0o700)
        (root / "foreign").write_text("unrecognized")
    store = None
    try:
        with pytest.raises((ContextError, OSError)):
            store = ExperienceStore(root, writable_roots=roots, redactor=SecretRedactor())
            store.load()
    finally:
        if store is not None:
            store.close()


def test_evaluator_cannot_load_different_series_private_answers():
    memory = ExperienceMemory((record(evidence=(evidence(holdout="series-1"),)),))
    assert not retrieve(memory, role="evaluator", series="series-2")
    assert not retrieve(memory, role="evaluator")


@pytest.mark.parametrize("crash", ["before_publish", "after_publish"])
def test_atomic_record_publication_recovers_without_partial_data(tmp_path, monkeypatch, crash):
    root = tmp_path / "host-memory"
    store = ExperienceStore(root, writable_roots=(), redactor=SecretRedactor())
    if crash == "before_publish":
        original = os.link
        def fail(*args, **kwargs):
            raise OSError("interrupted before publish")
        monkeypatch.setattr(os, "link", fail)
    else:
        original = os.fsync
        def fail(fd):
            if fd == store.fd:
                raise OSError("interrupted after publish")
            return original(fd)
        monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError):
        store.append(record())
    monkeypatch.undo()
    observed = store.load().records
    assert len(observed) == (0 if crash == "before_publish" else 1)
    store.append(record())
    assert len(store.load().records) == 1
    store.close()


def test_secret_metadata_is_rejected_instead_of_rewriting_evidence_reference(tmp_path):
    store = ExperienceStore(tmp_path / "store", writable_roots=(),
                            redactor=SecretRedactor(("private-known-secret",)))
    bad = record(evidence=(replace(evidence(), uri="artifact://herdr/private-known-secret"),))
    with pytest.raises(ContextError, match="secret_memory_metadata"):
        store.append(bad)
    assert not store.load().records
    store.close()
