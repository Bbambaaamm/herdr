# QuantLab host grant — explicit operator approval proposal

**State: PROPOSED / NOT ISSUED / NOT DEPLOYED.** Parent authority, root publication and exact independent review are separate mandatory gates. Owner: [Herdr #248](https://github.com/Bbambaaamm/herdr/issues/248). This is not a credentials file or a ready-to-write `SecurityGrant` JSON.

## Target identity and scope

| Field | Proposed value / acceptance |
| --- | --- |
| Consumer | `github:Bbambaaamm/Autonomous-Quant-Lab` |
| Consumer declaration | `/etc/herdr/consumers/quantlab.yaml`, `quantlab-paper`, `paper_only`, `no_live_broker_authority` |
| Trusted host policy | root-owned `/etc/herdr/host-policy.json`, presently **no QuantLab template** |
| Host UID | `1001` (`agentops`), fixed by active host policy; publisher must be privileged |
| Approved workspace | `/home/agentops/workspaces/quantlab` only |
| Result submission root | `/home/agentops/.local/state/agent-stack/tasks/results` only, exact identity-bound result slot |
| Allowed permissions | **only** `workspace-write` (no privilege escalation, no direct protected `main` write) |
| Tools | `read_file`, `search_files`, `patch`, `write_file`, `herdr_delegate_child`, `herdr_verify_work`, `herdr_submit_result` |
| Process policy | `enabled=false`, network=none, tools=none, credentials isolated from tools |
| Provider | `nous` only; exact route and credential references must be approved from trusted host profile, never extracted from existing model task |
| Executor | Hermès pinned version and SHA-256 validated against **trusted release inventory**, NOT merely syntactically well-formed. Observed prior pinned identity: `hermes:0.21.5:sha256:2e622affe56086408e159ec08c36fd8171d1181da3f4f5ba5259d1de160a9e34`; re-verify before approval |
| Model budget | `max_cost_microusd=0`, no automatic paid fallback; bounded context and execution time per parent, scheduler, and consumer limits |
| Grant lifetime | Proposed up to 24 hours for first canary (validator hard ceiling: 168 hours). `issued_at` and `expires_at` generated only by trusted publisher on approval |
| Parent-child relationship | Child permissions/tools/budget/fencing are subsets of current verified root grant; never copy an expired Herdr/Heating template as authority |
| Research/investment safety | PAPER-only. No live broker integration, live credentials, real orders, external finance side effects or automatic real-money trading |

## Required approvals and preflight evidence

1. **Trusted authority source:** Obtain a *current* approved parent/consumer grant ceiling from the existing host-security operator workflow. Both known on-host Heating/Herdr templates are expired (as of 2026-11-23); they are not acceptable source authorities. Verify independent owner approval of the specific QuantLab identity and requested tools/limits.
2. **Provenance:** Bind exact installed Herdr release, immutable code/runtime manifests, approved Hermes profile, pinned executor hash, current provider route and protected credential references, configuration owner/mode and stable filesystem reads. No agent- or issue-authored policy is trusted input.
3. **Offline review:** Run `validate_quantlab_template` against an operator-prepared candidate and `validate_policy_delta(current, proposed)` to prove **no unrelated host-policy or other consumer mutation**. These validators do not grant authorization. Include parent-subset, symlink/TOCTOU, expired-grant, stale-fencing, budget, missing-PAPER-gate and malformed-input negative tests in the implementation/review evidence.
4. **Independent review:** Require clean exact-head CI, independent P0/P1-free security review, confirmed rollback/backup, sufficient disk and recovery capacity, and explicit operator approval. Do not merge/deploy purely on test success.
5. **Privileged publication (separate approved action):** Back up current root-owned policy, verify source and candidate hashes, publish atomically with fixed ownership/mode and fsync, reread installed bytes, verify expected hash and refusal of out-of-scope requests, retain rollback receipt. **No command in this proposal performs publication**.
6. **Existing durable work:** Only after activation, reconcile the original `github-quantlab-issue-278-approval-7103063169` via the sanctioned Herdr recovery path; its last recorded execution stopped before agent/prompt delivery. Preserve task identity/fencing, and do not blind-requeue older uncertain attempts.
7. **E2E:** Observe one successful QuantLab Hermes task with durable result, independent review, CI, linked PR and successful next-cycle scheduling. Keep trading execution in QuantLab's own isolated PAPER-only service boundary.

## Known blockers

- Current host policy has no QuantLab grant; source templates are expired.
- `agentops` cannot perform unrestricted sudo; Desktop Commander `quantadmin` is connected, but its command API blocks sudo.
- Independent review of implementation PR #250 and operator root publication approval have not yet occurred.

**Disposition: DO NOT DEPLOY until all gates are independently evidenced.**
