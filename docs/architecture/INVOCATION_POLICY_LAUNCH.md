# Host invocation policy launch

Herdr owns physical launch and derives no permission from a prompt, TaskGraph field, environment variable or remote metadata. The host supplies a HostPolicyLaunchFactory backed by accepted consumer/provider authorization and exact approved code/runtime source manifests. Root and managed-child launch deny before pane creation when that host authority is unavailable. The embedding/configuration and live activation remain issue #78 work; this change does not install or deploy a runtime or modify credentials.

## Frozen execution bytes

ApprovedTree freezes a copied immutable manifest at construction. FrozenTree walks source components through held no-follow directory descriptors, admits bounded regular files only, checks every raw SHA-256 while copying, and creates a private independent storage tree outside worker writable roots. Explicit executable files are selected by the host manifest. A source checkout edit, rename or updater cannot change copied bytes. Complete inventory checks reject missing, extra, symlink, FIFO and changed entries; files and total bytes are bounded.

The independently copied roots are mounted by retained descriptors at the fixed policy code, Hermes and Python locations. No read-only alias of a writable runtime installation is used. Mount verification requires exact device/inode, read-only roots, no writable descendant mounts and non-host mount/PID namespaces. The host storage and copies remain outside the worker write surface for the lifetime of its owned pane. Host storage is part of the trusted host boundary, never a directory selected by the task.

The launch helper reopens each held host descriptor before bwrap creates namespaces, rechecks type/device/inode and admits exactly the declared descriptor/target pairs. Missing, duplicate, unused or changed descriptors deny. Managed workspaces also use their held original inode. Policy launches mask /run, make Hermes session/cache/log state ephemeral and pin PATH to the copied policy shim.

## Same-inode sealing order

1. Accept node identity, tools, permissions, workspace and host grant.
2. Create independent code/runtime copies and an empty exclusive 0600 grant inode in protected host storage.
3. Create the owned pane with exact consumer/agent/parent/task/run/fence environment.
4. Start bwrap with read-only descriptor binds and verify physical mount/PID identity.
5. Observe the actual runtime assurance and sign through the retained grant O_RDWR descriptor.
6. Fsync/read back/signature-verify the same inode and recheck its mounted read-only inode and digest.
7. Publish protected host policy evidence before recording agent-start intent and invoking Hermes.

The private signing key stays in the host object and is discarded after sealing. Only the signed public bundle is exposed to the worker. Version 2 evidence records grant/bundle/code/runtime hashes, every mounted tree inode, bundle inode, process start ticks, exact identity and sandbox attestation digest. Restart verification reopens those exact mounts and the signed bundle, checks namespace/environment/runtime assurance and rejects replaced processes or writable descendants. Historical completion may validate the grant at the protected launch timestamp; this never extends live invocation authorization. The protected scheduler attestation persists the bounded proof and revalidates exact consumer/parent/task/run/fence and every digest during replay; malformed or cross-attempt records fail closed. A legacy namespace-only record remains distinct from sealed invocation policy and cannot supply semantic acceptance.

Network assurance is measured: the retained host namespace is GLOBAL; an isolated namespace is NONE. This implementation never claims provider-only network enforcement or credential isolation. Enabled process grants therefore deny. Native file tools can operate within admitted scope; privileged operations and an approval broker require their separately proven host embedding.

## Delegation and lifecycle

prepare_child requires an accepted typed parent grant. Consumer/parent identity, lifetime, tools/arguments/paths, provider/privacy/credential and process ceilings must remain a mathematical subset; legitimate child workspaces must already be covered by host authorization. No automatic parent filesystem expansion occurs.

Root fencing increases for a new semantic attempt and is retained during ambiguous-delivery reconciliation. Scheduler identity remains authoritative for children. A protected queue field or browser status never substitutes for a policy mount or semantic acceptance evidence.

Prepared host objects and copies remain retained across ambiguous prompt outcomes. Cleanup of only factory-owned objects is allowed after closure of the exact owned pane has been proven; an unknown outcome retains resources for reconciliation. Recovery after host-process loss must reopen and prove retained objects from protected host evidence, without manufacturing a new grant, prompt, attempt or budget. Issue #85 owns semantic acceptance, #86 owns execution plans and #87 owns cumulative retry/budget accounting.

