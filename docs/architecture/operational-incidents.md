# Operational incidents · P0 offline slice

| Requirement | Existing component | Decision | Owner | Dependency |
| --- | --- | --- | --- | --- |
| Event and human steering | #100, GitHub intake and #53 | Report typed evidence upstream; proposals stay inert | #100 / #53 | Existing admission, budget, scheduler |
| Capacity | operation_readiness.capacity and the capacity watcher | Reuse values and verify the same publisher's snapshot | #126 | Host publisher; no new timer |
| Build lifecycle | PRs #227/#228, draft | Consume bounded projections; cleanup always blocked | #126 | Independent status, live host receipt |
| Backup | Existing offsite evidence and #126 | Consume redacted pinned reports; no OAuth or transport client | #126 | Verified exporter, independent restore |
| CI | Existing GitHub intake and exact-head workflow metadata | Pin approved inputs and HEAD; no merge signal | #183 | Verified CI exporter |
| Worker recovery | taskgraph, scheduler, work_cycle, reconciliation | Observe lease and fence; use read-only reconciliation on uncertain delivery | #53 | Bound snapshots and durable parent ACK |
| Cost and model routing | telemetry, routing, fallback_recovery | Keep as authority boundary; no integration that reserves or calls | #53 | No cost or routing effects |
| Evidence | evidence canonical hashing and existing host EvidenceStore | Reuse deterministic hashes; optional atomic export via same store | #183 | Protected evidence root and replay inputs |

Base `b8685da9222c73b5293becf0996b3ff3e291d122`. PR #225 is draft and context only. Build lifecycle modules are absent on the examined main and available in draft #227 at `79a1d8d` and #228 at `12e53c1`. Staging read-only observation reported ext4 at 97%, about 2.79 GiB available, Herdr inactive, capacity watcher active and RC6 link unchanged. The watcher file is regular, UID 1001, mode 0644. That publisher is not a root attestation.

## Input boundary

This slice runs offline. A trusted caller supplies exact SHA-256 pins from the already verified upstream exporter or host evidence. A hash from the same untrusted input is not a trust anchor. The current slice does not implement a new signature authority or automatically bind to a live GitHub, TaskGraph or backup exporter. If authenticated input is unavailable, report UNKNOWN or reject the batch. Existing upstream checks remain responsible for signature, freshness and trusted-origin verification. Nobody should derive, install or run a task from its report alone.

The incident ID binds scope, source, subject, incident type and object revision. The correlation ID omits the revision; updated HEAD or fencing revisions remain distinct incidents in the same correlation group. Event identity includes source event time, fixed detail codes, state and evidence digests. Replays use the earliest supplied observation time for identical events and newer source time for current state. Distinct claims at the same source time fail closed. Published reports are content-addressed and never create tasks.
