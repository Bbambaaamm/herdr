# Capacity events · #100 offline integration

| Requirement | Existing component | Decision | Dependency |
| --- | --- | --- | --- |
| Watcher source and snapshot | `deploy/herdr/check_capacity.py`, `operation_readiness.read_capacity_report` | Reuse the installed path, publisher ownership and descriptor checks | Existing five-minute timer |
| Provenance | `operation_readiness.read_protected`, scoped Ed25519 grants in `security.py`, draft host evidence #228 | Reuse protected root-owned reads for a typed receipt. Scoped grants and historical build receipts have different bindings | Reviewed host issuer for live receipts |
| Host-owned attestation | `herdr/capacity_attestor.py`, `operation_readiness.read_protected` | Reuse the protected reads; independently measure the filesystem and pin device/inode/mount | Host identity, freshness policy |
| Normalize and correlate | Operational incidents and adapters in #229 | Reuse contract, capacity validation, state and histories | Exact #229 base |
| Event and proposal | #100 EventEnvelope/TaskProposal specification, #183 acceptance | Supply minimal compatible capacity-only data contracts. No event dispatcher | Authenticated receipt, exact policy |
| Replay and partial writes | Existing `EvidenceStore` atomic immutable records | Add a capacity-observation record type keyed by server, scope and event second | Caller-owned protected store and complete replay scope |
| Build and workload context | #227/#228, `taskgraph`, `scheduler`, `work_cycle`, `telemetry` | Carry bounded diagnostic evidence. Workload state and ACK remain outside this diagnostic's authority | Existing operator and host admission paths |
| Effect authority | `security.py`, `admission.py`, scheduler and budgets | Leave untouched. Proposal is a data-only object | Separate future approval |

Audit baseline: main `b8685da9222c73b5293becf0996b3ff3e291d122`. Draft #229 is open at `1d2a5717f448b266ca3083bb8a77a043729ca4fa` with successful exact-head CI. Build lifecycle #227/#228 remain drafts. #100 is the architecture owner, #183 acceptance, #126 capacity, #53 existing control and #184 future canary. Repository search found no previously implemented EventEnvelope or TaskProposal for this slice.

Staging reports RC6, inactive Herdr and an active timer with a five-minute interval. Its capacity report is a regular UID 1001, mode 0644 file in an agentops-owned directory. The watcher UID proves which account can publish there. It does not authenticate an event on behalf of the host. No root receipt was present at the reserved input path. No host trust or production release configuration is installed by this PR.

## Host attestation

The v1 receipt bound host, scope, time and a report digest. It established that root published bytes, while permitting an issuer to copy publisher-supplied capacity and policy without measuring either. The reader also accepted receipts up to the general 15-minute observation limit. v1 did not identify the measured filesystem or method, constrain the receipt to the installed threshold, or provide an issuer with a protected publication path.

The reader expects the root-owned v2 receipt at `/run/herdr/capacity-exporter/receipt.json`. Its exact schema fields bind the server, scope, event second, report digest, method, filesystem and the exact `available_bytes`/`required_bytes` counters. That receipt binding is unchanged.

The reader no longer trusts the receipt alone. `capacity_attestor.verify` independently measures the filesystem and binds the measurement to the report: `O_NOFOLLOW | O_DIRECTORY`, two identity snapshots, and a device/inode/mount pin selected by the host policy. The independent measurement must equal the report counters exactly; no drift or slack tolerance exists, and an unpinned measurement must be the host root filesystem. Publisher identity stays with the existing protected read, which accepts only an owner-0 ancestry and a publisher-1001 regular file. `HOST_OWNED` requires root execution on the policy host, a receipt binding the report digest and counters, and an independent measurement that agrees exactly. A forged measurement, a foreign filesystem, a namespace-local mount point, an unpinned non-root measurement, a symlink, an inode race, a stale report, an expired receipt or a report replaced between reads all fail closed; without a receipt trust stays `PUBLISHER_OBSERVED`, `canary` reports `BLOCKED_PENDING_TRUST_ACCEPTANCE` with no proposal, and `record_host_observation` refuses durable publication.

`canary` is a read-only observation. `record_host_observation` and `replay_recorded` are explicit offline entry points. Their caller must supply a host-protected evidence directory outside worker-writable roots. Replay fails closed beyond 1,024 capacity records or 8,192 directory entries. A reviewed retention and archival policy is required before continuous operation. The attestor adds no scheduler, signing infrastructure, budget ledger or authorization surface.
