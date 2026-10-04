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
denies execution. Every `credential_ref_fields` argument is mandatory when the
tool is invoked and must be an explicit non-empty opaque string already present
in the signed grant. Omission, `null`, numbers, containers, empty strings and
ambient/default credential fallback all fail closed.
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

Production has an independent stage-one trust root at
`/run/herdr-bootstrap`; **PATH must resolve `hermes` from that frozen tree, not
from `/run/herdr/policy-code`**. The repository's regular
`agent-stack/policy-bin/hermes` is source material that #82 copies into this
host-owned bootstrap snapshot. Its only action is an absolute exec of the
independent host-OS `/usr/bin/python3` with `-I -S` and the fixed
`/run/herdr-bootstrap/agent-hermes-policy-stage1`. That stage-zero interpreter
is a separate trust anchor from the pinned CPython runtime being verified: it
must be root-owned, non-group/world-writable and outside worker-writable roots.
The stage-one verifier is stdlib-only and reads no policy Python.

Before stage two, stage one requires a bounded fixed
`/run/herdr-bootstrap/immutable-trees.json` with
`schema_version=herdr-policy-bootstrap-1` and
`authority=herdr-host-frozen-tree`. The proof is created by the host from the
same independently copied `FrozenTree` objects that #82 retains. It binds the
exact seven task/run/fence identity fields and, for each of
`/run/herdr/policy-code`, `/home/agentops/.hermes/hermes-agent`, and the pinned
CPython root, the exact device, inode, `FrozenTree.source_digest`, and
`snapshot_kind=host-frozen-copy`. Stage one requires the bootstrap root and all
three trees to be exact dedicated read-only mounts and rejects **every
unexpected descendant mount, read-only or writable**. A nested read-only bind
can shadow FrozenTree bytes just as effectively as a writable bind. It checks
the mounted tree inode identities and independently
recomputes the policy-code FrozenTree manifest digest before executing any
policy byte. A read-only alias of an ordinary worker-writable tree is therefore
not acceptable host evidence.

Only after those checks does stage one open both the verified stage-two
source inode and the pinned Python ELF with `O_NOFOLLOW`. It verifies the
Python SHA256, retains both FDs, and `execve`s the pinned interpreter while
supplying the stage-two script as `/proc/self/fd/<stage2-fd>`. The interpreter
therefore never reopens mutable policy code by pathname. Stage two requires
the inherited interpreter FD, the inherited source FD and the verified proof
digest; it checks that the loaded source inode is exactly the held stage-two
inode, then reopens the fixed bootstrap proof and revalidates its digest,
identity, exact tree inodes and no-descendant-mount state before importing
`herdr.security`, `herdr.hermes_guard`, or any Hermes module. Environment
markers alone are not continuity authority.

The guarded launcher then reads only the fixed bundle path and exact
host-controlled pane env: `HERDR_POLICY_CONSUMER`,
`HERDR_POLICY_AGENT_ID`, `HERDR_POLICY_PARENT_AGENT_ID`,
`HERDR_POLICY_PARENT_TASK_ID`, `HERDR_POLICY_TASK_ID`,
`HERDR_POLICY_RUN_TOKEN`, and `HERDR_POLICY_FENCING_TOKEN`. It verifies the
canonical signed bundle, identity/fence and attested runtime. Stage two rechecks
the inherited interpreter descriptor against `/proc/self/exe`, hashes the venv
site-packages import surface, requires an absent `sys.pycache_prefix` under the frozen read-only bootstrap tree, and adds
the verified site-packages without processing `.pth` files. Conventional
`__pycache__` and sourceless `.pyc` files have no execution authority. Empty,
truncated, noncanonical or invalid proofs/bundles fail closed. CLI/env-selected
grant, key, bundle, policy code and Hermes root paths have no authority.
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
that re-binds the new credential identity before use. Before any Hermes-facing module import, policy mode sets
`HERMES_SAFE_MODE=1` and `HERMES_ENABLE_PROJECT_PLUGINS=0`. Because Hermes
loads profile/project dotenv with override semantics, the guard also wraps the
dotenv loader and reasserts these values after every layer, while
`PluginManager.discover_and_load` is independently disabled. A `.env` cannot
re-enable user/project/entry-point Python. Process-capable tools are similarly
restricted to the attested local backend: terminal config is forced to
`env_type=local`, cached environments are checked before execution, and the
shared physical environment-construction seam rejects any non-local
`env_type` **before** SSH/Docker/Modal/Daytona/Vercel/plugin provisioning can
perform network or credential-bearing setup. `execute_code` is checked again
after acquisition as defense in depth. Those backends require a future
separately attested policy and are not authorized by #76.

## #82 integration interface

#82 owns physical bwrap setup, recovery and launch sequencing. #76 does not
implement #82 integration yet or duplicate its split-intent and
scheduler/sentinel recovery fixes. Required integration steps:

