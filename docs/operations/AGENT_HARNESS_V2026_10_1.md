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

- Active tool schemas: <= 100, target <= 80.
- `tool_loop_guardrails.hard_stop_enabled=true`.
- `hooks.pre_verify` points to `$HOME/.hermes/agent-hooks/cvm-evidence-gate.py`.
- The hook is explicitly allowlisted for each active profile.
- `hooks_auto_accept=false`.
- Secret files are checked by metadata only; their values are never read by the audit.
- Obsolete/unread configuration keys are removed rather than retained as apparent controls.

## Read-only audit

From this repository run:

```bash
python3 scripts/audit-agent-harness.py
```

The audit calls only offline/read-only Hermes inspection commands. It probes every installed profile twice and compares the stable prompt section plus tool schema metadata, validates the <=80 target, checks the harness rule and Evidence Gate, verifies secret-file permission metadata, and reports `gate_status: PASS|FAIL`.

## Scope boundary

A host audit can prove the Hermes runtime visible on that host. VS Code GUI state (open editors, local integrated terminals, extensions/panels) must be audited on the workstation that is actually running VS Code. If that workstation is offline or inaccessible, L0 remains partial rather than being inferred.
