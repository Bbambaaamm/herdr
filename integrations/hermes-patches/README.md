# Hermes host-reference SDK patch — DRAFT / NOT DEPLOYABLE

This folder contains an **external Hermes SDK patch** for the exact upstream
commit `ee5ee84a345204a3b1d6ef6ba1ab747e602867b9`.

- Isolated Hermes candidate commit: `29d47ae3d81100a62d03056144542bb7c4f7aa91`
- Transfer: `0001-host-reference-sdk-integration.patch.b64.txt`
- Decoded Git patch SHA-256:
  `49e5704c9ba0bee183c7e19f5b4981532ffad8a670d2bac92494883c41a1204a`
- Exact upstream `git apply --check`: PASS
- Targeted Hermes constructor/CLI/effect and mutation-gate tests: 13 PASS
- Herdr host-reference guard/contract suite: 58 PASS (includes 2 deletion/replacement negatives)

## Security design

The host-authenticated stage2 reference is a frozen nonsecret object, not a key,
pool selection or authority by itself. It reaches the deferred HermesCLI and
AIAgent constructors; ordinary provider credentials, fallback and Nous keepalive
are bypassed in this mode. The **original** object is validated before and after
construction.

The patch denies host-mode runtime changes in credential-pool recovery,
credential rotation, manual model switching, fallback activation and fallback
pool rebinding. Every request-assembly attempt validates the effective
provider/model/endpoint/api_mode and forbids raw SDK keys or forged pool identity.
Herdr's independent guard additionally rejects any deletion/replacement of
the original stage2-admitted reference, including when an SDK attribute was
changed to `None`. This must remain independently authoritative.

## Remaining blockers — no acceptance or publication

1. This is **not** upstream-approved and not a root-owned immutable runtime.
2. No full Hermes CLI lifecycle, network-isolated native Hermes zero-provider
   root→child→durable-result E2E or complete provider-effect interception audit.
3. SDK background workers, route-change callbacks, retries after partial output,
   concurrent fallback races and all direct model-call entrypoints still require
   independent adversarial review.
4. A clean upstream fork/review commit, new exact source inventory, updated
   Hermes stage1/stage2/executor pins and independent CI/security review must
   precede a *new* reviewed release candidate.
5. Separate operator approval for root-owned publication/schema2 policy and
   canary; RC6 stays fail-closed and no provider/model/queue calls are allowed.

To verify that the patch applies without making any changes:

```sh
base64 -d integrations/hermes-patches/0001-host-reference-sdk-integration.patch.b64.txt |
  git -C /path/to/exact/hermes-checkout apply --check -
```

**Do not** patch the live Hermes checkout, change the existing historical
root-owned source, waive source pins or merge PR #225 as final #132 acceptance.
