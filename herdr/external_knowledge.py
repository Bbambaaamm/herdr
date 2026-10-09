"""Vendor-neutral host contract for external knowledge providers.

Concrete providers live outside Herdr. This module defines bounded request,
response, health and registry semantics only; it grants no network, credential
or model-visible tool authority.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

_PROVIDER_RE = re.compile(r"[a-z][a-z0-9_.-]{0,63}")
_SOURCE_RE = re.compile(r"[a-z][a-z0-9_.-]{0,63}")
_REQUEST_RE = re.compile(r"[A-Za-z0-9._:-]{1,128}")
MAX_QUERY_CHARS = 16_384
MAX_SOURCES = 16
MAX_ANSWER_CHARS = 524_288


class KnowledgeErrorCode(StrEnum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_TRANSIENT = "UPSTREAM_TRANSIENT"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    INVALID_REQUEST = "INVALID_REQUEST"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class KnowledgeContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class KnowledgeRequest:
    request_id: str
    query: str
    sources: tuple[str, ...]
    conversation_id: str | None = None
    mode: str = "search"

    def __post_init__(self) -> None:
        if not _REQUEST_RE.fullmatch(self.request_id):
            raise KnowledgeContractError("invalid_request_id")
        if (not isinstance(self.query, str) or not self.query.strip()
                or len(self.query) > MAX_QUERY_CHARS or "\0" in self.query):
            raise KnowledgeContractError("invalid_query")
        if (not isinstance(self.sources, tuple) or not 1 <= len(self.sources) <= MAX_SOURCES
                or len(set(self.sources)) != len(self.sources)
                or any(not isinstance(source, str) or not _SOURCE_RE.fullmatch(source)
                       for source in self.sources)):
            raise KnowledgeContractError("invalid_sources")
        if (self.conversation_id is not None and (
                not isinstance(self.conversation_id, str)
                or not 1 <= len(self.conversation_id) <= 256
                or "\0" in self.conversation_id)):
            raise KnowledgeContractError("invalid_conversation_id")
        if self.mode != "search":
            raise KnowledgeContractError("invalid_mode")

    @classmethod
    def create(cls, query: str, sources: tuple[str, ...], *,
               conversation_id: str | None = None,
               request_id: str | None = None) -> "KnowledgeRequest":
        return cls(request_id or str(uuid4()), query, sources, conversation_id)

    def to_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "request_id": self.request_id,
            "query": self.query,
            "sources": list(self.sources),
            "mode": self.mode,
        }
        if self.conversation_id is not None:
            value["conversation_id"] = self.conversation_id
        return value

    @classmethod
    def from_dict(cls, raw: object) -> "KnowledgeRequest":
        if not isinstance(raw, dict):
            raise KnowledgeContractError("invalid_request")
        allowed = {"request_id", "query", "sources", "conversation_id", "mode"}
        if set(raw) - allowed or not {"request_id", "query", "sources"} <= set(raw):
            raise KnowledgeContractError("invalid_request")
        sources = raw["sources"]
        if not isinstance(sources, list):
            raise KnowledgeContractError("invalid_sources")
        return cls(
            request_id=raw["request_id"],
            query=raw["query"],
            sources=tuple(sources),
            conversation_id=raw.get("conversation_id"),
            mode=raw.get("mode", "search"),
        )


@dataclass(frozen=True, slots=True)
class KnowledgeSourceResult:
    source: str
    status: str
    duration_ms: int
    answer: str | None = None
    conversation_id: str | None = None
    error_code: KnowledgeErrorCode | None = None
    retryable: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not _SOURCE_RE.fullmatch(self.source):
            raise KnowledgeContractError("invalid_source_result")
        if self.status not in {"ok", "error"}:
            raise KnowledgeContractError("invalid_source_status")
        if type(self.duration_ms) is not int or not 0 <= self.duration_ms <= 86_400_000:
            raise KnowledgeContractError("invalid_source_duration")
        if self.status == "ok":
            if (not isinstance(self.answer, str) or not self.answer.strip()
                    or len(self.answer) > MAX_ANSWER_CHARS
                    or self.error_code is not None or self.retryable):
                raise KnowledgeContractError("invalid_source_success")
        else:
            if self.answer is not None or not isinstance(self.error_code, KnowledgeErrorCode):
                raise KnowledgeContractError("invalid_source_error")
        if (self.conversation_id is not None and (
                not isinstance(self.conversation_id, str)
                or not 1 <= len(self.conversation_id) <= 256
                or "\0" in self.conversation_id)):
            raise KnowledgeContractError("invalid_source_conversation")

    @classmethod
    def from_dict(cls, raw: object) -> "KnowledgeSourceResult":
        if not isinstance(raw, dict):
            raise KnowledgeContractError("invalid_source_result")
        allowed = {
            "source", "status", "duration_ms", "answer", "conversation_id",
            "error",
        }
        if set(raw) - allowed or not {"source", "status", "duration_ms"} <= set(raw):
            raise KnowledgeContractError("invalid_source_result")
        error = raw.get("error")
        error_code = None
        retryable = False
        if error is not None:
            if (not isinstance(error, dict) or set(error) != {"code", "retryable"}
                    or type(error["retryable"]) is not bool):
                raise KnowledgeContractError("invalid_source_error")
            try:
                error_code = KnowledgeErrorCode(error["code"])
            except (TypeError, ValueError) as exc:
                raise KnowledgeContractError("invalid_source_error") from exc
            retryable = error["retryable"]
        return cls(
            source=raw["source"],
            status=raw["status"],
            duration_ms=raw["duration_ms"],
            answer=raw.get("answer"),
            conversation_id=raw.get("conversation_id"),
            error_code=error_code,
            retryable=retryable,
        )


@dataclass(frozen=True, slots=True)
class KnowledgeResponse:
    request_id: str
    status: str
    answer: str
    sources: tuple[KnowledgeSourceResult, ...]
    partial: bool

    def __post_init__(self) -> None:
        if not _REQUEST_RE.fullmatch(self.request_id):
            raise KnowledgeContractError("invalid_response_id")
        if self.status not in {"completed", "error"}:
            raise KnowledgeContractError("invalid_response_status")
        if not isinstance(self.sources, tuple) or not self.sources:
            raise KnowledgeContractError("invalid_response_sources")
        names = tuple(item.source for item in self.sources)
        if len(set(names)) != len(names):
            raise KnowledgeContractError("duplicate_response_sources")
        successful = tuple(item for item in self.sources if item.status == "ok")
        expected_partial = 0 < len(successful) < len(self.sources)
        if self.partial != expected_partial:
            raise KnowledgeContractError("invalid_partial_flag")
        if self.status == "completed":
            if (not successful or not isinstance(self.answer, str) or not self.answer.strip()
                    or len(self.answer) > MAX_ANSWER_CHARS):
                raise KnowledgeContractError("invalid_completed_response")
        elif successful or self.answer:
            raise KnowledgeContractError("invalid_error_response")

    def to_dict(self) -> dict[str, object]:
        rows: list[dict[str, object]] = []
        for item in self.sources:
            row: dict[str, object] = {
                "source": item.source,
                "status": item.status,
                "duration_ms": item.duration_ms,
            }
            if item.answer is not None:
                row["answer"] = item.answer
            if item.conversation_id is not None:
                row["conversation_id"] = item.conversation_id
            if item.error_code is not None:
                row["error"] = {
                    "code": item.error_code.value,
                    "retryable": item.retryable,
                }
            rows.append(row)
        return {
            "request_id": self.request_id,
            "status": self.status,
            "answer": self.answer,
            "sources": rows,
            "meta": {"partial": self.partial},
        }

    @classmethod
    def from_dict(cls, raw: object) -> "KnowledgeResponse":
        if (not isinstance(raw, dict)
                or set(raw) != {"request_id", "status", "answer", "sources", "meta"}
                or not isinstance(raw["sources"], list)
                or not isinstance(raw["meta"], dict)
                or set(raw["meta"]) != {"partial"}
                or type(raw["meta"]["partial"]) is not bool):
            raise KnowledgeContractError("invalid_response")
        return cls(
            request_id=raw["request_id"],
            status=raw["status"],
            answer=raw["answer"],
            sources=tuple(KnowledgeSourceResult.from_dict(item) for item in raw["sources"]),
            partial=raw["meta"]["partial"],
        )


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    status: str
    error_code: KnowledgeErrorCode | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ready", "auth_required", "unavailable"}:
            raise KnowledgeContractError("invalid_health_status")
        if self.status == "ready" and self.error_code is not None:
            raise KnowledgeContractError("invalid_ready_health")
        if self.status != "ready" and not isinstance(self.error_code, KnowledgeErrorCode):
            raise KnowledgeContractError("invalid_failed_health")


class ExternalKnowledgeProvider(Protocol):
    provider_id: str

    def health(self) -> ProviderHealth:
        ...

    def query(self, request: KnowledgeRequest) -> KnowledgeResponse:
        ...


class ExternalKnowledgeRegistry:
    """Host-owned provider registry; registration is not tool authority."""

    def __init__(self) -> None:
        self._providers: dict[str, ExternalKnowledgeProvider] = {}

    def register(self, provider: ExternalKnowledgeProvider) -> None:
        provider_id = getattr(provider, "provider_id", None)
        if not isinstance(provider_id, str) or not _PROVIDER_RE.fullmatch(provider_id):
            raise KnowledgeContractError("invalid_provider_id")
        if provider_id in self._providers:
            raise KnowledgeContractError("duplicate_provider")
        if not callable(getattr(provider, "health", None)) or not callable(getattr(provider, "query", None)):
            raise KnowledgeContractError("invalid_provider")
        self._providers[provider_id] = provider

    def provider_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def health(self, provider_id: str) -> ProviderHealth:
        return self._get(provider_id).health()

    def query(self, provider_id: str, request: KnowledgeRequest) -> KnowledgeResponse:
        if not isinstance(request, KnowledgeRequest):
            raise KnowledgeContractError("invalid_request")
        response = self._get(provider_id).query(request)
        if not isinstance(response, KnowledgeResponse) or response.request_id != request.request_id:
            raise KnowledgeContractError("provider_response_mismatch")
        requested = set(request.sources)
        returned = {item.source for item in response.sources}
        if returned != requested:
            raise KnowledgeContractError("provider_source_mismatch")
        return response

    def _get(self, provider_id: str) -> ExternalKnowledgeProvider:
        if not isinstance(provider_id, str) or not _PROVIDER_RE.fullmatch(provider_id):
            raise KnowledgeContractError("invalid_provider_id")
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KnowledgeContractError("unknown_provider") from exc
