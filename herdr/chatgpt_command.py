"""Pure ChatGPT-to-GitHub proposal envelope, deliberately NOT execution authority.

This pre-intake contract has no host/process/network/filesystem side effects.
Github issue creation is a separate user-authorized connector action; the
existing maintainer-comment-v1 and root-only #53 admission stay authoritative.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

VERSION = 1
ROOT_REPOSITORY = "Bbambaaamm/herdr"
ROOT_ISSUE = 53
MARKER = "HERDR-CHATGPT-PROPOSAL-V1"
OPERATIONS = frozenset({"inspect", "implement", "review"})
TARGET_KINDS = frozenset({"issue", "pull_request"})
MAX_BYTES = 8192
FIELDS = frozenset({
    "version", "repository", "root_issue", "operation", "target_kind",
    "target_number", "objective", "constraints"
})


class ProposalDenied(ValueError):
    """No execution authorization follows from this envelope."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, value in pairs:
        if key in data:
            raise ProposalDenied("duplicate_field")
        data[key] = value
    return data


def _deny_nonfinite(_: str) -> None:
    raise ProposalDenied("nonfinite_number")


def _text(value: Any, *, maximum: int) -> bool:
    return (type(value) is str and 1 <= len(value) <= maximum
            and value == value.strip()
            and not any(ord(char) < 32 or ord(char) == 127 for char in value)
            and not re.search(r"[\u202a-\u202e\u2066-\u2069]", value))


@dataclass(frozen=True)
class CommandProposal:
    operation: str
    target_kind: str
    target_number: int
    objective: str
    constraints: tuple[str, ...]

    @classmethod
    def parse(cls, raw: bytes) -> "CommandProposal":
        if not isinstance(raw, bytes) or len(raw) > MAX_BYTES or not raw:
            raise ProposalDenied("invalid_request_size")
        try:
            document = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                                  parse_constant=_deny_nonfinite)
        except (UnicodeError, ValueError, TypeError) as exc:
            raise ProposalDenied("invalid_request_json") from exc
        if type(document) is not dict or set(document) != FIELDS:
            raise ProposalDenied("closed_request_schema")
        if (type(document["version"]) is not int or document["version"] != VERSION
                or document["repository"] != ROOT_REPOSITORY
                or type(document["root_issue"]) is not int
                or document["root_issue"] != ROOT_ISSUE):
            raise ProposalDenied("untrusted_repository_or_root")
        if (type(document["operation"]) is not str or document["operation"] not in OPERATIONS
                or type(document["target_kind"]) is not str
                or document["target_kind"] not in TARGET_KINDS
                or type(document["target_number"]) is not int
                or not 1 <= document["target_number"] <= 2**31 - 1):
            raise ProposalDenied("invalid_operation_or_target")
        if not _text(document["objective"], maximum=1600):
            raise ProposalDenied("invalid_objective")
        constraints = document["constraints"]
        if (type(constraints) is not list or len(constraints) > 12
                or any(not _text(x, maximum=320) for x in constraints)
                or len(set(constraints)) != len(constraints)):
            raise ProposalDenied("invalid_constraints")
        proposal = cls(document["operation"], document["target_kind"],
                       document["target_number"], document["objective"], tuple(constraints))
        # The GitHub renderer escapes markdown backticks as six-byte JSON
        # Unicode escapes. Accept only requests that remain within the
        # authenticated issue reader's same MAX_BYTES envelope after rendering.
        if len(proposal._issue_json().encode("utf-8")) > MAX_BYTES:
            raise ProposalDenied("rendered_request_too_large")
        return proposal

    @classmethod
    def from_github_issue(cls, issue: dict[str, Any]) -> "CommandProposal":
        """Verify the entire canonical proposal body, never infer authorization."""
        if (type(issue) is not dict or issue.get("state") != "open"
                or "pull_request" in issue or type(issue.get("number")) is not int
                or issue["number"] <= 0
                or type(issue.get("title")) is not str
                or type(issue.get("body")) is not str
                or len(issue["body"].encode("utf-8")) > 16384):
            raise ProposalDenied("invalid_proposal_issue")
        body = issue["body"]
        marker = chr(96) * 3 + "json\n"
        tail = "\n" + chr(96) * 3 + "\n\n"
        try:
            json_part = body.split(marker, 1)[1].split(tail, 1)[0]
        except IndexError as exc:
            raise ProposalDenied("missing_proposal_envelope") from exc
        if len(json_part.encode("utf-8")) > MAX_BYTES:
            raise ProposalDenied("invalid_proposal_size")
        proposal = cls.parse(json_part.encode("utf-8"))
        expected = proposal.github_issue_proposal()
        if issue["title"] != expected["title"] or body != expected["body"]:
            raise ProposalDenied("proposal_changed_or_noncanonical")
        return proposal

    def request(self) -> dict[str, Any]:
        return {
            "version": VERSION, "repository": ROOT_REPOSITORY, "root_issue": ROOT_ISSUE,
            "operation": self.operation, "target_kind": self.target_kind,
            "target_number": self.target_number, "objective": self.objective,
            "constraints": list(self.constraints),
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(self.request(), sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()

    def _issue_json(self) -> str:
        request = json.dumps(self.request(), sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False)
        # Preserve JSON semantics while denying Markdown fence injection.
        return request.replace(chr(96), chr(92) + "u0060")

    def github_issue_proposal(self) -> dict[str, Any]:
        """Return inert issue text; never an admission marker or task submission."""
        title = (f"[Herdr proposal] {self.operation}: "
                 f"{self.target_kind} #{self.target_number} [{self.digest[:12]}]")
        request = self._issue_json()
        if len(request.encode("utf-8")) > MAX_BYTES:
            raise ProposalDenied("rendered_request_too_large")
        body = (f"{MARKER}\n\n"
                f"Request SHA-256: `{self.digest}`\n\n"
                "Status: PROPOSED_ONLY — not approved, queued or executing.\n\n"
                f"Control issue: #{ROOT_ISSUE}.\n"
                "No authority is granted by this issue, its author, its labels, "
                "its text, or a ChatGPT message.\n\n"
                "```json\n" + request + "\n```\n\n"
                "Next gate: existing maintainer-comment-v1 approval and "
                "Herdr root-only intake, after independent verification.\n")
        return {
            "repository": ROOT_REPOSITORY, "title": title, "body": body,
            "request_sha256": self.digest, "status": "PROPOSED_ONLY",
            "execution_authorized": False, "root_issue": ROOT_ISSUE,
        }
