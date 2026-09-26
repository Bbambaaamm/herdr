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
→ signed/pinned release tag
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

Deployment creates a pre-change backup and supports atomic symlink rollback.

## Consumer upgrades

Consumer changes and Herdr upgrades are separate pull requests. A consumer may remain on an older compatible Herdr release while another consumer canaries the next release.

Model/provider policy is versioned separately from application code and must have explicit rollback.
