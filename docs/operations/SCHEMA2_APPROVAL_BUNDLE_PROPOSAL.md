# RC6 — schema-2 host authority approval bundle (PROPOSAL ONLY)

Status: **NOT APPROVED / NOT PUBLISHED**. This file is a review contract, not
an authority or a generated production configuration. No task, model, worker,
GitHub issue or current profile may select its own approval or hashes.

The machine-readable [proposal manifest](../../configs/schema2-approval-bundle.proposal.json)
contains explicit `null` placeholders. It **must never** be consumed as an
operator approval or automatically filled from a task, checkout or live
profile. It has no credentials or production grant contents.

## Source of truth and required records

1. Immutable RC6 code release: `v0.3.0-router-v5-p1d-rc6`, commit
   `8d8ad50375557b7ac77348e6475cb455682f4a9a`, verified by installed
   `herdr.release.verify_tree`. A new version must be separately reviewed.
2. Root-owned `herdr-runtime-publication-1` approval request: independently
   reviewed exact `code` / `hermes` / `python` file and executable inventories;
   existing `scripts/publish-herdr-runtime.py` can validate a **root-approved**
   request without `--publish`. No existing publication record is implicitly
   approved for RC6 merely because it exists.
3. Existing publisher's retained root-owned `herdr-runtime-publication-record-1`
   with `record_sha256`, `version`, `approval_sha256`, and three manifest hashes.
   Validate with `validate_runtime_publication_binding` and match the record's
   actual immutable source paths to host-policy trees.
4. `host-policy.json` schema 2 **preserving all existing grants/consumer
   ceilings, template identities, work_contracts and budget limits**. Include
   exact `private_launch.profile` name/source/file-hashes (trusted host review),
   `credential_approval` (finite, independently approved, expires),
   `runtime_publication` with retained record and manifest identity, and
   `plan_handoff.automatic_issuer=true` only after operator authorization.
   Profile credential contents and token hashes must never enter Git.
5. Root-owned `launch-plan-issuer.json` with issuer schema
   `herdr-automatic-launch-plan-1`, exact SHA-256 of the *reviewed schema-2
   host-policy*, approved cgroups/entrypoints and 1–60s finite timeout. Only
   the existing root-owned issuer may publish plans.
6. Root-owned `/etc/herdr/launch-plans` with protected ancestry, fresh no-replace
   publication and the existing one-shot FD custody/redeem path. Do not create
   this directory, socket or issuer service as part of a read-only audit.
7. A distinct operator-authorized **zero-provider, zero-budget disposable**
   root → child → durable result canary, with PID/mount/network/FD evidence,
   fencing, parent acceptance, restart/replay and cleanup. Offline tests and
   static schema-2 readiness never prove this final requirement.

## Read-only current-state check

Run from the **installed immutable** code tree, without privileged publish:

```sh
/usr/bin/python3 -I -B /opt/herdr/current/agent-stack/bin/agent-herdr-schema2-readiness
```

The immutable entrypoint becomes available only in a subsequent reviewed and
deployed release containing this proposal; the current RC6 does not have it.
Before then the operator may review source in Git, but must not execute a
mutable Git checkout with `sudo`.

Expected current result: `ROOT_PREFLIGHT_BLOCKED` (schema 1, missing profile,
wrong issuer pin and absent launch-plan root). This is a designed fail-closed
state and must **not** be fixed by fabricating credential hashes or copying a
live profile into Git. Hashes are audit evidence, never independent authority.

## Promotion gates

This PR is documentation plus a read-only readiness checker only. Require
separate exact-head CI, security review, root-owned publication approval,
operator confirmation, explicit rollback plan and native root/child canary.
Never automatically merge, deploy, rotate credentials, change `/etc/herdr`,
restart services, requeue historical tasks or authorize provider calls.
