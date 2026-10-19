# Budget audit recovery

Use this procedure when a completed agent run has retained budget evidence but
its final independent checker failed. A running service or a successful model
response alone does not establish task completion.

## 1. Stop and identify the original attempt

Keep the original task ID, run token, fencing token, allocation, operation ID,
audit, result, receipt and one-time marker. Confirm that the original unit and
its entire cgroup have no remaining processes. Never redispatch an uncertain
attempt merely because its final checker failed.

## 2. Verify the ownership boundary

Use the declared host UID. WorkBudgetAuthority requires the audit directory to
belong to the effective host UID and forbids group or world write access.
Root is a different UID; root access does not make root the original budget
host. Do not chown the original audit, relax this check, delete budget records,
remove its lock, reset a reservation, or manufacture a zero-cost settlement.

## 3. Pin and copy retained evidence

Read bounded regular files with no symlink following. Check owner, link count,
directory permissions, stable inode/content stamps and SHA-256 before and after
the read. Bind the audit to the original allocation, lineage, task identity,
plan, operation and sealed result receipt.

Create a new private copy of the pinned audit under the declared host UID.
Run the unchanged snapshot and reconciliation reader on that copy. Its lock
belongs only to the new private verification directory. Never construct a
write-capable budget authority against the original audit for a read-only check.

## 4. Check settlement without repeating work

Require the original operation to have started and to have a retained usage
record. Check cumulative upper bounds, implementation attempts and inflight
operations. Unknown measurements remain unknown; a missing response does not
permit releasing or repeating the original reservation.

Compare all original evidence hashes, stamps and budget-directory entries after
projection, then remove only the new temporary verification copy and its lock.
Do not change the original task status as a side effect of this check.

## 5. Keep completion claims separate

A budget projection verifies retained accounting evidence. It does not establish
real model inference, accepted coding work, integration, deployment or full
autonomy. Coding completion still requires the exact local result receipt,
commit, pull request, required CI checks, independent review and the retained
worker's accepted result record. Resume only that retained acceptance path.
