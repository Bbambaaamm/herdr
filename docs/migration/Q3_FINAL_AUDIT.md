# Q3 final audit: routers, Herdr, and dashboard

Status: **production verified on `quantlab-staging-01`**.

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
- Dashboard production tests, observability contract, deterministic bundle check,
  deployment input validation, dependency audit, and shell syntax are mandatory in
  the `agent-platform` CI job on Linux.
- Existing repository CI still runs formatting, lint, typing, PAPER-only runtime
  contracts, unit/integration suites, container smoke, and security scans.
- GitHub Actions CI run `36277649016` passed all ten required jobs for deployed
  commit `41179635c8654a60c5d9234acccb6e91b2028b72`, including `agent-platform`,
  `production-smoke`, `security`, `container-build`, and `agent-pipeline`.
- The pinned npm production dependency audit reported zero vulnerabilities.

## Live production evidence

The read-only audit and guarded rollout completed at `2026-09-26T23:44:57Z`:

- `/opt/agent-platform/release/DEPLOYED_GIT_SHA` is
  `41179635c8654a60c5d9234acccb6e91b2028b72`.
- The root-owned deployed manifest has SHA-256
  `a9f7b9cb7a5f33f4f839282e3cdbad5f2bb2a8c095bae84819cfd88c2a289046`;
  every listed file, including the Herdr binary, passed exact checksum validation.
- Herdr stayed on the audited binary SHA-256
  `2a02fed16beb651ef006e1d43f048f652ca4dc58ad053cd2d44450563d5c54b7`.
- The web service and both exporter/Herdr timers are active and enabled. The live
  Herdr unit reports `yes` for kernel tunable/module/control-group protection,
  namespace and SUID/SGID restrictions, and personality locking.
- The exporter retains `BindReadOnlyPaths` for both Model Router and Search Router
  profile directories. The web process still cannot access source databases, the
  Herdr socket, or raw bridge state. Exact Linux CI tests also prove source SQLite
  identity is unchanged across bounded reads.
- The fresh sanitized snapshot reported Model Router, Search Router, and Herdr
  available for both profiles. No task IDs, prompts, queries, logs, credentials, or
  raw errors were captured as rollout evidence.
- Live provider roles were derived by `last_used_at`, not row order or historical
  counts: Model Router current provider was `nous` for both profiles, with
  `openai-codex` historical. Search Router current provider was `parallel-keyless`
  for `majak` and `firecrawl-keyless` for `quantlab`; all other observed providers
  remained historical and fallback providers stayed a separate metric.
- Direct and public unauthenticated Agent Platform health returned `401`; the public
  QuantLab root response remained byte-path independent and kept the same HTTP
  status before maintenance, during validation, and after activation.
- Rollout touched only the Agent Platform release, its five systemd unit files, and
  its reserved Nginx fragment. QuantLab code, data, services, and execution settings
  were not changed; required PAPER-only CI stayed green.

## Rollback evidence

- Activation first installed the fail-closed maintenance fragment, validated Nginx,
  and confirmed the Agent Platform path returned `503` without falling through to
  QuantLab. The live authenticated route fragment was restored only after service,
  snapshot, sandbox, and manifest checks passed.
- Two earlier readiness-gate failures exercised the automatic rollback path and
  restored the old `8f2a5543515eb2d8ce84602e98d6c3d2163e1099` release, original unit hashes,
  healthy timers/web service, `401` Agent Platform boundary, and unchanged QuantLab
  root status before the successful attempt.
- The successful rollout retained the previous release in root-only mode `0700` at
  `/opt/agent-platform/rollback-20260926T234439Z-8f2a5543515eb2d8ce84602e98d6c3d2163e1099`.
  No database, credential, router state, or shared Nginx vhost was deleted or replaced.
