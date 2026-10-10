# #129 â€” Root-published immutable Hermes / Python execution trees

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
