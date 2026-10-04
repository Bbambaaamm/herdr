# Policy-governed MCP gateway

Issue: #70. Contract dependency: merged #69. Runtime activation requires the
shared security envelope #76 and integration evidence #78.

## Authority and boundaries

`herdr.mcp` provides host-side MCP client and authenticated server adapters.
Hermes selects a declared minimal node toolset. Herdr supplies admitted task,
attempt, fencing and idempotency identity, closed parent/consumer scopes and
fresh Capability Registry observations. GitHub remains the CI/review/merge
authority. MCP responses and MCP Tasks are remote observations, never Herdr
DONE, integration approval or deployment evidence.

An embedding service must resolve credentials to a host-owned CallContext.
Request metadata only correlates with that context. It cannot create a grant.
The listener, credential store, worker mounts, endpoint approval and actual
TaskGraph authority callbacks are activation work in #76/#78; importing this
module or merging this contract does not enable a runtime listener.

## Host configuration before a node executes

1. Approve fixed HTTPS endpoints and host-owned credential references. Redirects,
   cookies, remote callback URLs and implicit endpoint discovery are disabled.
2. Declare ServerBinding consumer, data policy, tool definition hashes, logical
   tool classes CORE/CONDITIONAL/PRIVILEGED, permissions, actual read-only effect,
   exact resource URIs and explicit Tasks/subscription opt-ins. Remote annotations
   do not establish the actual effect or permissions.
3. Register these pinned declarations through ClientAdapter.registry_snapshot.
   This step does not contact unused servers. First admitted use validates
   actual discovered schemas against approved hashes; unknown remote tools are
   omitted. Discovery pagination, payload, schema size and cache lifetime are
   bounded. No cache refresh changes an approved definition.
4. Freeze NodeToolset version, reason, registry hash, argument policy hash,
   minimal logical tool list, closed scope and invocation limits. Omitted tools
   have neither model-visible schemas nor invocation authority.
5. Provide host-owned active-attempt authority, target/argument authorization and
   runtime observations with matching requirement and registry hashes. A schema
   that accepts a path is insufficient to authorize that path.
6. Create a CallLedger on a host-only path outside every worker-writable mount.
   The security envelope must enforce these declared mount boundaries.

Only node-declared tool schemas enter model_context. Other providers are not
contacted by that operation. A node cannot silently widen tools, permissions,
endpoint, effect classification, consumer or argument policy. A changed policy
requires a fresh version/reason and a newly admitted context. An alternative
local executor receives the same permission and completion requirements; this
gateway does not automatically select a fallback executor.

## Protocol subset

The adapter targets MCP 2026-07-28: stateless HTTP POST, required per-request
metadata, JSON or request-scoped SSE, standard routing headers and validated
x-mcp-header primitive paths. It deliberately does not negotiate older
session-based versions. JSON is bounded, duplicate keys and nonfinite numbers
are rejected. Full JSON Schema 2020-12 validation runs in a disposable process
with CPU, memory and wall-clock limits. External schema references are denied.

The server adapter exposes discovery, the authenticated minimal tools/list,
tools/call, approved resources/list and resources/read. It implements the
opt-in Tasks extension's tasks/get by mapping a remote handle to the protected
local operation record and checking the exact active context. A foreign task's
completed status is only observed_complete. Neither foreign results nor events
can invoke Herdr lifecycle, merge or execution operations.

Resources expose exact host-approved URI mappings, with node permissions
checked again before transmission. Returned contents must bind the requested
URI. Resource templates and automatic web fetching are outside this subset.

Clients can explicitly open one bounded subscriptions/listen window.
Acknowledgment must precede events, acknowledged filters must be a subset of
requested filters and every event must carry the exact subscription ID.
Only requested tool/resource list changes and approved resource updates are
accepted. Changes invalidate observations and caches; they grant no permissions.
The window ends on graceful closure, cancellation, deadline or 64 events.
The host records event reason codes and digests. No automatic reconnect occurs.
The server adapter does not advertise push subscriptions; the approved embedding
listener can consume the client observation interface.

Multi-round-trip input_required remains a recorded hold. There is no automatic
elicitation, OAuth flow, sampling, tool expansion or execution of returned code.
Tool descriptions and raw results remain untrusted data for context assembly #73.

## Durable delivery and limits

The ledger reserves an immutable operation before transmission and commits
delivery_uncertain before sending bytes. Its operation identity binds consumer,
task, exact attempt/fence, frozen scopes/toolset and request digest. Reusing a key
with different arguments or context is denied. A process lock serializes each
operation; SQLite transactions and FULL synchronous WAL persist authority,
delivery counters, outcome digests and provider health across restart. Only bounded
operational Task metadata (identity, status, timestamps, TTL and poll interval)
is retained alongside remote handles; question/result payloads are excluded.
A running-task replay exposes the deterministic local handle and its admitted
descriptor, so the client can continue tasks/get after losing the first response.
Legacy/input-required replays expose the protected handle for current-state
retrieval without retaining remote questions. Approved
input/output validation schemas are frozen in the protected operation record
before transmission; they are control data, excluded from audit export.
Admission uses one immutable registry snapshot, checks for reload after runtime
observations and rechecks active policy after argument authorization immediately
before delivery. Region/class requirements come from provider/grant intersection;
the host remains responsible for actual argument data classification.

