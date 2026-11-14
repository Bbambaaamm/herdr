# Herdr RC7 — P0 network/security review and zero-provider E2E acceptance

**Date:** 2026-11-11
**Baseline:** draft PR #225 / existing RC6 remains unchanged
**Status:** SECURITY_STOP / NOT_READY_FOR_ROOT_PUBLICATION

This is an engineering review of the isolated candidate and physical
smoke probe, not an independent third-party security approval.
All effects and deployment remain blocked pending exact-head review and host
operator authorization.

## Verified P0 findings

### P0-1 — Private Hermes network namespace (candidate repair)

Historical RC6 shared the host network namespace. The draft candidate changes
`agent-stack/bin/agent_durable_sandbox.py` to require exactly one `--unshare-net`
for private-profile launches, enforced at command generation and by the closed
FD-launcher grammar.

The actual host WorkAuthorityClient uses a **pathname AF_UNIX** socket at
`/run/herdr-policy/bootstrap-authority.sock`, not an abstract socket. This
socket can be mounted via pinned read-only FD across separate net namespaces.

Physical staging smoke test: parent only listened on ephemeral
`127.0.0.1`; a child Bubblewrap namespace sharing host net connected and
delivered `HERDR_SAFE_LOOPBACK_PROBE`, exit 0. Repeating with
`--unshare-net` denied the connection, exit 1. No internet or provider contact.

**Impact:** a plugin, imported HTTP client or child process can bypass SDK
`host_reference` checks and emit packets while the namespace is shared.
Hermes Python globals are mutable by arbitrary in-process Python code;
their one-way deny flag is only defense in depth. A failed network gate
MUST prevent even a zero-cost provider from being called.

**Physical candidate evidence:** a fixture-only host Unix listener was
exposed to a private net namespace through a pinned read-only socket FD.
The child connected successfully and the host verified the authentic
`SO_PEERCRED` PID/UID/GID. The child's TCP connection to the parent's
`127.0.0.1` listener was denied, including from a subprocess. No provider calls.
A malformed-launch regression denies missing or duplicate `--unshare-net`
even when the test approval plan is recomputed for the malformed command.

A second physical test runs the **real** `WorkAuthorityClient` inside the
isolated user/PID/network namespace, passing its exact canonical
`work-authorize` tool request to a pinned pathname AF_UNIX fixture broker.
The fixture verifies the identity, digest, method and `SO_PEERCRED` before
returning `work-ok`. Child host-loopback TCP remains unavailable.

A third test invokes the **real** `dispatch_work_connection` on a host
thread with a prepared `HostWorkContractFactory` and a real child process
identity observed using `inspect_peer` across the network namespace.
The signed-grant/tool authorization succeeds once; a subsequent request
with the wrong grant SHA-256 is rejected. The host mount verification
entrypoint is a fixture adapter, **not** root-owned native
`PolicyMount.verify_mounted`. This confirms dispatcher and client IPC, but
not production `HostBootstrap` continuation, root launch plan, exact
mounted tree attestation, or durable result acknowledgment.

**Independent admission guard:** stage2 checks the origin-verified
`herdr.host_reference_egress.require_network_isolated_host_reference(grant)`
AFTER authenticating the grant and BEFORE arming SDK references or importing
Hermes CLI. Global/unverified network assurance is denied. Immutable RC6
remains unchanged and blocked.

**Still required before network acceptance:** prove the full root-owned
broker protocol (stage1, stage2, work budgets, parent-child ownership and
durable result) works after net namespace isolation, not only a test socket.
Recheck pinned inode, `SO_PEERCRED`, peer start ticks, fencing, `SCM_RIGHTS`,
socket revocation and replay. Keep model egress exclusively in the host broker
after exact reserve/charge/settle. The child must not receive host network,
bearer keys, writable broker configuration or a generic TCP proxy. Complete
IPv4/IPv6, UDP/DNS, plugin and grandchild egress denial tests.

### P0-2 — Insufficient proof of direct/provider effect coverage

`agent/auxiliary_client.py` and raw SDK/plugin clients need a kernel-level
barrier, not just SDK call-site checks. The draft SDK patch gates common
sync/async/stream/factory entrypoints and prevents inherited subagents,
but modules can be reimported, monkeypatched, or called via other libraries.

**Acceptance:** network-isolated child and all descendants fail to contact
parent localhost TCP (IPv4 and IPv6), resolved DNS, network interfaces and
any public endpoint without a model call. The same fixture verifies an
authorized FD/Unix broker exchange, identity/permissions/budget and a durable
result; external network never becomes available in the child. Denials must
not create a request reservation or charge.

### P0-3 — Pinned Hermes source mismatch and incomplete release provenance

