# Root Authority Slice C — Physical Acceptance Contract

This document is the bounded acceptance contract for the existing root → child
execution path. It does not create a scheduler, provider registry, admission
authority, or production activation path.

## Authoritative path

| Transition | Existing owner and entrypoint | Binding that must be retained | Evidence required |
| --- | --- | --- | --- |
| TaskGraph → Scheduler | `herdr/scheduler.py` (`DynamicChildScheduler`, canonical parent admission and delegation methods) | Task/node/attempt/run, consumer, role, tools, permissions, policy and fencing | Durable scheduler/audit record and replay with no duplicate claim |
| Scheduler → Router v5 | `herdr/scheduler_routing.py` (`record_managed_route` and route validation) | Authoritative TaskNode, capability/provider/model identity, budget and attempt | Deterministic route decision plus rejection evidence |
| Router → ManagedExecutionHandoff | `herdr/launch_plan_handoff.py`, `herdr/policy_launch.py` (`PreparedPolicyLaunch`) | Exact grant identity, profile binding, runtime publication, mount plan and result slot | Handoff digest and fail-closed stale/tamper regressions |
| Host Authority → Root Issuer | `herdr/launch_plan_issuer.py` (`_policy`, `_grant`, `_physical`, `issue_request`) | Root-owned policy/publication, peer credentials, identity, fencing and exact argv/FD set | Root-owned issuer receipt; no source-only substitute |
| Root Issuer → Native Hermes root | `herdr/native_fd_handoff.py`, `herdr/host_bootstrap.py` | One-shot descriptor custody, sealed grant, bootstrap identity and deadline | Kernel peer/mount/PID evidence and one-shot consumption |
| Root → Managed child | `herdr/child_evidence.py`, `herdr/policy_launch.py` | Parent/child identity, narrowed tools/permissions, child fencing and workspace | Child namespace/profile proof bound to parent grant |
| Child → Durable result | `herdr/result_submission.py` (`reserve_empty_result`, `submit`, `publish_slot_payload`) | Result-slot identity, idempotency key, task/run/fence and zero-cost scope | Exactly one reserved slot and one accepted payload |
| Result → Parent acceptance | `herdr/parent_publication.py`, `herdr/child_evidence.py` | Accepted child receipt, evidence digest, parent task and completion authority | Durable acceptance/replay evidence; no duplicate acceptance |

## Gates and evidence levels

`TESTED_OFFLINE` means disposable fixtures or source tests only. It never
establishes `TESTED_PHYSICAL`, `DEPLOYED`, or `ACCEPTED`.

The current source provides the following gates:

- `herdr/policy_launch.py`: immutable-tree verification, profile binding,
  mount descriptors and sealed physical evidence.
- `herdr/host_configuration.py` and `herdr/runtime_publication.py`: schema-2
  root-approved publication provenance and retained-record digest.
- `herdr/native_lifetime.py`: native PID/mount namespace lifetime proof and
  fail-closed exit validation.
- `herdr/result_submission.py`: durable result-slot reservation and
  idempotent publication.
- `herdr/parent_publication.py`: parent-owned acceptance and replay lock.

None of these source gates is evidence that the merged source is deployed on
`quantlab-staging-01`.

## Disposable lifetime matrix

The following attacks are required in a Linux disposable envelope, each with a
fresh fixture, initial snapshot, kernel observation, denial/pass result, and
cleanup: same-UID rename before/after mount; symlink, dangling-symlink and
nested-path substitution; writable workspace alias; Python, Hermes, SDK and
runtime-tree replacement; mode-only mutation; stale manifest; verify/exec
TOCTOU; host-policy drift; and post-launch tampering.

The existing probes are `scripts/probe-herdr-physical-bootstrap.py`,
`tests/physical/clean_envelope.py`, and the native namespace tests. They are
not promoted to physical acceptance until executed on Linux with the reviewed
runtime and kernel evidence retained.

## Canary boundary

The zero-provider canary may start only after all of the following are
independently PASS: exact-head source integrity, root-owned runtime publication,
schema-2 host policy, issuer compatibility, trusted profile, network isolation,
runtime lifetime, parent/child identity, fencing, result binding, zero-cost
budget, rollback and operator approval. No source-only result can satisfy that
gate.

