# Router v5 cost-aware shadow comparison (prototype only)

**Purpose:** compare the existing deterministic, policy-compliant route with
the least-cost eligible model under declared synthetic task-quality inputs.

This lives inside the existing `herdr.routing` implementation, **not** a
second router. It does not modify `select_route` or live managed handoff,
cannot return a `RoutingDecision`, and cannot reserve/charge budget or
call a model. The output is a `ShadowCostComparison` with
`may_execute=false` and all actual savings fields `null`.

## Algorithm and acceptance

1. Run exactly the existing `select_route` and
   `CapabilityRegistry.candidates` for the same requirement, grant policy,
   runtime state snapshot and time.
2. Require a typed synthetic pass/fail quality declaration for **every**
   eligible executor. Any omitted key or non-boolean declaration fails
   before comparison. These are fixture annotations, not trusted live
   quality observations.
3. Require a known nonnegative cost estimate bound to the exact
   requirement hash for every eligible executor. Otherwise report
   `BLOCKED_UNKNOWN_QUOTE`, not a default zero price.
4. Among *capability + permission + privacy + budget + runtime + synthetic
   quality-pass* candidates choose the lowest price, then stable executor ID.
5. Show the baseline quoted price and hypothetical gap. No projected
   cost saving is an actual token saving; output retains
   `actual_cost_savings_microusd=null` and
   `actual_token_savings=null`. If no quality-approved route exists,
   report `BLOCKED_NO_QUALITY_PASS`.

The existing default routing and scheduler remain unchanged; this helper
does **not** expose an executable route or a policy override. Tests cover
baseline stability, lower-price selection, quality rejection, missing
quality, absent price, budget exclusion and no network side effects.

## Pilot fixture: LoxxessTechnicalAI

Using synthetic `a-runtime` preferred and quoted at **40 microUSD**,
and equally capable `b-runtime` at **5 microUSD**, the normal Router v5
selects A. With declared quality passing for both, shadow selects B.
The hypothetical quote gap is **35 microUSD** for that one synthetic
request. No inference, actual cost, quality or token savings are measured.

## Production gates

Before applying cost-aware ranking to live model calls:

- Independent reviewer assesses how trustworthy grade/benchmark results,
  current pricing version, per-task expected tokens, retry cost and model
  latency are obtained and cryptographically bound to the requirement.
- The quality threshold and fail-closed unknowns become an explicit,
  independently authenticated policy; caller-supplied synthetic booleans
  must never become live ranking authority.
- Replayable offline A/B quality evaluation precedes any permissioned
  small canary; validate task success *after* test/review, not just a
  low token count.
- Existing Herdr #132 root runtime, sandbox, network, signed host
  transport and durable result/ACK gates must all pass. No unapproved
  model calls or issue queue activation.

**Current acceptance: offline shadow evidence only; live routing NO-GO.**
