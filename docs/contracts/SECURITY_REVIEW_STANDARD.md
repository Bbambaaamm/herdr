# Herdr Security Review and Acceptance Standard (2026-11-25)

Status: proposed project-wide engineering contract. This file does **not** grant
release, merge, supervisor, host-policy or sandbox authority.

## 1. One authority per fact

- Every authorization/ownership decision MUST identify the existing canonical
  issuer and must consume verified facts from it, not reverse-engineer them
  from logs or duplicate a state machine in a watchdog, router or UI.
- Durable child terminality is defined by
  `agent_durable_children.all_children_terminal` / scheduler replay and
  canonical parent-attempt binding. Owner guard can **observe**, not redefine.
- A guarded observation is `ACTIVE`, `TERMINAL` or `UNKNOWN`.
  `UNKNOWN` is a no-start result. Never promote incomplete evidence to
  success by searching text, ignoring journal order, guessing identity or
  swallowing validation exceptions.
- Verification MUST be read-only: no task, checkpoint, policy, lease, fence,
  controller, release or supervisor state changes during observation.

## 2. Threat model before implementation

For every security-sensitive PR, record affected trust boundary, authority
owner, allowed I/O, attacker-controlled inputs, failure behavior, replay/
recovery invariants, concurrency/TOCTOU assumptions and resource budgets.
Explicitly identify separate consumers that must continue on one consumer's
failure. No new fallback model, paid provider or extra worker without approval.

## 3. Required tests

1. Positive canonical fixtures created by the REAL existing issuer, plus
   negative mutations of those same records. Do not handcraft permissive
   synthetic logs as proof of terminality.
2. Differential tests: owner guard's result MUST agree with the canonical
   scheduler's result on terminal, active and uncertain/error states.
3. Identity and provenance: task/run/fence/repo/consumer/generation, signed
   or canonical binding where supported; mutation, replay and out-of-order
   event cases.
4. Pre-delivery failed-with-cleanup, failed-without-cleanup, regular child
   result with/without cleanup, active orphan and stale ledger.
5. Missing, truncated, symlinked, FIFO, oversized, malformed and concurrently
   modified evidence; no indefinite lock waits or unbounded resources.
6. Guard-module initialization failure and consumer isolation; preserve
   healthy unrelated agents without a second execution.
7. All changed-area tests, relevant E2E and complete repository CI, canonical
   source manifest, no forbidden generated artifacts.

## 4. Review discipline

- Freeze a narrow task contract and acceptance matrix before code changes.
- Review the entire changed trust boundary (including dependencies), not just
  lines changed to fix the last comment.
- Every independent finding must state exact HEAD, invariant, reproduction and
  severity. Triage: confirmed regression, already covered, or separate
  non-blocking follow-up (with issue link). Never resolve a confirmed defect
  by suppressing a test or weakening fail-closed behavior.
- Fix all confirmed in-scope findings, re-run contract suite, then request
  exactly one fresh independent exact-head review. Repeat only on a new
  actionable counterexample, not on unchanged code without new evidence.
- CI PASS and an AI COMMENTED review are **not** GitHub APPROVED or release
  authorization. Protected-branch approval and owner-controlled deployment
  remain separate gates.

## 5. Evidence and deployment

For each reviewed HEAD attach test commands/results, changed-files and manifest
check, remaining known limitations, independent reviewer finding disposition,
required GitHub check conclusions and the actual PR URL. No merge until the
actual protected-branch requirements are met. No production activation until
root controller preflight, capacity gate, immutable archive validation,
rollback proof and explicit authorization pass.

## 6. Anti-regression ownership

Contract suites must guard against reintroducing duplicate lifecycle parsers
in owner guard, false terminal states, lost orphan child claims, unsafe guard
imports and non-Herdr consumer starvation. A new lifecycle state requires
updating the canonical scheduler and its differential test first, then any
observer. If this standard needs changing, use a separate documented review.

## 7. Read-only ownership observation (mandatory)

- Watchdog observation MUST consume a single bounded immutable scheduler
  journal snapshot. Validating a path and reopening it later is prohibited.
- Observation MUST NOT invoke mutating reconciliation, create registry
  directories, create lock files, change reservations or write any proof.
  Reconciliation remains exclusively with the host recovery authority.
- A registry-backed observation MUST use non-mutating verification and bounded
  shared locks. Any held lock, unbound reservation, changed identity, invalid
  path, hostile file or authority error returns UNKNOWN; do not wait forever.
- An outer process deadline MUST bound the entire inventory, not just each
  file or lock. A timeout blocks Herdr start and permits later consumers to
  continue. Explicit tests must demonstrate this contract.
- Never equate green tests with approval. Exact-head independent review and
  protected-branch authorization remain mandatory.

## 8. Closed transitive read-only audit and release evidence

Every read-only observer review MUST trace transitive authority callbacks, not
merely the top-level function: owner_guard -> bounded subprocess -> bounded
snapshot -> scheduler replay -> ReadOnlyOwnershipRegistry ->
(ReadOnlyLegacyOwnershipInventory, HostOwnershipRelease, namespace_exited)
-> terminality.

- ReadOnlyOwnershipRegistry.reconcile_claim accepts exactly matching previously
  claimed or released identity, including a validated immutable tombstone.
  It never binds an absent identity or changes a state.
- ReadOnlyLegacyOwnershipInventory must use the EXISTING worker.lock inode
  without creation, fsync or recovery; absent/contended/invalid lock means
  UNKNOWN, never silent permission. Nested released-claim checks must also use
  the read-only registry, never instantiate the writer.
- HostOwnershipRelease is an evidence-only verifier in this call graph.
  Future changes to it or any transitive callback MUST undergo a transitive
  write/lock audit before merging.
- Tests MUST cover claimed, released and compacted tombstones, missing legacy
  worker lock, no file creation, altered identity, lock contention and FIFO
  swaps.
- A whole-suite timing-sensitive failure outside the changed trust boundary
  is triaged with exact test, repeated isolated reproductions, changed-file
  correlation and logs. Do not label it flaky from one success; do not skip it.

## 9. PR review loop closure

1. Before review generate a complete trust-boundary dependency map and
   invariant-by-fixture matrix.
2. Preserve every confirmed finding as a negative regression test plus a
   positive valid-state test.
3. Batch fixes by authority boundary rather than replying to individual
   comments with one-off conditions.
4. Require local contract suites, full CI and canonical manifest on exact HEAD.
5. Request one exact-head independent review after CI green, triaging findings
   as confirmed-and-fixed, refuted-with-evidence or new independent bug.
6. AI COMMENTED is never GitHub APPROVED. Branch protection, host authority,
   deployment and supervisor activation are separate gates.
