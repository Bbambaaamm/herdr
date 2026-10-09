# Microsoft 365 Gateway

## Purpose

\`herdr.m365_gateway\` is a host-side, read-only integration boundary for
Microsoft 365 retrieval through an already approved Microsoft tenant path. It
does not grant Herdr direct Graph, Outlook, Teams, SharePoint or OneDrive
permissions.

The supported deployment shape is:

\`\`\`text
Herdr host (agentops)
  -> delegated Entra token from the dedicated Azure CLI/MSAL cache
  -> authenticated Power Automate HTTP trigger
  -> Copilot Studio agent
  -> Microsoft 365 Copilot/MCP
  -> Outlook / Teams / SharePoint / OneDrive
\`\`\`

The Power Automate endpoint and all OAuth material are runtime configuration.
They MUST NOT be committed, copied into task payloads, telemetry, durable result
evidence, dashboard snapshots or model prompts.

## Security boundary

The gateway is intentionally a **host integration**, not generic child network
authority. Model-visible workers do not receive the endpoint URL or bearer
token. The module never logs query text, answer text or token bytes.

Required runtime configuration:

- \`HERDR_M365_GATEWAY_URL\` — approved HTTPS Power Automate trigger URL.
- \`HERDR_M365_TENANT_ID\` — Entra tenant used by the delegated identity.
- \`HERDR_M365_AZURE_CONFIG_DIR\` — absolute private Azure CLI cache directory
  owned by the effective host account (normally \`/home/agentops/.azure\`).

Optional bounded configuration:

- \`HERDR_M365_TIMEOUT_SECONDS\` — one HTTP attempt, 5..120 seconds, default 90.
- \`HERDR_M365_POLL_TIMEOUT_SECONDS\` — async polling budget, 10..3600 seconds,
  default 600.
- \`HERDR_M365_POLL_INTERVAL_SECONDS\` — 0.25..30 seconds, default 2.
- \`HERDR_M365_MAX_ATTEMPTS\` — 1..5, default 3.
- \`HERDR_M365_ALLOWED_HOST_SUFFIX\` — HTTPS host suffix allowlist; defaults to
  \`.environment.api.powerplatform.com\`.

The Azure cache directory must be owned by the calling uid and have no
group/other permission bits. Expired or interactive delegated authentication is
reported as \`AUTH_REQUIRED\`; Herdr must stop only M365 work and request a new
device login, not degrade or disable unrelated orchestration.

## Stable internal contract

Supported sources are:

- \`outlook\`
- \`teams\`
- \`sharepoint\`
- \`onedrive\`

A request contains a bounded query and one or more explicit sources. The
gateway fans sources out concurrently and preserves source-level provenance. A
single-source request may carry \`conversation_id\`; one conversation id is not
reused across multiple workload searches.

Conceptual v1 request:

\`\`\`json
{
  "request_id": "optional-id",
  "query": "Find historical Qimarox incidents.",
  "sources": ["outlook", "teams", "sharepoint"],
  "conversation_id": null
}
\`\`\`

Conceptual response:

\`\`\`json
{
  "request_id": "...",
  "status": "completed",
  "answer": "[OUTLOOK] ...",
  "sources": [
    {
      "source": "outlook",
      "status": "ok",
      "duration_ms": 33000,
      "answer": "...",
      "conversation_id": "..."
    }
  ],
  "meta": {
    "started_at": 0,
    "finished_at": 0,
    "partial": false
  }
}
\`\`\`

The aggregate answer is deterministic concatenation, not a second hidden model
call. Higher-level Herdr orchestration may synthesize or verify returned
evidence separately.

## Failure contract

Closed error codes:

- \`AUTH_REQUIRED\`
- \`AUTH_FORBIDDEN\`
- \`RATE_LIMITED\`
- \`UPSTREAM_TRANSIENT\`
- \`UPSTREAM_TIMEOUT\`
- \`INVALID_REQUEST\`
- \`GATEWAY_UNAVAILABLE\`
- \`PARTIAL_FAILURE\`
- \`INTERNAL_ERROR\`

429, 5xx, Power Automate/Copilot \`UnexpectedError\`, \`NoResponse\` and
\`SystemError\` are transient. Authentication and validation failures are not
retried. Multi-source queries keep successful source results when another
source fails (\`meta.partial=true\`).

## Long-running queries

Power Automate may switch to asynchronous response for work exceeding the
synchronous request window. The gateway accepts \`202 Accepted\`, validates the
returned \`Location\` against the HTTPS host allowlist, and polls within a
bounded async budget until a terminal 200 response or \`UPSTREAM_TIMEOUT\`.

This is the preferred mode for historical maintenance research across multiple
Microsoft 365 workloads.

## Health

\`M365Gateway.health()\` validates only local configuration and delegated token
availability. It deliberately does not execute a Microsoft 365 content search,
so health checks do not create model traffic or expose mailbox content.

## Operations

A device-code login is performed only for the dedicated host account:

\`\`\`bash
sudo -u agentops -H az login \
  --use-device-code \
  --tenant "$HERDR_M365_TENANT_ID" \
  --allow-no-subscriptions
\`\`\`

The runtime retrieves short-lived access tokens from that cache for resource
\`https://service.flow.microsoft.com/\`. Passwords and raw access tokens are
never stored in Herdr configuration.

When Conditional Access requires interactive renewal, operators repeat the
device login. Until then, the M365 specialist reports \`AUTH_REQUIRED\` while
the rest of Herdr stays available.

## Activation boundary

This module provides the reviewed host client and fan-out contract. It does
**not** by itself grant a managed child the M365 tool. Live model-visible routing
must go through explicit host-owned tool/broker authority and the normal Herdr
security grant before activation. Do not bypass the sandbox or expose the Azure
cache to managed children.
