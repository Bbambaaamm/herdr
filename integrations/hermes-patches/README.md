# Hermes host-reference SDK patch — DRAFT / NOT DEPLOYABLE

Pinned external upstream Hermes:
`ee5ee84a345204a3b1d6ef6ba1ab747e602867b9`.

- Local isolated Hermes patch commit:
  `ef0342358f6421efb4ce919ba859d69940ca13b7`
- Transfer artifact: `0001-host-reference-sdk-integration.patch.b64.txt`
- Decoded patch SHA256:
  `87a8a42c4c401302f5aae3dbe65824cd9295186beed48412379170d9ea37a70f`
- Applicability to original pinned Hermes: `git apply --check` PASS
- 18 targeted actual Hermes SDK tests PASS
- 229 selected original Hermes auxiliary/relay/stream regressions PASS
- 60 selected Herdr host-reference/guard/stage2 tests PASS

## Host-model effect separation

1. Original stage2 authenticates grant, host reference, profile, route and
   fencing identity. Only after these checks, **before loading Hermes CLI**,
   it arms a process-global **one-way SDK auxiliary denial mode**.
2. In host mode, `call_llm`, `async_call_llm`, shared auxiliary planning,
   synchronous/asynchronous/streaming relay entrypoints, raw auxiliary client
   factories and progress/stream helper entrypoints reject execution before
   provider resolution, client creation or provider HTTP requests.
3. The direct Agent SDK stream/nonstream, retry, summary, fallback and
   credential-rotation paths remain denied in host mode. Subagents and
   background review cannot inherit a host reference; managed children must
   instead obtain separate Herdr host-issued admission and budgets.
4. Herdr's independently authenticated `WorkInvocationGuard` and host
   transport remain the only intended model-effect execution authority.
   The SDK reference itself never grants an effect.

## Explicit limitations — NOT security acceptance

- Python module globals are writable by code with arbitrary execution in
  the same interpreter. This process-wide denial flag is **defense-in-depth**,
  not an isolation boundary against malicious plugins or direct `httpx` /
  `openai` imports. OS-enforced egress/credential restrictions, plugin
  isolation and independently verified host-effect routing remain mandatory.
- No proof that a subprocess spawned from an admitted host process cannot
  import a clean SDK without this one-way flag. A trust boundary across
  processes must be enforced by the native sandbox and host policy.
- Full Hermes suite, plugin-native model clients, concurrent cancellation,
  provider effects, physical root->child->durable-result E2E, immutable source
  inventory, production deployment and independent review are **not accepted**.
- No changes to active RC6, protected /etc/herdr configuration, host services,
  credential stores, provider calls or autonomous queue. Keep PR #225 DRAFT,
  issues #132/#129 OPEN.

To verify patch applicability without modifying the original checkout:

```sh
base64 -d integrations/hermes-patches/0001-host-reference-sdk-integration.patch.b64.txt |
  git -C /path/to/pinned/hermes-checkout apply --check -
```
