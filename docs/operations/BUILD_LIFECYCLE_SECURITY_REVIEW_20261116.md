# Herdr #126 — security review of PR #227 and PR #228

**Review date:** 2026-11-16. **Reviewer status: internal technical self-review,
NOT independent security approval.** Scope: the exact phase-1 and phase-2
read-only build lifecycle implementation and synthetic negative tests.
No cleanup execution, root-owned issuer setup, production host configuration,
Docker changes or provider calls were performed.

## Findings and dispositions

| Severity | Finding | Fix / present behavior | Acceptance |
| --- | --- | --- | --- |
| P1 hardening | Phase-1 nested directory changed during `scandir` could appear as complete bounded walk | Compare pinned directory `fstat` identity at both ends and explicitly mark `stable_snapshot_verified=false` | Targeted race test PASS; still not an atomic snapshot |
| P1 hardening | Phase-2 full `/proc` PID list and per-process FD names were materialized before applying max-pid/max-fd bounds | Streaming `os.scandir` with bounded observation and `UNKNOWN` for incomplete scans | Negative bound/no-`listdir` tests PASS |
| P1 hardening | Ambiguous mountinfo and escaped mount paths could be misclassified, and `mountinfo` had no explicit maximum read size | Bounded 2 MiB byte read; require valid ` - ` separator; decode octal path escaping; malformed => `UNKNOWN` | Escaped path/invalid/oversize tests PASS |
| P1 hardening | Signed root-owned JSON parser accepted duplicate object keys, potentially causing ambiguity between implementations | Strict duplicate-key rejection, including nested objects | Duplicate-key negative test PASS |
| P0 **release blocker** | No approved root-owned receipt signer, trust anchor or accepted host runtime for build evidence | Both PRs remain read-only; all missing root proofs => `BLOCKED_REVIEW`; no cleanup credentials issued | **NOT ACCEPTED** |
| P0 **release blocker** | No complete host-wide process, mount namespace, live TaskGraph lease/fence and durable parent ACK revalidation at cleanup time | Scanner reports scoped/unknown visibility and never grants deletion | **NOT ACCEPTED** |
| P0 **release blocker** | No safe FD-relative cleanup executor, independently approved exact build identity or signed deletion plan | No delete/move API present in these PRs; no cleanup attempted | **NOT ACCEPTED** |
| P0 **release blocker** | Independent external security reviewer has not accepted both exact PR heads | Draft PRs; require separate reviewer and new exact-head CI/security approval | **PENDING** |

The P0 items are **missing prerequisites**, not evidence of an exploitable
deletion path in this read-only code. They must not be described as fixed.
No direct cleanup authorization bypass was identified in the reviewed
read-only API; this is not a full penetration test.

## Evidence and remaining threats

- Complete selected regression at reviewed source: **146 PASS** across
  build inventory, Ed25519 host-evidence observer, TaskGraph, WorkCycle,
  Capacity Watcher, ownership/release and durable evidence tests.
- Existing `scripts/validate_repo.py` must pass and canonical source
  manifest must be regenerated on each exact head.
- `measurement_complete=true` means only that bounded traversal did not
  hit a recorded uncertainty; it **cannot** prove no concurrent file
  modification or different mount namespace. The explicit
  `stable_snapshot_verified=false` prohibits such an interpretation.
- The host-evidence receipt is historical. Neither an authentic Ed25519
  signature nor a released lease string proves the lease remains
  released now. The caller must never upgrade this data to an authorization.
- PID open-fd enumeration can race and may not see root-only processes,
  PID namespaces, path aliases or file descriptors held by different
  actors. Any missing visibility is not negative evidence.
- Mountinfo is only this process's namespace, not all namespaces.
- Root-owned public key and envelope files are read via existing protected
  no-follow logic. Test-only signer material must never be published.
- A complete cleanup security review still needs revalidation of pinned
  directory FDs and ancestor identity, mount topology, active execution
  epochs, task fencing, durable parent ACK, artifact preservation,
  safe recursive deletion and crash/replay on an independently approved
  non-production test root.

**Decision:** Phase-1/2 patches are suitable for continued offline review.
Cleanup, root-owned policy changes, runtime activation and autonomous model
execution remain **NO-GO**. Independent review still pending.
