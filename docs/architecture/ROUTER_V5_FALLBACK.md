# Router v5 unified routing, fallback and continuity

Status: implemented increment (`feat/router-v5-retry-backoff`), offline-only.
Authority: Herdr Router v5 is the single routing decision authority for
Herdr-managed tasks. Hermes native fallback is an execution mechanism only.

## 1. Current architecture audit

### Hermes (installed runtime)

- CLI: `hermes` 0.21.5, upstream `40d1e95f`, local `ee5ee84a`.
- Native fallback chain: `agent/fallback_cooldown.py`
  (`_provider_reset_delay`, `switch_deferred_by_reset`, `_arm_rate_limit_cooldown`,
  `min_switch_reset_seconds`), `agent/turn_recovery.py`, `agent/turn_api_error.py`
  (`FailoverReason` — 17 reasons, `_try_activate_fallback(reason=..., reset_at=...)`).
- Config keys observed: `fallback_providers`, `fallback_model`, `fallback_on`,
  `fallback.min_switch_reset_seconds`, `api_max_retries`, `auxiliary_model`,
  `fallback_policy`, `delegation.fallback`, `cron.fallback`.

### Herdr

- `herdr/routing.py` — `FailureKind`, `FailureScope`, `ScopeAttestation`,
  `classify_failure`, `select_route`, `bounded_fallback`, `CapabilityRegistry`-driven.
- `herdr/fallback_recovery.py` — `decide_managed_fallback` → RECONCILE / BLOCK /
  TERMINATE / FALLBACK, `ManagedExecutionHandoff`, durable audit with replay
  conflict detection (`append_or_get_strict`).
- `herdr/scheduler_routing.py` — `RoutingInput` / `RoutingRequirements` /
  `ManagedRoute` / `select_managed_route` / `prepare_managed_execution_handoff`.
- `herdr/security.py` — `ProviderCircuitBreaker`, `PolicyDenied`.
- `herdr/hermes_guard.py` — installs a guard into the Hermes CLI for Herdr-managed
  tasks; constrains provider credentials per route.

## 2. Duplication assessment

Single-authority invariant already enforced: for a private SDK / Herdr-managed
task, `_check_private_sdk_agent` rejects a non-empty `_fallback_chain`
(`PolicyDenied("private_sdk_fallback_not_empty")`), and
`herdr/private_profile_namespace.py` asserts `fallback_providers` /
`fallback_model` keys are absent. The Hermes native chain is therefore
**disabled**, not parallel. Herdr's own decision function is the only authority.

No second router, scheduler, budget ledger or recovery manager is introduced by
this increment. It extends `herdr/routing.py`, `herdr/fallback_recovery.py` and
`herdr/security.py` only.

## 3. Gap analysis (before this increment)

