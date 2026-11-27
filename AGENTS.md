# Agent instructions

## Home compute fleet (operator requirement)

Before planning or admitting workloads, consult the current home-worker inventory and evidence in [#95](https://github.com/Bbambaaamm/herdr/issues/95#issuecomment-7225748341), capacity safeguards #126 and root #53. Consider both home workers for eligible isolated tests, builds, analysis, temporary worktrees and artifacts; prefer them when current capacity, trusted executor, sandbox, grants and evidence gates permit. Record reasons for not using eligible capacity. Hetzner remains central orchestration and security authority. Do not introduce a second scheduler or competing implementation alongside Hermes.

SSH connectivity alone does not establish trusted remote execution. Require live capacity, scoped authorization, isolation, fencing/idempotency, credential protection, evidence verification and an isolated accepted canary before production dispatch. Never bypass host policy or release gates. Keep credentials outside Git. Existing project policies and acceptance gates remain in force.
