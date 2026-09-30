/* Contract tests, not a visual/browser acceptance test. Run: node --test dashboard-ui.test.js */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const STATES = ['idle', 'receiving', 'working', 'tool', 'delegating', 'waiting_result', 'waiting_user', 'speaking', 'complete', 'error', 'offline'];
const source = readFileSync(join(__dirname, 'dashboard-ui.js'), 'utf8');
const modulePromise = import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

function fixture() {
  const now = Math.floor(Date.now() / 1000);
  const sources = ['majak', 'quantlab'].flatMap(profile => [
    { profile, kind: 'herdr', status: 'available', reason: 'ok', observed_at: now,
      rows: [{ agent: `${profile}-hermes`, status: 'done' }, { agent: `${profile}-codex`, status: 'idle' }] },
    { profile, kind: 'router', status: 'available', reason: 'ok', data_at: now,
      rows: [{ task_id: null, requests: 1, input_tokens: null, output_tokens: 12, cost_microusd: null,
        actual_model: '<img src=x onerror=alert(1)>', provider: 'openai-codex',
        fallback_count: 0, successful_requests: 1, duration_ms: 100, last_used_at: now }] },
  ]);
  sources.push(
    { profile: 'majak', kind: 'search', status: 'available', reason: 'ok', observed_at: now, data_at: now,
      rows: [{ route_mode: 'fast', provider: 'exa-keyless', fallback_provider: 'exa-keyless', searches: 2,
        successful_searches: 2, duration_ms: 200, max_duration_ms: 120, fallback_count: 1,
        cost_microusd: 0, result_count: 10, extract_count: 0, last_used_at: now },
      { route_mode: 'fast', provider: 'nous-managed', fallback_provider: null, searches: 1,
        successful_searches: 1, duration_ms: 90, max_duration_ms: 90, fallback_count: 0,
        cost_microusd: null, result_count: 4, extract_count: 0, last_used_at: now - 60 }] },
    { profile: 'quantlab', kind: 'search', status: 'available', reason: 'ok', observed_at: now, data_at: now,
      rows: [{ route_mode: 'deep', provider: 'nous-managed', fallback_provider: null, searches: 1,
        successful_searches: 1, duration_ms: 300, max_duration_ms: 300, fallback_count: 0,
        cost_microusd: null, result_count: 8, extract_count: 3, last_used_at: now }] },
  );
  sources.push({
    profile: 'majak', kind: 'queue', status: 'unavailable', reason: 'not_configured', observed_at: now, data_at: null,
    rows: [],
  });
  sources.push({
    profile: 'quantlab', kind: 'queue', status: 'available', reason: 'ok', observed_at: now, data_at: now,
    rows: [{ task_id: 'issue190-prepare-20260926', issue: 190,
      issue_title: 'Cílová architektura runtime', issue_open: true, scheduler_state: 'active',
      status: 'pending', attempts: 0, max_attempts: 8, not_before: now + 3600, updated_at: now,
      agent: 'quantlab-hermes', kind: 'scheduled_acceptance', blocker: null, pr_number: 240 }],
  });
  sources.push({
    profile: 'quantlab', kind: 'admission', status: 'available', reason: 'ok', observed_at: now, data_at: now,
    rows: [
      { event: 'allow', reason: null, role: 'reader', repo: 'Bbambaaamm/herdr', issue: '3',
        node_count: 3, max_depth: 2, max_fanout: 2, child_tools_count: 0, agents_after: 2, observed_at: now - 2 },
      { event: 'deny', reason: 'global_agent_limit', role: 'reader', repo: 'Bbambaaamm/herdr', issue: '3',
        node_count: 3, max_depth: 2, max_fanout: 2, child_tools_count: 0, agents_after: null, observed_at: now - 1 },
    ],
  });
  sources.push({
    profile: 'quantlab', kind: 'release', status: 'available', reason: 'ok', observed_at: now, data_at: now,
    rows: [{ tag: 'v0.2.0-rc.2', commit: 'a'.repeat(40), config_sha256: 'b'.repeat(64), deployed_at: now }],
  });
  sources.push({
    profile: 'majak', kind: 'codex', status: 'available', reason: 'ok', observed_at: now, data_at: now,
    rows: [{
      used_percent: 82, window_minutes: 10080, resets_at: now + 3600, ordinary_usage_allowed: true,
      has_credits: false, credits_unlimited: false, credits_balance: '0', reset_credits_available: 0,
      lifetime_tokens: 123456789, peak_daily_tokens: 9000000, longest_running_turn_sec: 1200,
      current_streak_days: 7, longest_streak_days: 9,
      daily: [{ day: '2026-09-24', tokens: 1000 }, { day: '2026-09-25', tokens: 2000 }],
      limit_history: [{ at: now - 300, used_percent: 80 }, { at: now, used_percent: 82 }],
      routing_status: 'available', routing_policy_version: 'cost-aware-v1.0', routing_observed_at: now,
      routing_soft_limit_pct: 70, routing_hard_limit_pct: 90, routing_decisions: 7,
      routing_free: 5, routing_sol: 2, routing_astra: 0, routing_astra_escalations: 0,
      routing_premium_denied: 0, last_route_at: now, last_route_tier: 'sol',
      last_route_model: 'gpt-6-sol', last_route_reason: 'cheap_attempts_exhausted',
    }],
  });
  return { generated_at: now, sources };
}

