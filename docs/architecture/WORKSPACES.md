# Isolated coding workspaces

WorkspaceManager provisions one Git worktree per coding task on an exact base SHA. Worker jobs use only local Git operations and receive no GitHub write credentials.

A sealed ArtifactRef binds task_id, attempt, base_sha, local commit_sha, branch, changed-file manifest and a SHA-256 result_sha over those fields plus the actual bytes or deletion markers of every changed file. Review and integration must bind to this exact contract.

Seal requires a clean locally committed worktree. Integration revalidates the artifact and rejects a stale base. Same-file overlap or different bases are explicit conflicts. Cleanup retains the local branch/result commit and a 0600 artifact record; it never force-pushes or silently overwrites work.
