# QuantLab #248 — independent review and operator handoff

**Status: NOT APPROVED, NOT READY TO PUBLISH.** This packet describes checks and immutable evidence requirements, not a live grant, a sudo script or an authorization to resume tasks.

## A. Independent security reviewer job (read-only)

**Target:** Herdr PR #250 at the *fresh* exact HEAD of its GitHub branch. Use a different reviewer/model/session from the author. No tool calls with paid models without separately authorized budget. Do not submit a GitHub APPROVE review from the author account or impersonate a reviewer.

1. Record reviewer identity, runtime/model, time, PR base/head SHA and clean checkout status. If no independent reviewer can be provisioned within existing host policy, report `REVIEW_NOT_RUN` and retain this gate; do not use the blocked QuantLab #278 task as the reviewer.
2. Audit only changed files against `herdr/security.py`, `herdr/host_configuration.py`, `herdr/policy_launch.py`, `deploy/herdr/cutover/activate_heating.py`, `tests/herdr/test_host_configuration.py`, consumer `quantlab-paper` and exact current system policy metadata. No secrets or model credentials in review output.
3. Evaluate: (i) fixed UID/consumer/workspace/results binding, (ii) no excess tools/egress/process or nonzero cost, (iii) exact pinned executor authenticity vs mere syntax, (iv) policy delta TOCTOU and stable filesystem reads, (v) root/child/fencing/budget subset, (vi) provider and credential refs genuinely approved by host, (vii) PAPER-only execution boundary in QuantLab rather than metadata-only assertion, (viii) expiration and renewals, (ix) immutable release/code/runtime fingerprints, (x) signed/owned operator approval and rollback, (xi) no unsupported root permission escalation, (xii) negative tests on actual host launch path, not only isolated validator.
4. Run exact-head CI checks and at least `tests/herdr/test_quantlab_host_policy.py` and original host config/security/activation tests with pinned dependencies. Any missing dependency or inconclusive test must be recorded as NOT VERIFIED.
5. Return an evidence record: reviewer id, PR HEAD, files/lines for each finding, P0/P1/P2 severity, reproduction, test result, and `PASS` only if no unresolved P0/P1. Explicitly distinguish a preflight validator from a complete grant issuer/publisher. Never merge/deploy from an author's self-review.

### Current author-side static-review findings to be tested independently

- **P0 deployment gap:** PR #250 contains no trust-authorized grant minting or operator publish logic; successful validator alone cannot recover Hermes.
- **P1 proof gap:** validation of `hermes:<version>:sha256:<hash>` syntax is not proof of hash equivalence to the immutable installed Hermes binary.
- **P1 safety gap:** `PAPER-only` is a separate runtime/consumer boundary; host grant metadata alone does not prove no real broker or outbound money flow.
- **P1 acceptance gap:** a schema-1 policy without QuantLab and expired other grants cannot be treated as source authority, even if GitHub intake accepted issue #278.

These are open checks, not an independent verdict.

## B. Privileged operator preflight and approval package

**Inputs from trusted operator system, not from issue/model output:** exact installed release tag/commit and source/runtime manifests; approved *current* host parent/consumer authority for `github:Bbambaaamm/Autonomous-Quant-Lab`; approved Nous provider route/opaque credential references; pinned Hermes binary identity; proposed policy document with one new QuantLab grant; pre-change host-policy SHA-256; backup and recovery evidence; lock/lease/budget/capacity status.

**Proposed scoped fields:** see `QUANTLAB_HOST_GRANT_APPROVAL_PROPOSAL.md`. First canary lifetime proposed as 24h, cost 0, approved tools exactly seven, write scope only `/home/agentops/workspaces/quantlab`, no process or live-broker permissions. Do not copy expired Heating/Herdr template. Preserve all existing templates byte-for-byte and global policy fields.

**Read-only operator commands, from an authenticated SSH session:**

```bash
id
stat -c '%U:%G %a %n' /etc/herdr/host-policy.json
sha256sum /etc/herdr/host-policy.json
readlink -f /opt/herdr/current
systemctl is-active agent-stack-watchdog.service
systemctl is-active herdr-capacity-watch.service || true
df -h /
```

The operator must compare all generated evidence to a signed/reviewed admission manifest. The trusted host reader `herdr.host_configuration._read_configuration` and `herdr.quantlab_host_policy.validate_policy_delta` should be executed from the **exact reviewed immutable release**, not a mutable worktree. The latter is a *proposal-only* check: it cannot attest provenance, approve new authority or issue credentials.

**GO criteria:** exact-head CI and independent review PASS; current trusted parent authority explicitly authorizes QuantLab; new grant is a bounded subset of that authority; initial expiry, provider, pinned executor and immutable code/runtime hash match; RC6/RC7 capacity/recovery gates, rollback archive and owner approval are evidenced; no contradictory active workers or uncertain delivery. All conditions are AND, not alternatives.

**NO-GO criteria:** missing/expired grant; unverified executor hash; changed issuer/parent policy; lack of rollback/restore evidence; failure to acquire existing deployment/worker locks; uncertain original #278 delivery; incomplete CI/review or changed PR HEAD. Stop with exact blocker and retain current root policy.

**Only after GO**, separately invoke the existing, independently reviewed root-owned publication procedure with explicit operator authorization and hash-pinned candidate. Require atomic write, fsync, root owner/mode, reread/hash, fresh smoke checks, and verified rollback. This packet contains no publication command and no automatic sudo escalation.

## C. Post-publication canary

Do **not** manufacture a new approval or enqueue a second task. Reconcile original `github-quantlab-issue-278-approval-7103063169` against run/fence/session/result and absence of actual model delivery; use only supported Herdr recovery operation. Require durable outcome, independent exact-head code review/CI, draft PR and next dependency-ready selection. Verify QuantLab's own order routing remains PAPER-only.
