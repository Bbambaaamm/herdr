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
  A separately trusted host-only `profile_preflight(profile_name)` must
  return `True` before snapshot creation. It may validate or refresh live
  provider credentials; **only then** are the exact preapproved file hashes
  checked and copied through no-follow reads into anonymous write-sealed
  Linux memfds. Any post-refresh mismatch is a hard stop. Root/child paths
  skip later refreshes when using an approved sealed snapshot; the unchanged
  legacy path still performs its original provider preflight.
  The preflight callback and reviewed hashes are NOT supplied by a task.
- `PreparedPolicyLaunch` retains the private snapshot through sandbox
  attestation, bootstrap and the correct owned pane's lifetime, then closes
  its file descriptors on accepted cleanup. Credential-bearing memfds are
  closed in an independent `finally` even when an earlier stage, bootstrap
  or frozen-code cleanup fails; the prior error still propagates and cannot
  be misreported as a successful cleanup. Preparation failures also close
  snapshots without creating a new economic attempt.
- The root `agent-task-worker` and managed child `herdr/runtime.py`
  reject a mismatch between the host-approved profile name and the requested
  Hermes CLI profile. When approved and matching, they pass the exact typed
  snapshot to the existing `agent_durable_sandbox.command` FD bridge.
  `ApprovedProfile.identity` computes a canonical, bounded profile
  name/manifest/file-digest identity. The exact identity is included in the
  sandbox attestation whose hash is committed by the existing signed grant,
  as well as in retained policy evidence. The retained verifier checks the
  evidence against its signed attestation and compares approved on-disk
  sandbox bytes to the recorded digests.
  A child `HostPolicyLaunchFactory` with an approved profile additionally
  requires a host-owned `parent_approved_profile` with the same exact
  manifest, plus the **accepted live parent `PreparedPolicyLaunch`** whose
  signed proof contains those same approved profile hashes and whose accepted
  grant identity/hash equals the child factory's parent grant. Passing only
  a matching profile name or refreshing host credentials silently is denied.
  After a restart a host must first reattach/revalidate the parent authority;
  no synthetic, model-supplied or stale parent proof may authorize a child.
  There is **no secondary scheduler** or new persistence/cost authority.
- The sandbox implements a private `--tmpfs /home/agentops`, mounts
  approved profile data by sealed file descriptors, and finishes with
  nonrecursive `--remount-ro /home/agentops`. Runtime
  session/cache/log/paste submounts retain RW permissions. The hardened
  launcher refuses untrusted bwrap options, HOME/XDG path relocation,
  PID/proc bypasses and mount shadows.
  **New P1 safety hold:** both the workspace and exact writable result-slot
  sources must be pinned by immutable file/directory descriptors before
  this opt-in may run. Merely checking a mutable pathname and later issuing
  `--bind` permits a same-UID host rename/symlink attack into live Hermes
  credentials. Consequently `sandbox.command()` now FAILS CLOSED for any
  private-profile invocation without a `PinnedWorktree`, or with any
  remaining path-based `writable` mount. Root and managed-child production
  callers still supply path-based result slots, so private-profile execution
  remains deliberately disabled until the trusted host pins and retains
  those exact result FDs through bwrap/attestation. Existing legacy launches
  are unchanged. The physical test uses a deliberately FD-pinned workspace
  and no result slot (no model invocation).
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
grant, strict post-refresh hash validation, parent/child profile-identity
consistency, signed attestation/evidence validation and independent release
of credential-bearing file descriptors after failed cleanup.

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
