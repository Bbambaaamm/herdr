# Defect observation → admission decision bridge

Status: draft implementation on `feat/100-defect-admission`, stacked on
`feat/100-operational-incidents-p0` (#229).

## Ownership

- #100 remains the single Event/Trigger and Human Steering owner.
- #53 remains the sole autonomous backlog control root.
- #82 remains the durable task identity and execution authority.
- #87 remains the budget and economic reconciliation authority.

This module adds no scheduler, no budget ledger and no second source of truth.
It is a **proposal-only** classifier: its output is a `TaskProposal` payload that
must still pass the existing `AdmissionControl` / TaskGraph path. A decision here
is a request, never authority. Every `ADMIT` carries
`authorizes_execution: False`, `task_proposals_submitted: 0` and
`budget_operations: 0`.

## Normalization

`DefectObservation` pins one authenticated observation to an exact source
revision:

| Field | Meaning |
| --- | --- |
| `source` | authenticated origin (`CI_CHECK`, `REVIEW_COMMENT`, `VALIDATION`, `SECURITY_SCAN`, `RUNTIME_TELEMETRY`, `DEPENDENT_PR`, `EVIDENCE_STALENESS`, `UNTRUSTED_TEXT`) |
| `category` | defect class |
| `repository` | `owner/repo`, allow-listed by the caller |
| `commit_sha` | exact 40-hex source revision the observation is about |
| `ref` | branch or PR |
| `subject` | bounded tuple of identifiers (≤4) |
| `observed_at` | freshness |
| `evidence_sha256` | ≤4 bounded evidence digests; `UNKNOWN` requires evidence |
| `workflow` / `check_run_id` / `event_revision` | delivery identity |
| `finding_identity` | stable identity of the specific finding (required for every source) |

Fail-closed validation: malformed SHA/repo/ref/subject/timestamp/evidence raises
`DefectError` rather than being coerced. A source may only carry categories it
can actually observe (`SOURCE_CATEGORIES`); anything else is rejected, not
re-labelled. A known defect must carry at least one evidence digest — a CI
observation from the #100 adapter proves only "this exact revision failed a
required check", so `CI_CHECK` may not claim `TEST_REGRESSION` without per-test
evidence.

## Identity

- `fingerprint` = `digest([SCHEMA, source, repository, commit_sha, category, subject, workflow, finding_identity])`
  — semantic defect identity. A regression on a new revision is a new identity,
  and two distinct findings sharing a subject — two required checks, two review
  comments, two runtime errors — are distinct defects rather than one collapsed
  record. A repeated run of one finding (new `check_run_id`) is still the same
  defect: the run id is delivery identity.
- `deduplication_id` = `digest([fingerprint, workflow, check_run_id, event_revision, observed_at])`
  — delivery identity, so a redelivered webhook is not a new defect.

## Decision order (first match wins)

`DefectContext` carries **no healthy defaults**: budget, credentials, capacity,
repair state and resolution state must all be supplied as verified observations.
An unobserved state can never silently read as healthy and fall through to
ADMIT.

1. `UNTRUSTED_TEXT` → `DENY`
2. repository not authorized → `DENY`
3. credentials `MISSING` → `CREDENTIAL_GATE`
4. credentials `UNKNOWN` → `UNKNOWN`
5. budget `EXHAUSTED` → `BLOCKED`
6. budget `UNKNOWN` → `UNKNOWN`
7. capacity below floor → `BLOCKED`
8. category requires an operator (security findings) → `HUMAN_GATE`
9. already resolved → `NO_ACTION`
10. a repair is already active for this defect → `NO_ACTION`
11. `repeat_count >= max_repairs` (authoritative config) → `BLOCKED`
12. otherwise → `ADMIT` with a bounded single-node proposal

Unknown economic state is never treated as zero and never as permission.

## Durable dedup

`DecisionJournal` writes through the existing `admission.AuditLog`
(append-only JSONL, mode 0640) and serializes the check-then-append under an
inter-process `flock`, so concurrent deliveries of one decision produce exactly
one durable record. The dedup key is
`(fingerprint, commit_sha, disposition)`:

- the same event redelivered (restart, retry, duplicate webhook) creates no
  second record;
- the same defect reappearing on a **new** revision creates a new record;
- a changed PR HEAD invalidates an older approval (`approval_is_stale` compares
  the pinned `commit_sha`).

## §8 fault-injection coverage

Covered deterministically offline by `tests/herdr/test_defect_admission.py`:

| Scenario | Fixture |
| --- | --- |
| A new CI regression → one proposal | `test_a_…` |
| B duplicate CI event → no duplicate record | `test_b_…` |
| C known resolved defect → NO_ACTION | `test_c_…` |
| D reopened failure on a new SHA | `test_d_…` |
| E review finding follows the same workflow | `test_e_…` |
| F worker crash during patch → durable recovery | `test_f_…` |
| G crash after possible side effect → reconciliation | `test_g_…` (UNKNOWN, no second economic attempt) |
| I budget exhausted → BLOCKED | `test_i_…` |
| J missing credentials → CREDENTIAL_GATE | `test_j_…` |
| K unauthorized repository → DENY | `test_k_…` |
| L malicious comment is data, no grant escalation | `test_l_…` |
| M repeated failure → bounded stop | `test_m_…` |
| N successful fix → next selection | `test_n_…` |
| O capacity below floor → no unsafe work | `test_o_…` |
| P changed PR HEAD invalidates old review | `test_p_…` |
| Q ingress restart → no loss or duplication | `test_q_…` |
| R source change after approval → stale approval rejected | `test_r_…` |

Not covered here, by design:

- **H (provider HTTP 429 → bounded wait or approved fallback)** is owned by
  Router v5, delivered in PR #236.
- **F/G with a real crashed worker and live economic side effect** require the
  durable event consumer and the #85/#87 reconciliation path. If no approved
  long-running consumer is deployed, that integration is prepared but not
  activated.

## E4 independent review

Seven rounds against exact HEADs; all findings were fixed and the seventh round
returned **PASS (P0 0 / P1 0 / P2 0)** on
`3441ee2afbe308aed58276d1e1e8fab779fdb62d` (isolated export of that HEAD).

| Round | HEAD | Result |
| --- | --- | --- |
| 1 | `81ae0be0` | FAIL — 3×P1, 3×P2 (unhandled context states; fingerprint keyed on delivery id; non-atomic dedup; loose ref/timestamp/evidence; proposal not carrying the counters; `CI_CHECK` claiming unproven categories) |
| 2 | `a9570129` | FAIL — 3×P1, 1×P2 (healthy defaults on `DefectContext`; workflow not a check identity; mutable ADMIT payload) |
| 3 | `b92caf0c` | FAIL — 2×P1 (run id is not a stable check identity; nested `graph` mutable) |
| 4 | `027ec320` | FAIL — 1×P1, 1×P2 (only `CI_CHECK` required a stable identity; `_freeze` passed sets through) |
| 5 | `0506385b` | FAIL — 0×P1, 2×P2 (mutable `int` subclass; non-string `finding_identity` raised `TypeError`) |
| 6 | `605db0c2` | FAIL — 1×P1 (state membership checked without an exact type) |
| 7 | `3441ee2a` | **PASS — P0 0, P1 0, P2 0** |

Residual UNKNOWN outside the reviewed scope: this module does not itself call
the authenticated #100 source nor obtain `DefectContext` values from the
authoritative runtime, so their provenance cannot be proven by this PR. The
PASS does not extend to that future integration.

## Event Fabric bridge (`herdr/defect_event_bridge.py`)

`#100` owns the single Event/Trigger surface; `#53` owns the backlog. The bridge
is a pure translator between them and adds no authority:

- `DEFECT_CATEGORY` is the whole translation table — only an **open**
  `Source.CI` / `CI_VALIDATION_FAILED` observation is a code defect. Capacity,
  backup and worker incidents belong to their own operational owners and are
  never routed into a repair backlog.
- `defect_from_observation()` derives `commit_sha` from the #100 `head` fact
  and uses #100's own `correlation_id` as the finding identity — computed from
  #100's pinned (source, scope, subject) payload, so it is verifiable, stable and
  exactly #100's correlation granularity. No caller-chosen string is used as
  identity. #100 publishes no finer stable id today (`job_id` is a per-run
  instance), so distinct jobs inside one workflow are one defect; a finer split
  needs #100 to publish the workflow job definition id. Only an open observation
  reporting an actual `CI_FAILURE` is a defect.
