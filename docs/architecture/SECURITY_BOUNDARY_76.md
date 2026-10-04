# Issue #76 — policy/security invocation boundary

## Authority model

Hermes remains the cognitive parent and Herdr remains the deterministic policy
authority described by `HERMES_CONTROL_PLANE.md`. Model output, prompt text,
web/email/PDF content, tool output, tool schemas, plugin hooks and toolset
visibility are **not** authority.

`herdr/security.py` defines a versioned `SecurityGrant` with canonical JSON
and deterministic hashing. A grant binds:

- consumer;
- current `agent_id`;
- `parent_agent_id` and `parent_task_id`;
- current `task_id`, `run_token`, and fencing token;
- the accepted `CapabilityScope`;
- exact per-tool argument/path rules and signed workspace root;
- process/network/filesystem ceilings;
- host-produced physical runtime assurance;
- provider/data-residency/privacy routes;
- credential references, never raw credentials;
- exact side-effect approval evidence;
- optional `parent_grant_hash` for delegated children.

A delegated child must carry the exact hash of its accepted parent grant,
identify the parent's task and agent, and pass `require_subset_of(parent)`.
Tool, provider, permission, region, data-class, egress, retention, training,
process, network, writable-root and credential-reference ceilings can only stay
equal or narrow.
The child's issue/expiry interval must fit entirely inside the parent's.
If a child retains a custom tool, it must retain every parent path and
credential-reference field constraint, even when the argument is omitted from
the child's allowed keys: Hermes runtime defaults can still supply it.

`herdr/grant_factory.py:build_host_grant` is the host construction boundary.
Its inputs are trusted scheduler identity/lifetime/workspace, an admitted
`CapabilityScope`, exact `ToolRule` and `ProcessPolicy` values, the exact parent
grant for a child, a typed Capability Registry snapshot, host credential broker
inventory, and observed `RuntimeAssurance`. It derives each signed provider
route's endpoint and API mode from broker inventory, checks the mode against
registry executor metadata, and derives region/data policy from registry
provider metadata intersected with the admitted scope. It rejects unknown or
ambiguous routes. A root has no parent hash; a child receives the exact parent
hash and must pass `require_subset_of(parent)` before sealing. Model/prompt/tool
arguments have no factory input capable of adding a provider, URL, API mode,
region, credential ref, tool, permission, executor, or runtime assurance.
Broker refs are opaque identifiers, never bearer tokens. The request-local
resolver must bind the *effective* key after any refresh/rotation to exactly
one broker-verifiable signed ref; grant cardinality never supplies identity.
For the production Hermes lane, the Capability Registry must expose the exact
audited `HERMES_EXECUTOR` build identity as `ExecutorDescriptor.id`, and the
admitted `CapabilityScope.executors` must contain that exact id. Stable human
labels belong in `runtime_id` / `adapter_id`; they are not substitutes for
the signed executable identity. The bootstrap independently recomputes the
same build identity before importing Hermes and requires exact equality.

## Installed Hermes v0.21.5 finding

The audited host runs Hermes Agent v0.21.5. It supports:

- `pre_tool_call` plugin hooks;
- `tool_request` and `tool_execution` middleware;
- custom/plugin toolsets registered in the tool registry.

Those are useful defense-in-depth/UI surfaces, but they are not a security
authority in this release. `model_tools.handle_function_call` exposes
`skip_pre_tool_call_hook`, `skip_tool_request_middleware` and
`skip_tool_execution_middleware`; middleware failures are not a fail-closed
authorization primitive.

The built-in Hermes `file` toolset resolves to all of:

`patch`, `read_file`, `search_files`, `write_file`.

Therefore `--toolsets file` cannot express a read-only `read_file` grant.

## Authoritative invocation guard

`herdr/hermes_guard.py` installs an in-process guard at the actual audited
execution seams without changing the Hermes installation:

1. `agent.tool_executor._run_agent_tool_execution_middleware` — the common
   model-emitted execution chokepoint for sequential and concurrent calls.
   Authorization wraps its final `execute` callback, so it sees arguments only
   after request middleware and `pre_tool_call` modification and therefore also
   covers inline executors, `delegate_task`, context-engine and memory-provider
   tools that never enter `model_tools` or `ToolRegistry`;
2. `model_tools.handle_function_call` — direct/aliased calls, including callers
   that set all audited `skip_*` flags;
