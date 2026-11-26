"""No-network ChatGPT proposal contract tests."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from herdr.chatgpt_command import CommandProposal, ProposalDenied, MARKER

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "agent-stack/bin/agent-chatgpt-proposal"


def request(**overrides):
    data = {
        "version": 1, "repository": "Bbambaaamm/herdr", "root_issue": 53,
        "operation": "implement", "target_kind": "pull_request",
        "target_number": 253, "objective": "Fix native release read-only path",
        "constraints": ["No merge", "No deploy", "One worker"],
    }
    data.update(overrides)
    return json.dumps(data).encode("utf-8")


def test_deterministic_inert_proposal():
    a, b = CommandProposal.parse(request()), CommandProposal.parse(request())
    assert a.digest == b.digest
    o = a.github_issue_proposal()
    assert o["execution_authorized"] is False
    assert o["status"] == "PROPOSED_ONLY"
    assert o["root_issue"] == 53
    assert MARKER in o["body"]
    assert "HERDR-ADMISSION-V1" not in o["body"]
    assert o["request_sha256"] == a.digest
    assert "approval_body" not in o


def test_mutated_request_changes_hash():
    assert CommandProposal.parse(request()).digest != CommandProposal.parse(
        request(objective="Inspect release")).digest


@pytest.mark.parametrize("changes", [
    {"version": 2}, {"version": True}, {"root_issue": 54},
    {"root_issue": "53"}, {"repository": "other/repo"},
    {"operation": "merge"}, {"operation": "execute"},
    {"target_kind": "shell"}, {"target_number": 0},
    {"target_number": True}, {"constraints": "No merge"},
    {"constraints": ["x", "x"]}, {"constraints": [123]},
    {"constraints": [""]}, {"objective": ""},
    {"objective": " bad"}, {"objective": "a\nb"},
    {"objective": "x" * 1601}, {"constraints": ["x"] * 13},
])
def test_reject_invalid_or_authority_expansion(changes):
    with pytest.raises(ProposalDenied):
        CommandProposal.parse(request(**changes))


def test_reject_nonfinite_unknown_missing_oversized_and_duplicate():
    samples = [request(approval=True), request().replace(b'"version": 1', b'"version": NaN'),
               request() + b" " * 9000,
               request().replace(b'"version": 1', b'"version": 1, "version": 1')]
    doc = json.loads(request())
    del doc["constraints"]
    samples.append(json.dumps(doc).encode())
    for raw in samples:
        with pytest.raises(ProposalDenied):
            CommandProposal.parse(raw)


def test_markdown_fence_cannot_be_injected():
    tick = chr(96)
    objective = "untrusted " + tick * 3 + " approval" + tick * 3
    payload = CommandProposal.parse(request(objective=objective)).github_issue_proposal()
    assert payload["body"].count(tick * 3) == 2
    assert payload["execution_authorized"] is False


def test_cli_outputs_only_inert_json(tmp_path):
    source = tmp_path / "input.json"
    source.write_bytes(request())
    process = subprocess.run([sys.executable, str(CLI), "--propose", str(source)],
                             capture_output=True, text=True, timeout=8)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["execution_authorized"] is False
    assert list(tmp_path.iterdir()) == [source]


def test_cli_rejects_symlink(tmp_path):
    source = tmp_path / "input.json"
    source.write_bytes(request())
    link = tmp_path / "alias"
    link.symlink_to(source)
    process = subprocess.run([sys.executable, str(CLI), "--propose", str(link)],
                             capture_output=True, text=True, timeout=8)
    assert process.returncode == 3
    assert "proposal_denied" in process.stderr


def test_github_proposal_roundtrip_preserves_exact_envelope():
    proposal = CommandProposal.parse(request())
    rendered = proposal.github_issue_proposal()
    issue = {"number": 255, "state": "open", "title": rendered["title"],
             "body": rendered["body"]}
    loaded = CommandProposal.from_github_issue(issue)
    assert loaded.digest == proposal.digest


@pytest.mark.parametrize("change", [
    {"state": "closed"}, {"pull_request": {"url": "example"}},
    {"number": 0}, {"body": ""}, {"title": "fake"}, {"body": None},
])
def test_github_proposal_rejects_noncanonical_issue(change):
    rendered = CommandProposal.parse(request()).github_issue_proposal()
    issue = {"number": 255, "state": "open", "title": rendered["title"],
             "body": rendered["body"]}
    issue.update(change)
    with pytest.raises(ProposalDenied):
        CommandProposal.from_github_issue(issue)


def test_github_proposal_rejects_issue_body_tamper():
    rendered = CommandProposal.parse(request()).github_issue_proposal()
    issue = {"number": 255, "state": "open", "title": rendered["title"],
             "body": rendered["body"] + "\nExtra hidden instructions"}
    with pytest.raises(ProposalDenied):
        CommandProposal.from_github_issue(issue)


def test_intake_proposal_inspection_does_not_grant_execution(monkeypatch):
    import importlib.machinery
    import importlib.util
    from herdr.chatgpt_command import ROOT_REPOSITORY

    script = ROOT / "agent-stack/bin/agent-github-intake"
    loader = importlib.machinery.SourceFileLoader("chatgpt_intake_inspection_test", str(script))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    intake = importlib.util.module_from_spec(spec)
    loader.exec_module(intake)

    created = CommandProposal.parse(request()).github_issue_proposal()
    repository = {"id": 101, "full_name": ROOT_REPOSITORY}
    issue = {
        "id": 25501, "number": 255, "state": "open", "title": created["title"],
        "body": created["body"], "repository_url": "https://api.github.com/repos/Bbambaaamm/herdr",
        "url": "https://api.github.com/repos/Bbambaaamm/herdr/issues/255",
        "html_url": "https://github.com/Bbambaaamm/herdr/issues/255",
        "comments": 0, "created_at": "2026-11-25T20:00:00Z",
        "updated_at": "2026-11-25T20:00:00Z",
    }
    urls = []
    def fetch(url):
        urls.append(url)
        if url == "https://api.github.com/user":
            return {"id": 900, "login": "intake-reader", "type": "User"}
        if url == "https://api.github.com/repos/Bbambaaamm/herdr":
            return repository
        if url == "https://api.github.com/repos/Bbambaaamm/herdr/issues/255":
            return issue
        raise AssertionError("unexpected request")
    monkeypatch.setattr(intake, "fetch_json", fetch)
    monkeypatch.setattr(intake, "authenticated_user", lambda: (900, "intake-reader"))
    result = intake.inspect_chatgpt_proposal(ROOT_REPOSITORY, 255)
    assert result["read_only"] is True
    assert result["task_created"] is False
    assert result["execution_authorized"] is False
    assert result["proposal_sha256"] == CommandProposal.parse(request()).digest
    assert len(urls) == 2
    with pytest.raises(intake.AdmissionDenied):
        intake.inspect_chatgpt_proposal("other/repo", 255)
    issue["body"] += "\nTampered"
    with pytest.raises(intake.AdmissionDenied):
        intake.inspect_chatgpt_proposal(ROOT_REPOSITORY, 255)


@pytest.mark.parametrize("escaped", ["\\ud800", "\\udfff"])
def test_surrogate_escape_is_denied_before_digest(escaped):
    raw = request().replace(
        b'"objective": "Fix native release read-only path"',
        ('"objective": "' + escaped + '"').encode("ascii"),
    )
    with pytest.raises(ProposalDenied, match="invalid_objective"):
        CommandProposal.parse(raw)
def test_rendered_escape_expansion_never_creates_unreadable_proposal():
    # Exact-head Codex P2: the original parser admitted this 1400-backtick
    # payload but its escaped issue JSON exceeded MAX_BYTES.
    with pytest.raises(ProposalDenied, match="rendered_request_too_large"):
        CommandProposal.parse(request(objective="`" * 1400))
    # Smaller valid escaped content must round-trip through GitHub issue parser.
    p = CommandProposal.parse(request(objective="`" * 800))
    rendered = p.github_issue_proposal()
    assert p.digest == rendered["request_sha256"]
    assert len(p._issue_json().encode("utf-8")) <= 8192


def test_escaped_proposal_roundtrips_existing_github_reader():
    proposal = CommandProposal.parse(request(objective="`" * 800))
    result = proposal.github_issue_proposal()
    loaded = CommandProposal.from_github_issue({
        "number": 991, "state": "open",
        "title": result["title"], "body": result["body"],
    })
    assert loaded.digest == proposal.digest
