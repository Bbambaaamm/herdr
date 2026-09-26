# Machine City — true 3D revision, visual acceptance pending

Status: source implementation and CPU/UI/backend tests complete. Not deployed.

## Change

Replaced bitmap-based head/parallax and fake cutout mouth with a genuine skinned anatomical face, two ocular gimbals, mechanical jaw/pistons, and instanced armor. Added distinct flying Hermes and Codex machines with articulated arms and true 3D industrial city. Head can be inspected front/three-quarter/side. Removed photographic head and baked communications from the page. Renderer, model and read-only UI are now separate modules.

## Verification on 2026-09-25

- `machine-head.test.js`: 8/8 CPU tests passed. Real eye/mouth apertures, skeleton/mandible movement, gaze, finite volume, reduced-motion one-frame settling, render batching.
- `machine-entities.test.js`: 26/26 CPU tests passed. Independent articulated arms, distinct high/low models, reduced/offline lighting, city geometry and draw-call budgets.
- `dashboard-ui.test.js`: 13/13 Node DOM-stub tests passed. Both views, retained agent selection, all 11 explicit demo states, stale/failed data, unknown metrics, escaped HTML, WebGL failure fallback, overflow worker access and honest demo labels.
- Canonical `scripts/run_tests.sh tests/agent_platform_dashboard/test_production.py`: 43 passed.
- esbuild@0.28.1 production IIFE compilation passed; 633132 bytes. `git diff --check` passed.
- Bundle SHA-256: `ca4011f4be7f362c556bfd891ae8fecd8ea19acd94801c174a1ed0953b2d35a3`.
- Live service remained active, existing unauthenticated health response stayed HTTP 401. No release, nginx, systemd, router, task or privilege changes.

## Geometry budgets (not FPS claims)

High head: 9575 component instances, 50 mesh draw calls, ~381364 triangles including instances.
Low head: 4984 component instances, 42 mesh draw calls, ~196532 triangles including instances.
Each drone: 10 draw calls. City: 6 draw calls, 68 high/36 low towers.
High head + four drones + city: ~96 mesh draw calls before postprocessing.

## Unresolved acceptance gate

The permitted verification browser rejected the local file preview URL. No alternate browser or bypass was attempted. Therefore real GPU rendering, frame rate, visual quality and fidelity to the user's supplied reference are NOT verified. The MediaPipe-based sculpt is not the original film production mesh. CPU tests do not substitute for artistic review. Do not deploy on the basis of these tests alone.

Review idle, work and speaking at front/three-quarter/side, compare directly to reference, and adjust anatomy/materials/lighting before calling this finished. Review phone layout, agent picking, context loss and inactive-tab behavior in a real browser. The attached standalone demo is for this gate only.

## Honest data contract

Live snapshot remains read-only. Only states actually provided by Herdr drive live machines. Tool/delegation/speaking streams are unavailable, so their animation remains explicit demo-only. Unknown cost/tokens/fallback totals remain unknown; stale snapshots go offline. Extra workers beyond four visible machine slots remain accessible under project overflow buttons in the full work view. No claim of arbitrary-count 3D orchestration.

## Rebuild

Use the installed Three.js package and pin esbuild to 0.28.1. Addon and core aliases must be separate:

```sh
npx --yes esbuild@0.28.1 agent_platform_dashboard/static/machine-city-source.js --bundle --minify --format=iife --alias:three/addons=/home/agentops/.hermes/hermes-agent/node_modules/three/examples/jsm --alias:three=/home/agentops/.hermes/hermes-agent/node_modules/three/build/three.module.js --outfile=agent_platform_dashboard/static/machine-city.js
```

CPU Three.js tests are bundled using the same aliases and `--platform=node --format=esm`, then run with `node --test`. Existing Python test dependencies are supplied through `PYTHONPATH=/home/agentops/workspaces/majak/.phase1-devdeps` to the project's canonical runner.
