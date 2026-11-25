# ChatGPT → Herdr: double-approved admission binding (staging)

**Status: PREPARED, NOT ACTIVATED.** This is an authenticated read-only
preflight for future authorization. It does not enqueue or dispatch work.

## Why this is necessary

Herdr is currently configured as `root_only` on issue #53. A ChatGPT
proposal issue, or a ChatGPT request, cannot authorize a new process.
The existing `maintainer-comment-v1` GitHub admission is authoritative for
one Herdr root-cycle approval. The canonical host supervisor, scheduler,
fencing, budget, isolation and PR gates are separate authorities.

The optional command
`agent-github-intake --prepare-proposal-binding Bbambaaamm/herdr ISSUE`
reuses the same guarded `gh api` GET transport as existing intake. It:

1. Confirms the proposal issue has the **exact** canonical title/body and
   stable revision identity, using the phase-1/2 contract.
2. Requires a fresh `maintainer-comment-v1` approval on that exact proposal.
3. Requires a second fresh `maintainer-comment-v1` approval on #53,
   recorded AFTER the proposal approval.
4. Confirms both approval receipts belong to the same authenticated repository
   and to the exact current issue revisions.
5. Returns deterministic binding evidence with both GitHub approval IDs,
   both issue revisions, exact request digest, target and root #53.
6. Reports `VALIDATED_NOT_ADMITTED`, `task_created=false`,
   `execution_authorized=false` and a precise remaining blocker.

The pure `herdr.chatgpt_admission_binding` component rejects ambiguous
identities, missing/invalid receipts, mismatched source hashes,
out-of-order approvals and known repeated proposal identifiers. Its
`consumed_proposals` parameter MUST come from a protected durable record
before it may be used for actual admission.

## Missing live authority, next development slice

A proposed binding is **not yet** a runnable task. An actual admitted work
episode requires all of the following in the **existing** intake/TaskGraph:

- Host-owned, atomic `consumed_proposals` persistence, committed under
  `github-intake-state.lock` in the same durable consume-before-publication
  transaction as the #53 root approval. Include crash-window replay tests.
- Reconciliation of all existing proposal/approval/task histories so deleting
  or compacting a queue file cannot authorize a repeated economic attempt.
- A guarded mapping into the *existing* root #53 task, preserving parent ID,
  task/run token, fencing, budget, allowlisted tool/model scopes and owner.
- Observed PAUSED/UNKNOWN supervisor and already-active root task state MUST
  continue to block admission before any process creation.
- Independent exact-HEAD security review, passing CI, formal approval,
  verified immutable release and separate host activation authorization.

Do not add a second queue, switch to direct shell invocation, start a second
Hermes process, or attempt to use this preflight receipt as a host grant.
