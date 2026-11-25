"""Offline double-approval binding, without queue or host grants."""
import copy
from datetime import datetime, timezone, timedelta

import pytest
from herdr.chatgpt_command import CommandProposal
from herdr.chatgpt_admission_binding import (
    prepare_admission_binding, ProposalBindingDenied,
)


def fixture():
    raw = ('{"version":1,"repository":"Bbambaaamm/herdr","root_issue":53,'
           '"operation":"implement","target_kind":"pull_request",'
           '"target_number":253,"objective":"Fix native release verifier",'
           '"constraints":["No merge","No deploy"]}').encode()
    proposal = CommandProposal.parse(raw)
    early = datetime(2026, 11, 25, 12, tzinfo=timezone.utc)
    def receipt(issue_id, approval, sha, time):
        return {
            "version": 1, "approval_id": approval, "content_sha256": sha,
            "repository_id": 911, "issue_id": issue_id,
            "approver_user_id": 101, "approver_login": "maintainer",
            "approved_at": time.isoformat(),
            "expires_at": (time + timedelta(minutes=30)).isoformat(),
            "issue_updated_at": (time - timedelta(minutes=1)).isoformat(),
        }
    root = receipt(530, 5400, "b" * 64, early + timedelta(minutes=2))
    root["proposal_selection"] = {
        "issue_number": 300, "issue_id": 3000,
        "digest": proposal.digest, "revision": "a" * 64,
    }
    return dict(
        proposal=proposal, proposal_issue=300, proposal_issue_id=3000,
        proposal_revision="a" * 64, proposal_admission=receipt(3000, 3100, "a" * 64, early),
        root_revision="b" * 64, root_admission=root,
        consumed_proposals=set(),
    )


def test_two_independent_approvals_produce_inert_deterministic_binding():
    args = fixture()
    a = prepare_admission_binding(**args).evidence()
    b = prepare_admission_binding(**args).evidence()
    assert a == b
    assert a["root_issue"] == 53
    assert a["proposal_issue"] == 300
    assert a["target_number"] == 253
    assert len(a["binding_sha256"]) == 64
    assert "grant" not in a
    assert "execution_authorized" not in a


@pytest.mark.parametrize("mutation", [
    ("proposal_issue", 53),
    ("proposal_issue", True),
    ("proposal_issue_id", -1),
    ("proposal_revision", "wrong"),
    ("root_revision", "invalid"),
    ("consumed_proposals", None),
    ("consumed_proposals", {(300, fixture()["proposal"].digest)}),
])
def test_binding_denies_bad_or_duplicate_proposal(mutation):
    args = fixture()
    args[mutation[0]] = mutation[1]
    with pytest.raises(ProposalBindingDenied):
        prepare_admission_binding(**args)


@pytest.mark.parametrize("which,key,value", [
    ("proposal_admission", "approval_id", True),
    ("proposal_admission", "issue_id", 66),
    ("proposal_admission", "content_sha256", "c" * 64),
    ("proposal_admission", "repository_id", 98),
    ("root_admission", "version", 2),
    ("root_admission", "content_sha256", "a" * 64),
    ("root_admission", "approver_login", "not-valid!"),
])
def test_binding_denies_invalid_approval_evidence(which, key, value):
    args = fixture()
    args[which] = {**args[which], key: value}
    with pytest.raises(ProposalBindingDenied):
        prepare_admission_binding(**args)


def test_root_approval_must_follow_proposal_approval():
    args = fixture()
    args["root_admission"] = copy.deepcopy(args["root_admission"])
    args["root_admission"]["approved_at"] = args["proposal_admission"]["approved_at"]
    with pytest.raises(ProposalBindingDenied):
        prepare_admission_binding(**args)


def test_intake_prepare_binding_uses_existing_approval_helper(monkeypatch):
    import importlib.machinery
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "agent-stack/bin/agent-github-intake"
    loader = importlib.machinery.SourceFileLoader("binding_intake_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    args = fixture()
    rendered = args["proposal"].github_issue_proposal()
    repo = "Bbambaaamm/herdr"
    api = "https://api.github.com/repos/" + repo
    def issue(number, title, body, ident):
        return {"number": number, "id": ident, "state": "open",
                "title": title, "body": body, "comments": 0,
                "repository_url": api, "url": api + "/issues/" + str(number),
                "html_url": "https://github.com/" + repo + "/issues/" + str(number),
                "created_at": "2026-11-25T10:00:00+00:00",
                "updated_at": "2026-11-25T10:00:00+00:00"}
    proposal_issue = issue(300, rendered["title"], rendered["body"], 3000)
    root_issue = issue(53, "Root", "Root body", 530)
    repo_row = {"id": 911, "full_name": repo}
    args["proposal_admission"]["content_sha256"] = m.issue_revision(repo, repo_row, proposal_issue)
    args["root_admission"]["content_sha256"] = m.issue_revision(repo, repo_row, root_issue)
    args["root_admission"]["proposal_selection"]["revision"] = args["proposal_admission"]["content_sha256"]
    monkeypatch.setattr(m, "load_consumers", lambda: [
        {"consumer": "herdr", "repository": repo, "mode": "root_only", "root_issue": 53}])
    monkeypatch.setattr(m, "authenticated_user", lambda: (9, "reader"))
    monkeypatch.setattr(m, "fetch_json", lambda url: {
        api: repo_row, api + "/issues/300": proposal_issue,
        api + "/issues/53": root_issue,
    }[url])
    def approved(consumer, received):
        assert (consumer["mode"] == "all_open") == (received["number"] == 300)
        return received, args["proposal_admission"] if received["number"] == 300 else args["root_admission"]
    monkeypatch.setattr(m, "approved_revision", approved)
    result = m.prepare_chatgpt_proposal_binding(repo, 300)
    assert result["status"] == "VALIDATED_NOT_ADMITTED"
    assert not result["task_created"] and not result["execution_authorized"]
    assert result["binding"]["proposal_digest"] == args["proposal"].digest
    proposal_issue["body"] += "\nInjected"
    with pytest.raises(m.AdmissionDenied):
        m.prepare_chatgpt_proposal_binding(repo, 300)
