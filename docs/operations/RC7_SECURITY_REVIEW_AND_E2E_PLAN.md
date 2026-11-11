# Herdr RC7 — P0 network/security review and zero-provider E2E acceptance

**Date:** 2026-11-11
**Baseline:** draft PR #225 / existing RC6 remains unchanged
**Status:** SECURITY_STOP / NOT_READY_FOR_ROOT_PUBLICATION

This is an independent *read-only technical review of the observed code and
physical smoke probe*, not an independent third-party security approval.
All effects and deployment remain blocked pending exact-head review and host
operator authorization.

## Verified P0 findings

### P0-1 — Shared host network namespace in private Hermes sandbox

`agent-stack/bin/agent_durable_sandbox.py` intentionally retains host netns:
the existing abstract AF_UNIX delegation bridge is network-namespace scoped.
The private Bubblewrap command does **not** require `--unshare-net`.

Physical staging smoke test: parent only listened on ephemeral
`127.0.0.1`; a child Bubblewrap namespace sharing host net connected and
delivered `HERDR_SAFE_LOOPBACK_PROBE`, exit 0. Repeating with
`--unshare-net` denied the connection, exit 1. No internet or provider contact.

**Impact:** a plugin, imported HTTP client or child process can bypass SDK
`host_reference` checks and emit packets while the namespace is shared.
Hermes Python globals are mutable by arbitrary in-process Python code;
their one-way deny flag is only defense in depth. A failed network gate
MUST prevent even a zero-cost provider from being called.

**Immediate code mitigation in draft PR:** stage2 calls the origin-verified
`herdr.host_reference_egress.require_network_isolated_host_reference(grant)`
AFTER checking the authenticated host grant/profile and BEFORE arming the
SDK reference or importing Hermes CLI. It denies global/untyped network
assurance, unverified sandbox or missing assurance. This deliberately
**blocks current private host-reference activation** until redesign.

**Required structural repair:** move delegation/model-effect authority to
one host-owned broker reachable without sharing host network namespace,
using an independently verified pathname AF_UNIX socket with pinned inode
and peer credentials or a preconnected bounded FD channel. Recheck SCM_RIGHTS,
path length, SO_PEERCRED, peer start ticks and PID/fencing identity. Ensure the
broker alone can contact providers and only after exact reserve/charge/settle
checks. The child must not have host network, bearer keys or writable broker
configuration. No generic network proxy may be exposed as ambient authority.

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

- **BLOCKER:** P0-1, P0-2, P0-3, P0-4 are open.
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
