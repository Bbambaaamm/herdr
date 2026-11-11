# Hermes host-reference SDK patch — DRAFT / NOT DEPLOYABLE

Pinned external Hermes upstream commit:
`ee5ee84a345204a3b1d6ef6ba1ab747e602867b9`.

- Isolated external candidate commit:
  `6238133d7c636c353b4d2f18a749ac5c1f49fd21`
- Transfer: `0001-host-reference-sdk-integration.patch.b64.txt`
- Decoded Git patch SHA256:
  `668dff2d289ab2398d1ae960f2b2eef2f4314980cc7a6dac38487cde768fb02a`
- Exact upstream `git apply --check`: PASS
- Focused external SDK tests: **17 PASS**
- Previously verified Herdr guard and host-reference suite: **58 PASS**

## Candidate hardening completed

Herdr stage2 must independently authenticate the reference and keep the
original admitted object identity. The SDK patch uses a nonsecret frozen
reference through deferred `HermesCLI -> AIAgent` initialization and disables
normal key resolution/keepalive in host mode. The ordinary no-reference mode is
unchanged in targeted tests.

This candidate blocks post-construction SDK model switch, credential rotation,
fallback activation and fallback pool rebinding. It checks route/pool/key
identity before the request build and at provider-effect dispatch.

**Critical protection:** Direct SDK non-streaming/streaming provider transports,
retry dispatch, and iteration-limit summary calls reject host-mode requests
before opening the SDK transport. Only independently authenticated Herdr
`WorkInvocationGuard` and host transport can perform model effects. A reference
object alone never authorizes a model call.

**Delegation:** Host-mode agents cannot launch a normal inherited
`delegate_tool._build_child_agent` or background-review fork. A future managed
child must be issued by a separately approved host authority and receive its
own task identity, grant and budget, not an inherited SDK key.

## Not yet security-accepted

- The direct auxiliary APIs in `agent/auxiliary_client.py` such as
  `call_llm()`, their async/streaming variants, and external plugin/provider
  clients can run without a particular AIAgent object. These need explicit
  host-mode process-level denial or a verified centralized effect boundary
  with independent review. Do not enable these in production.
- Concurrency, stream callbacks after cancellation, direct raw transport
  imports and plugin code need further adversarial tests; only selected
  entrypoints are instrumented.
- No full external Hermes regression run, approved fork, immutable Hermes
  candidate release, regenerated source/executor pins or physical zero-provider
  root->child->durable-result E2E.
- No privileged root publication or active RC6 change. #132 remains OPEN,
  #225 DRAFT and MUST NOT be merged as a complete resolution.

To check the patch without applying it:

```sh
base64 -d integrations/hermes-patches/0001-host-reference-sdk-integration.patch.b64.txt |
  git -C /path/to/exact/hermes-checkout apply --check -
```
