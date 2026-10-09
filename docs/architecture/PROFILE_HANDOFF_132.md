# Issue #132 — host-authorized profile handoff (draft, not activation)

## Why this exists

The original root/child launch paths took their model SDK profile directly
from the existing host filesystem, while PR #131 introduces write-sealed
memory snapshots under an immutable readonly private HOME. The live RC26
server and blocked root task #53 have **not** changed.

## Implemented, fail-closed opt-in route

- `HostPolicyLaunchFactory` can receive one **typed host-owned**
  `ApprovedProfile(name, source, exact SHA-256 manifest)`. The manifest is
  copied into an immutable mapping. Neither a GitHub issue, a prompt, a child
  worker nor a TaskGraph node may supply or approve its own file hashes.
  The trusted host application must provision this reviewed manifest.
- The factory still checks the **existing** admitted `SecurityGrant`, task
  identity and parent scope before freezing profile inputs. No new grant is
  created; profile selection is an additional constraint, never authority.
  Files are copied through no-follow reads into anonymous, write-sealed
  Linux memfds only after grant admission.
- `PreparedPolicyLaunch` retains the private snapshot through sandbox
  attestation, bootstrap and the correct owned pane's lifetime, then closes
  its file descriptors on accepted cleanup. Preparation failures close
  snapshot descriptors without leaving a new economic attempt.
- The root `agent-task-worker` and managed child `herdr/runtime.py`
  reject a mismatch between the host-approved profile name and the requested
  Hermes CLI profile. When approved and matching, they pass the exact typed
  snapshot to the existing `agent_durable_sandbox.command` FD bridge.
  There is **no secondary scheduler** or new persistence/cost authority.
- The sandbox constructs a private `--tmpfs /home/agentops`, mounts approved
  profile data by sealed file descriptors, pins code/runtime/workspace from
  existing policy objects, and finishes mounting with nonrecursive
  `--remount-ro /home/agentops`. Runtime session/cache/log/paste submounts
  retain RW permissions. The hardened launcher refuses untrusted bwrap
  options, HOME/XDG path relocation, PID/proc bypasses and mount shadows.
- `sandbox.verify()` adds an independent attestation of the readonly
  HOME mount, exactly one selected profile, readonly sealed file contents,
  and four private RW runtimes. The pre-existing code/runtime and owned
  worktree identity checks remain mandatory.
- **Backward compatibility:** when the host has not supplied an approved
  profile, no new keyword argument is sent to legacy root/child bwrap command
  or verification mocks. Existing execution policy remains unchanged.

## Evidence and deliberate limitations

The isolated physical test constructs a host-authorized profile, enters the
real bwrap child namespace without running Hermes or connecting a provider,
verifies exact approved bytes, tests post-mount same-UID host replacement, and
attests profile HOME RO and runtime logs RW. Additional tests verify frozen
manifest immutability, prevention of profile selection mismatch, denial before
grant and post-pane descriptor release.

**This implementation is DRAFT and not sufficient to close P0 #129 or
activate the autonomous #53 coordinator.** In particular:

1. No production host manifest issuer/configuration has been deployed.
   Source digests must come from an independently reviewed, trusted host
   authority, never `sha256` of a task-selected live profile.
2. The original `FrozenTree` for pinned Hermes/Python source is protected
   at launch but its host storage owner must still be hardened against
   same-UID mutation for the **entire** sandbox lifetime.
3. Native pinned Hermes CLI must be exercised end-to-end in a network-isolated
   zero-provider/zero-cost session to verify actual credentials, prefill,
   history, logs, parent/child handoff and result delivery. No paid call may
   be attempted during these tests.
4. Root/child reconnection, rollback, replay-safe delivery, shared task
   lock, budgets, and release integrity require exact-head CI and independent
   security review before promotion. Do not merge stacked PRs out of order.
5. PR #125, #127, #128 and unrelated RC26 release blockers still have their
   own acceptance requirements. Issue #126's disk headroom improving is not
   a substitute for incident attribution or durable alerting.

No production permission changes, host credentials updates, queue resets,
manual task reruns or deployment actions are authorized by this document.
