# Agent Platform dashboard

The package contains two deliberately separated surfaces:

- an inert fixture harness (`contracts.py`, `fixtures.py`, `app.py`) for offline tests;
- a production read-only pipeline (`production_*.py`) that collects a bounded,
  sanitized snapshot and serves it from loopback behind independent authentication.

The production web process never opens router databases, the Herdr socket, task
files, repositories, or logs. It reads only an atomically published snapshot. The
one-shot exporter opens explicitly registered sources read-only, uses a closed SQL
authorizer, and publishes `unavailable` on schema, freshness, size, or access errors.
The separate Herdr bridge runs only the fixed `agent list` command and discards raw
fields before publication. No dashboard route dispatches work or changes runtime
state.

Router and Search Router rows include `last_used_at`. The UI calls the provider on
the most recent measured row **current (last run)** and lists other providers only
as historical. This describes observed execution, not configured entitlement or a
promise about the next route. Missing recency metadata fails closed.

Costs remain nullable: `null` means unknown, while zero is a measured zero. Prompts,
queries, tool arguments, model responses, raw errors, credentials, diffs, internal
thoughts, and logs are outside the snapshot contract. IDs are scoped pseudonyms,
not anonymization.

## Verification

From `ops/agent-platform/dashboard`:

```sh
python -m pytest -q tests/agent_platform_dashboard tests/test_observability_contract.py
npm ci
npm test
npm run build
git diff --exit-code -- agent_platform_dashboard/static/machine-city.js
```

The generated browser bundle is committed and rebuilt deterministically in CI.
The Linux production tests cover no-follow I/O, SQLite immutability, bounded
subprocesses, source isolation, authentication, stale/replay rejection, atomic
publication, and service-template hardening.

### Operator-device performance acceptance

Run the committed Machine City bundle against deterministic 12-agent and 30-agent
snapshots in an isolated local Chrome profile:

```sh
npm run benchmark:dashboard:headed
```

The benchmark does not connect to production or reuse the operator's browser
profile. It measures initial interactivity, telemetry-to-visible latency, sustained
frame cadence at both loads, WebGL identity, and reduced-motion behavior at a
1920x1080 viewport. It fails unless the dashboard becomes interactive within
2.5 seconds, shows telemetry changes within 500 ms, reaches display-rate 60 FPS
with 12 active agents, sustains at least 45 FPS with 30 active agents, and preserves
the reduced-motion contract. The JSON report and screenshot are written under
the ignored `dist/` directory. Use `npm run benchmark:dashboard` for the equivalent
headless diagnostic; only the headed run is operator-device acceptance evidence.

## Operational boundary

Deployment and rollback are governed by
`deploy/agent_platform/production/RUNBOOK.md`. Runtime credentials, databases,
socket paths, queue state, and logs never belong in Git. The dashboard is telemetry
only and cannot relax QuantLab's PAPER-only trading invariant.