3. `ToolRegistry.dispatch` — effective local-tool arguments at the registry
   boundary;
4. connector dispatch — the separate connector execution path;
5. `agent.turn_api_call.perform_api_call` as imported into
   `agent.conversation_loop`, plus
   `hermes_cli.middleware.run_llm_execution_middleware`. The signed provider
   route is checked before middleware callbacks and again before transport.

The Tool Search `tool_call` bridge is resolved to its underlying tool(s), and
connector batches are checked entry-by-entry. The guard authorizes the
effective arguments again at the lower dispatch seam, so request middleware
cannot authorize one path and execute another. Hermes `skip_*` flags do not
skip this layer.

The real-host compatibility probe proves that a grant containing only
`read_file`:

- allows scoped `read_file`;
- denies `write_file` even with all audited `skip_*` flags;
- denies direct `registry.dispatch("write_file", ...)`;
- denies a legacy alias to an ungranted tool;
- denies a connector side effect hidden behind `tool_call`;
- denies middleware rewriting an allowed file path outside the grant;
- denies a directly model-emitted inline/delegation tool even when an executable
  callback exists;
- authorizes an allowed inline call only on its final effective arguments and
  executes it once; nested registry dispatch reuses the same authorization
  context instead of consuming one-use approval evidence again.

No live Hermes config is changed by the probe.

## Per-argument, credential and process enforcement

Every granted tool needs a `ToolRule`. Unknown argument keys fail closed.
Declared path fields are canonicalized and must remain under an allowed root. Built-in file tool roots must remain within the signed workspace root.
V4A patch mode checks and normalizes every Update, Add, Delete and Move
source/destination header. Its top-level `path` is optional; when supplied it
is checked too. The normalized arguments are the ones passed to Hermes.
Relative paths use Hermes' task path resolver, and unavailable resolution
denies execution.
This logical check complements, and does not replace, #82's inode/mount
physical boundary.

Raw secret-like keys or values are rejected from model-controlled arguments.
A tool may receive only an explicit non-secret credential reference listed in
the signed grant.
Grant, provider-route and provider-request credential references accept only
opaque `pool:<provider>:<entry-id>` identities; raw keys and key hashes are
not authorization identities. For Hermes v0.21.5 the guard checks the actual
`agent.api_key` against `agent._credential_pool.entry_id_for_api_key` and the
pool's exact provider before using that opaque identity. Direct keys, token
callables and absent/ambiguous pools fail closed.

`terminal` / `execute_code` are process authorities, not alternate spellings
of file/network permissions. They require a `ProcessPolicy` and signed
`RuntimeAssurance`. The actual runtime network access and writable mounts
must be no broader than the process grant, and credential isolation must be
physically true. The implementation does not attempt brittle shell-command
parsing.

`RuntimeAssurance` is inside the signed grant and records:

- real sandbox verification status;
- the host-produced sandbox attestation digest;
- actual network access class;
- actual writable roots;
- whether raw credentials are isolated from tool-spawned processes.

A runtime claim supplied only by model text or CLI without the signed grant has
no authority.

## Side effects and approvals

Tool risk is typed. Built-in file/process tools cannot be reclassified to a
weaker risk class.

Routine `WORKSPACE_WRITE` and `PROCESS` operations may be authorized by the
signed task grant plus the verified physical sandbox, so normal coding does
not require a human approval for every edit or shell command. Consumer policy
may still require per-call approval for those classes.

`EXTERNAL_SIDE_EFFECT`, `CREDENTIAL_USE`, and `PHYSICAL` operations always
require an explicit approval class in the grant. Approval evidence is bound to
the exact consumer/agent/parent/task/run/fence identity, canonical tool and
canonical argument digest and is one-use across guarded processes. Missing, mismatched or
replayed evidence fails closed.
Consumption goes to the fixed `/run/herdr-policy/approval.sock` Unix broker.
The host registers verified grant approvals in a durable SQLite ledger outside
every model-writable mount, then serves atomic consumption from the host side.
The guarded process cannot choose the broker path; an absent/unreachable broker
denies a high-risk call. The broker and its ledger are an integration contract
for the host launch owner; #76 does not start a live service.

## Untrusted content and providers

`TaintRestrictions` can only remove tools/providers. There is deliberately no
untrusted-content API that can add a tool, permission or provider.