Every unexpected descendant mount beneath a frozen policy/runtime root is rejected, including read-only shadows. A read-only visible shadow can still refer to mutable external backing bytes and never proves the approved FrozenTree inventory. The real bwrap regression attempts a separate RO bind over approved module.py and denies sealing before agent start.

## Host-authenticated startup and durable recovery

The factory composes a fourth independent frozen tree at /run/herdr-bootstrap containing only the exact shim, independent stage-one script and canonical full-identity/tree proof. An inode-pinned private host Unix socket is mounted read-only at /run/herdr-policy/bootstrap-authority.sock. The actual FD launcher admits socket descriptors as a distinct type and binds only their declared target. Bash skips profile and rc loading and resolves Hermes through the frozen bootstrap PATH.

After physical shell attestation and same-inode signed grant sealing, the host registers the exact parent PID/start ticks, copied stage-one inode, stage-two hash, pinned Python inode/hash and bundle identity. The host accepts only a newly armed start from that exact shell, namespace, environment and frozen mount set. System interpreter root ownership is checked in the host namespace; guest UID remapping is not ownership evidence. The initial registration expires within sixty seconds and is never renewed for the same start. Missing registration, sink, physical scope or authentication denies before delivery.

A mandatory host sink fsyncs version 3 continuation evidence before the broker acknowledges stage two. The scheduler upgrades only the same already attested RUNNING attempt with a recorded agent-start intent; every old sealed field must remain identical. Replay validates this transition, and exact publication retries do not create another attempt or event. The immutable published receipt remains available to its owning launch after the short broker registry window expires. A root session persists the same evidence before ACK.

Before delivery and during managed-child reconciliation, the runtime reopens the authenticated agent PID/start ticks, exact pinned interpreter and bootstrap/source hashes, attested namespaces, original signed bundle and complete invocation identity. Historical version 2 shell-only evidence cannot authorize continuation or semantic acceptance. Cleanup can still close an exactly owned pane after a failed partial startup; it grants no delivery or tool authority.

Unsealed child proposals undergo the logical parent comparison before copying; signing always repeats the complete comparison against physically observed RuntimeAssurance. Network, writable roots, credential isolation and sandbox verification cannot widen. No provisional observation is treated as a sealed grant.

The explicit scripts/probe-herdr-physical-bootstrap.py operator probe freezes the actual installed runtime, binds the real broker socket and verifies/fsyncs the receipt while stage two is blocked on ACK, then invokes only Hermes --version. It uses an isolated home and invokes no provider, deployment or live service mutation. Unit host doubles are not physical acceptance evidence.


## Standalone host composition

Both executable entrypoints now compose their real HostPolicyLaunchFactory.
The worker reads the fixed /etc/herdr/host-policy.json for each new root attempt;
a task, environment variable or CLI request cannot select a policy file. The
bridge supplies a deferred parent factory and resolves the current canonical task
file after authenticated stage-three publication and parent peer checks. It
cannot resolve the parent eagerly because the bridge starts before that receipt
exists.

The closed schema contains schema_version=1, host_uid, code and exactly two
runtime ApprovedTree inventories (source, target, files, executable_files,
max_bytes, max_file_bytes), storage, task_store_root, templates keyed by consumer
and grant_ttl_seconds (1..3600). Templates are serialized SecurityGrant ceilings.
The configuration and all ancestors must be owned by root with no group/other
write permission; the bounded reader rejects symlinks, special files and changes
during reading. Private launch storage belongs to the executing host UID and is
0700. Approved hashes come from host release approval, never from a worker
request. Templates contain opaque credential references, not raw credentials.

Root grants narrow consumer templates to the exact invocation identity,
workspace, tools and permissions. Child grants additionally reopen and
authenticate the exact retained parent policy and compare all logical ceilings
against the current consumer template, including provider routes, credentials
and tool arguments. A missing configuration denies before pane creation or
provider preflight. Installation and live policy approval remain an explicit
deployment gate; no production configuration is installed by the unit tests.

