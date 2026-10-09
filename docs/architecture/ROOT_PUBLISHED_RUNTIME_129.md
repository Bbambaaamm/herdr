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

The existing P1 reviews of draft PR #131/#134 involving FD aliases,
literal-bind TOCTOU, writable credential paths and alternate mount
destinations remain separate blockers. They must be resolved before
private-HOME activation, alongside an isolated native Hermes
zero-provider test, exact-head CI/security review, signed rollback,
#78 E2E and #53 durable delivery reconciliation.

## Status

**Verified root-ownership enforcement and physical proof only.**
Parent #129 and child #132 remain OPEN. Production RC26, the queue,
leases/fences, credential sources and cumulative budgets are untouched.
