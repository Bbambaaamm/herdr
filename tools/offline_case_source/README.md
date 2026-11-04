# Hermes compact offline case source

The source manifest binds 124 case files and 476 composed core files. The 418-row repository `provenance/CANONICAL_SOURCE_MANIFEST.sha256` (`182e58758cbcf56e1f6f57ffd8dcfaf279aeb4157522da4ac8922e83b2f71c92`) is an explicit, pinned overlay at the existing composed core provenance path. It records the frozen repository source after the main189 source rebase; the build's exact `core_files` and overlay map bind the composed runtime bytes. The 448-file canonical base index remains unchanged (`07341cbd524b30d42a4e06d105ae9c174b185fd7988ceb9c7010acd7db3406a5`). `accepted-source-index.json` remains the exact SHA-256 pinned 1,471 member origin index (`c44b4461ef15b3b9e4ef98f98f19d05d6df189f9df0aa8958471a18a8218a49f`). `runtime-input-index.json` separately binds the 1,344 retained origin inputs and the native CLI input. The origin selection includes all 1,249 files beneath `proposed/sdk-source/`, all 93 beneath `proposed/core/`, `proposed/offline.apparmor`, and `proposed/runtime-composition.json`. Each row names its exact relative path, SHA-256, class, and provenance. The entire SDK source tree and layout are retained. The 93 core files remain because their source and composition contracts may be consumed after initial import; the profile and composition record have explicit validation consumers. No historical archive part or raw receipt is retained in the runtime tree.

The builder verifies **every original 1,471 file byte and the complete origin set** before materializing the selected inputs. For a composed core path named in `overlay_targets`, it reads the exact pinned overlay source; other core paths come from the repository tree. It also checks the exact 26,207,464-byte native CLI copy supplied by `reference-context.json.native_cli_input`, including its size, mode and SHA-256, before placing it at `native/herdr` in the compact package. These are SOURCE construction provenance checks. Runtime validation checks the pinned origin *metadata*, the runtime index, the exact retained file set, every retained byte including the package-local native CLI, the case files, the composed core and the complete package file set. It does not claim to verify absent historical bytes at runtime. Historical tar parts, receipts, original failure evidence, and old source ZIPs remain at their original external locations without relocation or deletion. The origin index is neither a signer nor a publication approval.

From the repository root, with the supplied immutable reference available:

```sh
python3 -I -B tools/offline_case_source/verify_runtime_history.py --build-only --repo-root "$PWD" --reference-json ../reference/reference-context.json --output ../verification/runtime
python3 -I -B tools/offline_case_source/verify_runtime_history.py --validate-only --package-root ../verification/runtime
```

The second command requires only the compact package and this repository's verifier code. It neither opens the original reference tree nor performs a publication effect. The root publisher still requires its existing root ownership, exact approved runtime policy, destination vacancy, and source checks before copying the compact source closure. It reads the native CLI only from the package-local pinned path. It never activates policy or issues authority. A prior source snapshot's local data-only materialization measured **65,300,597 bytes**, including **26,207,464 native-input bytes**, against the recorded **84,185,101 expanded bytes**. The artifact byte difference is **18,884,504 bytes**. This is not a disk reclaim estimate; no old artifact was moved or removed.

Portable closed-index logic tests:

```sh
PYTHONPATH=tools/offline_case_source python3 -B -m unittest discover -s tools/offline_case_source/tests/unit -p 'test_runtime_logic_portable.py' -q
```

The full real-reference inert suite requires explicit test-only injection before stdlib discovery:

```sh
PYTHONPATH=tools/offline_case_source:tools/offline_case_source/tests/unit python3 -B -c 'import reference_support,unittest; reference_support.configure("../reference/reference-context.json"); r=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover("tools/offline_case_source/tests/unit", pattern="test_*.py")); raise SystemExit(not r.wasSuccessful())'
```

The test-only `reference_support` fixture is outside runtime code. It uses the supplied context for the immutable origin and a data-only policy fixture for pure render tests; it does not assert host runtime approval. Locally this suite passed 183 tests with no failures, errors or skips. The candidate remains unissued: nonce `03414499dd0d1986968b2393d44275d0`, deadline `1793810588`, one attempt, 1,800 case seconds, one managed CHILD, zero external calls, and the unchanged fresh ROOT floor of 11,140,071,424 bytes. The old #185 capacity/evidence and all original failures remain historical. Actual physical ROOT, CHILD, SDK execution, semantic child/parent dependency, and E2E184 remain `NOT_ESTABLISHED`. This source result does not authorize host publication, issuer changes, policy activation, or a renewed attempt.
