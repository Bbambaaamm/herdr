# Context Compiler and authoritative memory

Issue #73. Contracts depend on #69 and #72. Live TaskGraph/provider/evidence
embedding is accepted in #78; work-plan fields connect to #86, original evidence
to #85/#74, cumulative trial budgets to #87, and measured provider usage to #79/#77.

## Authority and reconstruction

Herdr supplies a typed SkillNodeContext, frozen RegistrySnapshot, closed node,
parent and consumer scopes, authoritative ControlState and a current ProjectMap.
The compiler never reads an entire repository or reconstructs truth from provider
sessions. ControlState retains task, scope, acceptance, oracle, current diff,
current error and original evidence references. Empty diff/error are explicit;
other required fields cannot disappear during compaction or budget pressure.

ContextPlan is immutable and independent of the provider's conversation/session.
The same host snapshot deterministically reconstructs its plan and context.
Every source has project, revision, digest, data class and explicit availability/
verification state. Body bytes are loaded only through the host's bounded source
reader, checked against declared size/digest and redacted before model exposure.
The reader receives the exact ContextItem and must enforce its declared read bound;
it must not perform unbounded network retrieval. Failed optional retrieval is
recorded and leaves the node's own required REPAIR controls available. Missing,
conflicting, stale or unverified required evidence blocks compilation.

Provider session caches are always omitted from authoritative context. Their
contents cannot replace Herdr controls, accepted results, grants or task state.
Remote source bodies, skills and derived summaries retain context_data authority.
No compiler/memory method executes a tool, changes a grant, runs an experiment,
merges a PR or deploys anything.

## Minimal context and stable selection

The host begins with the named task/scope, directly referenced source/symbols,
nearest tests and valid instructions. Extra source requests require an explicit
reason. Optional items are sorted by priority and identity; every selected item
and omission is audited without source bytes. No repository scan is implicit.

ProjectMap is a small explicit snapshot of languages, build/test/lint commands,
important directories, Git rules and automation. Exact base SHA and relevant file
versions must still match before use. A change returns project_map_invalidated;
the host refreshes the map under a controlled reason.

SelectionSnapshot pins approved tool schemas and the resolved #72 skill bundle.
Its hash and reason remain frozen for the node. A changed snapshot records its
previous hash and a new nonempty reason. Skill payload/trace bind the selected
executor; changing provider re-resolves the same portable data for the new
executor while preserving Herdr control state and original references.

The stable prefix holds host/consumer rules, project conventions and stable
schemas/skills. Task identity, run/attempt/fence, current diff/error, node text and
selection audit belong to the dynamic envelope. A task-ID/error change preserves
the prefix when the stable inputs remain equal. Stable prefix hashes are evidence
of equal input only; they do not claim a provider cached or discounted anything.

## Redaction, token and output budgets

SecretRedactor combines host-provided known secrets with bounded common key,
Bearer, private-key, credential-assignment and credential-bearing URL patterns.
Redaction precedes model exposure and derived-memory/artifact persistence. Source
and memory identities containing secrets are rejected rather than silently
rewritten into different references. The host must supply its actual credential
set; heuristic matching alone cannot identify every arbitrary secret string.

Messages/parts renderer adapters preserve the same host-control/data envelope.
The host supplies a TokenCounter pinned to provider, executor version and
tokenizer version. No model-supplied estimate or missing tokenizer can satisfy
admission. Required context must fit the minimum of plan, scope and capability
input limits. Otherwise the task blocks/splits; required fields are never cut.
Optional content is admitted incrementally under both token and byte limits.
The trace reports tokenizer_input_tokens and explicitly marks provider usage and
cache evidence unmeasured. Live SDK token/cache measurements remain #79/#77.
These renderer ports are not an installed provider SDK or activated listener.

Large terminal/tool output must be captured under explicit byte/time limits by
the embedding worker. capture_output redacts before host artifact persistence,
checks the returned content-addressed reference and supplies exit code, elapsed
time, bounded stdout excerpt and a dedicated error excerpt with its tail. A
nonzero exit without stderr remains an explicit failure. Over-limit output is
blocked before persistence; source bytes and errors are not silently discarded.

## Evidence-preserving derived memory

Compaction accepts explicit original item hashes/references. It cannot replace a
mandatory item or any ControlState field. Its summary is marked unverified derived
data; original evidence references remain separate and must still be usable.
A summary cannot repair historical test outcomes or count as acceptance evidence.

Experience records bind project/task class, series/variant/attempt, hypothesis,
code/model/context/policy/evaluator/corpus/scope versions, baseline/outcome,
sample count, limitations and original artifact references. Outcomes distinguish
success, failure, uncertainty and unusable results. Infrastructure outages require
an unusable reason and cannot be recorded as proved candidate failure.

ExperienceStore is a POSIX host-only 0700 directory outside declared worker-writable
roots, walked through no-follow descriptors. Redacted records are immutable 0400
content-addressed files. Cross-process locking serializes identity conflicts;
fully flushed staging inodes are atomically linked before acceptance. Partial
staging is discarded after a crash; published records replay without overwriting
history. Original evidence is never copied over or modified by memory writes.

Retrieval is bounded to eight relevant records and uses project/task/data scope.
An identical conditions fingerprint flags a comparable prior trial; a changed
relevant version asks for review and a new trial reason. A new provider session
is not a changed factual condition. These are advisory derived observations;
#87 still admits any trial against its cumulative budget, and #85/#74 still own
required proof. Private holdout sources and their summaries are visible only to
the evaluator for their exact series. Missing/unverified/stale/conflicting sources
retain explicit states; optional retrieval outages cannot substitute assumptions
for missing mandatory proof. No automatic wiki, graph database, skill promotion
or production policy self-modification is introduced.

Security checks also cover context item identities, selection explanations and
captured artifact metadata against host-known secrets. Capture preserves private
holdout bindings and redacts a single bounded string across the entire admitted
output, including streams larger than 256 KiB. A derived compaction can never
be mandatory evidence. Current project-map inputs reject duplicate file entries.
Memory paths reject traversal components before worker-root isolation checks.
Loading immutable memory revalidates metadata and derives redacted text under
the current credential configuration without rewriting stored records.
Bounded recall prioritizes verified comparable trials before unusable notes.

Private holdout evidence must match the experience's exact series as well as
the evaluator's series. A redacted recall record carries publication_digest
for the immutable stored bytes separately from its current view content hash.
Re-appending that exact current redacted view acknowledges the original
publication; altered views or unknown publication claims fail closed.
Node binding identities are checked against known secrets before plan creation.
