# Hermes RC7: reproducible web/TUI candidates and protected wheel build

**Status: WEB+TUI VERIFIED CANDIDATE / WHEEL BLOCKED / RC7 NO-GO**

Date: 2026-11-16. All evidence refers to the exact isolated Hermes
candidate commit `ef0342358f6421efb4ce919ba859d69940ca13b7`
(based on upstream `ee5ee84a345204a3b1d6ef6ba1ab747e602867b9`).
No root-owned release, active service, project queue or model provider was touched.

## Build results

| Surface | Result | SHA256 of deterministic tar |
| --- | --- | --- |
| Web: `hermes_cli/web_dist/` | PASS, 62 files | `b428a9b4560367d89ef33607ef250c6c8ccebaf0ed2675fc0b2b0a49a9951c4f` |
| TUI: `ui-tui/dist/entry.js` | PASS, 1 file | `bdf7e5be3d65a359e1e04de8ddb285521162b217fd7a24683957571a848df0f8` |
| Hermes Python wheel | **BLOCKED** | None |

Npm version 11.19.0; Node 24.21.0. The exact
`package-lock.json` is SHA256
`193a3a3703499eb7c4b4ce48d3ba1e9dae2be62a48315c1e7ea9545e8be4a067`.
`uv.lock` is SHA256
`5b3798f326209475abca8ef7cbf7c9406f12e687c28c0b540dfe597466f48590`.

Installed npm dependencies with `npm ci --ignore-scripts --no-audit
--no-fund` into an isolated Git-archived scratch copy, rather than the
checked-out Hermes repository. The first *offline* install failed with
`ENOTCACHED semver@7.8.5`; the exact lockfile was then installed from the
npm registry **with all lifecycle scripts disabled**, adding 1,346 packages.
`npm run build --workspace web` and
`npm run build --workspace ui-tui` both passed. Both were run a second time
offline and the sorted, timestamp-normalized tar files matched byte-for-byte.
An independent repetition via the checked-in build script (using populated
offline npm cache) produced the **same two SHA256 hashes**, with no model
requests. This proves repeatability on this staging host and lockfile, not
bit-for-bit reproducibility on all systems.

## Why the wheel was NOT built

Upstream Hermes `setup.py` explicitly raises `RuntimeError: Building
wheels or sdists for hermes-agent is not supported` for `uv build` unless
the build runs under the **approved Nix/uv2nix derivation**.
`nix/python.nix` sets `HERMES_NIX_BUILD=1` inside the official Nix builder.
We verified the guard by invoking the real
`uv build --wheel` in the isolated scratch checkout: exit **2** and the
expected hard error. The initial `uv build --offline` also showed
a missing cached `setuptools==83.0.0` build dependency. The subsequently
online-resolved official build reached the correct setuptools guard.

No `HERMES_NIX_BUILD=1` flag was forged, the guard was not edited, and no
unsupported wheel was generated. **Nix is not installed on this staging
host.** A `docker` CLI being present does not itself establish an
approved isolated Nix builder. Do not treat the verified web/TUI archives as
a complete immutable runtime.

## Reproduce (scratch-only, never active release)

```sh
python3 -I -B scripts/build-hermes-web-tui-candidate.py \
  --hermes-checkout /path/to/verified-hermes-at-ef034235 \
  --scratch /path/to/new-empty-nonprivileged-scratch
```

This defaults to **offline npm**, and refuses a dirty checkout, wrong
Hermes commit, different lockfile, pre-existing scratch directory and
source-path overlap. If an operator explicitly allows contacting the npm
registry for pinned dependencies, append `--allow-npm-registry`. The
script always uses `npm ci --ignore-scripts`, hashes and re-builds
both outputs, and never runs `uv build` or forges a Nix build flag.

The machine-readable status is checked into
`docs/evidence/hermes_web_tui_rc7_candidate.audit.json`. The artifact
tar files and installation/build logs remain in the nonprivileged staging
scratch, **not published as a release or committed as trusted binaries**.

## Next RC7 hard gates

1. Obtain authorized, reviewed Nix/uv2nix build runner; build the Hermes
   wheel with the exact pinned Python source and dependencies inside the
   real Nix derivation. Review Nix fixed-output hashes, build hooks and
   all installed scripts; never spoof the Nix environment variable.
2. Review and hash complete web/TUI/optional plugin/locales/skills content.
   In particular, the Nix wrapper handles `HERMES_WEB_DIST` and
   `HERMES_TUI_DIR`; mere tar generation does not prove these are mounted
   or correctly consumed by the immutable runtime.
3. Perform dependency advisories, independent exact-head source and
   supply-chain review; compare the historic six venv version drifts.
4. Build the immutable, root-owned RC7 candidate with independently approved
   signatures/source inventory, stage1/stage2 and executor matching. Validate
   negative network and subprocess tests without provider calls.
5. Pass the real root -> child -> durable result -> parent ACK/replay E2E,
   then receive explicit privileged operator approval to publish or enable
   any autonomous queue.

**Verdict: NO-GO for RC7 release.**
