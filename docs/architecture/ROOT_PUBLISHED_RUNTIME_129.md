# #129 — Root-published immutable Hermes / Python execution trees

## Why the previous snapshots were not lifetime immutable

`FrozenTree.create()` copies approved code to a private host directory
owned by the `agentops` UID and chmods files/directories to 0400/0500.
That protects against accidental writes *inside* the `bubblewrap`
namespace, but a **concurrent host process with the same UID** can
chmod, unlink, rename or overwrite the snapshot while the sandbox's
read-only bind still refers to the underlying mutable host inode.
A start-time SHA-256 check cannot prove lifetime integrity.

## Implemented security primitive (draft, not deployed)

`FrozenTree.attach_immutable()` only opens a **pre-existing, root-owned**
published directory from the reviewed host release authority. It does
not copy, chmod, chown or publish user-owned source files.

The source must be an absolute canonical path. Every ancestry component
from `/` to the source directory must be root-owned and neither
group- nor world-writable; no symlinks are accepted. Every directory and
every regular file within the complete approved manifest is likewise
root-owned and not group/world writable. Extra entries, missing files,
unsafe file types, SHA mismatches or bound violations reject the source.
POSIX ACL named write grants are also represented by the group-class
mask bits, so a writable ACL mask fails the mode check.

The host factory can now receive an `ApprovedImmutableTree` in place of
an `ApprovedTree` for the frozen policy code, pinned Hermes SDK tree
and Python runtime. `PolicyMount.require_immutable_runtime()` requires
**all three** trees to use the root-published lifetime contract and
rechecks bytes, ownership and inodes. Private-HOME launches reject any
`PolicyMount` that does not satisfy this condition. This is enforced
again before `PreparedPolicyLaunch.seal()` accepts signed execution
evidence. Legacy code-only sandboxes remain unchanged.

The source tree is never modified during launch cleanup: the worker
only closes its held directory descriptors, including on verification
failure. No privileged filesystem command is executed by the worker.

## Physical evidence

On `quantlab-staging-01`, the already installed RC26 release contains
a suitable **nonsecret, representative** operator-controlled directory:

`/opt/herdr/releases/v0.3.0-rc.26-4d09b58b4416/provenance`

Its complete manifest currently consists of the single
`external-runtime-dependency.txt` file. This is **not** the Hermes
runtime and it is **not** an authorization to run a provider; it serves
only as a stable identity/mount fixture.

A real bwrap CHILD namespace binds its held directory FD readonly,
observes the expected file bytes/inode, and continues observing the
same bytes while same-UID host chmod and write attempts raise
`PermissionError`. Cleanup closes the FD and leaves root-published
release bytes and modes intact. The opposing negative test rejects an
otherwise valid SHA manifest stored below a mutable user-owned parent.

## Privileged publisher / release preflight still required

A trusted release operator must independently publish the **real**
approved Hermes and Python runtime bytes under root-only versioned
storage and produce a pinned digest manifest. Do **not** simply chown an
existing agentops-owned snapshot: a same-UID process may retain an
already-open writable FD even after a later chown. Instead create **new
root-owned inodes** with a reviewed publisher, write the authenticated
payload, close/fsync, set read-only modes, and atomically publish under a
root-owned non-writable parent. Reject symlinks, hardlinks to user-owned
files, inherited writable ACLs, and any unapproved file inventory.
This requires explicit privileged operator review; neither this PR nor
its tests mutate server ownership or install the approved SDK.

Once published, a host policy authority must supply the exact release
paths and reviewed manifests to `ApprovedImmutableTree`. The native
Hermes interpreter, imports, compiled extensions, dynamically loaded
shared libraries and all execution entrypoints must resolve solely
through these approved sources. An immutable policy-code bind alone
does not prove that untrusted imports cannot enter via other mounts or
environment paths.

## Successor security corrections (draft, not activated)

