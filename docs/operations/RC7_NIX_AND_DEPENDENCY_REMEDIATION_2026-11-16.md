# RC7 — approved Nix build workflow and dependency remediation

**2026-11-16. Status: REVIEW-ONLY / NOT EXECUTED / RC7 NO-GO.**

## Approved builder preparation

A manually dispatched workflow candidate is stored at
`.github/workflows/rc7-nix-wheel-review.yml`. It has no scheduled trigger,
push trigger, deployment trigger, model access or GitHub write permission.
Its job requires:

- An explicitly operator-provisioned, approved **self-hosted** runner with
  labels `self-hosted, linux, x64, herdr-nix-reviewed`.
- An existing protected GitHub Environment `rc7-nix-build-review` with
  required human reviewers. The workflow itself cannot create approval.
- A repository variable `RC7_REVIEWED_HERMES_REPOSITORY` specifying the
  approved HTTPS GitHub fork under `Bbambaaamm/`. The exact SDK commit
  `ef0342358f6421efb4ce919ba859d69940ca13b7` currently exists
  in a local scratch worktree only. Before manual execution it must be
  published independently and reviewed in an approved Git repository.
- A functioning Nix daemon and source-flake lock support, independently
  reviewed runner identity and isolated Nix sandbox.

Before Nix build, `scripts/rc7_hermes_nix_source_preflight.py` compares
Git HEAD, clean working tree, exact 1,821-file source digest and
`uv.lock`/`package-lock.json`/`flake.lock` to the stage2 candidate.
The real local Hermes fork passed this preflight. This does NOT approve
publishing or signing a wheel: it is a source-integrity prerequisite.

The proposed manual workflow attempts Nix `minimal`, `web` and `tui`
from the exact reviewed flake lock and records Nix store paths. It does
not attempt to deploy, sign, publish, merge, queue a task or run a model.
Nix isn't installed on the currently authorized staging machine and
Docker daemon access is denied, so **the workflow is unexecuted**.
No new runner or GitHub Environment was provisioned automatically.

## Vulnerability correction spike (isolated, no production changes)

On the exact Hermes candidate lock
`193a3a3703499eb7c4b4ce48d3ba1e9dae2be62a48315c1e7ea9545e8be4a067`,
the npm security audit reported 27 vulnerable dependency entries in the
complete workspace tree: 3 critical, 6 high, 9 moderate, 9 low.
Web scoped tree: 3 high, 1 moderate, 1 low; TUI: 3 high.
These are **dependency-tree findings**, not proof of reachable exploit
paths in the final web/TUI bundle.

An isolated, Git-archived scratch copy was used for
`npm audit fix --package-lock-only --ignore-scripts --no-audit`.
It returned nonzero due to an `ERESOLVE` peer dependency conflict involving
`vite@8.3.8` and `@rolldown/plugin-babel@0.2.3`. The proposed
`package-lock.json` hash remained unchanged. No `--force`,
`--legacy-peer-deps`, overrides or unsupported wheel build were used.

Before RC7 approval, reviewers must first reconcile the `vite`/
Rolldown peer graph and separately review fixes for critical packages
`simple-git`, `@simple-git/argv-parser` and `dompurify`. Also
triage high findings `brace-expansion`, `minimatch`,
`source-map-js`, `undici`, `vite` and `zod`.
Update the Hermes fork source and exact npm lock *as a new candidate commit*.
Rebuild web/TUI/Nix artifacts, rerun npm audit, check actual reachability,
SBOM provenance, Python dependency drift and independent security review.
**Do not reuse the prior source digest, web/TUI archive hashes or executor
identity after modifying the lock or source.**

## Remaining RC7 acceptance

1. Independently reviewed Hermes fork commit and root-owned immutable Nix
   wheel/asset closure.
2. Critical/high package advisories resolved or independently accepted with
   rigorous reachability/effect proof; rebuilt and signed artifacts.
3. Root-owned schema2 security and model authority accepted at exact head.
4. Full native zero-provider stage1→stage2→managed child→durable result→
   parent ACK/replay with negative kernel/network and restart tests.
5. Explicit operator approval for bounded model canary and rollback.

**The above gates remain open. Do not trigger a live build/release just
because the manual workflow exists.**
