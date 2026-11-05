"""Bounded scope evidence. A worker narrative never expands the frozen policy."""
from pathlib import PurePosixPath
import re
import json

from .evidence import EvidenceError, canonical, digest

_SHA = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class ScopeError(EvidenceError):
    code = "scope_invalid"


class ScopeReplan(ScopeError):
    code = "scope_replan_required"


class ScopeBlocked(ScopeError):
    code = "scope_blocked"


def require(ok, reason):
    if not ok:
        raise ScopeError(reason)


def bounded_json(value):
    # Bound depth/work before encoding, including malformed Python callers.
    pending = [(value, 0)]
    count = 0
    characters = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        require(depth <= 16 and count <= 20000, "scope JSON exceeds structural bound")
        if isinstance(item, dict):
            require(len(item) <= 4096 and all(isinstance(k, str) for k in item),
                    "invalid scope JSON object")
            characters += sum(len(k) for k in item)
            pending.extend((x, depth + 1) for x in item.values())
        elif isinstance(item, list):
            require(len(item) <= 4096, "scope JSON array exceeds bound")
            pending.extend((x, depth + 1) for x in item)
        elif isinstance(item, str):
            characters += len(item)
            require(len(item) <= 131072, "scope JSON string exceeds bound")
        else:
            require(item is None or type(item) in {bool, int}, "invalid scope JSON value")
            require(type(item) is not int or item.bit_length() <= 64, "scope integer exceeds bound")
        require(characters <= 131072, "scope JSON cumulative size exceeds bound")
    try:
        raw = canonical(value)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ScopeError("invalid scope JSON encoding") from exc
    require(len(raw) <= 131072, "scope JSON exceeds byte bound")
    return raw


def path(value):
    require(isinstance(value, str) and 1 <= len(value) <= 1024
            and "\\" not in value and ":" not in value and "\0" not in value
            and not PurePosixPath(value).is_absolute()
            and all(x not in {"", ".", "..", ".git"} for x in value.split("/")),
            "invalid scope path")
    return value


def strings(value, maximum, *, identifiers=False, nonempty=False):
    require(isinstance(value, list) and len(value) <= maximum
            and (not nonempty or bool(value))
            and all(isinstance(x, str) and 1 <= len(x) <= 1024 and "\0" not in x
                    and (not identifiers or _ID.fullmatch(x)) for x in value),
            "invalid bounded scope list")
    require(len(set(value)) == len(value), "duplicate scope item")
    return value


def validate_scope_policy(policy):
    require(isinstance(policy, dict)
            and type(policy.get("version")) is int and policy["version"] in {1, 2}
            and set(policy) == ({"version", "files", "acceptance_ids", "shared_contract_keys"}
                 | ({"shared_contracts"} if policy["version"] == 2 else set())),
            "unsupported scope policy")
    files = policy["files"]
    require(isinstance(files, list) and 1 <= len(files) <= 4096, "frozen file scope required")
    for row in files:
        require(isinstance(row, dict) and set(row) == {"path", "subtree"}
                and type(row["subtree"]) is bool, "invalid scope descriptor")
        path(row["path"])
    require(len({x["path"] for x in files}) == len(files), "duplicate frozen path")
    strings(policy["acceptance_ids"], 128, identifiers=True, nonempty=True)
    strings(policy["shared_contract_keys"], 128, identifiers=True)
    if policy["version"] == 2:
        rows = policy["shared_contracts"]
        require(isinstance(rows, list) and len(rows) <= 128, "shared contract mapping exceeds bound")
        for row in rows:
            require(isinstance(row, dict) and set(row) == {"key", "path", "base_sha256"}
                    and isinstance(row["key"], str) and _ID.fullmatch(row["key"])
                    and isinstance(row["base_sha256"], str) and _SHA.fullmatch(row["base_sha256"]),
                    "invalid frozen shared contract mapping")
            path(row["path"])
        require(len({row["key"] for row in rows}) == len(rows)
                and len({row["path"] for row in rows}) == len(rows)
                and {row["key"] for row in rows} == set(policy["shared_contract_keys"]),
                "shared contract mapping must cover each frozen key exactly once")
    bounded_json(policy)


def covers(policy, name):
    path(name)
    return any(name == row["path"] or row["subtree"] and name.startswith(row["path"] + "/")
               for row in policy["files"])


