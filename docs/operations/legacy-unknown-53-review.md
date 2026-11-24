# Legacy UNKNOWN #53 — schválené administrativní vyřazení

**Status: pouze draft PR, žádné schválení ani nasazení.** Tento dokument popisuje starý incident z 2. 10. 2026 a odděluje jej od novějšího PAUSED supervisora.

## Co se zachovává

Původní blokovaná úloha github-herdr-issue-53-20261002T102240Z, její canonical result a worker log jsou kontrolovány pevnými SHA256 v herdr/legacy_unknown_review.py. Historická Hermes session 20261002_102241_25ddcf prokazuje tvorbu PR #81, ale její výsledek ani externí fakturace nejsou formálně vypořádány. Výsledek a účtování zůstávají UNKNOWN. Původní task ani result se nikdy nepřepisují, starý ekonomický pokus se neopakuje.

## Tři oddělené operace

- agent-stack-recovery --inspect-legacy-unknown TASK_ID: pouze čtení, ověření SHA256, vždy HUMAN_REVIEW_REQUIRED.
- agent-stack-recovery --check-legacy-retirement TASK_ID: dry-run pod existujícími zámky; bez platného schválení vrací BLOCKED, se schválením pouze READY_FOR_SEPARATE_OPERATOR_APPLY.
- agent-stack-recovery --retire-legacy-unknown TASK_ID: zápis jednorázového auditního receipt až po samostatném schválení operátorem; nikdy nespouští Hermese.

Podporováno pouze přesné TASK_ID github-herdr-issue-53-20261002T102240Z.

## Brány před produkční aktivací

1. Exact-head CI, GitGuardian a nezávislý security review bez blokujících nálezů; zkontrolovat version parity instalovaných intake, dispatcher, worker, watchdog a recovery.
2. Schválený release deployment, autorizovaný host UID a odpovídající root-owned rozhodovací adresář. Nepřepisovat existující instalaci bez schválení.
3. Read-only inspekce skutečného incidentu s kontrolou původních task/result/log SHA a historických důkazů session/PR #81.
4. Nezávislé účetní/provenance rozhodnutí: zachovat UNKNOWN, žádná domnělá faktura, žádný retry. Potvrdit, že se neprovádí další stejná práce.
5. Ověřit nepřítomnost aktivních workerů a jiné pending/running úlohy Bbambaaamm/herdr#53; incident a novější PAUSED supervisor řešit odděleně.

## Host-owned operator decision

Pouze oprávněný operátor po externím review připraví root-owned regular file (bez symlink/hardlink, bez group/world write) na cestě:

`/etc/herdr/recovery-terminal-unknown/github-herdr-issue-53-20261002T102240Z.legacy-retirement.json`

Uzavřená JSON pole: schema_version=herdr-legacy-unknown-retirement-v1; action=retire_legacy_unknown_intake_blocker; task_id přesně starý task; original_task_sha256=fcc03dcd4cbc49666ddbd5fc5e991501b69d5c9f70a90227ed20b424bff116e3; original_result_sha256=e7455f61ed2e19847c3fab72c1eb2ca1032facb334967b7e8132c1ec0b442490; original_log_sha256=daf3bb82f8d2e4a4b0c411c92e0f91f0427eb849ebf48ee03a16f548da7888fc; review_evidence_sha256=c017dd6c579a4db6b986119e922fe96903e1fc9c2a3f257ed454ac2eb5f0e062; issued_at_epoch a expires_at_epoch celá čísla se životností maximálně 3600 sekund; approval_reference skutečné schválení; writer_scope=reviewed_writers_quiesced_and_locked; billing_disposition=preserved_unknown.

Samotná konverzace s ChatGPT nebo GitHub komentář **není** root-owned schválení. Soubor nevytvářet bez prokazatelného oprávnění host operátora.

## Dry-run a jednorázový apply

1. Zajistit quiescence všech příslušných writerů a ověřit instalovaný schválený release.
2. Spustit --inspect-legacy-unknown, potom po vydání rozhodnutí --check-legacy-retirement. Dry-run nesmí vytvořit receipt.
3. Teprve po samostatném potvrzení operátora jednou spustit --retire-legacy-unknown.
4. Pod existujícími recovery.lock, github-intake-state.lock, dispatcher.lock, worker.lock a worker.loop.lock transakce ověří task/result/log, root decision, absence aktivních úloh, přidá append-only receipt a znovu přečte originály.
5. Kontrola stejného rozhodnutí při opakování pouze vrátí already_retired; nesmí vytvořit druhé spuštění, měnit budget ani přepisovat canonical výsledek.
6. Ověřit záznam receipt, že stará úloha zůstává UNKNOWN a intake smí pouze zvažovat nové oprávněné maintainer-comment-v1 schválení.
7. Nezávislý audit P1: GitHub intake má vlastní active/dedup bránu. Po validovaném retirement receipt musí odfiltrovat pouze tuto jednu přesně doloženou starou blocked úlohu, jinak by i přes ověřený receipt zůstal root trvale zablokovaný. Jakýkoli jiný blocked/pending/running úkol stále drží dedup bariéru. Regresní test pokrývá oba případy.

## Další nezávislé blokace

Administrativní vyřazení samo nespustí nový worker. Pozdější repo-engineering supervisor je PAUSED a PR #247 má vlastní review gate. Tyto blokace je třeba vypořádat samostatně. Nikdy nepřesouvat starý task do pending ani nevytvářet fiktivní fencing token.

## Regresní testy a incident rollback

Syntetické testy pro souběh, duplicitní schválení, expirovaný souhlas, changed bytes, neplatný receipt, rollback po pádu při fsync, aktivní worker, wrong repo a nemožnost repeated retry. K nezávislému review přiložit přesný commit a CI results. Při nejasném receipt zachovat BLOCKED; rollback **není** jeho smazání, ale samostatně autorizovaná reconciliace s důkazy.