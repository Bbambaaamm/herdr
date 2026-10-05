"""Decode candidate data through the existing closed result evidence slot."""
import math
from .evidence import EvidenceError, canonical

def bounded_result(payload):
    nodes = [(payload, 0)]
    count = characters = 0
    while nodes:
        value, depth = nodes.pop()
        count += 1
        if depth > 16 or count > 20000:
            raise EvidenceError("result exceeds structural bound")
        if isinstance(value, dict):
            if len(value) > 4096 or any(not isinstance(k, str) for k in value):
                raise EvidenceError("invalid result object")
            characters += sum(len(k) for k in value)
            nodes.extend((x, depth + 1) for x in value.values())
        elif isinstance(value, (list, tuple)):
            if len(value) > 4096: raise EvidenceError("result array exceeds bound")
            nodes.extend((x, depth + 1) for x in value)
        elif isinstance(value, str):
            characters += len(value)
        elif type(value) is int:
            if value.bit_length() > 64: raise EvidenceError("result integer exceeds bound")
        elif type(value) is float:
            if not math.isfinite(value): raise EvidenceError("non-finite result number")
        elif value is not None and type(value) is not bool:
            raise EvidenceError("invalid result value")
        if characters > 1048576: raise EvidenceError("result text exceeds bound")
    try:
        if len(canonical(payload)) > 1048576: raise EvidenceError("result exceeds byte bound")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise EvidenceError("invalid result encoding") from exc

def completion_candidate(payload, *, workspace=None):
    bounded_result(payload)
    if not isinstance(payload, dict): raise EvidenceError("result object required")
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list): raise EvidenceError("result evidence array required")
    tagged = [(key, row[key]) for row in evidence if isinstance(row, dict)
              for key in ("herdr_completion", "herdr_control") if key in row]
    if not tagged:
        return dict(payload)  # Historical host transport; never acceptance authority.
    if len(tagged) != 1 or any(k in payload for k in
            ("artifact", "artifact_workspace", "pr_number", "scope_self_check", "next_action")):
        raise EvidenceError("ambiguous completion candidate")
    key, data = tagged[0]
    row = next(row for row in evidence if isinstance(row, dict) and key in row)
    if set(row) != {key} or not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise EvidenceError("invalid tagged completion candidate")
    allowed = ({"version", "artifact", "pr_number", "artifact_workspace", "scope_self_check"}
               if key == "herdr_completion" else {"version", "next_action"})
    required = {"version", "artifact", "pr_number"} if key == "herdr_completion" else allowed
    if not required <= set(data) <= allowed:
        raise EvidenceError("unsupported completion candidate fields")
    result = {**payload, **{k: v for k, v in data.items() if k != "version"}}
    if workspace is not None and key == "herdr_completion":
        if "artifact_workspace" in data and data["artifact_workspace"] != str(workspace):
            raise EvidenceError("candidate differs from admitted workspace")
        result["artifact_workspace"] = str(workspace)
    return result
