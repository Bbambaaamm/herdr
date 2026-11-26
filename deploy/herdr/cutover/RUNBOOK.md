# Versioned Herdr runtime cutover

This procedure supports initial migration from `/opt/agent-platform/release` and
upgrades between immutable versioned Herdr releases. Runtime promotion does not
activate a consumer, add permission, change host-policy, select a model, enable
provider calls or alter QuantLab execution. The external `herdr 0.9.1` binary
remains the dependency pinned by version, size and SHA-256.

## Release gate

Use only an annotated tag with a successful official `Release bundle` workflow.
Download its archive and adjacent `.sha256` artifact and verify them before any
host preparation. Never substitute an archive built from floating main, an
untagged worktree or `v0.1.0-bootstrap`.

The deterministic bundle contains the closed production payload, **five** validated
consumer policy overlays (Heating, Herdr, LOXXESS, Majak and QuantLab),
`RELEASE.json` and `MANIFEST.sha256`. It excludes secrets, credentials, databases,
logs, prompts, raw queries and the external Herdr binary. Consumer activation,
model/provider admission and deployment approval remain separate gates.

## Normal baseline classification

| Baseline | Required behavior |
|---|---|
| Healthy | Web active, direct/public unauthenticated health 401 and existing integrity/service gates pass. Apply exercises a healthy previous-release boot before final promotion. |
| Degraded but eligible | Versioned current release with failed/inactive web; exact release tree, public marker, units and consumer identity coherent; live Herdr socket; active telemetry timers/watchdog; no durable worker; direct health unavailable (connection refused/000, 502 or 503) and public boundary fail-closed (401, 502 or 503). Apply skips the known-broken previous web boot and records that fact. |
| Unsafe/inconsistent | Reject missing or mismatched identity/manifest/marker, drifted units/configuration, wrong owner/mode, unavailable socket, unsafe boundary, active durable worker, or unfinished transaction journal. Web failure alone is not permission to ignore these checks. |

The pre-manifest legacy directory is supported only through the existing pinned
legacy commit/binary/unit gates. It is not a generic degraded baseline and must
not be given invented versioned metadata.

## Controller placement and arguments

Preflight reads root-owned deployed metadata and installed unit bytes. It must
run as root from an immutable, manifest-valid controller. `ROOT.parent` must be
**exactly** `/opt/herdr/releases` or `/var/lib/herdr/incoming`, and ROOT's basename
must be `<tag>-<commit12>` as required by `verify_tree`. Do not add another directory
between an approved prefix and the extracted release root. For a not-yet-installed
normal candidate, prepare this exact layout through the separately authorized
operator path:

- controller: `/var/lib/herdr/incoming/<tag>-<commit12>/`;
- input archive: `/var/lib/herdr/incoming/<private-archive-stage>/REVIEWED.tar.gz`;
- archive stage root-owned mode 0700; all controller ancestors/source artifacts
  root-owned, not group/other writable, without unsafe symlinks/import artifacts.

The controller must be the same release as the normal candidate. Running it from
`/home`, `/tmp` or a mutable worktree is rejected. Preparing these protected paths
requires separate host authorization; the source/release workflow does not do it.

`--expected-legacy-commit` always refers to the value in
`/opt/agent-platform/release/DEPLOYED_GIT_SHA`, even when current points to RC6 or
another versioned release. It is **not** the current versioned release commit.
Versioned current identity is verified separately against its tree, installed
units and trusted public marker. Read and verify the legacy value before use;
do not replace it with the RC6, candidate or main SHA.

## Read-only normal preflight

After archive verification and authorized immutable-controller preparation:

```sh
sudo /usr/bin/python3 -I -B \
  /var/lib/herdr/incoming/<tag>-<commit12>/deploy/herdr/cutover/cutover.py preflight \
  --archive /var/lib/herdr/incoming/<private-archive-stage>/REVIEWED.tar.gz \
  --expected-legacy-commit <verified-legacy-DEPLOYED_GIT_SHA>
```

Placeholders must be replaced with the verified artifact paths and legacy value.
Preflight does not switch releases, change services, policy or configuration. It
verifies the controller and archive, consumer schemas, external binary, pinned
legacy identity, unit/Nginx hashes, current baseline classification, authentication
boundary and content-only legacy/candidate comparison. Temporary extraction is
bounded; no source contents or secrets are emitted. Any integrity/ownership/TOCTOU
failure is a hard stop.

Require `status=preflight_ok`, expected `release.tag`, full `release.commit`,
`current` and `baseline_health`. Derive the apply confirmation **only after this
successful actual preflight** from its `release.tag` plus `-` plus the first twelve
characters of its `release.commit`; the implementation does not emit a separate
confirmation-token field. Do not guess a token from a historical example.

## Authorized normal apply

Only after successful preflight, release verification and explicit deployment
approval, use the same controller, archive and legacy value:

```sh
sudo /usr/bin/python3 -I -B \
  /var/lib/herdr/incoming/<tag>-<commit12>/deploy/herdr/cutover/cutover.py apply \
  --archive /var/lib/herdr/incoming/<private-archive-stage>/REVIEWED.tar.gz \
  --expected-legacy-commit <verified-legacy-DEPLOYED_GIT_SHA> \
  --confirm <confirmation-derived-from-successful-actual-preflight>
```

