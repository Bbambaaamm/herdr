# Installer step 2/6 evidence — 26 November 2026

Owner: #262, child of #53. Base: `5fb42a5d8890822005419631d011ff43752a001a`.
Branch: `fix/262-degraded-cutover-rollback`. Final HEAD, CI and independent review
are recorded on the draft PR. This document does not grant deployment permission.

## Dedup and takeover

The complete owner-authorized Codex exception was read from the referenced chat.
Open PRs and cutover/RC6/rollback issues were checked. #11/#15 are historical;
#60 owns exact RC8 recovery; #121/#128 marker ACL, #126 headroom, #225 isolation
and #248 grants are separate scopes. No matching active installer implementation
was found. #262 was created and linked from #53. Unrelated changes were preserved.
Both isolated Windows worktree and Linux source clone started at the base above.
No Hermes task, lock, checkpoint, provider, model or configuration was changed.

## Observed incident and reproduced causes

Read-only staging samples confirmed RC6 symlink
`/opt/herdr/releases/v0.3.0-router-v5-p1d-rc6-8d8ad5037555`, active watchdog and
telemetry timers, failed web. The remote shell has HERDR_ENV unset; none was
manufactured. The marker is unreadable to agentops; no privilege/ACL change was
attempted. The bridge journal repeatedly reports `herdr_status_unavailable`.
Stored bridge JSON was 233751 seconds old while snapshot was 11 seconds old;
both Herdr sources were unavailable/source_failed, routers and release available.

Exporter intentionally catches source failures and successfully publishes an
unready snapshot. Wants/After does not propagate bridge failure. Web load requires
fresh available Herdr/router/release rows. Old switch_runtime started web without
checking these bytes. Normal preflight also rejected failed web outright;
normal apply and failure rollback demanded a healthy previous boot. The old
marker was restored only AFTER old-release export during the rollback exercise.
These controller defects are reproduced independently of the original raw input.

An isolated invocation of the actual RC6 bridge source from
`8d8ad50375557b7ac77348e6475cb455682f4a9a`, with a missing-name agent entry,
returned 78; current main returned 0 and published only the configured agent.
RC6 accepts a missing name in its type guard then indexes agent['name']; #238
already fixes it on main. This is a reproduced trigger, not proof that the same
raw envelope caused the live failure. No live agent-list call was made without
the authorized runtime context.

## Relation to PR #60 and safety

#60 merged as `31916cb3e56606e3933395a8b0ed55655365c0b1`, reviewed head
`c3d827690d08b57fef5ba23ab0db7220aadc756d`. It introduced exact RC8-to-RC12
authorization, verified quiescence, authority snapshots, failed archive retention
and shared root-only locking. Later #61/#62 add auth-first recovery health and
stable watchdog takeover; #167 bounds archives; #213 binds immutable preflight.
These gates remain. No RC6/archive identity is added to the RC8 allowlist.

The existing normal controller now checks generated data before web, restores the
old marker before old export, distinguishes healthy/degraded rollback, and gates
all service reactivation on exact authority restoration. The existing state
directory holds a root-only fsynced baseline journal. SIGTERM rolls back; SIGKILL
retains the journal and blocks both normal and RC8 recovery preflight. No second
scheduler, grant authority or automatic journal replay is introduced.

## Actual offline verification

Tests are unprivileged Linux tests. Privileged service operations, archive trust
and host identity are explicitly substituted in installer fixtures; no real
systemctl/nginx/provider operation is reachable. Real files, symlinks, closed
schema validation, socket listeners, process signals and cross-process locks are
exercised. Existing release/security suites cover trust boundaries separately.
This is offline evidence, not live deployment acceptance.

Before controller edits: same degraded-upgrade/invalid-dependency expectations
produced **7 failed, 10 deselected, exit 1**, with no setup errors in that retained
red run. Final new installer suite: **34 passed, exit 0**. Relevant release,
dashboard, agent-stack and security suite: **1378 passed, 1 skipped, exit 0**.
Repository contract and three skill-package lints passed on Linux. Windows lacks
fcntl; its lint import failed, so Linux results are authoritative here.

