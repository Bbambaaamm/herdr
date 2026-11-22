# Herdr #126 — Build Lifecycle phase 2: root-attested evidence observer

**Status: DRAFT / HISTORICAL RECEIPT VERIFICATION / READ-ONLY ONLY**

Stacked on phase 1 PR #227. Reuse existing capacity watcher, TaskGraph
lease/fencing and root-policy trust boundary; no second scheduler, no new
host issuer running in production, no new timer, no cleanup authority.
The new module is `herdr/build_lifecycle_host_evidence.py` and its
operator-only CLI is `scripts/scan-herdr-build-host-evidence.py`.

## Trust design and present status

- `/etc/herdr/build-lifecycle-trust.json` (proposed, **NOT INSTALLED**)
  is an independently root-owned immutable key file. The observer reads
  it only via existing `herdr.operation_readiness.read_protected`, with
  root ownership, no symlink traversal, no writable ancestors, bounded
  size and a single immutable snapshot.
- `/etc/herdr/build-lifecycle-receipts/<build-id>.json` (proposed,
  **NOT INSTALLED**) must be root-owned, non-writable, read-only, and
  signed with Ed25519 by the approved host-only evidence issuer. The
  private signing key must never be available to agents or build roots.
- Receipts are bound to `build_id`, exact inode + device, owner UID,
  source commit, TaskGraph task ID, attempt, fencing token, host-observed
  released lease, sealed artifact evidence digest and durable parent ACK
  digest. Signing scope includes all fields, issuer, key ID and 5-minute
  maximum validity window.
- The verifier checks signature, issuer identity, exact build root
  inode/device/owner, syntactic envelope, timestamps and expiry.
  Invalid or absent trust/receipt => `ROOT_EVIDENCE_UNAVAILABLE` or
  `ROOT_EVIDENCE_INVALID_OR_UNAVAILABLE`.
- A fully valid signed receipt only proves **HISTORICAL_SIGNATURE_VALID_ONLY**.
  Historical acceptance does not prove the original lease remains
  released or that no new process has opened the workspace. Even a
  matching signed record is *never* an executable cleanup grant.
- Caller-supplied user-owned manifest stays untrusted and
  `can_delete=false`, `cleanup_authorized=false` for all outcomes.

The root-owned trust and receipt publisher are **design requirements**,
not components deployed by this PR. Until separately reviewed, approved
and bound to the existing host issuer / TaskGraph evidence mechanism,
they remain absent and all real builds fail closed.

## Additional live read-only probes

- Host /proc PID inventory examines currently visible PIDs, each cwd,
  process root and up to 256 FDs. Any path under a candidate creates
  `PROCESS_REFERENCE_OBSERVED`; a permissions error or truncated scan
  creates `PROCESS_VISIBILITY_INCOMPLETE`. The snapshot is bounded by
  2048 PIDs and 64 reported hits. No PID is signaled or stopped.
- /proc/self/mountinfo is observed for mount points under the build
  root. Finding any mount blocks. An empty result explicitly means
  `NO_MOUNT_IN_OWN_NAMESPACE_ONLY` **not** proof that private or
  container mount namespaces contain no mount.
- No live TaskGraph or root broker query is currently authorized here.
  `lease_fencing_observation=UNKNOWN_NO_LIVE_HOST_AUTHORITY` and
  `parent_ack_observation=UNKNOWN_NO_LIVE_HOST_AUTHORITY` are deliberate.
- `cleanup_authorized=false` remains fixed even when all read-only
  observations are clear. This is not the host cleanup authority.

## Real staging read-only observation on 2026-11-16

```sh
python3 -I -B scripts/scan-herdr-build-host-evidence.py \
 --root /home/agentops/tmp \
 --name herdr-hermes-build-rc7-isolated-20261116 \
 --name herdr-hermes-build-rc7-repro-20261116 \
 --name herdr-hermes-build-audit-20261111 \
 --max-entries 1000 --max-depth 16
```

Three candidates: all `ROOT_EVIDENCE_UNAVAILABLE`, process scan
`UNKNOWN`, and mount scan `NO_MOUNT_IN_OWN_NAMESPACE_ONLY`. The phase 1
inventory is truncated at 1000 entries/build. All three remain
`BLOCKED_REVIEW`. There was no deletion, process termination, model
call, service change, root policy edit, or disk reclamation. The
root-owned receipt/trust records DO NOT currently exist on staging.

## Next required production P0 gates

1. Independently review signer integration with existing root-only host
   authority and immutable source manifest. Never trust a user-owned
   JSON file, synthetic test key, or hash alone as proof.
2. Bind receipt lineage to the existing TaskGraph and durable parent ACK
   evidence, exact build epoch, lease state, fencing token and attempt.
3. Expose a bounded host RPC to revalidate *at cleanup time* the same
   pinned root inode/mount namespace, no active PID/open FD, no live
   lease, no recovery/parent ACK dependency. Complete host namespace
   authority must be independently accepted; unprivileged /proc alone
   cannot establish global absence.
4. Keep the cleanup executor and approval separate from the read-only
   scanner. Implement and review FD-relative mount-aware traversal with
   zero symlink/rename race window, audit and rollback controls.
5. Only after complete P0 acceptance add explicit operator cleanup
   authorization. Nothing in this PR authorizes a delete/move.

**Disposition: P2 verification prototype only; NO-GO for cleanup and RC7.**
