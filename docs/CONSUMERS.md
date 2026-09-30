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

## Herdr self-hosted control root

Repository: Bbambaaamm/herdr

Herdr may consume its own repository backlog only through the root-only control issue `#53`.
The root is repo-scoped durable work and must not flatten every open Herdr issue into an
independent scheduler task. The stable coordinator reads live issues/PRs/CI/review state,
derives the current dependency/gate view, completes the nearest dependency-safe slice and
replans after every merge.

The initial deployment reuses the already-provisioned `quantlab-hermes` Hermes transport
with `safety_profile=herdr` and explicit `repo=Bbambaaamm/herdr` identity. Code work must
use a dedicated Herdr clone/worktree; the QuantLab checkout is transport-only and must never
be repurposed. A future dedicated Herdr Hermes profile may replace the transport without
changing the root-orchestration contract.

The #9 elapsed-time soak is an acceptance gate for its own dependency path, not a global
stop signal: unrelated dependency-safe Herdr work continues while that evidence matures.
Paid-provider activation, new credentials, production deployment and other irreversible
external actions remain explicit gates.

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
