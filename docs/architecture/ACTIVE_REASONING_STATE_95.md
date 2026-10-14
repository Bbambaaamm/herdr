# Active Reasoning State (#95)

This is a bounded task-local execution-state contract inspired by the
Evidence-Conclusion coevolution pattern described in LongHarness
(arXiv:2610.13075). It is intentionally not another scheduler, memory store,
permission boundary, or final evidence authority.

## Ownership

- TaskGraph, task/run/fence identity, grants and budgets remain existing Herdr authority.
- reasoning_state.py is a pure deterministic projector over host-validated events.
- A future #95 ExecutionEvent stream may durably store the events. This module
  does not create its own JSONL ledger.
- #73 owns ContextPlan projection.
- #75 owns gap-triggered retrieval.
- #96 owns evidence-bound tool discovery/read/compute.
- #99 owns provider rendering and structured model delta proposals.
- #85 remains the only final EvidenceBundle/DONE acceptance authority.
- #105 may consolidate accepted terminal results into long-term memory; task-local
  working evidence is not long-term memory.

## Current contract

Working evidence has an immutable ID, bounded statement, exact SourceRef
provenance, and lifecycle:

ACTIVE -> SUPERSEDED or ACTIVE -> RETRACTED.

Retired evidence remains in replay/audit history but is excluded from
active_evidence. Retiring support deterministically downgrades any affected
SUPPORTED conclusion to UNKNOWN. A model cannot silently keep a conclusion
established on retired evidence.

Conclusion claims are typed SUPPORTED, CONTESTED or UNKNOWN. SUPPORTED claims
must reference only ACTIVE evidence whose SourceRefs are VERIFIED. UNVERIFIED
sources may be working candidates, but cannot establish a supported fact.

Open gaps are explicit bounded questions. #75 can later map material gaps to
bounded KnowledgeNeed retrieval. This first slice intentionally does not
trigger tools or provider calls.

## Replay and failure behavior

Events bind one exact InvocationIdentity and a contiguous sequence. Identity
drift, gaps, duplicate evidence IDs, invalid supersession, stale/conflicting
active sources, and claims over retired evidence fail closed.

The projector is deterministic and provider-neutral. It does not need hidden
chain-of-thought or a provider transcript. Future persistence must preserve this
replay property.

## Next integration slices

1. Bind these events to the single #95 durable ExecutionEvent stream.
2. Add #99 ReasoningStateBinding and host-validated structured delta proposals.
3. Connect material open gaps to #75 KnowledgeNeed.
4. Add #74 A/B evaluation with R1 retrieval, R2 evidence
   adoption/reconciliation, and R3 verified transformation.
5. Keep #105 consolidation post-terminal only.
