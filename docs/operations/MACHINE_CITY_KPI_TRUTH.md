# Machine City KPI truth contract

Status: issue #80
Scope: top KPI strip and central coordinator state.

Machine City is read-only. It must never turn an observed runtime state into an authoritative durable lifecycle transition.

## Source layers

1. Durable task lifecycle: selected Herdr swarm/Agent Stack snapshot.
2. Live execution observation: sanitized `runtime_agents` projection, when `runtime_status=available`.
3. Router usage: bounded Maják + QuantLab router telemetry windows.
4. Terminal history: durable `done` and `failed` records retained for reliability reporting.

If a required source is unavailable, the UI shows `—` or an explicit unavailable state. It must not silently substitute a different semantic source.

## Top KPI definitions

| KPI | Definition | Source | Important limitation |
| --- | --- | --- | --- |
| Active | count of live runtime agents with status `working` | `runtime_agents` (+ live Maják projection) | never inferred from task state; `—` if live runtime unavailable |
| Running | durable tasks in `running` | selected durable task snapshot | does not mean every observed process is represented durably |
| Waiting | durable tasks in `pending` | selected durable task snapshot | reconciliation state is shown separately |
| Blocked / Failed | current `blocked` / terminal `failed` history | durable task snapshot | failed history is not an active blocker |
| Queue | `running + pending + blocked` | durable task snapshot | excludes `done` and `failed` |
| Durable success | `done / (done + failed)` | terminal durable history | lifecycle success only; not product quality or implementation success |
| Retries | sum of durable retry counters; initial attempt is zero | durable `attempt/attempts` | transport reconciliation must not invent retries |
| Avg task | unavailable until task-duration telemetry exists | none today | request/model latency is not substituted |
| Tokens | input + output only for router requests where both fields are known | router telemetry | partial token rows are excluded; known/unknown request coverage is shown |
| Cost known | sum of request cost only where cost is known | router telemetry | if zero requests are priced, value is `—`; unknown requests remain explicit |

## Durable vs live mismatch

A valid transitional state can be:

```text
durable task: pending
attempt_state: delivery_uncertain
runtime agent: working
```

The UI must show both facts. It may say that live work is observed, but it must not rewrite the durable task to `running`.

Likewise, historical `failed` records must remain visible for reliability without causing the central coordinator to claim that a current technical dependency exists.
## Reconciliation fields

Fallback swarm tasks expose:
- `attempt_state`;
- `delivery_reconcile_count`.

The live projection exposes only sanitized:
- `agent_id`;
- `status`;
- optional bound `task_id`.

No prompt, tool argument, credential, terminal text, filesystem path or model conversation is exported to Machine City.

## Screenshot incident, 2026-10-02

The observed screen showed:
- Active 0;
- Running 0;
- Waiting 1;
- Blocked / Failed 0 / 2;
- Queue 3.

At that moment live Herdr observation showed two working agents while the durable root was `pending/delivery_uncertain`. Therefore:
- Active 0 was false for live execution;
- Running 0 was correct durable state;
- Waiting 1 was correct durable state;
- Blocked / Failed 0 / 2 was correct lifecycle/history separation;
- Queue 3 was wrong because two terminal failed records were counted as active queue; correct queue depth was 1.

The old token KPI also mixed independently known input/output fields and double-counted unknown coverage. Issue #80 changes it to fully-known request pairs only.
