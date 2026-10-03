# Capability Registry v1 contract

Schema version: `1.0.0`. `herdr.capability` is a standard-library-only, offline
contract. A capability declares a logical spec; a provider advertises capability
refs; an executor binds a provider and spec to a particular runtime and adapter.
Names for providers, models/specs, and executors are execution policy data. They
are not added to the durable TaskGraph contract.

## Value model

All value objects are frozen dataclasses. `CapabilityDescriptor` declares a
versioned logical spec, typed feature values (presence means supported),
separate typed input/output modalities, nonnegative integer token limits,
latency enum, and a typed `DataPolicy`. The provider-neutral feature vocabulary
explicitly represents reasoning, coding, vision, audio, realtime, research,
computer use, OCR/document processing, tool use, structured output, MCP and A2A;
legacy `tools` is normalized to canonical `tool_use` before hashing and
matching; `json` and `streaming` remain backward-compatible v1 spellings. A
`null` token limit means unknown, never
unlimited. `ProviderDescriptor` contains supported refs, pricing version, modes,
and data handling. `ExecutorDescriptor` identifies runtime and adapter separately.
Registry validation rejects duplicate ids, unsupported schema versions, dangling
refs, unsupported modes, unknown fields, malformed limits, and secret-like material.

`DataPolicy` has explicit region and data class sets, egress (`none` <
`region_bound` < `global`), retention (`zero` < `limited` < `indefinite`), and
training (`excluded` or `allowed`). The evaluator requires a region, data class,
maximum egress and retention, and exact training policy in every requirement.
Unknown required data policy rejects routing. A provider and its capability must
both satisfy the data policy. No free-text privacy levels are interpreted.

`CapabilityScope` is an explicit, closed grant. Empty sets grant nothing. Child
scope is a subset only when every provider, capability, executor, tool, permission,
region, data class, and directional modality set is a subset of the parent. Each
child numeric ceiling must be no larger than its parent's; `null` is unbounded
and can only be a child ceiling when the parent is also unbounded. Egress,
retention and training limits are carried by every scope: a child may only
narrow them (`none` < `region_bound` < `global`, `zero` < `limited` <
`indefinite`, and `excluded` < `allowed`). A requirement is intersected with
those delegated limits and cannot authorize broader data handling. Call
`require_subset_of` before delegating a grant. The registry intersects this
grant with the task's `CapabilityRequirement` and declarations; it does not
implicitly grant features or tools from a descriptor.

The optional requirement `max_latency` is a hard ceiling ordered
`interactive < standard < batch`; null imposes no latency constraint.
An incompatible declaration returns `latency_exceeded`.

Requirement hard fields are separate from `preferred_providers`. Preferences
only rank candidates surviving all hard checks. Directional input/output token
floors must each fit their declared maxima and their sum must fit the shared
context window and any delegated context ceiling. Cost ceilings use nonnegative
integer micro-USD. Unknown estimated cost rejects when either requirement or
grant has a ceiling. No score can override a hard rejection.

## Runtime and matching

`RuntimeStateSnapshot` is supplied separately per executor. It carries an
explicit UTC observation timestamp, positive TTL in seconds, health enum,
remaining requests, estimated cost, a reason code for nonhealthy states, and the
exact `registry_hash` under which the observation was collected. The caller
also binds every non-null estimate to the exact `requirement_hash`; an estimate
for another requirement is treated as unknown rather than authorizing a budget
decision. The caller passes evaluation time (`at`); the match is deterministic for these inputs.
Fresh means `observed_at <= at < observed_at + TTL`. Missing, future, expired,
or registry-mismatched observations reject. A registry reload therefore fails
closed for old runtime observations until fresh state is supplied. Unknown,
degraded, or unavailable health and unknown or zero rate-limit availability
reject. Runtime observations never enter a descriptor or registry hash.

`CapabilityRegistry.candidates` returns every compatible executor, sorted first
by preference score then executor id, plus explicit per-executor rejection
codes. An unknown capability returns `unknown_capability` and no matches. The
registry never probes a provider. A caller may route only a returned match.

## Canonical serialization and reload

Every declaration has `to_json` and `to_hash_json`; both include
`schema_version`. Registry snapshots serialize sorted by id. Set-like arrays
are sorted lexicographically when constructed. Object keys are sorted by Unicode
code point in compact UTF-8 JSON (`ensure_ascii=False`, separators `,` and `:`,
no NaN). All numeric fields are bounded to `0..2^63-1` (TTL has its tighter bound).
Malformed registry collections are rejected as `CapabilityError` before reload.
Integers are decimal JSON integers; unknown numeric facts are JSON
`null`. Enums use their lowercase contract values. Hashes are lowercase SHA-256
hex of those exact bytes. Timestamps and live observations are absent from
declaration and registry hashes. Field order on input does not affect a hash.

Reload parses and validates the entire candidate, computes its hash, then swaps
the sole snapshot reference. A parse/validation failure leaves the last good
snapshot in place. Every `CapabilityMatch` pins the exact registry, capability,
provider, and executor hashes used to decide the route.

## Legacy TaskGraph adapter

`requirement_from_v1_model_policy` reads an existing v1 `model_policy` mapping
without mutating it. Legacy `model` and `fallback_model` strings retain their
order as opaque model hints; they do not become provider grants or provider
preferences. Existing node tools and permissions may be passed through
as hard requirements; the caller must still supply an explicit grant and typed
data policy before routing. Unknown legacy keys remain opaque. Historical node
payloads, TaskGraph validation, serialization, and graph hashes remain unchanged.