1. Keep the host-OS `/usr/bin/python3` stage-zero interpreter root-owned and
   outside every worker-writable root; it is independent of the pinned runtime
   being verified. Freeze four additional host-owned sources outside
   worker-writable roots: an independent bootstrap tree containing only the
   reviewed `hermes` entry and stage-one verifier, the approved #76 policy-code
   tree, the exact Hermes tree, and the exact pinned CPython runtime tree.
   Retain their directory FDs. Bind them as exact
   read-only mounts at `/run/herdr-bootstrap`, `/run/herdr/policy-code`, the
   fixed Hermes root and fixed Python root, with **no descendant mount at all**
inside any trusted tree unless a future proof schema explicitly binds that
descendant's identity and digest.
   PATH inside the pane must begin with `/run/herdr-bootstrap`, never the policy
   tree. Before bwrap, generate the bounded `immutable-trees.json` from those
   retained FrozenTree identities/digests and include it in the independent
   bootstrap snapshot. A mutable checkout merely re-bound read-only is not an
   accepted source.
2. Precreate an empty bundle inode through `stage_policy_bundle` on the host;
   retain its FD and device/inode and readonly-bind that same inode to
   `/run/herdr-policy/grant.bundle.json` before bwrap starts.
3. Supply all seven `HERDR_POLICY_*` identity env fields through host-controlled
   `PaneSplitParams.env` before bwrap. #82 already supplies task ID and run
   token in its own launch context; it must additionally supply consumer,
   agent ID, parent agent/task IDs and fencing token in the names above.
4. Verify actual bwrap state and produce its host attestation. Set
   `RuntimeAssurance` from observed writable mounts and network access. Set
   `credentials_isolated=true` only after raw credential files and env are
   physically inaccessible to tool-spawned processes. Read-only credential
   exposure is still exposure. Process tools fail closed otherwise.
5. Build the exact grant, including current/parent identity, process ceilings,
   exact tool rules and any delegated `parent_grant_hash`; call
   `child.require_subset_of(parent)` for children. Seal once through the held
   FD with the actual attestation digest. Do not rename the inode.
6. Register verified approval evidence with `ApprovalLedger` on the host and
   serve a host-created Unix listener at `/run/herdr-policy/approval.sock`.
   Keep its SQLite database and WAL outside all pane writable mounts; expose
   only the socket to the guarded pane. Start Hermes only after this authority
   is ready. If the broker is lost, high-risk calls fail closed.
7. Independently recheck the sandbox readonly bind, same device/inode and
   SHA256 returned by `seal`. Only after this check may `herdr agent start`
   occur. A stale/failed seal or mismatch must deny launch.
8. Kill/quarantine a superseded process before a newer fence is authoritative;
   the grant is scoped to one exact process/run/fence.

No #82 runtime or deployment change is made by #76.

## Round-5 bootstrap and filesystem authority clarification

This section supersedes any earlier wording that could be read as treating public environment variables or readable file descriptors as bootstrap provenance.

BootstrapAuthority is a host-only one-use authority. #82 must create the listener and register BootstrapExpectation only after the real sandbox/mount proof and same-inode grant seal exist. Registration binds the exact InvocationIdentity, frozen proof digest, exact stage-one inode and SHA256, exact held stage-two SHA256, exact pinned Python inode and SHA256, and sealed bundle SHA256. The authority also requires a host-supplied peer_authorizer callback. That callback must bind the SO_PEERCRED peer PID/start ticks and process ancestry to #82's independently retained physical launch intent/proof; being a child of the pane shell, presenting the expected argv, or reproducing readable digests is not sufficient. If this host broker is absent or the expectation is not registered, policy-mode Hermes startup intentionally fails closed. #76 provides this authority contract; #82 owns its physical launch wiring.

The same authenticated Unix connection is retained across stage-one exec into stage two. Stage two must complete the one-use handshake on that connected socket and prove the same sealed bundle digest before any policy/Hermes import authority is accepted. Verified stage one starts pinned Python with -I -S and an absent, read-only bootstrap-tree -X pycache_prefix before stage-two stdlib imports.

Policy-mode local file operations use RootFDWorkspace pinned directory descriptors. read_file, document/binary read_file_bytes, read-tracking metadata/version hashing, write_file and V4A patch physical opens are relative to held root/parent FDs with O_NOFOLLOW. V4A Add uses atomic no-clobber creation, and Move uses renameat2 RENAME_NOREPLACE (or fails closed when unavailable), so a raced-in destination cannot be overwritten. File backend selection is forced local before Hermes can provision a Docker/SSH/Modal/plugin backend.

Provider routes retain the most restrictive ceilings across the admitted scope, provider policy and every selected capability: region/data-class intersections plus egress, retention and training ceilings. Approval responses are read as bounded Unix-stream lines through the terminating newline. Exact security mountpoints reject duplicate/stacked entries rather than trusting an arbitrary equal-depth mount record.


