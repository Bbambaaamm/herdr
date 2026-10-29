# Reproducible offline acceptance for #184

Run the current checked-in contract regressions together before preparing a
privileged or economic canary. This command reuses existing intake, TaskGraph,
scheduler, budget, security, work verification, reviewer and parent publication
tests. It creates no alternative execution or recovery authority.

From a clean Linux checkout, as an unprivileged user with the existing CI Python
dependencies installed:

```sh
python scripts/probe-herdr-autonomy-offline.py --evidence-dir /tmp/herdr-offline-proof-UNIQUE
```

The output directory must not exist and must be outside the checkout. No network,
credential, administrator or model setup is needed. Test fixtures use temporary
repositories, queue data and synthetic transports. This command does not start
the live watchdog, read its queue, invoke a model, publish to GitHub, merge or
deploy. It runs once with a 15-minute bound and no automatic retry.

The command records JUnit, the test log and a JSON report bound to the Git head,
tree and all tracked source bytes before and after testing. Any required skip or
xfail, missing test, duplicate testcase, failed collection, nonzero exit, timeout,
dirty checkout or source drift blocks the aggregate result. Pytest plugin
autoload is disabled; the fixed test selectors cannot be replaced by CLI options.

## Coverage and limits

| #184 gate | Existing contract exercised |
|---|---|
| Duplicate event | Same approval replay and concurrent exclusive intake |
| Restart | Canonical TaskGraph replay and publication replay |
| Ambiguous delivery | Lost publication response and terminal UNKNOWN hold |
| Budget exhaustion | Parent/child shared ceiling and no refill |
| Invalid grant | Signed identity and alias rejection |
| Expired approval | Stale issue approval and publication permit |
| Worker crash | Lease recovery and stale-fence rejection |
| Provider outage | Uncertain provider stop without fallback/refill |
| Implementation test failure | Baseline repair boundary and validator rejection |
| Independent review rejection | Separate reviewer and explicit BLOCK |
| Exact artifact | Stale review rejection and independently imported Git bundle |
| No merge/deploy | Automatic operator-role denial and handoff-only publication |
| No duplicate economic effects | Durable pre-effect claims and retained inflight reservation |
| Consumer isolation | Repository-scoped intake identity and prior evidence |

`OFFLINE_CONTRACTS_PASSED` means these component contracts passed for the recorded
source. It is **not** proof of one connected native Issue → TaskGraph → SDK →
implementation → tests → independent review → draft PR run. The tests use
synthetic transport/reviewer inputs where their own fixtures specify them. The
report is advisory evidence, never an admission grant or a trusted worker result.
It deliberately reports `full_autonomy_verified=false`,
`native_sdk_cycle_verified=false` and no authority to dispatch, merge or deploy.
Historical cost and token measurements remain UNKNOWN.

## Remaining activation gates

Keep #185's original terminal UNKNOWN task and held accounting intact. Its
administrative classification does not make that work successful. Do not delete
maintenance gates or requeue the original action to obtain a green canary.

Use the existing #129/#132 physical envelope to verify the exact reviewed runtime
composition, parent/child lifetime isolation and rollback. Offline component
coverage does not replace that kernel/SDK proof. Reconcile stacked source PRs
before rollout; a passing unmerged PR is not an installed release.

After current-composition offline and physical evidence, require a separately
valid named issue, current revision approval, scoped capabilities, original
cumulative budget and explicit live-canary authorization. Run through #53's
existing intake and TaskGraph. Accept only original-worker artifacts, exact-head
tests/CI and independent review. Preserve unknown delivery on failure and recover
through the existing contract, without resetting attempts, budget or ownership.

Track the connected live acceptance in #184 and rollout/soak in #78. Proactive
routines remain under #100/#183; research under #182; evaluation/evolution under
#74/#98. Do not create duplicate backlog owners, schedules or dashboards.
