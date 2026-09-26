# QuantLab → Herdr source lineage

Herdr byl nejprve bootstrapován z ověřeného source capture z 2026-09-26. Před runtime cutoverem ale drift audit prokázal, že tento capture je starší než pozdější Git-backed Agent Platform vývoj.

## Pozorovaný runtime baseline

Živý `/opt/agent-platform/release/DEPLOYED_GIT_SHA` při migraci ukazoval na:

`8f2a5543515eb2d8ce84602e98d6c3d2163e1099`

Tento commit patří do `Bbambaaamm/Autonomous-Quant-Lab`.

## Platform baseline

Kanonický platformní import do Herdru pochází z QuantLab PR #251:
- branch: `q3-production-audit`
- commit: `41179635c8654a60c5d9234acccb6e91b2028b72`
- vztah k nasazenému `8f2a554...`: **6 commitů ahead / 0 behind**

Celý aktuální Agent Platform obsah z této lineage je mapován do kanonického top-level layoutu Herdru.

## Search Router

QuantLab PR #250 je samostatná dvoucommitová lineage. Do Herdru je z něj převzat pouze izolovaný subtree `ops/agent-platform/search-router`, nyní `integrations/search-router/`.

Tím se zachovává cost-aware Perplexity escalation bez sloučení nesouvisející zastaralé historie větve.

## Superseded import

QuantLab PR #239 / commit `0ac4eb85...` byl první Git-authoritative import, ale audit prokázal, že byl 31 commitů za nasazeným `8f2a554...`. Zůstává pouze historickou stopou.

## Pravidlo

Další generický Agent Platform / Herdr vývoj vzniká v `Bbambaaamm/herdr`. QuantLab, Maják a Heating konzumují verzované Herdr releasy a vlastní pouze svoje doménové policy a invarianty.

### Layout adaptation

One test-only path assumption was adapted after import: `tests/agent_platform_dashboard/test_production.py` resolves the standalone Herdr repository root with `parents[2]` instead of the former nested QuantLab `parents[3]`. The production `deploy/agent_platform/production/launch.py` intentionally keeps `parents[3]`; its canonical deployment depth is unchanged.
