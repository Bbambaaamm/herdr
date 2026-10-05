# ADR: Best-of-market Context + Memory Fabric

Date: 2026-10-05  
Status: proposed via PR; implementation remains gated by existing issues and evidence.

## Decision

Herdr owns the Context + Memory Fabric. External projects are references, adapters or benchmark candidates, not new sources of task/evidence authority.

The production direction is:

- **#73 Context Compiler** remains authoritative for ContextPlan, ControlState, scope, provenance, redaction, original evidence and deterministic reconstruction.
- **#105 Memory Fabric** adds semantic/procedural memory and background consolidation while retaining #73 ExperienceMemory as the episodic baseline.
- **#74 Eval** selects candidates by verified outcome, total-system tokens, cost, latency and safety.
- **#96 Tool Fabric v2** owns deferred tool discovery and programmatic processing.
- **#79 Router v5 / ProviderAdapter** owns provider-native context capabilities and fallback.
- **#77 Machine City** reads truthful metrics only.
- **#78 E2E** proves restart, fallback, rollback and vendor-independence.

## Technology portfolio

### Hindsight — preferred hybrid memory/retrieval candidate

Evaluate Hindsight-style mechanisms for:

- semantic + lexical/BM25 + relationship/temporal recall;
- consolidated observations backed by supporting memories;
- background retain/recall/reflect behavior.

Hindsight is never authoritative. Its external benchmark claims are not Herdr promotion evidence.

### Headroom + LLMLingua — compression candidates

Benchmark:

- no compression;
- Herdr native type-aware compression;
- Headroom-style type-aware compression + reversible retrieval/CCR;
- LLMLingua-2 / LongLLMLingua where runtime/licensing fit;
- provider-native compaction as a separate capability variant.

A shorter prompt is not enough: source fidelity and verified success must remain at or above baseline.

### LangMem — procedural/prompt learning principles

Adopt as design inspiration for:

- semantic / episodic / procedural memory taxonomy;
- trajectory/failure mining;
- procedural/prompt candidate optimization;
- multi-prompt credit-assignment hypotheses.

Any learned change is a proposal only and must pass #74 + review/promotion.

### Letta — background consolidation + versioned memory principles

Adopt:

- background "dreaming"/consolidation outside the hot path;
- Git/versioned, diffable memory history.

Do not introduce Letta as a required agent runtime.

### Graphiti — optional temporal relationship graph candidate

If structured + vector/hybrid retrieval is insufficient, evaluate Graphiti-style temporal/bi-temporal relationship retrieval.

The graph is derived/rebuildable and never an execution DAG.

### Mem0 — comparator/reference

Mem0 remains useful as a benchmark/reference for semantic/vector/graph memory, but is no longer a primary required building block.

Its intended role is mostly covered by:

- Herdr #105 contracts;
- Hindsight-style hybrid recall;
- optional Graphiti-style temporal graph.

### Provider-native optimization

Where capability-detected and measured, adapters may use:

- prompt/prefix caching;
- provider/server compaction;
- deferred tool search/schema loading;
- programmatic tool processing/code execution.

These are optimizations, not task/evidence authority.

### LMCache-like KV reuse

Future-only option for self-hosted vLLM/SGLang inference. It is not part of the current API-first baseline.

## Target architecture

```text
Herdr Task / Evidence Authority
            |
            v
     #73 Context Compiler
            |
   +--------+---------+
   |                  |
   v                  v
Compression         #105 Memory Fabric
race                - Episodic: #73 ExperienceMemory
- native            - Semantic: hybrid retrieval
- Headroom-style    - Procedural: learned proposals
- LLMLingua         - Consolidation: background
                     - Graph: optional temporal index
   |                  |
   +--------+---------+
            |
            v
       #96 Tool Fabric
 deferred schemas / programmatic transforms
            |
            v
       #79 ProviderAdapter
 cache / compaction / native capabilities
            |
            v
           Model
            |
            v
 #74 Eval -> CI/review -> canary/#78
```

## Optimization objective

Do not optimize for the shortest prompt.

Optimize for:

**total-system tokens and total cost per verified successful task**

Accounting includes:

- foreground model input/output/cached/cache-write tokens;
- background consolidation/learning tokens;
- retrieval/compression overhead;
- embedding/indexing compute/cost;
- retries, fallback and reviewer overhead.

Hard ordering:

1. policy/safety pass;
2. correctness/acceptance pass;
3. quality/reliability pass;
4. only then optimize tokens, cost and latency.

## Non-goals

- replacing Herdr TaskGraph with a memory graph;
- provider session state as durable truth;
- automatic production self-modification;
- forcing one external framework as a permanent runtime dependency;
- treating vector similarity or an LLM summary as verified evidence;
- claiming token savings before #74 measures foreground and total-system usage.

## Implementation ownership

- #74 — candidate benchmark/eval matrix.
- #77 — truthful context/memory/tool/cache observability.
- #78 — E2E/fallback/restart/rollback acceptance.
- #79 — provider-native context capability routing.
- #96 — deferred tools + programmatic processing.
- #98/#99 — procedural/prompt candidate generation and bounded rendering.
- #105 — semantic/procedural memory, consolidation and advisory retrieval.
