"""Host-only transport from an authenticated Herdr launch to an external knowledge provider.

The model-visible worker never receives provider credentials, endpoint URLs, or
this provider socket. The authenticated bootstrap broker invokes this client
only after the exact peer, grant, mount and work phase have been rechecked.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import stat
from pathlib import Path
from typing import Mapping

from .external_knowledge import (
    KnowledgeContractError,
    KnowledgeErrorCode,
    KnowledgeRequest,
    KnowledgeResponse,
    KnowledgeSourceResult,
)
from .capability import DataClass, Egress
from .security import (InvocationGuard, InvocationIdentity, PolicyDenied, ProviderRequest,
                       ProviderRoute, SECURITY_GRANT_VERSION, SecurityError, SecurityGrant)

POLICY_PATH = Path("/etc/herdr/external-knowledge.json")
PROVIDER_SOCKET_PATH = Path("/run/herdr-external-knowledge/provider.sock")
MAX_POLICY_BYTES = 65_536
MAX_PROVIDER_REQUEST_BYTES = 32_768
MAX_PROVIDER_RESPONSE_BYTES = 2_097_152
_LOG = logging.getLogger(__name__)


class ExternalKnowledgeHostError(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _read_regular_root_policy(path: Path) -> dict[str, object]:
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ExternalKnowledgeHostError("policy_untrusted")
    for parent in reversed(path.parents):
        try:
            info = parent.lstat()
        except OSError as exc:
            raise ExternalKnowledgeHostError("policy_unavailable") from exc
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != 0
                or info.st_mode & 0o022):
            raise ExternalKnowledgeHostError("policy_untrusted")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ExternalKnowledgeHostError("policy_unavailable") from exc
    try:
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != 0
                or before.st_mode & 0o022 or not 0 < before.st_size <= MAX_POLICY_BYTES):
            raise ExternalKnowledgeHostError("policy_untrusted")
        raw = bytearray()
        while len(raw) <= MAX_POLICY_BYTES:
            chunk = os.read(fd, min(65_536, MAX_POLICY_BYTES + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        after = os.fstat(fd)
        named = path.lstat()
        stamp = lambda item: (
            item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns,
            item.st_ctime_ns, item.st_mode, item.st_uid, item.st_nlink,
        )
        if (len(raw) > MAX_POLICY_BYTES or stamp(before) != stamp(after)
                or stamp(before) != stamp(named) or len(raw) != before.st_size):
            raise ExternalKnowledgeHostError("policy_changed")
        raw = bytes(raw)
    finally:
        os.close(fd)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ExternalKnowledgeHostError("policy_invalid") from exc
    if not isinstance(data, dict):
        raise ExternalKnowledgeHostError("policy_invalid")
    return data


def _token(value: object, *, limit: int = 64) -> str:
    import re
    if not isinstance(value, str) or not re.fullmatch(
            r"[a-z][a-z0-9_.-]{0,%d}" % (limit - 1), value):
        raise ExternalKnowledgeHostError("policy_invalid")
    return value


def _consumer_token(value: object) -> str:
    import re
    if (not isinstance(value, str) or len(value) > 256
            or not re.fullmatch(r"[A-Za-z0-9._:/@+-]{1,256}", value)):
        raise ExternalKnowledgeHostError("policy_invalid")
    return value


def _trusted_socket(path: Path) -> os.stat_result:
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ExternalKnowledgeHostError("provider_socket_untrusted")
    parents = list(path.parents)
    for index, parent in enumerate(reversed(parents)):
        try:
            info = parent.lstat()
        except OSError as exc:
            raise ExternalKnowledgeHostError("provider_socket_unavailable") from exc
        # System ancestors stay root-owned. The immediate private runtime
        # directory may be owned by the dedicated host account.
        allowed_uids = {0}
        if parent == path.parent:
            allowed_uids.add(os.geteuid())
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid not in allowed_uids
                or info.st_mode & 0o022):
            raise ExternalKnowledgeHostError("provider_socket_untrusted")
    try:
        info = path.lstat()
    except OSError as exc:
        raise ExternalKnowledgeHostError("provider_socket_unavailable") from exc
    if (not stat.S_ISSOCK(info.st_mode) or info.st_uid not in {0, os.geteuid()}
            or info.st_mode & 0o022):
        raise ExternalKnowledgeHostError("provider_socket_untrusted")
    return info


class HostExternalKnowledgePolicy:
    """Root-owned allowlist. It contains identifiers only, never credentials."""

    def __init__(
        self, consumers: Mapping[str, Mapping[str, tuple[str, ...]]],
        *, provider_capabilities: tuple[ProviderRoute, ...] = (),
    ):
        checked: dict[str, dict[str, tuple[str, ...]]] = {}
        for consumer, providers in consumers.items():
            consumer_id = _consumer_token(consumer)
            if not isinstance(providers, Mapping) or not providers:
                raise ExternalKnowledgeHostError("policy_invalid")
            rows: dict[str, tuple[str, ...]] = {}
            for provider, sources in providers.items():
                provider_id = _token(provider)
                if not isinstance(sources, (tuple, list)) or not 1 <= len(sources) <= 16:
                    raise ExternalKnowledgeHostError("policy_invalid")
                parsed = tuple(_token(source) for source in sources)
                if len(set(parsed)) != len(parsed):
                    raise ExternalKnowledgeHostError("policy_invalid")
                rows[provider_id] = tuple(sorted(parsed))
            checked[consumer_id] = rows
        self._consumers = checked
        # These facts come only from root-owned host configuration, never from
        # model arguments or provider response claims. Missing facts deny use.
        self._capabilities: dict[str, ProviderRoute] = {}
        for route in provider_capabilities:
            if (not isinstance(route, ProviderRoute)
                    or route.provider in self._capabilities
                    or route.api_mode != "external_knowledge"
                    or len(route.regions) != 1
                    or len(route.credential_refs) > 1
                    or route.max_egress is Egress.NONE):
                raise ExternalKnowledgeHostError("policy_invalid")
            self._capabilities[route.provider] = route

    @classmethod
    def from_file(cls, path: Path = POLICY_PATH) -> "HostExternalKnowledgePolicy":
        raw = _read_regular_root_policy(path)
        version = raw.get("version")
        expected = {"version", "consumers"}
        if version == 2:
            expected.add("provider_capabilities")
        if type(version) is not int or version not in {1, 2} or set(raw) != expected:
            raise ExternalKnowledgeHostError("policy_invalid")
        capabilities = ()
        if version == 2:
            rows = raw["provider_capabilities"]
            if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
                raise ExternalKnowledgeHostError("policy_invalid")
            try:
                capabilities = tuple(ProviderRoute.from_dict(row) for row in rows)
            except (SecurityError, TypeError, ValueError) as exc:
                raise ExternalKnowledgeHostError("policy_invalid") from exc
        consumers = raw["consumers"]
        if not isinstance(consumers, dict) or not consumers:
            raise ExternalKnowledgeHostError("policy_invalid")
        normalized: dict[str, dict[str, tuple[str, ...]]] = {}
        for consumer, value in consumers.items():
            if not isinstance(value, dict) or set(value) != {"providers"}:
                raise ExternalKnowledgeHostError("policy_invalid")
            providers = value["providers"]
            if not isinstance(providers, dict):
                raise ExternalKnowledgeHostError("policy_invalid")
            normalized[consumer] = {
                provider: tuple(sources) if isinstance(sources, list) else sources
                for provider, sources in providers.items()
            }
        return cls(normalized, provider_capabilities=capabilities)

    def allows(self, consumer: str, provider_id: str, sources: tuple[str, ...]) -> bool:
        providers = self._consumers.get(consumer)
        if providers is None:
            return False
        allowed = providers.get(provider_id)
        return allowed is not None and set(sources) <= set(allowed)

    def authorize(
        self, grant: SecurityGrant, provider_id: str, request: KnowledgeRequest,
    ) -> None:
        if not self.allows(grant.identity.consumer, provider_id, request.sources):
            raise PolicyDenied("external_knowledge_source_denied")
        capabilities = self._capabilities.get(provider_id)
        if capabilities is None:
            raise PolicyDenied("external_knowledge_capabilities_unverified")
        matching = [route for route in grant.provider_routes if route.provider == provider_id]
        if len(matching) != 1:
            raise PolicyDenied("provider_route_missing")
        route = matching[0]
        if (route.base_url != capabilities.base_url
                or route.api_mode != capabilities.api_mode
                or route.credential_refs != capabilities.credential_refs):
            raise PolicyDenied("external_knowledge_destination_denied")
        # No declassification proof exists for arbitrary model-controlled text.
        # Conservatively classify the entire query/conversation as SENSITIVE.
        # Neither the model nor the remote provider can select a lower class.
        if DataClass.SENSITIVE not in capabilities.data_classes:
            raise PolicyDenied("data_class_denied")
        InvocationGuard(grant).authorize_provider(ProviderRequest(
            provider=provider_id,
            region=capabilities.regions[0],
            data_class=DataClass.SENSITIVE,
            egress=capabilities.max_egress,
            retention=capabilities.max_retention,
            training=capabilities.training,
            credential_ref=(capabilities.credential_refs[0]
                            if capabilities.credential_refs else None),
        ))


def _error_response(
    request: KnowledgeRequest,
    code: KnowledgeErrorCode,
    *,
    retryable: bool = False,
) -> KnowledgeResponse:
    rows = tuple(
        KnowledgeSourceResult(
            source=source,
            status="error",
            duration_ms=0,
            error_code=code,
            retryable=retryable,
        )
        for source in request.sources
    )
    return KnowledgeResponse(
        request_id=request.request_id,
        status="error",
        answer="",
        sources=rows,
        partial=False,
    )


def _read_line(connection: socket.socket, limit: int) -> bytes:
    data = bytearray()
    while len(data) <= limit:
        chunk = connection.recv(min(65_536, limit + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        if b"\n" in data:
            line, _, trailing = bytes(data).partition(b"\n")
            if trailing:
                raise ExternalKnowledgeHostError("provider_protocol_invalid")
            return line
    raise ExternalKnowledgeHostError("provider_response_invalid")


class HostExternalKnowledgeClient:
    """Trusted host client for a provider daemon hidden from the worker sandbox."""

    def __init__(
        self,
        *,
        policy_path: Path = POLICY_PATH,
        socket_path: Path = PROVIDER_SOCKET_PATH,
        timeout_seconds: float = 900.0,
        grant: SecurityGrant | None = None,
    ):
        if (not isinstance(timeout_seconds, (int, float))
                or not 1 <= float(timeout_seconds) <= 900):
            raise ExternalKnowledgeHostError("invalid_timeout")
        self.policy_path = Path(policy_path)
        self.socket_path = Path(socket_path)
        self.timeout_seconds = float(timeout_seconds)
        self._grant = grant

    def query(
        self,
        identity: InvocationIdentity,
        grant_sha256: str,
        provider_id: str,
        request: KnowledgeRequest,
    ) -> KnowledgeResponse:
        import re
        if (not isinstance(identity, InvocationIdentity)
                or not isinstance(grant_sha256, str)
                or re.fullmatch(r"[0-9a-f]{64}", grant_sha256) is None
                or not isinstance(request, KnowledgeRequest)):
            return _error_response(request, KnowledgeErrorCode.INVALID_REQUEST)
        try:
            grant = self._grant
            if (not isinstance(grant, SecurityGrant)
                    or grant.schema_version != SECURITY_GRANT_VERSION
                    or grant.identity != identity or grant.hash != grant_sha256
                    or not grant.is_active()
                    or "herdr_external_knowledge" not in grant.scope.tools):
                raise PolicyDenied("external_knowledge_grant_mismatch")
            provider_id = _token(provider_id)
            policy = HostExternalKnowledgePolicy.from_file(self.policy_path)
            policy.authorize(grant, provider_id, request)
            _trusted_socket(self.socket_path)
            payload = json.dumps(
                {
                    "version": 1,
                    "provider_id": provider_id,
                    "request": request.to_dict(),
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8") + b"\n"
            if len(payload) > MAX_PROVIDER_REQUEST_BYTES:
                return _error_response(request, KnowledgeErrorCode.INVALID_REQUEST)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(self.timeout_seconds)
                connection.connect(str(self.socket_path))
                # Reopen protected host policy at the delivery boundary: a
                # source revocation or capability change during connect denies.
                policy = HostExternalKnowledgePolicy.from_file(self.policy_path)
                policy.authorize(grant, provider_id, request)
                connection.sendall(payload)
                raw = _read_line(connection, MAX_PROVIDER_RESPONSE_BYTES)
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict) or set(parsed) != {"response"}:
                raise ExternalKnowledgeHostError("provider_protocol_invalid")
            response = KnowledgeResponse.from_dict(parsed["response"])
            if (response.request_id != request.request_id
                    or {item.source for item in response.sources} != set(request.sources)):
                raise ExternalKnowledgeHostError("provider_response_mismatch")
            return response
        except (PolicyDenied, SecurityError) as exc:
            reason = exc.reason if isinstance(exc, PolicyDenied) else "external_knowledge_grant_invalid"
            # Closed reason codes only: never log query, conversation, response,
            # endpoint, credentials, or arbitrary exception text.
            _LOG.warning("external_knowledge_denied reason=%s", reason)
            return _error_response(request, KnowledgeErrorCode.AUTH_FORBIDDEN)
        except (OSError, TimeoutError):
            return _error_response(
                request, KnowledgeErrorCode.PROVIDER_UNAVAILABLE, retryable=True
            )
        except ExternalKnowledgeHostError as exc:
            if exc.reason.startswith("policy_"):
                _LOG.warning("external_knowledge_denied reason=%s", exc.reason)
                return _error_response(request, KnowledgeErrorCode.AUTH_FORBIDDEN)
            return _error_response(
                request,
                KnowledgeErrorCode.PROVIDER_UNAVAILABLE,
                retryable=exc.reason in {
                    "provider_socket_unavailable",
                    "provider_response_invalid",
                },
            )
        except (KnowledgeContractError, UnicodeError, ValueError):
            return _error_response(request, KnowledgeErrorCode.PROVIDER_UNAVAILABLE)


def bind_external_knowledge_host(bootstrap, grant, authority) -> None:
    """Attach host-only provider transport only when the signed tool is granted."""
    if "herdr_external_knowledge" not in grant.scope.tools:
        return
    if not callable(authority):
        raise ExternalKnowledgeHostError("durable_authority_required")
    bootstrap.external_knowledge_authority = authority
    bootstrap.external_knowledge_query = HostExternalKnowledgeClient(grant=grant).query