RC6 pinned source inventory requires `agent/host_reference.py` which is absent
from historical root-owned Hermes and upstream commit
`ee5ee84a345204a3b1d6ef6ba1ab747e602867b9`. Draft PR #225 carries
a candidate external SDK source patch, **not** an upstream-reviewed release.
A release cannot be called ready until there is one exact, independently
reviewed Hermes commit, signed inventory and matching stage1/stage2/executor
hashes. The previously observed six uv.lock-vs-historical version drifts
must be explicitly reconciled.

### P0-4 — Incomplete authorization and physical result continuity

Protected host-policy remains schema 1 and the real root-owned runtime
publication has not been approved. RC6's integrated physical Hermes probe
failed, whereas a standalone frozen-Python smoke test passed. A previous
temporary continuation alone was insufficient evidence of accepted completion.

**Acceptance:** one authorized zero-provider native root -> managed child ->
durable result -> parent acknowledgement scenario, verifying exactly once
ownership/fencing, no model calls, no provider credentials, capped budget,
no policy bypass, immutable origins, pre/post identity verification and
replay after intentional interruption.

## Exact-head review disposition

- **BLOCKER:** P0-1 is mitigated in the isolated candidate with a
  physical FD-mounted Unix socket/TCP smoke test but not accepted for native
  root-owned broker E2E; P0-2, P0-3 and P0-4 remain open.
- **Candidate code checks:** targeted unit/contract suites may pass while the
  OS isolation remains unsafe. They cannot waive a kernel or root gate.
- **Review must be external to the code author** and record explicit
  APPROVE/CHANGES_REQUESTED on the exact PR head. CI success alone is not
  an approval.
- **No merge, publish, live provider call, autonomous queue or schema2
  activation** based only on this review.

## RC7 execution sequence and gates

1. **P0 network-bridge design review:** specify broker IPC, namespace,
   peer authentication, inherited FD lifetime, zero ambient host networking,
   cancellation and bounded recovery. Record threat model and review.
2. **Implementation in isolated branches:** complete kernel-level egress
   isolation; connect broker with explicit per-task grant; add missing
   negative tests for subprocess, alternate Python HTTP stack, IPv4/IPv6,
   DNS, local TCP, Unix broker spoofing, FD replay and hard kill.
3. **Hermes provenance:** freeze exact reviewed Hermes fork commit; verify
   full Python/NPM source and generated artifacts; choose/reconcile extras
   and six version drifts; review install/build scripts and Nix closure.
4. **Exact-head evidence:** targeted and full regression tests, GitGuardian,
   pinned source preflight, security reviewer decision, tree hashes, signed
   manifests and documented rollbacks all PASS; no unresolved P0 findings.
5. **Release build (not yet authorized):** from an operator-reviewed
   annotated RC7 tag and exact commit, use
   `scripts/build-herdr-release.py`, verify with
   `herdr.release.verify_tree`, archive SHA256 and immutable root ownership.
   Never synthesize approval or reuse RC6 request/manifest as if it covered
   the new Hermes bytes.
6. **Protected host policy:** separately approved root-owned schema-2 policy,
   exact pinned code/Hermes/Python closures, launch plan and independent
   review; no host mutation from a scratch branch.
7. **First zero-provider physical E2E:** no provider credentials/model request;
   run one root -> child -> durable-result case with bounded budget and
   read-only sandbox; verify admitted namespace/net/UID/mount/FD source,
   receipt ordering, ACK and parent replay. Inject faults: revoked grant,
   stale fence, missing bundle, changed inode, unavailable broker, socket
   replay, resumed child and interrupted parent.
8. **Canary and rollback:** only after explicit operator GO. One managed
   job, fixed expiry, no hidden retry or broadened permissions. Validate
   audit evidence and rollback to the known verified RC6 when requested,
   without accepting the old unsafe host-reference behavior.

## Measurable GO/NO-GO checklist

- [ ] No child or grandchild can create unauthorized IPv4/IPv6 or DNS egress.
- [ ] Host IPC uses independently attested pinned FD/path + peer identity.
- [ ] All model effects are reserved by host authority; no direct SDK/plugin
      path can send requests.
- [ ] Exact reviewed Hermes commit and Python/JS provenance match manifests.
- [ ] Root preflight/ownership/immutable schema2 verified and authorized.
- [ ] Complete native zero-provider E2E with durable parent result PASS.
- [ ] Negative tests, replay and rollback evidence PASS.
- [ ] Exact-head CI and **independent** review accept all P0 fixes.
- [ ] Operator explicitly authorizes privileged publication/canary.

**Current verdict: NO-GO.** These are future gates, not completed milestones.


## 2026-11-13 — Integrated zero-provider candidate evidence and hard stop

