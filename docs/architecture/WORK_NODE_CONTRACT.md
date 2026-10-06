# Bounded work node contract (#86)

A persistent Hermes parent selects work; a Herdr node implements one approved
repair and ends. This contract uses the existing scheduler AuditLog, worktrees,
ArtifactRef and shared #85 completion gate. It introduces no queue, scheduler,
push/merge/deployment authority or TASKS.md.

## Authority before implementation

The host freezes WorkPlan (version 3 when a commit profile is bound; historical
versions 1/2 retain their original encoding): full admitted invocation identity,
specification version/digest, exact base commit, file/symbol scope, criteria,
immutable check argv and protected verification inputs, granted authority digest,
actual environment digest, budget reference, purpose, stop condition and mode.
Every criterion has an approved check. The host must approve baseline omission
policy and its reason explicitly. An expected baseline failure requires exit 1
and a predeclared output fingerprint. Unrelated baseline failure records a
blocker and never authorizes an extra repair.

Start requires the exact clean base and prerequisite commits as actual ancestors.
A DONE label cannot substitute for an integrated prerequisite. No dirty input is
reset, stashed or silently amended. Python symbol scopes reject duplicate symbols,
changed file modes and unsupported languages rather than pretending to confine
them. Protected verification inputs cannot be edited to obtain PASS: a legitimate
test change needs an independently reviewed new host plan and new evidence.

## Actual check environment

The initial CheckEnvironment implementation supports offline single-process
validation. HostCheckRunner copies bounded physical input bytes into a private,
independent FrozenTree and mounts the retained inode read-only at /workspace.
The original repository, home, runtime grants, credentials and inherited
environment are absent. The host approves executable and system-input hashes.
Mount/PID/network namespaces are checked physically before the command runs.
Seccomp denies all socket/io_uring networking, process creation and mount/namespace
escape syscalls. Root/system/workspace/dev mounts are read-only; only private
/tmp scratch is writable, with a finite tmpfs size. CPU, address space, file size,
open descriptors, wall time and captured output are bounded.

This profile deliberately rejects network-enabled or subprocess-enabled checks.
Preparation, implementation/model execution and validation have separate access
needs. A future host-approved profile must prove additional needs rather than
silently relaxing this one. Missing bwrap/seccomp/attestation blocks the check.
Check receipts bind the plan, environment, tested tree, physical isolation,
exit code and bounded output digest. Limit exhaustion is preserved as failure;
truncated output cannot become PASS.

## End, commit, recovery and ownership

The cycle moves PREPARE -> DISCOVER -> PLAN_GATE -> WORK -> VERIFY -> HYGIENE
-> HANDOFF -> FINISHED. Discovery records targeted inspected bytes/symbols,
facts and UNKNOWN areas. PlanArtifact binds outcome, constraints, criteria,
hard/soft oracle dimensions, proportional TeamPlan, advisory runbook/orientation
and prompt references. Material missing intent emits INFO_REQUIRED before work.
PASS ends model implementation. WorkInvocationGuard checks host phase authority
at provider and tool invocation seams. Host-controlled hygiene/validation and
review continue outside model implementation. Hook/content changes invalidate
test proof and return to VERIFY without bypassing hooks. Commit handoff verifies
the sealed ArtifactRef, committed raw Git bytes and the same physical tree that
passed the approved checks.

The existing worker uses a host-admitted work_contract_version=1 envelope.
Before Hermes starts, HostWorkContractFactory binds the signed grant and runs
baseline. Actual root and version-2 coding-child admission require both the
closed herdr_verify_work capability and the original bound result slot, plus
a host-approved LocalCommitPolicy, before baseline effects. Missing authority blocks before pane creation. The actual guarded SDK requests the frozen oracle through the authenticated
bootstrap Unix socket. SO_PEERCRED, process start/interpreter, full identity,
grant and physical mounts are checked before and after the request. The stable
request is persisted before effects; interruption stays UNKNOWN and cannot be
renamed into another verification. PASS blocks ordinary tools/providers and
the same tool submits the exact host-directed local candidate. Shared #85 then
collects exact-head independent review/CI. Only its accepted immutable bundle
ends handoff. A null PR reference waits for one exact same-repository/head/base
PR association through read-only GitHub collection; it grants no publication
authority. The original candidate is immutable throughout this wait.

Normal repository hooks run in a disposable offline Git environment, with
read-only config/hooks/original objects, private 128 MiB work tmpfs, bounded
output/time/memory/file sizes and a kernel process limit under an unprivileged
namespace UID. A hook cannot edit live metadata, disable another hook or read
host credentials. Changed content invalidates the old PASS. Only validated
content-addressed objects, the exact owned branch and original index are
published with durable Git lock/CAS operations. Pre-existing staged work blocks
publication without changing it. Restart restores the existing audit events, reuses the commit and
accepted bundle, and never redispatches finished work. A protected observation
of the original physical SDK request precedes oracle/commit effects. After
SDK loss, root and child recovery derive the exact candidate from that original
observation, passed checks, frozen declaration, sealed artifact and pinned
result inode. They do not start a model or repeat hooks. Accepted handoff recovery
does not require recreating a removed environment or artifact workspace.

Rollback has no generic reset/clean operation. A host authority must attest
exact owned edit digests and a quiesced writer. Changed ownership, symlinks,
staged/committed work or unsupported deleted-file restoration blocks rollback.
Only those attested paths are restored; unrelated human files are preserved.
Snapshots are removed only after the owned check process group has exited.
Evidence stays in the existing host audit/completion store.

