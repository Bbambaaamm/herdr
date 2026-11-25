# ChatGPT → Herdr: explicit selected root approval and activation gate

Status: SOURCE-ONLY, DRAFT. **NO LIVE ACTIVATION OR WORKER START.**

The previously developed ChatGPT proposal issues (#255), guarded GitHub
inspection (#256), double approval binding (#257) and durable consumption
transaction (#258) are combined with an explicit root-approval selection.

## Exact approval binding

The existing `HERDR-ADMISSION-V1` comment body supports one optional
`proposal_selection` only for root `Bbambaaamm/herdr#53`. The selection
is a closed object:

- `issue_number`: existing proposal issue number, not #53.
- `issue_id`: the GitHub issue's immutable numeric ID.
- `digest`: deterministic canonical ChatGPT request SHA-256.
- `revision`: current proposal GitHub issue revision SHA-256.

The commenter must retain current admin/maintain permission; the issue must
remain unchanged; the comment must be unedited, unexpired and pass all existing
`approved_revision` checks. The selected approval must be newer than the
proposal's own authenticated approval. A new root selected approval is **not**
equivalent to a generic root cycle and cannot be consumed by the normal
root-only scanner without the exact verified proposal binding.

The existing read-only helper now supports:

`agent-github-intake --approval-digest Bbambaaamm/herdr 53 --select-proposal N`

It first verifies the proposal's existing maintainer approval, current
canonical title/body, and GitHub identity. It then returns the proposed
selected root approval text. This command does NOT post the comment or
consume any approval.

Once the owner has explicitly posted both current approvals, the read-only
`--prepare-proposal-binding` path verifies matching selection and returns a
proposal/root binding with status `VALIDATED_NOT_ADMITTED`.

A future **host-owned** transaction may supply this verified binding to
the optional protected `_queue_issue_locked` path from PR #258. The
existing durable intent/claim transaction preserves idempotence and
crash-window quarantine. There is **no external route** to that internal
argument in this slice.

## End-to-end acceptance rehearsal

1. Prepare a small, non-destructive `inspect` proposal in ChatGPT, for a
   bounded existing Herdr issue/PR.
2. Create the candidate GitHub issue only after explicit user permission.
3. Post a valid proposal maintainer approval; do not treat issue author/labels
   as authority.
4. Generate the root #53 selected approval with the read-only helper and
   review its exact target, SHA-256 and expiry before posting.
5. Verify the complete double-approval chain via
   `--prepare-proposal-binding`; expected result:
   `VALIDATED_NOT_ADMITTED`, `task_created=false`.
6. Offline integration test: use fixture approvals and the existing locked
   transaction to prove exactly one root task, durable state, crash
   quarantine and duplicate denial. Do NOT create a live task as part of
   this test.
7. Before live activation: the trusted host controller MUST independently
   verify active/PAUSED supervisor and existing owner, run/fencing token,
   capacity, approved model credentials and deployment identity, plus CI,
   independent security review, formal approval and release provenance.
   Only after a separately authorized immutable release can a live dry-run
   be considered. The CLI here deliberately cannot trigger it.

These steps are separate: **GitHub proposal ≠ approved root episode ≠
host admission ≠ actual worker start ≠ completed PR**.

## Security review follow-up (2026-11-25)

An internal transitive review identified two additional requirements:
(1) An approved, selected proposal must generate a **target-specific** root
prompt, not the general backlog-drain prompt, or a valid approval could
produce the wrong economic task. The selected prompt is now deterministically
limited to the approved operation and issue/PR number; it never copies the
untrusted proposal objective as an instruction.
(2) Approval chronology is compared as actual offset-aware UTC instants,
not lexicographically as timestamp strings. Durable claim states use
strict string types so malformed untrusted data fails closed.
These changes are covered by negative tests; independent Codex review and
GitHub formal approval remain separate, unsatisfied release gates.
