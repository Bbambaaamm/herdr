# Herdr #129 — lifetime-stable Hermes profile namespace (security prototype)

## Problem and concrete attack

The production candidate in PR #125 overlays individual writable SDK paths
with `--tmpfs /home/agentops/.hermes/profiles/<name>/logs` inside `bwrap`
after `--ro-bind / /`. The host directory entries in the mounted root are
still live. An independent same-UID process can rename an already mounted
directory on the host, then substitute the original pathname with a symlink to
a writable task workspace. One-time post-startup mount attestation cannot
keep that pathname immutable.

Confirmed on `quantlab-staging-01` on 2026-10-09 with a disposable fixture.
The **real sandbox child** was identified via the bwrap supervisor's child PID
and its different mount namespace. After the host swapped `profile/logs`,
the child observed a symlink and could open a workspace sentinel. This is not
an inference from the bwrap supervisor's host mount namespace.

## Tested protective primitive

`herdr.private_profile_namespace.PrivateProfileSnapshot` implements **only
the input-fabric primitive** required for a stronger sandbox. It is not yet
connected to the live Herdr agent launcher.

1. A *trusted host authority* must provide an exact digest manifest of
   approved profile files. The prototype requires `config.yaml` and `.env`
   and can include bounded `auth.json` and referenced prefills. It refuses
   arbitrary path components, mutable session/database/log destinations,
   symlinks, unsupported types and content/length mismatches.
2. Source files are opened beneath a held directory descriptor with no-follow
   operations. Each byte-for-byte approved source is copied into an **anonymous
   sealed Linux memfd**. No credentials are written into the repository,
   test output, sandbox command string or a temporary disk file.
3. The prospective sandbox uses `--tmpfs /home/agentops`, not just per-profile
   subdirectory masks. `/home` must be root-owned and not group/world writable.
   This private root disconnects the sandbox from the host-writable
   `/home/agentops/.hermes` ancestors for the entire session lifetime.
4. Under the private root, bwrap recreates only the selected profile directory
   and copies sealed file-descriptor contents with `--ro-bind-data`.
   Writable `sessions/cache/logs/pastes` are private temporary directories
   **inside that isolated home**, never host profile aliases.
5. Physical tests read from the **sandbox child namespace**. Changes to the
   host source bytes and replacement of the host source directory with a
   symlink have no effect on the profile snapshot visible to the sandbox.

The prototype is fail-closed and does not silently select a model or call an
external provider.

## Required production integration (NOT complete)

- A trusted pre-admission authority must pin and sign the **approved digest
  manifest**, profile identity and referenced prefill inputs. Never let the
  untrusted worker approve its own `config.yaml`/`.env` hashes.
- Extend the existing `_POLICY_FD_LAUNCHER` to transport the sealed file
  descriptors via `--ro-bind-data` with exact identity, digest, size, seal
  and target checks. Retain the pinned launch owner and descriptors until bwrap
  has completed mounting them. No second scheduler or persistence backend.
- Reconstruct **only** explicitly admitted worktree, result slot, frozen Hermes
  code, frozen Python runtime and required bootstrap transport within private
  HOME using existing policy-owned FD bindings. Never restore the general
  host home as a mutable read/write bind. Validate actual `bwrap` mountinfo,
  stored inode identities and private readonly profile inputs.
- The existing `FrozenTree` for signed SDK and Python currently resides on
  an agentops-owned host tree. For a full same-UID adversary model, prove the
  **runtime import tree also cannot be modified during a live session** or
  migrate immutable sources into a root-owned/pinned authority. A readonly
  bind of an attacker-writable inode is insufficient by itself.
- Preserve real Hermes `--profile`, configuration, credentials, relative
  `prefill_messages_file` resolution, native chat history/pastes/logs,
  bootstrap receipt, child delegation and replay-safe task result channel.
  Exercise the pinned native SDK with a zero-cost / empty-provider grant and
  separate network namespace before any paid canary.
- Add a physical same-UID *after-mount* adversarial test during real guarded
  Hermes runtime; test root and managed-child paths, restart/recovery, altered
  profile and SDK source, ancestry swaps, extra/missing files and filesystem
  exhaustion. Existing TaskGraph/leases/fencing and cumulative budget are
  unchanged.
- Only exact-head CI, independent security review, signed release cutover,
  rollback and evidence-backed #78 E2E can clear #129. Until then keep #53
  autonomous coding blocked; no duplicate economic attempt or new grant.

## Status

**Prototype with physical evidence; NOT a production fix or activation.**
This scope is deliberately isolated from PR #125, PR #127, PR #128, disk
issue #126 and active RC26 runtime. It can be reviewed on the PR branch
without touching queue, credentials, deployment or model budget.