Apply holds the existing root-only deployment lock, repeats preflight, installs
an immutable candidate, captures exact prior authority and a root-only fsynced
transaction journal, and installs policy overlays only if absent or byte-identical.
It reserves dashboard traffic with maintenance 503 and quiesces timers, their
oneshots and watchdog; an active durable worker blocks promotion.

Before **every candidate web start**, require successful bridge oneshot, live
socket, fresh bridge rows and snapshot, closed target-specific schema, matching
release/bridge data, exact telemetry ownership/mode, and the target web config/auth
checks. The entire historical import closure must be safe; exporter exit zero or
an unauthenticated 401 alone is insufficient. Readiness is checked, not assumed
from a fixed delay.

Healthy baselines exercise the previous web boot: restore previous units and
marker **before** exporting previous-release telemetry, validate it, then promote
the candidate again. Degraded baselines skip that broken web exercise and record
`rollback_exercised=false`, `rollback_mode=skipped_known_degraded_previous`.
They must never claim an exercised healthy rollback. Final public health/current
identity and durable evidence precede stable watchdog takeover. An
`already_deployed` result requires coherent current symlink, all units, installed
consumer digest and public marker, not just an existing release directory.

## Failure, rollback and interruption

On candidate failure, quiesce timers/oneshots, web and watchdog before restoring
exact previous symlink, units, consumer files, marker, bridge and snapshot
bytes/modes/owners. Verify restoration before reactivation. Healthy rollback then
regenerates previous-release telemetry, validates freshness, starts web and waits
for public 401/Nginx convergence. Degraded rollback leaves web inactive instead of
recreating a failed service; it verifies the fail-closed boundary. Timers may
refresh restored telemetry after verification. Dispatch reopens only after
restoration, verification and failed-archive preservation succeed.

Outcomes distinguish successful promotion, `rollback_healthy`, `rollback_degraded`
and `rollback_incomplete`. A failed upgrade still exits 78. Incomplete rollback
retains maintenance/quiescence and the journal for operator intervention; a failed
restore never grants permission to continue service activation. No database,
credential, consumer state, shared vhost or legacy release is deleted.

SIGTERM/interrupt takes the same rollback path. SIGKILL or power loss cannot run
cleanup: `/var/lib/herdr/deployments/transaction.json` remains and blocks both
normal and historical RC8 preflight before archive validation. Reconcile its
captured authority against actual host state under the existing privileged
operator/deployment gates. Never remove it merely to make retry pass. No automatic
journal replay, policy expansion, provider activation or retry authority is added.
Successful apply or verified rollback removes the journal durably.

The T01–T15 matrix and offline evidence are in
`docs/evidence/CUTOVER_STEP2_2026-11-26.md`. Offline verification is not a live
staging deployment. QuantLab stays PAPER-only; Heating actuation stays disabled;
all other consumer invariants and separate activation gates remain authoritative.

## Heating repository-only consumer activation

Cutover intentionally does not enable a consumer. After a release containing the
reviewed Heating intake, coordinator and `heating-safe-engineering` contract is
current, activate its host ceiling separately:

```sh
python3 deploy/herdr/cutover/activate_heating.py preflight \
  --release /opt/herdr/releases/<tag>-<sha12>

sudo /usr/bin/python3 -I -B deploy/herdr/cutover/activate_heating.py apply \
  --release /opt/herdr/releases/<tag>-<sha12> \
  --confirm <exact-confirmation-printed-by-preflight>
```

The activation is limited to repository file tools plus protected verification
and result submission. It grants no process, delegation, Home Assistant, SSH,
MQTT, device, boiler, reload, restart or deployment capability. Apply holds the
dispatcher and worker locks, backs up the exact prior root-owned policy, binds the
complete immutable current release inventory, installs a seven-day Heating
ceiling, verifies that the `agentops` runtime can compose it, and restores the
backup on any failure. It also shares the cutover lock, preserves schema-2 private
launch settings, and can renew an existing matching Heating ceiling without
accepting capability drift. A fresh maintainer admission is still required
afterward.

The activation removes mutable `.git/**` metadata from approved runtime
inventories only after verifying every retained runtime byte against the existing
root-owned policy. Apply publishes an exact metadata-free, root-owned runtime
asset below the worker-readable, non-writable `/opt/herdr/runtime-assets` root and
then prepares and cleans up a complete `agentops` launch snapshot before reporting
success, so code or runtime drift remains fail-closed.

## Evidence and soak

The deployed tag, full commit, exact consumer-config digest, archive digest,
previous release, root HTTP status, and rollback exercise are recorded root-only
under `/var/lib/herdr/deployments`. A bounded copy containing only tag, commit,
config digest, and deployment time is exposed to the read-only dashboard snapshot.