Provider routes enforce provider membership, exact HTTPS `base_url`, exact `api_mode`, region, data class, egress, retention, training and credential-reference ceilings. The route metadata comes from the signed host grant. Ambiguous region/data class/credential routes fail closed at the Hermes execution seam. `ProviderCircuitBreaker` is per-provider. A fallback to an ungranted provider is denied before any middleware callback or model request. The terminal check catches a provider switch during middleware. This checks Hermes v0.21.5 normal execution path; it is not a general network firewall or proof of provider data residency.

## Authenticated bootstrap

Live Herdr 0.9.1 runs a persistent server that owns pane shells. `AgentStartParams`
contains only `name`, `kind`, `pane_id`, `args` (and timeout); client/worker FDs
and environment do not cross the daemon into Hermes. `PaneSplitParams` has an
`env` map. PR #88/#82 prepends `agent-stack/policy-bin` to PATH in the child
pane before bwrap, creates the bwrap sandbox, physically verifies it and
records attestation before `herdr agent start --kind hermes`.

The host calls `stage_policy_bundle(path)` before bwrap. It creates one empty,
regular, host-owned inode with `O_RDWR|O_EXCL|O_NOFOLLOW`, retains its FD, and
records device/inode. #82 must readonly-bind **that same inode** to the fixed
sandbox path `/run/herdr-policy/grant.bundle.json` before bwrap starts. After
real bwrap proof, the host builds `RuntimeAssurance` from observed state and
calls `PolicyBundleStage.seal` exactly once with the exact expected identity and
attestation digest. The helper signs with an ephemeral Ed25519 key, writes a
canonical versioned bundle through the held FD with `pwrite`/`ftruncate`,
fsyncs, rereads and verifies signature, identity, attestation and inode. It
returns SHA256/device/inode. No rename or replacement follows the bind. #82
must recheck the physical readonly bind against that SHA256 and device/inode,
then and only then start the agent. A failed or partial seal denies startup.

The pinned, host-owned inode and physical readonly bind are the bundle trust
root. The public Ed25519 key carried inside it proves canonical integrity after
seal but is not an independent external trust root. No private key or credential
is persisted or exposed in the sandbox. Missing Ed25519 support fails closed.

A live read-only host probe additionally verified the actual Herdr launch
chain, not merely a helper: Herdr 0.9.1 `agent start` in a fresh pane whose
`PATH` began with this worktree's `agent-stack/policy-bin` executed literal
`hermes --version`; the #76 shim intercepted it and failed closed on the absent
fixed `/run/herdr-policy/grant.bundle.json` read-only trust mount. The global
Hermes version banner never appeared, and the probe pane was closed. This proves
the supported path is `herdr server → pane shell → policy-bin/hermes → guarded
Hermes`; it does not claim #82 has integrated the bundle yet.

