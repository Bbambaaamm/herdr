# Phase8 inactive staging deployment bundle report

Both independent final reviews complete: P0 0 / P1 0. Baseline `1340fb47d54d47a05020666d12a6259f85599039`,
branch codex/agent-platform-phase1, initially clean. Sole writer in isolated worktree.

## Scope and decisions

Approved topology only: QuantLab remains 127.0.0.1:3000 and location /;
agent-platform has a separate unprivileged process at 127.0.0.1:3010 and
location ^~ /agent-platform/. This bundle DOES NOT start that process or route traffic.

**Q2 BLOCKED pending user approval**: production Basic Auth with a new server-
generated password not stored in Git. No password/htpasswd/auth implementation
was generated, selected, read or activated.
**Q3 BLOCKED pending user approval**: Herdr status exporter, Kanban SQLite mode=ro/
query_only, profile router DB mode=ro/query_only, Git allowlist and test reports.
No collector/source was connected. Fixture demo is explicitly not production data.

Delivered inactive systemd and Nginx templates, bounded refusal preflight, null
metadata example, explicit collision inventory helper and detailed collision/
rollback runbook. No changes to Phase7 runtime, live files, profiles, router, DB,
systemd state, Nginx state or services; no sudo/systemctl/push/deploy/install.

## Fail-closed controls

Service executes a standalone stdlib refusal guard with Python -I -B. It ALWAYS
exits 78: missing declarations have explicit reasons, populated declarations still
report Q2/Q3 approval required and production adapters unimplemented. No startup
success branch, server factory, fixture import, model/provider/DB helper or Herdr
control socket. Auth/source references are fixed metadata paths and never opened.
Metadata reader: explicit absolute path, no-follow every component, regular file,
no group/other write permission, <=8KiB; no raw paths/content/exception details in
output. Unknown keys/enable flags/secrets/fixtures and duplicate JSON keys deny.

Unit has DynamicUser/User agent-platform, no capabilities, NoNewPrivileges,
ProtectSystem=strict, ProtectHome=yes, no AF_UNIX, loopback IP and port-3010 bind
restrictions, no restart, no [Install]. Runtime enforcement/cgroup support and
future principal/config provisioning are not proven by static/native syntax checks.

Nginx server fragment never overrides root/listen/server_name/TLS. Exact no-slash
and ^~ slash-prefix both return 503; a private named error target prevents inherited
503 handling from forwarding elsewhere. The unreachable future upstream declaration
preserves the prefix, disables failover/cache/temp proxy files and strips request
headers/body. Removing refusal barriers needs a NEW approved implementation, not
just filling placeholders. No Basic Auth default is silently activated.

Collision helper checks a bounded, explicitly supplied effective-vhost inventory;
it does not read live config or attest inventory completeness. It rejects existing
reserved/nested/named locations, regex needing review, changed QuantLab root,
occupied 3010 and unit-name collisions. Empty diagnostic output is not permission.

Rollback runbook retains a 503 route tombstone, never falls back to QuantLab/3000,
never restores the entire shared vhost over unrelated changes and never deletes DB
state. Pre-activation failure affects scratch artifacts only. All operational steps
are documentation for a future separately approved deployment, not executed here.

## Verification

Test-first red: expected missing-preflight ImportError, exit 1, zero collected tests.
First targeted implementation: 26 PASS. Added named-location collision inventory,
FIFO/writable-file and scope checks: **33 PASS / 0 FAIL**, 1.0s. Linux-only marker
matches this systemd/Linux deployment bundle; tests read configuration templates,
not Python source text.

Broader canonical regression: **725 PASS / 0 FAIL, 30 files, 40.0s**, including all
33 Phase8 cases plus the 29-file Phase7 manifest (692 cases). Existing isolated
devdeps overlay, PYTHONDONTWRITEBYTECODE=1, scripts/run_tests.sh, -j 2,
--file-retries 0. No file retry, installation or model call.

Ruff preflight and test file PASS. Profile-scope zero findings. git diff --check
PASS. Static import/call gate: stdlib JSON/os/pathlib/stat/sys only; no runtime,
socket/connect/subprocess/exec/eval/serve/fixture/control imports/calls. Dynamic
preflight test forbids socket/Popen and verifies auth/source references are not
opened, even when explicitly declared. Only bounded metadata-file I/O is allowed.

