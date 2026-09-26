# Migration from Autonomous-Quant-Lab

## Goal

Make Bbambaaamm/herdr the authoritative home of generic Agent Platform / Herdr code while Autonomous-Quant-Lab becomes a consumer.

## Migration rules

1. Copy and verify before deleting anything from QuantLab.
2. Preserve the 2026-09-26 source/runtime provenance.
3. Move generic Herdr epics/issues to this repository.
4. Keep QuantLab domain and PAPER-only rules in QuantLab.
5. Replace duplicated platform source in QuantLab with a small consumer contract and immutable Herdr pin only after CI-green verification.
6. Runtime cutover is atomic and rollbackable; repository separation must not silently change production.

## Issue migration

The former QuantLab Herdr epic family 229–237 and model-portfolio epic 253 belong here. GitHub issue transfer is used so discussion/history remain intact. docs/migration/ISSUE_MAP.md records the resulting numbers.

## Source migration

The verified development source is imported as working source. The observed runtime snapshot remains under ops/runtime-observed/ only as evidence until each runtime component has an explicit source/build path in Herdr.

## Final QuantLab state

QuantLab should contain only:
- .herdr/consumer.yaml
- HERDR.lock
- its own domain policy and agents
- links to Herdr documentation

The old ops/agent-platform-source capture may be removed only after the Herdr release pin and rollback path are proven.
