# Host grant lifecycle — fail-closed expiry and operator renewal (proposal)

This is **one central Herdr control-plane component**, not a project-specific timer, new issuer, root authority, or second scheduler. Status: code review pending; **not installed/activated in production**.

## Detection: existing maintenance integration only

The *read-only* reporter `python -m herdr.grant_lifecycle` uses the canonical trusted, root-owned `/etc/herdr/host-policy.json` reader. It prints a redacted, deterministic JSON status for all configured consumers, not secrets, provider keys, complete grant bodies or untrusted issue text:

- exit `0`: every listed consumer is current beyond the 48-hour warning threshold
- exit `1`: one or more are within the warning threshold or expired — operator action required
- exit `2`: policy missing, malformed, untrusted or tampered — fail closed

An existing central Herdr maintenance/monitoring cycle may **later** call this read-only command once per cadence, de-duplicate by `(consumer, expiry, state)`, and open/update a single durable operator approval item. No new timer/worker or model budget is authorized by this PR. Detection MUST NOT call a grant issuer, change policy, requeue a task, restart Hermes or impersonate approval.

## Renewal: same-or-narrower proposal is not authorization

`validate_narrow_renewal(current, proposed, consumer)` is an offline comparison guard only. It requires exactly one existing consumer grant change, no host-wide or other-consumer change, bounded maximum lifetime (default 24h), stable workspace/process/runtime/credential/provider/tool rules/approval boundary, and non-expanding typed capability scope. A currently **expired** grant can only be used as a *ceiling for candidate comparison*, never as a live authority for a publisher or model call.

A separately approved privileged issuer must authenticate root operator approval and independent security review; verify the current parent chain and fixed release/profile/provider hash against trusted immutable evidence; choose fresh grant identity/fencing/expiry; acquire canonical locks; atomically back up and publish; validate reread and host launch; and preserve rollback. These components are outside this change. Auto-renewal is expressly **not** implemented, because extending a revoked or expired authority without fresh proof would bypass the trust boundary.

## Current live evidence, 2026-11-23

At audit, `github:Bbambaaamm/herdr` expired 2026-10-15 and `github:Bbambaaamm/heating` expired 2026-11-13; QuantLab is **not registered** in host templates. The reporter returned `action_required` (exit 1). Nothing was renewed, no reviewers started, and no task was replayed.

## Follow-on acceptance before declaring the incident permanently solved

1. Independent review and complete CI for this PR.
2. Wire the reporter into the existing central maintenance cycle, with bounded alert de-duplication, no additional scheduler, and tests for expired, absent, tampered, and multiple tenants.
3. Implement / verify a trusted privileged operator approval-publisher with exact hash, explicit fresh consent, atomic backup/rollback, bounded grant TTL, current parent authority, host path and immutable profile verification.
4. Prove an end-to-end canary: warning -> human/operator approval -> secure renewal -> exact run-bound launch -> expiry refusal; confirm unrelated projects are unchanged.

Until these gates pass: the system remains fail-closed and does not autonomously extend grants.