The FD bridge now requires an exact `ApprovedPrivateMountPlan` for any
ordinary descriptor or additional bind in a private-HOME launch. The
record lives under `/etc/herdr/launch-plans/<canonical-identity-sha256>.json`,
with a root-owned non-writable ancestry. It binds the complete invocation
identity (including attempt and fence), exact descriptors, writable targets
and the digest of the complete bwrap argv. Self-declared target/inode lists
and unrelated root-owned CLI files do not approve a launch. All authority
mounts remain readonly; additional literal binds are rejected.

The factory holds workspace/result descriptors through cleanup. Destination
ancestors are masked with fresh tmpfs mounts before names are built, so
host-side path replacements cannot redirect the mount into host credentials.
Sensitive HOME directories and mount aliases below mutable roots are denied.
The policy shim and stage-one launcher execute from the approved policy-code
inode, rather than a same-UID-writable bootstrap copy. The bootstrap snapshot
remains a transport for exact hash-verified metadata; it is not executable
code authority.
Stage two also imports its stage-one helpers from policy code. The interpreter
cache prefix is an absent path below the same immutable code tree, so a
host-owned bootstrap transport cannot supply forged bytecode before guards.

Signed private launch evidence includes root publication paths, complete
manifest digests, code/runtime inode identities, bootstrap executable hashes
and the root-approved mount-plan record identity. Retained verification
re-establishes these sources and actual mounted inodes. Private evidence
without this provenance is refused. Child attestation and replay retain both
profile and immutable-source evidence and reject outer/inner substitution.
Cleanup attempts every independent release and preserves the first error
while closing descriptors and clearing the live launch registry.

## Concrete operator publication procedure

`scripts/publish-herdr-runtime.py` is a release helper, never a worker or
installer hook. It performs no network call, activation or service change.
Its default mode validates the root-approved request and reports the intended
new version. `--publish` requires UID 0, copies verified payload bytes into
new inodes, fsyncs files/directories, validates root ownership and complete
inventories, and publishes using Linux `renameat2(RENAME_NOREPLACE)`.
Published nonsecret files use 0444 (0555 for approved executables) and
directories use 0555, so agentops can read/execute without write authority.
Existing versions cannot be replaced. Partial unpublished staging directories
are retained for operator diagnosis, with no deployment symlink change.

The operator must first authenticate the reviewed release commit and the
Hermes/Python manifests through the existing release authority. Do not derive
approval by hashing arbitrary live worker files. After independent review,
create a root-protected version parent (for example `/opt/herdr/immutable`)
and a root-protected publication request outside all repositories. The
request uses this closed schema (all three `trees` are mandatory):

```json
{
  "schema_version": "herdr-runtime-publication-1",
  "version": "reviewed-release-version",
  "destination": "/opt/herdr/immutable",
  "trees": {
    "code": {"source": "/approved/policy-payload", "target": "/run/herdr/policy-code", "files": {"relative/name": "reviewed-sha256"}, "executable_files": [], "max_bytes": 33554432, "max_file_bytes": 4194304},
    "hermes": {"source": "/approved/hermes-payload", "target": "/home/agentops/.hermes/hermes-agent", "files": {"relative/name": "reviewed-sha256"}, "executable_files": [], "max_bytes": 2147483648, "max_file_bytes": 268435456},
    "python": {"source": "/approved/python-payload", "target": "/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu", "files": {"relative/name": "reviewed-sha256"}, "executable_files": [], "max_bytes": 2147483648, "max_file_bytes": 268435456}
  }
}
```

The values above are schema placeholders, not an approved runtime. Each
`files` inventory must be complete and independently authenticated. Code must
include `agent-stack/policy-bin/hermes`, `agent-stack/policy-bin/herdr`,
`agent-stack/bin/agent-hermes-policy-stage1` and
`agent-stack/bin/agent-hermes-policy-run`; mark actual executable files in
`executable_files`. The request must mark the policy `hermes`/`herdr` shims
and Python `bin/python3.11` executable; missing execute approval is refused.
The reviewed Python closure must cover the interpreter,
stdlib, shared libraries, extension modules and Hermes dependencies actually
used by native Hermes. Credentials are never runtime publication payload.

