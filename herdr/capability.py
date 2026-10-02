"""Offline, provider-neutral capability registry contract v1.

Declarations are immutable. Runtime observations and grants are supplied by
the caller, so matching does not inspect process state or call providers.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Mapping

VERSION = "1.0.0"
_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]{1,256}$")
_SECRET_KEYS = ("secret", "token", "password", "passwd", "apikey", "api_key",
                "api-key", "access_key", "accesskey", "credential", "private_key", "privatekey")
_SECRET_VALUES = tuple(re.compile(x) for x in (
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", r"\bghp_[A-Za-z0-9]{20,}\b",
    r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", r"\bsk-[A-Za-z0-9_-]{20,}\b",
    r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", r"\bAKIA[0-9A-Z]{16}\b",
    r"\bAIza[0-9A-Za-z_-]{20,}\b"))
_TOKEN_FIELDS = frozenset({"context_tokens", "max_input_tokens", "max_output_tokens",
                           "min_context_tokens", "min_input_tokens", "min_output_tokens",
                           "max_context_tokens"})
# Upper bound for a runtime observation TTL: rejects absurd values at construction
# so freshness arithmetic can never overflow the datetime range.
MAX_TTL_SECONDS = 315_360_000


class CapabilityError(ValueError):
    """A capability contract is malformed or incompatible."""


def _token(value: str, name: str) -> None:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise CapabilityError(f"{name} must be a safe nonempty identifier")


def _number(value: int | None, name: str) -> None:
    if value is not None and (type(value) is not int or value < 0):
        raise CapabilityError(f"{name} must be a nonnegative integer or null")


def _set(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise CapabilityError(f"{name} must be an array")
    for item in value:
        _token(item, name)
        _secrets(item)
    if len(value) != len(set(value)):
        raise CapabilityError(f"{name} contains duplicates")
    return tuple(sorted(value))


def _secrets(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or (key not in _TOKEN_FIELDS and
                    any(fragment in key.lower() for fragment in _SECRET_KEYS)):
                raise CapabilityError("secret-like or invalid key")
            _secrets(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _secrets(item)
    elif isinstance(value, str) and any(pattern.search(value) for pattern in _SECRET_VALUES):
        raise CapabilityError("secret-like value")


def _digest(value: Mapping[str, Any]) -> str:
    _secrets(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _strict(cls: type, raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise CapabilityError(f"{cls.__name__} must be an object")
    _secrets(raw)
    names = {f.name for f in fields(cls)}
    if set(raw) != names:
        raise CapabilityError(f"{cls.__name__} fields differ: {sorted(set(raw) ^ names)}")
    return dict(raw)


def _time(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 64:
        raise CapabilityError("timestamp must be ISO-8601 UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CapabilityError("timestamp must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise CapabilityError("timestamp must be ISO-8601 UTC")
    return parsed


class Egress(StrEnum):
    NONE = "none"
    REGION_BOUND = "region_bound"
    GLOBAL = "global"


class DataClass(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"


class Retention(StrEnum):
    ZERO = "zero"
    LIMITED = "limited"
    INDEFINITE = "indefinite"


class Training(StrEnum):
    EXCLUDED = "excluded"
    ALLOWED = "allowed"


class Latency(StrEnum):
    INTERACTIVE = "interactive"
    STANDARD = "standard"
    BATCH = "batch"


class Feature(StrEnum):
    TOOLS = "tools"
    JSON = "json"
    STREAMING = "streaming"
    REASONING = "reasoning"


class Modality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


def _enum_set(value: Any, name: str, typ: type[StrEnum]) -> tuple[StrEnum, ...]:
    if not isinstance(value, (tuple, list)):
        raise CapabilityError(f"{name} must be an array")
    for item in value:
        if isinstance(item, str) and any(fragment in item.lower() for fragment in _SECRET_KEYS):
            raise CapabilityError("secret-like identifier")
    try:
        items = tuple(sorted((typ(x) for x in value), key=str))
    except ValueError as exc:
        raise CapabilityError(f"unknown typed {name} value") from exc
    if len(items) != len(set(items)):
        raise CapabilityError(f"{name} contains duplicates")
    return items


def _enum(value: Any, name: str, typ: type[StrEnum]) -> StrEnum:
    try:
        return typ(value)
    except (TypeError, ValueError) as exc:
        raise CapabilityError(f"unknown typed {name} value") from exc


class Health(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class Reason(StrEnum):
    UNKNOWN_CAPABILITY = "unknown_capability"
    POLICY_DENIED = "policy_denied"
    FEATURE_MISSING = "feature_missing"
    MODALITY_MISSING = "modality_missing"
    LIMIT_UNKNOWN = "limit_unknown"
    LIMIT_EXCEEDED = "limit_exceeded"
    DATA_POLICY_UNKNOWN = "data_policy_unknown"
    DATA_POLICY_DENIED = "data_policy_denied"
    TOOL_MISSING = "tool_missing"
    RUNTIME_MISSING = "runtime_missing"
    RUNTIME_STALE = "runtime_stale"
    RUNTIME_UNAVAILABLE = "runtime_unavailable"
    RATE_LIMITED = "rate_limited"
    PRICE_UNKNOWN = "price_unknown"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass(frozen=True)
class DataPolicy:
    regions: tuple[str, ...]
    data_classes: tuple[DataClass, ...]
    egress: Egress
    retention: Retention
    training: Training

    def __post_init__(self) -> None:
        object.__setattr__(self, "regions", _set(self.regions, "regions"))
        classes = _enum_set(self.data_classes, "data_classes", DataClass)
        if not self.regions or not classes:
            raise CapabilityError("data regions/classes must be explicit and unique")
        object.__setattr__(self, "data_classes", classes)
        for name, typ in (("egress", Egress), ("retention", Retention), ("training", Training)):
            object.__setattr__(self, name, _enum(getattr(self, name), name, typ))

    def to_json(self) -> dict[str, Any]:
        return {"regions": list(self.regions), "data_classes": list(self.data_classes),
                "egress": self.egress.value, "retention": self.retention.value,
                "training": self.training.value}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> DataPolicy:
        return cls(**_strict(cls, raw))


@dataclass(frozen=True)
class CapabilityDescriptor:
    id: str
    version: str
    spec_id: str
    features: tuple[Feature, ...]
    input_modalities: tuple[Modality, ...]
    output_modalities: tuple[Modality, ...]
    context_tokens: int | None
    max_input_tokens: int | None
    max_output_tokens: int | None
    latency: Latency
    data_policy: DataPolicy
    schema_version: str = VERSION

    def __post_init__(self) -> None:
        if self.schema_version != VERSION:
            raise CapabilityError("incompatible schema version")
        for name in ("id", "version", "spec_id"):
            _token(getattr(self, name), name)
        for name, typ in (("features", Feature), ("input_modalities", Modality),
                          ("output_modalities", Modality)):
            object.__setattr__(self, name, _enum_set(getattr(self, name), name, typ))
        if not self.input_modalities or not self.output_modalities:
            raise CapabilityError("modality direction must be explicit")
        for name in ("context_tokens", "max_input_tokens", "max_output_tokens"):
            _number(getattr(self, name), name)
        if self.context_tokens is not None:
            for name in ("max_input_tokens", "max_output_tokens"):
                declared = getattr(self, name)
                if declared is not None and declared > self.context_tokens:
                    raise CapabilityError(f"{name} exceeds context_tokens")
        object.__setattr__(self, "latency", _enum(self.latency, "latency", Latency))
        if not isinstance(self.data_policy, DataPolicy):
            raise CapabilityError("typed data policy required")
        _secrets(self.to_json())

    def to_json(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "id": self.id, "version": self.version,
                "spec_id": self.spec_id, "features": list(self.features),
                "input_modalities": list(self.input_modalities),
                "output_modalities": list(self.output_modalities),
                "context_tokens": self.context_tokens, "max_input_tokens": self.max_input_tokens,
                "max_output_tokens": self.max_output_tokens, "latency": self.latency.value,
                "data_policy": self.data_policy.to_json()}

    to_hash_json = to_json

    @property
    def hash(self) -> str:
        return _digest(self.to_hash_json())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> CapabilityDescriptor:
        d = _strict(cls, raw)
        d["data_policy"] = DataPolicy.from_dict(d["data_policy"])
        return cls(**d)


@dataclass(frozen=True)
class ProviderDescriptor:
    id: str
    version: str
    capability_refs: tuple[str, ...]
    pricing_version: str
    data_policy: DataPolicy
    transport_modes: tuple[str, ...]
    session_modes: tuple[str, ...]
    schema_version: str = VERSION

    def __post_init__(self) -> None:
        if self.schema_version != VERSION:
            raise CapabilityError("incompatible schema version")
        for name in ("id", "version", "pricing_version"):
            _token(getattr(self, name), name)
        for name in ("capability_refs", "transport_modes", "session_modes"):
            value = _set(getattr(self, name), name)
            if not value:
                raise CapabilityError(f"{name} must be explicit")
            object.__setattr__(self, name, value)
        if not isinstance(self.data_policy, DataPolicy):
            raise CapabilityError("typed data policy required")
        _secrets(self.to_json())

    def to_json(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "id": self.id, "version": self.version,
                "capability_refs": list(self.capability_refs), "pricing_version": self.pricing_version,
                "data_policy": self.data_policy.to_json(), "transport_modes": list(self.transport_modes),
                "session_modes": list(self.session_modes)}

    to_hash_json = to_json

    @property
    def hash(self) -> str:
        return _digest(self.to_json())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> ProviderDescriptor:
        d = _strict(cls, raw)
        d["data_policy"] = DataPolicy.from_dict(d["data_policy"])
        return cls(**d)


@dataclass(frozen=True)
class ExecutorDescriptor:
    id: str
    version: str
    provider_id: str
    capability_id: str
    runtime_id: str
    adapter_id: str
    transport_mode: str
    session_mode: str
    tools: tuple[str, ...]
    schema_version: str = VERSION

    def __post_init__(self) -> None:
        if self.schema_version != VERSION:
            raise CapabilityError("incompatible schema version")
        for name in ("id", "version", "provider_id", "capability_id", "runtime_id",
                     "adapter_id", "transport_mode", "session_mode"):
            _token(getattr(self, name), name)
        object.__setattr__(self, "tools", _set(self.tools, "tools"))
        _secrets(self.to_json())

    def to_json(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "id": self.id, "version": self.version,
                "provider_id": self.provider_id, "capability_id": self.capability_id,
                "runtime_id": self.runtime_id, "adapter_id": self.adapter_id,
                "transport_mode": self.transport_mode, "session_mode": self.session_mode,
                "tools": list(self.tools)}

    to_hash_json = to_json

    @property
    def hash(self) -> str:
        return _digest(self.to_json())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> ExecutorDescriptor:
        return cls(**_strict(cls, raw))


@dataclass(frozen=True)
class CapabilityScope:
    """Closed grant: empty sets deny; null budget ceilings mean unbounded."""
    providers: tuple[str, ...]
    capabilities: tuple[str, ...]
    executors: tuple[str, ...]
    tools: tuple[str, ...]
    permissions: tuple[str, ...]
    regions: tuple[str, ...]
    data_classes: tuple[DataClass, ...]
    input_modalities: tuple[Modality, ...]
    output_modalities: tuple[Modality, ...]
    max_cost_microusd: int | None
    max_context_tokens: int | None

    def __post_init__(self) -> None:
        for name in ("providers", "capabilities", "executors", "tools", "permissions",
                     "regions"):
            object.__setattr__(self, name, _set(getattr(self, name), name))
        for name in ("input_modalities", "output_modalities"):
            object.__setattr__(self, name, _enum_set(getattr(self, name), name, Modality))
        classes = _enum_set(self.data_classes, "data_classes", DataClass)
        object.__setattr__(self, "data_classes", classes)
        for name in ("max_cost_microusd", "max_context_tokens"):
            _number(getattr(self, name), name)

    def is_subset_of(self, parent: CapabilityScope) -> bool:
        if not isinstance(parent, CapabilityScope):
            raise CapabilityError("typed parent scope required")
        for name in ("providers", "capabilities", "executors", "tools", "permissions",
                     "regions", "data_classes", "input_modalities", "output_modalities"):
            if not set(getattr(self, name)) <= set(getattr(parent, name)):
                return False
        for name in ("max_cost_microusd", "max_context_tokens"):
            child, ceiling = getattr(self, name), getattr(parent, name)
            if ceiling is not None and (child is None or child > ceiling):
                return False
        return True

    def require_subset_of(self, parent: CapabilityScope) -> None:
        if not self.is_subset_of(parent):
            raise CapabilityError("child scope escalates above parent")

    def to_json(self) -> dict[str, Any]:
        return {name: list(getattr(self, name)) for name in (
            "providers", "capabilities", "executors", "tools", "permissions", "regions",
            "data_classes", "input_modalities", "output_modalities")} | {
            "max_cost_microusd": self.max_cost_microusd,
            "max_context_tokens": self.max_context_tokens}

    to_hash_json = to_json

    @property
    def hash(self) -> str:
        return _digest(self.to_json())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> CapabilityScope:
        return cls(**_strict(cls, raw))


@dataclass(frozen=True)
class CapabilityRequirement:
    capability_id: str
    features: tuple[Feature, ...]
    input_modalities: tuple[Modality, ...]
    output_modalities: tuple[Modality, ...]
    tools: tuple[str, ...]
    permissions: tuple[str, ...]
    region: str | None
    data_class: DataClass | None
    max_egress: Egress | None
    max_retention: Retention | None
    training: Training | None
    min_context_tokens: int | None
    min_input_tokens: int | None
    min_output_tokens: int | None
    max_cost_microusd: int | None
    preferred_providers: tuple[str, ...] = ()
    legacy_model_hints: tuple[str, ...] = ()
    schema_version: str = VERSION

    def __post_init__(self) -> None:
        if self.schema_version != VERSION:
            raise CapabilityError("incompatible schema version")
        _token(self.capability_id, "capability_id")
        for name, typ in (("features", Feature), ("input_modalities", Modality),
                          ("output_modalities", Modality)):
            object.__setattr__(self, name, _enum_set(getattr(self, name), name, typ))
        for name in ("tools", "permissions", "preferred_providers"):
            object.__setattr__(self, name, _set(getattr(self, name), name))
        if not isinstance(self.legacy_model_hints, (tuple, list)):
            raise CapabilityError("legacy_model_hints must be an array")
        for hint in self.legacy_model_hints:
            if not isinstance(hint, str):
                raise CapabilityError("legacy_model_hints must contain strings")
            _secrets(hint)
        if len(self.legacy_model_hints) != len(set(self.legacy_model_hints)):
            raise CapabilityError("duplicate legacy_model_hints")
        object.__setattr__(self, "legacy_model_hints", tuple(self.legacy_model_hints))
        if self.region is not None:
            _token(self.region, "region")
        for name, typ in (("data_class", DataClass), ("max_egress", Egress),
                          ("max_retention", Retention), ("training", Training)):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _enum(value, name, typ))
        for name in ("min_context_tokens", "min_input_tokens", "min_output_tokens",
                     "max_cost_microusd"):
            _number(getattr(self, name), name)
        _secrets(self.to_json())

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field in fields(self):
            value = getattr(self, field.name)
            result[field.name] = list(value) if isinstance(value, tuple) else value
        return result

    to_hash_json = to_json

    @property
    def hash(self) -> str:
        return _digest(self.to_json())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> CapabilityRequirement:
        return cls(**_strict(cls, raw))


@dataclass(frozen=True)
class RuntimeStateSnapshot:
    executor_id: str
    observed_at: str
    ttl_seconds: int
    health: Health
    remaining_requests: int | None
    estimated_cost_microusd: int | None
    reason_code: str | None

    def __post_init__(self) -> None:
        _token(self.executor_id, "executor_id")
        _time(self.observed_at)
        _number(self.ttl_seconds, "ttl_seconds")
        if self.ttl_seconds is None or not 0 < self.ttl_seconds <= MAX_TTL_SECONDS:
            raise CapabilityError("ttl_seconds must be positive and bounded")
        object.__setattr__(self, "health", _enum(self.health, "health", Health))
        _number(self.remaining_requests, "remaining_requests")
        _number(self.estimated_cost_microusd, "estimated_cost_microusd")
        if self.reason_code is not None:
            _token(self.reason_code, "reason_code")
        if self.health != Health.HEALTHY and self.reason_code is None:
            raise CapabilityError("nonhealthy observation requires reason_code")

    def is_fresh(self, at: str) -> bool:
        now, then = _time(at), _time(self.observed_at)
        if now < then:
            return False
        return (now - then) < timedelta(seconds=self.ttl_seconds)

    def to_json(self) -> dict[str, Any]:
        return {"executor_id": self.executor_id, "observed_at": self.observed_at,
                "ttl_seconds": self.ttl_seconds, "health": self.health.value,
                "remaining_requests": self.remaining_requests,
                "estimated_cost_microusd": self.estimated_cost_microusd,
                "reason_code": self.reason_code}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> RuntimeStateSnapshot:
        return cls(**_strict(cls, raw))


@dataclass(frozen=True)
class RegistrySnapshot:
    capabilities: tuple[CapabilityDescriptor, ...]
    providers: tuple[ProviderDescriptor, ...]
    executors: tuple[ExecutorDescriptor, ...]
    schema_version: str = VERSION

    def __post_init__(self) -> None:
        if self.schema_version != VERSION:
            raise CapabilityError("incompatible schema version")
        for name, typ in (("capabilities", CapabilityDescriptor), ("providers", ProviderDescriptor),
                          ("executors", ExecutorDescriptor)):
            items = getattr(self, name)
            if not isinstance(items, (tuple, list)) or any(not isinstance(x, typ) for x in items):
                raise CapabilityError(f"{name} must contain {typ.__name__}")
            ids = [x.id for x in items]
            if len(ids) != len(set(ids)):
                raise CapabilityError(f"duplicate {name} id")
            object.__setattr__(self, name, tuple(sorted(items, key=lambda x: x.id)))
        caps = {x.id for x in self.capabilities}
        providers = {x.id: x for x in self.providers}
        for provider in self.providers:
            if not set(provider.capability_refs) <= caps:
                raise CapabilityError("unknown capability ref")
        for executor in self.executors:
            provider = providers.get(executor.provider_id)
            if provider is None or executor.capability_id not in provider.capability_refs:
                raise CapabilityError("unknown executor ref")
            if (executor.transport_mode not in provider.transport_modes or
                    executor.session_mode not in provider.session_modes):
                raise CapabilityError("unsupported executor mode")

    def to_json(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version,
                "capabilities": [x.to_json() for x in self.capabilities],
                "providers": [x.to_json() for x in self.providers],
                "executors": [x.to_json() for x in self.executors]}

    to_hash_json = to_json

    @property
    def hash(self) -> str:
        return _digest(self.to_json())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> RegistrySnapshot:
        d = _strict(cls, raw)
        return cls(tuple(CapabilityDescriptor.from_dict(x) for x in d["capabilities"]),
                   tuple(ProviderDescriptor.from_dict(x) for x in d["providers"]),
                   tuple(ExecutorDescriptor.from_dict(x) for x in d["executors"]),
                   d["schema_version"])


@dataclass(frozen=True)
class RouteProvenance:
    registry_hash: str
    capability_hash: str
    provider_hash: str
    executor_hash: str

    def to_json(self) -> dict[str, str]:
        return {"registry_hash": self.registry_hash, "capability_hash": self.capability_hash,
                "provider_hash": self.provider_hash, "executor_hash": self.executor_hash}


@dataclass(frozen=True)
class CapabilityMatch:
    executor_id: str
    provider_id: str
    capability_id: str
    preference_score: int
    provenance: RouteProvenance

    def to_json(self) -> dict[str, Any]:
        return {"executor_id": self.executor_id, "provider_id": self.provider_id,
                "capability_id": self.capability_id, "preference_score": self.preference_score,
                "provenance": self.provenance.to_json()}


@dataclass(frozen=True)
class Rejection:
    executor_id: str | None
    reason: Reason

    def to_json(self) -> dict[str, Any]:
        return {"executor_id": self.executor_id, "reason": self.reason.value}


@dataclass(frozen=True)
class CandidateResult:
    matches: tuple[CapabilityMatch, ...]
    rejections: tuple[Rejection, ...]
    registry_hash: str

    def to_json(self) -> dict[str, Any]:
        return {"matches": [x.to_json() for x in self.matches],
                "rejections": [x.to_json() for x in self.rejections],
                "registry_hash": self.registry_hash}


class CapabilityRegistry:
    def __init__(self, snapshot: RegistrySnapshot | Mapping[str, Any]) -> None:
        self._snapshot = self._parse(snapshot)

    @staticmethod
    def _parse(candidate: RegistrySnapshot | Mapping[str, Any]) -> RegistrySnapshot:
        return candidate if isinstance(candidate, RegistrySnapshot) else RegistrySnapshot.from_dict(candidate)

    @property
    def snapshot(self) -> RegistrySnapshot:
        return self._snapshot

    def reload(self, candidate: RegistrySnapshot | Mapping[str, Any]) -> str:
        validated = self._parse(candidate)
        digest = validated.hash
        self._snapshot = validated
        return digest

    def candidates(self, requirement: CapabilityRequirement, policy: CapabilityScope,
                   runtime_state: tuple[RuntimeStateSnapshot, ...], *, at: str) -> CandidateResult:
        _time(at)
        if not isinstance(requirement, CapabilityRequirement) or not isinstance(policy, CapabilityScope):
            raise CapabilityError("typed requirement and policy required")
        snapshot = self._snapshot
        caps = {x.id: x for x in snapshot.capabilities}
        providers = {x.id: x for x in snapshot.providers}
        if requirement.capability_id not in caps:
            return CandidateResult((), (Rejection(None, Reason.UNKNOWN_CAPABILITY),), snapshot.hash)
        states: dict[str, RuntimeStateSnapshot] = {}
        for state in runtime_state:
            if not isinstance(state, RuntimeStateSnapshot) or state.executor_id in states:
                raise CapabilityError("runtime observations must be typed and unique")
            states[state.executor_id] = state
        cap = caps[requirement.capability_id]
        registry_hash = snapshot.hash
        matches: list[CapabilityMatch] = []
        rejects: list[Rejection] = []
        for executor in snapshot.executors:
            if executor.capability_id != cap.id:
                continue
            provider = providers[executor.provider_id]
            reason = _reject(requirement, policy, cap, provider, executor, states.get(executor.id), at)
            if reason is not None:
                rejects.append(Rejection(executor.id, reason))
                continue
            provenance = RouteProvenance(registry_hash, cap.hash, provider.hash, executor.hash)
            matches.append(CapabilityMatch(executor.id, provider.id, cap.id,
                                           int(provider.id in requirement.preferred_providers), provenance))
        matches.sort(key=lambda x: (-x.preference_score, x.executor_id))
        return CandidateResult(tuple(matches), tuple(rejects), registry_hash)


def _reject(req: CapabilityRequirement, grant: CapabilityScope, cap: CapabilityDescriptor,
            provider: ProviderDescriptor, executor: ExecutorDescriptor,
            state: RuntimeStateSnapshot | None, at: str) -> Reason | None:
    if (cap.id not in grant.capabilities or provider.id not in grant.providers or
        executor.id not in grant.executors or not set(req.permissions) <= set(grant.permissions) or
        not set(req.tools) <= set(grant.tools)):
        return Reason.POLICY_DENIED
    if not set(req.features) <= set(cap.features):
        return Reason.FEATURE_MISSING
    if not set(req.tools) <= set(executor.tools):
        return Reason.TOOL_MISSING
    if (not set(req.input_modalities) <= set(cap.input_modalities) & set(grant.input_modalities) or
        not set(req.output_modalities) <= set(cap.output_modalities) & set(grant.output_modalities)):
        return Reason.MODALITY_MISSING
    for needed, declared in ((req.min_context_tokens, cap.context_tokens),
                             (req.min_input_tokens, cap.max_input_tokens),
                             (req.min_output_tokens, cap.max_output_tokens)):
        if needed is not None and declared is None:
            return Reason.LIMIT_UNKNOWN
        if needed is not None and needed > declared:
            return Reason.LIMIT_EXCEEDED
    # The closed grant's context ceiling applies to every directional token floor,
    # not only to an explicit min_context_tokens.
    grant_context = grant.max_context_tokens
    if grant_context is not None:
        for needed in (req.min_context_tokens, req.min_input_tokens, req.min_output_tokens):
            if needed is not None and needed > grant_context:
                return Reason.POLICY_DENIED
    if (req.region is None or req.data_class is None or req.max_egress is None or
            req.max_retention is None or req.training is None):
        return Reason.DATA_POLICY_UNKNOWN
    if (req.region not in grant.regions or req.data_class not in grant.data_classes or
        req.region not in cap.data_policy.regions or req.region not in provider.data_policy.regions or
        req.data_class not in cap.data_policy.data_classes or req.data_class not in provider.data_policy.data_classes or
        list(Egress).index(cap.data_policy.egress) > list(Egress).index(req.max_egress) or
        list(Egress).index(provider.data_policy.egress) > list(Egress).index(req.max_egress) or
        list(Retention).index(cap.data_policy.retention) > list(Retention).index(req.max_retention) or
        list(Retention).index(provider.data_policy.retention) > list(Retention).index(req.max_retention) or
        cap.data_policy.training != req.training or provider.data_policy.training != req.training):
        return Reason.DATA_POLICY_DENIED
    if state is None:
        return Reason.RUNTIME_MISSING
    if not state.is_fresh(at):
        return Reason.RUNTIME_STALE
    if state.health != Health.HEALTHY:
        return Reason.RUNTIME_UNAVAILABLE
    if state.remaining_requests is None or state.remaining_requests == 0:
        return Reason.RATE_LIMITED
    ceilings = [x for x in (req.max_cost_microusd, grant.max_cost_microusd) if x is not None]
    if ceilings and state.estimated_cost_microusd is None:
        return Reason.PRICE_UNKNOWN
    if ceilings and state.estimated_cost_microusd > min(ceilings):
        return Reason.BUDGET_EXCEEDED
    return None


def requirement_from_v1_model_policy(model_policy: Mapping[str, Any], *, capability_id: str,
                                     tools: tuple[str, ...] = (), permissions: tuple[str, ...] = ()) -> CapabilityRequirement:
    """Read legacy model hints as preferences; never change a persisted node.

    Only values actually copied into the requirement are scanned for secret-like
    material. Opaque legacy keys (including token-limit keys such as ``max_tokens``
    or ``token_budget``) are left untouched and must not be misread as secrets.
    """
    if not isinstance(model_policy, Mapping):
        raise CapabilityError("model_policy must be an object")
    preferred = tuple(dict.fromkeys(x for x in (
        model_policy.get("model"), model_policy.get("fallback_model"))
        if isinstance(x, str)))
    _secrets(preferred)
    return CapabilityRequirement(capability_id, (), (), (), tools, permissions,
                                 None, None, None, None, None, None, None, None, None,
                                 legacy_model_hints=preferred)
