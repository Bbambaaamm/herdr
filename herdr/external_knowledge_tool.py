"""Protected model-visible read tool for host external knowledge providers."""
from __future__ import annotations

import json
import os
import re

from .external_knowledge import KnowledgeContractError, KnowledgeRequest
from .security import PolicyDenied, SecurityError

TOOL = "herdr_external_knowledge"
TOOLSET = "herdr_external_knowledge"
ARGUMENTS = ("provider_id", "query", "sources", "conversation_id")
MAX_RESULT_CHARS = 2_000_000

SCHEMA = {
    "name": TOOL,
    "description": (
        "Search an explicitly granted external knowledge provider through the "
        "host-only Herdr broker. This is read-only retrieval; provider credentials "
        "and endpoints are never exposed to the model."
    ),
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "required": ["provider_id", "query", "sources"],
        "properties": {
            "provider_id": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9_.-]{0,63}$",
            },
            "query": {
                "type": "string",
                "minLength": 1,
                "maxLength": 4096,
            },
            "sources": {
                "type": "array",
                "minItems": 1,
                "maxItems": 8,
                "uniqueItems": True,
                "items": {
                    "type": "string",
                    "pattern": "^[a-z][a-z0-9_.-]{0,63}$",
                },
            },
            "conversation_id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 256,
            },
        },
    },
}


def _arguments(raw: object) -> dict[str, object]:
    if (not isinstance(raw, dict)
            or set(raw) - set(ARGUMENTS)
            or not {"provider_id", "query", "sources"} <= set(raw)):
        raise SecurityError("closed external knowledge arguments required")
    provider_id = raw["provider_id"]
    query = raw["query"]
    sources = raw["sources"]
    conversation_id = raw.get("conversation_id")
    if (not isinstance(provider_id, str)
            or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,63}", provider_id)):
        raise SecurityError("bounded external knowledge provider required")
    if (not isinstance(query, str) or not 0 < len(query) <= 4096 or "\0" in query):
        raise SecurityError("bounded external knowledge query required")
    if (not isinstance(sources, list) or not 1 <= len(sources) <= 8
            or len(set(sources)) != len(sources)
            or any(not isinstance(source, str)
                   or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,63}", source)
                   for source in sources)):
        raise SecurityError("bounded external knowledge sources required")
    if (conversation_id is not None and (
            not isinstance(conversation_id, str)
            or not 0 < len(conversation_id) <= 256
            or "\0" in conversation_id)):
        raise SecurityError("bounded external knowledge conversation required")
    return {
        "provider_id": provider_id,
        "query": query,
        "sources": list(sources),
        **({"conversation_id": conversation_id} if conversation_id is not None else {}),
    }


def _require_parent_environment(identity) -> None:
    from .policy_launch import IDENTITY_ENV
    if os.environ.get("HERDR_DURABLE_SANDBOX") != "1":
        raise PolicyDenied("external_knowledge_sandbox_required")
    for field, key in IDENTITY_ENV.items():
        if os.environ.get(key) != str(getattr(identity, field)):
            raise PolicyDenied("external_knowledge_identity_mismatch")


def register_external_knowledge_tool(
    installation,
    registry,
    authorized_call,
    call_digest,
) -> None:
    guard = installation.guard
    if TOOL not in guard.grant.scope.tools:
        return
    if registry.get_entry(TOOL) is not None:
        raise SecurityError("external knowledge tool registration collision")

    from .work_authority import WorkAuthorityClient
    authority = WorkAuthorityClient()

    def handle(raw, task_id=None):
        try:
            if not installation.installed:
                raise PolicyDenied("external_knowledge_guard_inactive")
            _require_parent_environment(guard.grant.identity)
            checked_input = _arguments(raw)
            supplied = dict(checked_input)
            _, checked = guard.authorize_tool_call(
                TOOL,
                supplied,
                caller_task_id=task_id,
                consume_approval=authorized_call.get() != (
                    guard.grant.hash, TOOL, call_digest(TOOL, supplied)
                ),
            )
            admitted = _arguments(checked)
            request = KnowledgeRequest.create(
                admitted["query"],
                tuple(admitted["sources"]),
                conversation_id=admitted.get("conversation_id"),
            )
            response = authority.external_knowledge(
                guard.grant.identity,
                guard.grant.hash,
                admitted["provider_id"],
                request,
            )
            payload = json.dumps(
                response.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            if len(payload) > MAX_RESULT_CHARS:
                raise SecurityError("bounded external knowledge result required")
            return payload
        except PolicyDenied as exc:
            return json.dumps({"error": exc.reason})
        except (SecurityError, KnowledgeContractError, ValueError, TypeError, OSError):
            return json.dumps({"error": "external_knowledge_contract_denied"})

    registry.register(
        name=TOOL,
        toolset=TOOLSET,
        schema=SCHEMA,
        handler=handle,
        description=SCHEMA["description"],
        max_result_size_chars=MAX_RESULT_CHARS,
    )
    current = registry.get_entry(TOOL)
    if current is None or current.handler is not handle:
        raise SecurityError("external knowledge tool registration unavailable")
    installation.finalizers.append(
        lambda: registry.restore_registration(TOOL, current, None)
    )
