# Five-consumer host grant activation — operator-only GO / NO-GO package

**Status: REVIEW CANDIDATE. NOT AN AUTHORITY. NOT A DEPLOYMENT SCRIPT.**

Target host: `quantlab-staging-01`. Central Herdr: `Bbambaaamm/herdr`. One trusted runtime, one existing scheduler/watchdog/dispatcher. NO second Hermes orchestrator, consumer-specific policy publisher, policy self-approval or bulk task requeue.

## Verified 2026-11-23 (time-dependent; always recheck)

- `/etc/herdr/host-policy.json`: root-owned regular file, schema **1**, host UID `1001`, SHA-256 `83cc8182a0042e26576459c26a1064de68394a97fa6d23998777eeaa472b74ba`.
- `/opt/herdr/current` resolves to `/opt/herdr/releases/v0.3.0-router-v5-p1d-rc6-8d8ad5037555`. This is **not** automatically the release containing review PR #250 or grant-lifecycle PR #251.
- Existing host grants: Herdr expired **2026-10-15**, Heating expired **2026-11-13**. No root grant for QuantLab, LOXXESS or Majak.
- Existing automated launch-plan issuer expects *schema 2* with explicit immutable runtime/publication binding. A schema-1 consumer JSON mutation is NOT equivalent to enabling that issuer. Never silently switch schema or inherit a stale issuer policy.
- The existing watchdog is active. Queue audit observed pending 0 / running 0 / blocked 194. The original QuantLab #278 task was blocked before agent and economic delivery, but must still be reconciled under canonical fencing prior to replay.

## Exact intended project identities

| Intake consumer | Canonical host consumer | Approved workspace (proposed) | Hard restrictions |
|---|---|---|---|
| herdr | `github:Bbambaaamm/herdr` | `/home/agentops/workspaces/herdr` | No direct main writes, no ruleset/CI bypass, no privilege escalation |
| quantlab | `github:Bbambaaamm/Autonomous-Quant-Lab` | `/home/agentops/workspaces/quantlab` | PAPER-only, no live broker authority or real orders |
| majak | `github:Bbambaaamm/dotacni-majak` | `/home/agentops/workspaces/dotacni-majak` | Preserve source lineage, no unverified eligibility claims |
| loxxess | `github:Bbambaaamm/loxxess-technical-ai-assistant` | `/home/agentops/workspaces/loxxess-technical-ai-assistant` | Data minimization and separately approved enterprise permissions |
| heating | `github:Bbambaaamm/heating` | `/home/agentops/workspaces/heating` | No physical control / unsafe actuation from development-agent authority |

These are mappings to review, **not permissions**. Project intake `enabled=true`, GitHub issue approval or a running Hermes process do NOT confer host authorization.

## Operator gate checklist (all required)

1. **Trust source:** identify the current root-owned, operator-authorized issuance/publication process and **fresh, signed or otherwise trust-anchored operator approval** for every listed consumer. Validate issuer policy, owner, expiry, revocation, role separation and exact source hashes. Existing expired grants can be comparison ceilings only, never authority for fresh grants.
2. **Release compatibility:** select a reviewed, immutable Herdr release, independent P0/P1-free review and exact-head CI for all included PRs, verify runtime manifests/executable fingerprint, schema 1/2 compatibility and rollback. Do not use unmerged branches as live code.
3. **Per-consumer scope:** explicit permitted tools, arguments, paths, provider and credential references, model budget, parent/child ceiling, fencing, worktree, result slot, network/process limits and temporary lifetime. Independent review-only authority should be strictly narrower than implementation and must never gain write/deploy rights. Do not assume a blanket one-size grant for all five consumers.
4. **Security isolation:** verified immutable executor, real host sandbox, closed network capability, credential isolation, signed/root-approved provider routes, disk/capacity and recovery gate, no live-trading/physical-action side effects. No paid model fallback without separate approval.
5. **Pre-publication comparison:** reviewed operator-authored candidate policy must pass fixed-root trusted reader, canonical schema validation, current-parent validation, exact intended change/delta review, negative tests (missing/stale grant, symlink, tampering, changed code/runtime, parent escalation, mismatched UID, budget, result slot, replay), and independent reviewer identity/provenance. A diff to a valid-looking JSON is never enough.
6. **Transactional publication (separate authorized action):** acquire existing canonical deployment/dispatcher/worker locks; stop/prevent new admissions as required by the *reviewed* cutover procedure; back up root policy and signed publication record; compare prechange SHA; publish atomically with root-owned permission/mode and fsync; reread exact bytes and verify runtime launches. On failure restore proven backup, leave task queue/fencing untouched, report NO-GO.
7. **Canary:** after the grant and release are independently verified, reconcile **one** pre-delivery task (QuantLab #278) using existing durable recovery, preserving task and fencing identity; observe a result, independent review, CI and next-cycle selection. Gradually release only evidence-cleared tasks per consumer. No blind requeue of 194 blocked items.
8. **Continuous operation:** connect only the read-only grant-status reporter from PR #251 to the existing maintenance/status bridge after reviewed release promotion. Alert 48 h before expiry; renewal allowed only inside an independently preapproved, current, bounded root authorization lease, never by self-extension or new scheduler.

## Operator read-only preflight commands (safe to run with `quantadmin` SSH)

```bash
id
hostname
readlink -f /opt/herdr/current
stat -c '%U:%G %a %n' /etc/herdr/host-policy.json
sha256sum /etc/herdr/host-policy.json
systemctl is-active agent-stack-watchdog.service
df -h /
python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
policy=json.loads(Path('/etc/herdr/host-policy.json').read_text())
now=datetime.now(timezone.utc)
print('host_policy_schema',policy.get('schema_version'))
for consumer, raw in sorted(policy['templates'].items()):
    deadline=datetime.fromisoformat(raw['expires_at'])
    print(consumer, 'current' if deadline>now else 'expired', deadline.isoformat())
PY
```

The preflight prints no secrets or credentials and performs no mutation. The observed policy hash is a **checkpoint**, not a permanent approval; re-evaluate the digest immediately before any future transaction.

## Explicit stop and rollback controls

- **NO-GO:** missing/expired trusted root issuance authority; unresolved independent review/CI; schema-1 vs schema-2 publication mismatch; missing valid source parent; signature/profile/hash mismatch; insufficient capacity; uncertain worker/reservation state; changed old SHA; changes to other consumers outside separately approved delta; any PAPER-only or physical-control permission breach.
- A *new* authorization for a previously absent consumer is **not a renewal**; do not call `validate_narrow_renewal` as a grant issuer or treat its PASS as authorization.
- Do not install a timer, add sudo exceptions, edit `/etc/herdr/*`, restart watchdog, merge draft PRs, publish a JSON grant, or move blocked tasks under this packet alone.

## Current decision

**NO-GO for grant publication and autonomous Hermes dispatch.** This packet is ready for independent review and a privileged operator to gather/approve the missing trust evidence, not for unattended execution. Completion requires a separately approved, tested publisher and explicit operator acceptance of the final exact-hash candidate.
