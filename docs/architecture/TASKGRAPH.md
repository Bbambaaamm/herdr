# TaskGraph v1.1 contract

`herdr.taskgraph` is the canonical durable planner contract for Herdr. It is generic infrastructure: consumer-specific invariants such as QuantLab PAPER-only remain in each consumer policy and are not embedded in the core schema.

## Planner boundary

Planner output is a strict JSON object with `envelope` and `nodes`. Unknown or missing fields fail closed. The machine-readable structural contract is `docs/contracts/taskgraph-v1.1.schema.json`; semantic checks that JSON Schema cannot express are enforced by `TaskGraph.parse_planner_output()`.

The envelope binds an issue/spec hash, graph version, planner identity and consumer policy profile reference. Planner-requested node/depth/fanout limits may lower, but never raise, Herdr hard caps. Node metadata includes bounded timeout and retry count. Runtime state records lifecycle, attempt and optional lease/fencing identity with expiry.

## Graph semantics

`parent_id` is hierarchy/authority, not a scheduling prerequisite. `dependencies` are the authoritative scheduling DAG. The two edge sets are intentionally exposed separately so a child may report to a parent without forcing the parent to complete first.

Every non-root parent must exist. Parent hierarchy and dependency DAG are each acyclic. A child tool/permission set must be a subset of its direct parent policy. Unknown parents or dependencies, duplicate nodes, cycles and escalation attempts fail closed.

## Determinism

`graph_hash()` is SHA-256 over canonical structural JSON. It excludes `created_at`, sorts nodes by ID, normalizes set-like fields, and recursively sorts object keys. Equivalent planner structures therefore produce the same hash independent of creation time or list ordering where ordering has no semantic meaning.

## Secrets

Task payloads never carry credentials. Secret-like keys and high-confidence credential value patterns are rejected without echoing secret values into errors. Consumer runtimes resolve authorized credentials out-of-band after admission.

## Durable event log

`PersistentTaskGraph` is a single-writer append-only JSONL store. Complete events are fsync'd and bound to the exact graph hash. Replay initializes every node to `pending`, rejects malformed complete records, duplicate JSON keys, unknown event types/nodes or cross-graph events, and ignores only a final non-newline-terminated crash fragment.

This contract deliberately does not implement scheduling, worktrees, model execution or merge authority. Those belong to later Herdr milestones and consumer CI/review gates remain authoritative.
