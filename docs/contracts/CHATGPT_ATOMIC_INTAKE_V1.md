# ChatGPT → Herdr: atomic proposal consumption within existing GitHub intake

**Scope: source-only, not activated.** This change is deliberately stacked
on the proposal (#255), inspection (#256) and dual-approval (#257) slices.

## Durable transaction

The existing `github-intake-state.json` root row `Bbambaaamm/herdr#53`
now supports an optional `proposal_consumptions` map keyed by a canonical,
content-addressed binding SHA-256. Each entry contains:

- the exact previously validated proposal/root approval binding;
- the existing root task ID `github-herdr-issue-53-approval-<id>`;
- `publication_pending` or `published` state.

This map is **not a second queue or an independent authorization ledger**.
It is persisted by the **same `_consume_admission` state transaction**
that first consumes the existing root #53 approval. Both approval consumption
and the proposal claim must be durably written before the existing
`publish_task` can expose a pending task via renameat2 NOREPLACE, fsync
and directory fsync. `_mark_admission_published` then marks both the
root intent and the optional proposal claim published in the same state write.

All old consumers and normal root-only intake use the unchanged default
`proposal_binding=None`. Only an explicitly supplied, previously
verified binding may enter the optional branch of `_queue_issue_locked`;
there is **no CLI, GitHub webhook, MCP listener, auto-scanner or public
entrypoint** that activates the branch.

## Fail-closed behavior

- Reuse of the same proposal issue or content digest under another root
  approval is denied even if the original task is already terminal.
- Reuse of the same root approval remains denied by the existing history.
- Crashes after consuming either approval retain a `publication_pending`
  blocker and require host-authorized reconciliation, never blind retry.
- Publication commits both statuses or leaves `publication_pending` state.
- Incomplete, conflicting, malformed or hash-mismatched claims block intake.
- The ordinary scan merges durable proposal claims back into its snapshot,
  so a stale in-memory scan cannot erase consumption history.
- The optional binding is restricted to consumer `herdr`, repo
  `Bbambaaamm/herdr` and root issue #53.
- Legacy root-only scans and all other consumers remain unaffected.

## Not yet a production submission API

The internal optional argument is *not* an authority boundary: a future
host-owned activation path must obtain the binding fresh from authenticated
GitHub approvals and bind the root approval explicitly to the selected
proposal. The approval currently authorizes a root cycle, but does not
itself cryptographically express which ChatGPT proposal is selected.
That explicit operator intent remains an activation gate.

Before any activation, demonstrate:

1. Root approval explicitly binds the proposal issue ID, content digest,
   GitHub revision and authorization identity without broadening
   maintainer-comment-v1.
2. Host-controlled admission evaluates PAUSED/UNKNOWN/active owner status,
   original run/fencing authority and historical economic attempts.
3. Existing protected sandbox, budget, model/provider and child policies
   remain in force; unverified model selection causes a checkpointed hold.
4. The protected-controller release, CI, exact-head independent security
   review and required GitHub approval are satisfied.
5. Simulated crash windows, malicious input, repeated approval and
   concurrency checks pass; one accepted episode is never launched twice.

The current code delivers an **atomically durable optional task-claim
primitive**, not live ChatGPT → Hermes invocation.

## Independent review P2 closure

Pending proposal consumption must have an exact matching pending root
intent. A missing or mismatched intent blocks state load and subsequent
admissions, never allowing a newer root approval. A pending proposal
independently triggers reconciliation. Regression tests reproduce corrupted
intents and unchanged state on retry.