From the operator's authenticated checkout/interpreter, first run:

```text
python scripts/publish-herdr-runtime.py --configuration /etc/herdr/runtime-publication.json
```

Only after explicit privileged authorization, run the same command with
`--publish`. Record the returned approval digest, `publication.json`, exact
release commit and complete manifests. Keep old versions while any live or
retained launch references them; workers never delete published sources.

Tests run without root publication. They verify independent new inode copies,
retained writable source FD attacks, source symlinks/hardlinks, changed hashes,
ENOSPC preservation, atomic no-replace publication and actual worker-UID denial.
Actual root publication remains unexecuted and unaccepted.

## Activation gates and remaining integration

The new private mode remains opt-in. Schema 1 preserves the existing host
composition. Schema 2 of the same `/etc/herdr/host-policy.json` requires all
code/runtime trees to use `ApprovedImmutableTree`, complete bootstrap/CLI
and Python executable approvals, and a closed `private_launch` object:

```json
{"profile":{"name":"quantlab","source":"<approved-profile>/quantlab",
            "files":{"config.yaml":"<sha256>",".env":"<sha256>"}},
 "credential_approval":{"schema_version":"herdr-profile-credential-approval-1",
    "profile_sha256":"<canonical-profile-manifest-sha256>",
    "valid_until":"<operator-validated-timezone-aware-expiry>",
    "minimum_ttl_seconds":1860}}
```

These placeholders are a schema example, not an approved configuration.
The release operator validates credentials before publishing the finite
approval window. Before sealing each profile the host rereads the protected
configuration and verifies its exact profile digest and enough remaining
credential lifetime for the grant plus a 60-second margin. This offline check
does not prove a native login or authorize a provider call. The private path
never calls the legacy mutable-Hermes credential refresh.

Separate child bridge processes revalidate the canonical parent session,
current full invocation identity and signed retained physical evidence for
each admission. The parent's signed profile digest must equal the current
host-approved profile; changing a parent grant/profile denies before profile
preflight. In-process factories retain their existing live-parent checks.

Both root and child reserve an empty exact-attempt result inode and validate
the entire private sandbox command before pane creation. A retry may reuse
that empty inode only for the same full invocation identity and idempotency
key. Existing bytes, submission intent, unlabelled partial reservation,
changed fence/key, symlinks and hardlinks require reconciliation; no retry
truncates or deletes a result. Reservation metadata is not an admission or
completion authority. Signed evidence and pinned mount validation still apply.
The descriptor carries the exact reservation binding in the root-approved
plan. The host checks it again when building the command, and the FD launcher
checks empty bytes, full binding, inode/owner/mode/link count, submission intent
and a stable metadata stamp immediately before consuming the FD. The host
rechecks the held slot at grant seal and authenticated bootstrap confirmation.
Advisory flock is only local reservation serialization; it is not a defense
against hostile same-UID writes. Failure cleanup attempts all held resources
and removes newly allocated temporary policy snapshots even before pane split.
Late result checks use Linux `openat2` with `RESOLVE_NO_SYMLINKS`,
`RESOLVE_NO_MAGICLINKS` and `RESOLVE_BENEATH` for one coherent whole-path
lookup. They compare its inode and actual `/proc/self/fd` attachment name
with the approved result target; parent rename/replacement during lookup
denies launch. Unsupported kernel resolution fails closed. The FD launcher
also requires the held result source's actual name to equal its target.
Schema-2 immutable trees preserve executable inventories throughout later
verification and in signed retained source evidence. Both live verification
and cold recovery check actual execute bits against that inventory, so a
mode-only change cannot pass merely because file bytes still hash correctly.