def verify_scope_self_check(plan, artifact, report):
    """Check exact physical diff coverage and refusal states, not narrative truth.

    Justifications and symbol/resource descriptions stay self-reported data.
    The required independent exact-artifact review remains a separate gate.
    Operational size bounds do not measure code quality or justify any change.
    """
    policy = plan["scope_policy"]
    validate_scope_policy(policy)
    names = {"version", "spec_sha256", "artifact_sha256", "changed_groups",
             "unrelated_changes", "unexpected_side_effects", "followups_not_implemented",
             "shared_contract_changes", "verdict"}
    require(isinstance(report, dict) and set(report) == names
            and type(report["version"]) is int and report["version"] == 1
            and report["spec_sha256"] == plan["spec_hash"]
            and report["artifact_sha256"] == artifact.result_sha,
            "scope report binding mismatch")
    encoded = bounded_json(report)
    groups = report["changed_groups"]
    require(isinstance(groups, list) and 1 <= len(groups) <= 4096, "scope groups required")
    seen = set()
    linked_criteria = set()
    for group in groups:
        require(isinstance(group, dict) and set(group) ==
                {"files", "symbols", "resources", "acceptance_ids", "justification"},
                "invalid scope group")
        files = strings(group["files"], 4096, nonempty=True)
        for name in files:
            require(covers(policy, name), "change outside frozen scope")
            require(name not in seen, "scope groups overlap")
            seen.add(name)
        criteria = strings(group["acceptance_ids"], 128, identifiers=True, nonempty=True)
        require(set(criteria) <= set(policy["acceptance_ids"]), "unknown acceptance linkage")
        linked_criteria.update(criteria)
        strings(group["symbols"], 256)
        strings(group["resources"], 256)
        require(isinstance(group["justification"], str)
                and 1 <= len(group["justification"].strip()) <= 4096
                and "\0" not in group["justification"], "change justification required")
    require(seen == set(artifact.changed_files), "scope report differs from exact artifact")
    require(linked_criteria == set(policy["acceptance_ids"]), "scope report omits frozen acceptance linkage")
    for field in ("unrelated_changes", "unexpected_side_effects", "followups_not_implemented"):
        strings(report[field], 256)
    changes = report["shared_contract_changes"]
    require(isinstance(changes, list) and len(changes) <= 128, "contract changes exceed bound")
    keys = set()
    for row in changes:
        require(isinstance(row, dict) and set(row) == {"key", "previous_sha256", "next_sha256"}
                and isinstance(row["key"], str) and row["key"] in policy["shared_contract_keys"]
                and row["key"] not in keys
                and all(isinstance(row[k], str) and _SHA.fullmatch(row[k])
                        for k in ("previous_sha256", "next_sha256")),
                "undeclared shared contract change")
        keys.add(row["key"])
    verdict = report["verdict"]
    require(isinstance(verdict, str) and verdict in {"IN_SCOPE", "REPLAN_REQUIRED", "BLOCK"},
            "invalid scope verdict")
    if verdict == "BLOCK" or report["unexpected_side_effects"]:
        raise ScopeBlocked("scope blocked before functional acceptance")
    if verdict == "REPLAN_REQUIRED" or report["unrelated_changes"] or changes:
        # A declared shared-contract mutation still needs a revised host plan;
        # the worker cannot refresh dependencies or evidence by this report.
        raise ScopeReplan("scope or shared contract needs a revised host plan")
    return {"version": 1, "status": "IN_SCOPE", "report": json.loads(encoded),
            "report_sha256": digest(report), "policy_sha256": digest(policy),
            "coverage": "exact changed-file set and frozen acceptance linkage",
            "limitations": "worker explanations are advisory; independent review remains required"}


def verify_shared_contracts(plan, artifact, git):
    """Derive contract mutations from exact Git bytes, regardless of confession."""
    import hashlib
    import time
    from .workspace import WorkspaceError
    policy = plan["scope_policy"]
    validate_scope_policy(policy)
    if policy["version"] == 1:
        if policy["shared_contract_keys"]:
            raise ScopeReplan("frozen shared contract keys require a trusted path and base digest mapping")
        return
    deadline = time.monotonic() + 60
    total = 0
    for row in policy["shared_contracts"]:
        if time.monotonic() > deadline:
            raise ScopeReplan("shared contract verification exceeds cumulative bound")
        try:
            baseline = git.raw(["cat-file", "blob", artifact.base_sha + ":" + row["path"]])
        except WorkspaceError as exc:
            raise ScopeReplan("frozen shared contract baseline cannot be verified") from exc
        total += len(baseline)
        if total > 67108864 or time.monotonic() > deadline:
            raise ScopeReplan("shared contract verification exceeds cumulative bound")
        if hashlib.sha256(baseline).hexdigest() != row["base_sha256"]:
            raise ScopeReplan("frozen shared contract baseline digest differs")
        if row["path"] in artifact.changed_files:
            # The verified ArtifactRef is the exact base-to-commit diff, including
            # deletion and mode changes. A worker cannot omit this host observation.
            raise ScopeReplan("exact artifact changes a frozen shared contract; invalidate dependents and replan")
