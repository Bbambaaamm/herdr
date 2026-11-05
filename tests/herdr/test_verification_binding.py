"""Immutable malformed commit data must stop, rather than request transport retry."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr.evidence import EvidenceError, EvidenceUnavailable, digest
from herdr.verification_binding import commit_binding, commit_footer, verify_commit_binding


def fixture():
    plan = {"identity": {"id": "task"}, "spec_hash": "d" * 64,
            "policy_hash": "e" * 64, "base_sha": "b" * 40}
    return plan, SimpleNamespace(commit_sha="a" * 40)


@pytest.mark.parametrize("commit", [None, [], 1, "text", {"message": None},
                                   {"message": []}, {"message": "\ud800"},
                                   {"message": "x" * 65537}])
def test_malformed_immutable_commit_is_permanently_rejected(commit):
    plan, artifact = fixture()
    with pytest.raises(EvidenceError) as failure:
        verify_commit_binding(plan, artifact, {"sha": artifact.commit_sha, "commit": commit})
    assert type(failure.value) is EvidenceError
    assert not isinstance(failure.value, EvidenceUnavailable)


def test_valid_utf8_message_at_exact_byte_limit_retains_binding():
    plan, artifact = fixture()
    footer = commit_footer(plan)
    padding = 65536 - len(footer.encode("utf-8")) - 1
    message = "\u00e9" * (padding // 2) + "x" * (padding % 2) + "\n" + footer
    assert len(message.encode("utf-8")) == 65536
    proof = verify_commit_binding(plan, artifact,
                                  {"sha": artifact.commit_sha, "commit": {"message": message}})
    assert proof == {**commit_binding(plan), "binding_sha256": digest(commit_binding(plan))}


def test_one_byte_over_limit_cannot_hide_an_otherwise_valid_binding():
    plan, artifact = fixture()
    footer = commit_footer(plan)
    message = "x" * (65536 - len(footer.encode("utf-8"))) + "\n" + footer
    with pytest.raises(EvidenceError, match="bounded specification binding"):
        verify_commit_binding(plan, artifact,
                              {"sha": artifact.commit_sha, "commit": {"message": message}})


def collector_fixture(monkeypatch):
    """Reuse the existing collector fixture without a test-path import assumption."""
    path = Path(__file__).resolve().parents[1] / "agent_stack" / "test_completion_collector.py"
    spec = importlib.util.spec_from_file_location("verification_binding_collector_fixture", path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    artifact, plan, pr, checks, comment = helper.proof_fixture()
    helper.install_transport(monkeypatch, artifact, plan, pr, checks, comment)
    return helper.collector, artifact, plan


def stop_after_full_commit(monkeypatch, collector, artifact, plan, document):
    """Every later collection/review/acceptance seam is forbidden on this path."""
    calls, later_calls = [], []
    fixture_transport = collector.github
    pr_path = f"repos/{plan['repo']}/pulls/4"
    commit_path = f"repos/{plan['repo']}/commits/{artifact.commit_sha}"

    def forbidden(*args, **kwargs):
        later_calls.append(True)
        pytest.fail("malformed immutable evidence reached a later collection or acceptance seam")

    def github(path):
        calls.append(path)
        if path == commit_path:
            return document
        assert path == pr_path and len(calls) == 1
        return fixture_transport(path)

    monkeypatch.setattr(collector, "github", github)
    for name in ("github_command", "collect_checks", "verify_workflow",
                 "_unresolved_threads", "_check_effective_reviews", "accept_artifact"):
        monkeypatch.setattr(collector, name, forbidden)
    return calls, later_calls, [pr_path, commit_path]


@pytest.mark.parametrize("shape", [
    "null-resource", "list-resource", "string-resource", "integer-resource",
    "null-commit", "list-commit", "string-commit", "integer-commit", "invalid-utf8",
])
def test_collector_classifies_malformed_full_commit_as_invalid_evidence(monkeypatch, shape):
    collector, artifact, plan = collector_fixture(monkeypatch)
    malformed = {
        "null-resource": None, "list-resource": [], "string-resource": "text", "integer-resource": 1,
        "null-commit": {"sha": artifact.commit_sha, "commit": None},
        "list-commit": {"sha": artifact.commit_sha, "commit": []},
        "string-commit": {"sha": artifact.commit_sha, "commit": "text"},
        "integer-commit": {"sha": artifact.commit_sha, "commit": 1},
        "invalid-utf8": {"sha": artifact.commit_sha, "commit": {"message": "\ud800"}},
    }[shape]
    calls, later_calls, expected = stop_after_full_commit(
        monkeypatch, collector, artifact, plan, malformed)

    with pytest.raises(EvidenceError) as failure:
        collector.collect_github(plan, artifact, 4)

    assert type(failure.value) is EvidenceError
    assert not isinstance(failure.value, EvidenceUnavailable)
    assert str(failure.value) == (
        "reviewed commit origin differs from artifact" if shape.endswith("-resource")
        else "reviewed commit has no bounded specification binding")
    assert calls == expected and later_calls == []


@pytest.mark.parametrize("fault", ["duplicate-footer", "noncanonical-footer", "different-specification"])
def test_collector_preserves_canonical_footer_rejection_before_review(monkeypatch, fault):
    from herdr.verification_binding import PREFIX
    collector, artifact, plan = collector_fixture(monkeypatch)
    footer = commit_footer(plan)
    if fault == "duplicate-footer":
        message = footer + "\n" + footer
    elif fault == "noncanonical-footer":
        message = PREFIX + json.dumps(commit_binding(plan), sort_keys=True)
    else:
        message = commit_footer({**plan, "spec_hash": "f" * 64})
    document = {"sha": artifact.commit_sha, "commit": {"message": message}}
    calls, later_calls, expected = stop_after_full_commit(
        monkeypatch, collector, artifact, plan, document)

    with pytest.raises(EvidenceError) as failure:
        collector.collect_github(plan, artifact, 4)

    assert type(failure.value) is EvidenceError
    assert calls == expected and later_calls == []


def test_collector_accepts_exact_canonical_binding_with_fixture_transport(monkeypatch):
    collector, artifact, plan = collector_fixture(monkeypatch)
    transport, calls = collector.github, []

    def github(path):
        calls.append(path)
        return transport(path)

    def no_real_cli(*args, **kwargs):
        pytest.fail("fixture control must not launch a real GitHub command")

    monkeypatch.setattr(collector, "github", github)
    monkeypatch.setattr(collector, "github_command", no_real_cli)
    proof = collector.collect_github(plan, artifact, 4)
    assert proof["source"] == "github-api"
    assert proof["review"]["specification_binding"] == {
        **commit_binding(plan), "binding_sha256": digest(commit_binding(plan))}
    assert proof["review"]["commit_sha"] == artifact.commit_sha
    assert calls[:2] == [f"repos/{plan['repo']}/pulls/4",
                         f"repos/{plan['repo']}/commits/{artifact.commit_sha}"]
    assert any(path.endswith("/reviews?per_page=100") for path in calls)
