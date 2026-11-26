"""Pure proposal-to-root admission preflight; does not issue execution authority.

Only the existing intake may consume a maintainer approval and publish a task.
This validation can accompany that protected transaction after its runtime
owner/fencing and incident checks have been independently satisfied.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .chatgpt_command import CommandProposal, ROOT_ISSUE, ROOT_REPOSITORY

_HEX = re.compile(r"^[0-9a-f]{64}$")


class ProposalBindingDenied(ValueError):
    pass


def _positive(value):
    return type(value) is int and 0 < value <= 2**63 - 1


def _hex(value):
    return type(value) is str and _HEX.fullmatch(value) is not None


def _admission(value, *, issue_number, issue_id, issue_digest):
    """Validate existing maintainer-comment-v1 verified admission receipt."""
    required = {
        "version", "approval_id", "content_sha256", "repository_id",
        "issue_id", "approver_user_id", "approver_login", "approved_at",
        "expires_at", "issue_updated_at",
    }
    keys = set(value) if type(value) is dict else set()
    if keys not in (required, required | {"proposal_selection"}):
        raise ProposalBindingDenied("admission_receipt_shape")
    if (type(value["version"]) is not int or value["version"] != 1
            or not _positive(value["approval_id"])
            or not _positive(value["repository_id"])
            or not _positive(value["approver_user_id"])
            or type(value["issue_id"]) is not int or value["issue_id"] != issue_id
            or not _hex(value["content_sha256"])
            or value["content_sha256"] != issue_digest
            or type(value["approver_login"]) is not str
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", value["approver_login"])
            or any(type(value[x]) is not str or len(value[x]) > 64 or not value[x]
                   for x in ("approved_at", "expires_at", "issue_updated_at"))):
        raise ProposalBindingDenied("admission_receipt_invalid")
    return value


@dataclass(frozen=True)
class ProposalAdmissionBinding:
    """Immutable evidence correlation, NOT a queue command or grant."""
    proposal_issue: int
    proposal_issue_id: int
    proposal_digest: str
    proposal_revision: str
    proposal_approval_id: int
    root_approval_id: int
    root_revision: str
    operation: str
    target_kind: str
    target_number: int

    def evidence(self):
        payload = {
            "version": 1, "repository": ROOT_REPOSITORY,
            "root_issue": ROOT_ISSUE,
            "proposal_issue": self.proposal_issue,
            "proposal_issue_id": self.proposal_issue_id,
            "proposal_digest": self.proposal_digest,
            "proposal_revision": self.proposal_revision,
            "proposal_approval_id": self.proposal_approval_id,
            "root_approval_id": self.root_approval_id,
            "root_revision": self.root_revision,
            "operation": self.operation, "target_kind": self.target_kind,
            "target_number": self.target_number,
        }
        payload["binding_sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return payload


def prepare_admission_binding(
    *, proposal: CommandProposal, proposal_issue: int, proposal_issue_id: int,
    proposal_revision: str, proposal_admission: dict,
    root_revision: str, root_admission: dict,
    consumed_proposals: set[tuple[int, str]] | None = None,
) -> ProposalAdmissionBinding:
    """Compose two independently verified GitHub approvals with no side effects.

    The caller MUST first run existing approved_revision() for the proposal
    issue and the root #53 issue. Neither provided dict is self-authenticating:
    this function is only safe after the trusted GitHub intake produces them.
    """
    if (type(proposal) is not CommandProposal or not _positive(proposal_issue)
            or proposal_issue == ROOT_ISSUE or not _positive(proposal_issue_id)
            or not _hex(proposal_revision) or not _hex(root_revision)):
        raise ProposalBindingDenied("invalid_proposal_identity")
    _admission(proposal_admission, issue_number=proposal_issue,
               issue_id=proposal_issue_id, issue_digest=proposal_revision)
    root_id = root_admission.get("issue_id") if type(root_admission) is dict else None
    if not _positive(root_id):
        raise ProposalBindingDenied("root_identity_missing")
    _admission(root_admission, issue_number=ROOT_ISSUE,
               issue_id=root_id, issue_digest=root_revision)
    if proposal_admission["repository_id"] != root_admission["repository_id"]:
        raise ProposalBindingDenied("repository_identity_mismatch")
    if "proposal_selection" in proposal_admission:
        raise ProposalBindingDenied("selection_must_be_root_only")
    expected_selection = {
        "issue_number": proposal_issue,
        "issue_id": proposal_issue_id,
        "digest": proposal.digest,
        "revision": proposal_revision,
    }
    if root_admission.get("proposal_selection") != expected_selection:
        raise ProposalBindingDenied("root_approval_selection_missing_or_mismatched")
    try:
        proposal_time = datetime.fromisoformat(
            proposal_admission["approved_at"].replace("Z", "+00:00"))
        root_time = datetime.fromisoformat(
            root_admission["approved_at"].replace("Z", "+00:00"))
        if proposal_time.tzinfo is None or root_time.tzinfo is None:
            raise ValueError("timezone required")
    except ValueError as exc:
        raise ProposalBindingDenied("approval_time_invalid") from exc
    if not proposal_time.astimezone(timezone.utc) < root_time.astimezone(timezone.utc):
        raise ProposalBindingDenied("root_approval_must_follow_proposal")
    if consumed_proposals is None:
        raise ProposalBindingDenied("durable_dedup_evidence_required")
    if (proposal_issue, proposal.digest) in consumed_proposals:
        raise ProposalBindingDenied("proposal_already_consumed")
    return ProposalAdmissionBinding(
        proposal_issue, proposal_issue_id, proposal.digest, proposal_revision,
        proposal_admission["approval_id"], root_admission["approval_id"],
        root_revision, proposal.operation, proposal.target_kind,
        proposal.target_number,
    )
