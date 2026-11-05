# Consumer model

Each consumer pins one Herdr release/commit and supplies its own policy overlay.

## QuantLab

Repository: Bbambaaamm/Autonomous-Quant-Lab

Primary roles: research, coding, review, data/strategy tooling.
Hard invariant: PAPER-only. Herdr must never turn a model/tool permission into live broker authority.

## Maják

Repository: Bbambaaamm/dotacni-majak

Primary roles: web research, source verification, grant matching, document/workflow generation, coding and review.
Domain data, eligibility logic and source-quality rules remain in Maják.

### GitHub intake / completion root

Maják uses root-only autonomous intake. Herdr queues only consumer issue `#662`; the stable
`dotacni-majak-hermes` parent reads the live backlog/readiness state, selects the nearest
dependency-safe slice, delegates bounded child work, verifies consumer merge gates and replans.
Individual Maják product issues are not flattened into independent intake tasks.

Runtime GitHub intake consumers are declared in
`agent-stack/config/github-intake-consumers.json`. Durable intake/task identity is scoped by
`repository#issue` so issue numbers cannot collide across consumers.

## Herdr

Repository: Bbambaaamm/herdr

Herdr is also a consumer of its own orchestration runtime for repository maintenance and completion.
GitHub intake is root-only through issue `#53`: the stable `herdr-hermes` coordinator reads the
live Herdr backlog, derives dependency-safe AUTO work, delegates bounded child work and replans
after every merge. Individual Herdr implementation issues are not flattened into duplicate outer
durable tasks.

Runtime workspace: `/home/agentops/workspaces/herdr`.
Task worktrees: `/home/agentops/worktrees/herdr/` (outside the persistent checkout).
Repository policy profile: `herdr-core`.
The persistent Hermes process currently reuses the deployed `quantlab` Hermes runtime profile
for model/tool wiring only; Herdr repository authority and safety semantics come from the separate
`herdr-core` task contract.

A gated leaf does not stop unrelated AUTO work. Human/credential/external/privileged blockers
become a root blocker only when no dependency-ready AUTO work remains. Elapsed acceptance gates
such as the #9 soak are re-checked after cooldown and may never be fabricated.

## LOXXESS Technical AI Assistant

Repository: Bbambaaamm/loxxess-technical-ai-assistant

Primary roles: repository engineering, offline validation, documentation, configuration review and
safe preparation of the existing Microsoft Teams / Microsoft 365 / Power Platform solution.

GitHub intake is issue-scoped (`all_open`) and requires a fresh trusted maintainer acknowledgement
for each admitted issue episode. The stable `loxxess-hermes` coordinator reuses the deployed
`quantlab` Hermes profile only for model/tool transport. Repository authority and safety come from
the separate `loxxess-technical` task contract.

Hard boundaries include no DLP/ACP bypass, no unapproved billing/licensing/Gateway or production
publication, no exposure of raw private evidence or local configuration, and no claim of live
Teams/Microsoft 365 acceptance from offline tests or templates. Unknown stock is not zero, an
access failure is not an unavailable part, and owner-only success is not evidence for another user.

Runtime workspace: `/home/agentops/workspaces/loxxess-technical-ai-assistant`.
Task worktrees: `/home/agentops/workspaces/loxxess-technical-ai-assistant/worktrees/`.
Repository policy profile: `loxxess-technical`.

## Heating

Repository: Bbambaaamm/heating

Primary roles: repository engineering, diagnostics, tests, configuration review and safe deployment preparation.
Direct production actuation is not implied by Herdr access. Any Home Assistant write/deploy/actuation capability must be explicitly granted by Heating policy and should remain human-gated where safety-relevant.

### Repository-only Hermes pilot

Heating uses root-only intake through consumer issue `#172`. The stable `heating-hermes`
coordinator reuses the deployed `quantlab` Hermes runtime profile only for model/tool transport;
repository authority comes from the separate `heating-safe-engineering` contract.

The pilot is limited to repository inspection, isolated worktree edits, tests, documentation and
pull-request preparation. It grants no Home Assistant, Supervisor, SSH, MQTT, device, boiler,
reload, restart or production-deployment capability. A fresh maintainer approval bound to the
current issue revision is required before every admitted pilot cycle.

Runtime workspace: `/home/agentops/workspaces/heating`.
Task worktrees: `/home/agentops/workspaces/heating/worktrees/`.
Repository policy profile: `heating-safe-engineering`.

## Contract

A consumer supplies:
1. pinned Herdr version/commit;
2. policy profile;
3. repository/tool allowlists;
4. resource and cost ceilings;
5. domain invariants;
6. project CI/review/merge authority.

Herdr supplies orchestration, scheduling, model routing, audit, telemetry, recovery and common observability.
