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

## Single source of monitoring truth for all connected projects (Q3)

`fleet_report(trusted_policy, intake_inventory)` overlays read-only intake registration onto the central, root-owned host-policy expiry report. It reports each enabled/disabled project as `current`, `expiring`, `expired`, or `missing`, and identifies existing grants with no matching intake consumer. **Intake metadata is never an authorization source:** an `enabled` project without an actual grant is `missing`, never `current`. Never include credentials or full grant material in the status output. Only use a trusted fixed-path loader to read live host grants; treat intake configuration as untrusted display metadata.

For CI or deterministic offline analysis, use the bundled intake JSON as an *observed* inventory:

```python
import json
from pathlib import Path
from herdr.grant_lifecycle import fleet_report
from herdr.host_configuration import HOST_POLICY_CONFIG, _read_configuration
intake = json.loads(Path("agent-stack/config/github-intake-consumers.json").read_text())
print(json.dumps(fleet_report(_read_configuration(HOST_POLICY_CONFIG), intake), sort_keys=True))
```

Once independently approved, wire only this read-only report into the *existing* `hermes-maintenance` path, deduplicate change events by consumer+expiry+status, and publish telemetry through the existing status bridge. Keep a single publisher and no new scheduler, issuer, agent run or queue.

## Preapproved renewal design (Q2): bounded lease, not perpetual self-authorization

A feasible future automated renewal protocol uses a **separately signed, root-owned operator authorization lease** created explicitly in advance, covering a specific consumer, immutable parent authority hash, precise scope/profile/provider/credential ceiling, fixed release/executor hash, validity window, maximum extension count and absolute expiration. The renewal worker may request a new shorter child/consumer grant *only while the operator authorization lease itself remains valid*. It must never bootstrap an expired or missing parent and may never rewrite its own lease. Issuer decisions must be bound to the current lock, runtime, policy SHA and fencing token, audited and idempotent per renewal key. On expiry, revoked approval, changed hash, excess budget, unavailable root authority or uncertain state, stop and notify the operator.

The **read-only** `assess_renewal_eligibility(...)` distinguishes `no_renewal_due`, `candidate_requires_active_preapproval`, `expired_requires_fresh_operator_authority`, and `missing_authority`. It is deliberately **not** a cryptographic verifier or issuer. `validate_narrow_renewal` checks one same-or-narrower proposal, not its signer. Both checks can be integrated into the existing trusted root publisher only after separate design review and signature/revocation/lock/rollback tests. This PR neither creates the signed lease nor configures an unattended grant renewal. A perpetual renewal chain without periodic fresh operator trust evidence is not permitted.
