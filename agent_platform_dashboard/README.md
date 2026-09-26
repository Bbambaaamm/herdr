# Offline agent-platform dashboard

Standalone stdlib foundation, not the Hermes runtime dashboard. No live sources,
SQL, filesystem source lookup, command execution or Herdr socket. Python imports
are inert. The only source adapter is `fixtures.decode_snapshot(bytes)` (64KiB,
200 records maximum). Strict DTOs reject unknown fields; unknown cost stays null.

Use `contracts.project(snapshot, grant, now=...)` for a scoped metadata envelope,
`frontend.render(envelope)` for static HTML, or explicitly construct `DashboardApp`
with fixture `Login` registrations and a trusted clock. App default is disabled.
No authentication credential is part of the snapshot or output. All HTTP paths,
including CSS/health, require the configured fixture Basic credentials and grant.

`app.make_demo_server(application, enabled=True)` optionally constructs a stdlib
WSGI server bound ONLY to 127.0.0.1 on an OS-selected ephemeral port (0). It does
not start serving; the caller owns `serve_forever` / `server_close`. It is not
called by tests except through a fake factory. No default persistent port or CLI
startup. Do not use the fixture harness for real credentials/data or production.
Browser Basic Auth is only a local demo mechanism; production auth remains open.

Fixed routes: `/agent-platform/`, `style.css`, `api/v1/overview`, `health` under that
prefix. Only GET/HEAD. No request path is used as a filesystem path. There is no
file loader or symlink following; callers explicitly supply bounded bytes. A new
immutable app instance is an explicit fixture refresh. After 30 seconds, evidence
is stale; a future timestamp is unknown. No automatic refresh or network collector.

DTO kinds: agent (Herdr status), task (Kanban metadata), router (closed fixture
model/provider vocabulary, token counts, optional integer micro-USD cost and reason),
repo (commit/dirty), report (test counts/status/artifact digest). Each row carries
installation+immutable board+source epoch+profile, and each viewer has exact scope
grants. Board labels and profile environment variables are not authority. IDs are
pseudonyms, not anonymization. The example `demo.fixture_snapshot()` is synthetic.

The deployment proposal is localhost:3010 and `/agent-platform/`, NOT activated.
Deployment is BLOCKED pending auth/path/domain approval and origin isolation review.
A live exporter, read-only SQLite source (mode=ro plus query_only), bounded refresh,
rate limiting and production process isolation are deferred. No Nginx/systemd files
or services were changed. See PHASE7_DASHBOARD_DESIGN.md and the implementation report.
