# Step 3/6 — documentation, integration and release assessment

Owner-authorized scope: finish #263/#262 under #53, merge through protected PR,
tag a CI-green main commit and verify the official Release bundle offline.
Deployment, service changes, host policy, Hermes state and model activation are
not authorized. The final immutable identities/results are recorded on #263,
#262 and #53 after their corresponding operations, not predicted here.

## Starting evidence and merge rules

Verified main: `5fb42a5d8890822005419631d011ff43752a001a`; initial PR head:
`e75e59b167dd64ab5f77e6e1bf5bd9f185152538`. PR #263 is draft/open/mergeable;
all six review threads resolved. Previous head has successful CI 45844741023 and
independent review receipt 7195704619, but these do not approve the documentation
commit added in this step. New exact-head CI and independent review are required.

Main protection: strict Herdr contract check from app 15368, linear history,
resolved conversations, stale approval dismissal, admin enforcement, no force
push/deletion. Required formal approval count is zero. All three merge methods
are repository-enabled; squash respects the required linear history. Merge must
be bound to the newly reviewed head; no direct main push or bypass is permitted.

## Documentation correction

RUNBOOK now describes healthy/degraded/unsafe baselines consistently instead of
claiming every normal apply requires a healthy previous web boot. It documents
the target-specific bridge/snapshot checks, exact authority restoration before
reactivation, fresh telemetry after healthy rollback, degraded web normalization,
bounded Nginx convergence, and SIGTERM versus SIGKILL/power-loss reconciliation.

The controller root must be a direct child of an approved immutable prefix with
the exact release-id basename. Examples use the same protected archive for both
commands, explain the five actual consumer overlays, and distinguish the legacy
DEPLOYED_GIT_SHA argument from the current versioned commit. The confirmation is
derived only from successful actual preflight output. Historical RC8 recovery is
explicitly forbidden for RC6; its pinned RC8/RC12 authorization is unchanged.

## RC6-to-planned-main assessment

Base deployed RC6: `8d8ad50375557b7ac77348e6475cb455682f4a9a`.
The inspected delta to pre-documentation #263 head contains 91 changed files and
23 already-merged main commits plus three #263 commits. No consumer policy,
external binary pin, private-profile namespace or durable sandbox implementation
changed in that delta. The release overlay schemas/invariants still require all
five consumers, QuantLab PAPER-only, Heating actuation disabled and monotonically
bounded child authority. This is an installer candidate, not stable production.

| Area | Actual delta and release disposition |
|---|---|
| Installer/dashboard | #238 skips unnamed bridge entries; #263 adds baseline-aware transaction/readiness/rollback and reviewed hardening. Release acceptance includes T01–T15. |
| Maintenance/capacity | #240 introduces pre-backup reserve checks and bounded diagnostics in the existing maintenance path; reserve is not lowered. No host timer or service is changed by building the bundle. |
| Router/scheduler | #236 adds bounded retry/backoff/cooldown and a dispatch-not-before guard; #226 is non-executable cost shadow comparison. No live provider/router activation is authorized. |
| Security/readiness | Protected-reader changes preserve root authority except the explicit agentops capacity publication reader; existing sandbox/immutable profile code and external binary pin are unchanged. |
| Usage/telemetry | #222-related contracts and bridges collect bounded offline observations/references, including cache completeness. No provider credentials or new SDK/runtime are bundled. |
| Defect/incidents | #229/#237 add offline observations, read-only diagnostics and admission reconciliation; they do not grant dispatch authority. |
| ChatGPT ingress | #255–#259 add proposal/binding/consumption contracts with no external route to live selected-root admission. #259 has later independent clean review at 7d15187; live activation/formal host approval remains a separate unsatisfied gate. |
| Build lifecycle | #227/#228/#244 are read-only scanners/verifiers with no deletion executor or issuer; missing host proofs remain BLOCKED_REVIEW. Their documented NO-GO applies to cleanup/activation, which is not included in this release operation. |
| Runtime publication | #223/#224 are audits/proposals only; they do not install a root policy or approve runtime reuse. #225's separate unmerged Hermes runtime candidate is not silently included. |

The gate distinction above is scoped to packaging existing fail-closed source.
It does not declare blocked cleanup, autonomous dispatch, host grant, physical
sandbox acceptance or ChatGPT live activation complete. No blocked activation is
enabled or re-labeled as accepted. Any newly discovered applicable artifact-
release blocker must stop tagging until resolved.

## Version/workflow assessment

Tags through `v0.3.0-router-v5-p1d-rc7` already exist. RC7 points to 5fb42a5d and
its Release bundle 45824296850 succeeded; its deployment attempt was unsuccessful.
RC6 bundle 42725872736 succeeded. Historical rc3 was lightweight and its release
workflow failed; rc4 is annotated and succeeded. Do not repair/reuse old tags.
The nearest unallocated line candidate is rc8, subject to a fresh tag/ref check
immediately before creation after merge and post-merge CI.

Official `.github/workflows/release.yml` triggers on v* tag pushes, requires an
annotated tag pointing at a main ancestor, runs full Python/browser/security
checks and the official deterministic builder, and uploads archive + SHA-256 as
an Actions artifact retained 30 days. It has contents:read and does not publish a
GitHub Release. Do not fabricate a manual replacement bundle or claim publication
of a GitHub Release that this workflow never performs.

The source manifest binds the complete source tree; it is not itself part of the
closed installer payload. Verify it in the exact tagged checkout, then verify
the filtered committed payload against the official archive and its independent
MANIFEST.sha256/RELEASE.json. Reproducibility is checked with the same official
build_release contract at the same annotated tag and commit, not floating main.

## Staging boundary

Read-only sample before this step: RC6 current symlink, legacy SHA
`41179635c8654a60c5d9234acccb6e91b2028b72`, available root bytes 14198235136.
These observations are not a future deployment authorization or a capacity
guarantee. No protected controller directory has been prepared and no preflight
or apply has been run on the live host. Exact archive sizes, disk-reserve formula,
final controller/preflight paths and GO/NO-GO checklist will be recorded in the
step-4 plan only after official artifact verification. No confirmation token is
invented before actual preflight.
