"""Typed provider usage observation; measurement only, never economic authority.

This module normalizes provider-reported token usage and pricing metadata at the
ProviderAdapter -> telemetry boundary.  It is deliberately separate from
:mod:`herdr.work_budget` (reserved quoted ceilings and their settlement) and
from Router v5 routing decisions: it can never reserve, release, settle, retry,
fallback or authorize anything.

Contract invariants:

* ``UNKNOWN`` never becomes zero.  Every token/cost field is ``None`` unless the
  provider genuinely reported it, and the aggregate projection keeps a separate
  unknown counter instead of adding ``0``.
* ``NON_BILLABLE`` is reserved for a verified route authority. This adapter has
  no such authority yet, so a caller-supplied flag or label is rejected and an
  unknown charge cannot become a concrete zero.
* ``PARTIAL`` is reported whenever some buckets are measured and some are not;
  the per-field ``coverage`` map makes the gap explicit.
* Retry, fallback, timeout and uncertain-delivery reconciliation is keyed by
  ``request_id`` (one economic request) plus ``attempt_index`` (one transport
  attempt).  Only attempts that delivered a billable response are counted.
* Provider-specific field names never reach this contract verbatim and no prompt,
  response, credential or arbitrary metadata field exists here.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Iterable, Mapping

from .evidence import canonical, digest
from .telemetry import CostUnknownReason, PricingRegistry

USAGE_OBSERVATION_VERSION = "provider-usage-observation-1"
MAX_UNKNOWN_REASONS = 8
MAX_NOTES = 8
TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write")


class UsageStatus(StrEnum):
    """Measurement coverage of one provider observation."""

    MEASURED = "measured"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    NON_BILLABLE = "non_billable"


class DeliveryOutcome(StrEnum):
    """What actually happened to the transport attempt that produced this row."""

    DELIVERED = "delivered"
    TIMEOUT = "timeout"
    RETRY_SUPERSEDED = "retry_superseded"
    FALLBACK_SUPERSEDED = "fallback_superseded"
    UNCERTAIN = "uncertain_delivery"
    FAILED = "failed"


class UsageFieldError(ValueError):
    """A provider usage payload violated the closed normalization contract."""


class UnknownReason(StrEnum):
    """Explicit, bounded reasons a measurement is absent or incomplete."""

    PROVIDER_OMITTED = "provider_omitted"
    PROVIDER_MALFORMED = "provider_malformed"
    CONTRADICTORY = "contradictory"
    PRICING_MISSING = "pricing_missing"
    PRICING_STALE = "pricing_stale"
    NON_BILLABLE_ROUTE = "non_billable_route"
    DELIVERY_UNCERTAIN = "delivery_uncertain"
    TRANSPORT_FAILED = "transport_failed"


class ApiMode(StrEnum):
    """Closed set of wire shapes the adapter is allowed to normalize."""

    CHAT_COMPLETIONS = "chat_completions"
    ANTHROPIC_MESSAGES = "anthropic_messages"
    CODEX_RESPONSES = "codex_responses"


# Candidate provider field paths per wire shape: input/prompt total, output,
# cache read, cache write.  The first present path wins; a present-but-invalid
# value is a malformed observation, never a silent zero.
_CHAT_SHAPE = (
    (("prompt_tokens",), ("input_tokens",)),
    (("completion_tokens",), ("output_tokens",)),
    (("prompt_tokens_details", "cached_tokens"),
     ("cache_read_input_tokens",), ("prompt_cache_hit_tokens"), ("cached_tokens")),
    (("prompt_tokens_details", "cache_write_tokens"),
     ("prompt_tokens_details", "cache_creation_input_tokens"),
     ("cache_creation_input_tokens",), ("cache_write_tokens",), ("cache_writes",)),
)
_ANTHROPIC_SHAPE = (
    (("input_tokens",),),
    (("output_tokens",),),
    (("cache_read_input_tokens",),),
    (("cache_creation_input_tokens",),),
)
_CODEX_SHAPE = (
    (("input_tokens",),),
    (("output_tokens",),),
    (("input_tokens_details", "cached_tokens"),),
    (("input_tokens_details", "cache_write_tokens"),
     ("input_tokens_details", "cache_creation_tokens")),
)


def _nested(raw: Any, path: tuple[str, ...]) -> tuple[bool, Any]:
    """Return ``(present, value)`` for a bounded nested field path."""
    node = raw
    for key in path:
        if type(node) is not dict or key not in node:
            return False, None
        node = node[key]
    return True, node


def _count(value: Any, field: str) -> int:
    if type(value) is not int or isinstance(value, bool) or value < 0 or value > 10**15:
        raise UsageFieldError(f"{field} must be a bounded non-negative integer")
    return value


def _first_present(raw: Any, paths: tuple[tuple[str, ...], ...], field: str) -> int | None:
    for path in paths:
        present, value = _nested(raw, path)
        if not present:
            continue
        return _count(value, field)
    return None


def _token(value: str, name: str) -> str:
    if (type(value) is not str or not value or len(value) > 256
            or any(character.isspace() or character in "\\\x00" for character in value)):
        raise UsageFieldError(f"{name} must be a bounded safe token")
    return value


def _unknown_reasons(values: Iterable[str]) -> tuple[str, ...]:
    reasons: list[str] = []
    for value in values:
        try:
            reason = UnknownReason(value)
        except ValueError as exc:
            raise UsageFieldError("unknown reason outside closed contract") from exc
        if reason.value not in reasons:
            reasons.append(reason.value)
    if len(reasons) > MAX_UNKNOWN_REASONS:
        raise UsageFieldError("unknown reason set exceeds bounded contract")
    return tuple(reasons)


def _notes(values: Iterable[str]) -> tuple[str, ...]:
    notes: list[str] = []
    for value in values:
        if type(value) is not str or not value or len(value) > 256:
            raise UsageFieldError("note must be a bounded token")
        if value not in notes:
            notes.append(value)
    if len(notes) > MAX_NOTES:
        raise UsageFieldError("note set exceeds bounded contract")
    return tuple(notes)


@dataclass(frozen=True)
class PricingObservation:
    """Pinned per-million rates actually used, plus their provenance."""

    pricing_version: str
    input_microusd_per_million: int
    output_microusd_per_million: int
    cache_read_microusd_per_million: int | None = None
    cache_write_microusd_per_million: int | None = None
    currency: str = "USD"

    def __post_init__(self) -> None:
        _token(self.pricing_version, "pricing_version")
        for name in ("input_microusd_per_million", "output_microusd_per_million",
                     "cache_read_microusd_per_million", "cache_write_microusd_per_million"):
            value = getattr(self, name)
            if value is None:
                continue
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 10**12:
                raise UsageFieldError(f"{name} must be a bounded non-negative integer")
        if self.currency != "USD":
            raise UsageFieldError("pricing observation currently supports USD only")

    @classmethod
    def from_registry(
        cls, registry: PricingRegistry, *, provider: str, model: str, pricing_version: str,
    ) -> "PricingObservation | None":
        """Resolve an existing :class:`PricingRegistry` entry without inventing rates.

        Reuses the registry's own pinned entry; nothing is estimated here.
        """
        key = (provider, model, pricing_version)
        for entry in tuple(getattr(registry, "_entries", {}).values()):
            if (entry.provider, entry.model, entry.version) == key:
                return cls(
                    pricing_version=entry.version,
                    input_microusd_per_million=entry.input_microusd_per_million,
                    output_microusd_per_million=entry.output_microusd_per_million,
                    cache_read_microusd_per_million=entry.cached_microusd_per_million,
                )
        return None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PricingObservation":
        fields = {"pricing_version", "input_microusd_per_million", "output_microusd_per_million",
                  "cache_read_microusd_per_million", "cache_write_microusd_per_million", "currency"}
        if type(raw) is not dict or set(raw) - fields:
            raise UsageFieldError("closed pricing observation required")
        return cls(**{key: raw[key] for key in fields if key in raw})


@dataclass(frozen=True)
class UsageObservation:
    """One provider-reported measurement, or the explicit record that none exists."""

    schema_version: str
    provider: str
    model: str
    api_mode: ApiMode
    request_id: str
    attempt_index: int
    delivery: DeliveryOutcome
    status: UsageStatus
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    pricing: PricingObservation | None = None
    estimated_cost_microusd: int | None = None
    actual_cost_microusd: int | None = None
    cost_unknown_reason: CostUnknownReason | None = None
    unknown_reasons: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    reported_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != USAGE_OBSERVATION_VERSION:
            raise UsageFieldError("unsupported usage observation version")
        _token(self.provider, "provider")
        _token(self.model, "model")
        _token(self.request_id, "request_id")
        try:
            object.__setattr__(self, "api_mode", ApiMode(self.api_mode))
            object.__setattr__(self, "delivery", DeliveryOutcome(self.delivery))
            object.__setattr__(self, "status", UsageStatus(self.status))
        except ValueError as exc:
            raise UsageFieldError("usage observation enum outside closed contract") from exc
        if self.status is UsageStatus.NON_BILLABLE:
            raise UsageFieldError("non-billable route authority is unavailable")
        if type(self.attempt_index) is not int or isinstance(self.attempt_index, bool) or self.attempt_index < 0:
            raise UsageFieldError("attempt_index must be a non-negative integer")
        for name in TOKEN_FIELDS:
            value = getattr(self, name + "_tokens")
            if value is None:
                continue
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 10**15:
                raise UsageFieldError(f"{name}_tokens must be a bounded non-negative integer")
        # No cross-bucket bound here: ``input_tokens`` is uncached input for every
        # API mode, so a cache bucket may legitimately exceed it (a 100% cache hit
        # yields input_tokens == 0).  Contradictions against the provider-reported
        # input total are rejected in ``observe_usage`` before normalization.
        if (self.cache_read_tokens is None) != (self.cache_write_tokens is None):
            # Missing cache metadata is a coverage gap, not a contradiction; the
            # aggregate reports it through unknown_cache_observations.
            pass
        if self.input_tokens is None and self.status is UsageStatus.MEASURED:
            raise UsageFieldError("measured observation requires input coverage")
        if self.output_tokens is None and self.status in (
                UsageStatus.MEASURED, UsageStatus.PARTIAL):
            # Output is directly reported for every API mode; a row without it has
            # no trustworthy measurement.  Input may legitimately be missing in a
            # PARTIAL row when cache metadata prevents deriving uncached input.
            raise UsageFieldError("measured/partial observation requires output coverage")
        object.__setattr__(self, "unknown_reasons", _unknown_reasons(self.unknown_reasons))
        object.__setattr__(self, "notes", _notes(self.notes))
        if self.reported_sha256 is not None and (
                type(self.reported_sha256) is not str
                or len(self.reported_sha256) != 64
                or any(character not in "0123456789abcdef" for character in self.reported_sha256)):
            raise UsageFieldError("reported_sha256 must be lowercase sha256")
        self._require_coverage()
        self._require_cost()

    def _require_coverage(self) -> None:
        measured = tuple(name for name in TOKEN_FIELDS if getattr(self, name + "_tokens") is not None)
        if self.status is UsageStatus.MEASURED:
            if len(measured) != len(TOKEN_FIELDS):
                raise UsageFieldError("measured observation requires every token bucket")
            if self.delivery is not DeliveryOutcome.DELIVERED:
                raise UsageFieldError("measured observation requires a delivered response")
            if self.unknown_reasons:
                raise UsageFieldError("measured observation cannot carry unknown reasons")
            return
        if self.status is UsageStatus.NON_BILLABLE:
            if not measured and not self.unknown_reasons:
                raise UsageFieldError("non-billable observation requires a reason")
            if UnknownReason.NON_BILLABLE_ROUTE.value not in self.unknown_reasons:
                raise UsageFieldError("non-billable status requires the non-billable route reason")
            return
        if self.status is UsageStatus.PARTIAL:
            if not measured:
                raise UsageFieldError("partial observation requires at least one measured bucket")
            if self.output_tokens is None:
                raise UsageFieldError("partial observation must state output coverage")
            if not self.unknown_reasons:
                raise UsageFieldError("partial observation requires explicit unknown reasons")
            return
        if self.status is UsageStatus.UNKNOWN:
            if measured:
                raise UsageFieldError("unknown observation cannot carry measured buckets")
            if self.delivery is DeliveryOutcome.DELIVERED:
                raise UsageFieldError("unknown status cannot describe a delivered response")
            if not self.unknown_reasons:
                raise UsageFieldError("unknown observation requires explicit unknown reasons")
            return
        raise UsageFieldError("unreachable usage status")

    def _require_cost(self) -> None:
        for name in ("estimated_cost_microusd", "actual_cost_microusd"):
            value = getattr(self, name)
            if value is None:
                continue
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 10**15:
                raise UsageFieldError(f"{name} must be a bounded non-negative integer")
            if value == 0 and self.status is not UsageStatus.NON_BILLABLE:
                raise UsageFieldError("zero cost requires verified non-billable route authority")
        if self.status is UsageStatus.NON_BILLABLE:
            # A concrete zero is only permitted when the provider says the route is included.
            if self.actual_cost_microusd is not None and self.actual_cost_microusd != 0:
                raise UsageFieldError("non-billable observation cannot carry a non-zero actual cost")
            if self.estimated_cost_microusd is not None and self.estimated_cost_microusd != 0:
                raise UsageFieldError("non-billable observation cannot carry a non-zero estimated cost")
        if self.actual_cost_microusd is not None:
            if self.cost_unknown_reason is not None:
                raise UsageFieldError("known actual cost cannot carry cost_unknown_reason")
        elif self.cost_unknown_reason is None and self.status is not UsageStatus.NON_BILLABLE:
            raise UsageFieldError("unknown actual cost requires cost_unknown_reason")
        if self.cost_unknown_reason is not None:
            try:
                object.__setattr__(self, "cost_unknown_reason", CostUnknownReason(self.cost_unknown_reason))
            except ValueError as exc:
                raise UsageFieldError("cost unknown reason outside closed contract") from exc
            if self.cost_unknown_reason is CostUnknownReason.NON_BILLABLE:
                raise UsageFieldError("non-billable route authority is unavailable")
        if (self.actual_cost_microusd is not None or self.estimated_cost_microusd is not None):
            if self.pricing is None:
                raise UsageFieldError("known or estimated cost requires pinned pricing")
        if self.pricing is None and (self.status is UsageStatus.MEASURED or self.estimated_cost_microusd is not None):
            raise UsageFieldError("measured usage requires pinned pricing")

    @property
    def measured_fields(self) -> tuple[str, ...]:
        return tuple(name for name in TOKEN_FIELDS if getattr(self, name + "_tokens") is not None)

    @property
    def coverage(self) -> dict[str, bool]:
        """Per-field measurement coverage; never inferred from a missing value."""
        return {name: name in self.measured_fields for name in TOKEN_FIELDS}

    @property
    def cost_state(self) -> str:
        """Explicit economic state so a consumer cannot read unknown as zero.

        ``unknown`` means the cost is not known; it is never rendered as a zero.
        ``non_billable`` is the only state allowed a concrete zero.
        """
        if self.status is UsageStatus.NON_BILLABLE:
            return "non_billable"
        if self.status is UsageStatus.UNKNOWN or self.actual_cost_microusd is None:
            return "unknown"
        return "measured" if self.status is UsageStatus.MEASURED else "partial"

    @property
    def observation_id(self) -> str:
        return digest(self.to_json(include_observation_id=False))

    def to_json(self, *, include_observation_id: bool = True) -> dict[str, object]:
        data: dict[str, object] = {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "model": self.model,
            "api_mode": self.api_mode.value,
            "request_id": self.request_id,
            "attempt_index": self.attempt_index,
            "delivery": self.delivery.value,
            "status": self.status.value,
            "cost_state": self.cost_state,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "coverage": self.coverage,
            "pricing": None if self.pricing is None else {
                "pricing_version": self.pricing.pricing_version,
                "input_microusd_per_million": self.pricing.input_microusd_per_million,
                "output_microusd_per_million": self.pricing.output_microusd_per_million,
                "cache_read_microusd_per_million": self.pricing.cache_read_microusd_per_million,
                "cache_write_microusd_per_million": self.pricing.cache_write_microusd_per_million,
                "currency": self.pricing.currency,
            },
            "estimated_cost_microusd": self.estimated_cost_microusd,
            "actual_cost_microusd": self.actual_cost_microusd,
            "cost_unknown_reason": (
                self.cost_unknown_reason.value if self.cost_unknown_reason is not None else None
            ),
            "unknown_reasons": list(self.unknown_reasons),
            "notes": list(self.notes),
            "reported_sha256": self.reported_sha256,
        }
        if include_observation_id:
            data["observation_id"] = self.observation_id
        return data

    @classmethod
    def from_json(cls, raw: Mapping[str, Any]) -> "UsageObservation":
        allowed = set(cls.__dataclass_fields__) | {"observation_id", "coverage", "cost_state"}
        if type(raw) is not dict or set(raw) - allowed:
            raise UsageFieldError("unknown usage observation fields rejected")
        values = dict(raw)
        expected = values.pop("observation_id", None)
        supplied_coverage = values.pop("coverage", None)
        supplied_cost_state = values.pop("cost_state", None)
        pricing = values.get("pricing")
        if pricing is not None:
            values["pricing"] = PricingObservation.from_mapping(pricing)
        observation = cls(**values)
        if expected is not None and expected != observation.observation_id:
            raise UsageFieldError("usage observation_id mismatch")
        # Derived fields are not trusted input: a payload that disagrees with the
        # recomputed coverage or cost state is rejected rather than silently
        # accepted (fail-closed on tampered or stale evidence).
        if supplied_coverage is not None and supplied_coverage != observation.coverage:
            raise UsageFieldError("usage observation coverage mismatch")
        if supplied_cost_state is not None and supplied_cost_state != observation.cost_state:
            raise UsageFieldError("usage observation cost_state mismatch")
        return observation


@dataclass(frozen=True)
class UsageAggregate:
    """Per-task/route aggregate that keeps unknown and non-billable separate."""

    observations: int = 0
    measured_observations: int = 0
    partial_observations: int = 0
    unknown_observations: int = 0
    non_billable_observations: int = 0
    billable_attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    actual_cost_microusd: int = 0
    unknown_cost_observations: int = 0
    unknown_cache_observations: int = 0
    input_coverage: int = 0
    output_coverage: int = 0
    cache_read_coverage: int = 0
    cache_write_coverage: int = 0

    seen_observation_ids: frozenset[str] = frozenset()
    seen_attempts: frozenset[tuple[str, int, str]] = frozenset()

    def add(self, observation: UsageObservation) -> "UsageAggregate":
        # Replay protection: re-ingesting the same evidence event must be a no-op.
        # Identity is the observation digest (content-derived), never a
        # caller-supplied flag, so a replayed ledger entry cannot inflate totals.
        identity = observation.observation_id
        if identity in self.seen_observation_ids:
            return self
        attempt_key = (observation.request_id, observation.attempt_index)
        if any((request_id, attempt_index) == attempt_key
               for request_id, attempt_index, _ in self.seen_attempts):
            raise UsageFieldError("conflicting observation for transport attempt")
        seen = self.seen_observation_ids | {identity}
        attempts = self.seen_attempts | {(*attempt_key, identity)}
        if observation.status is UsageStatus.NON_BILLABLE:
            return replace(self, seen_observation_ids=seen, seen_attempts=attempts,
                           observations=self.observations + 1,
                           non_billable_observations=self.non_billable_observations + 1)
        if observation.status is UsageStatus.UNKNOWN:
            return replace(self, seen_observation_ids=seen, seen_attempts=attempts,
                           observations=self.observations + 1,
                           unknown_observations=self.unknown_observations + 1,
                           unknown_cost_observations=self.unknown_cost_observations + 1)
        # Partial observations never contribute token totals: a bucket that is
        # missing is not zero, and summing only the known buckets would silently
        # understate usage.  Coverage counters still record what was measured.
        fields = observation.measured_fields
        if observation.status is UsageStatus.PARTIAL:
            return replace(
                self,
                seen_observation_ids=seen,
                seen_attempts=attempts,
                observations=self.observations + 1,
                partial_observations=self.partial_observations + 1,
                billable_attempts=self.billable_attempts + int(
                    observation.delivery is DeliveryOutcome.DELIVERED),
                unknown_cost_observations=self.unknown_cost_observations
                + int(observation.actual_cost_microusd is None
                      and observation.cost_unknown_reason is not CostUnknownReason.NON_BILLABLE),
                unknown_cache_observations=self.unknown_cache_observations
                + int(bool({"cache_read", "cache_write"} - set(fields))),
                input_coverage=self.input_coverage + int("input" in fields),
                output_coverage=self.output_coverage + int("output" in fields),
                cache_read_coverage=self.cache_read_coverage + int("cache_read" in fields),
                cache_write_coverage=self.cache_write_coverage + int("cache_write" in fields),
            )
        return replace(
            self,
            seen_observation_ids=seen,
            seen_attempts=attempts,
            observations=self.observations + 1,
            measured_observations=self.measured_observations
            + int(observation.status is UsageStatus.MEASURED),
            partial_observations=self.partial_observations
            + int(observation.status is UsageStatus.PARTIAL),
            billable_attempts=self.billable_attempts + int(observation.delivery is DeliveryOutcome.DELIVERED),
            input_tokens=self.input_tokens + (observation.input_tokens or 0),
            output_tokens=self.output_tokens + (observation.output_tokens or 0),
            cache_read_tokens=self.cache_read_tokens + (observation.cache_read_tokens or 0),
            cache_write_tokens=self.cache_write_tokens + (observation.cache_write_tokens or 0),
            actual_cost_microusd=self.actual_cost_microusd + (observation.actual_cost_microusd or 0),
            unknown_cost_observations=self.unknown_cost_observations + int(
                observation.actual_cost_microusd is None
                and observation.cost_unknown_reason is not CostUnknownReason.NON_BILLABLE),
            unknown_cache_observations=self.unknown_cache_observations
            + int(bool({"cache_read", "cache_write"} - set(fields))),
            input_coverage=self.input_coverage + int("input" in fields),
            output_coverage=self.output_coverage + int("output" in fields),
            cache_read_coverage=self.cache_read_coverage + int("cache_read" in fields),
            cache_write_coverage=self.cache_write_coverage + int("cache_write" in fields),
        )


def _estimate(observation: UsageObservation) -> int | None:
    """Net cost from pinned rates and measured buckets only; never a guess."""
    pricing = observation.pricing
    if pricing is None:
        return None
    buckets = {name: getattr(observation, name + "_tokens") for name in TOKEN_FIELDS}
    if buckets["input"] is None or buckets["output"] is None:
        return None
    for name in ("cache_read", "cache_write"):
        rate = getattr(pricing, name + "_microusd_per_million")
        if buckets[name] is not None and rate is None:
            return None
        if buckets[name] is None:
            return None
    # ``input_tokens`` is already the uncached input: ``observe_usage`` subtracts
    # cache-read/cache-write from the provider prompt total for chat/codex, and
    # Anthropic reports uncached ``input_tokens`` directly.  Subtracting again
    # here would charge cached tokens twice.
    uncached = buckets["input"]
    if uncached < 0:
        raise UsageFieldError("cache buckets cannot exceed input tokens")
    numerator = (uncached * pricing.input_microusd_per_million
                 + (buckets["cache_read"] or 0) * (pricing.cache_read_microusd_per_million or 0)
                 + (buckets["cache_write"] or 0) * (pricing.cache_write_microusd_per_million or 0)
                 + buckets["output"] * pricing.output_microusd_per_million)
    return (numerator + 999_999) // 1_000_000


def observe_usage(
    *,
    provider: str,
    model: str,
    api_mode: ApiMode | str,
    request_id: str,
    attempt_index: int = 0,
    delivery: DeliveryOutcome | str = DeliveryOutcome.DELIVERED,
    usage: Mapping[str, Any] | None = None,
    pricing: PricingObservation | None = None,
    actual_cost_microusd: int | None = None,
    cost_unknown_reason: CostUnknownReason | str | None = None,
    unknown_reasons: Iterable[str] = (),
    notes: Iterable[str] = (),
    non_billable: bool = False,
    non_billable_route: str | None = None,
    reported_sha256: str | None = None,
) -> UsageObservation:
    """Normalize one provider response into the closed observation contract.

    ``usage`` is the raw provider payload (or ``None`` when the provider reported
    nothing).  Nothing is inferred from prefixes, hashes or prior requests: a
    missing field stays ``None`` and produces an explicit unknown reason.

    No verified non-billable route authority is available in this adapter. A
    caller-supplied flag or route label cannot turn an unknown charge into zero.
    """
    if type(non_billable) is not bool or non_billable or non_billable_route is not None:
        raise UsageFieldError("non-billable route authority is unavailable")
    if cost_unknown_reason == CostUnknownReason.NON_BILLABLE:
        raise UsageFieldError("non-billable route authority is unavailable")
    mode = ApiMode(api_mode)
    outcome = DeliveryOutcome(delivery)
    reasons = list(unknown_reasons)
    raw = usage if type(usage) is dict else None
    if raw is None:
        raw = {}
    shape = {ApiMode.CHAT_COMPLETIONS: _CHAT_SHAPE, ApiMode.ANTHROPIC_MESSAGES: _ANTHROPIC_SHAPE,
             ApiMode.CODEX_RESPONSES: _CODEX_SHAPE}[mode]
    buckets: dict[str, int | None] = {}
    for name, paths in zip(TOKEN_FIELDS, shape):
        try:
            buckets[name] = _first_present(raw, paths, name + "_tokens")
        except UsageFieldError:
            buckets[name] = None
            if UnknownReason.PROVIDER_MALFORMED.value not in reasons:
                reasons.append(UnknownReason.PROVIDER_MALFORMED.value)
    # Provider-reported input total, captured before normalization.
    # chat/codex: prompt total already includes cached tokens.
    # anthropic: input_tokens is uncached, so the total adds the cache buckets.
    if mode is ApiMode.ANTHROPIC_MESSAGES:
        base_input = buckets["input"]
        provider_input_total = (
            None if base_input is None
            else base_input + (buckets["cache_read"] or 0) + (buckets["cache_write"] or 0)
        )
    else:
        provider_input_total = buckets["input"]

    # Contradiction check against the provider total, never against the normalized
    # uncached input.  Cache buckets that exceed it are malformed evidence.
    if provider_input_total is not None:
        cache_sum = (buckets["cache_read"] or 0) + (buckets["cache_write"] or 0)
        malformed = cache_sum > provider_input_total
        if not malformed:
            for name in ("cache_read", "cache_write"):
                value = buckets[name]
                if value is not None and value > provider_input_total:
                    buckets[name] = None
                    malformed = True
        if malformed:
            for name in ("input", "cache_read", "cache_write"):
                buckets[name] = None
            if UnknownReason.PROVIDER_MALFORMED.value not in reasons:
                reasons.append(UnknownReason.PROVIDER_MALFORMED.value)

    if mode is not ApiMode.ANTHROPIC_MESSAGES:
        # Normalize the prompt total to uncached input; the normalized ``input``
        # bucket is always uncached input, for every API mode.  Without both cache
        # buckets the uncached input cannot be derived, so it is reported as
        # missing instead of treating the unknown cache write as zero.
        prompt_total = buckets["input"]
        cache_known = (buckets["cache_read"] is not None
                       and buckets["cache_write"] is not None)
        if prompt_total is not None:
            if cache_known:
                buckets["input"] = max(0, prompt_total - (buckets["cache_read"] or 0)
                                       - (buckets["cache_write"] or 0))
            else:
                buckets["input"] = None
                if UnknownReason.PROVIDER_OMITTED.value not in reasons:
                    reasons.append(UnknownReason.PROVIDER_OMITTED.value)
        elif not cache_known:
            if UnknownReason.PROVIDER_OMITTED.value not in reasons:
                reasons.append(UnknownReason.PROVIDER_OMITTED.value)
    if raw:
        reported_sha256 = digest(raw)

    status = UsageStatus.MEASURED
    if UnknownReason.PROVIDER_MALFORMED.value in reasons:
        # Malformed evidence is never reported as a partial measurement: the whole
        # observation degrades to UNKNOWN with no token buckets.
        status = UsageStatus.UNKNOWN
        buckets = {name: None for name in TOKEN_FIELDS}
        if outcome is DeliveryOutcome.DELIVERED:
            outcome = DeliveryOutcome.FAILED
    elif non_billable:
        status = UsageStatus.NON_BILLABLE
        reasons = [UnknownReason.NON_BILLABLE_ROUTE.value]
        notes = tuple(notes) + (f"non_billable_route={non_billable_route}",)
    elif outcome is not DeliveryOutcome.DELIVERED:
        # A response the transport never confirmed cannot be a measured row.
        status = UsageStatus.UNKNOWN
        buckets = {name: None for name in TOKEN_FIELDS}
        if outcome is DeliveryOutcome.DELIVERED:
            outcome = DeliveryOutcome.FAILED
        if not reasons:
            reasons = [UnknownReason.DELIVERY_UNCERTAIN.value
                       if outcome is DeliveryOutcome.UNCERTAIN
                       else UnknownReason.TRANSPORT_FAILED.value]
    elif not raw or all(value is None for value in buckets.values()):
        status = UsageStatus.UNKNOWN
        if outcome is DeliveryOutcome.DELIVERED:
            outcome = DeliveryOutcome.FAILED
        if not reasons:
            reasons = [UnknownReason.PROVIDER_OMITTED.value]
    elif any(value is None for value in buckets.values()):
        status = UsageStatus.PARTIAL
        if not reasons:
            reasons = [UnknownReason.PROVIDER_OMITTED.value]
    if status is UsageStatus.PARTIAL and buckets["output"] is None:
        # Output is always directly reported, never derived, so a missing output
        # bucket means the row carries no trustworthy measurement.  A missing
        # ``input`` is tolerated: uncached input is derived and may be unavailable
        # when cache metadata is incomplete, while output and cache buckets remain
        # valid evidence.
        status = UsageStatus.UNKNOWN
        buckets = {name: None for name in TOKEN_FIELDS}
        if outcome is DeliveryOutcome.DELIVERED:
            outcome = DeliveryOutcome.FAILED

    if status is UsageStatus.NON_BILLABLE:
        actual_cost_microusd = 0
        estimated_cost_microusd = 0
        cost_unknown_reason = None
    else:
        estimated_cost_microusd = None
        if actual_cost_microusd is None:
            if cost_unknown_reason is None:
                if status is UsageStatus.UNKNOWN:
                    cost_unknown_reason = (
                        UnknownReason.DELIVERY_UNCERTAIN.value
                        if outcome is DeliveryOutcome.UNCERTAIN
                        else UnknownReason.TRANSPORT_FAILED.value
                        if outcome in (DeliveryOutcome.TIMEOUT, DeliveryOutcome.FAILED)
                        else UnknownReason.PROVIDER_OMITTED.value)
                else:
                    cost_unknown_reason = (UnknownReason.PRICING_MISSING.value
                                           if pricing is None else UnknownReason.PROVIDER_OMITTED.value)
            if isinstance(cost_unknown_reason, str):
                mapped = {
                    UnknownReason.PRICING_MISSING.value: CostUnknownReason.PRICING_MISSING,
                    UnknownReason.PRICING_STALE.value: CostUnknownReason.PRICING_MISSING,
                    UnknownReason.DELIVERY_UNCERTAIN.value: CostUnknownReason.TOKEN_USAGE_MISSING,
                    UnknownReason.TRANSPORT_FAILED.value: CostUnknownReason.TOKEN_USAGE_MISSING,
                    UnknownReason.PROVIDER_OMITTED.value: CostUnknownReason.PROVIDER_NOT_REPORTED,
                    UnknownReason.PROVIDER_MALFORMED.value: CostUnknownReason.PROVIDER_NOT_REPORTED,
                    UnknownReason.CONTRADICTORY.value: CostUnknownReason.PROVIDER_NOT_REPORTED,
                }.get(cost_unknown_reason)
                cost_unknown_reason = mapped
        else:
            cost_unknown_reason = None

    observation = UsageObservation(
        schema_version=USAGE_OBSERVATION_VERSION,
        provider=provider,
        model=model,
        api_mode=mode,
        request_id=request_id,
        attempt_index=attempt_index,
        delivery=outcome,
        status=status,
        input_tokens=buckets["input"],
        output_tokens=buckets["output"],
        cache_read_tokens=buckets["cache_read"],
        cache_write_tokens=buckets["cache_write"],
        pricing=pricing,
        estimated_cost_microusd=estimated_cost_microusd,
        actual_cost_microusd=actual_cost_microusd,
        cost_unknown_reason=cost_unknown_reason,
        unknown_reasons=tuple(reasons),
        notes=tuple(notes),
        reported_sha256=reported_sha256,
    )
    estimated = _estimate(observation)
    if observation.status is UsageStatus.NON_BILLABLE:
        # A non-billable route carries a concrete zero, never a computed charge.
        estimated = 0
    if estimated is not None:
        observation = replace(observation, estimated_cost_microusd=estimated)
    return observation


def billable_cost_microusd(observation: UsageObservation) -> int | None:
    """Known billed cost in micro-USD, or ``None`` when it is unknown.

    ``None`` is the only representation of an unknown economic cost; callers must
    not coerce it to zero.  A provider-reported actual cost wins; otherwise a
    fully measured row falls back to its pricing-derived estimate.  A ``PARTIAL``
    row whose buckets are incomplete has no cost and stays ``None``.
    ``NON_BILLABLE`` is the sole state allowed a concrete zero, because the
    provider/route itself excluded the call from billing.
    """
    if observation.status is UsageStatus.UNKNOWN:
        return None
    if observation.status is UsageStatus.NON_BILLABLE:
        return 0
    if observation.actual_cost_microusd is not None:
        return observation.actual_cost_microusd
    return observation.estimated_cost_microusd


def select_billable(
    observations: Iterable[UsageObservation],
) -> dict[tuple[str, int], UsageObservation]:
    """Keep every transport attempt for economic reconciliation.

    A delivered retry can be charged separately from an earlier delivered
    attempt. An uncertain attempt remains unknown even when a later fallback
    delivers. The caller must reconcile each attempt with provider evidence;
    this read-only projection never assumes a superseded attempt was free.
    """
    billable: dict[tuple[str, int], UsageObservation] = {}
    for observation in observations:
        if observation.status is UsageStatus.NON_BILLABLE:
            continue
        key = (observation.request_id, observation.attempt_index)
        current = billable.get(key)
        if current is not None and current != observation:
            raise UsageFieldError("conflicting observation for transport attempt")
        billable[key] = observation
    return billable
