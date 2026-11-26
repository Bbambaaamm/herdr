# Step 4A: transactional systemd authority and capacity-safe RC6 rollback

Parent #53; implementation #264; capacity #126; previous #262 / #263; historical #60.
Development, independent review, protected merge and a new official release are
authorized. Staging configuration, drop-in, services, host-policy and Hermes are
not authorized to change during this work. No privileged staging commands are
part of this evidence. Tests use isolated files/processes, not live services.

## Reproduced cause

Base main/RC8: `832dbfecd7f9f9f4070f75230adc75565dce5d74`.
The original preflight checked base unit hashes but missed effective drop-ins.
The #126 override redirects maintenance to an existing local source tree whose
dispatcher/worker remain outside current. Removing it externally before apply
loses RC6's capacity guard on rollback: standard RC6 maintenance predates #126,
the journal did not capture drop-ins, and the controller restarts the restored
watchdog before returning to the operator. A later daemon-reload cannot change
the already running watchdog process.

Red-before-green: the original controller failed both new real-file tests:
`test_W22_candidate_watchdog_never_uses_baseline_dropin` and
`test_W19_journal_preserves_exact_override_authority`: **2 failed, exit 1**.
Remote isolated log: `/home/agentops/tmp/herdr-264-red.log`.

## Wider audit and exact measured authority

All six touched systemd units were read through systemctl show. In addition to
the watchdog override, export and Herdr oneshots have legitimate read-only
`sources.conf` drop-ins. The new closed checks preserve those exact mount files
and reject other loaded or pending unit-specific overrides, alternate fragments,
transient units, pending daemon reload, unexpected execution hooks/environment
files, and execution/user/working-directory drift. Candidate units are bound to
the same verified candidate manifest rather than validating themselves.

Measured watchdog drop-in: root:root 0644, 99 B,
SHA-256 `f5a0e3f8d20a7382a0abaef350f668a9e58c66dd9f622f4888968d194883a530`.
Measured watchdog script: root:root 0555,
SHA-256 `81ea7d476914c9e2e57b92565fdbe04f200b20db4135d1e0cc8b984e48f6adf9`.
Export source drop-in SHA-256:
`09cba797e1a7e32f2d5d7552029fdba0a68af09adee28ced76c5cd9e9e784f5c`.
Bridge source drop-in SHA-256:
`ff3151c4de83460048520673f0a7f5e7d637397d267bf7205f5b0155bf815153`.

The baseline approval descriptor pins exact symlink/owner/mode/content facts and
complete code-tree inventory digests for the existing operations tree (456 entries)
and maintenance tree (195 entries). Stable bounded no-follow file reads plus
directory identities and membership revalidation detect modification during scan.
This is a closed historical exception; its mutable agentops-owned maintenance
files are not relabelled root-owned immutable candidate code. Any drift blocks
restoration/dispatch until operator reconciliation. External CLI/helper paths
retain their existing authority; they are not new live model authorization.

## Transaction and rollback invariant

The v2 journal and retained root-only baseline-authority backup precede all
reconciliation. The exact #126 override is removed only after quiescence and a
persistent systemd transaction fence. The fence allows startup when no journal
exists, or when a protected volatile permit has been granted after full authority
verification. Power loss removes that permit and prevents unsafe RC6 activation.
The original drop-in and baseline authority are restored and verified before a
rollback permit/start. Incomplete rollback revokes permission, retains the fence
and journal and leaves dispatch stopped. No journal replay or separate restart.

## Test matrix and verification

W01 standard baseline/normal boot: effective-systemd and actual condition tests.
W02 approved RC6 exception: closed descriptor recognition.
W03/W25 unknown loaded/disk overrides: all six units.
W04 changed override; W05 owner/mode; W06 symlink/runtime inventory race.
W07 changed effective commands, environment, environment files, cwd, transient
state and pending reload; revalidation before apply mutation.
W08 before removal; W09 after removal; W10 reload; W11 bridge readiness;
W12 snapshot; W13 web; W14 candidate watchdog failures.
W15/W16 exact file restoration and permit before RC6 start, retained backup;
W17 restore/start/cleanup failure denies dispatch and retains fence/journal.
W18 actual SIGTERM after removal; W19 journal retained on SIGKILL (existing
subprocess test) and actual systemd power-loss condition without volatile permit.
W20 unfinished journal blocks before archive validation; orphan permit denied.
W21 existing real competing-process deployment-lock regression.
W22 candidate never uses baseline override; W23 complete existing capacity tests;
W24 existing exact PR60 recovery identity/admission tests; W26 healthy exercise.

Initial focused result: **86 passed, exit 0** (transaction/effective-systemd/
watchdog/capacity suites). Full release/security/integration/CI, final review,
merge and artifact verification are recorded separately when actually completed;
this document does not claim them in advance.

## Review findings addressed during implementation

Independent read-only review found the missing reboot startup fence, insufficient
candidate-unit binding, dependency directory membership race, stale-permit and
incomplete-rollback permit lifecycle, retained-backup and cleanup error handling.
Exact-HEAD review also reproduced the healthy RC6 + capacity-override exercise:
the override must be restored before the previous-runtime check and reconciled
again before final promotion. A dedicated W26 real-file regression covers both
the restored baseline and final override absence.
Actual systemd-analyze condition tests confirm OR-condition semantics without
touching services. Final exact-HEAD independent acceptance is still required.

## Deployment boundary

The previous RC8 tag and payload must not be altered or deployed with a manual
override-removal workaround. Select and verify a new annotated official release
after all merge/release gates; compute its archive/manifest/source/config digests,
reanalyze the complete RC6-to-candidate diff, then prepare exact protected paths
and updated capacity plan. No confirmation value precedes actual preflight.
Deployment of that new identity requires subsequent owner approval.
