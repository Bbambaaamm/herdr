# QuantLab host-policy activation — controlled PR and rollout gate

Status: **DESIGN / BLOCKED — no host grant or deployment included**  
Owner: [Herdr #248](https://github.com/Bbambaaamm/herdr/issues/248)  
Related: [QuantLab #278](https://github.com/Bbambaaamm/Autonomous-Quant-Lab/issues/278), [Herdr #53](https://github.com/Bbambaaamm/herdr/issues/53), [Herdr #126](https://github.com/Bbambaaamm/herdr/issues/126)

## Verified starting point (2026-11-23)

- The GitHub intake registry enables `quantlab` in `all_open` mode, but the root-owned `/etc/herdr/host-policy.json` schema-1 authority contains only `github:Bbambaaamm/heating` and `github:Bbambaaamm/herdr` templates. Neither grant can authorize QuantLab.
- Both current template expiry timestamps are already past; do not simply extend or copy either grant.
- QuantLab consumer config at `/etc/herdr/consumers/quantlab.yaml` specifies `policy_profile: quantlab-paper`, `paper_only`, `no_live_broker_authority` and child permission subset. This declaration does not constitute executable host authority.
- The existing exact task `github-quantlab-issue-278-approval-7103063169` was blocked with `task_invocation_policy_unavailable`, attempts 0, `economic_delivery_attempted=false`, `agent_start_attempted=false`, `pane_split_started=false`. The task must be reconciled, not duplicated.
- `agentops` has no noninteractive sudo. The root-owned policy cannot be edited or activated from a child task.
- 2026-11-23 capacity sample: approximately 10 GiB available, but current capacity/recovery approval is a separate mandatory gate.

## Deliverable boundary

This design PR records the exact rollout and verification contract only. It deliberately contains **no guessed SecurityGrant**, no credential, no root config replacement and no deployment script that could bypass protected admission. A subsequent implementation PR must derive the exact permitted scope from the reviewed parent authority and the consumer's current policy, provide deterministic negative tests, and undergo independent review before release authorization.

## Follow-up implementation PR: required changes

1. Add an explicitly approved, bounded `github:Bbambaaamm/Autonomous-Quant-Lab` template through the existing host-authority publication mechanism, not via GitHub issue contents, model output, or agent-controlled configuration. Bind it to the approved repository and `/home/agentops/workspaces/quantlab` workspace with exact parent identity and minimum tools/permissions.
2. Maintain `paper_only`, `no_live_broker_authority`, approved filesystem roots, no direct write to protected `main`, no secret exfiltration, no paid provider activation, bounded grants and child-subset checks.
3. Validate trust of the config path, file owner/mode, schema, immutable code/runtime manifest hashes, profile snapshot and grant expiry. A stale parent or unapproved profile is **DENY**; there is no permissive fallback.
4. Prepare a canonical **root-operator** install artifact with base hash, proposed hash, explicit operator authorization, atomic replacement, backup, health check and rollback. Host authority must not be granted by an unprivileged Hermes process.
5. Do not combine consumer authority publication with an unreviewed release cutover or RC7 activation. Existing RC6 safety gates and recovery/backup gates remain binding.

## Required deterministic tests (all negative cases must fail closed)

| Case | Expected |
| --- | --- |
| QuantLab consumer absent from host templates | DENY before pane/agent/model invocation |
| Expired grant or credential approval | DENY |
| Incorrect consumer/repo/task/fencing/parent identity | DENY |
| Workspace escapes approved root or symlink changes during verification | DENY |
| Child requests more tools/permissions/budget than parent | DENY |
| Grant tries to expose live broker or non-PAPER execution | DENY |
| Tampered policy bytes, owner, mode, schema, manifest or signature | DENY |
| Policy changed between read and launch | DENY |
| Prior task has ambiguous delivery / unknown result | No blind requeue |
| Valid, time-bounded approved QuantLab grant | PREPARE succeeds, with immutable attestation and bounded result slot |

Tests must not perform network/model calls, create live orders, modify production policy or start a second scheduler. Attach exact-head CI, independent review and negative-case evidence to the implementation PR.

## Release and restart sequence (operator-owned)

1. **Preflight:** read current deployed release, root policy hash and all grant expiries; verify #126 capacity, backup/recovery readiness and active leases/worktrees. Capture rollback provenance. Do not overwrite dirty QuantLab working tree.
2. **Review gate:** exact-head CI green, independent review with zero P0/P1 blockers, accepted parent/consumer authority and explicit privileged operator approval. PR merge alone is not activation.
3. **Publish:** privileged operator atomically publishes the exact reviewed policy, with trusted ownership, fsync/replace and rollback snapshot. Do not mutate existing grants in place through the agent.
4. **Attest:** verify file identity, hashes, current expiry, sandbox/profile binding, allowed scopes and denial tests against the installed bytes. Keep PAPER-only enforcement.
5. **Reconcile:** inspect the original QuantLab #278 task ID, run token, fencing and retained result. Only if previous delivery was provably absent, follow the documented **same-task** recovery route; no automatic independent economic attempt.
6. **E2E acceptance:** observe one actually completed Hermes task with immutable result, tests, review, CI and linked draft PR. Then verify Herdr chooses the next dependency-safe task without duplicate scheduling.
7. **Rollback:** on unexpected result, revert via the verified privileged rollback artifact and mark task/consumer blocked; retain durable evidence. Never weaken admission to achieve a green status.

## Acceptance checklist

- [ ] Actual reviewed QuantLab root grant contract and parent authority chosen
- [ ] Implementation PR with complete negative tests
- [ ] Exact-head CI and independent review PASS
- [ ] Operator-authorized root publication and hash evidence
- [ ] Fresh capacity/recovery gates satisfied
- [ ] Original #278 task safely reconciled, with one proven Hermes run
- [ ] Next-cycle continuation and PAPER-only verified

Until all boxes are evidenced: **NOT READY FOR DEPLOYMENT / NO AUTONOMOUS CODING CLAIM**.
