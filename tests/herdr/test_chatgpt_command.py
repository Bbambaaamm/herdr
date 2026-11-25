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
