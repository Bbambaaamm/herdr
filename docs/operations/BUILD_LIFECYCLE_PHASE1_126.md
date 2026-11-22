# Herdr #126 — Build Artifact Lifecycle Manager, phase 1 (read-only)

**Status: DRAFT / READ-ONLY / NO CLEANUP AUTHORITY**

This is the smallest first phase of the Build Artifact Lifecycle Manager.
It deliberately reuses the existing capacity watcher and TaskGraph/host
authority boundaries. It introduces **no** new systemd timer, agent,
scheduler, root policy or deletion API.

## Implementation

- `herdr/build_lifecycle.py` is a bounded inventory and optional manifest
  reader. It accepts **only explicitly enumerated names** under a chosen
  user-owned scratch root, rather than recursively searching all of `/home`.
  Names are strictly allowlisted to temporary Herdr/Hermes build prefixes.
- The root and child directories are opened with pinned directory file
  descriptors, `O_DIRECTORY|O_NOFOLLOW`; all root ancestry components
  reject symlinks. Recursion uses `os.scandir` on directory FDs and
  `stat(..., follow_symlinks=False)`. Hard links, symlinks, boundary changes,
  unreadable entries and traversal truncation appear as review blockers.
- Traversal is bounded by max entries, depth and number of candidates.
  A truncated measurement is marked `measurement_complete=false`; the
  partial allocated byte count is never treated as reclaimable capacity.
- Optional `herdr-build-manifest.json` declares v1 `build_id`,
  `source_commit` and `state`. It is untrusted user-owned input and is
  **never** accepted as host-signed approval, even when it claims
  `CLEANUP_ELIGIBLE`.
- Every returned row has `state=BLOCKED_REVIEW`,
  `cleanup_authorized=false`, `can_delete=false`. Every report has
  `deletion_performed=false` and `model_calls=0`.
- No subprocess, git mutation, file deletion, quarantine, external network,
  budget operation or provider model call is implemented.

The command below writes JSON to standard output only. For repeatability,
operator-provided evidence persistence can occur as a separately reviewed
step; the scanner does not modify the filesystem.

```sh
python3 -I -B scripts/scan-herdr-build-lifecycle.py \
  --root /home/agentops/tmp \
  --name herdr-hermes-build-rc7-isolated-20261116 \
  --name herdr-hermes-build-rc7-repro-20261116 \
  --name herdr-hermes-build-audit-20261111 \
  --max-entries 1000 --max-depth 16
```

### First real staging observation — 2026-11-16

Three explicitly named scratch builds were inspected with a 1000-entry
per-build bound. All three were `BLOCKED_REVIEW`; all were unregistered
legacy builds, each observation was truncated and **no file was removed**.
The observed byte counts are incomplete and should **not** replace full
read-only `du` estimates (~1.4 / ~1.6 / ~1.6 GiB). No current workflow,
lease, open-FD/recovery verification or independently preserved evidence
was established, so **nothing is declared safe to delete**.

## What phase 1 DOES NOT do

- No trusted lifecycle registry, lease owner, storage authority or
  signed manifest issuance. No authorization from caller-provided JSON.
- No full `/proc` process/FD or Git worktree inventory, no verified
  artifact archive attestation, no parent ACK/replay acceptance.
- No cleanup executor, recursive deletion, quarantine or root-owned Docker
  inspection; the scanning code cannot return a cleanup authorization.
- No claim that all same-device bind mounts are identifiable by the
  byte-count walk. A later cleanup implementation **must** use its
  own stronger root-owned mount/lease/fencing integrity checks.

## Next phases (not part of this PR)

1. Attach durable host-issued build identities at creation (build ID,
   repo, exact commit, user, pinned root inode, artifact evidence IDs).
   Reuse existing TaskGraph leases, durable evidence and AuditLog; do not
   create a parallel scheduler or permission authority.
2. Add independent, bounded owner-verified evidence receipts and full
   active-process/open-FD/mount/worktree/lease/fencing revalidation.
3. Expose a dry-run cleanup eligibility report based on all host-attested
   checks. Any UNKNOWN remains BLOCKED.
4. After separate operator authorization and independent security review,
   implement FD-relative cleanup on registered disposable trees, with
   crash/replay-safe audit and no symlink/mount traversal.
5. Keep the existing `herdr-capacity-watch.timer` as the capacity signal;
   do not turn its read-only service into a privileged deleter.

**Disposition:** safe phase-1 inventory candidate only. Release and
autonomous work remain NO-GO under existing #126/#132/#184 controls.
