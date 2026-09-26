# Phase 7 dashboard foundation report

PHASE7_DASHBOARD_FOUNDATION_DONE. Final regression and independent reviews passed; no unresolved in-scope P0/P1. Baseline after separate Phase6 commit:
`d1fca3347d698f75d32fb1fdd9772134b2041d56`; clean worktree verified between milestones.

## Delivered

Standalone `agent_platform_dashboard` standard-library package, fixed metadata DTOs,
bounded fixture JSON-byte reader, explicit principal/scope grants, default-off
read-only WSGI app, escaped static HTML/CSS frontend and deterministic synthetic
demo. No Hermes runtime, Kanban/router helper, controller, model/provider client,
Herdr socket, subprocess, source path or live DB dependency. No new dependency.

Five source contracts: Herdr agent state, Kanban task/run metadata, router provider/
model/token counts/nullable cost/reason, Git commit/dirty, test/report counts/status/
artifact digest. Every row binds installation, immutable board ID, source epoch,
profile and allowlisted board label. Model/provider labels are a closed fixture
vocabulary, not automatic live discovery. Free-only router/fallback settings unchanged.

All inputs are explicit bytes (64KiB maximum), exact keys/types and max 200 unique
rows. Unknown fields, duplicate JSON keys, malformed numbers and sensitive payload
fields fail closed with fixed error codes. There is no source-file loader: paths,
URLs and symlinks cannot be supplied or followed through HTTP. No SQLite reader is
shipped here. Future SQLite access remains deferred and must use mode=ro plus
query_only, fixed SELECTs, limits and sidecar checks; Phase6 tested that boundary.

The cache is one immutable injected snapshot; no daemon/refresh thread. Age over
30 seconds is stale; future timestamps are unknown. Explicit new app construction
refreshes fixtures. No retry/fallback interpretation or mutation from diagnostics.

## HTTP and UI safety

Fixed routes under /agent-platform/: page, style.css, api/v1/overview and health.
Only GET/HEAD. All routes require registered fixture Basic authentication; grants
are checked for expiry and exact scope. No anonymous fallback, ambient profile,
query source selector, path lookup, uploads or control endpoints. Host must equal
the injected loopback authority; forwarded headers do not grant trust. Authentication
uses constant-time credential comparison and never appears in snapshots/output/logs.

CSP default-src none, style-src self, frame-ancestors none; no-store, nosniff,
X-Frame-Options DENY and no-referrer. No JS, CDN, remote font, cookies or localStorage.
Static frontend shows only scope-filtered data and renders unknown costs as unknown.
Optional make_demo_server is default-off, constructs ONLY 127.0.0.1:port-0 and never
starts its loop. It was tested with a fake factory; no listener was started.

Existing Hermes React/Vite sources were inspected. Dependencies are absent in this
worktree and the existing backend includes unrelated control APIs. Separate stdlib
foundation avoids installing or coupling to those surfaces.

## Verification

Test-first red: both new files failed collection with expected ModuleNotFoundError,
exit 1, zero collected tests. Initial implementation 45 PASS. Security/limit and
server-factory coverage brought targeted total to **52 PASS / 0 FAIL** (27 contracts,
25 app), two files, 0.9s. Canonical runner with existing isolated devdeps overlay,
PYTHONDONTWRITEBYTECODE=1, -j 2 --file-retries 0. No retry/install.

Broader canonical regression: **692 PASS / 0 FAIL, 29 files, 40.3 seconds**.
Exact manifest = both new dashboard test files plus the 27-file Phase6 manifest
(Phase5 25-file manifest plus both Phase6 adapter test files). Same runner flags.

Ruff package and tests PASS; profile-scope zero findings; diff-check PASS. Static
AST guard permits only stdlib and local DTO/frontend modules, rejects open/connect/
socket/subprocess/exec/eval/decide/validate_snapshot/serve_forever and live-path
literals. Optional wsgiref server factory is explicit, loopback-only, default-off.
Dynamic guard forbids open/socket/Popen during HTML/API requests. No DB source means
no SQL injection or WAL/SHM sidecars; no path source means no symlink/traversal load.