Recovery hardening retains full immutable seven-field bootstrap identities, bounded process observation and explicit boolean host peer authorization. Host routes preserve all admitted-scope hard filters and the narrowest selected-capability/provider privacy ceilings. File facade methods cannot fall through to unverified backend I/O. Policy-mode search walks pinned directory descriptors without following links or spawning a shell; this bounded profile supports literal content and file globs with explicit limits (256 files, 4096 entries, depth 16, 512 KiB per searched file, 8 MiB total, 2 seconds). Regex, context and modified-order search require a separately admitted profile and fail explicitly. Large binary read requests are clamped to the 32 MiB physical file bound.

The host broker retains an immutable BootstrapContinuation only after authenticating both stages in the same peer PID/start ticks. The bounded host-only wait/lookup supplies #82 with full admitted identity, actual agent process identity, bundle/proof/stage-one/stage-two/Python hashes and interpreter inode. Public environment markers and a registered but unfinished launch cannot produce this receipt; it is observation of bootstrap continuity, with later live readiness and completion checks still required.

Startup bytecode lookup is redirected to an absent path inside the independently frozen read-only bootstrap tree, never writable shared same-UID /tmp storage. Host bootstrap registrations have a maximum 60-second admission window; expired expectations/tombstones/receipts are reclaimed and cannot be registered with their old deadline. The durable caller retains the completed receipt and fencing identity before delivery and cannot renew an old run. Socket dispatch rejects unrelated process credentials/source before reading and serves at most 16 distinct eligible peer PIDs independently. Directory search caps entries and elapsed time while streaming enumeration; duplicate V4A Add targets fail before any effect.

Delegation preserves physical network, writable-root, sandbox-verification and credential-isolation ceilings for every retained tool. Root-FD writers serialize explicit directory mutations across cooperating guarded processes. Conditional pre_content replacement fails closed because advisory locking cannot prove exclusivity against raw writers. Host authorization runs before bootstrap connection slots are reserved; cached authorization is bound to the exact registered identity/PID/start ticks. Approval transport admits SO_PEERCRED against a mandatory host authorizer before reserving any connection slot, then independently serves at most 16 authenticated fragmented clients. The host authorizer rechecks the exact grant hash before consumption and must bind the current authenticated agent PID/start ticks, full identity, active grant and consumer stop state. Missing peer authority blocks broker startup; untrusted helpers cannot reserve slots or consume another grant.

Host ownership of the independent system interpreter is verified by the mandatory broker in the host namespace. Linux user namespaces can show host root as an unmapped overflow UID; stage one checks the exact active system inode and safe mode, then must obtain host authentication before executing pinned stage two. Guest-visible UID numbers are not host ownership evidence. The non-root interpreter override is confined to explicit in-process test fixture construction; actual HostBootstrap uses the mandatory default.

The independent stage-zero process verifies the audit-known pinned stdlib source/native-extension digest and rejects unaudited ZIP/prefix overrides before execing pinned Python; stage two repeats these checks. Auxiliary endpoints remain exact, including path slashes/query bytes. Broker pool refs must identify their own provider; untrusted directive collections reject scalar/object coercion. Explicit replacement preserves observed file modes through fchmod.

Conditional pre_content replacement on a shared POSIX workspace is unsupported and fails before any publication. Directory locks alone cannot protect against a raw writer, so this closed profile no longer claims atomic compare-and-replace. Explicit full-file writes, no-clobber creates/moves and bounded local reads/search remain available; patch operations requiring existing-file conditional replacement return a clear denial. Enabling conditional replacement requires a separately proven exclusive mutation authority, not an advisory lock or a prompt claim.

The host clears native-loader/locale/shell startup controls before creating the pane or FD-launcher process; the immutable shim repeats the relevant clearing before system Python. Stage one verifies the independent complete pinned Python runtime tree digest d35e6083e474e8d049bad69c46bd84d97c8d4cfc650bcf32fce44e2e6299f0ef, including native libraries outside lib/python3.11, before exec. The shipped stage-two bootstrap exposes only fixed host-authenticated paths; parameterized roots and custom-script interpreter execution are removed. Unit fixtures substitute components in tests only; the launcher probe now proves direct/parameterized denial, while #82 owns the real physical positive/negative startup probes.


Native startup requires environment sanitation before the first native
executable. Presence-based controls such as LD_TRACE_LOADED_OBJECTS are removed
rather than assigned empty strings. The host spawn port checks the existing
terminal-server parent chain before creating a managed pane (unreadable or
changed sources deny); the trusted OS init is the ancestry boundary. The FD
launcher shell and bwrap clear startup controls, the host broker verifies their
absence in the actual shell and peer, and stage one denies residual controls.
These checks do not restart or change a live terminal server.
