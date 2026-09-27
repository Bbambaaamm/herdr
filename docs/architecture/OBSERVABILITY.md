# Agent Platform observability slice (#234)

This slice extends the production read model with bounded, sanitized observability
sources for Machine City. It is stacked on the Git source-of-truth import from PR
#239 and does not deploy or mutate runtime state.

## Sources

- `router`: model/provider, request counts, tokens, fallback count, success, latency,
  optional micro-USD cost.
- `search`: route mode, provider/fallback provider, search success, latency,
  fallback count, results/extracts and optional cost.
- `queue`: sanitized durable Agent Stack queue metadata, schema version 2.
- `admission`: bounded tail of `/var/lib/agent-platform-herdr/admission.jsonl`,
  projected to ALLOW/DENY, reason code, role, repo/issue, DAG dimensions,
  child-tool count and timestamp only. Raw detail/tool arguments are discarded.
- `codex`: sanitized account allowance/token activity from
  `/var/lib/agent-platform-herdr/codex-usage.json`, enriched with bounded
  cost-aware routing summary from `/var/lib/agent-platform-herdr/model-routing.json`:
  FREE/Sol/Astra decisions, Astra escalations, premium-denial count, policy limits
  and the last sanitized route reason/model.

The `codex` source is global account telemetry and is exposed once under the `majak`
profile to keep the existing two-profile snapshot envelope closed and deterministic.

## Safety / unknown semantics

- Prompt text, tool arguments, credentials, account IDs and access tokens are not
  part of the read model.
- Queue input is exact-field validated and rejects unknown fields.
- Codex usage is exact-field validated, bounded to 45 daily buckets and 288 limit
  history points, and becomes stale after 15 minutes.
- Unknown request cost remains `null`; the dashboard must not silently convert it
  to zero or infer subscription cost from API pricing.
- Queue and Codex data are optional observability sources; mandatory startup sources
  remain the existing Herdr/router sources.

## Queue v2

The durable queue projection accepts the current exporter schema with issue title,
open/scheduler state, attempt/max-attempts and PR metadata. This is intentionally
sanitized operational metadata only.

## Verification

Run:

    PYTHONPATH=ops/agent-platform/dashboard \
      python3 -m unittest discover \
      -s ops/agent-platform/dashboard/tests -v

The tests also exercise queue v2 rejection, Codex redaction, search projection and
fail-closed Codex staleness.
