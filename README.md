# Herdr

Herdr is the shared orchestration platform for autonomous project agents.

It owns the generic control plane: durable TaskGraph/DAG planning, dependency-aware scheduling, dynamic child-agent lifecycle, model and tool routing, admission control, budgets, review gates, telemetry, recovery, and Machine City observability.

## Consumers

Herdr is intentionally project-agnostic. Project-specific policy remains in the consumer repository.

- Autonomous-Quant-Lab — quantitative research/trading development; PAPER-only is a consumer invariant.
- dotacni-majak — grant discovery, verification, workflow and delivery.
- heating — heating/Home Assistant engineering; production actuation remains fail-closed behind explicit project policy and human gates.

## Canonical source

- `agent_platform_dashboard/` — Machine City, production read models and dashboard service.
- `agent-stack/` — current task/worker/watchdog operational tooling.
- `integrations/search-router/` — cost-aware web/search routing integration.
- `deploy/agent_platform/production/` — reviewed deployment templates and launch entrypoint.
- `runtime/` — current Git-backed runtime unit baseline.
- `tests/` — Python production/telemetry contracts.
- `package.json` + `scripts/build.mjs` — deterministic Machine City browser build.

The repository was initially bootstrapped from the verified 2026-09-26 capture. Before runtime cutover it was reconciled against the newer Git-backed QuantLab Q3 lineage and the independent Search Router lineage. Exact source SHAs and migration reasoning are recorded in `docs/migration/QUANTLAB_LINEAGE.md` and `provenance/quantlab-lineage/LINEAGE.json`.

The original source/runtime capture remains under `provenance/` and `ops/runtime-observed/` for audit and rollback evidence; it is not the current source baseline.

## Repository boundaries

Herdr owns generic orchestration code and platform deployment assets. It does not own QuantLab trading logic, Maják grant-domain logic, Heating automation logic, credentials, or project data.

## Current maturity

Version line: 0.x migration / contract stabilization.

The platform currently has an externally supplied runtime dependency named `herdr 0.9.1`, pinned by version and SHA-256. That binary is treated as an external dependency; this repository does not claim its source.

See `docs/architecture/OVERVIEW.md`, `docs/CONSUMERS.md`, `docs/VERSIONING_AND_DEPLOYMENT.md`, `docs/migration/FROM_QUANTLAB.md` and `docs/migration/QUANTLAB_LINEAGE.md`.
