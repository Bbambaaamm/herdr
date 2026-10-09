"""Host-side Microsoft 365 gateway client.

The gateway is deliberately outside model-visible network authority. It uses a
delegated Entra token cached for the dedicated host account, calls one approved
Power Automate endpoint, and returns bounded source-aware results. Query,
response and token content are never logged here.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urlparse
from uuid import uuid4

TOKEN_RESOURCE = "https://service.flow.microsoft.com/"
DEFAULT_SOURCES = ("outlook", "teams", "sharepoint")
MAX_BODY_BYTES = 2_000_000
MAX_QUERY_CHARS = 16_384
MAX_ANSWER_CHARS = 524_288
_TRANSIENT_CODES = frozenset({
    "NoResponse", "UnexpectedError", "SystemError",
    "ActionResponseTimedOut", "GatewayTimeout", "ServiceUnavailable",
})
_SYSTEM_ERROR_RE = re.compile(r"\bSystemError\b", re.IGNORECASE)


class Source(StrEnum):
    OUTLOOK = "outlook"
    TEAMS = "teams"
    SHAREPOINT = "sharepoint"
    ONEDRIVE = "onedrive"


class ErrorCode(StrEnum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_TRANSIENT = "UPSTREAM_TRANSIENT"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    INVALID_REQUEST = "INVALID_REQUEST"
    GATEWAY_UNAVAILABLE = "GATEWAY_UNAVAILABLE"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True, slots=True)
class GatewayError(Exception):
    code: ErrorCode
    retryable: bool = False
    http_status: int | None = None

    def __str__(self) -> str:
        return self.code.value


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True, slots=True)
class SourceResult:
    source: Source
    status: str
    duration_ms: int
    answer: str | None = None
    conversation_id: str | None = None
    error_code: ErrorCode | None = None
    retryable: bool = False

    def to_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "source": self.source.value,
            "status": self.status,
            "duration_ms": self.duration_ms,
        }
        if self.answer is not None:
            value["answer"] = self.answer
        if self.conversation_id is not None:
            value["conversation_id"] = self.conversation_id
        if self.error_code is not None:
            value["error"] = {
                "code": self.error_code.value,
                "retryable": self.retryable,
            }
        return value


@dataclass(frozen=True, slots=True)
class GatewayResponse:
    request_id: str
    status: str
    answer: str
    sources: tuple[SourceResult, ...]
    partial: bool
    started_at: float
    finished_at: float

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "answer": self.answer,
            "sources": [item.to_dict() for item in self.sources],
            "meta": {
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "partial": self.partial,
            },
        }


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    endpoint_url: str
    tenant_id: str
    azure_config_dir: str
    timeout_seconds: float = 90.0
    poll_timeout_seconds: float = 600.0
    poll_interval_seconds: float = 2.0
    max_attempts: int = 3
    allowed_host_suffix: str = ".environment.api.powerplatform.com"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "GatewayConfig":
        env = os.environ if env is None else env
        url = str(env.get("HERDR_M365_GATEWAY_URL", "")).strip()
        tenant = str(env.get("HERDR_M365_TENANT_ID", "")).strip()
        config_dir = str(env.get("HERDR_M365_AZURE_CONFIG_DIR", "")).strip()
        if not url or not tenant or not config_dir:
            raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE)
        return cls(
            endpoint_url=url,
            tenant_id=tenant,
            azure_config_dir=config_dir,
            timeout_seconds=_bounded_float(env.get("HERDR_M365_TIMEOUT_SECONDS"), 90.0, 5.0, 120.0),
            poll_timeout_seconds=_bounded_float(env.get("HERDR_M365_POLL_TIMEOUT_SECONDS"), 600.0, 10.0, 3600.0),
            poll_interval_seconds=_bounded_float(env.get("HERDR_M365_POLL_INTERVAL_SECONDS"), 2.0, 0.25, 30.0),
            max_attempts=_bounded_int(env.get("HERDR_M365_MAX_ATTEMPTS"), 3, 1, 5),
            allowed_host_suffix=str(
                env.get("HERDR_M365_ALLOWED_HOST_SUFFIX", ".environment.api.powerplatform.com")
            ).strip(),
        )

    def __post_init__(self) -> None:
        _require_endpoint(self.endpoint_url, self.allowed_host_suffix)
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", self.tenant_id):
            raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE)
        path = Path(self.azure_config_dir)
        if not path.is_absolute() or ".." in path.parts:
            raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE)


def _bounded_float(raw: object, default: float, lower: float, upper: float) -> float:
    try:
        value = default if raw in (None, "") else float(str(raw))
    except (TypeError, ValueError):
        raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE) from None
    if not lower <= value <= upper:
        raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE)
    return value


def _bounded_int(raw: object, default: int, lower: int, upper: int) -> int:
    try:
        value = default if raw in (None, "") else int(str(raw))
    except (TypeError, ValueError):
        raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE) from None
    if not lower <= value <= upper:
        raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE)
    return value


def _require_endpoint(url: str, suffix: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    allowed = suffix.lower()
    if (parsed.scheme != "https" or not host or not allowed
            or not host.endswith(allowed) or parsed.username or parsed.password):
        raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE)


class AzureCliTokenProvider:
    """Read an access token from the dedicated host account's Azure CLI cache."""

    def __init__(self, config: GatewayConfig, *,
                 runner: Callable[..., subprocess.CompletedProcess[str]] | None = None):
        self.config = config
        self._runner = subprocess.run if runner is None else runner

    def __call__(self) -> str:
        directory = Path(self.config.azure_config_dir)
        try:
            info = directory.stat()
        except OSError as exc:
            raise GatewayError(ErrorCode.AUTH_REQUIRED) from exc
        if not directory.is_dir() or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise GatewayError(ErrorCode.AUTH_REQUIRED)
        env = dict(os.environ)
        env["AZURE_CONFIG_DIR"] = str(directory)
        try:
            proc = self._runner([
                "az", "account", "get-access-token",
                "--tenant", self.config.tenant_id,
                "--resource", TOKEN_RESOURCE,
                "--query", "accessToken",
                "-o", "tsv",
            ], check=False, capture_output=True, text=True, timeout=20, env=env)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE, retryable=True) from exc
        token = (proc.stdout or "").strip()
        if proc.returncode != 0 or not token:
            stderr = (proc.stderr or "").lower()
            code = ErrorCode.AUTH_REQUIRED if any(term in stderr for term in (
                "az login", "interaction_required", "aadsts", "authentication", "expired",
            )) else ErrorCode.GATEWAY_UNAVAILABLE
            raise GatewayError(code, retryable=code is ErrorCode.GATEWAY_UNAVAILABLE)
        if token.count(".") != 2 or len(token) < 256:
            raise GatewayError(ErrorCode.AUTH_REQUIRED)
        return token


