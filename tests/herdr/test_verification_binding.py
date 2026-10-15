"""Immutable malformed commit data must stop, rather than request transport retry."""
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
