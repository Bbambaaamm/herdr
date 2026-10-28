# Approved native pilot operations

This package prepares the existing reviewed TaskGraph host factory, launch-plan
issuer and ordinary worker. It introduces no scheduler, work queue or budget
authority. The protected composition identifies runtime code, native entrypoints,
Python/Hermes release, operation sources, the frozen task and execution limits.
The private composition and authentication files are never publication inputs.

Order: verify composition and capacity; maintain the original login through the
official SDK as its owner; create a selected-key-only profile with no refresh
material; run the physical ordinary integration with mocked provider responses;
then admit the one approved live task. Only the existing host factory starts the
work budget clock. Preparation and administrator lifetimes are independent.
The live task retains its original fence, unknown reservations and cumulative
model allowance. Any started/uncertain attempt is reconciled, never redispatched.

`approved_pilot.py --composition PATH --sha256 HASH --check` is read-only with
respect to queue, budgets, credentials and service activation. Invocation without
`--check` performs the original approved one-shot admission path. The installed
sources and composition must be root-owned, read-only and reached through
protected, symlink-free ancestors. The operations package is loaded separately
from the worker runtime so it cannot shadow the worker's Herdr imports.

The selected credential must cover the larger of the grant lifetime and work plus
cleanup, plus the preparation bound and clock skew. Current pilot values are
2700/1800/600/300/30 seconds, requiring 3330 seconds. Short credentials fail
readiness; the worker cannot refresh or select an alternate provider/model.

Capacity admission keeps the existing 9 GiB stop floor plus 128 MiB start guard.
Additional measured preparation/growth allowances can only increase that bound.
A warning starts 256 MiB before the required bound. This is a bounded pilot
allowance, not proof of the broader persistent-capacity acceptance in #126.

`operation_archives` separates archive preparation from reclamation. It accepts
only bounded regular trees, independently verifies protected archives, checks
active process references, isolates a tree with no-replace rename, and restores
all original data if removal fails. Reclamation is explicit per source; there is
no periodic deletion policy or automatic removal of queue, ledger or evidence.

A fixture PASS is not real inference or acceptance. #9 remains open until the
live result, independent review, exact PR/CI, original-worker acceptance,
interrupted completion recovery, delegation, rollback and at least 24-hour soak
have their own evidence for the deployed composition.


## Credential and archive boundaries after security review

The HTTP child protects itself after exec and creates a fresh peer-authenticated
Unix connection. Inherited standard descriptors contain neither credentials nor
model responses. Root IPC responses are published through pinned no-follow
lookups into a root-owned response directory, with random exclusive temporary
files and descriptor-based metadata changes. Cache reclamation persists archive
file and directory names before isolating or removing any original.

GitHub publication keeps the existing ParentArtifactPublisher and its evidence
and intent authority. Its unprivileged process runs without GitHub credential
mounts. A bounded root peer executes only observe/push/create-PR through the
existing GitHubParentTransport and root-protected guard executable. Same-UID
processes with a different PID are rejected. Dispatch/reconciliation receive no
GitHub mounts. This does not relocate or redefine trust for existing host-wide
user-owned credential stores or other projects.
