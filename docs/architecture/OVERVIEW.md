# Herdr architecture

## Control plane

GitHub authorization or another approved ingress enters Herdr. Herdr plans a bounded TaskGraph, validates it, schedules ready nodes, admits work under permission/resource/cost policy, and launches isolated child workers.

Every child is subordinate to its parent policy. A child cannot gain tools, filesystem scope, network scope, model/provider scope, resource budget, or project authority that its parent did not have.

## Execution flow

authorized work
→ planner / deterministic TaskGraph
→ dependency scheduler
→ admission control
→ isolated child agents
→ tools and model router
→ reviewer / validators
→ consumer CI and project authority

Machine City is an observability surface over durable state; it is not merge or execution authority.

## Platform modules

- agent_platform_dashboard/ — current dashboard, production adapters and Machine City source.
- deploy/ — production deployment templates/runbook.
- ops/runtime-observed/ — captured operational runtime for provenance and migration; not the long-term source location.
- configs/consumers/ — platform-side compatibility defaults for known consumers.
- provenance/ — exact source/runtime lineage and external dependency pins.

## Security invariants

- no worker writes directly to consumer main branches;
- no child escalates above parent permissions;
- secrets are not carried in task payloads, telemetry or dashboard data;
- retry, fanout, time and cost are bounded;
- every route/fallback/denial is auditable;
- consumer-specific safety rules remain authoritative after routing.

## Consumer boundary

Herdr is reusable infrastructure. QuantLab, Maják and Heating are consumers. Their domain policies are not generalized into Herdr core.
