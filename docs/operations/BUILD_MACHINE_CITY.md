# Machine City build contract (#235 handoff)

The deployed bundle is generated from modular sources under
`agent_platform_dashboard/static/`. Do not hand-edit `machine-city.js`.

Pinned build toolchain:

- esbuild `0.28.2`
- three `0.186.1`
- Node.js `>=22`
- npm `11.17.0`

The build script refuses different versions.

## Build

```bash
npm ci
./build-machine-city.sh
```

The lockfile is authoritative. The build does not resolve packages or use a global
Hermes installation.

## Tests

Run the complete browser and geometry suite with the pinned dependencies:

```bash
npm test
```

CI rebuilds the production bundle and rejects any diff from the committed artifact.

## Source graph

`machine-city-source.js` mounts `dashboard-ui.js` and `machine-scene.js`.
`machine-scene.js` consumes `machine-core.js` and `machine-entities.js`.
The reactive core and all live animation state therefore have reviewable source;
the minified bundle is only a generated deploy artifact.