An ambiguous side effect is quarantined and never blindly sent again.
Read-only requests have at most the declared retry count; retries use the same
operation and recheck policy before every send. An exhausted read or polling
budget returns a non-retryable reconciliation outcome, including after restart.
Every post-send mutation failure retains uncertainty, including output-validator
timeouts. Eligible legacy prepared/read-retry rows freeze their validation plan
before transmission; uncertain mutations never receive a retry or a new plan.
Recorded outcomes replay without
another provider request. Raw results are not retained in telemetry: a replay
without its artifact requires explicit reconciliation of its recorded digest.

Invocation ceilings and reserved cost estimates are cumulative by consumer/task
across operation keys and attempts, with a sticky lower limit. Unknown cost
cannot satisfy a bounded cost policy. These are reservations from fresh host
quotes, not measurements of settled spend. Discovery is separately bounded and
audited. The full cross-provider cumulative execution/poll/discovery/error budget
and actual settlement belong to #87; these local counters cannot waive it.

Remote polling records its reservation before a request, respects advertised
poll intervals and is bounded to 32 polls. Task/consumer/fencing and changed
argument/provider policies are checked before polling. A provider's repeated
failures open its persisted circuit without blocking independent providers.
Terminal task results validate against the admitted schema even after a fresh
process restart, cache expiry or discovery outage. Polling never refreshes
discovery after consuming a short-lived terminal result. A legacy task lacking
its protected plan requires explicit reconciliation before another poll.

Malformed resource URIs and oversized TTLs produce bounded protocol errors.
The server returns 403 for denied authority, 503 for temporary availability
failure and 502 for uncertain delivery. Error metadata distinguishes retryable
availability from uncertainty requiring reconciliation; it never authorizes a
new economic operation. SSE accepts LF, CRLF and bare CR, including delimiters
split across reads, and media types/header names are compared case-insensitively.
Ambiguous case-duplicate headers and oversized request IDs fail within bounded
error handling. Valid JSON-RPC poll errors persist reconciliation_required,
quarantine further polling/delivery, and do not count as provider outages.
One inbound call or model-context assembly reuses a request-scoped verified
catalog even with zero discovery TTL. Post-send subscription outages before acknowledgment require reconciliation;
the same window is never reopened. Malformed pre-ack streams preserve uncertainty
too. Graceful/bounded subscription success clears the failure streak; a
disconnected stream retains its availability failure. Concurrent processes increment provider
failures atomically in SQLite, preserving the circuit threshold.

Audit stores identity hashes, immutable context bindings, reason codes and times.
It excludes raw arguments, prompts, bearer values, raw results and exception
details. The first live result is returned to its authorized caller as untrusted
data, not copied into audit.

## Dependencies and verification

Core Herdr remains importable without optional schema packages. Activating this
adapter requires the exact packages in requirements-mcp.txt in the approved
runtime environment. The release payload includes that lock and this contract;
Both CI and tagged-release jobs install the pinned optional packages. A missing validator fails closed.

Tests include actual loopback HTTP JSON/SSE, authenticated routing metadata,
side-effect response loss and restart without duplicate execution, a correlated
subscription stream, persisted circuit state, cost/call ceilings, scope/fence
denials, path authorization, malformed/external schemas, omitted tool context,
resource escape attempts and foreign Tasks without completion authority.
Fresh-process replay is tested with provider discovery and runtime observations
unavailable. Immediate terminal Tasks use the same result/output-schema checks
as polling. Successful polls reset consecutive failures. Discovery generation
checks preserve concurrent invalidation. All post-send mutation failures retain delivery uncertainty. Discovery outcomes
update persisted provider circuit health, and validated refresh clears consecutive
failures. Tool arguments and annotations require protocol objects; numeric
overflow is rejected during JSON decoding. Schema subprocesses respect existing
hard resource limits and distinguish runtime faults from invalid schemas.
Integer routing headers reject unsafe integral floats.

Protocol references:
- [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [Subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)
- [Resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
- [Opt-in Tasks extension](https://tasks.extensions.modelcontextprotocol.io/specification/draft/tasks)

The disposable schema helper runs from its trusted absolute sibling path with isolated Python imports and a minimal environment; worker current directories, PYTHONPATH and user startup modules cannot replace the validator. This does not assert that a Hermes runtime is credential-isolated.