The generated exact mount request is
available as `PolicyMount.private_mount_request` after the command builder
refuses a missing approval. A trusted operator/host authority must inspect
source provenance and publish the matching root record; copying a worker's
self-declaration into root storage without that validation is forbidden.
Keep the same live held descriptors when binding the record with
`PreparedPolicyLaunch.prepare_private_command()` and rebuilding the command.
The approval must exist before pane creation. No automatic privileged issuer
is implemented or installed by this change. A stale record from a previous
process/descriptor set cannot be reused merely because its task identity is
unchanged; record renewal requires trusted reconciliation. A cold restart
cannot self-approve that renewal.

Before activation, require exact-HEAD CI and independent security review, the
real root-published native Hermes closure and a technically network-isolated
zero-provider root/child/result test. Only after these gates may #78 E2E,
rollback/recovery and #53 delivery reconciliation proceed. Publication is
separate from acceptance and from any staging cutover.

## Status

Implementation and isolated tests are available for review. **No acceptance
or deployment is implied.** #129, #132, #53 and #78 remain OPEN. Production
RC26, existing queue/leases/fences, credential sources and budgets are untouched.

## One-shot operator launch-plan publication

`scripts/publish-herdr-launch-plan.py` supplies the operator publication step
for the existing private mount-plan authority. It accepts an independently
approved root-protected ticket only from
`/etc/herdr/launch-plan-approvals/<canonical-identity-sha256>.json`. It does not
accept a worker proposal path, hash arbitrary worker data into approval, start
a daemon, renew credentials, or install anything into a running deployment.

The closed ticket contains `schema_version: herdr-private-mount-issuance-1`,
the complete `plan` in the existing `herdr-private-mount-plan-1` schema, the
exact bwrap `argv`, and timezone-aware `not_before` / `expires_at` timestamps.
The issuance window must be active and at most one hour. The complete identity,
including the attempt/fence, determines the filename. All descriptors must
have unambiguous FD sources/targets and exactly one matching FD binding. The
complete argv digest and writable targets must agree with the approved plan;
reserved result metadata must name the same invocation and result inode.

The operator must independently approve the policy, immutable sources,
profile, command and actual held FD/result identities before creating a
ticket. Structural validation by this helper does not grant those permissions.
Run it only from an authenticated root-published code release with a trusted
interpreter, never by executing a mutable worker checkout as root:

```text
python scripts/publish-herdr-launch-plan.py --configuration /etc/herdr/launch-plan-approvals/<identity-sha256>.json
python scripts/publish-herdr-launch-plan.py --configuration /etc/herdr/launch-plan-approvals/<identity-sha256>.json --publish
```

Default mode performs read-only preflight. Explicit publication requires
UID 0 and an already root-protected `/etc/herdr/launch-plans` directory. It
creates a new inode, writes the canonical plan, applies 0444, fsyncs the file,
rereads the approval and checks expiry immediately before atomic
`renameat2(RENAME_NOREPLACE)`, then fsyncs the parent. It never overwrites an
existing identity, including on retry. Partial hidden files are retained for
operator reconciliation; worker evidence and old plans are never deleted.

The result is consumed by the existing `ApprovedPrivateMountPlan` reader.
Publication is not physical launch acceptance: the FD launcher, immutable
source checks, active grant, current fence, profile, result reservation and
bootstrap checks remain mandatory. The ticket window limits issuance; it does
not change the lifetime/recovery semantics of the retained plan or revoke a
previously issued record. Automatic issuance is available through the opt-in root authority below; credential renewal remains separate work; the opt-in live
worker/operator handoff is described below. This change does
not activate that path or establish private native root/child acceptance.

Tests use disposable ordinary-user files, with explicit root authority and
clock doubles. They exercise the existing reader consuming the new record,
full identity/argv/FD bindings, expiry and late withdrawal, exclusive fresh
inodes, actual no-replace rename, retained failure files and FD cleanup.
They also verify actual worker publication/approval refusal. These tests do
not claim real privileged publication or a production issuer installation.

