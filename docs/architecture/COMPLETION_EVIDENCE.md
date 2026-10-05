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
Unsupported symlink/submodule outputs and tracked files above 2 MB fail closed;
individual committed blobs are subject to the bounded verifier output limit.
This prevents clean filters from hiding bytes absent from CI/review. The collector
rejects outstanding change requests by any reviewer and rechecks PR head/base
identity after collecting proof. Accepted historical records remain immutable;
they describe the accepted commit, not later PR or deployment state.

Cleanup failure after acceptance remains eligible for recovery from blocked
storage, using the same exact result and accepted bundle without model dispatch.


### Store upgrades
The unique acceptance lookup scans pre-upgrade artifact/result-derived addresses
before new publication. Matching legacy records are bound to the protected
attempt and frozen plan, compared with the incoming claim and atomically indexed
at the new address without deleting originals. Conflicting old records require
trusted reconciliation; a rewritten claim cannot create a second accepted
outcome. Release upgrades must quiesce prior writers before enabling the new
addressing contract.

Missing immutable worker fields or a missing predispatch plan are permanent
rejections. Only late CI/review proof and temporarily unavailable host/provider
evidence can wait. Metadata and changed blobs have an explicit 2 MB bound;
exceeding it requires replanning rather than automatic verification polling.
Reviews and unresolved threads are refreshed after resolving clean-comment
commit candidates, before the final PR identity check.

### Mutable final gates and recovery
Required check runs and their workflow origin are recollected after resolving review candidates, alongside effective reviews and unresolved threads. A newly pending or failing rerun cannot reuse an older green snapshot. The Git verifier additionally uses a host-generated libseccomp filter to deny socket/network I/O and io_uring, including pathname-based AF_UNIX connections that a read-only mount alone would permit. A verifier timeout is temporary evidence unavailability; bounded output overflow remains a permanent rejection.

Unique-address reads also compare every matching legacy record, even if the new address already exists. This prevents an intermediate upgrade from hiding contradictory historical outcomes. Original records remain retained.

The worker retains an exact completed publication when pane cleanup fails after acceptance or verification waiting. Recovery recognizes both worker and watchdog cleanup markers and retries cleanup/verification on the same identity. Permanent rejection is exported as its actionable verification reason.

Temporary predispatch plan failures reschedule the same unexecuted attempt with its identity intact. They do not consume another model delivery. Invalid policy/specification failures remain blocked. The currently configured coding/report policy applies to Herdr; other enabled consumers retain explicitly labelled legacy_unverified_result completion until their own trusted policies are configured. Their prior behavior is not silently relabelled as verified.

EvidenceBundle v2 includes the exact sealed launch policy. A fresh coding/research/review acceptance reopens the protected process and checks process start ticks, all code/runtime mount inodes and read-only descendants, exact invocation environment, namespace/network assurance and the signed grant before and after GitHub evidence collection. A sandbox_verified flag alone is insufficient. The grant is verified at the protected launch timestamp for historical completion only; live call authorization continues to enforce current expiry. Once an immutable exact bundle has been accepted, restart may replay it after pane/workspace cleanup without recollection, execution or budget reset. Current task/parent identity must still match. Legacy records lacking this proof remain historical and require trusted replan; they are never relabeled as newly verified.

## Durable children use the same semantic acceptance boundary

A completed status and self-authored evidence hash do not authorize DONE.
New admitted child records use completion_contract_version=2. A host-created
ChildCompletionAuthority freezes the existing #85 plan before prompt delivery.
The prompt carries exact ArtifactRef identity, base, checks and report criteria.
The real runtime persists physical namespace/sealed-grant proof before Hermes
starts; fresh completion uses shared accept_artifact and exact host CI/review.
Model-supplied producer labels, sandbox flags and completion receipts are ignored.

An accepted child receipt binds full parent/task/run/fence identity, protected
specification, plan/policy, the complete result payload and immutable host bundle.
It is persisted in the existing scheduler audit before releasing the lease or
dependent work. Replay validates every binding; altered result JSON cannot reuse
an accepted receipt. Late result reconciliation has an in-process host authority
port and keeps the same attempt. Missing authority/check/review is quarantine,
never a second prompt or a false DONE.

