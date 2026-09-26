# Q3 final audit: routers, Herdr, and dashboard

Status: **code complete; live verification and rollout required before production sign-off**.

This audit is based on the latest reviewed Machine City/observability handoff plus
the captured production runtime source. Historical phase reports are not used as
current evidence.

## Closed findings

- Router and Search Router projections now publish bounded `last_used_at` evidence.
- The dashboard labels the provider on the newest measured row as **current (last
  run)** and lists all other observed providers as historical. Search fallback
  providers remain a separate metric. The server-rendered fallback has the same
  distinction.
- Missing provider identity or recency fails closed at the Python contract and the
  browser trust boundary. Sub-second timestamps are preserved for ordering.
- The duplicated Search Router projection created during source integration was
  removed; one implementation and one closed SQL allowlist remain.
- Search telemetry accepts a real null fallback provider without treating the
  source as corrupt.
- The browser build has a checked-in npm lockfile, exact Three.js/esbuild versions,
  one deterministic build path, and CI rejects bundle drift.
- The Herdr service has the same kernel/control-group/namespace hardening baseline
  as the other telemetry services. Its bridge still runs only `agent list`; web and
  exporter processes receive no Herdr control socket.
- Rollback now includes a concrete fail-closed Nginx maintenance fragment that
  reserves both dashboard paths and cannot fall through to QuantLab.

## Preserved invariants

- Telemetry is read-only and bounded. Live SQLite sources use read-only mode,
  `query_only`, `trusted_schema=OFF`, a closed authorizer, row/byte/time limits, and
  source identity checks. The HTTP process reads only the sanitized snapshot.
- Prompts, search queries, responses, raw errors, tool arguments, credentials,
  internal reasoning, logs, and diffs are not projected.
- No router, Herdr, dashboard, CI, or deployment change adds an order path or alters
  the QuantLab trading runtime. PAPER-only tests remain a mandatory repository CI
  gate.
- Unknown cost remains `null`; measured zero and unavailable remain distinct.
- Rollback preserves the `/agent-platform` route reservation and never proxies it
  to the QuantLab root service.

## Automated evidence

- Browser/dashboard/geometry tests: 67 passing locally.
- Cross-platform Python fixture/security tests: 52 passing locally.
- Dashboard production tests, observability contract, deterministic bundle check,
  deployment input validation, dependency audit, and shell syntax are mandatory in
  the `agent-platform` CI job on Linux.
- Existing repository CI still runs formatting, lint, typing, PAPER-only runtime
  contracts, unit/integration suites, container smoke, and security scans.

## Mandatory live gates

Production sign-off additionally requires read-only inspection of the installed
Model Router, Search Router, Herdr bridge, systemd sandboxes, Nginx route, telemetry
database immutability, current provider output, and PAPER-only runtime state. The
candidate must be deployed from a clean reviewed commit with a recorded rollback
directory and then pass authenticated/unauthenticated smoke tests. No live gate may
be inferred from historical telemetry or this source audit.
