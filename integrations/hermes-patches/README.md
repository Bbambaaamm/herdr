# Hermes host-reference SDK patch — DRAFT, NOT DEPLOYABLE

This directory includes the review-only nonsecret reference contract and an
**actual Hermes SDK source patch** based on the pinned external Hermes commit
`ee5ee84a345204a3b1d6ef6ba1ab747e602867b9`.

- External candidate commit (local isolated git worktree): `c5ccac0353e2b015723d43701817e5522b3f2819`
- Transfer patch: `0001-host-reference-sdk-integration.patch.b64.txt` (base64-encoded Git format-patch; decode before `git am`).
  SHA256 of decoded patch: `357f228a9badcaf2444e62fd862ddf92d9abcbb06cd1c1243c6f5137ba1a9979`
- Module source: `agent/host_reference.py`, included in that patch.
- Original SDK integration touches `run_agent.py`, `agent/agent_init.py`,
  `hermes_cli/cli_agent_setup_mixin.py` and adds 10 constructor/CLI seam tests.
- Do not apply to active Hermes checkout or copy into root-owned runtime.

## Behavioral contract

Herdr stage2 must authenticate the host reference before CLI construction.
The CLI passes that same original object through its deferred agent setup.
Host mode suppresses normal provider credential discovery and Nous keepalive,
rejects explicit raw API keys or runtime/model override, and only exposes a
nonsecret frozen ReferencePool identity view. The AIAgent constructor verifies
the canonical provider/model/endpoint and original reference object both before
and after initialization. Normal construction with no host reference retains
its legacy path.

**These are necessary but insufficient safeguards.** Herdr's independent
WorkInvocationGuard must still verify the authenticated grant, credential
reference, and runtime selection at every provider effect.

## Explicit unresolved gates

- No full Hermes CLI lifecycle, credential fallback, concurrency/race,
  network-egress, or native sandbox acceptance yet.
- No standalone upstream-approved fork/release, signed provenance, or updated
  host runtime/executor source pins.
- No static permission to select a credential, create an agent grant, make a
  model call, deploy, publish root-owned files, or activate schema-2 policy.
- Need adversarial tests across model switching, retries, credential rotation,
  provider fallback, constructor failure, and SDK package import paths.
- Only after independent review may a new immutable Hermes/runtime candidate
  be constructed and zero-provider native root→child→durable-result E2E run.

Candidate tests: 23 contract tests and 10 actual SDK constructor/CLI seam tests pass
on isolated staging checkout. This is **not** a completion claim for #132.

To verify applicability against exact upstream commit without changes:

```sh
base64 -d integrations/hermes-patches/0001-host-reference-sdk-integration.patch.b64.txt | git -C /path/to/pinned/hermes apply --check -
```
