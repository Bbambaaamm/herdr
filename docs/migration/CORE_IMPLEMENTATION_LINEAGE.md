# QuantLab core implementation candidates

Při oddělení Herdru byly v QuantLabu tři CI-green implementační PRy. Jejich práce se nezahazuje; migruje se do provider- a consumer-neutral Herdr core.

| Herdr issue | Původní QuantLab PR | Commit | Stav migrace |
|---|---:|---|---|
| #2 TaskGraph | #243 | `40c85d59b02f407ac3b5b70cd7b859f14ae16970` | Migrován do samostatného Herdr PR; `paper_only` envelope byl zobecněn na `policy_profile`. |
| #3 Scheduler/runtime | #244 | `7adf513481ed83a5d1253669732d1420ece7e3e5` | Kandidát zachován; před merge musí používat #2 TaskGraph a přesunout QuantLab-specific deny rules do consumer policy. |
| #5 Reviewer | #245 | `6562da0a09a970cba388cf9dcec999e1418b8cf7` | Kandidát zachován; lze migrovat po namespace/docstring generalizaci. |

## Migrační pravidlo

Do Herdr core se nepřenáší doménová bezpečnostní politika konkrétního consumeru. Platforma vynucuje obecné monotónní oprávnění, bounded execution, audit a policy hooks. QuantLab PAPER-only, Heating actuation gates a Maják source-verification rules zůstávají ve svých consumer policy vrstvách.

Původní PR/commit SHA zůstávají auditovatelnou proveniencí i po uzavření starých QuantLab PRů.
