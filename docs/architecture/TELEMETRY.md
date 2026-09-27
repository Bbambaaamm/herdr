# Unified Herdr telemetry

The module herdr/telemetry.py is the authoritative provider- and consumer-neutral event contract for Swarm state.

## Contract

Every event has a monotonic sequence, UTC timestamp, issue/task/parent/attempt/agent/role identity and a closed set of operational fields. Model/provider/router/fallback, token usage, latency, runtime, queue wait, cost, tool names, Git artifact SHAs, validator/reviewer result, retry/blocker and optional resource usage are represented directly.

The schema intentionally has no prompt, response, raw tool arguments, credential, log-text or arbitrary metadata field. Unknown fields fail closed during replay.

## Cost semantics

Costs are integer micro-USD. actual_cost_microusd = null requires an explicit CostUnknownReason. A known or estimated cost requires an explicit pricing version. PricingRegistry versions input/output/cached token rates and returns a reason instead of silently inventing zero.

## Replay and aggregation

TelemetryStore is append-only JSONL and assigns the authoritative sequence. materialize() deterministically recreates per-task state plus issue/agent/model/day aggregates. Out-of-order or mutated events fail closed.

Fallbacks are first-class model_fallback events and therefore remain visible in replay and aggregation.

## Live read boundary

read_since(sequence) and sse_since(sequence) provide bounded, read-only incremental delivery. They do not grant mutation authority and contain only the closed telemetry schema. Machine City can consume this stream/read model without parsing prose logs.

## Retention

The source event log remains append-only. Retention is applied to consumers/read windows or external archival; it never rewrites event history in place. The store enforces bounded reads to avoid accidental unbounded dashboard ingestion.
