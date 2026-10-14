# VS Code + Hermes CVM Harness v2026.10.1

This runbook maps the external harness contract onto the existing Herdr/Hermes architecture without creating a second orchestrator.

## Runtime contract

For non-trivial engineering work use:

**Contract -> Plan -> Act -> Evidence -> Gate**

The stable rule is carried in each active Hermes profile's `SOUL.md`. It must contain no timestamps, current branches, tool outputs, or other per-turn state. Existing sessions keep their frozen/cached prompt; rule changes apply to newly composed sessions.

Hermes' native verify-on-stop mechanism remains the primary edited-code evidence collector. A bounded `pre_verify` shell hook adds only the final response gate: an edited-code turn cannot finish its first attempt without an `EVIDENCE BUNDLE` and explicit `Gate Status`. The hook is individually allowlisted; `hooks_auto_accept` stays disabled.

## Existing Herdr primitives reused

- `docs/architecture/PROMPT_RUNTIME.md`: immutable prompt/work contract and shared evidence acceptance.
- `docs/architecture/CONTEXT_MEMORY.md`: stable-prefix versus dynamic-envelope boundary and minimal context selection.
- `docs/architecture/MCP_GATEWAY.md`: minimal frozen node toolsets and omitted-tool authority.
- `docs/architecture/COMPLETION_EVIDENCE.md`: host-owned durable evidence and model-DONE rejection.
- `docs/CONSUMERS.md`: Herdr's own `herdr-core` task contract and isolated task worktrees.

No new scheduler, evidence authority, memory store, or tool router is introduced by this harness layer.

## Required host settings

- Active tool schemas: hard limit `<= 100`, target `<= 80`.
- `tool_loop_guardrails.hard_stop_enabled=true`.
- `hooks.pre_verify` points to `$HOME/.hermes/agent-hooks/cvm-evidence-gate.py`.
- The hook is explicitly allowlisted for each active profile.
- `hooks_auto_accept=false`.
- Secret files are checked by metadata only; their values are never read by the audit.
- Obsolete/unread configuration keys are removed rather than retained as apparent controls.
- Stable prefix and canonical tool schemas must have identical SHA-256 fingerprints across consecutive offline probes.

## Read-only audit

From this repository run:

```bash
python3 scripts/audit-agent-harness.py
```

The audit is offline/read-only with respect to Hermes. For every installed profile it:

1. runs `hermes prompt-size --platform cli --json`;
2. builds Hermes' real inspection agent with dummy credentials and no provider call;
3. hashes the actual `stable` system-prompt tier and canonicalized tool-schema JSON twice;
4. validates the hard `<=100` tool limit and reports `>80` as an optimization warning rather than a hard failure;
5. checks the harness rule, hard-stop guard, Evidence Gate hook and hook allowlist;
6. verifies `.env` and hook permission metadata without reading secrets;
7. fails if the obsolete `code_execution.max_tool_calls` key is still present;
8. fails if a schema outside the canonical toolset map is anything other than the approved lazy-discovery meta-tools `tool_search`, `tool_describe`, and `tool_call`.

A PASS therefore proves stable prompt/tool fingerprints for the inspected host at audit time; it does not claim that an upstream API provider actually granted a cache hit.

## Host verification workspace

On hosts where `/tmp` is a bounded tmpfs, run repository verification with a private test base on the host filesystem rather than relying on pytest's default `/tmp` location. A full or quota-limited tmpfs can otherwise create false test failures such as `git init: Disk quota exceeded` before the code under test executes. Use an isolated, task-owned directory (for example under `$HOME/tmp`), set `TMPDIR` to it, and pass it as pytest `--basetemp`; never delete another task's temp tree to make room.

## Scope boundary

A host audit can prove the Hermes runtime visible on that host. VS Code GUI state (open editors, local integrated terminals, extensions/panels) must be audited on the workstation that is actually running VS Code. If that workstation is offline or intentionally out of scope, L0 remains partial rather than being inferred.
