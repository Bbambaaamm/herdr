# Herdr

Herdr is the shared orchestration platform for autonomous project agents.

It owns the generic control plane: durable TaskGraph/DAG planning, dependency-aware scheduling, dynamic child-agent lifecycle, model and tool routing, admission control, budgets, review gates, telemetry, recovery, and Machine City observability.

## Consumers

Herdr is intentionally project-agnostic. Project-specific policy remains in the consumer repository.

- Autonomous-Quant-Lab — quantitative research/trading development; PAPER-only is a consumer invariant.
- dotacni-majak — grant discovery, verification, workflow and delivery.
- heating — heating/Home Assistant engineering; production actuation remains fail-closed behind explicit project policy and human gates.

## Repository boundaries

Herdr owns generic orchestration code and platform deployment assets. It does not own QuantLab trading logic, Maják grant-domain logic, Heating automation logic, credentials, or project data.

The current source was bootstrapped from the verified Agent Platform capture made on 2026-09-26. The original provenance and runtime snapshot are retained under provenance/ and ops/runtime-observed/.

## Current maturity

Version line: 0.x bootstrap / migration.

The platform currently has an externally supplied runtime dependency named herdr 0.9.1, pinned by version and SHA-256. That binary is treated as an external dependency; this repository does not claim its source.

See docs/architecture/OVERVIEW.md, docs/CONSUMERS.md, docs/VERSIONING_AND_DEPLOYMENT.md and docs/migration/FROM_QUANTLAB.md.
