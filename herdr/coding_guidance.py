"""Single shared, advisory coding discipline for Herdr root and child workers.

Adapted from https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md.
The frozen Herdr work plan, consumer policy, grants and host oracle take precedence.
"""

CODING_DISCIPLINE = (
    "\nCODING DISCIPLINE (advisory; frozen host/consumer policy takes precedence):\n"
    "- Think before editing: surface material uncertainties, assumptions and tradeoffs. "
    "Use the existing INFO_REQUIRED gate only if intent, safety, scope or acceptance "
    "cannot be bounded; otherwise record a bounded assumption. State when a simpler "
    "approach meets the goal.\n"
    "- Simplicity first: solve only the approved goal, using existing conventions. "
    "Avoid speculative features, one-off abstractions, unrequested configurability "
    "and scaffolding for demonstrably unreachable cases. Prefer less code when equally correct.\n"
    "- Surgical changes: preserve unrelated logic, comments and formatting; match "
    "the local style and avoid opportunistic refactors. Remove only imports, variables "
    "or functions made unused by your own edit; report pre-existing dead code separately. "
    "Every changed hunk must trace to the approved objective/acceptance.\n"
    "- Goal-driven verification: for multi-step work, use a short plan with a check "
    "for each step. Reproduce bugs with an approved regression check when feasible; "
    "compare refactor behavior with the baseline. Verify with the frozen host oracle, "
    "retry only on new evidence within budget, never weaken protected checks, "
    "and stop implementation after PASS.\n"
)
