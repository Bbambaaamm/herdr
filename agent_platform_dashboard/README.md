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

## Operational boundary

Deployment and rollback are governed by
`deploy/agent_platform/production/RUNBOOK.md`. Runtime credentials, databases,
socket paths, queue state, and logs never belong in Git. The dashboard is telemetry
only and cannot relax QuantLab's PAPER-only trading invariant.