HTML smoke generated from synthetic fixtures at external `phase7-smoke/index.html`
with `style.css`, both under /home/agentops/workspaces/majak. Parsed successfully;
five tables, unknown cost and no scripts. No browser screenshot or network smoke
was claimed. WSGI routes/auth/headers/body exercised directly in memory.

Tests cover strict records/closed labels, sensitive and unknown fields, malformed/
duplicate JSON, hard row/byte bounds, stale/future clock, expired grants, hostile
Host, unsupported methods, query/path traversal, HTML escaping, missing/malformed
credentials, asset/health protection, A→B→A/copy_context concurrency, empty scope,
no env fallback, no I/O and sanitized Exception/preserved BaseException.

## Audit grounding and limits

Read PHASE6_DASHBOARD_CODEMAP_READY and PHASE6_PRIVACY_READY; verified mutating
Kanban/router connect helpers and shared Kanban root locally. Adopted explicit ACL,
read-only snapshots, no control socket and no auth inferred from profile paths.
Did not adopt raw task titles, arbitrary event payloads, inferred HERMES_HOME grants,
or claims that the QuantLab upstream is Hermes/unauthenticated. Read-only Nginx
config supports only a configured 127.0.0.1:3000 upstream; app identity/auth not proven.

**Deployment BLOCKED only**: production auth/path/domain approval, same-origin
isolation versus QuantLab, live exporter/provenance, process isolation/rate limits,
refresh/revocation policy. localhost:3010 and /agent-platform/ are proposals only.
No Nginx/systemd config, live port, service, profile, DB or router was changed.
No paid API, push, deploy or installation. Fixture credentials are not production
SSO; Python immutable DTOs are not a sandbox against hostile same-process code.
Pseudonym syntax cannot certify an upstream value is free of sensitive information.

## Exact Phase7 staging manifest

PHASE7_DASHBOARD_DESIGN.md
PHASE7_DASHBOARD_REPORT.md
agent_platform_dashboard/__init__.py
agent_platform_dashboard/README.md
agent_platform_dashboard/contracts.py
agent_platform_dashboard/fixtures.py
agent_platform_dashboard/frontend.py
agent_platform_dashboard/app.py
agent_platform_dashboard/demo.py
tests/agent_platform_dashboard/test_contracts.py
tests/agent_platform_dashboard/test_app.py

External HTML smoke/report copies are not staged. Commit hash goes in external
report after the separate local commit.

## Independent review record

quantlab-codex PHASE7_CODE_REVIEW_READY: 0 P0 / 0 P1, full files/design/tests read;
counts are coordinator-run evidence, not independently rerun by reviewer.
First majak-hermes PHASE7_PRIVACY_FINAL_READY was NOT accepted as sufficient gate:
its prose cited nonexistent CACHE_TTL/_cache/_html/BoardGrantScope/script.sh and
confused parametrized cases with function counts. A single corrected full-file
review was completed as PHASE7_PRIVACY_CORRECTED_READY: prior false references
explicitly retracted, 0 P0 / 0 P1 in scope. Independently verified the substantive
corrected claims against project(), DTO validators, byte decoder, Basic auth,
route/Host checks and frontend escaping. Minor prose/test-count inaccuracies were
not used as evidence: actual runner counts are 27+25 cases, cross-profile test
returns five versus one row, CSS is served as an asset rather than inline HTML,
and all route paths retain the /agent-platform/ prefix. No implementation defect
or code change resulted from either final review.

Read-only live reference checks still match prior baseline:
router __init__.py SHA256 62e6a5b0ed2e25c45d5b17dc6a7df852384d62dd361cded51ea6219a1eedf9f1;
conversation_loop.py e5ebc04d14026ba493e5b238e615ddc775807344a04eab40c907750522052b91;
turn_finalizer.py 77ca6c9e92cb7e887fd1d0d950da417e5540a865a6866af9ad0c23b784e7f6bf.
These are sampled code references, not hashes of all production state.

Final staging requires exactly the eleven listed Phase7 files.

PHASE7_DASHBOARD_FOUNDATION_DONE