## Bounded live worker/operator handoff

Schema 2 may opt into `private_launch.plan_handoff` with exactly
`proposal_directory` (an existing canonical owner-only 0700 directory outside
all admitted writable roots) and integer `timeout_seconds` in 1..60. Only the
root-protected host policy chooses this configuration. Without the option,
missing approval retains the original immediate denial.

The existing root and child command preparation paths retain their FDs and
wait before any pane is created. A fresh 0400 proposal in the configured
directory records the complete plan/argv, grant hash, approved profile digest
inventory, process PID/start ticks and grant expiry. It contains no profile
file bytes; command environment literals are limited to the native builder's
public HOME/PATH/sandbox values. This directory is review evidence, not a
task queue or an approval authority. No proposal or failed hidden stage is
overwritten, replayed, renewed or deleted by the handoff.

An independent trusted operator/issuer must verify the physical descriptors,
current policy and approval, then use the root ticket publisher above. Never
copy a proposal into the root approval directory as its own authorization.
The operator must finish within the configured deadline and current grant
and credential window. An existing proposal for the same full identity after
crash requires reconciliation; allocate a new identity/fence only through the
existing durable admission path, never by this helper.

The waiting worker repeatedly checks the current host profile/parent policy,
unchanged grant/profile, sealed profile inputs, immutable runtime, workspace
pin and empty bound result slot. It rebuilds and compares the complete held
command, verifies stable proposal bytes/inode/links/modes, and accepts only the
existing exact root-owned plan reader. Malformed authority records deny;
only a missing record is waited for. These checks and the deadline run again
after the final approved builder returns and immediately before actual native
pane run after pane readiness/command serialization. Existing durable split/fence,
bootstrap, provider and economic gates still apply.

This implements coordinated waiting/consumption, not automatic approval or
credential/plan renewal. No daemon, timer, root installation or live worker
activation is included. Tests use explicit root-reader/runtime doubles and
disposable real memfds, reservations, inodes, fsync and no-replace rename;
one test runs the existing operator publisher concurrently with the waiting
worker. This is not a privileged native root-child-result acceptance claim.


### Hermes source verification without Git runtime metadata

Runtime publication excludes `.git`. Stage two now verifies the same signed
Hermes executor/source pin using `herdr/hermes_source_inventory.json` from the
immutable policy-code tree, bound by an exact SHA-256 constant in the launcher.
The inventory records the audited revision, version and 15,208 ordered tracked
paths; it was produced only after matching the existing clean revision and full
tracked-source digest. Every tracked regular file is hashed in the original Git
index order, so the executor digest is unchanged. Missing/changed files, path
aliases, changed inventory, unknown schema fields and untracked importable
sources fail before native import. No runtime Git command, hook, configuration,
index or object database is required. Site-packages, Python, immutable namespace
and bootstrap authority checks remain prerequisites in the production path.

The committed inventory is reviewed release code. Workers cannot provide one or
refresh its pin. SDK updates require a new audited source inventory, explicit
launcher/source/executor pins and the existing release publication workflow.

## Automatic issuance through the existing root plan authority

Private host composition may opt into `private_launch.plan_handoff.automatic_issuer: true`.
The option does not install or activate an issuer. Existing configurations keep
the operator ticket flow. The automatic client requests one exact plan, before
seal/pane/provider work, using a bounded Unix `SOCK_SEQPACKET` operation and real
`SCM_RIGHTS` descriptors. The existing root-owned ticket publisher and
`ApprovedPrivateMountPlan` remain the publication and consumption authorities.

The root-protected `/etc/herdr/launch-plan-issuer.json` has exactly:

```json
{
  "schema_version": "herdr-automatic-launch-plan-1",
  "host_policy_sha256": "<SHA-256 of canonical current host-policy JSON>",
  "host_cgroups": ["/system.slice/<existing-approved-host-service>.service"],
  "entrypoints": ["agent-stack/bin/agent-task-worker", "agent-stack/bin/agent-durable-bridge"],
  "request_timeout_seconds": 30
}
```