Pinned worktree path/device/inode are verified around fresh collection. Accepted
bundle replay survives workspace cleanup. Old self-claimed historical completions
remain visibly legacy_unverified_result and cannot satisfy implementation
dependencies or the parent's verified child-completion barrier. This records
historical facts without promoting them to current semantic proof.

Host composition supplies authority objects through runtime/delegation/bridge
ports or the protected host module port; task/model/environment fields cannot
select them. #78 owns live joint embedding/activation, and #86/#87 own bounded
work phases and repair budgets. Unit lifecycle tests use explicit host-port
doubles; separate child evidence tests retain real Git/artifact validation and
exercise the shared physical gate. Actual bwrap confinement remains covered by
the physical launch suite. No production configuration or deployment is changed.


## Frozen scope and ScopeSelfCheck

A host-approved coding completion_contract can supply a closed scope policy:
finite file/subtree descriptors, acceptance identifiers and shared-contract
identifiers. The worker freezes this policy before dispatch and includes it in
the immutable specification/plan binding. Existing historical plans keep their
original meaning; configuring a new scope does not relabel an old acceptance.

A required scope_self_check binds the exact spec/result digest and covers the
physical ArtifactRef.changed_files set exactly once. Each group links to
declared acceptance and carries a bounded justification. Follow-up work stays
explicitly outside this result. Invalid paths, unknown criteria, missing files,
overlapping groups and extra authority fields deny before CI collection.
BLOCK/unexpected effects and REPLAN_REQUIRED/unrelated changes have distinct
permanent reason codes. Shared-contract mutations require a revised host plan;
this report cannot update the ownership registry or refresh stale evidence.

The accepted bundle retains a bounded immutable report and its digest.
Publication/restart compare that exact report; mutation during evidence
collection rejects publication. Symbol/resource descriptions and explanations
remain worker assertions: the required independent review of the exact artifact
continues to judge their meaning. File/JSON size bounds protect parsing and are
not quality heuristics. Large in-scope changes are not rejected by line count.

## Actual child host composition

The standalone agent-durable-bridge constructs ChildCompletionAuthority from
the authenticated current parent factory and its protected frozen child policy.
Protected cold recovery reconstructs that same source port from the exact
canonical parent and immutable policy; neither path depends on a module-global
test injection. Missing policy keeps completion pending and does not dispatch
another model attempt.

Before root dispatch, a protected child_completion_contracts object declares
version 1, a full base_sha, and at most 128 children indexed by exact child
specification SHA256. Each entry has kind coding/research/review and criteria.
Coding criteria use the closed scope policy (files, acceptance_ids and
shared_contract_keys); research/review use their declared report schema.
Objective, role, tools, permissions, exact worktree identity and ownership all
contribute to the child specification digest. A role name or model request
cannot select a more convenient acceptance kind or manufacture this policy.
#86 can produce these descriptors from its host-approved WorkPlan.

The host freezes the parent attempt/specification, workspace root, actual CI
workflow blob/application identity and bounded baseline observations. Restart
reuses those exact observations rather than recollecting a changed baseline.
The canonical source reader rejects symlinks, hardlinks, writable/public task
files, duplicate JSON fields, changed inodes and duplicate current attempts.
These are source requirements, not permission fields exposed in the socket.

Bridge responses preserve the original candidate handoff and separately expose
accepted_handoff. The latter derives from the protected accepted bundle and
full child receipt only after cleanup and actual namespace exit. Its Git-base
reference binds the full commit; base_sha256 is SHA256 of the canonical
{"git_commit": "<full base SHA>"} reference. Source/specification/shared-contract
changes deny the projection. Verified worker completion still has a distinct
parent_synthesis_and_integration next action and does not assert integration,
deployment or factual certainty outside the frozen artifact criteria.


## Reviewed specification, closed result submission and rejected attempts

A fresh independent review must target a commit containing exactly one canonical
Herdr-Verification-Binding footer. Its closed version-1 object carries the frozen
five-field attempt identity, spec_hash, policy_hash and base_sha. The host reads
the immutable commit metadata through GitHub and compares the whole canonical
object with the frozen plan. A green old PR at the same base cannot be rebound
to another task, run, fence, objective or policy by changing an ArtifactRef label.
The collector also rereads the selected bot comment before acceptance; deletion,
editing or a newer decision keeps the same attempt pending. Review is an
independent artifact gate, not a guarantee of truth beyond the frozen criteria.

