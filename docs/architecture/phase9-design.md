# Phase9 production readiness (inactive until quantadmin activation)

Q1/Q2/Q3 approved by user. This authorizes code and an admin runbook, not agentops
activation. Baseline 9cf68b0f; sole writer. Phase8 templates remain historical
refusal artifacts. New production templates are separate and explicitly selected.

Trust boundaries: a one-shot exporter reads an explicit root-owned source registry;
a separately invoked Herdr bridge issues only `agent list` and publishes a closed
status envelope. The web process cannot access the control socket, source DBs or
Git repositories; HTTP requests read only a bounded atomic snapshot. The exporter
has no provider/model imports or network API. No dynamic SQL, commands or paths
from HTTP. No fixture fallback.

Nginx requires Basic Auth for the entire exact/prefix path. The backend independently
verifies the same Basic password against a PBKDF2 verifier, so spoofed identity
headers or local loopback access cannot bypass auth. The only principal is michal,
with explicit profile grants. Password generation occurs ONLY in a future admin
TTY invocation; no credential is generated during development. Nginx sees a salted
crypt hash, backend a separate salted PBKDF2 verifier. No plaintext persisted.

Sources are explicit per majak/quantlab. Router schema independently verified via
mode=ro/query_only: requests contains task_id, id, started_at, ended_at,
input_tokens, output_tokens and cost_usd, plus sensitive columns which are never
selected. Fixed bounded recent-window aggregation uses only the former columns.
SQLite authorization restricts reads to approved columns, no writer helpers,
mutable DBs never use immutable=1. Live read-only WAL availability is an activation
check, not permission to create sidecars or change DB permissions.

Kanban source code defines tasks(id,status,current_run_id,created_at,...), but no
live DB was found in the inspected default/profile board roots. Until a real path,
board identity, schema and grant are verified, Kanban is unavailable (not empty).
No board-path guesses or fixture substitution. Git is an explicit repository
allowlist with fixed status/rev-parse commands and safe environment. Test reports
are bounded structured metadata inputs, not arbitrary Markdown parsing.

Snapshot: exact JSON keys, bounded rows/bytes, no unknown fields. Every source has
profile, kind, observation timestamp, optional data timestamp, availability/reason
and rows; task identifiers are deterministic profile-scoped SHA-256 pseudonyms
for cross-source audit correlation. No raw prompt, args, output, memory, errors,
credentials, diff or remote URI. Unknown cost stays null. Unavailable != zero;
stale/future snapshot evidence is explicitly unavailable, never silently refreshed.

Threats: unauthenticated HTTP/local header spoofing; wrong-profile joins; poisoned
JSON/source paths/symlinks; unbounded subprocess output/SQL; stale replay; concurrent
export; partial publication; credential leakage; shared-vhost collision/rollback.
Controls: double auth, exact profile ACL, no-follow regular-file readers, closed
DTOs, monotonic deadlines and bounded output, source query_only/authorizer, atomic
rename+directory fsync, nonblocking flock, unprivileged separated services, no
secret logging, operator-confirmed exact include change and deny-route rollback.
Root and approved source owners remain trusted. Runtime host sandbox enforcement,
TLS/vhost inheritance, real path grants and effective routing need admin validation.
