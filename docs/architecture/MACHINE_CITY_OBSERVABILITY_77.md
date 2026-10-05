# Machine City observability contract (#77)

Machine City is a read-only projection. It does not execute tools, grant approvals, mutate TaskGraph,
merge changes, deploy releases, start experiments, or call model providers.

## Truth model

The production snapshot contains a closed `observability` read model built server-side from already
sanitized durable source projections. Browser code validates and renders this model; it is not allowed
to infer lifecycle authority from log text, queue labels, demo state, or animation.

Every lifecycle/metric row carries:
- source;
- freshness and source age;
- unit and window;
- coverage numerator and denominator;
- reason code when unavailable or partial;
- optional evidence/result hash only when the accepted source actually supplies one.

The lifecycle axes are deliberately separate:
1. `observed_live_execution` — runtime observation only;
2. `delivery_reconciliation` — delivery/reconciliation evidence only;
3. `settled_control_cycle` — durable task control state only;
4. `verified_artifact` — UNKNOWN until the accepted #85 producer is wired;
5. `integrated_change` — UNKNOWN until an accepted integration producer is wired;
6. `deployed_version` — global deployed release identity from the release source. This is not proof
   that a particular task/result was integrated or deployed.

## Sources available on the #77 base

| Projection | Accepted source | Meaning |
| --- | --- | --- |
| runtime / reconcile / settled | `quantlab/swarm` | Observed and durable control state; never artifact verification |
| model router aggregates | `*/router` and Maják `codex` routing summary | Request-weighted tokens/cost/latency/fallback and current aggregate route policy |
| per-node router metrics | task-bound rows in `*/router` | Bounded newest-node slice with explicit node coverage |
| legacy search | `*/search` | Existing Search Router history only; explicitly not #97 Search+Verifier |
| deployed release | `quantlab/release` | Global release tag/commit only |

The read model emits explicit `UNKNOWN / producer_unavailable` rows for producers that are not
accepted into this base, including Execution/Tool Fabric, #97 Search+Verifier, Prompt Runtime,
Human/Event, Eval/Shadow, Budget, Context/Skill bundle, semantic guard, A2A/MCP specialist events,
reviewer outcomes, approval/HITL state, evidence acceptance, execution plan/check runner,
per-route durable decision trace, historical route policy, provider health, and circuit breaker state.

No missing producer is represented by a fabricated zero or PASS.

## Coverage and cost

Router cost/token/duration values are summed only from rows that contain an actual measurement.
A measured zero remains zero. A missing measurement remains `null` with
`reason=measurement_missing` and request-weighted coverage.

Per-node metrics use the source's already-anonymized task identity and derive a bounded display key
from it. The newest bounded node slice publishes an explicit `node_coverage` metric; a partial slice
is never described as complete.

Demo mode changes only the synthetic scene. When a production snapshot is present the UI labels
metrics as coming from that snapshot; when it is absent the UI says production metrics are
unavailable.

## Freshness and projection

Freshness is recomputed at authorized projection time from both source observation time and data
time. Profile projection rebuilds observability from the authorized source subset, preventing
cross-profile values from leaking through a precomputed aggregate.

Legacy charts remain available under a clearly labeled legacy detail section. Missing legacy router
or search sources render UNKNOWN/unavailable, not zero routes or 100% coverage.

## Data excluded

The observability schema is closed and bounded. It does not carry raw prompts, raw tool arguments or
results, credentials, approval tokens, private verifier rubrics, holdout answers, model chain-of-
thought, or unbounded logs.