| ID | Verified scenario | Result |
|---|---|---|
| T01 | healthy preflight/upgrade and healthy previous boot exercise | PASS |
| T02 | failed/inactive coherent baseline; skip broken previous boot | PASS |
| T03 | missing bridge or socket listener; no web start | PASS |
| T04 | invalid/stale bridge or failed producer result; no web start | PASS |
| T05 | missing snapshot; no web start | PASS |
| T06 | invalid snapshot schema; no web start | PASS |
| T07 | web failure after candidate activation | PASS |
| T08 | previous authority restored, healthy web restarted | PASS |
| T09 | exact marker/bridge/snapshot restored, web inactive, degraded outcome | PASS |
| T10 | failed restoration retains journal, maintenance, quiesced dispatch | PASS |
| T11 | real SIGTERM rollback; real SIGKILL durable journal; retry gate | PASS |
| T12 | repeated apply checks full deployed coherence | PASS |
| T13 | actual second process cannot acquire deployment lock | PASS |
| T14 | unsafe telemetry permissions; existing archive/manifest tamper tests | PASS |
| T15 | snapshot release mismatch and actual baseline marker mismatch | PASS |

Reproduce with Python 3.12 and the pinned CI dependencies:

```sh
python -m pytest -q tests/herdr/test_cutover_transaction.py
python -m pytest -q tests/herdr/test_cutover_transaction.py tests/herdr/test_release.py \
  tests/herdr/test_release_limits.py tests/herdr/test_release_dashboard_payload.py \
  tests/herdr/test_security.py tests/agent_platform_dashboard/test_production.py tests/agent_stack
python scripts/validate_repo.py
python scripts/lint-skills.py --all skills
python scripts/refresh_source_manifest.py
git diff --exit-code -- provenance/CANONICAL_SOURCE_MANIFEST.sha256
```

## Limits and approval gate

Read CI and independent reviewer evidence at final exact HEAD. An earlier full
suite started on intermediate source is not acceptance evidence. Self-review is
not independent approval. Failed web is normalized to inactive on degraded
rollback; original failure is not deliberately recreated. Timers may subsequently
refresh restored telemetry. Healthy rollback verifies exact restoration then regenerates previous-release
telemetry before freshness checks. Failed regeneration still fails closed. SIGKILL/power loss requires operator reconciliation under
existing deployment/privilege gates; never delete the journal merely to pass.

Staging was only read: no merge, release/tag, deployment, symlink/marker write,
operational service start/stop/restart, host-policy or Hermes change. Stop before
merge/deployment; step 3/6 is not authorized. Existing host grants and external
runtime availability remain separate deployment prerequisites.


## Independent review remediation

Independent GitHub Codex review of 20e8689 reported two P1 and two P2 findings.
All four are addressed with behavioral regressions: snapshot stability ignores
atime while retaining identity/ownership/size/mtime/ctime checks; readiness uses
the immutable target package in an isolated namespace and its own web decoder;
a pinned actual RC12 contract fixture exercises its three-key snapshot; healthy
rollback regenerates telemetry after exact restoration; legacy bootstrap does
not require a versioned release marker. Target imports reject existing bytecode,
verify immutable source ownership, and do not write bytecode or change sys.path.

The first exact-head CI run 45840440470 had 1 failed, 6622 passed, 115 skipped,
exit 1: the review's atime bug reproduced on the hosted runner. This is repaired;
new exact-head CI and re-review must be checked. The earlier intermediate
server-wide run had 7 failures: three superseded release mocks/source checks and
four unrelated physical SDK/profile environment failures. It is not a final
acceptance result and no Hermes environment/configuration was changed to mask it.

Second independent review of 6b1ecab found a P1 native-extension import precedence
issue on the pre-manifest legacy path and P2 asynchronous Nginx reload handling.
The complete target package closure is now checked before import: no symlinks,
nonregular entries, foreign/writable artifacts, native extensions or bytecode.
Healthy rollback uses the existing bounded public-401 convergence wait. Three
malicious-artifact regressions and a real 503-to-401 probe sequence were added.
The revised focused integration suite passed 1378 tests, 1 skipped, exit 0.
