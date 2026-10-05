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
const SWARM_STATUS = { pending: 'pending', ready: 'pending', running: 'running', review: 'running', blocked: 'blocked', done: 'done', failed: 'failed', cancelled: 'done' };
const GITHUB_REPO = 'Bbambaaamm/Autonomous-Quant-Lab';
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
const providerHistory = (rows, field = 'provider') => {
  const ordered = rows
    .filter(row => typeof row[field] === 'string' && Number.isFinite(row.last_used_at))
    .sort((left, right) => right.last_used_at - left.last_used_at || left[field].localeCompare(right[field]));
  const currentProvider = ordered[0]?.[field] || null;
  const historicalProviders = [...new Set(ordered.map(row => row[field]))]
    .filter(provider => provider !== currentProvider);
  return { currentProvider, historicalProviders };
};

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
    swarmKpis: $('#swarm-kpis'),
    kpiActive: $('#kpi-active'), kpiRunning: $('#kpi-running'), kpiWaiting: $('#kpi-waiting'),
    kpiBlocked: $('#kpi-blocked'), kpiQueue: $('#kpi-queue'), kpiSuccess: $('#kpi-success'),
    kpiRetries: $('#kpi-retries'), kpiAvgTask: $('#kpi-avg-task'), kpiTokens: $('#kpi-tokens'),
    kpiCost: $('#kpi-cost'),
    dagStatus: $('#taskgraph-status'), dagNodes: $('#taskgraph-nodes'),
    analyticsGrid: $('#swarm-analytics-grid'),
  };
  let liveData = null, demo = false, demoState = 'idle', view = 'work', selectedAgent = null, selectedTask = null, taskFilter = 'all';
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
  ui.canvas.addEventListener('swarm-task-hover', event => {
    const label = $('#task-hover-label'), detail = event.detail || {}, task = taskById(detail.taskId);
    if (!label || !task || view !== 'film') { if (label) label.hidden = true; return; }
    label.textContent = `${issueLabel(task)} · ${QUEUE_STATUS[task.status] || task.status} · ${task.issue_title || task.task_id}`;
    label.style.left = `${Math.max(12, detail.x + 14)}px`;
    label.style.top = `${Math.max(72, detail.y + 14)}px`;
    label.hidden = false;
  });
  ui.canvas.addEventListener('swarm-task-focus-position', event => {
    const badge = $('#task-selected-label'), detail = event.detail || {}, task = taskById(detail.taskId);
    if (!badge || !task || view !== 'film' || selectedTask !== task.task_id) { if (badge) badge.hidden = true; return; }
    badge.innerHTML = `<b>${escapeHTML(issueLabel(task))}</b><span>${escapeHTML(QUEUE_STATUS[task.status] || task.status)}</span>`;
    badge.style.left = `${Math.max(56, detail.x)}px`;
    badge.style.top = `${Math.max(110, detail.y)}px`;
    badge.hidden = false;
  });

  function sceneCall(method, ...args) {
    if (!scene || sceneFailed || typeof scene[method] !== 'function') return;
    try { return scene[method](...args); } catch (_) { failScene(); }
  }
  function source(profile, kind) { return liveData?.sources.find(item => item.profile === profile && item.kind === kind); }
  function queueSources() { return PROFILES.map(profile => source(profile, 'queue')).filter(Boolean); }
  function queueTasks(profile = null) {
    const values = profile ? [source(profile, 'queue')].filter(Boolean) : queueSources();
    return values.flatMap(value => value?.status === 'available' ? value.rows : []);
  }
  function taskProfile(row) { return row?.repo === 'Bbambaaamm/dotacni-majak' ? 'majak' : 'quantlab'; }
  function durableAgent(agent) { return agent === 'majak-hermes' ? 'dotacni-majak-hermes' : agent; }
  function sceneAgent(agent) { return agent === 'dotacni-majak-hermes' ? 'majak-hermes' : agent; }
  function swarmSource() { return source('quantlab', 'swarm'); }
  function swarmSnapshot() {
    const value = swarmSource();
    return value?.status === 'available' && value.rows.length === 1 ? value.rows[0] : null;
  }
  function swarmTasks() {
    const snapshot = swarmSnapshot(), sourceValue = swarmSource();
    if (!snapshot) return [];
    const issue = /^\d+$/.test(snapshot.issue) ? Number(snapshot.issue) : null;
    const updated = sourceValue?.data_at ?? sourceValue?.observed_at ?? null;
    return snapshot.tasks.map(row => ({
      task_id: row.task_id,
      status: SWARM_STATUS[row.state] || 'blocked',
      raw_state: row.state,
      attempts: row.attempt,
      max_attempts: row.max_attempts,
      not_before: null,
      updated_at: updated,
      agent: row.agent_id || null,
      kind: 'herdr_swarm',
      blocker: row.blocker,
      pr_number: null,
      issue,
      issue_state: snapshot.issue_state || 'unknown',
      issue_title: `Herdr swarm · ${row.role}`,
      repo: snapshot.repo,
      parent_task_id: row.parent_task_id,
      parent_agent_id: row.parent_agent_id,
      dependencies: row.dependencies,
      result_sha: row.result_sha,
      model: row.model,
      fallback_model: row.fallback_model,
      fencing_token: row.fencing_token,
      attempt_state: row.attempt_state,
      delivery_reconcile_count: row.delivery_reconcile_count,
    }));
  }
  function issueClosed(row) {
    return row?.issue_state === 'closed'
      || (row?.issue_open === false && row?.scheduler_state === 'closed');
  }
  function operationalTask(row) {
    return !issueClosed(row) || ['running', 'pending'].includes(row.status);
  }
  function operationalQueueTasks(profile = null) { return queueTasks(profile).filter(operationalTask); }
  function operationalSwarmTasks() { return swarmTasks().filter(operationalTask); }
  function swarmAgents() { return swarmSnapshot()?.agents || []; }
  function swarmRuntimeAgents() {
    const snapshot = swarmSnapshot();
    return snapshot?.runtime_status === 'available' ? snapshot.runtime_agents : null;
  }
  function runtimeLinkedTask() {
    const runtime = swarmRuntimeAgents();
    if (!runtime) return null;
    const activeTaskIds = runtime
      .filter(row => ['working', 'blocked'].includes(row.status) && row.task_id)
      .map(row => row.task_id);
    return activeTaskIds.map(taskById).find(Boolean) || null;
  }
  function coordinatorTasks() {
    return swarmSnapshot()
      ? [...operationalSwarmTasks(), ...operationalQueueTasks('majak')]
      : operationalQueueTasks();
  }
  function coordinatorTask() {
    return runtimeLinkedTask()
      || coordinatorTasks().filter(row => row.status === 'running')
        .sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0) || a.task_id.localeCompare(b.task_id))[0]
      || coordinatorTasks().find(row => row.status === 'blocked')
      || null;
  }
  function blockedAgents() {
    const swarm = swarmSnapshot();
    return [
      ...(swarmRuntimeAgents() || []).filter(row => row.status === 'blocked')
        .map(row => ({ ...row, agent: row.agent_id, profile: 'quantlab', runtime: true })),
      ...agents().filter(row => row.status === 'blocked' && (!swarm || row.profile === 'majak')),
    ];
  }
  function openBlockedAgent(row) {
    if (row.task_id && taskById(row.task_id)) openTaskDetail(row.task_id);
    else openDetail(row.agent);
  }
  function swarmEdges() { return swarmSnapshot()?.edges || []; }
  function taskRows() { return swarmSnapshot() ? [...swarmTasks(), ...queueTasks('majak')] : queueTasks(); }
  function admissionSource() { return source('quantlab', 'admission'); }
  function admissionRows() { const value = admissionSource(); return value?.status === 'available' ? value.rows : []; }
  function admissionDenials() { return admissionRows().filter(row => row.event === 'deny'); }
  function releaseInfo() {
    const value = source('quantlab', 'release');
    return value?.status === 'available' && value.rows.length === 1 ? value.rows[0] : null;
  }
  function activeQueueTasks() { return operationalQueueTasks().filter(row => ['pending', 'running', 'blocked'].includes(row.status)); }
  function taskById(taskId) { return taskRows().find(row => row.task_id === taskId) || queueTasks().find(row => row.task_id === taskId) || null; }
  const USER_ACTION_BLOCKERS = new Set(['user_action_required', 'agent_interactive_input_required', 'github_write_auth_required']);
  function userBlockedTasks(profile = null) { return operationalQueueTasks(profile).filter(row => row.status === 'blocked' && USER_ACTION_BLOCKERS.has(row.blocker)); }
  function technicalBlockedTasks(profile = null) { return operationalQueueTasks(profile).filter(row => row.status === 'blocked' && !USER_ACTION_BLOCKERS.has(row.blocker)); }
  function currentQueueTask(agent = null) {
    const priority = { running: 0, blocked: 1 };
    return operationalQueueTasks()
      .filter(row => (!agent || row.agent === agent) && Object.hasOwn(priority, row.status))
      .sort((a, b) => priority[a.status] - priority[b.status]
        || (b.updated_at || 0) - (a.updated_at || 0)
        || a.task_id.localeCompare(b.task_id))[0];
  }
  function nextQueueTask(agent = null) {
    return operationalQueueTasks().filter(row => (!agent || row.agent === agent) && row.status === 'pending')
      .sort((a, b) => (a.not_before ?? Number.MAX_SAFE_INTEGER) - (b.not_before ?? Number.MAX_SAFE_INTEGER) || a.task_id.localeCompare(b.task_id))[0];
  }
  function taskDisplay(row) { return row ? `${issueLabel(row)} · ${row.task_id}` : 'Žádná'; }
  function attemptLabel(row) { return row ? `${number(row.attempts)} / ${number(row.max_attempts)}` : 'Nedostupné'; }
  function issueUrl(row) { return Number.isFinite(row?.issue) ? `https://github.com/${row.repo || GITHUB_REPO}/issues/${row.issue}` : null; }
  function prUrl(row) { return Number.isFinite(row?.pr_number) ? `https://github.com/${row.repo || GITHUB_REPO}/pull/${row.pr_number}` : null; }
  function detailLink(url, label) { return url ? `<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(label)}</a>` : ''; }
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
    const tokenKnownRows = available ? rows.filter(row => Number.isFinite(row.input_tokens) && Number.isFinite(row.output_tokens)) : [];
    const tokenKnownRequests = available ? tokenKnownRows.reduce((sum, row) => sum + row.requests, 0) : null;
    const tokenKnownTotal = available ? tokenKnownRows.reduce((sum, row) => sum + row.input_tokens + row.output_tokens, 0) : null;
    const tokenUnknownRequests = available ? rows.filter(row => !Number.isFinite(row.input_tokens) || !Number.isFinite(row.output_tokens)).reduce((sum, row) => sum + row.requests, 0) : null;
    const providerState = providerHistory(rows);
    return {
      requests, input: completeSum('input_tokens'), output: completeSum('output_tokens'), cost: completeSum('cost_microusd'),
      inputKnown: input.known, outputKnown: output.known, costKnown: cost.known,
      inputKnownRequests: input.knownRequests, outputKnownRequests: output.knownRequests,
      inputUnknownRequests: input.unknownRequests, outputUnknownRequests: output.unknownRequests,
      tokenKnownRequests, tokenKnownTotal, tokenUnknownRequests,
      costKnownRequests: cost.knownRequests, costUnknownRequests: cost.unknownRequests,
      inputCoverage: input.coverage, outputCoverage: output.coverage, costCoverage: cost.coverage,
      fallbacks: completeSum('fallback_count'),
      models: [...new Set(rows.map(row => row.actual_model).filter(value => typeof value === 'string'))],
      providers: [...new Set(rows.map(row => row.provider).filter(value => typeof value === 'string'))],
      ...providerState, rows, router,
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
    const providerState = providerHistory(rows);
    return {
      searches, successful: available ? sumKnown('successful_searches') : null,
      duration, avgLatency: searches == null || duration == null ? null : searches === 0 ? 0 : duration / searches,
      maxLatency: maximum, fallbacks: available ? sumKnown('fallback_count') : null,
      cost: available ? sumKnown('cost_microusd') : null,
      results: available ? sumKnown('result_count') : null, extracts: available ? sumKnown('extract_count') : null,
      providers: [...new Set(rows.map(row => row.provider).filter(value => typeof value === 'string'))],
      fallbackProviders: [...new Set(rows.map(row => row.fallback_provider).filter(value => typeof value === 'string'))],
      ...providerState, routes, search,
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
      if (!grouped.has(key)) grouped.set(key, {
        model: key, requests: 0, fallbacks: 0, successes: 0, durationMs: 0, durationRequests: 0,
        inputTokens: 0, outputTokens: 0, tokenKnownRequests: 0, tokenUnknownRequests: 0,
      });
      const item = grouped.get(key);
      item.requests += row.requests;
      item.fallbacks += row.fallback_count;
      item.successes += row.successful_requests;
      if (Number.isFinite(row.duration_ms)) { item.durationMs += row.duration_ms; item.durationRequests += row.requests; }
      if (Number.isFinite(row.input_tokens) && Number.isFinite(row.output_tokens)) {
        item.inputTokens += row.input_tokens; item.outputTokens += row.output_tokens; item.tokenKnownRequests += row.requests;
      } else item.tokenUnknownRequests += row.requests;
    }
    return [...grouped.values()].sort((a, b) => b.requests - a.requests || a.model.localeCompare(b.model));
  }
  function swarmMetrics() {
    const queue = swarmSnapshot()
      ? [...operationalSwarmTasks(), ...operationalQueueTasks('majak')]
      : operationalQueueTasks();
    const history = swarmSnapshot()
      ? [...swarmTasks(), ...queueTasks('majak')] : queueTasks();
    const count = status => queue.filter(row => row.status === status).length;
    const running = count('running'), waiting = count('pending'), blockedOnly = count('blocked');
    const failed = history.filter(row => row.status === 'failed').length;
    const done = history.filter(row => row.status === 'done').length;
    const blocked = blockedOnly + failed;
    const runtimeAgents = swarmRuntimeAgents();
    const majakWorking = agents().filter(row => row.profile === 'majak' && row.status === 'working').length;
    const projected = PROFILES.filter(profile => liveData.sources.some(row => row.profile === profile));
    const majakAvailable = !projected.includes('majak') || source('majak', 'herdr')?.status === 'available';
    const activeAgents = swarmSnapshot()
      ? runtimeAgents === null || !majakAvailable ? null : runtimeAgents.filter(row => row.status === 'working').length + majakWorking
      : projected.every(profile => source(profile, 'herdr')?.status === 'available')
        ? agents().filter(row => row.status === 'working').length : null;
    const retries = history.reduce((sum, row) => sum + (Number.isSafeInteger(row.attempts) ? Math.max(0, row.attempts) : 0), 0);
    const terminal = done + failed;
    const success = terminal ? Math.round(done / terminal * 100) : null;
    const profiles = PROFILES.map(stats);
    const routersAvailable = profiles.every(value => value.router?.status === 'available');
    const tokenTotal = routersAvailable ? profiles.reduce((sum, value) => sum + (value.tokenKnownTotal || 0), 0) : null;
    const tokenKnownRequests = routersAvailable ? profiles.reduce((sum, value) => sum + (value.tokenKnownRequests || 0), 0) : null;
    const tokenUnknownRequests = routersAvailable ? profiles.reduce((sum, value) => sum + (value.tokenUnknownRequests || 0), 0) : null;
    const cost = routersAvailable ? profiles.reduce((sum, value) => sum + (value.costKnown || 0), 0) : null;
    const costKnownRequests = routersAvailable ? profiles.reduce((sum, value) => sum + (value.costKnownRequests || 0), 0) : null;
    const costUnknownRequests = routersAvailable ? profiles.reduce((sum, value) => sum + (value.costUnknownRequests || 0), 0) : null;
    const models = modelMetrics();
    const durationMs = models.reduce((sum, row) => sum + row.durationMs, 0);
    const durationRequests = models.reduce((sum, row) => sum + row.durationRequests, 0);
    const requestLatency = durationRequests ? durationMs / durationRequests : null;
    const fallbacks = profiles.every(value => value.fallbacks != null) ? profiles.reduce((sum, value) => sum + value.fallbacks, 0) : null;
    return { queue, running, waiting, blocked, blockedOnly, done, failed, activeAgents, retries, success,
      activeQueue: running + waiting + blockedOnly, tokenTotal, tokenKnownRequests, tokenUnknownRequests,
      cost, costKnownRequests, costUnknownRequests, requestLatency, fallbacks, models };
  }

  function renderSwarmKpis() {
    const root = $('#swarm-kpis');
    if (!root) return;
    if (!liveData) { root.innerHTML = '<div class="swarm-kpi"><span>Swarm</span><b>—</b><small>telemetrie nedostupná</small></div>'; return; }
    const m = swarmMetrics();
    const tokenValue = m.tokenTotal == null || !m.tokenKnownRequests ? '—' : compact.format(m.tokenTotal);
    const costValue = m.cost == null || !m.costKnownRequests ? '—' : money(m.cost);
    const cells = [
      ['Active', m.activeAgents == null ? '—' : m.activeAgents, m.activeAgents == null ? 'live runtime nedostupný' : 'živí pracující agenti', m.activeAgents ? 'running' : ''],
      ['Running', m.running, 'durable běžící tasky', m.running ? 'running' : ''],
      ['Waiting', m.waiting, 'durable pending', m.waiting ? 'waiting' : ''],
      ['Blocked / Failed', `${m.blockedOnly} / ${m.failed}`, 'blocked nyní / failed historie', m.blocked ? 'blocked' : ''],
      ['Queue', m.activeQueue, 'neterminální durable tasky', ''],
      ['Durable success', m.success == null ? '—' : `${m.success} %`, `${m.done} done · ${m.failed} failed v historii`, ''],
      ['Retries', m.retries, 'durable retry counter', m.retries ? 'waiting' : ''],
      ['Avg task', '—', 'task duration se neměří', ''],
      ['Tokens', tokenValue, m.tokenKnownRequests == null ? 'router telemetry nedostupná' : `${m.tokenKnownRequests} req known · ${m.tokenUnknownRequests || 0} unknown`, ''],
      ['Cost known', costValue, m.costKnownRequests == null ? 'router telemetry nedostupná' : `${m.costKnownRequests} req oceněno · ${m.costUnknownRequests || 0} unknown`, ''],
    ];
    root.innerHTML = cells.map(([label, value, note, state]) => `<article class="swarm-kpi" data-state="${state}"><span>${escapeHTML(label)}</span><b>${escapeHTML(String(value))}</b><small>${escapeHTML(note)}</small></article>`).join('');
  }

  function taskSortKey(row) {
    const order = { running: 0, blocked: 1, failed: 2, pending: 3, done: 4 };
    return [order[row.status] ?? 9, -(row.updated_at || 0), row.task_id];
  }
  function sortedTaskNodes() {
    return [...taskRows()].sort((a, b) => {
      const aa = taskSortKey(a), bb = taskSortKey(b);
      return aa[0] - bb[0] || aa[1] - bb[1] || String(aa[2]).localeCompare(String(bb[2]));
    });
  }
  function taskMatchesFilter(row) {
    if (taskFilter === 'all') return true;
    if (taskFilter === 'blocked') return row.status === 'blocked' || row.status === 'failed';
    return row.status === taskFilter;
  }

  function taskNodeHTML(row) {
    const durable = row.raw_state || QUEUE_STATUS[row.status] || row.status;
    const state = row.attempt_state && row.attempt_state !== durable ? `${durable} · ${row.attempt_state}` : durable;
    return `<button type="button" class="taskgraph-node" role="option" aria-selected="${String(selectedTask === row.task_id)}" data-task-id="${escapeHTML(row.task_id)}" data-status="${escapeHTML(row.status)}"><b>${escapeHTML(issueLabel(row))} · ${escapeHTML(row.task_id)}</b><span>${escapeHTML(state)}</span><small>${escapeHTML(row.issue_title || row.kind)} · pokus ${escapeHTML(attemptLabel(row))}</small></button>`;
  }
  function taskLaneHTML(label, rows, limit) {
    if (!rows.length) return '';
    const visible = rows.slice(0, limit);
    const overflow = rows.length - visible.length;
    return `<div class="taskgraph-lane" role="group" aria-label="${escapeHTML(label)}"><span class="taskgraph-lane-label">${escapeHTML(label)}</span><div class="taskgraph-lane-track">${visible.map(taskNodeHTML).join('')}${overflow ? `<div class="taskgraph-node taskgraph-cluster" data-status="pending"><b>+${overflow} uzlů</b><span>LOD cluster</span><small>další sanitizované tasky</small></div>` : ''}</div></div>`;
  }
  function taskEdgeHTML(edges, taskIds) {
    const visible = edges.filter(edge => taskIds.has(edge.from_task) && taskIds.has(edge.to_task));
    if (!visible.length) return '';
    const shown = visible.slice(0, 16), overflow = visible.length - shown.length;
    return `<div class="taskgraph-edge-strip" aria-label="Autoritativní DAG hrany">${shown.map(edge => `<span class="taskgraph-edge" data-edge-kind="${escapeHTML(edge.kind)}"><b>${escapeHTML(edge.from_task)}</b><i>→</i><b>${escapeHTML(edge.to_task)}</b><small>${escapeHTML(edge.kind)}</small></span>`).join('')}${overflow ? `<span class="taskgraph-edge taskgraph-edge-overflow">+${overflow} hran</span>` : ''}</div>`;
  }

  function renderTaskGraph() {
    const root = $('#taskgraph-nodes'), status = $('#taskgraph-status');
    if (!root || !status) return;
    const swarmValue = swarmSource(), queueValues = queueSources().filter(value => value.status === 'available');
    const sourceValue = swarmSnapshot()
      ? swarmValue
      : queueValues.length ? { status: 'available', observed_at: Math.max(...queueValues.map(value => value.observed_at || 0)) } : null;
    if (!sourceValue || sourceValue.status !== 'available') {
      status.textContent = 'Task telemetry není dostupná.';
      root.innerHTML = '<div class="obs-empty">TaskGraph nelze zobrazit bez durable queue.</div>';
      sceneCall('setTasks', []);
      return;
    }
    const allRows = sortedTaskNodes();
    const rows = allRows.filter(taskMatchesFilter);
    document.querySelectorAll('[data-task-filter]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.taskFilter === taskFilter)));
    const filterLabel = taskFilter === 'all' ? 'všechny stavy' : taskFilter === 'pending' ? 'čekající' : taskFilter === 'blocked' ? 'blocked + failed' : taskFilter;
    const authoritativeEdges = swarmEdges();
    status.textContent = swarmSnapshot()
      ? `Autoritativní Herdr DAG · ${authoritativeEdges.length} hran · filtr: ${filterLabel}.`
      : `Dependency telemetry není v aktuálním kontraktu · hrany se nevymýšlejí · filtr: ${filterLabel}.`;
    if (!allRows.length) {
      root.innerHTML = '<div class="obs-empty">Durable queue je prázdná.</div>';
      sceneCall('setTasks', []);
      return;
    }
    if (!rows.length) {
      root.innerHTML = '<div class="obs-empty">Pro zvolený filtr nejsou žádné tasky.</div>';
      sceneCall('setTasks', allRows.filter(row => row.status !== 'done'));
      return;
    }
    const edgeHTML = swarmSnapshot() ? taskEdgeHTML(authoritativeEdges, new Set(rows.map(row => row.task_id))) : '';
    if (taskFilter === 'all') {
      const priority = rows.filter(row => ['running', 'blocked', 'failed'].includes(row.status));
      const rest = rows.filter(row => !['running', 'blocked', 'failed'].includes(row.status));
      root.innerHTML = edgeHTML + taskLaneHTML('Aktivní / problémové', priority, 10) + taskLaneHTML('Čekající / hotové', rest, 14);
    } else {
      root.innerHTML = edgeHTML + taskLaneHTML(filterLabel, rows, 18);
    }
    const buttons = [...root.querySelectorAll('[data-task-id]')];
    buttons.forEach((button, index) => {
      button.addEventListener('click', () => openTaskDetail(button.dataset.taskId));
      button.addEventListener('keydown', event => {
        if (!['ArrowRight','ArrowLeft','ArrowDown','ArrowUp','Home','End','Enter',' '].includes(event.key)) return;
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openTaskDetail(button.dataset.taskId); return; }
        event.preventDefault();
        const step = event.key === 'ArrowDown' ? 2 : event.key === 'ArrowUp' ? -2 : event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : Math.max(0, Math.min(buttons.length - 1, index + step));
        buttons[next]?.focus();
      });
    });
    sceneCall('setTasks', allRows.filter(row => row.status !== 'done'));
  }

  function renderSwarmAnalytics() {
    const root = $('#swarm-analytics-grid');
    if (!root) return;
    if (!liveData) { root.innerHTML = '<article class="swarm-card"><header><h3>Swarm</h3></header><strong>—</strong><p>Živá telemetrie není dostupná.</p></article>'; return; }
    const m = swarmMetrics();
    const queueTotal = m.queue.length || 1;
    const mini = `<div class="swarm-mini">${['running','pending','blocked','failed','done'].map(status => { const count = m.queue.filter(row => row.status === status).length; return count ? `<i class="${status}" style="width:${(count / queueTotal * 100).toFixed(1)}%" title="${escapeHTML(QUEUE_STATUS[status] || status)}: ${count}"></i>` : ''; }).join('')}</div>`;
    const tokens = m.tokenTotal == null || !m.tokenKnownRequests ? '—' : compact.format(m.tokenTotal);
    const cost = m.cost == null || !m.costKnownRequests ? '—' : money(m.cost);
    const topModels = m.models.slice(0, 4);
    const mix = topModels.length ? topModels.map(row => `${escapeHTML(row.model)} ${fmt.format(row.requests)}`).join(' · ') : 'Model telemetry není dostupná.';
    root.innerHTML = [
      `<article class="swarm-card"><header><h3>Throughput</h3><span>tasks / time</span></header><strong>—</strong><p>Časová řada dokončených tasků není v autoritativním kontraktu; hodnotu neodhadujeme.</p></article>`,
      `<article class="swarm-card"><header><h3>Queue depth</h3><span>snapshot</span></header><strong>${fmt.format(m.activeQueue)}</strong>${mini}<p>${m.running} running · ${m.waiting} waiting · ${m.blockedOnly} blocked · ${m.failed} failed · ${m.done} done</p></article>`,
      `<article class="swarm-card"><header><h3>Latency</h3><span>router request avg</span></header><strong>${escapeHTML(latency(m.requestLatency))}</strong><p>Task queue/review p50+p95 nejsou dostupné; zobrazen je pouze měřený router request průměr.</p></article>`,
      `<article class="swarm-card"><header><h3>Tokens & cost</h3><span>known telemetry</span></header><strong>${escapeHTML(tokens)}</strong><p>${escapeHTML(cost)} known · ${m.costUnknownRequests || 0} req unknown · ${m.tokenUnknownRequests || 0} token fields unknown.</p></article>`,
      `<article class="swarm-card"><header><h3>Model mix</h3><span>requests</span></header><strong>${fmt.format(m.models.reduce((sum,row)=>sum+row.requests,0))}</strong><p>${mix}</p></article>`,
      `<article class="swarm-card"><header><h3>Reliability</h3><span>snapshot</span></header><strong>${fmt.format(m.retries)}</strong><p>true retries · ${m.blockedOnly} blocked · ${m.failed} failed · ${number(m.fallbacks)} model fallbacků.</p></article>`,
    ].join('');
  }

  function renderSwarm() {
    renderSwarmKpis();
    renderTaskGraph();
    renderSwarmAnalytics();
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
    const swarm = swarmSnapshot();
    const all = agents();
    if (swarm) {
      const tasks = operationalSwarmTasks();
      const blocked = tasks.filter(row => row.status === 'blocked');
      const runtimeAgents = swarmRuntimeAgents();
      const majakAgents = all.filter(row => row.profile === 'majak');
      const majakQueue = operationalQueueTasks('majak');
      const majakHerdr = source('majak', 'herdr');
      const majakProjected = liveData.sources.some(row => row.profile === 'majak');
      const userAttention = blocked.some(row => USER_ACTION_BLOCKERS.has(row.blocker))
        || (runtimeAgents?.some(row => row.status === 'blocked') ?? false)
        || majakAgents.some(row => row.status === 'blocked')
        || userBlockedTasks('quantlab').length
        || userBlockedTasks('majak').length;
      if (userAttention) return 'waiting_user';
      if (majakProjected && (!majakHerdr || majakHerdr.status !== 'available')) {
        return tasks.length || all.length ? 'error' : 'offline';
      }
      const working = (runtimeAgents?.some(row => row.status === 'working') ?? false)
        || swarmAgents().length
        || tasks.some(row => row.status === 'running')
        || majakAgents.some(row => row.status === 'working')
        || majakQueue.some(row => row.status === 'running');
      if (working) return 'working';
      if (blocked.length || technicalBlockedTasks('majak').length) return 'waiting_result';
      const majakOpen = majakQueue.some(row => row.status !== 'done');
      if (tasks.length && tasks.every(row => row.raw_state === 'done') && !majakOpen) return 'complete';
      if (majakAgents.some(row => row.status === 'idle')) return 'idle';
      return 'idle';
    }
    const hermes = all.filter(row => agentKind(row.agent) === 'hermes'), queued = operationalQueueTasks();
    if (all.some(row => row.status === 'blocked') || userBlockedTasks().length) return 'waiting_user';
    if (liveData.sources.some(row => row.kind === 'herdr' && row.status !== 'available')) return all.length ? 'error' : 'offline';
    if (hermes.some(row => row.status === 'working') || queued.some(row => row.status === 'running')) return 'working';
    if (technicalBlockedTasks().length) return 'waiting_result';
    if (hermes.some(row => row.status === 'idle')) return 'idle';
    if (hermes.length && hermes.every(row => row.status === 'done')) return 'complete';
    return 'offline';
  }
  function demoTarget() { return SCENE_AGENT_IDS.has(selectedAgent) ? selectedAgent : 'majak-codex'; }
  function faceCopy(state) {
    if (demo) return `DEMO · ${STATE_META[state].copy}`;
    const swarm = swarmSnapshot();
    const allAgents = agents();
    const runtimeAgents = swarmRuntimeAgents();
    const active = swarm
      ? [
          ...(runtimeAgents || []).filter(row => row.status === 'working').map(row => row.agent_id),
          ...allAgents.filter(row => row.profile === 'majak' && row.status === 'working').map(row => row.agent),
        ]
      : allAgents.filter(row => row.status === 'working').map(row => row.agent);
    const task = coordinatorTask();
    if (state === 'working' && task) {
      const project = task.repo === 'Bbambaaamm/dotacni-majak' ? 'Maják'
        : task.repo === 'Bbambaaamm/herdr' ? 'Herdr'
        : 'QuantLab';
      const durable = task.raw_state || task.status;
      const attempt = task.attempt_state && task.attempt_state !== durable
        ? ` / ${task.attempt_state}`
        : '';
      const taskRuntimeWorking = task.repo === 'Bbambaaamm/herdr'
        ? runtimeAgents?.some(row => row.status === 'working' && row.task_id === task.task_id) ?? false
        : allAgents.some(row => row.profile === (task.repo === 'Bbambaaamm/dotacni-majak' ? 'majak' : 'quantlab')
          && row.status === 'working' && row.agent === sceneAgent(task.agent));
      if (!taskRuntimeWorking) {
        return `${project} ${issueLabel(task)} · ${task.task_id} · durable ${durable}${attempt} · živý runtime nepotvrzen.`;
      }
      const reconcile = attempt ? ` · durable ${durable}${attempt}` : '';
      return `${project} ${issueLabel(task)} · ${task.task_id} · live práce probíhá${reconcile}.`;
    }
    if (state === 'working' || (state === 'idle' && active.length)) return `Pracují: ${active.join(', ')}. Přesný úkol zdroj neposkytuje.`;
    if (state === 'waiting_user') {
      const blockedAgents = [...new Set([
        ...(runtimeAgents || []).filter(row => row.status === 'blocked').map(row => row.agent_id),
        ...agents()
          .filter(row => row.status === 'blocked' && (!swarm || row.profile === 'majak'))
          .map(row => row.agent),
      ])];
      const blockerRows = swarm
        ? [...operationalSwarmTasks(), ...userBlockedTasks()]
        : userBlockedTasks();
      const blockedTasks = [...new Map(blockerRows.map(row => [row.task_id, row])).values()]
        .filter(row => row.status === 'blocked' && USER_ACTION_BLOCKERS.has(row.blocker))
        .map(row => `${issueLabel(row)} ${row.task_id}`);
      return `Zkontrolujte: ${[...blockedAgents, ...blockedTasks].join(', ') || 'blokovanou úlohu'}.`;
    }
    if (state === 'waiting_result') {
      const tasks = (swarm ? operationalSwarmTasks() : technicalBlockedTasks())
        .filter(row => row.status === 'blocked' && !USER_ACTION_BLOCKERS.has(row.blocker))
        .map(row => `${issueLabel(row)} ${row.blocker || row.task_id}`);
      return `Technicky blokováno: ${tasks.join(', ') || 'interní kontrola'}.`;
    }
    if (state === 'offline') return loadReason;
    if (state === 'error') return liveData.sources.filter(row => row.status === 'unavailable' && row.reason !== 'not_configured')
      .map(row => `${row.profile}/${row.kind}: ${row.reason}`).join(' · ') || 'Živý stav jednoho projektu není dostupný.';
    return STATE_META[state].copy;
  }
  function renderFace() {
    const state = effectiveState(), meta = STATE_META[state], color = toneColor(meta.tone);
    const currentTask = coordinatorTask();
    const pendingNext = coordinatorTasks()
      .filter(row => row.status === 'pending' && (!currentTask?.agent || row.agent === currentTask.agent))
      .sort((a, b) => (a.not_before ?? Number.MAX_SAFE_INTEGER) - (b.not_before ?? Number.MAX_SAFE_INTEGER) || a.task_id.localeCompare(b.task_id))[0];
    const nextTask = pendingNext?.task_id === currentTask?.task_id ? null : pendingNext;
    ui.faceState.textContent = meta.label; ui.faceTask.textContent = faceCopy(state);
    ui.coordinatorCurrent.textContent = demo ? `DEMO · ${STATE_META[state].label}` : taskDisplay(currentTask);
    ui.coordinatorNext.textContent = demo ? `DEMO · ${demoTarget()}` : taskDisplay(nextTask);
    ui.coordinatorCurrent.title = ui.coordinatorCurrent.textContent; ui.coordinatorNext.title = ui.coordinatorNext.textContent;
    ui.faceSignal.style.background = color; ui.faceSignal.style.color = color;
    ui.faceSignal.style.boxShadow = reduced ? 'none' : `0 0 13px ${color}`;
    if (state !== lastFaceState) { sceneCall('setState', state); lastFaceState = state; }
    const liveSwarm = swarmSnapshot(), queue = liveSwarm
      ? [...operationalSwarmTasks(), ...operationalQueueTasks('majak')]
      : operationalQueueTasks();
    const working = agents().filter(row => row.status === 'working');
    const majakWorking = working.filter(row => row.profile === 'majak');
    const runtimeAgents = liveSwarm ? swarmRuntimeAgents() : null;
    const runtimeWorking = runtimeAgents?.filter(row => row.status === 'working') || null;
    sceneCall('setActivity', {
      running: queue.filter(row => row.status === 'running').length,
      pending: queue.filter(row => row.status === 'pending').length,
      blocked: queue.filter(row => row.status === 'blocked').length,
      userBlocked: userBlockedTasks().length,
      workingAgents: liveSwarm
        ? (runtimeWorking?.length || 0) + majakWorking.length
        : working.length,
      activeAgent: liveSwarm
        ? (runtimeWorking?.[0]?.agent_id || majakWorking[0]?.agent || null)
        : (sceneAgent(currentTask?.agent) || working[0]?.agent || null),
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
      const queued = queueTasks(profile);
      const userBlocked = userBlockedTasks(profile).length;
      const technicalBlocked = technicalBlockedTasks(profile).length;
      $(`#${profile}-project-state`).textContent = rows.some(row => row.status === 'blocked') || userBlocked ? 'zásah'
        : rows.some(row => row.status === 'working') || queued.some(row => row.status === 'running') ? 'pracuje'
          : technicalBlocked ? 'čeká' : rows.every(row => row.unavailable) ? 'bez dat' : 'klid';
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
    const visibleProfiles = [...new Set(liveData.sources.map(value => value.profile))];
    const queueValues = queueSources();
    const queueComplete = visibleProfiles.length > 0
      && visibleProfiles.every(profile => source(profile, 'queue')?.status === 'available');
    ui.queueCount.textContent = queueComplete ? String(activeQueueTasks().length) : 'Nedostupné';
    ui.requestCount.textContent = number(total('requests')); ui.searchCount.textContent = number(searchCount);
    ui.searchLatency.textContent = latency(searchCount == null || searchDuration == null ? null : searchCount === 0 ? 0 : searchDuration / searchCount);
    const codex = codexStats().row;
    ui.costTotal.textContent = codex ? `${100 - codex.used_percent} %` : 'Nedostupné';
    ui.costTotal.title = codex ? `Reset ${resetLabel(codex.resets_at)}` : 'Codex usage snapshot není dostupný';
    $('#work-freshness').textContent = `Živý snapshot před ${age(liveData.generated_at)}`;
  }
  function renderObservability() {
    const kpis = $('#observability-kpis'), grid = $('#observability-grid');
    const truth = $('#observability-truth');
    if (truth) {
      const model = liveData?.observability;
      const fact = row => `<div class="metric"><span>${escapeHTML(row.id)}</span><strong>${row.value == null ? 'UNKNOWN' : escapeHTML(String(row.value))} ${escapeHTML(row.unit)}</strong><small>${escapeHTML(row.source)} · ${escapeHTML(row.freshness)} · age ${row.source_age_seconds == null ? 'UNKNOWN' : escapeHTML(String(row.source_age_seconds))}s · coverage ${row.coverage.covered}/${row.coverage.denominator}${row.reason ? ' · ' + escapeHTML(row.reason) : ''}${row.evidence_hash ? ' · ' + escapeHTML(row.evidence_hash) : ''}</small></div>`;
      truth.innerHTML = model
        ? `<article class="obs-panel"><h3>Lifecycle · durable source</h3><p>deployed_version is global release state; it does not attest task integration or deployment.</p>${model.lifecycle.map(fact).join('')}</article><article class="obs-panel"><h3>Measured router metrics · request coverage</h3>${model.metrics.map(fact).join('')}</article><article class="obs-panel full"><h3>Producer inventory</h3><p>legacy_search_router does not indicate #97 Search/Verifier availability.</p>${model.inventory.map(row => `<div class="metric"><span>${escapeHTML(row.id)}</span><strong>${escapeHTML(row.status)}</strong><small>${escapeHTML(row.source)} · ${escapeHTML(row.freshness)} · age ${row.source_age_seconds == null ? 'UNKNOWN' : escapeHTML(String(row.source_age_seconds))}s · coverage ${row.coverage.covered}/${row.coverage.denominator}${row.reason ? ' · ' + escapeHTML(row.reason) : ''}</small></div>`).join('')}</article>`
        : '<article class="obs-panel full"><div class="obs-empty">Production observability snapshot není dostupný.</div></article>';
    }
    if (!liveData) {
      kpis.innerHTML = '';
      grid.innerHTML = '<article class="obs-panel full"><div class="obs-empty">Živá telemetrie není dostupná.</div></article>';
      return;
    }
    const codex = codexStats().row;
    const routingAvailable = codex?.routing_status === 'available';
    const routeRows = routingAvailable ? [
      { label: 'FREE', value: codex.routing_free },
      { label: 'Sol', value: codex.routing_sol },
      { label: 'Astra', value: codex.routing_astra },
    ] : [];
    const profileStats = PROFILES.map(stats);
    const routersAvailable = profileStats.every(value => value.router?.status === 'available');
    const totalRequests = routersAvailable ? profileStats.reduce((sum, value) => sum + value.requests, 0) : null;
    const knownCost = routersAvailable ? profileStats.reduce((sum, value) => sum + value.costKnown, 0) : null;
    const knownCostRequests = routersAvailable ? profileStats.reduce((sum, value) => sum + (value.costKnownRequests || 0), 0) : null;
    const unknownCostRequests = routersAvailable ? profileStats.reduce((sum, value) => sum + value.costUnknownRequests, 0) : null;
    const workload = swarmMetrics();
    const activeAgents = workload.activeAgents;
    const activeQueue = workload.activeQueue;
    const remaining = codex ? 100 - codex.used_percent : null;
    const severity = remaining == null ? 'warn' : remaining <= 5 ? 'critical' : remaining <= 25 ? 'warn' : 'ok';
    const costCopy = knownCost == null ? 'Nedostupné'
      : !knownCostRequests ? `0 req oceněno · ${fmt.format(unknownCostRequests || 0)} unknown`
        : unknownCostRequests ? `${money(knownCost)} známé · ${fmt.format(unknownCostRequests)} req bez ceny` : money(knownCost);

    kpis.innerHTML = [
      `<article class="obs-kpi" data-severity="${severity}"><span>Codex allowance · zbývá</span><b>${remaining == null ? '—' : remaining + ' %'}</b><div class="obs-gauge"><i style="--gauge:${codex ? codex.used_percent : 0}%"></i></div><small>${codex ? (codex.ordinary_usage_allowed ? 'Běžné použití povoleno' : 'Limit vyčerpán') : 'Zdroj nedostupný'}</small></article>`,
      `<article class="obs-kpi"><span>Další reset Codex</span><b>${codex ? escapeHTML(resetLabel(codex.resets_at)) : '—'}</b><small>${codex ? escapeHTML(resetDistance(codex.resets_at)) : 'Čas resetu není dostupný'}</small></article>`,
      `<article class="obs-kpi"><span>Codex lifetime tokeny</span><b>${codex?.lifetime_tokens == null ? '—' : escapeHTML(compact.format(codex.lifetime_tokens))}</b><small>Peak/day: ${codex?.peak_daily_tokens == null ? '—' : escapeHTML(compact.format(codex.peak_daily_tokens))}</small></article>`,
      `<article class="obs-kpi"><span>Router požadavky</span><b>${number(totalRequests)}</b><small>${routersAvailable ? `${fmt.format(profileStats.reduce((s,v)=>s+(v.fallbacks||0),0))} fallbacků${routingAvailable ? ` · Astra eskalace ${fmt.format(codex.routing_astra_escalations)}` : ''}` : 'část routerů nedostupná'}</small></article>`,
      `<article class="obs-kpi"><span>Variabilní náklady</span><b>${knownCost == null || !knownCostRequests ? '—' : escapeHTML(money(knownCost))}</b><small>${escapeHTML(costCopy)}</small></article>`,
      `<article class="obs-kpi" data-severity="${activeQueue ? 'warn' : 'ok'}"><span>Aktivní práce</span><b>${activeAgents == null ? '—' : fmt.format(activeAgents)} agent · ${fmt.format(activeQueue)} fronta</b><small>${activeAgents == null ? 'Live runtime nedostupný · ' : ''}${activeQueue ? 'Durable fronta má neterminální úlohy' : 'Durable fronta bez aktivních položek'}</small></article>`,
    ].join('');

    const models = modelMetrics();
    const volumeRows = models.slice(0, 8);
    const fallbackRows = models.filter(row => row.requests > 0).map(row => ({ ...row, rate: row.fallbacks / row.requests * 100 }))
      .sort((a,b) => b.rate - a.rate || b.requests - a.requests).slice(0, 8);
    const latencyRows = models.filter(row => row.durationRequests > 0).map(row => ({ ...row, avg: row.durationMs / row.durationRequests }))
      .sort((a,b) => b.avg - a.avg).slice(0, 8);
    const tokenRows = models.filter(row => row.tokenKnownRequests > 0)
      .map(row => ({ ...row, tokens: row.inputTokens + row.outputTokens }))
      .sort((a,b) => b.tokens - a.tokens || b.requests - a.requests).slice(0, 8);

    const routerCoverageAvailable = profileStats.every(v => v.requests != null);
    const coverageMetric = (knownKey, unknownKey) => {
      if (!routerCoverageAvailable) return null;
      const known = profileStats.reduce((s,v)=>s+(v[knownKey] ?? 0),0);
      const unknown = profileStats.reduce((s,v)=>s+(v[unknownKey] ?? 0),0);
      const denominator = known + unknown;
      return denominator ? Math.round(known / denominator * 100) : null;
    };
    const coverage = [
      ['Input tokeny', coverageMetric('inputKnownRequests','inputUnknownRequests')],
      ['Output tokeny', coverageMetric('outputKnownRequests','outputUnknownRequests')],
      ['USD náklady', coverageMetric('costKnownRequests','costUnknownRequests')],
    ];

    const queueRows = queueTasks();
    const queueCounts = Object.fromEntries(Object.keys(QUEUE_STATUS).map(status => [status, queueRows.filter(row => row.status === status).length]));
    const queueTotal = Object.values(queueCounts).reduce((a,b)=>a+b,0);
    const admission = admissionSource();
    const admissionRowsNow = admissionRows();
    const admissionDenies = admissionDenials();
    const admissionAllows = admissionRowsNow.filter(row => row.event === 'allow');
    const denialReasons = [...new Map(
      admissionDenies.slice().reverse().map(row => [row.reason, row])
    ).values()].slice(0, 6);
    const searches = PROFILES.map(searchStats);
    const searchRoutesAvailable = searches.every(s => s.search?.status === 'available'
      && ['fast','deep','browser'].every(mode => s.routes[mode] != null));
    const searchRoutes = searchRoutesAvailable
      ? ['fast','deep','browser'].map(mode => ({ label: mode.toUpperCase(), value: searches.reduce((sum,s)=>sum+s.routes[mode],0) }))
      : [];
    const daily = (codex?.daily || []).map(row => ({ day: row.day.slice(5), tokens: row.tokens }));
    const history = codex?.limit_history || [];

    grid.innerHTML = [
      `<article class="obs-panel wide"><header><div><h3>Codex tokeny po dnech</h3><span>45 posledních měřených dní</span></div><span>${daily.length ? 'peak '+escapeHTML(compact.format(Math.max(...daily.map(r=>r.tokens)))) : 'bez dat'}</span></header>${lineChart(daily,'tokens',{id:'codexTokensArea'})}<p class="obs-note">Account-wide token activity z Codex app-serveru. Není převáděna na API cenu.</p></article>`,
      `<article class="obs-panel"><header><div><h3>Codex allowance</h3><span>časová řada využití</span></div><span>${codex ? codex.used_percent+' % použito' : 'nedostupné'}</span></header>${lineChart(history,'used_percent',{id:'codexLimitArea',suffix:' %',maxValue:100})}<p class="obs-note">${history.length < 2 ? 'Historii jsme právě začali sbírat; graf se bude plnit automaticky.' : 'Snapshot každých přibližně 5 minut.'}${routingAvailable ? ` · Router soft ${fmt.format(codex.routing_soft_limit_pct)} % / hard ${fmt.format(codex.routing_hard_limit_pct)} %.` : ''}</p></article>`,
      `<article class="obs-panel"><header><div><h3>Cost-aware router</h3><span>FREE / Sol / Astra · task decisions</span></div><span>${routingAvailable ? escapeHTML(codex.routing_policy_version) : 'nedostupné'}</span></header>${bars(routeRows,r=>r.value,v=>fmt.format(v))}<div class="obs-legend"><span>Astra eskalace: ${routingAvailable ? fmt.format(codex.routing_astra_escalations) : '—'}</span><span>Premium blokováno: ${routingAvailable ? fmt.format(codex.routing_premium_denied) : '—'}</span></div><p class="obs-note">${routingAvailable ? `Poslední route: ${escapeHTML(codex.last_route_model || '—')} · ${escapeHTML(codex.last_route_reason || '—')}` : 'Routing telemetry není dostupná.'}</p></article>`,
      `<article class="obs-panel"><header><div><h3>Model traffic</h3><span>počet skutečných provider requestů</span></div><span>top 8</span></header>${bars(volumeRows,r=>r.requests,v=>fmt.format(v))}</article>`,
      `<article class="obs-panel"><header><div><h3>Model tokeny</h3><span>skutečně změřené router requesty</span></div><span>top 8</span></header>${bars(tokenRows,r=>r.tokens,v=>compact.format(v))}<p class="obs-note">Per-model tokeny jsou autoritativní pro Hermes router. Codex Sol/Astra zde nejsou odhadovány; jejich account-wide tokeny zůstávají v samostatném grafu.</p></article>`,
      `<article class="obs-panel"><header><div><h3>Fallback pressure</h3><span>fallbacky / požadavky</span></div><span>vyšší = horší</span></header>${bars(fallbackRows,r=>r.rate,v=>v.toFixed(1)+' %',{percent:true,alert:r=>r.rate>=25})}</article>`,
      `<article class="obs-panel"><header><div><h3>Model latency</h3><span>průměr na request</span></div><span>jen známá latence</span></header>${bars(latencyRows,r=>r.avg,v=>latency(v))}</article>`,
      `<article class="obs-panel"><header><div><h3>Data coverage</h3><span>request-weighted completeness</span></div><span>fail-closed</span></header>${coverage.map(([name,pct])=>`<div class="coverage-row"><span>${escapeHTML(name)}</span><div class="coverage-track"><i style="width:${pct == null ? 0 : pct}%"></i></div><strong>${pct == null ? 'UNKNOWN' : pct+' %'}</strong></div>`).join('')}<p class="obs-note">100 % znamená, že každému requestu odpovídá měřená hodnota. Chybějící hodnoty nejsou dopočítány.</p></article>`,
      `<article class="obs-panel"><header><div><h3>Durable queue</h3><span>stav práce QuantLab</span></div><span>${queueTotal} záznamů</span></header>${queueTotal ? `<div class="queue-strip">${Object.entries(queueCounts).filter(([,count])=>count).map(([status,count])=>`<i class="${status}" style="width:${(count/queueTotal*100).toFixed(1)}%" title="${escapeHTML(QUEUE_STATUS[status])}: ${count}"></i>`).join('')}</div><div class="obs-legend">${Object.entries(queueCounts).map(([status,count])=>`<span>${escapeHTML(QUEUE_STATUS[status])}: ${count}</span>`).join('')}</div>` : '<div class="obs-empty">Fronta je prázdná.</div>'}</article>`,
      `<article class="obs-panel"><header><div><h3>Swarm admission</h3><span>ALLOW / DENY před spawnem</span></div><span>${admission?.status === 'available' ? `${admissionAllows.length} / ${admissionDenies.length}` : 'nedostupné'}</span></header>${admission?.status === 'available' ? `<div class="obs-legend"><span>ALLOW: ${admissionAllows.length}</span><span>DENY: ${admissionDenies.length}</span></div>${denialReasons.length ? `<div class="admission-reasons">${denialReasons.map(row => `<span><b>${escapeHTML(row.reason)}</b> · ${escapeHTML(row.repo)} #${escapeHTML(row.issue)} · ${escapeHTML(age(row.observed_at))}</span>`).join('')}</div>` : '<p class="obs-note">V aktuálním bounded tail nejsou žádné denialy.</p>'}<p class="obs-note">Zobrazeny jsou pouze sanitizované reason codes a DAG scope. Prompt, detail toolu ani secrets se neexportují.</p>` : '<div class="obs-empty">Admission audit není v aktuálním snapshotu dostupný.</div>'}</article>`,
      `<article class="obs-panel"><header><div><h3>Legacy Search Router route mix</h3><span>Fast / Deep / Browser · není #97 verifier</span></div><span>${searchRoutesAvailable ? 'měřený snapshot' : 'UNKNOWN'}</span></header>${searchRoutesAvailable ? bars(searchRoutes,r=>r.value,v=>fmt.format(v)) : '<div class="obs-empty">Legacy Search Router není v autorizovaném snapshotu dostupný.</div>'}</article>`,
      `<article class="obs-panel"><header><div><h3>Codex účet</h3><span>read-only stav</span></div><span>data před ${codexStats().source ? escapeHTML(age(codexStats().source.observed_at)) : '—'}</span></header><div class="obs-legend"><span>Kredity: ${codex ? escapeHTML(codex.credits_balance ?? 'neznámé') : '—'}</span><span>Reset kredity: ${codex ? fmt.format(codex.reset_credits_available) : '—'}</span><span>Streak: ${codex?.current_streak_days == null ? '—' : fmt.format(codex.current_streak_days)+' dní'}</span><span>Max streak: ${codex?.longest_streak_days == null ? '—' : fmt.format(codex.longest_streak_days)+' dní'}</span></div><p class="obs-note">USD odhad se zobrazí jen pokud jej billing route skutečně poskytne. Subscription allowance se nepřepočítává na API ceník.</p></article>`,
    ].join('');
  }

  function renderQueue() {
    const values = queueSources(), summary = $('#queue-summary'), list = $('#queue-list');
    if (!values.some(value => value.status === 'available')) {
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
      const title = row.issue_title || row.kind;
      return `<article class="queue-task" data-status="${escapeHTML(row.status)}"><div class="queue-task-main"><b>${escapeHTML(issueLabel(row))} · <code>${escapeHTML(row.task_id)}</code></b><small>${escapeHTML(title)} · ${escapeHTML(row.kind)} · ${escapeHTML(row.agent)}</small></div><span class="queue-status">${escapeHTML(QUEUE_STATUS[row.status] || row.status)}</span><span class="queue-attempt">Pokus ${escapeHTML(attemptLabel(row))}</span><time>${escapeHTML(timing)}</time><span class="queue-blocker">${escapeHTML(blocker)}</span></article>`;
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
      const currentProvider = value.currentProvider || 'Zatím bez provozu';
      const historicalProviders = value.historicalProviders.join(', ') || '—';
      const fallbackProviders = value.fallbackProviders.join(', ') || '—';
      return `<article class="search-card"><header><div><span>${escapeHTML(profile.toUpperCase())}</span><b>Search Router</b></div><span class="search-health">${number(value.searches)} hledání</span></header><div class="search-metrics"><div><span>Úspěšnost</span><b>${escapeHTML(success)}</b></div><div><span>Latence avg / max</span><b>${escapeHTML(`${latency(value.avgLatency)} / ${latency(value.maxLatency)}`)}</b></div><div><span>Fallbacky</span><b>${number(value.fallbacks)}</b></div><div><span>Náklady</span><b>${escapeHTML(money(value.cost))}</b></div></div><div class="search-routes"><span>FAST <b>${number(value.routes.fast)}</b></span><span>DEEP <b>${number(value.routes.deep)}</b></span><span>BROWSER <b>${number(value.routes.browser)}</b></span></div><p><span>Aktuální provider (poslední běh):</span> ${escapeHTML(currentProvider)}</p><p><span>Historické providery:</span> ${escapeHTML(historicalProviders)}</p><p><span>Pozorované fallback providery:</span> ${escapeHTML(fallbackProviders)}</p><p><span>Výsledky / extrakce:</span> ${number(value.results)} / ${number(value.extracts)} · data před ${escapeHTML(age(value.search.data_at))}</p></article>`;
    }).join('');
  }

  function renderWork() {
    $('#project-grid').innerHTML = PROFILES.map(profile => {
      const rows = agents().filter(row => row.profile === profile), value = stats(profile);
      const tokenCoverage = value.inputCoverage == null || value.outputCoverage == null ? null : Math.min(value.inputCoverage, value.outputCoverage);
      const tokenText = value.inputKnown == null ? 'Nedostupné' : `${number(value.inputKnown)} / ${number(value.outputKnown)}${tokenCoverage < 100 ? ` · ${tokenCoverage} % req` : ''}`;
      const costText = value.costKnown == null ? 'Nedostupné' : `${money(value.costKnown)} známé${value.costUnknownRequests ? ` + ${fmt.format(value.costUnknownRequests)} bez ceny` : ''}`;
      return `<article class="work-project"><h2>${profile.toUpperCase()}</h2>${rows.length ? rows.map(row => `<button class="work-agent" data-agent="${escapeHTML(row.agent)}"><b>${escapeHTML(row.agent)}</b><span>${statusLabel(row.status)}</span><small>${ROLES[agentKind(row.agent)]}</small></button>`).join('') : '<p>Živý stav agentů není dostupný.</p>'}<p class="work-models">Modely profilu: ${escapeHTML(value.models.join(', ') || 'Nedostupné')}</p><p class="work-models">Aktuální provider (poslední běh): ${escapeHTML(value.currentProvider || 'Nedostupné')}</p><p class="work-models">Historické providery: ${escapeHTML(value.historicalProviders.join(', ') || '—')}</p><div class="work-totals"><div><span>Požadavky</span><b>${number(value.requests)}</b></div><div><span>Tokeny vstup/výstup</span><b>${escapeHTML(tokenText)}</b></div><div><span>Známé náklady / fallbacky</span><b>${escapeHTML(costText)} · ${number(value.fallbacks)}</b></div></div></article>`;
    }).join('');
    $('#project-grid').querySelectorAll('[data-agent]').forEach(button => button.addEventListener('click', () => openDetail(button.dataset.agent)));
    renderObservability(); renderQueue(); renderSearch();
    $('#source-grid').innerHTML = (liveData?.sources || []).map(row => {
      const label = row.kind === 'codex' ? 'CODEX / ÚČET' : `${row.profile} / ${row.kind}`;
      return `<article class="source-card" data-status="${escapeHTML(row.status)}"><b>${escapeHTML(label)}</b><span>${escapeHTML(row.status)} · ${escapeHTML(row.reason)}</span><span>${row.status === 'available' ? `${row.rows.length} záznamů` : 'bez dat'}</span></article>`;
    }).join('');
    const sourceUserActionReasons = new Set(['user_action_required', 'auth_required', 'credentials_missing', 'permission_required']);
    const sourceActions = (liveData?.sources || []).filter(row => row.status === 'unavailable' && sourceUserActionReasons.has(row.reason));
    const blocked = blockedAgents();
    const queueAlerts = userBlockedTasks();
    const summary = $('#attention-summary');
    summary.hidden = Boolean(liveData) && !sourceActions.length && !blocked.length && !queueAlerts.length;
    summary.textContent = !liveData ? loadReason : `Vyžaduje váš zásah: ${[...blocked.map(row => row.agent), ...queueAlerts.map(row => `${issueLabel(row)} ${row.task_id}`), ...sourceActions.map(row => `${row.profile}/${row.kind} (${row.reason})`)].join(', ')}`;
    if (!summary.hidden) {
      const action = document.createElement('button'); action.type = 'button'; action.className = 'attention-action';
      action.textContent = blocked.length ? 'Otevřít blokovaného agenta' : queueAlerts.length ? 'Otevřít frontu' : 'Obnovit data';
      action.addEventListener('click', () => blocked.length ? openBlockedAgent(blocked[0]) : queueAlerts.length ? $('#queue-title').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' }) : refresh(true)); summary.append(' ', action);
    }
  }
  function renderTaskDetail() {
    const task = taskById(selectedTask);
    const swarmTask = task?.kind === 'herdr_swarm';
    const taskState = task?.raw_state || (task ? QUEUE_STATUS[task.status] || task.status : null);
    const dependencyEvidence = task
      ? swarmTask
        ? [
          task.parent_task_id ? `parent ${task.parent_task_id}` : 'root task',
          task.dependencies?.length ? `depends on ${task.dependencies.join(', ')}` : 'no dependencies',
        ].join(' · ')
        : 'Nedostupné v telemetry kontraktu · žádná hrana nebyla odvozena'
      : null;
    const modelEvidence = task
      ? swarmTask
        ? `${task.model || 'model nehlášen'} · fallback ${task.fallback_model || '—'}`
        : 'Nedostupné v telemetry kontraktu'
      : null;
    const resultEvidence = task
      ? swarmTask
        ? `result ${task.result_sha || '—'} · branch/base nejsou v kontraktu`
        : 'Nedostupné v telemetry kontraktu'
      : null;
    $('#detail-profile').textContent = 'SWARM TASK';
    $('#detail-title').textContent = task ? `${issueLabel(task)} · ${task.task_id}` : selectedTask || 'Task';
    $('#detail-role').textContent = 'Durable task node · read only';
    $('#detail-status').textContent = task ? `Stav: ${taskState}` : 'Task už není v aktuálním snapshotu';
    $('#detail-links').innerHTML = task ? [
      detailLink(issueUrl(task), `Otevřít Issue ${issueLabel(task)}`),
      detailLink(prUrl(task), task.pr_number ? `Otevřít PR #${task.pr_number}` : ''),
    ].filter(Boolean).join('') : '';
    const metrics = task ? [
      ['Task ID', task.task_id],
      ['Issue / název', `${issueLabel(task)} · ${task.issue_title || task.kind}`],
      ['Stav / scheduler', `${taskState} · ${swarmTask ? 'authoritative swarm' : task.scheduler_state || 'nehlášeno'}`],
      ['Pokus / maximum', attemptLabel(task)],
      ['Agent', task.agent || '—'],
      ['Typ', task.kind],
      ['PR', task.pr_number ? `#${task.pr_number}` : 'Není hlášeno'],
      ['Blocker', task.blocker || '—'],
      ['Čas', task.status === 'pending' ? `nejdříve ${queueTime(task.not_before)}` : `změna ${queueTime(task.updated_at)}`],
      ['Dependency edges', dependencyEvidence],
      ['Model / fallback', modelEvidence],
      ['Fencing token', swarmTask ? number(task.fencing_token) : 'Nedostupné v telemetry kontraktu'],
      ['Runtime / queue wait', 'Nedostupné v telemetry kontraktu'],
      ['Branch / base / result SHA', resultEvidence],
      ['Test / reviewer', 'Nedostupné v telemetry kontraktu'],
    ] : [['Stav', 'Task už není v aktuálním snapshotu']];
    $('#detail-metrics').innerHTML = metrics.map(([title, content]) => `<div><dt>${escapeHTML(title)}</dt><dd>${escapeHTML(content)}</dd></div>`).join('');
    const events = task ? [
      `Durable queue: ${issueLabel(task)} · ${task.task_id} · ${taskState}`,
      `Scheduler: ${swarmTask ? 'authoritative swarm' : task.scheduler_state || 'nehlášeno'} · pokus ${attemptLabel(task)}`,
      task.blocker ? `Blocker: ${task.blocker}` : 'Bez hlášeného blockeru',
      swarmTask
        ? `Autoritativní DAG: ${dependencyEvidence}.`
        : 'Dependency telemetry není součástí aktuálního snapshotu; DAG hrany nejsou odhadovány.',
      'Prompt, interní myšlenky a raw log nejsou v dashboardu zobrazovány.',
    ] : ['Task není v aktuálním snapshotu.'];
    $('#detail-events').innerHTML = events.map(event => `<li>${escapeHTML(event)}</li>`).join('');
  }

  function renderDetail() {
    if (selectedTask) { renderTaskDetail(); return; }
    if (!selectedAgent) return;
    const runtimeRow = swarmRuntimeAgents()?.find(item => item.agent_id === selectedAgent);
    const row = runtimeRow
      ? { ...runtimeRow, agent: runtimeRow.agent_id, profile: 'quantlab', runtime: true }
      : agents().find(item => item.agent === selectedAgent);
    const profile = row?.profile || (selectedAgent.startsWith('majak-') ? 'majak' : 'quantlab');
    const value = stats(profile), search = searchStats(profile), herdr = source(profile, 'herdr');
    const hasQueue = selectedAgent.endsWith('-hermes');
    const queueAgent = durableAgent(selectedAgent);
    const task = runtimeRow?.task_id
      ? taskById(runtimeRow.task_id)
      : hasQueue ? currentQueueTask(queueAgent) || nextQueueTask(queueAgent) : null;
    const currentTask = hasQueue
      ? task ? `${issueLabel(task)} · ${task.task_id} · ${QUEUE_STATUS[task.status] || task.status}` : 'Žádná úloha v durable queue'
      : 'Nedostupné v datovém kontraktu';
    const taskTitle = task?.issue_title || 'Nedostupné v telemetry kontraktu';
    const taskState = task
      ? `${QUEUE_STATUS[task.status] || task.status} · scheduler ${task.scheduler_state || 'nehlášeno'}`
      : 'Nedostupné v telemetry kontraktu';
    const taskTiming = task
      ? `${task.status === 'pending' ? 'nejdříve ' + queueTime(task.not_before) : 'změna ' + queueTime(task.updated_at)}`
      : 'Nedostupné v telemetry kontraktu';
    const tokenCoverage = value.inputCoverage == null || value.outputCoverage == null
      ? null : Math.min(value.inputCoverage, value.outputCoverage);
    const tokens = value.inputKnown == null ? 'Nedostupné'
      : `${number(value.inputKnown)} / ${number(value.outputKnown)}${tokenCoverage < 100 ? ` · coverage ${tokenCoverage} % req` : ''}`;
    const costs = value.costKnown == null ? 'Nedostupné'
      : `${money(value.costKnown)} známé${value.costUnknownRequests ? ` + ${fmt.format(value.costUnknownRequests)} req bez ceny` : ''}`;

    $('#detail-profile').textContent = row?.runtime ? 'HERDR' : profile.toUpperCase(); $('#detail-title').textContent = selectedAgent;
    $('#detail-role').textContent = row?.runtime ? 'Runtime agent · read only' : ROLES[agentKind(selectedAgent)];
    $('#detail-status').textContent = `Živý stav: ${row ? statusLabel(row.status) : 'Odpojeno / neznámé'}`;
    $('#detail-links').innerHTML = [
      detailLink(issueUrl(task), task ? `Otevřít Issue ${issueLabel(task)}` : ''),
      detailLink(prUrl(task), task?.pr_number ? `Otevřít PR #${task.pr_number}` : ''),
    ].filter(Boolean).join('');

    const metrics = [
      ['Aktuální úkol', currentTask],
      ['Issue / název', task ? `${issueLabel(task)} · ${taskTitle}` : 'Nedostupné v telemetry kontraktu'],
      ['Task stav', taskState],
      ['Pokus / maximum', attemptLabel(task)],
      ['Čas fronty', taskTiming],
      ['PR', task?.pr_number ? `#${task.pr_number}` : 'Není hlášeno'],
      ['Blocker', task?.blocker || '—'],
      ['Modely profilu', value.models.join(', ') || 'Nedostupné v aktuálním snapshotu'],
      ['Aktuální model provider / fallbacky', `${value.currentProvider || 'Nedostupné'} · ${number(value.fallbacks)}`],
      ['Historické model providery', value.historicalProviders.join(', ') || '—'],
      ['Tokeny vstup / výstup', tokens],
      ['Známé náklady profilu', costs],
      ['Aktuální search provider / fallbacky', `${search.currentProvider || 'Nedostupné'} · ${number(search.fallbacks)}`],
      ['Historické search providery', search.historicalProviders.join(', ') || '—'],
      ['Search / avg latence', `${number(search.searches)} · ${latency(search.avgLatency)}`],
      ['Runtime / queue wait', 'Nedostupné v telemetry kontraktu'],
      ['Branch / base / result SHA', 'Nedostupné v telemetry kontraktu'],
      ['Test / reviewer', 'Nedostupné v telemetry kontraktu'],
    ];
    $('#detail-metrics').innerHTML = metrics.map(([title, content]) => `<div><dt>${escapeHTML(title)}</dt><dd>${escapeHTML(content)}</dd></div>`).join('');
    const events = [];
    if (row) events.push(`Herdr hlásí stav „${row.status}“ · pozorováno před ${age(row.runtime ? swarmSource()?.observed_at : herdr?.observed_at)}`);
    if (task) events.push(`Durable queue: ${issueLabel(task)} · ${task.task_id} · ${QUEUE_STATUS[task.status] || task.status} · pokus ${attemptLabel(task)} · scheduler ${task.scheduler_state || 'nehlášeno'}`);
    if (task?.blocker) events.push(`Blocker: ${task.blocker}`);
    if (value.router?.status === 'available') events.push(`Router profilu: ${number(value.requests)} požadavků · data před ${age(value.router.data_at)}`);
    if (search.search?.status === 'available') events.push(`Search Router: ${number(search.searches)} hledání · ${latency(search.avgLatency)} průměr · ${number(search.fallbacks)} fallbacků · data před ${age(search.search.data_at)}`);
    events.push('Runtime, branch/SHA, test a reviewer data se nezobrazují, dokud je autoritativní telemetry kontrakt neposkytuje.');
    events.push('Zdroj neposkytuje prompt, historii nástrojů, interní myšlenky ani surové provozní záznamy úlohy.');
    if (demo) events.unshift('DEMO: pohyb 3D scény je syntetický. Tento detail stále zobrazuje skutečný snapshot.');
    $('#detail-events').innerHTML = events.map(event => `<li>${escapeHTML(event)}</li>`).join('');
  }
  function openDetail(name) {
    if (!PROFILES.flatMap(displayedAgents).some(row => row.agent === name)
      && !swarmRuntimeAgents()?.some(row => row.agent_id === name)) return;
    returnFocus = document.activeElement; selectedTask = null; selectedAgent = name; renderDetail();
    ui.detail.hidden = false; ui.backdrop.hidden = false; document.body.style.overflow = 'hidden';
    $('#detail-close').focus(); sceneCall('focusTask', null); sceneCall('focusAgent', name); if (demo) renderProjects(); renderTaskGraph(); renderFace();
  }
  function openTaskDetail(taskId) {
    const task = taskById(taskId); if (!task) return;
    returnFocus = document.activeElement; selectedAgent = null; selectedTask = taskId; renderTaskDetail();
    ui.detail.hidden = false; ui.backdrop.hidden = false; document.body.style.overflow = 'hidden';
    $('#detail-close').focus(); sceneCall('focusAgent', null); sceneCall('focusTask', taskId); renderTaskGraph(); renderFace();
  }
  function closeDetail() {
    ui.detail.hidden = true; ui.backdrop.hidden = true; document.body.style.overflow = '';
    sceneCall('focusAgent', null);
    sceneCall('focusTask', selectedTask || null);
    if (returnFocus?.isConnected) returnFocus.focus();
    else if (selectedTask) document.querySelector(`[data-task-id="${CSS.escape(selectedTask)}"]`)?.focus();
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
    const release = releaseInfo();
    const identity = release ? ` · ${release.tag} @ ${release.commit.slice(0, 12)}` : '';
    ui.header.textContent = demo ? (liveData ? 'DEMO · scéna syntetická · metriky z production snapshotu' : 'DEMO · scéna syntetická · production metriky nedostupné') : liveData ? `Živá data · ${age(liveData.generated_at)}${identity}` : loadReason;
    const color = demo ? '#e49a34' : liveData ? '#6adf9a' : '#ff7159'; ui.liveDot.style.background = color; ui.liveDot.style.color = color;
  }
  function renderAll() {
    updateHeader(); renderProjects(); renderTelemetry(); renderSwarm(); renderWork(); renderFace();
    if (!ui.detail.hidden) renderDetail();
  }
  function validateSnapshot(value) {
    if (!value || !Number.isFinite(value.generated_at) || !Array.isArray(value.sources)) throw new Error('invalid');
    const model = value.observability;
    const axes = ['observed_live_execution', 'delivery_reconciliation', 'settled_control_cycle', 'verified_artifact', 'integrated_change', 'deployed_version'];
    const inventory = ['runtime_swarm', 'model_routing', 'router', 'legacy_search_router', 'release',
      'fabric', 'tool_fabric', 'search_verifier', 'prompt_runtime', 'human_event', 'eval_shadow',
      'budget', 'context_skill', 'semantic_guard', 'mcp_a2a_specialist', 'reviewer',
      'approval_hitl', 'policy_registry', 'provider_health', 'circuit_breaker',
      'evidence_acceptance', 'execution_plan', 'work_protocol', 'route_decision_trace',
      'verification_baseline', 'route_policy_history'];
    const exact = (row, fields) => row && typeof row === 'object' && !Array.isArray(row)
      && Object.keys(row).sort().join(',') === fields.slice().sort().join(',');
    const coverage = value => exact(value, ['covered', 'denominator'])
      && [value.covered, value.denominator].every(n => Number.isSafeInteger(n) && n >= 0)
      && value.covered <= value.denominator;
    if (!exact(model, ['version', 'lifecycle', 'metrics', 'inventory']) || model.version !== 1
      || !Array.isArray(model.lifecycle) || model.lifecycle.length !== axes.length
      || model.lifecycle.some((row, i) => row.id !== axes[i])
      || !Array.isArray(model.metrics) || model.metrics.length > 128
      || !Array.isArray(model.inventory) || model.inventory.length !== inventory.length
      || model.inventory.some((row, i) => row.id !== inventory[i])) throw new Error('invalid');
    for (const row of [...model.lifecycle, ...model.metrics]) {
      const fields = ['id', 'value', 'unit', 'window', 'source', 'freshness', 'source_age_seconds', 'coverage', 'reason'];
      if (!(exact(row, fields) || exact(row, [...fields, 'evidence_hash']))
        || ['id', 'unit', 'window', 'source'].some(k => typeof row[k] !== 'string' || row[k].length > 80)
        || !(row.value == null || typeof row.value === 'boolean' || Number.isSafeInteger(row.value)
          || typeof row.value === 'string' && row.value.length <= 80)
        || !['fresh', 'stale', 'unavailable', 'unknown'].includes(row.freshness)
        || !(row.source_age_seconds == null || Number.isSafeInteger(row.source_age_seconds) && row.source_age_seconds >= 0)
        || !coverage(row.coverage) || !(row.reason == null || typeof row.reason === 'string' && row.reason.length <= 64)
        || row.evidence_hash != null && !/^(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(row.evidence_hash)) throw new Error('invalid');
    }
    for (const row of model.inventory) {
      if (!exact(row, ['id', 'status', 'reason', 'source', 'freshness', 'source_age_seconds', 'coverage'])
        || !['available', 'UNKNOWN'].includes(row.status)
        || typeof row.source !== 'string' || row.source.length > 80
        || !['fresh', 'stale', 'unavailable', 'unknown'].includes(row.freshness)
        || !(row.source_age_seconds == null || Number.isSafeInteger(row.source_age_seconds) && row.source_age_seconds >= 0)
        || !coverage(row.coverage) || !(row.reason == null || typeof row.reason === 'string' && row.reason.length <= 64)) throw new Error('invalid');
    }
    if (Date.now() / 1000 - value.generated_at > 90 || value.generated_at > Date.now() / 1000 + 5) throw new Error('stale');
    for (const item of value.sources) {
      if (!item || !PROFILES.includes(item.profile) || typeof item.kind !== 'string' || !Array.isArray(item.rows)) throw new Error('invalid');
      if (item.kind === 'herdr' && item.rows.some(row => typeof row.agent !== 'string' || typeof row.status !== 'string')) throw new Error('invalid');
      if (['router', 'search'].includes(item.kind)
        && item.rows.some(row => typeof row.provider !== 'string' || !Number.isFinite(row.last_used_at))) throw new Error('invalid');
      if (item.kind === 'queue') {
        const expected = item.profile === 'majak'
          ? { repo: 'Bbambaaamm/dotacni-majak', agent: 'dotacni-majak-hermes' }
          : { repo: 'Bbambaaamm/Autonomous-Quant-Lab', agent: 'quantlab-hermes' };
        if (item.rows.some(row =>
          typeof row.task_id !== 'string'
          || (row.repo != null && typeof row.repo !== 'string')
          || (item.profile === 'majak' && row.repo !== expected.repo)
          || (item.profile === 'quantlab' && row.repo != null && row.repo !== expected.repo)
          || (row.issue != null && (!Number.isSafeInteger(row.issue) || row.issue < 0))
          || (row.issue_title != null && (typeof row.issue_title !== 'string' || row.issue_title.length > 160))
          || typeof row.issue_open !== 'boolean'
          || (row.scheduler_state != null && typeof row.scheduler_state !== 'string')
          || row.agent !== expected.agent
          || typeof row.kind !== 'string'
          || !Object.hasOwn(QUEUE_STATUS, row.status)
          || !Number.isSafeInteger(row.attempts) || row.attempts < 0
          || !Number.isSafeInteger(row.max_attempts) || row.max_attempts < 0
          || (row.not_before != null && !Number.isFinite(row.not_before))
          || !Number.isFinite(row.updated_at)
          || (row.blocker != null && typeof row.blocker !== 'string')
          || (row.pr_number != null && (!Number.isSafeInteger(row.pr_number) || row.pr_number < 1))
        )) throw new Error('invalid');
      }
      if (item.kind === 'admission') {
        if (item.profile !== 'quantlab') throw new Error('invalid');
        if (item.rows.some(row => !['allow', 'deny'].includes(row.event)
          || (row.reason != null && typeof row.reason !== 'string')
          || typeof row.role !== 'string' || typeof row.repo !== 'string' || typeof row.issue !== 'string'
          || !Number.isSafeInteger(row.node_count) || row.node_count < 0
          || !Number.isSafeInteger(row.max_depth) || row.max_depth < 0
          || !Number.isSafeInteger(row.max_fanout) || row.max_fanout < 0
          || !Number.isSafeInteger(row.child_tools_count) || row.child_tools_count < 0
          || (row.agents_after != null && (!Number.isSafeInteger(row.agents_after) || row.agents_after < 0))
          || !Number.isFinite(row.observed_at)
          || (row.event === 'deny' && (row.reason == null || row.agents_after != null))
          || (row.event === 'allow' && (row.reason != null || row.agents_after == null))
        )) throw new Error('invalid');
      }
      if (item.kind === 'swarm') {
        if (item.profile !== 'quantlab' || (item.status === 'available' && item.rows.length !== 1)) throw new Error('invalid');
        for (const row of item.rows) {
          const runtimeStatus = row.runtime_status ?? 'unavailable';
          const runtimeAgents = row.runtime_agents ?? [];
          if (row.version !== 1 || typeof row.repo !== 'string' || typeof row.issue !== 'string'
            || (row.issue_state != null && !['open', 'closed', 'unknown'].includes(row.issue_state))
            || typeof row.paper_only !== 'boolean' || !Array.isArray(row.policy_profiles)
            || !Array.isArray(row.agents) || !Array.isArray(row.tasks) || !Array.isArray(row.edges)
            || !['available', 'unavailable', 'not_applicable'].includes(runtimeStatus)
            || !Array.isArray(runtimeAgents)
            || (runtimeStatus !== 'available' && runtimeAgents.length)
            || (row.repo === 'Bbambaaamm/Autonomous-Quant-Lab' && row.paper_only !== true)) throw new Error('invalid');
          const taskIds = new Set();
          for (const task of row.tasks) {
            if (!task || typeof task.task_id !== 'string' || taskIds.has(task.task_id)
              || !Object.hasOwn(SWARM_STATUS, task.state) || typeof task.role !== 'string'
              || !Number.isSafeInteger(task.attempt) || task.attempt < 0
              || !Number.isSafeInteger(task.max_attempts) || task.max_attempts < task.attempt
              || (task.attempt_state != null && !['dispatching','accepted','working','delivery_uncertain','verifying','completed','done','blocked','failed','retry_scheduled'].includes(task.attempt_state))
              || (task.delivery_reconcile_count != null && (!Number.isSafeInteger(task.delivery_reconcile_count) || task.delivery_reconcile_count < 0))
              || !Number.isSafeInteger(task.fencing_token) || task.fencing_token < 0
              || !Array.isArray(task.dependencies)
              || task.dependencies.some(dep => typeof dep !== 'string')
              || (task.parent_task_id != null && typeof task.parent_task_id !== 'string')
              || (task.parent_agent_id != null && typeof task.parent_agent_id !== 'string')
              || (task.agent_id != null && typeof task.agent_id !== 'string')
              || (task.result_sha != null && (typeof task.result_sha !== 'string' || !/^[0-9a-f]{64}$/.test(task.result_sha)))) throw new Error('invalid');
            taskIds.add(task.task_id);
          }
          const tasksById = new Map(row.tasks.map(task => [task.task_id, task]));
          const runtimeIds = new Set();
          for (const runtimeAgent of runtimeAgents) {
            if (!runtimeAgent || typeof runtimeAgent.agent_id !== 'string' || runtimeIds.has(runtimeAgent.agent_id)
              || !['idle','working','blocked','done','unknown'].includes(runtimeAgent.status)
              || (runtimeAgent.task_id != null && !tasksById.has(runtimeAgent.task_id))) throw new Error('invalid');
            const matches = row.tasks.filter(task => task.agent_id === runtimeAgent.agent_id
              && ['pending', 'ready', 'running', 'blocked', 'review'].includes(task.state));
            if (runtimeAgent.task_id != null && (matches.length !== 1
              || matches[0].task_id !== runtimeAgent.task_id)) throw new Error('invalid');
            runtimeIds.add(runtimeAgent.agent_id);
          }
          const agentIds = new Set(), agentTaskIds = new Set();
          for (const agent of row.agents) {
            if (!agent || typeof agent.agent_id !== 'string' || agentIds.has(agent.agent_id)
              || typeof agent.task_id !== 'string' || agentTaskIds.has(agent.task_id)
              || agent.state !== 'running'
              || (agent.parent_task_id != null && typeof agent.parent_task_id !== 'string')
              || (agent.parent_agent_id != null && typeof agent.parent_agent_id !== 'string')
              || !Number.isSafeInteger(agent.fencing_token) || agent.fencing_token < 0) throw new Error('invalid');
            const task = tasksById.get(agent.task_id);
            if (!task || task.state !== 'running' || task.agent_id !== agent.agent_id
              || task.parent_task_id !== agent.parent_task_id
              || task.parent_agent_id !== agent.parent_agent_id
              || task.fencing_token !== agent.fencing_token) throw new Error('invalid');
            agentIds.add(agent.agent_id); agentTaskIds.add(agent.task_id);
          }
          const expectedAgentTasks = new Set(row.tasks.filter(task => task.state === 'running' && task.agent_id != null).map(task => task.task_id));
          if (expectedAgentTasks.size !== agentTaskIds.size || [...expectedAgentTasks].some(taskId => !agentTaskIds.has(taskId))) throw new Error('invalid');
          for (const edge of row.edges) {
            if (!edge || !['parent', 'dependency'].includes(edge.kind)
              || typeof edge.from_task !== 'string' || typeof edge.to_task !== 'string'
              || !taskIds.has(edge.from_task) || !taskIds.has(edge.to_task)) throw new Error('invalid');
          }
        }
      }
      if (item.kind === 'release') {
        if (item.profile !== 'quantlab' || (item.status === 'available' && item.rows.length !== 1)) throw new Error('invalid');
        if (item.rows.some(row => typeof row.tag !== 'string' || !/^v[A-Za-z0-9._-]{1,62}$/.test(row.tag)
          || typeof row.commit !== 'string' || !/^[0-9a-f]{40}$/.test(row.commit)
          || typeof row.config_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(row.config_sha256)
          || !Number.isSafeInteger(row.deployed_at) || row.deployed_at < 0)) throw new Error('invalid');
      }
      if (item.kind === 'codex') {
        if (item.profile !== 'majak' || (item.status === 'available' && item.rows.length !== 1)) throw new Error('invalid');
        if (item.rows.some(row => !Number.isFinite(row.used_percent) || row.used_percent < 0 || row.used_percent > 100
          || !Array.isArray(row.daily) || !Array.isArray(row.limit_history)
          || !['available', 'unavailable'].includes(row.routing_status))) throw new Error('invalid');
        for (const row of item.rows) {
          if (row.routing_status !== 'available') continue;
          const routingNumbers = ['routing_observed_at', 'routing_soft_limit_pct', 'routing_hard_limit_pct',
            'routing_decisions', 'routing_free', 'routing_sol', 'routing_astra', 'routing_astra_escalations', 'routing_premium_denied'];
          if (typeof row.routing_policy_version !== 'string' || row.routing_policy_version.length > 64
            || routingNumbers.some(key => !Number.isSafeInteger(row[key]) || row[key] < 0)
            || row.routing_soft_limit_pct >= row.routing_hard_limit_pct || row.routing_hard_limit_pct > 100
            || row.routing_free + row.routing_sol + row.routing_astra > row.routing_decisions
            || row.routing_astra_escalations > row.routing_astra
            || (row.last_route_at != null && !Number.isFinite(row.last_route_at))
            || (row.last_route_tier != null && !['free', 'sol', 'astra'].includes(row.last_route_tier))
            || (row.last_route_model != null && typeof row.last_route_model !== 'string')
            || (row.last_route_reason != null && typeof row.last_route_reason !== 'string')) throw new Error('invalid');
        }
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
  document.querySelectorAll('[data-task-filter]').forEach(button => button.addEventListener('click', () => { taskFilter = button.dataset.taskFilter || 'all'; renderTaskGraph(); }));
  $('#demo-toggle').addEventListener('click', event => {
    demo = !demo; document.documentElement.dataset.mode = demo ? 'demo' : 'live';
    event.currentTarget.setAttribute('aria-pressed', String(demo)); event.currentTarget.textContent = demo ? 'Ukončit demo' : 'Demo režim'; ui.demo.hidden = !demo;
    if (demo) { demoState = 'idle'; ui.demoStates.querySelectorAll('button').forEach(button => { const active = button.dataset.demoState === 'idle'; button.classList.toggle('is-active', active); button.setAttribute('aria-pressed', String(active)); }); }
    updateHeader(); renderProjects(); renderFace(); if (!ui.detail.hidden) renderDetail(); if (!demo) refresh(true);
  });
  $('#demo-panel > div:first-child > span').textContent = 'Pouze animace jsou syntetické. Metriky jsou pouze z production snapshotu; bez něj zůstávají nedostupné.';
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
    const blocked = blockedAgents()[0]; if (blocked) openBlockedAgent(blocked); else applyView('work');
  });
  document.querySelectorAll('[data-project-toggle]').forEach(button => button.addEventListener('click', () => {
    const list = button.closest('.project').querySelector('.agent-list'), expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded)); list.hidden = expanded; renderProjects();
  }));
  document.addEventListener('visibilitychange', () => { sceneCall('setActive', !document.hidden && view === 'film'); if (!document.hidden) refresh(true); });
  sceneCall('onSelect', openDetail); sceneCall('onTaskSelect', openTaskDetail); updateMotion(); applyView(sceneFailed ? 'work' : 'film'); renderAll(); refresh(true);
  setInterval(refresh, 30000);
  setInterval(() => {
    if (document.hidden) return;
    if (liveData && Date.now() / 1000 - liveData.generated_at > 90) { liveData = null; loadReason = 'Snapshot je starší než 90 s · obnovte data'; renderAll(); }
    else { renderTelemetry(); updateHeader(); if (!ui.detail.hidden) renderDetail(); }
  }, 1000);
  return Object.freeze({ diagnostics: () => ({ view, mode: demo ? 'demo' : 'live', state: effectiveState(), reduced, selectedAgent, selectedTask, sceneAvailable: Boolean(scene) && !sceneFailed, freshSnapshot: Boolean(liveData), agentCount: agents().length, queueActive: activeQueueTasks().length }) });
}
