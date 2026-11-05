# Task-local active reasoning state (#95)

## Implemented scope and consumer boundary

herdr.reasoning_state is a standalone, pure contract for a bounded current
Evidence/Conclusion projection. Its API uses the existing
security.InvocationIdentity and context.SourceRef / SourceState types.
It neither changes those interfaces nor imports the scheduler, WorkCycle,
evidence collector, provider SDK or a persistence implementation.

The public API consists of WorkingEvidenceEntry, ConclusionClaim,
OpenGap, ReasoningEvent, ReasoningProjection and materialize.
ReasoningEvent factories validate structured event data and retain immutable
canonical bytes. from_json accepts the closed version-1 event schema;
to_json returns a fresh JSON-compatible value.

There is no live consumer or execution-event-store adapter in this increment.
No ContextPlan or PromptPlan renderer, retrieval/KnowledgeNeed integration,
MemoryProposal integration, checkpoint compactor, hand provisioning, event
cursor service or crash-restart workflow is wired here. Replaying a supplied
complete event prefix is a deterministic source-level contract check; it is
not physical recovery or end-to-end acceptance of #95.

## Authority

The host must authenticate event origin, authorize and classify source refs,
and pin the accepted source state before constructing or persisting events.
A source digest binds bytes, not truth. A model may propose a delta, but a
syntactically valid event or SourceState.VERIFIED label supplied by a model
does not authenticate that proposal.

SUPPORTED means working support inside this projection. It is not trusted
completion, an accepted EvidenceBundle, a permission grant or long-term memory.
It cannot release dependencies, change task status, reset budget, authorize an
operation or reconcile uncertain delivery. Those decisions remain with the
existing Herdr TaskGraph, admission, grants, fencing, budget and #85 evidence
authorities. The module performs no I/O, model call or external side effect.

An optional host-owned expected_identity argument to materialize rejects a
different task/run/fence or other InvocationIdentity field. Without it, replay
checks consistency within the supplied history only. The host must separately
bind persistence/update admission to current WorkPlan identity and its exact
spec/base/policy/grant references; this standalone projection does not check
their freshness or replace WorkCycle's plan-hash replay guard.

## Invariants on construction and export

- Evidence, claim and gap IDs are unique in their respective namespaces.
  References use bounded non-path ASCII identifiers and reject known credential
  shapes. Statements, questions, reasons, identity and source metadata are also
  checked for known secret patterns. The host still owns redaction of secrets
  that cannot be recognized by these patterns.
- ACTIVE evidence has at least one exact SourceRef whose state is VERIFIED or
  UNVERIFIED. STALE, UNAVAILABLE and CONFLICT refs cannot be active.
- Every claim reference names existing ACTIVE evidence. SUPPORTED claims have
  nonempty support and every referenced SourceRef is VERIFIED. UNKNOWN claims
  may have no support; CONTESTED claims need nonempty support.
- SUPERSEDED evidence names a distinct existing successor. Supersession chains
  cannot cycle. A successor may itself become superseded or retracted; the
  retained history does not become current support.
- Replay admits only ACTIVE → SUPERSEDED or ACTIVE → RETRACTED retirement.
  Retired IDs cannot be reused or resurrected. Every retirement removes affected
  bindings from all claim states; affected SUPPORTED claims become UNKNOWN,
  and a CONTESTED claim that loses its last binding becomes UNKNOWN.
- Event sequence starts at 1 with no gap or duplicate and one exact
  InvocationIdentity throughout. Wire version must be integer 1, excluding
  booleans and numeric lookalikes. Projection ordering and its SHA-256 digest
  are canonical. The digest is not a signature or acceptance receipt.

Direct constructors, event export/replay, projection export/hash and the
active_evidence / supported_claims views enforce these same invariants.
Malformed enum values, source input, encoding and iterator failures produce
bounded ReasoningStateError codes without copying input into the error.

## Resource limits

| Resource | Limit |
| --- | ---: |
| Events in a complete replay prefix | 2,048 |
| Evidence / claims / open gaps | 256 / 256 / 128 |
| Source refs per evidence / superseded IDs per event | 16 / 16 |
| Evidence IDs per claim | 64 |
| Statement / question bytes | 8,192 / 4,096 |
| Reason or evidence/claim/gap identifier characters | 128 |
| Canonical event / projection / replay bytes | 131,072 / 4,194,304 / 16,777,216 |

Iterable inputs consume at most their item limit plus one before rejection,
including direct dataclass constructors. This bounds item consumption from an
infinite generator; it does not preempt a caller-supplied iterator whose
individual next() blocks. Hosts must supply terminating iteration steps.
Serialization revalidates values and incrementally enforces byte bounds.
Overflow fails closed; it does not silently discard history or support.

Broader #95 remains open, including durable authenticated append/cursor/compaction,
WorkPlan freshness admission, renderer integration, replaceable hands,
physical isolation, uncertain-side-effect recovery and live E2E proof.