async function harness(t, options = {}) {
  const globals = ['document', 'matchMedia', 'CSS', 'setInterval', 'fetch'];
  const saved = Object.fromEntries(globals.map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
  t.after(() => {
    for (const key of globals) {
      if (saved[key]) Object.defineProperty(globalThis, key, saved[key]); else delete globalThis[key];
    }
  });
  const elements = new Map(), documentEvents = new Map(), intervals = [], mediaEvents = new Map(), overflowNodes = new Map();
  let activeElement = null, nodeSequence = 0;
  class Element {
    constructor(selector) {
      this.selector = selector; this.dataset = {}; this.style = {}; this.attrs = {}; this.events = new Map();
      this.children = []; this.hidden = ['#agent-detail', '#demo-panel', '#drawer-backdrop', '#webgl-fallback'].includes(selector);
      this.isConnected = true; this.textContent = ''; this.innerHTML = '';
      this.classList = { toggle() {} };
    }
    setAttribute(key, value) { this.attrs[key] = String(value); }
    getAttribute(key) { return this.attrs[key]; }
    removeAttribute(key) { delete this.attrs[key]; }
    addEventListener(type, callback) {
      this.events.set(type, [...(this.events.get(type) || []), callback]);
    }
    emit(type, details = {}) {
      const event = { currentTarget: this, target: this, preventDefault() { this.defaultPrevented = true; }, ...details };
      for (const callback of this.events.get(type) || []) callback(event);
      return event;
    }
    querySelectorAll(selector) {
      if (selector === 'button' && this.selector === '#demo-states') return this.children.filter(child => child instanceof Element);
      if (selector.startsWith('button:not(') && this.selector === '#agent-detail') return [get('#detail-close')];
      if (selector === '[data-overflow-profile]' && this.selector === '#film-view') {
        return ['majak', 'quantlab'].flatMap(profile => {
          if (!get(`#${profile}-agents`).innerHTML.includes(`data-overflow-profile="${profile}"`)) return [];
          if (!overflowNodes.has(profile)) {
            const button = new Element(`#overflow-${profile}`); button.dataset.overflowProfile = profile; overflowNodes.set(profile, button);
          }
          return [overflowNodes.get(profile)];
        });
      }
      return [];
    }
    querySelector(selector) { return get(selector); }
    closest(selector) { return selector === '.project' ? this.project : null; }
    replaceChildren(...children) { this.children = children; }
    append(...children) { this.children.push(...children); }
    insertAdjacentHTML(position, html) {
      this.innerHTML = position === 'beforeend' ? this.innerHTML + html : html + this.innerHTML;
    }
    focus() { activeElement = this; }
  }
  function get(selector) {
    if (!elements.has(selector)) elements.set(selector, new Element(selector));
    return elements.get(selector);
  }
  const viewButtons = ['film', 'work'].map(view => { const node = get(`#view-${view}`); node.dataset.view = view; return node; });
  const taskFilterButtons = ['all', 'running', 'pending', 'blocked', 'done'].map(filter => {
    const node = get(`#task-filter-${filter}`); node.dataset.taskFilter = filter; node.attrs['aria-pressed'] = String(filter === 'all'); return node;
  });
  const projectButtons = ['majak', 'quantlab'].map(profile => {
    const node = get(`#${profile}-title`); node.dataset.projectToggle = profile; node.attrs['aria-expanded'] = 'true';
    node.project = { querySelector: () => get(`#${profile}-agents`) }; return node;
  });
  globalThis.document = {
    hidden: false, body: { style: {} }, documentElement: { dataset: {} },
    get activeElement() { return activeElement; }, querySelector: get,
    querySelectorAll(selector) {
      return selector === '[data-view]' ? viewButtons
        : selector === '[data-project-toggle]' ? projectButtons
          : selector === '[data-task-filter]' ? taskFilterButtons : [];
    },
    createElement(type) { return new Element(`${type}-${++nodeSequence}`); },
    addEventListener(type, callback) { documentEvents.set(type, callback); },
  };
  globalThis.matchMedia = () => ({ matches: Boolean(options.reduced), addEventListener: (type, callback) => mediaEvents.set(type, callback) });
  globalThis.CSS = { escape: value => value };
  globalThis.setInterval = callback => { intervals.push(callback); return intervals.length; };
  let snapshot = fixture(), httpStatus = 200;
  globalThis.fetch = async () => ({ ok: httpStatus === 200, status: httpStatus, json: async () => structuredClone(snapshot) });
  const calls = { states: [], agents: [], tasks: [], demo: [], reduced: [], active: [], focused: [], focusedTasks: [], activity: [] };
  const scene = {
    setState: value => calls.states.push(value), setDemo: value => calls.demo.push(value),
    setAgents: value => calls.agents.push(value), setTasks: value => calls.tasks.push(value),
    setReduced: value => calls.reduced.push(value), setActivity: value => calls.activity.push(value),
    setActive: value => calls.active.push(value), focusAgent: value => calls.focused.push(value), focusTask: value => calls.focusedTasks.push(value),
    onSelect: callback => { calls.select = callback; }, onTaskSelect: callback => { calls.selectTask = callback; },
  };
  const { mountDashboard } = await modulePromise;
  const ui = mountDashboard(options.factory || (() => scene));
  await new Promise(resolve => setImmediate(resolve));
  return {
    ui, get, calls, viewButtons, taskFilterButtons, projectButtons, mediaEvents,
    snapshot: () => snapshot, setSnapshot: value => { snapshot = value; }, setHTTP: value => { httpStatus = value; },
    refresh: () => intervals[0](), tickAge: () => intervals[1](),
    click: selector => get(selector).emit('click'), documentEvents,
  };
}

test('partial telemetry stays explicit, Codex allowance is live, and snapshot values cannot inject HTML', async t => {
  const h = await harness(t);
  assert.equal(h.ui.diagnostics().freshSnapshot, true);
  assert.match(h.get('#header-status').textContent, /v0\.2\.0-rc\.2 @ a{12}/);
  assert.equal(h.get('#cost-total').textContent, '18 %');
  assert.match(h.get('#project-grid').innerHTML, /0 \/ 12 · 0 % req/);
  assert.match(h.get('#project-grid').innerHTML, /0 USD známé \+ 1 bez ceny/);
  assert.match(h.get('#observability-kpis').innerHTML, /123,5|123\.5|123/);
  assert.match(h.get('#observability-grid').innerHTML, /Codex tokeny po dnech/);
  assert.match(h.get('#observability-grid').innerHTML, /Cost-aware router/);
  assert.match(h.get('#observability-grid').innerHTML, /FREE/);
  assert.match(h.get('#observability-grid').innerHTML, /Sol/);
  assert.match(h.get('#observability-grid').innerHTML, /Astra eskalace: 0/);
  assert.match(h.get('#observability-grid').innerHTML, /Router soft 70 % \/ hard 90 %/);
  assert.match(h.get('#observability-grid').innerHTML, /Model tokeny/);
  assert.match(h.get('#observability-grid').innerHTML, /Fallback pressure/);
  assert.match(h.get('#project-grid').innerHTML, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(h.get('#project-grid').innerHTML, /<img src=x/);
  assert.equal(h.calls.agents.at(-1).length, 4);
  assert.equal(h.get('#link-layer').children.length, 0, 'live status must not fabricate communication links');
});

test('search layer shows bounded real telemetry without query text', async t => {
  const h = await harness(t);
  assert.equal(h.get('#search-count').textContent, '4');
  assert.equal(h.get('#search-latency').textContent, '148 ms');
  const html = h.get('#search-grid').innerHTML;
  assert.match(html, /MAJÁK|MAJAK/);
  assert.match(html, /exa-keyless/);
  assert.match(html, /nous-managed/);
  assert.match(html, /Aktuální provider \(poslední běh\):<\/span> exa-keyless/);
  assert.match(html, /Historické providery:<\/span> nous-managed/);
  assert.match(html, /FAST/);
  assert.match(html, /DEEP/);
  assert.match(html, /1 fallback|Fallbacky/);
  assert.doesNotMatch(html, /query_hash|official OpenAI|prompt/i);
});

test('model and search provider history cannot replace the most recent provider', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const router = h.snapshot().sources.find(item => item.profile === 'majak' && item.kind === 'router');
  router.rows.push({ ...router.rows[0], provider: 'legacy-provider', actual_model: 'legacy-model', last_used_at: now - 300 });
  await h.refresh();
  assert.match(h.get('#project-grid').innerHTML, /Aktuální provider \(poslední běh\): openai-codex/);
  assert.match(h.get('#project-grid').innerHTML, /Historické providery: legacy-provider/);
  h.calls.select('majak-codex');
  const detail = h.get('#detail-metrics').innerHTML;
  assert.match(detail, /Aktuální model provider[^]*openai-codex/);
  assert.match(detail, /Historické model providery[^]*legacy-provider/);
  assert.doesNotMatch(detail, /Aktuální model provider[^]*legacy-provider[^]*Historické model providery/);
});

test('provider recency is mandatory in the browser trust boundary', async t => {
  const h = await harness(t);
  const router = h.snapshot().sources.find(item => item.kind === 'router');
  delete router.rows[0].last_used_at;
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.equal(h.ui.diagnostics().state, 'offline');
});

test('release identity is mandatory and sanitized in the browser trust boundary', async t => {
  const h = await harness(t);
  const release = h.snapshot().sources.find(item => item.kind === 'release');
  release.rows[0].commit = '<script>alert(1)</script>';
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.doesNotMatch(h.get('#header-status').textContent, /script|alert/i);
});

test('durable QuantLab queue renders safe metadata and drives coordinator state', async t => {
  const h = await harness(t);
  assert.equal(h.get('#queue-count').textContent, 'Nedostupné');
  assert.equal(h.ui.diagnostics().queueActive, 1);
  assert.match(h.get('#queue-list').innerHTML, /issue190-prepare-20260926/);
  assert.match(h.get('#queue-list').innerHTML, /#190/);
  assert.match(h.get('#queue-list').innerHTML, /scheduled_acceptance/);
  assert.match(h.get('#coordinator-next').textContent, /issue190-prepare-20260926/);
  assert.equal(h.get('#coordinator-current').textContent, 'Žádná');
  assert.doesNotMatch(h.get('#queue-list').innerHTML, /prompt|PRIVATE|tool_args|log/i);

  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  queue.rows[0].status = 'running';
  queue.rows[0].attempts = 1;
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'working');
  assert.equal(h.get('#queue-count').textContent, 'Nedostupné');
  assert.match(h.get('#face-task').textContent, /#190/);
  assert.match(h.get('#face-task').textContent, /issue190-prepare-20260926/);
  assert.match(h.get('#coordinator-current').textContent, /issue190-prepare-20260926/);
  assert.equal(h.get('#coordinator-next').textContent, 'Žádná');
  assert.equal(h.calls.activity.at(-1).activeAgent, 'quantlab-hermes');
  assert.equal(h.calls.activity.at(-1).running, 1);
  assert.equal(h.get('#quantlab-project-state').textContent, 'pracuje');

  h.calls.select('quantlab-hermes');
  assert.match(h.get('#detail-metrics').innerHTML, /issue190-prepare-20260926/);
  assert.match(h.get('#detail-metrics').innerHTML, /Cílová architektura runtime/);
  assert.match(h.get('#detail-metrics').innerHTML, /1 \/ 8/);
  assert.match(h.get('#detail-metrics').innerHTML, /scheduler active/);
  assert.match(h.get('#detail-metrics').innerHTML, /#240/);
  assert.match(h.get('#detail-links').innerHTML, /issues\/190/);
  assert.match(h.get('#detail-links').innerHTML, /pull\/240/);
  assert.match(h.get('#detail-events').innerHTML, /Durable queue/);
  assert.match(h.get('#detail-events').innerHTML, /Runtime, branch\/SHA, test a reviewer data/);
  assert.doesNotMatch(h.get('#detail-events').innerHTML, /PRIVATE|tool_args|secret payload|raw log/i);
});

test('blocked queue task raises attention with sanitized blocker only', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  queue.rows[0].status = 'blocked';
  queue.rows[0].blocker = 'github_write_auth_required';
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'waiting_user');
  assert.match(h.get('#attention-summary').textContent, /issue190-prepare-20260926/);
  assert.match(h.get('#queue-list').innerHTML, /github_write_auth_required/);
  assert.doesNotMatch(h.get('#queue-list').innerHTML, /PRIVATE|secret|prompt/i);
});

test('technical queue blocker does not masquerade as user intervention', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  queue.rows[0].status = 'blocked';
  queue.rows[0].blocker = 'soak_evidence_pending';
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'waiting_result');
  assert.equal(h.get('#attention-summary').hidden, true);
  assert.match(h.get('#face-task').textContent, /technické závislosti/i);
  assert.match(h.get('#queue-list').innerHTML, /soak_evidence_pending/);
});