A new physical test, `tests/herdr/test_real_dispatch_mount_cross_netns.py`,
combines these operations in a **single fixture-owned run**:

1. A Bubblewrap child is isolated with separate network, user and PID
   namespaces, no capabilities, and four exact source FD-mounted policy trees.
2. The host calls the real `PolicyMount.verify_mounted(pid)` against the
   child's `/proc/<pid>/mountinfo`, verifying the grant file, policy-code,
   Hermes and Python tree inode identities and read-only mount rows.
3. The child uses the real `WorkAuthorityClient` through an FD-mounted
   pathname AF_UNIX socket. The host calls real
   `dispatch_work_connection` with `inspect_peer` verification of process
   start ticks and executable inode, then authenticates the work contract.
4. Correct work authorization succeeds; a second request using an incorrect
   grant hash is denied.
5. The sandbox child writes a bounded test result into a dedicated writable
   workspace mount. The host runs real contract verification and artifact
   sealing, persists a handoff event and reconstructs the finished work
   cycle from the append-only host audit ledger, without re-planning.
6. No provider call, model key, live issue execution, root publication,
   service restart or production queue mutation is performed.

This is **integrated physical fixture evidence**, **not accepted production
root-owned stage1 -> stage2 -> managed child -> parent ACK E2E**. It uses
temporary non-root-owned, unsigned/synthetic FrozenTrees and bundle source;
the full signed `HostBootstrap` continuation, root-owned private mount-plan
authority and real parent result publication transport are not exercised.
A test-only broker wrapper supplies the authentic work grant and calls
the actual mount verifier; it is not itself the root-owned HostBootstrap.
Its initial host filesystem view is a fixture read-only bind, not the
complete approved private HOME layout.

The official physical bootstrap probe now calls
`herdr.hermes_preflight.preflight_pinned_hermes_source` before any expensive
source snapshot. On the actual installed checkout, it exits **1 / blocked**
with `PINNED_HERMES_SOURCE_FILE_MISSING: agent/host_reference.py`. This is
a desired fail-closed result, not a passed stage1/stage2 chain. The source
preflight is presence-only: all later byte hashes, immutable inodes, root
signatures and launch-policy checks are still mandatory.

**Disposition remains NO-GO.** First finish the independently reviewed
exact external Hermes commit, root-published stage1/stage2 code/manifest,
approved schema-2 host launch policy, secure private HOME mount and broker
proof; then run official native root -> child -> durable result -> parent
ACK/replay with all negative controls. Never call a model or bypass the pin
for the sake of a green test.


## 2026-11-14 — Exact Hermes source and lock-reproduced venv candidate

Draft PR #225 adds a **new, non-deployable** Hermes runtime pin candidate,
fully documented in `docs/operations/HERMES_RUNTIME_PIN_CANDIDATE_132.md`.
The verified SDK source commit is `ef0342358f6421efb4ce919ba859d69940ca13b7`.
The complete 1,821-file source digest is
`d0bd4e3e6023166b3feed4b3fc47ac811d9453476866c8c5e4319bf1038f02fa`,
and the lock-reproduced 108-dependency venv surface digest is
`d986a36b26e4a57ce5a89fca094843c98b10f8d73c9185f95c09cb1da4172330`.
Both passed the **actual** stage2 source/site verifiers. The new executor
identity is `hermes:0.21.5:sha256:28cbd35dd0e7d738a321becce73eb05c91f269ac1c821e0e2adbfefd5b313b4b`.

The earlier 1,249-file inventory omitted 572 Git-tracked Python files
from declared runtime packages including `hermes_platform`, `plugins`
and `gateway`. A first import in isolated netns failed. After adding
exact candidate-commit sources (without test/developer .py files), the
real `run_agent.AIAgent` and `hermes_cli.main` imported successfully
in no-network safe mode. A lockfile venv compatibility check found
108 compatible external distributions. See the machine-readable read-only
audit `docs/evidence/hermes_runtime_candidate_132.audit.json`.

A preflight against the unchanged historical installed Hermes still fails
**as intended**, before runtime snapshotting:
`PINNED_HERMES_SOURCE_FILE_MISSING: agent/host_reference.py`.
This protects RC6 from adopting the new identity without an approved
runtime. The CLI `--version` attempted through an uninstalled-project
candidate did not provide a reliable terminal completion; no successful
full native CLI startup is claimed.

**Remaining release blockers unchanged:** independently reviewed and
root-published Hermes/Python closure, project wheel and asset provenance,
exact signed executor inventory, full host-bootstrap continuation,
stage2 admission, durable managed-child parent ACK/replay, root-owned
schema2 publication authorization, full negative kernel/plugin tests and
independent exact-head security approval. No RC7 tag, deployment or
provider/model call was made.