`agent-stack/policy-bin/hermes` is a regular executable shell entry (not a
symlink). It starts the fixed policy-code launcher with `/usr/bin/python3 -I -S`.
This host system Python and its standard library are the first-stage trust base.
The launcher reads only the fixed bundle path and exact host-controlled pane env:
`HERDR_POLICY_CONSUMER`, `HERDR_POLICY_AGENT_ID`,
`HERDR_POLICY_PARENT_AGENT_ID`, `HERDR_POLICY_PARENT_TASK_ID`,
`HERDR_POLICY_TASK_ID`, `HERDR_POLICY_RUN_TOKEN`, and
`HERDR_POLICY_FENCING_TOKEN`. It checks the exact readonly file bind and
verifies the canonical signed bundle, identity/fence and attested runtime. It
opens and hashes the pinned Hermes Python ELF, verifies its standard library,
then executes that held file
descriptor with `-I -S`. Stage two rechecks the inherited descriptor against
`/proc/self/exe`, hashes the venv site-packages import surface, installs a fresh
`sys.pycache_prefix`, and adds the verified site-packages without processing
`.pth` files. Conventional `__pycache__` and sourceless `.pyc` files have no
execution authority. It installs the guard before importing and
calling `hermes_cli.main`, passing ordinary Hermes argv through. Empty,
truncated, noncanonical or invalid bundles fail closed. CLI/env-selected grant,
key, bundle, policy code and Hermes root paths have no authority.
Before importing Hermes modules, bootstrap checks version 0.21.5, the audited
Git HEAD `ee5ee84a345204a3b1d6ef6ba1ab747e602867b9`, a clean tree and the
deterministic digest of actual tracked bytes. Every pre-guard Git command uses
a sterile environment plus command-line overrides disabling repository-local
`core.fsmonitor`, untracked cache and hooks, so repository configuration is not
an execution authority. It rejects unexpected untracked importable source
outside the venv. Production additionally requires the exact Hermes source/venv
root and pinned CPython runtime root to be dedicated read-only mounts for the
whole process lifetime; hashing alone is not a TOCTOU boundary. The executor identity combines that source
digest with pinned Python SHA256
`1e761eb19d6f2594ab8dc64bd99ad4e1753589f3bf1ec199e4eef3aaa21e3930`
and its standard-library SHA256
`330e97044fcb6873bc76ab37b63bfcd8c9a081d64d285adea164d3f72b548c2e`,
and site-packages SHA256
`61bbcc21c6f429974c9e6d10258a93056b439cb3a4afd5548e112694f5e0fea0`.
The signed scope must contain exactly
`hermes:0.21.5:sha256:2e622affe56086408e159ec08c36fd8171d1181da3f4f5ba5259d1de160a9e34`.
Outer tool authorization checks the proposed call without spending approval;
the final inline, registry, or connector seam consumes it for effective args.
The guard also owns the installed Hermes v0.21.5 auxiliary provider seams
(`_relay_sync_completion`, `_relay_async_completion`,
`_relay_sync_stream`), so compression, vision, memory and fallback attempts
must match an exact signed provider endpoint/API mode and trusted pool
credential before the provider callback runs. Native Anthropic credential
rotation is disabled in policy mode; a future refresh requires a trusted broker
that re-binds the new credential identity before use. Before any Hermes-facing
module import, the launcher sets `HERMES_SAFE_MODE=1` and
`HERMES_ENABLE_PROJECT_PLUGINS=0`; unpinned user/project/entry-point plugins
and user shell/webhook hooks therefore have no execution authority.

## #82 integration interface

#82 owns physical bwrap setup, recovery and launch sequencing. #76 does not
implement #82 integration yet or duplicate its split-intent and
scheduler/sentinel recovery fixes. Required integration steps:

1. Precreate an empty bundle inode through `stage_policy_bundle` on the host;
   retain its FD and device/inode. Readonly-bind that inode to
   `/run/herdr-policy/grant.bundle.json` before bwrap starts. Mount #76 policy
   code and `agent-stack/policy-bin` read-only; ensure that directory leads PATH
   inside the pane and that `hermes` resolves to the guarded launcher. In the
   same bwrap lifetime, bind the exact
   `/home/agentops/.hermes/hermes-agent` root and exact
   `/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu`
   root as dedicated read-only mounts. The launcher rejects a writable mount,
   the host root mount, or a parent-only mount; these roots must remain
   read-only until the guarded process exits.
2. Supply all seven `HERDR_POLICY_*` identity env fields through host-controlled
   `PaneSplitParams.env` before bwrap. #82 already supplies task ID and run
   token in its own launch context; it must additionally supply consumer,
   agent ID, parent agent/task IDs and fencing token in the names above.
3. Verify actual bwrap state and produce its host attestation. Set
   `RuntimeAssurance` from observed writable mounts and network access. Set
   `credentials_isolated=true` only after raw credential files and env are
   physically inaccessible to tool-spawned processes. Read-only credential
   exposure is still exposure. Process tools fail closed otherwise.
4. Build the exact grant, including current/parent identity, process ceilings,
   exact tool rules and any delegated `parent_grant_hash`; call
   `child.require_subset_of(parent)` for children. Seal once through the held
   FD with the actual attestation digest. Do not rename the inode.
5. Register verified approval evidence with `ApprovalLedger` on the host and
   serve a host-created Unix listener at `/run/herdr-policy/approval.sock`.
   Keep its SQLite database and WAL outside all pane writable mounts; expose
   only the socket to the guarded pane. Start Hermes only after this authority
   is ready. If the broker is lost, high-risk calls fail closed.
6. Independently recheck the sandbox readonly bind, same device/inode and
   SHA256 returned by `seal`. Only after this check may `herdr agent start`
   occur. A stale/failed seal or mismatch must deny launch.
7. Kill/quarantine a superseded process before a newer fence is authoritative;
   the grant is scoped to one exact process/run/fence.

No #82 runtime or deployment change is made by #76.
