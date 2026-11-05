# Hermes-first control plane

## Decision

Hermes is the persistent cognitive parent/orchestrator. Herdr is the deterministic execution and policy control plane. Consumer GitHub repositories remain the authority for CI, review, merge and domain-specific safety.

The root orchestration identity MUST NOT be replaced by a model-tier retry. A premium model may execute or advise on a bounded child node, but it does not become the control-plane parent.

## Responsibilities

| Layer | Owns | Must not own |
| --- | --- | --- |
| GitHub / consumer policy | authorized work, CI, review, merge, domain invariants | live agent scheduling |
| Hermes parent | decomposition, planning intent, replan, synthesis, delegation decisions | leases, fencing, permission escalation |
| Herdr | TaskGraph validation, admission, leases, fencing, lifecycle, spawn/kill, recovery | product/domain judgment |
| Model router | node-level executor/model choice under budget/capability policy | parent identity or authority |
| Child agents | bounded research/code/test/review work | uncontrolled spawning or merge authority |
| Machine City | durable-state observability | execution or merge authority |

## End-to-end flow

```text
authorized consumer Issue
        ↓
persistent Hermes parent
        ↓ proposes
deterministic TaskGraph
        ↓ validates
Herdr policy + admission
        ↓
dependency scheduler
        ↓
node-level model/executor router
   ┌────┼───────────────┐
   ↓    ↓               ↓
Hermes  Codex       specialist
child   coding       reviewer/tool
   └────┼───────────────┘
        ↓
artifact + evidence handoff
        ↓
independent validation
        ↓
consumer CI/review/verified gate
        ↓
merge authority outside Herdr
```

## Parent identity invariant

For one orchestration run, `parent_agent_id` is stable from accepted ingress until terminal completion/cancellation. Retry policy may change a child executor or model, but MUST NOT silently replace the parent coordinator.

Current anti-pattern to remove:

```text
attempt 0: quantlab-hermes
attempt N: quantlab-sol   ← parent identity changed because retries accumulated
```

Target:

```text
parent: quantlab-hermes (stable)
child/node executor: free → Sol → Astra or Codex, if policy allows
```
## Planning and delegation

Hermes may propose decomposition and child-requested subtasks. Herdr is the sole authority that mutates the durable graph after validating:

- parent-child permission subset;
- consumer safety hook;
- DAG node/depth/fanout caps;
- global/repo/issue concurrency;
- cost/time/resource budget;
- filesystem/network/tool scope;
- deterministic dependency semantics.

A child may request more work, but cannot directly spawn an unmanaged process. The request becomes a proposal that Herdr either admits or denies with an audited reason.

## Model and executor routing

Routing happens per TaskGraph node after admission, not by replacing the root coordinator. Each decision records task class, role, model/executor, reason, budget, fallback reason and attempt class.

Recommended executor classes:

- Hermes child: research, planning, synthesis, bounded tool workflows;
- Codex child: isolated coding/refactor/test implementation;
- premium reasoning child: architecture/hard-debug/judge when capability floor requires it;
- deterministic tool worker: schema checks, tests, formatters, artifact verification.

Retries are typed. Transport/lifecycle failures do not increase reasoning capability tier. Provider/capability failures may trigger a compatible model fallback within node policy.

## Durable orchestration state

The authoritative runtime state is Herdr's append-only event stream plus materialized TaskGraph state. Terminal panes are execution transports, not the source of truth.

Every dispatch uses a stable `task_id`, an `attempt_id`, a fencing token and an idempotency key. Results bind to all four plus the graph/spec hash and base SHA where applicable.
## Command/result handshake

Required state machine:

```text
queued
 → dispatching
 → accepted
 → working
 → result_ready
 → verifying
 → done
```

Ambiguous delivery enters `delivery_uncertain`; it is not equivalent to failed execution.

The dispatcher MUST separate:

1. submission accepted by terminal transport;
2. observed agent activity;
3. durable result publication;
4. result verification/commit.

