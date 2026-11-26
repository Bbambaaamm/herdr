# ChatGPT → GitHub → Herdr intake: authenticated rehearsal

Date: 2026-11-25. Scope: proposed work intake, **not live execution**.

## Evidence

- Public proposal: https://github.com/Bbambaaamm/herdr/issues/260
- Target: read-only `inspect` of pull request
  https://github.com/Bbambaaamm/herdr/pull/259
- Immutable canonical request SHA-256:
  `39730cd25aedc094a29b8f39e968f1601c89fa9a604b9a66e3d210a0568eba39`
- Exact live authenticated read using the source-only
  `agent-github-intake --inspect-proposal Bbambaaamm/herdr 260`:
  - `status=PROPOSED_ONLY`
  - `execution_authorized=false`
  - `task_created=false`
  - GitHub issue revision SHA-256:
    `5c2ec6363662901c26da890978c6157c540515b2394a1ffa3a1262208f98ea26`
- The proposal issue had **zero approval comments** during the check.
- No root #53 approval was posted.
- No queue publication, Hermes worker, deploy, policy change, service
  restart, merge or production API activation was performed.

## Validation

- Local sandboxed tests cover deterministic proposal creation, authenticated
  proposal verification, canonical selected-root approval, rejection of
  forged/missing/stale selection, optional root durable admission transaction,
  state corruption, crash-window fail-closed behavior, duplicate proposals,
  active or unknown existing root episode denial, and legacy root compatibility.
- These tests do not prove live host admission or working model inference.
- Independent GitHub security review was requested on PRs #255–#259.
  Formal GitHub APPROVED, exact-head fully green CI, protected merge,
  verified release and host-authorized rollout are still separate gates.

## Next live acceptance requirements

1. Review every stacked PR at its exact HEAD; fix all actionable P0/P1/P2.
2. Obtain one independent APPROVED review after the final push, and all
   protected branch required checks before each merge.
3. Merge in dependency order #255, #256, #257, #258, #259, refreshing
   stacked base checks as each preceding PR merges.
4. Verify signed/immutable release and separately approved host deployment.
5. Verify healthy model/tool inference, actual trusted owner/fencing state,
   supervisor incident resolution and capacity at the execution time.
6. Obtain authenticated human maintainer approval for proposal #260 and a
   separate selected root #53 approval. Use the current GitHub revisions,
   not the ones snapshotted in this historical evidence note.
7. An **authorized** host-owned entrypoint must invoke the existing
   durable admission with the proven proposal binding. The source-only
   helper is deliberately not such an entrypoint.
8. Read and reconcile task/attempt state from durable evidence. Only then
   can a safe real Hermes execution and result be claimed.
