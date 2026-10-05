"""Granted Hermes delegation through the authenticated durable parent bridge."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

from herdr.security import PolicyDenied, SecurityError
from herdr.child_ownership import ChildOwnership, ownership_schema

TOOL = "herdr_delegate_child"
TOOLSET = "herdr_delegation"
ARGUMENTS = ("key", "role", "objective", "prompt", "tool", "permission", "cwd", "ownership")
SCHEMA = {
    "name": TOOL,
    "description": "Delegate bounded work through the current Herdr task. Reuse the same key to reconcile the same child. Returned evidence is submitted work, subject to shared acceptance.",
    "parameters": {
        "type": "object", "additionalProperties": False,
        "required": ["key", "role", "objective", "prompt"],
        "properties": {
            "key": {"type": "string", "minLength": 1, "maxLength": 128},
            "role": {"type": "string", "minLength": 1, "maxLength": 32},
            "objective": {"type": "string", "minLength": 1, "maxLength": 8192},
            "prompt": {"type": "string", "minLength": 1, "maxLength": 32768},
            "tool": {"type": "array", "maxItems": 64, "uniqueItems": True,
                     "items": {"type": "string", "minLength": 1, "maxLength": 128}},
            "permission": {"type": "array", "maxItems": 64, "uniqueItems": True,
                     "items": {"type": "string", "minLength": 1, "maxLength": 128}},
            "cwd": {"type": "string", "maxLength": 4096},
            "ownership": ownership_schema(),
        },
    },
}


def _arguments(value):
    if not isinstance(value, dict) or set(value) - set(ARGUMENTS):
        raise SecurityError("closed delegation arguments required")
    checked = dict(value)
    for name, limit in (("key", 128), ("role", 32), ("objective", 8192), ("prompt", 32768)):
        item = checked.get(name)
        if not isinstance(item, str) or not 0 < len(item) <= limit or "\0" in item:
            raise SecurityError("bounded delegation text required")
    if not re.fullmatch(r"[A-Za-z0-9._:/+-]{1,128}", checked["key"]):
        raise SecurityError("bounded delegation key required")
    for name in ("tool", "permission"):
        items = checked.setdefault(name, [])
        if (not isinstance(items, list) or len(items) > 64
                or any(not isinstance(item, str) or not 0 < len(item) <= 128 or "\0" in item for item in items)
                or len(set(items)) != len(items)):
            raise SecurityError("bounded unique delegation scope required")
    if checked.get("ownership") is not None:
        checked["ownership"] = ChildOwnership.from_json(checked["ownership"]).to_json()
    cwd = checked.setdefault("cwd", "")
    if not isinstance(cwd, str) or len(cwd) > 4096 or "\0" in cwd:
        raise SecurityError("bounded delegation cwd required")
    if len(json.dumps(checked, ensure_ascii=False, allow_nan=False).encode()) > 131072:
        raise SecurityError("delegation request exceeds bound")
    return checked


def _require_parent_environment(identity):
    from herdr.policy_launch import IDENTITY_ENV
    if any(os.environ.get(key) != str(getattr(identity, field)) for field, key in IDENTITY_ENV.items()):
        raise PolicyDenied("delegation_identity_mismatch")
    for name, expected in (("HERDR_DURABLE_TASK_ID", identity.task_id),
                           ("HERDR_DURABLE_RUN_TOKEN", identity.run_token),
                           ("HERDR_DURABLE_AGENT", identity.agent_id)):
        if os.environ.get(name) != expected:
            raise PolicyDenied("delegation_parent_mismatch")
    if os.environ.get("HERDR_DURABLE_SANDBOX") != "1":
        raise PolicyDenied("delegation_sandbox_required")


def _client_delegate(arguments):
    # The helper path is inside this launch's approved immutable code snapshot.
    # Only its socket client is used; no shell, terminal, native RPC or subprocess.
    directory = Path(__file__).resolve().parents[1] / "agent-stack/bin"
    loader = SourceFileLoader("herdr_granted_durable_client", str(directory / "agent-durable-child"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    previous = list(sys.path)
    try:
        sys.path.insert(0, str(directory))
        loader.exec_module(module)
    finally:
        sys.path[:] = previous
    return module.client_delegate(argparse.Namespace(**arguments))


def register_delegation_tool(installation, registry, authorized_call, call_digest):
    guard = installation.guard
    if TOOL not in guard.grant.scope.tools:
        return
    # The protected name belongs to this guard; an existing plugin cannot win a
    # registration race or supply a replacement handler under the same name.
    if registry.get_entry(TOOL) is not None:
        raise SecurityError("delegation tool registration collision")

    def handle(arguments, task_id=None):
        try:
            if not installation.installed:
                raise PolicyDenied("delegation_guard_inactive")
            _require_parent_environment(guard.grant.identity)
            _arguments(arguments)
            supplied = dict(arguments)
            _, checked = guard.authorize_tool_call(
                TOOL, supplied, caller_task_id=task_id,
                consume_approval=authorized_call.get() != (
                    guard.grant.hash, TOOL, call_digest(TOOL, supplied)))
            admitted = _arguments(checked)
            if admitted.get("ownership") is not None:
                owner = ChildOwnership.from_json(admitted["ownership"])
                if owner.integration_owner != guard.grant.identity.task_id:
                    raise PolicyDenied("delegation_integration_owner_mismatch")
            result = _client_delegate(admitted)
            payload = json.dumps(result, ensure_ascii=False, allow_nan=False)
            if len(payload.encode()) > 524288:
                raise SecurityError("bounded delegation result required")
            return payload
        except PolicyDenied as exc:
            return json.dumps({"error": exc.reason})
        except (SecurityError, ValueError, OSError):
            return json.dumps({"error": "delegation_contract_denied"})

    registry.register(name=TOOL, toolset=TOOLSET, schema=SCHEMA, handler=handle,
                      description=SCHEMA["description"], max_result_size_chars=524288)
    current = registry.get_entry(TOOL)
    if current is None or current.handler is not handle:
        raise SecurityError("delegation tool registration unavailable")
    installation.finalizers.append(lambda: registry.restore_registration(TOOL, current, None))
