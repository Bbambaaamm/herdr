# Hermes runtime pin candidate — issue #132

**Status: DRAFT / NOT ROOT-PUBLISHED / NO-GO for autonomous model execution.**
Prepared from verified local Hermes SDK patch and `uv.lock`. No providers,
model calls, root-owned configuration edits, release/tag publication or queue operations.

## Exact candidate inputs

| Surface | Exact pin |
| --- | --- |
| Pinned Hermes SDK candidate commit | `ef0342358f6421efb4ce919ba859d69940ca13b7` |
| Original Hermes upstream commit | `ee5ee84a345204a3b1d6ef6ba1ab747e602867b9` |
| Source patch, decoded SHA256 | `87a8a42c4c401302f5aae3dbe65824cd9295186beed48412379170d9ea37a70f` |
| Pinned Hermes version | `0.21.5` |
| Exact source files | **1,821** |
| Source digest (stage2 algorithm) | `d0bd4e3e6023166b3feed4b3fc47ac811d9453476866c8c5e4319bf1038f02fa` |
| Inventory file SHA256 | `495d03622f965f608307b66aa0aa883f7669f7976070417c4b169babf610d617` |
| `uv.lock` SHA256 | `5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590` |
| `package-lock.json` SHA256 | `193a3a3703499eb7c4b4ce48d3ba1e9dae2be62a48315c1e7ea9545e8be4a067` |
| Frozen Python | `3.11.16` |
| Python binary SHA256 | `1e761eb19d6f2594ab8dc64bd99ad4e1753589f3bf1ec199e4eef3aaa21e3930` |
| Python stdlib digest | `330e97044fcb6873bc76ab37b63bfcd8c9a081d64d285adea164d3f72b548c2e` |
| Lock-reproduced venv/site SHA256 | `d986a36b26e4a57ce5a89fca094843c98b10f8d73c9185f95c09cb1da4172330` |
| Resulting executor identity | `hermes:0.21.5:sha256:28cbd35dd0e7d738a321becce73eb05c91f269ac1c821e0e2adbfefd5b313b4b` |

## Why 1,821 and not 1,249

The historical 1,249-name source pin included `agent.host_reference`
but omitted 572 tracked Python files in declared runtime packages:
`hermes_platform` (12), `plugins` (240), `gateway` (174),
`tui_gateway` (97), `cron` (33), `acp_adapter` (14) and `providers` (2).
An isolated real import initially failed with `ModuleNotFoundError:
hermes_platform`, then `plugins`. These paths exist at the exact candidate
commit, and are part of packages declared in `pyproject.toml`. They were
added to the source-only manifest, **not** copied from an unrelated version.

Only the 1,821 inventory files were copied into an isolated source tree,
together with a separately reproduced lockfile venv. No untracked
importable .py/.pyc/.so/.pth files were present. The exact
`agent-hermes-policy-run::_verify_hermes_build` function accepted the
source digest and manifest; `_digest_site_packages` accepted the venv
digest. `uv pip check` reported 108 compatible installed distributions.
An isolated Bubblewrap runtime with `--unshare-net --unshare-user` and
safe-mode environment imported `agent.host_reference`, `run_agent.AIAgent`,
and `hermes_cli.main` successfully with zero model calls.

## Local reproduction (read-only)

A local audit of the candidate source+venv root must use the pinned Herdr
source and actual stage2 verifier. The `scripts/audit-hermes-runtime-candidate.py`
tool checks the inventory and executor pins, both full source/venv hashes,
and the optional source lockfile. Inputs must refer to a **private, untrusted
candidate folder**, never to a privileged published root for modification.

The raw development Git checkout is deliberately **not** an approved runtime
root: it contains thousands of additional test Python files, which stage2
rejects. The isolated source snapshot is the exact allowlisted runtime tree.

## Remaining hard gates

1. The source and venv candidates are user-owned temporary copies, not an
   independently reviewed immutable and root-published Hermes release.
   The SDK patch commit is local and requires independent source review and
   trusted provenance before a signed release tag.
2. The venv was reconstructed with `uv sync --locked --no-dev
   --no-install-project --no-install-workspace --no-build --extra all
   --extra edge-tts --extra bedrock`. The project itself was not installed
   as a wheel, and the NPM/web/TUI distributable artifacts were not included
   in this complete runtime candidate. Optional dependencies and install
   scripts still need a separately audited build.
3. The earlier historical venv had 110 distributions and six package-version
   drifts from `uv.lock`; the reproduced venv has 108 compatible external
   dependencies but does **not** constitute byte-identical historical venv.
4. Full source import verification is **not** proof of runtime effect
   confinement. The SDK's host-reference identity contract, network
   isolation, authenticated host IPC, subagent/retry safety and model effect
   reservation require exact-head independent security approval.
5. The existing active RC6 stays unchanged. The official root-owned
   stage1/stage2→managed child→durable result→parent ACK E2E has not passed
   against this reviewed candidate. All operator/root-owned schema-2
   publication and model invocations are prohibited until separately approved.

**Acceptance: NO-GO**; track in #132 and draft PR #225.
