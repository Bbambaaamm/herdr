# Independent reviewer gate

The reviewer gate consumes the exact ArtifactRef produced by herdr.workspace. Worker prose is never evidence.

Required evidence is structured, produced by trusted CI/validator identities, and bound to the artifact result_sha. The independent model review is separately bound to the same artifact and the canonical evidence digest, and its actor must differ from the worker actor.

A ReviewRecord stores only hashes/identifiers and safe reason codes. Any task/attempt/base/commit/result/manifest change invalidates the record. BLOCK can be redispatched only within the configured fix-attempt budget; protected consumer paths or exhausted budgets become NEEDS_REPLAN.