After cutover, first verify that `agent-stack-watchdog.service` executes through
`/opt/herdr/current` and that dispatcher resolves `agent-task-worker` from the same
immutable release. Then require a soak with active/enabled Agent Platform services, fresh
Model Router/Search Router/Herdr telemetry for both profiles, no queue/lease or
routing regression, current-versus-historical provider semantics intact, and all
consumer invariants unchanged. QuantLab remains PAPER-only; Heating actuation stays
disabled; Maják provenance rules remain authoritative.


## Historical exact RC8 recovery — never use for RC6

This separate mode is restricted to the exact RC8-to-RC12 identities below.
For RC6 and other eligible versioned baselines, use normal `preflight`/`apply`
with the healthy/degraded classification described above. A failed RC6 web does
not authorize `recovery-preflight` or `recovery-apply`.

A separate `recovery-preflight` / `recovery-apply` path exists only for the
one known staging recovery state where exact RC8
`d58283bc4bf98490bb96bd9bffd58b293b451061` is fail-closed because its router
adapter returns unavailable once the last 1000 requests exceed 50 distinct
task/model/provider groups.

The recovery commands must run from a separately reviewed, manifest-valid
recovery-controller release. That controller is not installed. Its only allowed
target is the exact RC12 archive with all of these identities:

- tag `v0.3.0-rc.12`;
- commit `1d524ff25d8b340cb638224effb0f445fb4e4e98`;
- archive SHA-256
  `0f4fa8a24de0c367008532acb6319487d0da1948f458ee8d036910720ecb7b0f`;
- payload-manifest SHA-256
  `b97aa3900ad642ee55433cdb09b58fb99bb435360427a63eb1f68d9baa76938a`;
- config-contract SHA-256
  `3c7660874e437dd49dcbff83db20761fd595743c15ce3969a457d6f1de199ba9`.

Do not run normal RC12 `apply`, and do not run these commands from the extracted
RC12 tree: RC12 is the pinned target, not the recovery controller. Before any
privileged change, run the read-only recovery preflight from the extracted
controller tree:

```sh
sudo /usr/bin/python3 -I -B deploy/herdr/cutover/cutover.py recovery-preflight \
  --archive /home/quantadmin/herdr-rc12-review/herdr-v0.3.0-rc.12-1d524ff25d8b.tar.gz \
  --expected-legacy-commit 41179635c8654a60c5d9234acccb6e91b2028b72
```

Only an exact `preflight_ok` report with
`recovery_mode=rc8_router_overflow` authorizes the single recovery apply:

```sh
sudo /usr/bin/python3 -I -B deploy/herdr/cutover/cutover.py recovery-apply \
  --archive /home/quantadmin/herdr-rc12-review/herdr-v0.3.0-rc.12-1d524ff25d8b.tar.gz \
  --expected-legacy-commit 41179635c8654a60c5d9234acccb6e91b2028b72 \
  --confirm v0.3.0-rc.12-1d524ff25d8b
```

Recovery authorization is intentionally narrow:

- current must resolve to that exact immutable RC8 release;
- installed RC8 units must already satisfy the reviewed bootstrap hashes;
- the candidate must match every pinned RC12 identity and the exact archive
  bytes listed above;
- the Herdr Unix socket must accept a live connection, not merely leave a socket
  inode behind;
- both Herdr profile sources and the RC8 release source must be fresh/available;
- both router sources must be fresh `source_failed` with empty rows;
- a bounded read-only query against each live router database must independently
  prove at least 51 distinct task/model/provider groups without exposing rows;
- both telemetry timers must be active, web must be failed/inactive, and durable
  watchdog must be inactive;
- the durable watchdog lock must be unheld; an inactive systemd unit is not
  sufficient when a legacy or detached watchdog process still owns dispatch;
- public Agent Platform health must remain fail-closed: `401` from the exact
  verified auth-first Nginx route and its pinned common location include, or an
  upstream-facing `502`/`503`.

Before switching releases, recovery apply verifies that both telemetry timers,
both timer-triggered oneshot services, and the watchdog actually stopped. It
publishes the success record only after RC12 returns the authenticated `401`
health boundary and `current` resolves to RC12; the watchdog starts last.
The final watchdog start must remain `active/running` with the same nonzero
`MainPID` and restart count across a bounded observation interval. A process that
briefly becomes active and exits because another process owns the lock is a hard
failure, never successful deployment evidence.

Because the previous release is known unable to perform a healthy web boot,
`recovery-apply` does **not** claim a healthy rollback exercise. It records
`rollback_exercised=false` and
`rollback_mode=skipped_known_degraded_previous`. On any candidate failure it
restores the exact previous symlink, systemd unit bytes and deployed marker,
keeps the Agent Platform route on the reviewed maintenance 503 fragment,
re-quiesces the timers, their oneshot services and the durable watchdog before
restoring mutable authority, and aborts authority restoration if that gate fails.
It removes any premature success record only after exact authority restoration
is verified, restarts telemetry timers only after all fail-closed rollback checks
pass without error, and preserves the failed archive for audit even when another
rollback step is incomplete. Normal and recovery cutovers share one root-owned
non-blocking deployment lock under the verified mode-0700 `/run/herdr` directory,
held from authorization through success or rollback.

After a successful recovery promotion, the normal cutover path is authoritative
again for subsequent releases.
