# Cumulative work budgets (#87)

The host admits one stable consumer/work/lineage allocation. Task names, sessions,
providers and requeue locations cannot select a new allocation. Parent and child
ceilings are reserved together under the existing AuditLog's serialized extension;
queue transitions, leases and result reconciliation stay in the existing runtime.
There is no additional scheduler, router ledger or paid-provider activation.

New standalone work envelopes carry work_budget_version=1. A root-only envelope
uses child_work_budget_version=1; the frozen child catalogue version 3 explicitly
marks its coding entries with work contract and budget versions. Historical
catalogue versions 1/2 and envelopes without the new marker keep their meaning.
Unknown, Boolean or orphan budget markers fail admission.

## Admission and economic effects

Protected work definitions include a closed budget object with version,
allocation, ancestors and model_quotes, optionally a repair policy. The exact
allocation hash is frozen into WorkPlan.budget_reference. The host selects the
private audit directory from the approved lineage, outside worker-writable roots.
Cold recovery reads the original admission and allocation; it cannot replan,
increase counters or restore consumed capacity. BudgetLimits defaults to three
implementation attempts total, including the first; another total requires an
explicit versioned consumer policy and authorization reference.

Baseline, work verification, independent check adapters and local commit hygiene
reserve finite time before execution. Every check includes its declared timeout
plus 13 seconds for namespace startup and exit. Parallel child reservations
consume ancestor time/model/token/cost ceilings and concurrency before effects.
The implementation attempt begins once the baseline has been accepted.

The installed Hermes primary text middleware reserves a model call after final
request middleware, before the physical callback. Its quote binds exact provider,
model, API mode, endpoint, bounded request bytes, output tokens, token/cost ceiling
and wall deadline. The basic profile supports chat_completions text payloads,
one non-streamed output and SDK client max_retries=0. Unknown price is unavailable,
rather than zero; an explicitly approved zero-price quote still charges time,
tokens and model calls. Quotes must fit the signed grant's provider/context/cost
scope. Unsupported streaming, multimodal, auxiliary and internally retrying
routes block before dispatch.

The host socket checks the physical peer, original grant and mounts around budget
messages. A returned SDK callback proves delivery, but is not trusted billing or
token metering: those measurements remain explicitly UNKNOWN and their quoted
ceilings stay charged. A timeout or exception retains the original inflight
reservation. New session/request names cannot replace an uncertain operation.
No stronger-model or provider fallback is inferred from transport failure.

## Evidence, repair and alternatives

Implementation, baseline, flaky, provider, tool, dependency, policy and transport
failures have separate typed evidence. Output fingerprints contain hashes and
reason codes; model content, secrets and exception text are not audit authority.

Only a protected repair policy can reopen failed work. It binds approved output
fingerprints, reason, finite existing owned paths and a small changed-line ceiling
(maximum eight files / 200 changed lines). A new failed checker receipt and host
permit open the next implementation attempt. An unchanged tree or reused failure
cannot authorize another implementation call. UNKNOWN verification stays tied
to the original request. Scope, environment, oracle, grant and plan do not widen.

A host-approved flaky rerun is allowed once on the same tree. A changed result
records instability and does not by itself authorize PASS. Tool alternatives
must satisfy the same approved contract; at most one is permitted and parent
tool-fallback ceilings aggregate across children. Dependency alternatives are
once and workspace local. Provider fallback additionally needs original settled,
proven pre-delivery failure; uncertainty permits reconciliation only. These typed
adapter ports do not activate an unsupported transport or experimental executor.

## Stops, series and audit

Stop events bind task/executor/provider/consumer scope, source, reason and resume
condition. New economic work is denied while original reconciliation/settlement
remains available. Resume verifies current host approval/grant and remaining
capacity without resetting attempts. Exhaustion preserves artifacts and evidence;
it does not reset the worktree or cause a managed-device/domain side effect.

Variants, trials, statistical repetitions, candidate executions/depth/revisions,
implementation retries, provider/tool fallbacks and delivery reconciliation have
separate counters. All economic work still uses the same ancestor ceilings.
Explicit host series/search adapters reserve finite slots before dispatch;
candidate slots do not consume implementation retry allowance. EXPERIMENT and
live SearchEpisode execution remain closed until their separately owned approved
adapters exist. Historical work-budget-1 allocation hashes omit newly added
counter defaults; work-budget-2 includes them. Original serialized allocation
values remain immutable in the audit.

The hot projection advances only after durable append. An external audit change
invalidates it and requires chain-checked cold replay. Cold replay is finite
(8 MiB / 8192 events / bounded event size and elapsed parsing), nofollow and
host-owned; exceeding that profile blocks instead of accepting partial history.
There is no unlimited-history or automatic compaction claim.

## Evidence boundary and handoff

Tests cover actual host catalogue admission, physical baseline/oracle/Git
hygiene, Unix peer budget messages, cold recovery, finite repair, parallel parent
ceilings, typed alternatives, stops, series/counters and historical meaning.
The installed SDK probe observes real middleware reservation, timeout/UNKNOWN
retention and retry suppression using an explicit host admission/transport
fixture; its callback is local and free. These seams are independently tested.
They are not a whole deployed root/kernel/provider end-to-end acceptance claim.
Joint production activation/E2E remains separately owned; no live configuration,
provider spend, deployment or physical device change belongs to this delivery.

A new reservation and its physical start must fit the remaining elapsed ceiling;
a delayed start rechecks that bound. The guarded SDK also verifies that the
existing signed grant covers the quoted callback deadline plus delivery margin.
A failed lifetime check authorizes no model callback and does not pretend the
pre-effect reservation was consumed at zero or release it as a new operation.

The protected baseline/verification and hygiene reservations include the complete 120-second host-phase allowance introduced by #86. Full host elapsed measurements are not inferred from the subprocess proof duration: the time ceiling remains held explicitly as UNKNOWN. The generic historical checker keeps its original quote/measurement semantics when no new host-overhead profile is supplied.
