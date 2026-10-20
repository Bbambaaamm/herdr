# GitHub intake admission

Consumer repositories remain the authority for authorized work. Issue text,
issue authors, associations and labels are context, never execution permission.
The existing intake and queue stay in place; this protocol does not create a
new scheduler, approval service, budget authority or deployment permission.

An enabled consumer must declare `maintainer-comment-v1` admission. The intake
uses the installed guarded `gh api` for authenticated read-only API requests.
There is no direct HTTP or anonymous fallback. Missing authentication, unknown
roles, incomplete JSON/pagination or inconsistent repository/issue identities
withhold new work.

## Maintainer operation

1. Obtain a proposed acknowledgement without creating any task:

   `agent-github-intake --approval-digest OWNER/REPOSITORY ISSUE_NUMBER`

2. Review the exact current issue and the proposed repository/issue identity,
   digest and expiry. Post the returned `approval_body` as an issue comment
   only when that exact work is approved. This command never posts it.

The complete comment consists of this marker and one JSON object:

```text
HERDR-ADMISSION-V1
{"action":"approve","repository":"OWNER/REPOSITORY","issue_number":53,"issue_id":123,"content_sha256":"<64 hex digits>","expires_at":"<UTC timestamp>"}
```

The digest is SHA-256 over canonical UTF-8 JSON (`sort_keys=True`,
`ensure_ascii=False`, separators `,` and `:`) containing version, repository,
repository ID, issue ID/number/current open state, exact title and exact body.
Do not manually normalize or truncate the issue before calculating it. The
readonly helper supplies this representation. Bodies over the existing
12,000-character prompt boundary are denied rather than silently truncated.

The comment author must currently hold GitHub's `admin` role with legacy
`admin` permission, or `maintain` role with legacy `write` permission, for this
repository. The API user ID and login must match the comment's author. An
issue author with such a role still needs this explicit acknowledgement.
Custom/unknown roles are not guessed to have equivalent authority.

Comments must be unedited and unexpired, with expiry at most 24 hours after
creation. The helper proposes 30 minutes. Current issue `updated_at` must not
be later than the acknowledgement; this conservatively invalidates approval
after later issue activity, including non-content changes. The digest also
detects title/body changes. Intake re-reads the complete issue after checking
all bounded comment pages and current maintainer permission. Changes during
that check deny admission. More than 1,000 comments fail closed.

The newest maintainer acknowledgement takes precedence. A newer trusted
marker with `action: revoke`, an edited acknowledgement, invalid scope or
expired evidence cannot fall back to an older approval. Removing an approval
comment also removes that admission signal for work not yet queued. Intake
does not cancel an already active task or enlarge its permissions.

## Root flow and replay

Root-only consumers retain their configured issue selection, stable
coordinator, root task kind, prompt contract, active/blocked barriers and
cooldown. They have no authorization bypass. Each acknowledgement admits at
most one existing queue episode, identified deterministically by repository,
issue and comment ID. Replaying it after terminal completion does not create
another episode; the existing intake state retains consumed acknowledgement
IDs. Corrupt state or exhausted bounded history fails closed. Another root
cycle needs a new explicit acknowledgement under the same existing policy.

The queued task retains redacted admission provenance and the approved issue
digest. Issue-derived instructions remain subordinate to the host's existing
TaskGraph, grant, child-permission, budget, review, merge and deployment gates.
An acknowledgement does not replace any of them. Apply/deploy, model activation
and autonomous backlog activation remain separate approvals.

## Failure and scan bounds

Every retained state row and repository/issue key is validated, including closed or currently unselected consumers. Invalid rows, duplicate/migrating keys, identity mismatch or malformed consumed-approval history stop intake; they are never discarded as a fresh state.

A pending task is serialized and fsynced under a hidden temporary name, then published by Linux renameat2(RENAME_NOREPLACE) and directory fsync. No hard-link or partial final JSON is exposed. A crash before publication leaves only an ignored temporary; a crash after publication leaves a complete task whose deterministic approval ID retains at-most-once behavior. A durability error is a stopped transaction, not permission to reset or replace retained work.

The normal maintenance caller allows 30 seconds. Intake reserves six seconds for local persistence by limiting the GitHub scan to 24 seconds, with each guarded GET bounded by the smaller of five seconds and the remaining scan time. This is an HTTP/scan deadline, not a real-time filesystem guarantee. Only the authenticated user identity is cached within that single scan; maintainer permissions, issue revisions and approval evidence are checked afresh.

The fsynced github-intake.cursor.json (beside the existing stamp) records only the next consumer and last attempted issue for fair resumption. It is not authority and cannot admit work. Interrupted scans preserve unvisited issue state and all approval history, avoid a completed-scan stamp, and resume other consumers/issues on the next maintenance invocation. An issue requiring more fresh GitHub verification than the bounded window remains deferred; partial response pages or cached permissions never authorize it. The existing all-open fetch remains bounded to its first 100 API rows.