The existing herdr_submit_result interface remains status/evidence/summary.
Coding/research/review candidates use exactly one evidence object
{"herdr_completion":{"version":1,"artifact":<ArtifactRef>,"pr_number":<number>}}.
A required scope_self_check belongs inside that object. Root callers also
declare the exact isolated artifact_workspace; an admitted child never chooses
its workspace, which the host derives from the pinned worktree. Control cycles
use {"herdr_control":{"version":1,"next_action":<text>}} and a nonempty summary.
These objects are claims. They do not assert CI, review, scope, acceptance or
integration authority. Child receipts bind the original complete SDK payload,
not the host's decoded copy. Historical flat host transport remains readable.

Scope policy version 2 maps every shared_contract_key to an exact path and
base_sha256. The host checks the committed baseline and the actual ArtifactRef
diff. An omitted shared-contract confession cannot conceal a change. Any such
change invalidates the existing plan and dependent evidence; version-1 nonempty
shared keys without a trusted mapping also require replan. Every frozen
acceptance ID must appear in the aggregate change-group linkage.

Missing/unavailable evidence remains pending on the same attempt. Permanent
child rejection instead persists a full-identity needs_replan receipt, blocks
the child and clears its claim/lease. The original candidate remains immutable;
no accepted semantic receipt or completed dependency is manufactured. Physical
namespace exit and exact cleanup still gate parent terminalization. Root worker
and cold watchdog recovery close the exact owned session after a permanent
rejection; failed cleanup remains quarantined and retries cleanup without an
implementation redispatch. A lost retained physical invocation is permanent,
whereas a temporary observation/transport failure can remain pending.

## Acceptance history without a lifetime limit

The host-private .acceptance-index holds bounded per-attempt immutable intents.
An accepted bundle's exact proof is fsynced there before its original flat alias
is published. A crash between those steps recovers that same proof and alias
without repeating validators or accepting a different candidate. Flat bundles
and legacy aliases remain intact; conflicting outcomes fail closed.

Migration from the older flat layout uses durable Linux directory cookies
bound to the source directory identity and metadata. Each pass processes at most
512 entries, 8 MiB plus one bounded record, and one second between record
operations. Incomplete migration raises EvidenceUnavailable for the same attempt.
Participating publishers finish migration before changing the source directory.
Restart resumes the checkpoint; a changed source restarts the scan conservatively.
Old writers must first be quiesced by the existing ownership/epoch upgrade
barrier. This index is host evidence storage, not another task queue.

Completed migration makes lookup depend only on this attempt's intent and flat
proof. New publication and replay therefore have no global 10,000-result cutoff.
Index directories, locks, checkpoints and intents reject unsafe permissions,
foreign ownership, symlinks, extra hardlinks and invalid bindings. The existing
worker write-boundary protection covers the index with the rest of the store.
Artifact verification separately limits tracked file count, aggregate bytes
and elapsed checks; a per-file size limit alone is insufficient.

### Corrupt records and irrecoverable child pins

Authenticated parents without a frozen child-completion catalogue still use the existing durable delegation path. Preparation/instructions and accepted-handoff projection are conditional on a host completion authority. A completed candidate without that authority becomes a durable blocked/replan result; it cannot manufacture verified DONE. Reconciliation reuses the original claim and rejection.

A vanished, redirected, replaced or inaccessible admitted child worktree is a permanent evidence failure; transient device/resource I/O remains unavailable. Pin validation traverses each path component through no-follow directory descriptors. Already accepted immutable evidence retains its existing replay after cleanup.

Flat plan/accepted readers open nonblocking, then require a current-host-owned private regular single-link file with bounded size and stable descriptor/named-inode metadata. A FIFO cannot block a legacy-index writer. Exclusive publication uses Linux no-replace atomic rename after temporary-file fsync, avoiding a temporary two-link interval. Unsupported atomic publication fails closed. A directory-fsync interruption can still finish on exact replay without changing the immutable payload.