Only explicit non-delegated service cgroups are allowed, never a user slice or
an entire system slice. Their ancestry and migration controls must remain root
owned and non-writable by the service user. The existing host service must use
the approved immutable Python runtime and code release, with this invocation:

```text
<root-published-python>/bin/python3.11 -I -B <root-published-code>/agent-stack/bin/agent-herdr-host-entrypoint agent-stack/bin/agent-task-worker <existing-worker-arguments>
```

In opt-in automatic mode the existing dispatcher selects this pinned wrapper before claiming a pending task, and the worker starts its existing durable child bridge through the same wrapper. Both entrypoints must be approved. A missing/mismatched issuer policy, wrong UID or mutable caller release denies before the dispatcher updates the task. Schema-1 and manual configurations retain the existing invocation. Recovery uses the exact launch-time command, protected-policy digest, release source and kernel process start ticks retained in the execution session; it does not redefine an existing bridge under a later policy/release. An unverified live PID blocks termination/restart for reconciliation; exited/zombie processes do not block cleanup. All processes remain children of the existing host service; no additional dispatcher or queue is installed.

The wrapper protects the host process from same-UID ptrace/proc access before
running an existing approved entrypoint. It checks the current issuer-policy
pin, interpreter flags/path, and complete root-protected code/runtime manifests.
It does not start an agent, queue, scheduler, provider request, or alternative
admission authority. Only the configured existing entrypoints may run. They must
be compatible with the pinned interpreter and dependencies; verify that in the
new release before activation. Raw credentials are never issuer-policy fields.

The plan authority listens at `/run/herdr-launch-authority/issuer.sock` and transfers
exact approved native descriptors through `native-fds.sock` in the same root-protected
directory. One serialized issuance worker and up to 16 independent descriptor
receivers serve inside the existing authority process. Waiting connections use only
the existing bounded kernel socket backlog; there is no additional queue or authority. UID equality is insufficient: it verifies kernel
connection and per-message credentials, PID/start ticks, non-dumpability, exact
service cgroup, host mount/PID/user/cgroup/network namespaces, approved launcher
argv and actual interpreter inode. Sandbox callers, mutable checkouts, unrelated
same-UID processes and transferred connections from another PID are denied.
The issuer and existing host service must share the host namespaces; configure
neither service with a conflicting private mount/user/network namespace.

Each request binds the current root host-policy digest, full invocation/fence,
active grant under the existing consumer ceiling, optional active parent grant,
unchanged profile credential window, exact proposal evidence and complete actual
FD inventory. Real sealed profile memfds must match root-approved hashes. Code,
SDK and Python must match the complete immutable root-published manifests and
inodes. The bundle remains an empty pre-seal slot, bootstrap transport matches
approved entrypoint bytes/proof, and the result must be the exact empty reserved
inode with no previous delivery intent. Writable directories remain within the
host grant. Native command grammar, private masks, public environment and FD
mount roles are checked independently. Current host parent/bootstrap/fence and
work-policy verification remain mandatory in the existing launch path.

The authority creates a fresh root-owned 0400 issuance ticket, rechecks the peer,
policy, grant and sources before its no-replace publication, then calls the
existing 0444 plan publisher with the same live recheck immediately before the
plan's atomic no-replace publication. Existing tickets/plans are never replaced,
renewed, replayed or deleted. A failed unpublished stage is removed only when it
is still the exact inode created by that call. A visible approval or plan with
ambiguous publication retains bounded custody for exact reconciliation; a lost
response never authorizes reissuance or a new economic attempt.

