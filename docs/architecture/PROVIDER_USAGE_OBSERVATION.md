# #222 — Provider usage observation contract (design note)

Status: adapter implemented on `feat/222-provider-usage-observation`, tests green.
Wiring into the telemetry event stream and into Router v5 is deliberately **out of
scope** for this change; see "Boundaries" below.

## 1. What the audit found on `origin/main` (HEAD `d58283b`)

| Concern | Existing authority | Cache-read / cache-write | Billed cost | Pricing version |
| --- | --- | --- | --- | --- |
| Budget reservation + settlement | `herdr/work_budget.py`, `work_budget_configuration.py` (`BudgetSnapshot`) | none | `max_cost_microusd` (ceiling) | `pricing_version` in `model_quotes` (host configuration) |
| Route/retry/fallback decision | `herdr/routing.py`, `fallback_recovery.py`, `scheduler_routing.py` | none | none | none |
| Telemetry event | `herdr/telemetry.py` (`TelemetryEvent`, `PricingRegistry`, `CostUnknownReason`) | `cached_tokens` only | `estimated_cost_microusd`, `actual_cost_microusd`, `cost_unknown_reason` | via `PricingEntry.version` |
| Prompt/context envelope | `herdr/prompt_runtime.py`, `herdr/context.py` | placeholder `"cache_usage": "UNKNOWN"`, `"provider_usage": "UNKNOWN"` | none | none |
| Host transport | `herdr/host_model_transport.py` | offline fixture emits `prompt_tokens`/`completion_tokens` only | none | none |
| Codex account export | `agent-stack/bin/agent-codex-usage-export` | read-only account/billing export, no cache split, no per-response contract | daily cost aggregates | none |

No `ProviderAdapter`, `UsageObservation`, `provider_usage` module or cache-split
field exists anywhere on `origin/main`, `feat/230-capacity-attestor`,
`feat/100-capacity-attestor`, `feature/router-v5-cost-aware-shadow-20261116` or
`codex/router-v5-*`. The only occurrences of `ProviderAdapter` are historical
documentation. So the narrow adapter was genuinely missing and is implemented
here rather than duplicated.

## 2. Provider field coverage (what each adapter actually reports)

Wire shapes recognized by the adapter (`ApiMode`):

| Bucket | `chat_completions` | `anthropic_messages` | `codex_responses` |
| --- | --- | --- | --- |
| input (uncached) | `prompt_tokens` minus cached | `input_tokens` (already uncached) | `input_tokens` minus cached |
| output | `completion_tokens` / `output_tokens` | `output_tokens` | `output_tokens` |
| cache read | `prompt_tokens_details.cached_tokens`, `cache_read_input_tokens`, `prompt_cache_hit_tokens`, `cached_tokens` | `cache_read_input_tokens` | `input_tokens_details.cached_tokens` |
| cache write | `prompt_tokens_details.cache_write_tokens`, `...cache_creation_input_tokens`, `cache_write_tokens`, `cache_writes` | `cache_creation_input_tokens` | `input_tokens_details.cache_write_tokens` / `...cache_creation_tokens` |
| billed cost | not reported by any of these APIs | not reported | not reported |
| pricing version | not reported; must be pinned from `PricingRegistry` | same | same |

Provider-reported "billed cost" and "pricing version" are **not** available from
response bodies. Cost is therefore always derived from pinned rates
(`PricingObservation`) times measured buckets, or marked unknown. The contract
never invents a rate and never invents a cost.

## 3. Contract

`herdr/provider_usage.py`:

- `UsageStatus`: `MEASURED`, `PARTIAL`, `UNKNOWN`, `NON_BILLABLE`.
- `UsageObservation`: frozen, typed, closed-field record; `observation_id` is a
  canonical SHA-256 of the payload, so a row is addressable without a prompt,
  response, credential or arbitrary metadata.
- `PricingObservation`: `pricing_version` + per-million rates, resolvable from the
  existing `PricingRegistry` (`from_registry`) or supplied by the caller.
- `DeliveryOutcome`: `DELIVERED`, `TIMEOUT`, `RETRY_SUPERSEDED`,
  `FALLBACK_SUPERSEDED`, `UNCERTAIN`, `FAILED`.
- `UsageAggregate`: per-task projection that keeps unknown and non-billable
  separate from measured totals.
- `observe_usage(...)`: the single normalization entry point.
- `select_billable(...)`: reconciles attempts of one economic `request_id`;
  only a `DELIVERED` attempt bills, so retries/fallbacks/uncertain delivery are
  never charged twice.

Invariants enforced in `__post_init__`:

1. `MEASURED` requires all four buckets, a delivered response and no unknown
   reasons.
2. `PARTIAL` requires input+output coverage plus explicit unknown reasons; it
   contributes **no** token totals to the aggregate (a missing bucket is not 0).
3. `UNKNOWN` carries no token buckets and an explicit reason.
4. `NON_BILLABLE` is the only status that may carry a concrete zero cost, and only
   with `non_billable_route`.
5. A core bucket that is malformed or absent degrades the whole observation to
   `UNKNOWN` instead of reporting a partial sum.
6. A cache bucket larger than the reported input total is malformed evidence, not
   a clamped number.
7. Unknown cost requires `cost_unknown_reason`; known cost forbids it.

## 4. Offline fixtures (`tests/herdr/fixtures/`)

`anthropic_success.json`, `openai_success.json`, `codex_success.json`,
`anthropic_missing_cache.json` — synthetic provider JSON covering successful
calls and missing cache metadata. The scenarios timeout, retry, fallback,
uncertain delivery and non-billable are produced by the adapter's
`DeliveryOutcome` / `non_billable` inputs, not by network fixtures.

## 5. Boundaries (unchanged)

- `herdr/telemetry.py`, `herdr/work_budget*.py`, `herdr/routing.py`,
  `herdr/fallback_recovery.py`, `herdr/scheduler_routing.py`,
  `herdr/host_model_transport.py` are **not modified**.
- The adapter cannot reserve, release, settle, retry, fallback or authorize; it
  has no socket, subprocess, file-write or SDK dependency.
- No model call, router change, budget change, deployment or restart was made.

## 6. Follow-up required before this can be wired in

1. Telemetry event needs cache-read/cache-write fields (or a bounded
   `usage_observation_id` reference) — a separate contract change.
2. `prompt_runtime.py` / `context.py` placeholders need a bounded reference to an
   observation id rather than free text.
3. `host_model_transport.py` offline fixture usage lacks cache metadata, so a
   fixture-driven adapter run reports `PARTIAL`, not `MEASURED`.
4. Pricing version must be pinned per route from `work_budget_configuration`
   `model_quotes`; the adapter accepts it but does not invent it.