test('queue v2 browser contract rejects incomplete task metadata', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  delete queue.rows[0].max_attempts;
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.equal(h.ui.diagnostics().state, 'offline');
});

test('Majak durable queue is accepted, visible, and bound to dotacni-majak-hermes', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'majak');
  queue.status = 'available'; queue.reason = 'ok'; queue.data_at = now;
  queue.rows = [{
    task_id: 'github-majak-issue-662-test',
    repo: 'Bbambaaamm/dotacni-majak',
    issue: 662,
    issue_title: 'HERDR CONTROL · Dotační maják completion program',
    issue_open: true,
    scheduler_state: 'active',
    status: 'running',
    attempts: 1,
    max_attempts: 4,
    not_before: null,
    updated_at: now,
    agent: 'dotacni-majak-hermes',
    kind: 'github_root_orchestration',
    blocker: null,
    pr_number: null,
  }];
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, true);
  assert.equal(h.ui.diagnostics().queueActive, 2);
  assert.match(h.get('#queue-list').innerHTML, /github-majak-issue-662-test/);
  assert.match(h.get('#queue-list').innerHTML, /#662/);
  assert.match(h.get('#face-task').textContent, /Maják #662/);
  h.calls.select('majak-hermes');
  assert.match(h.get('#detail-metrics').innerHTML, /github-majak-issue-662-test/);
  assert.match(h.get('#detail-links').innerHTML, /dotacni-majak\/issues\/662/);
});

