# Durable completion evidence

Implementation: `herdr/evidence.py`, `agent_completion_evidence.py`, the existing worker finish path and watchdog recovery. Final managed-child integration depends on issue #82; this document does not claim that pending integration is complete.

## Authority and completion levels

A worker publication is a claim bound to one durable task/attempt. The host freezes a validation plan before dispatch and accepts it through the existing `ArtifactRef`, `WorkspaceManager` and `ReviewerGate`. A model's `producer`, `actor_id`, `signed`, or prose PASS is never proof of origin.

`control_cycle` proves only that the declared control result has a summary and next action. `verified_worker_result` proves the exact artifact satisfied its declared checks and independent review. Integration and deployment remain separate, initially null, and require their existing project/release gates. Neither a control cycle nor a report completion satisfies an unimplemented dependency.

## Frozen plan and bundle

Version 1 plans bind task ID, run token, attempt, fencing token, idempotency key, repository, specification digest, policy digest, baseline commit, allowed artifact root, required checks, reviewer, and validator environment. The plan's decision hash excludes observational baseline check results; the immutable stored envelope and accepted bundle hash include those observations.

Coding requires a sealed clean committed worktree, exact base/commit/content hashes, and both project checks. The collector reads authenticated GitHub evidence: exact repository and full SHA, actual GitHub application IDs, the pinned Herdr CI workflow/run/version, current successful checks, no unresolved review threads, and the actual Codex review bot's clean decision resolved to the full commit. A changed validation workflow requires trusted replanning. Accepted evidence is not reusable approval for a later merge or deployment.

Research/review contracts specify one JSON report under `reports/research/` or `reports/review/`. No unrelated file change is allowed. Research validates declared section coverage, summaries and credential-free HTTPS source references; schema validation does not assert source truth. Review validates its exact target commit, findings and consistent verdict; finishing a blocked review does not approve the target. Both require GitGuardian and independent exact-artifact review, without invented compilation evidence. Unsupported consumers/kinds/criteria fail closed.

## Process boundary and persistence

The trusted collector owns `tasks/verification`, outside worker-writable worktrees, workspace, Hermes home and caches. The task sandbox mounts it read-only. Permission bits or SHA-256 alone are not the authority boundary. Artifact Git commands run in a read-only, network-isolated namespace, with bounded output and disabled hooks/fsmonitor; untrusted clean filters cannot write host evidence. The host rechecks artifact bytes after external collection.

Plans and accepted bundles use canonical JSON with an integrity digest, a flushed temporary file, atomic exclusive publication, and directory fsync. Publication never overwrites a different record. Partial temporary files cannot be accepted. Missing, unavailable and invalid evidence have distinct statuses.

`verification_pending` retains the original publication, run token, idempotency key and attempt counter. Worker and watchdog reconcile that same publication; intake cannot launch another coding episode. Restart after bundle publication reuses the immutable accepted record, including after workspace removal.

## Retention and rollout

Accepted bundles and frozen plans outlive temporary workspaces. This implementation does not delete or rewrite them automatically. A future explicit host retention policy must preserve accepted audit bindings and coordinate access controls with issue #76. Bundle metadata contains digests and bounded source identities, rather than prompts, credentials, terminal text or model conversations.

Physical regressions test protected evidence mounts and hostile Git filters on a host with bubblewrap. CI records unsupported namespace capability as a skip; separate host validation must demonstrate that boundary before release. Historical DONE records remain historical and are not relabelled as newly verified results.


### Rejection and immutable acceptance
An accepted address is derived only from protected task/attempt identity and
the frozen plan, never from worker-selected result bytes. A different artifact,
workspace, PR reference or control result for that address is a conflict; one
attempt cannot publish two authoritative outcomes. Identical crash replay
reuses the existing record.

Only missing or unavailable evidence enters automatic verification reconciliation.
Invalid identity, changed policy/workflow, conflicting publication or rejected
artifact is preserved as blocked with verification_resolution: needs_replan
and an explicit protected next action. Worker, watchdog and intake do not silently
redispatch or poll this permanent rejection. A trusted subsequent plan must apply
the node/retry/budget policy; this adapter does not manufacture that permission.

Artifact verification compares every tracked regular file against the committed
Git blob without filters and derives result hashes from committed binary blobs.
Unsupported symlink/submodule outputs and tracked files above 64 MB fail closed;
individual committed blobs are subject to the bounded verifier output limit.
This prevents clean filters from hiding bytes absent from CI/review. The collector
rejects outstanding change requests by any reviewer and rechecks PR head/base
identity after collecting proof. Accepted historical records remain immutable;
they describe the accepted commit, not later PR or deployment state.

Cleanup failure after acceptance remains eligible for recovery from blocked
storage, using the same exact result and accepted bundle without model dispatch.
