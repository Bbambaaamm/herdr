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
   candidate verification and rollback exercise;
7. atomically switches `current`, publishes only bounded tag/SHA/config metadata,
   and verifies the internal health boundary and Herdr sandbox;
8. switches back to the previous release and verifies it, including restarting
   the watchdog against the previous `/opt/herdr/current`, then promotes the
   candidate again—exercising rollback of both web/export and durable orchestration
   before public activation;
9. restores the exact authenticated Nginx route and proves the QuantLab root status
   and unauthenticated `401` boundary are unchanged.

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
