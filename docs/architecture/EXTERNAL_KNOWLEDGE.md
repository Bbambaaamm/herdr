# External knowledge provider contract

Herdr remains project- and vendor-agnostic. Domain integrations such as enterprise
mail, collaboration systems, document stores, CMMS or maintenance knowledge live
in separate repositories and connect through a bounded host-side provider
contract.

The canonical Python contract is herdr.external_knowledge.

## Boundary

A provider may implement retrieval, authentication, retries and provider-specific
transport outside the Herdr repository. Herdr knows only:

- a stable provider id;
- a bounded query;
- an explicit list of requested logical sources;
- optional single-provider conversation continuity;
- source-preserving results;
- health and a closed set of error codes.

Registration does not grant model-visible tool authority, child network access or
credential access. A later tool/broker adapter must still pass normal Herdr
security grants before a model can invoke any external knowledge provider.

No provider endpoint, OAuth token, refresh token, mailbox/document content or
project-specific credential belongs in Herdr source, telemetry, TaskGraph payloads
or Machine City snapshots.

## Monotonic scope

A provider response must account for exactly the sources requested by the caller. It cannot
silently broaden or omit the source set. Failed sources remain explicit error rows; successful
and failed sources are distinct and partial success is explicit.

The generic source namespace uses bounded lowercase ids such as mail, chat,
documents, cmms or provider-defined equivalents. Herdr does not encode vendor
product names in core policy.

## Failure model

The closed provider-facing error taxonomy is:

- AUTH_REQUIRED
- AUTH_FORBIDDEN
- RATE_LIMITED
- UPSTREAM_TRANSIENT
- UPSTREAM_TIMEOUT
- INVALID_REQUEST
- PROVIDER_UNAVAILABLE
- PARTIAL_FAILURE
- INTERNAL_ERROR

Provider-specific errors must be mapped into this taxonomy before they cross the
boundary. Raw upstream error bodies are not part of the contract.

## Intended composition

A consumer-specific gateway may fan out to several enterprise sources and retain
source provenance. Herdr may then synthesize or verify results at a higher layer.

Typical flow:

consumer workflow
-> Herdr external knowledge registry
-> approved provider implementation in a separate repository
-> enterprise systems
-> source-preserving response
-> higher-level reasoning / verification

User interfaces and dashboards should target the consumer's domain API, not
enterprise mail/document systems directly. This allows the
provider implementation to change without coupling the UI to authentication or
transport details.

## Activation

This contract is intentionally dormant infrastructure. Shipping it does not
register any live provider, does not create a model tool, does not open network
egress and does not activate credentials. Runtime activation requires a separate
reviewed provider installation plus explicit host-owned authority.


## Guarded host bridge

A model may see an external knowledge provider only through the protected
herdr_external_knowledge read tool. The tool is inert unless all of the following
are true:

- the exact signed SecurityGrant contains the tool and its fixed READ ToolRule;
- the current TaskGraph/parent tool scope contains the tool;
- the physically authenticated bootstrap peer still matches the admitted
  process, interpreter, mount namespace, attempt and fence;
- the current work phase allows the invocation;
- the root-owned external-knowledge policy explicitly allows the consumer,
  provider id and every requested logical source;
- a private host provider daemon is available.

The worker sends its bounded request through the already authenticated Herdr
bootstrap authority socket. The host checks peer/grant/mount/phase before the
provider call and repeats those checks after the provider returns, before any
result crosses back into the sandbox. A phase/fence/peer change therefore
withholds the result rather than delivering stale authority.

The provider daemon socket lives outside the sandbox and is not mounted into the
worker namespace. Provider credentials, OAuth caches and network endpoints stay
host-only. The external provider receives only provider_id plus the bounded
generic KnowledgeRequest; Herdr invocation identity and grant hashes are not
forwarded to it.

The fixed host allowlist is /etc/herdr/external-knowledge.json. It contains only
consumer/provider/source identifiers, never credentials. The repository example
at deploy/herdr/external-knowledge.example.json documents its closed version-1
shape.

AUTH_REQUIRED and provider availability failures are returned as source-level
knowledge errors. They do not stop unrelated Herdr capabilities.

Activation remains separate from this contract. Shipping the bridge does not add
herdr_external_knowledge to an active consumer task profile, install a provider,
create credentials, or start a daemon.
