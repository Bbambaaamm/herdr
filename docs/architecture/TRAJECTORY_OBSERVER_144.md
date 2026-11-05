# Bounded trajectory observer (#144)

This source increment reuses PR130's two advisory signals: total tool-step
threshold and longest consecutive tool-ID repetition. The observer is unwired;
there is no active shadow adapter, telemetry reader, feature flag, task callback,
model call or storage implementation in this module.

Inputs are host-sanitized tool identifiers, never prompts, credentials, arguments,
tool outputs or arbitrary telemetry payloads. IDs use at most 128 ASCII characters
and reject paths, control characters and recognizable credential shapes. Input
errors contain fixed codes. Hosts remain responsible for classifying/redacting
secrets that cannot be recognized by these patterns.

Each trajectory consumes at most 4,097 items and admits at most 4,096. Overflow
rejects; it does not silently truncate a trajectory. Both thresholds are strict
integers bounded by 4,096; boolean/numeric lookalikes reject. A caller-supplied
iterator must have terminating next() steps; this pure contract cannot preempt
arbitrary code in an iterator. Signals contain only kind, count and severity
`observe`. They cannot stop/retry a task, release a dependency, alter a lease,
grant, fence or budget, or accept a completion.

SyntheticTrajectoryCase and replay_synthetic_controls provide deterministic,
explicitly synthetic control replay. A replay admits at most 64 unique cases and
16,384 total events. Canonical input bytes are capped at 4 MiB and bound by a
SHA-256 digest, which is provenance, not a signature or acceptance receipt. Output
contains aggregate signals and control-label matches, without original tool IDs.
Equivalent inputs produce equivalent fresh outputs; changed thresholds or cases
change the input digest. Control matches are not production precision/recall.

There is no representative labelled/timed historical dataset or usage evidence
in this increment. Historical precision, detection rate, false-positive rate,
p95 overhead and token-cost correlation therefore have `value: null`, status
`UNKNOWN`, denominator zero and an explicit missing-evidence reason. Empty or
successful synthetic controls do not promote these values to measured success.
The API deliberately accepts no production-score override or live trace loader.

Issue144 remains open for independently assessed dataset provenance and coverage,
historical replay, measured quality/overhead/cost correlation and any later
disabled-by-default shadow integration. Research thresholds remain targets.
TaskGraph, admission, fencing, budget, verifier and recovery keep their existing
authority. Source tests and merge establish no physical/SDK, semantic or E2E
acceptance and authorize no operational activation.
