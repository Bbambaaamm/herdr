"""Closed host-oracle request in the actual Hermes registry."""
import json
import os
import re

TOOL = "herdr_verify_work"
SCHEMA = {"name": TOOL,
    "description": "Run the frozen host verification oracle. PASS ends implementation; failure requires evidenced repair authority.",
    "parameters": {"type": "object", "additionalProperties": False, "required": ["request_id"],
                   "properties": {"request_id": {"type": "string", "pattern": "^[A-Za-z0-9_-]{1,64}$"},
                                  "handoff": {"type": "object", "additionalProperties": False,
                                      "required": ["pr_number"], "properties": {
                                          "pr_number": {"type": ["integer", "null"], "minimum": 1},
                                          "scope_claim": {"type": "object"}}}}}}

def register_work_tool(installation, registry, authorized_call, call_digest):
    from .security import PolicyDenied, SecurityError
    from .evidence import EvidenceError
    from .policy_launch import IDENTITY_ENV
    guard = installation.guard
    if TOOL not in guard.grant.scope.tools:
        return
    if not callable(getattr(guard, "verify_work", None)) or registry.get_entry(TOOL) is not None:
        raise SecurityError("work tool authority or registration unavailable")
    def handle(raw, task_id=None):
        try:
            if not installation.installed or os.environ.get("HERDR_DURABLE_SANDBOX") != "1":
                raise PolicyDenied("work_guard_inactive")
            if any(os.environ.get(key) != str(getattr(guard.grant.identity, field))
                   for field, key in IDENTITY_ENV.items()):
                raise PolicyDenied("work_identity_mismatch")
            if (not isinstance(raw, dict) or set(raw) not in ({"request_id"}, {"request_id", "handoff"})
                    or not isinstance(raw["request_id"], str)
                    or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", raw["request_id"])):
                raise PolicyDenied("work_request_invalid")
            guard.authorize_tool_call(TOOL, raw, caller_task_id=task_id,
                consume_approval=authorized_call.get() != (guard.grant.hash, TOOL, call_digest(TOOL, raw)))
            outcome = guard.verify_work(raw["request_id"], handoff=raw.get("handoff"), consume_approval=False)
            if outcome.get("submission") is not None:
                from .result_submission import submit
                submission = submit(guard, outcome["submission"])
                outcome = {key:value for key,value in outcome.items() if key != "submission"}
                outcome["result_delivery"] = submission
            return json.dumps(outcome, sort_keys=True)
        except PolicyDenied as exc:
            return json.dumps({"error": exc.reason})
        except (SecurityError, EvidenceError, ValueError, TypeError, OSError):
            return json.dumps({"error": "work_verification_denied"})
    registry.register(name=TOOL, toolset="herdr_work", schema=SCHEMA, handler=handle,
                      description=SCHEMA["description"], max_result_size_chars=8192)
    current = registry.get_entry(TOOL)
    if current is None or current.handler is not handle:
        raise SecurityError("work tool registration unavailable")
    installation.finalizers.append(lambda: registry.restore_registration(TOOL, current, None))
