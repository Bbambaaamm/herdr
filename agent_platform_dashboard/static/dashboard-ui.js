const STATE_META = {
  idle: { label: 'Čeká', copy: 'Klidový režim · žádná hlášená aktivní práce', tone: 'amber' },
  receiving: { label: 'Přijímá zadání', copy: 'Demo přijetí nového zadání', tone: 'amber' },
  working: { label: 'Zpracovává úlohu', copy: 'Demo zpracování úlohy', tone: 'amber' },
  tool: { label: 'Používá nástroj', copy: 'Demo nástrojové operace · živý zdroj tuto událost neposkytuje', tone: 'green' },
  delegating: { label: 'Deleguje', copy: 'Demo předání úkolu vybranému agentovi', tone: 'green' },
  waiting_result: { label: 'Čeká na výsledek', copy: 'Demo čekání · neprobíhá intenzivní práce', tone: 'amber' },
  waiting_user: { label: 'Čeká na zásah', copy: 'Agent je blokovaný a potřebuje kontrolu', tone: 'red' },
  speaking: { label: 'Mluví', copy: 'Stylizovaná animace odpovědi · audio není připojeno', tone: 'green' },
  complete: { label: 'Úloha dokončena', copy: 'Agent ohlásil stav done', tone: 'green' },
  error: { label: 'Problém systému', copy: 'Jeden nebo více datových zdrojů selhalo', tone: 'red' },
  offline: { label: 'Odpojeno', copy: 'Čerstvý živý stav není dostupný', tone: 'muted' },
};
const PROFILES = ['majak', 'quantlab'];
const SCENE_AGENT_IDS = new Set(['majak-hermes', 'majak-codex', 'quantlab-hermes', 'quantlab-codex']);
const ROLES = { hermes: 'Orchestrace, paměť, nástroje a řízení práce', codex: 'Implementace, testování a technická revize' };
const STATUS = { idle: 'Čeká', working: 'Pracuje', blocked: 'Blokováno', done: 'Hotovo', unknown: 'Neznámé', offline: 'Odpojeno' };
const QUEUE_STATUS = { pending: 'Čeká', running: 'Běží', blocked: 'Blokováno', done: 'Hotovo', failed: 'Selhalo' };
const fmt = new Intl.NumberFormat('cs-CZ');
const compact = new Intl.NumberFormat('cs-CZ', { notation: 'compact', maximumFractionDigits: 1 });
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);
const number = value => value == null ? 'Nedostupné' : fmt.format(value);
const money = value => value == null ? 'Neznámé' : value === 0 ? '0 USD' : `${(value / 1e6).toFixed(4)} USD`;
const latency = value => value == null ? 'Nedostupné' : value < 1000 ? `${fmt.format(Math.round(value))} ms` : `${(value / 1000).toFixed(2)} s`;
const age = value => Number.isFinite(value) ? `${Math.max(0, Math.floor(Date.now() / 1000 - value))} s` : 'Nedostupné';
const queueTime = value => Number.isFinite(value) ? new Date(value * 1000).toLocaleString('cs-CZ', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';
const issueLabel = row => Number.isFinite(row?.issue) ? `#${row.issue}` : 'bez issue';
const agentKind = name => name.endsWith('-hermes') ? 'hermes' : 'codex';
const statusLabel = status => STATUS[status] || STATUS.unknown;
const toneColor = tone => ({ green: '#6adf9a', red: '#ff7159', muted: '#716d66', amber: '#e49a34' })[tone];

/** Bind the read-only snapshot UI to a replaceable, fully geometric 3D renderer. */
export function mountDashboard(createScene) {
  const $ = selector => document.querySelector(selector);
  const ui = {
    film: $('#film-view'), work: $('#work-view'), faceState: $('#face-state'), faceTask: $('#face-task'),
    faceSignal: $('#face-signal'), header: $('#header-status'), liveDot: $('#live-dot'),
    snapshotAge: $('#snapshot-age'), agentCount: $('#agent-count'), queueCount: $('#queue-count'), requestCount: $('#request-count'),
    searchCount: $('#search-count'), searchLatency: $('#search-latency'),
    costTotal: $('#cost-total'), attention: $('#attention-action'), coordinatorCurrent: $('#coordinator-current'), coordinatorNext: $('#coordinator-next'), demo: $('#demo-panel'),
    demoStates: $('#demo-states'), detail: $('#agent-detail'), backdrop: $('#drawer-backdrop'),
    canvas: $('#machine-scene'), fallback: $('#webgl-fallback'),
  };
  let liveData = null, demo = false, demoState = 'idle', view = 'work', selectedAgent = null;
  let reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let scene = null, sceneFailed = false, lastFaceState = null, lastDemoKey = '', returnFocus = null;
  let fetchPending = false, loadReason = 'Načítám skutečná data';

  function failScene() {
    sceneFailed = true;
    ui.fallback.hidden = false;
    try { scene?.setActive(false); } catch (_) { /* Text UI is independent of the scene. */ }
    applyView('work');
  }
  try { scene = createScene(ui.canvas, ui.fallback); sceneFailed = !scene; }
  catch (_) { sceneFailed = true; ui.fallback.hidden = false; }
  ui.canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); failScene(); });
  ui.canvas.addEventListener('scene-unavailable', failScene);

  function sceneCall(method, ...args) {
    if (!scene || sceneFailed || typeof scene[method] !== 'function') return;
    try { return scene[method](...args); } catch (_) { failScene(); }
  }
  function source(profile, kind) { return liveData?.sources.find(item => item.profile === profile && item.kind === kind); }
  function queueSource() { return source('quantlab', 'queue'); }
  function queueTasks() { const value = queueSource(); return value?.status === 'available' ? value.rows : []; }
  function activeQueueTasks() { return queueTasks().filter(row => row.status !== 'done'); }
  function currentQueueTask(agent = 'quantlab-hermes') { return queueTasks().find(row => row.agent === agent && ['running', 'blocked', 'failed'].includes(row.status)); }
  function nextQueueTask(agent = 'quantlab-hermes') { return queueTasks().filter(row => row.agent === agent && row.status === 'pending').sort((a, b) => (a.not_before ?? Number.MAX_SAFE_INTEGER) - (b.not_before ?? Number.MAX_SAFE_INTEGER) || a.task_id.localeCompare(b.task_id))[0]; }
  function taskDisplay(row) { return row ? `${issueLabel(row)} · ${row.task_id}` : 'Žádná'; }
  function agents() {
    return PROFILES.flatMap(profile => {
      const value = source(profile, 'herdr');
      return value?.status === 'available' ? value.rows.map(row => ({ ...row, profile })) : [];
    });
  }
  function displayedAgents(profile) {
    const rows = agents().filter(row => row.profile === profile);
    return rows.length ? rows : ['hermes', 'codex'].map(kind => ({ agent: `${profile}-${kind}`, profile, status: 'offline', unavailable: true }));
  }
  function stats(profile) {
    const router = source(profile, 'router'), available = router?.status === 'available';
    const rows = available ? router.rows : [];
    const requests = available ? rows.reduce((total, row) => total + row.requests, 0) : null;
    const completeSum = key => !available || rows.some(row => !Number.isFinite(row[key]))
      ? null : rows.reduce((total, row) => total + row[key], 0);
    const partial = key => {
      if (!available) return { known: null, knownRequests: null, unknownRequests: null, coverage: null };
      let known = 0, knownRequests = 0, unknownRequests = 0;
      for (const row of rows) {
        if (Number.isFinite(row[key])) { known += row[key]; knownRequests += row.requests; }
        else unknownRequests += row.requests;
      }
      return { known, knownRequests, unknownRequests, coverage: requests === 0 ? 100 : Math.round(knownRequests / requests * 100) };
    };
    const input = partial('input_tokens'), output = partial('output_tokens'), cost = partial('cost_microusd');
    return {
      requests, input: completeSum('input_tokens'), output: completeSum('output_tokens'), cost: completeSum('cost_microusd'),
      inputKnown: input.known, outputKnown: output.known, costKnown: cost.known,
      inputKnownRequests: input.knownRequests, outputKnownRequests: output.knownRequests, costKnownRequests: cost.knownRequests,
      inputUnknownRequests: input.unknownRequests, outputUnknownRequests: output.unknownRequests,
      costUnknownRequests: cost.unknownRequests, inputCoverage: input.coverage, outputCoverage: output.coverage, costCoverage: cost.coverage,
      fallbacks: completeSum('fallback_count'),
      models: [...new Set(rows.map(row => row.actual_model).filter(value => typeof value === 'string'))],
      providers: [...new Set(rows.map(row => row.provider).filter(value => typeof value === 'string'))], rows, router,
    };
  }
  function searchStats(profile) {
    const search = source(profile, 'search'), available = search?.status === 'available';
    const rows = available ? search.rows : [];
    const sumKnown = key => !available || rows.some(row => !Number.isFinite(row[key]))
      ? null : rows.reduce((total, row) => total + row[key], 0);
    const searches = available ? sumKnown('searches') : null;
    const duration = available ? sumKnown('duration_ms') : null;
    const maximum = !available ? null : rows.length ? Math.max(...rows.map(row => row.max_duration_ms).filter(Number.isFinite)) : 0;
    const routes = Object.fromEntries(['fast', 'deep', 'browser'].map(mode => [mode,
      available ? rows.filter(row => row.route_mode === mode).reduce((total, row) => total + (Number.isFinite(row.searches) ? row.searches : 0), 0) : null]));
    return {
      searches, successful: available ? sumKnown('successful_searches') : null,
      duration, avgLatency: searches == null || duration == null ? null : searches === 0 ? 0 : duration / searches,
      maxLatency: maximum, fallbacks: available ? sumKnown('fallback_count') : null,
      cost: available ? sumKnown('cost_microusd') : null,
      results: available ? sumKnown('result_count') : null, extracts: available ? sumKnown('extract_count') : null,
      providers: [...new Set(rows.map(row => row.provider).filter(value => typeof value === 'string'))],
      fallbackProviders: [...new Set(rows.map(row => row.fallback_provider).filter(value => typeof value === 'string'))],
      routes, search,
    };
  }
  function codexStats() {
    const value = source('majak', 'codex');
    return { source: value, row: value?.status === 'available' && value.rows.length === 1 ? value.rows[0] : null };
  }
  function routerRows() {
    return PROFILES.flatMap(profile => stats(profile).rows.map(row => ({ ...row, profile })));
  }
  function modelMetrics() {
    const grouped = new Map();
    for (const row of routerRows()) {
      const key = row.actual_model;
      if (!grouped.has(key)) grouped.set(key, { model: key, requests: 0, fallbacks: 0, successes: 0, durationMs: 0, durationRequests: 0 });
      const item = grouped.get(key);
      item.requests += row.requests;
      item.fallbacks += row.fallback_count;
      item.successes += row.successful_requests;
      if (Number.isFinite(row.duration_ms)) { item.durationMs += row.duration_ms; item.durationRequests += row.requests; }
    }
    return [...grouped.values()].sort((a, b) => b.requests - a.requests || a.model.localeCompare(b.model));
  }
  function resetLabel(epoch) {
    if (!Number.isFinite(epoch)) return 'Neznámý';
    return new Date(epoch * 1000).toLocaleString('cs-CZ', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }
  function resetDistance(epoch) {
    if (!Number.isFinite(epoch)) return 'čas resetu není dostupný';
    const seconds = Math.max(0, epoch - Date.now() / 1000);
    const hours = Math.ceil(seconds / 3600);
    return hours < 48 ? `za ${hours} h` : `za ${Math.ceil(hours / 24)} dní`;
  }
  function lineChart(rows, valueKey, { id, suffix = '', maxValue = null } = {}) {
    if (!rows.length) return '<div class="obs-empty">Zatím bez časové řady.</div>';
    const width = 680, height = 178, left = 42, right = 12, top = 12, bottom = 26;
    const values = rows.map(row => Number(row[valueKey])).filter(Number.isFinite);
    if (!values.length) return '<div class="obs-empty">Zatím bez měřených hodnot.</div>';
    const ceiling = Math.max(maxValue ?? 0, ...values, 1);
    const x = index => rows.length === 1 ? (left + width - right) / 2 : left + index / (rows.length - 1) * (width - left - right);
    const y = value => top + (1 - Math.max(0, value) / ceiling) * (height - top - bottom);
    const points = rows.map((row, index) => [x(index), y(Number(row[valueKey]))]);
    const path = points.map(([px, py], index) => `${index ? 'L' : 'M'}${px.toFixed(1)},${py.toFixed(1)}`).join(' ');
    const area = `${path} L${x(rows.length - 1).toFixed(1)},${height - bottom} L${x(0).toFixed(1)},${height - bottom} Z`;
    const first = rows[0].day || queueTime(rows[0].at), midRow = rows[Math.floor((rows.length - 1) / 2)], mid = midRow.day || queueTime(midRow.at);
    const lastRow = rows[rows.length - 1], last = lastRow.day || queueTime(lastRow.at);
    const gradient = escapeHTML(id || 'obs');
    return `<svg class="obs-chart" viewBox="0 0 ${width} ${height}" role="img">
      <defs><linearGradient id="${gradient}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#70ddd0"/><stop offset="1" stop-color="#70ddd0" stop-opacity="0"/></linearGradient></defs>
      ${[0,.25,.5,.75,1].map(f => `<line class="grid" x1="${left}" y1="${(top+f*(height-top-bottom)).toFixed(1)}" x2="${width-right}" y2="${(top+f*(height-top-bottom)).toFixed(1)}"/>`).join('')}
      <path class="area" style="fill:url(#${gradient})" d="${area}"/><path class="line" d="${path}"/>
      ${points.slice(-12).map(([px,py]) => `<circle class="point" cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="2.1"/>`).join('')}
      <text class="axis" x="2" y="${top+4}">${escapeHTML(compact.format(ceiling)+suffix)}</text><text class="axis" x="2" y="${height-bottom+3}">0${escapeHTML(suffix)}</text>
      <text class="axis" x="${left}" y="${height-7}">${escapeHTML(first)}</text><text class="axis" text-anchor="middle" x="${(width/2).toFixed(1)}" y="${height-7}">${escapeHTML(mid)}</text><text class="axis" text-anchor="end" x="${width-right}" y="${height-7}">${escapeHTML(last)}</text>
    </svg>`;
  }
  function bars(rows, value, label, { percent = false, alert = false } = {}) {
    if (!rows.length) return '<div class="obs-empty">Žádná měřená data.</div>';
    const max = Math.max(...rows.map(value), percent ? 100 : 1);
    return `<div class="obs-bars">${rows.map(row => {
      const v = value(row), width = max ? Math.max(1, v / max * 100) : 0;
      return `<div class="obs-bar" data-alert="${alert ? String(alert(row)) : 'false'}"><label title="${escapeHTML(row.model || row.label)}">${escapeHTML(row.model || row.label)}</label><div class="obs-bar-track"><i class="obs-bar-fill" style="--bar:${width.toFixed(1)}%"></i></div><strong>${escapeHTML(label(v, row))}</strong></div>`;
    }).join('')}</div>`;
  }

  function effectiveState() {
    if (demo) return demoState;
    if (!liveData) return 'offline';
    const all = agents(), hermes = all.filter(row => agentKind(row.agent) === 'hermes'), queued = queueTasks();
    if (all.some(row => row.status === 'blocked') || queued.some(row => ['blocked', 'failed'].includes(row.status))) return 'waiting_user';
    if (liveData.sources.some(row => row.kind === 'herdr' && row.status !== 'available')) return all.length ? 'error' : 'offline';
    if (hermes.some(row => row.status === 'working') || queued.some(row => row.status === 'running')) return 'working';
    if (hermes.some(row => row.status === 'idle')) return 'idle';
    if (hermes.length && hermes.every(row => row.status === 'done')) return 'complete';
    return 'offline';
  }
  function demoTarget() { return SCENE_AGENT_IDS.has(selectedAgent) ? selectedAgent : 'majak-codex'; }
  function faceCopy(state) {
    if (demo) return `DEMO · ${STATE_META[state].copy}`;
    const active = agents().filter(row => row.status === 'working').map(row => row.agent), task = currentQueueTask();
    if (state === 'working' && task) return `QuantLab ${issueLabel(task)} · ${task.task_id} · ${QUEUE_STATUS[task.status]}.`;
    if (state === 'working' || (state === 'idle' && active.length)) return `Pracují: ${active.join(', ')}. Přesný úkol zdroj neposkytuje.`;
    if (state === 'waiting_user') {
      const blockedAgents = agents().filter(row => row.status === 'blocked').map(row => row.agent);
      const blockedTasks = queueTasks().filter(row => ['blocked', 'failed'].includes(row.status)).map(row => `${issueLabel(row)} ${row.task_id}`);
      return `Zkontrolujte: ${[...blockedAgents, ...blockedTasks].join(', ') || 'blokovanou úlohu'}.`;
    }
    if (state === 'offline') return loadReason;
    if (state === 'error') return liveData.sources.filter(row => row.status === 'unavailable' && row.reason !== 'not_configured')
      .map(row => `${row.profile}/${row.kind}: ${row.reason}`).join(' · ') || 'Živý stav jednoho projektu není dostupný.';
    return STATE_META[state].copy;
  }
  function renderFace() {
    const state = effectiveState(), meta = STATE_META[state], color = toneColor(meta.tone);
    const currentTask = currentQueueTask(), nextTask = nextQueueTask(currentTask?.agent || 'quantlab-hermes');
    ui.faceState.textContent = meta.label; ui.faceTask.textContent = faceCopy(state);
    ui.coordinatorCurrent.textContent = demo ? `DEMO · ${STATE_META[state].label}` : taskDisplay(currentTask);
    ui.coordinatorNext.textContent = demo ? `DEMO · ${demoTarget()}` : taskDisplay(nextTask);
    ui.coordinatorCurrent.title = ui.coordinatorCurrent.textContent; ui.coordinatorNext.title = ui.coordinatorNext.textContent;
    ui.faceSignal.style.background = color; ui.faceSignal.style.color = color;
    ui.faceSignal.style.boxShadow = reduced ? 'none' : `0 0 13px ${color}`;
    if (state !== lastFaceState) { sceneCall('setState', state); lastFaceState = state; }
    const queue = queueTasks(), working = agents().filter(row => row.status === 'working');
    sceneCall('setActivity', {
      running: queue.filter(row => row.status === 'running').length,
      pending: queue.filter(row => row.status === 'pending').length,
      blocked: queue.filter(row => ['blocked', 'failed'].includes(row.status)).length,
      workingAgents: working.length,
      activeAgent: currentTask?.agent || working[0]?.agent || null,
    });
    const target = demoTarget();
    const key = `${demo}:${demoState}:${target}`;
    if (key !== lastDemoKey) { sceneCall('setDemo', { enabled: demo, state: demoState, target }); lastDemoKey = key; }
    ui.attention.hidden = demo || !['waiting_user', 'error', 'offline'].includes(state);
    ui.attention.textContent = state === 'offline' ? 'Obnovit data' : state === 'waiting_user' ? 'Otevřít blokovaného agenta' : 'Zkontrolovat zdroje';
  }
  function agentButton(row) {
    const kind = agentKind(row.agent), role = demo ? 'Ukázkový stroj · syntetický' : row.unavailable ? 'Stav není dostupný' : kind === 'hermes' ? 'Koordinátor' : 'Vývojový agent';
    const state = demo ? row.agent === demoTarget() ? demoState : 'idle' : row.status;
    const label = demo ? `DEMO · ${STATE_META[state].label}` : statusLabel(state);
    return `<button class="agent-node" data-agent="${escapeHTML(row.agent)}" data-state="${escapeHTML(state)}" aria-label="${escapeHTML(`${row.agent}: ${label}`)}"><span class="agent-copy"><b>${escapeHTML(row.agent)}</b><small>${role}</small></span><span class="state-chip">${escapeHTML(label)}</span></button>`;
  }
  function renderProjects() {
    const sceneRows = [];
    let extraCount = 0;
    for (const profile of PROFILES) {
      const actual = agents().filter(row => row.profile === profile);
      const boundRows = ['hermes', 'codex'].map(kind => actual.find(row => row.agent === `${profile}-${kind}`)
        || { agent: `${profile}-${kind}`, profile, status: 'offline', unavailable: true });
      const extras = actual.filter(row => !SCENE_AGENT_IDS.has(row.agent)); extraCount += extras.length;
      const overflow = extras.length ? `<button type="button" class="scene-overflow" data-overflow-profile="${profile}">+${extras.length} dalších agentů — pracovní přehled</button>` : '';
      $(`#${profile}-agents`).innerHTML = boundRows.map(agentButton).join('') + overflow;
      const rows = actual.length ? actual : boundRows;
      const queued = profile === 'quantlab' ? queueTasks() : [];
      $(`#${profile}-project-state`).textContent = rows.some(row => row.status === 'blocked') || queued.some(row => ['blocked', 'failed'].includes(row.status)) ? 'zásah'
        : rows.some(row => row.status === 'working') || queued.some(row => row.status === 'running') ? 'pracuje' : rows.every(row => row.unavailable) ? 'bez dat' : 'klid';
      sceneRows.push(...boundRows.map(row => ({ ...row, id: row.agent, role: agentKind(row.agent), visible: !$(`#${profile}-agents`).hidden })));
    }
    ui.film.querySelectorAll('[data-agent]').forEach(button => button.addEventListener('click', () => openDetail(button.dataset.agent)));
    ui.film.querySelectorAll('[data-overflow-profile]').forEach(button => button.addEventListener('click', () => applyView('work')));
    $('#data-caveat').textContent = extraCount
      ? `3D scéna zobrazuje čtyři známé stroje. Dalších ${extraCount} agentů je v pracovním přehledu. Neznámé metriky nejsou odhady.`
      : 'Neznámé hodnoty zůstávají neznámé.';
    sceneCall('setAgents', sceneRows);
    // Communication lives in the 3D renderer. No arrows are inferred from idle/working.
    $('#link-layer').replaceChildren();
  }
  function renderTelemetry() {
    if (!liveData) {
      ui.snapshotAge.textContent = 'Nedostupné'; ui.agentCount.textContent = 'Neznámé'; ui.queueCount.textContent = 'Nedostupné';
      ui.requestCount.textContent = 'Nedostupné'; ui.searchCount.textContent = 'Nedostupné'; ui.searchLatency.textContent = 'Nedostupné';
      ui.costTotal.textContent = 'Nedostupné'; $('#work-freshness').textContent = loadReason; return;
    }
    const values = PROFILES.map(stats), total = key => values.every(value => value[key] != null) ? values.reduce((sum, value) => sum + value[key], 0) : null;
    const searches = PROFILES.map(searchStats), searchTotal = key => searches.every(value => value[key] != null) ? searches.reduce((sum, value) => sum + value[key], 0) : null;
    const searchCount = searchTotal('searches'), searchDuration = searchTotal('duration');
    ui.snapshotAge.textContent = age(liveData.generated_at);
    const complete = PROFILES.every(profile => source(profile, 'herdr')?.status === 'available');
    ui.agentCount.textContent = complete ? String(agents().length) : `${agents().length} ověřeno · část nedostupná`;
    ui.queueCount.textContent = queueSource()?.status === 'available' ? String(activeQueueTasks().length) : 'Nedostupné';
    ui.requestCount.textContent = number(total('requests')); ui.searchCount.textContent = number(searchCount);
    ui.searchLatency.textContent = latency(searchCount == null || searchDuration == null ? null : searchCount === 0 ? 0 : searchDuration / searchCount);
    const codex = codexStats().row;
    ui.costTotal.textContent = codex ? `${100 - codex.used_percent} %` : 'Nedostupné';
    ui.costTotal.title = codex ? `Reset ${resetLabel(codex.resets_at)}` : 'Codex usage snapshot není dostupný';
    $('#work-freshness').textContent = `Živý snapshot před ${age(liveData.generated_at)}`;
  }
  function renderObservability() {
    const kpis = $('#observability-kpis'), grid = $('#observability-grid');
    if (!liveData) {
      kpis.innerHTML = '';
      grid.innerHTML = '<article class="obs-panel full"><div class="obs-empty">Živá telemetrie není dostupná.</div></article>';
      return;
    }
    const codex = codexStats().row;
    const profileStats = PROFILES.map(stats);
    const routersAvailable = profileStats.every(value => value.router?.status === 'available');
    const totalRequests = routersAvailable ? profileStats.reduce((sum, value) => sum + value.requests, 0) : null;
    const knownCost = routersAvailable ? profileStats.reduce((sum, value) => sum + value.costKnown, 0) : null;
    const unknownCostRequests = routersAvailable ? profileStats.reduce((sum, value) => sum + value.costUnknownRequests, 0) : null;
    const activeAgents = agents().filter(row => row.status === 'working').length;
    const activeQueue = activeQueueTasks().length;
    const remaining = codex ? 100 - codex.used_percent : null;
    const severity = remaining == null ? 'warn' : remaining <= 5 ? 'critical' : remaining <= 25 ? 'warn' : 'ok';
    const costCopy = knownCost == null ? 'Nedostupné' : unknownCostRequests ? `${money(knownCost)} známé · ${fmt.format(unknownCostRequests)} req bez ceny` : money(knownCost);

    kpis.innerHTML = [
      `<article class="obs-kpi" data-severity="${severity}"><span>Codex allowance · zbývá</span><b>${remaining == null ? '—' : remaining + ' %'}</b><div class="obs-gauge"><i style="--gauge:${codex ? codex.used_percent : 0}%"></i></div><small>${codex ? (codex.ordinary_usage_allowed ? 'Běžné použití povoleno' : 'Limit vyčerpán') : 'Zdroj nedostupný'}</small></article>`,
      `<article class="obs-kpi"><span>Další reset Codex</span><b>${codex ? escapeHTML(resetLabel(codex.resets_at)) : '—'}</b><small>${codex ? escapeHTML(resetDistance(codex.resets_at)) : 'Čas resetu není dostupný'}</small></article>`,
      `<article class="obs-kpi"><span>Codex lifetime tokeny</span><b>${codex?.lifetime_tokens == null ? '—' : escapeHTML(compact.format(codex.lifetime_tokens))}</b><small>Peak/day: ${codex?.peak_daily_tokens == null ? '—' : escapeHTML(compact.format(codex.peak_daily_tokens))}</small></article>`,
      `<article class="obs-kpi"><span>Router požadavky</span><b>${number(totalRequests)}</b><small>${routersAvailable ? `${fmt.format(profileStats.reduce((s,v)=>s+(v.fallbacks||0),0))} fallbacků` : 'část routerů nedostupná'}</small></article>`,
      `<article class="obs-kpi"><span>Variabilní náklady</span><b>${knownCost == null ? '—' : escapeHTML(money(knownCost))}</b><small>${escapeHTML(costCopy)}</small></article>`,
      `<article class="obs-kpi" data-severity="${activeQueue ? 'warn' : 'ok'}"><span>Aktivní práce</span><b>${fmt.format(activeAgents)} agent · ${fmt.format(activeQueue)} fronta</b><small>${activeQueue ? 'Fronta má rozpracované/čekající úlohy' : 'Durable fronta bez aktivních položek'}</small></article>`,
    ].join('');

    const models = modelMetrics();
    const volumeRows = models.slice(0, 8);
    const fallbackRows = models.filter(row => row.requests > 0).map(row => ({ ...row, rate: row.fallbacks / row.requests * 100 }))
      .sort((a,b) => b.rate - a.rate || b.requests - a.requests).slice(0, 8);
    const latencyRows = models.filter(row => row.durationRequests > 0).map(row => ({ ...row, avg: row.durationMs / row.durationRequests }))
      .sort((a,b) => b.avg - a.avg).slice(0, 8);

    const totalRouterRequests = profileStats.every(v => v.requests != null) ? profileStats.reduce((s,v)=>s+v.requests,0) : 0;
    const coverageMetric = (knownKey, unknownKey) => {
      const known = profileStats.reduce((s,v)=>s+(v[knownKey] ?? 0),0);
      const unknown = profileStats.reduce((s,v)=>s+(v[unknownKey] ?? 0),0);
      const denominator = known + unknown;
      return denominator ? Math.round(known / denominator * 100) : (totalRouterRequests === 0 ? 100 : 0);
    };
    const coverage = [
      ['Input tokeny', coverageMetric('inputKnownRequests','inputUnknownRequests')],
      ['Output tokeny', coverageMetric('outputKnownRequests','outputUnknownRequests')],
      ['USD náklady', coverageMetric('costKnownRequests','costUnknownRequests')],
    ];

    const queueRows = queueTasks();
    const queueCounts = Object.fromEntries(Object.keys(QUEUE_STATUS).map(status => [status, queueRows.filter(row => row.status === status).length]));
    const queueTotal = Object.values(queueCounts).reduce((a,b)=>a+b,0);
    const searches = PROFILES.map(searchStats);
    const searchRoutes = ['fast','deep','browser'].map(mode => ({ label: mode.toUpperCase(), value: searches.every(s=>s.routes[mode]!=null) ? searches.reduce((sum,s)=>sum+s.routes[mode],0) : 0 }));
    const daily = (codex?.daily || []).map(row => ({ day: row.day.slice(5), tokens: row.tokens }));
    const history = codex?.limit_history || [];

    grid.innerHTML = [
      `<article class="obs-panel wide"><header><div><h3>Codex tokeny po dnech</h3><span>45 posledních měřených dní</span></div><span>${daily.length ? 'peak '+escapeHTML(compact.format(Math.max(...daily.map(r=>r.tokens)))) : 'bez dat'}</span></header>${lineChart(daily,'tokens',{id:'codexTokensArea'})}<p class="obs-note">Account-wide token activity z Codex app-serveru. Není převáděna na API cenu.</p></article>`,
      `<article class="obs-panel"><header><div><h3>Codex allowance</h3><span>časová řada využití</span></div><span>${codex ? codex.used_percent+' % použito' : 'nedostupné'}</span></header>${lineChart(history,'used_percent',{id:'codexLimitArea',suffix:' %',maxValue:100})}<p class="obs-note">${history.length < 2 ? 'Historii jsme právě začali sbírat; graf se bude plnit automaticky.' : 'Snapshot každých přibližně 5 minut.'}</p></article>`,
      `<article class="obs-panel"><header><div><h3>Model traffic</h3><span>počet požadavků</span></div><span>top 8</span></header>${bars(volumeRows,r=>r.requests,v=>fmt.format(v))}</article>`,
      `<article class="obs-panel"><header><div><h3>Fallback pressure</h3><span>fallbacky / požadavky</span></div><span>vyšší = horší</span></header>${bars(fallbackRows,r=>r.rate,v=>v.toFixed(1)+' %',{percent:true,alert:r=>r.rate>=25})}</article>`,
      `<article class="obs-panel"><header><div><h3>Model latency</h3><span>průměr na request</span></div><span>jen známá latence</span></header>${bars(latencyRows,r=>r.avg,v=>latency(v))}</article>`,
      `<article class="obs-panel"><header><div><h3>Data coverage</h3><span>request-weighted completeness</span></div><span>fail-closed</span></header>${coverage.map(([name,pct])=>`<div class="coverage-row"><span>${escapeHTML(name)}</span><div class="coverage-track"><i style="width:${pct}%"></i></div><strong>${pct} %</strong></div>`).join('')}<p class="obs-note">100 % znamená, že každému requestu odpovídá měřená hodnota. Chybějící hodnoty nejsou dopočítány.</p></article>`,
      `<article class="obs-panel"><header><div><h3>Durable queue</h3><span>stav práce QuantLab</span></div><span>${queueTotal} záznamů</span></header>${queueTotal ? `<div class="queue-strip">${Object.entries(queueCounts).filter(([,count])=>count).map(([status,count])=>`<i class="${status}" style="width:${(count/queueTotal*100).toFixed(1)}%" title="${escapeHTML(QUEUE_STATUS[status])}: ${count}"></i>`).join('')}</div><div class="obs-legend">${Object.entries(queueCounts).map(([status,count])=>`<span>${escapeHTML(QUEUE_STATUS[status])}: ${count}</span>`).join('')}</div>` : '<div class="obs-empty">Fronta je prázdná.</div>'}</article>`,
      `<article class="obs-panel"><header><div><h3>Search route mix</h3><span>Fast / Deep / Browser</span></div><span>aktuální snapshot</span></header>${bars(searchRoutes,r=>r.value,v=>fmt.format(v))}</article>`,
      `<article class="obs-panel"><header><div><h3>Codex účet</h3><span>read-only stav</span></div><span>data před ${codexStats().source ? escapeHTML(age(codexStats().source.observed_at)) : '—'}</span></header><div class="obs-legend"><span>Kredity: ${codex ? escapeHTML(codex.credits_balance ?? 'neznámé') : '—'}</span><span>Reset kredity: ${codex ? fmt.format(codex.reset_credits_available) : '—'}</span><span>Streak: ${codex?.current_streak_days == null ? '—' : fmt.format(codex.current_streak_days)+' dní'}</span><span>Max streak: ${codex?.longest_streak_days == null ? '—' : fmt.format(codex.longest_streak_days)+' dní'}</span></div><p class="obs-note">USD odhad se zobrazí jen pokud jej billing route skutečně poskytne. Subscription allowance se nepřepočítává na API ceník.</p></article>`,
    ].join('');
  }

  function renderQueue() {
    const value = queueSource(), summary = $('#queue-summary'), list = $('#queue-list');
    if (!value || value.status !== 'available') {
      summary.innerHTML = '';
      list.innerHTML = '<p class="queue-empty">Stav durable fronty není v aktuálním snapshotu dostupný.</p>';
      return;
    }
    const rows = queueTasks();
    const counts = Object.fromEntries(Object.keys(QUEUE_STATUS).map(status => [status, rows.filter(row => row.status === status).length]));
    summary.innerHTML = Object.entries(QUEUE_STATUS).map(([status, label]) =>
      `<div class="queue-stat" data-status="${escapeHTML(status)}"><span>${escapeHTML(label)}</span><b>${number(counts[status])}</b></div>`
    ).join('');
    const visible = rows.slice(0, 12);
    list.innerHTML = visible.length ? visible.map(row => {
      const blocker = row.blocker || '—';
      const timing = row.status === 'pending' ? `od ${queueTime(row.not_before)}` : `změna ${queueTime(row.updated_at)}`;
      return `<article class="queue-task" data-status="${escapeHTML(row.status)}"><div class="queue-task-main"><b>${escapeHTML(issueLabel(row))} · <code>${escapeHTML(row.task_id)}</code></b><small>${escapeHTML(row.kind)} · ${escapeHTML(row.agent)}</small></div><span class="queue-status">${escapeHTML(QUEUE_STATUS[row.status] || row.status)}</span><span class="queue-attempt">Pokus ${number(row.attempts)}</span><time>${escapeHTML(timing)}</time><span class="queue-blocker">${escapeHTML(blocker)}</span></article>`;
    }).join('') : '<p class="queue-empty">Fronta je prázdná.</p>';
    if (rows.length > visible.length) list.insertAdjacentHTML('beforeend', `<p class="queue-empty">+${rows.length - visible.length} dalších záznamů v sanitizovaném snapshotu.</p>`);
  }

  function renderSearch() {
    const grid = $('#search-grid');
    grid.innerHTML = PROFILES.map(profile => {
      const value = searchStats(profile);
      if (value.search?.status !== 'available') {
        return `<article class="search-card is-unavailable"><header><div><span>${escapeHTML(profile.toUpperCase())}</span><b>Search telemetry</b></div><span class="search-health">Nedostupné</span></header><p>Zdroj Search Routeru není v aktuálním snapshotu dostupný.</p></article>`;
      }
      const success = value.searches === 0 ? '—' : value.successful == null || value.searches == null
        ? 'Nedostupné' : `${Math.round(value.successful / value.searches * 100)} %`;
      const providers = value.providers.join(', ') || 'Zatím bez provozu';
      const fallbackProviders = value.fallbackProviders.join(', ') || '—';
      return `<article class="search-card"><header><div><span>${escapeHTML(profile.toUpperCase())}</span><b>Search Router</b></div><span class="search-health">${number(value.searches)} hledání</span></header><div class="search-metrics"><div><span>Úspěšnost</span><b>${escapeHTML(success)}</b></div><div><span>Latence avg / max</span><b>${escapeHTML(`${latency(value.avgLatency)} / ${latency(value.maxLatency)}`)}</b></div><div><span>Fallbacky</span><b>${number(value.fallbacks)}</b></div><div><span>Náklady</span><b>${escapeHTML(money(value.cost))}</b></div></div><div class="search-routes"><span>FAST <b>${number(value.routes.fast)}</b></span><span>DEEP <b>${number(value.routes.deep)}</b></span><span>BROWSER <b>${number(value.routes.browser)}</b></span></div><p><span>Provider:</span> ${escapeHTML(providers)}</p><p><span>Fallback provider:</span> ${escapeHTML(fallbackProviders)}</p><p><span>Výsledky / extrakce:</span> ${number(value.results)} / ${number(value.extracts)} · data před ${escapeHTML(age(value.search.data_at))}</p></article>`;
    }).join('');
  }

  function renderWork() {
    $('#project-grid').innerHTML = PROFILES.map(profile => {
      const rows = agents().filter(row => row.profile === profile), value = stats(profile);
      const tokenCoverage = value.inputCoverage == null || value.outputCoverage == null ? null : Math.min(value.inputCoverage, value.outputCoverage);
      const tokenText = value.inputKnown == null ? 'Nedostupné' : `${number(value.inputKnown)} / ${number(value.outputKnown)}${tokenCoverage < 100 ? ` · ${tokenCoverage} % req` : ''}`;
      const costText = value.costKnown == null ? 'Nedostupné' : `${money(value.costKnown)} známé${value.costUnknownRequests ? ` + ${fmt.format(value.costUnknownRequests)} bez ceny` : ''}`;
      return `<article class="work-project"><h2>${profile.toUpperCase()}</h2>${rows.length ? rows.map(row => `<button class="work-agent" data-agent="${escapeHTML(row.agent)}"><b>${escapeHTML(row.agent)}</b><span>${statusLabel(row.status)}</span><small>${ROLES[agentKind(row.agent)]}</small></button>`).join('') : '<p>Živý stav agentů není dostupný.</p>'}<p class="work-models">Modely profilu: ${escapeHTML(value.models.join(', ') || 'Nedostupné')}</p><div class="work-totals"><div><span>Požadavky</span><b>${number(value.requests)}</b></div><div><span>Tokeny vstup/výstup</span><b>${escapeHTML(tokenText)}</b></div><div><span>Známé náklady / fallbacky</span><b>${escapeHTML(costText)} · ${number(value.fallbacks)}</b></div></div></article>`;
    }).join('');
    $('#project-grid').querySelectorAll('[data-agent]').forEach(button => button.addEventListener('click', () => openDetail(button.dataset.agent)));
    renderObservability(); renderQueue(); renderSearch();
    $('#source-grid').innerHTML = (liveData?.sources || []).map(row => {
      const label = row.kind === 'codex' ? 'CODEX / ÚČET' : `${row.profile} / ${row.kind}`;
      return `<article class="source-card" data-status="${escapeHTML(row.status)}"><b>${escapeHTML(label)}</b><span>${escapeHTML(row.status)} · ${escapeHTML(row.reason)}</span><span>${row.status === 'available' ? `${row.rows.length} záznamů` : 'bez dat'}</span></article>`;
    }).join('');
    const problems = (liveData?.sources || []).filter(row => row.status === 'unavailable' && row.reason !== 'not_configured');
    const blocked = agents().filter(row => row.status === 'blocked');
    const queueAlerts = queueTasks().filter(row => ['blocked', 'failed'].includes(row.status));
    const summary = $('#attention-summary');
    summary.hidden = Boolean(liveData) && !problems.length && !blocked.length && !queueAlerts.length;
    summary.textContent = !liveData ? loadReason : `Vyžaduje kontrolu: ${[...blocked.map(row => row.agent), ...queueAlerts.map(row => `${issueLabel(row)} ${row.task_id}`), ...problems.map(row => `${row.profile}/${row.kind} (${row.reason})`)].join(', ')}`;
    if (!summary.hidden) {
      const action = document.createElement('button'); action.type = 'button'; action.className = 'attention-action';
      action.textContent = blocked.length ? 'Otevřít blokovaného agenta' : queueAlerts.length ? 'Otevřít frontu' : 'Obnovit data';
      action.addEventListener('click', () => blocked.length ? openDetail(blocked[0].agent) : queueAlerts.length ? $('#queue-title').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' }) : refresh(true)); summary.append(' ', action);
    }
  }
  function renderDetail() {
    if (!selectedAgent) return;
    const row = agents().find(item => item.agent === selectedAgent);
    const profile = row?.profile || (selectedAgent.startsWith('majak-') ? 'majak' : 'quantlab');
    const value = stats(profile), search = searchStats(profile), herdr = source(profile, 'herdr');
    const task = selectedAgent === 'quantlab-hermes' ? currentQueueTask(selectedAgent) : null;
    const currentTask = selectedAgent === 'quantlab-hermes'
      ? task ? `${issueLabel(task)} · ${task.task_id} · ${QUEUE_STATUS[task.status] || task.status}` : 'Žádná aktivní úloha v durable queue'
      : 'Nedostupné v datovém kontraktu';
    $('#detail-profile').textContent = profile.toUpperCase(); $('#detail-title').textContent = selectedAgent;
    $('#detail-role').textContent = ROLES[agentKind(selectedAgent)];
    $('#detail-status').textContent = `Živý stav: ${row ? statusLabel(row.status) : 'Odpojeno / neznámé'}`;
    const metrics = [
      ['Aktuální úkol', currentTask], ['Modely profilu', value.models.join(', ') || 'Nedostupné v aktuálním snapshotu'],
      ['Provider / fallbacky', `${value.providers.join(', ') || 'Nedostupné'} · ${number(value.fallbacks)}`],
      ['Požadavky / náklady profilu', `${number(value.requests)} · ${value.costKnown == null ? 'Nedostupné' : `${money(value.costKnown)} známé${value.costUnknownRequests ? ` + ${fmt.format(value.costUnknownRequests)} req bez ceny` : ''}`}`],
      ['Search provider / fallbacky', `${search.providers.join(', ') || 'Nedostupné'} · ${number(search.fallbacks)}`],
      ['Search hledání / latence / náklady', `${number(search.searches)} · ${latency(search.avgLatency)} · ${money(search.cost)}`],
    ];
    $('#detail-metrics').innerHTML = metrics.map(([title, content]) => `<div><dt>${escapeHTML(title)}</dt><dd>${escapeHTML(content)}</dd></div>`).join('');
    const events = [];
    if (row) events.push(`Herdr hlásí stav „${row.status}“ · pozorováno před ${age(herdr?.observed_at)}`);
    if (value.router?.status === 'available') events.push(`Router profilu: ${number(value.requests)} požadavků · data před ${age(value.router.data_at)}`);
    if (search.search?.status === 'available') events.push(`Search Router: ${number(search.searches)} hledání · ${latency(search.avgLatency)} průměr · ${number(search.fallbacks)} fallbacků · data před ${age(search.search.data_at)}`);
    if (task) events.push(`Durable queue: ${issueLabel(task)} · ${task.task_id} · pokus ${task.attempts} · metadata před ${age(queueSource()?.observed_at)}`);
    events.push('Zdroj neposkytuje prompt, historii nástrojů, interní myšlenky ani logy úlohy.');
    if (demo) events.unshift('DEMO: pohyb 3D scény je syntetický. Tento detail stále zobrazuje skutečný snapshot.');
    $('#detail-events').innerHTML = events.map(event => `<li>${escapeHTML(event)}</li>`).join('');
  }
  function openDetail(name) {
    if (!PROFILES.flatMap(displayedAgents).some(row => row.agent === name)) return;
    returnFocus = document.activeElement; selectedAgent = name; renderDetail();
    ui.detail.hidden = false; ui.backdrop.hidden = false; document.body.style.overflow = 'hidden';
    $('#detail-close').focus(); sceneCall('focusAgent', name); if (demo) renderProjects(); renderFace();
  }
  function closeDetail() {
    ui.detail.hidden = true; ui.backdrop.hidden = true; document.body.style.overflow = '';
    sceneCall('focusAgent', null);
    if (returnFocus?.isConnected) returnFocus.focus();
    else document.querySelector(`[data-agent="${CSS.escape(selectedAgent || '')}"]`)?.focus();
  }
  function applyView(next) {
    view = next; ui.film.hidden = next !== 'film'; ui.work.hidden = next !== 'work';
    document.querySelectorAll('[data-view]').forEach(button => {
      const active = button.dataset.view === next; button.classList.toggle('is-active', active); button.setAttribute('aria-pressed', String(active));
    });
    sceneCall('setActive', next === 'film' && !document.hidden);
    if (sceneFailed) ui.fallback.hidden = false;
  }
  function updateMotion() {
    document.documentElement.dataset.motion = reduced ? 'reduced' : 'full';
    const button = $('#motion-toggle'); button.setAttribute('aria-pressed', String(reduced)); button.textContent = reduced ? 'Povolit pohyb' : 'Omezit pohyb';
    sceneCall('setReduced', reduced); renderFace();
  }
  function updateHeader() {
    ui.header.textContent = demo ? 'DEMO · scéna syntetická, metriky skutečné' : liveData ? `Živá data · ${age(liveData.generated_at)}` : loadReason;
    const color = demo ? '#e49a34' : liveData ? '#6adf9a' : '#ff7159'; ui.liveDot.style.background = color; ui.liveDot.style.color = color;
  }
  function renderAll() {
    updateHeader(); renderProjects(); renderTelemetry(); renderWork(); renderFace();
    if (!ui.detail.hidden) renderDetail();
  }
  function validateSnapshot(value) {
    if (!value || !Number.isFinite(value.generated_at) || !Array.isArray(value.sources)) throw new Error('invalid');
    if (Date.now() / 1000 - value.generated_at > 90 || value.generated_at > Date.now() / 1000 + 5) throw new Error('stale');
    for (const item of value.sources) {
      if (!item || !PROFILES.includes(item.profile) || typeof item.kind !== 'string' || !Array.isArray(item.rows)) throw new Error('invalid');
      if (item.kind === 'herdr' && item.rows.some(row => typeof row.agent !== 'string' || typeof row.status !== 'string')) throw new Error('invalid');
      if (item.kind === 'queue') {
        if (item.profile !== 'quantlab') throw new Error('invalid');
        if (item.rows.some(row => typeof row.task_id !== 'string' || typeof row.agent !== 'string' || typeof row.kind !== 'string' || !Object.hasOwn(QUEUE_STATUS, row.status))) throw new Error('invalid');
      }
      if (item.kind === 'codex') {
        if (item.profile !== 'majak' || (item.status === 'available' && item.rows.length !== 1)) throw new Error('invalid');
        if (item.rows.some(row => !Number.isFinite(row.used_percent) || row.used_percent < 0 || row.used_percent > 100
          || !Array.isArray(row.daily) || !Array.isArray(row.limit_history))) throw new Error('invalid');
      }
    }
    return value;
  }
  async function refresh(force = false) {
    if (fetchPending || (!force && document.hidden)) return;
    fetchPending = true; const abort = new AbortController(), timer = setTimeout(() => abort.abort(), 10000);
    try {
      const response = await fetch('/agent-platform/api/v1/overview', { cache: 'no-store', headers: { Accept: 'application/json' }, signal: abort.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      liveData = validateSnapshot(await response.json()); loadReason = 'Čerstvý živý stav není dostupný';
      $('#server-fallback-details').removeAttribute('open');
    } catch (error) {
      liveData = null;
      loadReason = error.message === 'stale' ? 'Snapshot je starší než 90 s · obnovte data' : 'Živá data nejsou dostupná · ověřte připojení nebo přihlášení';
    } finally { clearTimeout(timer); fetchPending = false; renderAll(); }
  }

  for (const [state, meta] of Object.entries(STATE_META)) {
    const button = document.createElement('button'); button.type = 'button'; button.dataset.demoState = state; button.textContent = meta.label;
    button.addEventListener('click', () => {
      demoState = state; ui.demoStates.querySelectorAll('button').forEach(item => { const active = item.dataset.demoState === state; item.classList.toggle('is-active', active); item.setAttribute('aria-pressed', String(active)); });
      renderProjects(); renderFace();
    }); ui.demoStates.append(button);
  }
  document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => applyView(button.dataset.view)));
  $('#demo-toggle').addEventListener('click', event => {
    demo = !demo; document.documentElement.dataset.mode = demo ? 'demo' : 'live';
    event.currentTarget.setAttribute('aria-pressed', String(demo)); event.currentTarget.textContent = demo ? 'Ukončit demo' : 'Demo režim'; ui.demo.hidden = !demo;
    if (demo) { demoState = 'idle'; ui.demoStates.querySelectorAll('button').forEach(button => { const active = button.dataset.demoState === 'idle'; button.classList.toggle('is-active', active); button.setAttribute('aria-pressed', String(active)); }); }
    updateHeader(); renderProjects(); renderFace(); if (!ui.detail.hidden) renderDetail(); if (!demo) refresh(true);
  });
  $('#demo-panel > div:first-child > span').textContent = 'Pouze animace jsou syntetické. Metriky a detaily zůstávají skutečné.';
  $('#motion-toggle').addEventListener('click', () => { reduced = !reduced; updateMotion(); });
  matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', event => { reduced = event.matches; updateMotion(); });
  $('#detail-close').addEventListener('click', closeDetail); ui.backdrop.addEventListener('click', closeDetail);
  ui.detail.setAttribute('role', 'dialog'); ui.detail.setAttribute('aria-modal', 'true');
  document.addEventListener('keydown', event => {
    if (ui.detail.hidden) return;
    if (event.key === 'Escape') closeDetail();
    if (event.key === 'Tab') {
      const focusable = [...ui.detail.querySelectorAll('button:not([disabled]),a[href],[tabindex="0"]')];
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });
  ui.attention.addEventListener('click', () => {
    if (!liveData) { refresh(true); return; }
    const blocked = agents().find(row => row.status === 'blocked'); if (blocked) openDetail(blocked.agent); else applyView('work');
  });
  document.querySelectorAll('[data-project-toggle]').forEach(button => button.addEventListener('click', () => {
    const list = button.closest('.project').querySelector('.agent-list'), expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded)); list.hidden = expanded; renderProjects();
  }));
  document.addEventListener('visibilitychange', () => { sceneCall('setActive', !document.hidden && view === 'film'); if (!document.hidden) refresh(true); });
  sceneCall('onSelect', openDetail); updateMotion(); applyView(sceneFailed ? 'work' : 'film'); renderAll(); refresh(true);
  setInterval(refresh, 30000);
  setInterval(() => {
    if (document.hidden) return;
    if (liveData && Date.now() / 1000 - liveData.generated_at > 90) { liveData = null; loadReason = 'Snapshot je starší než 90 s · obnovte data'; renderAll(); }
    else { renderTelemetry(); updateHeader(); if (!ui.detail.hidden) renderDetail(); }
  }, 1000);
  return Object.freeze({ diagnostics: () => ({ view, mode: demo ? 'demo' : 'live', state: effectiveState(), reduced, selectedAgent, sceneAvailable: Boolean(scene) && !sceneFailed, freshSnapshot: Boolean(liveData), agentCount: agents().length, queueActive: activeQueueTasks().length }) });
}