test('single-profile authorized snapshot reports its available queue as complete', async t => {
  const h = await harness(t);
  h.setSnapshot({
    ...h.snapshot(),
    sources: h.snapshot().sources.filter(item => item.profile === 'quantlab'),
  });
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, true);
  assert.equal(h.get('#queue-count').textContent, '1');
});

test('running queue task outranks retained blocked or failed rows across profiles', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const majak = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'majak');
  majak.status = 'available'; majak.reason = 'ok'; majak.data_at = now;
  majak.rows = [{
    task_id: 'majak-retained-failure',
    repo: 'Bbambaaamm/dotacni-majak',
    issue: 662,
    issue_title: 'retained failure',
    issue_open: true,
    scheduler_state: 'active',
    status: 'failed',
    attempts: 4,
    max_attempts: 4,
    not_before: null,
    updated_at: now + 100,
    agent: 'dotacni-majak-hermes',
    kind: 'github_root_orchestration',
    blocker: 'provider_startup_failed',
    pr_number: null,
  }];
  const quant = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  quant.rows[0].status = 'running';
  quant.rows[0].updated_at = now;
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'working');
  assert.match(h.get('#face-task').textContent, /QuantLab #190/);
  assert.match(h.get('#coordinator-current').textContent, /issue190-prepare-20260926/);
  assert.equal(h.calls.activity.at(-1).activeAgent, 'quantlab-hermes');
});

test('queue headline is unavailable when only one consumer projection is available', async t => {
  const h = await harness(t);
  assert.equal(h.get('#queue-count').textContent, 'Nedostupné');
  const majak = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'majak');
  const now = Math.floor(Date.now() / 1000);
  majak.status = 'available'; majak.reason = 'ok'; majak.data_at = now;
  majak.rows = [];
  await h.refresh();
  assert.equal(h.get('#queue-count').textContent, '1');
});

test('Majak queue rejects wrong repo or coordinator identity', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'majak');
  queue.status = 'available'; queue.reason = 'ok'; queue.data_at = now;
  queue.rows = [{
    task_id: 'bad-majak-task',
    repo: 'Bbambaaamm/Autonomous-Quant-Lab',
    issue: 662,
    issue_title: 'bad',
    issue_open: true,
    scheduler_state: 'active',
    status: 'running',
    attempts: 0,
    max_attempts: 4,
    not_before: null,
    updated_at: now,
    agent: 'quantlab-hermes',
    kind: 'github_root_orchestration',
    blocker: null,
    pr_number: null,
  }];
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.equal(h.ui.diagnostics().state, 'offline');
});

test('both views preserve selected agent and detail follows new live status', async t => {
  const h = await harness(t);
  h.calls.select('majak-codex');
  assert.equal(h.get('#agent-detail').hidden, false);
  assert.equal(h.ui.diagnostics().selectedAgent, 'majak-codex');
  h.viewButtons[1].emit('click');
  assert.equal(h.ui.diagnostics().view, 'work');
  assert.equal(h.get('#film-view').hidden, true);
  assert.equal(h.get('#work-view').hidden, false);
  h.viewButtons[0].emit('click');
  assert.equal(h.ui.diagnostics().view, 'film');
  assert.equal(h.ui.diagnostics().selectedAgent, 'majak-codex');
  h.snapshot().sources[0].rows[1].status = 'blocked';
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'waiting_user');
  assert.match(h.get('#detail-status').textContent, /Blokováno/);
  assert.equal(h.get('#attention-action').hidden, false);
  assert.equal(h.calls.focused.at(-1), 'majak-codex');
});

test('all eleven demo states are explicit and target a valid machine without changing live data', async t => {
  const h = await harness(t);
  const original = structuredClone(h.snapshot());
  h.click('#demo-toggle');
  assert.equal(h.ui.diagnostics().mode, 'demo');
  assert.match(h.get('#header-status').textContent, /DEMO/);
  const buttons = h.get('#demo-states').children;
  assert.deepEqual(buttons.map(button => button.dataset.demoState), STATES);
  for (const button of buttons) {
    button.emit('click');
    assert.equal(h.ui.diagnostics().state, button.dataset.demoState);
    assert.equal(h.calls.demo.at(-1).enabled, true);
    assert.equal(h.calls.demo.at(-1).target, 'majak-codex');
    assert.match(h.get('#face-task').textContent, /^DEMO/);
    assert.match(h.get('#majak-agents').innerHTML, /Ukázkový stroj · syntetický/);
    assert.match(h.get('#majak-agents').innerHTML, /DEMO · Čeká/);
    assert(h.get('#majak-agents').innerHTML.includes(`data-agent="majak-codex" data-state="${button.dataset.demoState}"`));
    assert.doesNotMatch(h.get('#project-grid').innerHTML, /DEMO/);
  }
  assert.deepEqual(h.snapshot(), original);
  assert.equal(h.get('#request-count').textContent, '2');
  h.click('#demo-toggle');
  assert.equal(h.ui.diagnostics().mode, 'live');
  assert.equal(h.calls.demo.at(-1).enabled, false);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.ui.diagnostics().state, 'complete');
  assert.doesNotMatch(h.get('#majak-agents').innerHTML, /DEMO/);
});

test('demo focus changes synthetic film target without changing actual detail or work states', async t => {
  const h = await harness(t);
  const original = structuredClone(h.snapshot());
  h.click('#demo-toggle');
  h.get('#demo-states').children.find(button => button.dataset.demoState === 'working').emit('click');
  h.calls.select('quantlab-codex');
  assert.equal(h.calls.demo.at(-1).target, 'quantlab-codex');
  assert.match(h.get('#quantlab-agents').innerHTML, /data-agent="quantlab-codex" data-state="working"/);
  assert.match(h.get('#quantlab-agents').innerHTML, /DEMO · Zpracovává úlohu/);
  assert.match(h.get('#majak-agents').innerHTML, /data-agent="majak-codex" data-state="idle"/);
  assert.match(h.get('#detail-status').textContent, /Živý stav: Čeká/);
  assert.doesNotMatch(h.get('#project-grid').innerHTML, /DEMO/);
  assert.deepEqual(h.snapshot(), original);
});

