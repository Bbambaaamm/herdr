# Administrative terminal UNKNOWN in the existing recovery

This is delivery reconciliation for an original uncertain attempt. It does not
prove task completion, issue completion, usage, cost, or safe redispatch. The
task stays in `blocked/` with `attempt_state=terminal_unknown`; intake,
dispatcher, worker, durable bridge, canonical parent composition, recovery and
queue export retain the operator blocker.
No dependency is released and no successful result is manufactured.

## Preparation and activation are separate

The source change alone creates no decision, changes no live task and restarts
no service. Do not invoke the apply command while reviewing this change.

A future activation requires a separately approved maintenance operation:

1. Pin and independently review the exact release of **all** queue writers:
   intake, dispatcher, worker, recovery and durable bridge. Stop and verify
   quiescence of old coordinators/bridges before publishing the decision.
   A retained namespace custodian may keep its shared legacy epoch lock.
   Old installed binaries do not honor the new hold; the decision's
   `writer_scope` is an operator attestation, not automatic proof of migration.
2. Preserve the original result slot, task bytes, event histories and every
   original reservation. Inspect through the existing recovery's
   `--inspect-terminal-unknown TASK_ID`. Inspection reads only; it neither
   writes an approval nor calls SDK/provider/budget reconciliation.
3. Review a root-owned decision at
   `/etc/herdr/recovery-terminal-unknown/TASK_ID.json`. All ancestors must be
   root owned and not group/world writable. The directory must allow the
   configured host UID to traverse it and the file must allow that UID to
   read it (typically directory 0755, file 0644). No symlinks or multiple links.
   Never include credentials or task prompts in the decision.
4. Only with separate activation authorization, run the existing recovery as
   the configured host UID with `--apply-terminal-unknown TASK_ID`. Root itself
   is rejected unless it is the configured host UID. Applying is explicit;
   a normal watchdog only holds a pending decision and never applies it.

The closed decision schema is defined by `load_decision`. It binds task ID,
original run/idempotency/attempt/fence digest, all semantic task fields,
the observed empty result's device/inode/hash and modification/change timestamps, the complete matching original
budget-ledger inventory, the work-history hash and a separately reviewed
evidence hash. It also includes an approval reference, issuance/expiry (at
most one hour) and the maintenance attestation
`reviewed_writers_quiesced_and_locked`. Inspection does not set the evidence
hash or authorize the transition.

The supported scope is deliberately narrow: an original root modern WORK
attempt, already blocked for uncertain delivery, a baseline-only host work
history, an unchanged empty result and **no child ledger**. Existing children,
active workers/bridge, new result bytes, budget/history drift, an accepted
result or another queue copy require their own reconciliation. This path
does not close, collect or signal the retained agent session.

## Crash and concurrency behavior

The explicit operation owns the same recovery lock used by the ordinary
watchdog, plus existing dispatcher and worker-loop locks and the original
child-claim bridge lock. Locks are nonblocking; a busy writer denies apply.
It does not call `parent_attempt_guard`: that helper may initialize/replay
child evidence even with result reconciliation disabled.

Before changing the task, recovery exclusively publishes and fsyncs a sidecar
named `TASK_ID.watchdog-terminal-unknown-DECISION_SHA.json` in existing
`results/`. It retains the complete original task bytes, their hash, the
decision/evidence hashes, the exact after-state and budget/work hashes.
This is administrative history, never the canonical task result. Recovery
rechecks the task and all pinned observations before atomically writing the
after-state. An interrupted intent resumes only against the exact original
bytes; an already applied transition is a read-only idempotent result.
Neither path releases, settles, rewrites or recreates a reservation.

Late evidence must remain available for a separately reviewed explicit
reconciliation. Automatic recovery does not consume it, start a bridge,
clean a session or retry an UNKNOWN attempt. Removing an expired pending
decision is also an operator reconciliation; expiry never silently requeues.

## Verification

Synthetic Linux tests exercise original identity/accounting preservation,
exclusive publication, crash recovery, lock contention, stale inputs,
protected decisions, late-result holds and guards across existing writers.
They never use a real task, model, network provider, credential or deployment.
The ordinary agent-stack regressions must remain green. Green tests/review
prepare this capability; they do not mean any live transition was applied.
