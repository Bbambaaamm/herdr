# ChatGPT to Herdr: phase-1 proposal contract

Status: OFFLINE, proposal-only. NOT a worker, scheduler, intake, execution gateway,
authentication service, grant issuer or release authority.

ChatGPT should be a task-facing user interface. Hermes remains cognitive parent,
Herdr owns durable TaskGraph and host authorization, GitHub remains the existing
CI, maintainer approval, review and merge authority. Existing Herdr intake
is root-only on Bbambaaamm/herdr issue #53. An ordinary new GitHub issue
cannot directly authorize work, and a ChatGPT message is not a host grant.

## Closed request and output

herdr/chatgpt_command.py accepts one bounded UTF-8 JSON document with exactly:
version=1; repository=Bbambaaamm/herdr; root_issue=53; operation one of
inspect/implement/review; target_kind issue/pull_request; target_number positive
32-bit integer; objective (1..1600 characters); constraints (up to 12 distinct
strings, 1..320 characters each). Control characters and bidi overrides are
rejected. Duplicate JSON fields, unknown fields, nonfinite or invalid values
are rejected. The deterministic content SHA-256 provides a correlation key
but is NOT an authentication credential or durable idempotence reservation.

The offline CLI agent-stack/bin/agent-chatgpt-proposal --propose INPUT.json
renders a candidate GitHub issue body containing HERDR-CHATGPT-PROPOSAL-V1.
It never outputs a maintainer-comment-v1 approval or schedules a worker.
It has no network calls, queue writes, provider calls or host mutations.
The authenticated ChatGPT GitHub connector may post this candidate only on
explicit user authorization and only after checking for existing matching
proposal digests.

## Planned activation slice (NOT implemented)

Build an authorized root #53 proposal resolver within the existing
agent-github-intake pathway. Use existing maintainer identity, revision-bound
approval, consumed approval IDs, protected durable task ledger and current
TaskGraph episode, not a second scheduler/database. Validate current
pending/running/blocked/terminal states and active owner to prevent duplicate
economically meaningful attempts. Proposal issue contents remain untrusted.
PAUSED supervisor state, model unavailability, host capacity and release gates
are not bypassed.

## Required acceptance

- Creation of candidate proposal is not execution authorization.
- Duplicate/stale/edited requests do not cause repeated work.
- One authenticated maintainer approval binds one unchanged request and episode.
- Persistent records survive restart without a new economic attempt.
- Task identity, fencing, run token, budget and review gates remain canonical.
- ChatGPT status is grounded in durable evidence, not terminal or model text.
- No merge, deployment or restart without their separate host authority.

## Phase 2A: existing intake read-only inspection

The existing `agent-github-intake` can inspect one GitHub proposal through
`--inspect-proposal Bbambaaamm/herdr ISSUE_NUMBER`. It uses only the
pre-existing authenticated `gh api` GET transport and validates the actual
GitHub repository/issue revision. `CommandProposal.from_github_issue`
requires the entire canonical issue title/body to match the deterministic
renderer, preventing edited/forged markdown and digest mismatches.

The result includes the proposal SHA-256, repository issue revision SHA-256,
target and operation, plus `PROPOSED_ONLY`,
`execution_authorized=false`, `task_created=false`. No new authorization
channel, queue, worker, network listener or GitHub writer was added.

**Still required:** a separate implementation of a host-authorized,
revision-bound, single-episode proposal-to-root-#53 admission binding.
This read-only inspection is NOT a replacement for
`HERDR-ADMISSION-V1`. A proposal issue cannot be submitted as an
agent task by this command; the existing root-only intake continues
to admit only issue #53 with valid maintainer acknowledgment.
