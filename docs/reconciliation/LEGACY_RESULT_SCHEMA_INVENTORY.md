# Legacy result schema inventory

This inventory is derived from the producer contracts present in the current
repository (`herdr.evidence`, `herdr.accepted_index`, and the read-only
durable identity adapter). It is not a claim that the staging records were
read. A fresh staging export is required before any live replay.

## Observed contracts

* `herdr-accepted-evidence-v2`: `EvidenceStore` publishes version `2`
  envelopes. Control cycles use
  `environment.collector=host-control-v1` with `proof.source=host-schema-v1`;
  verified worker results use `environment.collector=github-api-v1` with
  `proof.source=github-api`. Its identity uses `id`, `run_token`, `attempt`,
  `idempotency_key`, and `fencing_token`. The adapter normalizes only the
  explicit `attempt` alias to `attempt_id` after the exact pair checks.
* `herdr.evidence.ArtifactRef-v1`: the immutable artifact shape uses
  `task_id` and `attempt`, but it is artifact evidence, not a result identity
  or completion authority.

The adapter never invents `consumer`, `ownership_epoch`, `repository`, `issue`,
run tokens, fencing tokens, or idempotency keys. Missing or conflicting values
remain `UNKNOWN`/fail-closed. Unversioned `attempt` or `attempts` fields are
not decoded.

## Live replay status

`NOT_RUN`: no fresh authoritative read-only staging export was available in
this checkout. The historical 73-row counts in the task contract are retained
as context only and are not re-published as current evidence.
