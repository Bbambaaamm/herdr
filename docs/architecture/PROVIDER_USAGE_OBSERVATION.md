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
- `UsageAggregate`: per-task projection that keeps unknown separate from measured
  totals and rejects conflicting observations for one transport attempt.
- `observe_usage(...)`: the single normalization entry point.
- `select_billable(...)`: returns observations keyed by
  `(request_id, attempt_index)`; every delivered attempt and unresolved delivery
  state remains visible. Conflicting records for one attempt fail closed.
- `billable_cost_microusd(...)`: returns a known cost or `None`. `None` is the only
  representation of an unknown cost; it must never be coerced to zero.

Invariants enforced in `__post_init__`:

1. `MEASURED` requires all four buckets, a delivered response and no unknown
   reasons.
2. `PARTIAL` requires output coverage (output is directly reported for every API
   mode) plus explicit unknown reasons; it contributes **no** token totals to the
   aggregate (a missing bucket is not 0).  `input_tokens` may be missing when
   chat/codex cache metadata is incomplete and uncached input cannot be derived;
   the directly reported output and cache buckets remain valid evidence. A
   confirmed `actual_cost_microusd` still contributes to the aggregate.
3. `UNKNOWN` carries no token buckets and an explicit reason.  Malformed evidence
   (`provider_malformed`) always degrades the whole observation to `UNKNOWN`.
   It rejects a claimed confirmed actual cost until delivery is reconciled.
4. `NON_BILLABLE` remains a reserved schema status. The adapter currently rejects
   it because no verified route authority is available. A caller-supplied route
   label cannot establish a concrete zero cost.
5. A cache bucket that exceeds the provider-reported input total is malformed
   evidence, not a clamped number.  The comparison is against that total: the
   chat/codex prompt total, and `input + cache_read + cache_write` for Anthropic.
6. Cost is computed exactly once from the normalized buckets:
   `uncached_input*input_rate + cache_read*cache_read_rate +
   cache_write*cache_write_rate + output*output_rate`. Normalization is not
   repeated in the price computation, so cached tokens are never charged twice.
7. Unknown cost requires `cost_unknown_reason`; known cost forbids it.
8. `cost_state` is `measured`, `partial`, `unknown` or `non_billable`; only
   `non_billable` may render a concrete zero.

## 4. Offline fixtures (`tests/herdr/fixtures/`)

`anthropic_success.json`, `openai_success.json`, `codex_success.json`,
`anthropic_missing_cache.json` — synthetic provider JSON covering successful
calls and missing cache metadata. The scenarios timeout, retry, fallback,
uncertain delivery is produced by the adapter's `DeliveryOutcome` input, not by
network fixtures. A non-billable fixture is deliberately rejected until a
verified route authority exists.

## 5. Boundaries (unchanged)

- `herdr/telemetry.py`, `herdr/work_budget*.py`, `herdr/routing.py`,
  `herdr/fallback_recovery.py`, `herdr/scheduler_routing.py`,
  `herdr/host_model_transport.py` are **not modified**.
- The adapter cannot reserve, release, settle, retry, fallback or authorize; it
  has no socket, subprocess, file-write or SDK dependency.
- No model call, router change, budget change, deployment or restart was made.

## 5a. Telemetry bridge identity guard

`herdr/usage_telemetry.py` is the measurement-only projection seam.  Its
`telemetry_usage_fields` / `usage_telemetry_event` require the projected
`provider` and `model` to satisfy the *telemetry* token contract
(`herdr.telemetry._TOKEN`, the closed class `[A-Za-z0-9._:/@+-]`), not merely the
adapter's `_token`, which rejects only empty, whitespace, backslash and NUL.
An identifier such as `provider;evil` passes the adapter but is outside the
telemetry character class; the bridge fails closed with `TelemetryError` instead
of letting the closed telemetry contract drop or misattribute the row.  This
reuses `herdr.telemetry._token` verbatim, so the two contracts cannot drift.
The same guard lives in the `UsageTelemetry` value object (`__post_init__`), so
it covers every projection path — a direct `project_usage_telemetry` call cannot
build (or serialize via `to_json`) a row whose provider/model telemetry would
reject; `telemetry_usage_fields` / `usage_telemetry_event` inherit it.

## 6. Follow-up required before this can be wired in

1. Telemetry event needs cache-read/cache-write fields (or a bounded
   `usage_observation_id` reference) — a separate contract change.
   **Partially landed:** the telemetry schema now carries an optional bounded
   `usage_observation_id` digest reference (`herdr/telemetry.py`, validated with
   the existing `_sha`), and the bridge populates it from the source observation
   (`herdr/usage_telemetry.py`, `TELEMETRY_USAGE_FIELDS`).  A usage row is now
   addressable without a prompt, response, credential or free text.  Cache-read
   and cache-write remain telemetry fields owned by the existing contract; this
   reference does not add them and does not change any economic authority.
2. `prompt_runtime.py` / `context.py` placeholders need a bounded reference to an
   observation id rather than free text.
3. `host_model_transport.py` offline fixture usage lacks cache metadata, so a
   fixture-driven adapter run reports `PARTIAL`, not `MEASURED`.
4. Pricing version must be pinned per route from `work_budget_configuration`
   `model_quotes`; the adapter accepts it but does not invent it.

## 7. Economic reconciliation rules (P1 review)

- **One normalization.** `observe_usage` converts the provider prompt total to
  uncached input exactly once (chat/codex subtract cache buckets; Anthropic
  `input_tokens` is already uncached). `_estimate` never subtracts cache again.
- **Cache buckets are validated against the provider input total.** chat/codex:
  `cache_read + cache_write` may not exceed the reported prompt total. Anthropic:
  the buckets are independent of `input_tokens`, so they are not bounded by it.
  Contradiction on chat/codex degrades the whole row to `UNKNOWN` (no buckets).
- **Cost is computed once** from `uncached_input*input_rate +
  cache_read*cache_read_rate + cache_write*cache_write_rate + output*output_rate`.
  Parametric tests cover cache hit 0 % / 50 % / 90 % / 100 % for chat, codex and
  Anthropic, including Anthropic cache-write.
- **Uncertain delivery is never a zero.** An uncertain attempt remains in
  `select_billable` alongside any later delivered attempt. Its cost stays
  unknown until provider evidence resolves it; the later attempt cannot erase it.
- **Non-billable needs verified route authority.** Neither a boolean nor a
  caller-supplied route name proves that a provider waived the charge. The
  adapter rejects both, and also rejects direct `NON_BILLABLE` records, until an
  existing host authority can supply a verifiable route contract.
- **Idempotent projection.** `UsageAggregate.add()` treats
  `(request_id, attempt_index)` as transport identity. Identical replay is a
  no-op; different content for the same identity is a conflict, never a second
  token or cost addition. No second budget settlement is introduced.
- **Derived fields are not trusted input.** `from_json` recomputes `coverage` and
  `cost_state` and rejects a payload whose supplied values disagree.
