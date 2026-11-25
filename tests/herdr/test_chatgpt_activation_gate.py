"""Explicit selection on existing root approval; no background worker launch."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

import pytest

from herdr.chatgpt_command import CommandProposal
from test_chatgpt_admission_binding import fixture

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack/bin/agent-github-intake"


@pytest.fixture
def m(monkeypatch):
    loader = importlib.machinery.SourceFileLoader("chatgpt_activation_gate_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setattr(module, "authenticated_user", lambda: (1, "reader"))
    return module


def test_explicit_root_selected_comment_validates_and_keeps_legacy_working(m, monkeypatch):
    args = fixture()
    root = "Bbambaaamm/herdr"
    api = "https://api.github.com/repos/" + root
    proposal = args["proposal"].github_issue_proposal()
    repo = {"id": 911, "full_name": root}
    def issue(number, title, body, ident, comments=1):
        return {
            "number": number, "id": ident, "state": "open",
            "title": title, "body": body, "comments": comments,
            "repository_url": api, "url": f"{api}/issues/{number}",
            "html_url": f"https://github.com/{root}/issues/{number}",
            "created_at": "2026-11-25T10:00:00Z",
            "updated_at": "2026-11-25T10:00:00Z",
        }
    prop = issue(300, proposal["title"], proposal["body"], 3000)
    root_issue = issue(53, "Control", "Root contract", 530)
    digest = m.issue_revision(root, repo, root_issue)
    pdigest = m.issue_revision(root, repo, prop)
    selection = {
        "issue_number": 300, "issue_id": 3000,
        "digest": args["proposal"].digest, "revision": pdigest,
    }
    def approval(issue_number, ident, revision, selection=None):
        value = {
            "action": "approve", "repository": root, "issue_number": issue_number,
            "issue_id": ident, "content_sha256": revision,
            "expires_at": "2026-11-25T12:25:00Z",
        }
        if selection is not None:
            value["proposal_selection"] = selection
        return m.APPROVAL_MARKER + json.dumps(value)
    def comment(number, ident, content, created):
        return {
            "id": ident, "body": content, "issue_url": f"{api}/issues/{number}",
            "user": {"id": 3, "login": "approver", "type": "User"},
            "created_at": created, "updated_at": created,
        }
    cproposal = comment(300, 3100, approval(300, 3000, pdigest), "2026-11-25T12:00:00Z")
    croot = comment(53, 5400, approval(53, 530, digest, selection),
                    "2026-11-25T12:02:00Z")
    rows = {
        api: repo,
        f"{api}/issues/53": root_issue,
        f"{api}/issues/300": prop,
        f"{api}/issues/53/comments?per_page=100&page=1": [croot],
        f"{api}/issues/300/comments?per_page=100&page=1": [cproposal],
        f"{api}/collaborators/approver/permission": {
            "role_name": "maintain", "permission": "write",
            "user": {"id": 3, "login": "approver", "type": "User"},
        }
    }
    monkeypatch.setattr(m, "fetch_json", lambda url: rows[url])
    monkeypatch.setattr(m, "now", lambda: m.datetime.fromisoformat("2026-11-25T12:03:00+00:00"))
    consumer = {
        "consumer": "herdr", "repository": root, "mode": "root_only",
        "root_issue": 53, "admission": {
            "signal": "maintainer-comment-v1", "max_age_seconds": 86400,
        }
    }
    proposal_consumer = {**consumer, "mode": "all_open"}
    verified_proposal, original = m.approved_revision(proposal_consumer, prop)
    assert original["approval_id"] == 3100 and "proposal_selection" not in original
    verified_root, selected = m.approved_revision(consumer, root_issue)
    assert selected["proposal_selection"] == selection
    assert verified_root["id"] == 530
    assert m.issue_revision(root, repo, verified_proposal) == pdigest
    actual = m.prepare_chatgpt_proposal_binding.__name__
    assert actual == "prepare_chatgpt_proposal_binding"
    monkeypatch.setattr(m, "load_consumers", lambda: [consumer])
    bound = m.prepare_chatgpt_proposal_binding(root, 300)
    assert bound["status"] == "VALIDATED_NOT_ADMITTED"
    assert bound["binding"]["proposal_digest"] == args["proposal"].digest
    assert not bound["execution_authorized"]
    # Canonical root selection is available for the existing read-only helper.
    monkeypatch.setattr(m.sys, "argv", ["agent-github-intake", "--approval-digest",
                                       root, "53", "--select-proposal", "300"])
    output = StringIO()
    with redirect_stdout(output):
        assert m.main() == 0
    generated = json.loads(output.getvalue())
    assert generated["read_only"] and not generated["task_created"]
    assert json.loads(generated["approval_body"].split("\n", 1)[1])["proposal_selection"] == selection
    # An unselected root cycle remains supported only with an ordinary root
    # approval. Selected approval may not be consumed without the binding.
    assert selected["proposal_selection"] == selection
