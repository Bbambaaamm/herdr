# Isolated coding workspaces

WorkspaceManager provisions one Git worktree per coding task on an exact base SHA. Worker jobs use only local Git operations and receive no GitHub write credentials.

A sealed ArtifactRef binds task_id, attempt, base_sha, local commit_sha, branch, changed-file manifest and a SHA-256 result_sha over those fields plus the actual bytes or deletion markers of every changed file. Review and integration must bind to this exact contract.

Seal requires a clean locally committed worktree. Integration revalidates the artifact and rejects a stale base. Same-file overlap or different bases are explicit conflicts. Cleanup retains the local branch/result commit and a 0600 artifact record; it never force-pushes or silently overwrites work.


## Durable child launch boundary

The bridge holds the admitted directory open and binds its device/inode to the
durable child identity. A host Python launcher duplicates that held directory
through the bridge's proc FD before entering bubblewrap's user namespace,
checks device/inode again, and passes the inherited descriptor through
--bind-fd or --ro-bind-fd. It never falls back to resolving the logical path.

A private tmpfs on the logical workspace parent supplies the mount destination.
Replacing or symlinking the host path after admission cannot redirect the
destination or expose a sibling worktree through that parent. Results remain
outside the worktree root and only the exact child result file is writable.

Before model delivery, the host verifies separate PID/mount namespaces, the
read-only host root, hidden Herdr configuration/releases, the canonical CLI
policy mount, and the actual workspace inode plus read/write mount mode.
Only that observation permits durable sandbox attestation. Physical tests cover
readers, writers, host path replacement, actual filesystem operations, sibling
result denial, and attestation replay without contacting a model provider.

Hermes toolset selection is a separate boundary: its file bundle contains
multiple tools. Exact invocation grants and credential/egress containment must
be enforced by the security envelope; schema omission alone is insufficient.


Root pane ownership is published to the canonical task queue before starting
the bridge, then mirrored to the attempt sidecar. Bridge identity, frozen policy
path, verified sandbox attestation and agent-start intent are persisted as
startup advances. Publishing a session cannot overwrite another run/idempotency
identity or authoritative lifecycle observations. Task writes use an atomic
replacement with file and parent-directory fsync. Crash regressions recover the
canonical record at bridge, sandbox and agent-start boundaries and close only
the owned pane. Failed child setup removes its frozen policy at every failure
stage; policy-copy failures also remove the incomplete temporary file.
