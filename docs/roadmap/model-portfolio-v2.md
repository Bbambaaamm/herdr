# Herdr Model Portfolio v2 — capability/cost-aware routing roadmap

Status: **PLANNED**  
Scope: Agent Platform / Herdr  
Created: 2026-09-27  
Related epic: #229  
Runtime prerequisite: #231  
Telemetry prerequisite: #234  
Admission/budget prerequisite: #236  
Rollout prerequisite: #237

## 1. Cíl

Rozšířit Herdr z jednoduchého model/fallback výběru na **capability + cost + reliability router**, který pro každý task vybírá model podle typu práce, historické úspěšnosti, ceny, latence, dostupnosti provideru a požadované kvality.

Cílem není mít co nejvíce modelů. Každý přidaný model musí mít jasnou roli a musí prokázat lepší `success/$`, `success/latency` nebo unikátní schopnost proti již nasazenému portfoliu.

## 2. Výchozí stav a vazba na Herdr v1

Současná koncepce Herdru používá FREE-first routing a placené modely až jako fallback/escalation. Herdr v1 (#229) současně zavádí durable TaskGraph, dynamické child agenty, izolaci, reviewer gate, jednotnou telemetry a admission control.

Model portfolio v2 na těchto kontraktech staví a **nesmí je obcházet**.

## 3. Kandidáti k nasazení

### Wave A — levná placená mezivrstva

1. **Qwen Flash-class**
   - bulk worker, extraction, summarization, tool calls, vision, long-context;
   - levná mezivrstva mezi FREE workery a premium modely.

2. **Gemini Flash-class**
   - fast agentic coding, tools, multimodal, repo/context analysis;
   - rychlý fallback pro coding/tool workloads.

3. **OpenAI Luna-class**
   - reliable cheap fallback, structured output, general reasoning;
   - snížit počet eskalací přímo do Sol/Astra-class modelů.

> Konkrétní provider/model ID a aktuální ceny musí být při implementaci ověřeny proti živé API dokumentaci. Architektura nesmí hardcodovat obchodní názvy ani ceny.

### Wave B — nezávislý premium reviewer

4. **Claude Opus-class**
   - architecture review, difficult debugging, independent code review, judge;
   - používat selektivně, ne jako běžného workera;
   - hlavní přínos: nezávislá druhá premium modelová rodina pro kontrolu výsledků.

### Wave C — experimentální levný worker

5. **DeepSeek Flash-class**
   - batch reasoning, code analysis, test generation;
   - pouze shadow/canary, dokud neprokáže lepší efektivitu než Wave A.

### Deferred

- Grok-class — zatím bez dostatečně unikátní role proti Search Routeru/Perplexity a ostatním agentům.
- Mistral/open-weight modely — znovu prioritizovat při požadavku na self-hosting / sovereign EU inference.
- Další premium modely — pouze pokud přidají měřitelnou schopnost, ne jen další fallback.

## 4. Cílový routing model

Herdr nesmí používat jeden lineární fallback chain. Výběr modelu musí být policy rozhodnutí minimálně nad těmito signály:

- `task_type`
- `role`
- `complexity`
- `expected_context_tokens`
- `tool_count`
- `vision_required`
- `latency_target`
- `quality_target`
- `estimated_cost`
- `provider_health`
- `rate_limit_state`
- `historical_success_rate`
- `historical_cost_per_success`
- `historical_latency_p50/p95`
- `fallback_count`
- `retry_count`

Příklad policy:

```text
FREE specialist
    ↓ if unsuitable / failed / low confidence
cheap paid worker (Qwen/Luna-class)
    ↓ if task is agentic coding/tools
Gemini Flash-class
    ↓ if independent premium review or hard architecture/debug
Claude Opus-class / Sol-class
    ↓ exceptional escalation only
Astra-class
```

Routing je task-specific: coding, research, document, vision a reviewer role mohou mít odlišné preferenční množiny.

## 5. Guardrails

- child nesmí rozšířit model/provider oprávnění nad parent policy;
- model selection respektuje resource/admission budget z #236;
- každý task má `max_cost_usd`, `max_attempts`, `max_fallbacks` a timeout;
- žádné nekonečné fallback řetězení;
- provider outage vede k auditovanému fallbacku;
- premium model se nepoužije jen proto, že levnější model vrátil stylisticky neideální výsledek;
- routing nesmí obejít reviewer/CI/merge autoritu;
- PAPER-only invariant QuantLabu zůstává nedotčený;
- secrets nikdy nesmí být v task payloadu, telemetry ani dashboardu.

## 6. Telemetry a rozhodování

Každý model invocation eviduje minimálně:

- provider + model ID;
- task/role;
- parent_agent_id / child_agent_id;
- reason for selection;
- input/output/cached tokens;
- estimated + actual cost;
- latency;
- tool calls;
- success/failure;
- CI/reviewer outcome;
- fallback reason;
- quality/judge outcome, pokud existuje.

Agregované metriky:

- `success_rate`
- `CI_green_rate`
- `review_pass_rate`
- `cost_per_success`
- `tokens_per_success`
- `latency_per_success`
- `fallback_rate`

Preference modelů se mění pouze na základě nasbírané evidence a versionované policy.

## 7. Fáze realizace

### Phase 0 — contracts

- [ ] dokončit #231 model-router adapter bez hardcodování jednoho modelu;
- [ ] dokončit #234 jednotnou model/token/cost/fallback telemetry;
- [ ] dokončit #236 resource/cost admission guardrails;
- [ ] definovat provider-neutral `ModelCapability` + `ModelPolicy` contract;
- [ ] oddělit logical role od konkrétního provider/model ID.

### Phase 1 — Wave A adapters

- [ ] Qwen adapter;
- [ ] Gemini adapter;
- [ ] OpenAI cheap-tier/Luna-class adapter;
- [ ] health/rate-limit/circuit-breaker per provider;
- [ ] secrets pouze přes existující secret mechanismus;
- [ ] dry-run route decision bez reálného placeného volání.

### Phase 2 — shadow evaluation

- [ ] replay reprezentativních historical tasks;
- [ ] shadow decisions vedle stávajícího routeru;
- [ ] porovnat quality/cost/latency;
- [ ] vytvořit baseline pro současný FREE → premium tok;
- [ ] žádné produkční přesměrování bez evidence.

### Phase 3 — Wave A canary

- [ ] 5 % eligible workloads;
- [ ] následně 10 %, 25 %, 50 % pouze pokud guardrails PASS;
- [ ] automatický rollback při zhoršení CI-green, review-pass, latency nebo cost/success;
- [ ] žádné plošné nasazení bez minimálního vzorku.

### Phase 4 — premium independent reviewer

- [ ] přidat Claude Opus-class adapter;
- [ ] povolit pouze role `ARCHITECT`, `REVIEWER`, `HARD_DEBUG`, `JUDGE`;
- [ ] ověřit přínos proti současnému premium reviewerovi;
- [ ] cost ceiling na task a den.

### Phase 5 — DeepSeek experiment

- [ ] shadow eligible batch workloads;
- [ ] canary max 5–10 %;
- [ ] promotion jen pokud porazí Wave A v `cost_per_success` nebo jiné předem určené metrice.

### Phase 6 — adaptive evidence-based policy

- [ ] agregovat outcome per `task_type × role × model`;
- [ ] policy může měnit preference pouze versionovaným deploymentem;
- [ ] žádný online self-modifying routing bez explicitní bounded policy;
- [ ] dashboard zobrazí proč byl model vybrán.

## 8. Acceptance criteria

- [ ] každý model má jasnou roli a dokumentovaný důvod existence;
- [ ] router umí vysvětlit selection reason;
- [ ] všechny fallbacky jsou auditované;
- [ ] task budget nelze překročit fallbackem/retry;
- [ ] provider outage nezastaví celý Herdr, pokud existuje kompatibilní alternativa;
- [ ] model preference je založena na evidence, ne hardcoded žebříčku;
- [ ] lze porovnat modely podle success, CI-green, review-pass, latency, tokens, cost a fallbacků;
- [ ] Wave A prokáže snížení premium escalation rate nebo cost/success proti baseline;
- [ ] premium reviewer prokáže měřitelný přínos, jinak se nepoužívá;
- [ ] rollback vrátí routing na předchozí versioned policy;
- [ ] žádná změna PAPER-only / merge authority / security invariants.

## 9. Co nyní nedělat

- nepřidávat všechny dostupné modely najednou;
- nehardcodovat obchodní modelová jména do TaskGraph schema;
- nedělat router jen podle `complexity`;
- neposílat každé selhání rovnou do nejdražšího modelu;
- neoptimalizovat podle ceny za token bez ceny za úspěšně dokončený task;
- nenasazovat self-learning policy bez versioningu a rollbacku.

## 10. Doporučené pořadí

```text
#231 router adapter
   + #234 telemetry
   + #236 budgets
        ↓
provider-neutral capability contract
        ↓
Wave A adapters
        ↓
shadow evaluation
        ↓
5→10→25→50 % canary
        ↓
premium independent reviewer
        ↓
DeepSeek experimental lane
        ↓
adaptive evidence-based policy
        ↓
#237 E2E staged rollout / soak / rollback
```

## 11. Rozhodovací zásada

**Model se do Herdru nepřidává proto, že je nový nebo silný. Přidává se pouze tehdy, když má unikátní roli nebo prokazatelně zlepší success/$, success/latency nebo kvalitu dané task class.**
