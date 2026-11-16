# Herdr RC7 — build, supply-chain and Router v5 audit

Date: 2026-11-16. Git candidate branch: `fix/132-hermes-host-reference-candidate`.
**Verdict: RC7 NO-GO, no root publication and no model execution.**

## Q1 — Approved Nix/uv2nix wheel and immutable runtime

- Exact Hermes SDK candidate source: `ef0342358f6421efb4ce919ba859d69940ca13b7`.
- Pinned source files: 1,821. Source SHA256:
  `d0bd4e3e6023166b3feed4b3fc47ac811d9453476866c8c5e4319bf1038f02fa`.
- Reproduced Python venv site SHA256:
  `d986a36b26e4a57ce5a89fca094843c98b10f8d73c9185f95c09cb1da4172330`.
- Hermes Nix build derivation: `nix/python.nix`, where Nix sets
  `HERMES_NIX_BUILD=1` only during its controlled build. Upstream
  `setup.py` denies wheel generation elsewhere.
- The staging host has **no `nix`, `nix-build` or
  `nix-instantiate` binaries**. It has a `docker` executable but
  the operator user has **permission denied** on the Docker daemon socket.
  No authorized Nix builder is currently connected.
- An earlier actual `uv build --wheel` in scratch ended with the
  upstream expected wheel guard error, exit 2. No false environment variable
  or unreviewed wheel was used.

**Action:** Obtain an explicitly authorized Nix/uv2nix runner with isolated
build environment. Build from reviewed exact Hermes commit, verify Nix
derivation and fixed inputs, then compare actual wheel contents to the
frozen Python inventory. Do not accept a developer-built wheel or allow
unreviewed network fetch scripts. After wheel, integrate the exact web/TUI
builds, pin hashes, evaluate external closure and sign a *new* release
candidate. No RC7 tag, image or wheel built in this audit.

## Q2 — Artifact and dependency verification

- `npm ci --ignore-scripts` installed 1,346 packages from exact
  `package-lock.json` after an initial offline cache miss. Node was
  24.21.0 and npm 11.19.0. Install scripts were disabled.
- Lock SHA256: `193a3a3703499eb7c4b4ce48d3ba1e9dae2be62a48315c1e7ea9545e8be4a067`.
- Web: 62 files, deterministic archive SHA256:
  `b428a9b4560367d89ef33607ef250c6c8ccebaf0ed2675fc0b2b0a49a9951c4f`.
- TUI: `ui-tui/dist/entry.js`, archive SHA256:
  `bdf7e5be3d65a359e1e04de8ddb285521162b217fd7a24683957571a848df0f8`.
- Both builds were repeated with byte-identical normalized tar archives;
  separate offline reproduction from Git archive produced the same hashes.
- The pin/runtime and build control suite previously passed 151 tests.
  Current Router/capability/scheduler/budget/telemetry regression:
  **156 PASS**, all offline.
- **New security finding:** `npm audit --json --omit=dev` against the
  exact lock/workspace on 2026-11-16 returned exit **1** and reported
  **27 vulnerable package entries**: 3 critical, 6 high, 9 moderate,
  9 low. Critical: `simple-git`,
  `@simple-git/argv-parser`, `dompurify`. High:
  `brace-expansion`, `minimatch`, `source-map-js`,
  `undici`, `vite`, `zod`.
  The targeted `npm audit --omit=dev --workspace web` result was **5**
  affected entries (3 high, 1 moderate, 1 low; no critical), including
  `brace-expansion`, `source-map-js` and `vite` at high severity.
  Targeted `--workspace ui-tui` was **3 high**, namely
  `source-map-js`, `undici` and `vite`; no critical entries.
  This result spans dependency trees per workspace; it does **not** prove
  that all are reachable in the final bundled web/TUI. However, before RC7 sign-off
  each advisory must be triaged against runtime reachability,
  exploitability, patched version and exact lockfile. A fixed lockfile
  needs rebuilt/re-hashed artifacts and a new independently reviewed pin.
- Existing GitGuardian check at previous exact HEAD passed; Herdr contract
  CI was still in progress on last inspection, so cannot be called PASS.

**Action:** review and resolve all critical/high advisories for each shipped
workspace and final artifact; produce a signed SBOM, per-asset hashes and a
lockfile/derivation provenance attestation. Run no networked provider test.

## Q3 — Remaining P0 gates to safe autonomous issues

1. **Approved, reproducible Hermes wheel** and complete Nix/uv2nix
   deployment closure, including pinned assets and installed import graph.
2. **Supply-chain security:** 27 npm audit entries require triage,
   critical/high advisory mitigation and new exact-lock rebuild.
3. **Independent security review** at final PR/head of SDK host-reference
   changes, process/plugin isolation, broker FD peer validation and
   model-effect coverage.
4. **Signed root-owned runtime + operator policy:** coherent source/venv/
   web/TUI hashes, new executor identity and reviewed schema-2 policy;
   original RC6 remains untouched.
5. **Native no-provider E2E:** complete real stage1 → stage2 → managed child →
   durable result → parent ACK/replay under kernel network/mount isolation
   with fault injection and no external provider calls.
6. **Activation:** authorized canary, bounded budget/leases and rollback
   evidence before queueing autonomous issues.

## Router v5 and token/cost efficiency: observed implementation

**Implemented and covered by offline tests:**
- The `CapabilityRegistry` filters for feature/tool/modalities,
  required input/output/context token capacity, data policy, runtime
  freshness, rate limit and per-task/grant estimated cost ceilings.
- The `select_route` decision is deterministic and audit-compatible:
  it orders eligible candidates by `-preference_score`, then
  `executor_id`; bounded fallback respects failure categories and
  terminal policy/budget constraints.
- `scheduler_routing` binds routing decisions to the TaskNode,
  policy/registry/requirement hashes, budget allocation and fencing
  identity. Dynamic selection requires explicit `routing_v5.enabled`.
- The existing telemetry format supports actual input/output/cached
  tokens, per-request cost, request latency and retry count.

**NOT demonstrated:**
- Automatic minimum-cost selection among all compatible candidates:
  the current route order is based on provider preference, not
  `estimated_cost_microusd` for successful eligible models.
- Real learned quality/performance routing (success rate, graded task
  outcome, latency and pricing calibration), adaptive complexity
  classification and benchmarked lowest-cost-sufficient-model policy.
- Verified production tokens/$ saved against a defensible baseline.
  The service was inactive during this audit; no provider/model calls
  were made. Hence **real savings are unknown**, not zero.

**Concrete offline counterexample:** with both routes eligible under the
same 50-microusd ceiling, the `a-runtime` fixture priced at 40 microusd
and preferred by policy was selected over the `b-runtime` fixture
priced at 5 microusd. These prices are **test inputs**, not real provider
rates. This demonstrates a functionality gap, not an actual loss.

**Recommended next architecture step:** add an optional, versioned
`cost-aware-sufficient` policy **inside existing Router v5** (not a
second router). Preserve all hard capability/privacy/authorization gates,
then among eligible models minimize *expected validated cost*, subject
to task quality thresholds and latency budgets. Evaluate offline
against exact task fixtures and shadow telemetry; produce token/cost
baseline and confidence bounds, ensure failure/fallback/quality
regressions remain bounded, and only then enable in a reviewed canary.

**Current overall decision: STOP / NO-GO for autonomously executed issues
and any cost-saving claim based on actual provider usage.**

Machine summary: `docs/evidence/rc7_supply_chain_audit_2026-11-16.json`.
