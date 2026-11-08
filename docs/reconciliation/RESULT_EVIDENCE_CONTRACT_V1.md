# Result evidence contract v1

`herdr-durable-result-v1` is a projection of the existing host-owned task
snapshot. It is not a result store, scheduler, retry authority, budget
authority, or completion gate.

## Authority map

| Boundary | Existing authority | Contract role |
| --- | --- | --- |
| Attempt identity | `agent-task-worker.prepare_attempt` and durable task row | Supplies `attempt_id`, `run_token`, `fencing_token`, `idempotency_key`, and the host-issued ownership epoch. |
| Result candidate | `herdr_submit_result` bound to the attempt-owned inode | Supplies bounded status/evidence/summary only. It cannot mark completion. |
| Root/child completion | `agent_completion_evidence.verify_completion` and existing #85 evidence store | Supplies trusted completion evidence and verification state. |
| Durable transition | Existing worker/scheduler transition code | Remains the only writer of task state. |
| Read-only consumer | `herdr.reconciliation.reconcile_task` | Validates the envelope and classifies; it never writes, retries, or accepts work. |

## Canonical fields

The envelope contains `schema`, `version`, exact `identity`, `result`,
`provenance`, `authority`, and `recovery` objects. Identity is copied only
from the authoritative task row; `attempts` is never treated as `attempt_id`.
The ownership epoch must be the host-issued object bound to the same run and
fence. Missing repository, issue, consumer, epoch, or lineage is a publication
error, not a guessed default.

`authority.verification_state` is descriptive (`candidate`, `verified`,
`unverified`, or `terminal_unknown`). The envelope itself never creates
completion authority. Reconciliation still requires the durable snapshot's
completion authority and exact identity match.

## Status and recovery rules

New root, child, blocked, failed, recovered, and control publications use the
same envelope. `terminal_unknown` is explicit and cannot be represented as a
completed result. Delivery uncertainty remains `RECOVERY_REQUIRED` and always
has `safe_to_retry=false`. Human gates and stale external state remain
classifications only; they do not mutate durable state.

## Compatibility boundary

Existing unversioned result records remain readable for the legacy adapter, but
new publications are canonicalized by the host worker. Historical backfill,
queue migration, recovery replay, provider calls, and physical staging E2E are
outside this slice.

