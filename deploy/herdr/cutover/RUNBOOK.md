# Versioned Herdr runtime cutover

This procedure migrates the existing Agent Platform services from the legacy
`/opt/agent-platform/release` directory to an immutable, tagged Herdr release.
It does not enable a consumer, add a tool or permission, change router state, or
alter QuantLab execution. The external `herdr 0.9.1` binary remains the pinned
dependency recorded by version, size, and SHA-256.

## Release gate

Use only an annotated tag whose `Release bundle` workflow completed successfully.
Download that workflow's archive and adjacent `.sha256` artifact. Verify the
download locally, then copy both files to a new mode-0700 directory owned by the
operator on `quantlab-staging-01`. Never build a production archive from floating
`main`, an untagged commit, or `v0.1.0-bootstrap`.

The bundle is deterministic and contains a closed production payload, three
validated consumer policy overlays, `RELEASE.json`, and `MANIFEST.sha256`. It does
not contain secrets, credentials, databases, logs, prompts, raw queries, or the
external Herdr binary.

## Unprivileged preflight

Extract the verified archive into a fresh private operator directory. Run the
cutover program from that extracted release so the reviewed tool and candidate
payload have the same tag and commit:

```sh
python3 deploy/herdr/cutover/cutover.py preflight \
  --archive /home/quantadmin/herdr-cutover/REVIEWED.tar.gz \
  --expected-legacy-commit 41179635c8654a60c5d9234acccb6e91b2028b72
```

Preflight is read-only. It verifies the annotated release metadata and every bundle
hash, consumer schemas, external binary, exact legacy commit, known unit/Nginx
hashes, service state, current authentication boundary, and a content-only diff
between the legacy and candidate runtime. It emits no source contents or secrets.
Any mismatch is a hard stop.

## Single privileged step

After preflight and the release workflow are green, run exactly one privileged
command. The confirmation is the release tag plus the first twelve commit
characters printed by preflight:

```sh
sudo /usr/bin/python3 -I -B deploy/herdr/cutover/cutover.py apply \
  --archive /home/quantadmin/herdr-cutover/REVIEWED.tar.gz \
  --expected-legacy-commit 41179635c8654a60c5d9234acccb6e91b2028b72 \
  --confirm vX.Y.Z-rc.N-0123456789ab
```

The apply operation:

1. repeats the full preflight as root;
2. installs an immutable `/opt/herdr/releases/<tag>-<sha12>` directory;
3. installs the exact policy overlays under `/etc/herdr/consumers` only when absent,
   refusing any mismatch on repeat;
4. changes the Agent Platform services and the durable agent-stack watchdog
   to execute through `/opt/herdr/current`, with dispatcher/worker/recovery/
   maintenance helpers resolved from that same immutable release;
5. reserves the public dashboard paths with the fail-closed maintenance fragment;
6. stops the durable watchdog, refuses promotion while any
   `agent-task-worker` remains active, and keeps durable dispatch quiescent through
   candidate verification and rollback exercise, snapshotting and restoring
   the exact previous systemd unit bytes and deployed-release marker;
7. atomically switches `current`, publishes only bounded tag/SHA/config metadata,
   and verifies the internal health boundary and Herdr sandbox;
8. switches back to the previous release, restores and verifies the exact
   previous systemd units and deployed-release marker, then promotes the candidate
   again—exercising rollback of both web/export and durable orchestration before
   public activation; the durable watchdog remains stopped throughout all
   intermediate transitions;
9. restores the exact authenticated Nginx route and proves the QuantLab root status
   and unauthenticated `401` boundary are unchanged.

An `already_deployed` result is accepted only when the current symlink,
all candidate systemd units, installed consumer policy digest, and bounded
`deployed-release.json` identify the same immutable release.

Any failure atomically returns `current` to the prior release, restarts the same
services, and restores the exact prior Nginx fragment. The route remains fail-closed
during the operation. No database, credential, consumer state, shared vhost, or
legacy release is deleted.

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


## Degraded RC8 recovery

The normal `apply` path remains strict and requires a healthy authenticated
previous runtime plus an exercised healthy rollback boot.

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
- public Agent Platform health must remain fail-closed: `401` from the exact
  verified auth-first Nginx route, or an upstream-facing `502`/`503`.

Before switching releases, recovery apply verifies that both telemetry timers,
both timer-triggered oneshot services, and the watchdog actually stopped. It
publishes the success record only after RC12 returns the authenticated `401`
health boundary and `current` resolves to RC12; the watchdog starts last.

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
