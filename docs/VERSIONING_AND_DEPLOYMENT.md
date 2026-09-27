# Versioning and deployment

## Versioning

Herdr uses Semantic Versioning.

- 0.x: migration and contract stabilization.
- 1.0.0: stable TaskGraph, scheduler, admission, telemetry, provider and consumer contracts.
- MINOR: backward-compatible capabilities/providers.
- PATCH: backward-compatible fixes.
- MAJOR: incompatible contract or policy-schema changes.

Consumer repositories pin both a tag and immutable commit SHA in HERDR.lock.

## Release path

main
→ CI-green immutable commit
→ annotated/pinned release tag
→ staging deployment
→ canary consumer(s)
→ soak and telemetry review
→ production promotion

No consumer follows floating main in production.

## Runtime layout

Recommended server layout:

/opt/herdr/releases/<version>/
 /opt/herdr/current -> immutable release
 /etc/herdr/consumers/<consumer>.yaml
 /var/lib/herdr/ durable state
 /var/log/herdr/ or structured journal/telemetry sink

The durable agent control-plane (`agent-task-worker`, dispatcher, recovery,
watchdog, intake/export and maintenance helpers) executes from
`/opt/herdr/current/agent-stack/bin`. Mutable copies under
`/home/agentops/.local/bin` are not production authority. External binaries
such as the pinned `herdr 0.9.1`, Hermes, Codex and rclone remain external
dependencies.

Deployment creates a pre-change backup and supports atomic symlink rollback.

The production cutover implementation and operator gates are defined in
`deploy/herdr/cutover/RUNBOOK.md`. A release tag triggers a full contract run and a
deterministic bundle whose payload and policy overlays are hash-bound. The public
dashboard reports the deployed tag and immutable commit from bounded read-only
metadata; it never infers deployment identity from floating `main`.

## Consumer upgrades

Consumer changes and Herdr upgrades are separate pull requests. A consumer may remain on an older compatible Herdr release while another consumer canaries the next release.

Model/provider policy is versioned separately from application code and must have explicit rollback.
