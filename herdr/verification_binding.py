"""An immutable commit binds independent review to this exact frozen task."""
import json
from .evidence import EvidenceError, canonical, digest

PREFIX = "Herdr-Verification-Binding: "

def commit_binding(plan):
    return {"version": 1, "identity": plan["identity"], "spec_hash": plan["spec_hash"],
            "policy_hash": plan["policy_hash"], "base_sha": plan["base_sha"]}

def commit_footer(plan):
    return PREFIX + canonical(commit_binding(plan)).decode("utf-8")

def verify_commit_binding(plan, artifact, document):
    if not isinstance(document, dict) or document.get("sha") != artifact.commit_sha:
        raise EvidenceError("reviewed commit origin differs from artifact")
    message = document.get("commit", {}).get("message")
    if not isinstance(message, str) or len(message.encode("utf-8")) > 65536:
        raise EvidenceError("reviewed commit has no bounded specification binding")
    rows = [line[len(PREFIX):] for line in message.splitlines() if line.startswith(PREFIX)]
    if len(rows) != 1:
        raise EvidenceError("reviewed commit requires exactly one immutable specification binding")
    try:
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result: raise ValueError("duplicate binding key")
                result[key] = value
            return result
        claimed = json.loads(rows[0], object_pairs_hook=unique)
        expected = commit_binding(plan)
        if canonical(claimed) != canonical(expected) or canonical(claimed).decode("utf-8") != rows[0]:
            raise ValueError("different frozen task")
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise EvidenceError("independent review is not bound to this frozen specification and attempt") from exc
    return {**expected, "binding_sha256": digest(expected)}
