# Hermes host-reference contract — review candidate only

This source is a **review-only patch** for an external Hermes agent tree.
It is NOT imported by active Herdr, installed into Hermes, approved as an
upstream commit, or part of the current signed runtime inventory.

The candidate defines a frozen nonsecret HostCredentialReference, a bounded
reference-only pool view, and fail-closed route validation. It never creates
credentials, grants authority, sends model requests, or stores API keys.

## Blocking integration work before a deployable fix

1. Review and integrate the original Hermes credential pool and agent constructor
   with a reference admitted by authenticated Herdr stage2. A model or task must
   never self-approve the binding. No mutable alias or secret may cross this edge.
2. Verify exact class/module identity and guarantee original pool selection,
   authenticated grant, endpoint/model and fence before every provider effect.
3. Review dependencies and generated runtime, build a new Hermes fork commit,
   regenerate its pinned source inventory and update Herdr executor identities.
4. Independently security review negative tests, runtime/sandbox, origin and
   signed host policy; perform zero-provider native E2E on a new immutable release.

Do not patch the old root-owned Hermes tree, remove missing paths from pins,
or treat successful candidate unit tests as authority.
