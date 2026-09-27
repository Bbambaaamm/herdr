# Prompt stall recovery and durable result reconciliation

## Incident

On 2026-09-26 the #3/#231 two-child live canary exposed a mismatch between Herdr terminal lifecycle observation and Agent Stack durable completion.

The canary itself succeeded. The durable swarm snapshot contained:

- parent `quantlab-hermes`;
- two distinct Hermes child agents;
- two parent edges;
- fencing tokens 1/2/3;
- both children `done`;
- parent `done`;
- `paper_only=true`.

The audit event log also contains submit, external-parent dispatch, two `subtask_spawned`, two child dispatches, two child completions and parent completion.

## Failure mode

The outer worker invokes:

```text
herdr agent prompt <agent> <prompt> --wait --timeout ...
```

Herdr requires a prompt sent from a settled state to produce an observed `working` or `blocked` state within five seconds. If it does not, Herdr returns `agent_prompt_stalled`.

Per the installed Herdr control contract, this error does **not** prove that the prompt was not delivered.
The Agent Stack worker currently treats a missing durable result after a grace period as retryable. On retry it:

- archives any previous result;
- allocates a new `run_token`;
- may choose a different model tier solely because attempt count increased;
- resubmits the full prompt.

This can duplicate economic work when delivery was successful but lifecycle observation or result publication was incomplete.

## Evidence from the canary

A successful canary snapshot was written at approximately 2026-09-26 22:35 UTC while the durable task later remained pending because no task result JSON matching the worker's current `run_token` was published.

Later retries included `agent_prompt_stalled` with agent state `done` or `idle`. The retry counter then caused the cost router to select a premium Sol executor even though the underlying problem was transport/result reconciliation, not task capability.

## Root causes

1. Terminal lifecycle observation is being used as a proxy for task delivery.
2. The worker depends on the model to write its own authoritative completion record.
3. Result publication is not transactionally bound to the dispatch attempt.
4. A retry creates a new token before proving the previous attempt is terminal.
5. Retry count is overloaded as a capability-escalation signal.
6. Existing side-effect evidence is not reconciled before redispatch.
7. Parent coordinator identity can change as a side effect of retry routing.

## Required behavior

`agent_prompt_stalled` MUST transition the attempt to `delivery_uncertain`, not directly to a new execution attempt.
Reconciliation order:

1. Check for an exact durable result for the same task/attempt.
2. Check Herdr durable execution/audit evidence for the same idempotency key.
3. Inspect whether the target agent is still working/blocked/settled without resubmitting.
4. Check task-specific side-effect evidence (snapshot, artifact, commit, PR, test record).
5. If completion can be proven, synthesize/commit the result from trusted runtime evidence.
6. If execution is still active, continue waiting under the same attempt.
7. Only if non-execution can be proven may a fresh attempt/token be allocated.
8. If delivery remains unknowable beyond the reconciliation deadline, fail closed for operator/recovery policy instead of blind replay of non-idempotent work.

## Proposed attempt contract

Each execution attempt should persist before submission:

```json
{
  "task_id": "...",
  "attempt_id": 4,
  "run_token": "...",
  "idempotency_key": "sha256(task_id + graph_hash + semantic_attempt)",
  "fencing_token": 17,
  "executor": "quantlab-hermes",
  "state": "dispatching"
}
```

Transport acknowledgement changes state to `accepted`; observed work changes it to `working`. Neither step creates a new semantic attempt.

Completion should be written by the trusted wrapper/runtime after validating executor output/evidence. Models may provide result content, but correctness cannot depend on the model remembering to create the queue's authoritative JSON file.

## Router change

Separate `execution_attempt` from `delivery_reconcile_count`.

Only capability/provider failure may contribute to model-tier escalation. `agent_prompt_stalled`, missing UI transition and result-file publication failure must not spend a premium attempt.
## Minimum implementation slice

- add durable attempt state with `dispatching/accepted/working/delivery_uncertain/result_ready/done`;
- keep the same attempt identity during delivery reconciliation;
- add a trusted result-commit helper in the worker/runtime;
- reconcile known canary evidence before any redispatch;
- classify retry reasons independently from capability escalation;
- keep `quantlab-hermes` as the root parent for the orchestration run;
- move Sol/Astra/Codex selection to bounded child/node execution;
- expose delivery uncertainty and reconciliation in telemetry;
- add tests for fast completion that skips observable `working`;
- add tests where prompt delivery succeeds but model does not write result JSON;
- add tests proving no duplicate child spawn after stalled acknowledgement;
- add tests proving no premium escalation on transport uncertainty.