Provider authentication preflight runs in the trusted host before root pane
creation, using the sanitized environment. A setup failure before any split
cleans its prepared snapshots and bootstrap socket. After a split, cleanup
requires proof of closure of every exactly owned pane; ambiguous ownership keeps
the prepared launch for reconciliation. A successful cleanup also removes the
retained host map entry. File-tool aliases read/write/review are rejected before
agent start; grants and actual Hermes tools use read_file/search_files/write_file/patch.

## Prompt-effect boundary during crash recovery

New start-intent records carry delivery_protocol_version=1 and the exact agent,
run, fence and idempotency key. They prove only that agent startup was attempted.
A separately fsynced, one-use child_prompt_delivery_attempted record binds the
same invocation and prompt hash immediately before the economic prompt call.
Recovery can close the exact owned pane after interrupted agent startup only
when this new protocol proves no prompt intent exists. Once the prompt intent
exists, delivery remains uncertain until same-attempt reconciliation; recovery
does not resend, reset the attempt or discard its resources. Historical start
records without this protocol retain unknown delivery status and remain
quarantined. Replayed duplicate starts cannot erase a possible prompt effect.

## Granted delegation and protected results

The explicit consumer tool scope includes herdr_delegate_child. Its fixed Hermes
registry handler belongs to the authenticated invocation guard and resolves in
the herdr_delegation toolset. The host template must explicitly grant a
DELEGATION rule with sandbox verification and only key, role, objective, prompt,
tool, permission and cwd arguments. This does not enable process execution.
Both root and child CLI toolsets derive from the admitted tools. The handler
checks all seven policy identity fields and the durable parent environment,
validates bounded closed arguments and invokes only the immutable helper's
socket client. The outer broker rechecks protected task scope and actual peer
PID/mount namespaces before child admission. Direct handler calls cannot skip
the guard, and effective call approval context is bound to the grant digest.
Uninstall restores the exact registry entry only while it still belongs to this
installation.

The child result's validated canonical evidence bytes are retained in the
fsync-protected scheduler record and reconstructed on replay. The parent reply
returns these bytes as evidence with their SHA-256; it never rereads changed
worker data as retained truth. Responses have an independent bounded 512 KiB
frame limit while requests remain 128 KiB. Public status snapshots contain the
evidence digest rather than its content. Submitted findings remain candidates
for shared #85 acceptance.

## Durable ownership after host death

Before creating snapshots or a grant, the factory commits an exclusive 0600
ownership record keyed by the complete invocation identity in private 0700
host storage. It pins the storage and launch-container device/inode plus the
original PID/start ticks. All frozen copies, staged grants and bootstrap socket
resources belong to that private container. Binding the Unix socket through a
held directory descriptor avoids sockaddr path-length limits.

A process-wide private object registry retains serving brokers for later
requests in the same host process. After host death, recovery uses only the
fixed host composition and the protected ownership record. It refuses a
still-live original host, a changed storage/container inode, symbolic links,
special entries or unexpected owners/modes/hardlinks. It removes only that
container after the exact owned pane is proven absent/closed. Other attempts
and foreign files remain intact. Cleanup is repeatable if the container was
already removed; a failed resource cleanup keeps the task quarantined.

## Split and partial-start recovery

New pane intent records carry split_protocol_version=1 with a false split-start
state. A separate full-attempt, one-use child_pane_split_started event is fsynced
immediately before the external split. Under the existing parent bridge lock,
a bounded zero-match scan can release and terminalize a pre-effect attempt only
when the versioned record proves the split was never invoked. A started or
historical unknown split with no identifiable pane remains quarantined; a
snapshot alone cannot prove an ambiguous server operation stopped. This
preserves the same task/run/fence/idempotency and creates no replacement work.

An interrupted agent start may also return native agent_not_found before any
agent record exists. Only this exact typed error, a proven absent economic
prompt and retained full-identity physical policy evidence permit closing the
owned sandbox. Transport errors, ambiguous output, missing grants and legacy
unknown prompt state retain the reservation. Permanent root policy/workspace/
tool denial becomes task_invocation_policy_denied before any pane or provider
preflight rather than consuming fresh semantic attempts.
