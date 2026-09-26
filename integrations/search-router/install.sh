#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
HERMES_ROOT="${HERMES_ROOT:-/home/agentops/.hermes}"

for profile in majak quantlab; do
  dst="$HERMES_ROOT/profiles/$profile/plugins/search-router"
  mkdir -p "$dst"
  if [[ -f "$dst/__init__.py" ]]; then
    cp -a "$dst/__init__.py" "$dst/__init__.py.before-perplexity-cost-router"
  fi
  install -m 0644 "$ROOT/__init__.py" "$dst/__init__.py"
  install -m 0644 "$ROOT/plugin.yaml" "$dst/plugin.yaml"
  python3 -m py_compile "$dst/__init__.py"
  echo "installed search-router for $profile"
done

echo "Search Router installed. Add PERPLEXITY_API_KEY to the profile environment only when paid escalation should be enabled."