test('completion effect is emitted once per state transition rather than on every poll', async t => {
  const h = await harness(t);
  assert.equal(h.calls.states.filter(state => state === 'complete').length, 1);
  await h.refresh(); await h.refresh();
  assert.equal(h.calls.states.filter(state => state === 'complete').length, 1);
});

test('stale or failed live data clears metrics and drawer instead of looking active', async t => {
  const h = await harness(t);
  h.calls.select('majak-codex');
  h.snapshot().generated_at = Math.floor(Date.now() / 1000) - 100;
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.equal(h.ui.diagnostics().state, 'offline');
  assert.equal(h.get('#agent-count').textContent, 'Neznámé');
  assert.equal(h.get('#cost-total').textContent, 'Nedostupné');
  assert.match(h.get('#work-freshness').textContent, /90 s/);
  assert.match(h.get('#detail-status').textContent, /Odpojeno/);
  assert.equal(h.get('#attention-action').textContent, 'Obnovit data');
  h.setHTTP(503); await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'offline');
  assert.match(h.get('#work-freshness').textContent, /připojení/);
});

test('snapshot freshness expires between fetches', async t => {
  const h = await harness(t);
  const originalNow = Date.now;
  t.after(() => { Date.now = originalNow; });
  Date.now = () => originalNow() + 91000;
  h.tickAge();
  assert.equal(h.ui.diagnostics().state, 'offline');
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
});

test('WebGL initialization failure leaves live working/text view usable', async t => {
  const h = await harness(t, { factory: () => { throw new Error('WebGL unavailable'); } });
  assert.equal(h.ui.diagnostics().sceneAvailable, false);
  assert.equal(h.ui.diagnostics().view, 'work');
  assert.equal(h.get('#work-view').hidden, false);
  assert.equal(h.get('#webgl-fallback').hidden, false);
  assert.equal(h.ui.diagnostics().freshSnapshot, true);
  assert.match(h.get('#project-grid').innerHTML, /majak-codex/);
});

for (const eventName of ['webglcontextlost', 'scene-unavailable']) {
  test(`${eventName} switches to usable text view without losing selection`, async t => {
    const h = await harness(t);
    h.calls.select('quantlab-codex');
    h.get('#machine-scene').emit(eventName);
    assert.equal(h.ui.diagnostics().sceneAvailable, false);
    assert.equal(h.ui.diagnostics().view, 'work');
    assert.equal(h.ui.diagnostics().selectedAgent, 'quantlab-codex');
    assert.equal(h.get('#work-view').hidden, false);
    assert.equal(h.get('#webgl-fallback').hidden, false);
    assert.equal(h.ui.diagnostics().freshSnapshot, true);
  });
}

test('reduced motion and inactive tab are forwarded explicitly to the renderer', async t => {
  const h = await harness(t, { reduced: true });
  assert.equal(h.ui.diagnostics().reduced, true);
  assert.equal(h.calls.reduced.at(-1), true);
  assert.equal(h.get('#motion-toggle').attrs['aria-pressed'], 'true');
  assert.equal(h.get('#face-signal').style.boxShadow, 'none');
  h.click('#motion-toggle');
  assert.equal(h.calls.reduced.at(-1), false);
  globalThis.document.hidden = true;
  h.documentEvents.get('visibilitychange')();
  assert.equal(h.calls.active.at(-1), false);
});

test('project collapsing preserves identities while marking corresponding scene machines hidden', async t => {
  const h = await harness(t);
  h.projectButtons[0].emit('click');
  assert.equal(h.get('#majak-agents').hidden, true);
  const rows = h.calls.agents.at(-1);
  assert.deepEqual(rows.filter(row => row.profile === 'majak').map(row => row.visible), [false, false]);
  assert.deepEqual(rows.filter(row => row.profile === 'quantlab').map(row => row.visible), [true, true]);
  assert.equal(rows.length, 4);
});

test('additional agents remain accessible without unprojected film labels or invented machine slots', async t => {
  const h = await harness(t);
  h.snapshot().sources[0].rows.push(
    { agent: 'majak-research-worker', status: 'working' },
    { agent: 'majak-review-worker', status: 'idle' },
  );
  h.snapshot().sources[2].rows.push({ agent: 'quantlab-test-worker', status: 'working' });
  await h.refresh();
  const majak = h.get('#majak-agents').innerHTML, quantlab = h.get('#quantlab-agents').innerHTML;
  assert.match(majak, /\+2 dalších agentů — pracovní přehled/);
  assert.match(quantlab, /\+1 dalších agentů — pracovní přehled/);
  assert.doesNotMatch(majak, /data-agent="majak-research-worker"/);
  assert.doesNotMatch(majak, /data-agent="majak-review-worker"/);
  assert.doesNotMatch(quantlab, /data-agent="quantlab-test-worker"/);
  assert.match(h.get('#project-grid').innerHTML, /data-agent="majak-research-worker"/);
  assert.match(h.get('#project-grid').innerHTML, /data-agent="quantlab-test-worker"/);
  assert.equal(h.get('#agent-count').textContent, '7');
  assert.equal(h.calls.agents.at(-1).length, 4);
  assert.match(h.get('#data-caveat').textContent, /Dalších 3 agentů/);
  const overflow = h.get('#film-view').querySelectorAll('[data-overflow-profile]');
  assert.equal(overflow.length, 2); overflow[0].emit('click');
  assert.equal(h.ui.diagnostics().view, 'work');
  h.calls.select('majak-research-worker');
  assert.equal(h.ui.diagnostics().selectedAgent, 'majak-research-worker');
  assert.match(h.get('#detail-status').textContent, /Pracuje/);
});

test('TaskGraph is explicit when dependency telemetry is unavailable', async t => {
  const h = await harness(t);
  const status = h.get('#taskgraph-status').textContent;
  assert.match(status, /Dependency telemetry/i);
  assert.match(h.get('#taskgraph-nodes').innerHTML, /issue190-prepare-20260926/);
  assert.doesNotMatch(h.get('#taskgraph-nodes').innerHTML, /dependency-edge|<svg/i);
  assert.equal(h.calls.tasks.at(-1).length, 1);
});

test('TaskGraph handles an empty queue without invented nodes', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  queue.rows = [];
  await h.refresh();
  assert.match(h.get('#taskgraph-nodes').innerHTML, /Durable queue je prázdná/);
  assert.deepEqual(h.calls.tasks.at(-1), []);
});

