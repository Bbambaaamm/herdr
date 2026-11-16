# Capacity events · #100 offline integration

| Requirement | Existing component | Decision | Dependency |
| --- | --- | --- | --- |
| Watcher source and snapshot | `deploy/herdr/check_capacity.py`, `operation_readiness.read_capacity_report` | Reuse the installed path, publisher ownership and descriptor checks | Existing five-minute timer |
| Provenance | `operation_readiness.read_protected`, scoped Ed25519 grants in `security.py`, draft host evidence #228 | Reuse protected root-owned reads for a typed receipt. Scoped grants and historical build receipts have different bindings | Reviewed host issuer for live receipts |
| Normalize and correlate | Operational incidents and adapters in #229 | Reuse contract, capacity validation, state and histories | Exact #229 base |
| Event and proposal | #100 EventEnvelope/TaskProposal specification, #183 acceptance | Supply minimal compatible capacity-only data contracts. No event dispatcher | Authenticated receipt, exact policy |
| Replay and partial writes | Existing `EvidenceStore` atomic immutable records | Add a capacity-observation record type keyed by server, scope and event second | Caller-owned protected store and complete replay scope |
| Build and workload context | #227/#228, `taskgraph`, `scheduler`, `work_cycle`, `telemetry` | Carry bounded diagnostic evidence. Workload state and ACK remain outside this diagnostic's authority | Existing operator and host admission paths |
| Effect authority | `security.py`, `admission.py`, scheduler and budgets | Leave untouched. Proposal is a data-only object | Separate future approval |

Audit baseline: main `b8685da9222c73b5293becf0996b3ff3e291d122`. Draft #229 is open at `1d2a5717f448b266ca3083bb8a77a043729ca4fa` with successful exact-head CI. Build lifecycle #227/#228 remain drafts. #100 is the architecture owner, #183 acceptance, #126 capacity, #53 existing control and #184 future canary. Repository search found no previously implemented EventEnvelope or TaskProposal for this slice.

Staging reports RC6, inactive Herdr and an active timer with a five-minute interval. Its capacity report is a regular UID 1001, mode 0644 file in an agentops-owned directory. The watcher UID proves which account can publish there. It does not authenticate an event on behalf of the host. No root receipt was present at the reserved input path. No host trust or production release configuration is installed by this PR.

The reader expects a root-owned receipt at `/run/herdr/capacity-exporter/receipt.json`. The exact schema fields bind the server, consumer, project, event second and SHA-256 of the bytes read from the watcher. The issuer needs independent host verification of the measurement and scope before issuing the receipt. A digest copied from an account-writable report is insufficient.

`canary` is a read-only observation. `record_host_observation` and `replay_recorded` are explicit offline entry points. Their caller must supply a host-protected evidence directory outside worker-writable roots. Replay fails closed beyond 1,024 capacity records or 8,192 directory entries. A reviewed retention and archival policy is required before continuous operation.
