# Single-owner Herdr: trusted required security-review check

**Status: source-only, NOT ACTIVE on protected main.**
This PR does not change any repository protection, review requirement,
release, host policy or running service.

## New security boundary

`Herdr security review` is an exact-PR-head commit status calculated by a
workflow whose source and checkout are the **protected default branch**, never
the incoming PR branch. The workflow uses only
`pull_request_target`, `issue_comment`, and trusted manual
`workflow_dispatch` triggers, not untrusted pull-request merge-ref workflow
execution. It checks out `main` with disabled persisted credentials and
does not run, install or fetch executable code or artifacts from the PR.
The token has only `contents:read`, `issues:read`,
`pull-requests:read`, and `statuses:write`.

The evaluator reads authenticated GitHub data and requires:

- exact canonical repository and open non-draft PR based on `main`;
- pinned GitHub Actions CI app ID 15368 and GitGuardian app ID 46505 with
  current successful checks on the exact PR head;
- no modifications to the protected CI workflow, security workflow or security
  evaluator relative to the PR's base SHA;
- complete review thread inventory with **no unresolved threads**;
- no outstanding effective `CHANGES_REQUESTED`;
- a verified GitHub Codex bot `chatgpt-codex-connector[bot]` comment with
  the typed closed `codex-review-state:v1` summary for **both code and
  security reviews**, matching the **full exact PR head**; both must be
  completed with neither findings nor unresolved findings;
- current clean summary not older than a later Codex submitted review;
- unchanged PR identity and head after the checks.

The check is **fail-closed** on missing, malformed, expired/stale, untrusted,
ambiguous, incomplete or negative evidence. Generic bot COMMENTED reviews,
prose approvals and user-created comments are not sufficient evidence.
Review discussions are also enforced separately by GitHub branch protection.

## Activation requirements

1. Review this gate independently at its exact HEAD, and run negative tests
   for changed SHA, app spoofing, unresolved P2, incomplete pagination,
   denied review, malformed typed summary and modified protected code.
2. Verify GitHub's public-repository `pull_request_target` event policy,
   which is being changed. If such events are blocked, use a trusted
   GitHub App instead of disabling platform security.
3. Merge the gate implementation into `main` by the **existing protected
   process**, requiring a separate authorized one-time migration.
4. Prove the new check actually publishes its status on the current PR HEAD
   under the expected GitHub Actions App identity; validate exact-head
   behavior for pull_request_target and issue_comment. After CI or review
   changes, manual workflow_dispatch may be necessary: do not treat a stale
   green result as proof of unchanged external review.
5. Add `Herdr security review` (app ID 15368) and GitGuardian
   (app ID 46505) as required checks while **retaining** the pinned
   `Herdr contract` (app ID 15368), strict base freshness, required
   conversation resolution, admin enforcement, linear history and bans on
   force-push/deletion.
6. Only **after** verified enforcement consider changing
   `required_approving_review_count` from 1 to 0. Never do it first.
7. A stronger future design should publish this status under a **dedicated
   GitHub App identity**, rather than sharing GitHub Actions identity with
   existing workflows; otherwise another privileged workflow with the same
   app identity could potentially spoof a context.
8. Any change to trusted gate/CI code requires a separate operator-reviewed
   migration, not self-approval by the code being changed.

## Current limitations

This implementation is not itself merged, required, installed or activated.
The `pull_request_target` policy and GitHub status association are not yet
demonstrated live. Existing Codex reviews of the gateway generally contain
COMMENTED suggestions without the typed clean security summary required by
this gate and will correctly remain blocked. No authorization bypass, merge,
status spoof, release or host restart is permitted to make the test green.

A single personal admin inherently retains authority to change settings;
software checks cannot create an independent organizational administrator.
No live merge is attempted in this development slice.

### Crash-window and event freshness

On every supported event the publisher writes **pending** to the exact
GitHub head SHA *before* collecting mutable remote evidence. If GitHub
errors, verification fails, or the runner crashes, no new success is
published for that recheck; a later fail-closed evaluation publishes
`failure`. HEAD and base identities are rechecked at the end.

`pull_request_review` and `pull_request_review_comment` are deliberately
excluded from this first privileged workflow because GitHub assigns them
PR merge refs rather than default-branch refs. Until a separate trusted
GitHub App handles those events, review edits may require an explicit
default-branch `workflow_dispatch` recheck. GitHub's own mandatory
conversation resolution must remain on. Do not rely on this prototype
alone to replace human approvals.