test('TaskGraph uses bounded LOD for more than twenty task records', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  const base = queue.rows[0];
  queue.rows = Array.from({ length: 25 }, (_, index) => ({
    ...base,
    task_id: `task-${String(index).padStart(2, '0')}`,
    issue: 300 + index,
    issue_title: `Task ${index}`,
    status: index === 0 ? 'running' : 'pending',
    updated_at: base.updated_at + index,
  }));
  await h.refresh();
  const html = h.get('#taskgraph-nodes').innerHTML;
  assert.match(html, /\+10 uzlů/);
  assert.match(html, /LOD cluster/);
  assert.equal(h.calls.tasks.at(-1).length, 25);
});

test('3D task selection synchronizes with task inspector state', async t => {
  const h = await harness(t);
  assert.equal(typeof h.calls.selectTask, 'function');
  h.calls.selectTask('issue190-prepare-20260926');
  assert.equal(h.ui.diagnostics().selectedTask, 'issue190-prepare-20260926');
  assert.equal(h.ui.diagnostics().selectedAgent, null);
  assert.match(h.get('#detail-title').textContent, /#190/);
  assert.match(h.get('#detail-metrics').innerHTML, /Dependency edges/);
  assert.match(h.get('#detail-events').innerHTML, /nejsou odhadovány/i);
});

test('Swarm KPI strip renders 10 cells from authoritative queue and router data', async t => {
  const h = await harness(t);
  const html = h.get('#swarm-kpis').innerHTML;
  assert.equal((html.match(/class="swarm-kpi"/g) || []).length, 10);
  assert.match(html, /<span>Active<\/span><b>0<\/b>/);
  assert.match(html, /<span>Running<\/span><b>0<\/b>/);
  assert.match(html, /<span>Waiting<\/span><b>1<\/b>/);
  assert.match(html, /<span>Blocked \/ Failed<\/span><b>0 \/ 0<\/b>/);
  assert.match(html, /<span>Queue<\/span><b>1<\/b>/);
  assert.match(html, /<span>Terminal success<\/span><b>—<\/b><small>0 done · 0 failed<\/small>/);
  assert.match(html, /<span>Retries<\/span><b>0<\/b>/);
  assert.match(html, /<span>Tokens<\/span><b>24<\/b>/);
  assert.match(html, /<span>Cost known<\/span><b>0 USD<\/b><small>2 req unknown<\/small>/);
});

test('Avg task stays explicitly unavailable when duration telemetry is missing', async t => {
  const h = await harness(t);
  const html = h.get('#swarm-kpis').innerHTML;
  assert.match(html, /<span>Avg task<\/span><b>\u2014<\/b><small>duration telemetry chybí<\/small>/);
  assert.doesNotMatch(html, /<span>Avg task<\/span><b>\d/);
});

test('Swarm analytics renders six cards with available or unavailable state', async t => {
  const h = await harness(t);
  const html = h.get('#swarm-analytics-grid').innerHTML;
  assert.equal((html.match(/class="swarm-card"/g) || []).length, 6);
  assert.match(html, /Throughput/);
  assert.match(html, /Queue depth/);
  assert.match(html, /Latency/);
  assert.match(html, /Tokens &/);
  assert.match(html, /Model mix/);
  assert.match(html, /Reliability/);
  assert.match(html, /100 ms/);
});

test('Stale snapshot clears swarm KPI strip and analytics to unavailable', async t => {
  const h = await harness(t);
  h.snapshot().generated_at = Math.floor(Date.now() / 1000) - 100;
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.match(h.get('#swarm-kpis').innerHTML, /telemetrie nedostupná/i);
  assert.match(h.get('#swarm-analytics-grid').innerHTML, /telemetrie není dostupná/i);
  assert.match(h.get('#taskgraph-status').textContent, /není dostupná/i);
  assert.deepEqual(h.calls.tasks.at(-1), []);
});

test('KPI Active tracks working agent count through live telemetry', async t => {
  const h = await harness(t);
  // Default fixture: 4 agents but none in 'working' status
  assert.match(h.get('#swarm-kpis').innerHTML, /<span>Active<\/span><b>0<\/b>/);
  const herdr = h.snapshot().sources.find(s => s.kind === 'herdr' && s.profile === 'quantlab');
  herdr.rows[0].status = 'working';
  await h.refresh();
  assert.match(h.get('#swarm-kpis').innerHTML, /<span>Active<\/span><b>1<\/b>/);
  assert.equal(h.calls.agents.at(-1).length, 4);
  assert.equal(h.calls.agents.at(-1).find(a => a.agent === 'quantlab-hermes').status, 'working');
});

test('TaskGraph task nodes carry aria-selected for keyboard/select sync', async t => {
  const h = await harness(t);
  const before = h.get('#taskgraph-nodes').innerHTML;
  assert.match(before, /role="option"/);
  assert.match(before, /aria-selected="false"/);
  assert.match(before, /data-task-id="issue190-prepare-20260926"/);
  h.calls.selectTask('issue190-prepare-20260926');
  const after = h.get('#taskgraph-nodes').innerHTML;
  assert.match(after, /aria-selected="true"/);
  assert.match(after, /data-task-id="issue190-prepare-20260926"/);
});


test('Retries KPI counts only attempts after the first try', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  queue.rows[0].attempts = 3;
  await h.refresh();
  assert.match(h.get('#swarm-kpis').innerHTML, /<span>Retries<\/span><b>2<\/b><small>opakované pokusy<\/small>/);
});

test('Blocked and failed stay semantically separate in KPI and analytics', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  const base = queue.rows[0];
  queue.rows = [
    { ...base, task_id: 'blocked-task', status: 'blocked', blocker: 'soak_evidence_pending' },
    { ...base, task_id: 'failed-task', status: 'failed', blocker: null },
  ];
  await h.refresh();
  assert.match(h.get('#swarm-kpis').innerHTML, /<span>Blocked \/ Failed<\/span><b>1 \/ 1<\/b>/);
  assert.match(h.get('#swarm-analytics-grid').innerHTML, /1 blocked · 1 failed/);
});

test('TaskGraph state filters do not invent or reorder hidden dependencies', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  const base = queue.rows[0];
  queue.rows = [
    { ...base, task_id: 'run-1', status: 'running' },
    { ...base, task_id: 'wait-1', status: 'pending' },
    { ...base, task_id: 'fail-1', status: 'failed' },
  ];
  await h.refresh();
  const blocked = h.taskFilterButtons.find(button => button.dataset.taskFilter === 'blocked');
  blocked.emit('click');
  assert.match(h.get('#taskgraph-nodes').innerHTML, /fail-1/);
  assert.doesNotMatch(h.get('#taskgraph-nodes').innerHTML, /run-1|wait-1/);
  assert.match(h.get('#taskgraph-status').textContent, /blocked \+ failed/);
  assert.equal(blocked.attrs['aria-pressed'], 'true');
});


