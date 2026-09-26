# Phase 7: offline read-only dashboard foundation

A separate `agent_platform_dashboard` package: standard-library DTO/fixture decoder,
read-only WSGI application, static CSS and deterministic demo snapshots. No runtime
imports. Existing Hermes React/Vite stack was inspected: dependencies are absent
in this worktree, and reusing its backend would expose unrelated control surfaces.
No installation is allowed. This foundation therefore uses server-rendered static
HTML, not a second Hermes chat UI. No JS/CDN/fonts/third-party requests.

Inputs are explicit bounded JSON **bytes**, never paths or live DB connections.
The fixture adapter validates exact keys/types and rejects unknown/sensitive fields
and duplicate JSON keys. Rows are typed Agent/Task/Router/Repo/Report DTOs with a
full immutable installation+board+source_epoch+profile Scope. No title, prompt,
args, output, memory, credentials, token, error text, diff, URL or freeform label.
Provider/model/status labels use closed fixture vocabularies. Unknown tokens/cost
stay null/unknown (not zero). Git/test/router metadata confers no authority.

There is deliberately NO filesystem/SQLite/Herdr source adapter in this milestone.
Thus no SQL or path from HTTP, no source sidecar writes and no socket permissions.
Future DB ingestion requires explicit mode=ro + query_only + fixed SELECTs and
sidecar verification, as exercised in Phase6 tests; live DB readers remain deferred.
The source cache is one immutable bounded snapshot (max 200 rows, 64KiB input);
there is no polling/refresh thread, mutable cache or implicit I/O on requests.
Snapshot timestamp/provenance are mandatory. Age >30s is stale; future clock values
are unknown, not fresh. Fixture refresh means explicitly constructing a new app.

Access: explicit immutable fixture principal→exact Scope grants, no profile-env or
board-slug inference. All routes, including assets and health, require an explicit
fixture HTTP Basic credential registration; none is minted from requests. Credentials
are not snapshot fields, logs, query params or output. Constant-time comparison;
expired grant denies. This is a localhost fixture auth harness, not production SSO.
No anonymous fallback. HTML/API always select only granted scopes. Unknown path,
query/path traversal and non-GET/HEAD methods reject; no command or upload endpoint.
Host must match the injected localhost authority; forwarded headers are ignored.
No cookies/localStorage. Responses use no-store, nosniff, frame denial and restrictive
CSP. HTML uses escaping. Request/error text is never logged or returned.

Default-off app; explicit `make_demo_server` may construct a loopback-only ephemeral
port-0 server, never starts a loop itself. No 3010 binding or persistent daemon is
performed by tests or implementation. WSGI tests exercise requests in memory.
An HTML smoke artifact from synthetic fixtures demonstrates the frontend without
network. No browser screenshot required for this static rendering boundary.

Read PHASE6_DASHBOARD_CODEMAP_READY and PHASE6_PRIVACY_READY. Independently verified
mutating Kanban/router open helpers and shared Kanban root. Adopted separate web
process, snapshot allowlists, explicit ACL, unknown cost, bounded stale evidence.
Rejected ACL inferred from HERMES_HOME/assignee, exposing native task_events.payload,
assuming QuantLab is Hermes, and direct Herdr control socket access. Nginx config
only proves a configured 127.0.0.1:3000 upstream; app auth/ownership not verified.

Deployment proposal only: separate service and 127.0.0.1:3010 under /agent-platform/.
BLOCKED for production auth/path/domain approval and verifying isolation from the
QuantLab browser origin. No Nginx/systemd/deploy artifacts are activated or modified.
No live source, router/profile/service change, paid API, install, push or deployment.

Gates: test-first missing-module run; strict DTO/JSON types, unknown/sensitive fields,
duplicate keys, bounds, stale/future timestamps, A→B→A grants and expiry, copy_context,
concurrency, malformed auth, XSS, traversal/query/method rejection, secure headers,
no network/subprocess/source I/O; HTML smoke; Ruff/profile/static checks; wider
canonical regression without retry; independent final code and privacy reviews.
