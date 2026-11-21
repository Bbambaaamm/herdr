"""Read-only bridge from provider usage observations to swarm telemetry.

This is the narrow integration seam between :mod:`herdr.provider_usage`
(normalized provider measurement) and :mod:`herdr.telemetry` (the closed
append-only swarm telemetry contract).  It is measurement-only: it never
reserves, grants, settles, routes, retries, falls back or authorizes anything,
and it never turns an unknown measurement into a concrete zero.

Projection rules (fail-closed):

* Only a ``MEASURED`` observation projects concrete token buckets.  ``PARTIAL``
  and ``UNKNOWN`` rows project ``None`` token fields plus an explicit
  ``cost_unknown_reason``: telemetry has no partial status, and summing only the
  known buckets of a partial row would silently understate usage.
* ``input_tokens`` is the provider prompt total (uncached input plus cache read
  plus cache write) and ``cached_tokens`` is the cache-read/cache-write sum, so
  the telemetry invariant ``cached_tokens <= input_tokens`` holds and the
  adapter's uncached ``input_tokens`` is exactly ``input_tokens - cached_tokens``.
  No bucket is charged twice.
* A confirmed ``actual_cost_microusd`` is preserved even on a ``PARTIAL`` row;
  an unknown cost stays ``None`` and always carries a closed unknown reason.
* ``NON_BILLABLE`` is the only state allowed a concrete zero.  The adapter
  cannot currently produce it because no verified non-billable route authority
  exists, so the bridge keeps the same fail-closed guard.
* ``provider``/``model`` must satisfy the *telemetry* token contract
  (``herdr.telemetry._TOKEN``), not merely the adapter's looser ``_token``.  The
  adapter rejects only whitespace, backslash and NUL; telemetry additionally
  rejects empty values and any character outside ``[A-Za-z0-9._:/@+-]``.  A
  value the adapter accepts but telemetry would reject fails closed here, at the
  boundary, instead of being silently dropped or coerced into another row.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .provider_usage import UsageObservation, UsageStatus
from .telemetry import CostUnknownReason, EventType, TelemetryError, TelemetryEvent
from .telemetry import _token as _telemetry_token

USAGE_TELEMETRY_VERSION = "usage-telemetry-bridge-1"

# The TelemetryEvent kwargs this bridge owns.  Every other telemetry field stays
# with the caller's existing authority; the bridge never invents it.
TELEMETRY_USAGE_FIELDS = (
    "provider",
    "model",
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "estimated_cost_microusd",
    "actual_cost_microusd",
    "cost_unknown_reason",
    "pricing_version",
)


@dataclass(frozen=True)
class UsageTelemetry:
    """Self-describing, read-only projection of one usage observation."""

    observation_id: str
    provider: str
    model: str
    api_mode: str
    request_id: str
    attempt_index: int
    delivery: str
    status: str
    cost_state: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    estimated_cost_microusd: int | None = None
    actual_cost_microusd: int | None = None
    cost_unknown_reason: CostUnknownReason | None = None
    pricing_version: str | None = None
    coverage: Mapping[str, bool] | None = None
    unknown_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.input_tokens is not None and self.cached_tokens is not None:
            if self.cached_tokens > self.input_tokens:
                raise TelemetryError("projected cached_tokens cannot exceed input_tokens")
        if self.actual_cost_microusd is None and self.cost_unknown_reason is None:
            raise TelemetryError("projected unknown actual cost requires cost_unknown_reason")
        if self.actual_cost_microusd is not None and self.cost_unknown_reason is not None:
            raise TelemetryError("projected known actual cost cannot carry cost_unknown_reason")
        if (self.actual_cost_microusd is not None or self.estimated_cost_microusd is not None) \
                and not self.pricing_version:
            raise TelemetryError("projected known/estimated cost requires pricing_version")

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": USAGE_TELEMETRY_VERSION,
            "observation_id": self.observation_id,
            "provider": self.provider,
            "model": self.model,
            "api_mode": self.api_mode,
            "request_id": self.request_id,
            "attempt_index": self.attempt_index,
            "delivery": self.delivery,
            "status": self.status,
            "cost_state": self.cost_state,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "estimated_cost_microusd": self.estimated_cost_microusd,
            "actual_cost_microusd": self.actual_cost_microusd,
            "cost_unknown_reason": (
                self.cost_unknown_reason.value if self.cost_unknown_reason is not None else None
            ),
            "pricing_version": self.pricing_version,
            "coverage": dict(self.coverage or {}),
            "unknown_reasons": list(self.unknown_reasons),
        }


def project_usage_telemetry(observation: UsageObservation) -> UsageTelemetry:
    """Project one observation onto telemetry fields without economic authority.

    The projection is stateless and read-only: it never mutates the observation,
    never deduplicates attempts and never resolves an unknown value.
    """
    if not isinstance(observation, UsageObservation):
        raise TypeError("project_usage_telemetry requires a UsageObservation")
    pricing_version = (
        observation.pricing.pricing_version if observation.pricing is not None else None
    )
    if observation.status is UsageStatus.MEASURED:
        input_tokens = (
            (observation.input_tokens or 0)
            + (observation.cache_read_tokens or 0)
            + (observation.cache_write_tokens or 0)
        )
        cached_tokens = (observation.cache_read_tokens or 0) + (observation.cache_write_tokens or 0)
        return UsageTelemetry(
            observation_id=observation.observation_id,
            provider=observation.provider,
            model=observation.model,
            api_mode=observation.api_mode.value,
            request_id=observation.request_id,
            attempt_index=observation.attempt_index,
            delivery=observation.delivery.value,
            status=observation.status.value,
            cost_state=observation.cost_state,
            input_tokens=input_tokens,
            output_tokens=observation.output_tokens,
            cached_tokens=cached_tokens,
            cache_read_tokens=observation.cache_read_tokens,
            cache_write_tokens=observation.cache_write_tokens,
            estimated_cost_microusd=observation.estimated_cost_microusd,
            actual_cost_microusd=observation.actual_cost_microusd,
            cost_unknown_reason=observation.cost_unknown_reason,
            pricing_version=pricing_version,
            coverage=observation.coverage,
            unknown_reasons=observation.unknown_reasons,
        )
    if observation.status is UsageStatus.NON_BILLABLE:
        # Unreachable through observe_usage today; kept fail-closed so a future
        # verified route authority cannot silently introduce a zero elsewhere.
        return UsageTelemetry(
            observation_id=observation.observation_id,
            provider=observation.provider,
            model=observation.model,
            api_mode=observation.api_mode.value,
            request_id=observation.request_id,
            attempt_index=observation.attempt_index,
            delivery=observation.delivery.value,
            status=observation.status.value,
            cost_state=observation.cost_state,
            input_tokens=observation.input_tokens,
            output_tokens=observation.output_tokens,
            cached_tokens=(
                None if observation.cache_read_tokens is None
                else observation.cache_read_tokens + (observation.cache_write_tokens or 0)
            ),
            cache_read_tokens=observation.cache_read_tokens,
            cache_write_tokens=observation.cache_write_tokens,
            estimated_cost_microusd=0,
            actual_cost_microusd=0,
            cost_unknown_reason=None,
            pricing_version=pricing_version,
            coverage=observation.coverage,
            unknown_reasons=observation.unknown_reasons,
        )
    # PARTIAL and UNKNOWN: no token totals, no estimated cost, unknown cost stays
    # None.  A confirmed actual cost on a PARTIAL row is preserved.
    if observation.actual_cost_microusd is not None:
        cost_unknown_reason = None
    else:
        cost_unknown_reason = (
            observation.cost_unknown_reason or CostUnknownReason.TOKEN_USAGE_MISSING
        )
    return UsageTelemetry(
        observation_id=observation.observation_id,
        provider=observation.provider,
        model=observation.model,
        api_mode=observation.api_mode.value,
        request_id=observation.request_id,
        attempt_index=observation.attempt_index,
        delivery=observation.delivery.value,
        status=observation.status.value,
        cost_state=observation.cost_state,
        input_tokens=None,
        output_tokens=None,
        cached_tokens=None,
        cache_read_tokens=None,
        cache_write_tokens=None,
        estimated_cost_microusd=None,
        actual_cost_microusd=observation.actual_cost_microusd,
        cost_unknown_reason=cost_unknown_reason,
        pricing_version=pricing_version,
        coverage=observation.coverage,
        unknown_reasons=observation.unknown_reasons,
    )


def telemetry_usage_fields(observation: UsageObservation) -> dict[str, Any]:
    """Return the exact TelemetryEvent kwargs owned by this bridge.

    The provider/model pair must satisfy the *telemetry* token contract, not just
    the adapter's.  The adapter's ``_token`` rejects only whitespace, backslash
    and NUL, so it accepts identifiers that ``herdr.telemetry`` would reject;
    projecting those would either be silently dropped by the closed telemetry
    contract or coerce the row into an unrelated identity.  Fail closed here.
    """
    projection = project_usage_telemetry(observation)
    try:
        _telemetry_token(projection.provider, "provider", required=True)
        _telemetry_token(projection.model, "model", required=True)
    except TelemetryError as exc:
        raise TelemetryError(
            f"usage observation {projection.observation_id!r} cannot be projected"
            f" into telemetry: {exc}"
        ) from exc
    return {name: getattr(projection, name) for name in TELEMETRY_USAGE_FIELDS}


def usage_telemetry_event(
    observation: UsageObservation,
    *,
    sequence: int,
    timestamp: str,
    issue: str,
    task_id: str,
    agent_id: str,
    role: str,
    attempt: int = 0,
    event_type: EventType | str = EventType.MODEL_ROUTE,
    retry_count: int = 0,
) -> TelemetryEvent:
    """Build one telemetry event from an observation at the existing boundary.

    The caller supplies the operational envelope (sequence, timestamp, issue,
    task, agent, role); the bridge supplies only the usage projection.  It does
    not append, persist or forward anything.
    """
    fields = telemetry_usage_fields(observation)
    return TelemetryEvent(
        sequence=sequence,
        timestamp=timestamp,
        event_type=EventType(event_type),
        issue=issue,
        task_id=task_id,
        attempt=attempt,
        agent_id=agent_id,
        role=role,
        retry_count=retry_count,
        **fields,
    )