test('stale telemetry source is technical data health, not a user-intervention banner', async t => {
  const h = await harness(t);
  const codex = h.snapshot().sources.find(item => item.kind === 'codex');
  codex.status = 'unavailable';
  codex.reason = 'stale';
  codex.rows = [];
  await h.refresh();
  assert.equal(h.get('#attention-summary').hidden, true);
  assert.doesNotMatch(h.get('#attention-summary').textContent, /stale/i);
  assert.match(h.get('#source-grid').innerHTML, /CODEX \/ ÚČET/);
  assert.match(h.get('#source-grid').innerHTML, /unavailable · stale/);
});


test('admission observability shows sanitized ALLOW/DENY reasons', async t => {
  const h = await harness(t);
  const html = h.get('#observability-grid').innerHTML;
  assert.match(html, /Swarm admission/);
  assert.match(html, /ALLOW: 1/);
  assert.match(html, /DENY: 1/);
  assert.match(html, /global_agent_limit/);
  assert.match(html, /Bbambaaamm\/herdr #3/);
  assert.doesNotMatch(html, /PRIVATE TOOL ARGUMENT|SECRET_TOOL_PAYLOAD|admit:denied_tool/);
});

test('admission browser contract rejects malformed deny rows', async t => {
  const h = await harness(t);
  const admission = h.snapshot().sources.find(item => item.kind === 'admission');
  admission.rows[1].reason = null;
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
});


test('authoritative swarm snapshot drives real DAG edges and child task lineage', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/herdr', issue: '7', paper_only: false, policy_profiles: ['default'],
      agents: [{
        agent_id: 'herdr-parent', task_id: 'parent', state: 'running',
        parent_task_id: null, parent_agent_id: null, fencing_token: 1,
      }],
      tasks: [
        {
          task_id: 'parent', parent_task_id: null, parent_agent_id: null,
          agent_id: 'herdr-parent', state: 'running', role: 'planner',
          model: 'model-a', fallback_model: 'model-b', attempt: 1, max_attempts: 2,
          blocker: null, fencing_token: 1, dependencies: [], result_sha: null,
        },
        {
          task_id: 'child', parent_task_id: 'parent', parent_agent_id: 'herdr-parent',
          agent_id: 'herdr-child', state: 'review', role: 'reviewer',
          model: 'model-a', fallback_model: 'model-b', attempt: 1, max_attempts: 2,
          blocker: null, fencing_token: 2, dependencies: [], result_sha: 'a'.repeat(64),
        },
      ],
      edges: [{ from_task: 'parent', to_task: 'child', kind: 'parent' }],
    }],
  });
  await h.refresh();
  assert.match(h.get('#taskgraph-status').textContent, /Autoritativní Herdr DAG · 1 hran/);
  assert.equal(h.ui.diagnostics().state, 'working');
  assert.match(h.get('#face-state').textContent, /Zpracovává úlohu/);
  assert.match(h.get('#face-task').textContent, /^Herdr #7/);
  assert.doesNotMatch(h.get('#taskgraph-status').textContent, /Dependency telemetry/i);
  const html = h.get('#taskgraph-nodes').innerHTML;
  assert.match(html, /data-edge-kind="parent"/);
  assert.match(html, /parent/);
  assert.match(html, /child/);
  const tasks = h.calls.tasks.at(-1);
  assert.equal(tasks.length, 2);
  const child = tasks.find(row => row.task_id === 'child');
  assert.equal(child.parent_task_id, 'parent');
  assert.equal(child.raw_state, 'review');
  assert.equal(child.status, 'running');
});

test('Majak root remains visible alongside authoritative QuantLab swarm tasks', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const majakQueue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'majak');
  majakQueue.status = 'available'; majakQueue.reason = 'ok'; majakQueue.data_at = now;
  majakQueue.rows = [{
    task_id: 'github-majak-issue-662-swarm-test',
    repo: 'Bbambaaamm/dotacni-majak',
    issue: 662,
    issue_title: 'HERDR CONTROL',
    issue_open: true,
    scheduler_state: 'active',
    status: 'running',
    attempts: 1,
    max_attempts: 4,
    not_before: null,
    updated_at: now,
    agent: 'dotacni-majak-hermes',
    kind: 'github_root_orchestration',
    blocker: null,
    pr_number: null,
  }];
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/herdr', issue: '7', paper_only: false, policy_profiles: ['default'],
      agents: [{
        agent_id: 'herdr-parent', task_id: 'parent', state: 'running',
        parent_task_id: null, parent_agent_id: null, fencing_token: 1,
      }],
      tasks: [
        {
          task_id: 'parent', parent_task_id: null, parent_agent_id: null,
          agent_id: 'herdr-parent', state: 'running', role: 'planner',
          model: 'model-a', fallback_model: null, attempt: 1, max_attempts: 2,
          blocker: null, fencing_token: 1, dependencies: [], result_sha: null,
        },
        {
          task_id: 'child', parent_task_id: 'parent', parent_agent_id: 'herdr-parent',
          agent_id: 'herdr-child', state: 'ready', role: 'worker',
          model: 'model-a', fallback_model: null, attempt: 0, max_attempts: 2,
          blocker: null, fencing_token: 2, dependencies: [], result_sha: null,
        },
      ],
      edges: [{ from_task: 'parent', to_task: 'child', kind: 'parent' }],
    }],
  });
  await h.refresh();
  const html = h.get('#taskgraph-nodes').innerHTML;
  assert.match(html, /github-majak-issue-662-swarm-test/);
  assert.match(html, /parent/);
  assert.match(html, /child/);
  assert.match(html, /data-edge-kind="parent"/);
  const tasks = h.calls.tasks.at(-1);
  assert.equal(tasks.length, 3);
  assert(tasks.some(row => row.task_id === 'github-majak-issue-662-swarm-test'));
  assert(tasks.some(row => row.task_id === 'parent'));
  assert(tasks.some(row => row.task_id === 'child'));
});

