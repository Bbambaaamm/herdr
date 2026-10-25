# Parent publication of verified local results

A bounded coding node finishes implementation at local PASS. The existing host
oracle, hygiene and WorkResultAuthority produce a sealed commit and an immutable
result observation. Opening a GitHub pull request belongs to the parent host;
it is not a new worker tool, work phase, task queue, scheduler or merge authority.

## Parent port

ParentArtifactPublisher in herdr/parent_publication.py consumes:

- an explicit host ParentPublicationPermit binding the full original attempt,
  repository, specification/plan hashes, base SHA/branch, result branch and expiry;
- the original HostWorkContractFactory and WorkResultAuthority observation;
- a private EvidenceStore outside every worker write root;
- a parent transport for remote observation, one branch push and one PR creation.

A fresh publication requires HANDOFF. It cannot run an oracle to turn WORK into
PASS, start an SDK, allocate another model call, reroute the executor or change
the result payload. The original launch/result observation and committed bytes
are checked before publication. The commit carries the existing immutable
verification footer. Publication does not produce a semantic acceptance bundle.

scripts/publish-herdr-parent-result.py is a parent host command. Its --permit
argument points to a root-owned, no-follow configuration with this closed shape:

    {"version":1,"permit":{...ParentPublicationPermit fields...},
     "transport":{"gh":"/approved/guarded/gh","home":"/parent/home"}}

The configuration must come from existing host approval, not task JSON or SDK
arguments. The command runs under the ordinary trusted host UID, reads the
canonical task and original result, and uses the existing worker's protected
cold work-cycle recovery. --inspect checks configuration only and performs no
remote or model operation. No configuration file or service is installed by
adding this code.

The parent invokes this command after local handoff. It leaves the original
null PR reference untouched. The ordinary worker/watchdog then discovers the
exact same-repository/head/base/approved-branch PR and reconciles CI/review on
the same attempt. Installing a parent command alone does not prove a live
parent/worker cycle or activate the command in an existing deployment.

## Publication and reconciliation

Publication records are immutable, namespaced plan records in the existing
host evidence store. A nonblocking host-private lock serializes attempts at the
port; it is not a second queue. Addresses bind the original identity and plan,
so renewing/replacing a permit cannot reset an UNKNOWN effect.

1. Validate the original local result and observe exact remote base/head/PRs.
2. Export a bounded incremental bundle through the existing read-only,
   network-isolated Git verifier.
3. Persist a push intent before the parent transport creates the absent branch.
4. Observe the exact remote head, persist a PR intent and create one PR.
5. Observe one exact open PR and persist the publication receipt.

A lost reply is reconciled by reading the original remote state. An unobserved
push or PR creation with an existing intent is UNKNOWN and is never repeated
automatically. A different base/head, ambiguous PR set, changed local result or
changed permit stops publication. A valid stored receipt replays without a
workspace, network access or a live SDK, including after permit expiry. It
records a historical publication, not current CI/review acceptance.

The port performs no merge, deployment, task-DONE transition or model work.
Existing #85 acceptance, scope checks, independent CI/review and cleanup remain
authoritative. In particular, this does not release an unrelated UNKNOWN model
reservation or reset any work budget.

## Parent GitHub transport

herdr/parent_github_transport.py uses the parent-selected guarded gh executable
and existing parent login. No credential is copied into the worker environment,
result payload, bundle, public PR body or transport log.

Credential-bearing Git runs only in a new private bare repository, with system
and global Git configuration disabled, no checkout, blank templates and disabled
hooks/fsmonitor/submodule recursion. It imports the approved base from the fixed
same-repository HTTPS origin and the exact local bundle. The imported result must
have the approved commit SHA and exactly the approved base as its one parent.
This transport profile deliberately supports a single host-committed work node.

The remote result ref is created with an empty expected-ref lease. An existing
different ref cannot be overwritten. API paths/repository and PR base/head are
host bound. Client output, elapsed time, process memory/file sizes and child
process lifetime are bounded. Temporary bare objects are derivative copies;
the original workspace and evidence remain subject to existing retention.

Tests separate real oracle/Git/receipt and bundle-import checks from explicit
GitHub transport fixtures. They exercise lost replies, changed bindings,
concurrent callers, expiry, UNKNOWN preservation, independent bare import and
client/credential-helper cleanup. These are component proofs, not a claim of
production rollout or completed autonomous implementation.

