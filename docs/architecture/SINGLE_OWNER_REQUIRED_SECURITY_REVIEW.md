# Single-owner Herdr: independent read-only merge review evidence

**STATUS: OFFLINE ADVISORY PROTOTYPE ONLY. NOT A REQUIRED CHECK.**

This PR does not change any repository protection or review requirement,
does not merge or deploy, and does not authorize Hermes execution.

## Security findings in independent PR #261 review

The first prototype exposed three blocking P1 issues and one P2.
The following source-only changes remove those unsafe activation paths:

- P1, status impersonation: an ordinary PR workflow can use the shared
  GitHub Actions App identity to publish the same status context. The
  default-branch workflow therefore has NO statuses:write permission.
  The evaluator has NO status publishing function and emits only an
  advisory JSON result and process exit code. Thus the prototype CANNOT
  be mistaken for a sufficient merge authorization. A dedicated,
  independently managed GitHub App will be required for publication.
- P1, forged CI: a PR can define a new Actions job named Herdr contract,
  retaining the same GitHub Actions App ID. The evaluator now follows
  the exact check run details URL to the actual Actions run, requiring
  the trusted CI workflow path, workflow ID 367993725, full PR HEAD,
  canonical repository, successful completed run and supported event.
  Only the trusted workflow's run can fulfill CI evidence.
- P1, stale green status: review changes, new inline findings or failing
  check reruns do not necessarily trigger the original workflow. Because
  the prototype now publishes NO approval status, it cannot leave behind
  a stale successful authorization. A future external publisher must
  implement reliable event subscriptions, invalidation on *all* review
  and check changes, reconciliation and no stale-success crash windows.
- P2, fork status poisoning: the original publisher wrote pending before
  verifying that an event targeted an eligible same-repository PR. The
  revised code NEVER publishes statuses; its API collector rejects
  incorrect repository, PR number, HEAD or base before reporting evidence.

## Current fail-closed evidence contract

The read-only evaluator inspects authenticated GitHub data and requires:

- exact canonical repository and open non-draft PR based on main;
- exact successful official Herdr CI workflow run from Actions App 15368,
  plus successful GitGuardian check from App 46505;
- no differences to the protected CI workflow, the read-only review
  workflow or evaluator code relative to the PR base SHA;
- complete and fully resolved review thread inventory;
- no outstanding effective CHANGES_REQUESTED;
- a GitHub-authenticated Codex bot comment containing the exact full
  SHA typed closed codex-review-state:v1 summary for BOTH code and
  security reviews, completed with no findings;
- the selected clean summary is not older than a later Codex review;
- unchanged PR HEAD and target base SHA through evidence collection.

The workflow uses only contents:read, issues:read and
pull-requests:read. It checks out ONLY protected main, never incoming PR
code. The result is an advisory log, NOT a GitHub merge status context.

Missing, stale, forged, incomplete and unknown evidence all fail closed.

## Necessary architecture before setting required approvals to zero

1. Independently approve this audit code and test the public repo Actions
   event policy on the default branch. Its present source-only workflow
   must not have status write permissions.
2. Create a DEDICATED GitHub App, installed on only the intended repo,
   whose installation token, signing key and credentials are controlled
   outside PR-executing GitHub Actions and inaccessible to PR authors.
   Restrict to the minimal status/check writing and read-only evidence
   permissions. Pin the resulting required status to that App ID.
3. Have the App subscribe to pull-request, review, review-comment,
   issue-comment, check-run/check-suite and base-change events.
   Verify signed event delivery, authenticate event subjects, invalidate
   prior positive results when evidence changes, and reconcile missed
   events. Checks must revalidate immediately before merge; stale positive
   statuses cannot survive a disqualifying event or runner crash.
4. The App itself must perform authoritative source checks, using the
   protected published version of this evaluator (or a separately audited
   immutable equivalent), not instructions/code/artifacts from a PR.
5. Obtain a real clean machine-readable Codex code+security summary
   from the provider; prose COMMENTED is not a valid approval.
6. Integrate and TEST the App on a harmless PR. Validate blocked cases
   including forged CI with identical App ID, competing status contexts,
   old or partial review evidence, changed protected file, CHANGES_REQUESTED,
   review edits after PASS, CI re-runs and fork PR status poisoning.
7. Add the dedicated App-pinned security status and GitGuardian
   to REQUIRED checks while retaining Herdr contract, strict freshness,
   conversation resolution, admin enforcement, linear history, and
   force-push/deletion denial.
8. Only after those checks are observed as working in real GitHub
   protection, request a separately authorized one-time change of the
   human approval count from 1 to 0. NEVER do that first.

## Current blockers

The source-only prototype lacks any independent credentialed publisher
and has no event-driven stale-success invalidation service.
GitHub Actions identity cannot be used as the merge authority.
The default branch remains on the existing branch protection policy
requiring a human approval. No authorization change is made by this PR.

A personal administrator ultimately controls repository settings;
that account-level authority cannot be removed by an ordinary workflow.
