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

## Heating

Repository: Bbambaaamm/heating

Primary roles: repository engineering, diagnostics, tests, configuration review and safe deployment preparation.
Direct production actuation is not implied by Herdr access. Any Home Assistant write/deploy/actuation capability must be explicitly granted by Heating policy and should remain human-gated where safety-relevant.

## Contract

A consumer supplies:
1. pinned Herdr version/commit;
2. policy profile;
3. repository/tool allowlists;
4. resource and cost ceilings;
5. domain invariants;
6. project CI/review/merge authority.

Herdr supplies orchestration, scheduling, model routing, audit, telemetry, recovery and common observability.