A missing UI state transition cannot prove that step 1 failed.

## Retry taxonomy

- `transport_uncertain`: reconcile only; same attempt/idempotency key; no model escalation;
- `provider_failure`: bounded compatible model fallback may occur;
- `capability_failure`: replan or capability-tier escalation may occur;
- `policy_denied`: no retry until policy/input changes;
- `execution_failed`: bounded retry with a new fencing token;
- `result_contract_failed`: recover from execution evidence before rerunning side effects.

A new `run_token`/attempt must be allocated only after the previous attempt is terminally reconciled.

## Consumer boundary

QuantLab PAPER-only, Maják provenance/UNKNOWN semantics, Heating actuation policy and future consumers remain external policy overlays. Hermes may reason about them; Herdr enforces their declared policy hooks.
## Required telemetry

Machine City and audit export must show:

- stable parent identity;
- child/task hierarchy and dependency edges;
- executor/model selected per node and why;
- attempt/idempotency/fencing identity;
- accepted/working/result timestamps;
- retries grouped by failure class;
- policy/admission denials;
- tokens, cost, latency and fallback;
- artifact/review/CI state;
- durable state after restart.

## Implementation sequence

1. Fix dispatch/result handshake and `agent_prompt_stalled` reconciliation.
2. Pin Hermes as stable root coordinator; move cost/capability routing to node executors.
3. Integrate #8 admission before every real child process creation.
4. Finish #3 live child lifecycle with durable result publication.
5. Add isolated workspaces (#4) and reviewer/redispatch (#5).
6. Unify telemetry (#6), then expose true hierarchy in Machine City (#7).
7. Exercise restart/crash/blocked-review/dependency failures and 24h soak in #9.

## Definition of Done

- root parent identity never changes because of retry count;
- two independent real children can run concurrently under one Hermes parent;
- every child has `parent_agent_id`, `parent_task_id`, lease and fencing token;
- no child exceeds parent or consumer policy;
- ambiguous prompt delivery cannot create duplicate economic work;
- provider/capability routing is node-level and auditable;
- restart reconstructs the same authoritative graph and attempts;
- Machine City reflects durable state, not terminal heuristics;
- consumer CI/review/merge authority remains unchanged.


## Physical invocation boundary

Root and managed-child launches require the host-only policy factory and same-inode sealing described in [Host invocation policy launch](INVOCATION_POLICY_LAUNCH.md). Physical evidence is verified before Hermes starts. Missing host authorization is a policy blocker; a model-visible schema, pane status or task field cannot supply it.

Managed root and child results use the granted herdr_submit_result Hermes tool. Its signed rule binds one precreated private regular inode to the complete invocation identity and idempotency key before the policy bundle is sealed. The tool accepts bounded status, evidence and summary, supplies identity and digest itself, checks the same inode under a lock and fsyncs it. General file-tool roots remain the workspace. Identical submission replays are idempotent; a different result cannot overwrite the retained candidate. Submission never grants semantic acceptance or final DONE; shared #85 remains required.

A child's versioned pre-split ownership intent is durable before admission/policy resource preparation. Native split intent precedes the call; an invoked/legacy unknown split remains quarantined. A root session retains its full launch identity before policy proof publication and a one-use prompt intent. Typed native agent absence permits pre-prompt cleanup only with the same marker, current sandbox PID and physically retained grant/attestation. Result replay uses fsynced scheduler evidence even when the mutable source result is corrupted; cleanup failure preserves candidate evidence while withholding the parent gate.

Nested child delegation is rejected before provisioning until a child-bound transport is available through #95. Root delegation retains its authenticated bridge.

Managed child claims persist the seven-component launch identity, idempotency key and deterministic pane marker in the same fsynced claim event. Runtime entry confirms that intent before CLI preparation, policy provisioning or pane creation. Replay distinguishes a versioned never-split intent from an ambiguous split/native-start observation; only the former permits absence-based cleanup without inventing native quiescence. Nested child delegation is denied before policy provisioning until a child-bound bridge is available.
