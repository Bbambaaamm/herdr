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
- Config keys observed in this profile
  (`/home/agentops/.hermes/profiles/quantlab/config.yaml`): `model.default`
  `meituan/longcat-2.5:free` via provider `nous`, `fallback_providers: []`
  (no native chain configured), `fallback.min_switch_reset_seconds: 120`,
  `agent.reasoning_effort: low`. The default profile additionally ships
  `api_max_retries` and `fallback_on` as commented defaults.
- Measured consequence: with an empty `fallback_providers` list and the guard's
  `private_sdk_fallback_not_empty` rejection, the Hermes native chain cannot
  widen the approved provider set here. It is a no-op, not a parallel authority.

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
| Per-task failed-candidate exclusion | EXISTING (`failed_executors` in the handoff) |
| Durable identity / handoff continuity | EXISTING |
| Duplicate economic effect protection (audit replay) | EXISTING |
| Uncertain-delivery reconciliation | EXISTING |
| Native-fallback isolation | EXISTING (chain forced empty) |
| Error taxonomy | PARTIAL (8 kinds) |
| **Retry-After parsing** | **MISSING** |
| **Reset-timestamp normalization** | **MISSING** |
| **Bounded backoff with jitter** | **MISSING** |
| **Provider cooldown expiry** | **PARTIAL** (in-memory, never expires, unwired) |
| Cross-task durable provider cooldown | MISSING (deliberate, see §5) |
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

### Cross-task durable cooldown — deliberately out of scope

Per-task failed-candidate exclusion already exists (`failed_executors` in the
handoff, honoured by `select_managed_route`). A *cross-task* provider cooldown
would need a durable cooldown store. That store is not added here on purpose:
it would be a second health authority next to `RuntimeStateSnapshot.health`
(`herdr/capability.py`), which is the existing authoritative health source with
its own TTL and `reason_code`. Adding a parallel store would violate the
single-authority rule. The correct home is the existing capacity/health
observability work (#126 / #230 / #232) feeding the registry's RuntimeState.

`ProviderCircuitBreaker` remains a local, per-process guard primitive; wiring it
to a durable store is the next decision, not a silent bolt-on.

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

## 11. E4 independent review and remediation

Review by `quantlab-codex` returned **E4 FAIL** in two rounds; every finding was
reproduced and fixed.

Round 1 at HEAD `88daac00` — three P1 and two P2.

| Finding | Fix |
| --- | --- |
| P1: the declared wait was never enforced at dispatch | `ManagedExecutionHandoff.not_before` + `assert_dispatchable()`; `WorkInvocationGuard.authorize_routing_model` calls it on every model authorisation |
| P1: an over-cap hint was shortened into an earlier attempt | parsers return unbounded waits; `plan_retry` fails closed (`deadline_exceeded`) when a hint exceeds the cap or the deadline |
| P1: the new `retry` field broke replay of older durable events | `normalize_transition_event()` + `AuditLog.append_or_get_strict(normalize=...)`; legacy payloads compare equal, genuinely different transitions still conflict |
| P2: `from_json` coerced `"false"` to `True` | strict JSON type checks; non-retryable guidance may not carry a wait |
| P2: `open(now=nan)` stored a NaN expiry forever | non-finite cooldown/reference times rejected |

Regression tests for every finding are in
`tests/herdr/test_router_retry_backoff.py`; the routing/namespace/security set
is 267 passed, 1 skipped.

Round 2 at HEAD `9107ade` — two further P1, both in durable replay.

| Finding | Fix |
| --- | --- |
| P1: a restored handoff lost `not_before`, so replay made an unready route dispatchable | `audit_event()` now serializes `not_before`; regression test asserts the round trip refuses early dispatch |
| P1: a genuine older FALLBACK event without `retry` still raised an audit identity conflict | `normalize_transition_event()` drops the *derived* timing fields (`retry`, `handoff.not_before`) before comparison; replay of an unchanged decision succeeds while a genuinely different transition still conflicts |

Round 3 at HEAD `894ec6c` — one further P1: a re-decision with a weaker
Retry-After (120 s → 0 s) produced a second durable record for the same source
attempt, and the later handoff was immediately dispatchable.

| Finding | Fix |
| --- | --- |
| P1: a later weaker hint could open an earlier retry window | the wait is *not* part of the decision identity; a re-decision replays the durable record (`authoritative_event != event` returns the stored transition), so the first recorded boundary governs. The conflict check stays normalized so derived timing never masquerades as a different decision. Regression test `test_changed_wait_replays_the_durable_boundary` |

Round 4 at HEAD `74019c0` — two backward-compatibility P1: a durable record
written with `retry` but without `not_before` replayed into an immediately
dispatchable handoff, and an older record without `retry` crashed
`from_audit_event`.

| Finding | Fix |
| --- | --- |
| P1: retryable hint without a boundary dispatched immediately | `from_audit_event` replays it as `RetryGuidance(False, None, "unknown")` — "re-decide required", never an immediate dispatch |
| P1: pre-`retry` record crashed replay | same fail-closed reconstruction; a new `"unknown"` guidance source is admitted |

Round 5 at HEAD `0f1895d` — the `"unknown"` marker was advisory only: a restored
transition still carried a handoff without a boundary that accepted an early
dispatch.

| Finding | Fix |
| --- | --- |
| P1: `"unknown"` did not enforce refusal | `ManagedExecutionHandoff.waits_for_provider` is set by every fallback decision; `assert_dispatchable` raises `handoff_wait_unknown` when the boundary is missing, and `from_audit_event` marks legacy handoffs the same way. Verified: both reviewer reproductions now refuse dispatch |

Round 6 at HEAD `de6510d` — a record written before `waits_for_provider` existed
re-decided into `fallback replay conflict`, because the normalizer did not drop
the new enforcement field.

| Finding | Fix |
| --- | --- |
| P1: legacy handoff without `waits_for_provider` conflicted | `normalize_transition_event` also drops `waits_for_provider` (enforcement metadata, not decision identity). Regression test `test_previous_format_without_wait_flag_replays_without_conflict` |

Cumulative: all six rounds of findings are fixed. The local routing/
namespace/security set is 271 passed, 1 skipped, exit 0, and
`scripts/validate_repo.py` reports `HERDR_REPOSITORY_CONTRACT_OK`.

## 12. Remaining blockers and next step

- Cross-task durable provider cooldown: BLOCKED on the capacity/observability
  lane (no new store, no parallel truth).
- Provider portfolio beyond OpenAI/Codex/Anthropic/Nous: BLOCKED on explicit
  operator approval (credentials, terms, spend authority).
- Live fallback pilot: NOT RUN — `AWAITING_EXPLICIT_OPERATOR_APPROVAL`.
- Independent re-review of the remediation: required before this PR is
  undrafted; not yet requested.
