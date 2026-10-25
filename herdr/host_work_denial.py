"""Bounded host denial metadata; never a work/budget transition or RPC authority."""
import sys
from types import CodeType, FunctionType, ModuleType

OPERATIONS = frozenset({"work-authorize", "work-budget", "work-verify",
                        "work-sdk-observation", "external-knowledge-query"})
SOURCES = frozenset({"work_authority", "work_contract_host", "work_cycle", "work_handoff",
                    "work_hygiene", "work_failure_control", "work_budget_configuration",
                    "work_budget", "check_runner", "evidence", "scope_evidence"})
ERROR_TYPES = frozenset({"WorkContractError", "EvidenceError", "EvidenceUnavailable",
    "EvidenceMissing", "PolicyDenied", "SecurityError", "TypeError", "ValueError",
    "RuntimeError", "KeyError", "OSError", "PermissionError", "FileNotFoundError",
    "TimeoutError", "Exception", "UnknownError"})
MAX_DENIALS = 8
MAX_FRAMES = 4


def validate_denial(value):
    if (type(value) is not dict or set(value) != {"operation", "error_type", "frames", "peer"}
            or type(value["operation"]) is not str or value["operation"] not in OPERATIONS
            or type(value["error_type"]) is not str or value["error_type"] not in ERROR_TYPES
            or type(value["frames"]) is not list or len(value["frames"]) > MAX_FRAMES):
        raise ValueError("closed host denial required")
    peer = value["peer"]
    if (type(peer) is not dict or set(peer) != {"pid", "start_ticks", "exe_device", "exe_inode"}
            or any(type(number) is not int or not 0 <= number < 2**64 for number in peer.values())
            or not 1 <= peer["pid"] < 2**31 or peer["start_ticks"] == 0 or peer["exe_inode"] == 0):
        raise ValueError("closed authenticated host peer required")
    frames = []
    for frame in value["frames"]:
        if (type(frame) is not dict or set(frame) != {"source", "line"}
                or type(frame["source"]) is not str or frame["source"] not in SOURCES
                or type(frame["line"]) is not int or not 1 <= frame["line"] <= 1_000_000):
            raise ValueError("closed host denial frame required")
        frames.append(dict(frame))
    return {"operation": value["operation"], "error_type": value["error_type"], "frames": frames, "peer": dict(peer)}


def _trusted_codes():
    # Only code objects actually held by these loaded canonical modules qualify.
    # A matching basename/co_filename on a caller-created frame is insufficient.
    found = {}
    def add(code, source):
        found[id(code)] = source
        for value in code.co_consts:
            if type(value) is CodeType:
                add(value, source)
    for source in sorted(SOURCES):
        module = sys.modules.get("herdr." + source)
        if type(module) is not ModuleType:
            continue
        for value in tuple(vars(module).values()):
            members = tuple(vars(value).values()) if type(value) is type and value.__module__ == module.__name__ else (value,)
            for member in members:
                if type(member) in (staticmethod, classmethod):
                    member = member.__func__
                if (type(member) is FunctionType and member.__module__ == module.__name__
                        and member.__code__.co_filename == module.__file__):
                    add(member.__code__, source)
    return found


def describe_denial(operation, error, peer):
    from .evidence import EvidenceError, EvidenceUnavailable, EvidenceMissing
    from .security import PolicyDenied, SecurityError
    from .work_cycle import WorkContractError
    classes = ((WorkContractError, "WorkContractError"), (EvidenceError, "EvidenceError"),
        (EvidenceUnavailable, "EvidenceUnavailable"), (EvidenceMissing, "EvidenceMissing"),
        (PolicyDenied, "PolicyDenied"), (SecurityError, "SecurityError"), (TypeError, "TypeError"),
        (ValueError, "ValueError"), (RuntimeError, "RuntimeError"), (KeyError, "KeyError"),
        (OSError, "OSError"), (PermissionError, "PermissionError"),
        (FileNotFoundError, "FileNotFoundError"), (TimeoutError, "TimeoutError"), (Exception, "Exception"))
    # Identity comparison never invokes an unknown exception metaclass's hash,
    # equality, name, str, args, chains, locals or request values.
    kind = next((name for cls, name in classes if type(error) is cls), "UnknownError")
    codes, frames = _trusted_codes(), []
    current = BaseException.__dict__["__traceback__"].__get__(error, type(error))
    for _ in range(64):
        if current is None:
            break
        source = codes.get(id(current.tb_frame.f_code))
        if source is not None and 1 <= current.tb_lineno <= 1_000_000:
            frames.append({"source": source, "line": current.tb_lineno})
            frames = frames[-MAX_FRAMES:]
        current = current.tb_next
    return validate_denial({"operation": operation, "error_type": kind, "frames": frames,
        "peer": {"pid": peer.pid, "start_ticks": peer.start_ticks,
                 "exe_device": peer.exe_device, "exe_inode": peer.exe_inode}})


def validate_denial_events(events, identity, plan_sha256, grant_sha256):
    if len(events) > MAX_DENIALS:
        raise ValueError("retained host denial limit exceeded")
    seen = []
    for index, row in enumerate(events, 1):
        if (type(row) is not dict or set(row) != {"event", "work_cycle", "plan_sha256",
                "grant_sha256", "provenance", "denial_index", "denial"}
                or row["event"] != "work_host_denial"
                or row["work_cycle"] != identity.to_json()
                or row["plan_sha256"] != plan_sha256 or row["grant_sha256"] != grant_sha256
                or row["provenance"] != "host_authenticated_request"
                or type(row["denial_index"]) is not int or row["denial_index"] != index):
            raise ValueError("retained host denial binding invalid")
        denial = validate_denial(row["denial"])
        if denial in seen:
            raise ValueError("duplicate retained host denial")
        seen.append(denial)