- `repair_tools()` reuses `ROLE_TOOL_ALLOWLIST["writer"]`; `git_push`,
  `deploy` and `git_merge` stay out of reach.
- `task_graph_spec()` is a single-node plan; `AdmissionControl` still applies
  its own ceilings and its own consumer policy.
- `admission_proposal()` takes a #100 `OperationalIncident` envelope, never a
  bare observation or a raw webhook, and requires the caller's `pin` to be one
  of the envelope's own evidence digests. Provenance beyond that is #100's
  EventEnvelope boundary, not the bridge's.
- The defect decision is recorded durably, and the gate verdict separately
  (`defect_admission_gate`). Only a recorded ALLOW makes the proposal
  idempotent: a pending verdict (crash between the two writes) or a denied one
  stays re-evaluable, so a transient gate denial can never wedge a repair. A
  later ALLOW replaces an older DENY, so the durable last word is never a stale
  denial. The claim, the gate call and the verdict write share one advisory
  lock, so concurrent deliveries of one defect cannot both reach the gate.
- Before asking again, the journal reconciles with the gate's own durable audit
  log (`AdmissionControl.has_allow`): an ALLOW recorded there with no verdict
  here is a crash between the two writes, and is deduplicated rather than
  re-requested. The two logs are not one transaction, so this is the only place
  the crash window is closed.
- The defect gate's own verdict is authoritative for its disposition: a
  BLOCKED defect stays blocked even if an earlier delivery of the same
  fingerprint was allowed by the swarm gate.
- The gate object must be the real `AdmissionControl`; the journal is
  mandatory. The returned proposal carries `authorizes_execution=False`,
  `task_proposals_submitted=0` and `budget_operations=0`. When the defect gate
  denies, the swarm gate is not consulted at all.

## Known boundary (not closable in this PR)

The bridge can require a #100 `OperationalIncident` envelope and a matching
evidence `pin`, but it cannot *authenticate* that envelope: both values arrive
from the same caller, and #100 exposes no signature or independently-verified
record primitive today. End-to-end provenance is therefore #100's
EventEnvelope boundary. Closing it needs a #100-side primitive (a durable
per-check identity plus an independently verifiable envelope digest); until
then the bridge must not be wired to any consumer that treats its proposal as
authenticated input.

Ownership is unchanged: `#100` produces the observation, `#8` admits or denies
the spawn, `#53` owns the backlog, `#82` the durable task identity.

## Out of scope

Live model calls, merges, deployments, credential creation, budget changes and
any widening of the approved provider/model/endpoint/egress set.