## Acceptance

- [ ] successful two-child canary is recognized as completed from durable evidence;
- [ ] `agent_prompt_stalled` alone never proves non-delivery;
- [ ] one semantic attempt cannot create two economically equivalent executions;
- [ ] retry does not rotate `run_token` until the prior attempt is terminally reconciled;
- [ ] missing model-written result JSON can be safely completed by trusted runtime evidence;
- [ ] transport/result-contract failure does not escalate to Sol/Astra;
- [ ] parent Hermes identity remains stable;
- [ ] stale fencing token/result cannot commit;
- [ ] crash/restart resumes reconciliation without blind replay;
- [ ] telemetry explains dispatch, uncertainty, reconciliation and final result.

## Relationship to roadmap

This remediation is a prerequisite for finishing #3 live child lifecycle and for #9 end-to-end dogfood. It should land before admission-control integration is considered production-ready because admission cannot prevent duplicate work caused by ambiguous redispatch.


## 2026-09-27 durable parent session-isolation incident

Issue #190 exposed a second, independent failure mode: the long-lived coordinator chat itself
can contain unrelated task history. While the #190 worker was active and correctly routed to
`quantlab-hermes`, `herdr agent read quantlab-hermes` showed the pane reasoning about unrelated
Herdr issues #3/#8. Earlier history also interleaved #190 and Machine City #235 prompts.

A worker lock serializes Agent Stack workers, but it cannot prevent other control paths or operator
steers from writing to the same persistent coordinator chat. Therefore **serialization alone is not
session isolation**.

The persistent coordinator is now treated as control-plane identity only. Every new semantic durable
attempt must:

1. resolve the persistent coordinator and its pane;
2. split a new task-owned pane;
3. start a fresh Hermes process in that pane;
4. bind it to an opaque named Hermes session derived from `task_id + run_token`;
5. send the durable task prompt only to that task-scoped agent;
6. keep the task pane alive through delivery reconciliation for that attempt;
7. close only the task-owned pane when the worker reaches a terminal/requeue decision.

The worker MUST fail closed if the isolated task session cannot be created. It MUST NOT silently fall
back to prompting the persistent coordinator chat.

Pane cleanup is also fail closed: a pane ID equal to the persistent coordinator pane is never closed,
cleanup failures are recorded without masking the durable task state, and a new semantic attempt is
blocked until its prior task-owned pane has been closed successfully.

The session name is attempt-scoped: reconciliation of the same semantic attempt preserves the same
identity, while a genuinely new attempt receives a new run token and therefore a new session. This
keeps orchestration identity stable without sharing model conversation state between unrelated tasks.

## Watchdog recovery boundary

The watchdog is a safety net, not a second executor.

- A file left in `tasks/running/` is considered orphaned only when its matching
  `agent-task-worker` process is absent and its execution age exceeds
  `timeout_seconds + 300s`.
- A matching durable result may be terminalized into `done/blocked/failed`.
- Dispatcher stamps `dispatch_claimed_at` before entering `running/`, so an
  old attempt timestamp cannot make a freshly claimed task look orphaned.
- Immediately before any orphan mutation, the watchdog re-checks both the worker
  process and exact durable result to close startup/publication races.
- Without a matching result, the task is moved to `blocked` with
  `orphaned_running_unknown_delivery`; it is never blindly requeued.
- Watchdog-generated recovery evidence is always written to a sidecar result;
  the canonical task result path remains exclusively owned by the executor/runtime.
- A stale/mismatched canonical result is preserved and never overwritten.
- Codex self-update prompts are treated as transport/UI stalls. For Codex panes
  only, the watchdog detects the active three-choice update menu and sends
  `Esc` to skip it. It never installs an update automatically.
- Escape is sent only when Herdr reports a Codex agent as both `idle` and
  `interactive_ready`, and the active menu has no later work/readiness markers.
- A passive update banner, historical menu, or menu text quoted by live work is
  not treated as a blocking dialog.

These rules preserve PAPER-only/runtime/resource guardrails and avoid duplicate
work while allowing the primary dispatcher to remain authoritative.
