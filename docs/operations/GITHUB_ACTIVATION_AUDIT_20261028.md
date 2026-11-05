# GitHub source activation audit — 28 October 2026

This report contains public repository evidence. It is not a server acceptance report and does not certify a complete autonomous cycle. UNKNOWN remains distinct from failure or absence.

## Versions and CI

Main is `49fea218fe9000e3242da7a41d45db795b3eb33b`. All 406 downloaded Git blobs matched the complete GitHub tree. [Main CI 40246348155](https://github.com/Bbambaaamm/herdr/actions/runs/40246348155) passed. PR #181 head at this audit was `579cdf78752a8629ee3dd7f153f81bfc948052de`; [CI 40696433389](https://github.com/Bbambaaamm/herdr/actions/runs/40696433389) passed, with no submitted or inline reviews available for that head.

## Confirmed source blocker

[The independent P1 on #169](https://github.com/Bbambaaamm/herdr/pull/169#discussion_r4339055831) remains unresolved. Both main and the audited #181 head have `ADMISSION_TIMEOUT = 15.0`. The worker cannot acknowledge until its immutable code/Hermes/Python wrapper completes; the existing bridge startup allowance is 60 seconds. Two virtual-clock slow-wrapper regressions (45 and 60 seconds) fail before the fix. The correction shares the 60-second wrapper allowance and retains a separate bounded 15-second acknowledgement period. It preserves nonce/PID/start-ticks checks, ownership epochs, parent-death fencing and quarantine without automatic retry. These tests disclose a simulated clock; existing process/lock/death tests exercise real Linux behavior. A passing unit regression is not a whole native runtime proof.

## Merge reconciliation

| PR | GitHub state at audit |
|---|---|
| #36, #83 | Merged |
| #102 | Open, unmerged |
| #164, #165, #166, #167, #168, #169 | Merged; #169 still has the unresolved P1 above |
| #177, #178 | Open, unmerged |
| #179, #180 | Merged |
| #181 | Open, unmerged; reviewed acceptance pending |

Merged status is not deployed status. Issue #78 and #9 acceptance must bind actual installed source, policy and measurement window. The branch-protection endpoint was inaccessible to this connector (403); an empty ruleset collection does not establish that the branch is unprotected. No gate was changed.

## Architecture inventory

The exact main tree contains 80 `herdr/*.py` modules and 137 Python test files. This matrix records relevant artifacts; it does not declare the complete roadmap contract satisfied.

| Component | Existing owners | Source artifacts in main | Matching test artifacts |
|---|---|---|---|
| Durable TaskGraph / DAG | #9, #82 | `herdr/taskgraph.py` | `tests/herdr/test_taskgraph.py` |
| Dependency-aware scheduler | #9, #82 | `herdr/scheduler.py` | `tests/herdr/test_scheduler.py` |
| Agent lifecycle / leases / fencing | #82, #95 | `herdr/runtime.py`, `herdr/child_ownership.py`, `agent-stack/bin/agent-task-worker` | `tests/herdr/test_runtime.py` |
| Admission control | #69, #76 | `herdr/admission.py` | `tests/herdr/test_admission.py` |
| WorkBudgetAuthority / ledger | #87, #185 | `herdr/work_budget.py`, `herdr/work_budget_configuration.py` | `tests/herdr/test_work_budget.py` |
| Runtime isolation / capability grants | #76, #129, #132 | `herdr/security.py`, `herdr/policy_launch.py`, `herdr/private_profile_namespace.py` | `tests/herdr/test_policy_launch.py`, `tests/herdr/test_private_profile_namespace.py` |
| Hermes Harness | #129, #132, #181 | `herdr/hermes_guard.py`, `herdr/hermes_cli_identity.py`, `herdr/hermes_terminal_transport.py` | `tests/herdr/test_hermes_terminal_transport.py` |
| Agent Skills Registry | #72 | `herdr/skills.py` | `tests/herdr/test_skills.py` |
| Context Compiler | #73 | `herdr/context.py` | `tests/herdr/test_context.py` |
| Memory Fabric | #105 | `herdr/memory.py` | `tests/herdr/test_memory.py` |
| ProviderAdapter / Model Router | #79 | `herdr/capability.py`, `agent-stack/bin/agent_model_policy.py` | `tests/herdr/test_capability.py` |
| Smart Agent Adapter | #104 | UNKNOWN | UNKNOWN |
| MCP / A2A gateway | #70, #71 | `herdr/mcp.py`, `herdr/a2a.py` | `tests/herdr/test_mcp.py`, `tests/herdr/test_a2a.py` |
| Teamwork Engine | #103 | UNKNOWN | UNKNOWN |
| Execution Fabric | #95 | `agent-stack/bin/agent-task-worker`, `herdr/runtime.py` | `tests/agent_stack/test_dispatch_admission_protocol.py` |
| Prompt Runtime | #99 | `herdr/prompt_runtime.py` | `tests/herdr/test_prompt_runtime.py` |
| Event / Trigger Fabric | #100, #183 | UNKNOWN | UNKNOWN |
| Human Steering Plane | #100 | `herdr/approval_broker.py` | UNKNOWN |
| Eval Framework | #74 | UNKNOWN | UNKNOWN |
| Agent Evolution Lab | #98 | UNKNOWN | UNKNOWN |
| Reviewer / Verifier Fabric | #85 | `herdr/reviewer.py`, `herdr/work_result_receipt.py`, `agent-stack/bin/agent_completion_evidence.py` | `tests/herdr/test_reviewer.py` |
| Machine City / Agent Platform | #77 | `agent_platform_dashboard/production_sources.py`, `agent_platform_dashboard/production_contract.py` | `tests/agent_platform_dashboard/test_production.py` |
| GitHub CI/CD / deployment | #9 | `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `herdr/release.py` | `tests/herdr/test_release.py` |
| Recovery / rollback / incidents | #9, #78, #185 | `agent-stack/bin/agent-stack-recovery`, `herdr/ownership_epoch.py` | UNKNOWN |
| Repository Experience Graph | #145 | UNKNOWN | UNKNOWN |
| Research registry / daily & weekly reports | #182 | Registry issue #182 | UNKNOWN |
| Versioned pilot preparation / capacity | #126, #181 | Candidate #181 | Candidate #181 tests |

Basic context/memory, capability matching, workers and approval primitives are reusable foundations, not acceptance of complete #95/#100/#103/#104/#105 contracts. Targeted searches found no dedicated EventEnvelope/TaskProposal/SteeringRequest/RoutineManifest, TeamworkEngine/RoleGraph, EvolutionLab/EvalFramework or SmartAgentAdapter implementation symbols in the audited Python source. Other reusable primitives may exist; these gaps remain UNKNOWN until their required contract is traced and tested.

## Research and routine gates

#182 currently records an initial historical index and explicitly leaves paper-level metadata/deduplication incomplete. Its comments were empty at audit. Main has CI and release workflows only; this does not exclude an external research schedule. Recurring GitHub research writes are UNKNOWN until their actual schedule, delivery and exact write evidence are reconciled. Do not create a duplicate scheduler, register or evaluator. Research summaries are not verified scientific findings or authorization to implement a proposal.

Use #100/#183 for versioned routine provenance, freshness, scope, deduplication and admission. Use #184 for the one-issue canary and #185 for original uncertain-delivery reconciliation. No new issue, model allowance, merge, deployment or proactive execution is implied by this report.


## Security review follow-up

The later review of `dc21dad83415a8d38b034052f6bc93f59a67391b` supersedes
the earlier "no major issues" code-review receipt. It found three P1s and one P2:

- [HTTP child credential exposure](https://github.com/Bbambaaamm/herdr/pull/181#discussion_r4402350517):
  exec resets dumpability, and inherited credential pipes can be opened early.
- [Archive directory durability](https://github.com/Bbambaaamm/herdr/pull/181#discussion_r4402350541):
  verified file bytes do not by themselves persist directory entries.
- [Privileged response alias substitution](https://github.com/Bbambaaamm/herdr/pull/181#discussion_r4402350563):
  predictable temporary paths in a user-owned directory can redirect root writes.
- [Mutable publication client](https://github.com/Bbambaaamm/herdr/pull/181#discussion_r4402350591):
  a user-owned executable alias is not a trusted credential client.

The candidate now uses a fresh authenticated Unix connection created after the
HTTP child disables dumpability; inherited stdin/stdout carry no credential or
model response. Root responses use exclusive random temporary names, opened
descriptors and a protected root-owned response directory. Archive reclamation
requires fsynced files, archive directory and parent, including existing archives.
Publication selects the root-protected GitHub guard directly and pins executable
identity. Its credential-bearing transport stays root; the original unprivileged
ParentArtifactPublisher retains result verification and the durable intent ledger
and receives only the three bounded semantic transport methods. Dispatch and
reconciliation do not receive credential mounts.

Regression tests cover the original alias/durability failures, a real same-UID
observer, exact publisher PID authentication and masking credentials before the
unprivileged exec. These are component tests, not complete ordinary SDK acceptance,
actual inference, deployment proof or full autonomy. Exact-head CI and independent
review of these changes remain mandatory. No finding is considered resolved
solely because its implementation changed.


### Follow-up mount-ancestry finding

The independent review of `29769de8ddea12ec6c51f6a5473e2179a347df2d`
identified [one further P1](https://github.com/Bbambaaamm/herdr/pull/181#discussion_r4403382750):
a concurrent HOME/.config rename could retain a credential mount under its old
name while the publisher masked a replacement pathname. The regression now
executes the actual publish/child functions with synthetic credential bytes,
renames HOME/.config as the unprivileged user between mounting and masking,
and verifies the subsequent unprivileged process cannot read the old mount.
It fails on the reviewed source before correction.

The correction never mounts GitHub credentials beneath HOME. The root transport
selects GH_CONFIG_DIR under a root-owned 0700 parent. Before privilege drop the
publisher checks protected ancestry, pins the original directory object using
no-follow descriptors, mounts an empty view through those descriptors and
verifies that the named object was replaced with a root-only mount. This uses
[GitHub CLI's documented GH_CONFIG_DIR](https://cli.github.com/manual/gh_help_environment)
and preserves the existing guard. CI's transport stub now uses a root-owned
system executable rather than the runner-owned Python interpreter; executable
custody checks remain enabled, including a regression rejecting a changed client
before external execution. Neither change grants inference, dispatch, merge or
deployment permission. Exact corrected-head review and CI are still required.
