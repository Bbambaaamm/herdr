"""Bounded SDK observations: descriptive metadata, never execution authority.

The authenticated host supplies invocation/plan bindings. These SDK observations
cannot establish network delivery, authorize a retry, or settle a reservation.
Errors before the authenticated bootstrap channel exists remain uncovered.
"""
import functools

PHASES = frozenset({"sdk_agent_init", "sdk_provider_check", "sdk_api_call", "sdk_middleware"})
OUTCOMES = frozenset({"failed"})
ERROR_TYPES = frozenset({"PolicyDenied", "SecurityError", "TypeError", "ValueError",
    "RuntimeError", "OSError", "PermissionError", "FileNotFoundError", "TimeoutError",
    "ImportError", "ModuleNotFoundError", "UnknownError"})
MAX_OBSERVATIONS = 8


def validate_observation(value):
    if (type(value) is not dict or set(value) != {"phase", "outcome", "error_type"}
            or type(value["phase"]) is not str or value["phase"] not in PHASES
            or type(value["outcome"]) is not str or value["outcome"] not in OUTCOMES
            or type(value["error_type"]) is not str or value["error_type"] not in ERROR_TYPES):
        raise ValueError("closed SDK observation required")
    return dict(value)


def error_type(error):
    # Fixed output values; never inspect exception text, args or dynamic names.
    from .security import PolicyDenied, SecurityError
    for cls, name in ((PolicyDenied, "PolicyDenied"), (SecurityError, "SecurityError"),
            (TimeoutError, "TimeoutError"), (PermissionError, "PermissionError"),
            (FileNotFoundError, "FileNotFoundError"), (ModuleNotFoundError, "ModuleNotFoundError"),
            (ImportError, "ImportError"),
            (TypeError, "TypeError"), (ValueError, "ValueError"),
            (RuntimeError, "RuntimeError"), (OSError, "OSError")):
        if isinstance(error, cls):
            return name
    return "UnknownError"


def report_failure(guard, phase, error):
    """Best effort only: reporting must never replace the original failure."""
    try:
        observer = getattr(guard, "observe_sdk", None)
        if callable(observer):
            return observer(validate_observation({"phase": phase, "outcome": "failed",
                                                  "error_type": error_type(error)})) is True
    except BaseException:
        pass
    return False


def observe_failures(guard, phase):
    def decorate(original):
        @functools.wraps(original)
        def observed(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except BaseException as error:
                report_failure(guard, phase, error)
                raise
        return observed
    return decorate


def validate_observation_events(events, identity, plan_sha256, grant_sha256):
    """Replay descriptive records without interpreting them as phase transitions."""
    if len(events) > MAX_OBSERVATIONS:
        raise ValueError("retained SDK observation limit exceeded")
    seen = []
    for index, row in enumerate(events, 1):
        if (type(row) is not dict or set(row) != {"event", "work_cycle", "plan_sha256",
                "grant_sha256", "provenance", "observation_index", "observation"}
                or row["event"] != "work_sdk_observation"
                or row["work_cycle"] != identity.to_json()
                or row["plan_sha256"] != plan_sha256 or row["grant_sha256"] != grant_sha256
                or row["provenance"] != "sdk_observed"
                or type(row["observation_index"]) is not int or row["observation_index"] != index):
            raise ValueError("retained SDK observation binding invalid")
        observation = validate_observation(row["observation"])
        if observation in seen:
            raise ValueError("duplicate retained SDK observation")
        seen.append(observation)
