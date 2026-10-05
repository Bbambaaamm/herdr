# Prompt Runtime

`herdr.prompt_runtime` composes accepted Skills #72, Context Compiler #73 and
invocation grants #76 into an immutable execution input. It adds no provider
client, queue, authorization writer or final completion authority. The host
freezes the prompt alongside the work contract; the resulting output is a
candidate for the shared #85 evidence gate.

## Identity and reconstruction

`PromptPlan` binds the complete invocation identity, spec/policy hashes, base
revision, exact grant, context versions, instructions, examples, compute policy,
output schema and evidence requirement. Serialized plans reconstruct without a
provider conversation or private chain of thought. Nested mutable caller data
cannot rewrite the frozen plan. Replay rejects unknown fields and changed
contract digests.

Provider switches use explicitly pinned alternative ContextPlans. Their
task/control, policy, base revision, scope and experiment bindings must have the
same authority hash. Executor-specific skill selection and rendering may differ.
The renderer and tokenizer must match the actual versioned registry executor and
granted provider. A new task/control input invalidates the old prompt.

## Authority and data

The static prefix preserves host policy, consumer policy, project background,
selected skills and the output contract. The dynamic section carries the exact
task binding, immediate work, current context and optional examples. The
precedence is host → consumer → task → context.

Repository instructions, project conventions, approved skill resources and
demonstrations are explicitly marked `context_data`. Loaded repository text can
recommend work but cannot activate a tool, change grants or bypass consumer
bans. Runtime invocation still passes through the independent #76 guard.
Additional skill resources must match an actual selected #72 resource digest.

Source policy and provider data-class checks happen before loading. Source
bytes, length and digest must match the frozen reference. Holdout material is
never a project instruction or demonstration, including in evaluator sessions.
Host-known and recognizable credentials are redacted before model input;
reference metadata and output schemas carrying secrets are rejected.

## Demonstrations and context pressure

`DemonstrationSelector` considers at most 256 candidates and selects 0–5
examples. Selection uses exact project/task-class/conditions, actual host
evidence, relevance and diverse categories/source digests. An example remains
advisory data. Rejection reasons survive into the bounded trace.

The final rendered prompt is measured with the selected host tokenizer against
the smallest plan/grant/capability limit. Optional examples can be omitted with
an explicit budget reason. Required instructions and the task/output contract
cannot be silently truncated; insufficient space blocks execution.

## Structured output and evidence

Output schemas use a bounded Draft 2020-12 subset: closed objects, finite arrays
and strings, bounded alternatives, and no references or executable regexes.
The provider adapter receives a `structured_output` request envelope. Native
mode requires both a renderer capability and the registry's structured-output
feature. Otherwise the host selects an explicitly allowed validated fallback
or blocks. Both paths run the same host schema and exact-identity validation.

The output includes its invocation identity, PromptPlan hash, result,
evidence references, reason code and one of:

- `VERIFIED_CANDIDATE`
- `PROVISIONAL`
- `INSUFFICIENT_EVIDENCE`
- `UNKNOWN`
- `BLOCKED`

Verified candidates require the declared minimum of distinct references verified
by the host against this exact plan. Self-reported confidence, invented evidence
and a model's `DONE` claim do not satisfy this contract. Validated outputs retain
both canonical result bytes and the original response digest. Their acceptance
is always `requires_shared_85_acceptance`.

## Measurement and integration

The trace contains plan/context/renderer/source hashes, selected/rejected
reasons, prompt bytes, tokenizer counts, example count and schema mode. It
contains no loaded source text or model result. Cache and provider usage remain
`UNKNOWN` until actual adapter observations arrive; tokenizer estimates do not
claim provider token or cache billing.

#74 compares frozen prompt/context/example variants using its ordinary budgeted
trials and protected acceptance results. #97/#79 supply the exact compute policy
reference; #86 freezes prompt and evidence requirements with the work contract.
#95 reconstructs execution from those references. Integration and live acceptance
remain subject to #78 and the core chain; this contract does not automatically
activate a runtime, provider, paid service or production configuration.