| Area | State |
| --- | --- |
| Routing decision authority | EXISTING |
| Bounded candidate fallback | EXISTING |
| Durable identity / handoff continuity | EXISTING |
| Duplicate economic effect protection (audit replay) | EXISTING |
| Uncertain-delivery reconciliation | EXISTING |
| Native-fallback isolation | EXISTING (chain forced empty) |
| Error taxonomy | PARTIAL (8 kinds) |
| **Retry-After parsing** | **MISSING** |
| **Reset-timestamp normalization** | **MISSING** |
| **Bounded backoff with jitter** | **MISSING** |
| **Provider cooldown expiry** | **PARTIAL** (in-memory, never expires) |
| Provider capability matrix | MISSING |
| Provider portfolio breadth | PARTIAL (openai, anthropic, codex, nous only) |
| Measured-quality adaptive routing | PARTIAL (#74 eval framework, no router feedback) |

## 4. Provider capability matrix (read-only, unmeasured)

No live or free inference probe was performed; a free call is still an external
model call. Capacity, rate limits and pricing are therefore UNKNOWN.

| Provider | Transport | Tool calling | Structured output | Context | Pricing | Free tier | Auth | Contract |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nous | MEASURED (integrated) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | MEASURED | EXISTING |
| OpenAI / Codex | MEASURED (integrated) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | MEASURED | EXISTING |
| Anthropic | MEASURED (integrated) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | MEASURED | EXISTING |
| OpenRouter Free | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NOT INTEGRATED | MISSING |
| Google Gemini | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NOT INTEGRATED | MISSING |
| GroqCloud | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NOT INTEGRATED | MISSING |
| Ollama / LM Studio | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | n/a | n/a | NOT INTEGRATED | MISSING |

Adding a provider requires a credential, an egress path and an authorization
grant. That is a HUMAN/PRIVILEGE gate, not a technical decision.

## 5. Unified routing / fallback design

1. A failed attempt is classified by `classify_failure(status, message, model_known)`.
2. `plan_retry` derives one bounded wait from explicit `Retry-After`, then a
   normalized reset timestamp, then capped exponential backoff with
   deterministic jitter. The wait is clamped to the task deadline; if it cannot
   fit, the decision is TERMINATE (fail closed).
3. `decide_managed_fallback` keeps its existing order: uncertain delivery →
   RECONCILE, terminal policy/budget → BLOCK, untrusted scope → BLOCK, attempt
   or fallback budget exhausted → TERMINATE, otherwise FALLBACK with a handoff.
   The handoff carries the same `task_id`, `run_token`, `fencing_token`, attempt
   counter, budget allocation id and both decision digests, so a provider switch
   preserves durable identity.
4. `ProviderCircuitBreaker` now has a real expiry: a cooldown never widens to
   another provider and never permanently removes a candidate.

## 6. Error taxonomy

`FailureKind` now distinguishes recovery budgets:

- `RATE_LIMITED` — transient fair-share 429.
- `RATE_LIMIT_QUOTA` — durable quota exhaustion (retryable candidate-locally,
  but a different candidate must still be approved).
- `PROVIDER_UNAVAILABLE`, `PROVIDER_SERVER_ERROR`, `TRANSPORT_TIMEOUT`.
- `AUTH_INVALID` — terminal.
- `MODEL_NOT_FOUND`, `CONTEXT_LIMIT`, `TOOL_INCOMPATIBLE`, `CAPABILITY_MISMATCH`.
- `INSUFFICIENT_CREDITS` — candidate-local, allows another approved candidate.
- `BUDGET_EXCEEDED`, `POLICY_DENIED` — terminal.
- `UNKNOWN`.

Retryable set: rate limits, provider/transport errors, model-not-found,
insufficient credits, and capability/context/tool gaps. Non-retryable: policy,
budget, auth, unknown.

## 7. Test plan coverage

`tests/herdr/test_router_retry_backoff.py` covers: delta-seconds and HTTP-date
Retry-After, epoch and ISO reset hints, naive-timestamp rejection, unusable
values, wait capping, deadline clamping, transient vs quota 429, the new status
taxonomy, per-provider cooldown expiry, audit round-trip of retry guidance, and
the managed-fallback wiring.

Not covered here (needs a live provider or eval harness): measured latency
p50/p95, real free-tier capacity, and quality-aware promotion.

## 8. Budget accounting

Unchanged. The existing WorkBudget ledger, `UsageAggregate` coverage rules and
`billable_cost_microusd()` remain authoritative. A provider switch's cache miss
is input-token cost and must be recorded by the existing usage observation
(#222/#233); this increment adds no cost path.

## 9. Staged rollout

- Stage 0 read-only audit — done.
- Stage 1 implementation + offline fixtures — this increment.
- Stage 2 independent security review + exact-head CI — pending.
- Stage 3 shadow routing — pending.
- Stage 4 zero-provider E2E — pending.
- Stage 5 approved limited live pilot — gated.
- Stage 6 measurement and promotion — gated.
- Stage 7 long-term autonomy integration — gated.

## 10. Missing credentials / permissions

- Offsite backup credentials: NOT VERIFIED (`rclone invalid_grant`).
- Staging capacity: BLOCKED (2.0 GB free of 75 GB).
- Live provider probes: not authorized.
- New provider accounts: not authorized.