Transport = Callable[[str, str, Mapping[str, str], bytes | None, float], HttpResponse]


def urllib_transport(method: str, url: str, headers: Mapping[str, str],
                     body: bytes | None, timeout: float) -> HttpResponse:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read(MAX_BODY_BYTES + 1)
            if len(payload) > MAX_BODY_BYTES:
                raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE)
            return HttpResponse(int(response.status), dict(response.headers.items()), payload)
    except urllib.error.HTTPError as exc:
        payload = exc.read(MAX_BODY_BYTES + 1)
        if len(payload) > MAX_BODY_BYTES:
            payload = b""
        return HttpResponse(int(exc.code), dict(exc.headers.items()), payload)
    except TimeoutError as exc:
        raise GatewayError(ErrorCode.UPSTREAM_TIMEOUT, retryable=True) from exc
    except urllib.error.URLError as exc:
        raise GatewayError(ErrorCode.GATEWAY_UNAVAILABLE, retryable=True) from exc


class M365Gateway:
    def __init__(self, config: GatewayConfig, *,
                 token_provider: Callable[[], str] | None = None,
                 transport: Transport | None = None,
                 sleep: Callable[[float], None] = time.sleep,
                 now: Callable[[], float] = time.time):
        self.config = config
        self.token_provider = AzureCliTokenProvider(config) if token_provider is None else token_provider
        self.transport = urllib_transport if transport is None else transport
        self.sleep = sleep
        self.now = now

    def health(self) -> dict[str, object]:
        try:
            self.token_provider()
        except GatewayError as exc:
            return {
                "status": "auth_required" if exc.code is ErrorCode.AUTH_REQUIRED else "unavailable",
                "error": exc.code.value,
            }
        return {"status": "ready"}

    def query(self, query: str, *, sources: tuple[Source | str, ...] = tuple(DEFAULT_SOURCES),
              conversation_id: str | None = None, request_id: str | None = None) -> GatewayResponse:
        checked_query = _query(query)
        checked_sources = _sources(sources)
        if conversation_id is not None and len(checked_sources) != 1:
            raise GatewayError(ErrorCode.INVALID_REQUEST)
        request_id = _request_id(request_id)
        started = self.now()
        results: dict[Source, SourceResult] = {}
        with ThreadPoolExecutor(max_workers=len(checked_sources)) as pool:
            futures = {
                pool.submit(self._query_source, source, checked_query, conversation_id): source
                for source in checked_sources
            }
            for future in as_completed(futures):
                source = futures[future]
                try:
                    results[source] = future.result()
                except GatewayError as exc:
                    results[source] = SourceResult(
                        source=source, status="error", duration_ms=0,
                        error_code=exc.code, retryable=exc.retryable)
                except Exception:
                    results[source] = SourceResult(
                        source=source, status="error", duration_ms=0,
                        error_code=ErrorCode.INTERNAL_ERROR, retryable=False)
        ordered = tuple(results[source] for source in checked_sources)
        succeeded = [item for item in ordered if item.status == "ok"]
        partial = len(succeeded) != len(ordered)
        status = "completed" if succeeded else "error"
        answer = "\n\n".join(
            f"[{item.source.value.upper()}]\n{item.answer}" for item in succeeded if item.answer
        )
        return GatewayResponse(
            request_id, status, answer, ordered, partial, started, self.now())

    def _query_source(self, source: Source, query: str,
                      conversation_id: str | None) -> SourceResult:
        started = self.now()
        prompt = _source_prompt(source, query)
        last_error: GatewayError | None = None
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                answer, returned_conversation = self._invoke(prompt, conversation_id)
                return SourceResult(
                    source=source, status="ok",
                    duration_ms=max(0, int((self.now() - started) * 1000)),
                    answer=answer, conversation_id=returned_conversation)
            except GatewayError as exc:
                last_error = exc
                if not exc.retryable or attempt >= self.config.max_attempts:
                    raise
                self.sleep(min(2 ** (attempt - 1), 8))
        raise last_error or GatewayError(ErrorCode.INTERNAL_ERROR)

    def _invoke(self, prompt: str, conversation_id: str | None) -> tuple[str, str | None]:
        token = self.token_provider()
        payload: dict[str, object] = {"query": prompt}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        response = self.transport(
            "POST", self.config.endpoint_url,
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
            body, self.config.timeout_seconds)
        if response.status == 202:
            location = _header(response.headers, "Location")
            if not location:
                raise GatewayError(ErrorCode.UPSTREAM_TRANSIENT, retryable=True, http_status=202)
            _require_endpoint(location, self.config.allowed_host_suffix)
            return self._poll(location, token)
        return self._parse_response(response)

    def _poll(self, location: str, token: str) -> tuple[str, str | None]:
        deadline = self.now() + self.config.poll_timeout_seconds
        while self.now() < deadline:
            response = self.transport(
                "GET", location, {"Authorization": f"Bearer {token}"}, None,
                min(self.config.timeout_seconds, 60.0))
            if response.status == 202:
                next_location = _header(response.headers, "Location")
                if next_location:
                    _require_endpoint(next_location, self.config.allowed_host_suffix)
                    location = next_location
                self.sleep(self.config.poll_interval_seconds)
                continue
            return self._parse_response(response)
        raise GatewayError(ErrorCode.UPSTREAM_TIMEOUT, retryable=True)

    def _parse_response(self, response: HttpResponse) -> tuple[str, str | None]:
        if response.status == 401:
            raise GatewayError(ErrorCode.AUTH_REQUIRED, http_status=401)
        if response.status == 403:
            raise GatewayError(ErrorCode.AUTH_FORBIDDEN, http_status=403)
        if response.status == 429:
            raise GatewayError(ErrorCode.RATE_LIMITED, retryable=True, http_status=429)
        if response.status >= 500:
            raise GatewayError(ErrorCode.UPSTREAM_TRANSIENT, retryable=True, http_status=response.status)
        if response.status != 200:
            raise GatewayError(ErrorCode.INVALID_REQUEST, http_status=response.status)
        try:
            data = json.loads(response.body.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise GatewayError(ErrorCode.UPSTREAM_TRANSIENT, retryable=True) from exc
        if not isinstance(data, dict):
            raise GatewayError(ErrorCode.UPSTREAM_TRANSIENT, retryable=True)
        code = data.get("code")
        if isinstance(code, str) and code:
            if code in _TRANSIENT_CODES:
                raise GatewayError(ErrorCode.UPSTREAM_TRANSIENT, retryable=True)
            raise GatewayError(ErrorCode.INTERNAL_ERROR)
        answer = data.get("answer")
        conversation_id = data.get("conversation_id")
        if (not isinstance(answer, str) or not answer.strip()
                or len(answer) > MAX_ANSWER_CHARS
                or (conversation_id is not None and (
                    not isinstance(conversation_id, str) or len(conversation_id) > 256))):
            raise GatewayError(ErrorCode.UPSTREAM_TRANSIENT, retryable=True)
        if _SYSTEM_ERROR_RE.search(answer):
            raise GatewayError(ErrorCode.UPSTREAM_TRANSIENT, retryable=True)
        return answer.strip(), conversation_id


def _header(headers: Mapping[str, str], name: str) -> str | None:
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return str(value)
    return None


def _query(value: object) -> str:
    if not isinstance(value, str):
        raise GatewayError(ErrorCode.INVALID_REQUEST)
    value = value.strip()
    if not value or len(value) > MAX_QUERY_CHARS or "\0" in value:
        raise GatewayError(ErrorCode.INVALID_REQUEST)
    return value


def _sources(values: tuple[Source | str, ...]) -> tuple[Source, ...]:
    if not isinstance(values, tuple) or not 1 <= len(values) <= 4:
        raise GatewayError(ErrorCode.INVALID_REQUEST)
    try:
        checked = tuple(item if isinstance(item, Source) else Source(str(item)) for item in values)
    except ValueError as exc:
        raise GatewayError(ErrorCode.INVALID_REQUEST) from exc
    if len(set(checked)) != len(checked):
        raise GatewayError(ErrorCode.INVALID_REQUEST)
    return checked


def _request_id(value: str | None) -> str:
    if value is None:
        return str(uuid4())
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value):
        raise GatewayError(ErrorCode.INVALID_REQUEST)
    return value


def _source_prompt(source: Source, query: str) -> str:
    scopes = {
        Source.OUTLOOK: (
            "Hledej pouze v Outlook e-mailech, ke kterým má přihlášený uživatel přístup. "
            "Nepoužívej Teams, SharePoint, OneDrive ani veřejný web."
        ),
        Source.TEAMS: (
            "Hledej pouze v Microsoft Teams zprávách a chatech, ke kterým má přihlášený "
            "uživatel přístup. Nepoužívej Outlook, SharePoint, OneDrive ani veřejný web."
        ),
        Source.SHAREPOINT: (
            "Hledej pouze v SharePoint dokumentech, souborech a stránkách, ke kterým má "
            "přihlášený uživatel přístup. Nepoužívej Outlook, Teams, OneDrive ani veřejný web."
        ),
        Source.ONEDRIVE: (
            "Hledej pouze v OneDrive souborech, ke kterým má přihlášený uživatel přístup. "
            "Nepoužívej Outlook, Teams, SharePoint ani veřejný web."
        ),
    }
    return f"{scopes[source]}\n\nUživatelský dotaz:\n{query}"
