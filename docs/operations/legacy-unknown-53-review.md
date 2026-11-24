# Legacy UNKNOWN: October 2 Herdr #53 — inspection-only first slice

This draft adds a narrowly scoped, read-only inspection of the exact legacy
github_root_orchestration attempt from October 2, 2026. It is **NOT** a
production retirement implementation or a live recovery command.

Pinned original task, result and worker log SHA-256 values prevent accidental
reuse for another historical or modern attempt. The original schema has no
fencing_token, ownership_epoch or result_contract; no such values are fabricated.

The trusted host may provide immutable evidence bytes to
herdr.legacy_unknown_review.inspect(). Session observations about PR #81 do
not become approval or accounting settlement. The inspection always returns
UNKNOWN, HUMAN_REVIEW_REQUIRED and production_transition_authorized=false.

Before a separate live recovery change, the host must independently bind the
original session/provenance, review missing cost settlement, gather a
root-owned explicit operator approval, acquire existing queue/recovery/
dispatcher/worker locks, write an append-only one-shot receipt, and prove
idempotent restart and crash behavior. Keep the canonical result unchanged.
Never retry the old economic attempt or bypass the later PAUSED supervisor.

Tests: python -m pytest -q tests/agent_stack/test_legacy_unknown_review.py
