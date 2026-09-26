# Hermes-first orchestration implementation backlog

This backlog turns the architecture and #3 live-canary findings into bounded implementation slices.

## P0 — Durable dispatch/result handshake

Goal: remove blind redispatch after ambiguous prompt delivery.

Scope:
- persist attempt before submission with task_id, attempt_id, run_token, idempotency_key and fencing token;
- add attempt states dispatching, accepted, working, delivery_uncertain, result_ready, verifying, done;
- treat agent_prompt_stalled as delivery uncertainty;
- reconcile durable execution evidence before redispatch;
- keep the same semantic attempt/run token while reconciling;
- trusted wrapper commits authoritative result after validating evidence;
- do not depend on the model writing queue-authoritative JSON;
- test fast completion with no observable working transition;
- test successful execution with missing model result JSON;
- test restart during delivery_uncertain;
- prove no duplicate child spawn.

Acceptance:
- successful #3 two-child canary settles DONE without another economic execution;
- stalled observation alone cannot create a fresh semantic attempt;
- stale fencing/result cannot commit;
- recovery survives worker restart.

Dependency: #3. Blocks production completion of #3 and #9.
## P0 — Stable Hermes parent + node-level executor routing

Goal: keep Hermes as the persistent coordinator while models/executors vary only per bounded TaskGraph node.

Scope:
- pin root parent identity for an orchestration run;
- remove retry-count-based root-agent replacement;
- split execution_attempt from delivery_reconcile_count;
- route model/executor after node admission;
- allow free → Sol → Astra/Codex fallback only for typed provider/capability failures;
- record executor/model/reason/fallback/cost per node;
- preserve parent/child policy subset and consumer safety hooks;
- test transport uncertainty does not escalate model tier;
- test child executor can change while parent_agent_id remains stable.

Acceptance:
- parent_agent_id is unchanged from ingress to terminal state;
- Sol/Astra/Codex are child/node executors or advisors, never implicit root replacements;
- routing is auditable and bounded;
- consumer CI/review/merge authority is unchanged.

Dependency: P0 durable handshake, #3, #10.

## P1 — Admission before process creation

Goal: connect #8 admission decisions to the real #3 runtime path.

Scope:
- call admission before pane/process/agent creation;
- enforce global/repo/issue, DAG, host-pressure, permission and consumer-policy limits;
- pass an immutable admitted policy envelope into the child;
- audit denied spawn before any process side effect;
- cancellation revokes leases and prevents stale completion.
Acceptance:
- denied spawn creates no pane/process;
- allowed spawn carries the exact bounded policy;
- child cannot expand parent tools/permissions;
- PAPER-only and other consumer invariants remain unchanged.

Dependency: #8 and stable #3 runtime.

## P1 — Finish real child lifecycle

Goal: promote the successful canary pattern into the canonical scheduler runtime.

Scope:
- durable parent/child/task/edge records;
- heartbeat, lease expiry, fencing and reclaim;
- child completion published by trusted runtime;
- dependency-aware parallel dispatch;
- bounded dynamic subtask proposals;
- cleanup only runtime-owned panes;
- crash/restart integration test.

Acceptance:
- two real independent Hermes children run concurrently;
- lost worker can be reclaimed without double commit;
- no unmanaged pane remains;
- restart reconstructs parent/child state and leases.

Dependency: P0 handshake and #8 integration. Closes the core of #3.

## P2 — Reviewer, telemetry and Machine City truth

After #3/#8 are stable:
- #4 isolated coding workspaces and artifact handoff;
- #5 independent reviewer + bounded redispatch;
- #6 unified model/token/cost/latency/retry telemetry;
- #7 Machine City hierarchy from durable state only;
- #9 E2E dogfood, failure matrix, rollback and 24h soak.

## Ordering

```text
P0 handshake
   ↓
P0 stable Hermes parent + node routing
   ↓
P1 #8 admission integration
   ↓
P1 finish #3 real lifecycle
   ↓
#4 → #5 → #6 → #7
   ↓
#9 E2E + 24h soak
```
