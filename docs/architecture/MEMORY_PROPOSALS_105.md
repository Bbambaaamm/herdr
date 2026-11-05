# Bounded semantic and procedural memory proposals

This is a source-only slice of #105. It adds proposal construction and optional
advisory recall to the existing `herdr.memory.ExperienceMemory` API. Existing
episodic `Experience`, retrieval and `ExperienceStore` behavior remain intact.
It does not complete the Memory Fabric issue or authorize runtime activation.

## Host input boundary

The trusted embedding host supplies two independent inputs:

1. Immutable canonical bytes of an outcome already accepted by the existing
   evidence authority: the stored version-2 `verified_worker_result` payload,
   without the collector's returned `bundle_hash` wrapper.
2. A frozen `AcceptedMemoryBinding` obtained independently from trusted host
   state. It pins project/repository, task/run/idempotency/attempt/fence,
   plan hash, exact artifact commit and result hash, and accepted bundle digest.

The host also supplies current immutable `SourceRef` snapshots. These inputs
must not be built from candidate text, a worker's JSON, an `Experience` marked
VERIFIED, or the same unchecked bytes being presented for validation. A typed
constructor and a matching SHA-256 prove shape/integrity, not acceptance or
authenticity. This API does not verify outcomes or replace the existing evidence
authority. The host must establish accepted provenance before calling it.

`ExperienceMemory.propose` checks the record digest, canonical encoding, exact
identity/plan/artifact binding and accepted record level against those pins.
It consumes no live EvidenceStore or ExperienceStore API. In particular, it
does not call acceptance-index lookup, load a store, publish or synchronize files.
Raw accepted payload/proof bytes are neither retained nor returned.

## Derived data and scope

Every `MemoryProposal` has a semantic or procedural kind, bounded candidate
summary, task class, accepted origin pins and original backing references.
Its state is always UNVERIFIED and its authority is `derived_context_data`.
The candidate may propose a lesson; it cannot turn that lesson into a verified
fact, active prompt, skill, grant, policy, experiment, accepted memory or task
result. Promotion/curation remains a separate existing host/review boundary.

This conservative slice accepts only PUBLIC backing refs in the same project,
with VERIFIED state and no holdout series. INTERNAL and SENSITIVE content is
excluded rather than automatically declassified. The host owns truthful data
classification. At least one backing ref must bind the exact accepted result
hash and artifact commit. Duplicate source names and ambiguous current bindings
are rejected. Known secrets in identities or provenance are rejected; candidate
summary text is redacted under the current host `SecretRedactor` configuration.
Heuristic redaction is not a substitute for the host's known-secret inventory.

## Current advisory recall and context

`ExperienceMemory.recall_proposals` takes a bounded caller-supplied catalog,
separate current accepted bindings and current source snapshots. It has no
source loader or network/store port. Project and task-class filtering happens
before exposure; ordering by proposal identity is deterministic.

Changed acceptance pins, missing sources, stale/unverified/conflicting support,
changed digest/revision, private content or holdout classification return fixed
reason codes and original public provenance without the lesson body. A source
retracted by its host is omitted from the current snapshot; this API does not
invent a new SourceState or revive omitted evidence. Unknown support is not a
verified fact. Secret metadata and current redaction rules are checked again
before recall. The original proposal hash identifies catalog bytes separately
from any newly redacted output view.

A usable recall row can produce `(ContextItem, bytes)` through `context_item`.
This uses the existing optional EPISODIC/derived-summary presentation path;
semantic/procedural kind remains typed inside the candidate payload. The first
reference identifies the derived bytes as UNVERIFIED; original references remain
attached. The item cannot be mandatory. The existing ContextCompiler enforces
provider scope, exact body digest, redaction, byte/token limits and retention of
mandatory controls. Optional proposal data yields under context budget pressure.
It never enters host/system authority or changes tool availability.

## Finite bounds

- Accepted canonical record: at most 2,000,000 bytes before parsing.
- Backing sources: 1–15; the sixteenth ContextItem reference is reserved for
  the derived body. Candidate summary: at most 8,192 UTF-8 bytes.
- Complete proposal: at most 16,384 canonical bytes.
- Proposal/current-source/current-binding catalogs: bounded lists or tuples,
  at most 256 each; no implicit consumption of arbitrary iterables.
- Proposal catalog: at most 262,144 canonical bytes.
- Recall: at most 8 rows, default 4; the complete canonical array, including
  framing, fits the explicit 2–262,144 byte budget (default 65,536).

## Evidence and remaining work

Fixtures cover deterministic kinds and source ordering; exact acceptance pins;
malformed, duplicate-member, oversized or self-claimed records; private/holdout,
cross-project and unavailable/stale/conflicting provenance; current redaction;
catalog and wire-size limits; and the actual existing ContextCompiler path in
both renderers, including optional-data removal before mandatory controls.
These are pure source tests with synthetic accepted host input, not a physical
SDK canary or a claim of real acceptance provenance.

There is no background consolidator, new memory store, vector/graph index,
curator/promotion engine, scheduler, model call, budget grant, deployment or live
data import. Full #105 curation, persistence/integration, poisoning evaluation
and comparable measured token/cost benefit remain open. #76/#129/#132 physical
isolation and #78/#184 connected acceptance remain with their existing owners.