## Modes and composition

REPAIR is the default for new bounded nodes. EXPERIMENT fails closed until #74's
explicit finite-series authority is configured. Mode, purpose and budget binding
survive restart. Completing a repair cannot promote it into an experiment.
Phase templates are ordered and proportional: a small repair needs WORK,
VERIFY and HANDOFF; discovery/architecture/data-model/release steps are optional
when appropriate and do not imply extra agents. Release prepares an exact
artifact; deployment remains separately authorized.

Historical envelopes retain their original counter/specification meaning.
#87 owns evidenced repair reopening and cumulative limits. Actual root/child
worker ports and guarded SDK phase IPC are part of this change; #78 remains
the owner of later joint deployment/E2E acceptance. No live activation, provider
spend or production configuration change is performed by this delivery.

Protected host configuration supplies work_contracts version 1 with exact
specification-keyed definitions, CheckEnvironment, accepted prebuild-review
sources and local commit profile. A required prebuild review must be an
accepted exact-contract/base report from another implementation agent; it
cannot replace post-build CI/review. Child completion catalogue version 2
explicitly marks coding work_contract_version=1; catalogue version 1 remains
historical. New standalone Herdr coding intake receives the work-contract
marker; missing configured authority blocks execution. Unsupported experiments,
network/subprocess check profiles and richer commit config require separately
implemented/approved profiles and are not silently relaxed.

### Exact runtime closure and early admission

Checks and commit hooks receive only the host-approved `CheckEnvironment.system_files`.
Every file is hashed, copied into host-private storage, and bound individually
read-only from its retained directory descriptor. `runtime_aliases` and
`runtime_executables` explicitly bind loader paths and executable helpers; an
unlisted file beside an approved library is absent. No entire host library
directory is mounted. This basic profile requires an explicit bounded runtime
closure; it does not discover or approve new dependencies in production.
Namespace startup has a separate finite ten-second bound. The declared oracle
wall deadline begins after the bootstrap attestation; recorded duration includes
startup. Cleanup follows process-group exit.

Repository configuration is closed: approved author, line-ending/comment and
commit-cleanup settings plus supported structural defaults are reproduced.
Unrecognized settings, including hook-specific flags, require an approved
richer profile and block before hook/ref effects. They are never silently
discarded. Hooks can execute only helpers in the same approved closure.

Modern child work preflight verifies protected work/hygiene/result capabilities
before pane split. Baseline and final physical binding still occur in their
proper later phase. During WORK, `herdr_submit_result` is denied so an arbitrary
early payload cannot pin the completion slot. Host verification/hygiene produces
the bound handoff before the SDK submits it. Oversized handoff requests and
truncated host responses become bounded policy denials.

Capability preflight has two stages. Root and child entrypoints verify the
approved hygiene profile and closed verify/result rules before splitting a pane.
The result slot is still unbound at this stage. After the host allocates its
attempt-specific inode, strict preflight requires the physical slot before
baseline or SDK startup. Logical parent-ceiling comparisons omit the old slot
from the synthetic comparison identity; the original parent's physical proof
and grant remain unchanged and separately verified.

The aggregate verification/hygiene admission limit includes thirteen seconds
per namespace operation for bounded startup and process exit, as well as every
declared execution timeout. A request exceeding 900 seconds is rejected.
Repository-config parsing retains the approved config inode, verifies its
content hash, and checks inode/content/timestamps after the separate read-only
Git parse. Replacement, in-place mutation and restore-to-the-original-byte
races all stop before hooks or ref effects.

The worker and watchdog share receipt-backed root completion verification. A
host-produced version-2 result does not need a model-supplied artifact workspace;
cold recovery supplies the original admitted workspace and invocation proof and
does not restart an SDK. Final Git index publication retains the bytes already
validated before object/ref publication as its CAS expectation, preserving late
foreign staging. Physical scope inventory includes Git-ignored paths, including
their deletion and newly created ignored files. Ignored-path admission is finite
under the same file/byte/nofollow bounds; oversized or special inputs block.

Proof duration includes the approved 10-second namespace startup and bounded exit
allowance: per-check admission and replay use timeout plus 13 seconds. The sealed
SDK handoff transports a check count and the original check-evidence digest; full
check proofs remain in the protected verification receipt. The exact candidate
shape is bounded before oracle/commit effects. The registry consumes required
one-shot tool approval once; its internal verification rechecks without consuming
the same approval again.

Work IPC uses the same compact UTF-8 canonical encoding as candidate preflight,
including non-ASCII scope narratives. Grant admission reserves the existing
signed lifetime for the complete bounded baseline and verification/hygiene
request; the socket checks the full remaining request interval before effects.
No lease or grant extension is inferred. Cold receipt recovery stays available
through the protected host path after SDK authority expires.

Known hook content invalidation can open a new immutable verification intent in
VERIFY when proofs are cleared and verification is explicitly reopened. It
cannot reuse the original PASS as a new check or silently submit modified bytes.
Unknown original hook/commit delivery still requires original evidence and does
not authorize repeating hooks.

Host request bounds now include a 120-second allowance for inventories, private Git construction, publication and receipt capture. A monotonic request deadline covers the complete protected callback; local reads, Git commands and publication gates consume that deadline. Admission never extends the original signed grant. Direct model result submissions stay denied in every work phase; only the verification handler opens an exact-payload internal submission context. Proven hook content invalidation retires its original private commit request; UNKNOWN delivery remains held. Formatter content promotion is not automatic.
