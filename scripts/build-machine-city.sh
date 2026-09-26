#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

[[ "$(node -p "require('./node_modules/esbuild/package.json').version")" == "0.28.2" ]]
[[ "$(node -p "require('./node_modules/three/package.json').version")" == "0.186.1" ]]

npm run build