Native checks against scratch copies only:

- systemd-analyze 259 verify --man=no: exit 0. Two warnings came from unrelated
  installed XFS CPUAccounting declarations, not this unit. No service start or
  daemon control; syntax does not certify actual sandbox enforcement.
- Nginx 1.28.3 -t: synthetic scratch HTTP server with a temporary Unix socket,
  isolated paths/log/temp/PID configuration; no live certificates/config/PID,
  no 3000/3010 TCP listener, no request-serving worker.
- Valid fragment: exit 0; duplicate prefix and exact location: expected exit 1.
  Duplicate named location: Nginx ACCEPTED it (exit 0); explicit inventory helper
  rejected it. This is why native syntax alone is not a sufficient collision gate.
- Nginx -t may create an EMPTY scratch PID file; verified empty. It is not a daemon
  PID. All temporary native artifacts were removed with their temp directories.

Native harness corrections recorded honestly: initial sandbox checks failed on
socket permissions; authorized scratch checks succeeded outside the sandbox. An
attempt to use listen port 0 was rejected by Nginx; changed the validation harness
to a scratch Unix socket. Initial assumptions that duplicate named locations fail
syntax and -t creates no PID file were disproven; corrected helper/docs/harness.
These were validation findings, not hidden pass-on-retry test results.

## Evidence and limitations

Verified the existing Nginx disk config's root/3000 declaration read-only; it is not
proof of effective running config. No live collision scan, TLS/auth validation,
source access or rollback was executed. Collision and rollback steps are explicit
future gates. Read native syntax as bundle validation ONLY, never staging activation.

Official references used for location/prefix behavior:
[Nginx location](https://nginx.org/en/docs/http/ngx_http_core_module.html#location),
[Nginx proxy_pass](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass).
Local systemd.exec(5)/resource-control(5) and installed native verifier informed the
hardening template. Production credential delivery and live source formats stay
undefined until Q2/Q3 approval and a separate implementation/review.

## Exact commit manifest

PHASE8_DEPLOYMENT_BUNDLE_REPORT.md
deploy/agent_platform/README.md
deploy/agent_platform/agent-platform-staging.service.in
deploy/agent_platform/agent-platform.nginx.conf.in
deploy/agent_platform/preflight.py
deploy/agent_platform/staging.example.json
tests/deploy/test_agent_platform_bundle.py

External report copy and scratch artifacts are not staged. Commit hash is appended
to the external report after the local commit. No activation is part of this gate.

## Independent review and production sample integrity

Quantlab-codex PHASE8_CODE_REVIEW_READY: P0 0 / P1 0 for the inactive scope.
Coordinator re-read the actual preflight, templates, tests and collision/rollback
runbook and confirmed the cited refusal/reference/collision behavior. Reviewer
read the files but did not independently execute the reported tests.

Read-only SHA-256 checks match the prior recorded baseline for these three files
(they are a sample, not a claim to hash every live file):

- Live model-router __init__.py: 62e6a5b0ed2e25c45d5b17dc6a7df852384d62dd361cded51ea6219a1eedf9f1
- Live agent/conversation_loop.py: e5ebc04d14026ba493e5b238e615ddc775807344a04eab40c907750522052b91
- Live agent/turn_finalizer.py: 77ca6c9e92cb7e887fd1d0d950da417e5540a865a6866af9ad0c23b784e7f6bf

Majak-hermes PHASE8_PRIVACY_REVIEW_READY: P0 0 / P1 0 in the same inactive scope.
Coordinator confirmed the cited bounded metadata reader, fixed refusal reasons,
no opened auth/source references, null example, denied Nginx locations and
rollback tombstone. Both reviewers explicitly distinguish reported test evidence
from their own read-only review. No additional P0/P1 repairs were required.
The privacy review was delayed by its provider rate limit/context compaction;
no duplicate prompt was sent. Native validation findings and corrections are
recorded above, independently of the clean final review verdicts.

## Final outcome

PHASE8_BUNDLE_READY

Only the inactive bundle is ready for a local commit. Q2 and Q3 remain **BLOCKED
pending user approval**, as do production implementation and deployment. No
credential generation, source connection, service start, push or deployment.
Exact seven-file staging manifest above; final cached diff check required before
commit. The external report receives the resulting commit hash and clean status.
