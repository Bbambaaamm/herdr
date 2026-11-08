# Slice C — Read-only operator package

This package is intentionally non-mutating. It is the review checklist for a
future `quantadmin` run; it does not authorize deployment, policy publication,
service restart, sudoers/AppArmor changes, credential use, or a canary.

## Required operator checks

1. Confirm hostname and active release identity.
2. Confirm the release archive and manifest SHA-256 against the approved
   exact-head package.
3. Confirm that `/opt/herdr/current`, the issuer, runtime trees and retained
   publication record are root-owned, regular/non-symlink files with the
   approved modes and ancestry.
4. Confirm schema-2 host-policy digest, publication-record digest, profile
   digest, issuer digest, consumer, parent/child grant identity, fencing and
   result-slot binding. Do not infer authority from a readable file alone.
5. Confirm all relevant services and timers before and after remain unchanged.
6. Run only the reviewed read-only preflight and capture stdout, stderr, exit
   code, release identity, service state and `/opt/herdr/current` before/after.

## Physical acceptance request (separate approval)

If and only if every read-only gate is PASS, request a separate approval for
one disposable, zero-provider root/child/result canary with:

- one disposable root and one child;
- zero provider/network calls and zero economic operations;
- synthetic credentials only;
- explicit timeout, fencing and cleanup;
- durable result reservation, one submission and one parent acceptance;
- retained kernel evidence for PID/mount namespaces, runtime inodes,
  credentials, network isolation and audit/replay state.

Any mismatch is `ROOT_PREFLIGHT_BLOCKED`; do not repair it by changing live
policy or retrying an uncertain operation.

## Rollback and cleanup

The operator must identify the exact reviewed release and prior release before
any later approval. Cleanup must wait for all disposable processes and mounts
to exit. No production queue, reservation, credential, service or release
symlink is in scope.