Client and server share the fixed transmitted request deadline. Binding ends at
that deadline plus the configured handoff window, capped at grant expiry minus
15 seconds. Descriptor custody survives for that fixed window plus a 15-second
dispatch/redemption reserve, never beyond grant expiry. Descheduling cannot reset
these windows. Manual handoff keeps its original single deadline. Root/current
peer, grant/profile/source, signed mount plan and bound host checks remain
mandatory. A successful descriptor send consumes custody before the syscall;
late issuer cleanup cannot resurrect it. Per-set inspection ownership prevents
expiry/cancellation from closing another thread's held descriptors or allowing a
cancelled set to send. No command is executed by the root descriptor authority.


Root operator preparation for a separately approved deployment:

1. Publish the reviewed new code/runtime closure and updated host policy. The old
   publication bundle is not this new source version and must not be reused.
2. Approve the exact existing host service cgroup(s)/entrypoint(s), pin the new
   canonical host policy, and create the root-protected issuer configuration,
   approval/plan directories and `/run/herdr-launch-authority` directory.
3. Start `scripts/serve-herdr-launch-plan-issuer.py` from the immutable release
   with its approved interpreter, `-I -B`, and the necessary root authority.
   Never execute a mutable worker checkout as root. An existing socket requires
   explicit reconciliation; this helper never unlinks it automatically.
4. Configure the existing host entrypoint wrapper and opt-in handoff; verify a
   real zero-provider root/child/result flow, then the existing canary, recovery
   and soak requirements before autonomous activation.

Source implementation and disposable tests do not establish privileged native
acceptance. Test root ownership, service admission and credential/interpreter
authority doubles are recorded explicitly. No service installation, root write,
provider call, budget change or deployment is performed by these tests.

Linux interfaces: [Unix credentials and descriptor passing](https://www.man7.org/linux/man-pages/man7/unix.7.html),
[non-dumpable process ownership](https://www.man7.org/linux/man-pages/man5/proc_pid.5.html),
[cgroup v2 migration permissions](https://cdn.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html).


### Isolated host dependency imports

The host entrypoint runs the approved Python with `-I -B`. That interpreter does
not automatically use Hermes venv packages; host grant creation needs
`cryptography`, and worker policy configuration needs `yaml`. After verifying
the exact two approved runtime targets and every immutable tree, the wrapper
adds only the approved Hermes `venv/lib/python3.11/site-packages` directory.
Approved code and sibling-script imports retain precedence. The selected Hermes
dependency directory precedes default interpreter site-packages, so duplicate
packages in that default directory cannot replace the selected dependencies.
It keeps isolated interpreter, code and sibling-script imports and does not
process `.pth` files or run `sitecustomize` hooks from the added directory.
A missing, aliased, unapproved or withdrawn runtime denies before the entrypoint
runs. Dependency import tests use explicit root-policy/fixture-tree doubles;
they do not establish native issuer, bootstrap or deployment acceptance.

### Compact retained executable inventory

Private launch proofs keep their 16 KiB frame limit. Complete runtime executable
path lists can exceed that limit before profile and bootstrap metadata is added.
New `herdr-immutable-sources-2` evidence binds an `executable_inventory` for each
code/SDK/Python source: exactly `sha256` and integer `count` (0 through 65,536).
The digest is SHA-256 of canonical JSON for the sorted executable relative names.
These commitments remain part of the signed sandbox attestation and grant.

Cold replay still checks root-owned ancestry, directory inode, complete content
manifest, approved bootstrap bytes and exact mounts. While walking every file,
it requires execute bits to be either all set (0111) or absent, collects the
actual executable names, and compares both their digest and count with the
retained signed commitment. A same-count mode swap, rename, addition, removal or
partial execute permission is denied. A compact source cannot omit its inventory,
contain a raw path list, or mix both representations.

Readers continue to accept bounded `herdr-immutable-sources-1` evidence and its
exact path-list mode checks. An old source with unknown executable metadata keeps
the legacy format; it cannot claim compact mode without an inventory commitment.
No frame, file-count, source-size, signature, authority or grant limit is enlarged.