test('Majak working state remains globally visible with terminal or blocked swarm', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const majakHerdr = h.snapshot().sources.find(item => item.kind === 'herdr' && item.profile === 'majak');
  majakHerdr.rows[0].status = 'working';
  const majakQueue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'majak');
  majakQueue.status = 'available'; majakQueue.reason = 'ok'; majakQueue.data_at = now;
  majakQueue.rows = [{
    task_id: 'github-majak-issue-662-global-state',
    repo: 'Bbambaaamm/dotacni-majak',
    issue: 662,
    issue_title: 'HERDR CONTROL',
    issue_open: true,
    scheduler_state: 'active',
    status: 'running',
    attempts: 1,
    max_attempts: 4,
    not_before: null,
    updated_at: now,
    agent: 'dotacni-majak-hermes',
    kind: 'github_root_orchestration',
    blocker: null,
    pr_number: null,
  }];
  const task = {
    task_id: 'terminal-swarm', parent_task_id: null, parent_agent_id: null,
    agent_id: null, state: 'done', role: 'worker',
    model: 'model-a', fallback_model: null, attempt: 1, max_attempts: 2,
    blocker: null, fencing_token: 0, dependencies: [], result_sha: 'a'.repeat(64),
  };
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/herdr', issue: '48', paper_only: false,
      policy_profiles: ['default'], agents: [], tasks: [task], edges: [],
    }],
  });

  await h.refresh();
  assert.equal(h.calls.states.at(-1), 'working');
  assert.match(h.get('#face-task').textContent, /Maják #662/);

  task.state = 'blocked';
  task.blocker = 'test_failed';
  await h.refresh();
  assert.equal(h.calls.states.at(-1), 'working');
  assert.match(h.get('#face-task').textContent, /Maják #662/);
});

test('swarm does not mask Majak herdr source failure', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const majakHerdr = h.snapshot().sources.find(item => item.kind === 'herdr' && item.profile === 'majak');
  majakHerdr.status = 'unavailable';
  majakHerdr.reason = 'stale';
  majakHerdr.rows = [];
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/herdr', issue: '48', paper_only: false,
      policy_profiles: ['default'], agents: [], tasks: [{
        task_id: 'terminal-swarm', parent_task_id: null, parent_agent_id: null,
        agent_id: null, state: 'done', role: 'worker',
        model: 'model-a', fallback_model: null, attempt: 1, max_attempts: 2,
        blocker: null, fencing_token: 0, dependencies: [], result_sha: 'a'.repeat(64),
      }], edges: [],
    }],
  });
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'error');
  assert.match(h.get('#face-task').textContent, /majak\/herdr.*stale/i);
});

test('swarm active counts include concurrently working Majak agent', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const majakHerdr = h.snapshot().sources.find(item => item.kind === 'herdr' && item.profile === 'majak');
  majakHerdr.rows[0].status = 'working';
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/herdr', issue: '48', paper_only: false,
      policy_profiles: ['default'],
      agents: [{
        agent_id: 'herdr-parent', task_id: 'parent', state: 'running',
        parent_task_id: null, parent_agent_id: null, fencing_token: 1,
      }],
      tasks: [{
        task_id: 'parent', parent_task_id: null, parent_agent_id: null,
        agent_id: 'herdr-parent', state: 'running', role: 'planner',
        model: 'model-a', fallback_model: null, attempt: 1, max_attempts: 2,
        blocker: null, fencing_token: 1, dependencies: [], result_sha: null,
      }],
      edges: [],
    }],
  });
  await h.refresh();
  assert.match(h.get('#swarm-kpis').innerHTML, /<span>Active<\/span><b>2<\/b>/);
  assert.equal(h.calls.activity.at(-1).workingAgents, 2);
});

test('AQL user blocker outside selected swarm remains global attention', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  const quantQueue = h.snapshot().sources.find(item => item.kind === 'queue' && item.profile === 'quantlab');
  quantQueue.status = 'available';
  quantQueue.reason = 'ok';
  quantQueue.data_at = now;
  quantQueue.rows = [{
    task_id: 'aql-human-blocked',
    repo: 'Bbambaaamm/Autonomous-Quant-Lab',
    issue: 190,
    issue_title: 'Needs GitHub write',
    issue_open: true,
    scheduler_state: 'blocked',
    status: 'blocked',
    attempts: 1,
    max_attempts: 4,
    not_before: null,
    updated_at: now,
    agent: 'quantlab-hermes',
    kind: 'github_issue_slice',
    blocker: 'github_write_auth_required',
    pr_number: null,
  }];
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/herdr', issue: '48', paper_only: false,
      policy_profiles: ['default'],
      agents: [{
        agent_id: 'herdr-parent', task_id: 'parent', state: 'running',
        parent_task_id: null, parent_agent_id: null, fencing_token: 1,
      }],
      tasks: [{
        task_id: 'parent', parent_task_id: null, parent_agent_id: null,
        agent_id: 'herdr-parent', state: 'running', role: 'planner',
        model: 'model-a', fallback_model: null, attempt: 1, max_attempts: 2,
        blocker: null, fencing_token: 1, dependencies: [], result_sha: null,
      }],
      edges: [],
    }],
  });
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'waiting_user');
  assert.match(h.get('#face-task').textContent, /aql-human-blocked/);
  assert.equal(h.get('#attention-summary').hidden, false);
  assert.match(h.get('#attention-summary').textContent, /aql-human-blocked/);
});

test('observability active work uses authoritative running agents only', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/herdr', issue: '48', paper_only: false, policy_profiles: ['default'],
      agents: [],
      tasks: [{
        task_id: 'blocked-history', parent_task_id: null, parent_agent_id: null,
        agent_id: 'historic-agent', state: 'blocked', role: 'worker',
        model: 'model-a', fallback_model: null, attempt: 1, max_attempts: 2,
        blocker: 'dependency_wait', fencing_token: 9, dependencies: [], result_sha: null,
      }],
      edges: [],
    }],
  });
  await h.refresh();
  assert.match(h.get('#swarm-kpis').innerHTML, /<span>Active<\/span><b>0<\/b>/);
  assert.match(h.get('#observability-kpis').innerHTML, /<span>Aktivní práce<\/span><b>0 agent ·/);
});

test('QuantLab swarm browser boundary rejects non-PAPER snapshots', async t => {
  const h = await harness(t);
  const now = Math.floor(Date.now() / 1000);
  h.snapshot().sources.push({
    profile: 'quantlab', kind: 'swarm', status: 'available', reason: 'ok',
    observed_at: now, data_at: now,
    rows: [{
      version: 1, repo: 'Bbambaaamm/Autonomous-Quant-Lab', issue: '231',
      paper_only: false, policy_profiles: [], agents: [], tasks: [], edges: [],
    }],
  });
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
});
