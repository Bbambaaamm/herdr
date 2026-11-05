# Explicit MCP tool selection (#96)

The existing MCP gateway can expose an opt-in, bounded selection of its approved
tools. `gateway.tool_index(context)` projects host-owned bindings into a compact
index. It contains exact server/name/logical identity, version, definition hash,
policy hash, effect class and data classification. It contains no remote tool
description, input/output schema, example, credential or tool result, and does
not discover a provider.

The index is bound to the current task context, including attempt/fence and
toolset, and to the current capability registry and provider policies. It is
advisory discovery metadata, not a grant or evidence of runtime availability.
Existing static admission checks apply while constructing it. No new budget,
permission, approval, dispatch or acceptance authority is created.

The host constructs `ToolSelection(index.hash, chosen_entries, reason_code)` and
passes it to `gateway.model_context(context, selection=selection)`. The gateway
rebuilds and compares the current index, validates every exact choice, and runs
the existing runtime admission for all selected tools before discovering any
provider. A changed identity, schema, policy, task/fence or registry requires a
new selection. Duplicate, empty, malformed and oversized selections fail closed.
The selected schema is checked against its approved definition hash again when
it is copied from the provider catalogue. Selection hashes and a bounded reason
code accompany the resulting model context; a successful resolution is recorded
in the existing audit ledger.

Limits are 512 index entries, 512 KiB of canonical index metadata, and 32 selected
entries. Only the chosen full schemas enter this model context. MCP `tools/list`
still returns the selected server's approved catalogue; this change does not
claim to reduce that wire response. Unselected servers are not discovered.

Calling `model_context(context)` without a selection preserves its original
output and behavior. Normal `gateway.call` remains the sole execution path with
its existing per-call policy, permission, budget, idempotency and uncertainty
checks. A selection cannot authorize a tool omitted from the node toolset, and a
tool excluded from one prompt is not thereby revoked from an otherwise admitted
toolset. Any caller needing a narrower execution grant must use the existing
host toolset/admission mechanism.

This source increment uses synthetic transports and private test ledgers. It
does not activate a provider, execute generated code, add tool-use examples,
change transport discovery semantics, alter grants, or establish physical SDK or
end-to-end acceptance. Generic programmatic orchestration, example provenance,
provider-native adapters and measured quality/cost benefits remain separate
parts of #96.
