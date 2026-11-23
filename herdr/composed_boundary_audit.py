"""Read-only composed-execution boundary audit; never an authority.

The audit answers one narrow question about already recorded, host-owned
evidence: do the five bound artifacts (role graph, policy, ordered action
trace, approval ledger, reviewer evidence) *cover* the composed execution
boundary, or do they contain a contradiction?

Design bounds (issue #76 proposal comment 2026-11-22T07:55:27Z):

* no new safety gate - the result cannot authorize, widen or bypass any
  ``SecurityGrant``/``RuntimeAssurance`` decision;
* purely offline over immutable artifacts supplied by the caller - no agent,
  model, network, filesystem or clock access;
* missing or unreadable evidence is ``UNKNOWN``, never a silent pass;
* digests are recomputed over canonical JSON, so a mutated artifact cannot be
  presented under an older digest.

Interface (unchanged from the proposal):
``audit_composed_boundaries(graph_sha256, policy_sha256, action_trace_sha256,
approval_ledger_sha256, evidence_sha256) -> ComposedSafetyCoverageV1``.

The five positional digests are the public contract.  The matching artifacts
are optional keyword arguments; a caller that supplies digests only receives
``UNKNOWN`` with ``artifact_missing`` findings instead of a fabricated pass.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .security import SecurityError, canonical_digest

VERSION = "herdr-composed-boundary-audit-1"

SCHEMA_GRAPH = "herdr-composed-boundary-graph-1"
SCHEMA_POLICY = "herdr-composed-boundary-policy-1"
SCHEMA_ACTION_TRACE = "herdr-composed-action-trace-1"
SCHEMA_APPROVAL_LEDGER = "herdr-composed-approval-ledger-1"
SCHEMA_EVIDENCE = "herdr-composed-boundary-evidence-1"

ARTIFACTS = ("graph", "policy", "action_trace", "approval_ledger", "evidence")

# Approval requirement follows the known RiskClass set in ``herdr/security.py``
# (``RiskClass`` is a ``StrEnum`` of lowercase values); anything outside it is
# evidence we cannot classify, so it is never silently treated as a low-risk
# action that needs no approval.
APPROVAL_RISK_CLASSES = frozenset((
    "read",
    "workspace_write",
    "delegation",
    "result_submission",
    "process",
    "external_side_effect",
    "credential_use",
    "physical",
))

_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ComposedSafetyCoverageV1:
    """Three-valued coverage result; ``VIOLATION``/``UNKNOWN`` are not safe."""

    status: str
    violations: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    metrics: Mapping[str, int] = field(default_factory=dict)
    digests: Mapping[str, str] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": VERSION,
            "status": self.status,
            "violations": list(self.violations),
            "unknowns": list(self.unknowns),
            "metrics": dict(self.metrics),
            "digests": dict(self.digests),
            "authoritative": False,
            "native_e2e_accepted": False,
        }


def _result(status: str, violations=(), unknowns=(), **metrics: int) -> ComposedSafetyCoverageV1:
    return ComposedSafetyCoverageV1(
        status=status,
        violations=tuple(dict.fromkeys(violations)),
        unknowns=tuple(dict.fromkeys(unknowns)),
        metrics={name: int(value) for name, value in sorted(metrics.items())},
    )


def _text(value: Any, name: str) -> str | None:
    return value if isinstance(value, str) and value else None


def _sha(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.match(value))


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(_text(item, "item") is not None for item in value)


def _epoch(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _normalize_abs_path(path: str) -> str | None:
    """Canonical absolute POSIX path, or ``None`` for ambiguous/escaping input.

    Only lexical normalization is performed; no filesystem is consulted.  A
    path that is not absolute, that contains a ``..`` segment, a NUL byte, a
    repeated separator or a trailing separator is rejected rather than
    silently reduced to an equivalent-looking path.
    """
    if not path.startswith("/") or "\x00" in path:
        return None
    if path == "/":
        return path
    if "//" in path or path.endswith("/") and path != "/":
        return None
    parts = path.split("/")[1:]
    if "." in parts or ".." in parts or "" in parts:
        return None
    return "/" + "/".join(parts)


def _path_within(path: Any, roots: Any) -> bool:
    """POSIX path containment; only absolute granted roots are honored.

    Both the candidate path and every root are lexically normalized first, so
    ``/ws/../etc/passwd`` can never be presented as contained in a grant of
    ``/ws``.
    """
    if not isinstance(path, str):
        return False
    target = _normalize_abs_path(path)
    if target is None:
        return False
    if not isinstance(roots, (list, tuple, set, frozenset)):
        return False
    for root in roots:
        if not isinstance(root, str):
            continue
        base = _normalize_abs_path(root)
        if base is None:
            continue
        if target == base or base == "/" or target.startswith(base + "/"):
            return True
    return False


def _ancestor(nodes: Mapping[str, Mapping[str, Any]], node_id: str, other: str) -> bool:
    """True when ``other`` is ``node_id`` or one of its ancestors."""
    seen: set[str] = set()
    current: str | None = node_id
    while current is not None and current not in seen:
        if current == other:
            return True
        seen.add(current)
        row = nodes.get(current)
        current = row.get("parent_id") if isinstance(row, dict) else None
    return False


def _subtree(nodes: Mapping[str, Mapping[str, Any]], root: str) -> set[str]:
    children: dict[str, set[str]] = {}
    for node_id, row in nodes.items():
        parent = row.get("parent_id") if isinstance(row, dict) else None
        children.setdefault(parent, set()).add(node_id)
    out: set[str] = set()
    stack = [root]
    while stack:
        current = stack.pop()
        if current in out:
            continue
        out.add(current)
        stack.extend(children.get(current, ()))
    return out


def _has_cycle(nodes: Mapping[str, Mapping[str, Any]]) -> bool:
    """True when some node's parent chain revisits itself.

    A parent-child cycle makes ancestry and subtree scope ill-defined, so it is
    a structural contradiction rather than an execution to be scored.
    """
    for node_id in nodes:
        seen: set[str] = set()
        current: str | None = node_id
        while current is not None and current in nodes:
            if current in seen:
                return True
            seen.add(current)
            current = nodes[current].get("parent_id")
    return False


def _evaluate(graph, policy, action_trace, approval_ledger, evidence,
              declared: Mapping[str, str]) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, int]]:
    """Structural and composition checks.

    ``violations`` are contradictions; ``unknowns`` record an effect the
    artifacts do not describe.  Neither is a pass: an unknown never degrades
    into ``COVERED``.
    """
    bad: list[str] = []
    unknowns: list[str] = []

    schemas = {
        "graph": (graph, SCHEMA_GRAPH),
        "policy": (policy, SCHEMA_POLICY),
        "action_trace": (action_trace, SCHEMA_ACTION_TRACE),
        "approval_ledger": (approval_ledger, SCHEMA_APPROVAL_LEDGER),
        "evidence": (evidence, SCHEMA_EVIDENCE),
    }
    for name, (artifact, expected) in schemas.items():
        if artifact.get("schema_version") != expected:
            unknowns.append(f"{name}_schema_unsupported")
    for name, artifact in (("graph", graph), ("policy", policy)):
        if not _epoch(artifact.get("epoch")):
            unknowns.append(f"{name}_epoch_invalid")

    nodes_raw = graph.get("nodes")
    grants_raw = policy.get("grants")
    steps_raw = action_trace.get("steps")
    entries_raw = approval_ledger.get("entries")
    if not isinstance(nodes_raw, list) or not nodes_raw:
        return (("graph_nodes_missing",), (), {})
    if not isinstance(grants_raw, dict) or not grants_raw:
        return (("policy_grants_missing",), (), {})
    if not isinstance(steps_raw, list):
        return (("action_trace_steps_missing",), (), {})
    if not isinstance(entries_raw, list):
        return (("approval_ledger_entries_missing",), (), {})

    nodes: dict[str, dict[str, Any]] = {}
    for row in nodes_raw:
        if not isinstance(row, dict):
            bad.append("graph_node_not_object")
            continue
        node_id = _text(row.get("id"), "node.id")
        if node_id is None or node_id in nodes:
            bad.append("graph_node_identity_invalid")
            continue
        if row.get("parent_id") is not None and _text(row.get("parent_id"), "node.parent_id") is None:
            bad.append("graph_parent_invalid")
        if _text(row.get("role"), "node.role") is None:
            unknowns.append("node_role_invalid")
        if "tools" not in row:
            unknowns.append("node_tools_missing")
        elif not _strings(row["tools"]):
            unknowns.append("node_tools_invalid")
        if not _strings(row.get("permissions")):
            unknowns.append("node_permissions_invalid")
        nodes[node_id] = row
    if bad:
        return (tuple(bad), tuple(unknowns), {})

    grants: dict[str, dict[str, Any]] = {}
    for key, row in grants_raw.items():
        if not isinstance(key, str) or not _sha(key) or not isinstance(row, dict):
            bad.append("policy_grant_invalid")
            continue
        if not _sha(row.get("identity_sha256")):
            unknowns.append("grant_identity_sha256_invalid")
        if not _strings(row.get("credential_refs")):
            unknowns.append("grant_credential_refs_invalid")
        roots = row.get("write_roots")
        if not _strings(roots) or any(_normalize_abs_path(root) is None for root in roots):
            unknowns.append("grant_write_roots_invalid")
        if not _strings(row.get("risk_classes")):
            unknowns.append("grant_risk_classes_invalid")
        approvals = row.get("approvals")
        if not isinstance(approvals, list) or any(
            not isinstance(item, dict)
            or _text(item.get("approval_id"), "approval.id") is None
            or _text(item.get("tool"), "approval.tool") is None
            for item in approvals
        ):
            unknowns.append("grant_approvals_invalid")
        grants[key] = row
    if bad:
        return (tuple(bad), tuple(unknowns), {})

    for node_id, row in nodes.items():
        parent = row.get("parent_id")
        if parent is not None and parent not in nodes:
            bad.append("graph_parent_unknown")
        grant = row.get("grant_sha256")
        if not _sha(grant) or grant not in grants:
            bad.append("node_grant_unbound")
    if bad:
        return (tuple(bad), tuple(unknowns), {})

    # Later scope checks require all of these fields to have a known shape.
    if unknowns:
        return ((), tuple(unknowns), {})

    if _has_cycle(nodes):
        bad.append("graph_role_cycle")
        return (tuple(bad), (), {})

    steps: list[dict[str, Any]] = []
    for row in steps_raw:
        if not isinstance(row, dict) or _text(row.get("node_id"), "step.node_id") is None:
            bad.append("action_step_invalid")
            continue
        seq = row.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
            bad.append("action_step_seq_invalid")
            continue
        if _text(row.get("tool"), "step.tool") is None:
            unknowns.append("action_step_tool_invalid")
        if not _sha(row.get("args_sha256")):
            unknowns.append("action_step_args_sha256_invalid")
        steps.append(row)
    entries: list[dict[str, Any]] = []
    for row in entries_raw:
        if not isinstance(row, dict):
            bad.append("approval_entry_invalid")
            continue
        if (any(_text(row.get(name), f"entry.{name}") is None
                for name in ("approval_id", "node_id", "tool"))
                or not _sha(row.get("args_sha256"))
                or not _sha(row.get("grant_sha256"))
                or isinstance(row.get("seq"), bool)
                or not isinstance(row.get("seq"), int)
                or row["seq"] < 0
                or not isinstance(row.get("consumed"), bool)):
            bad.append("approval_entry_malformed")
            continue
        entries.append(row)

    # Ordered cross-artifact references: a stale or replayed artifact cannot be
    # substituted for the one the trace was built against.
    if graph.get("policy_sha256") != declared["policy"]:
        bad.append("graph_policy_reference_mismatch")
    if action_trace.get("graph_sha256") != declared["graph"]:
        bad.append("action_trace_graph_reference_mismatch")
    if approval_ledger.get("graph_sha256") != declared["graph"]:
        bad.append("approval_ledger_graph_reference_mismatch")
    if evidence.get("action_trace_sha256") != declared["action_trace"]:
        bad.append("evidence_action_trace_reference_mismatch")
    # Reviewer evidence must record an independent review and its result, and
    # must be bound to the approval ledger it vouches for; otherwise a mutated
    # ledger could be evaluated against evidence that never reviewed it.
    if evidence.get("approval_ledger_sha256") != declared["approval_ledger"]:
        bad.append("evidence_approval_ledger_reference_mismatch")
    reviewer = evidence.get("reviewer")
    if not isinstance(reviewer, dict) or _text(reviewer.get("actor_id"), "evidence.reviewer.actor_id") is None:
        bad.append("evidence_reviewer_invalid")
    elif reviewer.get("independent") is not True:
        bad.append("evidence_reviewer_not_independent")
    if isinstance(reviewer, dict):
        if "result" not in reviewer:
            unknowns.append("review_result_missing")
        elif reviewer["result"] == "rejected":
            bad.append("review_result_rejected")
        elif reviewer["result"] != "accepted":
            unknowns.append("review_result_invalid")
    if not _sha(evidence.get("artifact_result_sha256")):
        bad.append("evidence_review_result_invalid")

    graph_epoch = graph.get("epoch")
    policy_epoch = policy.get("epoch")
    if graph_epoch != policy_epoch:
        bad.append("graph_policy_epoch_mismatch")
        if policy_epoch > graph_epoch:
            bad.append("stale_permission_epoch")

    # Parent-child scope: a child may never hold credentials or write roots its
    # parent does not hold (grant scope is a mathematical subset).
    for node_id, row in nodes.items():
        parent_id = row.get("parent_id")
        if parent_id is None:
            continue
        child_grant = grants[row["grant_sha256"]]
        parent_grant = grants[nodes[parent_id]["grant_sha256"]]
        child_creds = set(child_grant.get("credential_refs") or ())
        parent_creds = set(parent_grant.get("credential_refs") or ())
        child_roots = set(child_grant.get("write_roots") or ())
        parent_roots = set(parent_grant.get("write_roots") or ())
        if not child_creds <= parent_creds:
            bad.append("child_credential_scope_exceeds_parent")
        if any(not _path_within(root, parent_roots) for root in child_roots):
            bad.append("child_write_scope_exceeds_parent")

    # Credential confinement: one credential must not be usable from two
    # mutually independent branches of the role graph.
    holders: dict[str, list[str]] = {}
    for node_id, row in nodes.items():
        for ref in grants[row["grant_sha256"]].get("credential_refs") or ():
            if isinstance(ref, str):
                holders.setdefault(ref, []).append(node_id)
    for ref, node_ids in holders.items():
        for index, left in enumerate(node_ids):
            for right in node_ids[index + 1:]:
                if not _ancestor(nodes, left, right) and not _ancestor(nodes, right, left):
                    bad.append("credential_shared_across_branches")

    # Every step must belong to a recorded node; otherwise the trace describes
    # an execution the graph never admitted.
    for step in steps:
        if step["node_id"] not in nodes:
            bad.append("action_step_unknown_node")
    if bad:
        return (tuple(bad), tuple(unknowns), {})

    for step in steps:
        if step.get("tool") not in nodes[step["node_id"]]["tools"]:
            bad.append("action_step_tool_not_permitted")

    # Individually permitted writes can still compose into a wider blast radius:
    # the union of a subtree's recorded writes must stay inside that subtree
    # root's granted write roots.
    writes_by_node: dict[str, set[str]] = {}
    for step in steps:
        paths = step.get("write_paths")
        if paths is None:
            # A step that does not declare its write effect cannot be checked
            # for scope; that is missing evidence, not a recorded no-write.
            unknowns.append("action_step_write_paths_missing")
            continue
        if not isinstance(paths, list) or any(not isinstance(p, str) or not p for p in paths):
            bad.append("action_step_write_paths_invalid")
            continue
        if any(_normalize_abs_path(path) is None for path in paths):
            bad.append("action_step_write_path_invalid")
        writes_by_node.setdefault(step["node_id"], set()).update(paths)
    for node_id in nodes:
        allowed = set(grants[nodes[node_id]["grant_sha256"]].get("write_roots") or ())
        combined: set[str] = set()
        for member in _subtree(nodes, node_id):
            combined |= writes_by_node.get(member, set())
        if any(not _path_within(path, allowed) for path in combined):
            bad.append("composed_write_scope_exceeded")

    # Two independent agents writing the same path is an interacting-write
    # conflict even when each write is individually granted.
    path_owners: dict[str, list[tuple[str, int]]] = {}
    for step in steps:
        for path in writes_by_node.get(step["node_id"], ()):  # type: ignore[arg-type]
            path_owners.setdefault(path, []).append((step["node_id"], step["seq"]))
    conflicts = 0
    for owners in path_owners.values():
        for index, (left, _) in enumerate(owners):
            for right, _ in owners[index + 1:]:
                if not _ancestor(nodes, left, right) and not _ancestor(nodes, right, left):
                    conflicts += 1
    if conflicts:
        bad.append("concurrent_interacting_writes")

    # Approval ledger: entries must be well formed, bound to a recorded grant,
    # declared by the grant's own approval inventory, and consumed exactly once.
    by_approval: dict[str, int] = {}
    consumed: dict[str, bool] = {}
    for entry in entries:
        approval_id = _text(entry.get("approval_id"), "entry.approval_id")
        node_id = _text(entry.get("node_id"), "entry.node_id")
        tool = _text(entry.get("tool"), "entry.tool")
        args = entry.get("args_sha256")
        grant = entry.get("grant_sha256")
        seq = entry.get("seq")
        if (approval_id is None or node_id is None or tool is None or not _sha(args)
                or not _sha(grant) or isinstance(seq, bool) or not isinstance(seq, int)
                or seq < 0 or not isinstance(entry.get("consumed"), bool)):
            bad.append("approval_entry_malformed")
            continue
        if node_id not in nodes or grant != nodes[node_id]["grant_sha256"]:
            bad.append("approval_grant_mismatch")
        grant_row = grants.get(grant)
        recorded = grant_row.get("approvals") if isinstance(grant_row, dict) else None
        known = ({item["approval_id"]: item["tool"] for item in recorded}
                 if isinstance(recorded, list) else {})
        if approval_id not in known:
            bad.append("false_accepted_approval")
        elif known[approval_id] != tool:
            bad.append("approval_inventory_tool_mismatch")
        by_approval[approval_id] = by_approval.get(approval_id, 0) + 1
        if entry.get("consumed") is True:
            consumed[approval_id] = True
    false_approvals = sum(1 for code in bad if code == "false_accepted_approval")
    replays = sum(1 for count in by_approval.values() if count > 1)
    if replays:
        bad.append("replayed_approval")
    unconsumed = sum(1 for approval_id in by_approval if not consumed.get(approval_id))
    if unconsumed:
        bad.append("approval_not_consumed")

    # A high-risk action must be covered by exactly one approval entry that is
    # bound to it and whose recorded ``seq`` strictly precedes the action in
    # sequence order (``approval.seq < action.seq``).  An approval recorded at
    # the same ``seq`` as the action cannot demonstrate that it preceded it, so
    # it is a violation; no ledger-declared consent flag may waive that.
    # Symmetrically, one approval entry must not cover two distinct actions.
    missing = 0
    reordered = 0
    over_covered = 0
    for step in steps:
        risk = step.get("risk_class")
        if risk not in APPROVAL_RISK_CLASSES:
            # Unknown risk class: the ledger cannot prove this action was
            # authorized, so it is never treated as a no-approval action.
            bad.append("unknown_risk_class")
            continue
        key = (step["node_id"], step.get("tool"), step.get("args_sha256"))
        matching = [entry for entry in entries
                    if (entry.get("node_id"), entry.get("tool"), entry.get("args_sha256")) == key]
        if not matching:
            missing += 1
            continue
        if len(matching) > 1:
            over_covered += 1
        preceding = [entry for entry in matching
                     if isinstance(entry.get("seq"), int)
                     and not isinstance(entry.get("seq"), bool)
                     and entry["seq"] < step["seq"]]
        if len(preceding) != 1:
            reordered += 1
    # One entry matching several actions is the same over-coverage defect seen
    # from the ledger side: a single recorded approval cannot authorize two
    # distinct actions even when each action individually finds a match.
    for entry in entries:
        key = (entry.get("node_id"), entry.get("tool"), entry.get("args_sha256"))
        covered = sum(1 for step in steps
                      if (step["node_id"], step.get("tool"), step.get("args_sha256")) == key)
        if covered > 1:
            over_covered += 1
    if missing:
        bad.append("high_risk_action_without_approval")
    if reordered:
        bad.append("approval_after_action")
    if over_covered:
        bad.append("approval_bound_to_multiple_actions")

    metrics = {
        "nodes_total": len(nodes),
        "steps_total": len(steps),
        "approvals_total": len(entries),
        "cross_branch_write_conflicts": conflicts,
        "missing_approvals": missing,
        "replayed_approvals": replays,
        "unconsumed_approvals": unconsumed,
        "over_covered_actions": over_covered,
        "false_approvals": false_approvals,
        "additional_review": len(bad),
    }
    return (tuple(bad), tuple(unknowns), metrics)


def audit_composed_boundaries(graph_sha256, policy_sha256, action_trace_sha256,
                              approval_ledger_sha256, evidence_sha256, *,
                              graph=None, policy=None, action_trace=None,
                              approval_ledger=None, evidence=None):
    """Offline three-valued composed-boundary audit; see module docstring."""
    declared = {
        "graph": graph_sha256,
        "policy": policy_sha256,
        "action_trace": action_trace_sha256,
        "approval_ledger": approval_ledger_sha256,
        "evidence": evidence_sha256,
    }
    supplied = {
        "graph": graph,
        "policy": policy,
        "action_trace": action_trace,
        "approval_ledger": approval_ledger,
        "evidence": evidence,
    }
    unknowns: list[str] = []
    for name in ARTIFACTS:
        digest = declared[name]
        if not isinstance(digest, str) or not _SHA256.match(digest):
            unknowns.append(f"{name}_digest_malformed")
        if supplied[name] is None:
            unknowns.append(f"{name}_artifact_missing")
    if unknowns:
        return _result("UNKNOWN", unknowns=unknowns)

    violations: list[str] = []
    for name in ARTIFACTS:
        artifact = supplied[name]
        if not isinstance(artifact, Mapping):
            violations.append(f"{name}_artifact_not_object")
            continue
        try:
            observed = canonical_digest(dict(artifact))
        except (SecurityError, TypeError, ValueError, AttributeError):
            violations.append(f"{name}_artifact_not_canonical")
            continue
        if observed != declared[name]:
            violations.append(f"{name}_digest_mismatch")
    if violations:
        return _result("VIOLATION", violations=violations)

    try:
        found, unknowns, metrics = _evaluate(dict(graph), dict(policy), dict(action_trace),
                                   dict(approval_ledger), dict(evidence), declared)
    except (KeyError, TypeError, ValueError, AttributeError, SecurityError):
        # Incomplete evidence must never degrade into a pass.
        return _result("UNKNOWN", unknowns=("artifact_structure_incomplete",))
    if found:
        status = "VIOLATION"
    elif unknowns:
        status = "UNKNOWN"
    else:
        status = "COVERED"
    return _result(status, violations=found, unknowns=unknowns, **metrics)
